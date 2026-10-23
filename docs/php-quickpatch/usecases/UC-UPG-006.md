---
id: DOC-UC-QP-UPG-006
title: Đặc tả Use Case UC-UPG-006 — Đổi major base image Docker
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-006, docker, compose, base-image, major-upgrade, pb-013, override]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-ENV-005
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-STATE-QP-ENV-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-006 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-UPG-006: Đổi major base image Docker

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-03` DevOps Docker) — root hoặc thuộc nhóm `docker`.
- **Tác nhân hỗ trợ**: `SYS-03` Docker daemon, `docker compose`; Docker Hub (tag image, chỉ khi có mạng); proxy Nginx/Apache trên host hoặc trong Compose; System: Job runner.
- **Phạm vi (Scope)**: playbook PB-013 — dịch vụ Compose dùng image `php:`/`node:`; `migrate switch svc:<project>/<service> --target X.Y|N --plan <plan_id>`.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-03`: dịch vụ chạy trên base image major mới, image cũ được giữ bằng tag `qp-rollback/<project>-<service>:<run_id>` để rollback.
  - Người dùng dịch vụ: khi có lớp proxy, đổi upstream bằng reload proxy (không gián đoạn); khi không có lớp proxy, thời gian gián đoạn được đo và ghi báo cáo.
  - Chủ dữ liệu: entrypoint chứa `migrate` (vd `php artisan migrate`) được phát hiện và yêu cầu xác nhận trước khi chạy container mới (DOC-SRS-QP-ENV-005 §2.3 rủi ro 1); tool không `push` image (`BR-ENV-011`).
- **Tiền điều kiện (Pre-conditions)**:
  - `docker info` exit 0; CLI chạy trên host (`BR-ENV-009`).
  - Kế hoạch `approved`/`in_progress` cho dịch vụ; quét tương thích mã (PHP) hoặc `engines`/native addon (Node.js) của dịch vụ `PASS`.
  - Tag nhánh đích tồn tại trên Docker Hub hoặc Dockerfile build được.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: dịch vụ `<service>-qp<NEWND>` chạy image đích, `running` (và `healthy` khi image có `HEALTHCHECK`); upstream trỏ dịch vụ mới; health check 600 s ĐẠT; `switch_record` `PASSED`; manifest có `compose`, `created` (file override, Dockerfile bản sao), `copy` (cấu hình proxy, file compose).
  - **Đảm bảo tối thiểu**: khi lỗi, cấu hình proxy/file compose được khôi phục và container cũ chạy lại bằng tag `qp-rollback/...`.
- **Kích hoạt (Trigger)**: Operator chạy mục P5 "Chuyển dịch vụ {service} sang {image đích}" trên SCR-004, hoặc `migrate switch svc:<project>/<service> --target <nhánh> --plan <plan_id> --yes`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator bấm "Chuyển" trên mục P5 của dịch vụ; hệ thống chạy dry-run: quét `entrypoint`/`command` tìm chuỗi `migrate`, liệt kê volume ghi dùng chung, file sẽ tạo/sửa; SCR-011 hiển thị (UC-CON-003).
2. Operator xác nhận; CLI chạy C1–C2 (khoá, điều kiện) và C5 baseline trên dịch vụ cũ (URL của vhost proxy hoặc `http://127.0.0.1:<cổng publish>/`).
3. CLI gắn tag giữ image cũ: `docker tag <image ID cũ> qp-rollback/<project>-<service>:<run_id>` (`created`); ghi ID image cũ vào `switch.json` (`FR-UPG-DKR-001`).
4. CLI tạo file override `compose.qp-<service>-<NEW>.yaml` (`created`) định nghĩa dịch vụ `<service>-qp<NEWND>`: sao chép định nghĩa gốc, đổi `image:` sang tag nhánh đích hoặc `build.dockerfile` sang `Dockerfile.qp-<NEWND>` (bản sao với `FROM` mới), bỏ `ports:` trùng, giữ `volumes`, `networks`, `env_file`; kiểm `docker compose -f <gốc> -f <override> config` exit 0.
5. Sau khi Operator duyệt mục `SEMI`, CLI chạy `docker compose -f <gốc> -f <override> up -d --no-deps <service>-qp<NEWND>`; container `running`/`healthy` (`BR-ENV-011`).
6. CLI đổi upstream (c1): proxy trên host → sửa `fastcgi_pass`/`proxy_pass` theo PB-005; Nginx trong Compose → sửa file cấu hình được mount (`copy`), `docker compose exec <nginx> nginx -t`, `nginx -s reload`.
7. CLI xác minh `HC-C0` (phương pháp 5: container đích `running`/`healthy`), rồi chạy health check 600 s với `HC-C9` = `RestartCount` tăng 0 và `.State.Health.Status = healthy`; log = `docker logs --since <t_C9>` (DOC-SRS-QP-ENV-002 §7).
8. Health check ĐẠT; CLI ghi `PASSED`, audit result; mục P5/P6 `DONE`; thoát 0.
9. Mục P7 (có duyệt): dịch vụ `<service>-qp<NEWND>` trở thành dịch vụ chính trong file compose gốc; tag `qp-rollback/*` chỉ xoá theo `BR-SCN-014`.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Entrypoint/command chứa `migrate`**:
  - 1a1. Hệ thống yêu cầu Operator xác nhận riêng trước bước 5 vì container mới có thể thay đổi CSDL dùng chung với container cũ.
- **1b. Dịch vụ định tuyến bằng Traefik/Caddy theo nhãn, Kubernetes hoặc Swarm**:
  - 1b1. Mục ở mức `MANUAL` (ngoài phạm vi tự động, DOC-SRS-QP-ENV-005 §2.3).
- **1c. CLI chạy trong container**:
  - 1c1. Hành động bị khoá; hướng dẫn chạy ở host (`BR-ENV-009`).
- **2a. Đang có lượt chuyển `HC_RUNNING` hoặc khoá bận**:
  - 2a1. `ERR-ENV-409-01`.
- **2b. Dịch vụ không thuộc kế hoạch, hoặc nhánh đích `EOL`/`PRE_RELEASE`**:
  - 2b1. `ERR-UPG-409-02` hoặc `ERR-SCN-409-02`.
- **4a. `docker compose config` không hợp lệ**:
  - 4a1. CLI xoá file override theo manifest, `ABORTED`.
- **5a. `docker compose build`/`up` của dịch vụ đích thất bại** (vd tên extension trong `docker-php-ext-install` khác giữa nhánh):
  - 5a1. `ERR-ENV-424-02` "Không khởi động được dịch vụ {service} với image {image}."; dịch vụ cũ không bị đổi; Operator sửa Dockerfile trên staging.
- **6a. Không có lớp proxy (image publish cổng trực tiếp)** — phương án (c2) tạo lại tại chỗ:
  - 6a1. CLI `copy` file compose, đổi `image:`/`FROM` của chính dịch vụ, ghi `compose <file> <service>`, chạy `docker compose up -d --no-deps <service>`; đo thời gian gián đoạn từ lúc container cũ dừng tới lúc container mới trả mã baseline và ghi báo cáo.
- **6b. `nginx -t` trong container proxy thất bại**:
  - 6b1. CLI khôi phục file cấu hình, không reload, `ERR-ENV-500-02`.
- **7a. Vi phạm tiêu chí health check**:
  - 7a1. Tự rollback: (c1) khôi phục `copy` cấu hình proxy → `nginx -t` → reload; (c2) khôi phục file compose → hành động `compose` với tag `qp-rollback/...`; `ROLLED_BACK`, `ERR-SCN-500-01`.
  - 7a2. Rollback lỗi → `ROLLBACK_FAILED`, `ERR-HC-500-02`, khoá chuyển site (`ERR-UPG-423-01`).
- **8a. Job vượt 1.200 s**:
  - 8a1. Job `FAILED` với `ERR-JOB-504-01`.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-ENV-03`: tự rollback bắt đầu ≤ 5 s, hoàn tất ≤ 60 s.
- `NFR-ENV-05`: manifest trước thay đổi.
- Thời gian gián đoạn của phương án (c2) được đo và ghi báo cáo (SRS chưa đặt ngưỡng).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-UPG-001` | "Song song" = dịch vụ/container mới trong PB-013 | 4, 5 |
| `BR-ENV-011` | Chỉ chạy `docker compose build/up` sau duyệt; không `push` | 5 |
| `BR-ENV-009` | Không chạy PB-013 bên trong container | 1c |
| `BR-ENV-003`, `BR-ENV-005` | Tuần tự; kiểm cú pháp trước reload | 2, 6 |
| `BR-SCN-010`, `BR-HC-010`, `BR-SCN-014` | Tự hoàn tác; giữ image cũ tới khi đủ điều kiện gỡ | 7a, 9 |
| `BR-SCN-017` | Manifest trước thay đổi | 3, 4 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-UPG-DKR-001` | Chuyển 1 dịch vụ Compose | 1–9 |

### Giao diện và API liên quan
- Màn hình: `SCR-004`, `SCR-009` (site dạng `svc:`), `SCR-011`, `SCR-006`.
- API: `POST /api/v1/jobs` (`migrate_switch` với `site_id` dạng `svc:<project>/<service>`), `GET /api/v1/containers`, `GET /api/v1/switches/{run_id}`.

### Quan hệ với use case khác
- Dùng luồng C1–C12 của UC-UPG-002 với biến thể container; rollback bằng UC-UPG-004 (hành động `compose`); vá cùng nhánh tag image là UC-PTCH-003.

### Ghi chú và tài liệu tham chiếu
- PB-013: [environment-playbooks-container-node.md §2](../srs/environment-playbooks-container-node.md). ≥ 4 nhóm lệnh của PB-013 đang ở trạng thái "chưa kiểm chứng" (KC = Chưa: nhãn Compose, `docker inspect`, cú pháp override, `docker tag` giữ image cũ) → chỉ chạy ở mức `SEMI` có nhãn (`BR-ENV-010`) cho tới khi QA chạy thử.
