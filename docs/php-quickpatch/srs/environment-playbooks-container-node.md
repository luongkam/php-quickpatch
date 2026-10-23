---
id: DOC-SRS-QP-ENV-005
title: Playbook theo môi trường — Docker/Compose và Node.js (PB-013..PB-018)
version: 1.0.0
phase: Specification
domain: Security Patch Management
tags: [srs, playbook, docker, compose, nodejs, nodesource, tarball, nvm, systemd, pm2, parallel-install, rollback]
depends_on:
  - DOC-SRS-QP-ENV-001
  - DOC-SRS-QP-ENV-002
  - DOC-SRS-QP-SCN-NODE-001
  - BR-SCN-026
  - BR-SCN-027
  - BR-SCN-028
  - BR-ENV-009
  - BR-ENV-011
related_diagrams: []
author: BA Agent
last_updated: 2026-10-22
---

# Playbook theo môi trường — Docker/Compose và Node.js (PB-013..PB-018)

## Lịch sử sửa đổi (Revision History)
| Phiên bản | Ngày | Người thực hiện | Tóm tắt thay đổi |
| :--- | :--- | :--- | :--- |
| 1.0.0 | 2026-10-22 | BA Agent | Khởi tạo PB-013..PB-018; tag image Docker Hub, script NodeSource, README nvm, tài liệu pm2 kiểm chứng ngày 2026-10-22 |

## 1. Giới thiệu
Phần chi tiết của [environment-playbooks.md](environment-playbooks.md) (DOC-SRS-QP-ENV-001). Node.js tách 2 lớp: **nguồn cài** (PB-014 NodeSource, PB-015 tarball, PB-016 nvm) quyết định (a)(b); **quản lý tiến trình** (PB-017 systemd, PB-018 pm2) quyết định (c)(e). Mỗi ứng dụng Node.js là 1 "site" với `site_id` dạng `app:<unit>` hoặc `app:pm2:<tên>`. Cột "KC" theo quy ước của DOC-SRS-QP-ENV-003 §1.

## 2. PB-013 — Docker / Compose

### 2.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Docker daemon | `docker info` exit 0 | v0.1 |
| Đang ở trong container | `/.dockerenv` hoặc cgroup (v0.1) → `BR-ENV-009`: không chạy PB-013 bên trong container | v0.1 |
| File khai báo | Dockerfile/`Dockerfile.*` có `FROM php:`/`FROM node:`; `docker-compose.y*ml`/`compose.y*ml` có `image: php:`/`image: node:` (biểu thức của v0.1 `check_dockerfiles`, độ sâu 7 cấp) | v0.1 |
| Container đang chạy | `docker ps --format '{{.ID}} {{.Names}} {{.Image}}'`; phiên bản: `docker exec <id> php -n -r 'echo PHP_VERSION;'`, `docker exec <id> node -v` | v0.1 |
| Dịch vụ Compose của container | Nhãn `com.docker.compose.project`, `com.docker.compose.service` (`docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' <id>`) | Chưa (đối chiếu tài liệu Compose) |
| Image hiện tại chính xác | `docker inspect -f '{{.Image}}' <id>` (ID dạng `sha256:…`) — dùng cho rollback vì tag như `php:8.4-fpm` thay đổi theo thời gian | Chưa |
| Site → dịch vụ | (1) Nginx/Apache trên host: `fastcgi_pass`/`proxy_pass` tới cổng được publish (`docker port <id>`) → PB-005 cho lớp proxy; (2) Nginx là 1 dịch vụ cùng Compose: `fastcgi_pass <service>:9000` trong file cấu hình được mount; (3) image `php:X.Y-apache`/`node` publish cổng trực tiếp ra Internet: không có lớp proxy; (4) Traefik/Caddy định tuyến bằng nhãn: `MANUAL` | Chưa |
| Tag image tồn tại (Docker Hub, 2026-10-22) | `php:8.4-fpm` (cập nhật 2026-10-21), `php:8.4-apache`, `php:8.4-fpm-alpine`, `php:8.5-fpm`, `php:8.2-fpm`, `php:7.4-fpm`, `node:26`, `node:24-bookworm-slim`, `node:22-alpine` đều trả HTTP 200 trên API tag | Có |

### 2.2 Hành động
| Hành động | Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- | :--- |
| (a) (SEMI) | 1 | Tag ghim bản patch (vd `php:8.4.12-fpm`): sửa tag lên bản patch mới nhất cùng nhánh trong Dockerfile/compose (`copy`) — v0.1 `check_dockerfiles`; tag trôi theo nhánh (`php:8.4-fpm`): giữ tag | File đã sửa | v0.1 |
| (a) | 2 | `docker compose -f <file> build --pull <service>` rồi `docker compose -f <file> up -d --no-deps <service>` (chỉ sau khi duyệt, `BR-ENV-011`) | Container mới `running`; phiên bản trong container ≥ bản vá tối thiểu | v0.1 (khuyến nghị `--pull`) |
| (a) | 3 | Chưa rebuild được: mitigation ini ghi vào container đang chạy + `docker restart` (v0.1, mất khi container được tạo lại) | | v0.1 |
| (b) (SEMI) | 1 | Gắn tag giữ image cũ: `docker tag <image ID cũ> qp-rollback/<project>-<service>:<run_id>` (`created`) | `docker image inspect` thấy tag | Chưa |
| (b) | 2 | Tạo file override `compose.qp-<service>-<NEW>.yaml` (`created`, đặt cạnh file compose gốc): dịch vụ `<service>-qp<NEWND>` sao chép định nghĩa dịch vụ gốc, đổi `image:` sang tag nhánh đích (vd `php:8.5-fpm`) hoặc `build.dockerfile` sang `Dockerfile.qp-<NEWND>` (bản sao Dockerfile với `FROM` mới, `created`); bỏ `ports:` publish trùng; giữ `volumes`, `networks`, `env_file` | `docker compose -f <gốc> -f <override> config` exit 0 | Chưa (cú pháp override là tính năng chuẩn của Compose, chưa đối chiếu tài liệu) |
| (b) | 3 | `docker compose -f <gốc> -f <override> up -d --no-deps <service>-qp<NEWND>` | Container `running`; `healthy` nếu image có `HEALTHCHECK` | Chưa |
| (c1) đổi upstream (SEMI, không gián đoạn) | 1 | Lớp proxy trên host → PB-005: đổi `fastcgi_pass`/`proxy_pass` sang cổng/địa chỉ của dịch vụ mới; Nginx trong Compose: sửa file cấu hình được mount (`copy`) từ `<service>:9000` thành `<service>-qp<NEWND>:9000`, `docker compose exec <nginx> nginx -t`, `docker compose exec <nginx> nginx -s reload` | Kiểm tra cú pháp đạt; `HC-C0` phương pháp 5 | Có (`nginx -t`, `-s reload`) |
| (c2) tạo lại tại chỗ (SEMI, có gián đoạn) | 1 | Khi không có lớp proxy (trường hợp 3 ở §2.1): `copy` file compose; đổi `image:`/`FROM` của chính dịch vụ; ghi `compose <file> <service>`; `docker compose up -d --no-deps <service>`; đo thời gian gián đoạn từ lúc container cũ dừng tới lúc container mới trả mã baseline | Thời gian gián đoạn ghi vào báo cáo | Chưa |
| (d) | — | URL: vhost của lớp proxy hoặc `http://127.0.0.1:<cổng publish>/`; log: `docker logs --since <t_C9> <container>`; `HC-C9`: `RestartCount` tăng 0, `.State.Health.Status` = `healthy` (DOC-SRS-QP-ENV-002 §7) | | Chưa (cấu hình log lỗi PHP ra stderr của image chính thức) |
| (e) | — | (c1): khôi phục `copy` cấu hình proxy → `nginx -t` → reload. (c2): khôi phục file compose → hành động `compose` (`docker compose -f <file> up -d --no-deps <service>`) dùng tag `qp-rollback/...` | Container cũ `running`, mã HTTP = baseline | Chưa |
| Gỡ | — | Dịch vụ `<service>-qp<NEWND>` trở thành dịch vụ chính ở mục P7 (sửa file compose gốc, có duyệt); `qp-rollback/*` chỉ xoá theo `BR-SCN-014` | | — |

### 2.3 Sao lưu, quyền, rủi ro
| Mục | Nội dung |
| :--- | :--- |
| File sao lưu | File compose gốc, Dockerfile, file cấu hình proxy (host hoặc mount); ID image cũ (`switch.json`) |
| Restart/reload | (c1) chỉ reload proxy; (c2) tạo lại container dịch vụ |
| Root | Bắt buộc hoặc thuộc nhóm `docker` (quyền tương đương root trên host) |
| Rủi ro | (1) Entrypoint tự chạy migration CSDL (vd `php artisan migrate`) khi container mới khởi động ở (b) → thay đổi dữ liệu dùng chung với container cũ; tool quét `entrypoint`/`command` tìm chuỗi `migrate` và yêu cầu người vận hành xác nhận trước (b). (2) Hai container dùng chung volume ghi (session, cache, upload). (3) Tên extension trong `docker-php-ext-install` khác giữa nhánh; build thất bại → `ERR-ENV-424-02`. (4) Kubernetes, Swarm, Traefik nằm ngoài phạm vi (mục `MANUAL`) |

## 3. PB-014 — NodeSource

### 3.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Kho deb | `/etc/apt/sources.list.d/nodesource.sources` (`URIs: https://deb.nodesource.com/node_<N>.x`, `Suites: nodistro`) hoặc định dạng cũ `nodesource.list`; khoá `/usr/share/keyrings/nodesource.gpg`; ghim `/etc/apt/preferences.d/nodejs` (`Pin: origin deb.nodesource.com`, `Pin-Priority: 600`) | Có (script `setup_24.x`) |
| Kho rpm | `/etc/yum.repos.d/nodesource-nodejs.repo` (`baseurl=https://rpm.nodesource.com/pub_<N>.x/nodistro/nodejs/<arch>`, `module_hotfixes=1`) | Có (script rpm `setup_24.x`) |
| Major đang dùng | `<N>` trong `URIs`/`baseurl`; `dpkg-query -W nodejs` / `rpm -q nodejs` | Có |
| Kiến trúc hỗ trợ (deb) | Chỉ `amd64`, `arm64` | Có |

### 3.2 Hành động
| Hành động | Lệnh | KC |
| :--- | :--- | :--- |
| (a) | `apt-get install -y -q --only-upgrade nodejs` / `dnf -y upgrade nodejs` (v0.1 `node_upgrade`); restart ứng dụng theo PB-017/PB-018 (v0.1 `restart_node_services`) | v0.1 |
| (b) | NodeSource chỉ có 1 gói `nodejs` (1 major) cho mỗi hệ thống; script `setup_<N>.x` **xoá** file kho cũ (`nodesource.list`, `nodesource.sources`; rpm: `nodesource*.repo`) trước khi ghi kho mới → chạy script = đổi major tại chỗ, vi phạm `BR-UPG-001`. Cài song song dùng PB-015 (tarball) theo `BR-SCN-026` | Có |
| (c)(d)(e) | PB-017/PB-018 trỏ ứng dụng sang `$NEW_BIN` của PB-015 | — |
| P7 (sau khi mọi ứng dụng đã chuyển, SEMI) | Đổi kho sang major mới: `curl -fsSL https://deb.nodesource.com/setup_<NEW>.x -o /tmp/qp-nodesource.sh` → người duyệt xem nội dung → `bash /tmp/qp-nodesource.sh` → `apt-get install -y nodejs`; hoặc gỡ kho NodeSource | Có (URL `setup_24.x`, `setup_26.x` trả HTTP 200 trên `deb.` và `rpm.`) |
| File sao lưu | `nodesource.sources`/`.list`, `/etc/apt/preferences.d/nodejs`, `/etc/apt/preferences.d/nsolid`, `/usr/share/keyrings/nodesource.gpg`, `/etc/yum.repos.d/nodesource-*.repo` | Có |
| Root | Bắt buộc | — |
| Rủi ro | Script NodeSource chạy qua ống `bash` với quyền root; không hỗ trợ `armv7l`/`ppc64le`/`s390x` (deb) | Có |

## 4. PB-015 — Tarball theo prefix

### 4.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Binary không thuộc gói | `pkg_owner` rỗng và tồn tại `$PREFIX/lib/node_modules/npm` (v0.1 `node_upgrade`) | v0.1 |
| Vị trí dò | `/usr/local/bin/node`, `/opt/*/bin/node` (v0.1 `discover_node_bins`) | v0.1 |
| Quy ước cài song song | `/opt/node-v<ver>-linux-<arch>`, liên kết `/opt/node-<major>` (DOC-SRS-QP-SCN-NODE-001 §1.3) | — |

### 4.2 Hành động
| Hành động | Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- | :--- |
| (a) | 1 | v0.1 `node_upgrade_prefix`: lấy bản mới nhất cùng major từ `https://nodejs.org/dist/index.json`; tải `node-v<ver>-linux-<arch>.tar.xz` + `SHASUMS256.txt`; `sha256sum -c`; `tar -czf` phần cũ của prefix vào backup (ghi `untar`); giải nén đè `--strip-components=1` | `$BIN -v` = bản mới; restart ứng dụng (v0.1) | v0.1 |
| (b) | 1 | Như bước tải và kiểm SHA-256 ở trên với major đích; giải nén vào `/opt/node-v<ver>-linux-<arch>` (`created`) | `sha256sum -c` đạt | v0.1 |
| (b) | 2 | Kiểm tra nền tảng (`BR-SCN-028`): `$NEW_BIN --version` exit 0, không có lỗi `GLIBC_` | | — |
| (b) | 3 | `ln -sfn /opt/node-v<ver>-linux-<arch> /opt/node-<major>` (ghi `link` với đích cũ hoặc `created`) | `readlink -f /opt/node-<major>/bin/node` = binary mới | — |
| (b) | 4 | Không ghi đè `/usr/bin/node`, `/usr/local/bin/node` hoặc prefix đang được unit/pm2 dùng (`BR-SCN-012`, `BR-SCN-026`) | Liên kết mặc định không đổi | — |
| (c)(d)(e) | — | PB-017/PB-018 với `$NEW_BIN = /opt/node-<major>/bin/node` | — | — |
| Kiến trúc | — | `x64`, `arm64`, `armv7l`, `ppc64le`, `s390x` (v0.1) | — | v0.1 |
| Root | — | Bắt buộc khi ghi `/opt`; người dùng không root dùng prefix trong `$HOME` cho ứng dụng của chính mình | — | — |
| Rủi ro | — | (a) ghi đè prefix tại chỗ: ứng dụng đang chạy giữ binary cũ trong bộ nhớ đến khi restart; native addon cần build lại khi đổi major (`BR-SCN-022`) | — | — |

## 5. PB-016 — nvm

### 5.1 Nhận diện và liệt kê
| Mục | Lệnh/đường dẫn | KC |
| :--- | :--- | :--- |
| Binary | `/root/.nvm/versions/node/*/bin/node`, `/home/*/.nvm/versions/node/*/bin/node` (v0.1) | v0.1 |
| Chủ sở hữu | `stat -c %U <NVM_DIR>` | v0.1 (`run_in_dir_as_owner`) |
| Phiên bản đã cài | `ls <NVM_DIR>/versions/node/` | v0.1 |
| Đường dẫn binary của 1 phiên bản | `nvm which <ver>` (chạy trong shell đã nạp `nvm.sh`) | Có |

### 5.2 Hành động
Mọi lệnh nvm chạy dưới quyền chủ `$NVM_DIR`: `runuser -u <owner> -- env HOME=<home> bash -c '. "<NVM_DIR>/nvm.sh" && <lệnh>'` (nvm chỉ là hàm shell, không chạy được khi shell không nạp `nvm.sh`).

| Hành động | Lệnh | KC |
| :--- | :--- | :--- |
| (a) (SEMI) | `nvm install <major>` cài bản patch mới nhất của major vào **thư mục mới** `versions/node/v<ver mới>/`; ứng dụng vẫn trỏ đường dẫn tuyệt đối của bản cũ → (a) trên nvm luôn kèm 1 lượt chuyển ứng dụng (PB-017/PB-018) và health check. v0.1 chỉ in hướng dẫn `nvm install <major> && nvm alias default <major>` | Có (lệnh) / v0.1 |
| (b) (SEMI) | `nvm install <major đích> --reinstall-packages-from=current` (cài lại gói toàn cục của phiên bản hiện tại); `$NEW_BIN` = kết quả `nvm which <major đích>` | Có |
| (c)(e) | PB-017/PB-018 với đường dẫn tuyệt đối `$NEW_BIN` (không dựa vào `nvm use`, `BR-SCN-026`) | — |
| P7 | `nvm alias default <major mới>` chỉ sau khi mọi ứng dụng và cron của người dùng đã chuyển (đổi default làm đổi Node của mọi shell mới của người dùng); `nvm uninstall <ver cũ>` theo `BR-SCN-014` | Có |
| File sao lưu | Không có file hệ thống; ghi `nvm alias default` hiện tại vào manifest (`note`) | — |
| Root | Không cần (chạy dưới chủ `$NVM_DIR`); root được phép thay mặt bằng `runuser` | — |
| Rủi ro | Unit/cron gọi `node` qua `PATH` của shell đăng nhập sẽ đổi phiên bản khi đổi `alias default`; script cài nvm sửa file profile của người dùng | Có |

## 6. PB-017 — systemd

### 6.1 Nhận diện và liệt kê
| Mục | Lệnh | KC |
| :--- | :--- | :--- |
| Unit dùng Node.js | Unit trong `/etc/systemd/system/*.service` có `ExecStart` chứa `<prefix>/bin/(node\|npm)` hoặc `pm2` (v0.1 `restart_node_services`); v2 đọc cấu hình hiệu lực bằng `systemctl cat <unit>` (gồm drop-in) | v0.1 / Có |
| Trạng thái | `systemctl show -p ExecStart,MainPID,ActiveState,NRestarts,Environment <unit>` | Có |
| Binary thực tế | `readlink /proc/<MainPID>/exe` | Có |
| Cổng nghe | `ss -ltnp` lọc theo `MainPID` | Có |

### 6.2 Hành động (c) chuyển 1 ứng dụng và (e) rollback
| Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| 1 | Phân loại `ExecStart`: (i) đường dẫn tuyệt đối tới `node`; (ii) gọi `npm`/`npx`/`/usr/bin/env node` (phụ thuộc `PATH`); (iii) gọi `pm2-runtime`/`pm2` → chuyển sang PB-018 | — | — |
| 2 | Tạo drop-in `/etc/systemd/system/<unit>.d/zz-php-quickpatch-node.conf` (`created`, ghi `systemd <unit>` vào manifest trước): (i) `[Service]` + dòng `ExecStart=` rỗng + `ExecStart=` mới (giữ nguyên tham số, thay đường dẫn interpreter bằng `$NEW_BIN`); (ii) `[Service]` + `Environment=PATH=<thư mục bin của $NEW_BIN>:<PATH cũ>` | `systemd-analyze verify <unit>` không báo lỗi | Có (`ExecStart=` rỗng để xoá giá trị cũ — `BR-SCN-027`) / Chưa (`systemd-analyze verify` trên drop-in) |
| 3 | `systemctl daemon-reload`; `systemctl restart <unit>` | `ActiveState=active` trong ≤ 30 s; `readlink /proc/<MainPID>/exe` = `$NEW_BIN` (`HC-C0`) | Có |
| 4 | Health check biến thể Node.js (DOC-SRS-QP-ENV-002 §7) | `PASS` | — |
| (e) | Xoá drop-in (phát lại `created`) → hành động `systemd`: `systemctl daemon-reload`, `systemctl restart <unit>` | `readlink /proc/<MainPID>/exe` = `$OLD_BIN` | Có |
| Restart | `restart` gây gián đoạn trong thời gian ứng dụng khởi động (1 tiến trình) — đo và ghi báo cáo; không gián đoạn chỉ khi ứng dụng có ≥ 2 instance sau load balancer (ngoài phạm vi) | | — |
| File sao lưu | Unit gốc (chỉ đọc, không sửa — mọi thay đổi nằm trong drop-in); drop-in mới | | — |
| Root | Bắt buộc với unit hệ thống; unit người dùng (`systemctl --user`) chạy dưới chủ unit | | Chưa (`--user` cần phiên `systemd --user` đang chạy) |
| Rủi ro | Drop-in khác có tên sắp sau `zz-…` ghi đè lại `ExecStart`; tool kiểm tra `systemctl show -p ExecStart` sau `daemon-reload` | | — |

## 7. PB-018 — pm2

### 7.1 Nhận diện và liệt kê
| Mục | Lệnh | KC |
| :--- | :--- | :--- |
| pm2 đang chạy | `pm2 pid` exit 0 (v0.1); chạy dưới quyền chủ pm2 với `PM2_HOME` tương ứng | v0.1 |
| Danh sách ứng dụng | `pm2 jlist` (JSON thô); trường dùng: `name`, `pid`, `pm2_env.exec_interpreter`, `pm2_env.pm_exec_path`, `pm2_env.pm_cwd`, `pm2_env.exec_mode`, `pm2_env.instances`, `pm2_env.restart_time`, `pm2_env.pm_err_log_path`, `pm2_env.node_version` | Có (lệnh) / Chưa (tên trường) |

### 7.2 Hành động (c) chuyển 1 ứng dụng và (e) rollback
| Bước | Lệnh | Tiêu chí | KC |
| :--- | :--- | :--- | :--- |
| 1 | Có file ecosystem: `copy` file; đặt `interpreter: '<$NEW_BIN>'` cho ứng dụng (thuộc tính `interpreter` = đường dẫn tuyệt đối, mặc định `node`). Không có file ecosystem: sinh `STATE_DIR/pm2/<app>.config.js` (`created`) từ `pm2 jlist` (`name`, `script`, `cwd`, `args`, `env`, `instances`, `exec_mode`) với `interpreter` mới; ghi `pm2 <ecosystem> <app>` vào manifest với ecosystem cũ (hoặc bản sinh từ trạng thái cũ) | File hợp lệ (`node -e "require('<file>')"` exit 0) | Có (`interpreter`) |
| 2 | `pm2 delete <app>`; `pm2 start <ecosystem> --only <app>`; `pm2 save` (`BR-SCN-027`) | `pm2 jlist`: ứng dụng `online`, `exec_interpreter` = `$NEW_BIN` (`HC-C0`) | Có (`pm2 save`) / Chưa (`--only`) |
| 3 | Health check biến thể Node.js | `PASS` | — |
| (e) | Hành động `pm2`: `pm2 delete <app>`; `pm2 start <ecosystem cũ> --only <app>`; `pm2 save` | `exec_interpreter` = `$OLD_BIN` | — |
| P7 | Sau khi mọi ứng dụng của daemon pm2 đã chuyển: cài pm2 dưới `$NEW`, `pm2 update`; `pm2 unstartup` rồi `pm2 startup` để script khởi động dùng Node.js mới (hướng dẫn "Updating startup script after Node.js version upgrade" của pm2); `pm2 save` | `pm2 resurrect` sau khởi động lại máy đưa đủ ứng dụng về `online` | Có |
| Restart | `delete` + `start` gây gián đoạn cả ở chế độ cluster (đổi interpreter không áp dụng được bằng `pm2 reload`) — đo, ghi báo cáo | | Chưa (hành vi `reload` khi đổi interpreter) |
| File sao lưu | File ecosystem; `~/.pm2/dump.pm2` (danh sách đã `pm2 save`) của chủ pm2 | | Chưa (tên file dump) |
| Root | Không cần với daemon pm2 của chính người dùng; root thao tác thay qua `runuser` (v0.1 `run_in_dir_as_owner`) | | v0.1 |
| Rủi ro | Biến môi trường chỉ có trong phiên shell lúc `pm2 start` ban đầu không có trong `pm2 jlist` → ứng dụng khởi động lại thiếu biến; tool so sánh `pm2_env.env` trước/sau và yêu cầu duyệt khi khác | | — |

## 8. Tài liệu tham chiếu (References)
Truy cập ngày 2026-10-22 (UTC).

| Nguồn | URL | Dùng cho | Trạng thái |
| :--- | :--- | :--- | :--- |
| Docker Hub API tag | https://hub.docker.com/v2/repositories/library/php/tags/8.4-fpm (và các tag ở §2.1); https://hub.docker.com/v2/repositories/library/node/tags/26 | Tag image tồn tại | Kiểm chứng (HTTP 200) |
| NodeSource `setup_24.x` (deb) | https://deb.nodesource.com/setup_24.x | `nodesource.sources`, `nodistro`, `Pin-Priority: 600`, xoá kho cũ, chỉ `amd64`/`arm64` | Kiểm chứng (đọc script) |
| NodeSource `setup_24.x` (rpm) | https://rpm.nodesource.com/setup_24.x | `nodesource-nodejs.repo`, `baseurl`, `module_hotfixes=1`, xoá `nodesource*.repo` | Kiểm chứng (đọc script) |
| NodeSource `setup_26.x` | https://deb.nodesource.com/setup_26.x, https://rpm.nodesource.com/setup_26.x | Có script cho major 26 | Kiểm chứng (HTTP 200) |
| nvm README | https://raw.githubusercontent.com/nvm-sh/nvm/master/README.md | `nvm which`, `nvm alias default`, `--reinstall-packages-from`, nạp `nvm.sh` trong shell không tương tác | Kiểm chứng |
| pm2 — Application Declaration | https://pm2.keymetrics.io/docs/usage/application-declaration/ | Thuộc tính `interpreter` | Kiểm chứng |
| pm2 — Startup Script | https://pm2.keymetrics.io/docs/usage/startup/ | `pm2 unstartup`, `pm2 startup`, `pm2 save`, `pm2 resurrect`, cập nhật script khởi động sau khi nâng Node.js | Kiểm chứng |
| pm2 — Quick Start | https://pm2.keymetrics.io/docs/usage/quick-start/ | `pm2 jlist` | Kiểm chứng |
| Danh mục kịch bản Node.js | [version-scenarios-node.md](version-scenarios-node.md) (DOC-SRS-QP-SCN-NODE-001) | `BR-SCN-022`, `BR-SCN-026`..`028`, quy ước `/opt/node-<major>` | Đã đọc |
| php-quickpatch v0.1.0 | `/home/user/php-quickpatch/php-quickpatch.sh` | `discover_node_bins`, `node_upgrade`, `node_upgrade_prefix`, `restart_node_services`, `check_dockerfiles`, `check_containers` | Đã đọc |
