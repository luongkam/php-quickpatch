---
id: DOC-API-QP-003
title: Thiết kế hợp đồng API — Kế hoạch nâng cấp, checklist, tương thích, miễn trừ, audit, báo cáo
version: 1.0.0
phase: API & Integration Design
domain: Security Patch Management
tags: [api-design, plan, checklist, compatibility, waiver, audit, report]
depends_on:
  - DOC-API-QP-001
  - DOC-API-QP-004
  - DOC-API-QP-005
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - FR-PLAN-STS-001
  - FR-PLAN-CHK-001
  - FR-PLAN-CHK-002
  - FR-CMPT-RES-001
  - FR-JOB-AUD-003
  - FR-RPT-ASMT-001
related_diagrams:
  - DIAG-STATE-QP-PLAN-001
  - DIAG-SEQ-QP-PLAN-001
  - DIAG-SEQ-QP-UPG-001
author: BA Agent
last_updated: 2026-10-22
---

# Kế hoạch, checklist, tương thích, audit, báo cáo — đặc tả endpoint

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: 13 endpoint (#21–#29, #41–#44 của DOC-API-QP-001 §3.1) |

## 1. Quy ước
- Quy chuẩn chung: [api-spec.md §2](api-spec.md); thao tác điều khiển đồng bộ: [api-spec.md §2.14](api-spec.md); mô hình job và dry-run: [api-spec.md §2.13](api-spec.md). "Lỗi riêng" chỉ ghi mã ngoài [api-spec.md §2.16](api-spec.md).
- Đối tượng `Plan`, `ChecklistItem`: [api-spec-cli-json.md §7](api-spec-cli-json.md). Console đọc `STATE_DIR/plans/<plan_id>/plan.json`, `items.json`, `events.jsonl` (chỉ đọc); mọi thay đổi đi qua CLI (`C-SRS-05`).
- Cờ `stale` (`BR-PLAN-006`) được console tính lại mỗi lần `GET` (so `scan_fingerprint`, `catalog_version`, KEV mới/`R` của đích tăng ≥ 20, đích chuyển `EOL`) và **không ghi** vào file; CLI ghi cờ khi chạy lệnh `plan` kế tiếp (giữ nguyên tắc `GET` không đổi trạng thái).

## 2. Kế hoạch

### 2.1 `GET /api/v1/plans`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Danh sách kế hoạch — `FR-PLAN-STS-001` |
| Query | `runtime_id`, `status` (danh sách `draft`,`approved`,`in_progress`,`completed`,`rolled_back`,`cancelled`), `stale` (boolean), `page`, `limit` |
| Sắp xếp | `updated_at` giảm dần |

```json
"data": {"items": [
  {"plan_id": "PLN-20261022-103512-9b1c", "runtime_id": "php:3f9a0c1d2e4b", "runtime_label": "PHP 8.2.34 /usr/bin/php8.2", "mode": "cross_branch",
   "target": {"branch": "8.5", "patch_version": "8.5.12"}, "status": "draft", "stale": false, "stale_reasons": [],
   "deadline": {"date": "2026-12-01", "days_left": 40, "overdue": false},
   "progress": {"total": 31, "PENDING": 24, "RUNNING": 0, "DONE": 5, "FAILED": 0, "SKIPPED": 2, "WAIVED": 0},
   "created_at": "2026-10-22T10:35:12.004Z", "updated_at": "2026-10-22T10:37:40.880Z"}
]}
```
Lỗi riêng: không.

### 2.2 `POST /api/v1/plans`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chọn đích và sinh kế hoạch (job `plan_create`, loại `read`) — `FR-PLAN-TGT-001`, `FR-PLAN-GEN-001`, `FR-CON-PLAN-001` |
| Body | `runtime_id` (bắt buộc); `target` (bắt buộc; `^[4-9]\.[0-9]$` khi runtime PHP, `^[0-9]{1,2}$` khi Node.js); `sites` (mảng `site_id` ≤ 200, mặc định mọi site dùng runtime); `reason` (`<text>` 20–500 ký tự, bắt buộc khi đích không mang nhãn `RECOMMENDED` — CLI kiểm) |
| Kiểm trước khi tạo job | `runtime_id` có trong scan gần nhất; `target` đúng regex theo `kind`; `sites[]` thuộc site của runtime |
| Phản hồi | 202 như `POST /api/v1/jobs`; `plan_id` có trong `result.result.plan.plan_id` khi job kết thúc; SCR-004 theo dõi tiến độ qua SSE (`FR-CON-PLAN-001`) |

```json
{"runtime_id": "php:3f9a0c1d2e4b", "target": "8.5", "sites": ["blog.example.com", "shop.example.com"], "reason": null}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-ASMT-404-01` | 404 | `runtime_id` không có trong scan gần nhất |
| `ERR-CON-422-01` | 422 | `target` sai regex theo loại runtime; `sites[]` có site không dùng runtime; `reason` ngoài 20–500 ký tự |

Lỗi trong kết quả job: `ERR-SCN-409-01`, `ERR-SCN-409-02`, `ERR-SCN-409-03`, `ERR-PLAN-422-01`, `ERR-PLAN-409-01`, `ERR-SCN-412-01` (ghi trên kế hoạch, chặn mục P2), `ERR-CMPT-413-01`, `ERR-CMPT-422-01`, `ERR-CMPT-424-01`, `ERR-CMPT-504-01`, `ERR-PTCH-502-01`, `ERR-FEED-503-01`, `ERR-CLI-423-01`, `ERR-CLI-424-01`. Kế hoạch `draft`/`approved` cũ của cùng runtime bị huỷ và liệt kê ở `warnings[]` (`BR-PLAN-002`).

### 2.3 `GET /api/v1/plans/{plan_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chi tiết kế hoạch: đích, thứ tự site + canary, dependency phải nâng, tiền điều kiện, kết luận tương thích, hạn duyệt — `FR-PLAN-GEN-001`, `FR-PLAN-GEN-002`, `FR-PLAN-DEP-001`, `FR-PLAN-DL-001` |
| Dữ liệu | Đối tượng `Plan` (không kèm `checklist_items[]`, xem §3.1) + `progress` như §2.1 + `allowed_actions[]` ⊂ {`approve`, `cancel`, `complete`, `close_rolled_back`, `set_canary`} tính theo DIAG-STATE-QP-PLAN-001 để JS bật/tắt nút (ĐX) + `switches[]` (lượt chuyển của kế hoạch) |

```json
"data": {"plan": {"plan_id": "PLN-20261022-103512-9b1c", "status": "draft", "stale": false, "canary_site_id": "blog.example.com", "…": "Plan"},
         "progress": {"total": 31, "DONE": 5}, "allowed_actions": ["approve", "cancel", "set_canary"], "switches": []}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` không tồn tại |

### 2.4 `PATCH /api/v1/plans/{plan_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đổi trạng thái kế hoạch hoặc đổi site canary — `FR-PLAN-STS-001`, `FR-PLAN-GEN-002`, `BR-PLAN-003`, `BR-PLAN-004`, `BR-PLAN-007` |
| Nhóm | Điều khiển đồng bộ (ĐX, [api-spec.md §2.14](api-spec.md)); CLI ghi audit (duyệt, huỷ, đổi canary thuộc `BR-AUD-001`) |
| Body | Đúng **1** trong các dạng ở bảng dưới; 0 hoặc ≥ 2 dạng → 422 `ERR-CON-422-01` |
| Phản hồi | 200: `Plan` sau cập nhật + `warnings[]` |

| Body | Lệnh CLI | Trạng thái nguồn hợp lệ | Kết quả |
| :--- | :--- | :--- | :--- |
| `{"status": "approved"}` | `plan approve` | `draft`, không `stale`, đạt `BR-PLAN-003` | `approved` |
| `{"status": "cancelled", "reason": "<text>"}` (`reason` tuỳ chọn) | `plan cancel` | `draft`, `approved`, `in_progress` khi không có job của kế hoạch `RUNNING` | `cancelled` |
| `{"status": "completed"}` | `plan complete` (ĐX) | `in_progress`, mọi mục `DONE`/`SKIPPED`/`WAIVED` | `completed` |
| `{"status": "rolled_back", "reason": "<text>"}` | `plan close` (ĐX) | `in_progress` có lượt chuyển `ROLLED_BACK` | `rolled_back` |
| `{"canary_site_id": "<site_id>"}` | `plan canary` (ĐX) | `draft` (giữ `draft`) hoặc `approved` (về `draft`, `BR-PLAN-004`); site phải thuộc `site_order` và có kết luận `PASS`/`PENDING` | `site_order` đổi, canary mới đứng đầu |

```json
{"status": "approved"}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` không tồn tại |
| `ERR-PLAN-409-02` | 409 | Chuyển trạng thái không hợp lệ với trạng thái hiện tại; huỷ khi có job của kế hoạch `RUNNING`; canary không thuộc `site_order` |
| `ERR-PLAN-410-01` | 410 | Duyệt kế hoạch `stale`; `details.stale_reasons` |
| `ERR-PLAN-412-01` | 412 | Duyệt khi chưa đạt `BR-PLAN-003` (quét trước cài chưa đủ 100% site, mục P1 `AUTO` chưa `DONE`, tiền điều kiện chưa kiểm); `details.unmet[]` |
| `ERR-PLAN-422-01` | 422 | `reason` của `rolled_back` dưới 20 ký tự |
| `ERR-CLI-403-01` | 403 | Duyệt khi tiến trình `serve` không có quyền thực thi các mục của kế hoạch (người duyệt phải có quyền thực thi, `BR-PLAN-003`) |
| `ERR-CLI-423-01` | 423 | Khoá kế hoạch đang bị giữ quá 5 s |
| `ERR-JOB-504-01` | 504 | Lệnh CLI đồng bộ quá 30 s |

## 3. Checklist

### 3.1 `GET /api/v1/plans/{plan_id}/checklist-items`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Mục checklist hiệu lực theo giai đoạn/site — `FR-PLAN-CHK-001`, `FR-SCN-CHK-001`, `FR-CON-PLAN-002` |
| Query | `phase` (danh sách `P1`..`P7`), `site_id`, `status` (danh sách), `exec_type` (danh sách `AUTO`,`SEMI`,`MANUAL`), `blocked` (boolean), `page`, `limit` (tối đa 200) |
| Sắp xếp | `phase`, vị trí site trong `site_order`, `chk_id` (mục `OVERLAY` trước mục `VERSION` cùng giai đoạn, `FR-SCN-CHK-001`) |

```json
"data": {"items": [
  {"chk_id": "CHK-PHP-010-05", "scenario_id": "SCN-PHP-010", "site_id": null, "phase": "P2", "exec_type": "SEMI",
   "action": "Cài PHP 8.5 song song, không đổi mặc định hệ thống", "done_criteria": "php8.5 -v thoát 0; update-alternatives không đổi",
   "applies_when": null, "depends_on": ["CHK-PHP-010-01"], "blocked_by": [], "status": "PENDING", "verified": true,
   "cli_action": "migrate_install", "runnable": true, "run_kind": "write", "requires_dry_run": true, "requires_retype": false,
   "job_id": null, "reason": null, "evidence": null, "updated_at": "2026-10-22T10:35:12.004Z", "updated_by": "console:root"}
]}
```
`runnable` = mục `AUTO`/`SEMI` có `cli_action`, `status` ∈ {`PENDING`, `FAILED`}, `blocked_by` rỗng, kế hoạch cho phép chạy (§3.3). Mã mục, nội dung hành động trong ví dụ là minh hoạ định dạng (danh mục thật ở DOC-SRS-QP-SCN-PHP-002 §5). Lỗi riêng: `ERR-PLAN-404-01` (404, `plan_id` không tồn tại).

### 3.2 `PATCH /api/v1/plans/{plan_id}/checklist-items/{chk_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đặt trạng thái mục kèm lý do/bằng chứng — `FR-PLAN-CHK-001`, `FR-CON-PLAN-002`, `BR-PLAN-005`, `BR-SCN-018` |
| Nhóm | Điều khiển đồng bộ: `plan item <plan_id> <chk_id> --set <start\|done\|fail\|skip\|waive> [--reason] [--evidence] --json`; CLI ghi `events.jsonl` và audit |
| Body | `status` ∈ {`RUNNING`, `DONE`, `FAILED`, `SKIPPED`, `WAIVED`}; `reason`, `evidence` theo bảng |
| Trạng thái kế hoạch cho phép | `draft`, `approved`, `in_progress`; khác → 409 `ERR-PLAN-409-02` |

| `status` gửi lên | Áp cho mục | Trường bắt buộc | Ghi chú |
| :--- | :--- | :--- | :--- |
| `RUNNING` | `MANUAL` | — | Tương ứng hành động `start` của `FR-PLAN-CHK-001`; tuỳ chọn (`Q-ST-09`) |
| `DONE` | `MANUAL` | `evidence` 10–500 ký tự đối chiếu `done_criteria` | Mục `AUTO`/`SEMI` chỉ `DONE` qua job (§3.3) → 409 `ERR-PLAN-409-02` |
| `FAILED` | `MANUAL` | `evidence` 10–500 ký tự (ĐX) | |
| `SKIPPED` | Mọi loại | `reason` 20–500 ký tự (ĐX) | Mục không thoả `applies_when` đã được CLI đặt `SKIPPED` tự động |
| `WAIVED` | Mọi loại | `reason` 20–500 ký tự | `BR-PLAN-005` |

```json
{"status": "DONE", "evidence": "Đã chạy bộ test nghiệp vụ trên staging 8.5: 214/214 test đạt, log /srv/ci/run-881.txt"}
```
Response 200: `{"plan_id", "item": ChecklistItem, "plan_status"}`.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` hoặc `chk_id` không tồn tại |
| `ERR-PLAN-409-02` | 409 | Giá trị không hợp lệ với loại mục/trạng thái mục (vd `DONE` cho mục `AUTO`, mục đã `DONE`) hoặc với trạng thái kế hoạch |
| `ERR-PLAN-422-01` | 422 | `reason` < 20 ký tự hoặc `evidence` < 10 ký tự |
| `ERR-SCN-424-01` | 424 | `RUNNING`/`DONE` khi mục phụ thuộc chưa `DONE`/`WAIVED`; `details.blocked_by[]` |
| `ERR-CLI-423-01` | 423 | Khoá kế hoạch bị giữ quá 5 s |
| `ERR-JOB-504-01` | 504 | Lệnh CLI đồng bộ quá 30 s |

### 3.3 `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chạy mục `AUTO`/`SEMI` (job `plan_run_item`) — `FR-PLAN-CHK-002`, `BR-SCN-008`, `BR-CON-005` |
| Body | `dry_run` (boolean); `confirm_dry_run_job_id`; `confirm_retype` (mục bước 1 PB-006) |
| Loại job | `write` khi `cli_action` đổi hệ thống (vd `migrate_install`, `migrate_switch`, `fix`) → bắt buộc dry-run + xác nhận; `read` khi `cli_action` chỉ đọc (vd quét tương thích P3, `migrate_healthcheck`); mục `verified=false` luôn cần dry-run + xác nhận (không chạy ở mức `AUTO`, `BR-ENV-010`) |
| Kiểm trước khi tạo job | Console đọc `items.json`: mục tồn tại; `runnable = true`; kế hoạch `approved`/`in_progress` với mục đổi hệ thống (mục P1 đọc chạy được ở `draft`); kế hoạch không `stale` với mục P5 |
| Phản hồi | 202 như `POST /api/v1/jobs`; job kết thúc cập nhật trạng thái mục (`SUCCEEDED` → `DONE`, `FAILED`/`INTERRUPTED` → `FAILED`, `CANCELLED` trước thay đổi → `PENDING`, states.md `T-CHK-05..08`) và phát sự kiện SSE `plan_item` |

```json
{"dry_run": true}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` hoặc `chk_id` không tồn tại |
| `ERR-PLAN-409-02` | 409 | Mục không có `cli_action`, là `MANUAL`, đang `RUNNING`/`DONE`/`SKIPPED`/`WAIVED`; hoặc kế hoạch ở trạng thái không cho chạy mục đổi hệ thống |
| `ERR-PLAN-410-01` | 410 | Kế hoạch `stale` và mục thuộc P5 (`BR-PLAN-006`) |

Lỗi trong kết quả job: `ERR-SCN-424-01`, `ERR-UPG-409-02`, `ERR-PLAN-410-01` (CLI kiểm lại), cùng các mã của hành động bên trong ([api-spec-jobs.md §3.2](api-spec-jobs.md)).

## 4. Tương thích

### 4.1 `GET /api/v1/plans/{plan_id}/compatibility`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Kết quả quét tương thích theo site và từng hit — `FR-CMPT-RES-001`, `FR-CMPT-CODE-001`, `FR-CMPT-COMP-001` |
| Query | `site_id`, `level` (`error`,`warning`), `rule_id`, `waived` (boolean), `page`, `limit` (phân trang áp cho `hits[]`) |
| Dữ liệu | `verdicts[]` (mọi site), `hits[]` (trang hiện tại), và các danh sách có giới hạn: `composer_blockers[]`, `npm_engine_violations[]`, `native_addons[]`, `ini_findings[]`, `extension_gaps[]`, `frameworks[]`, `loaders[]`, `skipped_files[]` (> 2 MiB, `ERR-CMPT-413-01`), `tools[]` (`tools_manifest.json`) |

```json
"data": {"plan_id": "PLN-20261022-103512-9b1c", "target_branch": "8.5",
  "verdicts": [{"site_id": "shop.example.com", "status": "FAIL", "errors": 2, "warnings": 11, "waived": 0, "pending_parts": []}],
  "hits": [{"hit_id": "H-0c4e2a9f7b11", "site_id": "shop.example.com", "file": "/var/www/shop/lib/legacy.php", "line": 88,
            "rule_id": "BC-PHP-70-03", "level": "error", "snippet": "preg_replace('/x/e', …)", "waived": false, "waiver": null}],
  "composer_blockers": [], "npm_engine_violations": [], "native_addons": [], "ini_findings": [], "extension_gaps": [],
  "frameworks": [{"name": "wordpress", "version": "6.9.5", "php_min": "7.2", "php_max": "8.5", "supports_target": true}],
  "loaders": [], "skipped_files": [], "tools": [{"name": "PHPCompatibility", "version": "10.0.0-alpha2", "sha256": "…"}]},
"meta": {"request_id": "77aa…", "page": 1, "limit": 20, "total": 13}
```
`snippet` ≤ 200 ký tự, hiển thị bằng `textContent` (`NFR-SEC-009`). Dải PHP của framework trong ví dụ là minh hoạ.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` không tồn tại |
| `ERR-CON-404-01` | 404 | `site_id` không thuộc kế hoạch (`details.resource = site`) |

### 4.2 `POST /api/v1/plans/{plan_id}/compatibility-waivers`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Miễn trừ hit mức `error` kèm lý do, tính lại kết luận site (ngoại lệ có duyệt của `BR-UPG-002`) — `FR-CMPT-RES-001` |
| Nhóm | Điều khiển đồng bộ: `plan waive <plan_id> --site <site_id> --hits <hit_id,…> --reason <text> --json` (ĐX); CLI ghi audit (`BR-AUD-001` "miễn trừ") |
| Body | `site_id` (bắt buộc); `hit_ids` (1–200 phần tử, chỉ hit mức `error` của site); `reason` (20–500 ký tự) |
| Trạng thái kế hoạch | `draft`, `approved`, `in_progress` |
| Phản hồi | 201 |

```json
{"site_id": "shop.example.com", "hit_ids": ["H-0c4e2a9f7b11"], "reason": "File lib/legacy.php không được include ở production; đã xác minh bằng grep require/include toàn bộ mã"}
```
```json
"data": {"plan_id": "PLN-20261022-103512-9b1c", "site_id": "shop.example.com", "waived": ["H-0c4e2a9f7b11"], "already_waived": [],
         "compat_verdict": {"site_id": "shop.example.com", "status": "FAIL", "errors": 1, "warnings": 11, "waived": 1, "pending_parts": []}}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-PLAN-404-01` | 404 | `plan_id` không tồn tại |
| `ERR-PLAN-409-02` | 409 | Kế hoạch `completed`/`cancelled`/`rolled_back` |
| `ERR-PLAN-422-01` | 422 | `reason` < 20 ký tự |
| `ERR-CON-422-01` | 422 | `hit_id` không thuộc site hoặc không ở mức `error` (`details.field = hit_ids`) |
| `ERR-CLI-423-01` | 423 | Khoá kế hoạch bị giữ quá 5 s |
| `ERR-JOB-504-01` | 504 | Lệnh CLI đồng bộ quá 30 s |

## 5. Audit

### 5.1 `GET /api/v1/audit-events`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Truy vấn audit chỉ đọc cho SCR-010 — `FR-JOB-AUD-003`, `BR-AUD-002` |
| Query | `from`, `to` (ngày; mặc định 30 ngày gần nhất; khoảng ≤ 366 ngày) (ĐX), `action` (danh sách), `actor`, `source` (`cli`,`console`), `job_id`, `plan_id`, `run_id`, `page`, `limit` |
| Sắp xếp | `seq` giảm dần |
| Nguồn | `STATE_DIR/audit/audit-YYYYMM.jsonl`; `serve` không root chỉ đọc audit trong `STATE_DIR` của user (spec §2.3) |
| Ràng buộc | Không có endpoint `PATCH`/`DELETE` cho audit; phương thức khác `GET` → 405 |

```json
"data": {"items": [
  {"seq": 1042, "ts": "2026-10-22T10:42:01.402Z", "actor": "console:root", "sys_user": "root", "source": "console", "action": "fix",
   "args": ["fix", "--json", "--only", "php"], "job_id": "JOB-20261022-104201-5e0b", "run_id": "20261022-104201", "plan_id": null,
   "result": "intent", "exit_code": null, "prev_hash": "a3f0…", "hash": "5b9e…"}
]}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-422-01` | 422 | `from` > `to` hoặc khoảng > 366 ngày |

### 5.2 `POST /api/v1/audit-verifications`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Kiểm chuỗi hash audit (job `audit_verify`, loại `read`) — `FR-JOB-AUD-002`, `BR-AUD-003` |
| Body | `{"from": "2026-10-01", "to": "2026-10-22"}` (cả 2 tuỳ chọn; mặc định toàn bộ) |
| Phản hồi | 202 như `POST /api/v1/jobs` |

Kết quả job (`result.result` của `qp.audit/1`): `{"verified": true, "records": 1042, "first_broken_seq": null, "files": [{"file": "audit-202610.jsonl", "records": 1042, "ok": true}]}`. Chuỗi lệch → job `FAILED` (mã thoát 2), `result.errors[]` có `ERR-AUD-409-01` kèm `first_broken_seq`. Lỗi riêng: `ERR-CON-422-01` (ngày sai định dạng, `from` > `to`).

## 6. Báo cáo

### 6.1 `POST /api/v1/reports`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Tạo báo cáo đánh giá hoặc bằng chứng (job `report`, loại `read`) — `FR-RPT-ASMT-001`, `FR-RPT-AUD-001`, `BR-RPT-001..003` |
| Body | `type` ∈ {`assess`, `evidence`}; `format` ∈ {`json`, `csv`, `md`, `html`}; `from`, `to` (bắt buộc với `evidence`, không dùng với `assess`) |
| Xử lý | Console cấp `report_id`, đường dẫn `--out STATE_DIR/reports/<report_id>.<ext>` (không ghi đè, `BR-RPT-003`) |
| Phản hồi | 202: dữ liệu như `POST /api/v1/jobs` + `report_id` |

```json
{"type": "evidence", "format": "html", "from": "2026-10-01", "to": "2026-10-22"}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-RPT-422-01` | 422 | `format` không hỗ trợ; `from` > `to`; khoảng > 366 ngày; thiếu `from`/`to` với `evidence`; có `from`/`to` với `assess` |

Lỗi trong kết quả job: `ERR-AUD-409-01` (bằng chứng có chuỗi audit lệch, vẫn xuất báo cáo kèm cảnh báo), `ERR-RPT-409-01` (file đã tồn tại — không xảy ra khi console cấp `report_id` mới), `ERR-CLI-424-01`.

### 6.2 `GET /api/v1/reports/{report_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Siêu dữ liệu và tải file báo cáo — `FR-RPT-ASMT-001`, `FR-RPT-AUD-001`, `FR-CON-AUD-001` |
| Query | `download` (boolean, mặc định `false`) |
| Phản hồi `download=false` | 200 JSON (envelope) |
| Phản hồi `download=true` | 200, thân = file; `Content-Type`: `application/json` (json), `text/csv; charset=utf-8` (csv), `text/markdown; charset=utf-8` (md), `text/html; charset=utf-8` (html); `Content-Disposition: attachment; filename="<report_id>.<ext>"`; `X-QP-SHA256: <hex>`; thêm `Content-Security-Policy: sandbox` cho HTML để trình duyệt không chạy nội dung nếu mở trực tiếp (ĐX, ngoại lệ "chỉ JSON" của `FR-CON-API-001`) |

```json
"data": {"report_id": "RPT-20261022-121004-0e3c", "type": "evidence", "format": "html", "from": "2026-10-01", "to": "2026-10-22",
         "job_id": "JOB-20261022-121004-6a90", "state": "SUCCEEDED",
         "file": {"name": "RPT-20261022-121004-0e3c.html", "bytes": 418230, "sha256": "e1d0…", "created_at": "2026-10-22T12:10:19.551Z"},
         "download_url": "/api/v1/reports/RPT-20261022-121004-0e3c?download=1"}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-404-01` | 404 | `report_id` không tồn tại (`details.resource = report`), hoặc `download=1` khi job chưa tạo xong file (`details.reason = not_ready`) |

## 7. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| `docs/php-quickpatch/srs/functional-requirements.md` §5, §6, §10, §12 | `FR-PLAN-*`, `FR-CMPT-*`, `FR-JOB-AUD-*`, `FR-RPT-*` | Đã đọc |
| `docs/php-quickpatch/srs/business-rules.md` | `BR-PLAN-001..007`, `BR-AUD-001..005`, `BR-RPT-001..003` | Đã đọc |
| `docs/php-quickpatch/srs/states.md` §3, §5, §9 | `T-PLN-*`, `T-CHK-*`, `Q-ST-06`, `Q-ST-09` | Đã đọc |
| `docs/php-quickpatch/srs/flows.md` §4, `flows-upgrade.md` §2 | Body `POST /api/v1/plans`, `PATCH …`, miễn trừ, chạy mục | Đã đọc |
| `docs/php-quickpatch/srs/version-scenarios-common.md` §3, §5.2 | Giai đoạn P1–P7, `exec_type`, `checklist_item` | Đã đọc |
