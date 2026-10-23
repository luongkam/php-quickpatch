---
id: DOC-SRS-QP-FLOW-001
title: Sơ đồ tuần tự (Sequence Diagram) — php-quickpatch v2 — quy ước và luồng 1–4
version: 1.0.1
phase: Specification
domain: Security Patch Management
tags: [srs, sequence-diagram, mermaid, flows, feeds, snapshot, scan, assess, plan, checklist, patch, job, sse, openba]
depends_on:
  - DOC-BRS-QP-001
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-NFR-001
  - DOC-SRS-QP-SCN-000
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-003
  - DOC-SRS-QP-ENV-001
related_diagrams:
  - DIAG-SEQ-QP-FEED-002
  - DIAG-SEQ-QP-FEED-003
  - DIAG-SEQ-QP-SCAN-001
  - DIAG-SEQ-QP-PLAN-001
  - DIAG-SEQ-QP-PTCH-001
  - DIAG-SEQ-QP-UPG-001
  - DIAG-SEQ-QP-UPG-002
  - DIAG-SEQ-QP-UPG-003
  - DIAG-SEQ-QP-AUTH-002
  - DIAG-SEQ-QP-FLT-001
author: BA Agent
last_updated: 2026-10-22
---

# Sơ đồ tuần tự (Sequence Diagram) — php-quickpatch v2

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo bộ sơ đồ tuần tự theo `skills/sequence` (template 15, rules 01, 10): quy ước participant và cổng kiểm tra chung; luồng 1–4 trong tài liệu này; luồng 5–6 tách sang [flows-upgrade.md](flows-upgrade.md), luồng 7–8 tách sang [flows-console-fleet.md](flows-console-fleet.md) do giới hạn 800 dòng; 10 sơ đồ Mermaid `sequenceDiagram` có `autonumber`, đã kiểm cú pháp bằng `mermaid.parse` (Mermaid 11.4.1) |
| 1.0.1 | 2026-10-22 | BA Agent | Sửa theo review: (1) vẽ lại DIAG-SEQ-QP-FEED-003 theo `BR-CON-005` 1.0.1 — 2 bước dry-run (job `read`, `feeds import … --dry-run`, 0 thay đổi `feeds/`) → xác nhận trên SCR-011 (tải lại file, cổng D so SHA-256 nội dung và `force` với job dry-run, thiếu hoặc lệch → 428 `ERR-JOB-428-01`), thêm nhánh `ERR-CON-415-01`, `ERR-FEED-507-01`, `ERR-FEED-423-01`; §2.2 thêm ràng buộc, ghi chú §2.2 và §6.2 mục 1 ghi "đã quyết"; §1.7 thêm `UC-CON-003`, `FR-CON-SAFE-001`, `FR-CLI-SAFE-001`, `GET /api/v1/jobs/{job_id}`; (2) bỏ nhãn "mã đề xuất mới" của `ERR-JOB-429-02` (DIAG-SEQ-QP-PTCH-001) và §1.1; §6.2 mục 4–6 ghi "Đã xử lý ở DOC-SRS-QP-ERR-001 v1.0.1"; thay bảng mã lỗi §6.3 bằng liên kết error-matrix.md §3.3, §3.11, §3.13; (3) §6.1 đếm lại DIAG-SEQ-QP-FEED-003 (46 thông điệp, 15 mã ERR) và độ phủ 111/129 mã của error-matrix.md 1.1.0; §6.4 thêm nguồn; 5/5 sơ đồ của file qua `mermaid.parse` (Mermaid 11.4.1) |

## 1. Giới thiệu

### 1.1 Mục đích
Mô tả **ai gọi ai, theo thứ tự nào** cho 8 luồng nghiệp vụ chính của php-quickpatch v2, làm đầu vào cho Dev (cài đặt `php-quickpatch.sh`, `qp-feeds.py`, `qp-console.py`), QA (thiết kế test case theo từng nhánh `alt`/`break`) và kỹ sư bảo mật (rà soát cổng kiểm tra của console). Mọi mã `FR-*`, `BR-*`, `ERR-*`, `UC-*`, `SCR-*`, `NFR-*` và đường dẫn API dùng trong tài liệu là mã đã định nghĩa ở SRS ([spec.md](spec.md), [functional-requirements.md](functional-requirements.md), [business-rules.md](business-rules.md), [error-matrix.md](error-matrix.md), [nfr.md](nfr.md)) và các phụ lục. 3 mã lỗi do bản 1.0.0 của tài liệu này đề xuất (`ERR-JOB-429-02`, `ERR-UPG-409-03`, `ERR-FLT-422-03`) đã được định nghĩa chuẩn ở [error-matrix.md](error-matrix.md) từ bản 1.0.1 (§6.3).

### 1.2 Phạm vi
| Trong phạm vi | Ngoài phạm vi (tài liệu khác đã có hoặc không thuộc nhiệm vụ) |
| :--- | :--- |
| 8 luồng, 10 sơ đồ (§1.7); Phase 1 (cục bộ) và Phase 2 (máy trung tâm qua SSH, chỉ đặc tả); 21/35 use case của SRS | Đăng nhập rút gọn DIAG-SEQ-QP-AUTH-001 ([spec.md §4.1.3](spec.md)) — được thay bằng bản đầy đủ DIAG-SEQ-QP-AUTH-002; một lần `feeds update` mức CLI DIAG-SEQ-QP-FEED-001 ([data-sources-cache-cli.md §5.1](data-sources-cache-cli.md)) — được mở rộng ở DIAG-SEQ-QP-FEED-002; 14 use case chưa có sơ đồ riêng: `UC-FEED-005`, `UC-ASMT-002` (tra OSV có trong luồng 2, chưa vẽ SCR-005), `UC-PTCH-002`, `UC-PTCH-003`, `UC-UPG-003`, `UC-UPG-005`, `UC-UPG-006`, `UC-UPG-007`, `UC-JOB-003`, `UC-CLI-001`, `UC-RPT-001`, `UC-RPT-002`, `UC-FLT-001`, `UC-FLT-004` |

### 1.3 Bộ tài liệu (tách file do giới hạn 800 dòng)
| File | Mã tài liệu | Nội dung |
| :--- | :--- | :--- |
| `flows.md` (tài liệu này) | DOC-SRS-QP-FLOW-001 | Quy ước, cổng kiểm tra chung, luồng 1 (đồng bộ feed + snapshot), 2 (scan + assess), 3 (chọn đích + kế hoạch), 4 (vá cùng nhánh + SSE), ma trận truy vết tổng hợp, phát hiện và câu hỏi mở |
| [flows-upgrade.md](flows-upgrade.md) | DOC-SRS-QP-FLOW-002 | Luồng 5 (nâng major: cài song song → quét tương thích → nâng dependency → chuyển 1 site → health check → tự rollback), luồng 6 (rollback thủ công 1 lệnh) |
| [flows-console-fleet.md](flows-console-fleet.md) | DOC-SRS-QP-FLOW-003 | Luồng 7 (`serve` + token + chặn Host/CSRF), luồng 8 (Phase 2: máy trung tâm chạy CLI từ xa qua SSH) |

### 1.4 Participant
| Alias | Participant | Thành phần thực tế | Ghi chú |
| :--- | :--- | :--- | :--- |
| `Op` | Operator | Người vận hành `PER-01`, `PER-02`, `PER-03` (Phase 2: vai trò Operator/Admin theo `BR-FLT-008`); `SYS-01` khi chạy theo lịch | Actor |
| `BR` | Browser | Trình duyệt chạy JS của console qua SSH tunnel `ssh -N -L 17321:127.0.0.1:17321` | `EventSource` cho SSE |
| `CON` | Console (Python) | `qp-console.py`, Python ≥ 3.6 thư viện chuẩn, chỉ bind `127.0.0.1` (`BR-CON-001`); Phase 2: console máy trung tâm | Gọi CLI bằng `subprocess.Popen(argv, shell=False)` (`FR-CON-SAFE-003`) |
| `CLI` | CLI (Bash) | `php-quickpatch.sh` (Bash ≥ 4.3) và `qp-feeds.py` do CLI gọi (chuẩn hoá feed, điểm rủi ro, kế hoạch) | Một đường thực thi duy nhất cho mọi thay đổi hệ thống (`C-SRS-05`) |
| `SRC` | Feed sources | Nguồn online `SRC-001..016` qua HTTPS (TLS ≥ 1.2), gồm Packagist/npm registry khi lập kế hoạch (`BR-DATA-003`) | `SRC-017` = snapshot cục bộ, vẽ trong `FS` |
| `PKG` | Package manager / Panel | `apt-get`, `dnf`/`yum`, `apk`, API/CLI panel (`whmapi1`, `selectorctl`, `plesk bin`, `cyberpanel`…), Docker | Lệnh theo playbook `PB-000..018` |
| `WEB` | Web server / PHP-FPM | Nginx, Apache, LiteSpeed, dịch vụ `php-fpm` (`$OLD`, `$NEW`), systemd/pm2 cho Node.js | Kiểm cú pháp trước reload (`BR-ENV-005`) |
| `SITE` | Site | Ứng dụng PHP/Node.js của khách hàng phía sau `WEB` | Chỉ nhận `GET` khi health check (`BR-HC-002`) |
| `DB` | SQLite | `feeds/current/feeds.db` (console mở chỉ đọc `file:…?mode=ro`); Phase 2: `central.db` của máy trung tâm | — |
| `FS` | STATE_DIR (tệp) | `STATE_DIR` (`feeds/`, `state/`, `plans/`, `jobs/`, `audit/`, `backups/`, `switches/`, `console/`) | **Participant bổ sung**: SRS lưu job, kế hoạch, audit, manifest dưới dạng tệp ([spec.md §2.1](spec.md)), không lưu trong SQLite; tách riêng để sơ đồ không gán sai nơi lưu trữ |

### 1.5 Quy ước ký hiệu
| Ký hiệu | Ý nghĩa |
| :--- | :--- |
| `autonumber` | Đánh số bước; test case dẫn chiếu `<mã sơ đồ>#<số bước>` |
| `->>` / `-->>` | Lời gọi / phản hồi |
| `alt … else … end` | Rẽ nhánh thành công/lỗi; nhánh lỗi ghi mã `ERR-*` |
| `break … end` | Nhánh lỗi **kết thúc** luồng tại điểm đó (tương đương `else Lỗi` của template 15, dùng để tránh lồng quá sâu) |
| `opt`, `loop`, `par` | Bước tuỳ điều kiện, lặp, song song |
| Mã thoát CLI | 0 = thành công/không còn vấn đề, 1 = còn vấn đề hoặc thành công có cảnh báo, 2 = lỗi tham số/runtime/khoá (`BR-CLI-004`) |
| Mã HTTP | Theo cột HTTP của mã `ERR-*`; body theo rules/10 `{success, data, error{code, http, message, localization_key, details}, meta, timestamp}` (`FR-CON-API-001`) |
| `{job_id}`, `{site_id}`… | Tham số đường dẫn; giá trị thật theo regex `BR-CON-008` |

### 1.6 Cổng kiểm tra dùng chung
Để không lặp lại trong từng sơ đồ, các bước sau được vẽ đầy đủ một lần ở DIAG-SEQ-QP-AUTH-002 ([flows-console-fleet.md §2](flows-console-fleet.md)) và DIAG-SEQ-QP-PTCH-001 (§5), các sơ đồ khác vẽ rút gọn thành 1 bước kèm mã lỗi chính.

| Mã cổng | Nội dung | Thứ tự | Mã lỗi |
| :--- | :--- | :---: | :--- |
| G1 | Header `Host` thuộc `127.0.0.1:<port>`, `localhost:<port>` hoặc cổng `--allow-local-port` (`BR-CON-003`); kiểm trước định tuyến, áp cho cả tài nguyên tĩnh và SSE | 1 | `ERR-CON-400-01`, `ERR-CON-421-01` |
| G2 | Kích thước và phương thức: body ≤ 64 KiB (snapshot ≤ 20 MiB), header ≤ 8 KiB, phương thức hỗ trợ (`BR-CON-009`) | 2 | `ERR-CON-413-01`, `ERR-CON-405-01`, `ERR-CON-404-01` |
| G3 | Xác thực cookie `qp_session` hoặc `Authorization: Bearer` (`BR-AUTH-004`, `BR-AUTH-005`) | 3 | `ERR-AUTH-401-01`, `ERR-AUTH-401-02` |
| G4 | Request ghi bằng cookie: `X-QP-CSRF`, `Origin`, `Content-Type: application/json` (`BR-CON-004`) | 4 | `ERR-AUTH-403-01`, `ERR-AUTH-403-02`, `ERR-CON-415-01` |
| G5 | `action` thuộc danh sách trắng, tham số khớp regex/enum, không bắt đầu bằng `-` (`BR-CON-008`) | 5 | `ERR-CON-422-01` |
| J | Tạo job: ≤ 1 `write`, ≤ 2 `read`, ≤ 1 `data` cùng `RUNNING`; ≤ 20 `QUEUED`; không trùng hành động + đối tượng; job `write` thử khoá `STATE_DIR/.lock` không chặn, bận bởi CLI ngoài → `QUEUED`, thử lại mỗi 5 s tới 30 phút (`BR-JOB-001`, `BR-JOB-002`) | 6 | `ERR-JOB-409-01`, `ERR-JOB-429-01`, `ERR-JOB-409-02` |
| D | Job `write` cần dry-run `SUCCEEDED` cùng tham số chuẩn hoá, cùng phiên, ≤ 15 phút, `bundle_id` và `scan_fingerprint` không đổi; hành động toàn máy chủ cần xác nhận kép (`BR-CON-005`, `BR-CON-006`) | 7 | `ERR-JOB-428-01` |
| A | CLI ghi audit "intent" trước thay đổi, "result" khi kết thúc; không ghi được intent → không thay đổi (`BR-AUD-004`) | Trong CLI | `ERR-AUD-500-01` |
| X | Ánh xạ kết thúc job: exit 0 → `SUCCEEDED`, 1 → `SUCCEEDED_WITH_ISSUES`, 2 → `FAILED`, quá timeout → `FAILED`, mất tiến trình → `INTERRUPTED` (`BR-JOB-008`, `BR-JOB-005`) | Cuối | `ERR-JOB-500-01`, `ERR-JOB-504-01`, `ERR-JOB-500-02` |

### 1.7 Danh mục sơ đồ
| Mã sơ đồ | Luồng | File | Use case | FR chính | API chính |
| :--- | :--- | :--- | :--- | :--- | :--- |
| DIAG-SEQ-QP-FEED-002 | 1a. Đồng bộ feed online + dự phòng snapshot đóng gói | `flows.md` §2.1 | `UC-FEED-001`, `UC-FEED-002`, `UC-FEED-003` | `FR-FEED-CMD-001`, `FR-FEED-SYNC-001`, `FR-FEED-SNAP-001`, `FR-FEED-CACH-001..003`, `FR-FEED-NORM-001..002`, `FR-CON-FEED-001` | `POST /api/v1/jobs`, `GET /api/v1/feeds` |
| DIAG-SEQ-QP-FEED-003 | 1b. Nhập snapshot qua console (máy không ra Internet), dry-run → xác nhận | `flows.md` §2.2 | `UC-FEED-004`, `UC-CON-003` | `FR-FEED-SNAP-002..003`, `FR-FEED-CMD-004..005`, `FR-CON-FEED-002`, `FR-CON-SAFE-001`, `FR-CLI-SAFE-001` | `POST /api/v1/feed-snapshots` (2 lần), `GET /api/v1/jobs/{job_id}` |
| DIAG-SEQ-QP-SCAN-001 | 2. Scan + assess qua console | `flows.md` §3 | `UC-CON-002`, `UC-SCAN-001`, `UC-ASMT-001` | `FR-CON-OVW-001`, `FR-SCAN-*`, `FR-SCN-CLS-001..002`, `FR-SCN-LIFE-001`, `FR-SCN-LOCK-001`, `FR-ASMT-*`, `FR-CON-ASMT-001`, `FR-CLI-CMD-001` | `GET /api/v1/overview`, `POST /api/v1/jobs`, `GET /api/v1/runtimes/{runtime_id}/assessment` |
| DIAG-SEQ-QP-PLAN-001 | 3. Chọn phiên bản đích, sinh kế hoạch/checklist, duyệt | `flows.md` §4 | `UC-PLAN-001`, `UC-PLAN-002` | `FR-PLAN-*`, `FR-SCN-CHK-001`, `FR-UPG-PRE-001`, `FR-CMPT-*`, `FR-CON-PLAN-001..002`, `FR-CLI-CMD-002` | `GET /api/v1/runtimes/{runtime_id}/candidates`, `POST /api/v1/plans`, `GET`/`PATCH /api/v1/plans/{plan_id}` |
| DIAG-SEQ-QP-PTCH-001 | 4. Vá cùng nhánh bằng job + stream log SSE | `flows.md` §5 | `UC-PTCH-001`, `UC-CON-003`, `UC-JOB-001`, `UC-JOB-002` | `FR-CON-SAFE-001`, `FR-CON-SAFE-003`, `FR-JOB-RUN-001..003`, `FR-JOB-LOG-001..002`, `FR-JOB-AUD-001`, `FR-PTCH-PHP-001..002`, `FR-PTCH-MIT-001..002`, `FR-PTCH-RST-001`, `FR-PTCH-RBK-001` | `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}/events`, `POST /api/v1/jobs/{job_id}/cancellations` |
| DIAG-SEQ-QP-UPG-001 | 5a. Cài song song → quét tương thích → nâng dependency | [flows-upgrade.md §2](flows-upgrade.md) | `UC-UPG-001`, `UC-PLAN-003` | `FR-UPG-PRE-001`, `FR-UPG-INST-001`, `FR-UPG-CFG-002`, `FR-PLAN-CHK-001..002`, `FR-CMPT-CODE-003`, `FR-CMPT-COMP-001`, `FR-CMPT-RES-001` | `POST /api/v1/plans/{plan_id}/checklist-items/{chk_id}/runs`, `PATCH …/checklist-items/{chk_id}`, `POST …/compatibility-waivers` |
| DIAG-SEQ-QP-UPG-002 | 5b. Chuyển 1 site → health check → tự rollback | [flows-upgrade.md §3](flows-upgrade.md) | `UC-UPG-002` | `FR-UPG-SEQ-001`, `FR-UPG-SWT-001..002`, `FR-UPG-CFG-001`, `FR-UPG-HC-001..006`, `FR-UPG-RBK-002` | `POST /api/v1/jobs`, `GET /api/v1/switches/{run_id}` |
| DIAG-SEQ-QP-UPG-003 | 6. Rollback thủ công 1 lệnh (site và lượt chạy) | [flows-upgrade.md §4](flows-upgrade.md) | `UC-UPG-004`, `UC-PTCH-004` | `FR-UPG-RBK-001`, `FR-PTCH-RBK-002`, `FR-CON-RBK-001` | `GET /api/v1/switches`, `GET /api/v1/backup-runs`, `POST /api/v1/rollbacks` |
| DIAG-SEQ-QP-AUTH-002 | 7. `serve` + token + chặn Host/CSRF | [flows-console-fleet.md §2](flows-console-fleet.md) | `UC-CON-001` | `FR-CON-AUTH-001..006`, `FR-CON-SAFE-002`, `FR-CON-API-001`, `FR-JOB-RUN-004` | `POST`/`GET`/`DELETE /api/v1/sessions…` |
| DIAG-SEQ-QP-FLT-001 | 8. Phase 2: máy trung tâm chạy CLI từ xa qua SSH | [flows-console-fleet.md §3](flows-console-fleet.md) | `UC-FLT-002`, `UC-FLT-003` | `FR-FLT-INV-002`, `FR-FLT-EXEC-001..002`, `FR-FLT-RBAC-001`, `FR-FLT-DASH-001`, `FR-FLT-AUD-001` | `POST /api/v1/fleet-runs`, `GET /api/v1/fleet-runs/{fleet_run_id}`, `GET /api/v1/fleet-summary` |

## 2. Luồng 1 — Đồng bộ dữ liệu CVE/vòng đời online và dự phòng snapshot

### 2.1 Ngữ cảnh: Đồng bộ online từ console, dự phòng bằng snapshot đóng gói (DIAG-SEQ-QP-FEED-002)
- **Tiền điều kiện**: phiên console hợp lệ (luồng 7); hoặc lịch `SYS-01` đã cài bằng `feeds schedule install` (khi đó bắt đầu từ bước gọi CLI, có `--quiet`).
- **Hậu điều kiện thành công**: `feeds/current/` có `bundle_id` mới, `state/sync-status.json` cập nhật; nguồn lỗi giữ dữ liệu cũ với `data_origin` ≠ `PRIMARY` (`BR-FEED-006`), lượt chạy không bị chặn (`BR-FEED-008`).
- **Ngân sách**: tăng dần ≤ 180 s P95, đầy đủ ≤ 900 s (`NFR-FEED-001`); ≤ 45 request khi tăng dần (`NFR-FEED-008`); job `feeds update` timeout 960 s (`BR-JOB-008`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash + qp-feeds.py)
    participant SRC as Feed sources (SRC-001..016)
    participant DB as SQLite (feeds.db)
    participant FS as STATE_DIR (tệp)

    Op->>BR: Bấm "Đồng bộ ngay" trên SCR-008
    BR->>CON: POST /api/v1/jobs {action: "feeds_update"} + cookie qp_session + X-QP-CSRF
    CON->>CON: Cổng G1–G5 và J (BR-CON-003, BR-CON-004, BR-CON-008, BR-JOB-001)
    break Cổng G không đạt
        CON-->>BR: 400/401/403/421/422 (ERR-CON-421-01, ERR-AUTH-401-01, ERR-AUTH-403-01, ERR-CON-422-01)
    end
    break Đã có job feeds_update QUEUED/RUNNING hoặc hàng đợi đủ 20 job
        CON-->>BR: 409 ERR-JOB-409-01 hoặc 429 ERR-JOB-429-01
    end
    CON->>FS: Tạo jobs/{job_id}/job.json (loại data, không cần dry-run theo BR-JOB-003)
    CON-->>BR: 202 {job_id} (P95 ≤ 1.500 ms, NFR-PERF-002)
    CON->>CLI: Popen argv [script, "feeds", "update", "--json"], shell=False
    Note over CLI: Lịch SYS-01 (UC-FEED-002) bắt đầu tại đây với feeds update --quiet
    CLI->>FS: flock feeds/.lock, chờ tối đa 30 s (BR-FEED-015)
    break Khoá bị lượt đồng bộ khác giữ quá 30 s
        CLI-->>CON: exit 2, ERR-FEED-423-01
    end
    CLI->>FS: Kiểm dung lượng trống phân vùng chứa feeds/
    break Còn dưới 100 MB
        CLI-->>CON: exit 2, ERR-FEED-507-01 (bundle hiện có vẫn được dùng)
    end
    opt Chưa có current/ hợp lệ hoặc snapshot đóng gói mới hơn current/ (BR-FEED-053, BR-FEED-054)
        CLI->>FS: sha256sum feeds-snapshot.tar.gz so với QP_SNAPSHOT_SHA256, giải nén vào staging/, kiểm SHA256SUMS
        alt Toàn vẹn đạt (BR-FEED-010)
            CLI->>FS: rename staging/ → current/ trong ≤ 10 s, data_origin = SNAPSHOT
        else Lệch mã băm
            CLI->>FS: Xoá staging/, ghi ERR-FEED-422-02 (Critical), tiếp tục với cache nếu có
        end
    end
    loop Mỗi nguồn quá TTL, thứ tự SRC-006, 002, 009, 012, 011, 004, 001, 010, 003, 008
        CLI->>SRC: HTTPS GET có điều kiện (ETag kèm Accept-Encoding, If-Modified-Since), giãn cách theo BR-FEED-004
        alt 200, JSON hợp lệ, qua kiểm biến động BR-FEED-009
            SRC-->>CLI: Thân phản hồi
            CLI->>FS: Ghi tạm rồi rename raw/SRC-xxx + .meta.json (sha256), data_origin = PRIMARY
        else 304 Not Modified
            SRC-->>CLI: 304
            CLI->>FS: Cập nhật fetched_at trong .meta.json
        else 429, NVD 403, GitHub x-ratelimit-remaining = 0 hoặc Retry-After > 300 s
            SRC-->>CLI: Bị giới hạn tốc độ
            CLI->>FS: sync-status DEGRADED, ERR-FEED-429-01, giữ raw cũ
        else 401/403 khi đã gửi key/token
            SRC-->>CLI: Từ chối khoá
            CLI->>FS: sync-status FAILED, ERR-FEED-401-01 (không ghi key, BR-FEED-011)
        else JSON hỏng, sai schema hoặc biến động bất thường
            SRC-->>CLI: Phản hồi không dùng được
            CLI->>FS: Lưu raw/SRC-xxx/rejected/ (≤ 3 file), giữ raw cũ, ERR-FEED-502-01 hoặc ERR-FEED-502-02
        else DNS, TLS, kết nối hoặc 5xx sau 3 lần thử
            SRC-->>CLI: Lỗi mạng/máy chủ nguồn
            CLI->>CLI: Chuỗi dự phòng BR-FEED-006: nguồn chéo → cache cũ → snapshot SRC-017
            CLI->>FS: sync-status FAILED, ERR-FEED-503-01, data_origin = CROSS:SRC-xxx, CACHE hoặc SNAPSHOT
        end
        break Vượt ngân sách 900 s (đầy đủ) hoặc 180 s (tăng dần)
            CLI->>FS: Nguồn chưa xong giữ dữ liệu cũ, ERR-FEED-504-01
        end
    end
    CLI->>CLI: Kiểm python3 ≥ 3.6 (BR-FEED-012)
    alt Thiếu Python 3.6+
        Note over CLI: ERR-FEED-424-01 — chỉ giữ raw/ vừa tải (để feeds export --raw), không chuẩn hoá, current/ giữ nguyên
    else Có Python 3.6+
        CLI->>CLI: qp-feeds.py chuẩn hoá, khử trùng lặp, tính min_patched (FR-FEED-NORM-001, FR-FEED-NORM-002)
        Note over CLI: Bản ghi không phân tích được bị bỏ qua (ERR-FEED-422-01). Hai nguồn lệch vượt ngưỡng BR-FEED-027 → ERR-FEED-409-01
        CLI->>DB: Dựng staging/feeds.db (meta.bundle_id, advisory, kev_entry, min_patched, risk_assessment)
        CLI->>FS: Ghi staging/ gồm 9 file TSV, manifest.json, SHA256SUMS
        alt Đủ 9 TSV + feeds.db và khớp SHA256SUMS (BR-FEED-051)
            CLI->>FS: rename current/ → previous/, staging/ → current/ (bundle_id mới)
        else Thiếu file hoặc lệch mã băm
            CLI->>FS: Xoá staging/, current/ giữ nguyên, ERR-FEED-422-02
        end
    end
    CLI->>FS: Ghi state/sync-status.json, dọn feeds/ ≤ 60 MB (FR-FEED-CACH-003), nhả khoá
    CLI-->>CON: Envelope --json, exit 0 (mọi nguồn OK), 1 (DEGRADED) hoặc 2 (không có dữ liệu dùng được)
    CON->>FS: Cập nhật job.json theo cổng X (exit 2 → FAILED, ERR-JOB-500-01)
    BR->>CON: GET /api/v1/feeds
    CON->>CLI: feeds status --json (lệnh đọc, FR-FEED-CMD-002)
    CLI->>FS: Đọc state/sync-status.json, current/manifest.json
    CLI-->>CON: qp.feeds.status/1 (freshness, data_age_h, data_origin từng nguồn)
    CON-->>BR: 200 {success: true, data: qp.feeds.status/1}
    alt Mức STALE (168 giờ < tuổi ≤ 2.160 giờ)
        BR-->>Op: SCR-008 kèm cảnh báo ERR-FEED-412-01
    else Mức EXPIRED (tuổi > 2.160 giờ)
        BR-->>Op: SCR-008 kèm ERR-SCN-503-01, chỉ cho phép vá cùng nhánh (BR-FEED-005)
    else FRESH hoặc AGING
        BR-->>Op: SCR-008 với tuổi dữ liệu và nguồn lỗi (nếu có)
    end
```

### 2.2 Ngữ cảnh: Nhập snapshot qua console cho máy chủ không ra Internet — dry-run → xác nhận (DIAG-SEQ-QP-FEED-003)
- **Tiền điều kiện**: người vận hành đã chạy `feeds export --out FILE` trên máy có Internet (`FR-FEED-CMD-004`, loại dữ liệu riêng theo `BR-FEED-056`) và ghi lại SHA-256 in ra; phiên console hợp lệ.
- **Hậu điều kiện thành công**: job dry-run `SUCCEEDED` với 0 thay đổi trên `feeds/`; job nhập `SUCCEEDED`, `current` trỏ bundle của snapshot, audit có người chạy, SHA-256, `generated_at` (`BR-FEED-055`); 2 file tạm `work/upload-{job_id}.tar.gz` đã bị xoá.
- **Ràng buộc**: `feeds_import` là job `write`, bắt buộc dry-run trước (`BR-CON-005` 1.0.1, không thuộc ngoại lệ); job dry-run là `read` (`BR-JOB-003`); xác nhận ≤ 15 phút sau khi tạo job dry-run, cùng phiên, SHA-256 nội dung nhận và `force` bằng giá trị của job dry-run; thân `application/gzip` ≤ 20 MiB (`BR-CON-004` ngoại lệ 2, `BR-CON-009`), tải lên 2 lần vì bước xác nhận không dùng lại file của job dry-run; timeout mỗi job 600 s (`BR-JOB-008`, nhóm "khác"). Hợp đồng chi tiết: [api-spec.md §2.13.3](../api/api-spec.md), [api-spec-core.md §6.2](../api/api-spec-core.md).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash + qp-feeds.py)
    participant DB as SQLite (feeds.db)
    participant FS as STATE_DIR (tệp)

    Op->>BR: SCR-008 → "Nhập snapshot": chọn file .tar.gz, nhập SHA-256 64 ký tự hex, tuỳ chọn force (cho nhập snapshot cũ hơn)
    Note over Op,FS: Bước 1/2 — dry-run (BR-CON-005, FR-CON-SAFE-001)
    BR->>CON: POST /api/v1/feed-snapshots?dry_run=true[&force=true], thân application/gzip, X-QP-Snapshot-SHA256, cookie, X-QP-CSRF
    CON->>CON: Cổng G1–G5 (BR-CON-004 ngoại lệ 2, BR-CON-009) và J (job read)
    break Cổng không đạt
        CON-->>BR: 413 ERR-CON-413-01, 415 ERR-CON-415-01, 403 ERR-AUTH-403-01 hoặc ERR-AUTH-403-02, 422 ERR-CON-422-01 (header SHA-256 không đúng 64 hex), 409 ERR-JOB-409-01, 429 ERR-JOB-429-01
    end
    CON->>FS: Ghi luồng vào work/upload-{job_id}.tar.gz (0600), vừa ghi vừa tính SHA-256, kiểm 2 byte đầu 1f 8b
    break SHA-256 nội dung khác header, không phải gzip, hoặc không đủ dung lượng
        CON->>FS: Xoá file tạm, không tạo job
        CON-->>BR: 422 ERR-FEED-422-02 hoặc 507 ERR-FEED-507-01
    end
    CON->>FS: jobs/{job_id}/job.json loại read (BR-JOB-003), params = {sha256, force}
    CON-->>BR: 202 {dry_job_id}
    CON->>CLI: Popen [script, "feeds", "import", FILE, "--sha256", HEX, "--yes", "--json", "--dry-run"] (+ "--force"), shell=False
    CLI->>FS: Giải nén vào work/dryrun-{pid}/, kiểm SHA-256 gói, tar, SHA256SUMS, schema, generated_at, xoá thư mục tạm kể cả khi lỗi
    Note over CLI,FS: Không lấy feeds/.lock, không đổi staging/, bundles/, current, previous, snapshots/imported/ (FR-CLI-SAFE-001)
    alt Lệch SHA-256 gói hoặc SHA256SUMS, tar có mục bị cấm, giải nén > 50 MB
        CLI-->>CON: exit 2, ERR-FEED-422-02, dry_run = true
    else generated_at cũ hơn current và không có --force
        CLI-->>CON: exit 2, ERR-FEED-409-02
    else Mọi kiểm tra đạt (schema cùng major, generated_at ≤ hiện tại + 1 giờ)
        CLI-->>CON: exit 0, preview (bundle_id, generated_at, schema của snapshot so với current)
    end
    CON->>FS: Xoá work/upload-{dry_job_id}.tar.gz, job.json theo cổng X (exit 2 → FAILED, ERR-JOB-500-01)
    BR->>CON: GET /api/v1/jobs/{dry_job_id} sau SSE event status
    CON-->>BR: 200 {state, result.preview, result.fingerprint.bundle_id}
    break Job dry-run FAILED
        BR-->>Op: SCR-008 hiển thị lỗi của dry-run, không mở bước xác nhận
    end
    BR-->>Op: SCR-011: 4/4 mục của result.preview (NFR-USE-006)
    Op->>BR: Bấm "Xác nhận" trong ≤ 15 phút
    Note over Op,FS: Bước 2/2 — xác nhận, trình duyệt tải lại cùng file
    BR->>CON: POST /api/v1/feed-snapshots?confirm_dry_run_job_id={dry_job_id}[&force=true] + tải lại file + X-QP-Snapshot-SHA256
    CON->>CON: Cổng G1–G5 và J như bước 1 (cùng nhánh lỗi 4xx, 422 ERR-FEED-422-02, 507 ERR-FEED-507-01)
    CON->>FS: Ghi work/upload-{job_id}.tar.gz mới (0600), tính SHA-256 nội dung nhận lần này
    CON->>CON: Cổng D (BR-CON-005): job dry-run cùng action, SHA-256 nội dung và force bằng params của dry-run, cùng phiên, ≤ 15 phút, SUCCEEDED, bundle_id không đổi
    alt Thiếu confirm_dry_run_job_id hoặc không khớp (SHA-256, force, phiên, quá 15 phút, dry-run không SUCCEEDED, bundle_id đổi)
        CON->>FS: Xoá file vừa nhận, không tạo job
        CON-->>BR: 428 ERR-JOB-428-01, details.constraint (missing, params_mismatch, other_session, expired, not_succeeded, fingerprint_changed)
        BR-->>Op: SCR-008 yêu cầu chạy lại dry-run
    else Khớp
        CON->>FS: jobs/{job_id}/job.json loại write, thử khoá STATE_DIR/.lock theo cổng J (bận → QUEUED, quá 30 phút → ERR-JOB-409-02)
        CON-->>BR: 202 {job_id}
        CON->>CLI: Popen [script, "feeds", "import", FILE, "--sha256", HEX, "--yes", "--json"] (+ "--force"), shell=False
        CLI->>FS: Audit intent (cổng A)
        alt Không ghi được audit intent
            CLI-->>CON: exit 2, ERR-AUD-500-01, không nhập
        else Đã ghi intent
            CLI->>FS: flock feeds/.lock, chờ tối đa 30 s (BR-FEED-015)
            alt Khoá bị lượt đồng bộ khác giữ quá 30 s
                CLI-->>CON: exit 2, ERR-FEED-423-01
            else Có khoá
                CLI->>CLI: Kiểm lại toàn bộ (SHA-256 gói, tar, SHA256SUMS, schema, generated_at), giải nén ≤ 50 MB vào staging/
                alt Lệch SHA-256 gói hoặc SHA256SUMS, tar có mục bị cấm hoặc giải nén > 50 MB
                    CLI->>FS: Xoá staging/, current giữ nguyên
                    CLI-->>CON: exit 2, ERR-FEED-422-02 (Critical)
                else generated_at cũ hơn current và không có --force
                    CLI->>FS: Xoá staging/
                    CLI-->>CON: exit 2, ERR-FEED-409-02
                else Hợp lệ
                    CLI->>DB: Đọc meta.bundle_id của staging/feeds.db
                    CLI->>FS: Đổi bundle nguyên tử (BR-FEED-051): current trỏ bundle mới, previous trỏ bundle cũ, giữ ≤ 3 gói ở snapshots/imported/
                    CLI->>FS: Audit result (người chạy, SHA-256, generated_at), nhả feeds/.lock
                    CLI-->>CON: exit 0, qp.feeds.import/1 với bundle_id mới
                end
            end
        end
        CON->>FS: Xoá work/upload-{job_id}.tar.gz, cập nhật job.json (cổng X)
        CON-->>BR: SSE event status, end
        BR-->>Op: SCR-008 hiển thị bundle mới, data_origin = SNAPSHOT, hoặc thông báo lỗi
    end
```

Ghi chú: sơ đồ vẽ theo `BR-CON-005` 1.0.1 ([business-rules.md](business-rules.md)): `feeds_import` bắt buộc dry-run, xác nhận bằng cùng SHA-256 nội dung và cùng `force`; argv `feeds import … --dry-run` có trong danh sách trắng từ [spec.md §3.3.4](spec.md) 1.0.1. Mâu thuẫn ghi ở bản 1.0.0 của tài liệu này đã được quyết (§6.2 mục 1).

## 3. Luồng 2 — Scan và assess qua console

### 3.1 Ngữ cảnh: Quét lại máy chủ, đánh giá 1 runtime và so sánh ứng viên (DIAG-SEQ-QP-SCAN-001)
- **Tiền điều kiện**: phiên console hợp lệ; bundle `current/` có hoặc snapshot đóng gói hợp lệ.
- **Hậu điều kiện thành công**: `state/last-scan.json` mới; `result.json` của job `assess` chứa `qp.assess/1` cùng `bundle_id` với bảng so sánh (`BR-ASMT-003`); SCR-003 hiển thị.
- **Ràng buộc**: `scan` và `assess` là job `read`, không cần dry-run, chạy song song tối đa 2 job (`BR-JOB-001`); `scan` chỉ đọc (`BR-SCAN-001`); scan offline ≤ 60 s P95 (`NFR-PERF-004`, chưa đo); timeout job 1.800 s (`BR-JOB-008`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash + qp-feeds.py)
    participant SRC as Feed sources
    participant PKG as Package manager / Panel
    participant WEB as Web server / PHP-FPM
    participant DB as SQLite (feeds.db)
    participant FS as STATE_DIR (tệp)

    Op->>BR: Mở SCR-002 Tổng quan
    BR->>CON: GET /api/v1/overview (cookie qp_session)
    CON->>FS: Đọc state/last-scan.json, plans/, switches/index.tsv
    CON->>DB: Đọc feeds.db (mode=ro): tuổi dữ liệu từng nguồn
    CON-->>BR: 200 {counts, ranking, plan_deadlines, data_age_h, scan_age_h} (P95 ≤ 500 ms, NFR-PERF-001)
    BR-->>Op: SCR-002, scan_age_h > 24 giờ → hiện nút "Quét lại"
    Op->>BR: Bấm "Quét lại"
    BR->>CON: POST /api/v1/jobs {action: "scan"} + X-QP-CSRF
    CON->>CON: Cổng G1–G5 và J (job read)
    break Cổng G hoặc J không đạt
        CON-->>BR: 4xx (ERR-CON-422-01, ERR-JOB-409-01, ERR-JOB-429-01)
    end
    CON-->>BR: 202 {job_id}
    CON->>CLI: Popen [script, "scan", "--json"], env QP_JOB_ID, QP_ACTOR
    CLI->>CLI: Kiểm Bash ≥ 4.3, flock, curl (FR-CLI-ENV-001)
    break Bash < 4.3 hoặc thiếu flock/curl
        CLI-->>CON: exit 2, ERR-CLI-424-02 → job FAILED (ERR-JOB-500-01)
    end
    CLI->>FS: flock -s -n STATE_DIR/.lock (khoá chia sẻ, BR-JOB-002)
    break Khoá độc quyền đang bị lượt fix/migrate giữ
        CLI-->>CON: exit 2, ERR-CLI-423-01 → job FAILED (ERR-JOB-500-01)
    end
    opt Bundle quá TTL và không có --offline (BR-FEED-001)
        CLI->>SRC: feeds update tăng dần (DIAG-SEQ-QP-FEED-002), chờ tối đa 120 s (NFR-FEED-002)
        Note over CLI,SRC: Quá 120 s → đánh giá bằng bundle hiện có, gắn AGING hoặc STALE
    end
    break Không có current/ hợp lệ, không có snapshot hợp lệ, không có mạng
        CLI-->>CON: exit 2, ERR-FEED-503-01, mọi runtime UNKNOWN
    end
    CLI->>WEB: Nhận diện môi trường và playbook: tiến trình, nginx -T, apachectl -S (FR-SCAN-ENV-001, ≤ 5 s với ≤ 200 vhost)
    opt Không khớp playbook PHP nào
        Note over CLI: PB-000, ERR-ENV-422-01 — chỉ cho mitigation và hướng dẫn
    end
    CLI->>WEB: Kiểm kê site → runtime theo lệnh inventory của playbook (FR-SCAN-MAP-001)
    opt Site khớp ≥ 2 lớp gán, không giải được xung đột
        Note over CLI: ERR-ENV-422-02 — site chỉ ở mức MANUAL (BR-ENV-001)
    end
    CLI->>PKG: Gói sở hữu binary (dpkg -S, rpm -qf), lệnh liệt kê site/phiên bản của panel
    loop Mỗi binary PHP/Node.js (FR-SCAN-RT-001, FR-SCAN-RT-002)
        CLI->>CLI: Đọc phiên bản, giới hạn 10 s (BR-SCAN-002)
        alt Chuỗi bất thường, pre-release hoặc quá 10 s
            CLI->>CLI: Gán SCN-PHP-005/014 hoặc SCN-NODE-008, locked = true, ERR-SCN-422-01 (FR-SCN-LOCK-001)
        else Phiên bản hợp lệ
            CLI->>FS: Tra current/lifecycle.tsv, min_patched.tsv (FR-CLI-COMP-002)
            CLI->>CLI: Gán kịch bản (FR-SCN-CLS-001/002), trạng thái hỗ trợ và ưu tiên (FR-SCN-LIFE-001)
            opt Binary thuộc gói distro và phiên bản < min_patched_sec
                CLI->>SRC: OSV hệ distro, tracker distro (SRC-014, SRC-015), changelog gói SRC-016
                CLI->>DB: qp-feeds.py backport: FIXED, NOT_AFFECTED hoặc UNKNOWN (FR-FEED-NORM-003)
                Note over CLI,DB: ok-backport chỉ khi mọi CVE FIXED/NOT_AFFECTED (BR-SEC-002)
            end
        end
    end
    CLI->>FS: Kiểm kê dự án (find -P sâu 7 cấp), container, dấu hiệu webshell chỉ báo cáo (FR-SCAN-PRJ-001/002, FR-SCAN-WSH-001, BR-SEC-003)
    CLI->>SRC: OSV querybatch cho lockfile (lô ≤ 500, cache 6 giờ, FR-FEED-OSV-001)
    alt OSV lỗi và không có cache ≤ 7 ngày
        Note over CLI: ERR-FEED-503-02 — bỏ qua lockfile đó, scan vẫn hoàn tất (BR-FEED-008)
    else OSV trả kết quả
        SRC-->>CLI: Advisory theo package, gồm MAL-*
    end
    CLI->>FS: So site_binding với lượt chuyển PASSED gần nhất (FR-SCAN-DRF-001)
    opt Gán site bị đổi ngoài tool
        Note over CLI: drift_warnings[], ERR-SCAN-409-01
    end
    CLI->>FS: Ghi state/last-scan.json (ghi tạm + rename)
    CLI-->>CON: Envelope qp.scan/1 (bundle_id, freshness, data_age_h), exit 0 hoặc 1
    CON->>FS: Cập nhật job.json (cổng X)
    CON-->>BR: SSE event status, end
    Op->>BR: Chọn 1 runtime → SCR-003
    BR->>CON: POST /api/v1/jobs {action: "assess", params: {runtime_id}}
    CON->>CON: Cổng G1–G5: runtime_id khớp regex BR-CON-008
    break runtime_id sai định dạng
        CON-->>BR: 422 ERR-CON-422-01
    end
    CON-->>BR: 202 {job_id}
    CON->>CLI: Popen [script, "assess", "--runtime-id", ID, "--candidates", "--json"]
    alt Thiếu python3 ≥ 3.6
        CLI-->>CON: exit 2, ERR-CLI-424-01
    else runtime_id không có trong scan gần nhất
        CLI-->>CON: exit 2, ERR-ASMT-404-01
    else Hợp lệ (scan gần nhất ≤ 24 giờ, nếu không thì chạy scan đọc trước)
        CLI->>DB: Tập U(X), đếm CVE theo CVSS v3.1, KEV, vòng đời, min_patched (FR-ASMT-CUR-001)
        CLI->>DB: 4 loại ứng viên BR-ASMT-001, selectable theo BR-ASMT-002 (FR-ASMT-CAND-001)
        CLI->>PKG: apt-cache policy, dnf list available, whmapi1 php_get_installed_versions (FR-ASMT-CAND-002)
        Note over CLI,PKG: Lệnh verified=false không chạy → installable = unknown (BR-ENV-010)
        CLI->>DB: Điểm R, ΔR cùng bundle_id và ngày T (FR-ASMT-RISK-001/002, BR-ASMT-003), xếp hạng BR-ASMT-004
        alt Dữ liệu EXPIRED (> 90 ngày)
            Note over CLI: ERR-SCN-503-01 — ứng viên khác nhánh selectable = false
        else Dữ liệu STALE (> 7 ngày)
            Note over CLI: Cảnh báo ERR-FEED-412-01 trên kết quả
        end
        CLI-->>CON: Envelope qp.assess/1, exit 0 hoặc 1
    end
    CON->>FS: Lưu jobs/{job_id}/result.json, cập nhật job.json (cổng X)
    BR->>CON: GET /api/v1/runtimes/{runtime_id}/assessment
    CON->>FS: Đọc result.json của job assess mới nhất cho runtime_id
    alt Không có kết quả cho runtime_id
        CON-->>BR: 404 ERR-ASMT-404-01
    else Có kết quả
        CON-->>BR: 200 {current, candidates[], comparison, bundle_id, data_age_h, catalog_version}
        BR-->>Op: SCR-003: CVE/KEV, EOL/LTS, bảng so sánh, ΔR, nút "Vá cùng nhánh" và "Lập kế hoạch"
    end
```

Ghi chú: SRS không quy định `GET /api/v1/runtimes/{runtime_id}/assessment` tự tính hay đọc kết quả job; sơ đồ giả định console đọc `result.json` của job `assess` mới nhất (giữ nguyên tắc `GET` không tạo tiến trình, `FR-CON-AUTH-006`) — xem §6.2 mục 2.

## 4. Luồng 3 — Chọn phiên bản đích, sinh kế hoạch/checklist và duyệt

### 4.1 Ngữ cảnh: Từ SCR-003 tới kế hoạch `approved` (DIAG-SEQ-QP-PLAN-001)
- **Tiền điều kiện**: đã có kết quả `assess` của runtime (luồng 2); phiên console hợp lệ.
- **Hậu điều kiện thành công**: `STATE_DIR/plans/{plan_id}/` có `plan.json`, `items.json`, `events.jsonl` (ghi tạm + `rename`, `NFR-REL-006`); kế hoạch ở `draft`, sau duyệt ở `approved` (DIAG-STATE-QP-PLAN-001).
- **Ràng buộc**: từ SCR-002 tới checklist ≤ 4 thao tác (`NFR-USE-002`); sinh kế hoạch gồm quét tương thích ≤ 120 s cho 10.000 file `.php` và 300 package (`NFR-PERF-005`, chưa đo); `plan create` là job `read`, quét chỉ đọc và chạy Composer trên bản sao (`BR-CMPT-003`, `BR-CMPT-004`); 1 site ≤ 1.800 s (`BR-CMPT-005`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash + qp-feeds.py)
    participant SRC as Feed sources
    participant PKG as Package manager / Panel
    participant DB as SQLite (feeds.db)
    participant FS as STATE_DIR (tệp)

    Op->>BR: SCR-003 → "Lập kế hoạch"
    BR->>CON: GET /api/v1/runtimes/{runtime_id}/candidates
    CON->>FS: Đọc result.json của job assess mới nhất
    CON-->>BR: 200 candidates[] (types[], selectable, not_selectable_reason, installable)
    Op->>BR: Chọn nhánh đích, phạm vi site, nhập lý do khi đích không mang nhãn RECOMMENDED
    BR->>CON: POST /api/v1/plans {runtime_id, target, sites[], reason} + X-QP-CSRF
    CON->>CON: Cổng G1–G5 (target theo regex nhánh PHP hoặc dòng Node.js, reason 20–500 ký tự) và J
    break Tham số sai hoặc hàng đợi đầy
        CON-->>BR: 422 ERR-CON-422-01 hoặc 429 ERR-JOB-429-01
    end
    CON-->>BR: 202 {job_id}, SCR-004 hiển thị tiến độ qua SSE (FR-CON-PLAN-001)
    CON->>CLI: Popen [script, "plan", "create", "--runtime-id", ID, "--target", X.Y, "--sites", LIST, "--reason", TEXT, "--json"]
    CLI->>CLI: Kiểm python3 ≥ 3.6, flock -s -n STATE_DIR/.lock
    break Thiếu Python 3.6+ hoặc khoá độc quyền bị giữ
        CLI-->>CON: exit 2, ERR-CLI-424-01 hoặc ERR-CLI-423-01
    end
    CLI->>DB: Kiểm đích (FR-PLAN-TGT-001): selectable, BR-UPG-004, BR-SCN-005/006/007
    alt Đích EOL, PRE_RELEASE, UNKNOWN, "6.x", hoặc Node.js CURRENT cho site production
        CLI-->>CON: exit 2, ERR-SCN-409-02
    else Không nhánh đích nào thoả framework, loader hoặc engines
        CLI-->>CON: exit 2, ERR-SCN-409-01
    else Đích khác RECOMMENDED và lý do < 20 ký tự
        CLI-->>CON: exit 2, ERR-PLAN-422-01
    else Runtime đã có kế hoạch in_progress (BR-PLAN-002)
        CLI-->>CON: exit 2, ERR-PLAN-409-01
    else Đích hợp lệ
        CLI->>FS: Kế hoạch draft/approved cũ của runtime → cancelled, ghi audit (BR-PLAN-002)
        CLI->>PKG: Tiền điều kiện FR-UPG-PRE-001: kho có nhánh đích, df ≥ 2 GB, MemAvailable ≥ 512 MB, root hoặc API panel
        PKG-->>CLI: preconditions[] (check, required, actual, pass)
        Note over CLI,PKG: Không đạt → ghi ERR-SCN-412-01 trên kế hoạch, chặn mục P2 cài song song
        CLI->>FS: Kiểm công cụ quét trong tools/php theo tools_manifest.json (FR-CMPT-TOOL-001)
        opt Chưa có công cụ và có mạng
            CLI->>SRC: Tải PHPCompatibility, PHP_CodeSniffer, Composer theo phiên bản cố định của catalog (BR-CMPT-006)
            alt SHA-256 lệch giá trị catalog (BR-SEC-005)
                CLI->>FS: Xoá file tải về, ERR-PTCH-502-01
            else Không tải được (offline, lỗi mạng)
                Note over CLI: ERR-CMPT-424-01 — chỉ chạy bộ luật BC tĩnh FR-CMPT-CODE-001
            end
        end
        loop Mỗi site trong phạm vi (FR-CMPT-*)
            CLI->>FS: Luật BC tĩnh dải ($OLD, $NEW] trên *.php, *.inc, *.phtml (FR-CMPT-CODE-001, BR-CMPT-001)
            Note over CLI,FS: File > 2 MiB bị bỏ qua và liệt kê (ERR-CMPT-413-01)
            alt Có PHP ≥ 7.2 trên máy (BR-CMPT-002)
                CLI->>CLI: phpcs PHPCompatibility testVersion $NEW, song song theo số vCPU (FR-CMPT-CODE-002)
            else Không có PHP ≥ 7.2
                Note over CLI: ERR-CMPT-422-01 — phần PHPCompatibility PENDING
            end
            CLI->>FS: ini bị gỡ, extension, framework, loader mã hoá (FR-CMPT-INI-001, EXT-001, FWK-001, LDR-001)
            opt Loader không có bản chính thức cho nhánh đích
                Note over CLI: ERR-SCN-409-03 (BR-SCN-043)
            end
            CLI->>FS: Composer trên bản sao work/{plan_id}/ với --no-scripts --no-plugins (FR-CMPT-COMP-001, BR-CMPT-003)
            CLI->>SRC: GET repo.packagist.org/p2/{vendor}/{package}.json, cache 24 giờ (FR-CMPT-COMP-002, BR-DATA-003)
            alt Packagist không truy cập được
                Note over CLI,SRC: ERR-FEED-503-01 — min_compatible_version = unknown
            else Có metadata
                SRC-->>CLI: Phiên bản tối thiểu có require.php chấp nhận $NEW
            end
            break Quét 1 site vượt 1.800 s
                CLI->>FS: Phần chưa xong PENDING, ERR-CMPT-504-01
            end
            CLI->>CLI: Kết luận site PASS, FAIL (còn hit error chưa miễn trừ) hoặc PENDING (cần $NEW_BIN) (FR-CMPT-RES-001)
        end
        CLI->>CLI: Lắp checklist hiệu lực, upgrade_items[], site_order + canary, hạn duyệt, mục P2 vá cùng nhánh đứng trước khi runtime vulnerable (FR-SCN-CHK-001, FR-PLAN-DEP-001, FR-PLAN-GEN-002, FR-PLAN-DL-001, BR-UPG-006)
        CLI->>FS: Ghi tạm + rename plans/{plan_id}/plan.json, items.json, events.jsonl (draft, bundle_id, catalog_version, scan_fingerprint)
        CLI->>FS: Audit (lý do đích khác đề xuất, BR-PLAN-001)
        CLI-->>CON: Envelope qp.plan/1 {plan_id}, exit 0 hoặc 1 (có site FAIL/PENDING)
    end
    CON->>FS: Cập nhật job.json (cổng X)
    CON-->>BR: SSE event status, end
    BR->>CON: GET /api/v1/plans/{plan_id}, GET …/checklist-items, GET …/compatibility
    CON->>FS: Đọc plan.json, items.json, kiểm điều kiện lỗi thời BR-PLAN-006
    CON-->>BR: 200 {status: draft, stale, site_order, canary_site_id, upgrade_items[], deadline, checklist_items[]}
    BR-->>Op: SCR-004: checklist theo giai đoạn P1–P6, nhãn "chưa kiểm chứng", kết luận tương thích từng site
    opt Đổi site canary trước khi duyệt (BR-PLAN-004)
        Op->>BR: Chọn canary khác
        BR->>CON: PATCH /api/v1/plans/{plan_id} {canary_site_id} + X-QP-CSRF
        CON-->>BR: 200, ghi audit đổi canary
    end
    Op->>BR: Bấm "Duyệt kế hoạch"
    BR->>CON: PATCH /api/v1/plans/{plan_id} {status: "approved"} + X-QP-CSRF
    CON->>CLI: plan approve {plan_id} --json (argv cố định, shell=False)
    alt plan_id không tồn tại
        CLI-->>CON: exit 2 → 404 ERR-PLAN-404-01
    else Kế hoạch stale (BR-PLAN-006)
        CLI-->>CON: exit 2 → 410 ERR-PLAN-410-01
    else Kế hoạch không ở draft
        CLI-->>CON: exit 2 → 409 ERR-PLAN-409-02
    else Chưa đạt BR-PLAN-003 (quét trước cài chưa đủ 100% site, mục P1 AUTO chưa DONE, tiền điều kiện chưa kiểm)
        CLI-->>CON: exit 2 → 412 ERR-PLAN-412-01
    else Đạt
        CLI->>FS: Audit intent, plan.json status = approved, events.jsonl, audit result
        CLI-->>CON: exit 0
        CON-->>BR: 200 {status: approved}
        BR-->>Op: SCR-004 mở các mục P2 để chạy (luồng 5)
    end
```

Ghi chú: danh sách trắng `BR-CON-008` (spec §3.3.4) chưa có hành động cho `plan approve`, `plan item`, `plan cancel` và đổi canary, trong khi `PATCH /api/v1/plans/{plan_id}` và `PATCH …/checklist-items/{chk_id}` cần các thao tác này; sơ đồ giả định console gọi CLI với argv cố định ngoài hàng đợi job — xem §6.2 mục 3.

## 5. Luồng 4 — Vá cùng nhánh bằng job và stream log SSE

### 5.1 Ngữ cảnh: Dry-run → xác nhận → job `fix` → log trực tiếp → huỷ (DIAG-SEQ-QP-PTCH-001)
- **Tiền điều kiện**: runtime `vulnerable`, nhánh còn hỗ trợ, `locked = false`; `serve` chạy root cho thao tác hệ thống (`BR-CON-010`).
- **Hậu điều kiện thành công**: runtime `ok`/`ok-backport` hoặc có mitigation tạm; `STATE_DIR/backups/{run_id}/manifest` ghi trước thay đổi đầu tiên (kế thừa v0.1 `ensure_backup_dir`, `backup_file`, `record`); audit intent + result (`NFR-REL-002`).
- **Ràng buộc**: ≤ 3 thao tác trên console (`NFR-USE-001`); dòng log hiển thị ≤ 2 s ở P95 (`NFR-PERF-003`); timeout job `fix` 3.600 s (`BR-JOB-008`).

```mermaid
sequenceDiagram
    autonumber
    actor Op as Operator
    participant BR as Browser
    participant CON as Console (Python)
    participant CLI as CLI (Bash)
    participant PKG as Package manager / Panel
    participant WEB as Web server / PHP-FPM
    participant FS as STATE_DIR (tệp)

    Op->>BR: SCR-003 → "Vá cùng nhánh" (thao tác 1)
    BR->>CON: POST /api/v1/jobs {action: "fix", params: {only: "php"}, dry_run: true} + X-QP-CSRF
    CON->>CON: Cổng G1–G5 và J (lệnh --dry-run là job read, BR-JOB-003)
    break Cổng G hoặc J không đạt
        CON-->>BR: 4xx (ERR-CON-422-01, ERR-JOB-409-01, ERR-JOB-429-01)
    end
    CON-->>BR: 202 {job_id của dry-run}
    CON->>CLI: Popen [script, "fix", "--json", "--only", "php", "--dry-run"]
    CLI->>PKG: Gói sở hữu, nhóm gói theo nguồn cài (FR-PTCH-PHP-002, BR-PTCH-002), mốc min_patched_sec từ bundle
    CLI-->>CON: Gói sẽ nâng, mitigation sẽ ghi/gỡ, dịch vụ sẽ restart, 0 thay đổi, không ghi manifest (BR-CLI-003)
    CON->>FS: result.json, job.json SUCCEEDED
    CON-->>BR: SSE event end
    BR-->>Op: SCR-011: thay đổi dự kiến, đối tượng ảnh hưởng, gián đoạn dự kiến, khả năng hoàn tác (4/4 mục, NFR-USE-006)
    Op->>BR: Bấm "Xác nhận" trong ≤ 15 phút (thao tác 2)
    BR->>CON: POST /api/v1/jobs {action: "fix", params giống hệt, confirm_dry_run_job_id} + X-QP-CSRF
    CON->>CON: Cổng D (BR-CON-005) và quyền tiến trình serve (BR-CON-010)
    alt Không có dry-run hợp lệ (khác tham số, khác phiên, quá 15 phút, bundle_id hoặc scan_fingerprint đổi)
        CON-->>BR: 428 ERR-JOB-428-01
    else Đã có job fix cùng đối tượng QUEUED/RUNNING
        CON-->>BR: 409 ERR-JOB-409-01
    else Hợp lệ
        CON->>FS: Thử flock -x -n STATE_DIR/.lock (FR-JOB-RUN-002)
        alt Khoá bị lượt CLI ngoài console giữ
            CON->>FS: job QUEUED, thử lại mỗi 5 s
            Note over CON,FS: Quá 30 phút → job FAILED, ERR-JOB-409-02
        else Khoá rảnh và chưa có job write RUNNING (BR-JOB-001)
            CON->>CLI: Popen [script, "fix", "--json", "--only", "php"], env QP_JOB_ID, QP_ACTOR, start_new_session
        end
        CON-->>BR: 202 {job_id} (P95 ≤ 1.500 ms, NFR-PERF-002)
    end
    BR->>CON: GET /api/v1/jobs/{job_id}/events (EventSource chỉ gửi cookie, không gửi header tuỳ chỉnh)
    CON->>CON: Cổng G1, G3, giới hạn 3 luồng SSE mỗi phiên và 10 luồng toàn console (BR-JOB-007)
    alt job_id không tồn tại
        CON-->>BR: 404 ERR-JOB-404-01
    else Log đã bị dọn theo chính sách lưu giữ
        CON-->>BR: 410 ERR-JOB-410-01
    else Vượt giới hạn luồng SSE
        CON-->>BR: 429 ERR-JOB-429-02
    else Hợp lệ
        CON-->>BR: 200 text/event-stream, dòng retry: 2000
    end
    par CLI thực thi vá
        CLI->>FS: flock -x -n STATE_DIR/.lock, audit intent (cổng A)
        alt Không ghi được audit intent
            CLI-->>CON: exit 2, ERR-AUD-500-01, không thay đổi
        else Không root (BR-PTCH-003, BR-CLI-005)
            CLI->>FS: Issue "needs root" như v0.1, ERR-PTCH-403-01, chỉ xử lý mức dự án
        else Runtime locked (FR-SCN-LOCK-001)
            CLI->>FS: Runtime SKIPPED, ERR-SCN-422-01
        else Root, runtime vulnerable
            CLI->>FS: ensure_backup_dir, ghi manifest + note, phase = MANIFEST_WRITTEN (FR-PTCH-RBK-001)
            Note over CLI,FS: Dưới 50 MB trống tại STATE_DIR → dừng trước thay đổi, ERR-ENV-507-01
            CLI->>PKG: apt-get install --only-upgrade, dnf upgrade hoặc apk upgrade theo nhóm gói, phase = CHANGING
            PKG-->>CLI: Kết quả nâng gói
            CLI->>CLI: Đánh giá lại theo bundle và backport (BR-PTCH-001, BR-SEC-002), phase = VERIFYING
            alt Đã lên bản vá (ok hoặc ok-backport)
                opt Còn file zz-php-quickpatch-mitigation.ini
                    CLI->>FS: backup_file rồi xoá file mitigation, ghi copy vào manifest (FR-PTCH-MIT-002)
                end
            else Kho chưa có bản vá
                CLI->>FS: Ghi mitigation ini vào mọi conf.d của build, ghi created vào manifest (FR-PTCH-MIT-001), ERR-PTCH-424-01
                Note over CLI,FS: Không có thư mục conf.d → ERR-PTCH-412-01
            end
            alt Có --no-restart
                CLI->>FS: Issue high "chưa restart" (BR-PTCH-007)
            else Mặc định
                CLI->>WEB: Restart unit PHP-FPM khớp mẫu v0.1 và php[0-9]+-php-fpm, cPanel dùng restartsrv (FR-PTCH-RST-001)
                WEB-->>CLI: Trạng thái unit
            end
        end
        CLI->>FS: Audit result, dòng gợi ý rollback {run_id}
        CLI-->>CON: Envelope qp.fix/1, exit 0 (đã vá), 1 (còn vấn đề, vd chỉ có mitigation) hoặc 2
    and Console đẩy log
        loop Mỗi dòng mới trong jobs/{job_id}/output.log (≤ 20 MiB, che bí mật BR-SEC-006)
            CON-->>BR: event log, id = byte offset cuối dòng, ≤ 2 s sau khi CLI ghi
        end
        CON-->>BR: Comment heartbeat mỗi 15 s, event phase khi phase đổi
    end
    opt Mất kết nối SSE
        BR->>CON: Tự nối lại sau 2.000 ms với header Last-Event-ID
        CON-->>BR: Gửi tiếp từ byte offset sau Last-Event-ID
    end
    opt Người vận hành bấm "Huỷ" (UC-JOB-002)
        BR->>CON: POST /api/v1/jobs/{job_id}/cancellations + X-QP-CSRF
        CON->>FS: Đọc jobs/{job_id}/phase
        alt phase thuộc MANIFEST_WRITTEN, CHANGING, VERIFYING
            CON-->>BR: 423 ERR-JOB-423-01 (vùng tới hạn, BR-JOB-004)
        else Ngoài vùng tới hạn
            CON->>CLI: SIGTERM nhóm tiến trình, SIGKILL sau 10 s
            CON-->>BR: 202, job CANCELLED, ghi audit
        end
    end
    CON->>FS: job.json, result.json theo cổng X (quá 3.600 s → ERR-JOB-504-01, exit 2 → ERR-JOB-500-01)
    CON-->>BR: event status, event end, đóng luồng
    BR-->>Op: SCR-006: kết quả, run_id để rollback (luồng 6)
```

## 6. Truy vết, phát hiện và câu hỏi mở

### 6.1 Ma trận truy vết mã lỗi theo sơ đồ
| Sơ đồ | Số thông điệp đánh số | Số mã ERR | Mã ERR trên nhánh lỗi |
| :--- | :---: | :---: | :--- |
| DIAG-SEQ-QP-FEED-002 | 47 | 21 | `ERR-AUTH-401-01`, `ERR-AUTH-403-01`, `ERR-CON-421-01`, `ERR-CON-422-01`, `ERR-FEED-401-01`, `ERR-FEED-409-01`, `ERR-FEED-412-01`, `ERR-FEED-422-01`, `ERR-FEED-422-02`, `ERR-FEED-423-01`, `ERR-FEED-424-01`, `ERR-FEED-429-01`, `ERR-FEED-502-01`, `ERR-FEED-502-02`, `ERR-FEED-503-01`, `ERR-FEED-504-01`, `ERR-FEED-507-01`, `ERR-JOB-409-01`, `ERR-JOB-429-01`, `ERR-JOB-500-01`, `ERR-SCN-503-01` |
| DIAG-SEQ-QP-FEED-003 | 46 | 15 | `ERR-AUD-500-01`, `ERR-AUTH-403-01`, `ERR-AUTH-403-02`, `ERR-CON-413-01`, `ERR-CON-415-01`, `ERR-CON-422-01`, `ERR-FEED-409-02`, `ERR-FEED-422-02`, `ERR-FEED-423-01`, `ERR-FEED-507-01`, `ERR-JOB-409-01`, `ERR-JOB-409-02`, `ERR-JOB-428-01`, `ERR-JOB-429-01`, `ERR-JOB-500-01` |
| DIAG-SEQ-QP-SCAN-001 | 54 | 16 | `ERR-ASMT-404-01`, `ERR-CLI-423-01`, `ERR-CLI-424-01`, `ERR-CLI-424-02`, `ERR-CON-422-01`, `ERR-ENV-422-01`, `ERR-ENV-422-02`, `ERR-FEED-412-01`, `ERR-FEED-503-01`, `ERR-FEED-503-02`, `ERR-JOB-409-01`, `ERR-JOB-429-01`, `ERR-JOB-500-01`, `ERR-SCAN-409-01`, `ERR-SCN-422-01`, `ERR-SCN-503-01` |
| DIAG-SEQ-QP-PLAN-001 | 55 | 20 | `ERR-CLI-423-01`, `ERR-CLI-424-01`, `ERR-CMPT-413-01`, `ERR-CMPT-422-01`, `ERR-CMPT-424-01`, `ERR-CMPT-504-01`, `ERR-CON-422-01`, `ERR-FEED-503-01`, `ERR-JOB-429-01`, `ERR-PLAN-404-01`, `ERR-PLAN-409-01`, `ERR-PLAN-409-02`, `ERR-PLAN-410-01`, `ERR-PLAN-412-01`, `ERR-PLAN-422-01`, `ERR-PTCH-502-01`, `ERR-SCN-409-01`, `ERR-SCN-409-02`, `ERR-SCN-409-03`, `ERR-SCN-412-01` |
| DIAG-SEQ-QP-PTCH-001 | 53 | 17 | `ERR-AUD-500-01`, `ERR-CON-422-01`, `ERR-ENV-507-01`, `ERR-JOB-404-01`, `ERR-JOB-409-01`, `ERR-JOB-409-02`, `ERR-JOB-410-01`, `ERR-JOB-423-01`, `ERR-JOB-428-01`, `ERR-JOB-429-01`, `ERR-JOB-429-02`, `ERR-JOB-500-01`, `ERR-JOB-504-01`, `ERR-PTCH-403-01`, `ERR-PTCH-412-01`, `ERR-PTCH-424-01`, `ERR-SCN-422-01` |
| DIAG-SEQ-QP-UPG-001 | 67 | 19 | `ERR-AUD-500-01`, `ERR-CLI-403-01`, `ERR-CMPT-504-01`, `ERR-ENV-422-01`, `ERR-ENV-424-01`, `ERR-ENV-500-01`, `ERR-FEED-503-01`, `ERR-FEED-503-02`, `ERR-JOB-409-02`, `ERR-JOB-428-01`, `ERR-JOB-500-01`, `ERR-JOB-504-01`, `ERR-PLAN-409-02`, `ERR-PLAN-410-01`, `ERR-PLAN-422-01`, `ERR-PTCH-502-01`, `ERR-SCN-412-01`, `ERR-SCN-412-03`, `ERR-SCN-424-01` |
| DIAG-SEQ-QP-UPG-002 | 72 | 28 | `ERR-AUD-500-01`, `ERR-ENV-409-01`, `ERR-ENV-410-01`, `ERR-ENV-412-01`, `ERR-ENV-500-01`, `ERR-ENV-500-02`, `ERR-ENV-500-03`, `ERR-ENV-502-01`, `ERR-ENV-507-01`, `ERR-HC-412-01`, `ERR-HC-412-02`, `ERR-HC-412-03`, `ERR-HC-422-01`, `ERR-HC-422-02`, `ERR-HC-424-01`, `ERR-HC-424-02`, `ERR-HC-500-01`, `ERR-HC-500-02`, `ERR-JOB-428-01`, `ERR-JOB-504-01`, `ERR-SCN-409-02`, `ERR-SCN-412-02`, `ERR-SCN-424-01`, `ERR-SCN-500-01`, `ERR-UPG-409-01`, `ERR-UPG-409-02`, `ERR-UPG-409-03`, `ERR-UPG-423-01` |
| DIAG-SEQ-QP-UPG-003 | 48 | 11 | `ERR-AUD-500-01`, `ERR-CLI-423-01`, `ERR-CON-404-01`, `ERR-ENV-410-01`, `ERR-ENV-500-03`, `ERR-ENV-502-01`, `ERR-HC-500-02`, `ERR-JOB-409-02`, `ERR-JOB-428-01`, `ERR-JOB-504-01`, `ERR-PTCH-404-01` |
| DIAG-SEQ-QP-AUTH-002 | 56 | 20 | `ERR-AUTH-401-01`, `ERR-AUTH-401-02`, `ERR-AUTH-403-01`, `ERR-AUTH-403-02`, `ERR-AUTH-409-01`, `ERR-AUTH-429-01`, `ERR-CON-400-01`, `ERR-CON-404-01`, `ERR-CON-405-01`, `ERR-CON-409-01`, `ERR-CON-409-02`, `ERR-CON-409-03`, `ERR-CON-412-01`, `ERR-CON-413-01`, `ERR-CON-415-01`, `ERR-CON-421-01`, `ERR-CON-424-01`, `ERR-CON-500-01`, `ERR-CON-503-01`, `ERR-JOB-500-02` |
| DIAG-SEQ-QP-FLT-001 | 42 | 11 | `ERR-CLI-423-01`, `ERR-CON-422-01`, `ERR-FLT-401-01`, `ERR-FLT-403-01`, `ERR-FLT-403-02`, `ERR-FLT-404-01`, `ERR-FLT-409-01`, `ERR-FLT-422-02`, `ERR-FLT-422-03`, `ERR-FLT-424-01`, `ERR-FLT-504-01` |

Độ phủ (đếm lại 2026-10-22 trên 10 khối Mermaid của 3 file): 10 sơ đồ dùng 111/129 mã `ERR-*` của [error-matrix.md](error-matrix.md) 1.1.0, gồm `ERR-JOB-429-02`, `ERR-UPG-409-03`, `ERR-FLT-422-03` (định nghĩa chuẩn từ bản 1.0.1 của ma trận); 0 mã trên sơ đồ nằm ngoài ma trận. 18 mã chưa xuất hiện. (a) 6 mã ma trận thêm ở bản 1.0.1 và 1.1.0, chưa phản ánh vào sơ đồ: `ERR-FEED-503-03` (nguồn Phụ/Dự phòng/Tùy chọn lỗi, tách từ `ERR-FEED-503-01` theo error-matrix.md §5 mục 5; DIAG-SEQ-QP-FEED-002 vẫn ghi `ERR-FEED-503-01` cho mọi nguồn), `ERR-HC-412-04` (baseline URL khai báo không ổn định, tách từ `ERR-HC-412-02`), `ERR-CLI-412-01` (`STATE_DIR` hoặc thư mục lượt backup không đạt kiểm tra an toàn), `ERR-PTCH-409-01`, `ERR-PTCH-500-01`, `ERR-UPG-409-04` (3 mã đề xuất chờ PO duyệt `CR-FR-05`, `CR-FR-01`). (b) 12 mã thuộc luồng ngoài phạm vi tài liệu này: `ERR-AUD-409-01` (`UC-JOB-003`), `ERR-CLI-400-01` (chỉ phát sinh khi gọi CLI trực tiếp sai cú pháp; console dựng argv từ danh sách trắng), `ERR-CLI-428-01` (ghi ở phần ngữ cảnh luồng 6 cho đường CLI), `ERR-ENV-424-02` (`UC-UPG-006`), `ERR-FLT-422-01` (`UC-FLT-001`), `ERR-PTCH-424-02`, `ERR-PTCH-424-03`, `ERR-PTCH-424-04` (`UC-PTCH-002`), `ERR-RPT-409-01`, `ERR-RPT-422-01` (`UC-RPT-*`), `ERR-SCN-424-02` (`UC-UPG-005`), `ERR-UPG-412-01` (`UC-UPG-007`).

### 6.2 Phát hiện khi vẽ sơ đồ, giả định và câu hỏi mở
| STT | Phát hiện / giả định | Căn cứ | Cách vẽ trong sơ đồ | Đề xuất | Người quyết định |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | `feeds_import` là job `write` nhưng danh sách trắng (spec 1.0.0) không có `--dry-run`, mâu thuẫn `BR-CON-005` (mọi job ghi cần dry-run) | `BR-JOB-003`, spec §3.3.4, `FR-CON-FEED-002` | Từ bản 1.0.1: DIAG-SEQ-QP-FEED-003 chạy 2 bước dry-run → xác nhận, console so SHA-256 nội dung và `force` với job dry-run, thiếu hoặc lệch → 428 `ERR-JOB-428-01` | **Đã quyết** theo `BR-CON-005` 1.0.1 ([business-rules.md](business-rules.md)): bắt buộc dry-run cho `feeds_import`, không thuộc ngoại lệ; [spec.md §3.3.4](spec.md) từ 1.0.1 có `--dry-run` trong argv; hợp đồng API ở api-spec.md §2.13.3 | PO + Dev — đã đóng (business-rules.md §6 mục 2) |
| 2 | SRS không nói `GET /api/v1/runtimes/{runtime_id}/assessment` tự tính hay đọc kết quả job | spec §3.3.3, `FR-CON-ASMT-001` | Console đọc `result.json` của job `assess` mới nhất; chưa có → 404 `ERR-ASMT-404-01` | Ghi rõ vào hợp đồng API; khi `bundle_id` của kết quả khác bundle hiện tại, SCR-003 gắn nhãn "kết quả cũ" và nút đánh giá lại | Dev |
| 3 | Danh sách trắng `BR-CON-008` thiếu hành động cho duyệt/huỷ kế hoạch, đặt trạng thái mục, đổi canary, miễn trừ hit tương thích, sửa `hc_url`, trong khi các `PATCH`/`POST` tương ứng tồn tại | spec §3.3.3, §3.3.4 | Console gọi CLI `plan approve` với argv cố định, ngoài hàng đợi job, có audit | Bổ sung các dòng `plan_approve`, `plan_cancel`, `plan_item_set`, `plan_set_canary`, `plan_waive_hit`, `site_set_hc_url` vào spec §3.3.4 kèm regex tham số | BA + Dev |
| 4 | Không có mã lỗi khi chuyển site không theo `site_order` hoặc khi lượt trước `ROLLED_BACK` chưa được xác nhận | `BR-ENV-003`, `BR-UPG-003`, `FR-UPG-SEQ-001` | Dùng `ERR-UPG-409-03` | Đã xử lý ở DOC-SRS-QP-ERR-001 v1.0.1 ([error-matrix.md](error-matrix.md) §3.11) | BA — đã đóng |
| 5 | Không có mã lỗi khi SHA-256 gói CLI đẩy lên server lệch | `BR-FLT-003` | Dùng `ERR-FLT-422-03` | Đã xử lý ở DOC-SRS-QP-ERR-001 v1.0.1 ([error-matrix.md](error-matrix.md) §3.13) | BA — đã đóng |
| 6 | Không có mã lỗi khi vượt giới hạn 3 luồng SSE mỗi phiên / 10 luồng toàn console | `BR-JOB-007` | Dùng `ERR-JOB-429-02` | Đã xử lý ở DOC-SRS-QP-ERR-001 v1.0.1 ([error-matrix.md](error-matrix.md) §3.3) | BA — đã đóng |
| 7 | Bước nâng dependency P4 chạy `composer update` trên `$COPY`; `--no-scripts --no-plugins` chỉ bắt buộc cho phân tích lúc lập kế hoạch | `BR-CMPT-003`, `BR-CMPT-004`, mục `CHK-PHP-*-22` | Sơ đồ ghi đúng lệnh của checklist | Áp `--no-scripts --no-plugins` cho cả bước P4 để không chạy mã của package khi nâng | PO + kỹ sư bảo mật |
| 8 | Runtime trong container (`BR-ENV-009`) bị khoá (b)(c)(e) nhưng không có mã lỗi riêng | `BR-ENV-009`, DOC-SRS-QP-ENV-001 §2.3 bước 1 | Không vẽ nhánh này trong DIAG-SEQ-QP-UPG-001 | Bổ sung mã lỗi hoặc ghi rõ dùng issue cảnh báo kèm hướng dẫn PB-013 | BA |
| 9 | Chu kỳ cập nhật trạng thái đợt chạy Phase 2 chưa định nghĩa | `FR-FLT-EXEC-002`, API `GET /api/v1/fleet-runs/{fleet_run_id}` | Browser gọi `GET` định kỳ | Đề xuất 5 s, hoặc SSE như `FR-JOB-LOG-002`; chốt ở bước thiết kế API | PO + Dev |
| 10 | Giả định: audit intent/result của thao tác thay đổi hệ thống do CLI ghi (một đường thực thi cho CLI và console); console chỉ ghi sự kiện riêng (phát hành token, đăng nhập, huỷ job, đổi canary) | `C-SRS-05`, `FR-JOB-AUD-001`, `NFR-REL-002` | Cổng A nằm trong CLI | Ghi rõ trách nhiệm ghi audit ở `FR-JOB-AUD-001` | Dev |

### 6.3 Mã lỗi và mã mới của tài liệu này
**Mã lỗi**: tài liệu này không định nghĩa mã `ERR-*`. 3 mã do bản 1.0.0 đề xuất đã được định nghĩa chuẩn tại DOC-SRS-QP-ERR-001 từ v1.0.1, cùng HTTP, localization key và mức độ với đề xuất (error-matrix.md §5 mục 4); điều kiện phát sinh, thông báo VI/EN, thông báo kỹ thuật và hướng xử lý tra tại ma trận:
- `ERR-JOB-429-02` — [error-matrix.md §3.3](error-matrix.md) (Job runner `JOB`).
- `ERR-UPG-409-03` — [error-matrix.md §3.11](error-matrix.md) (Nâng cấp `UPG`).
- `ERR-FLT-422-03` — [error-matrix.md §3.13](error-matrix.md) (Phase 2 `FLT`).

**Mã tài liệu và mã sơ đồ** (rule 18):

| Mã | Loại | Phạm vi | Ghi chú |
| :--- | :--- | :--- | :--- |
| `DOC-SRS-QP-FLOW-001..003` | Mã tài liệu | 3 file sơ đồ tuần tự | Frontmatter rule 18 |
| `DIAG-SEQ-QP-FEED-002`, `-FEED-003`, `-SCAN-001`, `-PLAN-001`, `-PTCH-001`, `-UPG-001`, `-UPG-002`, `-UPG-003`, `-AUTH-002`, `-FLT-001` | Mã sơ đồ | 10 sơ đồ tuần tự | `related_diagrams` của rule 18; không trùng DIAG-SEQ-QP-AUTH-001, DIAG-SEQ-QP-FEED-001 đã phát hành |

### 6.4 Tài liệu tham chiếu
| Nguồn | Dùng cho | Trạng thái |
| :--- | :--- | :--- |
| Biên bản `docs/php-quickpatch/brainstorms/quickpatch-v2-console.md` (DOC-BRS-QP-001) | Quyết định PO: console Python 3 thư viện chuẩn, token + `127.0.0.1`, cài song song + chuyển từng site + rollback 1 lệnh, không agent; ngoài phạm vi: tool không sửa mã nguồn khách hàng | Đã đọc |
| SRS: [spec.md](spec.md), [functional-requirements.md](functional-requirements.md), [business-rules.md](business-rules.md), [error-matrix.md](error-matrix.md), [nfr.md](nfr.md) | Mã FR/BR/ERR/NFR/UC/SCR, danh mục API §3.3.3, danh sách trắng §3.3.4, sơ đồ trạng thái kế hoạch/job §4.1 | Đã đọc |
| Bản 1.0.1: [business-rules.md](business-rules.md) 1.1.0 (`BR-CON-004` ngoại lệ 2, `BR-CON-005`, `BR-JOB-003`, `BR-JOB-008`, §6 mục 2); [error-matrix.md](error-matrix.md) 1.1.0 (§2.1, §3.3, §3.11, §3.13, §5 mục 4, 5, 7); [spec.md §3.3.4](spec.md) 1.1.0 (argv `feeds_import`); [data-sources-cache-cli.md](data-sources-cache-cli.md) 1.0.1 §2.5, §4.3, §6.2 (`--dry-run` của `feeds import`); [api-spec.md §2.13.3](../api/api-spec.md), [api-spec-core.md §6.2](../api/api-spec-core.md) (2 bước `POST /api/v1/feed-snapshots`) | Vẽ lại DIAG-SEQ-QP-FEED-003, đóng §6.2 mục 1, 4–6, thay bảng §6.3 bằng liên kết, đếm lại độ phủ §6.1 | Đã đọc 2026-10-22 |
| [data-sources.md §5, §7](data-sources.md), [data-sources-cache-cli.md §2–§6](data-sources-cache-cli.md) | `BR-FEED-001..016`, `ERR-FEED-*`, thứ tự nguồn, bundle nguyên tử, snapshot, `feeds status` | Đã đọc |
| [environment-playbooks.md](environment-playbooks.md), [environment-playbooks-healthcheck.md](environment-playbooks-healthcheck.md), [version-scenarios-common.md](version-scenarios-common.md) | Playbook, C1–C12, R1–R7, health check, giai đoạn P1–P6 | Đã đọc |
| `/home/user/php-quickpatch/php-quickpatch.sh` v0.1.0 | Hành vi kế thừa: `flock -n 9` trên `STATE_DIR/.lock`, `ensure_backup_dir`/`backup_file`/`record` (manifest), `do_rollback` phát lại bằng `tac` rồi restart dịch vụ, `osv_check` (OSV `querybatch`), `restart_php_services`, mã thoát 0/1/2 | Đã đọc (grep hàm, 2026-10-22) |
| OpenBA-Kit `skills/sequence/SKILL.md`, `_templates/15-sequence-diagram.md`, `rules/01`, `rules/10`, `rules/16`, `rules/18`, `rules/19` | Cấu trúc, `autonumber`, `alt Hợp lệ`/`else Lỗi`, mã ERR tại điểm rẽ nhánh, response rules/10, frontmatter, lịch sử sửa đổi | Đã áp dụng |
| Mermaid — Sequence diagrams, https://mermaid.js.org/syntax/sequenceDiagram.html | Khối `alt/else`, `opt`, `loop`, `par/and`, `break`; "use `#59;` to include a semicolon in message text"; từ "end" có thể làm hỏng sơ đồ | Kiểm chứng (WebFetch 2026-10-22) |
| Mermaid 11.4.1 + jsdom 24.1.0 (`mermaid.parse`) | Kiểm cú pháp 10/10 sơ đồ; kiểm thêm 0 ký tự `;` và `#` trong khối Mermaid. Chạy thử cho thấy `#` làm mất phần sau của thông điệp mà không báo lỗi, `;` tách dòng gây lỗi cú pháp | Chạy thử 2026-10-22, đạt |
| WHATWG HTML — Server-sent events, https://html.spec.whatwg.org/multipage/server-sent-events.html | `EventSourceInit` chỉ có `withCredentials`; comment `:` khoảng 15 s giữ kết nối; `retry` (ms); `Last-Event-ID` khi nối lại | Kiểm chứng (WebFetch 2026-10-22) |
