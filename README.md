# myaur

维护 AUR（Arch User Repository）包的仓库：一个目录对应一个包。

## 包清单

| 包名 | 版本 | 上游 | 状态 |
|---|---|---|---|
| qoder-agent | 0.5.3 | https://qoder.com/ | 已构建（2026-11-04） |
| qoder-cn-agent | 0.5.3 | https://qoder.cn | 已构建（2026-11-04） |
| qoder-ide | 1.38.0 | https://qoder.com/ | 已推送 AUR（2026-11-03） |
| qoder-cn-ide | 1.38.0 | https://qoder.cn | 已推送 AUR（2026-11-03） |
| gw2api-bin | 4.27.0 | https://github.com/zexadev/gemini-web2api-go | 已构建（2026-11-04） |
| catpaw-cn | 2026.1016.1131 | https://s3plus.meituan.net/catpaw-external-resources/ide/win32-x64/stable/ | 已构建（2026-11-04） |
| catpaw | 2026.0929.1948 | https://s3-fra01-eu.mykeeta.net/catpaw-overseas/ide/win32-x64/stable/ | 已构建（2026-11-04） |
| trae-ide | 2.3.99397 | https://www.trae.cn/ | 已构建（2026-11-04） |
| trae-cn-ide | 2.3.99936 | https://www.trae.cn/ | 已构建（2026-11-04） |
| workbuddy-agent | 5.6.2.40046327_c7b525f3 | https://www.workbuddy.cn/app | 已推送 AUR（2026-11-03） |
| workbuddy-intl-agent | 5.9.4.42593613_fa0a0901 | https://www.workbuddy.ai | 已推送 AUR（2026-11-03） |

## 上游更新检测

`scripts/check-upstream-updates.py` 逐一探测上表 11 个产品的官方发布通道，与各包
`PKGBUILD` 的 `pkgver` 比较。只依赖 Python 标准库，无需安装任何包。

```bash
python3 scripts/check-upstream-updates.py            # 表格输出
python3 scripts/check-upstream-updates.py --json out.json
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
| gw2api-bin | GitHub Releases API |
| trae-ide / trae-cn-ide | 官方 icube 版本清单，取 Linux 构建号 |

## GitHub Actions 自动化（评估结论）

`.github/workflows/upstream-check.yml` 每 2 天跑一次探测，发现更新或探测失败时在
仓库里创建/更新一个 `upstream-check` Issue；全部为最新时自动关闭该 Issue。

**能做**：

- 定时探测、结果通知：完全可行。公开仓库不计费，runner 自带 Python 与 `gh`。
- 手动触发（`workflow_dispatch`）：可直接在 Actions 页面跑一次。
- 自动化提交 PR（改 `pkgver`、`source`、校验和）：技术上可行，但需要额外脚本把
  探测结果回写 PKGBUILD，并处理 `.SRCINFO` 生成与 `makepkg` 校验。

**不能直接做（或代价过高）**：

- 自动发布到 AUR：需要把 AUR 私钥放进仓库 Secret，且每个包都要跑一次
  `makepkg`/`namcap`，属于「发布」动作，按本仓库规则必须人工确认。
- 在 runner 上完整构建这 11 个包：单个 Electron 包解包 + 打包在 200–500 MB 量级，
  11 个包串行会触及单 job 6 小时上限与磁盘配额，且 `catpaw`/`catpaw-cn` 还要用
  `node-gyp` 重编原生模块，成本远高于本地构建。
- 长期无人值守：公开仓库的 scheduled workflow 在 60 天无仓库活动后会被自动禁用，
  需要有人偶尔提交或手动启用。

结论：**探测与通知交给 GitHub Actions，构建与 AUR 发布留在本地人工执行**。
workflow 只用 `issues: write` 权限，不接触任何凭据，也不在 CI 里构建产物。
