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
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
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
AR_HEADER_SIZE = 60


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


def http_json(url: str, headers: dict[str, str] | None = None) -> Any:
    return json.loads(http(url, headers))


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


def probe_catpaw(domain: str, current: str) -> Probe:
    """CatPaw / 妙手 query their update gateway with the running client version.

    The gateway answers ``204 No Content`` when the client is already current.
    """
    url = f"https://{domain}/api/gateway/ide/update?platform=win32-x64"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "ide-type": "CatPaw_Desk",
            "ide-version": current,
            "os-version": "10.0.19045",
            "user-mis-id": "0",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status == 204:
            return Probe(version=current)
        data = json.loads(resp.read())
    return Probe(version=data.get("version"), url=data.get("url"), checksum=data.get("sha256"))


def probe_workbuddy(domain: str, platform: str) -> Probe:
    data = http_json(f"https://{domain}/v2/update?platform={platform}")
    return Probe(
        version=data.get("version"),
        url=data.get("url"),
        checksum=data.get("sha256hash"),
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


def probe_qoder_ide(url: str) -> Probe:
    data = http_json(url)
    return Probe(version=data.get("productVersion"), url=data.get("url"),
                 checksum=data.get("sha256hash"))


def probe_qoder_cn_ide(url: str) -> Probe:
    """No update API: read the NEVRA out of the RPM lead via a range request."""
    raw = http(url, {"Range": "bytes=0-95"}, limit=96)
    name = raw[RPM_LEAD_NAME].decode("ascii", "replace").split("\x00", 1)[0]
    match = re.search(r"-(\d+(?:\.\d+)+)-", name)
    return Probe(version=match.group(1) if match else None, url=url, extra={"nevra": name})


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


def probe_mimo_deb(url: str) -> Probe:
    """Read the version from the control archive of MiMo's ``latest`` deb.

    The CDN object has no version in its name, so a single 2 MiB range
    request replaces downloading the whole 300 MB package.
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


def probe_github_release(repo: str) -> Probe:
    data = http_json(f"https://api.github.com/repos/{repo}/releases/latest")
    return Probe(
        version=str(data.get("tag_name", "")).lstrip("v"),
        url=data.get("html_url"),
    )


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
    ("catpaw-cn", "CatPaw 国内版", lambda cur: probe_catpaw("catpaw.meituan.com", cur)),
    ("workbuddy-intl-agent", "WorkBuddy 国际版",
     lambda _cur: probe_workbuddy("www.workbuddy.ai", "workbuddy-win32-x64-archive")),
    ("workbuddy-agent", "WorkBuddy 国内版",
     lambda _cur: probe_workbuddy("www.workbuddy.cn", "workbuddy-linux-x64-deb")),
    ("qoder-agent", "Qoder Agent 国际版",
     lambda _cur: probe_qoder_latest("https://download.qoder.com/qoder-app/releases/latest-linux.yml")),
    ("qoder-cn-agent", "Qoder Agent 国内版",
     lambda _cur: probe_qoder_latest(
         "https://qoder-app.oss-cn-beijing.aliyuncs.com/qoder-app/releases/latest-linux.yml")),
    ("qoder-ide", "Qoder IDE 国际版",
     lambda _cur: probe_qoder_ide("https://center.qoder.sh/algo/api/update/linux-x64/stable/latest")),
    ("qoder-cn-ide", "Qoder IDE 国内版",
     lambda _cur: probe_qoder_cn_ide(
         "https://qoder-ide-cn.oss-cn-hangzhou.aliyuncs.com/qoder/release/lastest/qoder-cn-ide_x86_64.rpm")),
    ("qoderwake-bin", "QoderWake 国际版",
     lambda _cur: probe_qoderwake("https://download.qoder.com/qoderwake/channels/manifest.json")),
    ("qoderwake-cn-bin", "QoderWake 国内版",
     lambda _cur: probe_qoderwake(
         "https://ide.qoder.com.cn/qoderwake-cn/channels/manifest.json")),
    ("mimo-desktop-bin", "Xiaomi MiMo 桌面版",
     lambda _cur: probe_mimo_deb(MIMO_DEB_LATEST)),
    ("gw2api-bin", "gemini-web2api-go",
     lambda _cur: probe_github_release("zexadev/gemini-web2api-go")),
    ("trae-ide", "Trae IDE 国际版",
     lambda _cur: probe_trae("https://icube-normal.traeapi.us/icube/api/v1/native/version/trae/latest")),
    ("trae-cn-ide", "Trae IDE 国内版",
     lambda _cur: probe_trae("https://api.trae.cn/icube/api/v1/native/version/trae/cn/latest")),
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
        if row["state"] == "update" and row.get("url"):
            lines.append(f"  {row['url']}")
        if row["state"] == "update" and row.get("checksum"):
            lines.append(f"  sha256: {row['checksum']}")
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
        rows.append(row)

    width = max(len(r["product"]) for r in rows) if rows else 0
    for row in rows:
        mark = {"current": "=", "update": ">", "error": "!"}[row["state"]]
        row["mark"] = mark
        upstream = row.get("upstream") or "-"
        line = f"{mark} {row['product']:<{width}}  {row['current'] or '-':<16} -> {upstream}"
        if row["state"] == "error":
            line += f"  ({row['error']})"
        print(line)
        if row["state"] == "update" and row.get("url"):
            print(f"    {row['url']}")
        if row["state"] == "update" and row.get("checksum"):
            print(f"    sha256: {row['checksum']}")

    updates = [r["package"] for r in rows if r["state"] == "update"]
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
