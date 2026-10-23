---
id: DOC-UC-QP-CON-001
title: Đặc tả Use Case UC-CON-001 — Mở console và đăng nhập bằng token
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-CON-001, serve, token, session, ssh-tunnel, dns-rebinding, csrf, csp, loopback]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-STATE-001
  - DOC-API-QP-001
  - DOC-API-QP-002
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-AUTH-001
  - DIAG-SEQ-QP-AUTH-002
  - DIAG-STATE-QP-CON-001
  - DIAG-STATE-QP-AUTH-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-CON-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: `NFR-CMP-003` đổi thành Python 3.6–3.14, phiên bản ổn định hiện hành và liền trước của 4 trình duyệt (theo nfr.md 1.0.1); đồng bộ tên `FR-CON-SAFE-002`, `FR-CON-API-001` theo functional-requirements.md (`CR-FR-06`) |

## UC-CON-001: Mở console và đăng nhập bằng token

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`, `PER-03`) có phiên SSH trên máy chủ.
- **Tác nhân hỗ trợ**: OpenSSH client trên máy trạm (local port forwarding); trình duyệt; tiến trình cục bộ khác trên cùng máy chủ (có thể kết nối `127.0.0.1:<port>`, `A-SRS-02`) là đối tượng phải chặn.
- **Phạm vi (Scope)**: `php-quickpatch.sh serve [--port N] [--allow-local-port N] [--replace] [--stop] [--token-file PATH]`, `qp-console.py`, SCR-001, API `/api/v1/sessions`.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: mở console ≤ 3 s sau khi chạy `serve` (`NFR-PERF-006`), đăng nhập bằng URL in ra mà không cần tạo tài khoản.
  - Kỹ sư bảo mật: console chỉ lắng nghe `127.0.0.1` — 0 socket trên địa chỉ khác (`NFR-SEC-001`); token 256 bit CSPRNG, so sánh hằng thời gian, 0 lần xuất hiện trong log/audit/JSON/`STATE_DIR` (`NFR-SEC-002`); 100% request có Host ngoài danh sách bị trả 421 (`NFR-SEC-004`); 100% request ghi bằng cookie thiếu CSRF/Origin sai bị từ chối (`NFR-SEC-005`).
  - Người dùng khác trên shared hosting: không đăng nhập được khi không có token; 5 lần sai trong 60 s → khoá đăng nhập 60 s (`BR-AUTH-003`).
  - `PER-04`: mỗi lần phát hành token (không kèm token), đăng nhập thành công/thất bại có bản ghi audit (`BR-AUD-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Operator có phiên SSH có TTY trên máy chủ (`A-SRS-03`), hoặc dùng `--token-file`.
  - Python ≥ 3.6 trên máy chủ.
  - Máy trạm mở được `ssh -N -L <port>:127.0.0.1:<port> <user>@<host>` (`A-SRS-01`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `serve` ở `LISTENING` trên `127.0.0.1:<port>` (mặc định 17321); PID file `STATE_DIR/console/serve.pid` quyền `0600`; trình duyệt có cookie `qp_session` (`HttpOnly`, `SameSite=Strict`, `Path=/`) và CSRF token trong biến bộ nhớ; job `RUNNING` của lần `serve` trước đã được đối soát ≤ 5 s (`NFR-REL-003`); SCR-002 hiển thị.
  - **Đảm bảo tối thiểu**: khi khởi động lỗi, không sinh token, không bind cổng khác, thoát 2; token sai không tạo phiên.
- **Kích hoạt (Trigger)**: Operator chạy `php-quickpatch.sh serve` trên terminal SSH.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chạy `php-quickpatch.sh serve` (`FR-CON-AUTH-001`).
2. Hệ thống kiểm Python ≥ 3.6, có TTY; đọc `STATE_DIR/console/serve.pid`; cổng 17321 (hoặc `--port` trong 1024–32767) rảnh (`BR-CON-002`).
3. Hệ thống bind duy nhất `127.0.0.1:<port>` (`BR-CON-001`), sinh token bằng `secrets.token_urlsafe(32)` (43 ký tự), giữ trong bộ nhớ chỉ SHA-256 của token, ghi PID file `0600`, ghi audit "token issued" không kèm token (`FR-CON-AUTH-002`, `BR-AUTH-001`).
4. Hệ thống đối soát job `RUNNING` của lần trước (PID không sống → `INTERRUPTED`) và dọn log job quá hạn (`FR-JOB-RUN-004`, `FR-JOB-LOG-003`).
5. Hệ thống in đúng 1 lần ra terminal: URL `http://127.0.0.1:<port>/#t=<token>` và lệnh `ssh -N -L <port>:127.0.0.1:<port> <user>@<host>`.
6. Operator mở tunnel trên máy trạm và mở URL trên trình duyệt.
7. Trình duyệt gửi `GET /`; hệ thống kiểm `Host` = `127.0.0.1:<port>` hoặc `localhost:<port>` trước định tuyến (`FR-CON-AUTH-005`, `BR-CON-003`), trả trang tĩnh nhúng kèm header CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer` (`FR-CON-SAFE-002`, `BR-CON-007`).
8. JS đọc fragment `#t=`, gọi `POST /api/v1/sessions` `{"token": "..."}`, rồi `history.replaceState` xoá fragment (`BR-AUTH-006`).
9. Hệ thống so `sha256(token nhập)` với giá trị lưu bằng `hmac.compare_digest` (`FR-CON-AUTH-003`, `BR-AUTH-002`), cấp `session_id` 32 byte, cookie `qp_session`, CSRF token 32 byte trong body; ghi audit đăng nhập thành công (`BR-AUTH-004`).
10. Trình duyệt gọi `GET /api/v1/overview` bằng cookie; hệ thống xác thực mọi request (trừ `GET /`, `GET /login`, `GET /static/*`, `POST /api/v1/sessions`) và trả envelope rules/10 `{success, data, error, meta, timestamp}` (`FR-CON-AUTH-004`, `FR-CON-API-001`).
11. Với mọi request ghi bằng cookie, trình duyệt gửi `X-QP-CSRF`, `Origin`, `Content-Type: application/json`; hệ thống kiểm trước khi xử lý (`FR-CON-AUTH-006`, `BR-CON-004`).
12. Console hiển thị SCR-002 (UC-CON-002).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. Không có Python ≥ 3.6**:
  - 2a1. Hệ thống in `ERR-CON-424-01` "Console cần Python 3.6 trở lên (hiện có: {version})."; CLI vẫn dùng được; thoát 2.
- **2b. Không có TTY và không có `--token-file`**:
  - 2b1. Hệ thống in `ERR-CON-412-01`, thoát 2.
- **2c. Có `--token-file PATH`**:
  - 2c1. Hệ thống ghi token vào file quyền `0600` thay vì in; xoá file khi `serve` dừng.
- **2d. Cổng bị phiên `serve` cũ của tool chiếm**:
  - 2d1. Không có `--replace` → `ERR-CON-409-01` kèm PID, thoát 2.
  - 2d2. Có `--replace` → phiên cũ nhận SIGTERM, chờ 10 s, SIGKILL; mọi phiên cũ mất hiệu lực; luồng tiếp tục bước 3.
- **2e. Cổng bị tiến trình khác chiếm**:
  - 2e1. `ERR-CON-409-02` kèm tên tiến trình, PID; không tự đổi cổng (`BR-CON-002`); thoát 2.
- **2f. `--port` ngoài 1024–32767**:
  - 2f1. `ERR-CLI-400-01`, thoát 2.
- **6a. Tunnel dùng cổng cục bộ khác cổng `serve`**:
  - 6a1. Request bị trả 421 `ERR-CON-421-01`; Operator mở tunnel đúng cổng hoặc chạy `serve --allow-local-port N` (tối đa 3 cổng).
- **7a. Header `Host` thiếu hoặc sai cú pháp**:
  - 7a1. 400 `ERR-CON-400-01`.
- **7b. Host không thuộc danh sách (DNS rebinding)**:
  - 7b1. 421 `ERR-CON-421-01`, áp cả cho tài nguyên tĩnh và SSE; ghi log không kèm Cookie/Authorization.
- **7c. Đường dẫn tĩnh không có trong bảng ánh xạ cố định**:
  - 7c1. 404 `ERR-CON-404-01`; không liệt kê thư mục, không ghép đường dẫn từ URL.
- **8a. Fragment bị mất (mở URL không có `#t=`)**:
  - 8a1. Console hiển thị SCR-001; Operator dán token vào ô nhập (ngoại lệ `BR-AUTH-006`).
- **9a. Token sai**:
  - 9a1. 401 `ERR-AUTH-401-01`; ghi audit đăng nhập thất bại gộp theo phút.
- **9b. 5 lần sai trong 60 s**:
  - 9b1. 429 `ERR-AUTH-429-01` cho mọi lần đăng nhập trong 60 s; 50 lần sai trong 1 phiên `serve` → in cảnh báo ra terminal của `serve` (`BR-AUTH-003`).
- **9c. Đã có 5 phiên hiệu lực**:
  - 9c1. 409 `ERR-AUTH-409-01`; Operator đăng xuất phiên khác.
- **10a. Client không phải trình duyệt (curl, script CI)**:
  - 10a1. Gửi `Authorization: Bearer <token>`; không tạo phiên, không cần CSRF; token qua query string bị từ chối (`BR-AUTH-005`).
- **10b. Phiên quá 30 phút không hoạt động hoặc quá 12 giờ từ đăng nhập**:
  - 10b1. 401 `ERR-AUTH-401-02`; console chuyển về SCR-001.
- **10c. Operator bấm "Đăng xuất"**:
  - 10c1. `DELETE /api/v1/sessions/current`; phiên bị xoá, cookie hết hạn.
- **10d. Body > 64 KiB, header > 8 KiB, phương thức không hỗ trợ, lỗi nội bộ**:
  - 10d1. 413 `ERR-CON-413-01`, 405 `ERR-CON-405-01`, 500 `ERR-CON-500-01` kèm mã tham chiếu, không trả stack trace (`BR-CON-009`).
- **11a. Request ghi thiếu `X-QP-CSRF`, `Origin` sai, hoặc không phải `application/json`**:
  - 11a1. 403 `ERR-AUTH-403-01`, 403 `ERR-AUTH-403-02`, 415 `ERR-CON-415-01`.
- **12a. Operator chạy `serve --stop` khi có job ghi `RUNNING`**:
  - 12a1. Hệ thống in `ERR-CON-409-03` kèm `job_id`, `phase`; request mới nhận 503 `ERR-CON-503-01`; console dừng sau khi job kết thúc; mọi phiên mất hiệu lực.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-SEC-001`..`NFR-SEC-006`, `NFR-SEC-009`: loopback, token, xác thực 100% endpoint, Host, CSRF, header/CSP, chống XSS.
- `NFR-PERF-006`: khởi động ≤ 3 s; RSS ≤ 100 MB khi rảnh.
- `NFR-PERF-007`: tài nguyên tĩnh ≤ 500 KB; SCR-002 hiển thị ≤ 2 s qua tunnel 1 Mbit/s, RTT 100 ms.
- `NFR-REL-001`: console hoạt động khi PHP-FPM, Node.js và web server đều dừng.
- `NFR-CMP-003`: Python 3.6–3.14; phiên bản ổn định hiện hành và liền trước của Chrome, Edge, Firefox, Safari ([nfr.md](../srs/nfr.md) v1.0.1).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-CON-001`, `BR-CON-002` | Chỉ loopback; cổng cố định, không tự tăng | 2, 3 |
| `BR-AUTH-001`, `BR-AUTH-006` | Token phiên `serve`; token qua URL fragment | 3, 5, 8 |
| `BR-AUTH-002`, `BR-AUTH-003`, `BR-AUTH-004`, `BR-AUTH-005` | So sánh hằng thời gian, giới hạn thử sai, phiên, Bearer | 9, 10 |
| `BR-CON-003`, `BR-CON-004`, `BR-CON-007`, `BR-CON-009` | Host, CSRF, header + tài nguyên tĩnh, giới hạn request | 7, 10, 11 |
| `BR-JOB-005` | Đối soát job khi khởi động lại | 4 |
| `BR-SEC-006`, `BR-AUD-001` | Không lộ bí mật; audit token/đăng nhập | 3, 9 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | 1–3, 12a |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | 3, 5 |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | 7 |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | 7 |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | 8, 9 |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | 10 |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | 10 |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | 11 |

### Giao diện và API liên quan
- Màn hình: `SCR-001` Đăng nhập token; đích sau đăng nhập `SCR-002`.
- API: `GET /`, `GET /login`, `GET /static/{file}`, `POST /api/v1/sessions`, `GET /api/v1/sessions/current`, `DELETE /api/v1/sessions/current`.

### Quan hệ với use case khác
- Tiền điều kiện của mọi use case trên console (UC-CON-002, UC-CON-003, UC-JOB-*, UC-PLAN-*, UC-UPG-*, UC-PTCH-*, UC-FEED-001/003/004, UC-RPT-*).
- `<<include>>` đối soát job của UC-JOB-001 (`FR-JOB-RUN-004`) ở bước 4.

### Ghi chú và tài liệu tham chiếu
- Hành vi thư viện chuẩn đã kiểm chứng trong SRS (spec §1.4): `secrets.token_urlsafe` (Python ≥ 3.6, 32 byte = 256 bit), `hmac.compare_digest`, `http.server` "chỉ kiểm tra bảo mật cơ bản", `EventSource` không gửi header tuỳ chỉnh.
- Cổng 17321 chưa đối chiếu sổ đăng ký IANA (`Q-SRS-01`); thời hạn phiên 30 phút/12 giờ/5 phiên chờ PO (`Q-SRS-03`).
- Máy trạng thái `serve` và phiên: [states.md §7](../srs/states.md); sơ đồ: [flows-console-fleet.md §2](../srs/flows-console-fleet.md).
- Auditor (`PER-04`) Phase 1 không có tài khoản riêng; xem console bằng phiên do Operator mở hoặc nhận báo cáo xuất (UC-RPT-001, UC-RPT-002).
