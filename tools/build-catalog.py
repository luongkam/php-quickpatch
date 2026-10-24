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
CATALOG_VERSION = '2026.10.24-1'
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
            'cli_action': cli_action(runtime, action, exec_type),
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


def cli_action(runtime, action, exec_type):
    """Whitelisted CLI action of an item the tool runs itself (FR-PLAN-CHK-002); None = guided."""
    a = action.lower()
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
    return None


def flow_of(item, kind):
    """patch = same-branch flow, upgrade = only when the branch changes, both = either plan mode."""
    if item['applies_when'] and 'mode=cross_branch' in item['applies_when']:
        return 'upgrade'
    a = item['action'].lower()
    if kind == 'OVERLAY' or item['cli_action'] or a.startswith(PATCH_FLOW):
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
    return rules


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
    for name, key, data in (('checklists.json', 'items', items), ('playbooks.json', 'playbooks', playbooks()),
                            ('bc_rules.json', 'rules', bc_rules())):
        with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
            json.dump(dict(head, **{key: data}), f, ensure_ascii=False, indent=1, sort_keys=False)
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
