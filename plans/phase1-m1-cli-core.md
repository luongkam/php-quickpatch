# M1 — Lõi CLI: khung repo, envelope `--json`, JSON Schema, test harness, tương thích v0.1

Mục tiêu: dựng khung mã v2 theo spec §2.1; mọi lệnh v0.1 (`scan`, `fix`, `rollback`) chạy như cũ và thêm `--json` theo DOC-API-QP-005; audit chuỗi hash, khoá đọc/ghi; bộ test Bash + `python3 -m unittest` chạy được trong container.

## 1. Tài liệu chính
spec §2.1, §2.5, §3.3.2; `api/api-spec-cli-json.md` §2–§5, §8; `srs/functional-requirements.md` §2, §7, §10, §11; `srs/business-rules.md` (`BR-CLI-*`, `BR-AUD-*`, `BR-JOB-002`, `BR-PTCH-*`, `BR-SEC-006`); `srs/error-matrix.md` (`ERR-CLI-*`, `ERR-PTCH-*`, `ERR-AUD-*`).

## 2. Thiết kế
- `php-quickpatch.sh` giữ là 1 file Bash (chạy được khi chỉ chép 1 file như v0.1) nhưng tách hàm theo nhóm; bộ ghi JSON thuần Bash: `json_str` escape `\`, `"`, U+0000–U+001F dạng `\uXXXX`; các mảng kết quả gom thành chuỗi JSON.
- `--json`: stdout chỉ 1 tài liệu JSON; dòng `[OK]/[WARN]/[VULN]/[i]` chuyển sang stderr và log (`FR-CLI-JSON-001`, `BR-CLI-002`). Không `--json` → đầu ra văn bản giống v0.1.1.
- Envelope: `schema`, `schema_version`, `tool`, `generated_at`, `host`, `command{name, subcommand, argv (đã che), job_id, actor}`, `dry_run`, `exit_code`, `data`, `catalog_version`, `result`, `issues[]`, `errors[]`, `warnings[]`. `data`/`catalog_version` = `null` + cảnh báo `ERR-FEED-503-01` cho tới M2/M3.
- `runtime_id` = `<php|node>:` + 12 hex đầu SHA-1 của `readlink -f`; `project_id` = 12 hex SHA-1 đường dẫn.
- Lệnh `schema <lệnh>` in file `share/php-quickpatch/schemas/qp.<lệnh>.v1.schema.json`. Schema viết cho `scan`, `fix` (dùng cho cả `rollback`), `assess`, `plan`, `migrate`, `feeds.status`, `audit`, `report` (các lệnh chưa làm có schema trước, test hình dạng dần theo mốc).
- Bộ kiểm JSON Schema 2020-12 tối thiểu viết bằng Python stdlib (`tests/python/jsonschema_lite.py`: `type`, `required`, `properties`, `items`, `enum`, `pattern`, `allOf`, `$ref` nội bộ, `additionalProperties`, `const`, `minimum/maximum`) — không cài gói pip.
- Khoá (`BR-JOB-002`, `CR-SRS-06`): lệnh đọc (`scan`, `fix --dry-run`, `rollback --dry-run`) `flock -s -n`; lệnh ghi `flock -x -n`; bận → `ERR-CLI-423-01`, thoát 2.
- `fix`/`rollback` (PTCH): giữ hành vi v0.1 và thêm: thư mục lượt nguyên tử (`FR-PTCH-RBK-001`, `ERR-PTCH-409-01`); `rollback --json` + `planned_actions[]`; `untar` chỉ restart Node khi `ARG2/bin/node` tồn tại; nhóm gói `ea-php` cho dpkg (`CR-SRS-07`); mẫu unit Remi `php[0-9]+-php-fpm` và kiểm dịch vụ active sau restart ≤ 15 s (`FR-PTCH-RST-001`, `ERR-PTCH-500-01`); WordPress sao lưu tar core + plugin (`FR-PTCH-WP-001`, `reversible=partial`); `docker-created` (`FR-PTCH-DKR-002`); kiểm dung lượng `STATE_DIR` ≥ 50 MB trước sao lưu (`ERR-ENV-507-01`).
- Audit (`FR-JOB-AUD-001`): Bash ghi `STATE_DIR/audit/audit-YYYYMM.jsonl` dưới `flock -x audit/.lock`, chuỗi `prev_hash`/`hash` theo `BR-AUD-003`; bản Python dùng chung định nghĩa (`qplib/audit.py`) cho `audit list|verify` (`FR-JOB-AUD-002/003`) và cho console sau này; `audit_anchor` trong envelope của job ghi.
- Python được gọi từ CLI: `feeds|assess|plan|report|audit|serve` → `python3 share/php-quickpatch/qp-feeds.py` (hoặc console); thiếu Python ≥ 3.6 → `ERR-CLI-424-01`.

## 3. Công việc
1. Khung thư mục `share/php-quickpatch/{qp-feeds.py,qplib/,console/,catalog/,schemas/}`, `tests/{bash,python,fixtures}`.
2. Bộ ghi JSON Bash + envelope; `--json` cho `scan`, `fix`, `rollback`; lệnh `schema`.
3. `scan --json`: `runtimes[]` (PHP/Node, `install_source`, `extensions`, `sapis`, `ini_scan_dirs`, `abi`, `npm_version`), `projects[]`, `containers[]`, `webshell_findings[]` (SHA-256, mtime, size), `dependency_findings[]` (OSV như v0.1), `summary`.
4. `fix --json`: `actions[]`, `runtimes_after[]`, `mitigations[]`, `restarts[]`, `restarted[]`, `restart_failures[]`, `counts`, `rollback_hint`, `preview` + `fingerprint` khi `--dry-run`.
5. Thay đổi PTCH liệt kê ở §2.
6. Audit Bash + Python, `audit list|verify` (đặt trong `qp-feeds.py`).
7. `FR-CLI-ENV-001`: kiểm Bash ≥ 4.3, `flock`; Python cho lệnh cần.
8. `FR-CLI-SAFE-001`: khung xác nhận `y/N` khi có TTY / `--yes` khi không TTY cho lệnh ghi mới (dùng từ M2).
9. Test: hồi quy v0.1 (so dòng văn bản và `counts`, `NFR-CMP-001`), schema, escape JSON, khoá, audit, PTCH với stub lệnh hệ thống.

## 4. Tiêu chí nghiệm thu
- Mọi FR ở bảng §6 có test tự động; các ca `TC-*` liệt kê được ánh xạ vào tên test.
- `scan --json`, `fix --dry-run --json`, `rollback --dry-run --json` hợp lệ theo schema; stdout đúng 1 tài liệu JSON; chuỗi có ký tự điều khiển/ngoặc kép được escape đúng (`TC-CLI-002`, `TC-CLI-003`).
- Không `--json`: đầu ra văn bản và mã thoát giống v0.1.1 trên cùng fixture (`NFR-CMP-001`).
- Audit: sửa 1 bản ghi → `audit verify` báo `seq` lệch (`ERR-AUD-409-01`); neo phát hiện cắt đuôi.
- `shellcheck -S warning` sạch; test v0.1.1 vẫn xanh.

## 5. Chưa thử được trên máy thật (dự kiến)
Restart PHP-FPM/Apache bằng systemd, `restartsrv_*` của cPanel, pm2, `docker exec/restart`, nâng gói thật bằng apt/dnf/apk: thử bằng stub ghi lại lệnh.

## 6. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | P0 | `US-CLI-01` | `AC-CLI-01`, `AC-CLI-02`, `AC-CLI-03` | TC-CLI-001, TC-CLI-002, TC-CLI-003 |
| `FR-CLI-JSON-002` | Công bố JSON Schema | P1 | `US-CLI-02` | `AC-CLI-04`, `AC-CLI-05`, `AC-CLI-06` | TC-CLI-004, TC-CLI-005, TC-CLI-006 |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | P0 | `US-CLI-03` | `AC-CLI-07`, `AC-CLI-08`, `AC-CLI-09`, bổ sung | TC-CLI-007, TC-CLI-008, TC-CLI-009, TC-CLI-101 |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | P0 | `US-CLI-10` | `AC-CLI-28`, `AC-CLI-29`, `AC-CLI-30` | TC-CLI-028, TC-CLI-029, TC-CLI-030 |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | P0 | `US-CLI-09` | `AC-CLI-25`, `AC-CLI-26`, `AC-CLI-27` | TC-CLI-025, TC-CLI-026, TC-CLI-027 |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | P0 | `US-SCAN-02` | `AC-SCAN-04`, `AC-SCAN-05`, `AC-SCAN-06` | TC-SCAN-004, TC-SCAN-005, TC-SCAN-006 |
| `FR-SCAN-RT-002` | Phát hiện runtime Node.js | P0 | `US-SCAN-02` | `AC-SCAN-04` | TC-SCAN-004 |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | P0 | `US-SCAN-03` | `AC-SCAN-07`, `AC-SCAN-08`, `AC-SCAN-09` | TC-SCAN-007, TC-SCAN-008, TC-SCAN-009 |
| `FR-SCAN-PRJ-002` | Kiểm kê container đang chạy | P0 | `US-SCAN-03` | `AC-SCAN-07`, `AC-SCAN-09` | TC-SCAN-007, TC-SCAN-009 |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | P0 | `US-SCAN-04` | `AC-SCAN-10`, `AC-SCAN-11`, `AC-SCAN-12` | TC-SCAN-010, TC-SCAN-011, TC-SCAN-012 |
| `FR-JOB-AUD-001` | Ghi audit append-only | P0 | `US-JOB-07` | `AC-JOB-19`, `AC-JOB-20`, `AC-JOB-21` | TC-JOB-019, TC-JOB-020, TC-JOB-021 |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | P1 | `US-JOB-08` | `AC-JOB-22`, `AC-JOB-23`, `AC-JOB-24` | TC-JOB-022, TC-JOB-023, TC-JOB-024 |
| `FR-JOB-AUD-003` | Truy vấn audit | P0 | `US-JOB-08` | `AC-JOB-22`, `AC-JOB-24` | TC-JOB-022, TC-JOB-024 |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | P0 | `US-PTCH-01` | `AC-PTCH-01`, `AC-PTCH-03`, `AC-PTCH-04` | TC-PTCH-001, TC-PTCH-003, TC-PTCH-004 |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | P0 | `US-PTCH-01`, `US-PTCH-01` (FR) / `US-FEED-08` (TC) | `AC-PTCH-01`, `AC-PTCH-02`, bổ sung | TC-PTCH-001, TC-PTCH-002, TC-SCN-105 |
| `FR-PTCH-MIT-002` | Tự gỡ mitigation khi đã vá | P0 | `US-PTCH-02` | `AC-PTCH-05` | TC-PTCH-005 |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | P0 | `US-PTCH-03`, `US-PTCH-03` (FR) / `US-SCN-02` (TC) | `AC-PTCH-08`, `AC-PTCH-09`, `AC-PTCH-10`, bổ sung | TC-PTCH-008, TC-PTCH-009, TC-PTCH-010, TC-SCN-109 |
| `FR-PTCH-DEP-001` | Cập nhật Composer package có lỗ hổng | P0 | `US-PTCH-04` | `AC-PTCH-11`, `AC-PTCH-12` | TC-PTCH-011, TC-PTCH-012 |
| `FR-PTCH-DEP-002` | Cập nhật npm package có lỗ hổng | P0 | `US-PTCH-04` | `AC-PTCH-13` | TC-PTCH-013 |
| `FR-PTCH-WP-001` | Cập nhật WordPress | P0 | `US-PTCH-05` | `AC-PTCH-14`, `AC-PTCH-15` | TC-PTCH-014, TC-PTCH-015 |
| `FR-PTCH-WP-002` | Kiểm tra toàn vẹn WordPress | P0 | `US-PTCH-05` | `AC-PTCH-14`, `AC-PTCH-16` | TC-PTCH-014, TC-PTCH-016 |
| `FR-PTCH-DKR-001` | Nâng tag image cùng nhánh | P0 | `US-PTCH-06` | `AC-PTCH-17`, `AC-PTCH-19` | TC-PTCH-017, TC-PTCH-019 |
| `FR-PTCH-DKR-002` | Ghi mitigation vào container đang chạy | P0 | `US-PTCH-06` | `AC-PTCH-18` | TC-PTCH-018 |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | P0 | `US-PTCH-07` | `AC-PTCH-20`, `AC-PTCH-21`, `AC-PTCH-22` | TC-PTCH-020, TC-PTCH-021, TC-PTCH-022 |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | P0 | `US-PTCH-08` | `AC-PTCH-23`, `AC-PTCH-24`, `AC-PTCH-25` | TC-PTCH-023, TC-PTCH-024, TC-PTCH-025 |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | P0 | `US-PTCH-09` | `AC-PTCH-26`, `AC-PTCH-27`, `AC-PTCH-28` | TC-PTCH-026, TC-PTCH-027, TC-PTCH-028 |

## Trạng thái FR (kết thúc M1, 2026-10-24)

| FR | Trạng thái | Test tự động | Ghi chú / chưa thử trên máy thật |
| :--- | :--- | :--- | :--- |
| `FR-CLI-JSON-001` | Xong | `test_m1_cli.sh` (TC-CLI-001..003), mọi test `--json` | `data`, `catalog_version` = `null` + cảnh báo `ERR-FEED-503-01` tới M2/M3 |
| `FR-CLI-JSON-002` | Xong | TC-CLI-004..006, `test_qplib.py` | 10 schema; schema `assess`/`plan`/`migrate`/`feeds`/`report` soạn theo DOC-API-QP-005, kiểm bằng đầu ra thật khi lệnh có ở M2–M7 |
| `FR-CLI-COMP-001` | Xong | TC-CLI-007, so từng dòng văn bản + mã thoát với v0.1.1 | |
| `FR-CLI-ENV-001` | Xong | TC-CLI-014, 028, 029, 102; `test_v011_state_dir.sh` | Bash < 4.3 chưa thử (container có Bash 5.2) |
| `FR-CLI-SAFE-001` | Xong (khung) | TC-CLI-025..027 qua `confirm` | Chưa có lệnh ghi mới dùng tới (từ M2) |
| `FR-SCAN-RT-001` | Một phần | TC-SCAN-004..006 | `scenario_ids`, `lifecycle_status` ở M2/M3 |
| `FR-SCAN-RT-002` | Một phần | TC-SCAN-004 | `apps[]` (systemd/pm2) ở M5 |
| `FR-SCAN-PRJ-001` | Một phần | TC-SCAN-007, 009 | `site_id` ở M3 |
| `FR-SCAN-PRJ-002` | Xong | TC-SCAN-007, 009 (stub `docker`) | Chưa thử Docker daemon thật |
| `FR-SCAN-WSH-001` | Xong | TC-SCAN-010, 012 | |
| `FR-JOB-AUD-001` | Xong phía CLI | TC-JOB-019..021, `test_audit.py` (Bash + Python cùng chuỗi) | Bản ghi của console ở M6 |
| `FR-JOB-AUD-002` | Xong | TC-JOB-022..024 (1.000 lần sửa 1 byte), neo job/`--anchor` | |
| `FR-JOB-AUD-003` | Xong phía CLI | TC-JOB-022 | API ở M6 |
| `FR-PTCH-PHP-001` | Xong | TC-PTCH-001, 003, 004 (stub dpkg/apt) | dnf/yum/apk chưa thử máy thật |
| `FR-PTCH-PHP-002` | Xong | TC-PTCH-002 (gồm `ea-php` trên dpkg, `CR-SRS-07`) | |
| `FR-PTCH-MIT-002` | Xong | TC-PTCH-005 | |
| `FR-PTCH-NODE-001` | Xong | TC-PTCH-008, 009 (tarball, stub tải) | Gói distro/NodeSource chưa thử máy thật; nvm vẫn là hướng dẫn (mục `SEMI` ở M3) |
| `FR-PTCH-DEP-001` | Xong | TC-PTCH-011, 012 (stub composer, OSV) | |
| `FR-PTCH-DEP-002` | Xong | TC-PTCH-013 | |
| `FR-PTCH-WP-001` | Xong | TC-PTCH-014, 015, 105 (stub wp-cli) | Mốc vá 7.0.7 lấy từ bundle ở M2 (M1 dùng dữ liệu v0.1) |
| `FR-PTCH-WP-002` | Xong | TC-PTCH-016 | |
| `FR-PTCH-DKR-001` | Xong | TC-PTCH-017 | |
| `FR-PTCH-DKR-002` | Xong | TC-PTCH-018, 106 | Chưa thử Docker thật |
| `FR-PTCH-RST-001` | Xong (systemd) | TC-PTCH-020, 022, 104 | Nhánh cPanel `restartsrv --check`, pm2, không systemd đã viết nhưng chưa thử trên máy thật |
| `FR-PTCH-RBK-001` | Xong | TC-PTCH-023, 024, 025, 102, 103 | |
| `FR-PTCH-RBK-002` | Một phần | TC-PTCH-026, 027, 101, 105, 106; `test_v011_*` | Dòng `switch` (R1–R7) ở M5 |

Kết quả chạy: `tests/run.sh` — 497 kiểm tra Bash + 17 test Python, 0 lỗi; `shellcheck -S warning` sạch.
