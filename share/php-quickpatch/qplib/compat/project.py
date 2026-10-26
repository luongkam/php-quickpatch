"""Compatibility scan of Node.js project directories with a target branch (CR-01, `compat --path`).

For code that does not run on this machine (AWS Lambda, containers built
elsewhere, a repository checkout): no runtime or site is needed. Each
directory holding a package.json (outside node_modules) is a project. Read
only: nothing under the scanned paths is written; native addons are loaded on
a copy in STATE_DIR/work/.
"""
import os
import re
import time
import urllib.parse

from .. import errors
from ..envelope import iso_ms
from . import deps, scan as S, semver

MAX_DEPTH = 6
TEXT_MAX = 512 * 1024
SKIP = S.SKIP_DIRS | {'.serverless', '.aws-sam', 'cdk.out', 'dist', 'build', 'coverage', '.terraform'}
DECL_FILES = re.compile(r'(\.ya?ml|\.json|\.tf|\.toml|\.[cm]?[jt]s|Dockerfile[^/]*|\.nvmrc|\.node-version|\.tool-versions|'
                        r'\.sh|Makefile)$')
# Where a Node.js version is declared, besides package.json engines (kept apart: FR-CMPT-NPM-001).
DECL = [
    ('lambda_runtime', re.compile(r'\bnodejs(\d+)\.x\b')),
    ('cdk_runtime', re.compile(r'\bRuntime\.NODEJS_(\d+)_X\b')),
    ('container_image', re.compile(r'\b(?:FROM\s+|image:\s*["\']?)(?:public\.ecr\.aws/lambda/)?node(?:js)?:(\d+)\b', re.I)),
    ('ci_node_version', re.compile(r'\bnode-version\s*:\s*["\']?(\d+)')),
    ('tool_versions', re.compile(r'^\s*nodejs\s+(\d+)', re.M)),
]
# Packages whose replacement is a migration of its own, whatever npm says about them.
KNOWN = {
    'aws-sdk': {'replacement': '@aws-sdk/client-* (AWS SDK for JavaScript v3)',
                'reason': {'en': 'AWS SDK for JavaScript v2 reached end-of-support on 2025-09-08; the Lambda '
                                 'Node.js 18+ runtimes include only v3',
                           'vi': 'AWS SDK for JavaScript v2 hết hỗ trợ từ 2025-09-08; runtime Lambda Node.js '
                                 '18 trở lên chỉ có sẵn v3'},
                'code': re.compile(r'''(?:require\s*\(\s*|from\s+)['"]aws-sdk(?:/[\w/-]+)?['"]''')},
}


# How a project is deployed (CR-03): Lambda functions updated by scripts (no IaC: the runtime is set in AWS),
# static sites (Next.js `output: "export"` synced to S3).
LAMBDA_CMD = re.compile(r'\baws\s+lambda\s+(update-function-code|create-function|update-function-configuration)\b')
FN_LITERAL = re.compile(r'--function-name[=\s]+["\']?([A-Za-z0-9_-]+)')
FN_VAR = re.compile(r'--function-name[=\s]+["\']?\$\{?([A-Za-z_][A-Za-z0-9_]*)')
REGION = re.compile(r'--region[=\s]+["\']?([a-z]{2}-[a-z]+-\d)')
NPM_INSTALL = re.compile(r'\bnpm\s+(install|i)\b(?![^\n]*--omit=dev)(?![^\n]*--production)')
NPM_CI = re.compile(r'\bnpm\s+ci\b')
S3_SYNC = re.compile(r'\baws\s+s3\s+(sync|cp)\b[^\n]*s3://["\']?\$?\{?([\w.$-]+)')
NEXT_EXPORT = re.compile(r'output\s*:\s*["\']export["\']')


def deploy_info(root, nested=()):
    """{kind: lambda|static_site|None, functions[], scripts[], region, npm_install, static_export, buckets[]}."""
    info = {'kind': None, 'functions': [], 'scripts': [], 'region': None, 'npm_install': False, 'static_export': False,
            'buckets': []}
    for fn in os.listdir(root) if os.path.isdir(root) else []:
        if fn.startswith('next.config.'):
            t = _text(os.path.join(root, fn)) or ''
            if NEXT_EXPORT.search(t):
                info['static_export'] = True
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP and not d.startswith('.') and os.path.join(dp, d) not in nested)
        for f in sorted(fns):
            if not (f.endswith('.sh') or f == 'Makefile'):
                continue
            path = os.path.join(dp, f)
            text = _text(path) or ''
            rel = os.path.relpath(path, root)
            lam = LAMBDA_CMD.search(text)
            s3 = S3_SYNC.search(text)
            if not lam and not s3:
                continue
            info['scripts'].append(rel)
            if lam:
                info['kind'] = 'lambda'
                names = FN_LITERAL.findall(text)
                for var in FN_VAR.findall(text):
                    names += re.findall(r'\b%s=["\']?([A-Za-z0-9_-]+)' % re.escape(var), text)
                for n in names:
                    if n not in info['functions']:
                        info['functions'].append(n)
                m = REGION.search(text)
                info['region'] = info['region'] or (m.group(1) if m else None)
                if NPM_INSTALL.search(text) and not NPM_CI.search(text):
                    info['npm_install'] = True
            elif s3 and info['kind'] is None:
                info['kind'] = 'static_site'
                for v in S3_SYNC.findall(text):
                    var = v[1].lstrip('$').strip('{}')
                    vals = re.findall(r'\b%s=["\']?([\w.-]+)' % re.escape(var), text)
                    for b in vals or [v[1]]:
                        if b not in info['buckets']:
                            info['buckets'].append(b)
    if info['kind'] is None and info['static_export']:
        info['kind'] = 'static_site'
    return info


# AWS SDK v2 -> v3: package of every v2 service client (sizes the migration, FR-CMPT-NPM-002 style).
SDK_V3 = {'DynamoDB.DocumentClient': '@aws-sdk/lib-dynamodb', 'DynamoDB': '@aws-sdk/client-dynamodb',
          'SES': '@aws-sdk/client-ses', 'SESV2': '@aws-sdk/client-sesv2', 'S3': '@aws-sdk/client-s3',
          'SQS': '@aws-sdk/client-sqs', 'SNS': '@aws-sdk/client-sns', 'Lambda': '@aws-sdk/client-lambda',
          'SecretsManager': '@aws-sdk/client-secrets-manager', 'SSM': '@aws-sdk/client-ssm',
          'CognitoIdentityServiceProvider': '@aws-sdk/client-cognito-identity-provider', 'KMS': '@aws-sdk/client-kms'}
SDK_NEW = re.compile(r'new\s+AWS\.([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)?)\s*\(')
SDK_PROMISE = re.compile(r'\.promise\s*\(\s*\)')
# Credentials that a browser bundle ships to every visitor (public env prefixes of Next.js, Vite, CRA, Nuxt).
CLIENT_SECRET = re.compile(r'(?:process\.env|import\.meta\.env)\.((?:NEXT_PUBLIC|VITE|REACT_APP|NUXT_PUBLIC)_[A-Z0-9_]*'
                           r'(?:PASS(?:WORD)?|SECRET|TOKEN|PRIVATE|API_?KEY|CREDENTIAL|AUTH)[A-Z0-9_]*)')
ENV_VAR = re.compile(r'process\.env\.([A-Z_][A-Z0-9_]*)|process\.env\[["\']([A-Z_][A-Z0-9_]*)["\']\]')
IAC_NAMES = ('serverless.yml', 'serverless.yaml', 'template.yaml', 'template.yml', 'samconfig.toml', '*.tf',
             'cdk.json', 'cdk.out')


def code_facts(root, files):
    """SDK v2 usage by service, credentials in a browser bundle, environment variables read by the code."""
    services, promise, secrets, env = {}, 0, [], set()
    for path in files:
        text = _text(path)
        if not text:
            continue
        rel = os.path.relpath(path, root)
        for n, line in enumerate(text.split('\n'), 1):
            for m in SDK_NEW.finditer(line):
                s = services.setdefault(m.group(1), {'service': m.group(1), 'package': SDK_V3.get(m.group(1)) or
                                                     '@aws-sdk/client-%s' % m.group(1).split('.')[0].lower(), 'sites': []})
                s['sites'].append({'file': rel, 'line': n})
            promise += len(SDK_PROMISE.findall(line))
            for m in CLIENT_SECRET.finditer(line):
                secrets.append({'file': rel, 'line': n, 'name': m.group(1)})
            for m in ENV_VAR.finditer(line):
                env.add(m.group(1) or m.group(2))
    return {'sdk_v2_services': sorted(services.values(), key=lambda s: s['service']), 'sdk_v2_promise_calls': promise,
            'client_secrets': secrets, 'env_vars': sorted(env)}


def ignored_iac(paths):
    """IaC files that a .gitignore of the scanned paths keeps out of the repository (ask the customer for them)."""
    import fnmatch
    out = []
    for root in paths:
        for dp, dns, fns in os.walk(os.path.realpath(root)):
            dns[:] = [d for d in dns if d not in SKIP and not d.startswith('.')]
            if '.gitignore' in fns:
                for line in (_text(os.path.join(dp, '.gitignore')) or '').split('\n'):
                    pat = line.strip().lstrip('/')
                    if pat and not pat.startswith('#') and any(fnmatch.fnmatch(n, pat) or pat == n for n in IAC_NAMES):
                        out.append({'gitignore': os.path.relpath(os.path.join(dp, '.gitignore'), os.path.realpath(root)),
                                    'pattern': pat})
    return out


def fix_trial(work, root, lockname, fs, offline, timeout=300):
    """`npm audit fix --package-lock-only` on a copy of package.json + lockfile, then OSV again on the new lockfile:
    which findings the automatic fix removes and which remain (needs npm and the network)."""
    import shutil
    import subprocess
    npm = shutil.which('npm')
    if offline or not npm:
        return {'ran': False, 'reason': 'offline' if offline else 'npm not found'}
    d = os.path.join(work, 'fix-trial', re.sub(r'[^\w.-]', '_', os.path.basename(root)))
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for f in ('package.json', lockname, '.npmrc'):
        if os.path.isfile(os.path.join(root, f)):
            shutil.copy2(os.path.join(root, f), os.path.join(d, f))
    try:
        env = dict(os.environ, npm_config_fetch_retries='0', npm_config_fetch_timeout='60000', npm_config_audit='true')
        p = subprocess.run([npm, 'audit', 'fix', '--package-lock-only', '--ignore-scripts', '--no-fund'], cwd=d,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'ran': False, 'reason': str(e)[:200]}
    _, pkgs = lock_packages(d)
    if not pkgs:
        return {'ran': False, 'reason': 'npm audit fix: %s' % p.stdout.decode('utf-8', 'replace')[-200:]}
    vul, meta = vulnerabilities(fs, os.path.join(d, lockname), pkgs, offline)
    if vul is None:
        return {'ran': False, 'reason': (meta or {}).get('error') or 'OSV'}
    return {'ran': True, 'exit_code': p.returncode,
            'remaining': [{'package': v['package'], 'version': v['version'], 'severity': v['severity'], 'dev': v['dev']}
                          for v in vul]}


def lock_parents(root):
    """{package: set(direct dependencies that pull it in)} from package-lock v2/v3 (empty for v1)."""
    lock = deps.read_json(os.path.join(root, 'package-lock.json')) or deps.read_json(os.path.join(root, 'npm-shrinkwrap.json'))
    pk = (lock or {}).get('packages')
    if not isinstance(pk, dict):
        return {}
    up = {}
    rootp = pk.get('') or {}
    direct = set()
    for k in ('dependencies', 'devDependencies', 'optionalDependencies'):
        direct |= set((rootp.get(k) or {}).keys())
    for key, p in pk.items():
        if not key or not isinstance(p, dict):
            continue
        name = key.split('node_modules/')[-1]
        for k in ('dependencies', 'optionalDependencies', 'peerDependencies'):
            for child in (p.get(k) or {}):
                up.setdefault(child, set()).add(name)
    out = {}
    for name in up:
        seen, todo, found = set(), [name], set()
        while todo:
            n = todo.pop()
            for par in up.get(n, ()):
                if par in seen:
                    continue
                seen.add(par)
                if par in direct:
                    found.add(par)
                else:
                    todo.append(par)
        out[name] = found
    out['__direct__'] = direct
    return out


def find_projects(paths, budget=None):
    """Directories with a package.json, outside node_modules and build output."""
    out = []
    for root in paths:
        root = os.path.realpath(root)
        if os.path.isfile(os.path.join(root, 'package.json')):
            out.append(root)
        base = root.count(os.sep)
        for dp, dns, fns in os.walk(root):
            dns[:] = sorted(d for d in dns if d not in SKIP and not d.startswith('.'))
            if dp.count(os.sep) - base >= MAX_DEPTH:
                dns[:] = []
            if dp != root and 'package.json' in fns:
                out.append(dp)
            if budget is not None and budget.over():
                break
    seen, res = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            res.append(p)
    return res


def _text(path):
    try:
        if os.path.getsize(path) > TEXT_MAX:
            return None
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return None


def declarations(root, own_projects=()):
    """Node.js versions declared in IaC, Dockerfiles, CI and version files of ROOT (not of nested projects)."""
    out = []
    nested = [p for p in own_projects if p != root and p.startswith(root.rstrip('/') + '/')]
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP and (not d.startswith('.') or d == '.github')
                        and os.path.join(dp, d) not in nested)
        for fn in sorted(fns):
            path = os.path.join(dp, fn)
            if fn in ('package-lock.json', 'package.json', 'npm-shrinkwrap.json') or not DECL_FILES.search(fn):
                continue
            text = _text(path)
            if text is None:
                continue
            rel = os.path.relpath(path, root)
            if fn in ('.nvmrc', '.node-version'):
                m = re.match(r'\s*v?(\d+)', text)
                if m:
                    out.append({'file': rel, 'line': 1, 'kind': 'version_file', 'text': text.strip()[:80],
                                'branch': m.group(1), 'path': path, 'code_uri': None})
                continue
            lines = text.split('\n')
            for n, line in enumerate(lines, 1):
                for kind, rx in DECL:
                    for m in rx.finditer(line):
                        d = {'file': rel, 'line': n, 'kind': kind, 'text': line.strip()[:160], 'branch': m.group(1),
                             'path': path, 'code_uri': None}
                        if kind == 'lambda_runtime':
                            d['code_uri'] = code_uri(lines, n - 1, dp)
                        out.append(d)
    return out


CODE_URI = re.compile(r'^\s*(?:CodeUri|codeUri|handler|Handler)\s*:\s*["\']?([^"\'\s#]+)')


def code_uri(lines, i, base):
    """CodeUri (SAM) of the function whose Runtime is on line I, else the directory of its Handler; only keys of
    the same block (same indentation, no line with less indentation in between) count."""
    ind = len(lines[i]) - len(lines[i].lstrip())
    block = []
    for rng in (range(i - 1, -1, -1), range(i + 1, len(lines))):
        for j in rng:
            ln = lines[j]
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            k = len(ln) - len(ln.lstrip())
            if k < ind:
                break
            if k == ind:
                m = CODE_URI.match(ln)
                if m:
                    block.append((ln.strip().split(':')[0].lower(), m.group(1)))
    uri = next((v for k, v in block if k == 'codeuri'), None)
    if uri is None:
        h = next((v for k, v in block if k == 'handler'), None)
        uri = os.path.dirname(h) if h else None
    return os.path.normpath(os.path.join(base, uri)) if uri else None


def lock_packages(root):
    """[(name, version, dev)] of package-lock.json / npm-shrinkwrap.json (v1, v2, v3)."""
    lock = None
    for f in ('package-lock.json', 'npm-shrinkwrap.json'):
        lock = deps.read_json(os.path.join(root, f))
        if lock is not None:
            break
    out = []
    if lock is None:
        return None, out
    if isinstance(lock.get('packages'), dict):
        for key, p in lock['packages'].items():
            if key and isinstance(p, dict) and not p.get('link') and p.get('version'):
                out.append((key.split('node_modules/')[-1], p['version'], bool(p.get('dev'))))
    else:
        def walk(d):
            for name, x in (d or {}).items():
                if x.get('version'):
                    out.append((name, x['version'], bool(x.get('dev'))))
                walk(x.get('dependencies'))
        walk(lock.get('dependencies'))
    seen, res = set(), []
    for p in out:
        if p[:2] not in seen:
            seen.add(p[:2])
            res.append(p)
    return f, res


def _vkey(v):
    return semver.vtuple(v or '0')


def fix_target(current, by_advisory):
    """Version that fixes every advisory: per advisory the smallest fixed version above CURRENT (same major
    line first), then the highest of those. -> (version | None, new major?, advisories with no fix)."""
    picks, unfixed = [], []
    for vid, a in sorted(by_advisory.items()):
        if vid.startswith('MAL-'):
            unfixed.append(vid)
            continue
        cands = sorted({f for f in a.get('fixed') or [] if _vkey(f) > _vkey(current)}, key=_vkey)
        if not cands:
            unfixed.append(vid)
            continue
        same = [f for f in cands if _vkey(f)[0] == _vkey(current)[0]]
        picks.append(same[0] if same else cands[0])
    if not picks:
        return None, None, unfixed
    best = max(picks, key=_vkey)
    return best, _vkey(best)[0] != _vkey(current)[0], unfixed


def vulnerabilities(fs, lockfile, pkgs, offline):
    """OSV (SRC-007) findings of the locked packages, with the version that fixes each one."""
    from ..feeds import osv
    from ..feeds.http import FetchError
    from ..feeds.query import Bundle
    kev = []
    try:
        with Bundle(fs) as b:
            kev = [r['cve_id'] for r in b.tsv('kev.tsv')]
    except LookupError:
        pass
    dev = {(n, v): d for n, v, d in pkgs}
    try:
        found, meta = osv.library_check(fs, 'npm', lockfile, [(n, v) for n, v, _ in pkgs], offline=offline,
                                        kev_ids=kev)
    except FetchError as e:
        return None, {'error': e.message}
    out = []
    for f in found:
        to, major, unfixed = fix_target(f['version'], f.get('by_advisory') or {})
        out.append(dict(f, dev=dev.get((f['package'], f['version']), False), fix_version=to, major_bump=major,
                        unfixed_advisories=unfixed))
    rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'unknown': 4}
    out.sort(key=lambda f: (rank.get(f['severity'], 5), f['dev'], f['package']))
    return out, meta


def direct_deps(root):
    pj = deps.read_json(os.path.join(root, 'package.json')) or {}
    out = {}
    for key, dev in (('dependencies', False), ('devDependencies', True), ('optionalDependencies', False)):
        for n, c in (pj.get(key) or {}).items():
            out.setdefault(n, (str(c), dev))
    return pj, out


def deprecated(root, pkgs, feeds_dir, offline, lang, files):
    """Direct dependencies marked deprecated on the npm registry, plus KNOWN migrations (with their call sites)."""
    _, direct = direct_deps(root)
    locked = {n: v for n, v, _ in pkgs}
    urls = deps.registry_urls(feeds_dir)
    out, unknown = [], []
    for name in sorted(direct):
        ver = locked.get(name)
        note = None
        if name in KNOWN:
            k = KNOWN[name]
            note = {'package': name, 'version': ver, 'dev': direct[name][1], 'source': 'catalog',
                    'message': k['reason'].get(lang) or k['reason']['en'], 'replacement': k['replacement'],
                    'call_sites': []}
            for path in files:
                text = _text(path)
                if text and k['code'].search(text):
                    for n, line in enumerate(text.split('\n'), 1):
                        if k['code'].search(line):
                            note['call_sites'].append({'file': os.path.relpath(path, root), 'line': n})
        if ver:
            try:
                body, _ = deps.fetch_json('%s/%s' % (urls['npm_url'], urllib.parse.quote(name, safe='@')),
                                          os.path.join(feeds_dir, 'cache', 'npm', deps._cache_name(name)), offline,
                                          headers={'Accept': 'application/vnd.npm.install-v1+json'})
                msg = ((body.get('versions') or {}).get(ver) or {}).get('deprecated')
                if msg:
                    if note is None:
                        note = {'package': name, 'version': ver, 'dev': direct[name][1], 'source': 'npm',
                                'message': str(msg)[:300], 'replacement': None, 'call_sites': []}
                    else:
                        note['npm_message'] = str(msg)[:300]
            except deps.RegistryError as e:
                unknown.append({'package': name, 'version': ver, 'reason': str(e)[:200]})
        if note:
            out.append(note)
    return out, unknown


# --- lifecycle (feeds bundle) -------------------------------------------------------
def lifecycle(fs, today, current, target, min_days=365):
    """Status and EOL of the current and target branches, and the branch BR-ASMT-002 would recommend."""
    from .. import assess as A
    from ..feeds import risk as R
    from ..feeds.query import Bundle
    try:
        with Bundle(fs) as b:
            ev = A.Evaluator(b, today)
            table = A.branch_table(ev, 'node')
            bundle_id = getattr(b, 'bundle_id', None) or os.path.basename(getattr(b, 'path', '') or '')
            exposure = {}
            for r in table:                    # vulnerabilities left in the newest release of the current branch
                if r['branch'] == current and r['latest']:
                    try:
                        e = ev.version('node', r['latest'])['exposure']
                        exposure = {'version': r['latest'], 'critical': e['n_crit'], 'high': e['n_high'],
                                    'medium': e['n_med'], 'low': e['n_low'], 'kev': e['n_kev']}
                    except (LookupError, KeyError):
                        exposure = {}
    except LookupError:
        return None
    rows = {r['branch']: r for r in table}
    cut = A.add_days(today, min_days)

    def info(branch):
        r = rows.get(branch)
        if r is None:
            return {'branch': branch, 'status': 'UNKNOWN', 'eol_date': None, 'days_to_eol': None, 'latest': None,
                    'lts': None}
        eol = r['lc'].get('eol_date') or None
        return {'branch': branch, 'status': r['status'], 'eol_date': eol, 'latest': r['latest'],
                'days_to_eol': (R.day_number(eol) - R.day_number(today)) if eol else None,
                'lts': bool(r['lc'].get('lts_start'))}
    good = [r for r in table if r['branch'].isdigit() and int(r['branch']) % 2 == 0 and r['status'] in A.LTS_NODE
            and (r['lc'].get('eol_date') or '') >= cut]
    rec = good[-1]['branch'] if good else None
    branches = [info(r['branch']) for r in table if r['branch'].isdigit() and int(r['branch']) % 2 == 0
                and (not current or not str(current).isdigit() or int(r['branch']) >= int(current))]
    cur_info = info(current) if current else None
    if cur_info is not None:
        cur_info['unpatched'] = exposure or None
    return {'today': today, 'bundle_id': bundle_id, 'current': cur_info,
            'target': info(target), 'recommended': rec, 'min_eol': cut,
            'recommended_eol': (rows[rec]['lc'].get('eol_date') or None) if rec in rows else None,
            'branches': branches,
            'target_ok': bool(rows.get(target)) and rows[target]['status'] in A.LTS_NODE
            and (rows[target]['lc'].get('eol_date') or '') >= cut}


# --- one project ---------------------------------------------------------------------
def owner_of(d, projects):
    """Project a declaration belongs to: the CodeUri of a SAM function, else the deepest project holding the file."""
    if d.get('code_uri'):
        for p in sorted(projects, key=len, reverse=True):
            if d['code_uri'] == p or d['code_uri'].startswith(p.rstrip('/') + '/'):
                return p
    for p in sorted(projects, key=len, reverse=True):
        if d['path'].startswith(p.rstrip('/') + '/'):
            return p
    return None


def scan_project(ctx, root, target, current_opt, node_bin, projects, decl, shared):
    """ctx: state_dir, feeds_dir, fs (FeedsDir), offline, lang, bc, budget, work, plan_dir."""
    lang = ctx['lang']
    pj, direct = direct_deps(root)
    res = {'path': root, 'name': pj.get('name') or os.path.basename(root), 'version': pj.get('version'),
           'lockfile': None, 'packages': 0, 'current_branch': None, 'current_source': None,
           'target_branch': target, 'target_patch': ctx['target_patch'], 'declarations': [], 'engines': None,
           'npm_engine_violations': [], 'npm_unknown': [], 'hits': [], 'rules_applied': [], 'skipped_files': [],
           'native_addons': [], 'vulnerabilities': None, 'vuln_meta': None, 'deprecated': [],
           'deprecated_unknown': [], 'parts': {}, 'errors': [], 'notes': []}
    res['declarations'] = decl
    test = str((pj.get('scripts') or {}).get('test') or '')
    res['has_tests'] = bool(test) and 'no test specified' not in test
    res['deploy'] = deploy_info(root, [p for p in projects if p != root and p.startswith(root.rstrip('/') + '/')])
    eng = (pj.get('engines') or {}).get('node') if isinstance(pj.get('engines'), dict) else None
    res['engines'] = eng
    # current branch: --current, else the most common declaration, else engines lower bound.
    cur = current_opt
    if cur:
        res['current_source'] = 'option'
    else:
        counts = {}
        for d in decl or shared:
            counts[d['branch']] = counts.get(d['branch'], 0) + 1
        if counts:
            cur = sorted(counts.items(), key=lambda kv: (-kv[1], -int(kv[0])))[0][0]
            res['current_source'] = 'declarations' if decl else 'repository'
        elif eng:
            m = re.search(r'(\d+)', eng)
            if m:
                cur, res['current_source'] = m.group(1), 'engines'
    res['current_branch'] = cur
    if not cur:
        note(res, 'current_unknown')
    # engines of the dependencies (FR-CMPT-NPM-001)
    viol, unknown, warns = deps.npm_engines(root, ctx['target_patch'], ctx['feeds_dir'], ctx['offline'])
    res['npm_engine_violations'], res['npm_unknown'] = viol, unknown
    for w in warns:
        note(res, 'yarn_pnpm' if 'yarn' in w else 'other', w)
    res['parts']['npm_engines'] = 'done'
    # breaking-change rules of (current, target] in the code of the project
    files, skipped, _ = S.list_files(root, S.JS_EXT, [os.path.relpath(p, root) for p in projects
                                                      if p != root and p.startswith(root.rstrip('/') + '/')],
                                     ctx['budget'])
    res['skipped_files'] = skipped
    res['files_scanned'] = len(files)
    if cur:
        rules = S.select_rules(ctx['bc'], 'node', cur, target)
        res['rules_applied'] = sorted(r['rule_id'] for r in rules)
        sf = S.scan_files(res['name'], root, files, rules, budget=ctx['budget'], loaders=False)
        res['hits'] = sf['hits']
        res['parts']['code_scan'] = 'done' if sf['complete'] else 'timeout'
        res['rules'] = [{'rule_id': r['rule_id'], 'version': r['version'], 'level': r['level'],
                         'change': r['change'], 'replacement': r.get('replacement')} for r in rules]
    else:
        res['parts']['code_scan'] = 'pending'
    # native addons, loaded with the target Node.js on a copy
    addons = deps.find_addons(root)
    if addons and node_bin:
        loaded, log = deps.addon_load(root, os.path.join(ctx['work'], re.sub(r'[^\w.-]', '_', res['name'])),
                                      node_bin, None, ctx['plan_dir'], re.sub(r'[^\w.-]', '_', res['name']))
        for a in loaded:
            if not a['load_ok']:
                res['errors'].append({'code': 'ERR-SCN-424-02', 'message': errors.message(
                    'ERR-SCN-424-02', package=a['package'], target=target)})
        res['native_addons'], res['npm_log'] = loaded, log
        res['parts']['native_addons'] = 'done'
    else:
        res['native_addons'] = [{'package': a, 'load_ok': None} for a in addons]
        if addons:
            res['parts']['native_addons'] = 'pending'
            note(res, 'addons_not_loaded', target=target)
    # known vulnerabilities of the locked packages (OSV) and deprecated direct dependencies
    lockname, pkgs = lock_packages(root)
    res['lockfile'] = lockname
    res['packages'] = len(pkgs)
    if lockname is None:
        note(res, 'no_lockfile')
        res['parts']['vulnerabilities'] = 'pending'
    else:
        vul, meta = vulnerabilities(ctx['fs'], os.path.join(root, lockname), pkgs, ctx['offline'])
        par = lock_parents(root)
        for v in vul or []:
            v['direct'] = v['package'] in direct or v['package'] in par.get('__direct__', ())
            v['via'] = [] if v['direct'] else sorted(par.get(v['package'], ()))
        res['vulnerabilities'], res['vuln_meta'] = vul, meta
        if vul is None:
            res['parts']['vulnerabilities'] = 'pending'
            res['errors'].append({'code': 'ERR-FEED-503-02', 'message': errors.message(
                'ERR-FEED-503-02', lockfile=os.path.join(root, lockname)) + ' (%s)' % meta.get('error')})
        else:
            res['parts']['vulnerabilities'] = 'done'
    res['deprecated'], res['deprecated_unknown'] = deprecated(root, pkgs, ctx['feeds_dir'], ctx['offline'], lang,
                                                              files)
    res.update(code_facts(root, files))
    for d in res['deprecated']:
        if d['package'] == 'aws-sdk':
            d['services'] = res['sdk_v2_services']
            d['promise_calls'] = res['sdk_v2_promise_calls']
    if lockname and res['vulnerabilities']:
        res['fix_trial'] = fix_trial(ctx['work'], root, lockname, ctx['fs'], ctx['offline'])
    if [u for u in unknown + res['deprecated_unknown'] if 'offline' in u.get('reason', '')
            or 'HTTP' in u.get('reason', '') or 'registry' in u.get('reason', '')]:
        res['errors'].append({'code': 'ERR-FEED-503-01', 'message': errors.message(
            'ERR-FEED-503-01', source='npm registry', origin='-', age_h='-')})
    res['verdict'] = verdict(res)
    res['work_items'] = work_items(res)
    return res


NOTES = {
    'current_unknown': 'Current Node.js branch unknown: give --current N.',
    'addons_not_loaded': 'Native addons not loaded: give --node-bin of a Node.js {target} binary.',
    'no_lockfile': 'No package-lock.json: vulnerabilities and engines of dependencies not checked.',
    'yarn_pnpm': 'yarn.lock/pnpm-lock.yaml only: check engines and advisories with yarn/pnpm.',
}


def note(res, key, text=None, **kw):
    msg = text or NOTES[key]
    for k, v in kw.items():
        msg = msg.replace('{%s}' % k, str(v))
    res['notes'].append({'key': key, 'args': kw, 'text': msg})


def verdict(res):
    """FAIL: something must change before the target runs the code; PENDING: a part could not run."""
    errs = sum(1 for h in res['hits'] if h['level'] == 'error')
    warns = sum(1 for h in res['hits'] if h['level'] == 'warning')
    blockers = [v for v in res['npm_engine_violations'] if v.get('severity') == 'error']
    blockers += [a for a in res['native_addons'] if a.get('load_ok') is False]
    vul = res['vulnerabilities'] or []
    sev = {}
    for v in vul:
        sev[v['severity']] = sev.get(v['severity'], 0) + 1
    pending = sorted(k for k, v in res['parts'].items() if v in ('pending', 'timeout'))
    status = 'FAIL' if errs or blockers else ('PENDING' if pending else 'PASS')
    return {'status': status, 'errors': errs, 'warnings': warns, 'blockers': len(blockers),
            'vulnerable_packages': len(vul), 'by_severity': sev,
            'malware': sum(1 for v in vul if v.get('is_malware')), 'deprecated': len(res['deprecated']),
            'runtime_changes': sum(1 for d in res['declarations'] if d['to_change']), 'pending_parts': pending}


def work_items(res):
    """What has to be done, one line per kind, with a size hint (no estimate of days)."""
    out = []
    n = sum(1 for d in res['declarations'] if d['to_change'])
    if n:
        out.append({'kind': 'runtime_declarations', 'count': n, 'size': 'S'})
    if res['engines'] and semver.satisfies(res['target_patch'], res['engines'], npm=True) is False:
        out.append({'kind': 'engines_field', 'count': 1, 'size': 'S'})
    vul = [v for v in res['vulnerabilities'] or [] if not v['dev']]
    minor = [v for v in vul if v['fix_version'] and not v['major_bump']]
    major = [v for v in vul if v['fix_version'] and v['major_bump']]
    nofix = [v for v in vul if not v['fix_version']]
    if minor:
        out.append({'kind': 'vuln_minor_upgrades', 'count': len(minor), 'size': 'S'})
    if major:
        out.append({'kind': 'vuln_major_upgrades', 'count': len(major), 'size': 'M'})
    if nofix:
        out.append({'kind': 'vuln_no_fix', 'count': len(nofix), 'size': 'M'})
    devv = [v for v in res['vulnerabilities'] or [] if v['dev']]
    if devv:
        out.append({'kind': 'vuln_dev_only', 'count': len(devv), 'size': 'S'})
    eng = [v for v in res['npm_engine_violations'] if v.get('severity') == 'error']
    if eng:
        out.append({'kind': 'engines_violations', 'count': len(eng), 'size': 'M'})
    for d in res['deprecated']:
        sites = len(d.get('call_sites') or [])
        out.append({'kind': 'migrate_package', 'package': d['package'], 'count': max(1, sites),
                    'size': 'L' if d['source'] == 'catalog' and sites > 10 else ('M' if sites or d['source'] == 'catalog'
                                                                              else 'S')})
    errs = [h for h in res['hits'] if h['level'] == 'error']
    if errs:
        out.append({'kind': 'code_errors', 'count': len(errs), 'size': 'M' if len(errs) > 5 else 'S'})
    warns = [h for h in res['hits'] if h['level'] == 'warning']
    if warns:
        out.append({'kind': 'code_warnings', 'count': len(warns), 'size': 'S'})
    add = [a for a in res['native_addons']]
    if add:
        out.append({'kind': 'native_addons', 'count': len(add), 'size': 'M'})
    out.append({'kind': 'regression_test', 'count': 1, 'size': 'M' if res['hits'] or add else 'S'})
    return out


def target_patch(fs, target):
    """Latest known release of the target branch (bundle), else TARGET.0.0."""
    from ..feeds.query import Bundle
    from ..feeds import versions as V
    try:
        with Bundle(fs) as b:
            mp = b.min_patched('node', target) or {}
            latest = mp.get('latest') or V.vmax(r['version'] for r in b.releases('node', target))
            if not latest:
                lc = b.lifecycle('node', target) or {}
                latest = lc.get('latest_hint')
            if latest:
                return latest, 'bundle'
    except LookupError:
        pass
    return '%s.0.0' % target, 'assumed'


def ensure_bundle(fs, offline):
    """Lifecycle data comes from the feeds bundle: update it (110 s budget, like scan) when there is none."""
    import subprocess
    import sys
    from ..feeds.query import Bundle
    try:
        with Bundle(fs):
            return None
    except LookupError:
        pass
    if offline:
        return 'no feeds bundle (offline): lifecycle not evaluated; run feeds update or feeds import'
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'qp-feeds.py')
    try:
        subprocess.run([sys.executable, '-I', script, 'feeds', 'update', '--quiet', '--budget', '110'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=130)
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        with Bundle(fs):
            return None
    except LookupError:
        return 'feeds update did not produce a bundle: lifecycle not evaluated'


def run(state_dir, paths, target, current=None, node_bin=None, offline=False, lang='en', today=None, budget_s=1800,
        warnings=None):
    """-> result dict of `compat --path` (qp.compat/1)."""
    from .. import catalog as qcatalog
    from ..feeds.store import FeedsDir
    fs = FeedsDir(state_dir)
    w = ensure_bundle(fs, offline)
    if w and warnings is not None:
        warnings.append(('ERR-FEED-503-01', w))
    cat = qcatalog.select(state_dir, [])
    if cat is None:
        raise errors.error('ERR-FEED-502-02', source='catalog', detail='no valid scenario catalog')
    today = today or time.strftime('%Y-%m-%d', time.gmtime())
    budget = S.Budget(budget_s)
    patch, patch_src = target_patch(fs, target)
    run_id = time.strftime('%Y%m%d-%H%M%S', time.gmtime()) + '-' + os.urandom(2).hex()
    work = os.path.join(state_dir, 'work', 'compat-' + run_id)
    out_dir = os.path.join(state_dir, 'reports', 'compat-' + run_id)
    ctx = {'state_dir': state_dir, 'feeds_dir': os.path.join(state_dir, 'feeds'), 'fs': fs, 'offline': offline,
           'lang': lang, 'bc': cat.bc_doc(), 'budget': budget, 'work': work, 'plan_dir': out_dir,
           'target_patch': patch}
    projects = find_projects(paths, budget)
    decls = []
    for root in paths:
        for d in declarations(os.path.realpath(root)):
            if not any(x['path'] == d['path'] and x['line'] == d['line'] and x['kind'] == d['kind'] for x in decls):
                decls.append(d)
    for d in decls:
        own = owner_of(d, projects)
        d['project'] = own
        d['to_change'] = d['branch'] != target
        base = next((os.path.realpath(r) for r in paths if d['path'].startswith(os.path.realpath(r).rstrip('/') + '/')),
                    os.path.dirname(d['path']))
        d['file'] = os.path.relpath(d['path'], base)
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    results = []
    for p in projects:
        mine = [d for d in decls if d['project'] == p]
        shared = [d for d in decls if d['project'] is None]
        results.append(scan_project(ctx, p, target, current, node_bin, projects, mine, shared))
    if os.path.isdir(work):
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    cur = current or next((r['current_branch'] for r in results if r['current_branch']), None)
    lc = lifecycle(fs, today, cur, target, (cat.meta.get('thresholds') or {}).get('target_eol_min_days', 365))
    summary = {'projects': len(results), 'by_status': {}, 'vulnerable_packages': 0, 'runtime_changes': 0,
               'deprecated': 0, 'errors': 0}
    for r in results:
        v = r['verdict']
        summary['by_status'][v['status']] = summary['by_status'].get(v['status'], 0) + 1
        summary['vulnerable_packages'] += v['vulnerable_packages']
        summary['runtime_changes'] += v['runtime_changes']
        summary['deprecated'] += v['deprecated']
        summary['errors'] += v['errors'] + v['blockers']
    shared = [d for d in decls if d['project'] is None]
    summary['runtime_changes'] += sum(1 for d in shared if d['to_change'])
    for d in decls:
        d.pop('path', None)
        if d.get('code_uri'):
            d['code_uri'] = os.path.relpath(d['code_uri'], next(
                (os.path.realpath(r) for r in paths if d['code_uri'].startswith(os.path.realpath(r))), '/'))
    return {'run_id': run_id, 'generated_at': iso_ms(), 'runtime': 'node', 'paths': [os.path.realpath(p) for p in paths],
            'shared_declarations': shared,
            'target_branch': target, 'target_patch': patch, 'target_patch_source': patch_src,
            'current_branch': cur, 'node_bin': node_bin, 'offline': offline, 'catalog_version': cat.version,
            'lifecycle': lc, 'summary': summary, 'projects': results, 'artifacts_dir': out_dir,
            'ignored_iac': ignored_iac(paths)}
