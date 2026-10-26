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
        res = result([project('reset', vulns=[], decls=[LAMBDA])], today='2026-10-22')
        r = B.build(res, 'en')['risks']
        self.assertEqual((r[0]['level'], r[0]['key']), ('critical', 'r_lambda_blocked'))
        res = result([project('reset', vulns=[], decls=[LAMBDA])], today='2025-10-01')
        keys = {x['key']: x['level'] for x in B.build(res, 'en')['risks']}
        self.assertEqual(keys['r_lambda_deprecated'], 'high')

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
        self.assertEqual(b['effort']['hours'], [5.0, 10.0])         # 0.5+0.25x2 + 4 ; 1+0.5x2 + 8
        self.assertEqual(b['effort']['days'], [1, 2])
        self.assertEqual(b['schedule']['prod_from'], '2026-10-27')  # 3 working days from Friday
        self.assertEqual(b['schedule']['prod_to'], '2026-10-29')

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
        self.assertEqual(sorted(j), ['assurance', 'checklist', 'effort', 'final_target', 'risks', 'schedule',
                                     'schedule_window'])


if __name__ == '__main__':
    unittest.main()
