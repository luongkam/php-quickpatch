---
id: DOC-AC-QP-PLAN
title: Tiêu chí chấp nhận — module PLAN và CMPT (kế hoạch nâng cấp, quét tương thích) — php-quickpatch v2
version: 1.0.1
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, plan, checklist, compatibility, phpcompatibility, composer, npm]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-SCN-PHP-001
  - DOC-SRS-QP-SCN-NODE-001
related_diagrams:
  - DIAG-STATE-QP-PLAN-001
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module PLAN và CMPT

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 59 scenario: `US-PLAN-01..08` (`AC-PLAN-01..26`), `US-CMPT-01..11` (`AC-CMPT-01..33`); quy ước ở [acceptance-criteria.md §1](acceptance-criteria.md) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: 3 story `US-CMPT-01`, `US-CMPT-05`, `US-CMPT-11` chỉ có `@security` ở scenario thứ 3, chưa đạt rule 08 (≥ 1 `@boundary`). Thêm 3 scenario `@boundary`, đánh số tiếp theo `AC-CMPT-33` theo [acceptance-criteria.md §1.3](acceptance-criteria.md) hướng (b): `AC-CMPT-34` (chọn Composer 2.2.30/2.10.3 theo `$OLD` 5.3.1/5.3.2/7.2.4/7.2.5 và mốc 2026-12-31 của `BR-SCN-044`), `AC-CMPT-35` (TTL cache Packagist 24 giờ: 23 giờ 59 phút/24 giờ 01 phút; phiên bản tối thiểu ≥ bản đang dùng theo `FR-CMPT-COMP-002`), `AC-CMPT-36` (diff Rector 0 file/1 file, chưa duyệt/đã duyệt theo `BR-SCN-011`, `CHK-PHP-007-20`). Thêm `BR-SCN-044` vào tham chiếu `US-CMPT-01`, `BR-SCN-011` đã có ở `US-CMPT-11`. Tổng file: 62 scenario (`AC-PLAN-01..26`, `AC-CMPT-01..36`); chỉ mục §2, §3 của acceptance-criteria.md và TC/RTM cần cập nhật ở file tương ứng |

Ký hiệu dùng chung: [acceptance-criteria.md §1.2](acceptance-criteria.md). Ví dụ chung: runtime PHP 8.2.34 (`runtime_id` = `php:3f2a9c1e0b7d`, dữ liệu kiểm thử) phục vụ 3 site, nhánh đích 8.5 (bản patch 8.5.12).

## 1. Module PLAN

## Story: US-PLAN-01 - Chọn phiên bản đích
Tham chiếu: `FR-PLAN-TGT-001` · `BR-UPG-004`, `BR-SCN-005`, `BR-SCN-006`, `BR-SCN-007`, `BR-PLAN-001`, `BR-ASMT-002` · `ERR-SCN-409-02`, `ERR-PLAN-422-01` · SCR-004

```gherkin
Feature: US-PLAN-01 Chọn phiên bản đích

  @AC-PLAN-01 @happy-path
  Scenario: Chọn đích đề xuất
    Given bundle mẫu 2026-10-22 và ứng viên "8.5.12" mang loại ["RECOMMENDED", "LATEST_STABLE"], "selectable" = true
    When người vận hành chạy "php-quickpatch.sh plan create --runtime-id php:3f2a9c1e0b7d --target 8.5 --json"
    Then "target" = {"branch": "8.5", "patch_version": "8.5.12", "types": ["RECOMMENDED", "LATEST_STABLE"], "override_reason": null}
    And phạm vi site mặc định gồm cả 3 site đang dùng runtime

  @AC-PLAN-02 @negative
  Scenario Outline: Đích bị cấm cho site production
    Given ngày chạy 2026-10-22 và site trong phạm vi là site production
    When người vận hành chạy "plan create --runtime-id php:3f2a9c1e0b7d --target <dich>"
    Then kế hoạch không được tạo và lỗi là "<loi>"

    Examples:
      | dich | loi                                                                                       |
      | 8.1  | ERR-SCN-409-02 "Không thể chuyển site production sang 8.1: nhánh đang ở trạng thái EOL." |
      | 8.6  | ERR-SCN-409-02 với trạng thái PRE_RELEASE                                                 |
      | 6.0  | ERR-SCN-409-02 với trạng thái UNKNOWN                                                     |

  @AC-PLAN-03 @negative
  Scenario: Đích khác đề xuất cần lý do tối thiểu 20 ký tự
    Given ứng viên "8.4.27" mang loại ["NEXT_SUPPORTED"] (không có "RECOMMENDED")
    When người vận hành tạo kế hoạch đích "8.4" với "--reason" dài 19 ký tự
    Then lệnh báo "ERR-PLAN-422-01" ("Vui lòng nhập lý do tối thiểu 20 ký tự.") và không tạo kế hoạch
    And với lý do dài 20 ký tự, kế hoạch được tạo, "override_reason" hiển thị trên kế hoạch và audit ghi lý do

  @AC-PLAN-04 @boundary
  Scenario Outline: Node.js CURRENT trước ngày LTS
    Given dòng Node.js 26 có ngày "lts" = "2026-10-28" và ứng dụng thuộc site production
    When người vận hành tạo kế hoạch đích "26" vào ngày "<ngay>"
    Then kết quả là "<ket_qua>"

    Examples:
      | ngay       | ket_qua                                         |
      | 2026-10-27 | từ chối với ERR-SCN-409-02 (trạng thái CURRENT) |
      | 2026-10-28 | tạo kế hoạch trạng thái draft                   |
```

## Story: US-PLAN-02 - Sinh kế hoạch nâng cấp
Tham chiếu: `FR-PLAN-GEN-001` · `BR-PLAN-002`, `BR-PLAN-006`, `BR-UPG-006`, `BR-SCN-016` · `ERR-PLAN-409-01` · `NFR-PERF-005`, `NFR-REL-006`

```gherkin
Feature: US-PLAN-02 Sinh kế hoạch nâng cấp

  @AC-PLAN-05 @happy-path
  Scenario: Kế hoạch khác nhánh có mục vá cùng nhánh đứng trước
    Given runtime PHP 8.2.34 ở trạng thái "vulnerable", "min_patched" nhánh 8.2 = "8.2.35"
    When người vận hành chạy "plan create --runtime-id php:3f2a9c1e0b7d --target 8.5 --json"
    Then "plan_id" khớp "^PLN-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$", trạng thái "draft", chế độ "cross_branch"
    And mục P2 "vá cùng nhánh 8.2.34 → 8.2.35" đứng trước mục P2 "cài song song 8.5"
    And kế hoạch lưu "bundle_id", "catalog_version", "scan_fingerprint" và hạn duyệt "2026-12-01"
    And "STATE_DIR/plans/<plan_id>/" chứa "plan.json", "items.json", "events.jsonl"
    And thời gian sinh kế hoạch cho site 10.000 file ".php", 300 package ≤ 120 s (mục tiêu, chưa đo)

  @AC-PLAN-06 @negative
  Scenario: Runtime đã có kế hoạch đang thực hiện
    Given runtime có kế hoạch "PLN-20261020-091500-4c2e" ở trạng thái "in_progress"
    When người vận hành tạo kế hoạch mới cho cùng runtime
    Then lệnh báo "ERR-PLAN-409-01" ("Runtime php:3f2a9c1e0b7d đã có kế hoạch đang thực hiện PLN-20261020-091500-4c2e.")
    And kế hoạch "in_progress" không thay đổi

  @AC-PLAN-07 @boundary
  Scenario: Thay kế hoạch draft cũ, không có bản vá cùng nhánh và ghi nguyên tử
    Given runtime có kế hoạch cũ ở trạng thái "draft"
    And runtime PHP 7.4.33 có "min_patched" = "NONE"
    When người vận hành tạo kế hoạch mới và tiến trình bị "kill -9" ngẫu nhiên trong 100 lần ghi kế hoạch
    Then kế hoạch "draft" cũ chuyển "cancelled" và có 1 bản ghi audit
    And kế hoạch của PHP 7.4.33 không có mục "vá cùng nhánh"
    And 0 file "plan.json" bị hỏng sau 100 lần kill (file luôn là bản cũ hoặc bản mới và parse được bằng JSON)
```

## Story: US-PLAN-03 - Thứ tự chuyển site và site canary
Tham chiếu: `FR-PLAN-GEN-002` · `BR-PLAN-004`, `BR-ENV-003`, `BR-UPG-002` · `ERR-UPG-409-01` · SCR-004

```gherkin
Feature: US-PLAN-03 Thứ tự chuyển site và site canary

  @AC-PLAN-08 @happy-path
  Scenario: Sắp site PASS theo số file PHP tăng dần
    Given 3 site có kết luận "PASS": "c.test" 3.500 file, "a.test" 120 file, "b.test" 800 file ".php"
    When tool sinh kế hoạch
    Then "site_order[]" = ["a.test", "b.test", "c.test"] và "canary_site_id" = "a.test"

  @AC-PLAN-09 @negative
  Scenario: Site FAIL bị chặn
    Given site "d.test" có kết luận "FAIL" với 2 hit mức error chưa miễn trừ
    When tool sinh kế hoạch rồi người vận hành chạy mục P5 của "d.test"
    Then "blocked_sites[]" chứa "d.test" và các mục P5 của site ở "PENDING" kèm lý do chặn
    And lệnh chạy mục P5 bị từ chối với "ERR-UPG-409-01" ("Site d.test còn 2 lỗi tương thích chưa xử lý.")

  @AC-PLAN-10 @boundary
  Scenario: Cùng số file và đổi canary trước/sau khi duyệt
    Given "x.test" và "w.test" cùng có 500 file ".php" và kết luận "PASS"
    When tool sinh kế hoạch
    Then "w.test" đứng trước "x.test" (so "site_id" tăng dần)
    And đổi canary sang "x.test" khi kế hoạch "draft" được chấp nhận và ghi audit
    And đổi canary khi kế hoạch "approved" đưa kế hoạch về "draft"
```

## Story: US-PLAN-04 - Danh sách dependency phải nâng
Tham chiếu: `FR-PLAN-DEP-001` · `BR-SCN-025`, `BR-SCN-043`, `BR-SCN-044`, `BR-SCN-045`, `BR-DATA-003` · `ERR-SCN-409-03`

```gherkin
Feature: US-PLAN-04 Danh sách dependency phải nâng

  @AC-PLAN-11 @happy-path
  Scenario: Gộp kết quả quét thành danh sách phải nâng
    Given kết quả quét có 1 extension thiếu gói trên 8.5 nhưng có PECL, 1 package Composer "vendor-test/b" 1.0.0 yêu cầu php ">=7.1 <8.1" với bản tối thiểu thoả "1.4.0"
    When tool sinh kế hoạch
    Then "upgrade_items[]" có 2 dòng, mỗi dòng có "component_type", "name", "current", "required", "min_compatible", "evidence", "chk_id"
    And dòng Composer có "min_compatible" = "1.4.0" và "chk_id" trỏ tới 1 mục P4

  @AC-PLAN-12 @negative
  Scenario: Loader mã hoá không có bản cho nhánh đích
    Given site dùng ionCube và ma trận loader của catalog (dữ liệu kiểm thử) không có loader cho mọi nhánh đích hợp lệ
    When tool sinh kế hoạch
    Then "errors[]" chứa "ERR-SCN-409-03" ("Không có ionCube cho PHP 8.5; không thể chuyển site …")
    And site được đưa vào "blocked_sites[]"

  @AC-PLAN-13 @boundary
  Scenario: Không tra được metadata khi offline
    Given lập kế hoạch với "--offline"
    When tool tính phiên bản tối thiểu tương thích của package Composer/npm
    Then "min_compatible" = "unknown" và 0 request tới "repo.packagist.org", "registry.npmjs.org"
    And gói npm vi phạm "engines.node" chỉ thuộc "devDependencies" được ghi là cảnh báo, không tạo mục P4 bắt buộc
```

## Story: US-PLAN-05 - Cập nhật trạng thái mục checklist
Tham chiếu: `FR-PLAN-CHK-001` · `BR-SCN-018`, `BR-PLAN-005` · `ERR-PLAN-422-01`, `ERR-PLAN-409-02`, `ERR-SCN-424-01`

```gherkin
Feature: US-PLAN-05 Cập nhật trạng thái mục checklist

  @AC-PLAN-14 @happy-path
  Scenario: Đánh dấu DONE cho mục MANUAL kèm bằng chứng
    Given kế hoạch "approved" có mục MANUAL "CHK-PHP-010-04" ở "PENDING"
    When người vận hành chạy "plan item <plan_id> CHK-PHP-010-04 --set done --reason 'Đã test 5 luồng thanh toán'"
    Then mục chuyển "DONE", "events.jsonl" có 1 dòng mới và audit có 1 bản ghi
    And console nhận sự kiện SSE "plan_item" cho mục này

  @AC-PLAN-15 @negative
  Scenario: Cập nhật mục của kế hoạch đã huỷ
    Given kế hoạch ở trạng thái "cancelled"
    When người vận hành đặt mục bất kỳ thành "done"
    Then lệnh báo "ERR-PLAN-409-02" ("Không thể done khi kế hoạch ở trạng thái cancelled.")

  @AC-PLAN-16 @boundary
  Scenario Outline: Độ dài lý do, bằng chứng và phụ thuộc
    Given mục "<loai>" ở trạng thái "PENDING"
    When người vận hành thực hiện "<hanh_dong>"
    Then kết quả là "<ket_qua>"

    Examples:
      | loai                         | hanh_dong                         | ket_qua                    |
      | MANUAL                       | done với bằng chứng 9 ký tự        | ERR-PLAN-422-01            |
      | MANUAL                       | done với bằng chứng 10 ký tự       | DONE                       |
      | AUTO                         | waive với lý do 19 ký tự           | ERR-PLAN-422-01            |
      | AUTO                         | waive với lý do 20 ký tự           | WAIVED                     |
      | P5 có mục P3 chưa DONE/WAIVED | start                             | ERR-SCN-424-01             |
```

## Story: US-PLAN-06 - Chạy mục checklist AUTO/SEMI
Tham chiếu: `FR-PLAN-CHK-002` · `BR-SCN-008`, `BR-CON-005`, `BR-ENV-010` · `ERR-JOB-428-01`, `ERR-UPG-409-02`

```gherkin
Feature: US-PLAN-06 Chạy mục checklist AUTO/SEMI

  @AC-PLAN-17 @happy-path
  Scenario: Chạy mục cài song song qua dry-run và xác nhận
    Given phiên console hợp lệ, kế hoạch "approved", mục P2 "cài song song 8.5" có "cli_action" = "migrate_install"
    When người vận hành bấm chạy mục, xem kết quả dry-run rồi xác nhận sau 3 phút
    Then 1 job "write" được tạo với "confirm_dry_run_job_id" của job dry-run
    And job "SUCCEEDED" làm mục chuyển "DONE"; job "FAILED" làm mục chuyển "FAILED" kèm "job_id"

  @AC-PLAN-18 @negative
  Scenario: Chạy mục khi chưa có dry-run hợp lệ hoặc kế hoạch chưa duyệt
    Given mục SEMI chuyển site "a.test" thuộc kế hoạch "draft"
    When client gửi "POST /api/v1/plans/<plan_id>/checklist-items/<chk_id>/runs" với "dry_run" = false và không có "confirm_dry_run_job_id"
    Then API trả HTTP 428 với "ERR-JOB-428-01"
    And khi gửi kèm dry-run hợp lệ, API trả HTTP 409 với "ERR-UPG-409-02" vì kế hoạch chưa "approved"

  @AC-PLAN-19 @boundary
  Scenario Outline: Thời hạn dry-run và lệnh chưa kiểm chứng
    Given mục "<muc>" và dry-run "SUCCEEDED" tạo cách đây <tuoi>
    When người vận hành xác nhận chạy
    Then kết quả là "<ket_qua>"

    Examples:
      | muc                                    | tuoi          | ket_qua                                         |
      | AUTO verified=true                     | 14 phút 59 s  | job ghi được tạo                                |
      | AUTO verified=true                     | 15 phút 01 s  | ERR-JOB-428-01                                  |
      | lệnh playbook verified=false           | 1 phút        | chỉ chạy ở mức SEMI, hiển thị nhãn "chưa kiểm chứng" |
```

## Story: US-PLAN-07 - Vòng đời và duyệt kế hoạch
Tham chiếu: `FR-PLAN-STS-001` · `BR-PLAN-003`, `BR-PLAN-006`, `BR-PLAN-007` · `ERR-PLAN-412-01`, `ERR-PLAN-410-01`, `ERR-PLAN-409-02` · SCR-004

```gherkin
Feature: US-PLAN-07 Vòng đời và duyệt kế hoạch

  @AC-PLAN-20 @happy-path
  Scenario: Duyệt, bắt đầu và hoàn tất kế hoạch
    Given kế hoạch "draft" không "stale", 100% site có kết quả phần quét chạy được trước khi cài, mọi mục P1 AUTO ở "DONE", tiền điều kiện đã kiểm
    When người vận hành chạy "plan approve <plan_id>"
    Then kế hoạch chuyển "approved" và audit ghi người duyệt
    And khi mục thay đổi hệ thống đầu tiên chạy, kế hoạch chuyển "in_progress"
    And khi mọi mục ở "DONE", "SKIPPED" hoặc "WAIVED", kế hoạch chuyển "completed"

  @AC-PLAN-21 @negative
  Scenario: Duyệt khi thiếu kết quả quét của 1 site
    Given kế hoạch "draft" có site "c.test" chưa có kết quả quét tương thích
    When người vận hành chạy "plan approve <plan_id>"
    Then lệnh báo "ERR-PLAN-412-01" với "{missing}" nêu "c.test"
    And kế hoạch giữ "draft"

  @AC-PLAN-22 @negative
  Scenario: Kế hoạch lỗi thời chặn mục P5
    Given kế hoạch "approved" có 4 mục "DONE"
    And sau khi duyệt, vhost của "b.test" bị đổi làm "scan_fingerprint" thay đổi
    When người vận hành mở kế hoạch và chạy mục P5 của "a.test"
    Then kế hoạch có "stale" = true, "stale_reasons[]" chứa lý do đổi "scan_fingerprint"
    And lệnh chạy mục P5 bị từ chối với "ERR-PLAN-410-01"
    And khi sinh lại kế hoạch, 4 mục "DONE" giữ nguyên trạng thái

  @AC-PLAN-23 @boundary
  Scenario Outline: Điều kiện lỗi thời và huỷ
    Given kế hoạch "approved" với đích 8.5
    When xảy ra "<su_kien>"
    Then kết quả là "<ket_qua>"

    Examples:
      | su_kien                                          | ket_qua                         |
      | R của đích tăng 19 điểm                           | stale = false                   |
      | R của đích tăng 20 điểm                           | stale = true                    |
      | đích có advisory KEV mới                          | stale = true                    |
      | lệnh "plan cancel" khi có job của kế hoạch RUNNING | ERR-PLAN-409-02                 |
      | có site ROLLED_BACK và người vận hành đóng kế hoạch | trạng thái rolled_back          |
```

## Story: US-PLAN-08 - Theo dõi hạn duyệt kế hoạch
Tham chiếu: `FR-PLAN-DL-001` · `BR-SCN-049`, `BR-SCN-029` · `ERR-PLAN-412-01` · SCR-002

```gherkin
Feature: US-PLAN-08 Theo dõi hạn duyệt kế hoạch

  @AC-PLAN-24 @happy-path
  Scenario: Hạn duyệt PHP 8.2 và Node.js 22 ngày 2026-10-22
    Given bundle mẫu 2026-10-22, runtime PHP 8.2.35 và Node.js 22.23.4 chưa có kế hoạch
    When kiểm toán viên chạy "php-quickpatch.sh scan --json"
    Then "result.plan_deadlines[]" có PHP 8.2 với "deadline" = "2026-12-01", "days_left" = 40
    And có Node.js 22 với "deadline" = "2027-03-31", "days_left" = 160
    And SCR-002 hiển thị cùng 2 hạn duyệt

  @AC-PLAN-25 @negative
  Scenario: Quá hạn duyệt và kế hoạch chưa đủ điều kiện
    Given ngày chạy 2026-12-02 và kế hoạch của PHP 8.2 vẫn ở "draft" do thiếu kết quả quét 1 site
    When người vận hành mở SCR-002 rồi bấm duyệt kế hoạch
    Then SCR-002 có mục cảnh báo mức "high" cho hạn duyệt đã quá 1 ngày
    And duyệt bị từ chối với "ERR-PLAN-412-01" và cảnh báo quá hạn vẫn hiển thị

  @AC-PLAN-26 @boundary
  Scenario Outline: Mốc bắt đầu cảnh báo EOL − 90 ngày
    Given PHP 8.3 có "eol" = "2027-12-31"
    When tool chạy vào ngày "<ngay>"
    Then cảnh báo hạn duyệt trên SCR-002 <hien_thi>

    Examples:
      | ngay       | hien_thi       |
      | 2027-10-01 | không hiển thị |
      | 2027-10-02 | hiển thị       |
```

## 2. Module CMPT

## Story: US-CMPT-01 - Công cụ quét cố định phiên bản
Tham chiếu: `FR-CMPT-TOOL-001` · `BR-CMPT-006`, `BR-SEC-005`, `BR-SCN-044` · `ERR-CMPT-424-01`, `ERR-PTCH-502-01` · `NFR-CAP-002`

```gherkin
Feature: US-CMPT-01 Công cụ quét cố định phiên bản

  @AC-CMPT-01 @happy-path
  Scenario: Cài công cụ quét lần đầu
    Given máy kiểm thử chuẩn có mạng và chưa có "STATE_DIR/tools/php"
    When người vận hành tạo kế hoạch đầu tiên
    Then "STATE_DIR/tools/php" chứa PHPCompatibility 10.0.0-alpha2, PHPCompatibilityWP 3.0.0-alpha2, PHP_CodeSniffer 4.0.4, Composer 2.10.3 và 2.2 LTS, Rector 2.7.0
    And "tools_manifest.json" ghi tên, phiên bản, SHA-256 của từng công cụ
    And dung lượng "tools/php" ≤ 80 MB (mục tiêu, chưa đo)

  @AC-CMPT-02 @negative
  Scenario: composer.phar tải về sai SHA-256 và máy offline
    Given "composer.phar" tải về có SHA-256 khác giá trị công bố
    When tool cài công cụ
    Then file bị xoá và lỗi "ERR-PTCH-502-01" ("Checksum mismatch for composer.phar; download discarded.")
    And khi máy offline và chưa có công cụ, kết quả có "ERR-CMPT-424-01" và chỉ bước quét luật breaking change tĩnh được chạy

  @AC-CMPT-03 @security
  Scenario: Công cụ chỉ đến từ catalog và không nằm trong docroot
    Given catalog ghi hash của "composer.lock" công cụ và 1 package trong lockfile có hash khác
    When tool cài công cụ
    Then việc cài bị huỷ, 0 file của package lệch hash được giữ lại
    And không file công cụ nào nằm dưới docroot của bất kỳ site nào
    And phiên bản công cụ chỉ đổi khi "catalog_version" mới ghi phiên bản khác

  @AC-CMPT-34 @boundary
  Scenario Outline: Chọn bản Composer theo PHP của runtime cũ và mốc hết vá của 2.2 LTS
    Given công cụ đã cài theo catalog (Composer 2.10.3 và 2.2.30 LTS), dự án có "composer.json" và "composer.lock"
    And "$OLD_BIN" là PHP <php_old>
    When tool kiểm kê Composer của dự án trên "$OLD_BIN" vào ngày <ngay>
    Then kết quả là "<ket_qua>"

    Examples:
      | php_old | ngay       | ket_qua                                                                 |
      | 5.3.1   | 2026-10-22 | không chạy Composer trên "$OLD_BIN", kiểm kê chỉ đọc "composer.lock"     |
      | 5.3.2   | 2026-10-22 | chạy Composer 2.2.30 (LTS)                                               |
      | 7.2.4   | 2026-10-22 | chạy Composer 2.2.30 (LTS)                                               |
      | 7.2.5   | 2026-10-22 | không dùng Composer 2.2.30 (ngoài dải 5.3.2 – < 7.2.5)                  |
      | 7.2.4   | 2026-12-31 | chạy Composer 2.2.30 (LTS)                                               |
      | 7.2.4   | 2027-01-01 | không cài gói bằng Composer 2.2.30, kiểm kê chỉ đọc "composer.lock"      |
```

## Story: US-CMPT-02 - Quét luật breaking change tĩnh
Tham chiếu: `FR-CMPT-CODE-001` · `BR-SCN-041`, `BR-CMPT-001`, `BR-CMPT-005` · `ERR-CMPT-504-01`, `ERR-CMPT-413-01`

```gherkin
Feature: US-CMPT-02 Quét luật breaking change tĩnh

  @AC-CMPT-04 @happy-path
  Scenario: Quét dải (7.4, 8.5] trước khi cài 8.5
    Given site "legacy.test" chạy PHP 7.4.33, chưa cài PHP 8.5, file "lib/a.php" dòng 12 gọi hàm "each("
    When tool quét luật breaking change với "$OLD" = 7.4 và "$NEW" = 8.5
    Then "compat.hits[]" có phần tử "file" = "lib/a.php", "line" = 12, "rule_id" khớp "^BC-PHP-", "level" = "error"
    And "snippet" dài ≤ 200 ký tự

  @AC-CMPT-05 @negative
  Scenario: Quét vượt 1.800 s
    Given site có 400.000 file ".php" và quét chưa xong sau 1.800 s
    When tool quét luật breaking change
    Then quét dừng, phần này có kết luận "PENDING" và kết quả chứa "ERR-CMPT-504-01"

  @AC-CMPT-06 @boundary
  Scenario: Tập file quét và biên dải phiên bản
    Given docroot có file ".php" 2.097.153 byte, thư mục "vendor/", "node_modules/", ".git/" và "tests/" được khai báo "không triển khai" với lý do 24 ký tự
    And catalog có luật phiên bản 7.4 và luật phiên bản 8.5
    When tool quét dải (7.4, 8.5]
    Then file 2.097.153 byte bị bỏ qua và liệt kê kèm "ERR-CMPT-413-01"
    And không có hit nào trong "vendor/", "node_modules/", ".git/", "tests/"
    And luật phiên bản 7.4 không được áp dụng, luật phiên bản 8.5 được áp dụng
```

## Story: US-CMPT-03 - Quét PHPCompatibility
Tham chiếu: `FR-CMPT-CODE-002` · `BR-SCN-042`, `BR-CMPT-001`, `BR-CMPT-002` · `ERR-CMPT-422-01`, `ERR-CMPT-424-01`, `ERR-CMPT-504-01`

```gherkin
Feature: US-CMPT-03 Quét PHPCompatibility

  @AC-CMPT-07 @happy-path
  Scenario: Quét site WordPress với testVersion 8.5
    Given site WordPress, công cụ đã cài, PHP 8.5 đã cài song song, máy 2 vCPU
    When tool chạy quét PHPCompatibility
    Then lệnh dùng "--standard=PHPCompatibilityWP --runtime-set testVersion 8.5 --extensions=php,inc,phtml --report=json" và binary "$NEW_BIN"
    And chạy 2 tiến trình song song
    And hit mức "ERROR"/"WARNING" được gộp vào "compat.hits[]" với "rule_id" = mã sniff

  @AC-CMPT-08 @negative
  Scenario: Không có PHP ≥ 7.2 để chạy PHP_CodeSniffer
    Given máy chỉ có PHP 5.6 và chưa cài nhánh đích
    When tool chạy quét PHPCompatibility
    Then phần PHPCompatibility có kết luận "PENDING" và kết quả chứa "ERR-CMPT-422-01"

  @AC-CMPT-09 @boundary
  Scenario: Chọn binary và bậc thang testVersion khi OLD < 7.0
    Given site chạy PHP 5.6, chưa cài 8.5, máy có PHP 7.4 và PHP 8.3
    When tool chạy quét PHPCompatibility
    Then binary chạy PHPCS là PHP 8.3 (bản cao nhất ≥ 7.2)
    And quét thêm "testVersion" 5.6 và 7.4 chỉ để nhóm báo cáo; kết luận ĐẠT chỉ xét "testVersion" 8.5
```

## Story: US-CMPT-04 - Kiểm tra cú pháp bằng binary đích
Tham chiếu: `FR-CMPT-CODE-003` · `BR-SCN-042` · `ERR-ENV-412-01`

```gherkin
Feature: US-CMPT-04 Kiểm tra cú pháp bằng binary đích

  @AC-CMPT-10 @happy-path
  Scenario: Lint 100% file bằng PHP 8.5
    Given "/usr/bin/php8.5" đã cài và docroot có 2.000 file "*.php", "*.inc", "*.phtml"
    When tool chạy mục P3 kiểm tra cú pháp
    Then "/usr/bin/php8.5 -l" chạy cho đúng 2.000 file, song song theo số vCPU
    And kết quả có 0 "Parse error" và phần lint đạt

  @AC-CMPT-11 @negative
  Scenario: Chưa cài binary đích
    Given "$NEW_BIN" của 8.5 không tồn tại
    When tool chạy mục P3 kiểm tra cú pháp
    Then kết quả chứa "ERR-ENV-412-01" ("Chưa cài PHP 8.5 trên máy chủ.") và phần lint là "PENDING"

  @AC-CMPT-12 @boundary
  Scenario: 1 file Parse error làm kết luận FAIL
    Given 1.999 file hợp lệ và 1 file "inc/x.inc" lỗi cú pháp ở dòng 7 trên PHP 8.5
    When tool chạy mục P3 kiểm tra cú pháp
    Then danh sách lỗi có "file" = "inc/x.inc", "line" = 7, "message" chứa "Parse error"
    And kết luận tương thích của site là "FAIL"
```

## Story: US-CMPT-05 - Composer platform và Packagist
Tham chiếu: `FR-CMPT-COMP-001`, `FR-CMPT-COMP-002` · `BR-SCN-044`, `BR-CMPT-003`, `BR-CMPT-004`, `BR-DATA-003` · `ERR-FEED-503-01`, `ERR-CMPT-424-01`

```gherkin
Feature: US-CMPT-05 Composer platform và Packagist

  @AC-CMPT-13 @happy-path
  Scenario: Phát hiện package chặn và phiên bản tối thiểu thoả
    Given "composer.lock" có "vendor-test/a" 2.1.0 yêu cầu php "^7.4 || ^8.0" và "vendor-test/b" 1.0.0 yêu cầu php ">=7.1 <8.1"
    And metadata Packagist (dữ liệu kiểm thử) cho "vendor-test/b" có bản 1.4.0 là bản nhỏ nhất chấp nhận PHP 8.5
    When tool phân tích Composer với "$NEW" = 8.5
    Then "composer_blockers[]" chỉ có "vendor-test/b" với "constraint" = ">=7.1 <8.1" và "min_compatible_version" = "1.4.0"
    And metadata được cache 24 giờ trong "feeds/cache/packagist/"

  @AC-CMPT-14 @negative
  Scenario: Packagist không truy cập được
    Given "repo.packagist.org" lỗi sau 3 lần thử và không có cache
    When tool tra phiên bản tối thiểu thoả
    Then kết quả chứa "ERR-FEED-503-01" và "min_compatible_version" = "unknown"
    And khi thiếu Composer và không tải được, phần kiểm "check-platform-reqs" có "ERR-CMPT-424-01"

  @AC-CMPT-15 @security
  Scenario: Composer chỉ chạy trên bản sao, không chạy script
    Given "composer.json" khai báo script "post-install-cmd" ghi file "/tmp/qp-test-marker"
    And PHP 8.5 đã cài song song
    When tool chạy "check-platform-reqs" và "why-not php 8.5.12"
    Then lệnh chạy trong "STATE_DIR/work/<plan_id>/" với "config.platform.php" = "8.5.12", "--no-scripts --no-plugins"
    And file "/tmp/qp-test-marker" không được tạo, SHA-256 của "composer.json"/"composer.lock" trong dự án không đổi
    And bản sao bị xoá khi xong; request tới Packagist chỉ chứa tên package

  @AC-CMPT-35 @boundary
  Scenario Outline: TTL cache Packagist 24 giờ và bản tối thiểu không thấp hơn bản đang dùng
    Given "composer.lock" có "vendor-test/b" 1.0.0 là blocker với "$NEW" = 8.5
    And metadata Packagist (dữ liệu kiểm thử) của "vendor-test/b": bản 0.9.0 và 1.4.0 chấp nhận PHP 8.5, mọi bản từ 1.0.0 tới trước 1.4.0 không chấp nhận
    And "feeds/cache/packagist/" có metadata của "vendor-test/b" ghi cách đây <tuoi_cache>
    When tool tra phiên bản tối thiểu thoả
    Then số request tới "https://repo.packagist.org/p2/vendor-test/b.json" là <so_request>
    And "min_compatible_version" = "1.4.0" (không chọn 0.9.0 vì thấp hơn bản đang dùng 1.0.0)

    Examples:
      | tuoi_cache     | so_request |
      | 23 giờ 59 phút | 0          |
      | 24 giờ 01 phút | 1          |
```

## Story: US-CMPT-06 - engines.node và native addon
Tham chiếu: `FR-CMPT-NPM-001`, `FR-CMPT-NPM-002` · `BR-SCN-025`, `BR-SCN-022`, `BR-DATA-003` · `ERR-SCN-424-02`

```gherkin
Feature: US-CMPT-06 engines.node và native addon

  @AC-CMPT-16 @happy-path
  Scenario: Ứng dụng nâng lên Node.js 24
    Given "package-lock.json" v3 có "pkg-a" "engines.node" = ">=18" và "pkg-b" "engines.node" = "<=20"
    And ứng dụng có native addon "addon-test" (dữ liệu kiểm thử)
    When tool quét với dòng đích 24 (bản patch 24.22.1)
    Then "npm_engine_violations[]" chỉ có "pkg-b"
    And sau khi cài dependency bằng "$NEW_BIN" trên bản sao, "native_addons[]" có "addon-test" với "abi_old", "abi_new", "load_ok" = true

  @AC-CMPT-17 @negative
  Scenario: Native addon không nạp được
    Given "addon-test" build lại bằng Node.js 24 nhưng "require('addon-test')" trả exit 1
    When tool quét native addon
    Then "load_ok" = false và kết quả chứa "ERR-SCN-424-02" ("Gói addon-test (native addon) không nạp được trên Node.js 24.")

  @AC-CMPT-18 @boundary
  Scenario: devDependencies và lockfile thiếu engines
    Given "pkg-c" vi phạm "engines.node" nhưng chỉ thuộc "devDependencies"
    And "pkg-d" không có trường "engines" trong lockfile
    When tool quét với dòng đích 24
    Then "pkg-c" được ghi là cảnh báo
    And tool gọi "registry.npmjs.org/pkg-d" chỉ với tên package; với "--offline" kết quả của "pkg-d" là "unknown"
```

## Story: US-CMPT-07 - Directive ini và extension
Tham chiếu: `FR-CMPT-INI-001`, `FR-CMPT-EXT-001` · `BR-SCN-045`, `BR-SCN-046`, `BR-SCN-018` · `ERR-SCN-424-01`

```gherkin
Feature: US-CMPT-07 Directive ini và extension

  @AC-CMPT-19 @happy-path
  Scenario: Directive bị gỡ và extension có trên đích
    Given site nâng từ 7.4 lên 8.5, ".user.ini" dòng 3 có "track_errors = On", pool có "php_admin_value[mbstring.func_overload]"
    And "$OLD_BIN -m" có "mysqli" và gói tương ứng cho 8.5 có trong kho
    When tool quét ini và extension
    Then "ini_findings[]" có 2 phần tử với "file", "line", "directive" và "removed_in" = "8.0"
    And "extension_gaps[]" có "mysqli" với "resolution" = "available"

  @AC-CMPT-20 @negative
  Scenario: Extension thiếu đang được site gọi
    Given extension "legacy_test" không có gói, PECL hay thay thế cho 8.5 và mã site có 14 lời gọi hàm tiền tố "legacy_test_"
    When tool quét extension rồi người vận hành chạy mục P5 của site
    Then "extension_gaps[]" có "legacy_test" với "resolution" = "missing", "usage_hits" = 14 và mục P4 tương ứng
    And mục P5 bị từ chối với "ERR-SCN-424-01" cho tới khi mục P4 ở "DONE" hoặc "WAIVED"

  @AC-CMPT-21 @boundary
  Scenario: Dải mở bên trái và extension không dùng
    Given site nâng từ 8.0 lên 8.5, ini có "track_errors = On"
    And extension "unused_test" có 0 lời gọi hàm tiền tố trong mã site
    When tool quét ini và extension
    Then "track_errors" không có trong "ini_findings[]" vì "removed_in" = 8.0 không thuộc dải (8.0, 8.5]
    And mục checklist của "unused_test" có trạng thái "SKIPPED"
```

## Story: US-CMPT-08 - Loader mã hoá
Tham chiếu: `FR-CMPT-LDR-001` · `BR-SCN-043` · `ERR-SCN-409-03`

```gherkin
Feature: US-CMPT-08 Loader mã hoá

  @AC-CMPT-22 @happy-path
  Scenario: Site dùng SourceGuardian, đích trong dải hỗ trợ
    Given "$OLD_BIN -m" liệt kê SourceGuardian và 37 file ".php" có header mã hoá SourceGuardian
    When tool quét loader với đích 8.5
    Then "loaders[]" có "name" = "SourceGuardian", "files_count" = 37, "target_supported" = true
    And mục P5 của site chỉ mở khi 1 file mã hoá mẫu chạy bằng "$NEW_BIN" trả exit 0

  @AC-CMPT-23 @negative
  Scenario: Không còn nhánh đích có loader
    Given site dùng ionCube và catalog (dữ liệu kiểm thử) không có loader ionCube cho nhánh đích hợp lệ nào
    When tool sinh ứng viên và kế hoạch
    Then mọi nhánh không có loader bị loại khỏi ứng viên
    And kết quả chứa "ERR-SCN-409-03"

  @AC-CMPT-24 @boundary
  Scenario: Giới hạn 50.000 file khi đọc nội dung
    Given docroot có 60.000 file ".php"
    When tool quét loader
    Then tool đọc nội dung tối đa 50.000 file và ghi chú số file chưa đọc = 10.000
```

## Story: US-CMPT-09 - Framework/CMS và ma trận PHP
Tham chiếu: `FR-CMPT-FWK-001` · `BR-SCN-005` · `ERR-SCN-409-01`

```gherkin
Feature: US-CMPT-09 Framework/CMS và ma trận PHP

  @AC-CMPT-25 @happy-path
  Scenario: Nhận diện Laravel và đối chiếu dải PHP
    Given "composer.lock" có "laravel/framework" 11.9.0 và ma trận framework (dữ liệu kiểm thử) ghi dải "8.2 - 8.5"
    When tool quét framework với đích 8.5
    Then "frameworks[]" có "name" = "laravel", "version" = "11.9.0", "php_min" = "8.2", "php_max" = "8.5", "supports_target" = true

  @AC-CMPT-26 @negative
  Scenario: Framework không hỗ trợ nhánh đích hợp lệ nào
    Given site dùng "laravel/framework" 9.52.0, ma trận (dữ liệu kiểm thử) ghi dải "8.0 - 8.2" và nhánh 8.2 hết hạn trước ngày chạy + 365 ngày
    When tool chọn nhánh đích
    Then kết quả chứa "ERR-SCN-409-01" ("Không có phiên bản đích tương thích với laravel 9.52.0.") kèm đề xuất nâng framework trước

  @AC-CMPT-27 @boundary
  Scenario: Framework không có trong ma trận
    Given site dùng "joomla/cms" phiên bản không có trong ma trận
    When tool quét framework
    Then "supports_target" = "unknown" và checklist có mục yêu cầu người vận hành xác nhận dải PHP
```

## Story: US-CMPT-10 - Kết luận tương thích theo site
Tham chiếu: `FR-CMPT-RES-001` · `BR-SCN-042`, `BR-UPG-002`, `BR-CMPT-001` · `ERR-PLAN-422-01` · SCR-004, SCR-009

```gherkin
Feature: US-CMPT-10 Kết luận tương thích theo site

  @AC-CMPT-28 @happy-path
  Scenario: Site đạt mọi phần quét
    Given site có 0 hit mức error, 12 hit mức warning, 0 Parse error, "check-platform-reqs" exit 0
    When tool tổng hợp kết luận
    Then "compat_verdict" = {"status": "PASS", "errors": 0, "warnings": 12, "waived": 0, "pending_parts": []}

  @AC-CMPT-29 @negative
  Scenario: Miễn trừ với lý do ngắn
    Given site có 1 hit mức error chưa miễn trừ
    When người vận hành gửi "POST /api/v1/plans/<plan_id>/compatibility-waivers" với lý do 15 ký tự
    Then API trả HTTP 422 với "ERR-PLAN-422-01"
    And kết luận của site vẫn là "FAIL"

  @AC-CMPT-30 @boundary
  Scenario: Miễn trừ hợp lệ, phần chờ cài và dùng lại kết quả
    Given site có đúng 1 hit mức error và chưa cài PHP 8.5
    When người vận hành miễn trừ hit với lý do 20 ký tự
    Then hit có trạng thái miễn trừ, audit có 1 bản ghi và "waived" = 1
    And kết luận là "PENDING" với "pending_parts[]" chứa phần cần "$NEW_BIN"
    And mở lại kế hoạch khi "scan_fingerprint" và nhánh đích không đổi thì kết quả quét được dùng lại, không quét lại
```

## Story: US-CMPT-11 - Rector tuỳ chọn trên bản sao
Tham chiếu: `FR-CMPT-RCT-001` · `BR-SCN-011` · `ERR-CMPT-424-01`

```gherkin
Feature: US-CMPT-11 Rector tuỳ chọn trên bản sao

  @AC-CMPT-31 @happy-path
  Scenario: Chạy Rector dry-run và duyệt diff
    Given người vận hành bật bước Rector cho site "legacy.test" trong kế hoạch
    When tool chạy bước Rector
    Then mã nguồn được sao chép vào thư mục ngoài docroot trong "STATE_DIR/work/<plan_id>/"
    And Rector chạy "--dry-run" trước và file "rector.diff" được lưu trong thư mục kế hoạch
    And sau khi người vận hành duyệt diff, thay đổi chỉ được ghi vào bản sao

  @AC-CMPT-32 @negative
  Scenario: Rector không có sẵn khi offline
    Given máy offline và "STATE_DIR/tools/php" không có Rector
    When người vận hành bật bước Rector
    Then kết quả chứa "ERR-CMPT-424-01" và mục Rector giữ "PENDING"

  @AC-CMPT-33 @security
  Scenario: Docroot production không bao giờ bị ghi
    Given SHA-256 của mọi file trong docroot "legacy.test" được ghi trước bước Rector
    When tool chạy Rector, người vận hành duyệt diff và áp dụng
    Then SHA-256 của mọi file trong docroot không đổi
    And khi bước Rector không được bật, không tiến trình Rector nào được chạy

  @AC-CMPT-36 @boundary
  Scenario Outline: Diff Rector rỗng, 1 file, chưa duyệt và đã duyệt
    Given site "legacy.test" chạy PHP 7.4.33 (kịch bản SCN-PHP-007, đích 8.5) và người vận hành đã bật mục Rector "CHK-PHP-007-20"
    And Rector "--dry-run" trên "$COPY" sinh "rector.diff" thay đổi <so_file> file
    When người vận hành <hanh_dong>
    Then <ket_qua>

    Examples:
      | so_file | hanh_dong          | ket_qua                                                                                                                                  |
      | 1       | chưa duyệt diff    | 0 file trong "$COPY" đổi SHA-256 và "CHK-PHP-007-20" không chuyển "DONE"                                                                 |
      | 1       | duyệt diff         | đúng 1 file trong "$COPY" đổi SHA-256; "CHK-PHP-007-20" chỉ chuyển "DONE" khi "CHK-PHP-007-14" tới "CHK-PHP-007-18" đạt trên "$COPY" sau khi ghi diff |
      | 0       | duyệt diff rỗng    | "rector.diff" có 0 hunk và 0 file trong "$COPY" đổi SHA-256                                                                               |
```
