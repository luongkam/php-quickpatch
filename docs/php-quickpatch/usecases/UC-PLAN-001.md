---
id: DOC-UC-QP-PLAN-001
title: Đặc tả Use Case UC-PLAN-001 — Chọn phiên bản đích và sinh kế hoạch nâng cấp
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PLAN-001, plan, target-version, checklist, compatibility, phpcompatibility, composer, canary]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-SCN-PHP-001
  - DOC-SRS-QP-SCN-NODE-001
  - DOC-SRS-QP-ENV-001
  - DOC-API-QP-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-PLAN-001
  - DIAG-STATE-QP-PLAN-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PLAN-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-PLAN-001`, `FR-CLI-CMD-002`, `FR-PLAN-GEN-002` trong bảng FR liên quan với functional-requirements.md |

## UC-PLAN-001: Chọn phiên bản đích và sinh kế hoạch nâng cấp

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`). Sinh kế hoạch là job `read` nên Operator không root được tạo kế hoạch; mục thay đổi hệ thống chỉ chạy được khi có root (spec §2.3).
- **Tác nhân hỗ trợ**: `SYS-02` Packagist (`repo.packagist.org`), npm registry, nguồn tải công cụ quét; `SYS-03` package manager/panel (kiểm kho có nhánh đích, chỉ đọc); System: Job runner (job `plan create`).
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh plan create`, `qp-feeds.py` (sinh kế hoạch), công cụ quét trong `STATE_DIR/tools/php`; console SCR-003 → SCR-004.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: từ SCR-002 tới checklist hoàn chỉnh ≤ 4 thao tác, không gõ lệnh (`NFR-USE-002`, KR3.1); thời gian sinh kế hoạch gồm quét tương thích ≤ 120 s cho 10.000 file `.php`, 300 package (`NFR-PERF-005`, chưa đo).
  - Chủ site/khách hàng hosting: quét tương thích không chạy mã dự án, không ghi docroot, Composer chạy trên bản sao với `--no-scripts --no-plugins` (`BR-CMPT-003`, `BR-CMPT-004`).
  - `PER-04`: mỗi bước checklist có mã kịch bản, lệnh/thao tác cụ thể, điều kiện hoàn thành kiểm tra được (KR3.3); lý do chọn đích khác đề xuất được ghi audit (`BR-PLAN-001`).
  - Chủ ứng dụng: chỉ tên package gửi tới Packagist/npm registry, không gửi phiên bản đang dùng (`BR-DATA-003`).
- **Tiền điều kiện (Pre-conditions)**:
  - Đã có kết quả `assess` của runtime (UC-ASMT-001) với danh sách ứng viên.
  - Runtime không `locked` (`FR-SCN-LOCK-001`) và không có kế hoạch `in_progress` (`BR-PLAN-002`).
  - Python ≥ 3.6; phiên console hợp lệ.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `STATE_DIR/plans/<plan_id>/` có `plan.json`, `items.json`, `events.jsonl` (ghi tạm + `rename`), kế hoạch `qp.plan/1` ở `draft` với `target`, `site_order[]`, `canary_site_id`, `blocked_sites[]`, `upgrade_items[]`, `preconditions[]`, `compat_verdict` từng site, hạn duyệt, dấu vân tay `bundle_id` + `catalog_version` + `scan_fingerprint`; kế hoạch `draft`/`approved` cũ của runtime chuyển `cancelled` có audit.
  - **Đảm bảo tối thiểu**: 0 thay đổi gói/dịch vụ/site; bản sao `STATE_DIR/work/<plan_id>/` bị xoá sau phân tích Composer; kế hoạch cũ giữ nguyên khi tạo kế hoạch thất bại trước bước 6.
- **Kích hoạt (Trigger)**: Operator bấm "Lập kế hoạch" trên SCR-003, hoặc chạy `plan create --runtime-id ID --target X.Y|N [--sites a,b] [--reason TEXT] --json`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator bấm "Lập kế hoạch" trên SCR-003; console hiển thị ứng viên (`types[]`, `selectable`, `not_selectable_reason`, `installable`) từ kết quả `assess` mới nhất (`FR-CON-PLAN-001`).
2. Operator chọn nhánh đích, phạm vi site (mặc định mọi site dùng runtime) và nhập lý do 20–500 ký tự khi đích không mang nhãn `RECOMMENDED`, rồi bấm "Sinh kế hoạch".
3. Console kiểm Host/phiên/CSRF, regex tham số (nhánh PHP `^[4-9]\.[0-9]$`, dòng Node.js `^[0-9]{1,2}$`), tạo job `plan create` loại `read` và hiển thị tiến độ qua SSE trên SCR-004 (`BR-CON-008`, `FR-CLI-CMD-002`).
4. CLI kiểm Python ≥ 3.6, lấy khoá chia sẻ `STATE_DIR/.lock`.
5. Hệ thống kiểm đích: ứng viên `selectable=true`; không phải `EOL`, `PRE_RELEASE`, `UNKNOWN`, "6.x"; với site production không phải Node.js `CURRENT` trước ngày `lts`; đích khác `RECOMMENDED` có lý do ≥ 20 ký tự (`FR-PLAN-TGT-001`).
6. Hệ thống chuyển kế hoạch `draft`/`approved` cũ của runtime sang `cancelled` và ghi audit (`BR-PLAN-002`).
7. Hệ thống kiểm tiền điều kiện cài song song: đĩa trống ≥ 2 GB, RAM khả dụng ≥ 512 MB, root hoặc API panel, OS còn hỗ trợ, kho có nhánh đích (`FR-UPG-PRE-001`, `BR-SCN-016`).
8. Hệ thống kiểm/cài công cụ quét theo phiên bản và hash cố định của catalog vào `STATE_DIR/tools/php` (`FR-CMPT-TOOL-001`, `BR-CMPT-006`, `BR-SEC-005`).
9. Với mỗi site trong phạm vi, hệ thống quét tương thích chỉ đọc:
   - luật breaking change tĩnh dải `($OLD, $NEW]` trên `*.php`, `*.inc`, `*.phtml` (`FR-CMPT-CODE-001`, `BR-CMPT-001`);
   - PHPCompatibility với `testVersion $NEW`, song song theo số vCPU (`FR-CMPT-CODE-002`, `BR-CMPT-002`);
   - nền tảng Composer trên bản sao và phiên bản tối thiểu thoả trên Packagist, cache 24 giờ (`FR-CMPT-COMP-001`, `FR-CMPT-COMP-002`);
   - `engines.node` và native addon cho ứng dụng Node.js (`FR-CMPT-NPM-001`, `FR-CMPT-NPM-002`);
   - directive ini bị gỡ, extension trên runtime đích, framework/CMS, loader mã hoá (`FR-CMPT-INI-001`, `FR-CMPT-EXT-001`, `FR-CMPT-FWK-001`, `FR-CMPT-LDR-001`).
10. Hệ thống kết luận tương thích từng site: `PASS`, `FAIL` (còn hit `error` chưa miễn trừ) hoặc `PENDING` (phần cần `$NEW_BIN` chưa chạy) (`FR-CMPT-RES-001`).
11. Hệ thống lắp checklist hiệu lực từ kịch bản `VERSION` + `OVERLAY` + hành động playbook, thay biến `$OLD`, `$NEW`, `$SITE`, gắn nhãn "chưa kiểm chứng" cho lệnh `verified=false` (`FR-SCN-CHK-001`).
12. Hệ thống lập danh sách thư viện/dependency phải nâng (extension, Composer package, npm package, native addon, framework/CMS, loader) gắn với mục P4 (`FR-PLAN-DEP-001`).
13. Hệ thống sinh kế hoạch: tạo `plan_id`, chế độ `same_branch` hoặc `cross_branch`, thêm mục P2 vá cùng nhánh đứng trước mục cài song song khi runtime `vulnerable` và còn hỗ trợ, chia checklist theo site, lưu dấu vân tay đầu vào (`FR-PLAN-GEN-001`, `BR-UPG-006`).
14. Hệ thống sắp `site_order` (site `PASS` theo số file `*.php` tăng dần rồi `site_id`), đặt site đầu làm canary, đưa site `FAIL` vào `blocked_sites[]` (`FR-PLAN-GEN-002`, `BR-PLAN-004`).
15. Hệ thống tính hạn duyệt: EOL − 30 ngày cho nhánh `SECURITY_ONLY`/`MAINTENANCE_LTS` hoặc còn ≤ 90 ngày tới EOL (`FR-PLAN-DL-001`, `BR-SCN-049`, `BR-SCN-029`).
16. Hệ thống ghi `plans/<plan_id>/` bằng ghi tạm + `rename`, ghi audit (kèm lý do khi đích khác đề xuất), xuất envelope `qp.plan/1`, thoát 0 (mọi site `PASS`) hoặc 1 (có site `FAIL`/`PENDING`).
17. Console mở checklist trên SCR-004: các giai đoạn P1–P7, kết luận tương thích từng site, `upgrade_items[]`, thứ tự site, canary, hạn duyệt, tiền điều kiện.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. Đích không mang nhãn `RECOMMENDED` và lý do < 20 ký tự**:
  - 2a1. Hệ thống trả `ERR-PLAN-422-01` "Vui lòng nhập lý do tối thiểu 20 ký tự."; use case quay lại bước 2.
- **3a. Tham số sai regex hoặc hàng đợi đủ 20 job**:
  - 3a1. Console trả `ERR-CON-422-01` hoặc `ERR-JOB-429-01`.
- **4a. Thiếu Python ≥ 3.6 hoặc khoá độc quyền đang bị lượt ghi giữ**:
  - 4a1. CLI thoát 2 với `ERR-CLI-424-01` hoặc `ERR-CLI-423-01`.
- **5a. Đích là nhánh `EOL`, `PRE_RELEASE`, `UNKNOWN`, chuỗi "6.x", hoặc Node.js `CURRENT` chưa tới ngày `lts` cho site production**:
  - 5a1. Hệ thống trả `ERR-SCN-409-02` (`BR-UPG-004`, `BR-SCN-007`); staging cách ly được dùng nhánh trung gian tối đa 30 ngày (ngoại lệ `BR-SCN-007`).
- **5b. Không có nhánh đích thoả framework, loader hoặc `engines` đã phát hiện**:
  - 5b1. Hệ thống trả `ERR-SCN-409-01`, đề xuất nâng framework/CMS trước hoặc chọn đích thủ công có lý do (`BR-SCN-005`, `BR-SCN-006`).
- **5c. Runtime đã có kế hoạch `in_progress`**:
  - 5c1. Hệ thống trả `ERR-PLAN-409-01` kèm `plan_id` đang thực hiện; Operator hoàn tất hoặc huỷ kế hoạch đó (UC-PLAN-002).
- **5d. Dữ liệu cũ > 90 ngày (`EXPIRED`)**:
  - 5d1. Hệ thống trả `ERR-SCN-503-01`; chỉ cho kế hoạch `same_branch` (`BR-FEED-005`).
- **7a. Tiền điều kiện không đạt** (vd đĩa trống 1,2 GB < 2 GB):
  - 7a1. Hệ thống ghi `ERR-SCN-412-01` vào `preconditions[]` của kế hoạch, chặn mục P2 cài song song; kế hoạch vẫn được sinh để Operator bổ sung tài nguyên.
- **8a. Công cụ tải về lệch SHA-256 của catalog**:
  - 8a1. Hệ thống xoá file, ghi `ERR-PTCH-502-01`, chạy tiếp với bộ luật BC tĩnh.
- **8b. Offline hoặc lỗi mạng, chưa có công cụ**:
  - 8b1. Hệ thống ghi `ERR-CMPT-424-01`; chỉ chạy `FR-CMPT-CODE-001`; phần PHPCompatibility/Composer của site ở `PENDING`.
- **9a. File nguồn > 2 MiB**:
  - 9a1. Hệ thống bỏ qua và liệt kê file, cảnh báo `ERR-CMPT-413-01`.
- **9b. Không có PHP ≥ 7.2 để chạy PHP_CodeSniffer**:
  - 9b1. Phần PHPCompatibility `PENDING`, cảnh báo `ERR-CMPT-422-01`; chạy lại sau khi cài `$NEW` (UC-PLAN-003).
- **9c. Quét 1 site vượt 1.800 s**:
  - 9c1. Hệ thống dừng phần chưa xong, đánh dấu `PENDING`, ghi `ERR-CMPT-504-01`; Operator khai báo thư mục loại trừ (lý do ≥ 20 ký tự) rồi sinh lại.
- **9d. Packagist hoặc npm registry không truy cập được, hoặc `--offline`**:
  - 9d1. `min_compatible_version = unknown`, ghi `ERR-FEED-503-01` (`BR-DATA-003`).
- **9e. Site dùng loader mã hoá không có bản chính thức cho nhánh đích**:
  - 9e1. Hệ thống ghi `ERR-SCN-409-03`, loại nhánh khỏi ứng viên, site vào `blocked_sites[]` (`BR-SCN-043`).
- **9f. Site chạy Apache `mod_php`**:
  - 9f1. Hệ thống thêm mục bước 1 PB-006 (chuyển `mod_php` → PHP-FPM cùng phiên bản) đứng trước mục chuyển site; cảnh báo `ERR-SCN-412-02` cho tới khi UC-UPG-003 `PASSED` (`BR-SCN-047`).
- **9g. Framework/CMS không có trong ma trận**:
  - 9g1. `supports_target=unknown`; checklist thêm mục `MANUAL` yêu cầu Operator xác nhận (`FR-CMPT-FWK-001`).
- **11a. Điều kiện `applies_when` của mục không thoả với dữ kiện quét** (vd site không dùng loader mã hoá):
  - 11a1. Mục được đặt `SKIPPED` ngay khi lắp checklist (`FR-SCN-CHK-001`, DOC-SRS-QP-SCN-000 §3.3).
- **13a. Runtime `vulnerable` thuộc nhánh còn hỗ trợ nhưng `min_patched = NONE`**:
  - 13a1. Không thêm mục vá cùng nhánh (ngoại lệ `BR-UPG-006`).
- **17a. Operator thoát giữa chừng khi job đang chạy**:
  - 17a1. Job tiếp tục; Operator xem lại tại SCR-006 (UC-JOB-001); job vượt 1.800 s → `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-USE-002`: từ SCR-002 tới checklist ≤ 4 thao tác (chọn runtime → chọn đích → "Sinh kế hoạch" → mở checklist).
- `NFR-PERF-005`: sinh kế hoạch gồm quét ≤ 120 s cho 10.000 file `.php`, 300 package (chưa đo, `A-SRS-05`).
- `NFR-REL-006`: 0 file `plan.json` hỏng sau 100 lần `kill -9` ngẫu nhiên.
- `NFR-CAP-002`: `tools/php` ≤ 80 MB (chưa đo).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-PLAN-001`, `BR-PLAN-002`, `BR-PLAN-004`, `BR-PLAN-006` | Đích khác đề xuất, 1 kế hoạch hiệu lực, canary, dấu vân tay lỗi thời | 2, 6, 13, 14 |
| `BR-UPG-004`, `BR-UPG-006`, `BR-ASMT-002` | Đích bị cấm, vá cùng nhánh trước, điều kiện chọn ứng viên | 5, 13 |
| `BR-SCN-005`, `BR-SCN-006`, `BR-SCN-007`, `BR-SCN-016` | Chọn nhánh đích PHP/Node.js, cấm nhánh trung gian, tiền điều kiện | 5, 7 |
| `BR-CMPT-001`..`BR-CMPT-006`, `BR-SEC-005`, `BR-DATA-003` | Tập file, binary PHPCS, Composer trên bản sao, không chạy mã dự án, thời gian tối đa, công cụ cố định, checksum, dữ liệu gửi ra | 8, 9 |
| `BR-SCN-041`..`BR-SCN-047`, `BR-SCN-022`, `BR-SCN-025` | Dải BC, điều kiện ĐẠT, loader, Composer, extension, ini, `mod_php`, native addon, `engines` | 9, 10 |
| `BR-SCN-018`, `BR-ENV-010`, `BR-ENV-003` | Phụ thuộc mục, lệnh chưa kiểm chứng, chuyển tuần tự có canary | 11, 14 |
| `BR-SCN-029`, `BR-SCN-049` | Hạn duyệt kế hoạch Node.js/PHP | 15 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | 1, 3, 17 |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | 3, 16 |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | 5 |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | 7 |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | 8 |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | 9 |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | 9 |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | 9 |
| `FR-CMPT-COMP-002` | Tra phiên bản tối thiểu thoả trên Packagist | 9 |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | 9 |
| `FR-CMPT-NPM-002` | Phát hiện native addon | 9 |
| `FR-CMPT-INI-001` | Quét directive ini bị gỡ | 9 |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | 9 |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | 9 |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | 9 |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | 10 |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | 11 |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | 12 |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | 13, 16 |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | 14 |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | 15 |

### Giao diện và API liên quan
- Màn hình: `SCR-003` (nút "Lập kế hoạch"), `SCR-004` Kế hoạch nâng cấp & checklist.
- API: `GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`, `GET /api/v1/plans/{plan_id}`, `GET /api/v1/plans/{plan_id}/checklist-items`, `GET /api/v1/plans/{plan_id}/compatibility`, `GET /api/v1/jobs/{job_id}/events`.

### Quan hệ với use case khác
- `<<extend>>` UC-ASMT-001 (điểm mở rộng: nút "Lập kế hoạch").
- Tiếp nối bởi UC-PLAN-002 (duyệt) và UC-PLAN-003 (thực hiện checklist).

### Ghi chú và tài liệu tham chiếu
- Phiên bản công cụ quét cố định trong catalog (PHPCompatibility 10.0.0-alpha2, PHP_CodeSniffer 4.0.4, Composer 2.10.3 và 2.2 LTS, Rector 2.7.0) theo DOC-SRS-QP-SCN-PHP-001 §7; use case không kiểm chứng lại các số phiên bản này.
- Nguồn: [functional-requirements.md §5, §6](../srs/functional-requirements.md), [flows.md §4](../srs/flows.md), [api-spec-plans.md](../api/api-spec-plans.md).
