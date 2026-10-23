---
id: DOC-UC-QP-UPG-007
title: Đặc tả Use Case UC-UPG-007 — Gỡ runtime cũ không còn sử dụng
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-007, migrate-remove-old, cleanup, p7, double-confirm, rollback-unavailable]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-ENV-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-007 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-UPG-007: Gỡ runtime cũ không còn sử dụng

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`).
- **Tác nhân hỗ trợ**: `SYS-03` package manager/panel (gỡ gói/prefix), log FPM/access, `ps`; System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh migrate remove-old --runtime-id <runtime_id>`; mục P7 "Gỡ nhánh cũ" của kế hoạch; console SCR-004.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng). Ưu tiên P2 (`FR-UPG-RMV-001`).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: giảm số runtime EOL còn cài trên máy (KR2.1: tỉ lệ runtime EOL phục vụ site giảm ≥ 50% sau 90 ngày) mà không phá site còn dùng.
  - Chủ site: runtime chỉ bị gỡ khi 14 ngày liên tục không có tiến trình hoặc request dùng nó (`BR-SCN-014`).
  - `PER-04`: Operator được cảnh báo rõ trước khi duyệt rằng các lượt chuyển trước đó mất khả năng rollback 1 lệnh; quyết định có xác nhận kép và audit.
- **Tiền điều kiện (Pre-conditions)**:
  - Mọi site/ứng dụng/cron từng dùng `$OLD` đã chuyển `PASSED`.
  - 14 ngày liên tục không có tiến trình hoặc request dùng `$OLD` (log FPM/access hoặc `ps`).
  - `serve` chạy root; kế hoạch `in_progress`.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: gói/prefix của `$OLD` đã gỡ; danh sách gói/prefix lưu trong manifest; các `switch_record` liên quan có `rollback_available=false`; mục P7 `DONE`; audit.
  - **Đảm bảo tối thiểu**: khi điều kiện 14 ngày không đạt, không có gói nào bị gỡ.
- **Kích hoạt (Trigger)**: Hệ thống đề xuất mục P7 "Gỡ PHP/Node.js {old}" khi điều kiện 14 ngày đạt; Operator bấm "Chạy" trên SCR-004, hoặc chạy `migrate remove-old --runtime-id <id> --yes`.

### Luồng sự kiện chính (Main Success Scenario)
1. Hệ thống kiểm mức sử dụng `$OLD` trong 14 ngày gần nhất và chỉ hiển thị mục P7 "Gỡ nhánh cũ" khi 0 tiến trình/request (`FR-UPG-RMV-001`, `BR-SCN-014`).
2. Operator bấm "Chạy"; hệ thống chạy dry-run: liệt kê gói/prefix sẽ gỡ, pool cũ, lượt chuyển sẽ mất khả năng rollback; SCR-011 hiển thị cảnh báo "rollback 1 lệnh không còn khả dụng cho các lượt chuyển trước" trước nút duyệt.
3. Operator xác nhận kép bằng cách gõ lại `runtime_id` (`BR-CON-006`); hệ thống ghi audit cả 2 bước.
4. CLI lấy khoá độc quyền, ghi audit intent, lưu danh sách gói/prefix vào manifest.
5. CLI gỡ gói/prefix của `$OLD` theo playbook.
6. CLI đánh dấu `rollback_available=false` trên các `switch_record` liên quan.
7. CLI ghi audit result, đặt mục P7 `DONE`, xuất `qp.migrate/1`, thoát 0.
8. Console làm mới SCR-004, SCR-007 (lượt chuyển hiển thị "runtime cũ đã gỡ").

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Còn site/tiến trình dùng `$OLD` trong 14 ngày**:
  - 1a1. Hệ thống trả `ERR-UPG-412-01` "Không thể gỡ {runtime}: còn {count} site/tiến trình dùng trong 14 ngày qua." kèm danh sách.
- **1b. `runtime_id` sai regex hoặc không có trong kết quả scan**:
  - 1b1. `ERR-CON-422-01` hoặc `ERR-ASMT-404-01`.
- **2a. `serve` không root**:
  - 2a1. 403 `ERR-CLI-403-01`; gọi CLI không root → `ERR-CLI-403-01`, thoát 2.
- **3a. Gõ lại sai `runtime_id` hoặc dry-run quá 15 phút**:
  - 3a1. 428 `ERR-JOB-428-01`.
- **3b. Gọi CLI không TTY thiếu `--yes`**:
  - 3b1. `ERR-CLI-428-01`.
- **4a. Không ghi được audit intent**:
  - 4a1. `ERR-AUD-500-01`, không gỡ.
- **5a. Gỡ gói thất bại (phụ thuộc gói khác)**:
  - 5a1. CLI dừng, ghi lỗi trong `errors[]`, thoát 2; manifest giữ danh sách gói để cài lại.
- **8a. Sau khi gỡ, Operator cần rollback 1 lượt chuyển cũ**:
  - 8a1. UC-UPG-004 trả `ERR-ENV-410-01`; Operator cài lại `$OLD` bằng `migrate install` theo danh sách gói trong manifest.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-002`: audit intent/result 100%.
- `NFR-USE-006`: SCR-011 hiển thị đủ 4/4 mục, trong đó mục "khả năng hoàn tác" ghi rõ mất khả năng rollback.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCN-014` | Gỡ nhánh cũ sau 14 ngày không dùng; cảnh báo mất rollback | 1, 2 |
| `BR-ENV-008` | Giữ runtime cũ tới khi đủ điều kiện gỡ | 1 |
| `BR-CON-006` | Xác nhận kép cho `migrate remove-old` | 3 |
| `BR-SCN-017`, `BR-AUD-001`, `BR-AUD-004` | Manifest; audit | 4, 7 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | 1–7 |

### Giao diện và API liên quan
- Màn hình: `SCR-004` (mục P7), `SCR-011` (xác nhận kép), `SCR-007`.
- API: `POST /api/v1/jobs` (`action=migrate_remove_old`, `confirm_retype` = `runtime_id`).

### Quan hệ với use case khác
- Thực hiện sau UC-UPG-002/UC-UPG-005/UC-UPG-006 `PASSED`; ảnh hưởng UC-UPG-004 (`ERR-ENV-410-01`).

### Ghi chú và tài liệu tham chiếu
- `FR-UPG-RMV-001`: [functional-requirements.md §8.2](../srs/functional-requirements.md); `BR-SCN-014`: [version-scenarios-common.md §4](../srs/version-scenarios-common.md).
