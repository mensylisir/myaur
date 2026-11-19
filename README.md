# myaur

维护 AUR（Arch User Repository）包的仓库：一个目录对应一个包。

## 包清单

| 包名 | 版本 | 上游 | 状态 |
|---|---|---|---|
| qoder-agent | 0.5.14 | https://qoder.com/ | 已推送 AUR（2026-11-18 升级；pkgrel 1 去重 desktop 中重复的 qoder 深链声明） |
| qoder-cn-agent | 0.5.14 | https://qoder.cn | 已推送 AUR（2026-11-18 升级；上游 CN 图标自带折角标记，不再额外加角标） |
| qoder-ide | 1.40.1 | https://qoder.com/ | 已推送 AUR（2026-11-16） |
| qoder-cn-ide | 1.40.1 | https://qoder.cn | 已推送 AUR（2026-11-13） |
| qoderwake-bin | 1.2.20 | https://qoder.com/ | 已推送 AUR（2026-11-18 升级；pkgrel 3 国际版圆形 INTL 角标；pkgrel 2 构建期断言区域固定为 global） |
| qoderwake-cn-bin | 1.2.20_cn | https://qoder.cn | 已推送 AUR（2026-11-18 升级；pkgrel 5 国内版圆形 CN 角标，构建期断言区域固定为 cn） |
| mimo-desktop-bin | 26.1116.161705 | https://mimo.xiaomimimo.com/desktop/ | 已推送 AUR（2026-11-18，x86_64；pkgrel 5 国内版圆形 CN 角标；pkgrel 2 补 mesa、修正 sandbox 权限与 AppArmor 缓存清理） |
| mimo-desktop-intl-bin | 26.1116.161705 | https://mimo-ai.xiaomimimo.com/desktop/ | 已推送 AUR（2026-11-18，x86_64；官方海外 Linux deb 重打包，国际版圆形 INTL 角标，可与国内版并存） |
| zcode-intl-bin | 3.18.2_10443 | https://zcode.z.ai/ | 已推送 AUR（2026-11-18；官方 Linux deb 重打包，保留 Z.ai 默认与系统语言；pkgrel 2 国际版圆形 INTL 角标） |
| zcode-cn-bin | 3.18.2_10443 | https://zcode.z.ai/cn | 已推送 AUR（2026-11-18；同一官方 deb 在包层切分，BigModel 默认、中文界面、独立数据目录，可与国际版并存；pkgrel 4 国内版圆形 CN 角标） |
| gw2api-bin | 4.30.0 | https://github.com/zexadev/gemini-web2api-go | 已推送 AUR（2026-11-18 升级；新增 `stream_idle_timeout_sec` 为运行时配置项，打包方式不变） |
| apifox-appimage-bin | 2.8.55 | https://apifox.com/ | 已推送 AUR（2026-11-18；官方 Linux AppImage 重打包，自带 Electron 37。AUR 的 `apifox-bin` 归他人所有，故用此名） |
| kilo-desktop-bin | 1.0.0.20261117 | https://kilo.ai | 已推送 AUR（2026-11-19；Anaconda Kilo Desktop 官方 deb 重打包，pkgver 追加 deb 构建日期） |
| claudemom | 0.1.9 | https://github.com/BigPizzaV3/ClaudeMom | 已推送 AUR（2026-11-19，x86_64；上游只发布 macOS/Windows 安装包，从 tag 源码编译 Tauri 2；自带 sherpa-onnx 静态库避免构建期联网，并显式补齐 cargo 漏传的 zstd/ring/sqlite3 静态库链接参数） |
| catpaw-cn | 2026.1030.1130 | https://s3plus.meituan.net/catpaw-external-resources/ide/win32-x64/stable/ | 已推送 AUR（2026-11-09） |
| catpaw | 2026.1111.1938 | https://s3-fra01-eu.mykeeta.net/catpaw-overseas/ide/win32-x64/stable/ | 已推送 AUR（2026-11-12，pkgrel 1） |
| trae-ide | 2.3.103560 | https://www.trae.cn/ | 已推送 AUR（2026-11-18 升级；pkgrel 3 国际版圆形 INTL 角标；pkgrel 2 补 x-scheme-handler/trae 深链声明） |
| trae-cn-ide | 2.3.103559 | https://www.trae.cn/ | 已推送 AUR（2026-11-18；pkgrel 4 国内版圆形 CN 角标并安装多尺寸；pkgrel 2 补 x-scheme-handler/trae-cn 深链声明） |
| workbuddy-agent | 5.11.3.43806934_ecace0f7 | https://www.workbuddy.cn/app | 已推送 AUR（2026-11-18；Windows 包 payload + 官方国内 deb 运行时，流程与 intl 一致；Wayland 下预置空快捷键避免 Add Keyboard Shortcuts 弹窗，并带 GPU/Wayland IME 启动参数） |
| workbuddy-intl-agent | 5.11.4.44121853_0026dff0 | https://www.workbuddy.ai | 已推送 AUR（2026-11-18；Windows 包 payload + 国内 deb 的定制 Electron/运行时，shadow asar 装配，修复 CREDENTIAL_BOOTSTRAP_FAILED；pkgrel 2 恢复 5.9.4 的 Wayland 快捷键防护与 GPU/IME 启动参数；pkgrel 3 将深链改为上游国际版实际注册的 workbuddy-ai，避免与国内版抢占 workbuddy://） |
| kimi-work-bin | 3.2.27 | https://www.kimi.com/products/kimi-work | 已推送 AUR（2026-11-13，x86_64；启动命令 kimi-work）；LEGACY：不锁定区域，建议改用 kimi-work-intl-bin / kimi-work-cn-bin |
| minimax-code-bin | 0.7.7 | https://agent.minimax.cn/download | 已推送 AUR（2026-11-13，x86_64） |
| kimi-code-intl-bin | 1.3.5 | https://code.kimi.ai/ | 已推送 AUR（2026-11-13；x86_64；命令 kimi-code，区域固定 global，Wayland 下禁用全局快捷键 portal 避免弹窗） |
| kimi-code-cn-bin | 1.3.5 | https://code.kimi.com/ | 已推送 AUR（2026-11-13；x86_64；命令 kimi-code-cn，区域固定 mainland-cn，Wayland 下禁用全局快捷键 portal 避免弹窗） |
| kimi-work-intl-bin | 3.2.27 | https://www.kimi.ai/products/kimi-work | 已推送 AUR（2026-11-13；x86_64；命令 kimi-work，区域固定 overseas，默认关闭 launcher 快捷键） |
| kimi-work-cn-bin | 3.2.27 | https://www.kimi.com/products/kimi-work | 已推送 AUR（2026-11-13；x86_64；命令 kimi-work-cn，区域固定 china，默认关闭 launcher 快捷键） |
| minimax-code-intl-bin | 3.1.16 | https://code.minimax.io/ | 已推送 AUR（2026-11-16，x86_64；命令 minimax-code，baseUrl agent.minimax.io，注册 minimax 深链，托盘菜单可退出；安装包取自官方镜像 filecdn.minimax.chat） |
| minimax-code-cn-bin | 3.1.16 | https://code.minimax.cn/ | 已推送 AUR（2026-11-16，x86_64；命令 minimax-code-cn，baseUrl agent.minimax.cn，注册 minimax-cn 深链，托盘菜单可退出） |
| appclone-bin | 1.1.2 | https://github.com/mensylisir/appclone | 已推送 AUR（2026-11-17） |
| dumate-app-bin | 1.0.92 | https://www.dumate.cn/ | 已推送 AUR（2026-11-14，x86_64；官方 deb 重打包，版本化 URL；与 AUR 已有 dumate-bin 功能相同） |

## 打赏

如果这些包省了你的时间，可以请我喝杯咖啡。

| 支付宝 | 微信 |
|---|---|
| <img src="docs/assets/donate-alipay.jpg" width="260" alt="支付宝收款码"> | <img src="docs/assets/donate-wechat.jpg" width="260" alt="微信收款码"> |

## 上游更新检测

`scripts/check-upstream-updates.py` 逐一探测上表各产品的官方发布通道，与各包
`PKGBUILD` 的 `pkgver` 比较。只依赖 Python 标准库，无需安装任何包。
`dumate-app-bin` 的上游只公布 `-latest.deb` 指针，需要下载 deb 读 control 才能拿到
版本，暂未纳入自动探测。

```bash
python3 scripts/check-upstream-updates.py            # 表格输出
python3 scripts/check-upstream-updates.py --json out.json
SMTP_PASS=<QQ 邮箱授权码> python3 scripts/check-upstream-updates.py --mail
```

退出码：`0` 全部为最新；`1` 有包待更新；`2` 至少一个探测失败（网络或协议变化）。

探测入口（均为官方渠道，无需登录）：

| 包 | 探测方式 |
|---|---|
| catpaw / catpaw-cn | 官方 update gateway（`ide-type: CatPaw_Desk`，返回 204 表示已最新） |
| workbuddy-intl-agent / workbuddy-agent | 官方 `/v2/update?platform=...` 接口 |
| qoder-agent / qoder-cn-agent | electron-builder 的 `latest-linux.yml` |
| qoder-ide | `center.qoder.sh` 更新接口 |
| qoder-cn-ide | RPM lead 的 NEVRA（HTTP Range 只取前 96 字节） |
| qoderwake-bin / qoderwake-cn-bin | 官方 channel `manifest.json` 的 `latest` 与 Linux amd64 归档 sha256 |
| mimo-desktop-bin | 官方 `latest` deb 的 control 归档（HTTP Range 取前 2 MiB，读 `Version`） |
| mimo-desktop-intl-bin | 同上，取海外 `mimodesktopai` 通道 |
| zcode-intl-bin / zcode-cn-bin | 官方下载页的 linux-x64 deb 链接，再读 control 归档的 `Version`（含 Debian revision） |
| gw2api-bin | GitHub Releases API |
| apifox-appimage-bin | 官方 `download/latest.yml`（与 Linux AppImage 同一发布版本） |
| kilo-desktop-bin | 官方 `latest` deb（control `Version` 恒为 1.0.0，再拼上 Last-Modified 日期） |
| claudemom | GitHub 版本 tag（上游不发 Linux 产物，也没有 release 版本语义） |
| trae-ide / trae-cn-ide | 官方 icube 版本清单，取 Linux 构建号 |

## 邮件通知（GitHub Actions）

`.github/workflows/upstream-check.yml` 每 2 天 03:00 UTC（也可手动触发）运行探测。
有包待更新或探测失败时，job 以非 0 退出，GitHub 会把「workflow 失败」的邮件发到
触发该定时任务的账号（即最后修改 `cron` 那一行的提交者，当前是仓库维护者），
无需配置任何 SMTP 凭证。全部为最新时 job 成功，不发送任何邮件。
不再创建 Issue，也不在 CI 里构建或发布。

可选：如果还想额外用 SMTP 直接发信（例如发给别的地址），在仓库
`Settings → Secrets and variables → Actions` 配置下表；不配置也不影响上面的失败通知。

| Secret | 说明 |
|---|---|
| `SMTP_HOST` | 可留空，默认 `smtp.qq.com` |
| `SMTP_PORT` | 可留空，默认 `465`（SSL） |
| `SMTP_USER` | 发件邮箱，默认 `710080675@qq.com` |
| `SMTP_PASS` | 该发件邮箱的 SMTP 授权码（QQ 邮箱需在设置里生成，不是登录密码） |
| `MAIL_TO` | 收件地址，默认 `710080675@qq.com` |

未配置 `SMTP_PASS` 时脚本跳过 SMTP 发信，探测本身照常执行。
GitHub 自带通知依赖该账号在 `Settings → Notifications` 里没有关闭 Actions 邮件，
且账号主邮箱是 `710080675@qq.com`。

**为什么不在 CI 里自动更新/发布**：

- 自动发布 AUR 需要把私钥放进仓库 Secret，且属于「发布」动作，按仓库规则必须人工确认。
- runner 上完整构建这些 Electron 包会触及单 job 6 小时上限与磁盘配额。
- 公开仓库的 scheduled workflow 在 60 天无活动后会被自动禁用。

结论：**CI 只负责探测与邮件提醒，构建与 AUR 发布留在本地人工执行**。
workflow 只有 `contents: read` 权限。
