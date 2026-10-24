"""HTTPS client of `feeds update` (DOC-SRS-QP-FEED-001 §3.3, BR-FEED-003/004/016).

- HTTPS only, certificate verified, TLS >= 1.2, at most 3 redirects and never
  to http:// (BR-FEED-016).
- Up to 3 attempts for network errors, timeouts, 408/429/5xx; waits from the
  source's retry delays; Retry-After <= 300 s is honoured, > 300 s stops the
  source with ERR-FEED-429-01. No retry for 400/401/403/404/410, except NVD
  403 (rate limiting) which is retried like 429.
- Conditional GET (ETag stored with its Accept-Encoding, Last-Modified).
- Per-source minimum interval between requests and a global time budget.
- Every request is logged (feed_fetch) without keys in the URL.
"""
import gzip
import hashlib
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
import warnings as _warnings

from .. import VERSION
from ..envelope import redact

USER_AGENT = 'php-quickpatch/%s (+https://github.com/luongkam/php-quickpatch)' % VERSION


class FetchError(Exception):
    """A source could not be fetched. code = ERR-FEED-*."""

    def __init__(self, code, message, http=None, attempts=0, retry_after=None):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.http = http
        self.attempts = attempts
        self.retry_after = retry_after


class BudgetExceeded(Exception):
    """The sync time budget is spent (ERR-FEED-504-01). Not a FetchError: no fallback is tried."""

    def __init__(self, message):
        Exception.__init__(self, message)
        self.code = 'ERR-FEED-504-01'
        self.message = message


class Response(object):
    def __init__(self, status, body, headers, url, duration_ms):
        self.status = status
        self.body = body
        self.headers = headers
        self.url = url
        self.duration_ms = duration_ms

    def json(self):
        return json.loads(self.body.decode('utf-8'))


class _HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith('https://'):
            raise FetchError('ERR-FEED-503-01', 'redirect to a non-HTTPS URL refused: %s' % newurl, http=code)
        return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)


def ssl_context():
    ctx = ssl.create_default_context()
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    except AttributeError:  # Python 3.6
        with _warnings.catch_warnings():
            _warnings.simplefilter('ignore')
            ctx.options |= getattr(ssl, 'OP_NO_TLSv1', 0) | getattr(ssl, 'OP_NO_TLSv1_1', 0)
    return ctx


class Fetcher(object):
    def __init__(self, conf, deadline=None, log=None, sleep=time.sleep, now=time.time):
        self.conf = conf              # effective source settings (sources.load)
        self.deadline = deadline      # absolute time.time() of the budget, or None
        self.log = log if log is not None else []   # feed_fetch rows
        self.sleep = sleep
        self.now = now
        self.last_request = {}
        self.requests = 0
        self.opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context()),
                                                  _HttpsOnlyRedirect())

    def remaining(self):
        return None if self.deadline is None else self.deadline - self.now()

    def _wait_interval(self, src):
        gap = float(self.conf[src].get('min_interval_s') or 0)
        last = self.last_request.get(src)
        if last is not None and gap > 0:
            delay = last + gap - self.now()
            if delay > 0:
                self._sleep(delay)

    def _sleep(self, seconds):
        rem = self.remaining()
        if rem is not None and seconds >= rem:
            raise BudgetExceeded('time budget exhausted')
        self.sleep(seconds)

    def request(self, src, url, headers=None, data=None, method=None, timeout=None, retry_statuses=()):
        """One logical request with retries. Returns Response (200/304/404...)."""
        if not url.startswith('https://'):
            raise FetchError('ERR-FEED-503-01', 'non-HTTPS URL refused: %s' % url)
        conf = self.conf[src]
        delays = list(conf.get('retry') or [5, 15, 45])
        attempts = 0
        hdrs = {'User-Agent': USER_AGENT, 'Accept-Encoding': 'gzip'}
        hdrs.update(headers or {})
        timeout = timeout or float(conf.get('timeout_s') or 30)
        last_err = None
        while True:
            attempts += 1
            rem = self.remaining()
            if rem is not None and rem <= 0:
                raise BudgetExceeded('time budget exhausted')
            t = timeout if rem is None else max(1.0, min(timeout, rem))
            self._wait_interval(src)
            self.last_request[src] = self.now()
            self.requests += 1
            start = self.now()
            status, body, rh = None, None, {}
            try:
                req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
                with self.opener.open(req, timeout=t) as r:
                    status, body, rh = r.status, r.read(), dict(r.headers)
            except urllib.error.HTTPError as e:
                status, rh = e.code, dict(e.headers or {})
                try:
                    body = e.read()
                except Exception:
                    body = b''
            except FetchError:
                raise
            except (urllib.error.URLError, socket.timeout, ConnectionError, ssl.SSLError, OSError) as e:
                last_err = str(getattr(e, 'reason', e))
            dur = int((self.now() - start) * 1000)
            if body and rh.get('Content-Encoding', rh.get('content-encoding', '')) == 'gzip':
                try:
                    body = gzip.decompress(body)
                except OSError:
                    last_err, status = 'truncated gzip body', None
            self.log.append({'src_id': src, 'url': redact(url), 'http_status': status,
                             'bytes': len(body) if body is not None else None,
                             'body_sha256': hashlib.sha256(body).hexdigest() if body else None,
                             'duration_ms': dur, 'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(start))})
            if status is not None and (status < 400 or status in (404, 410) or
                                       (status in (400, 401, 403) and status not in retry_statuses)):
                return Response(status, body or b'', rh, url, dur)
            retry_after = None
            if status is not None:
                last_err = 'HTTP %d' % status
                ra = rh.get('Retry-After') or rh.get('retry-after')
                if ra and str(ra).strip().isdigit():
                    retry_after = int(ra)
                    if retry_after > 300:
                        raise FetchError('ERR-FEED-429-01', 'Retry-After %d s > 300 s' % retry_after,
                                         http=status, attempts=attempts, retry_after=retry_after)
            if attempts >= 3:
                code = 'ERR-FEED-429-01' if status in (429,) + tuple(retry_statuses) else None
                raise FetchError(code or 'ERR-FEED-503-01', last_err or 'request failed', http=status,
                                 attempts=attempts, retry_after=retry_after)
            self._sleep(retry_after if retry_after is not None else delays[min(attempts - 1, len(delays) - 1)])
