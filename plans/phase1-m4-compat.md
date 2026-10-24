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

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).
