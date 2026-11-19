# claudemom 构建修复任务清单

关联 spec：[spec.md](file:///home/mensyli1/Documents/workspace/myaur/docs/specs/2026-11-19-claudemom/spec.md)

- [x] T1 修改 `claudemom/PKGBUILD` 的 `build()`：
  - [x] 在 `vite:build` 之后新增 `cargo build --release --locked -p ring -p libsqlite3-sys`（`-p zstd-sys` 会触发 cargo resolver panic，改用系统 libzstd）
  - [x] 把 `target/release/build/ring-*/out/libring_core_*.a` 与 `libsqlite3-sys-*/out/libsqlite3.a` 复制到 `${srcdir}/native-libs`
  - [x] 由 `Cargo.lock` 的 `ring` 版本推导 `ring_core_<a_b_p>_`
  - [x] 在 `RUSTFLAGS` 中追加 `-C link-arg=-lzstd -C link-arg=<native-libs>/libring_core_*.a -C link-arg=<native-libs>/libsqlite3.a`，并把 `zstd` 加入 `makedepends`
- [x] T2 清理旧构建产物：`rm -rf claudemom/src claudemom/pkg claudemom/*.pkg.tar.zst`
- [x] T3 全新构建验证：`SRCDEST=/tmp/cmsrc makepkg -f`，确认 exit 0 且链接不再报 ZSTD/ring/sqlite 未定义
- [x] T4 产物检查：`bsdtar -tf` 校验二进制、desktop、4 个尺寸图标、LICENSE 齐全，`ldd` 无缺失
- [x] T5 冒烟测试：无显示环境启动 15 秒（timeout 124），仅 appindicator 弃用警告，无动态库缺失与 panic
- [x] T6 生成 `.SRCINFO`（`makepkg --printsrcinfo`）
- [x] T7 更新 `README.md` 中 claudemom 的构建说明
- [x] T8 提交并推送 GitHub（`6df59d5`）
- [x] T9 新建 AUR `claudemom` 仓库并推送，`git ls-remote` 校验 HEAD `a3cd2f5`
- [x] T10 清理工作区临时产物（`src/`、`pkg/`、`*.pkg.tar.zst`）
