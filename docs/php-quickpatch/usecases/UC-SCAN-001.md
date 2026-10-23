---
id: DOC-UC-QP-SCAN-001
title: Đặc tả Use Case UC-SCAN-001 — Quét máy chủ và kiểm kê runtime, site, dự án
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-SCAN-001, scan, runtime, site-binding, playbook, webshell, scenario, cli, console]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-SCAN-001
  - DIAG-FLOW-QP-ENV-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-SCAN-001 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: tên `FR-CLI-COMP-001`, `FR-CLI-JSON-001` chép theo functional-requirements.md (`CR-FR-06`); bước 2 chọn và kiểm `STATE_DIR` theo spec §2.1 thay quy ước v0.1; thêm nhánh 2c `STATE_DIR` không đạt kiểm tra → `ERR-CLI-412-01`, thoát 2, 0 file đọc/ghi (`CR-SRS-13`); bổ sung ghi chú và nguồn |

## UC-SCAN-001: Quét máy chủ và kiểm kê runtime, site, dự án

- **Tác nhân chính (Primary Actor)**: Operator root hoặc Operator không root (`PER-01` người vận hành VPS, `PER-02` quản trị hosting có panel, `PER-03` DevOps Docker).
- **Tác nhân hỗ trợ (Secondary / System Actor)**: `SYS-02` nguồn online (khi bundle quá TTL); `SYS-03` hạ tầng đích (package manager, panel, Docker daemon, web server) — chỉ được đọc; System: Job runner của console khi quét được kích hoạt từ SCR-002.
- **Phạm vi (Scope)**: CLI `php-quickpatch.sh scan` (lệnh mặc định, kế thừa v0.1.0) và job `scan` của web console Phase 1.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng).
- **Kênh**: CLI văn bản / `--json`; console SCR-002 (nút "Quét lại"), SCR-009.
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`: biết trạng thái (`ok`, `ok-backport`, `vulnerable`, `eol`, `unknown`) của 100% binary PHP/Node.js trên máy trong 1 lượt chạy ≤ 60 s ở P95 khi offline (`NFR-PERF-004`).
  - `PER-02`: biết mỗi site đang dùng binary nào theo đúng playbook của panel; nhận diện môi trường ≤ 5 s với ≤ 200 vhost (`NFR-ENV-07`).
  - `PER-03`: nhận 1 tài liệu JSON hợp lệ theo schema `qp.scan/1` (`NFR-CMP-004`) và mã thoát 0/1/2 để CI quyết định (`BR-CLI-004`).
  - `PER-04` (Auditor): mọi kết quả ghi `bundle_id`, `data_age_h`, `stale_sources[]` để truy nguồn dữ liệu (`FR-FEED-AGE-001`).
  - Chủ site / khách hàng hosting: lượt quét ghi 0 file ngoài `STATE_DIR` và thư mục tạm của tool, restart 0 dịch vụ, cài 0 gói (`BR-SCAN-001`).
- **Tiền điều kiện (Pre-conditions)**:
  - Máy chủ Linux có Bash ≥ 4.3, `flock`, `curl` (`FR-CLI-ENV-001`).
  - Có ít nhất 1 trong 3 nguồn dữ liệu: bundle `feeds/current/` hợp lệ, snapshot đóng gói khớp `QP_SNAPSHOT_SHA256`, hoặc kết nối HTTPS tới `SRC-001..016` (`BR-FEED-053`).
  - Không có lượt ghi (`fix`, `rollback`, `migrate`) đang giữ khoá độc quyền `STATE_DIR/.lock` (`BR-JOB-002`).
  - Khi chạy từ console: phiên console hợp lệ (UC-CON-001).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: `STATE_DIR/state/last-scan.json` chứa envelope `qp.scan/1` với `environment`, `runtimes[]` (mỗi runtime có `runtime_id`, `scenario_ids[]`, `lifecycle_status`, `priority`, `state`, `locked`), `site_binding[]`, `projects[]`, `containers[]`, `webshell_findings[]`, `drift_warnings[]`, tuổi dữ liệu; mã thoát 0 (không còn vấn đề) hoặc 1 (còn vấn đề).
  - **Đảm bảo tối thiểu**: 0 thay đổi cấu hình hệ thống; mọi lỗi được ghi vào `errors[]`/`issues[]` của envelope và `php-quickpatch.log`; khoá `STATE_DIR/.lock` được giải phóng khi tiến trình kết thúc.
- **Kích hoạt (Trigger)**: Operator chạy `php-quickpatch.sh scan [--path DIR]... [--only php,node,composer,npm,wp,docker,webshell,sites] [--offline] [--json]`; hoặc bấm "Quét lại" trên SCR-002 (hiện khi kết quả scan cũ > 24 giờ, `FR-CON-OVW-001`); hoặc lệnh `assess` thấy kết quả scan cũ > 24 giờ (`FR-CLI-CMD-001`).

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chạy lệnh `scan` trên terminal SSH, hoặc bấm "Quét lại" trên SCR-002; console tạo job hành động `scan` (argv `scan --json [--only <enum>] [--offline]`, loại `read`) qua danh sách trắng (`BR-CON-008`, `BR-JOB-003`).
2. CLI kiểm tra môi trường chạy: phiên bản Bash, `flock`, `curl`, `EUID`; chọn và kiểm `STATE_DIR` theo spec §2.1 trước lần đọc/ghi đầu tiên trong thư mục và trước khi mở `STATE_DIR/.lock`: đường dẫn chính `/var/lib/php-quickpatch` (root) hoặc `$HOME/.php-quickpatch` (không root, `HOME` khác rỗng), chưa có thì `mkdir -m 0750`/`0700` không `-p`; kiểm bằng `lstat` (thư mục thật, không phải symlink; `st_uid` = `EUID`; `mode & 0022 = 0`); dự phòng `mktemp -d "${TMPDIR:-/tmp}/php-quickpatch-$EUID.XXXXXX"` chỉ cho người dùng không root (`FR-CLI-ENV-001`, `FR-CLI-COMP-001`, `CR-SRS-13`).
3. CLI lấy khoá chia sẻ `flock -s -n` trên `STATE_DIR/.lock` (`BR-JOB-002`).
4. CLI kiểm tra TTL từng nguồn trong bundle; nguồn quá TTL được đồng bộ trước, thời gian chờ tối đa 120 s, sau đó dùng bundle `current/` thay cho mảng ghi cứng `PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED` của v0.1 (`BR-FEED-001`, `NFR-FEED-002`, `FR-CLI-COMP-002`).
5. CLI nhận diện môi trường theo thuật toán 9 bước (container, panel, CloudLinux, LiteSpeed, distro, web server, Docker host, nguồn cài Node.js, `PB-000`), ghi `environment.evidence[]` (`FR-SCAN-ENV-001`), rồi áp giới hạn môi trường đặc biệt vào `environment.restrictions[]` (`FR-SCN-ENV-001`).
6. CLI phát hiện binary PHP (`FR-SCAN-RT-001`) và Node.js (`FR-SCAN-RT-002`) theo danh sách đường dẫn dò của v0.1 và biến `QP_PHP_BINS`/`QP_NODE_BINS`; đọc phiên bản mỗi binary với giới hạn 10 s (`BR-SCAN-002`); tính `runtime_id`.
7. CLI nạp catalog đã kiểm `SHA256SUMS` (`FR-SCN-CAT-001`), gán đúng 1 kịch bản `VERSION` và 0..n kịch bản `OVERLAY` cho mỗi runtime (`FR-SCN-CLS-001`, `FR-SCN-CLS-002`), tính `lifecycle_status`, `priority`, `days_to_eol`, `is_lts` tại thời điểm chạy (`FR-SCN-LIFE-001`).
8. Với binary thuộc gói distro, CLI xác định trạng thái vá từng CVE theo chuỗi advisory distro → tracker → changelog gói (`FR-FEED-DIST-001`, `FR-FEED-DIST-002`, `FR-FEED-NORM-003`) và gán `ok-backport` chỉ khi mọi CVE của nhánh là `FIXED`/`NOT_AFFECTED` (`BR-SEC-002`).
9. CLI đặt cờ `locked=true` cho runtime có `lifecycle_status` ∈ {`UNKNOWN`, `PRE_RELEASE`} (`FR-SCN-LOCK-001`, `BR-SCN-013`).
10. CLI kiểm kê site → runtime bằng lệnh liệt kê của từng playbook (`FR-SCAN-MAP-001`) và so với lượt chuyển `PASSED` gần nhất của từng site (`FR-SCAN-DRF-001`).
11. CLI kiểm kê dự án Composer/npm/WordPress/Docker (độ sâu 7 cấp, bỏ `node_modules`, `vendor`, `.git`, `.cache`, `.nvm`, `.npm`, `.composer`, không theo symlink — `FR-SCAN-PRJ-001`, `BR-SCAN-003`) và container đang chạy (`FR-SCAN-PRJ-002`); đánh giá dependency và WordPress theo UC-ASMT-002 khi `--only` có `composer`, `npm` hoặc `wp`.
12. CLI quét dấu hiệu webshell trên file `*.php` < 2 MB và file `*.ph*` trong `wp-content/uploads`, tối đa 50 kết quả mỗi nhóm, chỉ báo cáo (`FR-SCAN-WSH-001`).
13. CLI gắn tuổi dữ liệu vào kết quả (`FR-FEED-AGE-001`), in đầu ra văn bản định dạng v0.1 (`[OK]`, `[WARN]`, `[VULN]`, `[i]`, mục "Summary"); khi có `--json`, stdout chỉ chứa 1 envelope `qp.scan/1` và văn bản chuyển sang stderr và file log (`FR-CLI-JSON-001`); ghi `STATE_DIR/state/last-scan.json`.
14. CLI giải phóng khoá và thoát 0 hoặc 1 (`BR-CLI-004`); console chuyển job sang `SUCCEEDED`/`SUCCEEDED_WITH_ISSUES` (`BR-JOB-008`) và làm mới SCR-002, SCR-009.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. Tham số dòng lệnh không hợp lệ** (giá trị `--only` ngoài danh sách, tham số lạ):
  - 1a1. CLI in "Unknown or invalid argument: {arg}" kèm usage (`ERR-CLI-400-01`), thoát 2.
- **1b. Console nhận tham số ngoài danh sách trắng hoặc giá trị bắt đầu bằng `-`**:
  - 1b1. Console trả 422 `ERR-CON-422-01`, không tạo tiến trình (`FR-CON-SAFE-003`).
- **1c. Đã có job `scan` đang `QUEUED`/`RUNNING`, hoặc hàng đợi đủ 20 job**:
  - 1c1. Console trả `ERR-JOB-409-01` kèm `job_id` đang chạy, hoặc `ERR-JOB-429-01`; Operator theo dõi job hiện có ở SCR-006 (UC-JOB-001).
- **2a. Bash < 4.3 hoặc thiếu `flock`/`curl`**:
  - 2a1. CLI in `ERR-CLI-424-02`, thoát 2, không quét.
- **2b. Chạy không root**:
  - 2b1. CLI tiếp tục; cấu hình hệ thống không đọc được được ghi thành issue "needs root" như v0.1; hành động khả dụng giới hạn ở cấp dự án trong thư mục user sở hữu (`BR-PTCH-003`, `BR-CLI-005`).
- **2c. `STATE_DIR` không đạt kiểm tra spec §2.1** (đường dẫn chính là symlink, không phải thư mục thật, chủ sở hữu ≠ `EUID`, group/other có quyền ghi; root không tạo được `/var/lib/php-quickpatch`; không root `mktemp -d` dự phòng thất bại):
  - 2c1. CLI in "State directory {path} is unsafe ({reason}); aborting." với `reason` ∈ {`symlink`, `not_dir`, `owner`, `mode`, `create_failed`} (`ERR-CLI-412-01`), thoát 2 (`BR-CLI-004`).
  - 2c2. CLI đọc/ghi 0 file trong thư mục đó, không lấy khoá `STATE_DIR/.lock`, không chuyển sang dự phòng khi đường dẫn chính đã tồn tại nhưng không đạt; không quét.
  - 2c3. Khi chạy từ console: job chuyển `FAILED` với `ERR-JOB-500-01` (`BR-JOB-008`).
- **3a. Khoá `STATE_DIR/.lock` đang bị lượt ghi giữ**:
  - 3a1. CLI in "Another php-quickpatch run is in progress." (`ERR-CLI-423-01`), thoát 2.
  - 3a2. Job console ở `QUEUED`, thử lại mỗi 5 s; quá 30 phút → `FAILED` với `ERR-JOB-409-02` (`FR-JOB-RUN-002`).
- **4a. Có `--offline`**:
  - 4a1. CLI không gọi nguồn online, dùng `current/` rồi snapshot đóng gói; không gửi dữ liệu ra ngoài (`BR-FEED-013`).
- **4b. 1–15 nguồn không truy cập được sau 3 lần thử**:
  - 4b1. CLI ghi `ERR-FEED-503-01` cho nguồn đó, dùng chuỗi dự phòng (bản sao → cache → snapshot, `BR-FEED-006`), vẫn hoàn tất lượt quét (`BR-FEED-008`, `NFR-FEED-007`).
- **4c. Dữ liệu dùng cho kết quả cũ > 168 giờ (7 ngày)**:
  - 4c1. Mọi kết quả kèm cảnh báo `ERR-FEED-412-01` (`BR-DATA-001`).
  - 4c2. Cũ > 2.160 giờ (90 ngày): thêm `ERR-SCN-503-01`, tạm ngừng đề xuất nâng nhánh; chỉ vá cùng nhánh được đề xuất (`BR-FEED-005`).
- **4d. Không có bundle, snapshot không hợp lệ và không có mạng**:
  - 4d1. Snapshot lệch SHA-256 → `ERR-FEED-422-02`, không dùng snapshot.
  - 4d2. Mọi runtime nhận `UNKNOWN`, CLI ghi `ERR-FEED-503-01`, thoát 2.
- **4e. Không có Python ≥ 3.6**:
  - 4e1. CLI không chuẩn hoá feed (`ERR-FEED-424-01`, `BR-FEED-012`), dùng bundle sẵn có; lượt quét vẫn chạy (`NFR-CMP-005`).
- **5a. Không khớp playbook PHP nào (`PB-000`)**:
  - 5a1. CLI ghi `ERR-ENV-422-01`; runtime PHP chỉ được đề xuất mitigation và hướng dẫn thủ công.
- **5b. CLI chạy bên trong container (`/.dockerenv` hoặc cgroup)**:
  - 5b1. Đặt `in_container=1`; khoá cài song song, chuyển site, rollback site cho runtime trong container; đề xuất chạy PB-013 ở host (`BR-ENV-009`).
- **6a. Binary không trả phiên bản trong 10 s, hoặc chuỗi phiên bản bất thường** (major PHP = 6, vượt nhánh mới nhất, hậu tố lạ):
  - 6a1. Runtime nhận kịch bản `SCN-PHP-005`/`SCN-NODE-008`, `lifecycle_status=UNKNOWN`, CLI ghi `ERR-SCN-422-01` (`BR-SCN-001`); tiếp tục binary kế tiếp; bước 9 khoá runtime.
- **7a. Catalog trong snapshot sai `SHA256SUMS` hoặc schema**:
  - 7a1. CLI giữ catalog đang dùng, ghi `ERR-FEED-422-02` hoặc `ERR-FEED-502-02` (`FR-SCN-CAT-001`).
- **8a. Không đọc được changelog gói distro**:
  - 8a1. CVE được coi là `UNKNOWN`; runtime ở `vulnerable` kèm nhãn "chưa xác định", ưu tiên tính như chưa vá (`BR-SEC-002`, `BR-SCN-015`).
- **10a. Một site khớp ≥ 2 lớp gán và không xác định được cấu hình web server đang nạp**:
  - 10a1. CLI ghi `ERR-ENV-422-02`; site chỉ ở mức `MANUAL` (`BR-ENV-001`).
- **10b. Gán hiện tại của site khác lượt chuyển `PASSED` gần nhất**:
  - 10b1. CLI thêm `drift_warnings[]` và cảnh báo `ERR-SCAN-409-01`; SCR-009 hiển thị cảnh báo thay đổi ngoài tool.
- **11a. `docker info` trả mã ≠ 0**:
  - 11a1. CLI bỏ qua kiểm kê container, ghi dòng `[i]` vào kết quả.
- **11b. Dự án có `yarn.lock`/`pnpm-lock.yaml`**:
  - 11b1. CLI ghi cảnh báo kèm lệnh `yarn npm audit`/`pnpm audit` như v0.1 (không audit thay).
- **12a. Có ≥ 1 dấu hiệu webshell**:
  - 12a1. CLI ghi issue `critical` gồm đường dẫn, luật, SHA-256, `mtime`, kích thước; không xoá, sửa, đổi quyền hay di chuyển file (`BR-SEC-003`); lượt quét thoát 1.
- **14a. Job console vượt 1.800 s**:
  - 14a1. Job runner dừng tiến trình, job `FAILED` với `ERR-JOB-504-01` (`BR-JOB-008`).

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-PERF-004`: `scan` offline ≤ 60 s P95 với 4 PHP, 2 Node.js, 20 lockfile (chưa đo).
- `NFR-ENV-07`: nhận diện môi trường ≤ 5 s với ≤ 200 vhost.
- `NFR-FEED-002`: chờ đồng bộ tối đa 120 s; `NFR-FEED-007`: 100% lượt quét hoàn tất khi 1..15 nguồn lỗi.
- `NFR-CMP-001`: 100% test hồi quy hành vi v0.1 đạt; `NFR-CMP-004`: 100% đầu ra `--json` hợp lệ theo JSON Schema; `NFR-CMP-005`: chạy được khi không có Python 3.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-SCAN-001` | Quét chỉ đọc: 0 file ghi ngoài `STATE_DIR`, 0 dịch vụ restart, 0 gói cài | Toàn luồng |
| `BR-SCAN-002` | Tối đa 10 s cho mỗi lệnh đọc phiên bản binary/container | 6, 11 |
| `BR-SCAN-003` | Phạm vi tìm dự án: độ sâu 7, danh sách thư mục bỏ qua, không theo symlink | 11 |
| `BR-JOB-002` | Khoá chia sẻ cho lệnh đọc | 3 |
| `BR-FEED-001`, `BR-FEED-005`, `BR-FEED-006`, `BR-FEED-008`, `BR-FEED-012`, `BR-FEED-013`, `BR-DATA-001` | TTL, độ tươi, dự phòng, lỗi nguồn không chặn lượt chạy, chế độ chỉ đọc bundle, phạm vi dữ liệu gửi ra | 4 |
| `BR-ENV-001`, `BR-ENV-009` | Một site một playbook gán; giới hạn trong container | 5, 10 |
| `BR-SCN-001`, `BR-SCN-003`, `BR-SCN-013`, `BR-SCN-020`, `BR-SCN-040` | Gán kịch bản, tính trạng thái hỗ trợ, khoá phiên bản bất thường | 7, 9 |
| `BR-SEC-002`, `BR-SCN-015` | Điều kiện `ok-backport`, CVE với gói distro | 8 |
| `BR-SEC-003` | Không xoá webshell | 12 |
| `BR-CLI-001`, `BR-CLI-002`, `BR-CLI-004`, `BR-CLI-005`, `BR-PTCH-003` | Schema JSON, tương thích v0.1, mã thoát, quyền chạy | 2, 13, 14 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-CLI-COMP-001` | Giữ tương thích ngược v0.1 | 2, 13 |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | 4 |
| `FR-SCAN-ENV-001` | Nhận diện môi trường và chọn playbook | 5 |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | 5 |
| `FR-SCAN-RT-001` | Phát hiện runtime PHP | 6 |
| `FR-SCAN-RT-002` | Phát hiện runtime Node.js | 6 |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | 7 |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | 7 |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | 7 |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | 7 |
| `FR-FEED-DIST-001` | Tra advisory distro cho gói runtime | 8 |
| `FR-FEED-DIST-002` | Dự phòng tracker distro và changelog | 8 |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | 8 |
| `FR-SCN-LOCK-001` | Khoá tự động hoá với phiên bản bất thường | 9 |
| `FR-SCAN-MAP-001` | Kiểm kê site → runtime | 10 |
| `FR-SCAN-DRF-001` | Phát hiện gán site bị đổi ngoài tool | 10 |
| `FR-SCAN-PRJ-001` | Kiểm kê dự án | 11 |
| `FR-SCAN-PRJ-002` | Kiểm kê container đang chạy | 11 |
| `FR-SCAN-WSH-001` | Phát hiện dấu hiệu webshell (chỉ báo cáo) | 12 |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | 13 |
| `FR-CLI-JSON-001` | Xuất envelope `--json` có schema phiên bản | 13 |

### Giao diện và API liên quan
- Màn hình: `SCR-002` Tổng quan (nút "Quét lại"), `SCR-009` Site & ánh xạ runtime.
- API: `POST /api/v1/jobs` (`action=scan`), `GET /api/v1/environment`, `GET /api/v1/runtimes`, `GET /api/v1/runtimes/{runtime_id}`, `GET /api/v1/sites`, `GET /api/v1/projects`, `GET /api/v1/containers`, `GET /api/v1/webshell-findings`.

### Quan hệ với use case khác
- `<<include>>` UC-ASMT-002 (đánh giá dependency/WordPress ở bước 11 khi `--only` có `composer`, `npm`, `wp`).
- Được gọi trước bởi UC-ASMT-001 khi kết quả scan cũ > 24 giờ; kết quả là đầu vào của UC-CON-002, UC-PLAN-001, UC-PTCH-001.
- Khi chạy từ console: `<<include>>` UC-JOB-001 (theo dõi job và log).

### Ghi chú và tài liệu tham chiếu
- Hành vi kế thừa đã kiểm chứng trên `/home/user/php-quickpatch/php-quickpatch.sh` v0.1.0 (881 dòng, đọc ngày 2026-10-22): `STATE_DIR` (dòng 851–852), thông điệp khoá "Another php-quickpatch run is in progress." và thoát 2 (dòng 857).
- Thay đổi hành vi so với v0.1: v0.1 lấy khoá độc quyền cho mọi lệnh; v2 dùng khoá chia sẻ cho `scan` (`CR-SRS-06`, spec §4.3).
- Thay đổi hành vi so với v0.1 về `STATE_DIR` (`CR-SRS-13`, thêm ở spec.md 1.0.1, hiện hành 1.1.0): v0.1 dòng 851–852 dùng `mkdir -p` với dự phòng `${TMPDIR:-/tmp}/php-quickpatch-$EUID` cho cả root và không kiểm chủ sở hữu/symlink; v2 áp 5 bước kiểm tra của spec §2.1 (bước 2 và nhánh 2c), root không còn dự phòng. Đây là ngoại lệ tương thích được ghi trong `FR-CLI-COMP-001`.
- Nguồn: [spec.md §2.1, §3.3.2, §3.5, §4.1.4](../srs/spec.md), [error-matrix.md §3.5 `ERR-CLI-412-01`](../srs/error-matrix.md), [functional-requirements.md §2, §3](../srs/functional-requirements.md), [environment-playbooks.md §2.3](../srs/environment-playbooks.md), [data-sources-cache-cli.md §3.5, §4.5](../srs/data-sources-cache-cli.md), [flows.md §3](../srs/flows.md).
