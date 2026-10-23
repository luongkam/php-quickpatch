---
id: DOC-UC-QP-ASMT-002
title: Đặc tả Use Case UC-ASMT-002 — Xem findings thư viện và WordPress
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-ASMT-002, dependency, composer, npm, osv, malware, wordpress, findings]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-002
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-ASMT-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-DEP-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Hiển thị màn hình Findings thư viện (SCR-005)" |

## UC-ASMT-002: Xem findings thư viện và WordPress

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01` người vận hành VPS, `PER-03` DevOps Docker); Auditor (`PER-04`) xem kết quả.
- **Tác nhân hỗ trợ**: `SYS-02` OSV (`SRC-007`, nhận danh sách tên + phiên bản package) và wordpress.org (`SRC-012`); System: Job runner.
- **Phạm vi (Scope)**: phần đánh giá dependency của `scan` (`--only composer,npm,wp`), console SCR-005.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-03`: biết từng dự án có package nào dính advisory (mã, mức, KEV, bản sửa), package mã độc `MAL-*`, phiên bản WordPress dưới mốc vá.
  - Kỹ sư bảo mật: package `MAL-*` luôn ở mức Critical kèm khuyến nghị gỡ package và xoay vòng mọi secret trên máy (`BR-SEC-004`).
  - Chủ ứng dụng: chỉ OSV nhận danh sách package/phiên bản; chỉ `api.wordpress.org` nhận phiên bản WordPress + PHP; `--offline` không gửi dữ liệu (`BR-FEED-013`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có kết quả kiểm kê dự án (`FR-SCAN-PRJ-001`) với `composer.lock`, `package-lock.json` hoặc `wp-includes/version.php`.
  - Có mạng tới OSV, hoặc có cache OSV ≤ 7 ngày theo SHA-256 lockfile, hoặc snapshot biến thể `full` (Packagist).
  - Console: phiên hợp lệ.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `result.dependency_findings[]` và `result.wordpress_findings[]` trong `last-scan.json`; SCR-005 hiển thị findings nhóm theo dự án; mỗi finding có mức theo `BR-ASMT-005`.
  - **Đảm bảo tối thiểu**: lockfile không tra được được liệt kê kèm lý do (`ERR-FEED-503-02`); 0 file dự án bị ghi.
- **Kích hoạt (Trigger)**: Operator mở SCR-005, hoặc chạy `scan --only composer,npm,wp [--path DIR] --json`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator mở SCR-005; console gọi `GET /api/v1/dependency-findings` đọc kết quả scan gần nhất (`FR-CON-DEP-001`).
2. (Trong lượt scan) Hệ thống đọc danh sách `name version` từ `composer.lock`/`package-lock.json` của từng dự án như v0.1 `deps_of`.
3. Hệ thống tra OSV `querybatch` theo lô ≤ 500 package, xử lý `next_page_token`, tải chi tiết advisory mới, cache kết quả 6 giờ theo SHA-256 lockfile (`FR-FEED-OSV-001`).
4. Hệ thống tính mức từng advisory: CVSS v3.1 (Critical ≥ 9,0; High 7,0–8,9; Medium 4,0–6,9; Low 0,1–3,9), không có điểm → điểm thay thế `BR-FEED-043`, `MAL-*` → Critical; gắn cờ KEV và danh sách bản sửa (`FR-ASMT-DEP-001`, `BR-ASMT-005`).
5. Hệ thống đánh giá WordPress core: đọc `wp-includes/version.php`, so với `min_patched_sec` của nhánh theo `SRC-012` (bản nhỏ nhất có `wp_status ≠ insecure`), gắn KEV, tính `R` (`FR-ASMT-DEP-002`, `BR-FEED-025`).
6. Hệ thống ghi `dependency_findings[]` (`project_id`, `ecosystem`, `package`, `version`, `advisories[]`, `severity`, `in_kev`, `is_malware`, `fixed_versions[]`) và `wordpress_findings[]` vào kết quả scan.
7. Console hiển thị SCR-005 nhóm theo dự án: hệ sinh thái, package, phiên bản, advisory, mức, KEV, `MAL-*`, bản sửa, tuổi dữ liệu; nút "Vá dự án" mở UC-PTCH-002 qua dry-run + xác nhận.
8. Operator lọc theo mức/hệ sinh thái/dự án và chọn hành động tiếp theo.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Chưa có kết quả scan hoặc kết quả cũ > 24 giờ**:
  - 1a1. SCR-005 hiển thị nút "Quét lại" (UC-SCAN-001 với `--only composer,npm,wp`).
- **2a. Dự án dùng `yarn.lock` hoặc `pnpm-lock.yaml`**:
  - 2a1. Hệ thống không audit, hiển thị cảnh báo kèm lệnh `yarn npm audit` / `pnpm audit` như v0.1 (câu hỏi mở `Q-06`).
- **3a. OSV không truy cập được và không có cache ≤ 7 ngày cho lockfile**:
  - 3a1. Hệ thống bỏ qua lockfile đó, ghi `ERR-FEED-503-02` "Bỏ qua kiểm tra thư viện {lockfile}: không tra được OSV."; lượt scan vẫn hoàn tất (`BR-FEED-008`).
- **3b. `--offline`**:
  - 3b1. Hệ thống không gửi dữ liệu ra ngoài; Composer dùng bản xuất OSV Packagist trong snapshot `full` nếu có; npm → `ERR-FEED-503-02` (bản xuất npm 219 MB không đóng gói).
- **3c. OSV trả 429 hoặc `Retry-After` > 300 s**:
  - 3c1. Hệ thống ghi `ERR-FEED-429-01`, dùng cache cũ nếu có.
- **4a. Package có advisory `MAL-*`**:
  - 4a1. Finding Critical, `is_malware=true`, khuyến nghị gỡ package và xoay vòng token npm/GitHub, khoá SSH, `.env` như v0.1 (`BR-SEC-004`).
- **4b. Advisory thuộc KEV**:
  - 4b1. Finding đứng đầu xếp hạng, `R` ≥ 70 (`BR-SEC-001`).
- **5a. `SRC-012` lỗi**:
  - 5a1. Hệ thống tính `min_patched` WordPress từ NVD (`SRC-004`) theo DOC-SRS-QP-FEED-002 §6.2 (ngoại lệ `BR-FEED-025`).
- **5b. Nhánh WordPress không còn bản vá (`min_patched = NONE`)**:
  - 5b1. Finding Critical "nhánh không còn bản vá"; đề xuất nâng nhánh WordPress thủ công.
- **7a. Console `serve` chạy không root**:
  - 7a1. SCR-005 chỉ hiển thị dự án trong thư mục user sở hữu là có thể vá; dự án khác chỉ xem (`BR-PTCH-003`, `BR-CON-010`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-004`: tra OSV thêm ≤ 30 s cho ≤ 3.000 package (chưa đo).
- `NFR-PERF-001`: `GET /api/v1/dependency-findings` P95 ≤ 500 ms.
- `NFR-SEC-009`: dữ liệu package hiển thị bằng `textContent`, 0 cảnh báo XSS với dữ liệu mẫu độc hại (tên package do bên thứ ba đặt).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-ASMT-005` | Mức độ advisory dependency | 4 |
| `BR-SEC-004` | Package mã độc | 4a |
| `BR-SEC-001` | KEV ưu tiên cao nhất | 4b, 5 |
| `BR-FEED-001`, `BR-FEED-013`, `BR-FEED-043` | TTL cache OSV, phạm vi dữ liệu gửi ra, điểm thay thế | 3, 4 |
| `BR-FEED-025` | `min_patched` WordPress | 5 |
| `BR-FEED-008` | Lỗi nguồn không chặn lượt scan | 3a |
| `BR-PTCH-003`, `BR-CON-010` | Giới hạn theo quyền | 7a |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | 3 |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | 4, 6 |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | 5, 6 |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | 1, 7 |

### Giao diện và API liên quan
- Màn hình: `SCR-005` Findings thư viện / dependency.
- API: `GET /api/v1/dependency-findings`, `GET /api/v1/projects`, `POST /api/v1/jobs` (`scan` với `only`).

### Quan hệ với use case khác
- Được `<<include>>` bởi UC-SCAN-001 (bước 11).
- `<<extend>>` bởi UC-PTCH-002 (nút "Vá dự án").

### Ghi chú và tài liệu tham chiếu
- Nguồn OSV, cache và biến thể snapshot: [data-sources.md §3.1, §4](../srs/data-sources.md), [data-sources-cache-cli.md §4.4](../srs/data-sources-cache-cli.md).
