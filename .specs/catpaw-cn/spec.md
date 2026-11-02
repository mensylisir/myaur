# Spec: 新增 AUR 包 catpaw-cn（妙手国内版 Linux 移植）

## 目标

在 `myaur` 仓库新增 `catpaw-cn/`，把上游只发布 macOS（darwin-x64）安装包的「妙手」（CatPaw 国内版）转换为可安装的 Arch Linux 包。安装后命令为 `catpaw-cn`，数据目录与上游一致（`.meituan-catpaw`），不重新分发任何修改后的上游二进制以外的内容。

国际版 `catpaw` 在 `catpaw-cn` 跑通后按同一套脚本复制生成，本次 spec 只覆盖 `catpaw-cn`。

## 已确认的上游事实

| 项 | 值 | 来源 |
|---|---|---|
| 产品名 | 妙手 / catpaw-moon | `resources/app/product.json` |
| 版本 | `2026.1016.0034` | product.json `version`，dmg 文件名 `2026.1016.0034` |
| DMG | `https://s3plus.meituan.net/catpaw-external-resources/ide/darwin/stable/2026.1016.0034/妙手.20261016004642.dmg` | 用户提供 |
| DMG sha256 | `3c931da843e32128e4e3431f50231fac38f3b6f1c2a850bc9e783cc4d4deb3cf` | 已下载校验 |
| Electron | `42.11.2`（ABI 146） | `Electron Framework` 字符串 `Electron/42.11.2` |
| 应用结构 | `app.asar`（399 MB）+ `app.asar.unpacked` | `Contents/Resources/` |
| 运行时 | `resources/runtimes/{manifest.json,node,python}`，manifest 为 darwin/x64 | 已读取 |
| Linux 需要 | manifest `platform=linux, arch=x64`，assets 至少 `node`、`python` | `main-CH7oVGxu.js` 的 `IV()` / `Bfy` 逻辑 |
| PowerShell | Linux 上可选：manifest 不含 powershell 时 `h0t()` 通过（`powershell===void 0`） | 同上 |
| wecom-cli | asar 头部已登记 `@wecom/cli-linux-x64` / `-arm64`，但磁盘缺失 | asar 头部对比 |
| catpaw-cli | `@catpaw/agent-sdk` 的 `bin/catpaw-cli` 是 darwin-x64 的 Bun 二进制；Linux 版在官方 S3 | `scripts/postinstall.cjs` |
| agent-browser | `bin/agent-browser-darwin-x64`；Linux 版在 GitHub release | `scripts/postinstall.js` |
| asar 缺失 unpacked | 22 个（ffmpeg 残留、wecom linux/darwin-arm64、agent-browser 标记） | 头部对比，不影响本次替换 |

## 架构决策

1. **只支持 `x86_64`**：node-pty 没有 Linux 预编译，Arm64 需要交叉编译；其余原生模块虽有 arm64 包，但无法在当前环境验证。`arch=('x86_64')`，不承诺 aarch64。
2. **Electron 运行时用官方 Linux 包**：`electron-v42.11.2-linux-x64.zip`，与上游版本严格一致；替换 `resources/default_app.asar` 为上游 `app.asar`。
3. **会话运行时用官方 Linux 构建**：Node `v24.18.0`（nodejs.org）+ CPython `3.12.13`（python-build-standalone `20260807`，stripped install_only）。重写 `resources/runtimes/manifest.json` 为 linux/x64，`sha256` 取实际下载文件。
4. **原生模块全部换成 Linux 版本**（构建期不联网，全部作为 `source=()` 加入 PKGBUILD）：
   | 模块 | 版本 | 来源 |
   |---|---|---|
   | node-pty | 1.1.0 | npm 源码 + Electron 42 头文件本地 node-gyp 编译 |
   | node-addon-api | 7.1.1 | npm（node-pty 构建依赖） |
   | better-sqlite3 | 12.11.1 | GitHub release `electron-v146-linux-x64` 预编译 |
   | bufferutil | 4.1.0 | npm 源码 + 本地编译 |
   | utf-8-validate | 6.0.6 | npm 源码 + 本地编译 |
   | koffi | 3.2.0 | `@koromix/koffi-linux-x64` |
   | sharp | 0.35.2 | `@img/sharp-linux-x64` + `@img/sharp-libvips-linux-x64` 1.3.1 |
   | @napi-rs/canvas | 1.0.8 | `@napi-rs/canvas-linux-x64-gnu` |
   | @wecom/cli | 1.1.0 | `@wecom/cli-linux-x64` |
   | agent-browser | 0.27.3 | GitHub `agent-browser-linux-x64` |
   | @catpaw/agent-sdk CLI | 1.2.0-beta.33 | 官方 S3 `catpaw-cli-linux-x64` |
   | Electron headers | 42.11.2 | `artifacts.electronjs.org` `node-v42.11.2-headers.tar.gz` |
5. **不替换 `resources/native/xlsx-sidecar`**：上游只提供 Mach-O 通用二进制，无 Linux 版本；该文件不安装，Excel 侧车相关能力在 Linux 不可用，写入 DISCLAIMER 与 README。
6. **不安装 `paw` CLI 到 `/usr/bin`**：CN/国际两包会冲突；仅保留 `resources/bin/paw` 并在 Linux 下改写到 `/opt/catpaw-cn/catpaw-cn`。应用自身的 CLI 安装逻辑仍可把 shim 安装到用户目录。
7. **桌面集成以窗口标识为准**：应用实测 WM_CLASS / app_id 为 `catpaw-moon`（`--class` 参数无效），因此 desktop 文件名为 `catpaw-moon.desktop`、`Icon=catpaw-moon`、`StartupWMClass=catpaw-moon`，并把上游 `resources/icon.png` 缩放为 hicolor 16/24/32/48/64/128/256/512 图标，确保 Dash/任务栏不再显示无图标的蓝色菱形。国际版沿用 `catpaw-overseas` 标识，两者桌面条目互不合并。
8. **启动参数**：沿用 workbuddy-intl 的做法，`--no-sandbox --disable-dev-shm-usage --ozone-platform-hint=auto --enable-wayland-ime`。chrome-sandbox 需要 root:root 4755，包无法保证，因此构建时删除该文件；代价是渲染进程无 OS 级沙箱，已在 DISCLAIMER 说明。

## 文件与改动

新增：

- `catpaw-cn/PKGBUILD`
  - `pkgname=catpaw-cn`、`pkgver=2026.1016.0034`、`pkgrel=1`、`arch=('x86_64')`
  - `depends=('gtk3' 'nss' 'alsa-lib' 'libcups' 'libdrm' 'libx11' 'libxcb' 'libxcomposite' 'libxdamage' 'libxext' 'libxfixes' 'libxi' 'libxkbcommon' 'libxrandr' 'mesa' 'libsecret' 'libappindicator' 'libpulse' 'json-glib' 'wayland' 'systemd-libs' 'dbus' 'libnotify')`
  - `makedepends=('7zip' 'unzip' 'nodejs' 'node-gyp' 'python' 'gcc' 'make')`
  - `source=()` 含上表全部文件（dmg 用 `::` 重命名去掉中文），`noextract` 排除 dmg
  - `sha256sums=()` 全部真实值
  - `build()`：解 dmg → 调 `convert.sh`
  - `package()`：装到 `/opt/catpaw-cn`、`/usr/bin/catpaw-cn`、desktop、hicolor 图标、license/DISCLAIMER
  - `options=('!strip' '!debug')`
- `catpaw-cn/convert.sh`（bash，`set -Eeuo pipefail`）
  - `extract_dmg()`：`7z x` 到临时目录，定位 `*.app`，排除 `__MACOSX`
  - `stage_electron()`：解 Electron zip；删除 `default_app.asar`；重命名 `electron` → `catpaw-cn`
  - `copy_payload()`：复制 `app.asar`、`app.asar.unpacked`、`app/product.json`、`cli/`、`cli-apps/`、`app-extensions/`、`skills/`、`wasm/`、`icon.png`、托盘图标；跳过 `*.lproj`、`native/`、`runtimes/`、`bin/paw`（另行生成）
  - `replace_native_modules()`：按上表删除 darwin/win 目录并复制 Linux 包；`node-pty`/`bufferutil`/`utf-8-validate` 用 `node-gyp --nodedir=<headers>` 编译；`better-sqlite3` 解预编译 tar；`catpaw-cli`、`agent-browser` 放二进制并 `chmod 755`
  - `write_runtimes()`：清空 `resources/runtimes`；复制 node/python tar.gz 为 manifest 指定名字（版本号由 PKGBUILD 的 `NODE_VER`/`PYTHON_VER` 传入）；写 `manifest.json`（schemaVersion 2, platform linux, arch x64, node `bin/node`、python `bin/python3.12`，sha256 由 `sha256sum` 生成，文件数/解压体积上限放宽到 node 12000/400MB、python 10000/600MB）
  - `write_paw()`：生成 Linux 版 `resources/bin/paw`（`ELECTRON_RUN_AS_NODE=1` 调 `catpaw-cn` + `cli/catpaw-cli.js`）
  - `write_icon()`：`icon.png` → `resources/icon.png` 与包图标目录
- `catpaw-cn/catpaw-moon.desktop`（Name=妙手，Exec=/usr/bin/catpaw-cn，Icon=catpaw-moon，StartupWMClass=catpaw-moon；不注册 URL scheme）
- `catpaw-cn/catpaw-moon-{16,24,32,48,64,128,256,512}.png`（由上游 `resources/icon.png` 缩放生成的 hicolor 图标）
- `catpaw-cn/DISCLAIMER`（非官方移植、无 Linux xlsx-sidecar、运行时来源说明）
- `catpaw-cn/LICENSE.port-scripts`（本仓库脚本许可）

修改：

- `README.md`：新增 `catpaw-cn` 行（版本、上游、状态 `已构建`），说明非官方移植与验证命令。

## 明确不做

- 不修改 `app.asar` 内容（平台分支已自带 Linux 逻辑）。
- 不引入构建期网络访问；不在 PKGBUILD 里 `npm install`。
- 不支持 aarch64。
- 不创建 `catpaw`（国际版）包，待本包验证后单独执行。

## 验证步骤（完成定义）

1. `makepkg -f --nodeps` 在包目录成功（记录命令与日期）。
2. `makepkg --printsrcinfo > .SRCINFO`，再生成一次后 `git diff -- .SRCINFO` 为空。
3. `namcap PKGBUILD` 与 `namcap *.pkg.tar.zst`：环境缺 `namcap`，记录缺失并以 `bash -n` + 手工检查替代。
4. 运行态：该应用没有 `--version` 开关（传参会直接启动 GUI），改用 `ELECTRON_RUN_AS_NODE=1 /opt/catpaw-cn/catpaw-cn -e "console.log(process.versions.electron)"` 验证输出版本为 `42.11.2`；GUI 启动后确认 `WM_CLASS=catpaw-moon` 且 Dash 图标可解析。
5. 原生模块加载：以 Electron 作为 node，逐个 `require` node-pty / better-sqlite3 / koffi / sharp / @napi-rs/canvas / @wecom/cli-linux-x64，全部无异常。
6. 运行时：在临时 userData 下启动应用（有 `DISPLAY=:0`），确认 `runtime-install.log` 出现 `node`、`python` 的 `archive.checksum.ok` / `verify` 成功，无 `install.failed`。
7. 按 AGENTS 强制两轮 subagent 审查（标准 + 对抗），结论写入提交信息。
8. 未实际推送 AUR 前，README 状态不得写「已推送 AUR」。
