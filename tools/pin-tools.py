#!/usr/bin/env python3
"""Pin the compatibility scan tools (FR-CMPT-TOOL-001, BR-CMPT-006).

Writes tools/pinned-tools.json, read by tools/build-catalog.py into
catalog.json "tools". Needs network (Packagist, getcomposer.org, git).

For every package: version, git URL and commit (Packagist `source`), dist URL
(Packagist `dist`) and two hashes the installer accepts:
  archive_sha256  SHA-256 of `git archive --format=tar <commit>` (deterministic)
  dist_sha256     SHA-256 of the dist zip, when it could be downloaded here
composer.phar: SHA-256 published by getcomposer.org.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', 'pinned-tools.json')
PACKAGES = [  # DOC-SRS-QP-SCN-PHP-001 §7.3 (+ the dependencies they need at run time)
    ('squizlabs/php_codesniffer', '4.0.4', 'phpcs'),
    ('phpcsstandards/phpcsutils', '1.2.3', 'phpcs'),
    ('phpcompatibility/php-compatibility', '10.0.0-alpha2', 'phpcs'),
    ('phpcompatibility/phpcompatibility-paragonie', '2.0.0-alpha2', 'phpcs'),
    ('phpcompatibility/phpcompatibility-wp', '3.0.0-alpha2', 'phpcs'),
    ('rector/rector', '2.7.0', 'rector'),
    ('phpstan/phpstan', '2.3.2', 'rector'),
]
COMPOSER = [('composer', '2.10.3'), ('composer-lts', '2.2.30')]


def get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def archive_sha(url, ref):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['git', 'init', '-q', d], check=True)
        subprocess.run(['git', '-C', d, 'fetch', '-q', '--depth', '1', url, ref], check=True)
        tar = subprocess.run(['git', '-C', d, 'archive', '--format=tar', ref], check=True, stdout=subprocess.PIPE).stdout
        return hashlib.sha256(tar).hexdigest(), len(tar)


def main():
    out = {'packages': [], 'composer': []}
    for name, version, group in PACKAGES:
        meta = json.loads(get('https://repo.packagist.org/p2/%s.json' % name))
        rel = next(p for p in meta['packages'][name] if p['version'] == version)
        dist = rel['dist']
        src = rel.get('source') or {'url': 'https://github.com/%s.git' % name, 'reference': dist['reference']}
        a_sha, size = archive_sha(src['url'], src['reference'])
        try:
            d_sha = hashlib.sha256(get(dist['url'])).hexdigest()
        except Exception:                  # noqa: BLE001 - dist host not reachable from here
            d_sha = None
        out['packages'].append({'name': name, 'version': version, 'group': group, 'git_url': src['url'],
                                'reference': src['reference'], 'archive_sha256': a_sha, 'archive_bytes': size,
                                'dist_url': dist['url'], 'dist_sha256': d_sha})
        print('%s %s %s' % (name, version, a_sha[:12]))
    for key, version in COMPOSER:
        url = 'https://getcomposer.org/download/%s/composer.phar' % version
        sha = get(url + '.sha256sum').decode().split()[0]
        if hashlib.sha256(get(url)).hexdigest() != sha:
            raise SystemExit('composer %s: published sha256 does not match the download' % version)
        out['composer'].append({'name': key, 'version': version, 'url': url, 'sha256': sha})
        print('%s %s %s' % (key, version, sha[:12]))
    with open(OUT, 'w') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
