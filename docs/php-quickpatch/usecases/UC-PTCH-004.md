---
id: DOC-UC-QP-PTCH-004
title: Đặc tả Use Case UC-PTCH-004 — Rollback một lượt chạy
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PTCH-004, rollback, manifest, backup, run-id, v0.1-compat]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-UPG-003
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PTCH-004 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-RBK-001` trong bảng FR liên quan với `functional-requirements.md` (`CR-FR-06`): "Hiển thị màn hình Rollback và lịch sử (SCR-007)" |

## UC-PTCH-004: Rollback một lượt chạy

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`) cho mọi lượt; Operator không root chỉ rollback thay đổi do chính user tạo (manifest trong `~/.php-quickpatch/backups`, spec §2.3).
- **Tác nhân hỗ trợ**: `SYS-03` (systemd, package manager cho `composer install`/`npm ci`, web server khi lượt có dòng `switch`); System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh rollback [ID] [--dry-run] [--json]` (kế thừa v0.1 `do_rollback`); console SCR-007.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: hoàn tác 1 lượt `fix` bằng 1 lệnh hoặc 1 nút + 1 xác nhận; khôi phục 100% file có dòng `copy`/`created` trong manifest (`NFR-REL-005`).
  - `PER-04`: mỗi lượt rollback có audit intent/result và kết quả từng dòng manifest.
  - Chủ site: được biết trước những gì không hoàn tác được: gói đã nâng qua package manager không bị hạ cấp (`BR-PTCH-008`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có ít nhất 1 thư mục `STATE_DIR/backups/<run_id>/` chứa `manifest`.
  - Không có job `write` khác đang chạy.
  - Console: phiên hợp lệ.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: các dòng manifest được phát lại theo thứ tự ngược (`tac`): `copy` → khôi phục file, `created` → xoá file, `untar` → khôi phục prefix Node.js, `composer-install`/`npm-ci` → cài lại dependency, `note` → in cảnh báo; dịch vụ PHP/Node.js liên quan được restart; in "Rollback done. Package upgrades (apt/dnf/yum) are kept."; audit result.
  - **Đảm bảo tối thiểu**: khi lượt không tồn tại, không có thay đổi nào; mỗi dòng manifest lỗi được báo riêng.
- **Kích hoạt (Trigger)**: Operator chọn 1 lượt chạy trên SCR-007 và bấm "Rollback", hoặc chạy `rollback [ID]` (ID mặc định = lượt mới nhất).

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở SCR-007; console liệt kê lượt chạy từ `backups/*/manifest` và lượt chuyển từ `switches/index.tsv` (`FR-CON-RBK-001`).
2. Operator chọn 1 lượt `fix`; console hiển thị từng dòng manifest và danh sách hành động sẽ phát lại, kèm cảnh báo "gói đã nâng không bị hạ cấp".
3. Operator bấm "Rollback"; console tạo job dry-run `rollback <run_id> --json --dry-run` và hiển thị SCR-011 (UC-CON-003).
4. Operator xác nhận 1 lần; console tạo job `rollback <run_id> --json` loại `write` qua `POST /api/v1/rollbacks` (`kind=run`).
5. CLI lấy khoá độc quyền `STATE_DIR/.lock`, ghi audit intent.
6. CLI đọc `backups/<run_id>/manifest` và phát lại theo thứ tự ngược (`FR-PTCH-RBK-002`):
   - `copy` → `cp -a` bản sao lưu về vị trí gốc;
   - `created` → xoá file, bật cờ restart PHP;
   - `untar` → giải nén lại prefix Node.js;
   - `composer-install`/`npm-ci` → chạy `composer install`/`npm ci` dưới quyền chủ thư mục;
   - `note` → in cảnh báo (vd "apt upgraded: … (packages are not downgraded by rollback)").
7. CLI restart dịch vụ PHP-FPM và Node.js liên quan như v0.1.
8. CLI in "Rollback done. Package upgrades (apt/dnf/yum) are kept.", ghi audit result, xuất envelope `qp.rollback/1`, thoát 0.
9. Console chuyển job `SUCCEEDED`, làm mới SCR-007 với kết quả từng dòng manifest.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Gọi bằng CLI**:
  - 1a1. `rollback [ID]` giữ hành vi v0.1: không hỏi xác nhận (`BR-CLI-003`); không có ID → lượt mới nhất; luồng tiếp tục từ bước 5.
- **2a. `run_id` sai regex `^[0-9]{8}-[0-9]{6}$`**:
  - 2a1. Console trả `ERR-CON-422-01`.
- **4a. Dry-run quá 15 phút hoặc khác phiên**:
  - 4a1. Console trả 428 `ERR-JOB-428-01`.
- **4b. Đã có job `rollback` cho cùng `run_id`**:
  - 4b1. Console trả `ERR-JOB-409-01`.
- **5a. Khoá bị lượt khác giữ**:
  - 5a1. CLI in `ERR-CLI-423-01`, thoát 2; job console chờ ≤ 30 phút rồi `ERR-JOB-409-02`.
- **5b. Không ghi được audit intent**:
  - 5b1. CLI huỷ, `ERR-AUD-500-01`.
- **6a. Không có lượt backup cho ID**:
  - 6a1. CLI in "No backup run found in {dir}" (`ERR-PTCH-404-01`), thoát 2; console trả 404 với cùng mã.
- **6b. Lượt có dòng `switch` (lượt chuyển site)**:
  - 6b1. CLI chuyển sang quy trình R1–R7 của rollback site (UC-UPG-004, `BR-PTCH-008`).
- **6c. Khi phát lại hành động `reload`, kiểm cú pháp cấu hình khôi phục thất bại**:
  - 6c1. CLI không reload, giữ cấu hình đang chạy, ghi `ERR-ENV-500-03` (Critical); Operator can thiệp thủ công.
- **6d. Operator không root chọn lượt do root tạo**:
  - 6d1. Lượt không hiển thị trong danh sách của user; gọi trực tiếp → `ERR-PTCH-404-01` (thư mục backup của user không chứa lượt đó).
- **8a. ≥ 1 dòng manifest phát lại lỗi** (vd thư mục cha của file gốc đã bị xoá):
  - 8a1. CLI ghi cảnh báo cho từng dòng, tiếp tục dòng kế tiếp; thoát 1.
- **9a. Job vượt 600 s** (timeout nhóm "khác" của `BR-JOB-008`; `rollback` lượt chạy không thuộc nhóm `migrate rollback` 300 s):
  - 9a1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-005`: khôi phục 100% file có dòng `copy`/`created` của manifest.
- `NFR-CMP-001`: hành vi `rollback [ID]` của v0.1 giữ nguyên (`BR-CLI-002`).
- `NFR-CAP-003`: `backups/` không bị tự xoá ở Phase 1; cảnh báo khi > 1 GiB.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-PTCH-008` | Phát lại manifest ngược; gói không hạ cấp; lượt có `switch` dùng R1–R7 | 6 |
| `BR-CLI-002`, `BR-CLI-003`, `BR-CLI-004` | Tương thích v0.1, không hỏi xác nhận, mã thoát | 1a, 8 |
| `BR-CON-005`, `BR-CON-008` | Dry-run; regex `run_id` | 2, 3 |
| `BR-JOB-002`, `BR-JOB-008` | Khoá độc quyền; timeout | 5, 9a |
| `BR-AUD-001`, `BR-AUD-004` | Audit; đóng khi lỗi | 5, 8 |
| `BR-ENV-005` | Kiểm cú pháp trước reload | 6c |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | 1–4, 9 |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | 5–8 |

### Giao diện và API liên quan
- Màn hình: `SCR-007` Rollback & lịch sử thay đổi, `SCR-011`.
- API: `GET /api/v1/backup-runs`, `GET /api/v1/backup-runs/{run_id}`, `POST /api/v1/rollbacks` (`kind=run`).

### Quan hệ với use case khác
- Hoàn tác kết quả của UC-PTCH-001, UC-PTCH-002, UC-PTCH-003; lượt có `switch` chuyển sang UC-UPG-004.
- `<<include>>` UC-CON-003, UC-JOB-001.

### Ghi chú, phát hiện và tài liệu tham chiếu
- Hành vi đã kiểm chứng trên `php-quickpatch.sh` v0.1.0 `do_rollback` (dòng 807–825): đọc manifest bằng `tac`, các hành động `copy`, `created`, `untar`, `composer-install`, `npm-ci`, `note`; thông điệp "No backup run found in …" thoát 2; "Rollback done. Package upgrades (apt/dnf/yum) are kept."
- Giới hạn cần hiển thị ở SCR-011: cập nhật WordPress core bằng `wp-cli` chỉ sao lưu `version.php` (xem UC-PTCH-002); mitigation trong container không có dòng manifest (xem UC-PTCH-003).
- Tên schema `qp.rollback/1` theo quy ước `qp.<lệnh>/<major>` của `FR-CLI-JSON-001`.
