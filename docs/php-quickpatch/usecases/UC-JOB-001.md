---
id: DOC-UC-QP-JOB-001
title: Đặc tả Use Case UC-JOB-001 — Theo dõi job và log trực tiếp
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-JOB-001, job, queue, sse, log, flock, reconciliation, retention, health-check-report]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-STATE-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ERD-003
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-JOB-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: bỏ nhãn "mã đề xuất" của `ERR-JOB-429-02` ở 6b1, liên kết tới error-matrix.md §3.3 (định nghĩa chuẩn từ v1.0.1), xoá ghi chú cũ; nhánh 7a dẫn công thức timeout động của `BR-JOB-008` 1.0.1 (`plan create` 600 + 1.800 × số site; `migrate switch` mặc định 1.250 s, tối đa 4.800 s) và tách xử lý hết timeout theo `phase` (7a1 thường, 7a2 vùng tới hạn hoãn tối đa 600 s, 7a3 `HC_RUNNING` rollback site với `rollback_reason = TIMEOUT`); thêm `BR-JOB-004` vào bảng BR |

## UC-JOB-001: Theo dõi job và log trực tiếp

- **Tác nhân chính (Primary Actor)**: Operator root, Operator không root (`PER-01`, `PER-02`, `PER-03`) và Auditor chỉ xem (`PER-04`).
- **Tác nhân hỗ trợ**: System: Job runner (`qp-console.py` — hàng đợi, khoá, tiến trình con, SSE); CLI `php-quickpatch.sh` (tiến trình con); lượt CLI chạy ngoài console (dùng chung khoá).
- **Phạm vi (Scope)**: hàng đợi job, `STATE_DIR/jobs/<job_id>/`, luồng SSE, console SCR-006.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng) đối với người theo dõi; phần hàng đợi/khoá là sub-function được include bởi mọi use case tạo job.
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: thấy dòng log CLI trên SCR-006 ≤ 2 s ở P95 sau khi CLI ghi (`NFR-PERF-003`); nối lại luồng sau mất kết nối không mất/không lặp dòng.
  - Chủ máy chủ: không có 2 job ghi cùng `RUNNING` trên 1 máy chủ, kể cả khi CLI chạy ngoài console (`NFR-REL-004`); khởi động lại console không tự chạy lại job ghi (`NFR-REL-003`).
  - `PER-04`: `job.json`, `result.json` của job ghi giữ ≥ 365 ngày; log đã che bí mật (`BR-SEC-006`).
  - Quản trị dung lượng: `jobs/` ≤ 200 MiB (`NFR-CAP-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Phiên console hợp lệ; có ≥ 1 job được tạo từ các use case khác (UC-CON-003, UC-SCAN-001, UC-FEED-001…).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: job kết thúc ở `SUCCEEDED`, `SUCCEEDED_WITH_ISSUES`, `FAILED`, `CANCELLED` hoặc `INTERRUPTED` theo ánh xạ mã thoát; `jobs/<job_id>/{job.json, output.log, result.json, phase}` quyền thư mục `0700`, file `0600`; SCR-006 hiển thị log và kết quả.
  - **Đảm bảo tối thiểu**: job không lấy được khoá trong 30 phút → `FAILED` có mã lỗi; log vượt 20 MiB bị cắt và đánh dấu `truncated=true` (log đầy đủ còn ở `php-quickpatch.log`).
- **Kích hoạt (Trigger)**: một use case khác tạo job (`POST /api/v1/jobs` hoặc endpoint mặt tiền); Operator/Auditor mở SCR-006.

### Luồng sự kiện chính (Main Success Scenario)
1. Hệ thống nhận yêu cầu tạo job đã qua danh sách trắng, gán `job_id` (`JOB-YYYYmmdd-HHMMSS-XXXX`) và loại `read`/`write`/`data` (`FR-JOB-RUN-001`, `BR-JOB-003`).
2. Hệ thống xếp job vào hàng đợi FIFO theo `created_at`; tối đa 1 job `write`, 2 job `read`, 1 job `data` cùng `RUNNING`; ≤ 20 job `QUEUED` (`BR-JOB-001`).
3. Đến lượt, hệ thống thử khoá không chặn: `write` → `flock -x -n` `STATE_DIR/.lock`; `read` → `flock -s -n`; `data` → `feeds/.lock`; khoá rảnh → khởi chạy tiến trình con CLI, job `RUNNING` (`FR-JOB-RUN-002`, `BR-JOB-002`).
4. Hệ thống ghi stdout (`--json`) vào `result.json`, stderr và dòng log vào `output.log` (≤ 20 MiB), che bí mật theo `BR-SEC-006`; CLI ghi `phase` cho job `write` (`FR-JOB-LOG-001`).
5. Operator mở SCR-006: bảng job lọc theo loại/trạng thái/thời gian; chọn 1 job (`FR-CON-JOB-001`).
6. Trình duyệt mở `EventSource` tới `GET /api/v1/jobs/{job_id}/events` (cookie); hệ thống trả `text/event-stream` với `retry: 2000`, sự kiện `log` (`id` = byte offset cuối dòng), `status`, `phase`, `end`; heartbeat mỗi 15 s (`FR-JOB-LOG-002`, `BR-JOB-007`).
7. Tiến trình CLI kết thúc; hệ thống ánh xạ mã thoát: 0 → `SUCCEEDED`, 1 → `SUCCEEDED_WITH_ISSUES`, 2 → `FAILED` (`ERR-JOB-500-01`) (`BR-JOB-008`), ghi `job.json`, gửi `end` và đóng luồng.
8. SCR-006 hiển thị `result.json`; với job chuyển site, hiển thị báo cáo health check: bảng vòng × URL, biểu đồ thời gian phản hồi, ≤ 50 dòng log vi phạm (`FR-UPG-HC-006`).
9. Mỗi lần `serve` khởi động và mỗi 24 giờ, hệ thống dọn `output.log` quá 30 ngày, giữ `job.json`/`result.json` của job ghi ≥ 365 ngày, giữ tổng `jobs/` ≤ 200 MiB (`FR-JOB-LOG-003`, `BR-JOB-006`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. Hàng đợi đủ 20 job `QUEUED`**:
  - 2a1. 429 `ERR-JOB-429-01`.
- **2b. Đã có job cùng hành động + đối tượng `QUEUED`/`RUNNING`**:
  - 2b1. 409 `ERR-JOB-409-01` kèm `job_id` đang có.
- **3a. Khoá bị lượt CLI ngoài console giữ**:
  - 3a1. Job giữ `QUEUED`, thử lại mỗi 5 s; quá 30 phút → `FAILED` với `ERR-JOB-409-02` kèm PID giữ khoá.
- **3b. Lệnh `scan` chạy song song `scan` khác**:
  - 3b1. Cả 2 lấy khoá chia sẻ, chạy song song; `scan` vẫn bị chặn khi `fix` đang giữ khoá độc quyền (`CR-SRS-06`).
- **4a. Log vượt 20 MiB**:
  - 4a1. Hệ thống dừng ghi `output.log`, đặt `truncated=true`.
- **5a. `job_id` không tồn tại**:
  - 5a1. 404 `ERR-JOB-404-01`.
- **6a. Log đã bị dọn theo chính sách 30 ngày**:
  - 6a1. 410 `ERR-JOB-410-01`; Operator xem `result.json` hoặc audit.
- **6b. Phiên đã mở 3 luồng SSE hoặc console đã có 10 luồng**:
  - 6b1. 429 `ERR-JOB-429-02` (`job.sse.limit`, định nghĩa ở [error-matrix.md §3.3](../srs/error-matrix.md)); các luồng đang mở không bị ngắt; trình duyệt không tự nối lại sau 429; Operator đóng luồng không dùng rồi mở lại.
- **6c. Mất kết nối SSE**:
  - 6c1. Trình duyệt tự nối lại sau 2.000 ms với `Last-Event-ID`; hệ thống gửi tiếp từ byte offset sau giá trị đó.
- **6d. Client CI không dùng SSE**:
  - 6d1. Client gọi `GET /api/v1/jobs/{job_id}` mỗi 2 s (đề xuất DOC-API-QP-001 §2.13.1) hoặc `GET /api/v1/jobs/{job_id}/log?offset=N`.
- **7a. Job vượt timeout theo hành động** (`BR-JOB-008`): `scan`/`assess` 1.800 s; `plan create` = 600 s + 1.800 s × số site được quét tương thích (mỗi site giới hạn theo `BR-CMPT-005`; 10 site → 18.600 s); `fix` 3.600 s; `migrate install` 3.600 s; `migrate switch` = 600 s + `hc.baseline_rounds` × `hc.baseline_interval_s` + cửa sổ theo dõi hiệu lực (`hc.window_s`, hoặc `hc.skip_window_s` khi `hc_mode=skip`) — mặc định 600 + 5 × 10 + 600 = 1.250 s, tối đa 600 + 10 × 60 + 3.600 = 4.800 s; `migrate rollback` 300 s; `feeds update` 960 s; hành động khác 600 s. Job runner tính giá trị này khi tạo job và lưu ở trường `timeout_s` của `job.json` (DOC-SRS-QP-ERD-003, [erd-console-ops.md](../srs/erd-console-ops.md)):
  - 7a1. `phase` ngoài vùng tới hạn và khác `HC_RUNNING` (gồm mọi job `read`/`data`): hệ thống gửi SIGTERM tới nhóm tiến trình, SIGKILL sau 10 s; job `FAILED` với `ERR-JOB-504-01`.
  - 7a2. `phase` thuộc vùng tới hạn của `BR-JOB-004` (`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`): hệ thống hoãn tín hiệu tới khi CLI rời vùng tới hạn, tối đa thêm 600 s (đề xuất trong `BR-JOB-008`), rồi xử lý như 7a1 hoặc 7a3 theo `phase` mới; job `FAILED` với `ERR-JOB-504-01`.
  - 7a3. `phase = HC_RUNNING` (job `migrate switch`): hệ thống gửi SIGTERM; CLI dừng health check, rollback site theo R1–R7 với `rollback_reason = TIMEOUT` (giá trị đề xuất trong `BR-JOB-008`) rồi mới thoát; console chờ tối đa 300 s trước SIGKILL; job `FAILED` với `ERR-JOB-504-01`; SCR-006 hiển thị kết quả rollback của lượt chuyển (UC-UPG-004).
- **7b. Console hoặc máy khởi động lại khi job đang `RUNNING`**:
  - 7b1. Khi `serve` khởi động, hệ thống đối soát ≤ 5 s: PID không sống → `INTERRUPTED` với `ERR-JOB-500-02`; PID còn sống → nối lại đọc log; không tự chạy lại job ghi (`FR-JOB-RUN-004`, `BR-JOB-005`).
  - 7b2. Lượt chuyển `HC_RUNNING` bị gián đoạn được xử lý theo DOC-SRS-QP-ENV-002 §6.4 (UC-UPG-002 extension 14e).
- **7c. Operator huỷ job**:
  - 7c1. Xử lý theo UC-JOB-002.
- **8a. Auditor chỉ xem**:
  - 8a1. Auditor xem log/kết quả; Phase 1 không phân quyền theo vai trò trên console (xem index §RBAC).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-003`: dòng log hiển thị ≤ 2 s ở P95.
- `NFR-PERF-006`: RSS console ≤ 200 MB khi stream 3 log.
- `NFR-REL-003`, `NFR-REL-004`: đối soát ≤ 5 s, 0 job ghi tự chạy lại; không có 2 job ghi cùng `RUNNING`.
- `NFR-CAP-001`: `jobs/` ≤ 200 MiB; `NFR-SEC-010`: quyền thư mục `0700`, file `0600`.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-JOB-001` | Giới hạn đồng thời và hàng đợi | 2 |
| `BR-JOB-002` | Khoá dùng chung với CLI | 3 |
| `BR-JOB-003` | Phân loại job | 1 |
| `BR-JOB-004` | Vùng tới hạn (`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`) dùng để hoãn tín hiệu khi hết timeout | 7a2 |
| `BR-JOB-005` | Đối soát khi khởi động lại | 7b |
| `BR-JOB-006` | Lưu log và lưu giữ | 4, 9 |
| `BR-JOB-007` | Luồng SSE: 3/phiên, 10/console, `retry: 2000`, heartbeat 15 s, ≤ 2 s | 6 |
| `BR-JOB-008` | Ánh xạ mã thoát; timeout theo hành động (động cho `plan create`, `migrate switch`); xử lý khi hết timeout theo `phase` | 7, 7a |
| `BR-SEC-006` | Che bí mật trong log | 4 |
| `BR-HC-011` | Bằng chứng health check | 8 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-JOB-RUN-001` | Hàng đợi và chạy job | 1, 2, 7 |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | 3 |
| `FR-JOB-LOG-001` | Lưu log và kết quả job | 4 |
| `FR-CON-JOB-001` | Màn hình Jobs & Log (SCR-006) | 5, 8 |
| `FR-JOB-LOG-002` | Stream log qua SSE | 6 |
| `FR-UPG-HC-006` | Báo cáo health check | 8 |
| `FR-JOB-LOG-003` | Lưu giữ log job | 9 |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | 7b |

### Giao diện và API liên quan
- Màn hình: `SCR-006` Jobs & Log.
- API: `GET /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, `GET /api/v1/jobs/{job_id}/log`, `GET /api/v1/jobs/{job_id}/events`, `GET /api/v1/switches/{run_id}`.

### Quan hệ với use case khác
- Được `<<include>>` bởi mọi use case tạo job từ console; `<<extend>>` bởi UC-JOB-002 (huỷ job).

### Ghi chú và tài liệu tham chiếu
- WHATWG HTML Server-sent events (kiểm chứng trong SRS spec §1.4): `EventSource` chỉ có `withCredentials`, không gửi header tuỳ chỉnh → SSE xác thực bằng cookie; trường `retry`; header `Last-Event-ID`.
- Máy trạng thái job: [states.md §2](../srs/states.md).
