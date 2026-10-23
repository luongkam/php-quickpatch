---
id: DOC-UC-QP-RPT-001
title: Đặc tả Use Case UC-RPT-001 — Xuất báo cáo đánh giá
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-RPT-001, report, assessment, json, csv, markdown, html, sha256, auditor]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-API-QP-001
related_diagrams:
  - DIAG-UC-QP-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-RPT-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-CLI-CMD-004` thành "Cung cấp lệnh `report` và `audit`" theo functional-requirements.md (`CR-FR-06`) |

## UC-RPT-001: Xuất báo cáo đánh giá

- **Tác nhân chính (Primary Actor)**: Auditor (`PER-04`) — quyền Export; Operator root/không root xuất thay khi Auditor không có quyền shell/console.
- **Tác nhân hỗ trợ**: System: Job runner (job `report`, loại `read`); CLI + `qp-feeds.py`.
- **Phạm vi (Scope)**: `php-quickpatch.sh report assess --format json|csv|md|html --out FILE`; console SCR-010.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-04`: 1 file báo cáo gồm máy chủ, môi trường, runtime + đánh giá + ứng viên, CVE/KEV, EOL/LTS, dependency, WordPress, kế hoạch và hạn duyệt, nguồn dữ liệu + `fetched_at`, `bundle_id`, phiên bản tool; có SHA-256 để chứng minh file không bị sửa.
  - Người nhận báo cáo HTML: 1 file ≤ 5 MiB, CSS nhúng, không JavaScript, 0 tài nguyên ngoài (`BR-RPT-001`).
  - Kỹ sư bảo mật: file quyền `0600`, không ghi đè file có sẵn, bí mật đã che (`BR-RPT-003`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có kết quả scan và assess (UC-SCAN-001, UC-ASMT-001); Python ≥ 3.6.
  - Đường dẫn `--out` chưa tồn tại.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: file báo cáo theo định dạng chọn; SHA-256 in ra stdout và ghi audit; console cung cấp file tải về.
  - **Đảm bảo tối thiểu**: 0 thay đổi hệ thống; không ghi đè file đã tồn tại.
- **Kích hoạt (Trigger)**: Auditor bấm "Tạo báo cáo đánh giá" trên SCR-010, hoặc chạy `report assess --format html --out /root/reports/assess-2026-10-22.html`.

### Luồng sự kiện chính (Main Success Scenario)
1. Auditor chọn loại "đánh giá" và định dạng (`json`, `csv`, `md`, `html`) trên SCR-010; console gửi `POST /api/v1/reports` tạo job `report assess --format <f> --out STATE_DIR/reports/<report_id>.<ext>` (`FR-CLI-CMD-004`).
2. CLI kiểm Python ≥ 3.6, lấy khoá chia sẻ, đọc kết quả scan/assess, bundle, kế hoạch.
3. Hệ thống dựng nội dung: máy chủ, môi trường, runtime + đánh giá + ứng viên, CVE/KEV, EOL/LTS, dependency, WordPress, kế hoạch và hạn duyệt (`FR-RPT-ASMT-001`).
4. Hệ thống ghi nguồn gốc dữ liệu: `bundle_id`, `fetched_at` từng nguồn, `catalog_version`, phiên bản tool, `hostname`, thời điểm tạo UTC (`BR-RPT-002`).
5. Hệ thống xuất theo định dạng: JSON `qp.report.assess/1`; CSV RFC 4180, UTF-8, dòng tiêu đề, 1 dòng/finding; Markdown; HTML 1 file ≤ 5 MiB, CSS nhúng, không JavaScript (`BR-RPT-001`).
6. Hệ thống che bí mật (`BR-SEC-006`), ghi file quyền `0600`, tính SHA-256, in ra stdout và ghi audit.
7. Console hiển thị báo cáo đã tạo kèm SHA-256 và nút tải (`GET /api/v1/reports/{report_id}?download=1`, `Content-Disposition: attachment`).
8. Auditor tải file và đối chiếu SHA-256.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Định dạng không hỗ trợ**:
  - 1a1. `ERR-RPT-422-01` "Tham số báo cáo không hợp lệ: {detail}."
- **1b. File `--out` đã tồn tại (CLI)**:
  - 1b1. `ERR-RPT-409-01` "File {path} đã tồn tại; chọn tên khác." (`BR-RPT-003`).
- **2a. Thiếu Python ≥ 3.6**:
  - 2a1. `ERR-CLI-424-01`, thoát 2.
- **2b. Chưa có kết quả scan/assess hoặc kết quả cũ > 24 giờ**:
  - 2b1. Báo cáo ghi rõ thời điểm kết quả scan; Auditor yêu cầu Operator chạy UC-SCAN-001/UC-ASMT-001 trước khi xuất lại.
- **3a. Dữ liệu cũ > 7 ngày**:
  - 3a1. Báo cáo kèm cảnh báo `ERR-FEED-412-01` ở đầu file (`BR-DATA-001`); > 90 ngày kèm `ERR-SCN-503-01`.
- **5a. Báo cáo HTML vượt 5 MiB**:
  - 5a1. Hệ thống trả lỗi định dạng `ERR-RPT-422-01` và đề xuất định dạng `json`/`csv` (đề xuất; SRS chưa định nghĩa hành vi khi vượt).
- **7a. `report_id` không tồn tại**:
  - 7a1. 404 `ERR-CON-404-01`.
- **7b. Job vượt 600 s**:
  - 7b1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `BR-RPT-001`: HTML ≤ 5 MiB, 0 tài nguyên ngoài.
- `NFR-SEC-010`: file báo cáo quyền `0600`.
- `NFR-USE-005`: thông báo lỗi có bản tiếng Việt và tiếng Anh.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-RPT-001` | Định dạng báo cáo | 5 |
| `BR-RPT-002` | Nguồn gốc dữ liệu, SHA-256, audit | 4, 6 |
| `BR-RPT-003` | Không ghi đè, quyền `0600`, che bí mật | 1b, 6 |
| `BR-ASMT-003` | Số liệu trên cùng `bundle_id` | 3 |
| `BR-DATA-001` | Cảnh báo tuổi dữ liệu | 3a |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | 1, 2 |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | 3–6 |

### Giao diện và API liên quan
- Màn hình: `SCR-010` Audit & báo cáo.
- API: `POST /api/v1/reports` (`kind=assess`), `GET /api/v1/reports/{report_id}`.

### Quan hệ với use case khác
- Dùng kết quả UC-SCAN-001, UC-ASMT-001, UC-ASMT-002, UC-PLAN-001, UC-FEED-003.

### Ghi chú và tài liệu tham chiếu
- Tải file không phải JSON: thiết kế API dùng `?download=1` (DOC-API-QP-001 §6.2 mục 8).
- `FR-RPT-ASMT-001`: [functional-requirements.md §12](../srs/functional-requirements.md).
