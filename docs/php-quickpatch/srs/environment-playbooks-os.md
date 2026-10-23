---
id: DOC-SRS-QP-ENV-003
title: Playbook theo môi trường — Hệ điều hành và web server (PB-001..PB-006)
version: 1.0.2
phase: Specification
domain: Security Patch Management
tags: [srs, playbook, debian, ubuntu, sury, ondrej, rhel, almalinux, rocky, appstream, remi, alpine, nginx, apache, php-fpm, mod_php]
depends_on:
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-SCN-PHP-001
  - BR-SCN-012
  - BR-SCN-016
  - BR-SCN-045
  - BR-SCN-046
  - BR-SCN-047
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Playbook theo môi trường — Hệ điều hành và web server (PB-001..PB-006)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo PB-001..PB-006; lệnh kho Surý, Remi, AppStream, Alpine, cấu hình Debian `php-fpm` kiểm chứng ngày 2026-10-22 |
| 1.0.1 | 2026-10-22 | BA Agent | §6.3: thêm quy tắc đặt tên `<site_key>` (dạng băm SHA-1 khi `site_id` > 48 ký tự hoặc đường dẫn socket > 107 byte), giới hạn `sun_path`/`NAME_MAX`, kiểm tra trước khi ghi pool, ghi ánh xạ vào `switch.json`, ca kiểm thử domain dài; thay `qp-<site_id>` bằng `qp-<site_key>` ở §2.5, §6.4–§6.6; bổ sung nguồn ở §8 |
| 1.0.2 | 2026-10-22 | BA Agent | §2.4 bước 3: ghim giá trị đang dùng của cả nhóm `php` và `php-fpm.sock` (trước đây chỉ `--set php`), tiêu chí `readlink -f /run/php/php-fpm.sock` không đổi; thêm bước 3b đưa site trỏ alias `php-fpm.sock` sang socket có số phiên bản trước bước 5 (ghim không bền khi `php$OLD-fpm` restart hoặc khởi động lại máy, đã chạy thử); cập nhật §2.6 (file sao lưu, rủi ro 3), §6.2 bước 4, ghi chú đồng bộ `CHK-PHP-004-10`; §7.1 hàng MPM: dẫn nguồn PHP manual và đóng gói Debian thay cụm "khuyến nghị phổ biến"; bổ sung 4 nguồn ở §8 |

## 1. Giới thiệu
Tài liệu là phần chi tiết của [environment-playbooks.md](environment-playbooks.md) (DOC-SRS-QP-ENV-001): mô hình 5 hành động, thuật toán nhận diện, manifest, FR/BR/ERR chung nằm ở đó; health check ở [environment-playbooks-healthcheck.md](environment-playbooks-healthcheck.md). Mỗi playbook trình bày: nhận diện → liệt kê site/phiên bản → (a) vá cùng nhánh → (b) cài song song → (c) chuyển 1 site → (d) đầu vào health check → (e) rollback → file sao lưu → restart/reload → quyền → rủi ro. Cột "KC" (kiểm chứng): **Có** = đã đối chiếu tài liệu/mã nguồn chính thức (nguồn ở §8); **v0.1** = hành vi có sẵn trong `php-quickpatch.sh` v0.1.0; **Chưa** = chưa kiểm chứng, chỉ chạy ở mức `MANUAL`/`SEMI` (`BR-ENV-010`).

PB-001..PB-004 là lớp **cung cấp** PHP (cài gói); việc nối site với phiên bản PHP do PB-005 (Nginx/Apache + PHP-FPM) hoặc PB-006 (Apache `mod_php`) đảm nhận.

## 2. PB-001 — Debian/Ubuntu

### 2.1 Nhận diện tự động
| Dấu hiệu | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Họ OS | `. /etc/os-release`; `ID` = `debian`/`ubuntu` hoặc `ID_LIKE` chứa `debian` | Có |
| Trình quản lý gói | `command -v apt-get` (v0.1 `PKG_MGR=apt`) | v0.1 |
| Binary PHP thuộc gói | `dpkg -S "$(readlink -f /usr/bin/php8.3)"` → `php8.3-cli` (v0.1 `pkg_owner`) | v0.1 |
| Kho Ondřej Surý | File trong `/etc/apt/sources.list.d/` chứa `packages.sury.org/php` (Debian, Ubuntu Resolute) hoặc `ppa.launchpadcontent.net/ondrej/php` (Ubuntu Jammy/Noble) | Có |

### 2.2 Liệt kê phiên bản và site
| Mục | Lệnh | KC |
| :--- | :--- | :--- |
| Phiên bản PHP đã cài | `dpkg-query -W -f='${db:Status-Abbrev} ${Package} ${Version}\n' 'php*-cli' 'php*-fpm'` (lọc `ii`) | v0.1 |
| Dịch vụ FPM | `systemctl list-units --type=service 'php*-fpm.service' --no-legend --plain` | Có |
| Pool và socket | `/etc/php/<X.Y>/fpm/pool.d/*.conf`, directive `listen` (mặc định gói: `/run/php/php<X.Y>-fpm.sock`) | Có |
| Site → phiên bản | Theo PB-005 (socket trong `fastcgi_pass`/`SetHandler` → pool → thư mục `/etc/php/<X.Y>/`) hoặc PB-006 | — |
| Mặc định hệ thống | `update-alternatives --query php`; `update-alternatives --query php-fpm.sock` | Có |

### 2.3 (a) Vá cùng nhánh
| Bước | Lệnh | Tiêu chí thành công | KC |
| :--- | :--- | :--- | :--- |
| 1 | `apt-get update -q` | exit 0 | v0.1 |
| 2 | `DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade -o Dpkg::Options::=--force-confold <mọi gói php<X.Y>-* trạng thái ii>` (v0.1 `php_upgrade`) | exit 0; `pkg_has_cves` hoặc phiên bản ≥ bản vá tối thiểu (`BR-SCN-004`, `BR-SCN-015`) | v0.1 |
| 3 | Chưa có gói vá: ghi `zz-php-quickpatch-mitigation.ini` vào mọi `conf.d` của nhánh (v0.1 `php_mitigate`) | File tồn tại; ghi `created` vào manifest | v0.1 |
| 4 | Restart: `systemctl restart php<X.Y>-fpm` và web server (v0.1 `restart_php_services`) | Unit `active` | v0.1 |

### 2.4 (b) Cài song song `$NEW`
| Bước | Lệnh | Tiêu chí thành công | KC |
| :--- | :--- | :--- | :--- |
| 1 | Kiểm tra kho: `apt-cache policy php$NEW-fpm` | `Candidate` khác `(none)`; không có → bước 2 | Có |
| 2 (SEMI, `BR-ENV-004`) | Debian, Ubuntu Resolute: theo `https://packages.sury.org/php/README.txt`: `apt-get -y install lsb-release ca-certificates curl`; `curl -sSLo /tmp/debsuryorg-archive-keyring.deb https://packages.sury.org/debsuryorg-archive-keyring.deb`; `dpkg -i /tmp/debsuryorg-archive-keyring.deb`; ghi `deb [signed-by=/usr/share/keyrings/debsuryorg-archive-keyring.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main` vào `/etc/apt/sources.list.d/php.list`; `apt-get update`. Ubuntu Jammy/Noble: `add-apt-repository -y ppa:ondrej/php` | `apt-cache policy php$NEW-fpm` có `Candidate`; ghi `created` cho file kho và gói khoá | Có |
| 3 | Ghim mặc định hiện tại (`BR-SCN-012`), chạy trước bước 5 cho **cả 2 nhóm** `php` và `php-fpm.sock`: `update-alternatives --query <nhóm>`; exit 0 → ghi `Status`, `Value` và `readlink -f` của liên kết chính (`/usr/bin/php`, `/run/php/php-fpm.sock`) vào manifest (`link`), rồi `update-alternatives --set <nhóm> <Value đã ghi>` (ghim giá trị đang dùng, không mặc định là `$OLD`: máy có ≥ 3 nhánh có thể đang trỏ nhánh khác); exit 2 (nhóm chưa tồn tại, vd không pool nào nghe socket của `www.conf`) → ghi `note` "không có nhóm <nhóm>", bỏ qua nhóm đó | Sau bước 5 và sau bước 6: `readlink -f /usr/bin/php` và `readlink -f /run/php/php-fpm.sock` trùng giá trị đã ghi; `--query` của nhóm đã ghim có `Status: manual`. Khác → khôi phục theo dòng `link` (`update-alternatives --set <nhóm> <Value đã ghi>`), ghi lỗi, thoát 2 (UC-UPG-001 luồng 7a) | Có (chạy thử, §8) |
| 3b (SEMI) | Site trỏ alias `/run/php/php-fpm.sock` (§6.2 bước 4): ghim ở bước 3 **không bền** — `php$OLD-fpm` dừng (mỗi lần restart, vd hành động (a) hoặc v0.1 `restart_php_services`; mỗi lần tắt máy) thì `ExecStopPost` gọi `php-fpm-socket-helper remove`, `update-alternatives --remove` đưa nhóm về `auto` và nhánh có độ ưu tiên cao nhất (`$NEW`) được chọn. Vì vậy trước bước 5, mỗi site trỏ alias được đổi sang socket thật `readlink -f /run/php/php-fpm.sock` theo §6.4 bước 1–5 (thay socket `qp-<site_key>-$NEW.sock` bằng socket thật; cùng pool, cùng phiên bản PHP nên không chạy health check C10); manifest `copy` mỗi file; dry-run và xác nhận (`BR-CLI-003`) | 0 site trong kết quả §6.2 bước 4 còn trỏ `/run/php/php-fpm.sock`; `nginx -t`/`apachectl configtest` exit 0 (lỗi → khôi phục file, không reload, `ERR-ENV-500-02`). Người vận hành từ chối → không chạy bước 5, lượt `ABORTED` | Có (chạy thử, §8) |
| 4 | Lập danh sách extension: `$OLD_BIN -m` → tên gói `php$NEW-<ext>` theo bảng ánh xạ của FEAT-071 (`BR-SCN-045`) | Mọi extension có gói hoặc có quyết định thay thế | — |
| 5 | `apt-get install -y php$NEW-fpm php$NEW-cli php$NEW-<ext> …` — **không** cài gói meta `php$NEW` | exit 0; `systemctl is-active php$NEW-fpm` = `active` | Có |
| 6 | Kiểm tra: `php-fpm$NEW -t`; `$NEW_BIN -m` chứa mọi extension của bước 4 | exit 0 | Có |

Gói meta `php8.4` khai báo `Depends: libapache2-mod-php8.4 | php8.4-fpm | php8.4-cgi`; trên máy có Apache, cài gói meta có thể kéo theo `libapache2-mod-php8.4` (2 `mod_php` trong 1 Apache) — lý do của bước 5. Gói `php<X.Y>-fpm` không tự bật cấu hình Apache: postinst chỉ in hướng dẫn `a2enmod proxy_fcgi setenvif` và `a2enconf php<X.Y>-fpm`.

Ghi chú đồng bộ: `CHK-PHP-004-10` (DOC-SRS-QP-SCN-PHP-001) và các mục "Như `CHK-PHP-004-10`" hiện chỉ ghim nhóm `php` bằng `--set php $OLD_BIN`; cần thay bằng bước 3 (ghim giá trị đang dùng của cả `php` và `php-fpm.sock`), bước 3b và tiêu chí `readlink -f /run/php/php-fpm.sock` không đổi ở bản kế tiếp của tài liệu đó.

### 2.5 (c) Chuyển 1 site, (d) health check, (e) rollback
Theo PB-005 (site đang dùng PHP-FPM) hoặc PB-006 (site đang dùng `mod_php`). Đường dẫn riêng Debian (`<site_key>` theo §6.3.1): pool đích `/etc/php/$NEW/fpm/pool.d/qp-<site_key>.conf`; socket `/run/php/qp-<site_key>-$NEW.sock`; log FPM toàn cục `/var/log/php$NEW-fpm.log` (logrotate `/etc/logrotate.d/php$NEW-fpm`).

### 2.6 File sao lưu, reload, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | `/etc/php/$OLD/fpm/pool.d/*.conf`, `/etc/php/$OLD/*/php.ini` (đọc để sao chép cấu hình, `BR-SCN-046`), file kho mới (`created`), trạng thái `update-alternatives` của nhóm `php` và `php-fpm.sock` (`link`: `Status`, `Value`, `readlink -f`), file vhost/snippet của site trỏ alias `php-fpm.sock` (`copy`, bước 3b) |
| Restart/reload | (a): `systemctl restart php<X.Y>-fpm` (v0.1). (b)(c)(e): `systemctl reload php$NEW-fpm` — unit Debian có `ExecReload=/bin/kill -USR2 $MAINPID` (graceful) |
| Root | Bắt buộc (apt, `/etc/php`, systemd) |
| Rủi ro | (1) Kho Surý có thể cung cấp gói thư viện phụ thuộc khác bản của distro; `apt-get upgrade` toàn hệ thống sẽ nâng cả các gói đó (danh sách gói: chưa kiểm chứng) — giảm: chỉ nâng gói `php*` (v0.1 `--only-upgrade` theo danh sách gói). (2) PPA `ondrej/php` đang được gộp vào `packages.sury.org`; với Ubuntu Resolute chỉ dùng `packages.sury.org` (mô tả PPA trên Launchpad, 2026-10-22). (3) Unit `php<X.Y>-fpm` gọi `php-fpm-socket-helper install /run/php/php-fpm.sock … <XY>` khi khởi động, với độ ưu tiên alternative = số phiên bản; ở chế độ `auto`, `update-alternatives` chọn độ ưu tiên cao nhất, nên cài nhánh mới làm `/run/php/php-fpm.sock` trỏ sang nhánh mới — site trỏ vào `php-fpm.sock` đổi phiên bản ngoài ý muốn, không qua quét tương thích, health check hay manifest (vi phạm `BR-UPG-001`). Kiểm chứng: đọc `php-fpm.service` và `php-fpm-socket-helper`, chạy thử `update-alternatives` 1.22.6 với `--altdir`/`--admindir` riêng (§8): không ghim → liên kết sang `$NEW` ngay khi `$NEW` khởi động; có `--set` → giữ `$OLD` khi `$NEW` khởi động, nhưng về `Status: auto` và trỏ `$NEW` sau 1 lần restart `php$OLD-fpm` hoặc 1 lần khởi động lại máy (nhóm bị xoá khi mọi FPM dừng, tạo lại ở `auto`); giảm: bước 3 ghim trong lúc cài, bước 3b đưa mọi site trỏ alias sang socket có số phiên bản trước bước 5. (4) Hai pool cùng chạy làm tăng RAM (xem PB-005 §6.7) |

## 3. PB-002 — RHEL/Alma/Rocky AppStream

### 3.1 Nhận diện tự động
| Dấu hiệu | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Họ OS | `ID` ∈ {`rhel`, `almalinux`, `rocky`, `centos`} hoặc `ID_LIKE` chứa `rhel` | Có |
| PHP từ AppStream | `rpm -qf --qf '%{NAME} %{VERSION}\n' "$(readlink -f /usr/bin/php)"` → `php-cli`; gói **không** có tiền tố `php[0-9][0-9]-`, `ea-`, `alt-` | v0.1 |
| Stream đang bật (EL8, EL9) | `dnf module list --enabled php` | Có |
| EL10 | `VERSION_ID` bắt đầu `10`: RHEL 10 không phân phối nội dung dạng module | Có |

### 3.2 Dữ liệu vòng đời AppStream PHP (Red Hat, 2026-10-22)
| RHEL | Phiên bản PHP AppStream (bản RHEL đưa vào → ngày ngừng) |
| :--- | :--- |
| 8 | 7.2 (8.0 → 05/2021), 7.3 (8.1 → 11/2021), 7.4 (8.3, toàn vòng đời RHEL 8), 8.0 (8.6 → 11/2024), 8.2 (8.10 → 05/2029) |
| 9 | 8.0 (9.0, toàn vòng đời RHEL 9), 8.1 (9.1 → 05/2025), 8.2 (9.4 → 05/2029), 8.3 (9.6 → 05/2029) |
| 10 | 8.3 (10.0, toàn vòng đời RHEL 10), 8.4 (10.2 → 05/2029) |

### 3.3 Hành động
| Hành động | Lệnh / quyết định | KC |
| :--- | :--- | :--- |
| Liệt kê | `rpm -q php-cli php-fpm`; dịch vụ `php-fpm`; pool `/etc/php-fpm.d/*.conf` (đọc `listen` thực tế); site → PB-005 | v0.1 / Có |
| (a) Vá cùng nhánh | `dnf -y -q upgrade 'php*'` (EL7: `yum -y -q update 'php*'`) (v0.1); kiểm tra `rpm -q --changelog` (v0.1 `pkg_has_cves`) | v0.1 |
| (b) Cài song song | **Không hỗ trợ** trên AppStream: 1 hệ thống chỉ có 1 stream `php` (EL8/9 `dnf module switch-to php:<X.Y>` thay thế gói tại chỗ, vi phạm `BR-UPG-001`; EL10 chỉ có 1 gói `php` mỗi phiên bản phát hành). Tool đề xuất 3 phương án theo thứ tự: PB-003 (Remi SCL `php$NEWND`, cài cạnh gói AppStream), PB-013 (container), máy chủ mới | Có |
| (c)(d)(e) | Không áp dụng cho AppStream; khi chọn PB-003 thì site chuyển theo PB-005 | — |
| File sao lưu | (a): mitigation ini (`created`); không có file cấu hình bị sửa | v0.1 |
| Restart | `systemctl restart php-fpm` và `httpd`/`nginx` (v0.1) | v0.1 |
| Root | Bắt buộc | — |
| Rủi ro | (1) `dnf module reset php` / `switch-to` do người khác chạy sẽ thay PHP tại chỗ — tool phát hiện bằng so sánh `dnf module list --enabled php` giữa 2 lần `scan` và báo `ERR-ENV-422-02`. (2) Stream 8.1 trên RHEL 9 đã ngừng 05/2025 → kịch bản SCN-PHP-009 (EOL), bắt buộc lập kế hoạch nâng nhánh qua PB-003/PB-013 | Có (ngày ngừng 8.1) |

## 4. PB-003 — RHEL/Alma/Rocky + Remi SCL

### 4.1 Nhận diện tự động
| Dấu hiệu | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Kho Remi | `rpm -q remi-release` exit 0; hoặc `/etc/yum.repos.d/remi-safe.repo` | Có |
| Binary SCL | `/opt/remi/php*/root/usr/bin/php` (v0.1 `discover_php_bins`); lệnh bao `php84` | v0.1 / Có |
| Gói | `rpm -qf` → `php84-php-cli` (tiền tố `php[0-9][0-9]-`) | v0.1 |

### 4.2 Liệt kê phiên bản và site
| Mục | Lệnh | KC |
| :--- | :--- | :--- |
| Collection đã cài | `rpm -qa 'php[0-9][0-9]-runtime'` hoặc `ls -d /opt/remi/php*` | Chưa (tên gói `-runtime`) / v0.1 |
| Dịch vụ FPM | `systemctl list-units 'php[0-9][0-9]-php-fpm.service'` | Chưa |
| Pool | `/etc/opt/remi/php$NEWND/php-fpm.d/*.conf` (tool đọc đường dẫn thực tế bằng `rpm -ql php$NEWND-php-fpm`) | Chưa |
| Socket | Directive `listen` trong pool; dạng thường gặp `/var/opt/remi/php$NEWND/run/php-fpm/www.sock` | Chưa |
| Site → phiên bản | PB-005 | — |

### 4.3 Hành động
| Hành động | Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- | :--- |
| (a) | 1 | `dnf -y -q upgrade 'php$OLDND*'` (v0.1 glob `php[0-9]+*`) | `pkg_has_cves` hoặc ≥ bản vá tối thiểu | v0.1 |
| (a) | 2 | Kho Remi chưa có bản vá (độ trễ đã ghi ở DOC-SRS-QP-SCN-000 §7 mục 5: ngày 2026-10-22 Remi có 8.4.26, bản vá 8.4.27 mới ở `remi-test` dạng RC1) → mitigation ini, không bật `remi-test` | Mitigation `created` | v0.1 / Có |
| (b) | 1 (SEMI) | Thêm kho theo Remi wizard (EL9): `dnf config-manager --set-enabled crb`; `dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm`; `dnf install https://rpms.remirepo.net/enterprise/remi-release-9.rpm` (EL8/EL10: thay số 8/10) | `rpm -q remi-release` exit 0 | Có |
| (b) | 2 | `dnf install php$NEWND php$NEWND-php-fpm php$NEWND-php-<ext> …` (wizard: "Command to install: `dnf install php84`", "additional packages: `dnf install php84-php-xxx`") | exit 0; `php$NEWND --version` | Có (tên `-php-fpm` theo mẫu `-php-xxx`) |
| (b) | 3 | Không cài `php$NEWND-syspaths` (gói này đặt lệnh vào `/usr/bin/php`, đổi mặc định hệ thống — vi phạm `BR-SCN-012`) | `readlink -f /usr/bin/php` không đổi | Có |
| (b) | 4 | Đổi `listen` của pool đích khác mọi pool đang chạy; `systemctl enable --now php$NEWND-php-fpm` | Unit `active`; `ss -xlp`/`ss -tlnp` thấy socket/cổng mới | Chưa (tên unit) |
| (c)(d)(e) | — | PB-005 với socket Remi | — | — |
| Không dùng | — | Hình thức "single version" của wizard (`dnf module switch-to php:remi-8.4`, `dnf module install php:remi-8.4`) thay PHP tại chỗ → chỉ dùng cho (a) khi máy đã chọn hình thức này từ trước | — | Có |

### 4.4 File sao lưu, reload, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | `/etc/opt/remi/php$OLDND/php-fpm.d/*.conf`, `/etc/opt/remi/php$OLDND/php.ini`; file kho mới (`created`) |
| Restart/reload | `systemctl reload php$NEWND-php-fpm` (đường dẫn unit chưa kiểm chứng). Lỗ hổng v0.1: mẫu unit trong `restart_php_services` (`php[0-9.]*-fpm`, `php-fpm[0-9.]*`, `ea-php…`, `rh-php…`, `plesk-php…`) **không khớp** `php84-php-fpm`, nên (a) của v0.1 không restart FPM của Remi SCL; v2 bổ sung mẫu `php[0-9]+-php-fpm` |
| Root | Bắt buộc |
| Rủi ro | (1) SELinux `enforcing` (`getenforce`): socket/log ở đường dẫn mới có thể bị chặn đối với `httpd_t` → Nginx/Apache trả 502; giảm: `restorecon -Rv` trên file tool tạo, health check `HC-C2` phát hiện và tự rollback (lệnh `restorecon` chuẩn, nhãn cụ thể chưa kiểm chứng). (2) Kho EPEL/CRB kéo thêm gói. (3) Remi chậm bản vá so với php.net |

## 5. PB-004 — Alpine Linux

### 5.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Họ OS | `ID=alpine`; `command -v apk` | Có |
| Thường chạy trong container | `in_container=1` → `BR-ENV-009` (khoá (b)(c)(e), chuyển PB-013 ở host) | v0.1 |
| Gói theo nhánh | `apk info \| grep -E '^php[0-9]{2}(-fpm)?$'`; binary `/usr/bin/php84`, FPM `/usr/sbin/php-fpm84` | Có |
| Dịch vụ (OpenRC) | `/etc/init.d/php-fpm84`; `rc-service php-fpm84 status` | Có (file init) / Chưa (lệnh) |
| Pool | `/etc/php84/php-fpm.conf`, `/etc/php84/php-fpm.d/www.conf` | Có |
| Nhánh có trong kho (`community`, x86_64, 2026-10-22) | v3.22: 8.2, 8.3, 8.4; v3.23 và v3.24: 8.3, 8.4, 8.5; edge: 8.1–8.6. Hạn hỗ trợ: v3.22 → 2027-05-01, v3.23 → 2027-11-01, v3.24 → 2028-06-01 | Có |

### 5.2 Hành động
| Hành động | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| (a) | `apk upgrade --no-cache $(apk info \| grep "^php$OLDND")` (v0.1) | Phiên bản ≥ bản vá tối thiểu | v0.1 |
| (b) | `apk add --no-cache php$NEWND php$NEWND-fpm php$NEWND-<ext> …`; sửa `listen` trong `/etc/php$NEWND/php-fpm.d/www.conf` sang socket/cổng chưa dùng (mặc định upstream `www.conf.in` là `listen = 127.0.0.1:9000`, trùng cổng của nhánh cũ nếu nhánh cũ giữ mặc định); `rc-update add php-fpm$NEWND default`; `rc-service php-fpm$NEWND start` | Tiến trình `php-fpm$NEWND` chạy, cổng/socket mới đang nghe | Có (gói, upstream) / Chưa (giá trị `listen` trong gói Alpine, lệnh OpenRC) |
| (b) — nhánh không có trong kho của bản Alpine đang chạy | Không trộn gói của nhánh Alpine khác (`edge`) vào hệ thống; đề xuất nâng bản Alpine hoặc PB-013 | `ERR-ENV-424-01` | — |
| (c)(d)(e) | PB-005 | — | — |
| Restart/reload | `rc-service php-fpm$NEWND reload` (Chưa); v0.1 khi không có systemd: `/etc/init.d/php-fpm*` `restart` hoặc `pkill -USR2 -f 'php-fpm: master'` | | v0.1 |
| File sao lưu | `/etc/php$OLDND/php-fpm.d/*.conf`, `/etc/php$OLDND/php.ini` | | — |
| Root | Bắt buộc | | — |
| Rủi ro | Trùng cổng 9000 giữa 2 nhánh (giảm: `BR-ENV-007` socket riêng); musl khác glibc với extension PECL biên dịch sẵn | | — |

## 6. PB-005 — Nginx hoặc Apache + PHP-FPM

### 6.1 Nhận diện tự động
| Dấu hiệu | Lệnh | KC |
| :--- | :--- | :--- |
| Nginx đang chạy | `pgrep -f 'nginx: master'`; `nginx -v` | Có |
| Cấu hình Nginx đang nạp | `nginx -T` (in toàn bộ cấu hình kèm dòng `# configuration file <path>:`) | Có |
| Apache đang chạy | `pgrep -x apache2` hoặc `pgrep -x httpd` (v0.1) | v0.1 |
| Apache dùng FPM | `apachectl -M` có `proxy_fcgi_module`; vhost hoặc `conf-enabled/php<X.Y>-fpm.conf` có `SetHandler "proxy:unix:…\|fcgi://localhost"` | Có |
| Danh sách vhost Apache | `apachectl -S` (= `-t -D DUMP_VHOSTS`) | Có |

### 6.2 Liệt kê site và phiên bản đang gán
| Bước | Nginx | Apache |
| :--- | :--- | :--- |
| 1 | Tách `nginx -T` theo khối `server { }`; lấy `server_name`, `listen`, `root`, file nguồn | `apachectl -S` → danh sách `<VirtualHost>` (tên, cổng, file:dòng); đọc `ServerName`, `ServerAlias`, `DocumentRoot` |
| 2 | Trong `location ~ \.php$` (hoặc tương đương) lấy `fastcgi_pass`; nếu là tên `upstream` → lấy `server` của upstream; nếu nằm trong `include` → ghi file snippet | Lấy `SetHandler "proxy:unix:<sock>\|fcgi://…"` hoặc `ProxyPassMatch … fcgi://<host>:<port>/…` trong vhost; không có → áp `conf-enabled/php<X.Y>-fpm.conf` (Debian: cấu hình **toàn cục**, áp cho mọi vhost không tự khai báo) |
| 3 | Socket/cổng → pool: tìm `listen = <giá trị>` trong mọi file pool (`/etc/php/*/fpm/pool.d/*.conf`, `/etc/opt/remi/php*/php-fpm.d/*.conf`, `/etc/php*/php-fpm.d/*.conf`, `/etc/php-fpm.d/*.conf`); thư mục chứa pool → nhánh PHP | Như Nginx |
| 4 | Socket là liên kết (vd `/run/php/php-fpm.sock`) → `readlink -f` để ra socket thật, ghi cảnh báo "site trỏ socket không số phiên bản" (Debian: xử lý ở PB-001 §2.4 bước 3b trước khi cài `$NEW`) | Như Nginx |
| 5 | Site có ≥ 2 khối server (cổng 80 và 443) → mọi khối được ghi vào `binding_ref` và chuyển cùng lúc | Như Nginx với ≥ 2 `<VirtualHost>` |

### 6.3 (b) Chuẩn bị pool đích cho site (`FR-UPG-CFG-001`, `BR-ENV-007`)
Tool tạo file pool mới (ghi `created`), không sửa pool đang dùng.

#### 6.3.1 Quy tắc đặt tên `<site_key>`
Lý do: `site_id` của site tên miền dài tới 253 ký tự (regex `site_id` của `BR-CON-008`, [api-spec.md §2](../api/api-spec.md)), trong khi đường dẫn socket AF_UNIX tối đa 107 byte (`sun_path[108]` gồm byte NUL) và mỗi thành phần tên file tối đa 255 byte (`NAME_MAX`). Với `site_id` 253 ký tự: `qp-<site_id>.conf` = 261 byte, `<site_id>-8.4.error.log` = 267 byte (vượt `NAME_MAX`); socket `/run/php/qp-<site_id>-8.4.sock` = 274 byte. Ghi file có thành phần tên > 255 byte trả lỗi `ENAMETOOLONG`. PHP-FPM 8.4 không dừng khi đường dẫn socket ≥ 108 byte: ghi `WARNING` "cannot bind to UNIX socket … as path is too long … trying cut socket path instead" và bind vào đường dẫn bị cắt còn 107 byte, nên dịch vụ FPM đích vẫn `active` và kiểm tra của C3 (DOC-SRS-QP-ENV-001 §5.1) không phát hiện; lượt chỉ dừng ở C4 (FastCGI probe tới đường dẫn đầy đủ thất bại, `ERR-HC-424-01`) hoặc C8 (`nginx -t` báo "too long path in the unix domain socket", `ERR-ENV-500-02`), không nêu nguyên nhân độ dài. 2 site có cùng 107 byte đầu (hoặc 2 nhánh `X.Y` của cùng 1 site) bị cắt về cùng 1 đường dẫn socket.

| Mục | Quy tắc |
| :--- | :--- |
| `<site_key>` dạng đọc được | = `site_id` khi `site_id` khớp `^[a-z0-9.-]{1,48}$` **và** đường dẫn socket tính ra ≤ 107 byte. Vd `shop.example.com` |
| `<site_key>` dạng băm | Mọi trường hợp còn lại (`site_id` > 48 ký tự, có `:`/`/`, hoặc đường dẫn socket dạng đọc được > 107 byte): `h_` + 12 ký tự hex đầu của SHA-1 chuỗi `site_id` (UTF-8), cùng cách băm với `runtime_id` (DOC-SRS-QP-001 §1.3). Vd `site_id` = `khuyen-mai-thang-10.chi-nhanh-ho-chi-minh.shop.example.com` (58 ký tự) → `h_81375b32ac00`. Ký tự `_` không thuộc tập `[a-z0-9.-]` nên dạng băm không trùng dạng đọc được |
| Tên dẫn xuất | Pool `qp-<site_key>`; file pool `<thư mục pool của PB>/qp-<site_key>.conf`; socket `<thư mục socket của PB>/qp-<site_key>-<X.Y>.sock` (Debian `/run/php/`); log `/var/log/php-quickpatch/<site_key>-<X.Y>.error.log`; snippet Nginx `/etc/nginx/snippets/qp-<site_key>-php.conf` |
| Độ dài tối đa | Phần sau thư mục của socket: dạng đọc được ≤ 60 byte (`qp-` 3 + 48 + `-X.Y.sock` 9; nhánh PHP luôn khớp `^[4-9]\.[0-9]$`), dạng băm = 26 byte. Debian: ≤ 69 byte / 35 byte; thư mục Remi `/var/opt/remi/php84/run/php-fpm/` (32 byte, Chưa): ≤ 92 byte / 58 byte. Thành phần tên file dài nhất (dạng đọc được) là log `<site_key>-X.Y.error.log` ≤ 62 byte |
| Kiểm tra trong C3 | Tính đường dẫn socket bằng thư mục thực tế **trước khi tạo file pool, snippet, log đích**: dạng băm vẫn > 107 byte (thư mục socket > 81 byte) → lượt `ABORTED`, không tạo file đích, không đổi site, báo `ERR-ENV-500-01` với chi tiết `socket_path_too_long` (độ dài thực tế, giới hạn 107) |
| Truy vết ngược | Dòng đầu file pool: `; qp-site-id = <site_id>`. File `qp-<site_key>.conf` đã tồn tại với `qp-site-id` khác `site_id` của lượt → lượt `ABORTED`, không ghi đè, báo `ERR-ENV-500-01` với chi tiết `pool_name_collision`. Cùng `site_id` (pool giữ lại sau rollback, §6.6) → dùng lại |
| Ghi ánh xạ | `switch.json` của lượt có thêm trường `site_key`, `fpm_pool`, `fpm_socket`, `fpm_error_log`; rollback (§6.6), `--purge-pool` và health check đọc các trường này, không tính lại tên từ `site_id` |
| Kiểm thử bắt buộc | `site_id` 48 ký tự → dạng đọc được; 49 ký tự và 253 ký tự → dạng băm; trong 3 ca: socket ≤ 107 byte, mọi tên file ≤ 255 byte, `php-fpm$NEW -t` và `nginx -t`/`apachectl configtest` exit 0, log FPM không có chuỗi `path is too long`, FastCGI probe ở C4 (`BR-HC-003`) và tiêu chí `HC-C0` ở C10 đạt |

Ghi chú đồng bộ: `BR-ENV-007` (DOC-SRS-QP-ENV-001) và đường dẫn log nguồn 1 (DOC-SRS-QP-ENV-002 §5) ghi `qp-<site_id>`/`<site_id>`; với `site_id` ≤ 48 ký tự (dạng đọc được) hai cách ghi cho cùng kết quả. Cần thay bằng `<site_key>` ở 2 tài liệu đó và thêm 4 trường trên vào DOC-SRS-QP-ERD-004 §9.5 ở bản kế tiếp.

#### 6.3.2 Mẫu pool đích

```ini
; qp-site-id = shop.example.com
; /etc/php/8.4/fpm/pool.d/qp-shop.example.com.conf (Debian; thư mục theo PB provider; <site_key> = shop.example.com)
[qp-shop.example.com]
user = <user của pool cũ>
group = <group của pool cũ>
listen = /run/php/qp-shop.example.com-8.4.sock
listen.owner = <user của web server: www-data | nginx | apache>
listen.group = <group của web server>
listen.mode = 0660
pm = <giá trị pool cũ>            ; pm.max_children, pm.start_servers, pm.min/max_spare_servers, pm.max_requests sao chép từ pool cũ
pm.status_path = /qp-fpm-status   ; chỉ đọc qua FastCGI probe, không có location trên web server
catch_workers_output = yes
php_admin_value[error_log] = /var/log/php-quickpatch/shop.example.com-8.4.error.log
php_admin_flag[log_errors] = on
; các dòng php_value/php_admin_value/env[...] của pool cũ được sao chép, trừ directive đã bị xoá (BR-SCN-046)
```

Tiêu chí: `php-fpm$NEW -t` exit 0 (RHEL Remi: `/opt/remi/php$NEWND/root/usr/sbin/php-fpm -t`, Chưa; Alpine: `php-fpm$NEWND -t`, Chưa); sau `systemctl reload php$NEW-fpm`, socket tồn tại với quyền `0660`, đường dẫn socket ≤ 107 byte (§6.3.1) và log FPM của `$NEW` sau reload không có chuỗi `path is too long`.

### 6.4 (c) Chuyển 1 site
| Bước | Nginx | Apache | KC |
| :--- | :--- | :--- | :--- |
| 1 | `backup_file` mọi file trong `binding_ref` | Như Nginx | v0.1 |
| 2 | `fastcgi_pass` nằm trực tiếp trong file của site → thay giá trị bằng `unix:/run/php/qp-<site_key>-$NEW.sock;` | Trong mỗi `<VirtualHost>` của site, thay hoặc thêm khối `<FilesMatch ".+\.ph(?:ar\|p\|tml)$"> SetHandler "proxy:unix:/run/php/qp-<site_key>-$NEW.sock\|fcgi://localhost" </FilesMatch>` (khối này ghi đè cấu hình toàn cục `php<X.Y>-fpm.conf` cho riêng vhost) | Có (cú pháp `SetHandler` theo `php-fpm.conf` của gói Debian) |
| 3 | `fastcgi_pass` nằm trong snippet dùng chung (vd `snippets/fastcgi-php.conf`) hoặc `upstream` dùng chung → **không sửa** snippet/upstream; sao chép snippet thành `/etc/nginx/snippets/qp-<site_key>-php.conf` (`created`) với socket mới và đổi dòng `include` trong file của site | Không áp dụng | — |
| 4 | `nginx -t` | `apachectl configtest` | Có |
| 5 | `nginx -s reload` (hoặc `systemctl reload nginx`) | `apachectl -k graceful` (hoặc `systemctl reload apache2`/`httpd`) | Có |
| 6 | Xác minh `HC-C0` bằng FPM status của pool `qp-<site_key>` (tên lấy từ trường `fpm_pool` của `switch.json`) (DOC-SRS-QP-ENV-002 §3.4) | Như Nginx | — |

Manifest của lượt: `reload nginx|apache` → `switch` → `copy` (mỗi file) → `created` (pool, snippet).

### 6.5 (d) Đầu vào health check
URL theo DOC-SRS-QP-ENV-002 §3.1 với `server_name`/`ServerName` và `listen`; log: `php_admin_value[error_log]` của pool `qp-<site_key>` (nguồn 1; đường dẫn lấy từ trường `fpm_error_log` của `switch.json`, §6.3.1), log FPM toàn cục của `$NEW` (nguồn 2), `error_log` của khối server/`ErrorLog` của vhost (nguồn 3).

### 6.6 (e) Rollback 1 lệnh
`php-quickpatch.sh rollback-site <site_id>`: phát lại `copy` (khôi phục file vhost/snippet) → `nginx -t`/`apachectl configtest` → graceful reload. Pool `qp-<site_key>` của `$NEW` (tên đọc từ `switch.json`, §6.3.1) được giữ (chỉ xoá với `--purge-pool`), vì không còn site nào trỏ tới nên không nhận request.

### 6.7 File sao lưu, reload, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | Mọi file chứa khối server/`<VirtualHost>` của site (đường dẫn thật sau `readlink -f`, kể cả `sites-enabled` là liên kết), snippet bị thay `include`, pool cũ (chỉ đọc) |
| Restart/reload | Chỉ graceful reload Nginx/Apache và reload FPM đích (`BR-ENV-006`); không restart FPM `$OLD` |
| Root | Bắt buộc (sửa `/etc/nginx`, `/etc/apache2`, `/etc/php`) |
| Rủi ro 1 — RAM | Pool mới thêm tối đa `pm.max_children` tiến trình. Điều kiện trước C3: RAM khả dụng (`MemAvailable` trong `/proc/meminfo`) ≥ `pm.max_children` × RSS trung bình 1 worker của pool cũ (`ps -o rss= -C php-fpm<X.Y>`) + 256 MB; không đạt → đặt `pm = ondemand`, `pm.max_children` = ⌊(MemAvailable − 256 MB) / RSS⌋ (tối thiểu 2), ghi cảnh báo |
| Rủi ro 2 — công cụ quản lý cấu hình | Ansible/Puppet/Chef hoặc certbot ghi lại file vhost và xoá thay đổi; giảm: `scan` so sánh `binding_ref` với `switch_record` mỗi lần chạy, lệch → cảnh báo "site bị đổi ngoài tool" |
| Rủi ro 3 — `include` wildcard | `include /etc/nginx/conf.d/*.conf` có thể nạp file sao lưu nếu đặt sai thư mục; giảm: tool không bao giờ ghi bản sao lưu vào thư mục cấu hình web server (bản sao nằm trong `STATE_DIR/backups/`) |
| Rủi ro 4 — opcache, session | Opcache của pool mới trống ở request đầu (`BR-HC-006`); `session.save_path` khác giữa 2 nhánh có thể làm mất phiên đăng nhập hiện tại — tool sao chép `session.save_path` của pool cũ sang pool mới |

## 7. PB-006 — Apache mod_php
Phương án: chuyển Apache từ `mod_php` sang PHP-FPM cùng phiên bản (bước 1, toàn máy chủ), sau đó chuyển từng site sang `$NEW` theo PB-005 (bước 2).

### 7.1 Nhận diện và lý do rủi ro cao
| Mục | Nội dung | KC |
| :--- | :--- | :--- |
| Dấu hiệu | `ls /etc/apache2/mods-enabled/php*.load` (Debian) hoặc `httpd -M \| grep php` (v0.1 `php_sapis_note`); `apachectl -M` có `php_module`/`php7_module`/`php5_module` | v0.1 |
| MPM | `apachectl -V \| grep -i 'Server MPM'` — `mod_php` không biên dịch thread-safe (không `--enable-zts`) chỉ chạy với MPM `prefork` (PHP manual "Apache 2.x on Unix systems"). Debian: gói `libapache2-mod-php<X.Y>` mô tả "ONLY works with Apache's prefork MPM, as it is not compiled thread-safe"; file `php<X.Y>.load` có dòng `# Depends: mpm_prefork` (`a2enmod php<X.Y>` bật kèm `mpm_prefork`). `debian/control` không khai báo `Conflicts` với `mpm_event` | Có (§8) |
| Vì sao không chuyển từng site trực tiếp | `mod_php` nạp 1 thư viện PHP vào mọi tiến trình Apache; tool không cấu hình 2 `mod_php` trong 1 Apache (`BR-SCN-047`), nên mọi vhost chạy cùng 1 phiên bản. Muốn chuyển **từng** site phải đưa Apache sang PHP-FPM trước | — |
| Mức rủi ro | Bước 1 dưới đây thay đổi **toàn máy chủ** (mọi vhost), cần restart Apache (gián đoạn mọi site trong thời gian restart) | — |

### 7.2 Điều kiện trước bước 1 (chặn nếu không đạt)
| Mã | Điều kiện | Cách kiểm tra | Không đạt |
| :--- | :--- | :--- | :--- |
| P6-1 | 0 dòng `php_value`, `php_flag`, `php_admin_value`, `php_admin_flag` nằm ngoài khối `<IfModule mod_php*.c>`/`<IfModule php*_module>` trong `.htaccess` của mọi docroot và trong vhost | `grep -RnE '^\s*php_(admin_)?(value\|flag)' <docroot>/.htaccess …` + phân tích khối `IfModule` | Apache trả 500 khi gặp directive không có module xử lý. Tool chỉ liệt kê (không ghi docroot, `C-ENV-02`); chuyển giá trị sang `php_admin_value[...]` trong pool của site; người vận hành sửa `.htaccess` (mục `MANUAL`) |
| P6-2 | `php$OLD-fpm` có trong kho (cùng nhánh với `mod_php`) | `apt-cache policy php$OLD-fpm` / `dnf info php-fpm` | Nhánh `$OLD` đã EOL và kho không còn gói → chỉ còn phương án PB-013 hoặc máy chủ mới (`ERR-SCN-412-02`) |
| P6-3 | Khác biệt `php.ini` giữa SAPI `apache2` và `fpm` của `$OLD` đã được sao chép | `diff <(php -n -c /etc/php/$OLD/apache2/php.ini -i) …` theo danh sách directive | Liệt kê directive khác nhau, tool sao chép vào pool |

### 7.3 Bước 1 — `mod_php` → PHP-FPM cùng phiên bản `$OLD` (SEMI, 1 lần cho cả máy chủ)
| Bước | Debian/Ubuntu | KC |
| :--- | :--- | :--- |
| 1.1 | `apt-get install -y php$OLD-fpm` (+ extension tương ứng `$OLD_BIN -m`) | Có |
| 1.2 | Tạo pool theo từng site (§6.3, với `$OLD`) hoặc giữ pool `www` chung khi người vận hành chọn | — |
| 1.3 | `a2dismod php$OLD`; `a2dismod mpm_prefork`; `a2enmod mpm_event proxy_fcgi setenvif`; `a2enconf php$OLD-fpm` (2 lệnh cuối theo thông báo postinst của gói `php-fpm`) — ghi `link`/`created` cho mọi liên kết trong `mods-enabled`/`conf-enabled` | Có (`a2enmod proxy_fcgi setenvif`, `a2enconf`); Chưa (đổi MPM) |
| 1.4 | `apachectl configtest` | Có |
| 1.5 | `systemctl restart apache2` (đổi module MPM: dùng restart, không dùng graceful); đo thời gian gián đoạn | Có |
| 1.6 | Health check cho **mọi vhost** (≤ 50 vhost; > 50: mọi vhost có `hc_url` khai báo + 50 vhost chọn ngẫu nhiên): tiêu chí `HC-C1`, `HC-C2`, `HC-C5`, `HC-C7` trong 600 s | — |
| 1.7 | KHÔNG ĐẠT → rollback bước 1: khôi phục liên kết module/conf theo manifest, `systemctl restart apache2`, health check lại 1 vòng | — |
| RHEL | Module PHP nạp qua `/etc/httpd/conf.modules.d/*php*.conf`, MPM ở `/etc/httpd/conf.modules.d/00-mpm.conf` (Chưa); các bước tương ứng ở mức `MANUAL` | Chưa |

### 7.4 Bước 2 — chuyển từng site sang `$NEW`
Sau khi bước 1 `PASSED` và ≥ 24 giờ không có rollback, mỗi site chuyển sang `$NEW` theo PB-005 (biến thể Apache).

### 7.5 File sao lưu, reload, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | Toàn bộ liên kết trong `/etc/apache2/mods-enabled/`, `/etc/apache2/conf-enabled/` (ghi danh sách + đích liên kết), `/etc/apache2/apache2.conf`, file vhost |
| Restart/reload | Bước 1: restart Apache (1 lần). Bước 2: graceful |
| Root | Bắt buộc |
| Rủi ro | (1) Gián đoạn mọi site khi restart Apache (đo, ghi vào báo cáo). (2) `php_value` trong `.htaccess` gây 500 (điều kiện P6-1). (3) `mpm_event` thay đổi mô hình tiến trình: module chỉ chạy với MPM `prefork` (vd `mod_ruid2`, `mod_itk` — chưa kiểm chứng danh sách) không dùng được — tool liệt kê module đang bật (`apachectl -M`) cho người vận hành duyệt. (4) Quyền file: `mod_php` chạy dưới user Apache, FPM pool có thể chạy dưới user của site → file do ứng dụng tạo sau chuyển có chủ khác; tool đặt `user` của pool = user Apache ở bước 1 để giữ hành vi, đổi sang user site là quyết định riêng của người vận hành |

## 8. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22 (UTC).

| Nguồn | URL | Dùng cho | Trạng thái |
| :--- | :--- | :--- | :--- |
| Kho Surý (Debian) | https://packages.sury.org/php/README.txt | PB-001 (b) bước 2 | Kiểm chứng (tải file, đọc lệnh) |
| PPA Ondřej (Launchpad API) | https://api.launchpad.net/1.0/~ondrej/+archive/ubuntu/php | Mô tả: đang gộp vào `packages.sury.org`; Resolute dùng `packages.sury.org`; Jammy/Noble vẫn dùng PPA | Kiểm chứng |
| Danh sách file `php8.4-fpm` (Debian trixie) | https://packages.debian.org/trixie/amd64/php8.4-fpm/filelist | `/etc/apache2/conf-available/php8.4-fpm.conf`, `/etc/php/8.4/fpm/pool.d/www.conf`, unit `php8.4-fpm.service`, `/usr/sbin/php-fpm8.4` | Kiểm chứng |
| Đóng gói Debian `php8.4` 8.4.26-1~deb13u1 | https://sources.debian.org/src/php8.4/8.4.26-1~deb13u1/debian/ (`php-fpm.conf`, `php-fpm.postinst.extra`, `php-fpm.service`, `control`) | `SetHandler "proxy:unix:/run/php/php@PHP_VERSION@-fpm.sock\|fcgi://localhost"`; thông báo `a2enmod proxy_fcgi setenvif` / `a2enconf`; `ExecReload=/bin/kill -USR2 $MAINPID`; `php-fpm-socket-helper` cho `/run/php/php-fpm.sock`; gói meta `php8.4` phụ thuộc `libapache2-mod-php8.4 \| php8.4-fpm \| php8.4-cgi` | Kiểm chứng |
| Đóng gói Debian `php8.4` 8.4.26-1 (forky) | https://sources.debian.org/data/main/p/php8.4/8.4.26-1/debian/php-fpm.service; …/debian/php.load; …/debian/control | §2.4 bước 3/3b: `ExecStartPost=-/usr/lib/php/php-fpm-socket-helper install /run/php/php-fpm.sock /etc/php/@PHP_VERSION@/fpm/pool.d/www.conf @PHP_MAJOR@@PHP_MINOR@`, `ExecStopPost=… remove …`. §7.1: `php.load` có `# Depends: mpm_prefork`; mô tả `libapache2-mod-php8.4` "ONLY works with Apache's prefork MPM, as it is not compiled thread-safe"; không có `Conflicts` với MPM. Khi kiểm lại, bản `8.4.26-1~deb13u1` ở dòng trên không còn trên sources.debian.org (trixie: 8.4.24-1~deb13u1, trixie-proposed-updates: 8.4.27-1~deb13u1) | Kiểm chứng (tải file) |
| Debian `php-defaults` 96 (trixie) — `php-fpm-socket-helper` | https://sources.debian.org/data/main/p/php-defaults/96/php-fpm-socket-helper | §2.4: đọc `listen` của `www.conf`; socket chưa tồn tại → thoát 0 không đăng ký; `install` → `update-alternatives --install <DEFAULT_SOCKET> php-fpm.sock <SOCKET> <PRIORITY>`; `remove` → `update-alternatives --remove php-fpm.sock <SOCKET>` | Kiểm chứng (đọc mã nguồn) |
| `update-alternatives(1)` (dpkg, Debian trixie) | https://manpages.debian.org/trixie/dpkg/update-alternatives.1.en.html | §2.4: `--install` chỉ đổi liên kết khi nhóm ở `auto` và độ ưu tiên cao hơn; `--remove` của phương án đang được chọn → trỏ phương án khác "and the group is put back in automatic mode", hết phương án → xoá nhóm | Kiểm chứng; chạy thử `update-alternatives` 1.22.6 (Ubuntu 24.04) với `--altdir`/`--admindir` riêng: 5 tình huống (không ghim, ghim + `$NEW` khởi động, ghim + restart `$OLD`, ghim + tắt/bật máy, `--query` nhóm không tồn tại → exit 2) cho kết quả như §2.6 rủi ro (3) |
| PHP manual — Apache 2.x on Unix systems | https://www.php.net/manual/en/install.unix.apache2.php | §7.1: "Unless PHP was compiled with Zend Thread Safety (`--enable-zts`), `mod_php` requires the `prefork` MPM"; "Most distribution packages of `mod_php` are not built with ZTS" | Kiểm chứng |
| php-src `sapi/fpm/www.conf.in` (nhánh PHP-8.4) | https://raw.githubusercontent.com/php/php-src/PHP-8.4/sapi/fpm/www.conf.in | `listen = 127.0.0.1:9000`, `pm.status_path`, `catch_workers_output`, `php_admin_value[error_log]` | Kiểm chứng |
| php-src `sapi/fpm/fpm/fpm_sockets.c` (nhánh PHP-8.4) | https://raw.githubusercontent.com/php/php-src/PHP-8.4/sapi/fpm/fpm/fpm_sockets.c | §6.3.1: hàm `fpm_socket_af_unix_listening_socket` dùng `strlcpy` vào `sun_path` và ghi `ZLOG_WARNING` "cannot bind to UNIX socket '%s' as path is too long … trying cut socket path instead" (không dừng) | Kiểm chứng (đọc mã nguồn) |
| nginx `src/core/ngx_inet.c` (nhánh master) | https://raw.githubusercontent.com/nginx/nginx/master/src/core/ngx_inet.c | §6.3.1: `ngx_parse_unix_domain_url` trả lỗi "too long path in the unix domain socket" khi đường dẫn vượt `sizeof(saun->sun_path)` | Kiểm chứng (đọc mã nguồn) |
| glibc `sys/un.h`, Linux UAPI `linux/un.h`, `getconf` | `/usr/include/x86_64-linux-gnu/sys/un.h`; `/usr/include/linux/un.h` | §6.3.1: `sun_path[108]` (`UNIX_PATH_MAX 108`); `NAME_MAX` = 255 | Kiểm chứng (chạy thử Linux 6.18, Python 3: `bind` đường dẫn 107 byte thành công, 108 byte lỗi "AF_UNIX path too long"; `getconf NAME_MAX /` = 255) |
| Red Hat Application Streams Life Cycle | https://access.redhat.com/support/policy/updates/rhel-app-streams-life-cycle | Bảng §3.2 | Kiểm chứng |
| RHEL 10 release notes — Distribution of content | https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/10.0_release_notes/distribution | RHEL 10 không phân phối Application Stream dạng module | Kiểm chứng (qua trích dẫn kết quả tìm kiếm của trang chính thức) |
| Remi Configuration Wizard | https://rpms.remirepo.net/wizard/ (EL 9, PHP 8.4, "Multiple versions" và "Single version") | Lệnh kho, `dnf install php84`, `php84-php-xxx`, `php84-syspaths`, `dnf module switch-to php:remi-8.4`; 8.4.26 ổn định, 8.4.27RC1 ở `remi-test` | Kiểm chứng |
| Alpine packages | https://pkgs.alpinelinux.org/contents?branch=v3.22&name=php84-fpm&arch=x86_64&repo=community; https://pkgs.alpinelinux.org/packages?name=php8*-fpm&branch=v3.24 | Đường dẫn `/etc/init.d/php-fpm84`, `/etc/php84/php-fpm.d/www.conf`; nhánh theo bản Alpine | Kiểm chứng |
| Alpine releases | https://alpinelinux.org/releases.json | Hạn hỗ trợ v3.22–v3.24 | Kiểm chứng |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `pkg_owner`, `php_upgrade`, `php_mitigate`, `php_sapis_note`, `restart_php_services` | Đã đọc |
