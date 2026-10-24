"""Normalized bundle: files, atomic swap, readers (DOC-SRS-QP-FEED-003 §2.5, §3).

A bundle is an immutable directory bundles/<bundle_id>/ with manifest.json,
SHA256SUMS, the 9 TSV files read by Bash, feeds.db (SQLite) and parts.json.gz
(the per-source facts it was built from, public data only, so an incremental
sync after a snapshot can start from them). `current` and `previous` are
relative symlinks replaced with one rename(2) each (BR-FEED-051).
"""
import errno
import fcntl
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import time

from .. import VERSION, errors
from .sources import SOURCES as SOURCE_NAMES
from .store import utc_iso

SCHEMA = 'qp.feeds.bundle/1'
TSV = {
    'lifecycle.tsv': ['product', 'branch', 'ga_date', 'lts_start', 'active_support_end', 'eol_date', 'prerelease_date',
                      'php_net_supported', 'origin', 'latest_hint', 'codename'],
    'releases.tsv': ['product', 'branch', 'version', 'release_date', 'is_security', 'wp_status', 'abi_modules',
                     'lts_codename'],
    'min_patched.tsv': ['product', 'branch', 'min_patched_sec', 'min_patched_all', 'latest', 'driver_ids'],
    'advisories.tsv': ['adv_id', 'kind', 'status', 'product', 'cvss_rep', 'severity', 'in_kev', 'kev_due',
                       'published_at', 'modified_at', 'summary', 'cvss_rep_src'],
    'affected.tsv': ['adv_id', 'product', 'origin', 'v_start', 'start_incl', 'v_end', 'end_incl', 'v_exact', 'platform',
                     'unbounded', 'assessed', 'used', 'semver_vulnerable', 'semver_patched', 'fixed_in_branch', 'v_prefix'],
    'aliases.tsv': ['adv_id', 'alias_id'],
    'kev.tsv': ['cve_id', 'date_added', 'due_date', 'ransomware'],
    'exposure.tsv': ['product', 'version', 'n_crit', 'n_high', 'n_med', 'n_low', 'cvss_max', 'n_kev', 'adv_ids'],
    'framework_php.tsv': ['framework', 'cycle', 'php_min', 'php_max', 'eol_date'],
    # Not in §3.2: per-source status so Bash computes data age without Python (FR-FEED-AGE-001).
    'sources.tsv': ['src_id', 'name', 'role', 'status', 'last_ok_at', 'ttl_h', 'last_error', 'data_origin', 'records'],
}
REQUIRED = sorted(TSV) + ['feeds.db']
MAX_BUNDLES_KEPT = 2


def _cell(v):
    if v is None:
        return ''
    if isinstance(v, (list, tuple)):
        v = ','.join(str(x) for x in v)
    return str(v).replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')


def write_tsv(path, columns, rows):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('#' + '\t'.join(columns) + '\n')
        for r in rows:
            f.write('\t'.join(_cell(r.get(c)) for c in columns) + '\n')


def read_tsv(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        header = f.readline().lstrip('#').rstrip('\n').split('\t')
        for line in f:
            vals = line.rstrip('\n').split('\t')
            rows.append({k: (vals[i] if i < len(vals) and vals[i] != '' else None) for i, k in enumerate(header)})
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


DDL = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE feed_source(src_id TEXT PRIMARY KEY, ttl_hours INTEGER NOT NULL, enabled INTEGER NOT NULL,
  last_ok_at TEXT, source_updated_at TEXT, status TEXT NOT NULL, last_error TEXT, records INTEGER, data_origin TEXT);
CREATE TABLE feed_fetch(fetch_id INTEGER PRIMARY KEY AUTOINCREMENT, src_id TEXT NOT NULL, url TEXT NOT NULL,
  http_status INTEGER, bytes INTEGER, body_sha256 TEXT, duration_ms INTEGER NOT NULL, fetched_at TEXT NOT NULL);
CREATE TABLE lifecycle_branch(product TEXT NOT NULL, branch TEXT NOT NULL, ga_date TEXT, lts_start TEXT,
  active_support_end TEXT, eol_date TEXT, prerelease_date TEXT, php_net_supported INTEGER, latest_hint TEXT,
  origin TEXT NOT NULL, codename TEXT, PRIMARY KEY(product, branch));
CREATE TABLE release(product TEXT NOT NULL, version TEXT NOT NULL, branch TEXT NOT NULL, release_date TEXT,
  is_security INTEGER NOT NULL, wp_status TEXT, abi_modules INTEGER, lts_codename TEXT, PRIMARY KEY(product, version));
CREATE TABLE advisory(adv_id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL, published_at TEXT,
  modified_at TEXT NOT NULL, summary TEXT, cwe_ids TEXT, cvss_rep REAL, cvss_rep_src TEXT, in_kev INTEGER NOT NULL,
  workaround TEXT, products TEXT NOT NULL, severity TEXT NOT NULL);
CREATE TABLE advisory_alias(adv_id TEXT NOT NULL, alias_id TEXT NOT NULL, PRIMARY KEY(adv_id, alias_id));
CREATE TABLE advisory_score(adv_id TEXT NOT NULL, source TEXT NOT NULL, cvss_version TEXT NOT NULL, type TEXT,
  base_score REAL, vector TEXT, severity_text TEXT, PRIMARY KEY(adv_id, source, cvss_version));
CREATE TABLE affected_range(range_id INTEGER PRIMARY KEY AUTOINCREMENT, adv_id TEXT NOT NULL, product TEXT NOT NULL,
  origin TEXT NOT NULL, v_start TEXT, start_incl INTEGER NOT NULL, v_end TEXT, end_incl INTEGER NOT NULL,
  v_exact TEXT, platform TEXT NOT NULL, unbounded INTEGER NOT NULL, fixed_in_branch TEXT, used INTEGER NOT NULL,
  semver_vulnerable TEXT, semver_patched TEXT, v_prefix TEXT);
CREATE TABLE advisory_fix(adv_id TEXT NOT NULL, product TEXT NOT NULL, branch TEXT NOT NULL, fixed TEXT NOT NULL,
  candidates TEXT, PRIMARY KEY(adv_id, product, branch));
CREATE TABLE kev_entry(cve_id TEXT PRIMARY KEY, date_added TEXT NOT NULL, due_date TEXT, ransomware TEXT);
CREATE TABLE fix_evidence(adv_id TEXT NOT NULL, product TEXT NOT NULL, version TEXT NOT NULL,
  PRIMARY KEY(adv_id, product, version));
CREATE TABLE distro_fix(ecosystem TEXT NOT NULL, src_package TEXT NOT NULL, adv_id TEXT NOT NULL, fixed_version TEXT,
  state TEXT NOT NULL, origin TEXT NOT NULL, PRIMARY KEY(ecosystem, src_package, adv_id));
CREATE TABLE min_patched(product TEXT NOT NULL, branch TEXT NOT NULL, min_patched_sec TEXT, min_patched_all TEXT,
  latest TEXT, driver_ids TEXT, PRIMARY KEY(product, branch));
CREATE TABLE risk_assessment(subject TEXT PRIMARY KEY, score INTEGER NOT NULL, level TEXT NOT NULL,
  components TEXT NOT NULL, bundle_id TEXT NOT NULL);
CREATE TABLE exposure(product TEXT NOT NULL, version TEXT NOT NULL, n_crit INTEGER, n_high INTEGER, n_med INTEGER,
  n_low INTEGER, cvss_max TEXT, n_kev INTEGER, adv_ids TEXT, PRIMARY KEY(product, version));
CREATE TABLE framework_php_support(framework TEXT NOT NULL, cycle TEXT NOT NULL, php_min TEXT, php_max TEXT,
  eol_date TEXT, PRIMARY KEY(framework, cycle));
"""


def write_db(path, model, sources_rows, bundle_id, fetch_log=()):
    db = sqlite3.connect(path)
    try:
        db.executescript(DDL)
        db.executemany('INSERT INTO meta VALUES (?,?)', [('bundle_id', bundle_id), ('schema', SCHEMA),
                                                         ('generator', 'qp-feeds.py %s' % VERSION)])
        db.executemany('INSERT INTO feed_source VALUES (?,?,?,?,?,?,?,?,?)', [
            (s['src_id'], int(s.get('ttl_h') or 0), 0 if s.get('status') == 'DISABLED' else 1, s.get('last_ok_at'),
             s.get('source_updated_at'), s.get('status') or 'FAILED', s.get('last_error'), s.get('records'),
             s.get('data_origin')) for s in sources_rows])
        db.executemany('INSERT INTO feed_fetch(src_id,url,http_status,bytes,body_sha256,duration_ms,fetched_at) '
                       'VALUES (?,?,?,?,?,?,?)', [(r['src_id'], r['url'], r.get('http_status'), r.get('bytes'),
                                                   r.get('body_sha256'), r.get('duration_ms') or 0, r['fetched_at'])
                                                  for r in fetch_log])
        db.executemany('INSERT INTO lifecycle_branch VALUES (?,?,?,?,?,?,?,?,?,?,?)', [
            (r['product'], r['branch'], r.get('ga_date'), r.get('lts_start'), r.get('active_support_end'),
             r.get('eol_date'), r.get('prerelease_date'), r.get('php_net_supported'), r.get('latest_hint'),
             r.get('origin') or 'SRC-001', r.get('codename')) for r in model['lifecycle']])
        db.executemany('INSERT INTO release VALUES (?,?,?,?,?,?,?,?)', [
            (r['product'], r['version'], r['branch'], r.get('release_date'), r['is_security'], r.get('wp_status'),
             r.get('abi_modules'), r.get('lts_codename')) for r in model['releases']])
        db.executemany('INSERT INTO advisory VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', [
            (a['adv_id'], a['kind'], a['status'], a.get('published_at'), a.get('modified_at') or utc_iso(),
             a.get('summary'), a.get('cwe_ids'), float(a['cvss_rep']) if a.get('cvss_rep') else None,
             a.get('cvss_rep_src'), a['in_kev'], a.get('workaround'), ','.join(a['products']), a['severity'])
            for a in model['advisories']])
        db.executemany('INSERT INTO advisory_alias VALUES (?,?)', model['aliases'])
        rows = []
        for a in model['advisories']:
            for s in a['scores']:
                rows.append((a['adv_id'], s['source'], s['cvss_version'], s.get('type'), s.get('base_score'),
                             s.get('vector'), s.get('severity_text')))
        db.executemany('INSERT OR IGNORE INTO advisory_score VALUES (?,?,?,?,?,?,?)', rows)
        db.executemany('INSERT INTO affected_range(adv_id,product,origin,v_start,start_incl,v_end,end_incl,v_exact,'
                       'platform,unbounded,fixed_in_branch,used,semver_vulnerable,semver_patched,v_prefix) '
                       'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', [
                           (r['adv_id'], r['product'], r['origin'], r['v_start'], r['start_incl'], r['v_end'],
                            r['end_incl'], r['v_exact'], r['platform'], r['unbounded'], r['fixed_in_branch'],
                            r['used'], r['semver_vulnerable'], r['semver_patched'], r.get('v_prefix'))
                           for r in model['ranges']])
        db.executemany('INSERT INTO advisory_fix VALUES (?,?,?,?,?)', [
            (f['adv_id'], f['product'], f['branch'], f['fixed'], json.dumps(f['candidates'], sort_keys=True))
            for f in model['fixes']])
        db.executemany('INSERT INTO kev_entry VALUES (?,?,?,?)', [
            (k['cve_id'], k.get('date_added') or '', k.get('due_date'), k.get('ransomware')) for k in model['kev']])
        db.executemany('INSERT INTO fix_evidence VALUES (?,?,?)', model['fix_evidence'])
        db.executemany('INSERT INTO min_patched VALUES (?,?,?,?,?,?)', [
            (m['product'], m['branch'], m.get('min_patched_sec'), m.get('min_patched_all'), m.get('latest'),
             ','.join(m.get('driver_ids') or [])) for m in model['min_patched']])
        db.executemany('INSERT INTO exposure VALUES (?,?,?,?,?,?,?,?,?)', [
            (e['product'], e['version'], e['n_crit'], e['n_high'], e['n_med'], e['n_low'], e['cvss_max'], e['n_kev'],
             ','.join(e['adv_ids'])) for e in model['exposure']])
        db.executemany('INSERT OR IGNORE INTO framework_php_support VALUES (?,?,?,?,?)', [
            (f['framework'], f['cycle'], f['php_min'], f['php_max'], f.get('eol_date')) for f in model['framework']])
        db.commit()
    finally:
        db.close()


def tsv_rows(model, src_rows=()):
    adv = []
    for a in model['advisories']:
        for p in a['products']:
            adv.append(dict(a, product=p))
    return {
        'lifecycle.tsv': model['lifecycle'],
        'releases.tsv': model['releases'],
        'min_patched.tsv': model['min_patched'],
        'advisories.tsv': adv,
        'affected.tsv': model['ranges'],
        'aliases.tsv': [{'adv_id': a, 'alias_id': b} for a, b in model['aliases']],
        'kev.tsv': model['kev'],
        'exposure.tsv': model['exposure'],
        'framework_php.tsv': model['framework'],
        'sources.tsv': [dict(r, name=SOURCE_NAMES.get(r['src_id'], {}).get('name'),
                             role=SOURCE_NAMES.get(r['src_id'], {}).get('role')) for r in src_rows],
    }


def new_bundle_id(now=None):
    t = time.time() if now is None else now
    return 'b-%s-%s' % (time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(t)), os.urandom(4).hex())


def manifest_sources(st_src):
    out = []
    for sid in sorted(st_src):
        e = st_src[sid]
        out.append({'src_id': sid, 'status': e.get('status') or 'FAILED', 'last_ok_at': e.get('last_ok_at'),
                    'source_updated_at': e.get('source_updated_at'), 'records': e.get('records'),
                    'data_origin': e.get('data_origin'), 'last_error': e.get('last_error'),
                    'ttl_h': e.get('ttl_h')})
    return out


def write_sums(d):
    names = sorted(n for n in os.listdir(d) if n not in ('SHA256SUMS', '.lock') and os.path.isfile(os.path.join(d, n)))
    with open(os.path.join(d, 'SHA256SUMS'), 'w') as f:
        for n in names:
            f.write('%s  %s\n' % (sha256_file(os.path.join(d, n)), n))


def check_sums(d):
    """Mismatches between SHA256SUMS and the files of bundle D (BR-FEED-010). [] when OK."""
    bad = []
    p = os.path.join(d, 'SHA256SUMS')
    if not os.path.isfile(p):
        return ['SHA256SUMS missing']
    listed = set()
    with open(p) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            h, _, name = line.partition('  ')
            if '/' in name or name.startswith('.'):
                bad.append('unsafe name %r' % name)
                continue
            listed.add(name)
            fp = os.path.join(d, name)
            if not os.path.isfile(fp) or os.path.islink(fp):
                bad.append('%s missing' % name)
            elif sha256_file(fp) != h:
                bad.append('%s sha256 mismatch' % name)
    for n in REQUIRED + ['manifest.json']:
        if n not in listed:
            bad.append('%s not in SHA256SUMS' % n)
    return bad


def write(fs, model, parts, st_src, base=None, now=None, fetch_log=(), install_it=True):
    """W1: build staging/; then install() (W2-W5). Returns the manifest."""
    now = time.time() if now is None else now
    staging = fs.path('staging')
    if os.path.lexists(staging):
        shutil.rmtree(staging)
    os.mkdir(staging, 0o755 if os.geteuid() == 0 else 0o700)
    bundle_id = new_bundle_id(now)
    try:
        src_rows = manifest_sources(st_src)
        for name, rows in tsv_rows(model, src_rows).items():
            write_tsv(os.path.join(staging, name), TSV[name], rows)
        write_db(os.path.join(staging, 'feeds.db'), model, [dict(r, ttl_h=r.get('ttl_h')) for r in src_rows],
                 bundle_id, fetch_log)
        with open(os.path.join(staging, 'parts.json.gz'), 'wb') as f:
            f.write(gzip.compress(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode('utf-8'), mtime=0))
        files = []
        for n in sorted(os.listdir(staging)):
            files.append({'path': n, 'bytes': os.path.getsize(os.path.join(staging, n)),
                          'sha256': sha256_file(os.path.join(staging, n))})
        manifest = {'schema': SCHEMA, 'bundle_id': bundle_id, 'generated_at': utc_iso(now),
                    'generator': 'qp-feeds.py %s' % VERSION, 'base': base, 'today': model.get('today'),
                    'sources': src_rows, 'coverage': model['coverage'], 'files': files}
        with open(os.path.join(staging, 'manifest.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
        write_sums(staging)
        open(os.path.join(staging, '.lock'), 'w').close()
        bad = check_sums(staging)
        if bad:
            raise errors.error('ERR-FEED-422-02', details={'file': bad[0]})
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if install_it:
        install(fs, staging, bundle_id)
    return manifest


def install(fs, staging, bundle_id):
    """W2-W5 of BR-FEED-051; caller holds feeds/.lock."""
    target = fs.path('bundles', bundle_id)
    if check_sums(staging):
        shutil.rmtree(staging, ignore_errors=True)
        raise errors.error('ERR-FEED-422-02', details={'file': 'SHA256SUMS'})
    if os.path.lexists(target):
        # The same bundle is already there (e.g. `import --force` of the previous one): switch to it.
        same = not check_sums(target) and _read(os.path.join(target, 'SHA256SUMS')) == \
            _read(os.path.join(staging, 'SHA256SUMS'))
        shutil.rmtree(staging, ignore_errors=True)
        if not same:
            raise errors.error('ERR-FEED-422-02', details={'file': bundle_id, 'reason': 'bundle exists'})
    else:
        if not os.path.exists(os.path.join(staging, '.lock')):
            open(os.path.join(staging, '.lock'), 'w').close()
        os.rename(staging, target)                                      # W2
    old = os.readlink(fs.path('current')) if os.path.islink(fs.path('current')) else None
    tmp = fs.path('.current.new')
    if os.path.lexists(tmp):
        os.unlink(tmp)
    os.symlink(os.path.join('bundles', bundle_id), tmp)
    os.replace(tmp, fs.path('current'))                                 # W3
    if old and old != os.path.join('bundles', bundle_id):
        tmp = fs.path('.previous.new')
        if os.path.lexists(tmp):
            os.unlink(tmp)
        os.symlink(old, tmp)
        os.replace(tmp, fs.path('previous'))                            # W4
    prune(fs)                                                           # W5


def _read(path):
    try:
        with open(path, 'rb') as f:
            return f.read()
    except OSError:
        return None


def prune(fs):
    keep = set()
    for name in ('current', 'previous'):
        p = fs.path(name)
        if os.path.islink(p):
            keep.add(os.path.basename(os.readlink(p)))
    removed = []
    for b in sorted(os.listdir(fs.path('bundles'))):
        if b in keep:
            continue
        d = fs.path('bundles', b)
        lock = os.path.join(d, '.lock')
        try:
            fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
        except OSError:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(b)
            continue
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            continue                       # a reader still uses it; next run
        try:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(b)
        finally:
            os.close(fd)
    return removed


def _validated_path(fs, path):
    real = os.path.realpath(path)
    root = os.path.realpath(fs.path('bundles'))
    if os.path.dirname(real) != root:
        return None
    return real


def current(fs, which='current'):
    """Resolve CURRENT once and hold a shared lock on its .lock (reader side of §2.5).

    Returns {'path', 'manifest', 'release'} or None. QP_FEEDS_BUNDLE (set by the
    Bash parent, already locked there) is used when it points inside bundles/.
    """
    env = os.environ.get('QP_FEEDS_BUNDLE') if which == 'current' else None
    for _ in range(3):
        if env:
            path = _validated_path(fs, env)
            env = None
        else:
            link = fs.path(which)
            if not os.path.islink(link):
                return None
            path = _validated_path(fs, link)
        if not path:
            continue
        try:
            fd = os.open(os.path.join(path, '.lock'), os.O_RDONLY | os.O_NOFOLLOW)
        except OSError as e:
            if e.errno in (errno.ENOENT, errno.ELOOP):
                continue
            raise
        fcntl.flock(fd, fcntl.LOCK_SH)
        try:
            with open(os.path.join(path, 'manifest.json'), encoding='utf-8') as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            os.close(fd)
            continue

        def release(fd=fd):
            try:
                os.close(fd)
            except OSError:
                pass
        return {'path': path, 'manifest': manifest, 'release': release}
    return None


def load_parts(path):
    p = os.path.join(path, 'parts.json.gz')
    if not os.path.isfile(p):
        return {}
    with open(p, 'rb') as f:
        return json.loads(gzip.decompress(f.read()).decode('utf-8'))
