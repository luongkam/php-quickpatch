---
id: DOC-API-QP-002
title: Thiết kế hợp đồng API — Phiên, tổng quan, runtime, đánh giá, advisory, site, dự án, findings, nguồn dữ liệu
version: 1.0.2
phase: API & Integration Design
domain: Security Patch Management
tags: [api-design, session, cookie, overview, runtime, assessment, advisory, site, findings, feeds, snapshot, dry-run, static]
depends_on:
  - DOC-API-QP-001
  - DOC-API-QP-005
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-FEED-003
  - FR-CON-AUTH-003
  - FR-CON-AUTH-004
  - FR-CON-OVW-001
  - FR-CON-ASMT-001
  - FR-CON-SITE-001
  - FR-CON-FEED-002
related_diagrams:
  - DIAG-SEQ-QP-AUTH-002
  - DIAG-SEQ-QP-SCAN-001
  - DIAG-SEQ-QP-FEED-002
  - DIAG-SEQ-QP-FEED-003
author: BA Agent
last_updated: 2026-10-22
---

# Phiên, tổng quan, runtime, site, nguồn dữ liệu — đặc tả endpoint

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: 20 endpoint (#1–#20 của DOC-API-QP-001 §3.1) và 3 route tĩnh |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa ví dụ điểm rủi ro PHP 8.2.34 ở §3.1 `ranking` và §4.1 `risk` từ `R` = 78 `CRITICAL` thành `R` = 60 `HIGH` theo `BR-FEED-040` (không KEV, khớp ví dụ 3 của data-sources-merge-risk.md §8.5); thêm diễn giải thành phần điểm |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review, sửa lệch với business-rules.md 1.1.0 (§6 mục 2, 5), api-spec.md §2.4, §2.13.3 và api-spec-jobs.md §2.2 (bản 1.0.1 của file đã dùng nhãn này nên bản này là 1.0.2): (1) §2.1, §2.3 cookie đổi từ `qp_session` thành `qp_session_<port>_<iid>`, thêm `Max-Age=43200`, đăng xuất xoá đúng tên đó (`BR-AUTH-004`); (2) §6.2 `POST /api/v1/feed-snapshots` bắt buộc 2 bước dry-run → xác nhận (`BR-CON-005`): thêm query `dry_run`, `confirm_dry_run_job_id`; bước 1 tạo job `read` `feeds import … --dry-run`; bước 2 tải lại file, chỉ tạo job `write` khi SHA-256 nội dung và `force` khớp job dry-run; thêm `ERR-JOB-428-01` vào lỗi riêng; mỗi job xoá file tạm của chính nó; tách lỗi kết quả job theo job dry-run và job ghi |

## 1. Quy ước
- Quy chuẩn chung: [api-spec.md §2](api-spec.md). "Lỗi riêng" chỉ ghi mã ngoài [api-spec.md §2.16](api-spec.md).
- Endpoint đọc lấy dữ liệu từ `STATE_DIR/state/last-scan.json` (envelope `qp.scan/1`), kết quả job, `plans/`, `switches/`, `backups/` và `feeds/current/feeds.db` (mở `file:…?mode=ro`); không tạo tiến trình, trừ `GET /api/v1/feeds`. Chưa có `last-scan.json` → danh sách rỗng, `meta.scan = null`, JS hiển thị nút "Quét" (job `scan`).
- Ví dụ chỉ ghi `data`/`meta`; trường đầy đủ của đối tượng theo [api-spec-cli-json.md](api-spec-cli-json.md).

## 2. Phiên đăng nhập

### 2.1 `POST /api/v1/sessions`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đăng nhập bằng token `serve`, cấp cookie phiên và CSRF token — `FR-CON-AUTH-003`, `BR-AUTH-002..004` |
| Nhóm | Công khai (G1, G2; `Content-Type: application/json` bắt buộc; `Origin`, nếu có, phải thuộc danh sách cho phép) |
| Body | `{"token": "<chuỗi 43 ký tự base64url, regex ^[A-Za-z0-9_-]{43}$>"}`; sai định dạng được tính là 1 lần sai (401, không 422, để không phân biệt lỗi định dạng với lỗi giá trị) |
| Phản hồi | 200 + `Set-Cookie: qp_session_<port>_<iid>=<session_id>; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200` (`BR-AUTH-004`, [api-spec.md §2.4](api-spec.md)): `<port>` = cổng `serve` lắng nghe, `<iid>` = 8 ký tự hex sinh mỗi lần `serve` khởi động (`secrets.token_hex(4)`); `Max-Age` 43.200 s = thời hạn tuyệt đối 12 giờ từ lúc đăng nhập; không `Domain`, không `Secure`. Tên cookie khác nhau theo cổng và lần khởi động `serve`, nên 2 console mở qua 2 cổng cục bộ không ghi đè phiên của nhau. Body theo DIAG-SEQ-QP-AUTH-002 bước "200 {session_expires_at, csrf_token}" |

```json
{"token": "q3Zx…(43 ký tự)…"}
```
```json
"data": {"session_expires_at": "2026-10-22T22:30:00.000Z", "idle_timeout_s": 1800, "csrf_token": "Jt8m…(43 ký tự)…",
         "serve": {"user": "root", "is_root": true, "port": 17321}}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-AUTH-401-01` | 401 | Token sai hoặc sai định dạng; audit gộp theo phút (`BR-AUTH-003`) |
| `ERR-AUTH-429-01` | 429 | Đã sai 5 lần trong 60 s; header `Retry-After` = số giây còn lại; `details.retry_after_s` |
| `ERR-AUTH-409-01` | 409 | Đã có 5 phiên hiệu lực |
| `ERR-AUTH-403-02` | 403 | Có `Origin` nhưng không thuộc danh sách cho phép (ĐX) |

### 2.2 `GET /api/v1/sessions/current`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Thông tin phiên, quyền tiến trình `serve` để SCR-011 vô hiệu nút cần root — `FR-CON-AUTH-004`, `FR-CON-SAFE-001`, `BR-CON-010` |
| Ghi chú | Trả lại `csrf_token` của phiên cookie để JS lấy lại sau khi tải lại trang (token chỉ giữ trong bộ nhớ, `BR-AUTH-005`); trang khác nguồn không đọc được phản hồi vì không có CORS, và DNS rebinding bị chặn ở G1 (ĐX) |

```json
"data": {"auth": "cookie", "session_ref": "7f3a91c2", "created_at": "2026-10-22T10:30:00.000Z",
         "idle_expires_at": "2026-10-22T11:12:44.120Z", "session_expires_at": "2026-10-22T22:30:00.000Z",
         "csrf_token": "Jt8m…", "serve": {"user": "root", "is_root": true, "port": 17321, "allowed_local_ports": [17321]},
         "capabilities": {"system_actions": true, "disabled_actions": []}, "phase": 1}
```
Khi `serve` không root: `capabilities.system_actions = false`, `disabled_actions = [{"action": "migrate_install", "reason_code": "ERR-CLI-403-01"}, …]` theo cột "Cần root" của [api-spec-jobs.md §2](api-spec-jobs.md). Bearer: `auth = "bearer"`, `csrf_token = null`, `session_ref = "bearer"`. Lỗi riêng: không.

### 2.3 `DELETE /api/v1/sessions/current`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đăng xuất — `FR-CON-AUTH-004` |
| Body | Không có (không cần `Content-Type`); vẫn kiểm `X-QP-CSRF`, `Origin` (G4) |
| Phản hồi | 200 `{"logged_out": true}` + `Set-Cookie: qp_session_<port>_<iid>=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/` (đúng tên cookie của phiên `serve` hiện tại, `BR-AUTH-004`; không đụng cookie của console khác); với Bearer: 200 `{"logged_out": false}` (Bearer không có phiên) |

Lỗi riêng: không.

## 3. Tổng quan và môi trường

### 3.1 `GET /api/v1/overview`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Số liệu SCR-002 — `FR-CON-OVW-001`, `FR-ASMT-RANK-001`, `FR-PLAN-DL-001`, `FR-FEED-AGE-001` |
| Nguồn | `last-scan.json`, `plans/*/plan.json`, `switches/index.tsv`, `feeds/current/manifest.json`, `feeds/state/sync-status.json`, `jobs/` |
| Chỉ tiêu | P95 ≤ 500 ms (`NFR-PERF-001`) |

```json
"data": {
  "scan": {"generated_at": "2026-10-22T10:05:11.402Z", "scan_age_h": 0, "rescan_suggested": false},
  "counts": {"runtimes": 4, "ok": 2, "ok_backport": 0, "vulnerable": 1, "eol": 1, "unknown": 0, "eol_within_90d": 1,
             "kev_findings": 0, "critical_findings": 2, "vulnerable_packages": 3, "malware_packages": 0, "webshell_findings": 0},
  "ranking": [{"object_ref": "runtime:php:3f9a0c1d2e4b", "label": "PHP 8.2.34 /usr/bin/php8.2", "R": 60, "level": "HIGH", "reason_codes": ["CVSS_GE_9", "EOL_LE_90D"]}],
  "plan_deadlines": [{"runtime_id": "php:3f9a0c1d2e4b", "deadline": "2026-12-01", "days_left": 40, "plan_id": null, "plan_status": null}],
  "feeds": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "freshness": "AGING", "data_age_h": 12, "failed_sources": [{"src_id": "SRC-008", "last_error": "ERR-FEED-503-01"}]},
  "alerts": [],
  "jobs": {"running": 0, "queued": 0}
}
```
- `scan.rescan_suggested = true` khi `scan_age_h` > 24 (`FR-CON-OVW-001`).
- `ranking` gồm tối đa 10 đối tượng có `R` cao nhất (ĐX), thứ tự `BR-ASMT-004`.
- `alerts[].kind` ∈ {`HC_FAILED_KEPT`, `ROLLBACK_FAILED`, `WEBSHELL`, `DATA_STALE`, `DATA_EXPIRED`, `DRIFT`}; mỗi phần tử `{kind, object_ref, code, message}` với `code` lần lượt `ERR-HC-500-01`, `ERR-HC-500-02`, `null`, `ERR-FEED-412-01`, `ERR-SCN-503-01`, `ERR-SCAN-409-01`.

Lỗi riêng: không.

### 3.2 `GET /api/v1/environment`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Môi trường, playbook, giới hạn thao tác — `FR-SCAN-ENV-001`, `FR-SCN-ENV-001` |
| Nguồn | `last-scan.json` → `result.environment` |

```json
"data": {"os_id": "ubuntu", "os_version": "24.04", "pkg_mgr": "apt", "panel": "none", "has_systemd": true, "has_docker": true,
         "in_container": false, "is_root": true, "web_servers": ["nginx"],
         "playbooks": [{"pb_id": "PB-001", "layer": "provider"}, {"pb_id": "PB-003", "layer": "binding"}],
         "restrictions": []}
```
`restrictions[]` = `{code, message}`, vd `ERR-ENV-422-01` (PB-000: chỉ mitigation + hướng dẫn), giới hạn "trong container" (`BR-ENV-009`), "không root: chỉ cấp dự án" (`BR-PTCH-003`). Lỗi riêng: không.

## 4. Runtime, đánh giá, advisory

### 4.1 `GET /api/v1/runtimes`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Danh sách runtime, trạng thái, kịch bản — `FR-SCAN-RT-001`, `FR-SCAN-RT-002`, `FR-SCN-LIFE-001` |
| Query | `kind` (`php`,`node`), `state` (danh sách: `ok`,`ok-backport`,`vulnerable`,`eol`,`unknown`), `lifecycle_status` (danh sách), `priority` (danh sách), `locked` (boolean), `page`, `limit` |
| Sắp xếp | `risk.R` giảm dần, rồi `runtime_id` |

```json
"data": {"items": [
  {"runtime_id": "php:3f9a0c1d2e4b", "kind": "php", "bin": "/usr/bin/php8.2", "version": "8.2.34", "branch": "8.2",
   "state": "vulnerable", "lifecycle_status": "SECURITY_ONLY", "priority": "HIGH", "eol_date": "2026-12-31", "days_to_eol": 70,
   "is_lts": null, "scenario_ids": ["SCN-PHP-010", "SCN-PHP-015"], "install_source": "package", "locked": false,
   "risk": {"R": 60, "level": "HIGH"}, "site_count": 2}
]}
```
Giá trị `risk` của ví dụ theo `BR-FEED-040`, ví dụ 3 của [data-sources-merge-risk.md §8.5](../srs/data-sources-merge-risk.md): 2 CVE critical chưa vá, `cvss_max` = 9,8, không KEV, `SECURITY_ONLY`, `d` = 70 → `R_raw` = 39,2 + 8 + 0 + 5 + 8 = 60,2 → `R` = 60, `HIGH`. Lỗi riêng: không.

### 4.2 `GET /api/v1/runtimes/{runtime_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chi tiết runtime, kịch bản, cờ khoá tự động hoá — `FR-SCN-CLS-001`, `FR-SCN-CLS-002`, `FR-SCN-LOCK-001` |
| Dữ liệu | Toàn bộ đối tượng `runtime` ([api-spec-cli-json.md §5.1](api-spec-cli-json.md)) + `active_plan` `{plan_id, status}` + `last_assessment` `{job_id, generated_at, bundle_id, outdated}` |

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-ASMT-404-01` | 404 | `runtime_id` không có trong scan gần nhất |

### 4.3 `GET /api/v1/runtimes/{runtime_id}/assessment`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Đánh giá hiện tại + bảng so sánh cho SCR-003 — `FR-ASMT-CUR-001`, `FR-ASMT-CMP-001`, `FR-ASMT-RISK-001`, `FR-ASMT-RISK-002`, `FR-CON-ASMT-001` |
| Nguồn | `result.json` của job `assess` mới nhất cho `runtime_id` (không tự tính, DOC-SRS-QP-FLOW-001 §6.2 mục 2) |
| `meta.outdated` | `true` khi `bundle_id` của kết quả khác bundle hiện tại hoặc `scan_fingerprint` đã đổi → SCR-003 gắn nhãn "kết quả cũ" và nút "Đánh giá lại" (job `assess`) |

```json
"data": {"runtime_id": "php:3f9a0c1d2e4b", "job_id": "JOB-20261022-103020-1b77", "generated_at": "2026-10-22T10:30:41.220Z",
         "evaluated_on": "2026-10-22", "current": {"…": "qp.assess/1 result.current"}, "advisories": [], "comparison": {"rows": []}},
"meta": {"request_id": "c0ffee11aa22bb33", "outdated": false, "feed": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "freshness": "AGING", "data_age_h": 12, "stale_sources": []}}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-ASMT-404-01` | 404 | `runtime_id` không có trong scan gần nhất (`details.reason = runtime_not_found`) hoặc chưa có kết quả `assess` (`details.reason = no_assessment`) |

### 4.4 `GET /api/v1/runtimes/{runtime_id}/candidates`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Ứng viên, nhãn loại, khả năng chọn và khả năng cài — `FR-ASMT-CAND-001`, `FR-ASMT-CAND-002` |
| Nguồn | Như §4.3 |

```json
"data": {"runtime_id": "php:3f9a0c1d2e4b", "job_id": "JOB-20261022-103020-1b77", "recommended_branch": "8.5",
         "candidates": [{"version": "8.5.12", "branch": "8.5", "types": ["RECOMMENDED", "LATEST_STABLE"], "lifecycle_status": "ACTIVE",
                         "is_lts": null, "eol_date": "2029-12-31", "selectable": true, "not_selectable_reason": null,
                         "installable": "needs_repo", "install_source": "repo:ppa:ondrej/php"}]}
```
`not_selectable_reason` ∈ {`EOL`, `PRE_RELEASE`, `UNKNOWN`, `ABNORMAL_VERSION`, `EOL_WITHIN_90D`, `NO_LOADER`, `FRAMEWORK_UNSUPPORTED`, `DATA_EXPIRED`} (ĐX, mã hoá các điều kiện `BR-ASMT-002`, `BR-UPG-004`, `BR-SCN-043`, `BR-FEED-005`). Lỗi riêng: `ERR-ASMT-404-01` như §4.3.

### 4.5 `GET /api/v1/advisories`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Danh sách advisory đã chuẩn hoá — `FR-ASMT-CUR-001`, `FR-FEED-NORM-001` |
| Query | `runtime_id` (lọc advisory ảnh hưởng runtime, kèm `status`), `product` (`php`,`node`,`wordpress`), `severity` (danh sách `critical`,`high`,`medium`,`low`), `kev` (boolean), `status` (`UNPATCHED`,`FIXED_BACKPORT`,`NOT_AFFECTED`; chỉ khi có `runtime_id`), `page`, `limit` |
| Nguồn | `feeds.db` (`advisory`, `affected_range`, `kev_entry`, `min_patched`) + kết quả backport trong scan |
| Sắp xếp | `in_kev` giảm dần, `cvss` giảm dần, `published_at` giảm dần (`BR-SEC-001`) |

```json
"data": {"items": [
  {"adv_id": "CVE-2026-109618", "kind": "VULN", "product": "php", "cvss": 9.8, "severity": "critical", "in_kev": false, "kev_due": null,
   "published_at": "2026-10-21", "modified_at": "2026-10-21", "summary": "PHP uses longjmp() for out-of-memory…",
   "fixed_in": "8.2.35", "status": "UNPATCHED"}
]}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-ASMT-404-01` | 404 | `runtime_id` không có trong scan gần nhất |

### 4.6 `GET /api/v1/advisories/{adv_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chi tiết advisory, alias, điểm theo nguồn, dải ảnh hưởng — `FR-FEED-NORM-001` |
| Tra cứu | Theo `adv_id` chuẩn hoặc alias (vd GHSA) → trả bản ghi chuẩn, `data.requested_id` ghi mã đã hỏi |

```json
"data": {"adv_id": "CVE-2026-109618", "requested_id": "GHSA-w8hw-w9fx-j79w", "aliases": ["GHSA-w8hw-w9fx-j79w"], "kind": "VULN", "status": "PUBLISHED",
         "product": "php", "cvss_rep": 9.8, "severity": "critical", "in_kev": false, "kev": null,
         "affected": [{"origin": "NVD_CPE", "v_start": "8.4.0", "start_incl": true, "v_end": "8.4.27", "end_incl": false, "platform": "any"}],
         "min_patched_by_branch": [{"branch": "8.2", "min_patched": "8.2.35"}, {"branch": "8.4", "min_patched": "8.4.27"}],
         "sources": ["SRC-004", "SRC-008"], "affected_runtimes": ["php:3f9a0c1d2e4b"], "published_at": "2026-10-21", "modified_at": "2026-10-21"}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-404-01` | 404 | Không có advisory hoặc alias khớp (`details.resource = advisory`) |

## 5. Site, dự án, container, findings

### 5.1 `GET /api/v1/sites`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Bảng site của SCR-009 — `FR-SCAN-MAP-001`, `FR-SCAN-DRF-001`, `FR-CON-SITE-001` |
| Query | `runtime_id`, `pb_id`, `binding_kind`, `branch`, `compat_status` (`PASS`,`FAIL`,`PENDING`,`NONE`), `drift` (boolean), `page`, `limit` |
| Sắp xếp | `site_id` |

```json
"data": {"items": [
  {"site_id": "blog.example.com", "pb_id": "PB-003", "binding_kind": "nginx_fastcgi", "binding_ref": "/etc/nginx/sites-enabled/blog.conf:42",
   "current_branch": "8.2", "runtime_id": "php:3f9a0c1d2e4b", "owner_user": "blog", "server_names": ["blog.example.com"],
   "compat": {"plan_id": "PLN-20261022-103512-9b1c", "status": "PASS"}, "last_switch": null, "drift": null}
]}
```
Lỗi riêng: không.

### 5.2 `GET /api/v1/sites/{site_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Chi tiết site: `site_binding` đầy đủ, kết luận tương thích theo kế hoạch, 5 lượt chuyển gần nhất, cấu hình health check — `FR-CON-SITE-001`, `FR-CMPT-RES-001` |
| `site_id` trong đường dẫn | Mã hoá phần trăm (`app%3Apm2%3Aapi`, `svc%3Ashop%2Fphp`) |

```json
"data": {"site": {"site_id": "blog.example.com", "pb_id": "PB-003", "docroot": "/var/www/blog", "log_sources": ["/var/log/nginx/blog.error.log", "/var/log/php8.2-fpm.log"], "hc_mode": "full"},
         "hc_config": {"homepage": "https://blog.example.com/", "hc_urls": ["https://blog.example.com/wp-login.php"], "config_file": "/etc/php-quickpatch/sites.d/blog.example.com.conf"},
         "compat_verdicts": [{"plan_id": "PLN-20261022-103512-9b1c", "status": "PASS", "errors": 0, "warnings": 3, "waived": 0, "pending_parts": ["lint_new_bin"]}],
         "switches": [], "drift": null}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-404-01` | 404 | `site_id` không có trong scan gần nhất (`details.resource = site`) |

### 5.3 `PATCH /api/v1/sites/{site_id}`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Khai báo URL health check của site — `FR-CON-SITE-001`, `FR-UPG-HC-001`, `BR-HC-001`, `BR-HC-002` |
| Nhóm | Điều khiển đồng bộ: `migrate hc-urls <site_id> --set <url>… --json` (ĐX, [api-spec.md §2.14](api-spec.md)); ghi `sites.d/<site_id>.conf` (root: `/etc/php-quickpatch/`, không root: `~/.config/php-quickpatch/`); ghi audit "đổi hc_url" (`BR-AUD-001`) |
| Body | `{"hc_urls": [<0–10 URL>]}`; mỗi URL: scheme `http`/`https`, host thuộc `server_names` của site, không `userinfo`, không fragment, ≤ 2.048 ký tự; trang chủ luôn có, không cần khai báo (`BR-HC-001`); mảng rỗng = xoá URL khai báo |

```json
{"hc_urls": ["https://blog.example.com/wp-login.php", "https://blog.example.com/feed/"]}
```
Response 200: `data` = `hc_config` như §5.2.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-404-01` | 404 | `site_id` không tồn tại |
| `ERR-HC-422-02` | 422 | URL sai cú pháp, khác host của site, hoặc quá 10 URL |
| `ERR-CLI-423-01` | 423 | Khoá cấu hình site đang bị lượt khác giữ |
| `ERR-JOB-504-01` | 504 | Lệnh CLI đồng bộ quá 30 s |

### 5.4 `GET /api/v1/projects`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Dự án Composer/npm/WordPress/Docker — `FR-SCAN-PRJ-001` |
| Query | `kind` (danh sách `composer`,`npm`,`yarn`,`pnpm`,`wordpress`,`docker`), `site_id`, `owner`, `page`, `limit` |

```json
"data": {"items": [{"project_id": "a1b2c3d4e5f6", "dir": "/var/www/blog", "owner": "blog", "kinds": ["wordpress", "composer"], "site_id": "blog.example.com",
                    "lockfiles": ["/var/www/blog/composer.lock"], "findings": {"critical": 0, "high": 1, "medium": 2, "low": 0, "malware": 0}}]}
```
Lỗi riêng: không.

### 5.5 `GET /api/v1/containers`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Container đang chạy lúc scan — `FR-SCAN-PRJ-002` |
| Query | `compose_project`, `page`, `limit` |

```json
"data": {"items": [{"id": "4f2a91c0d3b7", "name": "shop-php-1", "image": "php:8.2-fpm", "php_version": "8.2.34", "node_version": null,
                    "compose_project": "shop", "compose_service": "php", "state": "vulnerable", "note": "mitigation mất khi container tạo lại"}]}
```
Lỗi riêng: không.

### 5.6 `GET /api/v1/dependency-findings`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Findings thư viện và WordPress core cho SCR-005 — `FR-ASMT-DEP-001`, `FR-ASMT-DEP-002`, `FR-CON-DEP-001` |
| Query | `project_id`, `ecosystem` (`Packagist`,`npm`,`WordPress`), `severity` (danh sách), `kev` (boolean), `malware` (boolean), `page`, `limit` |
| Sắp xếp | `is_malware` giảm dần, `in_kev` giảm dần, mức nghiêm trọng giảm dần, `package` |
| Nguồn | `last-scan.json` → `dependency_findings[]` + `wordpress_findings[]` (gộp thành 1 danh sách, `ecosystem = WordPress` cho core) |

```json
"data": {"items": [
  {"project_id": "a1b2c3d4e5f6", "dir": "/var/www/blog", "ecosystem": "Packagist", "package": "guzzlehttp/guzzle", "version": "6.5.8",
   "advisories": [{"adv_id": "GHSA-…", "severity": "high", "in_kev": false}], "severity": "high", "in_kev": false, "is_malware": false,
   "fixed_versions": ["7.4.5"], "suggested_action": {"action": "fix", "params": {"only": ["composer"], "path": "/var/www/blog"}}}
 ],
 "lockfile_warnings": [{"project_id": "b7c8d9e0f1a2", "lockfile": "/srv/app/yarn.lock", "message": "Chưa audit yarn.lock; chạy yarn npm audit", "suggested_command": "yarn npm audit"}],
 "osv_errors": [{"project_id": "c3d4e5f6a7b8", "code": "ERR-FEED-503-02"}]}
```
- `is_malware = true` (`MAL-*`) → `severity = critical`, khuyến nghị xoay vòng secret (`BR-SEC-004`).
- `suggested_action` là tham số sẵn cho `POST /api/v1/jobs` (dry-run trước, `FR-CON-DEP-001`); WordPress: `{"action": "fix", "params": {"only": ["wp"], "path": "<site_dir>"}}`.
- Tên package, phiên bản trong ví dụ là minh hoạ.

Lỗi riêng: không (lỗi OSV lúc scan nằm ở `data.osv_errors[]`).

### 5.7 `GET /api/v1/webshell-findings`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Dấu hiệu webshell, chỉ đọc — `FR-SCAN-WSH-001`, `BR-SEC-003` |
| Query | `project_id`, `rule`, `page`, `limit` |
| Ràng buộc | Không có endpoint xoá/sửa/cách ly file; `DELETE`/`PATCH` trên đường dẫn này → 405 |

```json
"data": {"items": [{"path": "/var/www/blog/wp-content/uploads/2026/10/x.php", "rule": "php_in_uploads", "sha256": "9b1f…", "mtime": "2026-10-20T03:11:09Z",
                    "size": 1842, "project_id": "a1b2c3d4e5f6", "site_id": "blog.example.com"}]}
```
Đường dẫn file hiển thị bằng `textContent` (`NFR-SEC-009`). Lỗi riêng: không.

## 6. Nguồn dữ liệu

### 6.1 `GET /api/v1/feeds`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Trạng thái nguồn dữ liệu cho SCR-008 — `FR-FEED-CMD-002`, `FR-CON-FEED-001` |
| Nhóm | Đọc; console chạy đồng bộ `feeds status --json` (lệnh đọc, timeout 10 s, ĐX) theo DIAG-SEQ-QP-FEED-002 |
| Dữ liệu | `data` = `result` của `qp.feeds.status/1` ([api-spec-cli-json.md §10](api-spec-cli-json.md)) + `cli_exit_code`; mã thoát 1 (`STALE`) và 2 (`EXPIRED`/không có bundle) vẫn trả HTTP 200 vì đó là trạng thái dữ liệu, không phải lỗi API |

```json
"data": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "freshness": "AGING", "data_age_h": 12, "sources": [{"src_id": "SRC-006", "name": "CISA KEV", "status": "OK", "age_h": 0, "ttl_h": 6, "records": 1754, "last_error": null, "data_origin": "PRIMARY"}],
         "schedule": {"type": "systemd", "interval_h": 6, "next_run": "2026-10-22T12:17:00Z"}, "snapshot": {"packaged_generated_at": "2026-10-20T06:00:00Z", "sha256_ok": true},
         "cli_exit_code": 0, "running_sync_job_id": null}
```
| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-JOB-504-01` | 504 | `feeds status --json` quá 10 s (`details.sync = true`) |

### 6.2 `POST /api/v1/feed-snapshots`
| Mục | Nội dung |
| :--- | :--- |
| Mục đích / FR | Tải lên snapshot cho máy chủ không ra Internet theo 2 bước dry-run → xác nhận, tạo job `feeds_import` — `FR-CON-FEED-002`, `FR-FEED-SNAP-003`, `BR-FEED-055`, `BR-CON-005` |
| Header | `Content-Type: application/gzip` (ngoại lệ `Content-Type` duy nhất, [api-spec.md §2.8](api-spec.md) mục 5, `BR-CON-004` ngoại lệ 2; ngoại lệ này không miễn dry-run); `Content-Length` ≤ 20.971.520; `X-QP-Snapshot-SHA256: <64 hex>`; `X-QP-CSRF`; `Origin` |
| Query | `dry_run` (boolean, mặc định `false`); `confirm_dry_run_job_id` (regex `^JOB-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$`, bắt buộc khi `dry_run=false`, không gửi cùng `dry_run=true`); `force` (boolean, mặc định `false`): cho nhập snapshot cũ hơn bundle hiện tại. Thân là nhị phân nên các cờ đặt ở query ([api-spec-jobs.md §2](api-spec-jobs.md) dòng #6) |
| Body | Nội dung nhị phân của `feeds-snapshot-*.tar.gz`; bước 2 tải lại toàn bộ file, không dùng lại file của bước 1 |
| Nhận file (cả 2 bước) | Console ghi luồng vào `STATE_DIR/work/upload-<job_id>.tar.gz` (quyền `0600`), vừa ghi vừa tính SHA-256; kiểm 2 byte đầu `1f 8b` (gzip); SHA-256 nội dung khác header hoặc không phải gzip → xoá file, 422 `ERR-FEED-422-02`, không tạo job |
| Bước 1 — `dry_run=true` | Tạo job `read` (`BR-JOB-003`) `feeds import <file> --sha256 <hex> --yes --json --dry-run [--force]`: CLI kiểm SHA-256, `SHA256SUMS`, tar, schema, `generated_at`, so với `current` (DOC-SRS-QP-FEED-003 §4.3, §6.2); không lấy `feeds/.lock`, không thay `current/` (`FR-CLI-SAFE-001`). `params` chuẩn hoá lưu trong job = `{"force", "sha256"}`. SCR-008 mở SCR-011 và đọc `GET /api/v1/jobs/{dry_job_id}` → `result.preview` |
| Bước 2 — `confirm_dry_run_job_id` | `dry_run=false` mà thiếu `confirm_dry_run_job_id` → 428 `ERR-JOB-428-01` (`details.constraint = missing`) ngay khi đọc xong dòng request và header, không đọc thân, không ghi file, đóng kết nối (ĐX). Có `confirm_dry_run_job_id` → nhận file như trên, rồi qua cổng D (điều kiện (a)–(f) của [api-spec.md §2.13.3](api-spec.md)): job dry-run tồn tại, cùng `action` `feeds_import`, cùng phiên (hoặc cùng Bearer), tạo ≤ 15 phút trước, trạng thái đạt điều kiện (e), `bundle_id` không đổi; SHA-256 nội dung nhận lần này và giá trị `force` phải bằng `params` của job dry-run. Không đạt → xoá file vừa nhận, không tạo job, 428 `ERR-JOB-428-01`. Đạt → job `write` `feeds import <file> --sha256 <hex> --yes --json [--force]` (CLI kiểm lại toàn bộ theo DOC-SRS-QP-FEED-003 §4.3) |
| File tạm | Mỗi job (dry-run và ghi) xoá file tạm của chính nó khi job chuyển sang trạng thái kết thúc bất kỳ, kể cả khi lỗi hoặc bị huỷ; job `INTERRUPTED` được dọn file khi `serve` đối soát lúc khởi động (`BR-JOB-005`, ĐX) |
| Thời gian nhận | Mỗi lần đọc socket chờ ≤ 30 s (`BR-CON-009`); tổng thời gian nhận ≤ 600 s mỗi bước (ĐX: 20 MiB qua tunnel 1 Mbit/s cần khoảng 168 s) |
| Phản hồi | 202 như `POST /api/v1/jobs` ([api-spec.md §2.13.1](api-spec.md)): bước 1 `kind = read`, `dry_run = true`; bước 2 `kind = write`, `dry_run = false` |

```json
"data": {"job_id": "JOB-20261022-140210-7c3e", "state": "QUEUED", "kind": "read", "dry_run": true,
         "links": {"self": "/api/v1/jobs/JOB-20261022-140210-7c3e", "events": "/api/v1/jobs/JOB-20261022-140210-7c3e/events", "log": "/api/v1/jobs/JOB-20261022-140210-7c3e/log"}}
```
Bước 2 gọi `POST /api/v1/feed-snapshots?confirm_dry_run_job_id=JOB-20261022-140210-7c3e` với cùng file, cùng `X-QP-Snapshot-SHA256`, cùng `force`; phản hồi cùng dạng với `kind = "write"`, `dry_run = false`.

| Lỗi riêng | HTTP | Điều kiện |
| :--- | :---: | :--- |
| `ERR-CON-413-01` | 413 | `Content-Length` > 20.971.520 hoặc thiếu `Content-Length` |
| `ERR-CON-415-01` | 415 | `Content-Type` khác `application/gzip` |
| `ERR-CON-422-01` | 422 | Thiếu `X-QP-Snapshot-SHA256` hoặc không đúng 64 ký tự hex; `confirm_dry_run_job_id` sai định dạng; gửi `confirm_dry_run_job_id` cùng `dry_run=true` (ĐX) |
| `ERR-FEED-422-02` | 422 | SHA-256 nội dung nhận khác giá trị header, hoặc không phải gzip |
| `ERR-JOB-428-01` | 428 | Bước 2 không đạt cổng D: thiếu `confirm_dry_run_job_id` hoặc job dry-run không tồn tại (`missing`); job không phải `feeds_import` (`action_mismatch`); SHA-256 nội dung nhận hoặc `force` khác job dry-run (`params_mismatch`); khác phiên (`other_session`); quá 15 phút (`expired`); job dry-run chưa đạt trạng thái (`not_succeeded`); `bundle_id` đã đổi (`fingerprint_changed`) — `BR-CON-005` |
| `ERR-FEED-507-01` | 507 | Không ghi được file tạm do thiếu dung lượng (dưới 100 MB trống) |

Lỗi trong kết quả job — cả job dry-run và job ghi: `ERR-FEED-422-02` (SHA256SUMS, tar có mục bị cấm, giải nén > 50 MB), `ERR-FEED-409-02` (cũ hơn bundle hiện tại, không `force`), `ERR-FEED-424-01`; chỉ job ghi: `ERR-FEED-423-01` (job dry-run không lấy `feeds/.lock`), `ERR-AUD-500-01`.

## 7. Route ngoài API
| Route | Nội dung | Header riêng | Lỗi |
| :--- | :--- | :--- | :--- |
| `GET /` | Khung ứng dụng HTML (tải JS, đọc fragment `#t=`, gọi `POST /api/v1/sessions`, rồi `history.replaceState`, `BR-AUTH-006`) | CSP §2.4; `Cache-Control: no-cache` + `ETag` (ĐX) | G1 (`ERR-CON-400-01`, `ERR-CON-421-01`) |
| `GET /login` | Trang SCR-001 (ô nhập token khi không có fragment) | Như trên | Như trên |
| `GET /static/{file}` | Chỉ tên file có trong bảng ánh xạ cố định đóng gói cùng console (vd `app.js`, `app.css`, `i18n-vi.json`, `i18n-en.json`); không ghép đường dẫn từ URL, không liệt kê thư mục; tổng ≤ 500 KB chưa nén (`NFR-PERF-007`) | `Content-Type` theo bảng; `Content-Encoding: gzip` khi có `Accept-Encoding: gzip`; `ETag`, `If-None-Match` → 304 (ĐX) | Không có trong bảng → 404 `ERR-CON-404-01` (envelope JSON) |

Không có script/style inline; JS chỉ gọi `connect-src 'self'` (`BR-CON-007`). 4 route công khai (`GET /`, `GET /login`, `GET /static/*`, `POST /api/v1/sessions`) là ngoại lệ duy nhất của `NFR-SEC-003`.

## 8. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| `docs/php-quickpatch/srs/functional-requirements.md` §2–§4, §9 | Trường dữ liệu `FR-SCAN-*`, `FR-ASMT-*`, `FR-CON-*` | Đã đọc |
| `docs/php-quickpatch/srs/flows-console-fleet.md` §2, `flows.md` §2–§3 | Trình tự đăng nhập, đồng bộ, nhập snapshot, scan/assess | Đã đọc |
| `docs/php-quickpatch/srs/data-sources-cache-cli.md` §3, §4.3, §6.4 | Bảng `advisories.tsv`/`affected.tsv`, kiểm toàn vẹn snapshot, `feeds status` | Đã đọc |
| `docs/php-quickpatch/srs/data-sources-merge-risk.md` §8.2, §8.3, §8.5 | Công thức `R` (`BR-FEED-040..042`), giá trị ví dụ `risk`/`ranking` của PHP 8.2.34 | Đã đọc, đối chiếu 2026-10-22 |
| `docs/php-quickpatch/srs/environment-playbooks.md` §4.2, `environment-playbooks-healthcheck.md` §2–§3 | `site_binding`, `hc_urls`, `sites.d/<site_id>.conf` | Đã đọc |
| `docs/php-quickpatch/srs/business-rules.md` 1.1.0 §4.7, §4.8, §6 mục 2, 5 | `BR-AUTH-004` (tên cookie, `Max-Age`), `BR-CON-005` (dry-run bắt buộc cho `feeds_import`, so SHA-256 và `force`) | Đã đọc, đối chiếu 2026-10-22 |
| `docs/php-quickpatch/api/api-spec.md` §2.4, §2.13.3; `api-spec-jobs.md` §2 dòng #6, §2.2 | Header `Set-Cookie`; cổng D, `details.constraint`, giao thức 2 bước của `feeds_import`; argv và query của `feeds_import` | Đã đọc, đối chiếu 2026-10-22 |
| `docs/php-quickpatch/srs/data-sources-cache-cli.md` §6.2 | `feeds import --dry-run`: không lấy `feeds/.lock`, không đổi `current` | Đã đọc, đối chiếu 2026-10-22 |
| WHATWG Fetch Standard | `Content-Type` CORS-safelisted (cơ sở ngoại lệ `application/gzip`) | Kiểm chứng (WebFetch 2026-10-22) |
