# Kế hoạch triển khai Phase 1 — php-quickpatch v2 (chỉ mục)

Ngày lập: 2026-10-24. Căn cứ: `plans/phase1-handoff.md` (bàn giao 2026-10-23), bộ thiết kế `docs/php-quickpatch/`.
Nguồn sự thật khi tài liệu mâu thuẫn: FR/BR/ERR trong `docs/php-quickpatch/srs/` (`BR-DATA-004`). Mâu thuẫn và cách xử lý ghi ở [phase1-conflicts.md](phase1-conflicts.md).

## 1. Quyết định áp dụng

| Chủ đề | Quyết định | Nguồn |
| :--- | :--- | :--- |
| Ngôn ngữ | CLI Bash ≥ 4.3; `qp-feeds.py` và console Python 3 thư viện chuẩn, 0 gói pip, 0 file JS/CSS từ CDN | Handoff §2, PO duyệt 2026-10-23 |
| Câu hỏi mở `Q-01..Q-09`, `Q-SRS-01` | Áp dụng đề xuất của SRS (spec §4.4): HC theo DOC-SRS-QP-ENV-002 §2; Rector P2 chỉ chạy trên bản sao; kho bên thứ ba ở mức `SEMI`; Python ≥ 3.6; `yarn.lock`/`pnpm-lock.yaml` chỉ cảnh báo; lịch chỉ chạy `feeds update`; chu kỳ 6 giờ; xếp hạng `BR-ASMT-004`; cổng `serve` 17321 | PO, 2026-10-24 |
| Phạm vi | Chỉ 159 FR Phase 1; 9 FR `FR-FLT-*` (Phase 2) không làm | PO |
| `Q-SRS-02..09` | Không thuộc danh sách PO đã chốt; dùng đề xuất SRS làm mặc định và ghi ở conflicts (chưa có quyết định ngược lại) | phase1-conflicts.md |
| `CR-FR-01..08` (chờ PO duyệt trong FR §15.2) | Triển khai theo nội dung FR (FR là nguồn sự thật); `CR-FR-02` đã thực hiện ở v0.1.1 | phase1-conflicts.md mục C-03 |

## 2. Kiến trúc mã (spec §2.1)

```text
php-quickpatch.sh                      # CLI Bash: scan/fix/rollback/migrate (không cần Python),
                                       # chuyển feeds/assess/plan/report/audit/serve sang Python
share/php-quickpatch/
├── qp-feeds.py                        # feeds, assess, plan, report, audit (Python ≥ 3.6, stdlib)
├── qplib/                             # module Python dùng chung (state dir, envelope, audit, semver…)
├── console/qp-console.py + static/    # web console (M6)
├── catalog/                           # scenarios.json, checklists.json, playbooks.json, bc_rules.json,
│                                      # mitigations.json, framework_php.tsv, catalog.json, SHA256SUMS
├── schemas/qp.<lệnh>.v1.schema.json   # JSON Schema 2020-12 (FR-CLI-JSON-002)
└── feeds-snapshot.tar.gz              # snapshot offline SRC-017 (M2)
tests/
├── run.sh                             # chạy toàn bộ
├── bash/test_*.sh                     # test Bash (không framework ngoài)
├── python/test_*.py                   # python3 -m unittest
└── fixtures/                          # dữ liệu nguồn giả lập, cây thư mục site, stub lệnh hệ thống
```

Thư mục `share/php-quickpatch` được tìm theo thứ tự: `<thư mục script>/share/php-quickpatch`, rồi `/usr/local/share/php-quickpatch` (DOC-SRS-QP-FEED-003 §2).

## 3. Các mốc

| Mốc | File | Nội dung | Số FR | AC/TC (RTM) |
| :--- | :--- | :--- | ---: | ---: |
| M1 | [phase1-m1-cli-core.md](phase1-m1-cli-core.md) | Khung repo, envelope `--json` + `schema_version`, JSON Schema, test harness, tương thích v0.1, scan/fix/rollback xuất JSON, audit chuỗi hash, khoá đọc/ghi | 26 | 66 |
| M2 | [phase1-m2-feeds.md](phase1-m2-feeds.md) | `qp-feeds.py`: 17 nguồn, cache SQLite có TTL, đồng bộ tăng dần, hợp nhất, `min_patched`, backport, điểm rủi ro, snapshot, lệnh `feeds`; thay mảng ghi cứng; finding dependency/WordPress | 40 | 106 |
| M3 | [phase1-m3-catalog-assess-plan.md](phase1-m3-catalog-assess-plan.md) | Catalog kịch bản/checklist, nhận diện môi trường + playbook, kiểm kê site, `assess`, `plan`, mitigation theo luật | 25 | 100 |
| M4 | [phase1-m4-compat.md](phase1-m4-compat.md) | Quét tương thích: luật BC tĩnh, PHPCompatibility, lint, Composer, Packagist, npm, ini, extension, framework, loader, kết luận, Rector | 14 | 41 |
| M5 | [phase1-m5-migrate.md](phase1-m5-migrate.md) | `migrate`: tiền điều kiện, cài song song, pool/ini/extension, chuyển site, health check `HC-C0..C9`, tự rollback, `rollback-site`, `ack`, Node.js, Compose, gỡ runtime cũ | 22 | 74 |
| M6 | [phase1-m6-console.md](phase1-m6-console.md) | `qp-console.py`: `serve`, token, phiên, Host/CSRF/CSP, danh sách trắng, job runner + `flock`, SSE, 11 màn hình, API Phase 1 | 29 | 92 |
| M7 | [phase1-m7-release.md](phase1-m7-release.md) | Báo cáo, `report`/`audit`, test đầu–cuối, đối chiếu RTM, tài liệu, phát hành 2.0.0 | 3 | 9 |
| | | **Tổng Phase 1** | **159** | **488** |

Phân bổ FR → mốc do script sinh từ `srs/functional-requirements.md` và `test/rtm.md` (kiểm 159/159 FR Phase 1, không trùng, không sót). Bảng chi tiết FR → US → AC → TC nằm trong từng file mốc.

## 4. Quy ước chung cho mọi mốc

- **Định nghĩa xong (DoD)** của 1 mốc:
  1. Mỗi FR của mốc có ít nhất 1 test tự động chạy được trong container (Bash hoặc `python3 -m unittest`), đặt tên/ghi chú theo `TC-*` tương ứng khi có.
  2. `tests/run.sh` xanh; `shellcheck -S warning` sạch cho mọi file Bash; `python3 -m py_compile` sạch.
  3. Không hồi quy test của mốc trước và của v0.1.1.
  4. Cập nhật bảng trạng thái FR trong file mốc (`Xong` / `Một phần` / `Chưa thử trên máy thật`), cập nhật mâu thuẫn mới vào conflicts.
  5. 1 commit riêng cho mốc, push lên nhánh làm việc.
  6. Báo cáo PO: việc đã xong, test đã chạy và kết quả, phần chưa thử trên máy thật (systemd, panel, Docker).
- **Giới hạn môi trường thử**: container không có systemd đang chạy, không có Docker daemon, không có panel. Phần đó thử bằng stub lệnh (`tests/fixtures/stubs/`) và cây thư mục giả lập; ghi rõ "chưa thử trên máy thật".
- **Không dùng `/opt/node22`** để thử nâng Node (Claude Code đang chạy bằng nó); chép ra prefix riêng.
- **Mạng**: test mặc định không gọi mạng (dữ liệu nguồn giả lập trong `tests/fixtures/feeds/`); có thêm test tuỳ chọn gọi nguồn thật khi đặt `QP_TEST_ONLINE=1`.
- **Bảo mật**: không commit secret; không ghi tên model AI vào commit, mã, tài liệu.

## 5. Theo dõi tiến độ

| Mốc | Trạng thái | Commit | Ghi chú |
| :--- | :--- | :--- | :--- |
| Việc 1 (v0.1.1) | Xong | `5919d7e` | 254 kiểm tra hồi quy, shellcheck sạch |
| M1 | Xong | `5b0a0ed` | 26 FR: 21 xong, 5 một phần (phần còn lại thuộc M2/M3/M5) |
| M2 | Xong | `3fe9502` | 40 FR: 31 xong, 9 một phần (assess ở M3; GHSA có token, Wordfence, tracker distro thật; snapshot đóng gói ở M7) |
| M3 | Xong | (commit M3) | 25 FR: 15 xong, 9 một phần, 1 chưa (`FR-PLAN-DEP-001` cần M4); phần còn lại thuộc M4 (quét tương thích), M5 (baseline, chuyển site), M6 (job) |
| M4 | Chưa bắt đầu | | |
| M5 | Chưa bắt đầu | | |
| M6 | Chưa bắt đầu | | |
| M7 | Chưa bắt đầu | | |
