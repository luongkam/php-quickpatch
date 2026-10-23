---
id: DOC-UC-QP-FLT-003
title: Đặc tả Use Case UC-FLT-003 — Xem dashboard tổng hợp nhiều server (Phase 2)
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FLT-003, phase-2, fleet, dashboard, drill-down, central-audit, viewer]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ERD-005
  - DOC-API-QP-006
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-FLT-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FLT-003 theo `skills/usecase`, template 26, rules 06, 17 (Phase 2 — chỉ đặc tả) |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-FLT-DASH-001` ("Hiển thị dashboard tổng hợp nhiều server") và `FR-FLT-AUD-001` ("Hợp nhất audit trung tâm") với DOC-SRS-QP-FR-001 1.0.1 (`CR-FR-06`) |

## UC-FLT-003: Xem dashboard tổng hợp nhiều server (Phase 2)

- **Tác nhân chính (Primary Actor)**: Viewer Phase 2 (`PER-04` Auditor chỉ xem) và Operator.
- **Tác nhân hỗ trợ**: máy trung tâm (`central.db` chứa envelope `--json` đã thu); UC-FLT-002 cung cấp dữ liệu.
- **Phạm vi (Scope)**: SCR-021 dashboard tổng hợp, màn hình đi sâu theo server (các màn hình Phase 1 ở chế độ chỉ đọc), audit trung tâm.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-04`: ma trận server × runtime với số KEV, Critical, EOL, chưa vá, `R`, thời điểm thu thập; audit hợp nhất giữ `hash` gốc từng server để kiểm chuỗi.
  - Operator: biết server nào cần xử lý trước và dữ liệu server nào đã cũ.
  - Người đọc số liệu tổng: dữ liệu server cũ > 24 giờ gắn nhãn "cũ"; > 7 ngày bị loại khỏi số liệu tổng và liệt kê riêng (`BR-FLT-006`).
- **Tiền điều kiện (Pre-conditions)**:
  - Tài khoản vai trò Viewer/Operator/Admin đã đăng nhập (UC-FLT-001).
  - Đã có ≥ 1 lượt thu `scan`/`assess` từ server (UC-FLT-002).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: SCR-021 hiển thị tổng số và ma trận; màn hình đi sâu hiển thị dữ liệu Phase 1 của server ở chế độ chỉ đọc; báo cáo audit hợp nhất có kết quả kiểm chuỗi từng nguồn.
  - **Đảm bảo tối thiểu**: chỉ đọc; Viewer không thực hiện được hành động ghi.
- **Kích hoạt (Trigger)**: người dùng mở SCR-021 hoặc chọn 1 server để đi sâu.

### Luồng sự kiện chính (Main Success Scenario)
1. Viewer mở SCR-021; console gọi `GET /api/v1/fleet-summary?group=<g>` (`FR-FLT-DASH-001`).
2. Hệ thống dựng ma trận server × runtime từ kết quả `scan`/`assess` mới nhất của từng server: KEV, Critical, EOL, chưa vá, `R`, mức, `collected_at`, `freshness_label` (`fresh` ≤ 24 giờ, `old` > 24 giờ, `excluded` > 7 ngày).
3. Hệ thống tính `totals` (servers, kev, critical, eol, unpatched) trên server `fresh`/`old`; server `excluded` liệt kê ở `excluded_servers[]` (`BR-FLT-006`).
4. Viewer lọc theo nhóm và chọn 1 server; console gọi `GET /api/v1/servers/{server_id}/results?latest=true` (`FR-FLT-DASH-002`).
5. Hệ thống hiển thị các màn hình Phase 1 (tổng quan, đánh giá runtime, findings, kế hoạch) ở chế độ chỉ đọc từ envelope đã thu; hành động đi qua UC-FLT-002 (chỉ Operator/Admin).
6. Viewer mở mục audit trung tâm; console gọi `GET /api/v1/fleet-audit-events`; hệ thống gộp audit của máy trung tâm và audit thu từ server theo thời gian, giữ `hash` gốc, kiểm chuỗi từng nguồn (`FR-FLT-AUD-001`).
7. Viewer xuất báo cáo (quyền Export của Viewer theo `BR-FLT-008`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Phiên hết hạn hoặc chưa đăng nhập**:
  - 1a1. 401 `ERR-AUTH-401-02`/`ERR-AUTH-401-01`.
- **2a. Server chưa từng được thu dữ liệu**:
  - 2a1. Server hiển thị trạng thái "chưa có dữ liệu", không tính vào `totals`.
- **3a. Server có `collected_at` > 7 ngày**:
  - 3a1. Server ở `excluded_servers[]`, không tính vào số liệu tổng.
- **4a. `server_id` không tồn tại**:
  - 4a1. 404 `ERR-FLT-404-01`.
- **5a. Viewer bấm hành động ghi**:
  - 5a1. Nút không hiển thị; gọi API trực tiếp → 403 `ERR-FLT-403-02`.
- **5b. Envelope đã thu thuộc major schema không hỗ trợ**:
  - 5b1. Màn hình hiển thị `ERR-FLT-422-02` cho server đó; đề xuất chạy lại thu thập bằng bản CLI hiện tại.
- **6a. Chuỗi hash audit của 1 nguồn lệch**:
  - 6a1. Báo cáo audit hợp nhất ghi `ERR-AUD-409-01` (Critical) cho nguồn đó, giữ nguyên dữ liệu làm bằng chứng.
- **6b. Audit của server đang `audit_pending`**:
  - 6b1. Báo cáo ghi rõ server chưa thu đủ audit tới thời điểm hiện tại.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-001` (áp dụng tương tự cho máy trung tâm): API đọc P95 ≤ 500 ms.
- `C-SRS-06`: máy trung tâm chỉ bind `127.0.0.1`.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FLT-006` | Độ tươi dữ liệu server | 2, 3 |
| `BR-FLT-008` | Vai trò Viewer/Operator/Admin | 5, 7 |
| `BR-AUD-003` | Chuỗi hash từng nguồn | 6 |
| `BR-ASMT-004`, `BR-FEED-042` | Thứ tự và phân mức rủi ro | 2 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FLT-DASH-001` | Hiển thị dashboard tổng hợp nhiều server | 1–3 |
| `FR-FLT-DASH-002` | Đi sâu theo server | 4, 5 |
| `FR-FLT-AUD-001` | Hợp nhất audit trung tâm | 6 |

### Giao diện và API liên quan
- Màn hình: `SCR-021` Phase 2 — Dashboard tổng hợp nhiều server.
- API: `GET /api/v1/fleet-summary`, `GET /api/v1/servers/{server_id}/results`, `GET /api/v1/fleet-audit-events`.

### Quan hệ với use case khác
- Dữ liệu từ UC-FLT-002; quyền từ UC-FLT-001; tương đương Phase 2 của UC-CON-002 và UC-JOB-003.

### Ghi chú và tài liệu tham chiếu
- [api-spec-phase2.md §3.6, §3.7, §3.13](../api/api-spec-phase2.md); `FR-FLT-DASH-*`: [functional-requirements.md §13](../srs/functional-requirements.md).
