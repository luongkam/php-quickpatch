---
id: DOC-UC-QP-FLT-002
title: Đặc tả Use Case UC-FLT-002 — Chạy lệnh từ xa theo đợt (Phase 2)
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FLT-002, phase-2, fleet, ssh, rollout, canary, batch, agentless]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FLOW-003
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FLT-002 theo `skills/usecase`, template 26, rules 06, 17 (Phase 2 — chỉ đặc tả) |
| 1.0.1 | 2026-10-22 | BA Agent | Bỏ nhãn "mã đề xuất" của `ERR-FLT-422-03` ở extension 2e1 và mục ghi chú; liên kết tới định nghĩa chuẩn ở error-matrix.md §3.13 (DOC-SRS-QP-ERR-001 v1.0.1) |

## UC-FLT-002: Chạy lệnh từ xa theo đợt (Phase 2)

- **Tác nhân chính (Primary Actor)**: Operator Phase 2 (`PER-01`, `PER-02` được gán vai trò Operator hoặc Admin).
- **Tác nhân hỗ trợ**: `SYS-04` kết nối SSH; CLI `php-quickpatch.sh` chạy trên từng server (`STATE_DIR` của server giữ backup, audit, feeds); máy trung tâm (`central.db`).
- **Phạm vi (Scope)**: `POST /api/v1/fleet-runs`, giao thức SSH S0–S7, SCR-022.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: chạy 1 lệnh trong danh sách trắng trên nhóm server theo đợt: canary 1 server → đợt ≤ 5 server, ≤ 10 kết nối song song; thu `scan --json` từ 100 server ≤ 20 phút (`NFR-PERF-008`).
  - Chủ server: lệnh ghi chỉ chạy khi dry-run thành công trên mọi server đích; đợt dừng khi canary lỗi hoặc > 20% server của đợt lỗi (`BR-FLT-005`); gói CLI được kiểm SHA-256 trước khi chạy (`BR-FLT-003`); 0 file tạm của tool còn lại ngoài `STATE_DIR` sau chạy (`NFR-SEC-012`).
  - `PER-04`: audit của từng server được gộp vào audit trung tâm, giữ `hash` gốc (`FR-FLT-AUD-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Tài khoản vai trò Operator/Admin đã đăng nhập (UC-FLT-001); server đã khai báo, khoá máy chủ đã ghim, kiểm kết nối `PASS`.
  - Hành động thuộc danh sách trắng (`BR-CON-008`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `fleet_run` `COMPLETED` với envelope `--json` và mã thoát từng server lưu trong `central.db` kèm `collected_at`; audit server đã gộp; thư mục tạm trên mọi server đã xoá.
  - **Đảm bảo tối thiểu**: khi điều kiện dừng xảy ra, đợt sau không chạy (`STOPPED`); server lỗi giữ mã lỗi; thư mục tạm chưa xoá được đánh dấu `cleanup_pending` để xoá ở lần kết nối sau.
- **Kích hoạt (Trigger)**: Operator chọn nhóm server, hành động (vd `fix`), kích thước đợt trên SCR-022 và bấm "Chạy".

### Luồng sự kiện chính (Main Success Scenario)
1. Operator gửi `POST /api/v1/fleet-runs` `{group, action, params, batch_size}` kèm CSRF; hệ thống kiểm vai trò, server tồn tại, danh sách trắng, tạo `fleet_run` (mỗi server `PENDING`), ghi audit trung tâm, trả 202 `{fleet_run_id}` (`FR-FLT-EXEC-002`).
2. Với lệnh ghi, hệ thống chạy giai đoạn dry-run trên mọi server đích, tối đa 10 kết nối song song; mỗi server theo các bước S1–S7 (`FR-FLT-EXEC-001`):
   - S1 kết nối (`BatchMode=yes`, `StrictHostKeyChecking=yes`, `ConnectTimeout=10`) và kiểm điều kiện;
   - S2 `mktemp -d /tmp/qp-remote.XXXXXXXXXX`;
   - S3 đẩy gói CLI bằng `tar` qua SSH;
   - S4 `sha256sum -c SHA256SUMS`, so hash với máy trung tâm (`BR-FLT-003`);
   - S5 chạy `<lệnh> --dry-run --json` (qua `sudo -n` khi `sudo_mode = sudo-n`) với timeout theo `BR-JOB-008`;
   - S6 thu audit mới bằng `audit list --from <ngày cuối đã thu> --json`;
   - S7 `rm -rf -- <TMP>` và kiểm không còn thư mục, chạy cả khi bước trước lỗi (`BR-FLT-001`).
3. Mọi server đích có dry-run thành công; hệ thống chạy đợt 1 gồm 1 server canary với lệnh ghi (S1–S7).
4. Canary đạt (mã thoát 0 hoặc 1, envelope hợp lệ); hệ thống chạy các đợt tiếp theo ≤ 5 server/đợt, ≤ 10 kết nối song song (`BR-FLT-005`).
5. Với mỗi server, hệ thống lưu envelope nguyên văn kèm `collected_at`, `server_id`, `fleet_run_id`; mã thoát 0/1/2 → `SUCCEEDED`/`SUCCEEDED_WITH_ISSUES`/`FAILED`.
6. Hết đợt, hệ thống đặt `fleet_run` `COMPLETED`, gộp audit server vào audit trung tâm giữ `hash` gốc (`FR-FLT-AUD-001`).
7. SCR-022 hiển thị tiến độ đợt và kết quả từng server; client gọi `GET /api/v1/fleet-runs/{fleet_run_id}` mỗi 5 s (đề xuất DOC-API-QP-001 §6.2 mục 11).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Vai trò Viewer**:
  - 1a1. 403 `ERR-FLT-403-02`.
- **1b. `server_id` trong yêu cầu không tồn tại**:
  - 1b1. 404 `ERR-FLT-404-01`.
- **1c. Hành động ngoài danh sách trắng hoặc tham số sai**:
  - 1c1. 422 `ERR-CON-422-01`.
- **1d. Lệnh đọc (vd `scan`, `assess`)**:
  - 1d1. Bỏ giai đoạn dry-run và canary; chạy song song ≤ 10 kết nối (đề xuất DOC-API-QP-006 §3.8, để đạt `NFR-PERF-008`; `BR-FLT-005` chưa nêu rõ ngoại lệ cho lệnh đọc — chờ PO xác nhận).
- **1e. Đã có đợt chạy `RUNNING` chứa cùng server với hành động ghi**:
  - 1e1. 409 `ERR-JOB-409-01` kèm `fleet_run_id` (đề xuất DOC-API-QP-006 §3.8).
- **2a. Không kết nối được trong 10 s, hoặc lệnh vượt timeout**:
  - 2a1. Server `TIMEOUT`, `ERR-FLT-504-01`; khi quá timeout, hệ thống đóng phiên, mở phiên mới gửi `pkill -TERM -f <TMP>/php-quickpatch.sh` (`BR-FLT-004`).
- **2b. Fingerprint khoá máy chủ khác giá trị đã ghim**:
  - 2b1. `ERR-FLT-403-01`, không gửi lệnh.
- **2c. Khoá SSH bị từ chối**:
  - 2c1. `ERR-FLT-401-01`.
- **2d. Thiếu điều kiện trên server**:
  - 2d1. `ERR-FLT-424-01`.
- **2e. SHA-256 gói CLI trên server lệch hash của máy trung tâm**:
  - 2e1. Server lỗi `ERR-FLT-422-03` ([error-matrix.md §3.13](../srs/error-matrix.md)), không chạy S5.
- **2f. JSON trả về sai schema hoặc khác major hỗ trợ (major 1)**:
  - 2f1. `ERR-FLT-422-02`.
- **2g. Khoá `STATE_DIR/.lock` của server đang bị lượt khác giữ**:
  - 2g1. Envelope có `ERR-CLI-423-01`, mã thoát 2; server `FAILED`.
- **2h. Có server đích chưa dry-run thành công**:
  - 2h1. `fleet_run` dừng trước bước ghi, giữ mã lỗi từng server (`BR-FLT-005`).
- **2i. Thu audit lỗi ở S6**:
  - 2i1. Giữ kết quả S5, đánh dấu `audit_pending`, thu lại ở lần chạy sau.
- **2j. Mất kết nối trước S7**:
  - 2j1. `cleanup_pending` trong `central.db`; lần kết nối kế tiếp xoá đúng đường dẫn đã ghi.
- **3a. Canary lỗi (mã thoát 2, timeout hoặc JSON sai)**:
  - 3a1. `fleet_run` `STOPPED`, `ERR-FLT-409-01` "Đã dừng đợt {batch}: {failed}/{total} server lỗi."
- **4a. Hơn 20% server của 1 đợt lỗi**:
  - 4a1. `fleet_run` `STOPPED`, `ERR-FLT-409-01`; đợt sau không chạy; Operator xem kết quả từng server rồi quyết định chạy tiếp.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-008`: thu `scan --json` từ 100 server (10 song song) ≤ 20 phút.
- `NFR-SEC-011`, `NFR-SEC-012`: 0 kết nối chấp nhận khoá chưa ghim; 0 file tạm còn lại ngoài `STATE_DIR`.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FLT-001` | Không agent; xoá thư mục tạm kể cả khi lỗi | 2 (S7) |
| `BR-FLT-002` | Xác thực SSH | 2 (S1) |
| `BR-FLT-003` | Toàn vẹn gói CLI | 2 (S4) |
| `BR-FLT-004` | Timeout từ xa theo `BR-JOB-008` | 2 (S5) |
| `BR-FLT-005` | Canary → đợt ≤ 5, ≤ 10 song song, điều kiện dừng, dry-run trên mọi server | 2–4 |
| `BR-FLT-008` | Vai trò Operator/Admin | 1 |
| `BR-CON-008` | Danh sách trắng lệnh | 1 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FLT-EXEC-002` | Chạy theo đợt | 1, 3, 4, 6 |
| `FR-FLT-EXEC-001` | Thực thi CLI từ xa | 2, 5 |

### Giao diện và API liên quan
- Màn hình: `SCR-022` Phase 2 — Đợt chạy từ xa & phân phối snapshot.
- API: `POST /api/v1/fleet-runs`, `GET /api/v1/fleet-runs/{fleet_run_id}`.

### Quan hệ với use case khác
- Tiền đề: UC-FLT-001; kết quả hiển thị ở UC-FLT-003; biến thể phân phối snapshot là UC-FLT-004.
- Trên từng server, lệnh chạy theo đúng use case Phase 1 tương ứng (vd UC-SCAN-001, UC-PTCH-001).

### Ghi chú và tài liệu tham chiếu
- Định nghĩa mã lỗi (gồm `ERR-FLT-422-03`): [error-matrix.md §3.13](../srs/error-matrix.md) (DOC-SRS-QP-ERR-001, định nghĩa chuẩn từ v1.0.1).
- Giao thức S0–S7: [api-spec-phase2.md §4.3](../api/api-spec-phase2.md); sơ đồ: [flows-console-fleet.md §3](../srs/flows-console-fleet.md).
