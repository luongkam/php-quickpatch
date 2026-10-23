---
id: DOC-SRS-QP-SCN-NODE-001
title: Phụ lục đặc tả — Danh mục kịch bản theo phiên bản Node.js (SCN-NODE-001..012)
version: 1.0.1
phase: Specification
domain: Security Patch Management
tags: [srs, appendix, scenario, checklist, nodejs, lts, upgrade, native-addon, openssl, npm, systemd, pm2]
depends_on:
  - DOC-BRS-QP-001
  - DOC-PRD-QP-001
  - DOC-SRS-QP-SCN-000
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Phụ lục đặc tả — Danh mục kịch bản theo phiên bản Node.js

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo danh mục kịch bản Node.js: bảng tổng hợp 12 kịch bản, dữ liệu vòng đời kiểm chứng ngày 2026-10-22, BR-SCN-020..030, danh mục breaking change, bảng ABI, cơ chế restart systemd/pm2, biến thể nguồn cài, checklist SCN-NODE-001..012 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: §4 thêm cột "Phạm vi áp dụng (Module / Kênh / Actor)" sau "Tên quy tắc" cho 11 quy tắc `BR-SCN-020..030` theo rule 02 §2 và business-rules.md §6 mục 1 (thay phạm vi mặc định ở business-rules.md §2), thêm đoạn quy ước cột ở đầu §4; §12 thêm nguồn business-rules.md và spec.md. Không đổi nội dung KHI/THÌ/NGOẠI LỆ |

## 1. Giới thiệu (Introduction)

### 1.1 Mục đích tài liệu (Purpose)
Tài liệu là dữ liệu nghiệp vụ cho tính năng "kịch bản + checklist" (FEAT-021, FEAT-022 trong `DOC-PRD-QP-001`) đối với runtime Node.js: trạng thái hỗ trợ, có phải LTS không, nhánh đích, breaking change phải quét, tác động tới native addon / npm / OpenSSL / ESM, cách restart (systemd, pm2) và checklist từ chuẩn bị đến dọn dẹp. Quy ước chung (trạng thái `CURRENT`/`ACTIVE_LTS`/`MAINTENANCE_LTS`/`EOL`, mức ưu tiên, giai đoạn P1..P7, loại mục, BR-SCN-001..018, ERR-SCN) nằm ở [version-scenarios-common.md](version-scenarios-common.md).

### 1.2 Phạm vi (Scope)
- **Trong phạm vi**: mọi binary Node.js tool phát hiện (kế thừa `discover_node_bins` v0.1: `/usr/bin/node`, `/usr/local/bin/node`, `/opt/*/bin/node`, aaPanel `/www/server/nodejs/*`, nvm của root và `/home/*`), mọi ứng dụng chạy bằng binary đó qua systemd hoặc pm2, image `node:` trong Dockerfile/compose.
- **Ngoài phạm vi**: sửa mã ứng dụng trên production; audit `yarn.lock`/`pnpm-lock.yaml` (giữ hành vi v0.1: chỉ cảnh báo); Windows (DOC-BRS-QP-001 §5.2); build/deploy image Docker.

### 1.3 Định nghĩa bổ sung (Definitions)
| Ký hiệu / thuật ngữ | Định nghĩa |
| :--- | :--- |
| `$OLD_PREFIX`, `$NEW_PREFIX` | Thư mục gốc cài Node.js (`$PREFIX/bin/node`); bản cài song song dùng `/opt/node-v<ver>-linux-<arch>` và liên kết `/opt/node-<major>` |
| `$APP` | Tên unit systemd hoặc tên tiến trình pm2 của ứng dụng |
| `$APPDIR`, `$COPY` | Thư mục ứng dụng (có `package.json`); bản sao trên staging dùng để cài dependency thử |
| NODE_MODULE_VERSION (ABI) | Số phiên bản ABI của native addon; khác số → addon phải build lại |
| Native addon | Gói có file `*.node`, `binding.gyp`, `"gypfile": true`, hoặc script cài dùng `node-gyp`/`prebuild-install`/`node-pre-gyp`/`node-gyp-build` |
| Drop-in systemd | File `/etc/systemd/system/$APP.service.d/zz-php-quickpatch-node.conf` do tool tạo để đổi `ExecStart` mà không sửa unit gốc |

### 1.4 Tài liệu tham chiếu (References)
Xem §12.

## 2. Bảng tổng hợp kịch bản Node.js
Ảnh chụp ngày 2026-10-22 (UTC); tool tính lại trạng thái theo BR-SCN-003. Đích theo BR-SCN-006; trong ngoặc là đích thay thế.

| Mã kịch bản | Loại | Dải phiên bản | Trạng thái (2026-10-22) | LTS? | EOL | Bản cuối / mới nhất | Đích khuyến nghị | Ưu tiên | Số mục checklist | Vị trí |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| `SCN-NODE-001` | VERSION | ≤ 16 (gồm 0.x, io.js 1–3, các dòng lẻ ≤ 15) | `EOL` (16 quá 1.137 ngày) | 16, 14, 12, 10… có; dòng lẻ không | 16: 2023-09-11 | 16.20.2 | 26 từ 2026-10-28 (24) | Nghiêm trọng | 32 | §10.1 |
| `SCN-NODE-002` | VERSION | 18 | `EOL` (quá 540 ngày) | Có (Hydrogen) | 2025-04-30 | 18.20.8 | 26 (24) | Nghiêm trọng | 31 | §10.2 |
| `SCN-NODE-003` | VERSION | 20 | `EOL` (quá 175 ngày) | Có (Iron) | 2026-04-30 | 20.20.2 (2026-03-24) | 26 (24) | Cao | 31 | §10.3 |
| `SCN-NODE-004` | VERSION | Dòng lẻ 17, 19, 21, 23, 25 | `EOL` (25 quá 143 ngày; 23 quá 508 ngày) | Không | 17: 2022-06-01; 19: 2023-06-01; 21: 2024-06-01; 23: 2025-06-01; 25: 2026-06-01 | 17.9.1 / 19.9.0 / 21.7.3 / 23.11.1 / 25.9.0 | 26 (24) | Nghiêm trọng (25: Cao) | 32 | §10.4 |
| `SCN-NODE-005` | VERSION | 22 | `MAINTENANCE_LTS` từ 2025-10-21; còn 190 ngày | Có (Jod) | 2027-04-30 | 22.23.4 (2026-10-20, `security`) | Vá 22.23.4; nâng 26 (24) trước 2027-03-31 | Trung bình (Cao khi chưa vá) | 15 | §10.5 |
| `SCN-NODE-006` | VERSION | 24 | `MAINTENANCE_LTS` từ 2026-10-20; còn 556 ngày | Có (Krypton) | 2028-04-30 | 24.22.1 (2026-10-20, `security`) | Vá 24.22.1; giữ nhánh | Trung bình (Cao khi chưa vá) | 15 | §10.6 |
| `SCN-NODE-007` | VERSION | 26 | `CURRENT` → `ACTIVE_LTS` ngày 2026-10-28 | Có từ 2026-10-28 | 2029-04-30 | 26.12.1 (2026-10-21, `security`) | Vá 26.12.1; giữ nhánh | Thấp (Cao khi chưa vá) | 11 | §10.7 |
| `SCN-NODE-008` | VERSION | Pre-release (`-nightly`, `-rc.N`, `-pre`, 27 alpha) và chuỗi bất thường | `PRE_RELEASE` / `UNKNOWN` | Không | — | 27 alpha dự kiến 2026-10-28 | Không đề xuất tự động; hạ về 26/24 cho production | Nghiêm trọng nếu phục vụ ứng dụng công khai | 12 | §10.8 |
| `SCN-NODE-009` | OVERLAY | Cài qua nvm | Theo nhánh | — | — | — | Như kịch bản VERSION | Theo nhánh | 11 | §10.9 |
| `SCN-NODE-010` | OVERLAY | Cài từ tarball (prefix không thuộc gói) | Theo nhánh | — | — | — | Như kịch bản VERSION | Theo nhánh | 11 | §10.10 |
| `SCN-NODE-011` | OVERLAY | Gói NodeSource (`deb.nodesource.com`/`rpm.nodesource.com`) | Theo nhánh | — | — | — | Như kịch bản VERSION | Theo nhánh | 11 | §10.11 |
| `SCN-NODE-012` | OVERLAY | Gói distro (Debian/Ubuntu `nodejs`, RHEL AppStream, Alpine) | Theo nhánh + tracker distro | — | Theo OS | Theo changelog gói | Như kịch bản VERSION | Theo BR-SCN-015 | 12 | §10.12 |

**Tổng**: 8 kịch bản `VERSION`, 4 kịch bản `OVERLAY`, 224 mục checklist.

> **Đối chiếu yêu cầu đầu vào**: yêu cầu ghi "24 (active LTS)". Lịch chính thức (`nodejs/Release/schedule.json`) ghi `v24.maintenance = 2026-10-20` và endoflife.date ghi `support = 2026-10-20` → từ 2026-10-20 Node.js 24 ở pha **Maintenance LTS** (common §7 mục 3). Node.js 26 vào LTS ngày 2026-10-28 (khớp yêu cầu).

## 3. Dữ liệu vòng đời Node.js đã kiểm chứng (2026-10-22)
Nguồn ưu tiên (BR-SCN-002): `https://raw.githubusercontent.com/nodejs/Release/main/schedule.json` và chỉ mục bản phát hành `https://nodejs.org/download/release/index.json`; sau đó `https://endoflife.date/api/nodejs.json`.

| Dòng | GA | Vào LTS | Vào Maintenance | EOL | Bản mới nhất (ngày) | npm kèm theo | OpenSSL | ABI |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| 14 | 2020-04-21 | 2020-10-27 | 2021-10-19 | 2023-04-30 | 14.21.3 (2023-02-16) | 6.14.18 | 1.1.1t | 83 |
| 16 | 2021-04-20 | 2021-10-26 | 2022-10-18 | 2023-09-11 | 16.20.2 (2023-08-08) | 8.19.4 | 1.1.1v | 93 |
| 17 | 2021-10-19 | — | 2022-04-01 | 2022-06-01 | 17.9.1 (2022-06-01) | 8.11.0 | 3.0.3 | 102 |
| 18 | 2022-04-19 | 2022-10-25 | 2023-10-18 | 2025-04-30 | 18.20.8 (2025-03-27) | 10.8.2 | 3.0.16 | 108 |
| 19 | 2022-10-18 | — | 2023-04-01 | 2023-06-01 | 19.9.0 (2023-04-10) | 9.6.3 | 3.0.8 | 111 |
| 20 | 2023-04-18 | 2023-10-24 | 2024-10-22 | 2026-04-30 | 20.20.2 (2026-03-24) | 10.8.2 | 3.0.19 | 115 |
| 21 | 2023-10-17 | — | 2024-04-01 | 2024-06-01 | 21.7.3 (2024-04-10) | 10.5.0 | 3.0.13 | 120 |
| 22 | 2024-04-24 | 2024-10-29 | 2025-10-21 | 2027-04-30 | 22.23.4 (2026-10-20, `security`) | 10.9.9 | 3.5.9 | 127 |
| 23 | 2024-10-16 | — | 2025-04-01 | 2025-06-01 | 23.11.1 (2025-05-14) | 10.9.2 | 3.0.16 | 131 |
| 24 | 2025-05-06 | 2025-10-28 | 2026-10-20 | 2028-04-30 | 24.22.1 (2026-10-20, `security`) | 11.19.1 | 3.5.9 | 137 |
| 25 | 2025-10-15 | — | 2026-04-01 | 2026-06-01 | 25.9.0 (2026-03-31) | 11.12.1 | 3.5.5 | 141 |
| 26 | 2026-05-05 | 2026-10-28 | 2027-10-20 (endoflife.date: 2027-10-27) | 2029-04-30 | 26.12.1 (2026-10-21, `security`) | 11.20.0 | 3.5.9 | 147 |
| 27 | Alpha 2026-10-28; GA dự kiến 2027-04-22 | Dự kiến 2027-10-20 | — | Dự kiến 2030-04-30 | — | — | — | — |

Ghi chú: (1) ngày `latestReleaseDate` của dòng 24 trên endoflife.date là 2026-10-21, chỉ mục phát hành ghi 2026-10-20 → dùng chỉ mục phát hành; (2) từ dòng 27, Node.js đổi lịch phát hành (bài "Evolving the Node.js Release Schedule"), không còn dòng lẻ (common §7 mục 4); (3) dòng 0.x không có trong endoflife.date → bản ghi tĩnh trong snapshot (FEAT-010).

Hệ quả cho BR-SCN-006 tại 2026-10-22 (hôm nay + 14 ngày = 2026-11-05; hôm nay + 365 ngày = 2027-10-22): 26 thoả (a) `lts` 2026-10-28 và (b) EOL 2029-04-30 → đích mặc định, nhưng chỉ được chuyển ứng dụng production từ 2026-10-28 (BR-SCN-007); 24 thoả (a)(b) → đích thay thế; 22 không thoả (b).

## 4. Quy tắc nghiệp vụ riêng Node.js (BR-SCN-020..030)
Mỗi BR gồm Tên quy tắc, Phạm vi áp dụng, KHI → THÌ → NGOẠI LỆ (rule 02 §2). Cột "Phạm vi áp dụng" theo mẫu `Module / Kênh / Actor` của [business-rules.md §1](business-rules.md) và quy ước ở [version-scenarios-common.md §4](version-scenarios-common.md): Module là mã module FR; Kênh ∈ {CLI (lệnh con theo [spec.md §3.3.2](spec.md)), console (`SCR-*`), API (`/api/v1`, hành động job theo [spec.md §3.3.4](spec.md))}; Actor theo [spec.md §2.3](spec.md). Cột này thay phạm vi mặc định của dải `BR-SCN-020..030` ở [business-rules.md §2](business-rules.md).

| Mã BR | Tên quy tắc | Phạm vi áp dụng (Module / Kênh / Actor) | KHI (WHEN) | THÌ (THEN) | NGOẠI LỆ (UNLESS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BR-SCN-020` | Gán kịch bản Node.js | SCN, SCAN (Node.js) / CLI (`scan`, `assess`), console SCR-002, SCR-003 (job `scan`), API (`GET /api/v1/runtimes`, `GET /api/v1/runtimes/{runtime_id}`) / PER-01, PER-03 | Đọc được `$BIN --version` (dạng `v24.22.1`) trong ≤ 10 s | Thứ tự: (1) hậu tố `-nightly`, `-rc.`, `-pre`, `-alpha`, hoặc dòng có `alpha`/`start` trong tương lai ở `schedule.json` → SCN-NODE-008 (`PRE_RELEASE`); chuỗi không khớp `^v\d+\.\d+\.\d+` hoặc major lớn hơn dòng mới nhất trong dữ liệu → SCN-NODE-008 (`UNKNOWN`); (2) major ≤ 16 → 001; 18 → 002; 20 → 003; lẻ 17–25 → 004; 22 → 005; 24 → 006; 26 → 007. Overlay: đường dẫn `*/.nvm/versions/node/*` → 009; không có gói sở hữu và `$PREFIX/lib/node_modules/npm` tồn tại → 010; gói sở hữu có nguồn `deb.nodesource.com`/`rpm.nodesource.com` → 011; gói sở hữu khác → 012 | Biến `QP_NODE_BINS` (v0.1) vẫn áp quy tắc trên |
| `BR-SCN-021` | Dải breaking change | CMPT, PLAN (Node.js) / CLI (`plan create`, `plan run`), console SCR-004, API (`POST /api/v1/plans`, `GET /api/v1/plans/{plan_id}/compatibility`) / PER-01, PER-03 | Nâng từ `$OLD` lên `$NEW` | Tập luật = mọi mục BC-NODE ở §5 có dòng `m` thoả `$OLD < m ≤ $NEW`, gồm cả dòng lẻ nằm giữa (thay đổi semver-major của dòng lẻ được mang sang dòng chẵn kế tiếp) | — |
| `BR-SCN-022` | Native addon | ASMT, CMPT, PLAN, UPG (Node.js) / CLI (`assess`, `plan create`, `plan run`, `migrate switch`), console SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01, PER-03 | Đổi major | Liệt kê addon (định nghĩa §1.3) của mỗi ứng dụng; sau khi cài dependency bằng `$NEW_BIN`, mỗi addon phải nạp được: `$NEW_BIN -e "require('<pkg>')"` (gói CommonJS) hoặc `$NEW_BIN --input-type=module -e "await import('<pkg>')"` (gói ESM) trả exit 0 | Addon chỉ dùng trong script build, không nạp lúc chạy → kiểm bằng `npm run build` |
| `BR-SCN-023` | OpenSSL 3 | CMPT, PLAN, UPG (Node.js) / CLI (`plan run`, `migrate switch`), console SCR-004, SCR-006, API (`POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01, PER-03 | `$OLD` ≤ 16 và `$NEW` ≥ 17 | Chạy build/test/khởi động thử bằng `$NEW_BIN`; 0 dòng `ERR_OSSL_EVP_UNSUPPORTED` trong log. Cờ `--openssl-legacy-provider` chỉ được dùng tạm khi có duyệt, hạn ≤ 30 ngày, ghi vào manifest để gỡ ở P7 | — |
| `BR-SCN-024` | npm và lockfile | CMPT, PLAN, UPG (Node.js) / CLI (`plan run`, `migrate switch`), console SCR-004, SCR-011, API (`POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01, PER-03 | npm của `$NEW` khác major npm của `$OLD` | `lockfileVersion` 1 (npm 5/6) phải được tái tạo trên `$COPY` bằng npm của `$NEW` (`npm install --package-lock-only`), duyệt diff, rồi `npm ci` exit 0. `lockfileVersion` 2/3 dùng trực tiếp `npm ci`. Mọi lệnh chạy dưới quyền chủ thư mục (v0.1 `run_in_dir_as_owner`) | Dự án dùng `yarn.lock`/`pnpm-lock.yaml`: giữ hành vi v0.1, chỉ cảnh báo và hướng dẫn |
| `BR-SCN-025` | Ràng buộc `engines.node` | ASMT, CMPT, PLAN (Node.js) / CLI (`assess`, `plan create`, `plan run`), console SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`) / PER-01, PER-03 | Chọn đích hoặc chạy P3 | `engines.node` của ứng dụng và của mọi gói trong lockfile (thiếu thì tra npm registry) phải chấp nhận phiên bản patch của `$NEW` theo semver; gói vi phạm đưa vào danh sách nâng (P4) | Gói chỉ dùng ở `devDependencies` không chạy trên production → cảnh báo |
| `BR-SCN-026` | Cài song song Node.js | UPG (cài song song, Node.js) / CLI (`migrate install --runtime node`, `plan run`), console SCR-004, SCR-011, API (`POST /api/v1/jobs` hành động `migrate_install`) / PER-01, PER-03, SYS-03 | Cài `$NEW` cạnh `$OLD` | Không ghi đè prefix hoặc gói đang được unit/pm2 dùng (BR-SCN-012). Gói NodeSource và gói distro chỉ có 1 gói `nodejs` cho mỗi hệ thống → `$NEW` cài bằng tarball (E1) hoặc nvm (E2); tarball tải từ nodejs.org và kiểm `SHASUMS256.txt` (kế thừa `node_upgrade_prefix`) | Docker (E6): cài song song = container mới |
| `BR-SCN-027` | Chuyển ứng dụng và restart | UPG (chuyển, hoàn tác, Node.js) / CLI (`migrate switch`, `migrate rollback`, `plan run`), console SCR-004, SCR-007, SCR-011, API (`POST /api/v1/jobs` hành động `migrate_switch`, `POST /api/v1/rollbacks`) / PER-01, PER-03, SYS-03 | Chuyển 1 ứng dụng sang `$NEW` | systemd: tạo drop-in đặt lại `ExecStart=` rỗng rồi `ExecStart=` mới trỏ `$NEW_BIN`, `systemctl daemon-reload`, `systemctl restart $APP`; pm2: đặt `interpreter: $NEW_BIN` trong ecosystem, `pm2 delete $APP`, `pm2 start <ecosystem> --only $APP`, `pm2 save`. Ghi manifest `created` (drop-in) hoặc `copy` (ecosystem) trước khi sửa | Ứng dụng chạy bằng supervisor khác → mục `Thủ công` |
| `BR-SCN-028` | glibc và nền tảng | PLAN, UPG (Node.js) / CLI (`plan create`, `plan run`, `migrate install --runtime node`), console SCR-004, SCR-011 / PER-01, PER-03, SYS-03 | Trước P2 khi dùng binary chính thức | Binary Linux chính thức từ Node.js 18 được build trên RHEL 8, tương thích glibc ≥ 2.28 (thông báo phát hành 18). Kiểm `ldd --version` và chạy thử `$NEW_BIN --version` sau giải nén; lỗi `GLIBC_` hoặc exit ≠ 0 → `ERR-SCN-412-03`. Yêu cầu glibc cụ thể của 24/26: chưa kiểm chứng, phép chạy thử là tiêu chí | Gói distro/NodeSource build cho chính OS → không áp dụng kiểm glibc |
| `BR-SCN-029` | Hạn duyệt kế hoạch nâng major | PLAN (Node.js) / CLI (`plan create`, `plan approve`), console SCR-002, SCR-004, API (`GET /api/v1/overview`, `GET /api/v1/plans/{plan_id}`) / PER-01, PER-03; PER-04 chỉ xem cảnh báo | Dòng ở `MAINTENANCE_LTS` hoặc còn ≤ 90 ngày tới EOL | Kế hoạch nâng major phải `approved` trước EOL − 30 ngày (22: trước 2027-03-31; 24: trước 2028-03-31); cảnh báo trên Tổng quan từ EOL − 90 ngày | — |
| `BR-SCN-030` | Bắt buộc staging và tệp ghim phiên bản | PLAN, UPG (Node.js) / CLI (`plan create`, `plan run`, `plan item --set waive`), console SCR-004, API (`PATCH /api/v1/plans/{plan_id}/checklist-items/{chk_id}`) / PER-01, PER-03 | `$OLD` ≤ 16, hoặc `$OLD` là dòng lẻ, hoặc khoảng cách ≥ 2 dòng LTS | P3, P4 chạy trên staging; P7 cập nhật `.nvmrc`, `.node-version`, `engines.node`, `FROM node:` trong Dockerfile/compose, phiên bản Node trong CI | Khoảng cách 1 dòng LTS (vd 24 → 26): staging khuyến nghị, được miễn trừ có duyệt |

## 5. Danh mục breaking change (BC-NODE)
"Runtime" = phát hiện bằng chạy thử/test/log; "Tĩnh" = mẫu quét trong mã của ứng dụng (không quét thư mục dependency). Nguồn: bài phát hành chính thức trên nodejs.org (§12).

| Mã BC | Dòng | Thay đổi | Loại | Cách phát hiện | Xử lý |
| :--- | :---: | :--- | :--- | :--- | :--- |
| `BC-NODE-17-01` | 17 | OpenSSL 3.0 (quictls); siết thuật toán và kích thước khoá → lỗi `ERR_OSSL_EVP_UNSUPPORTED`; thêm cờ tạm `--openssl-legacy-provider` | Đổi hành vi | Runtime: grep `ERR_OSSL_EVP_UNSUPPORTED` | Nâng thư viện dùng thuật toán cũ (BR-SCN-023) |
| `BC-NODE-18-01` | 18 | `fetch` toàn cục (thử nghiệm, từ undici) bật mặc định; binary Linux chính thức cần glibc ≥ 2.28; ABI 108 | Đổi hành vi / Nền tảng | Tĩnh: `global\.fetch\s*=`, `globalThis\.fetch\s*=`; `ldd --version` | Bỏ polyfill ghi đè hoặc giữ có kiểm thử; BR-SCN-028 |
| `BC-NODE-19-01` | 19 | ABI 111; npm 9 (cuối dòng) | ABI | Danh sách addon | Build lại addon |
| `BC-NODE-20-01` | 20 | `url.parse()` phát cảnh báo với cổng không phải số; `new WASI()` bắt buộc `version`; Permission Model thử nghiệm (`--experimental-permission`); test runner ổn định; ABI 115 | Đổi hành vi | Tĩnh: `url\.parse\(`, `new WASI\(` | WHATWG `URL`; truyền `version` |
| `BC-NODE-21-01` | 21 | `fetch`, WebStreams, `FormData`, `Headers`, `Request`, `Response` ổn định; WebSocket thử nghiệm sau cờ; ABI 120 | Đổi hành vi | Runtime | Kiểm thử gọi HTTP ra ngoài |
| `BC-NODE-22-01` | 22 | WebSocket bật mặc định; bỏ import assertions; `crypto.createCipher`/`createDecipher` EOL; runtime-deprecated `util.is*`, constructor `fs.Stats`; tăng `highWaterMark` mặc định của stream; `require(esm)` (sau cờ ở 22.0, bỏ cờ từ 22.12.0); ABI 127 | Xoá / Đổi hành vi | Tĩnh: `assert\s*\{\s*type`, `createCipher\(`, `createDecipher\(`, `util\.is[A-Z]` | Cú pháp `with { type: 'json' }`; `createCipheriv()` |
| `BC-NODE-23-01` | 23 | `require(esm)` bật mặc định: không còn `ERR_REQUIRE_ESM`, có thể ném `ERR_REQUIRE_ASYNC_MODULE` khi ESM dùng top-level `await`; xoá `process.assert`, `zlib.bytesRead`, cờ `--no-experimental-fetch`, `--no-experimental-global-webcrypto`, `--no-experimental-global-customevent`; `util.isBoolean`/`isBuffer`/`isDate`/`isError`… EOL; build yêu cầu C++20, cảnh báo GCC < 12.2; ABI 131 | Xoá / Đổi hành vi | Tĩnh: `process\.assert\(`, `bytesRead`; cờ trong `NODE_OPTIONS`, unit, ecosystem | Thay API; bỏ cờ đã xoá; `--no-experimental-require-module` để tắt tạm |
| `BC-NODE-24-01` | 24 | npm 11; Undici 7; `AsyncLocalStorage` dùng `AsyncContextFrame`; `URLPattern` toàn cục; `--experimental-permission` đổi thành `--permission`; `url.parse()` runtime-deprecated; xoá `tls.createSecurePair`, `dirent.path`, `truncate` với fd; runtime-deprecated `SlowBuffer`, `fs.F_OK`/`R_OK`/`W_OK`/`X_OK`; macOS tối thiểu 13.5; ABI 137 | Xoá / Đổi hành vi | Tĩnh: `createSecurePair`, `\.path\b` trên `Dirent`, `SlowBuffer`, `fs\.[FRWX]_OK`; cờ `--experimental-permission` | `fs.constants.*`, `Buffer.allocUnsafeSlow()`, `dirent.parentPath` |
| `BC-NODE-25-01` | 25 | `SlowBuffer` EOL; xoá `fs.F_OK`, `fs.R_OK`, `fs.W_OK`, `fs.X_OK`; Web Storage bật mặc định; ngừng phân phối Corepack; permission model thêm `--allow-net`; build cần Clang ≥ 19; ABI 141 | Xoá | Như BC-NODE-24-01; trường `packageManager` trong `package.json` | Cài Corepack riêng (`npm install -g corepack`, bản 0.36.0 yêu cầu `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0`) |
| `BC-NODE-26-01` | 26 | Temporal bật mặc định; V8 14.6; Undici 8.0.2; xoá `http.Server.prototype.writeHeader()`, module `_stream_wrap`/`_stream_readable`/`_stream_writable`/`_stream_duplex`/`_stream_transform`/`_stream_passthrough`, cờ `--experimental-transform-types`; `module.register()` runtime-deprecated; DEP0182 EOL; `localStorage` trả `undefined` khi không có file; build cần GCC ≥ 13.2, bỏ Python 3.9; ABI 147 | Xoá / Đổi hành vi | Tĩnh: `writeHeader\(`, `require\(['"]_stream_`, `module\.register\(`; cờ `--experimental-transform-types` | `writeHead()`; `require('stream')`; thay `module.register()` theo hướng dẫn deprecation của Node.js 26 (API thay thế chưa kiểm chứng trong phiên này) |

## 6. Native addon, npm và toolchain

### 6.1 Bảng ABI và npm theo dòng
| Dòng | 14 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| NODE_MODULE_VERSION | 83 | 93 | 102 | 108 | 111 | 115 | 120 | 127 | 131 | 137 | 141 | 147 |
| npm của bản mới nhất | 6.14.18 | 8.19.4 | 8.11.0 | 10.8.2 | 9.6.3 | 10.8.2 | 10.5.0 | 10.9.9 | 10.9.2 | 11.19.1 | 11.12.1 | 11.20.0 |
| `lockfileVersion` npm ghi | 1 | 2 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |

`lockfileVersion`: 1 = npm 5/6; 2 = npm 7/8 (tương thích ngược v1); 3 = npm 9 trở lên (tương thích npm 7) — theo tài liệu `package-lock.json` của npm.

### 6.2 Công cụ phụ trợ (npm registry, 2026-10-22)
| Gói | Bản | `engines.node` | Ảnh hưởng |
| :--- | :--- | :--- | :--- |
| `node-gyp` | 13.1.0 | `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` | Build lại addon trên đích 24/26 dùng được bản mới nhất; trên 22 cần ≥ 22.22.2 |
| `corepack` | 0.36.0 | `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` | Cần cài riêng từ Node.js 25 (BC-NODE-25-01) |
| `pm2` | 7.1.0 | `>=18.0.0` | Daemon pm2 bản mới nhất không chạy trên Node ≤ 16 → chuyển daemon sang `$NEW` (mục P6) |

## 7. Cơ chế restart (kế thừa và mở rộng v0.1)
| Cơ chế | v0.1 | v2 khi vá cùng major | v2 khi chuyển ứng dụng sang major mới | Hoàn tác |
| :--- | :--- | :--- | :--- | :--- |
| systemd | `restart_node_services`: tìm unit trong `/etc/systemd/system/*.service` có `ExecStart` chứa `${prefix}/bin/(node\|npm)` hoặc `pm2`, `systemctl restart` unit đang chạy | Giữ nguyên | Drop-in theo BR-SCN-027; kiểm `systemctl show -p NRestarts,ActiveState $APP` và `readlink /proc/<MainPID>/exe` = `$NEW_BIN` | Xoá drop-in (manifest `created`), `daemon-reload`, `restart` |
| pm2 | `pm2 reload all` khi `pm2 pid` chạy | Giữ nguyên | Ecosystem `interpreter: $NEW_BIN` + `pm2 delete`/`pm2 start --only`/`pm2 save`; sau khi mọi ứng dụng đã chuyển: cài pm2 dưới `$NEW`, `pm2 update`, rồi `pm2 unstartup` + `pm2 startup` để script khởi động dùng Node mới (tài liệu pm2), `pm2 save` | Khôi phục ecosystem (manifest `copy`), lặp lại lệnh |
| Không có | Cảnh báo "restart your Node.js apps by hand" | Giữ nguyên | Mục `Thủ công` | Mục `Thủ công` |

## 8. Biến thể thực thi theo môi trường
Hành động: **A1** cài `$NEW` song song; **A2** chuyển 1 ứng dụng; **A3** hoàn tác 1 ứng dụng; **A4** gỡ `$OLD`.

| Mã | Nguồn cài / môi trường | A1 | A2 | A3 | A4 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| E1 | Tarball nodejs.org (kế thừa `node_upgrade_prefix`) | Tải `node-v<ver>-linux-<arch>.tar.xz` + `SHASUMS256.txt`, `sha256sum -c`, giải nén vào `/opt/node-v<ver>-linux-<arch>`, liên kết `/opt/node-<major>`; kiến trúc theo v0.1 (`x64`, `arm64`, `armv7l`, `ppc64le`, `s390x`) | BR-SCN-027 | BR-SCN-027 | `tar -czf` prefix cũ vào backup rồi xoá |
| E2 | nvm (v0.40.8) của từng người dùng | Chạy dưới quyền chủ `$NVM_DIR`: `nvm install <major>` (có thể `--reinstall-packages-from=current`) | `ExecStart`/`interpreter` trỏ đường dẫn tuyệt đối `$NVM_DIR/versions/node/v<ver>/bin/node` (không dựa vào `nvm use`) | BR-SCN-027 | `nvm uninstall <ver cũ>`; `nvm alias default <major mới>` |
| E3 | NodeSource (`/etc/apt/sources.list.d/nodesource.sources`, suite `nodistro`, pin 600; chỉ `amd64`/`arm64`) | Không cài 2 major bằng NodeSource → dùng E1 | BR-SCN-027 | BR-SCN-027 | Khi không còn ứng dụng dùng gói cũ: đổi kho sang `node_<NEW>.x` và nâng gói (có duyệt), hoặc gỡ kho NodeSource |
| E4 | Gói distro (`nodejs` Debian/Ubuntu, AppStream RHEL, Alpine) | Kho OS có 1 gói `nodejs` (1 major) cho mỗi bản OS, vd Debian 12: 18, Debian 13: 20 → dùng E1 | BR-SCN-027 | BR-SCN-027 | Giữ gói distro nếu gói khác phụ thuộc (`apt-get -s purge nodejs`); không gỡ khi mô phỏng gỡ kèm gói khác |
| E5 | aaPanel (`/www/server/nodejs/*`, v0.1 đã dò) | Cài phiên bản mới qua trình quản lý Node của aaPanel (giao diện; CLI chưa kiểm chứng) | Chọn phiên bản cho dự án trong giao diện; mục `Thủ công` | Như A2 | Gỡ trong giao diện |
| E6 | Docker (`FROM node:` trong Dockerfile/compose, v0.1 `check_dockerfiles`) | Sửa tag sang `node:<NEW>` (tool chỉ sửa, không build/deploy) | Chạy container mới song song, đổi upstream reverse proxy | Trỏ upstream về container cũ | Xoá container/image cũ |

## 9. Ma trận lỗi bổ sung (Node.js)
Bổ sung cho [version-scenarios-common.md §6](version-scenarios-common.md#6-ma-trận-lỗi-của-bộ-máy-kịch-bản-error-matrix).

| Mã ERR | HTTP | Điều kiện phát sinh | Localization key | Thông báo hiển thị | Mức độ | Hành động tiếp theo |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `ERR-SCN-412-03` | 412 | Binary chính thức của `$NEW` không chạy được trên OS (lỗi `GLIBC_`, kiến trúc không hỗ trợ) (BR-SCN-028) | `scn.node.platform.unsupported` | "Node.js {target} không chạy được trên {os} ({detail})." | High | Dùng gói distro/NodeSource build cho OS, container (E6) hoặc máy chủ mới |
| `ERR-SCN-424-02` | 424 | Native addon không nạp được sau khi build lại bằng `$NEW_BIN` (BR-SCN-022) | `scn.node.addon.failed` | "Gói {package} (native addon) không nạp được trên Node.js {target}." | High | Nâng gói lên bản hỗ trợ ABI {abi} hoặc thay gói |

## 10. Kịch bản chi tiết SCN-NODE-001..012
Cột "Loại": **Tự động** (`AUTO`), **Bán tự động (duyệt)** (`SEMI`), **Thủ công** (`MANUAL`). "Như `CHK-NODE-001-NN`" = dùng lệnh/tiêu chí/rủi ro của mục mẫu SCN-NODE-001 với `$OLD` của kịch bản hiện tại.

### 10.1 SCN-NODE-001 — Node.js ≤ 16
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v(0\|[1-9]\|1[0-6])\.\d+\.\d+$` / 40 |
| Trạng thái, LTS, EOL | `EOL`. 16 (LTS Gallium) EOL 2023-09-11, bản cuối 16.20.2; 14 EOL 2023-04-30; 12 EOL 2022-04-30; 10 EOL 2021-04-30; dòng lẻ ≤ 15 và io.js 1–3 EOL trước đó. Quá ≥ 1.137 ngày → Nghiêm trọng |
| Đích | 26 (chuyển production từ 2026-10-28); thay thế 24 |
| Lộ trình | Production: một lần lên `$NEW` (BR-SCN-007). Mã/dependency trên staging: OpenSSL 3 (17) → `fetch` toàn cục (18) → ESM/`require(esm)` (22–23) → API bị xoá 24–26 |
| Dải BC | `BC-NODE-17-01` … `BC-NODE-26-01` (10 mục) khi đích 26 |
| Thay đổi chính | OpenSSL 1.1.1 → 3.5; npm 6/8 → 11 (lockfile 1/2 → 3); ABI 93 trở xuống → 147; glibc ≥ 2.28 cho binary chính thức |
| Môi trường | OS có glibc < 2.28 (vd CentOS 7 glibc 2.17 — chưa kiểm chứng trên máy thật) không chạy binary chính thức ≥ 18 → `ERR-SCN-412-03`, dùng E6 hoặc máy chủ mới |
| Restart | §7; pm2 7.1.0 yêu cầu Node ≥ 18 → daemon pm2 phải chạy trên `$NEW` |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-001-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | `$OLD_BIN --version` (timeout 10 s); `readlink -f $OLD_BIN`; `dpkg -S`/`rpm -qf`; `$OLD_PREFIX/bin/npm --version` | Chuỗi khớp `version_match`; nguồn cài (E1–E6) và bản npm ghi vào `scan --json` | Binary wrapper (vd shim của nvm) → luôn `readlink -f` như v0.1 |
| `CHK-NODE-001-02` | P1 | Kiểm kê ứng dụng dùng binary | Tự động | Unit systemd có `ExecStart` chứa `$OLD_PREFIX` (mẫu `restart_node_services` v0.1); `pm2 jlist` (interpreter, đường dẫn script, cwd); `crontab -l` của người dùng | Mỗi ứng dụng có `$APP`, `$APPDIR`, cơ chế (systemd/pm2/cron/khác) | Ứng dụng chạy bằng supervisor khác → người vận hành khai báo |
| `CHK-NODE-001-03` | P1 | Kiểm kê dự án của mỗi ứng dụng | Tự động | Đọc `package.json` (`engines.node`, `type`, `packageManager`, `scripts`), lockfile (`lockfileVersion`), `.nvmrc`, `.node-version` | Bản ghi dự án đủ trường trong state | `yarn.lock`/`pnpm-lock.yaml` → chỉ cảnh báo (v0.1) |
| `CHK-NODE-001-04` | P1 | Phát hiện native addon (BR-SCN-022) | Tự động | Tìm file `*.node` và `binding.gyp` trong thư mục dependency; gói có `"gypfile": true` hoặc script cài gọi `node-gyp`/`prebuild-install`/`node-pre-gyp`/`node-gyp-build` | Danh sách addon theo ứng dụng (có thể rỗng) | Addon tải bản build sẵn từ Internet → staging cần ra Internet tới host của gói |
| `CHK-NODE-001-05` | P1 | Kiểm tra glibc, kiến trúc (BR-SCN-028) | Tự động | `ldd --version`; `uname -m` | glibc ≥ 2.28 và kiến trúc thuộc danh sách E1; nếu không → `ERR-SCN-412-03` | OS cũ → chuyển máy/container |
| `CHK-NODE-001-06` | P1 | Đánh giá bảo mật so sánh `$OLD` với 22, 24, 26 | Tự động | FEAT-030, FEAT-032 (Node.js Security WG + NVD) | Bảng có cột LTS, trạng thái, EOL, số ngày còn lại, CVE theo mức; 22 hiển thị "không đủ điều kiện đích (EOL < hôm nay + 365)" | Dữ liệu cũ → BR-SCN-002 |
| `CHK-NODE-001-07` | P1 | Chọn và duyệt dòng đích (BR-SCN-006) | Bán tự động (duyệt) | FEAT-040; `engines.node` (BR-SCN-025) | Kế hoạch `approved`; đích ∈ {24, 26}; ngày chuyển production của 26 ≥ 2026-10-28 | Chọn 26 trước 2026-10-28 cho production → `ERR-SCN-409-02` |
| `CHK-NODE-001-08` | P1 | Sao lưu cấu hình ứng dụng | Tự động | Manifest `copy`: `package.json`, lockfile, unit systemd, file ecosystem pm2, `.nvmrc`; `.env` lưu quyền 0600 | Mỗi file có bản sao và SHA-256 trong manifest | `.env` chứa secret → thư mục backup quyền 0700, chỉ root đọc |
| `CHK-NODE-001-09` | P1 | Dựng staging cách ly (BR-SCN-030) | Thủ công | Bản sao ứng dụng + CSDL test; chặn inbound Internet | Ứng dụng staging trả HTTP 200 (hoặc tiến trình worker chạy ≥ 10 phút) trên `$OLD` | Staging gọi API thật (thanh toán, email) → dùng khoá test |
| `CHK-NODE-001-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | `df -BG --output=avail /opt`; `free -m` | Đĩa ≥ 2 GB, RAM khả dụng ≥ 512 MB | Thiếu đĩa → `ERR-SCN-412-01` |
| `CHK-NODE-001-11` | P2 | Cài `$NEW` song song (§8 A1, BR-SCN-026) | Bán tự động (duyệt) | E1: tải tarball + `SHASUMS256.txt`, `sha256sum -c`, giải nén `/opt/node-v<ver>-linux-<arch>`; E2: `nvm install <major>` | `$NEW_BIN --version` khớp `^v<NEW>\.`; `readlink -f /usr/bin/node` không đổi (BR-SCN-012) | Checksum sai → dừng, không giải nén |
| `CHK-NODE-001-12` | P2 | Cài công cụ phụ trợ dưới `$NEW` | Bán tự động (duyệt) | `$NEW_PREFIX/bin/npm install -g pm2` (khi dùng pm2); `npm install -g corepack` (khi có `packageManager`, BC-NODE-25-01) | `pm2 --version`, `corepack --version` chạy bằng `$NEW_BIN` exit 0 | Cài global ghi vào prefix đích, không ảnh hưởng `$OLD` |
| `CHK-NODE-001-13` | P3 | Kiểm tra `engines.node` (BR-SCN-025) | Tự động | Đối chiếu semver với bản patch của `$NEW`; tra npm registry khi lockfile thiếu | Danh sách gói vi phạm; 0 gói vi phạm trong `dependencies` sau P4 | Gói khai báo `engines` quá chặt nhưng vẫn chạy → miễn trừ có duyệt |
| `CHK-NODE-001-14` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] trong mã ứng dụng (BR-SCN-021) | Tự động | Mẫu "Tĩnh" ở §5; quét cờ trong `NODE_OPTIONS`, unit, ecosystem | 0 hit loại `Xoá` chưa xử lý; hit khác liệt kê file:dòng | Dương tính giả → duyệt theo trích đoạn |
| `CHK-NODE-001-15` | P3 | Cài dependency sạch trên `$COPY` bằng npm của `$NEW` (BR-SCN-024) | Bán tự động (duyệt) | `lockfileVersion` 1: `npm install --package-lock-only` rồi duyệt diff; sau đó `npm ci` (dưới quyền chủ thư mục) | `npm ci` exit 0; `lockfileVersion` = 3 | Giải lại cây phụ thuộc đổi phiên bản phụ → test ở mục 18 |
| `CHK-NODE-001-16` | P3 | Build lại và nạp thử native addon (BR-SCN-022) | Tự động | `npm rebuild` bằng `$NEW_BIN`; `require`/`import()` từng addon | 0 lỗi `ERR_DLOPEN_FAILED`; mọi addon exit 0; nếu không → `ERR-SCN-424-02` | Thiếu trình biên dịch/Python cho `node-gyp` → cài build tool trên staging |
| `CHK-NODE-001-17` | P3 | Kiểm tra OpenSSL 3 (BR-SCN-023) | Tự động | Chạy `npm run build` (nếu có) và khởi động thử bằng `$NEW_BIN`; grep log | 0 dòng `ERR_OSSL_EVP_UNSUPPORTED` | Dùng `--openssl-legacy-provider` vĩnh viễn → chỉ cho phép ≤ 30 ngày có duyệt |
| `CHK-NODE-001-18` | P3 | Chạy test của dự án bằng `$NEW_BIN` | Bán tự động (duyệt) | `npm test` (khi có script `test`) với `PATH=$NEW_PREFIX/bin:$PATH` | Exit 0; số test lỗi = 0 | Thiếu test → `WAIVED` có lý do, dựa vào mục 26–27 |
| `CHK-NODE-001-19` | P3 | Khởi động thử ứng dụng trên staging bằng `$NEW_BIN` trong 10 phút | Tự động | Health check BR-SCN-009 trên staging | Đạt 6 tiêu chí so với baseline staging | Tải staging thấp hơn production → canary ở P5 |
| `CHK-NODE-001-20` | P3 | Sửa mã theo báo cáo 13–19 | Thủ công | Lập trình viên; tool chạy lại 13–19 | Mục 13–19 đạt | Ngoài phạm vi tool |
| `CHK-NODE-001-21` | P4 | Nâng dependency vi phạm `engines` hoặc có lỗ hổng | Bán tự động (duyệt) | Trên `$COPY`: `npm install <gói>@<bản>`; `npm audit fix` (không `--force`, như v0.1); OSV `querybatch` | 0 vi phạm `engines` trong `dependencies`; OSV 0 Critical, 0 `MAL-*` | Major mới của gói đổi API → test lại mục 18 |
| `CHK-NODE-001-22` | P4 | Nâng framework ứng dụng (Express, NestJS, Next.js…) khi `engines.node` của framework không gồm `$NEW` | Thủ công | Theo hướng dẫn nâng cấp của framework | `engines.node` của framework chấp nhận `$NEW` | Framework không có ma trận chính thức trong tài liệu này → dựa vào `engines` |
| `CHK-NODE-001-23` | P5 | Chụp baseline trên `$OLD` | Tự động | BR-SCN-009: HTTP (nếu có cổng), `NRestarts`/`restart_time`, RSS | Baseline đủ trường cho mỗi ứng dụng | Ứng dụng không có HTTP → chỉ đo tiến trình |
| `CHK-NODE-001-24` | P5 | Chuyển ứng dụng canary sang `$NEW` (BR-SCN-027) | Bán tự động (duyệt) | systemd drop-in hoặc pm2 ecosystem; manifest `created`/`copy` | `readlink /proc/<pid>/exe` = `$NEW_BIN`; trạng thái `active`/`online` | Cài dependency trên production phải bằng `$NEW` (`npm ci` trước khi restart) |
| `CHK-NODE-001-25` | P5 | Chuyển từng ứng dụng còn lại, mỗi ứng dụng 1 lần duyệt | Bán tự động (duyệt) | Như mục 24, tuần tự | 100% ứng dụng `DONE`/`WAIVED` | Chuyển đồng loạt bị cấm (BR-SCN-008) |
| `CHK-NODE-001-26` | P6 | Health check 10 phút + tự hoàn tác (BR-SCN-009, BR-SCN-010) | Tự động | So baseline mục 23; thêm grep log `ERR_REQUIRE_ESM`, `ERR_REQUIRE_ASYNC_MODULE`, `ERR_DLOPEN_FAILED`, `ERR_OSSL_EVP_UNSUPPORTED` | Đạt 6 tiêu chí và 0 dòng log khớp; nếu không: hoàn tác ≤ 60 s, `ERR-SCN-500-01` | Lỗi chỉ xuất hiện ở tác vụ định kỳ → mục 28 |
| `CHK-NODE-001-27` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ ứng dụng | 100% kịch bản pass, ký xác nhận | Thiếu kịch bản → `WAIVED` có lý do |
| `CHK-NODE-001-28` | P6 | Chuyển cron/CLI và daemon pm2 sang `$NEW` | Bán tự động (duyệt) | Cron: thay `node`/`$OLD_BIN` bằng `$NEW_BIN`; pm2: `pm2 update`, `pm2 unstartup`, `pm2 startup`, `pm2 save` | 0 cron gọi `$OLD_BIN`; `systemctl cat pm2-<user>` chứa `$NEW_PREFIX/bin` trong `PATH` | Bỏ qua bước startup → sau reboot pm2 chạy lại bằng Node cũ |
| `CHK-NODE-001-29` | P7 | Gỡ cờ tạm `--openssl-legacy-provider` (nếu đã dùng) | Bán tự động (duyệt) | Xoá cờ khỏi `NODE_OPTIONS`/unit/ecosystem; restart; manifest | 0 nơi còn cờ; health check đạt | Gỡ sớm khi thư viện chưa nâng → lỗi OpenSSL quay lại |
| `CHK-NODE-001-30` | P7 | Thống kê `DeprecationWarning` 7 ngày | Tự động | Đếm dòng `DeprecationWarning`/`DEP0` trong journal hoặc log pm2 | Báo cáo theo mã DEP; nhóm mới đưa vào backlog | Deprecation runtime ở 26 sẽ thành lỗi ở dòng sau |
| `CHK-NODE-001-31` | P7 | Cập nhật tệp ghim phiên bản (BR-SCN-030) | Bán tự động (duyệt) | `.nvmrc`, `.node-version`, `engines.node`, `FROM node:` (v0.1 `check_dockerfiles`), CI | 0 tham chiếu dòng `$OLD` trong các tệp này | Đổi `engines` làm gói không cài được trên máy dev cũ → thông báo nhóm dev |
| `CHK-NODE-001-32` | P7 | Gỡ `$OLD` sau 14 ngày không có tiến trình dùng (BR-SCN-014, §8 A4) | Bán tự động (duyệt) | `ps -eo args` không chứa `$OLD_PREFIX` trong 14 ngày; backup prefix | `$OLD_BIN` không còn; bản nén prefix > 0 byte có SHA-256 | Mất rollback 1 lệnh → cảnh báo trước khi duyệt |

### 10.2 SCN-NODE-002 — Node.js 18
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v18\.\d+\.\d+$` / 50 |
| Trạng thái, LTS, EOL | `EOL` từ 2025-04-30 (LTS Hydrogen; bản cuối 18.20.8 ngày 2025-03-27); quá 540 ngày → Nghiêm trọng |
| Đích | 26 (từ 2026-10-28); thay thế 24 |
| Dải BC | `BC-NODE-19-01` … `BC-NODE-26-01` (8 mục) |
| Thay đổi chính | ABI 108 → 147; npm 10.8.2 → 11.20.0 (lockfile vẫn 3); `require(esm)` mặc định (23); xoá API 24–26; Corepack không còn đi kèm (25) |
| Môi trường | Gói distro: Debian 12 `nodejs 18.20.4+dfsg-1~deb12u2`; Ubuntu 24.04 `18.19.1+dfsg-6ubuntu5` (Launchpad chỉ có bản ở pocket Release, không có bản ở Security/Updates tại 2026-10-22) → overlay SCN-NODE-012 |
| Staging | Bắt buộc (khoảng cách ≥ 2 dòng LTS, BR-SCN-030) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-002-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `version_match`; nguồn cài và bản npm trong `scan --json` | Như `CHK-NODE-001-01` |
| `CHK-NODE-002-02` | P1 | Kiểm kê ứng dụng dùng binary | Tự động | Như `CHK-NODE-001-02` | Mỗi ứng dụng có `$APP`, `$APPDIR`, cơ chế chạy | Như `CHK-NODE-001-02` |
| `CHK-NODE-002-03` | P1 | Kiểm kê dự án của mỗi ứng dụng | Tự động | Như `CHK-NODE-001-03` | Bản ghi dự án đủ trường | Như `CHK-NODE-001-03` |
| `CHK-NODE-002-04` | P1 | Phát hiện native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-04` | Danh sách addon theo ứng dụng | Như `CHK-NODE-001-04` |
| `CHK-NODE-002-05` | P1 | Kiểm tra glibc, kiến trúc khi dùng binary chính thức (BR-SCN-028) | Tự động | Như `CHK-NODE-001-05` | glibc ≥ 2.28, kiến trúc hỗ trợ; nếu không → `ERR-SCN-412-03` | Như `CHK-NODE-001-05` |
| `CHK-NODE-002-06` | P1 | Đánh giá bảo mật so sánh với 22, 24, 26 | Tự động | Như `CHK-NODE-001-06` | Bảng đủ cột LTS, trạng thái, EOL, CVE | Như `CHK-NODE-001-06` |
| `CHK-NODE-002-07` | P1 | Chọn và duyệt dòng đích (BR-SCN-006) | Bán tự động (duyệt) | Như `CHK-NODE-001-07` | Kế hoạch `approved`; đích ∈ {24, 26} | Như `CHK-NODE-001-07` |
| `CHK-NODE-002-08` | P1 | Sao lưu cấu hình ứng dụng | Tự động | Như `CHK-NODE-001-08` | Mỗi file có bản sao và SHA-256 trong manifest | Như `CHK-NODE-001-08` |
| `CHK-NODE-002-09` | P1 | Dựng staging cách ly (BR-SCN-030) | Thủ công | Như `CHK-NODE-001-09` | Ứng dụng staging chạy trên `$OLD` | Như `CHK-NODE-001-09` |
| `CHK-NODE-002-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-NODE-001-10` | Đĩa ≥ 2 GB, RAM khả dụng ≥ 512 MB | Như `CHK-NODE-001-10` |
| `CHK-NODE-002-11` | P2 | Cài `$NEW` song song (§8 A1, BR-SCN-026) | Bán tự động (duyệt) | Như `CHK-NODE-001-11` | `$NEW_BIN --version` khớp `^v<NEW>\.`; `readlink -f /usr/bin/node` không đổi | Như `CHK-NODE-001-11` |
| `CHK-NODE-002-12` | P2 | Cài pm2/Corepack dưới `$NEW` (khi dùng) | Bán tự động (duyệt) | Như `CHK-NODE-001-12` | `pm2 --version`, `corepack --version` exit 0 | Như `CHK-NODE-001-12` |
| `CHK-NODE-002-13` | P3 | Kiểm tra `engines.node` (BR-SCN-025) | Tự động | Như `CHK-NODE-001-13` | 0 gói vi phạm trong `dependencies` sau P4 | Như `CHK-NODE-001-13` |
| `CHK-NODE-002-14` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] (BR-SCN-021) | Tự động | Như `CHK-NODE-001-14` | 0 hit loại `Xoá` chưa xử lý | Như `CHK-NODE-001-14` |
| `CHK-NODE-002-15` | P3 | Cài dependency sạch trên `$COPY` bằng npm của `$NEW` (BR-SCN-024) | Bán tự động (duyệt) | `npm ci` (lockfile 2/3) dưới quyền chủ thư mục | `npm ci` exit 0 | Như `CHK-NODE-001-15` |
| `CHK-NODE-002-16` | P3 | Build lại và nạp thử native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-16` | 0 `ERR_DLOPEN_FAILED`; nếu không → `ERR-SCN-424-02` | Như `CHK-NODE-001-16` |
| `CHK-NODE-002-17` | P3 | Kiểm tra ESM: `require()` module ESM và top-level `await` (BC-NODE-22-01, BC-NODE-23-01) | Tự động | Khởi động thử bằng `$NEW_BIN`; grep `ERR_REQUIRE_ASYNC_MODULE`, `ERR_REQUIRE_ESM` | 0 dòng khớp | Hành vi khác nhau giữa 22.x và 23+ → kiểm trên đúng bản patch đích |
| `CHK-NODE-002-18` | P3 | Chạy test của dự án bằng `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-NODE-001-18` | Exit 0; 0 test lỗi | Như `CHK-NODE-001-18` |
| `CHK-NODE-002-19` | P3 | Khởi động thử trên staging 10 phút | Tự động | Như `CHK-NODE-001-19` | Đạt 6 tiêu chí BR-SCN-009 | Như `CHK-NODE-001-19` |
| `CHK-NODE-002-20` | P3 | Sửa mã theo báo cáo | Thủ công | Như `CHK-NODE-001-20` | Các mục P3 đạt | Như `CHK-NODE-001-20` |
| `CHK-NODE-002-21` | P4 | Nâng dependency vi phạm `engines` hoặc có lỗ hổng | Bán tự động (duyệt) | Như `CHK-NODE-001-21` | 0 vi phạm `engines`; OSV 0 Critical, 0 `MAL-*` | Như `CHK-NODE-001-21` |
| `CHK-NODE-002-22` | P4 | Nâng framework ứng dụng khi `engines.node` không gồm `$NEW` | Thủ công | Như `CHK-NODE-001-22` | `engines.node` của framework chấp nhận `$NEW` | Như `CHK-NODE-001-22` |
| `CHK-NODE-002-23` | P5 | Chụp baseline trên `$OLD` | Tự động | Như `CHK-NODE-001-23` | Baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-002-24` | P5 | Chuyển ứng dụng canary (BR-SCN-027) | Bán tự động (duyệt) | Như `CHK-NODE-001-24` | `readlink /proc/<pid>/exe` = `$NEW_BIN`; `active`/`online` | Như `CHK-NODE-001-24` |
| `CHK-NODE-002-25` | P5 | Chuyển từng ứng dụng còn lại, mỗi ứng dụng 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-NODE-001-25` | 100% ứng dụng `DONE`/`WAIVED` | Như `CHK-NODE-001-25` |
| `CHK-NODE-002-26` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí và 0 dòng log lỗi theo mẫu | Như `CHK-NODE-001-26` |
| `CHK-NODE-002-27` | P6 | Kiểm thử nghiệp vụ | Thủ công | Như `CHK-NODE-001-27` | 100% kịch bản pass | Như `CHK-NODE-001-27` |
| `CHK-NODE-002-28` | P6 | Chuyển cron/CLI và daemon pm2 sang `$NEW` | Bán tự động (duyệt) | Như `CHK-NODE-001-28` | 0 cron gọi `$OLD_BIN`; script startup pm2 dùng `$NEW_PREFIX` | Như `CHK-NODE-001-28` |
| `CHK-NODE-002-29` | P7 | Thống kê `DeprecationWarning` 7 ngày | Tự động | Như `CHK-NODE-001-30` | Báo cáo theo mã DEP | Như `CHK-NODE-001-30` |
| `CHK-NODE-002-30` | P7 | Cập nhật tệp ghim phiên bản (BR-SCN-030) | Bán tự động (duyệt) | Như `CHK-NODE-001-31` | 0 tham chiếu dòng `$OLD` | Như `CHK-NODE-001-31` |
| `CHK-NODE-002-31` | P7 | Gỡ `$OLD` sau 14 ngày không dùng (BR-SCN-014) | Bán tự động (duyệt) | Như `CHK-NODE-001-32` | `$OLD_BIN` không còn; bản nén prefix có SHA-256 | Như `CHK-NODE-001-32` |

### 10.3 SCN-NODE-003 — Node.js 20
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v20\.\d+\.\d+$` / 60 |
| Trạng thái, LTS, EOL | `EOL` từ 2026-04-30 (LTS Iron; bản cuối 20.20.2 ngày 2026-03-24); quá 175 ngày → Cao |
| Đích | 26 (từ 2026-10-28); thay thế 24 |
| Dải BC | `BC-NODE-21-01` … `BC-NODE-26-01` (6 mục) |
| Thay đổi chính | ABI 115 → 147; npm 10.8.2 → 11.x; WebSocket mặc định, bỏ import assertions (22); `require(esm)` mặc định (23); `url.parse()` runtime-deprecated, xoá `tls.createSecurePair` (24); Corepack không còn đi kèm (25); xoá `writeHeader()`, `_stream_*` (26) |
| Môi trường | Gói distro: Debian 13 `nodejs 20.19.2+dfsg-1+deb13u2`; Ubuntu 25.10 `20.19.4` → overlay SCN-NODE-012 |
| Staging | Bắt buộc (20 → 24/26 cách ≥ 2 dòng LTS, BR-SCN-030) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-003-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `version_match`; nguồn cài và bản npm trong `scan --json` | Như `CHK-NODE-001-01` |
| `CHK-NODE-003-02` | P1 | Kiểm kê ứng dụng dùng binary | Tự động | Như `CHK-NODE-001-02` | Mỗi ứng dụng có `$APP`, `$APPDIR`, cơ chế chạy | Như `CHK-NODE-001-02` |
| `CHK-NODE-003-03` | P1 | Kiểm kê dự án của mỗi ứng dụng | Tự động | Như `CHK-NODE-001-03` | Bản ghi dự án đủ trường | Như `CHK-NODE-001-03` |
| `CHK-NODE-003-04` | P1 | Phát hiện native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-04` | Danh sách addon theo ứng dụng | Như `CHK-NODE-001-04` |
| `CHK-NODE-003-05` | P1 | Kiểm tra glibc, kiến trúc khi dùng binary chính thức (BR-SCN-028) | Tự động | Như `CHK-NODE-001-05` | glibc ≥ 2.28, kiến trúc hỗ trợ; nếu không → `ERR-SCN-412-03` | Như `CHK-NODE-001-05` |
| `CHK-NODE-003-06` | P1 | Đánh giá bảo mật so sánh với 22, 24, 26 | Tự động | Như `CHK-NODE-001-06` | Bảng đủ cột LTS, trạng thái, EOL, CVE | Như `CHK-NODE-001-06` |
| `CHK-NODE-003-07` | P1 | Chọn và duyệt dòng đích (BR-SCN-006) | Bán tự động (duyệt) | Như `CHK-NODE-001-07` | Kế hoạch `approved`; đích ∈ {24, 26} | Như `CHK-NODE-001-07` |
| `CHK-NODE-003-08` | P1 | Sao lưu cấu hình ứng dụng | Tự động | Như `CHK-NODE-001-08` | Mỗi file có bản sao và SHA-256 trong manifest | Như `CHK-NODE-001-08` |
| `CHK-NODE-003-09` | P1 | Dựng staging cách ly (BR-SCN-030) | Thủ công | Như `CHK-NODE-001-09` | Ứng dụng staging chạy trên `$OLD` | Như `CHK-NODE-001-09` |
| `CHK-NODE-003-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-NODE-001-10` | Đĩa ≥ 2 GB, RAM khả dụng ≥ 512 MB | Như `CHK-NODE-001-10` |
| `CHK-NODE-003-11` | P2 | Cài `$NEW` song song (§8 A1, BR-SCN-026) | Bán tự động (duyệt) | Như `CHK-NODE-001-11` | `$NEW_BIN --version` khớp `^v<NEW>\.`; `readlink -f /usr/bin/node` không đổi | Như `CHK-NODE-001-11` |
| `CHK-NODE-003-12` | P2 | Cài pm2/Corepack dưới `$NEW` (khi dùng) | Bán tự động (duyệt) | Như `CHK-NODE-001-12` | `pm2 --version`, `corepack --version` exit 0 | Như `CHK-NODE-001-12` |
| `CHK-NODE-003-13` | P3 | Kiểm tra `engines.node` (BR-SCN-025) | Tự động | Như `CHK-NODE-001-13` | 0 gói vi phạm trong `dependencies` sau P4 | Như `CHK-NODE-001-13` |
| `CHK-NODE-003-14` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] (BR-SCN-021) | Tự động | Như `CHK-NODE-001-14` | 0 hit loại `Xoá` chưa xử lý | Như `CHK-NODE-001-14` |
| `CHK-NODE-003-15` | P3 | Cài dependency sạch trên `$COPY` bằng npm của `$NEW` (BR-SCN-024) | Bán tự động (duyệt) | `npm ci` (lockfile 2/3) dưới quyền chủ thư mục | `npm ci` exit 0 | Như `CHK-NODE-001-15` |
| `CHK-NODE-003-16` | P3 | Build lại và nạp thử native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-16` | 0 `ERR_DLOPEN_FAILED`; nếu không → `ERR-SCN-424-02` | Như `CHK-NODE-001-16` |
| `CHK-NODE-003-17` | P3 | Kiểm tra ESM: `require()` module ESM và top-level `await` (BC-NODE-22-01, BC-NODE-23-01) | Tự động | Khởi động thử bằng `$NEW_BIN`; grep `ERR_REQUIRE_ASYNC_MODULE`, `ERR_REQUIRE_ESM` | 0 dòng khớp | Hành vi khác nhau giữa 22.x và 23+ → kiểm trên đúng bản patch đích |
| `CHK-NODE-003-18` | P3 | Chạy test của dự án bằng `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-NODE-001-18` | Exit 0; 0 test lỗi | Như `CHK-NODE-001-18` |
| `CHK-NODE-003-19` | P3 | Khởi động thử trên staging 10 phút | Tự động | Như `CHK-NODE-001-19` | Đạt 6 tiêu chí BR-SCN-009 | Như `CHK-NODE-001-19` |
| `CHK-NODE-003-20` | P3 | Sửa mã theo báo cáo | Thủ công | Như `CHK-NODE-001-20` | Các mục P3 đạt | Như `CHK-NODE-001-20` |
| `CHK-NODE-003-21` | P4 | Nâng dependency vi phạm `engines` hoặc có lỗ hổng | Bán tự động (duyệt) | Như `CHK-NODE-001-21` | 0 vi phạm `engines`; OSV 0 Critical, 0 `MAL-*` | Như `CHK-NODE-001-21` |
| `CHK-NODE-003-22` | P4 | Nâng framework ứng dụng khi `engines.node` không gồm `$NEW` | Thủ công | Như `CHK-NODE-001-22` | `engines.node` của framework chấp nhận `$NEW` | Như `CHK-NODE-001-22` |
| `CHK-NODE-003-23` | P5 | Chụp baseline trên `$OLD` | Tự động | Như `CHK-NODE-001-23` | Baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-003-24` | P5 | Chuyển ứng dụng canary (BR-SCN-027) | Bán tự động (duyệt) | Như `CHK-NODE-001-24` | `readlink /proc/<pid>/exe` = `$NEW_BIN`; `active`/`online` | Như `CHK-NODE-001-24` |
| `CHK-NODE-003-25` | P5 | Chuyển từng ứng dụng còn lại, mỗi ứng dụng 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-NODE-001-25` | 100% ứng dụng `DONE`/`WAIVED` | Như `CHK-NODE-001-25` |
| `CHK-NODE-003-26` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí và 0 dòng log lỗi theo mẫu | Như `CHK-NODE-001-26` |
| `CHK-NODE-003-27` | P6 | Kiểm thử nghiệp vụ | Thủ công | Như `CHK-NODE-001-27` | 100% kịch bản pass | Như `CHK-NODE-001-27` |
| `CHK-NODE-003-28` | P6 | Chuyển cron/CLI và daemon pm2 sang `$NEW` | Bán tự động (duyệt) | Như `CHK-NODE-001-28` | 0 cron gọi `$OLD_BIN`; script startup pm2 dùng `$NEW_PREFIX` | Như `CHK-NODE-001-28` |
| `CHK-NODE-003-29` | P7 | Thống kê `DeprecationWarning` 7 ngày | Tự động | Như `CHK-NODE-001-30` | Báo cáo theo mã DEP | Như `CHK-NODE-001-30` |
| `CHK-NODE-003-30` | P7 | Cập nhật tệp ghim phiên bản (BR-SCN-030) | Bán tự động (duyệt) | Như `CHK-NODE-001-31` | 0 tham chiếu dòng `$OLD` | Như `CHK-NODE-001-31` |
| `CHK-NODE-003-31` | P7 | Gỡ `$OLD` sau 14 ngày không dùng (BR-SCN-014) | Bán tự động (duyệt) | Như `CHK-NODE-001-32` | `$OLD_BIN` không còn; bản nén prefix có SHA-256 | Như `CHK-NODE-001-32` |

### 10.4 SCN-NODE-004 — Dòng lẻ 17, 19, 21, 23, 25
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v(17\|19\|21\|23\|25)\.\d+\.\d+$` / 70 |
| Trạng thái, LTS, EOL | `EOL`, không bao giờ là LTS. 17: 2022-06-01 (17.9.1); 19: 2023-06-01 (19.9.0); 21: 2024-06-01 (21.7.3); 23: 2025-06-01 (23.11.1); 25: 2026-06-01 (25.9.0). 25 quá 143 ngày → Cao; các dòng còn lại → Nghiêm trọng |
| Đích | 26 (từ 2026-10-28); thay thế 24. Không chọn dòng lẻ làm đích (từ dòng 27 không còn dòng lẻ) |
| Dải BC | Từ mục BC của dòng `$OLD + 1` đến `BC-NODE-26-01`: 17 → 9 mục; 19 → 7; 21 → 5; 23 → 3; 25 → 1 |
| Ghi chú | Dòng lẻ có tính năng bật mặc định mà dòng chẵn liền trước chưa có (vd `require(esm)` mặc định ở 23, Web Storage mặc định ở 25); hạ xuống 24 có thể mất tính năng → mục 17 |
| Staging | Bắt buộc (BR-SCN-030) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-004-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `version_match`; nguồn cài và bản npm trong `scan --json` | Như `CHK-NODE-001-01` |
| `CHK-NODE-004-02` | P1 | Kiểm kê ứng dụng dùng binary | Tự động | Như `CHK-NODE-001-02` | Mỗi ứng dụng có `$APP`, `$APPDIR`, cơ chế chạy | Như `CHK-NODE-001-02` |
| `CHK-NODE-004-03` | P1 | Kiểm kê dự án của mỗi ứng dụng | Tự động | Như `CHK-NODE-001-03` | Bản ghi dự án đủ trường | Như `CHK-NODE-001-03` |
| `CHK-NODE-004-04` | P1 | Phát hiện native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-04` | Danh sách addon theo ứng dụng | Như `CHK-NODE-001-04` |
| `CHK-NODE-004-05` | P1 | Kiểm tra glibc, kiến trúc khi dùng binary chính thức (BR-SCN-028) | Tự động | Như `CHK-NODE-001-05` | glibc ≥ 2.28, kiến trúc hỗ trợ; nếu không → `ERR-SCN-412-03` | Như `CHK-NODE-001-05` |
| `CHK-NODE-004-06` | P1 | Đánh giá bảo mật so sánh với 22, 24, 26 | Tự động | Như `CHK-NODE-001-06` | Bảng đủ cột LTS, trạng thái, EOL, CVE | Như `CHK-NODE-001-06` |
| `CHK-NODE-004-07` | P1 | Chọn và duyệt dòng đích (BR-SCN-006) | Bán tự động (duyệt) | Như `CHK-NODE-001-07` | Kế hoạch `approved`; đích ∈ {24, 26} | Như `CHK-NODE-001-07` |
| `CHK-NODE-004-08` | P1 | Sao lưu cấu hình ứng dụng | Tự động | Như `CHK-NODE-001-08` | Mỗi file có bản sao và SHA-256 trong manifest | Như `CHK-NODE-001-08` |
| `CHK-NODE-004-09` | P1 | Dựng staging cách ly (BR-SCN-030) | Thủ công | Như `CHK-NODE-001-09` | Ứng dụng staging chạy trên `$OLD` | Như `CHK-NODE-001-09` |
| `CHK-NODE-004-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-NODE-001-10` | Đĩa ≥ 2 GB, RAM khả dụng ≥ 512 MB | Như `CHK-NODE-001-10` |
| `CHK-NODE-004-11` | P2 | Cài `$NEW` song song (§8 A1, BR-SCN-026) | Bán tự động (duyệt) | Như `CHK-NODE-001-11` | `$NEW_BIN --version` khớp `^v<NEW>\.`; `readlink -f /usr/bin/node` không đổi | Như `CHK-NODE-001-11` |
| `CHK-NODE-004-12` | P2 | Cài pm2/Corepack dưới `$NEW` (khi dùng) | Bán tự động (duyệt) | Như `CHK-NODE-001-12` | `pm2 --version`, `corepack --version` exit 0 | Như `CHK-NODE-001-12` |
| `CHK-NODE-004-13` | P3 | Kiểm tra `engines.node` (BR-SCN-025) | Tự động | Như `CHK-NODE-001-13` | 0 gói vi phạm trong `dependencies` sau P4 | Như `CHK-NODE-001-13` |
| `CHK-NODE-004-14` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] (BR-SCN-021) | Tự động | Như `CHK-NODE-001-14` | 0 hit loại `Xoá` chưa xử lý | Như `CHK-NODE-001-14` |
| `CHK-NODE-004-15` | P3 | Cài dependency sạch trên `$COPY` bằng npm của `$NEW` (BR-SCN-024) | Bán tự động (duyệt) | `npm ci` (lockfile 2/3) dưới quyền chủ thư mục | `npm ci` exit 0 | Như `CHK-NODE-001-15` |
| `CHK-NODE-004-16` | P3 | Build lại và nạp thử native addon (BR-SCN-022) | Tự động | Như `CHK-NODE-001-16` | 0 `ERR_DLOPEN_FAILED`; nếu không → `ERR-SCN-424-02` | Như `CHK-NODE-001-16` |
| `CHK-NODE-004-17` | P3 | Kiểm tra tính năng của dòng lẻ khi đích là dòng thấp hơn (vd 25 → 24) | Tự động | Liệt kê API/cờ của dòng `$OLD` dùng trong mã và `NODE_OPTIONS`: Web Storage (`localStorage`), cờ `--experimental-*`, `--allow-net` | Danh sách rỗng hoặc mọi mục có phương án đã duyệt | Hạ major làm mất API → chọn 26 thay vì 24 |
| `CHK-NODE-004-18` | P3 | Kiểm tra ESM: `require()` module ESM và top-level `await` (BC-NODE-22-01, BC-NODE-23-01) | Tự động | Khởi động thử bằng `$NEW_BIN`; grep `ERR_REQUIRE_ASYNC_MODULE`, `ERR_REQUIRE_ESM` | 0 dòng khớp | Hành vi khác nhau giữa 22.x và 23+ → kiểm trên đúng bản patch đích |
| `CHK-NODE-004-19` | P3 | Chạy test của dự án bằng `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-NODE-001-18` | Exit 0; 0 test lỗi | Như `CHK-NODE-001-18` |
| `CHK-NODE-004-20` | P3 | Khởi động thử trên staging 10 phút | Tự động | Như `CHK-NODE-001-19` | Đạt 6 tiêu chí BR-SCN-009 | Như `CHK-NODE-001-19` |
| `CHK-NODE-004-21` | P3 | Sửa mã theo báo cáo | Thủ công | Như `CHK-NODE-001-20` | Các mục P3 đạt | Như `CHK-NODE-001-20` |
| `CHK-NODE-004-22` | P4 | Nâng dependency vi phạm `engines` hoặc có lỗ hổng | Bán tự động (duyệt) | Như `CHK-NODE-001-21` | 0 vi phạm `engines`; OSV 0 Critical, 0 `MAL-*` | Như `CHK-NODE-001-21` |
| `CHK-NODE-004-23` | P4 | Nâng framework ứng dụng khi `engines.node` không gồm `$NEW` | Thủ công | Như `CHK-NODE-001-22` | `engines.node` của framework chấp nhận `$NEW` | Như `CHK-NODE-001-22` |
| `CHK-NODE-004-24` | P5 | Chụp baseline trên `$OLD` | Tự động | Như `CHK-NODE-001-23` | Baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-004-25` | P5 | Chuyển ứng dụng canary (BR-SCN-027) | Bán tự động (duyệt) | Như `CHK-NODE-001-24` | `readlink /proc/<pid>/exe` = `$NEW_BIN`; `active`/`online` | Như `CHK-NODE-001-24` |
| `CHK-NODE-004-26` | P5 | Chuyển từng ứng dụng còn lại, mỗi ứng dụng 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-NODE-001-25` | 100% ứng dụng `DONE`/`WAIVED` | Như `CHK-NODE-001-25` |
| `CHK-NODE-004-27` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí và 0 dòng log lỗi theo mẫu | Như `CHK-NODE-001-26` |
| `CHK-NODE-004-28` | P6 | Kiểm thử nghiệp vụ | Thủ công | Như `CHK-NODE-001-27` | 100% kịch bản pass | Như `CHK-NODE-001-27` |
| `CHK-NODE-004-29` | P6 | Chuyển cron/CLI và daemon pm2 sang `$NEW` | Bán tự động (duyệt) | Như `CHK-NODE-001-28` | 0 cron gọi `$OLD_BIN`; script startup pm2 dùng `$NEW_PREFIX` | Như `CHK-NODE-001-28` |
| `CHK-NODE-004-30` | P7 | Thống kê `DeprecationWarning` 7 ngày | Tự động | Như `CHK-NODE-001-30` | Báo cáo theo mã DEP | Như `CHK-NODE-001-30` |
| `CHK-NODE-004-31` | P7 | Cập nhật tệp ghim phiên bản (BR-SCN-030) | Bán tự động (duyệt) | Như `CHK-NODE-001-31` | 0 tham chiếu dòng `$OLD` | Như `CHK-NODE-001-31` |
| `CHK-NODE-004-32` | P7 | Gỡ `$OLD` sau 14 ngày không dùng (BR-SCN-014) | Bán tự động (duyệt) | Như `CHK-NODE-001-32` | `$OLD_BIN` không còn; bản nén prefix có SHA-256 | Như `CHK-NODE-001-32` |

### 10.5 SCN-NODE-005 — Node.js 22
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v22\.\d+\.\d+$` / 80 |
| Trạng thái, LTS, EOL | `MAINTENANCE_LTS` (LTS Jod; vào LTS 2024-10-29, vào Maintenance 2025-10-21); EOL 2027-04-30, còn 190 ngày → Trung bình; Cao khi bản đang chạy < 22.23.4 và có CVE CVSS ≥ 7,0 chưa vá |
| Bản vá tối thiểu | 22.23.4 (2026-10-20, cờ `security`; trùng `NODE_FIXED` của v0.1) |
| Đích | Giữ dòng, vá 22.23.4. Nâng lên 26 (thay thế 24): kế hoạch `approved` trước 2027-03-31; cảnh báo từ 2027-01-30 (BR-SCN-029) |
| Dải BC khi nâng | `BC-NODE-23-01` … `BC-NODE-26-01` (4 mục) |
| Lưu ý | `node-gyp` 13.1.0 và `corepack` 0.36.0 yêu cầu ≥ 22.22.2 → vá trước khi build addon/cài Corepack |
| Môi trường | Ubuntu 26.04 dùng gói `nodejs 22.22.1` (Launchpad), hỗ trợ chuẩn của OS đến 2031-05-29, sau EOL upstream → overlay SCN-NODE-012, trạng thái vá theo changelog (BR-SCN-015) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-005-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `^v22\.`; nguồn cài trong `scan --json` | Như `CHK-NODE-001-01` |
| `CHK-NODE-005-02` | P1 | Xác định trạng thái vá so với 22.23.4 | Tự động | `node_state` v0.1 với mốc online; gói distro: changelog (BR-SCN-015) | Trạng thái ∈ {`ok`, `vulnerable`} ghi vào state | Changelog không ghi CVE → `vulnerable` |
| `CHK-NODE-005-03` | P1 | Kiểm kê ứng dụng và chụp baseline | Tự động | Như `CHK-NODE-001-02`, `CHK-NODE-001-23` | Danh sách ứng dụng; baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-005-04` | P2 | Vá cùng dòng lên ≥ 22.23.4 | Tự động | `node_upgrade` v0.1: gói (`apt-get install --only-upgrade`, `dnf upgrade`, `apk upgrade`), tarball (`node_upgrade_prefix`: `SHASUMS256.txt`, backup + manifest `untar`), nvm theo SCN-NODE-009; `--dry-run` chỉ in lệnh | `$OLD_BIN --version` ≥ v22.23.4 | Gói không bị hạ cấp khi rollback (v0.1) |
| `CHK-NODE-005-05` | P2 | Restart ứng dụng | Tự động | `restart_node_services` v0.1 (unit systemd theo prefix, `pm2 reload all`) | Unit `active`; số tiến trình pm2 `online` bằng trước khi vá | `--no-restart` → finding `high` |
| `CHK-NODE-005-06` | P3 | Nạp thử native addon sau vá (cùng ABI 127) | Tự động | Như `CHK-NODE-001-16` (không cần build lại) | 0 `ERR_DLOPEN_FAILED` | Addon build cho bản patch cũ vẫn dùng được; lỗi là dấu hiệu khác → kiểm log |
| `CHK-NODE-005-07` | P4 | Rà dependency (OSV, `npm audit`) | Tự động | OSV `querybatch`; `npm audit fix` không `--force` trong `fix` (v0.1) | 0 `MAL-*` chưa xử lý; finding Critical có kế hoạch | Như `CHK-NODE-001-21` |
| `CHK-NODE-005-08` | P6 | Health check sau vá | Tự động | BR-SCN-009 so baseline mục 03 | Đạt 6 tiêu chí; không đạt → `ERR-SCN-500-01`, khôi phục prefix (tarball) bằng manifest | Gói apt/dnf không hạ được tự động |
| `CHK-NODE-005-09` | P1 | Lập và duyệt kế hoạch nâng dòng trước 2027-03-31 (BR-SCN-029) | Bán tự động (duyệt) | Như `CHK-NODE-001-07` | Kế hoạch `approved` trước 2027-03-31; đích ∈ {24, 26} | Chọn 24 → lặp lại trước 2028-03-31 |
| `CHK-NODE-005-10` | P2 | (khi nâng) Sao lưu, điều kiện tiên quyết, cài `$NEW` song song, pm2/Corepack | Bán tự động (duyệt) | Như `CHK-NODE-001-08`, `-10`, `-11`, `-12` | Tiêu chí các mục mẫu đạt | Như các mục mẫu |
| `CHK-NODE-005-11` | P3 | (khi nâng) `engines`, BC (22, `$NEW`], `npm ci`, addon, ESM, test, chạy thử staging | Bán tự động (duyệt) | Như `CHK-NODE-001-13` … `-19` | Tiêu chí các mục mẫu đạt | `require(esm)` mặc định ở 23+ đổi hành vi nạp module |
| `CHK-NODE-005-12` | P4 | (khi nâng) Nâng dependency và framework | Bán tự động (duyệt) | Như `CHK-NODE-001-21`, `-22` | 0 vi phạm `engines`; OSV 0 Critical | Như mục mẫu |
| `CHK-NODE-005-13` | P5 | (khi nâng) Baseline, canary, chuyển từng ứng dụng | Bán tự động (duyệt) | Như `CHK-NODE-001-23` … `-25` | 100% ứng dụng `DONE`/`WAIVED` trước 2027-04-30 | Trễ hạn → ứng dụng chạy dòng `EOL` |
| `CHK-NODE-005-14` | P6 | (khi nâng) Health check, kiểm thử nghiệp vụ, cron và pm2 startup | Bán tự động (duyệt) | Như `CHK-NODE-001-26` … `-28` | Đạt BR-SCN-009; script startup pm2 dùng `$NEW_PREFIX` | Như mục mẫu |
| `CHK-NODE-005-15` | P7 | (khi nâng) Thống kê deprecation, cập nhật tệp ghim, gỡ 22 | Bán tự động (duyệt) | Như `CHK-NODE-001-30` … `-32` | `$OLD_BIN` không còn; 0 tham chiếu `22` trong tệp ghim | Như mục mẫu |

### 10.6 SCN-NODE-006 — Node.js 24
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v24\.\d+\.\d+$` / 90 |
| Trạng thái, LTS, EOL | `MAINTENANCE_LTS` từ 2026-10-20 (LTS Krypton từ 2025-10-28); EOL 2028-04-30, còn 556 ngày → Trung bình; Cao khi < 24.22.1 và có CVE CVSS ≥ 7,0 chưa vá |
| Bản vá tối thiểu | 24.22.1 (2026-10-20, cờ `security`; trùng `NODE_FIXED` v0.1) |
| Đích | Giữ dòng, vá 24.22.1 (24 là đích thay thế của các kịch bản EOL). Nâng lên 26: kế hoạch `approved` trước 2028-03-31; cảnh báo từ 2028-01-31 |
| Dải BC khi nâng | `BC-NODE-25-01`, `BC-NODE-26-01` (2 mục) |
| Lưu ý | `node-gyp` 13.1.0, `corepack` 0.36.0 yêu cầu ≥ 24.15.0 |
| Môi trường | Ubuntu 26.10 dùng gói `nodejs 24.19.0`; Debian forky/sid `24.21.0`/`24.22.0` (tại 2026-10-22) → overlay SCN-NODE-012 |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-006-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `^v24\.` | Như `CHK-NODE-001-01` |
| `CHK-NODE-006-02` | P1 | Xác định trạng thái vá so với 24.22.1 | Tự động | Như `CHK-NODE-005-02` | Trạng thái ∈ {`ok`, `vulnerable`} | Như `CHK-NODE-005-02` |
| `CHK-NODE-006-03` | P1 | Kiểm kê ứng dụng và chụp baseline | Tự động | Như `CHK-NODE-005-03` | Danh sách ứng dụng; baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-006-04` | P2 | Vá cùng dòng lên ≥ 24.22.1 | Tự động | Như `CHK-NODE-005-04` | `$OLD_BIN --version` ≥ v24.22.1 | Như `CHK-NODE-005-04` |
| `CHK-NODE-006-05` | P2 | Restart ứng dụng | Tự động | Như `CHK-NODE-005-05` | Unit `active`; số tiến trình pm2 `online` không đổi | Như `CHK-NODE-005-05` |
| `CHK-NODE-006-06` | P3 | Nạp thử native addon (cùng ABI 137) | Tự động | Như `CHK-NODE-005-06` | 0 `ERR_DLOPEN_FAILED` | Như `CHK-NODE-005-06` |
| `CHK-NODE-006-07` | P4 | Rà dependency (OSV, `npm audit`) | Tự động | Như `CHK-NODE-005-07` | 0 `MAL-*` chưa xử lý | Như `CHK-NODE-001-21` |
| `CHK-NODE-006-08` | P6 | Health check sau vá | Tự động | Như `CHK-NODE-005-08` | Đạt 6 tiêu chí | Như `CHK-NODE-005-08` |
| `CHK-NODE-006-09` | P1 | Hiển thị trạng thái `MAINTENANCE_LTS` (khác mô tả "active LTS" của yêu cầu) và lập kế hoạch nâng trước 2028-03-31 | Bán tự động (duyệt) | BR-SCN-003, BR-SCN-029 | Màn hình ghi `MAINTENANCE_LTS` từ 2026-10-20; kế hoạch `approved` trước 2028-03-31 | Hiểu nhầm 24 còn active → hiển thị ngày chuyển pha |
| `CHK-NODE-006-10` | P2 | (khi nâng) Sao lưu, điều kiện tiên quyết, cài 26 song song, pm2/Corepack | Bán tự động (duyệt) | Như `CHK-NODE-001-08`, `-10`, `-11`, `-12` | Tiêu chí các mục mẫu đạt | Như mục mẫu |
| `CHK-NODE-006-11` | P3 | (khi nâng) `engines`, BC (24, 26], `npm ci`, addon (ABI 137 → 147), test, chạy thử | Bán tự động (duyệt) | Như `CHK-NODE-001-13` … `-19` | Tiêu chí các mục mẫu đạt | Xoá `fs.F_OK`… (25), `writeHeader()` (26) |
| `CHK-NODE-006-12` | P4 | (khi nâng) Nâng dependency và framework | Bán tự động (duyệt) | Như `CHK-NODE-001-21`, `-22` | 0 vi phạm `engines`; OSV 0 Critical | Như mục mẫu |
| `CHK-NODE-006-13` | P5 | (khi nâng) Baseline, canary, chuyển từng ứng dụng | Bán tự động (duyệt) | Như `CHK-NODE-001-23` … `-25` | 100% ứng dụng `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-NODE-006-14` | P6 | (khi nâng) Health check, kiểm thử nghiệp vụ, cron và pm2 startup | Bán tự động (duyệt) | Như `CHK-NODE-001-26` … `-28` | Đạt BR-SCN-009 | Như mục mẫu |
| `CHK-NODE-006-15` | P7 | (khi nâng) Thống kê deprecation, cập nhật tệp ghim, gỡ 24 | Bán tự động (duyệt) | Như `CHK-NODE-001-30` … `-32` | `$OLD_BIN` không còn | Như mục mẫu |

### 10.7 SCN-NODE-007 — Node.js 26
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^v26\.\d+\.\d+$` / 100 |
| Trạng thái, LTS, EOL | `CURRENT` đến 2026-10-27, `ACTIVE_LTS` từ 2026-10-28 (khớp `schedule.json` và endoflife.date), `MAINTENANCE_LTS` từ 2027-10-20 theo `schedule.json` (endoflife.date ghi 2027-10-27; tool dùng `schedule.json` theo BR-SCN-002); EOL 2029-04-30 → Thấp; Cao khi < 26.12.1 và có CVE CVSS ≥ 7,0 chưa vá |
| Bản vá tối thiểu | 26.12.1 (2026-10-21, cờ `security`; trùng `NODE_FIXED` v0.1) |
| Đích | Giữ dòng (đích mặc định của các kịch bản khác). Dòng 27 chỉ thành ứng viên khi thoả BR-SCN-006 (a): từ 2027-10-06 (LTS dự kiến 2027-10-20 − 14 ngày) |
| Lưu ý | Ứng dụng production chỉ được chuyển **sang** 26 từ 2026-10-28 (BR-SCN-007); ứng dụng đã chạy 26 trước mốc này được giữ và vá |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-007-01` | P1 | Xác minh phiên bản, nguồn cài, npm đi kèm | Tự động | Như `CHK-NODE-001-01` | Chuỗi khớp `^v26\.` | Như `CHK-NODE-001-01` |
| `CHK-NODE-007-02` | P1 | Xác định trạng thái vá so với 26.12.1 | Tự động | Như `CHK-NODE-005-02` | Trạng thái ∈ {`ok`, `vulnerable`} | Như `CHK-NODE-005-02` |
| `CHK-NODE-007-03` | P1 | Tính lại pha hỗ trợ theo ngày chạy | Tự động | BR-SCN-003 với `schedule.json` | Trước 2026-10-28: `CURRENT`; từ 2026-10-28: `ACTIVE_LTS` | Snapshot offline cũ → BR-SCN-002 |
| `CHK-NODE-007-04` | P1 | Kiểm kê ứng dụng và chụp baseline | Tự động | Như `CHK-NODE-005-03` | Danh sách ứng dụng; baseline đủ trường | Như `CHK-NODE-001-23` |
| `CHK-NODE-007-05` | P2 | Vá cùng dòng lên ≥ 26.12.1 | Tự động | Như `CHK-NODE-005-04` | `$OLD_BIN --version` ≥ v26.12.1 | Như `CHK-NODE-005-04` |
| `CHK-NODE-007-06` | P2 | Restart ứng dụng | Tự động | Như `CHK-NODE-005-05` | Unit `active`; số tiến trình pm2 `online` không đổi | Như `CHK-NODE-005-05` |
| `CHK-NODE-007-07` | P3 | Nạp thử native addon (cùng ABI 147) | Tự động | Như `CHK-NODE-005-06` | 0 `ERR_DLOPEN_FAILED` | Như `CHK-NODE-005-06` |
| `CHK-NODE-007-08` | P4 | Rà dependency (OSV, `npm audit`) | Tự động | Như `CHK-NODE-005-07` | 0 `MAL-*` chưa xử lý | Như `CHK-NODE-001-21` |
| `CHK-NODE-007-09` | P6 | Health check sau vá | Tự động | Như `CHK-NODE-005-08` | Đạt 6 tiêu chí | Như `CHK-NODE-005-08` |
| `CHK-NODE-007-10` | P7 | Thống kê `DeprecationWarning` (vd `module.register()`) để chuẩn bị cho dòng sau | Tự động | Như `CHK-NODE-001-30` | Báo cáo theo mã DEP | Deprecation runtime của 26 có thể bị xoá ở 27 |
| `CHK-NODE-007-11` | P1 | Đánh giá lại ứng viên 27 từ 2027-10-06 | Tự động | BR-SCN-006 theo lịch `sync` | Ứng viên 27 chỉ hiển thị khi thoả (a)–(d) | Lịch mới của dòng 27 có thể đổi → dùng `schedule.json` mới nhất |

### 10.8 SCN-NODE-008 — Pre-release và chuỗi phiên bản bất thường
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | Điều kiện (1) của BR-SCN-020 / 10 |
| Trạng thái | `PRE_RELEASE` (bản nightly, `-rc.N`, `-pre`, alpha của dòng 27 dự kiến từ 2026-10-28) hoặc `UNKNOWN` (chuỗi lạ, major lớn hơn dữ liệu, không đọc được trong 10 s); phát `ERR-SCN-422-01`, khoá mục `AUTO` thay đổi hệ thống (BR-SCN-013) |
| Bối cảnh | Từ dòng 27, Node.js có giai đoạn alpha trước GA (27 alpha 2026-10-28, GA dự kiến 2027-04-22) và không còn dòng lẻ (common §7 mục 4) |
| Đích | Không đề xuất tự động; ứng dụng production hạ về 26 (từ 2026-10-28) hoặc 24 (BR-SCN-007) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-008-01` | P1 | Ghi chuỗi phiên bản thô và thông tin build | Tự động | `$OLD_BIN --version`; `$OLD_BIN -p "process.release"`; `$OLD_BIN -p "process.versions"` (timeout 10 s mỗi lệnh) | Chuỗi, `process.release.name`, `process.versions.modules` lưu vào state; `ERR-SCN-422-01` hiển thị | Lệnh treo → kill sau 10 s, ghi `timeout` |
| `CHK-NODE-008-02` | P1 | Khoá tự động hoá cho binary (BR-SCN-013) | Tự động | Cờ `locked` trong state | Job `fix`/`upgrade`/`switch` trên binary trả `SKIPPED` | Như `CHK-PHP-005-02` (phụ lục PHP) |
| `CHK-NODE-008-03` | P1 | Định danh file thực thi và nguồn | Tự động | `readlink -f`; `file`; `sha256sum`; `dpkg -S`/`rpm -qf`; so SHA-256 với `SHASUMS256.txt` của bản tương ứng trên `nodejs.org/download/nightly/` hoặc `/rc/` (khi có) | Kết luận `official`/`modified`/`unknown` | `modified` → mở sự cố bảo mật (mục 04) |
| `CHK-NODE-008-04` | P1 | Mở sự cố khi binary bị sửa đổi | Thủ công | Quy trình ứng cứu sự cố của tổ chức; sao lưu binary làm bằng chứng | Mã sự cố ghi vào kế hoạch | Xoá binary trước khi lưu bằng chứng |
| `CHK-NODE-008-05` | P1 | Liệt kê ứng dụng dùng binary, phân loại công khai/nội bộ | Tự động | Như `CHK-NODE-001-02`; công khai = lắng nghe trên IP không thuộc RFC 1918/loopback hoặc sau reverse proxy công khai | Danh sách + cờ `public`; ưu tiên Nghiêm trọng khi ≥ 1 ứng dụng công khai | Phân loại sai → sửa cờ có duyệt |
| `CHK-NODE-008-06` | P1 | Chọn phương án: hạ về 26/24 cho ứng dụng công khai; giữ nội bộ có duyệt | Bán tự động (duyệt) | BR-SCN-007; FEAT-040 | Kế hoạch `approved` ghi phương án từng ứng dụng | Giữ pre-release cho ứng dụng công khai → `ERR-SCN-409-02` |
| `CHK-NODE-008-07` | P2 | Cài dòng đích song song | Bán tự động (duyệt) | Như `CHK-NODE-001-11`, `-12` | `$NEW_BIN --version` khớp `^v(24\|26)\.` | Như mục mẫu |
| `CHK-NODE-008-08` | P3 | `engines`, `npm ci`, addon, test bằng dòng đích | Bán tự động (duyệt) | Như `CHK-NODE-001-13`, `-15`, `-16`, `-18` | Tiêu chí mục mẫu đạt | Mã dùng API chỉ có ở pre-release → sửa trước khi chuyển |
| `CHK-NODE-008-09` | P5 | Baseline, chuyển từng ứng dụng sang dòng đích | Bán tự động (duyệt) | Như `CHK-NODE-001-23` … `-25` | 100% ứng dụng công khai `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-NODE-008-10` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí | Như mục mẫu |
| `CHK-NODE-008-11` | P6 | Xác minh thủ công và gán lại phiên bản (khi binary là bản phát hành chính thức bị nhận sai) | Bán tự động (duyệt) | Người vận hành nhập phiên bản + bằng chứng ≥ 20 ký tự | Bản ghi audit; runtime được gán kịch bản ≠ SCN-NODE-008 | Gán sai → chạy lại mục 03 |
| `CHK-NODE-008-12` | P7 | Gỡ binary pre-release khỏi máy production sau 14 ngày không dùng; gỡ cờ `locked`; chạy lại `scan` | Bán tự động (duyệt) | §8 A4; `scan --json` | Không còn runtime gán SCN-NODE-008 trên production | Mất rollback về pre-release (chủ đích) |

### 10.9 SCN-NODE-009 — Node.js cài qua nvm
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; đường dẫn khớp `*/.nvm/versions/node/v<ver>/bin/node` (v0.1 dò `/root/.nvm` và `/home/*/.nvm`) / `match_order` 500 |
| Đặc điểm | nvm (bản hiện hành v0.40.8) là script shell theo từng người dùng, cài Node vào `$NVM_DIR/versions/node/v<ver>`; mỗi bản patch là 1 thư mục riêng → cài song song tự nhiên. v0.1 chỉ in hướng dẫn `nvm install <major> && nvm alias default <major>` |
| Rủi ro riêng | Ứng dụng khởi động qua shell đăng nhập phụ thuộc `nvm alias default`; script startup pm2 chứa `PATH` của thư mục nvm (ví dụ chính thức `env PATH=$PATH:/home/<user>/.nvm/versions/node/v22.0.0/bin pm2 startup systemd`) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-009-01` | P1 | Xác định người dùng sở hữu và `NVM_DIR` | Tự động | `stat -c %U <path>`; `NVM_DIR` = phần đường dẫn trước `/versions/node/`; `su - <user> -c '. "$NVM_DIR/nvm.sh" && nvm --version'` | Người dùng, `NVM_DIR`, phiên bản nvm lưu vào state | `nvm.sh` không có → coi như tarball (SCN-NODE-010) |
| `CHK-NODE-009-02` | P1 | Ghi alias mặc định và các bản đã cài | Tự động | `nvm alias default`; `nvm ls` (dưới quyền người dùng) | Giá trị alias và danh sách bản lưu vào state | Alias trỏ `lts/*` tự đổi khi cài bản mới |
| `CHK-NODE-009-03` | P1 | Tìm ứng dụng và script startup dùng đường dẫn nvm | Tự động | Unit/pm2 có `$NVM_DIR` trong `ExecStart`/`interpreter`/`PATH`; `systemctl cat pm2-<user>` | Danh sách ứng dụng phụ thuộc đường dẫn nvm | Ứng dụng chạy qua `nvm use` trong script riêng → khai báo thủ công |
| `CHK-NODE-009-04` | P2 | Vá cùng major qua nvm (thay cho cảnh báo của v0.1) | Bán tự động (duyệt) | Dưới quyền người dùng: `nvm install <major> --reinstall-packages-from=<bản cũ>` | Thư mục `v<patch mới>` tồn tại; `node --version` của thư mục mới ≥ bản vá tối thiểu | Chạy dưới root làm sai quyền thư mục → luôn `su - <user>` |
| `CHK-NODE-009-05` | P2 | (khi nâng major) Cài dòng đích qua nvm | Bán tự động (duyệt) | `nvm install <NEW> --reinstall-packages-from=<bản cũ>` | Thư mục bản đích tồn tại; `--version` khớp `^v<NEW>\.` | Gói global có native addon phải build lại (BR-SCN-022) |
| `CHK-NODE-009-06` | P5 | Trỏ ứng dụng sang đường dẫn tuyệt đối của bản mới (BR-SCN-027) | Bán tự động (duyệt) | Drop-in systemd hoặc `interpreter` pm2 = `$NVM_DIR/versions/node/v<ver>/bin/node` | `readlink /proc/<pid>/exe` = đường dẫn mới | Dùng `nvm use` trong unit → không xác định được bản → không cho phép |
| `CHK-NODE-009-07` | P6 | Cập nhật script startup pm2 của người dùng | Bán tự động (duyệt) | `pm2 unstartup`; `env PATH=$PATH:<thư mục bin mới> pm2 startup systemd -u <user> --hp <home>`; `pm2 save` | `systemctl cat pm2-<user>` chứa thư mục bin mới | Bỏ qua → sau reboot chạy bản cũ |
| `CHK-NODE-009-08` | P6 | Đặt alias mặc định sang bản mới | Bán tự động (duyệt) | `nvm alias default <major hoặc patch mới>` | Shell đăng nhập mới của người dùng: `node --version` = bản mới | Script cá nhân khác của người dùng đổi theo → thông báo người dùng |
| `CHK-NODE-009-09` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí | Như mục mẫu |
| `CHK-NODE-009-10` | P7 | Gỡ bản cũ sau 14 ngày không dùng | Bán tự động (duyệt) | `tar -czf` thư mục bản cũ vào backup; `nvm uninstall <bản cũ>` | Thư mục bản cũ không còn; bản nén có SHA-256 | Mất rollback 1 lệnh |
| `CHK-NODE-009-11` | P7 | Kiểm tra mọi lệnh nvm đã chạy dưới đúng người dùng | Tự động | Audit log (FEAT-092): `uid` của từng lệnh | 100% lệnh nvm có `uid` = người dùng sở hữu | Mục chỉ đọc, không thay đổi hệ thống |

### 10.10 SCN-NODE-010 — Node.js cài từ tarball
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; không có gói sở hữu, `$PREFIX/lib/node_modules/npm` tồn tại (điều kiện của v0.1 `node_upgrade`), không thuộc nvm/aaPanel / `match_order` 510 |
| Đặc điểm | v0.1 vá cùng major **tại chỗ**: tải tarball cùng major, kiểm `SHASUMS256.txt`, nén `bin`, `include`, `lib/node_modules/npm`, `lib/node_modules/corepack`, `share/doc/node` vào backup (manifest `untar`), giải nén đè `--strip-components=1`. v2 giữ cách này cho vá cùng major; nâng major luôn dùng prefix mới (BR-SCN-026) |
| Kiến trúc hỗ trợ | Theo v0.1: `x86_64`→`x64`, `aarch64`→`arm64`, `armv7l`, `ppc64le`, `s390x`; khác → không tự động |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-010-01` | P1 | Xác định prefix, kiến trúc, chủ sở hữu | Tự động | `${bin%/bin/node}`; `uname -m`; `stat -c '%U %a' <prefix>` | Prefix, `arch`, chủ, quyền lưu vào state | Prefix là `/usr/local` dùng chung với phần mềm khác → không xoá prefix ở P7 |
| `CHK-NODE-010-02` | P1 | Đếm ứng dụng dùng chung prefix | Tự động | Như `CHK-NODE-001-02` lọc theo prefix | Số ứng dụng theo prefix | Vá tại chỗ ảnh hưởng mọi ứng dụng cùng prefix → restart tất cả |
| `CHK-NODE-010-03` | P2 | Vá cùng major tại chỗ (kế thừa `node_upgrade_prefix`) | Tự động | Tải `node-v<ver>-linux-<arch>.tar.xz` + `SHASUMS256.txt`; `sha256sum -c`; backup + manifest `untar`; giải nén `--strip-components=1 --no-same-owner` | `$PREFIX/bin/node --version` ≥ bản vá tối thiểu; manifest có dòng `untar` | Dòng ≥ 25 không còn Corepack trong tarball → thư mục `corepack` cũ còn lại; tool ghi finding `low` |
| `CHK-NODE-010-04` | P2 | Restart và health check sau vá | Tự động | `restart_node_services`; BR-SCN-009 | Unit `active`; đạt 6 tiêu chí; không đạt → giải nén lại bản sao lưu (manifest `untar`) | Như `CHK-NODE-005-08` |
| `CHK-NODE-010-05` | P2 | (khi nâng major) Cài prefix mới có phiên bản trong tên | Bán tự động (duyệt) | Như `CHK-NODE-001-11` (E1); không giải nén major khác đè prefix cũ | Prefix mới tồn tại; prefix cũ không đổi (SHA-256 của `bin/node` cũ giữ nguyên) | Giải nén đè major khác làm hỏng mọi ứng dụng cùng prefix |
| `CHK-NODE-010-06` | P3 | (khi nâng major) `engines`, BC, `npm ci`, addon, test | Bán tự động (duyệt) | Như `CHK-NODE-001-13` … `-19` | Tiêu chí mục mẫu đạt | Như mục mẫu |
| `CHK-NODE-010-07` | P5 | (khi nâng major) Chuyển từng ứng dụng sang prefix mới (BR-SCN-027) | Bán tự động (duyệt) | Như `CHK-NODE-001-23` … `-25` | 100% ứng dụng `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-NODE-010-08` | P6 | (khi nâng major) Health check, cron, pm2 startup | Bán tự động (duyệt) | Như `CHK-NODE-001-26`, `-28` | Đạt BR-SCN-009; 0 cron gọi `$OLD_BIN` | Như mục mẫu |
| `CHK-NODE-010-09` | P7 | Đổi liên kết mặc định (`/usr/local/bin/node`) sang prefix mới — chỉ khi người vận hành chọn (ngoại lệ BR-SCN-012) | Bán tự động (duyệt) | `ln -sfn`; manifest `copy`/`note` liên kết cũ | `readlink -f /usr/local/bin/node` = `$NEW_BIN` | Script không khai báo đường dẫn tuyệt đối đổi phiên bản theo |
| `CHK-NODE-010-10` | P7 | Gỡ prefix cũ sau 14 ngày không dùng | Bán tự động (duyệt) | `tar -czf` prefix vào backup rồi xoá (không áp dụng khi prefix là `/usr/local`) | Prefix cũ không còn; bản nén có SHA-256 | Mất rollback 1 lệnh |
| `CHK-NODE-010-11` | P7 | Theo dõi bản patch mới cho prefix tarball | Tự động | Mỗi lần `sync` so `--version` với chỉ mục phát hành | Finding xuất hiện ≤ 6 giờ 15 phút sau khi có bản mới (KR1.1) | Không có kho gói → phụ thuộc lịch `sync` |

### 10.11 SCN-NODE-011 — Node.js từ NodeSource
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; gói `nodejs` có nguồn `deb.nodesource.com` (`apt-cache policy nodejs`) hoặc `rpm.nodesource.com` / `match_order` 520 |
| Đặc điểm (script `setup_<major>.x` tại 2026-10-22) | Ghi `/etc/apt/sources.list.d/nodesource.sources` (deb822, `URIs: https://deb.nodesource.com/node_<major>.x`, `Suites: nodistro`), khoá `/usr/share/keyrings/nodesource.gpg`, pin `Pin-Priority: 600` tại `/etc/apt/preferences.d/nodejs`; chỉ hỗ trợ `amd64`, `arm64`; `setup_26.x` tồn tại (HTTP 200). Một hệ thống chỉ có 1 gói `nodejs` → không cài 2 major bằng NodeSource |
| Vá cùng major | Kế thừa v0.1 `node_upgrade` (gói dpkg/rpm) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-011-01` | P1 | Xác định gói, kho, major của kho | Tự động | `dpkg-query -W -f='${Version}' nodejs`; `apt-cache policy nodejs`; đọc `URIs` trong `nodesource.sources` (hoặc `nodesource.list` của script cũ); RPM: `rpm -q --qf '%{VERSION}-%{RELEASE}' nodejs` + file `.repo` | Phiên bản gói, major của kho (`node_<major>.x`) lưu vào state | Kho và binary khác major (đã đổi kho nhưng chưa nâng) → finding `medium` |
| `CHK-NODE-011-02` | P1 | Kiểm tra kiến trúc được NodeSource hỗ trợ | Tự động | `dpkg --print-architecture` | `amd64` hoặc `arm64`; khác → không đề xuất NodeSource, dùng tarball | Mục chỉ đọc, không thay đổi hệ thống |
| `CHK-NODE-011-03` | P2 | Vá cùng major qua kho NodeSource | Tự động | `apt-get update`; `apt-get install -y -q --only-upgrade nodejs`; RPM: `dnf -y upgrade nodejs`; manifest `note` | `node --version` ≥ bản vá tối thiểu | Gói không bị hạ cấp khi rollback |
| `CHK-NODE-011-04` | P2 | Restart và health check sau vá | Tự động | `restart_node_services`; BR-SCN-009 | Unit `active`; đạt 6 tiêu chí | Như `CHK-NODE-005-08` |
| `CHK-NODE-011-05` | P2 | (khi nâng major) Cài dòng đích bằng tarball song song (BR-SCN-026) | Bán tự động (duyệt) | Như `CHK-NODE-001-11` | `$NEW_BIN --version` khớp `^v<NEW>\.`; gói `nodejs` không đổi | Đổi kho NodeSource trước khi chuyển ứng dụng → mọi ứng dụng đổi major cùng lúc (cấm) |
| `CHK-NODE-011-06` | P3 | (khi nâng major) `engines`, BC, `npm ci`, addon, test | Bán tự động (duyệt) | Như `CHK-NODE-001-13` … `-19` | Tiêu chí mục mẫu đạt | Như mục mẫu |
| `CHK-NODE-011-07` | P5 | (khi nâng major) Chuyển từng ứng dụng sang `$NEW_BIN` của tarball | Bán tự động (duyệt) | Như `CHK-NODE-001-23` … `-25` | 100% ứng dụng `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-NODE-011-08` | P6 | (khi nâng major) Health check, cron, pm2 startup | Bán tự động (duyệt) | Như `CHK-NODE-001-26`, `-28` | Đạt BR-SCN-009 | Như mục mẫu |
| `CHK-NODE-011-09` | P7 | Đổi kho NodeSource sang `node_<NEW>.x` và nâng gói khi không còn ứng dụng dùng `/usr/bin/node` cũ | Bán tự động (duyệt) | Manifest `copy` file kho; sửa `URIs`; `apt-get update`; `apt-get install -y nodejs` | `/usr/bin/node --version` khớp `^v<NEW>\.` | Còn script hệ thống gọi `/usr/bin/node` → kiểm `grep -rl /usr/bin/node /etc/cron* /etc/systemd/system` trước |
| `CHK-NODE-011-10` | P7 | (tuỳ chọn) Chuyển ứng dụng từ tarball về `/usr/bin/node` của gói để nhận vá tự động, rồi gỡ prefix tarball | Bán tự động (duyệt) | BR-SCN-027 + health check; `tar -czf` prefix rồi xoá | 100% ứng dụng dùng `/usr/bin/node`; prefix tarball không còn | Thêm 1 lần restart cho mỗi ứng dụng |
| `CHK-NODE-011-11` | P7 | (khi bỏ NodeSource) Gỡ file kho, khoá, pin | Bán tự động (duyệt) | Manifest `copy` rồi xoá `nodesource.sources`, `/usr/share/keyrings/nodesource.gpg`, `/etc/apt/preferences.d/nodejs`, `/etc/apt/preferences.d/nsolid`; `apt-get update` | `apt-cache policy nodejs` không còn nguồn `deb.nodesource.com` | Gói `nodejs` hiện tại không còn nhận vá → chỉ làm khi không còn dùng gói |

### 10.12 SCN-NODE-012 — Node.js từ gói distro
| Thuộc tính | Giá trị |
| :--- | :--- |
| Loại / điều kiện | `OVERLAY`; gói `nodejs` thuộc kho OS (Debian/Ubuntu, RHEL AppStream, Alpine) / `match_order` 530 |
| Gói theo OS (2026-10-22) | Debian 11 `12.22.12`, 12 `18.20.4`, 13 `20.19.2`; Ubuntu 20.04 `10.19.0`, 22.04 `12.22.9`, 24.04 `18.19.1` (chỉ pocket Release), 25.10 `20.19.4`, 26.04 `22.22.1`, 26.10 `24.19.0` (sources.debian.org, Launchpad). RHEL AppStream: chưa kiểm chứng trong phiên này |
| Vấn đề | Số phiên bản upstream cũ hoặc đã `EOL` nhưng có thể được distro vá (Debian `18.20.4+dfsg-1~deb12u2`); ngược lại gói ở universe có thể không nhận bản vá (Ubuntu 24.04 không có bản ở Security/Updates) → trạng thái vá theo changelog/tracker (BR-SCN-015), không theo số upstream |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-NODE-012-01` | P1 | Xác định gói, phiên bản gói, kho | Tự động | `dpkg-query -W -f='${Version}' nodejs` + `apt-cache policy nodejs`; `rpm -q nodejs`; `apk info -v nodejs` | Phiên bản gói và nguồn kho lưu vào state | Mục chỉ đọc, không thay đổi hệ thống |
| `CHK-NODE-012-02` | P1 | Xác định OS và hạn hỗ trợ OS | Tự động | Như `CHK-PHP-015-02` (phụ lục PHP 8.x) | Mốc hỗ trợ thường/mở rộng trong state | OS không có trong endoflife.date → `unknown` |
| `CHK-NODE-012-03` | P1 | Đối chiếu CVE với changelog gói | Tự động | `zcat /usr/share/doc/nodejs/changelog.Debian.gz \| grep -c <CVE>`; `rpm -q --changelog nodejs \| grep -c <CVE>` | Mỗi CVE (KEV hoặc CVSS ≥ 7,0) của dòng có trạng thái `patched`/`unknown` | Changelog không ghi CVE → `unknown` |
| `CHK-NODE-012-04` | P1 | Kiểm tra kênh vá của gói | Tự động | `apt-cache policy nodejs` (có nguồn `-security`/`-updates` không) | Có ≥ 1 kênh vá; nếu không → finding `high` "gói distro không nhận bản vá" | Gói thuộc kho cộng đồng (vd universe) không được vá đều đặn |
| `CHK-NODE-012-05` | P1 | Kiểm tra gói khác phụ thuộc `nodejs` | Tự động | `apt-cache rdepends --installed nodejs`; `rpm -q --whatrequires nodejs` | Danh sách gói phụ thuộc lưu vào state | Gỡ `nodejs` kéo theo gói hệ thống |
| `CHK-NODE-012-06` | P2 | Vá trong kho OS (kế thừa `node_upgrade`) | Tự động | `apt-get install -y -q --only-upgrade nodejs`; `dnf -y upgrade nodejs`; `apk upgrade nodejs`; manifest `note` | Sau nâng: mục 03 cho 100% CVE `patched`, hoặc kho không có bản mới hơn | Gói không bị hạ cấp khi rollback |
| `CHK-NODE-012-07` | P2 | Đề xuất chuyển ứng dụng sang tarball/NodeSource khi gói không có kênh vá hoặc dòng đã `EOL` | Bán tự động (duyệt) | Kết quả mục 03, 04; FEAT-040 | Kế hoạch `approved` hoặc `WAIVED` có lý do | Giữ gói không vá → CVE tồn tại |
| `CHK-NODE-012-08` | P2 | (khi chuyển/nâng) Cài dòng đích bằng tarball song song (BR-SCN-026) | Bán tự động (duyệt) | Như `CHK-NODE-001-11` | `$NEW_BIN --version` khớp `^v<NEW>\.`; gói `nodejs` không đổi | Như mục mẫu |
| `CHK-NODE-012-09` | P5 | (khi chuyển/nâng) `engines`, `npm ci`, addon, test, rồi chuyển từng ứng dụng | Bán tự động (duyệt) | Như `CHK-NODE-001-13` … `-25` | 100% ứng dụng `DONE`/`WAIVED` | Như mục mẫu |
| `CHK-NODE-012-10` | P6 | Health check 10 phút + tự hoàn tác | Tự động | Như `CHK-NODE-001-26` | Đạt 6 tiêu chí | Như mục mẫu |
| `CHK-NODE-012-11` | P7 | Giữ hoặc gỡ gói distro | Bán tự động (duyệt) | `apt-get -s purge nodejs` (mô phỏng) | Chỉ gỡ khi mô phỏng không gỡ kèm gói ngoài `nodejs`/`npm`; nếu giữ, ghi lý do | Gỡ nhầm gói hệ thống |
| `CHK-NODE-012-12` | P7 | Theo dõi trạng thái vá của gói mỗi lần `sync` | Tự động | Lặp lại mục 03, 04 | Finding cập nhật ≤ 6 giờ 15 phút sau khi changelog/tracker thay đổi | Tracker distro chưa tích hợp (Q-04 của PRD) |

## 11. Giả định và câu hỏi mở
| STT | Nội dung | Loại | Người quyết định |
| :--- | :--- | :--- | :--- |
| 1 | Yêu cầu đầu vào ghi Node.js 24 là "active LTS"; dữ liệu chính thức cho thấy 24 vào Maintenance LTS từ 2026-10-20. Tài liệu dùng dữ liệu chính thức và tính trạng thái động (BR-SCN-003) | Sai lệch dữ liệu đã xử lý | PO xác nhận |
| 2 | Yêu cầu glibc tối thiểu của binary chính thức 24/26 chưa kiểm chứng (chỉ có tuyên bố glibc ≥ 2.28 cho dòng 18); tiêu chí là chạy thử `$NEW_BIN --version` | Giả định | QA kiểm trên OS mục tiêu |
| 3 | Không có ma trận chính thức "framework Node.js ↔ dòng Node" tương đương §6 của phụ lục PHP; tool dựa vào `engines.node` của gói (BR-SCN-025) | Ràng buộc | BA |
| 4 | RHEL AppStream module `nodejs` và lệnh CLI aaPanel cho Node.js chưa kiểm chứng; mục tương ứng là `Thủ công` hoặc `Bán tự động` cho tới khi QA chạy thử | Ràng buộc | QA |
| 5 | Ngưỡng staging bắt buộc (BR-SCN-030: ≥ 2 dòng LTS, dòng lẻ, hoặc ≤ 16) là đề xuất của BA | Câu hỏi mở | PO duyệt |
| 6 | Mục "(khi nâng)" ở SCN-NODE-005, 006, 010, 011, 012 gộp nhiều mục mẫu của SCN-NODE-001; khi người vận hành chọn nâng, tool sinh mục con theo mẫu với `chk_id` gốc + hậu tố thứ tự | Ràng buộc thiết kế | Dev |
| 7 | Lịch dòng 27 (alpha 2026-10-28, GA 2027-04-22, LTS 2027-10-20) theo `schedule.json` có thể thay đổi; tool luôn đọc bản mới nhất | Giả định | Tool tự cập nhật |

## 12. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22.

| Nguồn | URL | Dùng cho |
| :--- | :--- | :--- |
| Quy ước chung của phụ lục | [version-scenarios-common.md](version-scenarios-common.md) (DOC-SRS-QP-SCN-000) | Trạng thái, ưu tiên, BR-SCN-001..018, ERR-SCN |
| Biên bản làm rõ yêu cầu v2 / PRD | `docs/php-quickpatch/brainstorms/quickpatch-v2-console.md` (DOC-BRS-QP-001); `docs/php-quickpatch/01-prd.md` (DOC-PRD-QP-001) | Phạm vi, FEAT, KR |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `discover_node_bins`, `node_state`, `node_latest`, `node_upgrade`, `node_upgrade_prefix` (`SHASUMS256.txt`, `untar`), `restart_node_services`, `NODE_FIXED`, manifest |
| Node.js Release WG | https://raw.githubusercontent.com/nodejs/Release/main/schedule.json | Lịch LTS/Maintenance/EOL, dòng 27 |
| Chỉ mục bản phát hành | https://nodejs.org/download/release/index.json | Bản mới nhất, ngày, npm, OpenSSL, ABI (`modules`), cờ `security`/`lts` |
| endoflife.date | https://endoflife.date/api/nodejs.json; `/api/ubuntu.json`, `/api/debian.json`, `/api/rhel.json` | Đối chiếu vòng đời Node.js và OS |
| Thông báo Node.js 17 | https://nodejs.org/en/blog/release/v17.0.0 | OpenSSL 3.0, `ERR_OSSL_EVP_UNSUPPORTED`, `--openssl-legacy-provider` |
| Thông báo Node.js 18 | https://nodejs.org/en/blog/announcements/v18-release-announce | `fetch` toàn cục thử nghiệm, glibc ≥ 2.28 |
| Thông báo Node.js 20 | https://nodejs.org/en/blog/release/v20.0.0 | Permission Model, `url.parse()`, WASI, ABI 115 |
| Thông báo Node.js 21 | https://nodejs.org/en/blog/announcements/v21-release-announce | `fetch`/WebStreams ổn định, WebSocket thử nghiệm |
| Thông báo Node.js 22 | https://nodejs.org/en/blog/release/v22.0.0; https://nodejs.org/en/blog/release/v22.12.0 | WebSocket mặc định, import assertions, `createCipher` EOL, ABI 127; `require(esm)` bỏ cờ từ 22.12.0 |
| Thông báo Node.js 23 | https://nodejs.org/en/blog/release/v23.0.0 | `require(esm)` mặc định, API bị xoá, ABI 131 |
| Thông báo Node.js 24 | https://nodejs.org/en/blog/release/v24.0.0 | npm 11, Undici 7, `--permission`, API bị xoá/deprecated, ABI 137 |
| Thông báo Node.js 25 | https://nodejs.org/en/blog/release/v25.0.0 | `SlowBuffer` EOL, xoá `fs.F_OK`…, Corepack ngừng phân phối, ABI 141 |
| Thông báo Node.js 26 | https://nodejs.org/en/blog/release/v26.0.0 | Temporal, Undici 8.0.2, API bị xoá, GCC 13.2, ABI 147 |
| Lịch phát hành mới | https://nodejs.org/en/blog/announcements/evolving-the-nodejs-release-schedule | Bỏ dòng lẻ từ 27 (common §7 mục 4) |
| npm docs | https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json | Ý nghĩa `lockfileVersion` 1/2/3 |
| npm registry | https://registry.npmjs.org/node-gyp, `/corepack`, `/pm2` | Bản mới nhất và `engines.node` |
| pm2 | https://pm2.keymetrics.io/docs/usage/startup/; https://pm2.keymetrics.io/docs/usage/application-declaration/ | `pm2 unstartup`/`startup` sau khi nâng Node, `pm2 save`, thuộc tính `interpreter` |
| nvm | https://raw.githubusercontent.com/nvm-sh/nvm/master/README.md | v0.40.8, `--reinstall-packages-from`, `nvm alias default` |
| NodeSource | https://raw.githubusercontent.com/nodesource/distributions/master/DEV_README.md; https://deb.nodesource.com/setup_26.x | Kho `nodistro`, file `nodesource.sources`, pin 600, kiến trúc `amd64`/`arm64` |
| Gói distro | https://sources.debian.org/api/src/nodejs/; Launchpad API `getPublishedSources` (`source_name=nodejs`) | Phiên bản `nodejs` theo bản Debian/Ubuntu và pocket |
| Quy tắc nghiệp vụ tổng hợp, SRS chính | [business-rules.md](business-rules.md) (DOC-SRS-QP-BR-001) §1, §2, §6 mục 1; [spec.md](spec.md) (DOC-SRS-QP-001) §2.3, §3.3.2, §3.3.4 | Mẫu cột "Phạm vi áp dụng" `Module / Kênh / Actor`, phạm vi mặc định dải `BR-SCN-020..030`, actor, lệnh CLI, hành động job (§4) |
| Chuẩn tài liệu | `luongkam/openba-kit/skills/srs/SKILL.md`, `rules/02` (§2 Phạm vi áp dụng), `03`, `05`, `09`, `11`, `16`, `18`, `19` | Cấu trúc, mã BR/ERR, metadata |
