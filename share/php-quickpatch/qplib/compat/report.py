"""Report of `compat --path` (CR-01): one self-contained HTML page or Markdown, English or Vietnamese.

Every value from the scanned code (paths, snippets, package names, advisory
text) is escaped; the page has no script and no external resource.
"""
import html
import os

from .. import VERSION

T = {
    'title': {'en': 'Node.js compatibility report', 'vi': 'Báo cáo tương thích Node.js'},
    'generated': {'en': 'Generated', 'vi': 'Tạo lúc'},
    'tool': {'en': 'Tool', 'vi': 'Công cụ'},
    'paths': {'en': 'Scanned paths', 'vi': 'Thư mục quét'},
    'data': {'en': 'Data', 'vi': 'Dữ liệu'},
    'summary': {'en': 'Summary', 'vi': 'Tóm tắt'},
    'overall': {'en': 'Overall result', 'vi': 'Kết luận chung'},
    'projects': {'en': 'Projects', 'vi': 'Dự án'},
    'project': {'en': 'Project', 'vi': 'Dự án'},
    'vulnerable': {'en': 'Packages with known vulnerabilities', 'vi': 'Package có lỗ hổng đã biết'},
    'runtime_changes': {'en': 'Places declaring the Node.js version to change', 'vi': 'Chỗ khai báo phiên bản Node.js cần đổi'},
    'deprecated_n': {'en': 'Packages to migrate or replace', 'vi': 'Package cần chuyển đổi/thay thế'},
    'code_errors': {'en': 'Breaking-change findings (error)', 'vi': 'Vi phạm breaking change (mức error)'},
    'lifecycle': {'en': 'Node.js lifecycle', 'vi': 'Vòng đời Node.js'},
    'branch': {'en': 'Branch', 'vi': 'Nhánh'},
    'status': {'en': 'Status', 'vi': 'Trạng thái'},
    'eol': {'en': 'End of life', 'vi': 'Hết hỗ trợ'},
    'days_left': {'en': 'Days left', 'vi': 'Còn (ngày)'},
    'latest': {'en': 'Latest release', 'vi': 'Bản mới nhất'},
    'current': {'en': 'Current', 'vi': 'Hiện tại'},
    'target': {'en': 'Target', 'vi': 'Đích'},
    'recommended': {'en': 'Recommended', 'vi': 'Khuyến nghị'},
    'no_lifecycle': {'en': 'No lifecycle data (no feeds bundle): run `php-quickpatch.sh feeds update`.',
                     'vi': 'Chưa có dữ liệu vòng đời (chưa có bundle feeds): chạy `php-quickpatch.sh feeds update`.'},
    'target_short': {'en': 'Node.js {t} has {d} days of support left (less than {m} days required for a target). '
                           'Node.js {r} is recommended.',
                     'vi': 'Node.js {t} chỉ còn {d} ngày hỗ trợ (đích cần còn ít nhất {m} ngày). '
                           'Khuyến nghị Node.js {r}.'},
    'target_closed': {'en': 'Node.js {t} is {s}: do not use it as a target. Node.js {r} is recommended.',
                      'vi': 'Node.js {t} đang ở trạng thái {s}: không nên chọn làm đích. Khuyến nghị Node.js {r}.'},
    'target_good': {'en': 'Node.js {t} is a supported target until {e}.',
                    'vi': 'Node.js {t} là đích được hỗ trợ tới {e}.'},
    'current_eol': {'en': 'Node.js {c} reached end of life on {e}: no more security fixes.',
                    'vi': 'Node.js {c} đã hết hỗ trợ từ {e}: không còn bản vá bảo mật.'},
    'work': {'en': 'Work to do', 'vi': 'Khối lượng việc'},
    'work_note': {'en': 'Sizes are hints for estimation (S: configuration or patch upgrade, M: code change and '
                        'retest, L: migration across many call sites), not an estimate in days.',
                  'vi': 'Mức S/M/L chỉ là gợi ý để ước lượng (S: đổi cấu hình hoặc nâng bản vá, M: sửa mã và '
                        'kiểm thử lại, L: chuyển đổi ở nhiều chỗ gọi), không phải số ngày công.'},
    'item': {'en': 'Item', 'vi': 'Hạng mục'},
    'count': {'en': 'Count', 'vi': 'Số lượng'},
    'size': {'en': 'Size', 'vi': 'Mức'},
    'decls': {'en': 'Node.js version declarations', 'vi': 'Khai báo phiên bản Node.js'},
    'file': {'en': 'File', 'vi': 'File'},
    'line': {'en': 'Line', 'vi': 'Dòng'},
    'kind': {'en': 'Kind', 'vi': 'Loại'},
    'change_to': {'en': 'Change', 'vi': 'Đổi thành'},
    'unchanged': {'en': 'already on target', 'vi': 'đã đúng đích'},
    'vulns': {'en': 'Known vulnerabilities (OSV)', 'vi': 'Lỗ hổng đã biết (OSV)'},
    'package': {'en': 'Package', 'vi': 'Package'},
    'version': {'en': 'Version', 'vi': 'Phiên bản'},
    'severity': {'en': 'Severity', 'vi': 'Mức'},
    'advisories': {'en': 'Advisories', 'vi': 'Advisory'},
    'fix': {'en': 'Upgrade to', 'vi': 'Nâng lên'},
    'no_fix': {'en': 'no fixed version', 'vi': 'chưa có bản sửa'},
    'major': {'en': 'new major', 'vi': 'đổi major'},
    'dev': {'en': 'dev only', 'vi': 'chỉ dev'},
    'kev': {'en': 'KEV', 'vi': 'KEV'},
    'malware': {'en': 'MALWARE', 'vi': 'MÃ ĐỘC'},
    'no_vulns': {'en': 'No known vulnerability in the locked packages.', 'vi': 'Không có lỗ hổng đã biết trong các package đã khoá.'},
    'vulns_skipped': {'en': 'Not checked.', 'vi': 'Chưa kiểm tra được.'},
    'deprecated': {'en': 'Packages to migrate or replace', 'vi': 'Package cần chuyển đổi hoặc thay thế'},
    'replacement': {'en': 'Replacement', 'vi': 'Thay bằng'},
    'reason': {'en': 'Reason', 'vi': 'Lý do'},
    'call_sites': {'en': 'Call sites', 'vi': 'Chỗ gọi'},
    'engines': {'en': 'Dependencies whose engines.node excludes the target', 'vi': 'Dependency có engines.node không nhận Node đích'},
    'engines_c': {'en': 'engines.node', 'vi': 'engines.node'},
    'hits': {'en': 'Code affected by breaking changes', 'vi': 'Mã bị ảnh hưởng bởi breaking change'},
    'rule': {'en': 'Rule', 'vi': 'Luật'},
    'level': {'en': 'Level', 'vi': 'Mức'},
    'code': {'en': 'Code', 'vi': 'Mã'},
    'no_hits': {'en': 'No breaking-change pattern found in the code.', 'vi': 'Không thấy mẫu breaking change nào trong mã.'},
    'rules': {'en': 'Breaking changes in the range', 'vi': 'Các breaking change trong dải'},
    'addons': {'en': 'Native addons', 'vi': 'Native addon'},
    'load_ok': {'en': 'loads on the target', 'vi': 'nạp được trên Node đích'},
    'load_fail': {'en': 'does NOT load on the target', 'vi': 'KHÔNG nạp được trên Node đích'},
    'load_unknown': {'en': 'not tested (give --node-bin)', 'vi': 'chưa thử (cần --node-bin)'},
    'notes': {'en': 'Notes', 'vi': 'Ghi chú'},
    'errors': {'en': 'Errors', 'vi': 'Lỗi'},
    'current_from': {'en': 'Current branch from', 'vi': 'Nhánh hiện tại lấy từ'},
    'files': {'en': 'JavaScript/TypeScript files scanned', 'vi': 'File JavaScript/TypeScript đã quét'},
    'locked': {'en': 'Locked packages', 'vi': 'Package trong lockfile'},
    'shared': {'en': 'Declarations outside the projects (CI, shared files)', 'vi': 'Khai báo ngoài các dự án (CI, file dùng chung)'},
    'method': {'en': 'How this report was made', 'vi': 'Cách lập báo cáo'},
    'limits': {'en': 'Limits', 'vi': 'Giới hạn'},
    'method_text': {
        'en': ['Vulnerabilities: OSV.dev for every package of package-lock.json; "Upgrade to" is the smallest version '
               'that fixes every advisory of the package.',
               'Deprecated packages: npm registry metadata of the direct dependencies, plus the migrations the tool '
               'knows (AWS SDK v2).',
               'Breaking changes: the rules of the php-quickpatch catalog for every Node.js major in (current, target], '
               'matched in the project code (node_modules excluded).',
               'Lifecycle: the php-quickpatch feeds bundle (endoflife.date, Node.js release schedule); a target must '
               'have at least 365 days of support left.'],
        'vi': ['Lỗ hổng: tra OSV.dev cho mọi package trong package-lock.json; cột "Nâng lên" là bản nhỏ nhất sửa '
               'được mọi advisory của package đó.',
               'Package hết hỗ trợ: metadata npm registry của dependency trực tiếp, cộng các chuyển đổi tool biết sẵn '
               '(AWS SDK v2).',
               'Breaking change: bộ luật trong catalog php-quickpatch cho mọi bản major Node.js trong dải (hiện tại, '
               'đích], so khớp trong mã của dự án (bỏ node_modules).',
               'Vòng đời: bundle feeds của php-quickpatch (endoflife.date, lịch phát hành Node.js); đích phải còn ít '
               'nhất 365 ngày hỗ trợ.']},
    'limits_text': {
        'en': ['Pattern matching finds likely call sites; it does not prove the code is correct on the target. '
               'Run the project tests on the target before switching.',
               'The tool does not change or deploy anything: runtime settings (Lambda, containers, CI) and package '
               'upgrades are done by the team.',
               'Behaviour changes without a code pattern (OpenSSL 3, fetch/undici, ESM loading) need tests.'],
        'vi': ['So khớp mẫu chỉ chỉ ra chỗ có khả năng bị ảnh hưởng, không chứng minh mã chạy đúng trên đích. '
               'Cần chạy test của dự án trên Node đích trước khi chuyển.',
               'Tool không sửa hay deploy gì: đổi runtime (Lambda, container, CI) và nâng package do team thực hiện.',
               'Thay đổi hành vi không có mẫu trong mã (OpenSSL 3, fetch/undici, nạp ESM) cần kiểm thử.']},
    'PASS': {'en': 'PASS', 'vi': 'ĐẠT'},
    'FAIL': {'en': 'FAIL', 'vi': 'KHÔNG ĐẠT'},
    'PENDING': {'en': 'INCOMPLETE', 'vi': 'CHƯA ĐỦ DỮ LIỆU'},
    'verdict_note': {
        'en': 'PASS/FAIL is about running on the target Node.js; known vulnerabilities are listed apart.',
        'vi': 'ĐẠT/KHÔNG ĐẠT xét khả năng chạy trên Node đích; lỗ hổng bảo mật liệt kê riêng.'},
    'option': {'en': '--current option', 'vi': 'tham số --current'},
    'declarations': {'en': 'its declarations', 'vi': 'khai báo của dự án'},
    'repository': {'en': 'repository declarations', 'vi': 'khai báo chung của repo'},
    'engines_src': {'en': 'package.json engines', 'vi': 'engines của package.json'},
    'unknown': {'en': 'unknown', 'vi': 'không rõ'},
    'shared_col': {'en': 'Shared', 'vi': 'Chung'},
    'c_pass': {'en': 'Upgrading to Node.js {t}: no compatibility blocker found in the code and dependencies.',
               'vi': 'Nâng lên Node.js {t}: không phát hiện điểm chặn tương thích trong mã và dependency.'},
    'c_fail': {'en': 'Not ready for Node.js {t} yet: {n} blocker(s) to fix first (code, engines, native addons).',
               'vi': 'Chưa nâng ngay lên Node.js {t} được: còn {n} điểm chặn phải sửa trước (mã, engines, native addon).'},
    'c_pending': {'en': 'Not enough data for a conclusion on Node.js {t}: {parts}.',
                  'vi': 'Chưa đủ dữ liệu để kết luận cho Node.js {t}: {parts}.'},
    'c_vuln': {'en': 'Security: {n} vulnerable package version(s) in production dependencies ({sev}); {fix} fixed by an '
                     'upgrade ({major} to a new major), {nofix} with no fixed version.',
               'vi': 'Bảo mật: {n} package có lỗ hổng trong dependency production ({sev}); {fix} sửa được bằng nâng '
                     'phiên bản ({major} phải lên major mới), {nofix} chưa có bản sửa.'},
    'c_novuln': {'en': 'Security: no known vulnerability in production dependencies.',
                 'vi': 'Bảo mật: không có lỗ hổng đã biết trong dependency production.'},
    'c_migrate': {'en': 'Migration: {items}.', 'vi': 'Chuyển đổi: {items}.'},
    'c_runtime': {'en': 'Configuration: {n} place(s) declare Node.js {c} and must change to {t}.',
                  'vi': 'Cấu hình: {n} chỗ khai báo Node.js {c} cần đổi sang {t}.'},
    'n_projects': {'en': '{n} project(s)', 'vi': '{n} dự án'},
}
KINDS = {
    'runtime_declarations': {'en': 'Change the Node.js version declarations (IaC, CI, Docker)',
                             'vi': 'Đổi khai báo phiên bản Node.js (IaC, CI, Docker)'},
    'engines_field': {'en': 'Update engines.node of package.json', 'vi': 'Cập nhật engines.node trong package.json'},
    'vuln_minor_upgrades': {'en': 'Upgrade vulnerable packages (same major)', 'vi': 'Nâng package có lỗ hổng (cùng major)'},
    'vuln_major_upgrades': {'en': 'Upgrade vulnerable packages to a new major (API may change)',
                            'vi': 'Nâng package có lỗ hổng lên major mới (có thể đổi API)'},
    'vuln_no_fix': {'en': 'Vulnerable packages with no fixed version: replace or accept the risk',
                    'vi': 'Package có lỗ hổng chưa có bản sửa: thay thế hoặc chấp nhận rủi ro'},
    'vuln_dev_only': {'en': 'Vulnerabilities in devDependencies only', 'vi': 'Lỗ hổng chỉ ở devDependencies'},
    'engines_violations': {'en': 'Dependencies that do not support the target (engines)',
                           'vi': 'Dependency không hỗ trợ Node đích (engines)'},
    'migrate_package': {'en': 'Migrate away from {package}', 'vi': 'Chuyển đổi khỏi {package}'},
    'code_errors': {'en': 'Fix code hit by breaking changes (error)', 'vi': 'Sửa mã vi phạm breaking change (mức error)'},
    'code_warnings': {'en': 'Review code with breaking-change warnings', 'vi': 'Rà soát mã có cảnh báo breaking change'},
    'native_addons': {'en': 'Rebuild and load native addons on the target', 'vi': 'Build lại và nạp thử native addon trên đích'},
    'regression_test': {'en': 'Regression tests on the target Node.js (staging)', 'vi': 'Kiểm thử hồi quy trên Node đích (staging)'},
}
DECL_KINDS = {'lambda_runtime': 'Lambda Runtime', 'cdk_runtime': 'CDK Runtime', 'container_image': 'Container image',
              'ci_node_version': 'CI node-version', 'tool_versions': '.tool-versions', 'version_file': '.nvmrc / .node-version'}
NOTES = {
    'current_unknown': {'vi': 'Không xác định được nhánh Node.js hiện tại: thêm --current N.'},
    'addons_not_loaded': {'vi': 'Chưa nạp thử native addon: thêm --node-bin trỏ tới Node.js {target}.'},
    'no_lockfile': {'vi': 'Không có package-lock.json: chưa kiểm lỗ hổng và engines của dependency.'},
    'yarn_pnpm': {'vi': 'Chỉ có yarn.lock/pnpm-lock.yaml: kiểm engines và advisory bằng yarn/pnpm.'},
}
SEV_ORDER = ('critical', 'high', 'medium', 'low', 'unknown')


def t(key, lang, **kw):
    s = T[key].get(lang) or T[key]['en']
    for k, v in kw.items():
        s = s.replace('{%s}' % k, str(v))
    return s


def kind_label(w, lang):
    s = KINDS[w['kind']].get(lang) or KINDS[w['kind']]['en']
    return s.replace('{package}', w.get('package') or '')


def note_text(n, lang):
    tr = (NOTES.get(n.get('key')) or {}).get(lang)
    if not tr:
        return n['text']
    for k, v in (n.get('args') or {}).items():
        tr = tr.replace('{%s}' % k, str(v))
    return tr


def overall(res):
    st = [p['verdict']['status'] for p in res['projects']]
    return 'FAIL' if 'FAIL' in st else ('PENDING' if 'PENDING' in st or not st else 'PASS')


def conclusions(res, lang):
    """Plain-language conclusions for the top of the report."""
    tgt, out = res['target_branch'], []
    st = overall(res)
    if st == 'PASS':
        out.append(t('c_pass', lang, t=tgt))
    elif st == 'FAIL':
        n = sum(p['verdict']['errors'] + p['verdict']['blockers'] for p in res['projects'])
        out.append(t('c_fail', lang, t=tgt, n=n))
    else:
        parts = sorted({x for p in res['projects'] for x in p['verdict']['pending_parts']})
        out.append(t('c_pending', lang, t=tgt, parts=', '.join(parts) or '-'))
    prod = [v for p in res['projects'] for v in p['vulnerabilities'] or [] if not v['dev']]
    if prod:
        sev = {}
        for v in prod:
            sev[v['severity']] = sev.get(v['severity'], 0) + 1
        out.append(t('c_vuln', lang, n=len(prod), sev=', '.join('%s %d' % (k, sev[k]) for k in SEV_ORDER if sev.get(k)),
                     fix=sum(1 for v in prod if v['fix_version']),
                     major=sum(1 for v in prod if v['fix_version'] and v['major_bump']),
                     nofix=sum(1 for v in prod if not v['fix_version'])))
    elif any(p['vulnerabilities'] is not None for p in res['projects']):
        out.append(t('c_novuln', lang))
    mig = {}
    for p in res['projects']:
        for d in p['deprecated']:
            mig[d['package']] = mig.get(d['package'], 0) + 1
    if mig:
        out.append(t('c_migrate', lang, items=', '.join('%s (%s)' % (k, t('n_projects', lang, n=n))
                                                        for k, n in sorted(mig.items()))))
    n = res['summary']['runtime_changes']
    if n:
        out.append(t('c_runtime', lang, n=n, c=res.get('current_branch') or '?', t=tgt))
    return out


def project_path(p, res):
    for root in res['paths']:
        if p['path'] == root or p['path'].startswith(root.rstrip('/') + '/'):
            rel = os.path.relpath(p['path'], root)
            return os.path.join(os.path.basename(root), rel) if rel != '.' else os.path.basename(root)
    return p['path']


def suggestion(d, target):
    txt = d['text']
    if d['kind'] == 'lambda_runtime':
        return txt.replace('nodejs%s.x' % d['branch'], 'nodejs%s.x' % target)
    if d['kind'] == 'cdk_runtime':
        return txt.replace('NODEJS_%s_X' % d['branch'], 'NODEJS_%s_X' % target)
    if d['kind'] == 'version_file':
        return target
    return txt.replace(d['branch'], target, 1)


def lifecycle_lines(res, lang):
    lc = res.get('lifecycle')
    if not lc:
        return [('warn', t('no_lifecycle', lang))]
    out = []
    cur, tgt, rec = lc.get('current'), lc['target'], lc.get('recommended')
    if cur and cur['status'] == 'EOL' and cur.get('eol_date'):
        out.append(('bad', t('current_eol', lang, c=cur['branch'], e=cur['eol_date'])))
    if tgt['status'] in ('EOL', 'UNKNOWN', 'PRE_RELEASE', 'CURRENT', 'ACTIVE') or not tgt.get('lts'):
        out.append(('bad', t('target_closed', lang, t=tgt['branch'], s=tgt['status'], r=rec or '-')))
    elif not lc['target_ok']:
        out.append(('warn', t('target_short', lang, t=tgt['branch'], d=tgt['days_to_eol'],
                              m=_days(lc['today'], lc['min_eol']), r=rec or '-')))
    else:
        out.append(('ok', t('target_good', lang, t=tgt['branch'], e=tgt['eol_date'])))
    return out


def _days(a, b):
    from ..feeds import risk as R
    return R.day_number(b) - R.day_number(a)


def aggregate_work(res):
    """{(kind, package): {project: count}, size: worst}."""
    rows, order = {}, []
    rank = {'S': 0, 'M': 1, 'L': 2}
    for p in res['projects']:
        for w in p['work_items']:
            key = (w['kind'], w.get('package'))
            if key not in rows:
                rows[key] = {'w': w, 'per': {}, 'size': w['size']}
                order.append(key)
            rows[key]['per'][p['name']] = w['count']
            if rank[w['size']] > rank[rows[key]['size']]:
                rows[key]['size'] = w['size']
    shared = [d for d in res.get('shared_declarations') or [] if d['to_change']]
    if shared:
        key = ('runtime_declarations', None)
        if key not in rows:
            rows[key] = {'w': {'kind': 'runtime_declarations'}, 'per': {}, 'size': 'S'}
            order.insert(0, key)
        rows[key]['per']['*'] = len(shared)
    return [rows[k] for k in order]


# --- HTML -----------------------------------------------------------------------------
CSS = """
:root{--fg:#1f2328;--muted:#59636e;--bg:#fff;--line:#d1d9e0;--soft:#f6f8fa;--ok:#1a7f37;--warn:#9a6700;--bad:#cf222e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,"Segoe UI",
Roboto,"Helvetica Neue",Arial,sans-serif}main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 8px;padding-bottom:4px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:20px 0 6px}.meta{color:var(--muted);font-size:13px}.meta code{font-size:12px}
table{border-collapse:collapse;width:100%;margin:6px 0 12px;font-size:13px}th,td{border:1px solid var(--line);
padding:5px 8px;text-align:left;vertical-align:top}th{background:var(--soft);font-weight:600}td.n{text-align:right}
code{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--soft);padding:1px 4px;
border-radius:4px;word-break:break-all}.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-weight:600;
font-size:12px;color:#fff}.PASS,.ok{background:var(--ok)}.FAIL,.bad{background:var(--bad)}.PENDING,.warn{background:var(--warn)}
.cards{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}.card{border:1px solid var(--line);border-radius:6px;
padding:10px 14px;min-width:150px;flex:1}.card b{display:block;font-size:22px}.card span{color:var(--muted);font-size:12px}
.msg{padding:8px 12px;border-radius:6px;margin:6px 0;border-left:4px solid}.msg.ok{background:#dafbe1;border-color:var(--ok);
color:var(--fg)}.msg.warn{background:#fff8c5;border-color:var(--warn);color:var(--fg)}.msg.bad{background:#ffebe9;
border-color:var(--bad);color:var(--fg)}.sev-critical,.sev-high{color:var(--bad);font-weight:600}.sev-medium{color:var(--warn)}
ul{margin:4px 0 8px;padding-left:20px}.wrap{overflow-x:auto}
@media print{main{max-width:none}h2{break-after:avoid}table{break-inside:auto}}
"""


def e(v):
    return html.escape('' if v is None else str(v), quote=True)


def _table(head, rows, nums=()):
    out = ['<div class="wrap"><table><thead><tr>%s</tr></thead><tbody>' % ''.join('<th>%s</th>' % e(h) for h in head)]
    for r in rows:
        out.append('<tr>%s</tr>' % ''.join('<td%s>%s</td>' % (' class="n"' if i in nums else '', c)
                                            for i, c in enumerate(r)))
    out.append('</tbody></table></div>')
    return ''.join(out)


def _badge(status, lang):
    return '<span class="badge %s">%s</span>' % (e(status), e(t(status, lang)))


def _sev(s):
    return '<span class="sev-%s">%s</span>' % (e(s), e(s))


def render_html(res, lang='en'):
    L = lambda k, **kw: t(k, lang, **kw)   # noqa: E731
    cur, tgt = res.get('current_branch') or '?', res['target_branch']
    st = overall(res)
    s = res['summary']
    sev = {}
    for p in res['projects']:
        for k, v in p['verdict']['by_severity'].items():
            sev[k] = sev.get(k, 0) + v
    o = ['<!doctype html><html lang="%s"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>%s %s → %s</title><style>%s</style></head><body><main>' % (e(lang), e(L('title')), e(cur), e(tgt), CSS)]
    o.append('<h1>%s: %s → %s</h1>' % (e(L('title')), e(cur), e(tgt)))
    lc = res.get('lifecycle') or {}
    o.append('<p class="meta">%s %s · %s php-quickpatch %s · catalog <code>%s</code> · bundle <code>%s</code><br>'
             '%s: %s</p>' % (e(L('generated')), e(res['generated_at']), e(L('tool')), e(VERSION),
                             e(res['catalog_version']), e(lc.get('bundle_id') or '-'), e(L('paths')),
                             ', '.join('<code>%s</code>' % e(p) for p in res['paths'])))
    # summary
    o.append('<h2>%s</h2>' % e(L('summary')))
    o.append('<p>%s: %s</p><ul>%s</ul><p class="meta">%s</p>' % (
        e(L('overall')), _badge(st, lang), ''.join('<li>%s</li>' % e(c) for c in conclusions(res, lang)),
        e(L('verdict_note'))))
    cards = [(s['projects'], L('projects')), (s['vulnerable_packages'], L('vulnerable')),
             (s['runtime_changes'], L('runtime_changes')), (s['deprecated'], L('deprecated_n')),
             (s['errors'], L('code_errors'))]
    o.append('<div class="cards">%s</div>' % ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (e(n), e(lbl))
                                                     for n, lbl in cards))
    if sev:
        o.append('<p>%s: %s</p>' % (e(L('vulnerable')), ', '.join(
            '%s %s' % (_sev(k), e(sev[k])) for k in SEV_ORDER if sev.get(k))))
    for cls, msg in lifecycle_lines(res, lang):
        o.append('<div class="msg %s">%s</div>' % (cls, e(msg)))
    # lifecycle table
    if lc:
        rows = []
        for lbl, b in ((L('current'), lc.get('current')), (L('target'), lc.get('target'))):
            if b:
                rows.append([e(lbl), e(b['branch']), e(b['status']), e(b.get('eol_date') or '-'),
                             e(b.get('days_to_eol') if b.get('days_to_eol') is not None else '-'), e(b.get('latest') or '-')])
        if lc.get('recommended'):
            rows.append([e(L('recommended')), e(lc['recommended']), '', '', '', ''])
        o.append('<h3>%s</h3>' % e(L('lifecycle')))
        o.append(_table(['', L('branch'), L('status'), L('eol'), L('days_left'), L('latest')], rows, nums=(4,)))
    # work
    o.append('<h2>%s</h2>' % e(L('work')))
    names = [p['name'] for p in res['projects']]
    agg = aggregate_work(res)
    star = any('*' in a['per'] for a in agg)
    head = [L('item')] + names + ([L('shared_col')] if star else []) + [L('size')]
    rows = []
    for a in agg:
        row = [e(kind_label(a['w'], lang))] + [e(a['per'].get(n, '')) for n in names]
        if star:
            row.append(e(a['per'].get('*', '')))
        row.append(e(a['size']))
        rows.append(row)
    o.append(_table(head, rows, nums=tuple(range(1, len(head) - 1))))
    o.append('<p class="meta">%s</p>' % e(L('work_note')))
    # projects
    for p in res['projects']:
        o.append(project_html(p, res, lang))
    shared = res.get('shared_declarations') or []
    if shared:
        o.append('<h2>%s</h2>' % e(L('shared')))
        o.append(_decl_table(shared, tgt, lang))
    o.append('<h2>%s</h2><ul>%s</ul>' % (e(L('method')), ''.join('<li>%s</li>' % e(x) for x in T['method_text'][lang])))
    o.append('<h3>%s</h3><ul>%s</ul>' % (e(L('limits')), ''.join('<li>%s</li>' % e(x) for x in T['limits_text'][lang])))
    o.append('</main></body></html>\n')
    return ''.join(o)


def _decl_table(decls, target, lang):
    rows = []
    for d in decls:
        rows.append(['<code>%s</code>' % e(d['file']), e(d['line']), e(DECL_KINDS.get(d['kind'], d['kind'])),
                     '<code>%s</code>' % e(d['text']),
                     '<code>%s</code>' % e(suggestion(d, target)) if d['to_change'] else e(t('unchanged', lang))])
    return _table([t('file', lang), t('line', lang), t('kind', lang), 'Node.js', t('change_to', lang)], rows, nums=(1,))


def project_html(p, res, lang):
    L = lambda k, **kw: t(k, lang, **kw)   # noqa: E731
    v = p['verdict']
    tgt = res['target_branch']
    o = ['<h2>%s: %s %s</h2>' % (e(L('project')), e(p['name']), _badge(v['status'], lang))]
    src = {'option': L('option'), 'declarations': L('declarations'), 'repository': L('repository'),
           'engines': L('engines_src')}.get(p['current_source'], L('unknown'))
    o.append('<p class="meta"><code>%s</code> · %s: %s (%s) · %s: %s · %s: %s</p>' % (
        e(project_path(p, res)), e(L('current_from')), e(p['current_branch'] or '?'), e(src), e(L('files')),
        e(p.get('files_scanned', 0)), e(L('locked')), e(p['packages'])))
    if p['declarations']:
        o.append('<h3>%s</h3>' % e(L('decls')))
        o.append(_decl_table(p['declarations'], tgt, lang))
    o.append('<h3>%s</h3>' % e(L('vulns')))
    if p['vulnerabilities'] is None:
        o.append('<p>%s</p>' % e(L('vulns_skipped')))
    elif not p['vulnerabilities']:
        o.append('<p>%s</p>' % e(L('no_vulns')))
    else:
        rows = []
        for f in p['vulnerabilities']:
            flags = []
            if f.get('is_malware'):
                flags.append(L('malware'))
            if f.get('in_kev'):
                flags.append(L('kev'))
            if f['dev']:
                flags.append(L('dev'))
            if f.get('major_bump'):
                flags.append(L('major'))
            ids = f['advisories']
            adv = ', '.join(e(i) for i in ids[:4]) + (' … (+%d)' % (len(ids) - 4) if len(ids) > 4 else '')
            fix = '<code>%s</code>' % e(f['fix_version']) if f['fix_version'] else e(L('no_fix'))
            if f['fix_version'] and f.get('unfixed_advisories'):
                fix += ' · %s: %s' % (e(L('no_fix')), e(', '.join(f['unfixed_advisories'])))
            rows.append(['<code>%s</code>' % e(f['package']), e(f['version']), _sev(f['severity']), adv, fix,
                         e(', '.join(flags))])
        o.append(_table([L('package'), L('version'), L('severity'), L('advisories'), L('fix'), ''], rows))
    if p['deprecated']:
        o.append('<h3>%s</h3>' % e(L('deprecated')))
        rows = []
        for d in p['deprecated']:
            sites = ', '.join('<code>%s:%s</code>' % (e(c['file']), e(c['line'])) for c in d['call_sites'][:20])
            if len(d['call_sites']) > 20:
                sites += ' … (+%d)' % (len(d['call_sites']) - 20)
            rows.append(['<code>%s</code> %s' % (e(d['package']), e(d['version'] or '')), e(d['message']),
                         e(d.get('replacement') or '-'), sites or '-'])
        o.append(_table([L('package'), L('reason'), L('replacement'), L('call_sites')], rows))
    if p['npm_engine_violations']:
        o.append('<h3>%s</h3>' % e(L('engines')))
        rows = [['<code>%s</code>' % e(x['package']), e(x.get('version')), '<code>%s</code>' % e(x['engines']),
                 e(L('dev') if x.get('dev') else '')] for x in p['npm_engine_violations']]
        o.append(_table([L('package'), L('version'), L('engines_c'), ''], rows))
    o.append('<h3>%s</h3>' % e(L('hits')))
    if p['hits']:
        rows = [['<code>%s:%s</code>' % (e(h['file']), e(h['line'])), e(h['rule_id']), e(h['level']),
                 '<code>%s</code>' % e(h['snippet'])] for h in p['hits']]
        o.append(_table([L('file'), L('rule'), L('level'), L('code')], rows))
    else:
        o.append('<p>%s</p>' % e(L('no_hits')))
    if p.get('rules'):
        o.append('<details><summary>%s (%s, %s]</summary><ul>%s</ul></details>' % (
            e(L('rules')), e(p['current_branch']), e(tgt), ''.join(
                '<li><b>%s</b> (%s): %s</li>' % (e(r['rule_id']), e(r['level']), e(r['change'])) for r in p['rules'])))
    if p['native_addons']:
        o.append('<h3>%s</h3><ul>%s</ul>' % (e(L('addons')), ''.join('<li><code>%s</code>: %s</li>' % (
            e(a['package']), e(L('load_ok') if a['load_ok'] else (L('load_unknown') if a['load_ok'] is None
                                                                   else L('load_fail'))))
            for a in p['native_addons'])))
    if p['notes'] or p['errors']:
        o.append('<h3>%s</h3><ul>%s%s</ul>' % (e(L('notes')), ''.join(
            '<li><code>%s</code> %s</li>' % (e(x['code']), e(x['message'])) for x in p['errors']),
            ''.join('<li>%s</li>' % e(note_text(n, lang)) for n in p['notes'])))
    return ''.join(o)


# --- Markdown ------------------------------------------------------------------------------
def md(v):
    s = '' if v is None else str(v)
    return s.replace('\\', '\\\\').replace('|', '\\|').replace('\n', ' ').replace('<', '&lt;').replace('>', '&gt;')


def _md_table(head, rows):
    out = ['| %s |' % ' | '.join(md(h) for h in head), '|%s|' % '|'.join(' --- ' for _ in head)]
    out += ['| %s |' % ' | '.join(r) for r in rows]
    return '\n'.join(out) + '\n'


def render_md(res, lang='en'):
    L = lambda k, **kw: t(k, lang, **kw)   # noqa: E731
    cur, tgt = res.get('current_branch') or '?', res['target_branch']
    s, lc = res['summary'], res.get('lifecycle') or {}
    o = ['# %s: %s → %s\n' % (L('title'), cur, tgt),
         '%s %s · php-quickpatch %s · catalog `%s` · bundle `%s`  ' % (L('generated'), res['generated_at'], VERSION,
                                                                     res['catalog_version'], lc.get('bundle_id') or '-'),
         '%s: %s\n' % (L('paths'), ', '.join('`%s`' % md(p) for p in res['paths'])),
         '## %s\n' % L('summary'),
         '%s: **%s**\n' % (L('overall'), t(overall(res), lang))]
    o.extend('- %s' % md(c) for c in conclusions(res, lang))
    o.append('\n_%s_\n' % md(L('verdict_note')))
    o.append(_md_table(['', ''], [[md(lbl), md(n)] for n, lbl in (
        (s['projects'], L('projects')), (s['vulnerable_packages'], L('vulnerable')),
        (s['runtime_changes'], L('runtime_changes')), (s['deprecated'], L('deprecated_n')),
        (s['errors'], L('code_errors')))]))
    for cls, msg in lifecycle_lines(res, lang):
        o.append('> %s%s\n' % ('**!** ' if cls != 'ok' else '', md(msg)))
    if lc:
        rows = []
        for lbl, b in ((L('current'), lc.get('current')), (L('target'), lc.get('target'))):
            if b:
                rows.append([md(lbl), md(b['branch']), md(b['status']), md(b.get('eol_date') or '-'),
                             md(b.get('days_to_eol')), md(b.get('latest') or '-')])
        if lc.get('recommended'):
            rows.append([md(L('recommended')), md(lc['recommended']), '', '', '', ''])
        o.append('### %s\n' % L('lifecycle'))
        o.append(_md_table(['', L('branch'), L('status'), L('eol'), L('days_left'), L('latest')], rows))
    o.append('## %s\n' % L('work'))
    names = [p['name'] for p in res['projects']]
    agg = aggregate_work(res)
    star = any('*' in a['per'] for a in agg)
    rows = []
    for a in agg:
        rows.append([md(kind_label(a['w'], lang))] + [md(a['per'].get(n, '')) for n in names]
                    + ([md(a['per'].get('*', ''))] if star else []) + [a['size']])
    o.append(_md_table([L('item')] + names + ([L('shared_col')] if star else []) + [L('size')], rows))
    o.append('_%s_\n' % md(L('work_note')))
    for p in res['projects']:
        v = p['verdict']
        o.append('## %s: %s — %s\n' % (L('project'), md(p['name']), t(v['status'], lang)))
        o.append('`%s` · %s: %s · %s: %s\n' % (md(project_path(p, res)), L('current_from'), md(p['current_branch'] or '?'),
                                              L('locked'), p['packages']))
        if p['declarations']:
            o.append('### %s\n' % L('decls'))
            o.append(_md_table([L('file'), L('line'), L('kind'), 'Node.js', L('change_to')], [
                ['`%s`' % md(d['file']), md(d['line']), md(DECL_KINDS.get(d['kind'], d['kind'])), '`%s`' % md(d['text']),
                 '`%s`' % md(suggestion(d, tgt)) if d['to_change'] else md(L('unchanged'))] for d in p['declarations']]))
        o.append('### %s\n' % L('vulns'))
        if p['vulnerabilities'] is None:
            o.append(L('vulns_skipped') + '\n')
        elif not p['vulnerabilities']:
            o.append(L('no_vulns') + '\n')
        else:
            rows = []
            for f in p['vulnerabilities']:
                flags = [x for x, on in ((L('malware'), f.get('is_malware')), (L('kev'), f.get('in_kev')),
                                         (L('dev'), f['dev']), (L('major'), f.get('major_bump'))) if on]
                rows.append(['`%s`' % md(f['package']), md(f['version']), md(f['severity']),
                             md(', '.join(f['advisories'][:4]) + (' …' if len(f['advisories']) > 4 else '')),
                             '`%s`' % md(f['fix_version']) if f['fix_version'] else md(L('no_fix')), md(', '.join(flags))])
            o.append(_md_table([L('package'), L('version'), L('severity'), L('advisories'), L('fix'), ''], rows))
        if p['deprecated']:
            o.append('### %s\n' % L('deprecated'))
            o.append(_md_table([L('package'), L('reason'), L('replacement'), L('call_sites')], [
                ['`%s` %s' % (md(d['package']), md(d['version'] or '')), md(d['message']), md(d.get('replacement') or '-'),
                 md(', '.join('%s:%s' % (c['file'], c['line']) for c in d['call_sites'][:20]) or '-')]
                for d in p['deprecated']]))
        if p['npm_engine_violations']:
            o.append('### %s\n' % L('engines'))
            o.append(_md_table([L('package'), L('version'), L('engines_c'), ''], [
                ['`%s`' % md(x['package']), md(x.get('version')), '`%s`' % md(x['engines']),
                 md(L('dev') if x.get('dev') else '')] for x in p['npm_engine_violations']]))
        o.append('### %s\n' % L('hits'))
        if p['hits']:
            o.append(_md_table([L('file'), L('rule'), L('level'), L('code')], [
                ['`%s:%s`' % (md(h['file']), h['line']), md(h['rule_id']), md(h['level']), '`%s`' % md(h['snippet'])]
                for h in p['hits']]))
        else:
            o.append(L('no_hits') + '\n')
        if p['native_addons']:
            o.append('### %s\n' % L('addons'))
            o.extend('- `%s`: %s' % (md(a['package']), L('load_ok') if a['load_ok'] else (
                L('load_unknown') if a['load_ok'] is None else L('load_fail'))) for a in p['native_addons'])
            o.append('')
        if p['notes'] or p['errors']:
            o.append('### %s\n' % L('notes'))
            o.extend('- `%s` %s' % (x['code'], md(x['message'])) for x in p['errors'])
            o.extend('- %s' % md(note_text(n, lang)) for n in p['notes'])
            o.append('')
    shared = res.get('shared_declarations') or []
    if shared:
        o.append('## %s\n' % L('shared'))
        o.append(_md_table([L('file'), L('line'), L('kind'), 'Node.js', L('change_to')], [
            ['`%s`' % md(d['file']), md(d['line']), md(DECL_KINDS.get(d['kind'], d['kind'])), '`%s`' % md(d['text']),
             '`%s`' % md(suggestion(d, tgt)) if d['to_change'] else md(L('unchanged'))] for d in shared]))
    o.append('## %s\n' % L('method'))
    o.extend('- %s' % x for x in T['method_text'][lang])
    o.append('\n### %s\n' % L('limits'))
    o.extend('- %s' % x for x in T['limits_text'][lang])
    return '\n'.join(o) + '\n'


def write(res, path, lang):
    """Write the report (format from the extension) with a temp file + rename; never through a symlink."""
    ext = os.path.splitext(path)[1].lower()
    text = render_html(res, lang) if ext in ('.html', '.htm') else render_md(res, lang)
    d = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(d, '.%s.tmp-%d' % (os.path.basename(path), os.getpid()))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)
    return path
