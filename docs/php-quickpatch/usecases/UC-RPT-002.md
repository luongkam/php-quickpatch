---
id: DOC-UC-QP-RPT-002
title: Đặc tả Use Case UC-RPT-002 — Xuất báo cáo bằng chứng thay đổi
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-RPT-002, report, evidence, audit, manifest, switch, health-check, auditor]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-RPT-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-CLI-CMD-004` trong bảng FR liên quan với SRS: "Cung cấp lệnh `report` và `audit`" |

## UC-RPT-002: Xuất báo cáo bằng chứng thay đổi

- **Tác nhân chính (Primary Actor)**: Auditor (`PER-04`) — quyền Export; Operator xuất thay khi cần.
- **Tác nhân hỗ trợ**: System: Job runner (job `report evidence`, loại `read`).
- **Phạm vi (Scope)**: `php-quickpatch.sh report evidence --from DATE --to DATE --format json|csv|md|html --out FILE`; console SCR-010.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-04`: trong khoảng ≤ 366 ngày, thấy trạng thái trước/sau (phiên bản, gói), người chạy, người duyệt, miễn trừ kèm lý do, rollback, và kết quả kiểm chuỗi hash audit, đủ để làm bằng chứng kiểm toán.
  - Chủ máy chủ: báo cáo chỉ đọc audit, manifest, `switch.json`, `hc.json`; không thay đổi hệ thống.
- **Tiền điều kiện (Pre-conditions)**:
  - Có audit (`STATE_DIR/audit/`) và backup (`STATE_DIR/backups/`) trong khoảng thời gian; Python ≥ 3.6.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: file báo cáo bằng chứng + SHA-256 (in ra stdout, ghi audit); báo cáo nêu `verified=true` của chuỗi hash.
  - **Đảm bảo tối thiểu**: khi chuỗi hash lệch, báo cáo vẫn được tạo và ghi rõ `first_broken_seq` (không che giấu lệch).
- **Kích hoạt (Trigger)**: Auditor chọn "Báo cáo bằng chứng" và khoảng thời gian trên SCR-010, hoặc chạy CLI tương ứng.

### Luồng sự kiện chính (Main Success Scenario)
1. Auditor chọn khoảng `from`–`to` và định dạng trên SCR-010; console gửi `POST /api/v1/reports` (`kind=evidence`) tạo job `report evidence --format <f> --out STATE_DIR/reports/<report_id>.<ext> --from <YYYY-MM-DD> --to <YYYY-MM-DD>` (`FR-CLI-CMD-004`).
2. CLI kiểm tham số: `from` ≤ `to`, khoảng ≤ 366 ngày, định dạng hợp lệ.
3. Hệ thống trích audit, manifest, `switch.json`, `hc.json` trong khoảng: trạng thái trước/sau (phiên bản, gói), người chạy, người duyệt, miễn trừ, rollback (`FR-RPT-AUD-001`).
4. Hệ thống chạy kiểm chuỗi hash audit cho khoảng (`FR-JOB-AUD-002`, `BR-AUD-003`) và đưa kết quả vào báo cáo.
5. Hệ thống ghi nguồn gốc (`bundle_id`, `catalog_version`, phiên bản tool, `hostname`, thời điểm tạo UTC), xuất theo định dạng, che bí mật, ghi file `0600`, in SHA-256 và ghi audit (`BR-RPT-001`, `BR-RPT-002`, `BR-RPT-003`).
6. Console hiển thị báo cáo và nút tải; Auditor tải file và đối chiếu SHA-256.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. `from` > `to`, khoảng > 366 ngày, hoặc định dạng không hỗ trợ**:
  - 2a1. `ERR-RPT-422-01`.
- **2b. File `--out` đã tồn tại**:
  - 2b1. `ERR-RPT-409-01`.
- **2c. Thiếu Python ≥ 3.6**:
  - 2c1. `ERR-CLI-424-01`.
- **3a. Không có sự kiện trong khoảng**:
  - 3a1. Báo cáo được tạo với 0 sự kiện và kết quả kiểm chuỗi.
- **3b. Manifest của 1 lượt đã bị xoá thủ công**:
  - 3b1. Báo cáo ghi dòng audit của lượt kèm ghi chú "không còn manifest".
- **4a. Chuỗi hash lệch**:
  - 4a1. Báo cáo ghi `verified=false`, `first_broken_seq`, mã `ERR-AUD-409-01` (Critical); Auditor điều tra theo UC-JOB-003.
- **6a. Job vượt 600 s**:
  - 6a1. Job `FAILED` với `ERR-JOB-504-01`; Auditor thu hẹp khoảng thời gian.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-007`: chuỗi hash phát hiện 100% thay đổi 1 byte.
- `BR-RPT-001`: HTML ≤ 5 MiB, 0 tài nguyên ngoài.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-RPT-001`, `BR-RPT-002`, `BR-RPT-003` | Định dạng, nguồn gốc, không ghi đè + che bí mật | 5 |
| `BR-AUD-003` | Chuỗi hash | 4 |
| `BR-AUD-005`, `BR-SEC-006` | Che dữ liệu | 5 |
| `BR-HC-011` | Bằng chứng health check (`baseline.json`, `hc.json`) | 3 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | 1, 2 |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | 3–5 |

### Giao diện và API liên quan
- Màn hình: `SCR-010` Audit & báo cáo.
- API: `POST /api/v1/reports` (`kind=evidence`), `GET /api/v1/reports/{report_id}`.

### Quan hệ với use case khác
- `<<include>>` kiểm chuỗi hash của UC-JOB-003; dùng bằng chứng do UC-PTCH-*, UC-UPG-*, UC-PLAN-002/003 tạo ra.

### Ghi chú và tài liệu tham chiếu
- PRD luồng giá trị §4.15 bước 7: xuất báo cáo bằng chứng cho kiểm toán sau khi nâng cấp.
- `FR-RPT-AUD-001`: [functional-requirements.md §12](../srs/functional-requirements.md).
