"""Read side of a bundle for Python commands (risk, assess, console).

Resolves `current` once and keeps the shared lock (DOC-SRS-QP-FEED-003 §2.5).
"""
import os
import sqlite3

from . import normalize, risk as R, versions as V
from .bundle import current, read_tsv
from .status import freshness


class Bundle(object):
    def __init__(self, fs):
        self.ref = current(fs)
        if self.ref is None:
            raise LookupError('no bundle')
        self.path = self.ref['path']
        self.manifest = self.ref['manifest']
        self.bundle_id = self.manifest['bundle_id']
        self._tsv = {}
        self._adv = None

    def close(self):
        self.ref['release']()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def tsv(self, name):
        if name not in self._tsv:
            self._tsv[name] = read_tsv(os.path.join(self.path, name))
        return self._tsv[name]

    def freshness(self, now=None):
        return freshness(self.manifest.get('sources', []), now)

    def lifecycle(self, product, branch):
        return next((r for r in self.tsv('lifecycle.tsv') if r['product'] == product and r['branch'] == branch), None)

    def min_patched(self, product, branch):
        return next((r for r in self.tsv('min_patched.tsv') if r['product'] == product and r['branch'] == branch), None)

    def releases(self, product, branch=None):
        return [r for r in self.tsv('releases.tsv') if r['product'] == product and (branch is None or r['branch'] == branch)]

    def advisories(self):
        """Advisory dicts with selected ranges (for matching versions not in exposure.tsv)."""
        if self._adv is None:
            db = sqlite3.connect('file:%s?mode=ro' % os.path.join(self.path, 'feeds.db'), uri=True)
            try:
                adv = {}
                for row in db.execute('SELECT adv_id, kind, status, cvss_rep, in_kev, products FROM advisory'):
                    adv[row[0]] = {'adv_id': row[0], 'kind': row[1], 'status': row[2],
                                   'cvss_rep': '%.1f' % row[3] if row[3] is not None else None, 'in_kev': row[4],
                                   'products': row[5].split(','), 'sel': {}}
                for row in db.execute('SELECT adv_id, product, origin, v_start, start_incl, v_end, end_incl, v_exact, '
                                      'platform, unbounded, semver_vulnerable, semver_patched, v_prefix FROM affected_range '
                                      'WHERE used = 1'):
                    a = adv.get(row[0])
                    if a is None:
                        continue
                    a['sel'].setdefault(row[1], []).append(
                        {'origin': row[2], 'v_start': row[3], 'start_incl': row[4], 'v_end': row[5], 'end_incl': row[6],
                         'v_exact': row[7], 'platform': row[8], 'unbounded': row[9], 'semver_vulnerable': row[10],
                         'semver_patched': row[11], 'prefix': row[12], 'product': row[1]})
                self._adv = list(adv.values())
            finally:
                db.close()
        return self._adv

    def exposure(self, product, version, exclude=()):
        """Summary of unpatched advisories for PRODUCT VERSION; EXCLUDE = ids fixed by a backport."""
        hits = None
        if not exclude:
            row = next((r for r in self.tsv('exposure.tsv') if r['product'] == product and r['version'] == version), None)
            if row:
                cvss10 = int(row['cvss_max'].replace('.', '')) if row.get('cvss_max') else 0
                return {'n_crit': int(row['n_crit']), 'n_high': int(row['n_high']), 'n_med': int(row['n_med']),
                        'n_low': int(row['n_low']), 'cvss10': cvss10, 'cvss_max': row['cvss_max'],
                        'n_kev': int(row['n_kev']), 'adv_ids': (row.get('adv_ids') or '').split(',') if row.get('adv_ids') else []}
        hits = normalize.exposure_of(self.advisories(), product, version)
        hits = [a for a in hits if a['adv_id'] not in set(exclude)]
        return normalize.summarize(hits)

    def assess(self, product, version, today, exclude=(), public_prerelease=False):
        """lifecycle_status, priority, R (FR-ASMT-RISK-001) of one version."""
        branch = V.branch_of(product, version)
        lc = self.lifecycle(product, branch)
        mp = self.min_patched(product, branch)
        wp = None
        if product == 'wordpress':
            rels = self.releases('wordpress')
            newest = V.branch_of('wordpress', V.vmax(r['version'] for r in rels)) if rels else None
            wp = {'newest_branch': newest, 'min_patched': (mp or {}).get('min_patched_sec'),
                  'has_supported': any(r['wp_status'] in ('latest', 'outdated') for r in rels if r['branch'] == branch)}
        status = R.lifecycle_status(product, lc, version, today, wp)
        d = R.days_to_eol((lc or {}).get('eol_date'), today)
        exp = self.exposure(product, version, exclude)
        sc = R.score(status, d, exp['n_crit'], exp['n_high'], exp['n_med'], exp['n_low'], exp['n_kev'], exp['cvss10'],
                     public_prerelease)
        return {'product': product, 'version': version, 'branch': branch, 'lifecycle_status': status,
                'eol_date': (lc or {}).get('eol_date'), 'days_to_eol': d, 'priority': sc['priority'],
                'min_patched': (mp or {}).get('min_patched_sec'), 'latest': (mp or {}).get('latest'),
                'driver_ids': ((mp or {}).get('driver_ids') or '').split(',') if (mp or {}).get('driver_ids') else [],
                'exposure': exp, 'risk': {'R': sc['R'], 'score': sc['R'], 'level': sc['level'], 'components': sc['components']},
                'bundle_id': self.bundle_id}
