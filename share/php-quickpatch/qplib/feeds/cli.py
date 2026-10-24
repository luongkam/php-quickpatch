"""`feeds` subcommands (DOC-SRS-QP-FEED-003 §6, FR-FEED-CMD-001..006)."""
import hashlib
import json
import os
import re
import shutil
import sys
import time

from .. import audit, errors, statedir
from . import bundle, schedule, snapshot, sources, status as fstatus, sync
from .store import FeedsDir, parse_iso

SUBCOMMANDS = ('update', 'status', 'verify', 'export', 'import', 'schedule')
EXIT_BY_FRESHNESS = {'FRESH': 0, 'AGING': 0, 'STALE': 1, 'EXPIRED': 2, None: 2}


def say(quiet, text=''):
    if not quiet:
        print(text)


def fill_data(env, fs, now=None):
    """Envelope `data` (FR-FEED-AGE-001) from the current bundle."""
    cur = bundle.current(fs)
    if not cur:
        return None
    try:
        m = cur['manifest']
        level, age, stale, _ = fstatus.freshness(m.get('sources', []), now)
        env.data = {'bundle_id': m['bundle_id'], 'freshness': level, 'data_age_h': age,
                    'stale_sources': stale}
        return m
    finally:
        cur['release']()


def confirm(command, a):
    """FR-CLI-SAFE-001 / BR-CLI-003 for Python write commands."""
    if '--dry-run' in a.flags or '--yes' in a.flags:
        return True
    if sys.stdin.isatty():
        try:
            with open('/dev/tty') as tty:
                sys.stderr.write('%s: apply these changes? [y/N] ' % command)
                sys.stderr.flush()
                ans = tty.readline().strip()
        except OSError:
            ans = ''
        if ans[:1] in ('y', 'Y'):
            return True
        print('Nothing was changed.')
        return False
    raise errors.error('ERR-CLI-428-01', '{command} needs --yes when not interactive.', command=command)


def audit_pair(state_dir, action, args, fn):
    """INTENT before the change, RESULT after (BR-AUD-004). Returns fn()'s (code, result)."""
    try:
        audit.write(state_dir, 'INTENT', action, args)
    except OSError as e:
        raise errors.error('ERR-AUD-503-01', 'Audit log unavailable: {detail}', detail=str(e))
    code, result = 2, None
    try:
        code, result = fn()
        return code, result
    finally:
        for _ in range(3):
            try:
                seq, h = audit.write(state_dir, 'RESULT', action, args, result='ok' if code in (0, 1) else 'failed',
                                     exit_code=code)
                if isinstance(result, dict):
                    result.setdefault('audit_anchor', {'seq': seq, 'hash': h})
                break
            except OSError:
                time.sleep(1)


def run(env, argv, warnings, Args):
    sub = argv[0] if argv else ''
    env.subcommand = sub or None
    if sub not in SUBCOMMANDS:
        raise errors.error('ERR-CLI-400-01', arg='feeds %s' % sub)
    env.schema = 'qp.feeds.%s/1' % sub
    rest = argv[1:]
    if sub == 'update':
        a = Args(rest, flags=('--json', '--force', '--accept-shrink', '--quiet', '--offline'),
                 options=('--source', '--budget'))
        return update(env, a, warnings)
    if sub == 'status':
        a = Args(rest, flags=('--json',))
        return show_status(env, a, warnings)
    if sub == 'verify':
        a = Args(rest, flags=('--json',), options=('--snapshot',))
        return verify(env, a, warnings)
    if sub == 'export':
        a = Args(rest, flags=('--json', '--raw'), options=('--out', '--variant'))
        return export(env, a, warnings)
    if sub == 'import':
        a = Args(rest, flags=('--json', '--force', '--dry-run', '--yes'), options=('--sha256',))
        return import_(env, a, warnings)
    a = Args(rest, flags=('--json', '--dry-run', '--yes'), options=('--interval-hours',))
    return sched(env, a, warnings)


def _no_positional(a):
    if a.positional:
        raise errors.error('ERR-CLI-400-01', arg=a.positional[0])


def update(env, a, warnings):
    _no_positional(a)
    only = None
    if '--source' in a.opts:
        only = [s.strip() for s in a.opts['--source'].split(',') if s.strip()]
        if not only or any(s not in sources.SOURCES for s in only):
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--source')
    if '--accept-shrink' in a.flags and '--force' not in a.flags:
        raise errors.error('ERR-CLI-400-01', '{arg} requires --force.', arg='--accept-shrink')
    budget = None
    if '--budget' in a.opts:
        b = a.opts['--budget']
        if not b.isdigit() or not 60 <= int(b) <= 3600:
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--budget')
        budget = int(b)
    quiet = '--quiet' in a.flags or '--json' in a.flags
    sd_warn = []
    state_dir = statedir.select(sd_warn)
    warnings.extend((None, w) for w in sd_warn)
    shrink = '--accept-shrink' in a.flags
    args = ['feeds', 'update'] + list(a.raw)

    def work():
        return sync.run(state_dir, only=only, force='--force' in a.flags, accept_shrink=shrink, budget=budget,
                        offline='--offline' in a.flags)
    if shrink:      # BR-FEED-009 exception is audited
        holder = {}

        def audited():
            code, result, w = work()
            holder['w'] = w
            return code, result
        code, result = audit_pair(state_dir, 'feeds_update_accept_shrink', args, audited)
        sync_warn = holder.get('w', [])
    else:
        code, result, sync_warn = work()
    warnings.extend(sync_warn)
    fill_data(env, FeedsDir(state_dir))
    for s in result['sources']:
        if s['outcome'] == 'failed' or (s['status'] in ('DEGRADED', 'FAILED') and s['last_error']):
            env.error(s['last_error'] or 'ERR-FEED-503-01', errors.message(
                s['last_error'] or 'ERR-FEED-503-01', source=s['src_id'], origin=s.get('data_origin') or '-',
                age_h='-', retry_after='-', budget=result['budget_s'], sources=s['src_id'], detail='-'),
                'feed:%s' % s['src_id'])
    if not quiet or code:
        out = sys.stdout if not quiet else sys.stderr
        if not quiet:
            out.write('feeds update: bundle %s\n' % result['bundle_id'])
        for s in result['sources']:
            if quiet and s['outcome'] != 'failed':
                continue
            out.write('  %-8s %-13s %-9s %s\n' % (s['src_id'], s['outcome'], s['status'] or '-', s['last_error'] or ''))
        for code_w, msg in sync_warn:
            if not quiet:
                out.write('  [WARN] %s%s\n' % (msg, ' [%s]' % code_w if code_w else ''))
    return code, result


def source_rows(fs, m, now):
    st = (fs.status() or {}).get('sources', {})
    rows = []
    level, age, stale, ages = fstatus.freshness(m.get('sources', []) if m else [], now)
    by = {r['src_id']: r for r in (m or {}).get('sources', [])}
    for sid in sorted(sources.SOURCES):
        if sid in ('SRC-016', 'SRC-017'):
            continue
        r = dict(by.get(sid) or {})
        r.update({k: v for k, v in (st.get(sid) or {}).items() if k in ('status', 'last_error', 'records', 'data_origin',
                                                                       'last_ok_at')} if st.get(sid) else {})
        last_ok = r.get('last_ok_at')
        rows.append({'src_id': sid, 'name': sources.SOURCES[sid]['name'],
                     'status': r.get('status') or ('DISABLED' if sid == 'SRC-013' else 'FAILED'),
                     'last_ok_at': last_ok,
                     'age_h': max(0, int((now - parse_iso(last_ok)) // 3600)) if last_ok else None,
                     'ttl_h': int(r.get('ttl_h') or sources.SOURCES[sid]['ttl_hours']),
                     'records': r.get('records'), 'last_error': r.get('last_error'),
                     'data_origin': r.get('data_origin')})
    return rows, level, age, stale


def show_status(env, a, warnings, now=None):
    _no_positional(a)
    now = time.time() if now is None else now
    sd_warn = []
    state_dir = statedir.select(sd_warn)
    fs = FeedsDir(state_dir)
    m = fill_data(env, fs, now)
    rows, level, age, stale = source_rows(fs, m, now)
    try:
        sch = schedule.show(state_dir, now)
    except OSError:
        sch = None
    if sch:
        sch = {'type': sch['type'], 'interval_h': sch['interval_h'], 'next_run': sch['next_run']}
    snap = snapshot.describe_packaged(os.environ.get('QP_SCRIPT'))
    result = {'bundle_id': m['bundle_id'] if m else None, 'generated_at': m['generated_at'] if m else None,
              'freshness': level, 'data_age_h': age, 'sources': rows, 'schedule': sch, 'snapshot': snap}
    if m and m.get('base'):
        result['base'] = m['base']
    if level == 'STALE':
        env.warning('ERR-FEED-412-01', errors.message('ERR-FEED-412-01', age_d=age // 24,
                                                      sources=','.join(s['src_id'] for s in stale)))
    elif level == 'EXPIRED':
        env.warning('ERR-SCN-503-01', errors.message('ERR-SCN-503-01', days=age // 24))
    if '--json' not in a.flags:
        if m:
            base = m.get('base') or {}
            print('Bundle %s | built %s%s' % (m['bundle_id'], m['generated_at'],
                                              ' | base: snapshot %s' % base['generated_at'] if base.get('generated_at') else ''))
        else:
            print('No bundle yet (feeds/current is missing).')
        print('%-8s %-28s %-9s %-21s %6s %5s %8s  %s' % ('SRC', 'Source', 'Status', 'Last OK (UTC)', 'Age', 'TTL',
                                                         'Records', 'Last error'))
        for r in rows:
            print('%-8s %-28s %-9s %-21s %6s %5s %8s  %s' % (
                r['src_id'], r['name'][:28], r['status'], (r['last_ok_at'] or '-').replace('T', ' ').rstrip('Z'),
                '%d h' % r['age_h'] if r['age_h'] is not None else '-', '%d h' % r['ttl_h'],
                r['records'] if r['records'] is not None else '-', r['last_error'] or '-'))
        line = 'Freshness: %s' % (level or 'none')
        if age is not None:
            line += ' - data %d h old' % age
            if stale:
                line += ' (oldest: %s)' % stale[0]['src_id']
        line += '. Schedule: %s' % ('%s every %d h, next %s' % (sch['type'], sch['interval_h'], sch['next_run'])
                                    if sch else 'none')
        print(line)
    return EXIT_BY_FRESHNESS.get(level if m else None, 2), result


def verify(env, a, warnings):
    _no_positional(a)
    state_dir = statedir.select([])
    fs = FeedsDir(state_dir)
    if a.opts.get('--snapshot'):
        path = a.opts['--snapshot']
        work = os.path.join(state_dir, 'work', 'verify-%d' % os.getpid())
        os.makedirs(work, mode=0o700)
        try:
            pin = None
            if os.path.realpath(path) == os.path.realpath(snapshot.packaged_path(os.environ.get('QP_SCRIPT')) or ''):
                pin = snapshot.packaged_sha(os.environ.get('QP_SCRIPT'))
            manifest, sha = snapshot.verify_archive(path, pin, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        if '--json' not in a.flags:
            print('Snapshot OK: %s (bundle %s, generated %s), sha256 %s' % (path, manifest['bundle_id'],
                                                                         manifest['generated_at'], sha))
        return 0, {'snapshot': path, 'sha256': sha, 'bundle_id': manifest['bundle_id'],
                   'generated_at': manifest['generated_at'], 'ok': True, 'problems': []}
    cur = bundle.current(fs)
    if not cur:
        raise errors.error('ERR-FEED-503-01', 'No bundle to verify (feeds/current is missing).', source='feeds/current',
                           origin='-', age_h='-')
    try:
        bid = cur['manifest']['bundle_id']
        problems = bundle.check_sums(cur['path'])
    finally:
        cur['release']()
    raw_bad = []
    for dp, dns, fns in os.walk(fs.path('raw')):
        dns[:] = [d for d in dns if d != 'rejected']
        for fn in fns:
            if not fn.endswith('.meta.json'):
                continue
            with open(os.path.join(dp, fn), encoding='utf-8') as f:
                meta = json.load(f)
            body_name = fn[:-len('.meta.json')]
            src = os.path.relpath(dp, fs.path('raw')).split(os.sep)[0]
            rel = os.path.relpath(os.path.join(dp, body_name), fs.path('raw', src))
            body = fs.load_raw(src, rel)
            if body is None or hashlib.sha256(body).hexdigest() != meta.get('sha256'):
                raw_bad.append('raw/%s/%s' % (src, rel))
    result = {'bundle_id': bid, 'ok': not problems and not raw_bad, 'problems': problems, 'raw_problems': raw_bad,
              'rebuilt_bundle_id': None}
    if problems:
        env.error('ERR-FEED-422-02', errors.message('ERR-FEED-422-02'), 'bundle:%s' % bid)
        # §4.3 row 3: rebuild the bundle from the stored source data.
        code, res, w = sync.run(state_dir, offline=True)
        result['rebuilt_bundle_id'] = res['bundle_id']
        warnings.extend(w)
    if '--json' not in a.flags:
        if result['ok']:
            print('Bundle %s OK (SHA256SUMS and raw .meta.json match).' % bid)
        for p in problems + raw_bad:
            print('  [FAIL] %s' % p)
        if result['rebuilt_bundle_id']:
            print('  rebuilt from stored source data: bundle %s' % result['rebuilt_bundle_id'])
    if problems:
        return 2, result
    if raw_bad:
        for p in raw_bad:
            warnings.append(('ERR-FEED-422-02', '%s does not match its .meta.json sha256' % p))
        return 1, result
    return 0, result


def export(env, a, warnings):
    _no_positional(a)
    out = a.opts.get('--out')
    variant = a.opts.get('--variant', 'standard')
    if not out:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--out')
    if variant not in ('standard', 'full'):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--variant')
    if os.path.lexists(out):
        raise errors.error('ERR-CLI-400-01', '{arg} already exists; refusing to overwrite.', arg=out)
    state_dir = statedir.select([])
    fs = FeedsDir(state_dir)
    fill_data(env, fs)
    extra = {}
    if variant == 'full':
        from . import osv
        extra['osv/Packagist-all.zip'] = osv.download_packagist_all(fs)
    res = snapshot.export(fs, out, variant=variant, raw='--raw' in a.flags, extra=extra)
    if '--json' not in a.flags:
        print('Snapshot written: %s (%d bytes)\nsha256 %s' % (res['file'], res['bytes'], res['sha256']))
    return 0, res


def import_(env, a, warnings):
    if len(a.positional) != 1:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='FILE')
    path = a.positional[0]
    sha = a.opts.get('--sha256', '')
    if not re.match(r'^[0-9a-fA-F]{64}$', sha):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--sha256')
    if not os.path.isfile(path):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg=path)
    dry = '--dry-run' in a.flags
    force = '--force' in a.flags
    state_dir = statedir.select([])
    fs = FeedsDir(state_dir)
    cur = bundle.current(fs)
    cur_gen = cur['manifest']['generated_at'] if cur else None
    cur_id = cur['manifest']['bundle_id'] if cur else None
    if cur:
        cur['release']()
    if dry:
        work = os.path.join(state_dir, 'work', 'dryrun-%d' % os.getpid())
        os.makedirs(os.path.join(state_dir, 'work'), mode=0o700, exist_ok=True)
        os.mkdir(work, 0o700)
        try:
            manifest, actual = snapshot.verify_archive(path, sha, work, current_generated_at=cur_gen, force=force)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        fill_data(env, fs)
        result = {'file': path, 'sha256': actual, 'bundle_id': manifest['bundle_id'],
                  'generated_at': manifest['generated_at'], 'previous_bundle_id': cur_id, 'imported': False,
                  'checks': ['sha256', 'tar', 'SHA256SUMS', 'schema', 'generated_at']}
        if '--json' not in a.flags:
            print('[dry-run] snapshot %s passes every check (bundle %s, generated %s); nothing was changed.'
                  % (path, manifest['bundle_id'], manifest['generated_at']))
        return 0, result
    if not confirm('feeds import', a):
        return 1, None
    args = ['feeds', 'import'] + list(a.raw)

    def work():
        with sync.FeedsLock(fs):
            wdir = fs.path('staging-import-%d' % os.getpid())
            os.mkdir(wdir, 0o700)
            try:
                manifest, actual = snapshot.verify_archive(path, sha, wdir, current_generated_at=cur_gen, force=force)
                snapshot.install_extracted(fs, wdir, manifest, actual, archive=path)
            finally:
                shutil.rmtree(wdir, ignore_errors=True)
        return 0, {'file': path, 'sha256': actual, 'bundle_id': manifest['bundle_id'],
                   'generated_at': manifest['generated_at'], 'previous_bundle_id': cur_id, 'imported': True}
    code, result = audit_pair(state_dir, 'feeds_import', args, work)
    anchor = result.pop('audit_anchor', None) if isinstance(result, dict) else None
    env.audit_anchor = anchor
    fill_data(env, fs)
    if '--json' not in a.flags:
        print('Imported snapshot %s: bundle %s (generated %s).' % (path, result['bundle_id'], result['generated_at']))
    return code, result


def sched(env, a, warnings):
    if not a.positional or a.positional[0] not in ('install', 'remove', 'show') or len(a.positional) > 1:
        raise errors.error('ERR-CLI-400-01', arg='feeds schedule %s' % ' '.join(a.positional))
    action = a.positional[0]
    env.subcommand = 'schedule'
    state_dir = statedir.select([])
    dry = '--dry-run' in a.flags
    script = os.path.abspath(os.environ.get('QP_SCRIPT') or 'php-quickpatch.sh')
    if action == 'show':
        info = schedule.show(state_dir)
        if '--json' not in a.flags:
            print('Schedule: %s' % ('%s every %d h at minute %02d, next %s' % (
                info['type'], info['interval_h'], info['minute'], info['next_run']) if info else 'none'))
        return 0, {'action': 'show', 'schedule': info}
    if action == 'install':
        n = a.opts.get('--interval-hours', '6')
        if not n.isdigit() or int(n) not in schedule.INTERVALS:
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--interval-hours')
        n = int(n)
        plan = schedule.plan_install(script, n)
        if n < 6 and not sources.load_keys(sources.key_config_paths(), []).get('NVD_API_KEY'):
            warnings.append((None, 'An interval below 6 h without an NVD API key may hit the NVD rate limit.'))
        result = {'action': 'install', 'type': plan['type'], 'interval_h': n, 'minute': plan['minute'],
                  'files': sorted(k for k in plan['content'] if k != 'crontab'),
                  'commands': [' '.join(c) for c in plan['commands']], 'replaces': plan['replaces'],
                  'content': plan['content']}
        if dry:
            if '--json' not in a.flags:
                for path, text in plan['content'].items():
                    print('[dry-run] would write %s:\n%s' % (path, text.rstrip('\n')))
                for c in result['commands']:
                    print('[dry-run] would run: %s' % c)
            return 0, result
        if not confirm('feeds schedule install', a):
            return 1, None

        def work():
            schedule.install(plan)
            return 0, result
        code, result = audit_pair(state_dir, 'feeds_schedule_install', ['feeds', 'schedule'] + list(a.raw), work)
        env.audit_anchor = result.pop('audit_anchor', None)
        if '--json' not in a.flags:
            print('Schedule installed: %s every %d h at minute %02d.' % (plan['type'], n, plan['minute']))
        return code, result
    plan = schedule.plan_remove()
    result = {'action': 'remove', 'type': plan['type'], 'files': plan['files'],
              'commands': [' '.join(c) for c in plan['commands']], 'removed': plan['current']}
    if dry:
        if '--json' not in a.flags:
            for p in plan['files']:
                print('[dry-run] would delete %s' % p)
            for c in result['commands']:
                print('[dry-run] would run: %s' % c)
        return 0, result
    if not plan['current'] and not plan['files']:
        if '--json' not in a.flags:
            print('No schedule installed; nothing to remove.')
        return 0, result
    if not confirm('feeds schedule remove', a):
        return 1, None

    def work():
        schedule.remove(plan)
        return 0, result
    code, result = audit_pair(state_dir, 'feeds_schedule_remove', ['feeds', 'schedule'] + list(a.raw), work)
    env.audit_anchor = result.pop('audit_anchor', None)
    if '--json' not in a.flags:
        print('Schedule removed.')
    return code, result

