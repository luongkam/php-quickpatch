---
id: DOC-BRS-QP-001
title: Biên bản làm rõ yêu cầu — php-quickpatch v2 (CVE online, kịch bản phiên bản, web console)
version: 1.0.0
phase: Elicitation
domain: Security Patch Management
tags: [brainstorm, php, nodejs, cve, dashboard, upgrade, openba]
depends_on: []
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Biên bản Phỏng vấn & Làm rõ Yêu cầu Nghiệp vụ — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo biên bản từ hội thoại với chủ sản phẩm |

## 1. Ý tưởng thô ban đầu (Raw Concept)
- **Người đề xuất**: Chủ sản phẩm (người vận hành nhiều hệ thống PHP/Node.js).
- **Bối cảnh**: Đã có `php-quickpatch.sh` v0.1.0 (Bash, 881 dòng, tại `/home/user/php-quickpatch/php-quickpatch.sh`). Bản này quét và tự vá PHP runtime, Node.js runtime, Composer, npm, WordPress core, Dockerfile/compose, container đang chạy, và tìm dấu hiệu webshell. Dữ liệu CVE hiện bị **ghi cứng** ở đầu script (`PHP_FIXED`, `NODE_FIXED`, `WP_FIXED`), chỉ phục vụ đợt PHP2Shell (CVE-2026-109618/109619), bản vá Node.js 2026-10-21 và wp2shell.
- **Mô tả ban đầu (nguyên văn)**:
  > "làm tự động lấy CVE từ nguồn online. ngoài ra có nhiều kịch bản: php ở máy đang là version nào, 4,5,6,7,8 gì đó, mỗi loại kịch bản sẽ có 1 list công việc cần xử lý. làm luôn giao diện web console làm dashboard. từ việc scan, lựa chọn version nâng cấp, đánh giá bảo mật của version hiện tại và version nâng cấp, các công việc cần làm (checklist chi tiết, scan được ra, nâng cấp cả các library hoặc dependencies liên quan, còn support hay không? lts hay không? sử dụng openBA để thiết kế chi tiết trước đã"

## 2. Quyết định đã chốt từ các vòng trước (v0.1.0)
| STT | Chủ đề | Quyết định |
| :--- | :--- | :--- |
| 1 | Môi trường mục tiêu | Hỗ trợ cả 3: VPS tự quản (SSH), Docker (host và container), hosting có panel (cPanel, Plesk, aaPanel, CyberPanel, DirectAdmin). Tool **tự nhận diện** môi trường và chọn cách xử lý. |
| 2 | Ngôn ngữ CLI | Bash (chạy được trên server không cần cài thêm runtime). |
| 3 | Mức tự động | **Được phép tự áp bản vá**. Có `--dry-run`, sao lưu và `rollback`. |
| 4 | Phạm vi runtime | PHP **và** Node.js (kèm Composer, npm, WordPress). |

## 3. Bảng câu hỏi phỏng vấn làm rõ (Socratic Probing) — vòng v2
| STT | Vấn đề mơ hồ / Góc khuất | Câu hỏi chất vấn từ BA Agent | Phản hồi chốt từ PO | Quyết định kỹ thuật / Nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Phạm vi dashboard | "Web dashboard chạy ở đâu và quản lý bao nhiêu server?" | "Cục bộ trước, trung tâm sau" | **Phase 1**: lệnh `serve` mở dashboard trên chính server được quản lý. **Phase 2**: dashboard trung tâm quản lý nhiều server qua SSH, không cài agent. Thiết kế cả hai, triển khai Phase 1 trước. |
| 2 | Công nghệ backend console | "Backend web console viết bằng gì?" | "Python 3 stdlib" | Backend dùng **Python 3 thư viện chuẩn** (`http.server`, `sqlite3`, `subprocess`, `json`), không cài gói pip. Console không chạy trên PHP, nên vẫn hoạt động khi PHP đang bị lỗi hoặc đang restart. CLI Bash bổ sung đầu ra `--json` để console đọc. |
| 3 | Nâng cấp khác major (vd 5.6→8.3) | "Nâng cấp khác major thì tool xử lý thế nào?" | "Cài song song, chuyển từng site" | Cài bản PHP mới **song song** bản cũ. Quét tương thích mã nguồn. Đạt thì chuyển **từng site** (FPM pool / vhost / MultiPHP) sang bản mới, kiểm tra sức khỏe site. Giữ bản cũ để **rollback bằng 1 lệnh**. Vá cùng nhánh (patch) vẫn tự động như v0.1. |
| 4 | Xác thực dashboard | "Đăng nhập vào dashboard thế nào?" | "Token + chỉ 127.0.0.1" | Mỗi lần chạy `serve` sinh token ngẫu nhiên. Server chỉ lắng nghe `127.0.0.1`. Truy cập qua SSH tunnel. Không có mật khẩu lưu trữ. |

## 4. Các điểm BA tự làm rõ (không cần hỏi PO, có căn cứ)
| STT | Vấn đề | Căn cứ đã kiểm chứng (2026-10-22) | Quyết định |
| :--- | :--- | :--- | :--- |
| 1 | Nguồn vòng đời phiên bản (support / LTS / EOL) | `https://endoflife.date/api/php.json` và `/api/nodejs.json` trả về `cycle`, `support`, `eol`, `lts`, `latest` (đã gọi thử thành công). | Dùng endoflife.date làm nguồn vòng đời chính. |
| 2 | Nguồn CVE của PHP core | NVD API 2.0 trả về CVE-2026-109618 kèm mô tả (đã gọi thử thành công). OSV **không** có bản ghi cho GHSA của php-src (trả "Vulnerability not found"). | PHP core: NVD (CPE `cpe:2.3:a:php:php`) + php.net releases JSON + GitHub Security Advisories của php-src. Không dựa vào OSV cho PHP core. |
| 3 | Lỗ hổng đang bị khai thác | CISA KEV feed JSON tải được (HTTP 200, khoảng 1,8 MB). | Đánh dấu CVE có trong KEV là ưu tiên cao nhất. |
| 4 | Lỗ hổng thư viện (Composer, npm) | OSV querybatch đã dùng ổn định trong v0.1 (gồm cả bản ghi mã độc `MAL-*`). | Giữ OSV cho Packagist và npm. |
| 5 | Bản vá backport của distro | v0.1 đọc changelog gói (`changelog.Debian.gz`, `rpm --changelog`) và nhận đúng bản vá Ubuntu `8.3.6-0ubuntu0.24.04.13`. | Giữ cơ chế này. Bổ sung nguồn tracker bảo mật của distro nếu cần (để SRS quyết định). |
| 6 | "PHP 6" | PHP 6 chưa từng được phát hành chính thức (dự án bị hủy, nhảy thẳng từ 5.6 lên 7.0). | Kịch bản "PHP 6" = phát hiện chuỗi phiên bản bất thường. Tool báo lỗi nhận diện, không đề xuất nâng cấp tự động. |
| 7 | Hook trong môi trường AgentKit | Hook `scout-block` chặn lệnh Bash chứa `dist`, `node_modules`, `vendor` khi chạy trong Claude Code. | Chỉ ảnh hưởng phiên làm việc với AI, không ảnh hưởng tool khi chạy trên server. |

## 5. Scope đã chốt (Agreed Scope)

### 5.1 Cần làm (In-scope)
1. **Tự động lấy dữ liệu CVE / vòng đời từ nguồn online**, có cache, có chế độ offline dùng bản snapshot đóng gói kèm tool. Thay thế mảng ghi cứng `PHP_FIXED` / `NODE_FIXED` / `WP_FIXED`.
2. **Danh mục kịch bản theo phiên bản đang chạy**: PHP 4.x, 5.x (5.2–5.6), "6" (bất thường), 7.0–7.4, 8.0–8.1 (EOL), 8.2 (chỉ vá bảo mật, EOL 2026-12-31), 8.3–8.5 (còn hỗ trợ), bản pre-release. Node.js: các bản EOL (≤ 20, các số lẻ), 22 (maintenance LTS), 24 (active LTS), 26. Mỗi kịch bản có **checklist công việc chi tiết**.
3. **Đánh giá bảo mật so sánh** giữa phiên bản hiện tại và các phiên bản nâng cấp ứng viên. Thông tin gồm: số CVE theo mức độ, CVE trong KEV, trạng thái hỗ trợ (active / security-only / EOL), có phải LTS không (Node.js), ngày EOL.
4. **Lựa chọn phiên bản nâng cấp** trên dashboard. Tool sinh kế hoạch nâng cấp: các bước, thư viện và dependency cần nâng (Composer, npm, extension PHP, framework/CMS), kết quả quét tương thích mã nguồn.
5. **Nâng cấp khác major theo mô hình cài song song + chuyển từng site + rollback 1 lệnh**. Vá cùng nhánh vẫn tự động như v0.1.
6. **Web console Phase 1**: chạy cục bộ bằng lệnh `serve`. Backend Python 3 stdlib. Xác thực bằng token, chỉ `127.0.0.1`. Các màn hình: tổng quan, đánh giá runtime, chọn phiên bản và kế hoạch / checklist, chạy job và xem log, findings thư viện, rollback.
7. **CLI Bash xuất JSON** (`--json`) để console và các hệ thống khác tiêu thụ.
8. **Thiết kế (chưa triển khai) Phase 2**: dashboard trung tâm nhiều server qua SSH.

### 5.2 Không làm (Out-of-scope) ở giai đoạn này
- Cài agent thường trú trên server được quản lý.
- Tự động sửa mã nguồn ứng dụng của khách hàng (chỉ quét và báo cáo tương thích). Nếu đề xuất công cụ refactor tự động, đó phải là bước tùy chọn có duyệt diff (để SRS quyết định).
- Tự xóa file nghi webshell (chỉ báo cáo, giữ như v0.1).
- Mở dashboard ra mạng ngoài, quản lý tài khoản/mật khẩu (chỉ token + `127.0.0.1` ở Phase 1).
- Hỗ trợ Windows Server.

## 6. Câu hỏi mở chuyển sang bước đặc tả
- Ngưỡng tự động chuyển site khi health check: mã HTTP, độ lệch nội dung, log lỗi PHP trong N phút. Giá trị cụ thể do SRS đề xuất, PO duyệt.
- Có cần tích hợp công cụ refactor tự động (ví dụ Rector) như bước tùy chọn không. SRS đề xuất, PO duyệt.
