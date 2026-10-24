"""Source adapters: fetch one source, validate it, turn it into facts (DOC-SRS-QP-FEED-001 §3.4).

Every collector returns facts (plain dicts with a 'type'):
  lifecycle  product, branch, ga_date, lts_start, active_support_end, eol_date,
             prerelease_date, php_net_supported, latest_hint, approx
  release    product, branch, version, release_date, is_security, wp_status, abi_modules, lts_codename
  advisory   adv_id, product[], kind, status, published_at, modified_at, summary, cwe_ids,
             workaround, aliases[], scores[], ranges[]
  fix        adv_id, product, version             (fix_evidence, SRC-003)
  alias      adv_id, alias_id
  kev        cve_id, date_added, due_date, ransomware
  framework  framework, cycle, php_min, php_max, eol_date
A collector raises http.FetchError when the source cannot be reached and
Invalid when the response is malformed or fails BR-FEED-009; the caller then
keeps the previous facts of that source (BR-FEED-006/007).
"""
import calendar
import json
import re
import subprocess
import time

from . import versions as V
from .http import FetchError
from .store import utc_iso

CVE_RE = re.compile(r'CVE-\d{4}-\d{4,}')
GHSA_RE = re.compile(r'GHSA(?:-[23456789cfghjmpqrvwx]{4}){3}')
DATE_FORMATS = ('%Y-%m-%d', '%d %b %Y', '%d %B %Y', '%Y-%m-%dT%H:%M:%S')


class Invalid(Exception):
    """Response rejected: code ERR-FEED-502-01 (malformed) or ERR-FEED-502-02 (anomaly)."""

    def __init__(self, code, message, body=None, name='response'):
        Exception.__init__(self, message)
        self.code, self.message, self.body, self.name = code, message, body, name


def iso_date(value):
    """Normalize a source date to YYYY-MM-DD, or None (BR-FEED-021)."""
    if value in (None, '', False, True):
        return None
    s = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return time.strftime('%Y-%m-%d', time.strptime(s[:19] if 'T' in s else s, fmt))
        except ValueError:
            pass
    raise ValueError('unparseable date %r' % value)


def _json(body, name, src):
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as e:
        raise Invalid('ERR-FEED-502-01', '%s: %s' % (src, e), body, name)


def shrink_check(ctx, src, key, new_count, max_drop_pct=20, max_drop_abs=None):
    """BR-FEED-009: reject a response whose record count fell abnormally."""
    prev = (ctx.prev_counts.get(src) or {}).get(key)
    if not prev or ctx.accept_shrink:
        return
    if max_drop_abs is not None:
        bad = prev - new_count > max_drop_abs
    else:
        bad = new_count < prev * (100 - max_drop_pct) / 100.0
    if bad:
        raise Invalid('ERR-FEED-502-02', '%s %s: %d records, was %d' % (src, key, new_count, prev))


# --- SRC-001 endoflife.date ------------------------------------------------
EOL_PRODUCTS = {'php': 'php', 'nodejs': 'node', 'wordpress': 'wordpress', 'laravel': 'laravel',
                'symfony': 'symfony', 'drupal': 'drupal', 'magento': 'magento', 'composer': 'composer'}
LEGACY_PRODUCTS = ('laravel', 'magento', 'wordpress')


def _php_range(spec):
    """'7.2.24 - 8.5' -> (7.2.24, 8.5); '8.3, 8.4' -> (8.3, 8.4); '5.2.4+' -> (5.2.4, None)."""
    s = str(spec or '').strip()
    m = re.match(r'^(\d+(?:\.\d+)*)\s*\+$', s)
    if m:
        return m.group(1), None
    m = re.match(r'^(\d+(?:\.\d+)*)\s*-\s*(\d+(?:\.\d+)*)$', s)
    if m:
        return m.group(1), m.group(2)
    parts = [x.strip() for x in s.split(',')]
    if parts and all(re.match(r'^\d+(?:\.\d+)*$', x) for x in parts):
        return V.vsorted(parts)[0], V.vsorted(parts)[-1]
    raise ValueError(spec)


def collect_eol(ctx):
    src = 'SRC-001'
    base = ctx.conf[src]['url'].rstrip('/')
    facts, counts, latest_gen = [], {}, None
    for prod, mapped in EOL_PRODUCTS.items():
        name = 'v1-%s.json' % prod
        try:
            body = ctx.get(src, name, '%s/v1/products/%s/' % (base, prod))
        except FetchError:
            if prod in ('php', 'nodejs'):
                return collect_eol_mirror(ctx)
            ctx.warn(src, 'endoflife.date %s unavailable; keeping previous data' % prod)
            facts.extend(f for f in ctx.prev_facts(src) if f.get('product') == mapped)
            continue
        if body is None:                       # 304
            facts.extend(f for f in ctx.prev_facts(src) if f.get('product') == mapped and f['type'] == 'lifecycle')
            continue
        doc = _json(body, name, src)
        if not str(doc.get('schema_version', '')).startswith('1.'):
            raise Invalid('ERR-FEED-502-02', '%s schema_version %r' % (src, doc.get('schema_version')), body, name)
        rels = (doc.get('result') or {}).get('releases') or []
        latest_gen = doc.get('generated_at') or latest_gen
        n = 0
        for r in rels:
            branch = str(r.get('name', ''))
            if not re.match(r'^\d+(\.\d+)*$', branch):
                ctx.unparseable(src, 'release name %r' % branch)
                continue
            try:
                facts.append({'type': 'lifecycle', 'product': mapped, 'branch': branch,
                              'ga_date': iso_date(r.get('releaseDate')), 'lts_start': iso_date(r.get('ltsFrom')),
                              'active_support_end': iso_date(r.get('eoasFrom')),
                              'eol_date': iso_date(r.get('eolFrom')), 'prerelease_date': None,
                              'php_net_supported': None, 'origin': src,
                              'latest_hint': (r.get('latest') or {}).get('name')})
                n += 1
            except ValueError as e:
                ctx.unparseable(src, str(e))
        counts[prod] = n
        ctx.save_raw(src, name, body)
    need = {'php': 18, 'nodejs': 26}
    for prod, minimum in need.items():
        if prod in counts and counts[prod] < minimum and not ctx.accept_shrink:
            raise Invalid('ERR-FEED-502-02', '%s %s: %d branches (< %d)' % (src, prod, counts[prod], minimum))
        if prod in counts:
            shrink_check(ctx, src, prod, counts[prod])
    # Legacy API: PHP support of frameworks/CMS (FR-FEED-EOL-003).
    for prod in LEGACY_PRODUCTS:
        name = 'legacy-%s.json' % prod
        try:
            body = ctx.get(src, name, '%s/%s.json' % (base, prod))
        except FetchError:
            facts.extend(f for f in ctx.prev_facts(src) if f['type'] == 'framework' and f['framework'] == prod)
            continue
        if body is None:
            facts.extend(f for f in ctx.prev_facts(src) if f['type'] == 'framework' and f['framework'] == prod)
            continue
        for cyc in _json(body, name, src):
            spec = None
            for k, v in cyc.items():
                if k.lower() == 'supportedphpversions':
                    spec = v
            if not spec:
                continue
            try:
                lo, hi = _php_range(spec)
                eol = cyc.get('eol')
                facts.append({'type': 'framework', 'framework': prod, 'cycle': str(cyc.get('cycle')),
                              'php_min': lo, 'php_max': hi,
                              'eol_date': None if eol in (False, None) else (iso_date(eol) if eol is not True else None)})
            except ValueError:
                ctx.unparseable(src, 'supportedPhpVersions %r' % spec)
        ctx.save_raw(src, name, body)
    ctx.counts[src] = counts
    return {'facts': facts, 'records': sum(counts.values()), 'source_updated_at': latest_gen, 'origin': 'PRIMARY'}


def collect_eol_mirror(ctx):
    """endoflife.date down: YAML front matter of products/{php,nodejs}.md on GitHub."""
    src = 'SRC-001'
    base = ctx.conf[src].get('mirror_url', '').rstrip('/')
    facts = []
    for prod, mapped in (('php', 'php'), ('nodejs', 'node')):
        body = ctx.get(src, 'mirror-%s.md' % prod, '%s/%s.md' % (base, prod), conditional=False)
        text = body.decode('utf-8', 'replace')
        cur = None
        for line in text.splitlines():
            m = re.match(r'^\s*-\s*releaseCycle:\s*"?([^"\s]+)"?', line)
            if m:
                cur = {'type': 'lifecycle', 'product': mapped, 'branch': m.group(1), 'ga_date': None,
                       'lts_start': None, 'active_support_end': None, 'eol_date': None, 'prerelease_date': None,
                       'php_net_supported': None, 'origin': src, 'latest_hint': None}
                facts.append(cur)
                continue
            m = re.match(r'^\s+(releaseDate|eoas|eol|lts|support|latest):\s*"?([^"\s]+)"?', line)
            if m and cur:
                k, v = m.groups()
                key = {'releaseDate': 'ga_date', 'eoas': 'active_support_end', 'support': 'active_support_end',
                       'eol': 'eol_date', 'lts': 'lts_start', 'latest': 'latest_hint'}[k]
                if key == 'latest_hint':
                    cur[key] = v
                elif v not in ('false', 'true'):
                    try:
                        cur[key] = iso_date(v)
                    except ValueError:
                        ctx.unparseable(src, '%s %r' % (k, v))
    facts.extend(f for f in ctx.prev_facts(src) if f['type'] == 'framework')
    return {'facts': facts, 'records': len(facts), 'origin': 'MIRROR'}


# --- SRC-002 php.net releases ----------------------------------------------
def collect_php_releases(ctx):
    src = 'SRC-002'
    base = ctx.conf[src]['url'].rstrip('/')
    try:
        body = ctx.get(src, 'index.json', base + '/index.php?json', conditional=False)
    except FetchError:
        return collect_php_releases_fallback(ctx)
    doc = _json(body, 'index.json', src)
    supported = set()
    facts = []
    for major, info in doc.items():
        if not isinstance(info, dict):
            continue
        supported.update(info.get('supported_versions') or [])
    if not supported:
        raise Invalid('ERR-FEED-502-02', '%s: no supported_versions' % src, body, 'index.json')
    ctx.save_raw(src, 'index.json', body)
    branches = set(supported) | set(ctx.server_branches.get('php', ()))
    stored_latest = {f['branch']: f['version'] for f in ctx.prev_facts(src) if f['type'] == 'release_latest'}
    for b in sorted(branches, key=V.vkey):
        name = 'branch-%s.json' % b
        try:
            body = ctx.get(src, name, '%s/index.php?json&version=%s&max=100' % (base, b), conditional=False)
        except FetchError as e:
            if b in supported:
                raise
            ctx.warn(src, 'php.net %s: %s' % (b, e.message))
            continue
        rels = _json(body, name, src)
        if not isinstance(rels, dict) or 'error' in rels:
            continue
        got = []
        for ver, info in rels.items():
            if not V.is_release(ver) or not isinstance(info, dict):
                continue
            tags = info.get('tags') or []
            try:
                d = iso_date(info.get('date'))
            except ValueError:
                ctx.unparseable(src, 'date %r' % info.get('date'))
                d = None
            got.append(ver)
            facts.append({'type': 'release', 'product': 'php', 'branch': V.branch_of('php', ver), 'version': ver,
                          'release_date': d, 'is_security': 1 if 'security' in tags else 0, 'wp_status': None,
                          'abi_modules': None, 'lts_codename': None})
        newest = V.vmax(got)
        if newest and b in stored_latest and V.vlt(newest, stored_latest[b]) and not ctx.accept_shrink:
            raise Invalid('ERR-FEED-502-02', '%s %s: latest %s < stored %s' % (src, b, newest, stored_latest[b]), body, name)
        if newest:
            facts.append({'type': 'release_latest', 'branch': b, 'version': newest})
        ctx.save_raw(src, name, body)
    for b in sorted(supported):
        facts.append({'type': 'supported', 'product': 'php', 'branch': b})
    return {'facts': facts, 'records': sum(1 for f in facts if f['type'] == 'release'), 'origin': 'PRIMARY'}


def collect_php_releases_fallback(ctx):
    """php.net down: php-src tags (git ls-remote), else previous data (BR-FEED-006)."""
    src = 'SRC-002'
    facts = []
    try:
        out = subprocess.run(['git', 'ls-remote', '--tags', 'https://github.com/php/php-src', 'php-*'],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60).stdout.decode()
    except (OSError, subprocess.SubprocessError):
        out = ''
    for m in re.finditer(r'refs/tags/php-(\d+\.\d+\.\d+)$', out, re.M):
        v = m.group(1)
        facts.append({'type': 'release', 'product': 'php', 'branch': V.branch_of('php', v), 'version': v,
                      'release_date': None, 'is_security': 0, 'wp_status': None, 'abi_modules': None,
                      'lts_codename': None})
    if not facts:
        raise FetchError('ERR-FEED-503-01', 'php.net and php-src tags unavailable')
    facts.extend(f for f in ctx.prev_facts(src) if f['type'] == 'supported')
    return {'facts': facts, 'records': len(facts), 'origin': 'CROSS:php-src-tags'}


# --- SRC-003 php.net ChangeLog, NEWS, eol.php ------------------------------
def collect_php_changelog(ctx):
    src = 'SRC-003'
    base = ctx.conf[src]['url'].rstrip('/')
    mirror = ctx.conf[src].get('mirror_url', '').rstrip('/')
    facts = []
    for major in ('5', '7', '8'):
        name = 'ChangeLog-%s.html' % major
        body = ctx.get(src, name, '%s/ChangeLog-%s.php' % (base, major))
        if body is None:
            facts.extend(f for f in ctx.prev_facts(src) if f.get('from') == name)
            continue
        html = body.decode('utf-8', 'replace')
        for sec in re.split(r'<section class="version" id="', html)[1:]:
            ver = sec.split('"', 1)[0]
            if not V.is_release(ver):
                continue
            for item in re.findall(r'<li>(.*?)</li>', sec, re.S):
                ghsas = sorted(set(GHSA_RE.findall(item)))
                cves = sorted(set(CVE_RE.findall(item)))
                for a in cves or ghsas:
                    facts.append({'type': 'fix', 'adv_id': a, 'product': 'php', 'version': ver, 'from': name})
                for c in cves:
                    for g in ghsas:
                        facts.append({'type': 'alias', 'adv_id': c, 'alias_id': g, 'from': name})
        ctx.save_raw(src, name, body)
    supported = [f['branch'] for f in ctx.facts_of('SRC-002') if f['type'] == 'supported']
    for b in supported:
        name = 'NEWS-%s.txt' % b
        try:
            body = ctx.get(src, name, '%s/PHP-%s/NEWS' % (mirror, b))
        except FetchError as e:
            ctx.warn(src, 'NEWS %s: %s' % (b, e.message))
            continue
        if body is None:
            facts.extend(f for f in ctx.prev_facts(src) if f.get('from') == name)
            continue
        ver = None
        item = []

        def flush():
            text = ' '.join(item)
            ghsas, cves = sorted(set(GHSA_RE.findall(text))), sorted(set(CVE_RE.findall(text)))
            for a in cves or ghsas:
                facts.append({'type': 'fix', 'adv_id': a, 'product': 'php', 'version': ver, 'from': name})
            for c in cves:
                for g in ghsas:
                    facts.append({'type': 'alias', 'adv_id': c, 'alias_id': g, 'from': name})
        for line in body.decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\d\d \w{3} \d{4}, PHP (\d+\.\d+\.\d+)\s*$', line)
            if m:
                if ver and item:
                    flush()
                ver, item = m.group(1), []
                continue
            if line.startswith('?? ??? ????'):
                if ver and item:
                    flush()
                ver, item = None, []
                continue
            if ver is None:
                continue
            if re.match(r'^\s+\.\s', line) or re.match(r'^- ', line):
                if item:
                    flush()
                item = [line]
            elif line.strip():
                item.append(line)
        if ver and item:
            flush()
        ctx.save_raw(src, name, body)
    name = 'eol.html'
    body = ctx.get(src, name, base + '/eol.php')
    if body is None:
        facts.extend(f for f in ctx.prev_facts(src) if f['type'] == 'lifecycle')
    else:
        html = body.decode('utf-8', 'replace')
        for m in re.finditer(r'<td>\s*(\d+\.\d+)\s*</td>\s*<td>\s*(\d{1,2} \w+ \d{4})', html):
            try:
                facts.append({'type': 'lifecycle', 'product': 'php', 'branch': m.group(1), 'ga_date': None,
                              'lts_start': None, 'active_support_end': None, 'eol_date': iso_date(m.group(2)),
                              'prerelease_date': None, 'php_net_supported': None, 'origin': src, 'latest_hint': None})
            except ValueError:
                ctx.unparseable(src, 'eol date %r' % m.group(2))
        ctx.save_raw(src, name, body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-004 NVD -------------------------------------------------------------
NVD_QUERIES = {
    'php-q1': ('php', {'virtualMatchString': 'cpe:2.3:a:php:php'}),
    'php-q2': ('php', {'sourceIdentifier': 'security@php.net'}),
    'node-q1': ('node', {'virtualMatchString': 'cpe:2.3:a:nodejs:node.js'}),
    'wordpress-q1': ('wordpress', {'virtualMatchString': 'cpe:2.3:a:wordpress:wordpress'}),
}
NVD_STATUS = {'Analyzed': 'PUBLISHED', 'Modified': 'PUBLISHED', 'Awaiting Analysis': 'AWAITING_ANALYSIS',
              'Received': 'AWAITING_ANALYSIS', 'Undergoing Analysis': 'AWAITING_ANALYSIS', 'Rejected': 'REJECTED',
              'Deferred': 'PUBLISHED'}
CNA_NAMES = {'php': {'php'}, 'node': {'node.js', 'node', 'nodejs'}, 'wordpress': {'wordpress'}}
WINDOW = 120 * 86400


def nvd_iso(t):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000', time.gmtime(t))


def nvd_scores(metrics):
    out = []
    for key, ver in (('cvssMetricV40', '4.0'), ('cvssMetricV31', '3.1'), ('cvssMetricV30', '3.0'), ('cvssMetricV2', '2.0')):
        for m in metrics.get(key, []) or []:
            d = m.get('cvssData', {})
            src = m.get('source', '')
            out.append({'source': 'NVD' if src == 'nvd@nist.gov' else 'CNA:' + src, 'cvss_version': ver,
                        'type': m.get('type'), 'base_score': d.get('baseScore'), 'vector': d.get('vectorString'),
                        'severity_text': (d.get('baseSeverity') or m.get('baseSeverity') or '').lower() or None})
    return out


def nvd_advisory(cve, product):
    ranges = [dict(r, product=product, origin='NVD_CPE') for r in V.nvd_ranges(cve.get('configurations'), product)]
    for a in cve.get('affected', []) or []:
        for r in V.cna_ranges(a.get('affectedData', []), CNA_NAMES[product]):
            ranges.append(dict(r, product=product, origin='CNA'))
    aliases = set()
    for ref in cve.get('references', []) or []:
        m = re.search(r'/security/advisories/(GHSA-[\w-]+)', ref.get('url', ''))
        if m:
            aliases.add(m.group(1))
    cwes = sorted({d.get('value') for w in cve.get('weaknesses', []) or [] for d in w.get('description', [])
                   if str(d.get('value', '')).startswith('CWE-')})
    desc = next((d.get('value') for d in cve.get('descriptions', []) if d.get('lang') == 'en'), None)
    return {'type': 'advisory', 'adv_id': cve['id'], 'products': [product], 'kind': 'VULN',
            'status': NVD_STATUS.get(cve.get('vulnStatus'), 'PUBLISHED'),
            'published_at': (cve.get('published') or '')[:19] + 'Z', 'modified_at': (cve.get('lastModified') or '')[:19] + 'Z',
            'summary': (desc or '')[:500] or None, 'cwe_ids': ','.join(cwes) or None, 'workaround': None,
            'aliases': sorted(aliases), 'scores': nvd_scores(cve.get('metrics', {})), 'ranges': ranges}


def collect_nvd(ctx):
    src = 'SRC-004'
    url = ctx.conf[src]['url']
    size = int(ctx.conf[src].get('page_size') or 200)
    prev = {f['adv_id'] + '|' + ','.join(f['products']): f for f in ctx.prev_facts(src) if f['type'] == 'advisory'}
    store = {}
    for f in prev.values():
        store.setdefault(f['adv_id'], f)
    cursor = ctx.fs.state('nvd-cursor', {})
    now = ctx.now()
    headers = {}
    if ctx.keys.get('NVD_API_KEY'):
        headers['apiKey'] = ctx.keys['NVD_API_KEY']
        ctx.conf[src]['min_interval_s'] = min(float(ctx.conf[src].get('min_interval_s') or 1), 1.0)
    seen = 0
    for qname, (product, params) in NVD_QUERIES.items():
        last = cursor.get(qname)
        if last is None and ctx.snapshot_base_at:
            last = ctx.snapshot_base_at - 86400 + 3600          # BR-FEED-002: generated_at - 1 day
        windows = [(None, None)]
        if last is not None:
            start = last - 3600
            windows = []
            while start < now:
                end = min(start + WINDOW, now)
                windows.append((start, end))
                start = end
        newest = last
        for ws, we in windows:
            index, total, got = 0, None, 0
            while total is None or index < total:
                q = dict(params, resultsPerPage=size, startIndex=index)
                if ws is not None:
                    q['lastModStartDate'], q['lastModEndDate'] = nvd_iso(ws), nvd_iso(we)
                full = url + '?' + '&'.join('%s=%s' % (k, v) for k, v in q.items())
                resp = ctx.fetcher.request(src, full, headers=headers, retry_statuses=(403,))
                if resp.status == 403:
                    raise FetchError('ERR-FEED-429-01', 'NVD returned 403', http=403)
                if resp.status != 200:
                    raise FetchError('ERR-FEED-503-01', 'NVD HTTP %s %s' % (resp.status, resp.headers.get('message', '')),
                                     http=resp.status)
                doc = _json(resp.body, 'page', src)
                if doc.get('format') != 'NVD_CVE' or not str(doc.get('version', '')).startswith('2.'):
                    raise Invalid('ERR-FEED-502-02', 'NVD format %r version %r' % (doc.get('format'), doc.get('version')))
                total = int(doc.get('totalResults', 0))
                vulns = doc.get('vulnerabilities', []) or []
                ctx.save_raw(src, '%s/page-%04d.json' % (qname, index // size), resp.body)
                for v in vulns:
                    cve = v.get('cve', {})
                    if not cve.get('id'):
                        continue
                    adv = nvd_advisory(cve, product)
                    old = store.get(adv['adv_id'])
                    if old and product not in old['products']:
                        adv['products'] = sorted(set(old['products']) | {product})
                        adv['ranges'] = [r for r in old['ranges'] if r['product'] != product] + adv['ranges']
                    if not old or old.get('modified_at', '') <= adv['modified_at'] or product not in old['products']:
                        store[adv['adv_id']] = adv
                    try:
                        lm = calendar.timegm(time.strptime(cve.get('lastModified', '')[:19], '%Y-%m-%dT%H:%M:%S'))
                        newest = lm if newest is None or lm > newest else newest
                    except ValueError:
                        pass
                got += len(vulns)
                index += size
                if not vulns:
                    break
            if total is not None and got != total:
                raise Invalid('ERR-FEED-502-02', 'NVD %s: %d of %d records received' % (qname, got, total))
            seen += got
        cursor[qname] = newest if newest is not None else now
    ctx.fs.save_state('nvd-cursor', cursor)
    facts = list(store.values())
    upd = max((f['modified_at'] for f in facts), default=None)
    return {'facts': facts, 'records': len(facts), 'source_updated_at': upd, 'origin': 'PRIMARY', 'fetched': seen}


# --- SRC-005 CVE.org (on demand) -------------------------------------------
def cveorg_advisory(doc, product):
    cna = (doc.get('containers') or {}).get('cna') or {}
    meta = doc.get('cveMetadata') or {}
    ranges = [dict(r, product=product, origin='CNA') for r in V.cna_ranges(cna.get('affected'), CNA_NAMES[product])]
    scores = []
    for m in cna.get('metrics', []) or []:
        for key, ver in (('cvssV4_0', '4.0'), ('cvssV3_1', '3.1'), ('cvssV3_0', '3.0')):
            if key in m:
                scores.append({'source': 'CNA:' + str(meta.get('assignerShortName', '')), 'cvss_version': ver,
                               'type': 'Secondary', 'base_score': m[key].get('baseScore'),
                               'vector': m[key].get('vectorString'),
                               'severity_text': (m[key].get('baseSeverity') or '').lower() or None})
    wk = ' '.join(w.get('value', '') for w in cna.get('workarounds', []) or [])[:1000] or None
    desc = next((d.get('value') for d in cna.get('descriptions', []) or [] if d.get('lang', '').startswith('en')), None)
    status = 'REJECTED' if meta.get('state') == 'REJECTED' else 'PUBLISHED'
    return {'type': 'advisory', 'adv_id': meta.get('cveId'), 'products': [product], 'kind': 'VULN', 'status': status,
            'published_at': (meta.get('datePublished') or '')[:19] + 'Z' if meta.get('datePublished') else None,
            'modified_at': (meta.get('dateUpdated') or meta.get('datePublished') or '')[:19] + 'Z',
            'summary': (desc or '')[:500] or None, 'cwe_ids': None, 'workaround': wk, 'aliases': [],
            'scores': scores, 'ranges': ranges, 'origin_src': 'SRC-005'}


def lookup_cveorg(ctx, wanted):
    """wanted: {cve_id: product}. Cache 24 h in cache/cve/ (BR-FEED-014); <= 200 per sync."""
    src = 'SRC-005'
    base = ctx.conf[src]['url'].rstrip('/')
    out = []
    for i, (cve, product) in enumerate(sorted(wanted.items())):
        if i >= 200:
            break
        cached = ctx.cache_get('cve', cve, ttl_s=86400)
        if cached is None:
            try:
                resp = ctx.fetcher.request(src, '%s/%s' % (base, cve))
            except FetchError as e:
                ctx.warn(src, '%s: %s' % (cve, e.message))
                continue
            if resp.status == 404:
                cached = {'_status': 'RESERVED'}
            elif resp.status == 200:
                cached = _json(resp.body, cve, src)
            else:
                continue
            ctx.cache_put('cve', cve, cached)
        if cached.get('_status') == 'RESERVED':
            out.append({'type': 'advisory', 'adv_id': cve, 'products': [product], 'kind': 'VULN', 'status': 'RESERVED',
                        'published_at': None, 'modified_at': utc_iso(ctx.now()), 'summary': None, 'cwe_ids': None,
                        'workaround': None, 'aliases': [], 'scores': [], 'ranges': [], 'origin_src': src})
        elif cached.get('dataType') == 'CVE_RECORD' and str(cached.get('dataVersion', '')).startswith('5.'):
            out.append(cveorg_advisory(cached, product))
    return out


# --- SRC-006 CISA KEV --------------------------------------------------------
def collect_kev(ctx):
    src = 'SRC-006'
    name = 'kev.json'
    try:
        body = ctx.get(src, name, ctx.conf[src]['url'], use_etag=False)
        origin = 'PRIMARY'
    except FetchError:
        body = ctx.get(src, name, ctx.conf[src]['mirror_url'], use_etag=True)
        origin = 'MIRROR'
    if body is None:
        return None
    doc = _json(body, name, src)
    vulns = doc.get('vulnerabilities') or []
    if int(doc.get('count', -1)) != len(vulns):
        raise Invalid('ERR-FEED-502-02', 'KEV count %s != %d entries' % (doc.get('count'), len(vulns)), body, name)
    prev_ver = (ctx.prev_counts.get(src) or {}).get('catalogVersion')
    if prev_ver and str(doc.get('catalogVersion', '')) < str(prev_ver) and not ctx.accept_shrink:
        raise Invalid('ERR-FEED-502-02', 'KEV catalogVersion %s < %s' % (doc.get('catalogVersion'), prev_ver), body, name)
    shrink_check(ctx, src, 'count', len(vulns), max_drop_abs=5)
    facts = []
    for v in vulns:
        if not CVE_RE.fullmatch(str(v.get('cveID', ''))):
            ctx.unparseable(src, 'cveID %r' % v.get('cveID'))
            continue
        facts.append({'type': 'kev', 'cve_id': v['cveID'], 'date_added': v.get('dateAdded'),
                      'due_date': v.get('dueDate'), 'ransomware': v.get('knownRansomwareCampaignUse')})
    ctx.save_raw(src, name, body)
    ctx.counts[src] = {'count': len(vulns), 'catalogVersion': doc.get('catalogVersion')}
    return {'facts': facts, 'records': len(facts), 'source_updated_at': doc.get('dateReleased'), 'origin': origin}


# --- SRC-008 GitHub Security Advisories (php-src) ----------------------------
def collect_ghsa(ctx):
    src = 'SRC-008'
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    if ctx.keys.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + ctx.keys['GITHUB_TOKEN']
    url = ctx.conf[src]['url'] + '?state=published&sort=updated&direction=desc&per_page=100'
    resp = ctx.fetcher.request(src, url, headers=headers)
    if resp.status in (401, 403, 429):
        code = 'ERR-FEED-401-01' if resp.status == 401 and 'Authorization' in headers else 'ERR-FEED-429-01'
        if resp.headers.get('x-ratelimit-remaining', resp.headers.get('X-RateLimit-Remaining')) != '0' and resp.status == 403:
            code = 'ERR-FEED-503-03'
        raise FetchError(code, 'GitHub API HTTP %d' % resp.status, http=resp.status)
    if resp.status != 200:
        raise FetchError('ERR-FEED-503-03', 'GitHub API HTTP %d' % resp.status, http=resp.status)
    items = _json(resp.body, 'advisories.json', src)
    facts = []
    for a in items:
        ghsa, cve = a.get('ghsa_id'), a.get('cve_id')
        if not ghsa:
            continue
        adv_id = cve or ghsa
        scores = []
        for ver, key in (('3.1', 'cvss_v3'), ('4.0', 'cvss_v4')):
            s = ((a.get('cvss_severities') or {}).get(key) or {})
            if s.get('score'):
                scores.append({'source': 'GHSA', 'cvss_version': ver if ver != '3.1' else '3.1', 'type': None,
                               'base_score': s['score'], 'vector': s.get('vector_string'), 'severity_text': None})
        if not scores and a.get('severity'):
            scores.append({'source': 'GHSA', 'cvss_version': 'NONE', 'type': None, 'base_score': None, 'vector': None,
                           'severity_text': {'moderate': 'medium'}.get(a['severity'], a['severity'])})
        ranges = []
        for vuln in a.get('vulnerabilities', []) or []:
            for p in str(vuln.get('patched_versions') or '').split(','):
                p = p.strip()
                if V.is_release(p):
                    ranges.append({'product': 'php', 'origin': 'GHSA', 'v_start': V.branch_of('php', p) + '.0',
                                   'start_incl': 1, 'v_end': p, 'end_incl': 0, 'v_exact': None,
                                   'unbounded': 0, 'platform': 'any'})
        facts.append({'type': 'advisory', 'adv_id': adv_id, 'products': ['php'], 'kind': 'VULN',
                      'status': 'WITHDRAWN' if a.get('withdrawn_at') else 'PUBLISHED',
                      'published_at': a.get('published_at'), 'modified_at': a.get('updated_at') or a.get('published_at'),
                      'summary': (a.get('summary') or '')[:500] or None, 'cwe_ids': None, 'workaround': None,
                      'aliases': [ghsa] if cve else [], 'scores': scores, 'ranges': ranges})
    ctx.save_raw(src, 'advisories.json', resp.body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-009 nodejs.org index ------------------------------------------------
def collect_node_index(ctx):
    src = 'SRC-009'
    name = 'index.json'
    try:
        body = ctx.get(src, name, ctx.conf[src]['url'])
    except FetchError:
        latest = [f for f in ctx.facts_of('SRC-001') if f['type'] == 'lifecycle' and f['product'] == 'node' and f.get('latest_hint')]
        if not latest:
            raise
        facts = [{'type': 'release', 'product': 'node', 'branch': V.branch_of('node', f['latest_hint']),
                  'version': f['latest_hint'], 'release_date': None, 'is_security': 0, 'wp_status': None,
                  'abi_modules': None, 'lts_codename': None} for f in latest]
        # Older releases (and their security flags) stay from the cache; a version is never taken
        # from two fallback tiers (BR-FEED-006).
        prev = [f for f in ctx.prev_facts(src) if f.get('type') == 'release']
        cached = {f['version'] for f in prev}
        facts = [f for f in facts if f['version'] not in cached] + prev
        return {'facts': facts, 'records': len(facts), 'origin': 'CROSS:SRC-001'}
    if body is None:
        return None
    items = _json(body, name, src)
    facts = []
    for it in items:
        v = str(it.get('version', ''))
        if not re.match(r'^v\d+\.\d+\.\d+$', v):
            ctx.unparseable(src, 'version %r' % v)
            continue
        ver = v[1:]
        try:
            d = iso_date(it.get('date'))
        except ValueError:
            d = None
        lts = it.get('lts')
        facts.append({'type': 'release', 'product': 'node', 'branch': V.branch_of('node', ver), 'version': ver,
                      'release_date': d, 'is_security': 1 if it.get('security') else 0, 'wp_status': None,
                      'abi_modules': int(it['modules']) if str(it.get('modules', '')).isdigit() else None,
                      'lts_codename': lts if isinstance(lts, str) and lts else None})
    if facts and V.vmax(f['version'] for f in facts) != facts[0]['version']:
        raise Invalid('ERR-FEED-502-02', 'nodejs index: first entry is not the newest', body, name)
    shrink_check(ctx, src, 'count', len(facts))
    ctx.counts[src] = {'count': len(facts)}
    ctx.save_raw(src, name, body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-010 nodejs/Release schedule -------------------------------------------
def collect_node_schedule(ctx):
    src = 'SRC-010'
    name = 'schedule.json'
    body = ctx.get(src, name, ctx.conf[src]['url'])
    if body is None:
        return None
    doc = _json(body, name, src)
    facts = []
    for key, d in doc.items():
        m = re.match(r'^v(\d+(?:\.\d+)?)$', key)
        if not m or not isinstance(d, dict):
            ctx.unparseable(src, 'key %r' % key)
            continue
        try:
            row = {'type': 'lifecycle', 'product': 'node', 'branch': m.group(1), 'ga_date': iso_date(d.get('start')),
                   'lts_start': iso_date(d.get('lts')), 'active_support_end': iso_date(d.get('maintenance')),
                   'eol_date': iso_date(d.get('end')), 'prerelease_date': iso_date(d.get('alpha')),
                   'php_net_supported': None, 'origin': src, 'latest_hint': None,
                   'codename': d.get('codename') or None}
        except ValueError as e:
            ctx.unparseable(src, str(e))
            continue
        seq = [row[k] for k in ('ga_date', 'lts_start', 'active_support_end', 'eol_date') if row[k]]
        if seq != sorted(seq):
            ctx.unparseable(src, 'dates out of order for %s' % key)
        facts.append(row)
    shrink_check(ctx, src, 'count', len(facts))
    ctx.counts[src] = {'count': len(facts)}
    ctx.save_raw(src, name, body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-011 Node.js Security WG ---------------------------------------------------
NODEWG_SEV = {'critical': 'critical', 'high': 'high', 'medium': 'medium', 'low': 'low'}


def collect_node_wg(ctx):
    src = 'SRC-011'
    name = 'index.json'
    body = ctx.get(src, name, ctx.conf[src]['url'])
    if body is None:
        return None
    doc = _json(body, name, src)
    if not isinstance(doc, dict) or not all(str(k).isdigit() for k in doc):
        raise Invalid('ERR-FEED-502-02', 'Node WG index keys are not integers', body, name)
    prev_max = (ctx.prev_counts.get(src) or {}).get('max_key')
    max_key = max(int(k) for k in doc) if doc else 0
    if prev_max and max_key < prev_max and not ctx.accept_shrink:
        raise Invalid('ERR-FEED-502-02', 'Node WG max key %d < %d' % (max_key, prev_max), body, name)
    facts, bad = [], 0
    for key in sorted(doc, key=int):
        r = doc[key]
        cves = [c for c in r.get('cve', []) or [] if CVE_RE.fullmatch(c)]
        try:
            vul = V.parse_semver(r.get('vulnerable'))
            pat = V.parse_semver(r.get('patched')) if r.get('patched') else []
        except V.SemverError:
            bad += 1
            continue
        platform = 'windows' if r.get('affectedEnvironments') == ['win32'] else 'any'
        sev = NODEWG_SEV.get(str(r.get('severity', '')).lower(), 'unknown')
        score = {'source': 'NODE_WG', 'cvss_version': 'NONE', 'type': None, 'base_score': None, 'vector': None,
                 'severity_text': sev}
        if r.get('cvss_score'):
            score = {'source': 'NODE_WG', 'cvss_version': '3.1', 'type': None, 'base_score': float(r['cvss_score']),
                     'vector': r.get('cvss'), 'severity_text': sev}
        # One advisory per CVE: a WG record listing 2 CVEs must not merge them (BR-FEED-023).
        for adv_id in cves or ['NODEWG-%s' % key]:
            facts.append({'type': 'advisory', 'adv_id': adv_id, 'products': ['node'], 'kind': 'VULN',
                          'status': 'PUBLISHED', 'published_at': None, 'modified_at': None,
                          'summary': (r.get('description') or '')[:500] or None, 'cwe_ids': None, 'workaround': None,
                          'aliases': ['NODEWG-%s' % key] if cves else [], 'scores': [score],
                          'ranges': [{'product': 'node', 'origin': 'NODE_WG', 'semver_vulnerable': r.get('vulnerable'),
                                      'semver_patched': r.get('patched') or '', 'platform': platform}]})
    if bad:
        ctx.unparseable(src, '%d record(s) with unparseable semver' % bad, count=bad)
    ctx.counts[src] = {'count': len(doc), 'max_key': max_key}
    ctx.save_raw(src, name, body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-012 WordPress.org stable-check --------------------------------------------
def collect_wp(ctx):
    src = 'SRC-012'
    name = 'stable-check.json'
    body = ctx.get(src, name, ctx.conf[src]['url'].rstrip('/') + '/stable-check/1.0/', conditional=False)
    doc = _json(body, name, src)
    if not isinstance(doc, dict):
        raise Invalid('ERR-FEED-502-02', 'stable-check is not an object', body, name)
    latest = [v for v, s in doc.items() if s == 'latest']
    if len(latest) != 1:
        raise Invalid('ERR-FEED-502-02', 'stable-check has %d latest versions' % len(latest), body, name)
    shrink_check(ctx, src, 'count', len(doc), max_drop_pct=0.0001)
    facts = []
    for ver, status in doc.items():
        if not re.match(r'^\d+(\.\d+)+$', ver) or status not in ('latest', 'outdated', 'insecure'):
            ctx.unparseable(src, '%s=%s' % (ver, status))
            continue
        facts.append({'type': 'release', 'product': 'wordpress', 'branch': V.branch_of('wordpress', ver),
                      'version': ver, 'release_date': None, 'is_security': 0, 'wp_status': status,
                      'abi_modules': None, 'lts_codename': None})
    ctx.counts[src] = {'count': len(doc)}
    ctx.save_raw(src, name, body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


# --- SRC-013 optional WordPress vulnerability DB (key) -------------------------------
def collect_wp_vulndb(ctx):
    """Wordfence Intelligence v3 production feed. Field mapping not verified with a real
    key in the design session (DOC-SRS-QP-FEED-001 §3.4): parsed best effort."""
    src = 'SRC-013'
    key = ctx.keys.get('WORDFENCE_API_KEY')
    if not key:
        raise FetchError('ERR-FEED-503-03', 'no key configured')
    resp = ctx.fetcher.request(src, ctx.conf[src]['url'], headers={'Authorization': 'Bearer ' + key})
    if resp.status in (401, 403):
        raise FetchError('ERR-FEED-401-01', 'key rejected (HTTP %d)' % resp.status, http=resp.status)
    if resp.status != 200:
        raise FetchError('ERR-FEED-503-03', 'HTTP %d' % resp.status, http=resp.status)
    doc = _json(resp.body, 'production.json', src)
    facts = []
    for vid, v in (doc.items() if isinstance(doc, dict) else []):
        for sw in v.get('software', []) or []:
            kind = {'plugin': 'wp-plugin', 'theme': 'wp-theme', 'core': 'wordpress'}.get(sw.get('type'))
            if not kind:
                continue
            prod = 'wordpress' if kind == 'wordpress' else '%s:%s' % (kind, sw.get('slug'))
            ranges = []
            for _, rng in (sw.get('affected_versions') or {}).items():
                ranges.append({'product': prod, 'origin': 'WORDFENCE', 'v_start': rng.get('from_version') if rng.get('from_version') != '*' else None,
                               'start_incl': 1 if rng.get('from_inclusive', True) else 0,
                               'v_end': rng.get('to_version') if rng.get('to_version') != '*' else None,
                               'end_incl': 1 if rng.get('to_inclusive', True) else 0, 'v_exact': None,
                               'unbounded': 0, 'platform': 'any'})
            cves = [c for c in (v.get('cve') or '').split(',') if CVE_RE.fullmatch(c.strip())]
            cv = v.get('cvss') or {}
            facts.append({'type': 'advisory', 'adv_id': cves[0] if cves else 'WF-%s' % vid, 'products': [prod],
                          'kind': 'VULN', 'status': 'PUBLISHED', 'published_at': v.get('published'),
                          'modified_at': v.get('updated'), 'summary': (v.get('title') or '')[:500] or None,
                          'cwe_ids': None, 'workaround': None, 'aliases': [],
                          'scores': [{'source': 'WORDFENCE', 'cvss_version': '3.1', 'type': None,
                                      'base_score': cv.get('score'), 'vector': cv.get('vector'), 'severity_text': cv.get('rating', '').lower() or None}],
                          'ranges': ranges})
    ctx.save_raw(src, 'production.json', resp.body)
    return {'facts': facts, 'records': len(facts), 'origin': 'PRIMARY'}


COLLECTORS = {'SRC-001': collect_eol, 'SRC-002': collect_php_releases, 'SRC-003': collect_php_changelog,
              'SRC-004': collect_nvd, 'SRC-006': collect_kev, 'SRC-008': collect_ghsa, 'SRC-009': collect_node_index,
              'SRC-010': collect_node_schedule, 'SRC-011': collect_node_wg, 'SRC-012': collect_wp,
              'SRC-013': collect_wp_vulndb}
