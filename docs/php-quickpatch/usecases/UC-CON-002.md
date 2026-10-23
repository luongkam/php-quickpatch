---
id: DOC-UC-QP-CON-002
title: Đặc tả Use Case UC-CON-002 — Xem tổng quan máy chủ
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-CON-002, overview, dashboard, ranking, kev, eol, plan-deadline, freshness]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-002
  - DOC-API-QP-002
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-SCAN-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-CON-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-CON-OVW-001` thành "Hiển thị màn hình Tổng quan (SCR-002)" theo `functional-requirements.md` (`CR-FR-06`) |

## UC-CON-002: Xem tổng quan máy chủ

- **Tác nhân chính (Primary Actor)**: Operator root, Operator không root (`PER-01`, `PER-02`, `PER-03`) và Auditor chỉ xem (`PER-04`).
- **Tác nhân hỗ trợ**: không có; console đọc `STATE_DIR` (`state/last-scan.json`, `feeds/current/`, `plans/`, `switches/index.tsv`).
- **Phạm vi (Scope)**: console SCR-002 Tổng quan, API `GET /api/v1/overview`.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`, `PER-03`: trong 1 màn hình thấy số runtime theo trạng thái, finding KEV/Critical, danh sách xử lý xếp theo `R`, hạn duyệt kế hoạch, tuổi dữ liệu và tuổi kết quả scan; tới checklist kế hoạch ≤ 4 thao tác (`NFR-USE-002`).
  - `PER-04`: 100% runtime có ngày EOL ≤ 90 ngày hiển thị cảnh báo (KR2.3); nguồn dữ liệu lỗi được hiển thị kèm thời điểm dữ liệu cuối (KR5.3).
  - Operator trực sự cố: lượt chuyển `HC_FAILED_KEPT`/`ROLLBACK_FAILED` hiển thị ở dải cảnh báo đầu trang kèm nút rollback.
- **Tiền điều kiện (Pre-conditions)**:
  - Phiên console hợp lệ (UC-CON-001).
  - Có ít nhất 1 kết quả scan (`last-scan.json`); nếu chưa có, SCR-002 hiển thị trạng thái rỗng và nút "Quét lại".
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: SCR-002 hiển thị số liệu tính trên cùng `bundle_id`, kèm `bundle_id`, tuổi dữ liệu từng nguồn và tuổi kết quả scan.
  - **Đảm bảo tối thiểu**: màn hình chỉ đọc; 0 thay đổi trạng thái hệ thống do mở SCR-002 (`GET` không đổi trạng thái, `NFR-SEC-005`).
- **Kích hoạt (Trigger)**: Operator/Auditor đăng nhập xong hoặc chọn mục "Tổng quan" trên thanh điều hướng.

### Luồng sự kiện chính (Main Success Scenario)
1. Người dùng mở SCR-002; trình duyệt gọi `GET /api/v1/overview` bằng cookie phiên (`FR-CON-OVW-001`).
2. Hệ thống đọc `last-scan.json`, bundle `current/`, `plans/*/plan.json`, `switches/index.tsv`.
3. Hệ thống đếm runtime theo trạng thái `ok`, `ok-backport`, `vulnerable`, `eol`, và EOL ≤ 90 ngày; đếm finding KEV, Critical, dependency có lỗ hổng.
4. Hệ thống xếp hạng runtime, WordPress core và dependency findings theo `R` giảm dần, cùng `R` theo thứ tự KEV → `cvss_max` ≥ 9,0 → EOL → `cvss_max` 7,0–8,9 → EOL ≤ 90 ngày → còn lại; mỗi dòng có `object_ref`, `R`, mức (`CRITICAL` 70–100, `HIGH` 40–69, `MEDIUM` 20–39, `LOW` 0–19), `reason_codes[]` (`FR-ASMT-RANK-001`, `BR-ASMT-004`).
5. Hệ thống tính hạn duyệt kế hoạch: EOL − 30 ngày cho nhánh `SECURITY_ONLY`/`MAINTENANCE_LTS` hoặc còn ≤ 90 ngày tới EOL; cảnh báo từ EOL − 90 ngày; quá hạn chưa `approved` → cảnh báo `high` (`FR-PLAN-DL-001`, `BR-SCN-049`, `BR-SCN-029`).
6. Hệ thống gắn tuổi dữ liệu từng nguồn, lỗi nguồn và mức tươi tổng (`BR-FEED-005`).
7. Console hiển thị SCR-002: thẻ số liệu, bảng xếp hạng, hạn duyệt, khối nguồn dữ liệu, tuổi kết quả scan; nút "Quét lại" (UC-SCAN-001), nút đồng bộ dữ liệu (UC-FEED-001).
8. Người dùng chọn 1 dòng xếp hạng để mở SCR-003 (UC-ASMT-001) hoặc 1 kế hoạch để mở SCR-004.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Phiên hết hạn**:
  - 1a1. 401 `ERR-AUTH-401-02`; chuyển về SCR-001.
- **1b. Host sai**:
  - 1b1. 421 `ERR-CON-421-01`.
- **2a. Chưa có kết quả scan**:
  - 2a1. SCR-002 hiển thị trạng thái rỗng và nút "Quét lại".
- **2b. Kết quả scan cũ > 24 giờ**:
  - 2b1. Hệ thống hiển thị tuổi kết quả và nút "Quét lại" nổi bật (`FR-CON-OVW-001`).
- **3a. Có runtime `locked` (`UNKNOWN`/`PRE_RELEASE`)**:
  - 3a1. Thẻ trạng thái hiển thị số runtime bị khoá kèm `ERR-SCN-422-01`.
- **4a. Có finding KEV**:
  - 4a1. Finding đứng đầu bảng, hiển thị `dueDate` của KEV (`BR-SEC-001`).
- **5a. Kế hoạch quá hạn duyệt**:
  - 5a1. Dòng hạn duyệt hiển thị số ngày quá hạn, mức `high`.
- **6a. Dữ liệu `STALE` (> 7 ngày) hoặc `EXPIRED` (> 90 ngày)**:
  - 6a1. Dải cảnh báo `ERR-FEED-412-01` hoặc `ERR-SCN-503-01` (chỉ đề xuất vá cùng nhánh).
- **6b. Nguồn lỗi**:
  - 6b1. Khối nguồn dữ liệu hiển thị mã lỗi cuối (`ERR-FEED-503-01`, `ERR-FEED-429-01`…) và `fetched_at` cuối cùng.
- **7a. Có lượt chuyển `HC_FAILED_KEPT` hoặc `ROLLBACK_FAILED`**:
  - 7a1. Dải cảnh báo đầu trang hiển thị `ERR-HC-500-01` hoặc `ERR-HC-500-02` kèm nút rollback (UC-UPG-004) tới khi Operator xử lý.
- **7b. Auditor chỉ xem**:
  - 7b1. Auditor không bấm hành động ghi; console Phase 1 không phân vai trò, việc chỉ xem là quy ước vận hành (xem index §RBAC). Phase 2: vai trò Viewer bị chặn hành động ghi (`BR-FLT-008`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-001`: `GET /api/v1/overview` P95 ≤ 500 ms với 5 phiên × 2 request/giây.
- `NFR-PERF-007`: SCR-002 hiển thị ≤ 2 s qua tunnel 1 Mbit/s, RTT 100 ms.
- `NFR-USE-003`, `NFR-USE-004`: WCAG 2.1 AA (tương phản ≥ 4,5:1, 100% thao tác bằng bàn phím); bố cục 360–1.920 px không cuộn ngang.
- `NFR-REL-001`: hiển thị được khi PHP-FPM, Node.js, web server đều dừng.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-ASMT-004`, `BR-FEED-042`, `BR-SEC-001` | Thứ tự xếp hạng, phân mức, KEV | 4 |
| `BR-SCN-049`, `BR-SCN-029` | Hạn duyệt kế hoạch PHP/Node.js | 5 |
| `BR-FEED-005`, `BR-DATA-001` | Độ tươi dữ liệu | 6 |
| `BR-ASMT-003` | Số liệu trên cùng `bundle_id` | 7 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | 1–3, 6, 7 |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | 4 |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | 5 |

### Giao diện và API liên quan
- Màn hình: `SCR-002` Tổng quan.
- API: `GET /api/v1/overview`.

### Quan hệ với use case khác
- Điểm vào của UC-ASMT-001, UC-PLAN-001/002, UC-SCAN-001 ("Quét lại"), UC-FEED-001 ("Đồng bộ"), UC-UPG-004 (dải cảnh báo).

### Ghi chú và tài liệu tham chiếu
- Phân mức rủi ro: [data-sources-merge-risk.md §8.3](../srs/data-sources-merge-risk.md); `FR-CON-OVW-001`: [functional-requirements.md §9](../srs/functional-requirements.md).
