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
