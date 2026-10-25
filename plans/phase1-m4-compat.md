# M4 — Quét tương thích mã nguồn và dependency

Mục tiêu: kết luận `PASS`/`FAIL`/`PENDING` theo site trước khi chuyển: luật BC tĩnh (`bc_rules.json`), PHPCompatibility/PHP_CodeSniffer và Composer tải về `STATE_DIR/tools/php` có kiểm checksum, `php -l` bằng binary đích, `check-platform-reqs` với PHP đích, Packagist tra bản tối thiểu, npm `engines`, native addon, ini bị gỡ, extension, framework/CMS, loader mã hoá, miễn trừ hit, Rector tuỳ chọn trên bản sao.

## 1. Tài liệu chính
`srs/functional-requirements.md` §6; `srs/version-scenarios-php.md` §7 (công cụ, loader), `-php-8x.md` (luật BC), `-node.md` (addon, engines); `srs/business-rules.md` (`BR-CMPT-*`, `BR-SCN-041..046`); `api/api-spec-plans.md` (compatibility, waivers).

## 2. Thiết kế
- Quét viết bằng Python (gọi `grep`, `phpcs`, `composer`, `php -l` qua `subprocess` argv cố định); kết quả lưu trong kế hoạch, dùng lại khi `scan_fingerprint` + nhánh đích không đổi.
- Công cụ: `composer.lock` + hash do catalog cung cấp; tải bằng Composer có kiểm `sha256sum`; offline/không tải được → chỉ chạy luật tĩnh (`ERR-CMPT-424-01`).
- Bản sao ghi trong `STATE_DIR/work/`; không bao giờ ghi docroot.

## 3. Tiêu chí nghiệm thu
- Fixture site PHP 5.6/7.4/8.2 có mã dùng `mysql_*`, `each()`, `create_function`, `${}` interpolation…: hit đúng `rule_id`, mức, dòng.
- Composer: ràng buộc `^7.2`, `>=5.6 <8.0`, `||` đánh giá đúng với bản patch đích.
- Kết luận `FAIL` khi còn hit `error` chưa miễn trừ; miễn trừ cần lý do ≥ 20 ký tự + audit.
- Thử PHPCompatibility thật bằng PHP 8.3 có sẵn trong container (nếu tải được công cụ qua proxy); nếu không tải được → ghi rõ.

## 4. Chưa thử được trên máy thật (dự kiến)
Loader ionCube/SourceGuardian thật; native addon build với Node đích ở prefix riêng (thử được một phần bằng Node có sẵn chép ra prefix khác).

## 5. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | P0 | `US-CMPT-01` | `AC-CMPT-01`, `AC-CMPT-02`, `AC-CMPT-03` | TC-CMPT-001, TC-CMPT-002, TC-CMPT-003 |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | P0 | `US-CMPT-02`, `US-CMPT-02` (FR) / `US-CMPT-06` (TC) | `AC-CMPT-04`, `AC-CMPT-05`, `AC-CMPT-06`, bổ sung | TC-CMPT-004, TC-CMPT-005, TC-CMPT-006, TC-CMPT-101 |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | P0 | `US-CMPT-03` | `AC-CMPT-07`, `AC-CMPT-08`, `AC-CMPT-09` | TC-CMPT-007, TC-CMPT-008, TC-CMPT-009 |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | P0 | `US-CMPT-04` | `AC-CMPT-10`, `AC-CMPT-11`, `AC-CMPT-12` | TC-CMPT-010, TC-CMPT-011, TC-CMPT-012 |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | P0 | `US-CMPT-05` | `AC-CMPT-13`, `AC-CMPT-14`, `AC-CMPT-15` | TC-CMPT-013, TC-CMPT-014, TC-CMPT-015 |
| `FR-CMPT-COMP-002` | Tra phiên bản tối thiểu thoả trên Packagist | P0 | `US-CMPT-05` | `AC-CMPT-13`, `AC-CMPT-14` | TC-CMPT-013, TC-CMPT-014 |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | P1 | `US-CMPT-06` | `AC-CMPT-16`, `AC-CMPT-18`, bổ sung | TC-CMPT-016, TC-CMPT-018, TC-CMPT-101, TC-CMPT-102 |
| `FR-CMPT-NPM-002` | Phát hiện native addon | P1 | `US-CMPT-06` | `AC-CMPT-16`, `AC-CMPT-17` | TC-CMPT-016, TC-CMPT-017 |
| `FR-CMPT-INI-001` | Quét directive ini bị gỡ | P0 | `US-CMPT-07` | `AC-CMPT-19`, `AC-CMPT-21` | TC-CMPT-019, TC-CMPT-021 |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | P0 | `US-CMPT-07` | `AC-CMPT-19`, `AC-CMPT-20`, `AC-CMPT-21` | TC-CMPT-019, TC-CMPT-020, TC-CMPT-021 |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | P1 | `US-CMPT-09` | `AC-CMPT-25`, `AC-CMPT-26`, `AC-CMPT-27` | TC-CMPT-025, TC-CMPT-026, TC-CMPT-027 |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | P0 | `US-CMPT-08` | `AC-CMPT-22`, `AC-CMPT-23`, `AC-CMPT-24` | TC-CMPT-022, TC-CMPT-023, TC-CMPT-024 |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | P0 | `US-CMPT-10` | `AC-CMPT-28`, `AC-CMPT-29`, `AC-CMPT-30` | TC-CMPT-028, TC-CMPT-029, TC-CMPT-030 |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | P2 | `US-CMPT-11` | `AC-CMPT-31`, `AC-CMPT-32`, `AC-CMPT-33` | TC-CMPT-031, TC-CMPT-032, TC-CMPT-033 |

## 6. Thiết kế đã làm (tóm tắt)
- Mã: `share/php-quickpatch/qplib/compat/` — `scan.py` (luật BC, tập file, loader, framework, mức dùng extension), `ini.py`, `deps.py` (Composer, Packagist, npm, native addon), `tools.py` (cài công cụ, PHPCompatibility, `php -l`, Rector), `semver.py`, `engine.py` (chạy theo site, kết luận, miễn trừ, `upgrade_items`); `plan.py` nối kết quả vào kế hoạch.
- Mẫu quét: tài liệu "Mẫu quét" của luật BC là văn xuôi, nên `tools/build-catalog.py` có bảng regex soạn tay cho từng luật (`bc_rules.json` → `scan[]`, 75 mẫu, kiểm biên dịch khi build), cùng bảng ini bị gỡ (`BR-SCN-046`), extension bị gỡ, gói Debian, package framework.
- Công cụ: `tools/pin-tools.py` sinh `tools/pinned-tools.json` (commit git + SHA-256 của `git archive`, phar Composer + SHA-256 công bố); catalog mang bảng này (`catalog.json` → `tools`). Zip dist của GitHub bị proxy chặn (403) nên `dist_sha256` để trống, cài từ git.
- Kết quả theo site ở `plans/<plan_id>/compat/<site_key>.json`; quét chạy ngoài khoá `plans/.lock`; `plan run` mục quét chỉ quét lại khi `scan_fingerprint`, đích, công cụ hoặc catalog đổi.
- Mục P3 có `cli_action` `compat --site $SITE --parts …` (lint, PHPCompatibility, luật BC, Composer, engines, addon) → `DONE`/`FAILED`/`PENDING` theo phần; mục Rector `compat-rector --site $SITE` (SEMI).
- Mục P4: mỗi dòng `upgrade_items` thành 1 mục con `-NN` của mục P4 khớp loại (Composer/npm/addon/framework/loader/extension); mục mẫu bị thay được giữ trong `plan.p4_replaced` để dựng lại khi quét lại.

## Trạng thái FR

| FR | Trạng thái | Test | Ghi chú |
| :--- | :--- | :--- | :--- |
| `FR-CMPT-TOOL-001` | Xong | `test_m4_compat.py` (ToolsTest), cài thật qua mạng | Cài thật PHPCompatibility 10.0.0-alpha2 + WP/Paragonie, PHPCSUtils 1.2.3, PHP_CodeSniffer 4.0.4, Composer 2.10.3/2.2.30 (14 MB, 5 s); Rector 2.7.0 + PHPStan 2.3.2 cài khi bật Rector (tổng 122 MB, vượt mục tiêu 80 MB của TC-CMPT-001 KQ3 — A-M4-04) |
| `FR-CMPT-CODE-001` | Xong | `test_m4_compat.sh`, `test_m4_compat.py` | TC-CMPT-004, 005, 006 |
| `FR-CMPT-CODE-002` | Xong | `test_m4_compat.sh` (có `QP_TEST_TOOLS_DIR`) | Chạy thật bằng PHP 8.3 của container (đóng vai `$NEW_BIN` 8.5): sniff `PHPCompatibility.FunctionUse.RemovedFunctions.eachDeprecatedRemoved`, `Keywords.ForbiddenNames.matchFound` |
| `FR-CMPT-CODE-003` | Xong | `test_m4_compat.sh` | `php -l` thật (PHP 8.3), 200 file/tiến trình từ 8.3 |
| `FR-CMPT-COMP-001` | Xong | `test_m4_compat.sh` (có công cụ) | `check-platform-reqs` thật bằng Composer 2.10.3 trên bản sao, script không chạy, bản sao bị xoá |
| `FR-CMPT-COMP-002` | Xong | `test_m4_compat.py` | Cache p2; đã gọi thử Packagist thật (guzzle, phpunit, laravel) |
| `FR-CMPT-NPM-001` | Xong | `test_m4_compat.sh`, `.py` | Đã gọi thử registry.npmjs.org thật |
| `FR-CMPT-NPM-002` | Một phần | `test_m4_compat.py` (AddonTest) | Node.js 22 thật chép ra prefix riêng: nạp addon được/không được, tạo lại lockfile v1 bằng npm mới (diff), lockfile gốc giữ nguyên SHA-256. Chưa thử build native thật (node-gyp), chưa thử chạy dưới uid chủ site |
| `FR-CMPT-INI-001` | Xong | `test_m4_compat.sh`, `.py` | TC-CMPT-019, 021 |
| `FR-CMPT-EXT-001` | Một phần | `test_m4_compat.sh` | Gói đích qua `apt-cache policy` (Debian/Ubuntu); `pecl` chỉ suy từ kho gói, chưa tra pecl.php.net; RHEL/remi chưa có |
| `FR-CMPT-FWK-001` | Xong | `test_m4_compat.sh`, `.py` | TC-CMPT-025 (dữ liệu test), 026 (`assess`), 027 (mục MANUAL xác nhận dải) |
| `FR-CMPT-LDR-001` | Một phần | `test_m4_compat.py` | Nhận diện header + bảng loader catalog, loại nhánh không có loader (`ERR-SCN-409-03`), site vào `blocked_sites`; chạy file mã hoá mẫu bằng `$NEW_BIN` là mục P4 SEMI (người vận hành), chưa tự động; chưa thử ionCube/SourceGuardian thật |
| `FR-CMPT-RES-001` | Xong | `test_m4_compat.sh`, `.py` | TC-CMPT-028..030; `plan waive`, `plan compat` |
| `FR-CMPT-RCT-001` | Xong | `test_m4_compat.sh` (có công cụ) | Rector 2.7.0 thật: dry-run trên bản sao, `rector-<site_key>.diff`, `--yes` chỉ ghi bản sao, docroot giữ nguyên SHA-256 |
| `FR-PLAN-GEN-002` (M3) | Xong | `test_m4_compat.sh`, `.py` | Thứ tự PASS → PENDING → FAIL, canary, `blocked_sites` |
| `FR-PLAN-DEP-001` (M3) | Xong | `test_m4_compat.sh`, `.py` | `upgrade_items[]` + mục P4 theo thành phần (TC-PLAN-011, 013, TC-SCN-013 KQ2) |

Kết quả chạy: `tests/run.sh` — 844 kiểm tra Bash + 114 test Python, 0 lỗi (`test_m4_compat.sh` 70 kiểm tra khi có `QP_TEST_TOOLS_DIR`, 63 khi không; `test_m4_compat.py` 32 test); `shellcheck -S warning` sạch.

## 7. Chưa thử trên máy thật
- Loader ionCube/SourceGuardian thật (chỉ thử header giả lập và bảng catalog).
- Build native addon thật bằng node-gyp; chạy npm dưới uid chủ ứng dụng (`runuser`).
- Ứng dụng Node.js chạy bằng systemd thật (thử bằng unit file trong mount namespace riêng, có `/run/systemd/system` giả).
- PHP 8.5 thật làm `$NEW_BIN` (thử bằng PHP 8.3 của container khoác phiên bản 8.5.11).
- Zip dist của GitHub (proxy chặn 403): `dist_sha256` trống, công cụ cài từ git; máy có mạng tự do vẫn đi đường git.
