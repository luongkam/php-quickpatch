---
id: DOC-AC-QP-PTCH
title: Tiêu chí chấp nhận — module PTCH, CLI, RPT (vá cùng nhánh, dòng lệnh, báo cáo) — php-quickpatch v2
version: 1.0.2
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, patch, rollback, manifest, cli, json, report, v0.1-compat]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-ENV-001
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module PTCH, CLI, RPT

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 64 scenario: `US-PTCH-01..09` (`AC-PTCH-01..28`), `US-CLI-01..10` (`AC-CLI-01..30`), `US-RPT-01..02` (`AC-RPT-01..06`); chuỗi thông báo kế thừa đối chiếu `php-quickpatch.sh` v0.1.0 |
| 1.0.1 | 2026-10-22 | BA Agent | Thêm bước `Given` cho `@AC-CLI-24` và `@AC-RPT-06`; gom biên khoảng `--from`/`--to` (366/367 ngày, `from` = `to`, `from` > `to`) về `@AC-RPT-06`; đổi `@AC-CLI-24` sang biên tập giá trị `--format`; thêm mã thoát (`BR-CLI-004`) vào tham chiếu US-CLI-08, US-RPT-02 |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review rule 08 (mỗi story ≥ 1 `@boundary`; `@security` không thay `@boundary`): thêm 4 scenario `@boundary` mới đánh số tiếp theo số lớn nhất của module — `@AC-PTCH-29` (US-PTCH-04, 0/1 package còn lỗ hổng sau vá, chuỗi kết quả đối chiếu `audit_lockfile` v0.1), `@AC-PTCH-30` (US-PTCH-05, 0 plugin cần cập nhật, dung lượng trống = S + 50 MB / S + 49 MB theo `FR-PTCH-WP-001`), `@AC-CLI-31` (US-CLI-01, U+0001/U+001F phải escape, U+0020/U+007F ngay ngoài dải, 0 runtime → mảng rỗng), `@AC-RPT-07` (US-RPT-01, HTML 5.242.880/5.242.881 byte, CSV 0 finding); thêm `BR-SCN-017`, `ERR-ENV-507-01` vào tham chiếu US-PTCH-05; thêm mục Tài liệu tham chiếu. Tổng 68 scenario |

Ký hiệu dùng chung: [acceptance-criteria.md §1.2](acceptance-criteria.md). Chuỗi tiếng Anh trong ngoặc kép là thông báo CLI giữ nguyên từ v0.1 (`BR-CLI-002`); "script" = `/usr/local/sbin/php-quickpatch.sh` trong môi trường kiểm thử.

## 1. Module PTCH

## Story: US-PTCH-01 - Vá PHP cùng nhánh
Tham chiếu: `FR-PTCH-PHP-001`, `FR-PTCH-PHP-002` · `BR-PTCH-001`, `BR-PTCH-002`, `BR-PTCH-003`, `BR-SCN-008` · `ERR-PTCH-424-01`, `ERR-PTCH-403-01` · `NFR-USE-001`

```gherkin
Feature: US-PTCH-01 Vá PHP cùng nhánh

  @AC-PTCH-01 @happy-path
  Scenario: Nâng gói dpkg từ 8.2.34 lên 8.2.35
    Given máy kiểm thử chuẩn, "/usr/bin/php8.2" bản 8.2.34 thuộc các gói dpkg "php8.2-cli", "php8.2-fpm", "php8.2-mysql" và kho đã có 8.2.35
    When người vận hành chạy "php-quickpatch.sh fix --only php"
    Then tool chạy "apt-get install -y -q --only-upgrade -o Dpkg::Options::=--force-confold" với đúng 3 gói đã cài của build
    And manifest của lượt có dòng "note" cho việc nâng gói
    And dòng kết quả có "PHP 8.2.35" kèm "now has the fix", runtime chuyển "ok" và cờ restart PHP được bật

  @AC-PTCH-02 @boundary
  Scenario Outline: Nhóm gói theo nguồn cài
    Given binary PHP thuộc gói "<goi>" quản lý bởi "<pm>"
    When tool xác định nhóm gói cần nâng
    Then biểu thức nhóm là "<nhom>"

    Examples:
      | pm   | goi             | nhom              |
      | dpkg | ea-php82-php-cli | ea-php[0-9]+      |
      | rpm  | alt-php82-cli    | alt-php[0-9]+     |
      | dpkg | lsphp82          | lsphp[0-9]+       |
      | apk  | php82            | php[0-9]*         |
      | dpkg | custom-php-test  | php               |

  @AC-PTCH-03 @negative
  Scenario: Kho chưa có bản vá
    Given kho gói chỉ có 8.2.34 cho nhánh 8.2 và "min_patched_sec" = "8.2.35"
    When người vận hành chạy "php-quickpatch.sh fix --only php"
    Then sau khi nâng gói, runtime vẫn là 8.2.34 và kết quả chứa "ERR-PTCH-424-01"
    And file mitigation tạm được ghi theo AC-PTCH-05, issue mức "critical" còn mở và mã thoát là 1

  @AC-PTCH-04 @boundary
  Scenario: Dry-run không thay đổi gói
    Given runtime PHP 8.2.34 "vulnerable"
    When người vận hành chạy "php-quickpatch.sh fix --only php --dry-run"
    Then lệnh in câu lệnh nâng gói sẽ chạy
    And 0 gói thay đổi phiên bản, không thư mục "STATE_DIR/backups/<run_id>" nào được tạo
```

## Story: US-PTCH-02 - Mitigation ini tạm thời
Tham chiếu: `FR-PTCH-MIT-001`, `FR-PTCH-MIT-002` · `BR-PTCH-004`, `BR-SCN-017` · `ERR-PTCH-412-01`

```gherkin
Feature: US-PTCH-02 Mitigation ini tạm thời

  @AC-PTCH-05 @happy-path
  Scenario: Ghi mitigation rồi tự gỡ khi đã vá
    Given runtime PHP 8.5.11 có CVE chưa vá khớp 1 luật trong "mitigations.json" và build có 2 thư mục conf.d (fpm, cli)
    When người vận hành chạy "php-quickpatch.sh fix --only php" trong lúc kho chưa có 8.5.12
    Then file "zz-php-quickpatch-mitigation.ini" được ghi vào cả 2 thư mục conf.d, mỗi file có 1 dòng "created" trong manifest
    And nội dung có dòng "fatal_error_backtraces = 0" vì luật chỉ áp dụng nhánh 8.5
    And ở lượt "fix" sau khi runtime lên 8.5.12 ("ok"), 2 file được sao lưu (dòng "copy") rồi xoá và cờ restart được bật

  @AC-PTCH-06 @negative
  Scenario: Build không có thư mục conf.d
    Given runtime "/srv/test/php/bin/php" chưa vá và "--ini" không trả thư mục quét nào
    When người vận hành chạy "php-quickpatch.sh fix --only php"
    Then kết quả chứa "ERR-PTCH-412-01" ("No conf.d scan dir for /srv/test/php/bin/php; set the mitigation in its php.ini by hand.")
    And không file "php.ini" nào bị sửa

  @AC-PTCH-07 @boundary
  Scenario: Không ghi đè file đã có và tuỳ chọn --no-memlimit
    Given thư mục conf.d đã có "zz-php-quickpatch-mitigation.ini" do người vận hành sửa tay
    And luật mitigation có dòng "memory_limit"
    When người vận hành chạy "php-quickpatch.sh fix --only php --no-memlimit"
    Then file có sẵn giữ nguyên SHA-256
    And file mitigation mới ở thư mục conf.d khác không có dòng "memory_limit"
```

## Story: US-PTCH-03 - Vá Node.js cùng major
Tham chiếu: `FR-PTCH-NODE-001` · `BR-PTCH-005`, `BR-SEC-005` · `ERR-PTCH-502-01`, `ERR-PTCH-424-01`

```gherkin
Feature: US-PTCH-03 Vá Node.js cùng major

  @AC-PTCH-08 @happy-path
  Scenario: Nâng Node.js tarball trong /usr/local
    Given "/usr/local/bin/node" bản v24.21.0 (tarball, x64), "min_patched" dòng 24 = "24.22.1"
    When người vận hành chạy "php-quickpatch.sh fix --only node"
    Then tool tải "node-v24.22.1-linux-x64.tar.xz" từ nodejs.org và kiểm SHA-256 theo "SHASUMS256.txt"
    And "bin", "include", "lib/node_modules/npm", "lib/node_modules/corepack", "share/doc/node" được sao lưu với dòng "untar" trong manifest
    And "/usr/local/bin/node --version" trả "v24.22.1"

  @AC-PTCH-09 @negative
  Scenario: Tarball sai checksum
    Given file tải về có SHA-256 khác dòng tương ứng trong "SHASUMS256.txt"
    When người vận hành chạy "php-quickpatch.sh fix --only node"
    Then file tải về bị xoá, kết quả chứa "ERR-PTCH-502-01" và prefix "/usr/local" không thay đổi

  @AC-PTCH-10 @boundary
  Scenario Outline: Nguồn cài và kiến trúc
    Given Node.js dòng 24 chưa vá cài theo "<nguon>" trên kiến trúc "<arch>"
    When người vận hành chạy "php-quickpatch.sh fix --only node"
    Then kết quả là "<ket_qua>"

    Examples:
      | nguon         | arch    | ket_qua                                              |
      | tarball       | arm64   | tải bản arm64 và nâng như AC-PTCH-08                  |
      | tarball       | riscv64 | issue mức "high", không tải file                      |
      | nvm           | x64     | tạo mục SEMI theo PB-016, không nâng tự động          |
      | gói NodeSource | x64    | nâng gói; kho chưa có bản vá → "ERR-PTCH-424-01"      |
```

## Story: US-PTCH-04 - Vá package Composer/npm
Tham chiếu: `FR-PTCH-DEP-001`, `FR-PTCH-DEP-002` · `BR-PTCH-006` · `ERR-PTCH-424-02`

```gherkin
Feature: US-PTCH-04 Vá package Composer/npm

  @AC-PTCH-11 @happy-path
  Scenario: Cập nhật package Composer có lỗ hổng
    Given dự án "/var/www/shop.test" thuộc user "shop" có finding "vendor-test/lib" 1.2.0, bản sửa 1.2.5
    When người vận hành chạy "php-quickpatch.sh fix --only composer"
    Then manifest có dòng "composer-install" và bản sao "composer.json", "composer.lock"
    And lệnh "composer update vendor-test/lib --with-all-dependencies --no-interaction --no-progress" chạy dưới uid của "shop"
    And OSV tra lại cho kết quả 0 advisory với "vendor-test/lib"

  @AC-PTCH-12 @negative
  Scenario: composer update thất bại
    Given "composer update" của dự án trả exit 2
    When người vận hành chạy "php-quickpatch.sh fix --only composer"
    Then "composer.json" và "composer.lock" được khôi phục từ backup và "composer install" được chạy lại
    And kết quả chứa "ERR-PTCH-424-02" ("/var/www/shop.test: composer update failed, lockfile restored (see log).") và issue mức "high"

  @AC-PTCH-13 @security
  Scenario: npm không dùng --force và chạy dưới quyền chủ thư mục
    Given dự án npm "/home/shop/app" thuộc user "shop" có 2 finding
    When người vận hành root chạy "php-quickpatch.sh fix --only npm"
    Then lệnh chạy là "npm audit fix --no-fund" không có "--force"
    And tiến trình npm có uid của "shop", không phải uid 0

  @AC-PTCH-29 @boundary
  Scenario Outline: Số package có lỗ hổng trước và sau khi vá
    Given dự án Composer "/var/www/shop.test" có <truoc> package có advisory trong "composer.lock" theo OSV, không package nào mang mã "MAL-*"
    And nếu "composer update" chạy, OSV tra lại còn <sau> package có advisory
    When người vận hành chạy "php-quickpatch.sh fix --only composer"
    Then kết quả là "<ket_qua>"

    Examples:
      | truoc | sau | ket_qua                                                                                                                            |
      | 0     | 0   | in "[OK] /var/www/shop.test/composer.lock: no known vulnerable packages."; "composer update" không chạy, 0 dòng manifest cho dự án |
      | 2     | 0   | mục "Summary" có "FIXED: /var/www/shop.test: 2 vulnerable Packagist package(s) updated", 0 issue cho dự án                        |
      | 2     | 1   | "Summary" có "FIXED: /var/www/shop.test: 1 vulnerable Packagist package(s) updated" và "HIGH: /var/www/shop.test: 1 vulnerable Packagist package(s) left; they need a manual major upgrade"; mã thoát 1 |
```

## Story: US-PTCH-05 - Cập nhật WordPress và kiểm toàn vẹn
Tham chiếu: `FR-PTCH-WP-001`, `FR-PTCH-WP-002` · `BR-PTCH-006`, `BR-FEED-025`, `BR-SEC-003`, `BR-SEC-005`, `BR-SCN-017` · `ERR-PTCH-424-03`, `ERR-PTCH-424-04`, `ERR-ENV-507-01`

```gherkin
Feature: US-PTCH-05 Cập nhật WordPress và kiểm toàn vẹn

  @AC-PTCH-14 @happy-path
  Scenario: Cập nhật WordPress 7.0.2 lên trên mốc vá
    Given site "/var/www/blog.test" chạy WordPress 7.0.2, "min_patched" nhánh 7.0 = "7.0.7"
    When người vận hành chạy "php-quickpatch.sh fix --only wp"
    Then "wp-cli.phar" được kiểm SHA-512 trước khi dùng
    And "wp core update --minor" và "wp plugin update --all --patch" chạy dưới quyền chủ site
    And phiên bản sau cập nhật ≥ "7.0.7" và "wp core verify-checksums" đạt

  @AC-PTCH-15 @negative
  Scenario: Không có wp-cli
    Given máy không có "wp" và không tải được "wp-cli.phar"
    When người vận hành chạy "php-quickpatch.sh fix --only wp"
    Then kết quả chứa "ERR-PTCH-424-03" ("wp-cli unavailable, update WordPress core to 7.0.7 by hand")
    And không file nào của site bị sửa

  @AC-PTCH-16 @security
  Scenario: File core bị sửa được báo cáo, không bị xoá
    Given file "wp-includes/load.php" của site khác checksum wordpress.org
    When người vận hành chạy "php-quickpatch.sh fix --only wp"
    Then kết quả chứa "ERR-PTCH-424-04" ("blog.test: core files differ from wordpress.org checksums (possible tampering)") và issue mức "high"
    And file "wp-includes/load.php" giữ nguyên SHA-256, quyền và vị trí
    And plugin không xác minh được checksum chỉ tạo cảnh báo

  @AC-PTCH-30 @boundary
  Scenario Outline: Số plugin cần cập nhật và dung lượng sao lưu
    Given site "/var/www/blog.test" chạy WordPress 7.0.2, "min_patched" nhánh 7.0 = "7.0.7" và "wp plugin list --update=available --field=name" trả <n> plugin
    And S là tổng kích thước "wp-admin", "wp-includes", file "*.php" ở gốc site và <n> thư mục plugin đó; phân vùng chứa STATE_DIR còn "<trong>" trống
    When người vận hành chạy "php-quickpatch.sh fix --only wp"
    Then kết quả là "<ket_qua>"

    Examples:
      | n | trong     | ket_qua                                                                                                                  |
      | 0 | S + 50 MB | manifest có đúng 1 dòng "untar" (tar core "wp-<site_hash>-core.tar.gz"), 0 dòng "untar" cho plugin; "wp core update --minor" chạy |
      | 3 | S + 50 MB | manifest có 4 dòng "untar" (1 core + 3 plugin), 0 dòng "copy" cho "version.php"; phiên bản sau cập nhật ≥ "7.0.7"         |
      | 3 | S + 49 MB | bỏ qua site với "ERR-ENV-507-01": 0 file của site bị sửa, 0 lệnh "wp core update" chạy, issue mức "critical" của site còn mở |
```

## Story: US-PTCH-06 - Tag image Docker và mitigation container
Tham chiếu: `FR-PTCH-DKR-001`, `FR-PTCH-DKR-002` · `BR-ENV-011`, `BR-DATA-002`, `BR-PTCH-004`, `BR-ENV-009` · `ERR-PTCH-412-01`

```gherkin
Feature: US-PTCH-06 Tag image Docker và mitigation container

  @AC-PTCH-17 @happy-path
  Scenario: Nâng tag ghim bản cũ trong Dockerfile và compose
    Given "Dockerfile" có "FROM php:8.2.34-fpm" và "compose.yaml" có "image: node:24.21.0"
    When người vận hành chạy "php-quickpatch.sh fix --only docker"
    Then 2 file được sao lưu rồi sửa thành "FROM php:8.2.35-fpm" và "image: node:24.22.1"
    And issue "cần rebuild/redeploy" được tạo cho mỗi file và không lệnh "docker build", "docker push" nào được chạy

  @AC-PTCH-18 @negative
  Scenario: Container PHP chưa vá không có thư mục conf.d
    Given container "web-test" chạy PHP 8.2.34 và không có thư mục conf.d
    When người vận hành chạy "php-quickpatch.sh fix --only docker"
    Then kết quả chứa "ERR-PTCH-412-01" cho container "web-test"
    And container có thư mục conf.d được ghi file mitigation, "docker restart" và issue mức "critical" "cần rebuild image"

  @AC-PTCH-19 @boundary
  Scenario Outline: Các dạng tag image
    Given Dockerfile có dòng "<dong>"
    When người vận hành chạy "php-quickpatch.sh fix --only docker <tuy_chon>"
    Then kết quả là "<ket_qua>"

    Examples:
      | dong                  | tuy_chon     | ket_qua                                            |
      | FROM php:8.2-fpm      |              | không sửa file, ghi chú cần "--pull" khi build     |
      | FROM php:7.4-fpm      |              | không sửa file, issue mức "high" nhánh EOL          |
      | FROM php:8.2.34-fpm   | --no-restart | sửa file; container không bị restart               |
```

## Story: US-PTCH-07 - Restart dịch vụ sau vá
Tham chiếu: `FR-PTCH-RST-001` · `BR-PTCH-007` · `ERR-CLI-423-01`

```gherkin
Feature: US-PTCH-07 Restart dịch vụ sau vá

  @AC-PTCH-20 @happy-path
  Scenario: Restart unit khớp mẫu gồm Remi SCL
    Given lượt "fix" đã nâng PHP và cờ restart bật; systemd đang chạy "php8.2-fpm.service", "php84-php-fpm.service", "nginx.service"
    When lượt "fix" tới bước restart
    Then "php8.2-fpm.service" và "php84-php-fpm.service" được restart
    And trên máy cPanel, tool chạy "/scripts/restartsrv_apache_php_fpm" và "/scripts/restartsrv_httpd"

  @AC-PTCH-21 @negative
  Scenario: Lượt fix không chạy được vì khoá bận
    Given một lượt "php-quickpatch.sh fix" khác đang giữ "STATE_DIR/.lock"
    When người vận hành chạy "php-quickpatch.sh fix"
    Then lệnh in "Another php-quickpatch run is in progress." tương ứng "ERR-CLI-423-01" với mã thoát 2
    And 0 dịch vụ bị restart

  @AC-PTCH-22 @boundary
  Scenario: --no-restart và lượt không thay đổi
    Given lượt "fix --no-restart" đã nâng PHP
    When lượt tới bước restart
    Then 0 dịch vụ bị restart và issue mức "high" "PHP services not restarted" được tạo
    And lượt "fix" không thay đổi gì thì không restart dịch vụ nào
```

## Story: US-PTCH-08 - Backup manifest theo lượt
Tham chiếu: `FR-PTCH-RBK-001` · `BR-SCN-017`, `BR-PTCH-008` · `ERR-ENV-507-01` · `NFR-ENV-05`, `NFR-CAP-003`

```gherkin
Feature: US-PTCH-08 Backup manifest theo lượt

  @AC-PTCH-23 @happy-path
  Scenario: Manifest ghi trước thay đổi đầu tiên
    Given lượt "fix" bắt đầu lúc "2026-10-22T10:42:01Z" sẽ sửa 1 file conf.d và nâng 1 dự án Composer
    When lượt "fix" chạy
    Then thư mục "STATE_DIR/backups/20261022-104201/" có "manifest" và "files/"
    And mọi dòng manifest có dạng "ACTION<TAB>ARG1<TAB>ARG2" và được ghi trước khi file tương ứng bị đổi
    And mục "Summary" in dòng "rollback: <script> rollback 20261022-104201"

  @AC-PTCH-24 @negative
  Scenario: Không đủ dung lượng ghi backup
    Given phân vùng chứa STATE_DIR còn 49 MB trống
    When người vận hành chạy lệnh thay đổi hệ thống
    Then lệnh dừng với "ERR-ENV-507-01" trước thay đổi đầu tiên và 0 file hệ thống bị sửa

  @AC-PTCH-25 @boundary
  Scenario: Dry-run và dung lượng backups lớn
    Given "STATE_DIR/backups/" chiếm 1,1 GiB
    When người vận hành chạy "php-quickpatch.sh fix --dry-run" rồi "php-quickpatch.sh fix"
    Then lượt dry-run không tạo thư mục backup
    And lượt thật in cảnh báo "backups/" > 1 GiB và không xoá thư mục backup nào
```

## Story: US-PTCH-09 - Rollback một lượt chạy
Tham chiếu: `FR-PTCH-RBK-002` · `BR-PTCH-008` · `ERR-PTCH-404-01`, `ERR-ENV-500-03` · `NFR-REL-005`

```gherkin
Feature: US-PTCH-09 Rollback một lượt chạy

  @AC-PTCH-26 @happy-path
  Scenario: Rollback lượt mới nhất
    Given lượt "20261022-104201" có các dòng "copy", "created", "composer-install", "note" và SHA-256 của mọi file trước lượt được ghi lại
    When người vận hành chạy "php-quickpatch.sh rollback"
    Then manifest được phát lại theo thứ tự ngược; file "created" bị xoá, file "copy" được khôi phục, "composer install" chạy lại
    And 100% file có dòng "copy" trở về SHA-256 trước lượt
    And dòng "note" được in thành cảnh báo và lệnh in "Rollback done. Package upgrades (apt/dnf/yum) are kept."

  @AC-PTCH-27 @negative
  Scenario: ID lượt không tồn tại
    Given không có thư mục "STATE_DIR/backups/20991231-000000"
    When người vận hành chạy "php-quickpatch.sh rollback 20991231-000000"
    Then lệnh in "No backup run found in" kèm đường dẫn thư mục backup, tương ứng "ERR-PTCH-404-01", mã thoát 2

  @AC-PTCH-28 @boundary
  Scenario: Lượt có dòng switch dùng quy trình rollback site
    Given lượt "20261022-111500" có dòng "switch<TAB>shop.test<TAB>8.1>8.4"
    And cấu hình khôi phục của Nginx không qua "nginx -t"
    When người vận hành chạy "php-quickpatch.sh rollback 20261022-111500"
    Then tool dùng quy trình R1–R7 của rollback site
    And kết quả chứa "ERR-ENV-500-03" và Nginx không bị reload
```

## 2. Module CLI

## Story: US-CLI-01 - Envelope --json
Tham chiếu: `FR-CLI-JSON-001` · `BR-CLI-001`, `BR-FEED-059`, `BR-SEC-006` · `ERR-CLI-400-01` · `NFR-CMP-004`

```gherkin
Feature: US-CLI-01 Envelope --json

  @AC-CLI-01 @happy-path
  Scenario: scan --json in đúng 1 tài liệu JSON
    Given máy kiểm thử chuẩn và bundle mẫu 2026-10-22
    When CI chạy "php-quickpatch.sh scan --json > out.json 2> err.txt"
    Then "out.json" là đúng 1 tài liệu JSON UTF-8 hợp lệ có "schema" = "qp.scan/1"
    And có các trường "tool", "generated_at", "host", "command", "dry_run", "exit_code", "data", "catalog_version", "result", "issues", "errors", "warnings"
    And văn bản cho người đọc chỉ nằm trong "err.txt" và file log; "exit_code" bằng mã thoát của tiến trình

  @AC-CLI-02 @negative
  Scenario: Tham số sai khi dùng --json
    Given máy kiểm thử chuẩn
    When CI chạy "php-quickpatch.sh scan --json --bogus"
    Then stdout là 1 tài liệu JSON có "errors[0].code" = "ERR-CLI-400-01" và "exit_code" = 2
    And mã thoát của tiến trình là 2

  @AC-CLI-03 @security
  Scenario: Escape chuỗi và che bí mật không cần jq
    Given máy không cài "jq", có thư mục dự án tên chứa dấu ngoặc kép, dấu "\" và ký tự tab
    And biến "QP_NVD_API_KEY" = "QPTESTKEY0001"
    When CI chạy "php-quickpatch.sh scan --json"
    Then đầu ra parse được bằng "python3 -m json.tool" và đường dẫn giữ đúng ký tự gốc sau khi parse
    And chuỗi "QPTESTKEY0001" xuất hiện 0 lần trong stdout, "command.argv" đã che giá trị bí mật bằng "***"

  @AC-CLI-31 @boundary
  Scenario Outline: Biên dải ký tự phải escape và mảng kết quả rỗng
    Given container kiểm thử Ubuntu 24.04 có Bash 5.2, "flock", "curl", không có "jq", chạy root, bundle mẫu 2026-10-22 và "<du_lieu>"
    When CI chạy "php-quickpatch.sh scan --json > out.json"
    Then "out.json" là đúng 1 tài liệu JSON parse được bằng "python3 -m json.tool"
    And kết quả là "<ket_qua>"

    Examples:
      | du_lieu                                                                 | ket_qua                                                                                                      |
      | thư mục dự án Composer "/var/www/a<U+0001>b" và "/var/www/c<U+001F>d"   | stdout chứa "\u0001" và "\u001f" (không phân biệt hoa thường), 0 byte 0x01 và 0x1F thô; "result.projects[].dir" sau parse giống tên gốc |
      | thư mục dự án Composer "/var/www/e<U+0020>f" và "/var/www/g<U+007F>h"   | JSON hợp lệ dù U+0020, U+007F không bắt buộc escape; "result.projects[].dir" sau parse giống tên gốc        |
      | 0 runtime PHP, 0 runtime Node.js, 0 thư mục dự án, 0 web server          | "result.runtimes" = [], "result.projects" = [] (không null, không thiếu khoá), "issues" = [], "exit_code" = 0 |
```

Ghi chú `@AC-CLI-31`: dải bắt buộc escape là U+0000–U+001F (RFC 8259 §7; [api-spec-cli-json.md §2](../api/api-spec-cli-json.md) "Mã hoá"). U+0000 không thể có trong tên file Linux nên biên dưới kiểm bằng U+0001; U+0020 và U+007F là giá trị ngay ngoài dải. Đã chạy thử `json.loads` của Python 3: chuỗi chứa byte 0x1F thô bị từ chối ("Invalid control character"), chuỗi chứa 0x7F thô được chấp nhận.

## Story: US-CLI-02 - Công bố JSON Schema
Tham chiếu: `FR-CLI-JSON-002` · `BR-CLI-001` · `ERR-CLI-400-01` · `NFR-CMP-004`

```gherkin
Feature: US-CLI-02 Công bố JSON Schema

  @AC-CLI-04 @happy-path
  Scenario: Schema của mọi lệnh được phát hành
    Given gói phát hành bản 2.0.0
    When CI liệt kê "share/php-quickpatch/schemas/" và chạy "php-quickpatch.sh schema scan"
    Then mỗi lệnh có file "qp.<lệnh>.v1.schema.json" với "$schema" là JSON Schema 2020-12
    And "schema scan" in đúng nội dung file "qp.scan.v1.schema.json"
    And 100% đầu ra mẫu của bộ test hồi quy hợp lệ theo schema tương ứng

  @AC-CLI-05 @negative
  Scenario: Lệnh không tồn tại
    Given gói phát hành bản 2.0.0
    When CI chạy "php-quickpatch.sh schema foo"
    Then lệnh báo "ERR-CLI-400-01" và mã thoát 2

  @AC-CLI-06 @boundary
  Scenario Outline: Quy tắc tăng major của schema
    Given schema hiện tại là "qp.scan/1"
    When bản phát hành mới "<thay_doi>"
    Then giá trị "schema" là "<schema>"

    Examples:
      | thay_doi                                | schema                                                              |
      | thêm trường "result.sites_count"        | qp.scan/1                                                           |
      | đổi tên trường "result.runtimes"        | qp.scan/2; "--json-schema 1" vẫn xuất "qp.scan/1" trong ≥ 2 bản minor kế tiếp |
```

## Story: US-CLI-03 - Tương thích ngược v0.1
Tham chiếu: `FR-CLI-COMP-001` · `BR-CLI-002`, `BR-CLI-004`, `BR-JOB-002` · `ERR-CLI-400-01`, `ERR-CLI-423-01` · `NFR-CMP-001`, `NFR-CMP-005`

```gherkin
Feature: US-CLI-03 Tương thích ngược v0.1

  @AC-CLI-07 @happy-path
  Scenario: Cú pháp v0.1 chạy không cần sửa script gọi
    Given cron gọi "php-quickpatch.sh fix --only php,node,composer,npm,wp,docker,webshell --no-memlimit" và máy không có python3
    When cron chạy lệnh
    Then đầu ra văn bản giữ tiền tố "[OK]", "[WARN]", "[VULN]", "[i]", mục "Summary" và dòng gợi ý "rollback:"
    And STATE_DIR là "/var/lib/php-quickpatch", log ghi vào "php-quickpatch.log", manifest giữ định dạng v0.1
    And 100% test hồi quy hành vi v0.1 đạt

  @AC-CLI-08 @negative
  Scenario: Tham số lạ và khoá bận
    Given máy kiểm thử chuẩn
    When người vận hành chạy "php-quickpatch.sh scan --foo"
    Then stderr có "Unknown argument: --foo" kèm usage, tương ứng "ERR-CLI-400-01", mã thoát 2
    And khi một lượt "fix" đang giữ khoá, "php-quickpatch.sh fix" in "Another php-quickpatch run is in progress." ("ERR-CLI-423-01") với mã thoát 2

  @AC-CLI-09 @boundary
  Scenario Outline: Mã thoát và khoá chia sẻ
    Given trạng thái "<trang_thai>"
    When người vận hành chạy "<lenh>"
    Then mã thoát là <ma>

    Examples:
      | trang_thai                          | lenh                    | ma |
      | không còn issue                      | php-quickpatch.sh scan  | 0  |
      | còn 1 issue mức high                 | php-quickpatch.sh scan  | 1  |
      | 1 lượt scan khác đang chạy           | php-quickpatch.sh scan  | 0  |
      | 1 lượt fix đang giữ khoá độc quyền   | php-quickpatch.sh scan  | 2  |
```

## Story: US-CLI-04 - Thay mảng ghi cứng bằng bundle
Tham chiếu: `FR-CLI-COMP-002` · `BR-DATA-002`, `BR-PTCH-001`, `BR-SEC-002` · `ERR-FEED-412-01` · `NFR-MNT-001`

```gherkin
Feature: US-CLI-04 Thay mảng ghi cứng bằng bundle

  @AC-CLI-10 @happy-path
  Scenario: Thông điệp lấy CVE từ dữ liệu online
    Given bundle mẫu 2026-10-22 và runtime PHP 8.2.34 upstream
    When người vận hành chạy "php-quickpatch.sh scan --only php"
    Then dòng "[VULN]" nêu "CVE-2026-109618" và "CVE-2026-109619" kèm "fixed in 8.2.35"
    And "php-quickpatch.sh" không chứa định nghĩa mảng "PHP_FIXED", "PHP_CVES", "NODE_FIXED", "WP_FIXED" (grep = 0 dòng)
    And mục "Environment" có dòng tuổi dữ liệu

  @AC-CLI-11 @negative
  Scenario: Dữ liệu STALE vẫn cho kết quả kèm cảnh báo
    Given bundle có "data_age_h" = 200
    When người vận hành chạy "php-quickpatch.sh scan" và "php-quickpatch.sh scan --json"
    Then đầu ra văn bản có dòng cảnh báo dữ liệu cũ 8 ngày và "warnings[]" chứa "ERR-FEED-412-01"
    And mã thoát ≥ 1

  @AC-CLI-12 @boundary
  Scenario: Advisory mới không cần bản script mới
    Given bundle mới (dữ liệu kiểm thử) thêm advisory nâng "min_patched" nhánh 8.3 lên "8.3.37"
    When người vận hành chạy "php-quickpatch.sh scan --only php" với runtime 8.3.36 upstream
    Then runtime 8.3.36 có trạng thái "vulnerable" mà "php-quickpatch.sh" giữ nguyên SHA-256
    And runtime 8.3.36 thuộc gói distro được quyết định theo chuỗi backport, không so số phiên bản upstream
```

## Story: US-CLI-05 - Lệnh assess
Tham chiếu: `FR-CLI-CMD-001` · `BR-CLI-001`, `BR-JOB-002` · `ERR-CLI-424-01`, `ERR-ASMT-404-01`, `ERR-CLI-423-01`

```gherkin
Feature: US-CLI-05 Lệnh assess

  @AC-CLI-13 @happy-path
  Scenario: Đánh giá dùng kết quả scan gần nhất
    Given "state/last-scan.json" tạo 2 giờ trước
    When CI chạy "php-quickpatch.sh assess --runtime-id php:3f2a9c1e0b7d --candidates --json"
    Then đầu ra có "schema" = "qp.assess/1" với "assessment.current" và "assessment.candidates[]"
    And không lượt scan mới nào được chạy

  @AC-CLI-14 @negative
  Scenario: Thiếu Python
    Given máy không có "python3"
    When CI chạy "php-quickpatch.sh assess --json"
    Then lệnh báo "ERR-CLI-424-01" ("assess requires Python 3.6+.") và mã thoát 2

  @AC-CLI-15 @boundary
  Scenario Outline: Tuổi kết quả scan và khoá
    Given "<dieu_kien>"
    When CI chạy "php-quickpatch.sh assess --bin /usr/bin/php8.2 --json"
    Then kết quả là "<ket_qua>"

    Examples:
      | dieu_kien                               | ket_qua                                   |
      | last-scan.json tạo 23 giờ 59 phút trước | dùng lại kết quả scan                      |
      | last-scan.json tạo 24 giờ 01 phút trước | chạy scan đọc trước rồi đánh giá           |
      | lượt fix đang giữ khoá độc quyền         | ERR-CLI-423-01, mã thoát 2                 |
```

## Story: US-CLI-06 - Lệnh plan
Tham chiếu: `FR-CLI-CMD-002` · `BR-PLAN-002`, `BR-PLAN-003`, `BR-CLI-003` · `ERR-PLAN-404-01`, `ERR-CLI-428-01`

```gherkin
Feature: US-CLI-06 Lệnh plan

  @AC-CLI-16 @happy-path
  Scenario: Vòng đời kế hoạch hoàn toàn từ terminal
    Given bundle mẫu 2026-10-22 và runtime "php:3f2a9c1e0b7d"
    When người vận hành lần lượt chạy "plan create --runtime-id php:3f2a9c1e0b7d --target 8.5", "plan list", "plan show <plan_id>", "plan approve <plan_id>"
    Then mỗi lệnh có "--json" trả "schema" = "qp.plan/1"
    And "plan show" liệt kê checklist, thứ tự site, dependency phải nâng và hạn duyệt; kế hoạch ở "approved" sau "plan approve"

  @AC-CLI-17 @negative
  Scenario: Mã kế hoạch hoặc mục không tồn tại
    Given không có kế hoạch "PLN-20261022-000000-ffff"
    When người vận hành chạy "plan show PLN-20261022-000000-ffff" và "plan item <plan_id> CHK-PHP-999-99 --set done --reason 'Đã kiểm tra thủ công xong'"
    Then cả 2 lệnh báo "ERR-PLAN-404-01" với mã thoát 2

  @AC-CLI-18 @boundary
  Scenario: plan run cần xác nhận khi không có TTY
    Given mục P2 "cài song song 8.5" của kế hoạch "approved"
    When script không có TTY chạy "plan run <plan_id> <chk_id>"
    Then lệnh báo "ERR-CLI-428-01" và 0 thay đổi
    And "plan run <plan_id> <chk_id> --dry-run" chạy thành công với 0 thay đổi; thêm "--yes" thì mục được thực thi
```

## Story: US-CLI-07 - Lệnh migrate và bí danh
Tham chiếu: `FR-CLI-CMD-003` · `BR-UPG-005`, `BR-CLI-003`, `BR-CLI-005` · `ERR-CLI-403-01`, `ERR-UPG-409-02`, `ERR-CLI-400-01`

```gherkin
Feature: US-CLI-07 Lệnh migrate và bí danh

  @AC-CLI-19 @happy-path
  Scenario Outline: Bí danh cho kết quả giống lệnh chuẩn
    Given máy kiểm thử chuẩn
    When người vận hành chạy "<bi_danh> --dry-run --json" và "<lenh_chuan> --dry-run --json" với cùng tham số
    Then 2 đầu ra có cùng "schema" = "qp.migrate/1" và cùng "result" (trừ "generated_at")

    Examples:
      | bi_danh                                   | lenh_chuan                                      |
      | upgrade --runtime php --target 8.5        | migrate install --runtime php --target 8.5      |
      | switch-site shop.test --target 8.5 --plan <plan_id> | migrate switch shop.test --target 8.5 --plan <plan_id> |
      | rollback-site shop.test                   | migrate rollback shop.test                      |

  @AC-CLI-20 @negative
  Scenario: Không root và chuyển site không có kế hoạch
    Given CLI chạy với EUID 1001
    When người vận hành chạy "php-quickpatch.sh migrate install --runtime php --target 8.5 --yes"
    Then lệnh báo "ERR-CLI-403-01" ("migrate install requires root.") với mã thoát 2
    And khi root chạy "migrate switch shop.test --target 8.5 --yes" không có "--plan" và không có "--no-plan", lệnh báo "ERR-UPG-409-02"

  @AC-CLI-21 @boundary
  Scenario Outline: Lý do của --no-plan
    Given site "shop.test" không thuộc kế hoạch nào
    When root chạy "migrate switch shop.test --target 8.5 --no-plan --reason '<ly_do>' --yes"
    Then kết quả là "<ket_qua>"

    Examples:
      | ly_do                 | ket_qua                                          |
      | Khẩn cấp vá PHP2She   | từ chối với ERR-CLI-400-01 (19 ký tự), mã thoát 2 |
      | Khẩn cấp vá PHP2Shel  | lượt chuyển được thực hiện (20 ký tự), audit ghi lý do |
```

## Story: US-CLI-08 - Lệnh report và audit
Tham chiếu: `FR-CLI-CMD-004` · `BR-RPT-001`, `BR-RPT-002`, `BR-RPT-003`, `BR-CLI-004` · `ERR-RPT-409-01`, `ERR-RPT-422-01`

```gherkin
Feature: US-CLI-08 Lệnh report và audit

  @AC-CLI-22 @happy-path
  Scenario: Xuất báo cáo và liệt kê audit
    Given bundle mẫu 2026-10-22 và audit có 120 bản ghi trong tháng 10/2026
    When kiểm toán viên chạy "report assess --format md --out /root/assess.md" và "audit list --from 2026-10-01 --to 2026-10-22 --json"
    Then file "/root/assess.md" được tạo với quyền 0600 và stdout in SHA-256 của file
    And "audit list" trả "schema" = "qp.audit/1" với 120 bản ghi

  @AC-CLI-23 @negative
  Scenario Outline: Tham số báo cáo không hợp lệ
    Given file "/root/assess.md" đã tồn tại
    When kiểm toán viên chạy "<lenh>"
    Then lệnh báo "<loi>" và không file nào bị ghi đè

    Examples:
      | lenh                                                  | loi            |
      | report assess --format md --out /root/assess.md       | ERR-RPT-409-01 |
      | report assess --format pdf --out /root/assess.pdf     | ERR-RPT-422-01 |

  @AC-CLI-24 @boundary
  Scenario Outline: Biên tập giá trị của --format
    Given bundle mẫu 2026-10-22, 3 runtime đã scan và file "/root/assess-<n>.<ext>" chưa tồn tại
    When kiểm toán viên chạy "php-quickpatch.sh report assess --format <format> --out /root/assess-<n>.<ext>"
    Then kết quả là "<ket_qua>"

    Examples:
      | n | format   | ext  | ket_qua                                                                   |
      | 1 | json     | json | tạo file quyền 0600 có "schema" = "qp.report.assess/1", stdout in SHA-256 |
      | 2 | csv      | csv  | tạo file quyền 0600, stdout in SHA-256                                    |
      | 3 | md       | md   | tạo file quyền 0600, stdout in SHA-256                                    |
      | 4 | html     | html | tạo file quyền 0600, stdout in SHA-256                                    |
      | 5 | markdown | md   | ERR-RPT-422-01, mã thoát 2, 0 file được tạo                               |
      | 6 | htm      | htm  | ERR-RPT-422-01, mã thoát 2, 0 file được tạo                               |
```

Ghi chú: biên độ dài khoảng `--from`/`--to` (366/367 ngày, `from` > `to`) chỉ kiểm ở `@AC-RPT-06` (US-RPT-02) để tránh trùng; `@AC-CLI-24` kiểm biên tập giá trị `--format` = {`json`, `csv`, `md`, `html`} của `FR-CLI-CMD-004`/`BR-RPT-001`, bổ sung cho giá trị ngoài tập "pdf" ở `@AC-CLI-23`.

## Story: US-CLI-09 - Dry-run và xác nhận trên CLI
Tham chiếu: `FR-CLI-SAFE-001` · `BR-CLI-003`, `BR-SCAN-001` · `ERR-CLI-428-01`

```gherkin
Feature: US-CLI-09 Dry-run và xác nhận trên CLI

  @AC-CLI-25 @happy-path
  Scenario: Xác nhận y/N trên terminal và dry-run
    Given người vận hành ở terminal SSH có TTY
    When người vận hành chạy "migrate install --runtime php --target 8.5 --dry-run" rồi chạy lại không có "--dry-run" và trả lời "y"
    Then lần dry-run in danh sách hành động, 0 gói thay đổi và không ghi manifest
    And lần chạy thật hỏi "y/N" trước khi thay đổi và thực hiện sau khi nhận "y"

  @AC-CLI-26 @negative
  Scenario: Không có TTY và thiếu --yes
    Given lệnh chạy từ cron không có TTY
    When cron chạy "php-quickpatch.sh migrate install --runtime php --target 8.5"
    Then lệnh báo "ERR-CLI-428-01" ("migrate install needs --yes when not interactive."), mã thoát 2 và 0 thay đổi

  @AC-CLI-27 @boundary
  Scenario: fix và rollback giữ hành vi v0.1
    Given lệnh chạy không có TTY
    When cron chạy "php-quickpatch.sh fix" và "php-quickpatch.sh rollback"
    Then cả 2 lệnh chạy không hỏi xác nhận như v0.1
    And lệnh ghi mới chạy có TTY, người vận hành nhấn Enter (mặc định "N") thì 0 thay đổi
```

## Story: US-CLI-10 - Kiểm quyền và môi trường chạy
Tham chiếu: `FR-CLI-ENV-001` · `BR-CLI-005`, `BR-PTCH-003` · `ERR-CLI-424-02`, `ERR-CLI-424-01`, `ERR-CLI-403-01` · `NFR-CMP-002`, `NFR-CMP-005`

```gherkin
Feature: US-CLI-10 Kiểm quyền và môi trường chạy

  @AC-CLI-28 @happy-path
  Scenario: Lệnh lõi chạy không cần Python
    Given máy có Bash 4.3, "flock", "curl", không có "python3", chạy root
    When người vận hành chạy "scan", "fix --dry-run", "rollback --dry-run", "migrate status"
    Then cả 4 lệnh chạy xong với mã thoát 0 hoặc 1

  @AC-CLI-29 @negative
  Scenario: Bash quá cũ hoặc thiếu flock
    Given máy có Bash 4.2
    When người vận hành chạy "php-quickpatch.sh scan"
    Then lệnh báo "ERR-CLI-424-02" ("Bash 4.3+ and flock are required (found: …).") và mã thoát 2
    And máy có Bash 5.2 nhưng thiếu "flock" cho cùng kết quả

  @AC-CLI-30 @boundary
  Scenario Outline: Python tối thiểu và quyền root
    Given máy có "<moi_truong>"
    When người vận hành chạy "<lenh>"
    Then kết quả là "<ket_qua>"

    Examples:
      | moi_truong                  | lenh                                   | ket_qua                                       |
      | Python 3.5, root            | php-quickpatch.sh serve                | ERR-CLI-424-01, mã thoát 2                    |
      | Python 3.6, root            | php-quickpatch.sh assess --json        | chạy                                          |
      | Python 3.12, EUID 1001      | php-quickpatch.sh fix --only php       | issue "needs root", lệnh tiếp tục như v0.1    |
      | Python 3.12, EUID 1001      | php-quickpatch.sh migrate install --runtime php --target 8.5 --yes | ERR-CLI-403-01, mã thoát 2 |
```

## 3. Module RPT

## Story: US-RPT-01 - Báo cáo đánh giá
Tham chiếu: `FR-RPT-ASMT-001` · `BR-RPT-001`, `BR-RPT-002`, `BR-RPT-003`, `BR-SEC-006` · `ERR-RPT-409-01`, `ERR-RPT-422-01` · SCR-010

```gherkin
Feature: US-RPT-01 Báo cáo đánh giá

  @AC-RPT-01 @happy-path
  Scenario: Báo cáo HTML 1 file
    Given bundle mẫu 2026-10-22, 3 runtime, 2 dự án Composer, 1 site WordPress, 1 kế hoạch
    When kiểm toán viên chạy "php-quickpatch.sh report assess --format html --out /root/assess.html"
    Then file là 1 tệp HTML ≤ 5 MiB, CSS nhúng, 0 thẻ "script", 0 URL tài nguyên ngoài
    And nội dung có máy chủ, môi trường, runtime + đánh giá + ứng viên, CVE/KEV, EOL/LTS, dependency, WordPress, kế hoạch và hạn duyệt
    And có "bundle_id", "fetched_at" từng nguồn, "catalog_version", phiên bản tool, "hostname", thời điểm tạo (UTC); stdout in SHA-256 và audit có 1 bản ghi

  @AC-RPT-02 @negative
  Scenario: File đích đã tồn tại
    Given file "/root/assess.html" đã tồn tại
    When kiểm toán viên chạy lại lệnh cùng "--out"
    Then lệnh báo "ERR-RPT-409-01" ("File /root/assess.html đã tồn tại; chọn tên khác.") và file cũ giữ nguyên SHA-256

  @AC-RPT-03 @security
  Scenario: CSV đúng chuẩn và che bí mật
    Given 1 finding có mô tả chứa dấu phẩy, dấu ngoặc kép và chuỗi "token=abc123"
    When kiểm toán viên chạy "report assess --format csv --out /root/assess.csv"
    Then file là CSV RFC 4180 UTF-8 có 1 dòng tiêu đề và 1 dòng mỗi finding, trường có dấu phẩy được bao ngoặc kép
    And chuỗi "abc123" xuất hiện 0 lần (được thay bằng "***") và quyền file là 0600

  @AC-RPT-07 @boundary
  Scenario Outline: Biên kích thước HTML và CSV không có finding
    Given bundle mẫu 2026-10-22, dữ liệu kiểm thử "<du_lieu>" và file "/root/assess-b<n>.<format>" chưa tồn tại
    When kiểm toán viên chạy "php-quickpatch.sh report assess --format <format> --out /root/assess-b<n>.<format>"
    Then kết quả là "<ket_qua>"

    Examples:
      | n | format | du_lieu                                          | ket_qua                                                                  |
      | 1 | html   | nội dung HTML dựng ra đúng 5.242.880 byte (5 MiB) | tạo file 5.242.880 byte, quyền 0600, stdout in SHA-256                    |
      | 2 | html   | nội dung HTML dựng ra 5.242.881 byte              | ERR-RPT-422-01 (đề xuất, xem ghi chú), mã thoát 2, 0 file được tạo        |
      | 3 | csv    | 3 runtime đã scan, 0 finding                      | file có đúng 1 dòng tiêu đề, 0 dòng dữ liệu, quyền 0600, stdout in SHA-256 |
```

Ghi chú `@AC-RPT-07`: `BR-RPT-001` giới hạn HTML ≤ 5 MiB nhưng [error-matrix.md](../srs/error-matrix.md) chưa nêu nguyên nhân "HTML vượt 5 MiB" cho `ERR-RPT-422-01` (hiện chỉ có định dạng không hỗ trợ và khoảng thời gian sai). Dòng `n` = 2 theo đề xuất [UC-RPT-001](../usecases/UC-RPT-001.md) luồng 5a và [api-spec.md §2.11](../api/api-spec.md) (job `FAILED`); chờ SRS bổ sung nguyên nhân này vào `ERR-RPT-422-01` trước khi chốt.

## Story: US-RPT-02 - Báo cáo bằng chứng thay đổi
Tham chiếu: `FR-RPT-AUD-001` · `BR-RPT-002`, `BR-AUD-003`, `BR-CLI-004` · `ERR-AUD-409-01`, `ERR-RPT-422-01` · SCR-010

```gherkin
Feature: US-RPT-02 Báo cáo bằng chứng thay đổi

  @AC-RPT-04 @happy-path
  Scenario: Báo cáo bằng chứng tháng 10/2026
    Given từ 2026-10-01 đến 2026-10-22 có 1 lượt "fix", 2 lượt chuyển site ("PASSED", "ROLLED_BACK"), 1 miễn trừ, 1 lần duyệt kế hoạch
    When kiểm toán viên chạy "report evidence --from 2026-10-01 --to 2026-10-22 --format json --out /root/ev.json"
    Then file có "schema" = "qp.report.evidence/1" và mỗi thay đổi có trạng thái trước/sau (phiên bản, gói), người chạy, người duyệt, miễn trừ, rollback
    And báo cáo trích dữ liệu từ audit, manifest, "switch.json", "hc.json" và có kết quả kiểm chuỗi hash "verified" = true
    And stdout in SHA-256 của file

  @AC-RPT-05 @negative
  Scenario: Chuỗi hash audit bị đứt
    Given bản ghi audit "seq" = 1532 bị sửa 1 byte
    When kiểm toán viên chạy "report evidence --from 2026-10-01 --to 2026-10-22 --format md --out /root/ev.md"
    Then báo cáo có mục kiểm toàn vẹn với "ERR-AUD-409-01" ("Nhật ký kiểm toán bị thay đổi từ bản ghi #1532.")
    And "verified" = false, "first_broken_seq" = 1532

  @AC-RPT-06 @boundary
  Scenario Outline: Khoảng thời gian báo cáo
    Given bundle mẫu 2026-10-22, audit có bản ghi từ 2025-10-20 tới 2026-10-22 và file "/root/ev-<n>.json" chưa tồn tại
    When kiểm toán viên chạy "php-quickpatch.sh report evidence --format json --out /root/ev-<n>.json --from <from> --to <to>"
    Then kết quả là "<ket_qua>"

    Examples:
      | n | from       | to         | ket_qua                                                                   |
      | 1 | 2025-10-21 | 2026-10-22 | tạo báo cáo (to − from = 366 ngày)                                        |
      | 2 | 2025-10-20 | 2026-10-22 | ERR-RPT-422-01 (to − from = 367 ngày), mã thoát 2, 0 file được tạo        |
      | 3 | 2026-10-22 | 2026-10-22 | tạo báo cáo (from = to, to − from = 0 ngày)                               |
      | 4 | 2026-10-22 | 2026-10-21 | ERR-RPT-422-01 (from > to 1 ngày), mã thoát 2, 0 file được tạo            |
```

## 4. Tài liệu tham chiếu
- RFC 8259 §7 "Strings" (https://www.rfc-editor.org/rfc/rfc8259#section-7): ký tự bắt buộc escape là dấu ngoặc kép, `\` và U+0000–U+001F — căn cứ `@AC-CLI-31`; kiểm chứng ngày 2026-10-22.
- `/home/user/php-quickpatch/php-quickpatch.sh` v0.1.0: `issue`/`fixed` dòng 56–61 (tiền tố `HIGH:`, `FIXED:` trong mục "Summary"), `audit_lockfile` dòng 533–563 (chuỗi "no known vulnerable packages.", "package(s) updated", "package(s) left; they need a manual major upgrade"), mã thoát dòng 878 — căn cứ `@AC-PTCH-29`.
- [functional-requirements.md](../srs/functional-requirements.md) `FR-PTCH-WP-001` (sao lưu tar core/plugin, ngưỡng dung lượng + 50 MB), `FR-CLI-JSON-001`, `FR-RPT-ASMT-001`; [business-rules.md](../srs/business-rules.md) `BR-RPT-001`; [api-spec-cli-json.md §2, §5](../api/api-spec-cli-json.md); [UC-RPT-001](../usecases/UC-RPT-001.md) luồng 5a.
