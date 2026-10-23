---
id: DOC-UC-QP-ASMT-001
title: Đặc tả Use Case UC-ASMT-001 — Đánh giá runtime và so sánh phiên bản ứng viên
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-ASMT-001, assess, risk-score, candidates, comparison, cve, kev, eol, lts]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-002
  - DOC-SRS-QP-SCN-000
  - DOC-API-QP-001
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-ASMT-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên FR trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): `FR-CLI-CMD-001` "Cung cấp lệnh `assess`", `FR-CON-ASMT-001` "Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003)" |

## UC-ASMT-001: Đánh giá runtime và so sánh phiên bản ứng viên

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`); Auditor (`PER-04`, chỉ xem kết quả).
- **Tác nhân hỗ trợ**: `SYS-03` hạ tầng đích (tra khả năng cài của ứng viên qua package manager/panel, chỉ đọc); `SYS-02` Docker Hub (tag image, chỉ khi có mạng, `BR-DATA-003`); System: Job runner (job `assess`).
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh assess`, `qp-feeds.py` (điểm rủi ro); console SCR-003.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: thấy cho 1 runtime: số CVE chưa vá theo 4 mức CVSS v3.1, số CVE KEV, trạng thái hỗ trợ, LTS, ngày EOL, số ngày còn lại, bản patch mới nhất, điểm rủi ro `R` 0–100 và `ΔR` của 4 loại ứng viên, trên cùng `bundle_id` (`BR-ASMT-003`).
  - `PER-04`: bảng so sánh ghi `bundle_id`, tuổi dữ liệu, `catalog_version` để đối chiếu.
  - Chủ site: lượt đánh giá chỉ đọc, 0 thay đổi hệ thống (`BR-SCAN-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có kết quả `scan` chứa `runtime_id` (UC-SCAN-001); kết quả cũ > 24 giờ hoặc không có → `assess` chạy scan đọc trước (`FR-CLI-CMD-001`).
  - Python ≥ 3.6 (lệnh `assess` cần Python).
  - Bundle feeds hợp lệ (online hoặc snapshot).
  - Console: phiên hợp lệ (UC-CON-001).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: envelope `qp.assess/1` gồm `assessment.current`, `assessment.candidates[]` (có `selectable`, `installable`), `assessment.comparison`; `result.ranking[]` cho mọi runtime; SCR-003 hiển thị danh sách CVE và bảng so sánh.
  - **Đảm bảo tối thiểu**: 0 thay đổi hệ thống; lỗi ghi trong `errors[]`.
- **Kích hoạt (Trigger)**: Operator chọn 1 runtime trên SCR-002 (mở SCR-003), hoặc chạy `assess --runtime-id ID | --bin PATH --candidates [--offline] --json`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chọn runtime trên SCR-002; console mở SCR-003 và tạo job `assess --runtime-id <runtime_id> --candidates --json` loại `read` (`BR-CON-008`, `FR-CON-ASMT-001`, `FR-CLI-CMD-001`).
2. CLI kiểm Python ≥ 3.6, lấy khoá chia sẻ `STATE_DIR/.lock` (`BR-JOB-002`), đọc kết quả scan gần nhất (≤ 24 giờ).
3. Hệ thống đánh giá runtime hiện tại: tập CVE chưa vá `U(X)`, đếm theo Critical ≥ 9,0 / High 7,0–8,9 / Medium 4,0–6,9 / Low 0,1–3,9, đếm KEV, trạng thái hỗ trợ, LTS, ngày EOL, số ngày còn lại, bản patch mới nhất cùng nhánh, `min_patched_sec`, gắn tuổi dữ liệu (`FR-ASMT-CUR-001`).
4. Hệ thống tính điểm rủi ro `R` theo công thức DOC-SRS-QP-FEED-002 §8.2, áp điểm sàn theo mức ưu tiên kịch bản và phân mức `CRITICAL` (70–100), `HIGH` (40–69), `MEDIUM` (20–39), `LOW` (0–19) (`FR-ASMT-RISK-001`, `BR-FEED-040`, `BR-FEED-041`, `BR-FEED-042`).
5. Hệ thống liệt kê 4 loại ứng viên `SAME_BRANCH_LATEST`, `NEXT_SUPPORTED`, `RECOMMENDED`, `LATEST_STABLE`, bỏ trùng, đánh dấu `selectable` (khác nhánh: `eol` ≥ hôm nay + 365 ngày) (`FR-ASMT-CAND-001`, `BR-ASMT-001`, `BR-ASMT-002`).
6. Hệ thống xác định `installable` ∈ {`yes`, `needs_repo`, `no`, `unknown`} cho từng ứng viên bằng lệnh liệt kê của playbook (`apt-cache policy`, `dnf list available`, `whmapi1 php_get_installed_versions`, `selectorctl --list`, `plesk bin php_handler --list`, `apk search`, tag Docker Hub) (`FR-ASMT-CAND-002`).
7. Hệ thống tính `R` cho từng ứng viên cùng bundle, cùng ngày `T`, và `ΔR = R(ứng viên) − R(hiện tại)` (`FR-ASMT-RISK-002`, `BR-FEED-044`).
8. Hệ thống lập bảng so sánh song song: số CVE theo mức, KEV, trạng thái hỗ trợ, LTS, EOL, số ngày còn lại, khoảng cách major, số hit tương thích `error`/`warning` (khi đã có), `R`, `ΔR` (`FR-ASMT-CMP-001`, `BR-ASMT-003`).
9. Hệ thống xếp hạng mọi runtime, WordPress core và dependency findings theo `R` giảm dần, cùng `R` theo thứ tự KEV → `cvss_max` ≥ 9,0 → EOL → `cvss_max` 7,0–8,9 → EOL ≤ 90 ngày → còn lại (`FR-ASMT-RANK-001`, `BR-ASMT-004`, `BR-SEC-001`).
10. CLI xuất envelope `qp.assess/1`, thoát 0 hoặc 1.
11. Console hiển thị SCR-003: danh sách CVE (mã, CVSS, mức, KEV, nguồn, ngày công bố, bản sửa), bảng so sánh, `ΔR`, `bundle_id`, tuổi dữ liệu, `catalog_version`; nút "Vá cùng nhánh" (dry-run) và "Lập kế hoạch" (`FR-CON-ASMT-001`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. `runtime_id` không có trong kết quả scan gần nhất**:
  - 1a1. Hệ thống trả `ERR-ASMT-404-01` "Không tìm thấy runtime {runtime_id}; hãy quét lại."; Operator chạy UC-SCAN-001.
- **1b. `runtime_id` sai regex `^(php|node):[0-9a-f]{12}$`**:
  - 1b1. Console trả `ERR-CON-422-01`, không tạo tiến trình.
- **1c. Đã có job `assess` cho cùng runtime đang chạy**:
  - 1c1. Console trả `ERR-JOB-409-01` kèm `job_id`.
- **1d. SCR-003 mở khi kết quả `assess` có `bundle_id` khác bundle hiện tại**:
  - 1d1. Console gắn nhãn "kết quả cũ" và nút đánh giá lại (DOC-API-QP-001 §6.2 mục 2).
- **2a. Thiếu Python ≥ 3.6**:
  - 2a1. CLI in `ERR-CLI-424-01` "{command} requires Python 3.6+.", thoát 2; Operator dùng `scan --json`.
- **2b. Khoá đang bị lượt ghi giữ**:
  - 2b1. CLI in `ERR-CLI-423-01`, thoát 2; job console chờ tối đa 30 phút rồi `ERR-JOB-409-02`.
- **2c. Kết quả scan cũ > 24 giờ hoặc không có**:
  - 2c1. CLI chạy scan đọc trước (UC-SCAN-001) rồi tiếp tục bước 3.
- **3a. Dữ liệu cũ > 7 ngày**:
  - 3a1. Kết quả kèm `ERR-FEED-412-01`; > 90 ngày kèm `ERR-SCN-503-01`, ứng viên khác nhánh bị đánh dấu `selectable=false` (chỉ đề xuất vá cùng nhánh, `BR-FEED-005`).
- **3b. Runtime thuộc nhánh EOL mà nguồn CNA không còn đánh giá**:
  - 3b1. CVE `assessed=false` không tính vào số đếm; hiển thị nhãn "Nhánh EOL — nguồn không còn đánh giá CVE mới" (`BR-FEED-029`); điểm sàn theo `BR-FEED-041` giữ `R` không thấp hơn mức ưu tiên kịch bản.
- **3c. Runtime là gói distro có CVE `UNKNOWN`**:
  - 3c1. CVE tính như chưa vá, hiển thị "chưa xác định" (`BR-SEC-002`, `BR-FEED-026`).
- **3d. Có ≥ 1 advisory KEV chưa vá**:
  - 3d1. `R` ≥ 70 (`CRITICAL`), runtime đứng đầu xếp hạng, hiển thị dòng KEV kèm `dueDate` (`BR-SEC-001`).
- **3e. Có bản bảo mật mới nhưng chưa có chi tiết CVE sau 6 giờ**:
  - 3e1. Hệ thống tạo advisory tạm `QP-SR-{product}-{r}` với `cvss_rep = 7,5`, hiển thị "Bản bảo mật {r} chưa có chi tiết CVE" (`BR-FEED-024`).
- **3f. Runtime `locked` (`UNKNOWN`/`PRE_RELEASE`)**:
  - 3f1. Hệ thống hiển thị `ERR-SCN-422-01`, không liệt kê ứng viên khác nhánh, nút "Vá cùng nhánh" và "Lập kế hoạch" bị vô hiệu (`BR-SCN-013`).
- **5a. Nhánh ứng viên `PRE_RELEASE` hoặc Node.js `CURRENT` chưa tới ngày `lts`**:
  - 5a1. Ứng viên chỉ hiển thị, `selectable=false` kèm `not_selectable_reason` (`BR-UPG-004`, `BR-SCN-007`).
- **5b. Framework, loader hoặc `engines` không có nhánh đích thoả `BR-SCN-005`/`BR-SCN-006`**:
  - 5b1. Không có ứng viên `RECOMMENDED`; hệ thống hiển thị `ERR-SCN-409-01` và đề xuất nâng framework/CMS trước.
- **6a. `--offline` hoặc lệnh liệt kê có `verified=false`**:
  - 6a1. `installable=unknown`; lệnh chưa kiểm chứng không được chạy (`BR-ENV-010`, `BR-DATA-003`).
- **6b. Nhánh đích không có trong kho đang bật**:
  - 6b1. `installable=needs_repo` kèm tên kho (Surý, Remi, LiteSpeed, NodeSource) (`BR-ENV-004`).
- **10a. Job vượt 1.800 s**:
  - 10a1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-001`: `GET /api/v1/runtimes/{runtime_id}/assessment` P95 ≤ 500 ms.
- `NFR-MNT-002`: 11 ví dụ điểm rủi ro trong DOC-SRS-QP-FEED-002 §8.5 đạt 100% trong test hồi quy.
- `NFR-USE-001`: từ SCR-003, vá cùng nhánh 1 runtime ≤ 3 thao tác (UC-PTCH-001).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SEC-001`, `BR-SEC-002` | KEV ưu tiên cao nhất; điều kiện `ok-backport` | 3, 9 |
| `BR-FEED-022`, `BR-FEED-024`, `BR-FEED-026`, `BR-FEED-028`, `BR-FEED-029` | So khớp dải, tín hiệu bản bảo mật, backport, CVSS đại diện, nhánh không được đánh giá | 3 |
| `BR-FEED-040`, `BR-FEED-041`, `BR-FEED-042`, `BR-FEED-043`, `BR-FEED-044` | Công thức, sàn, phân mức, điểm thay thế, điểm ứng viên | 4, 7 |
| `BR-ASMT-001`, `BR-ASMT-002`, `BR-ASMT-003`, `BR-ASMT-004` | Loại ứng viên, điều kiện chọn, so sánh nhất quán, thứ tự xếp hạng | 5, 8, 9 |
| `BR-UPG-004`, `BR-SCN-005`, `BR-SCN-006`, `BR-SCN-007` | Đích bị cấm, chọn nhánh đích PHP/Node.js, cấm nhánh trung gian | 5 |
| `BR-ENV-004`, `BR-ENV-010`, `BR-DATA-003` | Kho bên thứ ba, lệnh chưa kiểm chứng, dữ liệu gửi ra ngoài | 6 |
| `BR-FEED-005`, `BR-DATA-001` | Độ tươi dữ liệu | 3 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | 1, 2, 10 |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | 3 |
| `FR-ASMT-RISK-001` | Tính điểm rủi ro runtime | 4 |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | 5 |
| `FR-ASMT-CAND-002` | Xác định khả năng cài của ứng viên | 6 |
| `FR-ASMT-RISK-002` | So sánh điểm hiện tại và ứng viên | 7 |
| `FR-ASMT-CMP-001` | So sánh hiện tại với ứng viên | 8 |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | 9 |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | 1, 11 |

### Giao diện và API liên quan
- Màn hình: `SCR-003` Đánh giá runtime & so sánh phiên bản; điểm vào từ `SCR-002`.
- API: `POST /api/v1/jobs` (`action=assess`), `GET /api/v1/runtimes/{runtime_id}/assessment`, `GET /api/v1/runtimes/{runtime_id}/candidates`, `GET /api/v1/advisories`, `GET /api/v1/advisories/{adv_id}`.

### Quan hệ với use case khác
- `<<include>>` UC-SCAN-001 khi kết quả scan cũ > 24 giờ.
- `<<extend>>` bởi UC-PTCH-001 (nút "Vá cùng nhánh") và UC-PLAN-001 (nút "Lập kế hoạch").
- Kết quả là đầu vào của UC-RPT-001.

### Ghi chú và tài liệu tham chiếu
- Công thức và 11 ví dụ tính điểm: [data-sources-merge-risk.md §8](../srs/data-sources-merge-risk.md); trình tự: [flows.md §3](../srs/flows.md).
- Câu hỏi mở kế thừa: `Q-09` thứ tự xếp hạng (`BR-ASMT-004` đề xuất), `Q-SRS-05` chọn thủ công đích có `eol` ≥ hôm nay + 90 ngày.
