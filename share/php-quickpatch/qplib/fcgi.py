"""FastCGI client (standard library only) for the pre-switch trial run and the switch check.

DOC-SRS-QP-ENV-002 §3.3 (probe, BR-HC-003) and §3.4 method 1 (FPM status of the pool the
tool created, `pm.status_path = /qp-fpm-status`). Used by `migrate` through
`qp-feeds.py fcgi`; prints one JSON object.
"""
import json
import re
import socket
import struct
import time

VERSION = 1
BEGIN, END, PARAMS, STDIN, STDOUT, STDERR = 1, 3, 4, 5, 6, 7
RESPONDER = 1
FATAL_RE = re.compile(r'PHP (Fatal error|Parse error)')


def _record(kind, req_id, content=b''):
    out = b''
    for i in range(0, max(len(content), 1), 65535):
        chunk = content[i:i + 65535]
        pad = (8 - len(chunk) % 8) % 8
        out += struct.pack('!BBHHBB', VERSION, kind, req_id, len(chunk), pad, 0) + chunk + b'\0' * pad
        if not content:
            break
    return out


def _nv(name, value):
    n, v = name.encode(), value.encode()
    def ln(x):
        return struct.pack('!B', len(x)) if len(x) < 128 else struct.pack('!I', len(x) | 0x80000000)
    return ln(n) + ln(v) + n + v


def connect(endpoint, timeout):
    ep = endpoint[5:] if endpoint.startswith('unix:') else endpoint
    if ep.startswith('/'):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(ep)
        return s
    host, _, port = ep.rpartition(':')
    host = (host or '127.0.0.1').strip('[]')
    s = socket.create_connection((host, int(port)), timeout=timeout)
    s.settimeout(timeout)
    return s


def request(endpoint, params, timeout=10.0):
    """-> dict(ended, stdout bytes, stderr str, error)."""
    out = {'ended': False, 'stdout': b'', 'stderr': '', 'error': None}
    deadline = time.time() + timeout
    try:
        s = connect(endpoint, timeout)
    except OSError as e:
        out['error'] = 'connect: %s' % e
        return out
    try:
        body = b''.join(_nv(k, str(v)) for k, v in params.items())
        s.sendall(_record(BEGIN, 1, struct.pack('!HB5x', RESPONDER, 0)) + _record(PARAMS, 1, body)
                  + _record(PARAMS, 1) + _record(STDIN, 1))
        buf, err = b'', b''
        data = b''
        while not out['ended']:
            left = deadline - time.time()
            if left <= 0:
                out['error'] = 'timeout'
                break
            s.settimeout(left)
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            while len(data) >= 8:
                _, kind, _, clen, pad, _ = struct.unpack('!BBHHBB', data[:8])
                if len(data) < 8 + clen + pad:
                    break
                content = data[8:8 + clen]
                data = data[8 + clen + pad:]
                if kind == STDOUT:
                    buf += content
                elif kind == STDERR:
                    err += content
                elif kind == END:
                    out['ended'] = True
        out['stdout'], out['stderr'] = buf, err.decode('utf-8', 'replace')
    except OSError as e:
        out['error'] = str(e)
    finally:
        s.close()
    if not out['ended'] and out['error'] is None:
        out['error'] = 'connection closed before FCGI_END_REQUEST'
    return out


def split_response(raw):
    head, sep, body = raw.partition(b'\r\n\r\n')
    if not sep:
        head, sep, body = raw.partition(b'\n\n')
    headers = {}
    for line in head.decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    return headers, body


def probe(endpoint, docroot, host, port='80', https=False, script='index.php', timeout=10.0, version=''):
    """§3.3: GET / of the site's index.php on the target pool."""
    path = docroot.rstrip('/') + '/' + script
    params = {'REQUEST_METHOD': 'GET', 'SCRIPT_FILENAME': path, 'SCRIPT_NAME': '/' + script, 'REQUEST_URI': '/',
              'QUERY_STRING': '', 'DOCUMENT_ROOT': docroot, 'SERVER_NAME': host, 'HTTP_HOST': host,
              'SERVER_PORT': str(port), 'REMOTE_ADDR': '127.0.0.1', 'SERVER_PROTOCOL': 'HTTP/1.1',
              'GATEWAY_INTERFACE': 'CGI/1.1', 'HTTP_USER_AGENT': 'php-quickpatch-hc/%s' % version}
    if https:
        params['HTTPS'] = 'on'
    r = request(endpoint, params, timeout)
    headers, body = split_response(r['stdout'])
    status = headers.get('status', '200')
    reasons = []
    if not r['ended']:
        reasons.append(r['error'] or 'no FCGI_END_REQUEST')
    if status.startswith('5'):
        reasons.append('Status %s' % status)
    if FATAL_RE.search(r['stderr']):
        reasons.append(FATAL_RE.search(r['stderr']).group(0))
    if b'<?php' in body:
        reasons.append('body contains <?php')
    return {'ok': not reasons, 'status': status, 'detail': '; '.join(reasons) or 'Status %s' % status,
            'stderr_excerpt': r['stderr'][:300], 'body_bytes': len(body)}


def status(endpoint, path='/qp-fpm-status', timeout=10.0):
    """§3.4 method 1: `accepted conn` of the pool (None when the status page is not served)."""
    params = {'REQUEST_METHOD': 'GET', 'SCRIPT_FILENAME': path, 'SCRIPT_NAME': path, 'REQUEST_URI': path,
              'QUERY_STRING': '', 'SERVER_PROTOCOL': 'HTTP/1.1', 'GATEWAY_INTERFACE': 'CGI/1.1',
              'REMOTE_ADDR': '127.0.0.1'}
    r = request(endpoint, params, timeout)
    _, body = split_response(r['stdout'])
    m = re.search(rb'accepted conn:\s*(\d+)', body)
    return {'ok': bool(m), 'accepted_conn': int(m.group(1)) if m else None, 'detail': r['error'] or ''}


def main(argv):
    import argparse
    p = argparse.ArgumentParser(prog='fcgi')
    p.add_argument('mode', choices=('probe', 'status'))
    p.add_argument('--endpoint', required=True)
    p.add_argument('--docroot', default='')
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', default='80')
    p.add_argument('--https', action='store_true')
    p.add_argument('--timeout', type=float, default=10.0)
    p.add_argument('--version', default='')
    a = p.parse_args(argv)
    if a.mode == 'probe':
        res = probe(a.endpoint, a.docroot, a.host, a.port, a.https, timeout=a.timeout, version=a.version)
    else:
        res = status(a.endpoint, timeout=a.timeout)
    print(json.dumps(res, sort_keys=True))
    return 0 if res['ok'] else 1
