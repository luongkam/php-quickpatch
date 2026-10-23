---
id: DOC-API-QP-006
title: Thiết kế hợp đồng API — Phase 2 (máy trung tâm nhiều server) và giao thức SSH controller → host
version: 1.0.1
phase: API & Integration Design
domain: Security Patch Management
tags: [api-design, phase-2, fleet, ssh, rbac, host-key-pinning, rollout, snapshot-distribution]
depends_on:
  - DOC-API-QP-001
  - DOC-API-QP-005
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-FLOW-003
  - FR-FLT-EXEC-001
  - FR-FLT-EXEC-002
  - FR-FLT-RBAC-001
  - BR-FLT-001
  - BR-FLT-002
  - BR-FLT-003
  - BR-FLT-005
related_diagrams:
  - DIAG-SEQ-QP-FLT-001
author: BA Agent
last_updated: 2026-10-22
---

# Phase 2 — API máy trung tâm và giao thức SSH controller → host

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: xác thực tài khoản và vai trò, 13 endpoint Phase 2 (#45–#57 của DOC-API-QP-001 §3.2), giao thức SSH 8 bước (S0–S7), phân phối snapshot |
| 1.0.1 | 2026-10-22 | BA Agent | §3.7 sửa ví dụ runtime PHP 8.2.34 từ `R` = 78 `CRITICAL` thành `R` = 60 `HIGH` theo `BR-FEED-040` (khớp ví dụ 3 của data-sources-merge-risk.md §8.5, api-spec-core.md 1.0.1); định nghĩa nguồn của `totals` (`kev`, `critical` đếm finding từ `summary.*` của `qp.scan/1`, `eol`, `unpatched` đếm runtime) nên `totals` không đổi; thêm nguồn tham chiếu §6 |

## 1. Phạm vi
- **Chỉ đặc tả, chưa triển khai** (spec §1.2). Máy trung tâm chạy console cùng mã nguồn Phase 1, chỉ bind `127.0.0.1`, truy cập qua SSH tunnel (`C-SRS-06`); lưu danh mục server, tài khoản, đợt chạy, kết quả thu được trong `central.db` (SQLite, `FR-FLT-INV-001`).
- Quy chuẩn chung của [api-spec.md §2](api-spec.md) giữ nguyên (envelope, Host, CSRF, giới hạn, timeout). Khác biệt: §2 (xác thực bằng tài khoản, vai trò). Endpoint Phase 1 khi gọi trên máy trung tâm trả dữ liệu của chính máy trung tâm; dữ liệu server khác xem qua #50 (`FR-FLT-DASH-002`, chế độ chỉ đọc).
- **Không có webhook**: server được quản lý không gọi về máy trung tâm; máy trung tâm kéo dữ liệu qua SSH (§4).

## 2. Xác thực và vai trò

### 2.1 Đăng nhập tài khoản
| Hạng mục | Quy định | Căn cứ |
| :--- | :--- | :--- |
| Endpoint | `POST /api/v1/sessions` body `{"username": "...", "password": "..."}` (thay `{"token"}` của Phase 1); cookie, CSRF, giới hạn phiên như Phase 1 | `FR-FLT-RBAC-001`, `BR-AUTH-004` |
| Băm mật khẩu | `hashlib.scrypt(password, salt=<16 byte ngẫu nhiên>, n=2**17, r=8, p=1, maxmem=256 MiB, dklen=64)`; lưu `scrypt$17$8$1$<salt b64>$<hash b64>`; so bằng `hmac.compare_digest` (ĐX; tham số tối thiểu theo OWASP; `maxmem` phải > 128 MiB vì mặc định OpenSSL 1.1.0 là 32 MiB) | `Q-SRS-06`, `BR-AUTH-002` |
| Độ dài mật khẩu | 12–128 ký tự (ĐX) | — |
| Thử sai | 5 lần sai trong 60 s theo `username` → khoá đăng nhập tài khoản đó 60 s (`ERR-AUTH-429-01`) | `BR-AUTH-003` |
| Tài khoản Admin đầu tiên | Tạo bằng CLI trên máy trung tâm (ngoài API), không có mật khẩu mặc định (ĐX) | — |
| Bearer | Không hỗ trợ ở v1 của Phase 2 (ĐX, `Q-P2-02`) | — |

### 2.2 Ma trận quyền theo endpoint (`BR-FLT-008`)
| Endpoint | Viewer | Operator | Admin |
| :--- | :---: | :---: | :---: |
| #45 `GET /api/v1/servers`, #50 `…/results`, #51 `fleet-summary`, #53 `GET /api/v1/fleet-runs/{fleet_run_id}`, #57 `fleet-audit-events` | Có | Có | Có |
| #52 `POST /api/v1/fleet-runs`, #54 `POST /api/v1/feed-distributions` | — | Có | Có |
| #46–#49 quản lý server, kiểm kết nối; #55–#56 tài khoản | — | — | Có |
| Endpoint Phase 1 đọc / xuất báo cáo | Có | Có | Có |
| Endpoint Phase 1 tạo job ghi, điều khiển kế hoạch | — | Có | Có |

Vai trò không đủ → 403 `ERR-FLT-403-02` (kiểm sau G3, trước G5).

## 3. Endpoint Phase 2
Định danh (ĐX): `server_id` `^[a-z0-9][a-z0-9_.-]{0,62}$`; `fleet_run_id` `^FLR-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$`; `username` `^[a-z][a-z0-9_.-]{2,31}$`; `group` `^[a-z0-9_-]{1,32}$`.

### 3.1 `GET /api/v1/servers` (V)
Query: `group`, `enabled` (boolean), `last_check` (`PASS`,`FAIL`,`NONE`), `page`, `limit`. Sắp xếp `server_id`. FR: `FR-FLT-INV-001`.
```json
"data": {"items": [{"server_id": "web01", "host": "203.0.113.10", "port": 22, "ssh_user": "qpops", "auth": {"type": "key", "key_path": "/root/.ssh/qp_fleet_ed25519"},
                    "host_key_fingerprint": "SHA256:…", "groups": ["shop"], "sudo_mode": "sudo-n", "enabled": true,
                    "last_check": {"at": "2026-10-22T08:01:10Z", "result": "PASS"}, "collected_at": "2026-10-22T08:05:44Z", "freshness_label": "fresh"}]}
```
`freshness_label` ∈ {`fresh` (≤ 24 giờ), `old` (> 24 giờ), `excluded` (> 7 ngày)} theo `BR-FLT-006`. Lỗi riêng: không.

### 3.2 `POST /api/v1/servers` (A)
FR: `FR-FLT-INV-001`, `BR-FLT-002`. Phản hồi 201; ghi audit trung tâm.

| Trường | Ràng buộc |
| :--- | :--- |
| `server_id` | Regex trên, duy nhất |
| `host` | Tên miền (≤ 253 ký tự) hoặc địa chỉ IPv4/IPv6 |
| `port` | 1–65535, mặc định 22 |
| `ssh_user` | `^[a-z_][a-z0-9_-]{0,31}$` |
| `auth` | `{"type": "key", "key_path": "<đường dẫn tuyệt đối trên máy trung tâm, file quyền 0600>"}` hoặc `{"type": "agent"}`; có trường `password`/`passphrase` ở bất kỳ đâu → 422 (`BR-FLT-002`, `NFR-SEC-011`) |
| `host_key_fingerprint` | `^SHA256:[A-Za-z0-9+/]{43}$` do Admin lấy qua kênh tin cậy (vd console của nhà cung cấp VPS) |
| `groups` | ≤ 20 phần tử theo regex `group` |
| `sudo_mode` | `none` hoặc `sudo-n` |
| `enabled` | boolean, mặc định `true` |

```json
{"server_id": "web01", "host": "203.0.113.10", "port": 22, "ssh_user": "qpops", "auth": {"type": "key", "key_path": "/root/.ssh/qp_fleet_ed25519"},
 "host_key_fingerprint": "SHA256:…", "groups": ["shop"], "sudo_mode": "sudo-n", "enabled": true}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-FLT-422-01` | 422 | Sai định dạng, trùng `server_id` (`details.constraint = duplicate`), có trường mật khẩu, `key_path` không tồn tại hoặc quyền rộng hơn `0600` |
| `ERR-FLT-403-02` | 403 | Không phải Admin |

### 3.3 `PATCH /api/v1/servers/{server_id}` (A)
Cập nhật một phần mọi trường trừ `server_id`; `enabled=false` = tắt server (bỏ khỏi đợt chạy mới). Đổi `host_key_fingerprint` cần `confirm_retype` = `server_id` và xoá `known_hosts.d/<server_id>` để bước S0 ghim lại (ĐX). Phản hồi 200 với bản ghi mới. Lỗi riêng: `ERR-FLT-403-02`, `ERR-FLT-404-01`, `ERR-FLT-422-01`.

### 3.4 `DELETE /api/v1/servers/{server_id}` (A)
Xoá bản ghi, `known_hosts.d/<server_id>` và kết quả đã thu; audit trung tâm giữ nguyên. Server đang thuộc đợt chạy `RUNNING` → đặt `enabled=false` ngay, xoá khi đợt kết thúc; phản hồi 200 `{"deleted": true}` hoặc `{"deleted": false, "scheduled": true}` (ĐX). Lỗi riêng: `ERR-FLT-403-02`, `ERR-FLT-404-01`.

### 3.5 `POST /api/v1/servers/{server_id}/connection-checks` (A)
FR: `FR-FLT-INV-002`. Chạy đồng bộ bước S0–S1 (§4.3), tổng ≤ 30 s; body `{}`. Kết quả kiểm là dữ liệu nghiệp vụ nên trả **200** cả khi kiểm không đạt; mã lỗi nằm trong `data.errors[]`.
```json
"data": {"server_id": "web01", "result": "FAIL", "checked_at": "2026-10-22T08:01:10Z",
         "reachability": {"connected": false, "latency_ms": null},
         "host_key": {"expected": "SHA256:…", "observed": "SHA256:…", "matches": false},
         "prerequisites": [],
         "errors": [{"code": "ERR-FLT-403-01", "message": "Fingerprint khoá máy chủ khác giá trị đã ghim"}]}
```
`prerequisites[]` = `{check: bash_ge_4_3|flock|curl|sha256sum|tar|mktemp|python3_ge_3_6|sudo_n, required: true|false, actual, pass}` (`python3` không bắt buộc). Mã trong `errors[]`: `ERR-FLT-401-01`, `ERR-FLT-403-01`, `ERR-FLT-424-01`, `ERR-FLT-504-01`. Lỗi riêng (HTTP): `ERR-FLT-403-02`, `ERR-FLT-404-01`.

### 3.6 `GET /api/v1/servers/{server_id}/results` (V)
FR: `FR-FLT-DASH-002`. Query: `command` (`scan`,`assess`,`fix`,`migrate`,`feeds_status`,`audit`), `latest` (boolean, mặc định `true`), `page`, `limit`. `latest=true` → 1 phần tử mỗi `command`, kèm envelope `--json` đầy đủ ([api-spec-cli-json.md](api-spec-cli-json.md)) để console hiển thị các màn hình Phase 1 ở chế độ chỉ đọc.
```json
"data": {"items": [{"result_id": 88123, "command": "scan", "fleet_run_id": "FLR-20261022-080000-4b1e", "collected_at": "2026-10-22T08:05:44Z",
                    "exit_code": 1, "schema": "qp.scan/1", "schema_version": "1.0.0", "freshness_label": "fresh", "envelope": {"…": "qp.scan/1"}}]}
```
Lỗi riêng: `ERR-FLT-404-01`.

### 3.7 `GET /api/v1/fleet-summary` (V)
FR: `FR-FLT-DASH-001`, `BR-FLT-006`. Query: `group`. Ma trận server × runtime từ kết quả `scan`/`assess` mới nhất của từng server.
```json
"data": {"generated_at": "2026-10-22T08:30:00Z",
         "totals": {"servers": 42, "kev": 1, "critical": 9, "eol": 6, "unpatched": 14},
         "servers": [{"server_id": "web01", "collected_at": "2026-10-22T08:05:44Z", "freshness_label": "fresh",
                      "runtimes": [{"runtime_id": "php:3f9a0c1d2e4b", "kind": "php", "version": "8.2.34", "state": "vulnerable",
                                    "lifecycle_status": "SECURITY_ONLY", "kev_count": 0, "critical": 2, "R": 60, "level": "HIGH"}]}],
         "excluded_servers": [{"server_id": "legacy03", "collected_at": "2026-10-10T02:00:00Z"}]}
```
Server `old` vẫn tính vào `totals` kèm nhãn; server `excluded` (> 7 ngày) không tính vào `totals`, liệt kê ở `excluded_servers[]`. `totals.kev`, `totals.critical` = tổng `summary.kev_findings`, `summary.critical_issues` của `qp.scan/1` ([api-spec-cli-json.md](api-spec-cli-json.md)) trên các server được tính, tức đếm finding (runtime, WordPress core, package), không đếm runtime có `level = CRITICAL`; `totals.eol`, `totals.unpatched` đếm runtime (cùng quy ước SCR-021). `R`, `level` của từng runtime lấy nguyên từ envelope đã thu, tính theo `BR-FEED-040..042`: ví dụ PHP 8.2.34 (`SECURITY_ONLY`, 2 critical, 0 KEV) cho `R` = 60, `HIGH` như ví dụ 3 của [data-sources-merge-risk.md §8.5](../srs/data-sources-merge-risk.md). Số server và `totals` trong ví dụ là minh hoạ. Lỗi riêng: không.

### 3.8 `POST /api/v1/fleet-runs` (O)
FR: `FR-FLT-EXEC-001`, `FR-FLT-EXEC-002`, `BR-FLT-005`. Phản hồi 202 `{fleet_run_id, state: "PENDING", servers}`.

| Trường | Ràng buộc |
| :--- | :--- |
| `target` | `{"group": "<group>"}` hoặc `{"server_ids": [1–500 phần tử]}` (đúng 1 dạng); server `enabled=false` bị bỏ qua và liệt kê trong phản hồi |
| `action` | Danh sách trắng Phase 2 (ĐX): `scan`, `assess`, `fix`, `rollback_run`, `feeds_update`, `migrate_healthcheck`, `migrate_install`, `migrate_switch`, `migrate_rollback`; hành động có `site_id`, `plan_id`, `runtime_id`, `run_id` trong `params` chỉ nhận đúng 1 server |
| `params` | Theo lược đồ [api-spec-jobs.md §2](api-spec-jobs.md) |
| `batch_size` | 1–5, mặc định 5 |

Quy trình (`BR-FLT-005`): (1) hành động ghi → giai đoạn dry-run trên **mọi** server đích, ≤ 10 kết nối song song; có server dry-run không thành công → đợt dừng trước bước ghi; (2) đợt 1 = 1 server canary; (3) các đợt tiếp theo ≤ `batch_size` server; dừng khi canary lỗi hoặc > 20% server của 1 đợt lỗi (`ERR-FLT-409-01`). Hành động đọc bỏ qua bước (1)–(2), chạy song song ≤ 10 kết nối.
```json
{"target": {"group": "shop"}, "action": "fix", "params": {"only": ["php"]}, "batch_size": 5}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-FLT-403-02` | 403 | Không phải Operator/Admin |
| `ERR-FLT-404-01` | 404 | `server_ids[]` có server không tồn tại; `group` không có server nào |
| `ERR-CON-422-01` | 422 | `action` ngoài danh sách trắng Phase 2; `params` sai; hành động 1 server nhưng có ≥ 2 server |
| `ERR-JOB-409-01` | 409 | Đã có đợt chạy `RUNNING` chứa cùng server với hành động ghi (`details.fleet_run_id`) (ĐX) |

### 3.9 `GET /api/v1/fleet-runs/{fleet_run_id}` (V)
FR: `FR-FLT-EXEC-002`. Client gọi lại mỗi 5 s tới khi `state` kết thúc (ĐX, DOC-SRS-QP-FLOW-001 §6.2 mục 9).
```json
"data": {"fleet_run_id": "FLR-20261022-090000-7d21", "action": "fix", "params": {"only": ["php"]}, "state": "STOPPED", "stage": "batch",
         "current_batch": 2, "batches": [{"n": 1, "server_ids": ["web01"], "state": "SUCCEEDED"}, {"n": 2, "server_ids": ["web02", "web03", "web04", "web05", "web06"], "state": "STOPPED"}],
         "servers": [{"server_id": "web02", "state": "FAILED", "exit_code": 2, "error_code": "ERR-CLI-423-01", "collected_at": "2026-10-22T09:06:10Z"}],
         "error": {"code": "ERR-FLT-409-01", "message": "Đợt 2 có 2/5 server lỗi (40% > 20%)"},
         "created_by": "alice", "created_at": "2026-10-22T09:00:00Z", "ended_at": "2026-10-22T09:06:12Z"}
```
`state` ∈ {`PENDING`, `DRY_RUN`, `RUNNING`, `COMPLETED`, `STOPPED`}; trạng thái server ∈ {`PENDING`, `DRY_RUN_OK`, `RUNNING`, `SUCCEEDED`, `SUCCEEDED_WITH_ISSUES`, `FAILED`, `TIMEOUT`, `SKIPPED`} (ĐX). Lỗi riêng: `ERR-CON-404-01` (`details.resource = fleet_run`, `Q-API-04`).

### 3.10 `POST /api/v1/feed-distributions` (O)
FR: `FR-FLT-FEED-001`, `BR-FLT-007`, `BR-FEED-055`, `BR-FEED-056`. Body: `{"target": {...như §3.8}, "variant": "standard"|"full"}`. Máy trung tâm chạy `feeds update` (nếu bundle quá TTL) → `feeds export --out <file> --variant <v>` → tạo đợt chạy hành động nội bộ `feeds_import_remote` (đẩy snapshot ở bước S3, chạy `feeds import <TMP>/feeds-snapshot.tar.gz --sha256 <hex> --yes --json` ở bước S5). Snapshot chỉ chứa dữ liệu công khai, không chứa dữ liệu riêng của server khác (`BR-FEED-056`). Phản hồi 202 `{fleet_run_id, snapshot: {generated_at, sha256, bytes}}`. Lỗi riêng: `ERR-FLT-403-02`, `ERR-FLT-404-01`. Lỗi từng server: `ERR-FEED-422-02`, `ERR-FEED-409-02`.

### 3.11 `GET /api/v1/users` (A)
FR: `FR-FLT-RBAC-001`. Items `{username, role: viewer|operator|admin, enabled, created_at, last_login_at}`; không bao giờ trả hash mật khẩu. Lỗi riêng: `ERR-FLT-403-02`.

### 3.12 `POST /api/v1/users` (A)
Body `{"username", "role", "password"}` (12–128 ký tự). Phản hồi 201 `{username, role, enabled: true}`; mật khẩu không xuất hiện trong phản hồi, log, audit (`BR-SEC-006`). Trùng `username` → 422 `ERR-CON-422-01` `details.constraint = duplicate` (`Q-API-04`). Đổi vai trò, khoá, xoá tài khoản chưa có endpoint trong registry (`Q-P2-01`). Lỗi riêng: `ERR-FLT-403-02`.

### 3.13 `GET /api/v1/fleet-audit-events` (V)
FR: `FR-FLT-AUD-001`, `BR-AUD-003`. Query: `from`, `to` (≤ 366 ngày), `server_id` (hoặc `central`), `action`, `actor`, `page`, `limit`. Bản ghi giữ `hash`, `prev_hash` gốc của từng nguồn; `data.integrity[]` = `{source, verified, first_broken_seq, code}` với `code = ERR-AUD-409-01` khi chuỗi của nguồn lệch.
```json
"data": {"items": [{"source": "web01", "seq": 1042, "ts": "2026-10-22T10:42:01.402Z", "actor": "fleet:alice", "action": "fix", "result": "success", "hash": "5b9e…", "prev_hash": "a3f0…"}],
         "integrity": [{"source": "web01", "verified": true, "first_broken_seq": null, "code": null}]}
```
Lỗi riêng: không.

## 4. Giao thức SSH controller → host

### 4.1 Nguyên tắc
| Nguyên tắc | Nội dung | Căn cứ |
| :--- | :--- | :--- |
| Kéo, không agent, không webhook | Máy trung tâm mở SSH, đẩy gói CLI vào thư mục tạm, chạy lệnh `--json`, thu stdout, xoá thư mục tạm; không cài dịch vụ, cron, unit trên server | `BR-FLT-001` |
| Chỉ khoá SSH, ghim khoá máy chủ | Không mật khẩu; `known_hosts` riêng mỗi server; `StrictHostKeyChecking=yes` (OpenSSH: "refuses to connect to hosts whose host key has changed") | `BR-FLT-002`, `NFR-SEC-011` |
| Toàn vẹn gói | `sha256sum -c` gói CLI trên server; hash `SHA256SUMS` phải bằng giá trị của máy trung tâm | `BR-FLT-003` |
| Lệnh cố định | Chuỗi lệnh từ xa dựng từ mẫu cố định; mọi giá trị được trích dẫn bằng `shlex.quote` và đã qua regex của [api-spec-jobs.md §2](api-spec-jobs.md); không truyền văn bản tự do (lý do, bằng chứng) qua SSH | `BR-CON-008`, `NFR-SEC-007` |
| Đồng thời | ≤ 10 kết nối SSH song song toàn máy trung tâm; 1 server chỉ 1 lệnh ghi tại 1 thời điểm (khoá `STATE_DIR/.lock` của server vẫn áp dụng) | `BR-FLT-005`, `BR-JOB-002` |

### 4.2 Lệnh `ssh` chuẩn (argv do máy trung tâm dựng, `shell=False`)
```text
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes
    -o UserKnownHostsFile=<CENTRAL_STATE>/known_hosts.d/<server_id>
    -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=4
    [-o IdentitiesOnly=yes -i <key_path>]          # chỉ khi auth.type = key
    -p <port> -- <ssh_user>@<host> <lệnh từ xa theo §4.3>
```
`ServerAliveInterval=15` × `ServerAliveCountMax=4` → ngắt phiên sau 60 s không nhận phản hồi từ server (ĐX). `ssh` trả mã thoát của lệnh từ xa, hoặc 255 khi lỗi kết nối/xác thực (`ssh(1)` EXIT STATUS).

### 4.3 Các bước của 1 lần chạy trên 1 server
| Bước | Lệnh / thao tác | Timeout | Thành công | Lỗi → trạng thái server |
| :--- | :--- | :---: | :--- | :--- |
| S0 Ghim khoá (lần đầu hoặc sau khi Admin đổi fingerprint) | Máy trung tâm: `ssh-keyscan -T 10 -p <port> <host>` ghi ra file tạm → `ssh-keygen -l -E sha256 -f <file tạm>` → so với `host_key_fingerprint`; khớp → ghi dòng khoá vào `known_hosts.d/<server_id>` (`0600`) | 10 s | Có `known_hosts` đã xác minh | Không khớp → `ERR-FLT-403-01`, không ghi file (ssh-keyscan không tự xác thực khoá nên bắt buộc so fingerprint do Admin cung cấp) |
| S1 Kết nối + điều kiện | `bash --noprofile --norc -s` nhận script kiểm qua stdin: `BASH_VERSINFO`, `command -v flock curl sha256sum tar mktemp`, `python3 -c 'import sys; print(sys.version_info[:2])'`, `id -u`, `sudo -n true` (khi `sudo-n`) | 10 s kết nối + 20 s lệnh | `prerequisites[]` đạt | ssh 255 + "Host key verification failed" → `ERR-FLT-403-01`; "Permission denied" → `ERR-FLT-401-01`; quá thời gian/không kết nối → `ERR-FLT-504-01`; thiếu điều kiện → `ERR-FLT-424-01` (chuỗi thông báo OpenSSH chưa kiểm chứng trên mọi bản OpenSSH portable — QA xác nhận) |
| S2 Thư mục tạm | `mktemp -d /tmp/qp-remote.XXXXXXXXXX`; kiểm đầu ra khớp `^/tmp/qp-remote\.[A-Za-z0-9]{10}$`; máy trung tâm ghi `TMP` vào `central.db` trước bước S3 | 10 s | `TMP` | `ERR-FLT-504-01` |
| S3 Đẩy gói | Cục bộ `tar -C <gói CLI> -cf - .` → luồng stdin của `ssh … tar -C <TMP> -xf - --no-same-owner`; gói gồm `php-quickpatch.sh`, `share/php-quickpatch/` (trừ snapshot), `SHA256SUMS`; ≤ 10 MiB (ĐX) | 120 s | File có trong `TMP` | `ERR-FLT-504-01` |
| S4 Kiểm toàn vẹn | `cd <TMP> && sha256sum -c SHA256SUMS >/dev/null && sha256sum SHA256SUMS` (cú pháp dùng được với GNU coreutils và BusyBox) ; so hash in ra với hash `SHA256SUMS` của máy trung tâm | 30 s | Khớp | Lệch → `ERR-FLT-422-03` (mã đề xuất mới), không chạy S5 |
| S5 Chạy lệnh | `cd <TMP> && [sudo -n] env QP_ACTOR=fleet:<username> QP_JOB_ID=<fleet_run_id>:<server_id> bash <TMP>/php-quickpatch.sh <argv theo danh sách trắng> --json`; stdout ≤ 20 MiB, giữ 64 KiB cuối của stderr | Theo `BR-JOB-008` (vd `fix` 3.600 s) | Mã thoát 0/1/2 + stdout là envelope hợp lệ | Quá timeout → đóng phiên SSH, mở phiên mới gửi `pkill -TERM -f <TMP>/php-quickpatch.sh` (mẫu chứa đường dẫn ngẫu nhiên nên chỉ khớp tiến trình của lần chạy này), trạng thái `TIMEOUT`, `ERR-FLT-504-01`; JSON sai hoặc major không hỗ trợ → `ERR-FLT-422-02`; khoá của server bận → envelope có `ERR-CLI-423-01` |
| S6 Thu audit | `bash <TMP>/php-quickpatch.sh audit list --from <ngày bản ghi cuối đã thu> --json` | 60 s | Bản ghi mới gộp vào audit trung tâm, giữ `hash` gốc | Lỗi → giữ kết quả S5, đánh dấu `audit_pending`, thu lại ở lần chạy sau |
| S7 Dọn dẹp | `rm -rf -- <TMP>` rồi `test ! -e <TMP>`; chạy cả khi S3–S6 lỗi | 10 s | Không còn `TMP` (`NFR-SEC-012`) | Mất kết nối → `cleanup_pending` trong `central.db`; lần kết nối kế tiếp xoá đúng đường dẫn đã ghi (không xoá theo mẫu chung) |

Biến thể phân phối snapshot (§3.10): S3 đẩy thêm `feeds-snapshot.tar.gz` (≤ 15 MB biến thể `full`) vào `TMP`; S5 chạy `feeds import`. Hành động ghi qua `sudo -n` khi `sudo_mode = sudo-n`; `sudo` đòi mật khẩu → `sudo -n` thoát khác 0 ở S1, server bị đánh dấu thiếu điều kiện `ERR-FLT-424-01`.

### 4.4 Hợp đồng dữ liệu trả về
| Thành phần | Quy định |
| :--- | :--- |
| stdout của S5 | Đúng 1 envelope `qp.<lệnh>/<major>` ([api-spec-cli-json.md §3](api-spec-cli-json.md)); máy trung tâm hỗ trợ major 1; `command.job_id` = `<fleet_run_id>:<server_id>` để đối chiếu |
| Mã thoát | 0/1/2 của CLI → `SUCCEEDED`/`SUCCEEDED_WITH_ISSUES`/`FAILED`; 255 → lỗi SSH theo bảng S1 |
| Lưu trữ | Envelope lưu nguyên văn trong `central.db` kèm `collected_at`, `server_id`, `fleet_run_id`; dùng cho #50, #51 |
| Phiên bản CLI | Máy trung tâm luôn đẩy gói của chính nó (S3) nên phiên bản CLI trên mọi server trong 1 đợt giống nhau; `STATE_DIR` của server (backup, audit, feeds) được giữ giữa các lần chạy (`FR-FLT-EXEC-001`) |

### 4.5 Sơ đồ
Trình tự đầy đủ (dry-run trên mọi server → canary → các đợt, kèm nhánh lỗi): DIAG-SEQ-QP-FLT-001 ([flows-console-fleet.md §3](../srs/flows-console-fleet.md)).

## 5. Câu hỏi mở Phase 2
| Mã | Câu hỏi | Đề xuất | Người quyết định |
| :--- | :--- | :--- | :--- |
| `Q-P2-01` | Đổi vai trò, khoá, xoá tài khoản chưa có endpoint | Bổ sung `PATCH`/`DELETE /api/v1/users/{username}` qua CR khi triển khai Phase 2 | PO |
| `Q-P2-02` | Client CI có cần Bearer trên máy trung tâm | Không ở v1; CI dùng CLI trực tiếp trên từng server (`UC-CLI-001`) | PO + kỹ sư bảo mật |
| `Q-P2-03` | Tham số scrypt N=2^17 cần 128 MiB RAM mỗi lần đăng nhập | Chấp nhận trên máy trung tâm; đo thời gian băm trên máy 2 vCPU trước triển khai | Dev + QA |

## 6. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| `docs/php-quickpatch/srs/functional-requirements.md` §13, `business-rules.md` (`BR-FLT-001..008`) | FR/BR Phase 2 | Đã đọc |
| `docs/php-quickpatch/srs/flows-console-fleet.md` §3 | DIAG-SEQ-QP-FLT-001, mã đề xuất `ERR-FLT-422-03` | Đã đọc |
| `docs/php-quickpatch/srs/data-sources-merge-risk.md` §8.2, §8.3, §8.5 (ví dụ 3) | Công thức `R` (`BR-FEED-040..042`), giá trị `R` = 60 `HIGH` của PHP 8.2.34 trong ví dụ §3.7 | Đã đọc, đối chiếu 2026-10-22 |
| `docs/php-quickpatch/api/api-spec-cli-json.md` (`qp.scan/1` trường `summary`), `html-wireframe/fleet-dashboard.html` (SCR-021) | Nguồn của `totals.kev`, `totals.critical` (`summary.kev_findings`, `summary.critical_issues`), `totals.eol`, `totals.unpatched` đếm runtime | Đã đọc, đối chiếu 2026-10-22 |
| OpenSSH `ssh_config(5)`, `ssh(1)` — https://man.openbsd.org/ssh_config, https://man.openbsd.org/ssh | `BatchMode`, `StrictHostKeyChecking`, `UserKnownHostsFile`, `ConnectTimeout`, `ServerAliveInterval`, `ServerAliveCountMax` (mặc định 3), `IdentitiesOnly`; mã thoát 255 | Kiểm chứng (WebFetch 2026-10-22, bản OpenBSD) |
| `ssh-keyscan(1)` — https://man.openbsd.org/ssh-keyscan | `-p`, `-T` (mặc định 5 s); cảnh báo "cannot verify the authenticity of the host keys it obtains" | Kiểm chứng (WebFetch 2026-10-22) |
| `ssh-keygen(1)` — https://man.openbsd.org/ssh-keygen | `-l`, `-f`, `-E` (mặc định sha256); không ghi `-f -` đọc stdin → dùng file tạm | Kiểm chứng (WebFetch 2026-10-22) |
| OWASP Password Storage Cheat Sheet | scrypt N=2^17, r=8, p=1 | Kiểm chứng (WebFetch 2026-10-22) |
| Python `hashlib.scrypt` | Chữ ký, thêm từ 3.6, `maxmem` mặc định OpenSSL 1.1.0 = 32 MiB | Kiểm chứng (WebFetch 2026-10-22) |
| GNU coreutils 9.4 `sha256sum -c`, `mktemp -d` | `sha256sum -c` thoát 0 khi khớp, 1 khi file bị sửa; `mktemp -d /tmp/qp-remote.XXXXXXXXXX` sinh `/tmp/qp-remote.` + 10 ký tự chữ-số (khớp regex S2) | Chạy thử 2026-10-22 trên môi trường soạn tài liệu |
| BusyBox `sha256sum -c` (Alpine) | Cú pháp chung không dùng `--quiet`/`--strict` (tuỳ chọn GNU) | Chưa kiểm chứng (không có BusyBox trong môi trường soạn) |
