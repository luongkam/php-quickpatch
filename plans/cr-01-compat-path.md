# CR-01 — Quét tương thích thư mục dự án Node.js với nhánh đích, kèm báo cáo

| Mục | Nội dung |
| :--- | :--- |
| Nguồn yêu cầu | PO, trao đổi ngày 2026-10-26 (yêu cầu thật của dự án eKYC: AWS Lambda Node.js 18.x → 20/22, kiểm package có lỗ hổng, đưa phương án + effort) |
| Loại | Thêm lệnh mới, **ngoài danh sách FR Phase 1** (không có trong `srs/functional-requirements.md`); không đổi hành vi lệnh có sẵn |
| Trạng thái | Xong (xem commit CR-01) |
| Lý do | Lệnh `plan`/M4 chỉ quét được site có runtime trên máy; mã chạy nơi khác (AWS Lambda, container build ở CI, repo checkout) không có runtime/site nên không lập kế hoạch được |

## 1. Lệnh

```
php-quickpatch.sh compat --path DIR [--path DIR …] --target N
                         [--current N] [--node-bin PATH] [--report FILE.html|FILE.md]
                         [--lang en|vi] [--offline] [--json]
```

- Chỉ đọc thư mục quét; cần Python 3.6+ (như `assess`/`plan`). Không gọi AWS, không deploy, không sửa package.
- Mỗi thư mục có `package.json` (ngoài `node_modules`, `dist`, `build`, `.aws-sam`, `cdk.out`, …) là một dự án.
- `--target`: nhánh major Node.js đích; `--current`: nhánh hiện tại khi không khai báo ở đâu; `--node-bin`: binary Node.js đúng nhánh đích để nạp thử native addon trên bản sao.
- Kết quả `--json`: `qp.compat/1` (`schemas/qp.compat.v1.schema.json`). Mã thoát 0 khi mọi dự án `PASS` và không còn việc (lỗ hổng production, chuyển đổi package, đổi khai báo runtime); 1 khi còn việc; 2 khi lỗi tham số/chạy.
- Luôn ghi `report.html`, `report.md`, `result.json` vào `STATE_DIR/reports/compat-<run_id>/`; `--report` ghi thêm 1 bản (định dạng theo đuôi file; ghi file tạm + `rename`, không đi theo symlink).

## 2. Nội dung quét

| Phần | Cách làm | Dùng lại |
| :--- | :--- | :--- |
| Khai báo phiên bản Node.js | `Runtime: nodejsNN.x` (SAM/CloudFormation/Serverless), `Runtime.NODEJS_NN_X` (CDK), `FROM node:NN` / `public.ecr.aws/lambda/nodejs:NN`, `node-version:` (CI), `.nvmrc`, `.node-version`, `.tool-versions`; gắn vào dự án theo `CodeUri`/`Handler` cùng khối, hoặc theo thư mục; còn lại là "khai báo chung" | mới |
| Nhánh hiện tại | `--current`, else khai báo của dự án, else khai báo chung, else cận dưới của `engines.node` | mới |
| `engines.node` của dependency | lockfile v1/v2/v3, tra npm registry khi lockfile thiếu `engines`; devDependencies → cảnh báo | `deps.npm_engines` (M4) |
| Breaking change | Luật catalog `BC-NODE-*` cho mọi major trong (hiện tại, đích] trong mã `*.js/*.mjs/*.cjs/*.ts` | `scan.select_rules/scan_files` (M4) |
| Native addon | `binding.gyp`/`*.node`; có `--node-bin` → build lại + `require()` trên bản sao trong `STATE_DIR/work/` | `deps.addon_load` (M4) |
| Lỗ hổng | OSV (SRC-007, cache theo SHA-256 lockfile, offline dùng cache ≤ 7 ngày, `ERR-FEED-503-02`); "Nâng lên" = bản nhỏ nhất sửa được **mọi** advisory của package (ưu tiên cùng major); advisory chưa có bản sửa được liệt kê | `feeds.osv.library_check` (M2), thêm `by_advisory` |
| Package cần chuyển đổi | Dependency trực tiếp có `deprecated` trên npm registry; danh sách tool biết sẵn: `aws-sdk` v2 → AWS SDK v3 (hết hỗ trợ 2025-09-08), kèm chỗ gọi `require('aws-sdk')`/`from 'aws-sdk'` | mới |
| Vòng đời | Bundle feeds (cập nhật `feeds update --budget 110` khi chưa có bundle, như `scan`): trạng thái/EOL nhánh hiện tại và đích; nhánh khuyến nghị = LTS chẵn cao nhất còn ≥ 365 ngày (`BR-ASMT-002`) | `assess.branch_table` (M3) |

Kết luận mỗi dự án: `FAIL` khi có hit mức `error`, vi phạm `engines` mức error hoặc addon không nạp được; `PENDING` khi một phần chưa chạy được (mã khi không rõ nhánh hiện tại, addon khi không có `--node-bin`, lỗ hổng khi không tra được OSV); còn lại `PASS`. Lỗ hổng không làm `FAIL` (liệt kê riêng, như `scan`).

## 3. Báo cáo

HTML 1 trang tự chứa (CSS nội tuyến, không script, không tài nguyên ngoài, mọi giá trị lấy từ mã được escape, in được) và Markdown; tiếng Anh hoặc tiếng Việt (`--lang vi` hoặc `QP_LANG=vi`). Gồm: kết luận bằng lời, số liệu chính, vòng đời và khuyến nghị nhánh, bảng khối lượng việc theo dự án (mức S/M/L chỉ là gợi ý, không phải ngày công), từng dự án (khai báo cần đổi + gợi ý dòng mới, lỗ hổng + bản cần nâng, package cần chuyển đổi + chỗ gọi, engines, mã bị ảnh hưởng + các breaking change trong dải, native addon, ghi chú), khai báo chung (CI), cách lập và giới hạn.

## 4. Test

| Test | Nội dung |
| :--- | :--- |
| `tests/python/test_cr01_compat_path.py` (9) | Khai báo (SAM `CodeUri`/`Handler`, CDK, Dockerfile, `.nvmrc`, CI), gợi ý dòng mới, bản sửa mọi advisory, lockfile v1/v3/shrinkwrap, kết luận và hạng mục việc, escape HTML/Markdown, không ghi qua symlink, chạy offline không bundle (mọi phần cần dữ liệu `PENDING`, thư mục quét không đổi) |
| `tests/bash/test_cr01_compat.sh` (32) | Tham số sai, repo SAM 2 hàm với OSV/npm registry giả: gán khai báo theo hàm, vòng đời từ bundle fixture (18 EOL, 22 còn 190 ngày < 365, khuyến nghị 24), lỗ hổng + bản cần nâng, `aws-sdk` v2 + `request` deprecated, `engines` chặn → `FAIL`, `url.parse()` → `BC-NODE-20-01`, addon chờ `--node-bin`, báo cáo HTML/MD (escape, tự chứa, gợi ý `nodejs22.x`), tiếng Việt, `--node-bin`, `--current`, offline không cache → `ERR-FEED-503-02` |
| Thử thật | Repo Lambda mẫu (3 hàm `prod_*`, axios 0.21.1, jsonwebtoken 8.5.1, aws-sdk 2.x) với OSV.dev và npm registry thật, bundle feeds thật: axios → 0.33.0, jsonwebtoken → 9.0.0 (major), aws-sdk chưa có bản sửa + chuyển đổi v3 |

## 5. Giới hạn / chưa làm
- Chỉ Node.js (`--runtime php` báo chưa có); yarn/pnpm chỉ cảnh báo (không đọc `yarn.lock`/`pnpm-lock.yaml`).
- Không ước lượng ngày công; không đọc cấu hình AWS thật (alias, layer, lịch ngừng hỗ trợ runtime Lambda của AWS).
- Layer Lambda dùng chung (thư mục không có `package.json`) không được nhận là dự án.
- Chưa có màn hình console (M6) và chưa nằm trong RTM/SRS; cần PO bổ sung FR nếu giữ lệnh này cho bản phát hành.
