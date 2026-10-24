"""Feeds sync against the local fake sources (tests/fakesrv.py): FR-FEED-SYNC-001, CACH-*, SNAP-*,
OSV-001, DIST-001, regression of DOC-SRS-QP-FEED-002 §6.5 (TC-FEED-026)."""
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARE = os.path.join(ROOT, 'share', 'php-quickpatch')
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'feeds')
sys.path.insert(0, SHARE)

from qplib import errors, jsonschema_lite  # noqa: E402
from qplib.feeds import bundle, osv, schedule, snapshot, sync  # noqa: E402
from qplib.feeds.query import Bundle  # noqa: E402
from qplib.feeds.store import FeedsDir, read_json  # noqa: E402

SRV = None
BASE = None


def setUpModule():
    global SRV, BASE
    SRV = tempfile.mkdtemp()
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, 'tests', 'fakesrv.py'), FIX, SRV],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(150):
        if os.path.exists(os.path.join(SRV, 'port')):
            break
        time.sleep(0.1)
    port = open(os.path.join(SRV, 'port')).read()
    BASE = 'https://127.0.0.1:%s' % port
    os.environ['SSL_CERT_FILE'] = os.path.join(SRV, 'ca.pem')
    for k in ('NO_PROXY', 'no_proxy'):
        os.environ[k] = '127.0.0.1,localhost'
    setUpModule.proc = proc


def tearDownModule():
    setUpModule.proc.terminate()
    shutil.rmtree(SRV, ignore_errors=True)


def control(obj):
    with open(os.path.join(SRV, 'control.json'), 'w') as f:
        json.dump(obj, f)


def requests():
    try:
        return [json.loads(line) for line in open(os.path.join(SRV, 'requests.log'))]
    except OSError:
        return []


def sources_conf(feeds_dir, extra=''):
    os.makedirs(feeds_dir, exist_ok=True)
    out = []
    for n in range(1, 16):
        s = 'SRC-%03d' % n
        url, mirror = '%s/%s' % (BASE, s), '%s/%s-mirror' % (BASE, s)
        url = {'SRC-006': BASE + '/SRC-006/kev.json', 'SRC-009': BASE + '/SRC-009/index.json',
               'SRC-010': BASE + '/SRC-010/schedule.json', 'SRC-011': BASE + '/SRC-011/index.json'}.get(s, url)
        if s == 'SRC-006':
            mirror = BASE + '/SRC-006-mirror/kev.json'
        out.append('[%s]\nurl = %s\nmirror_url = %s\nretry_delays = 0,0,0\nmin_interval_s = 0\ntimeout_s = 10\n'
                   % (s, url, mirror))
    with open(os.path.join(feeds_dir, 'sources.conf'), 'w') as f:
        f.write(''.join(out) + extra)


class Base(unittest.TestCase):
    def setUp(self):
        control({})
        open(os.path.join(SRV, 'requests.log'), 'w').close()
        self.sd = tempfile.mkdtemp()
        os.chmod(self.sd, 0o700)
        os.environ.pop('QP_FEEDS_BUNDLE', None)
        os.environ.pop('QP_SCRIPT', None)
        FeedsDir(self.sd)
        sources_conf(os.path.join(self.sd, 'feeds'))
        self.fs = FeedsDir(self.sd)

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def sync(self, **kw):
        return sync.run(self.sd, **kw)

    def status(self, src):
        return self.fs.status()['sources'][src]

    def mp(self):
        with Bundle(self.fs) as b:
            return {(r['product'], r['branch']): r for r in b.tsv('min_patched.tsv')}


class Regression(Base):
    def test_tc_feed_026_v01_data(self):
        """§6.5: the algorithm on the fixture data gives the v0.1 values (WordPress per BR-FEED-025)."""
        code, res, _ = self.sync()
        self.assertEqual(code, 1)          # SRC-008 (GitHub) answers 403 like the real API without a token
        mp = self.mp()
        for b, v in (('8.2', '8.2.35'), ('8.3', '8.3.36'), ('8.4', '8.4.27'), ('8.5', '8.5.12')):
            self.assertEqual(mp[('php', b)]['min_patched_sec'], v)
            self.assertEqual(mp[('php', b)]['driver_ids'], 'CVE-2026-109618,CVE-2026-109619')
        for b, v in (('22', '22.23.4'), ('24', '24.22.1'), ('26', '26.12.1')):
            self.assertEqual(mp[('node', b)]['min_patched_sec'], v)
            self.assertEqual(mp[('node', b)]['driver_ids'], 'QP-SR-node-%s' % v)
        for b, v in (('6.9', '6.9.10'), ('7.0', '7.0.7'), ('7.1', '7.1.3'), ('4.1', 'NONE')):
            self.assertEqual(mp[('wordpress', b)]['min_patched_sec'], v)
        self.assertEqual(self.status('SRC-008')['status'], 'FAILED')
        self.assertEqual(self.status('SRC-008')['last_error'], 'ERR-FEED-503-03')   # secondary role

    def test_risk_examples_on_bundle(self):
        """§8.5 ex. 8, 10, 11 computed from the bundle (FR-ASMT-RISK-001)."""
        self.sync()
        today = time.strftime('%Y-%m-%d', time.gmtime())
        with Bundle(self.fs) as b:
            wp701 = b.assess('wordpress', '7.0.1', today)
            wp702 = b.assess('wordpress', '7.0.2', today)
            php = b.assess('php', '8.5.12', today)
        self.assertEqual((wp701['risk']['R'], wp701['risk']['level']), (71, 'CRITICAL'))
        self.assertEqual(wp701['exposure']['n_kev'], 3)
        self.assertEqual((wp702['risk']['R'], wp702['risk']['level']), (70, 'CRITICAL'))
        self.assertEqual(php['exposure']['adv_ids'], [])

    def test_bundle_layout(self):
        """FR-FEED-CACH-002: 9 TSV + feeds.db + manifest + SHA256SUMS; feeds.db meta = manifest."""
        self.sync()
        cur = os.path.realpath(self.fs.path('current'))
        self.assertEqual(os.path.dirname(cur), os.path.realpath(self.fs.path('bundles')))
        self.assertEqual(bundle.check_sums(cur), [])
        m = json.load(open(os.path.join(cur, 'manifest.json')))
        self.assertEqual(m['schema'], 'qp.feeds.bundle/1')
        self.assertRegex(m['bundle_id'], r'^b-\d{8}T\d{6}Z-[0-9a-f]{8}$')
        import sqlite3
        db = sqlite3.connect(os.path.join(cur, 'feeds.db'))
        self.assertEqual(dict(db.execute('SELECT key, value FROM meta')).get('bundle_id'), m['bundle_id'])
        header = open(os.path.join(cur, 'min_patched.tsv')).readline()
        self.assertEqual(header, '#product\tbranch\tmin_patched_sec\tmin_patched_all\tlatest\tdriver_ids\n')


class Sync(Base):
    def test_ttl_and_conditional_get(self):
        """BR-FEED-001: second run within TTL -> not_due; --force refetches with If-None-Match -> 304."""
        self.sync()
        code, res, _ = self.sync()
        outcomes = {s['src_id']: s['outcome'] for s in res['sources']}
        self.assertEqual(outcomes['SRC-006'], 'not_due')
        open(os.path.join(SRV, 'requests.log'), 'w').close()
        code, res, _ = self.sync(force=True)
        outcomes = {s['src_id']: s['outcome'] for s in res['sources']}
        self.assertEqual(outcomes['SRC-010'], 'not_modified')
        sent = [r for r in requests() if r['src'] == 'SRC-010']
        self.assertTrue(sent and sent[0]['if_none_match'])
        log = open(self.fs.path('state', 'last-sync.log')).read()
        self.assertIn('SRC-010 not_modified', log)
        self.assertIn('SRC-006 not_due', log)

    def test_due_rule_with_schedule(self):
        """age >= TTL - (N + 45 min): 24 h sources are due after 17 h 15 min with a 6 h schedule."""
        e = {'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 17.3 * 3600))}
        self.assertTrue(sync.is_due(e, {'ttl_hours': 24}, 6, time.time(), False))
        e = {'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 17 * 3600))}
        self.assertFalse(sync.is_due(e, {'ttl_hours': 24}, 6, time.time(), False))
        self.assertTrue(sync.is_due(e, {'ttl_hours': 24}, 6, time.time(), True))

    def test_retry_then_ok(self):
        """BR-FEED-003: 503 once, then OK (3 attempts allowed)."""
        control({'SRC-012': {'status': 503, 'times': 1}})
        self.sync(only=['SRC-012'])
        self.assertEqual(self.status('SRC-012')['status'], 'OK')
        self.assertEqual(len([r for r in requests() if r['src'] == 'SRC-012']), 2)

    def test_retry_after_too_long(self):
        self.sync()
        control({'SRC-010': {'status': 429, 'retry_after': 900}})
        self.sync(only=['SRC-010'], force=True)
        self.assertEqual(self.status('SRC-010')['last_error'], 'ERR-FEED-429-01')

    def test_failure_keeps_cache(self):
        """BR-FEED-006/007: primary down after a good run -> DEGRADED, CACHE, previous facts kept."""
        self.sync()
        before = self.mp()[('wordpress', '7.0')]['min_patched_sec']
        control({'SRC-012': {'status': 500}})
        code, res, _ = self.sync(only=['SRC-012'], force=True)
        self.assertEqual(code, 1)
        st = self.status('SRC-012')
        self.assertEqual((st['status'], st['data_origin'], st['last_error']), ('DEGRADED', 'CACHE', 'ERR-FEED-503-01'))
        self.assertEqual(self.mp()[('wordpress', '7.0')]['min_patched_sec'], before)

    def test_cross_source(self):
        """SRC-009 down -> latest of SRC-001 (CROSS:SRC-001), cached history kept."""
        self.sync()
        before = self.mp()[('node', '22')]['min_patched_sec']
        control({'SRC-009': {'status': 500}})
        self.sync(only=['SRC-009'], force=True)
        st = self.status('SRC-009')
        self.assertEqual((st['status'], st['data_origin']), ('DEGRADED', 'CROSS:SRC-001'))
        self.assertEqual(self.mp()[('node', '22')]['min_patched_sec'], before)

    def test_mirror(self):
        """SRC-006 primary down -> GitHub mirror (data_origin MIRROR, DEGRADED)."""
        control({'SRC-006': {'status': 503}})
        self.sync(only=['SRC-006'])
        st = self.status('SRC-006')
        self.assertEqual((st['status'], st['data_origin']), ('DEGRADED', 'MIRROR'))

    def test_malformed_rejected(self):
        """ERR-FEED-502-01: bad JSON goes to rejected/, previous data stays."""
        self.sync()
        control({'SRC-011': {'body': '<html>error</html>'}})
        code, res, w = self.sync(only=['SRC-011'], force=True)
        self.assertEqual(self.status('SRC-011')['last_error'], 'ERR-FEED-502-01')
        self.assertTrue(any(n.endswith('.gz') for n in os.listdir(self.fs.path('raw', 'SRC-011', 'rejected'))))
        self.assertEqual(self.mp()[('node', '20')]['driver_ids'], 'CVE-2026-21637,CVE-2026-21710')

    def test_shrink_needs_accept(self):
        """BR-FEED-009: KEV loses > 5 entries -> ERR-FEED-502-02 unless --force --accept-shrink."""
        self.sync()
        kev = json.load(open(os.path.join(FIX, 'SRC-006', 'kev.json')))
        kev['vulnerabilities'] = kev['vulnerabilities'][:2]
        kev['count'] = 2
        small = os.path.join(SRV, 'kev-small.json')
        json.dump(kev, open(small, 'w'))
        control({'SRC-006': {'file': small}})
        self.sync(only=['SRC-006'], force=True)
        self.assertEqual(self.status('SRC-006')['last_error'], 'ERR-FEED-502-02')
        self.sync(only=['SRC-006'], force=True, accept_shrink=True)
        self.assertEqual(self.status('SRC-006')['status'], 'OK')
        self.assertEqual(self.status('SRC-006')['records'], 2)

    def test_budget(self):
        """ERR-FEED-504-01: sources not reached within the budget keep their data."""
        t = [1000.0]
        clock = lambda: t[0]  # noqa: E731

        def slow_sleep(s):
            t[0] += s
        control({'SRC-002': {'status': 503}})
        sources_conf(self.fs.root, '')
        with open(self.fs.path('sources.conf'), 'a') as f:
            f.write('[SRC-002]\nretry_delays = 100,100,100\n')
        code, res, w = sync.run(self.sd, budget=60, now=clock, sleep=slow_sleep)
        self.assertTrue(res['pending'])
        self.assertTrue(any(c == 'ERR-FEED-504-01' for c, _ in w))

    def test_lock(self):
        """BR-FEED-015: a second sync waits, then ERR-FEED-423-01."""
        with sync.FeedsLock(self.fs):
            with self.assertRaises(errors.QPError) as cm:
                with sync.FeedsLock(self.fs, wait=0.3):
                    pass
        self.assertEqual(cm.exception.code, 'ERR-FEED-423-01')
        self.assertEqual(cm.exception.details['pid'], str(os.getpid()))

    def test_https_only(self):
        """BR-FEED-016: an http:// URL in sources.conf is refused."""
        with open(self.fs.path('sources.conf'), 'a') as f:
            f.write('[SRC-010]\nurl = http://example.invalid/schedule.json\n')
        with self.assertRaises(errors.QPError):
            self.sync(only=['SRC-010'])

    def test_nvd_paging_and_incremental(self):
        """SRC-004 pages of page_size and a lastMod window on the next run (BR-FEED-002)."""
        with open(self.fs.path('sources.conf'), 'a') as f:
            f.write('[SRC-004]\npage_size = 1\n')
        self.sync(only=['SRC-004'])
        self.assertEqual(self.status('SRC-004')['records'], 10)
        pages = [r for r in requests() if r['src'] == 'SRC-004']
        self.assertGreater(len(pages), 4)
        open(os.path.join(SRV, 'requests.log'), 'w').close()
        self.sync(only=['SRC-004'], force=True)
        self.assertTrue(all('lastModStartDate' in r['path'] for r in requests() if r['src'] == 'SRC-004'))
        self.assertEqual(self.status('SRC-004')['records'], 10)

    def test_atomic_swap_and_reader_lock(self):
        """BR-FEED-051: current/previous symlinks; a bundle held by a reader is not removed."""
        self.sync()
        first = os.path.basename(os.readlink(self.fs.path('current')))
        reader = bundle.current(self.fs)            # shared lock on the first bundle
        self.sync(force=True)
        second = os.path.basename(os.readlink(self.fs.path('current')))
        self.assertEqual(os.path.basename(os.readlink(self.fs.path('previous'))), first)
        self.sync(force=True)
        self.assertTrue(os.path.isdir(self.fs.path('bundles', first)))     # still read -> kept
        reader['release']()
        self.sync(force=True)
        self.assertFalse(os.path.isdir(self.fs.path('bundles', first)))
        self.assertNotEqual(first, second)


class Snapshots(Base):
    def setUp(self):
        Base.setUp(self)
        self.sync()
        self.out = os.path.join(self.sd, 'snap.tar.gz')
        self.res = snapshot.export(self.fs, self.out)

    def fresh(self):
        sd = tempfile.mkdtemp()
        os.chmod(sd, 0o700)
        self.addCleanup(shutil.rmtree, sd, True)
        return FeedsDir(sd)

    def do_import(self, fs, path, sha, force=False):
        with sync.FeedsLock(fs):
            w = fs.path('staging-test')
            os.mkdir(w)
            try:
                cur = bundle.current(fs)
                gen = cur['manifest']['generated_at'] if cur else None
                if cur:
                    cur['release']()
                m, actual = snapshot.verify_archive(path, sha, w, current_generated_at=gen, force=force)
                snapshot.install_extracted(fs, w, m, actual, archive=path)
                return m
            finally:
                shutil.rmtree(w, ignore_errors=True)

    def test_export_contents(self):
        """FR-FEED-SNAP-002 / BR-FEED-056: public data only, SHA256SUMS of bundle/."""
        with tarfile.open(self.out) as t:
            names = t.getnames()
        self.assertIn('manifest.json', names)
        self.assertIn('SHA256SUMS', names)
        self.assertIn('bundle/feeds.db', names)
        self.assertFalse([n for n in names if n.startswith(('cache', 'raw')) or n.endswith('.lock')])
        with self.assertRaises(FileExistsError):
            snapshot.export(self.fs, self.out)                      # never overwrites

    def test_import_ok_and_base(self):
        fs = self.fresh()
        m = self.do_import(fs, self.out, self.res['sha256'])
        self.assertEqual(os.path.basename(os.readlink(fs.path('current'))), m['bundle_id'])
        self.assertEqual(read_json(fs.path('state', 'base.json'))['type'], 'snapshot')
        self.assertEqual(len(os.listdir(fs.path('snapshots', 'imported'))), 1)

    def test_import_sha_mismatch(self):
        fs = self.fresh()
        with self.assertRaises(errors.QPError) as cm:
            self.do_import(fs, self.out, '0' * 64)
        self.assertEqual(cm.exception.code, 'ERR-FEED-422-02')
        self.assertFalse(os.path.lexists(fs.path('current')))

    def tamper(self, fn):
        """Rewrite the archive with FN(name, data) -> data, return (path, sha)."""
        out = os.path.join(self.sd, 'bad.tar.gz')
        with tarfile.open(self.out) as src, tarfile.open(out, 'w:gz') as dst:
            for m in src.getmembers():
                data = src.extractfile(m).read()
                data = fn(m.name, data)
                m.size = len(data)
                dst.addfile(m, io.BytesIO(data))
        return out, snapshot.sha256_of(out)

    def test_import_sums_mismatch(self):
        fs = self.fresh()
        path, sha = self.tamper(lambda n, d: d + b'#x\n' if n == 'bundle/lifecycle.tsv' else d)
        with self.assertRaises(errors.QPError) as cm:
            self.do_import(fs, path, sha)
        self.assertEqual(cm.exception.code, 'ERR-FEED-422-02')

    def test_import_unsafe_member(self):
        fs = self.fresh()
        out = os.path.join(self.sd, 'evil.tar.gz')
        with tarfile.open(out, 'w:gz') as t:
            info = tarfile.TarInfo('bundle/../../etc/x')
            info.size = 1
            t.addfile(info, io.BytesIO(b'x'))
        with self.assertRaises(errors.QPError):
            self.do_import(fs, out, snapshot.sha256_of(out))
        out2 = os.path.join(self.sd, 'link.tar.gz')
        with tarfile.open(out2, 'w:gz') as t:
            info = tarfile.TarInfo('bundle/feeds.db')
            info.type = tarfile.SYMTYPE
            info.linkname = '/etc/shadow'
            t.addfile(info)
        with self.assertRaises(errors.QPError):
            self.do_import(fs, out2, snapshot.sha256_of(out2))

    def test_import_older(self):
        """ERR-FEED-409-02 unless --force."""
        with self.assertRaises(errors.QPError) as cm:
            self.do_import(self.fs, self.out, self.res['sha256'])
        self.assertEqual(cm.exception.code, 'ERR-FEED-409-02')

    def test_packaged_snapshot(self):
        """FR-FEED-SNAP-001: pinned packaged snapshot installed on first use, wrong pin refused."""
        tool = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tool, True)
        os.makedirs(os.path.join(tool, 'share', 'php-quickpatch'))
        shutil.copy(self.out, os.path.join(tool, 'share', 'php-quickpatch', 'feeds-snapshot.tar.gz'))
        script = os.path.join(tool, 'php-quickpatch.sh')
        with open(script, 'w') as f:
            f.write('QP_SNAPSHOT_SHA256="%s"\n' % ('f' * 64))
        fs = self.fresh()
        w = []
        self.assertIsNone(snapshot.maybe_install_packaged(fs, script, w))
        self.assertEqual(w[0][0], 'ERR-FEED-422-02')
        with open(script, 'w') as f:
            f.write('QP_SNAPSHOT_SHA256="%s"\n' % self.res['sha256'])
        self.assertIsNotNone(snapshot.maybe_install_packaged(fs, script, []))
        self.assertTrue(os.path.islink(fs.path('current')))
        self.assertIsNone(snapshot.maybe_install_packaged(fs, script, []))      # not newer -> kept


class Osv(Base):
    def test_library_check_cache_and_paging(self):
        """FR-FEED-OSV-001: paging by next_page_token, cache per lockfile, stale cache when OSV fails."""
        with open(os.path.join(SRV, 'osv.vulns'), 'w') as f:
            f.write('left-pad 1.0.0 GHSA-aaaa-bbbb-cccc,MAL-2026-1\n')
        lock = os.path.join(self.sd, 'package-lock.json')
        open(lock, 'w').write('{}')
        control({'SRC-007': {'page_size': 1}})
        found, meta = osv.library_check(self.fs, 'npm', lock, [('left-pad', '1.0.0'), ('ok', '1.0.0')])
        self.assertEqual(found[0]['advisories'], ['GHSA-aaaa-bbbb-cccc', 'MAL-2026-1'])
        self.assertTrue(found[0]['is_malware'])
        self.assertEqual(meta['origin'], 'PRIMARY')
        n = len(requests())
        found, meta = osv.library_check(self.fs, 'npm', lock, [('left-pad', '1.0.0'), ('ok', '1.0.0')])
        self.assertEqual(meta['origin'], 'CACHE')
        self.assertEqual(len(requests()), n)
        control({'SRC-007': {'status': 503}})
        p = self.fs.path('cache', 'osv', os.listdir(self.fs.path('cache', 'osv'))[0])
        doc = json.load(open(p))
        doc['_cached_at'] -= 3 * 86400
        json.dump(doc, open(p, 'w'))
        found, meta = osv.library_check(self.fs, 'npm', lock, [('left-pad', '1.0.0')])
        self.assertEqual(meta['origin'], 'CACHE')        # <= 7 days
        doc['_cached_at'] -= 8 * 86400
        json.dump(doc, open(p, 'w'))
        with self.assertRaises(osv.FetchError) as cm:
            osv.library_check(self.fs, 'npm', lock, [('left-pad', '1.0.0')])
        self.assertEqual(cm.exception.code, 'ERR-FEED-503-02')

    def test_backport_chain(self):
        """§7: querybatch -> UNFIXED; per-CVE Ubuntu record -> FIXED; else changelog / UNKNOWN."""
        with open(os.path.join(SRV, 'osv.vulns'), 'w') as f:
            f.write('php8.3 8.3.6-0ubuntu0.24.04.13 UBUNTU-CVE-2026-17545\n')
        os.makedirs(os.path.join(SRV, 'osv-vulns'), exist_ok=True)
        json.dump({'id': 'UBUNTU-CVE-2026-109618', 'modified': '2026-10-21T00:00:00Z',
                   'affected': [{'package': {'ecosystem': 'Ubuntu:24.04:LTS', 'name': 'php8.3'},
                                 'ranges': [{'type': 'ECOSYSTEM', 'events': [{'introduced': '0'},
                                                                             {'fixed': '8.3.6-0ubuntu0.24.04.13'}]}]}]},
                  open(os.path.join(SRV, 'osv-vulns', 'UBUNTU-CVE-2026-109618.json'), 'w'))
        info = {'ID': 'ubuntu', 'VERSION_ID': '24.04', 'VERSION_CODENAME': 'noble'}
        orig = osv.source_package
        osv.source_package = lambda m, p: 'php8.3'
        try:
            res = osv.backport(self.fs, 'dpkg', 'php8.3-cli', '8.3.6-0ubuntu0.24.04.13',
                               ['CVE-2026-17545', 'CVE-2026-109618', 'CVE-2024-5585'], info=info, sleep=lambda s: None)
        finally:
            osv.source_package = orig
        st = {c['adv_id']: (c['state'], c['origin']) for c in res['cves']}
        self.assertEqual(st['CVE-2026-17545'], ('UNFIXED', 'OSV'))
        self.assertEqual(st['CVE-2026-109618'], ('FIXED', 'OSV'))
        self.assertEqual(st['CVE-2024-5585'], ('UNKNOWN', 'LOCAL_CHANGELOG'))
        self.assertEqual(res['state'], 'vulnerable')
        self.assertEqual(res['ecosystem'], 'Ubuntu:24.04:LTS')


class Schedule(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.orig = (schedule.SYSTEMD_DIR, schedule.CRON_FILE, schedule.kind, schedule.subprocess.run)
        schedule.SYSTEMD_DIR = self.d
        schedule.CRON_FILE = os.path.join(self.d, 'cron')
        self.calls = []
        schedule.subprocess.run = lambda cmd, **kw: self.calls.append(cmd) or subprocess.CompletedProcess(cmd, 0, b'', b'')

    def tearDown(self):
        schedule.SYSTEMD_DIR, schedule.CRON_FILE, schedule.kind, schedule.subprocess.run = self.orig
        shutil.rmtree(self.d, ignore_errors=True)

    def test_systemd_install_update_remove(self):
        """FR-FEED-SCHD-001 / BR-FEED-057: one timer, updated in place, fixed minute."""
        schedule.kind = lambda: 'systemd'
        plan = schedule.plan_install('/opt/qp/php-quickpatch.sh', 6)
        schedule.install(plan)
        timer = open(os.path.join(self.d, 'php-quickpatch-feeds.timer')).read()
        self.assertIn('OnCalendar=*-*-* 00/6:%02d:00' % plan['minute'], timer)
        self.assertIn('RandomizedDelaySec=900', timer)
        self.assertIn('ExecStart=/opt/qp/php-quickpatch.sh feeds update --quiet',
                      open(os.path.join(self.d, 'php-quickpatch-feeds.service')).read())
        self.assertIn(['systemctl', 'enable', '--now', 'php-quickpatch-feeds.timer'], self.calls)
        info = schedule.show()
        self.assertEqual((info['type'], info['interval_h']), ('systemd', 6))
        plan2 = schedule.plan_install('/opt/qp/php-quickpatch.sh', 12)
        self.assertEqual(plan2['minute'], plan['minute'])
        schedule.install(plan2)
        self.assertEqual(schedule.show()['interval_h'], 12)
        self.assertEqual(sorted(os.listdir(self.d)), ['php-quickpatch-feeds.service', 'php-quickpatch-feeds.timer'])
        schedule.remove(schedule.plan_remove())
        self.assertIsNone(schedule.show())

    def test_cron(self):
        schedule.kind = lambda: 'cron'
        schedule.install(schedule.plan_install('/opt/qp/php-quickpatch.sh', 24))
        line = open(schedule.CRON_FILE).read()
        self.assertRegex(line, r'^\d+ 0 \* \* \* root /opt/qp/php-quickpatch.sh feeds update --quiet # php-quickpatch-feeds$')
        self.assertEqual(schedule.show()['interval_h'], 24)


class Schemas(Base):
    def validate(self, name, result, exit_code=0):
        from qplib.envelope import Envelope
        env = Envelope('qp.feeds.%s/1' % name, 'feeds', ['feeds', name], subcommand=name)
        doc = env.document(exit_code, result)
        schema = json.load(open(os.path.join(SHARE, 'schemas', 'qp.feeds.%s.v1.schema.json' % name)))
        self.assertEqual(jsonschema_lite.validate(doc, schema), [])

    def test_update_export_schema(self):
        code, res, _ = self.sync()
        self.validate('update', res, code)
        out = os.path.join(self.sd, 's.tar.gz')
        self.validate('export', snapshot.export(self.fs, out))


if __name__ == '__main__':
    unittest.main()
