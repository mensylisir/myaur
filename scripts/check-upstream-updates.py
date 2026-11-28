#!/usr/bin/env python3
"""Check whether any packaged product has a newer upstream release.

Each package directory holds a PKGBUILD whose pkgver is compared against a
small, product-specific probe of the official release channel.  Only the
Python standard library is used so the script runs unchanged on a GitHub
Actions runner.

Exit status:
  0  every probe succeeded and no package is out of date
  1  at least one package has a newer upstream version
  2  at least one probe failed (network, protocol or parsing problem)
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import lzma
import os
import re
import smtplib
import ssl
import sys
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

UA = "myaur-upstream-check/1 (+https://github.com/mensylisir/myaur)"
TIMEOUT = 30
MAIL_TO_DEFAULT = "710080675@qq.com"

# Inno/RPM lead: the 66-byte name field starts at offset 10.
RPM_LEAD_NAME = slice(10, 76)

# MiMo publishes a versionless "latest" deb, so the version lives in its
# Debian control archive rather than in the file name or headers.
MIMO_DEB_LATEST = (
    "https://mimocode-cdn.xiaomimimo.com/mimocode/mimodesktop/XiaomiMiMo-latest-x64.deb"
)
MIMO_AI_DEB_LATEST = (
    "https://mimocode-cdn.xiaomimimo.com/mimocode/mimodesktopai/XiaomiMiMo-AI-latest-x64.deb"
)
# ZCode has neither an update manifest nor a versionless deb: its download
# pages link the current versioned Linux deb directly.
ZCODE_DOWNLOAD_PAGE = "https://zcode.z.ai/"
ZCODE_CN_DOWNLOAD_PAGE = "https://zcode.z.ai/cn"
# Kilo Desktop publishes one mutable "latest" deb per architecture and keeps
# Version at 1.0.0 across releases, so its Last-Modified date is part of the
# version the package tracks.
KILO_DEB_LATEST = (
    "https://autoupdate.desktop.anaconda.com/kilo-desktop/latest/latest/linux/x64/kilo-desktop.deb"
)
# Qoder IDE's update API answers from CDN nodes that lag behind a rollout, but
# the ``release/latest`` RPM in the same OSS bucket is refreshed by the release
# job, so its RPM lead is the authoritative version.
QODER_IDE_OSS_LATEST = (
    "https://qoder-ide.oss-accelerate.aliyuncs.com/release/latest/qoder-ide_x86_64.rpm"
)
QODER_IDE_OSS_VERSIONED = (
    "https://qoder-ide.oss-accelerate.aliyuncs.com/release/{version}/qoder-ide_x86_64.rpm"
)
AR_HEADER_SIZE = 60

# Packages whose PKGBUILD pins upstream pieces separately from pkgver.  Keys
# are PKGBUILD variable names, values are probe component names.  WorkBuddy's
# Windows payload and Linux donor deb are compared in main() because both need
# the build hash from the download URL, not just the numeric version.
COMPONENTS: dict[str, dict[str, str]] = {
    "workbuddy-agent": {"_sandbox": "sandbox", "_harness": "harness"},
    "workbuddy-intl-agent": {"_sandbox": "sandbox", "_harness": "harness"},
}


@dataclass
class Probe:
    """Result of querying one product."""

    version: str | None = None
    url: str | None = None
    checksum: str | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def http(url: str, headers: dict[str, str] | None = None, limit: int = 0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read(limit) if limit else resp.read()


def http_headers(url: str, method: str = "HEAD") -> dict[str, str]:
    """Return the response headers with lower-case names."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return {name.lower(): value for name, value in resp.headers.items()}


def http_json(url: str, headers: dict[str, str] | None = None) -> Any:
    """Fetch JSON, decompressing when the server ignores Accept-Encoding.

    download.qoder.com now returns gzip for the channel manifest even though
    urllib sends no Accept-Encoding; decode it here rather than failing on
    UndefinedCharacterError mid-run.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read()
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
    if encoding == "gzip":
        raw = gzip.decompress(raw)
    elif encoding == "deflate":
        raw = zlib.decompress(raw)
    return json.loads(raw)


def pkgver(pkg: str) -> str:
    text = (ROOT / pkg / "PKGBUILD").read_text(encoding="utf-8")
    variables = dict(re.findall(r"^(_\w+)=(\S+)", text, re.MULTILINE))
    match = re.search(r"^pkgver=(\S+)", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"{pkg}/PKGBUILD has no pkgver")

    def expand(value: str) -> str:
        for name, replacement in variables.items():
            value = value.replace("${%s}" % name, replacement)
        return value

    return expand(match.group(1))


def pkgvar(pkg: str, name: str) -> str | None:
    """Read one plain ``name=value`` variable from a PKGBUILD."""
    text = (ROOT / pkg / "PKGBUILD").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(name)}=(\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def comparable(version: Any) -> str:
    """Normalise pkgver encodings without hiding real upstream changes.

    WorkBuddy appends an 8-hex content hash after ``_``; the domestic
    qoderwake channel tags releases with ``-cn``/``_cn``.  Debian-style
    revisions are kept (``26.1105.50703-202`` becomes ``_202``), because a
    revision bump is still a new upstream package to rebuild.
    """
    version = str(version).replace("-", "_")
    # Only strip an 8-char hexadecimal hash that actually contains a letter:
    # a pure numeric suffix may be a real version/revision (e.g. _20261016).
    version = re.sub(r"_(?=[0-9a-f]{8}$)[0-9a-f]*[a-f][0-9a-f]*$", "", version)
    return re.sub(r"_cn$", "", version)


def version_key(version: str) -> tuple[int, ...]:
    """Numeric sort key so 2.3.100000 is newer than 2.3.99999."""
    return tuple(int(part) if part.isdigit() else 0
                 for part in re.split(r"[._\-]", version))


def probe_catpaw(domain: str, _current: str) -> Probe:
    """CatPaw / 妙手 publish the current installer through an unauthenticated API.

    The older ``/ide/update`` gateway answers 204 to every version, including
    versions that do not exist, so it cannot detect releases.  ``/ide/latest``
    returns the current manifest unconditionally and does work.
    """
    data = http_json(f"https://{domain}/api/gateway/ide/latest?platform=win32-x64")
    payload = data.get("data") or {}
    return Probe(
        version=payload.get("version"),
        url=payload.get("url"),
        checksum=payload.get("sha256"),
    )


def probe_electron_yml(url: str) -> Probe:
    """Read an electron-builder feed (``latest.yml`` / ``latest-linux.yml``).

    Used by products that port the installer of another platform.  Only the
    version and the first artifact are exposed; vendor feeds usually publish
    sha512, so the checksum is left for the packaging step to compute.
    """
    text = http(url).decode("utf-8", "replace")
    version = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    entries = re.findall(r"^\s*-\s*url:\s*(.+?)\s*$", text, re.MULTILINE)
    if not entries:
        entries = re.findall(r"^path:\s*(.+?)\s*$", text, re.MULTILINE)
    # Feeds list every platform artifact; prefer the installer this repository
    # actually repackages (deb for Linux ports, exe for Windows payload ports).
    preferred = next(
        (name for name in entries if name.lower().endswith((".deb", ".rpm", ".exe", ".zip"))),
        entries[0] if entries else None,
    )
    resolved = None
    if preferred:
        resolved = urllib.parse.urljoin(url, urllib.parse.quote(preferred))
    return Probe(version=version.group(1) if version else None, url=resolved)


def probe_npm(name: str, channel: str = "latest") -> Probe:
    """Latest version of an npm package, used for npm-distributed products."""
    data = http_json(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='')}")
    tags = data.get("dist-tags") or {}
    version = tags.get(channel)
    dist = ((data.get("versions") or {}).get(version) or {}).get("dist") or {}
    return Probe(version=version, url=dist.get("tarball"), checksum=dist.get("shasum"))


def with_build(version: Any, url: Any) -> str | None:
    """Combine a WorkBuddy version with the 8-hex build tag from its URL.

    The update API returns ``5.11.3.43806934`` while the real download is
    ``...-5.11.3.43806934-ecace0f7.exe``; two builds can share the numeric
    version but differ in that hash, and the hash alone is a real update.
    """
    if not version:
        return None
    match = re.search(r"-([0-9a-f]{8})\.(?:exe|zip|deb)(?:\?|$)", str(url or ""))
    return f"{version}_{match.group(1)}" if match else str(version)


def probe_workbuddy(domain: str, platform: str) -> Probe:
    """WorkBuddy ships a Windows payload plus separate Linux runtime pieces.

    The package tracks the Windows payload in pkgver, but the domestic deb and
    the two npm helper packages are pinned separately, so a release can change
    them without touching the payload version.  Collect all of them.
    """
    data = http_json(f"https://{domain}/v2/update?platform={platform}")
    components: dict[str, str | None] = {
        "payload": with_build(data.get("version"), data.get("url")),
    }
    try:
        deb = http_json("https://www.workbuddy.cn/v2/update?platform=workbuddy-linux-x64-deb")
        components["deb"] = with_build(deb.get("version"), deb.get("url"))
    except Exception as exc:  # noqa: BLE001 - a missing channel must not hide the payload
        components["deb"] = f"error: {type(exc).__name__}"
    try:
        components["sandbox"] = probe_npm("@tencent-ai/sandbox-cli-linux-x64").version
    except Exception as exc:  # noqa: BLE001
        components["sandbox"] = f"error: {type(exc).__name__}"
    try:
        # The package pins the beta harness build, not the stable dist-tag.
        components["harness"] = probe_npm("@tencent-ai/agent-harness-linux-x64", "beta").version
    except Exception as exc:  # noqa: BLE001
        components["harness"] = f"error: {type(exc).__name__}"
    return Probe(
        version=data.get("version"),
        url=data.get("url"),
        checksum=data.get("sha256hash"),
        extra={"components": components},
    )


def probe_qoder_latest(url: str) -> Probe:
    """qoder ships an electron-builder ``latest-linux.yml``."""
    text = http(url).decode("utf-8", "replace")
    version = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    rpm = re.search(r"url:\s*(\S+Qoder[^\s]*\.rpm)", text)
    checksum = None
    if rpm:
        block = text[rpm.start():].split("- url:")[0]
        sha = re.search(r"sha256:\s*(\w+)", block)
        checksum = sha.group(1) if sha else None
    return Probe(
        version=version.group(1) if version else None,
        url=rpm.group(1) if rpm else None,
        checksum=checksum,
    )


def probe_qoderwake(url: str) -> Probe:
    """qoderwake publishes a channel manifest listing per-arch runtime archives."""
    data = http_json(url)
    version = data.get("latest")
    if not isinstance(version, str) or not version:
        raise ValueError("manifest has no string 'latest' version")
    files = data.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest has no 'files' list")

    def pick(arch: str) -> dict[str, Any] | None:
        return next(
            (item for item in files
             if isinstance(item, dict)
             and item.get("os") == "linux" and item.get("arch") == arch),
            None,
        )

    amd64 = pick("amd64")
    if not amd64 or not amd64.get("url") or not amd64.get("sha256"):
        raise ValueError("manifest has no usable linux/amd64 archive entry")
    arm64 = pick("arm64")
    return Probe(
        version=version,
        url=amd64["url"],
        checksum=amd64["sha256"],
        extra={"arm64_sha256": (arm64 or {}).get("sha256")},
    )


def rpm_lead(url: str) -> tuple[str | None, str]:
    """Read the NEVRA out of the RPM lead with a 96-byte range request."""
    raw = http(url, {"Range": "bytes=0-95"}, limit=96)
    name = raw[RPM_LEAD_NAME].decode("ascii", "replace").split("\x00", 1)[0]
    match = re.search(r"-(\d+(?:\.\d+)+)-", name)
    return (match.group(1) if match else None), name


def probe_qoder_ide(url: str, current: str, attempts: int = 5) -> Probe:
    """The update API sits behind CDN nodes that lag behind a rollout: during a
    release the same URL alternates between the old and the new manifest, so a
    single request can miss a real update (1.42.1 shipped while some nodes kept
    answering 1.41.1).  Ask several times, keep the newest answer, and fall back
    to the version baked into the ``release/latest`` RPM, which the release job
    refreshes in the same OSS bucket and is therefore authoritative."""
    current_key = version_key(current)
    best: dict[str, Any] = {}
    best_key: tuple[int, ...] = ()
    for _ in range(attempts):
        try:
            data = http_json(url)
        except (urllib.error.URLError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        version = data.get("productVersion")
        if not isinstance(version, str) or not version:
            continue
        key = version_key(version)
        if key > best_key:
            best, best_key = data, key
        if best_key > current_key:
            break

    try:
        oss_version, _nevra = rpm_lead(QODER_IDE_OSS_LATEST)
    except (urllib.error.URLError, ValueError):
        oss_version = None
    if oss_version and version_key(oss_version) > best_key:
        return Probe(
            version=oss_version,
            url=QODER_IDE_OSS_VERSIONED.format(version=oss_version),
            extra={"source": "oss-latest-rpm"},
        )

    if not best:
        raise ValueError(f"no usable manifest after {attempts} requests")
    return Probe(version=best.get("productVersion"), url=best.get("url"),
                 checksum=best.get("sha256hash"))


def probe_qoder_cn_ide(url: str) -> Probe:
    """No update API: read the NEVRA out of the RPM lead via a range request."""
    version, name = rpm_lead(url)
    return Probe(version=version, url=url, extra={"nevra": name})


def ar_members(raw: bytes) -> list[tuple[str, bytes, int]]:
    """Split the first bytes of a Debian package into ``ar`` members."""
    if not raw.startswith(b"!<arch>\n"):
        raise ValueError("not an ar archive")
    members: list[tuple[str, bytes, int]] = []
    offset = 8
    while offset + AR_HEADER_SIZE <= len(raw):
        header = raw[offset:offset + AR_HEADER_SIZE]
        name = header[:16].decode("ascii", "replace").strip().rstrip("/")
        size = int(header[48:58].decode("ascii", "replace").strip() or "0")
        start = offset + AR_HEADER_SIZE
        members.append((name, raw[start:start + size], size))
        offset = start + size + (size & 1)
    return members


def probe_deb_control(url: str) -> Probe:
    """Read the version from the control archive of a Debian package.

    Used for products that publish a versionless "latest" deb (MiMo) or whose
    version only exists in the package metadata (ZCode's download page links
    ``ZCode-<version>-linux-x64.deb`` but the Debian revision lives in the
    control archive). A single 2 MiB range request replaces downloading the
    whole package.
    """
    raw = http(url, {"Range": "bytes=0-2097151"}, limit=2 * 1024 * 1024)
    control = None
    for name, data, size in ar_members(raw):
        if not name.startswith("control.tar"):
            continue
        if len(data) < size:
            raise ValueError(f"{name} truncated in the first 2 MiB")
        if name.endswith(".xz"):
            blob = lzma.decompress(data)
        elif name.endswith(".gz"):
            blob = gzip.decompress(data)
        elif name.endswith(".zst"):
            raise ValueError("control.tar.zst needs an external zstd decoder")
        else:
            blob = data
        with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
            names = tar.getnames()
            member = "./control" if "./control" in names else "control"
            if member in names:
                control = tar.extractfile(member).read().decode("utf-8", "replace")
        break
    if control is None:
        raise ValueError("deb has no readable control archive")
    match = re.search(r"^Version:\s*(\S+)", control, re.MULTILINE)
    if not match:
        raise ValueError("control archive has no Version field")
    raw_version = match.group(1)
    # Debian revisions use "-", which pkgver spells "_"; normalise so the
    # comparison does not depend on the revision separator.
    return Probe(
        version=raw_version.replace("-", "_"),
        url=url,
        extra={"control_version": raw_version},
    )


def probe_zcode_deb(page: str) -> Probe:
    """Pick the newest Linux deb linked from a ZCode download page."""
    text = http(page).decode("utf-8", "replace")
    urls = {
        match.group(1): match.group(0)
        for match in re.finditer(
            r"https://cdn-zcode\.z\.ai/zcode/electron/releases/(\d+(?:\.\d+)+)"
            r"/linux-x64/ZCode-\1-linux-x64\.deb",
            text,
        )
    }
    if not urls:
        raise ValueError("download page has no linux-x64 deb link")
    return probe_deb_control(urls[max(urls, key=version_key)])


def probe_apifox() -> Probe:
    """Apifox's Linux downloads are mutable "-latest" zips without a version.

    The channel manifest next to them is the Windows update feed and is tiny;
    Apifox ships every desktop platform from one release, so its version also
    covers the Linux AppImage (verified against X-AppImage-Version).
    """
    text = http("https://file-assets.apifox.com/download/latest.yml").decode(
        "utf-8", "replace"
    )
    version = re.search(r"^version:\s*(\S+)", text, re.MULTILINE)
    return Probe(
        version=version.group(1) if version else None,
        url="https://file-assets.apifox.com/download/Apifox-linux-latest.zip",
    )


def probe_kilo() -> Probe:
    """Kilo Desktop keeps Version at 1.0.0 across releases.

    Its deb is a mutable "latest" artifact without an update manifest, while
    the payload (app.asar and the unpacked native prebuilds) changes every
    build. The Last-Modified date is appended to the control version so a
    rebuilt artifact still reads as an upgrade.
    """
    control = probe_deb_control(KILO_DEB_LATEST)
    modified = http_headers(KILO_DEB_LATEST).get("last-modified")
    if not modified:
        raise ValueError("deb response has no Last-Modified header")
    stamp = parsedate_to_datetime(modified).strftime("%Y%m%d")
    return Probe(
        version=f"{control.extra['control_version']}.{stamp}",
        url=KILO_DEB_LATEST,
    )


def probe_github_release(repo: str) -> Probe:
    data = http_json(f"https://api.github.com/repos/{repo}/releases/latest")
    return Probe(
        version=str(data.get("tag_name", "")).lstrip("v"),
        url=data.get("html_url"),
    )


def probe_github_tags(repo: str) -> Probe:
    """Latest version tag; for repos that tag releases without publishing them."""
    tags = http_json(f"https://api.github.com/repos/{repo}/tags?per_page=30")
    for tag in tags:
        name = tag.get("name", "").lstrip("vV")
        if name and name[0].isdigit():
            return Probe(
                version=name,
                url=f"https://github.com/{repo}/releases/tag/{tag['name']}",
            )
    raise ValueError("no version tag found")


def probe_trae(url: str) -> Probe:
    """Trae exposes per-platform builds; the package tracks the Linux build id."""
    data = http_json(url)
    entries = data["data"]["manifest"]["linux"]["versions"]
    builds = []
    for entry in entries:
        match = re.search(r"/stable/(\d+(?:\.\d+)+)/", entry.get("url", ""))
        if match:
            builds.append((match.group(1), entry.get("url")))
    if not builds:
        return Probe()
    version, url = max(builds, key=lambda pair: version_key(pair[0]))
    return Probe(
        version=version,
        url=url,
        extra={"app_version": entries[0].get("version") if entries else None},
    )


PRODUCTS: tuple[tuple[str, str, Any], ...] = (
    ("catpaw", "CatPaw 国际版", lambda cur: probe_catpaw("global-gateway.catpaw.com", cur)),
    ("catpaw-cn", "CatPaw 国内版", lambda cur: probe_catpaw("catx.nocode.cn", cur)),
    ("workbuddy-intl-agent", "WorkBuddy 国际版",
     lambda _cur: probe_workbuddy("www.workbuddy.ai", "workbuddy-win32-x64-archive")),
    ("workbuddy-agent", "WorkBuddy 国内版",
     lambda _cur: probe_workbuddy("www.workbuddy.cn", "workbuddy-win32-x64-archive")),
    ("qoder-agent", "Qoder Agent 国际版",
     lambda _cur: probe_qoder_latest("https://download.qoder.com/qoder-app/releases/latest-linux.yml")),
    ("qoder-cn-agent", "Qoder Agent 国内版",
     lambda _cur: probe_qoder_latest(
         "https://qoder-app.oss-cn-beijing.aliyuncs.com/qoder-app/releases/latest-linux.yml")),
    ("qoder-ide", "Qoder IDE 国际版",
     lambda cur: probe_qoder_ide(
         "https://center.qoder.sh/algo/api/update/linux-x64/stable/latest", cur)),
    ("qoder-cn-ide", "Qoder IDE 国内版",
     lambda _cur: probe_qoder_cn_ide(
         "https://qoder-ide-cn.oss-cn-hangzhou.aliyuncs.com/qoder/release/lastest/qoder-cn-ide_x86_64.rpm")),
    ("qoderwake-bin", "QoderWake 国际版",
     lambda _cur: probe_qoderwake("https://download.qoder.com/qoderwake/channels/manifest.json")),
    ("qoderwake-cn-bin", "QoderWake 国内版",
     lambda _cur: probe_qoderwake(
         "https://ide.qoder.com.cn/qoderwake-cn/channels/manifest.json")),
    ("mimo-desktop-bin", "Xiaomi MiMo 桌面版",
     lambda _cur: probe_deb_control(MIMO_DEB_LATEST)),
    ("mimo-desktop-intl-bin", "Xiaomi MiMo 海外版",
     lambda _cur: probe_deb_control(MIMO_AI_DEB_LATEST)),
    ("zcode-intl-bin", "ZCode 国际版",
     lambda _cur: probe_zcode_deb(ZCODE_DOWNLOAD_PAGE)),
    ("zcode-cn-bin", "ZCode 国内版（BigModel）",
     lambda _cur: probe_zcode_deb(ZCODE_CN_DOWNLOAD_PAGE)),
    ("zcode-zai-cn-bin", "ZCode 国内版（Z.ai CN）",
     lambda _cur: probe_zcode_deb(ZCODE_CN_DOWNLOAD_PAGE)),
    ("gw2api-bin", "gemini-web2api-go",
     lambda _cur: probe_github_release("zexadev/gemini-web2api-go")),
    ("apifox-appimage-bin", "Apifox",
     lambda _cur: probe_apifox()),
    ("kilo-desktop-bin", "Kilo Desktop",
     lambda _cur: probe_kilo()),
    ("claudemom", "ClaudeMom",
     lambda _cur: probe_github_tags("BigPizzaV3/ClaudeMom")),
    ("trae-ide", "Trae IDE 国际版",
     lambda _cur: probe_trae("https://icube-normal.traeapi.us/icube/api/v1/native/version/trae/latest")),
    ("trae-cn-ide", "Trae IDE 国内版",
     lambda _cur: probe_trae("https://api.trae.cn/icube/api/v1/native/version/trae/cn/latest")),
    ("minimax-code-bin", "MiniMax Code（npm 版）",
     lambda _cur: probe_npm("@minimax-ai/code")),
    ("minimax-code-intl-bin", "MiniMax Code 国际版",
     lambda _cur: probe_electron_yml(
         "https://filecdn.minimax.chat/public/minimax-agent-prod/release/latest.yml")),
    ("minimax-code-cn-bin", "MiniMax Code 国内版",
     lambda _cur: probe_electron_yml(
         "https://filecdn.minimax.chat/public/minimax-agent-prod/release/latest.yml")),
    ("kimi-work-bin", "Kimi Work（旧包）",
     lambda _cur: probe_electron_yml("https://kimi-img.moonshot.cn/app/upgrade/latest.yml")),
    ("kimi-work-intl-bin", "Kimi Work 国际版",
     lambda _cur: probe_electron_yml("https://kimi-img.moonshot.cn/app/upgrade/latest.yml")),
    ("kimi-work-cn-bin", "Kimi Work 国内版",
     lambda _cur: probe_electron_yml("https://kimi-img.moonshot.cn/app/upgrade/latest.yml")),
    ("kimi-code-intl-bin", "Kimi Code 国际版",
     lambda _cur: probe_electron_yml("https://cdn.kimi.ai/kimi-code/desktop/latest-linux.yml")),
    ("kimi-code-cn-bin", "Kimi Code 国内版",
     lambda _cur: probe_electron_yml("https://cdn.kimi.com/kimi-code/desktop/latest-linux.yml")),
    ("appclone-bin", "appclone",
     lambda _cur: probe_github_release("mensylisir/appclone")),
)


def mail_body(payload: dict[str, Any]) -> str:
    lines = [
        f"检测时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    for row in payload["results"]:
        if row["state"] == "current":
            continue
        upstream = row.get("upstream") or "(探测失败)"
        line = f"- {row['product']}（{row['package']}）：{row['current']} -> {upstream}"
        if row["state"] == "error":
            line += f"，失败原因：{row['error']}"
        lines.append(line)
        if row["state"] in ("update", "components") and row.get("url"):
            lines.append(f"  {row['url']}")
        if row["state"] in ("update", "components") and row.get("checksum"):
            lines.append(f"  sha256: {row['checksum']}")
        for diff in row.get("component_updates") or ():
            lines.append(f"  {diff}")
    lines += [
        "",
        f"结论：{len(payload['updates'])} 个待更新，{len(payload['errors'])} 个探测失败。",
        "该通知只做提醒，构建与 AUR 发布仍需人工执行。",
        f"仓库：https://github.com/mensylisir/myaur",
    ]
    return "\n".join(lines)


def send_mail(payload: dict[str, Any]) -> None:
    password = os.environ.get("SMTP_PASS", "")
    if not password:
        print("SMTP_PASS 未配置，跳过邮件通知", file=sys.stderr)
        return
    host = os.environ.get("SMTP_HOST") or "smtp.qq.com"
    port = int(os.environ.get("SMTP_PORT") or "465")
    user = os.environ.get("SMTP_USER") or MAIL_TO_DEFAULT
    recipient = os.environ.get("MAIL_TO") or MAIL_TO_DEFAULT

    subject = "上游版本检测："
    subject += f"{len(payload['updates'])} 个待更新"
    if payload["errors"]:
        subject += f"，{len(payload['errors'])} 个探测失败"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = user
    message["To"] = recipient
    message.set_content(mail_body(payload))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, timeout=TIMEOUT, context=context) as smtp:
        smtp.login(user, password)
        smtp.send_message(message)
    print(f"邮件已发送至 {recipient}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write machine-readable results here")
    parser.add_argument("--only", nargs="*", help="limit to these package names")
    parser.add_argument(
        "--mail",
        action="store_true",
        help="email the report when any package is outdated or a probe fails",
    )
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    status = 0
    for pkg, label, probe in PRODUCTS:
        if args.only and pkg not in args.only:
            continue
        row: dict[str, Any] = {"package": pkg, "product": label}
        try:
            current = pkgver(pkg)
        except (OSError, SystemExit) as exc:
            row.update(current=None, upstream=None, state="error", error=str(exc))
            rows.append(row)
            status = max(status, 2)
            continue

        row["current"] = current
        try:
            result = probe(current)
        except Exception as exc:  # noqa: BLE001 - a broken probe must not abort the run
            row.update(upstream=None, state="error", error=f"{type(exc).__name__}: {exc}")
            status = max(status, 2)
            rows.append(row)
            continue

        row["upstream"] = result.version
        row["url"] = result.url
        row["checksum"] = result.checksum
        if result.extra:
            row["extra"] = result.extra
        if not result.version:
            row.update(state="error", error="probe returned no version")
            status = max(status, 2)
        elif comparable(result.version) == comparable(current):
            row["state"] = "current"
        else:
            row["state"] = "update"
            status = max(status, 1)

        # WorkBuddy: the Windows payload is the main program (it becomes
        # pkgver), while the domestic deb only supplies the customized Electron
        # runtime.  Compare both with the 8-hex build hash from the download
        # URL, because the update API's numeric version alone would hide a
        # rebuild that keeps the same version.
        if pkg in ("workbuddy-agent", "workbuddy-intl-agent") and row["state"] != "error":
            components = (result.extra or {}).get("components") or {}
            diffs: list[str] = []
            payload = components.get("payload")
            if payload:
                row["upstream"] = payload
            payload_changed = bool(payload and payload != current)
            if payload_changed:
                diffs.append(f"payload {current} -> {payload}")
            deb_pinned = f"{pkgvar(pkg, '_hostver')}_{pkgvar(pkg, '_hostbuild')}"
            deb_latest = components.get("deb")
            deb_changed = bool(deb_latest and deb_latest != deb_pinned)
            if deb_changed:
                diffs.append(f"deb {deb_pinned} -> {deb_latest}")
            for variable, key in (COMPONENTS.get(pkg) or {}).items():
                pinned = pkgvar(pkg, variable)
                latest = components.get(key)
                if pinned and latest and comparable(str(latest)) != comparable(pinned):
                    diffs.append(f"{variable} {pinned} -> {latest}")
            if diffs:
                row["component_updates"] = diffs
                row["state"] = "update" if (payload_changed or deb_changed) else "components"
                status = max(status, 1)
        rows.append(row)

    width = max(len(r["product"]) for r in rows) if rows else 0
    for row in rows:
        mark = {"current": "=", "update": ">", "components": "~", "error": "!"}[row["state"]]
        row["mark"] = mark
        upstream = row.get("upstream") or "-"
        line = f"{mark} {row['product']:<{width}}  {row['current'] or '-':<16} -> {upstream}"
        if row["state"] == "error":
            line += f"  ({row['error']})"
        print(line)
        if row["state"] in ("update", "components") and row.get("url"):
            print(f"    {row['url']}")
        if row["state"] in ("update", "components") and row.get("checksum"):
            print(f"    sha256: {row['checksum']}")
        for diff in row.get("component_updates") or ():
            print(f"    {diff}")

    updates = [r["package"] for r in rows if r["state"] in ("update", "components")]
    errors = [r["package"] for r in rows if r["state"] == "error"]
    print(f"\n{len(rows)} checked, {len(updates)} outdated, {len(errors)} probe errors")

    payload = {"updates": updates, "errors": errors, "results": rows}
    if args.json:
        args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.mail and status != 0:
        try:
            send_mail(payload)
        except Exception as exc:  # noqa: BLE001 - surface mail problems as a probe failure
            print(f"邮件发送失败：{type(exc).__name__}: {exc}", file=sys.stderr)
            status = max(status, 2)
    return status


if __name__ == "__main__":
    sys.exit(main())
