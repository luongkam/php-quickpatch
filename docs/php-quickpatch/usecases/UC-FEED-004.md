---
id: DOC-UC-QP-FEED-004
title: Đặc tả Use Case UC-FEED-004 — Xuất/nhập snapshot cho máy chủ không ra Internet
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FEED-004, feeds, snapshot, offline, export, import, sha256, air-gapped, dry-run]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-003
  - DOC-SRS-QP-FLOW-001
  - DOC-API-QP-001
  - DOC-API-QP-002
  - DOC-API-QP-004
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-FEED-003
  - DIAG-STATE-QP-FEED-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FEED-004 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: nhập snapshot qua console đi qua 2 bước dry-run → xác nhận theo `BR-CON-005` 1.0.1 — bước 4–7 tạo job `read` `feeds import … --dry-run` (kiểm SHA-256, `SHA256SUMS`, tar, schema, `generated_at`, 0 thay đổi `current/`) và hiển thị kết quả trên SCR-011; bước 8–9 xác nhận ≤ 15 phút, tải lại file, cổng D so SHA-256 nội dung và `force` với job dry-run; đánh số lại luồng chính (14 bước) và luồng nhánh; thêm nhánh 5c, 6a, 9a (`ERR-JOB-428-01`); thêm `BR-CON-004`, `BR-CON-005`, `BR-CLI-003`, `FR-CON-SAFE-001`, `FR-CLI-SAFE-001`, `NFR-USE-006`, quan hệ UC-CON-003; ghi chú mâu thuẫn chuyển thành "đã quyết", thêm ghi chú 2 wireframe cần cập nhật theo; `depends_on` thêm DOC-SRS-QP-FLOW-001, DOC-API-QP-002, DOC-API-QP-004 |

## UC-FEED-004: Xuất/nhập snapshot cho máy chủ không ra Internet

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01`, `PER-02`).
- **Tác nhân hỗ trợ**: máy nguồn có Internet và bundle tươi (chạy `feeds export`); System: Job runner (job dry-run loại `read` `feeds import … --dry-run` và job ghi `feeds import` khi tải lên qua console).
- **Phạm vi (Scope)**: `php-quickpatch.sh feeds export` (bí danh `snapshot export`), `feeds import` (bí danh `snapshot import`), snapshot đóng gói `share/php-quickpatch/feeds-snapshot.tar.gz`; console SCR-008 (khối "Nhập snapshot") và SCR-011 (xem trước dry-run và xác nhận).
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02` vận hành máy chủ không ra Internet: có dữ liệu CVE/KEV/vòng đời tuổi ≤ 7 ngày để đánh giá (KR5.2) mà không mở kết nối ra ngoài.
  - Kỹ sư bảo mật: 100% gói nhập được kiểm SHA-256 do người vận hành cung cấp; từ chối đường dẫn tuyệt đối, `..`, symlink, hardlink, thiết bị trong tar; tổng giải nén ≤ 50 MB (`BR-FEED-010`, `BR-FEED-055`); qua console, job ghi `feeds_import` chỉ được tạo khi job dry-run cùng SHA-256 nội dung và cùng `force` đã `SUCCEEDED` ≤ 15 phút trước, cùng phiên (`BR-CON-005`).
  - Chủ các máy chủ khác: snapshot xuất không chứa `cache/`, `distro_fix` của máy, API key, đường dẫn site (`BR-FEED-056`).
  - `PER-04`: mỗi lần nhập có bản ghi audit (người chạy, SHA-256, `generated_at`).
- **Tiền điều kiện (Pre-conditions)**:
  - Xuất: máy nguồn có bundle `current/` hợp lệ; đường dẫn `--out` chưa tồn tại.
  - Nhập: Operator có file `.tar.gz` và chuỗi SHA-256 64 ký tự hex lấy từ nguồn phát hành hoặc từ đầu ra `feeds export` của máy nguồn; qua console: file ≤ 20 MiB, còn trên máy chạy trình duyệt để tải lại ở bước xác nhận.
  - Console: phiên hợp lệ (UC-CON-001).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công (xuất)**: file `feeds-snapshot-<YYYYMMDDTHHMMSSZ>-<variant>.tar.gz` gồm `manifest.json`, `SHA256SUMS`, `bundle/`; SHA-256 của file được in ra stdout.
  - **Đảm bảo thành công (nhập)**: job dry-run `SUCCEEDED` với 0 thay đổi trên `feeds/`; `current/` được thay nguyên tử bằng bundle từ snapshot, `bundle_id` mới, audit ghi người chạy, SHA-256, `generated_at`; catalog trong snapshot được dùng nếu `catalog_version` lớn hơn (`FR-SCN-CAT-001`); 2 file tạm `work/upload-<job_id>.tar.gz` (của job dry-run và job ghi) đã bị xoá.
  - **Đảm bảo tối thiểu**: gói không đạt kiểm tra hoặc không đạt cổng D → `current/` giữ nguyên, không tạo job ghi, file tạm upload của mỗi job bị xoá khi job đó kết thúc hoặc khi request bị từ chối.
- **Kích hoạt (Trigger)**: Operator chạy `feeds export --out FILE [--variant standard|full] [--raw]` trên máy nguồn, rồi `feeds import FILE --sha256 HEX [--force]` trên máy đích; hoặc tải file lên SCR-008, xem trước và xác nhận trên SCR-011.

### Luồng sự kiện chính (Main Success Scenario)
1. Trên máy nguồn có Internet, Operator chạy `feeds export --out /tmp/feeds-snapshot-<ts>-standard.tar.gz` (`FR-FEED-CMD-004`).
2. Hệ thống đóng gói `current/` thành `manifest.json` + `SHA256SUMS` + `bundle/`, loại `cache/`, `distro_fix` của máy, key, đường dẫn site (`FR-FEED-SNAP-002`, `BR-FEED-056`), và in SHA-256 của file.
3. Operator chép file và chuỗi SHA-256 sang máy đích bằng kênh của tổ chức (scp qua bastion, thiết bị lưu trữ).
4. Operator mở SCR-008, chọn file, nhập SHA-256, để `force` = `false` và bấm "Xem trước"; trình duyệt gửi `POST /api/v1/feed-snapshots?dry_run=true` (`Content-Type: application/gzip`, header `X-QP-Snapshot-SHA256`, `X-QP-CSRF`, `Origin`; DOC-API-QP-001 §2.13.3, DOC-API-QP-002 §6.2) (`FR-CON-FEED-002`, `BR-CON-005`).
5. Console kiểm Host, phiên, CSRF, `Origin` (`BR-CON-004` ngoại lệ 2), kích thước ≤ 20 MiB (`BR-CON-009`); ghi luồng vào `STATE_DIR/work/upload-<job_id>.tar.gz` quyền `0600`, vừa ghi vừa tính SHA-256 và kiểm 2 byte đầu `1f 8b` (gzip); SHA-256 nội dung khớp header → tạo job dry-run loại `read` (`BR-JOB-003`) chạy `feeds import <file> --sha256 <hex> --yes --json --dry-run`, `params` của job = `{"force": false, "sha256": "<hex>"}`, trả 202 kèm `dry_job_id`.
6. CLI (dry-run) giải nén vào thư mục tạm `work/dryrun-<pid>/`, kiểm SHA-256 toàn gói bằng giá trị `--sha256`, đường dẫn tar, giới hạn 50 MB, từng dòng `SHA256SUMS`, `schema` cùng major, `generated_at` ≤ hiện tại + 1 giờ và không cũ hơn `current/`; không lấy `feeds/.lock`, không thay `staging/`, `bundles/`, `current`, `previous` (`FR-CLI-SAFE-001`, `BR-CLI-003`); xoá thư mục tạm, thoát 0 kèm `preview`. Console xoá file tạm của job dry-run, chuyển job `SUCCEEDED`.
7. SCR-008 đọc `GET /api/v1/jobs/{dry_job_id}` và mở SCR-011 hiển thị `result.preview` đủ 4 mục của `NFR-USE-006` (`FR-CON-SAFE-001`), trong đó thay đổi theo dry-run gồm kết quả kiểm SHA-256 gói, tar, `SHA256SUMS`, `schema`, `generated_at` và `bundle_id`, `generated_at` của snapshot so với bundle hiện tại; đối tượng ảnh hưởng là `feeds/current` (`FR-CON-FEED-002`).
8. Operator bấm "Xác nhận" trong ≤ 15 phút kể từ khi tạo job dry-run, cùng phiên; trình duyệt tải lại cùng file: `POST /api/v1/feed-snapshots?confirm_dry_run_job_id=<dry_job_id>` + `X-QP-Snapshot-SHA256` (bước xác nhận không dùng lại file của job dry-run).
9. Console kiểm như bước 5, ghi file mới `work/upload-<job_id>.tar.gz` (`0600`) và tính SHA-256 nội dung nhận lần này; qua cổng D (`BR-CON-005`): job dry-run tồn tại, cùng hành động `feeds_import`, cùng phiên, tạo ≤ 15 phút trước, `SUCCEEDED`, `bundle_id` hiện tại không đổi, SHA-256 nội dung và `force` bằng `params` của job dry-run; đạt → tạo job `write` (`BR-JOB-003`) chạy `feeds import <file> --sha256 <hex> --yes --json`, trả 202 kèm `job_id`.
10. CLI ghi audit intent (`FR-JOB-AUD-001`), lấy khoá `feeds/.lock`, chờ tối đa 30 s (`BR-FEED-015`).
11. CLI kiểm lại toàn bộ: SHA-256 toàn gói bằng giá trị `--sha256`, giải nén vào `staging/` với kiểm tra đường dẫn tar và giới hạn 50 MB, từng dòng `SHA256SUMS`, `schema` cùng major, `generated_at` ≤ hiện tại + 1 giờ và không cũ hơn `current/` (`FR-FEED-SNAP-003`, `BR-FEED-010`, `BR-FEED-055`).
12. CLI dựng bundle và thay `current/` nguyên tử: `current` trỏ bundle mới, `previous` trỏ bundle cũ (`FR-FEED-CACH-002`, `BR-FEED-051`).
13. CLI ghi audit result (người chạy, SHA-256, `generated_at`), giải phóng khoá, thoát 0 với `qp.feeds.import/1` kèm `bundle_id` mới (`FR-FEED-CMD-005`).
14. Console xoá file tạm của job ghi, chuyển job `SUCCEEDED`, làm mới SCR-008 với `bundle_id`, `data_origin = SNAPSHOT`, tuổi dữ liệu mới.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. File `--out` đã tồn tại**:
  - 1a1. CLI từ chối, không ghi đè (DOC-SRS-QP-FEED-003 §6.2), thoát 2.
- **1b. `--variant full`**:
  - 1b1. Hệ thống thêm bản xuất OSV Packagist toàn bộ (mục tiêu ≤ 15 MB nén) để máy đích quét `composer.lock` offline; npm không hỗ trợ offline.
- **1c. `--raw` (máy nguồn không có Python)**:
  - 1c1. Hệ thống thêm `raw/` (không gồm `cache/`) để chuẩn hoá ở máy có Python ≥ 3.6 (`BR-FEED-012`).
- **3a. Nhập bằng CLI thay cho console**:
  - 3a1. Operator tuỳ chọn chạy trước `feeds import FILE --sha256 HEX --dry-run` để chỉ kiểm, 0 thay đổi (`BR-CLI-003`, `FR-CLI-SAFE-001`).
  - 3a2. Operator chạy `feeds import FILE --sha256 HEX`; lệnh ghi mới có TTY hỏi `y/N`, không TTY bắt buộc `--yes` (`FR-CLI-SAFE-001`, `ERR-CLI-428-01`); cổng D chỉ áp cho job tạo qua console, luồng tiếp tục từ bước 10.
- **3b. Máy đích chưa từng có `current/` và Operator không nhập snapshot**:
  - 3b1. Hệ thống dùng snapshot đóng gói kèm tool sau khi kiểm SHA-256 với `QP_SNAPSHOT_SHA256` (`FR-FEED-SNAP-001`, `BR-FEED-053`); snapshot đóng gói có `generated_at` mới hơn `current/` → dựng lại bundle (`BR-FEED-054`).
- **4a. Thiếu SHA-256 hoặc chuỗi không đủ 64 ký tự hex**:
  - 4a1. Console trả `ERR-CON-422-01`, không nhận thân, không tạo job; CLI trả lỗi tham số, thoát 2.
- **4b. Snapshot cũ hơn `current/` và Operator chủ động quay về dữ liệu cũ**:
  - 4b1. Operator bật `force` trên SCR-008; trình duyệt gửi `?dry_run=true&force=true`, `params` của job dry-run = `{"force": true, "sha256": "<hex>"}`; bước 8 gửi `?confirm_dry_run_job_id=<dry_job_id>&force=true`; audit ghi cờ `--force`.
- **5a. File > 20 MiB hoặc thiếu `Content-Length` (bước 5 hoặc 9)**:
  - 5a1. Console trả 413 `ERR-CON-413-01`; Operator dùng đường CLI (extension 3a).
- **5b. Request thiếu `X-QP-CSRF` hoặc `Origin` sai (bước 5 hoặc 9)**:
  - 5b1. Console trả `ERR-AUTH-403-01`/`ERR-AUTH-403-02`, không lưu file.
- **5c. SHA-256 nội dung nhận khác header, không phải gzip, hoặc không đủ dung lượng ghi file tạm (bước 5 hoặc 9)**:
  - 5c1. Console xoá file tạm, không tạo job, trả 422 `ERR-FEED-422-02` hoặc 507 `ERR-FEED-507-01`.
- **6a. Job dry-run không đạt kiểm tra**:
  - 6a1. SHA-256 gói hoặc 1 dòng `SHA256SUMS` không khớp, tar chứa mục bị cấm, giải nén > 50 MB, `schema` khác major hoặc `generated_at` > hiện tại + 1 giờ → CLI thoát 2 với `ERR-FEED-422-02`; snapshot cũ hơn `current/` mà không có `force` → `ERR-FEED-409-02`; 0 thay đổi `feeds/`.
  - 6a2. Console xoá file tạm, chuyển job dry-run `FAILED` (`ERR-JOB-500-01`); SCR-008 hiển thị lỗi, không mở bước xác nhận. Với `ERR-FEED-409-02`, Operator quay về bước 4 theo extension 4b nếu chủ động nhập dữ liệu cũ hơn.
- **8a. Operator đóng SCR-011 hoặc không xác nhận trong 15 phút**:
  - 8a1. Không có job ghi; khi xác nhận sau 15 phút, cổng D trả `ERR-JOB-428-01` theo extension 9a.
- **9a. Không đạt cổng D (`BR-CON-005`)**:
  - 9a1. Thiếu `confirm_dry_run_job_id` → console trả 428 `ERR-JOB-428-01` (`details.constraint = missing`) ngay khi đọc xong dòng request và header, không đọc thân, không ghi file.
  - 9a2. SHA-256 nội dung nhận hoặc `force` khác `params` của job dry-run (`params_mismatch`), khác phiên (`other_session`), quá 15 phút (`expired`), job dry-run không `SUCCEEDED` (`not_succeeded`), `bundle_id` đã đổi do một lượt `feeds update` chạy giữa 2 bước (`fingerprint_changed`) → console xoá file vừa nhận, không tạo job, trả 428 `ERR-JOB-428-01`.
  - 9a3. SCR-008 yêu cầu chạy lại dry-run; luồng quay về bước 4.
- **10a. Không ghi được audit intent**:
  - 10a1. CLI huỷ nhập, `ERR-AUD-500-01` (`BR-AUD-004`).
- **10b. Lượt `feeds update` khác giữ khoá > 30 s**:
  - 10b1. CLI thoát 2 với `ERR-FEED-423-01`.
- **11a. SHA-256 toàn gói hoặc 1 dòng `SHA256SUMS` không khớp, hoặc tar chứa đường dẫn bị cấm/vượt 50 MB**:
  - 11a1. CLI từ chối, `ERR-FEED-422-02` (Critical), xoá `staging/`, `current/` giữ nguyên, thoát 2.
- **11b. Snapshot cũ hơn `current/` (đường CLI 3a không có `--force`)**:
  - 11b1. CLI từ chối với `ERR-FEED-409-02`, xoá `staging/`.
  - 11b2. Operator chủ động quay về dữ liệu cũ: chạy lại kèm `--force` (CLI) hoặc theo extension 4b (console); audit ghi cờ `--force`.
- **11c. `schema` khác major hoặc `generated_at` > hiện tại + 1 giờ**:
  - 11c1. CLI từ chối với `ERR-FEED-422-02`.
- **12a. Snapshot chứa catalog lỗi `SHA256SUMS`/schema**:
  - 12a1. Bundle dữ liệu vẫn được nhập; catalog đang dùng được giữ (`FR-SCN-CAT-001`), cảnh báo `ERR-FEED-502-02`.
- **14a. Tuổi dữ liệu của snapshot vừa nhập > 7 ngày**:
  - 14a1. Mọi kết quả sau đó kèm `ERR-FEED-412-01`; > 90 ngày kèm `ERR-SCN-503-01` (`BR-FEED-005`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-FEED-005`: `feeds/` ≤ 60 MB sau nhập.
- `NFR-SEC-010`: thư mục `STATE_DIR` quyền 0700/0750, file tạm upload 0600.
- `NFR-REL-002`: 100% job ghi có audit intent trước thay đổi và audit result khi kết thúc.
- `NFR-USE-006`: SCR-011 hiển thị 4/4 mục của `result.preview` trước khi Operator xác nhận nhập snapshot.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FEED-056` | Không xuất dữ liệu riêng của máy | 2 |
| `BR-CON-005` | Bắt buộc dry-run cho `feeds_import`; xác nhận ≤ 15 phút, cùng phiên, cùng SHA-256 nội dung và `force` | 4–9, 9a |
| `BR-CON-004` | Chống CSRF; ngoại lệ 2: `POST /api/v1/feed-snapshots` nhận `application/gzip`, vẫn bắt buộc `X-QP-CSRF`, `Origin` | 5, 9, 5b |
| `BR-CLI-003` | `--dry-run` 0 thay đổi; lệnh ghi mới cần xác nhận TTY hoặc `--yes` | 6, 3a |
| `BR-FEED-010`, `BR-FEED-055` | Toàn vẹn và quy tắc nhập snapshot | 6, 11 |
| `BR-FEED-015` | Một tiến trình giữ `feeds/.lock` | 10, 10b |
| `BR-FEED-051` | Thay bundle nguyên tử | 12 |
| `BR-FEED-053`, `BR-FEED-054` | Khởi tạo lần đầu, snapshot đóng gói mới hơn | 3b |
| `BR-FEED-005`, `BR-DATA-001` | Độ tươi sau khi nhập | 14a |
| `BR-CON-009` | Upload ≤ 20 MiB | 5, 9 |
| `BR-JOB-003`, `BR-AUD-001`, `BR-AUD-004` | Job dry-run là `read`, `feeds import` là job `write`; ghi audit; đóng khi lỗi | 5, 9, 10, 13 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FEED-CMD-004` | Lệnh `feeds export` (bí danh `snapshot export`) | 1 |
| `FR-FEED-SNAP-002` | Xuất snapshot | 2 |
| `FR-CON-FEED-002` | Nhập snapshot qua console (2 bước dry-run → xác nhận) | 4–9, 14 |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | 7, 8 |
| `FR-CLI-SAFE-001` | `--dry-run` và xác nhận cho lệnh thay đổi | 6, 3a |
| `FR-FEED-SNAP-003` | Nhập snapshot | 6, 11, 12 |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | 6, 10–13 |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | 3b |

### Giao diện và API liên quan
- Màn hình: `SCR-008` (khối "Nhập snapshot"), `SCR-011` (xem trước dry-run và xác nhận).
- API: `POST /api/v1/feed-snapshots` gọi 2 lần (`?dry_run=true[&force=true]`, rồi `?confirm_dry_run_job_id=<dry_job_id>[&force=true]`), `GET /api/v1/jobs/{job_id}` (`result.preview` của job dry-run, trạng thái job ghi), `GET /api/v1/feeds`. `feeds export` chỉ có ở CLI (DOC-API-QP-001 §5.3). Hợp đồng chi tiết: DOC-API-QP-001 §2.13.3, DOC-API-QP-002 §6.2, DOC-API-QP-004 §2 dòng #6 và §2.2.

### Quan hệ với use case khác
- Include UC-CON-003 (xem trước dry-run và xác nhận) cho bước 4–9; `feeds_import` dùng endpoint mặt tiền `POST /api/v1/feed-snapshots` thay cho `POST /api/v1/jobs`.
- Phase 2: UC-FLT-004 tự động hoá chuỗi xuất → đẩy → nhập từ máy trung tâm.
- Snapshot đóng gói do UC-FEED-005 tạo.

### Ghi chú, mâu thuẫn và tài liệu tham chiếu
- Đã quyết: bản 1.0.0 của DOC-SRS-QP-FLOW-001 §6.2 mục 1 ghi `feeds_import` là job `write` nhưng không có dry-run, trái `BR-CON-005`. `BR-CON-005` 1.0.1 (DOC-SRS-QP-BR-001 §6 mục 2) quyết bắt buộc dry-run cho `feeds_import`, không thuộc ngoại lệ; bước xác nhận tải lại file, console chỉ tạo job ghi khi SHA-256 nội dung nhận và `force` bằng giá trị của job dry-run. DOC-SRS-QP-FLOW-001 1.0.1 §6.2 mục 1 ghi "đã đóng" (PO + Dev); luồng chính bản 1.0.1 của tài liệu này vẽ theo quyết định đó.
- Cần cập nhật theo (ngoài phạm vi file này): wireframe `html-wireframe/feed-status.html` (khối "Nhập snapshot" đặt `dryNeeded: false`, gọi `POST /api/v1/feed-snapshots` 1 lần) và `html-wireframe/fleet-rollout.html` (ghi "feeds import không có --dry-run") còn theo bản trước `BR-CON-005` 1.0.1.
- Nguồn: [business-rules.md `BR-CON-005`, §6 mục 2](../srs/business-rules.md), [functional-requirements.md `FR-CON-FEED-002`](../srs/functional-requirements.md), [data-sources-cache-cli.md §4, §6.2](../srs/data-sources-cache-cli.md), [flows.md §2.2, §6.2 mục 1](../srs/flows.md), [api-spec.md §2.13.3](../api/api-spec.md), [api-spec-core.md §6.2](../api/api-spec-core.md), [api-spec-jobs.md §2.2](../api/api-spec-jobs.md).
