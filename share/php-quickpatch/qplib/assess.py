"""`assess` (FR-CLI-CMD-001): current runtime vs candidate versions.

FR-ASMT-CUR-001 current, FR-ASMT-CAND-001/002 candidates and installability,
FR-ASMT-CMP-001 comparison rows (R, delta_R on one bundle and one day T,
BR-ASMT-003). Runtimes come from the newest `scan --json` (state/last-scan.json,
re-run when older than 24 h or when the runtime is not in it).
"""
import json
import os
import re
import subprocess
import time

from . import catalog as qcatalog, errors
from .feeds import risk as R, versions as V
from .feeds.query import Bundle
from .feeds.store import FeedsDir, parse_iso

SCAN_MAX_AGE_S = 24 * 3600
SUPPORTED_PHP = ('ACTIVE', 'SECURITY_ONLY')
LTS_NODE = ('ACTIVE_LTS', 'MAINTENANCE_LTS')
CLOSED = ('EOL', 'PRE_RELEASE', 'UNKNOWN')
EOL_LABEL = {'en': 'EOL branch: sources no longer assess new CVEs',
             'vi': 'Nhánh EOL — nguồn không còn đánh giá CVE mới'}


def today_of(a=None):
    v = a.date('--today') if a is not None else None
    v = v or os.environ.get('QP_TODAY') or ''
    return v if re.match(r'^\d{4}-\d{2}-\d{2}$', v) else time.strftime('%Y-%m-%d', time.gmtime())


def add_days(date, n):
    return time.strftime('%Y-%m-%d', time.gmtime((R.day_number(date) + n) * 86400))


# --- scan result --------------------------------------------------------------
def last_scan_path(state_dir):
    return os.path.join(state_dir, 'state', 'last-scan.json')


def read_scan(state_dir):
    try:
        with open(last_scan_path(state_dir), encoding='utf-8') as f:
            doc = json.load(f)
        return doc if isinstance(doc.get('result'), dict) else None
    except (OSError, ValueError):
        return None


def run_scan(offline=False):
    """`php-quickpatch.sh scan --json` (read only, shared lock); it also refreshes state/last-scan.json."""
    script = os.environ.get('QP_SCRIPT') or ''
    if not os.path.isfile(script):
        raise errors.error('ERR-CLI-424-01', '{command} is not installed ({file} missing).', command='scan', file=script)
    cmd = ['bash', script, 'scan', '--json', '--only', 'php,node,sites'] + (['--offline'] if offline else [])
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=900)
        doc = json.loads(p.stdout.decode('utf-8'))
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        raise errors.error('ERR-CLI-424-01', '{command} failed: {file}', command='scan', file=str(e))
    if not isinstance(doc.get('result'), dict):
        raise errors.error('ERR-CLI-424-01', '{command} failed: {file}', command='scan',
                           file='; '.join(e.get('message', '') for e in doc.get('errors') or []))
    return doc


def scan_for(state_dir, offline=False, want=None, refresh=True):
    """Newest scan; a new one when it is missing, older than 24 h or WANT(doc) is false."""
    doc = read_scan(state_dir)
    if doc and time.time() - parse_iso(doc['generated_at']) <= SCAN_MAX_AGE_S and (want is None or want(doc)):
        return doc
    if not refresh:
        return doc
    return run_scan(offline)


def find_runtime(doc, runtime_id=None, bin_path=None):
    for rt in (doc or {}).get('result', {}).get('runtimes') or []:
        if (runtime_id and rt.get('runtime_id') == runtime_id) or (bin_path and rt.get('bin') == bin_path):
            return rt
    return None


def sites_of(doc, runtime_id):
    return [s for s in (doc or {}).get('result', {}).get('sites') or [] if s.get('runtime_id') == runtime_id]


# --- one version on the bundle ---------------------------------------------------
class Evaluator(object):
    """R and lifecycle of any version of a product on one bundle and one day T."""

    def __init__(self, bundle, today):
        self.b = bundle
        self.today = today
        self._adv = None

    def lifecycle_row(self, product, branch):
        return self.b.lifecycle(product, branch)

    def version(self, product, version, exclude=(), status=None):
        q = self.b.assess(product, version, self.today, exclude=exclude)
        if status and status != q['lifecycle_status']:
            e = q['exposure']
            sc = R.score(status, q['days_to_eol'], e['n_crit'], e['n_high'], e['n_med'], e['n_low'], e['n_kev'],
                         e['cvss10'])
            q['lifecycle_status'] = status
            q['priority'] = sc['priority']
            q['risk'] = {'R': sc['R'], 'score': sc['R'], 'level': sc['level'], 'components': sc['components']}
        lc = self.lifecycle_row(product, q['branch']) or {}
        q['is_lts'] = (bool(lc.get('lts_start')) if product == 'node' else None)
        q['lts_start'] = lc.get('lts_start')
        q['ga_date'] = lc.get('ga_date')
        return q

    def advisories(self, ids, fixed_ids, branch, product):
        if self._adv is None:
            self._adv = {r['adv_id']: r for r in self.b.tsv('advisories.tsv')}
            self._alias = {}
            for r in self.b.tsv('aliases.tsv'):
                self._alias.setdefault(r['adv_id'], []).append(r['alias_id'])
            self._aff = {}
            for r in self.b.tsv('affected.tsv'):
                self._aff.setdefault(r['adv_id'], []).append(r)
        out = []
        for aid, st in [(i, 'UNPATCHED') for i in ids] + [(i, 'FIXED_BACKPORT') for i in fixed_ids]:
            a = self._adv.get(aid)
            if not a:
                continue
            aff = [r for r in self._aff.get(aid, []) if r['product'] == product]
            fixed = next((r['fixed_in_branch'] for r in aff if r.get('fixed_in_branch')
                          and V.branch_of(product, r['fixed_in_branch']) == branch), None)
            out.append({'adv_id': aid, 'aliases': self._alias.get(aid, []),
                        'cvss': float(a['cvss_rep']) if a.get('cvss_rep') else None, 'severity': a.get('severity') or None,
                        'in_kev': a.get('in_kev') == '1', 'kev_due': a.get('kev_due') or None,
                        'published_at': a.get('published_at') or None, 'fixed_in': fixed,
                        'sources': sorted({r['origin'] for r in aff if r.get('origin')}), 'status': st})
        return out


def backport_fixed(rt):
    return [c['adv_id'] for c in ((rt.get('backport') or {}).get('cves') or [])
            if c.get('state') in ('FIXED', 'NOT_AFFECTED')]


def current(ev, rt, lang='en'):
    product, version = rt['kind'], rt.get('version') or ''
    status = rt.get('lifecycle_status') if rt.get('lifecycle_status') in ('PRE_RELEASE', 'UNKNOWN') else None
    fixed = backport_fixed(rt)
    q = ev.version(product, version, exclude=fixed, status=status)
    e = q['exposure']
    cur = {'version': version, 'version_raw': rt.get('version_raw'), 'branch': q['branch'],
           'cve_counts': {'critical': e['n_crit'], 'high': e['n_high'], 'medium': e['n_med'], 'low': e['n_low']},
           'kev_count': e['n_kev'], 'lifecycle_status': q['lifecycle_status'], 'is_lts': q['is_lts'],
           'eol_date': q['eol_date'], 'days_to_eol': q['days_to_eol'], 'latest_patch': q['latest'],
           'min_patched': q['min_patched'], 'priority': q['priority'], 'risk': q['risk'],
           'not_assessed_label': EOL_LABEL.get(lang, EOL_LABEL['en']) if q['lifecycle_status'] == 'EOL' else None}
    advs = ev.advisories(e.get('adv_ids') or [], fixed, q['branch'], product)
    return cur, advs, q


# --- candidates ------------------------------------------------------------------
def branch_table(ev, product):
    out = []
    for lc in ev.b.tsv('lifecycle.tsv'):
        if lc['product'] != product:
            continue
        b = lc['branch']
        mp = ev.b.min_patched(product, b) or {}
        latest = mp.get('latest') or V.vmax(r['version'] for r in ev.b.releases(product, b)) or lc.get('latest_hint')
        if not latest:
            continue
        st = R.lifecycle_status(product, lc, latest, ev.today)
        out.append({'branch': b, 'latest': latest, 'status': st, 'lc': lc})
    out.sort(key=lambda r: V.vkey(r['branch']))
    return out


def framework_limits(cat, doc, runtime_id):
    """(php_min, php_max, component) of frameworks found on the sites of the runtime (BR-SCN-005 d)."""
    if cat is None:
        return []
    rows = cat.framework_rows()
    roots = [s.get('docroot') for s in sites_of(doc, runtime_id) if s.get('docroot')]
    out = []
    for w in (doc or {}).get('result', {}).get('wordpress_findings') or []:
        d, ver = w.get('site_dir') or '', w.get('version') or ''
        if not ver or not any(d == r or d.startswith(r.rstrip('/') + '/') or r.startswith(d.rstrip('/') + '/')
                              for r in roots):
            continue
        mm = '.'.join(ver.split('.')[:2])
        for r in rows:
            if r['framework'] == 'WordPress' and mm in [x.strip() for x in re.split(r'[,/]', r['versions'])]:
                out.append((r['php_min'] or None, r['php_max'] or None, 'WordPress %s' % ver))
    return out


def fits(branch, limits):
    for lo, hi, _ in limits:
        if lo and V.vlt(branch, '.'.join(lo.split('.')[:2])):
            return False
        if hi and V.vlt(hi, branch):
            return False
    return True


def candidates(ev, cat, rt, doc, cur_q, expired=False, warnings=None, production=True):
    """FR-ASMT-CAND-001 + BR-ASMT-001/002, BR-SCN-005/006/007. Returns (list, errors)."""
    warnings = [] if warnings is None else warnings
    errs = []
    product = rt['kind']
    if cur_q['lifecycle_status'] == 'UNKNOWN':
        return [], errs        # SCN-PHP-005 / SCN-NODE-008: no automatic proposal
    today = ev.today
    th = (cat.meta.get('thresholds') if cat else None) or {}
    min_eol = add_days(today, th.get('target_eol_min_days', 365))
    manual_eol = add_days(today, 90)
    table = branch_table(ev, product)
    cur_b = cur_q['branch']
    types = {}

    def tag(row, t):
        types.setdefault(row['branch'], []).append(t)

    same = next((r for r in table if r['branch'] == cur_b), None)
    if same and same['status'] not in CLOSED and V.vlt(rt.get('version') or '0', same['latest']):
        tag(same, 'SAME_BRANCH_LATEST')
    higher = [r for r in table if V.vlt(cur_b, r['branch'])]
    limits = framework_limits(cat, doc, rt['runtime_id']) if product == 'php' else []
    if product == 'php':
        nxt = next((r for r in higher if r['status'] in SUPPORTED_PHP), None)
        ga_cut = add_days(today, -th.get('php_target_ga_age_days', 90))
        good = [r for r in table if r['lc'].get('ga_date') and r['lc']['ga_date'] <= ga_cut
                and r['lc'].get('eol_date') and r['lc']['eol_date'] >= min_eol and fits(r['branch'], limits)]
        rec = next((r for r in reversed(good) if r['status'] == 'ACTIVE'), None) or \
            next((r for r in reversed(good) if r['status'] == 'SECURITY_ONLY'), None)
        stable = next((r for r in reversed(table) if r['status'] in SUPPORTED_PHP), None)
    else:
        even = [r for r in table if r['branch'].isdigit() and int(r['branch']) % 2 == 0]
        nxt = next((r for r in even if V.vlt(cur_b, r['branch']) and r['status'] in LTS_NODE), None)
        lts_cut = add_days(today, th.get('node_lts_within_days', 14))
        good = [r for r in even if r['lc'].get('lts_start') and r['lc']['lts_start'] <= lts_cut
                and r['lc'].get('eol_date') and r['lc']['eol_date'] >= min_eol and r['status'] not in CLOSED]
        rec = good[-1] if good else next((r for r in reversed(even) if r['status'] in LTS_NODE
                                           and r['lc'].get('eol_date', '') >= min_eol), None)
        stable = next((r for r in reversed(even) if r['status'] not in CLOSED), None)
    if nxt:
        tag(nxt, 'NEXT_SUPPORTED')
    if rec:
        tag(rec, 'RECOMMENDED')
    elif higher or same:
        comp = limits[0][2] if limits else ('PHP' if product == 'php' else 'Node.js')
        errs.append(('ERR-SCN-409-01', errors.message('ERR-SCN-409-01', component=comp, version=cur_b)))
    if stable:
        tag(stable, 'LATEST_STABLE')
    pre = [r for r in table if r['status'] == 'PRE_RELEASE' and V.vlt(cur_b, r['branch'])]
    out = []
    for r in table:
        t = types.get(r['branch'])
        if t is None and r not in pre:
            continue
        lc = r['lc']
        eol = lc.get('eol_date')
        c = {'version': r['latest'], 'branch': r['branch'], 'types': t or [], 'lifecycle_status': r['status'],
             'is_lts': bool(lc.get('lts_start')) if product == 'node' else None, 'eol_date': eol or None,
             'selectable': True, 'not_selectable_reason': None, 'manual_with_reason': False}
        same_b = r['branch'] == cur_b
        if r['status'] in CLOSED:
            c['selectable'], c['not_selectable_reason'] = False, 'branch is %s (BR-UPG-004)' % r['status']
        elif same_b:
            pass
        elif expired:
            c['selectable'], c['not_selectable_reason'] = False, 'lifecycle data older than 90 days (ERR-SCN-503-01)'
        elif product == 'node' and r['status'] == 'CURRENT' and production:
            c['selectable'] = False
            c['not_selectable_reason'] = 'CURRENT until its LTS date %s; not for production (BR-SCN-007)' % (
                lc.get('lts_start') or '-')
        elif not eol or eol < min_eol:
            c['selectable'] = False
            c['not_selectable_reason'] = 'EOL %s is before %s (BR-ASMT-002)' % (eol or '-', min_eol)
            c['manual_with_reason'] = bool(eol and eol >= manual_eol)
        if c['selectable'] and limits and not same_b and not fits(r['branch'], limits):
            c['selectable'] = False
            c['not_selectable_reason'] = 'outside the PHP range of %s' % ', '.join(x[2] for x in limits)
        out.append(c)
    return out, errs


# --- installability (FR-ASMT-CAND-002) -------------------------------------------
def _apt_candidate(pkg):
    try:
        p = subprocess.run(['apt-cache', 'policy', pkg], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r'Candidate:\s*(\S+)', p.stdout.decode('utf-8', 'replace'))
    if p.returncode != 0:
        return None
    return m.group(1) if m and m.group(1) != '(none)' else ''


def installable(rt, cand, env, offline=False):
    product, src, pb = rt['kind'], rt.get('install_source'), (env or {}).get('pb_provider')
    same = cand['branch'] == (rt.get('branch') or '')
    if product == 'node':
        if src == 'nvm':
            return 'yes', 'nvm'
        if src in ('tarball', 'package', 'nodesource'):
            return 'yes', 'tarball:nodejs.org'     # BR-SCN-026: a new line installs from the official tarball
        if src == 'docker':
            return ('unknown', 'docker:node:%s' % cand['branch']) if offline else ('yes', 'docker:node:%s' % cand['branch'])
        return 'unknown', None
    if same and src == 'package':
        return 'yes', 'package'
    if pb == 'PB-001':
        got = _apt_candidate('php%s-fpm' % cand['branch'])
        if got is None:
            return 'unknown', None
        if got:
            return 'yes', 'package'
        os_id = (env or {}).get('os_id') or ''
        return 'needs_repo', 'repo:ppa:ondrej/php' if os_id == 'ubuntu' else 'repo:packages.sury.org/php'
    if pb == 'PB-013' or src == 'docker':
        return ('unknown', 'docker:php:%s-fpm' % cand['branch']) if offline else ('yes', 'docker:php:%s-fpm' % cand['branch'])
    return 'unknown', None      # commands of the other playbooks are not verified (BR-ENV-010)


# --- the command -------------------------------------------------------------------
def evaluate(state_dir, rt, doc, today, want_candidates, offline, env_out, lang='en'):
    """qp.assess/1 result. ENV_OUT: Envelope (data, catalog_version, errors, warnings)."""
    warnings = []
    cat = qcatalog.select(state_dir, warnings)
    for code, msg in warnings:
        env_out.error(code, msg, 'host')
    env_out.catalog_version = cat.version if cat else None
    fs = FeedsDir(state_dir)
    try:
        b = Bundle(fs)
    except LookupError:
        raise errors.error('ERR-FEED-503-01', 'No bundle: run feeds update or import a snapshot.', source='feeds',
                           origin='-', age_h='-')
    with b:
        level, age, stale, _ = b.freshness()
        env_out.data = {'bundle_id': b.bundle_id, 'freshness': level, 'data_age_h': age, 'stale_sources': stale}
        expired = level == 'EXPIRED'
        if level == 'STALE':
            env_out.warning('ERR-FEED-412-01', errors.message('ERR-FEED-412-01', age_d=(age or 0) // 24,
                                                              sources=','.join(s['src_id'] for s in stale)))
        if expired:
            env_out.error('ERR-SCN-503-01', errors.message('ERR-SCN-503-01', days=(age or 0) // 24))
        ev = Evaluator(b, today)
        cur, advs, cur_q = current(ev, rt, lang)
        res = {'runtime_id': rt['runtime_id'], 'evaluated_on': today, 'bundle_id': b.bundle_id,
               'catalog_version': cat.version if cat else None, 'scenario_ids': rt.get('scenario_ids') or [],
               'locked': bool(rt.get('locked')), 'current': cur, 'advisories': advs, 'candidates': [],
               'comparison': {'rows': []}}
        if rt.get('locked'):
            env_out.warning('ERR-SCN-422-01', errors.message('ERR-SCN-422-01', runtime=rt['kind'],
                                                             raw=rt.get('version_raw') or ''))
        if not want_candidates:
            return res, cat
        cands, errs = candidates(ev, cat, rt, doc, cur_q, expired=expired)
        for code, msg in errs:
            env_out.error(code, msg)
        envj = (doc or {}).get('result', {}).get('environment') or {}
        rows = [_row(cur_q, rt.get('version') or '', cur['risk']['R'], cur['risk']['R'], cur_q['branch'], rt['kind'])]
        for c in cands:
            c['installable'], c['install_source'] = installable(rt, c, envj, offline)
            q = ev.version(rt['kind'], c['version'])
            c['risk'] = q['risk']
            rows.append(_row(q, c['version'], q['risk']['R'], cur['risk']['R'], cur_q['branch'], rt['kind']))
        res['candidates'] = cands
        res['comparison'] = {'rows': rows, 'bundle_id': b.bundle_id, 'data_age_h': age,
                             'catalog_version': cat.version if cat else None, 'evaluated_on': today}
        return res, cat


def _row(q, version, r, r_cur, cur_branch, product):
    e = q['exposure']
    return {'version': version, 'cve_counts': {'critical': e['n_crit'], 'high': e['n_high'], 'medium': e['n_med'],
                                               'low': e['n_low']},
            'kev_count': e['n_kev'], 'lifecycle_status': q['lifecycle_status'], 'is_lts': q.get('is_lts'),
            'eol_date': q['eol_date'], 'days_to_eol': q['days_to_eol'],
            'major_gap': (V.vkey(version) or (0,))[0] - (V.vkey(cur_branch) or (0,))[0],
            'compat_errors': None, 'compat_warnings': None, 'R': r, 'delta_R': r - r_cur}


def run(env, argv, Args, warnings, state_dir):
    a = Args(argv, flags=('--candidates', '--offline', '--json'), options=('--runtime-id', '--bin', '--today'))
    rid, binp = a.opts.get('--runtime-id'), a.opts.get('--bin')
    if bool(rid) == bool(binp) or a.positional:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--runtime-id/--bin')
    today = today_of(a)
    offline = '--offline' in a.flags
    want = (lambda d: find_runtime(d, rid, binp) is not None)
    doc = scan_for(state_dir, offline, want)
    rt = find_runtime(doc, rid, binp)
    if rt is None:
        msg = errors.message('ERR-ASMT-404-01', runtime_id=rid or binp)
        raise errors.QPError('ERR-ASMT-404-01', msg, exit_code=2)
    lang = 'vi' if os.environ.get('QP_LANG') == 'vi' else 'en'
    res, _ = evaluate(state_dir, rt, doc, today, '--candidates' in a.flags, offline, env, lang)
    if '--json' not in a.flags:
        print_text(rt, res)
    return 0, res


def print_text(rt, res):
    c = res['current']
    print('%s %s (%s): %s, EOL %s (%s days), R=%d %s' % (rt['kind'], c['version'], rt['bin'], c['lifecycle_status'],
                                                       c['eol_date'] or '-', c['days_to_eol'], c['risk']['R'],
                                                       c['risk']['level']))
    print('  CVE: critical %(critical)d, high %(high)d, medium %(medium)d, low %(low)d' % c['cve_counts']
          + ', KEV %d' % c['kev_count'])
    if c['not_assessed_label']:
        print('  ' + c['not_assessed_label'])
    for cand in res['candidates']:
        print('  %-10s %-6s %-26s %-16s EOL %-10s %s%s' % (
            cand['version'], cand['branch'], ','.join(cand['types']) or '-', cand['lifecycle_status'],
            cand['eol_date'] or '-', 'selectable' if cand['selectable'] else 'not selectable',
            ' (%s)' % cand['not_selectable_reason'] if cand['not_selectable_reason'] else ''))
    for row in res['comparison']['rows']:
        print('  compare %-10s R=%-3d dR=%d' % (row['version'], row['R'], row['delta_R']))
