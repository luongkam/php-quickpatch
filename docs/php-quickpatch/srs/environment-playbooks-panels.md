---
id: DOC-SRS-QP-ENV-004
title: Playbook theo môi trường — Panel hosting (PB-007..PB-012)
version: 1.0.1
phase: Specification
domain: Security Patch Management
tags: [srs, playbook, cpanel, whm, easyapache4, multiphp, cloudlinux, php-selector, plesk, aapanel, cyberpanel, openlitespeed, litespeed, directadmin, custombuild]
depends_on:
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-SCN-PHP-001
  - BR-ENV-002
  - BR-ENV-010
  - BR-ENV-012
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Playbook theo môi trường — Panel hosting (PB-007..PB-012)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo PB-007..PB-012; lệnh panel kiểm chứng bằng tài liệu chính thức (cPanel OpenAPI, CloudLinux, Plesk CLI, DirectAdmin, LiteSpeed) hoặc mã nguồn chính thức (aaPanel, CyberPanel) ngày 2026-10-22 |
| 1.0.1 | 2026-10-22 | BA Agent | PB-009 §4.2: sửa bước gỡ nhánh cũ — `php_handler --remove` chỉ xoá handler tuỳ chỉnh nên không dùng cho `plesk-php<XY>-*`; thay bằng kiểm tra `--get-usage` rỗng 14 ngày (`BR-SCN-014`) và gỡ thành phần `php<X.Y>` qua Plesk Installer (SEMI, cú pháp CLI Gián tiếp/Chưa chạy thử); bổ sung 2 nguồn ở §8 |

## 1. Giới thiệu
Phần chi tiết của [environment-playbooks.md](environment-playbooks.md) (DOC-SRS-QP-ENV-001) cho máy chủ có panel. Với panel, playbook sở hữu cả lớp cung cấp lẫn lớp gán (`BR-ENV-002`): tool gọi API/CLI chính thức của panel; chỉ sửa file do panel sinh khi mã nguồn hoặc tài liệu của panel cho thấy panel đọc lại đúng file đó (`C-ENV-04`). Sau mỗi lời gọi panel, tool đọc lại giá trị bằng lệnh liệt kê của panel (`BR-ENV-012`). Cột "KC": **Có** = đã đối chiếu tài liệu/mã nguồn chính thức (§8); **Gián tiếp** = chỉ thấy qua trích dẫn kết quả tìm kiếm của trang chính thức không mở được; **v0.1** = có trong `php-quickpatch.sh` v0.1.0; **Chưa** = chưa kiểm chứng, chỉ dùng ở mức `MANUAL`/`SEMI` (`BR-ENV-010`).

## 2. PB-007 — cPanel/WHM EasyApache 4

### 2.1 Nhận diện tự động
| Dấu hiệu | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| cPanel | `-x /usr/local/cpanel/cpanel` | v0.1 |
| Binary EA4 | `/opt/cpanel/ea-php*/root/usr/bin/php` | v0.1 |
| Lệnh API | `whmapi1` (trên CloudLinux phải gọi đường dẫn đầy đủ `/usr/local/cpanel/bin/whmapi1`); `--output=json` cho JSON | Có |

### 2.2 Liệt kê phiên bản và site
| Mục | Lệnh | Trường dùng | KC |
| :--- | :--- | :--- | :--- |
| Phiên bản đã cài | `whmapi1 --output=json php_get_installed_versions` | `data.versions[]` (vd `ea-php84`) | Có |
| Mặc định hệ thống | `whmapi1 --output=json php_get_system_default_version` | `data.version` | Có |
| Site → phiên bản | `whmapi1 --output=json php_get_vhost_versions` | `vhost`, `version` (`ea-phpXY` \| `inherit` \| tên gói tuỳ chỉnh), `php_fpm` (1/0), `php_fpm_pool_parms`, `documentroot`, `account`, `homedir`, `is_suspended`, `phpversion_source.system_default` | Có |
| Handler theo phiên bản | `whmapi1 --output=json php_get_handlers version=ea-phpXY` | `available_handlers` (`suphp`, `cgi`, `dso`, `none`), `current_handler` | Có |

### 2.3 (a) Vá cùng nhánh
| Bước | Lệnh | KC |
| :--- | :--- | :--- |
| 1 | AlmaLinux/Rocky/CloudLinux: `dnf -y -q upgrade 'ea-php$OLDND*'` (v0.1 glob `ea-php[0-9]+*`); CentOS 7: `yum -y -q update` | v0.1 |
| 2 | Ubuntu (cPanel trên Ubuntu): `apt-get install -y -q --only-upgrade <gói ea-php$OLDND-* trạng thái ii>`. Lỗ hổng v0.1: biểu thức của `php_upgrade` cho dpkg (`php[0-9.]+\|lsphp[0-9]+\|plesk-php[0-9]+`) không khớp `ea-php84-…`, nên v0.1 nâng nhầm nhóm `php*`; v2 bổ sung `ea-php[0-9]+` | v0.1 / Có (cú pháp `apt install` của gói `ea-php##`) |
| 3 | Restart: `/scripts/restartsrv_apache_php_fpm` và `/scripts/restartsrv_httpd` | v0.1 |

### 2.4 (b) Cài song song `$NEW`
| Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| 1 | Liệt kê gói khả dụng: `dnf list available 'ea-php$NEWND*'` / `apt search ea-php$NEWND` | Có `ea-php$NEWND` | Có (dạng lệnh theo tài liệu cPanel) |
| 2 (SEMI) | AlmaLinux/Rocky: `dnf install -y ea-php$NEWND ea-php$NEWND-php-fpm ea-php$NEWND-php-<ext> …`; Ubuntu: `apt install --purge ea-php$NEWND ea-php$NEWND-php-fpm …`. Tên gói extension theo mẫu `ea-php##-php-<module>`; danh sách extension lấy từ `$OLD_BIN -m` (`BR-SCN-045`). Thay thế bằng giao diện: WHM » EasyApache 4 » Customize | `php_get_installed_versions` chứa `ea-php$NEWND` | Có (mẫu tên, lệnh `dnf`/`apt install --purge`) / Chưa (tên riêng gói `-php-fpm`) |
| 3 | Không đổi mặc định hệ thống (`php_set_system_default_version` không được gọi) (`BR-SCN-012`) | `php_get_system_default_version` không đổi | Có |

### 2.5 (c) Chuyển 1 site
| Bước | Lệnh | KC |
| :--- | :--- | :--- |
| 1 | Đọc trạng thái cũ của vhost từ `php_get_vhost_versions` → lưu `STATE_DIR/backups/<run_id>/cpanel-vhost.json`; ghi manifest `panel cpanel {"fn":"php_set_vhost_versions","version":"<cũ>","vhost":"<vhost>","php_fpm":<cũ>}` | Có |
| 2 | `backup_file <documentroot>/.htaccess` — cPanel ghi khối handler "php -- BEGIN cPanel-generated handler, do not edit" vào `.htaccess` của domain khi đổi phiên bản bằng MultiPHP (tool không tự ghi file này, `C-ENV-02`) | Có (bài hỗ trợ cPanel) |
| 3 | Kiểm tra RAM khi bật PHP-FPM lần đầu (`php_fpm` 0 → 1): cPanel khuyến nghị chỉ bật PHP-FPM khi máy có ≥ 2 GB RAM khả dụng hoặc ≥ 30 MB mỗi domain; không đạt → giữ `php_fpm` như cũ, ghi cảnh báo | Có |
| 4 | `whmapi1 --output=json php_set_vhost_versions version=ea-php$NEWND vhost=<vhost> php_fpm=<giữ giá trị cũ>`; mỗi lời gọi 1 vhost (API cho phép `vhost-1`, `vhost-2`… nhưng tool chuyển từng site) | Có |
| 5 | Kiểm tra `metadata.result = 1`; đọc lại `php_get_vhost_versions`: `version = ea-php$NEWND` (`BR-ENV-012`) | Có |
| 6 | Xác minh `HC-C0`: phương pháp 2 (worker FPM của `ea-php$NEWND` cho user `account`) hoặc 3 (đọc lại API) | — |
| 7 | Reload: không gọi thêm lệnh khi `HC-C0` đạt; `HC-C0` không đạt sau 10 s → `/scripts/restartsrv_apache_php_fpm` 1 lần rồi kiểm tra lại (việc API tự nạp lại cấu hình: Chưa) | v0.1 / Chưa |

### 2.6 (d) Health check, (e) rollback, sao lưu, quyền, rủi ro
| Mục | Nội dung | KC |
| :--- | :--- | :--- |
| (d) Đầu vào | URL: `vhost` + `documentroot`; log: log lỗi FPM của `ea-php$NEWND` (`/opt/cpanel/ea-php$NEWND/root/usr/var/log/php-fpm/error.log`), log lỗi Apache của domain, file `error_log` trong thư mục script khi PHP ghi log cạnh script | Chưa (đường dẫn log) |
| (e) Rollback | Phát lại `panel`: `whmapi1 php_set_vhost_versions version=<cũ> vhost=<vhost> php_fpm=<cũ>` (`version=inherit` nếu trước đó là `inherit`); đọc lại API; so `.htaccess` với bản sao lưu — khác ở khối cPanel-generated → khôi phục `copy` | Có |
| File sao lưu | `cpanel-vhost.json` (trạng thái API), `<documentroot>/.htaccess`; chỉ đọc: `/var/cpanel/userdata/<account>/<vhost>*` | Có / Chưa (đường dẫn userdata) |
| Restart/reload | (a) `restartsrv` (v0.1); (c)(e) xem bước 7 | v0.1 |
| Root | Bắt buộc (`whmapi1` cục bộ chạy bằng root; gọi API từ xa bằng token nằm ngoài phạm vi Phase 1) | Có |
| Rủi ro | (1) Script hậu giao dịch `009-phpconf.pl` kiểm tra lại khối handler trong `.htaccess` sau mỗi lần cài/gỡ/cập nhật gói PHP hoặc EasyApache — sửa tay `.htaccess` sẽ bị ghi đè; tool chỉ đổi qua API. (2) Handler `dso` không có với gói PHP của RHEL/CloudLinux. (3) Bật PHP-FPM thiếu RAM gây suy giảm hiệu năng toàn máy (bước 3). (4) Gói `ea-php` của nhánh EOL vẫn nằm trên mirror nhưng không nhận bản cập nhật — không chọn làm đích (`BR-SCN-007`) | Có |

## 3. PB-008 — CloudLinux alt-php + PHP Selector

### 3.1 Nhận diện và phạm vi áp dụng
| Dấu hiệu | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| PHP Selector | `selectorctl` có trong `PATH`; file `/etc/cl.selector/selector.conf` | Có |
| Binary alt-php | `/opt/alt/php*/usr/bin/php` (v0.1); `/opt/alt/phpXY/usr/bin/php-cgi`, `/opt/alt/phpXY/usr/bin/lsphp` | v0.1 / Có |
| CageFS | PHP Selector cần CageFS bật cho người dùng | Có |
| Site dùng PHP Selector khi | Trên cPanel: phiên bản MultiPHP của domain = phiên bản mặc định hệ thống (`phpversion_source.system_default = 1` hoặc `version` = `php_get_system_default_version`), handler không phải PHP-FPM, và `selectorctl --user-current --user=<account>` khác `native`. Ngược lại site thuộc PB-007 | Có (điều kiện theo hướng dẫn xử lý sự cố CloudLinux) |

### 3.2 Liệt kê
| Mục | Lệnh | KC |
| :--- | :--- | :--- |
| Phiên bản và đường dẫn | `selectorctl --list` (vd `5.3 5.3.28 /opt/alt/php53/usr/bin/php-cgi`) | Có |
| Trạng thái bật/tắt | `selectorctl --summary` (`e` = enabled, `d` = default) | Có |
| Phiên bản của 1 người dùng | `selectorctl --user-current --user=<user>` | Có |
| Người dùng theo phiên bản | `selectorctl --list-users --version=<X.Y>` | Có |
| Extension của người dùng | `selectorctl --list-user-extensions --user=<user> --version=<X.Y>` | Có |
| Domain → người dùng | PB-007 `php_get_vhost_versions` trường `account` (cPanel); DirectAdmin/Plesk: chủ sở hữu domain của panel | Có |

### 3.3 Hành động
| Hành động | Lệnh | KC |
| :--- | :--- | :--- |
| (a) | `dnf -y -q upgrade 'alt-php$OLDND*'` (v0.1 glob `alt-php[0-9]+*`); sau đó `cagefsctl --force-update` | v0.1 / Chưa (sự cần thiết của `cagefsctl` sau khi cập nhật) |
| (b) (SEMI) | Cài toàn bộ: `yum groupinstall alt-php`; cài 1 nhánh: `dnf install alt-php$NEWND alt-php$NEWND-<ext>`; sau đó `cagefsctl --force-update`; kiểm tra `selectorctl --summary` có dòng `$NEW` trạng thái `e` | Có (`groupinstall`, `--summary`) / Chưa (tên gói từng nhánh) |
| (c) (SEMI) | Ghi manifest `panel cloudlinux {"cmd":"set-user-current","version":"<cũ>","user":"<user>"}` và danh sách extension cũ; `selectorctl --set-user-current=$NEW --user=<user>` (đổi liên kết trình thông dịch của người dùng); bật cùng tập extension trên `$NEW` bằng tuỳ chọn `--enable-user-extensions` (`-e`) | Có (`--set-user-current`, tồn tại `--enable-user-extensions`) / Chưa (cú pháp danh sách extension) |
| (c) phạm vi | `--set-user-current` áp cho **mọi domain của người dùng** (PHP Selector theo người dùng). Tool chỉ cho chuyển khi người dùng có đúng 1 site, hoặc khi người vận hành duyệt chuyển cả nhóm site của người dùng như 1 đơn vị (health check chạy cho mọi site của người dùng); xem DOC-SRS-QP-ENV-001 §11 mục 4 | Có |
| (d) | URL: các domain của người dùng; `HC-C0` phương pháp 4 (tiến trình `lsphp`/`php-cgi` thuộc `/opt/alt/php$NEWND/` chạy dưới user); log: log lỗi Apache của domain, `error_log` cạnh script | Chưa (đường dẫn log) |
| (e) | `selectorctl --set-user-current=<cũ> --user=<user>`; kiểm tra `selectorctl --user-current --user=<user>` = cũ | Có |
| File sao lưu | Đầu ra `--user-current`, `--list-user-extensions` của người dùng (JSON trong thư mục backup); cấu hình selector của người dùng trong CageFS (chỉ đọc) | Có / Chưa (đường dẫn CageFS) |
| Restart/reload | Không restart Apache; thay đổi có hiệu lực khi tiến trình PHP của người dùng khởi tạo lại (thời gian hiệu lực: Chưa) — `HC-C0` xác minh | Chưa |
| Root | Bắt buộc. Người dùng hosting tự đổi trên cPanel » Select PHP Version → mục `MANUAL` | Có |
| Rủi ro | (1) Phạm vi người dùng (ở trên). (2) `mod_lsapi` không tương thích PHP-FPM (CloudLinux yêu cầu tắt PHP-FPM khi dùng `mod_lsapi`). (3) Đổi phiên bản MultiPHP của domain khác mặc định hệ thống làm PHP Selector mất hiệu lực cho domain đó. (4) File `php.ini` tuỳ chỉnh có thể làm hỏng việc đổi phiên bản qua PHP Selector hoặc MultiPHP (cảnh báo trong tài liệu CloudLinux) | Có |

## 4. PB-009 — Plesk

### 4.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Plesk | `-d /usr/local/psa` | v0.1 |
| Binary | `/opt/plesk/php/*/bin/php` | v0.1 |
| Handler PHP đã đăng ký | `plesk bin php_handler --list` (JSON: `plesk bin php_handler --list -json true`) | Có |
| Site dùng 1 handler | `plesk bin php_handler --get-usage -id <handler_id>` | Có |
| Danh sách domain | `plesk bin site --list` | Có |
| Cấu hình 1 site | `plesk bin site --info <domain>` (có trường handler PHP hay không: Chưa) | Có / Chưa |
| Tên handler | Dạng `plesk-php<XY>-fpm`, `plesk-php<XY>-fastcgi`; loại "FPM application" phục vụ được bởi Apache hoặc nginx, "FastCGI application" luôn do Apache phục vụ; có thêm loại "Dedicated FPM application" | Gián tiếp (ID `plesk-php83-fpm` trong bài KB Plesk) / Có (loại handler, tài liệu "Choosing the PHP Handler") |

Thuật toán site → phiên bản: với mỗi handler trong `--list`, gọi `--get-usage`; ghép `domain → handler_id → phiên bản`.

### 4.2 Hành động
| Hành động | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| (a) | Nâng gói `plesk-php$OLDND-*` qua apt/dnf (v0.1 nhận biểu thức `plesk-php[0-9]+`); sau đó `plesk bin php_handler --reread` (tài liệu: dùng lệnh này sau khi binary PHP được nâng cấp) | Phiên bản ≥ bản vá tối thiểu | v0.1 / Có |
| (b) (SEMI) | Liệt kê thành phần: `plesk installer --select-release-current --show-components`; cài: `plesk installer add --components php$NEW` (vd `php8.4`); sau đó `plesk bin php_handler --reread` | `--list` có `plesk-php$NEWND-fpm` | Gián tiếp |
| (c) (SEMI) | Ghi manifest `panel plesk {"cmd":"site -u","domain":"<d>","php_handler_id":"<id cũ>"}`; `plesk bin site -u <domain> -php_handler_id <id mới>` — giữ cùng **loại** handler với cũ (fpm → fpm, fastcgi → fastcgi, dedicated → dedicated); tuỳ chọn có 1 dấu gạch (`-php_handler_id`) | `--get-usage -id <id mới>` chứa domain (`BR-ENV-012`) | Có (cú pháp `site -u … -php_handler_id`) |
| (c) không dùng | `plesk bin php_handler --replace -old-id <cũ> -new-id <mới>` đổi handler cho **mọi** site và gói dịch vụ đang dùng handler cũ → vi phạm chuyển từng site | — | Có |
| (d) | URL theo domain; log lỗi của domain trong `/var/www/vhosts/system/<domain>/logs/` (`error_log`, `proxy_error_log`) | — | Chưa (đường dẫn) |
| (e) | `plesk bin site -u <domain> -php_handler_id <id cũ>`; kiểm tra `--get-usage -id <id cũ>` chứa domain | Đọc lại khớp | Có |
| Gỡ nhánh cũ — điều kiện (P7, `FR-UPG-RMV-001`) | Với mọi handler mà thuật toán §4.1 ánh xạ về nhánh `$OLD` (ID dạng `plesk-php$OLDND-*`, gồm FPM, FastCGI, Dedicated FPM): `plesk bin php_handler --get-usage -id <id>` trả danh sách domain rỗng, liên tục 14 ngày và không có tiến trình thuộc `/opt/plesk/php/$OLD/` (`BR-SCN-014`); không đạt → `ERR-UPG-412-01`, dừng. `--get-usage` chỉ liệt kê domain — việc gói dịch vụ (service plan) còn tham chiếu handler cũ chưa có lệnh liệt kê đã kiểm chứng → người vận hành xác nhận (`MANUAL`) | Danh sách domain rỗng với mọi handler của `$OLD`; người vận hành xác nhận không còn gói dịch vụ dùng handler cũ | Có (`--get-usage`) / Chưa (kiểm tra gói dịch vụ) |
| Gỡ nhánh cũ — thực hiện (SEMI, duyệt) | Gỡ thành phần `php$OLD` (vd `php7.4`) bằng Plesk Installer: `plesk installer remove --components php$OLD` (tên thành phần lấy từ `plesk installer --select-release-current --show-components`), hoặc giao diện Tools & Settings » Updates » Add/Remove Components; sau đó `plesk bin php_handler --reread` (sự cần thiết của `--reread` sau khi gỡ: Chưa). Mức `SEMI` giữ nguyên tới khi QA chạy thử cú pháp CLI (`BR-ENV-010`) | `plesk bin php_handler --list` không còn handler `plesk-php$OLDND-*`; `/opt/plesk/php/$OLD/bin/php` không còn | Có (đường giao diện) / Gián tiếp (cú pháp `installer remove --components`, KB Plesk) / Chưa (chạy thử CLI) |
| Gỡ nhánh cũ — không dùng | `plesk bin php_handler --remove -id <id>`: tài liệu CLI chỉ cho xoá handler **tuỳ chỉnh** và chỉ khi handler không được gói dịch vụ hay site nào dùng. Handler đi kèm thành phần Plesk (`plesk-php<XY>-fpm`, `plesk-php<XY>-fastcgi`) không phải handler tuỳ chỉnh → không gỡ nhánh cũ bằng lệnh này. Tool chỉ dùng `--remove` cho handler tuỳ chỉnh do người vận hành tự đăng ký (`--add`) và chỉ định ID | — | Có |

### 4.3 Sao lưu, reload, quyền, rủi ro
| Mục | Nội dung | KC |
| :--- | :--- | :--- |
| File sao lưu | Đầu ra `php_handler --list -json true` và `--get-usage` của handler cũ (JSON trong thư mục backup); pool FPM của domain `/opt/plesk/php/<X.Y>/etc/php-fpm.d/<domain>.conf` (chỉ đọc) | Có / Chưa (đường dẫn pool) |
| Restart/reload | Plesk tự tái tạo cấu hình web server khi đổi handler qua CLI (Chưa); v0.1 restart unit `plesk-php<X.Y>-fpm` cho (a) | v0.1 / Chưa |
| Root | Bắt buộc | — |
| Rủi ro | (1) Diễn đàn Plesk ghi nhận 503 sau khi đổi handler do thiếu socket FPM, khắc phục bằng `plesk bin domain --update-web-server-settings` hoặc `plesk repair web` (Chưa) — `HC-C2` phát hiện và tự rollback. (2) Tuỳ chọn nginx phục vụ PHP không dùng được với handler FastCGI (Chưa). (3) Subscription đồng bộ với gói dịch vụ có thể đặt lại handler theo gói (Chưa) — `scan` sau cửa sổ health check so sánh lại handler | — |

## 5. PB-010 — aaPanel

### 5.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| aaPanel | `-d /www/server/panel` | v0.1 |
| Phiên bản đã cài | `/www/server/php/<XY>/bin/php` tồn tại (panel dùng chính phép kiểm tra này trong `GetPHPVersion`) | v0.1 / Có |
| Web server của panel | `/www/server/nginx/sbin/nginx`, `/www/server/apache/bin/apachectl`, `/usr/local/lsws/bin/lswsctrl`; chế độ đa web server: cột `service_type` của bảng `sites` | Có |
| Danh sách site | Bảng `sites` (cột `name`, `id`, `parent_id`, `service_type`) trong SQLite `/www/server/panel/data/default.db` — đọc chỉ-đọc | Có |
| Phiên bản PHP của site | Nginx: dòng `include enable-php-<XY>.conf;` (hoặc `enable-php-<XY>-wpfastcgi.conf`) trong `/www/server/panel/vhost/nginx/<site>.conf`; Apache: `unix:/tmp/php-cgi-<XY>.sock\|fcgi://localhost` trong `/www/server/panel/vhost/apache/<site>.conf`; OpenLiteSpeed: `lsphp<XY>` trong `/www/server/panel/vhost/openlitespeed/detail/<site>.conf`. Giá trị `00` = trang tĩnh; `other` = FastCGI tuỳ chỉnh trong `/www/server/panel/vhost/other_php/<site>/enable-php-other.conf` | Có |
| Socket FPM | Mặc định `/tmp/php-cgi-<XY>.sock`; nếu `listen` trong `/www/server/php/<XY>/etc/php-fpm.conf` là cổng TCP thì dùng `127.0.0.1:<cổng>` | Có |

### 5.2 Hành động
| Hành động | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| (a) | PHP của aaPanel được biên dịch dưới `/www/server/php`, không có gói sở hữu → v0.1 ghi mitigation ini và báo "nâng cấp trong panel". Nâng bản vá: App Store » PHP-X.Y » Update (giao diện, `MANUAL`); lệnh nội bộ panel gọi khi nâng: `cd /www/server/panel/install && /bin/bash install_soft.sh <type> update php <X.Y>` (`<type>` 0/1, trên hệ apt panel đổi thành 3/4) | Phiên bản ≥ bản vá tối thiểu | v0.1 / Có (đọc từ mã nguồn `panelPlugin.py`) / Chưa (chạy thử) |
| (b) | App Store » PHP-X.Y » Install (`MANUAL`); hoặc `install_soft.sh <type> install php <X.Y>` (SEMI, Chưa chạy thử). Biên dịch từ mã nguồn — thời gian chưa đo | `/www/server/php/$NEWND/bin/php` tồn tại; `/www/server/nginx/conf/enable-php-$NEWND.conf` tồn tại | Có (đọc mã nguồn) / Chưa |
| (c) (SEMI) | Làm đúng thuật toán `SetPHPVersion` của panel: (1) `backup_file` các file vhost của site; (2) Nginx: thay chuỗi khớp `enable-php-(\w{2,5})\.conf` bằng `enable-php-$NEWND.conf` (giữ hậu tố `-wpfastcgi` nếu có), lặp lại cho `/www/server/panel/vhost/nginx/dir_auth/<site>/*.conf`; Apache: thay `unix:/tmp/php-cgi-<cũ>.sock\|fcgi://localhost` bằng địa chỉ FPM của `$NEWND`; OpenLiteSpeed: thay `lsphp<cũ>` bằng `lsphp$NEWND`; (3) kiểm tra cú pháp (`/www/server/nginx/sbin/nginx -t`, `/www/server/apache/bin/apachectl -t`); (4) reload như panel: `/etc/init.d/nginx reload`, `/etc/init.d/httpd reload`, `/usr/local/lsws/bin/lswsctrl reload` | Đọc lại file: phiên bản = `$NEWND` | Có (mã nguồn `panelSite.py`, `public/common.py`) |
| (d) | URL theo `server_name`; log truy cập `/www/wwwlogs/<site>.log` (Nginx) / `/www/wwwlogs/<site>-access_log` (Apache); log lỗi cùng thư mục; log FPM `/www/server/php/$NEWND/var/log/php-fpm.log` | | Có (log truy cập) / Chưa (log lỗi, log FPM) |
| (e) | Phát lại `copy` các file vhost → kiểm tra cú pháp → reload như bước (c)(4) | Đọc lại file = phiên bản cũ | Có |
| Restart FPM | `/etc/init.d/php-fpm-<XY> reload` | | Có |

### 5.3 Sao lưu, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | `/www/server/panel/vhost/nginx/<site>.conf`, `/www/server/panel/vhost/nginx/dir_auth/<site>/*.conf`, `/www/server/panel/vhost/apache/<site>.conf`, `/www/server/panel/vhost/openlitespeed/detail/<site>.conf` (file nào tồn tại) |
| Root | Bắt buộc |
| Rủi ro | (1) Panel đọc phiên bản PHP trực tiếp từ file vhost (`get_site_php_version`), không lưu trong DB → sửa file theo đúng thuật toán của panel giữ panel và tool nhất quán; thay đổi khác trên giao diện (SSL, rewrite) tái sinh file nhưng giữ dòng `enable-php-XX`. (2) Chế độ `other` (FastCGI tuỳ chỉnh) không chuyển tự động → `MANUAL`. (3) Biên dịch PHP mới tốn CPU/RAM trên máy production (thời gian chưa đo) — đề xuất chạy ngoài giờ cao điểm. (4) Nginx reload của panel có nhánh dự phòng `pkill -9 nginx && /etc/init.d/nginx start` khi reload lỗi (mã nguồn `ServiceReload`) — tool không dùng nhánh này, chỉ dùng `reload` sau `nginx -t` đạt |

## 6. PB-011 — CyberPanel / OpenLiteSpeed / LiteSpeed

### 6.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| CyberPanel | `-d /usr/local/CyberCP` | v0.1 |
| LiteSpeed không panel | `-x /usr/local/lsws/bin/lswsctrl` | v0.1 |
| Phiên bản LSPHP đã cài | `/usr/local/lsws/lsphp<XY>/bin/lsphp` (CyberPanel kiểm tra đúng đường dẫn này trước khi đổi) | Có |
| Danh sách site | `cyberpanel listWebsitesJson` (trường `domain`, `adminEmail`, `ipAddress`, `admin`, `package`, `state`; không có phiên bản PHP) | Có (mã nguồn `cli/cyberPanel.py`) |
| Phiên bản PHP của site | `/usr/local/lsws/conf/vhosts/<domain>/vhost.conf`: OpenLiteSpeed — dòng `path /usr/local/lsws/lsphp<XY>/bin/lsphp` trong khối `extprocessor`; LiteSpeed Enterprise — dòng `AddHandler application/x-httpd-php<XY> .php` | Có (mã nguồn `plogical/vhost.py`) |

### 6.2 Hành động
| Hành động | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| (a) | `apt-get install -y -q --only-upgrade <gói lsphp$OLDND*>` / `dnf -y upgrade 'lsphp$OLDND*'` (v0.1 nhận `lsphp[0-9]+`); restart `/usr/local/lsws/bin/lswsctrl restart` (v0.1) | Phiên bản ≥ bản vá tối thiểu | v0.1 |
| (b) | Kho LiteSpeed chưa có (SEMI, `BR-ENV-004`): tài liệu LiteSpeed dùng `wget -O - https://repo.litespeed.sh \| bash` — tool tải script về `WORK_DIR`, hiển thị nội dung cho người duyệt, không chạy trực tiếp qua ống; cài: Ubuntu/Debian `apt-get install lsphp$NEWND lsphp$NEWND-common lsphp$NEWND-mysql`, RHEL-family `dnf install lsphp$NEWND lsphp$NEWND-common lsphp$NEWND-mysqlnd` (+ `lsphp$NEWND-<ext>`) | `/usr/local/lsws/lsphp$NEWND/bin/lsphp` tồn tại | Có (tài liệu LiteSpeed, ví dụ với `lsphp85`) |
| (c) CyberPanel (SEMI) | `backup_file /usr/local/lsws/conf/vhosts/<domain>/vhost.conf`; ghi `panel cyberpanel {"cmd":"changePHP","domainName":"<d>","php":"<X.Y cũ>"}`; `cyberpanel changePHP --domainName <domain> --php $NEW` (vd `--php 8.4`). Lệnh tự sửa `vhost.conf` (OLS: dòng `path`; Enterprise: dòng `AddHandler`), tạm tạo `/home/<domain>/.lsphp_restart.txt` và khởi động lại LiteSpeed; với chế độ Apache phía sau thì restart dịch vụ PHP-FPM tương ứng | Đọc lại `vhost.conf` chứa `lsphp$NEWND` / `x-httpd-php$NEWND` (`BR-ENV-012`) | Có (mã nguồn) |
| (c) không panel (SEMI) | Sửa dòng `path` của `extprocessor` trong file cấu hình vhost OLS (cùng cách CyberPanel làm) → `lswsctrl restart` | Đọc lại file | Chưa (tên file vhost của OLS độc lập) |
| (d) | `HC-C0` phương pháp 3 (đọc lại `vhost.conf`) và 4 (tiến trình `lsphp` thuộc `/usr/local/lsws/lsphp$NEWND/`); log: `errorlog` khai báo trong `vhost.conf`, log máy chủ `/usr/local/lsws/logs/error.log` | | Chưa (đường dẫn log) |
| (e) | `cyberpanel changePHP --domainName <domain> --php <cũ>`; nếu lệnh lỗi → khôi phục `copy` `vhost.conf` rồi `lswsctrl restart` | Đọc lại file = cũ | Có |

### 6.3 Sao lưu, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | `/usr/local/lsws/conf/vhosts/<domain>/vhost.conf` |
| Restart/reload | CyberPanel `changePHP` khởi động lại LiteSpeed cho **toàn máy chủ** (`reStartLiteSpeed`); aaPanel dùng `lswsctrl reload` cho cùng web server. Thời gian gián đoạn: chưa đo |
| Root | Bắt buộc |
| Rủi ro | (1) Restart LiteSpeed ảnh hưởng mọi site (đo, ghi báo cáo). (2) Tiến trình PHP chế độ "detached" giữ phiên bản cũ đến khi khởi động lại — CyberPanel dùng file `.lsphp_restart.txt` để buộc khởi động lại; `HC-C0` phương pháp 4 xác minh. (3) Khi CyberPanel lưu cấu hình vhost trong Redis (nhánh `redisConf` của mã nguồn), không có file để sao lưu → tool lưu đầu ra `redis-cli get "vhost:<domain>"` vào thư mục backup và hạ mức xuống `MANUAL` (Chưa). (4) Script cài kho qua ống `bash` — chỉ chạy sau khi người duyệt xem nội dung |

## 7. PB-012 — DirectAdmin CustomBuild

### 7.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| DirectAdmin | `-d /usr/local/directadmin` | v0.1 |
| Lệnh CustomBuild | `da build …` (dạng trong tài liệu hiện hành; dạng cũ `./build` trong thư mục `custombuild`) | Có |
| Khe phiên bản | Tối đa 9 khe `php1_release`..`php9_release`; khe không dùng đặt `no`; `php1_release` là phiên bản chính, mặc định cho mọi domain và chạy webapps | Có |
| Đọc khe | `grep -E '^php[1-9]_(release\|mode)=' /usr/local/directadmin/custombuild/options.conf` | Có (tên file `options.conf`) / Chưa (đường dẫn đầy đủ) |
| Bộ chọn phiên bản theo domain | `da config-get php_version_selector` = `1` (bật bằng `da config-set php_version_selector 1` rồi `systemctl restart directadmin`) | Có |
| Phiên bản của domain | `php1_select=<k>` trong `/usr/local/directadmin/data/users/<USER>/domains/<DOMAIN>.conf` (không có dòng → khe 1); subdomain: dòng `sub=php1_select=<k>` trong `<DOMAIN>.subdomains.docroot.override` | Có |
| Binary, socket | `/usr/local/php<XY>/bin/php` (v0.1); socket PHP-FPM theo người dùng `/usr/local/php<XY>/sockets/<USER>.sock` (mẫu `/usr/local/php\|PHP1_RELEASE\|/sockets/\|USER\|.sock` trong template) | v0.1 / Có |

### 7.2 Hành động
| Hành động | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| (a) (SEMI) | Biên dịch lại PHP cùng nhánh: `da build update` (cập nhật danh sách phiên bản của CustomBuild) rồi `da build php` (biên dịch mọi khe đã cấu hình); thời gian biên dịch chưa đo | `/usr/local/php$OLDND/bin/php -v` ≥ bản vá tối thiểu | Có (`da build php`) / Chưa (`da build update`) |
| (b) (SEMI) | Chọn khe trống `k` ≥ 2 (`php<k>_release=no`); **không** đổi `php1_release` (đổi khe 1 = đổi phiên bản mặc định của mọi domain không có `php1_select`). `da build set php<k>_release $NEW`; `da build php`; `da build rewrite_confs` | `/usr/local/php$NEWND/bin/php` tồn tại; socket người dùng tồn tại | Có (`set phpN_release`, `php`, `rewrite_confs`) |
| (b) chế độ | `php1_mode` đặt chế độ (vd `php-fpm`); tài liệu chính thức minh hoạ cho khe 1, khe khác: Chưa | | Chưa |
| (c) (SEMI) | `backup_file` `<DOMAIN>.conf` (và `.subdomains.docroot.override` khi chuyển subdomain); đặt `php1_select=<k>` (thay dòng có sẵn hoặc thêm dòng — đúng cách script mẫu trong tài liệu DirectAdmin); `da build rewrite_confs`. Người dùng cũng tự chọn được ở trang Domain Setup (giao diện) | Đọc lại `php1_select=<k>`; `HC-C0` phương pháp 2 (worker của `php-fpm$NEWND` cho `<USER>`) | Có |
| (d) | URL theo domain; log lỗi Apache/Nginx của domain (`/var/log/httpd/domains/<domain>.error.log`), log PHP-FPM của khe | | Chưa (đường dẫn log) |
| (e) | Phát lại `copy` `<DOMAIN>.conf` → `da build rewrite_confs`; đọc lại `php1_select` | Bằng giá trị cũ | Có |

### 7.3 Sao lưu, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | `/usr/local/directadmin/data/users/<USER>/domains/<DOMAIN>.conf`, `<DOMAIN>.subdomains.docroot.override`, `options.conf` của CustomBuild (trước (b)) |
| Restart/reload | `da build rewrite_confs` tái sinh cấu hình web server cho mọi domain và nạp lại (cơ chế nạp lại: Chưa) |
| Root | Bắt buộc |
| Rủi ro | (1) `rewrite_confs` tác động **toàn máy chủ**: lỗi template ảnh hưởng mọi domain → health check thêm trang chủ của 5 domain khác chọn ngẫu nhiên (DOC-SRS-QP-ENV-001 §11 mục 5). (2) Biên dịch PHP trên production tốn CPU, có thể thất bại do thư viện thiếu. (3) Với `php1_mode=lsphp`, CloudLinux PHP Selector chỉ có hiệu lực theo điều kiện kết hợp với bộ chọn của DirectAdmin (tài liệu DirectAdmin) → site thuộc PB-008. (4) Thời gian `rewrite_confs` với nhiều domain chưa đo (`A-ENV-04`) |

## 8. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22 (UTC); các mục ghi "đọc lại/đọc/tìm kiếm 2026-10-23" được truy cập ngày 2026-10-23 (UTC).

| Nguồn | URL | Dùng cho | Trạng thái |
| :--- | :--- | :--- | :--- |
| cPanel WHM API 1 — `php_set_vhost_versions` | https://api.docs.cpanel.net/specifications/whm.openapi/php/php-php_set_vhost_versions.md | Tham số `version`, `vhost` (`vhost-1`…), `php_fpm`, `php_fpm_pool_parms`; cảnh báo RAM ≥ 2 GB / 30 MB mỗi domain | Kiểm chứng |
| cPanel WHM API 1 — `php_get_vhost_versions`, `php_get_installed_versions`, `php_get_handlers`, `php_get_system_default_version` | https://api.docs.cpanel.net/specifications/whm.openapi/php/php-php_get_vhost_versions.md (và các file `.md` cùng thư mục) | Trường liệt kê | Kiểm chứng |
| cPanel WHM API 1 — giới thiệu | https://api.docs.cpanel.net/whm/introduction.md | `whmapi1 --output=json`; đường dẫn đầy đủ trên CloudLinux | Kiểm chứng |
| cPanel — How to Locate and Install a PHP Version or Extension | https://docs.cpanel.net/ea4/php/how-to-locate-and-install-a-php-version-or-extension/ | Mẫu tên `ea-php##-php-module`; `dnf install` / `apt install --purge`; DSO không có với gói RHEL/CloudLinux | Kiểm chứng |
| cPanel Support — timestamps on htaccess | https://support.cpanel.net/hc/en-us/articles/360049919034 | `009-phpconf.pl` kiểm tra khối handler trong `.htaccess` | Kiểm chứng (qua trích dẫn kết quả tìm kiếm) |
| CloudLinux — Command-line tools / Components | https://docs.cloudlinux.com/cloudlinuxos/command-line_tools/; https://docs.cloudlinux.com/cloudlinuxos/cloudlinux_os_components/ | `selectorctl --list`, `--summary`, `--user-current`, `--set-user-current`, `--list-users`, `--list-user-extensions`, `--enable-user-extensions`; `yum groupinstall alt-php`; `cagefsctl --force-update`; `/etc/cl.selector/selector.conf`; điều kiện MultiPHP = mặc định hệ thống; `mod_lsapi` không tương thích PHP-FPM | Kiểm chứng |
| Plesk CLI — `php_handler` | https://docs.plesk.com/en-US/obsidian/cli-linux/72490/ | `--list [-json true]`, `--get-usage`, `--reread`, `--replace`, `--remove` ("The handler must not be used in service plans or websites", "Only custom handlers can be deleted" — đọc lại 2026-10-23) | Kiểm chứng |
| Plesk — Adding and Removing Plesk Components | https://docs.plesk.com/en-US/obsidian/administrator-guide/74719 | Gỡ thành phần qua Tools & Settings » Updates » Add/Remove Components (đọc 2026-10-23) | Kiểm chứng |
| Plesk KB — How to install/uninstall Plesk components | https://support.plesk.com/hc/en-us/articles/12377969757591 | `plesk installer remove --components php7.0`, `--show-components` (tìm kiếm 2026-10-23) | Gián tiếp (HTTP 403 khi tải trực tiếp; cú pháp lấy từ trích dẫn kết quả tìm kiếm) |
| Plesk CLI — `site` | https://docs.plesk.com/en-US/obsidian/cli-linux/67067/ | `site --list`, `--info`, `-u <domain> -php_handler_id <id>` | Kiểm chứng |
| Plesk CLI — `subscription` | https://docs.plesk.com/en-US/obsidian/cli-linux/using-command-line-utilities/subscription-subscriptions.37768/ | `-php_handler_id` cho subscription | Gián tiếp |
| Plesk — Choosing the PHP Handler | https://docs.plesk.com/zh-CN/obsidian/administrator-guide/75145/ | Loại handler FastCGI/FPM/Dedicated FPM | Gián tiếp |
| Plesk KB | https://support.plesk.com/hc/en-us/articles/12377820871447 (đổi handler hàng loạt, ID `plesk-php83-fpm`); bài KB cài thành phần `plesk installer add --components php8.3` | ID handler, cài PHP | Gián tiếp (HTTP 403 khi tải trực tiếp) |
| Diễn đàn Plesk | https://talk.plesk.com/threads/503-error-after-changing-php_handler_id-for-site.370625/ | Rủi ro 503 | Nguồn cộng đồng, chưa kiểm chứng |
| aaPanel mã nguồn | https://raw.githubusercontent.com/aaPanel/aaPanel/master/class/panelSite.py (`GetPHPVersion`, `GetSitePHPVersion`, `SetPHPVersion`); `class/public/common.py` (`get_site_php_version`, `get_fpm_address`, `ServiceReload`, `default.db`); `class/panelPlugin.py` (`install_soft.sh`) | PB-010 | Kiểm chứng (đọc mã nguồn, chưa chạy thử) |
| CyberPanel mã nguồn | https://raw.githubusercontent.com/usmannasir/cyberpanel/stable/cli/cyberPanel.py (`changePHP`, `listWebsitesJson`); `plogical/vhost.py` (`changePHP`); `managePHP/phpManager.py` (`getPHPString`) | PB-011 | Kiểm chứng (đọc mã nguồn, chưa chạy thử) |
| LiteSpeed — PHP Getting Started | https://docs.litespeedtech.com/lsws/extapp/php/getting_started/ | `repo.litespeed.sh`, gói `lsphp85`, `lsphp85-common`, `lsphp85-mysql(nd)`, đường dẫn `/usr/local/lsws/lsphp85/bin/lsphp` | Kiểm chứng |
| DirectAdmin — PHP, Multiple PHP versions, PHP-FPM | https://docs.directadmin.com/webservices/php/; https://docs.directadmin.com/webservices/php/multiple-php.html; https://docs.directadmin.com/webservices/php/php-fpm.html | `da build set php1_release`, `da build php`, `da build rewrite_confs`, 9 khe, `php_version_selector`, `php1_select`, file override subdomain, socket theo người dùng | Kiểm chứng |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `detect_env`, `discover_php_bins`, `php_upgrade`, `restart_php_services` | Đã đọc |
