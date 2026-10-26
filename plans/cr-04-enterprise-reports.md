# CR-04 — Hai tài liệu chuẩn tư vấn sinh từ phần mềm

Ngày: 2026-10-26. Yêu cầu của PO: thêm 2 mẫu báo cáo theo chuẩn của công ty tư vấn, do chính phần mềm sinh ra (không phải do skill viết tay):
- báo cáo hiện trạng bảo mật và phương án xử lý;
- báo cáo tương thích.

## 1. Hai tài liệu

| Mã | Tên (EN / VI) | Đọc giả | Câu hỏi trả lời |
| :--- | :--- | :--- | :--- |
| SPA | Security Posture Assessment & Remediation Plan / Báo cáo Đánh giá Hiện trạng An ninh và Kế hoạch Khắc phục | Đại diện khách, trưởng kỹ thuật phía khách | Hệ thống đang có rủi ro gì, mức nào, xử lý trước sau ra sao, bao giờ xong, xong rồi đã an toàn chưa |
| RCA | Runtime Compatibility Assessment & Migration Plan / Báo cáo Đánh giá Tương thích và Kế hoạch Nâng cấp Runtime | Trưởng kỹ thuật, quản lý dự án | Có lên được Node.js đích không, chọn dòng nào, phải sửa gì, làm thế nào, effort và lịch, rollback |

Mã tài liệu: `SPA-<DỰ ÁN>-<YYYYMMDD>`, `RCA-<DỰ ÁN>-<YYYYMMDD>`.

### Khung chung (theo mẫu deliverable của công ty tư vấn)
- Trang bìa: phân loại (mặc định MẬT — CONFIDENTIAL), khách hàng, dự án, mã tài liệu, phiên bản, ngày, người lập.
- Kiểm soát tài liệu: lịch sử phiên bản, danh sách phân phối, bảng phê duyệt (để trống cho khách ký).
- Mục lục đánh số.
- Tóm tắt điều hành:
  - kết luận tổng thể;
  - thẻ số liệu;
  - thông điệp chính;
  - quyết định cần phê duyệt;
  - bước tiếp theo.
- Phạm vi, phương pháp và nguồn dữ liệu, giới hạn và giả định.
- Phát hiện có mã (SEC-nn / CMP-nn). Mỗi phát hiện có:
  - mức độ;
  - nhóm;
  - phạm vi ảnh hưởng;
  - hiện trạng;
  - bằng chứng;
  - tác động;
  - khuyến nghị;
  - effort;
  - hạn xử lý (chỉ SPA);
  - tham chiếu.
- Lộ trình, sơ đồ tiến độ (ngày làm việc), thông tin khách cần cung cấp, phụ lục.

### SPA
1. Tóm tắt điều hành.
2. Phạm vi, phương pháp, giới hạn.
3. Phương pháp đánh giá mức độ. Thời hạn khắc phục theo mức:
   - Nghiêm trọng: 7 ngày;
   - Cao: 30 ngày;
   - Trung bình: 90 ngày;
   - Thấp: 180 ngày.
4. Tổng hợp phát hiện và bảng phân bố theo nhóm × mức độ.
5. Chi tiết phát hiện.
6. Hạng mục cần đánh giá bổ sung (FA-nn): review mã ứng dụng và review cấu hình AWS. Hai mục này máy quét không thấy được.
7. Lộ trình khắc phục 4 giai đoạn:
   - 0: Khoanh vùng;
   - 1: Khắc phục;
   - 2: Tăng cường;
   - 3: Bảo đảm.
8. Mức bảo đảm, rủi ro còn lại, tiêu chí nghiệm thu.
9. Thông tin cần khách cung cấp.
10. Phụ lục:
    - A: danh mục lỗ hổng VR-nnn, có CVE và bản sửa;
    - B: danh mục tài sản;
    - C: nguồn dữ liệu và thuật ngữ.

### RCA
1. Tóm tắt điều hành.
2. Phạm vi.
3. Phân tích phương án nền tảng đích. Mỗi dòng Node.js chẵn từ dòng hiện tại trở lên có:
   - ngày EOL;
   - ngày AWS Lambda ngừng hỗ trợ và chặn cập nhật;
   - số tháng còn hỗ trợ sau go-live;
   - đánh giá.
4. Ma trận tương thích theo thành phần: cấu hình runtime, mã, engines, native addon, AWS SDK, test tự động.
5. Tổng hợp phát hiện.
6. Chi tiết phát hiện.
7. Phương án triển khai, rollback (version + alias Lambda) và chiến lược kiểm thử.
8. Cơ cấu công việc, effort và tiến độ.
9. Rủi ro triển khai (MR-nn).
10. Thông tin cần khách cung cấp.
11. Phụ lục:
    - A: khai báo runtime cần đổi;
    - B: breaking change đã đánh giá;
    - C: danh mục tài sản.

## 2. Chức năng thêm vào phần mềm

| Thành phần | Nội dung |
| :--- | :--- |
| `qplib/compat/enterprise.py` | Mô hình tài liệu: section + block (h3, p, bullets, numbered, table, cards, rating, callout, finding, gantt). `security_doc`, `compat_doc`, `render_html` (A4, in được, không script, không tài nguyên ngoài, mọi giá trị từ mã đều được escape), `render_md`, `write` (tệp tạm + rename, `O_NOFOLLOW`) |
| `compat --path` | Luôn ghi `security-assessment.{html,md}` và `compatibility-assessment.{html,md}` vào `STATE_DIR/reports/compat-<run_id>/`, liệt kê trong `result.reports`. Tuỳ chọn mới: `--security-report FILE`, `--compat-report FILE`, `--client`, `--project-name`, `--prepared-by`, `--classification`, `--doc-version`. Thông tin bìa tối đa 120 ký tự, không có ký tự điều khiển |
| `report security\|compatibility --result RUN_ID\|FILE --out FILE` | Sinh lại tài liệu từ lần quét đã lưu (không quét lại), để điền thông tin bìa trước khi gửi. Nhận `result.json` của lượt quét, hoặc đầu ra `compat --json`. Không ghi đè (`ERR-RPT-409-01`). Sai định dạng → `ERR-RPT-422-01`. In SHA-256 như `FR-RPT-ASMT-001`. `qp.report/1`: `report_type` thêm `security`, `compatibility`. `report assess\|evidence` vẫn thuộc M7 |
| `project.py` | `lifecycle.branches` (bảng các dòng LTS để phân tích phương án); `has_tests` (scripts.test của package.json) |

## 3. Kiểm thử

| Bộ test | Nội dung |
| :--- | :--- |
| `tests/python/test_cr04_enterprise.py` (8) | Mã phát hiện liên tục và sắp theo mức độ; hạn xử lý critical = +7 ngày; phát hiện credential frontend và SDK v2; bảng phương án (Node 26 chưa có runtime Lambda); fallback khi kết quả cũ chưa có `branches`; escape HTML (tên dự án, thông tin bìa) và không tài nguyên ngoài; bảng Markdown đúng dạng; ngày công làm tròn 0,5; lệnh `report` (từ run id, từ envelope, SHA-256, từ chối ghi đè / định dạng / ký tự điều khiển / kết quả không phải compat / loại báo cáo lạ) |
| `tests/bash/test_cr01_compat.sh` (+22 kiểm tra) | Qua CLI thật: 4 tệp trong thư mục lượt quét, `--security-report`/`--compat-report`, `result.reports`, mã tài liệu, escape bìa, không script, schema `qp.compat/1` và `qp.report/1`, `report security` từ run id, SHA-256 khớp `sha256sum`, từ chối ghi đè/định dạng, `report assess` vẫn báo chưa có (M7) |

### Chạy trên dự án thật
Chạy trên repo Lambda của CR-03 với `--current 18 --target 24` (Python 3, mạng thật, OSV thật):
- sinh đủ 2 tài liệu (vi);
- kiểm tra hiển thị bằng Chromium:
  - bìa;
  - tóm tắt điều hành;
  - bảng phát hiện;
  - phân tích phương án;
  - ma trận;
  - bản in PDF A4.

Hai tài liệu thật chỉ gửi riêng cho người phụ trách, không đưa vào repo (repo public).

Những gì nhìn thấy và đã sửa trong lúc chạy thật:
- ngày công làm tròn 0,5;
- lệnh đổi runtime chuyển sang phần khuyến nghị;
- phát hiện "deprecated" có tác động;
- mô tả breaking change cắt theo từ;
- dòng Node chưa có runtime Lambda không gợi ý `nodejsN.x`;
- nhãn đánh giá xuống dòng trong bảng.

## 4. Chưa làm / chưa kiểm

- Chưa xuất .docx/.pdf trực tiếp. HTML có CSS `@page` A4: in ra PDF từ trình duyệt là được.
- Effort và ngày là ước lượng theo luật (ghi rõ trong tài liệu). Phần sửa do review mã và review AWS phát hiện chưa được tính.
- Mức độ của thành phần lấy theo advisory nặng nhất. Chưa phân tích đường gọi (reachability).
- Chưa thử trên Python 3.6 thật: chỉ kiểm cú pháp bằng `ast.parse(feature_version=(3, 6))` và bỏ toán tử `|` của dict.
- Nội dung chỉ cho Node.js (`compat --runtime node`). Tài liệu cho máy chủ PHP (`scan`/`assess`) thuộc M7 (`report assess`).
