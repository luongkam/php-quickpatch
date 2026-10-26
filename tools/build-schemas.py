#!/usr/bin/env python3
"""Generate share/php-quickpatch/schemas/qp.<command>.v1.schema.json.

Source of the shapes: docs/php-quickpatch/api/api-spec-cli-json.md (DOC-API-QP-005)
§3 envelope, §4 preview, §5 scan, §6 assess, §7 plan, §8 fix/rollback,
§9 migrate, §10 feeds status; audit/report from FR-JOB-AUD-002/003, FR-RPT-*.
Every file is self-contained (envelope under $defs) so it can be validated
without resolving references across files (FR-CLI-JSON-002).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'share/php-quickpatch/schemas')

ERR = '^ERR-[A-Z]+-[0-9]{3}-[0-9]{2,3}$'
S = {'type': 'string'}
SN = {'type': ['string', 'null']}
I = {'type': 'integer'}
IN = {'type': ['integer', 'null']}
N = {'type': 'number'}
NN = {'type': ['number', 'null']}
B = {'type': 'boolean'}
BN = {'type': ['boolean', 'null']}
ANY = {}


def arr(items=None, **kw):
    d = {'type': 'array'}
    if items is not None:
        d['items'] = items
    d.update(kw)
    return d


def obj(props, required=None, extra=True, nullable=False):
    d = {'type': ['object', 'null'] if nullable else 'object', 'properties': props}
    d['required'] = list(props) if required is None else required
    if not extra:
        d['additionalProperties'] = False
    return d


def enum(*values, nullable=False):
    v = list(values)
    if nullable:
        v.append(None)
    return {'enum': v}


ISSUE = obj({'severity': enum('critical', 'high', 'medium', 'low'),
             'code': {'type': ['string', 'null'], 'pattern': ERR},
             'message': S, 'object_ref': SN})
ERROR = obj({'code': {'type': 'string', 'pattern': ERR}, 'message': S, 'object_ref': SN},
            required=['code', 'message'])
WARNING = obj({'code': {'type': ['string', 'null'], 'pattern': ERR}, 'message': S, 'object_ref': SN},
              required=['code', 'message'])

ENVELOPE = obj({
    'schema': {'type': 'string', 'pattern': r'^qp\.[a-z]+(\.[a-z]+)*/[1-9][0-9]*$'},
    'schema_version': {'type': 'string', 'pattern': r'^[1-9][0-9]*\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'},
    'tool': obj({'name': {'const': 'php-quickpatch'}, 'version': S}),
    'generated_at': {'type': 'string', 'pattern': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$'},
    'host': obj({'hostname': S, 'os': S, 'kernel': S, 'is_root': B, 'in_container': B}),
    'command': obj({'name': S, 'subcommand': SN, 'argv': arr(S), 'job_id': SN, 'actor': SN}),
    'dry_run': B,
    'exit_code': enum(0, 1, 2),
    'data': obj({'bundle_id': SN, 'freshness': enum('FRESH', 'AGING', 'STALE', 'EXPIRED', nullable=True),
                 'data_age_h': NN,
                 'stale_sources': arr(obj({'src_id': S, 'age_h': NN, 'last_error': SN}, required=['src_id']))}),
    'catalog_version': SN,
    'result': ANY,
    'issues': arr(ISSUE),
    'errors': arr(ERROR),
    'warnings': arr(WARNING),
    'audit_anchor': {'type': ['object', 'null'], 'properties': {'seq': I, 'hash': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}}},
}, required=['schema', 'schema_version', 'tool', 'generated_at', 'host', 'command', 'dry_run', 'exit_code',
             'data', 'catalog_version', 'result', 'issues', 'errors', 'warnings'])

PREVIEW = obj({
    'changes': arr(obj({'type': S, 'action': enum('create', 'modify', 'delete', 'install', 'upgrade', 'remove',
                                                  'restart', 'reload', 'switch'),
                        'target': S, 'from': SN, 'to': SN, 'detail': SN, 'verified': B})),
    'affected': arr(obj({'kind': enum('runtime', 'site', 'app', 'project', 'container', 'host'), 'id': S, 'label': S})),
    'disruption': obj({'expected_s': NN, 'scope': enum('none', 'site', 'runtime', 'host'), 'basis': S}),
    'reversibility': obj({'level': enum('full', 'partial', 'none'), 'rollback_command': SN, 'notes': arr(S)}),
    'requires_retype': {'type': ['object', 'null']},
})
FINGERPRINT = obj({'bundle_id': SN, 'scan_fingerprint': SN, 'catalog_version': SN})

RISK = obj({'R': {'type': 'integer', 'minimum': 0, 'maximum': 100},
            'level': enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'), 'components': {'type': 'object'}},
           required=['R', 'level'], nullable=True)

RUNTIME = obj({
    'runtime_id': {'type': 'string', 'pattern': '^(php|node):[0-9a-f]{12}$'},
    'kind': enum('php', 'node'), 'bin': S, 'version_raw': SN, 'version': SN, 'branch': SN,
    'sapis': arr(S), 'ini_scan_dirs': arr(S), 'extensions': arr(S),
    'owner_pkg': obj({'manager': S, 'name': S, 'version': SN}, nullable=True),
    'install_source': S, 'scenario_ids': arr(S),
    'state': enum('ok', 'ok-backport', 'vulnerable', 'eol', 'unknown'),
    'lifecycle_status': enum('ACTIVE', 'SECURITY_ONLY', 'CURRENT', 'ACTIVE_LTS', 'MAINTENANCE_LTS', 'EOL',
                             'PRE_RELEASE', 'UNKNOWN', nullable=True),
    'priority': enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', nullable=True),
    'eol_date': SN, 'days_to_eol': IN, 'is_lts': BN, 'lts_codename': SN,
    'latest_patch': SN, 'min_patched': SN, 'driver_ids': arr(S),
    'backport': {'type': ['object', 'null']},
    'locked': B, 'lock_reason': SN, 'risk': RISK,
    'abi': SN, 'npm_version': SN, 'apps': arr(), 'site_ids': arr(S),
}, required=['runtime_id', 'kind', 'bin', 'version_raw', 'version', 'branch', 'install_source', 'state', 'locked'])

SITE = obj({'site_id': S, 'pb_id': S, 'server_names': arr(S), 'docroot': SN, 'owner_user': SN,
            'binding_kind': S, 'binding_ref': SN, 'current_branch': SN, 'current_bin': SN, 'runtime_id': SN,
            'runtime_endpoint': SN, 'log_sources': arr(), 'hc_urls': arr(S), 'hc_mode': SN},
           required=['site_id', 'pb_id', 'binding_kind'])

SCAN_RESULT = obj({
    'scan_fingerprint': SN,
    'environment': {'type': 'object'},
    'runtimes': arr(RUNTIME),
    'sites': arr(SITE),
    'projects': arr(obj({'project_id': {'type': 'string', 'pattern': '^[0-9a-f]{12}$'}, 'dir': S, 'owner': S,
                         'kinds': arr(enum('composer', 'npm', 'yarn', 'pnpm', 'wordpress', 'docker')),
                         'site_id': SN, 'lockfiles': arr(S)})),
    'containers': arr(obj({'id': S, 'name': S, 'image': S, 'php_version': SN, 'node_version': SN,
                           'compose_project': SN, 'compose_service': SN})),
    'dependency_findings': arr(obj({'project_id': SN, 'ecosystem': enum('Packagist', 'npm'), 'package': S,
                                    'version': S, 'advisories': arr(), 'severity': S, 'in_kev': B,
                                    'is_malware': B, 'fixed_versions': arr(S)})),
    'wordpress_findings': arr(obj({'site_dir': S, 'project_id': SN, 'version': S, 'min_patched': SN,
                                   'status': enum('ok', 'vulnerable', 'unknown'), 'advisories': arr(),
                                   'in_kev': B, 'risk': ANY})),
    'webshell_findings': arr(obj({'path': S, 'rule': S, 'sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
                                  'mtime': S, 'size': I, 'project_id': SN})),
    'drift_warnings': arr(obj({'site_id': S, 'expected': SN, 'actual': SN, 'code': S})),
    'ranking': arr(obj({'object_ref': S, 'R': I, 'level': S, 'reason_codes': arr(S)})),
    'plan_deadlines': arr(obj({'runtime_id': S, 'deadline': SN, 'days_left': IN, 'plan_id': SN, 'plan_status': SN},
                              required=['runtime_id', 'deadline', 'days_left'])),
    'summary': obj({'runtimes': I, 'by_state': obj({'ok': I, 'ok_backport': I, 'vulnerable': I, 'eol': I, 'unknown': I}),
                    'eol_within_90d': I, 'kev_findings': I, 'critical_issues': I, 'vulnerable_packages': I}),
}, required=['runtimes', 'projects', 'summary'])

MANIFEST_ACTIONS = ('copy', 'created', 'untar', 'docker-created', 'composer-install', 'npm-ci', 'note',
                    'switch', 'reload', 'panel', 'link', 'systemd', 'pm2', 'compose')
FIX_RESULT = obj({
    'run_id': {'type': ['string', 'null'], 'pattern': '^[0-9]{8}-[0-9]{6}$'},
    'scope': obj({'only': arr(S), 'paths': arr(S), 'no_restart': B, 'no_memlimit': B}),
    'actions': arr(obj({'seq': I, 'object_ref': SN, 'kind': S,
                        'status': enum('done', 'skipped', 'failed', 'planned'), 'detail': S,
                        'error_code': {'type': ['string', 'null'], 'pattern': ERR}})),
    'runtimes_after': arr(obj({'runtime_id': S, 'version_before': SN, 'version_after': SN, 'state_after': S})),
    'mitigations': arr(obj({'runtime_id': S, 'file': S, 'action': enum('added', 'removed', 'rewritten'),
                            'driver_ids': arr(S)}, required=['file', 'action'])),
    'restarts': arr(obj({'unit': S, 'status': enum('restarted', 'skipped_no_restart', 'failed')})),
    'restarted': arr(obj({'service': S, 'active': B, 'waited_s': {'type': 'integer', 'minimum': 0, 'maximum': 15}})),
    'restart_failures': arr(obj({'service': S, 'check': S, 'waited_s': I, 'error_code': {'const': 'ERR-PTCH-500-01'}})),
    'counts': obj({'fixed': I, 'open_issues': I, 'critical': I}),
    'rollback_hint': SN,
    'preview': PREVIEW, 'fingerprint': FINGERPRINT,
    'manifest': arr(obj({'seq': I, 'action': enum(*MANIFEST_ACTIONS), 'args': arr(S),
                         'status': enum('done', 'failed', 'skipped', 'planned')})),
    'planned_actions': arr(obj({'action': enum(*MANIFEST_ACTIONS), 'arg1': SN, 'arg2': SN,
                                'reversible': enum('full', 'partial', 'none')})),
}, required=['run_id', 'scope', 'actions', 'counts', 'rollback_hint'])

CANDIDATE = obj({'version': S, 'branch': S,
                 'types': arr(enum('SAME_BRANCH_LATEST', 'NEXT_SUPPORTED', 'RECOMMENDED', 'LATEST_STABLE')),
                 'lifecycle_status': SN, 'is_lts': BN, 'eol_date': SN, 'selectable': B, 'not_selectable_reason': SN,
                 'installable': enum('yes', 'needs_repo', 'no', 'unknown'), 'install_source': SN})
CVE_COUNTS = obj({'critical': I, 'high': I, 'medium': I, 'low': I})
ASSESS_RESULT = obj({
    'runtime_id': S, 'evaluated_on': S,
    'current': obj({'version': S, 'branch': S, 'cve_counts': CVE_COUNTS, 'kev_count': I, 'lifecycle_status': SN,
                    'is_lts': BN, 'eol_date': SN, 'days_to_eol': IN, 'latest_patch': SN, 'min_patched': SN,
                    'risk': RISK, 'not_assessed_label': SN}),
    'advisories': arr(obj({'adv_id': S, 'aliases': arr(S), 'cvss': NN, 'severity': SN, 'in_kev': B,
                           'kev_due': SN, 'published_at': SN, 'fixed_in': SN, 'sources': arr(S),
                           'status': enum('UNPATCHED', 'FIXED_BACKPORT', 'NOT_AFFECTED')})),
    'candidates': arr(CANDIDATE),
    'comparison': obj({'rows': arr(obj({'version': S, 'R': I, 'delta_R': I}, required=['version', 'R', 'delta_R']))}),
}, required=['runtime_id', 'evaluated_on', 'current', 'candidates', 'comparison'])

CHECKLIST_ITEM = obj({
    'chk_id': S, 'scenario_id': SN, 'site_id': SN, 'phase': {'type': 'string', 'pattern': '^P[1-7]$'},
    'action': S, 'exec_type': enum('AUTO', 'SEMI', 'MANUAL'), 'check_mechanism': SN, 'done_criteria': SN,
    'risk': SN, 'applies_when': SN, 'depends_on': arr(S),
    'status': enum('PENDING', 'RUNNING', 'DONE', 'FAILED', 'SKIPPED', 'WAIVED'),
    'blocked_by': arr(S), 'cli_action': SN, 'verified': B, 'job_id': SN, 'reason': SN, 'evidence': SN,
    'updated_at': SN, 'updated_by': SN,
}, required=['chk_id', 'phase', 'action', 'exec_type', 'status'])
PLAN = obj({
    'plan_id': {'type': 'string', 'pattern': '^PLN-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$'},
    'runtime_id': S,
    'status': enum('draft', 'approved', 'in_progress', 'completed', 'rolled_back', 'cancelled'),
    'mode': enum('same_branch', 'cross_branch'),
    'target': obj({'branch': S, 'patch_version': SN, 'types': arr(S), 'override_reason': SN}),
    'stale': B, 'stale_reasons': arr(S),
    'site_order': arr(S), 'canary_site_id': SN, 'blocked_sites': arr(obj({'site_id': S, 'reason': S})),
    'upgrade_items': arr(), 'preconditions': arr(), 'compat_verdicts': arr(),
    'deadline': {'type': ['object', 'null']},
    'checklist_items': arr(CHECKLIST_ITEM),
    'inputs': obj({'bundle_id': SN, 'catalog_version': SN, 'scan_fingerprint': SN}),
    'created_at': S, 'approved_at': SN, 'approved_by': SN, 'updated_at': SN,
}, required=['plan_id', 'runtime_id', 'status', 'mode', 'target', 'stale'])
PLAN_RESULT = {'type': ['object', 'null'], 'properties': {
    'plans': arr({'type': 'object', 'required': ['plan_id', 'status']}),
    'plan': PLAN, 'plan_id': S, 'item': CHECKLIST_ITEM,
    'run': {'type': 'object'}, 'preview': PREVIEW, 'fingerprint': FINGERPRINT}}

SWITCH = obj({'run_id': S, 'site_id': S, 'plan_id': SN, 'from_branch': SN, 'to_branch': SN,
              'status': enum('PREFLIGHT', 'SWITCHED', 'HC_RUNNING', 'PASSED', 'ROLLED_BACK', 'ROLLBACK_FAILED',
                             'HC_FAILED_KEPT', 'ABORTED'),
              't_start': SN, 't_switched': SN, 't_hc_end': SN, 't_rollback_end': SN, 'rollback_reason': SN,
              'rollback_available': B, 'actor': SN}, required=['run_id', 'site_id', 'status'])
STEP = obj({'step': S, 'status': enum('done', 'failed', 'skipped'), 'started_at': S, 'duration_ms': I, 'detail': SN,
            'error_code': {'type': ['string', 'null'], 'pattern': ERR}}, required=['step', 'status', 'detail'])
HC_SUMMARY = obj({'verdict': enum('PASS', 'FAIL', nullable=True), 'mode': enum('full', 'skip'), 'window_s': I,
                  'rounds_done': I,
                  'violations': arr(obj({'criterion': {'type': 'string', 'pattern': '^HC-C[0-9]$'}, 'url': SN,
                                         'detail': S}, required=['criterion', 'detail'])),
                  'report_ref': SN}, required=['verdict', 'mode', 'window_s', 'rounds_done', 'violations'], nullable=True)
BASELINE = obj({'rounds': I, 'per_url': arr(obj({'url': S, 'code_b': S, 'size_b': I, 'p95_ms': I}, required=['url', 'code_b'])),
                'w0': I}, required=['rounds', 'per_url', 'w0'], nullable=True)
MIGRATE_RESULT = {'type': ['object', 'null'], 'properties': {
    'run_id': SN, 'switch': {'anyOf': [{'type': 'null'}, SWITCH]}, 'switches': arr(SWITCH), 'steps': arr(STEP),
    'hc': HC_SUMMARY, 'hc_urls': arr(S),
    'manifest': arr(obj({'seq': I, 'action': enum(*MANIFEST_ACTIONS), 'args': arr(S),
                         'status': enum('done', 'failed', 'skipped', 'planned')})),
    'locked_after_rollback_failed': B,
    'site_id': S, 'baseline_only': B, 'baseline': BASELINE, 'config_file': S,
    'acknowledgement': obj({'run_id': S, 'site_id': S, 'plan_id': SN, 'status': enum('ROLLED_BACK', 'HC_FAILED_KEPT', 'ROLLBACK_FAILED'),
                            'acknowledged_at': S, 'acknowledged_by': S, 'binding_now': {'type': ['object', 'null']},
                            'switch_lock_released': B, 'next_allowed_sites': arr(S)}),
    'runtime': enum('php', 'node'), 'target': S, 'new_bin': SN, 'install_source': SN, 'repo_added': B, 'packages': arr(S),
    'cfg_report': obj({'copied': arr(S), 'dropped_directives': arr(S), 'extensions_installed': arr(S),
                       'not_transferable': arr(S)}),
    'preconditions': arr(obj({'check': S, 'required': S, 'actual': S, 'pass': B})),
    'runtime_id': SN, 'idle_days': I, 'removed_packages': arr(S),
    'affected_switches': arr(obj({'run_id': S, 'rollback_available': B})),
    'preview': PREVIEW, 'fingerprint': FINGERPRINT}}

FEEDS_STATUS_RESULT = obj({
    'bundle_id': SN, 'generated_at': SN, 'freshness': enum('FRESH', 'AGING', 'STALE', 'EXPIRED', nullable=True),
    'data_age_h': NN,
    'sources': arr(obj({'src_id': {'type': 'string', 'pattern': '^SRC-[0-9]{3}$'}, 'name': S,
                        'status': enum('OK', 'DEGRADED', 'FAILED', 'DISABLED'), 'last_ok_at': SN, 'age_h': NN,
                        'ttl_h': NN, 'records': IN, 'last_error': SN, 'data_origin': SN})),
    'schedule': {'type': ['object', 'null']},
    'snapshot': obj({'packaged_generated_at': SN, 'sha256_ok': BN}),
}, required=['bundle_id', 'freshness', 'sources'], nullable=True)

SHA = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
BUNDLE_ID = {'type': 'string', 'pattern': '^b-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$'}
FEEDS_UPDATE_RESULT = obj({
    'bundle_id': BUNDLE_ID, 'generated_at': S,
    'sources': arr(obj({'src_id': {'type': 'string', 'pattern': '^SRC-[0-9]{3}$'},
                        'outcome': enum('fetched', 'not_modified', 'not_due', 'failed', 'disabled'),
                        'status': enum('OK', 'DEGRADED', 'FAILED', 'DISABLED', nullable=True), 'last_error': SN,
                        'records': IN, 'data_origin': SN}, required=['src_id', 'outcome'])),
    'requests': I, 'budget_s': I, 'pending': arr(S), 'coverage': {'type': 'object'},
}, required=['bundle_id', 'sources'], nullable=True)
FEEDS_VERIFY_RESULT = obj({'bundle_id': SN, 'ok': B, 'problems': arr(S), 'raw_problems': arr(S),
                           'rebuilt_bundle_id': SN, 'snapshot': S, 'sha256': SHA, 'generated_at': S},
                          required=['ok'], nullable=True)
FEEDS_EXPORT_RESULT = obj({'file': S, 'sha256': SHA, 'bytes': I, 'bundle_id': BUNDLE_ID, 'generated_at': S,
                           'variant': enum('standard', 'full')}, required=['file', 'sha256', 'bundle_id'], nullable=True)
FEEDS_IMPORT_RESULT = obj({'file': S, 'sha256': SHA, 'bundle_id': BUNDLE_ID, 'generated_at': S,
                           'previous_bundle_id': SN, 'imported': B, 'checks': arr(S)},
                          required=['file', 'sha256', 'bundle_id', 'imported'], nullable=True)
FEEDS_SCHEDULE_RESULT = obj({'action': enum('install', 'remove', 'show'),
                             'type': enum('systemd', 'cron', 'crontab_user'), 'interval_h': I, 'minute': I,
                             'files': arr(S), 'commands': arr(S), 'schedule': {'type': ['object', 'null']},
                             'replaces': {'type': ['object', 'null']}, 'removed': {'type': ['object', 'null']},
                             'content': {'type': 'object'}}, required=['action'], nullable=True)

AUDIT_RECORD = obj({'seq': I, 'ts': S, 'record_type': enum('INTENT', 'RESULT', 'EVENT'), 'actor': S, 'sys_user': SN,
                    'source': enum('cli', 'console', 'central'), 'action': S, 'args': arr(S), 'job_id': SN,
                    'run_id': SN, 'plan_id': SN, 'result': SN, 'exit_code': IN,
                    'prev_hash': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
                    'hash': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}})
AUDIT_RESULT = {'type': ['object', 'null'], 'properties': {
    'records': {'oneOf': [arr(AUDIT_RECORD), I]},
    'total': I, 'page': I, 'limit': I,
    'verified': B, 'first_broken_seq': IN,
    'anchors_checked': arr(obj({'seq': I, 'hash': S, 'source': enum('job', 'manual'), 'match': B})),
    'last_anchor': {'type': ['object', 'null']}}}

REPORT_RESULT = obj({'report_type': enum('assess', 'evidence'), 'format': enum('json', 'csv', 'md', 'html'),
                     'file': S, 'sha256': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}, 'bytes': I},
                    required=['report_type', 'format', 'file', 'sha256'], nullable=True)

SCHEMA_RESULT = obj({'command': S, 'schema_file': S, 'schema': {'type': 'object'}}, nullable=True)

# CR-01: `compat --path DIR --target N` (Node.js project directories, outside the SRS command list).
VERDICT = obj({'status': enum('PASS', 'FAIL', 'PENDING'), 'errors': I, 'warnings': I, 'blockers': I,
               'vulnerable_packages': I, 'by_severity': {'type': 'object'}, 'malware': I, 'deprecated': I,
               'runtime_changes': I, 'pending_parts': arr(S)})
DECLARATION = obj({'file': S, 'line': I, 'kind': enum('lambda_runtime', 'cdk_runtime', 'container_image',
                                                      'ci_node_version', 'tool_versions', 'version_file'),
                   'text': S, 'branch': S, 'code_uri': SN, 'project': SN, 'to_change': B},
                  required=['file', 'line', 'kind', 'branch', 'to_change'])
VULN = obj({'package': S, 'version': S, 'advisories': arr(S), 'severity': S, 'in_kev': B, 'is_malware': B,
            'fixed_versions': arr(S), 'dev': B, 'fix_version': SN, 'major_bump': BN, 'unfixed_advisories': arr(S),
            'direct': B, 'via': arr(S)},
           required=['package', 'version', 'advisories', 'severity', 'fix_version', 'dev'])
BRANCH_INFO = obj({'branch': S, 'status': S, 'eol_date': SN, 'days_to_eol': IN, 'latest': SN, 'lts': BN,
                   'unpatched': {'type': ['object', 'null']}},
                  required=['branch', 'status'], nullable=True)
COMPAT_PROJECT = obj({
    'path': S, 'name': S, 'current_branch': SN, 'current_source': SN, 'target_branch': S, 'lockfile': SN,
    'packages': I, 'declarations': arr(DECLARATION), 'vulnerabilities': {'anyOf': [{'type': 'null'}, arr(VULN)]},
    'deprecated': arr(obj({'package': S, 'version': SN, 'source': enum('npm', 'catalog'), 'message': S,
                           'replacement': SN, 'call_sites': arr(obj({'file': S, 'line': I}))},
                          required=['package', 'source', 'message'])),
    'npm_engine_violations': arr(ANY), 'hits': arr(obj({'hit_id': S, 'file': S, 'line': I, 'rule_id': S,
                                                       'level': enum('error', 'warning'), 'snippet': S},
                                                      required=['file', 'line', 'rule_id', 'level'])),
    'native_addons': arr(obj({'package': S, 'load_ok': BN}, required=['package', 'load_ok'])),
    'parts': {'type': 'object'}, 'verdict': VERDICT,
    'deploy': obj({'kind': enum('lambda', 'static_site', nullable=True), 'functions': arr(S), 'scripts': arr(S),
                   'region': SN, 'npm_install': B, 'static_export': B, 'buckets': arr(S)}, required=['kind']),
    'work_items': arr(obj({'kind': S, 'count': I, 'size': enum('S', 'M', 'L')}, required=['kind', 'count', 'size'])),
    'errors': arr(ANY), 'notes': arr(ANY)},
    required=['path', 'name', 'current_branch', 'target_branch', 'declarations', 'vulnerabilities', 'deprecated',
              'hits', 'native_addons', 'verdict', 'work_items'])
COMPAT_RESULT = obj({
    'run_id': S, 'runtime': enum('node'), 'paths': arr(S), 'target_branch': S, 'target_patch': S,
    'current_branch': SN, 'catalog_version': SN,
    'lifecycle': obj({'today': S, 'bundle_id': SN, 'current': BRANCH_INFO, 'target': BRANCH_INFO,
                      'recommended': SN, 'recommended_eol': SN, 'min_eol': S, 'target_ok': B}, required=['target', 'recommended', 'target_ok'],
                     nullable=True),
    'summary': obj({'projects': I, 'by_status': {'type': 'object'}, 'vulnerable_packages': I, 'runtime_changes': I,
                    'deprecated': I, 'errors': I}),
    'projects': arr(COMPAT_PROJECT), 'shared_declarations': arr(DECLARATION), 'reports': arr(S),
    'brief': obj({'risks': arr(obj({'level': enum('critical', 'high', 'medium', 'low', 'info', 'unassessed'), 'area': S,
                                    'key': S, 'detect': enum('scan', 'manual')},
                                   required=['level', 'area', 'key'])),
                  'effort': {'type': 'object'}, 'schedule': arr(ANY), 'assurance': {'type': 'object'},
                  'checklist': arr(obj({'phase': S, 'key': S, 'status': enum('todo', 'not_needed', 'check')},
                                       required=['phase', 'key', 'status']))},
                 required=['risks', 'effort', 'schedule', 'assurance', 'checklist'])},
    required=['run_id', 'runtime', 'paths', 'target_branch', 'lifecycle', 'summary', 'projects', 'reports'],
    nullable=True)

COMMANDS = {
    'scan': ('qp.scan/1', SCAN_RESULT, 'Output of `php-quickpatch.sh scan --json` (DOC-API-QP-005 §5)'),
    'fix': ('qp.fix/1', FIX_RESULT, 'Output of `fix --json` and `rollback --json` (DOC-API-QP-005 §8)'),
    'assess': ('qp.assess/1', ASSESS_RESULT, 'Output of `assess --json` (DOC-API-QP-005 §6)'),
    'plan': ('qp.plan/1', PLAN_RESULT, 'Output of `plan <subcommand> --json` (DOC-API-QP-005 §7)'),
    'migrate': ('qp.migrate/1', MIGRATE_RESULT, 'Output of `migrate <subcommand> --json` (DOC-API-QP-005 §9)'),
    'feeds.status': ('qp.feeds.status/1', FEEDS_STATUS_RESULT, 'Output of `feeds status --json` (DOC-API-QP-005 §10)'),
    'feeds.update': ('qp.feeds.update/1', FEEDS_UPDATE_RESULT, 'Output of `feeds update --json` (FR-FEED-CMD-001)'),
    'feeds.verify': ('qp.feeds.verify/1', FEEDS_VERIFY_RESULT, 'Output of `feeds verify --json` (FR-FEED-CMD-003)'),
    'feeds.export': ('qp.feeds.export/1', FEEDS_EXPORT_RESULT, 'Output of `feeds export --json` (FR-FEED-CMD-004)'),
    'feeds.import': ('qp.feeds.import/1', FEEDS_IMPORT_RESULT, 'Output of `feeds import --json` (FR-FEED-CMD-005)'),
    'feeds.schedule': ('qp.feeds.schedule/1', FEEDS_SCHEDULE_RESULT, 'Output of `feeds schedule --json` (FR-FEED-CMD-006)'),
    'feeds': ('qp.feeds/1', {'type': ['object', 'null']}, 'Error envelope of `feeds` with an unknown subcommand'),
    'audit': ('qp.audit/1', AUDIT_RESULT, 'Output of `audit list|verify --json` (FR-JOB-AUD-002, FR-JOB-AUD-003)'),
    'report': ('qp.report/1', REPORT_RESULT, 'Output of `report assess|evidence --json` (FR-RPT-ASMT-001, FR-RPT-AUD-001)'),
    'schema': ('qp.schema/1', SCHEMA_RESULT, 'Output of `schema <command> --json`'),
    'compat': ('qp.compat/1', COMPAT_RESULT, 'Output of `compat --path DIR --target N --json` (CR-01)'),
}


def build(name, schema_id, result, title):
    major = schema_id.rsplit('/', 1)[1]
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'urn:php-quickpatch:schema:%s:%s' % (schema_id.split('/')[0], major),
        'title': schema_id,
        'description': title,
        '$defs': {'envelope': ENVELOPE},
        'allOf': [
            {'$ref': '#/$defs/envelope'},
            # result is null when the command stopped before producing data (§2)
            {'properties': {'schema': {'const': schema_id}, 'result': {'anyOf': [{'type': 'null'}, result]}}},
        ],
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (sid, result, title) in COMMANDS.items():
        path = os.path.join(OUT, 'qp.%s.v1.schema.json' % name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(build(name, sid, result, title), f, indent=2, ensure_ascii=False)
            f.write('\n')
    print('%d schemas -> %s' % (len(COMMANDS), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
