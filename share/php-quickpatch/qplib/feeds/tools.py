"""Internal qp-feeds.py commands used by php-quickpatch.sh and the release pipeline.

osv-check      FR-FEED-OSV-001: stdin "name version" lines -> TSV findings
backport       FR-FEED-DIST-001/002: distro backport chain for one package
risk           FR-ASMT-RISK-001: R of one product version (same result as the Bash CLI)
build-snapshot FR-FEED-SNAP-004: full sync in a private directory, release gate, export
"""
import json
import os
import shutil
import sys
import tempfile
import time

from .. import errors, statedir
from . import osv, snapshot, sources, sync
from .http import FetchError
from .query import Bundle
from .store import FeedsDir


def cmd_osv_check(env, argv, Args, warnings):
    a = Args(argv, flags=('--offline', '--json'), options=('--ecosystem', '--lockfile'))
    eco = a.opts.get('--ecosystem')
    if eco not in ('npm', 'Packagist'):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--ecosystem')
    pkgs = []
    for line in sys.stdin:
        parts = line.split()
        if len(parts) == 2:
            pkgs.append((parts[0], parts[1]))
    fs = FeedsDir(statedir.select([]))
    kev = []
    try:
        with Bundle(fs) as b:
            kev = [r['cve_id'] for r in b.tsv('kev.tsv')]
    except LookupError:
        pass
    try:
        findings, meta = osv.library_check(fs, eco, a.opts.get('--lockfile') or '', pkgs,
                                           offline='--offline' in a.flags, kev_ids=kev)
    except FetchError as e:
        sys.stderr.write('%s [%s]\n' % (e.message, 'ERR-FEED-503-02'))
        return 3, None
    for f in findings:
        print('\t'.join([f['package'], f['version'], ','.join(f['advisories']), f['severity'],
                         '1' if f['in_kev'] else '0', '1' if f['is_malware'] else '0', ','.join(f['fixed_versions'])]))
    if meta['origin'] != 'PRIMARY':
        sys.stderr.write('osv: cached result (%d h old)\n' % meta['age_h'])
    return 0, None


def cmd_backport(env, argv, Args, warnings):
    a = Args(argv, flags=('--offline', '--json'), options=('--manager', '--package', '--version', '--cves'))
    for k in ('--manager', '--package', '--version'):
        if not a.opts.get(k):
            raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg=k)
    cves = [c for c in (a.opts.get('--cves') or '').split(',') if c]
    fs = FeedsDir(statedir.select([]))
    res = osv.backport(fs, a.opts['--manager'], a.opts['--package'], a.opts['--version'], cves,
                       offline='--offline' in a.flags)
    if '--json' in a.flags:
        return 0, res
    print(res['state'] + ('\tunknown' if res['unknown_only'] else ''))
    for c in res['cves']:
        print('\t'.join([c['adv_id'], c['state'], c['origin'] or '', c['fixed_version'] or '']))
    return 0, res


def cmd_risk(env, argv, Args, warnings):
    a = Args(argv, flags=('--json',), options=('--product', '--version', '--today', '--exclude'))
    product, version = a.opts.get('--product'), a.opts.get('--version')
    if product not in ('php', 'node', 'wordpress') or not version:
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--product/--version')
    today = a.date('--today') or time.strftime('%Y-%m-%d', time.gmtime())
    fs = FeedsDir(statedir.select([]))
    try:
        b = Bundle(fs)
    except LookupError:
        raise errors.error('ERR-FEED-503-01', 'No bundle: run feeds update or import a snapshot.', source='feeds',
                           origin='-', age_h='-')
    with b:
        res = b.assess(product, version, today, exclude=[x for x in (a.opts.get('--exclude') or '').split(',') if x])
        level, age, stale, _ = b.freshness()
        env.data = {'bundle_id': b.bundle_id, 'freshness': level, 'data_age_h': age, 'stale_sources': stale}
    if '--json' not in a.flags:
        r = res['risk']
        print('%s %s: %s, %s, R=%d %s (%s)' % (product, version, res['lifecycle_status'], res['priority'], r['R'],
                                               r['level'], json.dumps(r['components'], sort_keys=True)))
    return 0, res


def gate(manifest, fs):
    """BR-FEED-058: P0 sources OK, KR5.1 coverage. Returns the list of failures."""
    bad = []
    st = {s['src_id']: s for s in manifest.get('sources', [])}
    for src in sources.P0_SOURCES:
        if (st.get(src) or {}).get('status') != 'OK':
            bad.append('%s is %s' % (src, (st.get(src) or {}).get('status', 'missing')))
    with Bundle(fs) as b:
        php = {r['branch'] for r in b.tsv('lifecycle.tsv') if r['product'] == 'php'}
        node = {r['branch'] for r in b.tsv('lifecycle.tsv') if r['product'] == 'node'}
    want_php = {'4.4', '5.0', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '7.0', '7.1', '7.2', '7.3', '7.4', '8.0',
                '8.1', '8.2', '8.3', '8.4', '8.5'}
    want_node = {str(n) for n in range(4, 27)}
    if want_php - php:
        bad.append('PHP branches missing: %s' % ', '.join(sorted(want_php - php)))
    if want_node - node:
        bad.append('Node.js branches missing: %s' % ', '.join(sorted(want_node - node, key=int)))
    return bad


def cmd_build_snapshot(env, argv, Args, warnings):
    a = Args(argv, flags=('--json', '--no-gate'), options=('--variant', '--out', '--budget'))
    out = a.opts.get('--out')
    variant = a.opts.get('--variant', 'standard')
    if not out or variant not in ('standard', 'full') or os.path.lexists(out):
        raise errors.error('ERR-CLI-400-01', 'Invalid or missing value for {arg}.', arg='--out/--variant')
    work = tempfile.mkdtemp(prefix='qp-build-snapshot-')
    try:
        os.environ.pop('QP_FEEDS_BUNDLE', None)
        code, res, w = sync.run(work, force=True, budget=int(a.opts.get('--budget') or 3600))
        warnings.extend(w)
        fs = FeedsDir(work)
        with Bundle(fs) as b:
            manifest = b.manifest
        failures = [] if '--no-gate' in a.flags else gate(manifest, fs)
        if failures:
            for f in failures:
                env.error('ERR-FEED-503-01', 'release gate: %s' % f, 'snapshot')
                sys.stderr.write('release gate: %s\n' % f)
            return 2, {'gate': failures, 'sync': res}
        extra = {}
        if variant == 'full':
            extra['osv/Packagist-all.zip'] = osv.download_packagist_all(fs)
        exp = snapshot.export(fs, out, variant=variant, built_by='release-pipeline', extra=extra)
        if '--json' not in a.flags:
            print('Snapshot %s\nsha256 %s\nQP_SNAPSHOT_SHA256=%s' % (exp['file'], exp['sha256'], exp['sha256']))
        return 0, dict(exp, gate=[], sync=res)
    finally:
        shutil.rmtree(work, ignore_errors=True)


COMMANDS = {'osv-check': cmd_osv_check, 'backport': cmd_backport, 'risk': cmd_risk,
            'build-snapshot': cmd_build_snapshot}
