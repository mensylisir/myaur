# claudemom 构建修复任务清单

关联 spec：[spec.md](file:///home/mensyli1/Documents/workspace/myaur/docs/specs/2026-11-19-claudemom/spec.md)

- [x] T1 修改 `claudemom/PKGBUILD` 的 `build()`：
  - [x] 在 `vite:build` 之后新增 `cargo build --release --locked -p ring -p libsqlite3-sys`（`-p zstd-sys` 会触发 cargo resolver panic，改用系统 libzstd）
  - [x] 把 `target/release/build/ring-*/out/libring_core_*.a` 与 `libsqlite3-sys-*/out/libsqlite3.a` 复制到 `${srcdir}/native-libs`
  - [x] 由 `Cargo.lock` 的 `ring` 版本推导 `ring_core_<a_b_p>_`
  - [x] 在 `RUSTFLAGS` 中追加 `-C link-arg=-lzstd -C link-arg=<native-libs>/libring_core_*.a -C link-arg=<native-libs>/libsqlite3.a`，并把 `zstd` 加入 `makedepends`
- [ ] T2 清理旧构建产物：`rm -rf claudemom/src claudemom/pkg claudemom/*.pkg.tar.zst`
- [ ] T3 全新构建验证：`SRCDEST=/tmp/cmsrc makepkg -f`，确认 exit 0 且 `-lzstd` 出现在构建脚本链接参数中
- [ ] T4 产物检查：`bsdtar -tf` 校验二进制、desktop、4 个尺寸图标、LICENSE
- [ ] T5 冒烟测试：`xvfb-run` 或 `timeout` 启动，确认无动态库缺失与 panic
- [ ] T6 生成 `.SRCINFO`（`makepkg --printsrcinfo`）
- [ ] T7 修正 `README.md` 中 claudemom 的"已推送 AUR"表述
- [ ] T8 提交并推送 GitHub
- [ ] T9 新建 AUR `claudemom` 仓库并推送，`git ls-remote` 校验
- [ ] T10 清理工作区临时产物（`src/`、`pkg/`、`*.pkg.tar.zst`）
