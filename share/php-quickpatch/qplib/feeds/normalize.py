"""Facts of every source -> normalized model (DOC-SRS-QP-FEED-002 §2-§6).

build(parts) returns plain lists of rows for the bundle writer:
lifecycle, releases, advisories, aliases, scores, ranges, fixes, kev,
fix_evidence, min_patched, exposure, framework, conflicts, coverage.
"""
import time

from . import versions as V
from .store import parse_iso, utc_iso

RUNTIMES = ('php', 'node', 'wordpress')
LIFECYCLE_PRIORITY = {'php': ['SRC-001', 'SRC-003', 'STATIC'], 'node': ['SRC-010', 'SRC-001']}
DATE_FIELDS = ('ga_date', 'lts_start', 'active_support_end', 'eol_date', 'prerelease_date')
# FR-FEED-EOL-002: PHP 4.4 (SRC-002 version=4.4, php.net eol.php).
STATIC_LIFECYCLE = [{'product': 'php', 'branch': '4.4', 'ga_date': '2005-07-11', 'eol_date': '2008-08-07'}]
PROXY = {'critical': 9.5, 'high': 8.0, 'medium': 5.5, 'low': 2.0, 'unknown': 7.5}   # BR-FEED-043
SEC_RELEASE_SCORE = 7.5
SEC_RELEASE_DELAY_S = 6 * 3600       # BR-FEED-024
EXCLUDED = ('REJECTED', 'WITHDRAWN')  # BR-FEED-031


def fmt_score(x):
    return None if x is None else '%.1f' % float(x)


def severity_of(score):
    """§1.3 bands; None -> 'unknown'."""
    if score is None:
        return 'unknown'
    s = round(float(score) * 10)
    if s >= 90:
        return 'critical'
    if s >= 70:
        return 'high'
    if s >= 40:
        return 'medium'
    if s >= 1:
        return 'low'
    return 'none'


def effective_score(adv):
    """cvss_rep, or the 'unknown' proxy (BR-FEED-043) when nothing scored the advisory."""
    return float(adv['cvss_rep']) if adv.get('cvss_rep') is not None else PROXY['unknown']


def cvss_rep(scores, kind):
    """BR-FEED-028 -> (score or None, source label)."""
    if kind == 'SEC_RELEASE':
        return SEC_RELEASE_SCORE, 'PROXY:sec_release'
    num = [s for s in scores if s.get('base_score') is not None and s.get('cvss_version') != 'NONE']
    for ver in ('3.1', '3.0'):
        for s in num:
            if s['source'] == 'NVD' and s.get('type') == 'Primary' and s['cvss_version'] == ver:
                return float(s['base_score']), 'NVD:%s:Primary' % ver
    v3 = [s for s in num if s['cvss_version'] in ('3.0', '3.1')]
    if v3:
        b = max(v3, key=lambda s: float(s['base_score']))
        return float(b['base_score']), '%s:%s:%s' % (b['source'], b['cvss_version'], b.get('type') or '-')
    v4 = [s for s in num if s['cvss_version'] == '4.0']
    if v4:
        b = max(v4, key=lambda s: float(s['base_score']))
        return float(b['base_score']), '%s:4.0:%s' % (b['source'], b.get('type') or '-')
    v2 = [s for s in num if s['cvss_version'] == '2.0' and s['source'] == 'NVD']
    if v2:
        return float(v2[0]['base_score']), 'NVD:2.0:%s' % (v2[0].get('type') or '-')
    texts = [s.get('severity_text') for s in scores if s.get('severity_text')]
    if texts:
        order = ['critical', 'high', 'unknown', 'medium', 'low']
        best = min((t if t in PROXY else 'unknown' for t in texts), key=order.index)
        return PROXY[best], 'PROXY:%s' % best
    return None, None


# --- range matching (§5) --------------------------------------------------
def range_hits(rng, version):
    if rng.get('origin') == 'NODE_WG':
        alts = rng.get('_vul')
        if alts is None:
            try:
                rng['_vul'] = alts = V.parse_semver(rng.get('semver_vulnerable'))
                rng['_pat'] = V.parse_semver(rng['semver_patched']) if rng.get('semver_patched') else []
            except V.SemverError:
                rng['_vul'] = alts = []
                rng['_pat'] = []
        return V.semver_satisfies(version, alts) and not (rng['_pat'] and V.semver_satisfies(version, rng['_pat']))
    if rng.get('origin') == 'CNA':
        return V.cna_match(version, rng)
    return V.in_range(version, rng)


def selected_ranges(ranges, product):
    """BR-FEED-022: which origin decides 'affected' for one advisory and product (Linux)."""
    rs = [r for r in ranges if r.get('product') == product and r.get('platform', 'any') == 'any']
    if product == 'node':
        order = ['NODE_WG', 'NVD_CPE', 'CNA', 'GHSA', 'SEC_RELEASE']
    elif product.startswith(('npm:', 'composer:')):
        order = ['OSV']
    else:
        order = ['NVD_CPE', 'CNA', 'GHSA', 'WORDFENCE', 'SEC_RELEASE']
    has_any = {r.get('origin') for r in ranges if r.get('product') == product}
    for o in order:
        if o in has_any:
            return [r for r in rs if r.get('origin') == o and not r.get('unbounded')]
    return []


def affects(sel, version):
    return any(range_hits(r, version) for r in sel)


def branch_start(product, branch):
    return branch + ('.0.0' if product == 'node' else '.0')


# --- the model --------------------------------------------------------------
def build(parts, today=None, now=None, linux=True, sec_seen=None):
    now = time.time() if now is None else now
    today = today or time.strftime('%Y-%m-%d', time.gmtime(now))
    facts = {src: (doc or {}).get('facts', []) for src, doc in parts.items()}
    conflicts = []
    lifecycle = _lifecycle(facts, conflicts)
    releases = _releases(facts)
    for (p, b) in {(r['product'], r['branch']) for r in releases}:
        if (p, b) not in lifecycle:
            lifecycle[(p, b)] = dict(product=p, branch=b, ga_date=None, lts_start=None, active_support_end=None,
                                     eol_date=None, prerelease_date=None,
                                     php_net_supported=(0 if p == 'php' else None), latest_hint=None,
                                     origin={'php': 'SRC-002', 'node': 'SRC-009', 'wordpress': 'SRC-012'}.get(p, 'SRC-001'),
                                     codename=None)
    by_branch = {}
    for r in releases:
        by_branch.setdefault((r['product'], r['branch']), []).append(r['version'])
    for k in by_branch:
        by_branch[k] = V.vsorted(by_branch[k])
    advisories, alias_rows = _advisories(facts)
    fix_ev = _fix_evidence(facts, advisories)
    _sec_releases(releases, by_branch, advisories, fix_ev, now, sec_seen)
    kev = {f['cve_id']: f for f in facts.get('SRC-006', []) if f.get('type') == 'kev'}
    for a in advisories.values():
        ids = {a['adv_id']} | set(a['aliases'])
        hit = [kev[i] for i in ids if i in kev]
        a['in_kev'] = 1 if hit else 0
        a['kev_due'] = hit[0].get('due_date') if hit else None
    for a in advisories.values():
        rep, src = cvss_rep(a['scores'], a['kind'])
        a['cvss_rep'] = fmt_score(rep)
        a['cvss_rep_src'] = src
        a['severity'] = severity_of(rep)
        a['sel'] = {p: selected_ranges(a['ranges'], p) for p in a['products']}
    fixes = _fixed_in_branch(lifecycle, by_branch, advisories, fix_ev, conflicts)
    min_patched = _min_patched(lifecycle, by_branch, advisories, fixes, releases, today)
    exposure = _exposure(releases, advisories)
    ranges = []
    for a in advisories.values():
        for r in a['ranges']:
            used = any(r is s for s in a['sel'].get(r.get('product'), []))
            fib = None
            if r.get('v_end') and r.get('product') in RUNTIMES:
                fib = fixes.get((a['adv_id'], r['product'], V.branch_of(r['product'], r['v_end'])), {}).get('fixed')
            ranges.append(dict(adv_id=a['adv_id'], product=r.get('product'), origin=r.get('origin'),
                               v_start=r.get('v_start'), start_incl=int(r.get('start_incl', 1)),
                               v_end=r.get('v_end'), end_incl=int(r.get('end_incl', 0)), v_exact=r.get('v_exact'),
                               platform=r.get('platform', 'any'), unbounded=int(r.get('unbounded', 0)),
                               fixed_in_branch=fib, assessed=1, used=1 if used else 0,
                               semver_vulnerable=r.get('semver_vulnerable'), semver_patched=r.get('semver_patched'),
                               v_prefix=r.get('prefix')))
    framework = sorted(({'framework': f['framework'], 'cycle': f['cycle'], 'php_min': f['php_min'],
                         'php_max': f['php_max'], 'eol_date': f.get('eol_date')}
                        for f in facts.get('SRC-001', []) if f.get('type') == 'framework'),
                       key=lambda r: (r['framework'], V.vkey(r['cycle'])))
    lc_rows = sorted(lifecycle.values(), key=lambda r: (r['product'], V.vkey(r['branch'])))
    adv_rows = sorted(advisories.values(), key=lambda a: a['adv_id'])
    coverage = {'php_branches': sum(1 for r in lc_rows if r['product'] == 'php'),
                'node_branches': sum(1 for r in lc_rows if r['product'] == 'node'),
                'advisories': len(adv_rows), 'kev': len(kev)}
    return {'today': today, 'lifecycle': lc_rows, 'releases': releases, 'advisories': adv_rows,
            'aliases': sorted(alias_rows), 'ranges': ranges, 'fixes': sorted(fixes.values(), key=lambda f: (
                f['adv_id'], f['product'], V.vkey(f['branch']))),
            'kev': sorted(kev.values(), key=lambda k: k['cve_id']), 'fix_evidence': sorted(fix_ev),
            'min_patched': min_patched, 'exposure': exposure, 'framework': framework,
            'conflicts': conflicts, 'coverage': coverage}


def _lifecycle(facts, conflicts):
    per = {}   # (product, branch) -> {src: fact}
    for src in ('SRC-001', 'SRC-003', 'SRC-010'):
        for f in facts.get(src, []):
            if f.get('type') == 'lifecycle':
                per.setdefault((f['product'], f['branch']), {})[src] = f
    for s in STATIC_LIFECYCLE:
        per.setdefault((s['product'], s['branch']), {})['STATIC'] = dict(s, lts_start=None, active_support_end=None,
                                                                           prerelease_date=None)
    supported = {f['branch'] for f in facts.get('SRC-002', []) if f.get('type') == 'supported'}
    out = {}
    for (p, b), by_src in per.items():
        order = LIFECYCLE_PRIORITY.get(p, ['SRC-001'])
        if p == 'php' and 'STATIC' in by_src and ('SRC-001' in by_src or 'SRC-003' in by_src):
            by_src = {k: v for k, v in by_src.items() if k != 'STATIC'}   # FR-FEED-EOL-002: only when missing
        row = dict(product=p, branch=b, latest_hint=(by_src.get('SRC-001') or {}).get('latest_hint'),
                   codename=(by_src.get('SRC-010') or {}).get('codename'))
        origin = None
        for field in DATE_FIELDS:
            val, chosen = None, None
            for src in order:
                v = (by_src.get(src) or {}).get(field)
                if v:
                    val, chosen = v, src
                    break
            row[field] = val
            if field == 'eol_date' and chosen:
                origin = chosen
            # BR-FEED-020: > 3 days apart -> ERR-FEED-409-01
            vals = {src: (by_src.get(src) or {}).get(field) for src in order if (by_src.get(src) or {}).get(field)}
            if len(vals) > 1:
                ds = sorted(parse_iso(v) for v in vals.values())
                if ds[-1] - ds[0] > 3 * 86400:
                    conflicts.append({'attribute': '%s %s %s' % (p, b, field), 'values': vals, 'chosen': val,
                                      'message': '%s %s %s: %s; using %s (%s)' % (
                                          p, b, field, ', '.join('%s=%s' % kv for kv in sorted(vals.items())),
                                          val, chosen)})
        row['origin'] = origin or next((s for s in order if s in by_src), 'SRC-001')
        row['php_net_supported'] = None
        if p == 'php':
            row['php_net_supported'] = 1 if b in supported else (0 if V.vkey(b) >= (5, 0) else None)
        out[(p, b)] = row
    return out


def _releases(facts):
    rows = {}
    for src, product in (('SRC-002', 'php'), ('SRC-009', 'node'), ('SRC-012', 'wordpress')):
        for f in facts.get(src, []):
            if f.get('type') == 'release' and f.get('product') == product:
                rows[(product, f['version'])] = dict(product=product, branch=f['branch'], version=f['version'],
                                                     release_date=f.get('release_date'),
                                                     is_security=int(f.get('is_security') or 0),
                                                     wp_status=f.get('wp_status'), abi_modules=f.get('abi_modules'),
                                                     lts_codename=f.get('lts_codename'))
    return sorted(rows.values(), key=lambda r: (r['product'], V.vkey(r['version'])))


ADV_SOURCES = ('SRC-004', 'SRC-005', 'SRC-011', 'SRC-008', 'SRC-013')
STATUS_PRIORITY = ('SRC-004', 'SRC-005')


def _canonical_order(i):
    for n, pre in enumerate(('CVE-', 'GHSA-', 'MAL-', 'QP-SR-')):
        if i.startswith(pre):
            return n
    return 9


def _advisories(facts):
    """BR-FEED-023: merge records sharing an id; adv_id = CVE, else GHSA, else OSV id."""
    recs = []
    for src in ADV_SOURCES:
        for f in facts.get(src, []):
            if f.get('type') == 'advisory' and f.get('adv_id'):
                recs.append((src, f))
    alias_to = {}
    for f in facts.get('SRC-003', []):
        if f.get('type') == 'alias':
            alias_to.setdefault(f['alias_id'], f['adv_id'])
    for src, f in recs:
        if f['adv_id'].startswith('CVE-'):
            for a in f.get('aliases', []):
                if not a.startswith(('CVE-', 'MAL-')):
                    alias_to.setdefault(a, f['adv_id'])
    groups = {}
    for src, f in recs:
        aid = f['adv_id']
        if aid.startswith('MAL-'):
            canon = aid
        elif aid.startswith('CVE-'):
            canon = aid
        else:
            cves = sorted(a for a in f.get('aliases', []) if a.startswith('CVE-'))
            canon = cves[0] if cves else alias_to.get(aid)
            if canon is None:
                for a in f.get('aliases', []):
                    if a in alias_to:
                        canon = alias_to[a]
                        break
            canon = canon or aid
        groups.setdefault(canon, []).append((src, f))
    out, alias_rows = {}, set()
    for canon, items in groups.items():
        a = {'adv_id': canon, 'products': [], 'aliases': set(), 'scores': [], 'ranges': [], 'sources': set()}
        kinds = set()
        by_src = {}
        for src, f in items:
            by_src.setdefault(src, f)
            a['sources'].add(src)
            for p in f.get('products', []):
                if p not in a['products']:
                    a['products'].append(p)
            for i in [f['adv_id']] + list(f.get('aliases', [])):
                if i != canon:
                    a['aliases'].add(i)
            for s in f.get('scores', []):
                if not any(s['source'] == x['source'] and s['cvss_version'] == x['cvss_version'] for x in a['scores']):
                    a['scores'].append(s)
            for r in f.get('ranges', []):
                if r not in a['ranges']:
                    a['ranges'].append(dict(r))
            kinds.add(f.get('kind', 'VULN'))
        a['kind'] = 'MALWARE' if canon.startswith('MAL-') else ('SEC_RELEASE' if kinds == {'SEC_RELEASE'} else 'VULN')
        statuses = [f.get('status') for _, f in items]
        if 'REJECTED' in statuses:
            a['status'] = 'REJECTED'
        else:
            prim = next((by_src[s].get('status') for s in STATUS_PRIORITY if s in by_src), None)
            if prim:
                a['status'] = prim
            elif canon.startswith('CVE-'):
                a['status'] = 'WITHDRAWN' if statuses and all(s == 'WITHDRAWN' for s in statuses) else 'PENDING_NVD'
            else:
                a['status'] = 'WITHDRAWN' if statuses and all(s == 'WITHDRAWN' for s in statuses) else 'PUBLISHED'

        def first(field, order=('SRC-004', 'SRC-005', 'SRC-008', 'SRC-011', 'SRC-013')):
            for s in order:
                if s in by_src and by_src[s].get(field):
                    return by_src[s][field]
            return None
        pubs = [f.get('published_at') for _, f in items if f.get('published_at')]
        mods = [f.get('modified_at') for _, f in items if f.get('modified_at')]
        a['published_at'] = _iso20(min(pubs)) if pubs else None
        a['modified_at'] = _iso20(max(mods)) if mods else None
        a['summary'] = first('summary')
        a['cwe_ids'] = first('cwe_ids')
        a['workaround'] = first('workaround', ('SRC-005', 'SRC-004'))
        a['aliases'] = sorted(a['aliases'])
        for al in a['aliases']:
            alias_rows.add((canon, al))
        out[canon] = a
    return out, alias_rows


def _iso20(s):
    try:
        return utc_iso(parse_iso(s))
    except ValueError:
        return None


def _fix_evidence(facts, advisories):
    """SRC-003 (adv, php, version) mapped to canonical ids; GHSA-only entries become advisories (FR-FEED-PCVE-002)."""
    alias_of = {}
    for a in advisories.values():
        for al in a['aliases']:
            alias_of.setdefault(al, a['adv_id'])
    for f in facts.get('SRC-003', []):
        if f.get('type') == 'alias':
            alias_of.setdefault(f['alias_id'], f['adv_id'])
    out = set()
    for f in facts.get('SRC-003', []):
        if f.get('type') != 'fix' or not f.get('version'):
            continue
        aid = f['adv_id'] if f['adv_id'] in advisories else alias_of.get(f['adv_id'], f['adv_id'])
        if aid not in advisories:
            advisories[aid] = {'adv_id': aid, 'products': ['php'], 'aliases': [], 'scores': [], 'ranges': [],
                               'sources': {'SRC-003'}, 'kind': 'VULN',
                               'status': 'PENDING_NVD' if aid.startswith('CVE-') else 'PUBLISHED',
                               'published_at': None, 'modified_at': None, 'summary': None, 'cwe_ids': None,
                               'workaround': None, 'in_kev': 0, 'kev_due': None}
        out.add((aid, 'php', f['version']))
    return out


def _sec_releases(releases, by_branch, advisories, fix_ev, now, sec_seen):
    """BR-FEED-024: temporary advisory QP-SR-{product}-{r} for a security release without CVE details."""
    seen = sec_seen if sec_seen is not None else {}
    newest = {}
    for r in releases:
        if r['is_security'] and r['product'] in ('php', 'node', 'wordpress'):
            k = (r['product'], r['branch'])
            if k not in newest or V.vcmp(r['version'], newest[k]['version']) > 0:
                newest[k] = r
    # Only the newest security release of a branch can raise min_patched (assumption A-M2-03).
    for r in newest.values():
        key = '%s@%s' % (r['product'], r['version'])
        first = seen.get(key)
        if first is None:
            seen[key] = first = now
        if r.get('release_date'):
            first = min(first, parse_iso(r['release_date']))
        if now - first < SEC_RELEASE_DELAY_S:
            continue
        p, b, ver = r['product'], r['branch'], r['version']
        covered = False
        for a in advisories.values():
            if a['kind'] == 'SEC_RELEASE' or p not in a['products'] or a['status'] in EXCLUDED:
                continue
            if a['adv_id'].startswith('QP-SR-'):
                continue
            if (a['adv_id'], p, ver) in fix_ev:
                covered = True
                break
            sel = selected_ranges(a['ranges'], p)
            vers = by_branch.get((p, b), [])
            if _fixed_by_releases(sel, vers) == ver:
                covered = True
                break
            if any(rg.get('v_end') == ver and not rg.get('end_incl') for rg in sel):
                covered = True
                break
        if covered:
            continue
        aid = 'QP-SR-%s-%s' % (p, ver)
        advisories[aid] = {'adv_id': aid, 'products': [p], 'aliases': [], 'scores': [], 'sources': {'BR-FEED-024'},
                           'ranges': [{'product': p, 'origin': 'SEC_RELEASE', 'v_start': branch_start(p, b),
                                       'start_incl': 1, 'v_end': ver, 'end_incl': 0, 'v_exact': None,
                                       'unbounded': 0, 'platform': 'any'}],
                           'kind': 'SEC_RELEASE', 'status': 'PUBLISHED',
                           'published_at': utc_iso(first), 'modified_at': utc_iso(first),
                           'summary': 'Security release %s %s without CVE details yet' % (p, ver), 'cwe_ids': None,
                           'workaround': None, 'in_kev': 0, 'kev_due': None}


def _fixed_by_releases(sel, vers):
    """§6.2: smallest release above every affected release and not affected itself."""
    hit = [v for v in vers if affects(sel, v)]
    if not hit:
        return None
    top = hit[-1]
    for v in vers:
        if V.vcmp(v, top) > 0 and not affects(sel, v):
            return v
    return 'NONE'


def _fixed_in_branch(lifecycle, by_branch, advisories, fix_ev, conflicts):
    """fixed(c, B) per BR-FEED-027 (max of every candidate) for php/node/wordpress branches."""
    fixes = {}
    ev = {}
    for aid, p, ver in fix_ev:
        ev.setdefault((aid, p, V.branch_of(p, ver)), set()).add(ver)
    branches = {}
    for (p, b) in lifecycle:
        if p in RUNTIMES:
            branches.setdefault(p, []).append(b)
    for a in advisories.values():
        if a['status'] in EXCLUDED or a['kind'] == 'MALWARE':
            continue
        for p in a['products']:
            if p not in RUNTIMES:
                continue
            sel = a['sel'].get(p, [])
            allr = [r for r in a['ranges'] if r.get('product') == p and r.get('platform', 'any') == 'any']
            for b in branches.get(p, []):
                vers = by_branch.get((p, b), [])
                if vers:
                    applies = any(affects(sel, v) for v in vers)
                else:
                    applies = affects(sel, branch_start(p, b)) or _range_in_branch(sel, p, b)
                if not applies and not ev.get((a['adv_id'], p, b)):
                    continue
                cands = {}
                if vers:
                    f = _fixed_by_releases(sel, vers)
                    if f and f != 'NONE':
                        cands['range'] = f
                    elif f == 'NONE':
                        cands['range'] = 'NONE'
                for r in allr:
                    e = r.get('v_end')
                    if e and V.branch_of(p, e) == b:
                        if r.get('end_incl'):
                            nxt = next((v for v in vers if V.vcmp(v, e) > 0), None)
                            cands.setdefault('end:' + r.get('origin', ''), nxt or 'PENDING_RELEASE')
                        else:
                            cur = cands.get('end:' + r.get('origin', ''))
                            if cur is None or (cur not in ('NONE', 'PENDING_RELEASE') and V.vcmp(e, cur) > 0):
                                cands['end:' + r.get('origin', '')] = e
                for v in ev.get((a['adv_id'], p, b), ()):
                    cur = cands.get('SRC-003')
                    if cur is None or V.vcmp(v, cur) > 0:
                        cands['SRC-003'] = v
                if not cands:
                    continue
                real = {k: v for k, v in cands.items() if v not in ('NONE', 'PENDING_RELEASE')}
                if real:
                    best = V.vmax(real.values())
                    if vers and best not in vers:
                        fixed = best if V.vcmp(best, vers[-1]) <= 0 else 'PENDING_RELEASE'
                        if fixed != 'PENDING_RELEASE':
                            fixed = next((v for v in vers if V.vcmp(v, best) >= 0), 'PENDING_RELEASE')
                    else:
                        fixed = best
                    if len(set(real.values())) > 1:
                        conflicts.append({'attribute': 'fixed_in_branch %s %s %s' % (a['adv_id'], p, b),
                                          'values': real, 'chosen': fixed,
                                          'message': '%s %s %s fixed version: %s; using %s' % (
                                              a['adv_id'], p, b,
                                              ', '.join('%s=%s' % kv for kv in sorted(real.items())), fixed)})
                elif 'PENDING_RELEASE' in cands.values():
                    fixed = 'PENDING_RELEASE'
                else:
                    fixed = 'NONE'
                fixes[(a['adv_id'], p, b)] = {'adv_id': a['adv_id'], 'product': p, 'branch': b, 'fixed': fixed,
                                              'candidates': cands}
    return fixes


def _range_in_branch(sel, product, branch):
    for r in sel:
        for k in ('v_start', 'v_end', 'v_exact'):
            v = r.get(k)
            if v and V.branch_of(product, v) == branch:
                return True
    return False


def _min_patched(lifecycle, by_branch, advisories, fixes, releases, today):
    """§6 + BR-FEED-025 (WordPress) + BR-FEED-030."""
    rel = {(r['product'], r['version']): r for r in releases}
    per_branch = {}
    for f in fixes.values():
        per_branch.setdefault((f['product'], f['branch']), []).append(f)
    out = []
    for (p, b), lc in sorted(lifecycle.items(), key=lambda kv: (kv[0][0], V.vkey(kv[0][1]))):
        if p not in RUNTIMES:
            continue
        vers = by_branch.get((p, b), [])
        latest = vers[-1] if vers else lc.get('latest_hint')
        row = {'product': p, 'branch': b, 'latest': latest}
        for key, sec in (('min_patched_sec', True), ('min_patched_all', False)):
            vals, drivers, bad = [], {}, set()
            for f in per_branch.get((p, b), []):
                a = advisories[f['adv_id']]
                if sec and not (effective_score(a) >= 7.0 or a['in_kev']):
                    continue
                if f['fixed'] in ('NONE', 'PENDING_RELEASE'):
                    bad.add(f['fixed'])
                    continue
                vals.append(f['fixed'])
                drivers.setdefault(f['fixed'], []).append(f['adv_id'])
            eol = lc.get('eol_date') and lc['eol_date'] < today and lc.get('php_net_supported') != 1
            if 'NONE' in bad or (bad and eol):
                mp = 'NONE'          # an EOL branch gets no further release
            elif bad:
                mp = 'PENDING_RELEASE'
            elif vals:
                mp = V.vmax(vals)
            else:
                mp = vers[0] if vers else None
            row[key] = mp
            if sec:
                row['driver_ids'] = sorted(drivers.get(mp, []))
        if p == 'wordpress' and vers and any(rel[(p, v)].get('wp_status') for v in vers):
            ok = [v for v in vers if rel[(p, v)].get('wp_status') != 'insecure']
            row['min_patched_sec'] = ok[0] if ok else 'NONE'
            if row['min_patched_all'] not in ('NONE', 'PENDING_RELEASE') and ok and \
                    V.vcmp(row['min_patched_all'] or '0', ok[0]) < 0:
                row['min_patched_all'] = ok[0]
            elif not ok:
                row['min_patched_all'] = 'NONE'
            ids = [f['adv_id'] for f in per_branch.get((p, b), []) if f['fixed'] == row['min_patched_sec']]
            row['driver_ids'] = sorted(ids)
        out.append(row)
    return out


def exposure_of(advisories, product, version):
    """Advisories affecting PRODUCT VERSION (not REJECTED/WITHDRAWN, Linux)."""
    hits = []
    for a in advisories:
        if a['status'] in EXCLUDED or a['kind'] == 'MALWARE' or product not in a['products']:
            continue
        if affects(a['sel'].get(product, []), version):
            hits.append(a)
    return hits


def summarize(hits):
    n = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    cmax, kev = 0, 0
    for a in hits:
        s = effective_score(a)
        sev = severity_of(s)
        if sev in n:
            n[sev] += 1
        cmax = max(cmax, int(round(s * 10)))
        kev += 1 if a.get('in_kev') else 0
    return {'n_crit': n['critical'], 'n_high': n['high'], 'n_med': n['medium'], 'n_low': n['low'],
            'cvss10': cmax, 'cvss_max': '%d.%d' % (cmax // 10, cmax % 10), 'n_kev': kev,
            'adv_ids': sorted(a['adv_id'] for a in hits)}


def _exposure(releases, advisories):
    by_product = {}
    for a in advisories.values():
        for p in a['products']:
            by_product.setdefault(p, []).append(a)
    out = []
    for r in releases:
        hits = exposure_of(by_product.get(r['product'], []), r['product'], r['version'])
        row = summarize(hits)
        row.update(product=r['product'], version=r['version'])
        out.append(row)
    return out
