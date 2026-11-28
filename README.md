# myaur

维护 AUR（Arch User Repository）包的仓库：一个目录对应一个包。

## 包清单

| 包名 | 版本 | 上游 | 状态 |
|---|---|---|---|
| qoder-agent | 0.5.21 | https://qoder.com/ | 已推送 AUR（2026-11-28 升级；保留 preload 修复：移除 argv 中 --require/--app、保留 realpathSync.native） |
| qoder-cn-agent | 0.5.21 | https://qoder.cn | 已推送 AUR（2026-11-28 升级；保留 preload 修复；上游 CN 图标自带折角标记，不额外加角标） |
| qoder-ide | 1.42.1 | https://qoder.com/ | 已推送 AUR（2026-11-28 升级；pkgrel 重置为 1，连同 preload / `--app` argv 修复一并发布；探测接口 CDN 节点滞后时以 `release/latest` RPM 的 NEVRA 为准） |
| qoder-cn-ide | 1.42.1 | https://qoder.cn | 已推送 AUR（2026-11-28 升级；pkgrel 重置为 1，连同 preload / `--app` argv 修复一并发布） |
| qoderwake-bin | 1.2.27 | https://qoder.com/ | 已推送 AUR（2026-11-28 pkgrel 2：区域断言此前只有函数定义未调用，已挂到 prepare，串区会直接构建失败；产物中确认 region 常量为 global；保留 INTL 角标） |
| qoderwake-cn-bin | 1.2.27_cn | https://qoder.cn | 已推送 AUR（2026-11-28 pkgrel 2：区域断言此前只有函数定义未调用，已挂到 prepare，串区会直接构建失败；产物中确认 region 常量为 cn；保留 CN 角标） |
| mimo-desktop-bin | 26.1120.201429 | https://mimo.xiaomimimo.com/desktop/ | 已推送 AUR（2026-11-20 升级；国内版圆形 CN 角标；上游图标改为 512px，按新尺寸派生多尺寸） |
| mimo-desktop-intl-bin | 26.1120.201429 | https://mimo-ai.xiaomimimo.com/desktop/ | 已推送 AUR（2026-11-20 升级，x86_64；官方海外 Linux deb 重打包，国际版圆形 INTL 角标，可与国内版并存） |
| zcode-intl-bin | 4.0.0_10870 | https://zcode.z.ai/ | 已推送 AUR（2026-11-24 pkgrel 2：asar 只保留 Z.ai 全球登录源，锁定国际账号；INTL 角标；语言跟随系统） |
| zcode-cn-bin | 4.0.0_10870 | https://zcode.z.ai/cn | 已推送 AUR（2026-11-24 pkgrel 5：asar 只保留 BigModel 登录源，锁定国内智谱账号；CN 角标；语言跟随系统） |
| zcode-zai-cn-bin | 4.0.0_10870 | https://zcode.z.ai/cn | 已推送 AUR（2026-11-24 新增：asar 只保留 Z.ai (CN) 登录源，锁定国内 Z.ai 账号；ZCN 角标；独立 /opt 与数据目录） |
| gw2api-bin | 4.33.0 | https://github.com/zexadev/gemini-web2api-go | 已推送 AUR（2026-11-26 升级；打包方式不变） |
| apifox-appimage-bin | 2.8.55 | https://apifox.com/ | 已推送 AUR（2026-11-18；官方 Linux AppImage 重打包，自带 Electron 37。AUR 的 `apifox-bin` 归他人所有，故用此名） |
| kilo-desktop-bin | 1.0.0.20261117 | https://kilo.ai | 已推送 AUR（2026-11-19；Anaconda Kilo Desktop 官方 deb 重打包，pkgver 追加 deb 构建日期） |
| claudemom | 0.1.14 | https://github.com/BigPizzaV3/ClaudeMom | 已推送 AUR（2026-11-24 升级；保留 launcher 路径、sherpa-onnx 1.13.8 静态库与 zstd/ring/sqlite3 链接参数） |
| catpaw-cn | 2026.1030.1130 | https://s3plus.meituan.net/catpaw-external-resources/ide/win32-x64/stable/ | 已推送 AUR（2026-11-09） |
| catpaw | 2026.1111.1938 | https://s3-fra01-eu.mykeeta.net/catpaw-overseas/ide/win32-x64/stable/ | 已推送 AUR（2026-11-12，pkgrel 1） |
| trae-ide | 2.3.106769 | https://www.trae.cn/ | 已推送 AUR（2026-11-26 升级；保留国际版圆形 INTL 角标；补 x-scheme-handler/trae 深链声明） |
| trae-cn-ide | 2.3.108162 | https://www.trae.cn/ | 已推送 AUR（2026-11-26 升级；保留 x86_64 归档、CN 角标与 trae-cn 深链声明） |
| workbuddy-agent | 5.11.3.43806934_ecace0f7 | https://www.workbuddy.cn/app | 已推送 AUR（2026-11-26：Windows payload 未变，deb 运行时升至 5.11.6、sandbox 5.13.3；Wayland 下预置空快捷键避免 Add Keyboard Shortcuts 弹窗，并带 GPU/Wayland IME 启动参数） |
| workbuddy-intl-agent | 5.11.7.44923190_525fde10 | https://www.workbuddy.ai | 已推送 AUR（2026-11-28 pkgrel 2：Windows payload 5.11.7，deb 运行时 5.11.6、sandbox 5.13.3；shadow asar 装配；IM 后端补丁的幂等判断收紧为只认后端工厂内的 linux 分支，避免上游出现同名字符串时误跳过；保留 Wayland 快捷键防护、GPU/IME 启动参数与 workbuddy-ai 深链） |
| kimi-work-bin | 3.2.29 | https://www.kimi.com/products/kimi-work | 已推送 AUR（2026-11-28 pkgrel 2，x86_64；启动命令 kimi-work；daimon 去 devDependencies 现带前置/后置断言，格式变动会直接构建失败）；LEGACY：不锁定区域，建议改用 kimi-work-intl-bin / kimi-work-cn-bin |
| minimax-code-bin | 0.8.0 | https://agent.minimax.cn/download | 已推送 AUR（2026-11-28 升级，x86_64） |
| kimi-code-intl-bin | 1.5.1 | https://code.kimi.ai/ | 已推送 AUR（2026-11-28 升级；x86_64；命令 kimi-code，区域固定 global，Wayland 下禁用全局快捷键 portal 避免弹窗；与国内版 deb 字节相同，按同一 sha256 校验） |
| kimi-code-cn-bin | 1.5.1 | https://code.kimi.com/ | 已推送 AUR（2026-11-28 升级；x86_64；命令 kimi-code-cn，区域固定 mainland-cn，Wayland 下禁用全局快捷键 portal 避免弹窗） |
| kimi-work-intl-bin | 3.2.29 | https://www.kimi.ai/products/kimi-work | 已推送 AUR（2026-11-28 pkgrel 2：字符串表 id 变更已适配（manual/lastEffective 15466/6565、resourcesPath 21706、appId/.desktop 6775/7472），并新增设备/账号区域 getter 固定——登录页与认证 URL 不再被系统区域带偏；区域固定 overseas，默认关闭 launcher 快捷键） |
| kimi-work-cn-bin | 3.2.29 | https://www.kimi.com/products/kimi-work | 已推送 AUR（2026-11-28 pkgrel 2：字符串表 id 变更已适配（manual/lastEffective 15466/6565、resourcesPath 21706、appId/.desktop 6775/7472），并新增设备/账号区域 getter 固定——登录页与认证 URL 不再被系统区域带偏；区域固定 china，默认关闭 launcher 快捷键） |
| minimax-code-intl-bin | 3.1.19 | https://code.minimax.io/ | 已推送 AUR（2026-11-28 pkgrel 2，x86_64；命令 minimax-code，baseUrl agent.minimax.io，注册 minimax 深链，托盘菜单可退出；区域改写后校验 .env.local 必须指向 agent.minimax.io；7z 解包前显式建输出目录） |
| minimax-code-cn-bin | 3.1.19 | https://code.minimax.cn/ | 已推送 AUR（2026-11-28 pkgrel 2，x86_64；命令 minimax-code-cn，baseUrl agent.minimax.cn，注册 minimax-cn 深链，托盘菜单可退出；新增断言：安装包 .env.local 必须指向 agent.minimax.cn，上游换通道会直接构建失败） |
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
| catpaw / catpaw-cn | 官方 `/api/gateway/ide/latest?platform=win32-x64`（旧 `/ide/update` 对任意版本都返回 204，无法探测；国内域名 `catx.nocode.cn`） |
| workbuddy-intl-agent / workbuddy-agent | 主程序是 Windows payload（pkgver 取 `版本_构建哈希`，哈希从下载 URL 的 `-<8hex>.exe` 解析，哈希变化也算更新）；同时对比官方国内 deb（`workbuddy-linux-x64-deb`，版本+构建哈希）与两个 npm 助手（`@tencent-ai/sandbox-cli-linux-x64` latest、`@tencent-ai/agent-harness-linux-x64` beta） |
| minimax-code-bin | npm registry `@minimax-ai/code` 的 latest |
| minimax-code-intl-bin / minimax-code-cn-bin | electron-builder `latest.yml`（Windows NSIS 安装包，两版共用同一官方镜像） |
| kimi-work-bin / kimi-work-intl-bin / kimi-work-cn-bin | electron-builder `latest.yml`（`kimi-img.moonshot.cn/app/upgrade`，Windows 安装包） |
| kimi-code-intl-bin / kimi-code-cn-bin | electron-builder `latest-linux.yml`（优先取 deb，国际 `cdn.kimi.ai` / 国内 `cdn.kimi.com`） |
| appclone-bin | GitHub Releases API |
| qoder-agent / qoder-cn-agent | electron-builder 的 `latest-linux.yml` |
| qoder-ide | `center.qoder.sh` 更新接口（多次取样取最新，CDN 节点滞后时回退到 `release/latest` RPM 的 NEVRA） |
| qoder-cn-ide | RPM lead 的 NEVRA（HTTP Range 只取前 96 字节） |
| qoderwake-bin / qoderwake-cn-bin | 官方 channel `manifest.json` 的 `latest` 与 Linux amd64 归档 sha256 |
| mimo-desktop-bin | 官方 `latest` deb 的 control 归档（HTTP Range 取前 2 MiB，读 `Version`） |
| mimo-desktop-intl-bin | 同上，取海外 `mimodesktopai` 通道 |
| zcode-intl-bin / zcode-cn-bin / zcode-zai-cn-bin | 官方下载页的 linux-x64 deb 链接，再读 control 归档的 `Version`（含 Debian revision） |
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
