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
