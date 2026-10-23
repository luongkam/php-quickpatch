---
id: DOC-UC-QP-FEED-002
title: Đặc tả Use Case UC-FEED-002 — Đồng bộ dữ liệu theo lịch
version: 1.0.1
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FEED-002, feeds, schedule, systemd-timer, cron, sys-01]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-003
related_diagrams:
  - DIAG-UC-QP-001
  - DIAG-SEQ-QP-FEED-001
  - DIAG-SEQ-QP-FEED-002
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FEED-002 theo `skills/usecase`, template 26, rules 06, 17 |
| 1.0.1 | 2026-10-22 | BA Agent | Thêm `DIAG-SEQ-QP-FEED-002` vào `related_diagrams` (khớp flows.md §1.7); khai 1 cấp độ duy nhất Sea Level theo rule 06, nêu rõ mục tiêu chung của bước cài lịch và bước chạy theo lịch |

## UC-FEED-002: Đồng bộ dữ liệu theo lịch

- **Tác nhân chính (Primary Actor)**: `SYS-01` System: Feed sync — bộ lập lịch (systemd timer hoặc cron) chạy `feeds update --quiet` với quyền của người đã cài lịch.
- **Tác nhân hỗ trợ**: Operator root hoặc Operator không root (`PER-01`, `PER-02`) — người cài/gỡ/xem lịch (`feeds schedule`); `SYS-02` nguồn online.
- **Phạm vi (Scope)**: `php-quickpatch.sh feeds schedule install|remove|show`, unit `php-quickpatch-feeds.service`/`.timer` hoặc dòng cron mang dấu `# php-quickpatch-feeds`.
- **Cấp độ (Level)**: Sea Level (mục tiêu người dùng). Mục tiêu duy nhất: dữ liệu `feeds/` được đồng bộ tự động theo chu kỳ N giờ mà Operator không phải chạy tay `feeds update`. Bước 1–4 (Operator cài lịch) là phần thiết lập, bước 5–8 (`SYS-01` chạy theo lịch) là phần thực hiện của cùng mục tiêu; bước 6 gọi luồng đồng bộ của UC-FEED-001 qua `<<include>>` nên không khai cấp độ riêng cho mỗi lần chạy.
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - `PER-01`, `PER-02`: cache không quá hạn mà không cần thao tác tay; tuổi dữ liệu ≤ 6 giờ 15 phút tại 99% thời điểm (`NFR-FEED-006`, KR1.1).
  - Nhà cung cấp nguồn: request không dồn vào phút 00 (phút chạy ngẫu nhiên 0–59, `RandomizedDelaySec=900`).
  - Chủ máy chủ: tối đa 1 lịch đồng bộ trên máy (`BR-FEED-057`); lịch chỉ chạy `feeds update`, không vá tự động ở Phase 1 (đề xuất `Q-07`).
- **Tiền điều kiện (Pre-conditions)**:
  - Cài lịch: có systemd, hoặc có cron (`/etc/cron.d/` khi root; `crontab` của user khi không root).
  - Mỗi lần chạy: như tiền điều kiện của UC-FEED-001 (Python ≥ 3.6, ≥ 100 MB trống, mạng HTTPS).
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: đúng 1 unit/dòng cron có dấu `php-quickpatch-feeds` với chu kỳ N giờ, N ∈ {1, 2, 3, 4, 6, 8, 12, 24}; mỗi lần chạy cập nhật bundle như UC-FEED-001; `feeds status` hiển thị loại lịch, chu kỳ, lần chạy kế tiếp.
  - **Đảm bảo tối thiểu**: lần chạy lỗi không làm hỏng `current/`; lịch đã có không bị nhân đôi.
- **Kích hoạt (Trigger)**: (1) Operator chạy `feeds schedule install [--interval-hours N]`, `remove`, `show`, hoặc thao tác lịch trên SCR-008 (job `feeds_schedule`); (2) đến mốc thời gian của timer/cron.

### Luồng sự kiện chính (Main Success Scenario)
1. Operator chạy `php-quickpatch.sh feeds schedule install --interval-hours 6` (mặc định 6, `Q-08`), hoặc chọn chu kỳ trên SCR-008; console tạo job `feeds_schedule` loại `write` sau dry-run và xác nhận (UC-CON-003).
2. CLI phát hiện lịch đã có qua tên unit hoặc dấu `# php-quickpatch-feeds` (`BR-FEED-057`).
3. Chưa có lịch: CLI chọn phút ngẫu nhiên `MM` ∈ 0–59 cố định cho máy và tạo `php-quickpatch-feeds.service` (`ExecStart=<script> feeds update --quiet`) + `.timer` (`OnCalendar=*-*-* 00/6:MM:00`, `RandomizedDelaySec=900`, `Persistent=true`) khi có systemd (`FR-FEED-SCHD-001`, `FR-FEED-CMD-006`).
4. CLI ghi audit thao tác cài lịch (`FR-JOB-AUD-001`) và in trạng thái lịch: loại, chu kỳ, lần chạy kế tiếp (UTC).
5. Đến mốc lịch, `SYS-01` khởi chạy `feeds update --quiet`.
6. CLI thực hiện đồng bộ theo luồng chính UC-FEED-001 bước 2–10 (`FR-FEED-SYNC-001`).
7. CLI chỉ in ra khi có lỗi (`--quiet`), ghi `feeds/state/sync-status.json` và `php-quickpatch.log`, thoát 0/1/2 theo DOC-SRS-QP-FEED-003 §6.3.
8. Lần mở SCR-008/`feeds status` kế tiếp hiển thị kết quả lần chạy theo lịch và thời điểm chạy kế tiếp (UC-FEED-003).

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **1a. `--interval-hours` ngoài tập {1, 2, 3, 4, 6, 8, 12, 24}**:
  - 1a1. CLI trả lỗi tham số `ERR-CLI-400-01`, thoát 2; console trả `ERR-CON-422-01`.
- **1b. N < 6 và không có API key NVD**:
  - 1b1. CLI cài lịch và in cảnh báo về hạn mức NVD (DOC-SRS-QP-FEED-003 §5.2).
- **1c. Lệnh ghi mới chạy không có TTY và thiếu `--yes`**:
  - 1c1. CLI in `ERR-CLI-428-01`, thoát 2 (`BR-CLI-003`).
- **2a. Đã có lịch**:
  - 2a1. CLI cập nhật chu kỳ tại chỗ, không tạo bản thứ 2 (`BR-FEED-057`).
- **3a. Máy không có systemd**:
  - 3a1. Root: CLI ghi dòng `MM */6 * * * root <script> feeds update --quiet # php-quickpatch-feeds` vào `/etc/cron.d/php-quickpatch-feeds`.
  - 3a2. Không root: CLI thêm dòng tương ứng vào `crontab -l` của user, cùng dấu đánh dấu; lịch chỉ cập nhật cache riêng của user.
- **3b. Operator chạy `feeds schedule remove`**:
  - 3b1. CLI xoá unit/dòng cron có dấu `php-quickpatch-feeds`, ghi audit, in "đã gỡ lịch".
- **3c. Operator chạy `feeds schedule show`**:
  - 3c1. CLI in loại lịch, chu kỳ, lần chạy kế tiếp; không thay đổi hệ thống.
- **4a. Không ghi được bản ghi audit intent (đĩa đầy, sai quyền)**:
  - 4a1. CLI huỷ thao tác cài/gỡ lịch, in `ERR-AUD-500-01` (`BR-AUD-004`).
- **6a. Lượt `feeds update` thủ công đang giữ `feeds/.lock` > 30 s**:
  - 6a1. Lần chạy theo lịch thoát 2 với `ERR-FEED-423-01`; lần chạy kế tiếp theo chu kỳ đồng bộ bình thường.
- **6b. Nguồn lỗi, vượt ngân sách, biến động bất thường, thiếu dung lượng**:
  - 6b1. Xử lý như extension 3a, 5a–5f, 7a–7b của UC-FEED-001 (`ERR-FEED-503-01`, `ERR-FEED-504-01`, `ERR-FEED-502-02`, `ERR-FEED-507-01`); lịch không chạy `--accept-shrink`.
- **6c. Máy tắt tại mốc lịch**:
  - 6c1. systemd chạy bù ngay khi timer được kích hoạt lại nếu đã lỡ ≥ 1 lần trong thời gian tắt (`Persistent=true`), vẫn áp `RandomizedDelaySec=900`.
  - 6c2. cron giả định máy chạy liên tục nên lần chạy bị lỡ chờ tới mốc kế tiếp (tuổi dữ liệu tối đa tăng thêm 1 chu kỳ); hành vi chạy bù của từng bản cron cụ thể chưa kiểm chứng.

### Yêu cầu đặc biệt (Special Requirements)
- `NFR-FEED-006`: tuổi dữ liệu ≤ 6 giờ 15 phút tại 99% thời điểm khi có mạng.
- `NFR-FEED-001`, `NFR-FEED-008`: mỗi lần chạy tăng dần ≤ 180 s P95 và ≤ 45 request.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FEED-057` | Tối đa 1 lịch đồng bộ, phút chạy ngẫu nhiên cố định theo máy | 2, 3 |
| `BR-FEED-001`..`BR-FEED-009`, `BR-FEED-015` | Quy tắc đồng bộ của mỗi lần chạy | 6 |
| `BR-CLI-003` | Lệnh ghi mới cần xác nhận TTY hoặc `--yes` | 1 |
| `BR-JOB-003` | `feeds schedule install/remove` là job `write` | 1 |
| `BR-AUD-001`, `BR-AUD-004` | Ghi audit, đóng khi lỗi | 4 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FEED-SCHD-001` | Cài/gỡ/xem lịch đồng bộ | 2, 3 |
| `FR-FEED-CMD-006` | Lệnh `feeds schedule` | 1, 3 |
| `FR-FEED-SYNC-001` | Điều phối một lần đồng bộ | 6 |

### Giao diện và API liên quan
- Màn hình: `SCR-008` (khối "Lịch đồng bộ").
- API: `POST /api/v1/jobs` (`action=feeds_schedule`), `GET /api/v1/feeds` (trường `schedule`).

### Quan hệ với use case khác
- `<<include>>` UC-FEED-001 (luồng đồng bộ từ bước 2).
- Kết quả được xem ở UC-FEED-003.

### Ghi chú và tài liệu tham chiếu
- Tham số timer systemd, dòng cron và chu kỳ: [data-sources-cache-cli.md §5.2](../srs/data-sources-cache-cli.md).
- Sơ đồ tuần tự: `DIAG-SEQ-QP-FEED-001` ([data-sources-cache-cli.md §5.1](../srs/data-sources-cache-cli.md)) cho 1 lần `feeds update`; `DIAG-SEQ-QP-FEED-002` ([flows.md §2.1](../srs/flows.md)), lần chạy theo lịch của `SYS-01` bắt đầu tại bước CLI gọi `feeds update --quiet`.
- Câu hỏi mở: `Q-07` (lịch không chạy vá tự động ở Phase 1), `Q-08` (chu kỳ 6 giờ) — spec §4.4.
- Kiểm chứng ngày 2026-10-22 (WebFetch): systemd.timer(5) — `Persistent=` lưu thời điểm kích hoạt cuối trên đĩa, "the service unit is triggered immediately if it would have been triggered at least once" khi timer không hoạt động, chỉ áp cho `OnCalendar=`; `RandomizedDelaySec=` trễ ngẫu nhiên đều trong [0, giá trị] (https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html). anacron(8): "Unlike cron(8), it does not assume that the machine is running continuously" (https://man7.org/linux/man-pages/man8/anacron.8.html).
