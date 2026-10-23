---
id: DOC-UC-QP-JOB-002
title: Đặc tả Use Case UC-JOB-002 — Huỷ job
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-JOB-002, job, cancel, sigterm, critical-section, health-check]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-STATE-001
  - DOC-API-QP-004
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-JOB-002 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-JOB-002: Huỷ job

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`) — người có phiên console.
- **Tác nhân hỗ trợ**: System: Job runner (gửi tín hiệu tới nhóm tiến trình); CLI (ghi `phase`, rollback site khi huỷ trong cửa sổ health check).
- **Phạm vi (Scope)**: `POST /api/v1/jobs/{job_id}/cancellations`, nút "Huỷ" trên SCR-006; Ctrl+C trên CLI.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: dừng job đọc hoặc job đang chờ trong ≤ 10 s (SIGTERM, SIGKILL sau 10 s); biết lý do khi không huỷ được.
  - Chủ site: job ghi không bị cắt ngang giữa lúc đang áp dụng thay đổi (`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`) để tránh trạng thái nửa vời (`BR-JOB-004`).
  - `PER-04`: mỗi lần huỷ có bản ghi audit.
- **Tiền điều kiện (Pre-conditions)**:
  - Job ở `QUEUED` hoặc `RUNNING`; phiên console hợp lệ, request qua kiểm CSRF.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: job ở `CANCELLED`; nhóm tiến trình con đã dừng; audit ghi người huỷ, `job_id`, `phase` tại thời điểm huỷ.
  - **Đảm bảo tối thiểu**: job ghi trong vùng tới hạn không bị dừng; Operator nhận lý do từ chối.
- **Kích hoạt (Trigger)**: Operator bấm "Huỷ" trên 1 job ở SCR-006.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator bấm "Huỷ" trên job ở SCR-006 (`FR-CON-JOB-002`).
2. Trình duyệt gửi `POST /api/v1/jobs/{job_id}/cancellations` kèm `X-QP-CSRF`, `Origin`.
3. Hệ thống đọc trạng thái job và `jobs/<job_id>/phase` (`FR-JOB-RUN-003`).
4. Job `RUNNING` loại `read` (hoặc `data`): hệ thống gửi SIGTERM tới nhóm tiến trình, gửi SIGKILL sau 10 s nếu còn chạy.
5. Hệ thống đặt job `CANCELLED`, ghi audit, gửi sự kiện `status`/`end` qua SSE.
6. SCR-006 hiển thị job `CANCELLED`; huỷ job không cần dry-run (ngoại lệ `BR-CON-005`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Huỷ từ CLI (Ctrl+C)**:
  - 1a1. Lệnh đọc dừng ngay; lệnh ghi áp cùng quy tắc vùng tới hạn của `BR-JOB-004` (`FR-JOB-RUN-003`).
- **2a. Thiếu CSRF/Origin sai**:
  - 2a1. 403 `ERR-AUTH-403-01`/`ERR-AUTH-403-02`.
- **3a. `job_id` không tồn tại**:
  - 3a1. 404 `ERR-JOB-404-01`.
- **3b. Job ở `QUEUED`**:
  - 3b1. Hệ thống chuyển `CANCELLED` ngay, trả 200 `effect=CANCELLED`; không có tiến trình phải dừng.
- **3c. Job đã kết thúc (`SUCCEEDED`, `SUCCEEDED_WITH_ISSUES`, `FAILED`, `CANCELLED`, `INTERRUPTED`)**:
  - 3c1. Hệ thống trả 200 `effect=ALREADY_ENDED`, trạng thái không đổi (DOC-API-QP-004 §3.5).
- **4a. Job `write` có `phase` ∈ {`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`}** (bước C6–C10, R1–R6, đang cài gói):
  - 4a1. 423 `ERR-JOB-423-01` "Job đang áp dụng thay đổi ({phase}); không thể huỷ lúc này."; Operator chờ bước hiện tại xong rồi huỷ hoặc rollback (UC-PTCH-004, UC-UPG-004).
- **4b. Job `write` có `phase = HC_RUNNING`** (cửa sổ health check sau chuyển site):
  - 4b1. Hệ thống dừng health check và rollback site với lý do `MANUAL` theo R1–R7 (UC-UPG-004), trả 202 `effect=HC_ROLLBACK_STARTED`; lượt chuyển `ROLLED_BACK`.
- **4c. Job `write` ngoài vùng tới hạn (`phase = null`, trước khi ghi manifest)**:
  - 4c1. Hệ thống dừng như bước 4 (202 `effect=SIGTERM_SENT`); chưa có thay đổi nào cần hoàn tác.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-002`: phản hồi yêu cầu huỷ P95 ≤ 1.500 ms.
- Dừng job đọc ≤ 10 s sau SIGTERM (SIGKILL ở giây thứ 10).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-JOB-004` | Quy tắc huỷ theo loại job và `phase` | 3–5, 4a, 4b |
| `BR-CON-004` | Chống CSRF | 2 |
| `BR-CON-005` | Huỷ job không cần dry-run | 6 |
| `BR-AUD-001` | Ghi audit huỷ job | 5 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-JOB-002` | Huỷ job từ console | 1, 6 |
| `FR-JOB-RUN-003` | Huỷ job | 3–5 |

### Giao diện và API liên quan
- Màn hình: `SCR-006` Jobs & Log (nút "Huỷ").
- API: `POST /api/v1/jobs/{job_id}/cancellations`.

### Quan hệ với use case khác
- `<<extend>>` UC-JOB-001; khi huỷ trong cửa sổ health check, `<<include>>` luồng rollback của UC-UPG-004.

### Ghi chú và tài liệu tham chiếu
- Máy trạng thái job (`T-JOB-*`): [states.md §2](../srs/states.md); sơ đồ huỷ: [flows.md §5](../srs/flows.md).
