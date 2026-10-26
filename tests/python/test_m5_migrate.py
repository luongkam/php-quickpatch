"""M5 unit tests: FastCGI client of the pre-switch trial run and the switch check (qplib/fcgi.py,
DOC-SRS-QP-ENV-002 §3.3/§3.4), the FR-UPG-SEQ-001 gate of migrate switch (plan.gate_checks),
T-CHK-13 (mark_rolled_back) and the catalog cli_action of P2/P5 items."""
import contextlib
import io
import json
import os
import shutil
import socket
import struct
import sys
import tempfile
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'share', 'php-quickpatch'))

from qplib import fcgi, plan as PL  # noqa: E402


class FakeFpm(threading.Thread):
    """A FastCGI responder on a unix socket: answers every request with STDOUT/STDERR of `reply`."""

    def __init__(self, path, reply):
        super().__init__(daemon=True)
        self.path, self.reply, self.params = path, reply, []
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        self.sock.listen(5)
        self.accepted = 0

    def run(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            self.accepted += 1
            data = b''
            while not data.endswith(fcgi._record(fcgi.STDIN, 1)):
                chunk = c.recv(65536)
                if not chunk:
                    break
                data += chunk
            self.params.append(data)
            out, err, end = self.reply(self)
            msg = b''
            if out:
                msg += fcgi._record(fcgi.STDOUT, 1, out)
            if err:
                msg += fcgi._record(fcgi.STDERR, 1, err)
            if end:
                msg += fcgi._record(fcgi.END, 1, struct.pack('!IB3x', 0, 0))
            c.sendall(msg)
            c.close()

    def stop(self):
        self.sock.close()


class FcgiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, 'fpm.sock')

    def tearDown(self):
        self.srv.stop()
        shutil.rmtree(self.tmp)

    def start(self, reply):
        self.srv = FakeFpm(self.path, reply)
        self.srv.start()

    def test_probe_ok(self):
        self.start(lambda s: (b'Content-type: text/html\r\n\r\n<html>ok</html>', b'', True))
        r = fcgi.probe('unix:' + self.path, '/var/www/a', 'a.test', version='2.0.0')
        self.assertTrue(r['ok'], r)
        self.assertEqual(r['status'], '200')
        self.assertIn(b'SCRIPT_FILENAME/var/www/a/index.php', self.srv.params[0])
        self.assertIn(b'php-quickpatch-hc/2.0.0', self.srv.params[0])

    def test_probe_5xx_fatal_and_source(self):
        """BR-HC-003: 5xx, PHP Fatal/Parse error on stderr, PHP source in the body fail the probe."""
        self.start(lambda s: (b'Status: 500 Internal Server Error\r\n\r\n<?php echo 1;',
                              b'PHP Parse error:  syntax error in /var/www/a/index.php on line 3', True))
        r = fcgi.probe('unix:' + self.path, '/var/www/a', 'a.test')
        self.assertFalse(r['ok'])
        self.assertIn('Status 500', r['detail'])
        self.assertIn('PHP Parse error', r['detail'])
        self.assertIn('<?php', r['detail'])

    def test_probe_no_end_request(self):
        self.start(lambda s: (b'Content-type: text/html\r\n\r\npartial', b'', False))
        r = fcgi.probe('unix:' + self.path, '/var/www/a', 'a.test', timeout=2)
        self.assertFalse(r['ok'])
        self.assertIn('FCGI_END_REQUEST', r['detail'])

    def test_probe_connect_refused(self):
        self.srv = FakeFpm(self.path, lambda s: (b'', b'', True))      # bound, never started
        r = fcgi.probe('unix:' + os.path.join(self.tmp, 'missing.sock'), '/var/www/a', 'a.test', timeout=1)
        self.assertFalse(r['ok'])
        self.assertIn('connect', r['detail'])

    def test_status_accepted_conn(self):
        """§3.4 method 1: accepted conn of the status page of the pool."""
        self.start(lambda s: (b'Content-type: text/plain\r\n\r\npool: qp-a\naccepted conn: %d\n' % s.accepted, b'', True))
        self.assertEqual(fcgi.status('unix:' + self.path)['accepted_conn'], 1)
        self.assertEqual(fcgi.status('unix:' + self.path)['accepted_conn'], 2)
        self.assertIn(b'SCRIPT_NAME/qp-fpm-status', self.srv.params[0])

    def test_large_params_and_main(self):
        self.start(lambda s: (b'Content-type: text/plain\r\n\r\n' + b'x' * 70000, b'', True))
        r = fcgi.probe('unix:' + self.path, '/' + 'd' * 300, 'a.test')
        self.assertTrue(r['ok'])
        self.assertEqual(r['body_bytes'], 70000)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(fcgi.main(['probe', '--endpoint', 'unix:' + self.path, '--docroot', '/x']), 0)
        self.assertTrue(json.loads(out.getvalue())['ok'])


def write_plan(state, plan_id, status='approved', order=('a.test', 'b.test', 'c.test'), items=None):
    d = os.path.join(state, 'plans', plan_id)
    os.makedirs(d)
    plan = {'plan_id': plan_id, 'runtime_id': 'php:0123456789ab', 'runtime_kind': 'php', 'status': status,
            'mode': 'cross_branch', 'target': {'branch': '8.4', 'patch_version': '8.4.27'}, 'stale': False,
            'stale_reasons': [], 'site_order': list(order), 'blocked_sites': [], 'inputs': {}}
    if items is None:
        items = [{'item_key': 'CHK-PHP-010-24@' + s, 'chk_id': 'CHK-PHP-010-24', 'site_id': s, 'phase': 'P5',
                  'status': 'PENDING', 'depends_on': [], 'blocked_by': [], 'exec_type': 'SEMI',
                  'cli_action': 'migrate switch %s --target 8.4 --plan $PLAN_ID' % s} for s in order]
    json.dump(plan, open(os.path.join(d, 'plan.json'), 'w'))
    json.dump({'items': items}, open(os.path.join(d, 'items.json'), 'w'))


def index(state, rows):
    os.makedirs(os.path.join(state, 'switches'), exist_ok=True)
    with open(os.path.join(state, 'switches', 'index.tsv'), 'w') as f:
        f.write('#ts\trun_id\tsite_id\tsite_key\tfrom>to\tstatus\tactor\tplan_id\tjob_id\trollback_reason\tnote\n')
        for run, site, st, plan, note in rows:
            f.write('2026-10-26T00:00:00.000Z\t%s\t%s\t%s\t8.3>8.4\t%s\tcli:root\t%s\t-\t-\t%s\n' % (run, site, site, st, plan, note))


class GateTest(unittest.TestCase):
    PID = 'PLN-20261026-000000-abcd'

    def setUp(self):
        self.state = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.state)

    def codes(self, site, target='8.4'):
        return [c for c, _ in PL.gate_checks(self.state, self.PID, site, target, '2026-10-26')]

    def test_draft_plan_refused(self):
        write_plan(self.state, self.PID, status='draft')
        self.assertEqual(self.codes('a.test'), ['ERR-UPG-409-02'])

    def test_order(self):
        """FR-UPG-SEQ-001: canary first; the next site only after the previous one PASSED."""
        write_plan(self.state, self.PID)
        self.assertEqual(self.codes('a.test'), [])
        self.assertEqual(self.codes('b.test'), ['ERR-UPG-409-03'])
        self.assertEqual(self.codes('x.test'), ['ERR-UPG-409-03'])
        index(self.state, [('20261026-000001', 'a.test', 'PASSED', self.PID, '-')])
        self.assertEqual(self.codes('b.test'), [])
        self.assertEqual(self.codes('c.test'), ['ERR-UPG-409-03'])
        self.assertEqual(self.codes('b.test', target='8.5'), ['ERR-CLI-400-01'])

    def test_failed_run_needs_ack(self):
        """BR-UPG-003: ROLLED_BACK/HC_FAILED_KEPT stops the plan until acknowledged; then same or next site."""
        write_plan(self.state, self.PID)
        index(self.state, [('20261026-000001', 'a.test', 'ROLLED_BACK', self.PID, '-')])
        self.assertEqual(self.codes('a.test'), ['ERR-UPG-409-03'])
        self.assertEqual(self.codes('b.test'), ['ERR-UPG-409-03'])
        index(self.state, [('20261026-000001', 'a.test', 'ROLLED_BACK', self.PID, '-'),
                           ('20261026-000001', 'a.test', 'ROLLED_BACK', self.PID, 'ack:2026-10-26T01:00:00.000Z')])
        self.assertEqual(self.codes('a.test'), [])
        self.assertEqual(self.codes('b.test'), [])
        self.assertEqual(self.codes('c.test'), ['ERR-UPG-409-03'])

    def test_deps_of_p5(self):
        """BR-SCN-018: the P5 item of the site waits for its P3/P4 items (ERR-SCN-424-01)."""
        items = [{'item_key': 'CHK-PHP-010-19@a.test', 'chk_id': 'CHK-PHP-010-19', 'site_id': 'a.test', 'phase': 'P3',
                  'status': 'PENDING', 'depends_on': [], 'blocked_by': [], 'exec_type': 'AUTO', 'cli_action': None},
                 {'item_key': 'CHK-PHP-010-24@a.test', 'chk_id': 'CHK-PHP-010-24', 'site_id': 'a.test', 'phase': 'P5',
                  'status': 'PENDING', 'depends_on': ['CHK-PHP-010-19@a.test'], 'blocked_by': [], 'exec_type': 'SEMI',
                  'cli_action': 'migrate switch a.test --target 8.4 --plan $PLAN_ID'}]
        write_plan(self.state, self.PID, order=('a.test',), items=items)
        self.assertEqual(self.codes('a.test'), ['ERR-SCN-424-01'])

    def test_mark_rolled_back_and_next(self):
        """T-CHK-13: a PASSED site rolled back by hand sends its P5 items back to FAILED."""
        write_plan(self.state, self.PID)
        p = os.path.join(self.state, 'plans', self.PID, 'items.json')
        items = json.load(open(p))
        items['items'][0]['status'] = 'DONE'
        json.dump(items, open(p, 'w'))
        self.assertEqual(PL.mark_rolled_back(self.state, self.PID, 'a.test', '20261026-000001'), 1)
        it = json.load(open(p))['items'][0]
        self.assertEqual((it['status'], it['reason']), ('FAILED', 'site_rolled_back 20261026-000001'))

    def test_switch_runs(self):
        index(self.state, [('20261026-000001', 'a.test', 'PASSED', self.PID, '-'),
                           ('20261026-000002', 'b.test', 'ROLLED_BACK', '-', '-')])
        self.assertEqual([r['run_id'] for r in PL.switch_runs(self.state, self.PID)], ['20261026-000001'])
        self.assertEqual(len(PL.switch_runs(self.state)), 2)


class CatalogActionTest(unittest.TestCase):
    def test_p2_p5_migrate_actions(self):
        items = json.load(open(os.path.join(ROOT, 'share', 'php-quickpatch', 'catalog', 'checklists.json')))['items']
        by = {i['chk_id']: i for i in items}
        self.assertEqual(by['CHK-PHP-010-16']['cli_action'], 'migrate install --runtime php --target $NEW --plan $PLAN_ID')
        self.assertEqual(by['CHK-PHP-010-23']['cli_action'], 'migrate switch $SITE --target $NEW --plan $PLAN_ID')
        self.assertEqual(by['CHK-NODE-010-05']['cli_action'], 'migrate install --runtime node --target $NEW --plan $PLAN_ID')
        self.assertIsNone(by['CHK-PHP-001-27']['cli_action'])          # new machine (DNS/upstream): guided
        self.assertIsNone(by['CHK-NODE-009-05']['cli_action'])          # nvm: guided
        self.assertIn('migrate', PL.WRITE_ACTIONS)


if __name__ == '__main__':
    unittest.main()
