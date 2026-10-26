# Mâu thuẫn tài liệu và cách xử lý — Phase 1

Quy tắc: FR/BR/ERR trong `docs/php-quickpatch/srs/` là nguồn sự thật (`BR-DATA-004`). Mâu thuẫn **làm đổi hành vi so với thiết kế** phải hỏi PO trước khi làm; các mục dưới ghi rõ loại.

Loại: **A** = chỉ khác câu chữ/số đếm, không đổi hành vi; **B** = chọn theo FR/BR/ERR, hành vi vẫn đúng thiết kế; **C** = đổi hành vi so với thiết kế → cần PO duyệt trước khi làm.

| Mã | Mốc | Mô tả | Nguồn | Xử lý | Loại | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| C-01 | M1 | `FR-CLI-JSON-001` không liệt kê trường `schema_version`; DOC-API-QP-005 §3.1 thêm `schema_version` (ĐX); handoff yêu cầu envelope có `schema_version` | FR §11, api-spec-cli-json §3.1, handoff §5 | Thêm `schema_version` và `command.subcommand/job_id/actor` (chỉ thêm trường, `BR-CLI-001`) | A | Áp dụng |
| C-02 | v0.1.1 | `manifest` sai loại (vd là thư mục): FR-PTCH-RBK-002 chỉ cho `reason` ∈ {`symlink`, `not_dir`, `owner`, `mode`} | FR-PTCH-RBK-002, ERR-CLI-412-01 | Dùng `reason=not_dir` cho mọi trường hợp "sai loại" (kể cả `manifest` không phải file thường) | A | Áp dụng |
| C-03 | M1–M6 | `CR-FR-01..08` trong FR §15.2 ghi "chờ PO duyệt" nhưng nội dung đã nằm trong FR, ERR (error-matrix 1.1.0), API, AC/TC | FR §15.2 | Triển khai theo FR; `CR-FR-02` đã làm ở v0.1.1. **Đề nghị PO xác nhận** ở báo cáo M1 (ảnh hưởng: `migrate ack`, sao lưu WordPress bằng tar, `docker-created`, kiểm dịch vụ sau restart thoát 2, mitigation có dòng `qp-rules`, bỏ qua SIGHUP/SIGPIPE) | B | Chờ PO xác nhận, mặc định làm theo FR |
| C-04 | M1 | `CR-SRS-06`: v0.1 lấy khoá độc quyền cho mọi lệnh; v2 dùng khoá chia sẻ cho lệnh đọc (`BR-JOB-002`) | spec §4.3 | Làm theo `BR-JOB-002`; ghi vào CHANGELOG | B | Áp dụng |
| C-05 | v0.1.1 | Mã `rollback <ID>` không đúng `YYYYmmdd-HHMMSS` bị từ chối (thoát 2); FR không nêu riêng, nhưng `BR-CON-008` quy định định dạng `run_id` | BR-CON-008 | Giữ trong v2 (`ERR-CLI-400-01`) | B | Áp dụng, đã báo PO |
| C-06 | M6 | Số endpoint: DOC-API-QP-001 ghi 57 (Phase 1: 44); spec 1.1.0 §3.3.3 có 58 (Phase 1: 45, thêm `POST /api/v1/switches/{run_id}/acknowledgements` của `CR-FR-01`) | spec §3.3.3, api-spec §3 | Làm 45 endpoint Phase 1 theo spec | A | Áp dụng |
| C-07 | M3 | DOC-API-QP-005 §7 liệt kê `command.subcommand` của `plan` thiếu `complete`, `close`, `canary`, `waive` (ghi "nếu CR được duyệt"); FR-CLI-CMD-002 1.1.0 đã có | FR-CLI-CMD-002 | Làm đủ theo FR | B | Áp dụng |
| C-08 | M2 | `feeds status`: DOC-SRS-QP-FEED-003 §6.4 in trường ở cấp cao nhất; DOC-API-QP-005 §10 đặt trong `result` của envelope | api-spec-cli-json §10 | Theo `FR-CLI-JSON-001` (envelope chung) → trong `result` | B | Áp dụng |
| C-09 | — | OpenBA-Kit (`luongkam/OpenBA-Kit`) không gắn được vào phiên (GitHub trả "không có quyền"); tài liệu chỉ dùng nó cho quy ước soạn tài liệu | handoff §1 | Không ảnh hưởng mã; kế hoạch viết theo quy ước sẵn có trong `docs/` | A | Đã báo PO |
| C-10 | M1–M7 | `Q-SRS-02..09` (spec §4.4) không nằm trong danh sách PO đã chốt (`Q-01..Q-09`, `Q-SRS-01`) | spec §4.4 | Dùng đề xuất SRS làm mặc định: gửi tên package/image tới registry khi lập kế hoạch (`--offline` tắt); phiên 30 phút/12 giờ/5 phiên; lệnh ghi mới không TTY cần `--yes`; đích thủ công cần lý do ≥ 20 ký tự; Bash ≥ 4.3; CloudLinux/DirectAdmin xác nhận kép; benchmark NFR do QA | B | Báo PO ở M1 |
| C-11 | M1 | `ERR-CLI-424-02`: error-matrix ghi "Bash 4.3+, flock and curl are required"; TC-CLI-029 ghi "Bash 4.3+ and flock are required"; FR-CLI-ENV-001 chỉ dừng khi thiếu Bash 4.3/`flock` | error-matrix §3.5, FR-CLI-ENV-001 | Dùng câu chữ của error-matrix; chỉ dừng khi Bash < 4.3 hoặc thiếu `flock` (theo FR), `curl` chỉ ghi trong chi tiết | A | Áp dụng |
| C-12 | M1 | v0.1 lọc webshell bằng `find -size -2M` (thực tế chỉ đọc file ≤ 1 MiB do làm tròn); FR-SCAN-WSH-001 ghi "< 2 MB" | FR-SCAN-WSH-001 | Theo FR: `-size -2097152c` (< 2 MiB); file 1–2 MiB nay cũng được quét | B | Áp dụng, ghi CHANGELOG |
| C-13 | M1 | TC-PTCH-002 ghi nhóm gói dạng biểu thức (`ea-php[0-9]+`), mã trả về tiền tố thật của gói (`ea-php82`) để dùng làm glob như v0.1 | BR-PTCH-002 | Kiểm theo tiền tố; không đổi hành vi | A | Áp dụng |
| C-14 | M2 | TC-PTCH-003, TC-PTCH-018 ghi issue mức `critical`; `FR-CLI-COMP-002` + DOC-SRS-QP-FEED-003 §3.4 quy định mức `critical`/`high` lấy từ điểm rủi ro (PHP 8.2.34 → R = 60 `HIGH`) | FR-CLI-COMP-002, TC-PTCH-003/018 | Theo FR: mức issue = mức của R; test cập nhật | B | Áp dụng, báo PO ở M2 |
| C-15 | M2 | Ví dụ §8.5 số 2 và 5 của DOC-SRS-QP-FEED-002 (PHP 8.4.26: 2 critical) khác dữ liệu NVD ngày 2026-10-24: NVD Primary 3.1 chấm CVE-2026-109619 = 8,1 (`high`) → 1 critical + 1 high, R = 45 | merge-risk §8.5, BR-FEED-028 | Công thức kiểm bằng đúng đầu vào của bảng §8.5 (11 ví dụ + RT-1/RT-2, Bash và Python); số đếm thật lấy theo `BR-FEED-028` | A | Áp dụng |
| C-16 | M2 | `BR-SCN-002` ưu tiên php.net cho ngày vòng đời PHP; merge-risk §4.1 / `BR-FEED-020` đặt `SRC-001` trước `SRC-003` (`eol.php`) | BR-SCN-002, BR-FEED-020 | Theo `BR-FEED-020` (§4.1); lệch > 3 ngày ghi `ERR-FEED-409-01` (vd PHP 5.4: 2015-09-14 vs 2015-09-03) | B | Áp dụng |
| C-17 | M2 | M1 dùng 1 schema `qp.feeds/1` cho mọi lệnh con; DOC-SRS-QP-FEED-003 §6.2, §7 quy định `qp.feeds.<lệnh con>/1` | FR-FEED-CMD-001..006 | Tách `qp.feeds.update|verify|export|import|schedule/1`; `qp.feeds/1` chỉ còn cho lỗi lệnh con không hợp lệ | B | Áp dụng |
| C-18 | M3 | `risk.components`: data dictionary DOC-SRS-QP-FEED-002 §2.2 ghi khoá `{cvss,count,kev,life,eol,floor}`; DOC-API-QP-005 §5.1/§6 và TC-ASMT-001 ghi `{S_cvss,S_cnt,S_kev,S_life,S_eol}` dạng số; FR-ASMT-RISK-001 ghi `risk.score`, DOC-API-QP-005 ghi `risk.R` | api-spec-cli-json §5.1, TC-ASMT-001 | Theo hợp đồng CLI + TC: `S_*` là số (1 chữ số thập phân, cùng cách tính số nguyên phần mười), thêm `floor`, `R_raw`; có cả `R` và `score` (cùng giá trị). Đổi so với M2 (chuỗi `cvss`/`count`…) | B | Áp dụng |
| C-19 | M3 | BR-SCN-040 bước (1) cần `pre-release-builds.php?format=json` của php.net nhưng danh mục nguồn `SRC-001..017` (DOC-SRS-QP-FEED-001) không có nguồn này | BR-SCN-040 | Thu thêm trong `SRC-002` (php.net), khoá `prerelease_url` trong `sources.conf`; nhánh có bản pre-release → dòng `lifecycle.tsv` không `ga_date`, có `prerelease_date`, `latest_hint`. Không lấy được → giữ fact cũ; không có dữ liệu → bản `8.6.0RC4` vào `SCN-PHP-005` (vẫn khoá) | A | Áp dụng |
| C-20 | M3 | Trường `environment` của `scan --json`: DOC-SRS-QP-ENV-001 §6 (`FR-SCAN-ENV-001`) ghi `{pb_provider, pb_bindings[], pb_node[], in_container, evidence[]}`; DOC-API-QP-005 §5 ghi `{os_id, …, playbooks[{pb_id, layer}], restrictions[]}` | FR-SCAN-ENV-001, api-spec-cli-json §5 | Xuất hợp của 2 tập trường (chỉ thêm trường) | A | Áp dụng |
| C-21 | M3 | TC-SCN-013 KQ2 mô tả mục "(khi nâng)" mở rộng thành mục con theo từng package; tài liệu kịch bản (vd `CHK-PHP-011-11` "Như `CHK-PHP-010-13` … `-17`") cho thấy mục "(khi nâng)" là tập các mục mẫu | FR-SCN-CHK-001 | Mở rộng thành mục con `-NN` theo mục mẫu được tham chiếu; mở rộng theo package làm cùng `upgrade_items` (M4) | B | Áp dụng; M4 đã thay mục mẫu P4 bằng mục con theo từng package (TC-SCN-013 KQ2 đạt) |
| C-22 | M3 | TC-ASMT-001 kỳ vọng `cve_counts.critical = 2`, `R = 60` cho PHP 8.2.34; dữ liệu NVD thật (C-15) cho 1 critical + 1 high, R = 58; bảng so sánh §6: 8.2.35/8.3.36/8.5.12 = 40/20/0 đúng, `delta_R` lệch 2 | C-15 | Test kiểm R của ứng viên theo bảng §6 và `delta_R = R − R(hiện tại)`; số đếm theo dữ liệu thật | A | Áp dụng |
| C-23 | M4 | `blocked_sites[]`: FR-PLAN-GEN-002 ghi danh sách site; schema `qp.plan/1` (DOC-API-QP-005 §7) là mảng `{site_id, reason}` | FR-PLAN-GEN-002, api-spec-cli-json §7 | Xuất `{site_id, reason}` theo schema | A | Áp dụng |
| C-24 | M4 | `plan waive` với hit không thuộc site: FR-CLI-CMD-002 liệt kê `ERR-PLAN-404-01`; api-spec-plans §4.2 ghi `ERR-CON-422-01` (`details.field = hit_ids`) cho hit không thuộc site hoặc không ở mức `error` | FR-CLI-CMD-002, api-spec-plans §4.2 | `ERR-CON-422-01` cho hit sai; `ERR-PLAN-404-01` cho kế hoạch/site không có. Test M3 đổi kỳ vọng theo | A | Áp dụng |
| C-25 | M4 | TC-CMPT-012 kỳ vọng `Parse error` cho file hỏng trên 8.5; với PHP 8 một số lỗi cú pháp cũ (vd `$s{0}`) là `Fatal error` lúc biên dịch | TC-CMPT-012 | Nhận cả `Parse error` và `Fatal error` của `php -l` là lỗi cú pháp (hit `php-l`, mức `error`); fixture dùng `function match()` (Parse error từ 8.0) | A | Áp dụng |
| C-26 | M4 | Mục "Mẫu quét" của luật BC trong DOC-SRS-QP-SCN-PHP-8X là mô tả, không phải regex chạy được | version-scenarios-php-8x | Regex soạn tay trong `tools/build-catalog.py` (`SCAN`), kiểm biên dịch khi build; phát hiện ngữ nghĩa (vd so sánh lỏng chuỗi–số) vẫn để PHPCompatibility/test | B | Áp dụng |
| C-27 | CR-01 | Lệnh `compat --path` (quét thư mục dự án Node.js với nhánh đích + báo cáo) không có trong FR Phase 1 | PO yêu cầu 2026-10-26 | Thêm lệnh mới, không đổi lệnh có sẵn; mô tả ở [cr-01-compat-path.md](cr-01-compat-path.md). Cần PO bổ sung FR/AC/TC vào SRS nếu giữ cho bản phát hành | C | PO đã yêu cầu; chờ cập nhật SRS |
| C-28 | M5 | Nhiều tiêu chí vi phạm trong cùng 1 vòng: `rollback_reason` là 1 mã (`HC-C0..C9`) nhưng tài liệu HC không nói chọn mã nào; mã 5xx luôn vi phạm cả `HC-C1` | DOC-SRS-QP-ENV-002 §6, states.md `T-SW-11` | `rollback_reason` = `HC-C2` khi có, ngược lại mã nhỏ nhất; mọi tiêu chí vẫn có trong `hc.violations[]` | A | Áp dụng |
| C-29 | M5 | `rollback <run_id>` của lượt có dòng `switch` (states.md `T-SW-15`): api-spec-cli-json §8 chỉ mô tả `qp.fix/1` cho `rollback` | states.md, api-spec-cli-json §8, §9 | Chạy R1–R7 của `migrate rollback --purge-pool`; xuất `qp.migrate/1` (`command.name = migrate`, `subcommand = rollback`) | A | Áp dụng |
| C-30 | M5 | `BR-PLAN-006`: `scan_fingerprint` gồm `site_binding`; mỗi lượt chuyển `PASSED` đổi gán site → lần `scan` kế tiếp làm kế hoạch `stale` (`SCAN_CHANGED`) và `FR-UPG-SEQ-001` từ chối site kế tiếp (`ERR-PLAN-410-01`) | BR-PLAN-006, FR-UPG-SEQ-001 | Giữ đúng thiết kế (kiểm `stale` trước mỗi lượt chuyển); người vận hành không chạy `scan` giữa các lượt chuyển hoặc tạo lại kế hoạch. Đề xuất PO: loại phần gán của các site đã chuyển bởi chính kế hoạch khỏi so sánh | C | Chờ PO |

## Giả định khi triển khai M2 (không đổi hành vi so với thiết kế)

| Mã | Nội dung |
| :--- | :--- |
| A-M2-01 | Bundle có thêm `sources.tsv` (trạng thái nguồn, để Bash tính tuổi dữ liệu không cần Python) và `parts.json.gz` (fact công khai của từng nguồn, để đồng bộ tăng dần sau snapshot); các TSV có thêm cột cuối (`latest_hint`, `codename`, `lts_codename`, `cvss_rep_src`, `used`, `semver_vulnerable`, `semver_patched`, `fixed_in_branch`, `v_prefix`) — chỉ thêm, không đổi thứ tự cột của §3.2 |
| A-M2-02 | Advisory không nguồn nào chấm điểm (`cvss_rep = null`) được tính như mức `unknown` = 7,5 khi xét `S_sec`, đếm mức và tính R (`BR-FEED-043` "không rõ") |
| A-M2-03 | Advisory tạm `BR-FEED-024` chỉ sinh cho bản bảo mật mới nhất của mỗi nhánh (chỉ bản này có thể nâng `min_patched`); thời điểm phát hiện = min(lần thấy đầu, ngày phát hành) |
| A-M2-04 | `SRC-009` lỗi → bản mới nhất của `SRC-001` (`CROSS:SRC-001`) cộng các bản đã có trong cache; 1 phiên bản không lấy từ 2 tầng dự phòng (`BR-FEED-006`) |
| A-M2-05 | Nhánh đã EOL có CVE chưa sửa → `NONE` (không bao giờ `PENDING_RELEASE`) |
| A-M2-06 | Bash tính phơi nhiễm từ `exposure.tsv`; phiên bản không có trong đó thì so dải `affected.tsv` bằng `awk` (bỏ dải semver Node WG — mọi bản Node.js đều có trong `exposure.tsv`) |
| A-M2-07 | CVE nêu ở nguồn khác mà NVD chưa có, CVE.org trả 404 → bản ghi `RESERVED` không có dải (không khớp phiên bản nào) |
| A-M2-08 | Ngân sách mặc định 900 s khi chưa có dữ liệu NVD và chưa có bundle, còn lại 180 s; `scan` gọi `feeds update --budget 110` (giới hạn chờ 120 s) |
| A-M2-09 | `scan`/`fix` chỉ mở bundle khi có kiểm tra php/node/wp/docker/composer/npm; mã thoát 2 vì "không có dữ liệu" chỉ khi có kiểm tra runtime/WordPress/image |
| A-M2-10 | Snapshot đóng gói chưa kèm repo tới M7 (`QP_SNAPSHOT_SHA256` rỗng): máy không mạng, không bundle → `ERR-FEED-503-01`, thoát 2 |
| A-M2-11 | `BR-FEED-012` (không Python thì `feeds update` chỉ tải raw) chưa làm: `feeds` cần Python (`ERR-CLI-424-01`); `scan`/`fix`/`rollback` vẫn chạy không Python với bundle/snapshot |
| A-M2-12 | Fixture `tests/fixtures/feeds` lấy từ nguồn thật ngày 2026-10-24; trạng thái vòng đời tính theo ngày chạy test, nên một số kỳ vọng (vd PHP 8.2 hết hạn 2026-12-31) sẽ phải cập nhật khi dữ liệu fixture được làm mới |

## Giả định khi triển khai M3 (không đổi hành vi so với thiết kế)

| Mã | Nội dung |
| :--- | :--- |
| A-M3-01 | Catalog sinh bằng `tools/build-catalog.py` từ các bảng Markdown; `catalog_version` = `2026.10.24-1`. Trường thêm của mục checklist: `flow` (`both` = luồng vá cùng nhánh, `upgrade` = chỉ khi đổi nhánh), `refs` (mục mẫu "Như …"), `expand`, `optional` ("(Tuỳ chọn)"), `manual_condition` (điều kiện "(khi có …)" người vận hành tự xét) |
| A-M3-02 | Kế hoạch `same_branch` đặt `SKIPPED` cho mục `flow=upgrade` (các kịch bản 001–010 không gắn nhãn "(khi nâng)" cho luồng nâng cấp) |
| A-M3-03 | `cli_action` chỉ có cho `scan`, `assess`, `fix`; mục P1 `AUTO` trả lời được bằng `scan`/`assess` được đặt `DONE` khi tạo kế hoạch (bằng chứng: dấu vân tay scan + bundle) |
| A-M3-04 | Mục theo site: P3–P5, P6 (trừ cron/pm2), mục "baseline"/"mỗi site"; khoá mục trong kế hoạch là `chk_id@site_id`, CLI nhận `CHK@SITE` hoặc `--site`. Runtime không có site → mục theo site `SKIPPED` ("no site uses this runtime") |
| A-M3-05 | `applies_when` 3 trạng thái: không thoả → `SKIPPED`; chưa xác định (framework khác WordPress, loader, site không có docroot) → `PENDING` (T-CHK-01). Framework chỉ nhận WordPress (`wp-includes/version.php`); loader/framework khác ở M4 |
| A-M3-06 | `mitigations.json`: 3 luật `MIT-PHP-001..003` kế thừa v0.1 (CVE PHP2Shell, `memory_limit` theo `--no-memlimit`, `fatal_error_backtraces` chỉ 8.5); không luật nào khớp CVE chưa vá → không ghi file. Không có catalog → dùng 3 luật gắn sẵn trong script |
| A-M3-07 | PB-000 + `ERR-ENV-422-01` khi mọi binary PHP không khớp playbook cung cấp và không có playbook gán site (bước 6); `pb_id` của từng runtime vẫn có thể là PB-000 (vd PHP tự build cạnh Nginx) |
| A-M3-08 | Site có trong file cấu hình web server nhưng không được tiến trình nào nạp → `sites[]` với `pb_id = PB-000`, `binding_kind = unmapped`, issue `high` `ERR-ENV-422-02`; mục checklist của site này ở mức `MANUAL` |
| A-M3-09 | `assess`/`plan` dùng `state/last-scan.json` (do `scan` ghi, mọi chế độ text/JSON); chạy `scan --only php,node,sites` khi file cũ hơn 24 giờ hoặc thiếu runtime. Ngày T lấy từ `--today` / `QP_TODAY` (kiểm thử) |
| A-M3-10 | Ứng viên nhánh không phải `RECOMMENDED`: bắt buộc `--reason`; nhánh không có trong danh sách ứng viên nhưng còn hỗ trợ (vd Node.js 24 cho runtime 20) được chọn với lý do (`override_reason`) |
| A-M3-11 | Node.js `CURRENT` trước ngày LTS: coi mọi site là production (chưa có cờ môi trường) → `selectable=false` |
| A-M3-12 | Kế hoạch `in_progress`: một lần chạy `fix` thoát 1 vì runtime khác vẫn được tính `DONE` cho mục khi không có hành động lỗi của runtime của kế hoạch (T-CHK-06) |
| A-M3-13 | Khoá ghi kế hoạch: `STATE_DIR/plans/.lock` (độc quyền, chờ ≤ 10 s), không dùng `STATE_DIR/.lock` để `scan` chạy song song được |

## Giả định khi triển khai M4 (không đổi hành vi so với thiết kế)

| Mã | Nội dung |
| :--- | :--- |
| A-M4-01 | Quét chạy trong `plan create` (chế độ `cross_branch`), ngoài khoá `plans/.lock`; kết quả theo site ở `plans/<plan_id>/compat/<site_key>.json`. Kế hoạch `same_branch` không quét tương thích |
| A-M4-02 | Phần "chạy được trước khi cài" của `BR-PLAN-003` = quét luật BC (`code_scan`); PHPCompatibility khi offline/không có công cụ, `php -l`, `check-platform-reqs`, addon chờ `$NEW_BIN` không chặn duyệt |
| A-M4-03 | Composer blocker (không thuộc dev), vi phạm `engines.node` mức error, addon không nạp được làm kết luận `FAIL` nhưng không phải hit miễn trừ được; chỉ hit mức `error` được miễn trừ (`ERR-CON-422-01`) |
| A-M4-04 | Rector + PHPStan (~108 MB) chỉ cài khi chạy mục Rector; nhóm PHPCompatibility + Composer 14 MB (TC-CMPT-001 KQ3 ≤ 80 MB đạt khi chưa bật Rector) |
| A-M4-05 | Công cụ cài từ commit git ghim + SHA-256 của `git archive --format=tar` (zip dist GitHub bị proxy chặn); catalog vẫn có chỗ cho `dist_url`/`dist_sha256` |
| A-M4-06 | Thứ tự site: `PASS` → `PENDING` → `FAIL`; trong cùng nhóm, site chưa quét được mã (docroot không đọc được) xếp sau, rồi số file PHP tăng dần, rồi `site_id`. Canary người vận hành chọn được giữ khi quét lại |
| A-M4-07 | Mục P3 có phần quét tương ứng: mọi phần `done` + 0 phát hiện chưa xử lý → `DONE`; có phát hiện → `FAILED` (chặn P5 qua phụ thuộc); phần còn chờ → `PENDING`. Miễn trừ hết hit → mục về `DONE` |
| A-M4-08 | Mỗi dòng `upgrade_items` (trừ npm chỉ ở devDependencies) thành 1 mục P4 con `-NN` của mục P4 khớp loại; mục mẫu "(khi nâng)" bị thay được giữ để dựng lại; extension 0 lời gọi → mục con `SKIPPED`; framework ngoài ma trận → mục con `MANUAL` xác nhận dải PHP |
| A-M4-09 | Lệnh thêm `plan compat ID [--site] [--level] [--rule] [--waived]` (đọc) cho `GET /plans/{id}/compatibility` (M6); `plan run` mục quét quét lại khi `scan_fingerprint`/đích/catalog/công cụ đổi, ngược lại dùng lại kết quả (TC-CMPT-030 KQ3) |
| A-M4-10 | Rector: `--dry-run` (hoặc không cờ) → diff `plans/<id>/rector-<site_key>.diff`, mục giữ `PENDING`; `--yes` chỉ chạy khi đã có diff, ghi bản sao `STATE_DIR/work/<id>/<site_key>/rector-src`, mục `DONE`. File Rector không phân tích được được liệt kê, không làm hỏng lần chạy |
| A-M4-11 | Ứng dụng Node.js chạy bằng unit systemd là site `app:systemd:<unit>` (docroot = `WorkingDirectory`, PB-017); pm2/Docker chưa thành site |
| A-M4-12 | `catalog_version` = `2026.10.25-1` (thêm `scan[]`, bảng ini/extension/framework, công cụ ghim, `cli_action` cho mục quét) |
| A-M4-13 | Thư mục `sites.d` khai báo "không triển khai": `/etc/php-quickpatch/sites.d/<site_key>.conf` (root) hoặc `~/.config/php-quickpatch/sites.d/` (không root); dòng đầu `# qp-site-id = <site_id>`; `exclude_dirs`, `exclude_reason` ≥ 20 ký tự |

## Giả định khi triển khai M5 (không đổi hành vi so với thiết kế)

| Mã | Nội dung |
| :--- | :--- |
| A-M5-01 | `migrate` (install/switch/rollback/healthcheck/ack/status/hc-urls/remove-old) viết bằng Bash trong `share/php-quickpatch/lib/{migrate,hc,pb,install}.sh`, nạp khi chạy `migrate` (C-01); Python chỉ cho FastCGI probe/kiểm pool (`qp-feeds.py fcgi`) và kiểm kế hoạch (`qp-feeds.py plan-gate`) |
| A-M5-02 | `run_id` của lượt chuyển = tên thư mục `backups/<run_id>`; `switches/index.tsv` thêm cột `site_key`, `note` (dòng `ack:<thời điểm>` khi xác nhận); `switch.vars` (key=value) là bản Bash của `switch.json` |
| A-M5-03 | Kiểm HC-C0 (C10, §3.4 cách 1): `accepted conn` của trang status pool đích tăng thêm ít nhất 1 ngoài chính các yêu cầu status (mỗi lần hỏi status cũng được đếm); thử lại tối đa 10 lần vì reload graceful có hiệu lực sau khi gửi tín hiệu. Vòng thăm dò sau rollback cũng thử lại ≤ 10 lần |
| A-M5-04 | Mọi yêu cầu health check dùng `curl --noproxy '*' --resolve <host của URL>:<port>:<địa chỉ vhost>`: biến `http_proxy` của máy không làm lệch kết quả; URL khai báo với host phụ (`www.`) được trỏ đúng địa chỉ |
| A-M5-05 | Ghim mặc định (`BR-SCN-012`) ghi manifest `link alt:<nhóm> <Value>|auto`; rollback lượt cài chạy `update-alternatives --set`/`--auto`. Gói đã cài không gỡ khi rollback (dòng `note`, như v0.1) |
| A-M5-06 | File kho/khoá do `add-apt-repository` tạo được ghi `created` sau khi lệnh chạy (tên không biết trước). Không có `add-apt-repository` dùng được → tool tự thêm `ppa:ondrej/php`: fingerprint từ Launchpad API, khoá từ keyserver.ubuntu.com, kiểm fingerprint bằng `gpg`, nguồn deb822 `Signed-By` riêng |
| A-M5-07 | `FR-UPG-CFG-002` "giá trị khác mặc định trong `php.ini`": so `php.ini` của `$OLD` với `/usr/lib/php/<OLD>/php.ini-production` của gói, ghi các dòng khác vào `conf.d/90-php-quickpatch-from-<OLD>.ini` của `$NEW` |
| A-M5-08 | `remove-old`: "xác nhận kép" của mục `SEMI` = `--yes` + `--reason` (≥ 20 ký tự). Bằng chứng 14 ngày: không site nào gán nhánh cũ, không tiến trình CLI của binary cũ, mtime log FPM/pool cũ và lượt chuyển `PASSED` cuối rời nhánh cũ ≥ 14 ngày. Node.js chỉ gỡ prefix `/opt/node-<major>` (lưu tar, rollback được) |
| A-M5-09 | Drift (`FR-SCAN-DRF-001`) so nhánh + endpoint (socket/cổng) với lượt `PASSED` gần nhất, không so `binding_ref` (số dòng đổi khi sửa file không liên quan) |
| A-M5-10 | `plan run` mục P5 `migrate switch` thêm `--yes` (đã xác nhận ở `plan run`); 1 lượt chuyển `PASSED` đặt `DONE` cho mọi mục P5 `migrate switch` của cùng site (mục "canary" và "từng site còn lại" cùng tồn tại cho mỗi site). `cli_action` P2/P5 chỉ cho mục cài song song / chuyển site trên chính máy (không cho "máy mới", nvm, prefix tự build) |
| A-M5-11 | `steps[]` của `install`/`remove-old` dùng tên `INST-*`/`RMV` (api-spec chỉ định nghĩa `C1..C12`, `R1..R7` cho switch/rollback) |
| A-M5-12 | Test switch chạy Nginx + PHP-FPM thật (2 nhánh) trong mount namespace với overlay `/etc`, `/var/lib`, `/var/log`, `/run` thay cho stub `nginx -t`/`systemctl` dự kiến ở mục 2 (giả lập lỗi bằng file cờ: không reload, `nginx -t` lỗi); `sleep` ≥ 5 s được tua nhanh |
| A-M5-13 | `catalog_version` = `2026.10.26-1` (thêm `cli_action` `migrate install`/`migrate switch`) |
| A-M5-14 | Không systemd: dịch vụ qua `service`; gói PHP của ondrej không đặt `pid =` nên script init không thấy tiến trình (môi trường test thêm `pid =`; máy dùng systemd không bị ảnh hưởng) |
