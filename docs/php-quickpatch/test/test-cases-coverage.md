---
id: DOC-TC-QP-COV
title: Ma trận độ phủ BR, ERR, NFR, chuyển trạng thái → test case — php-quickpatch v2
version: 1.0.2
phase: Testing
domain: Security Patch Management
tags: [test-cases, coverage, traceability, business-rules, error-matrix, nfr, state-transition, openba]
depends_on:
  - DOC-TC-QP-000
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-STATE-001
  - DOC-SRS-QP-ENV-001
  - DOC-AC-QP-000
  - DOC-RTM-QP-001
related_diagrams:
  - DIAG-STATE-QP-JOB-002
  - DIAG-STATE-QP-PLAN-002
  - DIAG-STATE-QP-ENV-003
  - DIAG-STATE-QP-CHK-001
  - DIAG-STATE-QP-FEED-001
  - DIAG-STATE-QP-FEED-002
  - DIAG-STATE-QP-CON-001
  - DIAG-STATE-QP-AUTH-001
author: BA Agent
last_updated: 2026-10-22
---

# Ma trận độ phủ BR, ERR, NFR, chuyển trạng thái → test case — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo ma trận phủ 198/198 BR và 120/120 ERR của registry SRS bằng 402 test case; NFR liên kết mức story |
| 1.0.1 | 2026-10-22 | BA Agent | Đối chiếu lại với error-matrix v1.0.1 (125 mã) và 404 test case hiện có: §3 thêm 5 mã `ERR-JOB-429-02` (`TC-CON-031`, `TC-CON-103`), `ERR-UPG-409-03` (`TC-UPG-022`, `TC-UPG-108`), `ERR-FLT-422-03` (`TC-FLT-009`), `ERR-FEED-503-03`, `ERR-HC-412-04`; tiêu đề §3 sửa từ "120/120" thành 123/125 mã có test case ghi mã, nêu rõ 2 mã tách chưa có test case ghi mã; sửa điều kiện `ERR-FEED-503-01`, `ERR-HC-412-02` theo bản tách mức độ; §2 thêm `TC-UPG-108` vào `BR-ENV-003`, `TC-CON-103` vào `BR-JOB-007`; thêm §5 truy vết 97/97 mã chuyển trạng thái `T-*` của DOC-SRS-QP-STATE-001 → test case kèm mức phủ (69 đủ, 14 một phần, 14 chưa phủ, trong đó 4 là chuyển `ĐX`) và lý do từng mã chưa phủ; §5.10 liệt kê việc cần làm ở test-cases.md §4, các file test case, rtm.md, states.md; §1 thêm cách đọc §5 và số liệu 404 test case; frontmatter thêm DOC-SRS-QP-STATE-001 và 8 sơ đồ trạng thái; mục tham chiếu đổi thành §6 |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review, đối chiếu lại cột "BR / ERR kiểm" của 421 test case hiện hành (thêm 17: `TC-PTCH-101`..`106`, `TC-CLI-102`..`104`, `TC-UPG-109`..`113`, `TC-JOB-025`, `TC-JOB-101`, `TC-JOB-102`): §2 thêm `BR-AUD-006` (`TC-JOB-102`) và `BR-ENV-013` (`TC-UPG-110`), tiêu đề 198/198 → 200/200 BR, nêu nguồn 2 BR mới; §3 theo error-matrix v1.1.0 thêm `ERR-CLI-412-01` (`TC-CLI-102`..`104`, `TC-FEED-105`), `ERR-PTCH-409-01` (`TC-PTCH-103`), `ERR-PTCH-500-01` (`TC-PTCH-104`), `ERR-UPG-409-04` (`TC-UPG-111`), tiêu đề 123/125 → 129/129 mã, ghi trạng thái đề xuất của 3 mã; dòng `ERR-JOB-429-02` bỏ ghi chú `TC-JOB-018` (đã sinh lại, không còn kiểm giới hạn luồng), thêm `TC-JOB-025`; `ERR-FEED-503-03` có `TC-FEED-002`, `TC-FEED-024`, `ERR-FEED-503-01` bỏ `TC-FEED-002` (8 → 7); `ERR-HC-412-04` có `TC-UPG-109`; 31 dòng BR/ERR khác thêm test case mới; §4 thêm 5 NFR chưa có dòng (`NFR-CMP-003`, `NFR-FEED-002`, `NFR-FEED-007`, `NFR-MNT-003`, `NFR-MNT-004`) liên kết trực tiếp tới test case đo chỉ tiêu, `NFR-PERF-003` thêm `TC-JOB-025`; thêm §4.1 mức phủ và việc cần làm cho 5 NFR (gồm thêm tham chiếu NFR vào story ở backlog.md); §1 cập nhật số liệu 421 test case và ghi §5 chưa đánh giá lại; §5.10 mục 1, 3–6 cập nhật trạng thái; §6 cập nhật phiên bản nguồn; frontmatter thêm DOC-SRS-QP-ENV-001, DOC-RTM-QP-001 |

## 1. Cách đọc
- Mỗi dòng liệt kê mọi test case có mã BR/ERR trong cột "BR / ERR kiểm"; mã TC liên kết tới file chứa test case.
- Một BR/ERR có thể được kiểm bởi nhiều test case; cột "Số TC" dùng để ưu tiên chọn test case hồi quy (chọn ≥ 1 test case mỗi mã).
- Bảng NFR (§4) liên kết theo story: test case thuộc story có tham chiếu NFR; NFR hiệu năng/dung lượng được đo trong các test case có KQ định lượng tương ứng. NFR chưa có story tham chiếu được liên kết trực tiếp tới test case đo chỉ tiêu, mức phủ và việc cần làm ở §4.1.
- Bảng chuyển trạng thái (§5) liên kết mỗi mã `T-*` của [states.md](../srs/states.md) (DOC-SRS-QP-STATE-001) với test case kiểm sự kiện, điều kiện bảo vệ và trạng thái đích của chuyển đó; mã test case kèm KQ hoặc dòng dữ liệu cụ thể. Test case chưa ghi mã `T-*` trong cột "BR / ERR kiểm", nên §5 là nơi duy nhất giữ truy vết này tới khi các file test case bổ sung.
- §2–§4 đếm trên 421 test case: 404 test case của bản 1.0.1 và 17 test case thêm sau đó — `TC-PTCH-101`..`TC-PTCH-106`, `TC-CLI-102`..`TC-CLI-104` ([test-cases-ptch-cli-rpt.md](test-cases-ptch-cli-rpt.md) v1.0.1); `TC-UPG-109`..`TC-UPG-113` ([test-cases-upg.md](test-cases-upg.md) v1.0.2); `TC-JOB-025`, `TC-JOB-101`, `TC-JOB-102` ([test-cases-job-flt.md](test-cases-job-flt.md) v1.0.2). Cột "BR / ERR kiểm" của test case được đọc lại ở bản hiện hành của từng file, gồm các test case sinh lại `TC-UPG-022`, `TC-JOB-018` và `TC-FEED-002`, `TC-FEED-024` (đổi mã `ERR-FEED-503-*` ở [test-cases-feed.md](test-cases-feed.md) v1.0.1).
- §5 giữ kết quả đánh giá của bản 1.0.1 trên 404 test case; chưa đánh giá lại với 17 test case trên (vd `TC-UPG-112`, `TC-UPG-113` được file chủ ghi là phủ `T-SW-07`, `T-SW-10`).

## 2. BR → test case (200/200 BR có ≥ 1 test case)
Nguồn danh sách mã: 198 BR của registry SRS bản 1.0.0 và 2 BR thêm ở bản 1.0.1 của tài liệu nguồn: `BR-AUD-006` ([business-rules.md](../srs/business-rules.md) v1.0.1), `BR-ENV-013` ([environment-playbooks.md](../srs/environment-playbooks.md) v1.0.1).

| BR | Tên quy tắc | Số TC | Test case |
| :--- | :--- | :---: | :--- |
| `BR-SEC-001` | KEV ưu tiên cao nhất | 3 | [`TC-ASMT-013`](test-cases.md), [`TC-ASMT-017`](test-cases.md), [`TC-FEED-017`](test-cases-feed.md) |
| `BR-SEC-002` | Điều kiện `ok-backport` | 5 | [`TC-FEED-023`](test-cases-feed.md), [`TC-FEED-025`](test-cases-feed.md), [`TC-CLI-012`](test-cases-ptch-cli-rpt.md), [`TC-SCN-104`](test-cases.md), [`TC-SCN-105`](test-cases.md) |
| `BR-SEC-003` | Không xoá webshell | 4 | [`TC-SCAN-010`](test-cases.md), [`TC-SCAN-011`](test-cases.md), [`TC-SCAN-012`](test-cases.md), [`TC-PTCH-016`](test-cases-ptch-cli-rpt.md) |
| `BR-DATA-001` | Cảnh báo tuổi dữ liệu | 6 | [`TC-SCN-006`](test-cases.md), [`TC-ASMT-004`](test-cases.md), [`TC-ASMT-012`](test-cases.md), [`TC-FEED-030`](test-cases-feed.md), [`TC-CLI-011`](test-cases-ptch-cli-rpt.md), [`TC-FEED-102`](test-cases-feed.md) |
| `BR-DATA-002` | Nguồn mốc bản vá | 5 | [`TC-FEED-008`](test-cases-feed.md), [`TC-PTCH-017`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-019`](test-cases-ptch-cli-rpt.md), [`TC-CLI-010`](test-cases-ptch-cli-rpt.md), [`TC-FEED-101`](test-cases-feed.md) |
| `BR-UPG-001` | Không thay runtime tại chỗ khi khác nhánh | 3 | [`TC-UPG-004`](test-cases-upg.md), [`TC-UPG-006`](test-cases-upg.md), [`TC-UPG-042`](test-cases-upg.md) |
| `BR-UPG-002` | Điều kiện chuyển site | 6 | [`TC-PLAN-009`](test-cases-plan-cmpt.md), [`TC-CMPT-028`](test-cases-plan-cmpt.md), [`TC-CMPT-029`](test-cases-plan-cmpt.md), [`TC-CMPT-030`](test-cases-plan-cmpt.md), [`TC-UPG-013`](test-cases-upg.md), [`TC-UPG-023`](test-cases-upg.md) |
| `BR-UPG-003` | Dừng khi health check thất bại | 8 | [`TC-UPG-022`](test-cases-upg.md), [`TC-UPG-023`](test-cases-upg.md), [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-035`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md), [`TC-UPG-111`](test-cases-upg.md), [`TC-UPG-112`](test-cases-upg.md), [`TC-UPG-113`](test-cases-upg.md) |
| `BR-UPG-004` | Đích bị cấm | 6 | [`TC-SCN-003`](test-cases.md), [`TC-ASMT-005`](test-cases.md), [`TC-ASMT-007`](test-cases.md), [`TC-PLAN-002`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md), [`TC-SCN-106`](test-cases.md) |
| `BR-SEC-004` | Package mã độc | 2 | [`TC-ASMT-014`](test-cases.md), [`TC-CON-034`](test-cases-con.md) |
| `BR-SEC-005` | Kiểm checksum mọi tải xuống thực thi | 6 | [`TC-CMPT-001`](test-cases-plan-cmpt.md), [`TC-CMPT-002`](test-cases-plan-cmpt.md), [`TC-PTCH-008`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-009`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-015`](test-cases-ptch-cli-rpt.md), [`TC-UPG-102`](test-cases-upg.md) |
| `BR-SEC-006` | Không để lộ bí mật | 5 | [`TC-FEED-053`](test-cases-feed.md), [`TC-CLI-003`](test-cases-ptch-cli-rpt.md), [`TC-RPT-003`](test-cases-ptch-cli-rpt.md), [`TC-JOB-013`](test-cases-job-flt.md), [`TC-UPG-111`](test-cases-upg.md) |
| `BR-DATA-003` | Mở rộng phạm vi dữ liệu gửi ra ngoài (đề xuất) | 5 | [`TC-PLAN-013`](test-cases-plan-cmpt.md), [`TC-CMPT-013`](test-cases-plan-cmpt.md), [`TC-CMPT-014`](test-cases-plan-cmpt.md), [`TC-CMPT-015`](test-cases-plan-cmpt.md), [`TC-CMPT-018`](test-cases-plan-cmpt.md) |
| `BR-DATA-004` | Thứ tự ưu tiên khi tài liệu mâu thuẫn | 2 | [`TC-FEED-102`](test-cases-feed.md), [`TC-UPG-101`](test-cases-upg.md) |
| `BR-UPG-005` | Chuyển site phải thuộc kế hoạch | 4 | [`TC-PLAN-018`](test-cases-plan-cmpt.md), [`TC-CLI-020`](test-cases-ptch-cli-rpt.md), [`TC-CLI-021`](test-cases-ptch-cli-rpt.md), [`TC-UPG-021`](test-cases-upg.md) |
| `BR-UPG-006` | Vá cùng nhánh trước nâng nhánh | 2 | [`TC-PLAN-005`](test-cases-plan-cmpt.md), [`TC-PLAN-007`](test-cases-plan-cmpt.md) |
| `BR-SCAN-001` | Quét chỉ đọc | 5 | [`TC-SCAN-001`](test-cases.md), [`TC-SCAN-007`](test-cases.md), [`TC-SCAN-010`](test-cases.md), [`TC-SCAN-015`](test-cases.md), [`TC-CLI-025`](test-cases-ptch-cli-rpt.md) |
| `BR-SCAN-002` | Giới hạn thời gian thăm dò | 2 | [`TC-SCAN-005`](test-cases.md), [`TC-SCAN-009`](test-cases.md) |
| `BR-SCAN-003` | Phạm vi tìm dự án | 1 | [`TC-SCAN-009`](test-cases.md) |
| `BR-ASMT-001` | Loại ứng viên | 4 | [`TC-ASMT-005`](test-cases.md), [`TC-SCN-101`](test-cases.md), [`TC-SCN-106`](test-cases.md), [`TC-SCN-107`](test-cases.md) |
| `BR-ASMT-002` | Ứng viên được chọn | 6 | [`TC-ASMT-007`](test-cases.md), [`TC-PLAN-003`](test-cases-plan-cmpt.md), [`TC-PLAN-004`](test-cases-plan-cmpt.md), [`TC-SCN-101`](test-cases.md), [`TC-SCN-107`](test-cases.md), [`TC-SCN-110`](test-cases.md) |
| `BR-ASMT-003` | So sánh nhất quán | 2 | [`TC-ASMT-008`](test-cases.md), [`TC-CON-020`](test-cases-con.md) |
| `BR-ASMT-004` | Thứ tự xếp hạng (đề xuất, PRD Q-09) | 2 | [`TC-ASMT-011`](test-cases.md), [`TC-ASMT-013`](test-cases.md) |
| `BR-ASMT-005` | Mức độ advisory dependency | 3 | [`TC-ASMT-014`](test-cases.md), [`TC-ASMT-016`](test-cases.md), [`TC-CON-032`](test-cases-con.md) |
| `BR-PLAN-001` | Đích khác đề xuất | 3 | [`TC-PLAN-003`](test-cases-plan-cmpt.md), [`TC-CON-025`](test-cases-con.md), [`TC-SCN-108`](test-cases.md) |
| `BR-PLAN-002` | Một kế hoạch hiệu lực mỗi runtime | 4 | [`TC-PLAN-006`](test-cases-plan-cmpt.md), [`TC-PLAN-007`](test-cases-plan-cmpt.md), [`TC-CLI-016`](test-cases-ptch-cli-rpt.md), [`TC-CON-024`](test-cases-con.md) |
| `BR-PLAN-003` | Điều kiện duyệt | 5 | [`TC-PLAN-020`](test-cases-plan-cmpt.md), [`TC-PLAN-021`](test-cases-plan-cmpt.md), [`TC-PLAN-025`](test-cases-plan-cmpt.md), [`TC-CLI-016`](test-cases-ptch-cli-rpt.md), [`TC-CON-026`](test-cases-con.md) |
| `BR-PLAN-004` | Site canary | 2 | [`TC-PLAN-008`](test-cases-plan-cmpt.md), [`TC-PLAN-010`](test-cases-plan-cmpt.md) |
| `BR-PLAN-005` | Trạng thái mục và ánh xạ PRD | 5 | [`TC-PLAN-014`](test-cases-plan-cmpt.md), [`TC-PLAN-015`](test-cases-plan-cmpt.md), [`TC-PLAN-016`](test-cases-plan-cmpt.md), [`TC-CON-027`](test-cases-con.md), [`TC-CON-028`](test-cases-con.md) |
| `BR-PLAN-006` | Kế hoạch lỗi thời | 2 | [`TC-PLAN-022`](test-cases-plan-cmpt.md), [`TC-PLAN-023`](test-cases-plan-cmpt.md) |
| `BR-PLAN-007` | Kết thúc kế hoạch | 2 | [`TC-PLAN-020`](test-cases-plan-cmpt.md), [`TC-PLAN-023`](test-cases-plan-cmpt.md) |
| `BR-CMPT-001` | Tập file quét | 2 | [`TC-CMPT-006`](test-cases-plan-cmpt.md), [`TC-CMPT-030`](test-cases-plan-cmpt.md) |
| `BR-CMPT-002` | Binary chạy PHPCS | 2 | [`TC-CMPT-008`](test-cases-plan-cmpt.md), [`TC-CMPT-009`](test-cases-plan-cmpt.md) |
| `BR-CMPT-003` | Composer trên bản sao | 1 | [`TC-CMPT-015`](test-cases-plan-cmpt.md) |
| `BR-CMPT-004` | Không chạy mã dự án | 3 | [`TC-CMPT-015`](test-cases-plan-cmpt.md), [`TC-UPG-029`](test-cases-upg.md), [`TC-CMPT-102`](test-cases-plan-cmpt.md) |
| `BR-CMPT-005` | Thời gian tối đa | 1 | [`TC-CMPT-005`](test-cases-plan-cmpt.md) |
| `BR-CMPT-006` | Công cụ quét cố định phiên bản | 2 | [`TC-CMPT-001`](test-cases-plan-cmpt.md), [`TC-CMPT-003`](test-cases-plan-cmpt.md) |
| `BR-PTCH-001` | Mốc vá từ bundle | 5 | [`TC-PTCH-001`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-003`](test-cases-ptch-cli-rpt.md), [`TC-CLI-010`](test-cases-ptch-cli-rpt.md), [`TC-SCN-106`](test-cases.md), [`TC-ASMT-101`](test-cases.md) |
| `BR-PTCH-002` | Nhóm gói theo nguồn cài | 2 | [`TC-PTCH-002`](test-cases-ptch-cli-rpt.md), [`TC-SCN-105`](test-cases.md) |
| `BR-PTCH-003` | Giới hạn theo quyền và môi trường | 3 | [`TC-SCN-014`](test-cases.md), [`TC-SCN-016`](test-cases.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) |
| `BR-PTCH-004` | Mitigation tạm | 7 | [`TC-PTCH-003`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-005`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-006`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-007`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-018`](test-cases-ptch-cli-rpt.md), [`TC-SCN-106`](test-cases.md), [`TC-PTCH-106`](test-cases-ptch-cli-rpt.md) |
| `BR-PTCH-005` | Vá Node.js tarball | 3 | [`TC-PTCH-008`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-010`](test-cases-ptch-cli-rpt.md), [`TC-SCN-109`](test-cases.md) |
| `BR-PTCH-006` | Vá cấp dự án | 5 | [`TC-PTCH-011`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-012`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-013`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-014`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-105`](test-cases-ptch-cli-rpt.md) |
| `BR-PTCH-007` | Restart sau vá cùng nhánh | 4 | [`TC-PTCH-020`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-022`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-104`](test-cases-ptch-cli-rpt.md), [`TC-JOB-101`](test-cases-job-flt.md) |
| `BR-PTCH-008` | Rollback lượt chạy | 10 | [`TC-PTCH-026`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-027`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md), [`TC-CON-036`](test-cases-con.md), [`TC-CON-037`](test-cases-con.md), [`TC-PTCH-101`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-102`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-105`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-106`](test-cases-ptch-cli-rpt.md), [`TC-CLI-103`](test-cases-ptch-cli-rpt.md) |
| `BR-AUTH-001` | Token phiên `serve` | 3 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-003`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `BR-AUTH-002` | So sánh hằng thời gian | 1 | [`TC-CON-102`](test-cases-con.md) |
| `BR-AUTH-003` | Giới hạn thử sai | 2 | [`TC-CON-006`](test-cases-con.md), [`TC-CON-007`](test-cases-con.md) |
| `BR-AUTH-004` | Phiên trình duyệt | 3 | [`TC-CON-005`](test-cases-con.md), [`TC-CON-007`](test-cases-con.md), [`TC-CON-010`](test-cases-con.md) |
| `BR-AUTH-005` | Bearer cho client API | 3 | [`TC-CON-007`](test-cases-con.md), [`TC-CON-008`](test-cases-con.md), [`TC-CON-009`](test-cases-con.md) |
| `BR-AUTH-006` | Token qua URL fragment | 2 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-005`](test-cases-con.md) |
| `BR-CON-001` | Chỉ loopback | 2 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `BR-CON-002` | Cổng cố định, không tự tăng | 2 | [`TC-CON-002`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `BR-CON-003` | Kiểm tra Host chống DNS rebinding | 3 | [`TC-CON-011`](test-cases-con.md), [`TC-CON-012`](test-cases-con.md), [`TC-CON-013`](test-cases-con.md) |
| `BR-CON-004` | Chống CSRF | 3 | [`TC-CON-014`](test-cases-con.md), [`TC-CON-015`](test-cases-con.md), [`TC-CON-016`](test-cases-con.md) |
| `BR-CON-005` | `job.params_sha256`, `job.session_hash`, `job.serve_instance_id`, `job.bundle_id`, `job.scan_fingerprint`, `job.created_at` đủ để kiểm "dry-run hợp lệ" | 7 | [`TC-PLAN-017`](test-cases-plan-cmpt.md), [`TC-PLAN-018`](test-cases-plan-cmpt.md), [`TC-PLAN-019`](test-cases-plan-cmpt.md), [`TC-CON-048`](test-cases-con.md), [`TC-CON-049`](test-cases-con.md), [`TC-CON-050`](test-cases-con.md), [`TC-PTCH-101`](test-cases-ptch-cli-rpt.md) |
| `BR-CON-006` | Xác nhận kép | 4 | [`TC-UPG-019`](test-cases-upg.md), [`TC-UPG-034`](test-cases-upg.md), [`TC-UPG-047`](test-cases-upg.md), [`TC-CON-051`](test-cases-con.md) |
| `BR-CON-007` | Header và tài nguyên tĩnh | 3 | [`TC-CON-052`](test-cases-con.md), [`TC-CON-053`](test-cases-con.md), [`TC-CON-054`](test-cases-con.md) |
| `BR-CON-008` | Danh sách trắng lệnh | 5 | [`TC-SCAN-011`](test-cases.md), [`TC-CON-034`](test-cases-con.md), [`TC-CON-055`](test-cases-con.md), [`TC-CON-056`](test-cases-con.md), [`TC-CON-057`](test-cases-con.md) |
| `BR-CON-009` | Giới hạn request | 4 | [`TC-CON-041`](test-cases-con.md), [`TC-CON-059`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md), [`TC-CON-101`](test-cases-con.md) |
| `BR-CON-010` | Quyền console | 1 | [`TC-CON-022`](test-cases-con.md) |
| `BR-JOB-001` | Giới hạn đồng thời | 2 | [`TC-JOB-001`](test-cases-job-flt.md), [`TC-JOB-002`](test-cases-job-flt.md) |
| `BR-JOB-002` | Khoá dùng chung với CLI | 8 | [`TC-PTCH-021`](test-cases-ptch-cli-rpt.md), [`TC-CLI-009`](test-cases-ptch-cli-rpt.md), [`TC-CLI-015`](test-cases-ptch-cli-rpt.md), [`TC-JOB-004`](test-cases-job-flt.md), [`TC-JOB-005`](test-cases-job-flt.md), [`TC-JOB-006`](test-cases-job-flt.md), [`TC-UPG-110`](test-cases-upg.md), [`TC-JOB-101`](test-cases-job-flt.md) |
| `BR-JOB-003` | Phân loại job | 2 | [`TC-CON-055`](test-cases-con.md), [`TC-JOB-001`](test-cases-job-flt.md) |
| `BR-JOB-004` | Huỷ job | 5 | [`TC-CON-029`](test-cases-con.md), [`TC-CON-030`](test-cases-con.md), [`TC-JOB-007`](test-cases-job-flt.md), [`TC-JOB-008`](test-cases-job-flt.md), [`TC-JOB-009`](test-cases-job-flt.md) |
| `BR-JOB-005` | Đối soát khi khởi động lại | 3 | [`TC-JOB-010`](test-cases-job-flt.md), [`TC-JOB-011`](test-cases-job-flt.md), [`TC-JOB-012`](test-cases-job-flt.md) |
| `BR-JOB-006` | Lưu log | 4 | [`TC-CON-031`](test-cases-con.md), [`TC-JOB-013`](test-cases-job-flt.md), [`TC-JOB-014`](test-cases-job-flt.md), [`TC-JOB-015`](test-cases-job-flt.md) |
| `BR-JOB-007` | Luồng SSE | 7 | [`TC-CON-029`](test-cases-con.md), [`TC-CON-031`](test-cases-con.md), [`TC-JOB-016`](test-cases-job-flt.md), [`TC-JOB-017`](test-cases-job-flt.md), [`TC-JOB-018`](test-cases-job-flt.md), [`TC-CON-103`](test-cases-con.md), [`TC-JOB-025`](test-cases-job-flt.md) |
| `BR-JOB-008` | Ánh xạ mã thoát | 3 | [`TC-JOB-002`](test-cases-job-flt.md), [`TC-JOB-003`](test-cases-job-flt.md), [`TC-UPG-110`](test-cases-upg.md) |
| `BR-AUD-001` | Sự kiện phải ghi | 3 | [`TC-JOB-019`](test-cases-job-flt.md), [`TC-UPG-022`](test-cases-upg.md), [`TC-UPG-111`](test-cases-upg.md) |
| `BR-AUD-002` | Chỉ nối thêm | 3 | [`TC-CON-047`](test-cases-con.md), [`TC-JOB-019`](test-cases-job-flt.md), [`TC-JOB-024`](test-cases-job-flt.md) |
| `BR-AUD-003` | Chuỗi hash | 8 | [`TC-RPT-005`](test-cases-ptch-cli-rpt.md), [`TC-CON-046`](test-cases-con.md), [`TC-JOB-021`](test-cases-job-flt.md), [`TC-JOB-022`](test-cases-job-flt.md), [`TC-JOB-023`](test-cases-job-flt.md), [`TC-JOB-024`](test-cases-job-flt.md), [`TC-FLT-011`](test-cases-job-flt.md), [`TC-JOB-102`](test-cases-job-flt.md) |
| `BR-AUD-004` | Đóng khi lỗi | 2 | [`TC-JOB-020`](test-cases-job-flt.md), [`TC-JOB-021`](test-cases-job-flt.md) |
| `BR-AUD-005` | Che dữ liệu | 1 | [`TC-JOB-019`](test-cases-job-flt.md) |
| `BR-AUD-006` | Neo chuỗi hash | 1 | [`TC-JOB-102`](test-cases-job-flt.md) (KQ1 neo `audit_anchor` trong `result.json`; KQ2 neo trên SCR-010 và báo cáo bằng chứng; KQ3–KQ5 cắt 3 bản ghi cuối và chuỗi tính lại → `ERR-AUD-409-01` khi đối chiếu `--anchor`) |
| `BR-CLI-001` | Tương thích schema JSON | 4 | [`TC-CLI-001`](test-cases-ptch-cli-rpt.md), [`TC-CLI-004`](test-cases-ptch-cli-rpt.md), [`TC-CLI-006`](test-cases-ptch-cli-rpt.md), [`TC-CLI-013`](test-cases-ptch-cli-rpt.md) |
| `BR-CLI-002` | Tương thích ngược v0.1 | 6 | [`TC-SCAN-008`](test-cases.md), [`TC-CLI-007`](test-cases-ptch-cli-rpt.md), [`TC-CLI-008`](test-cases-ptch-cli-rpt.md), [`TC-CLI-027`](test-cases-ptch-cli-rpt.md), [`TC-CLI-101`](test-cases-ptch-cli-rpt.md), [`TC-CLI-104`](test-cases-ptch-cli-rpt.md) |
| `BR-CLI-003` | Dry-run và xác nhận | 7 | [`TC-PTCH-004`](test-cases-ptch-cli-rpt.md), [`TC-CLI-018`](test-cases-ptch-cli-rpt.md), [`TC-CLI-019`](test-cases-ptch-cli-rpt.md), [`TC-CLI-025`](test-cases-ptch-cli-rpt.md), [`TC-CLI-026`](test-cases-ptch-cli-rpt.md), [`TC-CLI-027`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-101`](test-cases-ptch-cli-rpt.md) |
| `BR-CLI-004` | Mã thoát | 7 | [`TC-SCAN-008`](test-cases.md), [`TC-CLI-002`](test-cases-ptch-cli-rpt.md), [`TC-CLI-009`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-103`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-104`](test-cases-ptch-cli-rpt.md), [`TC-CLI-102`](test-cases-ptch-cli-rpt.md), [`TC-CLI-103`](test-cases-ptch-cli-rpt.md) |
| `BR-CLI-005` | Quyền chạy | 7 | [`TC-SCN-014`](test-cases.md), [`TC-SCN-015`](test-cases.md), [`TC-CLI-020`](test-cases-ptch-cli-rpt.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md), [`TC-CLI-102`](test-cases-ptch-cli-rpt.md), [`TC-CLI-104`](test-cases-ptch-cli-rpt.md), [`TC-FEED-105`](test-cases-feed.md) |
| `BR-CLI-006` | Ngôn ngữ | 1 | [`TC-CLI-101`](test-cases-ptch-cli-rpt.md) |
| `BR-RPT-001` | Định dạng báo cáo | 4 | [`TC-CLI-022`](test-cases-ptch-cli-rpt.md), [`TC-RPT-001`](test-cases-ptch-cli-rpt.md), [`TC-RPT-003`](test-cases-ptch-cli-rpt.md), [`TC-CON-045`](test-cases-con.md) |
| `BR-RPT-002` | Nguồn gốc dữ liệu | 3 | [`TC-CLI-022`](test-cases-ptch-cli-rpt.md), [`TC-RPT-001`](test-cases-ptch-cli-rpt.md), [`TC-RPT-004`](test-cases-ptch-cli-rpt.md) |
| `BR-RPT-003` | Không ghi đè, che bí mật | 3 | [`TC-CLI-023`](test-cases-ptch-cli-rpt.md), [`TC-RPT-002`](test-cases-ptch-cli-rpt.md), [`TC-RPT-003`](test-cases-ptch-cli-rpt.md) |
| `BR-FLT-001` | Không agent | 2 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `BR-FLT-002` | Xác thực SSH | 3 | [`TC-FLT-001`](test-cases-job-flt.md), [`TC-FLT-002`](test-cases-job-flt.md), [`TC-FLT-003`](test-cases-job-flt.md) |
| `BR-FLT-003` | Toàn vẹn gói CLI đẩy lên | 2 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `BR-FLT-004` | Timeout từ xa | 2 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `BR-FLT-005` | Chạy theo đợt | 2 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-008`](test-cases-job-flt.md) |
| `BR-FLT-006` | Độ tươi dữ liệu server | 1 | [`TC-FLT-012`](test-cases-job-flt.md) |
| `BR-FLT-007` | Phân phối snapshot | 2 | [`TC-FLT-013`](test-cases-job-flt.md), [`TC-FLT-015`](test-cases-job-flt.md) |
| `BR-FLT-008` | Vai trò Phase 2 | 5 | [`TC-FLT-004`](test-cases-job-flt.md), [`TC-FLT-005`](test-cases-job-flt.md), [`TC-FLT-006`](test-cases-job-flt.md), [`TC-FLT-008`](test-cases-job-flt.md), [`TC-FLT-010`](test-cases-job-flt.md) |
| `BR-SCN-001` | Gán kịch bản | 7 | [`TC-SCAN-004`](test-cases.md), [`TC-SCAN-005`](test-cases.md), [`TC-SCAN-006`](test-cases.md), [`TC-SCN-001`](test-cases.md), [`TC-SCN-002`](test-cases.md), [`TC-SCN-011`](test-cases.md), [`TC-SCN-013`](test-cases.md) |
| `BR-SCN-002` | Nguồn và độ tươi dữ liệu vòng đời | 2 | [`TC-FEED-101`](test-cases-feed.md), [`TC-FEED-102`](test-cases-feed.md) |
| `BR-SCN-003` | Tính trạng thái hỗ trợ | 7 | [`TC-SCN-005`](test-cases.md), [`TC-SCN-007`](test-cases.md), [`TC-SCN-101`](test-cases.md), [`TC-SCN-103`](test-cases.md), [`TC-SCN-107`](test-cases.md), [`TC-SCN-109`](test-cases.md), [`TC-SCN-110`](test-cases.md) |
| `BR-SCN-004` | Bản patch tối thiểu an toàn | 1 | [`TC-ASMT-101`](test-cases.md) |
| `BR-SCN-005` | Chọn nhánh đích PHP | 6 | [`TC-ASMT-005`](test-cases.md), [`TC-ASMT-006`](test-cases.md), [`TC-PLAN-001`](test-cases-plan-cmpt.md), [`TC-CMPT-025`](test-cases-plan-cmpt.md), [`TC-CMPT-026`](test-cases-plan-cmpt.md), [`TC-CMPT-027`](test-cases-plan-cmpt.md) |
| `BR-SCN-006` | Chọn nhánh đích Node.js | 2 | [`TC-PLAN-004`](test-cases-plan-cmpt.md), [`TC-SCN-107`](test-cases.md) |
| `BR-SCN-007` | Cấm nhánh trung gian trên production | 3 | [`TC-PLAN-002`](test-cases-plan-cmpt.md), [`TC-PLAN-004`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md) |
| `BR-SCN-008` | Vá cùng nhánh và nâng nhánh | 5 | [`TC-PLAN-017`](test-cases-plan-cmpt.md), [`TC-PTCH-001`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-004`](test-cases-ptch-cli-rpt.md), [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-020`](test-cases-upg.md) |
| `BR-SCN-009` | Ngưỡng health check sau chuyển (đề xuất, chờ PO duyệt) | 1 | [`TC-UPG-101`](test-cases-upg.md) |
| `BR-SCN-010` | Tự hoàn tác | 5 | [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-103`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md), [`TC-UPG-112`](test-cases-upg.md), [`TC-UPG-113`](test-cases-upg.md) |
| `BR-SCN-011` | Công cụ refactor tự động | 3 | [`TC-CMPT-031`](test-cases-plan-cmpt.md), [`TC-CMPT-032`](test-cases-plan-cmpt.md), [`TC-CMPT-033`](test-cases-plan-cmpt.md) |
| `BR-SCN-012` | Không đổi mặc định hệ thống khi cài song song | 2 | [`TC-UPG-004`](test-cases-upg.md), [`TC-UPG-039`](test-cases-upg.md) |
| `BR-SCN-013` | Phiên bản bất thường | 1 | [`TC-SCN-003`](test-cases.md) |
| `BR-SCN-014` | Gỡ nhánh cũ | 4 | [`TC-UPG-037`](test-cases-upg.md), [`TC-UPG-045`](test-cases-upg.md), [`TC-UPG-046`](test-cases-upg.md), [`TC-CON-036`](test-cases-con.md) |
| `BR-SCN-015` | CVE với gói distro | 4 | [`TC-FEED-023`](test-cases-feed.md), [`TC-FEED-024`](test-cases-feed.md), [`TC-SCN-103`](test-cases.md), [`TC-SCN-104`](test-cases.md) |
| `BR-SCN-016` | Điều kiện tiên quyết cài song song (đề xuất) | 3 | [`TC-UPG-001`](test-cases-upg.md), [`TC-UPG-002`](test-cases-upg.md), [`TC-UPG-003`](test-cases-upg.md) |
| `BR-SCN-017` | Ghi manifest | 11 | [`TC-PTCH-005`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-023`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-024`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-025`](test-cases-ptch-cli-rpt.md), [`TC-UPG-007`](test-cases-upg.md), [`TC-UPG-107`](test-cases-upg.md), [`TC-UPG-112`](test-cases-upg.md), [`TC-PTCH-102`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-103`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-105`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-106`](test-cases-ptch-cli-rpt.md) |
| `BR-SCN-018` | Thứ tự phụ thuộc mục | 5 | [`TC-SCN-012`](test-cases.md), [`TC-PLAN-016`](test-cases-plan-cmpt.md), [`TC-CMPT-020`](test-cases-plan-cmpt.md), [`TC-UPG-013`](test-cases-upg.md), [`TC-CON-027`](test-cases-con.md) |
| `BR-SCN-020` | Gán kịch bản Node.js | 5 | [`TC-SCN-002`](test-cases.md), [`TC-SCN-004`](test-cases.md), [`TC-SCN-107`](test-cases.md), [`TC-SCN-109`](test-cases.md), [`TC-SCN-110`](test-cases.md) |
| `BR-SCN-021` | Dải breaking change | 2 | [`TC-SCN-108`](test-cases.md), [`TC-CMPT-101`](test-cases-plan-cmpt.md) |
| `BR-SCN-022` | Native addon | 4 | [`TC-CMPT-016`](test-cases-plan-cmpt.md), [`TC-CMPT-017`](test-cases-plan-cmpt.md), [`TC-UPG-040`](test-cases-upg.md), [`TC-SCN-108`](test-cases.md) |
| `BR-SCN-023` | OpenSSL 3 | 2 | [`TC-UPG-041`](test-cases-upg.md), [`TC-UPG-107`](test-cases-upg.md) |
| `BR-SCN-024` | npm và lockfile | 1 | [`TC-CMPT-102`](test-cases-plan-cmpt.md) |
| `BR-SCN-025` | Ràng buộc `engines.node` | 3 | [`TC-PLAN-013`](test-cases-plan-cmpt.md), [`TC-CMPT-016`](test-cases-plan-cmpt.md), [`TC-CMPT-018`](test-cases-plan-cmpt.md) |
| `BR-SCN-026` | Cài song song Node.js | 2 | [`TC-UPG-006`](test-cases-upg.md), [`TC-UPG-039`](test-cases-upg.md) |
| `BR-SCN-027` | Chuyển ứng dụng và restart | 3 | [`TC-UPG-039`](test-cases-upg.md), [`TC-UPG-041`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md) |
| `BR-SCN-028` | glibc và nền tảng | 1 | [`TC-UPG-102`](test-cases-upg.md) |
| `BR-SCN-029` | Hạn duyệt kế hoạch nâng major | 5 | [`TC-PLAN-024`](test-cases-plan-cmpt.md), [`TC-PLAN-026`](test-cases-plan-cmpt.md), [`TC-CON-017`](test-cases-con.md), [`TC-SCN-109`](test-cases.md), [`TC-SCN-110`](test-cases.md) |
| `BR-SCN-030` | Bắt buộc staging và tệp ghim phiên bản | 1 | [`TC-SCN-108`](test-cases.md) |
| `BR-SCN-040` | Gán kịch bản PHP | 5 | [`TC-SCN-001`](test-cases.md), [`TC-SCN-003`](test-cases.md), [`TC-SCN-004`](test-cases.md), [`TC-SCN-101`](test-cases.md), [`TC-SCN-103`](test-cases.md) |
| `BR-SCN-041` | Dải breaking change cần quét | 3 | [`TC-CMPT-004`](test-cases-plan-cmpt.md), [`TC-CMPT-006`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md) |
| `BR-SCN-042` | Điều kiện ĐẠT của quét tương thích | 7 | [`TC-CMPT-007`](test-cases-plan-cmpt.md), [`TC-CMPT-009`](test-cases-plan-cmpt.md), [`TC-CMPT-010`](test-cases-plan-cmpt.md), [`TC-CMPT-011`](test-cases-plan-cmpt.md), [`TC-CMPT-012`](test-cases-plan-cmpt.md), [`TC-CMPT-028`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md) |
| `BR-SCN-043` | Loader mã hoá | 4 | [`TC-PLAN-012`](test-cases-plan-cmpt.md), [`TC-CMPT-022`](test-cases-plan-cmpt.md), [`TC-CMPT-023`](test-cases-plan-cmpt.md), [`TC-CMPT-024`](test-cases-plan-cmpt.md) |
| `BR-SCN-044` | Composer và platform | 3 | [`TC-PLAN-011`](test-cases-plan-cmpt.md), [`TC-CMPT-013`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md) |
| `BR-SCN-045` | Extension tương ứng | 5 | [`TC-PLAN-011`](test-cases-plan-cmpt.md), [`TC-CMPT-019`](test-cases-plan-cmpt.md), [`TC-CMPT-020`](test-cases-plan-cmpt.md), [`TC-CMPT-021`](test-cases-plan-cmpt.md), [`TC-UPG-009`](test-cases-upg.md) |
| `BR-SCN-046` | Sao chép cấu hình ini/pool | 4 | [`TC-CMPT-019`](test-cases-plan-cmpt.md), [`TC-CMPT-021`](test-cases-plan-cmpt.md), [`TC-UPG-007`](test-cases-upg.md), [`TC-UPG-009`](test-cases-upg.md) |
| `BR-SCN-047` | Site chạy `mod_php` | 2 | [`TC-UPG-017`](test-cases-upg.md), [`TC-UPG-018`](test-cases-upg.md) |
| `BR-SCN-048` | Trạng thái gói distro | 3 | [`TC-SCN-103`](test-cases.md), [`TC-SCN-104`](test-cases.md), [`TC-SCN-105`](test-cases.md) |
| `BR-SCN-049` | Hạn duyệt kế hoạch nâng cấp | 6 | [`TC-PLAN-005`](test-cases-plan-cmpt.md), [`TC-PLAN-024`](test-cases-plan-cmpt.md), [`TC-PLAN-025`](test-cases-plan-cmpt.md), [`TC-PLAN-026`](test-cases-plan-cmpt.md), [`TC-CON-017`](test-cases-con.md), [`TC-SCN-104`](test-cases.md) |
| `BR-SCN-050` | Bắt buộc staging | 1 | [`TC-SCN-102`](test-cases.md) |
| `BR-FEED-001` | TTL theo nguồn | 3 | [`TC-FEED-001`](test-cases-feed.md), [`TC-FEED-020`](test-cases-feed.md), [`TC-FEED-022`](test-cases-feed.md) |
| `BR-FEED-002` | Đồng bộ tăng dần NVD | 2 | [`TC-FEED-011`](test-cases-feed.md), [`TC-FEED-013`](test-cases-feed.md) |
| `BR-FEED-003` | Timeout và retry | 2 | [`TC-FEED-002`](test-cases-feed.md), [`TC-FEED-103`](test-cases-feed.md) |
| `BR-FEED-004` | Giới hạn tốc độ | 2 | [`TC-FEED-012`](test-cases-feed.md), [`TC-FEED-051`](test-cases-feed.md) |
| `BR-FEED-005` | Mức độ tươi và hiển thị tuổi dữ liệu | 10 | [`TC-SCN-006`](test-cases.md), [`TC-ASMT-004`](test-cases.md), [`TC-ASMT-009`](test-cases.md), [`TC-FEED-029`](test-cases-feed.md), [`TC-FEED-030`](test-cases-feed.md), [`TC-FEED-031`](test-cases-feed.md), [`TC-FEED-050`](test-cases-feed.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-038`](test-cases-con.md), [`TC-FEED-102`](test-cases-feed.md) |
| `BR-FEED-006` | Chuỗi dự phòng | 3 | [`TC-ASMT-018`](test-cases.md), [`TC-FEED-002`](test-cases-feed.md), [`TC-FEED-009`](test-cases-feed.md) |
| `BR-FEED-007` | Không ghi đè dữ liệu hợp lệ bằng phản hồi lỗi | 5 | [`TC-SCN-010`](test-cases.md), [`TC-FEED-006`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md), [`TC-FEED-103`](test-cases-feed.md), [`TC-FEED-106`](test-cases-feed.md) |
| `BR-FEED-008` | Lỗi nguồn không chặn lượt chạy | 5 | [`TC-ASMT-015`](test-cases.md), [`TC-FEED-002`](test-cases-feed.md), [`TC-FEED-004`](test-cases-feed.md), [`TC-FEED-021`](test-cases-feed.md), [`TC-CMPT-014`](test-cases-plan-cmpt.md) |
| `BR-FEED-009` | Phát hiện biến động bất thường | 3 | [`TC-FEED-006`](test-cases-feed.md), [`TC-FEED-018`](test-cases-feed.md), [`TC-FEED-019`](test-cases-feed.md) |
| `BR-FEED-010` | Toàn vẹn snapshot | 6 | [`TC-SCN-008`](test-cases.md), [`TC-SCN-009`](test-cases.md), [`TC-FEED-036`](test-cases-feed.md), [`TC-FEED-040`](test-cases-feed.md), [`TC-FEED-041`](test-cases-feed.md), [`TC-FEED-049`](test-cases-feed.md) |
| `BR-FEED-011` | Bảo vệ API key | 3 | [`TC-FEED-034`](test-cases-feed.md), [`TC-FEED-051`](test-cases-feed.md), [`TC-FEED-053`](test-cases-feed.md) |
| `BR-FEED-012` | Chế độ chỉ đọc bundle | 1 | [`TC-FEED-104`](test-cases-feed.md) |
| `BR-FEED-013` | Phạm vi dữ liệu gửi ra ngoài | 1 | [`TC-FEED-022`](test-cases-feed.md) |
| `BR-FEED-014` | Theo dõi CVE chưa đầy đủ | 1 | [`TC-FEED-013`](test-cases-feed.md) |
| `BR-FEED-015` | Một tiến trình đồng bộ | 2 | [`TC-FEED-003`](test-cases-feed.md), [`TC-JOB-006`](test-cases-job-flt.md) |
| `BR-FEED-016` | Bắt buộc HTTPS | 1 | [`TC-FEED-010`](test-cases-feed.md) |
| `BR-FEED-020` | Ưu tiên nguồn vòng đời | 3 | [`TC-SCN-005`](test-cases.md), [`TC-FEED-007`](test-cases-feed.md), [`TC-FEED-101`](test-cases-feed.md) |
| `BR-FEED-021` | Chuẩn hóa kiểu hỗn hợp | 1 | [`TC-FEED-107`](test-cases-feed.md) |
| `BR-FEED-022` | So khớp dải phiên bản | 3 | [`TC-FEED-014`](test-cases-feed.md), [`TC-FEED-015`](test-cases-feed.md), [`TC-FEED-016`](test-cases-feed.md) |
| `BR-FEED-023` | Khử trùng lặp, mã chuẩn | 2 | [`TC-FEED-011`](test-cases-feed.md), [`TC-FEED-028`](test-cases-feed.md) |
| `BR-FEED-024` | Tín hiệu bản bảo mật | 2 | [`TC-FEED-008`](test-cases-feed.md), [`TC-FEED-016`](test-cases-feed.md) |
| `BR-FEED-025` | `min_patched` WordPress | 3 | [`TC-ASMT-018`](test-cases.md), [`TC-ASMT-019`](test-cases.md), [`TC-PTCH-014`](test-cases-ptch-cli-rpt.md) |
| `BR-FEED-026` | Chuỗi quyết định backport | 4 | [`TC-FEED-023`](test-cases-feed.md), [`TC-FEED-024`](test-cases-feed.md), [`TC-SCN-104`](test-cases.md), [`TC-SCN-105`](test-cases.md) |
| `BR-FEED-027` | Phiên bản sửa khi các nguồn mâu thuẫn | 1 | [`TC-FEED-027`](test-cases-feed.md) |
| `BR-FEED-028` | Điểm CVSS đại diện | 1 | [`TC-FEED-026`](test-cases-feed.md) |
| `BR-FEED-029` | Nhánh không được đánh giá | 1 | [`TC-ASMT-002`](test-cases.md) |
| `BR-FEED-030` | Định nghĩa vá tối thiểu | 2 | [`TC-FEED-026`](test-cases-feed.md), [`TC-ASMT-101`](test-cases.md) |
| `BR-FEED-031` | Thu hồi advisory | 1 | [`TC-FEED-028`](test-cases-feed.md) |
| `BR-FEED-040` | Công thức điểm rủi ro | 1 | [`TC-ASMT-001`](test-cases.md) |
| `BR-FEED-041` | Điểm sàn theo mức ưu tiên kịch bản | 3 | [`TC-ASMT-002`](test-cases.md), [`TC-ASMT-017`](test-cases.md), [`TC-SCN-101`](test-cases.md) |
| `BR-FEED-042` | Phân mức | 3 | [`TC-ASMT-001`](test-cases.md), [`TC-ASMT-010`](test-cases.md), [`TC-ASMT-011`](test-cases.md) |
| `BR-FEED-043` | Điểm thay thế khi chỉ có mức độ chữ | 1 | [`TC-ASMT-016`](test-cases.md) |
| `BR-FEED-044` | Điểm cho phiên bản ứng viên | 3 | [`TC-ASMT-005`](test-cases.md), [`TC-ASMT-008`](test-cases.md), [`TC-SCN-106`](test-cases.md) |
| `BR-FEED-050` | Vị trí thư mục | 1 | [`TC-FEED-105`](test-cases-feed.md) |
| `BR-FEED-051` | Thay bundle nguyên tử | 2 | [`TC-FEED-032`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md) |
| `BR-FEED-052` | Lưu giữ | 1 | [`TC-FEED-034`](test-cases-feed.md) |
| `BR-FEED-053` | Khởi tạo lần đầu | 2 | [`TC-FEED-035`](test-cases-feed.md), [`TC-FEED-036`](test-cases-feed.md) |
| `BR-FEED-054` | Snapshot mới hơn dữ liệu hiện có | 1 | [`TC-FEED-037`](test-cases-feed.md) |
| `BR-FEED-055` | Nhập snapshot | 6 | [`TC-FEED-039`](test-cases-feed.md), [`TC-FEED-040`](test-cases-feed.md), [`TC-CON-039`](test-cases-con.md), [`TC-CON-040`](test-cases-con.md), [`TC-FLT-013`](test-cases-job-flt.md), [`TC-FLT-014`](test-cases-job-flt.md) |
| `BR-FEED-056` | Không xuất dữ liệu riêng | 2 | [`TC-FEED-038`](test-cases-feed.md), [`TC-FLT-015`](test-cases-job-flt.md) |
| `BR-FEED-057` | Một lịch đồng bộ | 2 | [`TC-FEED-045`](test-cases-feed.md), [`TC-FEED-047`](test-cases-feed.md) |
| `BR-FEED-058` | Cổng phát hành snapshot | 3 | [`TC-FEED-042`](test-cases-feed.md), [`TC-FEED-043`](test-cases-feed.md), [`TC-FEED-044`](test-cases-feed.md) |
| `BR-FEED-059` | Tương thích ngược schema JSON | 3 | [`TC-FEED-048`](test-cases-feed.md), [`TC-CLI-001`](test-cases-ptch-cli-rpt.md), [`TC-CON-038`](test-cases-con.md) |
| `BR-ENV-001` | Một site — một playbook gán | 3 | [`TC-SCAN-003`](test-cases.md), [`TC-SCAN-013`](test-cases.md), [`TC-SCAN-014`](test-cases.md) |
| `BR-ENV-002` | Site panel không sửa ngoài panel | 2 | [`TC-SCAN-001`](test-cases.md), [`TC-UPG-016`](test-cases-upg.md) |
| `BR-ENV-003` | Chuyển tuần tự, site đầu là canary | 7 | [`TC-PLAN-008`](test-cases-plan-cmpt.md), [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-020`](test-cases-upg.md), [`TC-UPG-021`](test-cases-upg.md), [`TC-CON-044`](test-cases-con.md), [`TC-UPG-108`](test-cases-upg.md), [`TC-UPG-110`](test-cases-upg.md) |
| `BR-ENV-004` | Kho gói bên thứ ba | 3 | [`TC-ASMT-005`](test-cases.md), [`TC-UPG-001`](test-cases-upg.md), [`TC-UPG-006`](test-cases-upg.md) |
| `BR-ENV-005` | Kiểm tra cú pháp trước reload | 3 | [`TC-UPG-008`](test-cases-upg.md), [`TC-UPG-012`](test-cases-upg.md), [`TC-UPG-038`](test-cases-upg.md) |
| `BR-ENV-006` | Phạm vi reload nhỏ nhất | 3 | [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-036`](test-cases-upg.md), [`TC-UPG-112`](test-cases-upg.md) |
| `BR-ENV-007` | Pool riêng cho site chuyển | 2 | [`TC-UPG-007`](test-cases-upg.md), [`TC-UPG-009`](test-cases-upg.md) |
| `BR-ENV-008` | Giữ runtime cũ để rollback | 2 | [`TC-UPG-036`](test-cases-upg.md), [`TC-UPG-046`](test-cases-upg.md) |
| `BR-ENV-009` | Trong container | 3 | [`TC-SCN-016`](test-cases.md), [`TC-PTCH-018`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-106`](test-cases-ptch-cli-rpt.md) |
| `BR-ENV-010` | Lệnh chưa kiểm chứng | 4 | [`TC-SCN-010`](test-cases.md), [`TC-PLAN-019`](test-cases-plan-cmpt.md), [`TC-UPG-016`](test-cases-upg.md), [`TC-CON-028`](test-cases-con.md) |
| `BR-ENV-011` | Không tự build/deploy image | 3 | [`TC-PTCH-017`](test-cases-ptch-cli-rpt.md), [`TC-UPG-043`](test-cases-upg.md), [`TC-UPG-044`](test-cases-upg.md) |
| `BR-ENV-012` | Không dùng kết quả panel không đọc lại được | 2 | [`TC-UPG-014`](test-cases-upg.md), [`TC-UPG-015`](test-cases-upg.md) |
| `BR-ENV-013` | Chặn lệnh ghi khi đang có lượt chuyển | 1 | [`TC-UPG-110`](test-cases-upg.md) (KQ1–KQ3 50/50 lần `fix`, `rollback <ID>`, `migrate install`, `rollback-site`, `switch-site` bị từ chối với `ERR-ENV-409-01`, 0 thay đổi, khoá chung đã nhả; KQ5 job mục checklist `AUTO` `FAILED`) |
| `BR-HC-001` | Trang chủ luôn có trong tập URL | 3 | [`TC-UPG-024`](test-cases-upg.md), [`TC-UPG-026`](test-cases-upg.md), [`TC-CON-042`](test-cases-con.md) |
| `BR-HC-002` | Chỉ GET, chỉ host của site | 5 | [`TC-UPG-024`](test-cases-upg.md), [`TC-UPG-026`](test-cases-upg.md), [`TC-CON-043`](test-cases-con.md), [`TC-UPG-106`](test-cases-upg.md), [`TC-UPG-109`](test-cases-upg.md) |
| `BR-HC-003` | Chạy thử trước khi nhận traffic | 3 | [`TC-UPG-027`](test-cases-upg.md), [`TC-UPG-028`](test-cases-upg.md), [`TC-UPG-029`](test-cases-upg.md) |
| `BR-HC-004` | Baseline tươi | 3 | [`TC-UPG-013`](test-cases-upg.md), [`TC-UPG-024`](test-cases-upg.md), [`TC-UPG-109`](test-cases-upg.md) |
| `BR-HC-005` | Đếm log theo byte offset | 1 | [`TC-UPG-103`](test-cases-upg.md) |
| `BR-HC-006` | Loại vòng khởi động khỏi P95 | 2 | [`TC-UPG-032`](test-cases-upg.md), [`TC-UPG-101`](test-cases-upg.md) |
| `BR-HC-007` | Ngưỡng nội dung thích nghi | 2 | [`TC-UPG-032`](test-cases-upg.md), [`TC-UPG-101`](test-cases-upg.md) |
| `BR-HC-008` | Chuỗi cấm đã có ở baseline | 1 | [`TC-UPG-105`](test-cases-upg.md) |
| `BR-HC-009` | Chống cache | 1 | [`TC-UPG-106`](test-cases-upg.md) |
| `BR-HC-010` | Tự rollback | 8 | [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-034`](test-cases-upg.md), [`TC-UPG-035`](test-cases-upg.md), [`TC-UPG-041`](test-cases-upg.md), [`TC-UPG-103`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md), [`TC-UPG-105`](test-cases-upg.md), [`TC-UPG-113`](test-cases-upg.md) |
| `BR-HC-011` | Lưu bằng chứng | 2 | [`TC-UPG-030`](test-cases-upg.md), [`TC-UPG-103`](test-cases-upg.md) |
| `BR-HC-012` | Tải tối đa | 1 | [`TC-UPG-030`](test-cases-upg.md) |

## 3. ERR → test case (129 mã của error-matrix v1.1.0: 129/129 mã có ≥ 1 test case ghi đúng mã)
Nguồn danh sách mã: [error-matrix.md](../srs/error-matrix.md) v1.1.0, gồm 120 mã của bản 1.0.0; 3 mã đề xuất ở DOC-SRS-QP-FLOW-001 §6.3 đã định nghĩa chuẩn ở bản 1.0.1 (`ERR-JOB-429-02`, `ERR-UPG-409-03`, `ERR-FLT-422-03`); 2 mã tách mức độ ở bản 1.0.1 (`ERR-FEED-503-03` từ `ERR-FEED-503-01`, `ERR-HC-412-04` từ `ERR-HC-412-02`); 4 mã đưa vào ma trận ở bản 1.1.0 (`ERR-CLI-412-01` §3.5; `ERR-PTCH-409-01`, `ERR-PTCH-500-01` §3.10; `ERR-UPG-409-04` §3.11).

Ghi chú độ phủ:
- 2 mã chưa có test case ở bản 1.0.1 của tài liệu này nay đã có: `ERR-FEED-503-03` (`TC-FEED-002`, `TC-FEED-024` của [test-cases-feed.md](test-cases-feed.md) v1.0.1 đổi mã theo vai trò nguồn), `ERR-HC-412-04` (`TC-UPG-109` của [test-cases-upg.md](test-cases-upg.md) v1.0.2).
- `ERR-PTCH-409-01`, `ERR-PTCH-500-01` (chờ PO duyệt `CR-FR-05`) và `ERR-UPG-409-04` (chờ PO duyệt `CR-FR-01`) là mã **đề xuất** theo error-matrix v1.1.0 §2.1; test case `TC-PTCH-103`, `TC-PTCH-104`, `TC-UPG-111` giữ nguyên khi PO duyệt, cần sửa KQ nếu PO đổi mã hoặc hành vi.

| ERR | HTTP | Điều kiện phát sinh | Số TC | Test case |
| :--- | :---: | :--- | :---: | :--- |
| `ERR-AUTH-401-01` | 401 | Thiếu cookie phiên/Bearer, phiên không tồn tại, hoặc token đăng nhập sai | 6 | [`TC-CON-006`](test-cases-con.md), [`TC-CON-008`](test-cases-con.md), [`TC-CON-009`](test-cases-con.md), [`TC-CON-010`](test-cases-con.md), [`TC-FLT-005`](test-cases-job-flt.md), [`TC-CON-102`](test-cases-con.md) |
| `ERR-AUTH-401-02` | 401 | Phiên quá 30 phút không hoạt động hoặc quá 12 giờ từ khi đăng nhập | 1 | [`TC-CON-010`](test-cases-con.md) |
| `ERR-AUTH-403-01` | 403 | Request ghi xác thực bằng cookie thiếu header `X-QP-CSRF` hoặc giá trị sai | 1 | [`TC-CON-015`](test-cases-con.md) |
| `ERR-AUTH-403-02` | 403 | Request ghi xác thực bằng cookie có `Origin` thiếu hoặc không thuộc danh sách cho phép | 1 | [`TC-CON-015`](test-cases-con.md) |
| `ERR-AUTH-409-01` | 409 | Đã có 5 phiên đăng nhập hiệu lực | 1 | [`TC-CON-007`](test-cases-con.md) |
| `ERR-AUTH-429-01` | 429 | 5 lần đăng nhập sai trong 60 s | 1 | [`TC-CON-006`](test-cases-con.md) |
| `ERR-CON-400-01` | 400 | Thiếu header `Host` hoặc request HTTP sai cú pháp | 1 | [`TC-CON-012`](test-cases-con.md) |
| `ERR-CON-404-01` | 404 | Đường dẫn API/tài nguyên tĩnh không tồn tại, hoặc tài nguyên (site, lượt chạy) không có | 2 | [`TC-CON-053`](test-cases-con.md), [`TC-CON-101`](test-cases-con.md) |
| `ERR-CON-405-01` | 405 | Phương thức HTTP không hỗ trợ cho đường dẫn | 2 | [`TC-CON-047`](test-cases-con.md), [`TC-CON-059`](test-cases-con.md) |
| `ERR-CON-409-01` | 409 | Cổng đang bị phiên `serve` cũ của tool chiếm | 1 | [`TC-CON-002`](test-cases-con.md) |
| `ERR-CON-409-02` | 409 | Cổng đang bị tiến trình khác chiếm | 1 | [`TC-CON-002`](test-cases-con.md) |
| `ERR-CON-409-03` | 409 | Yêu cầu dừng `serve` khi có job ghi đang `RUNNING` | 1 | [`TC-CON-004`](test-cases-con.md) |
| `ERR-CON-412-01` | 412 | `serve` chạy không có TTY và không có `--token-file` | 1 | [`TC-CON-003`](test-cases-con.md) |
| `ERR-CON-413-01` | 413 | Body > 64 KiB (upload snapshot > 20 MiB) hoặc header > 8 KiB | 2 | [`TC-CON-041`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md) |
| `ERR-CON-415-01` | 415 | Request ghi không có `Content-Type: application/json` | 1 | [`TC-CON-015`](test-cases-con.md) |
| `ERR-CON-421-01` | 421 | Header `Host` không thuộc danh sách cho phép (DNS rebinding, hoặc tunnel dùng cổng cục bộ khác) | 2 | [`TC-CON-012`](test-cases-con.md), [`TC-CON-013`](test-cases-con.md) |
| `ERR-CON-422-01` | 422 | Hành động không có trong danh sách trắng, hoặc tham số sai regex/enum/bắt đầu bằng `-` | 7 | [`TC-SCAN-011`](test-cases.md), [`TC-CON-034`](test-cases-con.md), [`TC-CON-056`](test-cases-con.md), [`TC-CON-057`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md), [`TC-CON-101`](test-cases-con.md), [`TC-UPG-111`](test-cases-upg.md) |
| `ERR-CON-424-01` | 424 | Không có `python3` hoặc Python < 3.6 khi chạy `serve` | 1 | [`TC-CON-003`](test-cases-con.md) |
| `ERR-CON-500-01` | 500 | Lỗi không lường trước trong `qp-console.py` | 1 | [`TC-CON-059`](test-cases-con.md) |
| `ERR-CON-503-01` | 503 | Console đang dừng, không nhận yêu cầu mới | 1 | [`TC-CON-059`](test-cases-con.md) |
| `ERR-JOB-404-01` | 404 | `job_id` không tồn tại | 3 | [`TC-CON-030`](test-cases-con.md), [`TC-JOB-008`](test-cases-job-flt.md), [`TC-JOB-017`](test-cases-job-flt.md) |
| `ERR-JOB-409-01` | 409 | Đã có job cùng hành động và cùng đối tượng đang `QUEUED`/`RUNNING` | 1 | [`TC-JOB-002`](test-cases-job-flt.md) |
| `ERR-JOB-409-02` | 409 | Khoá `STATE_DIR/.lock` bị lượt CLI ngoài console giữ quá 30 phút | 1 | [`TC-JOB-005`](test-cases-job-flt.md) |
| `ERR-JOB-410-01` | 410 | Log job đã bị dọn theo chính sách lưu giữ | 3 | [`TC-CON-031`](test-cases-con.md), [`TC-JOB-014`](test-cases-job-flt.md), [`TC-JOB-017`](test-cases-job-flt.md) |
| `ERR-JOB-423-01` | 423 | Yêu cầu huỷ job ghi đang ở vùng tới hạn | 2 | [`TC-CON-030`](test-cases-con.md), [`TC-JOB-008`](test-cases-job-flt.md) |
| `ERR-JOB-428-01` | 428 | Tạo job ghi không kèm dry-run hợp lệ (`BR-CON-005`) | 7 | [`TC-PLAN-018`](test-cases-plan-cmpt.md), [`TC-PLAN-019`](test-cases-plan-cmpt.md), [`TC-UPG-019`](test-cases-upg.md), [`TC-UPG-047`](test-cases-upg.md), [`TC-CON-049`](test-cases-con.md), [`TC-CON-050`](test-cases-con.md), [`TC-CON-051`](test-cases-con.md) |
| `ERR-JOB-429-01` | 429 | Hàng đợi đã có 20 job `QUEUED` | 1 | [`TC-JOB-002`](test-cases-job-flt.md) |
| `ERR-JOB-429-02` | 429 | Mở luồng SSE `GET /api/v1/jobs/{job_id}/events` khi phiên đã có 3 luồng hoặc toàn console đã có 10 luồng (`BR-JOB-007`) | 3 | [`TC-CON-031`](test-cases-con.md) (KQ2, luồng thứ 4 của phiên), [`TC-CON-103`](test-cases-con.md) (KQ2, luồng thứ 11 của console), [`TC-JOB-025`](test-cases-job-flt.md) (KQ1, cả 2 giới hạn 3 luồng/phiên và 10 luồng/console; KQ2, 10 luồng cũ không bị ngắt) |
| `ERR-JOB-500-01` | 500 | CLI của job kết thúc với mã thoát 2 | 2 | [`TC-JOB-002`](test-cases-job-flt.md), [`TC-UPG-022`](test-cases-upg.md) |
| `ERR-JOB-500-02` | 500 | Job bị gián đoạn (console hoặc máy khởi động lại, tiến trình mất) | 1 | [`TC-JOB-011`](test-cases-job-flt.md) |
| `ERR-JOB-504-01` | 504 | Job vượt timeout theo loại hành động (`BR-JOB-008`) | 1 | [`TC-JOB-003`](test-cases-job-flt.md) |
| `ERR-AUD-500-01` | 500 | Không ghi được bản ghi audit "intent" (đĩa đầy, sai quyền) | 1 | [`TC-JOB-020`](test-cases-job-flt.md) |
| `ERR-AUD-409-01` | 409 | Chuỗi hash audit không khớp khi kiểm tra | 5 | [`TC-RPT-005`](test-cases-ptch-cli-rpt.md), [`TC-CON-046`](test-cases-con.md), [`TC-JOB-023`](test-cases-job-flt.md), [`TC-FLT-011`](test-cases-job-flt.md), [`TC-JOB-102`](test-cases-job-flt.md) |
| `ERR-CLI-400-01` | 400 | Tham số dòng lệnh không hợp lệ hoặc thiếu (v0.1 "Unknown argument") | 9 | [`TC-SCAN-008`](test-cases.md), [`TC-FEED-046`](test-cases-feed.md), [`TC-CLI-002`](test-cases-ptch-cli-rpt.md), [`TC-CLI-005`](test-cases-ptch-cli-rpt.md), [`TC-CLI-008`](test-cases-ptch-cli-rpt.md), [`TC-CLI-021`](test-cases-ptch-cli-rpt.md), [`TC-CON-013`](test-cases-con.md), [`TC-CLI-101`](test-cases-ptch-cli-rpt.md), [`TC-UPG-111`](test-cases-upg.md) |
| `ERR-CLI-403-01` | 403 | Lệnh mới cần root nhưng chạy không root | 2 | [`TC-CLI-020`](test-cases-ptch-cli-rpt.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) |
| `ERR-CLI-412-01` | 412 | `STATE_DIR` chính, hoặc `backups/<run_id>/` và `manifest` khi `rollback [ID]`, không đạt kiểm tra `lstat` (symlink/không phải thư mục, chủ ≠ `EUID`, group/other ghi được) hoặc không tạo được thư mục (DOC-SRS-QP-001 §2.1) | 4 | [`TC-CLI-102`](test-cases-ptch-cli-rpt.md) (`STATE_DIR` chính), [`TC-CLI-103`](test-cases-ptch-cli-rpt.md) (`backups/<run_id>`, `manifest` khi `rollback`), [`TC-CLI-104`](test-cases-ptch-cli-rpt.md) (dự phòng không root khi `HOME` rỗng), [`TC-FEED-105`](test-cases-feed.md) (KQ4, root chạy `feeds status` khi không tạo được `/var/lib/php-quickpatch`) |
| `ERR-CLI-423-01` | 423 | Khoá `STATE_DIR/.lock` đang bị lượt khác giữ (v0.1) | 4 | [`TC-PTCH-021`](test-cases-ptch-cli-rpt.md), [`TC-CLI-008`](test-cases-ptch-cli-rpt.md), [`TC-CLI-015`](test-cases-ptch-cli-rpt.md), [`TC-JOB-006`](test-cases-job-flt.md) |
| `ERR-CLI-424-01` | 424 | Lệnh cần Python (`assess`, `plan`, `report`, `serve`) nhưng thiếu Python ≥ 3.6 | 2 | [`TC-CLI-014`](test-cases-ptch-cli-rpt.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) |
| `ERR-CLI-424-02` | 424 | Bash < 4.3 hoặc thiếu `flock`/`curl` | 1 | [`TC-CLI-029`](test-cases-ptch-cli-rpt.md) |
| `ERR-CLI-428-01` | 428 | Lệnh ghi mới chạy không có TTY và thiếu `--yes` | 2 | [`TC-CLI-018`](test-cases-ptch-cli-rpt.md), [`TC-CLI-026`](test-cases-ptch-cli-rpt.md) |
| `ERR-SCAN-409-01` | 409 | Gán site khác lượt chuyển gần nhất (bị đổi ngoài tool) | 1 | [`TC-SCAN-014`](test-cases.md) |
| `ERR-ASMT-404-01` | 404 | `runtime_id` không có trong kết quả scan gần nhất | 2 | [`TC-ASMT-003`](test-cases.md), [`TC-CON-021`](test-cases-con.md) |
| `ERR-PLAN-404-01` | 404 | `plan_id` hoặc `chk_id` không tồn tại | 1 | [`TC-CLI-017`](test-cases-ptch-cli-rpt.md) |
| `ERR-PLAN-409-01` | 409 | Runtime đã có kế hoạch `in_progress` | 2 | [`TC-PLAN-006`](test-cases-plan-cmpt.md), [`TC-CON-024`](test-cases-con.md) |
| `ERR-PLAN-409-02` | 409 | Hành động không hợp lệ với trạng thái hiện tại của kế hoạch/mục | 2 | [`TC-PLAN-015`](test-cases-plan-cmpt.md), [`TC-PLAN-023`](test-cases-plan-cmpt.md) |
| `ERR-PLAN-410-01` | 410 | Kế hoạch `stale` (`BR-PLAN-006`) | 1 | [`TC-PLAN-022`](test-cases-plan-cmpt.md) |
| `ERR-PLAN-412-01` | 412 | Duyệt kế hoạch khi chưa đạt `BR-PLAN-003` | 2 | [`TC-PLAN-021`](test-cases-plan-cmpt.md), [`TC-PLAN-025`](test-cases-plan-cmpt.md) |
| `ERR-PLAN-422-01` | 422 | Lý do miễn trừ/đích khác đề xuất < 20 ký tự, hoặc bằng chứng mục `MANUAL` < 10 ký tự | 7 | [`TC-PLAN-003`](test-cases-plan-cmpt.md), [`TC-PLAN-016`](test-cases-plan-cmpt.md), [`TC-CMPT-029`](test-cases-plan-cmpt.md), [`TC-CON-025`](test-cases-con.md), [`TC-CON-027`](test-cases-con.md), [`TC-SCN-108`](test-cases.md), [`TC-CLI-101`](test-cases-ptch-cli-rpt.md) |
| `ERR-CMPT-413-01` | 413 | File nguồn > 2 MiB bị bỏ qua khi quét | 1 | [`TC-CMPT-006`](test-cases-plan-cmpt.md) |
| `ERR-CMPT-422-01` | 422 | Không có PHP ≥ 7.2 để chạy PHP_CodeSniffer | 1 | [`TC-CMPT-008`](test-cases-plan-cmpt.md) |
| `ERR-CMPT-424-01` | 424 | Thiếu công cụ quét và không tải được (offline, lỗi mạng, hash lệch) | 3 | [`TC-CMPT-002`](test-cases-plan-cmpt.md), [`TC-CMPT-014`](test-cases-plan-cmpt.md), [`TC-CMPT-032`](test-cases-plan-cmpt.md) |
| `ERR-CMPT-504-01` | 504 | Quét 1 site vượt 1.800 s | 1 | [`TC-CMPT-005`](test-cases-plan-cmpt.md) |
| `ERR-PTCH-403-01` | 403 | Vá runtime hệ thống khi không root (v0.1 "needs root (or the hosting panel) to upgrade") | 1 | [`TC-SCN-015`](test-cases.md) |
| `ERR-PTCH-404-01` | 404 | Không có lượt backup cho `rollback [ID]` (v0.1, thoát 2) | 2 | [`TC-PTCH-027`](test-cases-ptch-cli-rpt.md), [`TC-CON-036`](test-cases-con.md) |
| `ERR-PTCH-409-01` | 409 | Thư mục `backups/<run_id>` vẫn tồn tại sau 10 lần thử tạo bằng `mkdir` không `-p` (đồng hồ hệ thống bị lùi); dừng trước thay đổi đầu tiên (mã đề xuất, `CR-FR-05`) | 1 | [`TC-PTCH-103`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-412-01` | 412 | Không có thư mục `conf.d` để ghi mitigation | 2 | [`TC-PTCH-006`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-018`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-424-01` | 424 | Nâng gói không đưa runtime lên bản vá (kho chưa có bản vá) | 2 | [`TC-PTCH-003`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-010`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-424-02` | 424 | `composer update`/`npm audit fix` thất bại, đã khôi phục file | 1 | [`TC-PTCH-012`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-424-03` | 424 | Không có wp-cli và không tải/kiểm được `wp-cli.phar` | 1 | [`TC-PTCH-015`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-424-04` | 424 | `wp core verify-checksums` báo lệch | 1 | [`TC-PTCH-016`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-500-01` | 500 | Dịch vụ vừa restart sau vá không đạt kiểm tra trạng thái trong 15 s, thăm dò mỗi 1 s; 1 mã cho mỗi dịch vụ lỗi, không tự rollback (mã đề xuất, `CR-FR-05`) | 1 | [`TC-PTCH-104`](test-cases-ptch-cli-rpt.md) |
| `ERR-PTCH-502-01` | 502 | Checksum file tải về không khớp | 2 | [`TC-CMPT-002`](test-cases-plan-cmpt.md), [`TC-PTCH-009`](test-cases-ptch-cli-rpt.md) |
| `ERR-UPG-409-01` | 409 | Site chưa có kết luận tương thích `PASS` | 2 | [`TC-PLAN-009`](test-cases-plan-cmpt.md), [`TC-UPG-023`](test-cases-upg.md) |
| `ERR-UPG-409-02` | 409 | Chuyển site không thuộc kế hoạch `approved`/`in_progress` | 3 | [`TC-PLAN-018`](test-cases-plan-cmpt.md), [`TC-CLI-020`](test-cases-ptch-cli-rpt.md), [`TC-UPG-021`](test-cases-upg.md) |
| `ERR-UPG-409-03` | 409 | Yêu cầu chuyển site không phải site kế tiếp của `site_order`, hoặc lượt chuyển trước của kế hoạch ở `ROLLED_BACK`/`HC_FAILED_KEPT` chưa được người vận hành xác nhận đã xử lý (`BR-ENV-003`, `BR-UPG-003`) | 5 | [`TC-UPG-022`](test-cases-upg.md) (lượt trước `ROLLED_BACK`), [`TC-UPG-108`](test-cases-upg.md) (không phải site kế tiếp), [`TC-UPG-111`](test-cases-upg.md) (KQ1, lượt trước `ROLLED_BACK` và `HC_FAILED_KEPT` chưa xác nhận), [`TC-UPG-112`](test-cases-upg.md) (KQ5, sau tự rollback do reload C9 lỗi), [`TC-UPG-113`](test-cases-upg.md) (KQ5, sau tự rollback do `HC-C0`) |
| `ERR-UPG-409-04` | 409 | `migrate ack RUN_ID` (console: `POST /api/v1/switches/{run_id}/acknowledgements`) cho lượt chuyển không ở `ROLLED_BACK`/`HC_FAILED_KEPT`/`ROLLBACK_FAILED`, hoặc lượt đã có `acknowledged_at` (mã đề xuất, `CR-FR-01`) | 1 | [`TC-UPG-111`](test-cases-upg.md) (KQ6, xác nhận lần 2 cho lượt đã có `acknowledged_at`). Nhánh lượt ở trạng thái khác 3 trạng thái trên (vd `PASSED`) chưa có dòng dữ liệu |
| `ERR-UPG-412-01` | 412 | Gỡ runtime cũ khi còn site/tiến trình dùng trong 14 ngày | 1 | [`TC-UPG-046`](test-cases-upg.md) |
| `ERR-UPG-423-01` | 423 | Lệnh chuyển site bị khoá sau lượt `ROLLBACK_FAILED` | 3 | [`TC-UPG-023`](test-cases-upg.md), [`TC-UPG-035`](test-cases-upg.md), [`TC-UPG-111`](test-cases-upg.md) |
| `ERR-RPT-409-01` | 409 | File `--out` đã tồn tại | 2 | [`TC-CLI-023`](test-cases-ptch-cli-rpt.md), [`TC-RPT-002`](test-cases-ptch-cli-rpt.md) |
| `ERR-RPT-422-01` | 422 | Định dạng không hỗ trợ, hoặc khoảng thời gian sai (`from` > `to`, dài hơn 366 ngày) | 3 | [`TC-CLI-023`](test-cases-ptch-cli-rpt.md), [`TC-CLI-024`](test-cases-ptch-cli-rpt.md), [`TC-RPT-006`](test-cases-ptch-cli-rpt.md) |
| `ERR-FLT-401-01` | 401 | Xác thực SSH thất bại (khoá bị từ chối) | 1 | [`TC-FLT-002`](test-cases-job-flt.md) |
| `ERR-FLT-403-01` | 403 | Fingerprint khoá máy chủ khác giá trị đã ghim | 1 | [`TC-FLT-002`](test-cases-job-flt.md) |
| `ERR-FLT-403-02` | 403 | Vai trò không đủ quyền cho thao tác | 3 | [`TC-FLT-005`](test-cases-job-flt.md), [`TC-FLT-006`](test-cases-job-flt.md), [`TC-FLT-008`](test-cases-job-flt.md) |
| `ERR-FLT-404-01` | 404 | `server_id` không tồn tại | 2 | [`TC-FLT-003`](test-cases-job-flt.md), [`TC-FLT-011`](test-cases-job-flt.md) |
| `ERR-FLT-409-01` | 409 | Đợt chạy bị dừng do canary lỗi hoặc tỉ lệ lỗi > 20% | 1 | [`TC-FLT-008`](test-cases-job-flt.md) |
| `ERR-FLT-422-01` | 422 | Dữ liệu khai báo server sai định dạng | 1 | [`TC-FLT-003`](test-cases-job-flt.md) |
| `ERR-FLT-422-02` | 422 | JSON trả về từ server sai schema hoặc khác major hỗ trợ | 1 | [`TC-FLT-009`](test-cases-job-flt.md) |
| `ERR-FLT-422-03` | 422 | SHA-256 gói CLI trên server (`sha256sum -c SHA256SUMS`) không khớp hash của máy trung tâm; lệnh từ xa không chạy (`BR-FLT-003`) | 1 | [`TC-FLT-009`](test-cases-job-flt.md) (KQ2, `web04`: bước S5 không chạy) |
| `ERR-FLT-424-01` | 424 | Server thiếu Bash ≥ 4.3, `flock` hoặc `curl` | 1 | [`TC-FLT-002`](test-cases-job-flt.md) |
| `ERR-FLT-504-01` | 504 | SSH không kết nối được trong 10 s hoặc lệnh từ xa vượt timeout | 2 | [`TC-FLT-003`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `ERR-SCN-422-01` | 422 | Chuỗi phiên bản không khớp dải đã biết: major PHP = 6, major vượt nhánh mới nhất trong dữ liệu, hậu tố lạ, hoặc binary không trả phiên bản trong 10 s | 3 | [`TC-SCAN-005`](test-cases.md), [`TC-SCAN-009`](test-cases.md), [`TC-SCN-003`](test-cases.md) |
| `ERR-SCN-409-01` | 409 | Không có nhánh đích thoả BR-SCN-005/006 với framework, loader hoặc `engines` đã phát hiện | 2 | [`TC-ASMT-006`](test-cases.md), [`TC-CMPT-026`](test-cases-plan-cmpt.md) |
| `ERR-SCN-409-02` | 409 | Người vận hành chọn đích là nhánh `EOL`, `PRE_RELEASE` hoặc Node.js `CURRENT` chưa tới ngày LTS cho site production | 3 | [`TC-PLAN-002`](test-cases-plan-cmpt.md), [`TC-PLAN-004`](test-cases-plan-cmpt.md), [`TC-SCN-102`](test-cases.md) |
| `ERR-SCN-412-01` | 412 | Điều kiện BR-SCN-016 không đạt | 1 | [`TC-UPG-002`](test-cases-upg.md) |
| `ERR-SCN-424-01` | 424 | Chạy mục khi mục phụ thuộc chưa `DONE`/`WAIVED` (BR-SCN-018) | 5 | [`TC-SCN-012`](test-cases.md), [`TC-PLAN-016`](test-cases-plan-cmpt.md), [`TC-CMPT-020`](test-cases-plan-cmpt.md), [`TC-UPG-013`](test-cases-upg.md), [`TC-CON-027`](test-cases-con.md) |
| `ERR-SCN-500-01` | 500 | Health check vi phạm BR-SCN-009; tool đã hoàn tác theo BR-SCN-010 | 5 | [`TC-UPG-022`](test-cases-upg.md), [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-103`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md), [`TC-UPG-113`](test-cases-upg.md) |
| `ERR-SCN-503-01` | 503 | Không lấy được dữ liệu vòng đời/CVE online và snapshot cũ > 90 ngày | 4 | [`TC-SCN-006`](test-cases.md), [`TC-ASMT-004`](test-cases.md), [`TC-ASMT-009`](test-cases.md), [`TC-FEED-102`](test-cases-feed.md) |
| `ERR-SCN-409-03` | 409 | Site dùng loader mã hoá và không còn nhánh đích có loader chính thức (BR-SCN-043) | 2 | [`TC-PLAN-012`](test-cases-plan-cmpt.md), [`TC-CMPT-023`](test-cases-plan-cmpt.md) |
| `ERR-SCN-412-02` | 412 | Site chạy `mod_php` và chưa chuyển được sang PHP-FPM (BR-SCN-047) | 1 | [`TC-UPG-018`](test-cases-upg.md) |
| `ERR-SCN-412-03` | 412 | Binary chính thức của `$NEW` không chạy được trên OS (lỗi `GLIBC_`, kiến trúc không hỗ trợ) (BR-SCN-028) | 1 | [`TC-UPG-102`](test-cases-upg.md) |
| `ERR-SCN-424-02` | 424 | Native addon không nạp được sau khi build lại bằng `$NEW_BIN` (BR-SCN-022) | 2 | [`TC-CMPT-017`](test-cases-plan-cmpt.md), [`TC-UPG-040`](test-cases-upg.md) |
| `ERR-FEED-503-01` | 503 | Nguồn có vai trò **Chính** (DOC-SRS-QP-FEED-001 §3.1) không truy cập được sau 3 lần thử (DNS, TLS, kết nối, HTTP 5xx) | 7 | [`TC-ASMT-018`](test-cases.md), [`TC-FEED-009`](test-cases-feed.md), [`TC-FEED-010`](test-cases-feed.md), [`TC-FEED-024`](test-cases-feed.md), [`TC-FEED-036`](test-cases-feed.md), [`TC-FEED-043`](test-cases-feed.md), [`TC-CMPT-014`](test-cases-plan-cmpt.md) |
| `ERR-FEED-503-02` | 503 | OSV không truy cập được và không có kết quả cache ≤ 7 ngày cho lockfile | 3 | [`TC-ASMT-015`](test-cases.md), [`TC-FEED-021`](test-cases-feed.md), [`TC-CON-033`](test-cases-con.md) |
| `ERR-FEED-503-03` | 503 | Nguồn có vai trò **Phụ**, **Dự phòng** hoặc **Tùy chọn** (`SRC-003`, `SRC-005`, `SRC-008`, `SRC-013`, `SRC-015`) không truy cập được sau 3 lần thử; kết quả tiếp tục theo chuỗi dự phòng `BR-FEED-006` | 2 | [`TC-FEED-002`](test-cases-feed.md) (KQ1, SRC-008 vai trò Phụ), [`TC-FEED-024`](test-cases-feed.md) (KQ1, SRC-015 vai trò Dự phòng) |
| `ERR-FEED-504-01` | 504 | Vượt ngân sách thời gian đồng bộ (900 s / 180 s) hoặc timeout 1 request | 2 | [`TC-FEED-004`](test-cases-feed.md), [`TC-FEED-103`](test-cases-feed.md) |
| `ERR-FEED-429-01` | 429 | Nguồn trả 429, NVD trả 403, GitHub `x-ratelimit-remaining = 0`, hoặc `Retry-After` > 300 s | 1 | [`TC-FEED-012`](test-cases-feed.md) |
| `ERR-FEED-401-01` | 401 | Nguồn trả 401/403 khi đã gửi key/token | 1 | [`TC-FEED-052`](test-cases-feed.md) |
| `ERR-FEED-502-01` | 502 | Phản hồi không phải JSON hợp lệ (vd trang lỗi HTML, JSON bị cắt) | 1 | [`TC-FEED-106`](test-cases-feed.md) |
| `ERR-FEED-502-02` | 502 | Sai schema tối thiểu hoặc vi phạm `BR-FEED-009` (số bản ghi giảm bất thường, phiên bản lùi) | 3 | [`TC-SCN-010`](test-cases.md), [`TC-FEED-006`](test-cases-feed.md), [`TC-FEED-018`](test-cases-feed.md) |
| `ERR-FEED-422-01` | 422 | 1 bản ghi không phân tích được (biểu thức semver, chuỗi CPE, ngày) | 2 | [`TC-FEED-015`](test-cases-feed.md), [`TC-FEED-107`](test-cases-feed.md) |
| `ERR-FEED-412-01` | 412 | Dữ liệu dùng cho kết quả ở mức `STALE` (> 7 ngày) | 6 | [`TC-ASMT-004`](test-cases.md), [`TC-ASMT-012`](test-cases.md), [`TC-FEED-030`](test-cases-feed.md), [`TC-CLI-011`](test-cases-ptch-cli-rpt.md), [`TC-CON-018`](test-cases-con.md), [`TC-FEED-102`](test-cases-feed.md) |
| `ERR-FEED-409-01` | 409 | Hai nguồn lệch nhau vượt ngưỡng của `BR-FEED-027` (vd `min_patched` khác nhau, ngày EOL lệch > 3 ngày) | 3 | [`TC-FEED-007`](test-cases-feed.md), [`TC-FEED-027`](test-cases-feed.md), [`TC-FEED-101`](test-cases-feed.md) |
| `ERR-FEED-423-01` | 423 | Một tiến trình `feeds update` khác đang giữ khóa > 30 s | 2 | [`TC-FEED-003`](test-cases-feed.md), [`TC-CON-040`](test-cases-con.md) |
| `ERR-FEED-424-01` | 424 | Không có `python3` ≥ 3.6 (`BR-FEED-012`) | 1 | [`TC-FEED-104`](test-cases-feed.md) |
| `ERR-FEED-507-01` | 507 | Dung lượng trống phân vùng chứa `feeds/` < 100 MB trước khi đồng bộ | 2 | [`TC-FEED-004`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md) |
| `ERR-FEED-422-02` | 422 | SHA256 snapshot không khớp (đóng gói hoặc nhập) | 8 | [`TC-SCN-009`](test-cases.md), [`TC-FEED-033`](test-cases-feed.md), [`TC-FEED-036`](test-cases-feed.md), [`TC-FEED-040`](test-cases-feed.md), [`TC-FEED-041`](test-cases-feed.md), [`TC-FEED-049`](test-cases-feed.md), [`TC-CON-040`](test-cases-con.md), [`TC-FLT-014`](test-cases-job-flt.md) |
| `ERR-FEED-409-02` | 409 | Nhập snapshot cũ hơn bundle hiện tại | 2 | [`TC-FEED-040`](test-cases-feed.md), [`TC-CON-040`](test-cases-con.md) |
| `ERR-ENV-409-01` | 409 | Đang có lượt chuyển ở `SWITCHED`/`HC_RUNNING` (`BR-ENV-003`) hoặc khoá `flock` đang bị giữ | 3 | [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-021`](test-cases-upg.md), [`TC-UPG-110`](test-cases-upg.md) |
| `ERR-ENV-410-01` | 410 | Runtime cũ đã bị gỡ, không rollback được (`BR-SCN-014`) | 2 | [`TC-UPG-037`](test-cases-upg.md), [`TC-CON-036`](test-cases-con.md) |
| `ERR-ENV-412-01` | 412 | `$NEW_BIN` không tồn tại hoặc không chạy được | 2 | [`TC-CMPT-011`](test-cases-plan-cmpt.md), [`TC-UPG-013`](test-cases-upg.md) |
| `ERR-ENV-422-01` | 422 | Không nhận diện được playbook cho PHP (`PB-000`) | 1 | [`TC-SCAN-002`](test-cases.md) |
| `ERR-ENV-422-02` | 422 | Không xác định được lớp gán của site (`BR-ENV-001`) | 1 | [`TC-SCAN-003`](test-cases.md) |
| `ERR-ENV-424-01` | 424 | Lệnh cài song song thất bại (gói không có trong kho, xung đột gói) | 1 | [`TC-UPG-005`](test-cases-upg.md) |
| `ERR-ENV-424-02` | 424 | `docker compose build/up` của dịch vụ đích thất bại | 1 | [`TC-UPG-043`](test-cases-upg.md) |
| `ERR-ENV-500-01` | 500 | Pool/handler đích không qua kiểm tra cú pháp hoặc dịch vụ FPM đích không `active` sau 15 s | 1 | [`TC-UPG-008`](test-cases-upg.md) |
| `ERR-ENV-500-02` | 500 | Kiểm tra cú pháp web server sau khi đổi lớp gán thất bại; đã khôi phục file | 1 | [`TC-UPG-012`](test-cases-upg.md) |
| `ERR-ENV-500-03` | 500 | Khi rollback, kiểm tra cú pháp sau khôi phục thất bại; chưa reload | 2 | [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md), [`TC-UPG-038`](test-cases-upg.md) |
| `ERR-ENV-502-01` | 502 | API/CLI panel trả lỗi hoặc giá trị đọc lại khác giá trị mong muốn (`BR-ENV-012`) | 1 | [`TC-UPG-015`](test-cases-upg.md) |
| `ERR-ENV-507-01` | 507 | Không đủ dung lượng để ghi backup (< 50 MB trống tại `STATE_DIR`) | 1 | [`TC-PTCH-024`](test-cases-ptch-cli-rpt.md) |
| `ERR-HC-412-01` | 412 | Không xác định được nguồn log lỗi của site (§5.1) | 1 | [`TC-UPG-025`](test-cases-upg.md) |
| `ERR-HC-412-02` | 412 | Baseline **trang chủ** không hợp lệ (§4): 5 mẫu trên `$OLD` có mã HTTP khác nhau, có 5xx hoặc khác `expect=`; lượt chuyển `ABORTED` | 1 | [`TC-UPG-025`](test-cases-upg.md) |
| `ERR-HC-412-03` | 412 | Không tìm được host hợp lệ cho trang chủ (§3.1 bước 1) | 1 | [`TC-UPG-026`](test-cases-upg.md) |
| `ERR-HC-412-04` | 412 | Baseline của **URL khai báo** trong `hc_url` không hợp lệ: URL bị loại khỏi tập thăm dò, lượt chuyển tiếp tục với URL còn lại | 1 | [`TC-UPG-109`](test-cases-upg.md) (KQ1 2 cảnh báo mức Low cho `/cart` mã `200,200,500,200,200` và `/api/ping` lệch `expect=204`; KQ2 không `ABORTED`) |
| `ERR-HC-422-01` | 422 | Tham số `hc.*` ngoài khoảng cho phép (§2) | 1 | [`TC-UPG-031`](test-cases-upg.md) |
| `ERR-HC-422-02` | 422 | URL khai báo sai cú pháp, khác host, hoặc quá 10 URL | 3 | [`TC-UPG-026`](test-cases-upg.md), [`TC-CON-043`](test-cases-con.md), [`TC-CON-044`](test-cases-con.md) |
| `ERR-HC-424-01` | 424 | FastCGI probe trên pool đích không đạt (§3.3) | 1 | [`TC-UPG-028`](test-cases-upg.md) |
| `ERR-HC-424-02` | 424 | Không có Python 3 để chạy FastCGI probe | 1 | [`TC-UPG-029`](test-cases-upg.md) |
| `ERR-HC-500-01` | 500 | Health check KHÔNG ĐẠT, người vận hành đã tắt tự rollback | 2 | [`TC-UPG-034`](test-cases-upg.md), [`TC-CON-018`](test-cases-con.md) |
| `ERR-HC-500-02` | 500 | Tự rollback thất bại hoặc site vẫn lỗi sau rollback | 1 | [`TC-UPG-035`](test-cases-upg.md) |

## 4. NFR → story → test case (60/60 NFR có dòng truy vết: 55 liên kết mức story, 5 liên kết trực tiếp)
Nguồn danh sách mã: 60 NFR của [nfr.md](../srs/nfr.md) (DOC-SRS-QP-NFR-001) v1.0.1. 55 NFR được story trong [backlog.md](../userstories/backlog.md) tham chiếu: cột "Test case" liệt kê test case sinh từ AC của các story đó. 5 NFR (`NFR-CMP-003`, `NFR-FEED-002`, `NFR-FEED-007`, `NFR-MNT-003`, `NFR-MNT-004`) chưa có story tham chiếu: cột "Test case" liệt kê test case đo trực tiếp chỉ tiêu, kèm KQ, mức phủ và phần còn thiếu (§4.1).

| NFR | Story tham chiếu | Số TC | Test case |
| :--- | :--- | :---: | :--- |
| `NFR-CAP-001` | `US-JOB-05` | 3 | [`TC-JOB-013`](test-cases-job-flt.md), [`TC-JOB-014`](test-cases-job-flt.md), [`TC-JOB-015`](test-cases-job-flt.md) |
| `NFR-CAP-002` | `US-CMPT-01` | 3 | [`TC-CMPT-001`](test-cases-plan-cmpt.md), [`TC-CMPT-002`](test-cases-plan-cmpt.md), [`TC-CMPT-003`](test-cases-plan-cmpt.md) |
| `NFR-CAP-003` | `US-PTCH-08` | 3 | [`TC-PTCH-023`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-024`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-025`](test-cases-ptch-cli-rpt.md) |
| `NFR-CMP-001` | `US-CLI-03` | 3 | [`TC-CLI-007`](test-cases-ptch-cli-rpt.md), [`TC-CLI-008`](test-cases-ptch-cli-rpt.md), [`TC-CLI-009`](test-cases-ptch-cli-rpt.md) |
| `NFR-CMP-002` | `US-CLI-10` | 3 | [`TC-CLI-028`](test-cases-ptch-cli-rpt.md), [`TC-CLI-029`](test-cases-ptch-cli-rpt.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) |
| `NFR-CMP-003` | — (chưa story nào tham chiếu; liên kết trực tiếp, xem §4.1) | 3 | [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) (dòng `Python 3.6, root`: `assess` chạy; dòng `Python 3.5`: `ERR-CLI-424-01`), [`TC-CON-003`](test-cases-con.md) (KQ2, `serve` trên Python 3.5 → `ERR-CON-424-01`), [`TC-CON-054`](test-cases-con.md) (0 vi phạm CSP trên 10 màn hình, chạy trên 4 trình duyệt × 2 bản ổn định gần nhất của [test-cases.md §2.2](test-cases.md)). **Một phần**: chưa có dòng dữ liệu cận trên Python 3.14 ([nfr.md](../srs/nfr.md) v1.0.1; `TC-CLI-030` dừng ở 3.12) và chưa có test case chạy `serve` rồi mở SCR-001..SCR-011 trên Python 3.6 |
| `NFR-CMP-004` | `US-CLI-01`, `US-CLI-02` | 6 | [`TC-CLI-001`](test-cases-ptch-cli-rpt.md), [`TC-CLI-002`](test-cases-ptch-cli-rpt.md), [`TC-CLI-003`](test-cases-ptch-cli-rpt.md), [`TC-CLI-004`](test-cases-ptch-cli-rpt.md), [`TC-CLI-005`](test-cases-ptch-cli-rpt.md), [`TC-CLI-006`](test-cases-ptch-cli-rpt.md) |
| `NFR-CMP-005` | `US-CLI-03`, `US-CLI-10` | 6 | [`TC-CLI-007`](test-cases-ptch-cli-rpt.md), [`TC-CLI-008`](test-cases-ptch-cli-rpt.md), [`TC-CLI-009`](test-cases-ptch-cli-rpt.md), [`TC-CLI-028`](test-cases-ptch-cli-rpt.md), [`TC-CLI-029`](test-cases-ptch-cli-rpt.md), [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) |
| `NFR-ENV-01` | `US-UPG-04` | 4 | [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-012`](test-cases-upg.md), [`TC-UPG-013`](test-cases-upg.md) |
| `NFR-ENV-02` | `US-UPG-12`, `US-CON-12` | 6 | [`TC-UPG-036`](test-cases-upg.md), [`TC-UPG-037`](test-cases-upg.md), [`TC-UPG-038`](test-cases-upg.md), [`TC-CON-035`](test-cases-con.md), [`TC-CON-036`](test-cases-con.md), [`TC-CON-037`](test-cases-con.md) |
| `NFR-ENV-03` | `US-UPG-11` | 3 | [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-034`](test-cases-upg.md), [`TC-UPG-035`](test-cases-upg.md) |
| `NFR-ENV-04` | `US-UPG-04` | 4 | [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-012`](test-cases-upg.md), [`TC-UPG-013`](test-cases-upg.md) |
| `NFR-ENV-05` | `US-PTCH-08`, `US-UPG-04` | 7 | [`TC-PTCH-023`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-024`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-025`](test-cases-ptch-cli-rpt.md), [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-012`](test-cases-upg.md), [`TC-UPG-013`](test-cases-upg.md) |
| `NFR-ENV-06` | `US-SCN-03` | 3 | [`TC-SCN-008`](test-cases.md), [`TC-SCN-009`](test-cases.md), [`TC-SCN-010`](test-cases.md) |
| `NFR-ENV-07` | `US-SCAN-01` | 3 | [`TC-SCAN-001`](test-cases.md), [`TC-SCAN-002`](test-cases.md), [`TC-SCAN-003`](test-cases.md) |
| `NFR-FEED-001` | `US-FEED-01` | 4 | [`TC-FEED-001`](test-cases-feed.md), [`TC-FEED-002`](test-cases-feed.md), [`TC-FEED-003`](test-cases-feed.md), [`TC-FEED-004`](test-cases-feed.md) |
| `NFR-FEED-002` | — (chưa story nào tham chiếu; liên kết trực tiếp, xem §4.1) | 0 | **Chưa phủ**: không test case nào đo thời gian `scan` chờ đồng bộ khi bundle quá TTL. Test case cần thêm: xem §4.1 mục 2 |
| `NFR-FEED-003` | `US-FEED-09` | 3 | [`TC-FEED-026`](test-cases-feed.md), [`TC-FEED-027`](test-cases-feed.md), [`TC-FEED-028`](test-cases-feed.md) |
| `NFR-FEED-004` | `US-FEED-03`, `US-FEED-11` | 6 | [`TC-FEED-008`](test-cases-feed.md), [`TC-FEED-009`](test-cases-feed.md), [`TC-FEED-010`](test-cases-feed.md), [`TC-FEED-032`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md), [`TC-FEED-034`](test-cases-feed.md) |
| `NFR-FEED-005` | `US-FEED-11` | 3 | [`TC-FEED-032`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md), [`TC-FEED-034`](test-cases-feed.md) |
| `NFR-FEED-006` | `US-FEED-10`, `US-FEED-15` | 6 | [`TC-FEED-029`](test-cases-feed.md), [`TC-FEED-030`](test-cases-feed.md), [`TC-FEED-031`](test-cases-feed.md), [`TC-FEED-045`](test-cases-feed.md), [`TC-FEED-046`](test-cases-feed.md), [`TC-FEED-047`](test-cases-feed.md) |
| `NFR-FEED-007` | — (chưa story nào tham chiếu; liên kết trực tiếp, xem §4.1) | 6 | [`TC-ASMT-015`](test-cases.md) (KQ2, OSV bị chặn, lượt quét hoàn tất), [`TC-ASMT-018`](test-cases.md) (`api.wordpress.org` trả 503 × 3, `min_patched` tính từ NVD), [`TC-FEED-021`](test-cases-feed.md) (KQ2, OSV lỗi, lockfile khác đánh giá bằng cache), [`TC-SCN-006`](test-cases.md) (không có mạng, bundle 2.200 giờ: `scan` trả kết quả với `ERR-SCN-503-01`), [`TC-FEED-035`](test-cases-feed.md) (không có mạng, chỉ có snapshot đóng gói: mọi runtime có kết quả với `data_origin` = `SNAPSHOT`), [`TC-FEED-002`](test-cases-feed.md) (đo phía `feeds update`, không phải `scan`: 1 nguồn lỗi, bundle mới vẫn được tạo). **Một phần**: chưa có test case cho lần lượt từng nguồn trong 15 nguồn online (`SRC-001`..`SRC-015`) lỗi và tổ hợp chặn toàn bộ theo cách kiểm của [data-sources.md §6](../srs/data-sources.md); test case cần thêm: xem §4.1 mục 3 |
| `NFR-FEED-008` | `US-FEED-01` | 4 | [`TC-FEED-001`](test-cases-feed.md), [`TC-FEED-002`](test-cases-feed.md), [`TC-FEED-003`](test-cases-feed.md), [`TC-FEED-004`](test-cases-feed.md) |
| `NFR-MNT-001` | `US-SCN-03`, `US-SCN-04`, `US-CLI-04` | 9 | [`TC-SCN-008`](test-cases.md), [`TC-SCN-009`](test-cases.md), [`TC-SCN-010`](test-cases.md), [`TC-SCN-011`](test-cases.md), [`TC-SCN-012`](test-cases.md), [`TC-SCN-013`](test-cases.md), [`TC-CLI-010`](test-cases-ptch-cli-rpt.md), [`TC-CLI-011`](test-cases-ptch-cli-rpt.md), [`TC-CLI-012`](test-cases-ptch-cli-rpt.md) |
| `NFR-MNT-002` | `US-ASMT-01`, `US-FEED-09` | 7 | [`TC-ASMT-001`](test-cases.md), [`TC-ASMT-002`](test-cases.md), [`TC-ASMT-003`](test-cases.md), [`TC-ASMT-004`](test-cases.md), [`TC-FEED-026`](test-cases-feed.md), [`TC-FEED-027`](test-cases-feed.md), [`TC-FEED-028`](test-cases-feed.md) |
| `NFR-MNT-003` | — (chưa story nào tham chiếu; liên kết trực tiếp, xem §4.1) | 0 | **Chưa phủ** bằng test case; đo bằng cổng CI. Bước kiểm cần thêm: xem §4.1 mục 4 |
| `NFR-MNT-004` | — (điều kiện phát hành lớp "Phase 1 — P0" ở [backlog.md](../userstories/backlog.md); liên kết trực tiếp, xem §4.1) | — | Đo bằng ma trận truy vết, không bằng test case riêng: [rtm.md](rtm.md) v1.0.2 §2 ghi 141/142 FR P0 có ≥ 1 test case, thiếu `FR-UPG-ACK-001` (§2.1 mục 1) → **chưa đạt**. [test-cases-upg.md](test-cases-upg.md) v1.0.2 đã thêm `TC-UPG-111` (`migrate ack`, `ERR-UPG-409-04`) cho FR này; rtm.md cần thêm dòng `FR-UPG-ACK-001` ↔ `TC-UPG-111` để đạt 142/142 |
| `NFR-PERF-001` | `US-CON-06`, `US-CON-19` | 6 | [`TC-CON-017`](test-cases-con.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-019`](test-cases-con.md), [`TC-CON-058`](test-cases-con.md), [`TC-CON-059`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md) |
| `NFR-PERF-002` | `US-CON-19` | 3 | [`TC-CON-058`](test-cases-con.md), [`TC-CON-059`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md) |
| `NFR-PERF-003` | `US-CON-10`, `US-JOB-06` | 7 | [`TC-CON-029`](test-cases-con.md), [`TC-CON-030`](test-cases-con.md), [`TC-CON-031`](test-cases-con.md), [`TC-JOB-016`](test-cases-job-flt.md), [`TC-JOB-017`](test-cases-job-flt.md), [`TC-JOB-018`](test-cases-job-flt.md), [`TC-JOB-025`](test-cases-job-flt.md) |
| `NFR-PERF-004` | `US-SCAN-02` | 3 | [`TC-SCAN-004`](test-cases.md), [`TC-SCAN-005`](test-cases.md), [`TC-SCAN-006`](test-cases.md) |
| `NFR-PERF-005` | `US-PLAN-02` | 3 | [`TC-PLAN-005`](test-cases-plan-cmpt.md), [`TC-PLAN-006`](test-cases-plan-cmpt.md), [`TC-PLAN-007`](test-cases-plan-cmpt.md) |
| `NFR-PERF-006` | `US-CON-01` | 4 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-002`](test-cases-con.md), [`TC-CON-003`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `NFR-PERF-007` | `US-CON-06`, `US-CON-17` | 6 | [`TC-CON-017`](test-cases-con.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-019`](test-cases-con.md), [`TC-CON-052`](test-cases-con.md), [`TC-CON-053`](test-cases-con.md), [`TC-CON-054`](test-cases-con.md) |
| `NFR-PERF-008` | `US-FLT-03` | 3 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-008`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `NFR-REL-001` | `US-CON-06` | 3 | [`TC-CON-017`](test-cases-con.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-019`](test-cases-con.md) |
| `NFR-REL-002` | `US-JOB-07` | 3 | [`TC-JOB-019`](test-cases-job-flt.md), [`TC-JOB-020`](test-cases-job-flt.md), [`TC-JOB-021`](test-cases-job-flt.md) |
| `NFR-REL-003` | `US-JOB-04` | 3 | [`TC-JOB-010`](test-cases-job-flt.md), [`TC-JOB-011`](test-cases-job-flt.md), [`TC-JOB-012`](test-cases-job-flt.md) |
| `NFR-REL-004` | `US-JOB-02` | 3 | [`TC-JOB-004`](test-cases-job-flt.md), [`TC-JOB-005`](test-cases-job-flt.md), [`TC-JOB-006`](test-cases-job-flt.md) |
| `NFR-REL-005` | `US-PTCH-09` | 3 | [`TC-PTCH-026`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-027`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md) |
| `NFR-REL-006` | `US-PLAN-02` | 3 | [`TC-PLAN-005`](test-cases-plan-cmpt.md), [`TC-PLAN-006`](test-cases-plan-cmpt.md), [`TC-PLAN-007`](test-cases-plan-cmpt.md) |
| `NFR-REL-007` | `US-JOB-08` | 3 | [`TC-JOB-022`](test-cases-job-flt.md), [`TC-JOB-023`](test-cases-job-flt.md), [`TC-JOB-024`](test-cases-job-flt.md) |
| `NFR-SEC-001` | `US-CON-01` | 4 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-002`](test-cases-con.md), [`TC-CON-003`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `NFR-SEC-002` | `US-CON-01` | 4 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-002`](test-cases-con.md), [`TC-CON-003`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) |
| `NFR-SEC-003` | `US-CON-03` | 3 | [`TC-CON-008`](test-cases-con.md), [`TC-CON-009`](test-cases-con.md), [`TC-CON-010`](test-cases-con.md) |
| `NFR-SEC-004` | `US-CON-04` | 3 | [`TC-CON-011`](test-cases-con.md), [`TC-CON-012`](test-cases-con.md), [`TC-CON-013`](test-cases-con.md) |
| `NFR-SEC-005` | `US-CON-05` | 3 | [`TC-CON-014`](test-cases-con.md), [`TC-CON-015`](test-cases-con.md), [`TC-CON-016`](test-cases-con.md) |
| `NFR-SEC-006` | `US-CON-17` | 3 | [`TC-CON-052`](test-cases-con.md), [`TC-CON-053`](test-cases-con.md), [`TC-CON-054`](test-cases-con.md) |
| `NFR-SEC-007` | `US-CON-18` | 3 | [`TC-CON-055`](test-cases-con.md), [`TC-CON-056`](test-cases-con.md), [`TC-CON-057`](test-cases-con.md) |
| `NFR-SEC-008` | `US-CON-18` | 3 | [`TC-CON-055`](test-cases-con.md), [`TC-CON-056`](test-cases-con.md), [`TC-CON-057`](test-cases-con.md) |
| `NFR-SEC-009` | `US-CON-07` | 3 | [`TC-CON-020`](test-cases-con.md), [`TC-CON-021`](test-cases-con.md), [`TC-CON-022`](test-cases-con.md) |
| `NFR-SEC-010` | `US-JOB-05` | 3 | [`TC-JOB-013`](test-cases-job-flt.md), [`TC-JOB-014`](test-cases-job-flt.md), [`TC-JOB-015`](test-cases-job-flt.md) |
| `NFR-SEC-011` | `US-FLT-01` | 3 | [`TC-FLT-001`](test-cases-job-flt.md), [`TC-FLT-002`](test-cases-job-flt.md), [`TC-FLT-003`](test-cases-job-flt.md) |
| `NFR-SEC-012` | `US-FLT-03` | 3 | [`TC-FLT-007`](test-cases-job-flt.md), [`TC-FLT-008`](test-cases-job-flt.md), [`TC-FLT-009`](test-cases-job-flt.md) |
| `NFR-USE-001` | `US-PTCH-01`, `US-CON-07` | 7 | [`TC-PTCH-001`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-002`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-003`](test-cases-ptch-cli-rpt.md), [`TC-PTCH-004`](test-cases-ptch-cli-rpt.md), [`TC-CON-020`](test-cases-con.md), [`TC-CON-021`](test-cases-con.md), [`TC-CON-022`](test-cases-con.md) |
| `NFR-USE-002` | `US-CON-08` | 3 | [`TC-CON-023`](test-cases-con.md), [`TC-CON-024`](test-cases-con.md), [`TC-CON-025`](test-cases-con.md) |
| `NFR-USE-003` | `US-CON-06` | 3 | [`TC-CON-017`](test-cases-con.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-019`](test-cases-con.md) |
| `NFR-USE-004` | `US-CON-06` | 3 | [`TC-CON-017`](test-cases-con.md), [`TC-CON-018`](test-cases-con.md), [`TC-CON-019`](test-cases-con.md) |
| `NFR-USE-005` | `US-CON-19` | 3 | [`TC-CON-058`](test-cases-con.md), [`TC-CON-059`](test-cases-con.md), [`TC-CON-060`](test-cases-con.md) |
| `NFR-USE-006` | `US-CON-16` | 4 | [`TC-CON-048`](test-cases-con.md), [`TC-CON-049`](test-cases-con.md), [`TC-CON-050`](test-cases-con.md), [`TC-CON-051`](test-cases-con.md) |

### 4.1 NFR liên kết trực tiếp: mức phủ và việc cần làm
| # | NFR | Mức phủ | Việc cần làm | File phải sửa |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `NFR-CMP-003` | Một phần (3 TC) | Thêm dòng dữ liệu `Python 3.14, root` × `assess --json` và `serve` vào `TC-CLI-030`; thêm 1 test case chạy `serve` trên Python 3.6 và 3.14, đăng nhập rồi mở SCR-001..SCR-011 trên Chrome, Edge, Firefox, Safari (2 bản ổn định gần nhất mỗi trình duyệt), KQ: 11/11 màn hình hiển thị, 0 lỗi JavaScript trên console DevTools, 0 vi phạm CSP | [test-cases-ptch-cli-rpt.md](test-cases-ptch-cli-rpt.md), [test-cases-con.md](test-cases-con.md) |
| 2 | `NFR-FEED-002` | Chưa phủ (0 TC) | Thêm 1 test case theo cách kiểm của data-sources.md §6: bundle có `data_age_h` = 12 với TTL 6 giờ, máy chủ giả lập nguồn trả chậm 300 s; chạy `php-quickpatch.sh scan --json`; KQ: tool ngừng chờ đồng bộ ≤ 120 s sau khi lệnh bắt đầu (đo bằng mốc thời gian trong `php-quickpatch.log`), đánh giá bằng bundle hiện có, `data.freshness` = `AGING`, mã thoát 0 hoặc 1 | [test-cases-feed.md](test-cases-feed.md) |
| 3 | `NFR-FEED-007` | Một phần (6 TC) | Thêm 1 test case: bundle có `data_age_h` = 12 (quá TTL để `scan` gọi nguồn), chạy 16 lượt `php-quickpatch.sh scan --json` — 15 lượt mỗi lượt cho 1 nguồn online trong `SRC-001`..`SRC-015` lỗi (chặn host bằng `/etc/hosts`; 2 nguồn chung host như `SRC-002`/`SRC-003` trên php.net, `SRC-007`/`SRC-014` trên OSV thì máy chủ giả lập nguồn trả 503 theo đường dẫn), 1 lượt chặn mọi host của 15 nguồn; KQ: 16/16 lượt có mã thoát 0 hoặc 1, mọi runtime có `status` khác `UNKNOWN`, `warnings[]` nêu nguồn bị chặn | [test-cases-feed.md](test-cases-feed.md) |
| 4 | `NFR-MNT-003` | Chưa phủ (0 TC, đo bằng CI) | Thêm bước kiểm tĩnh vào tiêu chí phát hành ([test-cases.md §1.5](test-cases.md)): `shellcheck -S warning php-quickpatch.sh` trả 0 phát hiện; `python3.6 -m py_compile` và `python3.14 -m py_compile` cho mọi file `*.py` của gói phát hành trả mã 0 | [test-cases.md](test-cases.md) |
| 5 | `NFR-MNT-004` | Đo bằng RTM, chưa đạt (141/142 FR P0) | Thêm dòng `FR-UPG-ACK-001` ↔ `TC-UPG-111` (`US-UPG-07`) và cập nhật tổng ở §2 | [rtm.md](rtm.md) |
| 6 | 5 NFR trên | Không truy vết được qua story | Thêm mã NFR vào story tương ứng (vd `NFR-FEED-002`, `NFR-FEED-007` vào `US-FEED-01` hoặc `US-FEED-10`; `NFR-CMP-003` vào `US-CON-01`; `NFR-MNT-003`, `NFR-MNT-004` vào điều kiện phát hành), sau đó đổi cột "Story tham chiếu" ở §4 | [backlog.md](../userstories/backlog.md) |

## 5. Chuyển trạng thái `T-*` → test case (97 mã của DOC-SRS-QP-STATE-001)
Nguồn danh sách mã: [states.md](../srs/states.md) v1.0.1 §2–§7 (rules/12, mỗi mã `T-*` ≥ 1 test case theo §1.1 của tài liệu đó). Mức phủ:
- **Đủ**: test case kiểm sự kiện kích hoạt, mọi điều kiện bảo vệ đã quy định trong SRS và trạng thái đích (hoặc mã lỗi khi bị từ chối). Phần gắn `ĐX` chưa kiểm được ghi ở cột "Ghi chú".
- **Một phần**: có test case nhưng thiếu ít nhất 1 trạng thái nguồn, nhánh hoặc điều kiện bảo vệ đã quy định; cột "Ghi chú" nêu phần thiếu.
- **Chưa phủ**: không có test case; cột "Ghi chú" nêu lý do (chuyển `ĐX` chờ câu hỏi `Q-ST-*`, hoặc AC nguồn không có kịch bản) và test case cần bổ sung ở file nào.

### 5.1 Tổng hợp
| Máy trạng thái | Số mã | Đủ | Một phần | Chưa phủ |
| :--- | :---: | :---: | :---: | :---: |
| `T-JOB` — Job console | 17 | 15 | 0 | 2 |
| `T-PLN` — Kế hoạch nâng cấp | 13 | 9 | 3 | 1 |
| `T-SW` — Lượt chuyển site | 19 | 11 | 4 | 4 |
| `T-CHK` — Mục checklist | 16 | 7 | 4 | 5 |
| `T-FD` — Bundle dữ liệu feed | 12 | 11 | 0 | 1 |
| `T-SRC` — Trạng thái nguồn dữ liệu | 5 | 2 | 2 | 1 |
| `T-CON` — Tiến trình serve và token | 8 | 7 | 1 | 0 |
| `T-SES` — Phiên trình duyệt | 7 | 7 | 0 | 0 |
| **Tổng** | **97** | **69** | **14** | **14** |

83/97 mã `T-*` có ≥ 1 test case; 14 mã chưa phủ, trong đó 4 mã là chuyển `ĐX` chờ duyệt.

### 5.2 Job console (DIAG-STATE-QP-JOB-002, states.md §2)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-JOB-01` | `[*]` → `QUEUED` | Đủ | 4 | [`TC-JOB-001`](test-cases-job-flt.md), [`TC-CON-014`](test-cases-con.md), [`TC-CON-048`](test-cases-con.md) (KQ2), [`TC-PLAN-017`](test-cases-plan-cmpt.md) (KQ1) | Job đọc trả 202 + `job_id`; job ghi kèm `confirm_dry_run_job_id` hợp lệ |
| `T-JOB-02` | `[*]` → không tạo | Đủ | 9 | [`TC-CON-012`](test-cases-con.md), [`TC-CON-009`](test-cases-con.md), [`TC-CON-015`](test-cases-con.md), [`TC-CON-041`](test-cases-con.md), [`TC-CON-056`](test-cases-con.md), [`TC-CON-057`](test-cases-con.md), [`TC-CON-049`](test-cases-con.md), [`TC-JOB-002`](test-cases-job-flt.md) (KQ1–KQ2), [`TC-CON-059`](test-cases-con.md) (KQ2) | Đủ 9/9 điều kiện của states.md §2.3: 421, 401, 403/415, 413, 422, 428, 409, 429, 503 |
| `T-JOB-03` | `QUEUED` → `RUNNING` | Đủ | 2 | [`TC-JOB-001`](test-cases-job-flt.md) (KQ1), [`TC-JOB-004`](test-cases-job-flt.md) | Giới hạn đồng thời theo loại job và khoá không chặn `-x`/`-s` |
| `T-JOB-04` | `QUEUED` → `QUEUED` (chờ khoá) | Đủ | 1 | [`TC-JOB-005`](test-cases-job-flt.md) (KQ1) | Thử lại mỗi 5 s |
| `T-JOB-05` | `QUEUED` → `FAILED` (chờ khoá 30 phút) | Đủ | 1 | [`TC-JOB-005`](test-cases-job-flt.md) (KQ2) | `ERR-JOB-409-02` |
| `T-JOB-06` | `QUEUED` → `CANCELLED` | Đủ | 2 | [`TC-JOB-007`](test-cases-job-flt.md) (KQ1), [`TC-CON-029`](test-cases-con.md) (KQ2) | — |
| `T-JOB-07` | `QUEUED` → `CANCELLED` (`CONSOLE_RESTART`) | Chưa phủ | 0 | — | Chuyển `ĐX` chờ `Q-ST-01`. `TC-JOB-010`..`012` chỉ có job `RUNNING`. Sau khi duyệt: thêm 1 job `QUEUED` vào `TC-JOB-012`, KQ: `CANCELLED` lý do `CONSOLE_RESTART`, 0 tiến trình được tạo |
| `T-JOB-08` | `RUNNING` → `SUCCEEDED` | Đủ | 3 | [`TC-JOB-001`](test-cases-job-flt.md) (KQ3), [`TC-JOB-019`](test-cases-job-flt.md), [`TC-PLAN-017`](test-cases-plan-cmpt.md) (KQ2) | Mã thoát 0 |
| `T-JOB-09` | `RUNNING` → `SUCCEEDED_WITH_ISSUES` | Đủ | 1 | [`TC-JOB-001`](test-cases-job-flt.md) (KQ3) | Mã thoát 1 |
| `T-JOB-10` | `RUNNING` → `FAILED` (mã thoát 2) | Đủ | 2 | [`TC-JOB-002`](test-cases-job-flt.md) (KQ3), [`TC-UPG-022`](test-cases-upg.md) (KQ2) | `ERR-JOB-500-01` |
| `T-JOB-11` | `RUNNING` → `FAILED` (timeout) | Đủ | 1 | [`TC-JOB-003`](test-cases-job-flt.md) | 6 dòng dữ liệu biên 300/301 s, 1.201 s, 1.800 s, 961 s, 601 s. Cách dừng job `write` vượt timeout trong vùng tới hạn chưa quy định (`Q-ST-02`), chưa kiểm |
| `T-JOB-12` | `RUNNING` (`read`, `data`) → `CANCELLED` | Đủ | 1 | [`TC-JOB-007`](test-cases-job-flt.md) (KQ2) | Phủ job `read` (SIGTERM nhóm, SIGKILL sau 10 s). Job `data` áp như `read` là `ĐX` (`Q-ST-03`), chưa kiểm |
| `T-JOB-13` | `RUNNING` (`write`, ngoài vùng tới hạn) → `CANCELLED` | Chưa phủ | 0 | — | AC-JOB-07..09 không có kịch bản. Cần test case bổ sung ở test-cases-job-flt.md: huỷ job `fix` khi `phase` chưa tới `MANIFEST_WRITTEN` → `CANCELLED`, audit `result` = `cancelled`, 0 thay đổi |
| `T-JOB-14` | `RUNNING` (`write`, vùng tới hạn) → `RUNNING` | Đủ | 2 | [`TC-JOB-008`](test-cases-job-flt.md) (dòng 1–2), [`TC-CON-030`](test-cases-con.md) (KQ1) | `ERR-JOB-423-01` với `MANIFEST_WRITTEN`, `VERIFYING`, `CHANGING` |
| `T-JOB-15` | `RUNNING` (`phase = HC_RUNNING`) → `CANCELLED` | Đủ | 1 | [`TC-JOB-009`](test-cases-job-flt.md) (KQ1) | Rollback `MANUAL`, liên kết `T-SW-11` |
| `T-JOB-16` | `RUNNING` → `INTERRUPTED` | Đủ | 2 | [`TC-JOB-011`](test-cases-job-flt.md), [`TC-JOB-012`](test-cases-job-flt.md) (KQ1) | `ERR-JOB-500-02`; đối soát ≤ 5 s; 0 job ghi tự chạy lại |
| `T-JOB-17` | `RUNNING` → `RUNNING` (PID còn sống) | Đủ | 1 | [`TC-JOB-010`](test-cases-job-flt.md) | Điều kiện `/proc/<pid>/cmdline` khớp `argv` là `ĐX` (`Q-ST-01`), chưa kiểm PID bị tái sử dụng |

### 5.3 Kế hoạch nâng cấp (DIAG-STATE-QP-PLAN-002, states.md §3)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-PLN-01` | `[*]` → `draft` | Đủ | 3 | [`TC-PLAN-005`](test-cases-plan-cmpt.md) (KQ1), [`TC-CLI-016`](test-cases-ptch-cli-rpt.md), [`TC-CON-023`](test-cases-con.md) | — |
| `T-PLN-02` | `[*]` → không tạo | Đủ | 7 | [`TC-PLAN-006`](test-cases-plan-cmpt.md), [`TC-PLAN-002`](test-cases-plan-cmpt.md), [`TC-PLAN-003`](test-cases-plan-cmpt.md), [`TC-PLAN-012`](test-cases-plan-cmpt.md), [`TC-CMPT-026`](test-cases-plan-cmpt.md), [`TC-FEED-102`](test-cases-feed.md) (dòng 91 ngày), [`TC-CON-024`](test-cases-con.md) | Đủ 6/6 mã: `ERR-PLAN-409-01`, `ERR-SCN-409-02`, `ERR-PLAN-422-01`, `ERR-SCN-409-03`, `ERR-SCN-409-01`, `ERR-SCN-503-01` |
| `T-PLN-03` | `draft` → `approved` | Đủ | 5 | [`TC-PLAN-020`](test-cases-plan-cmpt.md) (KQ1), [`TC-CLI-016`](test-cases-ptch-cli-rpt.md) (KQ2), [`TC-CON-026`](test-cases-con.md) (KQ2), [`TC-PLAN-021`](test-cases-plan-cmpt.md), [`TC-PLAN-025`](test-cases-plan-cmpt.md) (KQ2) | `TC-PLAN-021`, `TC-PLAN-025`: guard `BR-PLAN-003` không đạt → giữ `draft` (`ERR-PLAN-412-01`) |
| `T-PLN-04` | `draft`, `approved` → `cancelled` (kế hoạch mới cho cùng runtime) | Một phần | 1 | [`TC-PLAN-007`](test-cases-plan-cmpt.md) (KQ1) | Chỉ có nguồn `draft`; nguồn `approved` chưa có dòng dữ liệu (bổ sung vào `TC-PLAN-007`) |
| `T-PLN-05` | `draft`, `approved` → `cancelled` (`plan cancel`) | Một phần | 1 | [`TC-PLAN-023`](test-cases-plan-cmpt.md) (dòng 4) | Chỉ có guard âm (có job `RUNNING` → `ERR-PLAN-409-02`); luồng huỷ thành công chưa có test case |
| `T-PLN-06` | `approved` → `draft` (đổi canary) | Đủ | 1 | [`TC-PLAN-010`](test-cases-plan-cmpt.md) (KQ3) | — |
| `T-PLN-07` | `approved` → `in_progress` | Đủ | 2 | [`TC-PLAN-020`](test-cases-plan-cmpt.md) (KQ2), [`TC-UPG-020`](test-cases-upg.md) (KQ2) | — |
| `T-PLN-08` | `in_progress` → `in_progress` (lượt chuyển không `PASSED`) | Đủ | 2 | [`TC-UPG-022`](test-cases-upg.md) (KQ3), [`TC-UPG-104`](test-cases-upg.md) (KQ3) | Dừng các site còn lại (`BR-UPG-003`) |
| `T-PLN-09` | `in_progress` → `completed` | Đủ | 1 | [`TC-PLAN-020`](test-cases-plan-cmpt.md) (KQ3) | — |
| `T-PLN-10` | `in_progress` → `rolled_back` | Đủ | 1 | [`TC-PLAN-023`](test-cases-plan-cmpt.md) (dòng 5) | Guard "không có job `RUNNING`" là `ĐX`, chưa kiểm |
| `T-PLN-11` | `in_progress` → `cancelled` | Chưa phủ | 0 | — | AC-PLAN không có kịch bản. Cần test case bổ sung ở test-cases-plan-cmpt.md: `plan cancel` kế hoạch `in_progress` khi 0 job `RUNNING` → `cancelled`, mục chỉ đọc (`ERR-PLAN-409-02` khi cập nhật) |
| `T-PLN-12` | Giữ trạng thái, `stale=true` | Một phần | 2 | [`TC-PLAN-022`](test-cases-plan-cmpt.md), [`TC-PLAN-023`](test-cases-plan-cmpt.md) (dòng 1–3) | Phủ `scan_fingerprint` đổi, `R` đích tăng 19/20 điểm, KEV mới; chưa có dòng `catalog_version` đổi và nhánh đích chuyển `EOL` |
| `T-PLN-13` | Hành động không hợp lệ → không đổi | Đủ | 2 | [`TC-PLAN-015`](test-cases-plan-cmpt.md), [`TC-PLAN-023`](test-cases-plan-cmpt.md) (dòng 4) | `ERR-PLAN-409-02` |

### 5.4 Lượt chuyển site (DIAG-STATE-QP-ENV-003, states.md §4)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-SW-01` | `[*]` → `PREFLIGHT` | Đủ | 3 | [`TC-UPG-010`](test-cases-upg.md), [`TC-UPG-039`](test-cases-upg.md), [`TC-UPG-108`](test-cases-upg.md) (KQ3) | — |
| `T-SW-02` | `[*]` → không tạo | Đủ | 6 | [`TC-UPG-011`](test-cases-upg.md), [`TC-UPG-021`](test-cases-upg.md), [`TC-UPG-022`](test-cases-upg.md) (KQ1–KQ2), [`TC-UPG-023`](test-cases-upg.md) (KQ1), [`TC-UPG-108`](test-cases-upg.md) (KQ1–KQ2), [`TC-CLI-020`](test-cases-ptch-cli-rpt.md) (KQ2) | `ERR-ENV-409-01`, `ERR-UPG-409-02`, `ERR-UPG-423-01`, `ERR-UPG-409-03`. states.md §4.2 còn ghi "mã lỗi chưa định nghĩa" cho site kế tiếp khi lượt trước chưa xác nhận; error-matrix v1.0.1 đã định nghĩa `ERR-UPG-409-03` |
| `T-SW-03` | `PREFLIGHT` → `ABORTED` (C2–C6 không đạt) | Một phần | 4 | [`TC-UPG-013`](test-cases-upg.md) (dòng 1–2), [`TC-UPG-023`](test-cases-upg.md) (KQ2), [`TC-UPG-028`](test-cases-upg.md), [`TC-UPG-025`](test-cases-upg.md) | Phủ C2, C4, C5. C3 (`ERR-ENV-500-01`) và C6 (`ERR-ENV-507-01`) chưa có test case trong lượt chuyển; `TC-UPG-008`, `TC-PTCH-024` kiểm cùng mã ở mục tạo pool và lệnh thay đổi chung |
| `T-SW-04` | `PREFLIGHT` → `ABORTED` (huỷ job) | Chưa phủ | 0 | — | Cần test case bổ sung ở test-cases-job-flt.md: huỷ job `migrate_switch` khi `phase` chưa tới `MANIFEST_WRITTEN` → lượt `ABORTED`, job `CANCELLED`, 0 reload web server |
| `T-SW-05` | `PREFLIGHT` → `ABORTED` (C7/C8 lỗi, đã khôi phục) | Một phần | 2 | [`TC-UPG-012`](test-cases-upg.md), [`TC-UPG-015`](test-cases-upg.md) | Kiểm khôi phục ≤ 5 s, không reload, `ERR-ENV-500-02`/`ERR-ENV-502-01`; trạng thái đích `ABORTED` là `ĐX` (`Q-ST-04`), test case chưa khẳng định `status` |
| `T-SW-06` | `PREFLIGHT` → `SWITCHED` | Đủ | 3 | [`TC-UPG-010`](test-cases-upg.md) (KQ1–KQ2, KQ4), [`TC-UPG-014`](test-cases-upg.md), [`TC-UPG-039`](test-cases-upg.md) (KQ1–KQ2) | Manifest trước C7, graceful reload, C6–C10 ≤ 30 s, 0 phản hồi 5xx |
| `T-SW-07` | `PREFLIGHT` → `ROLLED_BACK` (C9 reload lỗi) | Chưa phủ | 0 | — | Cần test case bổ sung ở test-cases-upg.md: graceful reload ở C9 trả lỗi → R1–R7, `ROLLED_BACK`, `rollback_reason` = mã bước, dừng site còn lại |
| `T-SW-08` | `HC_RUNNING` → `HC_RUNNING` (chạy lại health check) | Đủ | 2 | [`TC-JOB-012`](test-cases-job-flt.md) (KQ2), [`TC-UPG-035`](test-cases-upg.md) (KQ2) | `t_C9` + 900 s, dùng `baseline.json` đã lưu |
| `T-SW-09` | `SWITCHED` → `HC_RUNNING` | Đủ | 2 | [`TC-UPG-010`](test-cases-upg.md) (KQ2–KQ3), [`TC-UPG-030`](test-cases-upg.md) | `HC-C0`: `accepted conn` của pool đích tăng ≥ 1 |
| `T-SW-10` | `SWITCHED` → `ROLLED_BACK` (`HC-C0` không đạt) | Chưa phủ | 0 | — | Test case tự rollback hiện có đều bắt đầu từ `HC_RUNNING`. Cần test case bổ sung ở test-cases-upg.md: C10 không thấy `accepted conn` tăng trong 10 s → `ROLLED_BACK`, `rollback_reason` = `HC-C0`, `ERR-SCN-500-01` |
| `T-SW-11` | `HC_RUNNING` → `ROLLED_BACK` | Đủ | 5 | [`TC-UPG-033`](test-cases-upg.md), [`TC-UPG-103`](test-cases-upg.md), [`TC-UPG-104`](test-cases-upg.md), [`TC-UPG-041`](test-cases-upg.md) (KQ2), [`TC-JOB-009`](test-cases-job-flt.md) (KQ1) | Nhánh (a) `HC-C2`, `HC-C7`, `HC-C9`; nhánh (b) huỷ job `MANUAL` |
| `T-SW-12` | `HC_RUNNING` → `HC_FAILED_KEPT` | Đủ | 2 | [`TC-UPG-034`](test-cases-upg.md), [`TC-CON-018`](test-cases-con.md) (KQ1) | `ERR-HC-500-01` |
| `T-SW-13` | `HC_RUNNING` → `PASSED` | Đủ | 4 | [`TC-UPG-010`](test-cases-upg.md) (KQ3), [`TC-UPG-030`](test-cases-upg.md) (KQ2), [`TC-UPG-020`](test-cases-upg.md) (KQ1), [`TC-UPG-039`](test-cases-upg.md) (KQ3) | Mở lượt cho site kế tiếp |
| `T-SW-14` | `HC_FAILED_KEPT` → `ROLLED_BACK` | Chưa phủ | 0 | — | `TC-UPG-034` KQ2, `TC-CON-018` KQ1 chỉ kiểm nút rollback hiển thị. Bước R1 (DOC-SRS-QP-ENV-001 §5.2) chưa nhận `HC_FAILED_KEPT` (`I-ST-01`, `Q-ST-05`); bổ sung test case sau khi CR được duyệt |
| `T-SW-15` | `PASSED` → `ROLLED_BACK` (thủ công) | Đủ | 3 | [`TC-UPG-036`](test-cases-upg.md), [`TC-CON-035`](test-cases-con.md), [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md) (KQ1) | R1–R6 ≤ 60 s |
| `T-SW-16` | `PASSED` → `PASSED` (`$OLD` đã gỡ) | Đủ | 2 | [`TC-UPG-037`](test-cases-upg.md), [`TC-CON-036`](test-cases-con.md) (KQ2) | `ERR-ENV-410-01` |
| `T-SW-17` | `PASSED` → `PASSED`, `rollback_available=false` | Đủ | 3 | [`TC-UPG-045`](test-cases-upg.md), [`TC-UPG-046`](test-cases-upg.md), [`TC-UPG-047`](test-cases-upg.md) | Biên 14 ngày, `ERR-UPG-412-01`, xác nhận kép |
| `T-SW-18` | 5 nguồn → `ROLLBACK_FAILED` | Một phần | 3 | [`TC-UPG-035`](test-cases-upg.md) (KQ1), [`TC-UPG-038`](test-cases-upg.md) (KQ2), [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md) (KQ2) | Nguồn `HC_RUNNING` có test case khẳng định `ROLLBACK_FAILED`; nguồn `PASSED` chỉ kiểm `ERR-ENV-500-03`, chưa khẳng định `status`; nguồn `PREFLIGHT`, `SWITCHED`, `HC_FAILED_KEPT` chưa có test case (`Q-ST-05`) |
| `T-SW-19` | `ROLLBACK_FAILED` → `ROLLBACK_FAILED` (xác nhận đã xử lý) | Một phần | 1 | [`TC-UPG-023`](test-cases-upg.md) (KQ2) | Chỉ kiểm khoá chuyển site được gỡ sau xác nhận; lệnh/API xác nhận chưa được SRS quy định (`Q-ST-07`) |

### 5.5 Mục checklist (DIAG-STATE-QP-CHK-001, states.md §5)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-CHK-01` | `[*]` → `PENDING` | Đủ | 3 | [`TC-SCN-011`](test-cases.md), [`TC-PLAN-009`](test-cases-plan-cmpt.md) (KQ1), [`TC-SCN-102`](test-cases.md) | Mục `OVERLAY` đứng trước `VERSION` |
| `T-CHK-02` | `[*]` → `SKIPPED` | Đủ | 3 | [`TC-SCN-013`](test-cases.md) (KQ1), [`TC-CMPT-021`](test-cases-plan-cmpt.md) (KQ2), [`TC-SCN-102`](test-cases.md) | `applies_when` không thoả; extension `usage_hits = 0` |
| `T-CHK-03` | `PENDING` → `RUNNING` (tạo job) | Đủ | 2 | [`TC-PLAN-017`](test-cases-plan-cmpt.md) (KQ1), [`TC-CLI-018`](test-cases-ptch-cli-rpt.md) (KQ2) | — |
| `T-CHK-04` | `PENDING` → `PENDING` (guard không đạt) | Một phần | 6 | [`TC-SCN-012`](test-cases.md), [`TC-CMPT-020`](test-cases-plan-cmpt.md) (KQ2), [`TC-CON-027`](test-cases-con.md) (KQ1), [`TC-PLAN-018`](test-cases-plan-cmpt.md), [`TC-PLAN-022`](test-cases-plan-cmpt.md) (KQ2), [`TC-PLAN-009`](test-cases-plan-cmpt.md) (KQ2) | Phủ `ERR-SCN-424-01`, `ERR-JOB-428-01`, `ERR-UPG-409-02`, `ERR-PLAN-410-01`; chưa có test case chạy mục khi runtime bị khoá (`ERR-SCN-422-01`) và khi kế hoạch `draft` cho mục không chuyển site (`ERR-PLAN-409-02`) |
| `T-CHK-05` | `RUNNING` → `DONE` | Đủ | 2 | [`TC-PLAN-017`](test-cases-plan-cmpt.md) (KQ2), [`TC-UPG-010`](test-cases-upg.md) (KQ3) | — |
| `T-CHK-06` | `RUNNING` → `DONE` hoặc `FAILED` (job `SUCCEEDED_WITH_ISSUES`) | Một phần | 1 | [`TC-UPG-033`](test-cases-upg.md) (KQ3) | Toàn bộ là `ĐX` (`Q-ST-06`). Có nhánh mục chuyển site có lượt `ROLLED_BACK` → `FAILED`; chưa có nhánh mục khác đánh giá theo `done_criteria` |
| `T-CHK-07` | `RUNNING` → `FAILED` | Đủ | 2 | [`TC-PLAN-017`](test-cases-plan-cmpt.md) (KQ2), [`TC-UPG-033`](test-cases-upg.md) (KQ3) | Nhánh job `INTERRUPTED` → `FAILED` là `ĐX`, chưa kiểm |
| `T-CHK-08` | `RUNNING` → `PENDING` (job `CANCELLED`) | Chưa phủ | 0 | — | Chuyển `ĐX` chờ `Q-ST-06`; bổ sung test case sau khi duyệt |
| `T-CHK-09` | `PENDING`, `RUNNING` → `DONE` (mục `MANUAL`) | Đủ | 3 | [`TC-PLAN-014`](test-cases-plan-cmpt.md), [`TC-PLAN-016`](test-cases-plan-cmpt.md) (dòng 1–2), [`TC-CON-026`](test-cases-con.md) (KQ2) | Biên bằng chứng 9/10 ký tự; nguồn `PENDING` là `ĐX` (`Q-ST-09`) |
| `T-CHK-10` | `PENDING` → `RUNNING` (`start` mục `MANUAL`) | Một phần | 1 | [`TC-PLAN-016`](test-cases-plan-cmpt.md) (dòng 5) | Chỉ có guard âm (phụ thuộc chưa đạt → `ERR-SCN-424-01`); CLI/API chưa có giá trị `start` (`I-ST-05`, `Q-ST-09`) |
| `T-CHK-11` | `PENDING`, `RUNNING` → `FAILED` (mục `MANUAL`) | Chưa phủ | 0 | — | Cần test case bổ sung ở test-cases-plan-cmpt.md: `plan item <plan_id> <chk_id> --set fail` → `FAILED`, ghi lý do và audit |
| `T-CHK-12` | `FAILED` → `RUNNING` (chạy lại) | Chưa phủ | 0 | — | Cần test case bổ sung ở test-cases-plan-cmpt.md: chạy lại mục `FAILED` qua dry-run + xác nhận → `RUNNING`, `job_id` mới, `events.jsonl` giữ lần chạy trước |
| `T-CHK-13` | `DONE` → `FAILED` (rollback thủ công lượt `PASSED`) | Chưa phủ | 0 | — | Chuyển `ĐX` chờ `Q-ST-10`; bổ sung KQ vào `TC-UPG-036` sau khi duyệt |
| `T-CHK-14` | `PENDING`, `FAILED` → `WAIVED` | Một phần | 2 | [`TC-PLAN-016`](test-cases-plan-cmpt.md) (dòng 3–4), [`TC-CON-027`](test-cases-con.md) (KQ2) | Biên lý do 19/20 ký tự từ `PENDING`; nguồn `FAILED` chưa có dòng dữ liệu |
| `T-CHK-15` | `PENDING` → `SKIPPED` (`--set skip`) | Chưa phủ | 0 | — | Cần test case bổ sung ở test-cases-plan-cmpt.md: `applies_when` không thoả → `SKIPPED`; thoả → `ERR-PLAN-409-02` |
| `T-CHK-16` | Mục kết thúc hoặc kế hoạch kết thúc → không đổi | Đủ | 2 | [`TC-PLAN-015`](test-cases-plan-cmpt.md), [`TC-CLI-017`](test-cases-ptch-cli-rpt.md) | `ERR-PLAN-409-02`, `ERR-PLAN-404-01` |

### 5.6 Bundle dữ liệu feed (DIAG-STATE-QP-FEED-001, states.md §6.1)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-FD-01` | `[*]` → `NO_BUNDLE` | Đủ | 3 | [`TC-FEED-035`](test-cases-feed.md), [`TC-FEED-036`](test-cases-feed.md), [`TC-FEED-050`](test-cases-feed.md) (dòng không có bundle) | Tiền điều kiện máy mới cài, chưa có `feeds/current/` |
| `T-FD-02` | `NO_BUNDLE` → mức theo tuổi snapshot | Đủ | 1 | [`TC-FEED-035`](test-cases-feed.md) | Giải nén ≤ 10 s, `data_origin = SNAPSHOT` |
| `T-FD-03` | `NO_BUNDLE` → mức theo dữ liệu vừa lấy (snapshot sai, có mạng) | Chưa phủ | 0 | — | `TC-FEED-036` chỉ có nhánh không có mạng. Cần test case bổ sung ở test-cases-feed.md: snapshot sai SHA-256, có mạng → đồng bộ đầy đủ ≤ 900 s |
| `T-FD-04` | `NO_BUNDLE` → `NO_BUNDLE` | Đủ | 1 | [`TC-FEED-036`](test-cases-feed.md) | `ERR-FEED-422-02`, runtime `UNKNOWN`, `ERR-FEED-503-01`, thoát 2 |
| `T-FD-05` | `FRESH` → `AGING` | Đủ | 2 | [`TC-FEED-029`](test-cases-feed.md), [`TC-FEED-031`](test-cases-feed.md) (dòng 6/7 giờ) | — |
| `T-FD-06` | `AGING` → `STALE` | Đủ | 3 | [`TC-FEED-030`](test-cases-feed.md), [`TC-FEED-031`](test-cases-feed.md) (dòng 168/169 giờ), [`TC-FEED-102`](test-cases-feed.md) (dòng 31, 90 ngày) | `ERR-FEED-412-01` |
| `T-FD-07` | `STALE` → `EXPIRED` | Đủ | 4 | [`TC-FEED-031`](test-cases-feed.md) (dòng 2.161 giờ), [`TC-FEED-050`](test-cases-feed.md), [`TC-FEED-102`](test-cases-feed.md) (dòng 91 ngày), [`TC-SCN-006`](test-cases.md) | `ERR-SCN-503-01`, chỉ vá cùng nhánh |
| `T-FD-08` | Bundle → mức theo tuổi bundle mới (`feeds update`) | Đủ | 3 | [`TC-FEED-001`](test-cases-feed.md), [`TC-FEED-032`](test-cases-feed.md), [`TC-CON-038`](test-cases-con.md) (KQ2) | — |
| `T-FD-09` | Bundle → không đổi (`feeds update` lỗi) | Đủ | 4 | [`TC-FEED-003`](test-cases-feed.md), [`TC-FEED-004`](test-cases-feed.md), [`TC-FEED-033`](test-cases-feed.md), [`TC-FEED-104`](test-cases-feed.md) | Đủ 5 mã: `ERR-FEED-423-01`, `ERR-FEED-507-01`, `ERR-FEED-424-01`, `ERR-FEED-504-01`, `ERR-FEED-422-02` |
| `T-FD-10` | Bundle → mức theo tuổi snapshot (`feeds import`) | Đủ | 5 | [`TC-FEED-039`](test-cases-feed.md), [`TC-FEED-040`](test-cases-feed.md), [`TC-FEED-041`](test-cases-feed.md), [`TC-CON-039`](test-cases-con.md), [`TC-CON-040`](test-cases-con.md) | Nhánh từ chối `ERR-FEED-422-02`, `ERR-FEED-409-02` |
| `T-FD-11` | Bundle → mức theo tuổi snapshot đóng gói mới hơn | Đủ | 1 | [`TC-FEED-037`](test-cases-feed.md) | Biên 2 `generated_at` bằng nhau |
| `T-FD-12` | Bundle → dựng lại (`feeds verify` lệch) | Đủ | 1 | [`TC-FEED-049`](test-cases-feed.md) | — |

### 5.7 Trạng thái nguồn dữ liệu (DIAG-STATE-QP-FEED-002, states.md §6.2)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-SRC-01` | → `DISABLED` | Một phần | 2 | [`TC-FEED-053`](test-cases-feed.md) (KQ1), [`TC-FEED-031`](test-cases-feed.md) | Có nhánh nguồn cần key bị bỏ qua key do file quyền rộng; chưa có test case cấu hình `enabled=0` từ `OK`/`DEGRADED`/`FAILED` |
| `T-SRC-02` | → `OK` | Đủ | 4 | [`TC-FEED-001`](test-cases-feed.md), [`TC-FEED-019`](test-cases-feed.md) (dòng HTTP 304), [`TC-FEED-051`](test-cases-feed.md) (KQ1), [`TC-FEED-103`](test-cases-feed.md) (KQ1) | — |
| `T-SRC-03` | → `DEGRADED` (lỗi, đã có `last_ok_at`) | Chưa phủ | 0 | — | Chuyển `ĐX` chờ `Q-ST-11`. `TC-FEED-103` KQ3 giữ dữ liệu cũ của SRC-009 nhưng mong đợi `FAILED`, trái tiêu chí `ĐX`; đối chiếu lại test case khi `Q-ST-11` được duyệt |
| `T-SRC-04` | → `FAILED` (lỗi, `last_ok_at = null`) | Một phần | 2 | [`TC-FEED-002`](test-cases-feed.md) (KQ1), [`TC-FEED-103`](test-cases-feed.md) (KQ3–KQ4) | Kiểm `FAILED` sau 3 lần thử; tiền điều kiện chưa nêu `last_ok_at = null` (tiêu chí `ĐX`, `Q-ST-11`) |
| `T-SRC-05` | `DEGRADED`, `FAILED` → `OK` (`--force --accept-shrink`) | Đủ | 1 | [`TC-FEED-006`](test-cases-feed.md) (KQ3) | Ghi audit |

### 5.8 Tiến trình serve và token (DIAG-STATE-QP-CON-001, states.md §7.1)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-CON-01` | `[*]` → `STARTING` | Đủ | 1 | [`TC-CON-001`](test-cases-con.md) | — |
| `T-CON-02` | `STARTING` → `STOPPED` | Đủ | 4 | [`TC-CON-002`](test-cases-con.md) (KQ1, KQ3), [`TC-CON-003`](test-cases-con.md), [`TC-CON-004`](test-cases-con.md) (KQ1), [`TC-CON-013`](test-cases-con.md) (KQ2) | Đủ 5 nhánh: `ERR-CON-424-01`, `ERR-CON-412-01`, `ERR-CON-409-01`, `ERR-CON-409-02`, `ERR-CLI-400-01` |
| `T-CON-03` | `STARTING` → `LISTENING` | Đủ | 3 | [`TC-CON-001`](test-cases-con.md), [`TC-CON-002`](test-cases-con.md) (KQ2), [`TC-CON-004`](test-cases-con.md) (KQ1) | Bind `127.0.0.1`, `--replace`, `--token-file` |
| `T-CON-04` | `LOGIN_OPEN` → `LOGIN_THROTTLED` | Đủ | 1 | [`TC-CON-006`](test-cases-con.md) (KQ1) | `ERR-AUTH-429-01` |
| `T-CON-05` | `LOGIN_THROTTLED` → `LOGIN_OPEN` | Một phần | 1 | [`TC-CON-006`](test-cases-con.md) (KQ2) | Chỉ kiểm còn khoá trước 60 s; chưa có bước gửi token đúng sau 60 s nhận 200 (bổ sung KQ vào `TC-CON-006`) |
| `T-CON-06` | `LISTENING` → `STOPPING` | Đủ | 3 | [`TC-CON-004`](test-cases-con.md) (KQ2), [`TC-CON-002`](test-cases-con.md) (KQ2), [`TC-CON-059`](test-cases-con.md) (KQ2) | `serve --stop`, `--replace`; request mới nhận `ERR-CON-503-01` |
| `T-CON-07` | `STOPPING` → `STOPPING` (còn job ghi) | Đủ | 1 | [`TC-CON-004`](test-cases-con.md) (KQ2) | `ERR-CON-409-03`. Xử lý job `QUEUED`, `read`/`data` khi dừng là `ĐX` (`Q-ST-01`), chưa kiểm |
| `T-CON-08` | `STOPPING` → `STOPPED` | Đủ | 1 | [`TC-CON-004`](test-cases-con.md) (KQ2) | Xoá `--token-file` khi dừng |

### 5.9 Phiên trình duyệt (DIAG-STATE-QP-AUTH-001, states.md §7.2)
| Mã | Chuyển trạng thái | Mức phủ | Số TC | Test case | Ghi chú |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `T-SES-01` | `[*]` → `ACTIVE` | Đủ | 1 | [`TC-CON-005`](test-cases-con.md) | — |
| `T-SES-02` | `[*]` → không tạo | Đủ | 3 | [`TC-CON-006`](test-cases-con.md), [`TC-CON-007`](test-cases-con.md) (KQ1), [`TC-CON-012`](test-cases-con.md) (KQ1) | `ERR-AUTH-401-01`, `ERR-AUTH-429-01`, `ERR-AUTH-409-01`, `ERR-CON-421-01` |
| `T-SES-03` | `ACTIVE` → `ACTIVE` | Đủ | 4 | [`TC-CON-008`](test-cases-con.md) (KQ1), [`TC-CON-010`](test-cases-con.md) (dòng 1), [`TC-CON-014`](test-cases-con.md), [`TC-CON-015`](test-cases-con.md) | Request ghi sai CSRF/Origin bị từ chối, phiên giữ nguyên |
| `T-SES-04` | `ACTIVE` → `EXPIRED` | Đủ | 1 | [`TC-CON-010`](test-cases-con.md) (dòng 2–3) | `ERR-AUTH-401-02` lý do `idle`, `absolute` |
| `T-SES-05` | `ACTIVE` → `REVOKED` | Đủ | 1 | [`TC-CON-010`](test-cases-con.md) (dòng 4) | Cookie cũ sau `serve --stop` rồi `serve` lại |
| `T-SES-06` | `ACTIVE` → `LOGGED_OUT` | Đủ | 1 | [`TC-CON-008`](test-cases-con.md) (KQ2) | — |
| `T-SES-07` | `EXPIRED`, `LOGGED_OUT`, `REVOKED` → không đổi | Đủ | 2 | [`TC-CON-008`](test-cases-con.md) (KQ2), [`TC-CON-010`](test-cases-con.md) (dòng 4) | `ERR-AUTH-401-01` |

### 5.10 Việc cần làm ở tài liệu khác
Tài liệu này chỉ ghi truy vết; test case và chỉ số tổng do file chủ cập nhật.

| # | Tài liệu | Việc cần làm | Căn cứ |
| :--- | :--- | :--- | :--- |
| 1 | [test-cases.md](test-cases.md) §4.2 | Dòng BR: 200 mã, 200 có test case (100%); dòng ERR: 129 mã của error-matrix v1.1.0, 129 có test case ghi mã (100%); dòng NFR: 60 mã, 55 liên kết qua story, 5 liên kết trực tiếp (§4.1); thêm dòng "Chuyển trạng thái `T-*`": 97 mã, 83 có ≥ 1 test case (85,6%, đánh giá trên 404 test case), dẫn tới §5; §3 và §4.1 tổng 421 test case (`PTCH`/`CLI`/`RPT` 74, `UPG` 60, `CON` 63, `JOB`/`FLT` 42); frontmatter `related_diagrams` đổi DIAG-STATE-QP-JOB-001, -PLAN-001, -ENV-002 sang mã chi tiết DIAG-STATE-QP-JOB-002, -PLAN-002, -ENV-003 | §3, §5.1; states.md `I-ST-07` (5) |
| 2 | test-cases-job-flt.md, test-cases-plan-cmpt.md, test-cases-upg.md, test-cases-feed.md | Thêm test case cho 10 mã chưa phủ không gắn `ĐX`: `T-JOB-13`, `T-SW-04` (job-flt); `T-PLN-11`, `T-CHK-11`, `T-CHK-12`, `T-CHK-15` (plan-cmpt); `T-SW-07`, `T-SW-10`, `T-SW-14` sau CR `Q-ST-05` (upg); `T-FD-03` (feed); bổ sung dòng dữ liệu/KQ cho 14 mã "Một phần"; ghi mã `T-*` vào cột "BR / ERR kiểm" | §5.2–§5.9 |
| 3 | [test-cases-feed.md](test-cases-feed.md) | Đã xong ở test-cases-feed.md v1.0.1: `TC-FEED-002` KQ1 (SRC-008) và `TC-FEED-024` KQ1 (SRC-015) ghi `ERR-FEED-503-03` | §3 dòng `ERR-FEED-503-03` |
| 4 | [test-cases-upg.md](test-cases-upg.md) | Đã xong ở test-cases-upg.md v1.0.2: `TC-UPG-109` phủ `ERR-HC-412-04` | §3 dòng `ERR-HC-412-04` |
| 5 | [test-cases-job-flt.md](test-cases-job-flt.md) | Đã xong ở test-cases-job-flt.md v1.0.2 theo cách khác: `TC-JOB-018` sinh lại chỉ còn hành vi `Last-Event-ID`, giới hạn luồng SSE chuyển sang `TC-JOB-025` (429 `ERR-JOB-429-02`) | §3 dòng `ERR-JOB-429-02` |
| 6 | [rtm.md](rtm.md) | RTM (FR ↔ TC, không có cột ERR) đối chiếu 17 test case thêm sau bản 1.0.1 của tài liệu này (§1) với bản hiện hành của rtm.md, thêm dòng còn thiếu (trong đó `FR-UPG-ACK-001` ↔ `TC-UPG-111`) và sửa tổng thành 421 test case | §1, §4.1 mục 5 |
| 7 | [states.md](../srs/states.md) | `T-SW-02` thay "mã lỗi chưa định nghĩa" bằng `ERR-UPG-409-03`; ma trận §6.2 chưa có chuyển nguồn tùy chọn → `DISABLED` khi key bị từ chối, trong khi error-matrix (`ERR-FEED-401-01`: "nguồn tùy chọn tự tắt") và `TC-FEED-052` KQ1 mong đợi tự tắt, còn `T-SRC-03`/`T-SRC-04` đưa về `DEGRADED`/`FAILED` | error-matrix v1.0.1 §3, §4.2 |

## 6. Tài liệu tham chiếu (References)
- [test-cases.md](test-cases.md) (DOC-TC-QP-000) và 6 file test case tách; bản đọc lại ở 1.0.2 của tài liệu này: [test-cases-ptch-cli-rpt.md](test-cases-ptch-cli-rpt.md) v1.0.1 (74 TC), [test-cases-upg.md](test-cases-upg.md) v1.0.2 (60 TC), [test-cases-job-flt.md](test-cases-job-flt.md) v1.0.2 (42 TC), [test-cases-feed.md](test-cases-feed.md) v1.0.1 (60 TC), [test-cases-con.md](test-cases-con.md) v1.0.1 (63 TC), [test-cases-plan-cmpt.md](test-cases-plan-cmpt.md) v1.0.0 (61 TC), test-cases.md v1.0.1 (61 TC)
- [business-rules.md](../srs/business-rules.md) (DOC-SRS-QP-BR-001) v1.0.1 — `BR-AUD-006` (Neo chuỗi hash), và phụ lục BR (`SCN`, `FEED`, `ENV`, `HC`); [environment-playbooks.md](../srs/environment-playbooks.md) (DOC-SRS-QP-ENV-001) v1.0.1 — `BR-ENV-013` (Chặn lệnh ghi khi đang có lượt chuyển)
- [error-matrix.md](../srs/error-matrix.md) (DOC-SRS-QP-ERR-001) v1.1.0 — 129 mã; §2.1 (số mã theo module, trạng thái đề xuất của `ERR-PTCH-409-01`, `ERR-PTCH-500-01`, `ERR-UPG-409-04`), §5 mục 4–5 (3 mã đưa vào ma trận, 2 mã tách mức độ), §5 mục 7 (4 mã thêm ở bản 1.1.0)
- [nfr.md](../srs/nfr.md) (DOC-SRS-QP-NFR-001) v1.0.1 — 60 NFR; `NFR-CMP-003` (Python 3.6–3.14, trình duyệt), `NFR-MNT-003`, `NFR-MNT-004`; [data-sources.md](../srs/data-sources.md) §6 — cách kiểm `NFR-FEED-002` (nguồn giả lập trả chậm 300 s) và `NFR-FEED-007` (chặn từng host bằng `/etc/hosts` và tổ hợp chặn toàn bộ)
- [rtm.md](rtm.md) (DOC-RTM-QP-001) v1.0.2 §2, §2.1 mục 1 — trạng thái `NFR-MNT-004` (141/142 FR P0, thiếu `FR-UPG-ACK-001`); [backlog.md](../userstories/backlog.md) (DOC-US-QP-001) v1.0.1 — bảng phân lớp phát hành (điều kiện `NFR-MNT-004`)
- [states.md](../srs/states.md) (DOC-SRS-QP-STATE-001) v1.0.1 — 97 mã `T-*` ở §2.2, §3.2, §4.2, §5.2, §6.1, §6.2, §7.1, §7.2; câu hỏi mở `Q-ST-01`..`Q-ST-13` và điểm lệch `I-ST-01`..`I-ST-07` ở §9
- [data-sources.md](../srs/data-sources.md) (DOC-SRS-QP-FEED-001) §3.1 — vai trò nguồn (Chính/Phụ/Dự phòng/Tùy chọn) dùng để xác định test case của `ERR-FEED-503-03`
- OpenBA-Kit `skills/test-cases/SKILL.md` bước 3: 100% mã `ERR-*` và `BR-*` có test case; `rules/12-state-transition-rules.md` §2 (ma trận chuyển trạng thái), `rules/14-test-case-traceability.md`
