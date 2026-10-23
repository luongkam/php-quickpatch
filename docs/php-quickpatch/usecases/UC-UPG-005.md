---
id: DOC-UC-QP-UPG-005
title: Đặc tả Use Case UC-UPG-005 — Chuyển ứng dụng Node.js sang major mới
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-UPG-005, nodejs, major-upgrade, systemd, pm2, nvm, native-addon, engines]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-SCN-NODE-001
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
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-UPG-005 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-UPG-005: Chuyển ứng dụng Node.js sang major mới

- **Tác nhân chính (Primary Actor)**: Operator root (`PER-01`) cho unit systemd hệ thống; Operator không root (`PER-03`) cho ứng dụng pm2/nvm của chính user (PB-016, PB-018).
- **Tác nhân hỗ trợ**: `SYS-03` systemd, pm2, npm; `SYS-02` nodejs.org (tarball + `SHASUMS256.txt`), npm registry (`engines.node`); System: Job runner.
- **Phạm vi (Scope)**: `php-quickpatch.sh migrate install --runtime node --target N` + `migrate switch app:<tên>|app:pm2:<tên> --target N --plan <plan_id>`; playbook PB-014..PB-018; health check biến thể Node.js.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-03`: ứng dụng chạy trên dòng LTS đích với `$OLD` giữ nguyên để rollback; kế hoạch nâng major của dòng 22 được duyệt trước 2027-03-31, dòng 24 trước 2028-03-31 (`BR-SCN-029`).
  - Người dùng ứng dụng: thời gian gián đoạn khi `systemctl restart` hoặc `pm2 delete` + `pm2 start` được đo và ghi báo cáo; ứng dụng lỗi được tự rollback ≤ 60 s.
  - Kỹ sư bảo mật: tarball kiểm `SHASUMS256.txt` (`BR-SEC-005`); cờ `--openssl-legacy-provider` chỉ dùng tạm ≤ 30 ngày có duyệt (`BR-SCN-023`).
- **Tiền điều kiện (Pre-conditions)**:
  - Kế hoạch Node.js `approved`/`in_progress`; P3 (quét `engines.node`, native addon), P4 (nâng gói vi phạm) của ứng dụng `DONE`/`WAIVED`.
  - Ứng dụng được quản lý bởi systemd (PB-017) hoặc pm2 (PB-018); supervisor khác → mục `MANUAL`.
  - Dòng đích thoả `BR-SCN-006` (LTS, `eol` ≥ hôm nay + 365 ngày).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `$NEW_BIN` cài song song (tarball/nvm, không ghi đè prefix đang dùng); ứng dụng chạy bằng `$NEW_BIN` (`readlink /proc/<MainPID>/exe` hoặc `pm2 jlist` `exec_interpreter` = `$NEW_BIN`); health check 600 s ĐẠT; `switch_record` `PASSED`.
  - **Đảm bảo tối thiểu**: khi không đạt, drop-in/ecosystem được khôi phục theo manifest, ứng dụng chạy lại bằng `$OLD_BIN`.
- **Kích hoạt (Trigger)**: Operator chạy mục P2 "Cài Node.js N song song" rồi mục P5 "Chuyển ứng dụng" trên SCR-004, hoặc CLI tương ứng.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chạy mục P2 cài Node.js đích; hệ thống cài `$NEW` bằng tarball (PB-015) hoặc nvm (PB-016) vì gói NodeSource/distro chỉ có 1 gói `nodejs` mỗi hệ thống; tarball kiểm `SHASUMS256.txt`; không ghi đè prefix/`/usr/bin/node` đang dùng (`FR-UPG-INST-001`, `BR-SCN-026`, `BR-SCN-012`).
2. Hệ thống chạy thử `$NEW_BIN --version` sau giải nén, kiểm `ldd --version` (`BR-SCN-028`).
3. Operator chạy các mục P3/P4 trên bản sao `$COPY`: tái tạo lockfile v1 bằng npm của `$NEW` (`npm install --package-lock-only`, duyệt diff), `npm ci` exit 0, nạp thử từng native addon bằng `$NEW_BIN` (`BR-SCN-022`, `BR-SCN-024`), 0 dòng `ERR_OSSL_EVP_UNSUPPORTED` khi `$OLD` ≤ 16 (`BR-SCN-023`) (UC-PLAN-003).
4. Operator bấm "Chuyển" trên mục P5 của ứng dụng; hệ thống chạy dry-run và hiển thị SCR-011 (unit/ecosystem sẽ đổi, thời gian gián đoạn dự kiến); Operator xác nhận (UC-CON-003).
5. CLI chạy C1–C6 như UC-UPG-002 (khoá, điều kiện, baseline biến thể Node.js: trang chủ `http://127.0.0.1:<port>/`, `NRestarts`/`restart_time`, RSS trung bình 5 mẫu), ghi manifest.
6. **systemd (PB-017)**: CLI ghi `systemd <unit>` vào manifest, tạo drop-in `/etc/systemd/system/<unit>.d/zz-php-quickpatch-node.conf` (`created`) với `ExecStart=` rỗng rồi `ExecStart=` mới trỏ `$NEW_BIN` (hoặc `Environment=PATH=<bin của $NEW_BIN>:<PATH cũ>`), `systemctl daemon-reload`, `systemctl restart <unit>` (`FR-UPG-NODE-001`, `BR-SCN-027`).
7. CLI xác minh `HC-C0`: `ActiveState=active` ≤ 30 s và `readlink /proc/<MainPID>/exe` = `$NEW_BIN`.
8. CLI chạy health check biến thể Node.js 600 s: `HC-C5` bỏ chuỗi `<?php`, thêm `Error: Cannot find module`; `HC-C9`: `NRestarts`/`restart_time` tăng 0, RSS ≤ 1,5 × baseline (DOC-SRS-QP-ENV-002 §7).
9. Health check ĐẠT; CLI ghi `PASSED`, audit result, đặt mục P5/P6 `DONE`, ghi thời gian gián đoạn đo được vào báo cáo; thoát 0.
10. Sau khi mọi ứng dụng của 1 daemon pm2 đã chuyển, mục P7 hướng dẫn cài pm2 dưới `$NEW`, `pm2 update`, `pm2 unstartup` rồi `pm2 startup`, `pm2 save`; cập nhật `.nvmrc`, `.node-version`, `engines.node`, `FROM node:`, phiên bản Node trong CI (`BR-SCN-030`).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Checksum tarball lệch**:
  - 1a1. `ERR-PTCH-502-01`, xoá file tải về, mục P2 `FAILED`.
- **2a. Binary chính thức lỗi `GLIBC_` hoặc kiến trúc không hỗ trợ**:
  - 2a1. `ERR-SCN-412-03`; đề xuất gói distro/NodeSource build cho OS, container hoặc máy chủ mới.
- **3a. Native addon không nạp được sau khi build lại bằng `$NEW_BIN`**:
  - 3a1. `ERR-SCN-424-02` "Gói {package} (native addon) không nạp được trên Node.js {target}."; mục P4 `FAILED`; Operator nâng gói lên bản hỗ trợ ABI mới hoặc thay gói.
- **3b. `engines.node` của gói không chấp nhận dòng đích**:
  - 3b1. Gói vào danh sách nâng P4 (`BR-SCN-025`); gói chỉ thuộc `devDependencies` → cảnh báo.
- **3c. Dự án dùng `yarn.lock`/`pnpm-lock.yaml`**:
  - 3c1. Chỉ cảnh báo và hướng dẫn như v0.1 (ngoại lệ `BR-SCN-024`).
- **3d. `$OLD` ≤ 16, `$OLD` là dòng lẻ, hoặc khoảng cách ≥ 2 dòng LTS**:
  - 3d1. P3, P4 bắt buộc chạy trên staging (`BR-SCN-030`); khoảng cách 1 dòng LTS → staging khuyến nghị, miễn trừ có duyệt.
- **4a. Dòng đích là `CURRENT` chưa tới ngày `lts` cho ứng dụng production**:
  - 4a1. `ERR-SCN-409-02`.
- **5a. Không xác định được cổng của ứng dụng**:
  - 5a1. Hệ thống dùng URL khai báo; không có → `ERR-HC-412-03`, Operator khai báo `hc_url`.
- **5b. Ứng dụng có `hc_node_probe=on`**:
  - 5b1. Trước chuyển, hệ thống khởi động tạm 1 tiến trình bằng `$NEW_BIN` với `PORT` trống ngẫu nhiên trong 20000–29999; ĐẠT khi trang chủ không trả 5xx trong ≤ 30 s, rồi dừng tiến trình tạm.
- **6a. pm2 (PB-018)**:
  - 6a1. Có file ecosystem: CLI `copy` file và đặt `interpreter: '<$NEW_BIN>'`; không có: sinh `STATE_DIR/pm2/<app>.config.js` (`created`) từ `pm2 jlist`; ghi `pm2 <ecosystem> <app>` vào manifest.
  - 6a2. CLI chạy `pm2 delete <app>`, `pm2 start <ecosystem> --only <app>`, `pm2 save` dưới quyền chủ pm2; xác minh `exec_interpreter` = `$NEW_BIN` (`BR-SCN-027`).
  - 6a3. `pm2_env.env` khác trước/sau → yêu cầu Operator duyệt trước khi tiếp tục.
- **6b. Ứng dụng chạy bằng supervisor khác systemd/pm2**:
  - 6b1. Mục chuyển ở mức `MANUAL` (ngoại lệ `BR-SCN-027`).
- **6c. Drop-in khác sắp sau `zz-…` ghi đè `ExecStart`**:
  - 6c1. CLI kiểm `systemctl show -p ExecStart` sau `daemon-reload`; sai → khôi phục theo manifest, `ABORTED`.
- **7a. `HC-C0` không đạt trong 30 s**:
  - 7a1. Tự rollback: xoá drop-in (phát lại `created`) → `systemctl daemon-reload`, `systemctl restart <unit>`; hoặc hành động `pm2` với ecosystem cũ; `ERR-SCN-500-01`.
- **8a. Vi phạm tiêu chí health check**:
  - 8a1. Tự rollback ≤ 60 s như 7a1, `ROLLED_BACK`, `ERR-SCN-500-01`; `--no-auto-rollback` đã duyệt → `HC_FAILED_KEPT`, `ERR-HC-500-01`; rollback lỗi → `ROLLBACK_FAILED`, `ERR-HC-500-02`.
- **9a. Cần cờ `--openssl-legacy-provider` để ứng dụng chạy**:
  - 9a1. Chỉ dùng khi Operator duyệt, hạn ≤ 30 ngày, ghi vào manifest để gỡ ở P7 (`BR-SCN-023`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-ENV-02`, `NFR-ENV-03`: rollback ≤ 60 s; tự rollback bắt đầu ≤ 5 s.
- `NFR-ENV-05`: manifest trước thay đổi.
- Thời gian gián đoạn khi restart 1 tiến trình được đo và ghi báo cáo (không gián đoạn chỉ khi có ≥ 2 instance sau load balancer — ngoài phạm vi).

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCN-006`, `BR-SCN-007` | Chọn nhánh đích Node.js; cấm `CURRENT` trước `lts` cho production | Tiền điều kiện, 4a |
| `BR-SCN-012`, `BR-SCN-026`, `BR-SCN-028` | Không đổi mặc định; cài song song Node.js; glibc | 1, 2 |
| `BR-SCN-021`, `BR-SCN-022`, `BR-SCN-023`, `BR-SCN-024`, `BR-SCN-025` | Dải BC, native addon, OpenSSL 3, lockfile, `engines.node` | 3 |
| `BR-SCN-027` | Chuyển ứng dụng và restart | 6, 6a |
| `BR-SCN-029`, `BR-SCN-030` | Hạn duyệt; bắt buộc staging và tệp ghim | Stakeholders, 3d, 10 |
| `BR-ENV-003`, `BR-SCN-010`, `BR-HC-010` | Tuần tự; tự hoàn tác | 5, 7a, 8a |
| `BR-SEC-005` | Kiểm checksum | 1 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-UPG-INST-001` | Cài runtime đích song song (PHP và Node.js) | 1, 2 |
| `FR-UPG-NODE-001` | Chuyển 1 ứng dụng Node.js (systemd/pm2) | 4–9 |

### Giao diện và API liên quan
- Màn hình: `SCR-004`, `SCR-009` (site dạng `app:`), `SCR-011`, `SCR-006`.
- API: `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`, `POST /api/v1/jobs` (`migrate_install`, `migrate_switch` với `site_id` dạng `app:`/`app:pm2:`).

### Quan hệ với use case khác
- `<<include>>` UC-UPG-001 (cài song song) và luồng C1–C12 của UC-UPG-002; rollback bằng UC-UPG-004 (hành động `systemd`, `pm2`).

### Ghi chú và tài liệu tham chiếu
- PB-017/PB-018: [environment-playbooks-container-node.md §6, §7](../srs/environment-playbooks-container-node.md); biến thể health check: [environment-playbooks-healthcheck.md §7](../srs/environment-playbooks-healthcheck.md); `BR-SCN-020..030`: [version-scenarios-node.md §4](../srs/version-scenarios-node.md).
- Lệnh chưa kiểm chứng trong SRS: `systemd-analyze verify` trên drop-in, `pm2 start --only`, tên trường `pm2 jlist`; chỉ chạy ở mức `SEMI` có nhãn "chưa kiểm chứng" (`BR-ENV-010`).
