"""Append-only audit log with a hash chain (FR-JOB-AUD-001..003, BR-AUD-001..006).

File: STATE_DIR/audit/audit-YYYYMM.jsonl, one record per line. A line is the
canonical JSON of the record: keys sorted, separators "," and ":", UTF-8
(json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False)).
hash = SHA-256(prev_hash || canonical JSON of the record without "hash").
The first record ever has prev_hash = 64 x "0"; the first record of a month
carries the hash of the last record of the previous month. php-quickpatch.sh
writes byte-identical lines (audit_write).
"""
import fcntl
import glob
import hashlib
import json
import os
import time

from .envelope import iso_ms, redact

ZERO = '0' * 64
FIELDS = ('action', 'actor', 'args', 'exit_code', 'hash', 'job_id', 'plan_id', 'prev_hash',
          'record_type', 'result', 'run_id', 'seq', 'source', 'sys_user', 'ts')


def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def record_hash(prev_hash, record_without_hash):
    data = (prev_hash + canonical(record_without_hash)).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def audit_files(state_dir):
    return sorted(glob.glob(os.path.join(glob.escape(state_dir), 'audit', 'audit-[0-9][0-9][0-9][0-9][0-9][0-9].jsonl')))


def _last_record(files):
    for path in reversed(files):
        if os.path.getsize(path) == 0:
            continue
        with open(path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536))
            lines = f.read().splitlines()
        for raw in reversed(lines):
            if raw.strip():
                return json.loads(raw.decode('utf-8'))
    return None


def _user():
    try:
        import pwd
        return pwd.getpwuid(os.geteuid()).pw_name
    except (ImportError, KeyError):
        return str(os.geteuid())


def write(state_dir, record_type, action, args=(), result=None, exit_code=None, run_id=None,
          plan_id=None, job_id=None, actor=None, timeout=5.0):
    """Append one record under the audit lock; return (seq, hash). Raises OSError."""
    adir = os.path.join(state_dir, 'audit')
    if not os.path.isdir(adir):
        os.mkdir(adir, 0o700)
    lock_fd = os.open(os.path.join(adir, '.lock'), os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    try:
        deadline = time.time() + timeout
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() >= deadline:
                    raise OSError('audit lock busy for %.0f s' % timeout)
                time.sleep(0.05)
        last = _last_record(audit_files(state_dir))
        user = _user()
        job = job_id if job_id is not None else (os.environ.get('QP_JOB_ID') or None)
        rec = {
            'action': action,
            'actor': actor or os.environ.get('QP_ACTOR') or 'cli:%s' % user,
            'args': [redact(a) for a in args],
            'exit_code': exit_code,
            'job_id': job,
            'plan_id': plan_id,
            'prev_hash': last['hash'] if last else ZERO,
            'record_type': record_type,
            'result': result,
            'run_id': run_id,
            'seq': (last['seq'] + 1) if last else 1,
            'source': 'console' if job else 'cli',
            'sys_user': user,
            'ts': iso_ms(),
        }
        rec['hash'] = record_hash(rec['prev_hash'], rec)
        path = os.path.join(adir, 'audit-%s.jsonl' % rec['ts'][:7].replace('-', ''))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        try:
            os.write(fd, (canonical(rec) + '\n').encode('utf-8'))
            os.fsync(fd)
        finally:
            os.close(fd)
        return rec['seq'], rec['hash']
    finally:
        os.close(lock_fd)


def read_records(state_dir):
    """Yield (file, line_no, raw_bytes, record_or_None) over every audit file in order."""
    for path in audit_files(state_dir):
        with open(path, 'rb') as f:
            for n, raw in enumerate(f, 1):
                raw = raw.rstrip(b'\n')
                if not raw:
                    continue
                try:
                    rec = json.loads(raw.decode('utf-8'))
                    if not isinstance(rec, dict):
                        rec = None
                except (ValueError, UnicodeDecodeError):
                    rec = None
                yield path, n, raw, rec


def job_anchors(state_dir):
    """audit_anchor of every jobs/*/result.json (BR-AUD-006)."""
    out = []
    for path in sorted(glob.glob(os.path.join(glob.escape(state_dir), 'jobs', '*', 'result.json'))):
        try:
            with open(path, encoding='utf-8') as f:
                doc = json.load(f)
        except (OSError, ValueError):
            continue
        anchor = doc.get('audit_anchor') if isinstance(doc, dict) else None
        if isinstance(anchor, dict) and isinstance(anchor.get('seq'), int) and isinstance(anchor.get('hash'), str):
            out.append({'seq': anchor['seq'], 'hash': anchor['hash'], 'source': 'job'})
    return out


def verify(state_dir, anchors=(), date_from=None, date_to=None):
    """Recompute the chain (BR-AUD-003) and compare anchors (BR-AUD-006).

    Every line must equal the canonical serialization of its record, so any
    changed byte is detected. Returns the result dict of qp.audit/1.
    """
    prev_hash, prev_seq = ZERO, 0
    records, broken, last = 0, None, None
    by_seq = {}
    for path, n, raw, rec in read_records(state_dir):
        seq = rec.get('seq') if rec else None
        in_range = True
        if rec and (date_from or date_to):
            day = str(rec.get('ts', ''))[:10]
            in_range = (not date_from or day >= date_from) and (not date_to or day <= date_to)
        ok = (rec is not None and set(rec) == set(FIELDS) and isinstance(seq, int)
              and seq == prev_seq + 1 and rec.get('prev_hash') == prev_hash)
        if ok:
            body = dict(rec)
            stored = body.pop('hash')
            ok = stored == record_hash(prev_hash, body) and raw == canonical(rec).encode('utf-8')
        if not ok and broken is None:
            broken = seq if isinstance(seq, int) else prev_seq + 1
        if rec is not None and isinstance(seq, int):
            by_seq[seq] = rec.get('hash')
            prev_seq, prev_hash = seq, rec.get('hash', '')
            last = {'seq': seq, 'hash': rec.get('hash')}
        else:
            prev_seq += 1
        if in_range:
            records += 1
    checked = []
    all_anchors = list(job_anchors(state_dir)) + [dict(a, source='manual') for a in anchors]
    anchor_broken = False
    for a in all_anchors:
        match = by_seq.get(a['seq']) == a['hash']
        checked.append({'seq': a['seq'], 'hash': a['hash'], 'source': a['source'], 'match': match})
        if not match:
            anchor_broken = True
            if broken is None:
                broken = a['seq'] if a['seq'] in by_seq else prev_seq + 1
    return {'verified': broken is None and not anchor_broken, 'records': records,
            'first_broken_seq': broken, 'anchors_checked': checked, 'last_anchor': last}


def list_records(state_dir, date_from=None, date_to=None, action=None, actor=None):
    out = []
    for _path, _n, _raw, rec in read_records(state_dir):
        if rec is None:
            continue
        day = str(rec.get('ts', ''))[:10]
        if date_from and day < date_from:
            continue
        if date_to and day > date_to:
            continue
        if action and rec.get('action') != action:
            continue
        if actor and rec.get('actor') != actor:
            continue
        out.append(rec)
    return out
