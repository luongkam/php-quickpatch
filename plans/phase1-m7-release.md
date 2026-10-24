# M7 — Báo cáo, kiểm thử đầu–cuối, RTM, phát hành 2.0.0

Mục tiêu: `report assess|evidence` 4 định dạng (json/csv/md/html) kèm SHA-256; test đầu–cuối theo use case chính (scan → assess → plan → compat → migrate → rollback; console); đối chiếu RTM (trạng thái từng FR/AC/TC: tự động/thủ công/chưa thử trên máy thật); cập nhật README, CHANGELOG, hướng dẫn cài đặt; dựng snapshot phát hành; `QP_VERSION=2.0.0`.

## 1. Tài liệu chính
`srs/functional-requirements.md` §12; `srs/business-rules.md` (`BR-RPT-*`); `userstories/acceptance-criteria-ptch-cli-rpt.md`; `test/test-cases*.md`, `test/rtm.md`; `usecases/`.

## 2. Tiêu chí nghiệm thu
- Báo cáo 4 định dạng hợp lệ (JSON theo schema, CSV phân tích được, HTML không tải tài nguyên ngoài, che bí mật `BR-SEC-006`), SHA-256 in ra khớp file.
- Báo cáo bằng chứng gồm audit + manifest + `switch.json` + `hc.json` trong khoảng ngày, kèm kết quả `audit verify`.
- `plans/phase1-rtm-status.md`: 159 FR, 488 AC/TC Phase 1 với trạng thái kiểm thử thực tế.
- Toàn bộ `tests/run.sh` xanh; shellcheck sạch; tag phiên bản 2.0.0 trong mã và CHANGELOG (không tạo tag git/release khi PO chưa yêu cầu).

## 3. FR → US → AC → TC

| FR | Tên | Ưu tiên | US | AC | TC |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `FR-RPT-ASMT-001` | Xuất báo cáo đánh giá | P1 | `US-RPT-01` | `AC-RPT-01`, `AC-RPT-02`, `AC-RPT-03` | TC-RPT-001, TC-RPT-002, TC-RPT-003 |
| `FR-RPT-AUD-001` | Xuất báo cáo bằng chứng thay đổi | P1 | `US-RPT-02` | `AC-RPT-04`, `AC-RPT-05`, `AC-RPT-06` | TC-RPT-004, TC-RPT-005, TC-RPT-006 |
| `FR-CLI-CMD-004` | Cung cấp lệnh `report` và `audit` | P0 | `US-CLI-08` | `AC-CLI-22`, `AC-CLI-23`, `AC-CLI-24` | TC-CLI-022, TC-CLI-023, TC-CLI-024 |

## Trạng thái FR
Cập nhật khi kết thúc mốc (Xong / Một phần / Chưa thử trên máy thật).
