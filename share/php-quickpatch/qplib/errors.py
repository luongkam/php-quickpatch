"""Error catalog (catalog/errors.tsv, generated from srs/error-matrix.md)."""
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CATALOG = os.path.join(_HERE, 'catalog', 'errors.tsv')
_cache = None


class QPError(Exception):
    """An error with an ERR-* code; exit code 2 unless stated otherwise."""

    def __init__(self, code, message, exit_code=2, http=None, details=None):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.http = http
        self.details = details or {}


def load():
    global _cache
    if _cache is None:
        _cache = {}
        try:
            with open(_CATALOG, encoding='utf-8') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    code, http, key, sev, vi, en = (line.rstrip('\n').split('\t') + [''] * 6)[:6]
                    _cache[code] = {'http': int(http) if http.isdigit() else None, 'key': key,
                                    'severity': sev, 'vi': vi, 'en': en}
        except OSError:
            pass
    return _cache


def info(code):
    return load().get(code, {})


def message(code, default=None, lang=None, **values):
    """Localized message of CODE (QP_LANG=vi → Vietnamese), {placeholders} filled."""
    lang = lang or os.environ.get('QP_LANG', 'en')
    entry = load().get(code, {})
    text = default if default is not None else entry.get('en', code)
    if lang == 'vi' and entry.get('vi'):
        text = entry['vi']
    for k, v in values.items():
        text = text.replace('{%s}' % k, str(v))
    return text


def error(code, default=None, exit_code=2, details=None, **values):
    """Build a QPError with the catalog message of CODE."""
    return QPError(code, message(code, default, **values), exit_code=exit_code,
                   http=info(code).get('http'), details=details)
