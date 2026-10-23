---
id: DOC-RTM-QP-001
title: Ma trận truy vết yêu cầu (RTM) FR → US → AC → TC — php-quickpatch v2
version: 1.0.2
phase: Testing
domain: Security Patch Management
tags: [rtm, traceability, test-cases, functional-requirements, userstory, openba]
depends_on:
  - DOC-SRS-QP-FR-001
  - DOC-US-QP-001
  - DOC-AC-QP-000
  - DOC-TC-QP-000
  - DOC-TC-QP-COV
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Ma trận truy vết yêu cầu (RTM) — FR → US → AC → TC — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo RTM theo rule 14 cho 167/167 FR, 120 user story, 372 AC và 402 test case; mỗi FR P0 có ≥ 1 test case (`NFR-MNT-004`) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: 36 dòng test case bổ sung dùng chung cho nhiều FR ghi cột User Story ID dạng "`US-…` (FR) / `US-…` (TC)" để story sở hữu test case khớp cột Story / AC của file test case; §1 thêm quy ước cột User Story ID, cột AC của dòng bổ sung và 5 phép kiểm tự động; chép lại tên 35 FR (108 dòng) theo [functional-requirements.md](../srs/functional-requirements.md) v1.0.1, gồm `FR-UPG-NODE-001`, `FR-UPG-SWT-001`, `FR-UPG-INST-001`, `FR-UPG-RBK-001`, `FR-FEED-CMD-001/004/005`, `FR-FEED-NORM-001` và 27 tên FR SRS đổi sang dạng động từ + tân ngữ |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review: thêm 3 dòng cho 2 test case bổ sung chưa truy vết — `TC-UPG-108` ↔ `FR-UPG-SEQ-001` (`US-UPG-07`), `TC-CON-103` ↔ `FR-CON-JOB-001` (`US-CON-10`) và ↔ `FR-JOB-LOG-002` (`US-JOB-06` (FR) / `US-CON-10` (TC)); thêm 2 dòng khoảng trống: `FR-UPG-ACK-001` (FR P0 mới của SRS 1.0.1, chưa có test case, backlog chưa liên kết story) và `AC-JOB-25` (AC mới của `US-JOB-06`, chưa có `TC-JOB-025`). §1 thêm quy ước dòng khoảng trống, trạng thái `Chờ bổ sung test case` và phép kiểm 6 (độ đầy đủ); §2 sửa thành 168 FR, 142 FR P0, 167/168 FR và 141/142 FR P0 có test case, 510 dòng, đối chiếu 404 test case và 373 AC; thêm §2.1 liệt kê khoảng trống và file phải sửa. Không liên kết tới `TC-JOB-025` vì test case này chưa tồn tại |

## 1. Quy ước
- Cột theo mẫu rule 14: FR ID, Tên yêu cầu chức năng, User Story ID, Acceptance Criteria, Test Case ID, Loại kiểm thử, Trạng thái. Mỗi dòng là 1 cặp FR ↔ test case; FR được kiểm bởi n test case có n dòng.
- Tên yêu cầu chức năng: chép nguyên văn cột tên FR của [functional-requirements.md](../srs/functional-requirements.md) (bản 1.0.1); khi SRS đổi tên FR, RTM đổi theo ở bản kế tiếp.
- User Story ID: story chứa FR ở cột "FR liên kết" của [backlog.md](../userstories/backlog.md). Khi test case thuộc story khác (test case bổ sung dùng chung cho nhiều FR, vd `TC-SCN-101` thuộc `US-SCN-02` nhưng cũng kiểm `FR-SCN-CLS-001` của `US-SCN-01`), cột ghi "`US-SCN-01` (FR) / `US-SCN-02` (TC)": vế (FR) là story chứa FR, vế (TC) là story ở cột Story / AC của test case. Bản 1.0.2 có 37 dòng dạng này.
- Acceptance Criteria: `AC-*` nguồn kèm nhóm scenario; test case bổ sung ghi `bổ sung (mở rộng …)` chép nguyên văn từ cột Story / AC của test case. AC trong ngoặc có thể thuộc story thứ ba (vd `AC-PTCH-05` của `US-PTCH-02` trong `TC-SCN-106`), vì test case bổ sung mở rộng nhiều AC liên module; truy vết AC → story tra ở [acceptance-criteria.md](../userstories/acceptance-criteria.md).
- Kiểm tự động trước mỗi lần phát hành RTM (script đối chiếu RTM với `test-cases*.md`, `functional-requirements.md`, `backlog.md`, `acceptance-criteria*.md`); mọi phép kiểm phải đạt 100% số dòng áp dụng:
  1. Story ở cột Story / AC của test case ∈ tập `US-*` của cột User Story ID trên dòng RTM.
  2. Vế (FR), hoặc giá trị duy nhất, của cột User Story ID là story có FR của dòng trong cột "FR liên kết" của backlog.
  3. Cột Acceptance Criteria: dòng thường chứa đúng mã `AC-*` của test case; dòng bổ sung trùng nguyên văn phần sau dấu "/" ở cột Story / AC của test case.
  4. Tên FR trùng nguyên văn tên trong `functional-requirements.md`.
  5. Liên kết Test Case ID trỏ đúng file chứa test case đó.
  6. Độ đầy đủ: mọi `FR-*` của `functional-requirements.md`, mọi `TC-*` của `test-cases*.md` và mọi `AC-*` (tag Gherkin `@AC-*` của `acceptance-criteria*.md`) xuất hiện ở ≥ 1 dòng RTM.
- Dòng khoảng trống: FR hoặc AC chưa có test case vẫn có 1 dòng để khoảng trống hiển thị trong RTM; cột Test Case ID ghi "Chưa có test case" kèm việc còn thiếu, cột Loại kiểm thử ghi "—", Trạng thái `Chờ bổ sung test case`. Dòng khoảng trống không áp phép kiểm 1, 3, 5 (không có test case) và được liệt kê ở §2.1; dòng sẽ được thay bằng dòng thường khi file test case bổ sung mã tương ứng.
- Kết quả kiểm bản 1.0.2 (đối chiếu 168 FR, 404 test case, 373 AC): 508/508 dòng có test case đạt cả 5 phép kiểm; phép kiểm 6 đạt: 404/404 test case có dòng thường, 168/168 FR và 373/373 AC có dòng, trong đó `FR-UPG-ACK-001` và `AC-JOB-25` chỉ có dòng khoảng trống (§2.1); dòng khoảng trống `FR-UPG-ACK-001` không đạt phép kiểm 2 vì backlog chưa liên kết FR này với story. Trước sửa: phép kiểm 6 thiếu 1 FR (`FR-UPG-ACK-001`), 2 test case (`TC-UPG-108`, `TC-CON-103`) và 1 AC (`AC-JOB-25`).
- Loại kiểm thử: loại chính · nhóm (định nghĩa ở [test-cases.md §1.4](test-cases.md)).
- Trạng thái: `Sẵn sàng test` (Phase 1, story P0/P1 đã đủ INVEST); `Chờ tách story (epic P2)` (story mức epic P2); `Đặc tả Phase 2 — chưa thực thi`; `Chờ bổ sung test case` (dòng khoảng trống). Kết quả chạy (`Đạt`/`Không đạt`/`Bị chặn`) ghi trong báo cáo kiểm thử, không ghi vào RTM.
- Ánh xạ AC → FR: story có 1 FR thì mọi AC truy vết tới FR đó; story có nhiều FR thì mỗi AC truy vết tới FR mà scenario kiểm chứng.

## 2. Tổng hợp độ phủ FR
| Module | Số FR | FR P0 | FR có ≥ 1 TC | FR P0 có ≥ 1 TC | Số dòng RTM | Tỉ lệ phủ FR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `SCAN` — Nhận diện & kiểm kê | 8 | 7 | 8 | 7 | 19 | 100% |
| `SCN` — Kịch bản phiên bản & checklist | 7 | 7 | 7 | 7 | 34 | 100% |
| `FEED` — Dữ liệu CVE / vòng đời online | 35 | 27 | 35 | 27 | 93 | 100% |
| `ASMT` — Đánh giá bảo mật | 9 | 9 | 9 | 9 | 28 | 100% |
| `PLAN` — Kế hoạch nâng cấp | 8 | 8 | 8 | 8 | 34 | 100% |
| `CMPT` — Quét tương thích | 14 | 10 | 14 | 10 | 41 | 100% |
| `PTCH` — Vá cùng nhánh | 14 | 14 | 14 | 14 | 34 | 100% |
| `UPG` — Nâng cấp khác nhánh / chuyển site | 20 | 17 | 19 | 16 | 68 | 95% |
| `CON` — Web console Phase 1 | 22 | 20 | 22 | 20 | 71 | 100% |
| `JOB` — Job runner, log, audit | 10 | 8 | 10 | 8 | 29 | 100% |
| `CLI` — Giao diện dòng lệnh | 10 | 9 | 10 | 9 | 31 | 100% |
| `RPT` — Báo cáo | 2 | 0 | 2 | 0 | 6 | 100% |
| `FLT` — Quản lý nhiều server (Phase 2) | 9 | 6 | 9 | 6 | 22 | 100% |
| **Tổng** | **168** | **142** | **167** | **141** | **510** | **99,4%** |

Số dòng RTM gồm 508 dòng có test case và 2 dòng khoảng trống. Tỉ lệ phủ FR = FR có ≥ 1 TC / Số FR. `NFR-MNT-004` (mỗi FR P0 có ≥ 1 test case trước phát hành) **chưa đạt**: 141/142 FR P0, thiếu `FR-UPG-ACK-001`.

### 2.1 Khoảng trống truy vết
| # | Mã thiếu | Hiện trạng (đã kiểm ngày 2026-10-22) | Việc cần làm | File phải sửa |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `FR-UPG-ACK-001` (P0, Phase 1) | Có ở [functional-requirements.md](../srs/functional-requirements.md) v1.0.1 và trong `AC-UPG-22` v1.0.1 (bước `migrate ack 20261022-140000 --reason …`); backlog chưa liên kết FR với story nào (`US-UPG-07` chỉ có `FR-UPG-SEQ-001`); 0 test case chạy `migrate ack` hoặc `POST /api/v1/switches/{run_id}/acknowledgements`. `TC-UPG-022` KQ2 và `TC-UPG-023` KQ2 chỉ kiểm trạng thái trước/sau xác nhận, không kiểm đầu ra `result.acknowledgement`, 2 bản ghi audit và `ERR-UPG-409-04`, nên không được tính là test case của FR này | Thêm `FR-UPG-ACK-001` vào cột "FR liên kết" của `US-UPG-07`; sinh lại `TC-UPG-022` theo `AC-UPG-22` v1.0.1 và thêm test case cho `ERR-UPG-409-04`; sau đó thay dòng khoảng trống ở §3.8 bằng dòng thường | [backlog.md](../userstories/backlog.md), [test-cases-upg.md](test-cases-upg.md), rtm.md |
| 2 | `AC-JOB-25` (Boundary, `US-JOB-06`) | Có ở [acceptance-criteria-job-flt.md](../userstories/acceptance-criteria-job-flt.md) v1.0.1 (tách từ `AC-JOB-18`); chưa có `TC-JOB-025`. Cùng giới hạn luồng SSE đang được kiểm ở `TC-CON-031` KQ2 (luồng thứ 4 của phiên) và `TC-CON-103` KQ2 (luồng thứ 11 của console); `TC-JOB-018` KQ2 còn nêu giới hạn nhưng không có bước thao tác | Sinh `TC-JOB-025` từ `AC-JOB-25`, sinh lại `TC-JOB-018` chỉ còn hành vi `Last-Event-ID`; thêm `AC-JOB-25` vào dòng `US-JOB-06` của backlog và [acceptance-criteria.md](../userstories/acceptance-criteria.md); sau đó thay dòng khoảng trống ở §3.10 bằng dòng có `TC-JOB-025` | [test-cases-job-flt.md](test-cases-job-flt.md), [backlog.md](../userstories/backlog.md), [acceptance-criteria.md](../userstories/acceptance-criteria.md), rtm.md |

## 3. Ma trận truy vết theo module

### 3.1 Module `SCAN` — Nhận diện & kiểm kê
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-SCAN-ENV-001` | Nhận diện môi trường và chọn playbook | `US-SCAN-01` | `AC-SCAN-01` (Happy path) | [`TC-SCAN-001`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-ENV-001` | Nhận diện môi trường và chọn playbook | `US-SCAN-01` | `AC-SCAN-02` (Negative) | [`TC-SCAN-002`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCAN-MAP-001` | Kiểm kê site → runtime | `US-SCAN-01` | `AC-SCAN-01` (Happy path) | [`TC-SCAN-001`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-MAP-001` | Kiểm kê site → runtime | `US-SCAN-01` | `AC-SCAN-03` (Boundary) | [`TC-SCAN-003`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | `US-SCAN-02` | `AC-SCAN-04` (Happy path) | [`TC-SCAN-004`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | `US-SCAN-02` | `AC-SCAN-05` (Negative) | [`TC-SCAN-005`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | `US-SCAN-02` | `AC-SCAN-06` (Boundary) | [`TC-SCAN-006`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCAN-RT-002` | Phát hiện runtime Node.js | `US-SCAN-02` | `AC-SCAN-04` (Happy path) | [`TC-SCAN-004`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | `US-SCAN-03` | `AC-SCAN-07` (Happy path) | [`TC-SCAN-007`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | `US-SCAN-03` | `AC-SCAN-08` (Negative) | [`TC-SCAN-008`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | `US-SCAN-03` | `AC-SCAN-09` (Boundary) | [`TC-SCAN-009`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCAN-PRJ-002` | Kiểm kê container đang chạy | `US-SCAN-03` | `AC-SCAN-07` (Happy path) | [`TC-SCAN-007`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-PRJ-002` | Kiểm kê container đang chạy | `US-SCAN-03` | `AC-SCAN-09` (Boundary) | [`TC-SCAN-009`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | `US-SCAN-04` | `AC-SCAN-10` (Happy path) | [`TC-SCAN-010`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | `US-SCAN-04` | `AC-SCAN-11` (Negative) | [`TC-SCAN-011`](test-cases.md) | Security · Negative | Sẵn sàng test |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | `US-SCAN-04` | `AC-SCAN-12` (Boundary) | [`TC-SCAN-012`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | `US-SCAN-05` | `AC-SCAN-13` (Happy path) | [`TC-SCAN-013`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | `US-SCAN-05` | `AC-SCAN-14` (Negative) | [`TC-SCAN-014`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | `US-SCAN-05` | `AC-SCAN-15` (Boundary) | [`TC-SCAN-015`](test-cases.md) | Functional · Boundary | Sẵn sàng test |

### 3.2 Module `SCN` — Kịch bản phiên bản & checklist
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` | `AC-SCN-01` (Happy path) | [`TC-SCN-001`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` | `AC-SCN-03` (Negative) | [`TC-SCN-003`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` | `AC-SCN-04` (Boundary) | [`TC-SCN-004`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-07`) | [`TC-SCN-101`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-05`) | [`TC-SCN-103`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | `US-SCN-01` | bổ sung (mở rộng `AC-SCN-04`, `AC-PTCH-05`) | [`TC-SCN-106`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | `US-SCN-01` | `AC-SCN-02` (Happy path) | [`TC-SCN-002`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | `US-SCN-01` | `AC-SCN-04` (Boundary) | [`TC-SCN-004`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | `US-SCN-01` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-05`) | [`TC-SCN-107`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | `US-SCN-01` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-02`, `AC-PLAN-24`) | [`TC-SCN-109`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | `US-SCN-01` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-05`, `AC-PLAN-04`) | [`TC-SCN-110`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LOCK-001` | Khoá tự động hoá với phiên bản bất thường | `US-SCN-01` | `AC-SCN-03` (Negative) | [`TC-SCN-003`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCN-LOCK-001` | Khoá tự động hoá với phiên bản bất thường | `US-SCN-01` | `AC-SCN-04` (Boundary) | [`TC-SCN-004`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | `AC-SCN-05` (Happy path) | [`TC-SCN-005`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | `AC-SCN-06` (Negative) | [`TC-SCN-006`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | `AC-SCN-07` (Boundary) | [`TC-SCN-007`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-07`) | [`TC-SCN-101`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | bổ sung (mở rộng `AC-SCN-05`) | [`TC-SCN-103`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` (FR) / `US-FEED-08` (TC) | bổ sung (mở rộng `AC-FEED-23`) | [`TC-SCN-104`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` (FR) / `US-FEED-08` (TC) | bổ sung (mở rộng `AC-FEED-24`) | [`TC-SCN-105`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-05`) | [`TC-SCN-107`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | bổ sung (mở rộng `AC-SCN-02`, `AC-PLAN-24`) | [`TC-SCN-109`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | `US-SCN-02` | bổ sung (mở rộng `AC-SCN-05`, `AC-PLAN-04`) | [`TC-SCN-110`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | `US-SCN-03` | `AC-SCN-08` (Happy path) | [`TC-SCN-008`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | `US-SCN-03` | `AC-SCN-09` (Negative) | [`TC-SCN-009`](test-cases.md) | Security · Negative | Sẵn sàng test |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | `US-SCN-03` | `AC-SCN-10` (Boundary) | [`TC-SCN-010`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | `US-SCN-04` | `AC-SCN-11` (Happy path) | [`TC-SCN-011`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | `US-SCN-04` | `AC-SCN-12` (Negative) | [`TC-SCN-012`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | `US-SCN-04` | `AC-SCN-13` (Boundary) | [`TC-SCN-013`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | `US-SCN-04` | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-02`, `AC-CMPT-09`) | [`TC-SCN-102`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | `US-SCN-04` | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-03`) | [`TC-SCN-108`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | `US-SCN-05` | `AC-SCN-14` (Happy path) | [`TC-SCN-014`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | `US-SCN-05` | `AC-SCN-15` (Negative) | [`TC-SCN-015`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | `US-SCN-05` | `AC-SCN-16` (Boundary) | [`TC-SCN-016`](test-cases.md) | Functional · Boundary | Sẵn sàng test |

### 3.3 Module `FEED` — Dữ liệu CVE / vòng đời online
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | `US-FEED-01` | `AC-FEED-01` (Happy path) | [`TC-FEED-001`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | `US-FEED-01` | `AC-FEED-02` (Negative) | [`TC-FEED-002`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | `US-FEED-01` | `AC-FEED-03` (Negative) | [`TC-FEED-003`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | `US-FEED-01` | `AC-FEED-04` (Boundary) | [`TC-FEED-004`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | `US-FEED-01` | bổ sung (mở rộng `AC-CLI-14`) | [`TC-FEED-104`](test-cases-feed.md) | Compat · Offline/Stale | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | `AC-FEED-01` (Happy path) | [`TC-FEED-001`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | `AC-FEED-02` (Negative) | [`TC-FEED-002`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | `AC-FEED-03` (Negative) | [`TC-FEED-003`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | `AC-FEED-04` (Boundary) | [`TC-FEED-004`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | bổ sung (mở rộng `AC-FEED-02`) | [`TC-FEED-103`](test-cases-feed.md) | Integration · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` | bổ sung (mở rộng `AC-CLI-14`) | [`TC-FEED-104`](test-cases-feed.md) | Compat · Offline/Stale | Sẵn sàng test |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | `US-FEED-01` (FR) / `US-FEED-02` (TC) | bổ sung (mở rộng `AC-FEED-06`) | [`TC-FEED-106`](test-cases-feed.md) | Integration · Bổ sung ERR | Sẵn sàng test |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | `US-FEED-02` | `AC-FEED-05` (Happy path) | [`TC-FEED-005`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | `US-FEED-02` | `AC-FEED-06` (Negative) | [`TC-FEED-006`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | `US-FEED-02` | `AC-FEED-07` (Boundary) | [`TC-FEED-007`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | `US-FEED-02` | bổ sung (mở rộng `AC-FEED-07`, `AC-FEED-08`) | [`TC-FEED-101`](test-cases-feed.md) | Integration · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | `US-FEED-02` | bổ sung (mở rộng `AC-FEED-05`) | [`TC-FEED-107`](test-cases-feed.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-EOL-002` | Bổ sung bản ghi vòng đời tĩnh | `US-FEED-02` | `AC-FEED-05` (Happy path) | [`TC-FEED-005`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-EOL-003` | Đồng bộ ma trận framework/CMS ↔ PHP | `US-FEED-02` | `AC-FEED-05` (Happy path) | [`TC-FEED-005`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | `US-FEED-03` | `AC-FEED-08` (Happy path) | [`TC-FEED-008`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | `US-FEED-03` | `AC-FEED-09` (Negative) | [`TC-FEED-009`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | `US-FEED-03` | `AC-FEED-10` (Security) | [`TC-FEED-010`](test-cases-feed.md) | Security · Security | Sẵn sàng test |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | `US-FEED-03` (FR) / `US-FEED-02` (TC) | bổ sung (mở rộng `AC-FEED-07`, `AC-FEED-08`) | [`TC-FEED-101`](test-cases-feed.md) | Integration · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-REL-002` | Đồng bộ bản phát hành Node.js | `US-FEED-03` | `AC-FEED-08` (Happy path) | [`TC-FEED-008`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-REL-003` | Đồng bộ trạng thái WordPress core | `US-FEED-03` | `AC-FEED-08` (Happy path) | [`TC-FEED-008`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | `US-FEED-04` | `AC-FEED-11` (Happy path) | [`TC-FEED-011`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | `US-FEED-04` | `AC-FEED-12` (Negative) | [`TC-FEED-012`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | `US-FEED-04` | `AC-FEED-13` (Boundary) | [`TC-FEED-013`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-PCVE-002` | Làm giàu alias GHSA ↔ CVE cho PHP | `US-FEED-04` | `AC-FEED-11` (Happy path) | [`TC-FEED-011`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-PCVE-003` | Tra CVE.org khi NVD thiếu | `US-FEED-04` | `AC-FEED-13` (Boundary) | [`TC-FEED-013`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | `US-FEED-05` | `AC-FEED-14` (Happy path) | [`TC-FEED-014`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | `US-FEED-05` | `AC-FEED-15` (Negative) | [`TC-FEED-015`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | `US-FEED-05` | `AC-FEED-16` (Boundary) | [`TC-FEED-016`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-WCVE-001` | Đồng bộ CVE WordPress core | `US-FEED-05` | `AC-FEED-14` (Happy path) | [`TC-FEED-014`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | `US-FEED-06` | `AC-FEED-17` (Happy path) | [`TC-FEED-017`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | `US-FEED-06` | `AC-FEED-18` (Negative) | [`TC-FEED-018`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | `US-FEED-06` | `AC-FEED-19` (Boundary) | [`TC-FEED-019`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | `US-FEED-07` | `AC-FEED-20` (Happy path) | [`TC-FEED-020`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | `US-FEED-07` | `AC-FEED-21` (Negative) | [`TC-FEED-021`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | `US-FEED-07` | `AC-FEED-22` (Security) | [`TC-FEED-022`](test-cases-feed.md) | Security · Security | Sẵn sàng test |
| `FR-FEED-DIST-001` | Tra advisory distro cho gói runtime | `US-FEED-08` | `AC-FEED-23` (Happy path) | [`TC-FEED-023`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-DIST-001` | Tra advisory distro cho gói runtime | `US-FEED-08` | bổ sung (mở rộng `AC-FEED-23`) | [`TC-SCN-104`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-FEED-DIST-002` | Dự phòng tracker distro và changelog | `US-FEED-08` | `AC-FEED-24` (Negative) | [`TC-FEED-024`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` | `AC-FEED-23` (Happy path) | [`TC-FEED-023`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` | `AC-FEED-24` (Negative) | [`TC-FEED-024`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` | `AC-FEED-25` (Boundary) | [`TC-FEED-025`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-05`) | [`TC-SCN-103`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` | bổ sung (mở rộng `AC-FEED-23`) | [`TC-SCN-104`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | `US-FEED-08` | bổ sung (mở rộng `AC-FEED-24`) | [`TC-SCN-105`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-FEED-NORM-001` | Chuẩn hoá và khử trùng lặp advisory | `US-FEED-09` | `AC-FEED-26` (Happy path) | [`TC-FEED-026`](test-cases-feed.md) | Compat · Happy path | Sẵn sàng test |
| `FR-FEED-NORM-001` | Chuẩn hoá và khử trùng lặp advisory | `US-FEED-09` | `AC-FEED-28` (Boundary) | [`TC-FEED-028`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | `US-FEED-09` (FR) / `US-ASMT-01` (TC) | bổ sung (mở rộng `AC-ASMT-01`) | [`TC-ASMT-101`](test-cases.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | `US-FEED-09` | `AC-FEED-26` (Happy path) | [`TC-FEED-026`](test-cases-feed.md) | Compat · Happy path | Sẵn sàng test |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | `US-FEED-09` | `AC-FEED-27` (Negative) | [`TC-FEED-027`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | `US-FEED-10` | `AC-FEED-29` (Happy path) | [`TC-FEED-029`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | `US-FEED-10` | `AC-FEED-30` (Negative) | [`TC-FEED-030`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | `US-FEED-10` | `AC-FEED-31` (Boundary) | [`TC-FEED-031`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | `US-FEED-10` | bổ sung (mở rộng `AC-FEED-31`, `AC-SCN-06`) | [`TC-FEED-102`](test-cases-feed.md) | Functional · Offline/Stale | Sẵn sàng test |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | `US-FEED-11` | `AC-FEED-32` (Happy path) | [`TC-FEED-032`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | `US-FEED-11` | `AC-FEED-34` (Boundary) | [`TC-FEED-034`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | `US-FEED-11` | bổ sung (mở rộng `AC-FEED-32`) | [`TC-FEED-105`](test-cases-feed.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | `US-FEED-11` (FR) / `US-FEED-02` (TC) | bổ sung (mở rộng `AC-FEED-06`) | [`TC-FEED-106`](test-cases-feed.md) | Integration · Bổ sung ERR | Sẵn sàng test |
| `FR-FEED-CACH-002` | Dựng và thay bundle nguyên tử | `US-FEED-11` | `AC-FEED-32` (Happy path) | [`TC-FEED-032`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-CACH-002` | Dựng và thay bundle nguyên tử | `US-FEED-11` | `AC-FEED-33` (Negative) | [`TC-FEED-033`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-CACH-003` | Dọn dẹp theo giới hạn dung lượng | `US-FEED-11` | `AC-FEED-34` (Boundary) | [`TC-FEED-034`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | `US-FEED-12` | `AC-FEED-35` (Happy path) | [`TC-FEED-035`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | `US-FEED-12` | `AC-FEED-36` (Negative) | [`TC-FEED-036`](test-cases-feed.md) | Security · Negative | Sẵn sàng test |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | `US-FEED-12` | `AC-FEED-37` (Boundary) | [`TC-FEED-037`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | `US-FEED-12` (FR) / `US-FEED-10` (TC) | bổ sung (mở rộng `AC-FEED-31`, `AC-SCN-06`) | [`TC-FEED-102`](test-cases-feed.md) | Functional · Offline/Stale | Sẵn sàng test |
| `FR-FEED-SNAP-002` | Xuất snapshot | `US-FEED-13` | `AC-FEED-38` (Happy path) | [`TC-FEED-038`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-SNAP-003` | Nhập snapshot | `US-FEED-13` | `AC-FEED-39` (Happy path) | [`TC-FEED-039`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-SNAP-003` | Nhập snapshot | `US-FEED-13` | `AC-FEED-40` (Negative) | [`TC-FEED-040`](test-cases-feed.md) | Security · Negative | Sẵn sàng test |
| `FR-FEED-SNAP-003` | Nhập snapshot | `US-FEED-13` | `AC-FEED-41` (Security) | [`TC-FEED-041`](test-cases-feed.md) | Security · Security | Sẵn sàng test |
| `FR-FEED-CMD-004` | Lệnh `feeds export` (bí danh `snapshot export`) | `US-FEED-13` | `AC-FEED-38` (Happy path) | [`TC-FEED-038`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-CMD-004` | Lệnh `feeds export` (bí danh `snapshot export`) | `US-FEED-13` (FR) / `US-FEED-01` (TC) | bổ sung (mở rộng `AC-CLI-14`) | [`TC-FEED-104`](test-cases-feed.md) | Compat · Offline/Stale | Sẵn sàng test |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | `US-FEED-13` | `AC-FEED-39` (Happy path) | [`TC-FEED-039`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | `US-FEED-13` | `AC-FEED-40` (Negative) | [`TC-FEED-040`](test-cases-feed.md) | Security · Negative | Sẵn sàng test |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | `US-FEED-13` | `AC-FEED-41` (Security) | [`TC-FEED-041`](test-cases-feed.md) | Security · Security | Sẵn sàng test |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | `US-FEED-14` | `AC-FEED-42` (Happy path) | [`TC-FEED-042`](test-cases-feed.md) | Integration · Happy path | Sẵn sàng test |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | `US-FEED-14` | `AC-FEED-43` (Negative) | [`TC-FEED-043`](test-cases-feed.md) | Integration · Negative | Sẵn sàng test |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | `US-FEED-14` | `AC-FEED-44` (Boundary) | [`TC-FEED-044`](test-cases-feed.md) | Integration · Boundary | Sẵn sàng test |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | `US-FEED-15` | `AC-FEED-45` (Happy path) | [`TC-FEED-045`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | `US-FEED-15` | `AC-FEED-46` (Negative) | [`TC-FEED-046`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | `US-FEED-15` | `AC-FEED-47` (Boundary) | [`TC-FEED-047`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | `US-FEED-15` | `AC-FEED-45` (Happy path) | [`TC-FEED-045`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | `US-FEED-15` | `AC-FEED-46` (Negative) | [`TC-FEED-046`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | `US-FEED-15` | `AC-FEED-47` (Boundary) | [`TC-FEED-047`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-CMD-002` | Lệnh `feeds status` | `US-FEED-16` | `AC-FEED-48` (Happy path) | [`TC-FEED-048`](test-cases-feed.md) | Functional · Happy path | Sẵn sàng test |
| `FR-FEED-CMD-002` | Lệnh `feeds status` | `US-FEED-16` | `AC-FEED-50` (Boundary) | [`TC-FEED-050`](test-cases-feed.md) | Functional · Boundary | Sẵn sàng test |
| `FR-FEED-CMD-003` | Lệnh `feeds verify` | `US-FEED-16` | `AC-FEED-49` (Negative) | [`TC-FEED-049`](test-cases-feed.md) | Functional · Negative | Sẵn sàng test |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | `US-FEED-17` | `AC-FEED-51` (Happy path) | [`TC-FEED-051`](test-cases-feed.md) | Integration · Happy path | Chờ tách story (epic P2) |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | `US-FEED-17` | `AC-FEED-52` (Negative) | [`TC-FEED-052`](test-cases-feed.md) | Integration · Negative | Chờ tách story (epic P2) |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | `US-FEED-17` | `AC-FEED-53` (Security) | [`TC-FEED-053`](test-cases-feed.md) | Security · Security | Chờ tách story (epic P2) |

### 3.4 Module `ASMT` — Đánh giá bảo mật
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | `US-ASMT-01` | `AC-ASMT-01` (Happy path) | [`TC-ASMT-001`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | `US-ASMT-01` | `AC-ASMT-02` (Boundary) | [`TC-ASMT-002`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | `US-ASMT-01` | `AC-ASMT-03` (Negative) | [`TC-ASMT-003`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | `US-ASMT-01` | `AC-ASMT-04` (Boundary) | [`TC-ASMT-004`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | `US-ASMT-01` | bổ sung (mở rộng `AC-ASMT-01`) | [`TC-ASMT-101`](test-cases.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-ASMT-RISK-001` | Tính điểm rủi ro runtime | `US-ASMT-01` | `AC-ASMT-01` (Happy path) | [`TC-ASMT-001`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-RISK-001` | Tính điểm rủi ro runtime | `US-ASMT-01` | `AC-ASMT-02` (Boundary) | [`TC-ASMT-002`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` | `AC-ASMT-05` (Happy path) | [`TC-ASMT-005`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` | `AC-ASMT-06` (Negative) | [`TC-ASMT-006`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` | `AC-ASMT-07` (Boundary) | [`TC-ASMT-007`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-07`) | [`TC-SCN-101`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` (FR) / `US-SCN-01` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-PTCH-05`) | [`TC-SCN-106`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-SCN-05`) | [`TC-SCN-107`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | `US-ASMT-02` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-05`, `AC-PLAN-04`) | [`TC-SCN-110`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-ASMT-CAND-002` | Xác định khả năng cài của ứng viên | `US-ASMT-02` | `AC-ASMT-05` (Happy path) | [`TC-ASMT-005`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-CMP-001` | So sánh hiện tại với ứng viên | `US-ASMT-03` | `AC-ASMT-08` (Happy path) | [`TC-ASMT-008`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-CMP-001` | So sánh hiện tại với ứng viên | `US-ASMT-03` | `AC-ASMT-09` (Negative) | [`TC-ASMT-009`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-ASMT-RISK-002` | So sánh điểm hiện tại và ứng viên | `US-ASMT-03` | `AC-ASMT-08` (Happy path) | [`TC-ASMT-008`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-RISK-002` | So sánh điểm hiện tại và ứng viên | `US-ASMT-03` | `AC-ASMT-10` (Boundary) | [`TC-ASMT-010`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | `US-ASMT-04` | `AC-ASMT-11` (Happy path) | [`TC-ASMT-011`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | `US-ASMT-04` | `AC-ASMT-12` (Negative) | [`TC-ASMT-012`](test-cases.md) | Functional · Negative | Sẵn sàng test |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | `US-ASMT-04` | `AC-ASMT-13` (Boundary) | [`TC-ASMT-013`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | `US-ASMT-05` | `AC-ASMT-14` (Happy path) | [`TC-ASMT-014`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | `US-ASMT-05` | `AC-ASMT-15` (Negative) | [`TC-ASMT-015`](test-cases.md) | Integration · Negative | Sẵn sàng test |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | `US-ASMT-05` | `AC-ASMT-16` (Boundary) | [`TC-ASMT-016`](test-cases.md) | Functional · Boundary | Sẵn sàng test |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | `US-ASMT-06` | `AC-ASMT-17` (Happy path) | [`TC-ASMT-017`](test-cases.md) | Functional · Happy path | Sẵn sàng test |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | `US-ASMT-06` | `AC-ASMT-18` (Negative) | [`TC-ASMT-018`](test-cases.md) | Integration · Negative | Sẵn sàng test |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | `US-ASMT-06` | `AC-ASMT-19` (Boundary) | [`TC-ASMT-019`](test-cases.md) | Functional · Boundary | Sẵn sàng test |

### 3.5 Module `PLAN` — Kế hoạch nâng cấp
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` | `AC-PLAN-01` (Happy path) | [`TC-PLAN-001`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` | `AC-PLAN-02` (Negative) | [`TC-PLAN-002`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` | `AC-PLAN-03` (Negative) | [`TC-PLAN-003`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` | `AC-PLAN-04` (Boundary) | [`TC-PLAN-004`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` (FR) / `US-SCN-04` (TC) | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-02`, `AC-CMPT-09`) | [`TC-SCN-102`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | `US-PLAN-01` (FR) / `US-SCN-04` (TC) | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-03`) | [`TC-SCN-108`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | `US-PLAN-02` | `AC-PLAN-05` (Happy path) | [`TC-PLAN-005`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | `US-PLAN-02` | `AC-PLAN-06` (Negative) | [`TC-PLAN-006`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | `US-PLAN-02` | `AC-PLAN-07` (Boundary) | [`TC-PLAN-007`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | `US-PLAN-02` (FR) / `US-SCN-04` (TC) | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-02`, `AC-CMPT-09`) | [`TC-SCN-102`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | `US-PLAN-02` (FR) / `US-SCN-04` (TC) | bổ sung (mở rộng `AC-SCN-11`, `AC-PLAN-03`) | [`TC-SCN-108`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | `US-PLAN-03` | `AC-PLAN-08` (Happy path) | [`TC-PLAN-008`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | `US-PLAN-03` | `AC-PLAN-09` (Negative) | [`TC-PLAN-009`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | `US-PLAN-03` | `AC-PLAN-10` (Boundary) | [`TC-PLAN-010`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | `US-PLAN-04` | `AC-PLAN-11` (Happy path) | [`TC-PLAN-011`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | `US-PLAN-04` | `AC-PLAN-12` (Negative) | [`TC-PLAN-012`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | `US-PLAN-04` | `AC-PLAN-13` (Boundary) | [`TC-PLAN-013`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | `US-PLAN-05` | `AC-PLAN-14` (Happy path) | [`TC-PLAN-014`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | `US-PLAN-05` | `AC-PLAN-15` (Negative) | [`TC-PLAN-015`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | `US-PLAN-05` | `AC-PLAN-16` (Boundary) | [`TC-PLAN-016`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | `US-PLAN-05` (FR) / `US-UPG-13` (TC) | bổ sung (mở rộng `AC-UPG-41`) | [`TC-UPG-107`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | `US-PLAN-06` (FR) / `US-CMPT-06` (TC) | bổ sung (mở rộng `AC-CMPT-18`) | [`TC-CMPT-102`](test-cases-plan-cmpt.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | `US-PLAN-06` | `AC-PLAN-17` (Happy path) | [`TC-PLAN-017`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | `US-PLAN-06` | `AC-PLAN-18` (Negative) | [`TC-PLAN-018`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | `US-PLAN-06` | `AC-PLAN-19` (Boundary) | [`TC-PLAN-019`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | `US-PLAN-07` | `AC-PLAN-20` (Happy path) | [`TC-PLAN-020`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | `US-PLAN-07` | `AC-PLAN-21` (Negative) | [`TC-PLAN-021`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | `US-PLAN-07` | `AC-PLAN-22` (Negative) | [`TC-PLAN-022`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | `US-PLAN-07` | `AC-PLAN-23` (Boundary) | [`TC-PLAN-023`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | `US-PLAN-08` | `AC-PLAN-24` (Happy path) | [`TC-PLAN-024`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | `US-PLAN-08` | `AC-PLAN-25` (Negative) | [`TC-PLAN-025`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | `US-PLAN-08` | `AC-PLAN-26` (Boundary) | [`TC-PLAN-026`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | `US-PLAN-08` (FR) / `US-FEED-08` (TC) | bổ sung (mở rộng `AC-FEED-23`) | [`TC-SCN-104`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | `US-PLAN-08` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-02`, `AC-PLAN-24`) | [`TC-SCN-109`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |

### 3.6 Module `CMPT` — Quét tương thích
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | `US-CMPT-01` | `AC-CMPT-01` (Happy path) | [`TC-CMPT-001`](test-cases-plan-cmpt.md) | Integration · Happy path | Sẵn sàng test |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | `US-CMPT-01` | `AC-CMPT-02` (Negative) | [`TC-CMPT-002`](test-cases-plan-cmpt.md) | Integration · Negative | Sẵn sàng test |
| `FR-CMPT-TOOL-001` | Cài và quản lý công cụ quét | `US-CMPT-01` | `AC-CMPT-03` (Security) | [`TC-CMPT-003`](test-cases-plan-cmpt.md) | Security · Security | Sẵn sàng test |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | `US-CMPT-02` | `AC-CMPT-04` (Happy path) | [`TC-CMPT-004`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | `US-CMPT-02` | `AC-CMPT-05` (Negative) | [`TC-CMPT-005`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | `US-CMPT-02` | `AC-CMPT-06` (Boundary) | [`TC-CMPT-006`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-CODE-001` | Quét luật breaking change tĩnh | `US-CMPT-02` (FR) / `US-CMPT-06` (TC) | bổ sung (mở rộng `AC-CMPT-16`) | [`TC-CMPT-101`](test-cases-plan-cmpt.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | `US-CMPT-03` | `AC-CMPT-07` (Happy path) | [`TC-CMPT-007`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | `US-CMPT-03` | `AC-CMPT-08` (Negative) | [`TC-CMPT-008`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-CODE-002` | Quét PHPCompatibility | `US-CMPT-03` | `AC-CMPT-09` (Boundary) | [`TC-CMPT-009`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | `US-CMPT-04` | `AC-CMPT-10` (Happy path) | [`TC-CMPT-010`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | `US-CMPT-04` | `AC-CMPT-11` (Negative) | [`TC-CMPT-011`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-CODE-003` | Kiểm tra cú pháp bằng binary đích | `US-CMPT-04` | `AC-CMPT-12` (Boundary) | [`TC-CMPT-012`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | `US-CMPT-05` | `AC-CMPT-13` (Happy path) | [`TC-CMPT-013`](test-cases-plan-cmpt.md) | Integration · Happy path | Sẵn sàng test |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | `US-CMPT-05` | `AC-CMPT-14` (Negative) | [`TC-CMPT-014`](test-cases-plan-cmpt.md) | Integration · Negative | Sẵn sàng test |
| `FR-CMPT-COMP-001` | Kiểm tra nền tảng Composer | `US-CMPT-05` | `AC-CMPT-15` (Security) | [`TC-CMPT-015`](test-cases-plan-cmpt.md) | Security · Security | Sẵn sàng test |
| `FR-CMPT-COMP-002` | Tra phiên bản tối thiểu thoả trên Packagist | `US-CMPT-05` | `AC-CMPT-13` (Happy path) | [`TC-CMPT-013`](test-cases-plan-cmpt.md) | Integration · Happy path | Sẵn sàng test |
| `FR-CMPT-COMP-002` | Tra phiên bản tối thiểu thoả trên Packagist | `US-CMPT-05` | `AC-CMPT-14` (Negative) | [`TC-CMPT-014`](test-cases-plan-cmpt.md) | Integration · Negative | Sẵn sàng test |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | `US-CMPT-06` | `AC-CMPT-16` (Happy path) | [`TC-CMPT-016`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | `US-CMPT-06` | `AC-CMPT-18` (Boundary) | [`TC-CMPT-018`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | `US-CMPT-06` | bổ sung (mở rộng `AC-CMPT-16`) | [`TC-CMPT-101`](test-cases-plan-cmpt.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-CMPT-NPM-001` | Quét ràng buộc `engines.node` | `US-CMPT-06` | bổ sung (mở rộng `AC-CMPT-18`) | [`TC-CMPT-102`](test-cases-plan-cmpt.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-CMPT-NPM-002` | Phát hiện native addon | `US-CMPT-06` | `AC-CMPT-16` (Happy path) | [`TC-CMPT-016`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-NPM-002` | Phát hiện native addon | `US-CMPT-06` | `AC-CMPT-17` (Negative) | [`TC-CMPT-017`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-INI-001` | Quét directive ini bị gỡ | `US-CMPT-07` | `AC-CMPT-19` (Happy path) | [`TC-CMPT-019`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-INI-001` | Quét directive ini bị gỡ | `US-CMPT-07` | `AC-CMPT-21` (Boundary) | [`TC-CMPT-021`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | `US-CMPT-07` | `AC-CMPT-19` (Happy path) | [`TC-CMPT-019`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | `US-CMPT-07` | `AC-CMPT-20` (Negative) | [`TC-CMPT-020`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-EXT-001` | Đối chiếu extension trên runtime đích | `US-CMPT-07` | `AC-CMPT-21` (Boundary) | [`TC-CMPT-021`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | `US-CMPT-08` | `AC-CMPT-22` (Happy path) | [`TC-CMPT-022`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | `US-CMPT-08` | `AC-CMPT-23` (Negative) | [`TC-CMPT-023`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-LDR-001` | Nhận diện loader mã hoá | `US-CMPT-08` | `AC-CMPT-24` (Boundary) | [`TC-CMPT-024`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | `US-CMPT-09` | `AC-CMPT-25` (Happy path) | [`TC-CMPT-025`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | `US-CMPT-09` | `AC-CMPT-26` (Negative) | [`TC-CMPT-026`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-FWK-001` | Nhận diện framework/CMS và ma trận PHP | `US-CMPT-09` | `AC-CMPT-27` (Boundary) | [`TC-CMPT-027`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | `US-CMPT-10` | `AC-CMPT-28` (Happy path) | [`TC-CMPT-028`](test-cases-plan-cmpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | `US-CMPT-10` | `AC-CMPT-29` (Negative) | [`TC-CMPT-029`](test-cases-plan-cmpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CMPT-RES-001` | Kết luận tương thích theo site | `US-CMPT-10` | `AC-CMPT-30` (Boundary) | [`TC-CMPT-030`](test-cases-plan-cmpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | `US-CMPT-11` | `AC-CMPT-31` (Happy path) | [`TC-CMPT-031`](test-cases-plan-cmpt.md) | Functional · Happy path | Chờ tách story (epic P2) |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | `US-CMPT-11` | `AC-CMPT-32` (Negative) | [`TC-CMPT-032`](test-cases-plan-cmpt.md) | Functional · Negative | Chờ tách story (epic P2) |
| `FR-CMPT-RCT-001` | Chạy Rector tuỳ chọn trên bản sao | `US-CMPT-11` | `AC-CMPT-33` (Security) | [`TC-CMPT-033`](test-cases-plan-cmpt.md) | Security · Security | Chờ tách story (epic P2) |

### 3.7 Module `PTCH` — Vá cùng nhánh
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | `US-PTCH-01` | `AC-PTCH-01` (Happy path) | [`TC-PTCH-001`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | `US-PTCH-01` | `AC-PTCH-03` (Negative) | [`TC-PTCH-003`](test-cases-ptch-cli-rpt.md) | Integration · Negative | Sẵn sàng test |
| `FR-PTCH-PHP-001` | Vá runtime PHP cùng nhánh | `US-PTCH-01` | `AC-PTCH-04` (Boundary) | [`TC-PTCH-004`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | `US-PTCH-01` | `AC-PTCH-01` (Happy path) | [`TC-PTCH-001`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | `US-PTCH-01` | `AC-PTCH-02` (Boundary) | [`TC-PTCH-002`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-PHP-002` | Nhận diện nhóm gói theo nguồn cài | `US-PTCH-01` (FR) / `US-FEED-08` (TC) | bổ sung (mở rộng `AC-FEED-24`) | [`TC-SCN-105`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | `US-PTCH-02` | `AC-PTCH-05` (Happy path) | [`TC-PTCH-005`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | `US-PTCH-02` | `AC-PTCH-06` (Negative) | [`TC-PTCH-006`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | `US-PTCH-02` | `AC-PTCH-07` (Boundary) | [`TC-PTCH-007`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | `US-PTCH-02` (FR) / `US-SCN-01` (TC) | bổ sung (mở rộng `AC-SCN-04`, `AC-PTCH-05`) | [`TC-SCN-106`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PTCH-MIT-002` | Tự gỡ mitigation khi đã vá | `US-PTCH-02` | `AC-PTCH-05` (Happy path) | [`TC-PTCH-005`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | `US-PTCH-03` | `AC-PTCH-08` (Happy path) | [`TC-PTCH-008`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | `US-PTCH-03` | `AC-PTCH-09` (Negative) | [`TC-PTCH-009`](test-cases-ptch-cli-rpt.md) | Security · Negative | Sẵn sàng test |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | `US-PTCH-03` | `AC-PTCH-10` (Boundary) | [`TC-PTCH-010`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-NODE-001` | Vá Node.js cùng major | `US-PTCH-03` (FR) / `US-SCN-02` (TC) | bổ sung (mở rộng `AC-SCN-02`, `AC-PLAN-24`) | [`TC-SCN-109`](test-cases.md) | Functional · Kịch bản phiên bản | Sẵn sàng test |
| `FR-PTCH-DEP-001` | Cập nhật Composer package có lỗ hổng | `US-PTCH-04` | `AC-PTCH-11` (Happy path) | [`TC-PTCH-011`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-DEP-001` | Cập nhật Composer package có lỗ hổng | `US-PTCH-04` | `AC-PTCH-12` (Negative) | [`TC-PTCH-012`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PTCH-DEP-002` | Cập nhật npm package có lỗ hổng | `US-PTCH-04` | `AC-PTCH-13` (Security) | [`TC-PTCH-013`](test-cases-ptch-cli-rpt.md) | Security · Security | Sẵn sàng test |
| `FR-PTCH-WP-001` | Cập nhật WordPress | `US-PTCH-05` | `AC-PTCH-14` (Happy path) | [`TC-PTCH-014`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-WP-001` | Cập nhật WordPress | `US-PTCH-05` | `AC-PTCH-15` (Negative) | [`TC-PTCH-015`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PTCH-WP-002` | Kiểm tra toàn vẹn WordPress | `US-PTCH-05` | `AC-PTCH-14` (Happy path) | [`TC-PTCH-014`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-WP-002` | Kiểm tra toàn vẹn WordPress | `US-PTCH-05` | `AC-PTCH-16` (Security) | [`TC-PTCH-016`](test-cases-ptch-cli-rpt.md) | Security · Security | Sẵn sàng test |
| `FR-PTCH-DKR-001` | Nâng tag image cùng nhánh | `US-PTCH-06` | `AC-PTCH-17` (Happy path) | [`TC-PTCH-017`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-DKR-001` | Nâng tag image cùng nhánh | `US-PTCH-06` | `AC-PTCH-19` (Boundary) | [`TC-PTCH-019`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-DKR-002` | Ghi mitigation vào container đang chạy | `US-PTCH-06` | `AC-PTCH-18` (Negative) | [`TC-PTCH-018`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | `US-PTCH-07` | `AC-PTCH-20` (Happy path) | [`TC-PTCH-020`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | `US-PTCH-07` | `AC-PTCH-21` (Negative) | [`TC-PTCH-021`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-PTCH-RST-001` | Restart dịch vụ sau vá | `US-PTCH-07` | `AC-PTCH-22` (Boundary) | [`TC-PTCH-022`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | `US-PTCH-08` | `AC-PTCH-23` (Happy path) | [`TC-PTCH-023`](test-cases-ptch-cli-rpt.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | `US-PTCH-08` | `AC-PTCH-24` (Negative) | [`TC-PTCH-024`](test-cases-ptch-cli-rpt.md) | Rollback · Negative | Sẵn sàng test |
| `FR-PTCH-RBK-001` | Ghi backup manifest theo lượt | `US-PTCH-08` | `AC-PTCH-25` (Boundary) | [`TC-PTCH-025`](test-cases-ptch-cli-rpt.md) | Rollback · Boundary | Sẵn sàng test |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | `US-PTCH-09` | `AC-PTCH-26` (Happy path) | [`TC-PTCH-026`](test-cases-ptch-cli-rpt.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | `US-PTCH-09` | `AC-PTCH-27` (Negative) | [`TC-PTCH-027`](test-cases-ptch-cli-rpt.md) | Rollback · Negative | Sẵn sàng test |
| `FR-PTCH-RBK-002` | Rollback lượt chạy | `US-PTCH-09` | `AC-PTCH-28` (Boundary) | [`TC-PTCH-028`](test-cases-ptch-cli-rpt.md) | Rollback · Boundary | Sẵn sàng test |

### 3.8 Module `UPG` — Nâng cấp khác nhánh / chuyển site
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | `US-UPG-01` | `AC-UPG-01` (Happy path) | [`TC-UPG-001`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | `US-UPG-01` | `AC-UPG-02` (Negative) | [`TC-UPG-002`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | `US-UPG-01` | `AC-UPG-03` (Boundary) | [`TC-UPG-003`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | `US-UPG-01` (FR) / `US-UPG-02` (TC) | bổ sung (mở rộng `AC-UPG-06`) | [`TC-UPG-102`](test-cases-upg.md) | Compat · Bổ sung BR/ERR | Sẵn sàng test |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | `US-UPG-02` | `AC-UPG-04` (Happy path) | [`TC-UPG-004`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | `US-UPG-02` | `AC-UPG-05` (Negative) | [`TC-UPG-005`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | `US-UPG-02` | `AC-UPG-06` (Boundary) | [`TC-UPG-006`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | `US-UPG-02` | bổ sung (mở rộng `AC-UPG-06`) | [`TC-UPG-102`](test-cases-upg.md) | Compat · Bổ sung BR/ERR | Sẵn sàng test |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | `US-UPG-03` | `AC-UPG-07` (Happy path) | [`TC-UPG-007`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | `US-UPG-03` | `AC-UPG-08` (Negative) | [`TC-UPG-008`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | `US-UPG-03` | `AC-UPG-09` (Boundary) | [`TC-UPG-009`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-CFG-002` | Sao chép ini tuỳ chỉnh và extension sang runtime đích | `US-UPG-03` | `AC-UPG-07` (Happy path) | [`TC-UPG-007`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-CFG-002` | Sao chép ini tuỳ chỉnh và extension sang runtime đích | `US-UPG-03` | `AC-UPG-09` (Boundary) | [`TC-UPG-009`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | `US-UPG-04` | `AC-UPG-10` (Happy path) | [`TC-UPG-010`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | `US-UPG-04` | `AC-UPG-11` (Negative) | [`TC-UPG-011`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | `US-UPG-04` | `AC-UPG-12` (Negative) | [`TC-UPG-012`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-SWT-001` | Chuyển 1 site (bước C1–C12) | `US-UPG-04` | `AC-UPG-13` (Boundary) | [`TC-UPG-013`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | `US-UPG-05` | `AC-UPG-14` (Happy path) | [`TC-UPG-014`](test-cases-upg.md) | Integration · Happy path | Sẵn sàng test |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | `US-UPG-05` | `AC-UPG-15` (Negative) | [`TC-UPG-015`](test-cases-upg.md) | Integration · Negative | Sẵn sàng test |
| `FR-UPG-SWT-002` | Chuyển 1 site qua API panel | `US-UPG-05` | `AC-UPG-16` (Boundary) | [`TC-UPG-016`](test-cases-upg.md) | Integration · Boundary | Sẵn sàng test |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | `US-UPG-06` | `AC-UPG-17` (Happy path) | [`TC-UPG-017`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | `US-UPG-06` | `AC-UPG-18` (Negative) | [`TC-UPG-018`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-SWT-003` | Chuyển Apache `mod_php` sang PHP-FPM cùng phiên bản | `US-UPG-06` | `AC-UPG-19` (Boundary) | [`TC-UPG-019`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | `US-UPG-07` | `AC-UPG-20` (Happy path) | [`TC-UPG-020`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | `US-UPG-07` | `AC-UPG-21` (Negative) | [`TC-UPG-021`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | `US-UPG-07` | `AC-UPG-22` (Negative) | [`TC-UPG-022`](test-cases-upg.md) | Rollback · Negative | Sẵn sàng test |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | `US-UPG-07` | `AC-UPG-23` (Boundary) | [`TC-UPG-023`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-SEQ-001` | Điều phối chuyển site theo kế hoạch | `US-UPG-07` | bổ sung (mở rộng `AC-UPG-20`) | [`TC-UPG-108`](test-cases-upg.md) | Functional · Bổ sung ERR | Sẵn sàng test |
| `FR-UPG-ACK-001` | Xác nhận đã xử lý lượt chuyển thất bại (đề xuất, `CR-FR-01`) | `US-UPG-07` (theo dòng Tham chiếu của story ở [acceptance-criteria-upg.md](../userstories/acceptance-criteria-upg.md); backlog chưa liên kết) | `AC-UPG-22` (Negative) — bước `migrate ack` | Chưa có test case (`TC-UPG-022` bản 1.0.1 chưa có bước `migrate ack`) | — | Chờ bổ sung test case |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | `US-UPG-08` | `AC-UPG-24` (Happy path) | [`TC-UPG-024`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | `US-UPG-08` | `AC-UPG-26` (Boundary) | [`TC-UPG-026`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-HC-001` | Lập tập URL thăm dò | `US-UPG-08` | bổ sung (mở rộng `AC-UPG-24`) | [`TC-UPG-106`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-HC-003` | Thu baseline | `US-UPG-08` | `AC-UPG-24` (Happy path) | [`TC-UPG-024`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-HC-003` | Thu baseline | `US-UPG-08` | `AC-UPG-25` (Negative) | [`TC-UPG-025`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | `US-UPG-09` | `AC-UPG-27` (Happy path) | [`TC-UPG-027`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | `US-UPG-09` | `AC-UPG-28` (Negative) | [`TC-UPG-028`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-HC-002` | FastCGI probe trước chuyển | `US-UPG-09` | `AC-UPG-29` (Boundary) | [`TC-UPG-029`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` | `AC-UPG-30` (Happy path) | [`TC-UPG-030`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` | `AC-UPG-31` (Negative) | [`TC-UPG-031`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` | `AC-UPG-32` (Boundary) | [`TC-UPG-032`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` | bổ sung (mở rộng `AC-UPG-32`) | [`TC-UPG-101`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` | bổ sung (mở rộng `AC-UPG-32`) | [`TC-UPG-105`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-HC-004` | Chạy cửa sổ theo dõi và kết luận | `US-UPG-10` (FR) / `US-UPG-08` (TC) | bổ sung (mở rộng `AC-UPG-24`) | [`TC-UPG-106`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-HC-006` | Báo cáo health check | `US-UPG-10` | `AC-UPG-30` (Happy path) | [`TC-UPG-030`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-HC-006` | Báo cáo health check | `US-UPG-10` | bổ sung (mở rộng `AC-UPG-32`) | [`TC-UPG-101`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-HC-005` | Ra quyết định sau health check | `US-UPG-11` | `AC-UPG-33` (Happy path) | [`TC-UPG-033`](test-cases-upg.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-UPG-HC-005` | Ra quyết định sau health check | `US-UPG-11` | `AC-UPG-34` (Negative) | [`TC-UPG-034`](test-cases-upg.md) | Rollback · Negative | Sẵn sàng test |
| `FR-UPG-HC-005` | Ra quyết định sau health check | `US-UPG-11` | `AC-UPG-35` (Boundary) | [`TC-UPG-035`](test-cases-upg.md) | Rollback · Boundary | Sẵn sàng test |
| `FR-UPG-HC-005` | Ra quyết định sau health check | `US-UPG-11` | bổ sung (mở rộng `AC-UPG-33`) | [`TC-UPG-103`](test-cases-upg.md) | Rollback · Tự rollback | Sẵn sàng test |
| `FR-UPG-HC-005` | Ra quyết định sau health check | `US-UPG-11` (FR) / `US-UPG-10` (TC) | bổ sung (mở rộng `AC-UPG-32`) | [`TC-UPG-105`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | `US-UPG-11` | `AC-UPG-33` (Happy path) | [`TC-UPG-033`](test-cases-upg.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | `US-UPG-11` | `AC-UPG-35` (Boundary) | [`TC-UPG-035`](test-cases-upg.md) | Rollback · Boundary | Sẵn sàng test |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | `US-UPG-11` | bổ sung (mở rộng `AC-UPG-33`) | [`TC-UPG-103`](test-cases-upg.md) | Rollback · Tự rollback | Sẵn sàng test |
| `FR-UPG-RBK-002` | Tự rollback khi health check thất bại | `US-UPG-11` (FR) / `US-UPG-13` (TC) | bổ sung (mở rộng `AC-UPG-39`) | [`TC-UPG-104`](test-cases-upg.md) | Rollback · Tự rollback | Sẵn sàng test |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | `US-UPG-12` | `AC-UPG-36` (Happy path) | [`TC-UPG-036`](test-cases-upg.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | `US-UPG-12` | `AC-UPG-37` (Negative) | [`TC-UPG-037`](test-cases-upg.md) | Rollback · Negative | Sẵn sàng test |
| `FR-UPG-RBK-001` | Rollback 1 site bằng 1 lệnh (R1–R7) | `US-UPG-12` | `AC-UPG-38` (Boundary) | [`TC-UPG-038`](test-cases-upg.md) | Rollback · Boundary | Sẵn sàng test |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | `US-UPG-13` | `AC-UPG-39` (Happy path) | [`TC-UPG-039`](test-cases-upg.md) | Functional · Happy path | Sẵn sàng test |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | `US-UPG-13` | `AC-UPG-40` (Negative) | [`TC-UPG-040`](test-cases-upg.md) | Functional · Negative | Sẵn sàng test |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | `US-UPG-13` | `AC-UPG-41` (Boundary) | [`TC-UPG-041`](test-cases-upg.md) | Functional · Boundary | Sẵn sàng test |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | `US-UPG-13` | bổ sung (mở rộng `AC-UPG-39`) | [`TC-UPG-104`](test-cases-upg.md) | Rollback · Tự rollback | Sẵn sàng test |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | `US-UPG-13` | bổ sung (mở rộng `AC-UPG-41`) | [`TC-UPG-107`](test-cases-upg.md) | Functional · Bổ sung BR | Sẵn sàng test |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | `US-UPG-14` | `AC-UPG-42` (Happy path) | [`TC-UPG-042`](test-cases-upg.md) | Integration · Happy path | Sẵn sàng test |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | `US-UPG-14` | `AC-UPG-43` (Negative) | [`TC-UPG-043`](test-cases-upg.md) | Integration · Negative | Sẵn sàng test |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | `US-UPG-14` | `AC-UPG-44` (Security) | [`TC-UPG-044`](test-cases-upg.md) | Security · Security | Sẵn sàng test |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | `US-UPG-15` | `AC-UPG-45` (Happy path) | [`TC-UPG-045`](test-cases-upg.md) | Functional · Happy path | Chờ tách story (epic P2) |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | `US-UPG-15` | `AC-UPG-46` (Negative) | [`TC-UPG-046`](test-cases-upg.md) | Functional · Negative | Chờ tách story (epic P2) |
| `FR-UPG-RMV-001` | Gỡ runtime cũ khi không còn site dùng | `US-UPG-15` | `AC-UPG-47` (Boundary) | [`TC-UPG-047`](test-cases-upg.md) | Functional · Boundary | Chờ tách story (epic P2) |

### 3.9 Module `CON` — Web console Phase 1
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | `US-CON-01` | `AC-CON-01` (Happy path) | [`TC-CON-001`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | `US-CON-01` | `AC-CON-02` (Negative) | [`TC-CON-002`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | `US-CON-01` | `AC-CON-03` (Negative) | [`TC-CON-003`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | `US-CON-01` | `AC-CON-04` (Security) | [`TC-CON-004`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | `US-CON-01` | `AC-CON-01` (Happy path) | [`TC-CON-001`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | `US-CON-01` | `AC-CON-03` (Negative) | [`TC-CON-003`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | `US-CON-01` | `AC-CON-04` (Security) | [`TC-CON-004`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | `US-CON-02` | `AC-CON-05` (Happy path) | [`TC-CON-005`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | `US-CON-02` | `AC-CON-06` (Negative) | [`TC-CON-006`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | `US-CON-02` | `AC-CON-07` (Security) | [`TC-CON-007`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | `US-CON-02` | bổ sung (mở rộng `AC-CON-06`) | [`TC-CON-102`](test-cases-con.md) | Security · Bảo mật console | Sẵn sàng test |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | `US-CON-03` | `AC-CON-08` (Happy path) | [`TC-CON-008`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | `US-CON-03` | `AC-CON-09` (Negative) | [`TC-CON-009`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | `US-CON-03` | `AC-CON-10` (Boundary) | [`TC-CON-010`](test-cases-con.md) | Security · Boundary | Sẵn sàng test |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | `US-CON-04` | `AC-CON-11` (Happy path) | [`TC-CON-011`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | `US-CON-04` | `AC-CON-12` (Negative) | [`TC-CON-012`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | `US-CON-04` | `AC-CON-13` (Security) | [`TC-CON-013`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | `US-CON-05` | `AC-CON-14` (Happy path) | [`TC-CON-014`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | `US-CON-05` | `AC-CON-15` (Negative) | [`TC-CON-015`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | `US-CON-05` | `AC-CON-16` (Security) | [`TC-CON-016`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | `US-CON-05` (FR) / `US-CON-02` (TC) | bổ sung (mở rộng `AC-CON-06`) | [`TC-CON-102`](test-cases-con.md) | Security · Bảo mật console | Sẵn sàng test |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | `US-CON-06` | `AC-CON-17` (Happy path) | [`TC-CON-017`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | `US-CON-06` | `AC-CON-18` (Negative) | [`TC-CON-018`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | `US-CON-06` | `AC-CON-19` (Boundary) | [`TC-CON-019`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | `US-CON-07` | `AC-CON-20` (Happy path) | [`TC-CON-020`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | `US-CON-07` | `AC-CON-21` (Negative) | [`TC-CON-021`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | `US-CON-07` | `AC-CON-22` (Security) | [`TC-CON-022`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | `US-CON-08` | `AC-CON-23` (Happy path) | [`TC-CON-023`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | `US-CON-08` | `AC-CON-24` (Negative) | [`TC-CON-024`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | `US-CON-08` | `AC-CON-25` (Boundary) | [`TC-CON-025`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | `US-CON-09` | `AC-CON-26` (Happy path) | [`TC-CON-026`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | `US-CON-09` | `AC-CON-27` (Negative) | [`TC-CON-027`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | `US-CON-09` | `AC-CON-28` (Boundary) | [`TC-CON-028`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | `US-CON-10` | `AC-CON-29` (Happy path) | [`TC-CON-029`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | `US-CON-10` | `AC-CON-30` (Negative) | [`TC-CON-030`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | `US-CON-10` | `AC-CON-31` (Boundary) | [`TC-CON-031`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | `US-CON-10` | bổ sung (mở rộng `AC-CON-31`) | [`TC-CON-103`](test-cases-con.md) | Functional · Bổ sung ERR | Sẵn sàng test |
| `FR-CON-JOB-002` | Huỷ job từ console | `US-CON-10` | `AC-CON-29` (Happy path) | [`TC-CON-029`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-JOB-002` | Huỷ job từ console | `US-CON-10` | `AC-CON-30` (Negative) | [`TC-CON-030`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | `US-CON-11` | `AC-CON-32` (Happy path) | [`TC-CON-032`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | `US-CON-11` | `AC-CON-33` (Negative) | [`TC-CON-033`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | `US-CON-11` | `AC-CON-34` (Security) | [`TC-CON-034`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | `US-CON-12` | `AC-CON-35` (Happy path) | [`TC-CON-035`](test-cases-con.md) | Rollback · Happy path | Sẵn sàng test |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | `US-CON-12` | `AC-CON-36` (Negative) | [`TC-CON-036`](test-cases-con.md) | Rollback · Negative | Sẵn sàng test |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | `US-CON-12` | `AC-CON-37` (Boundary) | [`TC-CON-037`](test-cases-con.md) | Rollback · Boundary | Sẵn sàng test |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | `US-CON-13` | `AC-CON-38` (Happy path) | [`TC-CON-038`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | `US-CON-13` | `AC-CON-40` (Negative) | [`TC-CON-040`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-FEED-002` | Nhập snapshot qua console | `US-CON-13` | `AC-CON-39` (Happy path) | [`TC-CON-039`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-FEED-002` | Nhập snapshot qua console | `US-CON-13` | `AC-CON-40` (Negative) | [`TC-CON-040`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-FEED-002` | Nhập snapshot qua console | `US-CON-13` | `AC-CON-41` (Boundary) | [`TC-CON-041`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | `US-CON-14` | `AC-CON-42` (Happy path) | [`TC-CON-042`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | `US-CON-14` | `AC-CON-43` (Negative) | [`TC-CON-043`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | `US-CON-14` | `AC-CON-44` (Boundary) | [`TC-CON-044`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | `US-CON-15` | `AC-CON-45` (Happy path) | [`TC-CON-045`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | `US-CON-15` | `AC-CON-46` (Negative) | [`TC-CON-046`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | `US-CON-15` | `AC-CON-47` (Security) | [`TC-CON-047`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | `US-CON-16` | `AC-CON-48` (Happy path) | [`TC-CON-048`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | `US-CON-16` | `AC-CON-49` (Negative) | [`TC-CON-049`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | `US-CON-16` | `AC-CON-50` (Negative) | [`TC-CON-050`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | `US-CON-16` | `AC-CON-51` (Security) | [`TC-CON-051`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | `US-CON-17` | `AC-CON-52` (Happy path) | [`TC-CON-052`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | `US-CON-17` | `AC-CON-53` (Negative) | [`TC-CON-053`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | `US-CON-17` | `AC-CON-54` (Security) | [`TC-CON-054`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | `US-CON-18` | `AC-CON-55` (Happy path) | [`TC-CON-055`](test-cases-con.md) | Security · Happy path | Sẵn sàng test |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | `US-CON-18` | `AC-CON-56` (Negative) | [`TC-CON-056`](test-cases-con.md) | Security · Negative | Sẵn sàng test |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | `US-CON-18` | `AC-CON-57` (Security) | [`TC-CON-057`](test-cases-con.md) | Security · Security | Sẵn sàng test |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | `US-CON-19` (FR) / `US-CLI-03` (TC) | bổ sung (mở rộng `AC-CLI-08`) | [`TC-CLI-101`](test-cases-ptch-cli-rpt.md) | Compat · Bổ sung BR | Sẵn sàng test |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | `US-CON-19` | `AC-CON-58` (Happy path) | [`TC-CON-058`](test-cases-con.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | `US-CON-19` | `AC-CON-59` (Negative) | [`TC-CON-059`](test-cases-con.md) | Functional · Negative | Sẵn sàng test |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | `US-CON-19` | `AC-CON-60` (Boundary) | [`TC-CON-060`](test-cases-con.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | `US-CON-19` | bổ sung (mở rộng `AC-CON-60`) | [`TC-CON-101`](test-cases-con.md) | Security · Bảo mật console | Sẵn sàng test |

### 3.10 Module `JOB` — Job runner, log, audit
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-JOB-RUN-001` | Xếp hàng và chạy job | `US-JOB-01` | `AC-JOB-01` (Happy path) | [`TC-JOB-001`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-RUN-001` | Xếp hàng và chạy job | `US-JOB-01` | `AC-JOB-02` (Negative) | [`TC-JOB-002`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-RUN-001` | Xếp hàng và chạy job | `US-JOB-01` | `AC-JOB-03` (Boundary) | [`TC-JOB-003`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | `US-JOB-02` | `AC-JOB-04` (Happy path) | [`TC-JOB-004`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | `US-JOB-02` | `AC-JOB-05` (Negative) | [`TC-JOB-005`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | `US-JOB-02` | `AC-JOB-06` (Boundary) | [`TC-JOB-006`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-RUN-003` | Huỷ job | `US-JOB-03` | `AC-JOB-07` (Happy path) | [`TC-JOB-007`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-RUN-003` | Huỷ job | `US-JOB-03` | `AC-JOB-08` (Negative) | [`TC-JOB-008`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-RUN-003` | Huỷ job | `US-JOB-03` | `AC-JOB-09` (Boundary) | [`TC-JOB-009`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | `US-JOB-04` | `AC-JOB-10` (Happy path) | [`TC-JOB-010`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | `US-JOB-04` | `AC-JOB-11` (Negative) | [`TC-JOB-011`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | `US-JOB-04` | `AC-JOB-12` (Boundary) | [`TC-JOB-012`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-LOG-001` | Lưu log và kết quả job | `US-JOB-05` | `AC-JOB-13` (Happy path) | [`TC-JOB-013`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-LOG-001` | Lưu log và kết quả job | `US-JOB-05` | `AC-JOB-15` (Boundary) | [`TC-JOB-015`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-LOG-003` | Lưu giữ log job | `US-JOB-05` | `AC-JOB-14` (Negative) | [`TC-JOB-014`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-LOG-003` | Lưu giữ log job | `US-JOB-05` | `AC-JOB-15` (Boundary) | [`TC-JOB-015`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-LOG-002` | Stream log qua SSE | `US-JOB-06` | `AC-JOB-16` (Happy path) | [`TC-JOB-016`](test-cases-job-flt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-JOB-LOG-002` | Stream log qua SSE | `US-JOB-06` | `AC-JOB-17` (Negative) | [`TC-JOB-017`](test-cases-job-flt.md) | Functional · Negative | Sẵn sàng test |
| `FR-JOB-LOG-002` | Stream log qua SSE | `US-JOB-06` | `AC-JOB-18` (Boundary) | [`TC-JOB-018`](test-cases-job-flt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-JOB-LOG-002` | Stream log qua SSE | `US-JOB-06` | `AC-JOB-25` (Boundary) | Chưa có test case (`TC-JOB-025` chưa sinh ở [test-cases-job-flt.md](test-cases-job-flt.md)) | — | Chờ bổ sung test case |
| `FR-JOB-LOG-002` | Stream log qua SSE | `US-JOB-06` (FR) / `US-CON-10` (TC) | bổ sung (mở rộng `AC-CON-31`) | [`TC-CON-103`](test-cases-con.md) | Functional · Bổ sung ERR | Sẵn sàng test |
| `FR-JOB-AUD-001` | Ghi audit append-only | `US-JOB-07` | `AC-JOB-19` (Happy path) | [`TC-JOB-019`](test-cases-job-flt.md) | Security · Happy path | Sẵn sàng test |
| `FR-JOB-AUD-001` | Ghi audit append-only | `US-JOB-07` | `AC-JOB-20` (Negative) | [`TC-JOB-020`](test-cases-job-flt.md) | Security · Negative | Sẵn sàng test |
| `FR-JOB-AUD-001` | Ghi audit append-only | `US-JOB-07` | `AC-JOB-21` (Boundary) | [`TC-JOB-021`](test-cases-job-flt.md) | Security · Boundary | Sẵn sàng test |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | `US-JOB-08` | `AC-JOB-22` (Happy path) | [`TC-JOB-022`](test-cases-job-flt.md) | Security · Happy path | Sẵn sàng test |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | `US-JOB-08` | `AC-JOB-23` (Negative) | [`TC-JOB-023`](test-cases-job-flt.md) | Security · Negative | Sẵn sàng test |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | `US-JOB-08` | `AC-JOB-24` (Security) | [`TC-JOB-024`](test-cases-job-flt.md) | Security · Security | Sẵn sàng test |
| `FR-JOB-AUD-003` | Truy vấn audit | `US-JOB-08` | `AC-JOB-22` (Happy path) | [`TC-JOB-022`](test-cases-job-flt.md) | Security · Happy path | Sẵn sàng test |
| `FR-JOB-AUD-003` | Truy vấn audit | `US-JOB-08` | `AC-JOB-24` (Security) | [`TC-JOB-024`](test-cases-job-flt.md) | Security · Security | Sẵn sàng test |

### 3.11 Module `CLI` — Giao diện dòng lệnh
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | `US-CLI-01` | `AC-CLI-01` (Happy path) | [`TC-CLI-001`](test-cases-ptch-cli-rpt.md) | Compat · Happy path | Sẵn sàng test |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | `US-CLI-01` | `AC-CLI-02` (Negative) | [`TC-CLI-002`](test-cases-ptch-cli-rpt.md) | Compat · Negative | Sẵn sàng test |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | `US-CLI-01` | `AC-CLI-03` (Security) | [`TC-CLI-003`](test-cases-ptch-cli-rpt.md) | Security · Security | Sẵn sàng test |
| `FR-CLI-JSON-002` | Công bố JSON Schema | `US-CLI-02` | `AC-CLI-04` (Happy path) | [`TC-CLI-004`](test-cases-ptch-cli-rpt.md) | Compat · Happy path | Sẵn sàng test |
| `FR-CLI-JSON-002` | Công bố JSON Schema | `US-CLI-02` | `AC-CLI-05` (Negative) | [`TC-CLI-005`](test-cases-ptch-cli-rpt.md) | Compat · Negative | Sẵn sàng test |
| `FR-CLI-JSON-002` | Công bố JSON Schema | `US-CLI-02` | `AC-CLI-06` (Boundary) | [`TC-CLI-006`](test-cases-ptch-cli-rpt.md) | Compat · Boundary | Sẵn sàng test |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | `US-CLI-03` | `AC-CLI-07` (Happy path) | [`TC-CLI-007`](test-cases-ptch-cli-rpt.md) | Compat · Happy path | Sẵn sàng test |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | `US-CLI-03` | `AC-CLI-08` (Negative) | [`TC-CLI-008`](test-cases-ptch-cli-rpt.md) | Compat · Negative | Sẵn sàng test |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | `US-CLI-03` | `AC-CLI-09` (Boundary) | [`TC-CLI-009`](test-cases-ptch-cli-rpt.md) | Compat · Boundary | Sẵn sàng test |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | `US-CLI-03` | bổ sung (mở rộng `AC-CLI-08`) | [`TC-CLI-101`](test-cases-ptch-cli-rpt.md) | Compat · Bổ sung BR | Sẵn sàng test |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | `US-CLI-04` | `AC-CLI-10` (Happy path) | [`TC-CLI-010`](test-cases-ptch-cli-rpt.md) | Compat · Happy path | Sẵn sàng test |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | `US-CLI-04` | `AC-CLI-11` (Negative) | [`TC-CLI-011`](test-cases-ptch-cli-rpt.md) | Compat · Negative | Sẵn sàng test |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | `US-CLI-04` | `AC-CLI-12` (Boundary) | [`TC-CLI-012`](test-cases-ptch-cli-rpt.md) | Compat · Boundary | Sẵn sàng test |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | `US-CLI-05` | `AC-CLI-13` (Happy path) | [`TC-CLI-013`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | `US-CLI-05` | `AC-CLI-14` (Negative) | [`TC-CLI-014`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | `US-CLI-05` | `AC-CLI-15` (Boundary) | [`TC-CLI-015`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | `US-CLI-06` | `AC-CLI-16` (Happy path) | [`TC-CLI-016`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | `US-CLI-06` | `AC-CLI-17` (Negative) | [`TC-CLI-017`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | `US-CLI-06` | `AC-CLI-18` (Boundary) | [`TC-CLI-018`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | `US-CLI-07` | `AC-CLI-19` (Happy path) | [`TC-CLI-019`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | `US-CLI-07` | `AC-CLI-20` (Negative) | [`TC-CLI-020`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | `US-CLI-07` | `AC-CLI-21` (Boundary) | [`TC-CLI-021`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | `US-CLI-08` | `AC-CLI-22` (Happy path) | [`TC-CLI-022`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | `US-CLI-08` | `AC-CLI-23` (Negative) | [`TC-CLI-023`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | `US-CLI-08` | `AC-CLI-24` (Boundary) | [`TC-CLI-024`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | `US-CLI-09` | `AC-CLI-25` (Happy path) | [`TC-CLI-025`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | `US-CLI-09` | `AC-CLI-26` (Negative) | [`TC-CLI-026`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-CLI-SAFE-001` | Áp `--dry-run` và xác nhận cho lệnh thay đổi | `US-CLI-09` | `AC-CLI-27` (Boundary) | [`TC-CLI-027`](test-cases-ptch-cli-rpt.md) | Compat · Boundary | Sẵn sàng test |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | `US-CLI-10` | `AC-CLI-28` (Happy path) | [`TC-CLI-028`](test-cases-ptch-cli-rpt.md) | Compat · Happy path | Sẵn sàng test |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | `US-CLI-10` | `AC-CLI-29` (Negative) | [`TC-CLI-029`](test-cases-ptch-cli-rpt.md) | Compat · Negative | Sẵn sàng test |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | `US-CLI-10` | `AC-CLI-30` (Boundary) | [`TC-CLI-030`](test-cases-ptch-cli-rpt.md) | Compat · Boundary | Sẵn sàng test |

### 3.12 Module `RPT` — Báo cáo
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | `US-RPT-01` | `AC-RPT-01` (Happy path) | [`TC-RPT-001`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | `US-RPT-01` | `AC-RPT-02` (Negative) | [`TC-RPT-002`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | `US-RPT-01` | `AC-RPT-03` (Security) | [`TC-RPT-003`](test-cases-ptch-cli-rpt.md) | Security · Security | Sẵn sàng test |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | `US-RPT-02` | `AC-RPT-04` (Happy path) | [`TC-RPT-004`](test-cases-ptch-cli-rpt.md) | Functional · Happy path | Sẵn sàng test |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | `US-RPT-02` | `AC-RPT-05` (Negative) | [`TC-RPT-005`](test-cases-ptch-cli-rpt.md) | Functional · Negative | Sẵn sàng test |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | `US-RPT-02` | `AC-RPT-06` (Boundary) | [`TC-RPT-006`](test-cases-ptch-cli-rpt.md) | Functional · Boundary | Sẵn sàng test |

### 3.13 Module `FLT` — Quản lý nhiều server (Phase 2)
| FR ID | Tên yêu cầu chức năng | User Story ID | Acceptance Criteria | Test Case ID | Loại kiểm thử | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-FLT-INV-001` | Quản lý danh mục server | `US-FLT-01` | `AC-FLT-01` (Happy path) | [`TC-FLT-001`](test-cases-job-flt.md) | Integration · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-INV-001` | Quản lý danh mục server | `US-FLT-01` | `AC-FLT-03` (Security) | [`TC-FLT-003`](test-cases-job-flt.md) | Security · Security | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-INV-002` | Kiểm tra kết nối và ghim khoá máy chủ | `US-FLT-01` | `AC-FLT-01` (Happy path) | [`TC-FLT-001`](test-cases-job-flt.md) | Integration · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-INV-002` | Kiểm tra kết nối và ghim khoá máy chủ | `US-FLT-01` | `AC-FLT-02` (Negative) | [`TC-FLT-002`](test-cases-job-flt.md) | Integration · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-INV-002` | Kiểm tra kết nối và ghim khoá máy chủ | `US-FLT-01` | `AC-FLT-03` (Security) | [`TC-FLT-003`](test-cases-job-flt.md) | Security · Security | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-RBAC-001` | Quản lý tài khoản và vai trò Phase 2 | `US-FLT-02` | `AC-FLT-04` (Happy path) | [`TC-FLT-004`](test-cases-job-flt.md) | Security · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-RBAC-001` | Quản lý tài khoản và vai trò Phase 2 | `US-FLT-02` | `AC-FLT-05` (Negative) | [`TC-FLT-005`](test-cases-job-flt.md) | Security · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-RBAC-001` | Quản lý tài khoản và vai trò Phase 2 | `US-FLT-02` | `AC-FLT-06` (Boundary) | [`TC-FLT-006`](test-cases-job-flt.md) | Security · Boundary | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-EXEC-001` | Thực thi CLI từ xa | `US-FLT-03` | `AC-FLT-07` (Happy path) | [`TC-FLT-007`](test-cases-job-flt.md) | Integration · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-EXEC-001` | Thực thi CLI từ xa | `US-FLT-03` | `AC-FLT-09` (Security) | [`TC-FLT-009`](test-cases-job-flt.md) | Security · Security | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-EXEC-002` | Chạy theo đợt | `US-FLT-03` | `AC-FLT-07` (Happy path) | [`TC-FLT-007`](test-cases-job-flt.md) | Integration · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-EXEC-002` | Chạy theo đợt | `US-FLT-03` | `AC-FLT-08` (Negative) | [`TC-FLT-008`](test-cases-job-flt.md) | Integration · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-EXEC-002` | Chạy theo đợt | `US-FLT-03` | `AC-FLT-09` (Security) | [`TC-FLT-009`](test-cases-job-flt.md) | Security · Security | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-DASH-001` | Hiển thị dashboard tổng hợp nhiều server | `US-FLT-04` | `AC-FLT-10` (Happy path) | [`TC-FLT-010`](test-cases-job-flt.md) | Functional · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-DASH-001` | Hiển thị dashboard tổng hợp nhiều server | `US-FLT-04` | `AC-FLT-12` (Boundary) | [`TC-FLT-012`](test-cases-job-flt.md) | Functional · Boundary | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-DASH-002` | Đi sâu theo server | `US-FLT-04` | `AC-FLT-10` (Happy path) | [`TC-FLT-010`](test-cases-job-flt.md) | Functional · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-DASH-002` | Đi sâu theo server | `US-FLT-04` | `AC-FLT-11` (Negative) | [`TC-FLT-011`](test-cases-job-flt.md) | Functional · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-AUD-001` | Hợp nhất audit trung tâm | `US-FLT-04` | `AC-FLT-10` (Happy path) | [`TC-FLT-010`](test-cases-job-flt.md) | Functional · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-AUD-001` | Hợp nhất audit trung tâm | `US-FLT-04` | `AC-FLT-11` (Negative) | [`TC-FLT-011`](test-cases-job-flt.md) | Functional · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-FEED-001` | Cache dữ liệu trung tâm và phân phối snapshot | `US-FLT-05` | `AC-FLT-13` (Happy path) | [`TC-FLT-013`](test-cases-job-flt.md) | Integration · Happy path | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-FEED-001` | Cache dữ liệu trung tâm và phân phối snapshot | `US-FLT-05` | `AC-FLT-14` (Negative) | [`TC-FLT-014`](test-cases-job-flt.md) | Integration · Negative | Đặc tả Phase 2 — chưa thực thi |
| `FR-FLT-FEED-001` | Cache dữ liệu trung tâm và phân phối snapshot | `US-FLT-05` | `AC-FLT-15` (Security) | [`TC-FLT-015`](test-cases-job-flt.md) | Security · Security | Đặc tả Phase 2 — chưa thực thi |

## 4. Tài liệu tham chiếu (References)
- [functional-requirements.md](../srs/functional-requirements.md) (DOC-SRS-QP-FR-001) bản 1.0.1 — nguồn tên FR và ưu tiên
- [backlog.md](../userstories/backlog.md) (DOC-US-QP-001), [acceptance-criteria.md](../userstories/acceptance-criteria.md) (DOC-AC-QP-000)
- [test-cases.md](test-cases.md) (DOC-TC-QP-000), [test-cases-coverage.md](test-cases-coverage.md) (DOC-TC-QP-COV) v1.0.1 — §6 mục 6 yêu cầu thêm dòng `TC-UPG-108`, `TC-CON-103`
- [test-cases-upg.md](test-cases-upg.md) (DOC-TC-QP-UPG) v1.0.1 — `TC-UPG-108`; [test-cases-con.md](test-cases-con.md) (DOC-TC-QP-CON) v1.0.1 — `TC-CON-103`
- [acceptance-criteria-upg.md](../userstories/acceptance-criteria-upg.md) v1.0.1 — `AC-UPG-22` có bước `migrate ack` (`FR-UPG-ACK-001`); [acceptance-criteria-job-flt.md](../userstories/acceptance-criteria-job-flt.md) v1.0.1 — `AC-JOB-25`
- OpenBA-Kit `rules/14-test-case-traceability.md` — mẫu bảng RTM chuẩn
