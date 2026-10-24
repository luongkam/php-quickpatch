"""Choose and check STATE_DIR (spec §2.1, CR-SRS-13, NFR-SEC-010).

Same 5 steps as select_state_dir in php-quickpatch.sh: root uses
/var/lib/php-quickpatch with no fallback; other users use ~/.php-quickpatch,
else the newest safe ${TMPDIR:-/tmp}/php-quickpatch-$EUID[.*], else a fresh
mkdtemp. Every path is checked with lstat (no symlink, owner = EUID,
mode & 0o022 == 0) before the first read or write; a failing primary path is
ERR-CLI-412-01 (exit 2).
"""
import glob
import os
import stat
import sys
import tempfile

from .errors import error


def unsafe_reason(path, kind='dir'):
    """Return why PATH must not be trusted, or None when it is safe."""
    try:
        st = os.lstat(path)
    except OSError:
        return 'not_dir'
    if stat.S_ISLNK(st.st_mode):
        return 'symlink'
    if kind == 'dir' and not stat.S_ISDIR(st.st_mode):
        return 'not_dir'
    if kind == 'file' and not stat.S_ISREG(st.st_mode):
        return 'not_dir'
    if st.st_uid != os.geteuid():
        return 'owner'
    if st.st_mode & 0o022:
        return 'mode'
    return None


def fail(path, reason):
    try:
        uid = os.lstat(path).st_uid
    except OSError:
        uid = '-'
    return error('ERR-CLI-412-01', path=path, reason=reason,
                 details={'path': path, 'reason': reason, 'uid': uid, 'euid': os.geteuid()})


def _tighten(path, want, warnings):
    mode = stat.S_IMODE(os.lstat(path).st_mode)
    if mode & ~want & 0o777:
        os.chmod(path, want)
        warnings.append('state dir %s: mode %o tightened to %o' % (path, mode, want))


def select(warnings=None):
    """Return the checked STATE_DIR path; raise QPError (ERR-CLI-412-01)."""
    warnings = [] if warnings is None else warnings
    if os.geteuid() == 0:
        p = '/var/lib/php-quickpatch'
        if not os.path.lexists(p):
            try:
                os.mkdir(p, 0o750)
                os.chmod(p, 0o750)
            except OSError:
                raise fail(p, 'create_failed')
        reason = unsafe_reason(p)
        if reason:
            raise fail(p, reason)
        _tighten(p, 0o750, warnings)
        return p
    home = os.environ.get('HOME', '')
    if home:
        p = os.path.join(home, '.php-quickpatch')
        exists = os.path.lexists(p)
        if not exists:
            try:
                os.mkdir(p, 0o700)
                os.chmod(p, 0o700)
                exists = True
            except OSError:
                pass
        if exists:
            reason = unsafe_reason(p)
            if reason:
                raise fail(p, reason)
            if os.access(p, os.W_OK | os.X_OK):
                _tighten(p, 0o700, warnings)
                return p
    tmp = os.environ.get('TMPDIR') or '/tmp'
    base = os.path.join(tmp, 'php-quickpatch-%d' % os.geteuid())
    best, best_m = None, -1
    for c in [base] + sorted(glob.glob(glob.escape(base) + '.*')):
        if not os.path.lexists(c):
            continue
        reason = unsafe_reason(c)
        if reason:
            warnings.append('skipped state dir candidate %s (%s)' % (c, reason))
            sys.stderr.write('[WARN] skipped unsafe state dir candidate %s (%s)\n' % (c, reason))
            continue
        if not os.access(c, os.W_OK | os.X_OK):
            continue
        m = os.lstat(c).st_mtime
        if m > best_m:
            best, best_m = c, m
    if best:
        _tighten(best, 0o700, warnings)
        return best
    try:
        best = tempfile.mkdtemp(prefix='php-quickpatch-%d.' % os.geteuid(), dir=tmp)
    except OSError:
        raise fail(base + '.XXXXXX', 'create_failed')
    reason = unsafe_reason(best)
    if reason:
        raise fail(best, reason)
    return best


def private_dir(state_dir, *parts):
    """Create (mode 0700) and return STATE_DIR/<parts>; refuse unsafe entries."""
    path = state_dir
    for part in parts:
        path = os.path.join(path, part)
        if not os.path.lexists(path):
            os.mkdir(path, 0o700)
        reason = unsafe_reason(path)
        if reason:
            raise fail(path, reason)
    return path
