"""qplib: STATE_DIR checks (spec §2.1), envelope, redaction, error catalog, schemas."""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARE = os.path.join(ROOT, 'share', 'php-quickpatch')
sys.path.insert(0, SHARE)

from qplib import errors, jsonschema_lite, statedir  # noqa: E402
from qplib.envelope import Envelope, redact  # noqa: E402

OTHER_UID = 4242


def run_as_nobody(code, env):
    """Run python CODE as user nobody (needs root); return (rc, stdout)."""
    # runuser resets HOME, so pass the environment through env(1).
    argv = ['runuser', '-u', 'nobody', '--', 'env'] + ['%s=%s' % kv for kv in sorted(env.items())]
    p = subprocess.run(argv + [sys.executable, '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode().strip()


SELECT = ('import sys; sys.path.insert(0, %r)\n'
          'from qplib import statedir\n'
          'from qplib.errors import QPError\n'
          'try:\n    print(statedir.select())\n'
          'except QPError as e:\n    print(e.code, e.details["reason"]); sys.exit(2)\n') % SHARE


@unittest.skipUnless(os.geteuid() == 0, 'needs root to create files owned by other users')
class StateDirPython(unittest.TestCase):
    """NFR-SEC-010 matrix for the Python side (non-root paths; root paths are in the Bash suite)."""

    def setUp(self):
        self.t = tempfile.mkdtemp()
        os.chmod(self.t, 0o1777)
        self.home = os.path.join(self.t, 'home')
        self.tmp = os.path.join(self.t, 'tmp')
        os.mkdir(self.home)
        os.mkdir(self.tmp)
        os.chmod(self.tmp, 0o1777)
        os.chown(self.home, 65534, -1)
        self.env = {'PATH': os.environ['PATH'], 'HOME': self.home, 'TMPDIR': self.tmp}

    def tearDown(self):
        shutil.rmtree(self.t)

    def plant(self, kind, path):
        if kind == 'other':
            os.mkdir(path)
            os.chown(path, OTHER_UID, -1)
        elif kind == 'symlink':
            target = tempfile.mkdtemp(dir=self.t)
            os.chown(target, OTHER_UID, -1)
            os.symlink(target, path)
        elif kind == 'mode':
            os.mkdir(path)
            os.chown(path, 65534, -1)
            os.chmod(path, 0o777)
        elif kind == 'file':
            open(path, 'w').close()
            os.chown(path, 65534, -1)

    def test_primary_planted_exits_2(self):
        expect = {'other': 'owner', 'symlink': 'symlink', 'mode': 'mode', 'file': 'not_dir'}
        for kind, reason in expect.items():
            p = os.path.join(self.home, '.php-quickpatch')
            self.plant(kind, p)
            rc, out = run_as_nobody(SELECT, self.env)
            self.assertEqual((rc, out), (2, 'ERR-CLI-412-01 %s' % reason), kind)
            self.assertEqual(os.listdir(self.tmp), [], kind)
            if os.path.isdir(p) and not os.path.islink(p):
                os.rmdir(p)
            else:
                os.unlink(p)

    def test_fresh_home_dir_is_0700(self):
        rc, out = run_as_nobody(SELECT, self.env)
        self.assertEqual(rc, 0)
        st = os.lstat(out)
        self.assertEqual((oct(st.st_mode & 0o777), st.st_uid), ('0o700', 65534))

    def test_fallback_skips_planted_candidates(self):
        env = dict(self.env, HOME='')
        for kind in ('other', 'symlink', 'mode', 'file'):
            for name in ('php-quickpatch-65534', 'php-quickpatch-65534.AbC123'):
                for e in os.listdir(self.tmp):
                    p = os.path.join(self.tmp, e)
                    shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.unlink(p)
                self.plant(kind, os.path.join(self.tmp, name))
                rc, out = run_as_nobody(SELECT, env)
                self.assertEqual(rc, 0, (kind, name))
                self.assertNotEqual(os.path.basename(out), name)
                self.assertTrue(os.path.basename(out).startswith('php-quickpatch-65534.'))
                st = os.lstat(out)
                self.assertEqual((oct(st.st_mode & 0o777), st.st_uid), ('0o700', 65534))

    def test_fallback_reuses_newest_own_dir(self):
        env = dict(self.env, HOME='')
        a = os.path.join(self.tmp, 'php-quickpatch-65534')
        b = os.path.join(self.tmp, 'php-quickpatch-65534.zzzzzz')
        for p in (a, b):
            os.mkdir(p, 0o700)
            os.chown(p, 65534, -1)
        os.utime(a, (1767225600, 1767225600))
        rc, out = run_as_nobody(SELECT, env)
        self.assertEqual((rc, out), (0, b))


class Envelope_(unittest.TestCase):
    def test_redact(self):
        os.environ['QP_NVD_API_KEY'] = 'QPTESTKEY0001'
        try:
            self.assertEqual(redact('key QPTESTKEY0001 token=abc&x=1 https://u:p4ss@h/x'),
                             'key *** token=***&x=1 https://u:***@h/x')
        finally:
            del os.environ['QP_NVD_API_KEY']

    def test_envelope_matches_schema(self):
        env = Envelope('qp.audit/1', 'audit', ['audit', 'verify', '--json'], subcommand='verify')
        env.error('ERR-AUD-409-01', 'x', 'host')
        doc = env.document(2, {'verified': False, 'records': 3, 'first_broken_seq': 2,
                               'anchors_checked': [], 'last_anchor': None})
        schema = json.load(open(os.path.join(SHARE, 'schemas', 'qp.audit.v1.schema.json')))
        self.assertEqual(jsonschema_lite.validate(doc, schema), [])
        doc['exit_code'] = 3
        self.assertTrue(jsonschema_lite.validate(doc, schema))


class ErrorCatalog(unittest.TestCase):
    def test_every_code_has_both_languages(self):
        cat = errors.load()
        self.assertGreaterEqual(len(cat), 129)
        for code, e in cat.items():
            self.assertTrue(e['vi'] and e['en'], code)

    def test_message_localized(self):
        self.assertEqual(errors.message('ERR-CLI-423-01', lang='en'), 'Another php-quickpatch run is in progress.')
        self.assertEqual(errors.message('ERR-CLI-424-01', lang='vi', command='assess'), 'assess cần Python 3.6 trở lên.')


class Schemas(unittest.TestCase):
    def test_every_schema_is_2020_12_and_self_contained(self):
        files = glob.glob(os.path.join(SHARE, 'schemas', 'qp.*.v1.schema.json'))
        self.assertGreaterEqual(len(files), 8)
        for f in files:
            s = json.load(open(f))
            self.assertEqual(s['$schema'], 'https://json-schema.org/draft/2020-12/schema', f)
            self.assertTrue(s['$id'].startswith('urn:php-quickpatch:schema:qp.'), f)
            self.assertIn('envelope', s['$defs'])

    def test_lite_validator_keywords(self):
        s = {'type': 'object', 'required': ['a'], 'properties': {
            'a': {'type': 'integer', 'minimum': 1}, 'b': {'enum': ['x']}, 'c': {'type': 'string', 'pattern': '^q'},
            'd': {'type': 'array', 'items': {'$ref': '#/$defs/n'}}}, '$defs': {'n': {'type': 'null'}}}
        self.assertEqual(jsonschema_lite.validate({'a': 1, 'b': 'x', 'c': 'qq', 'd': [None]}, s), [])
        self.assertEqual(len(jsonschema_lite.validate({'a': 0, 'b': 'y', 'c': 'z', 'd': [1]}, s)), 4)
        self.assertEqual(len(jsonschema_lite.validate({}, s)), 1)
        self.assertEqual(len(jsonschema_lite.validate({'a': True}, s)), 1)


if __name__ == '__main__':
    unittest.main()
