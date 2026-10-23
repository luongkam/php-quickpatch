---
id: DOC-UC-QP-UPG-004
title: Đặc tả Use Case UC-UPG-004 — Rollback 1 site bằng 1 lệnh
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-004, rollback-site, migrate-rollback, r1-r7, manifest, switch]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-UPG-003
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-004 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-RBK-001` trong bảng FR liên quan với `functional-requirements.md` (`CR-FR-06`): "Hiển thị màn hình Rollback và lịch sử (SCR-007)" |

## UC-UPG-004: Rollback 1 site bằng 1 lệnh

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`); Operator không root cho ứng dụng Node.js PB-016/PB-018 của chính user.
- **Tác nhân hỗ trợ**: `SYS-03` web server, PHP-FPM, API/CLI panel, systemd/pm2, Docker Compose; System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh migrate rollback <site_id> [<run_id>] [--purge-pool]` (bí danh `rollback-site`); console SCR-007, nút rollback trên dải cảnh báo SCR-002.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: site trở lại `$OLD` bằng 1 lệnh CLI hoặc 1 nút + 1 xác nhận, R1–R6 ≤ 60 s P95 (`NFR-ENV-02`, KR4.2).
  - Khách truy cập site: reload graceful, 0 phản hồi 5xx do reload (`NFR-ENV-04`); trang chủ trả mã HTTP bằng mã baseline sau rollback.
  - `PER-04`: `switch_record` ghi `ROLLED_BACK`, `t_rollback_end`, lý do `MANUAL`; audit intent/result.
- **Tiền điều kiện (Pre-conditions)**:
  - Có lượt chuyển của site ở `SWITCHED`, `HC_RUNNING`, `PASSED` hoặc `HC_FAILED_KEPT` với manifest trong `STATE_DIR/backups/<run_id>/`.
  - Binary `$OLD` còn trên máy (`BR-SCN-014`, `BR-ENV-008`).
  - Console: phiên hợp lệ; `serve` chạy root.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: lớp gán của site trỏ `$OLD`; `switch_record.status = ROLLED_BACK`; các site còn lại của kế hoạch dừng (`BR-UPG-003`); kế hoạch được phép đóng `rolled_back` (`BR-PLAN-007`).
  - **Đảm bảo tối thiểu**: khi cấu hình khôi phục không qua kiểm cú pháp, cấu hình đang chạy không bị reload; lỗi Critical được báo để Operator can thiệp thủ công.
- **Kích hoạt (Trigger)**: Operator chọn lượt chuyển trên SCR-007 (hoặc nút rollback ở dải cảnh báo `HC_FAILED_KEPT` trên SCR-002) và bấm "Rollback"; hoặc chạy `migrate rollback <site_id> [<run_id>] --yes`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở SCR-007; console liệt kê lượt chuyển từ `switches/index.tsv` kèm trạng thái và danh sách hành động sẽ phát lại (`FR-CON-RBK-001`).
2. Operator chọn lượt chuyển của site và bấm "Rollback"; console tạo job dry-run `migrate rollback <site_id> <run_id> --yes --json --dry-run` và hiển thị SCR-011 (UC-CON-003).
3. Operator xác nhận 1 lần; console gửi `POST /api/v1/rollbacks` (`kind=site`) tạo job `write`.
4. **R1**: CLI tìm lượt: `run_id` chỉ định, hoặc thư mục `backups/*` mới nhất có dòng `switch<TAB><site_id>` ở `SWITCHED`/`HC_RUNNING`/`PASSED` (≤ 1 s) (`FR-UPG-RBK-001`).
5. **R2**: CLI kiểm binary `$OLD` còn tồn tại (≤ 1 s).
6. **R3**: CLI lấy khoá `flock` (≤ 5 s), ghi audit intent.
7. **R4**: CLI phát lại manifest của lượt theo thứ tự ngược, chỉ các dòng thuộc lượt: `copy`, `panel`, `link`, `systemd`, `pm2`, `compose`; `created` chỉ xoá khi có `--purge-pool` (≤ 30 s).
8. **R5**: CLI thực hiện hành động `reload` cuối cùng: kiểm cú pháp, graceful reload (≤ 10 s) (`BR-ENV-005`, `BR-ENV-006`).
9. **R6**: CLI xác minh lớp gán trỏ lại `$OLD` bằng lệnh liệt kê của playbook và trang chủ trả mã HTTP bằng mã baseline (≤ 10 s).
10. **R7**: CLI ghi `switch_record.status = ROLLED_BACK`, `t_rollback_end`, lý do `MANUAL`, audit result; dừng các site còn lại của kế hoạch (`BR-UPG-003`); thoát 0.
11. Console làm mới SCR-007, SCR-009; kế hoạch hiển thị lựa chọn đóng `rolled_back` hoặc xử lý lỗi rồi chuyển lại (UC-PLAN-002).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Gọi bằng CLI**:
  - 1a1. Lệnh ghi mới: có TTY hỏi `y/N`; không TTY thiếu `--yes` → `ERR-CLI-428-01`; luồng tiếp tục từ bước 4.
- **2a. `site_id`/`run_id` sai regex**:
  - 2a1. Console trả `ERR-CON-422-01`.
- **2b. Chọn `--purge-pool`**:
  - 2b1. Bước R4 xoá thêm file pool/handler đích (dòng `created`); SCR-011 hiển thị danh sách file sẽ xoá.
- **3a. Dry-run không hợp lệ**:
  - 3a1. Console trả 428 `ERR-JOB-428-01`.
- **4a. Không có lượt chuyển của site có manifest**:
  - 4a1. CLI trả `ERR-PTCH-404-01` (console: 404 `ERR-CON-404-01` khi `site_id` không tồn tại).
- **5a. `$OLD` đã bị gỡ (UC-UPG-007)**:
  - 5a1. CLI trả `ERR-ENV-410-01` (Critical) "Không thể hoàn tác {site}: PHP {old} đã được gỡ khỏi máy chủ."; Operator cài lại `$OLD` bằng `migrate install` rồi chạy lại.
- **6a. Khoá bị lượt khác giữ**:
  - 6a1. CLI `ERR-CLI-423-01`; job console chờ ≤ 30 phút rồi `ERR-JOB-409-02`. Khi tự rollback trong cửa sổ health check, CLI dùng khoá site đang giữ, không chờ khoá chung.
- **6b. Không ghi được audit intent**:
  - 6b1. CLI huỷ, `ERR-AUD-500-01`.
- **7a. Panel trả lỗi hoặc đọc lại khác giá trị cũ**:
  - 7a1. CLI ghi `ERR-ENV-502-01`, dừng; `status = ROLLBACK_FAILED`, `ERR-HC-500-02` (Critical), khoá chuyển site (`ERR-UPG-423-01`).
- **8a. Kiểm cú pháp sau khôi phục thất bại**:
  - 8a1. CLI không reload, giữ cấu hình đang chạy, ghi `ERR-ENV-500-03` (Critical); `status = ROLLBACK_FAILED`; Operator can thiệp ngay theo manifest.
- **9a. Trang chủ không trả mã baseline sau rollback**:
  - 9a1. `status = ROLLBACK_FAILED`, `ERR-HC-500-02`; khoá mọi lệnh chuyển site tới khi Operator xác nhận đã xử lý.
- **10a. Lượt `HC_RUNNING` đang chạy health check**:
  - 10a1. Health check dừng; lý do rollback `MANUAL` (`BR-JOB-004`).
- **10b. Job vượt 300 s**:
  - 10b1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-ENV-02`: R1–R6 ≤ 60 s P95.
- `NFR-ENV-04`: graceful reload gây 0 phản hồi 5xx.
- `NFR-REL-005`: khôi phục 100% file có dòng `copy`/`created` (khi `--purge-pool`).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCN-010` | Tự hoàn tác/hoàn tác bằng manifest | 7 |
| `BR-SCN-014`, `BR-ENV-008` | Giữ runtime cũ; gỡ nhánh cũ làm mất khả năng rollback | 5 |
| `BR-UPG-003` | Dừng site còn lại của kế hoạch | 10 |
| `BR-PTCH-008` | Lượt có dòng `switch` dùng R1–R7 | 4 |
| `BR-ENV-005`, `BR-ENV-006`, `BR-ENV-012` | Kiểm cú pháp, reload nhỏ nhất, đọc lại panel | 7, 8 |
| `BR-PLAN-007` | Đóng kế hoạch `rolled_back` | 11 |
| `BR-CON-005`, `BR-CLI-003` | Dry-run; xác nhận lệnh ghi mới | 2, 1a |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | 1–3, 11 |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | 4–10 |

### Giao diện và API liên quan
- Màn hình: `SCR-007`, `SCR-011`, dải cảnh báo `SCR-002`, `SCR-009`.
- API: `GET /api/v1/switches`, `GET /api/v1/switches/{run_id}`, `POST /api/v1/rollbacks` (`kind=site`).

### Quan hệ với use case khác
- `<<extend>>` UC-UPG-002 (rollback thủ công sau `PASSED` hoặc `HC_FAILED_KEPT`); luồng R1–R7 cũng được UC-UPG-002 dùng khi tự rollback và UC-PTCH-004 dùng khi lượt có dòng `switch`.
- Áp dụng cho ứng dụng Node.js (UC-UPG-005) và dịch vụ Compose (UC-UPG-006) qua hành động `systemd`, `pm2`, `compose`.

### Ghi chú và tài liệu tham chiếu
- Quy trình R1–R7 và hành động manifest: [environment-playbooks.md §5.2, §5.3](../srs/environment-playbooks.md); sơ đồ: [flows-upgrade.md §4](../srs/flows-upgrade.md).
- Câu hỏi mở kế thừa: chưa có endpoint xác nhận "đã xử lý" sau `ROLLBACK_FAILED`/`HC_FAILED_KEPT` (`Q-ST-07`, DOC-API-QP-001 §6.2 mục 10).
