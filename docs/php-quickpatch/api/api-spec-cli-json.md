---
id: DOC-API-QP-005
title: Thiết kế hợp đồng API — Hợp đồng JSON của CLI (--json, schema_version) cho scan, assess, plan, fix, migrate, feeds status
version: 1.0.2
phase: API & Integration Design
domain: Security Patch Management
tags: [api-design, cli, json, json-schema, schema-version, dry-run, preview, console, ci]
depends_on:
  - DOC-API-QP-001
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-FEED-003
  - FR-CLI-JSON-001
  - FR-CLI-JSON-002
  - FR-PTCH-RST-001
  - FR-PTCH-RBK-002
  - FR-UPG-ACK-001
  - BR-FEED-040
  - BR-CLI-001
  - BR-CLI-004
  - BR-FEED-059
related_diagrams:
  - DIAG-SEQ-QP-SCAN-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-SEQ-QP-UPG-002
author: BA Agent
last_updated: 2026-10-22
---

# Hợp đồng JSON của CLI (`--json`)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo: envelope chung có `schema` + `schema_version`, quy tắc tương thích, đối tượng `preview` của dry-run, schema `qp.scan/1`, `qp.assess/1`, `qp.plan/1`, `qp.fix/1`, `qp.migrate/1`, `qp.feeds.status/1` |
| 1.0.1 | 2026-10-22 | BA Agent | §7 ví dụ `upgrade_items`: thay `chk_id` không tồn tại `CHK-PHP-012-22` bằng `CHK-PHP-010-22` (mục P4 nâng dependency của `SCN-PHP-010`, khớp runtime PHP 8.2 của ví dụ); thêm ghi chú nguồn mã mục |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review, đồng bộ functional-requirements.md 1.0.1 và data-sources-merge-risk.md §8.5: (1) §5.1, §6 điểm rủi ro PHP 8.2.34 sửa từ `R` 78/`CRITICAL` thành 60/`HIGH` kèm `components` (`BR-FEED-040`, ví dụ 3); bảng `comparison` sửa 8.3.36 = 20 (`ΔR` −40, sàn Trung bình), 8.5.12 = 0 (`ΔR` −60), thêm dòng 8.2.35 = 40 (`ΔR` −20, ví dụ 4); (2) §8 `qp.fix/1` thêm `restarted[]`, `restart_failures[]` (`FR-PTCH-RST-001`, `CR-FR-05`, `ERR-PTCH-500-01`), `planned_actions[]` của `rollback --dry-run --json` (`FR-PTCH-RBK-002`, `CR-FR-02`), giá trị `docker-created` của `manifest[].action`, kèm 2 ví dụ; (3) §9 `qp.migrate/1` thêm lệnh con `ack` và `result.acknowledgement` gồm `next_allowed_sites[]` (`FR-UPG-ACK-001`, chờ `CR-FR-01`). Mọi thay đổi hình dạng chỉ thêm trường, không tăng major (`BR-CLI-001`, §3.2) |

## 1. Giới thiệu
Console không tự quét hay tự thay đổi hệ thống: mọi job gọi `php-quickpatch.sh <lệnh> … --json` và đọc stdout (`C-SRS-05`, `FR-CON-SAFE-003`). Vì vậy đầu ra `--json` là **hợp đồng API thứ hai** của hệ thống, có 3 bên tiêu thụ: (1) `qp-console.py` (lưu vào `jobs/<job_id>/result.json`, `state/last-scan.json`, trả qua `GET /api/v1/jobs/{job_id}`); (2) pipeline CI của người dùng (`UC-CLI-001`); (3) máy trung tâm Phase 2 (`FR-FLT-EXEC-001`, kiểm schema → `ERR-FLT-422-02`). Quy chuẩn chung (thời gian, định danh, ngôn ngữ) theo [api-spec.md §2.1](api-spec.md).

## 2. Quy tắc đầu ra
| Quy tắc | Nội dung | Căn cứ |
| :--- | :--- | :--- |
| Kênh | stdout chứa **đúng 1** tài liệu JSON UTF-8 kết thúc bằng 1 ký tự xuống dòng; văn bản cho người đọc (`[OK]`, `[WARN]`, `[VULN]`, `[i]`) ra stderr và `php-quickpatch.log` | `FR-CLI-JSON-001`, `BR-CLI-002` |
| Mã hoá | Bash tự escape `\`, `"`, U+0000–U+001F (dạng `\uXXXX`); không phụ thuộc `jq`; khoá theo thứ tự cố định của schema | `FR-CLI-JSON-001` |
| Mã thoát | 0 = không còn vấn đề/thành công; 1 = còn vấn đề hoặc thành công có cảnh báo; 2 = lỗi tham số/runtime/khoá/toàn vẹn; giá trị giống trường `exit_code` | `BR-CLI-004`, error-matrix §2.2 |
| Lỗi trước khi có dữ liệu | Lệnh vẫn in envelope với `result: null` và `errors[]` (vd `ERR-CLI-400-01`, `ERR-CLI-424-02`) khi đã đọc được cờ `--json`; lỗi phân tích tham số trước khi gặp `--json` chỉ in văn bản ra stderr như v0.1 | `BR-CLI-002` |
| Che bí mật | `command.argv`, `message`, đường dẫn không chứa token, API key, mật khẩu (thay bằng `***`) | `BR-SEC-006` |
| Kích thước | Envelope ≤ 20 MiB (giới hạn log/kết quả job của console); mảng findings vượt ngưỡng bị cắt kèm `result.truncated[]` = tên mảng bị cắt (ĐX) | `BR-JOB-006` |
| Chọn major cũ | `--json-schema <major>` xuất major cũ trong ≥ 2 bản minor sau khi có major mới; major không hỗ trợ → `ERR-CLI-400-01` | `BR-CLI-001` |
| Schema công bố | `share/php-quickpatch/schemas/qp.<lệnh>.v<major>.schema.json` (JSON Schema 2020-12, `$schema` = `https://json-schema.org/draft/2020-12/schema`, `$id` = `urn:php-quickpatch:schema:qp.<lệnh>:<major>` (ĐX)); `php-quickpatch.sh schema <lệnh>` in schema | `FR-CLI-JSON-002` |

## 3. Envelope chung

### 3.1 Trường
| Trường | Kiểu | Bắt buộc | Mô tả | Căn cứ |
| :--- | :--- | :---: | :--- | :--- |
| `schema` | string | Có | Định danh schema `qp.<lệnh>/<major>`, regex `^qp\.[a-z]+(\.[a-z]+)*/[1-9][0-9]*$` (vd `qp.feeds.status/1`) | `FR-CLI-JSON-001` |
| `schema_version` | string | Có | SemVer `MAJOR.MINOR.PATCH` của schema; `MAJOR` bằng số sau `/` của `schema` (ĐX, §3.2) | `BR-CLI-001` |
| `tool` | object | Có | `{name: "php-quickpatch", version: "2.0.0"}` | `FR-CLI-JSON-001` |
| `generated_at` | string | Có | Thời điểm tạo envelope, UTC ms | |
| `host` | object | Có | `{hostname, os, kernel, is_root, in_container}` | |
| `command` | object | Có | `{name, subcommand, argv[] (đã che), job_id, actor}`; `job_id`, `actor` lấy từ biến `QP_JOB_ID`, `QP_ACTOR` do console truyền, `null` khi chạy tay (ĐX: thêm 3 trường so với FR) | `FR-CLI-JSON-001`, `BR-CON-008` |
| `dry_run` | boolean | Có | `true` khi có `--dry-run` | `BR-CLI-003` |
| `exit_code` | integer | Có | 0, 1 hoặc 2 | `BR-CLI-004` |
| `data` | object | Có | Độ tươi dữ liệu: `{bundle_id, freshness, data_age_h, stale_sources[{src_id, age_h, last_error}]}`; chưa có bundle → `bundle_id: null`, `freshness: null` kèm `ERR-FEED-503-01` | DOC-SRS-QP-FEED-003 §3.5, `Q-ST-13` |
| `catalog_version` | string \| null | Có | Phiên bản catalog hiệu lực | `FR-SCN-CAT-001` |
| `result` | object \| null | Có | Nội dung riêng của lệnh (§5–§10) | |
| `issues` | array | Có | Vấn đề còn mở: `{severity: critical\|high\|medium\|low, code: ERR-*\|null, message, object_ref}` | `FR-CLI-JSON-001` |
| `errors` | array | Có | Lỗi làm lệnh thất bại hoặc dừng 1 phần: `{code: ERR-*, message, object_ref}` | |
| `warnings` | array | Có | Cảnh báo không làm thất bại lệnh: `{code: ERR-*\|null, message, object_ref}` | error-matrix §2.2 |

`object_ref` (ĐX) = chuỗi chỉ đối tượng liên quan: `runtime:<runtime_id>`, `site:<site_id>`, `project:<project_id>`, `container:<id>`, `plan:<plan_id>/<chk_id>`, `source:<src_id>`, `host` hoặc `null`.

### 3.2 `schema` và `schema_version` — quy tắc tương thích
| Thay đổi | `schema` | `schema_version` | Bên tiêu thụ phải |
| :--- | :--- | :--- | :--- |
| Thêm trường tuỳ chọn, thêm giá trị enum ở trường được đánh dấu "mở rộng được" | Giữ `qp.<lệnh>/1` | Tăng MINOR (`1.0.0` → `1.1.0`) | Bỏ qua trường lạ; xử lý giá trị enum lạ như `UNKNOWN` |
| Sửa mô tả, ví dụ, ràng buộc không đổi hình dạng | Giữ | Tăng PATCH | Không đổi |
| Đổi tên, xoá, đổi kiểu trường, đổi nghĩa mã thoát | `qp.<lệnh>/2` | `2.0.0` | Kiểm `schema`; major không hỗ trợ → từ chối |

Console Phase 1 hỗ trợ major 1 của cả 6 schema; envelope có major khác, JSON không phân tích được hoặc thiếu trường bắt buộc → job `FAILED` với `ERR-JOB-500-01`, `details.reason = "invalid_envelope"` (ĐX). Máy trung tâm Phase 2 áp cùng kiểm tra → `ERR-FLT-422-02`. Enum "mở rộng được" (ĐX): `issues[].severity` **không**; `runtimes[].install_source`, `environment.panel`, `preview.changes[].type` **có**.

### 3.3 Ví dụ envelope
```json
{
  "schema": "qp.scan/1",
  "schema_version": "1.0.0",
  "tool": {"name": "php-quickpatch", "version": "2.0.0"},
  "generated_at": "2026-10-22T10:05:11.402Z",
  "host": {"hostname": "web01", "os": "ubuntu 24.04", "kernel": "6.8.0-85-generic", "is_root": true, "in_container": false},
  "command": {"name": "scan", "subcommand": null, "argv": ["scan", "--json"], "job_id": "JOB-20261022-100448-7c2e", "actor": "console:root"},
  "dry_run": false,
  "exit_code": 1,
  "data": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "freshness": "AGING", "data_age_h": 12,
           "stale_sources": [{"src_id": "SRC-004", "age_h": 12, "last_error": "ERR-FEED-429-01"}]},
  "catalog_version": "2026.10.20-1",
  "result": {"…": "theo §5"},
  "issues": [{"severity": "critical", "code": null, "message": "PHP 8.2.34 (/usr/bin/php8.2): CVE-2026-109618, CVE-2026-109619 chưa vá; bản vá tối thiểu 8.2.35", "object_ref": "runtime:php:3f9a0c1d2e4b"}],
  "errors": [],
  "warnings": [{"code": "ERR-FEED-503-02", "message": "OSV không truy cập được, bỏ qua /srv/app/composer.lock", "object_ref": "project:a1b2c3d4e5f6"}]
}
```

### 3.4 Khung JSON Schema của envelope (rút gọn)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:php-quickpatch:schema:qp.envelope:1",
  "type": "object",
  "required": ["schema", "schema_version", "tool", "generated_at", "host", "command", "dry_run", "exit_code", "data", "catalog_version", "result", "issues", "errors", "warnings"],
  "properties": {
    "schema": {"type": "string", "pattern": "^qp\\.[a-z]+(\\.[a-z]+)*/[1-9][0-9]*$"},
    "schema_version": {"type": "string", "pattern": "^[1-9][0-9]*\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"},
    "exit_code": {"enum": [0, 1, 2]},
    "dry_run": {"type": "boolean"},
    "issues": {"type": "array", "items": {"type": "object", "required": ["severity", "code", "message", "object_ref"],
      "properties": {"severity": {"enum": ["critical", "high", "medium", "low"]},
                     "code": {"type": ["string", "null"], "pattern": "^ERR-[A-Z]+-[0-9]{3}-[0-9]{2,3}$"}}}},
    "errors": {"type": "array", "items": {"type": "object", "required": ["code", "message"],
      "properties": {"code": {"type": "string", "pattern": "^ERR-[A-Z]+-[0-9]{3}-[0-9]{2,3}$"}}}}
  }
}
```
Schema của từng lệnh dùng `allOf` với khung này và khai báo `properties.result`.

## 4. Đối tượng `preview` và `fingerprint` của dry-run
Mọi lệnh ghi chạy `--dry-run` (`fix`, `rollback`, `migrate install|switch|rollback|remove-old`, `plan run` mục thay đổi hệ thống, `feeds schedule`) trả `result.preview` và `result.fingerprint`. SCR-011 hiển thị đủ 4 mục bắt buộc của `NFR-USE-006` từ đối tượng này; cổng D của console dùng `fingerprint` để kiểm `BR-CON-005` ([api-spec.md §2.13.3](api-spec.md)).

| Trường | Kiểu | Mô tả | Mục `NFR-USE-006` |
| :--- | :--- | :--- | :--- |
| `preview.changes[]` | array | `{type, action, target, from, to, detail, verified}`; `type` ∈ {`file`, `package`, `repo`, `service`, `pool`, `site_binding`, `panel`, `link`, `systemd`, `pm2`, `compose`, `cron`} (mở rộng được); `action` ∈ {`create`, `modify`, `delete`, `install`, `upgrade`, `remove`, `restart`, `reload`, `switch`}; `verified=false` khi lệnh playbook "chưa kiểm chứng" (`BR-ENV-010`) | Thay đổi dry-run |
| `preview.affected[]` | array | `{kind: runtime\|site\|app\|project\|container\|host, id, label}` | Đối tượng ảnh hưởng |
| `preview.disruption` | object | `{expected_s, scope: none\|site\|runtime\|host, basis}`; `expected_s` = số giây ước tính hoặc `null` khi không ước tính được; `basis` = căn cứ (vd "C6–C10 ≤ 30 s P95, `NFR-ENV-01`") | Gián đoạn dự kiến |
| `preview.reversibility` | object | `{level: full\|partial\|none, rollback_command, notes[]}` | Khả năng hoàn tác |
| `preview.requires_retype` | object \| null | `{value_kind: site_id\|runtime_id\|branch, rule: "BR-CON-006"}` khi hành động cần xác nhận kép | — |
| `fingerprint` | object | `{bundle_id, scan_fingerprint, catalog_version}` tại thời điểm dry-run | — |

```json
"preview": {
  "changes": [
    {"type": "package", "action": "upgrade", "target": "php8.2-fpm", "from": "8.2.34-1+ubuntu24.04.1", "to": "8.2.35-1+ubuntu24.04.1", "detail": "apt-get install -y -q --only-upgrade", "verified": true},
    {"type": "file", "action": "delete", "target": "/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini", "from": null, "to": null, "detail": "gỡ mitigation khi đã vá (FR-PTCH-MIT-002)", "verified": true},
    {"type": "service", "action": "restart", "target": "php8.2-fpm.service", "from": null, "to": null, "detail": "restart_php_services", "verified": true}
  ],
  "affected": [{"kind": "runtime", "id": "php:3f9a0c1d2e4b", "label": "PHP 8.2.34 /usr/bin/php8.2"},
               {"kind": "site", "id": "shop.example.com", "label": "shop.example.com (PB-003)"}],
  "disruption": {"expected_s": 5, "scope": "runtime", "basis": "restart php8.2-fpm; request đang xử lý bị ngắt"},
  "reversibility": {"level": "partial", "rollback_command": "php-quickpatch.sh rollback <run_id>",
                    "notes": ["Gói nâng qua apt không bị hạ cấp khi rollback (giữ hành vi v0.1)"]},
  "requires_retype": null
},
"fingerprint": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "scan_fingerprint": "5d0c9a…", "catalog_version": "2026.10.20-1"}
```
Số giây `expected_s` của ví dụ là minh hoạ; giá trị thực do CLI ước tính theo playbook (chưa đo).

## 5. `qp.scan/1` — lệnh `scan`
Console lưu envelope vào `STATE_DIR/state/last-scan.json` (ghi tạm + `rename`) và đọc lại cho các endpoint `GET /api/v1/overview`, `/environment`, `/runtimes`, `/sites`, `/projects`, `/containers`, `/dependency-findings`, `/webshell-findings`.

| Trường `result` | Kiểu | Nội dung | FR |
| :--- | :--- | :--- | :--- |
| `scan_fingerprint` | string | SHA-256 hex của `site_binding[]` + phiên bản runtime | `FR-PLAN-GEN-001` |
| `environment` | object | `{os_id, os_version, pkg_mgr, panel, has_systemd, has_docker, in_container, is_root, web_servers[], playbooks[{pb_id, layer}], restrictions[{code, message}]}` | `FR-SCAN-ENV-001`, `FR-SCN-ENV-001` |
| `runtimes[]` | array | §5.1 | `FR-SCAN-RT-001`, `FR-SCAN-RT-002`, `FR-SCN-*` |
| `sites[]` | array | `site_binding` (DOC-SRS-QP-ENV-001 §4.2): `site_id`, `pb_id`, `server_names[]`, `docroot`, `owner_user`, `binding_kind`, `binding_ref`, `current_branch`, `current_bin`, `runtime_id`, `runtime_endpoint`, `log_sources[]`, `hc_urls[]`, `hc_mode` | `FR-SCAN-MAP-001` |
| `projects[]` | array | `{project_id, dir, owner, kinds[composer\|npm\|yarn\|pnpm\|wordpress\|docker], site_id, lockfiles[]}` | `FR-SCAN-PRJ-001` |
| `containers[]` | array | `{id, name, image, php_version, node_version, compose_project, compose_service}` | `FR-SCAN-PRJ-002` |
| `dependency_findings[]` | array | `{project_id, ecosystem: Packagist\|npm, package, version, advisories[], severity, in_kev, is_malware, fixed_versions[]}` | `FR-ASMT-DEP-001` |
| `wordpress_findings[]` | array | `{site_dir, project_id, version, min_patched, status: ok\|vulnerable\|unknown, advisories[], in_kev, risk}` | `FR-ASMT-DEP-002` |
| `webshell_findings[]` | array | `{path, rule, sha256, mtime, size, project_id}` (chỉ báo cáo, `BR-SEC-003`) | `FR-SCAN-WSH-001` |
| `drift_warnings[]` | array | `{site_id, expected, actual, code: "ERR-SCAN-409-01"}` | `FR-SCAN-DRF-001` |
| `ranking[]` | array | `{object_ref, R, level: CRITICAL\|HIGH\|MEDIUM\|LOW, reason_codes[]}`; `reason_codes` ∈ {`KEV`, `CVSS_GE_9`, `EOL`, `CVSS_7_TO_8_9`, `EOL_LE_90D`, `OTHER`} theo thứ tự `BR-ASMT-004` (ĐX) | `FR-ASMT-RANK-001` |
| `plan_deadlines[]` | array | `{runtime_id, deadline, days_left, plan_id, plan_status}` | `FR-PLAN-DL-001` |
| `summary` | object | `{runtimes, by_state{ok, ok_backport, vulnerable, eol, unknown}, eol_within_90d, kev_findings, critical_issues, vulnerable_packages}` | `FR-CON-OVW-001` |

### 5.1 Đối tượng `runtime`
```json
{
  "runtime_id": "php:3f9a0c1d2e4b", "kind": "php", "bin": "/usr/bin/php8.2",
  "version_raw": "8.2.34", "version": "8.2.34", "branch": "8.2",
  "sapis": ["cli", "fpm"], "ini_scan_dirs": ["/etc/php/8.2/cli/conf.d", "/etc/php/8.2/fpm/conf.d"],
  "extensions": ["curl", "mbstring", "mysqli", "opcache"],
  "owner_pkg": {"manager": "dpkg", "name": "php8.2-cli", "version": "8.2.34-1+ubuntu24.04.1"},
  "install_source": "package", "scenario_ids": ["SCN-PHP-010", "SCN-PHP-015"],
  "state": "vulnerable", "lifecycle_status": "SECURITY_ONLY", "priority": "HIGH",
  "eol_date": "2026-12-31", "days_to_eol": 70, "is_lts": null, "lts_codename": null,
  "latest_patch": "8.2.35", "min_patched": "8.2.35", "driver_ids": ["CVE-2026-109618", "CVE-2026-109619"],
  "backport": {"status": "UNKNOWN", "source": "SRC-016"},
  "locked": false, "lock_reason": null,
  "risk": {"R": 60, "level": "HIGH", "components": {"S_cvss": 39.2, "S_cnt": 8, "S_kev": 0, "S_life": 5, "S_eol": 8}},
  "abi": null, "npm_version": null, "apps": [], "site_ids": ["shop.example.com", "blog.example.com"]
}
```
Enum: `kind` ∈ {`php`, `node`}; `state` ∈ {`ok`, `ok-backport`, `vulnerable`, `eol`, `unknown`} (`FR-SCAN-RT-001`); `lifecycle_status` ∈ {`ACTIVE`, `SECURITY_ONLY`, `CURRENT`, `ACTIVE_LTS`, `MAINTENANCE_LTS`, `EOL`, `PRE_RELEASE`, `UNKNOWN`} (DOC-SRS-QP-SCN-000 §2.1); `priority` ∈ {`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`} = mức "Nghiêm trọng/Cao/Trung bình/Thấp" của DOC-SRS-QP-SCN-000 §2.2 (ĐX: tên enum tiếng Anh); `install_source` PHP ∈ {`package`, `scl`, `panel`, `source_build`, `docker`, `unknown`}, Node.js ∈ {`package`, `nodesource`, `tarball`, `nvm`, `panel`, `docker`, `unknown`}; `backport.status` ∈ {`FIXED`, `NOT_AFFECTED`, `UNKNOWN`, `null`} (`FR-FEED-NORM-003`). Với Node.js: `abi` = `process.versions.modules`, `npm_version`, `apps[] {app_id, manager: systemd|pm2, unit_or_name, user}`, `is_lts`, `lts_codename`. Điểm `R` của ví dụ tính theo `BR-FEED-040`/`BR-FEED-041` (data-sources-merge-risk.md §8.5 ví dụ 3): `S_cvss` = 4 × 9,8 = 39,2; `S_cnt` = min(20; 4 × 2) = 8; `S_kev` = 0; `S_life` = 5 (`SECURITY_ONLY`); `S_eol` = 8 (`d` = 70 ≤ 90); `R_raw` = 60,2 → làm tròn 60, cao hơn sàn Cao = 40 → `R` = 60, mức `HIGH` (40–69, `BR-FEED-042`).

## 6. `qp.assess/1` — lệnh `assess`
Console lưu vào `jobs/<job_id>/result.json`; `GET /api/v1/runtimes/{runtime_id}/assessment` và `…/candidates` đọc kết quả `assess` mới nhất của `runtime_id` ([api-spec-core.md §4.3](api-spec-core.md)).

| Trường `result` | Kiểu | Nội dung | FR |
| :--- | :--- | :--- | :--- |
| `runtime_id` | string | Runtime được đánh giá | `FR-CLI-CMD-001` |
| `evaluated_on` | string (date) | Ngày `T` dùng chung cho hiện tại và ứng viên | `BR-ASMT-003` |
| `current` | object | `{version, branch, cve_counts{critical, high, medium, low}, kev_count, lifecycle_status, is_lts, eol_date, days_to_eol, latest_patch, min_patched, risk{R, level, components{}}, not_assessed_label}`; `not_assessed_label` = "nguồn không còn đánh giá CVE mới" với nhánh EOL (`BR-FEED-029`) hoặc `null` | `FR-ASMT-CUR-001`, `FR-ASMT-RISK-001` |
| `advisories[]` | array | `{adv_id, aliases[], cvss, severity, in_kev, kev_due, published_at, fixed_in, sources[], status: UNPATCHED\|FIXED_BACKPORT\|NOT_AFFECTED}` | `FR-ASMT-CUR-001` |
| `candidates[]` | array | `{version, branch, types[SAME_BRANCH_LATEST\|NEXT_SUPPORTED\|RECOMMENDED\|LATEST_STABLE], lifecycle_status, is_lts, eol_date, selectable, not_selectable_reason, installable: yes\|needs_repo\|no\|unknown, install_source}` | `FR-ASMT-CAND-001`, `FR-ASMT-CAND-002` |
| `comparison` | object | `{rows[{version, cve_counts, kev_count, lifecycle_status, is_lts, eol_date, days_to_eol, major_gap, compat_errors, compat_warnings, R, delta_R}]}` | `FR-ASMT-CMP-001`, `FR-ASMT-RISK-002` |

```json
"result": {
  "runtime_id": "php:3f9a0c1d2e4b", "evaluated_on": "2026-10-22",
  "current": {"version": "8.2.34", "branch": "8.2", "cve_counts": {"critical": 2, "high": 0, "medium": 0, "low": 0}, "kev_count": 0,
              "lifecycle_status": "SECURITY_ONLY", "is_lts": null, "eol_date": "2026-12-31", "days_to_eol": 70,
              "latest_patch": "8.2.35", "min_patched": "8.2.35", "risk": {"R": 60, "level": "HIGH", "components": {"S_cvss": 39.2, "S_cnt": 8, "S_kev": 0, "S_life": 5, "S_eol": 8}}, "not_assessed_label": null},
  "candidates": [
    {"version": "8.2.35", "branch": "8.2", "types": ["SAME_BRANCH_LATEST"], "lifecycle_status": "SECURITY_ONLY", "is_lts": null, "eol_date": "2026-12-31", "selectable": true, "not_selectable_reason": null, "installable": "yes", "install_source": "package"},
    {"version": "8.3.36", "branch": "8.3", "types": ["NEXT_SUPPORTED"], "lifecycle_status": "SECURITY_ONLY", "is_lts": null, "eol_date": "2027-12-31", "selectable": true, "not_selectable_reason": null, "installable": "needs_repo", "install_source": "repo:ppa:ondrej/php"},
    {"version": "8.5.12", "branch": "8.5", "types": ["RECOMMENDED", "LATEST_STABLE"], "lifecycle_status": "ACTIVE", "is_lts": null, "eol_date": "2029-12-31", "selectable": true, "not_selectable_reason": null, "installable": "needs_repo", "install_source": "repo:ppa:ondrej/php"}
  ],
  "comparison": {"rows": [{"version": "8.2.34", "R": 60, "delta_R": 0}, {"version": "8.2.35", "R": 40, "delta_R": -20},
                          {"version": "8.3.36", "R": 20, "delta_R": -40}, {"version": "8.5.12", "R": 0, "delta_R": -60}]}
}
```
Ngày EOL 8.3 (2027-12-31), 8.5 (2029-12-31) và đích đề xuất 8.5 theo `SCN-PHP-010` (DOC-SRS-QP-SCN-PHP-001 §2). Điểm `R` của ví dụ tính theo `BR-FEED-040`/`BR-FEED-041` trên cùng bundle, `T` = 2026-10-22 (`BR-FEED-044`), dùng làm giá trị kỳ vọng cho test hồi quy `NFR-MNT-002`:

| Phiên bản | `status`, `d` | CVE chưa vá | `R_raw` | Sàn (`priority`) | `R`, mức | `delta_R` | Nguồn |
| :--- | :--- | :--- | ---: | :--- | :--- | ---: | :--- |
| 8.2.34 (hiện tại) | `SECURITY_ONLY`, 70 | 2 critical, `cvss_max` 9,8, KEV 0 | 60,2 | 40 (Cao) | 60, `HIGH` | 0 | [merge-risk §8.5](../srs/data-sources-merge-risk.md) ví dụ 3 |
| 8.2.35 | `SECURITY_ONLY`, 70 | 0 | 13 | 40 (Cao: ≤ 90 ngày tới EOL) | 40, `HIGH` | −20 | merge-risk §8.5 ví dụ 4 |
| 8.3.36 | `SECURITY_ONLY`, 435 | 0 | 5 (`S_life` 5, `S_eol` 0) | 20 (Trung bình: > 90 ngày tới EOL) | 20, `MEDIUM` | −40 | Tính theo merge-risk §8.2 |
| 8.5.12 | `ACTIVE`, 1.166 | 0 | 0 | 0 (Thấp) | 0, `LOW` | −60 | merge-risk §8.5 ví dụ 1 |

Nguồn cài (`install_source`) trong ví dụ là minh hoạ định dạng; giá trị thật lấy từ bundle và hệ thống tại thời điểm chạy.

## 7. `qp.plan/1` — lệnh `plan`
Một schema cho mọi lệnh con; `command.subcommand` ∈ {`create`, `list`, `show`, `approve`, `item`, `run`, `cancel`} (thêm `complete`, `close`, `canary`, `waive` nếu CR ở [api-spec.md §2.14](api-spec.md) được duyệt). `result` theo lệnh con:

| Lệnh con | `result` |
| :--- | :--- |
| `list` | `{plans[]: PlanSummary}` |
| `create`, `show`, `approve`, `cancel` | `{plan: Plan}` |
| `item` | `{plan_id, item: ChecklistItem}` |
| `run` (có/không `--dry-run`) | `{plan_id, item: ChecklistItem, run: {action, child_schema, child_result}, preview?, fingerprint?}`; `child_result` = `result` của lệnh được gọi (vd `qp.migrate/1`) |

Đối tượng `Plan` (lưu ở `plans/<plan_id>/plan.json` + `items.json`, `FR-PLAN-GEN-001`):

| Trường | Kiểu | Nội dung | Căn cứ |
| :--- | :--- | :--- | :--- |
| `plan_id`, `runtime_id` | string | Định danh | spec §1.3 |
| `status` | enum | `draft`, `approved`, `in_progress`, `completed`, `rolled_back`, `cancelled` | DIAG-STATE-QP-PLAN-001 |
| `mode` | enum | `same_branch`, `cross_branch` | `FR-PLAN-GEN-001` |
| `target` | object | `{branch, patch_version, types[], override_reason}` | `FR-PLAN-TGT-001`, `BR-PLAN-001` |
| `stale`, `stale_reasons[]` | boolean, array | `stale_reasons` ∈ {`SCAN_CHANGED`, `TARGET_NEW_KEV`, `TARGET_RISK_UP_20`, `CATALOG_CHANGED`, `TARGET_EOL`} (ĐX: mã cho 4 điều kiện `BR-PLAN-006`) | `BR-PLAN-006` |
| `site_order[]`, `canary_site_id`, `blocked_sites[{site_id, reason}]` | array, string | Thứ tự chuyển, site canary | `FR-PLAN-GEN-002`, `BR-PLAN-004` |
| `upgrade_items[]` | array | `{component_type: extension\|composer\|npm\|native_addon\|framework\|loader, name, current, required, min_compatible, evidence, chk_id}` | `FR-PLAN-DEP-001` |
| `preconditions[]` | array | `{check, required, actual, pass}` | `FR-UPG-PRE-001` |
| `compat_verdicts[]` | array | `{site_id, status: PASS\|FAIL\|PENDING, errors, warnings, waived, pending_parts[]}` | `FR-CMPT-RES-001` |
| `deadline` | object | `{date, days_left, overdue}` | `FR-PLAN-DL-001` |
| `checklist_items[]` | array | `ChecklistItem` (chỉ có ở `show`, `create`) | `FR-SCN-CHK-001` |
| `inputs` | object | `{bundle_id, catalog_version, scan_fingerprint}` | `FR-PLAN-GEN-001` |
| `created_at`, `approved_at`, `approved_by`, `updated_at` | string | Mốc thời gian, actor | `BR-PLAN-003` |

Đối tượng `ChecklistItem` (DOC-SRS-QP-SCN-000 §5.2 + `FR-SCN-CHK-001`): `{chk_id, scenario_id, site_id, phase: P1..P7, action, exec_type: AUTO|SEMI|MANUAL, check_mechanism, done_criteria, risk, applies_when, depends_on[], status: PENDING|RUNNING|DONE|FAILED|SKIPPED|WAIVED, blocked_by[], cli_action, verified, job_id, reason, evidence, updated_at, updated_by}`. `blocked_by[]` (ĐX) = các `chk_id` phụ thuộc chưa `DONE`/`WAIVED` (`BR-SCN-018`).

```json
"result": {"plan": {
  "plan_id": "PLN-20261022-103512-9b1c", "runtime_id": "php:3f9a0c1d2e4b", "status": "draft", "mode": "cross_branch",
  "target": {"branch": "8.5", "patch_version": "8.5.12", "types": ["RECOMMENDED", "LATEST_STABLE"], "override_reason": null},
  "stale": false, "stale_reasons": [],
  "site_order": ["blog.example.com", "shop.example.com"], "canary_site_id": "blog.example.com", "blocked_sites": [],
  "upgrade_items": [{"component_type": "composer", "name": "guzzlehttp/guzzle", "current": "6.5.8", "required": "php >=7.2.5 <8.5", "min_compatible": "7.9.2", "evidence": "composer.lock require.php", "chk_id": "CHK-PHP-010-22"}],
  "preconditions": [{"check": "disk_free_gb", "required": ">= 2", "actual": "14.2", "pass": true}],
  "compat_verdicts": [{"site_id": "blog.example.com", "status": "PASS", "errors": 0, "warnings": 3, "waived": 0, "pending_parts": ["lint_new_bin"]}],
  "deadline": {"date": "2026-12-01", "days_left": 40, "overdue": false},
  "inputs": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "catalog_version": "2026.10.20-1", "scan_fingerprint": "5d0c9a…"},
  "created_at": "2026-10-22T10:35:12.004Z", "approved_at": null, "approved_by": null, "updated_at": "2026-10-22T10:37:40.880Z"
}}
```
Hạn duyệt 2026-12-01 = EOL 8.2 (2026-12-31) − 30 ngày theo `FR-PLAN-DL-001`; tên package và phiên bản trong `upgrade_items` là minh hoạ. `chk_id` `CHK-PHP-010-22` là mục P4 "Nâng dependency Composer, framework/CMS, loader cho `$NEW`" của `SCN-PHP-010` (runtime PHP 8.2 của ví dụ, DOC-SRS-QP-SCN-PHP-002 §5).

## 8. `qp.fix/1` — lệnh `fix` (và `rollback`)
`fix` giữ hành vi v0.1 (không hỏi xác nhận, `BR-CLI-003`); `rollback [ID] --json` dùng cùng schema với `command.name = "rollback"` (ĐX: dùng chung vì cùng manifest). Khác v0.1: `rollback --dry-run` không thay đổi gì và trả `planned_actions[]` (`FR-PTCH-RBK-002`, `CR-FR-02`); `fix` kiểm dịch vụ active sau restart (`FR-PTCH-RST-001`, `CR-FR-05`). Các trường `restarted[]`, `restart_failures[]`, `planned_actions[]` và giá trị `docker-created` của `manifest[].action` là thay đổi **chỉ thêm** theo §3.2: giữ `schema` = `qp.fix/1`, không tăng major (`BR-CLI-001`); vì `qp.fix/1` chưa phát hành, các trường này thuộc ngay `schema_version` `1.0.0`; nếu `CR-FR-02`/`CR-FR-05` được duyệt sau khi đã phát hành 1.0.0 thì tăng MINOR lên `1.1.0`.

| Trường `result` | Kiểu | Nội dung | FR |
| :--- | :--- | :--- | :--- |
| `run_id` | string \| null | Thư mục `backups/<run_id>`; `null` khi `--dry-run` hoặc không có thay đổi | `FR-PTCH-RBK-001` |
| `scope` | object | `{only[], paths[], no_restart, no_memlimit}` | `FR-CLI-COMP-001` |
| `actions[]` | array | `{seq, object_ref, kind: runtime_patch\|mitigation_add\|mitigation_remove\|composer_update\|npm_audit_fix\|wp_update\|wp_verify\|docker_tag\|container_mitigation\|restart\|restore, status: done\|skipped\|failed\|planned, detail, error_code}` | `FR-PTCH-*` |
| `runtimes_after[]` | array | `{runtime_id, version_before, version_after, state_after}` | `FR-PTCH-PHP-001`, `FR-PTCH-NODE-001` |
| `mitigations[]` | array | `{runtime_id, file, action: added\|removed, driver_ids[]}` | `FR-PTCH-MIT-001`, `FR-PTCH-MIT-002` |
| `restarts[]` | array | `{unit, status: restarted\|skipped_no_restart\|failed}`; `failed` khi lệnh restart thoát khác 0 hoặc dịch vụ không active sau 15 s | `FR-PTCH-RST-001` |
| `restarted[]` | array | Mỗi dịch vụ đã gửi lệnh restart/reload: `{service, active, waited_s}`; `service` = tên unit systemd, dịch vụ cPanel `restartsrv_<svc>`, tên ứng dụng pm2 hoặc tên tiến trình khi không có systemd; `active` (boolean) = kết quả kiểm sau restart (systemd `systemctl is-active --quiet`, cPanel `--check`, pm2 `pm2_env.status = online`, `pgrep`); `waited_s` (integer 0–15) = số giây từ khi lệnh restart trả về tới khi kiểm đạt, 15 khi hết thời gian. `--no-restart` → mảng rỗng | `FR-PTCH-RST-001` |
| `restart_failures[]` | array | Phần tử của `restarted[]` có `active = false`: `{service, check, waited_s, error_code: "ERR-PTCH-500-01"}`; `check` = lệnh kiểm đã dùng (ĐX). Mảng khác rỗng → `errors[]` có `ERR-PTCH-500-01` (mã đề xuất, error-matrix.md §3.10) cho từng dịch vụ, issue `critical` kèm `rollback_hint`, `exit_code` = 2; không tự rollback | `FR-PTCH-RST-001` |
| `counts` | object | `{fixed, open_issues, critical}` (tương ứng dòng "fixed: N \| open issues: N (critical: N)" của v0.1) | `BR-CLI-002` |
| `rollback_hint` | string \| null | `php-quickpatch.sh rollback <run_id>` | v0.1 `main()` |
| `preview`, `fingerprint` | object | Chỉ khi `dry_run=true` (§4) | `FR-CON-SAFE-001` |
| `manifest[]` (chỉ `rollback`) | array | Dòng manifest đã/ sẽ phát lại theo thứ tự ngược: `{seq, action: copy\|created\|untar\|docker-created\|composer-install\|npm-ci\|note\|switch\|reload\|panel\|link\|systemd\|pm2\|compose, args[], status}` | `FR-PTCH-RBK-002`, `FR-PTCH-RBK-001` |
| `planned_actions[]` (chỉ `rollback --dry-run`) | array | Dữ liệu xem trước cho SCR-011 (`BR-CON-005`): đúng 1 phần tử cho mỗi dòng manifest, theo thứ tự phát lại (ngược, `tac`): `{action, arg1, arg2, reversible}`; `action` cùng tập giá trị với `manifest[].action`; `arg1`, `arg2` (string \| null) = cột ARG1, ARG2 của dòng manifest; `reversible` ∈ {`full`, `partial`, `none`} (ĐX: cùng tập giá trị `preview.reversibility.level`) = mức khôi phục trạng thái trước lượt `fix` của dòng đó: `partial` cho `untar` của WordPress (thay đổi CSDL không hoàn tác, `FR-PTCH-WP-001`), `none` cho `note` (gói đã nâng không bị hạ cấp), `full` cho các dòng còn lại. Lần chạy này 0 file đổi, 0 dịch vụ restart/reload, không ghi audit "intent" | `FR-PTCH-RBK-002` |

Lỗi thường gặp trong `errors[]`/`issues[]`: `ERR-PTCH-403-01`, `ERR-PTCH-424-01`, `ERR-PTCH-412-01`, `ERR-PTCH-424-02`, `ERR-PTCH-424-03`, `ERR-PTCH-424-04`, `ERR-PTCH-502-01`, `ERR-PTCH-404-01` (rollback), `ERR-PTCH-500-01` và `ERR-PTCH-409-01` (mã đề xuất chờ `CR-FR-05`, error-matrix.md §3.10), `ERR-ENV-507-01`, `ERR-AUD-500-01`, `ERR-SCN-422-01` (runtime bị khoá → `SKIPPED`).

```json
"result": {
  "run_id": "20261022-104201", "scope": {"only": ["php"], "paths": [], "no_restart": false, "no_memlimit": false},
  "actions": [
    {"seq": 1, "object_ref": "runtime:php:3f9a0c1d2e4b", "kind": "runtime_patch", "status": "done", "detail": "apt upgraded: php8.2-cli php8.2-fpm", "error_code": null},
    {"seq": 2, "object_ref": "runtime:php:3f9a0c1d2e4b", "kind": "restart", "status": "done", "detail": "php8.2-fpm.service", "error_code": null}
  ],
  "runtimes_after": [{"runtime_id": "php:3f9a0c1d2e4b", "version_before": "8.2.34", "version_after": "8.2.35", "state_after": "ok"}],
  "mitigations": [], "restarts": [{"unit": "php8.2-fpm.service", "status": "restarted"}],
  "restarted": [{"service": "php8.2-fpm.service", "active": true, "waited_s": 1}], "restart_failures": [],
  "counts": {"fixed": 1, "open_issues": 0, "critical": 0}, "rollback_hint": "php-quickpatch.sh rollback 20261022-104201"
}
```
`waited_s` = 1 là minh hoạ (chưa đo). Ca dịch vụ không active (`TC-PTCH-104`): `restarted` = `[{"service": "php8.2-fpm.service", "active": false, "waited_s": 15}]`, `restart_failures` = `[{"service": "php8.2-fpm.service", "check": "systemctl is-active --quiet php8.2-fpm.service", "waited_s": 15, "error_code": "ERR-PTCH-500-01"}]`, `exit_code` = 2.

Ví dụ `rollback 20261022-104201 --dry-run --json` (manifest 5 dòng như `TC-PTCH-101`, `STATE_DIR` = `/var/lib/php-quickpatch` khi chạy root; `arg1`/`arg2` theo định dạng v0.1: `copy` = đường dẫn gốc + bản sao trong `files/`, `untar` = file `node-<prefix đổi / thành _>.tar.gz` + prefix, `note` = thông điệp):
```json
"result": {
  "run_id": null, "scope": {"only": [], "paths": [], "no_restart": false, "no_memlimit": false}, "actions": [],
  "planned_actions": [
    {"action": "note", "arg1": "apt upgraded: php8.2-cli php8.2-fpm (packages are not downgraded by rollback)", "arg2": null, "reversible": "none"},
    {"action": "docker-created", "arg1": "web-test", "arg2": "/usr/local/etc/php/conf.d/zz-php-quickpatch-mitigation.ini", "reversible": "full"},
    {"action": "untar", "arg1": "/var/lib/php-quickpatch/backups/20261022-104201/node-_usr_local.tar.gz", "arg2": "/usr/local", "reversible": "full"},
    {"action": "created", "arg1": "/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini", "arg2": null, "reversible": "full"},
    {"action": "copy", "arg1": "/var/www/shop.test/composer.lock", "arg2": "/var/lib/php-quickpatch/backups/20261022-104201/files/var/www/shop.test/composer.lock", "reversible": "full"}
  ],
  "preview": {"…": "theo §4"}, "fingerprint": {"…": "theo §4"},
  "counts": {"fixed": 0, "open_issues": 0, "critical": 0}, "rollback_hint": null
}
```

## 9. `qp.migrate/1` — lệnh `migrate`
`command.subcommand` ∈ {`install`, `switch`, `healthcheck`, `rollback`, `ack` (đề xuất, chờ `CR-FR-01`), `remove-old`, `status`, `hc-urls` (ĐX)}; bí danh `upgrade`, `switch-site`, `healthcheck`, `rollback-site` ghi `command.name` = `migrate` và `command.subcommand` tương ứng (`FR-CLI-CMD-003`).

| Lệnh con | Trường `result` |
| :--- | :--- |
| `install` | `{runtime: php\|node, target, new_bin, install_source, repo_added, packages[], cfg_report{copied[], dropped_directives[], extensions_installed[], not_transferable[]}, preconditions[], run_id}` (`FR-UPG-INST-001`, `FR-UPG-CFG-002`, `FR-UPG-PRE-001`) |
| `switch` | `{switch: SwitchRecord, steps[], hc: HcSummary, run_id}` |
| `healthcheck` | `{site_id, baseline_only, hc_urls[], baseline{rounds, per_url[{url, code_b, size_b, p95_ms}], w0}, hc: HcSummary\|null}` (`FR-UPG-HC-001`, `FR-UPG-HC-003`) |
| `rollback` | `{switch: SwitchRecord, steps[] (R1–R7), manifest[]}` (`FR-UPG-RBK-001`) |
| `ack` (đề xuất, chờ `CR-FR-01`) | `{acknowledgement: Acknowledgement}` (`FR-UPG-ACK-001`) |
| `remove-old` | `{runtime_id, idle_days, removed_packages[], affected_switches[{run_id, rollback_available: false}]}` (`FR-UPG-RMV-001`) |
| `status` | `{switches[]: SwitchRecord, locked_after_rollback_failed: bool}` |
| `hc-urls` (ĐX) | `{site_id, hc_urls[], config_file}` |

`SwitchRecord` (DOC-SRS-QP-ENV-001 §4.3): `{run_id, site_id, plan_id, from_branch, to_branch, status: PREFLIGHT|SWITCHED|HC_RUNNING|PASSED|ROLLED_BACK|ROLLBACK_FAILED|HC_FAILED_KEPT|ABORTED, t_start, t_switched, t_hc_end, t_rollback_end, rollback_reason: HC-C0..HC-C9|MANUAL|null, rollback_available, actor}`. `steps[]` = `{step: C1..C12|R1..R7, status: done|failed|skipped, started_at, duration_ms, detail, error_code}`. `HcSummary` = `{verdict: PASS|FAIL|null, mode: full|skip, window_s, rounds_done, violations[{criterion: HC-C0..HC-C9, url, detail}], report_ref: "backups/<run_id>/hc.json"}` (`FR-UPG-HC-004..006`).

`Acknowledgement` (`FR-UPG-ACK-001`, lệnh `migrate ack RUN_ID --reason TEXT --json`, `TEXT` 20–500 ký tự, không ký tự điều khiển; không cần `--dry-run`/`--yes`, `dry_run` luôn `false`):

| Trường | Kiểu | Nội dung |
| :--- | :--- | :--- |
| `run_id`, `site_id` | string | Lượt chuyển được xác nhận và site của lượt |
| `plan_id` | string \| null | Kế hoạch chứa lượt; `null` khi lượt chạy `--no-plan` |
| `status` | enum | Trạng thái lượt, không đổi sau xác nhận (states.md `T-SW-19`): `ROLLED_BACK`, `HC_FAILED_KEPT`, `ROLLBACK_FAILED` |
| `acknowledged_at` | string | Thời điểm xác nhận, UTC (ghi vào `backups/<run_id>/switch.json`) |
| `acknowledged_by` | string | Actor: `QP_ACTOR` khi chạy từ console (vd `console:root`); tên người dùng hệ thống (`id -un`) khi chạy tay (ĐX) |
| `binding_now` | object | Lớp gán hiện tại đọc lại theo playbook (`FR-SCAN-MAP-001`), làm bằng chứng: `{binding_kind, binding_ref, current_branch, current_bin, runtime_endpoint, runtime_id}` (ĐX: tập con của `site_binding`, §5) |
| `switch_lock_released` | boolean | `true` khi lượt `ROLLBACK_FAILED` này là lượt chưa xác nhận cuối cùng trên máy chủ, khoá `ERR-UPG-423-01` được gỡ; `false` trong mọi trường hợp khác |
| `next_allowed_sites[]` | array of string | `site_id` được phép chạy `migrate switch` sau xác nhận theo `FR-UPG-SEQ-001`: chính site lỗi (lượt mới) và site kế tiếp của `site_order[]` khi lượt thuộc kế hoạch; `[site_id]` khi `plan_id = null`; rỗng khi máy chủ vẫn còn lượt `ROLLBACK_FAILED` khác chưa xác nhận (ĐX) |

Lý do xác nhận không có trong `Acknowledgement` (chỉ ghi vào `switch.json` và audit sau khi che theo `BR-SEC-006`). Mã thoát của `ack`: 0 = đã xác nhận; 2 = `ERR-UPG-409-04` (mã đề xuất, error-matrix.md §3.11: lượt không ở 3 trạng thái trên hoặc đã xác nhận), `ERR-CLI-400-01` (`RUN_ID` không tồn tại hoặc lý do sai độ dài), `ERR-CLI-423-01` (khoá `STATE_DIR/.lock` đang bị lượt khác giữ, `BR-JOB-002`), `ERR-AUD-500-01`. Đây là thay đổi **chỉ thêm** (thêm 1 giá trị `command.subcommand` và 1 dạng `result`) theo §3.2: giữ `qp.migrate/1`, không tăng major (`BR-CLI-001`); nếu PO duyệt `CR-FR-01` sau khi `qp.migrate/1` 1.0.0 đã phát hành thì tăng MINOR lên `1.1.0`. `AC-UPG-22` và `TC-UPG-111` kiểm các trường này.

Mã thoát của `switch`: 0 = `PASSED`; 1 = `ROLLED_BACK` (`ERR-SCN-500-01`) hoặc `HC_FAILED_KEPT` (`ERR-HC-500-01`); 2 = `ABORTED` ở C1–C6 hoặc `ROLLBACK_FAILED` (`ERR-HC-500-02`). Lỗi điều kiện C1/C2 trong `errors[]`: `ERR-ENV-409-01`, `ERR-UPG-423-01`, `ERR-UPG-409-02`, `ERR-UPG-409-03` (mã đề xuất mới), `ERR-SCN-424-01`, `ERR-UPG-409-01`, `ERR-SCN-409-02`, `ERR-ENV-412-01`, `ERR-SCN-412-02`.

```json
"result": {
  "run_id": "20261022-111500",
  "switch": {"run_id": "20261022-111500", "site_id": "blog.example.com", "plan_id": "PLN-20261022-103512-9b1c",
             "from_branch": "8.2", "to_branch": "8.5", "status": "PASSED",
             "t_start": "2026-10-22T11:15:00.010Z", "t_switched": "2026-10-22T11:15:21.442Z", "t_hc_end": "2026-10-22T11:25:22.001Z",
             "t_rollback_end": null, "rollback_reason": null, "rollback_available": true, "actor": "console:root"},
  "steps": [{"step": "C4", "status": "done", "started_at": "2026-10-22T11:15:06.200Z", "duration_ms": 412, "detail": "FastCGI probe unix:/run/php/qp-blog.example.com.sock: 200", "error_code": null}],
  "hc": {"verdict": "PASS", "mode": "full", "window_s": 600, "rounds_done": 10, "violations": [], "report_ref": "backups/20261022-111500/hc.json"}
}
```

Ví dụ `migrate ack 20261022-140000 --reason '…' --json` (dữ liệu của `AC-UPG-22`: `site_order` = [`a.test`, `b.test`, `c.test`], canary `a.test` bị tự rollback; `binding_ref`, `runtime_endpoint`, `runtime_id` là minh hoạ):
```json
"result": {"acknowledgement": {
  "run_id": "20261022-140000", "site_id": "a.test", "plan_id": "PLN-20261022-103512-9b1c", "status": "ROLLED_BACK",
  "acknowledged_at": "2026-10-22T14:20:05.118Z", "acknowledged_by": "console:root",
  "binding_now": {"binding_kind": "nginx_fastcgi", "binding_ref": "/etc/nginx/sites-enabled/a.test.conf:18", "current_branch": "8.2", "current_bin": "/usr/sbin/php-fpm8.2",
                  "runtime_endpoint": "unix:/run/php/php8.2-fpm.sock", "runtime_id": "php:3f9a0c1d2e4b"},
  "switch_lock_released": false, "next_allowed_sites": ["a.test", "b.test"]
}}
```

## 10. `qp.feeds.status/1` — lệnh `feeds status`
Nội dung theo DOC-SRS-QP-FEED-003 §6.4. Theo `BR-DATA-004` (SRS chính `FR-CLI-JSON-001` ưu tiên hơn phụ lục), các trường của §6.4 nằm trong `result` của envelope chung; `schema` giữ `qp.feeds.status/1` (ĐX: bản phụ lục in các trường ở cấp cao nhất; bản 1.0.1 của DOC-SRS-QP-FEED-003 cần cập nhật ví dụ). `GET /api/v1/feeds` trả nguyên `result` trong `data` ([api-spec-core.md §6.1](api-spec-core.md)).

| Trường `result` | Kiểu | Nội dung |
| :--- | :--- | :--- |
| `bundle_id`, `generated_at` | string \| null | Bundle hiện hành |
| `freshness`, `data_age_h` | enum \| null, integer \| null | `FRESH`, `AGING`, `STALE`, `EXPIRED` (`BR-FEED-005`) |
| `sources[]` | array | `{src_id, name, status: OK\|DEGRADED\|FAILED\|DISABLED, last_ok_at, age_h, ttl_h, records, last_error, data_origin: PRIMARY\|CACHE\|SNAPSHOT\|CROSS:SRC-NNN}` |
| `schedule` | object \| null | `{type: systemd\|cron\|crontab_user, interval_h, next_run}` |
| `snapshot` | object | `{packaged_generated_at, sha256_ok}` |

```json
"result": {"bundle_id": "b-20261022T093000Z-3f2a9c1e", "generated_at": "2026-10-22T09:30:00Z", "freshness": "AGING", "data_age_h": 12,
  "sources": [{"src_id": "SRC-004", "name": "NVD CVE API 2.0", "status": "DEGRADED", "last_ok_at": "2026-10-21T21:10:04Z", "age_h": 12, "ttl_h": 6,
               "records": 1537, "last_error": "ERR-FEED-429-01", "data_origin": "CACHE"}],
  "schedule": {"type": "systemd", "interval_h": 6, "next_run": "2026-10-22T12:17:00Z"},
  "snapshot": {"packaged_generated_at": "2026-10-20T06:00:00Z", "sha256_ok": true}}
```
Mã thoát: 0 = `FRESH`/`AGING`; 1 = `STALE`; 2 = `EXPIRED` hoặc không có bundle (DOC-SRS-QP-FEED-003 §6.3).

## 11. Bên tiêu thụ và kiểm tra tương thích
| Schema | Console đọc ở | Phase 2 đọc ở | Test hồi quy |
| :--- | :--- | :--- | :--- |
| `qp.scan/1` | `state/last-scan.json` → endpoint #4–#6, #12, #15–#18 | `GET /api/v1/servers/{server_id}/results`, `fleet-summary` | Đầu ra mẫu 3 hệ điều hành × có/không panel kiểm bằng schema (`NFR-CMP-004`) |
| `qp.assess/1` | `jobs/<job_id>/result.json` → #8, #9 | Đi sâu theo server | Bộ 11 ví dụ điểm rủi ro (`NFR-MNT-002`); giá trị `R`, `delta_R` của ví dụ §6 |
| `qp.plan/1` | `plans/<plan_id>/` → #21–#29 | — | Chuyển trạng thái `T-PLN-*`, `T-CHK-*` (states.md) |
| `qp.fix/1` | `jobs/<job_id>/result.json` → #32 | Kết quả đợt chạy | So dòng văn bản v0.1 với `counts` (`NFR-CMP-001`, trừ ca `rollback --dry-run`); `planned_actions[]` (`TC-PTCH-101`); `restarted[]`, `restart_failures[]` (`TC-PTCH-104`) |
| `qp.migrate/1` | `jobs/<job_id>/result.json`, `backups/<run_id>/switch.json` → #38, #39 | — | Chuyển trạng thái `T-SW-*`; `result.acknowledgement` của `ack` (`AC-UPG-22`, `TC-UPG-111`) |
| `qp.feeds.status/1` | Gọi đồng bộ → #19 | Cột độ tươi của dashboard | `BR-FEED-059` |

## 12. Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| `docs/php-quickpatch/srs/functional-requirements.md` 1.0.1 §2–§11, §15.2, §15.3 | Trường đầu ra của `FR-SCAN-*`, `FR-ASMT-*`, `FR-PLAN-*`, `FR-PTCH-*`, `FR-UPG-*`, `FR-CLI-JSON-001/002`; `restarted[]`, `restart_failures[]` (`FR-PTCH-RST-001`), `planned_actions[]` (`FR-PTCH-RBK-002`), `result.acknowledgement` (`FR-UPG-ACK-001`); `CR-FR-01`, `CR-FR-02`, `CR-FR-05` | Đã đọc 2026-10-22 |
| `docs/php-quickpatch/srs/data-sources-cache-cli.md` §3.5, §6.3, §6.4 | `data` độ tươi, `qp.feeds.status/1`, mã thoát `feeds` | Đã đọc |
| `docs/php-quickpatch/srs/version-scenarios-common.md` §2, §3, §5 | `lifecycle_status`, `priority`, giai đoạn P1–P7, `checklist_item` | Đã đọc |
| `docs/php-quickpatch/srs/environment-playbooks.md` §4.2, §4.3, §5 | `site_binding`, `switch_record`, bước C1–C12, R1–R7, hành động manifest | Đã đọc |
| `docs/php-quickpatch/srs/data-sources-merge-risk.md` §8.2, §8.3, §8.5 | Công thức `R` (`BR-FEED-040`, `BR-FEED-041`), mức rủi ro `CRITICAL`/`HIGH`/`MEDIUM`/`LOW`, thứ tự xếp hạng, ví dụ 1, 3, 4 dùng ở §5.1, §6 | Đã đọc; số học §6 kiểm lại bằng Python 3 (`d` = 70, 435, 1.166 ngày tới 2026-12-31, 2027-12-31, 2029-12-31; `R_raw` 8.2.34 = 60,2) |
| `docs/php-quickpatch/srs/error-matrix.md` 1.1.0 §3.10, §3.11 | `ERR-PTCH-500-01`, `ERR-PTCH-409-01`, `ERR-UPG-409-04` (mã đề xuất chờ `CR-FR-05`, `CR-FR-01`) | Đã đọc |
| `/home/user/php-quickpatch/php-quickpatch.sh` v0.1.0 | Mã thoát, dòng Summary, manifest `copy`/`created`/`untar`/`composer-install`/`npm-ci`/`note`; định dạng ARG1/ARG2 ở ví dụ `planned_actions[]`: `backup_file` dòng 134–141 (`copy` gốc → `files/<đường dẫn>`), `record` dòng 143–147, tên tar `node-<prefix tr / _>.tar.gz` dòng 446, `do_rollback` dòng 807 | Đã đọc |
| JSON Schema 2020-12, https://json-schema.org/draft/2020-12 | URI meta-schema | Kiểm chứng (WebFetch 2026-10-22) |
