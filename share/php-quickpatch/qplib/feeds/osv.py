"""OSV lookups (SRC-007, SRC-014), distro trackers (SRC-015), local changelog (SRC-016).

library_check  FR-FEED-OSV-001: querybatch <= 500 per request, next_page_token,
               cache per lockfile sha256 for 6 h, stale cache <= 7 days when OSV
               fails (ERR-FEED-503-02), advisory details cached until `modified` changes.
backport       FR-FEED-DIST-001/002, FR-FEED-NORM-003, DOC-SRS-QP-FEED-002 §7 steps 0-5.
"""
import gzip
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request

from . import normalize, sources
from .http import FetchError, Fetcher, ssl_context
from .store import read_json, write_json

BATCH = 500
LIB_TTL = 6 * 3600
STALE_MAX = 7 * 86400
TRACKER_MAX = 50
CVE_RE = re.compile(r'CVE-\d{4}-\d{4,}')

ECOSYSTEMS = {('debian', '12'): 'Debian:12', ('debian', '13'): 'Debian:13',
              ('ubuntu', '24.04'): 'Ubuntu:24.04:LTS', ('ubuntu', '22.04'): 'Ubuntu:22.04:LTS',
              ('rhel', '8'): 'Red Hat', ('rhel', '9'): 'Red Hat',
              ('almalinux', '8'): 'AlmaLinux:8', ('almalinux', '9'): 'AlmaLinux:9',
              ('rocky', '8'): 'Rocky Linux:8', ('rocky', '9'): 'Rocky Linux:9'}
PREFIX = {'Ubuntu': 'UBUNTU-', 'Debian': 'DEBIAN-'}     # + CVE id: UBUNTU-CVE-2024-8926
UBUNTU_STATE = {'released': 'FIXED', 'needed': 'UNFIXED', 'deferred': 'UNFIXED', 'pending': 'UNFIXED',
                'not-affected': 'NOT_AFFECTED', 'DNE': 'UNKNOWN', 'ignored': 'UNFIXED', 'needs-triage': 'UNFIXED'}


def os_release(path='/etc/os-release'):
    info = {}
    try:
        with open(path) as f:
            for line in f:
                if '=' in line:
                    k, v = line.rstrip('\n').split('=', 1)
                    info[k] = v.strip('"')
    except OSError:
        pass
    return info


def ecosystem_of(info):
    osid, ver = info.get('ID', ''), info.get('VERSION_ID', '')
    if osid == 'alpine' and ver:
        return 'Alpine:v%s' % '.'.join(ver.split('.')[:2])
    major = ver.split('.')[0] if osid in ('rhel', 'almalinux', 'rocky', 'debian') else ver
    return ECOSYSTEMS.get((osid, major))


class Client(object):
    def __init__(self, fs, offline=False, now=time.time, sleep=time.sleep):
        self.fs = fs
        self.offline = offline
        self.now = now
        self.conf = sources.load(fs.root)
        self.fetcher = Fetcher(self.conf, deadline=None, sleep=sleep, now=now)

    def _cache_path(self, kind, key):
        safe = re.sub(r'[^A-Za-z0-9._@:+-]', '_', key)
        return self.fs.path('cache', kind, safe + '.json')

    def cache_get(self, kind, key, ttl):
        doc = read_json(self._cache_path(kind, key))
        if not doc:
            return None, None
        age = self.now() - doc.get('_cached_at', 0)
        return (doc.get('data'), age) if ttl is None or age <= ttl else (None, age)

    def cache_put(self, kind, key, data):
        p = self._cache_path(kind, key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        write_json(p, {'_cached_at': self.now(), 'data': data})

    def post_json(self, src, url, payload):
        resp = self.fetcher.request(src, url, headers={'Content-Type': 'application/json'},
                                    data=json.dumps(payload).encode(), method='POST')
        if resp.status != 200:
            raise FetchError('ERR-FEED-503-02', 'HTTP %d' % resp.status, http=resp.status)
        return resp.json()

    def get_json(self, src, url):
        resp = self.fetcher.request(src, url)
        if resp.status == 404:
            return None
        if resp.status != 200:
            raise FetchError('ERR-FEED-503-01', 'HTTP %d' % resp.status, http=resp.status)
        return resp.json()

    # --- querybatch with paging ---------------------------------------------
    def querybatch(self, src, queries):
        base = self.conf[src]['url'].rstrip('/')
        out = [[] for _ in queries]
        for i in range(0, len(queries), BATCH):
            chunk = queries[i:i + BATCH]
            pending = list(range(len(chunk)))
            tokens = {}
            while pending:
                body = {'queries': [dict(chunk[j], page_token=tokens[j]) if j in tokens else chunk[j] for j in pending]}
                doc = self.post_json(src, base + '/querybatch', body)
                res = doc.get('results') or []
                if len(res) != len(pending):            # SRC-007 integrity: one result per query
                    raise FetchError('ERR-FEED-503-02', 'querybatch returned %d results for %d queries'
                                     % (len(res), len(pending)))
                nxt = []
                for j, r in zip(pending, res):
                    out[i + j].extend(r.get('vulns') or [])
                    if r.get('next_page_token'):
                        tokens[j] = r['next_page_token']
                        nxt.append(j)
                pending = nxt
        return out

    def vuln(self, src, vid, modified=None):
        """Advisory detail, cached until `modified` changes."""
        cached, _ = self.cache_get('osv-vulns', vid, None)
        if cached is not None and (modified is None or cached.get('modified') == modified):
            return cached
        if self.offline:
            return cached
        base = self.conf[src]['url'].rstrip('/')
        doc = self.get_json(src, '%s/vulns/%s' % (base, vid))
        if doc is not None:
            self.cache_put('osv-vulns', vid, doc)
        return doc


def _severity(doc, kev):
    scores = []
    for s in doc.get('severity') or []:
        m = re.search(r'CVSS:(\d\.\d)/', str(s.get('score', '')))
        if m:
            scores.append({'source': 'OSV', 'cvss_version': m.group(1), 'type': None, 'base_score': None,
                           'vector': s['score'], 'severity_text': None})
    sev = ((doc.get('database_specific') or {}).get('severity') or '').lower()
    sev = {'moderate': 'medium'}.get(sev, sev)
    if sev in normalize.PROXY:
        return sev, normalize.PROXY[sev]
    return 'unknown', normalize.PROXY['unknown']


def _fixed_versions(doc, eco, name):
    out = []
    for a in doc.get('affected') or []:
        pk = a.get('package') or {}
        if pk.get('ecosystem') != eco or pk.get('name') != name:
            continue
        for r in a.get('ranges') or []:
            for ev in r.get('events') or []:
                if 'fixed' in ev and ev['fixed'] not in out:
                    out.append(ev['fixed'])
    return out


def library_check(fs, ecosystem, lockfile, packages, offline=False, kev_ids=(), now=time.time):
    """packages: [(name, version)]. Returns (findings, meta) or raises FetchError ERR-FEED-503-02."""
    client = Client(fs, offline=offline, now=now)
    try:
        with open(lockfile, 'rb') as f:
            lock_sha = hashlib.sha256(f.read()).hexdigest()
    except OSError:
        lock_sha = hashlib.sha256('\n'.join('%s %s' % p for p in packages).encode()).hexdigest()
    key = '%s-%s' % (ecosystem, lock_sha)
    cached, age = client.cache_get('osv', key, LIB_TTL)
    origin = 'CACHE'
    if cached is None:
        stale, sage = client.cache_get('osv', key, STALE_MAX)
        if offline:
            if stale is None:
                raise FetchError('ERR-FEED-503-02', 'offline and no cached OSV result')
            cached, age = stale, sage
        else:
            try:
                hits = client.querybatch('SRC-007', [{'package': {'name': n, 'ecosystem': ecosystem}, 'version': v}
                                                     for n, v in packages])
                cached = {'lock_sha256': lock_sha, 'results': [
                    {'name': n, 'version': v, 'vulns': h} for (n, v), h in zip(packages, hits) if h]}
                client.cache_put('osv', key, cached)
                origin, age = 'PRIMARY', 0
            except FetchError as e:
                if stale is None:
                    raise FetchError('ERR-FEED-503-02', 'OSV unavailable (%s) and no cached result <= 7 days'
                                     % e.message, http=e.http)
                cached, age = stale, sage
    findings = []
    kev = set(kev_ids)
    for r in cached['results']:
        ids, sev_best, score_best, in_kev, fixed, mal = [], 'low', 0.0, False, [], False
        for v in r['vulns']:
            vid = v['id']
            ids.append(vid)
            if vid.startswith('MAL-'):
                mal = True
                continue
            try:
                doc = client.vuln('SRC-007', vid, v.get('modified')) or {}
            except FetchError:
                doc = {}
            sev, score = _severity(doc, kev)
            if score > score_best:
                sev_best, score_best = sev, score
            if any(a in kev for a in doc.get('aliases') or []):
                in_kev = True
            for f in _fixed_versions(doc, ecosystem, r['name']):
                if f not in fixed:
                    fixed.append(f)
        findings.append({'package': r['name'], 'version': r['version'], 'advisories': ids,
                         'severity': 'critical' if mal else (sev_best if ids else 'low'), 'in_kev': in_kev,
                         'is_malware': mal, 'fixed_versions': fixed})
    return findings, {'lock_sha256': lock_sha, 'origin': origin, 'age_h': int((age or 0) // 3600)}


# --- distro backport (§7) ---------------------------------------------------------
def source_package(manager, package):
    try:
        if manager == 'dpkg':
            out = subprocess.run(['dpkg-query', '-W', '-f=${source:Package}', package], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=10).stdout.decode().strip()
            return out or package
        if manager == 'rpm':
            out = subprocess.run(['rpm', '-q', '--qf', '%{SOURCERPM}', package], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, timeout=10).stdout.decode().strip()
            m = re.match(r'^(.+)-[^-]+-[^-]+\.src\.rpm$', out)
            return m.group(1) if m else package
        if manager == 'apk':
            out = subprocess.run(['apk', 'info', '-o', package], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 timeout=10).stdout.decode()
            m = re.search(r'origin:\s*(\S+)|^(\S+)$', out, re.M)
            return package if not m else (m.group(1) or m.group(2))
    except (OSError, subprocess.SubprocessError):
        pass
    return package


def local_changelog(manager, package, src_package):
    """SRC-016: text of the installed package changelog ('' when unreadable)."""
    try:
        if manager == 'dpkg':
            for name in (package, src_package):
                p = '/usr/share/doc/%s/changelog.Debian.gz' % name
                if os.path.isfile(p):
                    with gzip.open(p, 'rb') as f:
                        return f.read().decode('utf-8', 'replace')
        elif manager == 'rpm':
            return subprocess.run(['rpm', '-q', '--changelog', package], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, timeout=10).stdout.decode('utf-8', 'replace')
    except (OSError, subprocess.SubprocessError):
        pass
    return ''


def _cve_of(vid, doc=None):
    for pre in ('UBUNTU-', 'DEBIAN-'):
        if vid.startswith(pre + 'CVE-'):
            return vid[len(pre):]
    if vid.startswith('CVE-'):
        return vid
    ids = list((doc or {}).get('upstream') or []) + list((doc or {}).get('aliases') or [])
    return [i for i in ids if CVE_RE.fullmatch(i)]


def backport(fs, manager, package, version, cves, offline=False, info=None, now=time.time, sleep=time.sleep):
    """Per-CVE state FIXED / UNFIXED / NOT_AFFECTED / UNKNOWN and the overall state (§7 step 5)."""
    info = info if info is not None else os_release()
    client = Client(fs, offline=offline, now=now, sleep=sleep)
    src_pkg = source_package(manager, package)
    eco = ecosystem_of(info)
    states = {c: None for c in cves}
    origin = {}
    fixed_ver = {}
    errors_seen = []
    # Step 1: querybatch on (source package, full version).
    if eco and not offline and manager in ('dpkg', 'rpm', 'apk'):
        key = '%s/%s@%s' % (eco, src_pkg, version)
        cached, _ = client.cache_get('osv-distro', key, LIB_TTL)
        try:
            if cached is None:
                hits = client.querybatch('SRC-014', [{'package': {'name': src_pkg, 'ecosystem': eco},
                                                      'version': version}])[0]
                cached = {'vulns': hits}
                client.cache_put('osv-distro', key, cached)
            unfixed = set()
            for v in cached['vulns']:
                c = _cve_of(v['id'])
                if isinstance(c, list):
                    try:
                        doc = client.vuln('SRC-014', v['id'], v.get('modified')) or {}
                    except FetchError:
                        doc = {}
                    c = _cve_of(v['id'], doc)
                for x in ([c] if isinstance(c, str) else c):
                    unfixed.add(x)
            for c in cves:
                if c in unfixed:
                    states[c], origin[c] = 'UNFIXED', 'OSV'
            # Step 2: per-CVE distro record.
            pre = next((p for k, p in PREFIX.items() if eco.startswith(k)), None)
            for c in cves:
                if states[c] or not pre:
                    continue
                try:
                    doc = client.vuln('SRC-014', pre + c)
                except FetchError:
                    doc = None
                if not doc:
                    continue
                for a in doc.get('affected') or []:
                    pk = a.get('package') or {}
                    if pk.get('ecosystem') == eco and pk.get('name') == src_pkg:
                        fx = _fixed_versions(doc, eco, src_pkg)
                        states[c], origin[c] = 'FIXED', 'OSV'
                        if fx:
                            fixed_ver[c] = fx[-1]
                        break
        except FetchError as e:
            errors_seen.append(e.code)
    # Step 3: Ubuntu / Red Hat trackers (<= 50 requests, 1 request/s).
    osid = info.get('ID', '')
    asked = 0
    if not offline:
        for c in cves:
            if states[c] or asked >= TRACKER_MAX:
                continue
            asked += 1
            try:
                if osid == 'ubuntu':
                    st = _ubuntu_tracker(client, c, src_pkg, info.get('VERSION_CODENAME', ''))
                    if st:
                        states[c], origin[c] = st, 'UBUNTU_API'
                elif osid in ('rhel', 'almalinux', 'rocky', 'centos'):
                    st = _redhat_tracker(client, c, src_pkg, info.get('VERSION_ID', '').split('.')[0])
                    if st:
                        states[c], origin[c] = st, 'REDHAT_API'
            except FetchError as e:
                errors_seen.append(e.code)
    # Step 4: local changelog.
    text = None
    for c in cves:
        if states[c]:
            continue
        if text is None:
            text = local_changelog(manager, package, src_pkg)
        if c in text:
            states[c], origin[c] = 'FIXED', 'LOCAL_CHANGELOG'
        else:
            states[c], origin[c] = 'UNKNOWN', 'LOCAL_CHANGELOG'
    vals = [states[c] for c in cves]
    if not cves or all(s in ('FIXED', 'NOT_AFFECTED') for s in vals):
        overall = 'ok-backport'
    else:
        overall = 'vulnerable'
    return {'state': overall, 'unknown_only': overall == 'vulnerable' and 'UNFIXED' not in vals,
            'ecosystem': eco, 'src_package': src_pkg, 'version': version,
            'cves': [{'adv_id': c, 'state': states[c], 'origin': origin.get(c), 'fixed_version': fixed_ver.get(c)}
                     for c in cves], 'errors': sorted(set(errors_seen))}


def _ubuntu_tracker(client, cve, src_pkg, codename):
    key = 'ubuntu/%s' % cve
    doc, _ = client.cache_get('tracker', key, 86400)
    if doc is None:
        url = client.conf['SRC-015']['url'].rstrip('/') + '/%s.json' % cve
        client.conf['SRC-015']['timeout_s'] = 60
        doc = client.get_json('SRC-015', url) or {}
        client.cache_put('tracker', key, doc)
    for p in doc.get('packages') or []:
        if p.get('name') != src_pkg:
            continue
        for s in p.get('statuses') or []:
            if s.get('release_codename') == codename:
                return UBUNTU_STATE.get(s.get('status'), 'UNKNOWN')
    return None


def _redhat_tracker(client, cve, src_pkg, major):
    key = 'redhat/%s' % cve
    doc, _ = client.cache_get('tracker', key, 86400)
    if doc is None:
        url = client.conf['SRC-015']['mirror_url'].rstrip('/') + '/%s.json' % cve
        client.conf['SRC-015']['timeout_s'] = 20
        doc = client.get_json('SRC-015', url) or {}    # 404 -> no data, never "not affected"
        client.cache_put('tracker', key, doc)
    tag = 'el%s' % major
    for r in doc.get('affected_release') or []:
        if str(r.get('package', '')).startswith(src_pkg + '-') and tag in str(r.get('package', '')):
            return 'FIXED'
    for s in doc.get('package_state') or []:
        if s.get('package_name') == src_pkg and ('enterprise_linux:%s' % major) in str(s.get('cpe', '')):
            st = s.get('fix_state')
            return {'Not affected': 'NOT_AFFECTED', 'Affected': 'UNFIXED', 'Fix deferred': 'UNFIXED',
                    'Will not fix': 'UNFIXED', 'Out of support scope': 'UNFIXED'}.get(st, 'UNKNOWN')
    return None


PACKAGIST_ALL = 'https://osv-vulnerabilities.storage.googleapis.com/Packagist/all.zip'


def download_packagist_all(fs, url=PACKAGIST_ALL):
    """Variant `full` of the snapshot (§4.4): the Packagist OSV export."""
    if not url.startswith('https://'):
        raise FetchError('ERR-FEED-503-02', 'non-HTTPS URL refused')
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context()))
    with opener.open(urllib.request.Request(url, headers={'User-Agent': 'php-quickpatch'}), timeout=120) as r:
        return r.read()
