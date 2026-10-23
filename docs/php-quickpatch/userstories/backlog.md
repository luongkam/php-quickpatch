---
id: DOC-US-QP-001
title: Danh mục User Story & Backlog — php-quickpatch v2
version: 1.0.1
phase: User Story
domain: Security Patch Management
tags: [userstory, backlog, invest, connextra, story-point, traceability, php, nodejs, console, cli, fleet, openba]
depends_on:
  - DOC-BRS-QP-001
  - DOC-PRD-QP-001
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-UC-QP-000
  - DOC-AC-QP-000
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-PLAN-001
  - DIAG-STATE-QP-JOB-001
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Danh mục User Story & Backlog — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo backlog 120 user story (Phase 1: 115, Phase 2 mức epic: 5) theo `skills/userstory`, template 27, rules 07, 16, 17, 18, 19; phủ 167/167 FR của SRS; mỗi story liên kết FR, use case và mã AC ở bộ tài liệu [acceptance-criteria.md](acceptance-criteria.md) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review, đồng bộ DOC-SRS-QP-FR-001 1.0.1 và PRD 1.0.1: `US-UPG-07` liên kết `FR-UPG-ACK-001` (P0, đề xuất `CR-FR-01`; đã kiểm ở `AC-UPG-22` bước `migrate ack`), thêm dòng FR này vào §6, §2 `UPG` phủ 20 FR, tổng 168 FR (Phase 1: 159, P0 136); `US-JOB-06` và dòng `FR-JOB-LOG-002` ở §6 thêm `AC-JOB-25` (tách từ `AC-JOB-18` ở acceptance-criteria-job-flt.md 1.0.1), §2 `JOB` 25 scenario, tổng 373; §6 chép lại nguyên văn 27 tên FR đổi theo `CR-FR-06`; §1.4 `PER-04` đổi Secondary → Primary (chỉ đọc, xuất báo cáo) theo PRD §2.1; §7 thêm `CR-FR-01`; §8 cập nhật phiên bản nguồn. Story point không đổi (455 SP) |

## 1. Giới thiệu

### 1.1 Mục đích
Tài liệu bóc tách 35 use case (DOC-UC-QP-000) và 168 FR (DOC-SRS-QP-FR-001 bản 1.0.1) của php-quickpatch v2 thành user story sẵn sàng đưa vào sprint backlog: câu chuẩn Connextra, kiểm tra INVEST (rule 07), story point, ưu tiên P0/P1/P2, phase, FR và AC liên kết. Người đọc: PO (sắp xếp backlog, duyệt câu hỏi mở), Dev (ước lượng, chia sprint), QA (viết test case `TC-*` từ AC theo rule 14).

### 1.2 Phạm vi và nguồn mã
- Phạm vi: toàn bộ FR Phase 1 (159 FR: P0 136, P1 20, P2 3) và Phase 2 (9 FR, chỉ đặc tả) của DOC-SRS-QP-FR-001 bản 1.0.1. `FR-UPG-ACK-001` (P0) đang ở trạng thái đề xuất chờ PO duyệt `CR-FR-01`; PO từ chối → gỡ FR này khỏi `US-UPG-07` và §6, tổng trở về 167 FR (Phase 1: 158, P0 135). Phase 2 và FR P2 được viết ở **mức epic** (cột Story ID có nhãn **[Epic]**), phải tách thành story ≤ 5 SP trước khi đưa vào sprint.
- Mã `FR-*`, `BR-*`, `ERR-*`, `NFR-*`, `UC-*`, `SCR-*` lấy từ registry của SRS (DOC-SRS-QP-001 và 4 file chi tiết). Mã `US-*` và `AC-*` được định nghĩa lần đầu tại bộ tài liệu này.
- Ngoài phạm vi: test case `TC-*` (bước `/test-case` sau), thiết kế giao diện chi tiết (đã có ở `html-wireframe/`).

### 1.3 Quy ước
| Mục | Quy ước |
| :--- | :--- |
| Mã story | `US-[MODULE]-NN`; `MODULE` trùng tiền tố FR của SRS (`SCAN`, `SCN`, `FEED`, `ASMT`, `PLAN`, `CMPT`, `PTCH`, `UPG`, `CON`, `JOB`, `CLI`, `RPT`, `FLT`); `NN` 2 chữ số, tăng dần trong module |
| Mã acceptance criteria | `AC-[MODULE]-NN`, 1 mã cho 1 scenario Gherkin, đánh số liên tục trong module theo thứ tự story; mỗi story có ≥ 3 scenario: happy path, negative path có mã `ERR-*`, boundary/security (rule 08) |
| Câu story | `Là một [actor], tôi muốn [hành động] để [giá trị]` (rule 07 §1); giá trị gắn với KR/NFR định lượng của PRD/SRS khi có |
| Story point | Thang Fibonacci 1, 2, 3, 5, 8 (dải 1–8). Mốc so sánh: `US-SCAN-04` = 2 SP (1 FR, 1 lệnh đọc, 1 trường JSON); `US-UPG-04` = 8 SP (12 bước, 4 nhánh lỗi, cần môi trường kiểm thử có web server). Story 8 SP được đánh dấu "Đạt có điều kiện" ở cột S của INVEST |
| Ưu tiên | Theo PRD §4.1, xét trong phase của story: **P0 (Must)** bắt buộc để phát hành phase; **P1 (Should)** được lùi tối đa 1 bản minor; **P2 (Nice to have)** được lùi sang đợt sau. Ưu tiên story = mức cao nhất trong các FR liên kết |
| Phase | `1` = cục bộ trên máy chủ được quản lý (triển khai); `2` = máy trung tâm nhiều server qua SSH (chỉ đặc tả) |
| Từ ngữ | Không dùng từ định tính (rule 16); mọi ngưỡng ghi bằng số kèm đơn vị (s, ms, MB, MiB, ngày, lần, ký tự) |

### 1.4 Actor dùng trong story (rule 17)
| Actor trong câu story | Mã | Loại | Điều kiện kỹ thuật (spec §2.3) |
| :--- | :--- | :--- | :--- |
| Người vận hành VPS | `PER-01` | Primary | CLI root hoặc console của `serve` chạy root; không root → chỉ cấp dự án (`BR-CLI-005`) |
| Quản trị hosting có panel | `PER-02` | Primary | Như PER-01, thao tác site qua playbook panel PB-007..PB-012 |
| Kỹ sư DevOps quản lý Docker | `PER-03` | Primary | Root hoặc nhóm `docker`; client API/CI đọc `--json` hoặc gọi `/api/v1` bằng Bearer |
| Kỹ sư bảo mật / kiểm toán viên | `PER-04` | Primary (chỉ đọc, xuất báo cáo) | Chỉ xem, xuất báo cáo, kiểm audit; Phase 1 không có vai trò kỹ thuật riêng (dùng token console hoặc CLI). Là Secondary khi chỉ nhận báo cáo do `PER-01`/`PER-02` xuất (PRD 1.0.1 §2.1) |
| Người bảo trì tool vận hành pipeline phát hành | `SYS-05` | System | Pipeline dựng snapshot (`FR-FEED-SNAP-004`) |
| Admin / Operator / Viewer máy trung tâm | — | Primary (Phase 2) | Vai trò tài khoản Phase 2 (`BR-FLT-008`) |

`SYS-01` (cron/systemd timer) là actor thực thi của `US-FEED-15`; `SYS-02`, `SYS-03`, `SYS-04` là actor hỗ trợ xuất hiện trong bước `Given`/`When` của AC.

## 2. Tổng hợp backlog
| Module | Epic | Số story | Story point | P0 | P1 | P2 | Phase | Số FR phủ | Số scenario AC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `SCAN` | Nhận diện & kiểm kê | 5 | 17 | 4 | 1 | 0 | 1 | 8 | 15 |
| `SCN` | Kịch bản phiên bản & checklist | 5 | 19 | 5 | 0 | 0 | 1 | 7 | 16 |
| `FEED` | Dữ liệu CVE / vòng đời online | 17 | 62 | 15 | 1 | 1 | 1 | 35 | 53 |
| `ASMT` | Đánh giá bảo mật | 6 | 20 | 6 | 0 | 0 | 1 | 9 | 19 |
| `PLAN` | Kế hoạch nâng cấp | 8 | 29 | 8 | 0 | 0 | 1 | 8 | 26 |
| `CMPT` | Quét tương thích | 11 | 40 | 8 | 2 | 1 | 1 | 14 | 33 |
| `PTCH` | Vá cùng nhánh (kế thừa v0.1) | 9 | 28 | 9 | 0 | 0 | 1 | 14 | 28 |
| `UPG` | Nâng cấp khác nhánh / chuyển site | 15 | 72 | 12 | 2 | 1 | 1 | 20 | 47 |
| `CON` | Web console Phase 1 | 19 | 66 | 18 | 1 | 0 | 1 | 22 | 60 |
| `JOB` | Job runner, log, audit | 8 | 28 | 8 | 0 | 0 | 1 | 10 | 25 |
| `CLI` | Giao diện dòng lệnh | 10 | 31 | 9 | 1 | 0 | 1 | 10 | 30 |
| `RPT` | Báo cáo | 2 | 6 | 0 | 2 | 0 | 1 | 2 | 6 |
| `FLT` | Quản lý nhiều server (Phase 2) | 5 | 37 | 4 | 1 | 0 | 2 | 9 | 15 |
| **Tổng** | | **120** | **455** | **106** | **11** | **3** | | **168** | **373** |

Phân lớp phát hành theo ưu tiên:

| Lớp | Số story | Story point | Điều kiện phát hành |
| :--- | :---: | :---: | :--- |
| Phase 1 — P0 (bắt buộc cho bản 2.0.0) | 102 | 373 | 100% AC của story P0 đạt; mỗi FR P0 có ≥ 1 test case truy vết được (`NFR-MNT-004`) |
| Phase 1 — P1 | 10 | 34 | Được lùi tối đa 1 bản minor (2.1.0) |
| Phase 1 — P2 (mức epic) | 3 | 11 | Chờ PO trả lời `Q-02` (Rector); lùi sang đợt sau |
| Phase 2 (mức epic) | 5 | 37 | Chỉ đặc tả; tách story trước khi lập kế hoạch Phase 2 |

## 3. Thứ tự phụ thuộc đề xuất
Story được viết để phát triển và kiểm thử độc lập bằng dữ liệu mẫu (bundle cố định ngày 2026-10-22, `last-scan.json` mẫu, manifest mẫu). Thứ tự dưới chỉ là thứ tự **tích hợp** để giảm stub:

| Đợt | Nhóm story | Lý do |
| :---: | :--- | :--- |
| 1 | `US-CLI-03`, `US-CLI-10`, `US-CLI-01`, `US-SCAN-01..04`, `US-FEED-11`, `US-FEED-12`, `US-FEED-01..09` | Nền tảng: giữ hành vi v0.1, envelope `--json`, kiểm kê, dữ liệu online thay mảng ghi cứng |
| 2 | `US-FEED-10`, `US-CLI-04`, `US-SCN-01..05`, `US-ASMT-01..06`, `US-PTCH-01..09`, `US-JOB-07` | Đánh giá, vá cùng nhánh, manifest, audit — thay thế 100% chức năng `scan`/`fix`/`rollback` của v0.1 |
| 3 | `US-JOB-01..06`, `US-CON-01..05`, `US-CON-16..19` | Lõi console: xác thực, bảo vệ thao tác, job runner, SSE |
| 4 | `US-CMPT-01..10`, `US-PLAN-01..08`, `US-UPG-01..12`, `US-CLI-05..09` | Kế hoạch, quét tương thích, cài song song, chuyển site, health check, rollback site |
| 5 | `US-CON-06..15`, `US-FEED-13..16`, `US-JOB-08`, `US-RPT-01..02`, `US-SCAN-05`, `US-CLI-02`, `US-UPG-13..14` | Màn hình console, snapshot, báo cáo, P1 |
| 6 | `US-FEED-17`, `US-CMPT-11`, `US-UPG-15`, `US-FLT-01..05` | P2 và Phase 2 (mức epic) |

## 4. Backlog theo epic (template 27)
Cột "Acceptance Criteria" liệt kê dải mã AC; nội dung Gherkin ở [acceptance-criteria.md](acceptance-criteria.md) và các file tách được liệt kê tại §2 của tài liệu đó.

### 4.1 — Nhận diện & kiểm kê (`SCAN`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-SCAN-01` | Nhận diện & kiểm kê | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **tool tự nhận diện môi trường (container, panel, distro, web server) để chọn playbook và lập bảng site → runtime trong ≤ 5 s với ≤ 200 vhost** để **biết site nào đang dùng binary PHP nào trước khi vá hoặc chuyển nhánh mà không phải đọc tay từng vhost**. | 5 | P0 | 1 | `FR-SCAN-ENV-001`, `FR-SCAN-MAP-001` | `UC-SCAN-001` | `AC-SCAN-01`..`AC-SCAN-03` |
| `US-SCAN-02` | Nhận diện & kiểm kê | Là một **người vận hành VPS (PER-01)**, tôi muốn **phát hiện mọi binary PHP và Node.js trên máy chủ kèm phiên bản, SAPI, gói sở hữu, nguồn cài và trạng thái vá** để **không bỏ sót runtime nào khi đánh giá CVE, kể cả bản do panel, nvm hoặc tự build cài**. | 5 | P0 | 1 | `FR-SCAN-RT-001`, `FR-SCAN-RT-002` | `UC-SCAN-001` | `AC-SCAN-04`..`AC-SCAN-06` |
| `US-SCAN-03` | Nhận diện & kiểm kê | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **kiểm kê dự án Composer/npm/WordPress/Dockerfile/compose (sâu tối đa 7 cấp thư mục) và container đang chạy** để **biết lockfile, image và container nào cần đánh giá lỗ hổng thư viện và base image**. | 3 | P0 | 1 | `FR-SCAN-PRJ-001`, `FR-SCAN-PRJ-002` | `UC-SCAN-001` | `AC-SCAN-07`..`AC-SCAN-09` |
| `US-SCAN-04` | Nhận diện & kiểm kê | Là một **người vận hành VPS (PER-01)**, tôi muốn **nhận danh sách file nghi webshell kèm SHA-256, `mtime`, kích thước mà tool không xoá, sửa, đổi quyền hay di chuyển file** để **xử lý sự cố xâm nhập theo quy trình riêng với bằng chứng còn nguyên trạng**. | 2 | P0 | 1 | `FR-SCAN-WSH-001` | `UC-SCAN-001` | `AC-SCAN-10`..`AC-SCAN-12` |
| `US-SCAN-05` | Nhận diện & kiểm kê | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **được cảnh báo khi site đang dùng nhánh/vị trí gán khác lượt chuyển `PASSED` gần nhất do tool thực hiện** để **phát hiện công cụ quản lý cấu hình hoặc panel ghi đè vhost trước khi chạy lượt chuyển kế tiếp**. | 2 | P1 | 1 | `FR-SCAN-DRF-001` | `UC-SCAN-001` | `AC-SCAN-13`..`AC-SCAN-15` |

### 4.2 — Kịch bản phiên bản & checklist (`SCN`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-SCN-01` | Kịch bản phiên bản & checklist | Là một **người vận hành VPS (PER-01)**, tôi muốn **mỗi runtime được gán đúng 1 kịch bản `VERSION` (cộng 0..n `OVERLAY` theo nguồn cài) và runtime có phiên bản bất thường bị khoá tự động hoá** để **nhận đúng checklist cho PHP 4.x–8.5 và Node.js ≤ 16–26, và tool không bao giờ tự vá/chuyển một binary không nhận diện được (vd chuỗi "6.x")**. | 5 | P0 | 1 | `FR-SCN-CLS-001`, `FR-SCN-CLS-002`, `FR-SCN-LOCK-001` | `UC-SCAN-001` | `AC-SCN-01`..`AC-SCN-04` |
| `US-SCN-02` | Kịch bản phiên bản & checklist | Là một **người vận hành VPS (PER-01)**, tôi muốn **trạng thái hỗ trợ (`ACTIVE`, `SECURITY_ONLY`, `ACTIVE_LTS`, `MAINTENANCE_LTS`, `CURRENT`, `EOL`, `PRE_RELEASE`, `UNKNOWN`), số ngày tới EOL và mức ưu tiên được tính tại thời điểm chạy** để **quyết định vá hay nâng nhánh dựa trên dữ liệu vòng đời của ngày chạy (UTC), không dựa vào giá trị ghi cứng**. | 3 | P0 | 1 | `FR-SCN-LIFE-001` | `UC-SCAN-001` | `AC-SCN-05`..`AC-SCN-07` |
| `US-SCN-03` | Kịch bản phiên bản & checklist | Là một **người vận hành VPS (PER-01)**, tôi muốn **catalog kịch bản, checklist, playbook, luật breaking change và mitigation được nạp từ gói dữ liệu có `SHA256SUMS` và cập nhật được qua snapshot** để **nhận kịch bản và luật mới mà không chờ bản script mới (0 dòng sửa trong `php-quickpatch.sh`, NFR-MNT-001)**. | 3 | P0 | 1 | `FR-SCN-CAT-001` | `UC-SCAN-001`, `UC-FEED-004` | `AC-SCN-08`..`AC-SCN-10` |
| `US-SCN-04` | Kịch bản phiên bản & checklist | Là một **người vận hành VPS (PER-01)**, tôi muốn **checklist hiệu lực của kế hoạch được lắp từ mục `VERSION`, `OVERLAY` và hành động playbook, đã thay biến `$OLD`/`$NEW`/`$SITE` và đánh dấu mục không áp dụng** để **có danh sách bước cho từng site, mỗi bước có lệnh hoặc thao tác và tiêu chí hoàn thành đo được (KR3.3)**. | 5 | P0 | 1 | `FR-SCN-CHK-001` | `UC-PLAN-001` | `AC-SCN-11`..`AC-SCN-13` |
| `US-SCN-05` | Kịch bản phiên bản & checklist | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **tool tự giới hạn thao tác theo môi trường: không root → chỉ cấp dự án; trong container → chỉ mitigation; `PB-000` → chỉ mitigation và hướng dẫn** để **không có lệnh nào chạy ngoài quyền tiến trình hoặc ngoài phạm vi playbook đã nhận diện**. | 3 | P0 | 1 | `FR-SCN-ENV-001` | `UC-SCAN-001` | `AC-SCN-14`..`AC-SCN-16` |

### 4.3 — Dữ liệu CVE / vòng đời online (`FEED`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-FEED-01` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **chạy `feeds update` (bí danh `sync`) để đồng bộ các nguồn quá TTL trong ngân sách 900 s (đầy đủ) / 180 s (tăng dần) và nhận tóm tắt kèm mã thoát 0/1/2** để **dữ liệu CVE/KEV/vòng đời dùng để đánh giá có tuổi ≤ 6 giờ 15 phút khi máy chủ có mạng (KR1.1)**. | 5 | P0 | 1 | `FR-FEED-CMD-001`, `FR-FEED-SYNC-001` | `UC-FEED-001` | `AC-FEED-01`..`AC-FEED-04` |
| `US-FEED-02` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **đồng bộ vòng đời PHP 4.4, 5.0–8.5 và Node.js 0.8–27 kèm ma trận framework/CMS ↔ PHP** để **trạng thái EOL/LTS và nhánh đích đề xuất dựa trên ngày chính thức của php.net, nodejs/Release và endoflife.date (KR5.1)**. | 3 | P0 | 1 | `FR-FEED-EOL-001`, `FR-FEED-EOL-002`, `FR-FEED-EOL-003` | `UC-FEED-001` | `AC-FEED-05`..`AC-FEED-07` |
| `US-FEED-03` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **đồng bộ bản phát hành mới nhất mỗi nhánh PHP, Node.js và trạng thái từng bản WordPress core** để **mốc vá lấy từ php.net, nodejs.org, wordpress.org thay cho trường `latest` chậm của endoflife.date (BR-DATA-002)**. | 3 | P0 | 1 | `FR-FEED-REL-001`, `FR-FEED-REL-002`, `FR-FEED-REL-003` | `UC-FEED-001` | `AC-FEED-08`..`AC-FEED-10` |
| `US-FEED-04` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **đồng bộ CVE PHP core từ NVD (truy vấn CPE và truy vấn CNA php.net), tra CVE.org khi NVD thiếu và làm giàu alias GHSA ↔ CVE** để **không bỏ sót CVE php-src, kể cả CVE mà OSV không có bản ghi**. | 5 | P0 | 1 | `FR-FEED-PCVE-001`, `FR-FEED-PCVE-002`, `FR-FEED-PCVE-003` | `UC-FEED-001` | `AC-FEED-11`..`AC-FEED-13` |
| `US-FEED-05` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **đồng bộ CVE Node.js core (Security WG + NVD) và CVE WordPress core (NVD)** để **đánh giá Node.js và WordPress dùng dải ảnh hưởng chính thức thay cho mảng `NODE_FIXED`/`WP_FIXED` ghi cứng**. | 3 | P0 | 1 | `FR-FEED-NCVE-001`, `FR-FEED-WCVE-001` | `UC-FEED-001` | `AC-FEED-14`..`AC-FEED-16` |
| `US-FEED-06` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **mọi advisory có trong CISA KEV được gắn cờ `in_kev` kèm `dueDate`** để **lỗ hổng đang bị khai thác luôn đứng đầu danh sách xử lý (BR-SEC-001)**. | 2 | P0 | 1 | `FR-FEED-KEV-001` | `UC-FEED-001` | `AC-FEED-17`..`AC-FEED-19` |
| `US-FEED-07` | Dữ liệu CVE / vòng đời online | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **tra OSV theo lô ≤ 500 package cho mỗi lockfile Composer/npm với cache 6 giờ theo SHA-256 lockfile** để **phát hiện package có lỗ hổng và mã độc `MAL-*` mà không gửi lặp cùng truy vấn trong 6 giờ**. | 3 | P0 | 1 | `FR-FEED-OSV-001` | `UC-ASMT-002` | `AC-FEED-20`..`AC-FEED-22` |
| `US-FEED-08` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **trạng thái vá của gói PHP/Node.js distro được xác định qua OSV distro, tracker distro và changelog gói** để **gói Ubuntu/Debian/RHEL đã backport bản vá được gắn `ok-backport` thay vì bị báo `vulnerable` theo số phiên bản upstream**. | 5 | P0 | 1 | `FR-FEED-DIST-001`, `FR-FEED-DIST-002`, `FR-FEED-NORM-003` | `UC-SCAN-001`, `UC-FEED-001` | `AC-FEED-23`..`AC-FEED-25` |
| `US-FEED-09` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **advisory từ nhiều nguồn được chuẩn hoá, khử trùng lặp và tính `min_patched` theo nhánh** để **mỗi CVE chỉ được đếm 1 lần và mốc vá tái lập đúng 8.2.35/8.3.36/8.4.27/8.5.12 như dữ liệu v0.1 (test hồi quy NFR-MNT-002)**. | 5 | P0 | 1 | `FR-FEED-NORM-001`, `FR-FEED-NORM-002` | `UC-FEED-001` | `AC-FEED-26`..`AC-FEED-28` |
| `US-FEED-10` | Dữ liệu CVE / vòng đời online | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **mọi kết quả (CLI văn bản, `--json`, console, báo cáo) ghi tuổi dữ liệu `data_age_h`, mức độ tươi và nguồn cũ nhất** để **biết kết luận đánh giá dựa trên dữ liệu cũ bao nhiêu giờ trước khi dùng làm bằng chứng**. | 3 | P0 | 1 | `FR-FEED-AGE-001` | `UC-SCAN-001`, `UC-FEED-003` | `AC-FEED-29`..`AC-FEED-31` |
| `US-FEED-11` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **phản hồi gốc của nguồn được cache kèm meta, bundle chuẩn hoá được thay nguyên tử và thư mục `feeds/` được dọn trong giới hạn 60 MB** để **một lần đồng bộ lỗi giữa chừng không làm hỏng dữ liệu đang được `scan` sử dụng**. | 5 | P0 | 1 | `FR-FEED-CACH-001`, `FR-FEED-CACH-002`, `FR-FEED-CACH-003` | `UC-FEED-001` | `AC-FEED-32`..`AC-FEED-34` |
| `US-FEED-12` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **tool dựng dữ liệu ban đầu từ snapshot đóng gói đã kiểm SHA-256 khi chưa có bundle hoặc khi snapshot mới hơn bundle** để **`scan` cho kết quả ngay lần chạy đầu, kể cả trên máy chủ không ra Internet**. | 3 | P0 | 1 | `FR-FEED-SNAP-001` | `UC-FEED-004` | `AC-FEED-35`..`AC-FEED-37` |
| `US-FEED-13` | Dữ liệu CVE / vòng đời online | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **xuất snapshot ở máy có mạng bằng `feeds export` và nhập vào máy không ra Internet bằng `feeds import FILE --sha256 HEX`** để **máy chủ cách ly mạng vẫn có dữ liệu CVE/KEV tuổi ≤ 7 ngày**. | 5 | P0 | 1 | `FR-FEED-SNAP-002`, `FR-FEED-SNAP-003`, `FR-FEED-CMD-004`, `FR-FEED-CMD-005` | `UC-FEED-004` | `AC-FEED-38`..`AC-FEED-41` |
| `US-FEED-14` | Dữ liệu CVE / vòng đời online | Là một **người bảo trì tool vận hành pipeline phát hành (SYS-05)**, tôi muốn **pipeline phát hành dựng snapshot `standard`, ghi `QP_SNAPSHOT_SHA256` và chặn phát hành khi snapshot > 7 ngày hoặc có nguồn P0 không `OK`** để **mọi bản tool phát hành kèm dữ liệu offline đạt KR5.1 và KR5.2**. | 3 | P0 | 1 | `FR-FEED-SNAP-004` | `UC-FEED-005` | `AC-FEED-42`..`AC-FEED-44` |
| `US-FEED-15` | Dữ liệu CVE / vòng đời online | Là một **người vận hành VPS (PER-01)**, tôi muốn **cài đúng 1 lịch đồng bộ (systemd timer hoặc cron) chu kỳ N ∈ {1, 2, 3, 4, 6, 8, 12, 24} giờ, mặc định 6 giờ, bằng `feeds schedule`** để **SYS-01 tự giữ dữ liệu tươi mà không cần chạy tay `feeds update`**. | 3 | P1 | 1 | `FR-FEED-SCHD-001`, `FR-FEED-CMD-006` | `UC-FEED-002` | `AC-FEED-45`..`AC-FEED-47` |
| `US-FEED-16` | Dữ liệu CVE / vòng đời online | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **xem trạng thái từng nguồn (`OK`/`DEGRADED`/`FAILED`/`DISABLED`), tuổi, TTL, lỗi cuối bằng `feeds status` và kiểm toàn vẹn bundle bằng `feeds verify`** để **xác nhận 100% file của bundle khớp `SHA256SUMS` trước khi dùng làm bằng chứng kiểm toán**. | 3 | P0 | 1 | `FR-FEED-CMD-002`, `FR-FEED-CMD-003` | `UC-FEED-003` | `AC-FEED-48`..`AC-FEED-50` |
| `US-FEED-17` **[Epic]** | Dữ liệu CVE / vòng đời online | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **bật nguồn lỗ hổng WordPress cần key (`SRC-013`) khi tôi khai báo key trong file cấu hình quyền `0600`** để **bổ sung advisory plugin/theme WordPress ngoài CVE core**. | 3 | P2 | 1 | `FR-FEED-WCVE-002` | `UC-FEED-001` | `AC-FEED-51`..`AC-FEED-53` |

### 4.4 — Đánh giá bảo mật (`ASMT`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-ASMT-01` | Đánh giá bảo mật | Là một **người vận hành VPS (PER-01)**, tôi muốn **xem đánh giá runtime hiện tại: số CVE chưa vá theo mức CVSS v3.1, số KEV, trạng thái hỗ trợ, ngày EOL, bản patch mới nhất, `min_patched` và điểm rủi ro `R` 0–100 có thành phần** để **biết runtime nào phải xử lý trong ≤ 24 giờ (`CRITICAL`) hay ≤ 7 ngày (`HIGH`)**. | 5 | P0 | 1 | `FR-ASMT-CUR-001`, `FR-ASMT-RISK-001` | `UC-ASMT-001` | `AC-ASMT-01`..`AC-ASMT-04` |
| `US-ASMT-02` | Đánh giá bảo mật | Là một **người vận hành VPS (PER-01)**, tôi muốn **xem 4 loại phiên bản ứng viên (`SAME_BRANCH_LATEST`, `NEXT_SUPPORTED`, `RECOMMENDED`, `LATEST_STABLE`) kèm khả năng cài trên máy chủ** để **chọn đích nâng cấp cài được bằng kho/panel đang có**. | 5 | P0 | 1 | `FR-ASMT-CAND-001`, `FR-ASMT-CAND-002` | `UC-ASMT-001` | `AC-ASMT-05`..`AC-ASMT-07` |
| `US-ASMT-03` | Đánh giá bảo mật | Là một **người vận hành VPS (PER-01)**, tôi muốn **so sánh song song hiện tại với từng ứng viên trên cùng `bundle_id`, cùng ngày `T`, gồm `R` và `ΔR`** để **thấy định lượng lợi ích bảo mật của vá cùng nhánh so với nâng nhánh**. | 3 | P0 | 1 | `FR-ASMT-CMP-001`, `FR-ASMT-RISK-002` | `UC-ASMT-001` | `AC-ASMT-08`..`AC-ASMT-10` |
| `US-ASMT-04` | Đánh giá bảo mật | Là một **người vận hành VPS (PER-01)**, tôi muốn **danh sách xử lý được xếp theo `R` giảm dần, cùng `R` thì theo KEV → `cvss_max` ≥ 9,0 → EOL → `cvss_max` 7,0–8,9 → EOL ≤ 90 ngày** để **xử lý đúng thứ tự rủi ro trên máy chủ có nhiều runtime và dự án**. | 2 | P0 | 1 | `FR-ASMT-RANK-001` | `UC-ASMT-001`, `UC-CON-002` | `AC-ASMT-11`..`AC-ASMT-13` |
| `US-ASMT-05` | Đánh giá bảo mật | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **nhận findings Composer/npm theo dự án gồm advisory, mức, KEV, `MAL-*` và phiên bản sửa** để **đưa package lỗ hổng vào lượt vá và gỡ package mã độc**. | 3 | P0 | 1 | `FR-ASMT-DEP-001` | `UC-ASMT-002` | `AC-ASMT-14`..`AC-ASMT-16` |
| `US-ASMT-06` | Đánh giá bảo mật | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **đánh giá phiên bản WordPress core của từng site so với `min_patched` của wordpress.org kèm cờ KEV** để **biết site WordPress nào còn dưới mốc vá (vd 7.0.2 còn CVE-2026-87902 thuộc KEV)**. | 2 | P0 | 1 | `FR-ASMT-DEP-002` | `UC-ASMT-002` | `AC-ASMT-17`..`AC-ASMT-19` |

### 4.5 — Kế hoạch nâng cấp (`PLAN`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-PLAN-01` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **chọn phiên bản đích từ ứng viên `selectable`, bị chặn với nhánh `EOL`/`PRE_RELEASE`/`UNKNOWN`/"6.x" và phải ghi lý do ≥ 20 ký tự khi khác đề xuất** để **kế hoạch không bao giờ đưa site production sang nhánh bị cấm**. | 3 | P0 | 1 | `FR-PLAN-TGT-001` | `UC-PLAN-001` | `AC-PLAN-01`..`AC-PLAN-04` |
| `US-PLAN-02` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **sinh kế hoạch nâng cấp ở trạng thái `draft` gồm checklist theo site, mục vá cùng nhánh đứng trước (khi có), hạn duyệt và dấu vân tay đầu vào** để **có kế hoạch gồm checklist của mọi site trong ≤ 120 s cho site ≤ 10.000 file `.php` (KR3.2) và phát hiện được khi hiện trạng máy chủ thay đổi**. | 5 | P0 | 1 | `FR-PLAN-GEN-001` | `UC-PLAN-001` | `AC-PLAN-05`..`AC-PLAN-07` |
| `US-PLAN-03` | Kế hoạch nâng cấp | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **kế hoạch tự sắp thứ tự chuyển site (ít file `*.php` trước) với site đầu là canary và liệt kê site bị chặn** để **lỗi tương thích lộ ra trên 1 site trước khi ảnh hưởng các site còn lại**. | 3 | P0 | 1 | `FR-PLAN-GEN-002` | `UC-PLAN-001` | `AC-PLAN-08`..`AC-PLAN-10` |
| `US-PLAN-04` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **nhận danh sách extension, Composer package, npm package, native addon, framework/CMS, loader phải nâng kèm phiên bản tối thiểu tương thích và mục checklist P4 tương ứng** để **lập trình viên biết thư viện nào phải nâng và lên phiên bản tối thiểu nào trước khi chuyển site**. | 3 | P0 | 1 | `FR-PLAN-DEP-001` | `UC-PLAN-001` | `AC-PLAN-11`..`AC-PLAN-13` |
| `US-PLAN-05` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **cập nhật trạng thái mục checklist (`start`, `done`, `fail`, `skip`, `waive`) kèm lý do/bằng chứng, có kiểm phụ thuộc** để **tiến độ kế hoạch phản ánh đúng thực tế và mỗi mục thủ công có bằng chứng**. | 3 | P0 | 1 | `FR-PLAN-CHK-001` | `UC-PLAN-003` | `AC-PLAN-14`..`AC-PLAN-16` |
| `US-PLAN-06` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **chạy mục `AUTO`/`SEMI` bằng job có dry-run + xác nhận, trạng thái mục cập nhật theo kết quả job** để **thực hiện checklist không phải gõ lệnh và mọi thay đổi đi qua cùng đường thực thi có manifest/audit**. | 5 | P0 | 1 | `FR-PLAN-CHK-002` | `UC-PLAN-003` | `AC-PLAN-17`..`AC-PLAN-19` |
| `US-PLAN-07` | Kế hoạch nâng cấp | Là một **người vận hành VPS (PER-01)**, tôi muốn **duyệt, bắt đầu, hoàn tất, huỷ kế hoạch theo máy trạng thái DIAG-STATE-QP-PLAN-001 và bị chặn khi kế hoạch lỗi thời** để **chỉ kế hoạch đủ điều kiện và còn khớp hiện trạng máy chủ mới được thực thi**. | 5 | P0 | 1 | `FR-PLAN-STS-001` | `UC-PLAN-002` | `AC-PLAN-20`..`AC-PLAN-23` |
| `US-PLAN-08` | Kế hoạch nâng cấp | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **thấy hạn duyệt kế hoạch (EOL − 30 ngày) và số ngày còn lại của runtime `SECURITY_ONLY`/`MAINTENANCE_LTS` hoặc còn ≤ 90 ngày tới EOL** để **100% runtime PHP 8.2 có kế hoạch `approved` trước 2026-12-01 (KR2.2)**. | 2 | P0 | 1 | `FR-PLAN-DL-001` | `UC-PLAN-001`, `UC-CON-002` | `AC-PLAN-24`..`AC-PLAN-26` |

### 4.6 — Quét tương thích (`CMPT`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-CMPT-01` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **công cụ quét (PHPCompatibility, PHP_CodeSniffer, Composer, Rector) được cài vào `STATE_DIR/tools/php` với phiên bản và hash cố định theo catalog** để **kết quả quét tái lập được và không có mã thực thi tải về chưa kiểm hash**. | 3 | P0 | 1 | `FR-CMPT-TOOL-001` | `UC-PLAN-001` | `AC-CMPT-01`..`AC-CMPT-03` |
| `US-CMPT-02` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **quét luật breaking change của catalog trong dải `($OLD, $NEW]` ngay cả khi chưa cài `$NEW`** để **ước lượng khối lượng sửa mã trước khi quyết định cài nhánh đích**. | 3 | P0 | 1 | `FR-CMPT-CODE-001` | `UC-PLAN-001` | `AC-CMPT-04`..`AC-CMPT-06` |
| `US-CMPT-03` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **quét PHPCompatibility với `testVersion` = `$NEW` (WordPress dùng `PHPCompatibilityWP`)** để **phát hiện hàm/cú pháp bị gỡ mà luật `grep` tĩnh không bắt được**. | 5 | P0 | 1 | `FR-CMPT-CODE-002` | `UC-PLAN-001` | `AC-CMPT-07`..`AC-CMPT-09` |
| `US-CMPT-04` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **kiểm tra cú pháp 100% file `*.php`, `*.inc`, `*.phtml` bằng `$NEW_BIN -l` sau khi cài nhánh đích** để **đạt 0 `Parse error` trước khi chuyển site (BR-SCN-042)**. | 2 | P0 | 1 | `FR-CMPT-CODE-003` | `UC-PLAN-003` | `AC-CMPT-10`..`AC-CMPT-12` |
| `US-CMPT-05` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **phân tích ràng buộc `require.php`/`require.ext-*` của Composer trên bản sao và tra phiên bản tối thiểu tương thích trên Packagist** để **biết package nào chặn nâng nhánh và phải nâng lên bản nào**. | 5 | P0 | 1 | `FR-CMPT-COMP-001`, `FR-CMPT-COMP-002` | `UC-PLAN-001` | `AC-CMPT-13`..`AC-CMPT-15` |
| `US-CMPT-06` | Quét tương thích | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **quét `engines.node` của ứng dụng/lockfile và nạp thử native addon bằng `$NEW_BIN` trên bản sao** để **ứng dụng Node.js không lỗi ABI hoặc `engines` sau khi đổi major**. | 5 | P1 | 1 | `FR-CMPT-NPM-001`, `FR-CMPT-NPM-002` | `UC-PLAN-001` | `AC-CMPT-16`..`AC-CMPT-18` |
| `US-CMPT-07` | Quét tương thích | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **liệt kê directive ini bị gỡ trong dải nâng cấp và đối chiếu extension của `$OLD` trên `$NEW`** để **pool/ini đích khởi động không lỗi và site không thiếu extension đang gọi**. | 3 | P0 | 1 | `FR-CMPT-INI-001`, `FR-CMPT-EXT-001` | `UC-PLAN-001` | `AC-CMPT-19`..`AC-CMPT-21` |
| `US-CMPT-08` | Quét tương thích | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **nhận diện loader mã hoá ionCube/SourceGuardian/Zend Guard và loại nhánh đích không có loader chính thức** để **không chuyển site dùng mã hoá sang nhánh làm site ngừng chạy**. | 3 | P0 | 1 | `FR-CMPT-LDR-001` | `UC-PLAN-001` | `AC-CMPT-22`..`AC-CMPT-24` |
| `US-CMPT-09` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **nhận diện framework/CMS và phiên bản của site, đối chiếu dải PHP hỗ trợ** để **nhánh đích nằm trong dải hỗ trợ của Laravel/Symfony/WordPress/Drupal/Magento/CodeIgniter/Joomla mà site dùng**. | 3 | P1 | 1 | `FR-CMPT-FWK-001` | `UC-PLAN-001` | `AC-CMPT-25`..`AC-CMPT-27` |
| `US-CMPT-10` | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **mỗi site có kết luận tương thích `PASS`/`FAIL`/`PENDING` tổng hợp từ mọi bước quét và miễn trừ được từng hit kèm lý do** để **chỉ site `PASS` mới được chuyển (BR-UPG-002)**. | 3 | P0 | 1 | `FR-CMPT-RES-001` | `UC-PLAN-001` | `AC-CMPT-28`..`AC-CMPT-30` |
| `US-CMPT-11` **[Epic]** | Quét tương thích | Là một **người vận hành VPS (PER-01)**, tôi muốn **tuỳ chọn chạy Rector trên bản sao mã nguồn ngoài docroot và xem diff trước khi ghi vào bản sao** để **lập trình viên có bản sửa gợi ý mà tool không ghi vào docroot production**. | 5 | P2 | 1 | `FR-CMPT-RCT-001` | `UC-PLAN-003` | `AC-CMPT-31`..`AC-CMPT-33` |

### 4.7 — Vá cùng nhánh (kế thừa v0.1) (`PTCH`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-PTCH-01` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **vá runtime PHP lên bản patch mới nhất cùng nhánh qua đúng nhóm gói theo nguồn cài (dpkg/rpm/apk, `ea-php`, `alt-php`, `lsphp`, `plesk-php`)** để **đóng CVE thuộc KEV hoặc CVSS ≥ 9,0 trong ≤ 24 giờ (KR1.2) mà không đổi nhánh**. | 5 | P0 | 1 | `FR-PTCH-PHP-001`, `FR-PTCH-PHP-002` | `UC-PTCH-001` | `AC-PTCH-01`..`AC-PTCH-04` |
| `US-PTCH-02` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **tool ghi mitigation ini tạm thời khi runtime chưa vá được và tự gỡ mitigation khi runtime đã vá** để **giảm bề mặt tấn công trong lúc chờ kho phát hành bản vá mà không để lại cấu hình tạm**. | 3 | P0 | 1 | `FR-PTCH-MIT-001`, `FR-PTCH-MIT-002` | `UC-PTCH-001` | `AC-PTCH-05`..`AC-PTCH-07` |
| `US-PTCH-03` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **vá Node.js lên bản mới nhất cùng major theo nguồn cài (gói/NodeSource, tarball có kiểm `SHASUMS256.txt`, nvm)** để **đóng CVE Node.js core mà không đổi major ứng dụng đang dùng**. | 3 | P0 | 1 | `FR-PTCH-NODE-001` | `UC-PTCH-001` | `AC-PTCH-08`..`AC-PTCH-10` |
| `US-PTCH-04` | Vá cùng nhánh (kế thừa v0.1) | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **cập nhật package Composer/npm có lỗ hổng dưới quyền chủ thư mục và khôi phục lockfile khi lệnh lỗi** để **dự án hết lỗ hổng đã biết mà không bị hỏng cây dependency**. | 3 | P0 | 1 | `FR-PTCH-DEP-001`, `FR-PTCH-DEP-002` | `UC-PTCH-002` | `AC-PTCH-11`..`AC-PTCH-13` |
| `US-PTCH-05` | Vá cùng nhánh (kế thừa v0.1) | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **cập nhật WordPress core (minor) và plugin (patch) rồi kiểm checksum core/plugin** để **site lên trên `min_patched` và phát hiện được file core bị sửa**. | 3 | P0 | 1 | `FR-PTCH-WP-001`, `FR-PTCH-WP-002` | `UC-PTCH-002` | `AC-PTCH-14`..`AC-PTCH-16` |
| `US-PTCH-06` | Vá cùng nhánh (kế thừa v0.1) | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **nâng tag image `php:`/`node:` ghim bản cũ lên bản patch mới nhất cùng nhánh và ghi mitigation vào container PHP chưa vá** để **Dockerfile/compose và container không còn bản đã biết lỗ hổng, kèm cảnh báo cần rebuild**. | 3 | P0 | 1 | `FR-PTCH-DKR-001`, `FR-PTCH-DKR-002` | `UC-PTCH-003` | `AC-PTCH-17`..`AC-PTCH-19` |
| `US-PTCH-07` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **dịch vụ PHP-FPM/Node.js bị ảnh hưởng được restart sau vá, gồm unit Remi SCL `php[0-9]+-php-fpm` và `restartsrv` của cPanel** để **bản vá có hiệu lực ngay khi lượt `fix` kết thúc**. | 2 | P0 | 1 | `FR-PTCH-RST-001` | `UC-PTCH-001` | `AC-PTCH-20`..`AC-PTCH-22` |
| `US-PTCH-08` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **mọi thay đổi file/gói/cấu hình của 1 lượt chạy được ghi vào backup manifest trước thay đổi đầu tiên** để **100% lượt thay đổi hoàn tác được (KR4.1, NFR-ENV-05)**. | 3 | P0 | 1 | `FR-PTCH-RBK-001` | `UC-PTCH-001` | `AC-PTCH-23`..`AC-PTCH-25` |
| `US-PTCH-09` | Vá cùng nhánh (kế thừa v0.1) | Là một **người vận hành VPS (PER-01)**, tôi muốn **rollback 1 lượt chạy bằng `rollback [ID]` (mặc định lượt mới nhất)** để **khôi phục 100% file có dòng `copy`/`created` trong manifest của lượt (NFR-REL-005)**. | 3 | P0 | 1 | `FR-PTCH-RBK-002` | `UC-PTCH-004` | `AC-PTCH-26`..`AC-PTCH-28` |

### 4.8 — Nâng cấp khác nhánh / chuyển site (`UPG`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-UPG-01` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **kiểm tiền điều kiện trước cài song song (đĩa trống ≥ 2 GB, RAM khả dụng ≥ 512 MB, quyền, kho có nhánh đích) và trước tạo pool (RAM theo `pm.max_children`)** để **cài/chuyển không làm cạn tài nguyên của các site đang chạy**. | 3 | P0 | 1 | `FR-UPG-PRE-001` | `UC-UPG-001`, `UC-PLAN-001` | `AC-UPG-01`..`AC-UPG-03` |
| `US-UPG-02` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **cài runtime đích song song bản cũ mà liên kết mặc định của hệ thống không đổi** để **các site đang chạy trên `$OLD` không bị ảnh hưởng trong lúc chuẩn bị nâng nhánh**. | 5 | P0 | 1 | `FR-UPG-INST-001` | `UC-UPG-001`, `UC-UPG-005` | `AC-UPG-04`..`AC-UPG-06` |
| `US-UPG-03` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **tạo pool/handler đích riêng cho site và sao chép ini tuỳ chỉnh, extension sang `$NEW` (loại directive bị gỡ)** để **site chuyển sang `$NEW` giữ đúng cấu hình đang dùng**. | 5 | P0 | 1 | `FR-UPG-CFG-001`, `FR-UPG-CFG-002` | `UC-UPG-001` | `AC-UPG-07`..`AC-UPG-09` |
| `US-UPG-04` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **chuyển 1 site sang `$NEW` theo 12 bước C1–C12 có backup, kiểm cú pháp, graceful reload và health check 600 s** để **đổi nhánh PHP cho từng site với đoạn ảnh hưởng request C6–C10 ≤ 30 s ở P95 (NFR-ENV-01)**. | 8 | P0 | 1 | `FR-UPG-SWT-001` | `UC-UPG-002` | `AC-UPG-10`..`AC-UPG-13` |
| `US-UPG-05` | Nâng cấp khác nhánh / chuyển site | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **chuyển site do panel quản lý bằng API/CLI chính thức của panel và đọc lại giá trị sau khi gọi** để **panel không ghi đè thay đổi và gán site của tool luôn khớp với panel**. | 5 | P0 | 1 | `FR-UPG-SWT-002` | `UC-UPG-002` | `AC-UPG-14`..`AC-UPG-16` |
| `US-UPG-06` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **chuyển máy chủ Apache `mod_php` sang PHP-FPM cùng phiên bản với xác nhận kép và health check mọi vhost** để **các site `mod_php` đủ điều kiện để chuyển nhánh từng site**. | 5 | P0 | 1 | `FR-UPG-SWT-003` | `UC-UPG-003` | `AC-UPG-17`..`AC-UPG-19` |
| `US-UPG-07` | Nâng cấp khác nhánh / chuyển site | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **chuyển site tuần tự theo kế hoạch: canary trước, site kế tiếp chỉ mở khi site trước `PASSED`, dừng khi có lượt `ROLLED_BACK` và mở lại sau khi tôi xác nhận đã xử lý lượt lỗi bằng `migrate ack` kèm lý do 20–500 ký tự** để **1 lỗi tương thích ảnh hưởng tối đa 1 site tại một thời điểm**. | 5 | P0 | 1 | `FR-UPG-SEQ-001`, `FR-UPG-ACK-001` (đề xuất, `CR-FR-01`) | `UC-UPG-002` | `AC-UPG-20`..`AC-UPG-23` |
| `US-UPG-08` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **tool tự lập tập URL thăm dò (trang chủ + ≤ 10 URL khai báo) và thu baseline 5 vòng trên `$OLD` ngay trước khi chuyển** để **health check so sánh với hành vi thật của site ngay trước lượt chuyển**. | 5 | P0 | 1 | `FR-UPG-HC-001`, `FR-UPG-HC-003` | `UC-UPG-002` | `AC-UPG-24`..`AC-UPG-26` |
| `US-UPG-09` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **chạy thử mã site trên pool đích bằng FastCGI probe trước khi đổi gán** để **phát hiện `PHP Fatal error`/`Parse error` khi site chưa nhận traffic thật trên `$NEW`**. | 3 | P0 | 1 | `FR-UPG-HC-002` | `UC-UPG-002` | `AC-UPG-27`..`AC-UPG-29` |
| `US-UPG-10` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **health check 600 s với 10 tiêu chí `HC-C0..C9` và báo cáo từng vòng × từng URL trên SCR-006 và `healthcheck --json`** để **có kết luận ĐẠT/KHÔNG ĐẠT định lượng và bằng chứng cho từng lượt chuyển**. | 5 | P0 | 1 | `FR-UPG-HC-004`, `FR-UPG-HC-006` | `UC-UPG-002`, `UC-JOB-001` | `AC-UPG-30`..`AC-UPG-32` |
| `US-UPG-11` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **site tự rollback về `$OLD` khi health check KHÔNG ĐẠT (bắt đầu ≤ 5 s, hoàn tất ≤ 60 s)** để **thời gian site lỗi sau chuyển giới hạn trong ≤ 60 s từ lúc phát hiện (NFR-ENV-03)**. | 5 | P0 | 1 | `FR-UPG-HC-005`, `FR-UPG-RBK-002` | `UC-UPG-002` | `AC-UPG-33`..`AC-UPG-35` |
| `US-UPG-12` | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **rollback 1 site về runtime cũ bằng 1 lệnh `migrate rollback` hoặc 1 nút + 1 xác nhận** để **khôi phục site trong ≤ 60 s ở P95 (KR4.2, NFR-ENV-02)**. | 5 | P0 | 1 | `FR-UPG-RBK-001` | `UC-UPG-004` | `AC-UPG-36`..`AC-UPG-38` |
| `US-UPG-13` | Nâng cấp khác nhánh / chuyển site | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **chuyển ứng dụng Node.js chạy bằng systemd/pm2 sang major mới bằng drop-in/`interpreter` có manifest** để **nâng Node.js từng ứng dụng mà không ghi đè `/usr/bin/node`**. | 5 | P1 | 1 | `FR-UPG-NODE-001` | `UC-UPG-005` | `AC-UPG-39`..`AC-UPG-41` |
| `US-UPG-14` | Nâng cấp khác nhánh / chuyển site | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **chuyển 1 dịch vụ Compose sang image major mới bằng dịch vụ song song sau khi tôi duyệt** để **đổi base image mà tool không tự build/push image ngoài lệnh đã duyệt**. | 5 | P1 | 1 | `FR-UPG-DKR-001` | `UC-UPG-006` | `AC-UPG-42`..`AC-UPG-44` |
| `US-UPG-15` **[Epic]** | Nâng cấp khác nhánh / chuyển site | Là một **người vận hành VPS (PER-01)**, tôi muốn **được đề xuất gỡ runtime cũ khi 14 ngày liên tục không còn site/tiến trình dùng, kèm cảnh báo mất khả năng rollback** để **giải phóng tài nguyên mà không gỡ nhầm runtime còn dùng**. | 3 | P2 | 1 | `FR-UPG-RMV-001` | `UC-UPG-007` | `AC-UPG-45`..`AC-UPG-47` |

### 4.9 — Web console Phase 1 (`CON`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-CON-01` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **chạy `serve` để mở console chỉ trên `127.0.0.1:17321` và nhận đúng 1 lần URL chứa token cùng lệnh SSH tunnel** để **dùng dashboard qua SSH tunnel mà không mở cổng ra mạng và không lưu mật khẩu**. | 5 | P0 | 1 | `FR-CON-AUTH-001`, `FR-CON-AUTH-002` | `UC-CON-001` | `AC-CON-01`..`AC-CON-04` |
| `US-CON-02` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **đăng nhập bằng token để nhận phiên cookie `qp_session` và CSRF token** để **thao tác trên console mà token không đi qua URL gửi lên máy chủ, log hay đĩa**. | 3 | P0 | 1 | `FR-CON-AUTH-003` | `UC-CON-001` | `AC-CON-05`..`AC-CON-07` |
| `US-CON-03` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **mọi request trừ 4 endpoint công khai phải có phiên hoặc Bearer hợp lệ, phiên hết hạn sau 30 phút không hoạt động hoặc 12 giờ, và có đăng xuất** để **phiên bị bỏ quên không thể bị dùng lại**. | 3 | P0 | 1 | `FR-CON-AUTH-004` | `UC-CON-001` | `AC-CON-08`..`AC-CON-10` |
| `US-CON-04` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **console từ chối mọi request có header `Host` ngoài `127.0.0.1:<port>`, `localhost:<port>` và cổng khai báo bằng `--allow-local-port`** để **trang web độc hại không dùng DNS rebinding để gọi API console qua trình duyệt của tôi**. | 2 | P0 | 1 | `FR-CON-AUTH-005` | `UC-CON-001` | `AC-CON-11`..`AC-CON-13` |
| `US-CON-05` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **request ghi xác thực bằng cookie bắt buộc có `X-QP-CSRF`, `Origin` hợp lệ và `Content-Type: application/json`** để **trang khác mở trong trình duyệt không kích hoạt được thao tác thay đổi hệ thống**. | 2 | P0 | 1 | `FR-CON-AUTH-006` | `UC-CON-001` | `AC-CON-14`..`AC-CON-16` |
| `US-CON-06` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **màn hình Tổng quan SCR-002 hiển thị số runtime theo trạng thái, finding KEV/Critical, tuổi dữ liệu, hạn duyệt và cảnh báo lượt chuyển lỗi** để **nắm tình trạng máy chủ trong 1 màn hình hiển thị ≤ 2 s qua tunnel 1 Mbit/s (NFR-PERF-007)**. | 5 | P0 | 1 | `FR-CON-OVW-001` | `UC-CON-002` | `AC-CON-17`..`AC-CON-19` |
| `US-CON-07` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **màn hình Đánh giá runtime SCR-003 hiển thị danh sách CVE, bảng so sánh ứng viên, `ΔR` và nút "Vá cùng nhánh" / "Lập kế hoạch"** để **vá cùng nhánh 1 runtime trong ≤ 3 thao tác (KR1.3, NFR-USE-001)**. | 5 | P0 | 1 | `FR-CON-ASMT-001` | `UC-ASMT-001` | `AC-CON-20`..`AC-CON-22` |
| `US-CON-08` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **chọn runtime → chọn đích → "Sinh kế hoạch" → mở checklist trên SCR-004, thấy tiến độ sinh kế hoạch qua SSE** để **có checklist hoàn chỉnh trong ≤ 4 thao tác, không gõ lệnh (KR3.1, NFR-USE-002)**. | 3 | P0 | 1 | `FR-CON-PLAN-001` | `UC-PLAN-001` | `AC-CON-23`..`AC-CON-25` |
| `US-CON-09` | Web console Phase 1 | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **lọc, chạy, đánh dấu, miễn trừ mục checklist, duyệt kế hoạch, đổi canary và khai báo `hc_url` trên SCR-004** để **điều phối toàn bộ kế hoạch nâng cấp trên 1 màn hình**. | 5 | P0 | 1 | `FR-CON-PLAN-002` | `UC-PLAN-002`, `UC-PLAN-003` | `AC-CON-26`..`AC-CON-28` |
| `US-CON-10` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **xem danh sách job, log trực tiếp, `result.json`, báo cáo health check và huỷ job ngoài vùng tới hạn trên SCR-006** để **theo dõi tiến trình thay đổi mà không mở phiên SSH thứ hai**. | 3 | P0 | 1 | `FR-CON-JOB-001`, `FR-CON-JOB-002` | `UC-JOB-001`, `UC-JOB-002` | `AC-CON-29`..`AC-CON-31` |
| `US-CON-11` | Web console Phase 1 | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **màn hình Findings thư viện SCR-005 nhóm theo dự án, có nút vá dự án qua dry-run + xác nhận** để **xử lý lỗ hổng Composer/npm/WordPress từ console**. | 3 | P0 | 1 | `FR-CON-DEP-001` | `UC-ASMT-002`, `UC-PTCH-002` | `AC-CON-32`..`AC-CON-34` |
| `US-CON-12` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **màn hình Rollback SCR-007 liệt kê lượt chạy và lượt chuyển, cho xem manifest và rollback với 1 xác nhận** để **hoàn tác bằng 1 nút + 1 xác nhận (KR4.2)**. | 3 | P0 | 1 | `FR-CON-RBK-001` | `UC-PTCH-004`, `UC-UPG-004` | `AC-CON-35`..`AC-CON-37` |
| `US-CON-13` | Web console Phase 1 | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **màn hình Nguồn dữ liệu SCR-008 hiển thị trạng thái từng nguồn, nút "Đồng bộ ngay" và tải lên snapshot ≤ 20 MiB kèm SHA-256** để **cập nhật dữ liệu từ console cho cả máy chủ có và không có Internet**. | 5 | P0 | 1 | `FR-CON-FEED-001`, `FR-CON-FEED-002` | `UC-FEED-001`, `UC-FEED-003`, `UC-FEED-004` | `AC-CON-38`..`AC-CON-41` |
| `US-CON-14` | Web console Phase 1 | Là một **quản trị hosting có panel (PER-02)**, tôi muốn **màn hình Site & ánh xạ runtime SCR-009 hiển thị playbook, kiểu gán, nhánh, kết luận tương thích, cảnh báo thay đổi ngoài tool và cho sửa `hc_url`** để **chọn site và chuyển/rollback theo kế hoạch từ cùng 1 bảng**. | 3 | P0 | 1 | `FR-CON-SITE-001` | `UC-UPG-002` | `AC-CON-42`..`AC-CON-44` |
| `US-CON-15` | Web console Phase 1 | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **màn hình Audit SCR-010 lọc bản ghi, kiểm chuỗi hash, tạo và tải báo cáo, không có thao tác sửa/xoá** để **lấy bằng chứng kiểm toán mà không cần quyền shell trên máy chủ**. | 3 | P1 | 1 | `FR-CON-AUD-001` | `UC-JOB-003`, `UC-RPT-001`, `UC-RPT-002` | `AC-CON-45`..`AC-CON-47` |
| `US-CON-16` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **mọi thao tác ghi hiển thị xem trước dry-run đủ 4/4 mục (thay đổi, đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác) và chỉ chạy khi tôi xác nhận trong ≤ 15 phút** để **không có thay đổi hệ thống nào xảy ra ngoài ý muốn (NFR-USE-006)**. | 5 | P0 | 1 | `FR-CON-SAFE-001` | `UC-CON-003` | `AC-CON-48`..`AC-CON-51` |
| `US-CON-17` | Web console Phase 1 | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **console chỉ phục vụ tài nguyên tĩnh nhúng sẵn và gửi đủ header bảo mật theo BR-CON-007** để **đạt 0 request tới origin khác và 0 vi phạm CSP trên 10 màn hình (NFR-SEC-006)**. | 2 | P0 | 1 | `FR-CON-SAFE-002` | `UC-CON-001` | `AC-CON-52`..`AC-CON-54` |
| `US-CON-18` | Web console Phase 1 | Là một **người vận hành VPS (PER-01)**, tôi muốn **console chỉ tạo job từ hành động trong danh sách trắng với tham số đã kiểm regex/enum, chạy bằng argv cố định `shell=False`** để **không thể chèn lệnh shell qua console (NFR-SEC-007, NFR-SEC-008)**. | 3 | P0 | 1 | `FR-CON-SAFE-003` | `UC-CON-003` | `AC-CON-55`..`AC-CON-57` |
| `US-CON-19` | Web console Phase 1 | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **API `/api/v1` trả envelope `{success, data, error, meta, timestamp}` với mã `ERR-*`, phân trang và giới hạn kích thước** để **viết script/CI gọi console theo hợp đồng có phiên bản `/api/v1` và mã lỗi `ERR-*` cố định**. | 3 | P0 | 1 | `FR-CON-API-001` | `UC-CON-001` | `AC-CON-58`..`AC-CON-60` |

### 4.10 — Job runner, log, audit (`JOB`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-JOB-01` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **job được xếp hàng FIFO với tối đa 1 job `write` và 2 job `read` cùng `RUNNING`, hàng đợi ≤ 20 job và timeout theo loại hành động** để **máy chủ không quá tải và thao tác ghi không chồng lên nhau**. | 5 | P0 | 1 | `FR-JOB-RUN-001` | `UC-JOB-001` | `AC-JOB-01`..`AC-JOB-03` |
| `US-JOB-02` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **job của console và lượt CLI dùng chung khoá `STATE_DIR/.lock` (ghi độc quyền, đọc chia sẻ)** để **không có 2 thao tác ghi cùng chạy trên 1 máy chủ (NFR-REL-004)**. | 3 | P0 | 1 | `FR-JOB-RUN-002` | `UC-JOB-001` | `AC-JOB-04`..`AC-JOB-06` |
| `US-JOB-03` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **huỷ job: `QUEUED` huỷ ngay, job đọc dừng trong ≤ 10 s, job ghi bị từ chối khi đang ở vùng tới hạn** để **huỷ không bao giờ để hệ thống ở trạng thái thay đổi dở dang**. | 3 | P0 | 1 | `FR-JOB-RUN-003` | `UC-JOB-002` | `AC-JOB-07`..`AC-JOB-09` |
| `US-JOB-04` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **khi `serve` khởi động lại, job `RUNNING` được đối soát trong ≤ 5 s và không job ghi nào tự chạy lại** để **biết job nào bị gián đoạn để kiểm tra manifest trước khi chạy lại**. | 3 | P0 | 1 | `FR-JOB-RUN-004` | `UC-JOB-001` | `AC-JOB-10`..`AC-JOB-12` |
| `US-JOB-05` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **stdout/stderr của job được lưu vào `result.json`/`output.log` ≤ 20 MiB, quyền `0600`, đã che bí mật và được dọn theo hạn 30/365 ngày và trần 200 MiB** để **xem lại kết quả job mà không lộ bí mật và không làm đầy đĩa**. | 3 | P0 | 1 | `FR-JOB-LOG-001`, `FR-JOB-LOG-003` | `UC-JOB-001` | `AC-JOB-13`..`AC-JOB-15` |
| `US-JOB-06` | Job runner, log, audit | Là một **người vận hành VPS (PER-01)**, tôi muốn **log job được đẩy qua SSE, nối lại được từ `Last-Event-ID` và có heartbeat 15 s** để **thấy dòng log mới ≤ 2 s sau khi CLI ghi (NFR-PERF-003)**. | 3 | P0 | 1 | `FR-JOB-LOG-002` | `UC-JOB-001` | `AC-JOB-16`..`AC-JOB-18`, `AC-JOB-25` |
| `US-JOB-07` | Job runner, log, audit | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **mọi sự kiện thuộc BR-AUD-001 ghi audit intent trước và result sau vào file JSONL chỉ nối thêm có chuỗi hash** để **có nhật ký không sửa được về ai làm gì, lúc nào (NFR-REL-002)**. | 5 | P0 | 1 | `FR-JOB-AUD-001` | `UC-JOB-003` | `AC-JOB-19`..`AC-JOB-21` |
| `US-JOB-08` | Job runner, log, audit | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **tra cứu audit theo thời gian/actor/hành động và kiểm chuỗi hash, nhận `seq` đầu tiên bị lệch** để **phát hiện 100% thay đổi 1 byte trong audit (NFR-REL-007)**. | 3 | P0 | 1 | `FR-JOB-AUD-002`, `FR-JOB-AUD-003` | `UC-JOB-003` | `AC-JOB-22`..`AC-JOB-24` |

### 4.11 — Giao diện dòng lệnh (`CLI`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-CLI-01` | Giao diện dòng lệnh | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **mọi lệnh có `--json` in đúng 1 tài liệu JSON envelope `qp.<lệnh>/<major>` ra stdout** để **pipeline CI đọc kết quả và mã thoát mà không phân tích văn bản**. | 5 | P0 | 1 | `FR-CLI-JSON-001` | `UC-CLI-001`, `UC-SCAN-001` | `AC-CLI-01`..`AC-CLI-03` |
| `US-CLI-02` | Giao diện dòng lệnh | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **JSON Schema 2020-12 của mọi lệnh được phát hành và in được bằng `schema <lệnh>`** để **kiểm hợp lệ đầu ra trong CI trước khi nâng phiên bản tool**. | 2 | P1 | 1 | `FR-CLI-JSON-002` | `UC-CLI-001` | `AC-CLI-04`..`AC-CLI-06` |
| `US-CLI-03` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **mọi cú pháp, mã thoát, định dạng dòng văn bản và đường dẫn trạng thái của v0.1 được giữ nguyên** để **script và cron hiện có gọi `php-quickpatch.sh` v0.1 chạy tiếp không cần sửa (NFR-CMP-001)**. | 5 | P0 | 1 | `FR-CLI-COMP-001` | `UC-SCAN-001` | `AC-CLI-07`..`AC-CLI-09` |
| `US-CLI-04` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **mảng ghi cứng `PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED` được thay bằng phép tra bundle online** để **nhận đánh giá đúng với CVE mới mà không chờ bản script mới**. | 3 | P0 | 1 | `FR-CLI-COMP-002` | `UC-SCAN-001` | `AC-CLI-10`..`AC-CLI-12` |
| `US-CLI-05` | Giao diện dòng lệnh | Là một **kỹ sư DevOps quản lý Docker (PER-03)**, tôi muốn **lệnh `assess` đánh giá runtime và ứng viên trên kết quả scan gần nhất** để **đưa đánh giá so sánh vào CI/script qua schema `qp.assess/1`**. | 3 | P0 | 1 | `FR-CLI-CMD-001` | `UC-ASMT-001`, `UC-CLI-001` | `AC-CLI-13`..`AC-CLI-15` |
| `US-CLI-06` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **dùng lệnh `plan create\|list\|show\|approve\|item\|run\|cancel`** để **quản lý kế hoạch nâng cấp hoàn toàn từ terminal khi không dùng console**. | 3 | P0 | 1 | `FR-CLI-CMD-002` | `UC-PLAN-001`, `UC-PLAN-002`, `UC-PLAN-003` | `AC-CLI-16`..`AC-CLI-18` |
| `US-CLI-07` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **dùng lệnh `migrate install\|switch\|healthcheck\|rollback\|remove-old\|status` và bí danh `upgrade`, `switch-site`, `healthcheck`, `rollback-site`** để **chạy nâng cấp khác nhánh bằng CLI theo cùng quy tắc như console**. | 3 | P0 | 1 | `FR-CLI-CMD-003` | `UC-UPG-001`, `UC-UPG-002`, `UC-UPG-004` | `AC-CLI-19`..`AC-CLI-21` |
| `US-CLI-08` | Giao diện dòng lệnh | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **dùng lệnh `report assess\|evidence` và `audit list\|verify`** để **xuất báo cáo và kiểm audit trực tiếp từ terminal**. | 2 | P0 | 1 | `FR-CLI-CMD-004` | `UC-RPT-001`, `UC-RPT-002`, `UC-JOB-003` | `AC-CLI-22`..`AC-CLI-24` |
| `US-CLI-09` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **lệnh thay đổi có `--dry-run` cho 0 thay đổi, và lệnh ghi mới hỏi xác nhận `y/N` hoặc bắt buộc `--yes` khi không có TTY** để **không thay đổi hệ thống ngoài ý muốn khi chạy từ script hoặc cron**. | 3 | P0 | 1 | `FR-CLI-SAFE-001` | `UC-PTCH-001`, `UC-UPG-001` | `AC-CLI-25`..`AC-CLI-27` |
| `US-CLI-10` | Giao diện dòng lệnh | Là một **người vận hành VPS (PER-01)**, tôi muốn **CLI kiểm Bash ≥ 4.3, `flock`, `curl`, Python ≥ 3.6 (lệnh cần Python) và quyền root trước khi chạy lệnh** để **lệnh dừng ngay với mã lỗi xác định thay vì chạy dở**. | 2 | P0 | 1 | `FR-CLI-ENV-001` | `UC-CLI-001` | `AC-CLI-28`..`AC-CLI-30` |

### 4.12 — Báo cáo (`RPT`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-RPT-01` | Báo cáo | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **xuất báo cáo đánh giá JSON/CSV/Markdown/HTML có nguồn dữ liệu, `bundle_id` và SHA-256 của file** để **nộp bằng chứng tình trạng lỗ hổng/EOL cho kiểm toán**. | 3 | P1 | 1 | `FR-RPT-ASMT-001` | `UC-RPT-001` | `AC-RPT-01`..`AC-RPT-03` |
| `US-RPT-02` | Báo cáo | Là một **kỹ sư bảo mật / kiểm toán viên (PER-04)**, tôi muốn **xuất báo cáo bằng chứng thay đổi trong khoảng thời gian gồm trạng thái trước/sau, người chạy, người duyệt, miễn trừ, rollback và kết quả kiểm audit** để **chứng minh mọi thay đổi trên máy chủ đều có kiểm soát**. | 3 | P1 | 1 | `FR-RPT-AUD-001` | `UC-RPT-002` | `AC-RPT-04`..`AC-RPT-06` |

### 4.13 — Quản lý nhiều server (Phase 2) (`FLT`)

| Story ID | Epic | User Story (Là một… tôi muốn… để…) | Story Point | Ưu tiên | Phase | FR liên kết | Use case | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| `US-FLT-01` **[Epic]** | Quản lý nhiều server (Phase 2) | Là một **Admin máy trung tâm Phase 2 (PER-01, PER-02)**, tôi muốn **khai báo server (host, cổng, user SSH, khoá, fingerprint SHA256, nhóm) và kiểm kết nối với khoá máy chủ đã ghim** để **máy trung tâm chỉ kết nối tới đúng server và không lưu mật khẩu SSH**. | 8 | P0 | 2 | `FR-FLT-INV-001`, `FR-FLT-INV-002` | `UC-FLT-001` | `AC-FLT-01`..`AC-FLT-03` |
| `US-FLT-02` **[Epic]** | Quản lý nhiều server (Phase 2) | Là một **Admin máy trung tâm Phase 2 (PER-01, PER-02)**, tôi muốn **tạo tài khoản Viewer/Operator/Admin và phân quyền theo vai trò trên máy trung tâm** để **kiểm toán viên chỉ xem, chỉ Operator/Admin được thay đổi**. | 8 | P0 | 2 | `FR-FLT-RBAC-001` | `UC-FLT-001` | `AC-FLT-04`..`AC-FLT-06` |
| `US-FLT-03` **[Epic]** | Quản lý nhiều server (Phase 2) | Là một **Operator máy trung tâm Phase 2 (PER-01, PER-02)**, tôi muốn **chạy lệnh CLI trong danh sách trắng trên nhóm server theo đợt (canary 1 server → đợt ≤ 5 server, ≤ 10 kết nối song song)** để **vá nhiều server mà 1 lỗi chỉ ảnh hưởng tối đa 1 đợt**. | 8 | P0 | 2 | `FR-FLT-EXEC-001`, `FR-FLT-EXEC-002` | `UC-FLT-002` | `AC-FLT-07`..`AC-FLT-09` |
| `US-FLT-04` **[Epic]** | Quản lý nhiều server (Phase 2) | Là một **Viewer máy trung tâm Phase 2 (PER-04)**, tôi muốn **xem ma trận server × runtime (KEV, Critical, EOL, chưa vá, `R`), đi sâu từng server và audit hợp nhất** để **nắm rủi ro của toàn bộ server trong 1 màn hình**. | 8 | P0 | 2 | `FR-FLT-DASH-001`, `FR-FLT-DASH-002`, `FR-FLT-AUD-001` | `UC-FLT-003` | `AC-FLT-10`..`AC-FLT-12` |
| `US-FLT-05` **[Epic]** | Quản lý nhiều server (Phase 2) | Là một **Operator máy trung tâm Phase 2 (PER-01, PER-02)**, tôi muốn **máy trung tâm đồng bộ dữ liệu một lần và đẩy snapshot tới server không ra Internet** để **mọi server cách ly dùng cùng `bundle_id` với máy trung tâm**. | 5 | P1 | 2 | `FR-FLT-FEED-001` | `UC-FLT-004` | `AC-FLT-13`..`AC-FLT-15` |
## 5. Kiểm tra INVEST (rule 07)
Tiêu chí đánh giá áp dụng cho mọi story:
- **I**: phát triển và kiểm thử được bằng dữ liệu mẫu mà không chờ story khác hoàn thành; cột ghi phụ thuộc tích hợp (nếu có).
- **N**: câu story mô tả mục tiêu, không chốt thiết kế giao diện; ngưỡng số lấy từ SRS và có thể đổi qua change request (rule 15).
- **V**: mỗi story gắn với ≥ 1 persona và ≥ 1 KR/NFR/BR của PRD/SRS.
- **E**: mọi FR liên kết đã đặc tả Input → Processing → Output trong SRS; lệnh "chưa kiểm chứng" của playbook không làm tăng ước lượng vì chỉ chạy ở mức `MANUAL`/`SEMI` (`BR-ENV-010`).
- **S**: ≤ 5 SP là "Đạt"; 8 SP là "Đạt có điều kiện"; story mức epic là "Chưa" và phải tách trước sprint.
- **T**: ≥ 3 scenario Gherkin có mã `ERR-*` hoặc ngưỡng số kiểm được.

| Story ID | I — Độc lập | N — Thương lượng | V — Giá trị | E — Ước lượng | S — Vừa vặn | T — Kiểm thử | Ghi chú |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| `US-SCAN-01` | Đạt; nền tảng cho UC-SCAN-001, test bằng máy mẫu PB-001/PB-005/PB-007 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-SCAN-02` | Đạt; trạng thái vá dùng bundle mẫu cố định khi chưa có US-FEED-09 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-SCAN-03` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-SCAN-04` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-SCAN-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc dữ liệu `switch_record` của US-UPG-04 (dùng `index.tsv` mẫu khi test) | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-SCN-01` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-SCAN-02 (đầu vào `version_raw`), test bằng danh sách chuỗi phiên bản mẫu | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-SCN-02` | Đạt; dùng `lifecycle.tsv` mẫu và ngày chạy giả lập | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-SCN-03` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-SCN-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-SCN-01, US-SCN-03 (dùng catalog mẫu) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-SCN-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-SCAN-01 (đầu vào `environment`) | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-01` | Đạt; nguồn giả lập bằng máy chủ HTTPS cục bộ trong test | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-FEED-02` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-03` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-04` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-FEED-05` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-06` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-FEED-07` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-08` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-FEED-09` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc raw cache của US-FEED-02..06 (dùng bộ raw cố định ngày 2026-10-22) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-FEED-10` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-11` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-FEED-12` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-13` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-FEED-14` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-15` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-16` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FEED-17` | Đạt; nguồn tuỳ chọn, tắt mặc định | Đạt | Đạt | Đạt | Chưa — mức epic (P2), tách trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-ASMT-01` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc bundle của US-FEED-09 (dùng bundle mẫu ngày 2026-10-22) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-ASMT-02` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-ASMT-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-ASMT-01, US-ASMT-02 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-ASMT-04` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-ASMT-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-FEED-07 (dùng phản hồi OSV mẫu) | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-ASMT-06` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-PLAN-01` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-ASMT-02 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (4 scenario) | - |
| `US-PLAN-02` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-SCN-04, US-CMPT-10 (dùng kết quả quét mẫu) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-PLAN-03` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PLAN-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc kết quả US-CMPT-05..09 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PLAN-05` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PLAN-06` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-01, US-CON-18 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-PLAN-07` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-PLAN-08` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CMPT-01` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-02` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CMPT-01 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CMPT-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-02 (`$NEW_BIN`) | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CMPT-05` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CMPT-06` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CMPT-07` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-08` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-09` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc ma trận của US-FEED-02 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-10` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CMPT-02..09 (dùng tập hit mẫu) | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CMPT-11` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CMPT-01 | Đạt | Đạt | Đạt | Chưa — mức epic (P2, chờ PO trả lời Q-02), tách trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-PTCH-01` | Đạt; kế thừa `php_upgrade` v0.1 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-PTCH-02` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-03` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-04` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-05` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-06` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-07` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-PTCH-08` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-PTCH-09` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-PTCH-08 (manifest mẫu) | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-UPG-01` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-UPG-02` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-01 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-02, US-CMPT-07 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-03, US-UPG-08..11 | Đạt | Đạt | Đạt | Đạt có điều kiện: 8 SP, tách C1–C5 và C6–C12 nếu velocity đội < 16 SP/sprint | Đạt (4 scenario) | - |
| `US-UPG-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-04 (khung C1–C12) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-06` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-07` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-04, US-PLAN-07 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | `FR-UPG-ACK-001` chờ PO duyệt `CR-FR-01` (§7) |
| `US-UPG-08` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-09` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-UPG-10` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-08 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-11` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-10, US-UPG-12 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-12` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-13` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-UPG-02, US-CMPT-06 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-14` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-UPG-15` | Đạt | Đạt | Đạt | Đạt | Chưa — mức epic (P2), tách trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-CON-01` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-CON-02` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CON-01 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CON-02 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-04` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CON-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CON-02 | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CON-06` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc API `GET /api/v1/overview` (dùng `last-scan.json` mẫu) | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CON-07` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-ASMT-01..03 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CON-08` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-PLAN-02, US-JOB-06 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-09` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-PLAN-05..07 | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CON-10` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-03, US-JOB-06 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-11` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-12` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-13` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-CON-14` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-15` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-08, US-RPT-01 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-16` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (4 scenario) | - |
| `US-CON-17` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CON-18` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CON-19` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-JOB-01` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-JOB-02` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-JOB-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-01 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-JOB-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-01 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-JOB-05` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-JOB-06` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-05 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (4 scenario) | - |
| `US-JOB-07` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-JOB-08` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-07 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-01` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CLI-02` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-CLI-01 | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CLI-03` | Đạt | Đạt | Đạt | Đạt | Đạt (5 SP) | Đạt (3 scenario) | - |
| `US-CLI-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-FEED-09 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-05` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-06` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-07` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-08` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-CLI-09` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-CLI-10` | Đạt | Đạt | Đạt | Đạt | Đạt (2 SP) | Đạt (3 scenario) | - |
| `US-RPT-01` | Đạt | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-RPT-02` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-JOB-07, US-JOB-08 | Đạt | Đạt | Đạt | Đạt (3 SP) | Đạt (3 scenario) | - |
| `US-FLT-01` | Đạt | Đạt | Đạt | Đạt | Chưa — mức epic Phase 2, tách thành story ≤ 5 SP trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-FLT-02` | Đạt | Đạt | Đạt | Đạt | Chưa — mức epic Phase 2, tách thành story ≤ 5 SP trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-FLT-03` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-FLT-01 | Đạt | Đạt | Đạt | Chưa — mức epic Phase 2, tách thành story ≤ 5 SP trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-FLT-04` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-FLT-03 (dữ liệu thu) | Đạt | Đạt | Đạt | Chưa — mức epic Phase 2, tách thành story ≤ 5 SP trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |
| `US-FLT-05` | Đạt (phát triển bằng dữ liệu mẫu); tích hợp: Phụ thuộc US-FLT-03 | Đạt | Đạt | Đạt | Chưa — mức epic Phase 2, tách trước khi đưa vào sprint | Đạt (3 scenario) | Mức epic |

## 6. Ma trận truy vết FR → User Story → Acceptance Criteria (rule 14)
Độ phủ: 168/168 FR (100%) của DOC-SRS-QP-FR-001 1.0.1, gồm 136/136 FR P0 Phase 1 (có `FR-UPG-ACK-001` đề xuất, `CR-FR-01`), 20/20 FR P1 Phase 1, 3/3 FR P2 Phase 1 và 9/9 FR Phase 2. Tên FR chép nguyên văn từ DOC-SRS-QP-FR-001 1.0.1 (27 tên đổi theo `CR-FR-06`). Cột Test Case của RTM rule 14 được bổ sung ở bước `/test-case`.

| FR ID | Tên yêu cầu chức năng | Ưu tiên | Phase | User Story | Acceptance Criteria |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `FR-SCAN-ENV-001` | Nhận diện môi trường và chọn playbook | P0 | 1 | `US-SCAN-01` | `AC-SCAN-01`..`AC-SCAN-03` |
| `FR-SCAN-MAP-001` | Kiểm kê site → runtime | P0 | 1 | `US-SCAN-01` | `AC-SCAN-01`..`AC-SCAN-03` |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | P0 | 1 | `US-SCAN-02` | `AC-SCAN-04`..`AC-SCAN-06` |
| `FR-SCAN-RT-002` | Phát hiện runtime Node.js | P0 | 1 | `US-SCAN-02` | `AC-SCAN-04`..`AC-SCAN-06` |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | P0 | 1 | `US-SCAN-03` | `AC-SCAN-07`..`AC-SCAN-09` |
| `FR-SCAN-PRJ-002` | Kiểm kê container đang chạy | P0 | 1 | `US-SCAN-03` | `AC-SCAN-07`..`AC-SCAN-09` |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | P0 | 1 | `US-SCAN-04` | `AC-SCAN-10`..`AC-SCAN-12` |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | P1 | 1 | `US-SCAN-05` | `AC-SCAN-13`..`AC-SCAN-15` |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | P0 | 1 | `US-SCN-01` | `AC-SCN-01`..`AC-SCN-04` |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | P0 | 1 | `US-SCN-01` | `AC-SCN-01`..`AC-SCN-04` |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | P0 | 1 | `US-SCN-02` | `AC-SCN-05`..`AC-SCN-07` |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | P0 | 1 | `US-SCN-03` | `AC-SCN-08`..`AC-SCN-10` |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | P0 | 1 | `US-SCN-04` | `AC-SCN-11`..`AC-SCN-13` |
| `FR-SCN-LOCK-001` | Khoá tự động hoá với phiên bản bất thường | P0 | 1 | `US-SCN-01` | `AC-SCN-01`..`AC-SCN-04` |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | P0 | 1 | `US-SCN-05` | `AC-SCN-14`..`AC-SCN-16` |
| `FR-ASMT-RISK-001` | Tính điểm rủi ro runtime | P0 | 1 | `US-ASMT-01` | `AC-ASMT-01`..`AC-ASMT-04` |
| `FR-ASMT-RISK-002` | So sánh điểm hiện tại và ứng viên | P0 | 1 | `US-ASMT-03` | `AC-ASMT-08`..`AC-ASMT-10` |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | P0 | 1 | `US-ASMT-01` | `AC-ASMT-01`..`AC-ASMT-04` |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | P0 | 1 | `US-ASMT-02` | `AC-ASMT-05`..`AC-ASMT-07` |
| `FR-ASMT-CAND-002` | Xác định khả năng cài của ứng viên | P0 | 1 | `US-ASMT-02` | `AC-ASMT-05`..`AC-ASMT-07` |
| `FR-ASMT-CMP-001` | So sánh hiện tại với ứng viên | P0 | 1 | `US-ASMT-03` | `AC-ASMT-08`..`AC-ASMT-10` |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | P0 | 1 | `US-ASMT-04` | `AC-ASMT-11`..`AC-ASMT-13` |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | P0 | 1 | `US-ASMT-05` | `AC-ASMT-14`..`AC-ASMT-16` |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | P0 | 1 | `US-ASMT-06` | `AC-ASMT-17`..`AC-ASMT-19` |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | P0 | 1 | `US-PLAN-01` | `AC-PLAN-01`..`AC-PLAN-04` |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | P0 | 1 | `US-PLAN-02` | `AC-PLAN-05`..`AC-PLAN-07` |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | P0 | 1 | `US-PLAN-03` | `AC-PLAN-08`..`AC-PLAN-10` |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | P0 | 1 | `US-PLAN-04` | `AC-PLAN-11`..`AC-PLAN-13` |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | P0 | 1 | `US-PLAN-05` | `AC-PLAN-14`..`AC-PLAN-16` |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | P0 | 1 | `US-PLAN-06` | `AC-PLAN-17`..`AC-PLAN-19` |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | P0 | 1 | `US-PLAN-07` | `AC-PLAN-20`..`AC-PLAN-23` |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | P0 | 1 | `US-PLAN-08` | `AC-PLAN-24`..`AC-PLAN-26` |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | P0 | 1 | `US-CMPT-01` | `AC-CMPT-01`..`AC-CMPT-03` |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | P0 | 1 | `US-CMPT-02` | `AC-CMPT-04`..`AC-CMPT-06` |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | P0 | 1 | `US-CMPT-03` | `AC-CMPT-07`..`AC-CMPT-09` |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | P0 | 1 | `US-CMPT-04` | `AC-CMPT-10`..`AC-CMPT-12` |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | P0 | 1 | `US-CMPT-05` | `AC-CMPT-13`..`AC-CMPT-15` |
| `FR-CMPT-COMP-002` | Tra phiên bản tối thiểu thoả trên Packagist | P0 | 1 | `US-CMPT-05` | `AC-CMPT-13`..`AC-CMPT-15` |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | P1 | 1 | `US-CMPT-06` | `AC-CMPT-16`..`AC-CMPT-18` |
| `FR-CMPT-NPM-002` | Phát hiện native addon | P1 | 1 | `US-CMPT-06` | `AC-CMPT-16`..`AC-CMPT-18` |
| `FR-CMPT-INI-001` | Quét directive ini bị gỡ | P0 | 1 | `US-CMPT-07` | `AC-CMPT-19`..`AC-CMPT-21` |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | P0 | 1 | `US-CMPT-07` | `AC-CMPT-19`..`AC-CMPT-21` |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | P1 | 1 | `US-CMPT-09` | `AC-CMPT-25`..`AC-CMPT-27` |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | P0 | 1 | `US-CMPT-08` | `AC-CMPT-22`..`AC-CMPT-24` |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | P0 | 1 | `US-CMPT-10` | `AC-CMPT-28`..`AC-CMPT-30` |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | P2 | 1 | `US-CMPT-11` | `AC-CMPT-31`..`AC-CMPT-33` |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | P0 | 1 | `US-PTCH-01` | `AC-PTCH-01`..`AC-PTCH-04` |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | P0 | 1 | `US-PTCH-01` | `AC-PTCH-01`..`AC-PTCH-04` |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | P0 | 1 | `US-PTCH-02` | `AC-PTCH-05`..`AC-PTCH-07` |
| `FR-PTCH-MIT-002` | Tự gỡ mitigation khi đã vá | P0 | 1 | `US-PTCH-02` | `AC-PTCH-05`..`AC-PTCH-07` |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | P0 | 1 | `US-PTCH-03` | `AC-PTCH-08`..`AC-PTCH-10` |
| `FR-PTCH-DEP-001` | Cập nhật Composer package có lỗ hổng | P0 | 1 | `US-PTCH-04` | `AC-PTCH-11`..`AC-PTCH-13` |
| `FR-PTCH-DEP-002` | Cập nhật npm package có lỗ hổng | P0 | 1 | `US-PTCH-04` | `AC-PTCH-11`..`AC-PTCH-13` |
| `FR-PTCH-WP-001` | Cập nhật WordPress | P0 | 1 | `US-PTCH-05` | `AC-PTCH-14`..`AC-PTCH-16` |
| `FR-PTCH-WP-002` | Kiểm tra toàn vẹn WordPress | P0 | 1 | `US-PTCH-05` | `AC-PTCH-14`..`AC-PTCH-16` |
| `FR-PTCH-DKR-001` | Nâng tag image cùng nhánh | P0 | 1 | `US-PTCH-06` | `AC-PTCH-17`..`AC-PTCH-19` |
| `FR-PTCH-DKR-002` | Ghi mitigation vào container đang chạy | P0 | 1 | `US-PTCH-06` | `AC-PTCH-17`..`AC-PTCH-19` |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | P0 | 1 | `US-PTCH-07` | `AC-PTCH-20`..`AC-PTCH-22` |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | P0 | 1 | `US-PTCH-08` | `AC-PTCH-23`..`AC-PTCH-25` |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | P0 | 1 | `US-PTCH-09` | `AC-PTCH-26`..`AC-PTCH-28` |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | P0 | 1 | `US-UPG-02` | `AC-UPG-04`..`AC-UPG-06` |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | P0 | 1 | `US-UPG-03` | `AC-UPG-07`..`AC-UPG-09` |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | P0 | 1 | `US-UPG-04` | `AC-UPG-10`..`AC-UPG-13` |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | P0 | 1 | `US-UPG-05` | `AC-UPG-14`..`AC-UPG-16` |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | P0 | 1 | `US-UPG-12` | `AC-UPG-36`..`AC-UPG-38` |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | P0 | 1 | `US-UPG-11` | `AC-UPG-33`..`AC-UPG-35` |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | P1 | 1 | `US-UPG-13` | `AC-UPG-39`..`AC-UPG-41` |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | P1 | 1 | `US-UPG-14` | `AC-UPG-42`..`AC-UPG-44` |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | P0 | 1 | `US-UPG-08` | `AC-UPG-24`..`AC-UPG-26` |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | P0 | 1 | `US-UPG-09` | `AC-UPG-27`..`AC-UPG-29` |
| `FR-UPG-HC-003` | Thu baseline | P0 | 1 | `US-UPG-08` | `AC-UPG-24`..`AC-UPG-26` |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | P0 | 1 | `US-UPG-10` | `AC-UPG-30`..`AC-UPG-32` |
| `FR-UPG-HC-005` | Ra quyết định sau health check | P0 | 1 | `US-UPG-11` | `AC-UPG-33`..`AC-UPG-35` |
| `FR-UPG-HC-006` | Báo cáo health check | P0 | 1 | `US-UPG-10` | `AC-UPG-30`..`AC-UPG-32` |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | P0 | 1 | `US-UPG-01` | `AC-UPG-01`..`AC-UPG-03` |
| `FR-UPG-CFG-002` | Sao chép ini tuỳ chỉnh và extension sang runtime đích | P0 | 1 | `US-UPG-03` | `AC-UPG-07`..`AC-UPG-09` |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | P0 | 1 | `US-UPG-06` | `AC-UPG-17`..`AC-UPG-19` |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | P0 | 1 | `US-UPG-07` | `AC-UPG-20`..`AC-UPG-23` |
| `FR-UPG-ACK-001` | Xác nhận đã xử lý lượt chuyển thất bại (đề xuất, `CR-FR-01`) | P0 | 1 | `US-UPG-07` | `AC-UPG-22` |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | P2 | 1 | `US-UPG-15` | `AC-UPG-45`..`AC-UPG-47` |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | P0 | 1 | `US-CON-01` | `AC-CON-01`..`AC-CON-04` |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | P0 | 1 | `US-CON-01` | `AC-CON-01`..`AC-CON-04` |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | P0 | 1 | `US-CON-02` | `AC-CON-05`..`AC-CON-07` |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | P0 | 1 | `US-CON-03` | `AC-CON-08`..`AC-CON-10` |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | P0 | 1 | `US-CON-04` | `AC-CON-11`..`AC-CON-13` |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | P0 | 1 | `US-CON-05` | `AC-CON-14`..`AC-CON-16` |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | P0 | 1 | `US-CON-06` | `AC-CON-17`..`AC-CON-19` |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | P0 | 1 | `US-CON-07` | `AC-CON-20`..`AC-CON-22` |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | P0 | 1 | `US-CON-08` | `AC-CON-23`..`AC-CON-25` |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | P0 | 1 | `US-CON-09` | `AC-CON-26`..`AC-CON-28` |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | P0 | 1 | `US-CON-10` | `AC-CON-29`..`AC-CON-31` |
| `FR-CON-JOB-002` | Huỷ job từ console | P0 | 1 | `US-CON-10` | `AC-CON-29`..`AC-CON-31` |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | P0 | 1 | `US-CON-11` | `AC-CON-32`..`AC-CON-34` |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | P0 | 1 | `US-CON-12` | `AC-CON-35`..`AC-CON-37` |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | P0 | 1 | `US-CON-13` | `AC-CON-38`..`AC-CON-41` |
| `FR-CON-FEED-002` | Nhập snapshot qua console | P1 | 1 | `US-CON-13` | `AC-CON-38`..`AC-CON-41` |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | P0 | 1 | `US-CON-14` | `AC-CON-42`..`AC-CON-44` |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | P1 | 1 | `US-CON-15` | `AC-CON-45`..`AC-CON-47` |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | P0 | 1 | `US-CON-16` | `AC-CON-48`..`AC-CON-51` |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | P0 | 1 | `US-CON-17` | `AC-CON-52`..`AC-CON-54` |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | P0 | 1 | `US-CON-18` | `AC-CON-55`..`AC-CON-57` |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | P0 | 1 | `US-CON-19` | `AC-CON-58`..`AC-CON-60` |
| `FR-JOB-RUN-001` | Xếp hàng và chạy job | P0 | 1 | `US-JOB-01` | `AC-JOB-01`..`AC-JOB-03` |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | P0 | 1 | `US-JOB-02` | `AC-JOB-04`..`AC-JOB-06` |
| `FR-JOB-RUN-003` | Huỷ job | P0 | 1 | `US-JOB-03` | `AC-JOB-07`..`AC-JOB-09` |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | P0 | 1 | `US-JOB-04` | `AC-JOB-10`..`AC-JOB-12` |
| `FR-JOB-LOG-001` | Lưu log và kết quả job | P0 | 1 | `US-JOB-05` | `AC-JOB-13`..`AC-JOB-15` |
| `FR-JOB-LOG-002` | Stream log qua SSE | P0 | 1 | `US-JOB-06` | `AC-JOB-16`..`AC-JOB-18`, `AC-JOB-25` |
| `FR-JOB-LOG-003` | Lưu giữ log job | P1 | 1 | `US-JOB-05` | `AC-JOB-13`..`AC-JOB-15` |
| `FR-JOB-AUD-001` | Ghi audit append-only | P0 | 1 | `US-JOB-07` | `AC-JOB-19`..`AC-JOB-21` |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | P1 | 1 | `US-JOB-08` | `AC-JOB-22`..`AC-JOB-24` |
| `FR-JOB-AUD-003` | Truy vấn audit | P0 | 1 | `US-JOB-08` | `AC-JOB-22`..`AC-JOB-24` |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | P0 | 1 | `US-CLI-01` | `AC-CLI-01`..`AC-CLI-03` |
| `FR-CLI-JSON-002` | Công bố JSON Schema | P1 | 1 | `US-CLI-02` | `AC-CLI-04`..`AC-CLI-06` |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | P0 | 1 | `US-CLI-03` | `AC-CLI-07`..`AC-CLI-09` |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | P0 | 1 | `US-CLI-04` | `AC-CLI-10`..`AC-CLI-12` |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | P0 | 1 | `US-CLI-05` | `AC-CLI-13`..`AC-CLI-15` |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | P0 | 1 | `US-CLI-06` | `AC-CLI-16`..`AC-CLI-18` |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | P0 | 1 | `US-CLI-07` | `AC-CLI-19`..`AC-CLI-21` |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | P0 | 1 | `US-CLI-08` | `AC-CLI-22`..`AC-CLI-24` |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | P0 | 1 | `US-CLI-09` | `AC-CLI-25`..`AC-CLI-27` |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | P0 | 1 | `US-CLI-10` | `AC-CLI-28`..`AC-CLI-30` |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | P1 | 1 | `US-RPT-01` | `AC-RPT-01`..`AC-RPT-03` |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | P1 | 1 | `US-RPT-02` | `AC-RPT-04`..`AC-RPT-06` |
| `FR-FLT-INV-001` | Quản lý danh mục server | P0 | 2 | `US-FLT-01` | `AC-FLT-01`..`AC-FLT-03` |
| `FR-FLT-INV-002` | Kiểm tra kết nối và ghim khoá máy chủ | P0 | 2 | `US-FLT-01` | `AC-FLT-01`..`AC-FLT-03` |
| `FR-FLT-EXEC-001` | Thực thi CLI từ xa | P0 | 2 | `US-FLT-03` | `AC-FLT-07`..`AC-FLT-09` |
| `FR-FLT-EXEC-002` | Chạy theo đợt | P0 | 2 | `US-FLT-03` | `AC-FLT-07`..`AC-FLT-09` |
| `FR-FLT-DASH-001` | Hiển thị dashboard tổng hợp nhiều server | P0 | 2 | `US-FLT-04` | `AC-FLT-10`..`AC-FLT-12` |
| `FR-FLT-DASH-002` | Đi sâu theo server | P1 | 2 | `US-FLT-04` | `AC-FLT-10`..`AC-FLT-12` |
| `FR-FLT-FEED-001` | Cache dữ liệu trung tâm và phân phối snapshot | P1 | 2 | `US-FLT-05` | `AC-FLT-13`..`AC-FLT-15` |
| `FR-FLT-RBAC-001` | Quản lý tài khoản và vai trò Phase 2 | P0 | 2 | `US-FLT-02` | `AC-FLT-04`..`AC-FLT-06` |
| `FR-FLT-AUD-001` | Hợp nhất audit trung tâm | P1 | 2 | `US-FLT-04` | `AC-FLT-10`..`AC-FLT-12` |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | P0 | 1 | `US-FEED-02` | `AC-FEED-05`..`AC-FEED-07` |
| `FR-FEED-EOL-002` | Bổ sung bản ghi vòng đời tĩnh | P0 | 1 | `US-FEED-02` | `AC-FEED-05`..`AC-FEED-07` |
| `FR-FEED-EOL-003` | Đồng bộ ma trận framework/CMS ↔ PHP | P1 | 1 | `US-FEED-02` | `AC-FEED-05`..`AC-FEED-07` |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | P0 | 1 | `US-FEED-03` | `AC-FEED-08`..`AC-FEED-10` |
| `FR-FEED-REL-002` | Đồng bộ bản phát hành Node.js | P0 | 1 | `US-FEED-03` | `AC-FEED-08`..`AC-FEED-10` |
| `FR-FEED-REL-003` | Đồng bộ trạng thái WordPress core | P0 | 1 | `US-FEED-03` | `AC-FEED-08`..`AC-FEED-10` |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | P0 | 1 | `US-FEED-04` | `AC-FEED-11`..`AC-FEED-13` |
| `FR-FEED-PCVE-002` | Làm giàu alias GHSA ↔ CVE cho PHP | P1 | 1 | `US-FEED-04` | `AC-FEED-11`..`AC-FEED-13` |
| `FR-FEED-PCVE-003` | Tra CVE.org khi NVD thiếu | P0 | 1 | `US-FEED-04` | `AC-FEED-11`..`AC-FEED-13` |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | P0 | 1 | `US-FEED-05` | `AC-FEED-14`..`AC-FEED-16` |
| `FR-FEED-WCVE-001` | Đồng bộ CVE WordPress core | P0 | 1 | `US-FEED-05` | `AC-FEED-14`..`AC-FEED-16` |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | P2 | 1 | `US-FEED-17` | `AC-FEED-51`..`AC-FEED-53` |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | P0 | 1 | `US-FEED-06` | `AC-FEED-17`..`AC-FEED-19` |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | P0 | 1 | `US-FEED-07` | `AC-FEED-20`..`AC-FEED-22` |
| `FR-FEED-DIST-001` | Tra advisory distro cho gói runtime | P0 | 1 | `US-FEED-08` | `AC-FEED-23`..`AC-FEED-25` |
| `FR-FEED-DIST-002` | Dự phòng tracker distro và changelog | P1 | 1 | `US-FEED-08` | `AC-FEED-23`..`AC-FEED-25` |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | P0 | 1 | `US-FEED-01` | `AC-FEED-01`..`AC-FEED-04` |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | P0 | 1 | `US-FEED-10` | `AC-FEED-29`..`AC-FEED-31` |
| `FR-FEED-NORM-001` | Chuẩn hoá và khử trùng lặp advisory | P0 | 1 | `US-FEED-09` | `AC-FEED-26`..`AC-FEED-28` |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | P0 | 1 | `US-FEED-09` | `AC-FEED-26`..`AC-FEED-28` |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | P0 | 1 | `US-FEED-08` | `AC-FEED-23`..`AC-FEED-25` |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | P0 | 1 | `US-FEED-11` | `AC-FEED-32`..`AC-FEED-34` |
| `FR-FEED-CACH-002` | Dựng và thay bundle nguyên tử | P0 | 1 | `US-FEED-11` | `AC-FEED-32`..`AC-FEED-34` |
| `FR-FEED-CACH-003` | Dọn dẹp theo giới hạn dung lượng | P1 | 1 | `US-FEED-11` | `AC-FEED-32`..`AC-FEED-34` |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | P0 | 1 | `US-FEED-12` | `AC-FEED-35`..`AC-FEED-37` |
| `FR-FEED-SNAP-002` | Xuất snapshot | P0 | 1 | `US-FEED-13` | `AC-FEED-38`..`AC-FEED-41` |
| `FR-FEED-SNAP-003` | Nhập snapshot | P0 | 1 | `US-FEED-13` | `AC-FEED-38`..`AC-FEED-41` |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | P0 | 1 | `US-FEED-14` | `AC-FEED-42`..`AC-FEED-44` |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | P1 | 1 | `US-FEED-15` | `AC-FEED-45`..`AC-FEED-47` |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | P0 | 1 | `US-FEED-01` | `AC-FEED-01`..`AC-FEED-04` |
| `FR-FEED-CMD-002` | Lệnh `feeds status` | P0 | 1 | `US-FEED-16` | `AC-FEED-48`..`AC-FEED-50` |
| `FR-FEED-CMD-003` | Lệnh `feeds verify` | P1 | 1 | `US-FEED-16` | `AC-FEED-48`..`AC-FEED-50` |
| `FR-FEED-CMD-004` | Lệnh `feeds export` (bí danh `snapshot export`) | P0 | 1 | `US-FEED-13` | `AC-FEED-38`..`AC-FEED-41` |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | P0 | 1 | `US-FEED-13` | `AC-FEED-38`..`AC-FEED-41` |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | P1 | 1 | `US-FEED-15` | `AC-FEED-45`..`AC-FEED-47` |

## 7. Giả định và câu hỏi mở
| Mã | Nội dung | Ảnh hưởng tới backlog | Người quyết định |
| :--- | :--- | :--- | :--- |
| `Q-01` | Ngưỡng health check theo DOC-SRS-QP-ENV-002 (600 s, `HC-C0..C9`) chưa được PO duyệt | AC của `US-UPG-08..11` dùng số liệu DOC-SRS-QP-ENV-002 theo `BR-DATA-004`; PO đổi ngưỡng → cập nhật AC, không đổi SP | PO |
| `Q-02` | Có tích hợp Rector không | `US-CMPT-11` giữ ở P2 mức epic tới khi PO trả lời | PO |
| `Q-03` | Cho phép thêm kho bên thứ ba | `US-UPG-02` coi thêm kho là mục `SEMI` (`BR-ENV-004`); PO trả lời "không" → bỏ scenario thêm kho, giữ SP | PO |
| `Q-07` | Vá cùng nhánh theo lịch không cần duyệt | Không có story vá tự động theo lịch; `US-FEED-15` chỉ cài lịch `feeds update` | PO |
| `Q-SRS-03` | Thời hạn phiên console 30 phút / 12 giờ / 5 phiên | AC của `US-CON-02`, `US-CON-03` dùng các số này | PO |
| `Q-SRS-06` | Phase 2 băm mật khẩu bằng `hashlib.scrypt` | `US-FLT-02` (epic) ghi theo SRS; xem lại khi tách story Phase 2 | PO + kỹ sư bảo mật |
| `Q-SRS-09` | `NFR-PERF-004`, `NFR-PERF-005`, `NFR-CAP-002` chưa đo | AC dẫn chiếu ngưỡng "mục tiêu, chưa đo" ở `US-PLAN-02`, `US-CMPT-01`; QA đo benchmark trước bản 2.0.0 | QA |
| `CR-FR-01` | Duyệt `FR-UPG-ACK-001` (lệnh `migrate ack`, `POST /api/v1/switches/{run_id}/acknowledgements`, `ERR-UPG-409-04`) theo DOC-SRS-QP-FR-001 §15.2 | `US-UPG-07` đã liên kết FR này và `AC-UPG-22` đã kiểm bước `migrate ack`; story giữ 5 SP, chưa cộng ước tính 3 SP Dev + 1 SP QA của `CR-FR-01` → ước lượng lại `US-UPG-07` khi PO duyệt. PO từ chối → gỡ FR khỏi `US-UPG-07` và §6, bỏ bước `migrate ack` ở `AC-UPG-22`, tổng về 167 FR | PO |
| `A-US-01` | Story point là ước lượng tương đối của BA trước buổi planning; đội Dev ước lượng lại bằng planning poker | Tổng 455 SP là con số tham khảo, không dùng để cam kết ngày phát hành | Dev |

## 8. Tài liệu tham chiếu
| Nguồn | Đường dẫn | Dùng cho | Trạng thái |
| :--- | :--- | :--- | :--- |
| OpenBA-Kit `skills/userstory/SKILL.md`, `_templates/27-userstory.md`, `rules/07-invest-user-story.md` | `/home/user/luongkam/openba-kit/` | Khung story, INVEST | Đã áp dụng |
| OpenBA-Kit `rules/14`, `16`, `17`, `18`, `19` | `/home/user/luongkam/openba-kit/rules/` | Truy vết, từ ngữ, actor, metadata, phiên bản | Đã áp dụng |
| Biên bản làm rõ yêu cầu v2 (DOC-BRS-QP-001) | [../brainstorms/quickpatch-v2-console.md](../brainstorms/quickpatch-v2-console.md) | Scope in/out, quyết định PO | Đã đọc |
| PRD v2 (DOC-PRD-QP-001) bản 1.0.1 | [../01-prd.md](../01-prd.md) | Persona (§2.1: `PER-04` là Primary chỉ đọc, xuất báo cáo), KR, định nghĩa P0/P1/P2 | Đã đối chiếu 2026-10-22 (bản 1.0.1) |
| SRS chính và 4 file chi tiết (DOC-SRS-QP-001, -FR-001, -BR-001, -ERR-001, -NFR-001) | [../srs/spec.md](../srs/spec.md), [../srs/functional-requirements.md](../srs/functional-requirements.md), [../srs/business-rules.md](../srs/business-rules.md), [../srs/error-matrix.md](../srs/error-matrix.md), [../srs/nfr.md](../srs/nfr.md) | Registry mã, ngưỡng số; DOC-SRS-QP-FR-001 1.0.1: tên 168 FR (27 tên đổi theo `CR-FR-06`), `FR-UPG-ACK-001` và `CR-FR-01` (§15.2) | Đã đối chiếu 2026-10-22 (FR 1.0.1) |
| Acceptance criteria UPG, JOB/FLT (DOC-AC-QP-UPG, DOC-AC-QP-JOB) bản 1.0.1 | [acceptance-criteria-upg.md](acceptance-criteria-upg.md), [acceptance-criteria-job-flt.md](acceptance-criteria-job-flt.md) | `AC-UPG-22` (bước `migrate ack`, `FR-UPG-ACK-001`); `AC-JOB-25` của `US-JOB-06` (tách từ `AC-JOB-18`) | Đã đối chiếu 2026-10-22 |
| Phụ lục SRS FEED, ENV, SCN | `../srs/data-sources*.md`, `../srs/environment-playbooks*.md`, `../srs/version-scenarios-*.md` | Chi tiết FR đã phát hành ở phụ lục | Đã đọc |
| Danh mục use case (DOC-UC-QP-000) | [../usecases/index.md](../usecases/index.md) | Ánh xạ UC → FR, actor | Đã đọc |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` (881 dòng) | Chuỗi thông báo, mã thoát, `STATE_DIR` kế thừa trong AC của `US-CLI-03`, `US-PTCH-*` | Đã đọc các dòng 39–876 liên quan (`grep`) |
