"""FR-CMPT-INI-001: ini directives removed in (OLD, NEW] (BR-SCN-046).

Looks at the php.ini and conf.d of the old runtime, the FPM pool of the site,
.user.ini and .htaccess under the docroot and the vhost files of the site
binding. Read only.
"""
import os
import re

from .scan import SKIP_DIRS, in_range

POOL_DIRS = ('/etc/php/*/fpm/pool.d', '/etc/opt/remi/php*/php-fpm.d', '/etc/php[0-9]*/php-fpm.d', '/etc/php-fpm.d')


def _patterns(directive):
    d = re.escape(directive)
    if directive.endswith('*'):
        d = re.escape(directive[:-1]) + r'[\w.]*'
    return [
        ('ini', re.compile(r'^\s*(%s)\s*=' % d, re.I)),
        ('pool', re.compile(r'^\s*php_(?:admin_)?(?:value|flag)\[(%s)\]\s*=' % d, re.I)),
        ('apache', re.compile(r'^\s*php_(?:admin_)?(?:value|flag)\s+(%s)\b' % d, re.I)),
    ]


def removed(bc, old, new):
    return [r for r in bc.get('ini_removed', []) if in_range(r['removed_in'], old, new)]


def scan_file(path, rules, kinds, opcache_rx=None, root=None):
    out = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = f.read().split('\n')
    except OSError:
        return out
    shown = os.path.relpath(path, root) if root and path.startswith(root.rstrip('/') + '/') else path
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith((';', '#')):
            continue
        for r in rules:
            for kind, rx in r['_rx']:
                if kind in kinds:
                    m = rx.search(line)
                    if m:
                        out.append({'file': shown, 'line': n, 'directive': m.group(1), 'removed_in': r['removed_in']})
        if opcache_rx is not None and 'ini' in kinds and opcache_rx.search(line):
            out.append({'file': shown, 'line': n, 'directive': 'zend_extension=opcache', 'removed_in': '8.5'})
    return out


def pool_files(endpoint):
    """FPM pool files whose `listen` is the endpoint of the site."""
    import glob
    ep = (endpoint or '').replace('unix:', '')
    out = []
    for d in POOL_DIRS:
        for f in glob.glob(os.path.join(d, '*.conf')):
            try:
                with open(f, encoding='utf-8', errors='replace') as fh:
                    text = fh.read()
            except OSError:
                continue
            for m in re.finditer(r'^\s*listen\s*=\s*(\S+)', text, re.M):
                if ep and (m.group(1) == ep or (':' in ep and m.group(1).endswith(':' + ep.rsplit(':', 1)[1]))):
                    out.append(f)
    return sorted(set(out))


def findings(bc, old, new, site, runtime, budget=None):
    rules = removed(bc, old, new)
    for r in rules:
        r['_rx'] = _patterns(r['directive'])
    opc = re.compile(bc['opcache_line']) if bc.get('opcache_line') and in_range('8.5', old, new) else None
    out = []
    files = []
    for d in runtime.get('ini_scan_dirs') or []:
        if os.path.isdir(d):
            files += [(os.path.join(d, f), ('ini',)) for f in sorted(os.listdir(d)) if f.endswith('.ini')]
    for ini in runtime.get('ini_files') or []:
        files.append((ini, ('ini',)))
    for f in pool_files(site.get('runtime_endpoint')):
        files.append((f, ('ini', 'pool')))
    for ref in (site.get('binding_ref') or '').split(','):
        p = ref.rsplit(':', 1)[0]
        if p and os.path.isfile(p) and p.startswith('/etc/'):
            files.append((p, ('apache',)))
    root = site.get('docroot')
    if root and os.path.isdir(root):
        for dp, dns, fns in os.walk(root):
            if budget is not None and budget.over():
                break
            dns[:] = [x for x in dns if x not in SKIP_DIRS]
            for fn in fns:
                if fn == '.user.ini':
                    files.append((os.path.join(dp, fn), ('ini',)))
                elif fn == '.htaccess':
                    files.append((os.path.join(dp, fn), ('apache',)))
    seen = set()
    for path, kinds in files:
        if path in seen:
            continue
        seen.add(path)
        out += scan_file(path, rules, kinds, opc, root)
    for r in rules:
        r.pop('_rx', None)
    return out
