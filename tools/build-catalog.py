#!/usr/bin/env python3
"""Build share/php-quickpatch/catalog/ (FR-SCN-CAT-001) from the scenario docs.

Sources (docs/php-quickpatch/srs/):
  version-scenarios-php.md     §2 summary, §5 BC-PHP, §6 framework matrix,
                               §7.1 loaders, §10 SCN-PHP-001..007
  version-scenarios-php-8x.md  §3..§11 SCN-PHP-008..016
  version-scenarios-node.md    §2 summary, §5 BC-NODE, §6.1 ABI, §10 SCN-NODE-001..012
  environment-playbooks.md     §2.3 detection, §3 playbook catalog

Output: scenarios.json, checklists.json, playbooks.json, bc_rules.json,
mitigations.json, framework_php.tsv, catalog.json (catalog_version) and
SHA256SUMS. scenarios.json and mitigations.json hold one record per line so
php-quickpatch.sh reads them without Python (C-01).

Usage: tools/build-catalog.py [--version YYYY.MM.DD-N] [--out DIR]
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRS = os.path.join(ROOT, 'docs/php-quickpatch/srs')
OUT = os.path.join(ROOT, 'share/php-quickpatch/catalog')
DATA_AS_OF = '2026-10-22'
CATALOG_VERSION = '2026.10.26-1'
FILES = ['scenarios.json', 'checklists.json', 'playbooks.json', 'bc_rules.json', 'mitigations.json',
         'framework_php.tsv', 'catalog.json']

EXEC = {'Tự động': 'AUTO', 'Bán tự động (duyệt)': 'SEMI', 'Thủ công': 'MANUAL'}


def read(name):
    with open(os.path.join(SRS, name), encoding='utf-8') as f:
        return f.read().split('\n')


def split_row(line):
    cells = re.split(r'(?<!\\)\|', line.strip().strip('|'))
    return [c.strip().replace('\\|', '|') for c in cells]


def unquote(cell):
    return cell.strip().strip('`').strip()


def clean(text):
    return re.sub(r'\s+', ' ', text.replace('<br>', '; ')).strip()


def table_after(lines, start, first_cell=None):
    """Rows (list of cells) of the first table at or after line START."""
    i = start
    while i < len(lines) and not lines[i].startswith('|'):
        i += 1
    rows = []
    header = split_row(lines[i]) if i < len(lines) else []
    i += 2
    while i < len(lines) and lines[i].startswith('|'):
        rows.append(split_row(lines[i]))
        i += 1
    return header, rows, i


# --- scenarios and checklists ----------------------------------------------
SUMMARY_COLS = {'php': {'range': 2, 'count': 8}, 'node': {'range': 2, 'count': 9}}

# Classifier of the scenarios whose version_match is a rule, not a regex
# (BR-SCN-040 steps (1)(2), BR-SCN-020, overlays by install source).
RULES = {
    'SCN-PHP-005': 'abnormal', 'SCN-PHP-014': 'prerelease_branch',
    'SCN-PHP-015': 'owned_package', 'SCN-PHP-016': 'no_package_not_panel',
    'SCN-NODE-008': 'prerelease_or_abnormal', 'SCN-NODE-009': 'nvm', 'SCN-NODE-010': 'tarball',
    'SCN-NODE-011': 'nodesource', 'SCN-NODE-012': 'distro_package',
}


def summary(lines, runtime):
    out = {}
    for line in lines:
        if not line.startswith('| `SCN-'):
            continue
        c = split_row(line)
        sid = unquote(c[0])
        cols = SUMMARY_COLS[runtime]
        out[sid] = {'kind': c[1], 'range': clean(c[cols['range']]), 'count': int(c[cols['count']]),
                    'status_snapshot': clean(c[3]).replace('`', ''), 'target_note': clean(c[-4 if runtime == 'php' else -4])}
    return out


def parse_attr(attrs, sid):
    """version_match / match_order from the attribute table."""
    for k, v in attrs.items():
        if 'match_order' in k or k.startswith('Loại / điều kiện'):
            m = re.search(r'/\s*(?:`match_order`\s*)?(\d+)\s*$', v)
            order = int(m.group(1)) if m else None
            if sid in RULES:
                return RULES[sid], order, clean(v)
            rx = re.match(r'`([^`]+)`\s*/\s*\d+\s*$', v)
            if rx:
                return rx.group(1).replace('|', '|'), order, None
            return 'rule', order, clean(v)
    return None, None, None


CHK_ID = re.compile(r'^CHK-(PHP|NODE)-\d{3}-\d{2}$')
REF_FULL = re.compile(r'`(CHK-(?:PHP|NODE)-\d{3}-\d{2})`')


def refs_of(text):
    """Template items named by 'Như `CHK-..-13` … `-17`', '`-10`, `-11`' (ranges expanded)."""
    out, base = [], None
    tokens = re.findall(r'`(CHK-(?:PHP|NODE)-\d{3}-\d{2}|-\d{2})`|(…)', text)
    pending_range = False
    for tok, ell in tokens:
        if ell:
            pending_range = True
            continue
        if tok.startswith('CHK-'):
            cur = tok
            base = tok[:-3]
        elif base:
            cur = base + tok
        else:
            continue
        if pending_range and out:
            a, b = int(out[-1][-2:]), int(cur[-2:])
            for n in range(a + 1, b):
                out.append('%s-%02d' % (cur[:-3], n))
        pending_range = False
        out.append(cur)
    seen, res = set(), []
    for r in out:
        if r not in seen:
            seen.add(r)
            res.append(r)
    return res


CONDITIONS = [
    (r'\(khi `framework` ≠ none\)', 'framework!=none'),
    (r'\(khi `framework` ∉ \{none, wordpress\}\)', 'framework!=none;framework!=wordpress'),
    (r'\(khi `framework=wordpress`\)', 'framework=wordpress'),
    (r'\(khi `loader` ≠ none\)', 'loader!=none'),
    (r'\(khi `composer=true`\)', 'composer=true'),
    (r'\(khi (?:SAPI = )?`mod_php`\)', 'sapi=mod_php'),
    (r'\(khi (?:nâng nhánh|nâng major|nâng|khác nhánh|chuyển/nâng)\)', 'mode=cross_branch'),
    (r'\(khi `\$OLD` = 5\.3\)', 'old_branch=5.3'),
    (r'\(khi overlay (SCN-[A-Z]+-\d{3})\)', 'overlay=\\1'),
    (r'\(khi có `phpunit\.xml\*`\)', 'phpunit=true'),
]


def applies_when(action):
    conds, manual = [], None
    for rx, expr in CONDITIONS:
        m = re.search(rx, action)
        if m:
            conds.append(m.expand(expr))
    if not conds:
        m = re.search(r'\((khi [^)]*)\)', action)
        if m:
            manual = m.group(1)          # judged by the operator (MANUAL condition)
    return ';'.join(conds) or None, manual


VAR_UNVERIFIED = re.compile(r'chưa kiểm chứng|Chưa kiểm chứng|chưa chạy thử', re.I)


def checklist_rows(header, rows, sid, runtime):
    items = []
    for c in rows:
        if len(c) < 7:
            continue
        chk = unquote(c[0])
        if not CHK_ID.match(chk):
            raise SystemExit('bad chk_id %r in %s' % (chk, sid))
        if chk[:-3].replace('CHK-', 'SCN-') != sid:
            raise SystemExit('%s outside %s' % (chk, sid))
        action = clean(c[2])
        exec_type = EXEC.get(c[3].strip())
        if not exec_type:
            raise SystemExit('unknown exec type %r in %s' % (c[3], chk))
        cond, manual_cond = applies_when(action)
        mech = clean(c[4])
        upgrade = bool(cond and 'mode=cross_branch' in cond)
        item = {
            'chk_id': chk, 'scenario_id': sid, 'runtime': runtime, 'phase': c[1].strip(), 'action': action,
            'exec_type': exec_type, 'check_mechanism': mech, 'done_criteria': clean(c[5]), 'risk': clean(c[6]) or None,
            'applies_when': cond, 'manual_condition': manual_cond,
            'optional': bool(re.match(r'\((?:Tuỳ|tuỳ) chọn\)', action)),
            'refs': refs_of(mech), 'expand': upgrade and bool(refs_of(mech)) and re.search(r'^Như ', mech) is not None,
            'depends_on': [], 'verified': not VAR_UNVERIFIED.search(mech + ' ' + action),
            'cli_action': cli_action(runtime, action, exec_type, c[1].strip()),
        }
        if not re.match(r'^P[1-7]$', item['phase']):
            raise SystemExit('bad phase %r in %s' % (item['phase'], chk))
        items.append(item)
    return items


# P1 checks answered by `scan --json` (runtime, package, OS, patch state, site map).
SCAN_FACTS = ('xác minh phiên bản', 'xác nhận sau vá', 'xác định trạng thái vá', 'ánh xạ site', 'kiểm kê extension',
              'xác định gói', 'xác định os', 'ghi nhận os', 'đối chiếu cve', 'đối chiếu tracker', 'kiểm tra kênh',
              'tính trạng thái', 'ghi chuỗi phiên bản', 'định danh file', 'kiểm tra gói sở hữu', 'đối chiếu banner',
              'liệt kê site', 'kiểm kê ứng dụng và')
ASSESS_FACTS = ('đánh giá bảo mật so sánh', 'hiển thị cảnh báo eol')
# Steps of the same-branch patch flow (BR-SCN-008); the rest only applies when the branch changes.
PATCH_FLOW = ('vá cùng', 'vá trong kho', 'mitigation', 'restart', 'xác nhận sau vá', 'health check sau vá',
              'chụp baseline health check trước khi vá', 'rà dependency')


MIGRATE_INSTALL = 'migrate install --runtime %s --target $NEW --plan $PLAN_ID'
MIGRATE_SWITCH = 'migrate switch $SITE --target $NEW --plan $PLAN_ID'


def cli_action(runtime, action, exec_type, phase=None):
    """Whitelisted CLI action of an item the tool runs itself (FR-PLAN-CHK-002); None = guided."""
    a = action.lower()
    if phase == 'P2' and exec_type == 'SEMI' and 'nvm' not in a and \
            (('song song' in a and not a.startswith(('cài công cụ phụ trợ', 'cài pm2'))) or 'cài prefix mới' in a):
        return MIGRATE_INSTALL % runtime            # FR-UPG-INST-001 (side-by-side install, PB-001 / PB-015)
    if phase == 'P5' and exec_type == 'SEMI' and 'chuyển' in a and not any(x in a for x in ('npm ci', 'máy mới', 'prefix mới')) and \
            ('canary' in a or 'từng site' in a or 'từng ứng dụng' in a):
        return MIGRATE_SWITCH                       # FR-UPG-SWT-001 / FR-UPG-SEQ-001
    if exec_type == 'AUTO' and a.startswith(('vá cùng nhánh', 'vá cùng major', 'vá cùng dòng', 'vá trong kho')):
        return 'fix --only %s' % runtime
    if exec_type == 'AUTO' and a.startswith('mitigation'):
        return 'fix --only php'
    if exec_type == 'AUTO' and a.startswith('restart'):
        return 'fix --only %s' % runtime
    if exec_type == 'AUTO' and a.startswith(ASSESS_FACTS):
        return 'assess --runtime-id $RUNTIME_ID --candidates'
    if exec_type == 'AUTO' and a.startswith(SCAN_FACTS):
        return 'scan --only %s,sites' % runtime
    parts = compat_parts(a) if exec_type == 'AUTO' else None
    if parts:
        return 'compat --site $SITE --parts %s' % ','.join(parts)
    if exec_type == 'SEMI' and 'rector' in a:
        return 'compat-rector --site $SITE'
    return None


def compat_parts(a):
    """Parts of the compatibility scan (FR-CMPT-*) that answer a P3 AUTO item; None = not a compat step."""
    a = re.sub(r'^\((?:a|khi [^)]*)\)\s*', '', a)
    if 'cùng abi' in a:
        return None                     # same ABI: patch flow, no compatibility scan
    parts = []
    if a.startswith('lint') or a.startswith('quét ngược'):
        parts.append('lint_new_bin')
    if a.startswith(('lint', 'quét phpcompatibility', 'quét ngược')) and 'phpcompatibility' in a:
        parts.append('phpcompat')
    if a.startswith('quét bộ luật bc') or (a.startswith('lint') and 'bộ luật bc' in a):
        parts.append('code_scan')
    if a.startswith('kiểm tra platform composer'):
        parts.append('composer_platform')
    if a.startswith('kiểm tra `engines.node`'):
        parts.append('npm_engines')
    if a.startswith(('build lại và nạp thử native addon', 'nạp thử native addon')):
        parts.append('native_addons')
    return parts or None


def flow_of(item, kind):
    """patch = same-branch flow, upgrade = only when the branch changes, both = either plan mode."""
    if item['applies_when'] and 'mode=cross_branch' in item['applies_when']:
        return 'upgrade'
    a = item['action'].lower()
    head = (item['cli_action'] or '').split(' ')[0]
    if kind == 'OVERLAY' or head in ('scan', 'assess', 'fix') or a.startswith(PATCH_FLOW):
        return 'both'
    return 'upgrade'


def scenarios_of(files, runtime):
    summ = summary(read(files[0]), runtime)
    scenarios, items = [], []
    for name in files:
        lines = read(name)
        for i, line in enumerate(lines):
            m = re.match(r'^#{2,3} (?:[\d.]+ )?(SCN-(?:PHP|NODE)-\d{3}) — (.*)$', line)
            if not m:
                continue
            sid, title = m.group(1), m.group(2).strip()
            header, attr_rows, j = table_after(lines, i + 1)
            attrs = {clean(r[0]).replace('`', ''): clean(r[1]) for r in attr_rows if len(r) >= 2}
            raw_attrs = {clean(r[0]): clean(r[1]) for r in attr_rows if len(r) >= 2}
            vmatch, order, cond = parse_attr(raw_attrs, sid)
            header, chk_rows, _ = table_after(lines, j)
            if not header or header[0] != 'Mã':
                raise SystemExit('no checklist table for %s' % sid)
            its = checklist_rows(header, chk_rows, sid, runtime)
            s = summ.get(sid)
            for it in its:
                it['flow'] = flow_of(it, s['kind'] if s else 'VERSION')
            if not s:
                raise SystemExit('%s not in the summary table' % sid)
            if len(its) != s['count']:
                raise SystemExit('%s: %d checklist items, summary says %d' % (sid, len(its), s['count']))
            bc_key = next((k for k in attrs if k.startswith('Dải BC')), None)
            scenarios.append({
                'scenario_id': sid, 'runtime': runtime, 'kind': s['kind'], 'title': title,
                'version_match': vmatch, 'match_order': order, 'match_condition': cond,
                'range': s['range'], 'bc_scope': attrs.get(bc_key) if bc_key else None,
                'target_note': attrs.get('Đích') or s['target_note'],
                'checklist_count': len(its), 'data_as_of': DATA_AS_OF,
            })
            items.extend(its)
    scenarios.sort(key=lambda x: x['scenario_id'])
    return scenarios, items, summ


# --- breaking changes --------------------------------------------------------
def bc_rules():
    rules = []
    lines = read('version-scenarios-php.md')
    for line in lines:
        if not line.startswith('| `BC-PHP-'):
            continue
        c = split_row(line)
        rid, ver, change, kind, scan, repl = unquote(c[0]), c[1], clean(c[2]), clean(c[3]), c[4], clean(c[5])
        info_part = None
        if 'mức `info`:' in scan:
            scan, info_part = scan.split('mức `info`:', 1)
        level = 'error' if re.search(r'Xoá', kind) else 'warning'
        pats = [{'pattern': p, 'level': level} for p in re.findall(r'`([^`]+)`', scan) if p.strip()]
        if info_part:
            pats += [{'pattern': p, 'level': 'info'} for p in re.findall(r'`([^`]+)`', info_part)]
        rules.append({'rule_id': rid, 'runtime': 'php', 'version': re.sub(r'\s*\(RC\)', '', ver).strip(),
                      'prerelease': '(RC)' in ver, 'change': change, 'kind': kind, 'level': level,
                      'detect': clean(scan + (' mức info: ' + info_part if info_part else '')),
                      'phpc': 'PHPC' in scan, 'runtime_only': scan.strip().startswith('Runtime'),
                      'ini': 'ini' in scan, 'patterns': pats, 'replacement': repl})
    for line in read('version-scenarios-node.md'):
        if not line.startswith('| `BC-NODE-'):
            continue
        c = split_row(line)
        rid, ver, change, kind, detect, fix = unquote(c[0]), c[1].strip(), clean(c[2]), clean(c[3]), c[4], clean(c[5])
        level = 'error' if 'Xoá' in kind else 'warning'
        static = detect.split('Tĩnh:', 1)[1] if 'Tĩnh:' in detect else ''
        static = re.split(r';\s*(?:Runtime|`ldd)', static)[0]
        pats = [{'pattern': p, 'level': level} for p in re.findall(r'`([^`]+)`', static)]
        rules.append({'rule_id': rid, 'runtime': 'node', 'version': ver, 'prerelease': False, 'change': change,
                      'kind': kind, 'level': level, 'detect': clean(detect), 'phpc': False,
                      'runtime_only': not pats, 'ini': False, 'patterns': pats, 'replacement': fix})
    known = {r['rule_id'] for r in rules}
    for rid in SCAN:
        if rid not in known:
            raise SystemExit('SCAN rule %s not in the BC tables' % rid)
    for r in rules:
        r['scan'] = [{'regex': rx, 'level': lvl, 'kind': 'php4_ctor' if rx == 'php4_ctor' else 'code'}
                     for rx, lvl in SCAN.get(r['rule_id'], [])]
        for sc in r['scan']:
            if sc['kind'] == 'code':
                re.compile(sc['regex'])
    return rules


# --- machine rules of the BC catalog (FR-CMPT-CODE-001, FR-CMPT-INI-001, FR-CMPT-EXT-001) ---
# The "Mẫu quét" column of §5 mixes regexes with prose ("Tên hàm", "Runtime",
# "ini: danh sách BR-SCN-046"); the regexes below are that column made exact
# (Python `re`, one line at a time). Function names come from the "Thay đổi"
# column. level: the column "Loại" of the part the pattern detects (BR-SCN-041).
def _fn(*names, tail=r'\s*\('):
    """Call of one of NAMES (not a method, not a declaration), followed by TAIL."""
    return r'(?<![\w$>:])(?<!function )\\?\b(?:%s)' % '|'.join(names) + tail


PREG_E = r"""preg_replace\s*\(\s*(['"])([^\w\s\\]).*?\2[a-zA-Z]*e[a-zA-Z]*\1"""
SCAN = {
    'BC-PHP-50-01': [(r'=&\s*new\b', 'warning')],
    'BC-PHP-50-02': [(_fn('array_merge'), 'warning'), (r'ip2long\s*\([^)]*\)\s*[!=]==?\s*-1', 'warning'),
                     (r'(?<![\w$>:])\b(?:include|require)\s*\(', 'warning')],
    'BC-PHP-53-01': [(_fn('ereg', 'eregi', 'ereg_replace', 'eregi_replace', 'split', 'spliti', 'sql_regcase',
                          'session_register', 'call_user_method', 'set_magic_quotes_runtime', 'dl'), 'warning'),
                     (r'=&\s*new\b', 'warning')],
    'BC-PHP-54-02': [(r'^(?!.*\b(?:function|fn|use)\b).*(?<![\w$>:])\b[A-Za-z_]\w*\s*\((?:[^()]*,)?\s*&\s*\$\w+', 'error')],
    'BC-PHP-54-03': [(_fn('session_register', 'session_unregister', 'session_is_registered',
                          'import_request_variables', 'define_syslog_variables'), 'error'),
                     (r'\b(?:break|continue)\s+\$', 'error')],
    'BC-PHP-54-04': [(_fn('htmlspecialchars', 'htmlentities', 'html_entity_decode', tail=r'\s*\(\s*[^,()]*\)'), 'warning')],
    'BC-PHP-55-01': [(_fn(r'mysql_\w+'), 'warning'), (PREG_E, 'warning'), (_fn('mcrypt_ecb', 'mcrypt_cbc', 'mcrypt_cfb', 'mcrypt_ofb'), 'warning')],
    'BC-PHP-56-01': [(r'''file_get_contents\s*\(\s*['"]https''', 'warning')],
    'BC-PHP-56-02': [(r'\$HTTP_RAW_POST_DATA\b', 'warning')],
    'BC-PHP-70-01': [(_fn(r'mysql_\w+', r'ereg\w*', r'eregi\w*', 'split', 'spliti', 'sql_regcase', r'mssql_\w+', r'sybase_\w+'), 'error')],
    'BC-PHP-70-02': [(r'<%', 'error'), (r'''<script\s+language\s*=\s*["']?php''', 'error')],
    'BC-PHP-70-03': [(PREG_E, 'error')],
    'BC-PHP-70-04': [(_fn('call_user_method', 'call_user_method_array', 'set_magic_quotes_runtime', 'mcrypt_generic_end',
                          'mcrypt_ecb', 'mcrypt_cbc', 'mcrypt_cfb', 'mcrypt_ofb'), 'error'),
                     (r'\$HTTP_RAW_POST_DATA\b', 'error')],
    'BC-PHP-70-05': [('php4_ctor', 'warning')],
    'BC-PHP-71-01': [(_fn(r'mcrypt_\w+'), 'warning')],
    'BC-PHP-72-01': [(_fn(r'mcrypt_\w+'), 'error')],
    'BC-PHP-72-02': [(_fn('each', 'create_function'), 'warning'), (r'\bfunction\s+__autoload\b', 'warning'),
                     (r'\(unset\)', 'warning'), (r'\$php_errormsg\b', 'warning')],
    'BC-PHP-73-01': [(r'\bdefine\s*\([^)]*,\s*true\s*\)', 'warning')],
    'BC-PHP-74-01': [(r'\$\w+\{\s*[\$\d\'"]', 'warning'), (r'\(real\)', 'warning'),
                     (_fn('is_real', 'get_magic_quotes_gpc', 'get_magic_quotes_runtime', 'money_format', 'hebrevc',
                          'convert_cyr_string', 'ezmlm_hash', 'restore_include_path'), 'warning')],
    'BC-PHP-74-02': [(_fn(r'ibase_\w+', r'recode\w*', r'wddx_\w+'), 'error')],
    'BC-PHP-80-02': [(_fn('each', 'create_function', 'money_format', 'hebrevc', 'convert_cyr_string', 'ezmlm_hash',
                          'restore_include_path', 'get_magic_quotes_gpc', 'get_magic_quotes_runtime', 'read_exif_data',
                          'gmp_random', 'imap_header'), 'error'),
                     (r'\bfunction\s+__autoload\b', 'error'), (r'\((?:real|unset)\)', 'error'), (r'\$php_errormsg\b', 'error')],
    'BC-PHP-80-03': [('php4_ctor', 'error')],
    'BC-PHP-80-04': [(r'\bfunction\s+match\s*\(', 'error'), (r'\bclass\s+match\b', 'error'),
                     (r'\$\w+\{\s*[\$\d\'"]', 'error')],
    'BC-PHP-80-05': [(_fn('is_resource'), 'warning')],
    'BC-PHP-80-06': [(_fn(r'xmlrpc_\w+'), 'error')],
    'BC-PHP-81-02': [(_fn('array_pop', 'array_shift', 'array_push', 'array_unshift', 'array_splice',
                          tail=r'\s*\(\s*\$GLOBALS\b'), 'error')],
    'BC-PHP-81-03': [(_fn('strftime', 'gmstrftime', 'strptime', 'date_sunrise', 'date_sunset', 'mhash', r'mhash_\w+',
                          'odbc_result_all'), 'warning'), (r'\bFILTER_SANITIZE_STRING\b', 'warning')],
    'BC-PHP-82-02': [(_fn('utf8_encode', 'utf8_decode'), 'warning'), (r'"[^"]*\$\{', 'warning')],
    'BC-PHP-83-01': [(r'(?<![\w$>:])\bget_(?:parent_)?class\s*\(\s*\)', 'warning')],
    'BC-PHP-84-01': [(r'\bfunction\b[^{;]*[(,]\s*(?!\?|mixed\b|null\b)[A-Za-z_\\][\w\\]*\s+&?(?:\.\.\.)?\$\w+\s*=\s*null\b', 'warning')],
    'BC-PHP-84-02': [(r'\bE_STRICT\b', 'warning')],
    'BC-PHP-84-03': [(_fn(r'imap_\w+', r'oci_\w+', r'pspell_\w+'), 'error')],
    'BC-PHP-85-01': [(r"""^[^'"#/]*`[^`]*`""", 'warning'), (r'\((?:boolean|integer|double|binary)\)', 'warning'),
                     (r'\bcase\s+[^:;?]+;', 'warning'), (r'\bfunction\s+__(?:sleep|wakeup)\s*\(', 'info')],
    'BC-NODE-18-01': [(r'\bglobal(?:This)?\.fetch\s*=', 'warning')],
    'BC-NODE-20-01': [(r'\burl\.parse\s*\(', 'warning'), (r'\bnew\s+WASI\s*\(', 'warning')],
    'BC-NODE-22-01': [(r'\bassert\s*\{\s*type', 'error'), (r'\bcreate(?:De)?[Cc]ipher\s*\(', 'error'),
                      (r'\butil\.is[A-Z]\w*\s*\(', 'warning')],
    'BC-NODE-23-01': [(r'\bprocess\.assert\s*\(', 'error'), (r'\bzlib\b.*\bbytesRead\b', 'error')],
    'BC-NODE-24-01': [(r'\bcreateSecurePair\s*\(', 'error'), (r'\bSlowBuffer\b', 'warning'),
                      (r'\bfs\.[FRWX]_OK\b', 'warning'), (r'--experimental-permission\b', 'warning')],
    'BC-NODE-25-01': [(r'\bSlowBuffer\b', 'error'), (r'\bfs\.[FRWX]_OK\b', 'error')],
    'BC-NODE-26-01': [(r'\.writeHeader\s*\(', 'error'), (r'''\brequire\s*\(\s*['"]_stream_''', 'error'),
                      (r'''\bfrom\s+['"]_stream_''', 'error'), (r'\bmodule\.register\s*\(', 'warning'),
                      (r'--experimental-transform-types\b', 'error')],
}

# BR-SCN-046: ini directives removed in the version range (removed_in).
INI_REMOVED = [
    ('register_globals', '5.4'), ('register_long_arrays', '5.4'), ('magic_quotes_gpc', '5.4'),
    ('magic_quotes_runtime', '5.4'), ('magic_quotes_sybase', '5.4'), ('safe_mode', '5.4'), ('safe_mode_gid', '5.4'),
    ('safe_mode_include_dir', '5.4'), ('safe_mode_exec_dir', '5.4'), ('safe_mode_allowed_env_vars', '5.4'),
    ('safe_mode_protected_env_vars', '5.4'), ('allow_call_time_pass_reference', '5.4'),
    ('define_syslog_variables', '5.4'), ('y2k_compliance', '5.4'), ('zend.ze1_compatibility_mode', '5.4'),
    ('asp_tags', '7.0'), ('always_populate_raw_post_data', '7.0'), ('sql.safe_mode', '7.2'),
    ('track_errors', '8.0'), ('mbstring.func_overload', '8.0'), ('disable_classes', '8.5'),
]
OPCACHE_LINE = r'^\s*zend_extension\s*=\s*"?([^"]*/)?opcache(\.so)?"?\s*$'

# Extensions taken out of core (BC-PHP-* "Xoá ext"): function prefixes, replacement.
EXT_REMOVED = [
    ('mysql', '7.0', 'BC-PHP-70-01', 'mysqli', ['mysql_']), ('ereg', '7.0', 'BC-PHP-70-01', 'pcre', ['ereg', 'eregi']),
    ('mssql', '7.0', 'BC-PHP-70-01', 'pdo_dblib', ['mssql_']), ('sybase_ct', '7.0', 'BC-PHP-70-01', 'pdo_dblib', ['sybase_']),
    ('mcrypt', '7.2', 'BC-PHP-72-01', 'openssl', ['mcrypt_']), ('interbase', '7.4', 'BC-PHP-74-02', 'pdo_firebird', ['ibase_']),
    ('recode', '7.4', 'BC-PHP-74-02', 'iconv', ['recode']), ('wddx', '7.4', 'BC-PHP-74-02', 'json', ['wddx_']),
    ('xmlrpc', '8.0', 'BC-PHP-80-06', None, ['xmlrpc_']), ('imap', '8.4', 'BC-PHP-84-03', None, ['imap_']),
    ('oci8', '8.4', 'BC-PHP-84-03', None, ['oci_']), ('pdo_oci', '8.4', 'BC-PHP-84-03', None, []),
    ('pspell', '8.4', 'BC-PHP-84-03', None, ['pspell_']),
]
# Compiled into every PHP build (no package to install); opcache from 8.5 (BR-SCN-045).
BUILTIN_EXT = ['core', 'date', 'filter', 'hash', 'json', 'libxml', 'pcre', 'random', 'reflection', 'spl', 'standard',
               'zlib', 'openssl', 'session', 'ctype', 'tokenizer', 'fileinfo', 'iconv', 'phar', 'posix', 'sockets',
               'calendar', 'exif', 'ftp', 'gettext', 'pdo', 'shmop', 'sysvmsg', 'sysvsem', 'sysvshm', 'ffi',
               'zend opcache@8.5']
# Debian/Ubuntu package suffix of an extension (php<X.Y>-<suffix>, PB-001).
EXT_PACKAGES = {'mysqli': 'mysql', 'mysqlnd': 'mysql', 'pdo_mysql': 'mysql', 'dom': 'xml', 'simplexml': 'xml',
                'xml': 'xml', 'xmlreader': 'xml', 'xmlwriter': 'xml', 'xsl': 'xml', 'pdo_sqlite': 'sqlite3',
                'sqlite3': 'sqlite3', 'pgsql': 'pgsql', 'pdo_pgsql': 'pgsql', 'zend opcache': 'opcache',
                'curl': 'curl', 'gd': 'gd', 'mbstring': 'mbstring', 'intl': 'intl', 'zip': 'zip', 'bcmath': 'bcmath',
                'soap': 'soap', 'readline': 'readline', 'imagick': 'imagick', 'redis': 'redis', 'memcached': 'memcached',
                'apcu': 'apcu', 'igbinary': 'igbinary', 'msgpack': 'msgpack', 'gmp': 'gmp', 'ldap': 'ldap',
                'snmp': 'snmp', 'tidy': 'tidy', 'odbc': 'odbc', 'pdo_odbc': 'odbc', 'enchant': 'enchant',
                'xdebug': 'xdebug', 'pcov': 'pcov', 'mongodb': 'mongodb', 'amqp': 'amqp', 'yaml': 'yaml',
                'imap': 'imap', 'xmlrpc': 'xmlrpc', 'ssh2': 'ssh2', 'uuid': 'uuid'}
# Composer packages of the frameworks of FR-CMPT-FWK-001 -> framework_php.tsv name.
FRAMEWORK_PACKAGES = {'laravel/framework': 'Laravel', 'symfony/http-kernel': 'Symfony', 'drupal/core': 'Drupal',
                      'drupal/core-recommended': 'Drupal', 'magento/product-community-edition': 'Magento',
                      'magento/magento2-base': 'Magento', 'codeigniter4/framework': 'CodeIgniter',
                      'joomla/cms': 'Joomla', 'joomla/joomla-cms': 'Joomla'}


# --- framework matrix, loaders, ABI ------------------------------------------
def framework_rows():
    rows = []
    lines = read('version-scenarios-php.md')
    start = next(i for i, l in enumerate(lines) if l.startswith('## 6. Ma trận framework'))
    _, table, _ = table_after(lines, start)
    for c in table:
        fw, vers, pmin, pmax, status, src = [clean(x).replace('`', '') for x in c[:6]]
        v_parts = [v.strip() for v in vers.split(' / ')]
        mins = [v.strip() for v in pmin.split(' / ')]
        maxs = [v.strip() for v in pmax.split(' / ')]
        n = len(v_parts)
        for k in range(n):
            mn = mins[k] if len(mins) == n else pmin
            mx = maxs[k] if len(maxs) == n else pmax
            rows.append((fw, v_parts[k], norm_php(mn), norm_php(mx), status, src))
    return rows


def norm_php(v):
    m = re.match(r'^(\d+\.\d+(?:\.\d+)?)', v)
    return m.group(1) if m else ''


def loaders():
    lines = read('version-scenarios-php.md')
    start = next(i for i, l in enumerate(lines) if l.startswith('**Bảng 7.1.1'))
    _, table, _ = table_after(lines, start)
    ioncube = {}
    for c in table:
        b, minv = c[0].strip(), c[1]
        m = re.match(r'^(\d+\.\d+(?:\.\d+)?)', minv.strip())
        if re.match(r'^\d+\.\d+$', b) and m:
            ioncube[b] = m.group(1)
    text = '\n'.join(lines)
    sg = re.search(r'PHP (\d+\.\d+) đến (\d+\.\d+) được hỗ trợ đầy đủ', text)
    return {
        'ioncube': {'detect': ['ionCube PHP Loader', 'ionCube Loader', '<?php //0'], 'min_loader_by_branch': ioncube,
                    'no_loader_branches': ['8.0']},
        'sourceguardian': {'detect': ['SourceGuardian', 'sg_load('], 'php_min': sg.group(1), 'php_max': sg.group(2)},
        'zend_guard': {'detect': ['Zend Guard Loader', 'Zend Optimizer'], 'php_min': None, 'php_max': None},
    }


def node_abi():
    lines = read('version-scenarios-node.md')
    start = next(i for i, l in enumerate(lines) if l.startswith('### 6.1'))
    header, table, _ = table_after(lines, start)
    lines_ = [h.strip() for h in header[1:]]
    out = {}
    for c in table:
        key = clean(c[0]).replace('`', '')
        out[key] = dict(zip(lines_, [x.strip() for x in c[1:]]))
    return {'node_module_version': out.get('NODE_MODULE_VERSION', {}), 'npm_latest': out.get('npm của bản mới nhất', {})}


# --- playbooks ---------------------------------------------------------------
DETECT = {
    'PB-001': [{'type': 'os_release', 'value': 'debian'}, {'type': 'exec', 'value': 'apt-get'}],
    'PB-002': [{'type': 'os_release', 'value': 'rhel'}, {'type': 'exec', 'value': 'dnf|yum'}],
    'PB-003': [{'type': 'cmd_exit0', 'value': 'rpm -q remi-release'}, {'type': 'file', 'value': '/etc/yum.repos.d/remi*.repo'}],
    'PB-004': [{'type': 'os_release', 'value': 'alpine'}, {'type': 'exec', 'value': 'apk'}],
    'PB-005': [{'type': 'cmd_exit0', 'value': "pgrep -f 'nginx: master'"},
               {'type': 'cmd_exit0', 'value': "apachectl -M | grep proxy_fcgi_module"}],
    'PB-006': [{'type': 'cmd_exit0', 'value': "apachectl -M | grep -E 'php[0-9]*_module'"},
               {'type': 'file', 'value': '/etc/apache2/mods-enabled/php*.load'}],
    'PB-007': [{'type': 'exec', 'value': '/usr/local/cpanel/cpanel'}],
    'PB-008': [{'type': 'exec', 'value': 'selectorctl'}, {'type': 'file', 'value': '/etc/cl.selector/selector.conf'}],
    'PB-009': [{'type': 'dir', 'value': '/usr/local/psa'}],
    'PB-010': [{'type': 'dir', 'value': '/www/server/panel'}],
    'PB-011': [{'type': 'dir', 'value': '/usr/local/CyberCP'}, {'type': 'exec', 'value': '/usr/local/lsws/bin/lswsctrl'}],
    'PB-012': [{'type': 'dir', 'value': '/usr/local/directadmin'}],
    'PB-013': [{'type': 'cmd_exit0', 'value': 'docker info'}],
    'PB-014': [{'type': 'cmd_exit0', 'value': 'apt-cache policy nodejs | grep nodesource'}],
    'PB-015': [{'type': 'dir', 'value': '$PREFIX/lib/node_modules/npm'}],
    'PB-016': [{'type': 'file', 'value': '*/.nvm/versions/node/*'}],
    'PB-017': [{'type': 'cmd_exit0', 'value': 'systemctl cat <unit> | grep ExecStart'}],
    'PB-018': [{'type': 'cmd_exit0', 'value': 'pm2 jlist'}],
    'PB-000': [],
}
LAYER = {'provider': 'provider', 'binding': 'binding', 'panel': 'panel', 'panel overlay': 'panel_overlay',
         'provider + binding': 'provider', '—': 'provider'}
RUNTIME = {'PB-014': 'node', 'PB-015': 'node', 'PB-016': 'node', 'PB-017': 'node', 'PB-018': 'node', 'PB-013': 'both'}


def action_of(cell, ref):
    text = clean(cell)
    if text.startswith('—') or not text:
        return []
    m = re.search(r'\b(AUTO|SEMI|MANUAL)\b', text)
    exec_type = m.group(1) if m else 'MANUAL'
    verified = not re.search(r'chưa chạy thử|Chưa|chưa kiểm chứng', text)
    return [{'cmd': text, 'exec_type': exec_type if verified or exec_type != 'AUTO' else 'SEMI',
             'verified': verified, 'source_ref': ref}]


def playbooks():
    lines = read('environment-playbooks.md')
    start = next(i for i, l in enumerate(lines) if l.startswith('## 3. Danh mục playbook'))
    _, table, _ = table_after(lines, start)
    out = []
    for c in table:
        pb = unquote(c[0])
        ref = re.sub(r'.*\]\(([^)]+)\).*', r'\1', c[9]) if '](' in c[9] else clean(c[9])
        layer = LAYER.get(clean(c[2]), 'provider')
        out.append({
            'pb_id': pb, 'environment': clean(c[1]), 'layer': layer, 'runtime': RUNTIME.get(pb, 'php'),
            'detect_rules': DETECT.get(pb, []), 'detect_note': clean(c[3]),
            'actions': {'inventory': [{'cmd': clean(c[3]) or 'scan', 'exec_type': 'AUTO', 'verified': True, 'source_ref': ref}]
                        if pb != 'PB-000' else [],
                        'patch': action_of(c[4], ref), 'install': action_of(c[5], ref), 'switch': action_of(c[6], ref),
                        'healthcheck_inputs': [], 'rollback': action_of(c[7], ref), 'reload': []},
            'backup_paths': [], 'requires_root': clean(c[8]).startswith('Có'), 'switch_budget_s': 30,
        })
    return out


# --- mitigations (FR-PTCH-MIT-001, inherited from v0.1 php_mitigation_ini) ----
PHP2SHELL = ['CVE-2026-109618', 'CVE-2026-109619']
MITIGATIONS = [
    {'rule_id': 'MIT-PHP-001', 'runtime': 'php', 'cves': PHP2SHELL, 'branches': [],
     'directive': 'session.upload_progress.enabled = 0', 'flag': None,
     'note': 'PHP2Shell: turn off session upload progress (v0.1)'},
    {'rule_id': 'MIT-PHP-002', 'runtime': 'php', 'cves': PHP2SHELL, 'branches': [],
     'directive': 'memory_limit = -1', 'flag': 'memlimit',
     'note': 'PHP2Shell: no memory_limit (skipped with --no-memlimit; an app may override it)'},
    {'rule_id': 'MIT-PHP-003', 'runtime': 'php', 'cves': PHP2SHELL, 'branches': ['8.5'],
     'directive': 'fatal_error_backtraces = 0', 'flag': None,
     'note': 'PHP2Shell: no backtraces in fatal errors (8.5 only)'},
]


# --- write -------------------------------------------------------------------
def dump_lines(path, head, key, records):
    """JSON with one record per line under KEY (greppable by php-quickpatch.sh)."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{' + ', '.join('%s: %s' % (json.dumps(k), json.dumps(v)) for k, v in head.items()))
        f.write(', %s: [\n' % json.dumps(key))
        f.write(',\n'.join(json.dumps(r, ensure_ascii=False, sort_keys=False) for r in records))
        f.write('\n]}\n')


def pinned_tools():
    """tools/pinned-tools.json (tools/pin-tools.py): versions and hashes of the scan tools."""
    p = os.path.join(ROOT, 'tools', 'pinned-tools.json')
    with open(p) as f:
        return json.load(f)


def main(argv):
    version, out = CATALOG_VERSION, OUT
    if '--version' in argv:
        version = argv[argv.index('--version') + 1]
    if '--out' in argv:
        out = argv[argv.index('--out') + 1]
    if not re.match(r'^\d{4}\.\d{2}\.\d{2}-\d+$', version):
        raise SystemExit('bad catalog version %s' % version)
    php_s, php_i, php_sum = scenarios_of(['version-scenarios-php.md', 'version-scenarios-php-8x.md'], 'php')
    node_s, node_i, node_sum = scenarios_of(['version-scenarios-node.md'], 'node')
    for runtime, s, summ, total in (('php', php_s, php_sum, 399), ('node', node_s, node_sum, 224)):
        if len(s) != len(summ):
            raise SystemExit('%s: %d scenarios parsed, summary has %d' % (runtime, len(s), len(summ)))
    if len(php_i) != 399 or len(node_i) != 224:
        raise SystemExit('checklist totals %d/%d, expected 399/224' % (len(php_i), len(node_i)))
    items = php_i + node_i
    ids = [i['chk_id'] for i in items]
    if len(set(ids)) != len(ids):
        raise SystemExit('duplicate chk_id')
    known = set(ids)
    for it in items:
        it['refs'] = [r for r in it['refs'] if r in known]
    os.makedirs(out, exist_ok=True)
    head = {'schema': 'qp.catalog/1', 'catalog_version': version}
    dump_lines(os.path.join(out, 'scenarios.json'), head, 'scenarios', php_s + node_s)
    dump_lines(os.path.join(out, 'mitigations.json'), head, 'rules', MITIGATIONS)
    bc_extra = {'ini_removed': [{'directive': d, 'removed_in': v} for d, v in INI_REMOVED],
                'opcache_line': OPCACHE_LINE,
                'ext_removed': [{'extension': e, 'removed_in': v, 'rule_id': r, 'replacement': rep, 'prefixes': px}
                                for e, v, r, rep, px in EXT_REMOVED],
                'builtin_ext': BUILTIN_EXT, 'ext_packages': EXT_PACKAGES, 'framework_packages': FRAMEWORK_PACKAGES}
    for name, key, data, extra in (('checklists.json', 'items', items, {}), ('playbooks.json', 'playbooks', playbooks(), {}),
                                   ('bc_rules.json', 'rules', bc_rules(), bc_extra)):
        with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
            json.dump(dict(head, **{key: data}, **extra), f, ensure_ascii=False, indent=1, sort_keys=False)
            f.write('\n')
    with open(os.path.join(out, 'framework_php.tsv'), 'w', encoding='utf-8') as f:
        f.write('framework\tversions\tphp_min\tphp_max\tstatus\tsource\n')
        for r in framework_rows():
            f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')
    meta = dict(head, data_as_of=DATA_AS_OF, built_from=sorted(
        ['version-scenarios-php.md', 'version-scenarios-php-8x.md', 'version-scenarios-node.md',
         'environment-playbooks.md']),
        counts={'scenarios': len(php_s) + len(node_s), 'checklist_items': len(items), 'php_items': len(php_i),
                'node_items': len(node_i)},
        loaders=loaders(), node=node_abi(),
        composer={'lts': {'version': '2.2.30', 'php_min': '5.3.2', 'support_until': '2026-12-31'},
                  'stable': {'version': '2.10.3', 'php_min': '7.2.5'}},
        thresholds={'php_target_ga_age_days': 90, 'target_eol_min_days': 365, 'node_lts_within_days': 14,
                    'deadline_before_eol_days': 30, 'deadline_warn_days': 90},
        tools=pinned_tools(),
        files=FILES[:-1])
    with open(os.path.join(out, 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write('\n')
    with open(os.path.join(out, 'SHA256SUMS'), 'w') as f:
        for name in FILES:
            with open(os.path.join(out, name), 'rb') as g:
                f.write('%s  %s\n' % (hashlib.sha256(g.read()).hexdigest(), name))
    print('catalog %s: %d scenarios, %d checklist items (%d PHP, %d Node.js) -> %s'
          % (version, len(php_s) + len(node_s), len(items), len(php_i), len(node_i), os.path.relpath(out, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
