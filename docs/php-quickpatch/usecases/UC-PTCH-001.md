---
id: DOC-UC-QP-PTCH-001
title: Đặc tả Use Case UC-PTCH-001 — Vá runtime PHP/Node.js cùng nhánh
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PTCH-001, fix, same-branch, php, nodejs, mitigation, restart, manifest, dry-run]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-ENV-005
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PTCH-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: bước 12 thêm kiểm dịch vụ active sau restart (thăm dò mỗi 1 s, tối đa 15 s) theo `FR-PTCH-RST-001` bản 1.0.1; thêm nhánh 12b (dịch vụ không active sau 15 s → `ERR-PTCH-500-01` đề xuất, issue `critical`, gợi ý `rollback <run_id>`, audit result `failed`, thoát 2, không tự rollback; console `FAILED` + SCR-007); cập nhật hậu điều kiện, bảng BR/FR và ghi chú; đồng bộ tên `FR-CLI-SAFE-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Áp `--dry-run` và xác nhận cho lệnh thay đổi" |

## UC-PTCH-001: Vá runtime PHP/Node.js cùng nhánh

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`). Operator không root chỉ vá được Node.js do chính user cài (tarball/nvm trong `$HOME`); runtime hệ thống nhận issue "needs root" như v0.1.
- **Tác nhân hỗ trợ**: `SYS-03` package manager (`apt-get`, `dnf`/`yum`, `apk`), panel (`restartsrv` của cPanel), systemd; `SYS-02` nodejs.org (tarball + `SHASUMS256.txt`); System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh fix [--only php,node] [--dry-run] [--no-restart] [--no-memlimit]` (kế thừa v0.1 `php_upgrade`, `node_upgrade_prefix`); console SCR-003 → SCR-011 → SCR-006.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: vá 1 runtime trên console ≤ 3 thao tác (chọn finding → xem dry-run → xác nhận, `NFR-USE-001`, KR1.3); trung vị thời gian từ phát hiện tới vá ≤ 24 giờ với finding KEV hoặc CVSS ≥ 9,0 (KR1.2).
  - `PER-04`: 100% lượt vá có manifest backup và audit intent trước thay đổi đầu tiên (`NFR-REL-002`, KR4.1).
  - Chủ site: khi kho chưa có bản vá, runtime được giảm thiểu bằng mitigation ini tạm thời thay vì để nguyên lỗ hổng (`BR-PTCH-004`).
- **Tiền điều kiện (Pre-conditions)**:
  - Runtime ở `vulnerable` (phiên bản < `min_patched_sec`), nhánh còn hỗ trợ, `locked=false` (UC-SCAN-001, UC-ASMT-001).
  - Không có job `write` khác đang `RUNNING` và không có lượt CLI ghi khác giữ `STATE_DIR/.lock`.
  - `STATE_DIR` còn ≥ 50 MB trống cho backup.
  - Console: `serve` chạy root cho runtime hệ thống (`BR-CON-010`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: runtime ở `ok`/`ok-backport`; file mitigation cũ (nếu có) đã gỡ; 100% dịch vụ PHP-FPM/Node.js liên quan đã restart và đạt kiểm tra trạng thái trong ≤ 15 s sau lệnh restart; `STATE_DIR/backups/<run_id>/manifest` + audit intent/result; dòng gợi ý `rollback <run_id>`; mã thoát 0.
  - **Đảm bảo tối thiểu**: khi không đưa được runtime lên bản vá, mitigation ini tạm đã ghi và issue `critical` được báo (mã thoát 1); khi có dịch vụ không đạt kiểm tra trạng thái sau 15 s, mỗi dịch vụ lỗi có issue `critical` `ERR-PTCH-500-01`, có dòng gợi ý `rollback <run_id>`, audit result `failed`, mã thoát 2 (bước 12b); mọi thay đổi file có dòng `copy`/`created` trong manifest để rollback (UC-PTCH-004).
- **Kích hoạt (Trigger)**: Operator bấm "Vá cùng nhánh" trên SCR-003, hoặc chạy `php-quickpatch.sh fix [--only php|node]`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator bấm "Vá cùng nhánh" trên SCR-003 (thao tác 1); console tạo job `fix --json --only php --dry-run` loại `read` (`BR-CON-008`, `FR-CON-SAFE-001`).
2. CLI xác định nhóm gói của build theo nguồn cài (dpkg `php[0-9.]+`, `ea-php[0-9]+`, `lsphp[0-9]+`, `plesk-php[0-9]+`; rpm thêm `alt-php[0-9]+`, `php[0-9]+`; apk `php[0-9]*`) và mốc `min_patched_sec` từ bundle (`FR-PTCH-PHP-002`, `BR-PTCH-002`, `BR-PTCH-001`).
3. CLI in dự kiến: gói sẽ nâng, mitigation sẽ ghi/gỡ, dịch vụ sẽ restart; 0 thay đổi, không ghi manifest (`FR-CLI-SAFE-001`, `BR-CLI-003`).
4. Console hiển thị SCR-011 với 4/4 mục: thay đổi dự kiến, đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác (`NFR-USE-006`).
5. Operator bấm "Xác nhận" trong ≤ 15 phút (thao tác 2); console kiểm dry-run hợp lệ (`BR-CON-005`) và tạo job `fix --json --only php` loại `write`.
6. CLI lấy khoá `flock -x -n` trên `STATE_DIR/.lock`, ghi audit intent (`FR-JOB-AUD-001`).
7. CLI tạo `STATE_DIR/backups/<run_id>/`, ghi manifest với dòng `note` trước thay đổi đầu tiên; `phase = MANIFEST_WRITTEN` (`FR-PTCH-RBK-001`, `BR-SCN-017`).
8. CLI nâng gói cùng nhánh: dpkg → `apt-get install -y -q --only-upgrade -o Dpkg::Options::=--force-confold <gói đã cài của build>`; rpm → `dnf -y -q upgrade '<glob>'` (`yum` khi không có dnf); apk → `apk upgrade --no-cache`; `phase = CHANGING` (`FR-PTCH-PHP-001`).
9. Với runtime Node.js: gói distro/NodeSource → nâng gói; tarball → tải bản mới nhất cùng major từ `SRC-009`, kiểm `SHASUMS256.txt`, sao lưu `bin`, `include`, `lib/node_modules/npm`, `lib/node_modules/corepack`, `share/doc/node` (hành động `untar`) (`FR-PTCH-NODE-001`, `BR-PTCH-005`, `BR-SEC-005`).
10. CLI đánh giá lại trạng thái theo bundle và backport (`BR-PTCH-001`, `BR-SEC-002`); runtime đạt `ok`/`ok-backport`; `phase = VERIFYING`.
11. Còn file `zz-php-quickpatch-mitigation.ini` của lượt trước → CLI `backup_file` rồi xoá file, ghi `copy` vào manifest (`FR-PTCH-MIT-002`).
12. CLI restart dịch vụ: unit PHP-FPM khớp mẫu v0.1 + `php[0-9]+-php-fpm` (Remi SCL), cPanel dùng `restartsrv`, Node.js restart unit/pm2 theo prefix; với từng dịch vụ đã restart, CLI thăm dò mỗi 1 s, tối đa 15 s, tới khi đạt: systemd `systemctl is-active --quiet <unit>` thoát 0; cPanel `/scripts/restartsrv_<svc> --check` thoát 0; pm2 `pm2 jlist` mọi ứng dụng đã reload có `pm2_env.status = online`; không systemd `pgrep -f 'php-fpm: master'`, `pgrep -x 'apache2|httpd'` trả PID (`FR-PTCH-RST-001`, `BR-PTCH-007`).
13. CLI ghi audit result, in dòng gợi ý rollback `<run_id>`, xuất envelope `qp.fix/1`, thoát 0.
14. Console đẩy log qua SSE ≤ 2 s/dòng, chuyển job `SUCCEEDED`, hiển thị kết quả và `run_id` trên SCR-006 (thao tác 3: xem kết quả) (UC-JOB-001).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Gọi bằng CLI**:
  - 1a1. Operator chạy `fix` trực tiếp; `fix` giữ hành vi v0.1 (không hỏi xác nhận, `BR-CLI-003`); Operator nên chạy `fix --dry-run` trước; luồng tiếp tục từ bước 6.
- **1b. Runtime `locked` (`UNKNOWN`/`PRE_RELEASE`)**:
  - 1b1. Runtime nhận `SKIPPED`, `ERR-SCN-422-01`; không vá (`FR-SCN-LOCK-001`).
- **1c. Runtime trong container hoặc playbook `PB-000`**:
  - 1c1. Chỉ cho phép mitigation (bước 10a2); không nâng gói (`BR-ENV-009`, `FR-SCN-ENV-001`).
- **1d. Dữ liệu cũ > 90 ngày**:
  - 1d1. Vá cùng nhánh vẫn được phép; kết quả kèm `ERR-SCN-503-01` (`BR-FEED-005`).
- **5a. Không có dry-run hợp lệ (khác tham số, khác phiên, > 15 phút, `bundle_id`/`scan_fingerprint` đổi)**:
  - 5a1. Console trả 428 `ERR-JOB-428-01`; quay lại bước 1.
- **5b. Đã có job `fix` cùng đối tượng đang chạy, hoặc hàng đợi đủ 20 job**:
  - 5b1. Console trả `ERR-JOB-409-01` hoặc `ERR-JOB-429-01`.
- **6a. Khoá bị lượt CLI ngoài console giữ**:
  - 6a1. Job ở `QUEUED`, thử lại mỗi 5 s; quá 30 phút → `FAILED`, `ERR-JOB-409-02`. Gọi bằng CLI → `ERR-CLI-423-01`, thoát 2.
- **6b. Không ghi được audit intent**:
  - 6b1. CLI huỷ, `ERR-AUD-500-01`, 0 thay đổi (`BR-AUD-004`).
- **6c. Chạy không root với runtime hệ thống**:
  - 6c1. CLI ghi issue `critical` "{label}: needs root (or the hosting panel) to upgrade" (`ERR-PTCH-403-01`) như v0.1, tiếp tục các hạng mục cấp dự án (`BR-PTCH-003`, `BR-CLI-005`).
- **7a. `STATE_DIR` còn < 50 MB**:
  - 7a1. CLI dừng trước thay đổi, `ERR-ENV-507-01`.
- **9a. Kiến trúc máy ngoài `x64`, `arm64`, `armv7l`, `ppc64le`, `s390x`**:
  - 9a1. Issue `high`, không tải tarball (`BR-PTCH-005`).
- **9b. Checksum tarball không khớp `SHASUMS256.txt`**:
  - 9b1. CLI xoá file tải về, `ERR-PTCH-502-01`, runtime giữ nguyên.
- **9c. Node.js cài bằng nvm (PB-016)**:
  - 9c1. Hệ thống tạo mục `SEMI` theo PB-016 cho chủ `$NVM_DIR` duyệt; không tự nâng (`FR-PTCH-NODE-001`).
- **10a. Nâng gói không đưa runtime lên bản vá (kho chưa có bản vá)**:
  - 10a1. CLI ghi issue `critical` `ERR-PTCH-424-01` "Package upgrade did not bring a fixed {runtime} (still {version}); interim mitigation applied."
  - 10a2. CLI ghi `zz-php-quickpatch-mitigation.ini` vào mọi thư mục `conf.d` của build theo luật `mitigations.json` khớp CVE chưa vá, không ghi đè file đã có, ghi `created` vào manifest, bật cờ restart (`FR-PTCH-MIT-001`, `BR-PTCH-004`); `--no-memlimit` bỏ dòng `memory_limit`.
  - 10a3. Lượt kết thúc với mã thoát 1; Operator theo dõi kho hoặc cân nhắc nâng nhánh (UC-PLAN-001).
- **10b. Build không có thư mục `conf.d`**:
  - 10b1. CLI ghi `ERR-PTCH-412-01` "No conf.d scan dir for {bin}; set the mitigation in its php.ini by hand."
- **12a. Có `--no-restart`**:
  - 12a1. CLI ghi issue `high` "chưa restart" (`BR-PTCH-007`).
- **12b. Dịch vụ không đạt kiểm tra trạng thái sau 15 s kể từ lệnh restart (ini mitigation lỗi, gói mới lỗi, directive pool sai)**:
  - 12b1. Với mỗi dịch vụ không đạt, CLI ghi lỗi `ERR-PTCH-500-01` (đề xuất) và issue `critical` "Service {service} is not running 15 seconds after restart; sites may be down. Check its log, then run rollback {run_id} if needed."; không tự rollback (`FR-PTCH-RST-001`).
  - 12b2. CLI ghi audit result `failed` (`BR-AUD-001`), in dòng gợi ý `rollback <run_id>`, xuất envelope `qp.fix/1`, thoát 2 (`BR-CLI-004`).
  - 12b3. Console chuyển job sang `FAILED` với `ERR-JOB-500-01` (`BR-JOB-008`); SCR-006 hiển thị `ERR-PTCH-500-01` theo dịch vụ và liên kết sang SCR-007, nơi Operator bấm Rollback lượt `<run_id>` (UC-PTCH-004).
- **14a. Operator bấm "Huỷ" khi job đang ở `MANIFEST_WRITTEN`/`CHANGING`/`VERIFYING`**:
  - 14a1. Console trả 423 `ERR-JOB-423-01` (`BR-JOB-004`); ngoài vùng tới hạn → huỷ theo UC-JOB-002.
- **14b. Job vượt 3.600 s, thoát 2, hoặc bị gián đoạn**:
  - 14b1. Job `FAILED`/`INTERRUPTED` với `ERR-JOB-504-01`, `ERR-JOB-500-01` hoặc `ERR-JOB-500-02`; Operator xem manifest và rollback khi cần (UC-PTCH-004).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-USE-001`: ≤ 3 thao tác trên console; `NFR-USE-006`: SCR-011 đủ 4/4 mục.
- `NFR-PERF-002`: tạo job P95 ≤ 1.500 ms; `NFR-PERF-003`: log hiển thị ≤ 2 s P95.
- `NFR-REL-002`, `NFR-REL-004`: audit intent/result 100%; không có 2 job ghi cùng `RUNNING` trên 1 máy chủ.
- `NFR-CMP-001`, `NFR-CMP-005`: hành vi `fix` v0.1 giữ nguyên; chạy được khi không có Python 3.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-PTCH-001`, `BR-PTCH-002` | Mốc vá từ bundle; nhóm gói theo nguồn cài | 2, 10 |
| `BR-PTCH-003`, `BR-CLI-005` | Giới hạn theo quyền và môi trường | 6c |
| `BR-PTCH-004` | Mitigation tạm | 10a, 11 |
| `BR-PTCH-005`, `BR-SEC-005` | Vá Node.js tarball, kiểm checksum | 9 |
| `BR-PTCH-007` | Restart sau vá cùng nhánh; `--no-restart` → issue `high` | 12, 12a, 12b |
| `BR-CLI-004` | Mã thoát (2 khi dịch vụ không active sau restart) | 12b |
| `BR-SCN-008`, `BR-SCN-017` | Vá cùng nhánh là mục `AUTO`; ghi manifest | 7, 8 |
| `BR-SEC-002` | Điều kiện `ok-backport` | 10 |
| `BR-CON-005`, `BR-CLI-003` | Dry-run trước thay đổi | 1–5 |
| `BR-JOB-001`, `BR-JOB-002`, `BR-JOB-004`, `BR-JOB-008` | Đồng thời, khoá, huỷ, timeout 3.600 s, ánh xạ mã thoát | 5, 6, 12b, 14 |
| `BR-AUD-001`, `BR-AUD-004` | Ghi audit, đóng khi lỗi | 6, 12b, 13 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | 1, 4, 5 |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | 3, 1a |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | 2 |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | 7 |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | 8, 10 |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | 9 |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | 10a |
| `FR-PTCH-MIT-002` | Tự gỡ mitigation khi đã vá | 11 |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | 12, 12a, 12b |

### Giao diện và API liên quan
- Màn hình: `SCR-003` (nút "Vá cùng nhánh"), `SCR-011` (dry-run + xác nhận), `SCR-006` (log, kết quả).
- API: `POST /api/v1/jobs` (`action=fix`, `dry_run=true` rồi `confirm_dry_run_job_id`), `GET /api/v1/jobs/{job_id}`, `GET /api/v1/jobs/{job_id}/events`.

### Quan hệ với use case khác
- `<<extend>>` UC-ASMT-001 (nút "Vá cùng nhánh"); được gọi bởi mục P2 vá cùng nhánh của UC-PLAN-003 (`BR-UPG-006`).
- `<<include>>` UC-CON-003 và UC-JOB-001; hoàn tác bằng UC-PTCH-004.

### Ghi chú và tài liệu tham chiếu
- Hành vi v0.1 đã kiểm chứng trên `php-quickpatch.sh` (881 dòng): thông điệp "needs root (or the hosting panel) to upgrade" (dòng 393); không root chỉ nâng Node.js có binary nằm trong `$HOME`, ngược lại issue "needs root to upgrade" (dòng 492); `record note "apt upgraded: … (packages are not downgraded by rollback)"` (dòng 313).
- Sửa lỗi v0.1 trong v2: mẫu unit Remi `php84-php-fpm` và biểu thức dpkg `ea-php` trên cPanel chạy Ubuntu (`CR-SRS-07`).
- Kiểm dịch vụ sau restart là hành vi mới của v2: v0.1 `restart_php_services` (dòng 759–780) và `restart_node_services` (dòng 782–796) chỉ gọi `run systemctl restart`/`restartsrv`/`pm2 reload all` và không kiểm trạng thái sau restart. Mã `ERR-PTCH-500-01` là mã **đề xuất** tại DOC-SRS-QP-FR-001 §15.1 (bản 1.0.1, chờ PO duyệt), chưa có trong `error-matrix.md`; kiểm thử bắt buộc tại DOC-SRS-QP-FR-001 §15.3 mục 4.
- Mâu thuẫn đã ghi: dry-run `fix` trên runtime chưa vá thường thoát 1; thiết kế API chấp nhận `SUCCEEDED_WITH_ISSUES` có `result.preview` và `result.errors[]` rỗng (DOC-API-QP-001 §6.2 mục 3, chờ PO + Dev).
