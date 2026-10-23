---
id: DOC-AC-QP-UPG
title: Tiêu chí chấp nhận — module UPG (cài song song, chuyển site, health check, rollback site) — php-quickpatch v2
version: 1.0.2
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, upgrade, site-switch, healthcheck, rollback, php-fpm, panel, nodejs, docker]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-ENV-004
  - DOC-SRS-QP-ENV-005
  - DOC-SRS-QP-ERR-001
related_diagrams:
  - DIAG-FLOW-QP-ENV-001
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module UPG

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 47 scenario cho `US-UPG-01..15` (`AC-UPG-01..47`); ngưỡng health check theo DOC-SRS-QP-ENV-002 (áp `BR-DATA-004`, chờ PO duyệt `Q-01`) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: `AC-UPG-22` thay Then "bị từ chối cho tới khi xác nhận" (không kiểm được) bằng mã thoát 2 + `ERR-UPG-409-03` (DOC-SRS-QP-ERR-001 v1.0.1, khớp UC-UPG-002 bước 2b1), job `migrate_switch` `FAILED`/`ERR-JOB-500-01`, vhost/pool của site giữ nguyên SHA-256; thêm bước xác nhận `migrate ack` theo `FR-UPG-ACK-001` (đề xuất `CR-FR-01`) có audit và mở lại chuyển site kế tiếp; dòng "Tham chiếu" của `US-UPG-07` thêm `FR-UPG-ACK-001`, `BR-AUD-001`, `ERR-UPG-409-03`, `ERR-JOB-500-01`; giữ 47 scenario |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review rule 08 (`US-UPG-14` chỉ có `@security`, chưa có `@boundary`; hướng (b) của [acceptance-criteria.md](acceptance-criteria.md) §1.3): thêm `AC-UPG-48` `@boundary` (đánh số tiếp theo số lớn nhất của module, không đổi mã cũ) — thời hạn ≤ 10 s của `HC-C0` phương pháp 5 cho dịch vụ Compose đích (DOC-SRS-QP-ENV-002 §3.4, §6.2; DOC-SRS-QP-ENV-005 §2.2): `healthy` tại T + 10 s → `HC_RUNNING`; còn `starting` tại T + 10 s hoặc `restarting` → `ROLLED_BACK`, `rollback_reason` = `HC-C0`, `ERR-SCN-500-01`, rollback (c1) trong `NFR-ENV-03`. Không dùng gợi ý "compose có 0 dịch vụ `php:`/`node:`" vì SRS không định nghĩa mã lỗi cho trường hợp này. Dòng "Tham chiếu" của `US-UPG-14` thêm `BR-HC-010`, `BR-SCN-010`, `ERR-SCN-500-01`, `NFR-ENV-03`. Tổng 48 scenario. Cần cập nhật theo ở file khác: [acceptance-criteria.md](acceptance-criteria.md) §1.3, §2, §3; cột AC của [backlog.md](backlog.md) (`AC-UPG-42..44` → thêm `AC-UPG-48`); thêm `TC-UPG-048` ở test-cases-upg.md và dòng tương ứng ở rtm.md |

Ký hiệu dùng chung: [acceptance-criteria.md §1.2](acceptance-criteria.md). Ví dụ chung: site `shop.test` (PB-005, Nginx + PHP-FPM, docroot `/var/www/shop.test`) chạy PHP 8.2 (`$OLD`), nhánh đích 8.5 (`$NEW`, `$NEW_BIN` = `/usr/bin/php8.5`), kế hoạch `PLN-20261022-103512-9b1c` ở trạng thái `approved`.

## Story: US-UPG-01 - Tiền điều kiện cài song song
Tham chiếu: `FR-UPG-PRE-001` · `BR-SCN-016`, `BR-ENV-004` · `ERR-SCN-412-01`

```gherkin
Feature: US-UPG-01 Tiền điều kiện cài song song

  @AC-UPG-01 @happy-path
  Scenario: Đạt mọi tiền điều kiện cài song song
    Given phân vùng cài còn 5 GB trống, "MemAvailable" = 900 MB, chạy root, Ubuntu 24.04 còn hỗ trợ, kho "packages.sury.org" có "php8.5-fpm"
    When người vận hành chạy "migrate install --runtime php --target 8.5 --dry-run --json"
    Then "preconditions[]" có từng dòng "check", "required", "actual", "pass" và mọi dòng "pass" = true

  @AC-UPG-02 @negative
  Scenario: Thiếu dung lượng đĩa
    Given phân vùng cài còn 1,9 GB trống
    When người vận hành chạy "migrate install --runtime php --target 8.5 --yes"
    Then lệnh báo "ERR-SCN-412-01" ("Máy chủ chưa đáp ứng điều kiện cài song song: …") nêu dung lượng 1,9 GB < 2 GB
    And 0 gói được cài

  @AC-UPG-03 @boundary
  Scenario Outline: Ngưỡng RAM khi tạo pool đích
    Given "MemAvailable" = <mem> MB, pool cũ có "pm.max_children" = 20 và RSS trung bình worker = 60 MB
    When tool kiểm tiền điều kiện tạo pool cho "shop.test"
    Then kết quả là "<ket_qua>"

    Examples:
      | mem   | ket_qua                                                            |
      | 1456  | đạt (cần 20 × 60 + 256 = 1.456 MB)                                 |
      | 1200  | không đạt; đề xuất "pm = ondemand", "pm.max_children" = 15         |
      | 300   | không đạt; đề xuất "pm = ondemand", "pm.max_children" = 2 (tối thiểu) |
```

## Story: US-UPG-02 - Cài runtime đích song song
Tham chiếu: `FR-UPG-INST-001` · `BR-UPG-001`, `BR-SCN-012`, `BR-SCN-026`, `BR-ENV-004`, `BR-ENV-010` · `ERR-ENV-424-01`, `ERR-SCN-412-01`

```gherkin
Feature: US-UPG-02 Cài runtime đích song song

  @AC-UPG-04 @happy-path
  Scenario: Cài PHP 8.5 cạnh PHP 8.2 trên Ubuntu
    Given máy kiểm thử chuẩn PB-001, "readlink -f /usr/bin/php" = "/usr/bin/php8.2" và tiền điều kiện đạt
    When người vận hành chạy "php-quickpatch.sh migrate install --runtime php --target 8.5 --yes"
    Then tool ghim mặc định bằng "update-alternatives --set" trước khi cài
    And sau khi cài, "/usr/bin/php8.5" chạy được, dịch vụ "php8.5-fpm" ở trạng thái "active"
    And "readlink -f /usr/bin/php" vẫn là "/usr/bin/php8.2" và 0 site bị đổi gán

  @AC-UPG-05 @negative
  Scenario: Lệnh cài thất bại
    Given kho không có gói "php8.5-fpm"
    When người vận hành chạy "migrate install --runtime php --target 8.5 --yes"
    Then lệnh báo "ERR-ENV-424-01" ("Cài PHP 8.5 thất bại: …")
    And liên kết mặc định "/usr/bin/php" không đổi

  @AC-UPG-06 @boundary
  Scenario Outline: Kho bên thứ ba và nguồn cài không cho phép
    Given môi trường "<moi_truong>"
    When người vận hành chạy "migrate install --runtime <rt> --target <dich>"
    Then kết quả là "<ket_qua>"

    Examples:
      | moi_truong                                  | rt   | dich | ket_qua                                                                  |
      | PB-001 chưa bật kho Surý                     | php  | 8.5  | mục SEMI thêm kho; file kho và khoá ký ghi dòng "created" trong manifest |
      | PB-002 RHEL 9 AppStream                      | php  | 8.5  | không cài song song; hướng dẫn PB-003 hoặc PB-013; không chạy "dnf module switch-to" |
      | Node.js gói distro "/usr/bin/node" dòng 22   | node | 24   | cài 24 bằng tarball dưới prefix riêng; "/usr/bin/node" không đổi        |
```

## Story: US-UPG-03 - Pool/handler đích và cấu hình
Tham chiếu: `FR-UPG-CFG-001`, `FR-UPG-CFG-002` · `BR-ENV-007`, `BR-SCN-045`, `BR-SCN-046`, `BR-SCN-017` · `ERR-ENV-500-01`, `ERR-ENV-424-01`

```gherkin
Feature: US-UPG-03 Pool/handler đích và cấu hình

  @AC-UPG-07 @happy-path
  Scenario: Tạo pool riêng và sao chép ini tuỳ chỉnh
    Given "shop.test" dùng pool chung "www" của 8.2 với "user = shop", "pm.max_children = 10"
    And "/etc/php/8.2/fpm/conf.d/99-shop.ini" không thuộc gói nào và "mysqli" có gói cho 8.5
    When tool chạy mục tạo pool/handler đích
    Then file pool "qp-shop.test" của 8.5 được tạo với socket "/run/php/qp-shop.test-8.5.sock", giữ "user", "group", "pm.*", có "error_log" = "/var/log/php-quickpatch/shop.test-8.5.error.log" và "pm.status_path = /qp-fpm-status"
    And "php-fpm8.5 -t" trả exit 0, manifest có dòng "created" cho file pool
    And "99-shop.ini" được sao chép sang thư mục cấu hình của 8.5, "php8.5-mysql" được cài và "/usr/bin/php8.5 -r 'exit(0);'" không in "Warning" hay "Fatal"

  @AC-UPG-08 @negative
  Scenario: Pool đích không khởi động
    Given file pool sinh ra có directive làm "php-fpm8.5 -t" trả exit 1
    When tool chạy mục tạo pool/handler đích
    Then kết quả có "ERR-ENV-500-01" ("Không tạo được pool PHP 8.5 cho shop.test.")
    And cấu hình đang phục vụ "shop.test" không thay đổi

  @AC-UPG-09 @boundary
  Scenario: Directive bị gỡ, extension thiếu và pool chung giữ nguyên
    Given ini tuỳ chỉnh có "track_errors = On" và extension "legacy_test" không có gói cho 8.5
    And file mitigation "zz-php-quickpatch-mitigation.ini" có trong conf.d của 8.2
    When tool sao chép cấu hình sang 8.5
    Then "cfg_report.dropped_directives[]" có "track_errors" kèm lý do, "not_transferable[]" có "legacy_test"
    And file mitigation không được sao chép và file pool "www" của 8.2 giữ nguyên SHA-256
```

## Story: US-UPG-04 - Chuyển 1 site (C1–C12)
Tham chiếu: `FR-UPG-SWT-001` · `BR-SCN-008`, `BR-SCN-018`, `BR-UPG-002`, `BR-ENV-003`, `BR-ENV-005`, `BR-ENV-006` · `ERR-ENV-409-01`, `ERR-ENV-500-02`, `ERR-SCN-424-01`, `ERR-ENV-412-01` · `NFR-ENV-01`, `NFR-ENV-04`, `NFR-ENV-05` · SCR-011

```gherkin
Feature: US-UPG-04 Chuyển 1 site (C1–C12)

  @AC-UPG-10 @happy-path
  Scenario: Chuyển shop.test sang 8.5 và đạt health check
    Given mục P3, P4 của "shop.test" ở "DONE", kết luận tương thích "PASS", pool đích đã tạo
    When người vận hành chạy "migrate switch shop.test --target 8.5 --plan PLN-20261022-103512-9b1c --yes"
    Then manifest có các dòng theo thứ tự "reload nginx", "switch shop.test 8.2>8.5", "copy <vhost>", "created <pool>" trước bước C7
    And "nginx -t" đạt rồi Nginx được graceful reload (không restart), bước C10 xác minh "accepted conn" của pool đích tăng ≥ 1
    And sau 600 s health check đạt, switch_record có "status" = "PASSED", mục P5/P6 của site chuyển "DONE"
    And đoạn C6–C10 kéo dài ≤ 30 s và 0 phản hồi 5xx với tải 20 request/giây quanh lúc reload

  @AC-UPG-11 @negative
  Scenario: Site khác đang trong health check
    Given site "blog.test" có lượt chuyển ở trạng thái "HC_RUNNING" còn 420 s
    When người vận hành chạy "migrate switch shop.test --target 8.5 --plan PLN-20261022-103512-9b1c --yes"
    Then lệnh báo "ERR-ENV-409-01" ("Site blog.test đang trong thời gian kiểm tra sau chuyển; chờ 420 giây.")
    And vhost và pool của "shop.test" không thay đổi

  @AC-UPG-12 @negative
  Scenario: Cấu hình web server lỗi sau khi đổi gán
    Given bước C7 ghi vhost mới làm "nginx -t" trả exit 1
    When lượt chuyển tới bước C8
    Then file vhost được khôi phục từ backup trong ≤ 5 s và Nginx không bị reload
    And kết quả có "ERR-ENV-500-02" và "shop.test" vẫn được phục vụ bởi PHP 8.2

  @AC-UPG-13 @boundary
  Scenario Outline: Điều kiện bước C2 và tuổi baseline
    Given trạng thái "<dieu_kien>"
    When người vận hành chạy lượt chuyển "shop.test"
    Then kết quả là "<ket_qua>"

    Examples:
      | dieu_kien                                   | ket_qua                                       |
      | mục P3 "CHK-PHP-010-12" còn "PENDING"        | ERR-SCN-424-01, lượt "ABORTED" trước C6       |
      | "/usr/bin/php8.5" không tồn tại             | ERR-ENV-412-01, lượt "ABORTED" trước C6       |
      | baseline có tuổi 120 s khi bắt đầu C7        | dùng baseline hiện có                         |
      | baseline có tuổi 121 s khi bắt đầu C7        | thu lại baseline trước C7                     |
```

## Story: US-UPG-05 - Chuyển site qua API panel
Tham chiếu: `FR-UPG-SWT-002` · `BR-ENV-002`, `BR-ENV-010`, `BR-ENV-012` · `ERR-ENV-502-01`

```gherkin
Feature: US-UPG-05 Chuyển site qua API panel

  @AC-UPG-14 @happy-path
  Scenario: Chuyển site cPanel bằng whmapi1
    Given máy cPanel (PB-007), site "shop.test" dùng "ea-php82" và "ea-php85" đã cài
    When người vận hành chạy lượt chuyển "shop.test" sang 8.5
    Then manifest có dòng "panel cpanel {"fn":"php_set_vhost_versions","version":"ea-php82","vhost":"shop.test","php_fpm":1}" trước lời gọi
    And file ".htaccess" của site được sao lưu trước khi gọi "whmapi1 php_set_vhost_versions"
    And giá trị đọc lại bằng "php_get_vhost_versions" là "ea-php85"

  @AC-UPG-15 @negative
  Scenario: Giá trị đọc lại khác giá trị mong muốn
    Given lời gọi panel trả thành công nhưng "php_get_vhost_versions" vẫn trả "ea-php82"
    When lượt chuyển tới bước kiểm đọc lại
    Then tool khôi phục theo dòng "panel" của manifest
    And kết quả có "ERR-ENV-502-01" ("Panel cpanel không áp dụng thay đổi cho shop.test: …")

  @AC-UPG-16 @boundary
  Scenario: Lệnh panel chưa kiểm chứng và file do panel sinh
    Given playbook PB-010 có lệnh cài "verified" = false
    And vhost của site PB-009 do Plesk sinh
    When người vận hành mở checklist và chạy lượt chuyển site PB-009
    Then lệnh "verified" = false chỉ hiển thị ở mức SEMI/MANUAL kèm nhãn "chưa kiểm chứng"
    And tool không sửa trực tiếp file vhost do Plesk sinh, chỉ gọi CLI chính thức của Plesk
```

## Story: US-UPG-06 - Chuyển mod_php sang PHP-FPM
Tham chiếu: `FR-UPG-SWT-003` · `BR-SCN-047`, `BR-CON-006` · `ERR-SCN-412-02`, `ERR-ENV-500-02`, `ERR-JOB-428-01`

```gherkin
Feature: US-UPG-06 Chuyển mod_php sang PHP-FPM

  @AC-UPG-17 @happy-path
  Scenario: Chuyển máy chủ 30 vhost từ mod_php sang PHP-FPM 8.2
    Given Apache có "php8.2_module" (PB-006) phục vụ 30 vhost
    When người vận hành chạy mục bước 1 PB-006 với dry-run hợp lệ và "confirm_retype" = "8.2"
    Then Apache phục vụ 30 vhost qua "proxy_fcgi" và "php8.2-fpm"
    And health check 600 s chạy trên cả 30 vhost và đạt
    And báo cáo ghi thời gian gián đoạn đo được

  @AC-UPG-18 @negative
  Scenario: 1 vhost không đạt health check sau khi chuyển FPM
    Given vhost "old.test" trả 500 sau khi chuyển sang PHP-FPM
    When health check của bước 1 kết thúc
    Then liên kết module và file cấu hình Apache được khôi phục, Apache được restart về "mod_php"
    And các site phụ thuộc nhận "ERR-SCN-412-02" ("Site old.test đang chạy mod_php; cần chuyển sang PHP-FPM trước khi đổi phiên bản.")

  @AC-UPG-19 @boundary
  Scenario Outline: Số vhost kiểm tra và xác nhận kép
    Given máy chủ có <n> vhost, trong đó 3 vhost có "hc_url"
    When người vận hành xác nhận bước 1 với "<retype>"
    Then kết quả là "<ket_qua>"

    Examples:
      | n  | retype           | ket_qua                                                   |
      | 50 | confirm_retype=8.2 | health check cả 50 vhost                                 |
      | 80 | confirm_retype=8.2 | health check 50 vhost ngẫu nhiên + 3 vhost có "hc_url"    |
      | 30 | không gửi          | ERR-JOB-428-01 ("details.constraint" = "retype_required") |
```

## Story: US-UPG-07 - Điều phối chuyển site theo kế hoạch
Tham chiếu: `FR-UPG-SEQ-001`, `FR-UPG-ACK-001` (đề xuất, `CR-FR-01`) · `BR-ENV-003`, `BR-UPG-003`, `BR-UPG-005`, `BR-SCN-008`, `BR-AUD-001` · `ERR-ENV-409-01`, `ERR-UPG-409-01`, `ERR-UPG-409-02`, `ERR-UPG-409-03`, `ERR-UPG-423-01`, `ERR-SCN-500-01`, `ERR-JOB-500-01` · SCR-009

```gherkin
Feature: US-UPG-07 Điều phối chuyển site theo kế hoạch

  @AC-UPG-20 @happy-path
  Scenario: Canary trước, site kế tiếp sau khi PASSED
    Given kế hoạch có "site_order" = ["a.test", "b.test", "c.test"], canary "a.test"
    When người vận hành chuyển "a.test" và lượt đạt "PASSED"
    Then nút chuyển "b.test" trên SCR-009 được mở; "c.test" vẫn khoá
    And mỗi lượt chuyển cần 1 dry-run và 1 xác nhận riêng; kế hoạch ở "in_progress"

  @AC-UPG-21 @negative
  Scenario: Chuyển site ngoài kế hoạch hoặc khi canary chưa xong
    Given "a.test" đang ở "HC_RUNNING"
    When người vận hành yêu cầu chuyển "b.test"
    Then yêu cầu bị từ chối với "ERR-ENV-409-01"
    And yêu cầu chuyển "z.test" (không thuộc kế hoạch "approved"/"in_progress" nào) từ console bị từ chối với "ERR-UPG-409-02"

  @AC-UPG-22 @negative
  Scenario: Canary bị tự rollback dừng các site còn lại tới khi được xác nhận
    Given kế hoạch "PLN-20261022-103512-9b1c" ở "in_progress" có "site_order" = ["a.test", "b.test", "c.test"], canary "a.test"
    And lượt chuyển "20261022-140000" của "a.test" kết thúc "ROLLED_BACK" với "ERR-SCN-500-01" và chưa có "acknowledged_at"
    And "b.test" có kết luận tương thích "PASS", mục P3/P4 ở "DONE" và máy chủ có 0 lượt ở "SWITCHED"/"HC_RUNNING"/"ROLLBACK_FAILED"
    When người vận hành chạy "migrate switch b.test --target 8.5 --plan PLN-20261022-103512-9b1c --yes --json"
    Then lệnh thoát mã 2 với "errors[0].code" = "ERR-UPG-409-03" ("Chưa thể chuyển b.test: …")
    And 0 switch_record được tạo cho "b.test"; file vhost và pool của "b.test" giữ nguyên SHA-256, lớp gán vẫn trỏ PHP 8.2
    And job "migrate_switch" cho "b.test" tạo từ SCR-009 kết thúc "FAILED" ("error.code" = "ERR-JOB-500-01") với "result.errors[0].code" = "ERR-UPG-409-03"
    And kế hoạch giữ "in_progress"
    And sau khi người vận hành chạy "migrate ack 20261022-140000 --reason 'Đã cài php8.5-intl còn thiếu trên pool đích' --json" (FR-UPG-ACK-001), lượt "20261022-140000" vẫn "ROLLED_BACK" với "acknowledged_at" khác rỗng, "result.acknowledgement.next_allowed_sites[]" chứa "b.test" và audit có 1 bản ghi "intent" + 1 bản ghi "result" mang "run_id" = "20261022-140000"
    And chạy lại lệnh ở bước When không còn "ERR-UPG-409-03" trong "errors[]" và switch_record của "b.test" được tạo ở "PREFLIGHT"

  @AC-UPG-23 @boundary
  Scenario: Khoá toàn máy sau ROLLBACK_FAILED và site chưa PASS
    Given lượt chuyển "a.test" ở "ROLLBACK_FAILED"
    And "d.test" có kết luận tương thích "FAIL"
    When người vận hành yêu cầu chuyển "b.test" rồi "d.test"
    Then yêu cầu chuyển "b.test" bị từ chối với "ERR-UPG-423-01"
    And sau khi người vận hành xác nhận đã xử lý "a.test", yêu cầu chuyển "d.test" bị từ chối với "ERR-UPG-409-01"
```

## Story: US-UPG-08 - Tập URL thăm dò và baseline
Tham chiếu: `FR-UPG-HC-001`, `FR-UPG-HC-003` · `BR-HC-001`, `BR-HC-002`, `BR-HC-004`, `BR-HC-005` · `ERR-HC-412-01`, `ERR-HC-412-02`, `ERR-HC-412-03`, `ERR-HC-422-02`

```gherkin
Feature: US-UPG-08 Tập URL thăm dò và baseline

  @AC-UPG-24 @happy-path
  Scenario: Trang chủ tự phát hiện, 3 URL khai báo và baseline 5 vòng
    Given vhost "shop.test" có "server_name _ shop.test www.shop.test", "listen 443 ssl" và 3 dòng "hc_url" cùng host
    When tool lập tập URL và thu baseline
    Then trang chủ là "https://shop.test:443/" gửi bằng "curl --resolve shop.test:443:127.0.0.1 --max-redirs 0"
    And request có "User-Agent: php-quickpatch-hc/<version>", "Accept-Encoding: identity", "Cache-Control: no-cache" và chỉ dùng phương thức GET
    And baseline gồm 5 vòng cách nhau 10 s cho 4 URL, "baseline.json" lưu "M(u)", "spread(u)", "P95_b(u)", "W0", byte offset và inode của từng file log

  @AC-UPG-25 @negative
  Scenario: Baseline trang chủ có mã HTTP khác nhau hoặc không có log lỗi
    Given 5 mẫu trang chủ trên 8.2 trả mã 200, 200, 502, 200, 200
    When tool thu baseline
    Then lượt chuyển "ABORTED" với "ERR-HC-412-02" mức High và site không bị đổi
    And khi không xác định được nguồn log lỗi nào, lượt "ABORTED" với "ERR-HC-412-01" trừ khi "hc_mode=skip" được duyệt

  @AC-UPG-26 @boundary
  Scenario: Giới hạn URL khai báo và host
    Given "sites.d/shop.test.conf" khai báo 12 dòng "hc_url", trong đó 1 URL có host "other.test"
    And site "ip.test" chỉ có "server_name _ 10.0.0.5"
    When tool lập tập URL
    Then "shop.test" giữ 10 URL khai báo đầu tiên hợp lệ, URL host "other.test" bị loại, mỗi URL bị loại có cảnh báo "ERR-HC-422-02"
    And "ip.test" nhận "ERR-HC-412-03" và phải khai báo ≥ 1 URL trước khi chuyển
```

## Story: US-UPG-09 - FastCGI probe trước chuyển
Tham chiếu: `FR-UPG-HC-002` · `BR-HC-003`, `BR-CMPT-004` · `ERR-HC-424-01`, `ERR-HC-424-02`

```gherkin
Feature: US-UPG-09 FastCGI probe trước chuyển

  @AC-UPG-27 @happy-path
  Scenario: Probe pool đích đạt
    Given pool "qp-shop.test" của 8.5 nghe "/run/php/qp-shop.test-8.5.sock" và docroot có "index.php"
    When tool chạy bước C4
    Then request FastCGI có "REQUEST_METHOD=GET", "SCRIPT_FILENAME=/var/www/shop.test/index.php", "HTTP_HOST=shop.test", "HTTPS=on"
    And nhận đủ "FCGI_END_REQUEST" trong ≤ 10 s, "Status" không bắt đầu bằng "5", stderr không có "PHP Fatal error"/"PHP Parse error", body không chứa "<?php"
    And kết quả probe được ghi vào "switch.json"

  @AC-UPG-28 @negative
  Scenario: Mã site lỗi Fatal trên 8.5
    Given "index.php" gọi hàm "each(" làm "FCGI_STDERR" có "PHP Fatal error: Uncaught Error: Call to undefined function each()"
    When tool chạy bước C4
    Then lượt chuyển "ABORTED" với "ERR-HC-424-01" ("Mã nguồn shop.test lỗi khi chạy thử trên PHP 8.5: …. Site chưa bị thay đổi.")
    And SHA-256 của vhost "shop.test" không đổi

  @AC-UPG-29 @boundary
  Scenario Outline: Trường hợp bỏ bước probe
    Given "<dieu_kien>"
    When tool chạy bước C4
    Then kết quả là "<ket_qua>"

    Examples:
      | dieu_kien                         | ket_qua                                            |
      | máy không có python3              | bỏ probe, cảnh báo "ERR-HC-424-02" mức Low, tiếp C5 |
      | site PB-011 dùng LSAPI            | bỏ probe, kiểm tra thay bằng bước C10              |
      | docroot không có "index.php"      | bỏ probe, tiếp C5                                  |
```

## Story: US-UPG-10 - Cửa sổ health check và báo cáo
Tham chiếu: `FR-UPG-HC-004`, `FR-UPG-HC-006` · `BR-HC-006`, `BR-HC-007`, `BR-HC-008`, `BR-HC-009`, `BR-HC-011`, `BR-HC-012` · `ERR-HC-422-01` · SCR-006

```gherkin
Feature: US-UPG-10 Cửa sổ health check và báo cáo

  @AC-UPG-30 @happy-path
  Scenario: 10 vòng đạt và báo cáo hiển thị trên SCR-006
    Given "shop.test" vừa qua C10 với 4 URL thăm dò và tham số mặc định
    When cửa sổ health check chạy
    Then vòng k chạy tại "t_C9 + (k − 1) × 60 s" với k = 1..10, mỗi vòng gửi tuần tự 1 request/URL (tổng 40 request)
    And "hc.json" có "verdict" = "PASS", "violations[]" rỗng và số liệu từng vòng
    And SCR-006 hiển thị bảng vòng × URL, biểu đồ thời gian phản hồi; "migrate healthcheck shop.test --json" trả cùng kết luận

  @AC-UPG-31 @negative
  Scenario: Tham số cấu hình ngoài khoảng
    Given "sites.d/shop.test.conf" đặt "hc.window_s = 100"
    When health check bắt đầu
    Then cảnh báo "ERR-HC-422-01" ("Giá trị hc.window_s=100 không hợp lệ; dùng mặc định 600.")
    And cửa sổ thực tế dài 600 s

  @AC-UPG-32 @boundary
  Scenario Outline: Ngưỡng tiêu chí ĐẠT
    Given baseline trang chủ 5 mẫu 48.100, 48.900, 49.200, 50.300, 51.000 byte, "P95_b" = 40 ms, "W0" = 10
    When "<quan_sat>"
    Then tiêu chí "<tieu_chi>" có kết quả "<ket_qua>"

    Examples:
      | quan_sat                                         | tieu_chi | ket_qua                         |
      | body 56.580 byte ở mọi vòng                       | HC-C4    | đạt                             |
      | body 56.581 byte ở 1 vòng                         | HC-C4    | ghi vi phạm, chưa KHÔNG ĐẠT     |
      | body 56.581 byte ở 2 vòng                         | HC-C4    | KHÔNG ĐẠT cuối cửa sổ           |
      | P95 vòng 2–10 = 140 ms, vòng 1 = 900 ms           | HC-C6    | đạt                             |
      | 20 dòng "PHP Warning" mới                         | HC-C8    | đạt                             |
      | 21 dòng "PHP Warning" mới                         | HC-C8    | KHÔNG ĐẠT ngay                  |
```

## Story: US-UPG-11 - Tự rollback khi health check không đạt
Tham chiếu: `FR-UPG-HC-005`, `FR-UPG-RBK-002` · `BR-HC-010`, `BR-SCN-010`, `BR-UPG-003`, `BR-CON-006` · `ERR-SCN-500-01`, `ERR-HC-500-01`, `ERR-HC-500-02`, `ERR-UPG-423-01` · `NFR-ENV-03`

```gherkin
Feature: US-UPG-11 Tự rollback khi health check không đạt

  @AC-UPG-33 @happy-path
  Scenario: Phản hồi 5xx kích hoạt tự rollback
    Given "shop.test" đang ở "HC_RUNNING" và vòng 3 nhận HTTP 502 tại thời điểm T
    When tool ra quyết định sau vi phạm "HC-C2"
    Then rollback bắt đầu ≤ T + 5 s bằng khoá site đang giữ và hoàn tất ≤ T + 60 s
    And switch_record có "status" = "ROLLED_BACK", "rollback_reason" = "HC-C2"; kết quả có "ERR-SCN-500-01" ("Site shop.test không đạt kiểm tra sau khi chuyển sang 8.5; đã hoàn tác về 8.2.")
    And 1 vòng thăm dò trên 8.2 cho mã HTTP mọi URL bằng mã baseline; mục P5 của site chuyển "FAILED"

  @AC-UPG-34 @negative
  Scenario: Tự rollback bị tắt có duyệt
    Given lượt chuyển chạy với "--no-auto-rollback" đã xác nhận kép bằng "confirm_retype" = "shop.test"
    When health check vi phạm "HC-C7"
    Then switch_record có "status" = "HC_FAILED_KEPT" và kết quả có "ERR-HC-500-01"
    And đầu màn hình SCR-002 hiển thị cảnh báo kèm nút rollback cho "shop.test" tới khi người vận hành xử lý

  @AC-UPG-35 @boundary
  Scenario: Rollback thất bại và health check bị gián đoạn
    Given tự rollback của "shop.test" gặp "nginx -t" lỗi sau khôi phục
    When tool hoàn tất bước quyết định
    Then switch_record có "status" = "ROLLBACK_FAILED", kết quả có "ERR-HC-500-02" và mọi lệnh chuyển site trên máy bị từ chối với "ERR-UPG-423-01"
    And với lượt khác ở "HC_RUNNING" mà tiến trình bị kill, lần chạy tool đầu tiên sau "t_C9 + 900 s" chạy lại health check đủ 10 vòng (600 s) bằng "baseline.json" đã lưu và không rollback khi chưa có vi phạm
```

## Story: US-UPG-12 - Rollback 1 site bằng 1 lệnh
Tham chiếu: `FR-UPG-RBK-001` · `BR-SCN-010`, `BR-UPG-003`, `BR-ENV-008`, `BR-SCN-014` · `ERR-ENV-410-01`, `ERR-ENV-500-03` · `NFR-ENV-02` · SCR-007

```gherkin
Feature: US-UPG-12 Rollback 1 site bằng 1 lệnh

  @AC-UPG-36 @happy-path
  Scenario: Rollback site đã PASSED
    Given "shop.test" có lượt "20261021-143000" trạng thái "PASSED" từ 8.2 sang 8.5
    When người vận hành chạy "php-quickpatch.sh migrate rollback shop.test --yes"
    Then tool chọn lượt mới nhất có dòng "switch<TAB>shop.test", phát lại manifest theo thứ tự ngược, chạy "nginx -t" rồi graceful reload
    And lớp gán trỏ lại 8.2, trang chủ trả mã bằng mã baseline, switch_record có "status" = "ROLLED_BACK" và audit có 1 bản ghi
    And bước R1–R6 hoàn tất ≤ 60 s; file pool đã tạo của 8.5 vẫn còn

  @AC-UPG-37 @negative
  Scenario: Runtime cũ đã bị gỡ
    Given PHP 8.2 đã bị gỡ khỏi máy chủ
    When người vận hành chạy "migrate rollback shop.test --yes"
    Then lệnh báo "ERR-ENV-410-01" ("Không thể hoàn tác shop.test: PHP 8.2 đã được gỡ khỏi máy chủ.") và không thay đổi cấu hình

  @AC-UPG-38 @boundary
  Scenario: --purge-pool và cấu hình khôi phục lỗi
    Given lượt "20261021-143000" có dòng "created" cho pool "qp-shop.test" của 8.5
    When người vận hành chạy "migrate rollback shop.test 20261021-143000 --purge-pool --yes"
    Then file pool "qp-shop.test" của 8.5 bị xoá
    And nếu cấu hình khôi phục không qua "nginx -t", kết quả có "ERR-ENV-500-03", Nginx không reload và cấu hình đang chạy giữ nguyên bản trước khôi phục
```

## Story: US-UPG-13 - Chuyển ứng dụng Node.js
Tham chiếu: `FR-UPG-NODE-001` · `BR-SCN-027`, `BR-SCN-022`, `BR-SCN-026`, `BR-ENV-003` · `ERR-SCN-424-02`

```gherkin
Feature: US-UPG-13 Chuyển ứng dụng Node.js

  @AC-UPG-39 @happy-path
  Scenario: Ứng dụng systemd chuyển từ Node.js 22 sang 24
    Given unit "api.service" có "ExecStart=/usr/bin/node /srv/api/server.js" (dòng 22) và "/opt/node-24/bin/node" đã cài song song
    When người vận hành chạy "migrate switch app:api --target 24 --plan <plan_id> --yes"
    Then drop-in trong "/etc/systemd/system/api.service.d/" đặt "ExecStart=" rỗng rồi "ExecStart=/opt/node-24/bin/node /srv/api/server.js", manifest có dòng "created" và "systemd api.service"
    And sau "systemctl daemon-reload" và restart, "readlink /proc/<MainPID>/exe" = "/opt/node-24/bin/node"
    And health check biến thể Node.js đạt: "NRestarts" tăng 0, RSS ≤ 1,5 × baseline; "/usr/bin/node" không đổi

  @AC-UPG-40 @negative
  Scenario: Native addon không nạp được
    Given addon của ứng dụng không nạp được bằng "/opt/node-24/bin/node" sau khi build lại trên bản sao
    When người vận hành chạy lượt chuyển "app:api"
    Then lượt chuyển dừng trước khi đổi unit với "ERR-SCN-424-02"

  @AC-UPG-41 @boundary
  Scenario: Ứng dụng pm2 của user không root và lỗi OpenSSL 3
    Given ứng dụng pm2 "web" thuộc user "deploy" (không root) chạy Node.js 16
    When user "deploy" chạy lượt chuyển "app:pm2:web" sang 24
    Then lượt được phép không cần root, manifest có dòng "copy" của file ecosystem và dòng "pm2"
    And khi log có dòng "ERR_OSSL_EVP_UNSUPPORTED" mới, tiêu chí "HC-C7" KHÔNG ĐẠT và ứng dụng được rollback bằng "pm2 delete", "pm2 start <ecosystem> --only web", "pm2 save"
```

## Story: US-UPG-14 - Chuyển dịch vụ Compose
Tham chiếu: `FR-UPG-DKR-001` · `BR-ENV-011`, `BR-UPG-001`, `BR-HC-010`, `BR-SCN-010` · `ERR-ENV-424-02`, `ERR-SCN-500-01` · `NFR-ENV-03`

```gherkin
Feature: US-UPG-14 Chuyển dịch vụ Compose

  @AC-UPG-42 @happy-path
  Scenario: Dịch vụ song song với image 8.5
    Given "compose.yaml" có dịch vụ "web" dùng "php:8.2-fpm" sau reverse proxy
    When người vận hành duyệt mục SEMI chuyển "svc:shop/web" sang "php:8.5-fpm"
    Then tool chạy "docker compose build" và "docker compose up -d --no-deps" cho dịch vụ mới chỉ sau khi duyệt
    And upstream reverse proxy trỏ sang dịch vụ mới, manifest có dòng "compose"
    And health check biến thể container đạt: "RestartCount" tăng 0, "Health.Status" = "healthy" khi image có HEALTHCHECK

  @AC-UPG-43 @negative
  Scenario: Build dịch vụ đích thất bại
    Given "docker compose build" của dịch vụ mới trả exit 1
    When tool chạy mục đã duyệt
    Then kết quả có "ERR-ENV-424-02" ("Không khởi động được dịch vụ web-85 với image php:8.5-fpm.")
    And dịch vụ "web" cũ vẫn nhận traffic

  @AC-UPG-44 @security
  Scenario: Không tự build/push và rollback dịch vụ
    Given mục chuyển dịch vụ chưa được duyệt
    When người vận hành chỉ chạy dry-run
    Then không lệnh "docker compose build", "docker compose up", "docker push" nào được chạy
    And trong mọi lượt, số lệnh "docker push" = 0; khi health check KHÔNG ĐẠT, tool chạy "docker compose -f compose.yaml up -d --no-deps web" để quay lại

  @AC-UPG-48 @boundary
  Scenario Outline: Thời hạn 10 s của HC-C0 với dịch vụ Compose đích
    Given lượt chuyển "svc:shop/web" sang 8.5 đã đổi upstream của Nginx trên host từ "web" sang "web-qp85", "nginx -t" exit 0 và reload xong tại thời điểm T (bắt đầu bước C10)
    And image của dịch vụ "web-qp85" <healthcheck>
    When tool xác minh "HC-C0" bằng phương pháp 5 của DOC-SRS-QP-ENV-002 §3.4 ("docker inspect" trạng thái container "web-qp85") và quan sát "<quan_sat>"
    Then "HC-C0" có kết quả "<hc_c0>" và switch_record có "status" = "<trang_thai>"
    And khi "HC-C0" KHÔNG ĐẠT: "rollback_reason" = "HC-C0", kết quả có "ERR-SCN-500-01" ("Site svc:shop/web không đạt kiểm tra sau khi chuyển sang 8.5; đã hoàn tác về 8.2."), tool khôi phục file cấu hình Nginx từ dòng "copy" của manifest, "nginx -t" exit 0 rồi reload; rollback bắt đầu ≤ T + 15 s và hoàn tất ≤ T + 70 s (vi phạm ghi nhận tại T + 10 s, "NFR-ENV-03")
    And khi "HC-C0" KHÔNG ĐẠT: upstream trỏ lại dịch vụ "web", container "web" không bị tạo lại và 1 vòng thăm dò cho mã HTTP trang chủ = mã baseline

    Examples:
      | healthcheck                  | quan_sat                                                                  | hc_c0     | trang_thai  |
      | có chỉ thị HEALTHCHECK       | ".State.Health.Status" = "healthy" lần đầu tại T + 10 s                   | ĐẠT       | HC_RUNNING  |
      | có chỉ thị HEALTHCHECK       | ".State.Health.Status" = "starting" tại T + 10 s, "healthy" tại T + 11 s  | KHÔNG ĐẠT | ROLLED_BACK |
      | không có chỉ thị HEALTHCHECK | ".State.Status" = "running" tại T + 1 s                                   | ĐẠT       | HC_RUNNING  |
      | không có chỉ thị HEALTHCHECK | ".State.Status" = "restarting" từ T tới T + 10 s                          | KHÔNG ĐẠT | ROLLED_BACK |
```

## Story: US-UPG-15 - Gỡ runtime cũ không còn dùng
Tham chiếu: `FR-UPG-RMV-001` · `BR-SCN-014`, `BR-ENV-008`, `BR-CON-006` · `ERR-UPG-412-01`, `ERR-JOB-428-01`

```gherkin
Feature: US-UPG-15 Gỡ runtime cũ không còn dùng

  @AC-UPG-45 @happy-path
  Scenario: Gỡ PHP 8.2 sau 14 ngày không dùng
    Given log FPM/access và "ps" cho thấy 0 tiến trình, 0 request dùng PHP 8.2 trong 14 ngày liên tục
    When người vận hành chạy "migrate remove-old --runtime-id <runtime_id_8.2>" với xác nhận kép "confirm_retype" = "<runtime_id_8.2>"
    Then màn hình xác nhận hiển thị cảnh báo mất khả năng rollback các lượt chuyển trước
    And danh sách gói/prefix của 8.2 được lưu vào manifest trước khi gỡ
    And các switch_record liên quan có "rollback_available" = false

  @AC-UPG-46 @negative
  Scenario: Runtime cũ còn được dùng
    Given access log có 1 request do pool PHP 8.2 xử lý cách đây 3 ngày
    When người vận hành chạy "migrate remove-old --runtime-id <runtime_id_8.2> --yes"
    Then lệnh báo "ERR-UPG-412-01" ("Không thể gỡ … : còn 1 site/tiến trình dùng trong 14 ngày qua.") và 0 gói bị gỡ

  @AC-UPG-47 @boundary
  Scenario Outline: Ngưỡng 14 ngày và xác nhận kép
    Given lần dùng cuối PHP 8.2 cách hiện tại <khoang>
    When người vận hành mở checklist P7
    Then kết quả là "<ket_qua>"

    Examples:
      | khoang          | ket_qua                                                      |
      | 13 ngày 23 giờ  | không đề xuất gỡ                                             |
      | 14 ngày         | đề xuất gỡ ở mức SEMI                                        |
      | 14 ngày         | xác nhận không gửi "confirm_retype" → ERR-JOB-428-01         |
```
