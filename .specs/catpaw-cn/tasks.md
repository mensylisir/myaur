# Tasks: catpaw-cn

## T1 源文件与校验和 — 已完成
- 18 个下载源 sha256 全部写入 PKGBUILD，makepkg 校验全部 Passed（2026-11-02）。
- 15 个仓库内本地文件也写入真实 sha256（无 SKIP）。
- 验收：`sha256sum` 输出与 PKGBUILD 完全一致；dmg sha256 为 `3c931da843e32128e4e3431f50231fac38f3b6f1c2a850bc9e783cc4d4deb3cf`。

## T2 编写 convert.sh — 已完成
- `convert.sh` 包含解 dmg、Electron、负载复制、原生模块替换、runtimes manifest、paw、metadata 等步骤；另用 `patch-skill-manifests.js` 生成 Linux 版 Skill 依赖清单。
- 构建期无网络调用；原生模块用 `node-gyp --nodedir` 与官方 Linux 预编译包。
- 验收：`bash -n convert.sh` 通过；`makepkg` 内完整跑通。

## T3 编写 PKGBUILD 与桌面文件 — 已完成
- `build()` 只调用 `convert.sh`；`package()` 安装 `/opt/catpaw-cn`、`/usr/bin/catpaw-cn`、`catpaw-moon.desktop` 与 hicolor 16–512 图标。
- 桌面 id 使用上游 `catpaw-moon`，与 WM_CLASS 一致；国际版预留 `catpaw-overseas`。
- 验收：`SRCDEST=<缓存> makepkg -f --nodeps` 成功产出 `catpaw-cn-2026.1016.0034-1-x86_64.pkg.tar.zst`（2026-11-02）；`.SRCINFO` 重复生成 diff 为空。

## T4 运行态验证 — 已完成
- Electron `42.11.2` / modules `146` / linux x64；require node-pty、better-sqlite3、koffi、sharp、@napi-rs/canvas、bufferutil、utf-8-validate 全部成功。
- 全新 HOME 启动最终产物：`runtime-install.log` 记录 `pip.install.ok`、`ensure.done status=ready componentErrors=none`，Node `24.18.0` 原子安装成功，无 darwin/macosx wheel 报错。
- `resources/bin/paw --version` 输出 `妙手 2026.1016.0034 (linux/x64)`，退出码 0。
- 说明：该应用没有 `--version` 命令行开关（传参会直接启动 GUI），版本改用 `ELECTRON_RUN_AS_NODE=1` 与 product.json 验证。
- 图标：GTK IconTheme 能解析 `catpaw-moon` 的 16/24/32/48/64/128/256/512 全部尺寸；`desktop-file-validate` 无错误；X11 实测 WM_CLASS=`catpaw-moon`。

## T5 审查与文档 — 已完成
- 第一轮标准/对抗审查均 REJECTED，已修复：新增 `.gitignore`、本地文件真实校验和、`noextract` 用 `${pkgver}`、删除 Mach-O `spawn-helper`、清理 asar `integrity`、启动器补 `--no-sandbox --disable-dev-shm-usage`、license 文件更名、精简 depends、移除冲突的 URL scheme 注册。
- 第二轮标准审查 APPROVED；对抗审查 REJECTED，已修复：删除 `*.part` 残留并加入 `.gitignore`、`--no-sandbox` 与 DISCLAIMER 措辞对齐并删除不可用 `chrome-sandbox`、补 `libnotify` 依赖、repack 后 chmod 0644、放宽 runtime manifest 阈值、版本号由 PKGBUILD 变量传入、修正 appId 与 WM class 混称、DISCLAIMER 补 ffmpeg 说明。
- 第三轮复审确认修复项落地，另发现 DISCLAIMER 把本地编译的 node-pty/bufferutil/utf-8-validate 写成「预编译包」，已修正；`python` 可执行路径改为由 `PYTHON_VER` 推导；`.gitignore` 的归档规则收窄到 `catpaw-cn/`，避免误吞其它包的本地 source。
- 最终构建 `SRCDEST=/tmp/catpaw/srcdest makepkg -f --nodeps` 成功（2026-11-03 01:12，33 个 source 全部 Passed）；`.SRCINFO` 重复生成无差异。
- 最终产物复验：app.asar 0644、无 chrome-sandbox、unpacked integrity=0、payload sha256 与上游一致；manifest node 24.18.0 / python 3.12.13 且 bin 路径正确；原生模块全部 require 成功；WM_CLASS=catpaw-moon；GTK IconTheme 16–512 全部可解析。

## T6 提交与推送 — 已完成
- GitHub：`git push origin main`，`c70299a..e290fea`（2026-11-03）。
- AUR：`a1273b0` 推送到 `ssh://aur@aur.archlinux.org/catpaw-cn.git` 的 `master`（2026-11-03）；`git clone`、`list-repos` 与包页面均可验证。
- 推送结果已记录在 `README.md` 与提交信息中。

