---
id: DOC-API-QP-004
title: Thiết kế hợp đồng API — Job, danh sách trắng hành động, log, SSE, backup manifest, lượt chuyển site, rollback
version: 1.0.1
phase: API & Integration Design
domain: Security Patch Management
tags: [api-design, job, whitelist, sse, event-stream, cancel, rollback, backup-manifest, switch]
depends_on:
  - DOC-API-QP-001
  - DOC-API-QP-005
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - FR-JOB-RUN-001
  - FR-JOB-LOG-002
  - FR-CON-SAFE-003
  - BR-CON-005
  - BR-CON-008
  - BR-JOB-007
  - BR-JOB-008
related_diagrams:
  - DIAG-STATE-QP-JOB-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-SEQ-QP-UPG-002
  - DIAG-SEQ-QP-UPG-003
author: BA Agent
last_updated: 2026-10-22
---

# Job, SSE, rollback — đặc tả endpoint

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: lược đồ `params` của 16 hành động danh sách trắng, 5 endpoint job, luồng SSE, 5 endpoint backup/lượt chuyển/rollback |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review, đồng bộ spec.md §3.3.4 (`CR-SRS-10`), business-rules.md 1.0.1 (§6 mục 2, 7) và error-matrix.md 1.0.1: (1) #6 `feeds_import` dry-run "Bắt buộc", argv thêm `[--dry-run]`, thêm §2.2 luồng 2 bước so SHA-256 và `force` (`BR-CON-005`); (2) timeout #8 `plan_create`, #11 `migrate_switch` theo công thức động của `BR-JOB-008`, #9 theo hành động bên trong, ví dụ `timeout_s` 1.200 → 1.250, thêm §2.3 xử lý khi hết timeout; (3) thêm #17 `feeds_verify`; (4) bỏ đoạn "Chênh lệch với spec §3.3.4"; (5) bỏ nhãn "mã đề xuất mới" của `ERR-UPG-409-03`, `ERR-JOB-429-02`, liên kết error-matrix.md |

## 1. Quy ước
- Quy chuẩn chung (envelope, header, cổng G1–G5/J/D, mã lỗi dùng chung, giới hạn, timeout): [api-spec.md §2](api-spec.md). Bảng "Lỗi riêng" chỉ ghi mã ngoài [api-spec.md §2.16](api-spec.md); "Lỗi trong kết quả job" là mã CLI trả trong `result.errors[]` khi job đã được tạo (HTTP của `GET /api/v1/jobs/{job_id}` vẫn 200). Định nghĩa chuẩn của mọi mã `ERR-*` (HTTP, localization key, thông điệp, mức độ): [error-matrix.md](../srs/error-matrix.md).
- Ví dụ chỉ ghi phần `data` (và `meta` khi có ý nghĩa); `success`, `error`, `timestamp` theo envelope chuẩn.

## 2. Danh sách trắng hành động và lược đồ `params` (`BR-CON-008`, `FR-CON-SAFE-003`)
Console chỉ dựng argv từ bảng dưới; đường dẫn script tuyệt đối xác định lúc `serve` khởi động; mọi giá trị là 1 phần tử argv, không qua shell; giá trị bắt đầu bằng `-` bị từ chối (422 `ERR-CON-422-01`). Biến môi trường tiến trình con chỉ gồm danh sách của `BR-CON-008` 1.0.1 ([spec.md §3.3.4](../srs/spec.md), mục "Biến môi trường tiến trình con"); console không nhận biến nào từ request.

| # | `action` | Endpoint tạo | `params` (kiểu, ràng buộc) | argv | Loại | Dry-run | Xác nhận kép | Cần root (`serve`) | Timeout (s) | `object_key` |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| 1 | `scan` | `POST /api/v1/jobs` | `only`: mảng enum {`php`,`node`,`composer`,`npm`,`wp`,`docker`,`webshell`,`sites`}, 1–8 phần tử, mặc định tất cả; `offline`: boolean | `scan --json [--only <list>] [--offline]` | read | — | — | Không | 1.800 | `host` |
| 2 | `assess` | `POST /api/v1/jobs` | `runtime_id` (bắt buộc) | `assess --runtime-id <id> --candidates --json` | read | — | — | Không | 1.800 | `runtime_id` |
| 3 | `fix` | `POST /api/v1/jobs` | `only` như #1 (bỏ `sites`); `path`: chuỗi bằng 1 `projects[].dir` của scan gần nhất; `no_restart`, `no_memlimit`: boolean | `fix --json [--only <list>] [--path <dir>] [--no-restart] [--no-memlimit] [--dry-run]` | write | Bắt buộc | — | Không bắt buộc (không root: chỉ cấp dự án, `BR-CLI-005`) | 3.600 | `host` |
| 4 | `rollback_run` | `POST /api/v1/rollbacks` (`kind=run`) | `run_id` (bắt buộc) | `rollback <run_id> --json [--dry-run]` | write | Bắt buộc | — | Theo thay đổi của lượt | 600 | `run_id` |
| 5 | `feeds_update` | `POST /api/v1/jobs` | `sources`: mảng `src_id`, 1–17 phần tử; `force`: boolean | `feeds update --json [--source <list>] [--force]` | data | — | — | Không | 960 | `host` |
| 6 | `feeds_import` | Chỉ `POST /api/v1/feed-snapshots` | File tải lên (thân `application/gzip`) + header `X-QP-Snapshot-SHA256` → `sha256` (64 hex thường); query: `force` (boolean, mặc định `false`), `dry_run` (boolean, mặc định `false`), `confirm_dry_run_job_id` (bắt buộc khi `dry_run=false`) | `feeds import <STATE_DIR/work/upload-<job_id>.tar.gz> --sha256 <hex> --yes --json [--dry-run] [--force]` | write | Bắt buộc (§2.2) | — | Không | 600 | `host` |
| 7 | `feeds_schedule` | `POST /api/v1/jobs` | `op`: enum {`install`,`remove`}; `interval_hours`: enum {1,2,3,4,6,8,12,24}, chỉ với `install`, mặc định 6 | `feeds schedule install --interval-hours <N> --yes --json [--dry-run]` \| `feeds schedule remove --yes --json [--dry-run]` | write | Bắt buộc | — | Không (không root: crontab của user) | 600 | `host` |
| 8 | `plan_create` | `POST /api/v1/plans` (hoặc `POST /api/v1/jobs`) | `runtime_id`, `target` (nhánh PHP `^[4-9]\.[0-9]$` hoặc dòng Node.js `^[0-9]{1,2}$` theo `kind` của runtime), `sites`: mảng `site_id` ≤ 200, `reason`: `<text>` | `plan create --runtime-id <id> --target <x> [--sites <list>] [--reason <text>] --json` | read | — | — | Không | 600 + 1.800 × số site quét tương thích (`BR-JOB-008`, `BR-CMPT-005`); vd 1 site → 2.400, 10 site → 18.600 | `runtime_id` |
| 9 | `plan_run_item` | `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs` | `plan_id`, `chk_id` (từ đường dẫn) | `plan run <plan_id> <chk_id> --yes --json [--dry-run]` | read hoặc write theo `cli_action` của mục | Bắt buộc khi mục `SEMI` hoặc đổi hệ thống | Mục bước 1 PB-006 (gõ nhánh PHP hiện tại) | Theo mục | Bằng timeout của hành động trong `cli_action` của mục, tính theo `BR-JOB-008` (vd mục chuyển site → công thức #11) (ĐX: `BR-JOB-008` chưa nêu riêng `plan run`) | `plan_id`+`chk_id` |
| 10 | `migrate_install` | `POST /api/v1/jobs` | `runtime`: enum {`php`,`node`}; `target` theo regex nhánh/dòng | `migrate install --runtime <r> --target <x> --yes --json [--dry-run]` | write | Bắt buộc | — | Có | 3.600 | `runtime`+`target` |
| 11 | `migrate_switch` | `POST /api/v1/jobs` | `site_id`, `target`, `plan_id` (bắt buộc cả 3); `no_auto_rollback`: boolean | `migrate switch <site_id> --target <x> --plan <plan_id> --yes --json [--dry-run] [--no-auto-rollback]` | write | Bắt buộc | Khi `no_auto_rollback=true` (gõ `site_id`) | Có, trừ PB-016/PB-018 của chính user | 600 + `hc.baseline_rounds` × `hc.baseline_interval_s` + `hc.window_s` (hoặc `hc.skip_window_s` khi `hc_mode=skip`) (`BR-JOB-008`); mặc định 600 + 5 × 10 + 600 = 1.250, tối đa 600 + 10 × 60 + 3.600 = 4.800 | `site_id` |
| 12 | `migrate_healthcheck` | `POST /api/v1/jobs` | `site_id` | `migrate healthcheck <site_id> --baseline-only --json` | read | — | — | Không | 600 | `site_id` |
| 13 | `migrate_rollback` | `POST /api/v1/rollbacks` (`kind=site`) | `site_id` (bắt buộc), `run_id`, `purge_pool`: boolean | `migrate rollback <site_id> [<run_id>] --yes --json [--dry-run] [--purge-pool]` | write | Bắt buộc | — | Có, trừ PB-016/PB-018 của chính user | 300 | `site_id` |
| 14 | `migrate_remove_old` | `POST /api/v1/jobs` | `runtime_id` | `migrate remove-old --runtime-id <id> --yes --json [--dry-run]` | write | Bắt buộc | Có (gõ `runtime_id`) | Có | 600 | `runtime_id` |
| 15 | `report` | `POST /api/v1/reports` | `type`: enum {`assess`,`evidence`}; `format`: enum {`json`,`csv`,`md`,`html`}; `from`, `to`: ngày | `report <type> --format <f> --out STATE_DIR/reports/<report_id>.<ext> [--from <d>] [--to <d>] --json` | read | — | — | Không | 600 | — |
| 16 | `audit_verify` | `POST /api/v1/audit-verifications` | `from`, `to`: ngày | `audit verify --json [--from <d>] [--to <d>]` | read | — | — | Không (audit của root cần root) | 600 | `host` |
| 17 | `feeds_verify` | `POST /api/v1/jobs` | Không có (`params` = `{}`; không nhận `snapshot` từ console) | `feeds verify --json` | read | — | — | Không | 600 | `host` |

### 2.1 Đồng bộ với spec §3.3.4
- Bảng trên đồng bộ với [spec.md §3.3.4](../srs/spec.md) bản 1.0.1 (`CR-SRS-10`): console chạy CLI với `stdin=DEVNULL` (không TTY) nên mọi hành động ghi kèm `--yes` (`BR-CLI-003`, thiếu → `ERR-CLI-428-01`) và mọi hành động kèm `--json` (`FR-CLI-JSON-001`); #15 đọc envelope `qp.report/1` (`FR-CLI-CMD-004`) chứa tên file, kích thước, SHA-256 (`BR-RPT-002`) của file trong `STATE_DIR/reports/` (thư mục `0700`, file `0600`, spec §2.1).
- Nhóm `control` (điều khiển đồng bộ, không tạo job, timeout 30 s) không thuộc bảng này: argv và endpoint ở [api-spec.md §2.14](api-spec.md).

### 2.2 Dry-run 2 bước của `feeds_import` (`BR-CON-005`, `FR-FEED-SNAP-003`)
| Bước | Request | Xử lý của console |
| :---: | :--- | :--- |
| 1 | `POST /api/v1/feed-snapshots?dry_run=true[&force=true]` + file + `X-QP-Snapshot-SHA256` | Ghi `STATE_DIR/work/upload-<job_id>.tar.gz` (`0600`), vừa ghi vừa tính SHA-256; lệch header hoặc không phải gzip → `ERR-FEED-422-02`, không tạo job. Khớp → job `dry_run=true` (loại `read`, `BR-JOB-003`) chạy `feeds import <file> --sha256 <hex> --yes --json --dry-run [--force]`: CLI kiểm SHA-256, `SHA256SUMS`, tar, schema, `generated_at`, 0 thay đổi `current/` (`FR-CLI-SAFE-001`) |
| 2 | Tải lại cùng file: `POST /api/v1/feed-snapshots?confirm_dry_run_job_id=<dry_job_id>[&force=true]` + `X-QP-Snapshot-SHA256` | Nhận đủ file và tính SHA-256 như bước 1, rồi qua cổng D ([api-spec.md §2.13.3](api-spec.md)). `params` chuẩn hoá của `feeds_import` = `{"force", "sha256"}`, nên job `write` chỉ được tạo khi SHA-256 nội dung nhận ở bước 2 và giá trị `force` bằng giá trị của job dry-run; lệch → xoá file tạm, không tạo job, 428 `ERR-JOB-428-01` với `details.constraint = params_mismatch`. Các điều kiện còn lại của cổng D giữ nguyên (cùng phiên, ≤ 15 phút, `bundle_id` không đổi) |

- File tạm của mỗi job (dry-run và job thật) bị xoá khi job đó kết thúc, kể cả khi lỗi; bước 2 không dùng lại file của bước 1.
- Header, giới hạn 20 MiB, thời gian nhận và lỗi riêng của endpoint: [api-spec-core.md §6.2](api-spec-core.md).

### 2.3 Tính và xử lý timeout (`BR-JOB-008`)
- Console tính timeout lúc tạo job và trả trong `data.timeout_s`: #8 lấy số site = số phần tử `sites`, hoặc số site đang dùng runtime theo scan gần nhất khi bỏ trống `sites` (ĐX); #11 lấy `hc.*` hiệu lực của site lúc tạo job (ĐX).
- Khi hết timeout: `phase` ∈ {`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`} (vùng tới hạn của `BR-JOB-004`) → hoãn tín hiệu tới khi rời vùng tới hạn, tối đa thêm 600 s (đề xuất); `phase = HC_RUNNING` → SIGTERM, CLI dừng health check, rollback site R1–R7 với `rollback_reason = TIMEOUT` (đề xuất) rồi thoát, console chờ tối đa 300 s trước SIGKILL; `phase` khác → SIGTERM nhóm tiến trình, SIGKILL sau 10 s. Job kết thúc `FAILED` với `ERR-JOB-504-01`.

## 3. Endpoint job

### 3.1 `GET /api/v1/jobs`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Bảng job của SCR-006 — `FR-JOB-RUN-001`, `FR-CON-JOB-001` |
| Query | `state` (danh sách enum §2.13.2 api-spec), `kind` (`read`,`write`,`data`), `action` (danh sách tên §2), `dry_run` (boolean), `plan_id`, `site_id`, `runtime_id`, `from`, `to` (ngày, theo `created_at`, khoảng ≤ 366 ngày), `page`, `limit` |
| Sắp xếp | `created_at` giảm dần |
| Nguồn | `STATE_DIR/jobs/*/job.json` |

```json
"data": {"items": [
  {"job_id": "JOB-20261022-104201-5e0b", "action": "fix", "kind": "write", "dry_run": false, "state": "SUCCEEDED",
   "phase": null, "object_key": "host", "created_at": "2026-10-22T10:42:01.118Z", "started_at": "2026-10-22T10:42:01.402Z",
   "ended_at": "2026-10-22T10:43:15.930Z", "exit_code": 0, "actor": "console:root", "related": {"run_id": "20261022-104201"}}
]},
"meta": {"request_id": "1f0c9e2a7b6d4c38", "page": 1, "limit": 20, "total": 37}
```
Lỗi riêng: không.

### 3.2 `POST /api/v1/jobs`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Tạo job từ hành động trong danh sách trắng — `FR-JOB-RUN-001`, `FR-CON-SAFE-001`, `FR-CON-SAFE-003` |
| Nhóm | Tạo job; cổng G1–G5, J, D |
| Body | `action` (enum §2, trừ `feeds_import`), `params` (object theo §2), `dry_run` (boolean, mặc định `false`), `confirm_dry_run_job_id` (bắt buộc với job ghi khi `dry_run=false`), `confirm_retype` (bắt buộc khi hành động cần xác nhận kép) |
| Phản hồi | 202 + `Location: /api/v1/jobs/{job_id}` |

Request (bước xác nhận sau dry-run):
```json
{"action": "migrate_switch",
 "params": {"site_id": "blog.example.com", "target": "8.5", "plan_id": "PLN-20261022-103512-9b1c", "no_auto_rollback": false},
 "dry_run": false, "confirm_dry_run_job_id": "JOB-20261022-111312-c41a", "confirm_retype": null}
```
Response 202:
```json
"data": {"job_id": "JOB-20261022-111500-8d2f", "action": "migrate_switch", "kind": "write", "dry_run": false, "state": "QUEUED",
         "object_key": "site:blog.example.com", "timeout_s": 1250,
         "links": {"self": "/api/v1/jobs/JOB-20261022-111500-8d2f", "events": "/api/v1/jobs/JOB-20261022-111500-8d2f/events",
                   "log": "/api/v1/jobs/JOB-20261022-111500-8d2f/log"}}
```

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-422-01` | 422 | `action` ngoài danh sách trắng hoặc là `feeds_import`; `params` thiếu trường bắt buộc, có trường lạ, sai regex/enum; `path` không thuộc `projects[].dir`; `confirm_dry_run_job_id` sai định dạng |
| `ERR-CLI-403-01` | 403 | Hành động cần root khi `serve` không root (§2, cột "Cần root") |
| `ERR-JOB-409-01` | 409 | Đã có job cùng `action` + `object_key` ở `QUEUED`/`RUNNING`; `details.job_id` |
| `ERR-JOB-429-01` | 429 | Hàng đợi đã có 20 job `QUEUED` |
| `ERR-JOB-428-01` | 428 | Job ghi thiếu dry-run hợp lệ hoặc thiếu/sai `confirm_retype`; `details.constraint` theo [api-spec.md §2.13.3](api-spec.md) |

Lỗi trong kết quả job (ví dụ theo hành động): `fix` — `ERR-PTCH-*`, `ERR-AUD-500-01`, `ERR-ENV-507-01`; `migrate_switch` — `ERR-ENV-409-01`, `ERR-UPG-423-01`, `ERR-UPG-409-01`, `ERR-UPG-409-02`, [`ERR-UPG-409-03`](../srs/error-matrix.md) (site không phải site kế tiếp của `site_order`, hoặc lượt trước `ROLLED_BACK`/`HC_FAILED_KEPT` chưa được xác nhận), `ERR-SCN-424-01`, `ERR-SCN-409-02`, `ERR-SCN-412-02`, `ERR-ENV-412-01`, `ERR-ENV-500-01`, `ERR-ENV-500-02`, `ERR-ENV-502-01`, `ERR-HC-412-01..03`, `ERR-HC-424-01`, `ERR-HC-424-02`, `ERR-SCN-500-01`, `ERR-HC-500-01`, `ERR-HC-500-02`; `migrate_install` — `ERR-SCN-412-01`, `ERR-SCN-412-03`, `ERR-ENV-424-01`, `ERR-ENV-424-02`, `ERR-PTCH-502-01`; `migrate_remove_old` — `ERR-UPG-412-01`; `feeds_update` — `ERR-FEED-*`; `feeds_verify` — `ERR-FEED-422-02`; trạng thái job — `ERR-JOB-500-01`, `ERR-JOB-500-02`, `ERR-JOB-504-01`, `ERR-JOB-409-02`.

### 3.3 `GET /api/v1/jobs/{job_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Trạng thái và kết quả job; nguồn `result.preview` cho SCR-011 — `FR-JOB-RUN-001`, `FR-JOB-LOG-001` |
| Nguồn | `jobs/<job_id>/job.json`, `phase`, `result.json` |

```json
"data": {
  "job_id": "JOB-20261022-104158-3a7d", "action": "fix", "kind": "read", "dry_run": true,
  "params": {"only": ["php"]}, "argv": ["fix", "--json", "--only", "php", "--dry-run"],
  "state": "SUCCEEDED_WITH_ISSUES", "phase": null, "object_key": "host", "timeout_s": 3600,
  "actor": "console:root", "session_ref": "7f3a91c2",
  "created_at": "2026-10-22T10:41:58.007Z", "started_at": "2026-10-22T10:41:58.230Z", "ended_at": "2026-10-22T10:42:06.911Z",
  "exit_code": 1, "confirm_dry_run_job_id": null,
  "related": {"runtime_id": null, "site_id": null, "plan_id": null, "chk_id": null, "run_id": null},
  "log": {"bytes": 4182, "truncated": false, "expired": false},
  "dry_run_valid_until": "2026-10-22T10:56:58.007Z",
  "error": null,
  "result": {"schema": "qp.fix/1", "schema_version": "1.0.0", "exit_code": 1, "dry_run": true, "result": {"preview": {"…": "api-spec-cli-json §4"}, "fingerprint": {"…": "…"}}, "issues": [], "errors": [], "warnings": []}
}
```
- `session_ref` = 8 hex đầu SHA-256 của `session_id` (hoặc `"bearer"`), dùng cho điều kiện "cùng phiên" của `BR-CON-005`; không bao giờ trả `session_id` (ĐX).
- `dry_run_valid_until` chỉ có với job `dry_run=true` = `created_at` + 15 phút (`BR-CON-005`).
- `error` khác `null` khi `state` ∈ {`FAILED`, `INTERRUPTED`}: `{code: ERR-JOB-500-01|ERR-JOB-500-02|ERR-JOB-504-01|ERR-JOB-409-02, message}`.
- `result` = envelope `--json` đầy đủ của CLI ([api-spec-cli-json.md](api-spec-cli-json.md)); `null` khi chưa kết thúc hoặc job `report`.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-JOB-404-01` | 404 | `job_id` không tồn tại |

### 3.4 `GET /api/v1/jobs/{job_id}/log`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đọc `output.log` theo đoạn (xem lịch sử, lấy phần cuối trước khi mở SSE) — `FR-JOB-LOG-001` |
| Query | `offset` (≥ 0, mặc định 0), `max_bytes` (1–262.144, mặc định 65.536) |
| Quy tắc | Trả các dòng trọn vẹn trong `[offset, offset + max_bytes)`; dòng chưa kết thúc bằng `\n` chỉ trả khi job đã kết thúc (ĐX, tránh cắt ký tự UTF-8); `text` đã che bí mật (`BR-SEC-006`) |

```json
"data": {"job_id": "JOB-20261022-104201-5e0b", "offset": 0, "next_offset": 1873, "size": 4182, "eof": false, "truncated": false,
         "text": "php-quickpatch 2.0.0 mode=fix log=/var/lib/php-quickpatch/php-quickpatch.log\n  [i] Backups for this run: /var/lib/php-quickpatch/backups/20261022-104201\n…"}
```
`eof` = job đã kết thúc và `next_offset` = `size`. Để lấy phần cuối: `offset` = max(0, `log.bytes` − 65.536) từ `GET /api/v1/jobs/{job_id}`.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-JOB-404-01` | 404 | `job_id` không tồn tại |
| `ERR-JOB-410-01` | 410 | `output.log` đã bị dọn theo `BR-JOB-006` (quá 30 ngày hoặc vượt 200 MiB tổng); `job.json` còn |
| `ERR-CON-422-01` | 422 | `offset` > `size` hoặc `max_bytes` ngoài khoảng |

### 3.5 `POST /api/v1/jobs/{job_id}/cancellations`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Yêu cầu huỷ job — `FR-JOB-RUN-003`, `FR-CON-JOB-002`, `BR-JOB-004` |
| Body | `{}` hoặc `{"reason": "<0–500 ký tự>"}` |
| Phản hồi | 202 khi đã gửi tín hiệu (job `RUNNING`); 200 khi kết thúc ngay (`QUEUED` → `CANCELLED`) hoặc job đã kết thúc từ trước (gọi lặp không lỗi) |

| `state`/`phase` hiện tại | Tác động | HTTP | `data.effect` |
| :--- | :--- | :---: | :--- |
| `QUEUED` | → `CANCELLED` ngay | 200 | `CANCELLED` |
| `RUNNING`, loại `read`/`data` | SIGTERM nhóm tiến trình, SIGKILL sau 10 s | 202 | `SIGTERM_SENT` |
| `RUNNING`, `write`, `phase` = `null` | Như trên; chưa có thay đổi cần hoàn tác | 202 | `SIGTERM_SENT` |
| `RUNNING`, `write`, `phase` ∈ {`MANIFEST_WRITTEN`, `CHANGING`, `VERIFYING`} | Từ chối | 423 | — |
| `RUNNING`, `write`, `phase` = `HC_RUNNING` | Dừng health check, rollback site R1–R7, `rollback_reason = MANUAL` | 202 | `HC_ROLLBACK_STARTED` |
| `SUCCEEDED`, `SUCCEEDED_WITH_ISSUES`, `FAILED`, `CANCELLED`, `INTERRUPTED` | Không đổi | 200 | `ALREADY_ENDED` |

```json
"data": {"job_id": "JOB-20261022-111500-8d2f", "state": "RUNNING", "phase": "HC_RUNNING", "effect": "HC_ROLLBACK_STARTED"}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-JOB-404-01` | 404 | `job_id` không tồn tại |
| `ERR-JOB-423-01` | 423 | Job ghi đang ở vùng tới hạn; `details.phase` |

## 4. Luồng SSE `GET /api/v1/jobs/{job_id}/events` (`FR-JOB-LOG-002`, `BR-JOB-007`)

### 4.1 Request
| Thành phần | Quy định |
| :--- | :--- |
| Xác thực | Cookie `qp_session` (trình duyệt, vì `EventSource` không gửi được header tuỳ chỉnh; `EventSourceInit` chỉ có `withCredentials`) hoặc `Authorization: Bearer` (curl/CI) |
| Header | `Accept: text/event-stream` (không bắt buộc); `Last-Event-ID` (byte offset) khi trình duyệt tự nối lại |
| Query | `offset` (≥ 0, mặc định 0) cho lần mở đầu; `Last-Event-ID` được ưu tiên khi có cả hai |
| Cổng | G1, G2, G3; giới hạn 3 luồng/phiên và 10 luồng/console |

### 4.2 Response
- `200`, `Content-Type: text/event-stream; charset=utf-8`, `Cache-Control: no-store`, header bảo mật [api-spec.md §2.4](api-spec.md), không `Content-Length`; kết nối giữ tới khi gửi sự kiện `end`.
- Dòng đầu tiên: `retry: 2000` (trình duyệt nối lại sau 2.000 ms khi mất kết nối).
- Heartbeat: dòng comment `: hb <timestamp>` mỗi 15 s; heartbeat không làm mới mốc 30 phút của phiên (ĐX, `Q-ST-12`).
- Console đọc `output.log` mỗi 500 ms (ĐX) và đẩy dòng mới để đạt độ trễ ≤ 2 s ở P95 (`NFR-PERF-003`).
- `204 No Content`: job đã kết thúc và điểm bắt đầu (`Last-Event-ID`/`offset`) ≥ kích thước log → trình duyệt dừng tự nối lại (WHATWG HTML §9.2).

| `event` | `id` | `data` (JSON 1 dòng) | Khi phát |
| :--- | :--- | :--- | :--- |
| `log` | Byte offset ngay sau dòng cuối của sự kiện | `{"offset": <đầu>, "next_offset": <cuối>, "lines": ["…"]}` (≤ 256 dòng hoặc ≤ 64 KiB mỗi sự kiện, ĐX) | Có dòng mới trọn vẹn trong `output.log` |
| `phase` | Không có (giữ `Last-Event-ID` của sự kiện `log` trước) | `{"phase": "CHANGING", "at": "<ts>"}` | `jobs/<job_id>/phase` đổi |
| `status` | Không có | `{"state": "RUNNING", "exit_code": null}` | `state` đổi |
| `plan_item` | Không có | `{"plan_id", "chk_id", "status"}` | Job của mục checklist làm đổi trạng thái mục (`FR-PLAN-CHK-001`) |
| `end` | Không có | `{"state": "SUCCEEDED", "exit_code": 0, "ended_at": "<ts>", "result_url": "/api/v1/jobs/<job_id>"}` hoặc `{"reason": "session_expired", "code": "ERR-AUTH-401-02"}` | Job kết thúc (sau sự kiện `log` cuối) hoặc phiên hết hạn; máy chủ đóng kết nối ngay sau đó |

Dòng log được mã hoá như chuỗi JSON (escape `"`, `\`, ký tự điều khiển), đã che bí mật (`BR-SEC-006`); JS hiển thị bằng `textContent` (`NFR-SEC-009`). JS phải gọi `EventSource.close()` khi nhận `end`.

Ví dụ luồng:
```text
retry: 2000

event: status
data: {"state":"RUNNING","exit_code":null}

event: log
id: 1873
data: {"offset":0,"next_offset":1873,"lines":["php-quickpatch 2.0.0 mode=fix log=/var/lib/php-quickpatch/php-quickpatch.log","  [i] Backups for this run: /var/lib/php-quickpatch/backups/20261022-104201"]}

event: phase
data: {"phase":"CHANGING","at":"2026-10-22T10:42:09.551Z"}

: hb 2026-10-22T10:42:24.000Z

event: end
data: {"state":"SUCCEEDED","exit_code":0,"ended_at":"2026-10-22T10:43:15.930Z","result_url":"/api/v1/jobs/JOB-20261022-104201-5e0b"}
```

### 4.3 Lỗi và nối lại
| Tình huống | Phản hồi | Hành vi trình duyệt | JS console phải |
| :--- | :--- | :--- | :--- |
| `job_id` không tồn tại | 404 `ERR-JOB-404-01` (JSON) | Status ≠ 200 → "fail the connection", không nối lại; JS không đọc được body | Gọi `GET /api/v1/jobs/{job_id}` để hiển thị lý do |
| Log đã bị dọn | 410 `ERR-JOB-410-01` | Như trên | Hiển thị `result` từ `GET /api/v1/jobs/{job_id}` |
| Vượt 3 luồng/phiên hoặc 10 luồng/console | 429 [`ERR-JOB-429-02`](../srs/error-matrix.md) (`BR-JOB-007`) | Như trên | Đóng luồng không dùng, thử lại |
| Phiên hết hạn khi đang stream | Sự kiện `end` với `reason=session_expired`, đóng kết nối; lần nối lại nhận 401 | Không nối lại sau 401 | Chuyển về SCR-001 |
| Mất kết nối giữa chừng | — | Tự nối lại sau 2.000 ms với `Last-Event-ID` | Không cần xử lý; console gửi tiếp từ offset, không lặp/mất dòng |
| Console khởi động lại | Kết nối đóng; job đối soát theo `FR-JOB-RUN-004` | Tự nối lại | Không cần xử lý |

## 5. Backup manifest, lượt chuyển site, rollback

### 5.1 `GET /api/v1/backup-runs`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Danh sách lượt chạy có manifest cho SCR-007 — `FR-PTCH-RBK-001`, `FR-CON-RBK-001` |
| Query | `from`, `to` (ngày, theo `run_id`), `has_switch` (boolean), `page`, `limit` |
| Sắp xếp | `run_id` giảm dần |
| Nguồn | `STATE_DIR/backups/*/manifest`, audit (lần rollback gần nhất của `run_id`) |

```json
"data": {"items": [
  {"run_id": "20261022-104201", "created_at": "2026-10-22T10:42:01Z", "lines": 3, "actions": {"copy": 1, "note": 1, "created": 1},
   "has_switch": false, "site_ids": [], "files_bytes": 2048, "job_id": "JOB-20261022-104201-5e0b", "actor": "console:root",
   "last_rollback": null, "warnings": ["Gói nâng qua package manager không bị hạ cấp khi rollback"]}
]}
```
Lỗi riêng: không.

### 5.2 `GET /api/v1/backup-runs/{run_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Nội dung manifest để người vận hành xem trước khi rollback — `FR-PTCH-RBK-001` |

```json
"data": {"run_id": "20261022-104201", "manifest": [
  {"seq": 1, "action": "note", "args": ["apt upgraded: php8.2-cli php8.2-fpm (packages are not downgraded by rollback)"], "replay": "warn"},
  {"seq": 2, "action": "copy", "args": ["/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini", "/var/lib/php-quickpatch/backups/20261022-104201/files/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini"], "replay": "restore"}
], "replay_order": "reverse"}
```
`action` ∈ {`copy`, `created`, `untar`, `composer-install`, `npm-ci`, `note` (v0.1), `switch`, `reload`, `panel`, `link`, `systemd`, `pm2`, `compose` (DOC-SRS-QP-ENV-001 §5.3)}; `replay` mô tả việc `rollback` sẽ làm: `restore`, `remove`, `untar`, `reinstall`, `warn`, `switch_back`, `reload`, `panel_restore`.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PTCH-404-01` | 404 | Không có thư mục `backups/<run_id>` hoặc thiếu file `manifest` |

### 5.3 `GET /api/v1/switches`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Lượt chuyển site cho SCR-007/SCR-009 — `FR-UPG-SWT-001`, `FR-CON-RBK-001` |
| Query | `site_id`, `plan_id`, `status` (danh sách enum `SwitchRecord.status`), `page`, `limit` |
| Sắp xếp | `t_start` giảm dần |
| Nguồn | `switches/index.tsv`, `backups/<run_id>/switch.json` |

```json
"data": {"items": [
  {"run_id": "20261022-111500", "site_id": "blog.example.com", "plan_id": "PLN-20261022-103512-9b1c", "from_branch": "8.2", "to_branch": "8.5",
   "status": "PASSED", "t_start": "2026-10-22T11:15:00.010Z", "t_hc_end": "2026-10-22T11:25:22.001Z", "rollback_reason": null,
   "rollback_available": true, "old_runtime_present": true, "actor": "console:root"}
]}
```
Lỗi riêng: không.

### 5.4 `GET /api/v1/switches/{run_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | `switch.json` + báo cáo health check (bảng vòng × URL, ≤ 50 dòng log vi phạm) cho SCR-006 — `FR-UPG-HC-006`, `BR-HC-011` |
| Nguồn | `backups/<run_id>/switch.json`, `baseline.json`, `hc.json` |

```json
"data": {
  "switch": {"run_id": "20261022-111500", "site_id": "blog.example.com", "status": "PASSED", "from_branch": "8.2", "to_branch": "8.5", "rollback_reason": null},
  "steps": [{"step": "C9", "status": "done", "duration_ms": 640, "error_code": null}],
  "hc": {"verdict": "PASS", "mode": "full",
         "params": {"window_s": 600, "interval_s": 60, "timeout_s": 10, "p95_factor": 1.5, "p95_add_ms": 1000, "size_dev_pct": 15},
         "baseline": [{"url": "https://blog.example.com/", "code_b": 200, "size_b": 48211, "p95_ms": 182}],
         "rounds": [{"n": 1, "at": "2026-10-22T11:16:22.010Z", "urls": [{"url": "https://blog.example.com/", "code": 200, "size": 48190, "ms": 171, "ok": true}]}],
         "violations": [], "log_excerpt": []}
}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-404-01` | 404 | Không có lượt chuyển `run_id` (`details.resource = switch`) |

### 5.5 `POST /api/v1/rollbacks`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Rollback 1 lượt chạy (`rollback_run`) hoặc 1 site (`migrate_rollback`) qua dry-run + 1 xác nhận — `FR-PTCH-RBK-002`, `FR-UPG-RBK-001`, `FR-CON-RBK-001` |
| Body | `kind`: enum {`run`, `site`}; `run_id` (bắt buộc với `run`, tuỳ chọn với `site` = lượt gần nhất); `site_id` (bắt buộc với `site`); `purge_pool` (boolean, chỉ `site`); `dry_run`; `confirm_dry_run_job_id` |
| Phản hồi | 202 như `POST /api/v1/jobs` |

```json
{"kind": "site", "site_id": "blog.example.com", "run_id": "20261022-111500", "purge_pool": false, "dry_run": true}
```
Kiểm tra trước khi tạo job (console đọc `backups/`, `switches/` chỉ đọc): `run_id` không có thư mục backup → 404 `ERR-PTCH-404-01`; `site_id` không có trong scan gần nhất và không có lượt chuyển → 404 `ERR-CON-404-01`. Dry-run trả `result.preview` gồm danh sách dòng manifest sẽ phát lại ngược, cảnh báo "gói đã nâng không bị hạ cấp" và "runtime cũ đã gỡ" khi có (`FR-CON-RBK-001`).

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PTCH-404-01` | 404 | Không có lượt backup `run_id` |
| `ERR-CON-404-01` | 404 | Không có site `site_id` |

Lỗi trong kết quả job: `ERR-ENV-410-01` (runtime cũ đã gỡ), `ERR-ENV-500-03`, `ERR-ENV-502-01`, `ERR-HC-500-02`, `ERR-CLI-423-01`, `ERR-AUD-500-01`; trạng thái job `ERR-JOB-504-01` (quá 300 s với `migrate_rollback`), `ERR-JOB-409-02`.

## 6. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| `docs/php-quickpatch/srs/spec.md` §3.3.3, §3.3.4 (bản 1.0.1, `CR-SRS-10`) | Danh mục API, danh sách trắng (`feeds_import` có `[--dry-run]`, `feeds_verify`, nhóm `control`) | Đã đọc |
| `docs/php-quickpatch/srs/functional-requirements.md` §9, §10 | `FR-CON-*`, `FR-JOB-*` | Đã đọc |
| `docs/php-quickpatch/srs/business-rules.md` 1.0.1 | `BR-CON-005..010`, `BR-JOB-001..008`; §6 mục 2 (`feeds_import` dry-run bắt buộc), mục 7 (timeout động) | Đã đọc |
| `docs/php-quickpatch/srs/error-matrix.md` 1.0.1 | Định nghĩa chuẩn `ERR-JOB-429-02`, `ERR-UPG-409-03` (§5 mục 4) | Đã đọc |
| `docs/php-quickpatch/srs/data-sources-cache-cli.md` §7 | `FR-FEED-SNAP-003` (`--dry-run` chỉ kiểm, 0 thay đổi), `FR-FEED-CMD-003` (`feeds verify`) | Đã đọc |
| `docs/php-quickpatch/api/api-spec-core.md` §6.2 | Header, giới hạn, lỗi riêng của `POST /api/v1/feed-snapshots` | Đã đọc |
| `docs/php-quickpatch/srs/states.md` `T-JOB-11` | Bảng timeout bản cũ (`migrate switch` 1.200 s, `plan create` 1.800 s); chờ cập nhật theo `BR-JOB-008` 1.0.1, file này áp công thức của BR (`BR-DATA-004`) | Đã đọc, còn lệch |
| `docs/php-quickpatch/srs/states.md` §2, §4 | `T-JOB-*`, `T-SW-*`, `phase` ↔ bước | Đã đọc |
| `docs/php-quickpatch/srs/flows.md` §5, `flows-upgrade.md` §3–§4 | Thứ tự dry-run → xác nhận → SSE → huỷ; body `POST /api/v1/rollbacks` | Đã đọc |
| WHATWG HTML §9.2 Server-sent events | `retry`, `Last-Event-ID`, comment, 204, "fail the connection" | Kiểm chứng (WebFetch 2026-10-22) |
