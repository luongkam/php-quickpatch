---
id: DOC-UC-QP-UPG-003
title: Đặc tả Use Case UC-UPG-003 — Chuyển Apache mod_php sang PHP-FPM
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-003, apache, mod_php, php-fpm, mpm-event, pb-006, server-wide]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-SCN-PHP-001
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-003 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-UPG-003: Chuyển Apache mod_php sang PHP-FPM

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01` người vận hành VPS).
- **Tác nhân hỗ trợ**: `SYS-03` Apache (`apachectl`, `a2enmod`/`a2dismod`, `a2enconf`), package manager (`apt-get install php$OLD-fpm`), systemd; các vhost trên máy (nhận health check `GET`); System: Job runner.
- **Phạm vi (Scope)**: bước 1 của playbook PB-006 — chuyển Apache từ `mod_php` sang PHP-FPM **cùng phiên bản `$OLD`** cho toàn máy chủ; mục `SEMI` có xác nhận kép trong kế hoạch.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng); thay đổi toàn máy chủ.
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`: sau bước này, từng site chuyển được sang `$NEW` theo PB-005 (UC-UPG-002) thay vì chuyển toàn bộ vhost cùng lúc (`BR-SCN-047`).
  - Khách truy cập mọi site trên máy: gián đoạn trong thời gian restart Apache được đo và ghi báo cáo; health check mọi vhost 600 s; không đạt → khôi phục `mod_php` và restart lại.
  - Chủ site: tool không ghi `.htaccess` trong docroot; directive `php_value`/`php_flag` ngoài khối `IfModule` được liệt kê để sửa thủ công (`C-ENV-02`).
- **Tiền điều kiện (Pre-conditions)**:
  - Máy chủ có site chạy `mod_php` (PB-006: `apachectl -M` có `php_module`/`php7_module`/`php5_module`).
  - Điều kiện chặn P6-1: 0 dòng `php_value`, `php_flag`, `php_admin_value`, `php_admin_flag` ngoài khối `<IfModule mod_php*.c>`/`<IfModule php*_module>` trong `.htaccess` và vhost.
  - Điều kiện P6-2: gói `php$OLD-fpm` có trong kho; P6-3: khác biệt `php.ini` giữa SAPI `apache2` và `fpm` của `$OLD` đã được sao chép.
  - Kế hoạch `approved`/`in_progress`; Operator root; Debian/Ubuntu (RHEL: các bước ở mức `MANUAL`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: Apache chạy MPM `event` + `proxy_fcgi` với PHP-FPM `$OLD`; mọi vhost đạt `HC-C1`, `HC-C2`, `HC-C5`, `HC-C7` trong 600 s; báo cáo thời gian gián đoạn; mục bước 1 PB-006 `DONE`; sau ≥ 24 giờ không rollback, site được phép chuyển sang `$NEW` (UC-UPG-002).
  - **Đảm bảo tối thiểu**: khi không đạt, liên kết module/conf được khôi phục theo manifest và Apache restart lại với `mod_php`; health check lại 1 vòng.
- **Kích hoạt (Trigger)**: Operator bấm "Chạy" trên mục "Chuyển Apache mod_php sang PHP-FPM" ở SCR-004 (sinh bởi UC-PLAN-001 khi phát hiện `mod_php`).

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chọn mục bước 1 PB-006 và bấm "Chạy"; hệ thống kiểm P6-1, P6-2, P6-3 và hiển thị kết quả (`FR-UPG-SWT-003`).
2. Hệ thống chạy dry-run: liệt kê module sẽ bật/tắt, liên kết `mods-enabled`/`conf-enabled` sẽ đổi, vhost bị ảnh hưởng (≤ 50 hoặc mẫu), module Apache đang bật cần MPM `prefork`, thời gian gián đoạn dự kiến; SCR-011 hiển thị.
3. Operator xác nhận kép bằng cách gõ lại nhánh PHP hiện tại `$OLD` (`BR-CON-006`); hệ thống ghi audit cả 2 bước.
4. CLI lấy khoá độc quyền, ghi audit intent, sao lưu toàn bộ liên kết trong `/etc/apache2/mods-enabled/`, `/etc/apache2/conf-enabled/`, `apache2.conf`, file vhost; ghi manifest.
5. CLI cài `php$OLD-fpm` và extension tương ứng `$OLD_BIN -m` (bước 1.1).
6. CLI tạo pool theo từng site (hoặc giữ pool `www` chung khi Operator chọn), đặt `user` của pool = user Apache để giữ hành vi quyền file (bước 1.2).
7. CLI chạy `a2dismod php$OLD`, `a2dismod mpm_prefork`, `a2enmod mpm_event proxy_fcgi setenvif`, `a2enconf php$OLD-fpm`; ghi `link`/`created` cho mọi liên kết (bước 1.3).
8. CLI chạy `apachectl configtest` (bước 1.4).
9. CLI chạy `systemctl restart apache2` (đổi MPM dùng restart, không graceful) và đo thời gian gián đoạn (bước 1.5).
10. CLI health check mọi vhost (≤ 50 vhost; > 50: vhost có `hc_url` + 50 vhost chọn ngẫu nhiên) theo `HC-C1`, `HC-C2`, `HC-C5`, `HC-C7` trong 600 s (bước 1.6).
11. Health check ĐẠT; CLI ghi audit result, báo cáo thời gian gián đoạn, đặt mục `DONE`, thoát 0.
12. Sau ≥ 24 giờ không rollback, hệ thống mở các mục chuyển từng site sang `$NEW` theo PB-005 (UC-UPG-002).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. P6-1 không đạt (có `php_value` ngoài `IfModule`)**:
  - 1a1. Hệ thống liệt kê file/dòng, đề xuất chuyển giá trị sang `php_admin_value[...]` trong pool; tạo mục `MANUAL` cho Operator sửa `.htaccess`; mục bước 1 bị chặn tới khi mục `MANUAL` `DONE`.
- **1b. P6-2 không đạt (nhánh `$OLD` EOL, kho không còn `php$OLD-fpm`)**:
  - 1b1. Hệ thống trả `ERR-SCN-412-02` "Site {vhost} đang chạy mod_php; cần chuyển sang PHP-FPM trước khi đổi phiên bản."; phương án còn lại: PB-013 (container) hoặc máy chủ mới.
- **1c. Máy RHEL-family**:
  - 1c1. Các bước tương ứng (`/etc/httpd/conf.modules.d/*php*.conf`, `00-mpm.conf`) chỉ ở mức `MANUAL` (lệnh chưa kiểm chứng, `BR-ENV-010`).
- **2a. Module Apache đang bật chỉ chạy với MPM `prefork`** (vd `mod_ruid2`, `mod_itk` — danh sách chưa kiểm chứng):
  - 2a1. Hệ thống liệt kê module (`apachectl -M`) để Operator duyệt trước khi xác nhận.
- **3a. Gõ lại sai nhánh hoặc dry-run quá 15 phút**:
  - 3a1. Console trả 428 `ERR-JOB-428-01` (`retype_mismatch`/`expired`).
- **4a. Không ghi được audit intent hoặc `STATE_DIR` < 50 MB**:
  - 4a1. Dừng trước thay đổi với `ERR-AUD-500-01` hoặc `ERR-ENV-507-01`.
- **5a. Cài `php$OLD-fpm` thất bại**:
  - 5a1. `ERR-ENV-424-01`; 0 thay đổi cấu hình Apache.
- **6a. Pool không qua `php-fpm$OLD -t` hoặc FPM không `active` sau 15 s**:
  - 6a1. `ERR-ENV-500-01`; khôi phục theo manifest.
- **8a. `apachectl configtest` thất bại**:
  - 8a1. CLI khôi phục liên kết module/conf trong ≤ 5 s, không restart, `ERR-ENV-500-02`.
- **10a. Health check không đạt ở ≥ 1 vhost**:
  - 10a1. CLI khôi phục liên kết module/conf theo manifest, `systemctl restart apache2`, health check lại 1 vòng (bước 1.7); kết quả `ROLLED_BACK` với `ERR-SCN-500-01`.
  - 10a2. Khôi phục thất bại hoặc vhost vẫn lỗi → `ERR-HC-500-02` (Critical), khoá chuyển site (`ERR-UPG-423-01`).
- **10b. Vhost không có host hợp lệ, hoặc 5 mẫu baseline khác mã HTTP / có 5xx**:
  - 10b1. Vhost bị loại khỏi tập mẫu kèm cảnh báo `ERR-HC-412-03`/`ERR-HC-412-02` (Low); trang chủ của vhost có `hc_url` khai báo vẫn bắt buộc.
- **11a. Job vượt 1.200 s**:
  - 11a1. Job `FAILED` với `ERR-JOB-504-01` (timeout nhóm `migrate switch`, `BR-JOB-008`).

### Yêu cầu đặc biệt (Special Requirements)
- Thời gian gián đoạn do restart Apache được đo và ghi vào báo cáo (chưa có chỉ tiêu định lượng trong SRS — xem ghi chú).
- `NFR-ENV-05`: manifest trước thay đổi; `NFR-REL-002`: audit intent/result.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCN-047` | Site chạy `mod_php` phải chuyển sang PHP-FPM trước khi đổi phiên bản | 1, 12 |
| `BR-CON-006` | Xác nhận kép cho PB-006 bước 1 | 3 |
| `BR-ENV-005` | Kiểm cú pháp trước reload/restart | 8 |
| `BR-ENV-006` | Ngoại lệ: đổi MPM cần restart | 9 |
| `BR-ENV-010` | Lệnh chưa kiểm chứng chỉ ở `MANUAL`/`SEMI` | 1c, 2a |
| `BR-SCN-017`, `BR-SCN-046` | Manifest; sao chép ini/pool | 4, 6 |
| `BR-HC-002`, `BR-HC-010`, `BR-HC-012` | Chỉ GET; tự rollback; tải tối đa | 10 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | 1–12 |

### Giao diện và API liên quan
- Màn hình: `SCR-004` (mục bước 1 PB-006), `SCR-011` (xác nhận kép), `SCR-006`.
- API: `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs` với `confirm_retype` = nhánh PHP hiện tại.

### Quan hệ với use case khác
- Được sinh bởi UC-PLAN-001 (extension 9f); là tiền đề của UC-UPG-002; `<<include>>` UC-CON-003, UC-JOB-001.

### Ghi chú và tài liệu tham chiếu
- Các bước 1.1–1.7 và điều kiện P6-1..P6-3: [environment-playbooks-os.md §7](../srs/environment-playbooks-os.md); `FR-UPG-SWT-003`: [functional-requirements.md §8.2](../srs/functional-requirements.md).
- Chưa định lượng: SRS chưa có ngưỡng thời gian gián đoạn chấp nhận được khi restart Apache ở bước 1.5; đề xuất QA đo trên máy 2 vCPU / 2 GB RAM với 50 vhost rồi PO chốt ngưỡng (câu hỏi mở mới, chưa có mã).
