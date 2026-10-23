---
id: DOC-UC-QP-JOB-003
title: Đặc tả Use Case UC-JOB-003 — Tra cứu và kiểm tra toàn vẹn audit
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-JOB-003, audit, append-only, hash-chain, integrity, auditor]
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-JOB-003 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Đồng bộ tên `FR-CON-AUD-001` trong bảng FR liên quan thành "Hiển thị màn hình Audit và báo cáo (SCR-010)" theo `srs/functional-requirements.md` |

## UC-JOB-003: Tra cứu và kiểm tra toàn vẹn audit

- **Tác nhân chính (Primary Actor)**: Auditor chỉ xem (`PER-04` kỹ sư bảo mật/kiểm toán viên).
- **Tác nhân hỗ trợ**: Operator (mở phiên console hoặc chạy CLI cho Auditor khi Auditor không có quyền shell); CLI và console là bên **ghi** audit (System: Job runner, mọi lệnh ghi).
- **Phạm vi (Scope)**: `STATE_DIR/audit/audit-YYYYMM.jsonl`; CLI `php-quickpatch.sh audit list|verify`; console SCR-010.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-04`: truy vết ai đã chạy gì, lúc nào (UTC, độ phân giải ms), trên đối tượng nào, kết quả ra sao; chuỗi hash phát hiện 100% thay đổi 1 byte (`NFR-REL-007`).
  - Operator: không có lệnh/API sửa hoặc xoá bản ghi audit (`BR-AUD-002`).
  - Kỹ sư bảo mật: `args` trong audit đã che token, cookie, `Authorization`, `X-QP-CSRF`, `QP_*_KEY`/`QP_*_TOKEN`, `password=`, `token=`, `secret=` (`BR-AUD-005`, `BR-SEC-006`).
- **Tiền điều kiện (Pre-conditions)**:
  - Có ≥ 1 file `audit-YYYYMM.jsonl`; người xem có quyền đọc `STATE_DIR/audit` (audit của root cần root, spec §3.3.2).
  - Console: phiên hợp lệ; `audit list`/`audit verify` cần Python ≥ 3.6.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: danh sách bản ghi lọc theo thời gian/actor/hành động/kết quả; kết quả kiểm chuỗi `{verified: true, records, first_broken_seq: null}`.
  - **Đảm bảo tối thiểu**: tra cứu và kiểm tra là thao tác chỉ đọc; file audit giữ nguyên làm bằng chứng khi phát hiện lệch.
- **Kích hoạt (Trigger)**: Auditor mở SCR-010, hoặc chạy `audit list [--from DATE] [--to DATE] [--action A] [--actor U] --json` / `audit verify [--from] [--to]`.

### Luồng sự kiện chính (Main Success Scenario)
1. (Ghi, diễn ra trước ở các use case khác) Với mỗi sự kiện thuộc `BR-AUD-001` (lệnh/job ghi, đăng nhập thành công/thất bại, phát hành token không kèm token, duyệt/huỷ kế hoạch, miễn trừ, đổi canary, nhập snapshot, `--accept-shrink`, đổi `hc_url`, mở khoá runtime `locked`), hệ thống ghi bản ghi "intent" trước thay đổi và "result" sau khi kết thúc vào `audit-YYYYMM.jsonl` mở `O_APPEND`, quyền `0600`, với `hash_n = SHA-256(hash_{n−1} ‖ JSON chuẩn hoá của bản ghi n)` (`FR-JOB-AUD-001`, `BR-AUD-002`, `BR-AUD-003`).
2. Auditor mở SCR-010; console gọi `GET /api/v1/audit-events` với bộ lọc thời gian, actor, hành động, kết quả và phân trang (`limit` mặc định 20, tối đa 200) (`FR-CON-AUD-001`, `FR-JOB-AUD-003`).
3. Hệ thống đọc các file tháng trong khoảng, trả bản ghi gồm `seq`, `ts`, `actor`, `sys_user`, `source` (`cli`/`console`), `action`, `args` (đã che), `job_id`, `run_id`, `plan_id`, `result`, `exit_code`, `prev_hash`, `hash`.
4. Auditor bấm "Kiểm tra toàn vẹn" cho khoảng thời gian; console gửi `POST /api/v1/audit-verifications` tạo job `audit verify --json [--from] [--to]` loại `read` (`FR-JOB-AUD-002`).
5. Hệ thống tính lại chuỗi hash qua các file tháng; bản ghi đầu file tháng mang `prev_hash` của bản ghi cuối tháng trước; bản ghi đầu tiên dùng 64 ký tự `0`.
6. Hệ thống trả `{verified: true, records: N, first_broken_seq: null}`; SCR-010 hiển thị kết quả.
7. Auditor dùng kết quả cho báo cáo bằng chứng (UC-RPT-002).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Không ghi được bản ghi "intent" (đĩa đầy, sai quyền)**:
  - 1a1. Thao tác thay đổi không bắt đầu; `ERR-AUD-500-01` (Critical) (`BR-AUD-004`).
- **1b. Không ghi được bản ghi "result"**:
  - 1b1. Hệ thống thử lại 3 lần cách 1 s, sau đó ghi lỗi vào `result.json` và stderr (`BR-AUD-004`).
- **2a. Auditor dùng CLI**:
  - 2a1. `audit list … --json` in envelope `qp.audit/1`; không root chỉ đọc audit của user (spec §2.3).
- **2b. Khoảng thời gian sai (`from` > `to`)**:
  - 2b1. 422 `ERR-CON-422-01` (console) hoặc lỗi tham số `ERR-CLI-400-01` (CLI).
- **2c. Thiếu Python ≥ 3.6 khi chạy `audit` trên CLI**:
  - 2c1. `ERR-CLI-424-01`, thoát 2; Auditor đọc trực tiếp file JSONL bằng công cụ của mình.
- **5a. Chuỗi hash không khớp** (bản ghi bị sửa, xoá, chèn ngoài tool):
  - 5a1. Hệ thống trả `{verified: false, first_broken_seq: n}` và `ERR-AUD-409-01` (Critical) "Nhật ký kiểm toán bị thay đổi từ bản ghi #{seq}."
  - 5a2. Auditor điều tra sự cố, giữ nguyên file làm bằng chứng; tool không sửa file.
- **5b. Root xoá file tháng thủ công ngoài tool**:
  - 5b1. Bản ghi đầu tháng kế tiếp có `prev_hash` không khớp → `ERR-AUD-409-01` (ngoại lệ `BR-AUD-002` được phát hiện bằng `BR-AUD-003`).
- **6a. Job vượt 600 s**:
  - 6a1. Job `FAILED` với `ERR-JOB-504-01`; Auditor thu hẹp khoảng thời gian.
- **7a. Auditor yêu cầu sửa/xoá bản ghi**:
  - 7a1. Không có nút, lệnh hay API sửa/xoá audit (`BR-AUD-002`); 405 `ERR-CON-405-01` cho phương thức không hỗ trợ.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-002`: 100% job ghi có audit intent trước thay đổi và audit result khi kết thúc.
- `NFR-REL-007`: chuỗi hash phát hiện 100% thay đổi 1 byte.
- `NFR-CAP-001`: `audit/` tăng ≤ 10 MiB/tháng với 1.000 sự kiện/ngày; giữ ≥ 365 ngày (`BR-AUD-002`).
- `NFR-SEC-010`: thư mục `audit` quyền `0700`, file `0600`.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-AUD-001` | Sự kiện phải ghi | 1 |
| `BR-AUD-002` | Chỉ nối thêm, giữ ≥ 365 ngày | 1, 7a |
| `BR-AUD-003` | Chuỗi hash | 1, 5 |
| `BR-AUD-004` | Đóng khi lỗi | 1a, 1b |
| `BR-AUD-005`, `BR-SEC-006` | Che dữ liệu | 3 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-JOB-AUD-001` | Ghi audit append-only | 1 |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | 2, 6 |
| `FR-JOB-AUD-003` | Truy vấn audit | 2, 3 |
| `FR-JOB-AUD-002` | Kiểm tra toàn vẹn audit | 4–6 |

### Giao diện và API liên quan
- Màn hình: `SCR-010` Audit & báo cáo.
- API: `GET /api/v1/audit-events`, `POST /api/v1/audit-verifications`.

### Quan hệ với use case khác
- Mọi use case ghi (UC-PTCH-*, UC-UPG-*, UC-PLAN-002/003, UC-FEED-002/004, UC-CON-001) tạo bản ghi audit ở bước 1.
- Kết quả là đầu vào của UC-RPT-002.

### Ghi chú và tài liệu tham chiếu
- Trách nhiệm ghi: audit intent/result của thao tác thay đổi hệ thống do CLI ghi (một đường thực thi cho CLI và console, `C-SRS-05`); console chỉ ghi sự kiện riêng (phát hành token, đăng nhập, huỷ job, đổi canary) — giả định ghi ở DOC-SRS-QP-FLOW-001 §6.2 mục 10.
- Phase 2: audit trung tâm hợp nhất ở UC-FLT-003.
