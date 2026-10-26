"""Answers for the customer at the top of the `compat --path` report (CR-02).

The questions a customer asks before a Node.js upgrade of a Lambda backend:
  1. What security risk do we carry today?
  2. Can we upgrade, and what does it affect?
  3. What has to change, and how much effort?
  4. When can it go to production?
  5. Once the scan is clean, is the system safe? What does the scan guarantee?
and a checklist to follow and tick. Every figure comes from the scan result; the
effort and the schedule are a rule-based first estimate that the team adjusts.
"""
import datetime
import html

SEV_ORDER = ('critical', 'high', 'medium', 'low', 'unknown')
LEVELS = ('critical', 'high', 'medium', 'low', 'info')

# AWS Lambda runtime deprecation of the Node.js runtimes: (deprecation, block function create,
# block function update). Source: docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html,
# as known on 2026-10-26; check that page before quoting the dates to a customer.
LAMBDA_SOURCE = 'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html'
LAMBDA_RUNTIMES = {
    '18': ('2025-09-01', '2026-02-03', '2026-03-09'),
    '20': ('2026-04-30', '2026-08-31', '2026-09-30'),
    '22': ('2027-04-30', '2027-06-01', '2027-07-01'),
    '24': ('2028-04-30', '2028-06-01', '2028-07-01'),
}
# End of support of libraries that the tool knows (deprecated packages of the catalog).
LIB_EOL = {'aws-sdk': ('2025-09-08', '@aws-sdk/client-* (v3)')}
_FETCH = {'en': 'fetch (built into Node.js ≥ 18), undici or axios', 'vi': 'fetch (có sẵn từ Node.js 18), undici hoặc axios'}
LIB_ALT = {'request': _FETCH, 'request-promise': _FETCH}


def lib_alt(name, lang):
    a = LIB_ALT.get(name)
    return (a.get(lang) or a['en']) if a else None

# Effort per work item: hours (low, high) = fixed + per-unit x count. A first estimate, not a quote.
EFFORT = {
    'runtime_declarations': (0.5, 0.25, 1, 0.5),
    'engines_field': (0.25, 0, 0.5, 0),
    'vuln_minor_upgrades': (0.5, 0.25, 1, 0.5),
    'vuln_major_upgrades': (1, 1, 2, 3),
    'vuln_no_fix': (0, 1, 0, 4),
    'vuln_dev_only': (0, 0.1, 0, 0.25),
    'engines_violations': (0, 0.5, 0, 2),
    'migrate_package': (4, 0.5, 8, 1.5),
    'code_errors': (0, 0.5, 0, 2),
    'code_warnings': (0, 0.25, 0, 1),
    'native_addons': (0, 1, 0, 4),
    'regression_test': (4, 0, 8, 0),
}
STAGING_DAYS = (1, 2)       # deploy to a test stage and test every function
PROD_DAYS = (1, 1)          # canary in production + 24 h watch

TB = {
    'answers': {'en': 'Answers for the customer', 'vi': 'Trả lời cho khách hàng'},
    'q1': {'en': '1. What security risk does the system carry today?', 'vi': '1. Hệ thống đang có rủi ro bảo mật gì?'},
    'q2': {'en': '2. Can it be upgraded? What does it affect?', 'vi': '2. Có nâng cấp được không? Có ảnh hưởng gì?'},
    'q3': {'en': '3. What has to change, and how much effort?', 'vi': '3. Cần sửa những gì, effort bao nhiêu?'},
    'q4': {'en': '4. When can it go to production?', 'vi': '4. Khi nào có thể triển khai?'},
    'q5': {'en': '5. Once the scan is clean, is the system safe?', 'vi': '5. Quét xong thì có đảm bảo an toàn không?'},
    'checklist': {'en': 'Checklist', 'vi': 'Checklist thực hiện'},
    'level': {'en': 'Level', 'vi': 'Mức'},
    'risk': {'en': 'Risk', 'vi': 'Rủi ro'},
    'action': {'en': 'What to do', 'vi': 'Cách xử lý'},
    'critical': {'en': 'Critical', 'vi': 'Nghiêm trọng'},
    'high': {'en': 'High', 'vi': 'Cao'},
    'medium': {'en': 'Medium', 'vi': 'Trung bình'},
    'low': {'en': 'Low', 'vi': 'Thấp'},
    'info': {'en': 'Info', 'vi': 'Thông tin'},
    'no_risk': {'en': 'No known security risk found by the scan.', 'vi': 'Bản quét không phát hiện rủi ro bảo mật đã biết.'},
    # risks
    'r_runtime_eol': {'en': 'Node.js {c} reached end of life on {e} ({d} days ago): new Node.js vulnerabilities are no longer fixed for it.',
                      'vi': 'Node.js {c} đã hết hỗ trợ từ {e} ({d} ngày trước): lỗ hổng mới của Node.js không còn được vá cho nhánh này.'},
    'r_runtime_cves': {'en': 'The newest Node.js {c} release ({v}) still has {n} known unfixed vulnerabilities ({sev}).',
                       'vi': 'Bản Node.js {c} mới nhất ({v}) vẫn còn {n} lỗ hổng đã biết chưa vá ({sev}).'},
    'a_runtime': {'en': 'Move every function to Node.js {r}.', 'vi': 'Chuyển mọi function sang Node.js {r}.'},
    'r_lambda_blocked': {'en': 'AWS Lambda runtime nodejs{c}.x: deprecated since {dep} (no more security patches from AWS); creating functions blocked since {bc}, updating them blocked since {bu}. {n} function(s) declared on it: a fix cannot be deployed until the runtime changes.',
                         'vi': 'Runtime AWS Lambda nodejs{c}.x: AWS ngừng vá bảo mật từ {dep}; chặn tạo function từ {bc}, chặn cập nhật function từ {bu}. {n} function đang khai báo runtime này: không deploy được bản sửa nào cho tới khi đổi runtime.'},
    'r_lambda_deprecated': {'en': 'AWS Lambda runtime nodejs{c}.x: deprecated since {dep}, no more security patches from AWS; create blocked from {bc}, update blocked from {bu}. {n} function(s) declared on it.',
                            'vi': 'Runtime AWS Lambda nodejs{c}.x: AWS ngừng vá bảo mật từ {dep}; sẽ chặn tạo function từ {bc}, chặn cập nhật từ {bu}. {n} function đang khai báo runtime này.'},
    'r_lambda_soon': {'en': 'AWS Lambda runtime nodejs{c}.x will be deprecated on {dep} (in {d} days).',
                      'vi': 'Runtime AWS Lambda nodejs{c}.x sẽ bị AWS ngừng hỗ trợ ngày {dep} (còn {d} ngày).'},
    'r_deps': {'en': '{n} production package(s) with known vulnerabilities ({sev}): {top}.',
               'vi': '{n} package production có lỗ hổng đã biết ({sev}): {top}.'},
    'r_deps_kev': {'en': '{n} of them are exploited in the wild (CISA KEV) or malicious.',
                   'vi': 'Trong đó {n} package có lỗ hổng đang bị khai thác thực tế (CISA KEV) hoặc là mã độc.'},
    'a_deps': {'en': 'Upgrade to the versions in the checklist; {nofix} package(s) have no fixed version: replace them.',
               'vi': 'Nâng lên phiên bản ghi trong checklist; {nofix} package chưa có bản sửa: cần thay thế.'},
    'a_deps_all': {'en': 'Upgrade to the versions in the checklist (every one has a fixed version).',
                   'vi': 'Nâng lên phiên bản ghi trong checklist (tất cả đều có bản sửa).'},
    'r_lib_eol': {'en': '{p} is out of support since {e} (no more security fixes); used at {n} place(s) in the code.',
                  'vi': '{p} đã hết hỗ trợ từ {e} (không còn bản vá bảo mật); đang dùng ở {n} chỗ trong mã.'},
    'a_lib_eol': {'en': 'Migrate to {r}.', 'vi': 'Chuyển sang {r}.'},
    'r_lib_dep': {'en': '{p} is deprecated by its authors: {m}', 'vi': '{p} đã bị tác giả ngừng phát triển: {m}'},
    'r_dev': {'en': '{n} vulnerable package(s) in devDependencies only (not deployed to Lambda if the build excludes them).',
              'vi': '{n} package có lỗ hổng chỉ ở devDependencies (không lên Lambda nếu bản build loại chúng).'},
    'r_unchecked': {'en': 'Package vulnerabilities of {n} project(s) were NOT checked (no package-lock.json or offline): the risk is unknown.',
                    'vi': '{n} dự án CHƯA kiểm được lỗ hổng package (thiếu package-lock.json hoặc offline): rủi ro chưa xác định.'},
    'a_none': {'en': '-', 'vi': '-'},
    'a_lib_any': {'en': 'Replace it with a maintained library.', 'vi': 'Thay bằng thư viện còn được duy trì.'},
    'sites_none': {'en': 'no direct call found in the code (indirect dependency?)',
                   'vi': 'không thấy chỗ gọi trực tiếp trong mã (dependency gián tiếp?)'},
    's_runtime': {'en': 'Node.js {c} is out of support', 'vi': 'Node.js {c} đã hết hỗ trợ'},
    's_platform': {'en': 'AWS Lambda runtime nodejs{c}.x is deprecated', 'vi': 'runtime AWS Lambda nodejs{c}.x đã bị AWS ngừng hỗ trợ'},
    's_deps': {'en': '{n} production package(s) with known vulnerabilities', 'vi': '{n} package production có lỗ hổng đã biết'},
    's_lib': {'en': '{p} is out of support', 'vi': '{p} đã hết hỗ trợ'},
    's_unchecked': {'en': 'package vulnerabilities not checked', 'vi': 'chưa kiểm được lỗ hổng package'},
    # upgrade
    'u_yes': {'en': 'Yes. No blocker was found for Node.js {t} in the code and the dependencies.',
              'vi': 'Có. Không thấy điểm chặn nào cho Node.js {t} trong mã và dependency.'},
    'u_fix_first': {'en': 'Yes, after fixing {n} blocker(s) listed in the checklist (code, engines, native addons).',
                    'vi': 'Có, sau khi sửa {n} điểm chặn liệt kê trong checklist (mã, engines, native addon).'},
    'u_pending': {'en': 'Not decided yet: {parts} could not be checked.', 'vi': 'Chưa kết luận được: chưa kiểm được {parts}.'},
    'u_target_bad': {'en': 'The requested target Node.js {t} is not a good choice: {why}. Recommended: Node.js {r}.',
                     'vi': 'Đích Node.js {t} được yêu cầu không phù hợp: {why}. Khuyến nghị: Node.js {r}.'},
    'u_target_short': {'en': 'support ends on {e} ({d} days left)', 'vi': 'chỉ được hỗ trợ đến {e} (còn {d} ngày)'},
    'u_target_eol': {'en': 'it is out of support since {e}', 'vi': 'đã hết hỗ trợ từ {e}'},
    'u_target_ok': {'en': 'Node.js {t} is supported until {e}.', 'vi': 'Node.js {t} được hỗ trợ đến {e}.'},
    'impact': {'en': 'Impact on the running system', 'vi': 'Ảnh hưởng tới hệ thống đang chạy'},
    'i_runtime': {'en': '{n} configuration line(s) change (Lambda runtime, CI, Docker); no code change for that part.',
                  'vi': 'Đổi {n} dòng cấu hình (runtime Lambda, CI, Docker); phần này không phải sửa mã.'},
    'i_deps': {'en': '{n} package upgrade(s), {m} of them to a new major version (API may change: retest the calls).',
               'vi': 'Nâng {n} package, trong đó {m} package lên major mới (API có thể đổi: phải kiểm thử lại chỗ gọi).'},
    'i_migrate': {'en': '{p}: {n} call site(s) to rewrite.', 'vi': '{p}: viết lại {n} chỗ gọi.'},
    'i_code': {'en': '{n} code line(s) hit by Node.js breaking changes.', 'vi': '{n} dòng mã chịu ảnh hưởng của breaking change Node.js.'},
    'i_none_code': {'en': 'No code line matches a known breaking change of Node.js {c} → {t}.',
                    'vi': 'Không dòng mã nào khớp breaking change đã biết của Node.js {c} → {t}.'},
    'i_downtime': {'en': 'No downtime expected: Lambda versions/aliases switch traffic and roll back in seconds.',
                   'vi': 'Không cần dừng dịch vụ: chuyển lưu lượng bằng version/alias của Lambda, rollback trong vài giây.'},
    # effort
    'e_item': {'en': 'Work item', 'vi': 'Hạng mục'},
    'e_count': {'en': 'Count', 'vi': 'Số lượng'},
    'e_hours': {'en': 'Hours (low–high)', 'vi': 'Giờ công (thấp–cao)'},
    'e_total': {'en': 'Total', 'vi': 'Tổng'},
    'e_days': {'en': 'about {lo}–{hi} person-days of development and testing (1 person); staging test {s1}–{s2} days and production rollout {p} day come on top.',
               'vi': 'khoảng {lo}–{hi} ngày công phát triển và kiểm thử (1 người); cộng thêm {s1}–{s2} ngày kiểm thử staging và {p} ngày triển khai production.'},
    'e_note': {'en': 'First estimate computed from the scan (fixed + per item hours); the team adjusts it to its own tests and release process.',
               'vi': 'Ước lượng sơ bộ tính từ kết quả quét (giờ cố định + giờ theo số lượng); team điều chỉnh theo quy trình test và release của mình.'},
    'regression_test': {'en': 'Regression tests on Node.js {t}', 'vi': 'Kiểm thử hồi quy trên Node.js {t}'},
    # schedule
    's_phase': {'en': 'Phase', 'vi': 'Giai đoạn'},
    's_days': {'en': 'Working days', 'vi': 'Ngày làm việc'},
    's_when': {'en': 'If started on {d}', 'vi': 'Nếu bắt đầu {d}'},
    's_dev': {'en': 'Fix and upgrade (code, packages, runtime)', 'vi': 'Sửa mã, nâng package, đổi runtime'},
    's_staging': {'en': 'Deploy to a test stage, test every function', 'vi': 'Deploy môi trường test, kiểm thử từng function'},
    's_prod': {'en': 'Production: canary through an alias, watch 24 h', 'vi': 'Production: canary qua alias, theo dõi 24 giờ'},
    's_answer': {'en': 'Production rollout possible between {a} and {b} (working days, 1 developer, starting {d}). Urgent security items (runtime, critical/high packages) can ship first, in {u} working day(s).',
                 'vi': 'Có thể triển khai production trong khoảng {a} đến {b} (ngày làm việc, 1 người, bắt đầu {d}). Các mục bảo mật gấp (runtime, package critical/high) có thể tách ra triển khai trước trong {u} ngày làm việc.'},
    # assurance
    'g_now': {'en': 'Status now', 'vi': 'Trạng thái hiện tại'},
    'g_now_bad': {'en': 'NOT SAFE: {items}.', 'vi': 'CHƯA AN TOÀN: {items}.'},
    'g_now_ok': {'en': 'No known risk in the scanned scope.', 'vi': 'Không còn rủi ro đã biết trong phạm vi đã quét.'},
    'g_covered': {'en': 'What the scan checks (and guarantees once clean)', 'vi': 'Bản quét kiểm tra (và bảo đảm khi sạch)'},
    'g_not': {'en': 'What the scan does NOT cover (other measures needed)', 'vi': 'Bản quét KHÔNG bao phủ (cần biện pháp khác)'},
    'g_done': {'en': 'When can we tell the customer "done"', 'vi': 'Khi nào báo khách "đã xử lý xong"'},
    'g_residual': {'en': 'Residual risk after the checklist', 'vi': 'Rủi ro còn lại sau checklist'},
    'g_residual_none': {'en': 'None known: every vulnerable package has a fixed version.', 'vi': 'Không còn rủi ro đã biết: mọi package có lỗ hổng đều có bản sửa.'},
    'g_residual_pkg': {'en': '{p} {v}: no fixed version ({a}) — replace the package or accept the risk in writing.',
                       'vi': '{p} {v}: chưa có bản sửa ({a}) — thay package hoặc chấp nhận rủi ro bằng văn bản.'},
    'g_c': {'en': ['Known vulnerabilities (OSV.dev, GitHub advisories, CISA KEV) of every package locked in package-lock.json ({n} packages), as of {at}.',
                   'Support status of the Node.js branch and of the AWS Lambda runtime.',
                   'Every place that declares the Node.js version (SAM/CloudFormation, CDK, Dockerfile, CI, .nvmrc).',
                   'Code patterns of the Node.js breaking changes between {c} and {t}; engines.node of the dependencies; deprecated libraries.'],
            'vi': ['Lỗ hổng đã công bố (OSV.dev, GitHub advisory, CISA KEV) của mọi package trong package-lock.json ({n} package), tại thời điểm {at}.',
                   'Trạng thái hỗ trợ của nhánh Node.js và của runtime AWS Lambda.',
                   'Mọi chỗ khai báo phiên bản Node.js (SAM/CloudFormation, CDK, Dockerfile, CI, .nvmrc).',
                   'Mẫu mã chịu breaking change của Node.js từ {c} lên {t}; engines.node của dependency; thư viện đã ngừng hỗ trợ.']},
    'g_n': {'en': ['Vulnerabilities not published yet (0-day) and the ones published after {at}: scan again regularly.',
                   'Flaws in the project\'s own logic (authentication of reset_password/verify, injection, access control): code review, SAST, penetration test.',
                   'AWS configuration: IAM roles (least privilege on DynamoDB), API Gateway authorisation, secrets in environment variables, encryption, logging.',
                   'Packages outside package-lock.json (Lambda layers, bundled files) and behaviour changes without a code pattern (OpenSSL 3, fetch): tests.'],
            'vi': ['Lỗ hổng chưa công bố (0-day) và lỗ hổng công bố sau {at}: cần quét lại định kỳ.',
                   'Lỗi trong logic của chính dự án (xác thực reset_password/verify, injection, phân quyền): review mã, SAST, pentest.',
                   'Cấu hình AWS: IAM role (quyền tối thiểu trên DynamoDB), phân quyền API Gateway, secret trong biến môi trường, mã hoá, log.',
                   'Package ngoài package-lock.json (Lambda layer, file đóng gói sẵn) và thay đổi hành vi không có mẫu mã (OpenSSL 3, fetch): cần kiểm thử.']},
    'g_d': {'en': ['Every item of the checklist is done or explicitly accepted.',
                   'A new scan with the same command shows 0 critical/high vulnerability in production packages and no declaration left on Node.js {c}.',
                   'All functions run on Node.js {r} (supported until {e}) and the regression tests pass.',
                   'The before/after reports are kept as evidence; the scan is repeated every week and on every dependency change.'],
            'vi': ['Mọi mục trong checklist đã làm xong hoặc được chấp nhận rủi ro bằng văn bản.',
                   'Quét lại bằng cùng lệnh: 0 lỗ hổng critical/high trong package production và không còn khai báo Node.js {c}.',
                   'Mọi function chạy Node.js {r} (được hỗ trợ đến {e}) và kiểm thử hồi quy đạt.',
                   'Lưu báo cáo trước/sau làm bằng chứng; quét lại hằng tuần và mỗi khi đổi dependency.']},
    'g_statement': {'en': 'The scan guarantees the known risks above are closed at the time of the scan; it does not prove the absence of unknown vulnerabilities or logic flaws.',
                    'vi': 'Kết quả quét bảo đảm các rủi ro đã biết nêu trên được xử lý tại thời điểm quét; không chứng minh hệ thống không còn lỗ hổng chưa biết hay lỗi logic.'},
    # checklist
    'c_phase': {'en': 'Phase', 'vi': 'Giai đoạn'},
    'c_task': {'en': 'Task', 'vi': 'Việc cần làm'},
    'c_state': {'en': 'Status', 'vi': 'Trạng thái'},
    'todo': {'en': 'To do', 'vi': 'Cần làm'},
    'not_needed': {'en': 'Not needed', 'vi': 'Không cần'},
    'check': {'en': 'To check', 'vi': 'Cần kiểm tra'},
    'p_prep': {'en': 'Preparation', 'vi': 'Chuẩn bị'},
    'p_runtime': {'en': 'Runtime', 'vi': 'Runtime'},
    'p_security': {'en': 'Security of packages', 'vi': 'Bảo mật package'},
    'p_code': {'en': 'Code', 'vi': 'Mã nguồn'},
    'p_test': {'en': 'Tests', 'vi': 'Kiểm thử'},
    'p_deploy': {'en': 'Production', 'vi': 'Triển khai'},
    'p_verify': {'en': 'Confirmation', 'vi': 'Xác nhận'},
    'k_branch': {'en': 'Create a working branch; run the current tests on Node.js {c} as a baseline.',
                 'vi': 'Tạo nhánh làm việc; chạy bộ test hiện có trên Node.js {c} làm mốc.'},
    'k_version': {'en': 'Publish a Lambda version of every function and point the live alias to it (rollback target).',
                  'vi': 'Publish version Lambda cho từng function và trỏ alias đang chạy vào đó (điểm rollback).'},
    'k_decl': {'en': '{f}:{l} — {x} → {y}', 'vi': '{f}:{l} — {x} → {y}'},
    'k_decl_none': {'en': 'Node.js version declarations: already {t}.', 'vi': 'Khai báo phiên bản Node.js: đã là {t}.'},
    'k_vuln': {'en': 'Upgrade {p} {v} → {f} ({s}{flags})', 'vi': 'Nâng {p} {v} → {f} ({s}{flags})'},
    'k_vuln_nofix': {'en': 'Replace {p} {v} (no fixed version: {a})', 'vi': 'Thay {p} {v} (chưa có bản sửa: {a})'},
    'k_vuln_none': {'en': 'No vulnerable production package.', 'vi': 'Không có package production nào có lỗ hổng.'},
    'k_dev': {'en': 'Upgrade {n} vulnerable devDependencies (npm audit fix).', 'vi': 'Nâng {n} devDependencies có lỗ hổng (npm audit fix).'},
    'k_migrate': {'en': 'Migrate {p} → {r} (call sites: {n}; {proj}).', 'vi': 'Chuyển {p} → {r} (chỗ gọi: {n}; {proj}).'},
    'k_hits': {'en': 'Fix {n} code line(s) hit by breaking changes (details per project below).',
               'vi': 'Sửa {n} dòng mã vi phạm breaking change (chi tiết theo dự án bên dưới).'},
    'k_hits_none': {'en': 'Code: no breaking-change pattern found.', 'vi': 'Mã: không thấy mẫu breaking change.'},
    'k_engines': {'en': 'Upgrade {n} dependency(ies) whose engines.node excludes Node.js {t}.',
                  'vi': 'Nâng {n} dependency có engines.node không nhận Node.js {t}.'},
    'k_addons': {'en': 'Rebuild and load the native addons on Node.js {t}: {a}.', 'vi': 'Build lại và nạp thử native addon trên Node.js {t}: {a}.'},
    'k_local': {'en': 'Run unit/integration tests on Node.js {t} (local or CI).', 'vi': 'Chạy unit/integration test trên Node.js {t} (máy dev hoặc CI).'},
    'k_stage': {'en': 'Deploy to the test stage and test every function: {fn}.', 'vi': 'Deploy lên môi trường test và kiểm thử từng function: {fn}.'},
    'k_aws': {'en': 'Check DynamoDB and other AWS calls (permissions, timeouts, SDK errors) on the new runtime.',
              'vi': 'Kiểm tra các lời gọi DynamoDB và dịch vụ AWS khác (quyền, timeout, lỗi SDK) trên runtime mới.'},
    'k_canary': {'en': 'Deploy to production with weighted alias routing (10% → 100%).', 'vi': 'Deploy production bằng alias chia lưu lượng (10% → 100%).'},
    'k_watch': {'en': 'Watch CloudWatch Errors, Duration, Throttles for 24 h; rollback = point the alias back to the previous version.',
                'vi': 'Theo dõi CloudWatch Errors, Duration, Throttles trong 24 giờ; rollback = trỏ alias về version cũ.'},
    'k_rescan': {'en': 'Scan again: php-quickpatch.sh compat {p} --target {t} --report after.html — expect 0 critical/high.',
                 'vi': 'Quét lại: php-quickpatch.sh compat {p} --target {t} --report after.html — kỳ vọng 0 critical/high.'},
    'k_evidence': {'en': 'Send the before/after reports to the customer; schedule a weekly scan.',
                   'vi': 'Gửi báo cáo trước/sau cho khách; đặt lịch quét hằng tuần.'},
}


def tb(key, lang, **kw):
    s = TB[key].get(lang) or TB[key]['en']
    for k, v in kw.items():
        s = s.replace('{%s}' % k, str(v))
    return s


def _date(s):
    return datetime.date(*map(int, s[:10].split('-')))


def _workdays(start, n):
    """Date after N working days (Mon-Fri) counted from START (START itself is day 1 when a working day)."""
    d, left = start, n
    while d.weekday() >= 5:
        d += datetime.timedelta(days=1)
    while left > 1:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def _sev_text(counts, lang):
    return ', '.join('%s %d' % (tb(k, lang).lower() if k in TB else k, counts[k]) for k in SEV_ORDER if counts.get(k))


def _hours(kind, count):
    f_lo, u_lo, f_hi, u_hi = EFFORT.get(kind, (0, 0.5, 0, 2))
    return f_lo + u_lo * count, f_hi + u_hi * count


def build(res, lang, today=None):
    """Data of the brief (language-specific texts are rendered by html()/markdown())."""
    today = today or (res.get('lifecycle') or {}).get('today') or res['generated_at'][:10]
    tgt, cur = res['target_branch'], res.get('current_branch') or '?'
    lc = res.get('lifecycle') or {}
    rec = lc.get('recommended') or tgt
    target_ok = lc.get('target_ok', True)
    final = tgt if target_ok or not lc.get('recommended') else rec
    projects = res['projects']
    risks = []
    # 1. runtime
    c = lc.get('current') or {}
    if c.get('status') == 'EOL' and c.get('eol_date'):
        un = c.get('unpatched') or {}
        lvl = 'critical' if (un.get('kev') or un.get('critical')) else 'high'
        r = {'level': lvl, 'area': 'runtime', 'key': 'r_runtime_eol',
             'args': {'c': c['branch'], 'e': c['eol_date'], 'd': (_date(today) - _date(c['eol_date'])).days},
             'more': [], 'action': ('a_runtime', {'r': final})}
        n = sum(un.get(k) or 0 for k in ('critical', 'high', 'medium', 'low'))
        if n:
            r['more'].append(('r_runtime_cves', {'c': c['branch'], 'v': un.get('version'), 'n': n,
                                                 'sev': _sev_text(un, lang) + (', KEV %d' % un['kev'] if un.get('kev') else '')}))
        risks.append(r)
    # 2. AWS Lambda runtime
    decls = [d for p in projects for d in p['declarations']] + list(res.get('shared_declarations') or [])
    by_branch = {}
    for d in decls:
        if d['kind'] in ('lambda_runtime', 'cdk_runtime'):
            by_branch[d['branch']] = by_branch.get(d['branch'], 0) + 1
    for b, n in sorted(by_branch.items()):
        if b not in LAMBDA_RUNTIMES:
            continue
        dep, bc, bu = LAMBDA_RUNTIMES[b]
        args = {'c': b, 'dep': dep, 'bc': bc, 'bu': bu, 'n': n, 'd': (_date(dep) - _date(today)).days}
        if today >= bu:
            risks.append({'level': 'critical', 'area': 'platform', 'key': 'r_lambda_blocked', 'args': args, 'more': [],
                          'action': ('a_runtime', {'r': final})})
        elif today >= dep:
            risks.append({'level': 'high', 'area': 'platform', 'key': 'r_lambda_deprecated', 'args': args, 'more': [],
                          'action': ('a_runtime', {'r': final})})
        elif args['d'] <= 180:
            risks.append({'level': 'medium', 'area': 'platform', 'key': 'r_lambda_soon', 'args': args, 'more': [],
                          'action': ('a_runtime', {'r': final})})
    # 3. vulnerable production packages (unique package@version over the projects)
    prod, dev = {}, {}
    for p in projects:
        for v in p['vulnerabilities'] or []:
            key = (v['package'], v['version'])
            (dev if v['dev'] else prod).setdefault(key, v)
    if prod:
        cnt = {}
        for v in prod.values():
            cnt[v['severity']] = cnt.get(v['severity'], 0) + 1
        top = sorted(prod.values(), key=lambda v: (SEV_ORDER.index(v['severity']) if v['severity'] in SEV_ORDER else 9,
                                                   v['package']))
        worst = next((s for s in SEV_ORDER if cnt.get(s)), 'medium')
        kev = sum(1 for v in prod.values() if v.get('in_kev') or v.get('is_malware'))
        nofix = sum(1 for v in prod.values() if not v['fix_version'])
        r = {'level': 'critical' if kev else (worst if worst in LEVELS else 'medium'), 'area': 'dependency', 'key': 'r_deps',
             'args': {'n': len(prod), 'sev': _sev_text(cnt, lang),
                      'top': ', '.join('%s %s' % (v['package'], v['version']) for v in top[:6]) + (' …' if len(top) > 6 else '')},
             'more': [('r_deps_kev', {'n': kev})] if kev else [],
             'action': ('a_deps', {'nofix': nofix}) if nofix else ('a_deps_all', {})}
        risks.append(r)
    # 4. libraries out of support / deprecated
    libs = {}
    for p in projects:
        for d in p['deprecated']:
            x = libs.setdefault(d['package'], {'d': d, 'sites': 0, 'projects': []})
            x['sites'] += len(d.get('call_sites') or [])
            x['projects'].append(p['name'])
    for name, x in sorted(libs.items()):
        if name in LIB_EOL:
            e, repl = LIB_EOL[name]
            risks.append({'level': 'high' if today >= e else 'medium', 'area': 'library', 'key': 'r_lib_eol',
                          'args': {'p': name, 'e': e, 'n': x['sites']}, 'more': [], 'action': ('a_lib_eol', {'r': repl})})
        else:
            alt = x['d'].get('replacement') or lib_alt(name, lang)
            risks.append({'level': 'medium', 'area': 'library', 'key': 'r_lib_dep',
                          'args': {'p': name, 'm': (x['d'].get('message') or '')[:160]}, 'more': [],
                          'action': ('a_lib_eol', {'r': alt}) if alt else ('a_lib_any', {})})
    if dev:
        risks.append({'level': 'low', 'area': 'dev', 'key': 'r_dev', 'args': {'n': len(dev)}, 'more': [],
                      'action': ('a_none', {})})
    unchecked = [p for p in projects if p['vulnerabilities'] is None]
    if unchecked:
        risks.append({'level': 'high', 'area': 'dependency', 'key': 'r_unchecked', 'args': {'n': len(unchecked)},
                      'more': [], 'action': ('a_none', {})})
    risks.sort(key=lambda r: LEVELS.index(r['level']))

    # effort
    rows, agg = [], {}
    for p in projects:
        for w in p['work_items']:
            k = (w['kind'], w.get('package'))
            agg.setdefault(k, {'kind': w['kind'], 'package': w.get('package'), 'count': 0, 'projects': 0})
            agg[k]['count'] += w['count'] if w['kind'] != 'regression_test' else 1
            agg[k]['projects'] += 1
    shared = sum(1 for d in res.get('shared_declarations') or [] if d['to_change'])
    if shared:
        k = ('runtime_declarations', None)
        agg.setdefault(k, {'kind': 'runtime_declarations', 'package': None, 'count': 0, 'projects': 0})
        agg[k]['count'] += shared
    lo_t = hi_t = 0.0
    for a in agg.values():
        if a['kind'] in ('regression_test',):
            lo, hi = _hours(a['kind'], 0)
            lo, hi = lo * a['projects'], hi * a['projects']
        elif a['kind'] == 'migrate_package' and not libs.get(a['package'], {}).get('sites'):
            lo, hi = 0.5 * a['projects'], 2.0 * a['projects']      # nothing calls it directly: drop or replace the dependency
        elif a['kind'] in ('migrate_package', 'runtime_declarations', 'vuln_minor_upgrades', 'vuln_major_upgrades'):
            f_lo, u_lo, f_hi, u_hi = EFFORT[a['kind']]
            lo = f_lo * max(1, a['projects']) + u_lo * a['count']
            hi = f_hi * max(1, a['projects']) + u_hi * a['count']
        else:
            lo, hi = _hours(a['kind'], a['count'])
        lo_t += lo
        hi_t += hi
        rows.append({'kind': a['kind'], 'package': a['package'], 'count': a['count'], 'hours': [round(lo, 1), round(hi, 1)]})
    d_lo, d_hi = max(1, int(-(-lo_t // 8))), max(1, int(-(-hi_t // 8)))
    effort = {'rows': rows, 'hours': [round(lo_t, 1), round(hi_t, 1)], 'days': [d_lo, d_hi],
              'staging_days': list(STAGING_DAYS), 'prod_days': PROD_DAYS[0]}
    # schedule
    start = _date(today)
    urgent_h = sum(r['hours'][1] for r in rows if r['kind'] in ('runtime_declarations', 'vuln_minor_upgrades'))
    sched = [
        {'phase': 's_dev', 'days': [d_lo, d_hi]},
        {'phase': 's_staging', 'days': list(STAGING_DAYS)},
        {'phase': 's_prod', 'days': list(PROD_DAYS)},
    ]
    total_lo = d_lo + STAGING_DAYS[0] + PROD_DAYS[0]
    total_hi = d_hi + STAGING_DAYS[1] + PROD_DAYS[1]
    schedule = {'start': start.isoformat(), 'phases': sched,
                'prod_from': _workdays(start, total_lo).isoformat(), 'prod_to': _workdays(start, total_hi).isoformat(),
                'urgent_days': max(1, int(-(-urgent_h // 8))) + 1}
    # assurance
    bad = []
    for r in risks:
        if r['level'] in ('critical', 'high'):
            bad.append(r['area'])
    residual = [{'package': v['package'], 'version': v['version'],
                 'advisories': v.get('unfixed_advisories') or v['advisories']}
                for v in prod.values() if not v['fix_version'] or v.get('unfixed_advisories')]
    packages = sum(p.get('packages') or 0 for p in projects)
    assurance = {'safe_now': not bad, 'problems': sorted(set(bad)), 'residual': residual, 'packages_checked': packages,
                 'unchecked_projects': [p['name'] for p in unchecked], 'at': res['generated_at'][:16].replace('T', ' ') + ' UTC',
                 'final_target': final, 'final_eol': ((lc.get('target') or {}).get('eol_date') if final == tgt
                                                      else lc.get('recommended_eol'))}
    # checklist
    cl = []

    def add(phase, key, status, **args):
        cl.append({'phase': phase, 'key': key, 'status': status, 'args': args})
    add('p_prep', 'k_branch', 'todo', c=cur)
    add('p_prep', 'k_version', 'todo' if by_branch else 'check')
    changing = [d for d in decls if d['to_change']]
    for d in changing:
        add('p_runtime', 'k_decl', 'todo', f=d.get('file'), l=d.get('line'), x=d.get('text'),
            y=_suggest(d, final))
    if not changing:
        add('p_runtime', 'k_decl_none', 'not_needed', t=final)
    for v in sorted(prod.values(), key=lambda v: (SEV_ORDER.index(v['severity']) if v['severity'] in SEV_ORDER else 9,
                                                  v['package'])):
        flags = (', KEV' if v.get('in_kev') else '') + (', major' if v.get('major_bump') else '')
        if v['fix_version']:
            add('p_security', 'k_vuln', 'todo', p=v['package'], v=v['version'], f=v['fix_version'], s=v['severity'],
                flags=flags)
        else:
            add('p_security', 'k_vuln_nofix', 'todo', p=v['package'], v=v['version'], a=', '.join(v['advisories'][:3]))
    if not prod and not unchecked:
        add('p_security', 'k_vuln_none', 'not_needed')
    if dev:
        add('p_security', 'k_dev', 'todo', n=len(dev))
    for name, x in sorted(libs.items()):
        alt = (LIB_EOL.get(name) or (None, x['d'].get('replacement') or lib_alt(name, lang)))[1]
        add('p_code', 'k_migrate', 'todo', p=name, r=alt or tb('a_lib_any', lang).rstrip('.').lower(),
            n=x['sites'] if x['sites'] else tb('sites_none', lang), proj=', '.join(x['projects']))
    nhits = sum(len(p['hits']) for p in projects)
    if nhits:
        add('p_code', 'k_hits', 'todo', n=nhits)
    else:
        add('p_code', 'k_hits_none', 'not_needed')
    eng = sum(1 for p in projects for v in p['npm_engine_violations'] if v.get('severity') == 'error')
    if eng:
        add('p_code', 'k_engines', 'todo', n=eng, t=final)
    addons = sorted({a['package'] for p in projects for a in p['native_addons']})
    if addons:
        add('p_code', 'k_addons', 'todo', t=final, a=', '.join(addons))
    add('p_test', 'k_local', 'todo', t=final)
    add('p_test', 'k_stage', 'todo', fn=', '.join(p['name'] for p in projects))
    add('p_test', 'k_aws', 'check')
    add('p_deploy', 'k_canary', 'todo')
    add('p_deploy', 'k_watch', 'todo')
    add('p_verify', 'k_rescan', 'todo', t=final, p=' '.join('--path %s' % x for x in res['paths']))
    add('p_verify', 'k_evidence', 'todo')
    return {'risks': risks, 'effort': effort, 'schedule': schedule, 'assurance': assurance, 'checklist': cl,
            'final_target': final}


def _suggest(d, target):
    txt = d.get('text') or ''
    if d['kind'] == 'lambda_runtime':
        return txt.replace('nodejs%s.x' % d['branch'], 'nodejs%s.x' % target)
    if d['kind'] == 'cdk_runtime':
        return txt.replace('NODEJS_%s_X' % d['branch'], 'NODEJS_%s_X' % target)
    if d['kind'] == 'version_file':
        return target
    return txt.replace(d['branch'], target, 1)


def to_json(b):
    """JSON form stored in result.brief (texts are not stored, only keys and arguments)."""
    def risk(r):
        return {'level': r['level'], 'area': r['area'], 'key': r['key'], 'args': r['args'],
                'more': [{'key': k, 'args': a} for k, a in r['more']],
                'action': {'key': r['action'][0], 'args': r['action'][1]}}
    return {'risks': [risk(r) for r in b['risks']], 'effort': b['effort'], 'schedule': b['schedule']['phases'],
            'schedule_window': {k: b['schedule'][k] for k in ('start', 'prod_from', 'prod_to', 'urgent_days')},
            'assurance': b['assurance'], 'checklist': b['checklist'], 'final_target': b['final_target']}


# --- texts shared by HTML and Markdown -------------------------------------------------------
def upgrade_lines(res, b, lang):
    tgt, cur = res['target_branch'], res.get('current_branch') or '?'
    lc = res.get('lifecycle') or {}
    st = [p['verdict']['status'] for p in res['projects']]
    out = []
    if 'FAIL' in st:
        n = sum(p['verdict']['errors'] + p['verdict']['blockers'] for p in res['projects'])
        out.append(tb('u_fix_first', lang, n=n))
    elif 'PENDING' in st or not st:
        parts = sorted({x for p in res['projects'] for x in p['verdict']['pending_parts']})
        out.append(tb('u_pending', lang, parts=', '.join(parts) or '-'))
    else:
        out.append(tb('u_yes', lang, t=tgt))
    t = lc.get('target') or {}
    if lc and not lc.get('target_ok') and lc.get('recommended'):
        if t.get('status') == 'EOL':
            why = tb('u_target_eol', lang, e=t.get('eol_date') or '?')
        else:
            why = tb('u_target_short', lang, e=t.get('eol_date') or '?', d=t.get('days_to_eol'))
        out.append(tb('u_target_bad', lang, t=tgt, why=why, r=lc['recommended']))
    elif t.get('eol_date'):
        out.append(tb('u_target_ok', lang, t=tgt, e=t['eol_date']))
    imp = []
    n = sum(1 for c in b['checklist'] if c['key'] == 'k_decl')
    if n:
        imp.append(tb('i_runtime', lang, n=n))
    vul = [c for c in b['checklist'] if c['key'] in ('k_vuln', 'k_vuln_nofix')]
    if vul:
        imp.append(tb('i_deps', lang, n=len(vul), m=sum(1 for c in vul if 'major' in c['args'].get('flags', ''))))
    for c in b['checklist']:
        if c['key'] == 'k_migrate' and isinstance(c['args']['n'], int):
            imp.append(tb('i_migrate', lang, p=c['args']['p'], n=c['args']['n']))
    nh = sum(len(p['hits']) for p in res['projects'])
    imp.append(tb('i_code', lang, n=nh) if nh else tb('i_none_code', lang, c=cur, t=b['final_target']))
    imp.append(tb('i_downtime', lang))
    return out, imp


def effort_label(row, lang, final):
    from .report import KINDS, kind_label
    if row['kind'] == 'regression_test':
        return tb('regression_test', lang, t=final)
    if row['kind'] in KINDS:
        return kind_label({'kind': row['kind'], 'package': row.get('package')}, lang)
    return row['kind']


def _fmt_h(x):
    return ('%.1f' % x).rstrip('0').rstrip('.')


SHORT = {'r_runtime_eol': 's_runtime', 'r_lambda_blocked': 's_platform', 'r_lambda_deprecated': 's_platform',
         'r_deps': 's_deps', 'r_lib_eol': 's_lib', 'r_unchecked': 's_unchecked'}


def _short(r, lang):
    return tb(SHORT[r['key']], lang, **r['args']) if r['key'] in SHORT else _risk_text(r, lang)


def _risk_text(r, lang):
    s = tb(r['key'], lang, **r['args'])
    for k, a in r['more']:
        s += ' ' + tb(k, lang, **a)
    return s


def _check_text(c, lang):
    return tb(c['key'], lang, **c['args'])


def e(v):
    return html.escape('' if v is None else str(v), quote=True)


def html_section(res, b, lang):
    o = ['<h2>%s</h2>' % e(tb('answers', lang))]
    # 1 risks
    o.append('<h3>%s</h3>' % e(tb('q1', lang)))
    if b['risks']:
        o.append('<div class="wrap"><table><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>' % (
            e(tb('level', lang)), e(tb('risk', lang)), e(tb('action', lang))))
        for r in b['risks']:
            o.append('<tr><td><span class="badge lv-%s">%s</span></td><td>%s</td><td>%s</td></tr>' % (
                e(r['level']), e(tb(r['level'], lang)), e(_risk_text(r, lang)), e(tb(r['action'][0], lang, **r['action'][1]))))
        o.append('</tbody></table></div>')
        if any(r['area'] == 'platform' for r in b['risks']):
            o.append('<p class="meta">AWS Lambda: <code>%s</code></p>' % e(LAMBDA_SOURCE))
    else:
        o.append('<div class="msg ok">%s</div>' % e(tb('no_risk', lang)))
    # 2 upgrade
    up, imp = upgrade_lines(res, b, lang)
    o.append('<h3>%s</h3><ul>%s</ul>' % (e(tb('q2', lang)), ''.join('<li>%s</li>' % e(x) for x in up)))
    o.append('<p><b>%s</b></p><ul>%s</ul>' % (e(tb('impact', lang)), ''.join('<li>%s</li>' % e(x) for x in imp)))
    # 3 effort
    ef = b['effort']
    o.append('<h3>%s</h3>' % e(tb('q3', lang)))
    o.append('<div class="wrap"><table><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>' % (
        e(tb('e_item', lang)), e(tb('e_count', lang)), e(tb('e_hours', lang))))
    for r in ef['rows']:
        o.append('<tr><td>%s</td><td class="n">%s</td><td class="n">%s–%s</td></tr>' % (
            e(effort_label(r, lang, b['final_target'])), e(r['count']), e(_fmt_h(r['hours'][0])), e(_fmt_h(r['hours'][1]))))
    o.append('<tr><th>%s</th><th></th><th class="n">%s–%s</th></tr></tbody></table></div>' % (
        e(tb('e_total', lang)), e(_fmt_h(ef['hours'][0])), e(_fmt_h(ef['hours'][1]))))
    o.append('<p><b>%s</b></p><p class="meta">%s</p>' % (
        e(tb('e_days', lang, lo=ef['days'][0], hi=ef['days'][1], s1=ef['staging_days'][0], s2=ef['staging_days'][1],
             p=ef['prod_days'])), e(tb('e_note', lang))))
    # 4 schedule
    sc = b['schedule']
    o.append('<h3>%s</h3>' % e(tb('q4', lang)))
    o.append('<div class="wrap"><table><thead><tr><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div>' % (
        e(tb('s_phase', lang)), e(tb('s_days', lang)), ''.join(
            '<tr><td>%s</td><td class="n">%s</td></tr>' % (e(tb(p['phase'], lang)),
                                                           e('%d' % p['days'][0] if p['days'][0] == p['days'][1]
                                                             else '%d–%d' % tuple(p['days'])))
            for p in sc['phases'])))
    o.append('<p><b>%s</b></p>' % e(tb('s_answer', lang, a=sc['prod_from'], b=sc['prod_to'], d=sc['start'],
                                       u=sc['urgent_days'])))
    # 5 assurance
    a = b['assurance']
    o.append('<h3>%s</h3>' % e(tb('q5', lang)))
    if a['safe_now']:
        o.append('<div class="msg ok"><b>%s:</b> %s</div>' % (e(tb('g_now', lang)), e(tb('g_now_ok', lang))))
    else:
        items = '; '.join(_short(r, lang) for r in b['risks'] if r['level'] in ('critical', 'high'))
        o.append('<div class="msg bad"><b>%s:</b> %s</div>' % (e(tb('g_now', lang)), e(tb('g_now_bad', lang, items=items))))
    args = {'n': a['packages_checked'], 'at': a['at'], 'c': res.get('current_branch') or '?', 't': b['final_target'],
            'r': b['final_target'], 'e': a.get('final_eol') or '?'}
    for key, title in (('g_c', 'g_covered'), ('g_n', 'g_not'), ('g_d', 'g_done')):
        o.append('<p><b>%s</b></p><ul>%s</ul>' % (e(tb(title, lang)), ''.join(
            '<li>%s</li>' % e(_fill(x, args)) for x in TB[key][lang if lang in TB[key] else 'en'])))
    o.append('<p><b>%s</b></p><ul>%s</ul>' % (e(tb('g_residual', lang)), ''.join(
        '<li>%s</li>' % e(tb('g_residual_pkg', lang, p=x['package'], v=x['version'], a=', '.join(x['advisories'][:3])))
        for x in a['residual']) or '<li>%s</li>' % e(tb('g_residual_none', lang))))
    o.append('<div class="msg warn">%s</div>' % e(tb('g_statement', lang)))
    # checklist
    o.append('<h2>%s</h2>' % e(tb('checklist', lang)))
    o.append('<div class="wrap"><table><thead><tr><th></th><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>' % (
        e(tb('c_phase', lang)), e(tb('c_task', lang)), e(tb('c_state', lang))))
    for c in b['checklist']:
        box = '&#9745;' if c['status'] == 'not_needed' else '&#9744;'
        o.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            box, e(tb(c['phase'], lang)), e(_check_text(c, lang)), e(tb(c['status'], lang))))
    o.append('</tbody></table></div>')
    return ''.join(o)


def _fill(s, args):
    for k, v in args.items():
        s = s.replace('{%s}' % k, str(v))
    return s


def md_section(res, b, lang, md):
    o = ['## %s\n' % tb('answers', lang), '### %s\n' % tb('q1', lang)]
    if b['risks']:
        o.append('| %s | %s | %s |\n| --- | --- | --- |' % (tb('level', lang), tb('risk', lang), tb('action', lang)))
        for r in b['risks']:
            o.append('| **%s** | %s | %s |' % (md(tb(r['level'], lang)), md(_risk_text(r, lang)),
                                              md(tb(r['action'][0], lang, **r['action'][1]))))
        o.append('')
        if any(r['area'] == 'platform' for r in b['risks']):
            o.append('_AWS Lambda: %s_\n' % LAMBDA_SOURCE)
    else:
        o.append(tb('no_risk', lang) + '\n')
    up, imp = upgrade_lines(res, b, lang)
    o.append('### %s\n' % tb('q2', lang))
    o.extend('- %s' % md(x) for x in up)
    o.append('\n**%s**\n' % tb('impact', lang))
    o.extend('- %s' % md(x) for x in imp)
    ef = b['effort']
    o.append('\n### %s\n' % tb('q3', lang))
    o.append('| %s | %s | %s |\n| --- | ---: | ---: |' % (tb('e_item', lang), tb('e_count', lang), tb('e_hours', lang)))
    for r in ef['rows']:
        o.append('| %s | %s | %s–%s |' % (md(effort_label(r, lang, b['final_target'])), r['count'],
                                         _fmt_h(r['hours'][0]), _fmt_h(r['hours'][1])))
    o.append('| **%s** | | **%s–%s** |\n' % (tb('e_total', lang), _fmt_h(ef['hours'][0]), _fmt_h(ef['hours'][1])))
    o.append('**%s**\n' % md(tb('e_days', lang, lo=ef['days'][0], hi=ef['days'][1], s1=ef['staging_days'][0],
                                 s2=ef['staging_days'][1], p=ef['prod_days'])))
    o.append('_%s_\n' % md(tb('e_note', lang)))
    sc = b['schedule']
    o.append('### %s\n' % tb('q4', lang))
    o.append('| %s | %s |\n| --- | ---: |' % (tb('s_phase', lang), tb('s_days', lang)))
    for p in sc['phases']:
        o.append('| %s | %s |' % (md(tb(p['phase'], lang)),
                                  '%d' % p['days'][0] if p['days'][0] == p['days'][1] else '%d–%d' % tuple(p['days'])))
    o.append('\n**%s**\n' % md(tb('s_answer', lang, a=sc['prod_from'], b=sc['prod_to'], d=sc['start'], u=sc['urgent_days'])))
    a = b['assurance']
    o.append('### %s\n' % tb('q5', lang))
    if a['safe_now']:
        o.append('**%s:** %s\n' % (tb('g_now', lang), md(tb('g_now_ok', lang))))
    else:
        items = '; '.join(_short(r, lang) for r in b['risks'] if r['level'] in ('critical', 'high'))
        o.append('**%s:** %s\n' % (tb('g_now', lang), md(tb('g_now_bad', lang, items=items))))
    args = {'n': a['packages_checked'], 'at': a['at'], 'c': res.get('current_branch') or '?', 't': b['final_target'],
            'r': b['final_target'], 'e': a.get('final_eol') or '?'}
    for key, title in (('g_c', 'g_covered'), ('g_n', 'g_not'), ('g_d', 'g_done')):
        o.append('**%s**\n' % tb(title, lang))
        o.extend('- %s' % md(_fill(x, args)) for x in TB[key][lang if lang in TB[key] else 'en'])
        o.append('')
    o.append('**%s**\n' % tb('g_residual', lang))
    o.extend('- %s' % md(tb('g_residual_pkg', lang, p=x['package'], v=x['version'], a=', '.join(x['advisories'][:3])))
             for x in a['residual'])
    if not a['residual']:
        o.append('- %s' % md(tb('g_residual_none', lang)))
    o.append('\n> %s\n' % md(tb('g_statement', lang)))
    o.append('## %s\n' % tb('checklist', lang))
    phase = None
    for c in b['checklist']:
        if c['phase'] != phase:
            phase = c['phase']
            o.append('\n**%s**\n' % tb(phase, lang))
        o.append('- [%s] %s%s' % ('x' if c['status'] == 'not_needed' else ' ', md(_check_text(c, lang)),
                                  ' _(%s)_' % tb(c['status'], lang) if c['status'] != 'todo' else ''))
    o.append('')
    return '\n'.join(o)
