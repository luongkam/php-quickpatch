---
id: DOC-UC-QP-UPG-002
title: Đặc tả Use Case UC-UPG-002 — Chuyển 1 site sang runtime mới và health check
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-002, migrate-switch, site-switch, health-check, canary, auto-rollback, baseline, fastcgi-probe, migrate-ack]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-ENV-004
  - DOC-API-QP-004
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-UPG-002
  - DIAG-STATE-QP-ENV-002
  - DIAG-FLOW-QP-ENV-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đặc tả luồng xác nhận đã xử lý lượt chuyển lỗi `FR-UPG-ACK-001` (đề xuất, `CR-FR-01` của DOC-SRS-QP-FR-001 §15.2) ở 2b2–2b7, 2c2, 14a4, 14b2, 14c2 (`migrate ack`, `POST /api/v1/switches/{run_id}/acknowledgements`, `ERR-UPG-409-04`); thêm `FR-UPG-ACK-001` vào bảng FR, BR liên quan và API; bỏ nhãn "mã đề xuất" của `ERR-UPG-409-03`, liên kết tới error-matrix.md §3.11; đổi tên `FR-CON-SITE-001` theo `CR-FR-06` |

## UC-UPG-002: Chuyển 1 site sang runtime mới và health check

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`).
- **Tác nhân hỗ trợ**: `SYS-03` web server (Nginx/Apache/LiteSpeed), PHP-FPM `$OLD`/`$NEW`, API/CLI panel; site của khách hàng (nhận request `GET` thăm dò); System: Job runner (job `migrate switch`, tự rollback trong cửa sổ health check).
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh migrate switch <site_id> --target X.Y --plan <plan_id>` (bí danh `switch-site`), `migrate healthcheck`, `migrate ack <run_id>` (đề xuất, `CR-FR-01`); mục P5/P6 của kế hoạch; console SCR-009, SCR-004, SCR-006, SCR-007.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: chuyển từng site, site đầu là canary; site lỗi được tự rollback bắt đầu ≤ 5 s và hoàn tất ≤ 60 s sau khi phát hiện vi phạm (`NFR-ENV-03`).
  - Khách truy cập site: đoạn C6–C10 ≤ 30 s P95 (`NFR-ENV-01`); graceful reload gây 0 phản hồi 5xx (`NFR-ENV-04`); health check ≤ 1 request đồng thời, ≤ 11 request/phút, chỉ `GET` (`BR-HC-002`, `BR-HC-012`).
  - `PER-04`: 100% lượt chuyển có manifest với dòng `switch` và ≥ 1 dòng khôi phục trước C7 (`NFR-ENV-05`); lưu `baseline.json`, `hc.json`, ≤ 50 dòng log vi phạm đã che bí mật (`BR-HC-011`).
  - Chủ khách hàng hosting: site panel không bị sửa ngoài cơ chế của panel (`BR-ENV-002`).
- **Tiền điều kiện (Pre-conditions)**:
  - Kế hoạch `approved`/`in_progress` chứa site (`BR-UPG-005`); site là site kế tiếp trong `site_order` (site đầu là canary).
  - Mục P3, P4 bắt buộc của site ở `DONE`/`WAIVED` (`BR-SCN-018`); kết luận tương thích `PASS` (`BR-UPG-002`).
  - `$NEW_BIN` đã cài (UC-UPG-001); không có lượt chuyển nào ở `SWITCHED`/`HC_RUNNING` trên máy (`BR-ENV-003`); không có lượt `ROLLBACK_FAILED` chưa được xác nhận đã xử lý (`FR-UPG-ACK-001`).
  - Site không chạy `mod_php` (nếu có: UC-UPG-003 trước, `BR-SCN-047`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: site trỏ `$NEW`; `switch_record.status = PASSED`; mục P5/P6 của site `DONE`; `STATE_DIR/backups/<run_id>/` có `manifest`, `switch.json`, `baseline.json`, `hc.json`; audit; site kế tiếp được mở.
  - **Đảm bảo tối thiểu**: khi health check không đạt và tự rollback bật, site trỏ lại `$OLD` (`ROLLED_BACK`), các site còn lại của kế hoạch dừng tới khi Operator xác nhận đã xử lý lượt đó (`BR-UPG-003`, `FR-UPG-ACK-001`); dừng trước C7 → `ABORTED`, site chưa bị thay đổi.
- **Kích hoạt (Trigger)**: Operator bấm "Chuyển" trên mục P5 của site ở SCR-004/SCR-009, hoặc chạy `migrate switch <site_id> --target 8.4 --plan <plan_id> --yes`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở SCR-009, kiểm site kế tiếp trong `site_order`, (tuỳ chọn) khai báo ≤ 10 URL `hc_url` cùng host (`FR-CON-SITE-001`, `FR-UPG-HC-001`).
2. Operator bấm "Chuyển"; console tạo job dry-run `migrate switch <site_id> --target <nhánh> --plan <plan_id> --yes --json --dry-run`; SCR-011 hiển thị file/lệnh panel sẽ đổi, dịch vụ sẽ reload, gián đoạn dự kiến, khả năng rollback (UC-CON-003).
3. Operator xác nhận trong ≤ 15 phút; console tạo job `write` `migrate switch` (`FR-UPG-SEQ-001`).
4. **C1**: CLI lấy khoá `STATE_DIR/.lock`, kiểm không có lượt ở `HC_RUNNING`; ghi audit intent; `switch_record.status = PREFLIGHT` (≤ 1 s).
5. **C2**: CLI kiểm điều kiện: P3/P4 `DONE`/`WAIVED`, kết luận `PASS`, nhánh đích hợp lệ (`BR-SCN-007`), `$NEW_BIN -r 'exit(0);'` exit 0 (≤ 10 s).
6. **C3**: CLI chuẩn bị pool/handler đích cho site, kiểm `php-fpm<X.Y> -t`, reload riêng FPM đích (≤ 15 s) (`FR-UPG-CFG-001`).
7. **C4**: CLI chạy FastCGI probe tới pool đích với `<docroot>/index.php`; ĐẠT khi nhận `FCGI_END_REQUEST` ≤ 10 s, `Status` không bắt đầu bằng `5`, stderr không có `PHP Fatal error`/`PHP Parse error`, body không chứa `<?php` (`FR-UPG-HC-002`, `BR-HC-003`).
8. **C5**: CLI lập tập URL (trang chủ tự phát hiện + URL khai báo) và thu baseline trên `$OLD`: 5 vòng cách 10 s, mã HTTP, `Location`, kích thước body, `time_total`; ghi byte offset log lỗi (`FR-UPG-HC-001`, `FR-UPG-HC-003`, `BR-HC-004`, `BR-HC-005`).
9. **C6**: CLI ghi manifest theo thứ tự `reload` → `switch <site_id> <from>><to>` → `copy`/`panel` → `created`, `backup_file` mọi file sẽ đổi (≤ 2 s) (`BR-SCN-017`).
10. **C7**: CLI đổi lớp gán: sửa file vhost/handler (PB-001..006) hoặc gọi API/CLI panel rồi đọc lại giá trị (PB-007..012) (≤ 5 s) (`FR-UPG-SWT-001`, `FR-UPG-SWT-002`, `BR-ENV-012`).
11. **C8**: CLI kiểm cú pháp web server (`nginx -t`, `apachectl configtest`, lệnh panel) (≤ 5 s) (`BR-ENV-005`).
12. **C9**: CLI graceful reload phạm vi nhỏ nhất (web server, FPM đích), `switch_record.status = SWITCHED` (≤ 5 s) (`BR-ENV-006`).
13. **C10**: CLI xác minh gán đã có hiệu lực (`HC-C0`: FPM status `accepted conn` tăng, tiến trình worker thuộc `$NEW_BIN`, lệnh liệt kê panel, tiến trình LSAPI) trong ≤ 10 s; `status = HC_RUNNING`.
14. **C11**: CLI giải phóng `STATE_DIR/.lock`, giữ `switches/<site_id>.lock`; chạy cửa sổ theo dõi 600 s: 10 vòng × 60 s, đánh giá tiêu chí `HC-C1`..`HC-C9` (mã HTTP = baseline, 0 phản hồi 5xx, timeout ≤ 2, lệch kích thước ≤ `T(u)`, không lộ mã nguồn/lỗi PHP, P95 trong ngưỡng, 0 Fatal mới, Warning ≤ max(20; 1,2 × W0), FPM `active`) (`FR-UPG-HC-004`, `BR-HC-006`..`BR-HC-009`).
15. Hệ thống kết luận ĐẠT sau 600 s và ra quyết định `PASSED` (`FR-UPG-HC-005`).
16. **C12**: CLI ghi `switch_record` `PASSED`, `hc.json`, audit result; đặt mục P5/P6 của site `DONE`; thoát 0.
17. Console hiển thị báo cáo health check (bảng vòng × URL, biểu đồ thời gian phản hồi, ≤ 50 dòng log vi phạm) trên SCR-006 (`FR-UPG-HC-006`) và mở site kế tiếp trong `site_order`.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. URL khai báo sai cú pháp, khác host, hoặc > 10 URL**:
  - 1a1. Hệ thống bỏ URL đó (lấy 10 URL đầu), cảnh báo `ERR-HC-422-02` (`BR-HC-002`).
- **1b. Không tìm được host hợp lệ cho trang chủ**:
  - 1b1. Hệ thống trả `ERR-HC-412-03`; Operator phải khai báo ≥ 1 `hc_url` (`BR-HC-001`).
- **1c. Tham số `hc.*` trong file cấu hình ngoài khoảng cho phép**:
  - 1c1. Hệ thống dùng giá trị mặc định, cảnh báo `ERR-HC-422-01`.
- **2a. Site không thuộc kế hoạch `approved`/`in_progress`**:
  - 2a1. Hệ thống trả `ERR-UPG-409-02`; trên CLI có thể dùng `--no-plan --reason TEXT` (lý do ≥ 20 ký tự, ghi audit) (`BR-UPG-005`).
- **2b. Site không phải site kế tiếp của `site_order`, hoặc lượt trước của kế hoạch ở `ROLLED_BACK`/`HC_FAILED_KEPT` chưa được xác nhận đã xử lý**:
  - 2b1. Hệ thống từ chối với `ERR-UPG-409-03` (Medium, mã thoát 2, không tạo lượt chuyển — DOC-SRS-QP-STATE-001 `T-SW-02`; định nghĩa ở [error-matrix.md](../srs/error-matrix.md) §3.11) (`BR-ENV-003`, `BR-UPG-003`). Site sai thứ tự: Operator chọn đúng site kế tiếp, use case quay lại bước 1.
  - 2b2. Lượt trước chưa xác nhận: Operator xử lý nguyên nhân lỗi, rồi chạy `migrate ack <run_id> --reason "<20–500 ký tự>" --json` hoặc bấm "Xác nhận đã xử lý" trên hàng site ở SCR-009 hay lượt chuyển ở SCR-007 và nhập lý do; console gọi `POST /api/v1/switches/{run_id}/acknowledgements` → hành động danh sách trắng `switch_ack`, loại `control` (đồng bộ, timeout 30 s, không cần dry-run, vẫn qua kiểm Host/phiên/CSRF) (`FR-UPG-ACK-001` đề xuất `CR-FR-01`, `FR-CON-SITE-001`, `FR-CON-RBK-001`).
  - 2b3. CLI lấy khoá `STATE_DIR/.lock` (`BR-JOB-002`); kiểm `run_id` có trong `switches/index.tsv`, `status` ∈ {`ROLLED_BACK`, `HC_FAILED_KEPT`, `ROLLBACK_FAILED`} và chưa có `acknowledged_at`; ghi audit "intent" (`actor`, `run_id`, `site_id`, `plan_id`, `status`, lý do đã che bí mật) (`BR-AUD-001`, `BR-SEC-006`).
  - 2b4. CLI đọc lại lớp gán hiện tại của site theo playbook (`FR-SCAN-MAP-001`) làm bằng chứng `binding_now`; nối 1 dòng vào `switches/index.tsv`, ghi `acknowledged_at` (UTC), `acknowledged_by`, `ack_reason` vào `backups/<run_id>/switch.json` bằng ghi file tạm + `rename`. Trạng thái lượt không đổi (`T-SW-19`); 0 thay đổi gói, dịch vụ, cấu hình web server hay site.
  - 2b5. CLI ghi audit "result", trả `result.acknowledgement` (`run_id`, `site_id`, `plan_id`, `status`, `acknowledged_at`, `acknowledged_by`, `binding_now`, `switch_lock_released`, `next_allowed_sites[]`), thoát 0. Operator được chuyển lại chính site lỗi bằng lượt mới (`run_id` mới) hoặc chuyển site kế tiếp của `site_order`; mục P5 của site lỗi giữ `FAILED`, kế hoạch chỉ `completed` khi mục đó chạy lại `DONE` hoặc được `WAIVED` (`FR-UPG-SEQ-001`, `BR-PLAN-007`). Use case quay lại bước 1.
  - 2b6. Lượt không ở 3 trạng thái trên, hoặc đã có `acknowledged_at` (xác nhận lần 2): Hệ thống trả `ERR-UPG-409-04` (Low, mã thoát 2; mã đề xuất `CR-FR-01`); `switches/index.tsv` và `switch.json` không đổi.
  - 2b7. `run_id` không tồn tại, hoặc lý do < 20 ký tự, > 500 ký tự hay chứa ký tự điều khiển: CLI trả `ERR-CLI-400-01`; console trả `ERR-CON-404-01` (`run_id` không có) hoặc `ERR-CON-422-01` (lý do sai).
- **2c. Có lượt `ROLLBACK_FAILED` chưa được xác nhận trên máy**:
  - 2c1. Hệ thống trả `ERR-UPG-423-01` (Critical, kiểm trước `ERR-UPG-409-03` theo `FR-UPG-SEQ-001`); mọi lệnh chuyển site trên máy bị khoá.
  - 2c2. Operator khôi phục thủ công theo `backups/<run_id>/manifest`, rồi xác nhận lượt đó theo 2b2–2b7; CLI gỡ khoá `ERR-UPG-423-01` (`switch_lock_released = true`) khi máy không còn lượt `ROLLBACK_FAILED` nào chưa xác nhận.
- **2d. Chọn `--no-auto-rollback`**:
  - 2d1. Hệ thống yêu cầu xác nhận kép (gõ lại `site_id`) và ghi audit cả 2 bước (`BR-CON-006`, ngoại lệ `BR-SCN-010`).
- **3a. Dry-run không hợp lệ**:
  - 3a1. Console trả 428 `ERR-JOB-428-01`.
- **4a. Đang có lượt `SWITCHED`/`HC_RUNNING` hoặc khoá đang bị giữ**:
  - 4a1. CLI trả `ERR-ENV-409-01` "Site {site} đang trong thời gian kiểm tra sau chuyển; chờ {remaining} giây."
- **4b. Không ghi được audit intent**:
  - 4b1. CLI thoát 2 với `ERR-AUD-500-01`, `ABORTED`.
- **5a. Mục P3/P4 chưa `DONE`/`WAIVED`**:
  - 5a1. `ERR-SCN-424-01`, `ABORTED`.
- **5b. Kết luận tương thích không `PASS`**:
  - 5b1. `ERR-UPG-409-01` "Site {site} còn {errors} lỗi tương thích chưa xử lý."; Operator sửa mã hoặc miễn trừ (UC-PLAN-003).
- **5c. Nhánh đích `EOL`/`PRE_RELEASE`/Node.js `CURRENT` cho site production**:
  - 5c1. `ERR-SCN-409-02`, `ABORTED`.
- **5d. `$NEW_BIN` không tồn tại hoặc không chạy được**:
  - 5d1. `ERR-ENV-412-01`, `ABORTED`; Operator chạy UC-UPG-001.
- **5e. Site chạy `mod_php`**:
  - 5e1. `ERR-SCN-412-02`, `ABORTED`; Operator chạy UC-UPG-003 trước.
- **6a. Pool đích không qua kiểm cú pháp hoặc FPM đích không `active` sau 15 s**:
  - 6a1. `ERR-ENV-500-01`, `ABORTED`, site không đổi.
- **7a. FastCGI probe không đạt**:
  - 7a1. `ERR-HC-424-01` "Mã nguồn {site} lỗi khi chạy thử trên PHP {target}: {detail}. Site chưa bị thay đổi.", `ABORTED`.
- **7b. Không có Python 3 hoặc playbook không có pool FastCGI (LSAPI PB-008/PB-011, container PB-013)**:
  - 7b1. Bỏ bước probe; thiếu Python → cảnh báo `ERR-HC-424-02` (Low); xác minh thay thế ở C10.
- **8a. Không xác định được nguồn log lỗi của site**:
  - 8a1. `ERR-HC-412-01`, `ABORTED`; Operator đặt `error_log` cho pool hoặc khai báo `hc_log`.
- **8b. Baseline không hợp lệ (5 mẫu khác mã HTTP hoặc có 5xx)**:
  - 8b1. Trang chủ → `ERR-HC-412-02` (High), `ABORTED`; Operator sửa lỗi trên `$OLD` hoặc duyệt `hc_mode=skip` (chỉ `HC-C0`..`HC-C2` trên trang chủ trong 120 s, xác nhận kép).
  - 8b2. URL khai báo → loại URL khỏi tập, cảnh báo `ERR-HC-412-02` (Low).
- **8c. Baseline cũ > 120 s khi bắt đầu C7**:
  - 8c1. Hệ thống thu lại baseline (`BR-HC-004`).
- **9a. `STATE_DIR` còn < 50 MB**:
  - 9a1. `ERR-ENV-507-01`, `ABORTED`.
- **10a. Panel trả lỗi hoặc giá trị đọc lại khác giá trị mong muốn**:
  - 10a1. CLI khôi phục theo manifest, `ERR-ENV-502-01`.
- **11a. Kiểm cú pháp web server thất bại**:
  - 11a1. CLI khôi phục file trong ≤ 5 s, không reload, `ERR-ENV-500-02`.
- **12a. Reload thất bại**:
  - 12a1. CLI chạy rollback site R1–R7 (UC-UPG-004).
- **13a. `HC-C0` không đạt trong 10 s**:
  - 13a1. CLI tự rollback (lý do `HC-C0`), `ROLLED_BACK`, `ERR-SCN-500-01`.
- **14a. Vi phạm tiêu chí fail-fast (`HC-C1`, `C2`, `C3`, `C5`, `C7`, `C8` khi vượt, `C9`) hoặc `HC-C4`/`HC-C6` ở cuối cửa sổ, tự rollback bật**:
  - 14a1. CLI gọi rollback site bằng khoá site đang giữ, bắt đầu ≤ 5 s, hoàn tất ≤ 60 s (`FR-UPG-RBK-002`, `BR-HC-010`).
  - 14a2. Sau R6, CLI chạy 1 vòng thăm dò trên `$OLD`: mã HTTP mọi URL = baseline → `ROLLED_BACK`, phát `ERR-SCN-500-01` "Site {vhost} không đạt kiểm tra sau khi chuyển sang {target}; đã hoàn tác về {old}."; mục P5 `FAILED`.
  - 14a3. Các site còn lại của kế hoạch dừng; kế hoạch giữ `in_progress` (`T-PLN-08`); lệnh chuyển site kế tiếp trả `ERR-UPG-409-03` tới khi lượt được xác nhận (`BR-UPG-003`); job thoát 1.
  - 14a4. Operator xử lý nguyên nhân (sửa mã, bổ sung extension, cấu hình pool) rồi xác nhận lượt `ROLLED_BACK` theo 2b2–2b7; sau đó chuyển lại site này bằng lượt mới hoặc chuyển site kế tiếp.
- **14b. Vi phạm, `--no-auto-rollback` đã duyệt**:
  - 14b1. `status = HC_FAILED_KEPT`, phát `ERR-HC-500-01` (Critical); SCR-002 hiển thị dải cảnh báo kèm nút rollback tới khi Operator xử lý (UC-UPG-004); lệnh chuyển site kế tiếp trả `ERR-UPG-409-03`.
  - 14b2. Operator rollback thủ công (UC-UPG-004, lượt thành `ROLLED_BACK`) hoặc khắc phục lỗi và giữ site trên `$NEW`, rồi xác nhận lượt đó theo 2b2–2b7.
- **14c. Tự rollback thất bại hoặc site vẫn lỗi sau rollback**:
  - 14c1. `status = ROLLBACK_FAILED`, phát `ERR-HC-500-02` (Critical); khoá mọi lệnh chuyển site trên máy (`ERR-UPG-423-01`).
  - 14c2. Operator khôi phục site thủ công theo manifest rồi xác nhận lượt theo 2b2–2b7; khoá được gỡ như 2c2.
- **14d. Operator huỷ job trong cửa sổ health check**:
  - 14d1. Hệ thống dừng health check và rollback site với lý do `MANUAL` (`BR-JOB-004`).
- **14e. Tiến trình health check bị dừng giữa chừng (máy khởi động lại, `kill`)**:
  - 14e1. Lần chạy tool kế tiếp thấy lượt `HC_RUNNING` có `t_C9` cách hiện tại > 900 s (600 s + 300 s) chưa có kết luận → chạy lại health check đầy đủ với `baseline.json`; không rollback khi chưa có bằng chứng vi phạm (DOC-SRS-QP-ENV-002 §6.4).
- **16a. Job vượt 1.200 s**:
  - 16a1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-ENV-01`: C6–C10 ≤ 30 s P95 trên máy 2 vCPU / 2 GB RAM với ≤ 50 vhost.
- `NFR-ENV-03`: tự rollback bắt đầu ≤ 5 s, hoàn tất ≤ 60 s.
- `NFR-ENV-04`: graceful reload gây 0 phản hồi 5xx (20 request/giây trong 30 s quanh reload).
- `NFR-ENV-05`: 100% lượt chuyển có manifest trước C7; KR4.3: tỉ lệ site tự rollback ≤ 10% trên site đã đạt quét tương thích.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-UPG-002`, `BR-UPG-003`, `BR-UPG-005` | Điều kiện chuyển, dừng khi thất bại tới khi được xác nhận, phải thuộc kế hoạch | 2, 2b, 2c, 5, 14a–14c |
| `BR-ENV-002`, `BR-ENV-003`, `BR-ENV-005`, `BR-ENV-006`, `BR-ENV-007`, `BR-ENV-012` | Panel, tuần tự + canary, kiểm cú pháp, reload nhỏ nhất, pool riêng, đọc lại panel | 4, 6, 10–12 |
| `BR-SCN-007`, `BR-SCN-008`, `BR-SCN-010`, `BR-SCN-017`, `BR-SCN-018`, `BR-SCN-047` | Nhánh đích hợp lệ, duyệt từng site, tự hoàn tác, manifest, phụ thuộc mục, `mod_php` | 5, 9, 14 |
| `BR-HC-001`..`BR-HC-012` | Tập URL, chỉ GET, probe, baseline, log, P95, ngưỡng nội dung, chuỗi cấm, chống cache, tự rollback, bằng chứng, tải tối đa | 7, 8, 13–17 |
| `BR-CON-005`, `BR-CON-006`, `BR-JOB-004` | Dry-run, xác nhận kép, huỷ trong cửa sổ health check | 2, 3, 14d |
| `BR-JOB-002`, `BR-AUD-001`, `BR-SEC-006`, `BR-PLAN-007` | Khoá dùng chung khi xác nhận, audit intent/result, che bí mật trong lý do, điều kiện kết thúc kế hoạch khi mục P5 `FAILED` | 2b2–2b7, 2c2, 14a4, 14b2, 14c2 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | 1, 17, 2b2 |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | 1, 8 |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | 2b1, 2b5, 2c1, 3, 17 |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | 4–16 |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | 7 |
| `FR-UPG-HC-003` | Thu baseline | 8 |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | 10 |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | 14 |
| `FR-UPG-HC-005` | Ra quyết định sau health check | 15, 14a–14c |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | 13a, 14a |
| `FR-UPG-HC-006` | Báo cáo health check | 17 |
| `FR-UPG-ACK-001` | Xác nhận đã xử lý lượt chuyển thất bại (đề xuất, `CR-FR-01`) | 2b2–2b7, 2c2, 14a4, 14b2, 14c2 |

### Giao diện và API liên quan
- Màn hình: `SCR-009` Site & ánh xạ runtime (nút "Xác nhận đã xử lý"), `SCR-004` (mục P5), `SCR-011`, `SCR-006` (báo cáo health check), `SCR-007` (nút "Xác nhận đã xử lý" của lượt chuyển), dải cảnh báo `SCR-002`.
- API: `GET`/`PATCH /api/v1/sites/{site_id}` (`hc_url`), `POST /api/v1/jobs` (`migrate_switch`, `migrate_healthcheck --baseline-only`), `GET /api/v1/switches`, `GET /api/v1/switches/{run_id}`, `POST /api/v1/switches/{run_id}/acknowledgements` (hành động `switch_ack`, loại `control`; đề xuất `CR-FR-01`, DOC-SRS-QP-001 §3.3.3).

### Quan hệ với use case khác
- `<<include>>` UC-CON-003, UC-JOB-001; `<<extend>>` bởi UC-UPG-004 (rollback thủ công, kèm xác nhận lượt theo `FR-UPG-ACK-001`) và UC-JOB-002 (huỷ trong cửa sổ health check).
- Tiền đề: UC-UPG-001 (cài song song), UC-UPG-003 (khi site chạy `mod_php`), UC-PLAN-003 (P3/P4).

### Ghi chú và tài liệu tham chiếu
- Quy trình C1–C12, R1–R7: [environment-playbooks.md §5](../srs/environment-playbooks.md); tham số và tiêu chí health check: [environment-playbooks-healthcheck.md §2, §6](../srs/environment-playbooks-healthcheck.md); sơ đồ: [flows-upgrade.md §3](../srs/flows-upgrade.md).
- `ERR-UPG-409-03` định nghĩa chuẩn ở [error-matrix.md](../srs/error-matrix.md) §3.11 (từ bản 1.0.1). `FR-UPG-ACK-001` và `ERR-UPG-409-04` là đề xuất của [functional-requirements.md](../srs/functional-requirements.md) §15.1–§15.2 (`CR-FR-01`), chờ PO duyệt; PO từ chối → bỏ các bước 2b2–2b7, 2c2, 14a4, 14b2, 14c2. Điểm chờ PO: có yêu cầu xác nhận kép (`BR-CON-006`) khi xác nhận lượt lỗi của site canary không.
- Câu hỏi mở `Q-01` (ngưỡng health check), `CR-SRS-02` (số liệu `BR-SCN-009` trỏ sang DOC-SRS-QP-ENV-002), `Q-SRS-08` (CloudLinux, DirectAdmin `rewrite_confs`).
