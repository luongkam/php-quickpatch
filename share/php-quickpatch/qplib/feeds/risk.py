"""lifecycle_status, priority and the 0-100 risk score (DOC-SRS-QP-FEED-002 §8, DOC-SRS-QP-SCN-000 §2).

All arithmetic is in integer tenths of a point (BR-FEED-040): the Bash CLI
computes the same R without Python (scan --json, NFR-CMP-005).
"""
import calendar
import re
import time

PRE_RE = re.compile(r'(alpha|beta|RC|-dev|-pre|nightly)', re.I)
FLOOR = {'CRITICAL': 70, 'HIGH': 40, 'MEDIUM': 20, 'LOW': 0}    # BR-FEED-041
S_LIFE = {'ACTIVE': 0, 'ACTIVE_LTS': 0, 'CURRENT': 0, 'SECURITY_ONLY': 50, 'MAINTENANCE_LTS': 50,
          'PRE_RELEASE': 80, 'EOL': 100, 'UNKNOWN': 100}


def day_number(date):
    """'YYYY-MM-DD' -> days since epoch (UTC)."""
    return calendar.timegm(time.strptime(date, '%Y-%m-%d')) // 86400


def days_to_eol(eol_date, today):
    if not eol_date:
        return None
    return day_number(eol_date) - day_number(today)


def lifecycle_status(product, lc, version, today, wp=None):
    """§2.1. lc = lifecycle row (or None). wp = {'newest_branch', 'has_supported', 'min_patched'} for WordPress."""
    if version and PRE_RE.search(str(version)):
        return 'PRE_RELEASE'
    if lc is None:
        return 'UNKNOWN'
    if product == 'wordpress':
        wp = wp or {}
        if wp.get('min_patched') == 'NONE':
            return 'EOL'
        if wp.get('newest_branch') == lc['branch']:
            return 'ACTIVE'
        if wp.get('has_supported'):
            return 'SECURITY_ONLY'
        return 'EOL' if lc.get('eol_date') and lc['eol_date'] < today else 'UNKNOWN'
    ga, eol = lc.get('ga_date'), lc.get('eol_date')
    support = lc.get('active_support_end')
    if eol and today > eol:
        if product == 'php' and lc.get('php_net_supported') == 1:
            pass        # BR-FEED-020: still supported until php.net drops it
        else:
            return 'EOL'
    if ga and today < ga:
        return 'PRE_RELEASE'
    if not ga and lc.get('prerelease_date'):
        return 'PRE_RELEASE'
    if product == 'node':
        lts = lc.get('lts_start')
        if not ga:
            return 'UNKNOWN'
        if not lts or today < lts:
            return 'CURRENT'
        if not support or today <= support:
            return 'ACTIVE_LTS'
        return 'MAINTENANCE_LTS'
    if not ga:
        return 'UNKNOWN'
    if support and today > support:
        return 'SECURITY_ONLY'
    return 'ACTIVE'


def priority(status, d, n_kev, cvss10, public_prerelease=False):
    """§2.2, first matching row from the top."""
    if status == 'UNKNOWN' or (d is not None and d < -365) or n_kev > 0 or \
            (status == 'PRE_RELEASE' and public_prerelease):
        return 'CRITICAL'
    if (d is not None and -365 <= d <= 90) or cvss10 >= 70:
        return 'HIGH'
    if status in ('SECURITY_ONLY', 'MAINTENANCE_LTS') and (d is None or d > 90):
        return 'MEDIUM'
    if status in ('ACTIVE', 'ACTIVE_LTS', 'CURRENT') and d is not None and d <= 365:
        return 'MEDIUM'
    return 'LOW'


def level(r):
    if r >= 70:
        return 'CRITICAL'
    if r >= 40:
        return 'HIGH'
    if r >= 20:
        return 'MEDIUM'
    return 'LOW'


def tenths(v):
    return '%d.%d' % (v // 10, v % 10)


def score(status, d, n_crit, n_high, n_med, n_low, n_kev, cvss10, public_prerelease=False):
    """§8.2 -> dict(R, level, components, priority)."""
    s_cvss = 4 * cvss10
    s_cnt = min(200, 40 * n_crit + 20 * n_high + 5 * n_med + 1 * n_low)
    s_kev = 200 if n_kev >= 1 else 0
    s_life = S_LIFE.get(status, 100)
    if d is None or d > 365:
        s_eol = 0
    elif d < 0:
        s_eol = 100
    elif d <= 90:
        s_eol = 80
    elif d <= 180:
        s_eol = 50
    else:
        s_eol = 20
    r10 = s_cvss + s_cnt + s_kev + s_life + s_eol
    prio = priority(status, d, n_kev, cvss10, public_prerelease)
    r = max((r10 + 5) // 10, FLOOR[prio])
    return {'R': r, 'level': level(r), 'priority': prio, 'R10': r10,
            'components': {'cvss': tenths(s_cvss), 'count': tenths(s_cnt), 'kev': tenths(s_kev),
                           'life': tenths(s_life), 'eol': tenths(s_eol), 'floor': FLOOR[prio],
                           'R_raw': tenths(r10)}}
