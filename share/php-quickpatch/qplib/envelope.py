"""--json envelope shared by every Python command (FR-CLI-JSON-001, DOC-API-QP-005 §3)."""
import datetime
import json
import os
import platform
import re
import socket
import sys

from . import VERSION

SECRET_ENV = re.compile(r'^QP_.*_(KEY|TOKEN|SECRET)$')
SECRET_KV = re.compile(r'(?i)((?:password|passwd|token|secret|api_key|apikey)=)[^&\s]*')
URL_PASS = re.compile(r'(://[^/:@\s]+:)[^@\s]+@')


def redact(text):
    """BR-SEC-006: mask secrets (QP_*_KEY/TOKEN values, k=v secrets, URL passwords)."""
    if not isinstance(text, str):
        return text
    for name, value in os.environ.items():
        if SECRET_ENV.match(name) and len(value) >= 4:
            text = text.replace(value, '***')
    text = SECRET_KV.sub(r'\1***', text)
    return URL_PASS.sub(r'\1***@', text)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def iso_ms(dt=None):
    dt = dt or utc_now()
    return dt.strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (dt.microsecond // 1000)


def in_container():
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup') as f:
            return bool(re.search(r'docker|containerd|kubepods|libpod', f.read()))
    except OSError:
        return False


def host():
    os_name = 'unknown'
    try:
        info = {}
        with open('/etc/os-release') as f:
            for line in f:
                if '=' in line:
                    k, v = line.rstrip('\n').split('=', 1)
                    info[k] = v.strip('"')
        os_name = ('%s %s' % (info.get('ID', 'unknown'), info.get('VERSION_ID', ''))).strip()
    except OSError:
        pass
    return {'hostname': socket.gethostname(), 'os': os_name, 'kernel': platform.release(),
            'is_root': os.geteuid() == 0, 'in_container': in_container()}


class Envelope(object):
    """Collects issues/errors/warnings and prints one JSON document."""

    def __init__(self, schema, name, argv, subcommand=None, dry_run=False):
        self.schema = schema
        self.name = name
        self.subcommand = subcommand
        self.argv = [redact(a) for a in argv]
        self.dry_run = dry_run
        self.issues = []
        self.errors = []
        self.warnings = []
        self.data = {'bundle_id': None, 'freshness': None, 'data_age_h': None, 'stale_sources': []}
        self.catalog_version = None
        self.audit_anchor = None

    def issue(self, severity, message, code=None, ref=None):
        self.issues.append({'severity': severity, 'code': code, 'message': redact(message), 'object_ref': ref})

    def error(self, code, message, ref=None):
        self.errors.append({'code': code, 'message': redact(message), 'object_ref': ref})

    def warning(self, code, message, ref=None):
        self.warnings.append({'code': code, 'message': redact(message), 'object_ref': ref})

    def document(self, exit_code, result):
        doc = {
            'schema': self.schema,
            'schema_version': '1.0.0',
            'tool': {'name': 'php-quickpatch', 'version': VERSION},
            'generated_at': iso_ms(),
            'host': host(),
            'command': {'name': self.name, 'subcommand': self.subcommand, 'argv': self.argv,
                        'job_id': os.environ.get('QP_JOB_ID') or None,
                        'actor': os.environ.get('QP_ACTOR') or None},
            'dry_run': bool(self.dry_run),
            'exit_code': exit_code,
            'data': self.data,
            'catalog_version': self.catalog_version,
            'result': result,
            'issues': self.issues,
            'errors': self.errors,
            'warnings': self.warnings,
            'audit_anchor': self.audit_anchor,
        }
        return doc

    def emit(self, exit_code, result, stream=None):
        stream = stream or sys.stdout
        stream.write(json.dumps(self.document(exit_code, result), ensure_ascii=False) + '\n')
        stream.flush()
