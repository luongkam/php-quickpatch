"""Dependencies: Composer platform (FR-CMPT-COMP-001/002), npm engines and
native addons (FR-CMPT-NPM-001/002).

Registries get only package names (BR-DATA-003); answers are cached 24 h in
STATE_DIR/feeds/cache/{packagist,npm}/. Composer and npm run only on a copy
in STATE_DIR/work/<plan_id>/ with --no-scripts --no-plugins (BR-CMPT-003).
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from . import semver

CACHE_TTL = 24 * 3600
DEFAULT_URLS = {'packagist_url': 'https://repo.packagist.org', 'npm_url': 'https://registry.npmjs.org'}
UNSTABLE = re.compile(r'(dev|alpha|beta|rc|patch\d*$)', re.I)


class RegistryError(Exception):
    pass


def registry_urls(feeds_dir):
    """[registry] packagist_url / npm_url of feeds/sources.conf (https only)."""
    urls = dict(DEFAULT_URLS)
    path = os.path.join(feeds_dir, 'sources.conf')
    if os.path.isfile(path):
        sect = None
        with open(path, encoding='utf-8') as f:
            lines = f.read().splitlines()
        for line in lines:
            line = line.strip()
            m = re.match(r'^\[(.+)\]$', line)
            if m:
                sect = m.group(1)
                continue
            if sect == 'registry' and '=' in line:
                k, v = (x.strip() for x in line.split('=', 1))
                if k in urls and v.startswith('https://'):
                    urls[k] = v.rstrip('/')
    return urls


def fetch_json(url, cache_path, offline=False, headers=None, now=None):
    """Cached GET (24 h); stale cache is used when the registry fails. Raises RegistryError."""
    now = time.time() if now is None else now
    cached = None
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, encoding='utf-8') as f:
                cached = json.load(f)
        except (OSError, ValueError):
            cached = None
    if cached and (offline or now - cached.get('fetched_at', 0) < CACHE_TTL):
        return cached['body'], 'CACHE'
    if offline:
        raise RegistryError('offline and no cached answer for %s' % url)
    if not url.startswith('https://'):
        raise RegistryError('non-https registry URL %s' % url)
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=dict({'User-Agent': 'php-quickpatch'}, **(headers or {})))
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read().decode('utf-8'))
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            tmp = cache_path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({'fetched_at': now, 'url': url, 'body': body}, f)
            os.replace(tmp, cache_path)
            return body, 'PRIMARY'
        except urllib.error.HTTPError as e:
            err = 'HTTP %s' % e.code
            if e.code == 404:
                break
        except (OSError, ValueError) as e:
            err = str(e)
        time.sleep(attempt)
    if cached:
        return cached['body'], 'STALE_CACHE'
    raise RegistryError('%s: %s' % (url, err))


def _cache_name(name):
    return re.sub(r'[^A-Za-z0-9._@-]', '~', name) + '.json'


# --- Composer ----------------------------------------------------------------------
def read_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def composer_blockers(root, target_patch):
    """Static part (no $NEW_BIN): require.php of every locked package and of the project."""
    lock = read_json(os.path.join(root, 'composer.lock'))
    proj = read_json(os.path.join(root, 'composer.json'))
    out, ext_req = [], set()
    if proj and isinstance((proj.get('require') or {}).get('php'), str):
        c = proj['require']['php']
        if semver.satisfies(target_patch, c) is False:
            out.append({'package': proj.get('name') or '(project)', 'version': proj.get('version') or '-',
                        'constraint': c, 'reason': 'composer.json require.php', 'dev': False})
    if not lock:
        return out, sorted(ext_req), proj is not None
    for dev, pkgs in ((False, lock.get('packages') or []), (True, lock.get('packages-dev') or [])):
        for p in pkgs:
            req = p.get('require') or {}
            for k in req:
                if k.startswith('ext-'):
                    ext_req.add(k[4:].lower())
            c = req.get('php')
            if isinstance(c, str) and semver.satisfies(target_patch, c) is False:
                out.append({'package': p.get('name'), 'version': str(p.get('version') or '').lstrip('v'),
                            'constraint': c, 'reason': 'require.php', 'dev': dev})
    return out, sorted(ext_req), True


def expand_p2(versions):
    """Packagist p2 'minified' lists: each entry inherits the keys of the previous one."""
    out, prev = [], {}
    for v in versions:
        cur = dict(prev)
        for k, val in v.items():
            if val == '__unset':
                cur.pop(k, None)
            else:
                cur[k] = val
        out.append(cur)
        prev = cur
    return out


def min_compatible(name, current, target_patch, feeds_dir, offline=False):
    """FR-CMPT-COMP-002: smallest stable version >= CURRENT whose require.php accepts TARGET_PATCH.
    -> (version | 'none' | 'unknown', error message or None)."""
    urls = registry_urls(feeds_dir)
    url = '%s/p2/%s.json' % (urls['packagist_url'], urllib.parse.quote(name))
    try:
        body, _ = fetch_json(url, os.path.join(feeds_dir, 'cache', 'packagist', _cache_name(name)), offline)
    except RegistryError as e:
        return 'unknown', str(e)
    vers = expand_p2(((body.get('packages') or {}).get(name)) or [])
    best = None
    for v in vers:
        ver = str(v.get('version') or '').lstrip('v')
        if not ver or UNSTABLE.search(ver) or semver.vtuple(ver) < semver.vtuple(current):
            continue
        c = (v.get('require') or {}).get('php')
        ok = True if c is None else semver.satisfies(target_patch, c)
        if ok and (best is None or semver.vtuple(ver) < semver.vtuple(best)):
            best = ver
    return (best or 'none'), None


def platform_check(root, work, new_bin, composer_phar, target_patch, timeout=600):
    """FR-CMPT-COMP-001 (2): check-platform-reqs + why-not on a copy of composer.json/lock.
    -> {'exit_code', 'blockers', 'output'}; the copy is removed."""
    os.makedirs(work, exist_ok=True)
    try:
        for f in ('composer.json', 'composer.lock'):
            if os.path.isfile(os.path.join(root, f)):
                shutil.copyfile(os.path.join(root, f), os.path.join(work, f))
        cj = read_json(os.path.join(work, 'composer.json')) or {}
        cj.setdefault('config', {}).setdefault('platform', {})['php'] = target_patch
        with open(os.path.join(work, 'composer.json'), 'w', encoding='utf-8') as f:
            json.dump(cj, f, indent=2)
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'COMPOSER_HOME': os.path.join(work, '.composer'),
               'COMPOSER_CACHE_DIR': os.path.join(work, '.cache'), 'COMPOSER_ALLOW_SUPERUSER': '1',
               'COMPOSER_NO_INTERACTION': '1', 'COMPOSER_DISABLE_NETWORK': '1', 'HOME': work}
        base = [new_bin, composer_phar, '--no-plugins', '--no-scripts', '--no-interaction', '--working-dir=' + work]
        p = subprocess.run(base + ['check-platform-reqs', '--lock'], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, env=env, timeout=timeout)
        out = p.stdout.decode('utf-8', 'replace')
        w = subprocess.run(base + ['why-not', 'php', target_patch], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           env=env, timeout=timeout)
        blockers = []
        for line in w.stdout.decode('utf-8', 'replace').splitlines():
            m = re.match(r'^(\S+/\S+)\s+(\S+)\s+requires\s+php\s+\((.+)\)', line.strip())
            if m:
                blockers.append({'package': m.group(1), 'version': m.group(2), 'constraint': m.group(3),
                                 'reason': 'why-not php %s' % target_patch, 'dev': False})
        return {'exit_code': p.returncode, 'blockers': blockers, 'output': out[-4000:]}
    finally:
        shutil.rmtree(work, ignore_errors=True)


# --- npm ---------------------------------------------------------------------------
def npm_engines(root, target_patch, feeds_dir, offline=False, max_lookups=300):
    """FR-CMPT-NPM-001 -> (violations, unknown, warnings)."""
    pj = read_json(os.path.join(root, 'package.json')) or {}
    lock = read_json(os.path.join(root, 'package-lock.json'))
    viol, unknown, warns = [], [], []
    eng = (pj.get('engines') or {}).get('node') if isinstance(pj.get('engines'), dict) else None
    if eng and semver.satisfies(target_patch, eng, npm=True) is False:
        viol.append({'package': pj.get('name') or '(app)', 'version': pj.get('version'), 'engines': eng,
                     'dev': False, 'severity': 'error'})
    if lock is None:
        if os.path.isfile(os.path.join(root, 'yarn.lock')) or os.path.isfile(os.path.join(root, 'pnpm-lock.yaml')):
            warns.append('yarn.lock/pnpm-lock.yaml only: run `yarn npm audit` / `pnpm audit` and check engines by hand')
        return viol, unknown, warns
    urls = registry_urls(feeds_dir)
    lookups = 0
    entries = []
    if isinstance(lock.get('packages'), dict):
        for key, p in lock['packages'].items():
            if not key or not isinstance(p, dict) or p.get('link'):
                continue
            entries.append((key.split('node_modules/')[-1], p.get('version'), p.get('engines'), bool(p.get('dev')), True))
    else:                                    # lockfileVersion 1: no engines recorded
        def walk(deps):
            for name, d in (deps or {}).items():
                entries.append((name, d.get('version'), None, bool(d.get('dev')), False))
                walk(d.get('dependencies'))
        walk(lock.get('dependencies'))
    for name, ver, engines, dev, has_field in entries:
        c = None
        if isinstance(engines, dict):
            c = engines.get('node')
        elif isinstance(engines, list):       # old ["node >= 0.8"] form
            c = next((e.split('node', 1)[1].strip() for e in engines if str(e).startswith('node')), None)
        if c is None and engines is None:
            if lookups >= max_lookups:
                unknown.append({'package': name, 'version': ver, 'reason': 'lookup limit'})
                continue
            lookups += 1
            try:
                body, _ = fetch_json('%s/%s' % (urls['npm_url'], urllib.parse.quote(name, safe='@')),
                                     os.path.join(feeds_dir, 'cache', 'npm', _cache_name(name)), offline,
                                     headers={'Accept': 'application/vnd.npm.install-v1+json'})
                c = (((body.get('versions') or {}).get(ver) or {}).get('engines') or {}).get('node')
            except RegistryError as e:
                unknown.append({'package': name, 'version': ver, 'reason': str(e)})
                continue
        if not c:
            continue
        ok = semver.satisfies(target_patch, c, npm=True)
        if ok is False:
            viol.append({'package': name, 'version': ver, 'engines': c, 'dev': dev,
                         'severity': 'warning' if dev else 'error'})
        elif ok is None:
            unknown.append({'package': name, 'version': ver, 'reason': 'engines %r not understood' % c})
    return viol, unknown, warns


def find_addons(root):
    """Native addons (DOC-SRS-QP-SCN-NODE-001 §1.3): binding.gyp, or a compiled *.node file."""
    nm = os.path.join(root, 'node_modules')
    out = {}
    if not os.path.isdir(nm):
        return []
    for dp, dns, fns in os.walk(nm):
        dns[:] = [d for d in dns if d != '.bin']
        if 'binding.gyp' in fns or any(f.endswith('.node') for f in fns):
            rel = os.path.relpath(dp, nm).split(os.sep)
            name = '/'.join(rel[:2]) if rel[0].startswith('@') else rel[0]
            if 'node_modules' in rel[1:]:
                idx = len(rel) - 1 - rel[::-1].index('node_modules')
                tail = rel[idx + 1:]
                name = '/'.join(tail[:2]) if tail and tail[0].startswith('@') else (tail[0] if tail else name)
            out.setdefault(name, True)
    return sorted(out)


def _lines(path):
    with open(path, encoding='utf-8') as f:
        return f.read().splitlines()


def _as_owner(cmd, owner):
    if owner and os.geteuid() == 0 and owner != 'root' and shutil.which('runuser'):
        return ['runuser', '-u', owner, '--'] + cmd
    return cmd


def addon_load(root, work, new_bin, owner, plan_dir, site_key, timeout=900):
    """BR-SCN-022 / BR-SCN-024 on a copy: regenerate a v1 lockfile with the new npm
    (diff kept in the plan), rebuild, then require() every addon with $NEW_BIN."""
    if os.path.lexists(work):
        shutil.rmtree(work)
    shutil.copytree(root, work, symlinks=True, ignore=shutil.ignore_patterns('.git'))
    npm_cli = os.path.join(os.path.dirname(os.path.dirname(new_bin)), 'lib', 'node_modules', 'npm', 'bin', 'npm-cli.js')
    log = []
    if owner and os.geteuid() == 0 and owner != 'root':
        subprocess.run(['chown', '-R', owner, work], check=False)
    env = dict(os.environ, npm_config_ignore_scripts='true', HOME=work)
    lock = read_json(os.path.join(work, 'package-lock.json'))
    if lock and lock.get('lockfileVersion') == 1 and os.path.isfile(npm_cli):
        before = _lines(os.path.join(work, 'package-lock.json'))
        p = subprocess.run(_as_owner([new_bin, npm_cli, 'install', '--package-lock-only', '--ignore-scripts'], owner),
                           cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        log.append(('npm install --package-lock-only', p.returncode))
        after = _lines(os.path.join(work, 'package-lock.json'))
        with open(os.path.join(plan_dir, 'lockfile-%s.diff' % site_key), 'w', encoding='utf-8') as f:
            f.writelines(l + '\n' for l in difflib.unified_diff(before, after, 'package-lock.json', 'package-lock.json (new npm)', lineterm=''))
    results = []
    for name in find_addons(work):
        rb = 0
        if os.path.isfile(npm_cli):
            p = subprocess.run(_as_owner([new_bin, npm_cli, 'rebuild', name], owner), cwd=work, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            rb = p.returncode
        q = subprocess.run(_as_owner([new_bin, '-e', 'require(%s)' % json.dumps(name)], owner), cwd=work,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        results.append({'package': name, 'rebuild_exit': rb, 'load_ok': q.returncode == 0,
                        'detail': q.stdout.decode('utf-8', 'replace')[-300:] if q.returncode else None})
    shutil.rmtree(work, ignore_errors=True)
    return results, log
