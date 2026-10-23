---
id: DOC-AC-QP-JOB
title: Tiêu chí chấp nhận — module JOB và FLT (job runner, log, audit, Phase 2) — php-quickpatch v2
version: 1.0.2
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, job, sse, audit, hash-chain, fleet, ssh, rbac, phase2]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
related_diagrams:
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module JOB và FLT

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 39 scenario: `US-JOB-01..08` (`AC-JOB-01..24`), `US-FLT-01..05` mức epic Phase 2 (`AC-FLT-01..15`) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: `AC-FLT-09` Then nêu server có gói CLI lệch SHA-256 có `state` = `FAILED`, `ERR-FLT-422-03` và bước S5 không chạy (khớp UC-FLT-002 bước 2e1, api-spec-phase2.md §4.3, `BR-FLT-003`); thêm `ERR-FLT-422-03` vào tham chiếu `US-FLT-03`. Tách `AC-JOB-18` (gộp 2 hành vi) thành `AC-JOB-18` (nối lại bằng `Last-Event-ID`) và `AC-JOB-25` mới (giới hạn 3 luồng/phiên, 10 luồng/console: Given dựng sẵn luồng, Then 429 `ERR-JOB-429-02`, luồng đang mở không bị ngắt; khớp UC-JOB-001 bước 6b1, api-spec-jobs.md §4.3); thêm `ERR-JOB-429-02` vào tham chiếu `US-JOB-06`; dùng số kế tiếp 25 để không đánh lại `AC-JOB-19..24`; tổng 40 scenario. Việc cần làm ở file khác: thêm `AC-JOB-25` vào dòng `US-JOB-06` của [acceptance-criteria.md](acceptance-criteria.md); sinh lại `TC-JOB-018` và thêm `TC-JOB-025` có bước thao tác cho từng KQ ở [test-cases-job-flt.md](../test/test-cases-job-flt.md); đồng bộ test-cases-coverage.md, rtm.md |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review rule 08 (4 story chỉ có `@security`, chưa có `@boundary`): thêm 4 scenario `@boundary`, đánh số tiếp theo số lớn nhất của module, không đổi mã cũ: `AC-JOB-26` (`US-JOB-08`, chuỗi hash qua ranh giới `audit-202610.jsonl`/`audit-202611.jsonl` lúc 23:59:59.999Z/00:00:00.000Z UTC, xoá bản ghi cuối tháng hoặc đổi `prev_hash` bản ghi đầu tháng → `first_broken_seq` = 1241, `ERR-AUD-409-01`; `BR-AUD-003`); `AC-FLT-16` (`US-FLT-01`, `port` 0/1/65535/65536, `server_id` 63/64 ký tự, `groups` 20/21 phần tử theo api-spec-phase2.md §3, §3.2 → 201 hoặc `ERR-FLT-422-01`); `AC-FLT-17` (`US-FLT-03`, canary thoát mã 1/2, đợt 5 server lỗi 0/5, 1/5 (20%, tiếp tục), 2/5 (40%, dừng), đợt 4 server lỗi 1/4 (25%, dừng); `BR-FLT-005`, nhánh lệnh ghi `fix`); `AC-FLT-18` (`US-FLT-05`, `generated_at` snapshot so với `current/` của server G − 1 s/G/G + 1 s, đồng hồ server G − 60 phút/G − 60 phút 1 s, gói hỏng ở 1/5 và 2/5 server của đợt; `ERR-FEED-409-02`, `ERR-FEED-422-02`, `ERR-FLT-409-01`). Không dùng tỉ lệ 21% reviewer gợi ý vì đợt ≤ 5 server không tạo được 21%; dùng 25% (1/4, `batch_size` = 4) làm giá trị nhỏ nhất vượt ngưỡng. Tham chiếu thêm `BR-AUD-001` (`US-JOB-08`), `BR-JOB-008` (`US-FLT-03`), `BR-FLT-005`, `BR-FEED-010`, `ERR-FEED-409-02`, `ERR-FLT-409-01` (`US-FLT-05`). Tổng 44 scenario. Việc cần làm ở file khác: [acceptance-criteria.md](acceptance-criteria.md) §1.3 (4 story của file này đã có `@boundary` bằng scenario mới thay cho hướng gắn tag `AC-JOB-24`, `AC-FLT-03`, `AC-FLT-09`), §2 (40 → 44), §3 (thêm `AC-JOB-26`, `AC-FLT-16`, `AC-FLT-17`, `AC-FLT-18`); cột AC và số scenario của [backlog.md](backlog.md); thêm `TC-JOB-026`, `TC-FLT-016..018` ở [test-cases-job-flt.md](../test/test-cases-job-flt.md); đồng bộ test-cases-coverage.md, rtm.md |

Ký hiệu dùng chung: [acceptance-criteria.md §1.2](acceptance-criteria.md). AC của module FLT là tiêu chí mức epic cho Phase 2 (chỉ đặc tả); khi tách story Phase 2, mỗi story con kế thừa scenario tương ứng và bổ sung chi tiết.

## 1. Module JOB

## Story: US-JOB-01 - Hàng đợi và chạy job
Tham chiếu: `FR-JOB-RUN-001` · `BR-JOB-001`, `BR-JOB-003`, `BR-JOB-008` · `ERR-JOB-429-01`, `ERR-JOB-409-01`, `ERR-JOB-500-01`, `ERR-JOB-504-01` · SCR-006

```gherkin
Feature: US-JOB-01 Hàng đợi và chạy job

  @AC-JOB-01 @happy-path
  Scenario: Giới hạn đồng thời theo loại job
    Given phiên console hợp lệ và hàng đợi rỗng
    When client tạo lần lượt job "fix" (write), "scan", "assess", "report" (read) cách nhau 1 s
    Then "fix", "scan", "assess" ở "RUNNING" và "report" ở "QUEUED" tới khi 1 job read kết thúc (FIFO theo "created_at")
    And "job.json" có "job_id" khớp "^JOB-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$", "action", "argv" đã che, "actor", "state", "created_at", "started_at", "ended_at", "exit_code", "result"
    And job thoát mã 0 có trạng thái "SUCCEEDED", thoát mã 1 có trạng thái "SUCCEEDED_WITH_ISSUES"

  @AC-JOB-02 @negative
  Scenario: Hàng đợi đầy, job trùng và CLI thất bại
    Given hàng đợi có 20 job "QUEUED"
    When client tạo job thứ 21
    Then API trả 429 "ERR-JOB-429-01" ("Hàng đợi đã đầy (20 job). Chờ job hiện tại hoàn thành.")
    And tạo job "migrate_switch" cho "shop.test" khi đã có job cùng hành động, cùng site đang "QUEUED" trả 409 "ERR-JOB-409-01" kèm "details.job_id"
    And job có CLI thoát mã 2 chuyển "FAILED" với "ERR-JOB-500-01"

  @AC-JOB-03 @boundary
  Scenario Outline: Timeout theo loại hành động
    Given job "<action>" chạy liên tục không kết thúc
    When thời gian chạy đạt <t> s
    Then trạng thái job là "<state>"

    Examples:
      | action           | t    | state                     |
      | migrate_rollback | 300  | RUNNING                   |
      | migrate_rollback | 301  | FAILED (ERR-JOB-504-01)   |
      | migrate_switch   | 1201 | FAILED (ERR-JOB-504-01)   |
      | scan             | 1800 | RUNNING                   |
      | feeds_update     | 961  | FAILED (ERR-JOB-504-01)   |
      | audit_verify     | 601  | FAILED (ERR-JOB-504-01)   |
```

## Story: US-JOB-02 - Khoá dùng chung với CLI
Tham chiếu: `FR-JOB-RUN-002` · `BR-JOB-002`, `BR-FEED-015` · `ERR-JOB-409-02`, `ERR-CLI-423-01` · `NFR-REL-004`

```gherkin
Feature: US-JOB-02 Khoá dùng chung với CLI

  @AC-JOB-04 @happy-path
  Scenario: Job đọc chạy song song với scan CLI
    Given người vận hành đang chạy "php-quickpatch.sh scan" trong SSH (khoá chia sẻ)
    When console tạo job "assess"
    Then job "assess" chuyển "RUNNING" trong ≤ 5 s mà không chờ lượt "scan" kết thúc
    And khi không có lượt CLI nào, job "fix" lấy được "flock -x -n" trên "STATE_DIR/.lock" và chạy ngay

  @AC-JOB-05 @negative
  Scenario: CLI ngoài console giữ khoá quá 30 phút
    Given lượt "php-quickpatch.sh fix" PID 5120 chạy từ SSH giữ khoá độc quyền trong 31 phút
    When console tạo job "migrate_install"
    Then job ở "QUEUED", thử lấy khoá lại mỗi 5 s
    And sau 30 phút job chuyển "FAILED" với "ERR-JOB-409-02" ("Một lượt php-quickpatch khác (PID 5120) giữ khoá quá 30 phút; job chưa chạy.")

  @AC-JOB-06 @boundary
  Scenario: Không bao giờ có 2 job ghi cùng chạy
    Given job "fix" của console đang "RUNNING"
    When người vận hành chạy "php-quickpatch.sh fix" từ SSH và chạy "php-quickpatch.sh feeds update"
    Then lệnh "fix" in "Another php-quickpatch run is in progress." ("ERR-CLI-423-01") với mã thoát 2
    And "feeds update" chạy được vì dùng "feeds/.lock"
    And trong 100 lần thử tạo đồng thời job ghi từ console và CLI, số lần có 2 thao tác ghi cùng chạy = 0
```

## Story: US-JOB-03 - Huỷ job
Tham chiếu: `FR-JOB-RUN-003` · `BR-JOB-004` · `ERR-JOB-423-01`, `ERR-JOB-404-01`

```gherkin
Feature: US-JOB-03 Huỷ job

  @AC-JOB-07 @happy-path
  Scenario: Huỷ job đang chờ và job đọc đang chạy
    Given job "report" ở "QUEUED" và job "scan" ở "RUNNING" bỏ qua SIGTERM
    When người vận hành gửi "POST /api/v1/jobs/{job_id}/cancellations" cho cả 2 job
    Then job "report" chuyển "CANCELLED" ngay với HTTP 200
    And job "scan" nhận SIGTERM cho cả nhóm tiến trình (HTTP 202, "effect" = "SIGTERM_SENT"), nhận SIGKILL sau 10 s rồi chuyển "CANCELLED"
    And audit ghi 2 lần huỷ

  @AC-JOB-08 @negative
  Scenario Outline: Huỷ không được phép hoặc job không tồn tại
    Given "<dieu_kien>"
    When người vận hành yêu cầu huỷ job
    Then API trả <http> "<loi>"

    Examples:
      | dieu_kien                                  | http | loi             |
      | job ghi ở "phase" = "MANIFEST_WRITTEN"      | 423  | ERR-JOB-423-01  |
      | job ghi ở "phase" = "VERIFYING"             | 423  | ERR-JOB-423-01  |
      | "job_id" = "JOB-20261022-000000-ffff"      | 404  | ERR-JOB-404-01  |

  @AC-JOB-09 @boundary
  Scenario: Huỷ trong cửa sổ health check và huỷ lặp
    Given job "migrate_switch" của "shop.test" ở "phase" = "HC_RUNNING"
    When người vận hành yêu cầu huỷ job
    Then API trả 202 với "effect" = "HC_ROLLBACK_STARTED", health check dừng và site được rollback với "rollback_reason" = "MANUAL"
    And yêu cầu huỷ lặp lại cho job đã kết thúc trả 200 và không đổi trạng thái job
```

## Story: US-JOB-04 - Đối soát job khi console khởi động lại
Tham chiếu: `FR-JOB-RUN-004` · `BR-JOB-005` · `ERR-JOB-500-02` · `NFR-REL-003`

```gherkin
Feature: US-JOB-04 Đối soát job khi console khởi động lại

  @AC-JOB-10 @happy-path
  Scenario: Console khởi động lại khi CLI vẫn chạy
    Given job "fix" "RUNNING" với PID 6200 và tiến trình console bị dừng bằng SIGKILL
    When người vận hành chạy lại "php-quickpatch.sh serve" trong lúc PID 6200 còn sống
    Then trong ≤ 5 s job vẫn ở "RUNNING" và console tiếp tục đọc log từ byte offset cuối
    And khi PID 6200 kết thúc, job nhận trạng thái theo mã thoát

  @AC-JOB-11 @negative
  Scenario: Máy khởi động lại làm mất tiến trình
    Given job "migrate_install" "RUNNING" và máy chủ khởi động lại
    When người vận hành chạy "php-quickpatch.sh serve"
    Then job chuyển "INTERRUPTED" với "ERR-JOB-500-02" ("Job … bị gián đoạn; kiểm tra trạng thái trước khi chạy lại.")
    And 0 job ghi nào được tự chạy lại

  @AC-JOB-12 @boundary
  Scenario: Nhiều job và lượt chuyển đang health check
    Given 50 job ở "RUNNING" trong "STATE_DIR/jobs/" và 1 lượt chuyển "HC_RUNNING" có "t_C9" cách hiện tại 920 s
    When console khởi động
    Then 100% job "RUNNING" được đối soát trong ≤ 5 s
    And health check của lượt chuyển được chạy lại đủ 10 vòng (600 s) bằng "baseline.json" đã lưu, không rollback khi chưa có vi phạm
```

## Story: US-JOB-05 - Lưu log, kết quả và lưu giữ
Tham chiếu: `FR-JOB-LOG-001`, `FR-JOB-LOG-003` · `BR-JOB-006`, `BR-SEC-006` · `ERR-JOB-410-01` · `NFR-SEC-010`, `NFR-CAP-001`

```gherkin
Feature: US-JOB-05 Lưu log, kết quả và lưu giữ

  @AC-JOB-13 @happy-path
  Scenario: Lưu kết quả job và che bí mật
    Given job "scan --json" ghi JSON ra stdout và 1 dòng "token=abc123" ra stderr
    When job kết thúc
    Then "STATE_DIR/jobs/<job_id>/" có quyền 0700 và chứa "job.json", "output.log", "result.json", "phase" với quyền 0600
    And "result.json" là JSON của stdout; "output.log" có dòng "token=***" và chuỗi "abc123" xuất hiện 0 lần

  @AC-JOB-14 @negative
  Scenario: Đọc log đã bị dọn
    Given job ghi kết thúc cách đây 31 ngày
    When client gọi "GET /api/v1/jobs/{job_id}/log"
    Then API trả 410 "ERR-JOB-410-01" ("Log của job … đã bị xoá theo chính sách lưu giữ 30 ngày.")
    And "GET /api/v1/jobs/{job_id}" vẫn trả "job.json" và "result.json" của job

  @AC-JOB-15 @boundary
  Scenario: Trần 20 MiB mỗi log và 200 MiB toàn thư mục
    Given 1 job ghi 25 MiB log và tổng "jobs/" đạt 205 MiB
    When job chạy xong và console thực hiện dọn dẹp lúc khởi động
    Then "output.log" của job dừng ở 20 MiB, "job.json" có "truncated" = true và toàn bộ 25 MiB log còn trong "php-quickpatch.log"
    And "output.log" cũ nhất bị xoá trước cho tới khi "jobs/" ≤ 200 MiB; "job.json", "result.json" của job ghi < 365 ngày được giữ
```

## Story: US-JOB-06 - Stream log qua SSE
Tham chiếu: `FR-JOB-LOG-002` · `BR-JOB-007` · `ERR-JOB-404-01`, `ERR-JOB-410-01`, `ERR-JOB-429-02` (định nghĩa ở [error-matrix.md](../srs/error-matrix.md) v1.0.1) · `NFR-PERF-003`

```gherkin
Feature: US-JOB-06 Stream log qua SSE

  @AC-JOB-16 @happy-path
  Scenario: Luồng sự kiện của job đang chạy
    Given phiên console hợp lệ và job "fix" "RUNNING"
    When trình duyệt mở "EventSource" tới "/api/v1/jobs/{job_id}/events" bằng cookie
    Then response có "Content-Type: text/event-stream" và dòng đầu "retry: 2000"
    And sự kiện "log" (trường "id" = byte offset cuối dòng), "status", "phase", "end" được đẩy; dòng log mới tới trình duyệt ≤ 2 s sau khi CLI ghi
    And comment heartbeat gửi mỗi 15 s và luồng đóng sau sự kiện "end"

  @AC-JOB-17 @negative
  Scenario Outline: Luồng không mở được
    Given "<dieu_kien>"
    When trình duyệt mở luồng sự kiện của job
    Then API trả <http> "<loi>"

    Examples:
      | dieu_kien                         | http | loi            |
      | job không tồn tại                  | 404  | ERR-JOB-404-01 |
      | "output.log" của job đã bị dọn      | 410  | ERR-JOB-410-01 |

  @AC-JOB-18 @boundary
  Scenario: Nối lại luồng sau khi mất kết nối
    Given luồng bị ngắt sau sự kiện "log" có "id" = 1873
    When trình duyệt kết nối lại với header "Last-Event-ID: 1873"
    Then luồng tiếp tục từ byte 1873, không có dòng log nào bị lặp hay mất

  @AC-JOB-25 @boundary
  Scenario: Giới hạn 3 luồng mỗi phiên và 10 luồng toàn console
    Given phiên A, B, C mỗi phiên đang mở 3 luồng SSE và phiên D đang mở 1 luồng SSE tới job "fix" "RUNNING" (console có 10 luồng từ 4 phiên)
    When phiên A mở luồng thứ 4 của phiên tới "/api/v1/jobs/{job_id}/events"
    And phiên D mở luồng thứ 2 của phiên (luồng thứ 11 trên console)
    Then cả 2 request trả 429 "ERR-JOB-429-02" với "localization_key" = "job.sse.limit"; thông báo của phiên A có "{limit}" = 3, của phiên D có "{limit}" = 10
    And 10 luồng đang mở không bị ngắt và vẫn nhận sự kiện; trình duyệt không tự nối lại 2 luồng bị từ chối
```

## Story: US-JOB-07 - Audit append-only
Tham chiếu: `FR-JOB-AUD-001` · `BR-AUD-001`, `BR-AUD-002`, `BR-AUD-003`, `BR-AUD-004`, `BR-AUD-005` · `ERR-AUD-500-01` · `NFR-REL-002`

```gherkin
Feature: US-JOB-07 Audit append-only

  @AC-JOB-19 @happy-path
  Scenario: Bản ghi intent và result của job ghi
    Given phiên console hợp lệ và tháng hiện tại 10/2026
    When job "fix" chạy và kết thúc với mã thoát 0
    Then "STATE_DIR/audit/audit-202610.jsonl" (quyền 0600, mở "O_APPEND") có bản ghi "intent" ghi trước thay đổi đầu tiên và bản ghi "result" sau khi kết thúc
    And mỗi bản ghi có "seq", "ts" (UTC, ms), "actor", "sys_user", "source" = "console", "action", "args" đã che, "job_id", "run_id", "plan_id", "result", "exit_code", "prev_hash", "hash"
    And "hash" = SHA-256("prev_hash" ‖ JSON chuẩn hoá của bản ghi không có "hash", khoá sắp theo bảng chữ cái)

  @AC-JOB-20 @negative
  Scenario: Không ghi được bản ghi intent
    Given thư mục "STATE_DIR/audit" không ghi được (phân vùng đầy)
    When người vận hành xác nhận job "migrate_install"
    Then thao tác bị huỷ trước thay đổi đầu tiên với "ERR-AUD-500-01" ("Không ghi được nhật ký kiểm toán; thao tác thay đổi đã bị huỷ.")
    And 0 gói được cài, 0 file hệ thống bị sửa

  @AC-JOB-21 @boundary
  Scenario: Chuỗi qua ranh giới file và lỗi ghi result
    Given audit chưa có bản ghi nào trước ngày 2026-10-22 và bản ghi cuối tháng 10 có "hash" = H
    When bản ghi đầu tiên được ghi và sau đó bản ghi đầu tiên của tháng 11/2026 được ghi
    Then bản ghi đầu tiên có "prev_hash" = 64 ký tự "0"; bản ghi đầu "audit-202611.jsonl" có "prev_hash" = H
    And khi ghi bản ghi "result" lỗi, tool thử lại 3 lần cách nhau 1 s rồi ghi lỗi vào "result.json" và stderr
```

## Story: US-JOB-08 - Truy vấn và kiểm toàn vẹn audit
Tham chiếu: `FR-JOB-AUD-002`, `FR-JOB-AUD-003` · `BR-AUD-001`, `BR-AUD-002`, `BR-AUD-003` · `ERR-AUD-409-01` · `NFR-REL-007`

```gherkin
Feature: US-JOB-08 Truy vấn và kiểm toàn vẹn audit

  @AC-JOB-22 @happy-path
  Scenario: Lọc audit và kiểm chuỗi
    Given audit có 1.240 bản ghi từ 2026-10-01 tới 2026-10-22, trong đó 12 bản ghi "migrate_switch"
    When kiểm toán viên chạy "audit list --from 2026-10-01 --to 2026-10-22 --action migrate_switch --json" và "audit verify --json"
    Then "audit list" trả đúng 12 bản ghi
    And "audit verify" trả {"verified": true, "records": 1240, "first_broken_seq": null}

  @AC-JOB-23 @negative
  Scenario: Bản ghi bị sửa 1 byte
    Given bản ghi "seq" = 877 bị sửa 1 byte bằng trình soạn thảo
    When kiểm toán viên chạy "audit verify --json"
    Then kết quả {"verified": false, "first_broken_seq": 877} và lỗi "ERR-AUD-409-01"

  @AC-JOB-24 @security
  Scenario: Phát hiện mọi thay đổi và không có đường sửa/xoá
    Given bộ test sửa 1 byte tại 1.000 vị trí ngẫu nhiên (mỗi lần trên 1 bản sao audit) và 1 lần xoá bản ghi cuối tháng 10
    When kiểm toán viên chạy "audit verify" cho từng bản sao
    Then 100% thay đổi bị phát hiện, kể cả bản ghi cuối tháng 10 bị xoá (phát hiện tại bản ghi đầu tháng 11)
    And CLI và API không có lệnh hay endpoint nào sửa hoặc xoá bản ghi audit

  @AC-JOB-26 @boundary
  Scenario: Chuỗi hash qua ranh giới 2 file tháng
    Given máy kiểm thử chuẩn dùng đồng hồ giả lập theo UTC, "audit-202610.jsonl" có chuỗi hợp lệ "seq" 1..1.239 và chưa có job ghi nào (không có neo "audit_anchor")
    When tool ghi bản ghi đăng nhập thất bại "seq" = 1.240 lúc "2026-10-31T23:59:59.999Z" và "seq" = 1.241 lúc "2026-11-01T00:00:00.000Z"
    And kiểm toán viên chạy "audit verify --json" trên audit gốc, trên bản sao A (xoá dòng "seq" = 1.240) và bản sao B (đổi "prev_hash" của "seq" = 1.241 thành 64 ký tự "0")
    Then "seq" = 1.240 là dòng cuối của "audit-202610.jsonl"; "seq" = 1.241 là dòng đầu của "audit-202611.jsonl" và có "prev_hash" = "hash" của "seq" = 1.240
    And audit gốc trả {"verified": true, "records": 1241, "first_broken_seq": null}
    And bản sao A và bản sao B đều trả "verified" = false, "first_broken_seq" = 1241 và "ERR-AUD-409-01" ("Nhật ký kiểm toán bị thay đổi từ bản ghi #1241.")
```

## 2. Module FLT — Phase 2 (mức epic)

## Story: US-FLT-01 - Danh mục server và ghim khoá SSH
Tham chiếu: `FR-FLT-INV-001`, `FR-FLT-INV-002` · `BR-FLT-001`, `BR-FLT-002`, `BR-FLT-008` · `ERR-FLT-401-01`, `ERR-FLT-403-01`, `ERR-FLT-404-01`, `ERR-FLT-422-01`, `ERR-FLT-424-01`, `ERR-FLT-504-01` · `NFR-SEC-011` · SCR-020

```gherkin
Feature: US-FLT-01 Danh mục server và ghim khoá SSH

  @AC-FLT-01 @happy-path
  Scenario: Thêm server và kiểm kết nối
    Given Admin đăng nhập máy trung tâm qua SSH tunnel
    When Admin thêm server "web01" (host "203.0.113.10", port 22, user "qp", "auth" = "key:/root/.ssh/qp_ed25519", fingerprint SHA256 đã xác nhận, nhóm "prod", "sudo_mode" = "sudo-n") rồi bấm kiểm kết nối
    Then bản ghi được lưu trong "central.db" và không có trường mật khẩu SSH nào
    And lệnh kết nối dùng "-o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=<known_hosts riêng> -o ConnectTimeout=10"
    And kết quả có "reachability" = true và "prerequisites[]" báo Bash ≥ 4.3, "flock", "curl" đạt

  @AC-FLT-02 @negative
  Scenario Outline: Kết nối bị từ chối
    Given server "web02" có "<dieu_kien>"
    When Admin bấm kiểm kết nối
    Then kết quả là "<loi>" và không lệnh nào được chạy trên server

    Examples:
      | dieu_kien                                     | loi             |
      | fingerprint khoá máy chủ khác giá trị đã ghim  | ERR-FLT-403-01  |
      | khoá SSH bị từ chối                             | ERR-FLT-401-01  |
      | thiếu "flock"                                   | ERR-FLT-424-01  |

  @AC-FLT-03 @security
  Scenario: Dữ liệu khai báo sai và không chấp nhận khoá chưa ghim
    Given Admin nhập server với port 70000 hoặc trường "password"
    When Admin lưu bản ghi
    Then lưu bị từ chối với "ERR-FLT-422-01"
    And server không phản hồi trong 10 s trả "ERR-FLT-504-01"; số kết nối SSH chấp nhận khoá máy chủ chưa ghim = 0; sửa "server_id" không tồn tại trả "ERR-FLT-404-01"

  @AC-FLT-16 @boundary
  Scenario Outline: Biên giá trị khi khai báo server
    Given Admin đăng nhập máy trung tâm và "central.db" chưa có bản ghi server nào
    And bản ghi server giống "web01" của AC-FLT-01, chỉ khác "<truong>" = <gia_tri> ("server_id" khác nhau ở mỗi dòng)
    When Admin gửi "POST /api/v1/servers"
    Then <ket_qua>

    # Ràng buộc: api-spec-phase2.md §3.2 ("port" 1–65535, "groups" ≤ 20 phần tử) và §3 ("server_id" khớp "^[a-z0-9][a-z0-9_.-]{0,62}$", tức 1–63 ký tự; đề xuất)
    Examples:
      | truong    | gia_tri                               | ket_qua                                                                                                     |
      | port      | 0                                     | API trả 422 "ERR-FLT-422-01" ("Thông tin server không hợp lệ: port.") và "central.db" có 0 bản ghi mới      |
      | port      | 1                                     | API trả 201 và bản ghi lưu "port" = 1                                                                       |
      | port      | 65535                                 | API trả 201 và bản ghi lưu "port" = 65535                                                                   |
      | port      | 65536                                 | API trả 422 "ERR-FLT-422-01" ("Thông tin server không hợp lệ: port.") và "central.db" có 0 bản ghi mới      |
      | server_id | 63 ký tự ("w" + 62 ký tự "0")         | API trả 201 và bản ghi lưu đủ 63 ký tự                                                                      |
      | server_id | 64 ký tự ("w" + 63 ký tự "0")         | API trả 422 "ERR-FLT-422-01" ("Thông tin server không hợp lệ: server_id.") và "central.db" có 0 bản ghi mới |
      | groups    | 20 nhóm khác nhau "g01".."g20"        | API trả 201 và bản ghi lưu 20 nhóm                                                                          |
      | groups    | 21 nhóm khác nhau "g01".."g21"        | API trả 422 "ERR-FLT-422-01" ("Thông tin server không hợp lệ: groups.") và "central.db" có 0 bản ghi mới    |
```

## Story: US-FLT-02 - Tài khoản và vai trò Phase 2
Tham chiếu: `FR-FLT-RBAC-001` · `BR-FLT-008` · `ERR-FLT-403-02`, `ERR-AUTH-401-01` · SCR-020

```gherkin
Feature: US-FLT-02 Tài khoản và vai trò Phase 2

  @AC-FLT-04 @happy-path
  Scenario: Admin tạo tài khoản Viewer và Operator
    Given Admin đăng nhập máy trung tâm (chỉ nghe 127.0.0.1, truy cập qua SSH tunnel)
    When Admin gửi "POST /api/v1/users" tạo "v1" vai trò Viewer và "o1" vai trò Operator
    Then 2 tài khoản được tạo, mật khẩu lưu dạng băm "hashlib.scrypt" và 0 mật khẩu dạng rõ trong "central.db"

  @AC-FLT-05 @negative
  Scenario: Viewer gọi thao tác thay đổi và sai mật khẩu
    Given "v1" đăng nhập với vai trò Viewer
    When "v1" gửi "POST /api/v1/fleet-runs"
    Then API trả 403 "ERR-FLT-403-02" ("Vai trò Viewer không được phép …")
    And đăng nhập "o1" với mật khẩu sai trả 401 "ERR-AUTH-401-01"

  @AC-FLT-06 @boundary
  Scenario Outline: Ma trận quyền theo vai trò
    Given người dùng có vai trò "<vai_tro>"
    When người dùng thực hiện "<thao_tac>"
    Then kết quả là "<ket_qua>"

    Examples:
      | vai_tro  | thao_tac                     | ket_qua         |
      | Viewer   | xem dashboard, xuất báo cáo   | cho phép        |
      | Operator | chạy "fix" theo đợt            | cho phép        |
      | Operator | thêm server                   | ERR-FLT-403-02  |
      | Admin    | thêm server, tạo tài khoản     | cho phép        |
```

## Story: US-FLT-03 - Chạy CLI từ xa theo đợt
Tham chiếu: `FR-FLT-EXEC-001`, `FR-FLT-EXEC-002` · `BR-FLT-001`, `BR-FLT-003`, `BR-FLT-004`, `BR-FLT-005`, `BR-FLT-008`, `BR-JOB-008` · `ERR-FLT-409-01`, `ERR-FLT-403-02`, `ERR-FLT-422-02`, `ERR-FLT-422-03` (định nghĩa ở [error-matrix.md](../srs/error-matrix.md) v1.0.1), `ERR-FLT-504-01` · `NFR-PERF-008`, `NFR-SEC-012` · SCR-022

```gherkin
Feature: US-FLT-03 Chạy CLI từ xa theo đợt

  @AC-FLT-07 @happy-path
  Scenario: Thu scan --json từ nhóm 100 server
    Given Operator chọn nhóm "prod" có 100 server đã ghim khoá
    When Operator chạy "scan --json" theo đợt
    Then canary 1 server chạy trước, sau đó các đợt ≤ 5 server với ≤ 10 kết nối song song
    And trên mỗi server, tool tạo thư mục "mktemp -d", đẩy gói CLI qua "tar" trên SSH, "sha256sum -c" khớp hash của máy trung tâm, chạy lệnh có timeout, thu stdout và mã thoát, xoá thư mục tạm
    And thu đủ kết quả 100 server trong ≤ 20 phút

  @AC-FLT-08 @negative
  Scenario Outline: Dừng đợt chạy
    Given "<dieu_kien>"
    When đợt chạy được đánh giá
    Then đợt dừng với "<loi>" và các đợt sau không chạy

    Examples:
      | dieu_kien                                     | loi            |
      | canary trả mã thoát 2                          | ERR-FLT-409-01 |
      | 2/5 server của 1 đợt lỗi (40% > 20%)            | ERR-FLT-409-01 |
      | Viewer yêu cầu chạy "fix"                       | ERR-FLT-403-02 |

  @AC-FLT-09 @security
  Scenario: Toàn vẹn gói CLI, ngưỡng lỗi và dọn file tạm
    Given 1/5 server của 1 đợt lỗi (20%) và 1 server có gói CLI bị sửa trên đường truyền
    When đợt chạy được đánh giá
    Then đợt tiếp tục vì tỉ lệ lỗi 20% không vượt ngưỡng
    And server có gói CLI lệch SHA-256 có kết quả "state" = "FAILED" với "ERR-FLT-422-03" ("Gói CLI trên {server} không khớp mã băm SHA-256 của máy trung tâm; không chạy lệnh.") và bước S5 (chạy lệnh) không chạy trên server đó
    And server trả JSON khác major hỗ trợ được ghi "ERR-FLT-422-02"
    And sau khi chạy, số file tạm của tool còn lại ngoài STATE_DIR trên mọi server = 0, kể cả server lỗi "ERR-FLT-422-03" và server lỗi "ERR-FLT-504-01"

  @AC-FLT-17 @boundary
  Scenario Outline: Ngưỡng lỗi của canary và ngưỡng 20% của 1 đợt
    Given Operator chạy "fix" với "batch_size" = <batch_size> trên 15 server "web01".."web15" của nhóm "shop", cả 15 server đã dry-run thành công và "web01" là canary
    And <dieu_kien>
    When đợt chứa server đó kết thúc và đợt chạy được đánh giá
    Then <ket_qua>

    # "Lỗi" = server "FAILED" (mã thoát 2, "ERR-FLT-422-02", "ERR-FLT-422-03") hoặc "TIMEOUT"; mã thoát 1 ("SUCCEEDED_WITH_ISSUES") không tính là lỗi (UC-FLT-002 bước 4, 5, nhánh 3a)
    # Mỗi đợt có ≤ 5 server nên tỉ lệ nhỏ nhất vượt 20% là 25% (1/4 server khi "batch_size" = 4); tỉ lệ 21% không xảy ra
    Examples:
      | batch_size | dieu_kien                                                  | ket_qua                                                                                                                   |
      | 5          | canary "web01" thoát mã 1                                  | đợt 2 ("web02".."web06") được chạy                                                                                        |
      | 5          | canary "web01" thoát mã 2                                  | "fleet_run" "STOPPED" với "ERR-FLT-409-01" ("Đã dừng đợt 1: 1/1 server lỗi."); "web02".."web15" không chạy lệnh ghi        |
      | 5          | 5/5 server của đợt 2 thoát mã 1                            | đợt 3 ("web07".."web11") được chạy                                                                                        |
      | 5          | 1/5 server của đợt 2 ("web04") thoát mã 2 (20%, bằng ngưỡng) | đợt 3 ("web07".."web11") được chạy                                                                                        |
      | 5          | 2/5 server của đợt 2 ("web03", "web04") thoát mã 2 (40%)   | "fleet_run" "STOPPED" với "ERR-FLT-409-01" ("Đã dừng đợt 2: 2/5 server lỗi."); "web07".."web15" không chạy lệnh ghi        |
      | 4          | đợt 2 gồm "web02".."web05", 1/4 server ("web04") ở "TIMEOUT" (25%) | "fleet_run" "STOPPED" với "ERR-FLT-409-01" ("Đã dừng đợt 2: 1/4 server lỗi."); "web06".."web15" không chạy lệnh ghi |
```

## Story: US-FLT-04 - Dashboard tổng hợp nhiều server
Tham chiếu: `FR-FLT-DASH-001`, `FR-FLT-DASH-002`, `FR-FLT-AUD-001` · `BR-FLT-006`, `BR-FLT-008`, `BR-AUD-003` · `ERR-FLT-404-01`, `ERR-AUD-409-01` · SCR-021

```gherkin
Feature: US-FLT-04 Dashboard tổng hợp nhiều server

  @AC-FLT-10 @happy-path
  Scenario: Ma trận rủi ro và đi sâu theo server
    Given dữ liệu thu từ 20 server trong 6 giờ qua
    When Viewer mở SCR-021 và lọc nhóm "prod"
    Then ma trận server × runtime hiển thị KEV, Critical, EOL, chưa vá, "R" và thời điểm thu thập của từng server
    And đi sâu vào "web01" hiển thị các màn hình Phase 1 ở chế độ chỉ đọc từ JSON đã thu
    And audit hợp nhất sắp theo thời gian, giữ "hash" gốc và kiểm chuỗi riêng từng server

  @AC-FLT-11 @negative
  Scenario: Server không tồn tại và chuỗi audit của 1 server bị đứt
    Given chuỗi audit thu từ "web03" bị sửa ở "seq" = 210
    When Viewer mở "GET /api/v1/servers/web99/results" và kiểm audit hợp nhất
    Then request "web99" trả 404 "ERR-FLT-404-01"
    And kiểm audit báo "ERR-AUD-409-01" chỉ cho nguồn "web03"; nguồn khác "verified" = true

  @AC-FLT-12 @boundary
  Scenario Outline: Độ tươi dữ liệu server
    Given server có "collected_at" cách hiện tại <tuoi>
    When Viewer mở SCR-021
    Then "<ket_qua>"

    Examples:
      | tuoi               | ket_qua                                          |
      | 24 giờ             | hiển thị bình thường                             |
      | 24 giờ 01 phút     | gắn nhãn "cũ"                                    |
      | 7 ngày 1 giây      | loại khỏi số liệu tổng, liệt kê ở danh sách riêng |
```

## Story: US-FLT-05 - Phân phối snapshot từ máy trung tâm
Tham chiếu: `FR-FLT-FEED-001` · `BR-FLT-005`, `BR-FLT-007`, `BR-FEED-010`, `BR-FEED-055`, `BR-FEED-056` · `ERR-FEED-422-02`, `ERR-FEED-409-02`, `ERR-FLT-409-01` · SCR-022

```gherkin
Feature: US-FLT-05 Phân phối snapshot từ máy trung tâm

  @AC-FLT-13 @happy-path
  Scenario: Đẩy snapshot tới 8 server không ra Internet
    Given máy trung tâm có mạng và 8 server nhóm "offline" không ra Internet
    When Operator chạy phân phối snapshot cho nhóm "offline"
    Then máy trung tâm chạy "feeds update" rồi "feeds export", đẩy file tới 8 server và chạy "feeds import FILE --sha256 HEX" trên từng server
    And 8 server có cùng "bundle_id" với máy trung tâm

  @AC-FLT-14 @negative
  Scenario: Snapshot hỏng trên đường truyền tới 1 server
    Given file snapshot trên server "off03" bị hỏng 1 byte khi truyền
    When "feeds import" chạy trên "off03"
    Then "off03" báo "ERR-FEED-422-02" và bundle của "off03" không đổi
    And 7 server còn lại nhập thành công

  @AC-FLT-15 @security
  Scenario: Snapshot phân phối không chứa dữ liệu riêng
    Given máy trung tâm có cache OSV theo lockfile, "distro_fix" và đường dẫn site của chính nó
    When Operator phân phối snapshot
    Then gói gửi đi không chứa "cache/", "distro_fix", API key hay đường dẫn site của bất kỳ server nào

  @AC-FLT-18 @boundary
  Scenario Outline: Biên thời điểm snapshot và ngưỡng lỗi khi phân phối
    Given máy trung tâm xuất snapshot có "generated_at" = G = "2026-10-22T09:30:00Z" để phân phối tới 8 server nhóm "offline" với "batch_size" = 5 (canary "off01", đợt 2 "off02".."off06", đợt 3 "off07", "off08")
    And mọi server có "current/" với "generated_at" = "2026-10-15T06:00:00Z" và đồng hồ theo UTC chuẩn, trừ: <dieu_kien>
    When Operator chạy phân phối snapshot cho nhóm "offline"
    Then <ket_qua>

    # Kiểm tra khi nhập trên từng server: data-sources-cache-cli.md §4.3 ("generated_at" ≤ giờ của server + 1 giờ; không cũ hơn "current/")
    Examples:
      | dieu_kien                                                            | ket_qua                                                                                                                                   |
      | "current/" của "off02" có "generated_at" = G − 1 giây                | "off02" nhập snapshot và có "bundle_id" bằng máy trung tâm                                                                                |
      | "current/" của "off02" có "generated_at" = G                         | "off02" nhập snapshot (snapshot không cũ hơn "current/") và có "bundle_id" bằng máy trung tâm                                             |
      | "current/" của "off02" có "generated_at" = G + 1 giây                | "off02" từ chối với "ERR-FEED-409-02", "current/" của "off02" không đổi; đợt 3 vẫn được chạy                                              |
      | lúc chạy "feeds import", đồng hồ "off02" = G − 60 phút               | "off02" nhập snapshot ("generated_at" = giờ của server + 60 phút, bằng giới hạn)                                                          |
      | lúc chạy "feeds import", đồng hồ "off02" = G − 60 phút 1 giây        | "off02" từ chối với "ERR-FEED-422-02", "current/" của "off02" không đổi; đợt 3 vẫn được chạy                                              |
      | 1/5 server của đợt 2 ("off03") nhận gói hỏng 1 byte (20%)            | "off03" báo "ERR-FEED-422-02"; đợt 3 được chạy và 7/8 server nhập snapshot                                                                |
      | 2/5 server của đợt 2 ("off03", "off04") nhận gói hỏng 1 byte (40%)   | "fleet_run" "STOPPED" với "ERR-FLT-409-01" ("Đã dừng đợt 2: 2/5 server lỗi."); "off07", "off08" không nhận snapshot và "current/" không đổi |
```
