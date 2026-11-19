# claudemom AUR 包：构建失败修复与发布

状态：待批准
日期：2026-11-19
涉及包：`claudemom`（从 `https://github.com/BigPizzaV3/ClaudeMom` tag `v0.1.9` 源码构建）

## 1. 问题

`makepkg -f` 在 `sherpa-onnx-sys v1.13.8` 的 **build script（构建脚本二进制）链接阶段**失败：

```
/usr/bin/ld.bfd: .../libzstd_safe-f27aa3d86c43113f.rlib(...): undefined reference to `ZSTD_getErrorName'
/usr/bin/ld.bfd: .../build_script_build...cgu.2.rcgu.o: undefined reference to `ZSTD_decompressStream'
error: could not compile `sherpa-onnx-sys` (build script) due to 1 previous error
==> ERROR: A failure occurred in build().
```

构建脚本依赖链 `sherpa-onnx-sys (build-deps) → zip/ureq → zstd-sys / ring`，链接 `build_script_build` 时 rustc 生成的 `cc` 命令行里 **没有** `-lzstd` 和 `-lring_core_0_17_14_`，只有对应的 `-L native=.../zstd-sys-*/out`、`-L native=.../ring-*/out`。

## 2. 已确认的事实（证据）

1. `sherpa-onnx-sys` 的 `-C link-arg=-fuse-ld=bfd` 已生效（链接行末尾出现 `-fuse-ld=bfd`，且 GNU ld 2.47 以最后一个 `-fuse-ld` 为准，实测确认）。
2. 失败日志 `/tmp/cm-makepkg.log` 中 `grep -- '-lzstd'` 命中 **0** 次；`zstd-sys-*/output`、`ring-*/output` 里 `cargo:rustc-link-lib=static=zstd` / `static=ring_core_0_17_14_` 确实存在。
3. 在同一 `srcdir`、同一 `RUSTFLAGS`、带 makepkg 的 `LDFLAGS`（`-Wl,--as-needed` 等）下，**增量**重链 `sherpa-onnx-sys` 构建脚本可以成功（`/tmp/repro-nold.log`、`/tmp/repro-ld.log` 均 exit 0），说明问题与 `LDFLAGS` 无关，只与全新构建时 build script 的链接参数有关。
4. 只删除 `target/release/build/sherpa-onnx-sys-*` 再构建，cargo 不会重新传递 `-l static=zstd`；但此时链接恰好成功（未拉入 zstd 目标文件）。因此这是一个**依赖构建状态的偶发失败**，不能靠"曾经构建成功"判定包可用。
5. 其他可复现环境因素已排除：磁盘配额（曾报 `Disk quota exceeded`，为 `/tmp` tmpfs 满，已清理 `/tmp/cm` 等临时目录，现 `/tmp` 使用率 14%）。

## 3. 结论（根因）

`cargo` 在编译 `sherpa-onnx-sys` 的 `build_script_build` 时，只传了 `-L native=`，没有传 `-l static=zstd` / `-l static=ring_core_0_17_14_`。全新构建时 `zip` 的 zstd 代码路径被拉入，链接即失败；增量构建时目标文件恰好未被拉入，才"看起来能过"。换链接器（bfd/lld）无法补齐缺失的 `-l`。

## 4. 修复方案（最小、确定）

修改唯一文件：[claudemom/PKGBUILD](file:///home/mensyli1/Documents/workspace/myaur/claudemom/PKGBUILD)

### 4.1 `build()`：显式补齐 `-lzstd` 与 `-lring_core_*`

实现时发现 `cargo build -p zstd-sys` 会让 cargo 的 feature resolver panic（`did not find features for (zstd-sys, NormalOrDev)`，因为 zstd-sys 只作为 build-dependency 出现），而 `-p ring` 正常。因此最终方案：

在 `npm ci` / `vite:build` 之后、正式 `cargo build` 之前插入：

```bash
cargo build --release --locked -p ring -p libsqlite3-sys
local _native="${srcdir}/native-libs"
install -d "${_native}"
find target/release/build -path '*/out/libring_core_*[0-9]_.a' \
  -exec install -m644 {} "${_native}/" \;
find target/release/build -path '*/out/libsqlite3.a' \
  -exec install -m644 {} "${_native}/" \;
_ringver="$(grep -A1 '^name = "ring"$' Cargo.lock \
  | sed -n 's/^version = "\(.*\)"$/\1/p' | head -1)"
_ringlib="ring_core_$(printf '%s' "${_ringver}" | tr '.' '_')_"
```

`RUSTFLAGS` 追加：

```bash
-C link-arg=-fuse-ld=bfd \
-C link-arg=-lzstd \
-C link-arg=${_native}/lib${_ringlib}.a \
-C link-arg=${_native}/libsqlite3.a
```

说明：

- 全新构建实测还发现最终二进制链接 `rusqlite` 时同样缺 `-lsqlite3`（报 `DSO missing from command line`），因此把 bundled 的 `libsqlite3.a` 一并按绝对路径传入。
- `-lzstd` 在链接 `sherpa-onnx-sys` 构建脚本时，cargo 已给出 `-L .../zstd-sys-*/out`，该目录内有 `libzstd.a`，会静态解析；其他链接行没有该路径时回退到系统 `libzstd.so`（`zstd` 加入 `makedepends`），`--as-needed` 下不会给最终二进制新增运行时依赖（`readelf -d` 已验证无 `libzstd` NEEDED）。
- `ring` 的静态库名随版本变化（0.17.14 → `ring_core_0_17_14_`），由 `Cargo.lock` 推导，避免写死。
- 传绝对路径而不是 `-l`：`-l` 会被 rustc 放在 rlib 之前，静态归档只能向左扫描，符号无法解析（实测 `ring` 因此失败）；`-C link-arg` 的路径位于 rlib 之后。
- 保留 `CARGO_PROFILE_RELEASE_STRIP=symbols` 和 `--remap-path-prefix`。

### 4.2 `check()`

沿用现有 `sherpa-onnx-sys` 版本断言，无需新增。

## 5. 验证步骤

1. 清理：`rm -rf claudemom/src claudemom/pkg claudemom/*.pkg.tar.zst`
2. 全新构建：`SRCDEST=/tmp/cmsrc makepkg -f`（必须从头解包），期望 exit 0。
3. `grep -- '-lzstd'` 在本次日志构建脚本链接参数中出现（可通过 `-v` 验证一次）。
4. 产物检查：`bsdtar -tf claudemom-0.1.9-1-x86_64.pkg.tar.zst`，确认 `/usr/bin/claudemom`、`/usr/lib/claudemom/claudemom`、desktop、4 个尺寸图标、LICENSE 齐全。
5. 冒烟：`xvfb-run -a ./pkg/claudemom/usr/lib/claudemom/claudemom --version`（或 `timeout 20` 启动，确认无动态库缺失、无 panic）。
6. `makepkg --printsrcinfo > .SRCINFO`。
7. 清理 `src/`、`pkg/`、`*.pkg.tar.zst`、`native-libs` 不进入提交。

## 6. 文档与发布

1. 修正 [README.md](file:///home/mensyli1/Documents/workspace/myaur/README.md) 中 claudemom 一行的"已推送 AUR"表述，改为构建通过后的实际状态。
2. 提交并推送 GitHub（`myaur` 仓库）。
3. 新建 AUR 仓库并推送：`git init` → `ssh://aur@aur.archlinux.org/claudemom.git`（直接 push 建库，无需网页 Submit Package），提交 `PKGBUILD` + `.SRCINFO`。
4. 推送后用 `git ls-remote` 校验远端 HEAD。

## 7. 风险与回退

- 风险：`ring` 静态库名推导错误 → 构建早期报 `cannot find -lring_core_...`，可立即发现，不会产出坏包。
- 风险：`cargo build -p ring -p zstd-sys` 在个别 cargo 版本需要 `--offline` 才能用已 fetch 的源码；若失败，退回 `cargo build --release --locked`（与正式构建相同的 fetch 状态）再复制归档。
- 回退：删除新增的预处理与两条 `-l`，恢复当前 PKGBUILD（问题复现，不发布）。

## 8. 需要批准的事项

- 采用 4.1 的"预构建原生库 + 显式 `-l`"方案，而不是继续尝试换链接器或 patch 上游 crate。
- 构建通过后同时推送 GitHub 与 AUR（新包 `claudemom`）。
