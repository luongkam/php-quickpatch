---
id: DOC-UC-QP-FLT-001
title: Đặc tả Use Case UC-FLT-001 — Quản lý danh mục server và tài khoản (Phase 2)
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FLT-001, phase-2, fleet, server-inventory, ssh, host-key-pinning, rbac, accounts]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ERD-005
  - DOC-API-QP-006
related_diagrams:
  - DIAG-UC-QP-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FLT-001 theo `skills/usecase`, template 26, rules 06, 17 (Phase 2 — chỉ đặc tả, chưa triển khai) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-FLT-RBAC-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Quản lý tài khoản và vai trò Phase 2" |

## UC-FLT-001: Quản lý danh mục server và tài khoản (Phase 2)

- **Tác nhân chính (Primary Actor)**: Admin Phase 2 (`PER-01`, `PER-02` được gán vai trò Admin).
- **Tác nhân hỗ trợ**: `SYS-04` kết nối SSH (OpenSSH client trên máy trung tâm, `ssh-keyscan`, `ssh-keygen`); server được quản lý (sshd, Bash, `flock`, `curl`); kênh tin cậy để lấy fingerprint khoá máy chủ (vd console của nhà cung cấp VPS).
- **Phạm vi (Scope)**: console máy trung tâm (chỉ bind `127.0.0.1`, truy cập qua SSH tunnel, `C-SRS-06`), `central.db` (SQLite), `known_hosts.d/<server_id>`; SCR-020.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Admin: khai báo, sửa, tắt, xoá server; ghim khoá máy chủ; tạo tài khoản Viewer/Operator/Admin.
  - Kỹ sư bảo mật: 0 kết nối SSH chấp nhận khoá máy chủ chưa ghim; 0 mật khẩu SSH lưu trữ (`NFR-SEC-011`); mật khẩu tài khoản băm bằng `hashlib.scrypt` (lệch rules/04 Argon2id/Bcrypt — `Q-SRS-06`).
  - Chủ server được quản lý: không cài agent, dịch vụ, cron, unit (`BR-FLT-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Máy trung tâm đã cài; tài khoản Admin đầu tiên tạo bằng CLI trên máy trung tâm, không có mật khẩu mặc định (đề xuất DOC-API-QP-006 §2.1).
  - Admin đăng nhập bằng `POST /api/v1/sessions` `{username, password}` qua SSH tunnel.
  - Khoá SSH (file quyền `0600` hoặc ssh-agent) của máy trung tâm đã được thêm vào `authorized_keys` của server.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: bản ghi server trong `central.db` (`server_id`, `host`, `port`, `ssh_user`, `auth`, `host_key_fingerprint`, `groups[]`, `sudo_mode`, `enabled`); khoá máy chủ đã ghim trong `known_hosts.d/<server_id>` (`0600`); kết quả kiểm kết nối và điều kiện; tài khoản có vai trò; audit trung tâm.
  - **Đảm bảo tối thiểu**: fingerprint không khớp → không ghi `known_hosts`; dữ liệu sai định dạng không được lưu.
- **Kích hoạt (Trigger)**: Admin mở SCR-020 và bấm "Thêm server", "Sửa", "Tắt", "Xoá", "Kiểm kết nối" hoặc "Tạo tài khoản".

### Luồng sự kiện chính (Main Success Scenario)
1. Admin mở SCR-020; console kiểm vai trò Admin (`FR-FLT-RBAC-001`, `BR-FLT-008`).
2. Admin bấm "Thêm server", nhập `server_id`, `host`, `port` (mặc định 22), `ssh_user`, `auth` (`key:<đường dẫn>` hoặc `agent`), `host_key_fingerprint` dạng `SHA256:…` lấy qua kênh tin cậy, `groups[]`, `sudo_mode` (`none`/`sudo-n`).
3. Hệ thống kiểm định dạng, không chấp nhận trường mật khẩu/passphrase, kiểm `key_path` tồn tại và quyền `0600`, lưu bản ghi vào `central.db`, ghi audit trung tâm (`FR-FLT-INV-001`, `BR-FLT-002`).
4. Admin bấm "Kiểm kết nối"; hệ thống chạy S0: `ssh-keyscan -T 10` → `ssh-keygen -l -E sha256` → so với `host_key_fingerprint`; khớp → ghi `known_hosts.d/<server_id>` (`FR-FLT-INV-002`).
5. Hệ thống chạy S1: `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=<known_hosts riêng> -o ConnectTimeout=10`, kiểm điều kiện từ xa: Bash ≥ 4.3, `flock`, `curl`, `sha256sum`, `tar`, `mktemp`, `python3` ≥ 3.6 (tuỳ chọn), `sudo -n true` (khi `sudo-n`).
6. Hệ thống trả 200 `{result: PASS, reachability, host_key.matches=true, prerequisites[]}`; SCR-020 hiển thị server sẵn sàng.
7. Admin bấm "Tạo tài khoản", nhập `username`, mật khẩu 12–128 ký tự, vai trò Viewer/Operator/Admin; hệ thống băm `hashlib.scrypt` và lưu (`FR-FLT-RBAC-001`).
8. Hệ thống ghi audit trung tâm cho mỗi thao tác.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Vai trò không phải Admin**:
  - 1a1. 403 `ERR-FLT-403-02` "Vai trò {role} không được phép {action}."
- **1b. Đăng nhập sai 5 lần trong 60 s theo `username`**:
  - 1b1. 429 `ERR-AUTH-429-01`; sai mật khẩu → 401 `ERR-AUTH-401-01`.
- **3a. Sai định dạng, trùng `server_id`, có trường mật khẩu, `key_path` không tồn tại hoặc quyền rộng hơn `0600`**:
  - 3a1. 422 `ERR-FLT-422-01` "Thông tin server không hợp lệ: {field}."
- **3b. Sửa server (`PATCH`)**:
  - 3b1. Cập nhật một phần trừ `server_id`; `enabled=false` = bỏ khỏi đợt chạy mới.
  - 3b2. Đổi `host_key_fingerprint` cần gõ lại `server_id` và xoá `known_hosts.d/<server_id>` để S0 ghim lại (đề xuất DOC-API-QP-006 §3.3).
- **3c. Xoá server đang thuộc đợt chạy `RUNNING`**:
  - 3c1. Hệ thống đặt `enabled=false` ngay, xoá khi đợt kết thúc; audit trung tâm giữ nguyên.
- **3d. `server_id` không tồn tại**:
  - 3d1. 404 `ERR-FLT-404-01`.
- **4a. Fingerprint khoá máy chủ khác giá trị đã ghim**:
  - 4a1. `ERR-FLT-403-01` (Critical) trong `data.errors[]`; không ghi `known_hosts`; Admin xác minh máy chủ trước khi cập nhật fingerprint.
- **5a. Khoá SSH bị từ chối**:
  - 5a1. `ERR-FLT-401-01`; Admin kiểm khoá và `authorized_keys`.
- **5b. Không kết nối được trong 10 s**:
  - 5b1. `ERR-FLT-504-01`; Admin kiểm mạng/tường lửa.
- **5c. Thiếu Bash ≥ 4.3, `flock`, `curl`, hoặc `sudo -n` đòi mật khẩu**:
  - 5c1. `ERR-FLT-424-01` "{server} chưa đủ điều kiện: {missing}."
- **7a. `username` trùng hoặc sai regex, mật khẩu ngoài 12–128 ký tự**:
  - 7a1. 422 `ERR-CON-422-01` (`details.constraint=duplicate` khi trùng, đề xuất `Q-API-04`).
- **7b. Đổi vai trò, khoá, xoá tài khoản**:
  - 7b1. Chưa có endpoint (`Q-P2-01`); Admin thao tác bằng CLI trên máy trung tâm tới khi có CR.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-SEC-011`: 0 kết nối SSH chấp nhận khoá máy chủ chưa ghim; 0 mật khẩu SSH lưu trữ.
- `C-SRS-06`: máy trung tâm chỉ bind `127.0.0.1`.
- Kiểm kết nối (S0–S1) ≤ 30 s mỗi server (DOC-API-QP-006 §3.5).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FLT-001` | Không agent | Tiền điều kiện |
| `BR-FLT-002` | Xác thực SSH chỉ bằng khoá, `known_hosts` riêng, `StrictHostKeyChecking=yes`, `BatchMode=yes`, `ConnectTimeout=10` | 3–5 |
| `BR-FLT-008` | Vai trò Viewer/Operator/Admin | 1, 7 |
| `BR-AUTH-002`, `BR-AUTH-003`, `BR-AUTH-004` | So sánh hằng thời gian, thử sai, phiên | 1b |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FLT-INV-001` | Quản lý danh mục server | 2, 3 |
| `FR-FLT-INV-002` | Kiểm tra kết nối và ghim khoá máy chủ | 4–6 |
| `FR-FLT-RBAC-001` | Quản lý tài khoản và vai trò Phase 2 | 1, 7 |

### Giao diện và API liên quan
- Màn hình: `SCR-020` Phase 2 — Danh sách server.
- API: `GET`/`POST /api/v1/servers`, `PATCH`/`DELETE /api/v1/servers/{server_id}`, `POST /api/v1/servers/{server_id}/connection-checks`, `GET`/`POST /api/v1/users`.

### Quan hệ với use case khác
- Tiền đề của UC-FLT-002, UC-FLT-003, UC-FLT-004.

### Ghi chú và tài liệu tham chiếu
- Phase 2 chỉ đặc tả, chưa triển khai (DOC-BRS-QP-001 §5.1 mục 8).
- Giao thức SSH S0–S7: [api-spec-phase2.md §4](../api/api-spec-phase2.md); `FR-FLT-*`: [functional-requirements.md §13](../srs/functional-requirements.md).
