#!/usr/bin/env python3
"""php-quickpatch Python commands: feeds, assess, plan, report, audit.

Called by php-quickpatch.sh as
    python3 -I qp-feeds.py --script <path of php-quickpatch.sh> <command> [args]
Standard library only, Python 3.6+ (C-SRS-01).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qplib import audit, errors, statedir  # noqa: E402
from qplib.envelope import Envelope  # noqa: E402
from qplib.errors import QPError  # noqa: E402

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class Args(object):
    """Tiny option parser that reports ERR-CLI-400-01 like the Bash CLI."""

    def __init__(self, argv, flags=(), options=(), multi=()):
        self.raw = list(argv)
        self.flags = set()
        self.opts = {}
        self.multi = {m: [] for m in multi}
        self.positional = []
        i = 0
        while i < len(argv):
            a = argv[i]
            if a in flags:
                self.flags.add(a)
            elif a in options or a in multi:
                if i + 1 >= len(argv):
                    raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg=a)
                if a in multi:
                    self.multi[a].append(argv[i + 1])
                else:
                    self.opts[a] = argv[i + 1]
                i += 1
            elif a.startswith('-'):
                raise errors.error('ERR-CLI-400-01', arg=a)
            else:
                self.positional.append(a)
            i += 1

    def date(self, name):
        v = self.opts.get(name)
        if v is not None and not DATE_RE.match(v):
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg=name)
        return v


def cmd_audit(env, argv, warn):
    sub = argv[0] if argv else ''
    env.subcommand = sub or None
    if sub not in ('list', 'verify'):
        raise errors.error('ERR-CLI-400-01', arg='audit %s' % sub)
    a = Args(argv[1:], flags=('--json',), options=('--from', '--to', '--action', '--actor', '--page', '--limit'),
             multi=('--anchor',))
    if a.positional:
        raise errors.error('ERR-CLI-400-01', arg=a.positional[0])
    date_from, date_to = a.date('--from'), a.date('--to')
    state_dir = statedir.select(warn)
    if sub == 'list':
        recs = audit.list_records(state_dir, date_from, date_to, a.opts.get('--action'), a.opts.get('--actor'))
        if '--json' not in a.flags:
            for r in recs:
                print('%6d %s %-8s %-22s %-24s %s' % (r['seq'], r['ts'], r['record_type'], r['actor'],
                                                     r['action'], r['result'] or '-'))
            print('%d record(s)' % len(recs))
        return 0, {'records': recs, 'total': len(recs)}
    anchors = []
    for spec in a.multi['--anchor']:
        m = re.match(r'^([1-9][0-9]*):([0-9a-f]{64})$', spec)
        if not m:
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--anchor')
        anchors.append({'seq': int(m.group(1)), 'hash': m.group(2)})
    res = audit.verify(state_dir, anchors, date_from, date_to)
    if res['verified']:
        if '--json' not in a.flags:
            print('Audit chain OK: %d record(s), %d anchor(s) checked.' % (res['records'], len(res['anchors_checked'])))
        return 0, res
    msg = errors.message('ERR-AUD-409-01', seq=res['first_broken_seq'])
    env.error('ERR-AUD-409-01', msg, 'host')
    sys.stderr.write(msg + '\n')
    return 2, res


NOT_YET = {'report': 'M7'}
SCHEMAS = {'audit': 'qp.audit/1', 'assess': 'qp.assess/1', 'plan': 'qp.plan/1', 'report': 'qp.report/1',
           'feeds': 'qp.feeds/1', 'compat': 'qp.compat/1'}


def main(argv):
    if len(argv) >= 2 and argv[0] == '--script':
        os.environ['QP_SCRIPT'] = argv[1]
        argv = argv[2:]
    if not argv:
        sys.stderr.write('usage: qp-feeds.py --script PATH COMMAND [args]\n')
        return 2
    command, rest = argv[0], argv[1:]
    json_mode = '--json' in rest
    schema = SCHEMAS.get(command, 'qp.%s/1' % command)
    if command == 'feeds' and rest[:1] == ['status']:
        schema = 'qp.feeds.status/1'
    env = Envelope(schema, command, argv, subcommand=rest[0] if rest and not rest[0].startswith('-') else None,
                   dry_run='--dry-run' in rest)
    warnings = []
    code, result = 2, None
    try:
        if command == 'audit':
            code, result = cmd_audit(env, rest, warnings)
        elif command == 'feeds':
            from qplib.feeds import cli as feeds_cli
            code, result = feeds_cli.run(env, rest, warnings, Args)
        elif command == 'assess':
            from qplib import assess
            code, result = assess.run(env, rest, Args, warnings, statedir.select(warnings))
        elif command == 'compat':
            from qplib.compat import cli as compat_cli
            code, result = compat_cli.run(env, rest, Args, warnings, statedir.select(warnings))
        elif command == 'plan':
            from qplib import plan
            code, result = plan.run(env, rest, Args, warnings, statedir.select(warnings))
        elif command in ('osv-check', 'backport', 'risk', 'build-snapshot'):
            from qplib.feeds import tools
            code, result = tools.COMMANDS[command](env, rest, Args, warnings)
        elif command in NOT_YET:
            raise errors.error('ERR-CLI-400-01', '{arg} is not available in this build yet (milestone %s).' % NOT_YET[command],
                               arg=command)
        else:
            raise errors.error('ERR-CLI-400-01', arg=command)
    except QPError as e:
        env.error(e.code, e.message, 'host')
        detail = ' '.join('%s=%s' % kv for kv in sorted(e.details.items()))
        sys.stderr.write('%s [%s]%s\n' % (e.message, e.code, (' ' + detail) if detail else ''))
        code, result = e.exit_code, None
    except Exception as e:  # noqa: BLE001 - keep the --json contract on a bug
        import traceback
        traceback.print_exc()
        warnings.append((None, 'internal error: %s: %s' % (type(e).__name__, e)))
        code, result = 2, None
    for w in warnings:
        code_w, msg = w if isinstance(w, tuple) else (None, w)
        env.warning(code_w, msg)
        if not json_mode and command != 'feeds':
            sys.stderr.write('WARN: %s\n' % msg)
    if json_mode:
        env.emit(code, result)
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
