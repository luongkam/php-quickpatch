# M5 — `migrate`: cài song song, chuyển từng site, health check, rollback site

Mục tiêu: hiện thực mô hình cài song song → chuyển từng site (C1–C12) → health check `HC-C0..C9` trong cửa sổ 600 s → tự rollback (R1–R7) → `rollback-site` 1 lệnh; Debian/Ubuntu + Nginx/Apache-FPM trước, rồi panel (cPanel, Plesk, aaPanel, CyberPanel, DirectAdmin), Node.js (systemd/pm2), Compose.

## 1. Tài liệu chính
`srs/environment-playbooks.md` (PB-000..018, §5 quy trình C/R, manifest), `-os.md`, `-panels.md`, `-container-node.md`, `-healthcheck.md`; `srs/flows-upgrade.md`; `srs/states.md` (lượt chuyển `T-SW-*`); `api/api-spec-cli-json.md` §9; `srs/error-matrix.md` (`ERR-ENV-*`, `ERR-HC-*`, `ERR-UPG-*`).

## 2. Thiết kế
- Toàn bộ `migrate` bằng Bash (C-01: chạy được không cần Python); FastCGI probe dùng Python khi có, không có → bỏ bước probe với cảnh báo theo tài liệu HC.
- Playbook là dữ liệu trong `catalog/playbooks.json` + hàm Bash theo `pb_id`; lệnh "chưa kiểm chứng" (`verified=false`) không chạy ở mức `AUTO`.
- `switches/index.tsv`, `backups/<run_id>/{manifest, switch.json, hc.json}`; `phase` file cho vùng tới hạn; bỏ qua SIGHUP/SIGPIPE từ `MANIFEST_WRITTEN` (`FR-JOB-LOG-001`, phía CLI).
- Test: cây `/etc/nginx`, `/etc/apache2`, `/etc/php`, `/run/php` giả lập được bind-mount vào đúng đường dẫn trong mount namespace riêng (`unshare -m`, như test v0.1.1) — mã sản phẩm không có biến "gốc giả" chỉ để test, stub `systemctl`, `nginx -t`, `apachectl`, `apt-get`, `whmapi1`…; máy chủ HTTP cục bộ giả lập site để thử health check (đổi mã HTTP, độ trễ, kích thước, log lỗi) và tự rollback.

## 3. Tiêu chí nghiệm thu
- Lượt chuyển `PASSED`, `ROLLED_BACK` (mỗi tiêu chí `HC-C0..C9` kích hoạt được), `HC_FAILED_KEPT` (`--no-auto-rollback`), `ROLLBACK_FAILED`, `ABORTED` ở C1–C6; chuyển trạng thái đúng `T-SW-*`.
- Thứ tự ghi manifest đúng §5.4; `migrate rollback` khôi phục gán cũ ≤ 60 s trên fixture.
- `ack`: mở khoá `ERR-UPG-423-01`/`ERR-UPG-409-03` đúng `FR-UPG-SEQ-001`.
- Cài song song thật trong container nếu kho cho phép (vd `php8.4` từ kho Ubuntu/ondrej qua proxy) — nếu không, ghi rõ.

## 4. Chưa thử được trên máy thật (dự kiến)
Reload Nginx/Apache/PHP-FPM bằng systemd thật, API panel thật, pm2/systemd cho Node, `docker compose up`, `mod_php` → FPM trên Apache thật.

## 5. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | P0 | `US-UPG-02` | `AC-UPG-04`, `AC-UPG-05`, `AC-UPG-06`, bổ sung | TC-UPG-004, TC-UPG-005, TC-UPG-006, TC-UPG-102 |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | P0 | `US-UPG-03` | `AC-UPG-07`, `AC-UPG-08`, `AC-UPG-09` | TC-UPG-007, TC-UPG-008, TC-UPG-009 |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | P0 | `US-UPG-04` | `AC-UPG-10`, `AC-UPG-11`, `AC-UPG-12`, `AC-UPG-13` | TC-UPG-010, TC-UPG-011, TC-UPG-012, TC-UPG-013 |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | P0 | `US-UPG-05` | `AC-UPG-14`, `AC-UPG-15`, `AC-UPG-16` | TC-UPG-014, TC-UPG-015, TC-UPG-016 |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | P0 | `US-UPG-12` | `AC-UPG-36`, `AC-UPG-37`, `AC-UPG-38` | TC-UPG-036, TC-UPG-037, TC-UPG-038 |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | P0 | `US-UPG-11`, `US-UPG-11` (FR) / `US-UPG-13` (TC) | `AC-UPG-33`, `AC-UPG-35`, bổ sung | TC-UPG-033, TC-UPG-035, TC-UPG-103, TC-UPG-104 |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | P1 | `US-UPG-13` | `AC-UPG-39`, `AC-UPG-40`, `AC-UPG-41`, bổ sung | TC-UPG-039, TC-UPG-040, TC-UPG-041, TC-UPG-104, TC-UPG-107 |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | P1 | `US-UPG-14` | `AC-UPG-42`, `AC-UPG-43`, `AC-UPG-44` | TC-UPG-042, TC-UPG-043, TC-UPG-044 |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | P0 | `US-UPG-08` | `AC-UPG-24`, `AC-UPG-26`, bổ sung | TC-UPG-024, TC-UPG-026, TC-UPG-106 |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | P0 | `US-UPG-09` | `AC-UPG-27`, `AC-UPG-28`, `AC-UPG-29` | TC-UPG-027, TC-UPG-028, TC-UPG-029 |
| `FR-UPG-HC-003` | Thu baseline | P0 | `US-UPG-08` | `AC-UPG-24`, `AC-UPG-25` | TC-UPG-024, TC-UPG-025 |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | P0 | `US-UPG-10`, `US-UPG-10` (FR) / `US-UPG-08` (TC) | `AC-UPG-30`, `AC-UPG-31`, `AC-UPG-32`, bổ sung | TC-UPG-030, TC-UPG-031, TC-UPG-032, TC-UPG-101, TC-UPG-105, TC-UPG-106 |
| `FR-UPG-HC-005` | Ra quyết định sau health check | P0 | `US-UPG-11`, `US-UPG-11` (FR) / `US-UPG-10` (TC) | `AC-UPG-33`, `AC-UPG-34`, `AC-UPG-35`, bổ sung | TC-UPG-033, TC-UPG-034, TC-UPG-035, TC-UPG-103, TC-UPG-105 |
| `FR-UPG-HC-006` | Báo cáo health check | P0 | `US-UPG-10` | `AC-UPG-30`, bổ sung | TC-UPG-030, TC-UPG-101 |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | P0 | `US-UPG-01`, `US-UPG-01` (FR) / `US-UPG-02` (TC) | `AC-UPG-01`, `AC-UPG-02`, `AC-UPG-03`, bổ sung | TC-UPG-001, TC-UPG-002, TC-UPG-003, TC-UPG-102 |
| `FR-UPG-CFG-002` | Sao chép ini tuỳ chỉnh và extension sang runtime đích | P0 | `US-UPG-03` | `AC-UPG-07`, `AC-UPG-09` | TC-UPG-007, TC-UPG-009 |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | P0 | `US-UPG-06` | `AC-UPG-17`, `AC-UPG-18`, `AC-UPG-19` | TC-UPG-017, TC-UPG-018, TC-UPG-019 |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | P0 | `US-UPG-07` | `AC-UPG-20`, `AC-UPG-21`, `AC-UPG-22`, `AC-UPG-23`, bổ sung | TC-UPG-020, TC-UPG-021, TC-UPG-022, TC-UPG-023, TC-UPG-108 |
| `FR-UPG-ACK-001` | Xác nhận đã xử lý lượt chuyển thất bại (đề xuất, `CR-FR-01`) | P0 | `US-UPG-07` (theo dòng Tham chiếu của story ở [acceptance-criteria-upg.md](../userstories/acceptance-criteria-upg.md); backlog chưa liên kết) | `AC-UPG-22` | Chưa có test case (`TC-UPG-022` bản 1.0.1 chưa có bước `migrate ack`) |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | P2 | `US-UPG-15` | `AC-UPG-45`, `AC-UPG-46`, `AC-UPG-47` | TC-UPG-045, TC-UPG-046, TC-UPG-047 |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | P0 | `US-CLI-07` | `AC-CLI-19`, `AC-CLI-20`, `AC-CLI-21` | TC-CLI-019, TC-CLI-020, TC-CLI-021 |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | P1 | `US-SCAN-05` | `AC-SCAN-13`, `AC-SCAN-14`, `AC-SCAN-15` | TC-SCAN-013, TC-SCAN-014, TC-SCAN-015 |

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).

| FR | Trạng thái | Test | Ghi chú |
| :--- | :--- | :--- | :--- |
| `FR-UPG-PRE-001` | Xong | `test_m5_install.sh` | 5 kiểm `preconditions[]` (đĩa ≥ 2 GB, RAM ≥ 512 MB, root, OS còn hỗ trợ theo bảng ngày hết hỗ trợ, kho có gói đích) + RAM của pool (`pm = ondemand`, §6.7) trong `pb5_pool` |
| `FR-UPG-INST-001` | Xong (PHP Debian/Ubuntu, Node.js tarball) | `test_m5_install.sh`; chạy thật | PHP 8.4 cài thật trong container từ `ppa:ondrej/php` (15 gói, 2 phút): ghim `alternatives`, kiểm liên kết mặc định không đổi, `php8.4-fpm` active. Node.js PB-015 thử bằng tarball giả lập (SHASUMS256, glibc). RHEL/Remi, Alpine, panel: `ERR-ENV-422-01` (chưa có) |
| `FR-UPG-CFG-001` | Xong (Debian layout) | `test_m5_migrate.sh` | Pool `qp-<site_key>` riêng, socket `/run/php/qp-<site_key>-<NEW>.sock`, error_log riêng, `pm.status_path`, chặn trùng tên (`; qp-site-id`) |
| `FR-UPG-CFG-002` | Xong | `test_m5_install.sh` | `conf.d/*.ini` không thuộc gói + giá trị `php.ini` khác bản production → `90-php-quickpatch-from-<OLD>.ini`; bỏ file mitigation; loại directive `BR-SCN-046` (bảng catalog) |
| `FR-UPG-SWT-001` | Xong (Nginx thật; Apache chưa thử) | `test_m5_migrate.sh` (nginx + PHP-FPM 8.3/8.4 thật) | C1–C12, `ABORTED` ở C2/C3/C4/C5/C8, thứ tự manifest §5.4, `phase` = `MANIFEST_WRITTEN`, bỏ qua SIGHUP/SIGPIPE |
| `FR-UPG-SWT-002` | Chưa | — | API panel (cPanel/Plesk/aaPanel/CyberPanel/DirectAdmin): `ERR-ENV-422-01` |
| `FR-UPG-SWT-003` | Chưa | — | `mod_php` → FPM: switch từ chối `ERR-SCN-412-02` |
| `FR-UPG-RBK-001` | Xong | `test_m5_migrate.sh` | `rollback-site` R1–R7 (≤ 60 s, đo ~2 s), `rollback <run_id>` của lượt chuyển = `--purge-pool` |
| `FR-UPG-RBK-002` | Xong | `test_m5_migrate.sh` | Tự rollback cho từng tiêu chí `HC-C0..C9`; `ROLLBACK_FAILED` khi cấu hình khôi phục không qua `nginx -t` |
| `FR-UPG-NODE-001` | Một phần | — | PB-017 (unit systemd: drop-in `ExecStart`, `daemon-reload`, `/proc/MainPID/exe`) đã viết, chưa chạy được: container không có systemd; pm2 chưa có |
| `FR-UPG-DKR-001` | Chưa | — | Compose: chưa có |
| `FR-UPG-HC-001` | Xong | `test_m5_migrate.sh` | Trang chủ + `hc_url` của `sites.d` + `--hc-url`, `expect=`, `size=ignore`, `cachebust=off`, URL host khác/userinfo/fragment bị loại |
| `FR-UPG-HC-002` | Xong | `test_m5_migrate.sh`, `test_m5_migrate.py` | FastCGI probe Python (`qplib/fcgi.py`); không có Python → bỏ bước với `ERR-HC-424-02` |
| `FR-UPG-HC-003` | Xong | `test_m5_migrate.sh` | 5 vòng baseline, `code_b`, `size_b`, spread, P95, chuỗi cấm, W0; `healthcheck --baseline-only` |
| `FR-UPG-HC-004` | Xong | `test_m5_migrate.sh` | Cửa sổ 600 s/60 s (test tua nhanh `sleep`), fail-fast C1/C2/C3/C5/C7/C8/C9, C4/C6 cuối cửa sổ |
| `FR-UPG-HC-005` | Xong | `test_m5_migrate.sh` | PASS → `PASSED`; FAIL → tự rollback / `HC_FAILED_KEPT` (`--no-auto-rollback --reason`) |
| `FR-UPG-HC-006` | Xong | `test_m5_migrate.sh` | `backups/<run_id>/hc.json`, `baseline.json`, `result.hc` |
| `FR-UPG-SEQ-001` | Xong | `test_m5_migrate.sh`, `test_m5_migrate.py` | `plan-gate`: kế hoạch approved/in_progress, stale, thứ tự `site_order[]`, lượt lỗi chưa ack, P3/P4 của site, đích khớp; `ERR-UPG-423-01` toàn máy; `plan run` mục P2/P5 gọi `migrate install/switch` |
| `FR-UPG-ACK-001` | Xong | `test_m5_migrate.sh` | `migrate ack`: `binding_now`, `switch_lock_released`, `next_allowed_sites` |
| `FR-UPG-RMV-001` | Xong | `test_m5_install.sh` | 14 ngày không dùng (site, tiến trình CLI, mtime log/pool, lượt chuyển cuối), `--reason` làm xác nhận thứ hai, lượt chuyển liên quan `rollback_available = false` |
| `FR-CLI-CMD-003` | Xong | `test_m5_migrate.sh` | `migrate` + bí danh `upgrade`, `switch-site`, `healthcheck`, `rollback-site`; `command.subcommand` |
| `FR-SCAN-DRF-001` | Xong | `test_m5_migrate.sh` | `scan` → `drift_warnings[]` (`ERR-SCAN-409-01`) so nhánh + endpoint với lượt `PASSED` gần nhất; cảnh báo cửa sổ health check bị gián đoạn |

Kết quả chạy: xem mục 6.

## 6. Kết quả kiểm thử
- `test_m5_migrate.sh`: 140 kiểm tra trên Nginx 1.24 + PHP-FPM 8.3 (Ubuntu) và 8.4 (ondrej) thật, trong mount namespace riêng (`/etc`, `/var/lib`, `/var/log`, `/run` là overlay; host không đổi).
- `test_m5_install.sh`: install/remove-old PHP (apt-get stub, apt-cache/update-alternatives/php-fpm thật) và Node.js (tarball giả lập).
- `test_m5_migrate.py`: FastCGI client (máy chủ FastCGI giả lập), `plan-gate`, T-CHK-13, `cli_action` P2/P5.
- Chạy thật ngoài test: `migrate install --runtime php --target 8.4 --add-repo --yes` trên container Ubuntu 24.04 (không có `add-apt-repository` dùng được → tool tự thêm PPA, kiểm fingerprint khoá qua Launchpad API + keyserver).

## 7. Chưa thử trên máy thật
- systemd thật: mọi reload/restart đi qua `service` (container không có systemd); Node.js PB-017 (drop-in unit, `systemctl daemon-reload`, `MainPID`) chưa chạy lần nào.
- Apache (`proxy_fcgi`, `apachectl -S`) chưa chạy thật; chỉ Nginx.
- Panel (cPanel, Plesk, aaPanel, CyberPanel, DirectAdmin), Compose, pm2, `mod_php` → FPM: chưa có trong bản này (`ERR-ENV-422-01` / `ERR-SCN-412-02`).
- RHEL/Remi/Alpine (PB-002..004): `migrate install` từ chối.
- Máy có HTTPS thật (chứng chỉ, `--insecure` khi chứng chỉ lỗi): chỉ thử HTTP.
- Gỡ gói thật bằng `apt-get remove` (test dùng stub).
