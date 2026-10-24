# M2 — Lớp dữ liệu online `qp-feeds.py`

Mục tiêu: thay `PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED` bằng bundle chuẩn hoá đồng bộ từ 17 nguồn `SRC-001..017`, có cache TTL, đồng bộ tăng dần, hợp nhất, `min_patched`, phát hiện backport, điểm rủi ro 0–100 (số nguyên, có ca làm tròn), snapshot offline và lệnh `feeds`.

## 1. Tài liệu chính
`srs/data-sources.md` (17 nguồn, chính sách gọi, `FR-FEED-*`, `BR-FEED-*`), `srs/data-sources-merge-risk.md` (mô hình, hợp nhất, so khớp dải phiên bản, `min_patched`, backport, `BR-FEED-040..044`), `srs/data-sources-cache-cli.md` (cây `feeds/`, bundle TSV + `feeds.db`, snapshot, `feeds` CLI, mã thoát), `srs/erd-feeds-files.md`, `srs/states.md` (máy trạng thái feed), `api/api-spec-cli-json.md` §10.

## 2. Thiết kế
- `qp-feeds.py` (stdlib: `urllib`, `json`, `sqlite3`, `hashlib`, `tarfile`, `gzip`, `csv`): bộ thu thập theo nguồn (adapter mỗi `SRC-*`), raw cache + `feeds.db`, chuẩn hoá → bundle `feeds/current/` (manifest.json, TSV cho Bash, `feeds.db`), đổi bundle nguyên tử (`BR-FEED-051`).
- Bash đọc TSV bằng `awk -F'\t'` (DOC-SRS-QP-FEED-003 §3.4) nên `scan`/`fix` không cần Python khi đã có bundle (C-01).
- Test không gọi mạng: `tests/fixtures/feeds/` chứa phản hồi mẫu (thu gọn từ nguồn thật) và máy chủ HTTP giả lập cục bộ (`http.server`) để thử TTL, 304/ETag, 429, timeout, lỗi TLS giả lập; test tuỳ chọn `QP_TEST_ONLINE=1` gọi nguồn thật.
- Snapshot `share/php-quickpatch/feeds-snapshot.tar.gz` dựng bằng `feeds export` (`FR-FEED-SNAP-004`).
- Lịch đồng bộ: `feeds schedule install|remove` (systemd timer / cron) — chỉ thử với stub.

## 3. Công việc
1. Adapter cho SRC-001..016, SRC-017 snapshot; chính sách gọi (timeout, retry, User-Agent, giới hạn tốc độ, key tuỳ chọn `QP_NVD_API_KEY`, `QP_GITHUB_TOKEN`, `QP_WPSCAN_TOKEN`).
2. Cache TTL + đồng bộ tăng dần; độ tươi `FRESH/AGING/STALE/EXPIRED`.
3. Hợp nhất nguồn, so khớp dải phiên bản (CPE, CNA, OSV, semver Node WG), `min_patched`, backport distro.
4. Điểm rủi ro `R` + mức + xếp hạng phụ; bộ ví dụ §8.5 và ca làm tròn §8.2.1 làm test hồi quy (`NFR-MNT-002`).
5. Lệnh `feeds update|status|verify|export|import|schedule` + bí danh `sync`, `snapshot export|import`; mã thoát §6.3.
6. Bash: tra bundle thay mảng ghi cứng (`FR-CLI-COMP-002`), dòng tuổi dữ liệu, `data` trong envelope; `dependency_findings[]`, `wordpress_findings[]` theo bundle.

## 4. Tiêu chí nghiệm thu
- Test hồi quy dữ liệu v0.1 (merge-risk §6.5): bundle dựng từ fixture cho `min_patched` = 8.2.35/8.3.36/8.4.27/8.5.12, Node 22.23.4/24.22.1/26.12.1, WP 6.9.5/7.0.2.
- Điểm rủi ro khớp mọi ví dụ §8.5 và ca làm tròn §8.2.1; `qp.assess/1` ví dụ §6 (R 60/40/20/0).
- `feeds status --json` hợp lệ schema; mã thoát 0/1/2 theo độ tươi.
- Snapshot: sai SHA-256 / `SHA256SUMS` / schema → giữ bundle cũ, đúng mã ERR.
- `scan` không có Python vẫn chạy với bundle TSV.

## 5. Chưa thử được trên máy thật (dự kiến)
Timer systemd/cron thật; nguồn cần key (SRC-013); tracker distro (SRC-015) trên RHEL/Alpine thật.

## 6. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-FEED-EOL-001` | Đồng bộ vòng đời runtime | P0 | `US-FEED-02` | `AC-FEED-05`, `AC-FEED-06`, `AC-FEED-07`, bổ sung | TC-FEED-005, TC-FEED-006, TC-FEED-007, TC-FEED-101, TC-FEED-107 |
| `FR-FEED-EOL-002` | Bổ sung bản ghi vòng đời tĩnh | P0 | `US-FEED-02` | `AC-FEED-05` | TC-FEED-005 |
| `FR-FEED-EOL-003` | Đồng bộ ma trận framework/CMS ↔ PHP | P1 | `US-FEED-02` | `AC-FEED-05` | TC-FEED-005 |
| `FR-FEED-REL-001` | Đồng bộ bản phát hành PHP | P0 | `US-FEED-03`, `US-FEED-03` (FR) / `US-FEED-02` (TC) | `AC-FEED-08`, `AC-FEED-09`, `AC-FEED-10`, bổ sung | TC-FEED-008, TC-FEED-009, TC-FEED-010, TC-FEED-101 |
| `FR-FEED-REL-002` | Đồng bộ bản phát hành Node.js | P0 | `US-FEED-03` | `AC-FEED-08` | TC-FEED-008 |
| `FR-FEED-REL-003` | Đồng bộ trạng thái WordPress core | P0 | `US-FEED-03` | `AC-FEED-08` | TC-FEED-008 |
| `FR-FEED-PCVE-001` | Đồng bộ CVE PHP core | P0 | `US-FEED-04` | `AC-FEED-11`, `AC-FEED-12`, `AC-FEED-13` | TC-FEED-011, TC-FEED-012, TC-FEED-013 |
| `FR-FEED-PCVE-002` | Làm giàu alias GHSA ↔ CVE cho PHP | P1 | `US-FEED-04` | `AC-FEED-11` | TC-FEED-011 |
| `FR-FEED-PCVE-003` | Tra CVE.org khi NVD thiếu | P0 | `US-FEED-04` | `AC-FEED-13` | TC-FEED-013 |
| `FR-FEED-NCVE-001` | Đồng bộ CVE Node.js core | P0 | `US-FEED-05` | `AC-FEED-14`, `AC-FEED-15`, `AC-FEED-16` | TC-FEED-014, TC-FEED-015, TC-FEED-016 |
| `FR-FEED-WCVE-001` | Đồng bộ CVE WordPress core | P0 | `US-FEED-05` | `AC-FEED-14` | TC-FEED-014 |
| `FR-FEED-WCVE-002` | Nguồn lỗ hổng WordPress cần key | P2 | `US-FEED-17` | `AC-FEED-51`, `AC-FEED-52`, `AC-FEED-53` | TC-FEED-051, TC-FEED-052, TC-FEED-053 |
| `FR-FEED-KEV-001` | Đồng bộ CISA KEV | P0 | `US-FEED-06` | `AC-FEED-17`, `AC-FEED-18`, `AC-FEED-19` | TC-FEED-017, TC-FEED-018, TC-FEED-019 |
| `FR-FEED-OSV-001` | Tra OSV cho Composer/npm có cache | P0 | `US-FEED-07` | `AC-FEED-20`, `AC-FEED-21`, `AC-FEED-22` | TC-FEED-020, TC-FEED-021, TC-FEED-022 |
| `FR-FEED-DIST-001` | Tra advisory distro cho gói runtime | P0 | `US-FEED-08` | `AC-FEED-23`, bổ sung | TC-FEED-023, TC-SCN-104 |
| `FR-FEED-DIST-002` | Dự phòng tracker distro và changelog | P1 | `US-FEED-08` | `AC-FEED-24` | TC-FEED-024 |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | P0 | `US-FEED-01`, `US-FEED-01` (FR) / `US-FEED-02` (TC) | `AC-FEED-01`, `AC-FEED-02`, `AC-FEED-03`, `AC-FEED-04`, bổ sung | TC-FEED-001, TC-FEED-002, TC-FEED-003, TC-FEED-004, TC-FEED-103, TC-FEED-104, TC-FEED-106 |
| `FR-FEED-AGE-001` | Gắn tuổi dữ liệu vào mọi kết quả | P0 | `US-FEED-10` | `AC-FEED-29`, `AC-FEED-30`, `AC-FEED-31`, bổ sung | TC-FEED-029, TC-FEED-030, TC-FEED-031, TC-FEED-102 |
| `FR-FEED-NORM-001` | Chuẩn hoá và khử trùng lặp advisory | P0 | `US-FEED-09` | `AC-FEED-26`, `AC-FEED-28` | TC-FEED-026, TC-FEED-028 |
| `FR-FEED-NORM-002` | Tính phiên bản vá tối thiểu | P0 | `US-FEED-09`, `US-FEED-09` (FR) / `US-ASMT-01` (TC) | bổ sung, `AC-FEED-26`, `AC-FEED-27` | TC-ASMT-101, TC-FEED-026, TC-FEED-027 |
| `FR-FEED-NORM-003` | Xác định trạng thái vá trong gói distro | P0 | `US-FEED-08`, `US-FEED-08` (FR) / `US-SCN-02` (TC) | `AC-FEED-23`, `AC-FEED-24`, `AC-FEED-25`, bổ sung | TC-FEED-023, TC-FEED-024, TC-FEED-025, TC-SCN-103, TC-SCN-104, TC-SCN-105 |
| `FR-FEED-CACH-001` | Lưu phản hồi gốc kèm meta | P0 | `US-FEED-11`, `US-FEED-11` (FR) / `US-FEED-02` (TC) | `AC-FEED-32`, `AC-FEED-34`, bổ sung | TC-FEED-032, TC-FEED-034, TC-FEED-105, TC-FEED-106 |
| `FR-FEED-CACH-002` | Dựng và thay bundle nguyên tử | P0 | `US-FEED-11` | `AC-FEED-32`, `AC-FEED-33` | TC-FEED-032, TC-FEED-033 |
| `FR-FEED-CACH-003` | Dọn dẹp theo giới hạn dung lượng | P1 | `US-FEED-11` | `AC-FEED-34` | TC-FEED-034 |
| `FR-FEED-SNAP-001` | Dùng snapshot đóng gói | P0 | `US-FEED-12`, `US-FEED-12` (FR) / `US-FEED-10` (TC) | `AC-FEED-35`, `AC-FEED-36`, `AC-FEED-37`, bổ sung | TC-FEED-035, TC-FEED-036, TC-FEED-037, TC-FEED-102 |
| `FR-FEED-SNAP-002` | Xuất snapshot | P0 | `US-FEED-13` | `AC-FEED-38` | TC-FEED-038 |
| `FR-FEED-SNAP-003` | Nhập snapshot | P0 | `US-FEED-13` | `AC-FEED-39`, `AC-FEED-40`, `AC-FEED-41` | TC-FEED-039, TC-FEED-040, TC-FEED-041 |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | P0 | `US-FEED-14` | `AC-FEED-42`, `AC-FEED-43`, `AC-FEED-44` | TC-FEED-042, TC-FEED-043, TC-FEED-044 |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | P1 | `US-FEED-15` | `AC-FEED-45`, `AC-FEED-46`, `AC-FEED-47` | TC-FEED-045, TC-FEED-046, TC-FEED-047 |
| `FR-FEED-CMD-001` | Lệnh `feeds update` (bí danh `sync`) | P0 | `US-FEED-01` | `AC-FEED-01`, `AC-FEED-02`, `AC-FEED-03`, `AC-FEED-04`, bổ sung | TC-FEED-001, TC-FEED-002, TC-FEED-003, TC-FEED-004, TC-FEED-104 |
| `FR-FEED-CMD-002` | Lệnh `feeds status` | P0 | `US-FEED-16` | `AC-FEED-48`, `AC-FEED-50` | TC-FEED-048, TC-FEED-050 |
| `FR-FEED-CMD-003` | Lệnh `feeds verify` | P1 | `US-FEED-16` | `AC-FEED-49` | TC-FEED-049 |
| `FR-FEED-CMD-004` | Lệnh `feeds export` (bí danh `snapshot export`) | P0 | `US-FEED-13`, `US-FEED-13` (FR) / `US-FEED-01` (TC) | `AC-FEED-38`, bổ sung | TC-FEED-038, TC-FEED-104 |
| `FR-FEED-CMD-005` | Lệnh `feeds import` (bí danh `snapshot import`) | P0 | `US-FEED-13` | `AC-FEED-39`, `AC-FEED-40`, `AC-FEED-41` | TC-FEED-039, TC-FEED-040, TC-FEED-041 |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | P1 | `US-FEED-15` | `AC-FEED-45`, `AC-FEED-46`, `AC-FEED-47` | TC-FEED-045, TC-FEED-046, TC-FEED-047 |
| `FR-CLI-COMP-002` | Thay mảng ghi cứng bằng bundle | P0 | `US-CLI-04` | `AC-CLI-10`, `AC-CLI-11`, `AC-CLI-12` | TC-CLI-010, TC-CLI-011, TC-CLI-012 |
| `FR-ASMT-RISK-001` | Tính điểm rủi ro runtime | P0 | `US-ASMT-01` | `AC-ASMT-01`, `AC-ASMT-02` | TC-ASMT-001, TC-ASMT-002 |
| `FR-ASMT-RISK-002` | So sánh điểm hiện tại và ứng viên | P0 | `US-ASMT-03` | `AC-ASMT-08`, `AC-ASMT-10` | TC-ASMT-008, TC-ASMT-010 |
| `FR-ASMT-DEP-001` | Đánh giá dependency Composer/npm | P0 | `US-ASMT-05` | `AC-ASMT-14`, `AC-ASMT-15`, `AC-ASMT-16` | TC-ASMT-014, TC-ASMT-015, TC-ASMT-016 |
| `FR-ASMT-DEP-002` | Đánh giá WordPress core | P0 | `US-ASMT-06` | `AC-ASMT-17`, `AC-ASMT-18`, `AC-ASMT-19` | TC-ASMT-017, TC-ASMT-018, TC-ASMT-019 |

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).
