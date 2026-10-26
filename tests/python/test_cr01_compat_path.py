"""CR-01 unit tests: `compat --path` (Node.js project directories with a target branch) and its report."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib.compat import project as P, report as RP  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


SAM = """Resources:
  ResetPassword:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: functions/reset/
      Handler: index.handler
      Runtime: nodejs18.x
  Verify:
    Type: AWS::Serverless::Function
    Properties:
      Handler: functions/verify/index.handler
      Runtime: nodejs18.x
"""


class DeclarationsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, 'repo')
        write(os.path.join(self.repo, 'template.yaml'), SAM)
        write(os.path.join(self.repo, 'cdk', 'stack.ts'), "new lambda.Function(this, 'F', { runtime: lambda.Runtime.NODEJS_18_X });\n")
        write(os.path.join(self.repo, 'Dockerfile'), 'FROM public.ecr.aws/lambda/nodejs:18\n')
        write(os.path.join(self.repo, '.nvmrc'), 'v18.20.4\n')
        write(os.path.join(self.repo, '.github', 'workflows', 'ci.yml'), 'steps:\n  - with:\n      node-version: "18"\n')
        write(os.path.join(self.repo, 'node_modules', 'x', 'template.yaml'), 'Runtime: nodejs16.x\n')
        for f in ('reset', 'verify'):
            write(os.path.join(self.repo, 'functions', f, 'package.json'), json.dumps({'name': f}))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_kinds_and_owners(self):
        decl = P.declarations(self.repo)
        got = sorted((d['file'], d['line'], d['kind'], d['branch']) for d in decl)
        self.assertEqual(got, [
            ('.github/workflows/ci.yml', 3, 'ci_node_version', '18'), ('.nvmrc', 1, 'version_file', '18'),
            ('Dockerfile', 1, 'container_image', '18'), ('cdk/stack.ts', 1, 'cdk_runtime', '18'),
            ('template.yaml', 7, 'lambda_runtime', '18'), ('template.yaml', 12, 'lambda_runtime', '18')])
        projects = P.find_projects([self.repo])
        self.assertEqual([os.path.basename(p) for p in projects], ['reset', 'verify'])
        own = {(d['file'], d['line']): P.owner_of(d, projects) for d in decl}
        self.assertEqual(os.path.basename(own[('template.yaml', 7)]), 'reset')        # CodeUri
        self.assertEqual(os.path.basename(own[('template.yaml', 12)]), 'verify')      # Handler path
        self.assertIsNone(own[('Dockerfile', 1)])

    def test_suggestions(self):
        for d in P.declarations(self.repo):
            s = RP.suggestion(d, '22')
            self.assertNotIn('18', s.replace('18.20', ''), (d, s))
            self.assertIn('22', s)


class FixTargetTest(unittest.TestCase):
    def test_every_advisory(self):
        by = {'GHSA-a': {'fixed': ['0.21.2']}, 'GHSA-b': {'fixed': ['0.28.0', '1.6.0']}, 'GHSA-c': {'fixed': ['1.7.4']},
              'GHSA-d': {'fixed': []}}
        self.assertEqual(P.fix_target('0.21.1', by), ('1.7.4', True, ['GHSA-d']))
        self.assertEqual(P.fix_target('0.21.1', {'GHSA-a': {'fixed': ['0.21.2']}, 'GHSA-b': {'fixed': ['0.28.0', '1.6.0']}}),
                         ('0.28.0', False, []))
        self.assertEqual(P.fix_target('2.0.0', {'MAL-1': {'fixed': []}}), (None, None, ['MAL-1']))


class LockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_v1_and_v3(self):
        write(os.path.join(self.tmp, 'a', 'package-lock.json'), json.dumps({'lockfileVersion': 3, 'packages': {
            '': {}, 'node_modules/x': {'version': '1.0.0'}, 'node_modules/x/node_modules/y': {'version': '2.0.0', 'dev': True},
            'node_modules/l': {'link': True}}}))
        self.assertEqual(P.lock_packages(os.path.join(self.tmp, 'a')),
                         ('package-lock.json', [('x', '1.0.0', False), ('y', '2.0.0', True)]))
        write(os.path.join(self.tmp, 'b', 'npm-shrinkwrap.json'), json.dumps({'lockfileVersion': 1, 'dependencies': {
            'x': {'version': '1.0.0', 'dependencies': {'z': {'version': '3.0.0', 'dev': True}}}}}))
        self.assertEqual(P.lock_packages(os.path.join(self.tmp, 'b')),
                         ('npm-shrinkwrap.json', [('x', '1.0.0', False), ('z', '3.0.0', True)]))
        self.assertEqual(P.lock_packages(self.tmp), (None, []))


def project(**kw):
    p = {'path': '/r/app', 'name': 'app', 'current_branch': '18', 'current_source': 'declarations',
         'target_branch': '22', 'target_patch': '22.23.4', 'engines': '>=18', 'declarations': [], 'packages': 3,
         'npm_engine_violations': [], 'hits': [], 'native_addons': [], 'vulnerabilities': [], 'deprecated': [],
         'parts': {'code_scan': 'done', 'npm_engines': 'done', 'vulnerabilities': 'done'}, 'errors': [], 'notes': [],
         'files_scanned': 2}
    p.update(kw)
    p['verdict'] = P.verdict(p)
    p['work_items'] = P.work_items(p)
    return p


class VerdictReportTest(unittest.TestCase):
    def result(self, projects):
        return {'run_id': 'x', 'generated_at': '2026-10-26T00:00:00.000Z', 'paths': ['/r'], 'target_branch': '22',
                'current_branch': '18', 'catalog_version': '2026.10.25-1', 'shared_declarations': [],
                'lifecycle': {'today': '2026-10-26', 'bundle_id': 'b-1', 'min_eol': '2027-10-26', 'recommended': '24',
                              'target_ok': False,
                              'current': {'branch': '18', 'status': 'EOL', 'eol_date': '2025-04-30', 'days_to_eol': -544,
                                          'latest': '18.20.8', 'lts': True},
                              'target': {'branch': '22', 'status': 'MAINTENANCE_LTS', 'eol_date': '2027-04-30',
                                         'days_to_eol': 186, 'latest': '22.23.4', 'lts': True}},
                'summary': {'projects': len(projects), 'by_status': {}, 'vulnerable_packages': 0, 'runtime_changes': 0,
                            'deprecated': 0, 'errors': 0},
                'projects': projects}

    def test_verdicts(self):
        self.assertEqual(project()['verdict']['status'], 'PASS')
        self.assertEqual(project(hits=[{'level': 'error', 'file': 'a.js', 'line': 1, 'rule_id': 'BC-NODE-22-01',
                                        'snippet': 'x'}])['verdict']['status'], 'FAIL')
        self.assertEqual(project(npm_engine_violations=[{'package': 'b', 'severity': 'error', 'engines': '<=20'}])
                         ['verdict']['status'], 'FAIL')
        self.assertEqual(project(parts={'code_scan': 'pending'})['verdict']['pending_parts'], ['code_scan'])
        w = project(engines='<=20', vulnerabilities=[
            {'package': 'a', 'version': '1', 'severity': 'high', 'dev': False, 'fix_version': '2', 'major_bump': True,
             'advisories': ['G'], 'unfixed_advisories': []},
            {'package': 'b', 'version': '1', 'severity': 'low', 'dev': True, 'fix_version': None, 'major_bump': None,
             'advisories': ['H'], 'unfixed_advisories': ['H']}])['work_items']
        self.assertEqual([(x['kind'], x['count'], x['size']) for x in w],
                         [('engines_field', 1, 'S'), ('vuln_major_upgrades', 1, 'M'), ('vuln_dev_only', 1, 'S'),
                          ('regression_test', 1, 'S')])

    def test_report_escapes(self):
        evil = '<script>alert(1)</script>'
        p = project(name='app' + evil, hits=[{'level': 'warning', 'file': 'a|b.js', 'line': 3, 'rule_id': 'BC-NODE-20-01',
                                               'snippet': 'url.parse(x) // ' + evil}],
                    deprecated=[{'package': 'aws-sdk', 'version': '2.1.0', 'source': 'catalog', 'message': 'v2 ' + evil,
                                 'replacement': '@aws-sdk/client-*', 'call_sites': [{'file': 'i.js', 'line': 1}]}])
        res = self.result([p])
        h = RP.render_html(res, 'vi')
        self.assertNotIn('<script', h)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', h)
        self.assertIn('Khuyến nghị Node.js 24', h)
        self.assertIn('Node.js 18 đã hết hỗ trợ từ 2025-04-30', h)
        m = RP.render_md(res, 'en')
        self.assertNotIn('<script', m)
        self.assertIn('a\\|b.js', m)
        self.assertIn('Migration: aws-sdk (1 project(s)).', m)

    def test_conclusions(self):
        vul = [{'package': 'axios', 'version': '0.21.1', 'severity': 'high', 'dev': False, 'fix_version': '1.7.4',
                'major_bump': True, 'advisories': ['G'], 'unfixed_advisories': []}]
        res = self.result([project(vulnerabilities=vul)])
        res['summary']['runtime_changes'] = 3
        c = RP.conclusions(res, 'en')
        self.assertEqual(c[0], 'Upgrading to Node.js 22: no compatibility blocker found in the code and dependencies.')
        self.assertIn('1 vulnerable package version(s) in production dependencies (high 1); 1 fixed by an upgrade '
                      '(1 to a new major), 0 with no fixed version.', c[1])
        self.assertIn('3 place(s) declare Node.js 18 and must change to 22.', c[2])

    def test_write_no_symlink(self):
        d = tempfile.mkdtemp()
        try:
            res = self.result([project()])
            target = os.path.join(d, 'secret')
            write(target, 'keep')
            os.symlink(target, os.path.join(d, 'r.md'))
            RP.write(res, os.path.join(d, 'r.md'), 'en')
            with open(target) as f:
                self.assertEqual(f.read(), 'keep')               # the link is replaced, not followed
            self.assertFalse(os.path.islink(os.path.join(d, 'r.md')))
        finally:
            shutil.rmtree(d)


class RunOfflineTest(unittest.TestCase):
    """End to end without network or feeds bundle: everything that needs data is PENDING, nothing is written
    under the scanned path."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, 'state')
        os.makedirs(self.state, 0o700)
        self.repo = os.path.join(self.tmp, 'repo')
        write(os.path.join(self.repo, 'template.yaml'), SAM)
        write(os.path.join(self.repo, 'functions', 'reset', 'package.json'),
              json.dumps({'name': 'reset', 'dependencies': {'aws-sdk': '^2'}}))
        write(os.path.join(self.repo, 'functions', 'reset', 'package-lock.json'), json.dumps(
            {'lockfileVersion': 3, 'packages': {'': {}, 'node_modules/aws-sdk': {'version': '2.1.0',
                                                                             'engines': {'node': '>= 10.0.0'}}}}))
        write(os.path.join(self.repo, 'functions', 'reset', 'index.js'),
              "const AWS = require('aws-sdk');\nconst url = require('url');\nconst u = url.parse(x);\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_run(self):
        before = sorted(os.walk(self.repo))
        w = []
        res = P.run(self.state, [self.repo], '22', offline=True, lang='en', today='2026-10-26', warnings=w)
        self.assertEqual(sorted(os.walk(self.repo)), before)
        self.assertEqual(res['lifecycle'], None)
        self.assertEqual(w[0][0], 'ERR-FEED-503-01')
        p = res['projects'][0]
        self.assertEqual((p['name'], p['current_branch'], p['current_source']), ('reset', '18', 'declarations'))
        self.assertEqual([(h['rule_id'], h['line']) for h in p['hits']], [('BC-NODE-20-01', 3)])
        self.assertIsNone(p['vulnerabilities'])
        self.assertEqual(p['verdict']['status'], 'PENDING')
        self.assertEqual([(d['package'], d['source'], d['call_sites']) for d in p['deprecated']],
                         [('aws-sdk', 'catalog', [{'file': 'index.js', 'line': 1}])])
        self.assertEqual(res['target_patch'], '22.0.0')
        self.assertTrue(os.path.isdir(res['artifacts_dir']))


if __name__ == '__main__':
    unittest.main()
