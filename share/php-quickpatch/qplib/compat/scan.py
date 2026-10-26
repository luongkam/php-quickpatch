"""Static parts of the compatibility scan (read only, no project code is run, BR-CMPT-004).

file set      BR-CMPT-001: *.php/*.inc/*.phtml (Node.js: *.js/*.mjs/*.cjs/*.ts) under the
              docroot, without vendor/, node_modules/, .git/ and the directories the
              operator declared "not deployed"; files > 2 MiB are listed, not read
BC rules      FR-CMPT-CODE-001: rules of bc_rules.json with a version in (OLD, NEW]
loaders       FR-CMPT-LDR-001: ionCube / SourceGuardian / Zend Guard markers, <= 50,000 files
ext usage     FR-CMPT-EXT-001: calls of the functions of an extension
frameworks    FR-CMPT-FWK-001: composer.lock packages, wp-includes/version.php
"""
import hashlib
import json
import os
import re
import time

MAX_FILE = 2 * 1024 * 1024
MAX_LOADER_FILES = 50000
SKIP_DIRS = {'vendor', 'node_modules', '.git', '.svn', '.hg'}
PHP_EXT = ('.php', '.inc', '.phtml')
JS_EXT = ('.js', '.mjs', '.cjs', '.ts')
SNIPPET = 200


class Budget(object):
    """BR-CMPT-005: 1,800 s per site scan."""

    def __init__(self, seconds=1800, start=None):
        self.deadline = (start or time.time()) + seconds

    def left(self):
        return self.deadline - time.time()

    def over(self):
        return time.time() > self.deadline


def vkey(v):
    return tuple(int(x) for x in re.findall(r'\d+', str(v or ''))[:3])


def in_range(version, old, new):
    """old < version <= new on X.Y (Node.js: N)."""
    return vkey(old) < vkey(version) <= vkey(new)


def list_files(root, exts, excluded=(), budget=None):
    """-> (files, skipped [{file, size}], truncated). Paths are absolute, sorted."""
    files, skipped = [], []
    excl = {os.path.normpath(os.path.join(root, e.strip('/'))) for e in excluded if e.strip('/')}
    for dp, dns, fns in os.walk(root):
        if budget is not None and budget.over():
            return sorted(files), skipped, True
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS and os.path.normpath(os.path.join(dp, d)) not in excl
                        and not os.path.islink(os.path.join(dp, d)))
        for fn in fns:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dp, fn)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            if st.st_size > MAX_FILE:
                skipped.append({'file': os.path.relpath(p, root), 'size': st.st_size})
                continue
            files.append(p)
    return sorted(files), sorted(skipped, key=lambda s: s['file']), False


def read_text(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8', 'replace')


def hit_id(site_id, file, line, rule_id, snippet):
    h = hashlib.sha1(('%s\0%s\0%s\0%s\0%s' % (site_id, file, line, rule_id, snippet)).encode('utf-8')).hexdigest()
    return 'H-' + h[:12]


def select_rules(bc, runtime, old, new):
    """BR-SCN-041 / BR-SCN-021: rules with old < version <= new (RC rules of a branch are kept)."""
    out = []
    for r in bc['rules']:
        if r['runtime'] != runtime or not r.get('scan'):
            continue
        if in_range(r['version'], old, new):
            out.append(r)
    return out


def compile_rules(rules):
    comp = []
    for r in rules:
        for s in r['scan']:
            if s['kind'] == 'code':
                rx = re.compile(s['regex'])
                comp.append((r['rule_id'], s['level'], rx, 'code'))
            else:
                comp.append((r['rule_id'], s['level'], None, s['kind']))
    return comp


CLASS_RE = re.compile(r'^\s*(?:abstract\s+|final\s+)*class\s+(\w+)', re.M | re.I)
NS_RE = re.compile(r'^\s*namespace\s+[\w\\]+\s*[;{]', re.M)


def php4_ctors(text):
    """Lines of methods named like their class in a file without namespace (BC-PHP-70-05, BC-PHP-80-03)."""
    if NS_RE.search(text):
        return []
    out = []
    for m in CLASS_RE.finditer(text):
        name = m.group(1)
        fm = re.compile(r'\bfunction\s+&?\s*%s\s*\(' % re.escape(name), re.I)
        for f in fm.finditer(text, m.end()):
            out.append(text.count('\n', 0, f.start()) + 1)
            break
    return out


# --- loaders (FR-CMPT-LDR-001) ---------------------------------------------------
LOADER_MARKS = (('ionCube', re.compile(r'^<\?php //0|ionCube Loader|ioncube_loader', re.M)),
                ('SourceGuardian', re.compile(r'sg_load\(|SourceGuardian')),
                ('ZendGuard', re.compile(r'<\?php @Zend;|Zend Optimizer|Zend Guard')))


def loader_of(head):
    for name, rx in LOADER_MARKS:
        if rx.search(head):
            return name
    return None


# --- extension usage (FR-CMPT-EXT-001) --------------------------------------------
USAGE = {
    'mysqli': [r'\bmysqli_\w+\s*\(', r'\bnew\s+\\?mysqli\b'], 'gd': [r'(?<![\w$>:])\bimage\w+\s*\('],
    'mbstring': [r'(?<![\w$>:])\bmb_\w+\s*\('], 'curl': [r'(?<![\w$>:])\bcurl_\w+\s*\('],
    'intl': [r'\bnew\s+\\?(?:NumberFormatter|IntlDateFormatter|Collator|Normalizer|Transliterator)\b',
             r'(?<![\w$>:])\b(?:intl|grapheme|idn|numfmt|datefmt)_\w+\s*\('],
    'zip': [r'\bnew\s+\\?ZipArchive\b', r'(?<![\w$>:])\bzip_\w+\s*\('],
    'pdo_mysql': [r'''['"]mysql:'''], 'pdo_pgsql': [r'''['"]pgsql:'''], 'pdo_sqlite': [r'''['"]sqlite:'''],
    'soap': [r'\bnew\s+\\?Soap(?:Client|Server)\b'], 'bcmath': [r'(?<![\w$>:])\bbc\w+\s*\('],
    'gmp': [r'(?<![\w$>:])\bgmp_\w+\s*\('], 'imagick': [r'\bnew\s+\\?Imagick\w*\b'],
    'redis': [r'\bnew\s+\\?Redis(?:Cluster)?\b'], 'memcached': [r'\bnew\s+\\?Memcached\b'],
    'apcu': [r'(?<![\w$>:])\bapcu_\w+\s*\('], 'ldap': [r'(?<![\w$>:])\bldap_\w+\s*\('],
    'xsl': [r'\bnew\s+\\?XSLTProcessor\b'], 'sqlite3': [r'\bnew\s+\\?SQLite3\b'],
    'pgsql': [r'(?<![\w$>:])\bpg_\w+\s*\('], 'odbc': [r'(?<![\w$>:])\bodbc_\w+\s*\('],
    'tidy': [r'(?<![\w$>:])\btidy_\w+\s*\(', r'\bnew\s+\\?tidy\b'],
}


def usage_patterns(exts, bc):
    """{ext: compiled regex} for the extensions of the old runtime."""
    removed = {e['extension']: e for e in bc.get('ext_removed', [])}
    out = {}
    for ext in exts:
        pats = USAGE.get(ext)
        if pats is None and ext in removed and removed[ext]['prefixes']:
            pats = [r'(?<![\w$>:])\b(?:%s)\w*\s*\(' % '|'.join(re.escape(p) for p in removed[ext]['prefixes'])]
        if pats is None and re.match(r'^[a-z][a-z0-9_]*$', ext):
            pats = [r'(?<![\w$>:])\b%s_\w+\s*\(' % re.escape(ext)]
        if pats:
            out[ext] = re.compile('|'.join(pats))
    return out


# --- one pass over the files -----------------------------------------------------
def scan_files(site_id, root, files, rules, usage=None, budget=None, loaders=True):
    """BC hits, loader files and extension usage in one read of every file."""
    comp = compile_rules(rules)
    code = [(rid, lvl, rx) for rid, lvl, rx, kind in comp if kind == 'code']
    ctor = [(rid, lvl) for rid, lvl, rx, kind in comp if kind == 'php4_ctor']
    hits, loader_files, counts = [], {}, {e: 0 for e in (usage or {})}
    read_for_loader = 0
    complete = True
    for path in files:
        if budget is not None and budget.over():
            complete = False
            break
        try:
            text = read_text(path)
        except OSError:
            continue
        rel = os.path.relpath(path, root)
        if loaders and read_for_loader < MAX_LOADER_FILES:
            read_for_loader += 1
            ld = loader_of(text[:4096])
            if ld:
                loader_files.setdefault(ld, []).append(rel)
        for ext, rx in (usage or {}).items():
            counts[ext] += len(rx.findall(text))
        if code:
            todo = [(rid, lvl, rx) for rid, lvl, rx in code if rx.search(text)]
            if todo:
                for n, line in enumerate(text.split('\n'), 1):
                    for rid, lvl, rx in todo:
                        if rx.search(line):
                            snip = line.strip()[:SNIPPET]
                            hits.append({'hit_id': hit_id(site_id, rel, n, rid, snip), 'site_id': site_id,
                                         'file': rel, 'line': n, 'rule_id': rid, 'level': lvl, 'snippet': snip,
                                         'source': 'bc_rules', 'waived': False, 'waiver': None})
        for rid, lvl in ctor:
            for n in php4_ctors(text):
                snip = text.split('\n')[n - 1].strip()[:SNIPPET]
                hits.append({'hit_id': hit_id(site_id, rel, n, rid, snip), 'site_id': site_id, 'file': rel,
                             'line': n, 'rule_id': rid, 'level': lvl, 'snippet': snip, 'source': 'bc_rules',
                             'waived': False, 'waiver': None})
    unread = max(0, len(files) - read_for_loader) if loaders else 0
    return {'hits': hits, 'loader_files': loader_files, 'loader_unread': unread, 'usage': counts,
            'complete': complete}


# --- frameworks (FR-CMPT-FWK-001) ------------------------------------------------
def composer_packages(root):
    p = os.path.join(root, 'composer.lock')
    try:
        with open(p, encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for pkg in (doc.get('packages') or []) + (doc.get('packages-dev') or []):
        if isinstance(pkg, dict) and pkg.get('name'):
            out[pkg['name']] = str(pkg.get('version') or '').lstrip('v')
    return out


def wp_version(root):
    try:
        text = read_text(os.path.join(root, 'wp-includes', 'version.php'))
    except OSError:
        return None
    m = re.search(r'''\$wp_version\s*=\s*['"]([^'"]+)['"]''', text)
    return m.group(1) if m else ''


def _version_tokens(cell):
    cell = re.sub(r'\([^)]*\)', '', cell)
    return [t.strip() for t in re.split(r',', cell) if t.strip()]


def matrix_row(rows, name, version):
    """Row of framework_php.tsv for NAME VERSION, or None."""
    for r in rows:
        if r['framework'].split(' ')[0].split('/')[0].lower() != name.lower():
            continue
        for tok in _version_tokens(r['versions']):
            m = re.match(r'^([\d.]+)\s*[–-]\s*([\d.]+)$', tok)
            if m:
                lo, hi = vkey(m.group(1)), vkey(m.group(2))
                n = len(m.group(2).split('.'))
                if lo <= vkey(version) and vkey(version)[:n] <= hi[:n]:
                    return r
                continue
            t = tok.rstrip('x').rstrip('.')
            if re.match(r'^[\d.]+$', t) and (version == t or version.startswith(t + '.')):
                return r
    return None


def frameworks(root, matrix_rows, bc, target_branch):
    """frameworks[] with supports_target True / False / 'unknown'."""
    found = []
    wp = wp_version(root)
    if wp is not None:
        found.append(('wordpress', wp or 'unknown'))
    pk = composer_packages(root)
    seen = set()
    for pkg, name in (bc.get('framework_packages') or {}).items():
        if pkg in pk and name not in seen:
            seen.add(name)
            found.append((name.lower(), pk[pkg]))
    out = []
    for name, ver in found:
        row = matrix_row(matrix_rows, name, ver)
        lo = (row or {}).get('php_min') or None
        hi = (row or {}).get('php_max') or None
        if row is None or lo is None:
            sup = 'unknown'
        elif vkey(target_branch)[:2] < vkey(lo)[:2]:
            sup = False
        elif hi is None:
            sup = 'unknown'
        else:
            sup = vkey(target_branch)[:2] <= vkey(hi)[:2]
        out.append({'name': name, 'version': ver, 'php_min': lo, 'php_max': hi, 'supports_target': sup})
    return out


def loaders_result(loader_files, unread, catalog_loaders, target_branch, runtime_exts=()):
    """loaders[] (FR-CMPT-LDR-001) with target_supported (BR-SCN-043)."""
    names = dict((k, len(v)) for k, v in loader_files.items())
    exts = ' '.join(runtime_exts).lower()
    if 'ioncube' in exts:
        names.setdefault('ionCube', 0)
    if 'sourceguardian' in exts:
        names.setdefault('SourceGuardian', 0)
    if 'zend guard' in exts or 'zend optimizer' in exts:
        names.setdefault('ZendGuard', 0)
    out = []
    for name, count in sorted(names.items()):
        out.append({'name': name, 'files_count': count, 'sample': (loader_files.get(name) or [None])[0],
                    'target_supported': loader_supports(name, target_branch, catalog_loaders),
                    'files_unread': unread})
    return out


def loader_supports(name, branch, catalog_loaders):
    cl = catalog_loaders or {}
    if name == 'ionCube':
        ic = cl.get('ioncube') or {}
        return branch in (ic.get('min_loader_by_branch') or {}) and branch not in (ic.get('no_loader_branches') or [])
    if name == 'SourceGuardian':
        sg = cl.get('sourceguardian') or {}
        return bool(sg.get('php_min')) and vkey(sg['php_min']) <= vkey(branch) <= vkey(sg.get('php_max') or '0')
    return False
