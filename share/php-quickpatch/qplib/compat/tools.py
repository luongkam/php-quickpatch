"""Scan tools (FR-CMPT-TOOL-001, BR-CMPT-006) and the runs that need a PHP binary:
PHPCompatibility (FR-CMPT-CODE-002), lint with $NEW_BIN (FR-CMPT-CODE-003),
Rector on a copy (FR-CMPT-RCT-001).

Tools live in STATE_DIR/tools/php (never in a docroot). Versions and hashes come
only from the catalog: a package is accepted when the SHA-256 of its dist zip
(`dist_sha256`) or of `git archive` of the pinned commit (`archive_sha256`)
matches; composer.phar must match the published SHA-256. tools_manifest.json
records name, version, SHA-256 and source of every installed tool.
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile

from .. import errors

GROUPS = {'phpcs': ('squizlabs/php_codesniffer', 'phpcsstandards/phpcsutils', 'phpcompatibility/php-compatibility',
                    'phpcompatibility/phpcompatibility-paragonie', 'phpcompatibility/phpcompatibility-wp'),
          'rector': ('rector/rector', 'phpstan/phpstan')}


class ToolError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def tools_dir(state_dir):
    return os.path.join(state_dir, 'tools', 'php')


def manifest_path(state_dir):
    return os.path.join(tools_dir(state_dir), 'tools_manifest.json')


def load_manifest(state_dir):
    try:
        with open(manifest_path(state_dir)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {'tools': []}


def save_manifest(state_dir, man):
    p = manifest_path(state_dir)
    tmp = p + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(man, f, indent=1, sort_keys=True)
    os.replace(tmp, p)


def pkg_dir(state_dir, name):
    return os.path.join(tools_dir(state_dir), name.replace('/', '__'))


def _scheme_ok(url, allow):
    return url.split(':', 1)[0] in allow


def _download(url, allow):
    if not _scheme_ok(url, allow):
        raise ToolError('ERR-CMPT-424-01', 'refused URL %s' % url)
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'php-quickpatch'}), timeout=120) as r:
        return r.read()


def _safe_members(names, dest):
    for n in names:
        if n.startswith('/') or '..' in n.split('/'):
            raise ToolError('ERR-PTCH-502-01', 'unsafe path %s in a tool archive' % n)


def _extract_tar(data, dest):
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        members = [m for m in t.getmembers() if m.name not in ('pax_global_header',)]
        _safe_members([m.name for m in members], dest)
        for m in members:
            if m.isdev() or m.isfifo():
                raise ToolError('ERR-PTCH-502-01', 'device entry %s in a tool archive' % m.name)
            if (m.issym() or m.islnk()) and (m.linkname.startswith('/') or '..' in m.linkname.split('/')):
                raise ToolError('ERR-PTCH-502-01', 'link %s leaves the tool directory' % m.name)
        t.extractall(dest, members=members)


def _extract_zip(data, dest):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        _safe_members(names, dest)
        top = os.path.commonprefix(names).split('/')[0] + '/' if names and '/' in names[0] else ''
        for n in names:
            rel = n[len(top):] if top and n.startswith(top) else n
            if not rel or n.endswith('/'):
                continue
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with z.open(n) as src, open(out, 'wb') as f:
                shutil.copyfileobj(src, f)


def _fetch_package(p, dest, allow):
    """-> (sha256, source). Raises ToolError (ERR-PTCH-502-01 on a hash mismatch)."""
    errs = []
    if p.get('dist_sha256') and p.get('dist_url'):
        try:
            data = _download(p['dist_url'], allow)
            sha = hashlib.sha256(data).hexdigest()
            if sha != p['dist_sha256']:
                raise ToolError('ERR-PTCH-502-01', errors.message('ERR-PTCH-502-01', file=p['name']))
            _extract_zip(data, dest)
            return sha, 'dist'
        except ToolError:
            raise
        except (OSError, ValueError, zipfile.BadZipFile) as e:
            errs.append('dist: %s' % e)
    if p.get('archive_sha256') and p.get('git_url'):
        if not _scheme_ok(p['git_url'], allow) or not shutil.which('git'):
            errs.append('git: not allowed or git missing')
        else:
            with tempfile.TemporaryDirectory() as g:
                env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
                try:
                    subprocess.run(['git', 'init', '-q', g], check=True, env=env, stdout=subprocess.DEVNULL)
                    subprocess.run(['git', '-C', g, 'fetch', '-q', '--depth', '1', p['git_url'], p['reference']],
                                   check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600)
                    data = subprocess.run(['git', '-C', g, 'archive', '--format=tar', p['reference']], check=True,
                                          stdout=subprocess.PIPE, timeout=600).stdout
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
                    errs.append('git: %s' % e)
                    data = None
                if data is not None:
                    sha = hashlib.sha256(data).hexdigest()
                    if sha != p['archive_sha256']:
                        raise ToolError('ERR-PTCH-502-01', errors.message('ERR-PTCH-502-01', file=p['name']))
                    _extract_tar(data, dest)
                    return sha, 'git'
    raise ToolError('ERR-CMPT-424-01', '%s %s: %s' % (p['name'], p['version'], '; '.join(errs) or 'no source'))


def install(state_dir, catalog_meta, group, offline=False, allow=('https',)):
    """Install the packages of GROUP (and composer.phar) when missing. -> tools list. Raises ToolError."""
    spec = catalog_meta.get('tools') or {}
    want = [p for p in spec.get('packages', []) if p['name'] in GROUPS.get(group, ())]
    if group == 'composer':
        want = []
    root = tools_dir(state_dir)
    os.makedirs(root, mode=0o755, exist_ok=True)
    man = load_manifest(state_dir)
    have = {t['name']: t for t in man['tools']}
    for p in want:
        t = have.get(p['name'])
        if t and t['version'] == p['version'] and os.path.isdir(pkg_dir(state_dir, p['name'])):
            continue
        if offline:
            raise ToolError('ERR-CMPT-424-01', errors.message('ERR-CMPT-424-01', tool=p['name']))
        tmp = tempfile.mkdtemp(prefix='.install-', dir=root)
        try:
            sha, src = _fetch_package(p, tmp, allow)
            dest = pkg_dir(state_dir, p['name'])
            if os.path.lexists(dest):
                shutil.rmtree(dest)
            os.rename(tmp, dest)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        have[p['name']] = {'name': p['name'], 'version': p['version'], 'sha256': sha, 'source': src}
    if group in ('composer', 'phpcs'):
        for c in spec.get('composer', []):
            path = os.path.join(root, '%s-%s.phar' % (c['name'], c['version']))
            t = have.get(c['name'])
            if t and t['version'] == c['version'] and os.path.isfile(path):
                continue
            if offline:
                if group == 'composer':
                    raise ToolError('ERR-CMPT-424-01', errors.message('ERR-CMPT-424-01', tool='composer'))
                continue
            try:
                data = _download(c['url'], allow)
            except (OSError, ValueError) as e:
                if group == 'composer':
                    raise ToolError('ERR-CMPT-424-01', '%s: %s' % (c['url'], e))
                continue
            if hashlib.sha256(data).hexdigest() != c['sha256']:
                raise ToolError('ERR-PTCH-502-01', errors.message('ERR-PTCH-502-01', file='composer.phar'))
            with open(path, 'wb') as f:
                f.write(data)
            have[c['name']] = {'name': c['name'], 'version': c['version'], 'sha256': c['sha256'], 'source': 'phar'}
    man['tools'] = sorted(have.values(), key=lambda t: t['name'])
    save_manifest(state_dir, man)
    return man['tools']


def installed(state_dir, group):
    have = {t['name'] for t in load_manifest(state_dir)['tools']}
    return all(n in have and os.path.isdir(pkg_dir(state_dir, n)) for n in GROUPS[group])


def composer_phar(state_dir, catalog_meta, lts=False):
    for c in (catalog_meta.get('tools') or {}).get('composer', []):
        if (c['name'] == 'composer-lts') == lts:
            p = os.path.join(tools_dir(state_dir), '%s-%s.phar' % (c['name'], c['version']))
            if os.path.isfile(p):
                return p
    return None


# --- PHP binaries --------------------------------------------------------------------
def php_version(binary):
    try:
        p = subprocess.run([binary, '-n', '-r', 'echo PHP_VERSION;'], stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=10)
        v = p.stdout.decode().strip()
        return v if re.match(r'^\d+\.\d+\.\d+', v) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def pick_phpcs_php(new_bin, candidates):
    """BR-CMPT-002: $NEW_BIN if installed, else the highest PHP >= 7.2 of the machine."""
    if new_bin:
        return new_bin
    best, bv = None, None
    for b in candidates:
        v = php_version(b)
        if v and tuple(int(x) for x in v.split('.')[:2]) >= (7, 2):
            key = tuple(int(x) for x in re.findall(r'\d+', v)[:3])
            if bv is None or key > bv:
                best, bv = b, key
    return best


# --- PHPCompatibility (FR-CMPT-CODE-002) ------------------------------------------------
def phpcs(state_dir, php_bin, root, files, test_version, wordpress, parallel, timeout):
    """-> (hits [{file, line, rule_id, level, snippet}], command argv). Raises ToolError."""
    base = pkg_dir(state_dir, 'squizlabs/php_codesniffer')
    paths = ','.join(pkg_dir(state_dir, n) for n in GROUPS['phpcs'][1:])
    with tempfile.NamedTemporaryFile('w', suffix='.lst', delete=False) as lst:
        lst.write('\n'.join(files) + '\n')
    cmd = [php_bin, '-d', 'memory_limit=1G', os.path.join(base, 'bin', 'phpcs'), '-q',
           '--standard=%s' % ('PHPCompatibilityWP' if wordpress else 'PHPCompatibility'),
           '--runtime-set', 'installed_paths', paths, '--runtime-set', 'testVersion', test_version,
           '--extensions=php,inc,phtml', '--report=json', '--parallel=%d' % max(1, parallel),
           '--file-list=%s' % lst.name]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.unlink(lst.name)
        raise ToolError('ERR-CMPT-504-01', 'PHPCompatibility timed out')
    os.unlink(lst.name)
    out = p.stdout.decode('utf-8', 'replace')
    try:
        doc = json.loads(out[out.index('{'):])
    except ValueError:
        raise ToolError('ERR-CMPT-424-01', 'PHP_CodeSniffer failed (exit %d): %s' % (
            p.returncode, (p.stderr.decode('utf-8', 'replace') or out)[-300:]))
    hits = []
    for path, info in (doc.get('files') or {}).items():
        rel = os.path.relpath(path, root)
        for m in info.get('messages') or []:
            hits.append({'file': rel, 'line': m.get('line'), 'rule_id': m.get('source'),
                         'level': 'error' if m.get('type') == 'ERROR' else 'warning',
                         'snippet': (m.get('message') or '')[:200]})
    return hits, cmd


# --- lint (FR-CMPT-CODE-003) ---------------------------------------------------------------
LINT_RE = re.compile(r'(?:PHP )?(Parse|Fatal) error:\s+(.*?) in (.+?) on line (\d+)')


def lint(new_bin, root, files, parallel, timeout):
    """php -l with $NEW_BIN; 200 files per process from PHP 8.3, else one. -> (errors, checked)."""
    v = php_version(new_bin) or '0'
    per = 200 if tuple(int(x) for x in re.findall(r'\d+', v)[:2]) >= (8, 3) else 1
    batches = [files[i:i + per] for i in range(0, len(files), per)]
    errs, ok = {}, 0
    import concurrent.futures as cf

    def one(batch):
        p = subprocess.run([new_bin, '-d', 'display_errors=1', '-d', 'log_errors=0', '-l'] + batch,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return p.stdout.decode('utf-8', 'replace')

    with cf.ThreadPoolExecutor(max_workers=max(1, parallel)) as ex:
        for out in ex.map(one, batches):
            ok += out.count('No syntax errors detected')
            for m in LINT_RE.finditer(out):
                path = m.group(3)
                key = (path, m.group(4))
                if key not in errs:
                    errs[key] = {'file': os.path.relpath(path, root), 'line': int(m.group(4)),
                                 'message': '%s error: %s' % (m.group(1), m.group(2))}
    return sorted(errs.values(), key=lambda e: (e['file'], e['line'])), ok


# --- Rector (FR-CMPT-RCT-001) --------------------------------------------------------------
def rector(state_dir, php_bin, src_root, copy_dir, target_branch, apply=False, timeout=1800):
    """Rector on a copy outside the docroot: --dry-run -> unified diff; APPLY writes the copy only."""
    if not apply:
        if os.path.lexists(copy_dir):
            shutil.rmtree(copy_dir)
        shutil.copytree(src_root, copy_dir, symlinks=True, ignore=shutil.ignore_patterns('.git', 'node_modules'))
    xy = target_branch.replace('.', '')
    cfg = os.path.join(os.path.dirname(copy_dir), 'rector.php')
    with open(cfg, 'w') as f:
        f.write("<?php\nuse Rector\\Config\\RectorConfig;\nreturn RectorConfig::configure()\n"
                "    ->withPaths([%s])\n    ->withSkip([%s])\n    ->withoutParallel()\n    ->withPhpSets(php%s: true);\n"
                % (json.dumps(copy_dir), json.dumps(os.path.join(copy_dir, 'vendor')), xy))
    # Rector is installed beside PHPStan, not under its vendor/: load the PHPStan phar autoloader first
    # (one process: workers of a parallel run would not get the -d option).
    cmd = [php_bin, '-d', 'memory_limit=2G', '-d', 'auto_prepend_file=' + os.path.join(
        pkg_dir(state_dir, 'phpstan/phpstan'), 'bootstrap.php'),
           os.path.join(pkg_dir(state_dir, 'rector/rector'), 'bin', 'rector'),
           'process', '--config', cfg, '--no-progress-bar', '--output-format=json'] + ([] if apply else ['--dry-run'])
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = p.stdout.decode('utf-8', 'replace')
    try:
        doc = json.loads(out[out.index('{'):])
    except ValueError:
        raise ToolError('ERR-CMPT-424-01', 'Rector failed (exit %d): %s' % (
            p.returncode, (p.stderr.decode('utf-8', 'replace') or out)[-300:]))
    # Files Rector cannot parse (already broken on the old branch, or not PHP) are listed, not fatal.
    errs = [{'file': os.path.relpath(e.get('file') or '', copy_dir), 'message': str(e.get('message', ''))[:300]}
            for e in doc.get('errors') or []]
    diff = ''.join(d.get('diff', '') for d in doc.get('file_diffs') or [])
    return diff, len(doc.get('file_diffs') or []), cmd, errs
