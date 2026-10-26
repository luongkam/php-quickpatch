"""Compatibility scan of one site (FR-CMPT-*) and its verdict (FR-CMPT-RES-001).

Result file: STATE_DIR/plans/<plan_id>/compat/<site_key>.json. A result is reused
while scan_fingerprint and the target do not change and no pending part can run
now (TC-CMPT-030); waivers are kept by hit_id across rescans.
"""
import json
import os
import re
import shutil
import time

from .. import errors
from ..envelope import iso_ms
from . import deps, ini, scan as S, tools as T

PARTS_BEFORE_INSTALL = ('code_scan',)
SITES_D = '/etc/php-quickpatch/sites.d'


def site_conf(site):
    """Directories declared "not deployed" (BR-CMPT-001): sites.d/<site_key>.conf,
    first line '# qp-site-id = <site_id>', keys exclude_dirs and exclude_reason (>= 20 chars)."""
    key = site.get('site_key') or site['site_id']
    dirs = [SITES_D] if os.geteuid() == 0 else \
        [os.path.join(os.environ.get('HOME', ''), '.config', 'php-quickpatch', 'sites.d')]
    for d in dirs:
        p = os.path.join(d, key + '.conf')
        try:
            with open(p, encoding='utf-8') as f:
                lines = f.read().split('\n')
        except OSError:
            continue
        if not lines or lines[0].strip() != '# qp-site-id = %s' % site['site_id']:
            return {'exclude_dirs': [], 'note': '%s ignored: first line is not "# qp-site-id = %s"' % (p, site['site_id'])}
        kv = {}
        for line in lines[1:]:
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                kv[k.strip()] = v.strip()
        ex = [x.strip() for x in kv.get('exclude_dirs', '').split(',') if x.strip()]
        reason = kv.get('exclude_reason', '')
        if ex and len(reason) < 20:
            return {'exclude_dirs': [], 'note': '%s: exclude_dirs ignored (exclude_reason < 20 characters)' % p}
        return {'exclude_dirs': ex, 'exclude_reason': reason or None, 'file': p}
    return {'exclude_dirs': []}


def result_path(plan_dir, site):
    return os.path.join(plan_dir, 'compat', '%s.json' % (site.get('site_key') or site['site_id']))


def load_result(plan_dir, site):
    try:
        with open(result_path(plan_dir, site), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_result(plan_dir, site, res):
    p = result_path(plan_dir, site)
    os.makedirs(os.path.dirname(p), mode=0o700, exist_ok=True)
    tmp = '%s.tmp-%d' % (p, os.getpid())
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def verdict(res):
    hits = res.get('hits') or []
    errs = sum(1 for h in hits if h['level'] == 'error' and not h.get('waived'))
    warns = sum(1 for h in hits if h['level'] == 'warning')
    waived = sum(1 for h in hits if h.get('waived'))
    blockers = [b for b in res.get('composer_blockers') or [] if not b.get('dev')]
    blockers += [v for v in res.get('npm_engine_violations') or [] if v.get('severity') == 'error']
    blockers += [a for a in res.get('native_addons') or [] if a.get('load_ok') is False]
    pending = sorted(k for k, v in (res.get('parts') or {}).items() if v in ('pending', 'timeout'))
    status = 'FAIL' if errs or blockers else ('PENDING' if pending else 'PASS')
    return {'site_id': res['site_id'], 'status': status, 'errors': errs, 'warnings': warns, 'waived': waived,
            'blockers': len(blockers), 'pending_parts': pending}


def new_bin_for(scan_doc, kind, branch):
    best = None
    for rt in (scan_doc or {}).get('result', {}).get('runtimes') or []:
        if rt.get('kind') == kind and rt.get('branch') == branch and not rt.get('locked'):
            if best is None or rt['bin'].startswith('/usr/bin/'):
                best = rt['bin']
    return best


def php_candidates(scan_doc):
    out = [rt['bin'] for rt in (scan_doc or {}).get('result', {}).get('runtimes') or []
           if rt.get('kind') == 'php' and rt.get('version') and not rt.get('locked')]
    w = shutil.which('php')
    if w and os.path.realpath(w) not in out:
        out.append(os.path.realpath(w))
    return out


def _err(res, code, msg):
    res['errors'].append({'code': code, 'message': msg})


def _add_hits(res, raw, source):
    for h in raw:
        snip = (h.get('snippet') or '')[:S.SNIPPET]
        res['hits'].append({'hit_id': S.hit_id(res['site_id'], h['file'], h['line'], h['rule_id'], snip),
                            'site_id': res['site_id'], 'file': h['file'], 'line': h['line'], 'rule_id': h['rule_id'],
                            'level': h['level'], 'snippet': snip, 'source': source, 'waived': False, 'waiver': None})


def run_site(ctx, site, rt, target, plan_id, plan_dir, scan_doc, previous=None):
    """ctx: state_dir, catalog (qplib.catalog.Catalog), offline, feeds_dir, allow (URL schemes)."""
    ctx = dict(ctx, plan_id=plan_id)
    cat = ctx['catalog']
    bc = cat.bc_doc()
    budget = S.Budget(ctx.get('budget_s', 1800))
    kind = rt['kind']
    old, new, patch = rt.get('branch') or '', target['branch'], target['patch_version']
    root = site.get('docroot') or ''
    conf = site_conf(site)
    new_bin = new_bin_for(scan_doc, kind, new)
    res = {'site_id': site['site_id'], 'site_key': site.get('site_key'), 'runtime_id': rt['runtime_id'],
           'old_branch': old, 'target_branch': new, 'target_patch': patch, 'new_bin': new_bin,
           'scan_fingerprint': (scan_doc or {}).get('result', {}).get('scan_fingerprint'),
           'catalog_version': cat.version, 'started_at': iso_ms(), 'finished_at': None, 'docroot': root,
           'excluded_dirs': conf.get('exclude_dirs'), 'exclude_reason': conf.get('exclude_reason'),
           'parts': {}, 'hits': [], 'skipped_files': [], 'composer_blockers': [], 'npm_engine_violations': [],
           'npm_unknown': [], 'native_addons': [], 'ini_findings': [], 'extension_gaps': [], 'frameworks': [],
           'loaders': [], 'tools': [], 'ladder': {}, 'facts': {}, 'errors': [], 'notes': []}
    if conf.get('note'):
        res['notes'].append(conf['note'])
    if not root or not os.path.isdir(root):
        res['parts']['code_scan'] = 'pending'
        res['notes'].append('docroot %r not readable' % root)
        return finish(res, previous)
    exts = S.PHP_EXT if kind == 'php' else S.JS_EXT
    files, skipped, trunc = S.list_files(root, exts, conf.get('exclude_dirs') or (), budget)
    res['skipped_files'] = skipped
    res['files_scanned'] = len(files)
    if skipped:
        _err(res, 'ERR-CMPT-413-01', errors.message('ERR-CMPT-413-01', count=len(skipped)))
    rules = S.select_rules(bc, kind, old, new)
    res['rules_applied'] = sorted(r['rule_id'] for r in rules)
    usage = S.usage_patterns([e for e in rt.get('extensions') or [] if e not in bc.get('builtin_ext', [])], bc) \
        if kind == 'php' else {}
    sf = S.scan_files(site['site_id'], root, files, rules, usage, budget, loaders=(kind == 'php'))
    res['hits'].extend(sf['hits'])
    res['parts']['code_scan'] = 'done' if sf['complete'] and not trunc else 'timeout'
    if res['parts']['code_scan'] == 'timeout':
        _err(res, 'ERR-CMPT-504-01', errors.message('ERR-CMPT-504-01', site=site['site_id']))
    if kind == 'php':
        php_parts(ctx, res, site, rt, files, root, bc, cat, new_bin, scan_doc, budget, sf)
    else:
        node_parts(ctx, res, site, rt, root, cat, new_bin, plan_dir, budget)
    return finish(res, previous)


def php_parts(ctx, res, site, rt, files, root, bc, cat, new_bin, scan_doc, budget, sf):
    old, new, patch = res['old_branch'], res['target_branch'], res['target_patch']
    par = os.cpu_count() or 1
    # PHPCompatibility (FR-CMPT-CODE-002, BR-CMPT-002)
    try:
        if not T.installed(ctx['state_dir'], 'phpcs'):
            T.install(ctx['state_dir'], cat.meta, 'phpcs', ctx.get('offline'), ctx.get('allow', ('https',)))
        tools_ok = True
    except T.ToolError as e:
        tools_ok = False
        _err(res, e.code, e.message if e.code != 'ERR-CMPT-424-01' else
             errors.message('ERR-CMPT-424-01', tool='PHPCompatibility') + ' (%s)' % e.message)
        res['parts']['phpcompat'] = 'pending'
    res['tools'] = T.load_manifest(ctx['state_dir'])['tools']
    if tools_ok:
        php = T.pick_phpcs_php(new_bin, php_candidates(scan_doc))
        if not php:
            res['parts']['phpcompat'] = 'pending'
            _err(res, 'ERR-CMPT-422-01', errors.message('ERR-CMPT-422-01', target=new))
        elif files:
            wp = any(f['name'] == 'wordpress' for f in res['frameworks']) or os.path.isfile(
                os.path.join(root, 'wp-includes', 'version.php'))
            try:
                raw, cmd = T.phpcs(ctx['state_dir'], php, root, files, new, wp, par, max(60, int(budget.left())))
                _add_hits(res, raw, 'phpcompatibility')
                res['phpcs'] = {'php': php, 'standard': 'PHPCompatibilityWP' if wp else 'PHPCompatibility',
                                'test_version': new, 'parallel': par}
                res['parts']['phpcompat'] = 'done'
                if S.vkey(old) < (7, 0):               # ladder, for grouping only (BR-SCN-042)
                    for tv in ('5.6', '7.4'):
                        lr, _ = T.phpcs(ctx['state_dir'], php, root, files, tv, wp, par, max(60, int(budget.left())))
                        res['ladder'][tv] = {'errors': sum(1 for h in lr if h['level'] == 'error'),
                                             'warnings': sum(1 for h in lr if h['level'] == 'warning')}
            except T.ToolError as e:
                res['parts']['phpcompat'] = 'timeout' if e.code == 'ERR-CMPT-504-01' else 'pending'
                _err(res, e.code, e.message)
        else:
            res['parts']['phpcompat'] = 'done'
    # lint with $NEW_BIN (FR-CMPT-CODE-003)
    if new_bin:
        errs, checked = T.lint(new_bin, root, files, par, max(60, int(budget.left())))
        res['lint'] = {'bin': new_bin, 'checked': checked, 'files': len(files), 'parse_errors': errs}
        _add_hits(res, [{'file': e['file'], 'line': e['line'], 'rule_id': 'php-l', 'level': 'error',
                         'snippet': e['message']} for e in errs], 'php-l')
        res['parts']['lint_new_bin'] = 'done'
    else:
        res['parts']['lint_new_bin'] = 'pending'
        _err(res, 'ERR-ENV-412-01', errors.message('ERR-ENV-412-01', runtime='PHP', target=new))
    # Composer (FR-CMPT-COMP-001/002)
    blockers, ext_req, has_composer = deps.composer_blockers(root, patch)
    res['facts']['composer'] = has_composer
    for b in blockers:
        if not b.get('dev') and b['package'] and '/' in b['package']:
            mc, err = deps.min_compatible(b['package'], b['version'], patch, ctx['feeds_dir'], ctx.get('offline'))
            b['min_compatible_version'] = mc
            if err:
                _err(res, 'ERR-FEED-503-01', errors.message('ERR-FEED-503-01', source='Packagist', origin='-',
                                                            age_h='-') + ' (%s)' % err)
        else:
            b['min_compatible_version'] = None
    res['composer_blockers'] = blockers
    if has_composer and os.path.isfile(os.path.join(root, 'composer.lock')):
        phar = T.composer_phar(ctx['state_dir'], cat.meta)
        if new_bin and phar:
            pc = deps.platform_check(root, os.path.join(ctx['state_dir'], 'work', ctx['plan_id'], res['site_key'] or
                                                        res['site_id'], 'composer'), new_bin, phar, patch)
            res['composer_platform'] = {'exit_code': pc['exit_code'], 'output': pc['output']}
            known = {b['package'] for b in blockers}
            for b in pc['blockers']:
                if b['package'] not in known:
                    b['min_compatible_version'] = None
                    blockers.append(b)
            if pc['exit_code'] != 0 and not [b for b in blockers if not b.get('dev')]:
                blockers.append({'package': '(platform)', 'version': '-', 'constraint': 'check-platform-reqs exit %d'
                                 % pc['exit_code'], 'reason': 'check-platform-reqs', 'dev': False,
                                 'min_compatible_version': None})
            res['parts']['composer_platform'] = 'done'
        else:
            res['parts']['composer_platform'] = 'pending'
            if not phar:
                _err(res, 'ERR-CMPT-424-01', errors.message('ERR-CMPT-424-01', tool='composer'))
    # ini (FR-CMPT-INI-001), extensions (FR-CMPT-EXT-001)
    res['ini_findings'] = ini.findings(bc, old, new, site, rt, budget)
    res['extension_gaps'] = extension_gaps(rt, new, new_bin, bc, sf['usage'], ext_req)
    # frameworks (FR-CMPT-FWK-001), loaders (FR-CMPT-LDR-001)
    res['frameworks'] = S.frameworks(root, cat.framework_rows(), bc, new)
    res['loaders'] = S.loaders_result(sf['loader_files'], sf['loader_unread'], cat.meta.get('loaders'), new,
                                      rt.get('extensions') or [])
    for ld in res['loaders']:
        if ld['files_unread']:
            res['notes'].append('loader scan: %d file(s) not read (limit %d)' % (ld['files_unread'], S.MAX_LOADER_FILES))
        if not ld['target_supported']:
            _err(res, 'ERR-SCN-409-03', errors.message('ERR-SCN-409-03', loader=ld['name'], target=new,
                                                       vhost=res['site_id']))
    res['facts'].update({'framework': (res['frameworks'][0]['name'] if res['frameworks'] else 'none'),
                         'loader': (res['loaders'][0]['name'].lower() if res['loaders'] else 'none')})


def node_parts(ctx, res, site, rt, root, cat, new_bin, plan_dir, budget):
    patch = res['target_patch']
    viol, unknown, warns = deps.npm_engines(root, patch, ctx['feeds_dir'], ctx.get('offline'))
    res['npm_engine_violations'], res['npm_unknown'] = viol, unknown
    res['parts']['npm_engines'] = 'done'
    res['notes'].extend(warns)
    if unknown and any('offline' in (u.get('reason') or '') or 'HTTP' in (u.get('reason') or '') for u in unknown):
        _err(res, 'ERR-FEED-503-01', errors.message('ERR-FEED-503-01', source='npm registry', origin='-', age_h='-'))
    addons = deps.find_addons(root)
    abi = (cat.meta.get('node') or {}).get('node_module_version') or {}
    abi_old, abi_new = rt.get('abi') or abi.get(res['old_branch']), abi.get(res['target_branch'])
    if addons and new_bin:
        loaded, log = deps.addon_load(root, os.path.join(ctx['state_dir'], 'work', ctx['plan_id'],
                                                         res['site_key'] or res['site_id'], 'app'),
                                      new_bin, site.get('owner_user'), plan_dir, res['site_key'] or res['site_id'])
        res['npm_log'] = log
        for a in loaded:
            a.update(abi_old=abi_old, abi_new=abi_new)
            if not a['load_ok']:
                _err(res, 'ERR-SCN-424-02', errors.message('ERR-SCN-424-02', package=a['package'], target=res['target_branch']))
        res['native_addons'] = loaded
        res['parts']['native_addons'] = 'done'
    else:
        res['native_addons'] = [{'package': a, 'abi_old': abi_old, 'abi_new': abi_new, 'load_ok': None} for a in addons]
        if addons:
            res['parts']['native_addons'] = 'pending'
            _err(res, 'ERR-ENV-412-01', errors.message('ERR-ENV-412-01', runtime='Node.js', target=res['target_branch']))
    res['facts'].update({'framework': 'none', 'loader': 'none', 'composer': False})


def extension_gaps(rt, new, new_bin, bc, usage, ext_req):
    """BR-SCN-045 (a) available, (b) pecl, (c) replaced; else missing. Builtin extensions are left out."""
    old_exts = [e for e in (rt.get('extensions') or []) if e and e not in bc.get('builtin_ext', [])]
    if S.vkey(new) >= (8, 5):
        old_exts = [e for e in old_exts if e != 'zend opcache']
    new_exts = None
    if new_bin:
        try:
            import subprocess
            p = subprocess.run([new_bin, '-m'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
            new_exts = {l.strip().lower() for l in p.stdout.decode().splitlines() if l and not l.startswith('[')}
        except OSError:
            new_exts = None
    removed = {e['extension']: e for e in bc.get('ext_removed', []) if S.in_range(e['removed_in'], '0', new)}
    pk = bc.get('ext_packages') or {}
    out = []
    for ext in sorted(set(old_exts)):
        hits = usage.get(ext)
        pkg = 'php%s-%s' % (new, pk.get(ext, ext.replace(' ', '-')))
        if new_exts is not None and ext in new_exts:
            res = 'available'
        elif ext in removed:
            res = 'replaced' if (hits == 0 and removed[ext]['replacement']) else \
                ('pecl' if _apt_has(pkg) else 'missing')
        else:
            got = _apt_has(pkg)
            res = 'available' if got else ('missing' if got is False else 'unknown')
        out.append({'extension': ext, 'package_new': pkg, 'resolution': res, 'usage_hits': hits,
                    'replacement': (removed.get(ext) or {}).get('replacement'),
                    'required_by_composer': ext in ext_req})
    return out


def _apt_has(pkg):
    """apt-cache policy PKG: True (candidate), False (none), None (no apt)."""
    import subprocess
    try:
        p = subprocess.run(['apt-cache', 'policy', pkg], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r'Candidate:\s*(\S+)', p.stdout.decode('utf-8', 'replace'))
    if p.returncode != 0:
        return None
    return bool(m and m.group(1) != '(none)')


def finish(res, previous):
    if previous:
        old = {h['hit_id']: h for h in previous.get('hits') or [] if h.get('waived')}
        for h in res['hits']:
            if h['hit_id'] in old:
                h['waived'], h['waiver'] = True, old[h['hit_id']].get('waiver')
    res['finished_at'] = iso_ms()
    res['verdict'] = verdict(res)
    return res


def reusable(prev, scan_doc, target, kind, state_dir=None, offline=True):
    """TC-CMPT-030 KQ3: same fingerprint, same target, nothing pending that could run now."""
    if not prev or prev.get('scan_fingerprint') != (scan_doc or {}).get('result', {}).get('scan_fingerprint'):
        return False
    if prev.get('target_branch') != target['branch'] or prev.get('target_patch') != target['patch_version']:
        return False
    pend = prev.get('verdict', {}).get('pending_parts') or []
    if ('lint_new_bin' in pend or 'native_addons' in pend or 'composer_platform' in pend) and \
            new_bin_for(scan_doc, kind, target['branch']):
        return False
    if 'phpcompat' in pend and (not offline or (state_dir and T.installed(state_dir, 'phpcs'))):
        return False
    return 'code_scan' not in pend


def waive(res, hit_ids, reason, actor):
    """Mark error hits as waived (FR-CMPT-RES-001). -> (waived, already, bad)."""
    by = {h['hit_id']: h for h in res.get('hits') or []}
    bad = [h for h in hit_ids if h not in by or by[h]['level'] != 'error']
    if bad:
        return [], [], bad
    done, already = [], []
    for h in hit_ids:
        if by[h].get('waived'):
            already.append(h)
            continue
        by[h]['waived'] = True
        by[h]['waiver'] = {'reason': reason, 'by': actor, 'at': iso_ms()}
        done.append(h)
    res['verdict'] = verdict(res)
    return done, already, []


def upgrade_items(res):
    """FR-PLAN-DEP-001: what must be upgraded for the site (component_type, name, current, required, ...)."""
    out = []
    for b in res.get('composer_blockers') or []:
        if not b.get('dev'):
            out.append({'component_type': 'composer', 'name': b['package'], 'current': b['version'],
                        'required': 'php %s does not satisfy %s' % (res['target_patch'], b['constraint']),
                        'min_compatible': b.get('min_compatible_version'), 'evidence': 'composer.lock require.php'})
    for v in res.get('npm_engine_violations') or []:
        out.append({'component_type': 'npm', 'name': v['package'], 'current': v.get('version'),
                    'required': 'engines.node %s' % v['engines'], 'min_compatible': None,
                    'evidence': 'package-lock.json engines' + (' (devDependency)' if v.get('dev') else ''),
                    'warning_only': bool(v.get('dev'))})
    for a in res.get('native_addons') or []:
        if a.get('abi_old') != a.get('abi_new') or a.get('load_ok') is False:
            out.append({'component_type': 'native_addon', 'name': a['package'], 'current': 'ABI %s' % a.get('abi_old'),
                        'required': 'build for ABI %s' % a.get('abi_new'), 'min_compatible': None,
                        'evidence': 'binding.gyp / *.node'})
    for g in res.get('extension_gaps') or []:
        if g['resolution'] in ('missing', 'pecl', 'unknown', 'replaced'):
            out.append({'component_type': 'extension', 'name': g['extension'], 'current': 'loaded on %s' % res['old_branch'],
                        'required': g['package_new'] if g['resolution'] != 'replaced' else (g.get('replacement') or '-'),
                        'min_compatible': None, 'evidence': '%s, %s call(s) in the site' % (g['resolution'], g['usage_hits']),
                        'usage_hits': g['usage_hits'], 'resolution': g['resolution']})
    for f in res.get('frameworks') or []:
        if f['supports_target'] is not True:
            out.append({'component_type': 'framework', 'name': f['name'], 'current': f['version'],
                        'required': 'PHP %s within %s - %s' % (res['target_branch'], f['php_min'] or '?', f['php_max'] or '?'),
                        'min_compatible': None, 'evidence': 'framework_php.tsv',
                        'confirm_range': f['supports_target'] == 'unknown'})
    for ld in res.get('loaders') or []:
        out.append({'component_type': 'loader', 'name': ld['name'], 'current': '%d encoded file(s)' % ld['files_count'],
                    'required': 'loader for PHP %s, sample file runs with $NEW_BIN' % res['target_branch'],
                    'min_compatible': None, 'evidence': ld.get('sample') or 'runtime extension',
                    'target_supported': ld['target_supported']})
    return out


def hit_filter(hits, level=None, rule=None, waived=None):
    out = hits
    if level:
        out = [h for h in out if h['level'] == level]
    if rule:
        out = [h for h in out if h['rule_id'] == rule or re.match(re.escape(rule).replace(r'\*', '.*') + '$', h['rule_id'])]
    if waived is not None:
        out = [h for h in out if bool(h.get('waived')) == waived]
    return out


def rector_run(ctx, site, plan_dir, target, apply=False, php=None):
    """FR-CMPT-RCT-001: dry-run diff (or apply to the copy). Raises ToolError."""
    if not T.installed(ctx['state_dir'], 'rector'):
        T.install(ctx['state_dir'], ctx['catalog'].meta, 'rector', ctx.get('offline'), ctx.get('allow', ('https',)))
    key = site.get('site_key') or site['site_id']
    copy = os.path.join(ctx['state_dir'], 'work', ctx['plan_id'], key, 'rector-src')
    diff, n, cmd, errs = T.rector(ctx['state_dir'], php, site['docroot'], copy, target['branch'], apply=apply)
    out = os.path.join(plan_dir, 'rector-%s.diff' % key)
    if not apply:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(diff)
    return {'diff_file': out, 'files_changed': n, 'copy': copy, 'applied': apply, 'file_errors': errs,
            'started': time.time()}
