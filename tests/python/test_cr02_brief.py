"""CR-02 unit tests: answers for the customer in the compat report (qplib/compat/brief.py)."""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib.compat import brief as B, report as RP  # noqa: E402


def project(name, vulns=None, decls=None, deprecated=None, hits=None, work=None):
    return {'name': name, 'path': '/r/' + name, 'packages': 10, 'current_branch': '18',
            'vulnerabilities': vulns, 'declarations': decls or [], 'deprecated': deprecated or [],
            'hits': hits or [], 'npm_engine_violations': [], 'native_addons': [],
            'verdict': {'status': 'PASS', 'errors': 0, 'blockers': 0, 'pending_parts': [], 'by_severity': {}},
            'work_items': work or [{'kind': 'regression_test', 'count': 1, 'size': 'S'}]}


def result(projects, today='2026-10-22', target='22', target_ok=False):
    return {'target_branch': target, 'current_branch': '18', 'generated_at': today + 'T08:00:00.000Z',
            'paths': ['/r'], 'shared_declarations': [], 'projects': projects,
            'lifecycle': {'today': today, 'current': {'branch': '18', 'status': 'EOL', 'eol_date': '2025-04-30',
                                                      'unpatched': {'version': '18.20.8', 'critical': 0, 'high': 2,
                                                                    'medium': 1, 'low': 0, 'kev': 0}},
                          'target': {'branch': target, 'status': 'MAINTENANCE_LTS', 'eol_date': '2027-04-30',
                                     'days_to_eol': 190}, 'recommended': '24', 'recommended_eol': '2028-04-30',
                          'target_ok': target_ok}}


LAMBDA = {'file': 'template.yaml', 'line': 6, 'kind': 'lambda_runtime', 'text': 'Runtime: nodejs18.x', 'branch': '18',
          'to_change': True}


class BriefTest(unittest.TestCase):
    def test_lambda_risk_levels_by_date(self):
        """AWS table: nodejs18.x deprecated 2025-09-01, block create 2027-07-29, block update 2027-08-31."""
        keys = lambda today: {x['key']: x['level'] for x in B.build(        # noqa: E731
            result([project('reset', vulns=[], decls=[LAMBDA])], today=today), 'en')['risks']}
        self.assertEqual(keys('2026-10-22')['r_lambda_deprecated'], 'high')
        self.assertEqual(keys('2027-09-01')['r_lambda_blocked'], 'critical')
        self.assertNotIn('r_lambda_deprecated', keys('2025-08-01'))
        r = next(x for x in B.build(result([project('reset', vulns=[], decls=[LAMBDA])], today='2026-10-22'), 'vi')['risks']
                 if x['key'] == 'r_lambda_deprecated')
        self.assertIn('Amazon Linux 2) đã hết vòng đời từ 2026-06-30', B._risk_text(r, 'vi'))

    def test_runtime_eol_counts_unpatched(self):
        res = result([project('reset', vulns=[])])
        r = next(x for x in B.build(res, 'vi')['risks'] if x['key'] == 'r_runtime_eol')
        self.assertEqual(r['level'], 'high')
        self.assertIn('3 lỗ hổng', B._risk_text(r, 'vi'))

    def test_dependencies_kev_is_critical_and_unique(self):
        v = {'package': 'axios', 'version': '0.21.1', 'severity': 'high', 'advisories': ['GHSA-1'], 'dev': False,
             'fix_version': '0.28.0', 'major_bump': False, 'in_kev': True}
        res = result([project('a', vulns=[v]), project('b', vulns=[dict(v)])])
        b = B.build(res, 'en')
        dep = next(x for x in b['risks'] if x['key'] == 'r_deps')
        self.assertEqual((dep['level'], dep['args']['n']), ('critical', 1))
        self.assertEqual(sum(1 for c in b['checklist'] if c['key'] == 'k_vuln'), 1)
        self.assertEqual(b['assurance']['residual'], [])

    def test_unchecked_projects_are_a_risk(self):
        b = B.build(result([project('a', vulns=None)]), 'en')
        self.assertIn('r_unchecked', [x['key'] for x in b['risks']])
        self.assertFalse(b['assurance']['safe_now'])

    def test_effort_and_schedule(self):
        work = [{'kind': 'runtime_declarations', 'count': 2, 'size': 'S'},
                {'kind': 'regression_test', 'count': 1, 'size': 'S'}]
        b = B.build(result([project('a', vulns=[], work=work)], today='2026-10-23'), 'en')   # a Friday
        self.assertEqual(b['effort']['hours'], [3.0, 6.0])          # 0.5+0.25x2 + 2 ; 1+0.5x2 + 4 (small project)
        self.assertEqual(b['effort']['days'], [1, 1])
        self.assertEqual(b['schedule']['prod_from'], '2026-10-27')  # 3 working days from Friday
        self.assertEqual(b['schedule']['prod_to'], '2026-10-28')
        work[1:1] = []
        big = project('a', vulns=[], work=work)
        big['files_scanned'] = 200
        self.assertEqual(B.build(result([big], today='2026-10-23'), 'en')['effort']['hours'], [5.0, 10.0])

    def test_workdays(self):
        self.assertEqual(B._workdays(datetime.date(2026, 10, 24), 1), datetime.date(2026, 10, 26))   # Saturday
        self.assertEqual(B._workdays(datetime.date(2026, 10, 26), 5), datetime.date(2026, 10, 30))

    def test_target_recommendation_and_rendering(self):
        res = result([project('reset', vulns=[], decls=[LAMBDA])])
        b = B.build(res, 'vi')
        self.assertEqual(b['final_target'], '24')
        self.assertIn('Runtime: nodejs24.x', [c['args'].get('y') for c in b['checklist'] if c['key'] == 'k_decl'])
        up, _ = B.upgrade_lines(res, b, 'vi')
        self.assertIn('Khuyến nghị: Node.js 24', up[1])
        md = B.md_section(res, b, 'vi', RP.md)
        self.assertIn('### 5. Quét xong thì có đảm bảo an toàn không?', md)
        self.assertIn('được hỗ trợ đến 2028-04-30', md)
        page = B.html_section(res, b, 'en')
        self.assertIn('Answers for the customer', page)
        self.assertNotIn('<script', page)

    def test_json_form(self):
        j = B.to_json(B.build(result([project('a', vulns=[])]), 'en'))
        self.assertEqual(sorted(j), ['ask', 'assurance', 'checklist', 'effort', 'final_target', 'risks', 'schedule',
                                     'schedule_window'])


class LambdaRepoShapeTest(unittest.TestCase):
    """CR-03: a Lambda repository without IaC (deploy.sh + aws lambda update-function-code), a Next.js static export,
    credentials in NEXT_PUBLIC_*, indirect vulnerabilities, a gitignored serverless.yml (shape of a real Lambda case)."""

    def setUp(self):
        import json as J
        import tempfile
        self.tmp = tempfile.mkdtemp()
        r = self.root = os.path.join(self.tmp, 'repo')
        for d in ('backend/verify/src', 'frontend/src'):
            os.makedirs(os.path.join(r, d))
        open(os.path.join(r, 'backend/.gitignore'), 'w').write('node_modules\nserverless.yml\n')
        open(os.path.join(r, 'backend/verify/deploy.sh'), 'w').write(
            'STAGE=$1\nif [ "$STAGE" == "dev" ]; then\n  FUNCTION_NAME="dev_verify"\nelse\n  FUNCTION_NAME="prod_verify"\nfi\n'
            'npm install\nzip -r f.zip .\naws lambda update-function-code --function-name "$FUNCTION_NAME" '
            '--zip-file fileb://f.zip --region ap-northeast-1\n')
        J.dump({'name': 'verify', 'dependencies': {'axios': '^1.7.9', 'aws-sdk': '^2.1692.0'}},
               open(os.path.join(r, 'backend/verify/package.json'), 'w'))
        J.dump({'lockfileVersion': 3, 'packages': {
            '': {'dependencies': {'axios': '^1.7.9', 'aws-sdk': '^2.1692.0'}},
            'node_modules/axios': {'version': '1.7.9', 'dependencies': {'form-data': '^4.0.0', 'follow-redirects': '^1'}},
            'node_modules/form-data': {'version': '4.0.1'}, 'node_modules/follow-redirects': {'version': '1.15.9'},
            'node_modules/aws-sdk': {'version': '2.1692.0', 'dependencies': {'uuid': '8.0.0'}},
            'node_modules/uuid': {'version': '8.0.0'}}}, open(os.path.join(r, 'backend/verify/package-lock.json'), 'w'))
        open(os.path.join(r, 'backend/verify/src/db.js'), 'w').write(
            "const AWS = require('aws-sdk');\nconst db = new AWS.DynamoDB.DocumentClient();\n"
            "const ses = new AWS.SES();\nexports.get = (k) => db.get({TableName: process.env.USER_INFO_TABLE, Key: k}).promise();\n")
        open(os.path.join(r, 'frontend/next.config.ts'), 'w').write('export default { output: "export" };\n')
        open(os.path.join(r, 'frontend/deploy.sh'), 'w').write('npm run build\naws s3 sync out s3://$B --delete\nB=prod-front\n')
        open(os.path.join(r, 'frontend/src/api.ts'), 'w').write(
            'const p = process.env.NEXT_PUBLIC_API_PASSWORD || "admin";\nconst u = process.env.NEXT_PUBLIC_API_URL;\n')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_deploy_info(self):
        from qplib.compat import project as P
        v = P.deploy_info(os.path.join(self.root, 'backend/verify'))
        self.assertEqual((v['kind'], v['functions'], v['region'], v['npm_install']),
                         ('lambda', ['dev_verify', 'prod_verify'], 'ap-northeast-1', True))
        f = P.deploy_info(os.path.join(self.root, 'frontend'))
        self.assertEqual((f['kind'], f['static_export']), ('static_site', True))

    def test_code_facts_and_parents(self):
        from qplib.compat import project as P
        d = os.path.join(self.root, 'backend/verify')
        c = P.code_facts(d, [os.path.join(d, 'src/db.js')])
        self.assertEqual([(s['service'], s['package'], len(s['sites'])) for s in c['sdk_v2_services']],
                         [('DynamoDB.DocumentClient', '@aws-sdk/lib-dynamodb', 1), ('SES', '@aws-sdk/client-ses', 1)])
        self.assertEqual((c['sdk_v2_promise_calls'], c['env_vars']), (1, ['USER_INFO_TABLE']))
        fe = os.path.join(self.root, 'frontend')
        s = P.code_facts(fe, [os.path.join(fe, 'src/api.ts')])['client_secrets']
        self.assertEqual([(x['name'], x['line']) for x in s], [('NEXT_PUBLIC_API_PASSWORD', 1)])   # API_URL is not a secret
        par = P.lock_parents(d)
        self.assertEqual((sorted(par['form-data']), sorted(par['uuid'])), (['axios'], ['aws-sdk']))
        self.assertEqual(P.ignored_iac([self.root]), [{'gitignore': 'backend/.gitignore', 'pattern': 'serverless.yml'}])

    def test_brief_without_iac(self):
        from qplib.compat import project as P
        vd = os.path.join(self.root, 'backend/verify')
        p = project('verify', vulns=[
            {'package': 'form-data', 'version': '4.0.1', 'severity': 'critical', 'advisories': ['GHSA-f'], 'dev': False,
             'fix_version': '4.0.6', 'major_bump': False, 'direct': False, 'via': ['axios']}])
        p['path'] = vd
        p['deploy'] = P.deploy_info(vd)
        fe = project('frontend', vulns=[
            {'package': 'next', 'version': '15.0.3', 'severity': 'critical', 'advisories': ['GHSA-n'], 'dev': False,
             'fix_version': '15.5.28', 'major_bump': False, 'direct': True, 'via': []}])
        fe['path'] = os.path.join(self.root, 'frontend')
        fe['deploy'] = P.deploy_info(fe['path'])
        fe['client_secrets'] = [{'file': 'src/api.ts', 'line': 1, 'name': 'NEXT_PUBLIC_API_PASSWORD'}]
        res = result([p, fe])
        res['ignored_iac'] = P.ignored_iac([self.root])
        res['current_branch'] = None
        b = B.build(res, 'vi')
        keys = {r['key']: r['level'] for r in b['risks']}
        self.assertEqual(keys['r_runtime_unknown'], 'high')               # runtime not in the repository
        self.assertEqual(keys['r_static'], 'medium')                      # static export: lower than critical
        self.assertEqual(keys['r_client_secret'], 'high')
        self.assertEqual(keys['r_manual_logic'], 'unassessed')
        self.assertEqual([k for k, _ in b['ask']][:3], ['ask_runtime', 'ask_iac', 'ask_gateway'])
        via = next(c for c in b['checklist'] if c['key'] == 'k_vuln_via')
        self.assertEqual(via['args']['via'], 'axios')
        res['current_branch'] = '18'
        b = B.build(res, 'vi')
        self.assertIn('r_lambda_deprecated', [r['key'] for r in b['risks']])
        self.assertEqual([c['args']['fn'] for c in b['checklist'] if c['key'] == 'k_fn_runtime'], ['dev_verify', 'prod_verify'])
        self.assertIn('k_npm_ci', [c['key'] for c in b['checklist']])


if __name__ == '__main__':
    unittest.main()
