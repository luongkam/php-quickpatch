---
id: DOC-AC-QP-CON
title: Tiêu chí chấp nhận — module CON (web console Phase 1) — php-quickpatch v2
version: 1.0.2
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, console, auth, token, csrf, dns-rebinding, csp, sse, api]
depends_on:
  - DOC-AC-QP-000
  - DOC-US-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-API-QP-001
related_diagrams:
  - DIAG-SEQ-QP-AUTH-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận — module CON

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 60 scenario cho `US-CON-01..19` (`AC-CON-01..60`); hợp đồng request/response đối chiếu API `/api/v1` (DOC-API-QP-001) |
| 1.0.1 | 2026-10-22 | BA Agent | `AC-CON-31`: thêm Given 3 luồng SSE đang mở trong phiên; Then nêu rõ luồng thứ 4 trả 429 `ERR-JOB-429-02` (`job.sse.limit`) và 3 luồng đang mở không bị ngắt, khớp `TC-CON-031`, UC-JOB-001 bước 6b1, api-spec-jobs.md §4.3; thêm `ERR-JOB-429-02` vào tham chiếu `US-CON-10` |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review: (1) `AC-CON-06` khớp `BR-AUTH-003` (business-rules.md 1.0.1/1.1.0): token đúng gửi trước khi hết 60 s trả 200 và cấp phiên + `csrf_token` thay cho 429; thêm lần sai thứ 6 trong cùng 60 s vẫn trả 429 kèm `Retry-After` 1–60 và phản hồi ≤ 500 ms (api-spec.md §5 ma trận kiểm tra, dòng "Giới hạn thử sai không chặn token đúng"). (2) Đủ `@boundary` cho 19/19 story theo rule 08 và quy ước acceptance-criteria.md §1.1, §1.3: gắn thêm `@boundary` cho `AC-CON-04` (cổng 1023/32767/32768), `AC-CON-07` (phiên thứ 6), `AC-CON-13` (`--allow-local-port` lần 4), `AC-CON-57` (fuzz, chuỗi 300 ký tự); thêm 6 scenario `@boundary` mới: `AC-CON-61` (`US-CON-05`, Origin/Content-Type), `AC-CON-62` (`US-CON-07`, tuổi dữ liệu 168/169/2.160/2.161 giờ), `AC-CON-63` (`US-CON-11`, cache OSV 7 ngày), `AC-CON-64` (`US-CON-15`, khoảng lọc audit 0/366/367 ngày, from > to), `AC-CON-65` (`US-CON-16`, xác nhận dry-run 14:59/15:00/15:01), `AC-CON-66` (`US-CON-17`, tài nguyên tĩnh 500.000 byte qua tunnel 1 Mbit/s); tổng 66 scenario. Bổ sung mã tham chiếu tương ứng cho `US-CON-02`, `US-CON-07`, `US-CON-11`, `US-CON-15`. Cần cập nhật theo ở file khác: acceptance-criteria.md §1.3, §2 (60 → 66), §3; test-cases-con.md `TC-CON-006` KQ2 và TC mới cho `AC-CON-61..66` |

Ký hiệu dùng chung: [acceptance-criteria.md §1.2](acceptance-criteria.md). "Request ghi hợp lệ" = request `POST`/`PATCH`/`DELETE` có cookie `qp_session`, header `X-QP-CSRF` đúng, `Origin: http://127.0.0.1:17321`, `Content-Type: application/json`. Trình duyệt kiểm thử: 2 phiên bản gần nhất của Chrome, Edge, Firefox, Safari (`NFR-CMP-003`) mở qua `ssh -N -L 17321:127.0.0.1:17321`.

## Story: US-CON-01 - Khởi động serve và token 1 lần
Tham chiếu: `FR-CON-AUTH-001`, `FR-CON-AUTH-002` · `BR-CON-001`, `BR-CON-002`, `BR-CON-010`, `BR-AUTH-001`, `BR-AUTH-006`, `BR-JOB-005` · `ERR-CON-409-01`, `ERR-CON-409-02`, `ERR-CON-409-03`, `ERR-CON-412-01`, `ERR-CON-424-01` · `NFR-SEC-001`, `NFR-SEC-002`, `NFR-PERF-006`

```gherkin
Feature: US-CON-01 Khởi động serve và token 1 lần

  @AC-CON-01 @happy-path
  Scenario: Khởi động console trên cổng mặc định
    Given máy kiểm thử chuẩn, người vận hành ở terminal SSH có TTY, cổng 17321 trống
    When người vận hành chạy "php-quickpatch.sh serve"
    Then "ss -ltnp" cho thấy đúng 1 socket nghe "127.0.0.1:17321" và 0 socket trên địa chỉ khác hay IPv6
    And terminal in đúng 1 lần URL "http://127.0.0.1:17321/#t=<token 43 ký tự>" và lệnh "ssh -N -L 17321:127.0.0.1:17321 <user>@<host>"
    And "STATE_DIR/console/serve.pid" có quyền 0600, console sẵn sàng trong ≤ 3 s, RSS lúc rảnh ≤ 100 MB
    And audit có bản ghi "token issued" và chuỗi token xuất hiện 0 lần trong STATE_DIR, log, audit

  @AC-CON-02 @negative
  Scenario: Cổng đang bị chiếm
    Given cổng 17321 bị phiên serve cũ PID 3100 (cmdline chứa "qp-console.py") chiếm
    When người vận hành chạy "php-quickpatch.sh serve"
    Then lệnh báo "ERR-CON-409-01" ("Cổng 17321 đang được phiên console cũ (PID 3100) sử dụng.") và không dừng PID 3100
    And "serve --replace" gửi SIGTERM tới PID 3100, chờ 10 s, gửi SIGKILL nếu còn sống rồi khởi động phiên mới
    And khi cổng bị "nginx" PID 812 chiếm, lệnh báo "ERR-CON-409-02", mã thoát 2 và không thử cổng khác

  @AC-CON-03 @negative
  Scenario: Không có TTY hoặc Python quá cũ
    Given "serve" được khởi chạy bởi systemd không có TTY và không có "--token-file"
    When tiến trình khởi động
    Then tiến trình dừng với "ERR-CON-412-01" ("Không có terminal để in token; dùng --token-file.")
    And trên máy có Python 3.5, "serve" dừng với "ERR-CON-424-01" ("Console cần Python 3.6 trở lên (hiện có: 3.5).")

  @AC-CON-04 @security @boundary
  Scenario: Biên cổng, file token và dừng khi có job ghi
    Given máy kiểm thử chuẩn
    When người vận hành chạy "serve --port 1023", "serve --port 32768", "serve --port 32767 --token-file /root/qp.token"
    Then 2 lệnh đầu bị từ chối với mã thoát 2; lệnh thứ 3 nghe "127.0.0.1:32767" và tạo "/root/qp.token" quyền 0600
    And "serve --stop" khi có job ghi "RUNNING" báo "ERR-CON-409-03" và console dừng sau khi job kết thúc; "/root/qp.token" bị xoá khi dừng
    And không tuỳ chọn dòng lệnh nào cho phép bind địa chỉ khác "127.0.0.1"
```

## Story: US-CON-02 - Đăng nhập bằng token
Tham chiếu: `FR-CON-AUTH-003` · `BR-AUTH-002`, `BR-AUTH-003`, `BR-AUTH-004`, `BR-AUTH-005`, `BR-AUTH-006` · `ERR-AUTH-401-01`, `ERR-AUTH-429-01`, `ERR-AUTH-409-01` · `NFR-PERF-001` · SCR-001

```gherkin
Feature: US-CON-02 Đăng nhập bằng token

  @AC-CON-05 @happy-path
  Scenario: Đăng nhập bằng URL có fragment
    Given console đang chạy và người vận hành mở URL "http://127.0.0.1:17321/#t=<token>" qua tunnel
    When trang đăng nhập đọc fragment và gửi "POST /api/v1/sessions" với "{"token": "<token>"}"
    Then API trả 200 với "session_expires_at" và "csrf_token", kèm cookie "qp_session" có "HttpOnly", "SameSite=Strict", "Path=/", không có "Domain"
    And thanh địa chỉ không còn "#t=" sau "history.replaceState" và log truy cập của console không chứa token
    And audit có bản ghi đăng nhập thành công

  @AC-CON-06 @negative
  Scenario: Sai token 5 lần trong 60 s không chặn token đúng
    Given console đang chạy và có ít hơn 5 phiên đăng nhập hiệu lực
    When client gửi 5 lần "POST /api/v1/sessions" với token sai trong 40 s
    And trước khi hết 60 s kể từ lần sai thứ 5, client gửi 1 lần token đúng rồi 1 lần token sai (lần sai thứ 6)
    Then 4 lần sai đầu trả 401 "ERR-AUTH-401-01"; lần sai thứ 5 trả 429 "ERR-AUTH-429-01" ("Nhập sai token quá nhiều lần. Thử lại sau {retry_after} giây.") kèm header "Retry-After" 1–60
    And lần gửi token đúng trước khi hết 60 s trả 200, cấp cookie phiên và "csrf_token" (`BR-AUTH-003`: token đúng luôn được cấp phiên)
    And lần sai thứ 6 trong cùng 60 s vẫn trả 429 "ERR-AUTH-429-01" kèm "Retry-After" 1–60
    And mỗi phản hồi trả về trong ≤ 500 ms (máy chủ không chèn "sleep")

  @AC-CON-07 @security @boundary
  Scenario: Giới hạn phiên và lưu trữ phía trình duyệt
    Given đã có 5 phiên đăng nhập hiệu lực
    When client thứ 6 đăng nhập bằng token đúng
    Then API trả 409 "ERR-AUTH-409-01"
    And sau 50 lần đăng nhập sai trong 1 phiên serve, terminal của serve in 1 cảnh báo
    And "localStorage" và "sessionStorage" của trang không chứa token hay CSRF token

```

## Story: US-CON-03 - Xác thực request và hết hạn phiên
Tham chiếu: `FR-CON-AUTH-004` · `BR-AUTH-004`, `BR-AUTH-005` · `ERR-AUTH-401-01`, `ERR-AUTH-401-02` · `NFR-SEC-003`

```gherkin
Feature: US-CON-03 Xác thực request và hết hạn phiên

  @AC-CON-08 @happy-path
  Scenario: Cookie, Bearer và đăng xuất
    Given phiên console hợp lệ
    When trình duyệt gọi "GET /api/v1/overview" và curl gọi cùng endpoint với "Authorization: Bearer <token>"
    Then cả 2 request trả 200
    And sau "DELETE /api/v1/sessions/current", request tiếp theo dùng cookie cũ trả 401 "ERR-AUTH-401-01"

  @AC-CON-09 @negative
  Scenario: Thiếu thông tin xác thực
    Given console đang chạy
    When client gọi mọi endpoint trong danh mục API không kèm cookie hay Bearer, và gọi "GET /api/v1/overview?token=<token>"
    Then 100% endpoint trừ "GET /", "GET /login", "GET /static/*", "POST /api/v1/sessions" trả 401 "ERR-AUTH-401-01"
    And token truyền qua query string không được chấp nhận

  @AC-CON-10 @boundary
  Scenario Outline: Thời hạn phiên
    Given phiên đăng nhập lúc T0 và request cuối lúc T1
    When client gửi request lúc "<thoi_diem>"
    Then kết quả là "<ket_qua>"

    Examples:
      | thoi_diem                                      | ket_qua                                 |
      | T1 + 29 phút 59 s                              | 200                                     |
      | T1 + 30 phút 01 s                              | 401 ERR-AUTH-401-02 (lý do idle)        |
      | T0 + 12 giờ 00 phút 01 s, có request mỗi 5 phút | 401 ERR-AUTH-401-02 (lý do absolute)    |
      | sau khi "serve --stop" rồi "serve" lại          | 401 ERR-AUTH-401-01                     |
```

## Story: US-CON-04 - Chặn DNS rebinding bằng Host
Tham chiếu: `FR-CON-AUTH-005` · `BR-CON-003` · `ERR-CON-421-01`, `ERR-CON-400-01`, `ERR-CLI-400-01` · `NFR-SEC-004`

```gherkin
Feature: US-CON-04 Chặn DNS rebinding bằng Host

  @AC-CON-11 @happy-path
  Scenario Outline: Host hợp lệ
    Given console nghe cổng 17321
    When client gửi "GET /login" với header "Host: <host>"
    Then response có mã 200

    Examples:
      | host            |
      | 127.0.0.1:17321 |
      | localhost:17321 |
      | LOCALHOST:17321 |

  @AC-CON-12 @negative
  Scenario: DNS rebinding và thiếu Host
    Given phiên console hợp lệ
    When trang "http://evil.test:17321/" phân giải về 127.0.0.1 gửi "GET /api/v1/overview", "GET /static/app.js", "GET /api/v1/jobs/<job_id>/events" với "Host: evil.test:17321"
    Then cả 3 request trả 421 "ERR-CON-421-01" trước khi định tuyến và trước khi kiểm xác thực
    And request không có header Host trả 400 "ERR-CON-400-01"
    And dòng log của các request này không chứa giá trị Cookie hay Authorization

  @AC-CON-13 @security @boundary
  Scenario: Cổng cục bộ khai báo thêm
    Given "serve --allow-local-port 8080"
    When client gửi request với "Host: 127.0.0.1:8080" và với "Host: 127.0.0.1:17322"
    Then request "Host: 127.0.0.1:8080" được xử lý; request "Host: 127.0.0.1:17322" trả 421 "ERR-CON-421-01"
    And "serve" khai báo "--allow-local-port" 4 lần bị từ chối khi khởi động với "ERR-CLI-400-01"
```

## Story: US-CON-05 - Chống CSRF cho request ghi
Tham chiếu: `FR-CON-AUTH-006` · `BR-CON-004` · `ERR-AUTH-403-01`, `ERR-AUTH-403-02`, `ERR-CON-415-01` · `NFR-SEC-005`

```gherkin
Feature: US-CON-05 Chống CSRF cho request ghi

  @AC-CON-14 @happy-path
  Scenario: Request ghi hợp lệ
    Given phiên console hợp lệ
    When trình duyệt gửi "POST /api/v1/jobs" là request ghi hợp lệ tạo job "scan"
    Then API trả 202 với "job_id"

  @AC-CON-15 @negative
  Scenario Outline: Thiếu yếu tố chống CSRF
    Given phiên console hợp lệ
    When client gửi "POST /api/v1/jobs" bằng cookie với "<sai_lech>"
    Then API trả <http> "<loi>" và 0 job được tạo

    Examples:
      | sai_lech                               | http | loi             |
      | không có header X-QP-CSRF               | 403  | ERR-AUTH-403-01 |
      | X-QP-CSRF sai 1 ký tự                   | 403  | ERR-AUTH-403-01 |
      | Origin: https://evil.test               | 403  | ERR-AUTH-403-02 |
      | Content-Type: text/plain                | 415  | ERR-CON-415-01  |

  @AC-CON-16 @security
  Scenario: Bearer, CORS và GET không đổi trạng thái
    Given console đang chạy
    When curl gửi "POST /api/v1/jobs" chỉ với "Authorization: Bearer <token>" (không cookie), không có X-QP-CSRF
    Then API trả 202
    And mọi response, kể cả "OPTIONS", không có header "Access-Control-Allow-*"
    And mọi request "GET" trong bộ test không tạo job, không đổi trạng thái kế hoạch hay site

  @AC-CON-61 @boundary
  Scenario Outline: Biên danh sách Origin và Content-Type
    Given phiên console hợp lệ trên "serve --allow-local-port 8080" và không có job "scan" nào "QUEUED"/"RUNNING" trước mỗi lần gửi
    When client gửi "POST /api/v1/jobs" tạo job "scan" bằng cookie, header "X-QP-CSRF" đúng, "Origin" = "<origin>" và "Content-Type" = "<content_type>"
    Then kết quả là "<ket_qua>"

    Examples:
      | origin                         | content_type                     | ket_qua                                  |
      | http://127.0.0.1:17321         | application/json; charset=utf-8  | 202, 1 job được tạo                      |
      | http://localhost:17321         | application/json                 | 202, 1 job được tạo                      |
      | http://127.0.0.1:8080          | application/json                 | 202, 1 job được tạo (cổng khai báo)      |
      | http://127.0.0.1:17322         | application/json                 | 403 ERR-AUTH-403-02 (lệch 1 cổng), 0 job |
      | https://127.0.0.1:17321        | application/json                 | 403 ERR-AUTH-403-02 (khác scheme), 0 job |
      | (không gửi header Origin)      | application/json                 | 403 ERR-AUTH-403-02, 0 job               |
      | http://127.0.0.1:17321         | application/x-www-form-urlencoded | 415 ERR-CON-415-01, 0 job               |
```

## Story: US-CON-06 - Màn hình Tổng quan SCR-002
Tham chiếu: `FR-CON-OVW-001` · `BR-FEED-005`, `BR-SCN-049`, `BR-SCN-029` · `ERR-HC-500-01`, `ERR-FEED-412-01` · `NFR-PERF-001`, `NFR-PERF-007`, `NFR-REL-001`, `NFR-USE-003`, `NFR-USE-004`

```gherkin
Feature: US-CON-06 Màn hình Tổng quan SCR-002

  @AC-CON-17 @happy-path
  Scenario: Tổng quan máy chủ
    Given phiên console hợp lệ, "last-scan.json" tạo 3 giờ trước với 4 runtime (1 "ok", 1 "ok-backport", 1 "vulnerable", 1 "eol") và 1 runtime còn 70 ngày tới EOL
    When người vận hành mở SCR-002 qua tunnel 1 Mbit/s, RTT 100 ms
    Then màn hình hiển thị số runtime theo từng trạng thái, số runtime EOL ≤ 90 ngày, số finding KEV/Critical, số dependency có lỗ hổng
    And hiển thị tuổi dữ liệu và lỗi của từng nguồn, hạn duyệt kế hoạch, danh sách xếp hạng, nút "Đồng bộ dữ liệu"
    And SCR-002 hiển thị xong trong ≤ 2 s; "GET /api/v1/overview" đạt P95 ≤ 500 ms với 5 phiên × 2 request/giây

  @AC-CON-18 @negative
  Scenario: Có lượt chuyển lỗi và dữ liệu cũ
    Given site "shop.test" có lượt chuyển ở "HC_FAILED_KEPT" và bundle có "data_age_h" = 200
    When người vận hành mở SCR-002
    Then đầu trang có dải cảnh báo "ERR-HC-500-01" cho "shop.test" kèm nút rollback
    And có dải cảnh báo "ERR-FEED-412-01" nêu nguồn cũ nhất

  @AC-CON-19 @boundary
  Scenario Outline: Tuổi kết quả scan, dịch vụ dừng và bố cục
    Given "<dieu_kien>"
    When người vận hành mở SCR-002
    Then "<ket_qua>"

    Examples:
      | dieu_kien                                        | ket_qua                                         |
      | last-scan.json tạo 24 giờ trước                  | không hiển thị nút "Quét lại"                   |
      | last-scan.json tạo 24 giờ 01 phút trước          | hiển thị nút "Quét lại"                         |
      | PHP-FPM, Node.js và web server đều dừng           | 10/10 màn hình console vẫn mở được              |
      | cửa sổ trình duyệt rộng 360 px                    | không có thanh cuộn ngang, mọi nút dùng được bằng bàn phím |
```

## Story: US-CON-07 - Màn hình Đánh giá runtime SCR-003
Tham chiếu: `FR-CON-ASMT-001` · `BR-ASMT-003`, `BR-CON-010`, `BR-FEED-005` · `ERR-ASMT-404-01`, `ERR-FEED-412-01`, `ERR-SCN-503-01` · `NFR-USE-001`, `NFR-SEC-009`

```gherkin
Feature: US-CON-07 Màn hình Đánh giá runtime SCR-003

  @AC-CON-20 @happy-path
  Scenario: Vá cùng nhánh trong 3 thao tác
    Given phiên console hợp lệ, "serve" chạy root, runtime PHP 8.2.34 có 2 CVE Critical
    When người vận hành mở SCR-003 của runtime
    Then danh sách CVE hiển thị mã, CVSS, mức, KEV, nguồn, ngày công bố, bản sửa; bảng so sánh hiển thị "R", "ΔR", "bundle_id", tuổi dữ liệu, "catalog_version"
    And chuỗi thao tác (1) chọn runtime, (2) bấm "Vá cùng nhánh" mở SCR-011 với kết quả dry-run, (3) bấm xác nhận tạo job "fix" — tổng 3 thao tác

  @AC-CON-21 @negative
  Scenario: Runtime không còn trong kết quả scan
    Given URL SCR-003 trỏ "runtime_id" = "php:0123456789ab" không có trong scan gần nhất
    When người vận hành mở URL
    Then màn hình hiển thị lỗi "ERR-ASMT-404-01" ("Không tìm thấy runtime php:0123456789ab; hãy quét lại.") kèm nút "Quét lại"

  @AC-CON-22 @security
  Scenario: Dữ liệu độc hại hiển thị dạng văn bản và quyền không root
    Given mô tả 1 advisory chứa "<img src=x onerror=alert(1)>" và "serve" chạy với EUID 1001
    When người vận hành mở SCR-003
    Then chuỗi được hiển thị nguyên văn bằng "textContent", không có script nào chạy và 0 vi phạm CSP
    And nút "Vá cùng nhánh" bị vô hiệu kèm lý do "cần root"

  @AC-CON-62 @boundary
  Scenario Outline: Ngưỡng tuổi dữ liệu trên SCR-003
    Given phiên console hợp lệ, "serve" chạy root, kết quả "assess" mới nhất của runtime "php:3f2a9c1e0b7d" có "meta.feed.data_age_h" = <tuoi_h>, mọi nguồn dùng cho kết quả có TTL ≤ 24 giờ, và ứng viên "8.5.12" khác nhánh có "selectable" = true khi bỏ qua tuổi dữ liệu
    When người vận hành mở SCR-003 của runtime
    Then "meta.feed.freshness" = "<muc>" và màn hình hiển thị "<ket_qua>"

    Examples:
      | tuoi_h | muc     | ket_qua                                                                                                                         |
      | 168    | AGING   | dòng "Dữ liệu cũ 168 giờ", không có dải "ERR-FEED-412-01"; ứng viên khác nhánh vẫn chọn được                                   |
      | 169    | STALE   | dải cảnh báo "ERR-FEED-412-01" nêu nguồn cũ nhất; ứng viên khác nhánh vẫn chọn được                                            |
      | 2160   | STALE   | dải cảnh báo "ERR-FEED-412-01"; ứng viên khác nhánh vẫn chọn được                                                              |
      | 2161   | EXPIRED | dải "ERR-SCN-503-01"; mọi ứng viên khác nhánh có "not_selectable_reason" = "DATA_EXPIRED"; chỉ nút "Vá cùng nhánh" còn dùng được |
```

## Story: US-CON-08 - Sinh kế hoạch trên SCR-004
Tham chiếu: `FR-CON-PLAN-001` · `BR-PLAN-001` · `ERR-PLAN-409-01`, `ERR-PLAN-422-01` · `NFR-USE-002`

```gherkin
Feature: US-CON-08 Sinh kế hoạch trên SCR-004

  @AC-CON-23 @happy-path
  Scenario: Từ Tổng quan tới checklist trong 4 thao tác
    Given phiên console hợp lệ ở SCR-002
    When người vận hành (1) chọn runtime PHP 8.2.34, (2) chọn đích "8.5.12", (3) bấm "Sinh kế hoạch", (4) mở checklist
    Then "POST /api/v1/plans" trả 202 với "job_id" và tiến độ job hiển thị qua SSE
    And checklist của kế hoạch "draft" hiển thị sau đúng 4 thao tác, không có bước gõ lệnh

  @AC-CON-24 @negative
  Scenario: Runtime đã có kế hoạch đang thực hiện
    Given runtime có kế hoạch "in_progress"
    When người vận hành bấm "Sinh kế hoạch"
    Then màn hình hiển thị "ERR-PLAN-409-01" kèm liên kết tới kế hoạch đang thực hiện

  @AC-CON-25 @boundary
  Scenario Outline: Lý do khi chọn đích khác đề xuất
    Given người vận hành chọn đích "8.4.27" (không mang loại "RECOMMENDED")
    When người vận hành nhập lý do dài <n> ký tự và bấm "Sinh kế hoạch"
    Then kết quả là "<ket_qua>"

    Examples:
      | n  | ket_qua                                          |
      | 19 | API trả 422 "ERR-PLAN-422-01", không tạo kế hoạch |
      | 20 | API trả 202, kế hoạch hiển thị lý do              |
```

## Story: US-CON-09 - Thao tác checklist trên SCR-004
Tham chiếu: `FR-CON-PLAN-002` · `BR-SCN-018`, `BR-PLAN-003`, `BR-PLAN-005`, `BR-ENV-010` · `ERR-SCN-424-01`, `ERR-PLAN-422-01`

```gherkin
Feature: US-CON-09 Thao tác checklist trên SCR-004

  @AC-CON-26 @happy-path
  Scenario: Điều phối kế hoạch trên 1 màn hình
    Given phiên console hợp lệ và kế hoạch "draft" có 3 site
    When người vận hành lọc giai đoạn "P4", site "b.test", trạng thái "PENDING", đánh dấu 1 mục MANUAL "DONE" kèm bằng chứng 32 ký tự, đổi canary sang "b.test", khai báo 2 "hc_url" rồi bấm "Duyệt"
    Then danh sách lọc chỉ chứa mục khớp cả 3 điều kiện
    And mục MANUAL chuyển "DONE", canary là "b.test", 2 "hc_url" được lưu, kế hoạch chuyển "approved"; mỗi thao tác có 1 bản ghi audit

  @AC-CON-27 @negative
  Scenario: Mục bị chặn bởi phụ thuộc và lý do ngắn
    Given mục P5 của "a.test" phụ thuộc mục P3 "CHK-PHP-010-12" còn "PENDING"
    When người vận hành bấm chạy mục P5 rồi miễn trừ 1 mục khác với lý do 12 ký tự
    Then lần chạy bị từ chối với "ERR-SCN-424-01" nêu "CHK-PHP-010-12"
    And lần miễn trừ bị từ chối với "ERR-PLAN-422-01"

  @AC-CON-28 @boundary
  Scenario: Hiển thị trạng thái và nhãn
    Given checklist có 1 mục "verified" = false, 1 mục "PENDING" có phụ thuộc chưa đạt, 1 mục "FAILED"
    When người vận hành mở checklist
    Then mục "verified" = false có nhãn "chưa kiểm chứng" và không có nút chạy ở mức AUTO
    And 2 mục còn lại hiển thị là "blocked" kèm danh sách mục phụ thuộc hoặc "job_id" thất bại
```

## Story: US-CON-10 - Jobs & Log SCR-006 và huỷ job
Tham chiếu: `FR-CON-JOB-001`, `FR-CON-JOB-002` · `BR-JOB-004`, `BR-JOB-007` · `ERR-JOB-423-01`, `ERR-JOB-404-01`, `ERR-JOB-410-01`, `ERR-JOB-429-02` (định nghĩa ở [error-matrix.md](../srs/error-matrix.md) v1.0.1) · `NFR-PERF-003`

```gherkin
Feature: US-CON-10 Jobs & Log SCR-006 và huỷ job

  @AC-CON-29 @happy-path
  Scenario: Theo dõi log trực tiếp và huỷ job đang chờ
    Given phiên console hợp lệ, 1 job "fix" "RUNNING" và 1 job "scan" "QUEUED"
    When người vận hành mở SCR-006, lọc loại "write", mở job "fix", rồi huỷ job "scan"
    Then dòng log mới của job "fix" hiển thị ≤ 2 s sau khi CLI ghi
    And khi job "fix" kết thúc, màn hình hiển thị "result.json"; job "scan" chuyển "CANCELLED"

  @AC-CON-30 @negative
  Scenario: Huỷ job ghi trong vùng tới hạn và job không tồn tại
    Given job "migrate_switch" đang ở "phase" = "CHANGING"
    When người vận hành bấm huỷ job
    Then API trả 423 "ERR-JOB-423-01" ("Job đang áp dụng thay đổi (CHANGING); không thể huỷ lúc này.") và job tiếp tục chạy
    And mở "JOB-20261022-000000-ffff" (không tồn tại) hiển thị "ERR-JOB-404-01"

  @AC-CON-31 @boundary
  Scenario: Log đã bị dọn và giới hạn luồng SSE
    Given job ghi kết thúc 31 ngày trước và "output.log" đã bị dọn
    And trong cùng phiên, 3 tab SCR-006 đang giữ 3 luồng SSE tới 1 job "fix" "RUNNING"
    When người vận hành mở job đã bị dọn log
    And mở luồng log thứ 4 (tab SCR-006 thứ 4 tới job "fix") trong cùng phiên
    Then phần log hiển thị "ERR-JOB-410-01", "job.json" và "result.json" vẫn xem được
    And "GET /api/v1/jobs/{job_id}/events" lần thứ 4 của phiên trả 429 "ERR-JOB-429-02" với "localization_key" = "job.sse.limit" (tối đa 3 luồng/phiên)
    And 3 luồng đang mở vẫn nhận sự kiện và trình duyệt không tự nối lại luồng bị từ chối
```

## Story: US-CON-11 - Findings thư viện SCR-005
Tham chiếu: `FR-CON-DEP-001`, `FR-FEED-OSV-001` · `BR-ASMT-005`, `BR-SEC-004`, `BR-CON-008` · `ERR-FEED-503-02`, `ERR-CON-422-01`

```gherkin
Feature: US-CON-11 Findings thư viện SCR-005

  @AC-CON-32 @happy-path
  Scenario: Vá dự án Composer từ console
    Given phiên console hợp lệ và dự án "/var/www/shop.test" có 3 finding Composer
    When người vận hành mở SCR-005, bấm "Vá dự án", xem dry-run rồi xác nhận
    Then bảng nhóm theo dự án hiển thị hệ sinh thái, package, phiên bản, advisory, mức, KEV, "MAL-*", bản sửa
    And job "fix" được tạo với "--only composer --path /var/www/shop.test"

  @AC-CON-33 @negative
  Scenario: Lockfile không tra được OSV
    Given lockfile của dự án "/var/www/api.test" bị bỏ qua do OSV lỗi và không có cache 7 ngày
    When người vận hành mở SCR-005
    Then dòng của dự án hiển thị "ERR-FEED-503-02" thay cho danh sách finding

  @AC-CON-34 @security
  Scenario: Đường dẫn ngoài danh sách dự án, yarn/pnpm và mã độc
    Given dự án "/var/www/web.test" chỉ có "yarn.lock" và 1 dự án có package "MAL-2026-0001"
    When client gửi "POST /api/v1/jobs" action "fix" với "path" = "/etc"
    Then API trả 422 "ERR-CON-422-01" vì "/etc" không thuộc "projects[].dir"
    And SCR-005 hiển thị cảnh báo kèm lệnh "yarn npm audit" cho "/var/www/web.test" và finding mã độc mức Critical kèm khuyến nghị xoay vòng secret

  @AC-CON-63 @boundary
  Scenario Outline: Tuổi cache OSV khi OSV không truy cập được
    Given phiên console hợp lệ, OSV ("SRC-007") không truy cập được sau 3 lần thử ở lượt "scan" gần nhất
    And kết quả OSV trong cache cho lockfile "/var/www/shop.test/composer.lock" có "osv_fetched_at" cách thời điểm "scan" <tuoi_cache>
    When người vận hành mở SCR-005
    Then dòng của dự án "/var/www/shop.test" hiển thị "<ket_qua>"

    Examples:
      | tuoi_cache          | ket_qua                                                                        |
      | 7 ngày 00 giờ 00 phút | danh sách finding lấy từ cache kèm tuổi dữ liệu 168 giờ, không có "ERR-FEED-503-02" |
      | 7 ngày 00 giờ 01 phút | "ERR-FEED-503-02" thay cho danh sách finding                                   |
```

## Story: US-CON-12 - Rollback & lịch sử SCR-007
Tham chiếu: `FR-CON-RBK-001` · `BR-PTCH-008`, `BR-SCN-014` · `ERR-PTCH-404-01`, `ERR-ENV-410-01` · `NFR-ENV-02`

```gherkin
Feature: US-CON-12 Rollback & lịch sử SCR-007

  @AC-CON-35 @happy-path
  Scenario: Rollback site bằng 1 nút và 1 xác nhận
    Given phiên console hợp lệ và "shop.test" có lượt chuyển "20261021-143000" "PASSED"
    When người vận hành mở SCR-007, chọn lượt, bấm "Rollback" rồi xác nhận 1 lần sau khi xem danh sách hành động sẽ phát lại
    Then job "migrate_rollback" được tạo và site trở về 8.2 trong ≤ 60 s

  @AC-CON-36 @negative
  Scenario: Lượt backup không còn hoặc runtime cũ đã gỡ
    Given thư mục "backups/20261001-080000" đã bị xoá ngoài tool
    When người vận hành chọn rollback lượt "20261001-080000"
    Then màn hình hiển thị "ERR-PTCH-404-01"
    And với lượt chuyển mà PHP 8.2 đã bị gỡ, nút "Rollback" bị vô hiệu kèm cảnh báo "runtime cũ đã gỡ" ("ERR-ENV-410-01")

  @AC-CON-37 @boundary
  Scenario: Danh sách phát lại và cảnh báo gói
    Given lượt "20261022-104201" có 7 dòng manifest gồm 1 dòng "note" nâng gói
    When người vận hành mở xem trước rollback
    Then màn hình liệt kê đúng 7 dòng theo thứ tự ngược với thứ tự ghi
    And hiển thị cảnh báo "gói đã nâng không bị hạ cấp"
```

## Story: US-CON-13 - Nguồn dữ liệu SCR-008 và nhập snapshot
Tham chiếu: `FR-CON-FEED-001`, `FR-CON-FEED-002` · `BR-FEED-005`, `BR-FEED-055`, `BR-FEED-059`, `BR-CON-009` · `ERR-FEED-423-01`, `ERR-FEED-422-02`, `ERR-FEED-409-02`, `ERR-CON-413-01`

```gherkin
Feature: US-CON-13 Nguồn dữ liệu SCR-008 và nhập snapshot

  @AC-CON-38 @happy-path
  Scenario: Xem nguồn và đồng bộ ngay
    Given phiên console hợp lệ
    When người vận hành mở SCR-008 và bấm "Đồng bộ ngay"
    Then bảng hiển thị mỗi nguồn: trạng thái, lần lấy thành công, tuổi, TTL, số bản ghi, lỗi cuối, "data_origin"; độ tươi tổng và lịch đồng bộ
    And job loại "data" "feeds_update" được tạo và tiến độ hiển thị trên màn hình

  @AC-CON-39 @happy-path
  Scenario: Tải lên snapshot cho máy không ra Internet
    Given file snapshot 2,8 MB và SHA-256 64 ký tự hex của file
    When người vận hành tải lên file kèm SHA-256 trên SCR-008
    Then file được lưu tạm tại "STATE_DIR/work/upload-<job_id>.tar.gz" quyền 0600 và job "feeds import" chạy
    And bundle mới hiển thị trên SCR-008 và file tạm bị xoá khi job kết thúc

  @AC-CON-40 @negative
  Scenario Outline: Đồng bộ hoặc nhập không thành công
    Given "<dieu_kien>"
    When người vận hành thực hiện thao tác trên SCR-008
    Then màn hình hiển thị "<loi>" và bundle hiện tại không đổi

    Examples:
      | dieu_kien                                   | loi             |
      | lượt "feeds update" khác giữ khoá > 30 s     | ERR-FEED-423-01 |
      | SHA-256 nhập khác SHA-256 thật của file      | ERR-FEED-422-02 |
      | snapshot cũ hơn bundle hiện tại              | ERR-FEED-409-02 |

  @AC-CON-41 @boundary
  Scenario Outline: Giới hạn kích thước tải lên
    Given file snapshot có kích thước <kich_thuoc>
    When người vận hành tải lên file
    Then kết quả là "<ket_qua>" và không file tạm nào còn lại sau đó

    Examples:
      | kich_thuoc                | ket_qua                           |
      | 20.971.520 byte (20 MiB)  | chấp nhận, chạy job "feeds import" |
      | 20.971.521 byte           | 413 ERR-CON-413-01                |
```

## Story: US-CON-14 - Site & ánh xạ runtime SCR-009
Tham chiếu: `FR-CON-SITE-001` · `BR-HC-001`, `BR-HC-002`, `BR-ENV-003` · `ERR-HC-422-02`

```gherkin
Feature: US-CON-14 Site & ánh xạ runtime SCR-009

  @AC-CON-42 @happy-path
  Scenario: Bảng site và khai báo URL kiểm tra
    Given phiên console hợp lệ và máy có 40 site
    When người vận hành mở SCR-009 và gửi "PATCH /api/v1/sites/shop.test" với 3 "hc_url" cùng host
    Then bảng hiển thị mỗi site: playbook, kiểu gán, nhánh hiện tại, binary, kết luận tương thích, lượt chuyển gần nhất, cảnh báo thay đổi ngoài tool
    And 3 "hc_url" được lưu và audit ghi thay đổi "hc_url"

  @AC-CON-43 @negative
  Scenario: URL khác host
    Given phiên console hợp lệ
    When người vận hành khai báo "hc_url" = "https://other.test/api" cho "shop.test"
    Then API trả 422 với "ERR-HC-422-02" ("URL kiểm tra https://other.test/api bị bỏ qua: …") và danh sách "hc_url" không đổi

  @AC-CON-44 @boundary
  Scenario: Số URL tối đa và nút chuyển site
    Given "a.test" đang "HC_RUNNING"
    When người vận hành khai báo đúng 10 "hc_url" cho "b.test" rồi mở dòng "b.test"
    Then 10 URL được lưu; khai báo URL thứ 11 trả "ERR-HC-422-02"
    And nút "Chuyển" của "b.test" bị vô hiệu kèm lý do "a.test đang kiểm tra sau chuyển"
```

## Story: US-CON-15 - Audit & báo cáo SCR-010
Tham chiếu: `FR-CON-AUD-001`, `FR-JOB-AUD-003` · `BR-AUD-002`, `BR-RPT-001` · `ERR-AUD-409-01`, `ERR-CON-405-01`, `ERR-CON-422-01`

```gherkin
Feature: US-CON-15 Audit & báo cáo SCR-010

  @AC-CON-45 @happy-path
  Scenario: Lọc audit, kiểm chuỗi và tải báo cáo
    Given phiên console hợp lệ và audit có 1.240 bản ghi
    When kiểm toán viên lọc theo actor "console:root" và hành động "migrate_switch", bấm "Kiểm tra chuỗi hash", rồi tạo báo cáo "evidence" định dạng "html"
    Then danh sách phân trang mặc định 20 bản ghi/trang và chỉ có bản ghi khớp bộ lọc
    And kết quả kiểm tra hiển thị "verified" = true và số bản ghi đã kiểm
    And file báo cáo tải về được qua "GET /api/v1/reports/{report_id}"

  @AC-CON-46 @negative
  Scenario: Chuỗi hash bị đứt
    Given bản ghi "seq" = 877 bị sửa ngoài tool
    When kiểm toán viên bấm "Kiểm tra chuỗi hash"
    Then màn hình hiển thị "ERR-AUD-409-01" ("Nhật ký kiểm toán bị thay đổi từ bản ghi #877.")

  @AC-CON-47 @security
  Scenario: Không có thao tác sửa hay xoá audit
    Given phiên console hợp lệ
    When client gửi "PATCH /api/v1/audit-events" và "DELETE /api/v1/audit-events"
    Then cả 2 request trả 405 "ERR-CON-405-01" và file audit giữ nguyên SHA-256
    And SCR-010 không có nút sửa hay xoá bản ghi

  @AC-CON-64 @boundary
  Scenario Outline: Khoảng thời gian lọc audit
    Given phiên console hợp lệ và audit có bản ghi từ 2025-10-20 tới 2026-10-22
    When kiểm toán viên lọc SCR-010 từ "<from>" tới "<to>" (gửi "GET /api/v1/audit-events?from=<from>&to=<to>")
    Then kết quả là "<ket_qua>"

    Examples:
      | from       | to         | ket_qua                                                                                      |
      | 2026-10-22 | 2026-10-22 | 200, chỉ gồm bản ghi có "ts" thuộc ngày 2026-10-22 UTC (from = to, to − from = 0 ngày)     |
      | 2025-10-21 | 2026-10-22 | 200, danh sách sắp theo "seq" giảm dần (to − from = 366 ngày)                               |
      | 2025-10-20 | 2026-10-22 | 422 ERR-CON-422-01 (to − from = 367 ngày), danh sách đang hiển thị không đổi                |
      | 2026-10-22 | 2026-10-21 | 422 ERR-CON-422-01 (from > to 1 ngày), danh sách đang hiển thị không đổi                    |
```

## Story: US-CON-16 - Dry-run và xác nhận SCR-011
Tham chiếu: `FR-CON-SAFE-001` · `BR-CON-005`, `BR-CON-006` · `ERR-JOB-428-01` · `NFR-USE-006`

```gherkin
Feature: US-CON-16 Dry-run và xác nhận SCR-011

  @AC-CON-48 @happy-path
  Scenario: Xem trước đủ 4 mục và xác nhận trong 15 phút
    Given phiên console hợp lệ và runtime PHP 8.2.34 "vulnerable"
    When người vận hành bấm "Vá cùng nhánh"
    Then 1 job "dry_run" = true chạy và SCR-011 hiển thị 4/4 mục: thay đổi (file sẽ đổi, gói sẽ nâng, dịch vụ sẽ reload/restart), đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác
    And khi người vận hành xác nhận sau 4 phút, job ghi được tạo với "confirm_dry_run_job_id" bằng mã job dry-run

  @AC-CON-49 @negative
  Scenario Outline: Dry-run không còn hợp lệ
    Given job dry-run "SUCCEEDED" của hành động "fix"
    When người vận hành xác nhận với điều kiện "<dieu_kien>"
    Then API trả 428 "ERR-JOB-428-01" với "details.constraint" = "<constraint>" và 0 job ghi được tạo

    Examples:
      | dieu_kien                                   | constraint      |
      | xác nhận sau 15 phút 01 s                    | expired         |
      | xác nhận từ phiên đăng nhập khác             | other_session   |
      | "params" khác với lúc dry-run                | params_mismatch |

  @AC-CON-50 @negative
  Scenario: Hiện trạng thay đổi giữa dry-run và xác nhận
    Given job dry-run "SUCCEEDED" lúc 10:00 với "bundle_id" "b-20261022T093000Z-3f2a9c1e"
    And lúc 10:05 một lượt "feeds update" tạo "bundle_id" mới
    When người vận hành xác nhận lúc 10:06
    Then API trả 428 "ERR-JOB-428-01" với "details.constraint" = "fingerprint_changed"

  @AC-CON-51 @security
  Scenario: Xác nhận kép cho thao tác không hoàn tác được
    Given người vận hành chuẩn bị chạy "migrate_switch" cho "shop.test" với "no_auto_rollback" = true
    When người vận hành xác nhận với "confirm_retype" = "shop.tes"
    Then API trả 428 "ERR-JOB-428-01" với "details.constraint" = "retype_mismatch"
    And với "confirm_retype" = "shop.test", job được tạo và audit ghi cả bước xác nhận thường và bước gõ lại

  @AC-CON-65 @boundary
  Scenario Outline: Biên 15 phút của dry-run khi xác nhận
    Given job dry-run "SUCCEEDED" của hành động "fix" trong cùng phiên, "bundle_id" và "scan_fingerprint" không đổi tới lúc xác nhận
    And đồng hồ của máy kiểm thử được điều khiển để thời điểm xác nhận = "created_at" của job dry-run + <khoang>
    When người vận hành bấm xác nhận trên SCR-011
    Then kết quả là "<ket_qua>"

    Examples:
      | khoang          | ket_qua                                                                        |
      | 14 phút 59 s    | 202, 1 job ghi được tạo với "confirm_dry_run_job_id" bằng mã job dry-run       |
      | 15 phút 00 s    | 202, 1 job ghi được tạo                                                        |
      | 15 phút 01 s    | 428 ERR-JOB-428-01, "details.constraint" = "expired", 0 job ghi được tạo       |
```

## Story: US-CON-17 - Tài nguyên tĩnh và header bảo mật
Tham chiếu: `FR-CON-SAFE-002` · `BR-CON-007` · `ERR-CON-404-01` · `NFR-SEC-006`, `NFR-PERF-007`

```gherkin
Feature: US-CON-17 Tài nguyên tĩnh và header bảo mật

  @AC-CON-52 @happy-path
  Scenario: Header bảo mật trên mọi phản hồi
    Given console đang chạy
    When client gọi "GET /", mọi file trong "/static/" và "GET /api/v1/overview"
    Then mọi phản hồi có "Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    And có "X-Content-Type-Options: nosniff", "Referrer-Policy: no-referrer", "X-Frame-Options: DENY", "Cross-Origin-Opener-Policy: same-origin", "Cross-Origin-Resource-Policy: same-origin"
    And phản hồi API có "Cache-Control: no-store"; tổng dung lượng tài nguyên tĩnh ≤ 500 KB

  @AC-CON-53 @negative
  Scenario: Đường dẫn tĩnh không có trong bảng ánh xạ
    Given console đang chạy
    When client gọi "GET /static/../../etc/passwd", "GET /static/%2e%2e/serve.pid", "GET /static/", "GET /static/unknown.js"
    Then cả 4 request trả 404 "ERR-CON-404-01" và không phản hồi nào liệt kê thư mục hay chứa nội dung file ngoài bảng ánh xạ

  @AC-CON-54 @security
  Scenario: 0 vi phạm CSP và 0 request ra ngoài trên 10 màn hình
    Given trình duyệt kiểm thử ghi nhận báo cáo CSP và nhật ký mạng
    When người vận hành mở lần lượt SCR-001 tới SCR-010 và mở SCR-011
    Then số vi phạm CSP = 0 và số request tới origin khác "http://127.0.0.1:17321" = 0
    And mã nguồn tĩnh không có script/style inline và không gọi "eval"

  @AC-CON-66 @boundary
  Scenario: Tài nguyên tĩnh tại giới hạn 500 KB qua tunnel chậm
    Given bản dựng kiểm thử có tổng kích thước chưa nén của mọi file trong bảng ánh xạ tĩnh đúng 500.000 byte (bằng giới hạn của "NFR-PERF-007")
    And trình duyệt kiểm thử không có cache, điều tiết mạng 1 Mbit/s, RTT 100 ms, gửi "Accept-Encoding: gzip"
    When người vận hành mở SCR-002 lần đầu rồi tải lại trang
    Then ở lần mở đầu, mọi phản hồi "/static/*" có "Content-Encoding: gzip" và SCR-002 hiển thị đủ dữ liệu trong ≤ 2 s
    And ở lần tải lại, trình duyệt gửi "If-None-Match" và nhận 304 cho 100% file tĩnh không đổi (ETag/304 là đề xuất của api-spec-core.md §7)
    And mọi phản hồi 200 và 304 có đủ header của "BR-CON-007"
```

## Story: US-CON-18 - Danh sách trắng lệnh
Tham chiếu: `FR-CON-SAFE-003` · `BR-CON-008`, `BR-JOB-003` · `ERR-CON-422-01` · `NFR-SEC-007`, `NFR-SEC-008`

```gherkin
Feature: US-CON-18 Danh sách trắng lệnh

  @AC-CON-55 @happy-path
  Scenario: Dựng argv cố định cho hành động fix dry-run
    Given phiên console hợp lệ
    When client gửi "POST /api/v1/jobs" với "action" = "fix", "params" = {"only": ["php"]}, "dry_run" = true
    Then tiến trình con được tạo bằng argv ["<script tuyệt đối>", "fix", "--json", "--only", "php", "--dry-run"] với "shell=False", stdin "DEVNULL", "close_fds=True", "start_new_session=True", "cwd" = STATE_DIR
    And biến môi trường của tiến trình con chỉ gồm "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG=C.UTF-8", "HOME", "QP_JOB_ID", "QP_ACTOR" (và "QP_*_KEY"/"QP_*_TOKEN" khi được cấu hình)

  @AC-CON-56 @negative
  Scenario: Tham số chèn lệnh
    Given phiên console hợp lệ
    When client gửi action "migrate_switch" với "site_id" = "shop.test; rm -rf /" và action "shell" với "cmd" = "id"
    Then cả 2 request trả 422 "ERR-CON-422-01"; log ghi "field" nhưng không ghi giá trị tham số
    And 0 tiến trình con được tạo

  @AC-CON-57 @security @boundary
  Scenario: Fuzz 1.000 giá trị tham số
    Given bộ 1.000 giá trị gồm chuỗi bắt đầu bằng "-", "$(id)", dấu backtick, ký tự xuống dòng, "../", chuỗi 300 ký tự
    When client gửi lần lượt các giá trị vào "site_id", "plan_id", "runtime_id", "chk_id", "target"
    Then 100% request không khớp regex/enum trả 422 "ERR-CON-422-01" và 0 tiến trình con được tạo
    And phân tích tĩnh mã Python cho 0 lần dùng "shell=True", "os.system", "os.popen", "eval", "exec"
```

## Story: US-CON-19 - Hợp đồng API /api/v1
Tham chiếu: `FR-CON-API-001` · `BR-CON-009` · `ERR-CON-404-01`, `ERR-CON-405-01`, `ERR-CON-413-01`, `ERR-CON-415-01`, `ERR-CON-422-01`, `ERR-CON-500-01`, `ERR-CON-503-01` · `NFR-PERF-001`, `NFR-PERF-002`, `NFR-USE-005`

```gherkin
Feature: US-CON-19 Hợp đồng API /api/v1

  @AC-CON-58 @happy-path
  Scenario: Envelope và phân trang
    Given phiên console hợp lệ và 130 job
    When client gọi "GET /api/v1/jobs?page=2&limit=50"
    Then response "Content-Type: application/json" có các khoá "success" = true, "data" (50 phần tử), "error" = null, "meta" ("page" = 2, "limit" = 50, "total" = 130), "timestamp"
    And API đọc đạt P95 ≤ 500 ms; "POST /api/v1/jobs" trả "job_id" với P95 ≤ 1.500 ms

  @AC-CON-59 @negative
  Scenario: Lỗi nội bộ, console đang dừng và phương thức sai
    Given lỗi giả lập trong handler "GET /api/v1/overview"
    When client gọi endpoint đó
    Then API trả 500 "ERR-CON-500-01" với mã tham chiếu, "localization_key" = "con.internal" và body không có stack trace
    And khi console đang dừng, request mới trả 503 "ERR-CON-503-01"; "PUT /api/v1/overview" trả 405 "ERR-CON-405-01"

  @AC-CON-60 @boundary
  Scenario Outline: Giới hạn kích thước và tham số phân trang
    Given phiên console hợp lệ
    When client gửi "<request>"
    Then kết quả là "<ket_qua>"

    Examples:
      | request                                     | ket_qua                   |
      | body JSON 65.536 byte (64 KiB)               | xử lý bình thường         |
      | body JSON 65.537 byte                        | 413 ERR-CON-413-01        |
      | header tổng 8.193 byte                       | 413 ERR-CON-413-01        |
      | GET /api/v1/jobs?limit=201                   | 422 ERR-CON-422-01        |
      | GET /api/v1/jobs?page=0                      | 422 ERR-CON-422-01        |
```
