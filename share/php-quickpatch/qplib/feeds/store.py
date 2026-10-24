"""feeds/ directory: raw responses, per-source parsed facts, sync state (DOC-SRS-QP-FEED-003 §2).

raw/SRC-xxx/<name>[.gz] + <name>.meta.json   last response of each source (FR-FEED-CACH-001)
raw/SRC-xxx/rejected/                        <= 3 rejected responses (BR-FEED-007)
parts/SRC-xxx.json.gz                         facts parsed from the last good response;
                                              the normalizer builds a bundle from these
state/sync-status.json, state/last-sync.log  per-source status and sync log
"""
import gzip
import json
import os
import time

from .. import statedir


def utc_iso(t=None):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() if t is None else t))


def parse_iso(s):
    """'2026-10-22T09:30:00Z' (or with .ms, or a date) -> epoch seconds."""
    import calendar
    s = str(s).rstrip('Z')
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return calendar.timegm(time.strptime(s, fmt))
        except ValueError:
            pass
    raise ValueError('bad ISO time: %r' % s)


def atomic_write(path, data, mode=0o644):
    tmp = '%s.tmp-%d' % (path, os.getpid())
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def write_json(path, obj, mode=0o644):
    atomic_write(path, (json.dumps(obj, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8'), mode)


def read_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class FeedsDir(object):
    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.root = os.path.join(state_dir, 'feeds')
        mode = 0o755 if os.geteuid() == 0 else 0o700
        if not os.path.lexists(self.root):
            os.mkdir(self.root, mode)
            os.chmod(self.root, mode)
        reason = statedir.unsafe_reason(self.root)
        if reason == 'mode' and os.geteuid() == 0:
            reason = None   # feeds/ is 0755 for root (NFR-FEED-004); STATE_DIR itself is 0750
        if reason:
            raise statedir.fail(self.root, reason)
        for d in ('raw', 'parts', 'cache', 'bundles', 'state', 'snapshots'):
            p = os.path.join(self.root, d)
            if not os.path.isdir(p):
                os.makedirs(p, exist_ok=True)

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    # --- raw ---------------------------------------------------------------
    def save_raw(self, src, name, body, meta):
        d = self.path('raw', src, os.path.dirname(name))
        os.makedirs(d, exist_ok=True)
        base = self.path('raw', src, name)
        gz = len(body) > 1024 * 1024
        target = base + '.gz' if gz else base
        atomic_write(target, gzip.compress(body) if gz else body)
        other = base if gz else base + '.gz'
        if os.path.exists(other):
            os.unlink(other)
        import hashlib
        meta = dict(meta, sha256=hashlib.sha256(body).hexdigest(), bytes=len(body), file=os.path.basename(target))
        write_json(base + '.meta.json', meta)
        return meta

    def raw_meta(self, src, name):
        return read_json(self.path('raw', src, name + '.meta.json'), {})

    def load_raw(self, src, name):
        base = self.path('raw', src, name)
        for p, z in ((base + '.gz', True), (base, False)):
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    data = f.read()
                return gzip.decompress(data) if z else data
        return None

    def reject(self, src, name, body, reason):
        d = self.path('raw', src, 'rejected')
        os.makedirs(d, exist_ok=True)
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        atomic_write(os.path.join(d, '%s-%s.gz' % (stamp, os.path.basename(name))), gzip.compress(body or b''))
        write_json(os.path.join(d, '%s-%s.reason.json' % (stamp, os.path.basename(name))), {'reason': reason})
        files = sorted(f for f in os.listdir(d) if f.endswith('.gz'))
        for old in files[:-3]:
            os.unlink(os.path.join(d, old))
            r = os.path.join(d, old[:-3] + '.reason.json')
            if os.path.exists(r):
                os.unlink(r)

    # --- parsed facts ------------------------------------------------------
    def save_parts(self, src, facts, meta):
        doc = dict(meta, src_id=src, facts=facts)
        atomic_write(self.path('parts', src + '.json.gz'),
                     gzip.compress(json.dumps(doc, ensure_ascii=False, sort_keys=True).encode('utf-8')))

    def load_parts(self, src):
        p = self.path('parts', src + '.json.gz')
        if not os.path.exists(p):
            return None
        with open(p, 'rb') as f:
            return json.loads(gzip.decompress(f.read()).decode('utf-8'))

    # --- state ---------------------------------------------------------------
    def status(self):
        return read_json(self.path('state', 'sync-status.json'), {})

    def save_status(self, status):
        write_json(self.path('state', 'sync-status.json'), status)

    def state(self, name, default=None):
        return read_json(self.path('state', name + '.json'), default)

    def save_state(self, name, obj):
        write_json(self.path('state', name + '.json'), obj)

    def log_sync(self, line):
        p = self.path('state', 'last-sync.log')
        if os.path.exists(p) and os.path.getsize(p) > 1024 * 1024:
            for i in range(4, 0, -1):
                a, b = '%s.%d' % (p, i), '%s.%d' % (p, i + 1)
                if os.path.exists(a):
                    os.replace(a, b)
            os.replace(p, p + '.1')
        with open(p, 'a', encoding='utf-8') as f:
            f.write('%s %s\n' % (utc_iso(), line))
