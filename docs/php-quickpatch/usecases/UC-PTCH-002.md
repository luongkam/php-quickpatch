---
id: DOC-UC-QP-PTCH-002
title: Đặc tả Use Case UC-PTCH-002 — Vá dependency dự án (Composer, npm, WordPress)
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PTCH-002, fix, composer, npm, wordpress, wp-cli, project-level, osv]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PTCH-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-DEP-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Hiển thị màn hình Findings thư viện (SCR-005)" |

## UC-PTCH-002: Vá dependency dự án (Composer, npm, WordPress)

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root / shared hosting (`PER-01`, `PER-02`, `PER-03`). Không root: chỉ dự án trong thư mục user sở hữu (`BR-PTCH-003`).
- **Tác nhân hỗ trợ**: `SYS-02` OSV (tra lại sau vá), Packagist/npm registry (do `composer`/`npm` gọi), wordpress.org (do `wp-cli` gọi), nguồn tải `wp-cli.phar` + `.sha512`; System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh fix --only composer,npm,wp [--path DIR]` (kế thừa v0.1 `fix_composer`, `fix_npm`, `wp_cmd`); console SCR-005.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`, `PER-03`: package có advisory được nâng lên bản sửa trong cùng ràng buộc của dự án; WordPress core lên bản ≥ `min_patched` của nhánh.
  - Chủ ứng dụng: lệnh chạy dưới quyền chủ thư mục (`runuser`), npm không dùng `--force`, lỗi thì khôi phục `composer.json/lock` hoặc file npm (`BR-PTCH-006`).
  - Kỹ sư bảo mật: `wp-cli.phar` và `composer.phar` tải về được kiểm SHA-512/SHA-256 trước khi chạy (`BR-SEC-005`); lệch checksum core WordPress được báo như dấu hiệu xâm nhập, không tự xoá file (`BR-SEC-003`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có `dependency_findings[]`/`wordpress_findings[]` từ lượt scan (UC-ASMT-002).
  - Có `composer`/`composer.phar`, `npm`, `wp-cli` hoặc tải được bản đã kiểm checksum.
  - Không có job `write` khác đang chạy; `STATE_DIR` còn ≥ 50 MB trống.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: package dính advisory đã nâng, OSV tra lại không còn finding; WordPress ở phiên bản ≥ `min_patched`, `wp core verify-checksums` đạt; manifest có `composer-install`/`npm-ci` và `copy` cho file lock; audit intent/result.
  - **Đảm bảo tối thiểu**: khi `composer update` lỗi, `composer.json/lock` được khôi phục và `composer install` chạy lại; package còn lại được báo issue `high`; 0 file ngoài thư mục dự án và `STATE_DIR` bị ghi bởi tool.
- **Kích hoạt (Trigger)**: Operator bấm "Vá dự án" trên SCR-005, hoặc chạy `fix --only composer,npm,wp [--path DIR]`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chọn dự án trên SCR-005 và bấm "Vá dự án"; console tạo job dry-run `fix --json --only composer,npm,wp --path <dir thuộc projects[]> --dry-run` (`FR-CON-DEP-001`, `BR-CON-008`).
2. Console hiển thị SCR-011: package sẽ nâng, file lock sẽ đổi, site bị ảnh hưởng, khả năng hoàn tác; Operator xác nhận trong ≤ 15 phút (UC-CON-003).
3. CLI lấy khoá độc quyền, ghi audit intent, tạo `STATE_DIR/backups/<run_id>/manifest` (`FR-PTCH-RBK-001`).
4. Với dự án Composer: CLI ghi `composer-install <dir>` vào manifest (phát lại sau khi khôi phục file), `backup_file` `composer.json`, `composer.lock`, chạy `composer update <pkgs> --with-all-dependencies --no-interaction --no-progress` dưới quyền chủ thư mục (`FR-PTCH-DEP-001`, `BR-PTCH-006`).
5. Với dự án npm: CLI ghi `npm-ci <dir>`, `backup_file` `package.json`, `package-lock.json`, chạy `npm audit fix --no-fund` (không `--force`) dưới quyền chủ thư mục (`FR-PTCH-DEP-002`).
6. CLI tra lại OSV cho lockfile mới; package đã sửa được đếm, package còn lại → issue `high`.
7. Với site WordPress dưới `min_patched`: CLI lấy `wp-cli` (tải `wp-cli.phar` và kiểm SHA-512 khi chưa có), `backup_file` `wp-includes/version.php`, chạy `wp core update --minor` và `wp plugin update --all --patch` dưới quyền chủ site (`FR-PTCH-WP-001`, `BR-FEED-025`).
8. CLI đọc lại phiên bản WordPress, so với `min_patched`; đạt → ghi "WordPress updated to {v}".
9. CLI chạy `wp core verify-checksums` và `wp plugin verify-checksums --all`; core khớp checksum (`FR-PTCH-WP-002`).
10. CLI ghi audit result, xuất envelope `qp.fix/1`, thoát 0; console chuyển job `SUCCEEDED` và làm mới SCR-005.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. `--path` không thuộc `projects[]` của lượt scan hoặc chứa giá trị bắt đầu bằng `-`**:
  - 1a1. Console trả `ERR-CON-422-01`, không tạo tiến trình.
- **1b. Operator không root chọn dự án không thuộc user**:
  - 1b1. Nút vá vô hiệu kèm lý do; CLI bỏ qua dự án đó với issue "needs root" (`BR-PTCH-003`, `BR-CLI-005`).
- **1c. Gọi bằng CLI**:
  - 1c1. `fix` giữ hành vi v0.1 (không hỏi xác nhận); luồng bắt đầu từ bước 3.
- **2a. Dry-run không còn hợp lệ**:
  - 2a1. Console trả 428 `ERR-JOB-428-01`.
- **3a. Không ghi được audit intent hoặc `STATE_DIR` < 50 MB**:
  - 3a1. CLI dừng trước thay đổi với `ERR-AUD-500-01` hoặc `ERR-ENV-507-01`.
- **4a. Không có `composer` và không tải/kiểm được `composer.phar`**:
  - 4a1. CLI ghi cảnh báo "composer not available", bỏ qua dự án Composer; tải về lệch SHA-256 → `ERR-PTCH-502-01`.
- **4b. `composer update` thất bại**:
  - 4b1. CLI khôi phục `composer.json/lock` từ backup, chạy `composer install --no-interaction --no-progress`, ghi `ERR-PTCH-424-02` "{dir}: composer update failed, lockfile restored (see log)."; Operator nâng major thủ công trên staging.
- **5a. `npm audit fix` không giải quyết hết lỗ hổng**:
  - 5a1. CLI ghi cảnh báo "npm audit fix could not resolve everything (no --force used)"; package còn lại → issue `high` (`ERR-PTCH-424-02` khi lệnh thoát lỗi).
- **5b. Dự án dùng `yarn.lock`/`pnpm-lock.yaml`**:
  - 5b1. CLI không vá, chỉ cảnh báo kèm lệnh `yarn npm audit`/`pnpm audit` như v0.1.
- **6a. OSV không truy cập được khi tra lại**:
  - 6a1. Kết quả sau vá ghi `ERR-FEED-503-02`; trạng thái package giữ "chưa xác minh".
- **6b. Lockfile còn package `MAL-*`**:
  - 6b1. Issue Critical kèm khuyến nghị gỡ package và xoay vòng secret (`BR-SEC-004`); tool không tự gỡ package.
- **7a. Không có `wp-cli` và không tải/kiểm được `wp-cli.phar`**:
  - 7a1. CLI ghi issue `critical` `ERR-PTCH-424-03` "wp-cli unavailable, update WordPress core to {fix} by hand".
- **8a. WordPress vẫn dưới `min_patched` sau cập nhật**:
  - 8a1. CLI ghi issue `critical` "WordPress still {v} after update attempt"; thoát 1.
- **9a. `wp core verify-checksums` báo lệch**:
  - 9a1. CLI ghi issue `high` `ERR-PTCH-424-04` "{site}: core files differ from wordpress.org checksums (possible tampering)"; không xoá/sửa file (`BR-SEC-003`); Operator xử lý theo quy trình sự cố.
- **9b. Plugin không xác minh được với wordpress.org**:
  - 9b1. CLI ghi cảnh báo liệt kê ≤ 20 plugin để Operator kiểm nguồn gốc.
- **10a. Job vượt 3.600 s hoặc bị gián đoạn**:
  - 10a1. Job `FAILED`/`INTERRUPTED` (`ERR-JOB-504-01`, `ERR-JOB-500-02`); Operator dùng `rollback <run_id>` (UC-PTCH-004).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-005`: `rollback <run_id>` khôi phục 100% file có dòng `copy`/`created` của manifest.
- `NFR-USE-006`: SCR-011 hiển thị 4/4 mục.
- `NFR-SEC-007`: 0 `shell=True`/`os.system`/`eval` ở console; argv dựng từ danh sách trắng.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-PTCH-006` | Vá cấp dự án dưới quyền chủ thư mục, npm không `--force`, khôi phục khi lỗi | 4, 5, 7 |
| `BR-PTCH-003`, `BR-CLI-005` | Giới hạn theo quyền | 1b |
| `BR-SEC-005` | Kiểm checksum `composer.phar`, `wp-cli.phar` | 4a, 7 |
| `BR-SEC-003`, `BR-SEC-004` | Không xoá file nghi vấn; package mã độc | 6b, 9a |
| `BR-FEED-025` | `min_patched` WordPress | 7, 8 |
| `BR-CON-005`, `BR-SCN-017` | Dry-run; ghi manifest trước thay đổi | 2, 3 |
| `BR-AUD-001`, `BR-AUD-004` | Audit; đóng khi lỗi | 3, 10 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | 1, 10 |
| `FR-PTCH-DEP-001` | Cập nhật Composer package có lỗ hổng | 4, 6 |
| `FR-PTCH-DEP-002` | Cập nhật npm package có lỗ hổng | 5, 6 |
| `FR-PTCH-WP-001` | Cập nhật WordPress | 7, 8 |
| `FR-PTCH-WP-002` | Kiểm tra toàn vẹn WordPress | 9 |

### Giao diện và API liên quan
- Màn hình: `SCR-005` (nút "Vá dự án"), `SCR-011`, `SCR-006`.
- API: `POST /api/v1/jobs` (`action=fix`, `only` = `composer`/`npm`/`wp`, `path`), `GET /api/v1/dependency-findings`, `GET /api/v1/projects`.

### Quan hệ với use case khác
- `<<extend>>` UC-ASMT-002 (nút "Vá dự án"); `<<include>>` UC-CON-003, UC-JOB-001; hoàn tác bằng UC-PTCH-004.
- Được gọi bởi mục P4 "nâng dependency" của UC-PLAN-003 khi nâng nhánh.

### Ghi chú, phát hiện và tài liệu tham chiếu
- Lệnh đã kiểm chứng trên `php-quickpatch.sh` v0.1.0: `fix_composer` (dòng 565–575), `fix_npm` (dòng 578–585), kiểm SHA-512 `wp-cli.phar` (dòng 610–611), `wp core update --minor`, `wp plugin update --all --patch` (dòng 634–635), `verify-checksums` (dòng 642–645), cảnh báo `yarn.lock`/`pnpm-lock.yaml` (dòng 598).
- Phát hiện: v0.1 chỉ `backup_file` `wp-includes/version.php` trước `wp core update`; `rollback` vì vậy không khôi phục được các file core khác do `wp-cli` thay. SRS (`FR-PTCH-WP-001`, `BR-PTCH-008`) chưa nêu giới hạn này. Đề xuất: SCR-011 hiển thị "cập nhật WordPress core không hoàn tác được bằng rollback" ở mục khả năng hoàn tác (chờ PO duyệt).
