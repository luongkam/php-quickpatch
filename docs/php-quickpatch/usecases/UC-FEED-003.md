---
id: DOC-UC-QP-FEED-003
title: Đặc tả Use Case UC-FEED-003 — Xem trạng thái và kiểm tra toàn vẹn nguồn dữ liệu
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FEED-003, feeds, status, verify, freshness, integrity, auditor]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-FEED-001
  - DIAG-STATE-QP-FEED-002
  - DIAG-SEQ-QP-FEED-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FEED-003 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Thêm `DIAG-SEQ-QP-FEED-002` vào `related_diagrams` và mục tham chiếu (khớp flows.md §1.7, spec.md bảng sơ đồ); sửa theo review: đồng bộ tên `FR-CON-FEED-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Hiển thị màn hình Nguồn dữ liệu (SCR-008)" |

## UC-FEED-003: Xem trạng thái và kiểm tra toàn vẹn nguồn dữ liệu

- **Tác nhân chính (Primary Actor)**: Auditor (`PER-04` kỹ sư bảo mật/kiểm toán, chỉ xem) hoặc Operator (`PER-01`).
- **Tác nhân hỗ trợ**: không có tác nhân ngoài; lệnh chỉ đọc `STATE_DIR/feeds/`.
- **Phạm vi (Scope)**: `php-quickpatch.sh feeds status [--json]`, `feeds verify [--snapshot FILE]`; console SCR-008, dải tuổi dữ liệu trên SCR-002.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-04`: biết từng nguồn đang `OK`/`DEGRADED`/`FAILED`/`DISABLED`, tuổi dữ liệu, TTL, số bản ghi, lỗi cuối và `data_origin` để đưa vào báo cáo bằng chứng.
  - `PER-01`: biết dữ liệu dùng để đánh giá còn trong mức `FRESH`/`AGING` (≤ 168 giờ) trước khi vá hoặc lập kế hoạch (`BR-FEED-005`).
  - Kỹ sư bảo mật: phát hiện 100% file bundle hoặc raw bị sửa so với `SHA256SUMS`/`.meta.json` (`BR-FEED-010`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có thư mục `feeds/` (bundle `current/` từ đồng bộ hoặc snapshot).
  - Console: phiên đăng nhập hợp lệ (UC-CON-001).
  - `feeds verify` cần quyền đọc `feeds/current/` và `feeds/raw/`.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: Operator/Auditor nhận bảng trạng thái nguồn và mức độ tươi tổng (`FRESH`, `AGING`, `STALE`, `EXPIRED`); `feeds verify` báo khớp/lệch từng file.
  - **Đảm bảo tối thiểu**: `feeds status` không thay đổi dữ liệu; `feeds verify` chỉ dựng lại bundle từ raw khi phát hiện lệch (DOC-SRS-QP-FEED-003 §4.3).
- **Kích hoạt (Trigger)**: Operator/Auditor mở SCR-008, hoặc chạy `feeds status` / `feeds verify`.

### Luồng sự kiện chính (Main Success Scenario)
1. Auditor mở SCR-008; console gọi `GET /api/v1/feeds`, đọc kết quả `feeds status --json` (`FR-CON-FEED-001`).
2. Hệ thống đọc `feeds/state/sync-status.json` và `current/manifest.json` (`FR-FEED-CMD-002`).
3. Hệ thống tính tuổi từng nguồn, phân mức độ tươi theo `BR-FEED-005`: `FRESH` (≤ TTL), `AGING` (TTL < tuổi ≤ 168 giờ), `STALE` (168 < tuổi ≤ 2.160 giờ), `EXPIRED` (> 2.160 giờ); nguồn tuỳ chọn đang tắt không tính tuổi (`FR-FEED-AGE-001`).
4. Hệ thống hiển thị: `bundle_id`, thời điểm tạo bundle, snapshot nền; bảng `SRC-001..017` (trạng thái, lần lấy thành công UTC, tuổi, TTL, số bản ghi, lỗi cuối, `data_origin`); lịch đồng bộ và lần chạy kế tiếp; trạng thái SHA-256 của snapshot đóng gói.
5. Auditor (có quyền shell trên máy chủ) hoặc Operator chạy `php-quickpatch.sh feeds verify` trên terminal SSH; console Phase 1 chỉ hiển thị trạng thái, không có nút kiểm toàn vẹn (DOC-API-QP-001 §5: `feeds verify` chỉ có ở CLI).
6. Hệ thống so `current/SHA256SUMS` với file thực tế và so `.meta.json.sha256` với từng file raw (`FR-FEED-CMD-003`, `BR-FEED-010`).
7. Hệ thống báo 100% file khớp, mã thoát 0.
8. Auditor ghi nhận `bundle_id`, tuổi dữ liệu vào hồ sơ kiểm toán hoặc xuất báo cáo (UC-RPT-001).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Gọi bằng CLI**:
  - 1a1. `feeds status` in bảng văn bản; `--json` in tài liệu `qp.feeds.status/1` (`BR-FEED-059`); mã thoát 0 khi `FRESH`/`AGING`, 1 khi `STALE`, 2 khi `EXPIRED` hoặc không có bundle (DOC-SRS-QP-FEED-003 §6.3).
- **1b. Phiên console hết hạn hoặc Host không hợp lệ**:
  - 1b1. Console trả `ERR-AUTH-401-02` (chuyển về SCR-001) hoặc `ERR-CON-421-01`.
- **2a. Không có bundle `current/` và không có snapshot hợp lệ**:
  - 2a1. Hệ thống hiển thị "không có dữ liệu", `freshness=EXPIRED`, mã thoát 2; đề xuất UC-FEED-001 hoặc UC-FEED-004.
- **3a. Mức `STALE`**:
  - 3a1. Hệ thống hiển thị cảnh báo `ERR-FEED-412-01` kèm nguồn cũ nhất (`BR-DATA-001`).
- **3b. Mức `EXPIRED`**:
  - 3b1. Hệ thống hiển thị `ERR-SCN-503-01`: tạm ngừng đề xuất nâng nhánh, chỉ cho vá cùng nhánh.
- **4a. Nguồn ở `FAILED`/`DEGRADED`**:
  - 4a1. Cột "Lỗi cuối" hiển thị mã lỗi (`ERR-FEED-503-01`, `ERR-FEED-429-01`, `ERR-FEED-401-01`, `ERR-FEED-502-01`, `ERR-FEED-502-02`) và nguồn dự phòng đang dùng.
- **4b. Đang có lượt `feeds update` chạy**:
  - 4b1. Hệ thống hiển thị PID và tiến độ; thao tác đồng bộ mới bị từ chối với `ERR-FEED-423-01` khi khoá giữ > 30 s.
- **6a. `feeds verify --snapshot FILE`**:
  - 6a1. Hệ thống kiểm gói snapshot chỉ định theo DOC-SRS-QP-FEED-003 §4.3 (SHA-256 toàn gói, `SHA256SUMS`, đường dẫn trong tar), không thay `current/`.
- **6b. Phát hiện ≥ 1 file lệch hash**:
  - 6b1. Hệ thống ghi `ERR-FEED-422-02` (Critical), liệt kê file lệch.
  - 6b2. Hệ thống tự dựng lại bundle từ `raw/` theo thay thế nguyên tử (`FR-FEED-CACH-002`); raw cũng lệch → giữ bundle hiện tại, đánh dấu lỗi, đề xuất đồng bộ lại (UC-FEED-001) hoặc nhập snapshot (UC-FEED-004); thoát 2.
- **6c. Auditor không có quyền đọc `feeds/` của root (console `serve` không root)**:
  - 6c1. Hệ thống chỉ hiển thị cache riêng của user đang chạy `serve` (spec §2.3).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-001`: API đọc `GET /api/v1/feeds` P95 ≤ 500 ms với 5 phiên đồng thời × 2 request/giây.
- `NFR-FEED-006`: tuổi dữ liệu ≤ 6 giờ 15 phút tại 99% thời điểm (chỉ số hiển thị trên SCR-008).
- `NFR-USE-005`: 100% thông báo lỗi có localization key, bản tiếng Việt và tiếng Anh.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FEED-005`, `BR-DATA-001` | Phân mức tươi và cảnh báo tuổi dữ liệu | 3 |
| `BR-FEED-010` | Toàn vẹn bundle/snapshot | 6 |
| `BR-FEED-051` | Dựng lại bundle nguyên tử khi lệch | 6b |
| `BR-FEED-059` | Tương thích ngược schema `qp.feeds.status/1` | 1a |
| `BR-CON-010` | Quyền console = quyền tiến trình `serve` | 6c |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | 1, 4 |
| `FR-FEED-CMD-002` | Lệnh `feeds status` | 2, 4 |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | 3 |
| `FR-FEED-CMD-003` | Lệnh `feeds verify` | 5–7 |

### Giao diện và API liên quan
- Màn hình: `SCR-008` Nguồn dữ liệu; dải tuổi dữ liệu trên `SCR-002`.
- API: `GET /api/v1/feeds`.

### Quan hệ với use case khác
- `<<extend>>` bởi UC-FEED-001 khi Auditor/Operator chọn "Đồng bộ ngay" từ SCR-008.
- Kết quả là đầu vào bằng chứng cho UC-RPT-001.

### Ghi chú và tài liệu tham chiếu
- Định dạng đầu ra `feeds status`: [data-sources-cache-cli.md §6.4](../srs/data-sources-cache-cli.md); kiểm toàn vẹn: §4.3.
- Sơ đồ tuần tự: `DIAG-SEQ-QP-FEED-002` ([flows.md §2.1](../srs/flows.md)), bước console gọi `GET /api/v1/feeds` và chạy `feeds status --json` (bước 1–4 của UC này).
- Ghi chú lệch: danh sách trắng console (spec §3.3.4) và thiết kế API (DOC-API-QP-001) không có hành động `feeds_verify`, nên Auditor chỉ xem được trạng thái trên console; kiểm toàn vẹn cần quyền shell. Đề xuất bổ sung hành động đọc `feeds_verify` vào `BR-CON-008` (chờ BA + Dev duyệt).
