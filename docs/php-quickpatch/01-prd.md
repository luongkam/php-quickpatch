---
id: DOC-PRD-QP-001
title: Tài liệu Yêu cầu Sản phẩm (PRD) — php-quickpatch v2
version: 1.0.1
phase: Planning
domain: Security Patch Management
tags: [prd, php, nodejs, cve, kev, eol, lts, upgrade, dashboard, web-console, openba]
depends_on:
  - DOC-BRS-QP-001
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Tài liệu Yêu cầu Sản phẩm (PRD) — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo PRD từ biên bản `DOC-BRS-QP-001` và baseline `php-quickpatch.sh` v0.1.0; dữ liệu vòng đời và nguồn CVE kiểm chứng trực tuyến ngày 2026-10-22 |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review và `CR-SRS-04` của SRS (`srs/spec.md` §4.3): §2.1 đổi `PER-04` từ Secondary sang Primary (chỉ đọc, xuất báo cáo, tra cứu audit) vì là actor chính của `UC-JOB-003`, `UC-RPT-001`, `UC-RPT-002` theo rule 17, ghi vai trò Secondary khi chỉ nhận báo cáo do người khác xuất; §3.3 thay mã kịch bản `SCN-PHP-4`, `SCN-PHP-82`, `SCN-NODE-EOL`… bằng mã SRS `SCN-PHP-001..016`, `SCN-NODE-001..012`, thêm dòng `SCN-NODE-008` và ánh xạ `SCN-ENV-*` sang kịch bản OVERLAY/playbook; §4.2–§4.14 thay cột "Mã FR dự kiến" (placeholder `FR-*-xxx`, gồm 3 tiền tố không có trong SRS `FR-SCN-PHP`, `FR-SCN-NODE`, `FR-ASMT-BKP`) bằng cột "Mã FR (SRS)" lấy từ ma trận truy vết `srs/spec.md` §4.2 cho đủ 70 FEAT; FEAT-020/021 ghi số kịch bản theo SRS; §9 thêm 3 nguồn đối chiếu (SRS, phụ lục kịch bản/playbook, use case) |

## Metadata
- **Product Name**: php-quickpatch v2 (CLI Bash + Web Console Python 3 stdlib)
- **Document Version**: 1.0.1
- **Status**: Draft
- **Product Owner**: Chủ sản phẩm (người vận hành nhiều hệ thống PHP/Node.js)
- **Lead BA**: BA Agent
- **Last Updated**: 2026-10-22
- **Tài liệu đầu vào**: `brainstorms/quickpatch-v2-console.md` (`DOC-BRS-QP-001`), `/home/user/php-quickpatch/php-quickpatch.sh` (v0.1.0, 881 dòng)
- **Tài liệu kế tiếp**: Roadmap (`02-roadmap.md`), SRS (đặc tả FR/BR/ERR/NFR chi tiết)

---

## 1. Tầm nhìn & Mục tiêu sản phẩm (Vision & Objectives)

### 1.1 Tuyên ngôn sứ mệnh (Product Vision Statement)
**Dành cho** người vận hành VPS, quản trị hosting có panel và DevOps quản lý Docker đang chạy nhiều phiên bản PHP (từ 4.x đến 8.5) và Node.js trên cùng hạ tầng,
**những người cần** biết trong ≤ 24 giờ kể từ khi bản vá được công bố runtime nào đang có CVE nghiêm trọng (đặc biệt CVE trong danh mục CISA KEV), runtime nào đã hết hỗ trợ (EOL), và cần một lộ trình nâng cấp có thể hoàn tác,
**php-quickpatch v2** là bộ công cụ không cần agent thường trú gồm CLI Bash và web console cục bộ,
**giúp** tự động lấy dữ liệu CVE/vòng đời từ nguồn online, phân loại máy chủ theo kịch bản phiên bản, so sánh rủi ro giữa phiên bản hiện tại và phiên bản nâng cấp ứng viên, sinh checklist công việc chi tiết (gồm extension, Composer, npm, framework/CMS), rồi thực thi vá cùng nhánh hoặc nâng cấp khác major theo mô hình cài song song, chuyển từng site và rollback bằng 1 lệnh.
**Khác với** v0.1.0 (dữ liệu advisory ghi cứng, chỉ phục vụ 1 đợt bản vá) và với trình quản lý phiên bản của panel (không đánh giá CVE/KEV, không quét tương thích mã), v2 lấy dữ liệu theo thời gian thực từ nguồn chính thức, vẫn hoạt động offline bằng snapshot, và mọi thay đổi đều có manifest rollback.

### 1.2 Bối cảnh & baseline v0.1.0 (phải kế thừa)
v0.1.0 đã có các hành vi dưới đây. v2 **giữ nguyên** hành vi và tham số dòng lệnh của chúng (tương thích ngược), chỉ thay nguồn dữ liệu và bổ sung tính năng.

| STT | Hành vi v0.1.0 (đã đọc trong mã nguồn) | Cách v2 xử lý | Feature |
| :--- | :--- | :--- | :--- |
| 1 | 3 chế độ `scan` (mặc định), `fix`, `rollback [ID]`; tùy chọn `--path`, `--only`, `--dry-run`, `--no-restart`, `--no-memlimit`, `--offline`, `--version`, `-h` | Giữ nguyên cú pháp; bổ sung `--json` và các lệnh mới | FEAT-100, FEAT-101 |
| 2 | Mã thoát: 0 = không còn vấn đề, 1 = còn vấn đề, 2 = lỗi tham số/runtime | Giữ nguyên | FEAT-101 |
| 3 | Nhận diện môi trường: container (`/.dockerenv`, cgroup), 5 panel (cPanel, Plesk, aaPanel, CyberPanel, DirectAdmin), package manager (apt, dnf, yum, apk), systemd, Docker daemon, quyền root | Giữ nguyên, mở rộng ánh xạ site → runtime | FEAT-001, FEAT-004 |
| 4 | Dò nhiều binary PHP song song (`/usr/bin/php*`, `ea-php`, `alt-php`, `remi`, `plesk`, aaPanel, `lsphp`) và Node.js (hệ thống, `/opt`, aaPanel, nvm) | Giữ nguyên | FEAT-002 |
| 5 | Nhận diện bản vá backport của distro qua changelog gói (`changelog.Debian.gz`, `rpm --changelog`) | Giữ nguyên, danh sách CVE lấy từ dữ liệu online thay vì mảng `PHP_CVES` | FEAT-035 |
| 6 | Vá cùng nhánh PHP qua apt/dnf/yum/apk; Node.js qua gói hoặc tarball kèm kiểm tra `SHASUMS256.txt` | Giữ nguyên | FEAT-060, FEAT-062 |
| 7 | Mitigation tạm thời bằng file `zz-php-quickpatch-mitigation.ini` khi chưa vá được, tự gỡ khi đã vá | Giữ cơ chế; nội dung mitigation lấy từ bộ luật theo CVE trong gói dữ liệu | FEAT-061 |
| 8 | Composer/npm: tra OSV `querybatch` (lô 500 package), phát hiện mã độc `MAL-*`, `composer update --with-all-dependencies`, `npm audit fix` (không `--force`), chạy dưới quyền chủ thư mục | Giữ nguyên, thêm cache | FEAT-015, FEAT-063 |
| 9 | WordPress: cập nhật core bản minor, plugin bản patch, `verify-checksums` | Giữ nguyên, mốc phiên bản lấy từ dữ liệu online thay vì `WP_FIXED` | FEAT-064 |
| 10 | Docker: nâng tag `php:`/`node:` trong Dockerfile/compose, mitigation trong container đang chạy | Giữ nguyên | FEAT-065 |
| 11 | Phát hiện dấu hiệu webshell: **chỉ báo cáo, không xóa** | Giữ nguyên | FEAT-005 |
| 12 | Restart PHP-FPM/web server/LiteSpeed/cPanel `restartsrv`, unit systemd và pm2 của Node.js | Giữ nguyên | FEAT-066 |
| 13 | Backup theo lượt chạy tại `STATE_DIR/backups/<YYYYmmdd-HHMMSS>/manifest`, các hành động `copy`, `created`, `untar`, `composer-install`, `npm-ci`, `note`; rollback chạy manifest theo thứ tự ngược | Giữ định dạng, bổ sung hành động cho nâng cấp khác major | FEAT-067, FEAT-074 |
| 14 | `STATE_DIR` = `/var/lib/php-quickpatch` (root) hoặc `~/.php-quickpatch` (non-root); khóa `flock` trên `STATE_DIR/.lock` để chỉ 1 lượt chạy tại một thời điểm | Giữ nguyên, console dùng chung khóa | FEAT-090 |

### 1.3 Vấn đề cần giải quyết (Problem Statement)
| Mã | Vấn đề (đo được) | Bằng chứng |
| :--- | :--- | :--- |
| `PB-01` | Dữ liệu advisory ghi cứng trong 4 mảng (`PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED`). Mỗi đợt bản vá mới cần sửa mã và phát hành lại script. | `php-quickpatch.sh` dòng 13–18 |
| `PB-02` | Mốc ghi cứng lỗi thời sau vài tuần. Ví dụ: `WP_FIXED` = 6.9.5 / 7.0.2, nhưng ngày 2026-10-22 API `stable-check` của wordpress.org đánh dấu cả hai là `insecure`; bản mới nhất của nhánh là 6.9.10 và 7.0.7, bản `latest` là 7.1.3. | Gọi `api.wordpress.org/core/stable-check/1.0/` ngày 2026-10-22 |
| `PB-03` | v0.1 chỉ trả nhãn `eol` cho nhánh không có trong mảng (ví dụ PHP 5.6, 7.4, 8.1) và không đưa ra lộ trình nâng cấp, không quét tương thích mã. | Hàm `php_state`, `check_php` |
| `PB-04` | Nhánh có trong dữ liệu nhưng mới hơn mảng bị gắn `unknown` và bỏ qua kiểm tra. | Hàm `php_state`, `node_state` |
| `PB-05` | Không có đầu ra máy đọc được (JSON), không có giao diện để so sánh phiên bản và theo dõi job. | `usage()` v0.1 |
| `PB-06` | PHP 8.2 hết hạn hỗ trợ ngày 2026-12-31 (còn 70 ngày tính từ 2026-10-22); PHP 8.4 kết thúc giai đoạn active support cùng ngày. Người vận hành cần kế hoạch nâng cấp trước mốc này. | endoflife.date `/api/php.json` |

### 1.4 Mục tiêu kinh doanh (Business Goals — OKRs / KPIs)
Quy ước đo: mọi mốc thời gian lấy từ audit log (FEAT-092) và bảng dữ liệu nguồn (FEAT-016) của chính tool, múi giờ UTC. "Server dùng v2" = server đã chạy `scan` của v2 ít nhất 1 lần.

- **Mục tiêu 1 (O1) — Rút ngắn thời gian từ lúc có bản vá đến lúc server được vá**
  - **KR1.1**: Tuổi dữ liệu advisory trong cache khi server có mạng ≤ 6 giờ 15 phút tại 99% thời điểm đo (chu kỳ đồng bộ mặc định 6 giờ + tối đa 15 phút xử lý).
  - **KR1.2**: Thời gian trung vị từ lúc finding được ghi nhận (`detected_at`) đến lúc job vá cùng nhánh thành công (`fixed_at`) ≤ 24 giờ với finding thuộc KEV hoặc CVSS ≥ 9.0; ≤ 7 ngày với CVSS 7.0–8.9. Baseline v0.1: chưa đo được (phụ thuộc người bảo trì sửa mảng dữ liệu và phát hành lại script). Chỉ tiêu này phụ thuộc quyết định Q-07.
  - **KR1.3**: Vá cùng nhánh 1 runtime trên dashboard cần ≤ 3 thao tác: chọn finding → xem kết quả `--dry-run` → xác nhận chạy.
- **Mục tiêu 2 (O2) — Giảm tỉ lệ runtime EOL còn đang phục vụ site**
  - **KR2.1**: Tỉ lệ runtime PHP/Node.js EOL trên tổng runtime đang phục vụ site giảm ≥ 50% sau 90 ngày kể từ lần `scan` đầu tiên trên mỗi server dùng v2.
  - **KR2.2**: 100% runtime PHP 8.2 phát hiện được có kế hoạch nâng cấp ở trạng thái "Đã duyệt" trước 2026-12-01 (30 ngày trước EOL 2026-12-31).
  - **KR2.3**: 100% runtime có ngày EOL trong vòng ≤ 90 ngày hiển thị cảnh báo trên màn hình Tổng quan và trong `scan --json`.
- **Mục tiêu 3 (O3) — Giảm công sức lập kế hoạch nâng cấp**
  - **KR3.1**: Từ màn hình Tổng quan đến checklist kế hoạch nâng cấp hoàn chỉnh cần ≤ 4 thao tác: chọn runtime → chọn phiên bản đích → bấm "Sinh kế hoạch" → mở checklist; không phải gõ lệnh.
  - **KR3.2**: Thời gian sinh kế hoạch (gồm quét tương thích) ≤ 120 giây cho 1 site có ≤ 10.000 file `.php` và ≤ 300 package trong `composer.lock`, trên máy 2 vCPU / 2 GB RAM (mục tiêu đề xuất, SRS xác nhận bằng benchmark).
  - **KR3.3**: 100% bước trong checklist có: mã kịch bản, lệnh hoặc thao tác cụ thể, điều kiện hoàn thành kiểm tra được; 0 bước chỉ có mô tả định tính.
- **Mục tiêu 4 (O4) — Mọi thay đổi đều hoàn tác được**
  - **KR4.1**: 100% job thay đổi hệ thống (`fix`, `upgrade`, `switch`) ghi manifest backup và bản ghi audit trước khi sửa file đầu tiên.
  - **KR4.2**: Rollback 1 site về runtime cũ hoàn tất ≤ 60 giây (không tính thời gian health check), bằng 1 lệnh CLI hoặc 1 nút + 1 xác nhận trên dashboard.
  - **KR4.3**: Tỉ lệ site bị tự rollback do health check thất bại ≤ 10% trên tổng site đã đạt quét tương thích (đo trong 90 ngày); chỉ số này đo độ chính xác của quét tương thích.
- **Mục tiêu 5 (O5) — Dữ liệu đầy đủ và chịu lỗi nguồn**
  - **KR5.1**: 100% nhánh PHP 4.4 và 5.0–8.5, Node.js 4–26 có bản ghi vòng đời trong snapshot offline đóng gói kèm bản phát hành.
  - **KR5.2**: Snapshot offline có tuổi ≤ 7 ngày tại ngày phát hành bản tool; tool cảnh báo khi dữ liệu dùng để đánh giá cũ hơn 7 ngày.
  - **KR5.3**: Khi 1 hoặc nhiều nguồn online lỗi, 100% lượt `scan` vẫn hoàn tất bằng dữ liệu cache/snapshot và ghi tên nguồn lỗi kèm thời điểm dữ liệu cuối cùng.

---

## 2. Đối tượng mục tiêu & Chân dung người dùng (Target Audience & Personas)

### 2.1 Bảng Persona và Actor (Rule 17)
| Persona ID | Loại Actor | Vai trò / Nhóm người dùng | Mục tiêu chính | Nỗi đau hiện tại (Pain points) | Hành vi công nghệ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PER-01` | Primary | Người vận hành VPS tự quản | Vá CVE KEV/Critical trong ≤ 24 giờ; biết runtime nào EOL; nâng cấp major mà không chuyển đồng loạt mọi site | Phải chờ bản script mới khi có CVE; PHP 7.4/8.1 bị gắn `eol` nhưng không có lộ trình; không biết thư viện nào lỗi khi lên PHP 8.x | Quản lý 1–20 VPS Linux (Debian/Ubuntu, RHEL-family, Alpine), có root qua SSH, nginx/Apache + PHP-FPM, Node.js chạy bằng systemd/pm2; 100% thao tác qua terminal SSH |
| `PER-02` | Primary | Quản trị hosting có panel | Biết site nào đang dùng runtime nào; chuyển từng site sang PHP mới theo cơ chế của panel; giữ bản cũ cho site chưa tương thích | Trình chọn PHP của panel không cho biết CVE/KEV, không quét tương thích mã; nâng cấp hàng loạt làm lỗi site khách dùng mã cũ | cPanel (EA-PHP), Plesk, aaPanel, CyberPanel (lsphp), DirectAdmin; 20–500 site/server; dùng cả UI panel và SSH |
| `PER-03` | Primary | DevOps quản lý Docker | Pin image `php:`/`node:` đã vá; biết base image EOL; có kế hoạch đổi major của base image; đưa kết quả quét vào CI | Container vẫn chạy bản cũ sau khi Dockerfile đã sửa; image pin cũ không ai rà; v0.1 không có JSON cho CI | Dockerfile/compose trong repo, Docker daemon trên host, pipeline CI đọc JSON và mã thoát |
| `PER-04` | Primary (chỉ đọc, xuất báo cáo) | Kỹ sư bảo mật / kiểm toán viên | Có bằng chứng: CVE/KEV theo runtime, trạng thái EOL/LTS, lịch sử thay đổi và rollback, nguồn dữ liệu và thời điểm lấy | Không có báo cáo chuẩn hóa; không truy vết được ai đã chạy gì, lúc nào | Phase 1: trực tiếp dùng console (token phiên `serve` do người vận hành cấp) hoặc CLI để xem đánh giá, tra cứu và kiểm toàn vẹn audit, xuất báo cáo (JSON/CSV/Markdown/HTML); 0 thao tác thay đổi trên server. Khi không có quyền shell/console thì nhận báo cáo do `PER-01`/`PER-02` xuất thay (vai trò Secondary). Phase 2: vai trò Viewer |
| `SYS-01` | System | Bộ lập lịch (cron hoặc systemd timer) | Chạy `sync` theo chu kỳ để cache không quá hạn; tùy chọn chạy `scan --json` định kỳ | — | Do tool cài/gỡ bằng lệnh; chạy với quyền của người cài |
| `SYS-02` | System | Nguồn dữ liệu online | Cung cấp dữ liệu vòng đời, bản phát hành, CVE, KEV, advisory thư viện | Giới hạn tốc độ (NVD, GitHub API), độ trễ cập nhật khác nhau giữa các nguồn | Xem danh sách tại mục 2.2 |
| `SYS-03` | System | Hạ tầng đích trên server (package manager, panel, Docker daemon, systemd/pm2, web server) | Thực thi lệnh cài, chuyển, restart do tool gọi | Mỗi panel/distro có cơ chế riêng | apt/dnf/yum/apk, CLI panel, `docker`, `systemctl`, `pm2` |
| `SYS-04` | System (Phase 2) | Kết nối SSH tới server được quản lý | Phase 2: dashboard trung tâm chạy CLI từ xa, thu JSON | Server không ra Internet; khóa SSH khác nhau | OpenSSH client trên máy trung tâm, không cài agent |

> **Phân loại `PER-04` (rule 17)**: `PER-04` là Primary Actor duy nhất của `UC-JOB-003`, `UC-RPT-001`, `UC-RPT-002` và đồng Primary của `UC-FEED-003`, `UC-ASMT-001`, `UC-CON-002`, `UC-JOB-001` (`usecases/index.md` §3). Phase 1 chưa có vai trò kỹ thuật chặn thao tác ghi của người giữ token `serve`; "chỉ đọc" là quy ước vận hành (`usecases/index.md` §7.2 mục 1). Tài liệu hạ nguồn cần đồng bộ phân loại này: `srs/spec.md` §2.3, `usecases/index.md` §2.1, `userstories/backlog.md` §1.4.

### 2.2 Nguồn dữ liệu online (`SYS-02`) — kiểm chứng ngày 2026-10-22
| Nguồn | Endpoint | Dùng cho | Kết quả kiểm chứng |
| :--- | :--- | :--- | :--- |
| endoflife.date | `https://endoflife.date/api/php.json`, `/api/nodejs.json` | Vòng đời: `cycle`, `support`, `eol`, `lts`, `latest` | HTTP 200; 18 nhánh PHP (5.0–8.5), 26 dòng Node.js (1–26). Trường `latest` của PHP là 8.5.11 (2026-09-24), **chậm hơn** php.net (8.5.12 ngày 2026-10-21) → không dùng `latest` của endoflife.date làm mốc bản vá |
| endoflife.date (framework/CMS) | `/api/laravel.json`, `/api/wordpress.json`, `/api/magento.json`, `/api/symfony.json`, `/api/drupal.json` | Ma trận framework/CMS ↔ PHP | HTTP 200; có `supportedPhpVersions` (laravel, magento) và `supportedPHPVersions` (wordpress, khác chữ hoa); symfony, drupal không có trường này |
| php.net releases | `https://www.php.net/releases/index.php?json&version=8.4` (và `&max=N`) | Bản phát hành mới nhất mỗi nhánh, nhãn `security`, `supported_versions` | HTTP 200; 8.4.27 ngày 21 Oct 2026, `tags: ["security"]`, `supported_versions: 8.2, 8.3, 8.4, 8.5` |
| NVD API 2.0 | `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=…` (lọc theo CPE `cpe:2.3:a:php:php`) | CVE PHP core, CVSS, CWE, khoảng phiên bản bị ảnh hưởng | HTTP 200; CVE-2026-109618: CVSS v3.1 9.8, v4.0 9.2, CWE-416; khoảng ảnh hưởng `< 8.2.35`, `< 8.3.36`, `< 8.4.27`, `< 8.5.12` (trùng `PHP_FIXED` của v0.1) |
| GitHub Security Advisories (php-src) | `https://github.com/php/php-src/security/advisories` | Advisory php-src (GHSA) | Trang web truy cập được: GHSA-w8hw-w9fx-j79w, GHSA-6wmf-4rv5-p3rp (Critical, 2026-10-21). REST API `api.github.com/repos/php/php-src/security-advisories`: **chưa kiểm chứng** (proxy của phiên làm việc chặn, không phải lỗi của API) |
| CISA KEV | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | Gắn cờ CVE đang bị khai thác | HTTP 200, 1.803.428 byte, `catalogVersion` 2026.10.21, 1.754 bản ghi. CVE-2026-63030 và CVE-2026-60137 (wp2shell) **có** trong KEV; CVE-2026-109618/109619 (PHP2Shell) **chưa có** |
| nodejs.org | `https://nodejs.org/dist/index.json` | Bản phát hành Node.js, cờ `security`, `lts` | Truy cập được; v26.12.1 (2026-10-21) `security: true` |
| Node.js Security WG | `https://raw.githubusercontent.com/nodejs/security-wg/main/vuln/core/index.json` | CVE Node.js core kèm khoảng `vulnerable` / `patched` (semver) | HTTP 200, 194 bản ghi |
| OSV | `https://api.osv.dev/v1/querybatch` | Advisory Packagist, npm (gồm `MAL-*`) | HTTP 200. OSV **không** có CVE-2026-109618 (HTTP 404 "Vulnerability not found") → không dùng OSV cho PHP core |
| Packagist | `https://repo.packagist.org/p2/{vendor}/{package}.json` | Phiên bản ứng viên và ràng buộc `require.php` của package | HTTP 200 |
| npm registry | `https://registry.npmjs.org/{package}` | Phiên bản ứng viên và `engines.node` | HTTP 200 |
| wordpress.org | `https://api.wordpress.org/core/stable-check/1.0/`, `/core/version-check/1.7/` | Trạng thái `latest` / `outdated` / `insecure` của từng bản WordPress core | HTTP 200; 934 `insecure`, 24 `outdated`, 1 `latest` (7.1.3) |

### 2.3 Ma trận phân quyền (RBAC Matrix)
Phase 1 không có tài khoản người dùng. Quyền được xác định bởi (a) có token của phiên `serve` hay không và (b) tiến trình CLI/console chạy với root hay không (kế thừa v0.1). Cột Phase 2 là đề xuất thiết kế, SRS Phase 2 chốt.

| Chức năng / Tài nguyên | Không token | Token console (Phase 1) | CLI root | CLI non-root | P2 Viewer | P2 Operator | P2 Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Xem tổng quan, đánh giá, findings | - | View | View | View | View | View | Full |
| Đồng bộ dữ liệu (`sync`) | - | Execute | Execute | Execute (cache riêng của user) | - | Execute | Full |
| Sinh kế hoạch / checklist | - | Create | Create | Create | View | Create | Full |
| Vá runtime cùng nhánh (PHP/Node hệ thống) | - | Execute (nếu `serve` chạy bằng root) | Execute | - | - | Execute | Full |
| Vá project-level (Composer, npm, WordPress) | - | Execute | Execute | Execute (thư mục user sở hữu) | - | Execute | Full |
| Cài runtime song song, chuyển site | - | Execute (nếu root) | Execute | - | - | Execute | Full |
| Rollback | - | Execute | Execute | Execute (chỉ thay đổi do user tạo) | - | Execute | Full |
| Xem log job, audit | - | View | View | View (của user) | View | View | Full |
| Xuất báo cáo | - | Export | Export | Export | Export | Export | Full |
| Quản lý danh sách server, khóa SSH (Phase 2) | - | - | - | - | - | - | Full |

---

## 3. Phạm vi sản phẩm (Product Scope)

### 3.1 Nằm trong phạm vi (In-Scope) — khớp mục 5.1 của `DOC-BRS-QP-001`
1. **Tự động lấy dữ liệu CVE / vòng đời từ nguồn online**, có cache, có chế độ offline dùng snapshot đóng gói kèm tool; thay thế toàn bộ mảng ghi cứng `PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED`. → FEAT-010 đến FEAT-019
2. **Danh mục kịch bản theo phiên bản đang chạy** (PHP 4.x, 5.x, "6" bất thường, 7.x, 8.0–8.5, pre-release; Node.js EOL, LTS, Current), mỗi kịch bản có checklist công việc chi tiết. → FEAT-020 đến FEAT-023
3. **Đánh giá bảo mật so sánh** giữa phiên bản hiện tại và các phiên bản nâng cấp ứng viên: số CVE theo mức độ, CVE trong KEV, trạng thái hỗ trợ (active / security-only / EOL), LTS (Node.js), ngày EOL. → FEAT-030 đến FEAT-035
4. **Lựa chọn phiên bản nâng cấp** trên dashboard và CLI; sinh kế hoạch gồm các bước, thư viện/dependency phải nâng (Composer, npm, extension PHP, framework/CMS), kết quả quét tương thích mã nguồn. → FEAT-040 đến FEAT-043, FEAT-050 đến FEAT-054
5. **Vá cùng nhánh tự động** như v0.1 và **nâng cấp khác major** theo mô hình cài song song → chuyển từng site → health check → rollback 1 lệnh. → FEAT-060 đến FEAT-067, FEAT-070 đến FEAT-077
6. **Web console Phase 1** chạy cục bộ bằng lệnh `serve`, backend Python 3 stdlib, xác thực token, chỉ lắng nghe `127.0.0.1`, truy cập qua SSH tunnel; 6 màn hình: Tổng quan, Đánh giá runtime, Chọn phiên bản & Kế hoạch/Checklist, Jobs & Log, Findings thư viện, Rollback. → FEAT-080 đến FEAT-087, FEAT-090 đến FEAT-092
7. **CLI Bash xuất JSON** (`--json`) cho console và hệ thống khác (CI). → FEAT-100 đến FEAT-102
8. **Báo cáo và xuất dữ liệu** cho kiểm toán. → FEAT-110, FEAT-111
9. **Thiết kế (chưa triển khai) Phase 2**: dashboard trung tâm quản lý nhiều server qua SSH, không agent. → FEAT-120 đến FEAT-123
10. **Kế thừa toàn bộ hành vi v0.1.0** liệt kê ở mục 1.2. → FEAT-001 đến FEAT-005, FEAT-060 đến FEAT-067

### 3.2 Nằm ngoài phạm vi (Out-of-Scope)
| STT | Hạng mục | Lý do / Ghi chú |
| :--- | :--- | :--- |
| 1 | Cài agent thường trú trên server được quản lý | Quyết định PO (`DOC-BRS-QP-001` mục 5.2); Phase 2 chỉ dùng SSH |
| 2 | Tự động sửa mã nguồn ứng dụng của khách hàng | Chỉ quét và báo cáo tương thích. Refactor tự động (ví dụ Rector) chỉ có thể là bước tùy chọn có duyệt diff — chờ SRS đề xuất, PO duyệt (Q-02) |
| 3 | Tự xóa file nghi webshell | Giữ hành vi v0.1: chỉ báo cáo |
| 4 | Mở dashboard ra mạng ngoài; quản lý tài khoản/mật khẩu | Phase 1 chỉ token + `127.0.0.1`; RBAC tài khoản thuộc thiết kế Phase 2 |
| 5 | Hỗ trợ Windows Server | Quyết định PO |
| 6 | Triển khai mã nguồn Phase 2 | Phase 2 chỉ thiết kế trong đợt này |
| 7 | Audit `yarn.lock`, `pnpm-lock.yaml` | Giữ hành vi v0.1: chỉ cảnh báo và hướng dẫn chạy `yarn npm audit` / `pnpm audit` (Q-06) |
| 8 | Tự build và deploy lại image Docker | Giữ hành vi v0.1: tool sửa tag trong Dockerfile/compose và báo cần rebuild; không chạy pipeline build/deploy |
| 9 | Nâng cấp hệ điều hành / web server (nginx, Apache) khác major | Không thuộc yêu cầu; checklist chỉ ghi điều kiện tiên quyết nếu runtime đích yêu cầu |

### 3.3 Danh mục kịch bản phiên bản (tóm tắt, dữ liệu tại 2026-10-22)
Phân loại trạng thái được **tính động** từ dữ liệu vòng đời (FEAT-010) tại thời điểm chạy, không ghi cứng. Bảng dưới là ảnh chụp ngày 2026-10-22 để minh họa và làm dữ liệu kiểm thử. Mã kịch bản dùng đúng mã của SRS: `SCN-PHP-001..016` (`srs/version-scenarios-php.md`, `srs/version-scenarios-php-8x.md`) và `SCN-NODE-001..012` (`srs/version-scenarios-node.md`); 1 dòng của bảng có thể gộp nhiều kịch bản SRS.

| Mã kịch bản | Nhánh | Trạng thái (nguồn) | Hành động mặc định của tool | Điểm chú ý chính trong checklist |
| :--- | :--- | :--- | :--- | :--- |
| `SCN-PHP-001` | PHP 4.x | EOL 2008-08-07, bản cuối 4.4.9 (php.net/eol.php; endoflife.date không có nhánh 4.x → bổ sung bản ghi tĩnh) | Không vá được; đánh giá + kế hoạch nâng cấp khác major; quét tương thích bắt buộc | Khoảng cách 4 major; bắt buộc cài song song, không nâng tại chỗ |
| `SCN-PHP-002` (5.0–5.2), `SCN-PHP-003` (5.3–5.5), `SCN-PHP-004` (5.6) | PHP 5.0–5.6 | EOL: 5.0 ngày 2005-09-05, 5.2 ngày 2011-01-06, 5.6 ngày 2018-12-31 | Như trên | Extension `mysql`, `ereg`, `mssql`, `sybase_ct` bị gỡ khỏi PHP 7.0 → thay bằng `mysqli`/`PDO`, `preg_*` |
| `SCN-PHP-005` | "PHP 6" và chuỗi phiên bản bất thường (gồm nhánh mới hơn dữ liệu nhưng không có trong nguồn pre-release) | PHP 6 chưa từng phát hành; RFC đặt tên chọn "PHP 7" (58 phiếu PHP 7, 24 phiếu PHP 6) | Báo lỗi nhận diện, **không** đề xuất nâng cấp tự động | Xác minh binary, banner `php -v`, gói sở hữu binary |
| `SCN-PHP-006` (7.0–7.2), `SCN-PHP-007` (7.3–7.4) | PHP 7.0–7.4 | EOL: 7.0 ngày 2019-01-10 … 7.4 ngày 2022-11-28 | Đánh giá + kế hoạch nâng cấp khác major | PHP 8.0 gỡ `each()`, `create_function()`, `array_key_exists()` trên object, directive `mbstring.func_overload` |
| `SCN-PHP-008` (8.0), `SCN-PHP-009` (8.1) | PHP 8.0–8.1 | EOL: 8.0 ngày 2023-11-26, 8.1 ngày 2025-12-31 | Đánh giá + kế hoạch nâng cấp cùng major 8 | Kiểm tra `require.php` của Composer package với nhánh đích |
| `SCN-PHP-010` | PHP 8.2 | Chỉ vá bảo mật; EOL 2026-12-31 (còn 70 ngày) | Vá cùng nhánh tự động (ví dụ 8.2.35 cho PHP2Shell) + bắt buộc có kế hoạch nâng cấp (KR2.2) | Cảnh báo EOL ≤ 90 ngày |
| `SCN-PHP-011` | PHP 8.3 | Chỉ vá bảo mật (active kết thúc 2025-12-31); EOL 2027-12-31 | Vá cùng nhánh tự động | — |
| `SCN-PHP-012` | PHP 8.4 | Active support đến 2026-12-31; EOL 2028-12-31 | Vá cùng nhánh tự động | Chuyển sang "chỉ vá bảo mật" từ 2027-01-01 |
| `SCN-PHP-013` | PHP 8.5 | Active support đến 2027-12-31; EOL 2029-12-31 | Vá cùng nhánh tự động | — |
| `SCN-PHP-014` | Pre-release (alpha/beta/RC, hậu tố `-dev`) có trong nguồn pre-release của php.net | Không có trong `supported_versions` của php.net; trạng thái `PRE_RELEASE` | Không vá tự động; nhánh mới hơn dữ liệu mà không có trong nguồn pre-release chuyển sang `SCN-PHP-005` (`UNKNOWN`, như nhãn `unknown` của v0.1) | Cảnh báo không dùng cho production |
| `SCN-NODE-001` (≤ 16), `SCN-NODE-002` (18), `SCN-NODE-003` (20), `SCN-NODE-004` (dòng lẻ 17–25) | Node.js ≤ 20 và mọi dòng số lẻ | 20 EOL 2026-04-30; 25 EOL 2026-06-01 | Đánh giá + kế hoạch nâng cấp lên dòng LTS còn hỗ trợ | Native addon cần build lại; kiểm tra `engines.node` |
| `SCN-NODE-005` | Node.js 22 | Maintenance LTS; EOL 2027-04-30 (còn 190 ngày) | Vá cùng major tự động | — |
| `SCN-NODE-006` | Node.js 24 | LTS; active support kết thúc 2026-10-20 → Maintenance LTS; EOL 2028-04-30 | Vá cùng major tự động | — |
| `SCN-NODE-007` | Node.js 26 | Current; vào LTS ngày 2026-10-28 (sau 6 ngày); EOL 2029-04-30 | Vá cùng major tự động | — |
| `SCN-NODE-008` | Pre-release (`-nightly`, `-rc.N`, `-pre`, bản alpha) và chuỗi phiên bản bất thường | `PRE_RELEASE` / `UNKNOWN` | Không vá, không đề xuất nâng cấp tự động | Production hạ về dòng LTS còn hỗ trợ |

> **Ghi chú đối chiếu biên bản**: `DOC-BRS-QP-001` ghi "24 (active LTS)". Dữ liệu endoflife.date ngày 2026-10-22 cho thấy Node.js 24 đã chuyển sang Maintenance LTS từ 2026-10-20 và Node.js 26 vào Active LTS từ 2026-10-28. Đây là minh chứng cho yêu cầu phân loại động (FEAT-021), không phải thay đổi phạm vi.

**Kịch bản môi trường (kết hợp với kịch bản phiên bản để sinh checklist)**: `SCN-ENV-PKG` (runtime do package manager quản lý), `SCN-ENV-SRC` (build từ mã nguồn hoặc build của panel, không có gói sở hữu), `SCN-ENV-PANEL` (panel quản lý phiên bản PHP theo site), `SCN-ENV-DOCKER` (image/container), `SCN-ENV-NVM` (Node.js cài bằng nvm), `SCN-ENV-NOROOT` (không có root, chế độ shared hosting). SRS hiện thực các mã này bằng kịch bản `OVERLAY` và playbook môi trường (`FR-SCN-ENV-001`): `SCN-ENV-PKG` → `SCN-PHP-015`, `SCN-NODE-011`, `SCN-NODE-012`, `PB-001`..`PB-004`, `PB-014`; `SCN-ENV-SRC` → `SCN-PHP-016`, `SCN-NODE-010`, `PB-015`; `SCN-ENV-PANEL` → `PB-007`..`PB-012`; `SCN-ENV-DOCKER` → `PB-013`; `SCN-ENV-NVM` → `SCN-NODE-009`, `PB-016`; `SCN-ENV-NOROOT` → giới hạn `BR-PTCH-003` (chỉ thao tác cấp dự án).

---

## 4. Bóc tách danh mục tính năng (Feature Breakdown)

### 4.1 Quy ước
- **Mức độ ưu tiên** xét trong phạm vi phase của tính năng: **P0 (Must)** = bắt buộc để phát hành phase đó; **P1 (Should)** = nên có trong bản phát hành của phase, được phép lùi tối đa 1 bản minor; **P2 (Nice to have)** = có thể lùi sang đợt sau.
- **Phase 1** = cục bộ trên chính server được quản lý (triển khai trước). **Phase 2** = dashboard trung tâm nhiều server qua SSH (chỉ thiết kế trong đợt này).
- **Mã FR (SRS)** theo Rule 01 `FR-[MODULE]-[FEATURE]-[SEQ]`, lấy từ ma trận truy vết FEAT → FR của `srs/spec.md` §4.2 (`DOC-SRS-QP-001`); mỗi FEAT có ≥ 1 FR. Chi tiết từng FR: `srs/functional-requirements.md`.
- **Tổng số**: 70 tính năng. Phase 1: 66 (P0: 58, P1: 7, P2: 1). Phase 2 (chỉ thiết kế): 4 (P0: 3, P1: 1).

| Mã MODULE | Phân hệ |
| :--- | :--- |
| `SCAN` | Nhận diện môi trường & kiểm kê |
| `FEED` | Đồng bộ dữ liệu CVE / vòng đời |
| `SCN` | Danh mục kịch bản phiên bản |
| `ASMT` | Đánh giá bảo mật |
| `PLAN` | Chọn phiên bản đích & kế hoạch |
| `CMPT` | Quét tương thích |
| `PTCH` | Vá cùng nhánh (kế thừa v0.1) |
| `UPG` | Nâng cấp khác major |
| `CON` | Web console |
| `JOB` | Job runner, log, audit |
| `CLI` | Giao diện dòng lệnh |
| `RPT` | Báo cáo & xuất dữ liệu |
| `FLT` | Quản lý nhiều server (Phase 2) |

### 4.2 Nhận diện môi trường & kiểm kê (`SCAN`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-001` | SCAN | Nhận diện môi trường | P0 (Must) | 1 | PER-01, PER-02, PER-03 | Kế thừa v0.1: container, 5 panel, package manager, systemd, Docker daemon, quyền root, hệ điều hành; xuất kết quả trong `--json` | `FR-SCAN-ENV-001` |
| `FEAT-002` | SCAN | Phát hiện runtime PHP và Node.js | P0 (Must) | 1 | PER-01, PER-02, PER-03 | Kế thừa danh sách đường dẫn dò của v0.1; ghi phiên bản, đường dẫn, gói sở hữu, SAPI (FPM, `mod_php`), nguồn cài (gói / build / panel / nvm) | `FR-SCAN-RT-001`, `FR-SCAN-RT-002` |
| `FEAT-003` | SCAN | Kiểm kê dự án | P0 (Must) | 1 | PER-01, PER-02, PER-03 | Kế thừa v0.1: `composer.lock`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, WordPress (`wp-includes/version.php`), Dockerfile/compose, container đang chạy; độ sâu tìm kiếm 7 cấp như v0.1 | `FR-SCAN-PRJ-001`, `FR-SCAN-PRJ-002` |
| `FEAT-004` | SCAN | Ánh xạ site → runtime đang phục vụ | P0 (Must) | 1 | PER-01, PER-02 | Xác định mỗi site/vhost đang dùng FPM pool, handler hoặc thiết lập panel nào, trỏ tới binary PHP nào; là đầu vào bắt buộc của chuyển từng site (FEAT-072) | `FR-SCAN-MAP-001`, `FR-SCAN-DRF-001`, `FR-CON-SITE-001` |
| `FEAT-005` | SCAN | Phát hiện dấu hiệu webshell | P0 (Must) | 1 | PER-01, PER-02, PER-04 | Kế thừa v0.1: mẫu regex, file `.ph*` trong `wp-content/uploads`, tối đa 50 kết quả mỗi nhóm; chỉ báo cáo, không xóa | `FR-SCAN-WSH-001` |

### 4.3 Đồng bộ dữ liệu CVE / vòng đời (`FEED`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-010` | FEED | Đồng bộ dữ liệu vòng đời | P0 (Must) | 1 | PER-01..04, SYS-02 | Lấy `support`, `eol`, `lts`, `releaseDate` từ endoflife.date cho PHP, Node.js; bổ sung bản ghi tĩnh cho nhánh nguồn không có: PHP 4.4 (EOL 2008-08-07) và Node.js 0.x (endoflife.date chỉ có dòng 1–26) | `FR-FEED-EOL-001`, `FR-FEED-EOL-002`, `FR-FEED-EOL-003` |
| `FEAT-011` | FEED | Đồng bộ bản phát hành & mốc bản vá | P0 (Must) | 1 | PER-01..03, SYS-02 | php.net releases JSON (bản mới nhất mỗi nhánh, nhãn `security`, `supported_versions`); nodejs.org `index.json` (`security`, `lts`); wordpress.org `stable-check`. Thay thế `PHP_FIXED`, `NODE_FIXED`, `WP_FIXED` | `FR-FEED-REL-001`, `FR-FEED-REL-002`, `FR-FEED-REL-003`, `FR-FEED-NORM-002`, `FR-CLI-COMP-002` |
| `FEAT-012` | FEED | Đồng bộ CVE PHP core | P0 (Must) | 1 | PER-01, PER-02, PER-04, SYS-02 | NVD API 2.0 (CPE `cpe:2.3:a:php:php`, khoảng phiên bản bị ảnh hưởng, CVSS v3.1/v4.0, CWE) + GitHub Security Advisories của php-src; đồng bộ tăng dần theo `lastModified`; không dùng OSV cho PHP core | `FR-FEED-PCVE-001`, `FR-FEED-PCVE-002`, `FR-FEED-PCVE-003` |
| `FEAT-013` | FEED | Đồng bộ CVE Node.js core | P0 (Must) | 1 | PER-01, PER-03, SYS-02 | Node.js Security WG `vuln/core/index.json` (khoảng `vulnerable`/`patched` semver) + NVD | `FR-FEED-NCVE-001` |
| `FEAT-014` | FEED | Đồng bộ CISA KEV | P0 (Must) | 1 | PER-01..04, SYS-02 | Tải KEV JSON (≈ 1,8 MB), gắn cờ KEV cho mọi CVE khớp; lưu `dateAdded`, `dueDate`, `knownRansomwareCampaignUse` | `FR-FEED-KEV-001` |
| `FEAT-015` | FEED | Tra cứu OSV cho thư viện | P0 (Must) | 1 | PER-01..03 | Kế thừa `querybatch` lô 500 của v0.1 cho Packagist, npm (gồm `MAL-*`); thêm cache kết quả theo cặp (package, version) | `FR-FEED-OSV-001` |
| `FEAT-016` | FEED | Cache cục bộ có TTL | P0 (Must) | 1 | PER-01..04 | Lưu dữ liệu chuẩn hóa vào SQLite tại `STATE_DIR`; mỗi bản ghi có `source`, `fetched_at`, `source_updated_at`; tự lấy lại khi quá TTL ở lần `scan`/`sync` kế tiếp; dùng `ETag`/`If-Modified-Since` khi nguồn hỗ trợ | `FR-FEED-SYNC-001`, `FR-FEED-AGE-001`, `FR-FEED-CACH-001`, `FR-FEED-CACH-002`, `FR-FEED-CACH-003`, `FR-CON-FEED-001` |
| `FEAT-017` | FEED | Snapshot offline | P0 (Must) | 1 | PER-01..03 | Snapshot dữ liệu đóng gói kèm mỗi bản phát hành tool (tuổi ≤ 7 ngày, KR5.2); `--offline` dùng cache rồi snapshot; lệnh xuất/nhập snapshot để chép sang server không ra Internet; cảnh báo khi dữ liệu > 7 ngày | `FR-FEED-SNAP-001`, `FR-FEED-SNAP-002`, `FR-FEED-SNAP-003`, `FR-FEED-SNAP-004`, `FR-FEED-CMD-003`, `FR-FEED-CMD-004`, `FR-FEED-CMD-005`, `FR-CON-FEED-002` |
| `FEAT-018` | FEED | Lịch đồng bộ tự động | P1 (Should) | 1 | SYS-01, PER-01, PER-02 | Lệnh cài/gỡ cron hoặc systemd timer chạy `sync` mỗi 6 giờ (mặc định, cấu hình được, Q-08); không cài trùng khi đã có lịch | `FR-FEED-SCHD-001`, `FR-FEED-CMD-006` |
| `FEAT-019` | FEED | Chuẩn hóa & khử trùng lặp advisory | P0 (Must) | 1 | PER-01..04 | Gộp CVE ↔ GHSA ↔ OSV alias; chọn điểm CVSS theo thứ tự ưu tiên nguồn (SRS chốt); ghi lỗi từng nguồn mà không làm hỏng lượt chạy (KR5.3); tuân thủ giới hạn tốc độ nguồn | `FR-FEED-NORM-001`, `FR-FEED-NORM-002` |

### 4.4 Danh mục kịch bản phiên bản (`SCN`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-020` | SCN | Kịch bản PHP theo nhánh | P0 (Must) | 1 | PER-01, PER-02, PER-03 | Phân loại 16 kịch bản `SCN-PHP-001..016` (14 `VERSION` + 2 `OVERLAY`, mục 3.3) theo dữ liệu vòng đời tại thời điểm chạy; "PHP 6" → lỗi nhận diện (`SCN-PHP-005`) | `FR-SCN-CLS-001`, `FR-SCN-LIFE-001`, `FR-SCN-LOCK-001` |
| `FEAT-021` | SCN | Kịch bản Node.js theo dòng | P0 (Must) | 1 | PER-01, PER-03 | Phân loại 12 kịch bản `SCN-NODE-001..012` (8 `VERSION` + 4 `OVERLAY`): EOL, Maintenance LTS, Active LTS, Current, dòng số lẻ, pre-release; tính động theo ngày chạy | `FR-SCN-CLS-002`, `FR-SCN-LIFE-001`, `FR-SCN-LOCK-001` |
| `FEAT-022` | SCN | Checklist công việc theo kịch bản | P0 (Must) | 1 | PER-01..03 | Mỗi kịch bản phiên bản × kịch bản môi trường có checklist: bước, lệnh/thao tác, điều kiện hoàn thành, có/không tự động hóa được; định nghĩa checklist là dữ liệu trong gói snapshot, cập nhật không cần sửa script | `FR-SCN-CAT-001`, `FR-SCN-CHK-001` |
| `FEAT-023` | SCN | Kịch bản môi trường đặc biệt | P0 (Must) | 1 | PER-01..03 | `SCN-ENV-SRC`, `SCN-ENV-PANEL`, `SCN-ENV-DOCKER`, `SCN-ENV-NVM`, `SCN-ENV-NOROOT`: kế thừa cách xử lý của v0.1 (hướng dẫn thủ công, mitigation, chỉ project-level) | `FR-SCN-ENV-001` |

### 4.5 Đánh giá bảo mật (`ASMT`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-030` | ASMT | Đánh giá runtime hiện tại | P0 (Must) | 1 | PER-01..04 | Mỗi runtime: số CVE chưa vá theo mức Critical/High/Medium/Low, số CVE trong KEV, trạng thái active / security-only / EOL, LTS (Node.js), ngày EOL, số ngày còn lại, bản vá cùng nhánh mới nhất | `FR-ASMT-CUR-001`, `FR-ASMT-RISK-001` |
| `FEAT-031` | ASMT | Liệt kê phiên bản ứng viên | P0 (Must) | 1 | PER-01..03 | Ứng viên = bản vá cùng nhánh mới nhất + mọi nhánh còn hỗ trợ cao hơn; đánh dấu ứng viên nào cài được từ nguồn hiện có trên server (kho distro, panel, tag Docker) | `FR-ASMT-CAND-001`, `FR-ASMT-CAND-002` |
| `FEAT-032` | ASMT | So sánh hiện tại vs ứng viên | P0 (Must) | 1 | PER-01..04 | Bảng song song: CVE còn lại, KEV, trạng thái hỗ trợ, LTS, ngày EOL, khoảng cách major, số cảnh báo tương thích (nếu đã quét) | `FR-ASMT-CMP-001`, `FR-ASMT-RISK-002` |
| `FEAT-033` | ASMT | Xếp hạng ưu tiên xử lý | P0 (Must) | 1 | PER-01..04 | Thứ tự đề xuất: (1) có CVE trong KEV; (2) CVSS ≥ 9.0; (3) runtime EOL; (4) CVSS 7.0–8.9; (5) EOL trong ≤ 90 ngày; (6) còn lại. PO duyệt thứ tự (Q-09) | `FR-ASMT-RANK-001`, `FR-ASMT-RISK-001` |
| `FEAT-034` | ASMT | Đánh giá dependency | P0 (Must) | 1 | PER-01..04 | Kế thừa v0.1: findings Composer/npm từ OSV, `MAL-*` là Critical kèm khuyến nghị xoay vòng secret; WordPress core theo `stable-check` + KEV | `FR-ASMT-DEP-001`, `FR-ASMT-DEP-002`, `FR-FEED-WCVE-001`, `FR-FEED-WCVE-002` |
| `FEAT-035` | ASMT | Nhận diện bản vá backport của distro | P0 (Must) | 1 | PER-01, PER-02 | Kế thừa v0.1: đọc changelog gói (dpkg/rpm), đối chiếu danh sách CVE lấy online; runtime có đủ CVE trong changelog được gắn `ok-backport`. Nguồn tracker distro bổ sung: Q-04 | `FR-FEED-DIST-001`, `FR-FEED-DIST-002`, `FR-FEED-NORM-003` |

### 4.6 Chọn phiên bản đích & kế hoạch (`PLAN`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-040` | PLAN | Chọn phiên bản đích | P0 (Must) | 1 | PER-01..03 | Trên dashboard (danh sách ứng viên từ FEAT-031) hoặc CLI (`plan --target`); chặn chọn pre-release và nhánh EOL làm đích | `FR-PLAN-TGT-001` |
| `FEAT-041` | PLAN | Sinh kế hoạch nâng cấp | P0 (Must) | 1 | PER-01..03 | Ghép checklist kịch bản (FEAT-022) + kết quả quét tương thích (FEAT-050..054) + danh sách site bị ảnh hưởng (FEAT-004); ghi thứ tự chuyển site (site đầu tiên làm canary) và điều kiện tiên quyết | `FR-PLAN-GEN-001`, `FR-PLAN-GEN-002` |
| `FEAT-042` | PLAN | Checklist có trạng thái | P0 (Must) | 1 | PER-01..04 | Trạng thái mỗi bước: `todo`, `doing`, `done`, `skipped`, `blocked`; tự chuyển `done` khi job tương ứng thành công; kế hoạch có trạng thái `draft` → `approved` → `in_progress` → `completed` / `rolled_back` | `FR-PLAN-CHK-001`, `FR-PLAN-CHK-002`, `FR-PLAN-STS-001`, `FR-PLAN-DL-001` |
| `FEAT-043` | PLAN | Danh sách thư viện & dependency phải nâng | P0 (Must) | 1 | PER-01..03 | Extension PHP (tên gói tương ứng trên runtime đích, extension bị gỡ khỏi core), Composer package có `require.php` không thỏa nhánh đích (kèm phiên bản tối thiểu thỏa từ Packagist), npm package có `engines.node` không thỏa, framework/CMS cần nâng | `FR-PLAN-DEP-001`, `FR-CMPT-COMP-002` |

### 4.7 Quét tương thích (`CMPT`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-050` | CMPT | Quét tương thích mã PHP | P0 (Must) | 1 | PER-01, PER-02 | Bộ luật tĩnh đóng gói (hàm/extension/cú pháp bị gỡ theo từng bản, ví dụ `mysql_*`, `ereg*` ở 7.0; `each()`, `create_function()` ở 8.0) + `php -l` bằng binary đích sau khi cài song song; kết quả theo file:dòng, mức `error`/`warning`; chỉ đọc, không sửa mã | `FR-CMPT-TOOL-001`, `FR-CMPT-CODE-001`, `FR-CMPT-CODE-002`, `FR-CMPT-CODE-003`, `FR-CMPT-RES-001`, `FR-CMPT-RCT-001` |
| `FEAT-051` | CMPT | Quét tương thích Composer | P0 (Must) | 1 | PER-01..03 | Đối chiếu `require.php`, `require.ext-*` của từng package trong `composer.lock` với runtime đích | `FR-CMPT-COMP-001`, `FR-CMPT-COMP-002`, `FR-CMPT-TOOL-001` |
| `FEAT-052` | CMPT | Quét tương thích npm | P1 (Should) | 1 | PER-01, PER-03 | Đối chiếu `engines.node`; phát hiện native addon cần build lại khi đổi major Node.js | `FR-CMPT-NPM-001`, `FR-CMPT-NPM-002` |
| `FEAT-053` | CMPT | Quét cấu hình ini & extension | P0 (Must) | 1 | PER-01, PER-02 | Directive bị gỡ (ví dụ `mbstring.func_overload` ở 8.0), extension đang bật ở runtime cũ nhưng chưa có gói cho runtime đích | `FR-CMPT-INI-001`, `FR-CMPT-EXT-001`, `FR-CMPT-LDR-001` |
| `FEAT-054` | CMPT | Nhận diện framework/CMS & ma trận PHP | P1 (Should) | 1 | PER-01, PER-02 | Nhận diện WordPress, Laravel, Symfony, Drupal, Magento, Joomla qua `composer.lock`/file đặc trưng; đối chiếu phiên bản PHP được hỗ trợ (endoflife.date nếu có trường hỗ trợ PHP, nếu không thì bộ dữ liệu đóng gói) | `FR-CMPT-FWK-001`, `FR-CMPT-LDR-001`, `FR-FEED-EOL-003` |

### 4.8 Vá cùng nhánh — kế thừa v0.1 (`PTCH`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-060` | PTCH | Vá runtime PHP cùng nhánh | P0 (Must) | 1 | PER-01, PER-02 | Kế thừa `php_upgrade` (apt `--only-upgrade`, dnf/yum, apk); mốc vá lấy từ FEAT-011/012; kiểm tra lại trạng thái sau khi nâng | `FR-PTCH-PHP-001`, `FR-PTCH-PHP-002` |
| `FEAT-061` | PTCH | Mitigation ini tạm thời | P0 (Must) | 1 | PER-01..03 | Kế thừa cơ chế `zz-php-quickpatch-mitigation.ini` và `--no-memlimit`; nội dung lấy từ bộ luật mitigation theo CVE trong gói dữ liệu; tự gỡ khi runtime đã vá | `FR-PTCH-MIT-001`, `FR-PTCH-MIT-002` |
| `FEAT-062` | PTCH | Vá Node.js cùng major | P0 (Must) | 1 | PER-01, PER-03 | Kế thừa: gói hệ thống, tarball kèm kiểm tra SHA-256 từ `SHASUMS256.txt`, hướng dẫn cho nvm | `FR-PTCH-NODE-001` |
| `FEAT-063` | PTCH | Cập nhật Composer/npm có lỗ hổng | P0 (Must) | 1 | PER-01..03 | Kế thừa: `composer update <pkgs> --with-all-dependencies`, khôi phục `composer.json/lock` khi lỗi; `npm audit fix` không `--force`; chạy dưới quyền chủ thư mục | `FR-PTCH-DEP-001`, `FR-PTCH-DEP-002` |
| `FEAT-064` | PTCH | Cập nhật WordPress | P0 (Must) | 1 | PER-01, PER-02 | Kế thừa: `wp core update --minor`, `wp plugin update --all --patch`, `verify-checksums`; mốc từ `stable-check` | `FR-PTCH-WP-001`, `FR-PTCH-WP-002` |
| `FEAT-065` | PTCH | Vá Docker image/container | P0 (Must) | 1 | PER-03 | Kế thừa: nâng tag cùng nhánh trong Dockerfile/compose, mitigation trong container đang chạy + restart; báo cần rebuild | `FR-PTCH-DKR-001`, `FR-PTCH-DKR-002` |
| `FEAT-066` | PTCH | Restart dịch vụ | P0 (Must) | 1 | PER-01..03 | Kế thừa `restart_php_services`, `restart_node_services`; `--no-restart` ghi finding "chưa restart" | `FR-PTCH-RST-001` |
| `FEAT-067` | PTCH | Backup manifest & rollback theo lượt chạy | P0 (Must) | 1 | PER-01..04 | Kế thừa định dạng manifest và `rollback [ID]`; ghi rõ gói đã nâng qua package manager **không** bị hạ cấp khi rollback (như v0.1) | `FR-PTCH-RBK-001`, `FR-PTCH-RBK-002` |

### 4.9 Nâng cấp khác major (`UPG`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-070` | UPG | Cài runtime PHP đích song song | P0 (Must) | 1 | PER-01, PER-02 | Cài nhánh đích bên cạnh bản cũ qua nguồn có sẵn (kho distro, cơ chế đa phiên bản của panel); không gỡ, không thay binary cũ; kiểm tra dung lượng trống trước khi cài | `FR-UPG-PRE-001`, `FR-UPG-INST-001` |
| `FEAT-071` | UPG | Sao chép cấu hình & extension | P0 (Must) | 1 | PER-01, PER-02 | Chuyển thiết lập ini tùy chỉnh, FPM pool, extension tương ứng sang runtime đích; báo directive/extension không chuyển được (FEAT-053) | `FR-UPG-CFG-001`, `FR-UPG-CFG-002` |
| `FEAT-072` | UPG | Chuyển từng site | P0 (Must) | 1 | PER-01, PER-02 | Chuyển 1 site/lần (FPM pool, handler vhost, thiết lập PHP theo site của panel); chỉ cho phép khi site đã đạt quét tương thích không có lỗi mức `error` hoặc người vận hành xác nhận bỏ qua có ghi audit | `FR-UPG-SWT-001`, `FR-UPG-SWT-002`, `FR-UPG-SWT-003`, `FR-UPG-SEQ-001`, `FR-UPG-PRE-001` |
| `FEAT-073` | UPG | Health check sau chuyển | P0 (Must) | 1 | PER-01, PER-02 | Kiểm tra mã HTTP, độ lệch nội dung so với trước khi chuyển, log lỗi PHP trong N phút; ngưỡng cụ thể do SRS đề xuất, PO duyệt (Q-01) | `FR-UPG-HC-001`, `FR-UPG-HC-002`, `FR-UPG-HC-003`, `FR-UPG-HC-004`, `FR-UPG-HC-005`, `FR-UPG-HC-006`, `FR-UPG-SEQ-001` |
| `FEAT-074` | UPG | Rollback site bằng 1 lệnh | P0 (Must) | 1 | PER-01, PER-02 | `rollback-site <site>` hoặc 1 nút + 1 xác nhận; tự rollback khi health check thất bại; hoàn tất ≤ 60 giây (KR4.2) | `FR-UPG-RBK-001`, `FR-UPG-RBK-002`, `FR-UPG-HC-005` |
| `FEAT-075` | UPG | Nâng cấp Node.js khác major | P1 (Should) | 1 | PER-01, PER-03 | Cài dòng đích song song (prefix riêng hoặc nvm), chuyển từng unit systemd / app pm2, health check, rollback | `FR-UPG-NODE-001`, `FR-UPG-INST-001` |
| `FEAT-076` | UPG | Đề xuất đổi major cho Docker | P1 (Should) | 1 | PER-03 | Sửa `FROM`/`image:` sang tag major đích (có backup), đính kèm kết quả quét tương thích; báo cần rebuild/redeploy | `FR-UPG-DKR-001` |
| `FEAT-077` | UPG | Gỡ runtime cũ khi không còn site dùng | P2 (Nice to have) | 1 | PER-01, PER-02 | Chỉ đề xuất khi 0 site dùng runtime cũ trong ≥ N ngày (SRS chốt N); yêu cầu xác nhận; sau khi gỡ thì không rollback site về runtime đó được | `FR-UPG-RMV-001` |

### 4.10 Web console (`CON`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-080` | CON | Lệnh `serve` và xác thực token | P0 (Must) | 1 | PER-01..03 | Python 3 stdlib (`http.server`, `sqlite3`, `subprocess`, `json`); chỉ bind `127.0.0.1`; cổng mặc định cố định (SRS chốt), `--port` để đổi; khi cổng bận bởi phiên `serve` cũ của tool thì báo và cho dừng phiên cũ, không tự tăng cổng; token ngẫu nhiên ≥ 32 byte sinh mỗi lần chạy, chỉ giữ trong bộ nhớ; in URL + lệnh SSH tunnel mẫu; mọi request thiếu token trả 401 | `FR-CON-AUTH-001`, `FR-CON-AUTH-002`, `FR-CON-AUTH-003`, `FR-CON-AUTH-004`, `FR-CON-AUTH-005`, `FR-CON-AUTH-006`, `FR-CON-API-001` |
| `FEAT-081` | CON | Màn hình Tổng quan | P0 (Must) | 1 | PER-01..03 | Số runtime theo trạng thái (vá / chưa vá / EOL / sắp EOL ≤ 90 ngày), số finding KEV/Critical, số dependency có lỗ hổng, tuổi dữ liệu từng nguồn và lỗi nguồn, nút `sync` | `FR-CON-OVW-001`, `FR-CON-FEED-001` |
| `FEAT-082` | CON | Màn hình Đánh giá runtime | P0 (Must) | 1 | PER-01..04 | Hiển thị FEAT-030..033: chi tiết CVE (mã, CVSS, KEV, nguồn), bảng so sánh hiện tại vs ứng viên | `FR-CON-ASMT-001` |
| `FEAT-083` | CON | Màn hình Chọn phiên bản & Kế hoạch/Checklist | P0 (Must) | 1 | PER-01..03 | Chọn đích, sinh kế hoạch, xem/cập nhật checklist, chạy bước tự động hóa được qua job; đạt KR3.1 (≤ 4 thao tác) | `FR-CON-PLAN-001`, `FR-CON-PLAN-002` |
| `FEAT-084` | CON | Màn hình Jobs & Log | P0 (Must) | 1 | PER-01..04 | Danh sách job (hàng đợi, đang chạy, kết thúc), log trực tiếp cập nhật ≤ 2 giây/lần, hủy job | `FR-CON-JOB-001`, `FR-CON-JOB-002` |
| `FEAT-085` | CON | Màn hình Findings thư viện | P0 (Must) | 1 | PER-01..04 | Composer, npm, WordPress theo dự án: package, phiên bản, advisory ID, KEV, `MAL-*`; nút vá (FEAT-063/064) | `FR-CON-DEP-001` |
| `FEAT-086` | CON | Màn hình Rollback | P0 (Must) | 1 | PER-01, PER-02, PER-04 | Danh sách lượt chạy có manifest và các lần chuyển site; xem nội dung manifest; rollback với 1 xác nhận | `FR-CON-RBK-001` |
| `FEAT-087` | CON | Bảo vệ thao tác thay đổi | P0 (Must) | 1 | PER-01..03 | Mọi thao tác thay đổi hiển thị kết quả `--dry-run` trước và yêu cầu xác nhận; token gửi qua header (chống CSRF); tài nguyên tĩnh nhúng sẵn, 0 request tới CDN | `FR-CON-SAFE-001`, `FR-CON-SAFE-002`, `FR-CON-SAFE-003`, `FR-CON-AUTH-005`, `FR-CON-AUTH-006` |

### 4.11 Job runner, log, audit (`JOB`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-090` | JOB | Job runner | P0 (Must) | 1 | PER-01..03 | Console gọi CLI Bash dưới dạng tiến trình con; tối đa 1 job thay đổi hệ thống tại một thời điểm (dùng chung khóa `flock` của v0.1); job chỉ đọc chạy song song tối đa 2; hàng đợi FIFO; hủy job bằng SIGTERM | `FR-JOB-RUN-001`, `FR-JOB-RUN-002`, `FR-JOB-RUN-003`, `FR-JOB-RUN-004`, `FR-CON-SAFE-003` |
| `FEAT-091` | JOB | Lưu & stream log job | P0 (Must) | 1 | PER-01..04 | Mỗi job có file log riêng và JSON kết quả; giữ log theo chính sách dung lượng/thời gian (SRS chốt) | `FR-JOB-LOG-001`, `FR-JOB-LOG-002`, `FR-JOB-LOG-003` |
| `FEAT-092` | JOB | Audit trail | P0 (Must) | 1 | PER-04 | Ghi append-only: thời điểm, nguồn (CLI/console), user hệ thống, lệnh + tham số, ID lượt backup, kết quả, mã thoát; không có chức năng sửa/xóa qua console | `FR-JOB-AUD-001`, `FR-JOB-AUD-002`, `FR-JOB-AUD-003`, `FR-CON-AUD-001` |

### 4.12 Giao diện dòng lệnh (`CLI`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-100` | CLI | Đầu ra `--json` | P0 (Must) | 1 | PER-03, PER-04, console | Mọi lệnh có `--json`; schema có trường `schema_version`; stdout chỉ chứa JSON, log người đọc ghi ra stderr/file | `FR-CLI-JSON-001`, `FR-CLI-JSON-002` |
| `FEAT-101` | CLI | Tương thích ngược v0.1 | P0 (Must) | 1 | PER-01..03 | Giữ `scan`, `fix`, `rollback [ID]`, toàn bộ tùy chọn và mã thoát 0/1/2 của v0.1 | `FR-CLI-COMP-001`, `FR-CLI-COMP-002`, `FR-CLI-ENV-001` |
| `FEAT-102` | CLI | Lệnh mới | P0 (Must) | 1 | PER-01..03 | Đề xuất (SRS chốt tên): `sync`, `assess`, `plan`, `upgrade`, `switch-site`, `rollback-site`, `serve`, `report`, `snapshot export/import`; mỗi lệnh thay đổi hệ thống hỗ trợ `--dry-run` | `FR-CLI-CMD-001`, `FR-CLI-CMD-002`, `FR-CLI-CMD-003`, `FR-CLI-CMD-004`, `FR-CLI-SAFE-001`, `FR-FEED-CMD-001`, `FR-FEED-CMD-002`, `FR-FEED-CMD-004`, `FR-FEED-CMD-005`, `FR-CON-AUTH-001` |

### 4.13 Báo cáo & xuất dữ liệu (`RPT`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-110` | RPT | Báo cáo đánh giá | P1 (Should) | 1 | PER-04, PER-01, PER-02 | Xuất JSON, CSV, Markdown, HTML tĩnh 1 file: runtime, CVE/KEV, EOL/LTS, dependency, kế hoạch; ghi nguồn dữ liệu và thời điểm lấy | `FR-RPT-ASMT-001`, `FR-CON-AUD-001` |
| `FEAT-111` | RPT | Báo cáo bằng chứng thay đổi | P1 (Should) | 1 | PER-04 | Trích audit trail + manifest theo khoảng thời gian: trạng thái trước/sau, ai chạy, rollback nếu có | `FR-RPT-AUD-001` |

### 4.14 Quản lý nhiều server — Phase 2, chỉ thiết kế (`FLT`)
| Feature ID | Phân hệ (Module) | Tên tính năng | Mức độ ưu tiên | Phase | Persona phục vụ | Mô tả vắn tắt | Mã FR (SRS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FEAT-120` | FLT | Danh mục server | P0 (Must) | 2 | PER-01, PER-02, SYS-04 | Khai báo host, cổng, user SSH, khóa/agent, nhóm; không cài agent | `FR-FLT-INV-001`, `FR-FLT-INV-002`, `FR-FLT-RBAC-001` |
| `FEAT-121` | FLT | Thực thi từ xa qua SSH | P0 (Must) | 2 | PER-01, PER-02, SYS-04 | Đẩy CLI Bash vào thư mục tạm, chạy lệnh với `--json`, thu kết quả, xóa thư mục tạm; chạy theo đợt (canary → nhóm) | `FR-FLT-EXEC-001`, `FR-FLT-EXEC-002` |
| `FEAT-122` | FLT | Dashboard tổng hợp nhiều server | P0 (Must) | 2 | PER-01, PER-02, PER-04 | Ma trận server × runtime (KEV, EOL, chưa vá), lọc theo nhóm, đi sâu vào màn hình Phase 1 của từng server | `FR-FLT-DASH-001`, `FR-FLT-DASH-002`, `FR-FLT-AUD-001`, `FR-FLT-RBAC-001` |
| `FEAT-123` | FLT | Cache dữ liệu trung tâm | P1 (Should) | 2 | PER-01, PER-02 | Máy trung tâm đồng bộ feed 1 lần và đẩy snapshot tới server không ra Internet | `FR-FLT-FEED-001` |

### 4.15 Luồng giá trị chính (nâng cấp khác major trên dashboard)
1. `scan` (FEAT-001..005) → Tổng quan hiển thị runtime PHP 7.4 phục vụ 12 site, trạng thái EOL (FEAT-081).
2. Mở Đánh giá runtime → so sánh 7.4 với ứng viên 8.3, 8.4, 8.5 (FEAT-030..033, FEAT-082).
3. Chọn đích 8.4 → "Sinh kế hoạch" → hệ thống quét tương thích mã, Composer, ini, framework (FEAT-040..043, FEAT-050..054).
4. Duyệt kế hoạch → job cài PHP 8.4 song song và sao chép cấu hình (FEAT-070, FEAT-071, FEAT-090).
5. Chuyển site canary → health check (FEAT-072, FEAT-073); thất bại → tự rollback (FEAT-074).
6. Chuyển lần lượt các site còn lại; checklist tự cập nhật trạng thái (FEAT-042).
7. Xuất báo cáo bằng chứng cho kiểm toán (FEAT-110, FEAT-111).

---

## 5. Giả định & Ràng buộc (Assumptions & Constraints)

### 5.1 Ràng buộc (Constraints)
| Mã | Ràng buộc | Căn cứ |
| :--- | :--- | :--- |
| `C-01` | CLI viết bằng Bash, chạy không cần cài thêm runtime; lệnh `scan`/`fix`/`rollback` **không** phụ thuộc Python 3 (khi thiếu Python 3 chỉ mất console). Phiên bản Bash tối thiểu: v0.1 đã dùng `mapfile`, `${var^^}`, chỉ số mảng âm; con số chính xác chưa kiểm chứng, SRS chốt | `DOC-BRS-QP-001` mục 2; mã v0.1 |
| `C-02` | Web console: Python 3 **chỉ thư viện chuẩn**, không cài gói pip. `ThreadingHTTPServer` có từ Python 3.7; phiên bản tối thiểu: Q-05 | `DOC-BRS-QP-001` mục 3; docs.python.org |
| `C-03` | Tài liệu Python ghi `http.server` "không khuyến nghị cho production, chỉ có kiểm tra bảo mật cơ bản" → bắt buộc bind `127.0.0.1`, token mỗi phiên, truy cập qua SSH tunnel; không có TLS riêng (kênh SSH đã mã hóa) | docs.python.org/3/library/http.server.html |
| `C-04` | Thao tác cấp hệ thống (vá/cài runtime, sửa cấu hình server, chuyển site, restart dịch vụ) yêu cầu root; không có root chỉ thực hiện thao tác cấp dự án (Composer, npm, WordPress) — kế thừa v0.1 | `detect_env`, `check_php` v0.1 |
| `C-05` | Không agent thường trú; Phase 2 chỉ dùng SSH | Quyết định PO |
| `C-06` | Chỉ Linux: Debian/Ubuntu (apt), RHEL-family (dnf/yum), Alpine (apk) — như v0.1 | `detect_env` v0.1 |
| `C-07` | Trạng thái lưu tại `STATE_DIR` của v0.1; dữ liệu có cấu trúc dùng SQLite (`sqlite3` stdlib); chỉ 1 job thay đổi hệ thống tại một thời điểm (khóa `flock`) | v0.1 `main()` |
| `C-08` | Tôn trọng giới hạn tốc độ nguồn: GitHub REST API không xác thực 60 request/giờ (docs.github.com); NVD API không có key 5 request / 30 giây, có key 50 request / 30 giây (theo tài liệu thư viện cộng đồng, **chưa kiểm chứng** trên trang chính thức NVD). Hỗ trợ khai báo API key/token tùy chọn trong file cấu hình quyền `0600` | docs.github.com; pkg.go.dev, pypi nvd-api |
| `C-09` | Console hoạt động khi server không ra Internet: 0 tài nguyên tải từ CDN | Yêu cầu offline của `DOC-BRS-QP-001` |
| `C-10` | Mọi tải xuống binary (Node.js tarball, `composer.phar`, `wp-cli.phar`) phải kiểm tra checksum như v0.1 | `node_upgrade_prefix`, `composer_cmd`, `wp_cmd` v0.1 |

### 5.2 Giả định (Assumptions)
| Mã | Giả định | Hệ quả nếu sai |
| :--- | :--- | :--- |
| `A-01` | Server có `curl` và HTTPS ra các nguồn ở mục 2.2, hoặc người vận hành nhập snapshot thủ công | Chạy chế độ offline, cảnh báo tuổi dữ liệu |
| `A-02` | Người vận hành có SSH vào server để mở tunnel tới console | Chỉ dùng được CLI |
| `A-03` | Kho gói distro hoặc panel cung cấp được nhánh PHP đích để cài song song | Kế hoạch đánh dấu bước cài là `blocked`, ghi nguồn cần bổ sung (Q-03) |
| `A-04` | endoflife.date, php.net, NVD, KEV, OSV giữ định dạng JSON đã kiểm chứng ngày 2026-10-22 | Bộ đọc nguồn báo lỗi nguồn, dùng cache/snapshot (KR5.3) |
| `A-05` | Site kiểm tra được bằng HTTP từ chính server (gửi tới `127.0.0.1` kèm header `Host`) | Health check báo `unknown`, không tự chuyển các site tiếp theo |
| `A-06` | Dung lượng đĩa trống đủ cho runtime song song và backup; ngưỡng tối thiểu do SRS chốt | Job cài dừng trước khi thay đổi |

---

## 6. Quy tắc nghiệp vụ định hướng (chuyển SRS đặc tả theo Rule 02)
| Mã BR | Nội dung định hướng |
| :--- | :--- |
| `BR-SEC-001` | CVE có trong CISA KEV luôn xếp hạng ưu tiên cao nhất, bất kể điểm CVSS |
| `BR-SEC-002` | Runtime chỉ được gắn `ok-backport` khi changelog gói chứa **tất cả** CVE áp dụng cho nhánh đó (kế thừa `pkg_has_cves`) |
| `BR-SEC-003` | Tool không xóa file nghi webshell; chỉ báo cáo và khuyến nghị xử lý sự cố |
| `BR-DATA-001` | Dữ liệu dùng để đánh giá cũ hơn 7 ngày → mọi kết quả kèm cảnh báo tuổi dữ liệu |
| `BR-DATA-002` | Mốc bản vá lấy từ php.net / nodejs.org / wordpress.org; trường `latest` của endoflife.date không dùng làm mốc vá |
| `BR-UPG-001` | Nâng cấp khác major không bao giờ thay thế runtime tại chỗ; luôn cài song song và chuyển từng site |
| `BR-UPG-002` | Site chỉ được chuyển khi quét tương thích không có lỗi mức `error`, trừ khi người vận hành xác nhận bỏ qua (ghi audit) |
| `BR-UPG-003` | Health check thất bại → tự rollback site và dừng chuyển các site tiếp theo trong kế hoạch |
| `BR-UPG-004` | Pre-release, nhánh EOL và "PHP 6" không được chọn làm phiên bản đích |

---

## 7. Rủi ro (Risks)
Thang đo: **Xác suất** trong 12 tháng — Thấp < 10%, Trung bình 10–50%, Cao > 50%. **Tác động** — Thấp: chậm đồng bộ, không sai kết quả; Trung bình: sai lệch kết quả đánh giá, không gián đoạn site; Cao: gián đoạn site hoặc bỏ sót CVE thuộc KEV.

| Mã | Rủi ro | Xác suất / Tác động | Hướng xử lý |
| :--- | :--- | :--- | :--- |
| `R-01` | Nguồn online đổi định dạng hoặc ngừng dịch vụ | Trung bình / Cao | Kiểm tra schema khi đọc; fallback cache/snapshot (FEAT-016, FEAT-017) |
| `R-02` | Độ trễ khác nhau giữa các nguồn (đã ghi nhận: endoflife.date `latest` chậm hơn php.net) | Cao / Trung bình | BR-DATA-002; hiển thị `source_updated_at` từng nguồn |
| `R-03` | Panel ghi đè cấu hình do tool chuyển site | Trung bình / Cao | Chuyển site qua cơ chế/CLI của panel (SRS chi tiết theo từng panel) |
| `R-04` | Quét tương thích tĩnh bỏ sót lỗi chạy thực tế | Trung bình / Trung bình | Canary + health check + rollback tự động; đo KR4.3 |
| `R-05` | Bị giới hạn tốc độ NVD/GitHub khi đồng bộ lần đầu | Cao / Thấp | Đồng bộ tăng dần, snapshot làm dữ liệu khởi tạo, API key tùy chọn (C-08) |

---

## 8. Câu hỏi mở (chuyển SRS / PO duyệt)
| Mã | Câu hỏi | Người quyết định |
| :--- | :--- | :--- |
| `Q-01` | Ngưỡng health check: mã HTTP chấp nhận, ngưỡng độ lệch nội dung (%), số dòng log lỗi PHP trong N phút (từ `DOC-BRS-QP-001` mục 6) | SRS đề xuất, PO duyệt |
| `Q-02` | Có tích hợp công cụ refactor tự động (ví dụ Rector) làm bước tùy chọn có duyệt diff không (từ `DOC-BRS-QP-001` mục 6) | SRS đề xuất, PO duyệt |
| `Q-03` | Có cho phép tool thêm kho gói bên thứ ba để cài PHP song song (ví dụ packages.sury.org / `ppa:ondrej/php` cho Debian/Ubuntu, Remi cho RHEL-family) không | PO |
| `Q-04` | Có bổ sung nguồn tracker bảo mật của distro (Debian Security Tracker, Ubuntu USN, Red Hat) ngoài changelog gói không | SRS (theo `DOC-BRS-QP-001` mục 4.5) |
| `Q-05` | Phiên bản Python 3 tối thiểu cho console (3.7 nếu dùng `ThreadingHTTPServer`) và cách xử lý server chỉ có bản cũ hơn | SRS đề xuất, PO duyệt |
| `Q-06` | Có mở rộng audit cho `yarn.lock`, `pnpm-lock.yaml` trong v2 không | PO |
| `Q-07` | Có cho phép job vá cùng nhánh chạy theo lịch không cần người duyệt không (ảnh hưởng KR1.2) | PO |
| `Q-08` | Chu kỳ đồng bộ mặc định 6 giờ có được chấp nhận không | PO |
| `Q-09` | Thứ tự xếp hạng ưu tiên ở FEAT-033 (đặc biệt vị trí "runtime EOL" so với CVSS 7.0–8.9) | PO |

---

## 9. Tài liệu tham chiếu
| Nguồn | Nội dung sử dụng | Trạng thái |
| :--- | :--- | :--- |
| `/home/user/php-quickpatch/docs/php-quickpatch/brainstorms/quickpatch-v2-console.md` | Quyết định PO, scope in/out | Đã đọc |
| `/home/user/php-quickpatch/php-quickpatch.sh` (v0.1.0) | Baseline hành vi (mục 1.2) | Đã đọc toàn bộ 881 dòng |
| https://endoflife.date/api/php.json, https://endoflife.date/api/nodejs.json | Ngày support/EOL/LTS ở mục 3.3 | Gọi thử 2026-10-22, HTTP 200 |
| https://endoflife.date/api/laravel.json (và wordpress, magento, symfony, drupal) | Ma trận framework ↔ PHP | Gọi thử 2026-10-22, HTTP 200 |
| https://www.php.net/releases/index.php?json&version=8.4 | Bản phát hành, `supported_versions` | Gọi thử 2026-10-22, HTTP 200 |
| https://www.php.net/eol.php | EOL PHP 4.4 (2008-08-07) và các nhánh cũ | Đọc 2026-10-22 |
| https://www.php.net/manual/en/migration70.removed-exts-sapis.php | Extension gỡ ở PHP 7.0 (`ereg`, `mssql`, `mysql`, `sybase_ct`) | Đọc 2026-10-22 |
| https://www.php.net/manual/en/migration80.incompatible.php | `each()`, `create_function()`, `array_key_exists()` trên object, `mbstring.func_overload` gỡ ở PHP 8.0 | Đọc 2026-10-22 |
| https://wiki.php.net/rfc/php6 | PHP 6 không phát hành; bỏ phiếu 58–24 chọn tên PHP 7 | Đọc 2026-10-22 |
| https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-109618 | CVSS, CWE, khoảng phiên bản ảnh hưởng | Gọi thử 2026-10-22, HTTP 200 |
| https://github.com/php/php-src/security/advisories | GHSA php-src | Đọc trang web 2026-10-22; REST API chưa kiểm chứng |
| https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | KEV | Gọi thử 2026-10-22, HTTP 200 |
| https://nodejs.org/dist/index.json | Bản phát hành Node.js, cờ `security`/`lts` | Đọc 2026-10-22 |
| https://raw.githubusercontent.com/nodejs/security-wg/main/vuln/core/index.json | CVE Node.js core | Gọi thử 2026-10-22, HTTP 200 |
| https://api.osv.dev/v1/querybatch, https://api.osv.dev/v1/vulns/CVE-2026-109618 | Advisory thư viện; OSV không có CVE PHP core | Gọi thử 2026-10-22 (200 / 404) |
| https://repo.packagist.org/p2/laravel/framework.json, https://registry.npmjs.org/express | Metadata package | Gọi thử 2026-10-22, HTTP 200 |
| https://api.wordpress.org/core/stable-check/1.0/ | Trạng thái bản WordPress core | Gọi thử 2026-10-22, HTTP 200 |
| https://docs.python.org/3/library/http.server.html | Cảnh báo production; `ThreadingHTTPServer` từ 3.7 | Đọc 2026-10-22 |
| https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | 60 request/giờ khi không xác thực | Đọc 2026-10-22 |
| https://pkg.go.dev/github.com/git-pkgs/vulns/nvd, https://pypi.org/project/nvd-api | Giới hạn tốc độ NVD 5 / 50 request mỗi 30 giây | Nguồn cộng đồng, chưa kiểm chứng trên trang NVD chính thức |
| OpenBA-Kit: `skills/prd/SKILL.md`, `_templates/01-prd.md`, `rules/01`, `16`, `17`, `18`, `19` | Cấu trúc và quy ước tài liệu | Đã áp dụng |
| `srs/spec.md` §4.2 (ma trận FEAT → FR), §4.3 (`CR-SRS-04`) | Cột "Mã FR (SRS)" ở §4.2–§4.14; yêu cầu đổi mã kịch bản | Đã đối chiếu 2026-10-22 (bản 1.0.1): 167 mã FR dùng trong PRD đều có trong `srs/functional-requirements.md` |
| `srs/version-scenarios-php.md`, `srs/version-scenarios-php-8x.md`, `srs/version-scenarios-node.md`, `srs/environment-playbooks.md` | Mã kịch bản `SCN-PHP-001..016`, `SCN-NODE-001..012`, playbook `PB-001..PB-018` ở §3.3 | Đã đối chiếu 2026-10-22 (bản 1.0.1) |
| `usecases/index.md` §3, §7.2; `usecases/UC-JOB-003.md`, `UC-RPT-001.md`, `UC-RPT-002.md` | Actor chính của use case, phân loại `PER-04` ở §2.1 | Đã đối chiếu 2026-10-22 (bản 1.0.1) |
