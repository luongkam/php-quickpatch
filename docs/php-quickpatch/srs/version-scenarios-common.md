---
id: DOC-SRS-QP-SCN-000
title: Phụ lục đặc tả — Quy ước chung cho danh mục kịch bản theo phiên bản (PHP và Node.js)
version: 1.0.2
phase: Specification
domain: Security Patch Management
tags: [srs, appendix, scenario, checklist, lifecycle, php, nodejs, business-rules, error-matrix]
depends_on:
  - DOC-BRS-QP-001
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Phụ lục đặc tả — Quy ước chung cho danh mục kịch bản theo phiên bản

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo quy ước chung: trạng thái hỗ trợ, mức ưu tiên, loại mục checklist, quy tắc nghiệp vụ BR-SCN, từ điển dữ liệu, ma trận lỗi ERR-SCN; liên kết mã lỗi bổ sung của từng danh mục |
| 1.0.1 | 2026-10-22 | BA Agent | §5.2: sửa regex `chk_id` thành `^CHK-(PHP\|NODE)-[0-9]{3}-[0-9]{2}(-[0-9]{2})?$` để chấp nhận mục con hậu tố `-NN` do `FR-SCN-CHK-001` sinh, thống nhất với `BR-CON-008`, api-spec, ERD console; thêm ví dụ `CHK-PHP-007-11-01` |
| 1.0.2 | 2026-10-22 | BA Agent | §4: thêm cột "Phạm vi áp dụng (Module / Kênh / Actor)" sau "Tên quy tắc" cho 18 quy tắc `BR-SCN-001..018` theo rule 02 §2 và business-rules.md §6 mục 1 (thay phạm vi mặc định ở business-rules.md §2); thêm đoạn quy ước cột ở đầu §4. Không đổi nội dung KHI/THÌ/NGOẠI LỆ. Đánh số 1.0.2 vì 1.0.1 đã dùng cho lần sửa regex `chk_id` |

## 1. Giới thiệu (Introduction)

### 1.1 Mục đích tài liệu (Purpose)
Tài liệu này là phần dùng chung của phụ lục "Danh mục kịch bản theo phiên bản" trong bộ đặc tả php-quickpatch v2. Nội dung gồm định nghĩa, quy tắc nghiệp vụ và cấu trúc dữ liệu mà tính năng "kịch bản + checklist" dùng cho cả hai runtime. Hai danh mục cụ thể nằm ở:

| Tài liệu | Mã | Nội dung |
| :--- | :--- | :--- |
| [version-scenarios-php.md](version-scenarios-php.md) | DOC-SRS-QP-SCN-PHP-001 | Bảng tổng hợp kịch bản PHP, danh mục breaking change, ma trận framework/CMS, biến thể theo môi trường, kịch bản SCN-PHP-001..007 |
| [version-scenarios-php-8x.md](version-scenarios-php-8x.md) | DOC-SRS-QP-SCN-PHP-002 | Kịch bản SCN-PHP-008..016 (PHP 8.x, pre-release, backport distro, tự build) |
| [version-scenarios-node.md](version-scenarios-node.md) | DOC-SRS-QP-SCN-NODE-001 | Bảng tổng hợp và toàn bộ kịch bản SCN-NODE-001..012 |

### 1.2 Phạm vi (Scope)
- **Trong phạm vi**: cách tool gán một runtime đang chạy vào kịch bản, cách tính trạng thái hỗ trợ và phiên bản đích, nội dung checklist từng kịch bản (chuẩn bị → cài song song → quét → nâng dependency → chuyển site → kiểm tra → dọn dẹp), ngưỡng kiểm tra sức khỏe sau khi chuyển.
- **Ngoài phạm vi** (theo biên bản DOC-BRS-QP-001 §5.2): tự sửa mã nguồn ứng dụng trên production, tự xoá file nghi webshell, cài agent thường trú, Windows Server.
- Yêu cầu chức năng (FR), giao diện console và API được đặc tả ở SRS chính (`docs/php-quickpatch/srs/spec.md`, do bước đặc tả khác lập). Phụ lục này chỉ cung cấp dữ liệu và quy tắc mà các FR đó tiêu thụ.

### 1.3 Định nghĩa và ký hiệu (Definitions & Acronyms)
| Thuật ngữ / ký hiệu | Định nghĩa |
| :--- | :--- |
| Kịch bản phiên bản (`kind = VERSION`) | Kịch bản gán theo dải số phiên bản của runtime, mã `SCN-PHP-NNN` / `SCN-NODE-NNN`. Mỗi runtime phát hiện được có đúng 1 kịch bản loại này. |
| Kịch bản bổ trợ (`kind = OVERLAY`) | Kịch bản gán theo nguồn cài đặt (gói distro có backport, tự build, nvm, tarball, NodeSource, gói distro Node.js). Bổ sung mục checklist vào kịch bản phiên bản. |
| Nhánh (branch / line) | PHP: `MAJOR.MINOR` (vd `8.4`). Node.js: `MAJOR` (vd `24`). |
| Nhánh đích (`$NEW`) | Nhánh tool đề xuất nâng lên, tính theo BR-SCN-005 (PHP) hoặc BR-SCN-006 (Node.js). |
| `$OLD`, `$OLD_BIN`, `$NEW_BIN` | Nhánh hiện tại, đường dẫn binary hiện tại, đường dẫn binary đích (vd `/usr/bin/php8.5`, `/opt/node-26/bin/node`). |
| `$SITE`, `$VHOST`, `$APP` | Thư mục gốc site (docroot), tên miền của vhost, tên ứng dụng Node.js (unit systemd hoặc tên tiến trình pm2). |
| `$TV` | Giá trị `testVersion` của PHPCompatibility (vd `8.5` hoặc dải `7.4-8.5`). |
| BC-PHP-xx-NN, BC-NODE-xx-NN | Mã mục trong danh mục breaking change (khoá dữ liệu nội bộ của phụ lục, không phải mã FR/BR). |
| §8 A1..A4 / E1..E10 (PHP), E1..E6 (Node.js) | Hành động và môi trường trong bảng "Biến thể thực thi theo môi trường" của từng danh mục. |
| Backup manifest | Tệp `manifest` trong `STATE_DIR/backups/<run-id>/` kế thừa từ v0.1 (các bước `copy`, `created`, `untar`, `composer-install`, `npm-ci`, `note`), được phát lại ngược khi rollback. |
| KEV | Danh mục CISA Known Exploited Vulnerabilities. |

### 1.4 Tài liệu tham chiếu (References)
Xem §9.

## 2. Trạng thái hỗ trợ và mức ưu tiên

### 2.1 Bảng giá trị trạng thái (`lifecycle_status`)
| Giá trị | Áp dụng | Điều kiện tính (ngày tính = ngày chạy tool, UTC) |
| :--- | :--- | :--- |
| `ACTIVE` | PHP | GA ≤ hôm nay ≤ `support` (hết hỗ trợ chủ động) |
| `SECURITY_ONLY` | PHP | `support` < hôm nay ≤ `eol` |
| `CURRENT` | Node.js | Nhánh đã GA, chưa tới ngày `lts`, hôm nay ≤ `eol` (gồm mọi nhánh lẻ còn hạn) |
| `ACTIVE_LTS` | Node.js | `lts` ≤ hôm nay ≤ `maintenance` (endoflife.date: trường `support`) |
| `MAINTENANCE_LTS` | Node.js | `maintenance` < hôm nay ≤ `eol` |
| `EOL` | Cả hai | hôm nay > `eol` |
| `PRE_RELEASE` | Cả hai | Chuỗi phiên bản có hậu tố `alpha`, `beta`, `RC`, `-dev`, `-pre`, `-nightly`, hoặc nhánh chưa có trong dữ liệu vòng đời nhưng có trong nguồn pre-release chính thức |
| `UNKNOWN` | Cả hai | Không khớp quy tắc nào ở trên (xem SCN-PHP-005, SCN-NODE-008) |

### 2.2 Mức ưu tiên kịch bản (`priority`)
| Mức | Điều kiện (chỉ cần thoả 1 điều kiện, xét từ trên xuống) |
| :--- | :--- |
| Nghiêm trọng | `UNKNOWN`; hoặc quá `eol` > 365 ngày; hoặc có CVE thuộc KEV chưa vá trên đúng bản đang chạy; hoặc `PRE_RELEASE` đang phục vụ ≥ 1 site/ứng dụng công khai |
| Cao | Quá `eol` từ 1 đến 365 ngày; hoặc còn ≤ 90 ngày tới `eol`; hoặc có CVE CVSS ≥ 7,0 chưa vá trên bản đang chạy |
| Trung bình | `SECURITY_ONLY` / `MAINTENANCE_LTS` còn > 90 ngày tới `eol`; hoặc `ACTIVE` / `ACTIVE_LTS` / `CURRENT` còn ≤ 365 ngày tới `eol` |
| Thấp | `ACTIVE` / `ACTIVE_LTS` / `CURRENT` còn > 365 ngày tới `eol` và không có CVE CVSS ≥ 7,0 chưa vá |

## 3. Giai đoạn và loại mục checklist

### 3.1 Giai đoạn (`phase`)
| Mã | Giai đoạn | Mô tả |
| :--- | :--- | :--- |
| P1 | Chuẩn bị | Xác minh phiên bản, kiểm kê site/ứng dụng, extension, framework, đánh giá bảo mật so sánh, sao lưu |
| P2 | Cài song song / vá cùng nhánh | Cài nhánh đích bên cạnh nhánh cũ, hoặc vá lên bản patch mới nhất của cùng nhánh |
| P3 | Quét | Lint cú pháp, quét tương thích, quét mẫu breaking change, chạy test |
| P4 | Nâng dependency | Composer/npm, framework/CMS, plugin, extension, loader mã hoá, native addon |
| P5 | Chuyển site / ứng dụng | Chụp baseline, chuyển từng site/ứng dụng sang nhánh đích |
| P6 | Kiểm tra | Health check tự động theo BR-SCN-009, kiểm thử nghiệp vụ, chuyển CLI/cron |
| P7 | Dọn dẹp | Gỡ mitigation tạm, gỡ nhánh cũ theo BR-SCN-014, cập nhật CI/Docker |

### 3.2 Loại mục (`exec_type`)
| Giá trị | Nhãn trong bảng checklist | Định nghĩa |
| :--- | :--- | :--- |
| `AUTO` | Tự động | Tự động bởi tool: tool tự thực hiện khi chạy chế độ `fix` hoặc job trên console, tôn trọng `--dry-run`, ghi backup manifest trước mọi thay đổi. |
| `SEMI` | Bán tự động (duyệt) | Bán tự động có duyệt: tool chuẩn bị lệnh, danh sách gói hoặc diff; chỉ thực thi sau khi người vận hành bấm duyệt trên console hoặc xác nhận trên CLI. |
| `MANUAL` | Thủ công | Người vận hành hoặc lập trình viên thực hiện; tool chỉ hiển thị hướng dẫn và kiểm tra tiêu chí hoàn thành. |

### 3.3 Trạng thái thực hiện mục (`item_status`)
`PENDING` → `RUNNING` → `DONE` | `FAILED`; ngoài ra `SKIPPED` (điều kiện `applies_when` không thoả) và `WAIVED` (người có quyền duyệt miễn trừ, bắt buộc ghi lý do ≥ 20 ký tự). Mục `FAILED` có thể chuyển lại `RUNNING` khi chạy lại.

## 4. Quy tắc nghiệp vụ dùng chung (Business Rules)

Dải mã: BR-SCN-001..019 dùng chung; BR-SCN-020..039 riêng Node.js (trong [version-scenarios-node.md](version-scenarios-node.md)); BR-SCN-040..059 riêng PHP (trong [version-scenarios-php.md](version-scenarios-php.md)).

Mỗi BR gồm Tên quy tắc, Phạm vi áp dụng, KHI → THÌ → NGOẠI LỆ (rule 02 §2). Cột "Phạm vi áp dụng" theo mẫu `Module / Kênh / Actor` của [business-rules.md §1](business-rules.md): Module là mã module FR (`SCN`, `SCAN`, `ASMT`, `PLAN`, `CMPT`, `PTCH`, `UPG`, `FEED`); Kênh ∈ {CLI (lệnh con theo [spec.md §3.3.2](spec.md)), console (`SCR-*`), API (`/api/v1`), báo cáo, lịch đồng bộ}; Actor theo [spec.md §2.3](spec.md). Cột này thay phạm vi mặc định của dải `BR-SCN-001..018` ở [business-rules.md §2](business-rules.md).

| Mã BR | Tên quy tắc | Phạm vi áp dụng (Module / Kênh / Actor) | KHI (WHEN) | THÌ (THEN) | NGOẠI LỆ (UNLESS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BR-SCN-001` | Gán kịch bản | SCN, SCAN / CLI (`scan`, `assess`), console SCR-002, SCR-003 (job `scan`), API (`GET /api/v1/runtimes/{runtime_id}`) / PER-01..03 | Tool phát hiện 1 binary runtime (PHP hoặc Node.js) | Gán đúng 1 kịch bản `VERSION` theo `version_match`, xét theo thứ tự: (1) kịch bản bất thường/pre-release, (2) dải số phiên bản. Gán thêm 0..n kịch bản `OVERLAY` theo nguồn cài đặt. Checklist hiệu lực = hợp các mục; mục `OVERLAY` cùng giai đoạn đứng trước mục `VERSION`. | Binary không trả về phiên bản trong 10 s → gán SCN-PHP-005 / SCN-NODE-008 và phát `ERR-SCN-422-01` |
| `BR-SCN-002` | Nguồn và độ tươi dữ liệu vòng đời | SCN, FEED / CLI (`feeds update`, `scan`, `assess`, `--offline`), console SCR-008, lịch đồng bộ / PER-01, PER-02, SYS-01, SYS-02 | Tool cần trạng thái, ngày EOL, bản patch mới nhất | PHP: ưu tiên php.net (`supported-versions.php`, `eol.php`, `releases/index.php?json`, `pre-release-builds.php?format=json`), sau đó endoflife.date. Node.js: ưu tiên `nodejs/Release/schedule.json` và `nodejs.org/dist/index.json`, sau đó endoflife.date. Cache 24 giờ. Khi lệch giữa 2 nguồn: dùng nguồn ưu tiên và ghi cảnh báo vào log. | Không có mạng (`--offline`): dùng snapshot đóng gói; snapshot cũ > 30 ngày → cảnh báo; cũ > 90 ngày → `ERR-SCN-503-01`, chỉ cho phép vá cùng nhánh |
| `BR-SCN-003` | Tính trạng thái hỗ trợ | SCN, ASMT / CLI (`scan`, `assess`), console SCR-002, SCR-003, API (`GET /api/v1/runtimes`) / PER-01..04 | Có dữ liệu vòng đời của nhánh | Tính `lifecycle_status` theo §2.1 và `priority` theo §2.2 tại thời điểm chạy, không lưu cứng trong dữ liệu kịch bản | — |
| `BR-SCN-004` | Bản patch tối thiểu an toàn | SCN, ASMT, PTCH / CLI (`scan`, `assess`, `fix`), console SCR-003, SCR-011, API (`GET /api/v1/runtimes/{runtime_id}/candidates`) / PER-01..04 | Nhánh hiện tại còn hỗ trợ | Bản patch tối thiểu = bản nhỏ nhất của nhánh đã vá mọi CVE CVSS ≥ 7,0 và mọi CVE thuộc KEV đã công bố cho nhánh; đề xuất mặc định = bản patch mới nhất của nhánh | Gói distro: áp BR-SCN-015 |
| `BR-SCN-005` | Chọn nhánh đích PHP | SCN, ASMT, PLAN (PHP) / CLI (`assess`, `plan create`), console SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`) / PER-01, PER-02 | Kịch bản cần nâng khác nhánh | Đích = nhánh GA mới nhất thoả đồng thời: (a) `ACTIVE`; (b) GA ≤ hôm nay − 90 ngày; (c) `eol` ≥ hôm nay + 365 ngày; (d) nằm trong dải PHP hỗ trợ của mọi framework/CMS và loader mã hoá phát hiện được (ma trận §6, §7 của danh mục PHP). Không có nhánh thoả (a) → xét lần lượt nhánh cũ hơn chỉ với (b)(c)(d). | Không nhánh nào thoả (c)(d) → `ERR-SCN-409-01`, đề xuất nâng framework/CMS trước; người vận hành có thể chọn đích thủ công có duyệt nhưng không vi phạm BR-SCN-007 |
| `BR-SCN-006` | Chọn nhánh đích Node.js | SCN, ASMT, PLAN (Node.js) / CLI (`assess`, `plan create`), console SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`) / PER-01, PER-03 | Kịch bản cần nâng khác major | Đích = nhánh chẵn mới nhất thoả: (a) ngày `lts` ≤ hôm nay + 14 ngày; (b) `eol` ≥ hôm nay + 365 ngày; (c) mọi `engines.node` của ứng dụng và dependency chấp nhận nhánh; (d) mọi native addon có bản build được cho `NODE_MODULE_VERSION` của nhánh. Không có nhánh thoả → nhánh LTS kế tiếp cũ hơn thoả (b)(c)(d). | Như BR-SCN-005 |
| `BR-SCN-007` | Cấm nhánh trung gian trên production | PLAN, UPG / CLI (`plan create`, `migrate switch`), console SCR-004, SCR-011, API (`POST /api/v1/plans`) / PER-01..03 | Lộ trình cần đi qua nhiều major (vd 5.6 → 8.5) | Quét bậc thang theo nhiều `testVersion` được phép; chỉ chuyển site production sang nhánh đích cuối. Không chuyển production sang nhánh `EOL`, `PRE_RELEASE`, hoặc nhánh Node.js `CURRENT` trước ngày `lts` của nó. | Staging cách ly mạng (không nhận request từ Internet) được dùng nhánh trung gian tối đa 30 ngày |
| `BR-SCN-008` | Vá cùng nhánh và nâng nhánh | PTCH, PLAN, UPG / CLI (`fix`, `plan run`, `migrate switch`), console SCR-004, SCR-011 / PER-01..03 | Bản đang chạy thấp hơn bản patch tối thiểu (BR-SCN-004) | Vá cùng nhánh là mục `AUTO` trong chế độ `fix` (kế thừa v0.1: `php_upgrade`, `node_upgrade`). Nâng khác nhánh luôn là chuỗi mục, mỗi lần chuyển site là mục `SEMI` duyệt riêng từng site. | `--dry-run`: chỉ in lệnh |
| `BR-SCN-009` | Ngưỡng health check sau chuyển (đề xuất, chờ PO duyệt) | UPG (health check) / CLI (`migrate switch`, `migrate healthcheck`), console SCR-006, SCR-009 / PER-01..03, SYS-03 | Một site/ứng dụng vừa chuyển sang nhánh đích | Cửa sổ theo dõi 10 phút, lấy mẫu mỗi 60 s. Tập URL = trang chủ + tối đa 10 URL người dùng khai báo; mỗi vòng gửi 1 request/URL, timeout 10 s. ĐẠT khi tất cả: (1) mã HTTP trùng mã baseline ở 100% request; (2) 0 phản hồi 5xx; (3) kích thước body lệch ≤ 15% so với trung vị baseline; (4) body không chứa `<?php`, `Fatal error`, `Parse error`; (5) P95 thời gian phản hồi ≤ 1,5 × P95 baseline và ≤ P95 baseline + 1.000 ms; (6) PHP: 0 dòng `PHP Fatal error`/`PHP Parse error` mới trong log của pool đích, số dòng `PHP Warning` ≤ max(20; 1,2 × baseline cùng thời lượng); Node.js: số lần khởi động lại (`NRestarts` systemd hoặc `restart_time` pm2) tăng 0, RSS ≤ 1,5 × baseline | Site khai báo `healthcheck: skip` → chỉ kiểm (1)(2) với trang chủ trong 2 phút |
| `BR-SCN-010` | Tự hoàn tác | UPG (health check, rollback) / CLI (`migrate switch [--no-auto-rollback]`), console SCR-006, SCR-007 / PER-01..03, SYS-03 | Health check vi phạm ≥ 1 tiêu chí của BR-SCN-009 | Tool tự hoàn tác site/ứng dụng về nhánh cũ bằng manifest (≤ 60 s từ lúc phát hiện), phát `ERR-SCN-500-01`, đánh dấu mục chuyển site `FAILED` | Người vận hành bật `--no-auto-rollback` cho lần chạy (bắt buộc duyệt) |
| `BR-SCN-011` | Công cụ refactor tự động | CMPT (PHP), PLAN / CLI (`plan run`), console SCR-004 / PER-01, PER-02 | Người vận hành chọn bước tuỳ chọn Rector (PHP) | Chỉ chạy trên bản sao mã nguồn ngoài docroot production, luôn `--dry-run` trước, hiển thị diff để duyệt; chỉ ghi vào bản sao sau khi duyệt; tool không ghi vào docroot production | — |
| `BR-SCN-012` | Không đổi mặc định hệ thống khi cài song song | UPG (cài song song) / CLI (`migrate install`, `plan run`), console SCR-004, SCR-011 / PER-01..03, SYS-03 | Cài nhánh đích trên cùng máy | Trước khi cài, ghim mặc định hiện tại (Debian/Ubuntu: `update-alternatives --set` cho `php` và `php-fpm.sock`; Node.js: không ghi đè `/usr/bin/node` hoặc prefix đang được unit/pm2 dùng). Tiêu chí: sau cài, `readlink -f` của các liên kết mặc định không đổi | Người vận hành chủ động chọn đổi mặc định ở mục P6 "chuyển CLI/cron" |
| `BR-SCN-013` | Phiên bản bất thường | SCN, PTCH, PLAN, UPG / CLI (`scan`, `fix`, `plan`, `migrate`), console SCR-002, SCR-003, SCR-004, API (`GET /api/v1/runtimes/{runtime_id}`) / PER-01..03 | Kịch bản `UNKNOWN` hoặc `PRE_RELEASE` | Khoá mọi mục `AUTO` thay đổi hệ thống cho runtime đó; chỉ cho phép mục kiểm tra/ báo cáo; hiển thị `ERR-SCN-422-01` | Sau khi người vận hành xác minh thủ công và gán lại phiên bản thật (có duyệt) |
| `BR-SCN-014` | Gỡ nhánh cũ | UPG / CLI (`migrate remove-old`), console SCR-004, SCR-007, SCR-011 / PER-01, PER-02 | Không còn site/ứng dụng/cron dùng nhánh cũ | Chỉ đề xuất gỡ khi đủ 14 ngày liên tục không có tiến trình hoặc request dùng nhánh cũ (log FPM/access hoặc `ps`); gỡ là mục `SEMI`; trước khi gỡ lưu danh sách gói/prefix vào manifest | Sau khi gỡ, rollback 1 lệnh không còn khả dụng cho các lần chuyển trước đó; console phải hiển thị cảnh báo này trước nút duyệt |
| `BR-SCN-015` | CVE với gói distro | SCAN, ASMT, FEED, PTCH / CLI (`scan`, `assess`, `fix`), console SCR-002, SCR-003, API, báo cáo / PER-01..04 | Binary thuộc gói distro (dpkg/rpm/apk) | Trạng thái vá CVE xác định bằng changelog gói (`changelog.Debian.gz`, `rpm -q --changelog`) hoặc tracker bảo mật distro, không so sánh số phiên bản upstream (kế thừa `pkg_has_cves` v0.1) | Không đọc được changelog → coi là chưa xác định, mức ưu tiên tính như chưa vá |
| `BR-SCN-016` | Điều kiện tiên quyết cài song song (đề xuất) | UPG, PLAN / CLI (`plan create`, `plan approve`, `migrate install`), console SCR-004 / PER-01..03 | Trước mục P2 cài nhánh đích | Yêu cầu: dung lượng trống ≥ 2 GB tại phân vùng cài; RAM khả dụng ≥ 512 MB; quyền root hoặc API panel; OS còn trong thời hạn hỗ trợ và có kho gói chứa nhánh đích | Không đạt → `ERR-SCN-412-01` |
| `BR-SCN-017` | Ghi manifest | PTCH, UPG, PLAN / CLI (`fix`, `plan run`, `migrate install`, `migrate switch`, `migrate remove-old`), console (job ghi) / PER-01..03 | Mọi mục `AUTO`/`SEMI` thay đổi file, gói hoặc cấu hình | Ghi bước hoàn tác vào backup manifest trước khi thay đổi; mục không có bước hoàn tác (vd nâng gói apt/dnf) ghi `note` như v0.1 | `--dry-run` |
| `BR-SCN-018` | Thứ tự phụ thuộc mục | PLAN / CLI (`plan run`, `plan item`), console SCR-004, API (`POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`) / PER-01..03 | Người vận hành chạy 1 mục checklist | Mục P5 chỉ chạy khi mọi mục P3, P4 bắt buộc của cùng site ở `DONE` hoặc `WAIVED` | Vi phạm → `ERR-SCN-424-01` |

## 5. Cấu trúc dữ liệu kịch bản (Data Dictionary)

### 5.1 Thực thể `scenario`
| Tên trường (Logical) | Tên cột (Physical) | Kiểu dữ liệu | Độ dài | Cho phép Null? | Khóa | Ràng buộc / Giá trị mặc định | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Mã kịch bản | scenario_id | VARCHAR | 16 | Không | PK | Regex `^SCN-(PHP\|NODE)-\d{3}$` | Định danh kịch bản |
| Runtime | runtime | ENUM | - | Không | - | `php`, `node` | Runtime áp dụng |
| Loại | kind | ENUM | - | Không | - | `VERSION`, `OVERLAY` | Theo dải phiên bản hay theo nguồn cài đặt |
| Biểu thức khớp | version_match | VARCHAR | 256 | Không | - | Regex trên chuỗi phiên bản thô hoặc điều kiện nguồn cài đặt | Dùng ở BR-SCN-001 |
| Thứ tự xét | match_order | SMALLINT | - | Không | - | 1..999, nhỏ xét trước | Kịch bản bất thường/pre-release có giá trị nhỏ nhất |
| Dải breaking change | bc_scope | VARCHAR | 64 | Có | - | vd `(OLD, NEW]` | Chọn mọi mục BC có phiên bản trong dải |
| Ghi chú đích | target_note | TEXT | - | Có | - | - | Phương án thay thế khi BR-SCN-005/006 không ra đích |
| Ngày dữ liệu | data_as_of | DATE | - | Không | - | `2026-10-22` cho bản 1.0.0 | Ngày kiểm chứng dữ liệu trong tài liệu |

### 5.2 Thực thể `checklist_item`
| Tên trường (Logical) | Tên cột (Physical) | Kiểu dữ liệu | Độ dài | Cho phép Null? | Khóa | Ràng buộc / Giá trị mặc định | Diễn giải nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Mã mục | chk_id | VARCHAR | 20 | Không | PK | Regex `^CHK-(PHP\|NODE)-[0-9]{3}-[0-9]{2}(-[0-9]{2})?$` (khớp `BR-CON-008`); dài tối đa 18 ký tự (`CHK-NODE-NNN-NN-NN`) | vd `CHK-PHP-007-11` (mục mẫu); `CHK-PHP-007-11-01` (mục con thứ 01 sinh khi mở rộng mục "(khi nâng)", `FR-SCN-CHK-001`) |
| Mã kịch bản | scenario_id | VARCHAR | 16 | Không | FK → scenario | - | Kịch bản chứa mục |
| Giai đoạn | phase | ENUM | - | Không | - | `P1`..`P7` | Theo §3.1 |
| Hành động | action | TEXT | - | Không | - | ≤ 500 ký tự | Mô tả hành động cụ thể |
| Loại | exec_type | ENUM | - | Không | - | `AUTO`, `SEMI`, `MANUAL` | Theo §3.2 |
| Lệnh / cơ chế kiểm tra | check_mechanism | TEXT | - | Không | - | Lệnh shell, API panel hoặc thao tác giao diện | Cách thực hiện và cách kiểm tra |
| Tiêu chí hoàn thành | done_criteria | TEXT | - | Không | - | Phải đo được (số, mã thoát, chuỗi) | Điều kiện chuyển `DONE` |
| Rủi ro | risk | TEXT | - | Có | - | - | Rủi ro và cách giảm |
| Điều kiện áp dụng | applies_when | VARCHAR | 256 | Có | - | vd `framework=wordpress`, `loader=ioncube` | Không thoả → `SKIPPED` |
| Phụ thuộc | depends_on | JSON | - | Có | - | Mảng `chk_id` | Dùng ở BR-SCN-018 |
| Trạng thái | item_status | ENUM | - | Không | - | Mặc định `PENDING` | Theo §3.3, lưu theo từng lần chạy và từng site |

## 6. Ma trận lỗi của bộ máy kịch bản (Error Matrix)

Ma trận lỗi tổng hợp của sản phẩm nằm ở SRS chính; bảng dưới chỉ gồm lỗi phát sinh từ tính năng kịch bản + checklist.

| Mã ERR | HTTP | Điều kiện phát sinh | Localization key | Thông báo hiển thị | Mức độ | Hành động tiếp theo |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `ERR-SCN-422-01` | 422 | Chuỗi phiên bản không khớp dải đã biết: major PHP = 6, major vượt nhánh mới nhất trong dữ liệu, hậu tố lạ, hoặc binary không trả phiên bản trong 10 s | `scn.version.unrecognized` | "Không nhận diện được phiên bản {runtime} '{raw}'. Tự động hoá cho runtime này đã bị khoá." | High | Làm theo checklist SCN-PHP-005 hoặc SCN-NODE-008 |
| `ERR-SCN-409-01` | 409 | Không có nhánh đích thoả BR-SCN-005/006 với framework, loader hoặc `engines` đã phát hiện | `scn.target.incompatible` | "Không có phiên bản đích tương thích với {component} {version}." | High | Nâng framework/CMS/loader trước hoặc chọn đích thủ công có duyệt |
| `ERR-SCN-409-02` | 409 | Người vận hành chọn đích là nhánh `EOL`, `PRE_RELEASE` hoặc Node.js `CURRENT` chưa tới ngày LTS cho site production | `scn.target.not_allowed` | "Không thể chuyển site production sang {target}: nhánh đang ở trạng thái {status}." | High | Chọn nhánh đích khác hoặc dùng staging cách ly |
| `ERR-SCN-412-01` | 412 | Điều kiện BR-SCN-016 không đạt | `scn.precondition.failed` | "Máy chủ chưa đáp ứng điều kiện cài song song: {detail}." | High | Bổ sung tài nguyên/quyền hoặc chuyển sang máy chủ mới |
| `ERR-SCN-424-01` | 424 | Chạy mục khi mục phụ thuộc chưa `DONE`/`WAIVED` (BR-SCN-018) | `scn.dependency.pending` | "Chưa thể thực hiện {chk_id}: mục {dep_id} chưa hoàn thành." | Medium | Hoàn thành mục phụ thuộc hoặc xin miễn trừ |
| `ERR-SCN-500-01` | 500 | Health check vi phạm BR-SCN-009; tool đã hoàn tác theo BR-SCN-010 | `scn.switch.rolled_back` | "Site {vhost} không đạt kiểm tra sau khi chuyển sang {target}; đã hoàn tác về {old}." | Critical | Xem báo cáo health check và log; sửa lỗi trên staging rồi chạy lại |
| `ERR-SCN-503-01` | 503 | Không lấy được dữ liệu vòng đời/CVE online và snapshot cũ > 90 ngày | `scn.data.stale` | "Dữ liệu vòng đời đã cũ {days} ngày; tạm ngừng đề xuất nâng nhánh." | Medium | Khôi phục kết nối mạng hoặc cập nhật bản tool có snapshot mới |

Mã lỗi riêng từng runtime: `ERR-SCN-409-03`, `ERR-SCN-412-02` ([danh mục PHP §9](version-scenarios-php.md#9-ma-trận-lỗi-bổ-sung-php)); `ERR-SCN-412-03`, `ERR-SCN-424-02` ([danh mục Node.js §9](version-scenarios-node.md#9-ma-trận-lỗi-bổ-sung-nodejs)).

## 7. Sai lệch dữ liệu đã phát hiện khi kiểm chứng (2026-10-22)
| STT | Sai lệch | Bằng chứng | Xử lý trong thiết kế |
| :--- | :--- | :--- | :--- |
| 1 | endoflife.date chậm 1 bản patch so với php.net | endoflife.date `php.json`: `8.5.latest = 8.5.11`; php.net `releases/active.php`: 8.5.12 phát hành 2026-10-21 (tương tự 8.2.35, 8.3.36, 8.4.27) | BR-SCN-002: bản patch mới nhất lấy từ php.net |
| 2 | Ngày EOL PHP 5.4 lệch 11 ngày | php.net `eol.php`: 2015-09-03; endoflife.date: 2015-09-14 | BR-SCN-002: ưu tiên php.net |
| 3 | Node.js 24 không còn ở pha Active LTS | `nodejs/Release/schedule.json`: `v24.maintenance = 2026-10-20`; endoflife.date `support = 2026-10-20` | Danh mục Node.js ghi Node 24 = `MAINTENANCE_LTS` từ 2026-10-20, khác mô tả "active LTS" ở yêu cầu đầu vào |
| 4 | Node.js đổi lịch phát hành từ nhánh 27 | `schedule.json`: `v27.alpha = 2026-10-28`, `start = 2027-04-22`, `lts = 2027-10-20`; bài "Evolving the Node.js Release Schedule" trên nodejs.org | Từ 27 không còn nhánh lẻ; kịch bản SCN-NODE-008 xử lý bản alpha |
| 5 | Remi chưa cập nhật bản vá 2026-10-21 | rpms.remirepo.net/wizard liệt kê 8.5.11, 8.4.26 tại 2026-10-22 | Mục vá cùng nhánh trên E2 (Remi) phải chấp nhận độ trễ kho; tool so với changelog gói (BR-SCN-015) |

## 8. Giả định, ràng buộc và câu hỏi mở
| STT | Nội dung | Loại | Người quyết định |
| :--- | :--- | :--- | :--- |
| 1 | Các ngưỡng BR-SCN-009 (15%, 1,5×, 10 phút, 20 dòng Warning) là đề xuất của BA dựa trên câu hỏi mở số 1 của biên bản DOC-BRS-QP-001 §6 | Câu hỏi mở | PO duyệt |
| 2 | Rector là bước tuỳ chọn có duyệt diff theo BR-SCN-011, chỉ trên bản sao (câu hỏi mở số 2 của DOC-BRS-QP-001 §6) | Câu hỏi mở | PO duyệt |
| 3 | Ngưỡng 90 ngày sau GA (BR-SCN-005 b) và 14 ngày trước LTS (BR-SCN-006 a) là đề xuất | Câu hỏi mở | PO duyệt |
| 4 | Ngưỡng tài nguyên BR-SCN-016 (2 GB đĩa, 512 MB RAM) chưa đo thực nghiệm | Giả định | Dev đo khi triển khai |
| 5 | Tên lệnh CLI v2 cho từng mục do SRS chính đặt; phụ lục chỉ mô tả cơ chế bằng lệnh hệ thống và hành vi v0.1 | Ràng buộc | BA (SRS chính) |
| 6 | Lệnh CLI của panel đánh dấu "chưa kiểm chứng" trong bảng biến thể môi trường cần chạy thử trên máy có panel trước khi đưa vào mục `AUTO` | Ràng buộc | QA |

## 9. Tài liệu tham chiếu (References)
Các nguồn dưới được truy cập ngày 2026-10-22.

| Nguồn | URL | Dùng cho |
| :--- | :--- | :--- |
| Biên bản làm rõ yêu cầu v2 | `docs/php-quickpatch/brainstorms/quickpatch-v2-console.md` (DOC-BRS-QP-001) | Phạm vi, quyết định nghiệp vụ |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | Hành vi kế thừa: backup manifest, `pkg_has_cves`, vá cùng nhánh, mitigation, restart |
| endoflife.date API | https://endoflife.date/api/php.json, https://endoflife.date/api/nodejs.json | Trạng thái, ngày EOL |
| php.net | https://www.php.net/supported-versions.php, https://www.php.net/eol.php, https://www.php.net/releases/active.php | Vòng đời PHP |
| Node.js Release WG | https://raw.githubusercontent.com/nodejs/Release/main/schedule.json | Lịch LTS/maintenance/EOL |
| Node.js blog | https://nodejs.org/en/blog/announcements/evolving-the-nodejs-release-schedule | Lịch phát hành mới từ nhánh 27 |
| Remi wizard | https://rpms.remirepo.net/wizard/ | Độ trễ kho Remi |
| ISO/IEC/IEEE 29148, OpenBA-Kit rules 02, 03, 09, 11, 16, 18, 19 | `luongkam/openba-kit/rules/` | Quy ước tài liệu |
