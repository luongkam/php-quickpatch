---
id: DOC-AC-QP-FEED
title: Tiêu chí chấp nhận — module FEED (dữ liệu CVE / vòng đời online) — php-quickpatch v2
version: 1.0.2
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, feed, cve, kev, osv, nvd, snapshot, cache]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-002
  - DOC-SRS-QP-FEED-003
  - DOC-SRS-QP-ERR-001
related_diagrams:
  - DIAG-FLOW-QP-FEED-001
  - DIAG-SEQ-QP-FEED-001
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module FEED

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 53 scenario cho `US-FEED-01..17` (`AC-FEED-01..53`); quy ước và ký hiệu dùng chung ở [acceptance-criteria.md §1](acceptance-criteria.md) |
| 1.0.1 | 2026-10-22 | BA Agent | `AC-FEED-43`: Given định lượng lỗi SRC-004, Then nêu `ERR-FEED-503-01`, mã thoát 2 của `build-snapshot`, không cập nhật `QP_SNAPSHOT_SHA256` và không đính kèm snapshot; `AC-FEED-41`: chuyển thành Scenario Outline, tách trường hợp `generated_at` = hiện tại + 61 phút thành dòng Examples riêng có `ERR-FEED-422-02`, mã thoát 2 và `current/` không đổi (DOC-SRS-QP-FEED-003 §4.3) |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review rule 08 (4 story chưa có `@boundary`): `AC-FEED-22` (`US-FEED-07`) gắn thêm `@boundary`, đổi mốc 13:59/14:01 thành 14:00:00/14:00:01 (tuổi cache đúng 6 giờ còn hạn, 6 giờ 1 giây hết hạn theo `age > TTL` của `BR-FEED-001`); thêm `AC-FEED-54` (`US-FEED-03`, bản mới nhất của nhánh lớn hơn/bằng/nhỏ hơn bản đã lưu, `BR-FEED-009`), `AC-FEED-55` (`US-FEED-13`, giải nén đúng giới hạn 50 MB và thêm 1 byte, `generated_at` = T + 60 phút và T + 60 phút 1 giây), `AC-FEED-56` (`US-FEED-17`, hạn mức 25 request WPScan trong 24 giờ); file có 56 scenario. Chỉ mục [acceptance-criteria.md](acceptance-criteria.md) §1.3, §2, §3 và cột AC của [backlog.md](backlog.md) cần cập nhật theo |

Ký hiệu "máy kiểm thử chuẩn", "bundle mẫu 2026-10-22": [acceptance-criteria.md §1.2](acceptance-criteria.md). Nguồn `SRC-001..017`: DOC-SRS-QP-FEED-001 §3. Trong test, mọi nguồn online được thay bằng máy chủ HTTPS giả lập trả phản hồi đã ghi ngày 2026-10-22.

## Story: US-FEED-01 - Đồng bộ thủ công bằng feeds update
Tham chiếu: `FR-FEED-CMD-001`, `FR-FEED-SYNC-001` · `BR-FEED-001`, `BR-FEED-006`, `BR-FEED-008`, `BR-FEED-015` · `ERR-FEED-503-01`, `ERR-FEED-423-01`, `ERR-FEED-504-01`, `ERR-FEED-507-01` · `NFR-FEED-001`, `NFR-FEED-008`

```gherkin
Feature: US-FEED-01 Đồng bộ thủ công bằng feeds update

  @AC-FEED-01 @happy-path
  Scenario: Đồng bộ tăng dần khi bundle 5 ngày tuổi
    Given máy kiểm thử chuẩn có bundle tạo 5 ngày trước, mọi nguồn trả HTTP 200 hoặc 304
    When người vận hành chạy "php-quickpatch.sh feeds update --json"
    Then chỉ nguồn có "now − fetched_at" > TTL được gọi, theo thứ tự SRC-006, 002, 009, 012, 011, 004, 001, 010, 003, 008
    And lệnh hoàn tất trong ≤ 180 s, gửi ≤ 45 request và in tóm tắt có "bundle_id" mới
    And mã thoát là 0

  @AC-FEED-02 @negative
  Scenario: Một nguồn lỗi sau 3 lần thử, đồng bộ vẫn hoàn tất
    Given "api.github.com" trả HTTP 502 cho mọi request của SRC-008
    When người vận hành chạy "php-quickpatch.sh feeds update --json"
    Then SRC-008 có trạng thái "FAILED" với "last_error" = "ERR-FEED-503-01" sau đúng 3 lần thử
    And dữ liệu alias GHSA dùng nguồn chéo SRC-003 và ghi "data_origin" tương ứng
    And các nguồn khác được cập nhật, bundle mới được tạo và mã thoát là 1

  @AC-FEED-03 @negative
  Scenario: Lượt đồng bộ khác đang giữ khoá
    Given một tiến trình "feeds update" (PID 4242) đang giữ "feeds/.lock"
    When người vận hành chạy "php-quickpatch.sh feeds update" và khoá vẫn bị giữ sau 30 s
    Then lệnh báo "ERR-FEED-423-01" với thông báo "Đang có lượt đồng bộ dữ liệu khác chạy (PID 4242)." và mã thoát 2
    And "scan" chạy cùng lúc vẫn đọc "feeds/current/" mà không chờ khoá

  @AC-FEED-04 @boundary
  Scenario: Vượt ngân sách thời gian và thiếu dung lượng
    Given NVD trả chậm 30 s mỗi request và ngân sách mặc định 180 s
    When người vận hành chạy "php-quickpatch.sh feeds update --json"
    Then khi hết 180 s, các nguồn chưa xong giữ dữ liệu cũ, kết quả có "ERR-FEED-504-01" liệt kê các nguồn đó và mã thoát là 1
    And khi phân vùng chứa "feeds/" còn 99 MB trống, lệnh không gọi nguồn nào và báo "ERR-FEED-507-01"
    And "--budget 59" hoặc "--budget 3601" bị từ chối với mã thoát 2
```

## Story: US-FEED-02 - Đồng bộ vòng đời và ma trận framework
Tham chiếu: `FR-FEED-EOL-001`, `FR-FEED-EOL-002`, `FR-FEED-EOL-003` · `BR-FEED-009`, `BR-FEED-020`, `BR-FEED-021` · `ERR-FEED-502-02`, `ERR-FEED-409-01`, `ERR-FEED-422-01`

```gherkin
Feature: US-FEED-02 Đồng bộ vòng đời và ma trận framework

  @AC-FEED-05 @happy-path
  Scenario: Đủ bản ghi vòng đời và ma trận framework
    Given phản hồi ghi ngày 2026-10-22 của SRC-001, SRC-003, SRC-010
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-001,SRC-003,SRC-010 --force"
    Then bảng "lifecycle_branch" có PHP 4.4, 5.0–8.5 và Node.js 0.8, 0.10, 0.12, 1–27
    And PHP 4.4 có "origin" = "STATIC", GA "2005-07-11", EOL "2008-08-07" khi SRC-001 và SRC-003 không trả nhánh 4.4
    And chuỗi "supportedPhpVersions"/"supportedPHPVersions" dạng "8.3 - 8.5" được lưu thành [8.3, 8.5] không phân biệt hoa thường

  @AC-FEED-06 @negative
  Scenario: Số bản ghi vòng đời giảm bất thường
    Given lần đồng bộ trước SRC-001 "php" có 18 nhánh
    And phản hồi mới hợp lệ cú pháp chỉ có 9 nhánh (giảm 50%)
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-001"
    Then phản hồi bị từ chối với "ERR-FEED-502-02" và dữ liệu cũ của SRC-001 được giữ
    And phản hồi lỗi được lưu vào "feeds/raw/SRC-001/rejected/" (tối đa 3 file gần nhất)
    And chỉ lệnh "feeds update --force --accept-shrink" mới chấp nhận phản hồi đó và ghi 1 bản ghi audit

  @AC-FEED-07 @boundary
  Scenario Outline: Lệch ngày EOL giữa 2 nguồn
    Given SRC-010 ghi "eol" dòng Node.js 26 = "2029-04-30" và SRC-001 ghi "<ngay_src001>"
    When tool chuẩn hoá vòng đời
    Then "eol_date" của dòng 26 = "2029-04-30" (nguồn ưu tiên 1) và cảnh báo xung đột <canh_bao>

    Examples:
      | ngay_src001 | canh_bao                    |
      | 2029-05-03  | không có "ERR-FEED-409-01"   |
      | 2029-05-04  | có "ERR-FEED-409-01"         |
```

## Story: US-FEED-03 - Đồng bộ bản phát hành
Tham chiếu: `FR-FEED-REL-001`, `FR-FEED-REL-002`, `FR-FEED-REL-003` · `BR-DATA-002`, `BR-FEED-006`, `BR-FEED-007`, `BR-FEED-009`, `BR-FEED-016`, `BR-FEED-024` · `ERR-FEED-503-01`, `ERR-FEED-502-02` · `NFR-FEED-004`

```gherkin
Feature: US-FEED-03 Đồng bộ bản phát hành

  @AC-FEED-08 @happy-path
  Scenario: Mốc bản mới nhất lấy từ nguồn chính thức
    Given SRC-002 trả 8.5.12 ngày 2026-10-21 nhãn "security" và SRC-001 trả "latest" = "8.5.11"
    And SRC-009 trả v26.12.1 "security: true" và SRC-012 trả trạng thái từng bản WordPress core
    When người vận hành chạy "php-quickpatch.sh feeds update --force --json"
    Then bản mới nhất nhánh PHP 8.5 = "8.5.12" với "is_security" = 1, không dùng "8.5.11" của SRC-001
    And mỗi nhánh lưu tối đa 100 bản phát hành và Node.js lưu trường "modules"
    And sự kiện "security_release_detected" được ghi cho 8.5.12 và 26.12.1

  @AC-FEED-09 @negative
  Scenario: php.net không truy cập được
    Given "www.php.net" lỗi DNS trong 3 lần thử
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-002"
    Then SRC-002 báo "ERR-FEED-503-01" với thông báo nêu nguồn đang dùng và tuổi dữ liệu
    And bản mới nhất mỗi nhánh lấy theo thứ tự dự phòng: tag php-src, rồi SRC-001, có "data_origin" tương ứng

  @AC-FEED-10 @security
  Scenario: Từ chối URL không phải HTTPS và chứng chỉ không hợp lệ
    Given file cấu hình khai báo URL nguồn "http://mirror.test/php.json"
    And một nguồn HTTPS chuyển hướng 301 sang "http://"
    And một nguồn HTTPS dùng chứng chỉ tự ký
    When người vận hành chạy "php-quickpatch.sh feeds update"
    Then cả 3 nguồn bị từ chối, không có byte phản hồi nào được ghi vào "feeds/raw/"
    And mỗi nguồn ghi "ERR-FEED-503-01" và kết nối dùng TLS ≥ 1.2 có xác thực chứng chỉ

  @AC-FEED-54 @boundary
  Scenario Outline: Bản mới nhất của nhánh so với bản đã lưu
    Given bundle hiện tại lưu bản mới nhất nhánh PHP 8.5 = "8.5.12" lấy từ SRC-002
    And phản hồi mới của SRC-002 hợp lệ cú pháp và có bản mới nhất nhánh 8.5 = "<phan_hoi>"
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-002 --force"
    Then <ket_qua>

    Examples:
      | phan_hoi | ket_qua                                                                                                                         |
      | 8.5.13   | phản hồi được chấp nhận, bản mới nhất nhánh 8.5 = "8.5.13"                                                                        |
      | 8.5.12   | phản hồi được chấp nhận (bằng bản đã lưu), bản mới nhất nhánh 8.5 giữ "8.5.12"                                                    |
      | 8.5.11   | phản hồi bị từ chối với "ERR-FEED-502-02", dữ liệu cũ của SRC-002 được giữ và phản hồi được lưu vào "feeds/raw/SRC-002/rejected/" |
```

## Story: US-FEED-04 - Đồng bộ CVE PHP core
Tham chiếu: `FR-FEED-PCVE-001`, `FR-FEED-PCVE-002`, `FR-FEED-PCVE-003` · `BR-FEED-002`, `BR-FEED-004`, `BR-FEED-014`, `BR-FEED-023` · `ERR-FEED-429-01`, `ERR-FEED-504-01`

```gherkin
Feature: US-FEED-04 Đồng bộ CVE PHP core

  @AC-FEED-11 @happy-path
  Scenario: Đồng bộ tăng dần NVD bằng 2 truy vấn
    Given "last_lastmod" của NVD = "2026-10-21T21:00:00Z" và không có API key
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-004"
    Then truy vấn CPE "cpe:2.3:a:php:php" và truy vấn "sourceIdentifier=security@php.net" dùng "lastModStartDate" = "2026-10-21T20:00:00Z"
    And khoảng cách giữa 2 request NVD liên tiếp ≥ 6 s
    And kết quả 2 truy vấn được gộp theo "cve.id"; "CVE-2026-109618" có CVSS v3.1 9,8 và dải ảnh hưởng "< 8.2.35", "< 8.3.36", "< 8.4.27", "< 8.5.12"
    And cặp kiểm thử "GHSA-test-0002" ↔ "CVE-2026-109618" trong "NEWS" được lưu vào "advisory_alias"

  @AC-FEED-12 @negative
  Scenario: NVD giới hạn tốc độ
    Given NVD trả HTTP 403 cho request không có key
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-004"
    Then SRC-004 báo "ERR-FEED-429-01" và dữ liệu NVD cũ được giữ nguyên
    And khi nguồn trả "Retry-After: 301", tool không gọi lại nguồn đó trong lượt đồng bộ hiện tại

  @AC-FEED-13 @boundary
  Scenario: Cửa sổ NVD dài hơn 120 ngày và CVE chưa có trên NVD
    Given "last_lastmod" cách hiện tại 150 ngày
    And "CVE-2026-999001" (dữ liệu kiểm thử) có trong SRC-008 nhưng NVD trả 0 kết quả
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-004,SRC-005,SRC-008"
    Then NVD được gọi bằng 2 cửa sổ liên tiếp, mỗi cửa sổ ≤ 120 ngày
    And CVE.org được tra cho "CVE-2026-999001"; phản hồi 404 "CVE_RECORD_DNE" cho "status" = "RESERVED"
    And CVE ở trạng thái "RESERVED" được tra lại ở mỗi lần đồng bộ, tối đa 30 ngày
```

## Story: US-FEED-05 - Đồng bộ CVE Node.js và WordPress core
Tham chiếu: `FR-FEED-NCVE-001`, `FR-FEED-WCVE-001` · `BR-FEED-022`, `BR-FEED-024`, `BR-FEED-025` · `ERR-FEED-422-01`, `ERR-FEED-429-01`

```gherkin
Feature: US-FEED-05 Đồng bộ CVE Node.js và WordPress core

  @AC-FEED-14 @happy-path
  Scenario: Dải semver của Node.js Security WG
    Given SRC-011 có 194 bản ghi ngày 2026-10-22
    When tool chuẩn hoá và đánh giá Node.js 22.12.0
    Then 40 bản ghi ảnh hưởng 22.12.0 (13 high, 17 medium, 10 low)
    And Node.js 22.23.3, 24.22.1, 26.12.1 có 0 bản ghi khớp từ SRC-011
    And CVE WordPress core được lấy từ NVD với CPE "cpe:2.3:a:wordpress:wordpress"

  @AC-FEED-15 @negative
  Scenario: Bản ghi có biểu thức semver không đọc được
    Given 1 bản ghi SRC-011 có "vulnerable" = "^22.x.?" và 193 bản ghi hợp lệ
    When tool chuẩn hoá SRC-011
    Then bản ghi lỗi bị bỏ qua với "ERR-FEED-422-01" ("Bỏ qua 1 bản ghi không đọc được từ SRC-011.")
    And 193 bản ghi còn lại được chuẩn hoá và bundle mới được tạo

  @AC-FEED-16 @boundary
  Scenario: Advisory tạm của bản bảo mật và bản ghi chỉ cho Windows
    Given SRC-009 gắn "security: true" cho 22.23.4 lúc "2026-10-20T12:00:00Z" và chưa có advisory thật nào có "fixed_in_branch" = "22.23.4"
    And 1 bản ghi SRC-011 có "affectedEnvironments" = ["win32"]
    When tool chuẩn hoá lúc "2026-10-20T17:59:00Z" và lúc "2026-10-20T18:00:00Z"
    Then lúc 17:59 chưa có advisory tạm; lúc 18:00 có "QP-SR-node-22.23.4" với "cvss_rep" = 7,5 và dải "< 22.23.4" trong nhánh 22
    And bản ghi "win32" không ảnh hưởng runtime trên Linux
    And advisory tạm bị xoá khi có advisory thật với "fixed_in_branch" = "22.23.4"
```

## Story: US-FEED-06 - Gắn cờ CISA KEV
Tham chiếu: `FR-FEED-KEV-001` · `BR-SEC-001`, `BR-FEED-009` · `ERR-FEED-502-02`

```gherkin
Feature: US-FEED-06 Gắn cờ CISA KEV

  @AC-FEED-17 @happy-path
  Scenario: Gắn cờ KEV từ catalog 2026.10.21
    Given SRC-006 trả "catalogVersion" = "2026.10.21" với 1.754 bản ghi
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-006 --force"
    Then advisory "CVE-2026-63030" và "CVE-2026-60137" có "in_kev" = 1 kèm "dueDate"
    And advisory "CVE-2026-109618" có "in_kev" = 0
    And request gửi header "If-Modified-Since" bằng thời điểm lấy thành công lần trước

  @AC-FEED-18 @negative
  Scenario: KEV giảm hơn 5 bản ghi
    Given lần trước KEV có 1.754 bản ghi và phản hồi mới có 1.748 bản ghi
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-006"
    Then phản hồi bị từ chối với "ERR-FEED-502-02" và cờ "in_kev" giữ theo dữ liệu cũ

  @AC-FEED-19 @boundary
  Scenario Outline: Ngưỡng giảm KEV và phản hồi 304
    Given lần trước KEV có 1.754 bản ghi
    When nguồn trả "<phan_hoi>"
    Then kết quả là "<ket_qua>"

    Examples:
      | phan_hoi               | ket_qua                                    |
      | HTTP 200, 1.749 bản ghi | chấp nhận (giảm đúng 5 bản ghi)             |
      | HTTP 304               | chỉ cập nhật "fetched_at", không tải lại thân |
```

## Story: US-FEED-07 - Tra OSV Composer/npm có cache
Tham chiếu: `FR-FEED-OSV-001` · `BR-FEED-001`, `BR-FEED-013` · `ERR-FEED-503-02`

```gherkin
Feature: US-FEED-07 Tra OSV Composer/npm có cache

  @AC-FEED-20 @happy-path
  Scenario: Lockfile 1.200 package được tra theo lô
    Given "package-lock.json" có 1.200 cặp tên/phiên bản và chưa có cache cho SHA-256 của file
    When người vận hành chạy "php-quickpatch.sh scan --only npm --json"
    Then tool gửi 3 request "querybatch" với 500, 500 và 200 package
    And advisory "MAL-*" có trong kết quả và trang tiếp theo theo "next_page_token" được tải hết
    And kết quả được cache theo SHA-256 của lockfile

  @AC-FEED-21 @negative
  Scenario: OSV lỗi và cache đã quá 7 ngày
    Given "api.osv.dev" không truy cập được và cache của lockfile có tuổi 8 ngày
    When người vận hành chạy "php-quickpatch.sh scan --only npm --json"
    Then lockfile bị bỏ qua với "ERR-FEED-503-02"
    And các lockfile khác có cache ≤ 7 ngày vẫn được đánh giá bằng cache

  @AC-FEED-22 @security @boundary
  Scenario: Dữ liệu gửi ra ngoài và biên TTL cache 6 giờ
    Given lockfile đã được tra OSV lúc "2026-10-22T08:00:00Z", nội dung không đổi và cache theo SHA-256 của lockfile còn nguyên
    When người vận hành chạy lại "php-quickpatch.sh scan --only npm --json" với đồng hồ giả lập cố định lúc "2026-10-22T14:00:00Z" và lúc "2026-10-22T14:00:01Z"
    Then lúc 14:00:00 (tuổi cache đúng 6 giờ, chưa thoả "age > TTL") không có request OSV nào; lúc 14:00:01 (tuổi 6 giờ 1 giây) có request OSV mới
    And thân request OSV chỉ chứa ecosystem, tên package, phiên bản; không chứa đường dẫn dự án, hostname hay tên site
    And với "--offline", tool không gửi request nào ra Internet
```

## Story: US-FEED-08 - Xác định bản vá backport của gói distro
Tham chiếu: `FR-FEED-DIST-001`, `FR-FEED-DIST-002`, `FR-FEED-NORM-003` · `BR-FEED-026`, `BR-SEC-002`, `BR-SCN-015` · `ERR-FEED-503-01`

```gherkin
Feature: US-FEED-08 Xác định bản vá backport của gói distro

  @AC-FEED-23 @happy-path
  Scenario: Gói Ubuntu 8.3.6-0ubuntu0.24.04.13 được gắn ok-backport
    Given bundle mẫu 2026-10-22 và "/usr/bin/php8.3" thuộc gói nguồn "php8.3" phiên bản "8.3.6-0ubuntu0.24.04.13" trên Ubuntu 24.04
    When người vận hành chạy "php-quickpatch.sh scan --only php --json"
    Then "CVE-2026-17545" có kết quả "UNFIXED", 45 CVE có kết quả "FIXED" (gồm "CVE-2026-109618"), "CVE-2024-2408" và "CVE-2024-5585" có kết quả "NOT_AFFECTED"
    And runtime có "state" = "ok-backport" và "risk.score" = 33, mức "MEDIUM"

  @AC-FEED-24 @negative
  Scenario: Nguồn distro lỗi, chỉ còn changelog gói
    Given OSV distro (SRC-014) và tracker Ubuntu (SRC-015) trả lỗi sau 3 lần thử
    And changelog gói không nhắc tới "CVE-2026-17545"
    When tool xác định trạng thái vá
    Then mỗi nguồn lỗi ghi "ERR-FEED-503-01"
    And "CVE-2026-17545" có kết quả "UNKNOWN", runtime có "state" = "vulnerable" kèm nhãn "chưa xác định"

  @AC-FEED-25 @boundary
  Scenario: Phiên bản upstream đã ≥ min_patched_sec
    Given runtime PHP 8.3.36 thuộc gói distro và "min_patched_sec" của nhánh 8.3 = "8.3.36"
    When tool xác định trạng thái vá
    Then runtime có "state" = "ok" ở bước 0
    And không có request nào tới SRC-014, SRC-015 cho runtime này
```

## Story: US-FEED-09 - Chuẩn hoá advisory và tính min_patched
Tham chiếu: `FR-FEED-NORM-001`, `FR-FEED-NORM-002` · `BR-FEED-023`, `BR-FEED-027`, `BR-FEED-028`, `BR-FEED-030`, `BR-FEED-031` · `ERR-FEED-409-01`, `ERR-FEED-422-01` · `NFR-MNT-002`, `NFR-FEED-003`

```gherkin
Feature: US-FEED-09 Chuẩn hoá advisory và tính min_patched

  @AC-FEED-26 @happy-path
  Scenario: Hồi quy với dữ liệu ghi cứng của v0.1
    Given raw cache cố định ngày 2026-10-22 của mọi nguồn
    When tool chuẩn hoá và tính "min_patched"
    Then PHP: 8.2 → "8.2.35", 8.3 → "8.3.36", 8.4 → "8.4.27", 8.5 → "8.5.12"
    And Node.js: 22 → "22.23.4", 24 → "24.22.1", 26 → "26.12.1"
    And WordPress: 6.9 → "6.9.10", 7.0 → "7.0.7", 7.1 → "7.1.3"
    And chuẩn hoá 2.000 CVE + 2.000 bản ghi KEV dùng ≤ 200 MB RSS và ≤ 30 s CPU

  @AC-FEED-27 @negative
  Scenario: Hai nguồn mâu thuẫn phiên bản sửa
    Given "CVE-2025-1861" có NVD "versionEndExcluding" = "8.2.26" và CNA "lessThan" = "8.2.28" cho nhánh 8.2
    When tool tính "fixed_in_branch"
    Then "fixed_in_branch" = "8.2.28" (giá trị lớn nhất)
    And log ghi cả 2 giá trị và cảnh báo "ERR-FEED-409-01"
    And PHP 8.2.26 vẫn được đánh giá là bị "CVE-2025-1861" ảnh hưởng

  @AC-FEED-28 @boundary
  Scenario: Khử trùng lặp, mã độc và advisory bị thu hồi
    Given advisory GHSA "GHSA-test-0003" có alias "CVE-2026-999002" và bản ghi NVD "CVE-2026-999002"
    And advisory "MAL-2026-0002" có alias trùng 1 CVE
    And 1 CVE PHP có trạng thái "Rejected" trên NVD
    When tool chuẩn hoá
    Then chỉ có 1 advisory "adv_id" = "CVE-2026-999002", "GHSA-test-0003" nằm trong "advisory_alias"
    And "MAL-2026-0002" là advisory riêng, không gộp với CVE
    And CVE "Rejected" bị loại khỏi mọi phép tính nhưng bản ghi được giữ 90 ngày
```

## Story: US-FEED-10 - Gắn tuổi dữ liệu vào mọi kết quả
Tham chiếu: `FR-FEED-AGE-001` · `BR-FEED-005`, `BR-DATA-001` · `ERR-FEED-412-01`, `ERR-SCN-503-01` · `NFR-FEED-006`

```gherkin
Feature: US-FEED-10 Gắn tuổi dữ liệu vào mọi kết quả

  @AC-FEED-29 @happy-path
  Scenario: Dữ liệu 12 giờ tuổi ở mức AGING
    Given nguồn cũ nhất được dùng là SRC-004 với tuổi 12 giờ, TTL 6 giờ
    When người vận hành chạy "php-quickpatch.sh scan --json" và "php-quickpatch.sh scan"
    Then envelope có "data.data_age_h" = 12, "data.freshness" = "AGING", "data.stale_sources[]" chứa "SRC-004"
    And đầu ra văn bản có dòng "Dữ liệu cũ 12 giờ (nguồn: SRC-004)" trong mục "Environment"

  @AC-FEED-30 @negative
  Scenario: Dữ liệu STALE gắn cảnh báo ở mọi đầu ra
    Given nguồn cũ nhất được dùng có tuổi 200 giờ
    When người vận hành chạy "scan --json", mở SCR-002 và xuất "report assess --format md"
    Then cả 3 đầu ra chứa cảnh báo "ERR-FEED-412-01" với thông báo "Dữ liệu dùng để đánh giá đã cũ 8 ngày (nguồn: …)."

  @AC-FEED-31 @boundary
  Scenario Outline: Ngưỡng mức độ tươi
    Given nguồn cũ nhất được dùng có TTL 6 giờ và tuổi <tuoi> giờ
    And nguồn tuỳ chọn SRC-013 đang tắt và có dữ liệu cũ 900 giờ
    When tool tính độ tươi
    Then "data.freshness" = "<muc>" và SRC-013 không được tính vào "data_age_h"

    Examples:
      | tuoi | muc     |
      | 6    | FRESH   |
      | 7    | AGING   |
      | 168  | AGING   |
      | 169  | STALE   |
      | 2161 | EXPIRED |
```

## Story: US-FEED-11 - Cache gốc và thay bundle nguyên tử
Tham chiếu: `FR-FEED-CACH-001`, `FR-FEED-CACH-002`, `FR-FEED-CACH-003` · `BR-FEED-007`, `BR-FEED-011`, `BR-FEED-051`, `BR-FEED-052` · `ERR-FEED-422-02`, `ERR-FEED-507-01` · `NFR-FEED-004`, `NFR-FEED-005`

```gherkin
Feature: US-FEED-11 Cache gốc và thay bundle nguyên tử

  @AC-FEED-32 @happy-path
  Scenario: Lưu raw và thay bundle
    Given SRC-006 trả thân 1.803.428 byte kèm "ETag"
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-006 --force"
    Then file raw được ghi tạm rồi "rename", nén gzip vì lớn hơn 1 MB và ".meta.json" có "sha256", "ETag"
    And "current/" cũ thành "previous/", "staging/" thành "current/" với "bundle_id" mới và chỉ tồn tại đúng 1 "previous/"

  @AC-FEED-33 @negative
  Scenario: Bundle staging lỗi toàn vẹn
    Given chuẩn hoá ghi xong "staging/" nhưng 1 file TSV có SHA-256 khác "SHA256SUMS"
    When bước thay bundle chạy
    Then bundle mới bị từ chối với "ERR-FEED-422-02", "staging/" bị xoá và "current/" giữ "bundle_id" cũ
    And khi dung lượng trống < 100 MB trước khi đồng bộ, lệnh dừng với "ERR-FEED-507-01" và không ghi raw

  @AC-FEED-34 @boundary
  Scenario: Giới hạn dung lượng và bảo vệ key
    Given "feeds update" chạy mỗi 6 giờ trong 30 ngày với API key NVD giả "QPTESTKEY0001"
    When người vận hành đo "du -sb feeds/" và tìm chuỗi "QPTESTKEY0001" trong "feeds/", log, "--json", audit
    Then "feeds/" ≤ 60 MB và mỗi nguồn giữ tối đa 3 file trong "rejected/"
    And chuỗi "QPTESTKEY0001" xuất hiện 0 lần
```

## Story: US-FEED-12 - Khởi tạo dữ liệu từ snapshot đóng gói
Tham chiếu: `FR-FEED-SNAP-001` · `BR-FEED-010`, `BR-FEED-053`, `BR-FEED-054` · `ERR-FEED-422-02`, `ERR-FEED-503-01`

```gherkin
Feature: US-FEED-12 Khởi tạo dữ liệu từ snapshot đóng gói

  @AC-FEED-35 @happy-path
  Scenario: Lần chạy đầu không có mạng
    Given máy chủ mới cài tool, không có "feeds/current/", không có mạng
    And SHA-256 của "feeds-snapshot.tar.gz" khớp "QP_SNAPSHOT_SHA256"
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then snapshot được giải nén thành "current/" trong ≤ 10 s
    And mọi runtime có kết quả đánh giá với "data_origin" = "SNAPSHOT" và tuổi dữ liệu tính từ "generated_at" của snapshot

  @AC-FEED-36 @negative
  Scenario: Snapshot đóng gói sai SHA-256 và không có mạng
    Given không có "feeds/current/", không có mạng và SHA-256 của snapshot khác "QP_SNAPSHOT_SHA256"
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then snapshot bị từ chối với "ERR-FEED-422-02"
    And mọi runtime có trạng thái "UNKNOWN", "errors[]" chứa "ERR-FEED-503-01" và mã thoát là 2

  @AC-FEED-37 @boundary
  Scenario: Snapshot đóng gói mới hơn bundle hiện có
    Given "current/" có "generated_at" = "2026-10-10T06:00:00Z" và snapshot đóng gói của bản tool mới có "generated_at" = "2026-10-20T06:00:00Z"
    When tool khởi động lần đầu sau khi nâng cấp
    Then bundle được dựng lại từ snapshot rồi đồng bộ tăng dần từ "2026-10-19T06:00:00Z"
    And khi 2 giá trị "generated_at" bằng nhau, "current/" được giữ nguyên
```

## Story: US-FEED-13 - Xuất/nhập snapshot offline
Tham chiếu: `FR-FEED-SNAP-002`, `FR-FEED-SNAP-003`, `FR-FEED-CMD-004`, `FR-FEED-CMD-005` · `BR-FEED-010`, `BR-FEED-055`, `BR-FEED-056` · `ERR-FEED-422-02`, `ERR-FEED-409-02`

```gherkin
Feature: US-FEED-13 Xuất/nhập snapshot offline

  @AC-FEED-38 @happy-path
  Scenario: Xuất snapshot standard ở máy có mạng
    Given máy A có bundle tuổi 2 giờ, có cache OSV, "distro_fix" và API key NVD
    When người vận hành chạy "php-quickpatch.sh feeds export --out /root/qp-snap.tar.gz --variant standard"
    Then file chứa "manifest.json", "SHA256SUMS", "bundle/" và lệnh in SHA-256 của file
    And gói không chứa "cache/", "distro_fix" của máy A, API key hay đường dẫn site
    And kích thước file ≤ 3 MB

  @AC-FEED-39 @happy-path
  Scenario: Nhập snapshot ở máy không ra Internet
    Given máy B không có mạng, bundle hiện có "generated_at" cũ hơn snapshot
    When người vận hành chạy "php-quickpatch.sh feeds import /root/qp-snap.tar.gz --sha256 <64 ký tự hex đã in ở máy A>"
    Then "current/" được thay bằng bundle của snapshot và mã thoát là 0
    And audit ghi người chạy, SHA-256 và "generated_at" của snapshot

  @AC-FEED-40 @negative
  Scenario: Nhập snapshot sai SHA-256 hoặc cũ hơn
    Given máy B có bundle "generated_at" = "2026-10-21T06:00:00Z"
    When người vận hành nhập snapshot với "--sha256" khác giá trị thật
    Then lệnh từ chối với "ERR-FEED-422-02", mã thoát 2 và "current/" không đổi
    And khi nhập snapshot đúng SHA-256 nhưng "generated_at" = "2026-10-20T06:00:00Z", lệnh từ chối với "ERR-FEED-409-02" trừ khi có "--force"

  @AC-FEED-41 @security
  Scenario Outline: Gói snapshot độc hại hoặc có generated_at tương lai bị từ chối
    Given máy B có bundle mẫu 2026-10-22 trong "current/"
    And gói "/root/qp-bad.tar.gz" có SHA-256 khớp "--sha256", mọi kiểm tra khác của DOC-SRS-QP-FEED-003 §4.3 đạt, trừ: <bat_thuong>
    When người vận hành chạy "php-quickpatch.sh feeds import /root/qp-bad.tar.gz" với "--sha256" bằng SHA-256 thật của gói
    Then lệnh từ chối với "ERR-FEED-422-02" và mã thoát 2
    And 0 file được ghi ngoài thư mục tạm của tool và "current/" giữ "bundle_id" = "b-20261022T093000Z-3f2a9c1e"

    Examples:
      | bat_thuong                                                                             |
      | có mục mang đường dẫn tuyệt đối "/etc/cron.d/x"                                        |
      | có mục mang đường dẫn "../x"                                                           |
      | có 1 symlink                                                                           |
      | có 1 hardlink                                                                          |
      | có 1 file thiết bị                                                                     |
      | tổng dung lượng giải nén 51 MB (giới hạn 50 MB)                                        |
      | "manifest.json" có "generated_at" = thời điểm chạy lệnh + 61 phút (giới hạn + 60 phút) |

  @AC-FEED-55 @boundary
  Scenario Outline: Biên dung lượng giải nén và generated_at khi nhập snapshot
    Given máy B có bundle mẫu 2026-10-22 trong "current/" và đồng hồ giả lập cố định T = "2026-10-22T12:00:00Z"
    And gói "/root/qp-edge.tar.gz" có mọi kiểm tra khác của DOC-SRS-QP-FEED-003 §4.3 đạt, tổng dung lượng giải nén <giai_nen> và "manifest.json" có "generated_at" = "<generated_at>"
    When người vận hành chạy "php-quickpatch.sh feeds import /root/qp-edge.tar.gz" với "--sha256" bằng SHA-256 thật của gói
    Then <ket_qua>

    # L = giới hạn "tổng dung lượng giải nén ≤ 50 MB" của DOC-SRS-QP-FEED-003 §4.3 tính bằng byte; SRS chưa quy đổi 1 MB = 10^6 hay 2^20 byte, Dev chốt hằng số trước khi viết test
    Examples:
      | giai_nen   | generated_at         | ket_qua                                                                                                        |
      | đúng L     | 2026-10-22T11:00:00Z | "current/" được thay bằng bundle của snapshot và mã thoát là 0                                                 |
      | L + 1 byte | 2026-10-22T11:00:00Z | lệnh từ chối với "ERR-FEED-422-02", mã thoát 2 và "current/" giữ "bundle_id" = "b-20261022T093000Z-3f2a9c1e" |
      | 10 MB      | 2026-10-22T13:00:00Z | T + 60 phút, bằng giới hạn: "current/" được thay bằng bundle của snapshot và mã thoát là 0                     |
      | 10 MB      | 2026-10-22T13:00:01Z | T + 60 phút 1 giây: lệnh từ chối với "ERR-FEED-422-02", mã thoát 2 và "current/" không đổi                     |
```

## Story: US-FEED-14 - Dựng snapshot khi phát hành
Tham chiếu: `FR-FEED-SNAP-004` · `BR-FEED-058` · `ERR-FEED-503-01`

```gherkin
Feature: US-FEED-14 Dựng snapshot khi phát hành

  @AC-FEED-42 @happy-path
  Scenario: Pipeline dựng snapshot đạt cổng phát hành
    Given pipeline phát hành có mạng và API key NVD của pipeline
    When pipeline chạy "qp-feeds.py build-snapshot --variant standard"
    Then mọi nguồn P0 SRC-001, 002, 004, 006, 009, 010, 011, 012 ở trạng thái "OK"
    And độ phủ có PHP 4.4 + 5.0–8.5 và Node.js 4–26; test hồi quy "min_patched" (AC-FEED-26) đạt
    And "QP_SNAPSHOT_SHA256" trong "php-quickpatch.sh" và ghi chú phát hành bằng SHA-256 của gói

  @AC-FEED-43 @negative
  Scenario: Nguồn P0 lỗi chặn phát hành
    Given NVD (SRC-004) trả HTTP 503 cho mọi request sau 3 lần thử trong lượt build và các nguồn P0 khác ở "OK"
    When pipeline chạy "qp-feeds.py build-snapshot --variant standard" và kiểm cổng phát hành
    Then SRC-004 có trạng thái "FAILED" với "last_error" = "ERR-FEED-503-01" và lệnh in SRC-004 là nguồn chặn cổng "BR-FEED-058"
    And "qp-feeds.py build-snapshot" kết thúc với mã thoát 2 (quy ước 0/1/2 của DOC-SRS-QP-FEED-003 §6.3; SRS chưa nêu riêng mã thoát của "build-snapshot")
    And "QP_SNAPSHOT_SHA256" trong "php-quickpatch.sh" giữ giá trị cũ và gói phát hành không chứa "share/php-quickpatch/feeds-snapshot.tar.gz" mới

  @AC-FEED-44 @boundary
  Scenario Outline: Tuổi snapshot tại ngày phát hành
    Given snapshot có "generated_at" cách thời điểm phát hành <tuoi>
    When pipeline kiểm cổng phát hành
    Then kết quả là "<ket_qua>"

    Examples:
      | tuoi             | ket_qua                                                |
      | 7 ngày           | cho phát hành                                          |
      | 7 ngày 1 giây    | chặn, trừ khi có văn bản PO duyệt ngoại lệ bản vá khẩn  |
```

## Story: US-FEED-15 - Lịch đồng bộ định kỳ
Tham chiếu: `FR-FEED-SCHD-001`, `FR-FEED-CMD-006` · `BR-FEED-057` · `ERR-CLI-400-01` · `NFR-FEED-006`

```gherkin
Feature: US-FEED-15 Lịch đồng bộ định kỳ

  @AC-FEED-45 @happy-path
  Scenario: Cài lịch systemd mặc định 6 giờ
    Given máy kiểm thử chuẩn có systemd và chưa có lịch
    When người vận hành chạy "php-quickpatch.sh feeds schedule install"
    Then tồn tại "/etc/systemd/system/php-quickpatch-feeds.service" có "ExecStart" chứa "feeds update --quiet"
    And "php-quickpatch-feeds.timer" có "OnCalendar=*-*-* 00/6:MM:00" với MM cố định trong 0–59, "RandomizedDelaySec=900", "Persistent=true"
    And "feeds schedule show" in loại lịch, chu kỳ 6 giờ và thời điểm chạy kế tiếp

  @AC-FEED-46 @negative
  Scenario: Chu kỳ không thuộc tập cho phép
    Given máy kiểm thử chuẩn
    When người vận hành chạy "php-quickpatch.sh feeds schedule install --interval-hours 5"
    Then lệnh báo "ERR-CLI-400-01", mã thoát 2 và không tạo unit hay dòng cron nào

  @AC-FEED-47 @boundary
  Scenario: Cài lặp, không systemd và chu kỳ dưới 6 giờ
    Given máy chủ không có systemd và đã có dòng cron mang dấu "# php-quickpatch-feeds"
    When người vận hành chạy "feeds schedule install --interval-hours 4" 2 lần
    Then "/etc/cron.d/php-quickpatch-feeds" có đúng 1 dòng mang dấu "# php-quickpatch-feeds", được cập nhật tại chỗ
    And lệnh in cảnh báo hạn mức NVD khi không có API key vì chu kỳ 4 < 6 giờ
    And "feeds schedule remove" xoá dòng đó và "feeds schedule show" báo không có lịch
```

## Story: US-FEED-16 - Trạng thái nguồn và kiểm toàn vẹn bundle
Tham chiếu: `FR-FEED-CMD-002`, `FR-FEED-CMD-003` · `BR-FEED-005`, `BR-FEED-010`, `BR-FEED-059` · `ERR-FEED-422-02` · SCR-008

```gherkin
Feature: US-FEED-16 Trạng thái nguồn và kiểm toàn vẹn bundle

  @AC-FEED-48 @happy-path
  Scenario: Xem trạng thái nguồn dạng JSON
    Given bundle "b-20261022T093000Z-3f2a9c1e" có SRC-004 "DEGRADED" tuổi 12 giờ và SRC-013 "DISABLED"
    When kiểm toán viên chạy "php-quickpatch.sh feeds status --json"
    Then đầu ra có "schema" = "qp.feeds.status/1", "bundle_id", "freshness" = "AGING", "data_age_h" = 12
    And mỗi phần tử "sources[]" có "src_id", "name", "status", "last_ok_at", "age_h", "ttl_h", "records", "last_error", "data_origin"
    And có khối "schedule" và "snapshot.sha256_ok"; mã thoát là 0

  @AC-FEED-49 @negative
  Scenario: Bundle bị sửa ngoài tool
    Given 1 byte của "feeds/current/advisory.tsv" bị sửa sau khi dựng bundle
    When kiểm toán viên chạy "php-quickpatch.sh feeds verify"
    Then lệnh báo "ERR-FEED-422-02" nêu file lệch
    And bundle được dựng lại từ "raw/" và lần "feeds verify" kế tiếp báo khớp

  @AC-FEED-50 @boundary
  Scenario Outline: Mã thoát của feeds status theo độ tươi
    Given độ tươi tổng của bundle là "<muc>"
    When kiểm toán viên chạy "php-quickpatch.sh feeds status"
    Then mã thoát là <ma>

    Examples:
      | muc             | ma |
      | FRESH           | 0  |
      | AGING           | 0  |
      | STALE           | 1  |
      | EXPIRED         | 2  |
      | không có bundle | 2  |
```

## Story: US-FEED-17 - Nguồn lỗ hổng WordPress cần key
Tham chiếu: `FR-FEED-WCVE-002` · `BR-FEED-011`, `BR-FEED-004`, `BR-SEC-001`, `BR-SEC-006` · `ERR-FEED-401-01`

```gherkin
Feature: US-FEED-17 Nguồn lỗ hổng WordPress cần key

  @AC-FEED-51 @happy-path
  Scenario: Bật nguồn khi có token WPScan
    Given file cấu hình quyền 0600 khai báo "QP_WPSCAN_TOKEN"
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-013"
    Then SRC-013 có trạng thái "OK" và advisory plugin/theme WordPress được thêm vào bundle
    And số request tới WPScan trong 24 giờ ≤ 25

  @AC-FEED-52 @negative
  Scenario: Khoá truy cập bị từ chối
    Given token đã khai báo bị nguồn trả HTTP 401
    When người vận hành chạy "php-quickpatch.sh feeds update"
    Then SRC-013 báo "ERR-FEED-401-01" ("Khóa truy cập SRC-013 bị từ chối.") và tự tắt tới lần sửa cấu hình kế tiếp
    And các nguồn khác vẫn đồng bộ bình thường

  @AC-FEED-53 @security
  Scenario: File cấu hình quyền rộng và che key
    Given file cấu hình chứa token có quyền 0644
    When người vận hành chạy "php-quickpatch.sh feeds update --json"
    Then token bị bỏ qua, SRC-013 giữ "DISABLED" và có cảnh báo về quyền file
    And chuỗi token xuất hiện 0 lần trong log, "--json", audit, snapshot và ".meta.json"

  @AC-FEED-56 @boundary
  Scenario Outline: Hạn mức 25 request WPScan trong 24 giờ
    Given file cấu hình quyền 0600 chỉ khai báo "QP_WPSCAN_TOKEN" hợp lệ (không có key Wordfence, Patchstack)
    And trong 24 giờ trước lượt chạy, tool đã gửi <da_gui> request tới WPScan
    And server có 2 site WordPress (dữ liệu kiểm thử) dùng 2 phiên bản core chưa có cache WPScan: "wp-a.test" có CVE core với "in_kev" = 1, "wp-b.test" không có CVE nào trong KEV
    When người vận hành chạy "php-quickpatch.sh feeds update --source SRC-013"
    Then tool gửi thêm <gui_them> request WPScan và tổng số request WPScan trong 24 giờ là <tong>
    And phiên bản core được tra WPScan trong lượt này: <duoc_tra>

    Examples:
      | da_gui | gui_them | tong | duoc_tra                                        |
      | 23     | 2        | 25   | của "wp-a.test" và "wp-b.test"                  |
      | 24     | 1        | 25   | chỉ của "wp-a.test" (site có KEV được ưu tiên)  |
      | 25     | 0        | 25   | không có                                        |
```
