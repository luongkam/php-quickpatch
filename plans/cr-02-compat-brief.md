# CR-02 — Báo cáo `compat --path` trả lời trực tiếp mối lo của khách

Yêu cầu (PO, 2026-10-26): báo cáo CR-01 thiên về kỹ thuật, chưa trả lời câu khách hỏi (vd khách eKYC: Lambda Node.js 18 hết hỗ trợ, thư viện cũ có lỗ hổng): **giờ đang có rủi ro bảo mật gì, quét xong có đảm bảo không, checklist là gì**, kèm effort và thời điểm triển khai.

## Thay đổi
Phần đầu báo cáo (HTML/Markdown, vi/en) là "Trả lời cho khách hàng" (`qplib/compat/brief.py`), sau đó mới đến phần kỹ thuật cũ:

| Câu hỏi | Nội dung | Nguồn số liệu |
| :--- | :--- | :--- |
| 1. Đang có rủi ro bảo mật gì? | Bảng rủi ro xếp theo mức (Nghiêm trọng/Cao/Trung bình/Thấp) + cách xử lý: runtime Node.js hết hỗ trợ (kèm số lỗ hổng chưa vá của bản mới nhất nhánh cũ), runtime AWS Lambda (ngày AWS ngừng vá, chặn tạo, chặn cập nhật function), package production có lỗ hổng (KEV/mã độc → Nghiêm trọng), thư viện hết hỗ trợ (aws-sdk v2), lỗ hổng chỉ ở devDependencies, dự án chưa kiểm được | Bundle feeds (vòng đời, CVE), OSV, npm registry, bảng runtime Lambda |
| 2. Nâng cấp được không, ảnh hưởng gì? | Kết luận + đích khuyến nghị (đích được yêu cầu hết hỗ trợ/còn < 365 ngày → nêu lý do, chuyển sang nhánh khuyến nghị) + danh sách ảnh hưởng | Kết luận CR-01 |
| 3. Cần sửa gì, effort bao nhiêu? | Bảng hạng mục, số lượng, giờ công thấp–cao; tổng ngày công | Quy tắc `EFFORT` (giờ cố định + giờ theo số lượng), ghi rõ là ước lượng sơ bộ |
| 4. Khi nào triển khai? | Các giai đoạn (sửa, staging, production canary) + khoảng ngày production theo ngày làm việc; phần bảo mật gấp tách được | Lịch tính từ ngày quét |
| 5. Quét xong có đảm bảo không? | Trạng thái hiện tại (an toàn/chưa), phạm vi bản quét bảo đảm, phạm vi KHÔNG bao phủ (0-day, lỗi logic, cấu hình AWS/IAM/DynamoDB, layer), điều kiện báo "xong", rủi ro còn lại (package chưa có bản sửa), câu tuyên bố giới hạn | Kết quả quét |
| Checklist | Từng việc có ô đánh dấu theo giai đoạn: chuẩn bị (nhánh, publish version Lambda), mỗi dòng khai báo runtime cần đổi, mỗi package cần nâng/thay, chuyển đổi thư viện, mã, kiểm thử (từng function, DynamoDB), triển khai canary qua alias, theo dõi CloudWatch 24 h, quét lại + gửi báo cáo trước/sau | Kết quả quét |

`--json`: `result.brief` (chỉ khoá + tham số, không lưu văn bản): `risks[]`, `effort`, `schedule[]`, `schedule_window`, `assurance`, `checklist[]`, `final_target`. `lifecycle.current.unpatched`, `lifecycle.recommended_eol` mới.

## Giả định
| Mã | Nội dung |
| :--- | :--- |
| A-CR02-01 | Ngày ngừng hỗ trợ runtime AWS Lambda (`nodejs18.x`..`nodejs24.x`: deprecation, chặn tạo, chặn cập nhật) là bảng trong mã theo trang AWS Lambda runtimes như biết ngày 2026-10-26; báo cáo in link nguồn. Cần đối chiếu trang AWS trước khi gửi khách và cập nhật bảng khi AWS đổi lịch |
| A-CR02-02 | Effort: giờ cố định + giờ × số lượng cho từng loại việc, 8 giờ/ngày, 1 người; staging 1–2 ngày, production 1 ngày; ngày làm việc thứ 2–6, không tính ngày lễ |
| A-CR02-03 | "Bảo đảm" chỉ áp dụng cho rủi ro đã biết tại thời điểm quét; báo cáo luôn ghi rõ phạm vi không bao phủ |
| A-CR02-04 | Mức rủi ro: Lambda đã chặn cập nhật → Nghiêm trọng; Lambda đã deprecated hoặc Node.js EOL → Cao (Nghiêm trọng khi nhánh cũ còn lỗ hổng critical/KEV chưa vá); package: mức cao nhất của advisory, KEV/mã độc → Nghiêm trọng |

## Kiểm thử
`test_cr01_compat.sh` (thêm 14 kiểm tra CR-02 trên fixture SAM 2 function nodejs18.x), `test_cr02_brief.py` (8 test: mức rủi ro theo ngày, số lỗ hổng chưa vá, KEV, dự án chưa kiểm, effort, lịch ngày làm việc, đích khuyến nghị, JSON).
