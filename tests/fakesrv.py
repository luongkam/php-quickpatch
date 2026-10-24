#!/usr/bin/env python3
"""Local HTTPS stand-in for the 17 data sources (tests only, no network).

    fakesrv.py FIXTURE_DIR STATE_DIR

STATE_DIR receives ca.pem (trust it with SSL_CERT_FILE), port, requests.log
(one JSON line per request) and may hold control.json, re-read on every
request, to script failures:
    {"SRC-006": {"status": 503}, "SRC-004": {"status": 429, "retry_after": 1, "times": 1},
     "SRC-009": {"file": "/abs/other.json"}, "SRC-002": {"delay": 3}, "SRC-012": {"body": "not json"}}
OSV querybatch answers from STATE_DIR/osv.vulns ("name version ID,ID" lines),
like the curl stub of tests/bash/stubs.sh.
"""
import email.utils
import hashlib
import http.server
import json
import os
import socketserver
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse

FIX, STATE = sys.argv[1], sys.argv[2]
LOCK = threading.Lock()
COUNTS = {}


def make_cert():
    ca_key, ca = os.path.join(STATE, 'ca.key'), os.path.join(STATE, 'ca.pem')
    key, csr, crt = (os.path.join(STATE, n) for n in ('srv.key', 'srv.csr', 'srv.pem'))
    ext = os.path.join(STATE, 'ext.cnf')
    with open(ext, 'w') as f:
        f.write('subjectAltName=IP:127.0.0.1,DNS:localhost\nbasicConstraints=CA:FALSE\n')
    q = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', ca_key, '-out', ca,
                    '-days', '2', '-subj', '/CN=qp-test-ca', '-addext', 'basicConstraints=critical,CA:TRUE',
                    '-addext', 'keyUsage=critical,keyCertSign,cRLSign'], **q)
    subprocess.run(['openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-keyout', key, '-out', csr,
                    '-subj', '/CN=127.0.0.1'], **q)
    subprocess.run(['openssl', 'x509', '-req', '-in', csr, '-CA', ca, '-CAkey', ca_key, '-CAcreateserial',
                    '-out', crt, '-days', '2', '-extfile', ext], **q)
    return crt, key


LAST_CTL = [None]


def control():
    """control.json; a new version resets the per-source request counters ("times")."""
    try:
        with open(os.path.join(STATE, 'control.json')) as f:
            text = f.read()
    except OSError:
        text = ''
    with LOCK:
        if text != LAST_CTL[0]:
            LAST_CTL[0] = text
            COUNTS.clear()
    try:
        return json.loads(text) if text else {}
    except ValueError:
        return {}


def read(rel):
    p = rel if rel.startswith('/') else os.path.join(FIX, rel)
    try:
        with open(p, 'rb') as f:
            return f.read()
    except OSError:
        return None


def nvd(qs):
    """SRC-004: choose the query file, filter by lastMod window, page."""
    if 'sourceIdentifier' in qs:
        name = 'php-q2'
    else:
        vms = qs.get('virtualMatchString', [''])[0]
        name = {'cpe:2.3:a:php:php': 'php-q1', 'cpe:2.3:a:nodejs:node.js': 'node-q1',
                'cpe:2.3:a:wordpress:wordpress': 'wordpress-q1'}.get(vms)
    doc = json.loads(read('SRC-004/%s.json' % name) or b'{"vulnerabilities": []}')
    vulns = doc.get('vulnerabilities', [])
    start = qs.get('lastModStartDate', [None])[0]
    end = qs.get('lastModEndDate', [None])[0]
    if start:
        vulns = [v for v in vulns if start[:19] <= v['cve']['lastModified'][:19] <= (end or '9999')[:19]]
    size = int(qs.get('resultsPerPage', ['2000'])[0])
    idx = int(qs.get('startIndex', ['0'])[0])
    page = vulns[idx:idx + size]
    return json.dumps({'resultsPerPage': len(page), 'startIndex': idx, 'totalResults': len(vulns),
                       'format': 'NVD_CVE', 'version': '2.0', 'timestamp': '2026-10-24T19:48:00.000',
                       'vulnerabilities': page}).encode()


def osv_batch(body, page_size=None):
    """querybatch; with control {"SRC-007": {"page_size": N}} results are paged by next_page_token."""
    vul = {}
    try:
        with open(os.path.join(STATE, 'osv.vulns')) as f:
            for line in f:
                parts = line.split()
                if len(parts) == 3:
                    vul[(parts[0], parts[1])] = parts[2].split(',')
    except OSError:
        pass
    q = json.loads(body.decode())['queries']
    out = []
    for x in q:
        ids = vul.get((x['package']['name'], x.get('version')), [])
        start = int(x.get('page_token') or 0)
        if page_size:
            page, nxt = ids[start:start + page_size], start + page_size
            r = {'vulns': [{'id': i, 'modified': '2026-10-01T00:00:00Z'} for i in page]}
            if nxt < len(ids):
                r['next_page_token'] = str(nxt)
        else:
            r = {'vulns': [{'id': i, 'modified': '2026-10-01T00:00:00Z'} for i in ids]}
        out.append(r)
    return json.dumps({'results': out}).encode()


def osv_vuln(vid):
    p = os.path.join(STATE, 'osv-vulns', vid + '.json')
    if os.path.isfile(p):
        return open(p, 'rb').read()
    if vid.startswith(('GHSA-', 'MAL-', 'CVE-', 'PYSEC-')):
        return json.dumps({'id': vid, 'modified': '2026-10-01T00:00:00Z', 'aliases': [],
                           'database_specific': {'severity': 'HIGH'}, 'affected': []}).encode()
    return None


def route(src, rest, qs, body, ctl=None):
    """-> (status, body, extra headers)."""
    if src == 'SRC-001':
        if rest.startswith('v1/products/'):
            return 200, read('SRC-001/v1-%s.json' % rest.split('/')[2]), {}
        if rest.endswith('.json'):
            return 200, read('SRC-001/legacy-%s' % rest), {}
    if src == 'SRC-002':
        if rest == 'pre-release-builds.php':
            return 200, read('SRC-002/pre-release-builds.json'), {}
        if 'version' in qs:
            b = read('SRC-002/branch-%s.json' % qs['version'][0])
            return 200, b if b is not None else b'{"error":"Unknown version"}', {}
        return 200, read('SRC-002/index.json'), {}
    if src == 'SRC-003':
        if rest.startswith('ChangeLog-'):
            return 200, read('SRC-003/%s.html' % rest[:-4]), {}
        if rest == 'eol.php':
            return 200, read('SRC-003/eol.html'), {}
    if src == 'SRC-003-mirror' and rest.endswith('/NEWS'):
        return 200, read('SRC-003/NEWS-%s.txt' % rest.split('/')[0][4:]), {}
    if src == 'SRC-004':
        return 200, nvd(qs), {}
    if src in ('SRC-006', 'SRC-006-mirror'):
        return 200, read('SRC-006/kev.json'), {}
    if src == 'SRC-008':
        return 403, b'{"message":"API rate limit exceeded"}', {'X-RateLimit-Remaining': '60'}
    if src in ('SRC-009', 'SRC-010', 'SRC-011'):
        return 200, read('%s/%s' % (src, rest)), {}
    if src == 'SRC-012':
        return 200, read('SRC-012/stable-check.json'), {}
    if src in ('SRC-007', 'SRC-014'):
        if rest == 'querybatch':
            return 200, osv_batch(body, (ctl or {}).get('page_size')), {}
        if rest.startswith('vulns/'):
            return 200, osv_vuln(rest[6:]), {}
    if src == 'SRC-005':
        return 200, read('SRC-005/%s.json' % rest), {}
    return 404, b'{"message":"Not Found"}', {}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def handle_any(self, body=b''):
        u = urllib.parse.urlsplit(self.path)
        parts = u.path.lstrip('/').split('/', 1)
        src, rest = parts[0], parts[1] if len(parts) > 1 else ''
        qs = urllib.parse.parse_qs(u.query, keep_blank_values=True)
        ctl = control().get(src, {})
        with LOCK:
            n = COUNTS[src] = COUNTS.get(src, 0) + 1
            with open(os.path.join(STATE, 'requests.log'), 'a') as f:
                f.write(json.dumps({'src': src, 'path': self.path, 'method': self.command, 'n': n,
                                    'if_none_match': self.headers.get('If-None-Match'),
                                    'if_modified_since': self.headers.get('If-Modified-Since'),
                                    'api_key': bool(self.headers.get('apiKey')), 't': time.time()}) + '\n')
        if ctl.get('delay'):
            time.sleep(float(ctl['delay']))
        times = ctl.get('times')
        if ctl.get('status') and (times is None or n <= times):
            hdr = {}
            if ctl.get('retry_after') is not None:
                hdr['Retry-After'] = str(ctl['retry_after'])
            return self.reply(int(ctl['status']), b'{"error":"scripted"}', hdr)
        if ctl.get('body') is not None:
            return self.reply(200, ctl['body'].encode(), {})
        if ctl.get('file'):
            return self.reply(200, read(ctl['file']), {})
        status, data, hdr = route(src, rest, qs, body, ctl)
        if data is None:
            return self.reply(404, b'{"message":"Not Found"}', {})
        etag = '"%s"' % hashlib.sha256(data).hexdigest()[:16]
        if status == 200 and self.command == 'GET':
            hdr = dict(hdr, ETag=etag, **{'Last-Modified': email.utils.formatdate(1761300000, usegmt=True)})
            if self.headers.get('If-None-Match') == etag:
                return self.reply(304, b'', hdr)
        return self.reply(status, data, hdr)

    def reply(self, status, data, hdr):
        self.send_response(status)
        for k, v in hdr.items():
            self.send_header(k, v)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def do_GET(self):
        self.handle_any()

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        self.handle_any(self.rfile.read(n))


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def main():
    crt, key = make_cert()
    srv = Server(('127.0.0.1', 0), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(crt, key)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    with open(os.path.join(STATE, 'port.tmp'), 'w') as f:
        f.write(str(srv.server_address[1]))
    os.replace(os.path.join(STATE, 'port.tmp'), os.path.join(STATE, 'port'))
    srv.serve_forever()


if __name__ == '__main__':
    main()
