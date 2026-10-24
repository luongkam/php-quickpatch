# M3 — Catalog kịch bản, nhận diện môi trường, `assess`, `plan`

Mục tiêu: chuyển 28 kịch bản `SCN-*` và checklist `CHK-*` từ `version-scenarios-*.md` sang `share/php-quickpatch/catalog/` (JSON/TSV, `SHA256SUMS`, `catalog_version`); gán kịch bản cho runtime; nhận diện môi trường + playbook và kiểm kê site (Debian/Ubuntu + Nginx/Apache-FPM trước, panel nhận diện ở mức đọc); lệnh `assess` (hiện tại so với ứng viên, KEV, support, LTS, EOL, `R`) và `plan` (chọn đích, sinh kế hoạch, checklist có trạng thái, vòng đời, hạn duyệt); mitigation theo `mitigations.json`.

## 1. Tài liệu chính
`srs/version-scenarios-common.md`, `-php.md`, `-php-8x.md`, `-node.md`; `srs/environment-playbooks.md` §2.3, §3, §4; `-os.md`, `-panels.md` (phần nhận diện); `srs/states.md` (kế hoạch, mục checklist); `srs/erd-console-db.md`/`erd-feeds-files.md` (tệp kế hoạch); `api/api-spec-cli-json.md` §5–§7; `api/api-spec-plans.md`.

## 2. Thiết kế
- Catalog sinh bằng script `tools/build-catalog.py` từ bảng Markdown của các tài liệu kịch bản (để cập nhật catalog không cần sửa tay JSON), kết quả commit vào `share/php-quickpatch/catalog/`.
- `assess`, `plan` ở Python (`qp-feeds.py`), đọc `state/last-scan.json` (chạy `scan --json` khi quá 24 giờ hoặc chưa có), bundle `feeds/current/` và catalog.
- Kế hoạch lưu `STATE_DIR/plans/<plan_id>/{plan.json, items.json, events.jsonl}` ghi tạm + `rename`; máy trạng thái `T-PLN-*`, `T-CHK-*` của states.md.
- `scan` (Bash) bổ sung `environment`, `sites[]`, `scan_fingerprint`, `ranking[]`, `plan_deadlines[]`.

## 3. Tiêu chí nghiệm thu
- Catalog: 28 kịch bản, mọi `CHK-*` của tài liệu có trong `checklists.json`; `SHA256SUMS` sai → giữ catalog cũ (`ERR-FEED-422-02`).
- Gán kịch bản đúng cho bảng phiên bản mẫu (PHP 4.4, 5.2–5.6, "6.0", 7.0–7.4, 8.0–8.5, pre-release; Node ≤ 20, số lẻ, 22, 24, 26, nvm/tarball/nodesource).
- `assess` ví dụ §6 của DOC-API-QP-005 cho đúng `candidates[]`, `comparison.rows[]` (`R`, `delta_R`).
- `plan`: chuyển trạng thái hợp lệ/không hợp lệ theo `T-PLN-*`, `T-CHK-*`; lý do/bằng chứng sai độ dài → `ERR-PLAN-422-01`; `stale` theo 4 điều kiện `BR-PLAN-006`.
- Nhận diện môi trường trên cây `/etc` giả lập (Nginx, Apache-FPM, `mod_php`, cPanel/Plesk/aaPanel/CyberPanel/DirectAdmin ở mức file đánh dấu).

## 4. Chưa thử được trên máy thật (dự kiến)
Nhận diện panel thật (lệnh `whmapi1`, `plesk bin`, `selectorctl`…), `apt-cache policy`/`dnf list available` trên kho thật cho `installable`.

## 5. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-SCN-CLS-001` | Gán kịch bản cho runtime PHP | P0 | `US-SCN-01`, `US-SCN-01` (FR) / `US-SCN-02` (TC) | `AC-SCN-01`, `AC-SCN-03`, `AC-SCN-04`, bổ sung | TC-SCN-001, TC-SCN-003, TC-SCN-004, TC-SCN-101, TC-SCN-103, TC-SCN-106 |
| `FR-SCN-CLS-002` | Gán kịch bản cho runtime Node.js | P0 | `US-SCN-01`, `US-SCN-01` (FR) / `US-SCN-02` (TC) | `AC-SCN-02`, `AC-SCN-04`, bổ sung | TC-SCN-002, TC-SCN-004, TC-SCN-107, TC-SCN-109, TC-SCN-110 |
| `FR-SCN-LIFE-001` | Tính trạng thái hỗ trợ và mức ưu tiên động | P0 | `US-SCN-02`, `US-SCN-02` (FR) / `US-FEED-08` (TC) | `AC-SCN-05`, `AC-SCN-06`, `AC-SCN-07`, bổ sung | TC-SCN-005, TC-SCN-006, TC-SCN-007, TC-SCN-101, TC-SCN-103, TC-SCN-104, TC-SCN-105, TC-SCN-107, TC-SCN-109, TC-SCN-110 |
| `FR-SCN-CAT-001` | Nạp catalog kịch bản/checklist/playbook | P0 | `US-SCN-03` | `AC-SCN-08`, `AC-SCN-09`, `AC-SCN-10` | TC-SCN-008, TC-SCN-009, TC-SCN-010 |
| `FR-SCN-CHK-001` | Lắp checklist hiệu lực | P0 | `US-SCN-04` | `AC-SCN-11`, `AC-SCN-12`, `AC-SCN-13`, bổ sung | TC-SCN-011, TC-SCN-012, TC-SCN-013, TC-SCN-102, TC-SCN-108 |
| `FR-SCN-LOCK-001` | Khoá tự động hoá với phiên bản bất thường | P0 | `US-SCN-01` | `AC-SCN-03`, `AC-SCN-04` | TC-SCN-003, TC-SCN-004 |
| `FR-SCN-ENV-001` | Áp kịch bản môi trường đặc biệt | P0 | `US-SCN-05` | `AC-SCN-14`, `AC-SCN-15`, `AC-SCN-16` | TC-SCN-014, TC-SCN-015, TC-SCN-016 |
| `FR-PLAN-TGT-001` | Chọn phiên bản đích | P0 | `US-PLAN-01`, `US-PLAN-01` (FR) / `US-SCN-04` (TC) | `AC-PLAN-01`, `AC-PLAN-02`, `AC-PLAN-03`, `AC-PLAN-04`, bổ sung | TC-PLAN-001, TC-PLAN-002, TC-PLAN-003, TC-PLAN-004, TC-SCN-102, TC-SCN-108 |
| `FR-PLAN-GEN-001` | Sinh kế hoạch nâng cấp | P0 | `US-PLAN-02`, `US-PLAN-02` (FR) / `US-SCN-04` (TC) | `AC-PLAN-05`, `AC-PLAN-06`, `AC-PLAN-07`, bổ sung | TC-PLAN-005, TC-PLAN-006, TC-PLAN-007, TC-SCN-102, TC-SCN-108 |
| `FR-PLAN-GEN-002` | Sắp thứ tự chuyển site và chọn site canary | P0 | `US-PLAN-03` | `AC-PLAN-08`, `AC-PLAN-09`, `AC-PLAN-10` | TC-PLAN-008, TC-PLAN-009, TC-PLAN-010 |
| `FR-PLAN-DEP-001` | Lập danh sách thư viện và dependency phải nâng | P0 | `US-PLAN-04` | `AC-PLAN-11`, `AC-PLAN-12`, `AC-PLAN-13` | TC-PLAN-011, TC-PLAN-012, TC-PLAN-013 |
| `FR-PLAN-CHK-001` | Quản lý trạng thái mục checklist | P0 | `US-PLAN-05`, `US-PLAN-05` (FR) / `US-UPG-13` (TC) | `AC-PLAN-14`, `AC-PLAN-15`, `AC-PLAN-16`, bổ sung | TC-PLAN-014, TC-PLAN-015, TC-PLAN-016, TC-UPG-107 |
| `FR-PLAN-CHK-002` | Chạy mục checklist tự động/bán tự động | P0 | `US-PLAN-06`, `US-PLAN-06` (FR) / `US-CMPT-06` (TC) | bổ sung, `AC-PLAN-17`, `AC-PLAN-18`, `AC-PLAN-19` | TC-CMPT-102, TC-PLAN-017, TC-PLAN-018, TC-PLAN-019 |
| `FR-PLAN-STS-001` | Quản lý vòng đời kế hoạch | P0 | `US-PLAN-07` | `AC-PLAN-20`, `AC-PLAN-21`, `AC-PLAN-22`, `AC-PLAN-23` | TC-PLAN-020, TC-PLAN-021, TC-PLAN-022, TC-PLAN-023 |
| `FR-PLAN-DL-001` | Theo dõi hạn duyệt kế hoạch | P0 | `US-PLAN-08`, `US-PLAN-08` (FR) / `US-FEED-08` (TC), `US-PLAN-08` (FR) / `US-SCN-02` (TC) | `AC-PLAN-24`, `AC-PLAN-25`, `AC-PLAN-26`, bổ sung | TC-PLAN-024, TC-PLAN-025, TC-PLAN-026, TC-SCN-104, TC-SCN-109 |
| `FR-ASMT-CUR-001` | Đánh giá runtime hiện tại | P0 | `US-ASMT-01` | `AC-ASMT-01`, `AC-ASMT-02`, `AC-ASMT-03`, `AC-ASMT-04`, bổ sung | TC-ASMT-001, TC-ASMT-002, TC-ASMT-003, TC-ASMT-004, TC-ASMT-101 |
| `FR-ASMT-CAND-001` | Liệt kê phiên bản ứng viên | P0 | `US-ASMT-02`, `US-ASMT-02` (FR) / `US-SCN-01` (TC), `US-ASMT-02` (FR) / `US-SCN-02` (TC) | `AC-ASMT-05`, `AC-ASMT-06`, `AC-ASMT-07`, bổ sung | TC-ASMT-005, TC-ASMT-006, TC-ASMT-007, TC-SCN-101, TC-SCN-106, TC-SCN-107, TC-SCN-110 |
| `FR-ASMT-CAND-002` | Xác định khả năng cài của ứng viên | P0 | `US-ASMT-02` | `AC-ASMT-05` | TC-ASMT-005 |
| `FR-ASMT-CMP-001` | So sánh hiện tại với ứng viên | P0 | `US-ASMT-03` | `AC-ASMT-08`, `AC-ASMT-09` | TC-ASMT-008, TC-ASMT-009 |
| `FR-ASMT-RANK-001` | Xếp hạng ưu tiên xử lý | P0 | `US-ASMT-04` | `AC-ASMT-11`, `AC-ASMT-12`, `AC-ASMT-13` | TC-ASMT-011, TC-ASMT-012, TC-ASMT-013 |
| `FR-CLI-CMD-001` | Cung cấp lệnh `assess` | P0 | `US-CLI-05` | `AC-CLI-13`, `AC-CLI-14`, `AC-CLI-15` | TC-CLI-013, TC-CLI-014, TC-CLI-015 |
| `FR-CLI-CMD-002` | Cung cấp lệnh `plan` | P0 | `US-CLI-06` | `AC-CLI-16`, `AC-CLI-17`, `AC-CLI-18` | TC-CLI-016, TC-CLI-017, TC-CLI-018 |
| `FR-SCAN-ENV-001` | Nhận diện môi trường và chọn playbook | P0 | `US-SCAN-01` | `AC-SCAN-01`, `AC-SCAN-02` | TC-SCAN-001, TC-SCAN-002 |
| `FR-SCAN-MAP-001` | Kiểm kê site → runtime | P0 | `US-SCAN-01` | `AC-SCAN-01`, `AC-SCAN-03` | TC-SCAN-001, TC-SCAN-003 |
| `FR-PTCH-MIT-001` | Ghi mitigation ini tạm thời | P0 | `US-PTCH-02`, `US-PTCH-02` (FR) / `US-SCN-01` (TC) | `AC-PTCH-05`, `AC-PTCH-06`, `AC-PTCH-07`, bổ sung | TC-PTCH-005, TC-PTCH-006, TC-PTCH-007, TC-SCN-106 |

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).
