"""M3 unit tests: catalog validation/selection (FR-SCN-CAT-001), checklist
assembly (FR-SCN-CHK-001), applies_when, plan input checks (FR-PLAN-*)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib import catalog as C, errors, plan as PL  # noqa: E402

PACKAGED = os.path.join(ROOT, 'share', 'php-quickpatch', 'catalog')


def resum(d):
    import hashlib
    with open(os.path.join(d, 'SHA256SUMS'), 'w') as f:
        for n in C.FILES:
            with open(os.path.join(d, n), 'rb') as g:
                f.write('%s  %s\n' % (hashlib.sha256(g.read()).hexdigest(), n))


def copy_catalog(dest, version=None):
    shutil.copytree(PACKAGED, dest)
    os.unlink(os.path.join(dest, 'errors.tsv'))
    if version:
        p = os.path.join(dest, 'catalog.json')
        meta = json.load(open(p))
        meta['catalog_version'] = version
        json.dump(meta, open(p, 'w'))
        resum(dest)
    return dest


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_packaged_is_valid(self):
        v = C.check(PACKAGED)
        self.assertRegex(v, r'^\d{4}\.\d{2}\.\d{2}-\d+$')
        cat = C.Catalog(PACKAGED, v)
        self.assertEqual(len(cat.scenarios), 28)
        self.assertEqual(len(cat.items), 623)
        self.assertEqual(set(cat.playbooks), {'PB-%03d' % n for n in range(19)})

    def test_sha_mismatch_rejected(self):
        d = copy_catalog(os.path.join(self.tmp, 'c'))
        with open(os.path.join(d, 'bc_rules.json'), 'a') as f:
            f.write(' ')
        with self.assertRaises(C.CatalogError) as cm:
            C.check(d)
        self.assertEqual(cm.exception.code, 'ERR-FEED-422-02')

    def test_schema_rejected(self):
        d = copy_catalog(os.path.join(self.tmp, 'c'))
        p = os.path.join(d, 'checklists.json')
        doc = json.load(open(p))
        del doc['items'][0]['done_criteria']
        json.dump(doc, open(p, 'w'))
        resum(d)
        with self.assertRaises(C.CatalogError) as cm:
            C.check(d)
        self.assertEqual(cm.exception.code, 'ERR-FEED-502-02')

    def test_select_newest_valid(self):
        sd = self.tmp
        os.makedirs(os.path.join(sd, 'feeds'))
        copy_catalog(os.path.join(sd, 'feeds', 'catalog'), '2099.01.02-1')
        warnings = []
        self.assertEqual(C.select(sd, warnings).version, '2099.01.02-1')
        copy_catalog(os.path.join(self.tmp, 'old'), '2000.01.01-1')
        shutil.rmtree(os.path.join(sd, 'feeds', 'catalog'))
        shutil.copytree(os.path.join(self.tmp, 'old'), os.path.join(sd, 'feeds', 'catalog'))
        self.assertEqual(C.select(sd, warnings).version, C.check(PACKAGED))
        self.assertEqual(warnings, [])

    def test_install_imported(self):
        feeds = os.path.join(self.tmp, 'feeds')
        os.makedirs(feeds)
        src = copy_catalog(os.path.join(self.tmp, 'snap'), '2099.03.01-1')
        w = []
        self.assertEqual(C.install_imported(src, feeds, w), '2099.03.01-1')
        self.assertEqual(C.check(os.path.join(feeds, 'catalog')), '2099.03.01-1')
        older = copy_catalog(os.path.join(self.tmp, 'snap2'), '2099.02.01-1')
        self.assertIsNone(C.install_imported(older, feeds, w))
        bad = copy_catalog(os.path.join(self.tmp, 'snap3'), '2099.04.01-1')
        with open(os.path.join(bad, 'scenarios.json'), 'a') as f:
            f.write('x')
        self.assertIsNone(C.install_imported(bad, feeds, w))
        self.assertEqual(w[0][0], 'ERR-FEED-422-02')
        self.assertEqual(C.check(os.path.join(feeds, 'catalog')), '2099.03.01-1')

    def test_snapshot_files(self):
        files = C.files_for_snapshot()
        self.assertEqual(sorted(files), sorted('catalog/' + n for n in C.FILES + ['SHA256SUMS']))


def site(sid, root, kind='nginx_fastcgi', pb='PB-005'):
    return {'site_id': sid, 'docroot': root, 'binding_kind': kind, 'pb_id': pb, 'owner_user': 'www-data'}


class AssembleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = C.Catalog(PACKAGED, C.check(PACKAGED))

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.a = os.path.join(self.tmp, 'a')
        self.b = os.path.join(self.tmp, 'b')
        os.makedirs(os.path.join(self.a, 'wp-includes'))
        os.makedirs(self.b)
        open(os.path.join(self.a, 'wp-includes', 'version.php'), 'w').close()
        open(os.path.join(self.b, 'composer.json'), 'w').close()
        self.rt = {'runtime_id': 'php:aaaaaaaaaaaa', 'kind': 'php', 'bin': '/usr/bin/php8.4',
                   'scenario_ids': ['SCN-PHP-012', 'SCN-PHP-015']}
        self.scan = {'result': {'environment': {'restrictions': []}, 'wordpress_findings': []}}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def items(self, mode='cross_branch', sites=None, rt=None):
        sites = [site('a.test', self.a), site('b.test', self.b)] if sites is None else sites
        return PL.assemble(self.cat, rt or self.rt, sites, mode, {'branch': '8.5'}, self.scan, '8.4')

    def test_overlay_first_in_each_phase(self):
        its = self.items()
        for ph in PL.PHASES:
            kinds = [i['scenario_id'] for i in its if i['phase'] == ph]
            if 'SCN-PHP-015' in kinds and 'SCN-PHP-012' in kinds:
                self.assertLess(max(n for n, k in enumerate(kinds) if k == 'SCN-PHP-015'),
                                min(n for n, k in enumerate(kinds) if k == 'SCN-PHP-012'), ph)

    def test_expand_and_substitute(self):
        its = self.items()
        subs = sorted({i['chk_id'] for i in its if i['chk_id'].startswith('CHK-PHP-012-11-')})
        self.assertEqual(len(subs), len(self.cat.item('CHK-PHP-012-11')['refs']))
        self.assertTrue(all('$NEW' not in i['action'] and '$OLD ' not in i['check_mechanism'] for i in its))
        self.assertFalse(any(i['chk_id'] == 'CHK-PHP-012-11' for i in its))

    def test_same_branch_skips_upgrade_steps(self):
        its = self.items('same_branch')
        up = [i for i in its if i['flow'] == 'upgrade']
        self.assertTrue(up)
        self.assertEqual({i['status'] for i in up}, {'SKIPPED'})
        self.assertFalse(any(i['chk_id'].startswith('CHK-PHP-012-11-') for i in its))

    def test_per_site_keys_and_depends(self):
        its = self.items()
        p5 = [i for i in its if i['phase'] == 'P5']
        self.assertEqual(sorted({i['site_id'] for i in p5}), ['a.test', 'b.test'])
        keys = [i['item_key'] for i in its]
        self.assertEqual(len(keys), len(set(keys)))
        for i in p5:
            deps = [d for d in its if d['item_key'] in i['depends_on']]
            self.assertTrue(deps)
            self.assertTrue(all(d['phase'] in ('P3', 'P4') and d['site_id'] in (i['site_id'], None) for d in deps))

    def test_no_site(self):
        its = self.items(sites=[])
        p5 = [i for i in its if i['phase'] == 'P5']
        self.assertTrue(p5 and all(i['status'] == 'SKIPPED' and i['site_id'] is None for i in p5))

    def test_pb000_site_manual(self):
        its = self.items(sites=[site('legacy.test', None, 'unmapped', 'PB-000')])
        self.assertEqual({i['exec_type'] for i in its if i['site_id'] == 'legacy.test'}, {'MANUAL'})

    def test_restrictions_add_manual_items(self):
        self.scan['result']['environment']['restrictions'] = [{'code': 'SCN-ENV-NOROOT', 'message': 'not root'}]
        its = self.items()
        env = [i for i in its if i['scenario_id'] == 'SCN-ENV']
        self.assertEqual([(i['chk_id'], i['exec_type']) for i in env], [('CHK-PHP-000-01', 'MANUAL')])

    def test_applies_when(self):
        fa = PL.site_facts(site('a.test', self.a), self.scan)
        fb = PL.site_facts(site('b.test', self.b), self.scan)
        ctx = {'mode': 'cross_branch', 'old_branch': '8.4', 'scenario_ids': ['SCN-PHP-015']}
        self.assertIs(PL.applies('framework=wordpress', [fa], ctx), True)
        self.assertIs(PL.applies('framework=wordpress', [fb], ctx), False)
        self.assertIs(PL.applies('framework!=none', [fb], ctx), None)       # other frameworks: M4
        self.assertIs(PL.applies('composer=true', [fb], ctx), True)
        self.assertIs(PL.applies('composer=true', [fa], ctx), False)
        self.assertIs(PL.applies('loader!=none', [fa], ctx), None)
        self.assertIs(PL.applies('mode=cross_branch;overlay=SCN-PHP-015', [], ctx), True)
        self.assertIs(PL.applies('old_branch=5.3', [], ctx), False)
        self.assertIs(PL.applies('sapi=mod_php', [PL.site_facts(site('m', None, 'apache_mod_php'), self.scan)], ctx), True)


class InputTest(unittest.TestCase):
    def test_reason_bounds(self):
        self.assertEqual(PL.reason_ok('x' * 20, 20), 'x' * 20)
        for bad in (None, 'x' * 19, 'x' * 501, 'line\nbreak and more than twenty'):
            with self.assertRaises(errors.QPError) as cm:
                PL.reason_ok(bad, 20)
            self.assertEqual(cm.exception.code, 'ERR-PLAN-422-01')

    def test_deadline(self):
        cur = {'eol_date': '2026-12-31', 'days_to_eol': 70, 'lifecycle_status': 'SECURITY_ONLY'}
        self.assertEqual(PL.deadline_of(cur, '2026-10-22', 'draft'),
                         {'date': '2026-12-01', 'days_left': 40, 'overdue': False, 'warn': True})
        node22 = {'eol_date': '2027-04-30', 'days_to_eol': 190, 'lifecycle_status': 'MAINTENANCE_LTS'}
        self.assertEqual(PL.deadline_of(node22, '2026-10-22', 'draft')['date'], '2027-03-31')
        active = {'eol_date': '2029-12-31', 'days_to_eol': 1166, 'lifecycle_status': 'ACTIVE'}
        self.assertIsNone(PL.deadline_of(active, '2026-10-22', 'draft'))
        late = PL.deadline_of(cur, '2026-12-10', 'draft')
        self.assertTrue(late['overdue'])
        self.assertFalse(PL.deadline_of(cur, '2026-12-10', 'approved')['overdue'])


if __name__ == '__main__':
    unittest.main()
