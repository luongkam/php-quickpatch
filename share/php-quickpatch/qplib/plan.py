"""`plan` (FR-CLI-CMD-002, FR-PLAN-*, FR-SCN-CHK-001).

Plans live in STATE_DIR/plans/<plan_id>/{plan.json, items.json, events.jsonl},
written to a temp file + rename under plans/.lock. State machines:
DOC-SRS-QP-STATE-001 T-PLN-01..13 (plan) and T-CHK-01..16 (checklist item).
"""
import fcntl
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

from . import assess as A, audit, catalog as qcatalog, errors
from .envelope import iso_ms
from .feeds import risk as R, versions as V
from .feeds.query import Bundle
from .feeds.store import FeedsDir

PLAN_ID_RE = re.compile(r'^PLN-\d{8}-\d{6}-[0-9a-f]{4}$')
HIT_RE = re.compile(r'^H-[0-9a-f]{12}$')
CTRL_RE = re.compile(r'[\x00-\x1f\x7f]')
TERMINAL = ('completed', 'rolled_back', 'cancelled')
CLOSED_ITEM = ('DONE', 'SKIPPED', 'WAIVED')
PHASES = ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')
READ_ACTIONS = ('scan', 'assess')
WRITE_ACTIONS = ('fix',)


def actor():
    return os.environ.get('QP_ACTOR') or 'cli:%s' % audit._user()


def reason_ok(text, minimum):
    """--reason 20-500 / --evidence 10-500 characters, no control characters (FR-CLI-CMD-002)."""
    if text is None or len(text.strip()) < minimum or len(text) > 500 or CTRL_RE.search(text):
        raise errors.error('ERR-PLAN-422-01', min=minimum, details={'min': minimum, 'max': 500})
    return text.strip()


def not_allowed(action, status):
    return errors.error('ERR-PLAN-409-02', action=action, status=status, details={'action': action, 'status': status})


# --- storage ------------------------------------------------------------------
class Store(object):
    def __init__(self, state_dir):
        self.root = os.path.join(state_dir, 'plans')
        self.state_dir = state_dir
        if not os.path.isdir(self.root):
            os.makedirs(self.root, 0o700)
        self._lock_fd = None

    def __enter__(self):
        self._lock_fd = os.open(os.path.join(self.root, '.lock'), os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        deadline = time.time() + 10
        while True:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() > deadline:
                    os.close(self._lock_fd)
                    raise errors.error('ERR-CLI-423-01')
                time.sleep(0.1)

    def __exit__(self, *exc):
        os.close(self._lock_fd)

    def dir(self, plan_id):
        return os.path.join(self.root, plan_id)

    def ids(self):
        return sorted(os.path.basename(p) for p in glob.glob(os.path.join(self.root, 'PLN-*'))
                      if PLAN_ID_RE.match(os.path.basename(p)))

    def load(self, plan_id):
        if not PLAN_ID_RE.match(plan_id or '') or not os.path.isfile(os.path.join(self.dir(plan_id), 'plan.json')):
            raise errors.error('ERR-PLAN-404-01', id=plan_id)
        with open(os.path.join(self.dir(plan_id), 'plan.json'), encoding='utf-8') as f:
            plan = json.load(f)
        with open(os.path.join(self.dir(plan_id), 'items.json'), encoding='utf-8') as f:
            items = json.load(f)['items']
        return plan, items

    def _write(self, path, obj):
        tmp = '%s.tmp-%d' % (path, os.getpid())
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def save(self, plan, items=None):
        d = self.dir(plan['plan_id'])
        if not os.path.isdir(d):
            os.mkdir(d, 0o700)
        plan['updated_at'] = iso_ms()
        if items is not None:
            self._write(os.path.join(d, 'items.json'), {'plan_id': plan['plan_id'], 'items': items})
        self._write(os.path.join(d, 'plan.json'), plan)

    def event(self, plan_id, kind, **kw):
        rec = dict(ts=iso_ms(), event=kind, actor=actor(), **kw)
        with open(os.path.join(self.dir(plan_id), 'events.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + '\n')


# --- checklist assembly (FR-SCN-CHK-001) ------------------------------------------
def site_facts(site, scan):
    """framework / composer / sapi / phpunit of one site: True/False, or None when unknown."""
    root = site.get('docroot') or ''
    known = bool(root) and os.path.isdir(root)
    wp = known and os.path.isfile(os.path.join(root, 'wp-includes', 'version.php'))
    for w in scan.get('result', {}).get('wordpress_findings') or []:
        if root and (w.get('site_dir') or '').rstrip('/') == root.rstrip('/'):
            wp = True
    return {
        'framework': 'wordpress' if wp else None,
        'not_wordpress': (not wp) if known else None,
        'composer': os.path.isfile(os.path.join(root, 'composer.json')) if known else None,
        'phpunit': bool(glob.glob(os.path.join(root, 'phpunit.xml*'))) if known else None,
        'sapi': 'mod_php' if site.get('binding_kind') == 'apache_mod_php' else 'fpm',
        'loader': None,
    }


def clause(key, op, val, facts, ctx):
    """True / False / None (not decided) for one applies_when clause."""
    if key == 'mode':
        return (ctx['mode'] == val) == (op == '=')
    if key == 'old_branch':
        return (ctx['old_branch'] == val) == (op == '=')
    if key == 'overlay':
        return (val in ctx['scenario_ids']) == (op == '=')
    if facts is None:
        return None
    if key == 'framework':
        if val == 'wordpress':
            is_wp = True if facts['framework'] == 'wordpress' else (False if facts['not_wordpress'] else None)
            return is_wp if op == '=' or is_wp is None else not is_wp
        if val == 'none':
            has = True if facts['framework'] else None      # other frameworks: detected in M4
            return has if op == '!=' or has is None else not has
        return None
    if key == 'composer':
        return None if facts['composer'] is None else (facts['composer'] == (val == 'true')) == (op == '=')
    if key == 'phpunit':
        return None if facts['phpunit'] is None else (facts['phpunit'] == (val == 'true')) == (op == '=')
    if key == 'sapi':
        return (facts['sapi'] == val) == (op == '=')
    if key == 'loader':
        return None if facts['loader'] is None else (facts['loader'] == val) == (op == '=')
    return None


def applies(expr, facts_list, ctx):
    """applies_when of an item over the facts of its sites: True / False / None."""
    if not expr:
        return True
    res = True
    for part in expr.split(';'):
        m = re.match(r'^([a-z_]+)(!=|=)(.+)$', part)
        if not m:
            return None
        key, op, val = m.groups()
        if key in ('mode', 'old_branch', 'overlay'):
            v = clause(key, op, val, None, ctx)
        else:
            vals = [clause(key, op, val, f, ctx) for f in facts_list] or [False]
            v = True if any(x is True for x in vals) else (False if all(x is False for x in vals) else None)
        if v is False:
            return False
        if v is None:
            res = None
    return res


def per_site(it):
    if (it.get('cli_action') or '').split(' ')[0] in READ_ACTIONS:
        return False
    a = it['action'].lower()
    if it['phase'] in ('P3', 'P4', 'P5'):
        return True
    if it['phase'] == 'P6':
        return not any(w in a for w in ('cron', 'pm2 startup', 'cli/cron'))
    return 'baseline' in a or 'mỗi site' in a


def substitute(text, vars_):
    if not text:
        return text
    for k in sorted(vars_, key=len, reverse=True):
        if vars_[k]:
            text = text.replace('$' + k, vars_[k])
    return text


def env_items(rt, env, runtime_kind):
    """FR-SCN-ENV-001: MANUAL items for the restrictions of the environment."""
    out = []
    pref = 'CHK-%s-000-' % ('PHP' if runtime_kind == 'php' else 'NODE')
    n = 0
    for r in env.get('restrictions') or []:
        n += 1
        out.append({'chk_id': '%s%02d' % (pref, n), 'scenario_id': 'SCN-ENV', 'phase': 'P1',
                    'action': 'Environment limit %s: %s. Do the system-level steps by hand (panel or root).' % (
                        r.get('code'), r.get('message')),
                    'exec_type': 'MANUAL', 'check_mechanism': 'Hosting panel or a root shell',
                    'done_criteria': 'Operator evidence that the runtime-level step was done', 'risk': None,
                    'applies_when': None, 'manual_condition': None, 'optional': False, 'refs': [], 'expand': False,
                    'verified': True, 'cli_action': None, 'flow': 'both'})
    return out


def assemble(cat, rt, sites, mode, target, scan, old_branch):
    """Effective checklist: VERSION + OVERLAY items (OVERLAY first in a phase), playbook/env items."""
    env = scan.get('result', {}).get('environment') or {}
    sids = list(rt.get('scenario_ids') or [])
    scen = cat.scenarios
    sids = [s for s in sids if s in scen]
    order = {s: (0 if scen[s]['kind'] == 'OVERLAY' else 1) for s in sids}
    base = env_items(rt, env, rt['kind'])
    for s in sids:
        base.extend(cat.items_of(s))
    base.sort(key=lambda it: (PHASES.index(it['phase']), order.get(it['scenario_id'], -1), it['chk_id']))
    ctx = {'mode': mode, 'old_branch': old_branch, 'scenario_ids': sids}
    facts = {s['site_id']: site_facts(s, scan) for s in sites}
    target_branch = target['branch']
    nd = lambda b: (b or '').replace('.', '')   # noqa: E731
    out = []
    for it in base:
        expanded = []
        if it.get('expand') and mode == 'cross_branch':
            for n, ref in enumerate(it['refs'], 1):
                t = cat.item(ref)
                if t is None:
                    continue
                sub = dict(t, chk_id='%s-%02d' % (it['chk_id'], n), scenario_id=it['scenario_id'],
                           phase=it['phase'], parent=it['chk_id'], template=ref, flow=it.get('flow'),
                           applies_when=t.get('applies_when'))
                expanded.append(sub)
        for one in (expanded or [it]):
            if one.get('flow') == 'upgrade' and mode == 'same_branch':
                status, reason = 'SKIPPED', 'same_branch plan: step of a branch upgrade'
                targets = [None]
            else:
                status, reason = 'PENDING', None
                targets = [s for s in sites] if per_site(one) else [None]
                if not targets:
                    targets = [None]
            for site in targets:
                st, why = status, reason
                fl = [facts[site['site_id']]] if site else list(facts.values())
                if st == 'PENDING':
                    ok = applies(one.get('applies_when'), fl, ctx)
                    if ok is False:
                        st, why = 'SKIPPED', 'applies_when %s not met' % one['applies_when']
                    elif site is None and per_site(one) and not sites:
                        st, why = 'SKIPPED', 'no site uses this runtime'
                vars_ = {'OLD': old_branch, 'NEW': target_branch, 'OLDND': nd(old_branch), 'NEWND': nd(target_branch),
                         'OLD_BIN': rt.get('bin'), 'RUNTIME_ID': rt['runtime_id'],
                         'SITE': site['site_id'] if site else None, 'VHOST': site['site_id'] if site else None,
                         'OWNER': site.get('owner_user') if site else None, 'DOCROOT': site.get('docroot') if site else None}
                exec_type = one['exec_type']
                if exec_type == 'AUTO' and not one.get('verified', True):
                    exec_type = 'SEMI'                      # BR-ENV-010
                if site and site.get('pb_id') == 'PB-000':
                    exec_type = 'MANUAL'                    # BR-ENV-001: site with no known binding
                key = one['chk_id'] + ('@' + site['site_id'] if site else '')
                out.append({
                    'item_key': key, 'chk_id': one['chk_id'], 'scenario_id': one['scenario_id'],
                    'site_id': site['site_id'] if site else None, 'phase': one['phase'],
                    'action': substitute(one['action'], vars_), 'exec_type': exec_type,
                    'check_mechanism': substitute(one['check_mechanism'], vars_),
                    'done_criteria': substitute(one['done_criteria'], vars_), 'risk': substitute(one.get('risk'), vars_),
                    'applies_when': one.get('applies_when'), 'manual_condition': one.get('manual_condition'),
                    'optional': bool(one.get('optional')), 'depends_on': [], 'status': st, 'blocked_by': [],
                    'cli_action': substitute(one.get('cli_action'), vars_), 'verified': bool(one.get('verified', True)),
                    'job_id': None, 'reason': why, 'evidence': None, 'updated_at': iso_ms(), 'updated_by': 'system',
                    'parent': one.get('parent'), 'template': one.get('template'), 'flow': one.get('flow')})
    # BR-SCN-018: a P5 item of a site waits for the mandatory P3/P4 items of the same site.
    for it in out:
        if it['phase'] == 'P5':
            it['depends_on'] = [o['item_key'] for o in out if o['phase'] in ('P3', 'P4') and not o['optional']
                                and o['site_id'] in (it['site_id'], None) and o['status'] != 'SKIPPED']
    return out


def blocked_by(it, items):
    by_key = {o['item_key']: o for o in items}
    return [k for k in it.get('depends_on') or [] if by_key.get(k, {}).get('status') not in CLOSED_ITEM]


def refresh_blocked(items):
    for it in items:
        it['blocked_by'] = blocked_by(it, items) if it['status'] not in CLOSED_ITEM else []


# --- inputs, stale, deadline, preconditions --------------------------------------------
def target_facts(ev, product, version):
    q = ev.version(product, version)
    kev = sorted(a for a in q['exposure'].get('adv_ids') or [] if _in_kev(ev, a))
    return {'R': q['risk']['R'], 'kev_ids': kev, 'status': q['lifecycle_status']}


def _in_kev(ev, adv_id):
    if not hasattr(ev, '_kev'):
        ev._kev = {r['adv_id'] for r in ev.b.tsv('advisories.tsv') if r.get('in_kev') == '1'}
    return adv_id in ev._kev


def deadline_of(cur, today, status):
    """FR-PLAN-DL-001: EOL - 30 days for SECURITY_ONLY/MAINTENANCE_LTS or <= 90 days to EOL."""
    eol, d = cur.get('eol_date'), cur.get('days_to_eol')
    if not eol or d is None or d < 0:
        return None
    if cur.get('lifecycle_status') not in ('SECURITY_ONLY', 'MAINTENANCE_LTS') and d > 90:
        return None
    date = A.add_days(eol, -30)
    left = R.day_number(date) - R.day_number(today)
    return {'date': date, 'days_left': left,
            'overdue': left < 0 and status not in ('approved', 'in_progress', 'completed'),
            'warn': d <= 90}


def preconditions(rt):
    """BR-SCN-016: >= 2 GB free where the target installs, >= 512 MB RAM available, root."""
    out = []
    path = '/usr' if os.path.isdir('/usr') else '/'
    try:
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize / 1024.0 ** 3
        out.append({'check': 'disk_free_gb', 'required': '>= 2', 'actual': '%.1f' % free, 'pass': free >= 2})
    except OSError:
        out.append({'check': 'disk_free_gb', 'required': '>= 2', 'actual': None, 'pass': False})
    mem = None
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    mem = int(line.split()[1]) // 1024
    except OSError:
        pass
    out.append({'check': 'mem_available_mb', 'required': '>= 512', 'actual': None if mem is None else str(mem),
                'pass': mem is not None and mem >= 512})
    out.append({'check': 'root', 'required': 'EUID 0 or panel API', 'actual': str(os.geteuid()), 'pass': os.geteuid() == 0})
    return out


def check_stale(plan, state_dir, today):
    """BR-PLAN-006 / T-PLN-12. Adds reasons; never clears a stale plan."""
    if plan['status'] in TERMINAL:
        return False
    reasons = set(plan.get('stale_reasons') or [])
    inputs = plan.get('inputs') or {}
    scan = A.read_scan(state_dir)
    if scan and inputs.get('scan_fingerprint') and \
            scan['result'].get('scan_fingerprint') != inputs['scan_fingerprint']:
        reasons.add('SCAN_CHANGED')
    cat = qcatalog.select(state_dir, [])
    if cat and inputs.get('scenario_sums') and cat.scenario_sums(inputs.get('scenario_ids') or []) != inputs['scenario_sums']:
        reasons.add('CATALOG_CHANGED')
    try:
        with Bundle(FeedsDir(state_dir)) as b:
            ev = A.Evaluator(b, today)
            tf = target_facts(ev, plan['runtime_kind'], plan['target']['patch_version'])
    except LookupError:
        tf = None
    if tf:
        if set(tf['kev_ids']) - set(inputs.get('target_kev_ids') or []):
            reasons.add('TARGET_NEW_KEV')
        if inputs.get('target_R') is not None and tf['R'] - inputs['target_R'] >= 20:
            reasons.add('TARGET_RISK_UP_20')
        if tf['status'] == 'EOL':
            reasons.add('TARGET_EOL')
    changed = sorted(reasons) != sorted(plan.get('stale_reasons') or [])
    plan['stale_reasons'] = sorted(reasons)
    plan['stale'] = bool(reasons)
    return changed


# --- views ------------------------------------------------------------------------
def view(plan, items, with_items=True, today=None):
    p = dict(plan)
    p.pop('runtime_kind', None)
    if today and p.get('deadline'):
        d = dict(p['deadline'])
        d['days_left'] = R.day_number(d['date']) - R.day_number(today)
        d['overdue'] = d['days_left'] < 0 and p['status'] not in ('approved', 'in_progress', 'completed')
        p['deadline'] = d
    if with_items:
        refresh_blocked(items)
        p['checklist_items'] = items
        p['counts'] = {s: sum(1 for i in items if i['status'] == s)
                       for s in ('PENDING', 'RUNNING', 'DONE', 'FAILED', 'SKIPPED', 'WAIVED')}
    return p


def summary(plan):
    keys = ('plan_id', 'runtime_id', 'status', 'mode', 'target', 'stale', 'stale_reasons', 'deadline', 'canary_site_id',
            'created_at', 'approved_at', 'updated_at')
    return {k: plan.get(k) for k in keys}


# --- commands -----------------------------------------------------------------------
class Ctx(object):
    def __init__(self, env, state_dir, a, warnings):
        self.env = env
        self.state_dir = state_dir
        self.a = a
        self.warnings = warnings
        self.today = A.today_of(a)


def audited(ctx, action, fn, plan_id=None):
    args = ['plan'] + list(ctx.a.raw)
    try:
        audit.write(ctx.state_dir, 'INTENT', action, args, plan_id=plan_id)
    except OSError as e:
        raise errors.error('ERR-AUD-503-01', 'Audit log unavailable: {detail}', detail=str(e))
    code = 2
    try:
        code, res = fn()
        return code, res
    finally:
        for _ in range(3):
            try:
                seq, h = audit.write(ctx.state_dir, 'RESULT', action, args, result='ok' if code in (0, 1) else 'failed',
                                     exit_code=code, plan_id=plan_id)
                ctx.env.audit_anchor = {'seq': seq, 'hash': h}
                break
            except OSError:
                time.sleep(1)


def new_plan_id():
    return 'PLN-%s-%s' % (time.strftime('%Y%m%d-%H%M%S', time.gmtime()), os.urandom(2).hex())


def cmd_create(ctx):
    a = ctx.a
    rid, tgt = a.opts.get('--runtime-id'), a.opts.get('--target')
    if not rid or not tgt or not re.match(r'^\d+(\.\d+)?$', tgt):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--runtime-id/--target')
    reason = a.opts.get('--reason')
    if reason is not None:
        reason = reason_ok(reason, 20)
    offline = '--offline' in a.flags
    scan = A.scan_for(ctx.state_dir, offline, lambda d: A.find_runtime(d, rid) is not None)
    rt = A.find_runtime(scan, rid)
    if rt is None:
        raise errors.QPError('ERR-ASMT-404-01', errors.message('ERR-ASMT-404-01', runtime_id=rid), exit_code=2)
    sites = A.sites_of(scan, rid)
    if a.opts.get('--sites'):
        want = [s for s in a.opts['--sites'].split(',') if s]
        unknown = [s for s in want if s not in [x['site_id'] for x in sites]]
        if unknown:
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--sites %s' % unknown[0])
        sites = [s for s in sites if s['site_id'] in want]
    res, cat = A.evaluate(ctx.state_dir, rt, scan, ctx.today, True, offline, ctx.env)
    if cat is None:
        raise errors.error('ERR-FEED-502-02', source='catalog', detail='no valid scenario catalog')
    cur = res['current']
    cands = res['candidates']
    cur_branch = cur['branch']
    tgt_branch = tgt if rt['kind'] == 'php' else tgt.split('.')[0]
    cand = next((c for c in cands if c['branch'] == tgt_branch), None)
    mode = 'same_branch' if tgt_branch == cur_branch else 'cross_branch'
    if mode == 'same_branch' and cand is None:
        cand = {'version': cur.get('latest_patch') or rt.get('version'), 'branch': cur_branch,
                'types': ['SAME_BRANCH_LATEST'], 'lifecycle_status': cur['lifecycle_status'], 'selectable':
                cur['lifecycle_status'] not in A.CLOSED, 'not_selectable_reason': None, 'manual_with_reason': False}
    if cand is None:
        with Bundle(FeedsDir(ctx.state_dir)) as b:
            lc = b.lifecycle(rt['kind'], tgt_branch)
            st = R.lifecycle_status(rt['kind'], lc, None, ctx.today) if lc else 'UNKNOWN'
            if st not in A.CLOSED and lc:
                mp = b.min_patched(rt['kind'], tgt_branch) or {}
                cand = {'version': mp.get('latest') or lc.get('latest_hint'), 'branch': tgt_branch, 'types': [],
                        'lifecycle_status': st, 'eol_date': lc.get('eol_date'), 'selectable': False,
                        'not_selectable_reason': 'not a candidate of BR-ASMT-001', 'manual_with_reason': False}
                eol = lc.get('eol_date') or ''
                cand['manual_with_reason'] = bool(eol and eol >= A.add_days(ctx.today, 90))
        if cand is None:
            raise errors.error('ERR-SCN-409-02', target=tgt_branch, status=st, details={'status': st})
    if cand['lifecycle_status'] in A.CLOSED:      # BR-UPG-004, BR-SCN-007
        raise errors.error('ERR-SCN-409-02', target=tgt_branch, status=cand['lifecycle_status'],
                           details={'status': cand['lifecycle_status']})
    if mode == 'cross_branch' and ctx.env.data.get('freshness') == 'EXPIRED':
        raise errors.error('ERR-SCN-503-01', days=(ctx.env.data.get('data_age_h') or 0) // 24)
    override = None
    if mode == 'cross_branch' and 'RECOMMENDED' not in cand['types']:
        if reason is None:
            raise errors.error('ERR-PLAN-422-01', min=20, details={'min': 20, 'why': 'target is not RECOMMENDED'})
        override = reason
    if not cand['selectable']:
        if rt['kind'] == 'node' and cand['lifecycle_status'] == 'CURRENT':
            raise errors.error('ERR-SCN-409-02', target=tgt_branch, status='CURRENT', details={'status': 'CURRENT'})
        if not cand.get('manual_with_reason'):
            raise errors.error('ERR-SCN-409-02', target=tgt_branch, status=cand['lifecycle_status'],
                               details={'status': cand['lifecycle_status'], 'reason': cand.get('not_selectable_reason')})
        if reason is None:
            raise errors.error('ERR-PLAN-422-01', min=20, details={'min': 20, 'why': cand.get('not_selectable_reason')})
        override = reason

    def work():
        with Store(ctx.state_dir) as store:
            olds = []
            for pid in store.ids():
                p, _ = store.load(pid)
                if p['runtime_id'] != rid:
                    continue
                if p['status'] == 'in_progress':
                    raise errors.error('ERR-PLAN-409-01', runtime=rid, plan_id=pid)
                if p['status'] in ('draft', 'approved'):
                    olds.append(p)
            items = assemble(cat, rt, sites, mode, {'branch': tgt_branch}, scan, cur_branch)
            plan_id = new_plan_id()
            # P1 checks answered by this scan/assess (T-CHK-05 with the read actions run now).
            for it in items:
                head = (it.get('cli_action') or '').split(' ')[0]
                if it['status'] == 'PENDING' and it['exec_type'] == 'AUTO' and head in READ_ACTIONS:
                    it['status'] = 'DONE'
                    it['evidence'] = 'scan %s (%s); assess on bundle %s' % (
                        scan['result'].get('scan_fingerprint', '')[:12], scan.get('generated_at'),
                        ctx.env.data.get('bundle_id'))
                    it['updated_by'] = 'system'
            refresh_blocked(items)
            with Bundle(FeedsDir(ctx.state_dir)) as b:
                tf = target_facts(A.Evaluator(b, ctx.today), rt['kind'], cand['version'])
            order = sorted(sites, key=lambda s: (php_files(s.get('docroot')), s['site_id']))
            site_order = [s['site_id'] for s in order]
            plan = {
                'plan_id': plan_id, 'runtime_id': rid, 'status': 'draft', 'mode': mode,
                'target': {'branch': tgt_branch, 'patch_version': cand['version'], 'types': cand['types'],
                           'override_reason': override},
                'stale': False, 'stale_reasons': [],
                'site_order': site_order, 'canary_site_id': site_order[0] if site_order else None, 'blocked_sites': [],
                'upgrade_items': [], 'preconditions': preconditions(rt) if mode == 'cross_branch' else [],
                'compat_verdicts': [{'site_id': s, 'status': 'PENDING', 'errors': 0, 'warnings': 0, 'waived': 0,
                                     'pending_parts': ['code_scan', 'phpcompat', 'lint_new_bin']}
                                    for s in site_order] if mode == 'cross_branch' else [],
                'deadline': deadline_of(cur, ctx.today, 'draft'),
                'inputs': {'bundle_id': ctx.env.data.get('bundle_id'), 'catalog_version': cat.version,
                           'scan_fingerprint': scan['result'].get('scan_fingerprint'),
                           'scenario_ids': rt.get('scenario_ids') or [],
                           'scenario_sums': cat.scenario_sums(rt.get('scenario_ids') or []),
                           'target_R': tf['R'], 'target_kev_ids': tf['kev_ids'], 'evaluated_on': ctx.today},
                'current': {'version': cur['version'], 'branch': cur_branch, 'lifecycle_status': cur['lifecycle_status'],
                            'R': cur['risk']['R']},
                'runtime_kind': rt['kind'], 'locked': bool(rt.get('locked')),
                'created_at': iso_ms(), 'created_by': actor(), 'approved_at': None, 'approved_by': None,
                'started_at': None, 'completed_at': None, 'updated_at': None,
            }
            store.save(plan, items)
            store.event(plan_id, 'created', status='draft', target=plan['target'], mode=mode)
            for p in olds:      # T-PLN-04 / BR-PLAN-002
                p['status'] = 'cancelled'
                p['cancel_reason'] = 'superseded by %s' % plan_id
                store.save(p)
                store.event(p['plan_id'], 'cancelled', reason='superseded', by=plan_id)
                audit.write(ctx.state_dir, 'RESULT', 'plan_cancel', ['plan', 'cancel', p['plan_id'], 'superseded'],
                            result='ok', exit_code=0, plan_id=p['plan_id'])
            return 0, {'plan': view(plan, items)}
    return audited(ctx, 'plan_create', work)


def php_files(root, cap=200000):
    n = 0
    if not root or not os.path.isdir(root):
        return 0
    for _, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
        n += sum(1 for f in files if f.endswith(('.php', '.inc', '.phtml')))
        if n > cap:
            break
    return n


def load_checked(ctx, store, plan_id, save=True):
    plan, items = store.load(plan_id)
    if check_stale(plan, ctx.state_dir, ctx.today) and save:
        store.save(plan)
        store.event(plan_id, 'stale', reasons=plan['stale_reasons'])
    return plan, items


def cmd_list(ctx):
    with Store(ctx.state_dir) as store:
        plans = []
        for pid in store.ids():
            p, _ = store.load(pid)
            plans.append(summary(view(p, [], with_items=False, today=ctx.today)))
    plans.sort(key=lambda p: p.get('created_at') or '', reverse=True)
    return 0, {'plans': plans}


def cmd_show(ctx, plan_id):
    with Store(ctx.state_dir) as store:
        plan, items = load_checked(ctx, store, plan_id)
    return 0, {'plan': view(plan, items, today=ctx.today)}


def cmd_approve(ctx, plan_id):
    def work():
        with Store(ctx.state_dir) as store:
            plan, items = load_checked(ctx, store, plan_id)
            if plan['status'] != 'draft':
                raise not_allowed('approve', plan['status'])
            if plan['stale']:
                raise errors.error('ERR-PLAN-410-01', reasons=','.join(plan['stale_reasons']))
            missing = []
            pend = [v['site_id'] for v in plan.get('compat_verdicts') or [] if v['status'] == 'PENDING'
                    and set(v.get('pending_parts') or []) - {'lint_new_bin'}]
            if pend:
                missing.append('compatibility scan of %d site(s): %s' % (len(pend), ', '.join(pend)))
            p1 = [i['item_key'] for i in items if i['phase'] == 'P1' and i['exec_type'] == 'AUTO'
                  and i['status'] not in CLOSED_ITEM]
            if p1:
                missing.append('P1 AUTO items not done: %s' % ', '.join(p1))
            if plan['mode'] == 'cross_branch' and not plan.get('preconditions'):
                missing.append('preconditions not checked')
            if missing:
                raise errors.error('ERR-PLAN-412-01', missing='; '.join(missing), details={'missing': missing})
            plan['status'] = 'approved'
            plan['approved_at'] = iso_ms()
            plan['approved_by'] = actor()
            if plan.get('deadline'):
                plan['deadline']['overdue'] = False
            store.save(plan)
            store.event(plan_id, 'approved')
            return 0, {'plan': view(plan, items, today=ctx.today)}
    return audited(ctx, 'plan_approve', work, plan_id)


def cmd_cancel(ctx, plan_id):
    def work():
        with Store(ctx.state_dir) as store:
            plan, items = store.load(plan_id)
            if plan['status'] in TERMINAL:
                raise not_allowed('cancel', plan['status'])
            if any(i['status'] == 'RUNNING' and i.get('job_id') for i in items):
                raise not_allowed('cancel', 'running a job')
            plan['status'] = 'cancelled'
            store.save(plan)
            store.event(plan_id, 'cancelled')
            return 0, {'plan': view(plan, items, today=ctx.today)}
    return audited(ctx, 'plan_cancel', work, plan_id)


def maybe_complete(store, plan, items):
    """T-PLN-09: every item DONE/SKIPPED/WAIVED -> completed."""
    if plan['status'] == 'in_progress' and items and all(i['status'] in CLOSED_ITEM for i in items):
        plan['status'] = 'completed'
        plan['completed_at'] = iso_ms()
        store.event(plan['plan_id'], 'completed')
        return True
    return False


def cmd_complete(ctx, plan_id):
    def work():
        with Store(ctx.state_dir) as store:
            plan, items = store.load(plan_id)
            if plan['status'] != 'in_progress' or not all(i['status'] in CLOSED_ITEM for i in items):
                raise not_allowed('complete', plan['status'] if plan['status'] != 'in_progress' else
                                  'in_progress with open items')
            maybe_complete(store, plan, items)
            store.save(plan)
            return 0, {'plan': view(plan, items, today=ctx.today)}
    return audited(ctx, 'plan_complete', work, plan_id)


def switches_rolled_back(state_dir, plan_id):
    path = os.path.join(state_dir, 'switches', 'index.tsv')
    try:
        with open(path, encoding='utf-8') as f:
            return any(plan_id in line and '\tROLLED_BACK' in line for line in f)
    except OSError:
        return False


def cmd_close(ctx, plan_id):
    reason = reason_ok(ctx.a.opts.get('--reason'), 20)

    def work():
        with Store(ctx.state_dir) as store:
            plan, items = store.load(plan_id)
            if plan['status'] != 'in_progress' or not switches_rolled_back(ctx.state_dir, plan_id):
                raise not_allowed('close_rolled_back', plan['status'])
            if any(i['status'] == 'RUNNING' and i.get('job_id') for i in items):
                raise not_allowed('close_rolled_back', 'running a job')
            plan['status'] = 'rolled_back'
            plan['close_reason'] = reason
            store.save(plan)
            store.event(plan_id, 'rolled_back', reason=reason)
            return 0, {'plan': view(plan, items, today=ctx.today)}
    return audited(ctx, 'plan_close_rolled_back', work, plan_id)


def cmd_canary(ctx, plan_id, site_id):
    def work():
        with Store(ctx.state_dir) as store:
            plan, items = store.load(plan_id)
            if plan['status'] not in ('draft', 'approved'):
                raise not_allowed('set canary', plan['status'])
            if site_id not in plan.get('site_order') or len(plan['site_order']) < 2:
                raise not_allowed('set canary %s' % site_id, plan['status'])
            plan['site_order'] = [site_id] + [s for s in plan['site_order'] if s != site_id]
            plan['canary_site_id'] = site_id
            if plan['status'] == 'approved':      # T-PLN-06
                plan['status'] = 'draft'
                plan['approved_at'] = None
                plan['approved_by'] = None
            store.save(plan)
            store.event(plan_id, 'canary', site_id=site_id, status=plan['status'])
            return 0, {'plan': view(plan, items, today=ctx.today)}
    return audited(ctx, 'plan_set_canary', work, plan_id)


def find_item(items, chk, site=None):
    if '@' in chk and site is None:
        chk, site = chk.split('@', 1)
    hits = [i for i in items if i['chk_id'] == chk and (site is None or i['site_id'] == site)]
    if not hits:
        raise errors.error('ERR-PLAN-404-01', id=chk + ('@' + site if site else ''))
    if len(hits) > 1:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.',
                           arg='%s: add --site (one of %s)' % (chk, ', '.join(i['site_id'] or '-' for i in hits)))
    return hits[0]


def deps_ok(it, items):
    pend = blocked_by(it, items)
    if pend:
        raise errors.error('ERR-SCN-424-01', chk_id=it['chk_id'], dep_id=pend[0], details={'blocked_by': pend})


def cmd_item(ctx, plan_id, chk):
    a = ctx.a
    action = a.opts.get('--set')
    if action not in ('start', 'done', 'fail', 'skip', 'waive'):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--set')
    reason, evidence = a.opts.get('--reason'), a.opts.get('--evidence')
    if action == 'waive':
        reason = reason_ok(reason, 20)
    elif reason is not None:
        reason = reason_ok(reason, 20)
    if action == 'done':
        evidence = reason_ok(evidence, 10)
    elif evidence is not None:
        evidence = reason_ok(evidence, 10)

    def work():
        with Store(ctx.state_dir) as store:
            plan, items = load_checked(ctx, store, plan_id)
            it = find_item(items, chk, a.opts.get('--site'))
            if plan['status'] in TERMINAL or it['status'] in CLOSED_ITEM:      # T-CHK-16
                raise not_allowed('%s %s' % (action, it['item_key']), plan['status'] if plan['status'] in TERMINAL
                                  else it['status'])
            src = it['status']
            if action == 'start':                       # T-CHK-10
                if it['exec_type'] != 'MANUAL' or src != 'PENDING':
                    raise not_allowed('start %s' % it['item_key'], src)
                deps_ok(it, items)
                new = 'RUNNING'
            elif action == 'done':                      # T-CHK-09
                if it['exec_type'] != 'MANUAL' or src not in ('PENDING', 'RUNNING'):
                    raise not_allowed('done %s (%s item: use plan run)' % (it['item_key'], it['exec_type']), src)
                deps_ok(it, items)
                if it['phase'] == 'P5' and plan['stale']:
                    raise errors.error('ERR-PLAN-410-01', reasons=','.join(plan['stale_reasons']))
                new = 'DONE'
            elif action == 'fail':                      # T-CHK-11
                if it['exec_type'] != 'MANUAL' or src not in ('PENDING', 'RUNNING'):
                    raise not_allowed('fail %s' % it['item_key'], src)
                new = 'FAILED'
            elif action == 'skip':                      # T-CHK-15
                site = next((s for s in (A.read_scan(ctx.state_dir) or {}).get('result', {}).get('sites') or []
                             if s['site_id'] == it['site_id']), None)
                ok = applies(it.get('applies_when'), [site_facts(site, A.read_scan(ctx.state_dir) or {})] if site else [],
                             {'mode': plan['mode'], 'old_branch': plan['current']['branch'],
                              'scenario_ids': plan['inputs'].get('scenario_ids') or []})
                if src != 'PENDING' or ok is not False:
                    raise not_allowed('skip %s (applies_when holds or is unknown: use waive)' % it['item_key'], src)
                new = 'SKIPPED'
            else:                                       # T-CHK-14
                if src not in ('PENDING', 'FAILED'):
                    raise not_allowed('waive %s' % it['item_key'], src)
                new = 'WAIVED'
            it['status'] = new
            it['reason'] = reason or it.get('reason')
            if evidence:
                it['evidence'] = evidence
            it['updated_at'] = iso_ms()
            it['updated_by'] = actor()
            maybe_complete(store, plan, items)
            refresh_blocked(items)
            store.save(plan, items)
            store.event(plan_id, 'item', item=it['item_key'], **{'from': src, 'to': new, 'reason': reason,
                                                                  'evidence': evidence})
            return 0, {'plan_id': plan_id, 'item': it}
    return audited(ctx, 'plan_item_set', work, plan_id)


def cmd_waive(ctx, plan_id):
    a = ctx.a
    site = a.opts.get('--site')
    hits = [h for h in (a.opts.get('--hits') or '').split(',') if h]
    reason_ok(a.opts.get('--reason'), 20)
    if not site or not hits or len(hits) > 200 or any(not HIT_RE.match(h) for h in hits):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--site/--hits')

    def work():
        with Store(ctx.state_dir) as store:
            plan, _ = store.load(plan_id)
            known = set()
            for v in plan.get('compat_verdicts') or []:
                if v['site_id'] == site:
                    known.update(h.get('hit_id') for h in v.get('hits') or [])
            missing = [h for h in hits if h not in known]
            if missing:
                raise errors.error('ERR-PLAN-404-01', id=missing[0])
            return 0, {'plan': view(plan, [], with_items=False)}
    return audited(ctx, 'plan_waive_hits', work, plan_id)


def cmd_run(ctx, plan_id, chk):
    a = ctx.a
    dry = '--dry-run' in a.flags
    with Store(ctx.state_dir) as store:
        plan, items = load_checked(ctx, store, plan_id)
        it = find_item(items, chk, a.opts.get('--site'))
    head = (it.get('cli_action') or '').split(' ')[0]
    if plan['status'] in TERMINAL:
        raise not_allowed('run %s' % it['item_key'], plan['status'])
    if it['status'] not in ('PENDING', 'FAILED'):                # T-CHK-03 / T-CHK-12
        raise not_allowed('run %s' % it['item_key'], it['status'])
    deps_ok(it, items)                                            # T-CHK-04: ERR-SCN-424-01
    if it['phase'] == 'P5' and plan['stale']:
        raise errors.error('ERR-PLAN-410-01', reasons=','.join(plan['stale_reasons']))
    if it['exec_type'] == 'MANUAL' or not it.get('cli_action') or head not in READ_ACTIONS + WRITE_ACTIONS:
        raise not_allowed('run %s (no CLI action in this build)' % it['item_key'], it['status'])
    if it['exec_type'] == 'AUTO' and not it.get('verified', True):
        raise not_allowed('run %s (command not verified, BR-ENV-010)' % it['item_key'], it['status'])
    write = head in WRITE_ACTIONS
    if write and plan['status'] not in ('approved', 'in_progress'):
        raise not_allowed('run %s' % it['item_key'], plan['status'])
    if write and plan.get('locked'):
        raise errors.error('ERR-SCN-422-01', runtime=plan['runtime_id'], raw=plan['current']['version'])
    if write and not dry and '--yes' not in a.flags and not sys.stdin.isatty():
        raise errors.error('ERR-CLI-428-01', command='plan run')
    args = it['cli_action'].split() + ['--json']
    if write and dry:
        args.append('--dry-run')
    if '--offline' in a.flags:
        args.append('--offline')

    def execute():
        script = os.environ.get('QP_SCRIPT') or ''
        try:
            p = subprocess.run(['bash', script] + args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3600)
            child = json.loads(p.stdout.decode('utf-8'))
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            return 2, {'schema': None, 'result': None, 'error': str(e)}
        return child.get('exit_code', p.returncode), child

    if write and dry:
        code, child = execute()
        res = {'plan_id': plan_id, 'item': it, 'run': {'action': it['cli_action'], 'child_schema': child.get('schema'),
                                                     'child_exit_code': code, 'child_result': child.get('result')}}
        if isinstance(child.get('result'), dict):
            res['preview'] = child['result'].get('preview')
            res['fingerprint'] = child['result'].get('fingerprint')
        return 0, res

    def work():
        code, child = execute()
        ok = code == 0 or (code == 1 and _runtime_ok(child, plan['runtime_id']))
        with Store(ctx.state_dir) as store:
            plan2, items2 = store.load(plan_id)
            it2 = find_item(items2, it['item_key'])
            src = it2['status']
            it2['status'] = 'DONE' if ok else 'FAILED'
            it2['job_id'] = os.environ.get('QP_JOB_ID') or None
            it2['evidence'] = '%s exit %s (%s)' % (it['cli_action'], code, child.get('generated_at'))
            it2['updated_at'] = iso_ms()
            it2['updated_by'] = actor()
            if write and plan2['status'] == 'approved':          # T-PLN-07
                plan2['status'] = 'in_progress'
                plan2['started_at'] = iso_ms()
                store.event(plan_id, 'in_progress')
            maybe_complete(store, plan2, items2)
            refresh_blocked(items2)
            store.save(plan2, items2)
            store.event(plan_id, 'run', item=it2['item_key'], action=it['cli_action'], exit_code=code,
                        **{'from': src, 'to': it2['status']})
            return (0 if ok else 1), {'plan_id': plan_id, 'item': it2,
                                      'run': {'action': it['cli_action'], 'child_schema': child.get('schema'),
                                              'child_exit_code': code, 'child_result': child.get('result')}}
    return audited(ctx, 'plan_run_item', work, plan_id)


def _runtime_ok(child, runtime_id):
    """Exit 1 of the child concerns other objects when nothing failed for this runtime (T-CHK-06)."""
    res = child.get('result') or {}
    for r in res.get('runtimes_after') or []:
        if r.get('runtime_id') == runtime_id:
            return r.get('state_after') in ('ok', 'ok-backport')
    for r in res.get('runtimes') or []:
        if r.get('runtime_id') == runtime_id:
            return r.get('state') in ('ok', 'ok-backport')
    ref = 'runtime:' + runtime_id
    if 'actions' in res:
        return not any(a.get('object_ref') == ref and a.get('status') == 'failed' for a in res['actions'])
    return False


SUBCOMMANDS = ('create', 'list', 'show', 'approve', 'item', 'run', 'cancel', 'complete', 'close', 'canary', 'waive')


def run(env, argv, Args, warnings, state_dir):
    sub = argv[0] if argv else ''
    env.subcommand = sub or None
    if sub not in SUBCOMMANDS:
        raise errors.error('ERR-CLI-400-01', arg='plan %s' % sub)
    a = Args(argv[1:], flags=('--json', '--dry-run', '--yes', '--offline'),
             options=('--runtime-id', '--target', '--sites', '--reason', '--set', '--evidence', '--site', '--hits',
                      '--today'))
    ctx = Ctx(env, state_dir, a, warnings)
    pos = a.positional
    need = {'create': 0, 'list': 0, 'show': 1, 'approve': 1, 'cancel': 1, 'complete': 1, 'close': 1, 'canary': 2,
            'item': 2, 'run': 2, 'waive': 1}[sub]
    if len(pos) != need:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='plan %s arguments' % sub)
    cat = qcatalog.select(state_dir, [])
    env.catalog_version = cat.version if cat else None
    if sub == 'create':
        code, res = cmd_create(ctx)
    elif sub == 'list':
        code, res = cmd_list(ctx)
    elif sub == 'show':
        code, res = cmd_show(ctx, pos[0])
    elif sub == 'approve':
        code, res = cmd_approve(ctx, pos[0])
    elif sub == 'cancel':
        code, res = cmd_cancel(ctx, pos[0])
    elif sub == 'complete':
        code, res = cmd_complete(ctx, pos[0])
    elif sub == 'close':
        code, res = cmd_close(ctx, pos[0])
    elif sub == 'canary':
        code, res = cmd_canary(ctx, pos[0], pos[1])
    elif sub == 'item':
        code, res = cmd_item(ctx, pos[0], pos[1])
    elif sub == 'waive':
        code, res = cmd_waive(ctx, pos[0])
    else:
        code, res = cmd_run(ctx, pos[0], pos[1])
    if '--json' not in a.flags:
        print_text(sub, res)
    return code, res


def print_text(sub, res):
    if sub == 'list':
        for p in res['plans']:
            print('%s %-12s %-11s %-6s -> %-8s %s' % (p['plan_id'], p['status'], p['mode'], p['runtime_id'],
                                                     (p['target'] or {}).get('patch_version'),
                                                     'STALE ' + ','.join(p['stale_reasons']) if p['stale'] else ''))
        print('%d plan(s)' % len(res['plans']))
        return
    if 'plan' in res:
        p = res['plan']
        print('%s %s (%s) %s -> %s %s' % (p['plan_id'], p['status'], p['mode'], p['runtime_id'],
                                          p['target']['patch_version'],
                                          'STALE ' + ','.join(p['stale_reasons']) if p.get('stale') else ''))
        if p.get('deadline'):
            print('  approve by %(date)s (%(days_left)d days left)' % p['deadline'])
        for it in p.get('checklist_items') or []:
            print('  %-8s %-24s %-2s %-6s %s' % (it['status'], it['item_key'], it['phase'], it['exec_type'],
                                                 it['action'][:80]))
        return
    it = res.get('item') or {}
    print('%s %s: %s' % (res.get('plan_id'), it.get('item_key'), it.get('status')))
    if res.get('run'):
        print('  %s -> exit %s' % (res['run']['action'], res['run'].get('child_exit_code')))
