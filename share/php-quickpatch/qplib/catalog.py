"""Scenario catalog (FR-SCN-CAT-001): packaged share/php-quickpatch/catalog or
STATE_DIR/feeds/catalog imported from a snapshot, whichever is valid and newer.

A catalog is valid when SHA256SUMS lists and matches every file of FILES and
the JSON files have their required keys (ERR-FEED-422-02 / ERR-FEED-502-02);
an invalid catalog never replaces the one in use. Same rules as catalog_open
in php-quickpatch.sh.
"""
import csv
import hashlib
import json
import os
import re
import shutil

FILES = ['scenarios.json', 'checklists.json', 'playbooks.json', 'bc_rules.json', 'mitigations.json',
         'framework_php.tsv', 'catalog.json']
VERSION_RE = re.compile(r'^\d{4}\.\d{2}\.\d{2}-\d+$')
PACKAGED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'catalog')
REQUIRED_KEYS = {'scenarios.json': 'scenarios', 'checklists.json': 'items', 'playbooks.json': 'playbooks',
                 'bc_rules.json': 'rules', 'mitigations.json': 'rules'}
ITEM_KEYS = ('chk_id', 'scenario_id', 'phase', 'action', 'exec_type', 'check_mechanism', 'done_criteria')
PB_ACTIONS = ('inventory', 'patch', 'install', 'switch', 'rollback')


class CatalogError(Exception):
    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def vkey(v):
    return tuple(int(x) for x in re.findall(r'\d+', v or ''))


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def check(d):
    """Validate the catalog in D; return its catalog_version or raise CatalogError."""
    sums = os.path.join(d, 'SHA256SUMS')
    if not os.path.isfile(sums):
        raise CatalogError('ERR-FEED-422-02', 'SHA256SUMS missing')
    listed = {}
    with open(sums) as f:
        for line in f:
            h, _, name = line.rstrip('\n').partition('  ')
            if name:
                listed[name] = h
    for name in FILES:
        p = os.path.join(d, name)
        if name not in listed or not os.path.isfile(p):
            raise CatalogError('ERR-FEED-422-02', '%s missing' % name)
        if _sha(p) != listed[name]:
            raise CatalogError('ERR-FEED-422-02', '%s sha256 mismatch' % name)
    data = {}
    try:
        for name, key in REQUIRED_KEYS.items():
            with open(os.path.join(d, name), encoding='utf-8') as f:
                doc = json.load(f)
            if not isinstance(doc.get(key), list):
                raise CatalogError('ERR-FEED-502-02', '%s: no %s[]' % (name, key))
            data[name] = doc
        with open(os.path.join(d, 'catalog.json'), encoding='utf-8') as f:
            meta = json.load(f)
    except ValueError as e:
        raise CatalogError('ERR-FEED-502-02', 'invalid JSON: %s' % e)
    version = meta.get('catalog_version')
    if not VERSION_RE.match(str(version or '')):
        raise CatalogError('ERR-FEED-502-02', 'catalog.json: bad catalog_version %r' % version)
    for it in data['checklists.json']['items']:
        if any(k not in it for k in ITEM_KEYS):
            raise CatalogError('ERR-FEED-502-02', 'checklists.json: item without %s' % ', '.join(ITEM_KEYS))
    for pb in data['playbooks.json']['playbooks']:
        if not isinstance(pb.get('actions'), dict) or any(a not in pb['actions'] for a in PB_ACTIONS):
            raise CatalogError('ERR-FEED-502-02', 'playbooks.json: %s without actions' % pb.get('pb_id'))
    return version


class Catalog(object):
    def __init__(self, d, version):
        self.dir = d
        self.version = version
        self._cache = {}

    def _load(self, name, key):
        if name not in self._cache:
            with open(os.path.join(self.dir, name), encoding='utf-8') as f:
                self._cache[name] = json.load(f)
        return self._cache[name][key]

    @property
    def meta(self):
        if 'catalog.json' not in self._cache:
            with open(os.path.join(self.dir, 'catalog.json'), encoding='utf-8') as f:
                self._cache['catalog.json'] = json.load(f)
        return self._cache['catalog.json']

    @property
    def scenarios(self):
        return {s['scenario_id']: s for s in self._load('scenarios.json', 'scenarios')}

    @property
    def items(self):
        return self._load('checklists.json', 'items')

    @property
    def playbooks(self):
        return {p['pb_id']: p for p in self._load('playbooks.json', 'playbooks')}

    @property
    def bc_rules(self):
        return self._load('bc_rules.json', 'rules')

    def bc_doc(self):
        """Whole bc_rules.json (rules + ini/extension/framework tables used by the compatibility scan)."""
        self._load('bc_rules.json', 'rules')
        return self._cache['bc_rules.json']

    @property
    def mitigations(self):
        return self._load('mitigations.json', 'rules')

    def framework_rows(self):
        with open(os.path.join(self.dir, 'framework_php.tsv'), encoding='utf-8') as f:
            return list(csv.DictReader(f, delimiter='\t'))

    def items_of(self, scenario_id):
        return [i for i in self.items if i['scenario_id'] == scenario_id]

    def item(self, chk_id):
        return next((i for i in self.items if i['chk_id'] == chk_id), None)

    def scenario_sums(self, scenario_ids):
        """Fingerprint of the scenarios a plan uses (BR-PLAN-006 'catalog_version changed for its scenarios')."""
        h = hashlib.sha256()
        for sid in sorted(scenario_ids):
            h.update(json.dumps(self.scenarios.get(sid), sort_keys=True).encode())
            h.update(json.dumps(self.items_of(sid), sort_keys=True).encode())
        return h.hexdigest()


def select(state_dir=None, warnings=None, packaged=PACKAGED):
    """The catalog in use, or None. Rejected catalogs are reported in WARNINGS as (code, message)."""
    warnings = [] if warnings is None else warnings
    best = None
    dirs = [packaged] + ([os.path.join(state_dir, 'feeds', 'catalog')] if state_dir else [])
    for d in dirs:
        if not os.path.isfile(os.path.join(d, 'catalog.json')):
            continue
        try:
            v = check(d)
        except CatalogError as e:
            warnings.append((e.code, 'catalog %s rejected: %s' % (d, e.detail)))
            continue
        if best is None or vkey(v) > vkey(best.version):
            best = Catalog(d, v)
    return best


def install_imported(src, feeds_dir, warnings):
    """Copy a catalog/ found in an imported snapshot to FEEDS_DIR/catalog (tmp + rename).
    Kept only when valid and newer than the catalog already imported."""
    try:
        v = check(src)
    except CatalogError as e:
        warnings.append((e.code, 'snapshot catalog rejected: %s; the catalog in use is kept' % e.detail))
        return None
    dest = os.path.join(feeds_dir, 'catalog')
    if os.path.isfile(os.path.join(dest, 'catalog.json')):
        try:
            if vkey(check(dest)) >= vkey(v):
                return None
        except CatalogError:
            pass
    tmp = dest + '.new'
    old = dest + '.old'
    for p in (tmp, old):
        if os.path.lexists(p):
            shutil.rmtree(p)
    os.makedirs(tmp)
    for name in FILES + ['SHA256SUMS']:
        shutil.copyfile(os.path.join(src, name), os.path.join(tmp, name))
    if os.path.lexists(dest):
        os.rename(dest, old)
    os.rename(tmp, dest)
    if os.path.lexists(old):
        shutil.rmtree(old)
    return v


def files_for_snapshot(d=PACKAGED):
    """{'catalog/<name>': bytes} of a catalog, for feeds export / build-snapshot."""
    out = {}
    for name in FILES + ['SHA256SUMS']:
        with open(os.path.join(d, name), 'rb') as f:
            out['catalog/' + name] = f.read()
    return out
