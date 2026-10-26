# M6 — Web console `qp-console.py`

Mục tiêu: `serve` chỉ bind `127.0.0.1` (cổng mặc định 17321), token 256-bit 1 lần, phiên cookie `qp_session_<port>_<iid>`, kiểm Host, CSRF, CSP, danh sách trắng hành động (`shell=False`), job runner + `flock` dùng chung với CLI, SSE log, đối soát job, 11 màn hình Phase 1 (SCR-001..011) theo wireframe, 45 endpoint `/api/v1` Phase 1.

## 1. Tài liệu chính
`api/api-spec.md` (quy chuẩn, cổng kiểm tra G1–G4, ánh xạ mã thoát → HTTP §2.14), `api-spec-core.md`, `api-spec-plans.md`, `api-spec-jobs.md`; `srs/states.md` (job, `serve`, phiên); `srs/erd-console-db.md`, `erd-console-ops.md`; `srs/flows-console-fleet.md` §2; `html-wireframe/*.html` (11 màn Phase 1); `srs/nfr.md` (`NFR-SEC-*`, `NFR-PERF-*`).

## 2. Thiết kế
- `http.server.ThreadingHTTPServer` (lớp tương đương cho 3.6), router tự viết; mọi lớp bảo vệ tự cài (`C-SRS-02`).
- `console.db` (SQLite) là bảng chiếu dựng lại từ tệp `STATE_DIR` (`NT-*` của erd.md).
- Giao diện: HTML/CSS/JS thuần nhúng trong `console/static/`, không CDN; CSP `default-src 'self'`.
- Job: `subprocess.Popen(argv, shell=False, stdin=DEVNULL, stdout=fd result.json, stderr=fd output.log, start_new_session=True, env=<danh sách trắng>)`.
- Test: `unittest` gọi HTTP thật tới console chạy trên cổng ngẫu nhiên; CLI thật với fixture; kiểm header bảo mật, Host 421, CSRF 403, giới hạn thử sai 429, SSE nối lại `Last-Event-ID`; thử giao diện bằng Playwright (Chromium có sẵn) cho luồng ≤ 4 thao tác.

## 3. Tiêu chí nghiệm thu
- Mọi endpoint Phase 1 trả envelope rules/10; mã lỗi đúng error-matrix.
- `NFR-SEC-001..006`: chỉ `127.0.0.1`, token 256-bit, Host/CSRF/CSP 0 ngoại lệ trong bộ test.
- Dry-run + xác nhận ≤ 15 phút (`BR-CON-005`), xác nhận kép cho hành động toàn máy chủ.
- 11 màn hình hiển thị dữ liệu thật từ CLI trên fixture; ảnh chụp màn hình lưu ở báo cáo mốc.

## 4. Chưa thử được trên máy thật (dự kiến)
Truy cập qua SSH tunnel thật từ máy người vận hành; hiệu năng P95 trên 2 vCPU/2 GB; trình duyệt Safari/Edge.

## 5. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-CON-AUTH-001` | Khởi động console bằng `serve` | P0 | `US-CON-01` | `AC-CON-01`, `AC-CON-02`, `AC-CON-03`, `AC-CON-04` | TC-CON-001, TC-CON-002, TC-CON-003, TC-CON-004 |
| `FR-CON-AUTH-002` | Sinh và hiển thị token phiên `serve` | P0 | `US-CON-01` | `AC-CON-01`, `AC-CON-03`, `AC-CON-04` | TC-CON-001, TC-CON-003, TC-CON-004 |
| `FR-CON-AUTH-003` | Đăng nhập bằng token và cấp phiên | P0 | `US-CON-02` | `AC-CON-05`, `AC-CON-06`, `AC-CON-07`, bổ sung | TC-CON-005, TC-CON-006, TC-CON-007, TC-CON-102 |
| `FR-CON-AUTH-004` | Xác thực mọi request, đăng xuất, hết hạn phiên | P0 | `US-CON-03` | `AC-CON-08`, `AC-CON-09`, `AC-CON-10` | TC-CON-008, TC-CON-009, TC-CON-010 |
| `FR-CON-AUTH-005` | Chặn DNS rebinding bằng kiểm tra Host | P0 | `US-CON-04` | `AC-CON-11`, `AC-CON-12`, `AC-CON-13` | TC-CON-011, TC-CON-012, TC-CON-013 |
| `FR-CON-AUTH-006` | Chống CSRF cho request ghi | P0 | `US-CON-05`, `US-CON-05` (FR) / `US-CON-02` (TC) | `AC-CON-14`, `AC-CON-15`, `AC-CON-16`, bổ sung | TC-CON-014, TC-CON-015, TC-CON-016, TC-CON-102 |
| `FR-CON-OVW-001` | Hiển thị màn hình Tổng quan (SCR-002) | P0 | `US-CON-06` | `AC-CON-17`, `AC-CON-18`, `AC-CON-19` | TC-CON-017, TC-CON-018, TC-CON-019 |
| `FR-CON-ASMT-001` | Hiển thị màn hình Đánh giá runtime và so sánh (SCR-003) | P0 | `US-CON-07` | `AC-CON-20`, `AC-CON-21`, `AC-CON-22` | TC-CON-020, TC-CON-021, TC-CON-022 |
| `FR-CON-PLAN-001` | Hiển thị màn hình Chọn phiên bản và sinh kế hoạch (SCR-004) | P0 | `US-CON-08` | `AC-CON-23`, `AC-CON-24`, `AC-CON-25` | TC-CON-023, TC-CON-024, TC-CON-025 |
| `FR-CON-PLAN-002` | Thao tác checklist trên console | P0 | `US-CON-09` | `AC-CON-26`, `AC-CON-27`, `AC-CON-28` | TC-CON-026, TC-CON-027, TC-CON-028 |
| `FR-CON-JOB-001` | Hiển thị màn hình Jobs & Log (SCR-006) | P0 | `US-CON-10` | `AC-CON-29`, `AC-CON-30`, `AC-CON-31`, bổ sung | TC-CON-029, TC-CON-030, TC-CON-031, TC-CON-103 |
| `FR-CON-JOB-002` | Huỷ job từ console | P0 | `US-CON-10` | `AC-CON-29`, `AC-CON-30` | TC-CON-029, TC-CON-030 |
| `FR-CON-DEP-001` | Hiển thị màn hình Findings thư viện (SCR-005) | P0 | `US-CON-11` | `AC-CON-32`, `AC-CON-33`, `AC-CON-34` | TC-CON-032, TC-CON-033, TC-CON-034 |
| `FR-CON-RBK-001` | Hiển thị màn hình Rollback và lịch sử (SCR-007) | P0 | `US-CON-12` | `AC-CON-35`, `AC-CON-36`, `AC-CON-37` | TC-CON-035, TC-CON-036, TC-CON-037 |
| `FR-CON-FEED-001` | Hiển thị màn hình Nguồn dữ liệu (SCR-008) | P0 | `US-CON-13` | `AC-CON-38`, `AC-CON-40` | TC-CON-038, TC-CON-040 |
| `FR-CON-FEED-002` | Nhập snapshot qua console | P1 | `US-CON-13` | `AC-CON-39`, `AC-CON-40`, `AC-CON-41` | TC-CON-039, TC-CON-040, TC-CON-041 |
| `FR-CON-SITE-001` | Hiển thị màn hình Site và ánh xạ runtime (SCR-009) | P0 | `US-CON-14` | `AC-CON-42`, `AC-CON-43`, `AC-CON-44` | TC-CON-042, TC-CON-043, TC-CON-044 |
| `FR-CON-AUD-001` | Hiển thị màn hình Audit và báo cáo (SCR-010) | P1 | `US-CON-15` | `AC-CON-45`, `AC-CON-46`, `AC-CON-47` | TC-CON-045, TC-CON-046, TC-CON-047 |
| `FR-CON-SAFE-001` | Xem trước dry-run và xác nhận (SCR-011) | P0 | `US-CON-16` | `AC-CON-48`, `AC-CON-49`, `AC-CON-50`, `AC-CON-51` | TC-CON-048, TC-CON-049, TC-CON-050, TC-CON-051 |
| `FR-CON-SAFE-002` | Phục vụ tài nguyên tĩnh nhúng kèm header bảo mật | P0 | `US-CON-17` | `AC-CON-52`, `AC-CON-53`, `AC-CON-54` | TC-CON-052, TC-CON-053, TC-CON-054 |
| `FR-CON-SAFE-003` | Kiểm tra hành động theo danh sách trắng và tham số | P0 | `US-CON-18` | `AC-CON-55`, `AC-CON-56`, `AC-CON-57` | TC-CON-055, TC-CON-056, TC-CON-057 |
| `FR-CON-API-001` | Tuân thủ hợp đồng API REST `/api/v1` | P0 | `US-CON-19`, `US-CON-19` (FR) / `US-CLI-03` (TC) | bổ sung, `AC-CON-58`, `AC-CON-59`, `AC-CON-60` | TC-CLI-101, TC-CON-058, TC-CON-059, TC-CON-060, TC-CON-101 |
| `FR-JOB-RUN-001` | Xếp hàng và chạy job | P0 | `US-JOB-01` | `AC-JOB-01`, `AC-JOB-02`, `AC-JOB-03` | TC-JOB-001, TC-JOB-002, TC-JOB-003 |
| `FR-JOB-RUN-002` | Dùng chung khoá với CLI | P0 | `US-JOB-02` | `AC-JOB-04`, `AC-JOB-05`, `AC-JOB-06` | TC-JOB-004, TC-JOB-005, TC-JOB-006 |
| `FR-JOB-RUN-003` | Huỷ job | P0 | `US-JOB-03` | `AC-JOB-07`, `AC-JOB-08`, `AC-JOB-09` | TC-JOB-007, TC-JOB-008, TC-JOB-009 |
| `FR-JOB-RUN-004` | Đối soát job sau khi console khởi động lại | P0 | `US-JOB-04` | `AC-JOB-10`, `AC-JOB-11`, `AC-JOB-12` | TC-JOB-010, TC-JOB-011, TC-JOB-012 |
| `FR-JOB-LOG-001` | Lưu log và kết quả job | P0 | `US-JOB-05` | `AC-JOB-13`, `AC-JOB-15` | TC-JOB-013, TC-JOB-015 |
| `FR-JOB-LOG-002` | Stream log qua SSE | P0 | `US-JOB-06`, `US-JOB-06` (FR) / `US-CON-10` (TC) | `AC-JOB-16`, `AC-JOB-17`, `AC-JOB-18`, `AC-JOB-25`, bổ sung | TC-JOB-016, TC-JOB-017, TC-JOB-018, Chưa có test case (`TC-JOB-025` chưa sinh ở [test-cases-job-flt.md](test-cases-job-flt.md)), TC-CON-103 |
| `FR-JOB-LOG-003` | Lưu giữ log job | P1 | `US-JOB-05` | `AC-JOB-14`, `AC-JOB-15` | TC-JOB-014, TC-JOB-015 |

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).
