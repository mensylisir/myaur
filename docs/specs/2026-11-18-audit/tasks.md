# 任务清单：AUR 包全量复审（2026-11-18）

## T1 机械检查（已完成）

- [x] 27 个 `.SRCINFO` 与 `makepkg --printsrcinfo` 一致
- [x] 所有 `*.sh` / `*.install` 通过 `bash -n`
- [x] 所有 desktop 通过 `desktop-file-validate`（仅 hint/warning）
- [x] README 版本与 PKGBUILD 一致

## T2 深链协议核实

- [x] WorkBuddy：确认上游 `cli/product.json` 国内 `deepLinkSchemes=["workbuddy"]`、国际 `["workbuddy-ai"]`；国际版 desktop 原先误写 `workbuddy`，已改为 `workbuddy-ai`
- [x] minimax：国内 desktop `minimax-cn`、国际 `minimax`，与两版区域补丁一致，无需改动
- [x] zcode：app 内无 `setAsDefaultProtocolClient`，仅由 desktop MimeType 决定；`zcode://` 为上游共用，已在 spec 记录为上游限制
- [x] qoder / trae：两版协议分别为 `qoder`/`qoder-app` 与 `qoder-cn`/`qoder-cn-app`、`trae`/`trae-cn`，已分离
- [x] catpaw、mimo：无运行时协议注册，无冲突
- [x] 根据证据完成 desktop MimeType 修改（仅 WorkBuddy 国际版）

## T3 Wayland 全局快捷键核实

- [x] catpaw / catpaw-cn：asar 中仅 import，无 `globalShortcut.register` 调用
- [x] zcode-intl-bin / zcode-cn-bin：asar 中无 `globalShortcut`
- [x] mimo-desktop-bin / mimo-desktop-intl-bin：最新 26.1116 两版 asar 均无 `globalShortcut`
- [x] minimax-code-cn-bin / minimax-code-intl-bin：默认 `getDefaultShortcut()` 返回 `{}`，仅截图流程或用户自定义时注册，启动不触发门户
- [x] qoder-agent / qoder-cn-agent / qoder-ide / qoder-cn-ide：无 `globalShortcut`
- [x] trae-ide / trae-cn-ide：launcher 预置 `floatingChat.enabled=false`，全局快捷键仅在用户启用/截图时注册
- [x] workbuddy 两版：`shortcut-state.json` 读写路径确认为 `userData/shortcut-state.json`，国内 `~/.workbuddy/app`、国际 `~/.workbuddy-ai/app`，与 launcher 一致
- [x] 除 kimi-code 已带 `--disable-features=GlobalShortcutsPortal` 外，其余包无需新增该参数

## T4 数据目录与窗口类核实

- [x] qoder-ide / qoder-cn-ide：`dataFolderName` 分别为 `.qoder` / `.qoder-cn`
- [x] qoder-agent / qoder-cn-agent：`dataDirectoryName` 与 `protocolScheme` 均不同
- [x] trae-ide / trae-cn-ide：`dataFolderName` 分别为 `.trae` / `.trae-cn`
- [x] catpaw / catpaw-cn：`package.json` name 分别为 `catpaw-overseas` / `catpaw-moon`，userData 分离
- [x] minimax-code-*：`package.json` name 已改写为 `minimax-code-cn` / `minimax-code-intl`，userData 分离
- [x] mimo-*：官方两包 productName 分别为 `Xiaomi MiMo` / `Xiaomi MiMo AI`，dataFolderName 不同
- [x] workbuddy-*：product.json 的 `dataFolderName` 为 `.workbuddy` / `.workbuddy-ai`，与 launcher 路径一致

## T5 冲突声明核实

- [x] `kimi-work-bin` 与 `kimi-work-cn-bin`：命令/desktop/安装前缀均不同，无文件重叠，无需 conflicts
- [x] `kimi-code-desktop-bin` 与 `kimi-code-cn-bin`：cn 仅占 `kimi-code-cn` 前缀，无文件重叠，无需 conflicts
- [x] 未发现需要补 conflicts 的包

## T6 仓库卫生

- [x] `.gitignore` 已覆盖 workbuddy 两目录的 `.tgz`（改为 `/workbuddy-*/*.tgz`）
- [x] 确认无 `.deb` / `.zip` / `.tgz` / `.exe` / `.rpm` 被 git 跟踪

## T7 修复与验证

- [x] 修复 `workbuddy-intl-agent/workbuddy-international.desktop` 的深链为 `workbuddy-ai`
- [x] 更新 PKGBUILD sha256 与 `pkgrel=3`，重新生成 `.SRCINFO`
- [x] `makepkg -f` 构建通过（5.11.4.44121853_0026dff0-3，x86_64，构建后已清理产物）
- [x] 清理构建产物与临时下载（`src/`、`pkg/`、`.pkg.tar.zst`、`/tmp/mimo-check` 等）
- [x] 复查全部机械检查（27 包 SRCINFO 同步、脚本语法通过、desktop 仅 hint）
- [x] 运行 `python3 scripts/check-upstream-updates.py`：Qoder Agent 国内 0.5.14、QoderWake 国际 1.2.20、QoderWake 国内 1.2.20-cn、Trae 国际 2.3.103560 有更新（本轮不升级）
- [x] 提交 GitHub（不推 AUR）：`25458a5` 已推送 `origin/main`

## T8 第二轮：上游升级 + 继续审查（已完成）

- [x] `python3 scripts/check-upstream-updates.py` 全量探测：除 4 个待升级包外全部为最新
- [x] `qoder-cn-agent` 0.5.13 → 0.5.14（新 rpm sha256 校验通过，Electron 43，`makepkg -f` 构建通过）
- [x] `qoderwake-bin` 1.2.18 → 1.2.20（x86_64/aarch64 sha256 更新，构建通过）
- [x] `qoderwake-cn-bin` 1.2.18-cn → 1.2.20-cn（`pkgver=1.2.20_cn`，构建通过）
- [x] `trae-ide` 2.3.99397 → 2.3.103560（b2sums 更新，构建通过；`dataFolderName=.trae`、`urlProtocol=trae` 未变；ckg 内置 gcc 库仍存在）
- [x] 运行 1.2.20 两个 QoderWake 二进制于临时 HOME：状态目录分别为 `~/.qoderwake` / `~/.qoderwake-cn`，端口 19820 / 19830，隔离正常
- [x] 发现并修复 qoder 两个 agent 包的上游 desktop 重复 scheme：intl `qoder`/`qoder-app`、cn `qoder-cn` 各重复两次，`prepare()` 中去重
- [x] `qoder-agent` 重新构建 0.5.12-2；`qoder-cn-agent` 0.5.14-1 重新构建，两份 desktop 均通过 `desktop-file-validate` 且无重复
- [x] `qoder-ide` / `qoder-cn-ide` 1.40.1 全量构建验证通过；desktop scheme 分别为 `qoder`+`qoder-ide` / `qoder-cn`+`qoder-cn-ide`，无重复
- [x] 补查无自动探针的包：kimi-code 1.3.5、kimi-work 3.2.27（官方 latest 接口）、minimax-code 0.7.7（npm latest）、appclone 1.1.2（GitHub）、dumate 1.0.92（官方 latest deb 控制信息），均是最新
- [x] `.gitignore` 补 `/trae-ide/Trae-linux-*.tar.gz`
- [x] 清理全部 `src/`、`pkg/`、`*.pkg.tar.zst` 与本轮下载归档
- [x] 复查：27 包 `.SRCINFO` 同步、全部 desktop 无 error、无大文件待提交

## T9 第三轮：国内 / 国际版区分度审查与修复（待执行）

- [x] 逐对核对 11 组双版包的图标 / 登录 / 名称 / 协议（结论见 spec.md 第三轮表格）
- [x] F1 `trae-ide/trae.desktop` 增加 `x-scheme-handler/trae`；`trae-cn-ide/trae-cn.desktop` 增加 `x-scheme-handler/trae-cn`
- [x] F2 `trae-cn-ide` 增加 `imagemagick` makedepends，生成 16~512 带 CN 角标图标并安装全部尺寸（构建通过，512 图标已目视确认）
- [x] F2 `zcode-cn-bin` 对每个尺寸图标合成 CN 角标（构建通过，16/512/1024 已确认）
- [x] F2 `qoderwake-cn-bin` 对 512 / 128 图标合成 CN 角标（构建通过，512 图标已目视确认）
- [x] F3 `kimi-work-bin` 头部注释与 README 标记 legacy（不锁定区域，建议改用 -intl / -cn）
- [x] F4 在 spec 记录 zcode 深链共用、qoderwake URL 集相同两项上游限制
- [x] 三个改动包 `makepkg -f` 构建通过；图标 sha256 比对（intl 不变、cn 变化）；desktop 校验全绿
- [x] 三个包 `.SRCINFO` 同步；清理构建产物
- [x] 提交并推送 GitHub（不推 AUR）：`ee11496` 已推送 `origin/main`

## 验收标准

- 所有包 `.SRCINFO` 同步、脚本语法通过、desktop 无 error。
- 每一对国内 / 国际包在 `/opt` 前缀、命令、desktop id、Icon、StartupWMClass、userData、深链协议上均有明确结论（分离或记录为上游限制）。
- 所有存在 `globalShortcut` 的 Electron 包在 Wayland 下不再触发 GNOME 授权弹窗，或已记录无法修复的上游限制。
- 改动后的包构建通过且无构建产物残留。
