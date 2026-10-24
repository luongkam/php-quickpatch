"""One `feeds update` run (FR-FEED-SYNC-001, DIAG-SEQ-QP-FEED-001).

1. feeds/.lock (wait <= 30 s, ERR-FEED-423-01) and >= 100 MB free (ERR-FEED-507-01).
2. Each enabled source that is due (age >= TTL - (N + 45 min), BR-FEED-001) is
   collected in SYNC_ORDER within the time budget (900 s full / 180 s
   incremental). A failing source keeps its previous facts (BR-FEED-006/007)
   and is reported with its role's error code.
3. CVE.org fills CVEs that NVD lacks (FR-FEED-PCVE-003, BR-FEED-014).
4. The facts of every source are normalized into a new bundle that replaces
   `current` atomically (bundle.install).
"""
import errno
import fcntl
import os
import time

from .. import errors
from . import bundle, collect, normalize, snapshot, sources
from .http import BudgetExceeded, Fetcher, FetchError
from .store import FeedsDir, parse_iso, read_json, utc_iso, write_json

LOCK_WAIT_S = 30
MIN_FREE_MB = 100
DUE_MARGIN_S = 45 * 60


class SyncError(errors.QPError):
    pass


class FeedsLock(object):
    """Exclusive flock on feeds/.lock (BR-FEED-015). Not STATE_DIR/.lock of fix."""

    def __init__(self, fs, wait=LOCK_WAIT_S, sleep=time.sleep):
        self.path = fs.path('.lock')
        self.wait = wait
        self.sleep = sleep
        self.fd = None

    def __enter__(self):
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        deadline = time.time() + self.wait
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if e.errno not in (errno.EAGAIN, errno.EACCES) or time.time() >= deadline:
                    pid = '?'
                    try:
                        pid = os.pread(fd, 32, 0).decode().strip() or '?'
                    except OSError:
                        pass
                    os.close(fd)
                    raise errors.error('ERR-FEED-423-01', pid=pid, details={'lock': 'feeds/.lock', 'pid': pid})
                self.sleep(0.2)
        os.ftruncate(fd, 0)
        os.pwrite(fd, ('%d\n' % os.getpid()).encode(), 0)
        self.fd = fd
        return self

    def __exit__(self, *exc):
        try:
            os.ftruncate(self.fd, 0)
        finally:
            os.close(self.fd)   # releases the lock


def free_mb(path):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize // (1024 * 1024)


def schedule_interval_h(state_dir):
    from . import schedule
    try:
        info = schedule.show(state_dir)
        return int(info.get('interval_h') or 0) if info else 0
    except Exception:  # noqa: BLE001 - a broken schedule must not stop a sync
        return 0


def server_branches(state_dir):
    """PHP branches running on this server, from the last scan (FR-FEED-REL-001 (b))."""
    doc = read_json(os.path.join(state_dir, 'state', 'last-scan.json'), {}) or {}
    res = doc.get('result') or {}
    out = set()
    for rt in res.get('runtimes', []) or []:
        if rt.get('kind') == 'php' and rt.get('branch'):
            out.add(rt['branch'])
    return {'php': sorted(out)}


class Context(object):
    """What collectors see of the sync (collect.py)."""

    def __init__(self, fs, conf, keys, fetcher, accept_shrink=False, branches=None,
                 snapshot_base_at=None, base_parts=None, now=time.time):
        self.fs = fs
        self.conf = conf
        self.keys = keys
        self.fetcher = fetcher
        self.accept_shrink = accept_shrink
        self.server_branches = branches or {}
        self.snapshot_base_at = snapshot_base_at
        self.base_parts = base_parts or {}
        self.now = now
        self.prev_counts = fs.state('counts', {}) or {}
        self.counts = {}
        self.warnings = []          # (src, code, message)
        self.unparseable_n = {}
        self.unparseable_msgs = {}
        self.primary_error = {}     # src -> FetchError of the primary endpoint
        self.fetch_kinds = {}       # src -> set('fetched', 'not_modified')
        self._pending = {}

    # --- requests -----------------------------------------------------------
    def get(self, src, name, url, conditional=True, use_etag=True, headers=None):
        """GET a document of SRC. Returns its body (a 304 returns the stored body)."""
        meta = self.fs.raw_meta(src, name) if conditional else {}
        hdrs = dict(headers or {})
        stored = self.fs.load_raw(src, name) if meta else None
        if stored is not None and meta.get('url') == url:
            if use_etag and meta.get('etag') and meta.get('accept_encoding', 'gzip') == 'gzip':
                hdrs['If-None-Match'] = meta['etag']
            if meta.get('last_modified'):
                hdrs['If-Modified-Since'] = meta['last_modified']
        try:
            resp = self.fetcher.request(src, url, headers=hdrs)
        except FetchError as e:
            self.primary_error.setdefault(src, e)
            raise
        if resp.status == 304 and stored is not None:
            self.fetch_kinds.setdefault(src, set()).add('not_modified')
            self._pending[(src, name)] = dict(meta, fetched_at=utc_iso(self.now()), http_status=304,
                                              duration_ms=resp.duration_ms)
            return stored
        if resp.status != 200:
            e = FetchError('ERR-FEED-503-01', 'HTTP %d from %s' % (resp.status, url), http=resp.status)
            self.primary_error.setdefault(src, e)
            raise e
        self.fetch_kinds.setdefault(src, set()).add('fetched')
        h = {k.lower(): v for k, v in resp.headers.items()}
        self._pending[(src, name)] = {'url': url, 'http_status': 200, 'etag': h.get('etag'),
                                      'last_modified': h.get('last-modified'), 'accept_encoding': 'gzip',
                                      'fetched_at': utc_iso(self.now()), 'duration_ms': resp.duration_ms}
        return resp.body

    def save_raw(self, src, name, body):
        meta = self._pending.pop((src, name), None) or {'url': None, 'http_status': 200,
                                                        'fetched_at': utc_iso(self.now())}
        if 'fetched' not in self.fetch_kinds.get(src, ()) and 'not_modified' not in self.fetch_kinds.get(src, ()):
            self.fetch_kinds.setdefault(src, set()).add('fetched')
        self.fs.save_raw(src, name, body, meta)

    # --- previous data ------------------------------------------------------
    def prev_doc(self, src):
        doc = self.fs.load_parts(src)
        if doc is None:
            doc = self.base_parts.get(src)
        return doc

    def prev_facts(self, src):
        doc = self.prev_doc(src)
        return list(doc.get('facts', [])) if doc else []

    def facts_of(self, src):
        """Facts of SRC as of now (parts written earlier in this run, else previous)."""
        return self.prev_facts(src)

    # --- diagnostics --------------------------------------------------------
    def warn(self, src, msg, code=None):
        self.warnings.append((src, code, msg))

    def unparseable(self, src, msg, count=1):
        self.unparseable_n[src] = self.unparseable_n.get(src, 0) + count
        self.unparseable_msgs.setdefault(src, []).append(msg)

    # --- on-demand cache (cache/<kind>/<key>.json) --------------------------
    def cache_get(self, kind, key, ttl_s):
        p = self.fs.path('cache', kind, key.replace('/', '_') + '.json')
        doc = read_json(p)
        if not doc or self.now() - doc.get('_cached_at', 0) > ttl_s:
            return None
        return doc.get('data')

    def cache_put(self, kind, key, data):
        d = self.fs.path('cache', kind)
        os.makedirs(d, exist_ok=True)
        write_json(os.path.join(d, key.replace('/', '_') + '.json'), {'_cached_at': self.now(), 'data': data})


def is_due(entry, conf_src, interval_h, now, force):
    if force:
        return True
    fetched = (entry or {}).get('fetched_at')
    if not fetched:
        return True
    ttl = float(conf_src.get('ttl_hours') or 0) * 3600
    return now - parse_iso(fetched) >= ttl - (interval_h * 3600 + DUE_MARGIN_S)


def role_code(src, code):
    if code == 'ERR-FEED-503-01' and sources.SOURCES[src]['role'] != 'primary':
        return 'ERR-FEED-503-03'
    return code


def run(state_dir, only=None, force=False, accept_shrink=False, budget=None, offline=False,
        out=None, now=time.time, sleep=time.sleep, today=None):
    """Run one sync. Returns (exit_code, result dict, warnings list of (code, msg))."""
    fs = FeedsDir(state_dir)
    warnings = []
    with FeedsLock(fs):
        mb = free_mb(fs.root)
        if mb < MIN_FREE_MB:
            raise errors.error('ERR-FEED-507-01', free=mb, details={'free_mb': mb})
        t0 = now()
        conf = sources.load(fs.root)
        bad = [s for s, c in conf.items() if c.get('config_error')]
        for s in bad:
            raise errors.error('ERR-CLI-400-01', 'sources.conf: %s' % conf[s]['config_error'], arg='sources.conf')
        key_warn = []
        keys = sources.load_keys(sources.key_config_paths(), key_warn)
        for w in key_warn:
            warnings.append((None, w))
        snap_warn = []
        installed = snapshot.maybe_install_packaged(fs, os.environ.get('QP_SCRIPT'), snap_warn, now=now())
        warnings.extend(snap_warn)
        status = fs.status() or {}
        st_src = status.setdefault('sources', {})
        interval = schedule_interval_h(state_dir)
        cur = bundle.current(fs)
        base_parts, snapshot_base_at = {}, None
        base = fs.state('base') or None
        if base and base.get('type') == 'snapshot' and base.get('generated_at'):
            snapshot_base_at = parse_iso(base['generated_at'])
        if cur:
            base_parts = bundle.load_parts(cur['path'])
            for row in cur['manifest'].get('sources', []):     # seed: data inherited from the bundle
                e = st_src.setdefault(row['src_id'], {})
                if not e:
                    e.update(row)
                    e['fetched_at'] = row.get('last_ok_at')
                    if row.get('data_origin') and installed:
                        e['data_origin'] = 'SNAPSHOT'
            cur['release']()
        if fs.state('nvd-cursor') is None and cur is None:
            default_budget = 900
        else:
            default_budget = 180
        budget = int(budget or default_budget)
        fetcher = Fetcher(conf, deadline=t0 + budget, log=[], sleep=sleep, now=now)
        ctx = Context(fs, conf, keys, fetcher, accept_shrink=accept_shrink, branches=server_branches(state_dir),
                      snapshot_base_at=snapshot_base_at, base_parts=base_parts, now=now)
        order = list(sources.SYNC_ORDER) + [s for s in ('SRC-013',) if s not in sources.SYNC_ORDER]
        if only:
            order = [s for s in order if s in only] + [s for s in only if s not in order]
        report, pending = [], []
        budget_hit = False
        for src in order:
            c = conf[src]
            entry = st_src.setdefault(src, {})
            entry['ttl_h'] = int(c.get('ttl_hours') or 0)
            if src == 'SRC-013' and not keys.get('WORDFENCE_API_KEY'):
                c['enabled'] = 0
            if not c.get('enabled'):
                entry.update(status='DISABLED', last_error=None)
                report.append((src, 'disabled', None))
                continue
            if src not in collect.COLLECTORS:
                continue
            if offline:
                report.append((src, 'not_due', None))
                continue
            if not is_due(entry, c, interval, now(), force):
                fs.log_sync('%s not_due' % src)
                report.append((src, 'not_due', None))
                continue
            if budget_hit:
                pending.append(src)
                continue
            entry['last_attempt_at'] = utc_iso(now())
            try:
                res = collect.COLLECTORS[src](ctx)
            except BudgetExceeded:
                budget_hit = True
                pending.append(src)
                continue
            except FetchError as e:
                code = role_code(src, e.code)
                _keep_previous(ctx, fs, src, entry, code)
                fs.log_sync('%s failed %s %s' % (src, code, e.message))
                report.append((src, 'failed', code))
                continue
            except collect.Invalid as e:
                fs.reject(src, e.name, e.body, e.message)
                _keep_previous(ctx, fs, src, entry, e.code)
                fs.log_sync('%s failed %s %s' % (src, e.code, e.message))
                report.append((src, 'failed', e.code))
                warnings.append((e.code, errors.message(e.code, source=src, detail=e.message)))
                continue
            kinds = ctx.fetch_kinds.get(src, set())
            kind = 'fetched' if 'fetched' in kinds or not kinds else 'not_modified'
            if res is not None:
                origin = res.get('origin', 'PRIMARY')
                fs.save_parts(src, res['facts'], {'records': res.get('records'), 'data_origin': origin,
                                                  'source_updated_at': res.get('source_updated_at'),
                                                  'fetched_at': utc_iso(now())})
            else:
                origin = (ctx.prev_doc(src) or {}).get('data_origin', 'PRIMARY')
                res = {'records': (ctx.prev_doc(src) or {}).get('records')}
            perr = ctx.primary_error.get(src)
            degraded = origin != 'PRIMARY'
            entry.update(status='DEGRADED' if degraded else 'OK', last_ok_at=utc_iso(now()), fetched_at=utc_iso(now()),
                         last_error=role_code(src, perr.code) if degraded and perr else None,
                         records=res.get('records'), data_origin=origin,
                         source_updated_at=res.get('source_updated_at') or entry.get('source_updated_at'))
            fs.log_sync('%s %s records=%s origin=%s' % (src, kind, res.get('records'), origin))
            report.append((src, kind, entry['last_error']))
            if ctx.unparseable_n.get(src):
                n = ctx.unparseable_n[src]
                warnings.append(('ERR-FEED-422-01', errors.message('ERR-FEED-422-01', count=n, source=src)))
        if pending:
            for src in pending:
                entry = st_src.setdefault(src, {})
                _keep_previous(ctx, fs, src, entry, 'ERR-FEED-504-01')
                report.append((src, 'failed', 'ERR-FEED-504-01'))
                fs.log_sync('%s failed ERR-FEED-504-01 budget' % src)
            warnings.append(('ERR-FEED-504-01', errors.message('ERR-FEED-504-01', budget=budget, sources=','.join(pending))))
        # FR-FEED-PCVE-003 / BR-FEED-014: CVE.org for CVEs NVD lacks.
        if not offline and conf['SRC-005'].get('enabled') and (only is None or 'SRC-005' in only or 'SRC-004' in (only or ())):
            _cveorg(ctx, fs, st_src, now)
        if ctx.counts:
            counts = dict(ctx.prev_counts)
            counts.update(ctx.counts)
            fs.save_state('counts', counts)
        for src, code, msg in ctx.warnings:
            warnings.append((code, '%s: %s' % (src, msg)))
        parts = collect_parts(fs, base_parts)
        if not parts:
            fs.save_status(status)
            raise errors.error('ERR-FEED-503-01', 'No usable data: every source failed and there is no cache or snapshot.',
                               source='all', origin='-', age_h='-')
        seen = fs.state('sec-release-seen', {}) or {}
        model = normalize.build(parts, today=today, now=now(), sec_seen=seen)
        fs.save_state('sec-release-seen', seen)
        for c in model['conflicts']:
            warnings.append(('ERR-FEED-409-01', c['message']))
        new = bundle.write(fs, model, parts, st_src, base=base, now=now(), fetch_log=fetcher.log)
        status['last_run'] = {'at': utc_iso(t0), 'duration_s': int(now() - t0), 'bundle_id': new['bundle_id'],
                              'requests': fetcher.requests}
        fs.save_status(status)
        _log_fetches(fs, fetcher.log)
        prune_cache(fs, now())
    enabled = [s for s in order if conf[s].get('enabled') and s in collect.COLLECTORS]
    bad_src = [s for s in enabled if st_src.get(s, {}).get('status') in ('DEGRADED', 'FAILED')]
    code = 1 if bad_src else 0
    result = {'bundle_id': new['bundle_id'], 'generated_at': new['generated_at'],
              'sources': [{'src_id': s, 'outcome': k, 'status': st_src.get(s, {}).get('status'),
                           'last_error': err, 'records': st_src.get(s, {}).get('records'),
                           'data_origin': st_src.get(s, {}).get('data_origin')} for s, k, err in report],
              'requests': fetcher.requests, 'budget_s': budget, 'pending': pending,
              'coverage': new['coverage']}
    return code, result, warnings


def _keep_previous(ctx, fs, src, entry, code):
    """BR-FEED-006/007: keep the previous facts; status DEGRADED (cache/snapshot) or FAILED."""
    own = fs.load_parts(src)
    if own is not None:
        origin = 'CACHE'
    elif ctx.base_parts.get(src) is not None:
        origin = 'SNAPSHOT'
    else:
        origin = None
    entry.update(status='DEGRADED' if origin else 'FAILED', last_error=code)
    if origin:
        entry['data_origin'] = origin
    else:
        entry['data_origin'] = None
        entry.setdefault('last_ok_at', None)


def _cveorg(ctx, fs, st_src, now):
    """CVEs mentioned by other sources but missing from NVD (or without ranges)."""
    nvd = {f['adv_id']: f for f in ctx.prev_facts('SRC-004') if f.get('type') == 'advisory'}
    wanted = {}
    for src in ('SRC-003', 'SRC-011', 'SRC-008'):
        for f in ctx.prev_facts(src):
            ids = []
            if f.get('type') == 'fix':
                ids = [f['adv_id']]
            elif f.get('type') == 'advisory':
                ids = [f['adv_id']] + list(f.get('aliases', []))
            for a in ids:
                if not a.startswith('CVE-'):
                    continue
                n = nvd.get(a)
                if n is None or (not n.get('ranges') and n.get('status') in ('AWAITING_ANALYSIS', 'PUBLISHED')):
                    wanted[a] = (f.get('product') or (f.get('products') or ['php'])[0])
    for a, n in nvd.items():
        if n.get('status') in ('AWAITING_ANALYSIS', 'PENDING_NVD', 'RESERVED') and not n.get('ranges'):
            pub = n.get('published_at') or n.get('modified_at')
            try:
                if pub and now() - parse_iso(pub) > 30 * 86400:
                    continue
            except ValueError:
                pass
            wanted[a] = n['products'][0]
    entry = st_src.setdefault('SRC-005', {})
    entry['ttl_h'] = 24
    if not wanted:
        entry.setdefault('status', 'OK')
        return
    try:
        facts = collect.lookup_cveorg(ctx, wanted)
    except BudgetExceeded:
        return
    fs.save_parts('SRC-005', facts, {'records': len(facts), 'data_origin': 'PRIMARY', 'fetched_at': utc_iso(now())})
    entry.update(status='OK', last_ok_at=utc_iso(now()), fetched_at=utc_iso(now()), records=len(facts),
                 data_origin='PRIMARY', last_error=None)


def collect_parts(fs, base_parts):
    """Facts per source: own parts/ first, else the ones carried by the current bundle."""
    out = {}
    for src in sorted(set(sources.SOURCES) | set(base_parts)):
        doc = fs.load_parts(src)
        if doc is None:
            doc = base_parts.get(src)
        if doc is not None:
            out[src] = doc
    return out


def prune_cache(fs, now, max_age=7 * 86400):
    """BR-FEED-052: on-demand cache entries older than 7 days are removed."""
    for dp, _, fns in os.walk(fs.path('cache')):
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                if now - os.lstat(p).st_mtime > max_age:
                    os.unlink(p)
            except OSError:
                pass


def _log_fetches(fs, rows):
    """feed_fetch rows, kept 30 days (BR-FEED-052)."""
    path = fs.path('state', 'fetch-log.json')
    old = read_json(path, []) or []
    cutoff = utc_iso(time.time() - 30 * 86400)
    keep = [r for r in old if r.get('fetched_at', '') >= cutoff] + rows
    write_json(path, keep[-5000:])
