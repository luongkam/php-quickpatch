---
id: DOC-UC-QP-FLT-004
title: Đặc tả Use Case UC-FLT-004 — Phân phối snapshot từ máy trung tâm (Phase 2)
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FLT-004, phase-2, fleet, snapshot, distribution, offline, feeds-import]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-003
  - DOC-API-QP-006
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-FLT-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FLT-004 theo `skills/usecase`, template 26, rules 06, 17 (Phase 2 — chỉ đặc tả) |

## UC-FLT-004: Phân phối snapshot từ máy trung tâm (Phase 2)

- **Tác nhân chính (Primary Actor)**: Operator Phase 2 (vai trò Operator hoặc Admin).
- **Tác nhân hỗ trợ**: `SYS-04` kết nối SSH; `SYS-02` nguồn online (máy trung tâm có Internet); CLI trên từng server (`feeds import`).
- **Phạm vi (Scope)**: `POST /api/v1/feed-distributions`; máy trung tâm chạy `feeds update` + `feeds export`; đẩy snapshot tới server không ra Internet; SCR-022.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Operator: mọi server không ra Internet có bundle tuổi ≤ 7 ngày (KR5.2) bằng 1 thao tác trên máy trung tâm.
  - Chủ từng server: snapshot chỉ chứa dữ liệu công khai, không chứa dữ liệu riêng của server khác (`BR-FEED-056`, `BR-FLT-007`); mỗi server kiểm SHA-256 trước khi nhập (`BR-FEED-055`).
- **Tiền điều kiện (Pre-conditions)**:
  - Tài khoản Operator/Admin đăng nhập; server đã ghim khoá máy chủ và kiểm kết nối `PASS` (UC-FLT-001).
  - Máy trung tâm có Python ≥ 3.6 và mạng HTTPS tới nguồn.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: mỗi server đích có `current/` mới từ snapshot, audit trên server ghi người chạy (`fleet:<username>`), SHA-256, `generated_at`; `fleet_run` `COMPLETED`.
  - **Đảm bảo tối thiểu**: server từ chối snapshot lệch hash hoặc cũ hơn bundle hiện có giữ nguyên `current/`.
- **Kích hoạt (Trigger)**: Operator chọn nhóm server và biến thể (`standard`/`full`) trên SCR-022, bấm "Phân phối snapshot".

### Luồng sự kiện chính (Main Success Scenario)
1. Operator gửi `POST /api/v1/feed-distributions` `{target, variant}`; hệ thống kiểm vai trò (`BR-FLT-008`) (`FR-FLT-FEED-001`).
2. Máy trung tâm chạy `feeds update` khi bundle quá TTL (UC-FEED-001), rồi `feeds export --out <file> --variant <v>` (UC-FEED-004), loại dữ liệu riêng (`BR-FEED-056`).
3. Hệ thống tạo đợt chạy hành động nội bộ `feeds_import_remote` và trả 202 `{fleet_run_id, snapshot: {generated_at, sha256, bytes}}`.
4. Với từng server theo đợt (UC-FLT-002): S1 kết nối, S2 thư mục tạm, S3 đẩy gói CLI + `feeds-snapshot.tar.gz` (≤ 15 MB biến thể `full`), S4 kiểm SHA-256 gói CLI.
5. S5: server chạy `feeds import <TMP>/feeds-snapshot.tar.gz --sha256 <hex> --yes --json`; CLI kiểm SHA-256 toàn gói, `SHA256SUMS`, schema, `generated_at`, thay `current/` nguyên tử, ghi audit (`BR-FLT-007`, `BR-FEED-055`).
6. S6 thu audit; S7 xoá thư mục tạm.
7. Hệ thống lưu kết quả từng server; `fleet_run` `COMPLETED`; SCR-022 hiển thị tuổi dữ liệu mới của từng server.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Vai trò Viewer**:
  - 1a1. 403 `ERR-FLT-403-02`.
- **1b. Nhóm không có server hoặc `server_id` không tồn tại**:
  - 1b1. 404 `ERR-FLT-404-01`.
- **2a. Đồng bộ trên máy trung tâm lỗi nguồn**:
  - 2a1. Xử lý theo UC-FEED-001 (`ERR-FEED-503-01`…); snapshot vẫn được xuất từ bundle hiện có kèm tuổi dữ liệu; Operator quyết định có phân phối hay không.
- **4a. Lỗi kết nối, khoá máy chủ, gói CLI lệch hash, thiếu điều kiện**:
  - 4a1. Như UC-FLT-002 extension 2a–2e (`ERR-FLT-504-01`, `ERR-FLT-403-01`, `ERR-FLT-401-01`, `ERR-FLT-422-03` (mã đề xuất), `ERR-FLT-424-01`).
- **5a. SHA-256 snapshot không khớp trên server**:
  - 5a1. Server từ chối, `ERR-FEED-422-02` (Critical), `current/` giữ nguyên.
- **5b. Snapshot cũ hơn bundle hiện có của server**:
  - 5b1. Server từ chối, `ERR-FEED-409-02`; server đó đã có dữ liệu mới hơn, không cần nhập.
- **5c. Server có `feeds update` đang giữ khoá > 30 s**:
  - 5c1. `ERR-FEED-423-01`; server `FAILED` cho lần phân phối này.
- **5d. Canary lỗi hoặc > 20% server của đợt lỗi**:
  - 5d1. `fleet_run` `STOPPED`, `ERR-FLT-409-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-SEC-012`: 0 file tạm của tool còn lại ngoài `STATE_DIR` sau chạy từ xa.
- KR5.2: snapshot phân phối có tuổi ≤ 7 ngày.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FLT-007` | Phân phối snapshot, `feeds import --sha256`, không gửi dữ liệu riêng | 2, 5 |
| `BR-FEED-055`, `BR-FEED-056`, `BR-FEED-010` | Nhập snapshot; không xuất dữ liệu riêng; toàn vẹn | 2, 5 |
| `BR-FLT-001`..`BR-FLT-005` | Không agent, SSH, toàn vẹn gói, timeout, đợt | 4, 6 |
| `BR-FLT-008` | Vai trò | 1 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FLT-FEED-001` | Cache dữ liệu trung tâm và phân phối snapshot | 1–7 |

### Giao diện và API liên quan
- Màn hình: `SCR-022` Phase 2 — Đợt chạy từ xa & phân phối snapshot.
- API: `POST /api/v1/feed-distributions`, `GET /api/v1/fleet-runs/{fleet_run_id}`.

### Quan hệ với use case khác
- `<<include>>` UC-FEED-001, UC-FEED-004 (trên máy trung tâm) và UC-FLT-002 (cơ chế đợt chạy).

### Ghi chú và tài liệu tham chiếu
- [api-spec-phase2.md §3.10](../api/api-spec-phase2.md); `FR-FLT-FEED-001`: [functional-requirements.md §13](../srs/functional-requirements.md).
