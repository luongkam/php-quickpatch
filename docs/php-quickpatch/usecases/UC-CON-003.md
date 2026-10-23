---
id: DOC-UC-QP-CON-003
title: Đặc tả Use Case UC-CON-003 — Xem trước dry-run và xác nhận thao tác thay đổi
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-CON-003, dry-run, confirm, double-confirm, whitelist, argv, subprocess]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-API-QP-001
  - DOC-API-QP-004
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-CON-003 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đổi tên `FR-CON-SAFE-003` thành "Kiểm tra hành động theo danh sách trắng và tham số" (`CR-FR-06`); nhánh 8b1 bỏ `feeds_import` khỏi ngoại lệ (theo `BR-CON-005` 1.0.1: bắt buộc dry-run, xác nhận cùng SHA-256 và `force`), thêm ngoại lệ 3 thao tác điều khiển đồng bộ (`control`, `BR-JOB-003`); Phạm vi thêm `feeds_import`, quan hệ thêm UC-FEED-004, API thêm endpoint mặt tiền `POST /api/v1/feed-snapshots`; ghi chú danh sách trắng cập nhật theo spec.md §3.3.4 1.1.0 |

## UC-CON-003: Xem trước dry-run và xác nhận thao tác thay đổi

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`, `PER-03`).
- **Tác nhân hỗ trợ**: System: Job runner (chạy job dry-run và job ghi); CLI `php-quickpatch.sh`.
- **Phạm vi (Scope)**: hộp thoại SCR-011, cổng D (dry-run) và cổng G5 (danh sách trắng) của `qp-console.py`; áp cho mọi hành động ghi: `fix`, `rollback_run`, `feeds_schedule`, `plan_run_item` (mục thay đổi hệ thống), `migrate_install`, `migrate_switch`, `migrate_rollback`, `migrate_remove_old`, `feeds_import` (qua endpoint mặt tiền `POST /api/v1/feed-snapshots`, UC-FEED-004).
- **Cấp độ (Level)**: Fish Level (sub-function, được include bởi các use case thay đổi hệ thống).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: trước mọi thao tác ghi thấy 4/4 mục: thay đổi theo dry-run, đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác (`NFR-USE-006`); xác nhận bằng 1 nút (hoặc gõ lại `site_id`/nhánh/`runtime_id` với hành động toàn máy chủ).
  - Kỹ sư bảo mật: 100% tham số sai danh sách trắng/regex trả 422 và không tạo tiến trình khi fuzz 1.000 giá trị (`NFR-SEC-008`); 0 `shell=True`, `os.system`, `os.popen`, `eval`, `exec` (`NFR-SEC-007`).
  - Chủ site: job ghi chỉ chạy khi dry-run cùng tham số đã `SUCCEEDED` ≤ 15 phút trước và trạng thái máy (`bundle_id`, `scan_fingerprint`) không đổi (`BR-CON-005`).
- **Tiền điều kiện (Pre-conditions)**:
  - Phiên console hợp lệ; request ghi qua kiểm CSRF (UC-CON-001).
  - Hành động có trong danh sách trắng `BR-CON-008`.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: job ghi được tạo (202 `{job_id}`) với `confirm_dry_run_job_id` hợp lệ; audit intent do CLI ghi trước thay đổi.
  - **Đảm bảo tối thiểu**: khi không đạt cổng D hoặc G5, 0 tiến trình ghi được tạo; dry-run ghi 0 thay đổi, không ghi manifest (`BR-CLI-003`).
- **Kích hoạt (Trigger)**: Operator bấm 1 nút hành động ghi trên SCR-003, SCR-004, SCR-005, SCR-007, SCR-008 hoặc SCR-009.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator bấm nút hành động ghi; trình duyệt gửi `POST /api/v1/jobs` `{"action", "params", "dry_run": true}` kèm `X-QP-CSRF`.
2. Hệ thống tra `action` trong danh sách trắng, kiểm từng tham số bằng regex/enum (`site_id`, nhánh PHP `^[4-9]\.[0-9]$`, dòng Node.js `^[0-9]{1,2}$`, `run_id`, `plan_id`, `runtime_id`, `chk_id`), từ chối giá trị bắt đầu bằng `-` (`FR-CON-SAFE-003`, `BR-CON-008`).
3. Hệ thống dựng argv cố định (đường dẫn script tuyệt đối xác định lúc `serve` khởi động), tạo job `read` và chạy `subprocess.Popen(argv, shell=False, stdin=DEVNULL, close_fds=True, start_new_session=True, env=<danh sách trắng>, cwd=STATE_DIR)` với `--dry-run`.
4. CLI chạy chế độ dry-run: in hành động dự kiến, 0 thay đổi, không ghi manifest; trả `result.preview` và `result.fingerprint` (`bundle_id`, `scan_fingerprint`).
5. Console mở SCR-011 hiển thị 4/4 mục: file sẽ đổi, gói sẽ cài/nâng, dịch vụ sẽ reload/restart, site/đối tượng bị ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác (`FR-CON-SAFE-001`).
6. Operator bấm "Xác nhận" trong ≤ 15 phút.
7. Trình duyệt gửi `POST /api/v1/jobs` `{"action", "params" giống hệt, "dry_run": false, "confirm_dry_run_job_id"}`.
8. Hệ thống kiểm cổng D: job dry-run tồn tại, cùng `action`; `params` sau chuẩn hoá giống hệt; cùng phiên; tạo ≤ 15 phút trước; `SUCCEEDED`; `bundle_id` và `scan_fingerprint` không đổi (`BR-CON-005`).
9. Hệ thống tạo job ghi qua hàng đợi (UC-JOB-001), trả 202 `{job_id}` trong P95 ≤ 1.500 ms (`NFR-PERF-002`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. `action` không có trong danh sách trắng, tham số sai regex/enum, hoặc bắt đầu bằng `-`**:
  - 2a1. 422 `ERR-CON-422-01` "Tham số {field} không hợp lệ."; không ghi giá trị vào log; 0 tiến trình.
- **2b. Hành động cần root khi `serve` không root**:
  - 2b1. Nút vô hiệu kèm lý do (`BR-CON-010`); qua API: 403 `ERR-CLI-403-01` ở cổng J (DOC-API-QP-001 §2.13.4).
- **3a. Đã có job cùng hành động + đối tượng đang `QUEUED`/`RUNNING`, hoặc hàng đợi 20 job**:
  - 3a1. 409 `ERR-JOB-409-01` hoặc 429 `ERR-JOB-429-01`.
- **4a. Dry-run thất bại (thoát 2)**:
  - 4a1. SCR-011 hiển thị lỗi đầu tiên `ERR-JOB-500-01`, nút "Xác nhận" vô hiệu.
- **4b. Dry-run kết thúc `SUCCEEDED_WITH_ISSUES` (vd `fix` trên runtime chưa vá thoát 1)**:
  - 4b1. Hệ thống chấp nhận khi có `result.preview` và `result.errors[]` rỗng (đề xuất DOC-API-QP-001 §6.2 mục 3, chờ PO + Dev).
- **5a. Hành động tác động toàn máy chủ hoặc không hoàn tác được** (PB-006 bước 1, `migrate remove-old`, `--no-auto-rollback`, `feeds update --accept-shrink`, `hc_mode=skip`):
  - 5a1. SCR-011 yêu cầu gõ lại `site_id`, nhánh hoặc `runtime_id` (`confirm_retype`); hệ thống ghi audit cả 2 bước (`BR-CON-006`).
- **6a. Operator đóng hộp thoại hoặc quá 15 phút**:
  - 6a1. Không tạo job ghi; lần xác nhận sau trả 428 `ERR-JOB-428-01` (`details.constraint=expired`); Operator chạy lại dry-run.
- **8a. `params` khác, khác phiên, khác `action`, `bundle_id`/`scan_fingerprint` đổi, hoặc gõ lại sai**:
  - 8a1. 428 `ERR-JOB-428-01` với `details.constraint` ∈ {`missing`, `action_mismatch`, `params_mismatch`, `other_session`, `expired`, `not_succeeded`, `fingerprint_changed`, `retype_required`, `retype_mismatch`}.
- **8b. Ngoại lệ không cần dry-run**:
  - 8b1. Chỉ 3 ngoại lệ của `BR-CON-005`: (1) rollback do health check tự kích hoạt (trong CLI); (2) huỷ job; (3) thao tác điều khiển đồng bộ loại `control` (`BR-JOB-003`: `plan_approve`, `plan_cancel`, `plan_complete`, `plan_close_rolled_back`, `plan_set_canary`, `plan_item_set`, `plan_waive_hits`, `site_set_hc_urls`) — không tạo job, vẫn qua kiểm Host, phiên, CSRF, danh sách trắng, xác nhận kép khi thuộc `BR-CON-006` và ghi audit.
  - 8b2. Nhập snapshot (`feeds_import`) KHÔNG thuộc ngoại lệ: bắt buộc dry-run qua `POST /api/v1/feed-snapshots?dry_run=true`; bước xác nhận tải lại file, cổng D so thêm SHA-256 nội dung nhận và giá trị `force` với job dry-run (UC-FEED-004 bước 4–9).
- **9a. Thiếu CSRF/Origin sai**:
  - 9a1. 403 `ERR-AUTH-403-01` hoặc `ERR-AUTH-403-02`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-USE-006`: 4/4 mục trên SCR-011 cho mọi thao tác ghi.
- `NFR-SEC-007`, `NFR-SEC-008`: không thực thi chuỗi lệnh tự do; fuzz 1.000 giá trị → 100% trả 422.
- `NFR-PERF-002`: tạo job P95 ≤ 1.500 ms.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-CON-008` | Danh sách trắng lệnh, regex tham số, biến môi trường | 2, 3 |
| `BR-CON-005` | Dry-run hợp lệ ≤ 15 phút, cùng tham số, cùng phiên | 8 |
| `BR-CON-006` | Xác nhận kép | 5a |
| `BR-CON-010` | Quyền console | 2b |
| `BR-JOB-003` | Mọi job `--dry-run` là `read` | 3 |
| `BR-CLI-003` | `--dry-run` → 0 thay đổi | 4 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | 2, 3 |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | 4–9 |

### Giao diện và API liên quan
- Màn hình: `SCR-011` Hộp thoại xem trước dry-run & xác nhận.
- API: `POST /api/v1/jobs` (`dry_run=true`) → `GET /api/v1/jobs/{job_id}` (`result.preview`) → `POST /api/v1/jobs` (`confirm_dry_run_job_id`, `confirm_retype`); `feeds_import`: `POST /api/v1/feed-snapshots?dry_run=true` → `POST /api/v1/feed-snapshots?confirm_dry_run_job_id=<dry_job_id>` (DOC-API-QP-001 §2.13.3).

### Quan hệ với use case khác
- Được `<<include>>` bởi UC-PTCH-001..004, UC-PLAN-003, UC-UPG-001..007, UC-FEED-002, UC-FEED-004.
- `<<include>>` UC-JOB-001 (chạy job dry-run và job ghi).

### Ghi chú và tài liệu tham chiếu
- Giao thức dry-run → xác nhận: [api-spec.md §2.13.3](../api/api-spec.md); danh sách trắng: [spec.md §3.3.4](../srs/spec.md).
- Đã quyết: danh sách trắng spec.md §3.3.4 bản 1.1.0 đã có nhóm `control` (8 hành động điều khiển kế hoạch/site, `CR-SRS-10`) và `feeds_import` với `--dry-run`; `BR-CON-005` 1.0.1 (DOC-SRS-QP-BR-001 §6 mục 2) bỏ ngoại lệ `feeds_import`. `migrate ack` (`switch_ack`) vẫn là đề xuất `CR-FR-01`.
