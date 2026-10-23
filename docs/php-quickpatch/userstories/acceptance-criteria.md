---
id: DOC-AC-QP-000
title: Tiêu chí chấp nhận (Acceptance Criteria) — php-quickpatch v2 — chỉ mục, SCAN, SCN, ASMT
version: 1.0.1
phase: User Story
domain: Security Patch Management
tags: [acceptance-criteria, gherkin, bdd, scan, scenario, assessment, php, nodejs, openba]
depends_on:
  - DOC-US-QP-001
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-FEED-002
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-SCN-000
related_diagrams:
  - DIAG-FLOW-QP-ENV-001
author: BA Agent
last_updated: 2026-10-22
---

# Tiêu chí chấp nhận (Acceptance Criteria) — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo 372 scenario Gherkin cho 120 user story của [backlog.md](backlog.md) theo `skills/ac`, template 28, rules 08, 16, 18, 19; tách 7 file do giới hạn 800 dòng; file này chứa quy ước, chỉ mục và AC của module SCAN, SCN, ASMT |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: (1) thêm `AC-JOB-25` vào dòng `US-JOB-06` của chỉ mục §3 (scenario tách từ `AC-JOB-18` ở [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) v1.0.1); thêm cột số scenario theo file ở §2, tổng 373 scenario (bản 1.0.0 ghi 372), đếm lại bằng tag `@AC-*` của 7 file. (2) Sửa quy ước §1.1 cho khớp rule 08: mọi story có ≥ 1 `@happy-path`, ≥ 1 `@negative`, ≥ 1 `@boundary`; `@security` là loại bổ sung, không thay `@boundary`; 1 scenario được mang đồng thời `@security @boundary`. Thêm §1.3 liệt kê 26 story ở 6 file tách chưa có `@boundary` (16 story của file này đã đạt) kèm hướng xử lý: gắn thêm `@boundary` cho 9 scenario `@security` đã kiểm giới hạn số/thời gian, bổ sung scenario `@boundary` mới cho 17 story còn lại. Việc này cần làm ở các file tách, không làm trong file này |

## 1. Quy ước

### 1.1 Cấu trúc
- Mỗi story là 1 `Feature`; mỗi scenario mang 1 tag mã `@AC-[MODULE]-NN` và 1 hoặc 2 tag loại: `@happy-path`, `@negative` (lỗi nghiệp vụ có mã `ERR-*`), `@boundary` (biên/giới hạn số, ngưỡng thời gian), `@security` (bảo mật). Theo rule 08, mọi story có ≥ 1 `@happy-path`, ≥ 1 `@negative` và ≥ 1 `@boundary`; `@security` là loại bổ sung, không thay được `@boundary`. Scenario bảo mật kiểm tra giá trị tại hoặc ngay ngoài 1 giới hạn số hoặc thời gian mang đồng thời `@security @boundary`.
- Từ khoá Gherkin giữ tiếng Anh (`Feature`, `Scenario`, `Given`, `When`, `Then`, `And`); nội dung tiếng Việt; tên lệnh, trường JSON, mã lỗi giữ nguyên.
- Dòng "Tham chiếu" dưới tiêu đề story liệt kê FR, BR, ERR, NFR, màn hình liên quan; scenario chỉ dùng mã có trong registry của SRS.
- Ngày tham chiếu dữ liệu: bundle ngày 2026-10-22 (UTC) và các ví dụ tính ở DOC-SRS-QP-FEED-002 §8.5 trừ khi scenario ghi ngày khác. Tên site, package, mã advisory dạng `GHSA-test-…`, đường dẫn `/srv/test/…` là **dữ liệu kiểm thử**, không phải dữ liệu thật.

### 1.2 Ký hiệu dùng chung trong `Given`
| Ký hiệu | Nghĩa |
| :--- | :--- |
| "máy kiểm thử chuẩn" | VPS 2 vCPU / 2 GB RAM, Ubuntu 24.04, Bash 5.2, Python 3.12, `flock`, `curl`, chạy root, `STATE_DIR=/var/lib/php-quickpatch` |
| "bundle mẫu 2026-10-22" | `feeds/current/` dựng từ raw cache cố định ngày 2026-10-22 (`bundle_id` `b-20261022T093000Z-3f2a9c1e`, `catalog_version` `2026.10.20-1`), `data_age_h` ≤ 6 |
| "phiên console hợp lệ" | Đã đăng nhập theo `AC-CON-05`, có cookie `qp_session` và CSRF token, `serve` chạy root trên cổng 17321 |
| `php:3f2a9c1e0b7d` | `runtime_id` mẫu (dữ liệu kiểm thử) của runtime PHP 8.2.34 dùng xuyên suốt các file AC |
| "dry-run hợp lệ" | Job `dry_run=true` cùng tham số chuẩn hoá, cùng phiên, `SUCCEEDED`, tạo ≤ 15 phút trước, `bundle_id` và `scan_fingerprint` không đổi (`BR-CON-005`) |

### 1.3 Story chưa có `@boundary` (cần sửa ở file tách)
Kiểm tra ngày 2026-10-22 bằng cách đếm tag loại theo `Feature` trên 7 file: cả 120 story có `@happy-path` và `@negative`; 94 story có `@boundary`, gồm 16/16 story của file này. 26 story dưới đây chỉ có 1 scenario `@security` ở vị trí scenario thứ 3, chưa đạt rule 08. Hướng xử lý: (a) gắn thêm `@boundary` cho scenario đã kiểm giới hạn số/thời gian, giữ nguyên mã AC; (b) bổ sung 1 scenario `@boundary` mới, đánh số tiếp theo số lớn nhất của module (như `AC-JOB-25`), rồi cập nhật chỉ mục §3 và tổng ở §2.

| File | (a) Gắn thêm `@boundary` — giới hạn đã kiểm | (b) Story cần scenario `@boundary` mới |
| :--- | :--- | :--- |
| [acceptance-criteria-con.md](acceptance-criteria-con.md) | `AC-CON-04` (`US-CON-01`, cổng 1023/32767/32768); `AC-CON-07` (`US-CON-02`, phiên thứ 6 khi giới hạn 5); `AC-CON-13` (`US-CON-04`, `--allow-local-port` lần 4 khi tối đa 3, `BR-CON-003`); `AC-CON-57` (`US-CON-18`, fuzz 1.000 giá trị, chuỗi 300 ký tự) | `US-CON-05`, `US-CON-07`, `US-CON-11`, `US-CON-15`, `US-CON-16`, `US-CON-17` |
| [acceptance-criteria-feed.md](acceptance-criteria-feed.md) | `AC-FEED-22` (`US-FEED-07`, TTL cache 6 giờ: 13:59/14:01); `AC-FEED-41` (`US-FEED-13`, 51 MB/50 MB, +61/+60 phút) | `US-FEED-03`, `US-FEED-17` |
| [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) | `AC-JOB-24` (`US-JOB-08`, xoá bản ghi cuối tháng 10, phát hiện ở bản ghi đầu tháng 11); `AC-FLT-03` (`US-FLT-01`, timeout 10 s; nên đổi port 70000 thành 65536 để kiểm ngay ngoài dải 1–65535); `AC-FLT-09` (`US-FLT-03`, tỉ lệ lỗi 20% bằng ngưỡng) | `US-FLT-05` |
| [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) | — | `US-CMPT-01`, `US-CMPT-05`, `US-CMPT-11` |
| [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) | — | `US-PTCH-04`, `US-PTCH-05`, `US-CLI-01`, `US-RPT-01` |
| [acceptance-criteria-upg.md](acceptance-criteria-upg.md) | — | `US-UPG-14` |

## 2. Bộ tài liệu AC (tách file ≤ 800 dòng)
| File | Module | Story | Số scenario |
| :--- | :--- | :--- | ---: |
| [acceptance-criteria.md](acceptance-criteria.md) (tài liệu này) | `SCAN`, `SCN`, `ASMT` | `US-SCAN-01..05`, `US-SCN-01..05`, `US-ASMT-01..06` | 50 |
| [acceptance-criteria-feed.md](acceptance-criteria-feed.md) | `FEED` | `US-FEED-01..17` | 53 |
| [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) | `PLAN`, `CMPT` | `US-PLAN-01..08`, `US-CMPT-01..11` | 59 |
| [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) | `PTCH`, `CLI`, `RPT` | `US-PTCH-01..09`, `US-CLI-01..10`, `US-RPT-01..02` | 64 |
| [acceptance-criteria-upg.md](acceptance-criteria-upg.md) | `UPG` | `US-UPG-01..15` | 47 |
| [acceptance-criteria-con.md](acceptance-criteria-con.md) | `CON` | `US-CON-01..19` | 60 |
| [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) | `JOB`, `FLT` | `US-JOB-01..08`, `US-FLT-01..05` | 40 |
| **Tổng** | 13 module | 120 story | **373** |

## 3. Chỉ mục story → mã AC
| Story ID | Tên ngắn | Ưu tiên | Mã AC | File |
| :--- | :--- | :---: | :--- | :--- |
| `US-SCAN-01` | Nhận diện môi trường và kiểm kê site → runtime | P0 | `AC-SCAN-01`, `AC-SCAN-02`, `AC-SCAN-03` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCAN-02` | Phát hiện runtime PHP và Node.js | P0 | `AC-SCAN-04`, `AC-SCAN-05`, `AC-SCAN-06` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCAN-03` | Kiểm kê dự án và container | P0 | `AC-SCAN-07`, `AC-SCAN-08`, `AC-SCAN-09` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCAN-04` | Phát hiện webshell chỉ báo cáo | P0 | `AC-SCAN-10`, `AC-SCAN-11`, `AC-SCAN-12` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCAN-05` | Cảnh báo gán site bị đổi ngoài tool | P1 | `AC-SCAN-13`, `AC-SCAN-14`, `AC-SCAN-15` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCN-01` | Gán kịch bản và khoá phiên bản bất thường | P0 | `AC-SCN-01`, `AC-SCN-02`, `AC-SCN-03`, `AC-SCN-04` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCN-02` | Trạng thái hỗ trợ và mức ưu tiên động | P0 | `AC-SCN-05`, `AC-SCN-06`, `AC-SCN-07` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCN-03` | Nạp và cập nhật catalog | P0 | `AC-SCN-08`, `AC-SCN-09`, `AC-SCN-10` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCN-04` | Lắp checklist hiệu lực | P0 | `AC-SCN-11`, `AC-SCN-12`, `AC-SCN-13` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-SCN-05` | Giới hạn thao tác theo môi trường đặc biệt | P0 | `AC-SCN-14`, `AC-SCN-15`, `AC-SCN-16` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-FEED-01` | Đồng bộ thủ công bằng feeds update | P0 | `AC-FEED-01`, `AC-FEED-02`, `AC-FEED-03`, `AC-FEED-04` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-02` | Đồng bộ vòng đời và ma trận framework | P0 | `AC-FEED-05`, `AC-FEED-06`, `AC-FEED-07` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-03` | Đồng bộ bản phát hành | P0 | `AC-FEED-08`, `AC-FEED-09`, `AC-FEED-10` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-04` | Đồng bộ CVE PHP core | P0 | `AC-FEED-11`, `AC-FEED-12`, `AC-FEED-13` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-05` | Đồng bộ CVE Node.js và WordPress core | P0 | `AC-FEED-14`, `AC-FEED-15`, `AC-FEED-16` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-06` | Gắn cờ CISA KEV | P0 | `AC-FEED-17`, `AC-FEED-18`, `AC-FEED-19` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-07` | Tra OSV Composer/npm có cache | P0 | `AC-FEED-20`, `AC-FEED-21`, `AC-FEED-22` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-08` | Xác định bản vá backport của gói distro | P0 | `AC-FEED-23`, `AC-FEED-24`, `AC-FEED-25` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-09` | Chuẩn hoá advisory và tính min_patched | P0 | `AC-FEED-26`, `AC-FEED-27`, `AC-FEED-28` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-10` | Gắn tuổi dữ liệu vào mọi kết quả | P0 | `AC-FEED-29`, `AC-FEED-30`, `AC-FEED-31` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-11` | Cache gốc và thay bundle nguyên tử | P0 | `AC-FEED-32`, `AC-FEED-33`, `AC-FEED-34` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-12` | Khởi tạo dữ liệu từ snapshot đóng gói | P0 | `AC-FEED-35`, `AC-FEED-36`, `AC-FEED-37` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-13` | Xuất/nhập snapshot offline | P0 | `AC-FEED-38`, `AC-FEED-39`, `AC-FEED-40`, `AC-FEED-41` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-14` | Dựng snapshot khi phát hành | P0 | `AC-FEED-42`, `AC-FEED-43`, `AC-FEED-44` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-15` | Lịch đồng bộ định kỳ | P1 | `AC-FEED-45`, `AC-FEED-46`, `AC-FEED-47` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-16` | Trạng thái nguồn và kiểm toàn vẹn bundle | P0 | `AC-FEED-48`, `AC-FEED-49`, `AC-FEED-50` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-FEED-17` | Nguồn lỗ hổng WordPress cần key | P2 | `AC-FEED-51`, `AC-FEED-52`, `AC-FEED-53` | [acceptance-criteria-feed.md](acceptance-criteria-feed.md) |
| `US-ASMT-01` | Đánh giá runtime hiện tại và điểm rủi ro | P0 | `AC-ASMT-01`, `AC-ASMT-02`, `AC-ASMT-03`, `AC-ASMT-04` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-ASMT-02` | Phiên bản ứng viên và khả năng cài | P0 | `AC-ASMT-05`, `AC-ASMT-06`, `AC-ASMT-07` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-ASMT-03` | So sánh hiện tại với ứng viên | P0 | `AC-ASMT-08`, `AC-ASMT-09`, `AC-ASMT-10` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-ASMT-04` | Xếp hạng ưu tiên xử lý | P0 | `AC-ASMT-11`, `AC-ASMT-12`, `AC-ASMT-13` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-ASMT-05` | Đánh giá dependency Composer/npm | P0 | `AC-ASMT-14`, `AC-ASMT-15`, `AC-ASMT-16` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-ASMT-06` | Đánh giá WordPress core | P0 | `AC-ASMT-17`, `AC-ASMT-18`, `AC-ASMT-19` | [acceptance-criteria.md](acceptance-criteria.md) |
| `US-PLAN-01` | Chọn phiên bản đích | P0 | `AC-PLAN-01`, `AC-PLAN-02`, `AC-PLAN-03`, `AC-PLAN-04` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-02` | Sinh kế hoạch nâng cấp | P0 | `AC-PLAN-05`, `AC-PLAN-06`, `AC-PLAN-07` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-03` | Thứ tự chuyển site và site canary | P0 | `AC-PLAN-08`, `AC-PLAN-09`, `AC-PLAN-10` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-04` | Danh sách dependency phải nâng | P0 | `AC-PLAN-11`, `AC-PLAN-12`, `AC-PLAN-13` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-05` | Cập nhật trạng thái mục checklist | P0 | `AC-PLAN-14`, `AC-PLAN-15`, `AC-PLAN-16` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-06` | Chạy mục checklist AUTO/SEMI | P0 | `AC-PLAN-17`, `AC-PLAN-18`, `AC-PLAN-19` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-07` | Vòng đời và duyệt kế hoạch | P0 | `AC-PLAN-20`, `AC-PLAN-21`, `AC-PLAN-22`, `AC-PLAN-23` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PLAN-08` | Theo dõi hạn duyệt kế hoạch | P0 | `AC-PLAN-24`, `AC-PLAN-25`, `AC-PLAN-26` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-01` | Công cụ quét cố định phiên bản | P0 | `AC-CMPT-01`, `AC-CMPT-02`, `AC-CMPT-03` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-02` | Quét luật breaking change tĩnh | P0 | `AC-CMPT-04`, `AC-CMPT-05`, `AC-CMPT-06` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-03` | Quét PHPCompatibility | P0 | `AC-CMPT-07`, `AC-CMPT-08`, `AC-CMPT-09` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-04` | Kiểm tra cú pháp bằng binary đích | P0 | `AC-CMPT-10`, `AC-CMPT-11`, `AC-CMPT-12` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-05` | Composer platform và Packagist | P0 | `AC-CMPT-13`, `AC-CMPT-14`, `AC-CMPT-15` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-06` | engines.node và native addon | P1 | `AC-CMPT-16`, `AC-CMPT-17`, `AC-CMPT-18` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-07` | Directive ini và extension | P0 | `AC-CMPT-19`, `AC-CMPT-20`, `AC-CMPT-21` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-08` | Loader mã hoá | P0 | `AC-CMPT-22`, `AC-CMPT-23`, `AC-CMPT-24` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-09` | Framework/CMS và ma trận PHP | P1 | `AC-CMPT-25`, `AC-CMPT-26`, `AC-CMPT-27` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-10` | Kết luận tương thích theo site | P0 | `AC-CMPT-28`, `AC-CMPT-29`, `AC-CMPT-30` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-CMPT-11` | Rector tuỳ chọn trên bản sao | P2 | `AC-CMPT-31`, `AC-CMPT-32`, `AC-CMPT-33` | [acceptance-criteria-plan-cmpt.md](acceptance-criteria-plan-cmpt.md) |
| `US-PTCH-01` | Vá PHP cùng nhánh | P0 | `AC-PTCH-01`, `AC-PTCH-02`, `AC-PTCH-03`, `AC-PTCH-04` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-02` | Mitigation ini tạm thời | P0 | `AC-PTCH-05`, `AC-PTCH-06`, `AC-PTCH-07` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-03` | Vá Node.js cùng major | P0 | `AC-PTCH-08`, `AC-PTCH-09`, `AC-PTCH-10` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-04` | Vá package Composer/npm | P0 | `AC-PTCH-11`, `AC-PTCH-12`, `AC-PTCH-13` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-05` | Cập nhật WordPress và kiểm toàn vẹn | P0 | `AC-PTCH-14`, `AC-PTCH-15`, `AC-PTCH-16` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-06` | Tag image Docker và mitigation container | P0 | `AC-PTCH-17`, `AC-PTCH-18`, `AC-PTCH-19` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-07` | Restart dịch vụ sau vá | P0 | `AC-PTCH-20`, `AC-PTCH-21`, `AC-PTCH-22` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-08` | Backup manifest theo lượt | P0 | `AC-PTCH-23`, `AC-PTCH-24`, `AC-PTCH-25` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-PTCH-09` | Rollback một lượt chạy | P0 | `AC-PTCH-26`, `AC-PTCH-27`, `AC-PTCH-28` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-UPG-01` | Tiền điều kiện cài song song | P0 | `AC-UPG-01`, `AC-UPG-02`, `AC-UPG-03` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-02` | Cài runtime đích song song | P0 | `AC-UPG-04`, `AC-UPG-05`, `AC-UPG-06` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-03` | Pool/handler đích và cấu hình | P0 | `AC-UPG-07`, `AC-UPG-08`, `AC-UPG-09` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-04` | Chuyển 1 site (C1–C12) | P0 | `AC-UPG-10`, `AC-UPG-11`, `AC-UPG-12`, `AC-UPG-13` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-05` | Chuyển site qua API panel | P0 | `AC-UPG-14`, `AC-UPG-15`, `AC-UPG-16` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-06` | Chuyển mod_php sang PHP-FPM | P0 | `AC-UPG-17`, `AC-UPG-18`, `AC-UPG-19` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-07` | Điều phối chuyển site theo kế hoạch | P0 | `AC-UPG-20`, `AC-UPG-21`, `AC-UPG-22`, `AC-UPG-23` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-08` | Tập URL thăm dò và baseline | P0 | `AC-UPG-24`, `AC-UPG-25`, `AC-UPG-26` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-09` | FastCGI probe trước chuyển | P0 | `AC-UPG-27`, `AC-UPG-28`, `AC-UPG-29` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-10` | Cửa sổ health check và báo cáo | P0 | `AC-UPG-30`, `AC-UPG-31`, `AC-UPG-32` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-11` | Tự rollback khi health check không đạt | P0 | `AC-UPG-33`, `AC-UPG-34`, `AC-UPG-35` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-12` | Rollback 1 site bằng 1 lệnh | P0 | `AC-UPG-36`, `AC-UPG-37`, `AC-UPG-38` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-13` | Chuyển ứng dụng Node.js | P1 | `AC-UPG-39`, `AC-UPG-40`, `AC-UPG-41` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-14` | Chuyển dịch vụ Compose | P1 | `AC-UPG-42`, `AC-UPG-43`, `AC-UPG-44` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-UPG-15` | Gỡ runtime cũ không còn dùng | P2 | `AC-UPG-45`, `AC-UPG-46`, `AC-UPG-47` | [acceptance-criteria-upg.md](acceptance-criteria-upg.md) |
| `US-CON-01` | Khởi động serve và token 1 lần | P0 | `AC-CON-01`, `AC-CON-02`, `AC-CON-03`, `AC-CON-04` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-02` | Đăng nhập bằng token | P0 | `AC-CON-05`, `AC-CON-06`, `AC-CON-07` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-03` | Xác thực request và hết hạn phiên | P0 | `AC-CON-08`, `AC-CON-09`, `AC-CON-10` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-04` | Chặn DNS rebinding bằng Host | P0 | `AC-CON-11`, `AC-CON-12`, `AC-CON-13` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-05` | Chống CSRF cho request ghi | P0 | `AC-CON-14`, `AC-CON-15`, `AC-CON-16` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-06` | Màn hình Tổng quan SCR-002 | P0 | `AC-CON-17`, `AC-CON-18`, `AC-CON-19` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-07` | Màn hình Đánh giá runtime SCR-003 | P0 | `AC-CON-20`, `AC-CON-21`, `AC-CON-22` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-08` | Sinh kế hoạch trên SCR-004 | P0 | `AC-CON-23`, `AC-CON-24`, `AC-CON-25` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-09` | Thao tác checklist trên SCR-004 | P0 | `AC-CON-26`, `AC-CON-27`, `AC-CON-28` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-10` | Jobs & Log SCR-006 và huỷ job | P0 | `AC-CON-29`, `AC-CON-30`, `AC-CON-31` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-11` | Findings thư viện SCR-005 | P0 | `AC-CON-32`, `AC-CON-33`, `AC-CON-34` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-12` | Rollback & lịch sử SCR-007 | P0 | `AC-CON-35`, `AC-CON-36`, `AC-CON-37` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-13` | Nguồn dữ liệu SCR-008 và nhập snapshot | P0 | `AC-CON-38`, `AC-CON-39`, `AC-CON-40`, `AC-CON-41` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-14` | Site & ánh xạ runtime SCR-009 | P0 | `AC-CON-42`, `AC-CON-43`, `AC-CON-44` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-15` | Audit & báo cáo SCR-010 | P1 | `AC-CON-45`, `AC-CON-46`, `AC-CON-47` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-16` | Dry-run và xác nhận SCR-011 | P0 | `AC-CON-48`, `AC-CON-49`, `AC-CON-50`, `AC-CON-51` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-17` | Tài nguyên tĩnh và header bảo mật | P0 | `AC-CON-52`, `AC-CON-53`, `AC-CON-54` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-18` | Danh sách trắng lệnh | P0 | `AC-CON-55`, `AC-CON-56`, `AC-CON-57` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-CON-19` | Hợp đồng API /api/v1 | P0 | `AC-CON-58`, `AC-CON-59`, `AC-CON-60` | [acceptance-criteria-con.md](acceptance-criteria-con.md) |
| `US-JOB-01` | Hàng đợi và chạy job | P0 | `AC-JOB-01`, `AC-JOB-02`, `AC-JOB-03` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-02` | Khoá dùng chung với CLI | P0 | `AC-JOB-04`, `AC-JOB-05`, `AC-JOB-06` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-03` | Huỷ job | P0 | `AC-JOB-07`, `AC-JOB-08`, `AC-JOB-09` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-04` | Đối soát job khi console khởi động lại | P0 | `AC-JOB-10`, `AC-JOB-11`, `AC-JOB-12` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-05` | Lưu log, kết quả và lưu giữ | P0 | `AC-JOB-13`, `AC-JOB-14`, `AC-JOB-15` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-06` | Stream log qua SSE | P0 | `AC-JOB-16`, `AC-JOB-17`, `AC-JOB-18`, `AC-JOB-25` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-07` | Audit append-only | P0 | `AC-JOB-19`, `AC-JOB-20`, `AC-JOB-21` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-JOB-08` | Truy vấn và kiểm toàn vẹn audit | P0 | `AC-JOB-22`, `AC-JOB-23`, `AC-JOB-24` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-CLI-01` | Envelope --json | P0 | `AC-CLI-01`, `AC-CLI-02`, `AC-CLI-03` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-02` | Công bố JSON Schema | P1 | `AC-CLI-04`, `AC-CLI-05`, `AC-CLI-06` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-03` | Tương thích ngược v0.1 | P0 | `AC-CLI-07`, `AC-CLI-08`, `AC-CLI-09` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-04` | Thay mảng ghi cứng bằng bundle | P0 | `AC-CLI-10`, `AC-CLI-11`, `AC-CLI-12` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-05` | Lệnh assess | P0 | `AC-CLI-13`, `AC-CLI-14`, `AC-CLI-15` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-06` | Lệnh plan | P0 | `AC-CLI-16`, `AC-CLI-17`, `AC-CLI-18` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-07` | Lệnh migrate và bí danh | P0 | `AC-CLI-19`, `AC-CLI-20`, `AC-CLI-21` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-08` | Lệnh report và audit | P0 | `AC-CLI-22`, `AC-CLI-23`, `AC-CLI-24` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-09` | Dry-run và xác nhận trên CLI | P0 | `AC-CLI-25`, `AC-CLI-26`, `AC-CLI-27` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-CLI-10` | Kiểm quyền và môi trường chạy | P0 | `AC-CLI-28`, `AC-CLI-29`, `AC-CLI-30` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-RPT-01` | Báo cáo đánh giá | P1 | `AC-RPT-01`, `AC-RPT-02`, `AC-RPT-03` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-RPT-02` | Báo cáo bằng chứng thay đổi | P1 | `AC-RPT-04`, `AC-RPT-05`, `AC-RPT-06` | [acceptance-criteria-ptch-cli-rpt.md](acceptance-criteria-ptch-cli-rpt.md) |
| `US-FLT-01` | Danh mục server và ghim khoá SSH | P0 | `AC-FLT-01`, `AC-FLT-02`, `AC-FLT-03` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-FLT-02` | Tài khoản và vai trò Phase 2 | P0 | `AC-FLT-04`, `AC-FLT-05`, `AC-FLT-06` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-FLT-03` | Chạy CLI từ xa theo đợt | P0 | `AC-FLT-07`, `AC-FLT-08`, `AC-FLT-09` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-FLT-04` | Dashboard tổng hợp nhiều server | P0 | `AC-FLT-10`, `AC-FLT-11`, `AC-FLT-12` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |
| `US-FLT-05` | Phân phối snapshot từ máy trung tâm | P1 | `AC-FLT-13`, `AC-FLT-14`, `AC-FLT-15` | [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) |

## 4. Module SCAN — Nhận diện và kiểm kê

## Story: US-SCAN-01 - Nhận diện môi trường và kiểm kê site → runtime
Tham chiếu: `FR-SCAN-ENV-001`, `FR-SCAN-MAP-001` · `BR-ENV-001`, `BR-ENV-002`, `BR-SCAN-001` · `ERR-ENV-422-01`, `ERR-ENV-422-02` · `NFR-ENV-07` · SCR-009

```gherkin
Feature: US-SCAN-01 Nhận diện môi trường và kiểm kê site → runtime

  @AC-SCAN-01 @happy-path
  Scenario: Nhận diện cPanel và lập bảng site → runtime cho 40 vhost
    Given máy kiểm thử chuẩn có file thực thi "/usr/local/cpanel/cpanel" và 40 vhost dùng ea-php81, ea-php83
    When người vận hành chạy "php-quickpatch.sh scan --only sites --json"
    Then "environment.pb_provider" bằng "PB-007" và "environment.evidence[]" chứa dấu hiệu "/usr/local/cpanel/cpanel"
    And "result" có đúng 40 bản ghi site_binding, mỗi bản ghi có "site_id", "pb_id", "binding_kind" = "cpanel_multiphp", "binding_ref", "current_branch", "current_bin"
    And bước nhận diện playbook hoàn tất trong ≤ 5 s
    And 0 file ngoài STATE_DIR bị ghi, 0 dịch vụ bị reload

  @AC-SCAN-02 @negative
  Scenario: PHP không khớp playbook nào được gán PB-000
    Given máy chủ không có panel, không có tiến trình "nginx: master" hay "apache2"/"httpd", PHP duy nhất ở "/srv/test/php/bin/php" không thuộc gói nào
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "environment.pb_provider" bằng "PB-000"
    And "errors[]" chứa mã "ERR-ENV-422-01" với thông báo "Không nhận diện được cách PHP được cài và gán cho site trên máy chủ này."
    And runtime đó chỉ cho phép hành động mitigation ini; hành động cài song song và chuyển site bị khoá

  @AC-SCAN-03 @boundary
  Scenario: Site khớp 2 lớp gán được chọn theo cấu hình web server đang nạp
    Given site "shop.test" có vhost trong "/etc/nginx/sites-enabled/shop.test.conf" xuất hiện trong "nginx -T"
    And có file "/etc/apache2/sites-available/shop.test.conf" không xuất hiện trong "apachectl -S"
    And site "legacy.test" không xuất hiện trong cấu hình đang nạp của web server nào
    When người vận hành chạy "php-quickpatch.sh scan --only sites --json"
    Then site "shop.test" có "binding_kind" = "nginx_fastcgi" và lớp Apache được ghi vào "environment.evidence[]"
    And "issues[]" chứa "ERR-ENV-422-02" cho site "legacy.test" và site này chỉ có mục checklist mức MANUAL
```

## Story: US-SCAN-02 - Phát hiện runtime PHP và Node.js
Tham chiếu: `FR-SCAN-RT-001`, `FR-SCAN-RT-002` · `BR-SCAN-002`, `BR-SCN-001` · `ERR-SCN-422-01` · `NFR-PERF-004`

```gherkin
Feature: US-SCAN-02 Phát hiện runtime PHP và Node.js

  @AC-SCAN-04 @happy-path
  Scenario: Phát hiện 1 PHP gói distro và 1 Node.js tarball
    Given máy kiểm thử chuẩn có "/usr/bin/php8.3" thuộc gói "php8.3-cli" phiên bản "8.3.6-0ubuntu0.24.04.13"
    And có "/usr/local/bin/node" phiên bản "v24.22.1" không thuộc gói, có "/usr/local/lib/node_modules/npm"
    When người vận hành chạy "php-quickpatch.sh scan --only php,node --json"
    Then "result.runtimes[]" có 2 phần tử, "runtime_id" khớp regex "^(php|node):[0-9a-f]{12}$"
    And phần tử PHP có "version" = "8.3.6", "branch" = "8.3", "owner_pkg" = "php8.3-cli", "install_source" = "package", "sapis[]" và "extensions[]" không rỗng
    And phần tử Node.js có "install_source" = "tarball", "abi" lấy từ "process.versions.modules" và "npm_version" khác rỗng
    And "state" của mỗi runtime thuộc tập "ok", "ok-backport", "vulnerable", "eol", "unknown"

  @AC-SCAN-05 @negative
  Scenario: Binary không trả phiên bản trong 10 s
    Given "/srv/test/php-hang/bin/php" treo khi chạy "-n -r 'echo PHP_VERSION;'"
    And "QP_PHP_BINS" chứa "/srv/test/php-hang/bin/php" và "/usr/bin/php8.3"
    When người vận hành chạy "php-quickpatch.sh scan --only php --json"
    Then lệnh thăm dò binary treo bị dừng sau 10 s
    And runtime đó có "state" = "unknown", kịch bản "SCN-PHP-005" và "errors[]" chứa "ERR-SCN-422-01"
    And runtime "/usr/bin/php8.3" vẫn có đủ các trường "version", "branch", "owner_pkg", "install_source", "state" trong cùng lượt quét

  @AC-SCAN-06 @boundary
  Scenario: Đường dẫn trùng qua symlink chỉ tạo 1 runtime
    Given "/usr/bin/php" trỏ "/etc/alternatives/php" rồi tới "/usr/bin/php8.3"
    And "QP_PHP_BINS" chứa thêm "/usr/bin/php8.3" và tồn tại "/usr/bin/php-config8.3"
    When người vận hành chạy "php-quickpatch.sh scan --only php --json"
    Then "result.runtimes[]" có đúng 1 runtime PHP với "bin" = "/usr/bin/php8.3"
    And "runtime_id" bằng "php:" + 12 ký tự hex đầu của SHA-1 chuỗi "/usr/bin/php8.3"
    And không có runtime nào được tạo từ file "php-config8.3"
```

## Story: US-SCAN-03 - Kiểm kê dự án và container
Tham chiếu: `FR-SCAN-PRJ-001`, `FR-SCAN-PRJ-002` · `BR-SCAN-001`, `BR-SCAN-002`, `BR-SCAN-003` · `ERR-CLI-400-01`, `ERR-SCN-422-01`

```gherkin
Feature: US-SCAN-03 Kiểm kê dự án và container

  @AC-SCAN-07 @happy-path
  Scenario: Kiểm kê dự án đủ 4 loại và 2 container đang chạy
    Given "/var/www/shop.test" chứa "composer.lock", "package-lock.json", "wp-includes/version.php", "Dockerfile" và thuộc user "shop"
    And "docker info" trả exit 0 với 2 container chạy image "php:8.2.34-fpm" và "node:24.22.1"
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "result.projects[]" có 1 phần tử với "project_id" = 12 ký tự hex đầu SHA-1 của "/var/www/shop.test", "owner" = "shop", "kinds[]" gồm composer, npm, wordpress, docker
    And "site_id" của dự án bằng site có docroot chứa "/var/www/shop.test"
    And "result.containers[]" có 2 phần tử với "php_version" = "8.2.34" và "node_version" = "24.22.1" tương ứng

  @AC-SCAN-08 @negative
  Scenario: Tuỳ chọn --path thiếu giá trị
    Given máy kiểm thử chuẩn
    When người vận hành chạy "php-quickpatch.sh scan --path"
    Then lệnh in usage như v0.1 và kết thúc với mã thoát 2
    And khi chạy kèm "--json", "errors[]" chứa "ERR-CLI-400-01"
    And không thư mục nào được quét

  @AC-SCAN-09 @boundary
  Scenario: Giới hạn độ sâu 7 cấp, thư mục loại trừ và container treo
    Given "/var/www/a/b/c/d/e/f/composer.lock" ở độ sâu 7 và "/var/www/a/b/c/d/e/f/g/composer.lock" ở độ sâu 8
    And "/var/www/app/node_modules/x/package-lock.json" và symlink "/var/www/link" trỏ ra "/opt"
    And 1 container có lệnh "docker exec … php -r" treo
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then chỉ lockfile ở độ sâu 7 có trong "result.projects[]"; lockfile trong "node_modules" và đích của symlink không được liệt kê
    And container treo được dừng thăm dò sau 10 s, có "php_version" rỗng và cảnh báo "ERR-SCN-422-01"
```

## Story: US-SCAN-04 - Phát hiện webshell chỉ báo cáo
Tham chiếu: `FR-SCAN-WSH-001` · `BR-SEC-003`, `BR-SCAN-001`, `BR-CON-008` · `ERR-CON-422-01`

```gherkin
Feature: US-SCAN-04 Phát hiện webshell chỉ báo cáo

  @AC-SCAN-10 @happy-path
  Scenario: Báo cáo file PHP trong thư mục uploads của WordPress
    Given site WordPress "/var/www/blog.test" có file "wp-content/uploads/2026/10/x.php" 1.024 byte
    And SHA-256 và mtime của file được ghi lại trước khi quét
    When người vận hành chạy "php-quickpatch.sh scan --only webshell --json"
    Then "result.webshell_findings[]" có phần tử với "path", "rule", "sha256" (64 ký tự hex), "mtime", "size" = 1024
    And "issues[]" có đúng 1 issue mức "critical" cho nhóm webshell và mã thoát là 1
    And SHA-256, mtime, quyền và vị trí của file sau lượt quét không đổi

  @AC-SCAN-11 @negative
  Scenario: Console từ chối yêu cầu xoá file nghi webshell
    Given phiên console hợp lệ và "result.webshell_findings[]" có 1 file
    When client gửi "POST /api/v1/jobs" với "action" = "delete_webshell"
    Then API trả HTTP 422 với "error.code" = "ERR-CON-422-01"
    And không tiến trình con nào được tạo và file vẫn còn nguyên

  @AC-SCAN-12 @boundary
  Scenario: Giới hạn kích thước file và số kết quả mỗi nhóm
    Given thư mục dự án có 1 file "*.php" 2.097.152 byte (2 MiB) khớp mẫu và 60 file "*.php" < 2 MB khớp cùng 1 mẫu
    When người vận hành chạy "php-quickpatch.sh fix --only webshell --json"
    Then file 2 MiB không được đọc nội dung
    And "result.webshell_findings[]" có tối đa 50 phần tử cho nhóm mẫu đó
    And lượt "fix" không tạo dòng nào trong backup manifest cho các file này
```

## Story: US-SCAN-05 - Cảnh báo gán site bị đổi ngoài tool
Tham chiếu: `FR-SCAN-DRF-001` · `BR-ENV-001` · `ERR-SCAN-409-01` · SCR-009

```gherkin
Feature: US-SCAN-05 Cảnh báo gán site bị đổi ngoài tool

  @AC-SCAN-13 @happy-path
  Scenario: Gán site khớp lượt chuyển gần nhất
    Given site "shop.test" có switch_record "20261020-101500" trạng thái "PASSED" sang nhánh "8.4"
    And "binding_ref" hiện tại trỏ pool "qp-shop.test" của PHP 8.4
    When người vận hành chạy "php-quickpatch.sh scan --only sites --json"
    Then "result.drift_warnings[]" không có phần tử nào cho "shop.test"

  @AC-SCAN-14 @negative
  Scenario: Công cụ quản lý cấu hình ghi đè vhost về PHP 8.1
    Given site "shop.test" có lượt chuyển "PASSED" gần nhất sang "8.4"
    And vhost hiện tại trỏ lại socket "/run/php/php8.1-fpm.sock"
    When người vận hành chạy "php-quickpatch.sh scan --only sites --json"
    Then "result.drift_warnings[]" có phần tử "site_id" = "shop.test", "expected" = "8.4", "actual" = "8.1"
    And "warnings[]" chứa "ERR-SCAN-409-01" với thông báo "Site shop.test đang dùng 8.1, khác 8.4 do tool chuyển lần trước."
    And SCR-009 hiển thị cảnh báo thay đổi ngoài tool trên dòng của site

  @AC-SCAN-15 @boundary
  Scenario: Site chưa từng được tool chuyển
    Given site "new.test" không có switch_record nào trong "STATE_DIR/switches/index.tsv"
    When người vận hành chạy "php-quickpatch.sh scan --only sites --json"
    Then "result.drift_warnings[]" không có phần tử nào cho "new.test"
    And lượt quét không ghi file nào vào "STATE_DIR/switches/"
```

## 5. Module SCN — Kịch bản phiên bản và checklist

## Story: US-SCN-01 - Gán kịch bản và khoá phiên bản bất thường
Tham chiếu: `FR-SCN-CLS-001`, `FR-SCN-CLS-002`, `FR-SCN-LOCK-001` · `BR-SCN-001`, `BR-SCN-013`, `BR-SCN-020`, `BR-SCN-040`, `BR-UPG-004` · `ERR-SCN-422-01`

```gherkin
Feature: US-SCN-01 Gán kịch bản và khoá phiên bản bất thường

  @AC-SCN-01 @happy-path
  Scenario: PHP 8.2 gói distro nhận 1 kịch bản VERSION và 1 OVERLAY
    Given runtime "/usr/bin/php8.2" trả "8.2.34" và thuộc gói "php8.2-cli"
    When tool gán kịch bản trong lượt "scan --json"
    Then "scenario_ids[]" bằng ["SCN-PHP-010", "SCN-PHP-015"]
    And có đúng 1 kịch bản loại VERSION trong "scenario_ids[]"

  @AC-SCN-02 @happy-path
  Scenario: Node.js cài bằng nvm nhận kịch bản dòng 22 và overlay nvm
    Given runtime "/home/dev/.nvm/versions/node/v22.23.3/bin/node" trả "v22.23.3"
    When tool gán kịch bản trong lượt "scan --json"
    Then "scenario_ids[]" bằng ["SCN-NODE-005", "SCN-NODE-009"]

  @AC-SCN-03 @negative
  Scenario: Chuỗi phiên bản "6.0.0-dev" bị khoá tự động hoá
    Given runtime "/srv/test/php6/bin/php" trả "6.0.0-dev"
    When người vận hành chạy "php-quickpatch.sh fix --json"
    Then runtime nhận kịch bản "SCN-PHP-005", "lifecycle_status" = "UNKNOWN", "locked" = true
    And "errors[]" chứa "ERR-SCN-422-01" với thông báo "Không nhận diện được phiên bản PHP '6.0.0-dev'. Tự động hoá cho runtime này đã bị khoá."
    And mọi hành động vá, mitigation tự động, cài song song, chuyển site trên runtime này có kết quả "SKIPPED" và 0 gói bị nâng

  @AC-SCN-04 @boundary
  Scenario Outline: Biên của quy tắc gán kịch bản
    Given runtime trả chuỗi phiên bản "<raw>"
    When tool gán kịch bản
    Then kịch bản VERSION là "<scn>" và cờ "locked" là <locked>

    Examples:
      | raw                   | scn          | locked |
      | 8.6.0RC4              | SCN-PHP-014  | true   |
      | 10.0.0                | SCN-PHP-005  | true   |
      | 5.6.40                | SCN-PHP-004  | false  |
      | 8.5.12                | SCN-PHP-013  | false  |
      | v27.0.0-nightly202610 | SCN-NODE-008 | true   |
      | v16.20.2              | SCN-NODE-001 | false  |
```

## Story: US-SCN-02 - Trạng thái hỗ trợ và mức ưu tiên động
Tham chiếu: `FR-SCN-LIFE-001` · `BR-SCN-003`, `BR-DATA-001`, `BR-FEED-005`, `BR-FEED-020` · `ERR-FEED-412-01`, `ERR-SCN-503-01`

```gherkin
Feature: US-SCN-02 Trạng thái hỗ trợ và mức ưu tiên động

  @AC-SCN-05 @happy-path
  Scenario: Tính trạng thái ngày 2026-10-22 cho PHP 8.2 và Node.js 24
    Given bundle mẫu 2026-10-22 và ngày chạy 2026-10-22 (UTC)
    And runtime PHP 8.2.35 và Node.js 24.22.1
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then PHP 8.2 có "lifecycle_status" = "SECURITY_ONLY", "eol_date" = "2026-12-31", "days_to_eol" = 70, "priority" = "Cao"
    And Node.js 24 có "lifecycle_status" = "MAINTENANCE_LTS", "is_lts" = true, "eol_date" = "2028-04-30", "days_to_eol" = 556
    And file catalog "scenarios.json" không chứa trường "lifecycle_status" hay "priority" ghi cứng

  @AC-SCN-06 @negative
  Scenario: Dữ liệu vòng đời cũ hơn 90 ngày
    Given máy chủ không có mạng và bundle có "data_age_h" = 2.200
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "errors[]" chứa "ERR-SCN-503-01" với thông báo "Dữ liệu vòng đời đã cũ 91 ngày; tạm ngừng đề xuất nâng nhánh."
    And chỉ hành động vá cùng nhánh được đề xuất; danh sách ứng viên khác nhánh không được sinh

  @AC-SCN-07 @boundary
  Scenario Outline: Biên ngày EOL tính tại thời điểm chạy
    Given dữ liệu vòng đời PHP 8.2 có "support" = "2025-12-31", "eol" = "2026-12-31" và php.net không còn liệt kê 8.2 trong "supported_versions" khi ngày chạy > 2026-12-31
    And runtime PHP 8.2.35 không còn CVE chưa vá
    When tool tính trạng thái vào ngày "<ngay>"
    Then "lifecycle_status" = "<status>", "days_to_eol" = <days>, "priority" = "<prio>"

    Examples:
      | ngay       | status        | days | prio         |
      | 2026-12-31 | SECURITY_ONLY | 0    | Cao          |
      | 2027-01-01 | EOL           | -1   | Cao          |
      | 2027-12-31 | EOL           | -365 | Cao          |
      | 2028-01-01 | EOL           | -366 | Nghiêm trọng |
```

## Story: US-SCN-03 - Nạp và cập nhật catalog
Tham chiếu: `FR-SCN-CAT-001` · `BR-FEED-010`, `BR-ENV-010` · `ERR-FEED-422-02`, `ERR-FEED-502-02` · `NFR-MNT-001`, `NFR-ENV-06`

```gherkin
Feature: US-SCN-03 Nạp và cập nhật catalog

  @AC-SCN-08 @happy-path
  Scenario: Catalog trong snapshot nhập mới hơn catalog đóng gói
    Given catalog đóng gói có "catalog_version" = "2026.10.20-1"
    And snapshot đã nhập chứa thư mục "catalog/" có "catalog_version" = "2026.11.05-1" và "SHA256SUMS" khớp mọi file
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then envelope có "catalog_version" = "2026.11.05-1"
    And kịch bản và luật mới của catalog được áp dụng mà file "php-quickpatch.sh" không thay đổi (so SHA-256 trước/sau)

  @AC-SCN-09 @negative
  Scenario: Catalog trong snapshot sai SHA-256 bị từ chối
    Given catalog đang dùng có "catalog_version" = "2026.10.20-1"
    And snapshot nhập chứa "catalog/checklists.json" có SHA-256 khác dòng tương ứng trong "SHA256SUMS"
    When tool nạp catalog trong lượt "scan --json"
    Then "errors[]" chứa "ERR-FEED-422-02"
    And catalog hiệu lực vẫn là "2026.10.20-1"

  @AC-SCN-10 @boundary
  Scenario: Catalog sai schema và lệnh chưa kiểm chứng
    Given catalog mới có "catalog_version" lớn hơn nhưng "playbooks.json" thiếu khoá bắt buộc "actions"
    And catalog đang dùng có 1 lệnh playbook "verified" = false
    When tool nạp catalog
    Then catalog mới bị từ chối với "ERR-FEED-502-02" và catalog đang dùng được giữ
    And lệnh "verified" = false chỉ xuất hiện ở mục mức MANUAL hoặc SEMI kèm nhãn "chưa kiểm chứng", không bao giờ ở mức AUTO
```

## Story: US-SCN-04 - Lắp checklist hiệu lực
Tham chiếu: `FR-SCN-CHK-001` · `BR-SCN-001`, `BR-SCN-018`, `BR-ENV-010` · `ERR-SCN-424-01` · `NFR-MNT-001`

```gherkin
Feature: US-SCN-04 Lắp checklist hiệu lực

  @AC-SCN-11 @happy-path
  Scenario: Checklist cho site PHP 8.2 gói distro nâng lên 8.5
    Given runtime PHP 8.2.34 có "scenario_ids[]" = ["SCN-PHP-010", "SCN-PHP-015"], site "shop.test" gán PB-005, nhánh đích "8.5"
    When tool lắp checklist hiệu lực khi sinh kế hoạch
    Then mỗi mục có "chk_id" khớp "^CHK-PHP-[0-9]{3}-[0-9]{2}(-[0-9]{2})?$", "site_id" = "shop.test", "phase", "exec_type", "check_mechanism", "done_criteria", "verified"
    And mục OVERLAY của SCN-PHP-015 đứng trước mục VERSION của SCN-PHP-010 trong cùng giai đoạn
    And mọi chuỗi "$OLD", "$NEW", "$SITE" trong "check_mechanism" đã được thay bằng "8.2", "8.5", "shop.test"

  @AC-SCN-12 @negative
  Scenario: Chạy mục P5 khi mục P3 chưa hoàn thành
    Given checklist của "shop.test" có mục P3 "CHK-PHP-010-12" ở trạng thái "PENDING"
    When người vận hành chạy mục P5 chuyển site của "shop.test"
    Then yêu cầu bị từ chối với "ERR-SCN-424-01" và thông báo nêu "CHK-PHP-010-12"
    And trạng thái mục P5 giữ nguyên "PENDING"

  @AC-SCN-13 @boundary
  Scenario: Mục không áp dụng và mục "(khi nâng)" được mở rộng
    Given site không dùng WordPress, có 2 package Composer phải nâng và checklist chứa mục có "applies_when" = "framework=wordpress"
    When tool lắp checklist hiệu lực
    Then mục "applies_when" = "framework=wordpress" có trạng thái "SKIPPED"
    And mục "(khi nâng)" sinh đúng 2 mục con có hậu tố "-01", "-02" gắn với 2 package
```

## Story: US-SCN-05 - Giới hạn thao tác theo môi trường đặc biệt
Tham chiếu: `FR-SCN-ENV-001` · `BR-ENV-009`, `BR-PTCH-003`, `BR-CLI-005` · `ERR-ENV-422-01`, `ERR-PTCH-403-01`

```gherkin
Feature: US-SCN-05 Giới hạn thao tác theo môi trường đặc biệt

  @AC-SCN-14 @happy-path
  Scenario: Chạy không root chỉ được vá cấp dự án
    Given CLI chạy với EUID 1001 (user "shop") và "/home/shop/app" có "composer.lock"
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "environment.restrictions[]" ghi giới hạn "không root: chỉ cấp dự án"
    And checklist có mục MANUAL hướng dẫn thao tác trên giao diện panel cho runtime hệ thống

  @AC-SCN-15 @negative
  Scenario: Vá runtime hệ thống khi không root
    Given CLI chạy với EUID 1001 và "/usr/bin/php8.2" ở trạng thái "vulnerable"
    When người vận hành chạy "php-quickpatch.sh fix --only php"
    Then issue mức "critical" có thông báo "PHP 8.2.34 (/usr/bin/php8.2): needs root (or the hosting panel) to upgrade" tương ứng "ERR-PTCH-403-01"
    And 0 gói hệ thống bị nâng và lệnh tiếp tục với các mục cấp dự án

  @AC-SCN-16 @boundary
  Scenario: Chạy trong container chỉ cho mitigation
    Given tool chạy trong container có file "/.dockerenv"
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "environment.in_container" = true và "environment.restrictions[]" ghi "trong container: chỉ mitigation"
    And hành động cài song song, chuyển site, rollback site trên runtime trong container bị khoá kèm hướng dẫn chạy PB-013 ở host
```

## 6. Module ASMT — Đánh giá bảo mật

## Story: US-ASMT-01 - Đánh giá runtime hiện tại và điểm rủi ro
Tham chiếu: `FR-ASMT-CUR-001`, `FR-ASMT-RISK-001` · `BR-SEC-001`, `BR-FEED-029`, `BR-FEED-040`, `BR-FEED-041`, `BR-FEED-042` · `ERR-ASMT-404-01`, `ERR-FEED-412-01` · `NFR-MNT-002`

```gherkin
Feature: US-ASMT-01 Đánh giá runtime hiện tại và điểm rủi ro

  @AC-ASMT-01 @happy-path
  Scenario: Đánh giá PHP 8.2.34 upstream ngày 2026-10-22
    Given bundle mẫu 2026-10-22 và runtime PHP 8.2.34 build upstream
    When người vận hành chạy "php-quickpatch.sh assess --runtime-id php:3f2a9c1e0b7d --json"
    Then "assessment.current.cve_counts" = {"critical": 2, "high": 0, "medium": 0, "low": 0} và "kev_count" = 0
    And "lifecycle_status" = "SECURITY_ONLY", "eol_date" = "2026-12-31", "days_to_eol" = 70, "latest_patch" = "8.2.35", "min_patched" = "8.2.35"
    And "risk.score" = 60, "risk.level" = "HIGH", "risk.components" = {"S_cvss": 39.2, "S_cnt": 8, "S_kev": 0, "S_life": 5, "S_eol": 8}

  @AC-ASMT-02 @boundary
  Scenario: Nhánh EOL được nâng lên điểm sàn CRITICAL
    Given bundle mẫu 2026-10-22 và runtime PHP 7.4.33
    When tool tính đánh giá
    Then "R_raw" = 68,2 và "risk.score" = 70 do điểm sàn mức ưu tiên "Nghiêm trọng" (EOL > 365 ngày)
    And "risk.level" = "CRITICAL"
    And CVE có "assessed" = false không được đếm và kết quả hiển thị nhãn "Nhánh EOL — nguồn không còn đánh giá CVE mới"

  @AC-ASMT-03 @negative
  Scenario: runtime_id không có trong kết quả scan gần nhất
    Given kết quả scan gần nhất không chứa "php:0123456789ab"
    When người vận hành chạy "php-quickpatch.sh assess --runtime-id php:0123456789ab --json"
    Then "errors[]" chứa "ERR-ASMT-404-01" với thông báo "Không tìm thấy runtime php:0123456789ab; hãy quét lại."
    And mã thoát là 2

  @AC-ASMT-04 @boundary
  Scenario Outline: Cảnh báo theo tuổi dữ liệu dùng để đánh giá
    Given bundle có "data_age_h" = <age>
    When người vận hành chạy "php-quickpatch.sh assess --runtime-id php:3f2a9c1e0b7d --json"
    Then "data.freshness" = "<muc>" và mảng cảnh báo <canh_bao>

    Examples:
      | age   | muc     | canh_bao                                   |
      | 168   | AGING   | không chứa "ERR-FEED-412-01"                |
      | 169   | STALE   | chứa "ERR-FEED-412-01"                      |
      | 2160  | STALE   | chứa "ERR-FEED-412-01"                      |
      | 2161  | EXPIRED | chứa "ERR-SCN-503-01"                       |
```

## Story: US-ASMT-02 - Phiên bản ứng viên và khả năng cài
Tham chiếu: `FR-ASMT-CAND-001`, `FR-ASMT-CAND-002` · `BR-ASMT-001`, `BR-ASMT-002`, `BR-UPG-004`, `BR-SCN-005`, `BR-ENV-004`, `BR-ENV-010`, `BR-DATA-003` · `ERR-SCN-409-01`

```gherkin
Feature: US-ASMT-02 Phiên bản ứng viên và khả năng cài

  @AC-ASMT-05 @happy-path
  Scenario: Ứng viên cho PHP 8.2.34 trên Ubuntu có kho Surý
    Given bundle mẫu 2026-10-22, runtime PHP 8.2.34 playbook PB-001, kho "packages.sury.org" đã bật
    When người vận hành chạy "php-quickpatch.sh assess --runtime-id php:3f2a9c1e0b7d --candidates --json"
    Then "assessment.candidates[]" chứa "8.2.35" loại ["SAME_BRANCH_LATEST"], "8.3.36" loại ["NEXT_SUPPORTED"], "8.5.12" loại ["RECOMMENDED", "LATEST_STABLE"]
    And mỗi phiên bản chỉ xuất hiện 1 lần trong danh sách
    And ứng viên nhánh 8.6 (PRE_RELEASE) có "selectable" = false và "not_selectable_reason" khác rỗng
    And mỗi ứng viên có "installable" thuộc tập "yes", "needs_repo", "no", "unknown" và "install_source" tương ứng

  @AC-ASMT-06 @negative
  Scenario: Không có nhánh đích thoả ràng buộc framework
    Given site dùng runtime PHP 8.1 có framework mà ma trận trong bundle ghi dải PHP "8.0 - 8.2"
    And PHP 8.2 có "eol" nhỏ hơn ngày chạy + 365 ngày
    When tool sinh ứng viên
    Then không có ứng viên mang loại "RECOMMENDED"
    And "errors[]" chứa "ERR-SCN-409-01" với đề xuất nâng framework trước

  @AC-ASMT-07 @boundary
  Scenario Outline: Ngưỡng selectable theo ngày EOL của nhánh khác nhánh hiện tại
    Given ngày chạy "2026-10-22" và nhánh ứng viên khác nhánh hiện tại có "eol" = "<eol>"
    When tool đánh dấu ứng viên
    Then "selectable" = <sel> và chọn thủ công kèm lý do được phép = <manual>

    Examples:
      | eol        | sel   | manual |
      | 2027-10-22 | true  | true   |
      | 2027-10-21 | false | true   |
      | 2027-01-20 | false | true   |
      | 2027-01-19 | false | false  |
```

## Story: US-ASMT-03 - So sánh hiện tại với ứng viên
Tham chiếu: `FR-ASMT-CMP-001`, `FR-ASMT-RISK-002` · `BR-ASMT-003`, `BR-FEED-042`, `BR-FEED-044` · `ERR-SCN-503-01` · SCR-003

```gherkin
Feature: US-ASMT-03 So sánh hiện tại với ứng viên

  @AC-ASMT-08 @happy-path
  Scenario: Bảng so sánh PHP 8.2.34 với 8.2.35 và 8.5.12
    Given bundle mẫu 2026-10-22 và runtime PHP 8.2.34 upstream có "R" = 60
    When người vận hành mở bảng so sánh của runtime
    Then dòng "8.2.35" có "R" = 40 và "ΔR" = -20; dòng "8.5.12" có "R" = 0 và "ΔR" = -60
    And mọi cột (CVE theo mức, KEV, trạng thái hỗ trợ, LTS, EOL, số ngày còn lại, khoảng cách major, "R", "ΔR") tính trên cùng "bundle_id" và cùng ngày T
    And bảng hiển thị "bundle_id", tuổi dữ liệu và "catalog_version"

  @AC-ASMT-09 @negative
  Scenario: Dữ liệu hết hạn chặn đề xuất nâng nhánh
    Given bundle có "data_age_h" = 2.400 và runtime PHP 8.2.34
    When người vận hành mở bảng so sánh
    Then "errors[]" chứa "ERR-SCN-503-01"
    And chỉ dòng ứng viên "SAME_BRANCH_LATEST" được hiển thị là có thể chọn

  @AC-ASMT-10 @boundary
  Scenario Outline: Làm tròn điểm và ngưỡng phân mức
    Given ứng viên có "R_raw" = <raw> và điểm sàn mức ưu tiên = 0
    When tool tính "R" của ứng viên
    Then "R" = <r> và mức = "<level>"

    Examples:
      | raw  | r  | level    |
      | 19,4 | 19 | LOW      |
      | 19,5 | 20 | MEDIUM   |
      | 39,5 | 40 | HIGH     |
      | 69,4 | 69 | HIGH     |
      | 69,5 | 70 | CRITICAL |
```

## Story: US-ASMT-04 - Xếp hạng ưu tiên xử lý
Tham chiếu: `FR-ASMT-RANK-001` · `BR-SEC-001`, `BR-FEED-042`, `BR-ASMT-004` · `ERR-FEED-412-01` · SCR-002

```gherkin
Feature: US-ASMT-04 Xếp hạng ưu tiên xử lý

  @AC-ASMT-11 @happy-path
  Scenario: Xếp 3 đối tượng theo R giảm dần
    Given bundle mẫu 2026-10-22, site WordPress 7.0.1 ("R" = 71), runtime PHP 7.4.33 ("R" = 70), runtime PHP 8.2.34 ("R" = 60)
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "result.ranking[]" theo thứ tự WordPress 7.0.1, PHP 7.4.33, PHP 8.2.34
    And mỗi phần tử có "object_ref", "R", "level" và "reason_codes[]" khác rỗng

  @AC-ASMT-12 @negative
  Scenario: Xếp hạng khi dữ liệu đã cũ
    Given bundle có "data_age_h" = 200
    When người vận hành chạy "php-quickpatch.sh scan --json"
    Then "result.ranking[]" vẫn chứa 100% runtime, site WordPress và dependency của lượt quét
    And "warnings[]" chứa "ERR-FEED-412-01" nêu nguồn cũ nhất

  @AC-ASMT-13 @boundary
  Scenario: Cùng R = 70, đối tượng có KEV đứng trước
    Given WordPress 7.0.2 có "R" = 70 và 1 CVE thuộc KEV, PHP 7.4.33 có "R" = 70 không có KEV
    And 2 runtime PHP khác có cùng "R" = 40, cùng hạng, "object_ref" là "php:aaaaaaaaaaaa" và "php:bbbbbbbbbbbb"
    When tool xếp hạng
    Then WordPress 7.0.2 đứng trước PHP 7.4.33
    And "php:aaaaaaaaaaaa" đứng trước "php:bbbbbbbbbbbb"
```

## Story: US-ASMT-05 - Đánh giá dependency Composer/npm
Tham chiếu: `FR-ASMT-DEP-001` · `BR-ASMT-005`, `BR-SEC-004`, `BR-FEED-013`, `BR-FEED-043` · `ERR-FEED-503-02` · SCR-005

```gherkin
Feature: US-ASMT-05 Đánh giá dependency Composer/npm

  @AC-ASMT-14 @happy-path
  Scenario: Finding Composer có CVSS và package mã độc npm
    Given dự án "/var/www/shop.test" có "vendor-test/lib" 1.2.0 trong "composer.lock" với advisory kiểm thử "GHSA-test-0001" CVSS 8,1, bản sửa 1.2.5
    And "package-lock.json" có "evil-test" 0.0.1 với advisory "MAL-2026-0001"
    When người vận hành chạy "php-quickpatch.sh scan --only composer,npm --json"
    Then "result.dependency_findings[]" có "vendor-test/lib" mức "high", "fixed_versions" = ["1.2.5"]
    And "evil-test" có "is_malware" = true, mức "critical" và khuyến nghị gỡ package, xoay vòng token npm/GitHub, khoá SSH, file ".env"

  @AC-ASMT-15 @negative
  Scenario: OSV không truy cập được và không có cache 7 ngày
    Given "api.osv.dev" bị chặn và không có kết quả cache ≤ 7 ngày cho SHA-256 của "composer.lock"
    When người vận hành chạy "php-quickpatch.sh scan --only composer --json"
    Then "warnings[]" chứa "ERR-FEED-503-02" với thông báo "Bỏ qua kiểm tra thư viện /var/www/shop.test/composer.lock: không tra được OSV."
    And lượt quét vẫn hoàn tất và các mục khác vẫn có kết quả

  @AC-ASMT-16 @boundary
  Scenario: Advisory không có điểm CVSS và lockfile yarn/pnpm
    Given advisory npm chỉ có mức chữ "high" trong "database_specific.severity"
    And dự án khác chỉ có "yarn.lock" và dự án thứ ba chỉ có "pnpm-lock.yaml"
    When tool đánh giá dependency
    Then advisory mức chữ "high" được gán điểm proxy 8,0 và mức "high"
    And 2 dự án yarn/pnpm nhận cảnh báo kèm lệnh "yarn npm audit" và "pnpm audit", không gửi truy vấn OSV cho 2 lockfile này
```

## Story: US-ASMT-06 - Đánh giá WordPress core
Tham chiếu: `FR-ASMT-DEP-002` · `BR-FEED-025`, `BR-SEC-001`, `BR-FEED-041` · `ERR-FEED-503-01` · SCR-005

```gherkin
Feature: US-ASMT-06 Đánh giá WordPress core

  @AC-ASMT-17 @happy-path
  Scenario: WordPress 7.0.2 còn CVE thuộc KEV
    Given bundle mẫu 2026-10-22 và site WordPress "/var/www/blog.test" phiên bản 7.0.2
    When người vận hành chạy "php-quickpatch.sh scan --only wp --json"
    Then "result.wordpress_findings[]" có "version" = "7.0.2", "min_patched" = "7.0.7", "in_kev" = true
    And advisory "CVE-2026-87902" được liệt kê và "R" = 70, mức "CRITICAL" do điểm sàn KEV

  @AC-ASMT-18 @negative
  Scenario: Nguồn wordpress.org lỗi
    Given "api.wordpress.org" trả HTTP 503 trong 3 lần thử và cache cũ 30 giờ
    When người vận hành chạy "php-quickpatch.sh scan --only wp --json"
    Then "warnings[]" chứa "ERR-FEED-503-01" nêu nguồn dữ liệu đang dùng và tuổi 30 giờ
    And "min_patched" của nhánh được tính từ dữ liệu NVD theo thuật toán dự phòng

  @AC-ASMT-19 @boundary
  Scenario Outline: Nhánh WordPress không còn bản vá
    Given bundle mẫu 2026-10-22 và site WordPress phiên bản "<ver>"
    When tool đánh giá WordPress core
    Then "min_patched" = "<mp>" và "status" = "<status>"

    Examples:
      | ver   | mp    | status     |
      | 4.5.3 | NONE  | eol        |
      | 7.1.3 | 7.1.3 | ok         |
      | 6.9.9 | 6.9.10 | vulnerable |
```
