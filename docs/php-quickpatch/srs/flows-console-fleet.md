---
id: DOC-SRS-QP-FLOW-003
title: Sơ đồ tuần tự — php-quickpatch v2 — luồng 7 (serve, token, Host/CSRF) và luồng 8 (Phase 2 chạy CLI từ xa qua SSH)
version: 1.0.1
phase: Specification
domain: Security Patch Management
tags: [srs, sequence-diagram, mermaid, console, serve, token, session, dns-rebinding, csrf, fleet, ssh, phase-2, openba]
depends_on:
  - DOC-SRS-QP-FLOW-001
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
related_diagrams:
  - DIAG-SEQ-QP-AUTH-002
  - DIAG-SEQ-QP-FLT-001
  - DIAG-SEQ-QP-AUTH-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Sơ đồ tuần tự — luồng 7 (serve, token, Host/CSRF) và luồng 8 (Phase 2)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: DIAG-SEQ-QP-AUTH-002 (bản đầy đủ của DIAG-SEQ-QP-AUTH-001: khởi động `serve`, token 256 bit, cổng G1–G4, Bearer, đăng xuất, dừng console) và DIAG-SEQ-QP-FLT-001 (Phase 2: dry-run toàn nhóm, canary, đợt ≤ 5 server qua SSH). Tách từ DOC-SRS-QP-FLOW-001 do giới hạn 800 dòng |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: bỏ chú thích "(mã đề xuất mới)" của `ERR-FLT-422-03` trong DIAG-SEQ-QP-FLT-001 vì mã đã được định nghĩa chuẩn ở error-matrix.md §3.13 (DOC-SRS-QP-ERR-001 v1.0.1); câu dẫn cuối §4 trỏ tới định nghĩa chuẩn này |

## 1. Quy ước
Participant, ký hiệu và cổng dùng chung theo [flows.md §1.4–§1.6](flows.md). Cổng mặc định 17321 (`BR-CON-002`, câu hỏi mở `Q-SRS-01`). Luồng 7 là nơi vẽ đầy đủ cổng G1–G4; các sơ đồ khác vẽ rút gọn.

## 2. Luồng 7 — Khởi động `serve`, xác thực token, chặn Host và CSRF

### 2.1 Ngữ cảnh (DIAG-SEQ-QP-AUTH-002)
- **Use case**: `UC-CON-001`.
- **Tiền điều kiện**: người vận hành có phiên SSH trên máy chủ (có TTY, `A-SRS-03`) và mở được SSH local forwarding từ máy trạm (`A-SRS-01`).
- **Hậu điều kiện thành công**: console chỉ lắng nghe `127.0.0.1:17321` (`NFR-SEC-001`); trình duyệt có cookie `qp_session` và CSRF token trong bộ nhớ; job `RUNNING` của lần chạy trước đã được đối soát (`NFR-REL-003`).
- **Ràng buộc**: khởi động ≤ 3 s, RSS ≤ 100 MB khi rảnh (`NFR-PERF-006`); token 256 bit CSPRNG, 0 lần xuất hiện trong log/audit/JSON/`STATE_DIR` (`NFR-SEC-002`); 100% endpoint (trừ `GET /`, `GET /login`, `GET /static/*`, `POST /api/v1/sessions`) trả 401 khi thiếu xác thực (`NFR-SEC-003`); 100% Host sai trả 421 (`NFR-SEC-004`); 100% request ghi bằng cookie thiếu CSRF/Origin sai bị từ chối (`NFR-SEC-005`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash)
    participant FS as STATE_DIR (tệp)

    Op->>CLI: Terminal SSH trên máy chủ: php-quickpatch.sh serve [--port 17321]
    CLI->>CLI: Kiểm python3 ≥ 3.6, --port trong 1024–32767 (FR-CON-AUTH-001, BR-CON-002)
    break Thiếu Python 3.6+
        CLI-->>Op: exit 2, ERR-CON-424-01
    end
    break Không có TTY và không có --token-file (BR-AUTH-001)
        CLI-->>Op: exit 2, ERR-CON-412-01
    end
    CLI->>FS: Đọc console/serve.pid, kiểm cổng 127.0.0.1:17321
    alt Cổng bị phiên serve cũ giữ (PID sống, cmdline chứa qp-console.py) và không có --replace
        CLI-->>Op: exit 2, ERR-CON-409-01 kèm PID cũ
    else Cổng bị tiến trình khác giữ
        CLI-->>Op: exit 2, ERR-CON-409-02, không tự chọn cổng khác
    else Cổng rảnh, hoặc phiên cũ và có --replace
        opt Có --replace và phiên serve cũ còn sống
            CLI->>CLI: SIGTERM PID cũ, chờ 10 s, SIGKILL nếu còn sống
        end
        CLI->>CON: Khởi động qp-console.py, bind duy nhất 127.0.0.1:17321, không bind IPv6 (BR-CON-001)
        CON->>CON: token = secrets.token_urlsafe(32), chỉ giữ SHA-256 trong bộ nhớ (FR-CON-AUTH-002)
        CON->>FS: Ghi console/serve.pid quyền 0600, audit "token issued" không kèm token
        CON->>FS: Đối soát jobs/*/job.json: RUNNING có PID chết → INTERRUPTED (ERR-JOB-500-02), không tự chạy lại job ghi (FR-JOB-RUN-004)
        CON->>FS: Dọn output.log quá 30 ngày, giữ jobs/ ≤ 200 MiB (FR-JOB-LOG-003)
        CON-->>Op: In đúng 1 lần URL http://127.0.0.1:17321/ kèm fragment t=TOKEN và lệnh ssh -N -L 17321:127.0.0.1:17321 user@host
    end
    Op->>BR: Máy trạm: mở tunnel, dán URL vào trình duyệt
    BR->>CON: GET / (Host: 127.0.0.1:17321), fragment không được gửi lên máy chủ
    CON->>CON: G1 kiểm Host trước định tuyến và trước xác thực (FR-CON-AUTH-005, BR-CON-003)
    alt Thiếu Host hoặc request sai cú pháp
        CON-->>BR: 400 ERR-CON-400-01
    else Host ngoài danh sách (DNS rebinding, vd attacker.example:17321, hoặc tunnel dùng cổng cục bộ khác chưa khai báo)
        CON-->>BR: 421 ERR-CON-421-01, log không ghi Cookie/Authorization
    else Đường dẫn tĩnh không có trong bảng ánh xạ cố định (FR-CON-SAFE-002)
        CON-->>BR: 404 ERR-CON-404-01
    else Hợp lệ
        CON-->>BR: 200 trang tĩnh + CSP default-src 'none', nosniff, no-referrer, X-Frame-Options DENY, COOP, CORP (BR-CON-007)
    end
    BR->>BR: JS đọc fragment t, history.replaceState xoá fragment, giữ token trong biến bộ nhớ (BR-AUTH-005, BR-AUTH-006)
    BR->>CON: POST /api/v1/sessions {token}, Content-Type: application/json
    CON->>CON: G1, G2, giới hạn thử sai (BR-AUTH-003)
    alt Đã sai 5 lần trong 60 s
        CON-->>BR: 429 ERR-AUTH-429-01, từ chối đăng nhập 60 s
    else compare_digest(SHA-256 token nhập, SHA-256 lưu) sai (BR-AUTH-002)
        CON->>FS: Audit đăng nhập thất bại gộp theo phút, 50 lần sai → cảnh báo trên terminal serve
        CON-->>BR: 401 ERR-AUTH-401-01
    else Đã có 5 phiên hiệu lực
        CON-->>BR: 409 ERR-AUTH-409-01
    else Token đúng
        CON->>CON: session_id 32 byte ngẫu nhiên, CSRF token 32 byte (BR-AUTH-004)
        CON->>FS: Audit đăng nhập thành công
        CON-->>BR: 200 {session_expires_at, csrf_token} + Set-Cookie qp_session (HttpOnly, SameSite=Strict, Path=/)
    end
    BR->>CON: GET /api/v1/overview (cookie qp_session)
    CON->>CON: G1, G3 xác thực phiên (FR-CON-AUTH-004)
    alt Thiếu cookie/Bearer hoặc phiên không tồn tại
        CON-->>BR: 401 ERR-AUTH-401-01
    else Quá 30 phút không hoạt động hoặc quá 12 giờ từ lúc đăng nhập
        CON-->>BR: 401 ERR-AUTH-401-02, JS chuyển về SCR-001
    else Phiên hợp lệ
        CON-->>BR: 200 dữ liệu SCR-002 (P95 ≤ 500 ms, NFR-PERF-001)
    end
    BR->>CON: POST /api/v1/jobs (cookie, X-QP-CSRF, Origin: http://127.0.0.1:17321, Content-Type: application/json)
    CON->>CON: G1–G4 (FR-CON-AUTH-006, BR-CON-004, BR-CON-009)
    alt Body > 64 KiB hoặc header > 8 KiB
        CON-->>BR: 413 ERR-CON-413-01
    else Phương thức không hỗ trợ cho đường dẫn
        CON-->>BR: 405 ERR-CON-405-01
    else Thiếu hoặc sai X-QP-CSRF
        CON-->>BR: 403 ERR-AUTH-403-01
    else Origin thiếu hoặc ngoài danh sách (trang khác gửi request chéo nguồn)
        CON-->>BR: 403 ERR-AUTH-403-02, không gửi Access-Control-Allow-*
    else Content-Type khác application/json
        CON-->>BR: 415 ERR-CON-415-01
    else Đạt G1–G4
        CON->>CON: Cổng G5, J, D theo DIAG-SEQ-QP-PTCH-001
        CON-->>BR: 202 {job_id}
    end
    opt Client không phải trình duyệt (curl, script CI)
        Op->>CON: Request kèm Authorization: Bearer TOKEN, không cookie
        CON->>CON: G1, G3 Bearer, không yêu cầu CSRF, token trong query string bị từ chối (BR-AUTH-005)
        CON-->>Op: 2xx hoặc 401 ERR-AUTH-401-01
    end
    opt Đăng xuất
        BR->>CON: DELETE /api/v1/sessions/current + X-QP-CSRF
        CON-->>BR: 200, huỷ phiên, xoá cookie
    end
    opt Dừng console
        Op->>CLI: php-quickpatch.sh serve --stop
        CLI->>FS: Kiểm job write RUNNING
        alt Có job write RUNNING
            CLI-->>Op: ERR-CON-409-03, chờ job kết thúc rồi dừng
        else Không có
            CLI->>CON: SIGTERM
            CON-->>BR: Request mới trong lúc dừng → 503 ERR-CON-503-01
            CON->>FS: Huỷ mọi phiên, xoá token file, xoá serve.pid
        end
    end
    Note over BR,CON: Lỗi không lường trước ở mọi bước → 500 ERR-CON-500-01 kèm mã tham chiếu log, không trả stack trace (BR-CON-009)
```

## 3. Luồng 8 — Phase 2: máy trung tâm chạy CLI từ xa qua SSH

### 3.1 Ngữ cảnh (DIAG-SEQ-QP-FLT-001)
- **Use case**: `UC-FLT-002` (chạy lệnh theo đợt), `UC-FLT-003` (xem tổng hợp). Phase 2 chỉ đặc tả, chưa triển khai.
- **Participant**: `CON` = console máy trung tâm (Python, chỉ bind `127.0.0.1`, truy cập qua SSH tunnel, `C-SRS-06`); `DB` = `central.db` (SQLite, `FR-FLT-INV-001`); `CLI` = `php-quickpatch.sh` chạy trên server được quản lý; `FS` = `STATE_DIR` của server (giữ backup, audit, feeds theo `FR-FLT-EXEC-001`).
- **Tiền điều kiện**: tài khoản vai trò Operator đã đăng nhập (`FR-FLT-RBAC-001`); server đã khai báo và ghim fingerprint khoá máy chủ (`FR-FLT-INV-002`).
- **Hậu điều kiện thành công**: `fleet_run` có kết quả từng server; audit server được gộp, giữ `hash` gốc (`FR-FLT-AUD-001`); 0 file tạm còn lại ngoài `STATE_DIR` trên server (`NFR-SEC-012`).
- **Ràng buộc**: canary 1 server → đợt ≤ 5 server, ≤ 10 kết nối song song, dừng khi canary lỗi hoặc > 20% server của đợt lỗi (`BR-FLT-005`); thu `scan --json` từ 100 server với 10 kết nối song song ≤ 20 phút (`NFR-PERF-008`); 0 kết nối chấp nhận khoá máy chủ chưa ghim, 0 mật khẩu SSH lưu trữ (`NFR-SEC-011`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator (vai trò Operator)
    participant BR as Browser
    participant CON as Console trung tâm (Python)
    participant DB as SQLite (central.db)
    participant CLI as CLI (Bash) trên server
    participant FS as STATE_DIR server (tệp)

    Note over Op,CON: Đăng nhập tài khoản Phase 2 qua SSH tunnel, máy trung tâm chỉ bind 127.0.0.1, cổng G1–G4 như DIAG-SEQ-QP-AUTH-002
    Op->>BR: SCR-022 → chọn nhóm server, hành động fix, kích thước đợt
    BR->>CON: POST /api/v1/fleet-runs {group, action: "fix", params, batch_size} + X-QP-CSRF
    CON->>DB: Tra vai trò tài khoản và danh sách server của nhóm
    alt Vai trò Viewer (BR-FLT-008)
        CON-->>BR: 403 ERR-FLT-403-02
    else server_id trong yêu cầu không tồn tại
        CON-->>BR: 404 ERR-FLT-404-01
    else Hành động ngoài danh sách trắng hoặc tham số sai
        CON-->>BR: 422 ERR-CON-422-01
    else Hợp lệ
        CON->>DB: Tạo fleet_run, trạng thái từng server = PENDING, audit trung tâm
        CON-->>BR: 202 {fleet_run_id}
    end
    loop Giai đoạn dry-run trên mọi server đích, tối đa 10 kết nối song song (BR-FLT-005)
        CON->>CLI: ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=known_hosts riêng -o ConnectTimeout=10, chỉ khoá SSH (BR-FLT-002)
        alt Không kết nối được trong 10 s
            CON->>DB: Server TIMEOUT, ERR-FLT-504-01
        else Fingerprint khoá máy chủ khác giá trị đã ghim
            CON->>DB: Server lỗi, ERR-FLT-403-01, không gửi lệnh
        else Khoá SSH bị từ chối
            CON->>DB: Server lỗi, ERR-FLT-401-01
        else Đã kết nối
            CON->>CLI: mktemp -d, đẩy gói CLI bằng tar qua SSH, sha256sum -c (BR-FLT-003)
            alt SHA-256 gói CLI lệch hash của máy trung tâm
                CON->>DB: Server lỗi, ERR-FLT-422-03, không chạy
            else Thiếu Bash ≥ 4.3, flock hoặc curl
                CON->>DB: Server lỗi, ERR-FLT-424-01
            else Gói hợp lệ
                CON->>CLI: Chạy TMP/php-quickpatch.sh fix --dry-run --json (sudo -n khi sudo_mode = sudo-n), timeout theo BR-JOB-008
                CLI->>FS: Khoá chia sẻ, đọc bundle feeds/current/ của server
                alt Vượt timeout (BR-FLT-004)
                    CON->>CLI: Ngắt phiên SSH
                    CON->>DB: Server TIMEOUT, ERR-FLT-504-01
                else Có stdout
                    CLI-->>CON: Envelope qp.fix/1 + mã thoát
                    alt JSON sai schema hoặc khác major hỗ trợ
                        CON->>DB: Server lỗi, ERR-FLT-422-02
                    else Hợp lệ
                        CON->>DB: Lưu kết quả dry-run, collected_at
                    end
                end
            end
            CON->>CLI: Xoá thư mục TMP, kể cả khi lỗi (BR-FLT-001)
        end
    end
    break Có server đích chưa dry-run thành công
        CON->>DB: fleet_run dừng trước bước ghi, giữ mã lỗi từng server (BR-FLT-005)
        CON-->>BR: Trạng thái fleet_run và lỗi từng server
    end
    CON->>CLI: Đợt 1 = 1 server canary: fix --json (cùng quy trình đẩy gói, kiểm SHA-256, dọn TMP)
    CLI->>FS: flock -x STATE_DIR/.lock, audit intent, manifest, vá như DIAG-SEQ-QP-PTCH-001
    alt Khoá của server đang bị lượt khác giữ
        CLI-->>CON: exit 2, ERR-CLI-423-01
    else Hoàn tất
        CLI-->>CON: Envelope qp.fix/1, exit 0 hoặc 1
    end
    alt Canary lỗi (exit 2, timeout hoặc JSON sai)
        CON->>DB: fleet_run STOPPED, ERR-FLT-409-01
    else Canary đạt
        loop Các đợt tiếp theo, ≤ 5 server mỗi đợt, ≤ 10 kết nối song song
            CON->>CLI: fix --json trên từng server của đợt
            CLI-->>CON: Envelope + mã thoát
            CON->>DB: Kết quả từng server, collected_at
            break Hơn 20% server của đợt lỗi
                CON->>DB: fleet_run STOPPED, ERR-FLT-409-01, đợt sau không chạy
            end
        end
        CON->>DB: fleet_run COMPLETED, gộp audit server vào audit trung tâm giữ hash gốc (FR-FLT-AUD-001)
    end
    BR->>CON: GET /api/v1/fleet-runs/{fleet_run_id}
    CON->>DB: Đọc trạng thái fleet_run
    CON-->>BR: 200 trạng thái và mã lỗi từng server
    BR->>CON: GET /api/v1/fleet-summary
    CON->>DB: Ma trận server × runtime, collected_at
    CON-->>BR: 200, dữ liệu > 24 giờ gắn nhãn "cũ", > 7 ngày loại khỏi số liệu tổng (BR-FLT-006)
    BR-->>Op: SCR-022 tiến độ đợt, SCR-021 dashboard tổng hợp
```

## 4. Ánh xạ bước → yêu cầu (rút gọn)
| Sơ đồ | Nhóm bước | FR | BR | NFR |
| :--- | :--- | :--- | :--- | :--- |
| DIAG-SEQ-QP-AUTH-002 | Khởi động `serve`, cổng, token, đối soát job | `FR-CON-AUTH-001`, `FR-CON-AUTH-002`, `FR-JOB-RUN-004`, `FR-JOB-LOG-003` | `BR-CON-001`, `BR-CON-002`, `BR-AUTH-001`, `BR-JOB-005` | `NFR-PERF-006`, `NFR-SEC-001`, `NFR-SEC-002`, `NFR-REL-003` |
| DIAG-SEQ-QP-AUTH-002 | Host, tài nguyên tĩnh, header | `FR-CON-AUTH-005`, `FR-CON-SAFE-002` | `BR-CON-003`, `BR-CON-007` | `NFR-SEC-004`, `NFR-SEC-006` |
| DIAG-SEQ-QP-AUTH-002 | Đăng nhập, phiên, Bearer, đăng xuất | `FR-CON-AUTH-003`, `FR-CON-AUTH-004` | `BR-AUTH-002..006` | `NFR-SEC-003` |
| DIAG-SEQ-QP-AUTH-002 | CSRF, giới hạn request, lỗi nội bộ, dừng console | `FR-CON-AUTH-006`, `FR-CON-API-001` | `BR-CON-004`, `BR-CON-009` | `NFR-SEC-005` |
| DIAG-SEQ-QP-FLT-001 | Phân quyền, tạo đợt | `FR-FLT-RBAC-001`, `FR-FLT-EXEC-002` | `BR-FLT-008`, `BR-FLT-005` | — |
| DIAG-SEQ-QP-FLT-001 | SSH, đẩy gói, chạy từ xa, dọn tạm | `FR-FLT-INV-002`, `FR-FLT-EXEC-001` | `BR-FLT-001..004` | `NFR-SEC-011`, `NFR-SEC-012` |
| DIAG-SEQ-QP-FLT-001 | Canary, đợt, tổng hợp, audit | `FR-FLT-EXEC-002`, `FR-FLT-DASH-001`, `FR-FLT-AUD-001` | `BR-FLT-005`, `BR-FLT-006` | `NFR-PERF-008` |

Phát hiện và giả định của tài liệu này được tổng hợp tại [flows.md §6](flows.md). Mã `ERR-FLT-422-03` dùng ở DIAG-SEQ-QP-FLT-001 được định nghĩa chuẩn tại [error-matrix.md §3.13](error-matrix.md) (DOC-SRS-QP-ERR-001, từ v1.0.1).

## 5. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| [spec.md §1.4, §3.3, §4.1.3](spec.md) (DOC-SRS-QP-001) | Danh mục API, DIAG-SEQ-QP-AUTH-001, nguồn Python `secrets`/`hmac`/`http.server` đã kiểm chứng | Đã đọc |
| [functional-requirements.md §9, §10, §13](functional-requirements.md), [business-rules.md §4.7–§4.9, §4.12](business-rules.md) | `FR-CON-*`, `FR-JOB-*`, `FR-FLT-*`, `BR-AUTH-*`, `BR-CON-*`, `BR-JOB-*`, `BR-FLT-*` | Đã đọc |
| WHATWG HTML — Server-sent events, https://html.spec.whatwg.org/multipage/server-sent-events.html | `EventSourceInit` chỉ có `withCredentials` (không gửi header tuỳ chỉnh → SSE xác thực bằng cookie); dòng bắt đầu bằng `:` bị bỏ qua, khuyến nghị gửi khoảng 15 s để giữ kết nối; trường `retry` tính bằng mili giây; header `Last-Event-ID` khi nối lại | Kiểm chứng (WebFetch 2026-10-22) |
| Mermaid — Sequence diagrams, https://mermaid.js.org/syntax/sequenceDiagram.html | Cú pháp khối `alt`, `opt`, `loop`, `par`, `break`; tránh `;` và `#` trong thông điệp | Kiểm chứng (WebFetch 2026-10-22); 2 sơ đồ qua `mermaid.parse` (Mermaid 11.4.1) |
