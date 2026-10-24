"""Feeds: version matching (DOC-SRS-QP-FEED-002 §5), risk score (§8), merge rules (§4, §6)."""
import json
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARE = os.path.join(ROOT, 'share', 'php-quickpatch')
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'feeds')
sys.path.insert(0, SHARE)

from qplib.feeds import normalize, risk, versions as V  # noqa: E402
from qplib.feeds.collect import nvd_advisory  # noqa: E402


def nvd_cve(cve_id):
    for q in ('php-q1', 'php-q2', 'node-q1', 'wordpress-q1'):
        with open(os.path.join(FIX, 'SRC-004', q + '.json')) as f:
            for v in json.load(f)['vulnerabilities']:
                if v['cve']['id'] == cve_id:
                    return v['cve']
    raise KeyError(cve_id)


class Versions(unittest.TestCase):
    def test_compare_like_sort_v(self):
        self.assertTrue(V.vlt('8.4.9', '8.4.10'))
        self.assertEqual(V.vcmp('8.4', '8.4.0'), 0)
        self.assertEqual(V.vmax(['22.9.0', '22.23.4', '22.23.3']), '22.23.4')
        self.assertEqual(V.branch_of('node', '0.12.18'), '0.12')
        self.assertEqual(V.branch_of('php', '8.4.27'), '8.4')

    def test_semver_node_wg(self):
        """§5.4: affected <=> matches `vulnerable` and not `patched`."""
        alts = V.parse_semver('^22.0.0 || ^24.0.0 || 20.x')
        self.assertTrue(V.semver_satisfies('22.23.3', alts))
        self.assertTrue(V.semver_satisfies('20.1.0', alts))
        self.assertFalse(V.semver_satisfies('23.0.0', alts))
        self.assertTrue(V.semver_satisfies('22.23.2', V.parse_semver('^22.23.2')))
        self.assertFalse(V.semver_satisfies('22.23.1', V.parse_semver('^22.23.2')))
        self.assertFalse(V.semver_satisfies('22.24.0', V.parse_semver('~22.23.2')))
        self.assertTrue(V.semver_satisfies('18.5.0', V.parse_semver('>=18.0.0 <18.19.1')))
        self.assertTrue(V.semver_satisfies('12.0.0', V.parse_semver('10.0.0 - 12.1.0')))
        with self.assertRaises(V.SemverError):
            V.parse_semver('not a range')

    def test_cpe_and_platform(self):
        """§5.1: AND node with only Windows CPEs -> platform windows (CVE-2024-4577)."""
        cve = nvd_cve('CVE-2024-4577')
        ranges = V.nvd_ranges(cve['configurations'], 'php')
        self.assertTrue(ranges)
        self.assertEqual({r['platform'] for r in ranges}, {'windows'})
        adv = nvd_advisory(cve, 'php')
        self.assertEqual(normalize.selected_ranges(adv['ranges'], 'php'), [])   # Linux: no NVD_CPE range applies

    def test_cpe_na_and_unbounded(self):
        na = {'criteria': 'cpe:2.3:a:php:php:-:*:*:*:*:*:*:*', 'vulnerable': True}
        self.assertIsNone(V.cpe_match_to_range(na))
        star = V.cpe_match_to_range({'criteria': 'cpe:2.3:a:php:php:*:*:*:*:*:*:*:*', 'vulnerable': True})
        self.assertEqual(star['unbounded'], 1)
        self.assertFalse(V.in_range('8.4.1', star))
        exact = V.cpe_match_to_range({'criteria': 'cpe:2.3:a:php:php:8.4.1:*:*:*:*:*:*:*', 'vulnerable': True})
        self.assertTrue(V.in_range('8.4.1', exact))
        self.assertFalse(V.in_range('8.4.2', exact))

    def test_cna_prefix(self):
        """§5.2: `8.4.*` + lessThan 8.4.27 only matches the 8.4 branch."""
        r = V.cna_ranges([{'product': 'PHP', 'versions': [{'version': '8.4.*', 'lessThan': '8.4.27',
                                                            'status': 'affected'}]}], {'php'})[0]
        self.assertTrue(V.cna_match('8.4.26', r))
        self.assertFalse(V.cna_match('8.4.27', r))
        self.assertFalse(V.cna_match('8.3.30', r))

    def test_osv_events(self):
        rs = V.osv_ranges({'ranges': [{'type': 'ECOSYSTEM', 'events': [{'introduced': '0'}, {'fixed': '1.2.5'},
                                                                       {'introduced': '2.0.0'},
                                                                       {'last_affected': '2.0.3'}]}],
                           'versions': ['3.0.0']})
        hit = lambda v: any(V.in_range(v, r) for r in rs)  # noqa: E731
        self.assertTrue(hit('1.2.4'))
        self.assertFalse(hit('1.2.5'))
        self.assertTrue(hit('2.0.3'))
        self.assertFalse(hit('2.0.4'))
        self.assertTrue(hit('3.0.0'))


class Risk(unittest.TestCase):
    """§8.5 examples 1-11 and the rounding cases RT-1, RT-2 of §8.2.1 (NFR-MNT-002)."""
    CASES = [  # status, d, C, H, M, L, KEV, cvss10, R, level
        ('ACTIVE', 1166, 0, 0, 0, 0, 0, 0, 0, 'LOW'),
        ('ACTIVE', 801, 2, 0, 0, 0, 0, 98, 47, 'HIGH'),
        ('SECURITY_ONLY', 70, 2, 0, 0, 0, 0, 98, 60, 'HIGH'),
        ('SECURITY_ONLY', 70, 0, 0, 0, 0, 0, 0, 40, 'HIGH'),
        ('SECURITY_ONLY', 435, 9, 15, 21, 3, 0, 98, 64, 'HIGH'),
        ('SECURITY_ONLY', 435, 0, 0, 1, 0, 0, 69, 33, 'MEDIUM'),
        ('EOL', -1424, 2, 0, 2, 0, 0, 98, 70, 'CRITICAL'),
        ('MAINTENANCE_LTS', 190, 0, 1, 0, 0, 0, 75, 40, 'HIGH'),
        ('MAINTENANCE_LTS', 190, 0, 3, 3, 1, 0, 80, 47, 'HIGH'),
        ('EOL', -175, 0, 0, 0, 0, 0, 0, 40, 'HIGH'),
        ('SECURITY_ONLY', None, 1, 1, 1, 0, 3, 98, 71, 'CRITICAL'),
        ('SECURITY_ONLY', None, 0, 1, 0, 0, 1, 81, 70, 'CRITICAL'),
        ('ACTIVE', 500, 0, 0, 1, 0, 0, 50, 21, 'MEDIUM'),          # RT-1: 20.5 -> 21 (round() gives 20)
        ('SECURITY_ONLY', 120, 0, 0, 5, 0, 0, 60, 37, 'MEDIUM'),   # RT-2: 36.5 -> 37 (round() gives 36)
    ]

    def test_examples(self):
        for st, d, c, h, m, l, k, c10, want_r, want_lvl in self.CASES:
            res = risk.score(st, d, c, h, m, l, k, c10)
            self.assertEqual((res['R'], res['level']), (want_r, want_lvl), (st, d, res))

    def test_components_are_tenths(self):
        res = risk.score('SECURITY_ONLY', 70, 2, 0, 0, 0, 0, 98)
        self.assertEqual(res['components'], {'S_cvss': 39.2, 'S_cnt': 8.0, 'S_kev': 0.0, 'S_life': 5.0,
                                             'S_eol': 8.0, 'floor': 40, 'R_raw': 60.2})
        self.assertEqual(json.dumps(res['components']['S_cnt']), '8.0')

    def test_levels(self):
        self.assertEqual([risk.level(r) for r in (0, 19, 20, 39, 40, 69, 70, 100)],
                         ['LOW', 'LOW', 'MEDIUM', 'MEDIUM', 'HIGH', 'HIGH', 'CRITICAL', 'CRITICAL'])

    def test_lifecycle_status(self):
        php = {'branch': '8.2', 'ga_date': '2022-12-08', 'active_support_end': '2024-12-31',
               'eol_date': '2026-12-31', 'php_net_supported': 1}
        self.assertEqual(risk.lifecycle_status('php', php, '8.2.34', '2026-10-24'), 'SECURITY_ONLY')
        self.assertEqual(risk.lifecycle_status('php', php, '8.2.34', '2027-01-05'), 'SECURITY_ONLY')  # BR-FEED-020
        self.assertEqual(risk.lifecycle_status('php', dict(php, php_net_supported=0), '8.2.34', '2027-01-05'), 'EOL')
        self.assertEqual(risk.lifecycle_status('php', php, '8.6.0RC1', '2026-10-24'), 'PRE_RELEASE')
        self.assertEqual(risk.lifecycle_status('php', None, '9.0.0', '2026-10-24'), 'UNKNOWN')
        node = {'branch': '24', 'ga_date': '2025-05-06', 'lts_start': '2025-10-28', 'active_support_end': '2026-10-20',
                'eol_date': '2028-04-30'}
        self.assertEqual(risk.lifecycle_status('node', node, '24.22.1', '2026-10-24'), 'MAINTENANCE_LTS')
        self.assertEqual(risk.lifecycle_status('node', node, '24.22.1', '2026-01-01'), 'ACTIVE_LTS')
        self.assertEqual(risk.lifecycle_status('node', node, '24.1.0', '2025-06-01'), 'CURRENT')
        wp = {'branch': '7.0', 'eol_date': None}
        self.assertEqual(risk.lifecycle_status('wordpress', wp, '7.0.1', '2026-10-24',
                                               {'newest_branch': '7.1', 'has_supported': True}), 'SECURITY_ONLY')
        self.assertEqual(risk.lifecycle_status('wordpress', wp, '7.0.1', '2026-10-24',
                                               {'newest_branch': '7.0'}), 'ACTIVE')
        self.assertEqual(risk.lifecycle_status('wordpress', wp, '7.0.1', '2026-10-24',
                                               {'min_patched': 'NONE'}), 'EOL')

    def test_priority_floor(self):
        self.assertEqual(risk.priority('UNKNOWN', None, 0, 0), 'CRITICAL')
        self.assertEqual(risk.priority('EOL', -400, 0, 0), 'CRITICAL')
        self.assertEqual(risk.priority('ACTIVE', 800, 1, 0), 'CRITICAL')
        self.assertEqual(risk.priority('ACTIVE', 800, 0, 70), 'HIGH')
        self.assertEqual(risk.priority('ACTIVE', 300, 0, 0), 'MEDIUM')
        self.assertEqual(risk.priority('ACTIVE', 800, 0, 69), 'LOW')


def adv(adv_id, product='php', scores=(), ranges=(), aliases=(), status='PUBLISHED', src='SRC-004'):
    return src, {'type': 'advisory', 'adv_id': adv_id, 'products': [product], 'kind': 'VULN', 'status': status,
                 'published_at': '2026-10-21T00:00:00Z', 'modified_at': '2026-10-21T00:00:00Z', 'summary': 's',
                 'cwe_ids': None, 'workaround': None, 'aliases': list(aliases), 'scores': list(scores),
                 'ranges': list(ranges)}


def rng(product, start, end, origin='NVD_CPE', end_incl=0):
    return {'product': product, 'origin': origin, 'v_start': start, 'start_incl': 1, 'v_end': end,
            'end_incl': end_incl, 'v_exact': None, 'unbounded': 0, 'platform': 'any'}


def score(source, ver, base, typ=None, text=None):
    return {'source': source, 'cvss_version': ver, 'type': typ, 'base_score': base, 'vector': None,
            'severity_text': text}


def rel(product, version, sec=0, date='2026-01-01', wp=None):
    return {'type': 'release', 'product': product, 'branch': V.branch_of(product, version), 'version': version,
            'release_date': date, 'is_security': sec, 'wp_status': wp, 'abi_modules': None, 'lts_codename': None}


def lc(product, branch, ga='2024-01-01', eol='2030-01-01'):
    return {'type': 'lifecycle', 'product': product, 'branch': branch, 'ga_date': ga, 'lts_start': None,
            'active_support_end': None, 'eol_date': eol, 'prerelease_date': None, 'php_net_supported': None,
            'origin': 'SRC-001', 'latest_hint': None}


class Merge(unittest.TestCase):
    NOW = time.mktime((2026, 10, 24, 12, 0, 0, 0, 0, 0))

    def build(self, advs, releases, lifecycles, extra=None, now=None):
        by = {}
        for src, f in advs:
            by.setdefault(src, []).append(f)
        by.setdefault('SRC-002', []).extend(r for r in releases if r['product'] == 'php')
        by.setdefault('SRC-009', []).extend(r for r in releases if r['product'] == 'node')
        by.setdefault('SRC-012', []).extend(r for r in releases if r['product'] == 'wordpress')
        by.setdefault('SRC-001', []).extend(lifecycles)
        for k, v in (extra or {}).items():
            by.setdefault(k, []).extend(v)
        m = normalize.build({k: {'facts': v} for k, v in by.items()}, today='2026-10-24', now=now or self.NOW)
        m['mp'] = {(r['product'], r['branch']): r for r in m['min_patched']}
        return m

    def test_cvss_rep_order(self):
        """BR-FEED-028: NVD Primary 3.x first, then max 3.x of others, then 4.0, then NVD 2.0, then proxy."""
        self.assertEqual(normalize.cvss_rep([score('NVD', '3.1', 8.1, 'Primary'), score('CNA:x', '3.1', 9.8, 'Secondary'),
                                             score('CNA:x', '4.0', 9.2, 'Secondary')], 'VULN'), (8.1, 'NVD:3.1:Primary'))
        self.assertEqual(normalize.cvss_rep([score('CNA:x', '3.1', 7.5, 'Secondary'), score('GHSA', '3.1', 8.8)], 'VULN')[0], 8.8)
        self.assertEqual(normalize.cvss_rep([score('CNA:x', '4.0', 9.2, 'Secondary'), score('NVD', '2.0', 5.0)], 'VULN')[0], 9.2)
        self.assertEqual(normalize.cvss_rep([score('NVD', '2.0', 5.0, 'Primary')], 'VULN')[0], 5.0)
        self.assertEqual(normalize.cvss_rep([score('NODE_WG', 'NONE', None, text='high')], 'VULN'), (8.0, 'PROXY:high'))
        self.assertEqual(normalize.cvss_rep([], 'SEC_RELEASE'), (7.5, 'PROXY:sec_release'))
        self.assertEqual(normalize.cvss_rep([], 'VULN'), (None, None))

    def test_fixed_max_and_min_patched(self):
        """BR-FEED-027 (CVE-2025-1861 shape): NVD 8.2.26, CNA 8.2.28, ChangeLog 8.2.28 -> 8.2.28 + ERR-FEED-409-01."""
        rels = [rel('php', '8.2.%d' % i) for i in range(24, 30)]
        a = adv('CVE-2025-1861', scores=[score('NVD', '3.1', 9.1, 'Primary')],
                ranges=[rng('php', '8.2.0', '8.2.26'), rng('php', '8.2.0', '8.2.28', 'CNA')])
        m = self.build([a], rels, [lc('php', '8.2')],
                       {'SRC-003': [{'type': 'fix', 'adv_id': 'CVE-2025-1861', 'product': 'php', 'version': '8.2.28'}]})
        mp = m['mp'][('php', '8.2')]
        self.assertEqual(mp['min_patched_sec'], '8.2.28')
        self.assertEqual(mp['driver_ids'], ['CVE-2025-1861'])
        self.assertTrue(any('CVE-2025-1861' in c['message'] for c in m['conflicts']))

    def test_none_and_pending(self):
        rels = [rel('php', '8.3.%d' % i) for i in (1, 2, 3)]
        pend = adv('CVE-1', scores=[score('NVD', '3.1', 9.8, 'Primary')], ranges=[rng('php', '8.3.0', '8.3.4')])
        m = self.build([pend], rels, [lc('php', '8.3')])
        self.assertEqual(m['mp'][('php', '8.3')]['min_patched_sec'], 'PENDING_RELEASE')
        none = adv('CVE-2', scores=[score('NVD', '3.1', 9.8, 'Primary')], ranges=[rng('php', '8.0.0', '9.0.0')])
        m = self.build([none], rels, [lc('php', '8.3')])
        self.assertEqual(m['mp'][('php', '8.3')]['min_patched_sec'], 'NONE')
        low = adv('CVE-3', scores=[score('NVD', '3.1', 5.0, 'Primary')], ranges=[rng('php', '8.3.0', '8.3.3')])
        m = self.build([low], rels, [lc('php', '8.3')])
        self.assertEqual(m['mp'][('php', '8.3')]['min_patched_sec'], '8.3.1')    # not in S_sec -> GA version
        self.assertEqual(m['mp'][('php', '8.3')]['min_patched_all'], '8.3.3')

    def test_dedup_aliases_and_malware(self):
        """BR-FEED-023: GHSA record merges into the CVE; MAL-* never merges."""
        cve = adv('CVE-2026-1', scores=[score('NVD', '3.1', 7.0, 'Primary')], aliases=['GHSA-aaaa-bbbb-cccc'])
        ghsa = adv('GHSA-aaaa-bbbb-cccc', scores=[score('GHSA', '3.1', 9.0)], src='SRC-008')
        mal = adv('MAL-2026-1', aliases=['CVE-2026-1'], src='SRC-008')
        m = self.build([cve, ghsa, mal], [], [lc('php', '8.4')])
        ids = sorted(a['adv_id'] for a in m['advisories'])
        self.assertEqual(ids, ['CVE-2026-1', 'MAL-2026-1'])
        merged = [a for a in m['advisories'] if a['adv_id'] == 'CVE-2026-1'][0]
        self.assertEqual(merged['cvss_rep'], '7.0')          # NVD Primary wins (BR-FEED-028)
        self.assertIn(('CVE-2026-1', 'GHSA-aaaa-bbbb-cccc'), m['aliases'])
        self.assertEqual([a['kind'] for a in m['advisories'] if a['adv_id'] == 'MAL-2026-1'], ['MALWARE'])

    def test_rejected_excluded(self):
        """BR-FEED-031."""
        rels = [rel('php', '8.4.%d' % i) for i in (1, 2)]
        r = adv('CVE-9', scores=[score('NVD', '3.1', 9.8, 'Primary')], ranges=[rng('php', '8.4.0', '8.4.2')],
                status='REJECTED')
        m = self.build([r], rels, [lc('php', '8.4')])
        self.assertEqual(m['mp'][('php', '8.4')]['min_patched_sec'], '8.4.1')
        self.assertEqual([e['n_crit'] for e in m['exposure']], [0, 0])

    def test_kev_via_alias(self):
        a = adv('CVE-2026-7', scores=[score('NVD', '3.1', 6.0, 'Primary')], ranges=[rng('php', '8.4.0', '8.4.2')])
        kev = {'type': 'kev', 'cve_id': 'CVE-2026-7', 'date_added': '2026-10-01', 'due_date': '2026-10-22',
               'ransomware': 'Unknown'}
        m = self.build([a], [rel('php', '8.4.1'), rel('php', '8.4.2')], [lc('php', '8.4')], {'SRC-006': [kev]})
        self.assertEqual(m['advisories'][0]['in_kev'], 1)
        self.assertEqual(m['mp'][('php', '8.4')]['min_patched_sec'], '8.4.2')    # KEV -> in S_sec although medium
        self.assertEqual(m['exposure'][0]['n_kev'], 1)

    def test_temporary_advisory(self):
        """BR-FEED-024: a security release without CVE data gets QP-SR-* after 6 h; a real fix removes it."""
        rels = [rel('node', '22.23.3', 0), rel('node', '22.23.4', 1, date='2026-10-24')]
        m = self.build([], rels, [lc('node', '22')], now=time.mktime((2026, 10, 24, 3, 0, 0, 0, 0, 0)) - time.timezone)
        self.assertEqual([a['adv_id'] for a in m['advisories']], [])                       # < 6 h
        m = self.build([], rels, [lc('node', '22')])
        self.assertEqual([a['adv_id'] for a in m['advisories']], ['QP-SR-node-22.23.4'])
        self.assertEqual(m['mp'][('node', '22')]['min_patched_sec'], '22.23.4')
        self.assertEqual(m['advisories'][0]['cvss_rep'], '7.5')
        real = adv('CVE-2026-50', 'node', scores=[score('NVD', '3.1', 7.5, 'Primary')],
                   ranges=[{'product': 'node', 'origin': 'NODE_WG', 'semver_vulnerable': '>=22.0.0 <22.23.4',
                            'semver_patched': '^22.23.4', 'platform': 'any'}], src='SRC-011')
        m = self.build([real], rels, [lc('node', '22')])
        self.assertEqual([a['adv_id'] for a in m['advisories']], ['CVE-2026-50'])

    def test_wordpress_min_patched(self):
        """BR-FEED-025: smallest version of the branch that is not insecure; none -> NONE."""
        rels = [rel('wordpress', '7.0.1', wp='insecure'), rel('wordpress', '7.0.7', wp='outdated'),
                rel('wordpress', '7.1.3', wp='latest'), rel('wordpress', '4.1.42', wp='insecure')]
        m = self.build([], rels, [lc('wordpress', '7.0'), lc('wordpress', '7.1'), lc('wordpress', '4.1')])
        got = {r['branch']: r['min_patched_sec'] for r in m['min_patched'] if r['product'] == 'wordpress'}
        self.assertEqual(got, {'4.1': 'NONE', '7.0': '7.0.7', '7.1': '7.1.3'})

    def test_lifecycle_priority_conflict(self):
        """§4.1 Node.js: SRC-010 before SRC-001; > 3 days apart -> ERR-FEED-409-01."""
        a = lc('node', '26', eol='2029-04-30')
        a['active_support_end'] = '2027-10-27'
        b = dict(lc('node', '26', eol='2029-04-30'), origin='SRC-010', active_support_end='2027-10-20')
        m = normalize.build({'SRC-001': {'facts': [a]}, 'SRC-010': {'facts': [b]}}, today='2026-10-24', now=self.NOW)
        self.assertEqual([r['active_support_end'] for r in m['lifecycle'] if r['product'] == 'node'], ['2027-10-20'])
        self.assertEqual(len(m['conflicts']), 1)


if __name__ == '__main__':
    unittest.main()
