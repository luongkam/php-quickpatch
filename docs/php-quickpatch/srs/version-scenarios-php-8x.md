---
id: DOC-SRS-QP-SCN-PHP-002
title: Phụ lục đặc tả — Danh mục kịch bản theo phiên bản PHP (SCN-PHP-008..016 — PHP 8.x, pre-release, backport distro, tự build)
version: 1.0.1
phase: Specification
domain: Security Patch Management
tags: [srs, appendix, scenario, checklist, php, php8, pre-release, backport, source-build]
depends_on:
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-SCN-PHP-001
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Phụ lục đặc tả — Kịch bản PHP 8.x, pre-release, backport distro và tự build

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo checklist SCN-PHP-008..016; dữ liệu vòng đời và bản vá kiểm chứng ngày 2026-10-22 |
| 1.0.1 | 2026-10-22 | BA Agent | Định lượng theo rule 16: thay "ngoài giờ cao điểm" (`CHK-PHP-010-08`, `CHK-PHP-016-08`) bằng "khung giờ thấp tải" đo được (§1, ĐX); thay "(khi cần)" của `CHK-PHP-016-09` bằng điều kiện `applies_when` đánh giá được; thêm câu hỏi mở §12 mục 6 |

## 1. Giới thiệu (Introduction)
Tài liệu là phần tiếp theo của [version-scenarios-php.md](version-scenarios-php.md) (tách file do giới hạn 800 dòng). Bảng tổng hợp, dữ liệu vòng đời (§3), quy tắc BR-SCN-040..050 (§4), danh mục breaking change BC-PHP (§5), ma trận framework/CMS (§6), loader/Composer/công cụ quét (§7), biến thể môi trường E1..E10 (§8) và mã lỗi bổ sung (§9) nằm ở tài liệu đó. Quy ước trạng thái, mức ưu tiên, giai đoạn P1..P7, loại mục và BR-SCN-001..018 nằm ở [version-scenarios-common.md](version-scenarios-common.md).

Cột "Loại": **Tự động** (`AUTO`), **Bán tự động (duyệt)** (`SEMI`), **Thủ công** (`MANUAL`). "Như `CHK-PHP-004-NN`" nghĩa là dùng đúng lệnh/tiêu chí/rủi ro của mục mẫu trong SCN-PHP-004 với `$OLD` của kịch bản hiện tại. Mục có điều kiện ghi `(khi ...)` tương ứng trường `applies_when` (common §5.2); mọi điều kiện phải đánh giá được từ dữ kiện quét hoặc kết quả mục trước.

**Khung giờ thấp tải** (ĐX, dùng ở cột "Rủi ro" của mục restart/build): thời điểm thoả ít nhất 1 trong 2 điều kiện: (1) nằm trong `maintenance_window` do người vận hành khai báo, mặc định 01:00–05:00 giờ máy chủ; (2) số request trong 5 phút gần nhất theo access log của các site dùng binary < 20% giá trị P95 của số request mỗi 5 phút trong 24 giờ trước. Đề xuất cho Phase 1: chỉ hiển thị khuyến nghị này trong bước xem trước dry-run, không tự chặn theo giờ (câu hỏi mở §12 mục 6).

## 2. Hai luồng xử lý cho nhánh PHP 8.x
| Luồng | Áp dụng | Nội dung | Kế thừa v0.1 |
| :--- | :--- | :--- | :--- |
| Vá cùng nhánh | Nhánh còn hỗ trợ (8.2–8.5) và bản đang chạy thấp hơn bản patch tối thiểu (BR-SCN-004) | Mục `AUTO` trong chế độ `fix`: nâng gói cùng nhánh, mitigation tạm nếu chưa vá được, restart, gỡ mitigation khi đã vá | `php_upgrade`, `php_mitigate`, `php_unmitigate`, `restart_php_services`, `pkg_has_cves` |
| Nâng khác nhánh | Nhánh `EOL` (8.0, 8.1), hoặc người vận hành chọn đích mới, hoặc BR-SCN-049 | Chuỗi mục P1–P7 cài song song → quét → nâng dependency → chuyển từng site → health check → dọn dẹp | Manifest, `rollback [ID]` |

Bản patch tối thiểu tại 2026-10-22 (php.net `releases/active.php`, cùng ngày phát hành 21 Oct 2026, nhãn `security`; trùng `PHP_FIXED` của v0.1 và khoảng ảnh hưởng của CVE-2026-109618 trên NVD): **8.2.35, 8.3.36, 8.4.27, 8.5.12**.

## 3. SCN-PHP-008 — PHP 8.0
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.0\.\d+$` / 100 |
| Trạng thái, EOL | `EOL` từ 2023-11-26 (bản cuối 8.0.30); quá 1.061 ngày → Nghiêm trọng |
| Đích | 8.5; thay thế 8.4 (Magento 2.4.8, Drupal 10.x/11.2, WordPress 6.7–6.8, Laravel 11), 8.3 |
| Lộ trình | Cùng major: chuyển một lần 8.0 → `$NEW`; staging khuyến nghị (BR-SCN-050 cho phép miễn trừ có duyệt) |
| Dải BC | `BC-PHP-81-01` … `BC-PHP-85-02` (12 mục), chủ yếu `Deprecated` + `imap`/`oci8`/`pdo_oci`/`pspell` rời lõi (8.4) và `disable_classes` bị xoá (8.5) |
| Framework/CMS | Laravel 9 (8.0–8.2, EOL 2024-02-06) → Laravel 12/13; Magento 2.4.x không có bản nào trong §6 hỗ trợ 8.0; WordPress 7.x chạy được 8.0–8.5 |
| Loader | ionCube **không có loader cho 8.0**: phát hiện ionCube trên site chạy 8.0 nghĩa là file mã hoá không được nạp → ghi finding mức High; đích phải có loader (§7.1 tài liệu PHP) |
| Composer | Composer 2.10.x chạy trên cả `$OLD` và `$NEW` |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-008-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.0\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-008-02` | P1 | Ánh xạ site → pool/handler → binary | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-008-03` | P1 | Kiểm kê extension (`imap`, `oci8`, `pdo_oci`, `pspell`) và ini `disable_classes` | Tự động | `$OLD_BIN -m`; `$OLD_BIN -i`; số hit tiền tố `imap_`, `oci_`, `pspell_` | Danh sách + số hit trong state | Extension bật nhưng không dùng → `SKIPPED` |
| `CHK-PHP-008-04` | P1 | Nhận diện framework/CMS, loader, Composer; ghi finding nếu có file ionCube trên 8.0 | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer`; finding loader (nếu có) | Như `CHK-PHP-004-04` |
| `CHK-PHP-008-05` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | Như `CHK-PHP-004-05` |
| `CHK-PHP-008-06` | P1 | Chọn và duyệt nhánh đích | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved` | Như `CHK-PHP-004-06` |
| `CHK-PHP-008-07` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-008-08` | P1 | Dựng staging cách ly hoặc ghi miễn trừ (BR-SCN-050) | Thủ công | Như `CHK-PHP-004-08` | Trang chủ staging HTTP 200, hoặc `WAIVED` có lý do ≥ 20 ký tự | Miễn trừ staging → lỗi chỉ phát hiện ở canary |
| `CHK-PHP-008-09` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 | Như `CHK-PHP-004-09` |
| `CHK-PHP-008-10` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-008-11` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | Theo §8 tài liệu PHP | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-008-12` | P2 | Cài extension tương ứng (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | `imap` không còn trong lõi 8.4+ |
| `CHK-PHP-008-13` | P2 | Tạo pool FPM `$NEW`, loại `disable_classes` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm | Như `CHK-PHP-004-13` |
| `CHK-PHP-008-14` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | 0 `Parse error` | Như `CHK-PHP-004-14` |
| `CHK-PHP-008-15` | P3 | Quét PHPCompatibility `testVersion` `$NEW` | Tự động | Lệnh chuẩn §7.3 tài liệu PHP | 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-008-16` | P3 | Quét bộ luật BC dải (8.0, `$NEW`] | Tự động | Mẫu §5 từ `BC-PHP-81-01` | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-008-17` | P3 | Kiểm tra platform Composer (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 hoặc gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-008-18` | P3 | Chạy test bằng `$NEW_BIN` với `error_reporting=-1`, đếm `Deprecated` (BC-PHP-81-01, BC-PHP-82-01) | Bán tự động (duyệt) | `$NEW_BIN -d error_reporting=-1 vendor/bin/phpunit` | Exit 0; số `Deprecated` theo nhóm ghi vào báo cáo | Dynamic property và `null` vào hàm built-in chỉ lộ lúc chạy |
| `CHK-PHP-008-19` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 14–18 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-008-20` | P3 | Sửa mã theo báo cáo 14–18 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-008-21` | P4 | Nâng dependency Composer trên `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-21` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-008-22` | P4 | Nâng framework/CMS (khi `framework` ≠ none) | Thủ công | Như `CHK-PHP-004-22` | Thuộc dải §6 | Như `CHK-PHP-004-22` |
| `CHK-PHP-008-23` | P4 | Cài loader cho `$NEW` và chạy thử file mã hoá (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | Như `CHK-PHP-004-23` |
| `CHK-PHP-008-24` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-008-25` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 27 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-008-26` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-008-27` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-008-28` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-008-29` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-008-30` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-008-31` | P7 | Gỡ `$OLD` (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 | `$OLD_BIN` không còn | Như `CHK-PHP-004-32` |
| `CHK-PHP-008-32` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:8.0` | Như `CHK-PHP-004-33` |

## 4. SCN-PHP-009 — PHP 8.1
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.1\.\d+$` / 110 |
| Trạng thái, EOL | `EOL` từ 2025-12-31 (bản cuối 8.1.34); quá 295 ngày → Cao |
| Đích | 8.5; thay thế 8.4/8.3 |
| Lộ trình | Một lần 8.1 → `$NEW`; staging khuyến nghị |
| Dải BC | `BC-PHP-82-01` … `BC-PHP-85-02` (9 mục); trọng tâm dynamic property (8.2), nullable ngầm định (8.4), `imap` rời lõi (8.4), backtick/cast/`__sleep()` (8.5) |
| Framework/CMS | Laravel 10 (8.1–8.3, EOL 2025-02-04) → Laravel 12/13; Magento 2.4.6 (8.1–8.2) → 2.4.8/2.4.9; Drupal 10.4–10.6 (8.1–8.4); Symfony 6.4 LTS (≥ 8.1.0); Joomla 5 (≥ 8.1.0) |
| Môi trường | Ubuntu 22.04 dùng gói mặc định 8.1 (`php-defaults 92ubuntu1`), hỗ trợ chuẩn đến 2027-06-01 → overlay SCN-PHP-015 và BR-SCN-048 |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-009-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.1\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-009-02` | P1 | (khi overlay SCN-PHP-015) Đọc trạng thái vá của gói distro | Tự động | `pkg_has_cves` (v0.1) với danh sách CVE online | Mỗi CVE của nhánh có trạng thái `patched`/`unpatched`/`unknown` | Changelog không ghi CVE → `unknown` (BR-SCN-015) |
| `CHK-PHP-009-03` | P1 | Ánh xạ site → pool/handler → binary | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-009-04` | P1 | Kiểm kê extension (`imap`, `oci8`, `pspell`) | Tự động | `$OLD_BIN -m`; số hit tiền tố hàm | Danh sách + số hit trong state | Như `CHK-PHP-008-03` |
| `CHK-PHP-009-05` | P1 | Nhận diện framework/CMS, loader, Composer | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer` | Như `CHK-PHP-004-04` |
| `CHK-PHP-009-06` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 (kèm hạn hỗ trợ OS khi có overlay) | Tự động | FEAT-030, FEAT-032; BR-SCN-048 | Bảng ≥ 3 ứng viên đủ trường; có cột EOL OS khi có overlay | Như `CHK-PHP-004-05` |
| `CHK-PHP-009-07` | P1 | Chọn và duyệt nhánh đích | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved` | Như `CHK-PHP-004-06` |
| `CHK-PHP-009-08` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-009-09` | P1 | Dựng staging cách ly hoặc ghi miễn trừ (BR-SCN-050) | Thủ công | Như `CHK-PHP-004-08` | Staging HTTP 200 hoặc `WAIVED` có lý do | Như `CHK-PHP-008-08` |
| `CHK-PHP-009-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 | Như `CHK-PHP-004-09` |
| `CHK-PHP-009-11` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-009-12` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | Theo §8; Ubuntu 22.04 cần kho Ondřej Surý cho 8.4/8.5 | `$NEW_BIN -v` exit 0; FPM `active` | Kho bên thứ ba thay gói `php-common` dùng chung → kiểm tra `apt-get -s install` không gỡ gói 8.1 |
| `CHK-PHP-009-13` | P2 | Cài extension tương ứng (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | Như `CHK-PHP-008-12` |
| `CHK-PHP-009-14` | P2 | Tạo pool FPM `$NEW` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm | Như `CHK-PHP-004-13` |
| `CHK-PHP-009-15` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | 0 `Parse error` | Như `CHK-PHP-004-14` |
| `CHK-PHP-009-16` | P3 | Quét PHPCompatibility `testVersion` `$NEW` | Tự động | Lệnh chuẩn §7.3 | 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-009-17` | P3 | Quét bộ luật BC dải (8.1, `$NEW`] | Tự động | Mẫu §5 từ `BC-PHP-82-01` | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-009-18` | P3 | Kiểm tra platform Composer (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 hoặc gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-009-19` | P3 | Chạy test bằng `$NEW_BIN`, đếm `Deprecated` | Bán tự động (duyệt) | Như `CHK-PHP-008-18` | Exit 0; số `Deprecated` theo nhóm trong báo cáo | Như `CHK-PHP-008-18` |
| `CHK-PHP-009-20` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 15–19 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-009-21` | P3 | Sửa mã theo báo cáo 15–19 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-009-22` | P4 | Nâng dependency Composer trên `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-21` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-009-23` | P4 | Nâng framework/CMS (khi `framework` ≠ none) | Thủ công | Như `CHK-PHP-004-22` | Thuộc dải §6 | Như `CHK-PHP-004-22` |
| `CHK-PHP-009-24` | P4 | Loader cho `$NEW` (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | Như `CHK-PHP-004-23` |
| `CHK-PHP-009-25` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-009-26` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 28 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-009-27` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-009-28` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-009-29` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-009-30` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-009-31` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-009-32` | P7 | Gỡ `$OLD` (BR-SCN-014); với gói mặc định của OS chỉ gỡ khi không gói nào khác phụ thuộc | Bán tự động (duyệt) | §8 A4; `apt-get -s purge 'php8.1-*'` xem danh sách gói bị gỡ kèm | `$OLD_BIN` không còn; 0 gói ngoài danh sách bị gỡ kèm | Gỡ gói mặc định kéo theo gói khác (vd `php-defaults`) → chỉ gỡ khi `apt-get -s` sạch |
| `CHK-PHP-009-33` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:8.1` | Như `CHK-PHP-004-33` |

## 5. SCN-PHP-010 — PHP 8.2
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.2\.\d+$` / 120 |
| Trạng thái, EOL | `SECURITY_ONLY` (active kết thúc 2024-12-31); EOL **2026-12-31** (php.net `supported-versions.php` và endoflife.date trùng nhau); còn 70 ngày → Cao |
| Bản vá tối thiểu | 8.2.35 (21 Oct 2026, nhãn `security`) |
| Đích | Vá 8.2.35 ngay (luồng vá); nâng nhánh lên 8.5 (thay thế 8.4/8.3) với kế hoạch `approved` trước **2026-12-01** (BR-SCN-049, KR2.2) |
| Dải BC khi nâng | `BC-PHP-83-01` … `BC-PHP-85-02` (6 mục) |
| Framework/CMS | Laravel 11 (8.2–8.4, EOL 2026-03-12), Laravel 12 (8.2–8.5); Symfony 7.4 LTS (≥ 8.2.0); Magento 2.4.7 (8.2–8.3); CodeIgniter 4.7 (≥ 8.2) |
| Môi trường | Debian 12 dùng gói mặc định 8.2 (`php8.2 8.2.32-1~deb12u1`); Debian 12 hết hỗ trợ thường 2026-07-11, LTS đến 2028-06-30 → overlay SCN-PHP-015 hiển thị cả 2 mốc (BR-SCN-048) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-010-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.2\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-010-02` | P1 | Xác định trạng thái vá so với 8.2.35 (kế thừa `php_state`) | Tự động | So `PHP_VERSION` với 8.2.35; gói distro: `pkg_has_cves` với danh sách CVE online | Trạng thái ∈ {`ok`, `ok-backport`, `vulnerable`} ghi vào state | Changelog không ghi CVE → `vulnerable` theo BR-SCN-015 |
| `CHK-PHP-010-03` | P1 | Ánh xạ site → pool/handler → binary | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-010-04` | P1 | Hiển thị cảnh báo EOL ≤ 90 ngày và đánh giá so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032; KR2.3 | Màn hình Tổng quan và `scan --json` có trường `days_to_eol` = 70 (tại 2026-10-22) và bảng ≥ 3 ứng viên | Dữ liệu cũ → BR-SCN-002 |
| `CHK-PHP-010-05` | P1 | Chụp baseline health check trước khi vá | Tự động | BR-SCN-009 (10 vòng, 60 s/vòng) | Baseline đủ trường cho mỗi site dùng binary | Bỏ qua baseline → không đánh giá được sau vá |
| `CHK-PHP-010-06` | P2 | Vá cùng nhánh lên ≥ 8.2.35 (luồng vá, BR-SCN-008) | Tự động | `php_upgrade` v0.1: apt `install --only-upgrade`, `dnf upgrade`, `yum update`, `apk upgrade`; `--dry-run` chỉ in lệnh; manifest `note` | `PHP_VERSION` ≥ 8.2.35 hoặc trạng thái `ok-backport` | Kho Sury/Remi chậm phát hành (common §7 mục 5); gói không bị hạ cấp khi rollback |
| `CHK-PHP-010-07` | P2 | Mitigation tạm khi chưa vá được | Tự động | `php_mitigate` v0.1: tạo `zz-php-quickpatch-mitigation.ini` trong mọi thư mục conf.d (nội dung theo bộ luật CVE trong gói dữ liệu, FEAT-061); manifest `created` | File có trong 100% thư mục conf.d của binary; finding `critical` "still unpatched" được ghi | `memory_limit = -1` bỏ giới hạn bộ nhớ; `--no-memlimit` để tắt |
| `CHK-PHP-010-08` | P2 | Restart PHP-FPM và web server | Tự động | `restart_php_services` v0.1 (systemd, cPanel `restartsrv`, LiteSpeed `lswsctrl`) | Mọi unit đã restart ở trạng thái `active`; `--no-restart` → finding `high` | v0.1 dùng `systemctl restart` (không phải reload) → request đang xử lý bị ngắt; chạy trong khung giờ thấp tải (§1) |
| `CHK-PHP-010-09` | P3 | Xác nhận sau vá và gỡ mitigation khi đã vá | Tự động | Chạy lại `php_state`; `php_unmitigate` v0.1 | Trạng thái `ok`/`ok-backport`; 0 file `zz-php-quickpatch-mitigation.ini` còn lại | Gỡ mitigation khi bản vá chưa nạp → restart trước khi kiểm (mục 08) |
| `CHK-PHP-010-10` | P6 | Health check sau vá | Tự động | BR-SCN-009 so với baseline mục 05 | Đạt 6 tiêu chí; không đạt → `ERR-SCN-500-01`, hoàn tác cấu hình bằng manifest, hạ gói là mục `Thủ công` | Gói đã nâng không tự hạ được (v0.1) |
| `CHK-PHP-010-11` | P1 | Lập và duyệt kế hoạch nâng nhánh trước 2026-12-01 (BR-SCN-049) | Bán tự động (duyệt) | Chọn đích theo BR-SCN-005 + §6 + §7.1; FEAT-041 | Kế hoạch `approved` trước 2026-12-01; đích ∈ {8.3, 8.4, 8.5} | Chọn 8.3 → EOL 2027-12-31, lặp lại sau 14 tháng |
| `CHK-PHP-010-12` | P1 | Nhận diện framework/CMS, loader, Composer | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer` | Như `CHK-PHP-004-04` |
| `CHK-PHP-010-13` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-010-14` | P1 | Dựng staging cách ly hoặc ghi miễn trừ (BR-SCN-050) | Thủ công | Như `CHK-PHP-004-08` | Staging HTTP 200 hoặc `WAIVED` có lý do | Như `CHK-PHP-008-08` |
| `CHK-PHP-010-15` | P2 | Kiểm tra điều kiện tiên quyết và ghim mặc định (BR-SCN-016, BR-SCN-012) | Tự động | Như `CHK-PHP-004-09`, `CHK-PHP-004-10` | Đạt BR-SCN-016; `readlink -f /usr/bin/php` không đổi sau cài | Như `CHK-PHP-004-09` |
| `CHK-PHP-010-16` | P2 | Cài `$NEW` song song và extension tương ứng (§8 A1, BR-SCN-045) | Bán tự động (duyệt) | Theo §8; so `-m` 2 bên | `$NEW_BIN -v` exit 0; FPM `active`; extension thiếu chưa có phương án = 0 | Như `CHK-PHP-009-12` |
| `CHK-PHP-010-17` | P2 | Tạo pool FPM `$NEW` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm (`disable_classes` khi `$NEW` = 8.5) | Như `CHK-PHP-004-13` |
| `CHK-PHP-010-18` | P3 | Lint + PHPCompatibility `testVersion` `$NEW` + bộ luật BC dải (8.2, `$NEW`] | Tự động | Như `CHK-PHP-004-14`, `-15`, `-16` | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-16` |
| `CHK-PHP-010-19` | P3 | Kiểm tra platform Composer (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 hoặc gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-010-20` | P3 | Chạy test bằng `$NEW_BIN`, đếm `Deprecated` | Bán tự động (duyệt) | Như `CHK-PHP-008-18` | Exit 0; số `Deprecated` theo nhóm trong báo cáo | Như `CHK-PHP-008-18` |
| `CHK-PHP-010-21` | P3 | (Tuỳ chọn) Rector trên `$COPY`, sau đó sửa mã còn lại | Bán tự động (duyệt) | Như `CHK-PHP-004-19`, `CHK-PHP-004-20` | Diff đã duyệt; mục 18–20 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-010-22` | P4 | Nâng dependency Composer, framework/CMS, loader cho `$NEW` | Bán tự động (duyệt) | Như `CHK-PHP-004-21`, `-22`, `-23` | `check-platform-reqs` exit 0; framework thuộc §6; file mã hoá mẫu exit 0 | Laravel 11 chỉ đến 8.4 → lên Laravel 12/13 trước khi chọn 8.5 |
| `CHK-PHP-010-23` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 25 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-010-24` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt; hoàn tất trước 2026-12-31 | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` trước 2026-12-31 | Trễ hạn → site chạy nhánh `EOL` từ 2027-01-01, ưu tiên tăng lên Cao/Nghiêm trọng |
| `CHK-PHP-010-25` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-010-26` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-010-27` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-010-28` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-010-29` | P7 | Gỡ 8.2 (BR-SCN-014) | Bán tự động (duyệt) | Như `CHK-PHP-009-32` | `$OLD_BIN` không còn; 0 gói ngoài danh sách bị gỡ kèm | Như `CHK-PHP-009-32` |
| `CHK-PHP-010-30` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:8.2` | Như `CHK-PHP-004-33` |

## 6. SCN-PHP-011 — PHP 8.3
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.3\.\d+$` / 130 |
| Trạng thái, EOL | `SECURITY_ONLY` (active kết thúc 2025-12-31); EOL 2027-12-31; còn 435 ngày → Trung bình (Cao khi < 8.3.36 vì CVE-2026-109618, CVSS v3.1 9.8) |
| Bản vá tối thiểu | 8.3.36 (21 Oct 2026, nhãn `security`) |
| Đích | Giữ nhánh, vá 8.3.36. Nâng lên 8.5 (thay thế 8.4) với kế hoạch `approved` trước 2027-12-01; tool cảnh báo từ 2027-10-02 (EOL − 90 ngày) |
| Dải BC khi nâng | `BC-PHP-84-01` … `BC-PHP-85-02` (5 mục) |
| Môi trường | Ubuntu 24.04 dùng gói mặc định 8.3 (`php-defaults 93ubuntu2`), hỗ trợ chuẩn đến 2029-05-31 → overlay SCN-PHP-015 (v0.1 đã nhận đúng bản vá `8.3.6-0ubuntu0.24.04.13`) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-011-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.3\.\d+` | Như `CHK-PHP-004-01` |
| `CHK-PHP-011-02` | P1 | Xác định trạng thái vá so với 8.3.36 | Tự động | Như `CHK-PHP-010-02` | Trạng thái ∈ {`ok`, `ok-backport`, `vulnerable`} | Như `CHK-PHP-010-02` |
| `CHK-PHP-011-03` | P1 | Ánh xạ site và chụp baseline health check | Tự động | Như `CHK-PHP-004-02`; BR-SCN-009 | `unmapped` = 0; baseline đủ trường | Như `CHK-PHP-010-05` |
| `CHK-PHP-011-04` | P2 | Vá cùng nhánh lên ≥ 8.3.36 | Tự động | Như `CHK-PHP-010-06` | `PHP_VERSION` ≥ 8.3.36 hoặc `ok-backport` | Như `CHK-PHP-010-06` |
| `CHK-PHP-011-05` | P2 | Mitigation tạm khi chưa vá được | Tự động | Như `CHK-PHP-010-07` | File mitigation có trong 100% thư mục conf.d | Như `CHK-PHP-010-07` |
| `CHK-PHP-011-06` | P2 | Restart PHP-FPM và web server | Tự động | Như `CHK-PHP-010-08` | Unit `active` | Như `CHK-PHP-010-08` |
| `CHK-PHP-011-07` | P3 | Xác nhận sau vá, gỡ mitigation | Tự động | Như `CHK-PHP-010-09` | `ok`/`ok-backport`; 0 file mitigation | Như `CHK-PHP-010-09` |
| `CHK-PHP-011-08` | P4 | Rà dependency của site trên nhánh hiện tại (Composer/npm/WordPress, kế thừa v0.1) | Tự động | OSV `querybatch`; `stable-check` WordPress | Danh sách finding; 0 `MAL-*` chưa xử lý | `composer update` đổi phiên bản phụ → chạy trong `fix` có manifest |
| `CHK-PHP-011-09` | P6 | Health check sau vá | Tự động | Như `CHK-PHP-010-10` | Đạt 6 tiêu chí | Như `CHK-PHP-010-10` |
| `CHK-PHP-011-10` | P1 | Lập và duyệt kế hoạch nâng nhánh trước 2027-12-01 (BR-SCN-049) | Bán tự động (duyệt) | Như `CHK-PHP-010-11` | Kế hoạch `approved` trước 2027-12-01 | Để sát hạn → không đủ thời gian cho framework |
| `CHK-PHP-011-11` | P2 | (khi nâng nhánh) Sao lưu, điều kiện tiên quyết, cài `$NEW` song song, extension, pool | Bán tự động (duyệt) | Như `CHK-PHP-010-13` … `CHK-PHP-010-17` | Toàn bộ tiêu chí của 5 mục mẫu đạt | Như các mục mẫu |
| `CHK-PHP-011-12` | P3 | (khi nâng nhánh) Lint + PHPCompatibility + bộ luật BC dải (8.3, `$NEW`] + Composer + test | Bán tự động (duyệt) | Như `CHK-PHP-010-18` … `CHK-PHP-010-20` | BR-SCN-042 ĐẠT; test exit 0 | Như `CHK-PHP-004-16` |
| `CHK-PHP-011-13` | P4 | (khi nâng nhánh) Nâng dependency, framework/CMS, loader | Bán tự động (duyệt) | Như `CHK-PHP-010-22` | Như mục mẫu | Magento 2.4.7 tối đa 8.3 → lên 2.4.8 trước |
| `CHK-PHP-011-14` | P5 | (khi nâng nhánh) Chuyển canary rồi từng site | Bán tự động (duyệt) | Như `CHK-PHP-010-23`, `-24` | 100% site `DONE`/`WAIVED` trước 2027-12-31 | Như `CHK-PHP-010-24` |
| `CHK-PHP-011-15` | P6 | (khi nâng nhánh) Health check, kiểm thử nghiệp vụ, chuyển cron | Bán tự động (duyệt) | Như `CHK-PHP-010-25` … `-27` | Đạt BR-SCN-009; 0 cron gọi `$OLD_BIN` | Như mục mẫu |
| `CHK-PHP-011-16` | P7 | (khi nâng nhánh) Thống kê `Deprecated`, gỡ 8.3, cập nhật Dockerfile/CI | Bán tự động (duyệt) | Như `CHK-PHP-010-28` … `-30` | `$OLD_BIN` không còn; 0 tham chiếu `php:8.3` | Gói 8.3 là mặc định Ubuntu 24.04 → kiểm tra `apt-get -s purge` |

## 7. SCN-PHP-012 — PHP 8.4
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.4\.\d+$` / 140 |
| Trạng thái, EOL | `ACTIVE` đến 2026-12-31, chuyển `SECURITY_ONLY` từ 2027-01-01 (tool tự tính lại theo BR-SCN-003); EOL 2028-12-31; còn 801 ngày → Thấp (Cao khi < 8.4.27) |
| Bản vá tối thiểu | 8.4.27 (21 Oct 2026, nhãn `security`) |
| Đích | Giữ nhánh, vá 8.4.27. Nâng lên 8.5 tuỳ chọn; bắt buộc có kế hoạch `approved` trước 2028-12-01 |
| Dải BC khi nâng | `BC-PHP-85-01`, `BC-PHP-85-02` (2 mục) |
| Môi trường | Debian 13 dùng gói mặc định 8.4 (`php8.4 8.4.24-1~deb13u1` trong trixie, `8.4.26-1~deb13u1` trong trixie-proposed-updates tại 2026-10-22) → overlay SCN-PHP-015; Debian chưa có 8.4.27 → trạng thái vá xác định bằng changelog (BR-SCN-015) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-012-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.4\.\d+` | Như `CHK-PHP-004-01` |
| `CHK-PHP-012-02` | P1 | Xác định trạng thái vá so với 8.4.27 | Tự động | Như `CHK-PHP-010-02` | Trạng thái ∈ {`ok`, `ok-backport`, `vulnerable`} | Debian 13 chưa có bản vá trong kho → `vulnerable` cho tới khi changelog ghi CVE |
| `CHK-PHP-012-03` | P1 | Ánh xạ site và chụp baseline health check | Tự động | Như `CHK-PHP-011-03` | `unmapped` = 0; baseline đủ trường | Như `CHK-PHP-010-05` |
| `CHK-PHP-012-04` | P2 | Vá cùng nhánh lên ≥ 8.4.27 | Tự động | Như `CHK-PHP-010-06` | `PHP_VERSION` ≥ 8.4.27 hoặc `ok-backport` | Như `CHK-PHP-010-06` |
| `CHK-PHP-012-05` | P2 | Mitigation tạm khi chưa vá được | Tự động | Như `CHK-PHP-010-07` | File mitigation có trong 100% thư mục conf.d | Như `CHK-PHP-010-07` |
| `CHK-PHP-012-06` | P2 | Restart PHP-FPM và web server | Tự động | Như `CHK-PHP-010-08` | Unit `active` | Như `CHK-PHP-010-08` |
| `CHK-PHP-012-07` | P3 | Xác nhận sau vá, gỡ mitigation | Tự động | Như `CHK-PHP-010-09` | `ok`/`ok-backport`; 0 file mitigation | Như `CHK-PHP-010-09` |
| `CHK-PHP-012-08` | P4 | Rà dependency của site trên nhánh hiện tại | Tự động | Như `CHK-PHP-011-08` | 0 `MAL-*` chưa xử lý | Như `CHK-PHP-011-08` |
| `CHK-PHP-012-09` | P6 | Health check sau vá | Tự động | Như `CHK-PHP-010-10` | Đạt 6 tiêu chí | Như `CHK-PHP-010-10` |
| `CHK-PHP-012-10` | P1 | Ghi nhắc chuyển trạng thái `SECURITY_ONLY` ngày 2027-01-01 và lập kế hoạch nâng nhánh trước 2028-12-01 | Bán tự động (duyệt) | Như `CHK-PHP-010-11` | Kế hoạch `approved` trước 2028-12-01 | Không có hành động thay đổi hệ thống ở mục này |
| `CHK-PHP-012-11` | P2 | (khi nâng nhánh) Sao lưu, điều kiện tiên quyết, cài 8.5 song song, extension, pool | Bán tự động (duyệt) | Như `CHK-PHP-010-13` … `-17` | Toàn bộ tiêu chí mục mẫu đạt | Như các mục mẫu |
| `CHK-PHP-012-12` | P3 | (khi nâng nhánh) Quét dải (8.4, 8.5] + Composer + test | Bán tự động (duyệt) | Như `CHK-PHP-010-18` … `-20` | BR-SCN-042 ĐẠT | Backtick, `(integer)`, `case ...;` (BC-PHP-85-01) chỉ là Deprecated → không chặn, ghi báo cáo |
| `CHK-PHP-012-13` | P4 | (khi nâng nhánh) Nâng dependency, framework/CMS, loader | Bán tự động (duyệt) | Như `CHK-PHP-010-22` | Như mục mẫu | Magento 2.4.8 tối đa 8.4; Drupal 11.1/11.2 tối đa 8.4 |
| `CHK-PHP-012-14` | P5 | (khi nâng nhánh) Chuyển canary rồi từng site | Bán tự động (duyệt) | Như `CHK-PHP-010-23`, `-24` | 100% site `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-PHP-012-15` | P6 | (khi nâng nhánh) Health check, kiểm thử nghiệp vụ, chuyển cron | Bán tự động (duyệt) | Như `CHK-PHP-010-25` … `-27` | Đạt BR-SCN-009; 0 cron gọi `$OLD_BIN` | Như mục mẫu |
| `CHK-PHP-012-16` | P7 | (khi nâng nhánh) Thống kê `Deprecated`, gỡ 8.4, cập nhật Dockerfile/CI | Bán tự động (duyệt) | Như `CHK-PHP-010-28` … `-30` | `$OLD_BIN` không còn; 0 tham chiếu `php:8.4` | Như mục mẫu |

## 8. SCN-PHP-013 — PHP 8.5
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^8\.5\.\d+$` / 150 |
| Trạng thái, EOL | `ACTIVE` đến 2027-12-31; EOL 2029-12-31; còn 1.166 ngày → Thấp (Cao khi < 8.5.12) |
| Bản vá tối thiểu | 8.5.12 (21 Oct 2026, nhãn `security`); endoflife.date ghi `latest` 8.5.11 → không dùng làm mốc vá (common §7 mục 1) |
| Đích | Giữ nhánh (là đích mặc định của các kịch bản khác). 8.6 chỉ trở thành ứng viên mặc định khi thoả BR-SCN-005 (b): từ 2027-02-17 nếu 8.6.0 GA đúng 2026-11-19 |
| Mitigation riêng | v0.1 thêm `fatal_error_backtraces = 0` vào file mitigation khi phiên bản khớp `8.5.*` (hàm `php_mitigation_ini`) |
| Loader | ionCube 15.5.0+ và SourceGuardian 17.0.0 có loader cho 8.5 |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-013-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^8\.5\.\d+` | Như `CHK-PHP-004-01` |
| `CHK-PHP-013-02` | P1 | Xác định trạng thái vá so với 8.5.12 | Tự động | Như `CHK-PHP-010-02` | Trạng thái ∈ {`ok`, `ok-backport`, `vulnerable`} | Như `CHK-PHP-010-02` |
| `CHK-PHP-013-03` | P1 | Ánh xạ site và chụp baseline health check | Tự động | Như `CHK-PHP-011-03` | `unmapped` = 0; baseline đủ trường | Như `CHK-PHP-010-05` |
| `CHK-PHP-013-04` | P1 | Kiểm tra loader mã hoá có bản cho 8.5 (khi `loader` ≠ none) | Tự động | `$OLD_BIN -v` có dòng loader; §7.1 tài liệu PHP | Dòng loader có mặt và file mã hoá mẫu chạy exit 0 | Loader cũ hơn 15.5.0 không nạp được trên 8.5 |
| `CHK-PHP-013-05` | P2 | Vá cùng nhánh lên ≥ 8.5.12 | Tự động | Như `CHK-PHP-010-06` | `PHP_VERSION` ≥ 8.5.12 hoặc `ok-backport` | Kho Remi liệt kê 8.5.11 tại 2026-10-22 → chờ kho hoặc mitigation |
| `CHK-PHP-013-06` | P2 | Mitigation tạm khi chưa vá được (gồm `fatal_error_backtraces = 0`) | Tự động | Như `CHK-PHP-010-07` | File mitigation có trong 100% thư mục conf.d và chứa 3 directive | Như `CHK-PHP-010-07` |
| `CHK-PHP-013-07` | P2 | Restart PHP-FPM và web server | Tự động | Như `CHK-PHP-010-08` | Unit `active` | Như `CHK-PHP-010-08` |
| `CHK-PHP-013-08` | P3 | Xác nhận sau vá, gỡ mitigation | Tự động | Như `CHK-PHP-010-09` | `ok`/`ok-backport`; 0 file mitigation | Như `CHK-PHP-010-09` |
| `CHK-PHP-013-09` | P4 | Rà dependency của site | Tự động | Như `CHK-PHP-011-08` | 0 `MAL-*` chưa xử lý | Như `CHK-PHP-011-08` |
| `CHK-PHP-013-10` | P6 | Health check sau vá | Tự động | Như `CHK-PHP-010-10` | Đạt 6 tiêu chí | Như `CHK-PHP-010-10` |
| `CHK-PHP-013-11` | P7 | Thống kê log `Deprecated` 7 ngày để chuẩn bị cho 8.6 | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm thông điệp | Deprecated 8.5 (backtick, `__sleep()`) có thể bị xoá ở bản sau |
| `CHK-PHP-013-12` | P1 | Đánh giá lại ứng viên 8.6 từ 2027-02-17 | Tự động | BR-SCN-005 chạy theo lịch `sync` | Khi 8.6 thoả (a)(b)(c)(d), console hiển thị ứng viên mới; trước mốc này không hiển thị | Framework chưa hỗ trợ 8.6 (vd Drupal) → (d) không thoả |

## 9. SCN-PHP-014 — PHP 8.6 pre-release
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | Điều kiện (1) của BR-SCN-040: `^8\.6\.\d+(alpha\|beta\|RC)\d*` hoặc hậu tố `-dev`, và nhánh 8.6 có trong `pre-release-builds.php?format=json` / 10 |
| Trạng thái | `PRE_RELEASE`. Tại 2026-10-22: 8.6.0RC4 phát hành 2026-10-21; RC5 dự kiến 2026-11-05; GA dự kiến 2026-11-19 (wiki.php.net/todo/php86). Ưu tiên Nghiêm trọng nếu phục vụ ≥ 1 site công khai (common §2.2) |
| Đích | Production: hạ về 8.5.12 (nhánh `ACTIVE`, BR-SCN-007 cấm production trên pre-release). Môi trường nội bộ/staging: được giữ, nâng lên 8.6.0 GA sau 2026-11-19 |
| Breaking change | `BC-PHP-86-01` (theo `UPGRADING` nhánh PHP-8.6, có thể đổi trước GA). Khi hạ về 8.5: mã đã dùng tính năng mới của 8.6 sẽ lỗi trên 8.5 → quét ngược bằng `testVersion` 8.5 |
| Loader / framework | ionCube chưa nêu loader 8.6; SourceGuardian 17.0.0 liệt kê đến 8.5; Drupal: không bản nào hỗ trợ 8.6; Composer package chưa khai báo 8.6 → `check-platform-reqs` có thể lỗi |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-014-01` | P1 | Ghi chuỗi phiên bản và đối chiếu nguồn pre-release | Tự động | `$OLD_BIN -n -r 'echo PHP_VERSION,"\|",PHP_EXTRA_VERSION;'`; `pre-release-builds.php?format=json` | Chuỗi (vd `8.6.0RC4`) và loại pre-release lưu vào state; `ERR-SCN-422-01` hiển thị (BR-SCN-013) | Build `-dev` từ git không có trong JSON → SCN-PHP-005 |
| `CHK-PHP-014-02` | P1 | Khoá mục `AUTO` thay đổi hệ thống cho binary (BR-SCN-013) | Tự động | Cờ `locked` trong state | Job `fix` trên binary trả `SKIPPED` | Như `CHK-PHP-005-02` |
| `CHK-PHP-014-03` | P1 | Liệt kê site dùng binary và phân loại công khai/nội bộ | Tự động | FEAT-004; site công khai = vhost có bản ghi DNS công khai hoặc nghe trên IP không phải RFC 1918 | Danh sách site + cờ `public`; ưu tiên tính lại | Phân loại sai → người vận hành sửa cờ có duyệt |
| `CHK-PHP-014-04` | P1 | Kiểm tra loader và framework hỗ trợ 8.6 | Tự động | §6, §7.1 tài liệu PHP | Mỗi site có kết luận `supported`/`unsupported`/`unknown` cho 8.6 | Thiếu dữ liệu → `unknown`, không coi là hỗ trợ |
| `CHK-PHP-014-05` | P1 | Chọn phương án: (a) hạ về 8.5 cho site công khai; (b) giữ nội bộ và chờ GA | Bán tự động (duyệt) | BR-SCN-007; FEAT-040 chặn chọn pre-release làm đích | Kế hoạch `approved` ghi phương án cho từng site | Giữ RC cho site công khai vi phạm BR-SCN-007 → `ERR-SCN-409-02` |
| `CHK-PHP-014-06` | P2 | (a) Cài 8.5 song song, extension, pool | Bán tự động (duyệt) | Như `CHK-PHP-010-15` … `-17` với `$NEW` = 8.5 | `$NEW_BIN -v` = 8.5.12+; FPM `active` | Như mục mẫu |
| `CHK-PHP-014-07` | P3 | (a) Quét ngược với 8.5: lint + PHPCompatibility `testVersion` 8.5 | Tự động | Như `CHK-PHP-004-14`, `-15` | 0 `Parse error`; 0 `ERROR` | Mã dùng cú pháp mới của 8.6 → sửa trước khi chuyển |
| `CHK-PHP-014-08` | P4 | (a) Kiểm tra Composer với 8.5 (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 | Lock sinh trên 8.6 có gói yêu cầu > 8.5 → `update` trên `$COPY` |
| `CHK-PHP-014-09` | P5 | (a) Chuyển từng site công khai sang 8.5 (canary trước) | Bán tự động (duyệt) | Như `CHK-PHP-004-24`, `-26`, `-27` | 100% site công khai `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-PHP-014-10` | P6 | (a) Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-014-11` | P2 | (b) Sau GA: cài 8.6.0 GA (gói hoặc tarball có SHA-256 từ `releases/index.php?json&version=8.6`) thay bản RC trên môi trường nội bộ | Bán tự động (duyệt) | Kiểm `sha256sum -c`; `$BIN -v` | `PHP_VERSION` khớp `^8\.6\.\d+$` (không hậu tố); runtime được gán lại kịch bản theo dữ liệu vòng đời mới | Dữ liệu vòng đời chưa có 8.6 → vẫn `UNKNOWN` tới lần `sync` có dữ liệu |
| `CHK-PHP-014-12` | P7 | Gỡ build RC khỏi máy (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 sau 14 ngày không request | Không còn binary có hậu tố `RC`/`beta`/`alpha` | Mất rollback 1 lệnh về RC (chủ đích) |
| `CHK-PHP-014-13` | P7 | Gỡ cờ `locked` và chạy lại `scan` | Tự động | `scan --json` | Không còn runtime gán SCN-PHP-014 | Còn binary RC ở đường dẫn khác → quay lại mục 01 |

## 10. SCN-PHP-015 — PHP gói distro có backport
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; binary có gói sở hữu (`dpkg -S`, `rpm -qf`, `apk info --who-owns`) / `match_order` 500 |
| Vấn đề | Distro giữ số phiên bản upstream cũ nhưng vá CVE bằng backport: vd Ubuntu 24.04 `8.3.6-0ubuntu0.24.04.13` đã có bản vá PHP2Shell dù upstream 8.3.6 < 8.3.36 (v0.1 nhận đúng); Debian 12 `8.2.32-1~deb12u1` < 8.2.35 upstream. So sánh số phiên bản upstream cho kết luận sai |
| Gói mặc định theo OS (Launchpad `php-defaults`, sources.debian.org) | Ubuntu 18.04 → 7.2; 20.04 → 7.4; 22.04 → 8.1; 24.04 → 8.3. Debian 11 → 7.4; 12 → 8.2; 13 → 8.4 |
| Hạn hỗ trợ OS (endoflife.date) | Ubuntu 20.04: chuẩn đến 2025-05-31, ESM đến 2030-04-23; 22.04: 2027-06-01 / 2032-04-21; 24.04: 2029-05-31 / 2034-04-25. Debian 11: LTS đến 2026-08-31; 12: thường đến 2026-07-11, LTS đến 2028-06-30; 13: thường đến 2028-08-09, LTS đến 2030-06-30. RHEL 8: 2029-05-31; 9: 2032-05-31; 10: 2035-05-31 |
| Quy tắc | BR-SCN-015 (trạng thái vá qua changelog/tracker), BR-SCN-048 (hiển thị 2 mốc, giảm 1 bậc ưu tiên khi đủ điều kiện) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-015-01` | P1 | Xác định gói, phiên bản gói đầy đủ và kho nguồn | Tự động | `dpkg-query -W -f='${Package} ${Version}\n' <pkg>` + `apt-cache policy <pkg>`; `rpm -q --qf '%{NAME} %{VERSION}-%{RELEASE} %{VENDOR}\n' <pkg>`; `apk info -v <pkg>` | `package`, `pkg_version`, `origin` (kho OS / Ondřej Surý / Remi / khác) lưu vào state | Gói từ kho bên thứ ba không có backport của OS → xử lý như upstream |
| `CHK-PHP-015-02` | P1 | Xác định OS và hạn hỗ trợ OS | Tự động | `/etc/os-release`; endoflife.date `ubuntu`/`debian`/`rhel` | OS, phiên bản, mốc hỗ trợ thường và mở rộng trong state | Bản OS không có trong endoflife.date → `unknown`, không giảm bậc |
| `CHK-PHP-015-03` | P1 | Đối chiếu CVE với changelog gói (kế thừa `pkg_has_cves`) | Tự động | `zcat /usr/share/doc/<pkg>/changelog.Debian.gz \| grep -c <CVE>`; `rpm -q --changelog <pkg> \| grep -c <CVE>` | Mỗi CVE (KEV hoặc CVSS ≥ 7,0) của nhánh có trạng thái `patched`/`unknown` | Changelog không ghi mã CVE → `unknown` (BR-SCN-015) |
| `CHK-PHP-015-04` | P1 | Đối chiếu tracker bảo mật của distro (nguồn bổ sung, câu hỏi mở Q-04 của PRD) | Tự động | Tracker Debian/Ubuntu/Red Hat (endpoint chưa kiểm chứng, chờ SRS chốt) | Trạng thái CVE theo tracker lưu cạnh kết quả changelog; lệch nhau → cảnh báo | Endpoint đổi định dạng → giữ changelog là nguồn chính |
| `CHK-PHP-015-05` | P1 | Kiểm tra kênh nhận bản vá đang bật | Tự động | `apt-cache policy <pkg>` có nguồn `-security`/`-updates`; Ubuntu hết hỗ trợ chuẩn: `pro status` (dịch vụ ESM) | Có ≥ 1 kênh vá đang bật cho gói; nếu OS đã qua hỗ trợ chuẩn mà ESM/LTS tắt → finding `high` | Máy không đăng ký ESM → không nhận bản vá sau hỗ trợ chuẩn |
| `CHK-PHP-015-06` | P1 | Tính trạng thái và ưu tiên theo BR-SCN-048 | Tự động | Kết quả mục 02–05 | Màn hình hiển thị EOL upstream và EOL OS; ưu tiên đã tính | Sai lệch 2 mốc gây hiểu nhầm → hiển thị chú thích nguồn |
| `CHK-PHP-015-07` | P2 | Vá trong kho OS (kế thừa `php_upgrade`) | Tự động | `apt-get install -y -q --only-upgrade -o Dpkg::Options::=--force-confold <pkgs>`; `dnf -y upgrade '<glob>'`; manifest `note` | Sau nâng, mục 03 cho 100% CVE `patched` hoặc kho chưa có bản vá mới hơn | Gói không bị hạ cấp khi rollback (v0.1) |
| `CHK-PHP-015-08` | P2 | Mitigation và hẹn kiểm lại khi kho OS chưa có bản vá | Tự động | Như `CHK-PHP-010-07`; lịch `sync` 6 giờ (FEAT-018) | File mitigation có mặt; finding còn mở được kiểm lại ở mỗi lần `sync` | Độ trễ kho (vd Remi tại 2026-10-22) |
| `CHK-PHP-015-09` | P2 | (khi nâng nhánh) Ưu tiên gói trong kho OS; thêm kho bên thứ ba chỉ khi có duyệt | Bán tự động (duyệt) | `apt-get -s install php$NEW-fpm`: đếm gói bị gỡ; file kho mới ghi manifest `created` | 0 gói của OS bị gỡ trong mô phỏng; file kho có trong manifest | Kho bên thứ ba thay gói dùng chung (`php-common`) |
| `CHK-PHP-015-10` | P3 | Kiểm tra toàn vẹn gói sau vá | Tự động | `dpkg --verify <pkg>` / `rpm -V <pkg>` | 0 sai lệch trên file binary và thư viện | Sai lệch file cấu hình là bình thường → chỉ xét file thực thi |
| `CHK-PHP-015-11` | P6 | Restart và health check sau vá | Tự động | Như `CHK-PHP-010-08`, `CHK-PHP-010-10` | Unit `active`; đạt 6 tiêu chí BR-SCN-009 | Như mục mẫu |
| `CHK-PHP-015-12` | P7 | Ghi chú rollback không hạ gói vào báo cáo | Tự động | Manifest `note` (v0.1) | Báo cáo job có dòng "Package upgrades are kept" | Người vận hành kỳ vọng rollback hạ gói |
| `CHK-PHP-015-13` | P7 | Cảnh báo khi OS còn ≤ 180 ngày tới hết hỗ trợ (thường hoặc LTS) | Tự động | So hôm nay với mốc mục 02 | Finding `medium` xuất hiện đúng khi còn ≤ 180 ngày | Nâng cấp OS ngoài phạm vi tool (PRD §3.2 mục 9) |

## 11. SCN-PHP-016 — PHP tự build, không thuộc gói
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; `pkg_owner` rỗng và đường dẫn không thuộc panel (§8 E5–E9 tài liệu PHP); ví dụ `/usr/local/bin/php`, `/usr/local/php*`, `/opt/*` / `match_order` 510 |
| Vấn đề | Không có kho gói → không nhận bản vá tự động; v0.1 chỉ cảnh báo "source build or panel build" và áp mitigation. Trạng thái vá chỉ suy ra từ số phiên bản upstream |
| Ưu tiên | Theo kịch bản `VERSION`, tăng 1 bậc khi không xác định được nguồn build (mục 02 không có `Configure Command`) |
| Phương án | (a) Build bản patch/nhánh đích từ tarball php.net vào prefix mới song song, chuyển site, giữ prefix cũ để rollback; (b) chuyển sang gói (E1/E2) để nhận vá tự động — khuyến nghị |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-016-01` | P1 | Xác nhận không có gói sở hữu và không thuộc panel | Tự động | `pkg_owner` v0.1; so đường dẫn với mẫu E5–E9 | Cờ `source_build=true` trong state | Panel lạ không có trong danh sách → người vận hành gắn nhãn panel thủ công |
| `CHK-PHP-016-02` | P1 | Thu thập cấu hình build hiện tại | Tự động | `$OLD_BIN -i` (dòng `Configure Command`); `<prefix>/bin/php-config --configure-options` nếu có; `$OLD_BIN -m`; `$OLD_BIN --ini` | Tuỳ chọn configure, danh sách extension, đường dẫn ini lưu vào state | Không có `Configure Command` → ưu tiên tăng 1 bậc |
| `CHK-PHP-016-03` | P1 | Xác định cách chạy FPM/SAPI | Tự động | `systemctl cat <unit>` có `ExecStart` chứa prefix; `ps -eo pid,args \| grep 'php-fpm: master'`; script init | Tên unit/lệnh khởi động lưu vào state | Tiến trình chạy bằng `nohup` không có unit → mục 10 tạo unit mới |
| `CHK-PHP-016-04` | P1 | Đánh giá trạng thái vá theo số phiên bản upstream | Tự động | So `PHP_VERSION` với bản patch tối thiểu (BR-SCN-004) | Trạng thái `ok`/`vulnerable`/`eol` | Bản vá tự áp (patch riêng) không nhận diện được → coi là `vulnerable` |
| `CHK-PHP-016-05` | P1 | Chọn phương án (a) build lại hoặc (b) chuyển sang gói | Bán tự động (duyệt) | FEAT-040 | Kế hoạch `approved` ghi phương án | (a) cần lặp lại mỗi lần có bản vá |
| `CHK-PHP-016-06` | P2 | (a) Tải tarball và kiểm SHA-256 | Tự động | Tải `php-<ver>.tar.xz` từ php.net; lấy `sha256` trong `releases/index.php?json&version=<ver>`; `sha256sum -c` | `sha256sum -c` báo `OK` | Lệch checksum → dừng, không build |
| `CHK-PHP-016-07` | P2 | (a) Cài thư viện phát triển cần cho các tuỳ chọn `--with-*` | Bán tự động (duyệt) | Gói `-dev`/`-devel` tương ứng; chạy `./configure <tuỳ chọn>` thử | `./configure` exit 0 | Bỏ tuỳ chọn của extension đã rời lõi (§5) khỏi configure |
| `CHK-PHP-016-08` | P2 | (a) Build và cài vào prefix mới `/opt/php-<ver>` | Bán tự động (duyệt) | `make -j$(nproc)`; `make install`; manifest `created /opt/php-<ver>` | `/opt/php-<ver>/bin/php -v` exit 0; `-m` chứa mọi extension của mục 02 hoặc có thay thế (BR-SCN-045) | `make -j$(nproc)` dùng toàn bộ nhân CPU → chạy trong khung giờ thấp tải (§1); cần ≥ 2 GB đĩa (BR-SCN-016) |
| `CHK-PHP-016-09` | P2 | (a) Cài extension PECL và loader cho build mới (khi `-m` của build mới ở mục 08 thiếu extension có trong danh sách mục 02, hoặc `loader` ≠ none) | Bán tự động (duyệt) | `/opt/php-<ver>/bin/pecl install <ext>` hoặc `phpize` + build; §7.1 cho loader | `-m` có extension; file mã hoá mẫu exit 0 | Extension PECL không có bản cho nhánh mới |
| `CHK-PHP-016-10` | P2 | Tạo unit/pool FPM mới cho prefix mới | Tự động | Sao chép unit, đổi `ExecStart` và socket; `/opt/php-<ver>/sbin/php-fpm -t`; `systemctl daemon-reload` | `php-fpm -t` exit 0; unit mới `active` | Trùng socket/PID file với bản cũ → đặt tên theo `<ver>` |
| `CHK-PHP-016-11` | P3 | (khi khác nhánh) Lint + PHPCompatibility + BC + Composer + test | Bán tự động (duyệt) | Như `CHK-PHP-010-18` … `-20` | BR-SCN-042 ĐẠT | Như mục mẫu |
| `CHK-PHP-016-12` | P5 | Chuyển từng site sang socket của prefix mới (canary trước) | Bán tự động (duyệt) | Như `CHK-PHP-004-24`, `-26`, `-27` | 100% site `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-PHP-016-13` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-016-14` | P7 | Gỡ prefix cũ sau 14 ngày không request (BR-SCN-014) | Bán tự động (duyệt) | Lưu `tar -czf` của prefix cũ vào backup trước khi xoá; manifest | Prefix cũ không còn; bản nén > 0 byte có SHA-256 | Mất rollback 1 lệnh |
| `CHK-PHP-016-15` | P7 | Theo dõi bản patch mới cho build tự quản | Tự động | Mỗi lần `sync` so `PHP_VERSION` với `releases/index.php?json` | Finding xuất hiện trong ≤ 6 giờ 15 phút sau khi php.net phát hành bản mới (KR1.1) | Không có cơ chế tự build lại → người vận hành phải duyệt mục 06–13 mỗi lần |

## 12. Giả định và câu hỏi mở
| STT | Nội dung | Loại | Người quyết định |
| :--- | :--- | :--- | :--- |
| 1 | Ngày GA 8.6 (2026-11-19) là kế hoạch trên wiki.php.net, có thể dời; mốc 2027-02-17 ở SCN-PHP-013 tính lại theo ngày GA thực tế | Giả định | Tool tự tính |
| 2 | Endpoint tracker bảo mật Debian/Ubuntu/Red Hat (`CHK-PHP-015-04`) chưa kiểm chứng; phụ thuộc quyết định Q-04 của PRD | Câu hỏi mở | SRS chính |
| 3 | Debian LTS có tiếp tục vá gói `php8.2` sau 2026-12-31 hay không: chưa kiểm chứng; tool chỉ dựa vào changelog gói thực tế | Giả định | Tool tự xác định qua changelog |
| 4 | Phân loại site "công khai" ở `CHK-PHP-014-03` dựa vào DNS/IP; người vận hành có thể sửa có duyệt | Giả định | PO duyệt |
| 5 | Mục "(khi nâng nhánh)" ở SCN-PHP-011, SCN-PHP-012 gộp nhiều mục mẫu của SCN-PHP-010; khi người vận hành chọn nâng nhánh, tool sinh từng mục con theo mẫu với `chk_id` gốc + hậu tố thứ tự | Ràng buộc thiết kế | Dev |
| 6 | "Khung giờ thấp tải" (§1) là đề xuất: khoá cấu hình `maintenance_window`, mặc định 01:00–05:00 và ngưỡng 20% P95 cần PO duyệt; chưa quyết định tool có chặn mục restart/build ngoài khung giờ hay chỉ cảnh báo trong dry-run | Câu hỏi mở | PO |

## 13. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22. Nguồn dùng chung (php.net, endoflife.date, migration guide, framework, loader, Composer, công cụ quét) xem [version-scenarios-php.md §12](version-scenarios-php.md#12-tài-liệu-tham-chiếu-references).

| Nguồn | URL | Dùng cho |
| :--- | :--- | :--- |
| php.net bản phát hành hiện hành | https://www.php.net/releases/active.php | Bản patch tối thiểu 8.2.35, 8.3.36, 8.4.27, 8.5.12 |
| php.net pre-release | https://www.php.net/pre-release-builds.php?format=json | 8.6.0RC4 (21 October 2026), SHA-256 tarball |
| Lịch PHP 8.6 | https://wiki.php.net/todo/php86 | RC5 2026-11-05, GA 2026-11-19 |
| php-src UPGRADING 8.6 | https://raw.githubusercontent.com/php/php-src/PHP-8.6/UPGRADING | BC-PHP-86-01 |
| NVD API 2.0 (qua PRD §2.2) | https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-109618 | CVSS 9.8, khoảng ảnh hưởng `< 8.2.35`, `< 8.3.36`, `< 8.4.27`, `< 8.5.12` |
| Launchpad API | https://api.launchpad.net/1.0/ubuntu/+archive/primary?ws.op=getPublishedSources&source_name=php-defaults&exact_match=true | Gói PHP mặc định theo bản Ubuntu |
| Debian Sources API | https://sources.debian.org/api/src/php-defaults/, `/api/src/php8.2/`, `/api/src/php8.4/` | Gói PHP theo bản Debian, `8.2.32-1~deb12u1`, `8.4.24-1~deb13u1` |
| endoflife.date OS | https://endoflife.date/api/ubuntu.json, `/api/debian.json`, `/api/rhel.json` | Hạn hỗ trợ OS (SCN-PHP-015) |
| Remi wizard | https://rpms.remirepo.net/wizard/ | 8.5.11, 8.4.26 tại 2026-10-22 (độ trễ kho) |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `php_state`, `pkg_has_cves`, `php_upgrade`, `php_mitigation_ini` (`fatal_error_backtraces` cho 8.5), `php_unmitigate`, `restart_php_services`, manifest |
