---
id: DOC-UC-QP-PLAN-002
title: Đặc tả Use Case UC-PLAN-002 — Duyệt kế hoạch nâng cấp
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PLAN-002, plan, approve, cancel, canary, stale, lifecycle]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-STATE-001
  - DOC-API-QP-001
  - DOC-API-QP-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-PLAN-001
  - DIAG-STATE-QP-PLAN-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PLAN-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-PLAN-STS-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Quản lý vòng đời kế hoạch" |

## UC-PLAN-002: Duyệt kế hoạch nâng cấp

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`) — người duyệt phải là actor có quyền thực thi các mục thay đổi hệ thống của kế hoạch (`BR-PLAN-003`, spec §2.3). Operator không root chỉ duyệt được kế hoạch mà mọi mục thay đổi thuộc phạm vi user sở hữu.
- **Tác nhân hỗ trợ**: không có tác nhân ngoài; console gọi CLI `plan approve|cancel` đồng bộ.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh plan approve|cancel|show`; console SCR-004 (nút "Duyệt kế hoạch", "Huỷ kế hoạch", đổi canary).
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: chỉ duyệt khi 100% site có kết quả quét tương thích phần chạy được trước khi cài, mục P1 `AUTO` đã `DONE`, tiền điều kiện đã kiểm (`BR-PLAN-003`); kế hoạch nâng nhánh PHP 8.2 được duyệt trước 2026-12-01 (KR2.2).
  - `PER-04`: mỗi lần duyệt, huỷ, đổi canary có bản ghi audit (actor, thời điểm UTC, `plan_id`) (`BR-AUD-001`).
  - Chủ site: kế hoạch lỗi thời (`stale`) không được duyệt, tránh chuyển site theo dữ liệu cũ (`BR-PLAN-006`).
- **Tiền điều kiện (Pre-conditions)**:
  - Kế hoạch ở `draft` (UC-PLAN-001).
  - Phiên console hợp lệ; request ghi qua kiểm CSRF.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `plan.json` có `status=approved`, người duyệt, thời điểm; `events.jsonl` và audit có bản ghi duyệt; SCR-004 mở các mục P2 để chạy.
  - **Đảm bảo tối thiểu**: khi không đạt điều kiện, trạng thái kế hoạch không đổi và lý do thiếu được trả về (`details.missing[]`).
- **Kích hoạt (Trigger)**: Operator bấm "Duyệt kế hoạch" trên SCR-004, hoặc chạy `plan approve <plan_id>`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở SCR-004; console đọc `plan.json`, `items.json` và kiểm điều kiện lỗi thời mỗi lần mở kế hoạch (`FR-PLAN-STS-001`, `BR-PLAN-006`).
2. Console hiển thị trạng thái `draft`, `stale=false`, hạn duyệt, kết luận tương thích từng site, tiền điều kiện, site canary (`FR-CON-PLAN-002`).
3. Operator rà soát checklist, (tuỳ chọn) đổi site canary, rồi bấm "Duyệt kế hoạch".
4. Console gửi `PATCH /api/v1/plans/{plan_id}` `{"status": "approved"}` kèm `X-QP-CSRF`, `Origin`; gọi CLI `plan approve <plan_id> --json` với argv cố định, `shell=False`, timeout 30 s (DOC-API-QP-001 §2.14).
5. CLI ghi audit intent (`FR-JOB-AUD-001`).
6. CLI kiểm `BR-PLAN-003`: kế hoạch không `stale`; phần quét tương thích chạy được trước khi cài đã có kết quả cho 100% site; mục P1 `AUTO` ở `DONE`; tiền điều kiện `FR-UPG-PRE-001` đã kiểm; người duyệt có quyền thực thi.
7. CLI đặt `status=approved`, ghi `events.jsonl`, audit result; thoát 0.
8. Console trả 200 `{status: approved}`; SCR-004 hiển thị kế hoạch `approved` và mở các mục P2 (cài song song hoặc vá cùng nhánh) để chạy (UC-PLAN-003).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Kế hoạch `stale`** (`scan_fingerprint` đổi; nhánh đích có KEV mới hoặc `R` của đích tăng ≥ 20; `catalog_version` của kịch bản liên quan đổi; nhánh đích chuyển `EOL`):
  - 1a1. SCR-004 hiển thị `stale_reasons[]`; nút duyệt trả `ERR-PLAN-410-01` "Kế hoạch đã lỗi thời ({reasons}); hãy sinh lại trước khi chuyển site."; Operator sinh lại (UC-PLAN-001), trạng thái mục đã `DONE` được giữ.
- **1b. `plan_id` không tồn tại**:
  - 1b1. Hệ thống trả `ERR-PLAN-404-01`.
- **1c. Quá hạn duyệt mà kế hoạch chưa `approved`**:
  - 1c1. SCR-002 và SCR-004 hiển thị cảnh báo mức `high` kèm số ngày quá hạn (`FR-PLAN-DL-001`, `BR-SCN-049`).
- **3a. Operator đổi site canary trước khi duyệt**:
  - 3a1. Console gửi `PATCH /api/v1/plans/{plan_id}` `{"canary_site_id"}`; CLI đặt canary mới, ghi audit đổi canary (`BR-PLAN-004`, `BR-AUD-001`); use case quay lại bước 3.
- **3b. Operator đổi canary sau khi kế hoạch đã `approved`**:
  - 3b1. Kế hoạch trở về `draft` (`BR-PLAN-004`), cần duyệt lại từ bước 3.
- **3c. Operator huỷ kế hoạch**:
  - 3c1. Console gửi `PATCH …` `{"status": "cancelled"}`; CLI chuyển `cancelled` khi không có job của kế hoạch đang `RUNNING` (`BR-PLAN-007`), ghi audit.
  - 3c2. Có job của kế hoạch đang `RUNNING` → `ERR-PLAN-409-02`; Operator chờ job kết thúc hoặc huỷ job (UC-JOB-002).
- **4a. Request thiếu `X-QP-CSRF` hoặc `Origin` sai**:
  - 4a1. Console trả `ERR-AUTH-403-01` hoặc `ERR-AUTH-403-02`, không gọi CLI.
- **4b. Khoá kế hoạch đang bị thao tác khác giữ quá 5 s**:
  - 4b1. Console trả 423 `ERR-CLI-423-01` (DOC-API-QP-001 §2.14); Operator thử lại.
- **5a. Không ghi được audit intent**:
  - 5a1. CLI huỷ thao tác, `ERR-AUD-500-01` (`BR-AUD-004`).
- **6a. Kế hoạch không ở `draft`**:
  - 6a1. Hệ thống trả `ERR-PLAN-409-02` "Không thể approve khi kế hoạch ở trạng thái {status}."
- **6b. Chưa đạt `BR-PLAN-003`**:
  - 6b1. Hệ thống trả `ERR-PLAN-412-01` "Chưa thể duyệt: {missing}." liệt kê site chưa có kết quả quét, mục P1 chưa `DONE`, tiền điều kiện chưa kiểm.
  - 6b2. Operator hoàn thành điều kiện còn thiếu (UC-PLAN-003) rồi quay lại bước 3.
- **6c. Người duyệt là tiến trình `serve` không root trong khi kế hoạch có mục cần root**:
  - 6c1. Nút "Duyệt kế hoạch" vô hiệu kèm lý do (`BR-CON-010`); qua API trả `ERR-PLAN-412-01` với `missing` = quyền thực thi.
- **8a. Kết thúc kế hoạch** (sau khi thực hiện):
  - 8a1. Mọi mục ở `DONE`/`SKIPPED`/`WAIVED` → kế hoạch `completed` (`BR-PLAN-007`).
  - 8a2. Có lượt chuyển `ROLLED_BACK` và Operator đóng kế hoạch kèm lý do → `rolled_back` (`BR-PLAN-007`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-002`: thao tác ghi P95 ≤ 1.500 ms tới khi trả kết quả.
- `NFR-REL-006`: 0 file `plan.json` hỏng sau 100 lần `kill -9` ngẫu nhiên (ghi tạm + `rename`).
- `NFR-SEC-005`: 100% request ghi bằng cookie thiếu `X-QP-CSRF` hoặc `Origin` sai bị từ chối.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-PLAN-003` | Điều kiện duyệt | 6 |
| `BR-PLAN-004` | Site canary, đổi sau duyệt → `draft` | 3a, 3b |
| `BR-PLAN-006` | Kế hoạch lỗi thời | 1 |
| `BR-PLAN-007` | Kết thúc/huỷ kế hoạch | 3c, 8a |
| `BR-SCN-049`, `BR-SCN-029` | Hạn duyệt kế hoạch nâng cấp PHP/Node.js | 1c |
| `BR-AUD-001`, `BR-AUD-004` | Ghi audit duyệt/huỷ/đổi canary; đóng khi lỗi | 5, 7 |
| `BR-CON-004`, `BR-CON-010` | Chống CSRF; quyền console | 4, 6c |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | 1, 6, 7, 8a |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | 2, 3, 8 |

### Giao diện và API liên quan
- Màn hình: `SCR-004` Kế hoạch nâng cấp & checklist; cảnh báo hạn duyệt trên `SCR-002`.
- API: `GET /api/v1/plans`, `GET /api/v1/plans/{plan_id}`, `PATCH /api/v1/plans/{plan_id}`.

### Quan hệ với use case khác
- Tiếp nối UC-PLAN-001; mở đường cho UC-PLAN-003, UC-UPG-001, UC-UPG-002.

### Ghi chú, mâu thuẫn và tài liệu tham chiếu
- Danh sách trắng `BR-CON-008` (spec §3.3.4) chưa có hành động `plan_approve`, `plan_cancel`, `plan_set_canary`; thiết kế API đề xuất bổ sung (DOC-API-QP-001 §2.14, DOC-SRS-QP-FLOW-001 §6.2 mục 3) — chờ BA + Dev.
- Sơ đồ trạng thái kế hoạch: [spec.md §4.1.1](../srs/spec.md), ma trận chuyển trạng thái: [states.md §3](../srs/states.md).
