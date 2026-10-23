---
id: DOC-UC-QP-UPG-001
title: Đặc tả Use Case UC-UPG-001 — Cài runtime đích song song
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-001, migrate-install, side-by-side, php-fpm, pool, ini, extension, preconditions]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-003
  - DOC-SRS-QP-ENV-004
  - DOC-SRS-QP-ENV-005
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-UPG-001
  - DIAG-FLOW-QP-ENV-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: đồng bộ tên `FR-CLI-CMD-003` trong bảng FR liên quan với `functional-requirements.md` (`CR-FR-06`): "Cung cấp lệnh `migrate` và bí danh" |

## UC-UPG-001: Cài runtime đích song song

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`, `PER-02`). Ngoại lệ: Operator không root được cài Node.js qua nvm (PB-016) cho ứng dụng của chính mình (DOC-SRS-QP-ENV-001 §2.4).
- **Tác nhân hỗ trợ**: `SYS-03` package manager (`apt`, `dnf`, `apk`), panel (EasyApache/MultiPHP, CloudLinux Selector, Plesk, aaPanel, CyberPanel, DirectAdmin), kho bên thứ ba (Surý, Remi, LiteSpeed, NodeSource); `SYS-02` nodejs.org (tarball); System: Job runner.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh migrate install --runtime php|node --target X.Y|N [--from BIN]` (bí danh `upgrade`); mục P2 "Cài song song" của kế hoạch; console SCR-004.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: có `$NEW_BIN` và dịch vụ FPM đích `active` mà 0 site bị đổi; `$OLD` giữ nguyên để rollback 1 lệnh (`BR-ENV-008`).
  - Chủ site: liên kết mặc định của hệ thống (`readlink -f` của `php`, `php-fpm.sock`, `/usr/bin/node`) không đổi sau khi cài (`BR-SCN-012`); không thay runtime tại chỗ khi khác nhánh (`BR-UPG-001`).
  - `PER-04`: mỗi gói/kho/file cấu hình được thêm có dòng manifest và audit.
- **Tiền điều kiện (Pre-conditions)**:
  - Kế hoạch `cross_branch` ở `approved`/`in_progress` (UC-PLAN-002); mục P2 vá cùng nhánh (nếu có) đã `DONE` (`BR-UPG-006`).
  - Tiền điều kiện `BR-SCN-016`: đĩa trống ≥ 2 GB, RAM khả dụng ≥ 512 MB, root hoặc API panel, OS còn hỗ trợ, kho có nhánh đích.
  - Không chạy trong container (`BR-ENV-009`); playbook PHP khác `PB-000`.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `$NEW_BIN` cài song song, `$NEW_BIN -r 'exit(0);'` không in `Warning`/`Fatal`; dịch vụ FPM đích `active`; ini tuỳ chỉnh và extension đã sao chép (`cfg_report`); pool/handler đích cho từng site đã tạo và qua `php-fpm<X.Y> -t` (có thể chạy ở C3 của UC-UPG-002); mục P2 `DONE`; kế hoạch `in_progress`.
  - **Đảm bảo tối thiểu**: 0 site bị đổi gán; manifest ghi `link`, `created`, `copy` trước thay đổi; khi lỗi, liên kết mặc định giữ nguyên.
- **Kích hoạt (Trigger)**: Operator bấm "Chạy" trên mục P2 "Cài PHP/Node.js <target> song song" ở SCR-004, hoặc chạy `migrate install --runtime php --target 8.4 --yes`.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chọn mục P2 "Cài song song" trên SCR-004 và bấm "Chạy"; console tạo job dry-run `plan run <plan_id> <chk_id> --yes --json --dry-run` (`FR-PLAN-CHK-002`).
2. CLI kiểm tiền điều kiện cài song song và in lệnh cài dự kiến của playbook (vd `apt-cache policy php8.4-fpm`), kho cần thêm, liên kết sẽ ghim; 0 thay đổi (`FR-UPG-PRE-001`).
3. Console hiển thị SCR-011; Operator xác nhận trong ≤ 15 phút (UC-CON-003).
4. Console tạo job `write`; CLI chạy `migrate install --runtime php --target 8.4` (`FR-CLI-CMD-003`), lấy khoá độc quyền, ghi audit intent, manifest, `phase = MANIFEST_WRITTEN`; kế hoạch `approved` → `in_progress`.
5. CLI ghim mặc định hiện tại trước khi cài (Debian/Ubuntu: `update-alternatives --set` cho `php` và `php-fpm.sock`; Node.js: không ghi đè `/usr/bin/node` hoặc prefix đang dùng), ghi `link` vào manifest (`BR-SCN-012`).
6. CLI chạy lệnh `install` của playbook (vd `apt-get install php8.4-fpm php8.4-cli` + extension có `resolution=available`), `phase = CHANGING` (`FR-UPG-INST-001`).
7. CLI kiểm `readlink -f` các liên kết mặc định không đổi, `phase = VERIFYING`.
8. CLI sao chép file `conf.d/*.ini` không thuộc gói và giá trị khác mặc định trong `php.ini` của `$OLD` sang `$NEW`, loại directive bị gỡ theo `BR-SCN-046` (ghi lý do), không sao chép file mitigation; cài gói extension `available`; ghi `created`/`copy` vào manifest (`FR-UPG-CFG-002`).
9. CLI khởi động dịch vụ FPM đích, chờ `active` ≤ 15 s, chạy `$NEW_BIN -r 'exit(0);'` không in `Warning`/`Fatal`.
10. CLI tạo pool/handler đích cho từng site trong kế hoạch: sao chép pool `$OLD` sang `$NEW`, giữ `user`/`group`/`pm.*`, socket mới khác socket cũ, pool riêng `qp-<site_id>` khi site cũ dùng pool chung; kiểm `php-fpm<X.Y> -t` (`FR-UPG-CFG-001`, `BR-ENV-007`).
11. CLI ghi audit result, đặt mục P2 `DONE`, ghi `events.jsonl`, xuất `qp.migrate/1`, thoát 0.
12. Console làm mới SCR-004; các mục P3 cần `$NEW_BIN` (lint, PHPCompatibility, Composer platform) mở để chạy (UC-PLAN-003).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Mục phụ thuộc chưa `DONE`/`WAIVED`, hoặc kế hoạch `stale`**:
  - 1a1. Hệ thống trả `ERR-SCN-424-01` hoặc `ERR-PLAN-410-01`.
- **1b. Gọi CLI không qua kế hoạch**:
  - 1b1. `migrate install` là lệnh ghi mới: có TTY → hỏi `y/N`; không TTY và thiếu `--yes` → `ERR-CLI-428-01` (`BR-CLI-003`).
- **1c. `serve` chạy không root**:
  - 1c1. Console trả 403 `ERR-CLI-403-01` ở cổng J, không tạo tiến trình (DOC-API-QP-001 §2.13.4).
- **2a. Tiền điều kiện không đạt** (vd RAM khả dụng 380 MB < 512 MB):
  - 2a1. Hệ thống trả `ERR-SCN-412-01` "Máy chủ chưa đáp ứng điều kiện cài song song: {detail}."; Operator bổ sung tài nguyên hoặc chuyển sang máy chủ mới.
- **2b. Nhánh đích không có trong kho đang bật**:
  - 2b1. Hệ thống tạo mục `SEMI` riêng "Thêm kho" (Surý, Remi, LiteSpeed, NodeSource); sau khi Operator duyệt, CLI thêm file kho + khoá ký, ghi `created` vào manifest (`BR-ENV-004`). PO cấm thêm kho (`Q-03`) → đề xuất PB-013 hoặc máy chủ mới.
- **2c. Playbook `PB-000` hoặc CLI chạy trong container**:
  - 2c1. Hệ thống trả `ERR-ENV-422-01` hoặc khoá hành động theo `BR-ENV-009`.
- **3a. Dry-run không hợp lệ hoặc job ghi khác giữ khoá > 30 phút**:
  - 3a1. Console trả 428 `ERR-JOB-428-01`, hoặc job `FAILED` `ERR-JOB-409-02`.
- **4a. Không root và không có API panel**:
  - 4a1. CLI thoát 2 với `ERR-CLI-403-01` (`BR-CLI-005`).
- **4b. Không ghi được audit intent**:
  - 4b1. CLI thoát 2 với `ERR-AUD-500-01`, 0 thay đổi.
- **6a. Lệnh cài thất bại (gói không có trong kho, xung đột gói)**:
  - 6a1. CLI thoát 2 với `ERR-ENV-424-01` "Cài {runtime} {target} thất bại: {detail}."; 0 site bị đổi.
- **6b. Máy chủ dùng panel (PB-007..PB-012)**:
  - 6b1. CLI cài qua lệnh/API của panel theo DOC-SRS-QP-ENV-004; lệnh `verified=false` chỉ chạy ở mức `SEMI` có nhãn "chưa kiểm chứng" (`BR-ENV-010`).
  - 6b2. Panel trả lỗi hoặc giá trị đọc lại khác giá trị mong muốn → `ERR-ENV-502-01` (`BR-ENV-012`).
- **6c. Node.js tarball (PB-015)**:
  - 6c1. CLI tải tarball bản mới nhất của major đích, kiểm `SHASUMS256.txt`; lệch → `ERR-PTCH-502-01`.
  - 6c2. Binary chính thức không chạy được trên OS (lỗi `GLIBC_`, kiến trúc) → `ERR-SCN-412-03` (`BR-SCN-028`); đề xuất gói distro/NodeSource, container hoặc máy chủ mới.
- **7a. Liên kết mặc định bị đổi sau khi cài**:
  - 7a1. CLI khôi phục liên kết theo dòng `link` của manifest, ghi lỗi, thoát 2 (`BR-SCN-012`).
- **8a. Directive không chuyển được (bị gỡ ở `$NEW`)**:
  - 8a1. Directive vào `dropped_directives[]` kèm lý do; extension không có gói → `not_transferable[]`, mục P4 tương ứng ở `PENDING`.
- **9a. `$NEW_BIN` in `Warning`/`Fatal` hoặc dịch vụ FPM đích không `active` sau 15 s**:
  - 9a1. CLI thoát 2 với `ERR-ENV-500-01`; 0 site bị đổi.
- **10a. Pool đích không qua `php-fpm<X.Y> -t`**:
  - 10a1. CLI xoá file pool mới theo manifest, `ERR-ENV-500-01`.
- **10b. RAM không đủ cho pool đích** (`MemAvailable` < `pm.max_children` × RSS trung bình worker cũ + 256 MB):
  - 10b1. Hệ thống đề xuất `pm = ondemand` và `pm.max_children` = ⌊(MemAvailable − 256 MB) / RSS⌋, tối thiểu 2, để Operator duyệt (`FR-UPG-PRE-001`).
- **11a. Job vượt 3.600 s**:
  - 11a1. Job `FAILED` với `ERR-JOB-504-01`; Operator xem manifest và rollback khi cần (UC-PTCH-004).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-REL-002`: audit intent/result 100%; `NFR-ENV-05`: manifest có trước thay đổi.
- `NFR-ENV-06`: thêm playbook mới chỉ cần dữ liệu catalog, 0 dòng sửa trong luồng.
- `NFR-MNT-001`: thêm kịch bản/checklist: 0 dòng sửa trong `php-quickpatch.sh`.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-UPG-001` | Không thay runtime tại chỗ khi khác nhánh | 6 |
| `BR-UPG-006` | Vá cùng nhánh trước nâng nhánh | Tiền điều kiện |
| `BR-SCN-012` | Không đổi mặc định hệ thống | 5, 7 |
| `BR-SCN-016` | Điều kiện tiên quyết cài song song | 2 |
| `BR-SCN-017` | Ghi manifest | 4, 8 |
| `BR-SCN-045`, `BR-SCN-046` | Extension tương ứng; sao chép ini/pool | 8, 10 |
| `BR-SCN-026`, `BR-SCN-028` | Cài song song Node.js; glibc và nền tảng | 6c |
| `BR-ENV-004`, `BR-ENV-007`, `BR-ENV-009`, `BR-ENV-010`, `BR-ENV-012` | Kho bên thứ ba, pool riêng, container, lệnh chưa kiểm chứng, đọc lại panel | 2b, 6b, 10 |
| `BR-SEC-005` | Kiểm checksum tải xuống | 6c |
| `BR-CLI-003`, `BR-CLI-005`, `BR-CON-005` | Xác nhận, quyền, dry-run | 1, 3, 4 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-UPG-PRE-001` | Kiểm tra tiền điều kiện cài song song và chuyển site | 2, 10b |
| `FR-CLI-CMD-003` | Cung cấp lệnh `migrate` và bí danh | 4 |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | 5–7, 9 |
| `FR-UPG-CFG-002` | Sao chép ini tuỳ chỉnh và extension sang runtime đích | 8 |
| `FR-UPG-CFG-001` | Tạo pool/handler đích cho site | 10 |

### Giao diện và API liên quan
- Màn hình: `SCR-004` (mục P2), `SCR-011`, `SCR-006`.
- API: `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs` hoặc `POST /api/v1/jobs` (`action=migrate_install`).

### Quan hệ với use case khác
- Được gọi từ UC-PLAN-003 (mục P2); `<<include>>` UC-CON-003, UC-JOB-001.
- Được dùng lại bởi UC-UPG-005 (cài Node.js major mới).
- Tiếp nối: UC-UPG-002 (chuyển site).

### Ghi chú và tài liệu tham chiếu
- Lệnh cài theo từng playbook: [environment-playbooks-os.md](../srs/environment-playbooks-os.md), [environment-playbooks-panels.md](../srs/environment-playbooks-panels.md), [environment-playbooks-container-node.md](../srs/environment-playbooks-container-node.md); trình tự: [flows-upgrade.md §2](../srs/flows-upgrade.md).
- Câu hỏi mở `Q-03` (cho phép kho bên thứ ba) — spec §4.4.
