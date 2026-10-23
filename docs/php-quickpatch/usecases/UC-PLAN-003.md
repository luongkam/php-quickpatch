---
id: DOC-UC-QP-PLAN-003
title: Đặc tả Use Case UC-PLAN-003 — Thực hiện và cập nhật checklist
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PLAN-003, checklist, auto, semi, manual, waive, lint, rector, compatibility-waiver]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-STATE-001
  - DOC-API-QP-001
  - DOC-API-QP-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-UPG-001
  - DIAG-STATE-QP-CHK-001
  - DIAG-STATE-QP-PLAN-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PLAN-003 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-CMPT-RCT-001` với SRS: "Chạy Rector tuỳ chọn trên bản sao" |

## UC-PLAN-003: Thực hiện và cập nhật checklist

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`) cho mục thay đổi hệ thống; Operator không root cho mục cấp dự án và mục `MANUAL`.
- **Tác nhân hỗ trợ**: System: Job runner (chạy mục `AUTO`/`SEMI`); `SYS-03` hạ tầng đích; lập trình viên của khách hàng (thực hiện mục `MANUAL` như sửa mã, nâng framework).
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh plan item|run`, console SCR-004 (bảng checklist), bản sao mã nguồn ngoài docroot cho Rector.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: chạy mục `AUTO`/`SEMI` bằng 1 nút qua dry-run + xác nhận; biết mục nào bị chặn bởi phụ thuộc; checklist tự cập nhật trạng thái khi job kết thúc.
  - `PER-04`: mục `WAIVED` có lý do ≥ 20 ký tự, mục `MANUAL` → `DONE` có bằng chứng ≥ 10 ký tự, mọi thay đổi trạng thái có audit (`BR-PLAN-005`).
  - Chủ site: không có thay đổi nào ghi vào docroot production; Rector chỉ ghi bản sao sau khi Operator duyệt diff (`BR-SCN-011`).
- **Tiền điều kiện (Pre-conditions)**:
  - Kế hoạch ở `approved` hoặc `in_progress` (UC-PLAN-002) để chạy mục thay đổi hệ thống; mục `MANUAL`/miễn trừ cập nhật được ở `draft`.
  - Kế hoạch không `stale` khi chạy mục P5 (`BR-PLAN-006`).
  - Phiên console hợp lệ.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: trạng thái mục (`PENDING` → `RUNNING` → `DONE`/`FAILED`, hoặc `SKIPPED`/`WAIVED`) được ghi vào `items.json`, `events.jsonl`, audit; sự kiện SSE `plan_item` cập nhật SCR-004; kế hoạch chuyển `in_progress` khi mục thay đổi hệ thống đầu tiên chạy; mọi mục kết thúc → kế hoạch `completed` (`BR-PLAN-007`).
  - **Đảm bảo tối thiểu**: mục không đủ điều kiện không chạy; job ghi có manifest và audit intent trước thay đổi.
- **Kích hoạt (Trigger)**: Operator bấm "Chạy" trên 1 mục `AUTO`/`SEMI`, "Đánh dấu hoàn thành" trên mục `MANUAL`, "Miễn trừ" trên mục hoặc hit tương thích; hoặc chạy `plan run <plan_id> <chk_id> [--dry-run] [--yes]` / `plan item <plan_id> <chk_id> --set done|fail|skip|waive [--reason TEXT]`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở checklist trên SCR-004, lọc theo giai đoạn P1–P7, site, trạng thái; hệ thống hiển thị mục bị chặn bởi phụ thuộc và nhãn "chưa kiểm chứng" (`FR-CON-PLAN-002`).
2. Operator chọn 1 mục `AUTO`/`SEMI` (vd P3 "kiểm tra cú pháp bằng binary đích") và bấm "Chạy".
3. Hệ thống kiểm phụ thuộc: mục P5 chỉ chạy khi mọi mục P3, P4 bắt buộc của cùng site ở `DONE`/`WAIVED` (`BR-SCN-018`); tra `cli_action` của mục trong danh sách trắng (`FR-PLAN-CHK-002`, `FR-CON-SAFE-003`).
4. Với mục `SEMI` hoặc mục thay đổi hệ thống, hệ thống chạy dry-run của mục và hiển thị SCR-011; Operator xác nhận trong ≤ 15 phút (UC-CON-003). Mục `AUTO` chỉ đọc (vd lint P3) bỏ qua bước này (`FR-PLAN-CHK-002`).
5. Console tạo job `plan run <plan_id> <chk_id> --yes --json`; hệ thống đặt mục `RUNNING`; kế hoạch `approved` chuyển `in_progress` khi đây là mục thay đổi hệ thống đầu tiên (`FR-PLAN-STS-001`).
6. Job thực thi mục. Với mục P3 lint: hệ thống chạy `$NEW_BIN -l` cho 100% file theo `BR-CMPT-001`, song song theo số vCPU, liệt kê `Parse error` (`FR-CMPT-CODE-003`); cập nhật kết luận tương thích site (`FR-CMPT-RES-001`).
7. Job kết thúc `SUCCEEDED`; hệ thống đặt mục `DONE`, ghi `events.jsonl`, audit, phát sự kiện SSE `plan_item` (`FR-PLAN-CHK-001`).
8. Với mục `MANUAL` (vd sửa mã theo hit tương thích, kiểm thử nghiệp vụ), Operator bấm "Đánh dấu hoàn thành" và nhập bằng chứng ≥ 10 ký tự đối chiếu `done_criteria`; hệ thống đặt `DONE` và ghi audit (`BR-PLAN-005`).
9. Hệ thống làm mới SCR-004: tiến độ theo giai đoạn, mục P5 của site mở khi P3, P4 đạt điều kiện.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. Mục `verified=false`**:
  - 2a1. Mục không chạy được ở mức `AUTO`; hiển thị lệnh kèm nhãn "chưa kiểm chứng" để Operator chạy thủ công rồi đánh dấu như mục `MANUAL` (`BR-ENV-010`).
- **2b. Console `serve` không root, mục cần root**:
  - 2b1. Nút "Chạy" vô hiệu kèm lý do; qua API trả 403 `ERR-CLI-403-01` (`BR-CON-010`, DOC-API-QP-001 §2.13.4).
- **3a. Mục phụ thuộc chưa `DONE`/`WAIVED`**:
  - 3a1. Hệ thống trả `ERR-SCN-424-01` "Chưa thể thực hiện {chk_id}: mục {dep_id} chưa hoàn thành."
- **3b. Kế hoạch `stale` khi chạy mục P5 chưa chạy**:
  - 3b1. Hệ thống trả `ERR-PLAN-410-01`; Operator sinh lại kế hoạch (UC-PLAN-001).
- **3c. Mục chuyển site khi kế hoạch chưa `approved`/`in_progress`**:
  - 3c1. Hệ thống trả `ERR-UPG-409-02` (`BR-UPG-005`).
- **3d. `plan_id`/`chk_id` không tồn tại hoặc sai regex**:
  - 3d1. Hệ thống trả `ERR-PLAN-404-01` hoặc `ERR-CON-422-01`.
- **4a. Không có dry-run hợp lệ (quá 15 phút, tham số khác, khác phiên, `bundle_id`/`scan_fingerprint` đổi)**:
  - 4a1. Console trả 428 `ERR-JOB-428-01`; Operator chạy lại dry-run (`BR-CON-005`).
- **5a. Đã có job cùng `plan_id` + `chk_id` đang chạy**:
  - 5a1. Console trả `ERR-JOB-409-01`.
- **6a. Chưa cài `$NEW_BIN` khi chạy lint**:
  - 6a1. Hệ thống trả `ERR-ENV-412-01`; phần lint giữ `PENDING` tới khi mục P2 cài song song `DONE` (UC-UPG-001).
- **6b. Lint tìm thấy `Parse error`**:
  - 6b1. Job thoát 1; mục `FAILED` kèm danh sách file/dòng; kết luận site `FAIL`; Operator sửa mã (mục `MANUAL`) hoặc miễn trừ hit (extension 8b) rồi chạy lại — mục `FAILED` được phép chuyển lại `RUNNING`.
- **6c. Job thất bại (thoát 2), vượt timeout hoặc bị gián đoạn**:
  - 6c1. Mục `FAILED` kèm `job_id`, lỗi `ERR-JOB-500-01`, `ERR-JOB-504-01` hoặc `ERR-JOB-500-02`.
- **6d. Operator bật bước tuỳ chọn Rector** (`FR-CMPT-RCT-001`, P2):
  - 6d1. Hệ thống tạo bản sao mã nguồn `$COPY` ngoài docroot, chạy Rector `--dry-run`, lưu `rector.diff` trong thư mục kế hoạch và hiển thị diff.
  - 6d2. Operator duyệt diff; hệ thống chỉ ghi thay đổi vào bản sao, không bao giờ ghi docroot production (`BR-SCN-011`); triển khai mã đã sửa là mục `MANUAL` của lập trình viên.
- **8a. Bằng chứng mục `MANUAL` < 10 ký tự, hoặc lý do miễn trừ < 20 ký tự**:
  - 8a1. Hệ thống trả `ERR-PLAN-422-01`.
- **8b. Operator miễn trừ mục hoặc hit tương thích mức `error`**:
  - 8b1. Operator nhập lý do ≥ 20 ký tự; mục → `WAIVED` (`plan item … --set waive`) hoặc hit được miễn trừ qua `POST /api/v1/plans/{plan_id}/compatibility-waivers`; hệ thống ghi audit và tính lại kết luận site (`BR-UPG-002`, `FR-CMPT-RES-001`).
- **8c. Hành động không hợp lệ với trạng thái mục/kế hoạch** (vd đặt `DONE` cho mục `SKIPPED`):
  - 8c1. Hệ thống trả `ERR-PLAN-409-02`.
- **9a. Mọi mục ở `DONE`/`SKIPPED`/`WAIVED`**:
  - 9a1. Kế hoạch chuyển `completed` (`BR-PLAN-007`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-002`: cập nhật trạng thái mục P95 ≤ 1.500 ms; `NFR-PERF-003`: sự kiện tiến độ hiển thị ≤ 2 s.
- `NFR-USE-006`: dry-run của mục ghi hiển thị đủ 4/4 mục (thay đổi, đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác).
- `NFR-REL-002`: 100% job ghi có audit intent trước thay đổi và audit result khi kết thúc.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCN-018` | Thứ tự phụ thuộc mục | 3 |
| `BR-PLAN-005` | Trạng thái mục, lý do miễn trừ ≥ 20 ký tự, bằng chứng `MANUAL` ≥ 10 ký tự | 7, 8 |
| `BR-PLAN-006`, `BR-PLAN-007` | Kế hoạch lỗi thời; kết thúc kế hoạch | 3b, 9a |
| `BR-SCN-008`, `BR-CON-005` | Mục `SEMI` duyệt riêng; dry-run trước thay đổi | 4 |
| `BR-SCN-042`, `BR-CMPT-001`, `BR-UPG-002` | Điều kiện ĐẠT quét tương thích, tập file, miễn trừ hit | 6, 8b |
| `BR-SCN-011` | Rector chỉ trên bản sao, duyệt diff | 6d |
| `BR-ENV-010`, `BR-CON-010` | Lệnh chưa kiểm chứng; quyền console | 2 |
| `BR-UPG-005` | Chuyển site phải thuộc kế hoạch | 3c |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | 1, 8, 9 |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | 2–5 |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | 6 |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | 7, 8 |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | 6d |

### Giao diện và API liên quan
- Màn hình: `SCR-004` (bảng checklist), `SCR-011` (dry-run + xác nhận), `SCR-006` (log job).
- API: `GET /api/v1/plans/{plan_id}/checklist-items`, `PATCH /api/v1/plans/{plan_id}/checklist-items/{chk_id}`, `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`, `GET /api/v1/plans/{plan_id}/compatibility`, `POST /api/v1/plans/{plan_id}/compatibility-waivers`.

### Quan hệ với use case khác
- `<<include>>` UC-CON-003 (dry-run + xác nhận) và UC-JOB-001 (theo dõi job).
- Mục P2 gọi UC-PTCH-001 (vá cùng nhánh) hoặc UC-UPG-001 (cài song song); mục P5 gọi UC-UPG-002, UC-UPG-005, UC-UPG-006; mục P7 gọi UC-UPG-007.

### Ghi chú và tài liệu tham chiếu
- Giai đoạn và loại mục: [version-scenarios-common.md §3](../srs/version-scenarios-common.md); máy trạng thái mục: [states.md §5](../srs/states.md).
- Câu hỏi mở `Q-02` (Rector, P2) — đề xuất của SRS: có, chỉ chạy trên bản sao, luôn dry-run + duyệt diff.
