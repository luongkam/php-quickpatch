"""`compat --path DIR --target N` (CR-01, qp.compat/1): compatibility of Node.js project directories.

Read only for the scanned paths. Writes the report (HTML and Markdown) and the
JSON result to STATE_DIR/reports/compat-<run_id>/, plus --report FILE when given.
"""
import json
import os
import re
import subprocess

from .. import assess as A, errors
from . import project as P, report as RP


def node_major(binary):
    try:
        p = subprocess.run([binary, '-v'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r'^v?(\d+)\.\d+\.\d+', p.stdout.decode('utf-8', 'replace').strip())
    return m.group(1) if m else None


def bad(arg):
    return errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg=arg)


def run(env, argv, Args, warnings, state_dir):
    a = Args(argv, flags=('--json', '--offline'),
             options=('--target', '--current', '--node-bin', '--report', '--lang', '--today', '--runtime'),
             multi=('--path',))
    if a.positional:
        raise errors.error('ERR-CLI-400-01', arg=a.positional[0])
    if (a.opts.get('--runtime') or 'node') != 'node':
        raise errors.error('ERR-CLI-400-01', '{arg} is not available in this build yet.',
                           arg='compat --runtime %s' % a.opts['--runtime'])
    target = a.opts.get('--target') or ''
    if not re.match(r'^\d{1,2}$', target):
        raise bad('--target')
    cur = a.opts.get('--current')
    if cur is not None and not re.match(r'^\d{1,2}$', cur):
        raise bad('--current')
    paths = a.multi['--path']
    if not paths:
        raise bad('--path')
    for p in paths:
        if not os.path.isdir(p):
            raise bad('--path %s' % p)
    lang = a.opts.get('--lang') or ('vi' if os.environ.get('QP_LANG') == 'vi' else 'en')
    if lang not in ('en', 'vi'):
        raise bad('--lang')
    node_bin = a.opts.get('--node-bin')
    if node_bin:
        if not (os.path.isfile(node_bin) and os.access(node_bin, os.X_OK)):
            raise bad('--node-bin')
        got = node_major(node_bin)
        if got != target:
            raise bad('--node-bin (Node.js %s, target %s)' % (got or '?', target))
        node_bin = os.path.realpath(node_bin)
    out_file = a.opts.get('--report')
    if out_file is not None:
        if not out_file.lower().endswith(('.html', '.htm', '.md')):
            raise bad('--report (.html or .md)')
        if not os.path.isdir(os.path.dirname(os.path.abspath(out_file))):
            raise bad('--report %s' % out_file)
    today = A.today_of(a)
    res = P.run(state_dir, paths, target, cur, node_bin, '--offline' in a.flags, lang, today, warnings=warnings)
    env.catalog_version = res['catalog_version']
    for p in res['projects']:
        for x in p['errors']:
            env.error(x['code'], x['message'], 'project:%s' % p['path'])
    d = res['artifacts_dir']
    res['reports'] = [RP.write(res, os.path.join(d, 'report.html'), lang),
                      RP.write(res, os.path.join(d, 'report.md'), lang)]
    if out_file:
        res['reports'].append(RP.write(res, os.path.abspath(out_file), lang))
    with open(os.path.join(d, 'result.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    worst = RP.overall(res)
    vul = sum(1 for p in res['projects'] for v in p['vulnerabilities'] or [] if not v['dev'])
    code = 0 if worst == 'PASS' and not vul and not res['summary']['deprecated'] and \
        not res['summary']['runtime_changes'] else 1
    if '--json' not in a.flags:
        print_text(res, lang)
    return code, res


def print_text(res, lang):
    lc = res.get('lifecycle')
    print('%s %s -> %s' % (RP.t('title', lang), res.get('current_branch') or '?', res['target_branch']))
    for _, msg in RP.lifecycle_lines(res, lang):
        print('  ' + msg)
    for p in res['projects']:
        v = p['verdict']
        print('%-30s %-10s vuln %d (%s), runtime %d, migrate %d, code %d/%d' % (
            p['name'], RP.t(v['status'], lang), v['vulnerable_packages'],
            ', '.join('%s %d' % (k, n) for k, n in sorted(v['by_severity'].items())) or '-',
            v['runtime_changes'], v['deprecated'], v['errors'], v['warnings']))
    if lc is None:
        print('  ' + RP.t('no_lifecycle', lang))
    for r in res['reports']:
        print('report: %s' % r)
