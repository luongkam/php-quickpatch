"""Version comparison and affected-range matching (DOC-SRS-QP-FEED-002 §5).

Upstream versions compare as tuples of their numeric groups, missing parts = 0
(like `sort -V` on dotted numbers, §5.1). Distro package versions are never
compared numerically here (§5.3).
"""
import functools
import re

_NUM = re.compile(r'\d+')


@functools.lru_cache(maxsize=65536)
def vkey(version):
    """Sort key of an upstream version: '8.4.27' -> (8, 4, 27)."""
    return tuple(int(x) for x in _NUM.findall(str(version or '')))


def vcmp(a, b):
    ka, kb = vkey(a), vkey(b)
    n = max(len(ka), len(kb))
    ka += (0,) * (n - len(ka))
    kb += (0,) * (n - len(kb))
    return (ka > kb) - (ka < kb)


def vlt(a, b):
    return vcmp(a, b) < 0


def vmax(versions):
    best = None
    for v in versions:
        if v and (best is None or vcmp(v, best) > 0):
            best = v
    return best


def vsorted(versions):
    return sorted(versions, key=functools.cmp_to_key(vcmp))


def is_release(version):
    """Plain X.Y.Z (no RC/alpha/beta suffix)."""
    return bool(re.match(r'^\d+\.\d+\.\d+$', str(version or '')))


def branch_of(product, version):
    """php/wordpress -> 'X.Y'; node -> 'N' (or '0.N' for 0.x)."""
    parts = str(version or '').lstrip('v').split('.')
    if product == 'node':
        if parts[0] == '0' and len(parts) > 1:
            return '0.' + parts[1]
        return parts[0]
    return '.'.join(parts[:2]) if len(parts) >= 2 else parts[0]


# --- NVD CPE configurations (§5.1) ---------------------------------------
CPE_PRODUCTS = {'php': 'php:php', 'node': 'nodejs:node.js', 'wordpress': 'wordpress:wordpress'}
_FOREIGN_OS = ('cpe:2.3:o:microsoft:', 'cpe:2.3:o:apple:')


def cpe_vendor_product(criteria):
    parts = criteria.split(':')
    return ':'.join(parts[3:5]) if len(parts) > 5 else ''


def cpe_match_to_range(m):
    """One NVD cpeMatch -> dict(v_start, start_incl, v_end, end_incl, v_exact, unbounded) or None (NA)."""
    parts = m.get('criteria', '').split(':')
    v = parts[5] if len(parts) > 5 else '*'
    if v == '-':
        return None
    rng = {'v_start': None, 'start_incl': 1, 'v_end': None, 'end_incl': 0, 'v_exact': None, 'unbounded': 0}
    if v not in ('*', ''):
        rng['v_exact'] = v
        return rng
    if 'versionStartIncluding' in m:
        rng['v_start'], rng['start_incl'] = m['versionStartIncluding'], 1
    elif 'versionStartExcluding' in m:
        rng['v_start'], rng['start_incl'] = m['versionStartExcluding'], 0
    if 'versionEndIncluding' in m:
        rng['v_end'], rng['end_incl'] = m['versionEndIncluding'], 1
    elif 'versionEndExcluding' in m:
        rng['v_end'], rng['end_incl'] = m['versionEndExcluding'], 0
    if rng['v_start'] is None and rng['v_end'] is None:
        rng['unbounded'] = 1
    return rng


def nvd_ranges(configurations, product):
    """Ranges of PRODUCT in NVD configurations, with platform from AND nodes."""
    want = CPE_PRODUCTS[product]
    out = []
    for cfg in configurations or []:
        nodes = cfg.get('nodes', [])
        platform = 'any'
        if cfg.get('operator') == 'AND':
            for n in nodes:
                ms = n.get('cpeMatch', [])
                if ms and all(not m.get('vulnerable') for m in ms):
                    crit = [m.get('criteria', '') for m in ms]
                    if all(c.startswith('cpe:2.3:o:microsoft:') for c in crit):
                        platform = 'windows'
                    elif all(c.startswith('cpe:2.3:o:apple:') for c in crit):
                        platform = 'macos'
        for n in nodes:
            for m in n.get('cpeMatch', []):
                if not m.get('vulnerable') or cpe_vendor_product(m.get('criteria', '')) != want:
                    continue
                rng = cpe_match_to_range(m)
                if rng is None:
                    continue
                rng['platform'] = platform
                out.append(rng)
    return out


def in_range(version, rng):
    """Is VERSION inside one affected_range row (unbounded rows never match)."""
    if rng.get('unbounded'):
        return False
    if rng.get('v_exact'):
        return vcmp(version, rng['v_exact']) == 0
    s, e = rng.get('v_start'), rng.get('v_end')
    if s is not None:
        c = vcmp(version, s)
        if c < 0 or (c == 0 and not rng.get('start_incl', 1)):
            return False
    if e is not None:
        c = vcmp(version, e)
        if c > 0 or (c == 0 and not rng.get('end_incl', 0)):
            return False
    return True


# --- CNA affected (§5.2) ---------------------------------------------------
def cna_ranges(affected_items, product_names):
    """CNA 'affected' entries -> ranges; product_names lowercased, e.g. {'php'}."""
    out = []
    for a in affected_items or []:
        if str(a.get('product', '')).lower() not in product_names:
            continue
        for v in a.get('versions', []):
            if v.get('status') != 'affected':
                continue
            ver = str(v.get('version', ''))
            rng = {'v_start': None, 'start_incl': 1, 'v_end': None, 'end_incl': 0, 'v_exact': None,
                   'unbounded': 0, 'platform': 'any'}
            if ver.endswith('.*'):
                rng['v_start'] = ver[:-2] + '.0'
                rng['prefix'] = ver[:-1]
            elif ver not in ('0', '*', '', 'n/a'):
                rng['v_start'] = ver
            if v.get('lessThan') not in (None, '*'):
                rng['v_end'], rng['end_incl'] = v['lessThan'], 0
            elif v.get('lessThanOrEqual') not in (None, '*'):
                rng['v_end'], rng['end_incl'] = v['lessThanOrEqual'], 1
            elif rng['v_start'] and 'prefix' not in rng:
                rng['v_exact'], rng['v_start'] = rng['v_start'], None
            if rng['v_start'] is None and rng['v_end'] is None and rng['v_exact'] is None:
                rng['unbounded'] = 1
            out.append(rng)
    return out


def cna_match(version, rng):
    if rng.get('prefix') and not str(version).startswith(rng['prefix']):
        return False
    return in_range(version, rng)


# --- OSV events (§5.3) -----------------------------------------------------
def osv_ranges(affected):
    """OSV affected[].ranges[] (ECOSYSTEM/SEMVER) -> list of ranges."""
    out = []
    for r in affected.get('ranges', []):
        if r.get('type') not in ('ECOSYSTEM', 'SEMVER'):
            continue
        start = None
        for ev in r.get('events', []):
            if 'introduced' in ev:
                start = None if ev['introduced'] in ('0', '') else ev['introduced']
                out.append({'v_start': start, 'start_incl': 1, 'v_end': None, 'end_incl': 0, 'v_exact': None,
                            'unbounded': 0, 'platform': 'any'})
            elif 'fixed' in ev and out:
                out[-1]['v_end'], out[-1]['end_incl'] = ev['fixed'], 0
            elif 'last_affected' in ev and out:
                out[-1]['v_end'], out[-1]['end_incl'] = ev['last_affected'], 1
    for v in affected.get('versions', []):
        out.append({'v_start': None, 'start_incl': 1, 'v_end': None, 'end_incl': 0, 'v_exact': v,
                    'unbounded': 0, 'platform': 'any'})
    return out


# --- node-semver subset of the Node.js Security WG (§5.4) ------------------
class SemverError(ValueError):
    pass


_SV = re.compile(r'^(\^|~|>=|<=|>|<|=)?v?(\d+|x|\*)(?:\.(\d+|x|\*))?(?:\.(\d+|x|\*))?$')


def _comparator(token):
    """Return list of (op, version tuple) for one token."""
    m = _SV.match(token)
    if not m:
        raise SemverError(token)
    op, a, b, c = m.group(1) or '', m.group(2), m.group(3), m.group(4)
    wild = lambda x: x is None or x in ('x', '*')  # noqa: E731
    if wild(a):
        return []                      # '*' matches everything
    A = int(a)
    if wild(b):                       # N.x
        lo, hi = (A, 0, 0), (A + 1, 0, 0)
    else:
        B = int(b)
        if wild(c):                   # N.N.x
            lo, hi = (A, B, 0), (A, B + 1, 0)
            if op == '^':
                hi = (A + 1, 0, 0) if A > 0 else (0, B + 1, 0)
        else:
            lo = hi = None
    if lo is not None:                # partial version: a whole range
        return {'': [('>=', lo), ('<', hi)], '=': [('>=', lo), ('<', hi)], '^': [('>=', lo), ('<', hi)],
                '~': [('>=', lo), ('<', hi)], '>=': [('>=', lo)], '<': [('<', lo)],
                '>': [('>=', hi)], '<=': [('<', hi)]}[op]
    B = int(b)
    C = int(c)
    v = (A, B, C)
    if op == '^':
        hi = (A + 1, 0, 0) if A > 0 else ((0, B + 1, 0) if B > 0 else (0, 0, C + 1))
        return [('>=', v), ('<', hi)]
    if op == '~':
        return [('>=', v), ('<', (A, B + 1, 0))]
    return [(op or '=', v)]


def parse_semver(expr):
    """'^22.23.2 || 24.x' -> list of alternatives, each a list of comparators."""
    expr = str(expr or '').strip()
    if not expr:
        raise SemverError('empty')
    alts = []
    for part in expr.split('||'):
        toks = part.split()
        if not toks:
            raise SemverError(expr)
        # "A - B" hyphen ranges
        if len(toks) == 3 and toks[1] == '-':
            alts.append(_comparator('>=' + toks[0]) + _comparator('<=' + toks[2]))
            continue
        comps = []
        for t in toks:
            comps.extend(_comparator(t))
        alts.append(comps)
    return alts


def semver_satisfies(version, alts):
    v = vkey(version)[:3]
    v += (0,) * (3 - len(v))
    for comps in alts:
        ok = True
        for op, ref in comps:
            ok = {'>=': v >= ref, '<=': v <= ref, '>': v > ref, '<': v < ref, '=': v == ref}[op]
            if not ok:
                break
        if ok:
            return True
    return False


# --- Composer constraints (FR-CMPT-COMP-001; also used for npm engines) ----
def constraint_ok(version, constraint):
    """Composer/npm style constraint check against VERSION (best effort)."""
    c = str(constraint or '').strip().replace(',', ' ')
    if c in ('', '*'):
        return True
    alts = []
    for part in re.split(r'\s*\|\|?\s*', c):
        toks = part.split()
        comps = []
        for t in toks:
            t = t.lstrip('v') if not t.startswith(('>', '<', '=', '^', '~')) else t
            comps.extend(_comparator(t.replace('.*', '.x')))
        alts.append(comps)
    return semver_satisfies(version, alts)
