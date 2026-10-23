---
id: DOC-SRS-QP-NFR-001
title: Yêu cầu phi chức năng (NFR) — php-quickpatch v2
version: 1.1.0
phase: Specification
domain: Security Patch Management
tags: [srs, nfr, iso-25010, performance, security, reliability, usability, compatibility, maintainability]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-PRD-QP-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-ENV-001
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Yêu cầu phi chức năng (NFR) — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 45 NFR theo ISO/IEC 25010 (rules/04) cho CLI, console, quét tương thích, job, audit, Phase 2; chỉ mục 15 NFR đã phát hành (`NFR-FEED-001..008`, `NFR-ENV-01..07`); ghi các điểm lệch có chủ đích so với mức mặc định của rules/04 |
| 1.0.1 | 2026-10-22 | BA Agent | `NFR-CMP-002`: nâng trần Bash lên 5.3 (Alpine 3.23/3.24, Ubuntu 26.04 dùng Bash 5.3), thêm Ubuntu 26.04 LTS vào ma trận CI; `NFR-CMP-003`: Python 3.6–3.14 (Ubuntu 26.04 và Alpine 3.24 mặc định Python 3.14); `NFR-MNT-003`: `py_compile` trên 3.6 và 3.14; thêm §5 Tài liệu tham chiếu |
| 1.1.0 | 2026-10-22 | BA Agent | Sửa theo review. Mức MINOR theo rule 19 vì thêm tiêu chí kiểm tra chủ sở hữu/symlink mới và đổi chỉ tiêu đo, không chỉ làm rõ câu chữ (cách đánh số như spec.md, business-rules.md 1.1.0). (1) `NFR-SEC-010`: thêm điều kiện `STATE_DIR`, `backups/<run_id>/` và `manifest` có `st_uid` = `EUID`, không symlink, `mode & 0022 = 0`; cách đo bằng thư mục/symlink do user khác tạo sẵn ở đường dẫn chính, dự phòng và `manifest` (100% thoát 2 với `ERR-CLI-412-01` hoặc bỏ qua ứng viên, 0 file ghi vào); FR liên quan thêm `FR-CLI-ENV-001`, `FR-PTCH-RBK-002` (spec.md `CR-SRS-13`); (2) `NFR-REL-007`: ghi phạm vi phát hiện theo `BR-AUD-003`, `BR-AUD-006` (chuỗi hash phát hiện thay đổi khi hash phía sau không được tính lại; cắt đuôi và chuỗi tính lại chỉ phát hiện bằng neo), cách đo thêm ca cắt đuôi, tính lại chuỗi và `--anchor` (business-rules.md §6 mục 8); (3) `NFR-ENV-05` ở §3: chép lại tóm tắt theo environment-playbooks.md §8 (dòng `created` từ C3, nhánh `ABORTED`); (4) `NFR-PERF-007`: 500 KB chưa nén cần 4 s ở 1 Mbit/s nên thêm ngân sách ≤ 150 KB trên dây ở lần tải đầu (gzip), ≤ 2 s lần tải đầu, ≤ 1 s khi cache ấm, điều kiện đo DevTools cụ thể; ghi "(mục tiêu, chưa đo)"; (5) thêm §6 Tài liệu cần cập nhật theo; §5 thêm nguồn kiểm chứng |

## 1. Quy ước và môi trường đo
- Mã `NFR-[NHÓM]-[SEQ]`: `PERF` hiệu năng, `SEC` bảo mật, `REL` độ tin cậy, `USE` khả dụng, `CMP` tương thích, `MNT` bảo trì, `CAP` dung lượng.
- **Máy đo chuẩn** (trừ khi ghi khác): VPS 2 vCPU / 2 GB RAM, SSD, Linux có systemd, ≤ 50 vhost, ≤ 20 lockfile, băng thông ≥ 10 Mbit/s; console truy cập qua SSH tunnel có RTT ≤ 100 ms. P95 đo trên ≥ 20 lần chạy.
- Mỗi NFR có cách đo; NFR ghi "(mục tiêu, chưa đo)" phải được QA đo bằng benchmark trước khi phát hành bản 2.0.0.

## 2. Lệch có chủ đích so với rules/04
| Mục rules/04 | Mức của rules/04 | Mức áp dụng | Lý do |
| :--- | :--- | :--- | :--- |
| Throughput | ≥ 1.000 TPS | Không áp dụng; console phục vụ ≤ 5 phiên của 1 người vận hành | Công cụ quản trị cục bộ, không phải dịch vụ công khai |
| TLS 1.3 cho mọi giao tiếp | TLS 1.3 | Console: HTTP trên loopback trong SSH tunnel (`C-SRS-03`); kết nối ra nguồn online: TLS ≥ 1.2 (`NFR-FEED-004`) vì máy chủ nguồn bên thứ ba quyết định phiên bản TLS | Lưu lượng console không rời `127.0.0.1`; SSH mã hoá kênh |
| Mã hoá at-rest AES-256, băm Argon2id/Bcrypt | AES-256, Argon2id/Bcrypt | Phase 1 không lưu mật khẩu (token chỉ trong bộ nhớ); Phase 2 dùng `hashlib.scrypt` (thư viện chuẩn) — câu hỏi mở Q-SRS-06 | Ràng buộc Python thư viện chuẩn (`C-SRS-01`) |
| Uptime 99,9%, RPO/RTO | 99,9%, RPO < 15 phút, RTO < 1 giờ | Không áp dụng cho console (chạy theo nhu cầu); thay bằng yêu cầu hoàn tác `NFR-REL-*` và `NFR-ENV-02` | Console không phải dịch vụ thường trú (DOC-BRS-QP-001 §5.2) |

## 3. NFR đã phát hành ở phụ lục (chỉ mục)
| Mã | Nhóm | Tóm tắt | Vị trí |
| :--- | :--- | :--- | :--- |
| `NFR-FEED-001` | Hiệu năng | Đồng bộ tăng dần ≤ 180 s P95; đầy đủ ≤ 900 s | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-002` | Hiệu năng | `scan` chờ đồng bộ tối đa 120 s | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-003` | Tài nguyên | Chuẩn hoá 2.000 CVE + 2.000 KEV ≤ 200 MB RSS, ≤ 30 s CPU | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-004` | Bảo mật | TLS ≥ 1.2 có xác thực chứng chỉ; quyền thư mục; 0 key trong log | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-005` | Dung lượng | `feeds/` ≤ 60 MB | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-006` | Độ tươi | Tuổi dữ liệu ≤ 6 giờ 15 phút tại 99% thời điểm (KR1.1) | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-007` | Độ tin cậy | 100% `scan` hoàn tất khi 1..15 nguồn lỗi (KR5.3) | [data-sources.md §6](data-sources.md) |
| `NFR-FEED-008` | Tải lên nguồn | Đồng bộ tăng dần ≤ 45 request | [data-sources.md §6](data-sources.md) |
| `NFR-ENV-01` | Hiệu năng | Bước C6–C10 của 1 lượt chuyển ≤ 30 s P95 | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-02` | Độ tin cậy | Rollback 1 site ≤ 60 s P95 (KR4.2) | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-03` | Độ tin cậy | Tự rollback bắt đầu ≤ 5 s, hoàn tất ≤ 60 s | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-04` | Độ tin cậy | Graceful reload gây 0 phản hồi 5xx | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-05` | Phục hồi | 100% lượt chuyển có manifest với dòng `switch` và ≥ 1 dòng khôi phục trước bước C7 (KR4.1); 100% file pool/handler do lượt tạo có dòng `created` từ bước C3, trước khi file được tạo; 0 file pool/handler của lượt còn lại sau nhánh `ABORTED` | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-06` | Bảo trì | Thêm playbook chỉ cần dữ liệu catalog | [environment-playbooks.md §8](environment-playbooks.md) |
| `NFR-ENV-07` | Tương thích | Nhận diện môi trường ≤ 5 s với ≤ 200 vhost | [environment-playbooks.md §8](environment-playbooks.md) |

## 4. NFR mới

### 4.1 Hiệu năng (`PERF`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-PERF-001` | API console đọc (`GET /api/v1/...`, trừ SSE): P95 ≤ 500 ms với 5 phiên đồng thời, mỗi phiên 2 request/giây | Script gửi request qua loopback 10 phút, đo `time_total` | `FR-CON-API-001` |
| `NFR-PERF-002` | API console tạo job/ghi (`POST`, `PATCH`): P95 ≤ 1.500 ms tính tới khi trả `job_id` (không gồm thời gian chạy job) | Như trên | `FR-JOB-RUN-001`, `FR-CON-SAFE-001` |
| `NFR-PERF-003` | Độ trễ log job: dòng CLI ghi ra hiển thị trên SCR-006 ≤ 2 s ở P95 | So dấu thời gian dòng log với thời điểm sự kiện SSE tới trình duyệt | `FR-JOB-LOG-002` |
| `NFR-PERF-004` | `scan` (không đồng bộ feed, không tra OSV) ≤ 60 s P95 trên máy đo chuẩn có 4 binary PHP, 2 binary Node.js, 20 lockfile; tra OSV thêm ≤ 30 s cho ≤ 3.000 package (mục tiêu, chưa đo) | `time php-quickpatch.sh scan --json --offline` và chạy có mạng | `FR-SCAN-*`, `FR-ASMT-DEP-001` |
| `NFR-PERF-005` | Sinh kế hoạch gồm quét tương thích ≤ 120 s cho 1 site có ≤ 10.000 file `.php` và ≤ 300 package trong `composer.lock` (KR3.2; mục tiêu, chưa đo) | Benchmark trên bộ mã WordPress + Laravel mẫu, đo từ lúc tạo job tới `plan` ở `draft` | `FR-PLAN-GEN-001`, `FR-CMPT-*` |
| `NFR-PERF-006` | Tiến trình console: khởi động tới lúc nhận request ≤ 3 s; RSS ≤ 100 MB khi rảnh, ≤ 200 MB khi stream 3 log | `/usr/bin/time -v`, `ps -o rss` | `FR-CON-AUTH-001` |
| `NFR-PERF-007` | Tài nguyên tĩnh của console tổng ≤ 500 KB chưa nén (KB = 1.000 byte). Lần tải đầu SCR-002 (cache trống): tổng byte truyền trên dây của mọi phản hồi (HTML, tài nguyên tĩnh, `GET /api/v1/overview`, gồm header) ≤ 150 KB, nhờ trả bản nén gzip (module `gzip` thư viện chuẩn) với `Content-Encoding: gzip` khi request có `Accept-Encoding: gzip`; SCR-002 hiển thị đủ dữ liệu ≤ 2 s. Cache ấm (tải lại trong cùng phiên): 0 byte thân tài nguyên tĩnh không đổi được truyền lại (304 theo `ETag`/`If-None-Match` hoặc dùng bản trong cache); SCR-002 hiển thị đủ dữ liệu ≤ 1 s. Cả hai qua tunnel 1 Mbit/s, RTT 100 ms (mục tiêu, chưa đo) | DevTools: profile điều tiết tuỳ chỉnh 1.000 kbit/s tải xuống và tải lên, latency 100 ms; 1 phiên, không có job chạy, dữ liệu mẫu ≤ 50 site; Network lấy tổng cột "Transferred", Performance đo từ lúc điều hướng tới khi khối dữ liệu SCR-002 hiển thị; 20 lần mỗi chế độ (cache trống, cache ấm), lấy P95. Cơ sở ước tính lần tải đầu: 150.000 byte × 8 / 10⁶ bit/s = 1,2 s truyền + 3 RTT nối tiếp (HTML → tài nguyên tĩnh → API) = 0,3 s, còn 0,5 s cho xử lý phía console (bằng P95 của `NFR-PERF-001`). Mức cũ 500 KB chưa nén không đạt được 2 s: 500.000 × 8 / 10⁶ = 4 s chỉ để truyền | `FR-CON-OVW-001`, `FR-CON-SAFE-002` |

### 4.2 Bảo mật (`SEC`) — OWASP Top 10 áp dụng cho console
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-SEC-001` | Console chỉ lắng nghe `127.0.0.1`: 0 socket của tiến trình console trên địa chỉ khác | `ss -ltnp` lọc PID console trên 3 bản phân phối | `FR-CON-AUTH-001` |
| `NFR-SEC-002` | Token có 256 bit ngẫu nhiên từ CSPRNG; so sánh hằng thời gian; 0 lần token xuất hiện trong log, audit, `--json`, file trong `STATE_DIR` (trừ `--token-file` do người vận hành chỉ định) | Review mã + `grep -r <token>` toàn bộ `STATE_DIR` và log sau phiên test | `FR-CON-AUTH-002`, `FR-CON-AUTH-003` |
| `NFR-SEC-003` | 100% endpoint (trừ 4 endpoint công khai ở `FR-CON-AUTH-004`) trả 401 khi không có cookie/Bearer hợp lệ | Test tự động duyệt danh mục API (spec §3.3.3) | `FR-CON-AUTH-004` |
| `NFR-SEC-004` | 100% request có `Host` ngoài danh sách cho phép trả 421, kể cả tài nguyên tĩnh và SSE | Test với `curl -H 'Host: attacker.example:17321'` | `FR-CON-AUTH-005` |
| `NFR-SEC-005` | 100% request ghi bằng cookie thiếu `X-QP-CSRF` hoặc `Origin` sai bị từ chối; 0 endpoint `GET` đổi trạng thái | Test tự động; trang HTML ngoài gửi form `POST` tới console phải thất bại | `FR-CON-AUTH-006` |
| `NFR-SEC-006` | Mọi phản hồi có đủ header của `BR-CON-007`; 0 lỗi vi phạm CSP trên 10 màn hình Phase 1; 0 request tới origin khác `127.0.0.1:<port>` | DevTools Console/Network, file HAR | `FR-CON-SAFE-002` |
| `NFR-SEC-007` | 0 lời gọi `shell=True`, `os.system`, `os.popen`, `eval`, `exec` trong mã Python; 0 `eval` trong mã Bash xử lý dữ liệu ngoài | `grep -nE` trong CI; `shellcheck` mức `error` = 0 | `FR-CON-SAFE-003` |
| `NFR-SEC-008` | 100% tham số job ngoài danh sách trắng hoặc sai regex trả 422 và không tạo tiến trình | Fuzz 1.000 giá trị/tham số (gồm `;`, `$(...)`, `` ` ``, `--option`, `../`, ký tự xuống dòng) | `FR-CON-SAFE-003` |
| `NFR-SEC-009` | XSS: mọi dữ liệu từ máy chủ (đường dẫn file, trích đoạn mã, log) hiển thị bằng `textContent`, không `innerHTML` với dữ liệu động; 0 cảnh báo XSS khi hiển thị file tên chứa `<script>` | Test với dữ liệu mẫu độc hại; review mã JS | `FR-CON-*` |
| `NFR-SEC-010` | Quyền, chủ sở hữu và loại tệp của `STATE_DIR` (spec §2.1, `CR-SRS-13`): (1) quyền: `STATE_DIR` `0700` (không root) / `0750` (root); `audit/`, `jobs/`, `console/`, `plans/` `0700`; file trong đó `0600`; (2) trước lần đọc/ghi đầu tiên, `STATE_DIR` là thư mục thật (không symlink), `st_uid` = `EUID`, `mode & 0022 = 0` (kiểm bằng `lstat`); trước khi `rollback [ID]` đọc `manifest`, `backups/<run_id>/` (thư mục thật) và `backups/<run_id>/manifest` (file thường) đạt cùng 3 điều kiện; (3) đường dẫn chính hoặc `backups/<run_id>/`, `manifest` không đạt → 100% lượt thoát 2 với `ERR-CLI-412-01`; ứng viên dự phòng (chỉ người dùng không root) không đạt → 100% bị bỏ qua, tool tạo thư mục mới bằng `mktemp -d` mode `0700`; 0 file được tạo hoặc sửa trong thư mục không đạt; 0 dòng của `manifest` không đạt được thực thi | (1) `stat -c %a` trong test cài đặt; `STATE_DIR` chủ `EUID` mode `0755` (do v0.1 tạo) → về `0750`/`0700` và 1 dòng cảnh báo trong log. (2)(3) Ma trận test: tạo sẵn đối tượng có chủ là user khác (UID ≠ `EUID`, dựng bằng root trong test) tại đường dẫn chính (`/var/lib/php-quickpatch` khi root; `$HOME/.php-quickpatch` khi không root), tại 2 tên ứng viên dự phòng (`${TMPDIR:-/tmp}/php-quickpatch-$EUID`, `${TMPDIR:-/tmp}/php-quickpatch-$EUID.<6 ký tự>`; chạy không root với `HOME` rỗng), tại `backups/<run_id>/` và `backups/<run_id>/manifest`; mỗi vị trí 4 kiểu: symlink tới thư mục/file của user khác, thư mục/file có chủ là user khác, thư mục/file chủ `EUID` nhưng group/other ghi được (`0777`/`0666`), sai loại (file thường ở vị trí thư mục, thư mục ở vị trí `manifest`); chạy `scan`, `fix --dry-run`, `rollback [ID]`; so `sha256sum` và mtime mọi file trong thư mục tạo sẵn trước/sau, so file đích của các dòng `copy`/`created` trong `manifest` giả trước/sau | `FR-CLI-ENV-001`, `FR-PTCH-RBK-002`, `FR-JOB-AUD-001`, `FR-JOB-LOG-001` |

### 4.3 Độ tin cậy (`REL`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-REL-001` | Console hoạt động khi PHP-FPM, Node.js và web server đều dừng: 10/10 màn hình Phase 1 mở được | Dừng dịch vụ rồi kiểm thử | `FR-CON-*` |
| `NFR-REL-002` | 100% job ghi có bản ghi audit "intent" trước thay đổi đầu tiên và bản ghi "result" khi kết thúc (KR4.1) | Đối chiếu `jobs/*/job.json` với `audit/*.jsonl` sau bộ test | `FR-JOB-AUD-001` |
| `NFR-REL-003` | Khởi động lại console khi đang có job: 100% job `RUNNING` được đối soát (`INTERRUPTED` hoặc tiếp tục theo dõi) trong ≤ 5 s sau khi `serve` chạy lại; 0 job ghi tự chạy lại | Test kill `qp-console.py` ở từng `phase` | `FR-JOB-RUN-004` |
| `NFR-REL-004` | Không có 2 job ghi cùng `RUNNING` trên 1 máy chủ, kể cả khi 1 job từ CLI và 1 job từ console | Test đồng thời 50 lần | `FR-JOB-RUN-002` |
| `NFR-REL-005` | Rollback lượt chạy (`rollback [ID]`) khôi phục 100% file có dòng `copy`/`created` của manifest | Test so SHA-256 file trước/sau trên 20 kịch bản | `FR-PTCH-RBK-002` |
| `NFR-REL-006` | Dữ liệu kế hoạch không hỏng khi mất điện/kill giữa lúc ghi: ghi tạm + `rename`; 0 file `plan.json` không parse được sau 100 lần kill ngẫu nhiên | Test kill -9 trong lúc cập nhật mục | `FR-PLAN-GEN-001`, `FR-PLAN-CHK-001` |
| `NFR-REL-007` | Phạm vi phát hiện của audit (`BR-AUD-003`, `BR-AUD-006`): (1) chuỗi hash phát hiện 100% thay đổi 1 byte, xoá hoặc chèn bản ghi ở giữa chuỗi khi các hash phía sau không được tính lại; `audit verify` báo đúng `seq` đầu tiên lệch (`ERR-AUD-409-01`); (2) sửa rồi tính lại toàn bộ hash phía sau, xoá N bản ghi cuối hoặc xoá cả file tháng mới nhất: chuỗi hash không phát hiện được; phát hiện 100% bằng đối chiếu neo khi có ≥ 1 neo (`audit_anchor` trong `jobs/*/result.json` hoặc `--anchor SEQ:HASH`, đề xuất của `BR-AUD-006`) có `seq` ≥ `seq` của bản ghi đầu tiên bị sửa hoặc xoá; (3) không còn neo nào như vậy (vd root xoá cả audit và `jobs/*/result.json`, không có neo lưu ngoài máy) → ngoài phạm vi phát hiện; kết luận ĐẠT chỉ có nghĩa "khớp với các neo đã đối chiếu" (business-rules.md §5 mục 2) | (1) Sửa ngẫu nhiên 1 byte 100 lần, mỗi lần trên 1 bản sao audit, rồi chạy `audit verify`. (2) Lấy neo A trước khi thay đổi; mỗi ca cắt 1, 3, 10 bản ghi cuối, xoá file tháng mới nhất, sửa 1 bản ghi rồi tính lại hash phía sau theo công thức `BR-AUD-003`; chạy `audit verify --anchor A` và chạy với neo trong `jobs/*/result.json` → 100% `ERR-AUD-409-01`. (3) Cùng các ca, xoá mọi `jobs/*/result.json` và không truyền `--anchor` → ghi nhận ĐẠT, xác nhận giới hạn đã nêu (`TC-JOB-023`, `TC-JOB-024`, `TC-JOB-102`) | `FR-JOB-AUD-002` |

### 4.4 Khả dụng (`USE`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-USE-001` | Vá cùng nhánh 1 runtime trên console ≤ 3 thao tác: chọn finding → xem dry-run → xác nhận (KR1.3) | Đếm thao tác theo kịch bản test | `FR-CON-ASMT-001`, `FR-CON-SAFE-001` |
| `NFR-USE-002` | Từ SCR-002 tới checklist kế hoạch hoàn chỉnh ≤ 4 thao tác, không gõ lệnh (KR3.1) | Như trên | `FR-CON-PLAN-001` |
| `NFR-USE-003` | WCAG 2.1 AA: tương phản chữ ≥ 4,5:1; 100% thao tác dùng được bằng bàn phím (Tab, Enter, Esc); mọi trường nhập có nhãn | Công cụ kiểm tra tương phản + test bàn phím | `FR-CON-*` |
| `NFR-USE-004` | Bố cục dùng được ở chiều rộng 360–1.920 px; ≤ 1.024 px bảng chuyển sang dạng thẻ, không cuộn ngang trang | Kiểm thử ở 360, 768, 1.024, 1.920 px | `FR-CON-*` |
| `NFR-USE-005` | 100% thông báo lỗi hiển thị có localization key (rules/11) và bản tiếng Việt; console có bản tiếng Anh cho 100% chuỗi | So danh sách key với `error-matrix.md` | `FR-CON-API-001` |
| `NFR-USE-006` | Mọi thao tác ghi trên console hiển thị: danh sách thay đổi của dry-run, site/dịch vụ bị ảnh hưởng, gián đoạn dự kiến (giây), khả năng hoàn tác — 4/4 mục trên SCR-011 | Review UI theo checklist | `FR-CON-SAFE-001` |

### 4.5 Tương thích (`CMP`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-CMP-001` | 100% test hồi quy hành vi v0.1 đạt: cú pháp, tuỳ chọn, mã thoát, định dạng dòng văn bản, manifest, `rollback [ID]` (KR: FEAT-101) | Bộ test chạy script v0.1 và v2 trên cùng máy mẫu, so đầu ra theo `BR-CLI-002` | `FR-CLI-COMP-001` |
| `NFR-CMP-002` | CLI chạy trên Bash 4.3 tới 5.3 và trên Debian 11–13, Ubuntu LTS 20.04, 22.04, 24.04, 26.04, AlmaLinux/Rocky 8–10, Alpine 3.22–3.24 (ma trận CI; Bash 5.3 là bản mặc định của Alpine 3.23, Alpine 3.24 và Ubuntu 26.04 — §5) | CI container theo từng bản; mỗi lượt ghi `bash --version` của image vào kết quả CI | `FR-CLI-ENV-001` |
| `NFR-CMP-003` | Console chạy trên Python 3.6–3.14 và hiển thị đúng trên phiên bản ổn định hiện hành và liền trước của Chrome, Edge, Firefox, Safari | CI Python đa phiên bản 3.6–3.14, gồm `python3` mặc định của Ubuntu 26.04 và Alpine 3.24 (3.14 — §5); kiểm thử trình duyệt | `FR-CON-AUTH-001` |
| `NFR-CMP-004` | Schema `--json`: 100% đầu ra mẫu hợp lệ theo JSON Schema đã phát hành; thay đổi không tương thích chỉ khi tăng major (`BR-CLI-001`) | Validate trong CI | `FR-CLI-JSON-001`, `FR-CLI-JSON-002` |
| `NFR-CMP-005` | `scan`, `fix`, `rollback`, `migrate` chạy được khi máy không có Python 3 (C-01) | Test trên image không có `python3` | `FR-CLI-ENV-001` |

### 4.6 Bảo trì (`MNT`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-MNT-001` | Thêm kịch bản, mục checklist, luật BC hoặc luật mitigation chỉ cần sửa catalog: 0 dòng sửa trong `php-quickpatch.sh` | Review thay đổi khi cập nhật catalog | `FR-SCN-CAT-001` |
| `NFR-MNT-002` | Test hồi quy `min_patched` (DOC-SRS-QP-FEED-002 §6.5) và 11 ví dụ điểm rủi ro (§8.5) đạt 100% | CI với bundle mẫu 2026-10-22 | `FR-FEED-NORM-002`, `FR-ASMT-RISK-001` |
| `NFR-MNT-003` | `shellcheck` 0 lỗi mức `error` và `warning`; mã Python qua `python3 -m py_compile` trên 3.6 và 3.14 (cận dưới và cận trên của `NFR-CMP-003`) | CI | Mọi FR |
| `NFR-MNT-004` | Mỗi FR P0 có ≥ 1 test case truy vết được (rules/14) trước khi phát hành | Ma trận truy vết test | Mọi FR P0 |

### 4.7 Dung lượng (`CAP`)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-CAP-001` | `jobs/` ≤ 200 MiB; `audit/` tăng ≤ 10 MiB/tháng với 1.000 sự kiện/ngày | `du -sb` sau 30 ngày mô phỏng | `FR-JOB-LOG-003`, `FR-JOB-AUD-001` |
| `NFR-CAP-002` | `tools/php` ≤ 80 MB (mục tiêu, chưa đo) | `du -sb` sau `FR-CMPT-TOOL-001` | `FR-CMPT-TOOL-001` |
| `NFR-CAP-003` | Thư mục `backups/` không bị tool tự xoá ở Phase 1 (giữ khả năng rollback); `scan` cảnh báo khi `backups/` > 1 GiB | Test với 1,1 GiB dữ liệu mẫu | `FR-PTCH-RBK-001` |

### 4.8 Phase 2 (`PERF`, `SEC` — chỉ đặc tả)
| Mã | Yêu cầu định lượng | Cách đo | FR liên quan |
| :--- | :--- | :--- | :--- |
| `NFR-PERF-008` | Thu `scan --json` từ 100 server (10 kết nối song song) ≤ 20 phút khi mỗi server ≤ 60 s | Mô phỏng 100 container SSH | `FR-FLT-EXEC-001`, `FR-FLT-EXEC-002` |
| `NFR-SEC-011` | 0 kết nối SSH chấp nhận khoá máy chủ chưa ghim; 0 mật khẩu SSH lưu trên máy trung tâm | Test với máy chủ đổi khoá; review `central.db` | `FR-FLT-INV-002` |
| `NFR-SEC-012` | Sau mỗi lần chạy từ xa: 0 file tạm của tool còn lại ngoài `STATE_DIR` trên server | `find /tmp -name 'qp-*'` sau 100 lần chạy, gồm lần bị ngắt | `FR-FLT-EXEC-001` |

## 5. Tài liệu tham chiếu (References)
Kiểm chứng khi soạn bản 1.0.1 cho `NFR-CMP-002`, `NFR-CMP-003`, `NFR-MNT-003` và bản 1.1.0 cho `NFR-PERF-007`, `NFR-SEC-010`, `NFR-REL-007`, `NFR-ENV-05`.

| Nguồn | Nội dung đã kiểm chứng | Trạng thái |
| :--- | :--- | :--- |
| pkgs.alpinelinux.org — https://pkgs.alpinelinux.org/packages?name=bash&branch=v3.22&repo=main&arch=x86_64 | Alpine 3.22: `bash 5.2.37-r0` | Kiểm chứng |
| pkgs.alpinelinux.org — https://pkgs.alpinelinux.org/packages?name=bash&branch=v3.23&repo=main&arch=x86_64 | Alpine 3.23: `bash 5.3.3-r1` | Kiểm chứng |
| pkgs.alpinelinux.org — https://pkgs.alpinelinux.org/packages?name=bash&branch=v3.24&repo=main&arch=x86_64 | Alpine 3.24: `bash 5.3.9-r1` | Kiểm chứng |
| pkgs.alpinelinux.org — https://pkgs.alpinelinux.org/packages?name=python3&branch=v3.24&repo=main&arch=x86_64 | Alpine 3.24: `python3 3.14.8-r0` | Kiểm chứng |
| endoflife.date — https://endoflife.date/api/v1/products/ubuntu/releases/26.04 | Ubuntu 26.04 "Resolute Raccoon" LTS: phát hành 2026-04-23; hết hỗ trợ chuẩn 2031-05-29 | Kiểm chứng |
| Launchpad — https://launchpad.net/ubuntu/resolute/+source/bash | Ubuntu 26.04: `bash 5.3-2ubuntu1` (pocket Release) | Kiểm chứng |
| Launchpad — https://launchpad.net/ubuntu/resolute/+source/python3-defaults | Ubuntu 26.04: `python3-defaults 3.14.3-0ubuntu2` (Python mặc định 3.14) | Kiểm chứng |
| endoflife.date — https://endoflife.date/api/v1/products/python/releases/3.14 | Python 3.14: phát hành 2025-10-07; EOL 2030-10-31 | Kiểm chứng |
| Phiên bản Bash/Python mặc định của Debian 11–13, Ubuntu 20.04–24.04, AlmaLinux/Rocky 8–10 | Nằm trong khoảng Bash 4.3–5.3 và Python 3.6–3.14 | Chưa kiểm chứng trong phiên này; CI ghi `bash --version`, `python3 --version` của từng image để xác nhận |
| docs.python.org — https://docs.python.org/3/library/gzip.html | `gzip.compress()`: "Added in version 3.2" → có trên mọi bản Python 3.6–3.14 của `NFR-CMP-003`; chạy thử `python3 -c "import gzip; gzip.compress"` trên Python 3.13 đạt | Kiểm chứng (2026-10-22) |
| MDN — https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control | Tài nguyên có hash trong URL dùng `max-age` dài + `immutable`; HTML dùng `no-cache` để luôn kiểm lại — 2 cách đạt điều kiện cache ấm của `NFR-PERF-007` cùng với `ETag`/304 (đề xuất của api-spec-core.md) | Kiểm chứng (2026-10-22) |
| Tính toán `NFR-PERF-007` | 500.000 byte × 8 / 10⁶ bit/s = 4 s; 150.000 byte × 8 / 10⁶ bit/s = 1,2 s; 3 RTT × 100 ms = 0,3 s. Tỉ lệ nén gzip thực tế của bộ tài nguyên tĩnh chưa có số liệu | Phép tính: kiểm chứng; tỉ lệ nén: chưa đo (QA đo khi có bản dựng) |
| [spec.md](spec.md) §2.1 (5 bước kiểm tra `STATE_DIR`), §3.5 (`ERR-CLI-412-01`), §4.3 `CR-SRS-13` | Điều kiện và cách đo của `NFR-SEC-010` | Đối chiếu |
| [business-rules.md](business-rules.md) `BR-AUD-003`, `BR-AUD-006`, §5 mục 2, §6 mục 8 | Phạm vi phát hiện của `NFR-REL-007` | Đối chiếu |
| [environment-playbooks.md](environment-playbooks.md) §8 `NFR-ENV-05` (nội dung từ bản 1.0.1) | Tóm tắt `NFR-ENV-05` ở §3 | Đối chiếu |

## 6. Tài liệu cần cập nhật theo bản 1.1.0
| # | NFR | Tài liệu | Nội dung cần cập nhật |
| :--- | :--- | :--- | :--- |
| 1 | `NFR-PERF-007` | [business-rules.md](business-rules.md) `BR-CON-007`; [functional-requirements.md](functional-requirements.md) `FR-CON-SAFE-002`; [api-spec-core.md §7](../api/api-spec-core.md) (`GET /static/{file}`), [api-spec.md §6.2](../api/api-spec.md) mục 7 | Gzip cho tài nguyên tĩnh khi có `Accept-Encoding: gzip`, `Vary: Accept-Encoding`; cơ chế cache ấm (`ETag`/304 hoặc hash trong tên + `max-age`); bỏ nhãn "(ĐX)" khi PO duyệt |
| 2 | `NFR-PERF-007` | `AC-CON-66`, test case tương ứng; `UC-CON-001`, `UC-CON-002` (dòng NFR) | Thêm kiểm "Transferred" ≤ 150 KB ở lần tải đầu và ≤ 1 s khi cache ấm |
| 3 | `NFR-SEC-010` | test-cases-coverage.md (dòng `NFR-SEC-010`), test case của `FR-CLI-ENV-001`, `FR-PTCH-RBK-002`; `UC-FEED-004`, `UC-JOB-001`, `UC-JOB-003`, `UC-RPT-001` (dòng NFR) | Ca thư mục/symlink/`manifest` do user khác tạo sẵn theo ma trận test của `NFR-SEC-010` |
| 4 | `NFR-REL-007` | `UC-JOB-003`, `UC-RPT-002`, backlog.md `US-JOB-08`; test-cases-coverage.md (dòng `NFR-REL-007` thêm `TC-JOB-102`) | Thay câu "phát hiện 100% thay đổi 1 byte" bằng phạm vi (1)–(3) của `NFR-REL-007` |
