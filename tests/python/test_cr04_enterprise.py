"""CR-04 unit tests: the two enterprise documents built from a compat result (qplib/compat/enterprise.py, docs.py)."""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qplib import errors  # noqa: E402
from qplib.compat import docs as D, enterprise as E  # noqa: E402
from test_cr02_brief import LAMBDA, project, result  # noqa: E402


def vuln(pkg, ver, sev, fix, dev=False, direct=True, via=None, adv='GHSA-xxxx-yyyy-zzzz'):
    return {'package': pkg, 'version': ver, 'severity': sev, 'advisories': [adv], 'dev': dev, 'fix_version': fix,
            'major_bump': False, 'direct': direct, 'via': via or [], 'in_kev': False, 'unfixed_advisories': [],
            'by_advisory': {adv: {'severity': sev, 'summary': '%s issue <b>bold</b>' % pkg,
                                  'aliases': ['CVE-2026-0001'], 'fixed': [fix]}}}


def sample(today='2026-10-26'):
    api = project('api', vulns=[vuln('form-data', '4.0.1', 'critical', '4.0.6', direct=False, via=['axios']),
                                vuln('axios', '1.7.9', 'high', '1.20.0'),
                                vuln('glob', '10.4.5', 'high', '10.5.0', dev=True)],
                  decls=[LAMBDA], deprecated=[
                      {'package': 'request', 'version': '2.88.2', 'source': 'npm', 'message': 'request has been deprecated'},
                      {'package': 'aws-sdk', 'version': '2.1692.0', 'dev': False, 'source': 'catalog',
                       'message': 'AWS SDK for JavaScript v2 end of support', 'replacement': '@aws-sdk/client-*',
                       'call_sites': [{'file': 'src/mail.js', 'line': 1}], 'promise_calls': 2,
                       'services': [{'service': 'SES', 'package': '@aws-sdk/client-ses',
                                     'sites': [{'file': 'src/mail.js', 'line': 3}]}]}],
                  work=[{'kind': 'migrate_package', 'package': 'aws-sdk', 'count': 1, 'size': 'M'},
                        {'kind': 'regression_test', 'count': 1, 'size': 'S'}])
    api['deploy'] = {'kind': 'lambda', 'functions': ['dev_api', 'prod_api'], 'region': 'ap-northeast-1',
                     'npm_install': True, 'scripts': ['deploy.sh'], 'static_export': False, 'buckets': []}
    api.update({'sdk_v2_services': [{'service': 'SES', 'package': '@aws-sdk/client-ses',
                                     'sites': [{'file': 'src/mail.js', 'line': 3, 'text': 'new AWS.SES()'}]}],
                'sdk_v2_promise_calls': 2, 'env_vars': ['TABLE'], 'client_secrets': []})
    api['has_tests'] = False
    web = project('web<img src=x onerror=alert(1)>', vulns=[])
    web['client_secrets'] = [{'file': 'src/api.ts', 'line': 4, 'name': 'NEXT_PUBLIC_API_PASSWORD'}]
    res = result([api, web], today=today, target='24', target_ok=True)
    res['lifecycle']['target'].update({'eol_date': '2028-04-30', 'days_to_eol': 552, 'lts': True})
    res['lifecycle']['branches'] = [
        {'branch': '18', 'status': 'EOL', 'eol_date': '2025-04-30', 'lts': True},
        {'branch': '22', 'status': 'MAINTENANCE_LTS', 'eol_date': '2027-04-30', 'lts': True},
        {'branch': '24', 'status': 'MAINTENANCE_LTS', 'eol_date': '2028-04-30', 'lts': True},
        {'branch': '26', 'status': 'ACTIVE_LTS', 'eol_date': '2029-04-30', 'lts': True}]
    res.update({'run_id': '20261026-080000-abcd', 'runtime': 'node', 'catalog_version': '2026.10.26-1',
                'ignored_iac': [], 'summary': {'projects': 2}})
    return res


class EnterpriseDocTest(unittest.TestCase):
    def test_security_findings_ids_severity_and_due_dates(self):
        doc = E.build('security', sample(), 'en', {'client': 'ACME', 'project': 'Portal'})
        self.assertEqual(doc['meta']['doc_id'], 'SPA-PORTAL-20261026')
        ids = [f['id'] for f in doc['findings']]
        self.assertEqual(ids, ['SEC-%02d' % i for i in range(1, len(ids) + 1)])
        sev = [f['severity'] for f in doc['findings']]
        self.assertEqual(sev, sorted(sev, key=E.SEV.index))                 # most severe first
        self.assertEqual(sev[0], 'critical')
        full = E.security_findings(sample(), 'en', E.BR.build(sample(), 'en'))
        self.assertEqual(full[0]['due'], '2026-11-02')                      # critical: 7 days
        titles = ' '.join(f['title'] for f in doc['findings'])
        self.assertIn('form-data', titles)
        self.assertIn('browser', titles.lower())                            # NEXT_PUBLIC_* credential

    def test_compat_doc_options_and_findings(self):
        doc = E.build('compatibility', sample(), 'vi', {})
        self.assertTrue(doc['meta']['doc_id'].startswith('RCA-'))
        md = E.render_md(doc)
        self.assertIn('Node.js 24 (nodejs24.x)', md)
        self.assertIn('Khuyến nghị', md)
        self.assertIn('Node.js 26 |', md)                                   # no Lambda runtime yet: no nodejs26.x
        self.assertIn('AWS Lambda chưa cung cấp runtime này', md)
        self.assertIn('aws lambda update-function-configuration --function-name prod_api --runtime nodejs24.x', md)
        titles = [f['title'] for f in doc['findings']]
        self.assertTrue(any('SDK' in x for x in titles))
        self.assertEqual(doc['findings'][0]['id'], 'CMP-01')

    def test_options_fallback_without_branch_table(self):
        res = sample()
        del res['lifecycle']['branches']
        head, rows = E._options(res, 'en', E.BR.build(res, 'en'), '2026-11-10')
        self.assertEqual([r[0] for r in rows], ['Node.js 18 (nodejs18.x)', 'Node.js 24 (nodejs24.x)'])

    def test_html_is_escaped_and_self_contained(self):
        for kind in ('security', 'compatibility'):
            for lang in ('en', 'vi'):
                h = E.render_html(E.build(kind, sample(), lang, {'client': 'A & <B>'}))
                self.assertNotIn('<script', h.lower())
                self.assertNotIn('<img', h)
                self.assertIn('web&lt;img src=x onerror=alert(1)&gt;', h)
                self.assertIn('A &amp; &lt;B&gt;', h)
                self.assertNotRegex(h, r'<link|src="http|@import')
                self.assertIn('@page', h)

    def test_markdown_tables_are_well_formed(self):
        md = E.render_md(E.build('security', sample(), 'en', {}))
        self.assertTrue(md.startswith('# Security Posture Assessment & Remediation Plan'))
        for line in md.splitlines():
            if line.startswith('| ') and not line.startswith('| ---'):
                self.assertTrue(line.endswith('|'), line)
        self.assertNotIn('<b>', md)

    def test_person_days_in_half_days(self):
        self.assertEqual(E._pd(40.4, 88.5, 'en'), '5–11 person-days')
        self.assertEqual(E._pd(1, 13, 'en'), '0.5–1.5 person-days')


class ReportCommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state = os.path.join(self.tmp, 'state')
        res = sample()
        run = os.path.join(self.state, 'reports', 'compat-' + res['run_id'])
        os.makedirs(run)
        json.dump(res, open(os.path.join(run, 'result.json'), 'w'))
        self.env_file = os.path.join(self.tmp, 'env.json')
        json.dump({'schema': 'qp.compat/1', 'result': res}, open(self.env_file, 'w'))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_cmd(self, *argv):
        sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))
        import importlib.util
        spec = importlib.util.spec_from_file_location('qpfeeds', os.path.join(ROOT, 'share', 'php-quickpatch', 'qp-feeds.py'))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return D.run(None, list(argv) + ['--json'], m.Args, [], self.state)

    def test_from_run_id_and_envelope(self):
        out = os.path.join(self.tmp, 'spa.html')
        code, r = self.run_cmd('security', '--result', '20261026-080000-abcd', '--out', out, '--client', 'ACME')
        self.assertEqual(code, 0)
        self.assertEqual(r['sha256'], hashlib.sha256(open(out, 'rb').read()).hexdigest())
        self.assertIn('ACME', open(out, encoding='utf-8').read())
        out2 = os.path.join(self.tmp, 'rca.md')
        code, r = self.run_cmd('compatibility', '--result', self.env_file, '--out', out2, '--lang', 'vi')
        self.assertEqual((code, r['format'], r['source_run_id']), (0, 'md', '20261026-080000-abcd'))

    def test_refusals(self):
        out = os.path.join(self.tmp, 'x.html')
        open(out, 'w').write('keep')
        with self.assertRaises(errors.QPError) as c:
            self.run_cmd('security', '--result', self.env_file, '--out', out)
        self.assertEqual(c.exception.code, 'ERR-RPT-409-01')
        self.assertEqual(open(out).read(), 'keep')
        with self.assertRaises(errors.QPError) as c:
            self.run_cmd('security', '--result', self.env_file, '--out', os.path.join(self.tmp, 'y.pdf'))
        self.assertEqual(c.exception.code, 'ERR-RPT-422-01')
        with self.assertRaises(errors.QPError) as c:
            self.run_cmd('security', '--result', self.env_file, '--out', os.path.join(self.tmp, 'z.md'),
                         '--client', 'bad\x1bname')
        self.assertEqual(c.exception.code, 'ERR-CLI-400-01')
        bogus = os.path.join(self.tmp, 'bogus.json')
        json.dump({'hello': 1}, open(bogus, 'w'))
        with self.assertRaises(errors.QPError):
            self.run_cmd('security', '--result', bogus, '--out', os.path.join(self.tmp, 'w.md'))
        with self.assertRaises(errors.QPError):
            self.run_cmd('summary', '--result', bogus, '--out', os.path.join(self.tmp, 'w.md'))


if __name__ == '__main__':
    unittest.main()
