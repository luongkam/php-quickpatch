"""M4 unit tests: compatibility scan (FR-CMPT-*), its verdict and its use in the plan
(FR-CMPT-RES-001, FR-PLAN-GEN-002, FR-PLAN-DEP-001). No root, no network."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib import catalog as C, plan as PL  # noqa: E402
from qplib.compat import deps, engine as CE, ini, scan as S, semver, tools as T  # noqa: E402

PACKAGED = os.path.join(ROOT, 'share', 'php-quickpatch', 'catalog')


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


class SemverTest(unittest.TestCase):
    def test_composer_constraints(self):
        cases = [('8.5.12', '^7.2', False), ('7.4.33', '^7.2', True), ('8.5.12', '>=5.6 <8.0', False),
                 ('7.4.33', '>=5.6 <8.0', True), ('8.5.12', '^7.4 || ^8.0', True), ('8.5.12', '^7.4|^8.0', True),
                 ('8.5.12', '~7.1', False), ('7.4.33', '7.4.*', True), ('8.5.12', '>=7.1 <8.1', False),
                 ('8.5.12', '>=8.1', True), ('8.0.30', '^8.0.2', True), ('8.0.1', '^8.0.2', False)]
        for v, c, want in cases:
            self.assertIs(semver.satisfies(v, c), want, '%s %s' % (v, c))

    def test_npm_ranges(self):
        cases = [('24.11.0', '>=18', True), ('24.11.0', '<=20', False), ('24.11.0', '^18.0.0 || >=20', True),
                 ('24.11.0', '18.x || 20.x', False), ('24.11.0', '>= 14.17.0', True), ('22.1.0', '^22', True)]
        for v, c, want in cases:
            self.assertIs(semver.satisfies(v, c, npm=True), want, '%s %s' % (v, c))

    def test_not_understood(self):
        self.assertIsNone(semver.satisfies('8.5.12', 'banana'))


class CodeScanTest(unittest.TestCase):
    """FR-CMPT-CODE-001 (TC-CMPT-004, 006), FR-CMPT-LDR-001 (TC-CMPT-022, 024), FR-CMPT-FWK-001."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(PACKAGED, 'bc_rules.json'), encoding='utf-8') as f:
            cls.bc = json.load(f)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'legacy.test')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def scan(self, old, new, excluded=()):
        files, skipped, _ = S.list_files(self.root, S.PHP_EXT, excluded)
        rules = S.select_rules(self.bc, 'php', old, new)
        return S.scan_files('legacy.test', self.root, files, rules), skipped, rules

    def test_each_line_12_and_snippet(self):
        write(os.path.join(self.root, 'lib', 'a.php'),
              '<?php\n' + '\n' * 10 + 'while (list($k, $v) = each($arr)) { echo $k . str_repeat("x", 400); }\n')
        sf, _, _ = self.scan('7.4', '8.5')
        hit = [h for h in sf['hits'] if h['file'] == 'lib/a.php']
        self.assertEqual([(h['line'], h['rule_id'], h['level']) for h in hit], [(12, 'BC-PHP-80-02', 'error')])
        self.assertLessEqual(len(hit[0]['snippet']), 200)
        self.assertRegex(hit[0]['hit_id'], r'^H-[0-9a-f]{12}$')

    def test_fixture_56_74_82(self):
        """mysql_*, each(), create_function, ${} interpolation over three source branches."""
        write(os.path.join(self.root, 'db.php'), '<?php\n$c = mysql_connect("h");\n')
        write(os.path.join(self.root, 'fn.php'), '<?php\n$f = create_function(\'$a\', \'return $a;\');\n')
        write(os.path.join(self.root, 'tpl.php'), '<?php\necho "Hello ${name}";\n')
        got = {}
        for old in ('5.6', '7.4', '8.2'):
            sf, _, _ = self.scan(old, '8.5')
            got[old] = sorted((h['file'], h['rule_id'], h['level']) for h in sf['hits'])
        self.assertIn(('db.php', 'BC-PHP-70-01', 'error'), got['5.6'])
        self.assertIn(('fn.php', 'BC-PHP-80-02', 'error'), got['5.6'])
        self.assertIn(('tpl.php', 'BC-PHP-82-02', 'warning'), got['7.4'])
        self.assertNotIn('BC-PHP-70-01', [r for _, r, _ in got['7.4']])          # 7.0 not in (7.4, 8.5]
        self.assertEqual([r for _, r, _ in got['8.2']], [])                    # all three removed before 8.2

    def test_file_set_and_range_bounds(self):
        """TC-CMPT-006: > 2 MiB skipped, vendor/node_modules/.git and declared dirs left out, (old, new]."""
        write(os.path.join(self.root, 'big.php'), '<?php\n' + 'x' * (2 * 1024 * 1024 + 1 - 6))
        self.assertEqual(os.path.getsize(os.path.join(self.root, 'big.php')), 2097153)
        for d in ('vendor', 'node_modules', '.git', 'tests'):
            write(os.path.join(self.root, d, 'x.php'), '<?php\n$c = mysql_connect("h");\n$a = each($b);\n')
        sf, skipped, rules = self.scan('7.4', '8.5', excluded=('tests',))
        self.assertEqual([s['file'] for s in skipped], ['big.php'])
        self.assertEqual(sf['hits'], [])
        ids = [r['rule_id'] for r in rules]
        self.assertFalse([i for i in ids if i.startswith('BC-PHP-74')])
        self.assertIn('BC-PHP-85-01', ids)

    def test_site_conf_exclusion(self):
        """BR-CMPT-001: sites.d/<site_key>.conf, first line names the site, reason >= 20 characters."""
        d = os.path.join(self.tmp, 'sites.d')
        old_d, old_home = CE.SITES_D, os.environ.get('HOME')
        CE.SITES_D = d
        os.environ['HOME'] = self.tmp
        try:
            for base in (d, os.path.join(self.tmp, '.config', 'php-quickpatch', 'sites.d')):
                write(os.path.join(base, 'legacy.test.conf'),
                      '# qp-site-id = legacy.test\nexclude_dirs = tests, docs\nexclude_reason = not deployed to prod\n')
            conf = CE.site_conf({'site_id': 'legacy.test', 'site_key': 'legacy.test'})
            self.assertEqual((conf['exclude_dirs'], conf['exclude_reason']), (['tests', 'docs'], 'not deployed to prod'))
            for base in (d, os.path.join(self.tmp, '.config', 'php-quickpatch', 'sites.d')):
                write(os.path.join(base, 'legacy.test.conf'),
                      '# qp-site-id = legacy.test\nexclude_dirs = tests\nexclude_reason = too short\n')
            conf = CE.site_conf({'site_id': 'legacy.test', 'site_key': 'legacy.test'})
            self.assertEqual(conf['exclude_dirs'], [])
            self.assertIn('exclude_reason < 20', conf['note'])
            self.assertEqual(CE.site_conf({'site_id': 'other.test', 'site_key': 'legacy.test'})['exclude_dirs'], [])
        finally:
            CE.SITES_D = old_d
            if old_home is not None:
                os.environ['HOME'] = old_home

    def test_php4_constructor(self):
        write(os.path.join(self.root, 'old.php'), '<?php\nclass Foo {\n  function Foo() {}\n}\n')
        sf, _, _ = self.scan('7.4', '8.5')
        self.assertEqual([(h['line'], h['rule_id']) for h in sf['hits']], [(3, 'BC-PHP-80-03')])

    def test_loaders(self):
        """TC-CMPT-022 (37 SourceGuardian files, 8.5 supported) and ionCube with no loader for 8.0."""
        for i in range(37):
            write(os.path.join(self.root, 'enc', 'f%02d.php' % i), '<?php // SourceGuardian\nsg_load("abc");\n')
        sf, _, _ = self.scan('7.4', '8.5')
        cat = C.Catalog(PACKAGED, C.check(PACKAGED))
        res = S.loaders_result(sf['loader_files'], sf['loader_unread'], cat.meta['loaders'], '8.5')
        self.assertEqual([(r['name'], r['files_count'], r['target_supported']) for r in res],
                         [('SourceGuardian', 37, True)])
        self.assertFalse(S.loader_supports('ionCube', '8.0', cat.meta['loaders']))
        self.assertTrue(S.loader_supports('ionCube', '8.5', cat.meta['loaders']))

    def test_loader_read_limit(self):
        """TC-CMPT-024: at most 50,000 files read for loader headers; the rest is counted."""
        files = ['/nonexistent/%d.php' % i for i in range(3)]
        old = S.MAX_LOADER_FILES
        S.MAX_LOADER_FILES = 1
        try:
            write(os.path.join(self.root, 'a.php'), '<?php\n')
            write(os.path.join(self.root, 'b.php'), '<?php\n')
            sf = S.scan_files('x', self.root, [os.path.join(self.root, 'a.php'), os.path.join(self.root, 'b.php')],
                              [])
        finally:
            S.MAX_LOADER_FILES = old
        self.assertEqual(sf['loader_unread'], 1)
        self.assertTrue(files)

    def test_frameworks(self):
        """TC-CMPT-025 / 027: matrix range from test data; framework missing from the matrix -> unknown."""
        rows = [{'framework': 'Laravel', 'versions': '11', 'php_min': '8.2', 'php_max': '8.5'}]
        write(os.path.join(self.root, 'composer.lock'), json.dumps({'packages': [
            {'name': 'laravel/framework', 'version': 'v11.9.0'}, {'name': 'joomla/cms', 'version': '2.5.0'}]}))
        fw = S.frameworks(self.root, rows, self.bc, '8.5')
        self.assertIn({'name': 'laravel', 'version': '11.9.0', 'php_min': '8.2', 'php_max': '8.5',
                       'supports_target': True}, fw)
        self.assertEqual([f['supports_target'] for f in fw if f['name'] == 'joomla'], ['unknown'])

    def test_budget(self):
        """TC-CMPT-005: the scan stops when the budget is spent."""
        write(os.path.join(self.root, 'a.php'), '<?php\n')
        b = S.Budget(0)
        time.sleep(0.01)
        sf = S.scan_files('x', self.root, [os.path.join(self.root, 'a.php')], [], budget=b)
        self.assertFalse(sf['complete'])


class IniTest(unittest.TestCase):
    """FR-CMPT-INI-001 (TC-CMPT-019 KQ1, TC-CMPT-021 KQ1)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(PACKAGED, 'bc_rules.json'), encoding='utf-8') as f:
            self.bc = json.load(f)
        self.root = os.path.join(self.tmp, 'www')
        write(os.path.join(self.root, '.user.ini'), '; comment\nmemory_limit = 128M\ntrack_errors = On\n')
        self.pool = os.path.join(self.tmp, 'pool.conf')
        write(self.pool, '[www]\nlisten = /run/php/x.sock\nphp_admin_value[mbstring.func_overload] = 0\n')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def findings(self, old):
        out = ini.findings(self.bc, old, '8.5', {'docroot': self.root, 'runtime_endpoint': None}, {})
        rules = ini.removed(self.bc, old, '8.5')
        for r in rules:
            r['_rx'] = ini._patterns(r['directive'])
        out += ini.scan_file(self.pool, rules, ('ini', 'pool'))
        return out

    def test_removed_in_80(self):
        got = sorted((os.path.basename(f['file']), f['line'], f['directive'], f['removed_in']) for f in self.findings('7.4'))
        self.assertEqual(got, [('.user.ini', 3, 'track_errors', '8.0'), ('pool.conf', 3, 'mbstring.func_overload', '8.0')])

    def test_left_open_range(self):
        self.assertEqual([f for f in self.findings('8.0') if f['directive'] == 'track_errors'], [])


class DepsTest(unittest.TestCase):
    """FR-CMPT-COMP-001/002 (TC-CMPT-013, 014), FR-CMPT-NPM-001 (TC-CMPT-016, 018)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.feeds = os.path.join(self.tmp, 'feeds')
        self.root = os.path.join(self.tmp, 'app')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def cache(self, kind, name, body):
        write(os.path.join(self.feeds, 'cache', kind, deps._cache_name(name)),
              json.dumps({'fetched_at': time.time(), 'url': 'x', 'body': body}))

    def test_composer_blockers_and_min_compatible(self):
        write(os.path.join(self.root, 'composer.lock'), json.dumps({
            'packages': [{'name': 'vendor-test/a', 'version': '2.1.0', 'require': {'php': '^7.4 || ~8.0.0'}},
                         {'name': 'vendor-test/ok', 'version': '1.0.0', 'require': {'php': '>=7.2', 'ext-intl': '*'}}],
            'packages-dev': [{'name': 'vendor-test/dev', 'version': '0.1.0', 'require': {'php': '<8.0'}}]}))
        blockers, ext_req, has = deps.composer_blockers(self.root, '8.5.12')
        self.assertTrue(has)
        self.assertEqual(ext_req, ['intl'])
        self.assertEqual([(b['package'], b['dev']) for b in blockers], [('vendor-test/a', False), ('vendor-test/dev', True)])
        # Packagist p2 minified: each entry inherits the keys of the one before it.
        self.cache('packagist', 'vendor-test/a', {'packages': {'vendor-test/a': [
            {'version': '3.0.0-beta1', 'require': {'php': '>=8.1'}}, {'version': '2.4.0'},
            {'version': '2.3.0', 'require': {'php': '^7.4 || ^8.0'}}, {'version': '2.2.0', 'require': {'php': '^7.4'}},
            {'version': '2.1.0'}]}})
        self.assertEqual(deps.min_compatible('vendor-test/a', '2.1.0', '8.5.12', self.feeds), ('2.3.0', None))

    def test_packagist_offline_unknown(self):
        mc, err = deps.min_compatible('vendor-test/zz', '1.0.0', '8.5.12', self.feeds, offline=True)
        self.assertEqual(mc, 'unknown')
        self.assertIn('offline', err)

    def test_registry_https_only(self):
        write(os.path.join(self.feeds, 'sources.conf'),
              '[registry]\npackagist_url = http://evil.test\nnpm_url = https://npm.mirror.test/\n')
        u = deps.registry_urls(self.feeds)
        self.assertEqual((u['packagist_url'], u['npm_url']), ('https://repo.packagist.org', 'https://npm.mirror.test'))

    def test_npm_engines_lock_v3(self):
        write(os.path.join(self.root, 'package.json'), json.dumps({'name': 'api', 'engines': {'node': '>=18'}}))
        write(os.path.join(self.root, 'package-lock.json'), json.dumps({'lockfileVersion': 3, 'packages': {
            '': {'name': 'api'},
            'node_modules/pkg-a': {'version': '1.0.0', 'engines': {'node': '>=18'}},
            'node_modules/pkg-b': {'version': '2.0.0', 'engines': {'node': '<=20'}},
            'node_modules/pkg-c': {'version': '3.0.0', 'engines': {'node': '<=16'}, 'dev': True},
            'node_modules/pkg-d': {'version': '4.0.0'}}}))
        self.cache('npm', 'pkg-d', {'versions': {'4.0.0': {'engines': {'node': '>=12'}}}})
        viol, unknown, _ = deps.npm_engines(self.root, '24.11.0', self.feeds)
        self.assertEqual([(v['package'], v['severity']) for v in viol], [('pkg-b', 'error'), ('pkg-c', 'warning')])
        self.assertEqual(unknown, [])
        shutil.rmtree(os.path.join(self.feeds, 'cache'))
        _, unknown, _ = deps.npm_engines(self.root, '24.11.0', self.feeds, offline=True)
        self.assertEqual([u['package'] for u in unknown], ['pkg-d'])

    def test_yarn_only_warning(self):
        write(os.path.join(self.root, 'yarn.lock'), '# yarn\n')
        _, _, warns = deps.npm_engines(self.root, '24.11.0', self.feeds)
        self.assertTrue(warns and 'yarn' in warns[0])


class ToolsTest(unittest.TestCase):
    """FR-CMPT-TOOL-001: tools only from the catalog pins, checked before use (TC-CMPT-002, 003)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, 'repo')
        os.makedirs(self.repo)
        env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t',
                   GIT_COMMITTER_EMAIL='t@t')
        write(os.path.join(self.repo, 'bin', 'phpcs'), '#!/bin/sh\n')
        for cmd in (['init', '-q'], ['add', '.'], ['commit', '-qm', 'x']):
            subprocess.run(['git', '-C', self.repo] + cmd, check=True, env=env)
        self.ref = subprocess.run(['git', '-C', self.repo, 'rev-parse', 'HEAD'], stdout=subprocess.PIPE,
                                  check=True).stdout.decode().strip()
        data = subprocess.run(['git', '-C', self.repo, 'archive', '--format=tar', self.ref], stdout=subprocess.PIPE,
                              check=True).stdout
        self.sha = hashlib.sha256(data).hexdigest()
        self.state = os.path.join(self.tmp, 'state')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def meta(self, sha):
        pk = [{'name': n, 'version': '1.0.0', 'reference': self.ref, 'git_url': 'file://' + self.repo,
               'archive_sha256': sha, 'dist_url': None, 'dist_sha256': None} for n in T.GROUPS['phpcs']]
        return {'tools': {'packages': pk, 'composer': []}}

    def test_install_checked(self):
        tools = T.install(self.state, self.meta(self.sha), 'phpcs', allow=('file',))
        self.assertEqual(sorted(t['name'] for t in tools), sorted(T.GROUPS['phpcs']))
        self.assertTrue(all(t['sha256'] == self.sha and t['source'] == 'git' for t in tools))
        self.assertTrue(T.installed(self.state, 'phpcs'))
        with open(T.manifest_path(self.state)) as f:
            man = json.load(f)
        self.assertEqual(len(man['tools']), len(T.GROUPS['phpcs']))

    def test_tampered_hash(self):
        with self.assertRaises(T.ToolError) as cm:
            T.install(self.state, self.meta('0' * 64), 'phpcs', allow=('file',))
        self.assertEqual(cm.exception.code, 'ERR-PTCH-502-01')
        left = [n for n in os.listdir(T.tools_dir(self.state)) if n != 'tools_manifest.json']
        self.assertEqual(left, [])

    def test_offline_or_scheme_refused(self):
        with self.assertRaises(T.ToolError) as cm:
            T.install(self.state, self.meta(self.sha), 'phpcs', offline=True)
        self.assertEqual(cm.exception.code, 'ERR-CMPT-424-01')
        with self.assertRaises(T.ToolError) as cm:
            T.install(self.state, self.meta(self.sha), 'phpcs')       # file:// not allowed by default
        self.assertEqual(cm.exception.code, 'ERR-CMPT-424-01')

    def test_catalog_pins(self):
        meta = C.Catalog(PACKAGED, C.check(PACKAGED)).meta['tools']
        names = {p['name']: p['version'] for p in meta['packages']}
        self.assertEqual(names['phpcompatibility/php-compatibility'], '10.0.0-alpha2')
        self.assertEqual(names['squizlabs/php_codesniffer'], '4.0.4')
        self.assertEqual(names['rector/rector'], '2.7.0')
        self.assertTrue(all(len(p['archive_sha256']) == 64 for p in meta['packages']))
        self.assertEqual(sorted((c['name'], c['version']) for c in meta['composer'])[0][1][:4], '2.10')


def result(site_id, hits=(), parts=None, **kw):
    res = {'site_id': site_id, 'site_key': site_id, 'old_branch': '8.4', 'target_branch': '8.5',
           'target_patch': '8.5.12', 'hits': [], 'composer_blockers': [], 'npm_engine_violations': [],
           'native_addons': [], 'extension_gaps': [], 'frameworks': [], 'loaders': [], 'errors': [],
           'parts': parts or {'code_scan': 'done', 'phpcompat': 'done', 'lint_new_bin': 'done',
                              'composer_platform': 'done'}, 'finished_at': 'now'}
    for n, (rule, level, src) in enumerate(hits):
        res['hits'].append({'hit_id': 'H-%012x' % (hash(site_id) % 10 ** 9 + n), 'site_id': site_id, 'file': 'a.php',
                            'line': n + 1, 'rule_id': rule, 'level': level, 'snippet': '', 'source': src,
                            'waived': False, 'waiver': None})
    res.update(kw)
    res['verdict'] = CE.verdict(res)
    return res


class VerdictPlanTest(unittest.TestCase):
    """FR-CMPT-RES-001 (TC-CMPT-028..030), FR-PLAN-GEN-002 (TC-PLAN-008..010, 012), FR-PLAN-DEP-001
    (TC-PLAN-011, 013), TC-SCN-013 KQ2, TC-CMPT-020/021."""

    @classmethod
    def setUpClass(cls):
        cls.cat = C.Catalog(PACKAGED, C.check(PACKAGED))

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rt = {'runtime_id': 'php:aaaaaaaaaaaa', 'kind': 'php', 'bin': '/usr/bin/php8.4',
                   'scenario_ids': ['SCN-PHP-012']}
        self.scan = {'result': {'environment': {'restrictions': []}, 'wordpress_findings': []}}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def plan(self, results, files):
        sites = [{'site_id': s, 'docroot': os.path.join(self.tmp, s), 'binding_kind': 'nginx_fastcgi',
                  'pb_id': 'PB-005'} for s in sorted(files)]
        items = PL.assemble(self.cat, self.rt, sites, 'cross_branch', {'branch': '8.5'}, self.scan, '8.4', results)
        plan = {'plan_id': 'PLN-20261025-000000-abcd', 'site_order': sorted(files), 'runtime_kind': 'php',
                'target': {'branch': '8.5', 'patch_version': '8.5.12'}}
        PL.apply_compat(plan, items, results, files)
        return plan, items

    def test_pass_verdict(self):
        """TC-CMPT-028: 0 errors, 12 warnings, check-platform-reqs exit 0."""
        v = result('a.test', [('BC-PHP-84-01', 'warning', 'bc_rules')] * 12)['verdict']
        self.assertEqual({k: v[k] for k in ('status', 'errors', 'warnings', 'waived', 'pending_parts')},
                         {'status': 'PASS', 'errors': 0, 'warnings': 12, 'waived': 0, 'pending_parts': []})

    def test_waive_and_pending(self):
        """TC-CMPT-030: 1 error waived, $NEW_BIN missing -> PENDING with lint_new_bin."""
        res = result('a.test', [('BC-PHP-80-02', 'error', 'bc_rules')],
                     parts={'code_scan': 'done', 'phpcompat': 'done', 'lint_new_bin': 'pending'})
        self.assertEqual(res['verdict']['status'], 'FAIL')
        hid = res['hits'][0]['hit_id']
        self.assertEqual(CE.waive(res, ['H-000000000000'], 'r' * 20, 'cli:root'), ([], [], ['H-000000000000']))
        done, already, bad = CE.waive(res, [hid], 'tests folder is not deployed', 'cli:root')
        self.assertEqual((done, already, bad), ([hid], [], []))
        self.assertEqual((res['verdict']['status'], res['verdict']['waived'], res['verdict']['pending_parts']),
                         ('PENDING', 1, ['lint_new_bin']))
        self.assertEqual(CE.waive(res, [hid], 'tests folder is not deployed', 'cli:root'), ([], [hid], []))
        again = CE.finish(result('a.test', [('BC-PHP-80-02', 'error', 'bc_rules')]), res)   # rescan keeps waivers
        self.assertTrue(again['hits'][0]['waived'])

    def test_reusable(self):
        scan = {'result': {'scan_fingerprint': 'f1', 'runtimes': []}}
        prev = dict(result('a.test'), scan_fingerprint='f1')
        self.assertTrue(CE.reusable(prev, scan, {'branch': '8.5', 'patch_version': '8.5.12'}, 'php'))
        self.assertFalse(CE.reusable(prev, {'result': {'scan_fingerprint': 'f2'}},
                                     {'branch': '8.5', 'patch_version': '8.5.12'}, 'php'))
        self.assertFalse(CE.reusable(prev, scan, {'branch': '8.5', 'patch_version': '8.5.13'}, 'php'))

    def test_site_order_and_blocked(self):
        """TC-PLAN-008/010 (PASS by file count then site_id) and TC-PLAN-009 (FAIL blocked, P5 reason)."""
        files = {'c.test': 3500, 'a.test': 120, 'b.test': 800, 'x.test': 500, 'w.test': 500, 'd.test': 10}
        results = {s: result(s) for s in files}
        results['d.test'] = result('d.test', [('BC-PHP-80-02', 'error', 'bc_rules')] * 2)
        plan, items = self.plan(results, files)
        self.assertEqual(plan['site_order'], ['a.test', 'w.test', 'x.test', 'b.test', 'c.test', 'd.test'])
        self.assertEqual(plan['canary_site_id'], 'a.test')
        self.assertEqual([b['site_id'] for b in plan['blocked_sites']], ['d.test'])
        p5 = [i for i in items if i['phase'] == 'P5' and i['site_id'] == 'd.test']
        self.assertTrue(p5 and all(i['status'] == 'PENDING' and i['reason'].startswith('blocked: compatibility FAIL')
                                   for i in p5))
        with self.assertRaises(Exception) as cm:
            PL.blocked_site_error(plan, p5[0])
        self.assertEqual(cm.exception.code, 'ERR-UPG-409-01')
        self.assertIn('d.test', cm.exception.message)
        self.assertIn(' 2 ', cm.exception.message)
        p3 = [i for i in items if i['site_id'] == 'd.test' and (i.get('cli_action') or '').startswith('compat')]
        self.assertEqual(sorted({(','.join(PL.parts_of(i)), i['status']) for i in p3}),
                         [('composer_platform', 'DONE'), ('lint_new_bin,phpcompat,code_scan', 'FAILED')])

    def test_upgrade_items_and_p4(self):
        """TC-PLAN-011, TC-SCN-013 KQ2 (2 packages -> -01, -02), TC-CMPT-020/021, TC-PLAN-013 KQ2."""
        res = result('a.test', composer_blockers=[
            {'package': 'vendor-test/b', 'version': '1.0.0', 'constraint': '>=7.1 <8.1', 'dev': False,
             'min_compatible_version': '1.4.0'},
            {'package': 'vendor-test/c', 'version': '2.0.0', 'constraint': '<8.0', 'dev': False,
             'min_compatible_version': 'unknown'}],
            extension_gaps=[{'extension': 'legacy_test', 'package_new': 'php8.5-legacy-test', 'resolution': 'missing',
                             'usage_hits': 14, 'replacement': None},
                            {'extension': 'unused_test', 'package_new': 'php8.5-unused-test', 'resolution': 'missing',
                             'usage_hits': 0, 'replacement': None}],
            npm_engine_violations=[{'package': 'pkg-c', 'version': '1', 'engines': '<=16', 'dev': True,
                                    'severity': 'warning'}])
        plan, items = self.plan({'a.test': res}, {'a.test': 10})
        rows = plan['upgrade_items']
        comp = [r for r in rows if r['component_type'] == 'composer']
        self.assertEqual([(r['name'], r['min_compatible'], r['chk_id']) for r in comp],
                         [('vendor-test/b', '1.4.0', 'CHK-PHP-012-13-01'), ('vendor-test/c', 'unknown', 'CHK-PHP-012-13-02')])
        for r in rows:
            for k in ('component_type', 'name', 'current', 'required', 'min_compatible', 'evidence', 'chk_id'):
                self.assertIn(k, r)
        p4 = {i['chk_id']: i for i in items if i['phase'] == 'P4' and i['site_id'] == 'a.test'}
        self.assertEqual(sorted(k for k in p4 if k.startswith('CHK-PHP-012-13')),
                         ['CHK-PHP-012-13-01', 'CHK-PHP-012-13-02', 'CHK-PHP-012-13-03', 'CHK-PHP-012-13-04'])
        self.assertEqual(p4['CHK-PHP-012-13-03']['status'], 'PENDING')         # legacy_test, 14 calls
        self.assertEqual(p4['CHK-PHP-012-13-04']['status'], 'SKIPPED')         # unused_test, 0 calls
        self.assertEqual([r['chk_id'] for r in rows if r['component_type'] == 'npm'], [None])   # dev: warning only
        p5 = [i for i in items if i['phase'] == 'P5' and i['site_id'] == 'a.test' and i['status'] == 'PENDING']
        self.assertIn('CHK-PHP-012-13-03@a.test', p5[0]['depends_on'])
        self.assertNotIn('CHK-PHP-012-13-04@a.test', p5[0]['depends_on'])
        # A rescan with nothing to upgrade gives the template item back.
        PL.apply_compat(plan, items, {'a.test': result('a.test')})
        self.assertEqual([i['chk_id'] for i in items if i['phase'] == 'P4' and i['chk_id'].startswith('CHK-PHP-012-13')],
                         ['CHK-PHP-012-13-01'])
        self.assertEqual(plan['upgrade_items'], [])

    def test_loader_without_target_blocks(self):
        """TC-PLAN-012: a loader with no build for the target puts the site in blocked_sites."""
        res = result('a.test', loaders=[{'name': 'ionCube', 'files_count': 3, 'sample': 'x.php',
                                         'target_supported': False, 'files_unread': 0}])
        plan, items = self.plan({'a.test': res}, {'a.test': 10})
        self.assertEqual([b['site_id'] for b in plan['blocked_sites']], ['a.test'])
        p5 = next(i for i in items if i['phase'] == 'P5' and i['site_id'] == 'a.test' and i['status'] == 'PENDING')
        with self.assertRaises(Exception) as cm:
            PL.blocked_site_error(plan, p5)
        self.assertEqual(cm.exception.code, 'ERR-SCN-409-03')

    def test_loader_limits(self):
        """BR-SCN-043 / TC-CMPT-023: branches without a loader build are left out of the candidates."""
        from qplib import assess as A

        class Cat(object):
            meta = {'loaders': {'ioncube': {'min_loader_by_branch': {}, 'no_loader_branches': []}}}
        lim = A.loader_limits(Cat(), {'extensions': ['core', 'the ioncube php loader']})
        self.assertEqual([(n, ok('8.5')) for n, ok in lim], [('ionCube', False)])
        lim = A.loader_limits(self.cat, {'extensions': ['the ioncube php loader']})
        self.assertEqual([(ok('8.0'), ok('8.5')) for _, ok in lim], [(False, True)])
        self.assertEqual(A.loader_limits(self.cat, {'extensions': ['core']}), [])

    def test_framework_unknown_needs_confirmation(self):
        """TC-CMPT-027: framework missing from the matrix -> MANUAL item to confirm the PHP range."""
        res = result('a.test', frameworks=[{'name': 'joomla', 'version': '2.5.0', 'php_min': None, 'php_max': None,
                                            'supports_target': 'unknown'}])
        plan, items = self.plan({'a.test': res}, {'a.test': 10})
        it = [i for i in items if i.get('component', {}).get('type') == 'framework']
        self.assertEqual([(i['exec_type'], i['action'][:31]) for i in it], [('MANUAL', 'Confirm the PHP range of joomla')])


NODE_SRC = '/opt/node22'


@unittest.skipUnless(os.path.isfile(os.path.join(NODE_SRC, 'bin', 'node')), 'no Node.js to copy')
class AddonTest(unittest.TestCase):
    """FR-CMPT-NPM-002 (TC-CMPT-016 KQ2, TC-CMPT-017, TC-CMPT-102 KQ1-3) with a real Node.js copied to
    a prefix of the test (never the original one)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.prefix = os.path.join(cls.tmp, 'node24')
        os.makedirs(os.path.join(cls.prefix, 'bin'))
        shutil.copy2(os.path.join(NODE_SRC, 'bin', 'node'), os.path.join(cls.prefix, 'bin', 'node'))
        shutil.copytree(os.path.join(NODE_SRC, 'lib', 'node_modules', 'npm'),
                        os.path.join(cls.prefix, 'lib', 'node_modules', 'npm'), symlinks=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_load_and_lockfile_v1(self):
        app = os.path.join(self.tmp, 'app')
        write(os.path.join(app, 'package.json'), json.dumps({'name': 'legacy-node', 'version': '1.0.0'}))
        write(os.path.join(app, 'package-lock.json'), json.dumps(
            {'name': 'legacy-node', 'version': '1.0.0', 'lockfileVersion': 1, 'requires': True}, indent=2))
        ok = os.path.join(app, 'node_modules', 'addon-test')
        write(os.path.join(ok, 'package.json'), json.dumps({'name': 'addon-test', 'version': '1.0.0'}))
        write(os.path.join(ok, 'binding.gyp'), '{"targets": []}')
        write(os.path.join(ok, 'index.js'), 'module.exports = 1;\n')
        bad = os.path.join(app, 'node_modules', 'addon-bad')
        write(os.path.join(bad, 'package.json'), json.dumps({'name': 'addon-bad', 'version': '1.0.0'}))
        write(os.path.join(bad, 'build', 'Release', 'bad.node'), 'not an ELF file')
        write(os.path.join(bad, 'index.js'), "module.exports = require('./build/Release/bad.node');\n")
        self.assertEqual(deps.find_addons(app), ['addon-bad', 'addon-test'])
        with open(os.path.join(app, 'package-lock.json'), 'rb') as f:
            before = hashlib.sha256(f.read()).hexdigest()
        plan_dir = os.path.join(self.tmp, 'plan')
        os.makedirs(plan_dir)
        work = os.path.join(self.tmp, 'work', 'app')
        res, log = deps.addon_load(app, work, os.path.join(self.prefix, 'bin', 'node'), None, plan_dir, 'app')
        got = {r['package']: r['load_ok'] for r in res}
        self.assertEqual(got, {'addon-test': True, 'addon-bad': False})
        self.assertIn(('npm install --package-lock-only', 0), log)
        with open(os.path.join(plan_dir, 'lockfile-app.diff'), encoding='utf-8') as f:
            self.assertIn('"lockfileVersion": 3', f.read())
        with open(os.path.join(app, 'package-lock.json'), 'rb') as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), before)
        self.assertFalse(os.path.exists(work))


if __name__ == '__main__':
    unittest.main()
