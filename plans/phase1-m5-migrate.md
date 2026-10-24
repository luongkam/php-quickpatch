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
