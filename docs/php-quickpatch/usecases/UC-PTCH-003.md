---
id: DOC-UC-QP-PTCH-003
title: Đặc tả Use Case UC-PTCH-003 — Vá image/container Docker cùng nhánh
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-PTCH-003, docker, dockerfile, compose, image-tag, container, mitigation]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-005
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-JOB-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-PTCH-003 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: bảng FR liên quan đổi tên `FR-PTCH-DKR-002` thành "Ghi mitigation vào container đang chạy" theo DOC-SRS-QP-FR-001 (`CR-FR-06`) |

## UC-PTCH-003: Vá image/container Docker cùng nhánh

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-03` DevOps Docker) — root hoặc thuộc nhóm `docker` (quyền tương đương root trên host, DOC-SRS-QP-ENV-005 §2.3).
- **Tác nhân hỗ trợ**: `SYS-03` Docker daemon; `SYS-02` php.net/nodejs.org (bản patch mới nhất cùng nhánh); System: Job runner; pipeline CI của `PER-03` (build/redeploy image ngoài tool).
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh fix --only docker` (kế thừa v0.1 `check_dockerfiles`, `check_containers`); Dockerfile, `docker-compose.y*ml`, `compose.y*ml`; container đang chạy trên host.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-03`: tag image `php:`/`node:` ghim bản patch được nâng lên bản patch mới nhất cùng nhánh; biết base image EOL; container đang chạy bản chưa vá được giảm thiểu cho tới khi rebuild.
  - Chủ dịch vụ: tool không tự build/push image (`BR-ENV-011`); mọi file Dockerfile/compose bị sửa có bản sao lưu.
- **Tiền điều kiện (Pre-conditions)**:
  - `docker info` exit 0 (khi xử lý container đang chạy); có Dockerfile/compose chứa `FROM php:`/`FROM node:`/`image: php:`/`image: node:` (khi xử lý file).
  - CLI chạy trên host, không ở trong container (`BR-ENV-009`).
  - Bundle feeds có mốc vá của nhánh (`BR-DATA-002`).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: tag ghim bản patch thấp hơn mốc được đổi sang bản patch mới nhất cùng nhánh trong file đã sao lưu; issue `high` "rebuild and redeploy the image(s) to apply the new tag"; container PHP chưa vá có file mitigation trong `conf.d` và đã `docker restart` (trừ `--no-restart`); issue `critical` "cần rebuild image".
  - **Đảm bảo tối thiểu**: tool không chạy `docker build`, `docker push`; file không đổi khi `--dry-run`.
- **Kích hoạt (Trigger)**: Operator chạy `fix --only docker [--path DIR] [--dry-run] [--no-restart]`, hoặc tạo job `fix` với `only=docker` trên console.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator tạo job dry-run `fix --json --only docker --dry-run` trên console (hoặc chạy CLI); SCR-011 hiển thị file sẽ sửa, container sẽ ghi mitigation và restart (UC-CON-003).
2. Operator xác nhận; console tạo job `fix --json --only docker` loại `write`.
3. CLI lấy khoá độc quyền, ghi audit intent, tạo manifest (`FR-PTCH-RBK-001`).
4. CLI quét Dockerfile/compose bằng biểu thức `FROM`/`image:` của v0.1 (độ sâu 7 cấp) (`FR-PTCH-DKR-001`).
5. Với tag ghim bản patch thấp hơn mốc vá: CLI xác định bản patch mới nhất cùng nhánh từ php.net/nodejs.org (`BR-DATA-002`), `backup_file` rồi ghi lại tag (vd `php:8.4.12-fpm` → `php:8.4.<bản mới nhất>-fpm`).
6. CLI ghi issue `high` "rebuild and redeploy the image(s) to apply the new tag" cho mỗi file đã sửa.
7. Với container đang chạy PHP chưa vá: CLI đọc thư mục `conf.d` trong container (`php --ini`), ghi `zz-php-quickpatch-mitigation.ini` vào container bằng `docker exec`, rồi `docker restart <id>` (`FR-PTCH-DKR-002`, `BR-PTCH-004`).
8. CLI ghi issue `critical` "container {name}: PHP {v} (image {image}) needs a rebuild" và ghi chú mitigation mất khi container được tạo lại.
9. CLI ghi audit result, xuất `qp.fix/1`, thoát 1 (còn việc rebuild/redeploy).
10. `PER-03` rebuild và redeploy image bằng pipeline CI hoặc `docker compose build --pull` ngoài tool.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. Dry-run không còn hợp lệ**:
  - 2a1. Console trả 428 `ERR-JOB-428-01`.
- **3a. CLI chạy trong container**:
  - 3a1. Chỉ cho phép mitigation cho runtime trong chính container đó; hướng dẫn chạy tool ở host (`BR-ENV-009`).
- **4a. Không có Dockerfile/compose chứa `FROM php:`, `FROM node:`, `image: php:` hoặc `image: node:`**:
  - 4a1. CLI ghi "No Dockerfile or compose file found." và chuyển sang bước 7.
- **5a. Tag trôi theo nhánh (vd `php:8.4-fpm`, `node:24`)**:
  - 5a1. CLI giữ tag, ghi chú "rebuild with `docker build --pull` / `docker compose build --pull`".
- **5b. Tag thuộc nhánh EOL**:
  - 5b1. CLI ghi issue `high` "PHP/Node image {ver} is EOL", không đổi tag; đề xuất đổi major base image (UC-UPG-006).
- **5c. Không lấy được bản patch mới nhất (offline, nguồn lỗi)**:
  - 5c1. CLI dùng mốc `min_patched` của bundle làm tag đích; nguồn lỗi ghi `ERR-FEED-503-01`.
- **5d. `--dry-run`**:
  - 5d1. CLI in "[dry-run] rewrite image tags in {file}", không ghi file.
- **7a. Container không có thư mục `conf.d` (`php --ini` trả `(none)`)**:
  - 7a1. CLI ghi `ERR-PTCH-412-01`, không ghi mitigation.
- **7b. Có `--no-restart`**:
  - 7b1. CLI ghi mitigation nhưng không restart container; issue `high` "chưa restart".
- **7c. `docker info` exit ≠ 0**:
  - 7c1. CLI bỏ qua phần container.
- **9a. Job vượt 3.600 s hoặc thoát 2**:
  - 9a1. Job `FAILED` (`ERR-JOB-504-01`, `ERR-JOB-500-01`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-002`: audit intent trước thay đổi, audit result khi kết thúc.
- `NFR-CMP-005`: chạy được khi không có Python 3.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-ENV-011` | Không tự build/deploy image | 9, 10 |
| `BR-ENV-009` | Trong container chỉ mitigation | 3a, 7 |
| `BR-DATA-002` | Nguồn mốc bản vá php.net/nodejs.org | 5 |
| `BR-PTCH-004` | Mitigation tạm | 7 |
| `BR-SCN-017`, `BR-CON-005` | Ghi manifest; dry-run | 1, 3 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-PTCH-DKR-001` | Nâng tag image cùng nhánh | 4–6 |
| `FR-PTCH-DKR-002` | Ghi mitigation vào container đang chạy | 7, 8 |

### Giao diện và API liên quan
- Màn hình: `SCR-011`, `SCR-006`; container hiển thị trên `SCR-002`.
- API: `POST /api/v1/jobs` (`action=fix`, `only=docker`), `GET /api/v1/containers`, `GET /api/v1/projects`.

### Quan hệ với use case khác
- `<<include>>` UC-CON-003, UC-JOB-001; đổi major base image là UC-UPG-006.

### Ghi chú, phát hiện và tài liệu tham chiếu
- Hành vi đã kiểm chứng trên `php-quickpatch.sh` v0.1.0: `check_dockerfiles` (dòng 651–699), `check_containers` ghi mitigation qua `docker exec` và `docker restart` (dòng 701–720).
- Phát hiện: v0.1 không ghi dòng manifest cho file mitigation trong container, nên `rollback` không gỡ được file này; SRS `FR-PTCH-DKR-002` chưa nêu. Đề xuất: ghi dòng `note` vào manifest kèm lệnh gỡ thủ công (chờ BA + Dev).
