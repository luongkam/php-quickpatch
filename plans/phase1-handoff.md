# Bàn giao: sửa 2 lỗi v0.1 và triển khai Phase 1 của php-quickpatch v2

Ngày bàn giao: 2026-10-23. Người duyệt (PO): chủ repo `luongkam`.

## 1. Trạng thái khi bàn giao

- **Tool v0.1.0** tại `php-quickpatch.sh` (Bash, 881 dòng). Có `scan`, `fix`, `rollback`. Tool tự nhận diện môi trường, gồm VPS, panel hosting và Docker. Dữ liệu CVE đang **ghi cứng** ở dòng 13–18 (`PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED`). Tool đã được thử trên Ubuntu 24.04 (PHP 8.3, Node 22, Composer), với các fixture giả lập cho Composer, npm, WordPress, Dockerfile và webshell.
- **Bộ thiết kế OpenBA** nằm ở `docs/php-quickpatch/`: khoảng 27.000 dòng, 87 file Markdown, 14 wireframe, 34 sơ đồ đã render, cộng trang tổng hợp `preview.html`.
  - Số mã ID: 168 FR, 200 BR, 129 ERR, 60 NFR, 28 kịch bản `SCN-*`, 35 UC, 120 US, 394 AC, 421 TC.
  - RTM phủ 99,4% FR và 94,4% AC.
- **Kiểm định thiết kế:** đã chạy 2 vòng, mỗi vòng 3 góc nhìn (truy vết, rule OpenBA, độ chính xác kỹ thuật). Vòng 1 tìm 81 vấn đề, vòng 2 tìm 175 vấn đề. Đã áp dụng 569 sửa đổi và bác 65 đề xuất sai. **Các sửa đổi của vòng 2 chưa được kiểm lại**, và còn khoảng 70 lỗi mức low (chủ yếu lệch tên hoặc lệch tham chiếu trong `test/rtm.md`, related_diagrams của một vài UC, tên FR dạng cụm danh từ).
- **OpenBA-Kit** là repo public `luongkam/OpenBA-Kit` (commit `dea3e3a`). Tài liệu tham chiếu nó tại `/home/user/luongkam/openba-kit`.

## 2. Quyết định đã chốt

| Chủ đề | Quyết định | Nguồn |
| :--- | :--- | :--- |
| Môi trường | VPS, panel (cPanel, Plesk, aaPanel, CyberPanel, DirectAdmin), Docker; tự nhận diện | Biên bản brainstorm §2 |
| CLI | Bash ≥ 4.3; được tự áp bản vá, có `--dry-run`, backup, `rollback` | Biên bản §2 |
| Phạm vi runtime | PHP và Node.js, kèm Composer, npm, WordPress | Biên bản §2 |
| Dashboard | Phase 1 chạy cục bộ bằng lệnh `serve`; Phase 2 trung tâm qua SSH (Phase 2 chỉ thiết kế, chưa làm) | Biên bản §3 mục 1 |
| Backend console + lớp dữ liệu online | Python 3 thư viện chuẩn, 0 gói pip. **PO đã đồng ý ngày 2026-10-23** dùng `qp-feeds.py` (Python) cho đồng bộ CVE/vòng đời | Biên bản §3 mục 2, spec §2.1 |
| Nâng khác major | Cài song song, chuyển từng site, health check, rollback 1 lệnh | Biên bản §3 mục 3 |
| Xác thực console | Token 256-bit sinh mỗi lần `serve`, chỉ bind `127.0.0.1`, truy cập qua SSH tunnel | Biên bản §3 mục 4 |
| Câu hỏi mở `Q-01..Q-09`, `Q-SRS-01` (spec §4.4) | **Mặc định áp dụng đề xuất của SRS** cho đến khi PO nói khác | Bàn giao này |
| 2 lỗi bảo mật v0.1 (mục 4) | **PO đồng ý sửa ngay trong script v0.1** (bản v0.1.1) | Bàn giao này |

Lưu ý: `CR-SRS-07` (unit Remi `php84-php-fpm` không được restart; biểu thức dpkg không khớp `ea-php` trên cPanel chạy Ubuntu) **không** thuộc 2 lỗi trên. Hai lỗi này sửa trong mã v2.

## 3. Thứ tự đọc tài liệu

1. `docs/php-quickpatch/brainstorms/quickpatch-v2-console.md`: quyết định nghiệp vụ, phạm vi làm và không làm.
2. `docs/php-quickpatch/srs/spec.md`: kiến trúc (§2.1, gồm thành phần phát hành và bố cục `STATE_DIR`), ràng buộc (§2.5), giao diện ngoài và lệnh CLI (§3.3), CR (§4.3), câu hỏi mở (§4.4).
3. `srs/functional-requirements.md`, `srs/business-rules.md`, `srs/error-matrix.md`, `srs/nfr.md`: yêu cầu chi tiết, nguồn sự thật cho mã ID.
4. `srs/data-sources.md`, `srs/data-sources-merge-risk.md`, `srs/data-sources-cache-cli.md`: 17 nguồn `SRC-*`, TTL, hợp nhất nguồn, `min_patched`, điểm rủi ro (số nguyên, có ca test làm tròn), cache, snapshot, lệnh `feeds`.
5. `srs/version-scenarios-common.md`, `-php.md`, `-php-8x.md`, `-node.md`: 28 kịch bản và checklist `CHK-*`, là dữ liệu cho `share/php-quickpatch/catalog/`.
6. `srs/environment-playbooks*.md`: `PB-001..019` (cài song song, chuyển site, rollback theo từng môi trường) và health check `HC-C0..C9`.
7. `srs/erd*.md`, `srs/flows*.md`, `srs/states.md`: dữ liệu, luồng tuần tự, máy trạng thái (job, plan, site migration, checklist, feed, phiên console).
8. `api/api-spec*.md`: 57 API REST của console, cộng hợp đồng JSON của CLI (`api-spec-cli-json.md`, có `schema_version`).
9. `html-wireframe/*.html`: 14 màn hình (11 cho Phase 1, 3 `fleet-*` cho Phase 2).
10. `userstories/`, `test/`: user story, AC Gherkin, test case, RTM. Dùng làm tiêu chí nghiệm thu.

`preview.html` gom toàn bộ hồ sơ để đọc nhanh trên trình duyệt.

## 4. Việc 1: sửa 2 lỗi bảo mật của v0.1 (làm trước, phát hành v0.1.1)

1. **`rollback --dry-run` vẫn thay đổi file thật.** `do_rollback` (từ dòng 807) chạy trực tiếp `cp -a`, `rm -f`, `tar -xzf`, `composer install` và `npm ci`, không kiểm tra `DRY_RUN`; chỉ hàm `run()` tôn trọng cờ này. Cách sửa: mọi hành động phát lại manifest phải đi qua nhánh dry-run và chỉ in ra việc sẽ làm. Căn cứ: `FR-PTCH-RBK-002`.
2. **`STATE_DIR` dự phòng đoán trước được và không kiểm chủ sở hữu.** Dòng 851–852 dùng `mkdir -p` và dự phòng `${TMPDIR:-/tmp}/php-quickpatch-$EUID` cho mọi người dùng, kể cả root, không kiểm symlink, chủ sở hữu hay quyền. Người dùng cục bộ khác có thể tạo sẵn thư mục, cài một `manifest` giả, và khi `rollback` chạy thì các lệnh trong manifest chạy bằng quyền người chạy tool. Cách sửa: theo đúng 5 bước "Chọn và kiểm tra an toàn `STATE_DIR`" ở spec §2.1 (root không có dự phòng; không root dùng `mktemp -d … .XXXXXX` mode 0700; dùng `lstat`; `st_uid = EUID`; `mode & 0022 = 0`; kiểm `backups/<run_id>/` và `manifest` trước khi đọc). Thoát với mã 2 và báo `ERR-CLI-412-01`. Căn cứ: `CR-SRS-13`, `NFR-SEC-010`.

Tiêu chí xong:
- Có test hồi quy:
  - `rollback --dry-run` không làm đổi SHA-256 của file nào trong manifest và không chạy lệnh nào.
  - Thư mục hoặc symlink do user khác tạo sẵn ở đường dẫn chính và đường dẫn dự phòng: 100% các lượt thoát mã 2 hoặc bỏ qua ứng viên, không ghi file nào vào đó.
  - Ca root trên filesystem chỉ đọc.
- Shellcheck sạch ở mức warning.
- Đổi `QP_VERSION` thành 0.1.1, ghi rõ thay đổi hành vi so với v0.1.0.

## 5. Việc 2: triển khai Phase 1 (chỉ các FR phase 1)

Bắt đầu bằng việc lập kế hoạch trong `plans/` (một file index và các file phase). Làm theo từng mốc; mỗi mốc có test chạy được và một commit riêng. Thứ tự đề xuất:

| Mốc | Nội dung | Tài liệu chính |
| :--- | :--- | :--- |
| M1 | Khung repo theo spec §2.1 (`share/php-quickpatch/{qp-feeds.py,console/,catalog/,schemas/}`), envelope `--json` có `schema_version`, JSON Schema, bộ test (Bash và `python3 -m unittest`, không cần gói ngoài), giữ tương thích ngược `scan`/`fix`/`rollback` | spec §2.1, §3.3; `api-spec-cli-json.md`; `FR-CLI-*` |
| M2 | `qp-feeds.py`: 17 nguồn, cache SQLite có TTL, đồng bộ tăng dần, hợp nhất nguồn, `min_patched`, phát hiện backport, điểm rủi ro, snapshot offline, lệnh `feeds update/status/...`; thay các mảng ghi cứng | `data-sources*.md`; `FR-FEED-*` |
| M3 | Catalog kịch bản và checklist (chuyển từ `version-scenarios-*.md` sang JSON/TSV), gán kịch bản, `assess` (hiện tại so với ứng viên, KEV, support, LTS, EOL, điểm rủi ro), `plan` (chọn đích, sinh checklist có trạng thái) | `version-scenarios-*.md`; `FR-SCN-*`, `FR-ASMT-*`, `FR-PLAN-*` |
| M4 | Quét tương thích: luật BC tĩnh, PHPCompatibility/phpcs và Composer tải về `STATE_DIR/tools/php` có kiểm checksum, `check-platform-reqs` với PHP đích, extension, ini, framework, npm `engines` | `FR-CMPT-*` |
| M5 | `migrate`: cài song song, pool, ini, extension, chuyển từng site, health check `HC-C0..C9`, tự rollback, `rollback-site`. Làm Debian/Ubuntu + Nginx/Apache-FPM trước, rồi tới các panel | `environment-playbooks*.md`; `FR-UPG-*` |
| M6 | Console `qp-console.py`: `serve`, token, kiểm tra Host, CSRF, CSP, danh sách trắng lệnh (`shell=False`), job runner + `flock`, SSE, audit chuỗi hash, 11 màn hình Phase 1 theo wireframe, 57 API | `api-spec*.md`, `states.md`, `erd*.md`, `html-wireframe/`; `FR-CON-*`, `FR-JOB-*` |
| M7 | Báo cáo (`FR-RPT-*`), test đầu–cuối, đối chiếu RTM, cập nhật tài liệu, phát hành 2.0.0 | `test/`, `userstories/` |

## 6. Ràng buộc kỹ thuật bắt buộc

- `scan`, `fix`, `rollback` và `migrate` phải chạy được khi máy không có Python (`C-01`). Python 3.6 trở lên chỉ bắt buộc cho console, `assess`, `plan`, `report` và chuẩn hoá feed.
- Python chỉ dùng thư viện chuẩn, không cài gói pip, không tải JS/CSS từ CDN. Console gọi CLI bằng argv cố định với `shell=False` (`C-SRS-01..05`).
- Mọi thay đổi hệ thống đi qua CLI để dùng chung `flock`, manifest và audit.
- Rollback phát lại manifest theo thứ tự ngược. Bước cài lại (`composer-install`, `npm-ci`) phải được ghi vào manifest **trước** bước sao lưu file, để khi chạy ngược chúng chạy sau bước khôi phục (lỗi này đã gặp và đã sửa ở v0.1).
- Không tự xoá file nghi webshell.
- Không mở console ra mạng ngoài.

## 7. Môi trường thử nghiệm và lưu ý

- Container cloud không có systemd đang chạy và không có Docker daemon. Các phần restart service, panel và container thật phải thử bằng fixture hoặc giả lập; ghi rõ phần nào chưa thử được trên máy thật.
- Biến môi trường dùng cho test: `QP_PHP_BINS` và `QP_NODE_BINS` (ghi đè việc dò runtime). Khi thử nâng Node, **không** thử trên `/opt/node22` vì Claude Code đang chạy bằng nó; hãy chép ra một prefix riêng.
- Nếu môi trường có AgentKit, hook `scout-block` có thể chặn các lệnh Bash chứa `dist`, `node_modules` hoặc `vendor`. Khi bị chặn, dùng công cụ Read/Grep hoặc lệnh `npm ls`/`composer show`; không tìm cách lách hook.
- HTTPS ra ngoài đi qua proxy có sẵn. endoflife.date, php.net, NVD, CISA KEV và OSV đã gọi thử thành công ngày 2026-10-22.

## 8. Quy trình git

- Làm trên nhánh riêng, commit theo mốc và push. Không tạo pull request trừ khi PO yêu cầu.
- Không commit secret. Không ghi tên model AI vào commit, code hay tài liệu.
