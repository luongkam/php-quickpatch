"""Offline snapshots (DOC-SRS-QP-FEED-003 §4, FR-FEED-SNAP-001..004, BR-FEED-010/053..056).

Archive layout:
  manifest.json   the bundle manifest + variant, tool_version_min, built_by
  SHA256SUMS      sha256sum lines for every file under bundle/
  bundle/         the bundle files (no .lock, no host data)
  raw/            only with `feeds export --raw` (BR-FEED-012)
  catalog/        the scenario catalog with its own SHA256SUMS (FR-SCN-CAT-001)
"""
import hashlib
import io
import json
import os
import re
import shutil
import tarfile
import time

from .. import VERSION, catalog as qcatalog, errors
from . import bundle
from .store import parse_iso, utc_iso, write_json

MAX_UNPACKED = 50 * 1024 * 1024
KEEP_IMPORTED = 3
BUNDLE_ID_RE = re.compile(r'^b-\d{8}T\d{6}Z-[0-9a-f]{8}$')


def sha256_of(path):
    return bundle.sha256_file(path)


def integrity(detail, **kw):
    d = dict(kw)
    d['detail'] = detail
    return errors.error('ERR-FEED-422-02', details=d)


def _add_bytes(tar, name, data, mtime):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = mtime
    info.mode = 0o644
    info.uname = info.gname = 'root'
    tar.addfile(info, io.BytesIO(data))


def export(fs, out, variant='standard', raw=False, built_by='feeds export', extra=None):
    """FR-FEED-SNAP-002 / BR-FEED-056: public data only. Returns dict(file, sha256, bytes, bundle_id)."""
    cur = bundle.current(fs)
    if cur is None:
        raise errors.error('ERR-FEED-503-01', 'No bundle to export (feeds/current is missing).',
                           source='feeds/current', origin='-', age_h='-')
    try:
        src = cur['path']
        names = sorted(n for n in os.listdir(src) if n != '.lock' and os.path.isfile(os.path.join(src, n)))
        manifest = dict(cur['manifest'])
        manifest.update(variant=variant, tool_version_min=VERSION.split('-')[0], built_by=built_by)
        sums = ''.join('%s  bundle/%s\n' % (bundle.sha256_file(os.path.join(src, n)), n) for n in names)
        mtime = int(parse_iso(manifest['generated_at']))
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)   # never overwrite (§6.2 --out)
        with os.fdopen(fd, 'wb') as f:
            with tarfile.open(fileobj=f, mode='w:gz', format=tarfile.PAX_FORMAT) as tar:
                _add_bytes(tar, 'manifest.json', (json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True)
                                                  + '\n').encode('utf-8'), mtime)
                _add_bytes(tar, 'SHA256SUMS', sums.encode(), mtime)
                for n in names:
                    with open(os.path.join(src, n), 'rb') as fh:
                        _add_bytes(tar, 'bundle/' + n, fh.read(), mtime)
                if raw:
                    root = fs.path('raw')
                    for dp, dns, fns in os.walk(root):
                        dns[:] = sorted(d for d in dns if d != 'rejected')
                        for fn in sorted(fns):
                            p = os.path.join(dp, fn)
                            if os.path.islink(p):
                                continue
                            with open(p, 'rb') as fh:
                                _add_bytes(tar, 'raw/' + os.path.relpath(p, root), fh.read(), mtime)
                files = dict(extra or {})
                try:
                    qcatalog.check(qcatalog.PACKAGED)
                    for name, data in qcatalog.files_for_snapshot().items():
                        files.setdefault(name, data)
                except (qcatalog.CatalogError, OSError):
                    pass
                for name, data in sorted(files.items()):
                    _add_bytes(tar, name, data, mtime)
    finally:
        cur['release']()
    return {'file': out, 'sha256': sha256_of(out), 'bytes': os.path.getsize(out),
            'bundle_id': manifest['bundle_id'], 'generated_at': manifest['generated_at'], 'variant': variant}


def safe_extract(archive, dest):
    """§4.3 last row: refuse absolute paths, '..', links, devices; <= 50 MB unpacked."""
    total = 0
    try:
        tar = tarfile.open(archive, mode='r:gz')
    except (tarfile.TarError, OSError, EOFError) as e:
        raise integrity('unreadable archive: %s' % e, file=archive)
    with tar:
        members = []
        try:
            for m in tar:
                n = m.name
                if n.startswith('/') or '..' in n.split('/') or '\\' in n:
                    raise integrity('unsafe path %r' % n, file=n)
                if not (m.isfile() or m.isdir()):
                    raise integrity('link or device entry %r' % n, file=n)
                total += m.size
                if total > MAX_UNPACKED:
                    raise integrity('unpacked size above 50 MB', file=archive)
                members.append(m)
        except (tarfile.TarError, EOFError, OSError) as e:
            raise integrity('corrupt archive: %s' % e, file=archive)
        for m in members:
            target = os.path.join(dest, m.name)
            if m.isdir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            src = tar.extractfile(m)
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            with os.fdopen(fd, 'wb') as out:
                shutil.copyfileobj(src, out)


def check_extracted(d):
    """SHA256SUMS of the archive + bundle schema. Returns the archive manifest."""
    sums = os.path.join(d, 'SHA256SUMS')
    if not os.path.isfile(sums):
        raise integrity('SHA256SUMS missing', file='SHA256SUMS')
    listed = set()
    with open(sums) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            h, _, name = line.partition('  ')
            if not name.startswith('bundle/') or '..' in name.split('/'):
                raise integrity('unsafe SHA256SUMS entry %r' % name, file=name)
            p = os.path.join(d, name)
            if not os.path.isfile(p):
                raise integrity('%s missing' % name, file=name)
            actual = bundle.sha256_file(p)
            if actual != h:
                raise integrity('%s sha256 mismatch' % name, file=name, expected=h, actual=actual)
            listed.add(name[len('bundle/'):])
    bdir = os.path.join(d, 'bundle')
    for n in os.listdir(bdir) if os.path.isdir(bdir) else []:
        if n not in listed:
            raise integrity('bundle/%s not in SHA256SUMS' % n, file=n)
    try:
        with open(os.path.join(d, 'manifest.json'), encoding='utf-8') as f:
            manifest = json.load(f)
        with open(os.path.join(bdir, 'manifest.json'), encoding='utf-8') as f:
            inner = json.load(f)
    except (OSError, ValueError) as e:
        raise integrity('manifest unreadable: %s' % e, file='manifest.json')
    if str(manifest.get('schema', '')).rsplit('/', 1)[0] != 'qp.feeds.bundle' or \
            str(manifest.get('schema')).rsplit('/', 1)[-1] != bundle.SCHEMA.rsplit('/', 1)[-1]:
        raise integrity('schema %r not supported' % manifest.get('schema'), file='manifest.json')
    if inner.get('bundle_id') != manifest.get('bundle_id') or not BUNDLE_ID_RE.match(str(inner.get('bundle_id'))):
        raise integrity('bundle_id mismatch', file='manifest.json')
    missing = [n for n in bundle.REQUIRED if n not in listed]
    if missing:
        raise integrity('missing %s' % ', '.join(missing), file=missing[0])
    bad = bundle.check_sums(bdir)
    if bad:
        raise integrity(bad[0], file='bundle/SHA256SUMS')
    return manifest


def verify_archive(archive, expected_sha, workdir, now=None, current_generated_at=None, force=False):
    """Every check of §4.3 for an archive. Returns (manifest, archive sha256). Leaves files in WORKDIR."""
    now = time.time() if now is None else now
    actual = sha256_of(archive)
    if expected_sha is not None and actual != expected_sha.lower():
        raise integrity('archive sha256 mismatch', file=archive, expected=expected_sha, actual=actual)
    safe_extract(archive, workdir)
    manifest = check_extracted(workdir)
    gen = parse_iso(manifest['generated_at'])
    if gen > now + 3600:
        raise integrity('generated_at %s is in the future' % manifest['generated_at'], file='manifest.json')
    if current_generated_at and not force and gen <= parse_iso(current_generated_at):
        raise errors.error('ERR-FEED-409-02', gen_at=manifest['generated_at'], current_at=current_generated_at,
                           exit_code=2, details={'snapshot': manifest['generated_at'], 'current': current_generated_at})
    return manifest, actual


def install_extracted(fs, workdir, manifest, archive_sha, archive=None, warnings=None):
    """W1-W5 for an extracted snapshot; caller holds feeds/.lock (BR-FEED-051)."""
    if os.path.isdir(os.path.join(workdir, 'catalog')):
        qcatalog.install_imported(os.path.join(workdir, 'catalog'), fs.root, [] if warnings is None else warnings)
    staging = fs.path('staging')
    if os.path.lexists(staging):
        shutil.rmtree(staging)
    shutil.move(os.path.join(workdir, 'bundle'), staging)
    os.chmod(staging, 0o755 if os.geteuid() == 0 else 0o700)
    open(os.path.join(staging, '.lock'), 'w').close()
    bundle.install(fs, staging, manifest['bundle_id'])
    reset_local_state(fs, {'type': 'snapshot', 'generated_at': manifest['generated_at'], 'sha256': archive_sha})
    if archive:
        keep_imported(fs, archive, manifest, archive_sha)


def reset_local_state(fs, base):
    """After a snapshot the next sync starts from its data (BR-FEED-002, BR-FEED-053)."""
    for n in os.listdir(fs.path('parts')):
        os.unlink(fs.path('parts', n))
    for n in ('nvd-cursor', 'counts', 'sync-status'):
        p = fs.path('state', n + '.json')
        if os.path.exists(p):
            os.unlink(p)
    write_json(fs.path('state', 'base.json'), base)


def keep_imported(fs, archive, manifest, sha):
    d = fs.path('snapshots', 'imported')
    os.makedirs(d, exist_ok=True)
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(parse_iso(manifest['generated_at'])))
    target = os.path.join(d, '%s-%s.tar.gz' % (stamp, sha[:8]))
    if not os.path.exists(target):
        shutil.copyfile(archive, target)
    files = sorted(os.listdir(d))
    for old in files[:-KEEP_IMPORTED]:
        os.unlink(os.path.join(d, old))


def packaged_path(script):
    """<script dir>/share/php-quickpatch/feeds-snapshot.tar.gz, else /usr/local/share/... (§2.2)."""
    cands = []
    if script:
        cands.append(os.path.join(os.path.dirname(os.path.abspath(script)), 'share', 'php-quickpatch',
                                  'feeds-snapshot.tar.gz'))
    cands.append('/usr/local/share/php-quickpatch/feeds-snapshot.tar.gz')
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def packaged_sha(script):
    """QP_SNAPSHOT_SHA256 constant of php-quickpatch.sh (the pin of the packaged snapshot)."""
    try:
        with open(script, encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^QP_SNAPSHOT_SHA256=["\']?([0-9a-f]{64})["\']?\s*$', line)
                if m:
                    return m.group(1)
    except (OSError, TypeError):
        pass
    return None


def packaged_generated_at(path):
    try:
        with tarfile.open(path, mode='r:gz') as tar:
            m = tar.getmember('manifest.json')
            if not m.isfile():
                return None
            return json.loads(tar.extractfile(m).read().decode('utf-8')).get('generated_at')
    except (tarfile.TarError, OSError, KeyError, ValueError, EOFError):
        return None


def maybe_install_packaged(fs, script, warnings, now=None):
    """BR-FEED-053/054: no current, or packaged snapshot newer than current -> install it. Caller holds the lock."""
    path = packaged_path(script)
    if not path:
        return None
    gen = packaged_generated_at(path)
    if not gen:
        return None
    cur = bundle.current(fs)
    cur_gen = cur['manifest'].get('generated_at') if cur else None
    if cur:
        cur['release']()
    if cur_gen and parse_iso(gen) <= parse_iso(cur_gen):
        return None
    work = fs.path('staging-snapshot-%d' % os.getpid())
    if os.path.lexists(work):
        shutil.rmtree(work)
    os.mkdir(work, 0o700)
    try:
        manifest, sha = verify_archive(path, packaged_sha(script) or '0' * 64, work, now=now)
        install_extracted(fs, work, manifest, sha, warnings=warnings)
        return manifest
    except errors.QPError as e:
        warnings.append((e.code, '%s: %s (%s)' % (path, e.message, e.details.get('detail', ''))))
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def describe_packaged(script):
    path = packaged_path(script)
    if not path:
        return {'packaged_generated_at': None, 'sha256_ok': None}
    pin = packaged_sha(script)
    return {'packaged_generated_at': packaged_generated_at(path),
            'sha256_ok': bool(pin) and sha256_of(path) == pin}


def stamp_now():
    return utc_iso()
