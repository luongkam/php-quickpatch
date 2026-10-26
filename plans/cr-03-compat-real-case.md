# CR-03 — Cải tiến `compat --path` theo tình huống thật (Lambda Node.js 18)

Ngày: 2026-10-26. Đầu vào:
- **Repo thật** của một dự án khách (giấu tên vì repo này public):
  - 3 Lambda Node.js 18, mỗi function có 2 bản dev/prod, deploy bằng script;
  - DynamoDB, SES;
  - frontend Next.js export tĩnh lên S3.
- **Phiên phân tích thủ công** cùng ngày trên chính repo đó. Phiên đó dùng `scan --only npm`, `npm audit`, `npm audit fix` trên bản sao, đọc mã bằng tay, bảng runtime của AWS và chạy thử handler.

Chi tiết lỗ hổng của khách (tên repo, function, file, lỗi logic cụ thể) không ghi ở đây. Báo cáo đầy đủ chỉ gửi riêng cho người phụ trách.

## 1. So sánh

| Hạng mục | Thủ công | Công cụ trước CR-03 | Công cụ sau CR-03 |
| :--- | :--- | :--- | :--- |
| Lambda trong repo | Đọc script deploy → 3 function × dev/prod, vùng AWS | Không thấy (chỉ nhận SAM/CDK) | `deploy_info`: 6 function, vùng, `npm install`, `$LATEST` |
| Runtime Node.js của Lambda | Không có trong repo (đặt trên AWS), lấy theo lời khách | Bỏ sót rủi ro chính | Rủi ro "chưa rõ runtime" + lệnh `aws lambda get-function-configuration`; với `--current 18`: dòng rủi ro Lambda kèm ngày AWS |
| Ngày ngừng hỗ trợ runtime Lambda | Lấy trực tiếp từ trang AWS (18.x chặn cập nhật 31/08/2027) | **Sai**: ghi "đã chặn cập nhật từ 2026-03-09", mức Nghiêm trọng | Bảng theo trang AWS (copy 2026-10-26, in nguồn và ngày copy); thêm cảnh báo Amazon Linux 2 hết vòng đời 30/06/2026 |
| Mức nghiêm trọng của package | `npm audit` (vì `scan --only npm` in "critical: 0") | Có (OSV + mức advisory) | Như trước |
| Bản sửa dùng được | `npm audit fix` trên bản sao: proxy 0; reset/verify còn uuid + aws-sdk | Chỉ có "nâng lên" theo OSV | `fix_trial`: chạy `npm audit fix --package-lock-only` trên bản sao rồi tra OSV lại. Kết quả trùng với phân tích thủ công |
| Dependency gián tiếp | form-data/follow-redirects do axios kéo vào | Ghi "nâng form-data" như dependency trực tiếp | `via`: "gián tiếp do axios kéo vào: `npm update` hoặc nâng axios" |
| Frontend export tĩnh | Next 15.0.3: advisory phía server không áp dụng | Gộp vào package production, mức Nghiêm trọng | Tách thành dòng "Frontend tĩnh", mức Trung bình, có giải thích |
| aws-sdk v2 | ~10 lời gọi `.promise()`, DocumentClient → lib-dynamodb, SES → client-ses | "3 chỗ gọi" (đếm `require`) | Theo client: DocumentClient (2), SES (1), 12 lời gọi `.promise()`; effort tính theo số lời gọi |
| Credential trong frontend | Credential API trong biến `NEXT_PUBLIC_*` | Không | `client_secrets`: biến `NEXT_PUBLIC_*` chứa PASSWORD/SECRET/TOKEN, mức Cao |
| `serverless.yml` bị gitignore | Có ghi nhận, xin khách | Không | `ignored_iac` → mục "Cần khách cung cấp" |
| Biến môi trường | Liệt kê tay | Không | `env_vars` (11 biến) → mục "Cần khách cung cấp" |
| `npm install` trong deploy | Ghi ở R-12 | Không | Checklist: dùng `npm ci --omit=dev` |
| Lỗi logic ứng dụng (xác thực, phân quyền, SSRF, lưu mật khẩu, log) | Phát hiện bằng đọc mã (có lỗi mức Critical) | Không | Không tự phát hiện. Báo cáo có dòng **"Chưa đánh giá"**, cột "Phát hiện bằng", độ bao phủ ("đánh giá được 9 nhóm, 2 nhóm cần review"), checklist review mã |
| Cấu hình AWS (API Gateway, IAM, WAF) | Cần quyền của khách | Không | Dòng "Chưa đánh giá" + mục "Cần khách cung cấp" |
| Chạy thử handler trên Node 22/24 | Có (gọi handler với event giả) | Không | Không (chạy mã khách trên máy quét là rủi ro); để trong checklist kiểm thử |
| Effort / lịch | 7–10 ngày công, 2 tuần (gồm cả sửa lỗi logic) | 6–12 ngày công (kiểm thử hồi quy tính nặng) | 5–10 ngày công, production 03–11/11/2026; ghi rõ chưa gồm phần sửa do review |
| Yêu cầu nghiệp vụ mới của khách (pháp lý) | Phân tích riêng | Ngoài phạm vi công cụ | Ngoài phạm vi công cụ |

## 2. Thay đổi trong mã
- `project.py`:
  - `deploy_info`: Lambda từ script `aws lambda update-function-code/create-function`, cả tên function ghi qua biến; static site từ `aws s3 sync` / `output: "export"`.
  - `lock_parents`: dependency trực tiếp nào kéo gói vào.
  - `code_facts`: client SDK v2 theo service, `.promise()`, credential trong biến build công khai, biến môi trường.
  - `ignored_iac`, và `fix_trial` (cần npm và mạng; offline thì bỏ qua).
  - `DECL_FILES` thêm `.sh` và `Makefile`, nên bắt được `--runtime nodejs18.x` trong script.
- `brief.py`:
  - Bảng runtime Lambda đúng theo trang AWS.
  - Các rủi ro mới: runtime chưa rõ, credential lộ ra trình duyệt, frontend tĩnh, phiên bản bị npm đánh dấu deprecated (thay cho "thư viện ngừng phát triển"), dòng "Chưa đánh giá".
  - Cột "Phát hiện bằng", độ bao phủ, kết quả thử bản sửa, mục "Cần khách cung cấp".
  - Checklist theo từng function (dev trước, rồi prod).
  - Effort kiểm thử hồi quy theo kích thước dự án; ghi rõ phần chưa gồm.

## 3. Giả định
| Mã | Nội dung |
| :--- | :--- |
| A-CR03-01 | Bảng runtime Lambda là bản copy ngày 2026-10-26, báo cáo in kèm ngày copy. Chưa tự tải trang AWS mỗi lần quét (định dạng trang không ổn định). |
| A-CR03-02 | Frontend export tĩnh: mức rủi ro package production giới hạn ở Trung bình, kèm lý do. Advisory nào áp dụng cho bản export vẫn cần người đọc xác nhận. |
| A-CR03-03 | `fix_trial` không sửa repo. Nó chạy `npm audit fix --package-lock-only --ignore-scripts` trong `STATE_DIR/work/`, đặt `fetch-retries=0` để không treo khi không có mạng. |
| A-CR03-04 | Không tự phát hiện lỗi logic (thiếu kiểm token, IDOR, SSRF, mật khẩu plaintext). Báo cáo nói rõ bản quét không làm phần này để khách không hiểu "quét sạch = an toàn". |

## 4. Việc còn lại (đề xuất)
- `scan --only npm` (đường v0.1) chỉ in GHSA, không có mức nghiêm trọng, nên in "critical: 0" dù có lỗ hổng critical. Nên dùng chung `osv.library_check` với `compat` (M7).
- Đọc `serverless.yml` / Terraform khi có (runtime, route, IAM).
- Tuỳ chọn chạy thử handler với event giả trên Node đích, trong sandbox (cần khách đồng ý).
- Một số kiểm tĩnh rẻ cho Lambda: `console.log` của response hoặc token, `client_secret` trong query string, so sánh mật khẩu plaintext. Chỉ ở mức cảnh báo, không thay được review.

## 5. Kiểm thử
- `test_cr02_brief.py` thêm `LambdaRepoShapeTest`, dựng một repo cùng dạng tình huống thật: `deploy.sh` không có IaC, static export, `NEXT_PUBLIC_API_PASSWORD`, dependency gián tiếp, `serverless.yml` bị gitignore.
- `test_cr01_compat.sh` cập nhật theo ngày AWS đúng.
- Đã chạy thật trên repo của khách. Kết quả không đưa vào repo này vì chứa lỗ hổng chưa vá của khách.
