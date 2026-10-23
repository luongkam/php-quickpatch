---
id: DOC-UC-QP-FEED-001
title: Đặc tả Use Case UC-FEED-001 — Đồng bộ dữ liệu CVE/vòng đời thủ công
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FEED-001, feeds, sync, cve, kev, eol, nvd, osv, bundle, cli, console]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-002
  - DOC-SRS-QP-FEED-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-FEED-001
  - DIAG-SEQ-QP-FEED-002
  - DIAG-STATE-QP-FEED-001
  - DIAG-STATE-QP-FEED-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FEED-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CON-FEED-001` trong bảng FR liên quan với `functional-requirements.md` 1.0.1 (`CR-FR-06`): "Hiển thị màn hình Nguồn dữ liệu (SCR-008)" |

## UC-FEED-001: Đồng bộ dữ liệu CVE/vòng đời thủ công

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`); Operator không root đồng bộ vào cache riêng của user (spec §2.3).
- **Tác nhân hỗ trợ (Secondary / System Actor)**: `SYS-02` nguồn online `SRC-001..016` (HTTPS); System: Job runner của console khi bấm "Đồng bộ ngay".
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh feeds update` (bí danh `sync`), bộ chuẩn hoá `qp-feeds.py`, thư mục `STATE_DIR/feeds/`; console SCR-008.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: tuổi dữ liệu advisory ≤ 6 giờ 15 phút tại 99% thời điểm khi có mạng (`NFR-FEED-006`, KR1.1); không phải chờ bản script mới khi có CVE mới.
  - `PER-04` (Auditor): mỗi bản ghi mang `data_origin` (`PRIMARY`, `MIRROR`, `CROSS:<SRC>`, `CACHE`, `SNAPSHOT`) và `fetched_at` để truy nguồn (`BR-FEED-006`).
  - Nhà cung cấp nguồn (NVD, GitHub, endoflife.date…): tool tôn trọng giới hạn tốc độ (NVD ≥ 6 s/request khi không có key) và gửi ≤ 45 request mỗi lần đồng bộ tăng dần (`BR-FEED-004`, `NFR-FEED-008`).
  - Kỹ sư bảo mật: 0 API key xuất hiện trong log, `--json`, audit, snapshot (`BR-FEED-011`, `NFR-FEED-004`).
- **Tiền điều kiện (Pre-conditions)**:
  - Python ≥ 3.6 để chuẩn hoá (thiếu → chỉ tải raw, `BR-FEED-012`).
  - Phân vùng chứa `feeds/` còn ≥ 100 MB trống.
  - Không có tiến trình `feeds update` khác giữ `feeds/.lock` quá 30 s (`BR-FEED-015`).
  - Có kết nối HTTPS (TLS ≥ 1.2) tới các host nguồn đang bật.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `feeds/current/` được thay nguyên tử bằng bundle mới (`bundle_id` mới, 9 file TSV + `feeds.db` + `SHA256SUMS`), `current/` cũ thành `previous/`; `feeds/state/sync-status.json` ghi trạng thái từng nguồn; mã thoát 0 khi mọi nguồn bật đều `OK`.
  - **Đảm bảo tối thiểu**: khi lỗi giữa chừng, `current/` giữ nguyên, `staging/` bị xoá (`BR-FEED-051`); dữ liệu hợp lệ không bị ghi đè bằng phản hồi lỗi (`BR-FEED-007`); khoá `feeds/.lock` được giải phóng.
- **Kích hoạt (Trigger)**: Operator chạy `php-quickpatch.sh feeds update [--source SRC-NNN,…] [--force] [--accept-shrink] [--budget SEC] [--json]`, hoặc bấm "Đồng bộ ngay" trên SCR-008 / nút đồng bộ trên SCR-002 (job `feeds_update`, loại `data`).

### Luồng sự kiện chính (Main Success Scenario)
1. Operator yêu cầu đồng bộ bằng CLI hoặc nút "Đồng bộ ngay"; console tạo job `feeds update --json [--source …] [--force]` (`BR-CON-008`), tối đa 1 job `data` cùng `RUNNING` (`BR-JOB-001`).
2. CLI lấy khoá `flock` trên `feeds/.lock`, chờ tối đa 30 s (`BR-FEED-015`).
3. CLI kiểm tra dung lượng trống của phân vùng `feeds/` ≥ 100 MB.
4. CLI gọi `qp-feeds.py sync` với ngân sách 900 s (đồng bộ đầy đủ) hoặc 180 s (tăng dần khi bundle hiện có ≤ 7 ngày tuổi) (`FR-FEED-SYNC-001`, `NFR-FEED-001`).
5. Với mỗi nguồn quá TTL theo thứ tự `SRC-006`, `002`, `009`, `012`, `011`, `004`, `001`, `010`, `003`, `008`, hệ thống gửi GET có điều kiện (ETag/`If-Modified-Since`), tôn trọng giới hạn tốc độ (`BR-FEED-001`, `BR-FEED-004`, `BR-FEED-016`):
   - vòng đời PHP/Node.js và bản ghi tĩnh PHP 4.4 (`FR-FEED-EOL-001`, `FR-FEED-EOL-002`), ma trận framework/CMS ↔ PHP (`FR-FEED-EOL-003`);
   - bản phát hành PHP, Node.js, trạng thái WordPress core (`FR-FEED-REL-001`, `FR-FEED-REL-002`, `FR-FEED-REL-003`);
   - CVE PHP core qua NVD tăng dần (`FR-FEED-PCVE-001`, `BR-FEED-002`), alias GHSA ↔ CVE (`FR-FEED-PCVE-002`), tra CVE.org khi NVD thiếu (`FR-FEED-PCVE-003`);
   - CVE Node.js core (`FR-FEED-NCVE-001`), CVE WordPress core (`FR-FEED-WCVE-001`), nguồn WordPress cần key khi được cấu hình (`FR-FEED-WCVE-002`);
   - CISA KEV (`FR-FEED-KEV-001`).
6. Hệ thống lưu mỗi phản hồi 200 vào `raw/SRC-xxx/` kèm `.meta.json` (SHA-256, ETag, `fetched_at`) bằng ghi tạm + `rename`; phản hồi 304 chỉ cập nhật `fetched_at` (`FR-FEED-CACH-001`).
7. Hệ thống kiểm schema tối thiểu và ngưỡng biến động số bản ghi trước khi chuẩn hoá (`BR-FEED-009`).
8. Hệ thống chuẩn hoá, khử trùng lặp advisory theo mã chuẩn (`FR-FEED-NORM-001`) và tính `min_patched` từng nhánh (`FR-FEED-NORM-002`) vào `staging/`.
9. Hệ thống kiểm `SHA256SUMS` của `staging/`, đổi tên `current/` → `previous/`, `staging/` → `current/` (`FR-FEED-CACH-002`, `BR-FEED-051`).
10. Hệ thống dọn `feeds/` về ≤ 60 MB theo chính sách lưu giữ (`FR-FEED-CACH-003`, `BR-FEED-052`, `NFR-FEED-005`).
11. CLI giải phóng khoá, in tóm tắt (văn bản hoặc `qp.feeds.status/1`) và thoát 0 (`FR-FEED-CMD-001`).
12. Console chuyển job sang `SUCCEEDED` và làm mới bảng nguồn trên SCR-008 (`FR-CON-FEED-001`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Mã nguồn trong `--source` sai định dạng, hoặc `--budget` ngoài 60–3.600 s**:
  - 1a1. CLI trả lỗi tham số `ERR-CLI-400-01`, thoát 2; console trả `ERR-CON-422-01`.
- **1b. Đã có job `feeds update` đang `QUEUED`/`RUNNING` trên console**:
  - 1b1. Console trả `ERR-JOB-409-01` kèm `job_id` đang chạy.
- **2a. Một tiến trình `feeds update` khác giữ khoá quá 30 s** (vd lịch `SYS-01` đang chạy, UC-FEED-002):
  - 2a1. CLI in `ERR-FEED-423-01` kèm PID, thoát 2; Operator xem tiến trình bằng `feeds status` (UC-FEED-003).
- **3a. Dung lượng trống < 100 MB**:
  - 3a1. CLI in `ERR-FEED-507-01`, không đồng bộ, dữ liệu cũ vẫn được dùng; thoát 2.
- **4a. Không có Python ≥ 3.6**:
  - 4a1. Hệ thống chỉ tải raw, không chuẩn hoá (`BR-FEED-012`), ghi `ERR-FEED-424-01`; Operator dùng `feeds export --raw` để chuẩn hoá trên máy có Python (UC-FEED-004).
- **5a. Nguồn không truy cập được sau 3 lần thử (chờ 5 s, 15 s, 45 s)** (DNS, TLS, HTTP 5xx):
  - 5a1. Hệ thống ghi `ERR-FEED-503-01`, đặt nguồn `FAILED`, dùng chuỗi dự phòng nguồn chéo → cache → snapshot (`BR-FEED-006`); tiếp tục nguồn kế tiếp; kết quả cuối thoát 1 (`DEGRADED`).
- **5b. Nguồn trả 429, NVD trả 403, GitHub `x-ratelimit-remaining = 0`, hoặc `Retry-After` > 300 s**:
  - 5b1. Hệ thống dừng nguồn đó, ghi `ERR-FEED-429-01`; Operator khai báo API key/token hoặc chờ.
- **5c. Nguồn trả 401/403 khi đã gửi key**:
  - 5c1. Hệ thống ghi `ERR-FEED-401-01` (không ghi key); nguồn tuỳ chọn tự tắt tới lần sửa cấu hình.
- **5d. File cấu hình chứa key có quyền rộng hơn `0600`**:
  - 5d1. Hệ thống bỏ qua key, ghi cảnh báo, gọi nguồn không key (`BR-FEED-011`).
- **5e. Vượt ngân sách thời gian (900 s / 180 s) hoặc timeout 1 request**:
  - 5e1. Hệ thống dừng các nguồn còn lại, giữ dữ liệu cũ của chúng, ghi `ERR-FEED-504-01` liệt kê nguồn chưa xong; Operator chạy lại với `--source` riêng.
- **5f. URL nguồn cấu hình dùng `http://` hoặc chuyển hướng sang `http://`**:
  - 5f1. Hệ thống từ chối URL (`BR-FEED-016`), ghi `ERR-FEED-503-01` cho nguồn đó.
- **7a. Phản hồi không phải JSON hợp lệ (trang lỗi HTML, JSON bị cắt)**:
  - 7a1. Hệ thống giữ raw và bundle cũ của nguồn, lưu phản hồi lỗi vào `raw/<SRC>/rejected/` (tối đa 3 file), ghi `ERR-FEED-502-01` (`BR-FEED-007`).
- **7b. Số bản ghi giảm > 20% (KEV: giảm > 5 bản ghi) hoặc phiên bản mới nhất của nhánh lùi**:
  - 7b1. Hệ thống từ chối phản hồi, ghi `ERR-FEED-502-02` (`BR-FEED-009`).
  - 7b2. Operator kiểm tra nguồn thủ công rồi chạy lại `feeds update --force --accept-shrink` từ CLI; thao tác cần xác nhận kép và ghi audit (`BR-CON-006`, `BR-AUD-001`).
- **8a. Một bản ghi không phân tích được (biểu thức semver, chuỗi CPE, ngày)**:
  - 8a1. Hệ thống bỏ qua bản ghi, ghi `ERR-FEED-422-01` (Low), tiếp tục.
- **8b. Hai nguồn lệch nhau vượt ngưỡng (`min_patched` khác nhau, ngày EOL lệch > 3 ngày)**:
  - 8b1. Hệ thống chọn giá trị theo `BR-FEED-027`, ghi `ERR-FEED-409-01` (Low) và log đối chiếu.
- **9a. `staging/` không qua kiểm `SHA256SUMS` hoặc thiếu file**:
  - 9a1. Hệ thống xoá `staging/`, giữ `current/` (`BR-FEED-051`), ghi `ERR-FEED-422-02`, thoát 2.
- **11a. Kết quả còn dữ liệu cũ > 7 ngày sau đồng bộ**:
  - 11a1. Tóm tắt kèm `ERR-FEED-412-01`; > 90 ngày kèm `ERR-SCN-503-01` (`BR-FEED-005`).
- **12a. Job vượt 960 s**:
  - 12a1. Job runner dừng tiến trình, job `FAILED` với `ERR-JOB-504-01` (`BR-JOB-008`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-FEED-001`: đồng bộ tăng dần ≤ 180 s P95, đầy đủ ≤ 900 s.
- `NFR-FEED-003`: chuẩn hoá 2.000 CVE + 2.000 KEV ≤ 200 MB RSS, ≤ 30 s CPU.
- `NFR-FEED-004`: TLS ≥ 1.2 có xác thực chứng chỉ; 0 key trong log.
- `NFR-FEED-005`: `feeds/` ≤ 60 MB; `NFR-FEED-008`: đồng bộ tăng dần ≤ 45 request.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FEED-001`, `BR-FEED-002`, `BR-FEED-003`, `BR-FEED-004` | TTL, NVD tăng dần, timeout/retry, giới hạn tốc độ | 4, 5 |
| `BR-FEED-006`, `BR-FEED-007`, `BR-FEED-008`, `BR-FEED-009` | Dự phòng, không ghi đè bằng phản hồi lỗi, lỗi nguồn không chặn, biến động bất thường | 5, 7 |
| `BR-FEED-011`, `BR-FEED-012`, `BR-FEED-013`, `BR-FEED-015`, `BR-FEED-016` | API key, chế độ chỉ đọc bundle, phạm vi dữ liệu gửi ra, một tiến trình đồng bộ, bắt buộc HTTPS | 2, 4, 5 |
| `BR-FEED-022`, `BR-FEED-023`, `BR-FEED-027`, `BR-FEED-030` | So khớp dải, khử trùng lặp, mâu thuẫn nguồn, vá tối thiểu | 8 |
| `BR-FEED-051`, `BR-FEED-052` | Thay bundle nguyên tử, lưu giữ | 9, 10 |
| `BR-FEED-005`, `BR-DATA-001`, `BR-DATA-002` | Độ tươi, cảnh báo tuổi dữ liệu, nguồn mốc bản vá | 5, 11 |
| `BR-SEC-001` | KEV ưu tiên cao nhất (cờ `in_kev`) | 5 |
| `BR-JOB-001`, `BR-JOB-008` | Tối đa 1 job `data`; timeout `feeds update` 960 s | 1, 12 |
| `BR-CON-006` | Xác nhận kép cho `--accept-shrink` | 7b |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | 1, 11 |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | 2–4 |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | 5 |
| `FR-FEED-EOL-002` | Bổ sung bản ghi vòng đời tĩnh | 5 |
| `FR-FEED-EOL-003` | Đồng bộ ma trận framework/CMS ↔ PHP | 5 |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | 5 |
| `FR-FEED-REL-002` | Đồng bộ bản phát hành Node.js | 5 |
| `FR-FEED-REL-003` | Đồng bộ trạng thái WordPress core | 5 |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | 5 |
| `FR-FEED-PCVE-002` | Làm giàu alias GHSA ↔ CVE cho PHP | 5 |
| `FR-FEED-PCVE-003` | Tra CVE.org khi NVD thiếu | 5 |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | 5 |
| `FR-FEED-WCVE-001` | Đồng bộ CVE WordPress core | 5 |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | 5 |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | 5 |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | 6 |
| `FR-FEED-NORM-001` | Chuẩn hoá và khử trùng lặp advisory | 8 |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | 8 |
| `FR-FEED-CACH-002` | Dựng và thay bundle nguyên tử | 9 |
| `FR-FEED-CACH-003` | Dọn dẹp theo giới hạn dung lượng | 10 |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | 1, 12 |

### Giao diện và API liên quan
- Màn hình: `SCR-008` Nguồn dữ liệu (nút "Đồng bộ ngay"), `SCR-002` Tổng quan (nút đồng bộ dữ liệu).
- API: `POST /api/v1/jobs` (`action=feeds_update`), `GET /api/v1/feeds`, `GET /api/v1/jobs/{job_id}/events`.

### Quan hệ với use case khác
- UC-FEED-002 dùng lại luồng chính từ bước 2 với tác nhân `SYS-01`.
- Khi tạo từ console: `<<include>>` UC-JOB-001.
- Bundle mới là đầu vào của UC-SCAN-001, UC-ASMT-001, UC-PLAN-001.

### Ghi chú và tài liệu tham chiếu
- Giá trị TTL từng nguồn: [data-sources.md §3.1](../srs/data-sources.md); chính sách gọi nguồn: §3.3; trình tự: [data-sources-cache-cli.md §5.1](../srs/data-sources-cache-cli.md); mã thoát `feeds`: §6.3.
- Câu hỏi mở kế thừa: `Q-08` chu kỳ 6 giờ (spec §4.4).
