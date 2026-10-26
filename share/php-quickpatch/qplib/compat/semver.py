"""Version constraints of Composer (`require.php`) and npm (`engines.node`).

Operators: `^`, `~`, `>=`, `>`, `<=`, `<`, `=`, `!=`, wildcards (`*`, `x`,
`8.*`), hyphen ranges (`7.1 - 8.0`), AND by space/comma, OR by `||` (Composer
also `|`). Stability flags (`@dev`) and `v` prefixes are ignored. Only the
numeric part of versions is compared (FR-CMPT-COMP-001, BR-SCN-025).
"""
import re

_NUM = re.compile(r'\d+')


def vtuple(v, n=3):
    parts = [int(x) for x in _NUM.findall(str(v or ''))[:n]]
    return tuple(parts + [0] * (n - len(parts)))


def _parts(v):
    """'8.2' -> ([8, 2], 2 given parts); wildcards end the list."""
    out = []
    for p in str(v).lstrip('vV=').split('.'):
        if p in ('*', 'x', 'X', ''):
            break
        m = re.match(r'^(\d+)', p)
        if not m:
            break
        out.append(int(m.group(1)))
        if m.group(1) != p:          # 1.2.3-beta: stop after the numeric part
            break
    return out


def _bump(parts, idx):
    p = list(parts[:idx + 1])
    p[idx] += 1
    return tuple(p + [0] * (3 - len(p)))


def _pad(parts):
    return tuple((list(parts) + [0, 0, 0])[:3])


class ConstraintError(ValueError):
    pass


def _term(tok, npm):
    """One comparator -> list of (op, version tuple)."""
    tok = tok.strip()
    if not tok or tok in ('*', 'x', 'X', 'latest'):
        return []
    m = re.match(r'^(\^|~>?|>=|<=|>|<|==?|!=)?\s*(v?[\dxX*][\w.*+-]*)$', tok)
    if not m:
        raise ConstraintError(tok)
    op, ver = m.group(1) or '', m.group(2)
    ver = ver.split('+')[0]
    p = _parts(ver)
    if not p:
        return [] if op in ('', '=', '==', '>=') else [('<', (0, 0, 0))]
    if op == '^':
        if p[0] != 0 or len(p) == 1:
            return [('>=', _pad(p)), ('<', _bump(p, 0))]
        if len(p) >= 2 and (p[1] != 0 or len(p) == 2):
            return [('>=', _pad(p)), ('<', _bump(p, 1))]
        return [('>=', _pad(p)), ('<', _bump(p, 2))]
    if op in ('~', '~>'):
        if npm or len(p) >= 3:
            return [('>=', _pad(p)), ('<', _bump(p, 1 if len(p) >= 2 else 0))]
        return [('>=', _pad(p)), ('<', _bump(p, max(0, len(p) - 2)))]
    if op in ('', '=', '=='):
        if len(p) < 3:                          # partial or wildcard -> range
            return [('>=', _pad(p)), ('<', _bump(p, len(p) - 1))]
        return [('=', _pad(p))]
    if op == '!=':
        return [('!=', _pad(p))]
    if op == '<=' and len(p) < 3:
        return [('<', _bump(p, len(p) - 1))]
    if op == '>' and len(p) < 3:
        return [('>=', _bump(p, len(p) - 1))]
    return [(op, _pad(p))]


def _and_set(text, npm):
    text = text.strip()
    m = re.match(r'^(\S+)\s+-\s+(\S+)$', text)
    if m:                                   # hyphen range
        lo, hi = _parts(m.group(1)), _parts(m.group(2))
        hi_c = ('<=', _pad(hi)) if len(hi) >= 3 else ('<', _bump(hi, len(hi) - 1))
        return [('>=', _pad(lo)), hi_c]
    toks = re.split(r'[\s,]+', re.sub(r'(>=|<=|>|<|!=|==?|\^|~>?)\s+', r'\1', text))
    out = []
    for t in toks:
        t = re.sub(r'@\w+$', '', t)
        out.extend(_term(t, npm))
    return out


def parse(constraint, npm=False):
    """-> list of AND-sets (OR of ANDs). Raises ConstraintError."""
    c = str(constraint or '').strip()
    if not c:
        return [[]]
    ors = re.split(r'\s*\|\|\s*' if npm else r'\s*\|\|?\s*', c)
    return [_and_set(o, npm) for o in ors if o.strip() != '' or len(ors) == 1]


def _cmp(v, op, w):
    return {'>=': v >= w, '>': v > w, '<=': v <= w, '<': v < w, '=': v == w, '!=': v != w}[op]


def satisfies(version, constraint, npm=False):
    """True / False; None when the constraint cannot be read."""
    try:
        sets = parse(constraint, npm)
    except ConstraintError:
        return None
    v = vtuple(version)
    return any(all(_cmp(v, op, w) for op, w in s) for s in sets)
