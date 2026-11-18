# AUR 包全量复审（2026-11-18）规格

## 目标

对 `/home/mensyli1/Documents/workspace/myaur` 下全部 AUR 包做一次从头开始的只读审计，重点排查：

1. 单版本被拆成国内 / 国际两个包后，路径、数据目录、桌面文件、图标、WMClass、命令、深链协议是否仍然混用；
2. Wayland 下 Electron 走 XDG GlobalShortcuts portal 导致 GNOME 弹 “Add Keyboard Shortcuts” 的问题是否在所有相关包中仍有防护；
3. 空白窗口 / 空白弹窗的既有修复是否仍在（尤其 WorkBuddy、catpaw、trae、minimax）；
4. 旧修复是否发生回归。

发现问题后：修复、`makepkg` 构建验证、提交 GitHub；**不推送 AUR**。

## 已完成的机械检查（本轮）

| 检查 | 结果 |
| --- | --- |
| 27 个 PKGBUILD 的 `.SRCINFO` 与 `makepkg --printsrcinfo` 比对 | 全部一致 |
| 所有 `*.sh` / `*.install` 的 `bash -n` | 全部通过 |
| 所有 desktop 文件 `desktop-file-validate` | 仅 hint/warning，无 error |
| README 版本与 PKGBUILD 对照 | 一致 |

## 已确认仍存在的既有修复

- `workbuddy-agent`：PKGBUILD 内联 launcher 在 Wayland 下预置 `~/.workbuddy/app/shortcut-state.json` 空 accelerator，并带 `--no-sandbox --disable-dev-shm-usage --disable-gpu-sandbox --in-process-gpu --ozone-platform-hint=auto --enable-wayland-ime --class=workbuddy`。
- `workbuddy-intl-agent/start.sh`：同样的快捷键预置（`~/.workbuddy-ai/app`，尊重 `WORKBUDDY_*`/`CODEBUDDY_*`）与 GPU/Wayland 参数；桌面文件名 `workbuddy-international.desktop` 与 `CHROME_DESKTOP`、`--class` 一致。
- `kimi-code-cn-bin` / `kimi-code-intl-bin`：Wayland 下追加 `--disable-features=GlobalShortcutsPortal`；两版 `KIMI_CODE_HOME` 分离，国内版深链改为 `kimi-code-cn`。
- `kimi-work-cn-bin` / `kimi-work-intl-bin`：`patch-region.js` 把区域固定为 china/overseas、把 `launcherEnabled` 默认改为 false、改写 `package.json` 的 name 与 desktopName，资源走独立 `/opt` 前缀。
- `minimax-code-cn-bin` / `minimax-code-intl-bin`：launcher 使用 `--no-sandbox` 与独立 `--user-data-dir`；`patch-region.js` 改写 package.json name、区域端点、托盘菜单。
- `zcode-cn-bin` / `zcode-intl-bin`：独立 `/opt` 前缀、独立 `ZCODE_DESKTOP_USER_DATA_DIR` / `ZCODE_DATA_BASE_DIR`、独立 desktop id 与 `--class`。
- `mimo-desktop-bin` / `mimo-desktop-intl-bin`：`envguard.so` 隔离超大环境变量，官方 payload 的 productName / 二进制不同。

## 待核实并可能修复的问题（按优先级）

### P1 深链协议（国内 / 国际互抢）

| 包对 | 现状 | 风险 |
| --- | --- | --- |
| `workbuddy-agent` / `workbuddy-intl-agent` | 两个 desktop 都声明 `x-scheme-handler/workbuddy` | 后安装者独占 `workbuddy://`，点链接可能打开另一版本 |
| `minimax-code-cn-bin` / `minimax-code-intl-bin` | desktop 分别声明 `minimax-cn` / `minimax`，但未确认 app 自身是否在两版都调用 `setAsDefaultProtocolClient('minimax')` | 若运行时两版都写 `~/.local/share/applications/minimax.desktop`，会互相覆盖 |
| `zcode-cn-bin` / `zcode-intl-bin` | 两版都由 app 内建 `zcode://` | 注释已承认后安装者独占；需确认是否可接受或有包级隔离手段 |

核实命令：在已下载的官方包（deb / zip）中解包 `app.asar`，检索 `setAsDefaultProtocolClient`、`x-scheme-handler`、协议常量。

修复原则：
- 只有存在两个版本的包才处理；单包不引入额外复杂度。
- 若 app 支持第二协议（如 WorkBuddy 的 `buddy-app://`、miniMax 的 `minimax-cn://`），让国内版独占主协议、国际版只保留自身可用的第二协议；否则在 spec 中记录为上游限制，不做伪隔离。
- 修改 desktop 的 `MimeType` 时同步改 `.SRCINFO`、`pkgrel`。

### P1 Wayland 全局快捷键

需静态确认以下包的 payload 是否注册 `globalShortcut`，以及是否已有防护：

- `catpaw` / `catpaw-cn`（`patch-overlay-window.js` 只处理空白窗口，未见快捷键防护）
- `zcode-intl-bin` / `zcode-cn-bin`
- `mimo-desktop-bin` / `mimo-desktop-intl-bin`
- `minimax-code-*`
- `workbuddy-*`（已有 shortcut-state.json，需确认状态文件路径与 app 实际读取路径一致）
- `qoder-agent` / `qoder-cn-agent`、`qoder-ide` / `qoder-cn-ide`
- `trae-ide` / `trae-cn-ide`
- `kimi-work-*`、`kimi-code-*`（已确认）

核实命令：对已解包的 `app.asar`（或 asar 文件）执行 `grep -a` 检索 `globalShortcut`、`GlobalShortcutsPortal`、`shortcut-state`。

修复原则：优先采用与 `kimi-code-*` 相同的 `--disable-features=GlobalShortcutsPortal`（Wayland 分支）；若 app 有状态文件机制则按 `workbuddy-*` 方式预置。

### P2 数据目录 / 窗口类隔离

逐对核对：

- `qoder-ide` / `qoder-cn-ide`：`product.json` 的 `dataFolderName` / `nameShort` / `applicationName` 是否不同；相同则需在包内 patch 或通过 `--user-data-dir` 隔离。
- `trae-ide` / `trae-cn-ide`：同上。
- `catpaw` / `catpaw-cn`：productName / userData 路径是否不同。
- `minimax-code-*`：`package.json` name 已改，确认 userData 不再共用。
- `mimo-*`：确认 `envguard` 不改变 userData，且两版 productName 不同。
- `workbuddy-*`：确认国内 `~/.workbuddy`、国际 `~/.workbuddy-ai` 与 app 实际路径一致。

### P2 旧包冲突声明

- `kimi-work-cn-bin` 未声明 `conflicts=('kimi-work-bin' 'kimi-bin')`（国际版已声明）。核实文件是否重叠：若 `kimi-work-bin` 安装 `/usr/bin/kimi-work`、`/usr/share/applications/kimi-work.desktop`，与 cn 不冲突，则保持现状；若存在重叠则补 conflicts。
- `kimi-code-cn-bin` 未声明 `conflicts=('kimi-code-desktop-bin')`（国际版已声明）。同样先核实文件重叠。

### P3 仓库卫生

- `workbuddy-agent/`、`workbuddy-intl-agent/` 目录内留有构建下载物（`.deb`、`.zip`、`.tgz`）。确认 `.gitignore` 已忽略；若未忽略且未被跟踪，加入忽略规则或清理，避免误提交大文件。

## 变更清单（仅在实际确认后执行）

| 文件 | 变更 | 触发条件 |
| --- | --- | --- |
| `workbuddy-intl-agent/workbuddy-international.desktop` | 若确认 app 支持 `buddy-app://`，移除 `x-scheme-handler/workbuddy`，只保留 `buddy-app` | 国内/国际同时安装时 workbuddy 深链互抢 |
| `minimax-code-intl-bin/minimax-code-intl.desktop` | 若 app 运行时会覆盖 `minimax` 协议，改为专用协议或删除冲突项 | 静态证据确认 |
| `*/PKGBUILD`、`*/*.sh` | 为确认缺少防护的包补 Wayland 全局快捷键 / 空白窗口修复 | P1 核实为「无防护」 |
| `qoder-ide` / `qoder-cn-ide`、`trae-ide` / `trae-cn-ide` 相关补丁或 launcher | 数据目录隔离 | P2 核实为共用 |
| `kimi-work-cn-bin/PKGBUILD`、`kimi-code-cn-bin/PKGBUILD` | 补 `conflicts` | P2 核实存在文件重叠 |
| `.gitignore` | 忽略构建下载物 | P3 核实未忽略 |

每次改动都要：

1. 同步 `.SRCINFO`（`makepkg --printsrcinfo > .SRCINFO`）；
2. `pkgrel` +1（PKGBUILD 内容变更时）；
3. `makepkg -f` 构建通过；
4. 清理构建产物；
5. 提交 GitHub，不推 AUR。

## 验证步骤

1. `for d in */; do diff -q <(cd "$d" && makepkg --printsrcinfo) "$d/.SRCINFO"; done`
2. `bash -n` 所有脚本；`desktop-file-validate` 所有 desktop。
3. 对每个改动包执行 `makepkg -f`（至少 `--printsrcinfo` + `--packagelist`）。
4. 逐对复查：`/opt` 前缀、`/usr/bin` 命令、desktop id、Icon、StartupWMClass、userData、MimeType。
5. `python3 scripts/check-upstream-updates.py` 记录上游新版本（仅记录，不在本轮升级）。

## 不在首轮范围（第二轮已执行）

- 上游新版本升级（Qoder Agent 国内 0.5.14、QoderWake 1.2.20 / 1.2.20-cn、Trae 国际 2.3.103560）已在第二轮无条件升级并构建验证。
- AUR 推送仍不在范围：所有变更只提交 GitHub。
- 新增包仍不在范围。

## 核实结论（2026-11-18 执行）

1. **WorkBuddy 深链已修复**：上游 `resources/app.asar.unpacked/cli/product.json` 中国内版 `deepLinkSchemes=["workbuddy"]`、国际版 `["workbuddy-ai"]`。国际版 desktop 原先声明 `workbuddy`，会与国内版争抢主协议，已改为 `x-scheme-handler/workbuddy-ai`。`buddy-app` 为应用运行时对两版都追加的兼容协议，属上游行为，保留。
2. **WorkBuddy 数据目录无误**：`getWorkbuddyUserDataDir()` 使用 product.json 的 `dataFolderName`，国内 `.workbuddy`、国际 `.workbuddy-ai`，`shortcut-state.json` 位于其下 `app/`，与两个 launcher 的预置路径一致。
3. **mimo 最新 26.1116 两版**：asar 中均无 `globalShortcut` 与 `setAsDefaultProtocolClient`；productName / dataFolderName 不同，隔离完整。
4. **minimax 默认不注册全局快捷键**：`getDefaultShortcut()` 返回空对象，只有截图流程或用户自定义快捷键时才注册，不会在 Wayland 启动时触发门户弹窗。
5. **zcode 深链为上游共用限制**：asar 中没有运行时协议注册，`zcode://` 只由 desktop 文件声明，两版无法在包级拆分；保留“后安装者持有 handler”的现状并在此记录。
6. **kimi-work / kimi-code 旧包无需新增 conflicts**：cn 包只占用带 `-cn` 的独立命令、desktop 与安装前缀，与旧单包无文件重叠。
7. **仓库卫生**：`.gitignore` 补齐 `/workbuddy-*/*.tgz`，避免国际版构建下载物被误提交。
8. **第二轮升级与复审**：4 个包无条件升级并构建通过；QoderWake 两版状态目录 / 端口隔离实测正常；发现并修复 qoder 两版 desktop 中重复的 scheme 声明（`desktop-file-validate` 不再有重复项警告）；另补查 5 个无自动探针的包，均为最新。

## 第三轮：国内 / 国际版区分度审查（2026-11-18）

逐对核对图标、登录（区域）、名称与其他身份字段。结论如下。

| 包对 | 名称 / 桌面项 | 图标 | 登录 / 区域 | 结论 |
| --- | --- | --- | --- | --- |
| qoder-agent / qoder-cn-agent | `Qoder` / `Qoder CN`，desktop id、`StartupWMClass` 均不同 | 512 png sha256 不同 | `dataDirectoryName` `com.qoder.app.stable` / `com.qodercn.app.stable`；协议 `qoder` / `qoder-cn` | 完整分离 |
| qoder-ide / qoder-cn-ide | `appId`、desktop、`StartupWMClass` 不同 | 图像不同（sha256 不同） | `product.json` 的 `appId` / `dataFolderName` / 协议 / update / license / privacy 域名全部不同 | 完整分离 |
| trae-ide / trae-cn-ide | `Trae` / `Trae CN`，`StartupWMClass` `Trae` / `Trae-cn` | **字节相同**（均为上游 `code.png`） | userData `Trae` / `Trae CN`，协议 `trae` / `trae-cn` | 图标无区分 → 修复；深链未声明 → 修复 |
| workbuddy / workbuddy-intl | `WorkBuddy` / `WorkBuddy AI` | 图像相同，但两版 desktop 名不同；intl 仅 256px | 域名 `workbuddy.cn` / `workbuddy.ai`、`dataFolderName` `.workbuddy` / `.workbuddy-ai` | 完整分离 |
| kimi-code-intl-bin / -cn-bin | `kimi-code-app-intl` / `-cn`，desktop 不同 | CN 带角标，图像不同 | 同 deb + `patch-region.js`：协议 `kimi-code` / `kimi-code-cn`、API host、区域常量 | 完整分离 |
| kimi-work-intl-bin / -cn-bin | `kimi-desktop-intl` / `-cn`，desktop 不同 | 图像不同 | 区域常量 `overseas` / `china` 钉死 | 完整分离 |
| minimax-code-intl / -cn | `name` 不同，desktop 不同 | 图像不同 | 独立 `--user-data-dir`，intl 区域改 overseas | 完整分离 |
| mimo-desktop-bin / -intl-bin | 官方两个 deb，产品名 / desktop 不同 | 图像不同 | 官方独立 deb，URI scheme 不同 | 完整分离 |
| catpaw / catpaw-cn | `catpaw` / `catpaw-cn` | 图像不同 | `APP_ID` `com.catx.catpaw.overseas` / 国内对应值 | 完整分离 |
| zcode-intl-bin / zcode-cn-bin | `ZCode` / `ZCode（国内版）`，desktop id 不同 | **字节相同** | 同一 asar；CN 由 `patch.cjs` 把 BigModel/智谱设为默认并固定中文；user data 目录独立；`zcode://` 两版共用（上游限制） | 图标无区分 → 修复 |
| qoderwake-bin / qoderwake-cn-bin | `QoderWake` / `QoderWake 国内版` | **字节相同**；console SVG 已区分（`qoderwake-icon-cn.svg`） | 不同上游产物（`download.qoder.com` / `ide.qoder.com.cn`）；状态目录 `~/.qoderwake` / `~/.qoderwake-cn`，端口 19820 / 19830；区域由构建期常量固定（见下文） | 图标无区分 → 修复 |

### 本轮修复项

- **F1 Trae 深链**：`trae.desktop` 的 `MimeType` 增加 `x-scheme-handler/trae`，`trae-cn.desktop` 增加 `x-scheme-handler/trae-cn`（与两版 `product.json` 的 `urlProtocol` 一致），否则注册深链后 `xdg-open` 找不到处理程序。
- **F2 国内版图标角标**（用户决定：仿照 kimi 加角标）：
  - `trae-cn-ide`：新增 `makedepends=('imagemagick')`，从上游 512 png 生成 16/24/32/48/64/128/256/512 各尺寸并合成角标，安装到对应 hicolor 目录（原仅 512）。
  - `zcode-cn-bin`：对解包出的每个尺寸 png 合成角标后再安装为 `zcode-cn.png`。
  - `qoderwake-cn-bin`：对 512 与 128 两张源图分别合成角标。
  - 角标规范：右下角圆角方块，底色 `#C8102E`，白色粗体 `CN`；宽度为图像宽度 38%，距右边与下边各 6%，小尺寸（≤24px）按比例缩小。
- **F3 `kimi-work-bin` 标记 legacy**：PKGBUILD 头部注释与 README 注明“早期通用包，不锁定区域，建议改用 `kimi-work-intl-bin` / `kimi-work-cn-bin`”；不新增 conflicts，避免破坏现有用户。
- **F4 记录上游限制**：`zcode://` 两版共用；不强行二进制 patch。
- **F5 QoderWake 区域固定（补充核实）**：两版二进制都内置了 `global` / `cn` 两张区域表，所以 URL 集合看起来相同，但实际区域由构建期常量 `Cs()` 决定：国际版为 `` return`global`?… ``（base `https://qoder.com`），国内版为 `` return`cn`?… ``（base `https://qoder.com.cn`）；`homeDirName`、`binaryName`、console 的 docs/pricing 链接也随该常量切换，与登录账号无关，配置项里没有任何 region/endpoint 覆盖。为防止上游以后把区域改成运行时判定，两个 PKGBUILD 新增 `check()`：用 `grep -a` 断言二进制中的区域选择器分别为 `global` / `cn`，否则构建失败。Bun 打包的 250MB 可执行文件不做字节级改写，避免破坏内嵌 JS。

### 第三轮验证步骤

1. `trae-cn-ide`、`zcode-cn-bin`、`qoderwake-cn-bin` 执行 `makepkg -f`，构建通过且产物清理。
2. 比对：国际版图标 sha256 不变；国内版新图标与上游不同，且各尺寸存在。
3. `desktop-file-validate` 全绿；`trae-cn.desktop` 的 `MimeType` 含 `x-scheme-handler/trae-cn`，`trae.desktop` 含 `x-scheme-handler/trae`。
4. 三个包 `.SRCINFO` 重新生成并与 PKGBUILD 一致。
5. 所有改动只提交 GitHub，不推 AUR。
