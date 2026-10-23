---
id: DOC-UC-QP-CLI-001
title: Đặc tả Use Case UC-CLI-001 — Tích hợp CI đọc kết quả --json
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-CLI-001, ci, json, json-schema, exit-code, envelope, devops]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-API-QP-005
related_diagrams:
  - DIAG-UC-QP-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-CLI-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: `NFR-CMP-002` chép theo nfr.md hiện hành (Bash 4.3 tới 5.3; thêm Ubuntu LTS 26.04) và liên kết tới nfr.md; tên `FR-CLI-CMD-001`, `FR-CLI-JSON-001` chép theo functional-requirements.md (`CR-FR-06`); thêm `DOC-SRS-QP-NFR-001` vào `depends_on` |

## UC-CLI-001: Tích hợp CI đọc kết quả --json

- **Tác nhân chính (Primary Actor)**: `PER-03` DevOps — pipeline CI (Operator root hoặc không root, tuỳ quyền runner) gọi CLI trên máy chủ hoặc trong job CI.
- **Tác nhân hỗ trợ**: hệ thống CI (đọc stdout và mã thoát); bộ kiểm JSON Schema 2020-12 của CI; `SYS-02` nguồn online (khi không `--offline`).
- **Phạm vi (Scope)**: mọi lệnh CLI có `--json` (`scan`, `assess`, `fix --dry-run`, `plan`, `migrate status`, `feeds status`, `report`, `audit`), lệnh `schema <lệnh>`, schema trong `share/php-quickpatch/schemas/`; client API dùng `Authorization: Bearer`.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-03`: stdout chứa đúng 1 tài liệu JSON UTF-8 hợp lệ theo schema đã phát hành (`NFR-CMP-004`); mã thoát chỉ nhận 3 giá trị 0/1/2 với ý nghĩa cố định giữa các bản phát hành để chặn pipeline (`BR-CLI-004`).
  - Bảo trì CI: thêm trường không đổi major schema; đổi tên/xoá/đổi kiểu → tăng major; bản có major mới vẫn xuất major cũ bằng `--json-schema <major cũ>` trong ≥ 2 bản minor kế tiếp (`BR-CLI-001`).
  - Kỹ sư bảo mật: `command.argv` trong JSON đã che bí mật (`BR-SEC-006`); JSON không chứa token/API key.
- **Tiền điều kiện (Pre-conditions)**:
  - Runner có Bash ≥ 4.3, `flock`, `curl`; Python ≥ 3.6 cho lệnh `assess`, `plan`, `report`.
  - Pipeline lưu được schema `qp.<lệnh>.v<major>.schema.json` hoặc gọi `schema <lệnh>`.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: CI nhận envelope gồm `schema` (`qp.<lệnh>/<major>`), `tool{name, version}`, `generated_at`, `host{hostname, os, kernel, is_root, in_container}`, `command{name, argv}`, `dry_run`, `exit_code`, `data` (độ tươi feed: `bundle_id`, `freshness`, `data_age_h`, `stale_sources[]`), `catalog_version`, `result`, `issues[]`, `errors[]`, `warnings[]`; pipeline quyết định đạt/không đạt theo mã thoát và `issues[].severity`.
  - **Đảm bảo tối thiểu**: khi lỗi tham số/môi trường, stdout vẫn là JSON hợp lệ với `errors[].code` = mã `ERR-*` và mã thoát 2.
- **Kích hoạt (Trigger)**: pipeline CI chạy bước bảo mật, vd `php-quickpatch.sh scan --only php,node,composer,npm,docker --json --path /repo`.

### Luồng sự kiện chính (Main Success Scenario)
1. Pipeline CI chạy lệnh với `--json` trên runner hoặc máy chủ đích.
2. CLI kiểm môi trường chạy (Bash, `flock`, `curl`, `python3` khi lệnh cần) và quyền (`FR-CLI-ENV-001`).
3. CLI thực hiện lệnh (vd `scan`, `assess --runtime-id ID --candidates`) (`FR-CLI-CMD-001`).
4. CLI ghi văn bản cho người đọc ra stderr và file log; ghi đúng 1 tài liệu JSON ra stdout, tự escape chuỗi (`\`, `"`, ký tự điều khiển) không phụ thuộc `jq` (`FR-CLI-JSON-001`).
5. CLI thoát 0 (không còn vấn đề), 1 (còn vấn đề hoặc thành công có cảnh báo) hoặc 2 (lỗi tham số/runtime/khoá).
6. Pipeline lấy schema bằng `php-quickpatch.sh schema scan` hoặc file `share/php-quickpatch/schemas/qp.scan.v1.schema.json` (JSON Schema 2020-12) (`FR-CLI-JSON-002`).
7. Pipeline kiểm stdout theo schema, đọc `issues[]` (`severity`, `code`, `message`), `data.freshness`, và quyết định chặn merge/deploy khi có finding `critical`/KEV hoặc mã thoát ≠ 0.
8. Pipeline lưu envelope làm artifact bằng chứng cho `PER-04`.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Tham số sai**:
  - 1a1. JSON có `errors[].code = ERR-CLI-400-01`, mã thoát 2.
- **1b. Pipeline gọi API console thay cho CLI**:
  - 1b1. Client gửi `Authorization: Bearer <token>` (không tạo phiên, không cần CSRF); token qua query string bị từ chối (`BR-AUTH-005`); job tạo bằng `POST /api/v1/jobs`, kết quả đọc bằng `GET /api/v1/jobs/{job_id}` mỗi 2 s (đề xuất DOC-API-QP-001 §2.13.1); `result` = envelope `--json` của CLI.
- **2a. Bash < 4.3 hoặc thiếu `flock`/`curl`**:
  - 2a1. `ERR-CLI-424-02`, mã thoát 2.
- **2b. Lệnh cần Python mà thiếu Python ≥ 3.6**:
  - 2b1. `ERR-CLI-424-01`, mã thoát 2; pipeline dùng `scan --json` (không cần Python, `NFR-CMP-005`).
- **2c. Lệnh mới cần root mà runner không root**:
  - 2c1. `ERR-CLI-403-01`, mã thoát 2; lệnh v0.1 (`scan`, `fix`) ghi issue "needs root" và tiếp tục.
- **2d. Lệnh ghi mới không có TTY và thiếu `--yes`**:
  - 2d1. `ERR-CLI-428-01`, mã thoát 2 (`BR-CLI-003`).
- **3a. Khoá `STATE_DIR/.lock` đang bị lượt khác giữ**:
  - 3a1. `ERR-CLI-423-01`, mã thoát 2; pipeline thử lại sau khoảng chờ do pipeline cấu hình.
- **3b. `runtime_id` không có trong scan gần nhất**:
  - 3b1. `ERR-ASMT-404-01`; pipeline chạy `scan` trước.
- **3c. Dữ liệu cũ > 7 ngày hoặc nguồn lỗi**:
  - 3c1. `warnings[]`/`issues[]` chứa `ERR-FEED-412-01`/`ERR-FEED-503-01`; `data.freshness` = `STALE`; mã thoát theo kết quả tổng.
- **6a. Pipeline cần schema major cũ sau khi tool nâng major**:
  - 6a1. Gọi `--json-schema <major cũ>` (hỗ trợ ≥ 2 bản minor kế tiếp, `BR-CLI-001`).
- **7a. Đầu ra không khớp schema đã phát hành** (lỗi tool):
  - 7a1. Pipeline đánh dấu bước lỗi; vi phạm `NFR-CMP-004`, cần báo lỗi cho bên phát hành tool.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-CMP-004`: 100% đầu ra `--json` hợp lệ theo JSON Schema đã phát hành.
- `NFR-CMP-002`: CLI chạy trên Bash 4.3 tới 5.3 và trên Debian 11–13, Ubuntu LTS 20.04, 22.04, 24.04, 26.04, AlmaLinux/Rocky 8–10, Alpine 3.22–3.24 (ma trận CI; nội dung gốc và nguồn kiểm chứng: [nfr.md §4.5, §5](../srs/nfr.md)).
- `NFR-CMP-005`: `scan`, `fix`, `rollback`, `migrate` chạy được khi không có Python 3.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-CLI-001` | Tương thích schema JSON | 6, 6a |
| `BR-CLI-004` | Mã thoát 0/1/2 | 5 |
| `BR-CLI-005` | Quyền chạy | 2c |
| `BR-CLI-003` | Xác nhận lệnh ghi mới | 2d |
| `BR-FEED-059` | Tương thích ngược schema `feeds` | 6 |
| `BR-SEC-006` | Che bí mật trong `argv` | 4 |
| `BR-AUTH-005` | Bearer cho client API | 1b |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CLI-ENV-001` | Kiểm tra quyền và môi trường chạy | 2 |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | 3 |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | 4, 5 |
| `FR-CLI-JSON-002` | Công bố JSON Schema | 6 |

### Giao diện và API liên quan
- Giao diện: stdout/stderr/mã thoát của CLI; `share/php-quickpatch/schemas/qp.<lệnh>.v<major>.schema.json`; hợp đồng `--json` tại DOC-API-QP-005.
- API (tuỳ chọn): `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}` với `Authorization: Bearer`.

### Quan hệ với use case khác
- Dùng đầu ra của UC-SCAN-001, UC-ASMT-001, UC-FEED-003, UC-RPT-001; Phase 2 máy trung tâm cũng đọc cùng envelope (UC-FLT-002).

### Ghi chú và tài liệu tham chiếu
- Hợp đồng `--json`: [api-spec-cli-json.md](../api/api-spec-cli-json.md); envelope: [functional-requirements.md §11](../srs/functional-requirements.md).
- `NFR-CMP-002`: [nfr.md](../srs/nfr.md) (DOC-SRS-QP-NFR-001) §4.5, nguồn §5. Kiểm chứng lại ngày 2026-10-23 trên pkgs.alpinelinux.org (nhánh `main`, `x86_64`): Alpine 3.23 có `bash 5.3.3-r1`, Alpine 3.24 có `bash 5.3.9-r1` — https://pkgs.alpinelinux.org/packages?name=bash&branch=v3.23&repo=main&arch=x86_64, https://pkgs.alpinelinux.org/packages?name=bash&branch=v3.24&repo=main&arch=x86_64. Bash 5.3 của Ubuntu 26.04: theo nfr.md §5 (Launchpad), chưa kiểm chứng lại trong phiên này.
