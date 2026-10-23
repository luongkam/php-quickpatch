---
id: DOC-SRS-QP-SCN-PHP-001
title: Phụ lục đặc tả — Danh mục kịch bản theo phiên bản PHP (tổng hợp, dữ liệu tham chiếu, SCN-PHP-001..007)
version: 1.0.2
phase: Specification
domain: Security Patch Management
tags: [srs, appendix, scenario, checklist, php, upgrade, breaking-change, compatibility, lifecycle]
depends_on:
  - DOC-BRS-QP-001
  - DOC-PRD-QP-001
  - DOC-SRS-QP-SCN-000
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Phụ lục đặc tả — Danh mục kịch bản theo phiên bản PHP

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo danh mục kịch bản PHP: bảng tổng hợp 16 kịch bản, dữ liệu vòng đời kiểm chứng ngày 2026-10-22, BR-SCN-040..050, danh mục breaking change, ma trận framework/CMS, loader mã hoá, biến thể môi trường, checklist SCN-PHP-001..007 |
| 1.0.1 | 2026-10-22 | BA Agent | BR-SCN-040 phân loại theo chuỗi `PHP_VERSION` thô (pre-release xác định bằng nhánh > GA mới nhất + nguồn pre-release; `-dev`/RC của nhánh đã GA → khoá + overlay SCN-PHP-016) kèm bảng ví dụ kiểm thử; BR-SCN-041 thêm mức `info` cho soft-deprecated; BR-SCN-045/046 và BC-PHP-85-01/02 xử lý OPcache luôn nạp ở 8.5, `__sleep()`/`__wakeup()` soft-deprecated; §7.3 ghim chính xác PHPCompatibility 10.0.0-alpha2 / PHPCompatibilityWP 3.0.0-alpha2 kèm `composer.lock`; §8 E5–E9 trỏ sang PB-007..PB-012 đã kiểm chứng; điều kiện `applies_when` định lượng cho CHK-PHP-001-24, CHK-PHP-002-22 |
| 1.0.2 | 2026-10-22 | BA Agent | Sửa theo review (kiểm chứng ngày 2026-10-23): (1) §4 thêm cột "Phạm vi áp dụng (Module / Kênh / Actor)" cho 11 quy tắc `BR-SCN-040..050` theo rule 02 §2 và business-rules.md §6 mục 1, thêm đoạn quy ước cột; (2) Composer 2.2 LTS cần PHP ≥ 5.3.2 (không phải 5.3.0) ở `BR-SCN-044`, §7.2, SCN-PHP-001/002/003, `CHK-PHP-003-05`; `$OLD` < 5.3.2 chỉ đọc `composer.lock`; (3) `CHK-PHP-004-14` lint theo lô `-n 200` khi `$NEW` ≥ 8.3, bọc lệnh để `xargs` không dừng ở file lỗi đầu tiên (exit 255), tiêu chí theo dòng `Errors parsing`; `BR-SCN-042` (1) và các mục lint dùng cùng tiêu chí; §7.3 ghi số đo; (4) `CHK-PHP-004-24` baseline 5 vòng × 10 s theo DOC-SRS-QP-ENV-002 §4 và `BR-HC-004`; (5) §7.1 mốc loader ionCube 8.3 = 13.3.0, 8.1 = 12.0.1, thêm bảng 7.1.1 Encoder → Loader; (6) SCN-PHP-001 thay cụm định tính về WordPress bằng dải ≤ 3.1.x; §11, §12 bổ sung nguồn. Đánh số 1.0.2 vì 1.0.1 đã dùng |

## 1. Giới thiệu (Introduction)

### 1.1 Mục đích tài liệu (Purpose)
Tài liệu là phần dữ liệu nghiệp vụ cho tính năng "kịch bản + checklist" (FEAT-020, FEAT-022 trong `DOC-PRD-QP-001`) đối với runtime PHP. Mỗi kịch bản cho biết: trạng thái hỗ trợ, nhánh đích khuyến nghị, breaking change phải quét, tác động tới extension / framework / loader mã hoá / Composer, và checklist công việc từ chuẩn bị đến dọn dẹp. Quy ước chung (trạng thái, mức ưu tiên, giai đoạn P1..P7, loại mục, BR-SCN-001..018, ma trận lỗi ERR-SCN) nằm ở [version-scenarios-common.md](version-scenarios-common.md) và không lặp lại ở đây.

| Tài liệu | Mã | Nội dung |
| :--- | :--- | :--- |
| Tài liệu này | DOC-SRS-QP-SCN-PHP-001 | §2 tổng hợp; §3–§9 dữ liệu tham chiếu dùng chung cho mọi kịch bản PHP; §10 kịch bản SCN-PHP-001..007 |
| [version-scenarios-php-8x.md](version-scenarios-php-8x.md) | DOC-SRS-QP-SCN-PHP-002 | Kịch bản SCN-PHP-008..016 (PHP 8.0–8.6, backport distro, tự build) |
| [version-scenarios-node.md](version-scenarios-node.md) | DOC-SRS-QP-SCN-NODE-001 | Danh mục Node.js |

### 1.2 Phạm vi (Scope)
- **Trong phạm vi**: mọi binary PHP mà tool phát hiện (kế thừa `discover_php_bins` của v0.1: `/usr/bin/php*`, `ea-php`, `alt-php`, `remi`, `plesk`, aaPanel, `lsphp`, `/usr/local/php*`), mọi site/vhost ánh xạ tới binary đó (FEAT-004).
- **Ngoài phạm vi**: tool không sửa mã nguồn trên docroot production (DOC-BRS-QP-001 §5.2); Rector chỉ chạy trên bản sao theo BR-SCN-011; không nâng cấp OS hoặc web server khác major.

### 1.3 Định nghĩa bổ sung (Definitions)
Ký hiệu `$OLD`, `$NEW`, `$OLD_BIN`, `$NEW_BIN`, `$SITE`, `$VHOST`, `$TV` theo [version-scenarios-common.md §1.3](version-scenarios-common.md). Bổ sung:

| Ký hiệu | Định nghĩa |
| :--- | :--- |
| `$NEWND` | Nhánh đích bỏ dấu chấm, dùng trong tên gói (vd `85` cho 8.5) |
| `$TOOLS` | Thư mục công cụ quét cô lập `STATE_DIR/tools/php` (PHPCompatibility, PHP_CodeSniffer, Rector, Composer), cài bằng Composer, không đặt trong docroot |
| `$COMPOSER` | Đường dẫn `composer.phar` do tool quản lý (BR-SCN-044) |
| `$COPY` | Bản sao mã nguồn site trên staging hoặc ngoài docroot, dùng cho Rector và nâng dependency |
| `$OWNER` | Người dùng hệ thống sở hữu docroot (v0.1 `run_in_dir_as_owner`) |
| Staging cách ly | Bản sao site không nhận request từ Internet (BR-SCN-007) |

### 1.4 Tài liệu tham chiếu (References)
Xem §12.

## 2. Bảng tổng hợp kịch bản PHP
Dữ liệu trạng thái là ảnh chụp ngày 2026-10-22 (UTC). Khi chạy, tool tính lại theo BR-SCN-003. "Đích" tính theo BR-SCN-005; giá trị trong ngoặc là đích thay thế khi framework/loader giới hạn (§6, §7).

| Mã kịch bản | Loại | Dải phiên bản | Trạng thái (2026-10-22) | EOL (php.net) | Bản cuối / mới nhất | Đích khuyến nghị | Ưu tiên | Số mục checklist | Vị trí |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `SCN-PHP-001` | VERSION | 4.0–4.4 | `EOL` (quá 6.650 ngày) | 2008-08-07 (4.4) | 4.4.9 | 8.5 (8.4) | Nghiêm trọng | 34 | §10.1 |
| `SCN-PHP-002` | VERSION | 5.0–5.2 | `EOL` (quá 5.768 ngày tính từ 5.2) | 2005-09-05 / 2006-08-24 / 2011-01-06 | 5.0.5 / 5.1.6 / 5.2.17 | 8.5 (8.4) | Nghiêm trọng | 34 | §10.2 |
| `SCN-PHP-003` | VERSION | 5.3–5.5 | `EOL` (quá 3.745 ngày tính từ 5.5) | 2014-08-14 / 2015-09-03 / 2016-07-21 | 5.3.29 / 5.4.45 / 5.5.38 | 8.5 (8.4) | Nghiêm trọng | 35 | §10.3 |
| `SCN-PHP-004` | VERSION | 5.6 | `EOL` (quá 2.852 ngày) | 2018-12-31 | 5.6.40 | 8.5 (8.4) | Nghiêm trọng | 33 | §10.4 |
| `SCN-PHP-005` | VERSION | "6.x" và chuỗi bất thường | `UNKNOWN` | Không có (PHP 6 chưa từng phát hành) | — | Không đề xuất tự động | Nghiêm trọng | 13 | §10.5 |
| `SCN-PHP-006` | VERSION | 7.0–7.2 | `EOL` (quá 2.152 ngày tính từ 7.2) | 2019-01-10 / 2019-12-01 / 2020-11-30 | 7.0.33 / 7.1.33 / 7.2.34 | 8.5 (8.4) | Nghiêm trọng | 35 | §10.6 |
| `SCN-PHP-007` | VERSION | 7.3–7.4 | `EOL` (quá 1.424 ngày tính từ 7.4) | 2021-12-06 / 2022-11-28 | 7.3.33 / 7.4.33 | 8.5 (8.4) | Nghiêm trọng | 35 | §10.7 |
| `SCN-PHP-008` | VERSION | 8.0 | `EOL` (quá 1.061 ngày) | 2023-11-26 | 8.0.30 | 8.5 (8.4) | Nghiêm trọng | 32 | [8x §3](version-scenarios-php-8x.md#3-scn-php-008--php-80) |
| `SCN-PHP-009` | VERSION | 8.1 | `EOL` (quá 295 ngày) | 2025-12-31 | 8.1.34 | 8.5 (8.4) | Cao | 33 | [8x §4](version-scenarios-php-8x.md#4-scn-php-009--php-81) |
| `SCN-PHP-010` | VERSION | 8.2 | `SECURITY_ONLY`, còn 70 ngày | 2026-12-31 | 8.2.35 (2026-10-21) | Vá 8.2.35 ngay; nâng 8.5 (8.4) | Cao | 30 | [8x §5](version-scenarios-php-8x.md#5-scn-php-010--php-82) |
| `SCN-PHP-011` | VERSION | 8.3 | `SECURITY_ONLY`, còn 435 ngày | 2027-12-31 | 8.3.36 (2026-10-21) | Vá 8.3.36; nâng 8.5 trước 2027-12-01 | Trung bình (Cao nếu < 8.3.36) | 16 | [8x §6](version-scenarios-php-8x.md#6-scn-php-011--php-83) |
| `SCN-PHP-012` | VERSION | 8.4 | `ACTIVE` đến 2026-12-31, sau đó `SECURITY_ONLY` | 2028-12-31 | 8.4.27 (2026-10-21) | Vá 8.4.27; giữ nhánh | Thấp (Cao nếu < 8.4.27) | 16 | [8x §7](version-scenarios-php-8x.md#7-scn-php-012--php-84) |
| `SCN-PHP-013` | VERSION | 8.5 | `ACTIVE` đến 2027-12-31 | 2029-12-31 | 8.5.12 (2026-10-21) | Vá 8.5.12; giữ nhánh | Thấp (Cao nếu < 8.5.12) | 12 | [8x §8](version-scenarios-php-8x.md#8-scn-php-013--php-85) |
| `SCN-PHP-014` | VERSION | 8.6 pre-release (alpha/beta/RC/`-dev`) | `PRE_RELEASE` (8.6.0RC4 ngày 2026-10-21; GA dự kiến 2026-11-19) | Chưa công bố | 8.6.0RC4 | Không dùng cho production; hạ về 8.5 hoặc chờ 8.6.0 GA | Nghiêm trọng nếu phục vụ site công khai | 13 | [8x §9](version-scenarios-php-8x.md#9-scn-php-014--php-86-pre-release) |
| `SCN-PHP-015` | OVERLAY | Gói distro có backport (dpkg/rpm/apk) | Theo vòng đời OS và tracker distro | Theo OS | Theo changelog gói | Như kịch bản VERSION, ưu tiên gói trong kho OS | Theo BR-SCN-048 | 13 | [8x §10](version-scenarios-php-8x.md#10-scn-php-015--php-gói-distro-có-backport) |
| `SCN-PHP-016` | OVERLAY | Tự build / không thuộc gói / không thuộc panel | Theo nhánh | Theo nhánh | Theo `php -v` | Build lại từ tarball php.net (SHA-256) hoặc chuyển sang gói | Theo nhánh + 1 bậc nếu không xác định được bản vá | 15 | [8x §11](version-scenarios-php-8x.md#11-scn-php-016--php-tự-build-không-thuộc-gói) |

**Tổng**: 14 kịch bản `VERSION`, 2 kịch bản `OVERLAY`, 399 mục checklist.

## 3. Dữ liệu vòng đời PHP đã kiểm chứng (2026-10-22)
Nguồn ưu tiên theo BR-SCN-002: php.net (`supported-versions.php`, `eol.php`, `releases/active.php`, `pre-release-builds.php?format=json`), sau đó `https://endoflife.date/api/php.json`.

| Nhánh | GA | Hết active (php.net) | EOL php.net | EOL endoflife.date | Bản mới nhất php.net | `latest` endoflife.date | Ghi chú |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 4.4 | — | — | 2008-08-07 | Không có bản ghi | 4.4.9 | — | Bản ghi tĩnh trong snapshot (FEAT-010) |
| 5.0 / 5.1 / 5.2 | 2004-07-13 / 2005-11-24 / 2006-11-02 | — | 2005-09-05 / 2006-08-24 / 2011-01-06 | Trùng | 5.0.5 / 5.1.6 / 5.2.17 | Trùng | — |
| 5.3 / 5.4 / 5.5 | 2009-06-30 / 2012-03-01 / 2013-06-20 | — | 2014-08-14 / **2015-09-03** / 2016-07-21 | 2014-08-14 / **2015-09-14** / 2016-07-21 | 5.3.29 / 5.4.45 / 5.5.38 | Trùng | Lệch EOL 5.4 (common §7 mục 2) |
| 5.6 | 2014-08-28 | — | 2018-12-31 | 2018-12-31 | 5.6.40 | 5.6.40 | — |
| 7.0 / 7.1 / 7.2 | 2015-12-03 / 2016-12-01 / 2017-11-30 | — | 2019-01-10 / 2019-12-01 / 2020-11-30 | Trùng | 7.0.33 / 7.1.33 / 7.2.34 | Trùng | — |
| 7.3 / 7.4 | 2018-12-06 / 2019-11-28 | — | 2021-12-06 / 2022-11-28 | Trùng | 7.3.33 / 7.4.33 | Trùng | — |
| 8.0 | 2020-11-26 | 2022-11-26 | 2023-11-26 | 2023-11-26 | 8.0.30 | 8.0.30 | — |
| 8.1 | 2021-11-25 | 2023-11-25 | 2025-12-31 | 2025-12-31 | 8.1.34 | 8.1.34 | — |
| 8.2 | 2022-12-08 | 2024-12-31 | 2026-12-31 | 2026-12-31 | 8.2.35 (21 Oct 2026, `security`) | 8.2.34 | endoflife.date chậm 1 bản |
| 8.3 | 2023-11-23 | 2025-12-31 | 2027-12-31 | 2027-12-31 | 8.3.36 (21 Oct 2026, `security`) | 8.3.35 | Như trên |
| 8.4 | 2024-11-21 | 2026-12-31 | 2028-12-31 | 2028-12-31 | 8.4.27 (21 Oct 2026, `security`) | 8.4.26 | Như trên |
| 8.5 | 2025-11-20 | 2027-12-31 | 2029-12-31 | 2029-12-31 | 8.5.12 (21 Oct 2026, `security`) | 8.5.11 | Như trên |
| 8.6 | GA dự kiến 2026-11-19 (wiki.php.net/todo/php86) | Dự kiến 2028-12-31 | Dự kiến 2030-12-31 | Chưa có | 8.6.0RC4 (21 Oct 2026) | — | Ngày dự kiến suy ra từ RFC `release_cycle_update` (2 năm sửa lỗi + 2 năm bảo mật, kết thúc 31/12, áp dụng từ 8.2); php.net chưa công bố → tool không dùng cho tới khi có trong `supported-versions` |

Hệ quả cho BR-SCN-005 tại 2026-10-22 (hôm nay + 365 ngày = 2027-10-22): 8.5 thoả (a)(b)(c) → đích mặc định; 8.4 thoả (b)(c) → đích thay thế thứ nhất; 8.3 thoả (b)(c) (EOL 2027-12-31) → đích thay thế thứ hai; 8.2 không thoả (c). 8.6 chỉ đủ điều kiện (b) từ 2027-02-17 (GA + 90 ngày) nếu GA đúng 2026-11-19.

## 4. Quy tắc nghiệp vụ riêng PHP (BR-SCN-040..050)
Mỗi BR gồm Tên quy tắc, Phạm vi áp dụng, KHI → THÌ → NGOẠI LỆ (rule 02 §2). Cột "Phạm vi áp dụng" theo mẫu `Module / Kênh / Actor` của [business-rules.md §1](business-rules.md) và quy ước ở [version-scenarios-common.md §4](version-scenarios-common.md): Module là mã module FR; Kênh ∈ {CLI (lệnh con theo [spec.md §3.3.2](spec.md)), console (`SCR-*`), API (`/api/v1`, hành động job theo [spec.md §3.3.4](spec.md))}; Actor theo [spec.md §2.3](spec.md) (`SYS-02` nguồn online, `SYS-03` hạ tầng đích). Cột này thay phạm vi mặc định của dải `BR-SCN-040..050` ở [business-rules.md §2](business-rules.md).

| Mã BR | Tên quy tắc | Phạm vi áp dụng (Module / Kênh / Actor) | KHI (WHEN) | THÌ (THEN) | NGOẠI LỆ (UNLESS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BR-SCN-040` | Gán kịch bản PHP | SCN, SCAN (PHP) / CLI (`scan`, `assess`), console SCR-002, SCR-003 (job `scan`), API (`GET /api/v1/runtimes`, `GET /api/v1/runtimes/{runtime_id}`) / PER-01..03 | Đọc được chuỗi `PHP_VERSION` thô (`$RAW`) bằng `$BIN -n -r 'echo PHP_VERSION;'` trong ≤ 10 s. Phân loại luôn dùng `$RAW` nguyên vẹn; hàm `php_version` của v0.1 (cắt mọi ký tự từ ký tự đầu tiên không phải số/dấu chấm bằng `${v%%[^0-9.]*}`, nên `8.6.0RC4` thành `8.6.0`) chỉ dùng để so sánh số (mốc vá, ứng viên), không dùng để phân loại | Tách `$RAW` theo `^(\d+)\.(\d+)\.(\d+)(.*)$` thành `MAJOR`, `MINOR`, `PATCH`, `SUFFIX`. Loại hậu tố: rỗng → GA; bắt đầu bằng `alpha`, `beta` hoặc `RC` → pre-release; đúng `-dev` → bản dev; bắt đầu bằng `-` và khác `-dev` (phần `PHP_EXTRA_VERSION` do distro/người build thêm, vd `-1ubuntu2.24`) → GA có phiên bản bổ sung; còn lại → bất thường. `GA_MAX` = nhánh `MAJOR.MINOR` lớn nhất có trong dữ liệu vòng đời (php.net `supported-versions`, endoflife.date). Xét theo `match_order`: (1) `MAJOR.MINOR` > `GA_MAX` **và** `pre-release-builds.php?format=json` có khoá cùng `MAJOR.MINOR` mang `release.version` không rỗng và `release.enabled` khác `false` (khoá `enabled` vắng mặt coi là bật; ngày 2026-10-22 chỉ khoá `8.6.0` thoả, `release.version` = `8.6.0RC4`) → SCN-PHP-014, với mọi loại hậu tố; (2) `$RAW` không khớp biểu thức tách, hoặc hậu tố bất thường, hoặc `MAJOR` = 6, hoặc `MAJOR` ≥ 10, hoặc `MAJOR.MINOR` > `GA_MAX` mà không thoả (1) → SCN-PHP-005; (3) so `MAJOR.MINOR.PATCH` (không gồm hậu tố) với `version_match` của SCN-PHP-001..004, 006..013; khi hậu tố là pre-release hoặc `-dev` của nhánh đã GA (vd `8.4.28-dev`, `8.5.13RC1`) → giữ kịch bản theo dải số, thêm overlay SCN-PHP-016 và khoá mọi mục `AUTO` thay đổi hệ thống như BR-SCN-013. Overlay theo nguồn cài: có gói sở hữu (`dpkg -S`, `rpm -qf`, `apk info --who-owns`) → thêm SCN-PHP-015; không có gói sở hữu và đường dẫn không thuộc panel (PB-007..PB-012, §8 E5..E9) → thêm SCN-PHP-016. Ví dụ kiểm thử: bảng 4.1 | Biến môi trường `QP_PHP_BINS` (v0.1) chỉ định binary: vẫn áp quy tắc trên. Không đọc được phiên bản trong 10 s → SCN-PHP-005 (BR-SCN-001) |
| `BR-SCN-041` | Dải breaking change cần quét | CMPT, PLAN (PHP) / CLI (`plan create`, `plan run`), console SCR-004, API (`POST /api/v1/plans`, `GET /api/v1/plans/{plan_id}/compatibility`) / PER-01, PER-02 | Kịch bản cần nâng từ `$OLD` lên `$NEW` | Tập luật quét = mọi mục BC-PHP ở §5 có phiên bản `v` thoả `$OLD < v ≤ $NEW`; mục loại `Xoá` có mức `error`, loại `Đổi hành vi`/`Deprecated` có mức `warning`, phần ghi `Soft-deprecated` (deprecation chỉ ở tài liệu, runtime không phát `E_DEPRECATED`) có mức `info`: chỉ liệt kê trong báo cáo, không tính vào BR-SCN-042 | — |
| `BR-SCN-042` | Điều kiện ĐẠT của quét tương thích | CMPT, PLAN, UPG (PHP) / CLI (`plan create`, `plan run`, `plan waive`, `migrate switch`), console SCR-004, API (`GET /api/v1/plans/{plan_id}/compatibility`, `POST /api/v1/plans/{plan_id}/compatibility-waivers`) / PER-01, PER-02 | Chạy giai đoạn P3 | ĐẠT khi đồng thời: (1) `php -l` bằng `$NEW_BIN` cho 100% file `*.php`, `*.inc`, `*.phtml` (lệnh ở `CHK-PHP-004-14`): 0 dòng `Errors parsing` (dòng này xuất hiện cho mỗi file có `Parse error` hoặc lỗi biên dịch `Fatal error`, vd `Cannot redeclare`) và số dòng `No syntax errors detected` bằng số file; (2) PHPCompatibility 10.x với `--runtime-set testVersion $NEW`: 0 lỗi mức `ERROR`; (3) bộ luật BC (BR-SCN-041): 0 hit mức `error` chưa được miễn trừ. Khi `$OLD` < 7.0, chạy thêm bậc thang `testVersion` 5.6 và 7.4 chỉ để nhóm báo cáo, không dùng để quyết định ĐẠT | Hit nằm trong thư mục do người vận hành khai báo "không triển khai" (vd `tests/`, `docs/`) được loại trừ, phải ghi lý do ≥ 20 ký tự |
| `BR-SCN-043` | Loader mã hoá | ASMT, CMPT, PLAN, UPG (PHP) / CLI (`assess`, `plan create`, `plan run`, `migrate switch`), console SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`) / PER-01, PER-02 | Phát hiện ionCube/SourceGuardian (§7.1) trên site | Loại khỏi danh sách ứng viên mọi nhánh không có loader chính thức (ionCube: không có 8.0, chưa có 8.6 tại 2026-10-22; SourceGuardian: ngoài dải 5.3–8.5); site chỉ được chuyển khi 1 file mã hoá mẫu chạy với `$NEW_BIN` trả exit 0 | Không còn nhánh hợp lệ → `ERR-SCN-409-03` |
| `BR-SCN-044` | Composer và platform | SCAN, CMPT, PLAN (PHP, Composer) / CLI (`scan`, `plan create`, `plan run`), console SCR-004, SCR-005, API (`GET /api/v1/plans/{plan_id}/compatibility`, `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01, PER-02 | Site có `composer.json` | Mọi lệnh Composer chạy dưới quyền `$OWNER` (v0.1). Trên `$OLD` từ 5.3.2 đến < 7.2.5 dùng Composer 2.2 LTS (min PHP 5.3.2 theo getcomposer.org, vá lỗi nghiêm trọng đến 2026-12-31); `$OLD` < 5.3.2 → không chạy Composer trên `$OLD`, kiểm kê chỉ bằng cách đọc `composer.lock` (parser của tool); trên `$NEW` dùng bản 2.x ổn định mới nhất (2.10.3, min PHP 7.2.5). Khi `config.platform.php` có giá trị, cập nhật thành bản patch của `$NEW` trong bản sao trước khi `update`. ĐẠT khi `$NEW_BIN $COMPOSER check-platform-reqs` exit 0 | Dự án không có `composer.lock` → chỉ cảnh báo, không chặn |
| `BR-SCN-045` | Extension tương ứng | CMPT, PLAN, UPG (cài song song, PHP) / CLI (`plan create`, `plan run`, `migrate install --runtime php`), console SCR-004, SCR-011, API (`POST /api/v1/jobs` hành động `migrate_install`, `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01, PER-02, SYS-03 | Cài `$NEW` song song | Với mỗi extension trong `$OLD_BIN -m`: (a) có trong `$NEW_BIN -m` sau cài; hoặc (b) có gói PECL/bên thứ ba cho `$NEW` đã duyệt; hoặc (c) có thay thế trong §5 và mã nguồn không còn gọi hàm của extension (quét theo tiền tố hàm). Thiếu cả 3 → chặn P5 cho site dùng extension đó. Extension `Zend OPcache` khi `$NEW` ≥ 8.5: đánh dấu "tích hợp sẵn" (php.net: từ 8.5 OPcache luôn được biên dịch vào binary và luôn nạp) → coi như thoả (a), không sinh lệnh cài gói extension riêng cho opcache (sự tồn tại của gói `php$NEW-opcache` trên kho 8.5: chưa kiểm chứng) | Extension không được site nào gọi (0 hit tiền tố hàm) → đánh dấu `SKIPPED` |
| `BR-SCN-046` | Sao chép cấu hình ini/pool | CMPT, UPG (PHP) / CLI (`plan create`, `plan run`, `migrate install --runtime php`, `migrate switch`), console SCR-004, SCR-011, API (`POST /api/v1/jobs` hành động `migrate_install`, `migrate_switch`) / PER-01, PER-02, SYS-03 | Tạo pool FPM hoặc ini cho `$NEW` từ cấu hình `$OLD` | Loại bỏ directive đã xoá trong dải: `register_globals`, `register_long_arrays`, `magic_quotes_gpc`, `magic_quotes_runtime`, `magic_quotes_sybase`, `safe_mode*`, `allow_call_time_pass_reference`, `define_syslog_variables`, `y2k_compliance`, `zend.ze1_compatibility_mode` (5.4); `asp_tags`, `always_populate_raw_post_data` (7.0); `sql.safe_mode` (7.2); `track_errors`, `mbstring.func_overload` (8.0); `disable_classes` (8.5). Khi `$NEW` ≥ 8.5, loại thêm dòng nạp OPcache khớp `^\s*zend_extension\s*=\s*"?([^"]*/)?opcache(\.so)?"?\s*$` (vd `zend_extension=opcache`, `zend_extension=opcache.so`, đường dẫn tuyệt đối tới `opcache.so`) trong ini sao chép từ `$OLD` (vd file `conf.d/10-opcache.ini` của Debian), vì 8.5 phát `Warning` cho dòng này; các directive `opcache.*` (vd `opcache.enable`, `opcache.enable_cli`) được giữ. Mỗi directive bị loại được ghi vào báo cáo. ĐẠT khi `php-fpm$NEW -t` (hoặc lệnh kiểm tra của panel) exit 0 và `$NEW_BIN -r 'exit(0);'` không in `Warning`/`Fatal` ra stderr | — |
| `BR-SCN-047` | Site chạy `mod_php` | PLAN, UPG (PHP, `mod_php`) / CLI (`plan create`, `plan run`, `migrate switch`), console SCR-004, SCR-011, API (`POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`, `POST /api/v1/jobs` hành động `migrate_switch`) / PER-01, PER-02, SYS-03 | Site được phục vụ qua Apache `mod_php` (v0.1 `php_sapis_note`) | Trước P5, thêm mục chuyển site sang PHP-FPM của `$OLD` và health check BR-SCN-009 riêng; tool không cấu hình 2 module `mod_php` trong cùng 1 tiến trình Apache | Không chuyển được sang FPM → `ERR-SCN-412-02`, chỉ cho phép phương án máy chủ/container mới (§8 E10) |
| `BR-SCN-048` | Trạng thái gói distro | SCN, ASMT, FEED (PHP, gói distro) / CLI (`scan`, `assess`), console SCR-002, SCR-003, API (`GET /api/v1/runtimes/{runtime_id}/assessment`) / PER-01, PER-02, SYS-02; PER-04 chỉ xem | Kịch bản có overlay SCN-PHP-015 | Hiển thị song song: EOL upstream (php.net) và hạn hỗ trợ của OS (endoflife.date `ubuntu`/`debian`/`rhel`). Trạng thái vá CVE theo BR-SCN-015. Mức ưu tiên tính theo EOL upstream, giảm 1 bậc (không thấp hơn "Trung bình") khi changelog gói xác nhận đã vá mọi CVE KEV và CVSS ≥ 7,0 đã công bố cho nhánh và OS còn trong hạn hỗ trợ | Không đọc được changelog → không giảm bậc |
| `BR-SCN-049` | Hạn duyệt kế hoạch nâng cấp | PLAN (PHP) / CLI (`plan create`, `plan approve`), console SCR-002, SCR-004, API (`GET /api/v1/overview`, `GET /api/v1/plans/{plan_id}`) / PER-01, PER-02; PER-04 chỉ xem cảnh báo | Nhánh ở `SECURITY_ONLY` hoặc còn ≤ 90 ngày tới EOL | Kế hoạch nâng cấp phải ở trạng thái `approved` trước EOL − 30 ngày (với 8.2: trước 2026-12-01, khớp KR2.2); tool hiển thị số ngày còn lại trên màn hình Tổng quan | — |
| `BR-SCN-050` | Bắt buộc staging | PLAN, UPG (PHP) / CLI (`plan create`, `plan run`, `plan item --set waive`), console SCR-004, API (`PATCH /api/v1/plans/{plan_id}/checklist-items/{chk_id}`) / PER-01, PER-02 | `MAJOR($OLD)` < `MAJOR($NEW)` | Mục P3, P4 chạy trên staging cách ly; mục P5 chỉ mở khi P3 ĐẠT (BR-SCN-042) trên staging | Cùng major (vd 8.1 → 8.5): staging là khuyến nghị, người vận hành được miễn trừ có duyệt |

**Bảng 4.1 — Ví dụ kiểm thử BR-SCN-040** (dữ liệu ngày 2026-10-22: `GA_MAX` = 8.5; nguồn pre-release có khoá `8.2.27`, `8.3.31`, `8.4.27`, `8.5.12` với `release.enabled` = `false` và `dev_version` dạng `8.x.y-dev`, khoá `8.6.0` có `release.version` = `8.6.0RC4`). Mỗi dòng là 1 ca kiểm thử bắt buộc của FR-SCN-CLS-001.

| `$RAW` | Loại hậu tố | Bước khớp | Kịch bản `VERSION` | Overlay / khoá | Ghi chú |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `8.6.0RC4` | pre-release | (1) | SCN-PHP-014 | Overlay theo nguồn cài; khoá theo BR-SCN-013 (`PRE_RELEASE`) | v0.1 `php_version` trả `8.6.0`; quy tắc bản 1.0.0 (đòi hậu tố trên giá trị đã cắt) không khớp bước nào với giá trị này → ca hồi quy bắt buộc |
| `8.6.0-dev` | dev | (1) | SCN-PHP-014 | Như trên | Nhánh 8.6 có trong nguồn pre-release |
| `8.4.28-dev` | dev | (3) | SCN-PHP-012 | Thêm SCN-PHP-016; khoá mục `AUTO` thay đổi hệ thống | Không gán SCN-PHP-014 dù nguồn pre-release có khoá `8.4.27` với `dev_version` = `8.4.27-dev` |
| `8.5.13RC1` | pre-release | (3) | SCN-PHP-013 | Thêm SCN-PHP-016; khoá như trên | RC của bản patch thuộc nhánh đã GA |
| `8.4.27` | GA | (3) | SCN-PHP-012 | SCN-PHP-015 khi có gói sở hữu | — |
| `8.1.2-1ubuntu2.24` | GA có phiên bản bổ sung | (3) | SCN-PHP-009 | SCN-PHP-015 | Định dạng `PHP_EXTRA_VERSION` của gói Ubuntu: suy từ tên gói `8.1.2-1ubuntu2.24`, chưa chạy thử trên máy Ubuntu |
| `8.7.0-dev` | dev | (2) | SCN-PHP-005 | Khoá theo BR-SCN-013 | 8.7 > `GA_MAX` và không có trong nguồn pre-release (giá trị giả định cho bản tự build từ nhánh phát triển của php-src) |
| `6.0.0-dev` | dev | (2) | SCN-PHP-005 | Như trên | `MAJOR` = 6 |
| `8.4.27custom` | bất thường | (2) | SCN-PHP-005 | Như trên | Hậu tố không bắt đầu bằng `alpha`/`beta`/`RC`/`-` |

## 5. Danh mục breaking change (BC-PHP)
Cột "Mẫu quét" là luật tĩnh của bộ dữ liệu tool (FEAT-050); "PHPC" = phát hiện bởi PHPCompatibility 10.x; "Runtime" = không phát hiện tĩnh được, dựa vào test (P3) và health check/log (P6). Nguồn: trang migration php.net, php-src `UPGRADING`, php-legacy-docs.zend.com (tham chiếu §12).

| Mã BC | Bản | Thay đổi | Loại | Mẫu quét | Thay thế |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BC-PHP-50-01` | 5.0 | Mô hình đối tượng mới: đối tượng được tham chiếu bằng handle, không còn sao chép theo giá trị khi gán/truyền; hàm trùng tên lớp chỉ là constructor khi khai báo trong chính lớp đó | Đổi hành vi | Runtime; cảnh báo khi thấy `=& new` hoặc gán đối tượng rồi sửa bản sao | `clone` khi cần bản sao |
| `BC-PHP-50-02` | 5.0 | `array_merge()` chỉ nhận mảng; `strrpos()` dùng toàn bộ needle; `ip2long()` trả `false` khi IP sai; khai báo hàm trong file bị include 2 lần gây Fatal | Đổi hành vi | `array_merge\(`, `ip2long\(` so với `-1`; `(include\|require)\s*\(` không có `_once` | Ép `(array)`; so sánh `=== false`; `include_once` |
| `BC-PHP-53-01` | 5.3 | Deprecated: họ `ereg*`/`split()`/`spliti()`/`sql_regcase()`, `session_register()`, `call_user_method()`, `set_magic_quotes_runtime()`, `dl()`, gán `=& new`, truyền tham chiếu lúc gọi, directive `register_globals`/`magic_quotes_*`/`safe_mode` | Deprecated | Tên hàm; `=&\s*new\b` | `preg_*`, `$_SESSION`, `call_user_func()` |
| `BC-PHP-54-01` | 5.4 | Xoá register globals, magic quotes, safe mode; các directive liên quan gây `E_CORE_ERROR` khi khởi động | Xoá | ini: danh sách BR-SCN-046 (5.4); mã: biến request dùng trực tiếp không qua `$_GET`/`$_POST`/`$_REQUEST`/`$_COOKIE` (Runtime) | Đọc superglobal; tự escape bằng prepared statement |
| `BC-PHP-54-02` | 5.4 | Xoá truyền tham chiếu lúc gọi (`f(&$x)`) | Xoá (Fatal) | PHPC; lời gọi có `&\$` trong danh sách đối số (loại trừ dòng `function`) | Khai báo `&` ở chữ ký hàm |
| `BC-PHP-54-03` | 5.4 | Xoá `session_register()`, `session_unregister()`, `session_is_registered()`, `import_request_variables()`, `define_syslog_variables()`; xoá cú pháp `break $var`/`continue $var`; `trait`, `callable`, `insteadof` thành từ khoá | Xoá | Tên hàm; `\b(break\|continue)\s+\$` | `$_SESSION`; hằng số nguyên |
| `BC-PHP-54-04` | 5.4 | `htmlspecialchars()`/`htmlentities()`/`html_entity_decode()` mặc định UTF-8 (trước ISO-8859-1); `TZ` không còn đặt múi giờ | Đổi hành vi | Lời gọi không truyền tham số encoding | Truyền encoding; đặt `date.timezone` |
| `BC-PHP-55-01` | 5.5 | Deprecated `ext/mysql`, modifier `/e` của `preg_replace()`, `mcrypt_ecb/cbc/cfb/ofb()` | Deprecated | `mysql_\w+\(`; `preg_replace` với pattern có `e` trong modifier | `mysqli`/`PDO`; `preg_replace_callback()` |
| `BC-PHP-56-01` | 5.6 | `json_decode()` từ chối `true`/`false`/`null` không viết thường; stream SSL/TLS kiểm tra chứng chỉ peer và tên máy mặc định; GMP thành object; mcrypt yêu cầu key/IV hợp lệ | Đổi hành vi | `file_get_contents\(\s*['"]https`, `stream_context_create` (Runtime) | Cấu hình CA bundle, `openssl.cafile` |
| `BC-PHP-56-02` | 5.6 | Deprecated `$HTTP_RAW_POST_DATA`/`always_populate_raw_post_data`; gọi phương thức non-static từ ngữ cảnh không tương thích | Deprecated | `\$HTTP_RAW_POST_DATA` | `file_get_contents('php://input')` |
| `BC-PHP-70-01` | 7.0 | Xoá extension `ereg`, `mssql`, `mysql`, `sybase_ct` và nhiều SAPI (vd `apache`, `apache2filter`, `isapi`, `nsapi`) | Xoá ext | `\b(mysql_\w+\|ereg\w*\|eregi\w*\|split\|spliti\|sql_regcase\|mssql_\w+\|sybase_\w+)\s*\(` | `mysqli`/`PDO_MySQL`, `preg_*`, `PDO_DBLIB`/`sqlsrv` |
| `BC-PHP-70-02` | 7.0 | Xoá thẻ ASP `<% %>`, `<%=` và `<script language="php">`; xoá ini `asp_tags` | Xoá | `<%`, `<script\s+language\s*=\s*["']?php` | `<?php` |
| `BC-PHP-70-03` | 7.0 | Xoá modifier `/e` (`PREG_REPLACE_EVAL`) | Xoá | `preg_replace\s*\(` với pattern kết thúc bằng modifier chứa `e` | `preg_replace_callback()` |
| `BC-PHP-70-04` | 7.0 | Xoá `call_user_method()`, `call_user_method_array()`, `set_magic_quotes_runtime()`, `mcrypt_generic_end()`, `mcrypt_ecb/cbc/cfb/ofb()`, `$HTTP_RAW_POST_DATA`; `dl()` không dùng được trong PHP-FPM | Xoá | Tên hàm/biến | `call_user_func()`, `mcrypt_generic_deinit()`, `php://input` |
| `BC-PHP-70-05` | 7.0 | Deprecated constructor kiểu PHP 4 (phương thức trùng tên lớp) và gọi tĩnh phương thức non-static | Deprecated | PHPC; `class\s+(\w+)` + `function\s+\1\s*\(` | `__construct()` |
| `BC-PHP-70-06` | 7.0 | Biến gián tiếp đánh giá trái → phải; `list()` gán trái → phải, không rỗng, không unpack chuỗi; `foreach` không đổi con trỏ mảng; literal bát phân sai là Parse error; thay đổi xử lý chia cho 0; `E_STRICT` được phân loại lại; constructor lớp nội tại ném exception khi lỗi | Đổi hành vi | PHPC + `php -l` bằng `$NEW_BIN`; còn lại Runtime | Sửa mã |
| `BC-PHP-71-01` | 7.1 | Gọi hàm thiếu tham số ném `ArgumentCountError` (trước là Warning); `void`, `iterable` không dùng làm tên lớp; deprecated `ext/mcrypt` | Đổi hành vi | PHPC; `mcrypt_\w+\(` | Truyền đủ tham số; `openssl_*`/`sodium_*` |
| `BC-PHP-72-01` | 7.2 | `mcrypt` chuyển khỏi lõi sang PECL | Xoá ext | `mcrypt_\w+\(` | `openssl_*`, `sodium_*` |
| `BC-PHP-72-02` | 7.2 | Deprecated `each()`, `create_function()`, `__autoload()`, `track_errors`/`$php_errormsg`, `(unset)` cast, `parse_str()` 1 tham số, `assert()` với chuỗi, `mbstring.func_overload`, hằng chưa định nghĩa được coi là chuỗi; `count()` trên giá trị không Countable phát Warning; xoá ini `sql.safe_mode` | Deprecated / Đổi hành vi | PHPC; `\beach\s*\(`, `create_function\s*\(`, `function\s+__autoload\b` | `foreach`, closure, `spl_autoload_register()` |
| `BC-PHP-73-01` | 7.3 | Nhãn kết thúc heredoc/nowdoc được nhận khi xuất hiện đầu dòng có thụt lề; `continue` nhắm `switch` phát Warning; deprecated hằng không phân biệt hoa thường (`define(..., true)`), needle không phải chuỗi trong `strpos()` và họ hàm, alias `mbereg*` | Đổi hành vi / Deprecated | PHPC; `define\s*\([^)]*,\s*true\s*\)` | `continue 2`; needle kiểu chuỗi |
| `BC-PHP-74-01` | 7.4 | Deprecated ternary lồng không ngoặc, offset bằng `{}`, `(real)`/`is_real()`, `array_key_exists()` trên object, `get_magic_quotes_gpc/runtime()`, `money_format()`, `hebrevc()`, `convert_cyr_string()`, `ezmlm_hash()`, `restore_include_path()`, `allow_url_include`, `implode()` đảo tham số; truy cập mảng trên giá trị không phải mảng phát Notice; `fn` thành từ khoá | Deprecated | PHPC; `\$\w+\{` | Ngoặc rõ ràng, `[]`, `(float)`, `NumberFormatter` |
| `BC-PHP-74-02` | 7.4 | `interbase` (Firebird còn PDO_Firebird), `recode`, `wddx` chuyển sang PECL | Xoá ext | `ibase_\w+\(`, `recode\w*\(`, `wddx_\w+\(` | `PDO_Firebird`, `iconv`/`mbstring`, JSON |
| `BC-PHP-80-01` | 8.0 | So sánh chuỗi không phải số với số: so sánh như chuỗi (vd `0 == "foo"` thành `false`) | Đổi hành vi | Runtime (PHPC không phát hiện đầy đủ) | `===`, ép kiểu tường minh |
| `BC-PHP-80-02` | 8.0 | Xoá `each()`, `create_function()`, `__autoload()`, `array_key_exists()` trên object, cast `(real)`/`(unset)`, `track_errors`/`$php_errormsg`, `money_format()`, `hebrevc()`, `convert_cyr_string()`, `ezmlm_hash()`, `restore_include_path()`, `get_magic_quotes_gpc/runtime()`, `read_exif_data()`, `gmp_random()`, `imap_header()` | Xoá | PHPC + tên hàm | Như BC-PHP-72-02, BC-PHP-74-01 |
| `BC-PHP-80-03` | 8.0 | Phương thức trùng tên lớp không còn là constructor | Xoá | PHPC; mẫu của BC-PHP-70-05 | `__construct()` |
| `BC-PHP-80-04` | 8.0 | `match` là từ khoá; ternary lồng không ngoặc và offset `{}` thành lỗi biên dịch; `@` không chặn lỗi Fatal; `error_reporting` mặc định `E_ALL`, `display_startup_errors` bật; nhiều Notice/Warning nâng mức (đọc biến/khoá không định nghĩa thành Warning) | Xoá / Đổi hành vi | PHPC; `php -l` | Sửa mã; xem log P6 |
| `BC-PHP-80-05` | 8.0 | Xoá directive `mbstring.func_overload`; nhiều hàm trả object thay resource (vd `curl_init()` → `CurlHandle`, `xml_parser_create()` → `XMLParser`) nên kiểm tra `is_resource()` sai | Xoá / Đổi hành vi | ini; `is_resource\(` | `=== false`, `instanceof` |
| `BC-PHP-80-06` | 8.0 | `xmlrpc` chuyển sang PECL; `call_user_func_array()` hiểu khoá chuỗi là named argument; tham số tuỳ chọn đứng trước tham số bắt buộc bị deprecated | Xoá ext / Đổi hành vi | `xmlrpc_\w+\(`; PHPC | Thư viện userland; mảng đối số có chỉ số số |
| `BC-PHP-81-01` | 8.1 | Deprecated truyền `null` cho tham số non-nullable của hàm built-in (vd `strlen(null)`); chuyển float không nguyên sang int ngầm định; autovivification từ `false` | Deprecated | Runtime (log `Deprecated`) | Kiểm tra `null`, ép kiểu |
| `BC-PHP-81-02` | 8.1 | Lớp con override phương thức lớp nội tại không khai báo kiểu trả về tương thích phát Deprecated; `Serializable` không có `__serialize()`/`__unserialize()` deprecated; hạn chế ghi toàn bộ `$GLOBALS`; `readonly`, `never` thành từ khoá | Deprecated / Xoá | PHPC; `array_\w+\(\s*\$GLOBALS` | `#[\ReturnTypeWillChange]`, `__serialize()` |
| `BC-PHP-81-03` | 8.1 | Deprecated `strftime()`/`gmstrftime()`, `strptime()`, `date_sunrise()`/`date_sunset()`, `FILTER_SANITIZE_STRING`, `mhash*()`, `odbc_result_all()`, `auto_detect_line_endings`, `key()`/`current()`... trên object | Deprecated | Tên hàm/hằng | `IntlDateFormatter`/`date()`, `htmlspecialchars()`, `hash()` |
| `BC-PHP-82-01` | 8.2 | Deprecated tạo dynamic property (trừ lớp có `#[\AllowDynamicProperties]` và `stdClass`) | Deprecated | Runtime + phân tích tĩnh (PHPStan/Rector nếu có) | Khai báo thuộc tính |
| `BC-PHP-82-02` | 8.2 | Deprecated `utf8_encode()`/`utf8_decode()`, nội suy `"${var}"`/`"${expr}"`, callable tương đối (`"self::m"`, `["parent","m"]`, `"static::m"`...), mbstring encoding `QPrint`/`Base64`/`Uuencode`/`HTML-ENTITIES` | Deprecated | `utf8_(en\|de)code\(`; `"\$\{`; PHPC | `mb_convert_encoding()`, `"{$var}"`, `self::m(...)` |
| `BC-PHP-82-03` | 8.2 | `strtolower()`, `strtoupper()`, `stristr()`, `stripos()`, `strripos()`, `lcfirst()`, `ucfirst()`, `ucwords()`, `str_ireplace()` không còn phụ thuộc locale; `str_split('')` trả `[]`; `ksort()` với khoá chuỗi số đổi thứ tự | Đổi hành vi | Runtime | `mb_*` khi cần theo locale |
| `BC-PHP-83-01` | 8.3 | Deprecated `get_class()`/`get_parent_class()` không tham số và tăng/giảm trên giá trị không phải số; `range()` đổi kết quả với chuỗi và ném `ValueError`/`TypeError`; kiểm tra visibility hằng lớp khi kế thừa | Deprecated / Đổi hành vi | PHPC; `get_(parent_)?class\(\s*\)` | `static::class`, `$this::class` |
| `BC-PHP-84-01` | 8.4 | Deprecated tham số nullable ngầm định (`function f(Foo $x = null)`) | Deprecated | PHPC; khai báo có kiểu không bắt đầu bằng `?` và mặc định `= null` | `?Foo $x = null` |
| `BC-PHP-84-02` | 8.4 | Xoá mức lỗi `E_STRICT` (hằng `E_STRICT` deprecated); `exit()` đổi hành vi; hằng của lớp extension có kiểu; deprecated `_` làm tên lớp, `0 ** -n` | Xoá / Deprecated | `E_STRICT`; PHPC | Bỏ `E_STRICT` khỏi `error_reporting` |
| `BC-PHP-84-03` | 8.4 | `imap`, `oci8`, `pdo_oci`, `pspell` chuyển sang PECL | Xoá ext | `imap_\w+\(`, `oci_\w+\(`, `pspell_\w+\(` | PECL hoặc thư viện userland đã duyệt |
| `BC-PHP-85-01` | 8.5 | Deprecated toán tử backtick (alias `shell_exec()`), ép kiểu `(boolean)`/`(integer)`/`(double)`/`(binary)`, kết thúc `case` bằng `;`, `null` làm offset mảng hoặc đối số của `array_key_exists()`, tăng chuỗi không phải số, khai báo lại hằng, ini `report_memleaks`, suy `$_SERVER['argc']`/`$_SERVER['argv']` từ query string ở SAPI khác CLI (`register_argc_argv`), `__wakeup()` của `DateTimeInterface`/`DateTime`/`DateTimeImmutable`/`DateTimeZone`/`DateInterval`/`DatePeriod`. Soft-deprecated (chỉ ở tài liệu, không phát `E_DEPRECATED` — RFC `soft-deprecate-sleep-wakeup` thay cho bản deprecation cứng đã bỏ phiếu): `__sleep()`/`__wakeup()` do mã người dùng khai báo | Deprecated; riêng `__sleep()`/`__wakeup()`: Soft-deprecated (mức `info`, BR-SCN-041) | `` ` `` ngoài chuỗi; `\((boolean\|integer\|double\|binary)\)`; `case\s+[^:]+;`; PHPC; mức `info`: `function\s+__(sleep\|wakeup)\s*\(` | `shell_exec()`, `(bool)`/`(int)`/`(float)`/`(string)`, `register_argc_argv=0` + `$_GET`; `__serialize()`/`__unserialize()` |
| `BC-PHP-85-02` | 8.5 | Xoá ini `disable_classes`; OPcache luôn được biên dịch vào binary và luôn nạp, build không còn sinh `opcache.so`, cờ configure `--enable-opcache`/`--disable-opcache` bị xoá, dòng `zend_extension=opcache.so` phát Warning (`opcache.enable`, `opcache.enable_cli` vẫn có hiệu lực); huỷ cấu trúc giá trị không phải mảng (khác `null`) phát Warning; so sánh lỏng object không so sánh được đổi hành vi; cấm alias tên `array`/`callable` | Xoá / Đổi hành vi | ini: `disable_classes`, dòng `zend_extension` nạp opcache (mẫu ở BR-SCN-046); Runtime | `disable_functions`; bỏ dòng `zend_extension` của opcache, giữ `opcache.*`; kiểm tra kiểu trước khi huỷ cấu trúc |
| `BC-PHP-86-01` | 8.6 (RC) | `foreach` theo tham chiếu có thể duyệt phần tử bị bỏ qua sau khi nén mảng; `??`/`empty()` trên magic property không gọi `__get()` khi `__isset()` đã ghi thuộc tính; DOM: thuộc tính `@readonly` thành `public private(set)` | Đổi hành vi | Runtime | Theo `UPGRADING` nhánh PHP-8.6 (có thể thay đổi trước GA) |

## 6. Ma trận framework/CMS ↔ PHP
Dùng ở BR-SCN-005 (d). "—" = nguồn không nêu, tool coi là "chưa xác định" và yêu cầu người vận hành xác nhận.

| Framework/CMS | Phiên bản | PHP tối thiểu | PHP tối đa được hỗ trợ | Trạng thái framework (2026-10-22) | Nguồn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| WordPress | 7.0, 7.1 | 7.4 | 8.5 | Còn hỗ trợ (7.1.3 là `latest`) | make.wordpress.org (bảng tương thích); endoflife.date |
| WordPress | 6.9 | 7.2.24 | 8.5 | Nhánh cũ | Như trên |
| WordPress | 6.7, 6.8 | 7.2.24 | 8.4 | Nhánh cũ | Như trên |
| WordPress | 6.6 | 7.2.24 | 8.3 | Nhánh cũ | Như trên |
| WordPress | 6.4, 6.5 | 7.0 | 8.3 | Nhánh cũ | Như trên |
| WordPress | 6.2 / 6.3 | 5.6 / 7.0 | 8.2 | Nhánh cũ | Như trên |
| Laravel | 13 | 8.3 | 8.5 | Sửa lỗi đến Q3 2027, bảo mật đến 2028-03-17 | laravel.com/docs/13.x/releases |
| Laravel | 12 | 8.2 | 8.5 | Chỉ vá bảo mật đến 2027-02-24 | Như trên |
| Laravel | 11 / 10 / 9 / 8 | 8.2 / 8.1 / 8.0 / 7.3 | 8.4 / 8.3 / 8.2 / 8.1 | EOL (2026-03-12 / 2025-02-04 / 2024-02-06 / 2023-01-24) | laravel.com; endoflife.date |
| Laravel | 7 / 6 LTS | 7.2 | 8.0 | EOL | endoflife.date |
| Symfony | 8.1 / 8.0 | 8.4.0 | — | 8.1 hỗ trợ đến 2027-01; 8.0 EOL 2026-07 | symfony.com/releases |
| Symfony | 7.4 LTS | 8.2.0 | — | Sửa lỗi đến 2028-11, bảo mật đến 2029-11 | Như trên |
| Symfony | 6.4 LTS | 8.1.0 | — | Sửa lỗi đến 2026-11, bảo mật đến 2027-11 | Như trên |
| CodeIgniter | 4.7.x (4.7.5) | 8.2 | 8.5 (cần ≥ 4.7.0) | Chỉ bản mới nhất được bảo trì | codeigniter.com user guide |
| CodeIgniter | 4.x cũ | 8.1 cần ≥ 4.1.6; 8.2 cần ≥ 4.2.11; 8.3 cần ≥ 4.4.4; 8.4 cần ≥ 4.6.0 | — | Không bảo trì | Như trên; CodeIgniter 3: chưa kiểm chứng |
| Magento Open Source / Adobe Commerce | 2.4.9 | 8.5 | 8.5 | Còn hỗ trợ | experienceleague.adobe.com; endoflife.date |
| Magento / Adobe Commerce | 2.4.8 | 8.3 | 8.4 | Còn hỗ trợ (2.4.8-p5) | Như trên |
| Magento / Adobe Commerce | 2.4.7 / 2.4.6 | 8.2 / 8.1 | 8.3 / 8.2 | Còn hỗ trợ | Như trên |
| Magento / Adobe Commerce | 2.4.4–2.4.5 / 2.4.2–2.4.3 | 8.1 / 7.4 | 8.1 / 7.4 | EOL 2024-11-25 / 2022-11-28 | endoflife.date |
| Drupal | 12.0 | 8.5 | 8.5 | — | drupal.org PHP requirements |
| Drupal | 11.3, 11.4 | 8.3 | 8.5 | 11.4 hỗ trợ đến 2027-07-07 | Như trên; endoflife.date |
| Drupal | 11.1, 11.2 | 8.3 | 8.4 | EOL | Như trên |
| Drupal | 10.4–10.6 | 8.1 | 8.4 | 10.6 EOL 2026-12-16 | Như trên |
| Drupal | Mọi bản còn hỗ trợ | — | Không hỗ trợ PHP 8.6 | Không có bản nào hỗ trợ PHP 7.x | drupal.org |
| Joomla | 6.x | 8.3.0 (khuyến nghị 8.4) | — | Hỗ trợ đến 2028-10-17, EOL 2029-10-16 | manual.joomla.org; endoflife.date |
| Joomla | 5.x | 8.1.0 (khuyến nghị 8.3) | — | Hết active 2026-10-13, EOL 2027-10-12 | Như trên |
| Joomla | 4.x / 3.x | Chưa kiểm chứng | Chưa kiểm chứng | EOL 2025-10-14 / 2023-08-17 | endoflife.date |

Hệ quả nổi bật: (1) Magento 2.4.9 chỉ hỗ trợ PHP 8.5, Magento 2.4.8 tối đa 8.4 → nâng Magento và nâng PHP phải thực hiện cùng một lần chuyển site trên staging (mục P4 và P5 cùng đợt); (2) Laravel 11 trở xuống không chạy chính thức trên 8.5 → nâng Laravel trước; (3) WordPress 7.x yêu cầu PHP ≥ 7.4.

## 7. Loader mã hoá, Composer và công cụ quét

### 7.1 Loader mã hoá
| Loader | Nhận diện | Hỗ trợ theo nhánh PHP (kiểm chứng 2026-10-22) | Xử lý |
| :--- | :--- | :--- | :--- |
| ionCube Loader | `$BIN -v` chứa `ionCube PHP Loader`; `$BIN -m` chứa `ionCube Loader`; file chứa `ionCube Loader` hoặc tiền tố `<?php //0` (quét tối đa 50.000 file `.php`) | Bản hiện hành 15.5.1 (2026-09-18). Mốc theo changelog ioncube.com/loaders.php (đọc 2026-10-23): PHP 8.5: từ 15.5.0 (bản đầy đủ 2026-03-12, beta 2025-11-21); 8.4: từ 14.4.0 (đầy đủ 2025-01-30, beta 2024-11-28); 8.3: từ 13.3.0 (đầy đủ 2024-07-02, beta 2024-06-07); 8.2: từ 13.0.0 (2023-08-24); 8.1: từ 12.0.1 (2022-08-12). Catalog chỉ nhận mốc bản đầy đủ, không nhận bản beta. **Không có loader cho PHP 8.0**. PHP 8.6: trang loader chưa nêu. PHP 4.x/5.x/7.x: chỉ còn gói legacy không bảo trì | BR-SCN-043; tổ hợp Encoder → Loader theo bảng 7.1.1; tổ hợp ngoài bảng: chưa kiểm chứng → bắt buộc chạy thử file mẫu (mục P4) |
| SourceGuardian Loader | `$BIN -m` chứa `SourceGuardian`; file chứa `sg_load(` | Loader 17.0.0 (2026-04-13): "PHP 5.3 đến 8.5 được hỗ trợ đầy đủ"; một số nền tảng ARM chỉ từ 7.4 | Như trên |
| Zend Guard Loader / Zend Optimizer | `$BIN -v` chứa `Zend Guard Loader` hoặc `Zend Optimizer` | Chưa kiểm chứng trong phiên này | Coi như không có loader cho nhánh đích → yêu cầu mã nguồn gốc từ nhà cung cấp (mục Thủ công) |

**Bảng 7.1.1 — ionCube: Encoder → Loader** (trích changelog https://www.ioncube.com/loaders.php, đọc 2026-10-23). Dùng cho BR-SCN-043: khi biết định dạng Encoder của file mã hoá (nhà cung cấp khai báo), tool loại trước nhánh đích mà loader không chạy được định dạng đó; kết luận cuối vẫn là chạy thử file mẫu bằng `$NEW_BIN`.

| Loader cho PHP | Bản loader tối thiểu (ngày) | Chạy được file do Encoder định dạng | Ghi chú changelog |
| :--- | :--- | :--- | :--- |
| 8.1 | 12.0.1 (2022-08-12) | PHP 8.1 (Encoder V12) | "New loaders including those for PHP 8.1 that can run files produced by the PHP 8.1 V12 Encoders" |
| 8.2 | 13.0.0 (2023-08-24) | PHP 8.2 (Encoder V13) | "Includes loaders for PHP 8.2 to accompany the PHP 8.2 encoder" |
| 8.3 | 13.3.0 (2024-07-02) | PHP 8.2; từ 14.0.0 (2024-10-14) thêm PHP 8.3 (Encoder V14) | 14.0.0: "PHP 8.3 loader that can run PHP 8.3-encoded files produced by the V14 encoder" → catalog yêu cầu loader ≥ 14.0.0 cho file định dạng PHP 8.3 (suy từ changelog) |
| 8.4 | 14.4.0 (2025-01-30) | PHP 8.3, 8.2; từ 15.0.0 (2025-10-14) thêm PHP 8.4 (Encoder V15) | 15.0.0: loader mới cũng chạy file của Encoder bản cũ hơn |
| 8.5 | 15.5.0 (2026-03-12) | PHP 8.4, 8.3, 8.2 | Danh sách định dạng lấy từ ghi chú bản beta 2025-11-21; ghi chú bản đầy đủ không nhắc lại |
| — | — | Định dạng PHP 8.1 trở về trước trên loader 8.2–8.5 | Trang không nêu → chưa kiểm chứng, chạy thử file mẫu |

### 7.2 Composer
| Bản | Phát hành | PHP tối thiểu để chạy | Bảo trì | Dùng khi |
| :--- | :--- | :--- | :--- | :--- |
| 2.10.3 | 2026-08-27 | 7.2.5 | `bugfix` | Mọi thao tác bằng `$NEW_BIN` |
| 2.2.30 (LTS) | — | 5.3.2 (getcomposer.org/doc/00-intro.md: "still offers support for PHP 5.3.2+") | `critical-security` đến 2026-12-31 | Kiểm kê trên `$OLD_BIN` 5.3.2–7.2.4; `$OLD_BIN` < 5.3.2 (5.3.0, 5.3.1 và mọi bản cũ hơn) không chạy Composer, chỉ đọc `composer.lock`; sau 2026-12-31 tool chỉ dùng để đọc `composer.lock`, không cài gói |

Lệnh dùng: `$NEW_BIN $COMPOSER check-platform-reqs` (ĐẠT khi exit 0), `$NEW_BIN $COMPOSER why-not php <bản patch $NEW>` (liệt kê gói chặn), `$NEW_BIN $COMPOSER update --with-all-dependencies` (trên `$COPY`). Composer 2 sinh `vendor/composer/platform_check.php`; file này làm site lỗi ngay khi PHP không thoả ràng buộc, vì vậy luôn chạy `install`/`update` bằng đúng `$NEW_BIN` trước khi chuyển site.

### 7.3 Công cụ quét tương thích
| Công cụ | Bản (Packagist, 2026-10-22) | Yêu cầu chạy | Vai trò trong checklist |
| :--- | :--- | :--- | :--- |
| PHPCompatibility | 10.0.0-alpha2 (2025-11-28); bản ổn định cuối 9.3.5 (2019-12-27, trước khi PHP 8.0 GA) | PHP ≥ 5.4, PHP_CodeSniffer `^3.13.3 \|\| ^4.0`; README ghi kiểm thử trên PHP 7.2–8.5 | Bắt buộc (BR-SCN-042). Dùng 10.x vì 9.3.5 không có luật cho 8.x. Ghim chính xác `10.0.0-alpha2` theo quy trình cài bên dưới (BR-CMPT-006) |
| PHPCompatibilityWP | 3.0.0-alpha2 (2025-12-16) | Phụ thuộc PHPCompatibility `^10.0@dev` và PHPCompatibilityParagonie `^2.0@dev` (bản ghim: 2.0.0-alpha2, 2025-11-29) | Thay standard khi `framework=wordpress` để bỏ qua hàm có polyfill trong core. Ghim chính xác `3.0.0-alpha2` |
| PHP_CodeSniffer | 4.0.4 (2026-08-06) | PHP ≥ 7.2 | Chạy PHPCompatibility, luôn bằng `$NEW_BIN` |
| Rector | 2.7.0 (2026-10-06) | PHP `^7.4 \|\| ^8.0` | Tuỳ chọn có duyệt diff (BR-SCN-011), chỉ trên `$COPY`, luôn `--dry-run` trước |

Quy trình cài công cụ quét vào `$TOOLS` (FR-CMPT-TOOL-001, BR-CMPT-006):
1. **Không** dùng ràng buộc dải có cờ `@dev` (vd `^10.0.0@dev`): Packagist (kiểm 2026-10-22) có nhánh `dev-develop` mang `branch-alias` `10.x-dev` (cập nhật 2026-09-21, yêu cầu PHP ≥ 7.2 và PHP_CodeSniffer `^4.0.2`); Composer chọn phiên bản cao nhất thoả ràng buộc nên sẽ cài `10.x-dev` thay vì `10.0.0-alpha2`, làm kết quả quét khác nhau giữa 2 máy hoặc 2 ngày.
2. `$TOOLS/composer.json` khai báo `"minimum-stability": "alpha"`, `"prefer-stable": true` và ràng buộc chính xác trong khối `require`: `phpcompatibility/php-compatibility: 10.0.0-alpha2`, `squizlabs/php_codesniffer: 4.0.4`, `rector/rector: 2.7.0`; khi cần standard WordPress thêm `phpcompatibility/phpcompatibility-wp: 3.0.0-alpha2` và `phpcompatibility/phpcompatibility-paragonie: 2.0.0-alpha2`.
3. Catalog công cụ trong bundle chứa `composer.lock` đã dựng sẵn; với mỗi gói, lockfile ghi `dist.reference` (commit), catalog ghi thêm SHA-256 của file dist do tool tính khi dựng catalog vì Packagist để trống `dist.shasum` cho các bản trên (kiểm 2026-10-22).
4. Cài bằng `$NEW_BIN $COMPOSER install --no-dev --no-interaction` với đúng `composer.lock` của catalog (không chạy `update`/`require`); ĐẠT khi exit 0, `$NEW_BIN $COMPOSER show --locked --format=json` trả đúng phiên bản đã ghim cho 100% gói, và SHA-256 file dist khớp catalog. Lệch hash → `ERR-CMPT-424-01`.

Lệnh quét chuẩn: `$NEW_BIN $TOOLS/vendor/bin/phpcs -p -s --standard=PHPCompatibility --runtime-set testVersion $NEW --extensions=php,inc,phtml --report=json --report-file=<json> $SITE`.

Lint cú pháp (BR-SCN-042 (1), lệnh ở `CHK-PHP-004-14`): từ PHP 8.3, `php -l` nhận nhiều file trong 1 lệnh (php-src `UPGRADING` nhánh PHP-8.3: "It is now possible to lint multiple files"); mọi nhánh đích hợp lệ tại 2026-10-22 (8.3, 8.4, 8.5) đều thoả, nên lint chạy theo lô 200 file/tiến trình. Đo ngày 2026-10-23 trên container 4 vCPU, PHP 8.3.6, file mẫu 3–5 dòng: `xargs -n1 -P2` mất 14,1 s cho 1.000 file (≈ 14 ms/file, ngoại suy ≈ 141 s cho 10.000 file, vượt cả ngân sách 120 s của `NFR-PERF-005`); `xargs -n 200 -P 2` mất 0,92 s cho 10.000 file. Kết quả lô trùng kết quả từng file ở 6 ca thử (2 file khai báo trùng tên lớp/hàm: không báo lỗi giả; `Parse error`; 2 lỗi biên dịch `Fatal error`; file hợp lệ sau file lỗi vẫn được lint). GNU `xargs` dừng đọc đầu vào khi 1 lệnh con thoát mã 255 (man xargs; `php -l` trả 255 khi có file lỗi): đo cùng ngày, lệnh không bọc chỉ lint 200/600 file và bỏ sót file lỗi thứ 2; vì vậy lệnh con được bọc `sh -c '"$0" -l "$@" || exit 1'` để đổi 255 thành 1 (`xargs` trả 123 và chạy hết các lô). Số đo chỉ cho bước lint với file nhỏ; `NFR-PERF-005` (gồm PHPCompatibility và Composer) vẫn chưa đo.

## 8. Biến thể thực thi theo môi trường
Hành động: **A1** cài `$NEW` song song; **A2** chuyển 1 site sang `$NEW`; **A3** hoàn tác 1 site về `$OLD`; **A4** gỡ `$OLD`. Mọi A2/A3 ghi bước `copy` vào manifest trước khi sửa file (BR-SCN-017). Lệnh ghi "chưa kiểm chứng" phải được QA chạy thử trước khi chuyển thành mục `AUTO` (common §8 mục 6). Bảng dưới là tóm tắt; lệnh chi tiết, cột kiểm chứng (KC) và bước đọc lại sau mỗi lệnh panel (`BR-ENV-012`) thuộc [environment-playbooks.md](environment-playbooks.md) (DOC-SRS-QP-ENV-001) với ánh xạ E1 = PB-001, E2 = PB-003, E3 = PB-002, E4 = PB-004, E5 = PB-007/PB-008, E6 = PB-009, E7 = PB-010, E8 = PB-011, E9 = PB-012, E10 = PB-013. Khi lệnh ở bảng này khác playbook, playbook là nguồn áp dụng. Lệnh E5–E9 dưới đây chép từ [environment-playbooks-panels.md](environment-playbooks-panels.md) (DOC-SRS-QP-ENV-004, kiểm chứng ngày 2026-10-22); "KC = Có" = đã đối chiếu tài liệu hoặc mã nguồn chính thức của panel, chưa chạy thử trên máy có panel.

| Mã | Môi trường (nhận diện như v0.1) | A1 Cài song song | A2 Chuyển site | A3 Hoàn tác | A4 Gỡ nhánh cũ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| E1 | Debian/Ubuntu + kho Ondřej Surý (`packages.sury.org`; PPA `ondrej/php` cho Ubuntu Jammy/Noble, Ubuntu Resolute dùng `packages.sury.org`) | `apt-get install -y php$NEW-fpm php$NEW-cli php$NEW-<ext>`; dịch vụ `php$NEW-fpm`; socket `/run/php/php$NEW-fpm.sock` | nginx: đổi `fastcgi_pass` sang socket mới → `nginx -t` → `systemctl reload nginx`; Apache: đổi `SetHandler "proxy:unix:/run/php/php$NEW-fpm.sock\|fcgi://localhost"` → `apachectl configtest` → `systemctl reload apache2` | Khôi phục file vhost từ manifest → kiểm tra cấu hình → reload | `apt-get purge 'php$OLD-*'` |
| E2 | RHEL-family + Remi (gói song song `phpXY` dưới `/opt/remi/phpXY`, v0.1 đã dò) | `dnf install php$NEWND php$NEWND-php-fpm php$NEWND-php-<ext>` (chưa kiểm chứng tên gói trên máy thật) | Như E1 với socket/cổng của pool `php$NEWND-php-fpm` | Như E1 | `dnf remove 'php$OLDND-*'` |
| E3 | RHEL AppStream module (1 phiên bản PHP trên hệ thống) | Không cài song song được bằng module → dùng E2 hoặc E10 | — | — | — |
| E4 | Alpine (`apk`, gói đánh số theo nhánh như `php84`) | `apk add php$NEWND php$NEWND-fpm` (chưa kiểm chứng gói theo từng bản Alpine) | Như E1 | Như E1 | `apk del 'php$OLDND*'` |
| E5 | cPanel EasyApache 4 (`ea-phpXY`) → [PB-007](environment-playbooks-panels.md#2-pb-007--cpanelwhm-easyapache-4); CloudLinux `alt-phpXY` + PHP Selector → [PB-008](environment-playbooks-panels.md#3-pb-008--cloudlinux-alt-php--php-selector) | `SEMI`: `dnf install -y ea-php$NEWND ea-php$NEWND-php-fpm ea-php$NEWND-php-<ext>` (Ubuntu: `apt install --purge …`); không gọi `php_set_system_default_version` (BR-SCN-012). KC: Có (mẫu tên gói, lệnh); Chưa (tên riêng gói `-php-fpm`) | `SEMI`: `whmapi1 --output=json php_set_vhost_versions version=ea-php$NEWND vhost=$VHOST php_fpm=<giữ giá trị cũ>`; ĐẠT khi `metadata.result = 1` và `php_get_vhost_versions` đọc lại `version = ea-php$NEWND`; chỉ chạy `/scripts/restartsrv_apache_php_fpm` (v0.1) 1 lần khi xác minh sau 10 s không đạt (KC: Có). PB-008: `selectorctl --set-user-current=$NEW --user=<user>` (phạm vi mọi domain của người dùng) | `whmapi1 php_set_vhost_versions version=<cũ> vhost=$VHOST php_fpm=<cũ>` (`inherit` nếu trước đó là `inherit`) + đọc lại; PB-008: `selectorctl --set-user-current=<cũ> --user=<user>` (KC: Có) | Gỡ gói `ea-php$OLDND*` khi `php_get_vhost_versions` không còn vhost dùng `$OLD` trong 14 ngày (BR-SCN-014); lệnh gỡ: chưa kiểm chứng |
| E6 | Plesk (`/opt/plesk/php/X.Y`) → [PB-009](environment-playbooks-panels.md#4-pb-009--plesk) | `SEMI`: `plesk installer add --components php$NEW` rồi `plesk bin php_handler --reread`; ĐẠT khi `plesk bin php_handler --list` có handler `plesk-php$NEWND-*` (KC: Gián tiếp) | `SEMI`: `plesk bin site -u $VHOST -php_handler_id <id mới cùng loại handler cũ, vd plesk-php$NEWND-fpm>`; ĐẠT khi `plesk bin php_handler --get-usage -id <id mới>` chứa `$VHOST` (KC: Có). Không dùng `php_handler --replace` (đổi mọi site) | `plesk bin site -u $VHOST -php_handler_id <id cũ>` + đọc lại `--get-usage -id <id cũ>` (KC: Có) | `plesk bin php_handler --remove` (bị từ chối khi handler còn site/gói dịch vụ dùng, KC: Có); gỡ thành phần qua Plesk Installer |
| E7 | aaPanel (`/www/server/php/XY`) → [PB-010](environment-playbooks-panels.md#5-pb-010--aapanel) | `MANUAL`: App Store » PHP-X.Y » Install; hoặc `SEMI`: `cd /www/server/panel/install && /bin/bash install_soft.sh <type> install php <X.Y>` (KC: Có — đọc mã nguồn; chưa chạy thử) | `SEMI`: sửa file vhost đúng thuật toán `SetPHPVersion` của panel (Nginx: `enable-php-$NEWND.conf`; Apache: địa chỉ FPM của `$NEWND`; OpenLiteSpeed: `lsphp$NEWND`) → `nginx -t`/`apachectl -t` → reload như panel; ĐẠT khi đọc lại file vhost có phiên bản `$NEWND` (KC: Có — đọc mã nguồn) | Phát lại `copy` các file vhost → kiểm tra cú pháp → reload; đọc lại = phiên bản cũ (KC: Có) | Gỡ trong App Store (`MANUAL`) |
| E8 | CyberPanel / OpenLiteSpeed / LiteSpeed (`lsphpXY`) → [PB-011](environment-playbooks-panels.md#6-pb-011--cyberpanel--openlitespeed--litespeed) | Ubuntu/Debian: `apt-get install lsphp$NEWND lsphp$NEWND-common lsphp$NEWND-mysql`; RHEL-family: `dnf install lsphp$NEWND lsphp$NEWND-common lsphp$NEWND-mysqlnd` (+ `lsphp$NEWND-<ext>`); kho LiteSpeed chưa có → `SEMI` (BR-ENV-004). KC: Có | `SEMI`: `cyberpanel changePHP --domainName $VHOST --php $NEW` (lệnh tự sửa `vhost.conf` và khởi động lại LiteSpeed toàn máy chủ); ĐẠT khi đọc lại `vhost.conf` chứa `lsphp$NEWND` hoặc `x-httpd-php$NEWND` (KC: Có — đọc mã nguồn). Không panel: sửa dòng `path` của `extprocessor` → `/usr/local/lsws/bin/lswsctrl restart` (KC: Chưa) | `cyberpanel changePHP --domainName $VHOST --php <cũ>`; lệnh lỗi → khôi phục `copy` `vhost.conf` → `lswsctrl restart` (v0.1) | Gỡ gói `lsphp$OLDND*` |
| E9 | DirectAdmin CustomBuild (`/usr/local/phpXY`) → [PB-012](environment-playbooks-panels.md#7-pb-012--directadmin-custombuild) | `SEMI`: chọn khe trống `k` ≥ 2 (`php<k>_release=no`), không đổi `php1_release`; `da build set php<k>_release $NEW && da build php && da build rewrite_confs`; ĐẠT khi `/usr/local/php$NEWND/bin/php` tồn tại (KC: Có) | `SEMI` (yêu cầu `da config-get php_version_selector` = `1`): `backup_file` `<DOMAIN>.conf`; đặt `php1_select=<k>`; `da build rewrite_confs` (tác động cấu hình mọi domain); ĐẠT khi đọc lại `php1_select=<k>` (KC: Có) | Phát lại `copy` `<DOMAIN>.conf` → `da build rewrite_confs`; đọc lại `php1_select` = giá trị cũ (KC: Có) | Đặt khe của `$OLD` về `no` rồi `da build php` (PB-012 chưa định nghĩa; chưa kiểm chứng) |
| E10 | Docker (image `php:` trong Dockerfile/compose, v0.1 `check_dockerfiles`) | Build image mới từ `php:$NEW-fpm` hoặc `php:$NEW-apache` (ngoài phạm vi: tool chỉ sửa tag, không build/deploy) | Chạy container mới song song, đổi upstream của reverse proxy | Trỏ upstream về container cũ | Xoá container/image cũ |

## 9. Ma trận lỗi bổ sung (PHP)
Bổ sung cho [version-scenarios-common.md §6](version-scenarios-common.md#6-ma-trận-lỗi-của-bộ-máy-kịch-bản-error-matrix).

| Mã ERR | HTTP | Điều kiện phát sinh | Localization key | Thông báo hiển thị | Mức độ | Hành động tiếp theo |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `ERR-SCN-409-03` | 409 | Site dùng loader mã hoá và không còn nhánh đích có loader chính thức (BR-SCN-043) | `scn.php.loader.unavailable` | "Không có {loader} cho PHP {target}; không thể chuyển site {vhost}." | High | Lấy bản mã hoá/mã nguồn mới từ nhà cung cấp hoặc chọn nhánh đích có loader |
| `ERR-SCN-412-02` | 412 | Site chạy `mod_php` và chưa chuyển được sang PHP-FPM (BR-SCN-047) | `scn.php.modphp.blocking` | "Site {vhost} đang chạy mod_php; cần chuyển sang PHP-FPM trước khi đổi phiên bản." | High | Chuyển sang PHP-FPM hoặc dùng container/máy chủ mới |

## 10. Kịch bản chi tiết SCN-PHP-001..007
Cột "Loại": **Tự động** (`AUTO`), **Bán tự động (duyệt)** (`SEMI`), **Thủ công** (`MANUAL`) theo common §3.2. Mục có điều kiện ghi `(khi ...)` tương ứng trường `applies_when`.

### 10.1 SCN-PHP-001 — PHP 4.x
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^4\.\d+\.\d+$` / 40 |
| Trạng thái, EOL | `EOL`; nhánh cuối 4.4 hết hỗ trợ 2008-08-07 (bản cuối 4.4.9, php.net/eol.php); endoflife.date không có 4.x → bản ghi tĩnh; quá 6.650 ngày → Nghiêm trọng |
| Đích | 8.5 (thay thế 8.4/8.3 theo §6, §7) |
| Lộ trình | Production: 4.x → `$NEW` một lần trên **máy chủ/container mới** (OS chạy PHP 4 không có kho gói cho 8.x). Mã nguồn trên staging: sửa nhóm BC 5.0 → 5.3/5.4 → 7.0 → 8.0 → 8.1–8.5; quét bậc thang `testVersion` 5.6, 7.4, `$NEW` |
| Dải BC | Toàn bộ §5: `BC-PHP-50-01` … `BC-PHP-85-02` (40 mục) |
| Extension bị xoá/thay | Như SCN-PHP-004, cộng phụ thuộc register globals/magic quotes (5.4) |
| Framework/CMS | WordPress chạy được trên PHP 4 là bản ≤ 3.1.x: WordPress 2.5–3.1 yêu cầu PHP ≥ 4.3, từ WordPress 3.2 (phát hành 2011-07-04) yêu cầu PHP ≥ 5.2.4 (wordpress.org, trang Version 3.2, mục "Requirements Changes"); bản ≤ 3.1.x không có trong §6 và đường nâng trực tiếp từ ≤ 3.1.x lên 7.x chưa kiểm chứng → coi như viết lại/chuyển dữ liệu; framework PHP 4 khác: không có trong §6 → `ERR-SCN-409-01` cho mọi đích nếu không nâng framework |
| Loader | Loader cho PHP 4 chỉ còn gói legacy → cần mã nguồn gốc (mục 23) |
| Composer | Không áp dụng trên `$OLD` (Composer 2.2 LTS cần PHP ≥ 5.3.2, BR-SCN-044); chỉ dùng trên `$NEW` nếu dự án mới thêm Composer |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-001-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | `$OLD_BIN -n -r 'echo PHP_VERSION,"\|",PHP_SAPI;'` (lệnh `-r` trả exit ≠ 0 → dùng `$OLD_BIN -v`); `readlink -f`; `dpkg -S`/`rpm -qf` | Chuỗi khớp `^4\.\d+\.\d+`; nguồn cài ghi vào `scan --json` | Cả 2 cách không trả phiên bản trong 10 s → SCN-PHP-005 |
| `CHK-PHP-001-02` | P1 | Ghi nhận OS và hạn hỗ trợ OS | Tự động | `/etc/os-release` hoặc `/etc/redhat-release`; đối chiếu endoflife.date | OS, phiên bản, ngày EOL OS có trong báo cáo | OS không có `/etc/os-release` → đọc `/etc/issue` |
| `CHK-PHP-001-03` | P1 | Ánh xạ site → handler → binary (FEAT-004) | Tự động | `apachectl -S`/`httpd -S`, `httpd.conf` (`LoadModule php4_module`), `.htaccess` | 100% vhost có binary; `unmapped` = 0 | SAPI là `mod_php` → không cấu hình song song trên máy cũ (BR-SCN-047), chuyển bằng máy mới |
| `CHK-PHP-001-04` | P1 | Kiểm kê extension, `php.ini` (`register_globals`, `magic_quotes_gpc`, `safe_mode`, `short_open_tag`) | Tự động | `$OLD_BIN -m`; `$OLD_BIN -i` | Giá trị 4 directive và danh sách extension lưu vào state | Mã phụ thuộc `register_globals=On` hỏng âm thầm trên 8.x → mục 17 |
| `CHK-PHP-001-05` | P1 | Nhận diện framework/CMS và loader | Tự động | File phiên bản CMS; §7.1 | Mỗi site có `framework`, `loader` | CMS tự viết → `framework=custom` |
| `CHK-PHP-001-06` | P1 | Đánh giá bảo mật so sánh 4.x với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | NVD trả 0 CVE cho nhánh EOL → hiển thị "EOL, không còn bản vá" thay vì "0 CVE" |
| `CHK-PHP-001-07` | P1 | Chọn và duyệt nhánh đích, phương án máy chủ mới | Bán tự động (duyệt) | BR-SCN-005; §8 E1/E2/E10 cho máy mới | Kế hoạch `approved`; ghi rõ máy đích và địa chỉ IP | Chi phí máy mới ngoài phạm vi tool |
| `CHK-PHP-001-08` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File sao lưu > 0 byte, có SHA-256; khôi phục thử thành công trên máy mới | CSDL MySQL 4.x/5.0 dump không nạp thẳng vào MySQL 8 → mục 12 |
| `CHK-PHP-001-09` | P2 | Chuẩn bị máy chủ/container mới đạt BR-SCN-016 | Thủ công | VPS mới hoặc E10; kiểm tra bằng `df -BG`, `free -m`, endoflife.date | Đĩa ≥ 2 GB trống, RAM ≥ 512 MB, OS còn hỗ trợ ≥ 365 ngày | Sai múi giờ/locale → đặt `date.timezone` (BC-PHP-54-04) |
| `CHK-PHP-001-10` | P2 | Cài `$NEW` trên máy mới (§8 A1) | Bán tự động (duyệt) | E1/E2: cài gói; E10: image `php:$NEW-fpm` | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-001-11` | P2 | Cài extension tương ứng (BR-SCN-045) | Bán tự động (duyệt) | So `$OLD_BIN -m` với `$NEW_BIN -m` | Extension thiếu chưa có phương án = 0 | `mysql` không có trên 8.x → sửa mã |
| `CHK-PHP-001-12` | P2 | Chuyển CSDL sang máy chủ CSDL đang được hỗ trợ | Thủ công | Dump trên máy cũ, nạp trên máy mới, so số bảng và số dòng | Số bảng bằng nhau; chênh lệch số dòng mỗi bảng = 0 | Charset `latin1` → `utf8mb4` làm hỏng ký tự → kiểm tra 20 bản ghi có dấu |
| `CHK-PHP-001-13` | P2 | Tạo pool FPM `$NEW`, không sao chép directive đã xoá (BR-SCN-046) | Tự động | Sinh pool mới; `php-fpm$NEW -t` | Exit 0; 0 directive thuộc danh sách BR-SCN-046 | Như `CHK-PHP-004-13` |
| `CHK-PHP-001-14` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | Như `CHK-PHP-004-14` (0 dòng `Errors parsing`) | Thẻ `<%`, `<script language="php">` gây lỗi (BC-PHP-70-02) |
| `CHK-PHP-001-15` | P3 | Quét PHPCompatibility bậc thang 5.6, 7.4 và `$NEW` | Tự động | Lệnh chuẩn §7.3 với 3 giá trị `testVersion` | Lượt `$NEW`: 0 `ERROR` | PHPCompatibility không có luật riêng cho PHP 4 → mục 16, 17 |
| `CHK-PHP-001-16` | P3 | Quét bộ luật BC dải (4.x, `$NEW`] | Tự động | Mẫu quét `BC-PHP-50-01` … mục cuối ≤ `$NEW` | 0 hit `error` chưa miễn trừ | Dương tính giả → duyệt theo trích đoạn |
| `CHK-PHP-001-17` | P3 | Đánh giá phụ thuộc register globals / magic quotes (BC-PHP-54-01) | Thủ công | Báo cáo heuristic của tool: biến đọc trước khi gán trong cùng file, `extract($_REQUEST\|$_GET\|$_POST)`, `stripslashes(` trên dữ liệu request | Mỗi file trong báo cáo có kết luận "đã sửa" hoặc "không ảnh hưởng" | Heuristic bỏ sót → bù bằng kiểm thử nghiệp vụ (mục 30) |
| `CHK-PHP-001-18` | P3 | Rà soát ngữ nghĩa đối tượng PHP 5 (BC-PHP-50-01) và constructor PHP 4 (BC-PHP-80-03) | Thủ công | Danh sách lớp có phương thức trùng tên lớp; vị trí gán đối tượng rồi sửa | 0 lớp còn constructor kiểu PHP 4; chỗ cần bản sao đã dùng `clone` | Lỗi logic không gây lỗi cú pháp → mục 30 |
| `CHK-PHP-001-19` | P3 | (Tuỳ chọn) Rector trên `$COPY` (BR-SCN-011) | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; mục 14–16 chạy lại đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-001-20` | P3 | Sửa mã theo báo cáo 14–18 | Thủ công | Lập trình viên; tool chạy lại 14–16 | BR-SCN-042 ĐẠT | Số hit mức `error` > 500 hoặc > 20% số file → đánh giá phương án viết lại, ghi quyết định vào kế hoạch |
| `CHK-PHP-001-21` | P3 | Chạy test tự động (khi có) bằng `$NEW_BIN` | Bán tự động (duyệt) | `$NEW_BIN vendor/bin/phpunit` | Exit 0 | Không có `phpunit.xml*` → `SKIPPED`, dựa vào mục 29–30 |
| `CHK-PHP-001-22` | P4 | Nâng/thay framework/CMS lên bản thuộc dải §6 (khi `framework` ≠ none) | Thủ công | Theo hướng dẫn framework; với CMS không có đường nâng: chuyển dữ liệu sang bản mới | Phiên bản thuộc dải §6; trang chủ staging HTTP 200 | Mất tuỳ biến/giao diện cũ |
| `CHK-PHP-001-23` | P4 | Thay mã mã hoá bằng mã nguồn/bản mã hoá mới (khi `loader` ≠ none) (BR-SCN-043) | Thủ công | Liên hệ nhà cung cấp; chạy thử bằng `$NEW_BIN` | File mẫu exit 0 | Nhà cung cấp không còn → viết lại module |
| `CHK-PHP-001-24` | P4 | Thêm Composer và thư viện thay thế (khi mục 16 có ≥ 1 hit thuộc `BC-PHP-70-01`, `BC-PHP-72-01`, `BC-PHP-74-02`, `BC-PHP-80-06` hoặc `BC-PHP-84-03` — nhóm extension rời lõi mà cột "Thay thế" là thư viện/PECL; hoặc `$COPY` có `composer.json` và `$NEW_BIN $COMPOSER check-platform-reqs` trên `$COPY` exit ≠ 0) | Bán tự động (duyệt) | `$NEW_BIN $COMPOSER require <gói>` trên `$COPY` | `check-platform-reqs` exit 0; OSV 0 Critical | Gói thay thế không còn bảo trì → chọn gói có bản phát hành trong 365 ngày gần nhất trên Packagist |
| `CHK-PHP-001-25` | P5 | Hạ TTL DNS hoặc chuẩn bị upstream reverse proxy ≥ 24 giờ trước chuyển | Thủ công | `dig +noall +answer $VHOST` | TTL ≤ 300 s tại thời điểm chuyển | TTL cũ còn cache → chờ đủ TTL cũ |
| `CHK-PHP-001-26` | P5 | Chụp baseline health check trên máy cũ | Tự động | BR-SCN-009 | Có baseline cho mỗi URL | Như `CHK-PHP-004-24` |
| `CHK-PHP-001-27` | P5 | Chuyển site canary sang máy mới (đổi DNS/upstream) | Bán tự động (duyệt) | Đổi bản ghi DNS hoặc upstream; manifest `note` ghi giá trị cũ | Health check mục 29 ĐẠT | Hoàn tác phụ thuộc TTL → BR-SCN-010 không bảo đảm ≤ 60 s; ghi rõ trong kế hoạch |
| `CHK-PHP-001-28` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như mục 27 | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-001-29` | P6 | Health check 10 phút + hoàn tác (BR-SCN-009/010) | Tự động | So baseline mục 26 | Đạt 6 tiêu chí; nếu không → đổi lại DNS/upstream, `ERR-SCN-500-01` | Như `CHK-PHP-004-28` |
| `CHK-PHP-001-30` | P6 | Kiểm thử nghiệp vụ toàn bộ chức năng | Thủ công | Kịch bản chủ site | 100% kịch bản pass, ký xác nhận | Như `CHK-PHP-004-29` |
| `CHK-PHP-001-31` | P6 | Chuyển cron/CLI sang máy mới với `$NEW_BIN` | Bán tự động (duyệt) | `crontab -l -u $OWNER` máy cũ → máy mới | 0 cron còn chạy trên máy cũ; lần chạy đầu exit 0 | Cron chạy trùng 2 máy → tắt trên máy cũ trước |
| `CHK-PHP-001-32` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm thông điệp | Như `CHK-PHP-004-31` |
| `CHK-PHP-001-33` | P7 | Ngừng máy cũ sau 14 ngày không có request (BR-SCN-014) | Thủ công | Access log máy cũ 14 ngày = 0 request site | Máy cũ tắt; bản sao lưu cuối giữ ≥ 90 ngày | Mất rollback → cảnh báo trước khi duyệt |
| `CHK-PHP-001-34` | P7 | Cập nhật Dockerfile/CI/tài liệu vận hành (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu PHP 4 | Như `CHK-PHP-004-33` |

### 10.2 SCN-PHP-002 — PHP 5.0–5.2
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^5\.[0-2]\.\d+$` / 50 |
| Trạng thái, EOL | `EOL`: 5.0 ngày 2005-09-05 (5.0.5), 5.1 ngày 2006-08-24 (5.1.6), 5.2 ngày 2011-01-06 (5.2.17); quá ≥ 5.768 ngày → Nghiêm trọng |
| Đích | 8.5 (thay thế 8.4/8.3 theo §6, §7) |
| Lộ trình | Production: 5.0–5.2 → `$NEW` một lần. Mã nguồn trên staging: BC 5.3/5.4 (register globals, magic quotes, call-time pass-by-reference) → 7.0 → 8.0 → 8.1–8.5; bậc thang `testVersion` 5.6, 7.4, `$NEW` |
| Dải BC | `BC-PHP-53-01` … `BC-PHP-85-02` (38 mục) |
| Extension bị xoá/thay | Như SCN-PHP-004 |
| Framework/CMS | Bản framework chạy được trên 5.2 không có trong §6 → nâng framework là điều kiện bắt buộc (mục 23) |
| Loader | Như SCN-PHP-004 |
| Composer | Không chạy được trên `$OLD` (Composer 2.2 LTS cần ≥ 5.3.2, BR-SCN-044); kiểm kê bằng cách đọc `composer.lock`; chỉ chạy Composer bằng `$NEW_BIN` |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-002-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^5\.[0-2]\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-002-02` | P1 | Ghi nhận OS và hạn hỗ trợ OS | Tự động | `/etc/os-release`; endoflife.date | OS + ngày EOL OS trong báo cáo | OS hết hỗ trợ → nhánh máy mới (mục 10) |
| `CHK-PHP-002-03` | P1 | Ánh xạ site → handler → binary (FEAT-004) | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-002-04` | P1 | Kiểm kê extension và giá trị `register_globals`, `magic_quotes_gpc`, `magic_quotes_runtime`, `safe_mode`, `allow_call_time_pass_reference` | Tự động | `$OLD_BIN -m`; `$OLD_BIN -i` | Giá trị 5 directive và danh sách extension trong state | Directive bật → mục 17 bắt buộc |
| `CHK-PHP-002-05` | P1 | Nhận diện framework/CMS và loader | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader` | Như `CHK-PHP-004-04` |
| `CHK-PHP-002-06` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | Như `CHK-PHP-004-05` |
| `CHK-PHP-002-07` | P1 | Chọn và duyệt nhánh đích, phương án cùng máy hoặc máy mới | Bán tự động (duyệt) | BR-SCN-005, BR-SCN-016 | Kế hoạch `approved` | Như `CHK-PHP-004-06` |
| `CHK-PHP-002-08` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-002-09` | P1 | Dựng staging cách ly | Thủ công | Như `CHK-PHP-004-08` | Trang chủ staging HTTP 200 | Như `CHK-PHP-004-08` |
| `CHK-PHP-002-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016); không đạt → chuẩn bị máy mới | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 trên máy đích | Như `CHK-PHP-004-09` |
| `CHK-PHP-002-11` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) (khi cùng máy) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-002-12` | P2 | Cài `$NEW` song song hoặc trên máy mới (§8 A1) | Bán tự động (duyệt) | Theo §8 | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-002-13` | P2 | Cài extension tương ứng (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | Như `CHK-PHP-004-12` |
| `CHK-PHP-002-14` | P2 | Tạo pool FPM `$NEW`, loại directive 5.4 (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm | Directive 5.4 còn trong ini gây `E_CORE_ERROR` |
| `CHK-PHP-002-15` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | Như `CHK-PHP-004-14` (0 dòng `Errors parsing`) | Như `CHK-PHP-004-14` |
| `CHK-PHP-002-16` | P3 | Quét PHPCompatibility bậc thang 5.6, 7.4, `$NEW` | Tự động | Lệnh chuẩn §7.3 | Lượt `$NEW`: 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-002-17` | P3 | Đánh giá phụ thuộc register globals / magic quotes / call-time pass-by-reference (BC-PHP-54-01, BC-PHP-54-02) | Thủ công | Báo cáo heuristic như `CHK-PHP-001-17` + hit `&\$` trong lời gọi | Mỗi file có kết luận "đã sửa"/"không ảnh hưởng" | Heuristic bỏ sót → mục 31 |
| `CHK-PHP-002-18` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] | Tự động | Mẫu §5 từ `BC-PHP-53-01` | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-002-19` | P3 | Chạy test tự động bằng `$NEW_BIN` (khi có) | Bán tự động (duyệt) | `$NEW_BIN vendor/bin/phpunit` | Exit 0 | Như `CHK-PHP-004-18` |
| `CHK-PHP-002-20` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 15–18 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-002-21` | P3 | Sửa mã theo báo cáo 15–18 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-002-22` | P4 | Thêm/nâng dependency qua Composer trên `$NEW_BIN` (khi `$COPY` có `composer.json` và `$NEW_BIN $COMPOSER check-platform-reqs` trên `$COPY` exit ≠ 0, hoặc FR-CMPT-COMP-002 trả ≥ 1 package phải nâng, hoặc mục 18 có ≥ 1 hit thuộc `BC-PHP-70-01`, `BC-PHP-72-01`, `BC-PHP-74-02`, `BC-PHP-80-06`, `BC-PHP-84-03`) | Bán tự động (duyệt) | `$NEW_BIN $COMPOSER update --with-all-dependencies` trên `$COPY` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-002-23` | P4 | Nâng framework/CMS lên bản thuộc §6 (khi `framework` ≠ none) | Thủ công | Theo hướng dẫn framework | Phiên bản thuộc dải §6 | Nâng qua ≥ 2 major framework phải đi từng bước theo upgrade guide |
| `CHK-PHP-002-24` | P4 | Loader cho `$NEW` và chạy thử file mã hoá (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | `ERR-SCN-409-03` |
| `CHK-PHP-002-25` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-002-26` | P5 | (khi `mod_php`) Chuyển sang PHP-FPM của `$OLD` trước hoặc dùng máy mới (BR-SCN-047) | Bán tự động (duyệt) | Như `CHK-PHP-004-25` | Health check ĐẠT | `ERR-SCN-412-02` |
| `CHK-PHP-002-27` | P5 | Chuyển site canary (§8 A2, hoặc DNS/upstream khi máy mới) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` / `CHK-PHP-001-27` | Mục 29 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-002-28` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Tuần tự | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-002-29` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí; nếu không → hoàn tác, `ERR-SCN-500-01` | Như `CHK-PHP-004-28` |
| `CHK-PHP-002-30` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-002-31` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass, ký xác nhận | Như `CHK-PHP-004-29` |
| `CHK-PHP-002-32` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-002-33` | P7 | Gỡ `$OLD` hoặc ngừng máy cũ sau 14 ngày không request (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 | `$OLD_BIN` không còn / máy cũ tắt | Mất rollback 1 lệnh |
| `CHK-PHP-002-34` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:5.0`–`php:5.2` | Như `CHK-PHP-004-33` |

### 10.3 SCN-PHP-003 — PHP 5.3–5.5
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^5\.[3-5]\.\d+$` / 60 |
| Trạng thái, EOL | `EOL`: 5.3 ngày 2014-08-14 (5.3.29), 5.4 ngày 2015-09-03 theo php.net (endoflife.date ghi 2015-09-14; tool dùng php.net theo BR-SCN-002) (5.4.45), 5.5 ngày 2016-07-21 (5.5.38); quá ≥ 3.745 ngày → Nghiêm trọng |
| Đích | 8.5 (thay thế 8.4/8.3 theo §6, §7) |
| Lộ trình | Production: một lần lên `$NEW`. Mã nguồn: 5.3 cần xử lý thêm BC 5.4 (call-time pass-by-reference, register globals); 5.5 đã cảnh báo `ext/mysql` và `/e` → xoá ở 7.0; bậc thang `testVersion` 5.6, 7.4, `$NEW` |
| Dải BC | 5.3: `BC-PHP-54-01` … `BC-PHP-85-02` (37 mục); 5.4: từ `BC-PHP-55-01` (33 mục); 5.5: từ `BC-PHP-56-01` (32 mục) |
| Extension bị xoá/thay | Như SCN-PHP-004 |
| Framework/CMS | Mọi bản WordPress trong §6 cần PHP ≥ 5.6 → site WordPress đang chạy 5.3–5.5 là bản ngoài §6, phải lên 7.x (PHP ≥ 7.4); framework chạy được trên 5.3–5.5 không có bản nào trong §6 hỗ trợ 8.x → nâng framework |
| Loader | Như SCN-PHP-004 |
| Composer | Kiểm kê bằng Composer 2.2 LTS trên `$OLD_BIN` khi `$OLD` ≥ 5.3.2, đến 2026-12-31; `$OLD` 5.3.0–5.3.1 hoặc sau mốc 2026-12-31: chỉ đọc `composer.lock` (BR-SCN-044) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-003-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^5\.[3-5]\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-003-02` | P1 | Ánh xạ site → handler → binary (FEAT-004) | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-003-03` | P1 | Kiểm kê extension và directive bị xoá ở 5.4 (khi `$OLD` = 5.3) | Tự động | `$OLD_BIN -m`; `$OLD_BIN -i` | Danh sách extension + giá trị directive trong state | Directive còn bật → mục 17 |
| `CHK-PHP-003-04` | P1 | Nhận diện framework/CMS, loader | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer` | Như `CHK-PHP-004-04` |
| `CHK-PHP-003-05` | P1 | Kiểm kê Composer trên `$OLD` bằng Composer 2.2 LTS (khi `composer=true`) | Tự động | `$OLD` ≥ 5.3.2: `$OLD_BIN composer-2.2.phar show --locked --format=json` (chạy dưới `$OWNER`); `$OLD` 5.3.0–5.3.1: không chạy Composer, đọc `composer.lock` bằng parser của tool (BR-SCN-044) | Danh sách gói + phiên bản lưu vào state; OSV `querybatch` đã chạy | Sau 2026-12-31 Composer 2.2 hết vá → chỉ đọc `composer.lock` bằng parser của tool |
| `CHK-PHP-003-06` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | Như `CHK-PHP-004-05` |
| `CHK-PHP-003-07` | P1 | Chọn và duyệt nhánh đích | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved` | Như `CHK-PHP-004-06` |
| `CHK-PHP-003-08` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-003-09` | P1 | Dựng staging cách ly | Thủ công | Như `CHK-PHP-004-08` | Trang chủ staging HTTP 200 | Như `CHK-PHP-004-08` |
| `CHK-PHP-003-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 | Như `CHK-PHP-004-09` |
| `CHK-PHP-003-11` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-003-12` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | Theo §8 | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-003-13` | P2 | Cài extension tương ứng (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | Như `CHK-PHP-004-12` |
| `CHK-PHP-003-14` | P2 | Tạo pool FPM `$NEW` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm | Như `CHK-PHP-004-13` |
| `CHK-PHP-003-15` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | Như `CHK-PHP-004-14` (0 dòng `Errors parsing`) | Như `CHK-PHP-004-14` |
| `CHK-PHP-003-16` | P3 | Quét PHPCompatibility bậc thang 5.6, 7.4, `$NEW` | Tự động | Lệnh chuẩn §7.3 | Lượt `$NEW`: 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-003-17` | P3 | (khi `$OLD` = 5.3) Đánh giá call-time pass-by-reference và register globals (BC-PHP-54-01, BC-PHP-54-02) | Thủ công | Hit `&\$` trong lời gọi; heuristic như `CHK-PHP-001-17` | Mỗi hit có kết luận | Như `CHK-PHP-001-17` |
| `CHK-PHP-003-18` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] | Tự động | Mẫu §5 | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-003-19` | P3 | Kiểm tra platform Composer trên `$COPY` (khi `composer=true`) | Tự động | `$NEW_BIN $COMPOSER check-platform-reqs`; `why-not php <patch $NEW>` | Exit 0 hoặc mọi gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-003-20` | P3 | Chạy test tự động bằng `$NEW_BIN` (khi có) | Bán tự động (duyệt) | `$NEW_BIN vendor/bin/phpunit` | Exit 0 | Như `CHK-PHP-004-18` |
| `CHK-PHP-003-21` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 15–19 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-003-22` | P3 | Sửa mã theo báo cáo 15–19 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-003-23` | P4 | Nâng dependency Composer bằng Composer 2.10.x trên `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-21` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-003-24` | P4 | Nâng framework/CMS (khi `framework` ≠ none) | Thủ công | Như `CHK-PHP-004-22` | Thuộc dải §6 | Như `CHK-PHP-004-22` |
| `CHK-PHP-003-25` | P4 | Loader cho `$NEW` (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | Như `CHK-PHP-004-23` |
| `CHK-PHP-003-26` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-003-27` | P5 | (khi `mod_php`) Chuyển sang PHP-FPM của `$OLD` trước (BR-SCN-047) | Bán tự động (duyệt) | Như `CHK-PHP-004-25` | Health check ĐẠT | Như `CHK-PHP-004-25` |
| `CHK-PHP-003-28` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 30 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-003-29` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-003-30` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-003-31` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-003-32` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-003-33` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-003-34` | P7 | Gỡ `$OLD` (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 | `$OLD_BIN` không còn | Như `CHK-PHP-004-32` |
| `CHK-PHP-003-35` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:5.3`–`php:5.5` | Như `CHK-PHP-004-33` |

### 10.4 SCN-PHP-004 — PHP 5.6
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^5\.6\.\d+$` / 70 |
| Trạng thái, EOL | `EOL` từ 2018-12-31 (bản cuối 5.6.40); quá 2.852 ngày → ưu tiên Nghiêm trọng |
| Đích (BR-SCN-005) | 8.5; thay thế 8.4 khi framework tối đa 8.4 (Magento 2.4.8, Drupal 10.x/11.2, WordPress 6.7–6.8), 8.3 khi tối đa 8.3 |
| Lộ trình | Production: 5.6 → `$NEW` một lần (BR-SCN-007). Mã nguồn trên staging: sửa nhóm BC 7.0 → 7.x → 8.0 → 8.1–8.5; quét bậc thang `testVersion` 7.4 rồi `$NEW` |
| Dải BC | `BC-PHP-70-01` … `BC-PHP-85-02` (30 mục) |
| Extension bị xoá/thay | `mysql`, `ereg`, `mssql`, `sybase_ct` (7.0); `mcrypt` (7.2); `interbase`, `recode`, `wddx` (7.4); `xmlrpc` (8.0); `imap`, `oci8`, `pdo_oci`, `pspell` (8.4) |
| Framework/CMS | WordPress chạy 5.6 là ≤ 6.2 → phải lên 7.x (PHP ≥ 7.4); Laravel ≤ 5.x, Symfony ≤ 3.x, CodeIgniter 3, Joomla 3, Magento 1 không có bản hỗ trợ 8.5 trong §6 → nâng framework là việc của lập trình viên (mục 22) |
| Loader | ionCube/SourceGuardian cho 5.6 → cần loader 8.5 (ionCube 15.5.x, SourceGuardian 17.0.0) và file mã hoá chạy được trên loader mới |
| Composer | Inventory bằng Composer 2.2 LTS trên `$OLD_BIN`; `update` bằng Composer 2.10.x trên `$NEW_BIN` |
| Môi trường | Kiểm tra OS theo BR-SCN-016 (mục 09); OS hết hỗ trợ hoặc kho không có gói `$NEW` → dùng E10 hoặc máy chủ mới theo cách chuyển của SCN-PHP-001 (mục 25–28) |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-004-01` | P1 | Xác minh phiên bản, SAPI và nguồn cài của `$OLD_BIN` | Tự động | `$OLD_BIN -n -r 'echo PHP_VERSION,"\|",PHP_SAPI;'`; `readlink -f $OLD_BIN`; `dpkg -S`/`rpm -qf` | Chuỗi khớp `^5\.6\.\d+\|`; nguồn cài (gói/panel/tự build) ghi vào `scan --json` | Binary wrapper của panel trả sai nguồn → luôn `readlink -f` như v0.1 |
| `CHK-PHP-004-02` | P1 | Ánh xạ site → pool/handler → binary (FEAT-004) | Tự động | `nginx -T`, `apachectl -S`, `pool.d/*.conf` (`listen =`), cấu hình panel, `.htaccess` có `AddHandler`/`SetHandler` | 100% vhost có binary; số vhost `unmapped` = 0 | Handler khai báo trong `.htaccess` bị bỏ sót → luôn đọc `.htaccess` ở docroot |
| `CHK-PHP-004-03` | P1 | Kiểm kê extension, `php.ini`, `disable_functions`, giá trị pool | Tự động | `$OLD_BIN -m`; `$OLD_BIN --ini`; `php_admin_value[...]` trong pool | Danh sách lưu vào state; mỗi extension gắn nhãn theo BR-SCN-045 | Extension nạp riêng trong pool không thấy bằng CLI → đọc cả pool |
| `CHK-PHP-004-04` | P1 | Nhận diện framework/CMS, loader mã hoá, Composer (FEAT-054) | Tự động | `composer.lock` (`laravel/framework`, `symfony/*`, `drupal/core`, `magento/*`, `codeigniter4/framework`, `joomla/*`), `wp-includes/version.php`; nhận diện loader theo §7.1 | Mỗi site có `framework`, `framework_version`, `loader`, `composer` (true/false) | CMS tuỳ biến đổi tên file nhận diện → cho phép khai báo thủ công |
| `CHK-PHP-004-05` | P1 | Đánh giá bảo mật so sánh 5.6 với ứng viên 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng có ≥ 3 ứng viên: số CVE theo mức, số KEV, `lifecycle_status`, EOL, số ngày còn lại | Dữ liệu cũ hơn 30 ngày → cảnh báo theo BR-SCN-002 |
| `CHK-PHP-004-06` | P1 | Chọn và duyệt nhánh đích | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved`; đích ∈ {8.3, 8.4, 8.5} và nằm trong dải của framework/loader | Chọn 8.3 (EOL 2027-12-31) → phải lập kế hoạch lần 2 trong ≤ 14 tháng |
| `CHK-PHP-004-07` | P1 | Sao lưu docroot, cấu hình vhost/pool và CSDL | Bán tự động (duyệt) | `tar -czf` docroot vào thư mục backup; `copy` cấu hình vào manifest; tool đề xuất `mysqldump --single-transaction --routines <db>` để người vận hành duyệt | Mỗi file sao lưu > 0 byte và có SHA-256 trong manifest; khôi phục thử 1 file và 1 bảng trên staging thành công | Đĩa trống < 1,2 × (docroot + CSDL) → dừng, `ERR-SCN-412-01` |
| `CHK-PHP-004-08` | P1 | Dựng staging cách ly từ bản sao | Thủ công | Vhost/máy riêng, chặn inbound Internet, tắt SMTP và cron gửi ra ngoài | Trang chủ staging trả HTTP 200 trên 5.6; quy tắc firewall chỉ cho IP quản trị | Staging gửi email/thanh toán thật → tắt khoá API thật trên staging |
| `CHK-PHP-004-09` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | `df -BG --output=avail <phân vùng>`; `free -m`; `/etc/os-release` + endoflife.date; kho có gói `$NEW` | Đĩa ≥ 2 GB, RAM khả dụng ≥ 512 MB, OS còn hỗ trợ, gói đích tồn tại; nếu không → `ERR-SCN-412-01` | OS hết hỗ trợ → chuyển phương án E10/máy chủ mới |
| `CHK-PHP-004-10` | P2 | Ghim mặc định CLI/FPM hiện tại (BR-SCN-012) | Tự động | Debian/Ubuntu: `update-alternatives --set php $OLD_BIN`; ghi `readlink -f` của `/usr/bin/php` | `readlink -f /usr/bin/php` trước và sau cài trùng nhau | Kho không dùng alternatives → cron/systemd phải dùng đường dẫn tuyệt đối (mục 29) |
| `CHK-PHP-004-11` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | E1: `apt-get install -y php$NEW-fpm php$NEW-cli`; E2..E10 theo §8 | `$NEW_BIN -v` exit 0; dịch vụ FPM đích `active` | Kho bên thứ ba chậm vá (common §7 mục 5) → BR-SCN-015 |
| `CHK-PHP-004-12` | P2 | Cài extension tương ứng/thay thế (BR-SCN-045) | Bán tự động (duyệt) | Cài gói `php$NEW-<ext>`; so sánh `$OLD_BIN -m` với `$NEW_BIN -m` | Số extension thiếu chưa có phương án = 0 | `mysql`, `ereg`, `mcrypt` không có bản lõi → bắt buộc sửa mã (mục 20) |
| `CHK-PHP-004-13` | P2 | Tạo pool FPM cho `$NEW` từ pool cũ, loại directive đã xoá (BR-SCN-046) | Tự động | Sao chép pool, đổi `listen` sang socket mới; `php-fpm$NEW -t` | `php-fpm$NEW -t` exit 0; 0 directive thuộc danh sách BR-SCN-046; socket mới chưa bị chiếm trước khi tạo | `listen` trùng → FPM không khởi động; tool kiểm tra trước |
| `CHK-PHP-004-14` | P3 | Lint cú pháp toàn bộ mã bằng `$NEW_BIN` | Tự động | `find $SITE -type f \( -name '*.php' -o -name '*.inc' -o -name '*.phtml' \) -print0 \| xargs -0 -n 200 -P 2 sh -c '"$0" -l "$@" \|\| exit 1' $NEW_BIN 2>&1`; `-n 200` khi `$NEW` ≥ 8.3, `-n 1` khi `$NEW` < 8.3 (bản < 8.3 không lint nhiều file trong 1 lệnh); lớp bọc `sh -c` đổi mã thoát 255 thành 1 để `xargs` không dừng ở lô lỗi đầu tiên (§7.3) | ĐẠT: `xargs` exit 0, 0 dòng `Errors parsing`, số dòng `No syntax errors detected` = số file tìm được. Danh sách file lỗi lấy từ dòng `Errors parsing <file>`; dòng và thông điệp lấy từ dòng `Parse error`/`Fatal error … on line N`. `xargs` exit 123 → có file lỗi; exit khác 0 và 123 → lỗi công cụ, mục `FAILED` | Lint không thấy hàm bị xoá → mục 15, 16; tổng số dòng `No syntax errors detected` + `Errors parsing` < số file → tiến trình lint bị ngắt, chạy lại mục |
| `CHK-PHP-004-15` | P3 | Quét PHPCompatibility `testVersion` 7.4 (nhóm báo cáo) và `$NEW` (quyết định) | Tự động | Lệnh chuẩn §7.3 với `--runtime-set testVersion 7.4` và `$NEW` | Lượt `$NEW`: 0 `ERROR`; mọi `WARNING` có trong báo cáo kế hoạch | PHPCompatibility 10 đang alpha → luôn kèm mục 16 |
| `CHK-PHP-004-16` | P3 | Quét bộ luật BC của tool cho dải (5.6, `$NEW`] (BR-SCN-041) | Tự động | Mẫu quét §5 từ `BC-PHP-70-01` đến mục cuối ≤ `$NEW` | 0 hit mức `error` chưa miễn trừ; hit `warning` liệt kê theo file:dòng | Dương tính giả trong chuỗi/comment → báo cáo kèm trích đoạn 3 dòng để duyệt |
| `CHK-PHP-004-17` | P3 | Kiểm tra platform Composer (khi `composer=true`) (BR-SCN-044) | Tự động | `$NEW_BIN $COMPOSER check-platform-reqs`; `why-not php <patch $NEW>` trên `$COPY` | Exit 0, hoặc mọi gói chặn có phiên bản thay thế từ Packagist trong kế hoạch | `config.platform.php` ghim 5.6 → sửa ở mục 21 |
| `CHK-PHP-004-18` | P3 | Chạy test tự động của dự án bằng `$NEW_BIN` (khi có `phpunit.xml*`) | Bán tự động (duyệt) | `$NEW_BIN vendor/bin/phpunit` trên staging | Exit 0; 0 test lỗi | PHPUnit 4/5 không chạy trên 8.x → nâng PHPUnit ở mục 21 |
| `CHK-PHP-004-19` | P3 | (Tuỳ chọn) Rector trên `$COPY` (BR-SCN-011) | Bán tự động (duyệt) | `$NEW_BIN $TOOLS/vendor/bin/rector process $COPY --dry-run` → duyệt diff → chạy không `--dry-run` trên `$COPY` | Diff đã duyệt; mục 14–16 chạy lại đạt | Rector đổi ngữ nghĩa → bắt buộc chạy lại mục 18 |
| `CHK-PHP-004-20` | P3 | Sửa mã theo báo cáo 14–17 | Thủ công | Lập trình viên sửa trên nhánh mã/staging; tool chạy lại 14–17 | Mục 14–17 ĐẠT theo BR-SCN-042 | Ngoài phạm vi tool; công sức tỉ lệ với số hit |
| `CHK-PHP-004-21` | P4 | Nâng dependency Composer (khi `composer=true`) | Bán tự động (duyệt) | Trên `$COPY`: sửa ràng buộc, `$NEW_BIN $COMPOSER update --with-all-dependencies` | `check-platform-reqs` exit 0; OSV: 0 Critical, 0 `MAL-*` (FEAT-015) | Major framework mới đổi API → mục 22 |
| `CHK-PHP-004-22` | P4 | Nâng framework/CMS lên bản thuộc dải §6 cho `$NEW` (khi `framework` ≠ none) | Thủ công | Theo hướng dẫn nâng cấp của framework; WordPress: `wp core update` trên staging rồi `wp core verify-checksums` | Phiên bản framework thuộc dải §6; trang chủ staging HTTP 200 | Nâng qua nhiều major (vd Laravel 5 → 13) phải đi từng bước theo upgrade guide |
| `CHK-PHP-004-23` | P4 | Cài loader cho `$NEW` và chạy thử file mã hoá (khi `loader` ≠ none) (BR-SCN-043) | Bán tự động (duyệt) | Cài loader §7.1; `$NEW_BIN <file mã hoá mẫu>` | `$NEW_BIN -v` có dòng loader; file mẫu exit 0 | File mã hoá cho 5.6 không chạy trên loader 8.x → cần bản mới từ nhà cung cấp, `ERR-SCN-409-03` |
| `CHK-PHP-004-24` | P5 | Chụp baseline health check trên `$OLD` | Tự động | Bước C5: `hc.baseline_rounds` = 5 vòng cách `hc.baseline_interval_s` = 10 s ngay trước C6, trang chủ + ≤ 10 URL (DOC-SRS-QP-ENV-002 §4, BR-SCN-009); `W0` lấy từ log trong 600 s trước `t_C7` | Baseline hợp lệ theo DOC-SRS-QP-ENV-002 §4 (5 mẫu cùng mã HTTP, không 5xx); có mã HTTP, kích thước body trung vị, P95 mỗi URL và `W0`; tuổi baseline ≤ 120 s khi bắt đầu C7 (BR-HC-004), quá → thu lại | Baseline không hợp lệ ở trang chủ → `ERR-HC-412-02`, lượt chuyển `ABORTED` |
| `CHK-PHP-004-25` | P5 | (khi SAPI = `mod_php`) Chuyển site sang PHP-FPM của 5.6 trước (BR-SCN-047) | Bán tự động (duyệt) | Tạo pool 5.6, đổi handler, health check BR-SCN-009 | Health check ĐẠT trên FPM 5.6 | Không có FPM cho 5.6 trên OS → `ERR-SCN-412-02` |
| `CHK-PHP-004-26` | P5 | Chuyển site canary (lượng request thấp nhất) sang `$NEW` (§8 A2) | Bán tự động (duyệt) | E1: sửa `fastcgi_pass`/`SetHandler` → `nginx -t`/`apachectl configtest` → reload; manifest `copy` | Kiểm tra cấu hình exit 0; reload exit 0; mục 28 ĐẠT | Lỗi chỉ xuất hiện dưới tải → giữ canary ≥ 24 giờ trước mục 27 |
| `CHK-PHP-004-27` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như mục 26, tuần tự; site sau chỉ bắt đầu khi site trước ĐẠT mục 28 | 100% site trong kế hoạch `DONE` hoặc `WAIVED` | Chuyển đồng loạt bị cấm (BR-SCN-008) |
| `CHK-PHP-004-28` | P6 | Health check 10 phút sau mỗi lần chuyển + tự hoàn tác (BR-SCN-009, BR-SCN-010) | Tự động | Lấy mẫu 60 s, so baseline mục 24 | Đạt 6 tiêu chí BR-SCN-009; nếu không: hoàn tác ≤ 60 s và phát `ERR-SCN-500-01` | URL cần đăng nhập không được kiểm → mục 29 |
| `CHK-PHP-004-29` | P6 | Kiểm thử nghiệp vụ (đăng nhập, form, upload, thanh toán) | Thủ công | Kịch bản do chủ site cung cấp | 100% kịch bản pass; người kiểm ký xác nhận trên console | Thiếu kịch bản → ghi `WAIVED` kèm lý do |
| `CHK-PHP-004-30` | P6 | Chuyển cron và lệnh CLI của site sang `$NEW_BIN` | Bán tự động (duyệt) | `crontab -l -u $OWNER`, `/etc/cron.d/*`: thay `php`/`$OLD_BIN` bằng `$NEW_BIN`; manifest `copy` | 0 dòng cron của site còn gọi `$OLD_BIN`; lần chạy kế tiếp exit 0 | Cron gọi `php` không đường dẫn → phụ thuộc mặc định (BR-SCN-012) |
| `CHK-PHP-004-31` | P7 | Thống kê log `Deprecated` 7 ngày sau chuyển | Tự động | Đếm dòng `PHP Deprecated` theo thông điệp trong log pool `$NEW` | Báo cáo có số dòng theo nhóm thông điệp; số nhóm mới so với P3 = 0 hoặc đã đưa vào backlog | Deprecated của 8.x sẽ thành lỗi ở bản kế tiếp |
| `CHK-PHP-004-32` | P7 | Gỡ nhánh 5.6 (BR-SCN-014, §8 A4) | Bán tự động (duyệt) | Sau 14 ngày liên tục 0 request/tiến trình dùng `$OLD` | `$OLD_BIN` không còn; 0 pool `$OLD`; manifest có danh sách gói/prefix đã gỡ | Mất rollback 1 lệnh → console hiển thị cảnh báo trước nút duyệt |
| `CHK-PHP-004-33` | P7 | Cập nhật Dockerfile/compose/CI sang `$NEW` (khi có) | Bán tự động (duyệt) | v0.1 `check_dockerfiles`: thay `FROM php:5.6-*` bằng `php:$NEW-*` | 0 tham chiếu `php:5.6` trong Dockerfile/compose của dự án | Image cần build lại (ngoài phạm vi tool) |

### 10.5 SCN-PHP-005 — "PHP 6.x" và chuỗi phiên bản bất thường
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | Điều kiện (2) của BR-SCN-040: `^6\.`, `MAJOR` ≥ 10, `MAJOR.MINOR` mới hơn dữ liệu và không có trong nguồn pre-release, chuỗi không đúng định dạng, hoặc không đọc được phiên bản trong 10 s / 20 |
| Trạng thái | `UNKNOWN` → ưu tiên Nghiêm trọng (common §2.2); phát `ERR-SCN-422-01`; khoá mục `AUTO` thay đổi hệ thống (BR-SCN-013) |
| Căn cứ | PHP 6 chưa từng phát hành: dự án PHP 6 (Unicode) khởi động 2005, bị dừng 2010; RFC "Name of Next Release of PHP" chọn tên PHP 7 với 58 phiếu PHP 7 / 24 phiếu PHP 6 (wiki.php.net/rfc/php6). Do đó chuỗi `6.x` chỉ có thể là snapshot phát triển cũ, bản build sửa đổi, wrapper giả, hoặc binary bị can thiệp |
| Đích | Không đề xuất tự động. Sau khi người vận hành gán lại phiên bản thật (mục 10), kịch bản được tính lại theo BR-SCN-040 |
| Dải BC / framework / loader / Composer | Không áp dụng cho tới khi gán lại phiên bản |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-005-01` | P1 | Ghi chuỗi phiên bản thô từ 2 nguồn | Tự động | `$OLD_BIN -n -r 'echo PHP_VERSION,"\|",PHP_MAJOR_VERSION,".",PHP_MINOR_VERSION;'`; dòng 1 của `$OLD_BIN -v` (timeout 10 s mỗi lệnh) | 2 giá trị (hoặc mã thoát/timeout) lưu vào state; `ERR-SCN-422-01` hiển thị | Lệnh treo → tool kill sau 10 s, ghi `timeout` |
| `CHK-PHP-005-02` | P1 | Khoá tự động hoá cho binary (BR-SCN-013) | Tự động | Gắn cờ `locked` cho runtime trong state | Mọi job `fix`/`upgrade`/`switch` trên binary trả `SKIPPED` với lý do `scn.version.unrecognized` | Người vận hành bỏ qua cảnh báo → khoá ở tầng job, không chỉ ở giao diện |
| `CHK-PHP-005-03` | P1 | Định danh file thực thi | Tự động | `readlink -f $OLD_BIN`; `file <path>`; `sha256sum <path>`; `stat -c '%U %Y %s' <path>` | Đường dẫn thật, loại file (ELF/script), SHA-256, chủ sở hữu, mtime lưu vào state | Wrapper shell in phiên bản giả → `file` báo `script` |
| `CHK-PHP-005-04` | P1 | Kiểm tra gói sở hữu và toàn vẹn gói | Tự động | `dpkg -S <path>` + `dpkg --verify <pkg>`; `rpm -qf <path>` + `rpm -V <pkg>` | Có/không có gói; số dòng sai lệch checksum của binary = 0 hoặc được báo cáo | Sai lệch checksum → chuyển mục 09 ngay |
| `CHK-PHP-005-05` | P1 | Đối chiếu banner với thông tin build | Tự động | `$OLD_BIN -i` (trường `Build Date`, `Configure Command`, `Zend Engine`); so với chuỗi ở mục 01 | Báo cáo khớp/không khớp cho 3 trường | Ánh xạ Zend Engine ↔ major PHP là heuristic, chưa kiểm chứng trong phiên này |
| `CHK-PHP-005-06` | P1 | Quét dấu hiệu webshell/IOC (FEAT-005, kế thừa v0.1) | Tự động | `check_webshells` của v0.1 trên docroot dùng binary này | Báo cáo tối đa 50 kết quả mỗi nhóm; số kết quả ghi vào state | Chỉ báo cáo, không xoá (DOC-BRS-QP-001 §5.2) |
| `CHK-PHP-005-07` | P1 | Liệt kê site đang dùng binary (FEAT-004) | Tự động | Như `CHK-PHP-004-02` | Danh sách site; nếu ≥ 1 site công khai → ưu tiên giữ Nghiêm trọng | Site bị bỏ sót → đọc cả `.htaccess` |
| `CHK-PHP-005-08` | P1 | Tìm nguồn gốc binary trong lịch sử vận hành | Thủ công | Hỏi người cài; lịch sử lệnh (`/root/.bash_history`), log gói (`/var/log/dpkg.log`, `/var/log/dnf.log`) | Có kết luận nguồn gốc (snapshot/bản build/wrapper/không rõ) ghi vào console | Log đã xoay vòng → kết luận "không rõ" |
| `CHK-PHP-005-09` | P1 | Mở sự cố bảo mật khi binary bị can thiệp (khi mục 04 sai lệch hoặc mục 06 có kết quả) | Thủ công | Quy trình ứng cứu sự cố của tổ chức; cô lập máy | Mã sự cố được ghi vào kế hoạch | Xoá binary trước khi lấy bằng chứng làm mất dấu vết → sao lưu binary vào thư mục backup trước |
| `CHK-PHP-005-10` | P1 | Xác minh thủ công và gán lại phiên bản thật | Bán tự động (duyệt) | Người vận hành nhập phiên bản + bằng chứng (≥ 20 ký tự); BR-SCN-013 | Bản ghi audit có người duyệt, thời điểm; runtime được tính lại sang kịch bản ≠ SCN-PHP-005 | Gán sai phiên bản → mục 12 kiểm lại bằng binary sạch |
| `CHK-PHP-005-11` | P2 | Cài lại PHP từ nguồn chính thức (khi binary không đáng tin) | Bán tự động (duyệt) | `apt-get install --reinstall <pkg>` / `dnf reinstall <pkg>`; hoặc cài nhánh đích theo §8 A1 | `dpkg --verify`/`rpm -V` 0 sai lệch; `$BIN -v` trả phiên bản thuộc dải đã biết | Reinstall ghi đè bằng chứng → mục 09 trước |
| `CHK-PHP-005-12` | P6 | Chạy lại `scan` và xác nhận kịch bản mới | Tự động | `scan --json` | Binary được gán kịch bản ≠ SCN-PHP-005; cờ `locked` được gỡ | Vẫn bất thường → giữ khoá, quay lại mục 08 |
| `CHK-PHP-005-13` | P7 | Lưu bằng chứng vào báo cáo kiểm toán (FEAT-110) | Tự động | Xuất JSON/Markdown gồm kết quả mục 01–12 | Báo cáo có SHA-256 của binary, kết luận và người duyệt | Báo cáo chứa đường dẫn nội bộ → chỉ chia sẻ cho PER-04 |

### 10.6 SCN-PHP-006 — PHP 7.0–7.2
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^7\.[0-2]\.\d+$` / 80 |
| Trạng thái, EOL | `EOL`: 7.0 ngày 2019-01-10 (7.0.33), 7.1 ngày 2019-12-01 (7.1.33), 7.2 ngày 2020-11-30 (7.2.34); quá ≥ 2.152 ngày → Nghiêm trọng |
| Đích | 8.5 (thay thế 8.4/8.3 theo §6, §7) |
| Lộ trình | Production: một lần lên `$NEW`. Mã nguồn: xử lý `mcrypt` (rời lõi ở 7.2), `each()`/`create_function()` (deprecated 7.2, xoá 8.0), nhóm BC 8.0, sau đó deprecated 8.1–8.5; bậc thang `testVersion` 7.4, `$NEW` |
| Dải BC | 7.0: `BC-PHP-71-01` … `BC-PHP-85-02` (24 mục); 7.1: từ `BC-PHP-72-01` (23 mục); 7.2: từ `BC-PHP-73-01` (21 mục) |
| Extension bị xoá/thay | `mcrypt` (7.2); `interbase`, `recode`, `wddx` (7.4); `xmlrpc` (8.0); `imap`, `oci8`, `pdo_oci`, `pspell` (8.4) |
| Framework/CMS | WordPress 6.4–6.5 tối thiểu 7.0, 6.6–6.9 tối thiểu 7.2.24 → lên WordPress 7.x (PHP ≥ 7.4) cùng đợt; Laravel 6/7 (7.2–8.0) → lên Laravel 12/13 qua từng major; Magento 2.4.2/2.4.3 chỉ 7.4 (không áp dụng cho 7.0–7.2) |
| Loader | ionCube cho 7.x là gói legacy; đích 8.5 cần loader 15.5.x; **không** chọn 8.0 làm đích khi có ionCube (BR-SCN-043) |
| Composer | `$OLD` < 7.2.5: kiểm kê bằng Composer 2.2 LTS; `$OLD` 7.2.5–7.2.34: dùng được Composer 2.10.x |
| Môi trường | Ubuntu 18.04 dùng gói mặc định PHP 7.2 (Launchpad `php-defaults 60ubuntu1`), hết hỗ trợ chuẩn 2023-05-31, ESM đến 2028-04-26 → kèm overlay SCN-PHP-015 |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-006-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^7\.[0-2]\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-006-02` | P1 | Ánh xạ site → pool/handler → binary | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-006-03` | P1 | Kiểm kê extension, đặc biệt `mcrypt`, `xmlrpc`, `imap`, `interbase`, `wddx` | Tự động | `$OLD_BIN -m`; đếm hit tiền tố `mcrypt_`, `xmlrpc_`, `imap_`, `ibase_`, `wddx_` trong mã | Danh sách extension + số hit theo tiền tố trong state | Extension bật nhưng không dùng → `SKIPPED` theo BR-SCN-045 |
| `CHK-PHP-006-04` | P1 | Nhận diện framework/CMS, loader, Composer | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer` | Như `CHK-PHP-004-04` |
| `CHK-PHP-006-05` | P1 | Kiểm kê Composer trên `$OLD` (khi `composer=true`) | Tự động | `$OLD_BIN <composer 2.2 hoặc 2.10> show --locked --format=json` dưới `$OWNER` | Danh sách gói trong state; OSV đã chạy | Như `CHK-PHP-003-05` |
| `CHK-PHP-006-06` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | Như `CHK-PHP-004-05` |
| `CHK-PHP-006-07` | P1 | Chọn và duyệt nhánh đích | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved` | Như `CHK-PHP-004-06` |
| `CHK-PHP-006-08` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-006-09` | P1 | Dựng staging cách ly | Thủ công | Như `CHK-PHP-004-08` | Trang chủ staging HTTP 200 | Như `CHK-PHP-004-08` |
| `CHK-PHP-006-10` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 | Như `CHK-PHP-004-09` |
| `CHK-PHP-006-11` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-006-12` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | Theo §8 | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-006-13` | P2 | Cài extension tương ứng; thay `mcrypt` bằng `openssl`/`sodium` hoặc PECL đã duyệt (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | Dữ liệu đã mã hoá bằng mcrypt cần giải mã/mã hoá lại → lập trình viên xử lý ở mục 22 |
| `CHK-PHP-006-14` | P2 | Tạo pool FPM `$NEW` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm (`sql.safe_mode`, `track_errors`, `mbstring.func_overload`, `disable_classes`) | Như `CHK-PHP-004-13` |
| `CHK-PHP-006-15` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | Như `CHK-PHP-004-14` (0 dòng `Errors parsing`) | Như `CHK-PHP-004-14` |
| `CHK-PHP-006-16` | P3 | Quét PHPCompatibility `testVersion` 7.4 và `$NEW` | Tự động | Lệnh chuẩn §7.3 | Lượt `$NEW`: 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-006-17` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] | Tự động | Mẫu §5 | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-006-18` | P3 | Kiểm tra so sánh lỏng chuỗi–số (BC-PHP-80-01) bằng test và log | Bán tự động (duyệt) | Liệt kê `==`/`!=`/`switch` có 1 vế là literal số trong mã của site; yêu cầu test bao phủ các vị trí này | Mỗi vị trí trong danh sách có test hoặc đã đổi sang `===` | Không phát hiện tĩnh đầy đủ → health check P6 là lớp chặn cuối |
| `CHK-PHP-006-19` | P3 | Kiểm tra platform Composer (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 hoặc gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-006-20` | P3 | Chạy test tự động bằng `$NEW_BIN` (khi có) | Bán tự động (duyệt) | `$NEW_BIN vendor/bin/phpunit` | Exit 0 | Như `CHK-PHP-004-18` |
| `CHK-PHP-006-21` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 15–19 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-006-22` | P3 | Sửa mã theo báo cáo 15–19 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-006-23` | P4 | Nâng dependency Composer trên `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-21` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-006-24` | P4 | Nâng framework/CMS (khi `framework` ≠ none) | Thủ công | Như `CHK-PHP-004-22` | Thuộc dải §6 | Như `CHK-PHP-004-22` |
| `CHK-PHP-006-25` | P4 | Loader cho `$NEW` (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | Như `CHK-PHP-004-23` |
| `CHK-PHP-006-26` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-006-27` | P5 | (khi `mod_php`) Chuyển sang PHP-FPM của `$OLD` trước | Bán tự động (duyệt) | Như `CHK-PHP-004-25` | Health check ĐẠT | Như `CHK-PHP-004-25` |
| `CHK-PHP-006-28` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 30 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-006-29` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-006-30` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-006-31` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-006-32` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-006-33` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-006-34` | P7 | Gỡ `$OLD` (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 | `$OLD_BIN` không còn | Như `CHK-PHP-004-32` |
| `CHK-PHP-006-35` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:7.0`–`php:7.2` | Như `CHK-PHP-004-33` |

### 10.7 SCN-PHP-007 — PHP 7.3–7.4
| Thuộc tính | Giá trị |
| :--- | :--- |
| `version_match` / `match_order` | `^7\.[34]\.\d+$` / 90 |
| Trạng thái, EOL | `EOL`: 7.3 ngày 2021-12-06 (7.3.33), 7.4 ngày 2022-11-28 (7.4.33); quá ≥ 1.424 ngày → Nghiêm trọng |
| Đích | 8.5 (thay thế 8.4/8.3 theo §6, §7) |
| Lộ trình | Production: một lần lên `$NEW`. Mã nguồn: nhóm BC 8.0 (6 mục, nhiều nhất trong dải), sau đó deprecated 8.1–8.5; `testVersion` `$NEW` (không cần bậc thang) |
| Dải BC | 7.3: `BC-PHP-74-01` … `BC-PHP-85-02` (20 mục); 7.4: từ `BC-PHP-80-01` (18 mục) |
| Extension bị xoá/thay | `interbase`, `recode`, `wddx` (7.4, khi `$OLD` = 7.3); `xmlrpc` (8.0); `imap`, `oci8`, `pdo_oci`, `pspell` (8.4) |
| Framework/CMS | WordPress 7.x hỗ trợ 7.4–8.5 → nâng WordPress trước trên 7.4, rồi đổi PHP; Laravel 8 (7.3–8.1) → lên 12/13; Magento 2.4.2/2.4.3 (chỉ 7.4) → Magento 2.4.8 (8.3–8.4) hoặc 2.4.9 (chỉ 8.5) phải đổi cùng đợt với PHP |
| Loader | ionCube cho 7.4 có (loader 10.4.0 trở lên); đích cần loader tương ứng (§7.1) |
| Composer | Composer 2.10.x chạy được trên `$OLD` (≥ 7.2.5) |
| Môi trường | Gói mặc định PHP 7.4 trên Ubuntu 20.04 (`php-defaults 75`, hết hỗ trợ chuẩn 2025-05-31, ESM đến 2030-04-23) và Debian 11 (`php-defaults 76`, LTS đến 2026-08-31) → kèm overlay SCN-PHP-015 |

| Mã | GĐ | Hành động | Loại | Lệnh / cơ chế kiểm tra | Tiêu chí hoàn thành | Rủi ro |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `CHK-PHP-007-01` | P1 | Xác minh phiên bản, SAPI, nguồn cài | Tự động | Như `CHK-PHP-004-01` | Chuỗi khớp `^7\.[34]\.\d+`; nguồn cài trong `scan --json` | Như `CHK-PHP-004-01` |
| `CHK-PHP-007-02` | P1 | Ánh xạ site → pool/handler → binary | Tự động | Như `CHK-PHP-004-02` | `unmapped` = 0 | Như `CHK-PHP-004-02` |
| `CHK-PHP-007-03` | P1 | Kiểm kê extension (`xmlrpc`, `imap`, `oci8`, `pspell`, `interbase`, `wddx`) và directive `mbstring.func_overload`, `track_errors` | Tự động | `$OLD_BIN -m`; `$OLD_BIN -i`; đếm hit tiền tố hàm | Danh sách + số hit trong state | Như `CHK-PHP-006-03` |
| `CHK-PHP-007-04` | P1 | Nhận diện framework/CMS, loader, Composer | Tự động | Như `CHK-PHP-004-04` | Mỗi site có `framework`, `loader`, `composer` | Như `CHK-PHP-004-04` |
| `CHK-PHP-007-05` | P1 | Đánh giá bảo mật so sánh với 8.3, 8.4, 8.5 | Tự động | FEAT-030, FEAT-032 | Bảng ≥ 3 ứng viên đủ trường | Như `CHK-PHP-004-05` |
| `CHK-PHP-007-06` | P1 | Chọn và duyệt nhánh đích; xác định có cần nâng framework cùng đợt (Magento) | Bán tự động (duyệt) | BR-SCN-005 + §6 + §7.1 | Kế hoạch `approved`, có cờ `framework_upgrade_same_batch` = true/false | Như `CHK-PHP-004-06` |
| `CHK-PHP-007-07` | P1 | Sao lưu docroot, cấu hình, CSDL | Bán tự động (duyệt) | Như `CHK-PHP-004-07` | File > 0 byte, SHA-256, khôi phục thử thành công | Như `CHK-PHP-004-07` |
| `CHK-PHP-007-08` | P1 | Dựng staging cách ly | Thủ công | Như `CHK-PHP-004-08` | Trang chủ staging HTTP 200 | Như `CHK-PHP-004-08` |
| `CHK-PHP-007-09` | P2 | Kiểm tra điều kiện tiên quyết (BR-SCN-016) | Tự động | Như `CHK-PHP-004-09` | Đạt BR-SCN-016 | Như `CHK-PHP-004-09` |
| `CHK-PHP-007-10` | P2 | Ghim mặc định CLI/FPM (BR-SCN-012) | Tự động | Như `CHK-PHP-004-10` | `readlink -f /usr/bin/php` không đổi | Như `CHK-PHP-004-10` |
| `CHK-PHP-007-11` | P2 | Cài `$NEW` song song (§8 A1) | Bán tự động (duyệt) | Theo §8 | `$NEW_BIN -v` exit 0; FPM `active` | Như `CHK-PHP-004-11` |
| `CHK-PHP-007-12` | P2 | Cài extension tương ứng/thay thế (BR-SCN-045) | Bán tự động (duyệt) | So `-m` 2 bên | Thiếu chưa có phương án = 0 | `imap` rời lõi ở 8.4 → PECL hoặc thư viện userland |
| `CHK-PHP-007-13` | P2 | Tạo pool FPM `$NEW` (BR-SCN-046) | Tự động | `php-fpm$NEW -t` | Exit 0; 0 directive bị cấm | Như `CHK-PHP-004-13` |
| `CHK-PHP-007-14` | P3 | Lint cú pháp bằng `$NEW_BIN` | Tự động | Như `CHK-PHP-004-14` | Như `CHK-PHP-004-14` (0 dòng `Errors parsing`) | Ternary lồng không ngoặc, offset `{}` là lỗi biên dịch ở 8.0 (BC-PHP-80-04) |
| `CHK-PHP-007-15` | P3 | Quét PHPCompatibility `testVersion` `$NEW` | Tự động | Lệnh chuẩn §7.3 | 0 `ERROR` | Như `CHK-PHP-004-15` |
| `CHK-PHP-007-16` | P3 | Quét bộ luật BC dải (`$OLD`, `$NEW`] | Tự động | Mẫu §5 | 0 hit `error` chưa miễn trừ | Như `CHK-PHP-004-16` |
| `CHK-PHP-007-17` | P3 | Kiểm tra so sánh lỏng chuỗi–số (BC-PHP-80-01) | Bán tự động (duyệt) | Như `CHK-PHP-006-18` | Mỗi vị trí có test hoặc đã đổi sang `===` | Như `CHK-PHP-006-18` |
| `CHK-PHP-007-18` | P3 | Kiểm tra platform Composer (khi `composer=true`) | Tự động | Như `CHK-PHP-004-17` | Exit 0 hoặc gói chặn có bản thay thế | Như `CHK-PHP-004-17` |
| `CHK-PHP-007-19` | P3 | Chạy test tự động bằng `$NEW_BIN` (khi có) với `error_reporting=E_ALL` | Bán tự động (duyệt) | `$NEW_BIN -d error_reporting=-1 vendor/bin/phpunit` | Exit 0; số thông báo `Deprecated` được ghi vào báo cáo | Như `CHK-PHP-004-18` |
| `CHK-PHP-007-20` | P3 | (Tuỳ chọn) Rector trên `$COPY` | Bán tự động (duyệt) | Như `CHK-PHP-004-19` | Diff đã duyệt; 14–18 đạt | Như `CHK-PHP-004-19` |
| `CHK-PHP-007-21` | P3 | Sửa mã theo báo cáo 14–19 | Thủ công | Lập trình viên | BR-SCN-042 ĐẠT | Như `CHK-PHP-004-20` |
| `CHK-PHP-007-22` | P4 | Nâng dependency Composer trên `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-21` | `check-platform-reqs` exit 0; OSV 0 Critical, 0 `MAL-*` | Như `CHK-PHP-004-21` |
| `CHK-PHP-007-23` | P4 | (khi `framework=wordpress`) Nâng WordPress lên 7.x trên `$OLD` trước khi đổi PHP | Bán tự động (duyệt) | `wp core update` trên staging rồi production; `wp core verify-checksums` (kế thừa v0.1) | Phiên bản core = `latest` của `stable-check`; verify-checksums exit 0 | Plugin không tương thích WordPress 7.x → `wp plugin list --update=available` và duyệt từng plugin |
| `CHK-PHP-007-24` | P4 | Nâng framework/CMS khác (khi `framework` ∉ {none, wordpress}) | Thủ công | Như `CHK-PHP-004-22` | Thuộc dải §6 | Magento phải nâng cùng đợt với PHP (mục 06) |
| `CHK-PHP-007-25` | P4 | Loader cho `$NEW` (khi `loader` ≠ none) | Bán tự động (duyệt) | Như `CHK-PHP-004-23` | File mẫu exit 0 | Như `CHK-PHP-004-23` |
| `CHK-PHP-007-26` | P5 | Chụp baseline health check | Tự động | BR-SCN-009 | Baseline đủ trường | Như `CHK-PHP-004-24` |
| `CHK-PHP-007-27` | P5 | (khi `mod_php`) Chuyển sang PHP-FPM của `$OLD` trước | Bán tự động (duyệt) | Như `CHK-PHP-004-25` | Health check ĐẠT | Như `CHK-PHP-004-25` |
| `CHK-PHP-007-28` | P5 | Chuyển site canary (§8 A2) | Bán tự động (duyệt) | Như `CHK-PHP-004-26` | Mục 30 ĐẠT | Như `CHK-PHP-004-26` |
| `CHK-PHP-007-29` | P5 | Chuyển từng site còn lại, mỗi site 1 lần duyệt | Bán tự động (duyệt) | Như `CHK-PHP-004-27` | 100% site `DONE`/`WAIVED` | Như `CHK-PHP-004-27` |
| `CHK-PHP-007-30` | P6 | Health check 10 phút + tự hoàn tác | Tự động | BR-SCN-009/010 | Đạt 6 tiêu chí | Như `CHK-PHP-004-28` |
| `CHK-PHP-007-31` | P6 | Kiểm thử nghiệp vụ | Thủ công | Kịch bản chủ site | 100% pass | Như `CHK-PHP-004-29` |
| `CHK-PHP-007-32` | P6 | Chuyển cron/CLI sang `$NEW_BIN` | Bán tự động (duyệt) | Như `CHK-PHP-004-30` | 0 cron gọi `$OLD_BIN` | Như `CHK-PHP-004-30` |
| `CHK-PHP-007-33` | P7 | Thống kê log `Deprecated` 7 ngày | Tự động | Như `CHK-PHP-004-31` | Báo cáo theo nhóm | Như `CHK-PHP-004-31` |
| `CHK-PHP-007-34` | P7 | Gỡ `$OLD` (BR-SCN-014) | Bán tự động (duyệt) | §8 A4 | `$OLD_BIN` không còn | Như `CHK-PHP-004-32` |
| `CHK-PHP-007-35` | P7 | Cập nhật Dockerfile/CI (khi có) | Bán tự động (duyệt) | Như `CHK-PHP-004-33` | 0 tham chiếu `php:7.3`, `php:7.4` | Như `CHK-PHP-004-33` |

## 11. Giả định và câu hỏi mở
| STT | Nội dung | Loại | Người quyết định |
| :--- | :--- | :--- | :--- |
| 1 | PHPCompatibility 10.x đang ở bản alpha (10.0.0-alpha2); BR-SCN-042 dùng nó làm điều kiện bắt buộc kết hợp bộ luật BC của tool và `php -l`. Khi 10.0.0 ổn định phát hành, cập nhật §7.3 (ràng buộc ghim, `composer.lock` và SHA-256 của catalog công cụ) | Giả định | BA + Dev |
| 2 | Lệnh panel ở §8 E5–E9 đã được đối chiếu tài liệu/mã nguồn chính thức (PB-007..PB-012, KC = Có) nhưng chưa chạy thử trên máy có panel; lệnh ghi KC = Chưa/Gián tiếp và tên gói Remi/Alpine (E2, E4) ghi "chưa kiểm chứng" phải được QA chạy thử trên máy có panel/OS tương ứng trước khi đặt `verified=true` và chuyển mục `SEMI` thành tự động hoá đầy đủ (BR-ENV-010) | Ràng buộc | QA |
| 3 | ionCube: tổ hợp Encoder → Loader đã có một phần ở bảng 7.1.1 (định dạng PHP 8.2–8.4 trên loader 8.3–8.5); định dạng PHP 8.1 trở về trước trên loader 8.2+ và toàn bộ SourceGuardian chưa kiểm chứng. Cách tool biết định dạng Encoder của 1 file (đọc header file hay nhà cung cấp khai báo) chưa quyết; checklist dùng phép chạy thử file mẫu làm tiêu chí cuối | Câu hỏi mở | PO + nhà cung cấp loader |
| 4 | Ngày hết hỗ trợ dự kiến của 8.6 (2028-12-31 / 2030-12-31) suy ra từ RFC `release_cycle_update`, chưa có trên `supported-versions.php` | Giả định | Tool tự cập nhật khi php.net công bố |
| 5 | Ma trận §6 lấy tại 2026-10-22; snapshot dữ liệu (FEAT-017) phải chứa bảng này và được làm mới mỗi lần phát hành tool | Ràng buộc | Dev |
| 6 | Heuristic phát hiện phụ thuộc register globals (`CHK-PHP-001-17`) có thể bỏ sót; kiểm thử nghiệp vụ là lớp chặn cuối | Giả định | PO duyệt mức chấp nhận |
| 7 | Số đo lint theo lô ở §7.3 (0,92 s cho 10.000 file nhỏ trên 4 vCPU, PHP 8.3.6, đo 2026-10-23) chỉ là số đo của bước lint; cần ghi vào `NFR-PERF-005` ở [nfr.md](nfr.md) và đo lại toàn bộ chỉ tiêu (lint + PHPCompatibility + Composer) trên bộ mã WordPress + Laravel mẫu. Hành vi `-n 1` cho `$NEW` < 8.3 suy từ `UPGRADING` 8.3, chưa chạy thử trên binary < 8.3 | Ràng buộc | Dev + QA |

## 12. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22, trừ khi ghi khác.

| Nguồn | URL | Dùng cho |
| :--- | :--- | :--- |
| Quy ước chung của phụ lục | [version-scenarios-common.md](version-scenarios-common.md) (DOC-SRS-QP-SCN-000) | Trạng thái, ưu tiên, BR-SCN-001..018, ERR-SCN |
| Biên bản làm rõ yêu cầu v2 | `docs/php-quickpatch/brainstorms/quickpatch-v2-console.md` (DOC-BRS-QP-001) | Scope, quyết định cài song song, Rector tuỳ chọn |
| PRD v2 | `docs/php-quickpatch/01-prd.md` (DOC-PRD-QP-001) | FEAT, KR2.2 |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `discover_php_bins`, `php_version`, `pkg_owner`, `php_upgrade`, `php_mitigate`, `restart_php_services`, manifest, `check_dockerfiles`, `check_webshells` |
| php.net vòng đời | https://www.php.net/supported-versions.php, https://www.php.net/eol.php | §3 |
| php.net bản phát hành | https://www.php.net/releases/active.php, https://www.php.net/pre-release-builds.php?format=json | 8.2.35/8.3.36/8.4.27/8.5.12 (21 Oct 2026), 8.6.0RC4; cấu trúc JSON pre-release (gọi thử 2026-10-22: khoá `8.2.27`, `8.3.31`, `8.4.27`, `8.5.12` có `release.enabled=false`, `dev_version` dạng `8.x.y-dev`; khoá `8.6.0` có `release.version=8.6.0RC4`, không có `enabled`) dùng cho BR-SCN-040 và bảng 4.1 |
| php.net hằng số định sẵn | https://www.php.net/manual/en/reserved.constants.php (`PHP_VERSION`, `PHP_EXTRA_VERSION`); https://php.watch/codex/PHP_VERSION (định dạng `MAJOR.MINOR.RELEASE-<Extra-info>`) | Hậu tố `PHP_EXTRA_VERSION` trong BR-SCN-040; định dạng cụ thể của gói Ubuntu (`-1ubuntu2.24`): chưa chạy thử |
| Lịch PHP 8.6 | https://wiki.php.net/todo/php86 | RC5 2026-11-05, GA 2026-11-19 |
| RFC chu kỳ phát hành | https://wiki.php.net/rfc/release_cycle_update | 2 năm sửa lỗi + 2 năm bảo mật, kết thúc 31/12, từ 8.2 |
| RFC tên PHP 7 | https://wiki.php.net/rfc/php6 | PHP 6 bị bỏ, 58/24 phiếu |
| endoflife.date | https://endoflife.date/api/php.json, `/api/laravel.json`, `/api/wordpress.json`, `/api/magento.json`, `/api/symfony.json`, `/api/drupal.json`, `/api/joomla.json`, `/api/ubuntu.json`, `/api/debian.json`, `/api/rhel.json` | §3, §6, vòng đời OS |
| Migration guide php.net | https://www.php.net/manual/en/migration56.incompatible.php, `migration56.deprecated`, `migration70.incompatible`, `migration70.removed-exts-sapis`, `migration70.deprecated`, `migration71.incompatible`, `migration71.deprecated`, `migration72.incompatible`, `migration72.deprecated`, `migration72.other-changes`, `migration73.incompatible`, `migration73.deprecated`, `migration74.incompatible`, `migration74.deprecated`, `migration74.removed-extensions`, `migration80.incompatible`, `migration80.deprecated`, `migration81.incompatible`, `migration81.deprecated`, `migration82.incompatible`, `migration82.deprecated`, `migration83.incompatible`, `migration83.deprecated`, `migration84.incompatible`, `migration84.deprecated`, `migration84.removed-extensions`, `migration85.incompatible`, `migration85.deprecated` | §5 |
| php.net PHP 8.5 (đọc 2026-10-22) | https://www.php.net/manual/en/migration85.incompatible.php (mục Opcache: OPcache luôn biên dịch sẵn và luôn nạp, không còn `opcache.so`, `zend_extension=opcache.so` phát warning; xoá `disable_classes`); https://www.php.net/manual/en/migration85.deprecated.php (`__sleep()`/`__wakeup()` soft-deprecated; backtick, cast không chuẩn, `case` kết thúc bằng `;`, `null` làm offset, `report_memleaks`, `register_argc_argv`); https://wiki.php.net/rfc/soft-deprecate-sleep-wakeup ("documentation-only", Implemented, 26/5 phiếu); https://raw.githubusercontent.com/php/php-src/PHP-8.5/UPGRADING (`__wakeup()` của các lớp Date bị deprecated) | BC-PHP-85-01, BC-PHP-85-02, BR-SCN-041 (mức `info`), BR-SCN-045, BR-SCN-046 |
| Migration guide cũ | https://php-legacy-docs.zend.com/manual/php5/en/migration5.incompatible, `migration5.oop`, `migration54.incompatible` | BC-PHP-50, BC-PHP-54 |
| php-src UPGRADING | https://raw.githubusercontent.com/php/php-src/PHP-5.3/UPGRADING (và nhánh `PHP-5.4`, `PHP-5.5`, `PHP-7.0`, `PHP-8.0`, `PHP-8.6`) | BC-PHP-53/54/55, `/e` (7.0), `xmlrpc` (8.0), BC-PHP-86 |
| php-src UPGRADING 8.3 (đọc 2026-10-23) | https://raw.githubusercontent.com/php/php-src/PHP-8.3/UPGRADING (mục CLI: "It is now possible to lint multiple files") | `CHK-PHP-004-14`, §7.3 (lint theo lô) |
| GNU xargs (đọc 2026-10-23) | https://man7.org/linux/man-pages/man1/xargs.1.html ("If any invocation of the command exits with a status of 255, xargs will stop immediately"; mã thoát 123/124); chạy thử GNU findutils 4.9.0 | `CHK-PHP-004-14`, §7.3 (lớp bọc `sh -c`) |
| WordPress | https://make.wordpress.org/core/handbook/references/php-compatibility-and-wordpress-versions/ | §6 |
| WordPress 3.2 (đọc 2026-10-23) | https://wordpress.org/documentation/wordpress-version/version-3-2/ ("Requirements Changes – PHP 5.2.4 or greater (old requirement – since WordPress 2.5 was PHP 4.3 or greater)", phát hành July 4, 2011) | SCN-PHP-001 hàng Framework/CMS |
| Laravel | https://laravel.com/docs/13.x/releases | §6 |
| Symfony | https://symfony.com/releases | §6 |
| CodeIgniter | https://codeigniter.com/user_guide/intro/requirements.html | §6 |
| Adobe Commerce | https://experienceleague.adobe.com/en/docs/commerce-operations/installation-guide/system-requirements | §6 |
| Drupal | https://www.drupal.org/docs/getting-started/system-requirements/php-requirements | §6 |
| Joomla | https://manual.joomla.org/docs/next/get-started/technical-requirements/, https://manual.joomla.org/docs/5.4/get-started/technical-requirements/ | §6 |
| ionCube | https://www.ioncube.com/loaders.php (đọc lại 2026-10-23: changelog 12.0.1, 13.0.0, 13.3.0, 14.0.0, 14.4.0, 15.0.0, 15.5.0, 15.5.1); https://blog.ioncube.com/2022/08/12/ioncube-php-8-1-support-faq-were-almost-ready/; https://support.cpanel.net/hc/en-us/articles/1500001647462 | §7.1 mốc loader theo nhánh, bảng 7.1.1 Encoder → Loader (không có loader PHP 8.0) |
| SourceGuardian | https://www.sourceguardian.com/loaders.html | §7.1 |
| Composer | https://getcomposer.org/versions; https://repo.packagist.org/p2/composer/composer.json; https://getcomposer.org/doc/00-intro.md (đọc 2026-10-23: "Composer in its latest version requires PHP 7.2.5 to run. A long-term-support version (2.2.x) still offers support for PHP 5.3.2+") | §7.2, BR-SCN-044 |
| Packagist | https://repo.packagist.org/p2/phpcompatibility/php-compatibility.json, https://repo.packagist.org/p2/phpcompatibility/php-compatibility~dev.json (`dev-develop`, `branch-alias` `10.x-dev`, 2026-09-21), `phpcompatibility/phpcompatibility-wp`, `phpcompatibility/phpcompatibility-paragonie` (2.0.0-alpha2), `squizlabs/php_codesniffer`, `rector/rector` | §7.3 (phiên bản, ràng buộc, `dist.shasum` rỗng) |
| Playbook môi trường | [environment-playbooks.md](environment-playbooks.md) (DOC-SRS-QP-ENV-001), [environment-playbooks-panels.md](environment-playbooks-panels.md) (DOC-SRS-QP-ENV-004) | §8 E1–E10, lệnh panel E5–E9 đã kiểm chứng |
| PHPCompatibility README | https://raw.githubusercontent.com/PHPCompatibility/PHPCompatibility/develop/README.md | `testVersion`, lệnh cài 10.x |
| Kho gói PHP | https://launchpad.net/~ondrej/+archive/ubuntu/php; https://rpms.remirepo.net/wizard/; Launchpad API `getPublishedSources` (`php-defaults`); https://sources.debian.org/api/src/php-defaults/ | §8, gói mặc định theo OS |
| cPanel WHM API 1 | https://api.docs.cpanel.net/openapi/whm/operation/php_set_vhost_versions/ | §8 E5 (tên hàm và tham số `version`/`vhost`/`php_fpm` kiểm chứng trong PB-007) |
| Quy tắc nghiệp vụ tổng hợp, SRS chính, health check | [business-rules.md](business-rules.md) (DOC-SRS-QP-BR-001) §1, §2, §6 mục 1; [spec.md](spec.md) (DOC-SRS-QP-001) §2.3, §3.3.2, §3.3.4; [environment-playbooks-healthcheck.md](environment-playbooks-healthcheck.md) (DOC-SRS-QP-ENV-002) §2, §4, `BR-HC-004`; [environment-playbooks.md](environment-playbooks.md) §5.1 bước C5 | Cột "Phạm vi áp dụng" (§4); tham số baseline của `CHK-PHP-004-24` |
| Chuẩn tài liệu | `luongkam/openba-kit/skills/srs/SKILL.md`, `rules/02` (§2 Phạm vi áp dụng), `03`, `05`, `09`, `11`, `16`, `18`, `19` | Cấu trúc, mã BR/ERR, metadata |
