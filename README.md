# myaur

维护 AUR（Arch User Repository）包的仓库：一个目录对应一个包。

## 包清单

| 包名 | 版本 | 上游 | 状态 |
|---|---|---|---|
| qoder-agent | 0.5.2 | https://qoder.com/ | 已构建（2026-11-02） |
| qoder-cn-agent | 0.5.2 | https://qoder.cn | 已构建（2026-11-02） |
| qoder-ide | 1.38.0 | https://qoder.com/ | 已构建（2026-11-02） |
| qoder-cn-ide | 1.38.0 | https://qoder.cn | 已构建（2026-11-02） |
| gw2api-bin | 4.26.0 | https://github.com/zexadev/gemini-web2api-go | 已构建（2026-11-02） |
| catpaw-cn | 2026.1016.0034 | https://s3plus.meituan.net/catpaw-external-resources/ide/darwin/stable/ | 已构建（2026-11-03） |
| trae-ide | 2.3.93439 | https://www.trae.cn/ | 待构建 |
| trae-cn-ide | 2.3.98528 | https://www.trae.cn/ | 待构建 |
| workbuddy-agent | 5.6.2.40046327_c7b525f3 | https://www.workbuddy.cn/app | 待构建 |
| workbuddy-intl-agent | 5.9.4.42593613_fa0a0901 | https://www.workbuddy.ai | 待构建 |

## 说明

- Qoder 四个包由原 AUR 包改名接续维护：`qoder-bin` → `qoder-agent`、`qoder-cn-bin` → `qoder-cn-agent`、`qoder-ide-bin` → `qoder-ide`、`qoder-cn-ide-bin` → `qoder-cn-ide`。安装后的命令与目录保持上游命名（`qoder`、`qoder-cn`、`qoder-ide`、`qoder-cn-ide`）。
- 构建验证使用 `makepkg -f --nodeps`（2026-11-02），未执行 clean chroot 与 `namcap`：当前环境缺少 `namcap`，`updpkgsums` 同样缺失（源码未变，校验和由上游文件直接计算）。
- Trae / WorkBuddy 四包因原 AUR 名已被占用而改名接续：`trae` → `trae-ide`、`trae-cn` → `trae-cn-ide`、`workbuddy` → `workbuddy-agent`、`workbuddy-international` → `workbuddy-intl-agent`。安装后的命令与目录保持上游命名。
- `catpaw-cn` 是非官方 Linux 移植：上游只发布 macOS DMG，包内用官方 Linux Electron 42.11.2、Node 24.18.0、CPython 3.12.13 与各原生模块的官方 Linux 预编译包替换 darwin 组件（node-pty/bufferutil/utf-8-validate 用官方源码本地编译），并生成 Linux 版 Skill 依赖清单。仅支持 x86_64；上游 Mach-O 的 `xlsx-sidecar` 不安装。构建命令：`SRCDEST=<缓存> makepkg -f --nodeps`（2026-11-03），全部 source 校验通过；`.SRCINFO` 由 `makepkg --printsrcinfo` 生成且重复生成无差异。当前环境缺 `namcap`/`updpkgsums`，校验和由 `sha256sum` 计算并经 makepkg 校验通过。
- `catpaw-cn` 的窗口标识实测为 `catpaw-moon`，桌面文件同名（`catpaw-moon.desktop`，`Icon`/`StartupWMClass` 均为 `catpaw-moon`），图标安装到 `hicolor/{16..512}x*/apps/catpaw-moon.png`；已用 GTK IconTheme 验证 16–512 全部可解析，Dash/任务栏不会再显示无图标占位。国际版计划使用 `catpaw-overseas`，两者数据目录分别为 `~/.meituan-catpaw` 与 `~/.catpaw-overseas`，可同时安装且不会在 Dash 中合并。
- `.specs/<包名>/` 存放维护计划（`spec.md` 与 `tasks.md`），仅作记录用途，不参与构建。
- `workbuddy-agent` 沿用原包的 `pkgver()` 联网查更新接口与 `sha256sums=SKIP`，不符合本仓库 AGENTS 的构建期不联网、校验和必须真实两条规则，发布前需先修正。
