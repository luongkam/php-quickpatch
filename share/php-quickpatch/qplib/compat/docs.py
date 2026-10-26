"""`report security|compatibility --result FILE|RUN_ID --out FILE` (CR-04, qp.report/1).

Re-renders an enterprise document from a saved `compat` result, without scanning again, so the
cover page (client, project, author, classification, version) can be filled in before the document
is sent. Read only, except for the new --out file: an existing file is never overwritten
(ERR-RPT-409-01, as for the other `report` kinds). Prints the SHA-256 of the file (FR-RPT-ASMT-001).
"""
import hashlib
import json
import os
import re

from .. import errors
from . import enterprise as EN
from .cli import META, bad, meta_opts

KINDS = ('security', 'compatibility')
FORMATS = {'html': '.html', 'md': '.md'}
RUN_ID_RE = re.compile(r'^\d{8}-\d{6}-[0-9a-f]{4}$')


def load_result(ref, state_dir):
    """A compat result: result.json of a run (path or run id), or a saved `compat --json` envelope."""
    path = ref
    if not os.path.isfile(path) and RUN_ID_RE.match(ref):
        path = os.path.join(state_dir, 'reports', 'compat-' + ref, 'result.json')
    if not os.path.isfile(path):
        raise bad('--result %s' % ref)
    try:
        with open(path, encoding='utf-8') as f:
            res = json.load(f)
    except (OSError, ValueError):
        raise bad('--result %s (not JSON)' % ref)
    if isinstance(res, dict) and isinstance(res.get('result'), dict) and res.get('schema') == 'qp.compat/1':
        res = res['result']
    if not (isinstance(res, dict) and res.get('runtime') == 'node' and isinstance(res.get('projects'), list)
            and res.get('target_branch')):
        raise bad('--result %s (not a compat result)' % ref)
    return res


def run(env, argv, Args, warnings, state_dir):
    a = Args(argv, flags=('--json',), options=('--result', '--out', '--format', '--lang') + tuple(o for o, _ in META))
    kind = a.positional[0] if a.positional else None
    if kind not in KINDS or len(a.positional) != 1:
        raise bad('report %s' % (' '.join(a.positional) or '(kind)'))
    if not a.opts.get('--result'):
        raise bad('--result')
    out = a.opts.get('--out')
    if not out:
        raise bad('--out')
    fmt = a.opts.get('--format') or {'.html': 'html', '.htm': 'html', '.md': 'md'}.get(os.path.splitext(out)[1].lower())
    if fmt not in FORMATS or os.path.splitext(out)[1].lower() not in (('.html', '.htm') if fmt == 'html' else ('.md',)):
        raise errors.error('ERR-RPT-422-01', detail='format=%s out=%s (html or md, matching the extension)' % (fmt, out))
    out = os.path.abspath(out)
    if not os.path.isdir(os.path.dirname(out)):
        raise bad('--out %s' % out)
    if os.path.lexists(out):
        raise errors.error('ERR-RPT-409-01', path=out)
    lang = a.opts.get('--lang') or ('vi' if os.environ.get('QP_LANG') == 'vi' else 'en')
    if lang not in ('en', 'vi'):
        raise bad('--lang')
    res = load_result(a.opts['--result'], state_dir)
    doc = EN.build(kind, res, lang, meta_opts(a))
    EN.write(doc, out)
    with open(out, 'rb') as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    result = {'report_type': kind, 'format': fmt, 'file': out, 'sha256': digest, 'bytes': os.path.getsize(out),
              'lang': lang, 'doc_id': doc['meta']['doc_id'], 'source_run_id': res.get('run_id'),
              'findings': len(doc.get('findings') or [])}
    if '--json' not in a.flags:
        print('%s  %s' % (digest, out))
    return 0, result
