"""Audit hash chain (FR-JOB-AUD-001..003, BR-AUD-003, BR-AUD-006; TC-JOB-019..024)."""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib import audit  # noqa: E402


def make_record(prev, seq, ts, action='fix', record_type='RESULT', result='ok', exit_code=0):
    rec = {'action': action, 'actor': 'cli:root', 'args': ['fix', '--only', 'php'], 'exit_code': exit_code,
           'job_id': None, 'plan_id': None, 'prev_hash': prev, 'record_type': record_type, 'result': result,
           'run_id': None, 'seq': seq, 'source': 'cli', 'sys_user': 'root', 'ts': ts}
    rec['hash'] = audit.record_hash(prev, rec)
    return rec


def write_chain(state_dir, months):
    """months: list of (YYYYMM, count). Returns the records written."""
    os.makedirs(os.path.join(state_dir, 'audit'), exist_ok=True)
    prev, seq, out = audit.ZERO, 0, []
    for month, count in months:
        path = os.path.join(state_dir, 'audit', 'audit-%s.jsonl' % month)
        with open(path, 'w', encoding='utf-8') as f:
            for i in range(count):
                seq += 1
                ts = '%s-%s-%02dT10:00:%02d.000Z' % (month[:4], month[4:], 1 + i % 22, i % 60)
                action = 'migrate_switch' if i % 10 == 0 else 'fix'
                rec = make_record(prev, seq, ts, action=action)
                f.write(audit.canonical(rec) + '\n')
                prev = rec['hash']
                out.append(rec)
    return out


class AuditChain(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_tc_job_019_write_fields_and_hash(self):
        audit.write(self.d, 'INTENT', 'fix', ['fix', 'token=abc'])
        seq, h = audit.write(self.d, 'RESULT', 'fix', ['fix'], result='ok', exit_code=0, run_id='20261022-104201')
        self.assertEqual(seq, 2)
        files = audit.audit_files(self.d)
        self.assertEqual(len(files), 1)
        self.assertEqual(oct(os.stat(files[0]).st_mode & 0o777), '0o600')
        recs = [json.loads(line) for line in open(files[0])]
        self.assertEqual(set(recs[0]), set(audit.FIELDS))
        self.assertEqual(recs[0]['prev_hash'], audit.ZERO)
        self.assertEqual(recs[0]['args'], ['fix', 'token=***'])
        self.assertIsNone(recs[0]['result'])
        body = dict(recs[1])
        stored = body.pop('hash')
        self.assertEqual(stored, audit.record_hash(recs[0]['hash'], body))
        self.assertEqual(h, stored)
        self.assertTrue(audit.verify(self.d)['verified'])

    def test_tc_job_021_chain_crosses_month_files(self):
        recs = write_chain(self.d, [('202610', 5), ('202611', 3)])
        first_nov = json.loads(open(os.path.join(self.d, 'audit', 'audit-202611.jsonl')).readline())
        self.assertEqual(recs[0]['prev_hash'], audit.ZERO)
        self.assertEqual(first_nov['prev_hash'], recs[4]['hash'])
        self.assertTrue(audit.verify(self.d)['verified'])

    def test_tc_job_022_list_and_verify(self):
        write_chain(self.d, [('202610', 120)])
        rows = audit.list_records(self.d, '2026-10-01', '2026-10-22', action='migrate_switch')
        self.assertEqual(len(rows), 12)
        res = audit.verify(self.d)
        self.assertEqual((res['verified'], res['records'], res['first_broken_seq']), (True, 120, None))

    def test_tc_job_023_one_byte_changed(self):
        write_chain(self.d, [('202610', 900)])
        path = os.path.join(self.d, 'audit', 'audit-202610.jsonl')
        lines = open(path, 'rb').read().split(b'\n')
        lines[876] = lines[876].replace(b'"actor":"cli:root"', b'"actor":"cli:rooT"')
        open(path, 'wb').write(b'\n'.join(lines))
        res = audit.verify(self.d)
        self.assertEqual((res['verified'], res['first_broken_seq']), (False, 877))

    def test_tc_job_024_every_single_byte_change_is_detected(self):
        write_chain(self.d, [('202610', 60), ('202611', 20)])
        files = audit.audit_files(self.d)
        originals = {f: open(f, 'rb').read() for f in files}
        rng = random.Random(20261024)
        missed = []
        for i in range(1000):
            f = rng.choice(files)
            data = bytearray(originals[f])
            pos = rng.randrange(len(data))
            old = data[pos]
            new = old
            while new == old:
                new = rng.randrange(256)
            data[pos] = new
            open(f, 'wb').write(bytes(data))
            if audit.verify(self.d)['verified']:
                missed.append((f, pos, old, new))
            open(f, 'wb').write(originals[f])
        self.assertEqual(missed, [])
        # Deleting the last record of October is caught at the first of November.
        oct_path = files[0]
        lines = originals[oct_path].split(b'\n')
        open(oct_path, 'wb').write(b'\n'.join(lines[:-2] + [b'']))
        res = audit.verify(self.d)
        self.assertFalse(res['verified'])
        self.assertEqual(res['first_broken_seq'], 61)

    def test_anchors_catch_truncation_and_rehash(self):
        recs = write_chain(self.d, [('202610', 10)])
        os.makedirs(os.path.join(self.d, 'jobs', 'JOB-1'))
        with open(os.path.join(self.d, 'jobs', 'JOB-1', 'result.json'), 'w') as f:
            json.dump({'audit_anchor': {'seq': 10, 'hash': recs[9]['hash']}}, f)
        self.assertTrue(audit.verify(self.d)['verified'])
        # Drop the last 2 records: the chain alone is still valid, the anchor is not.
        path = audit.audit_files(self.d)[0]
        lines = open(path).read().splitlines()[:8]
        open(path, 'w').write('\n'.join(lines) + '\n')
        res = audit.verify(self.d)
        self.assertFalse(res['verified'])
        self.assertEqual(res['anchors_checked'][0]['match'], False)
        # Recomputed chain after an edit: caught by a manual anchor.
        write_chain(self.d, [('202610', 10)])
        shutil.rmtree(os.path.join(self.d, 'jobs'))
        good = audit.verify(self.d, anchors=[{'seq': 5, 'hash': recs[4]['hash']}])
        self.assertTrue(good['verified'])
        bad = audit.verify(self.d, anchors=[{'seq': 5, 'hash': 'f' * 64}])
        self.assertFalse(bad['verified'])
        self.assertEqual(bad['first_broken_seq'], 5)

    def test_bash_and_python_share_one_chain(self):
        """php-quickpatch.sh audit_write and qplib.audit.write interleave."""
        script = os.path.join(ROOT, 'php-quickpatch.sh')
        bash = ('. "$1"; STATE_DIR="$2"; ARGV_ORIG=(fix "--path" $\'/srv/a "b"\\\\c\\td\'); audit_args; '
                'audit_write INTENT fix "" "" && audit_write RESULT fix ok 1 && echo "$REPLY"')
        audit.write(self.d, 'EVENT', 'login_ok', [])
        out = subprocess.check_output(['bash', '-c', bash, '_', script, self.d]).decode()
        seq, h = out.split()
        self.assertEqual(int(seq), 3)
        audit.write(self.d, 'EVENT', 'token_issued', ['serve', 'é€'])
        res = audit.verify(self.d)
        self.assertTrue(res['verified'], res)
        self.assertEqual(res['records'], 4)
        recs = audit.list_records(self.d)
        self.assertEqual(recs[1]['args'], ['fix', '--path', '/srv/a "b"\\c\td'])
        self.assertEqual(recs[2]['hash'], h)


if __name__ == '__main__':
    unittest.main()
