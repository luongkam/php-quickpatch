---
id: DOC-UC-QP-FEED-005
title: Đặc tả Use Case UC-FEED-005 — Dựng snapshot khi phát hành tool
version: 1.0.0
phase: Use Case
domain: Security Patch Management
tags: [usecase, cockburn, UC-FEED-005, feeds, snapshot, release-pipeline, sys-05, release-gate]
depends_on:
  - DOC-SRS-QP-001
  - DOC-SRS-QP-FR-001
  - DOC-SRS-QP-BR-001
  - DOC-SRS-QP-ERR-001
  - DOC-SRS-QP-FEED-001
  - DOC-SRS-QP-FEED-002
  - DOC-SRS-QP-FEED-003
related_diagrams:
  - DIAG-UC-QP-001
author: BA Agent
last_updated: 2026-10-22
---

# Đặc tả Use Case Chi tiết (Alistair Cockburn Format)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo đặc tả UC-FEED-005 theo `skills/usecase`, template 26, rules 06, 17 |

## UC-FEED-005: Dựng snapshot khi phát hành tool

- **Tác nhân chính (Primary Actor)**: `SYS-05` pipeline phát hành (System actor, DOC-SRS-QP-FEED-001 §2.3).
- **Tác nhân hỗ trợ**: `SYS-02` nguồn online `SRC-001..012`; người phát hành (maintainer) nhận kết quả cổng phát hành; PO (duyệt ngoại lệ cho bản vá khẩn).
- **Phạm vi (Scope)**: `qp-feeds.py build-snapshot --variant standard` trên máy build; hằng `QP_SNAPSHOT_SHA256` trong `php-quickpatch.sh`; ghi chú phát hành.
- **Cấp độ (Level)**: Kite Level (quy trình phát hành của tổ chức) gồm 1 mục tiêu chính là tạo gói snapshot hợp lệ.
- **Các bên liên quan & Kỳ vọng (Stakeholders & Interests)**:
  - Mọi Operator (`PER-01..03`): bản tool mới có snapshot tuổi ≤ 7 ngày tại ngày phát hành (KR5.2) và có bản ghi vòng đời cho 100% nhánh PHP 4.4, 5.0–8.5 và Node.js 4–26 (KR5.1).
  - Máy chủ không ra Internet: dùng được snapshot ngay lần chạy đầu, kiểm SHA-256 với `QP_SNAPSHOT_SHA256` (`BR-FEED-010`).
  - Kỹ sư bảo mật: snapshot chỉ chứa dữ liệu công khai (`BR-FEED-056`), không chứa API key của pipeline (`BR-FEED-011`).
- **Tiền điều kiện (Pre-conditions)**:
  - Máy build có Python ≥ 3.6, mạng HTTPS tới mọi nguồn `SRC-001..012`, API key NVD của pipeline.
  - Test hồi quy DOC-SRS-QP-FEED-002 §6.5 (`min_patched`) có sẵn trong pipeline.
- **Hậu điều kiện (Post-conditions)**:
  - **Đảm bảo thành công**: file `feeds-snapshot.tar.gz` (biến thể `standard`, mục tiêu ≤ 3 MB nén) đi kèm bản phát hành; `QP_SNAPSHOT_SHA256` và ghi chú phát hành chứa SHA-256 của file.
  - **Đảm bảo tối thiểu**: khi cổng phát hành không đạt, pipeline không phát hành bản tool (trừ ngoại lệ PO duyệt bằng văn bản).
- **Kích hoạt (Trigger)**: Pipeline phát hành bắt đầu bước đóng gói của 1 bản tool mới.

### Luồng sự kiện chính (Main Success Scenario)
1. Pipeline chạy `qp-feeds.py build-snapshot --variant standard` trên máy build (`FR-FEED-SNAP-004`).
2. Hệ thống đồng bộ đầy đủ mọi nguồn `SRC-001..012` (dùng `GET /api/v1/products/full` cho `SRC-001`, API key NVD của pipeline), chuẩn hoá, hợp nhất như UC-FEED-001.
3. Hệ thống đóng gói bundle thành `manifest.json` (thêm `variant`, `tool_version_min`, `built_by: release-pipeline`), `SHA256SUMS`, `bundle/` (DOC-SRS-QP-FEED-003 §4.1).
4. Pipeline kiểm cổng phát hành (`BR-FEED-058`): (a) mọi nguồn P0 `SRC-001`, `002`, `004`, `006`, `009`, `010`, `011`, `012` ở `OK`; (b) độ phủ vòng đời đạt KR5.1; (c) test hồi quy DOC-SRS-QP-FEED-002 §6.5 khớp; (d) `generated_at` không cũ hơn 7 ngày so với ngày phát hành.
5. Pipeline tính `sha256sum feeds-snapshot.tar.gz`, ghi giá trị vào hằng `QP_SNAPSHOT_SHA256` trong `php-quickpatch.sh` và vào ghi chú phát hành.
6. Pipeline đính kèm snapshot vào gói phát hành tại `share/php-quickpatch/feeds-snapshot.tar.gz`.

### Các luồng nhánh & Ngoại lệ (Extensions / Alternative Flows)
- **2a. 1 nguồn P0 lỗi sau 3 lần thử, bị giới hạn tốc độ, hoặc phản hồi bất thường** (`ERR-FEED-503-01`, `ERR-FEED-429-01`, `ERR-FEED-502-01`, `ERR-FEED-502-02`):
  - 2a1. Bước 4(a) không đạt; pipeline dừng phát hành, báo nguồn lỗi cho người phát hành.
- **2b. Vượt ngân sách thời gian đồng bộ**:
  - 2b1. Hệ thống ghi `ERR-FEED-504-01`; pipeline chạy lại với `--source` các nguồn còn thiếu; vẫn lỗi → dừng phát hành.
- **2c. API key NVD bị từ chối**:
  - 2c1. Hệ thống ghi `ERR-FEED-401-01` (không ghi key); pipeline dừng phát hành tới khi cập nhật key.
- **4a. Độ phủ vòng đời thiếu nhánh hoặc test hồi quy sai**:
  - 4a1. Pipeline dừng phát hành, liệt kê nhánh thiếu/test sai.
- **4b. Bản vá khẩn cần phát hành khi cổng không đạt**:
  - 4b1. PO duyệt ngoại lệ bằng văn bản (`BR-FEED-058` ngoại lệ); ghi chú phát hành nêu tiêu chí không đạt.
- **4c. Snapshot > 7 ngày tại ngày phát hành**:
  - 4c1. Pipeline dựng lại snapshot (quay về bước 1) trước khi phát hành.
- **5a. Hash ghi vào script khác hash file thực tế (lỗi đóng gói)**:
  - 5a1. Máy dùng snapshot sẽ từ chối với `ERR-FEED-422-02`; pipeline phải kiểm lại bằng `feeds verify --snapshot FILE` trước khi phát hành (đề xuất bổ sung bước kiểm, chờ Dev duyệt).

### Yêu cầu đặc biệt (Special Requirements)
- KR5.1: 100% nhánh PHP 4.4, 5.0–8.5 và Node.js 4–26 có bản ghi vòng đời trong snapshot.
- KR5.2: snapshot ≤ 7 ngày tuổi tại ngày phát hành.
- Biến thể `standard` ≤ 3 MB nén; `full` ≤ 15 MB nén (DOC-SRS-QP-FEED-003 §4.4).
- `NFR-MNT-002`: test hồi quy `min_patched` và 11 ví dụ điểm rủi ro đạt 100%.

### Quy tắc nghiệp vụ liên quan (Business Rules)
| Mã BR | Nội dung áp dụng | Bước |
| :--- | :--- | :--- |
| `BR-FEED-058` | Cổng phát hành snapshot | 4 |
| `BR-FEED-010` | Toàn vẹn snapshot qua `QP_SNAPSHOT_SHA256` | 5 |
| `BR-FEED-056` | Không xuất dữ liệu riêng | 3 |
| `BR-FEED-011` | Không ghi API key vào snapshot | 2, 3 |
| `BR-FEED-002`, `BR-FEED-004` | Đồng bộ NVD, giới hạn tốc độ | 2 |

### Yêu cầu chức năng liên quan (FR)
| Mã FR | Tên | Bước |
| :--- | :--- | :--- |
| `FR-FEED-SNAP-004` | Dựng snapshot khi phát hành | 1–6 |

### Giao diện và API liên quan
- Không có màn hình hay API console (DOC-API-QP-001 §5.3); giao diện là pipeline phát hành và file `share/php-quickpatch/feeds-snapshot.tar.gz`.

### Quan hệ với use case khác
- `<<include>>` UC-FEED-001 (luồng đồng bộ đầy đủ ở bước 2).
- Kết quả được dùng ở UC-FEED-004 extension 3b và UC-SCAN-001 bước 4.

### Ghi chú và tài liệu tham chiếu
- Quy trình dựng snapshot: [data-sources-cache-cli.md §4.2](../srs/data-sources-cache-cli.md); cổng phát hành: §8 `BR-FEED-058`.
