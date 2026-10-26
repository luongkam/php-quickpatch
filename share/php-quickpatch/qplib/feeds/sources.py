"""Catalog of the 17 data sources and their configuration (DOC-SRS-QP-FEED-001 §3, FEED-003 §2.4).

feeds/sources.conf (INI, no secrets) may override per source: enabled,
ttl_hours, url, mirror_url, timeout_s, min_interval_s, retry_delays (seconds,
comma list), page_size. Every URL must be https:// (BR-FEED-016).
feeds.conf (mode 0600, BR-FEED-011) or QP_* variables hold API keys.
"""
import os
import stat

ROLES = {'primary': 'ERR-FEED-503-01', 'secondary': 'ERR-FEED-503-03',
         'fallback': 'ERR-FEED-503-03', 'optional': 'ERR-FEED-503-03'}

# Sync order of DIAG-SEQ-QP-FEED-001 (FEED-003 §5.1).
SYNC_ORDER = ['SRC-006', 'SRC-002', 'SRC-009', 'SRC-012', 'SRC-011', 'SRC-004', 'SRC-001', 'SRC-010',
              'SRC-003', 'SRC-008', 'SRC-013']

SOURCES = {
    'SRC-001': dict(name='endoflife.date', role='primary', ttl_hours=24, timeout_s=30, min_interval_s=1,
                    url='https://endoflife.date/api', mirror_url='https://raw.githubusercontent.com/endoflife-date/endoflife.date/master/products'),
    'SRC-002': dict(name='php.net releases', role='primary', ttl_hours=6, timeout_s=30, min_interval_s=1,
                    url='https://www.php.net/releases',
                    prerelease_url='https://www.php.net/pre-release-builds.php?format=json'),
    'SRC-003': dict(name='php.net ChangeLog/NEWS', role='secondary', ttl_hours=24, timeout_s=60, min_interval_s=1,
                    url='https://www.php.net', mirror_url='https://raw.githubusercontent.com/php/php-src'),
    'SRC-004': dict(name='NVD CVE API 2.0', role='primary', ttl_hours=6, timeout_s=180, min_interval_s=6,
                    url='https://services.nvd.nist.gov/rest/json/cves/2.0', page_size=200,
                    retry_delays='30,60,120'),
    'SRC-005': dict(name='CVE.org CVE Services', role='fallback', ttl_hours=24, timeout_s=20, min_interval_s=1,
                    url='https://cveawg.mitre.org/api/cve'),
    'SRC-006': dict(name='CISA KEV', role='primary', ttl_hours=6, timeout_s=60, min_interval_s=0,
                    url='https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
                    mirror_url='https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json'),
    'SRC-007': dict(name='OSV (Packagist, npm)', role='primary', ttl_hours=6, timeout_s=60, min_interval_s=0,
                    url='https://api.osv.dev/v1'),
    'SRC-008': dict(name='GitHub Security Advisories', role='secondary', ttl_hours=6, timeout_s=30, min_interval_s=0,
                    url='https://api.github.com/repos/php/php-src/security-advisories'),
    'SRC-009': dict(name='nodejs.org release index', role='primary', ttl_hours=6, timeout_s=60, min_interval_s=0,
                    url='https://nodejs.org/dist/index.json'),
    'SRC-010': dict(name='nodejs/Release schedule', role='primary', ttl_hours=24, timeout_s=30, min_interval_s=0,
                    url='https://raw.githubusercontent.com/nodejs/Release/main/schedule.json'),
    'SRC-011': dict(name='Node.js Security WG', role='primary', ttl_hours=6, timeout_s=30, min_interval_s=0,
                    url='https://raw.githubusercontent.com/nodejs/security-wg/main/vuln/core/index.json'),
    'SRC-012': dict(name='WordPress.org core API', role='primary', ttl_hours=6, timeout_s=30, min_interval_s=0,
                    url='https://api.wordpress.org/core'),
    'SRC-013': dict(name='WordPress vuln DB (key)', role='optional', ttl_hours=24, timeout_s=120, min_interval_s=1,
                    url='https://www.wordfence.com/api/intelligence/v3/vulnerabilities/production', enabled=0),
    'SRC-014': dict(name='OSV (distro)', role='primary', ttl_hours=6, timeout_s=60, min_interval_s=0,
                    url='https://api.osv.dev/v1'),
    'SRC-015': dict(name='Distro trackers', role='fallback', ttl_hours=24, timeout_s=60, min_interval_s=1,
                    url='https://ubuntu.com/security/cves', mirror_url='https://access.redhat.com/hydra/rest/securitydata/cve'),
    'SRC-016': dict(name='Local package changelog', role='fallback', ttl_hours=0, timeout_s=10, min_interval_s=0, url=''),
    'SRC-017': dict(name='Offline snapshot', role='fallback', ttl_hours=0, timeout_s=0, min_interval_s=0, url=''),
}
# Sources refreshed by `feeds update` on a schedule (the others are on demand).
SCHEDULED = ['SRC-001', 'SRC-002', 'SRC-003', 'SRC-004', 'SRC-006', 'SRC-008', 'SRC-009', 'SRC-010',
             'SRC-011', 'SRC-012', 'SRC-013']
ON_DEMAND = ['SRC-005', 'SRC-007', 'SRC-014', 'SRC-015']
# Release gate (BR-FEED-058): P0 sources that must be OK in a snapshot build.
P0_SOURCES = ['SRC-001', 'SRC-002', 'SRC-004', 'SRC-006', 'SRC-009', 'SRC-010', 'SRC-011', 'SRC-012']

KEY_NAMES = {'NVD_API_KEY': 'SRC-004', 'GITHUB_TOKEN': 'SRC-008', 'WORDFENCE_API_KEY': 'SRC-013',
             'WPSCAN_API_TOKEN': 'SRC-013', 'PATCHSTACK_API_KEY': 'SRC-013'}
ENV_ALIASES = {'NVD_API_KEY': 'QP_NVD_API_KEY', 'GITHUB_TOKEN': 'QP_GITHUB_TOKEN',
               'WORDFENCE_API_KEY': 'QP_WORDFENCE_KEY', 'WPSCAN_API_TOKEN': 'QP_WPSCAN_TOKEN',
               'PATCHSTACK_API_KEY': 'QP_PATCHSTACK_KEY'}


class ConfigError(ValueError):
    pass


def _parse_ini(path):
    out, cur = {}, None
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                cur = line[1:-1].strip()
                out.setdefault(cur, {})
            elif '=' in line and cur:
                k, v = line.split('=', 1)
                out[cur][k.strip()] = v.strip()
    return out


def load(feeds_dir):
    """Effective per-source settings: defaults + feeds/sources.conf overrides."""
    conf = {}
    for sid, s in SOURCES.items():
        c = dict(enabled=1, retry_delays='5,15,45', page_size=200, mirror_url='')
        c.update(s)
        conf[sid] = c
    for sid in conf:
        conf[sid]['enabled'] = int(SOURCES[sid].get('enabled', 1))
    path = os.path.join(feeds_dir, 'sources.conf')
    if os.path.isfile(path):
        for sid, values in _parse_ini(path).items():
            if sid not in conf:
                continue
            for k, v in values.items():
                if k in ('enabled', 'ttl_hours', 'page_size'):
                    conf[sid][k] = int(v)
                elif k in ('timeout_s', 'min_interval_s'):
                    conf[sid][k] = float(v)
                elif k in ('url', 'mirror_url', 'retry_delays', 'prerelease_url'):
                    conf[sid][k] = v
    for sid, c in conf.items():
        for k in ('url', 'mirror_url', 'prerelease_url'):
            if c.get(k) and not c[k].startswith('https://'):
                c['config_error'] = 'non-https %s %s' % (k, c[k])
        c['retry'] = [float(x) for x in str(c['retry_delays']).split(',') if x.strip() != '']
    return conf


def load_keys(config_paths, warnings):
    """API keys: QP_* variables override feeds.conf; a file wider than 0600 is ignored."""
    keys = {}
    for path in config_paths:
        if not path or not os.path.isfile(path):
            continue
        mode = stat.S_IMODE(os.stat(path).st_mode)
        if mode & 0o077:
            warnings.append('%s has mode %o (wider than 0600): its keys are ignored' % (path, mode))
            continue
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if v.strip():
                        keys[k.strip()] = v.strip()
        break
    for k, env in ENV_ALIASES.items():
        if os.environ.get(env):
            keys[k] = os.environ[env]
    return keys


def key_config_paths():
    if os.geteuid() == 0:
        return ['/etc/php-quickpatch/feeds.conf']
    home = os.environ.get('HOME', '')
    return [os.path.join(home, '.config', 'php-quickpatch', 'feeds.conf')] if home else []
