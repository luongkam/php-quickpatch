#!/usr/bin/env bash
# M4 — compatibility scan in the plan (FR-CMPT-CODE-001/003, FR-CMPT-COMP-001/002,
# FR-CMPT-INI-001, FR-CMPT-EXT-001, FR-CMPT-RES-001, FR-CMPT-RCT-001, FR-PLAN-GEN-002,
# FR-PLAN-DEP-001, FR-CLI-CMD-002 `plan waive` / `plan compat`; TC-CMPT-002, 004, 006,
# 010..015, 019..021, 028..033, TC-PLAN-009, 011, 013, 021). Day T = 2026-10-22.
# The real PHPCompatibility run needs installed tools: QP_TEST_TOOLS_DIR=<STATE_DIR>/tools/php
# of a machine that ran `plan create` online (otherwise that part is skipped).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'feeds_cleanup; rm -rf "$T"' EXIT
# shellcheck disable=SC2034  # FX is read by the stubs
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; dpkg_stubs; curl_stub; apt_stub
SD=/var/lib/php-quickpatch
feeds_fixture
export QP_TODAY=2026-10-22
J=$T/out.json
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
stub apt-cache 'case "$2" in php8.5-mysql|php8.5-mbstring|php8.5-fpm) printf "%s:\n  Installed: (none)\n  Candidate: 8.5.11-1\n" "$2";; *) printf "%s:\n  Installed: (none)\n  Candidate: (none)\n" "$2";; esac'
PHP_REAL=$(command -v php8.3 || command -v php)

# --- fixture: PHP 7.4 runtime, two sites and one site with no readable docroot ------------
B=$T/bin; W=$T/www
fake_php "$B/p74/bin/php" 7.4.33 "" "Core date json mbstring mysqli legacy_test unused_test"
dpkg_owns "$B/p74/bin/php" php7.4-cli 7.4.33-1
# $NEW_BIN double: answers version probes as 8.5.11, runs the real PHP for everything else (php -l, phpcs).
new_php() {
  mkdir -p "${1%/*}"
  cat >"$1" <<EOF
#!/usr/bin/env bash
case "\$*" in
  *PHP_VERSION*) printf 8.5.11 ;;
  --ini) echo "Configuration File (php.ini) Path: /etc"; echo "Scan for additional .ini files in: (none)" ;;
  -m) printf '[PHP Modules]\nCore\ndate\njson\nmbstring\nmysqli\n\n[Zend Modules]\n' ;;
  *) exec "$PHP_REAL" "\$@" ;;
esac
EOF
  chmod +x "$1"
}
L=$W/legacy; O=$W/ok
mkdir -p "$L/lib" "$L/inc" "$L/vendor/x" "$L/node_modules/y" "$L/.git" "$O"
{ echo '<?php'; for _ in $(seq 2 11); do echo '// filler'; done; echo 'while (list($k, $v) = each($arr)) { echo $k; }'; } >"$L/lib/a.php"
printf '<?php\n// 1\n// 2\n// 3\n// 4\n// match is a keyword from PHP 8.0\nfunction match($a) { return $a; }\n' >"$L/inc/x.inc"
{ echo '<?php'; for i in $(seq 1 14); do echo "legacy_test_call($i);"; done; } >"$L/lib/ext.php"
printf '<?php\n$c = mysql_connect("h");\n$a = each($b);\n' | tee "$L/vendor/x/v.php" "$L/node_modules/y/n.php" "$L/.git/g.php" >/dev/null
python3 -c "open('$L/big.php','w').write('<?php\n' + 'x' * (2097153 - 6))"
printf '; site ini\nmemory_limit = 128M\ntrack_errors = On\n' >"$L/.user.ini"
cat >"$L/composer.json" <<'EOF'
{"name": "acme/legacy", "require": {"vendor-test/a": "^2.1"}, "scripts": {"post-install-cmd": "touch /tmp/qp-test-marker"}}
EOF
cat >"$L/composer.lock" <<'EOF'
{"packages": [{"name": "vendor-test/a", "version": "2.1.0", "require": {"php": "^7.4 || ~8.0.0"}}], "packages-dev": []}
EOF
for i in 1 2; do printf '<?php\necho %d;\n' "$i" >"$O/f$i.php"; done
mkdir -p "$SD/feeds/cache/packagist"
python3 - "$SD/feeds/cache/packagist/vendor-test~a.json" <<'PY'
import json, sys, time
json.dump({'fetched_at': time.time(), 'url': 'https://repo.packagist.org/p2/vendor-test/a.json', 'body': {'packages': {
    'vendor-test/a': [{'version': '2.4.0', 'require': {'php': '>=8.1'}}, {'version': '2.3.0', 'require': {'php': '^7.4 || ^8.0'}},
                      {'version': '2.2.0', 'require': {'php': '^7.4'}}, {'version': '2.1.0'}]}}}, open(sys.argv[1], 'w'))
PY
sha_tree() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c1-64); }
L_SHA=$(sha_tree "$L")

scan_with() {   # scan_with BINS: scan, then put the three sites on the 7.4 runtime
  QP_PHP_BINS="$1" QP_NODE_BINS=" " qp scan --offline --json --only php,sites --path "$W" >"$J" 2>/dev/null
  R74=$(json_get "$J" "[r['runtime_id'] for r in d['result']['runtimes'] if r['bin']=='$B/p74/bin/php'][0]")
  python3 - "$SD/state/last-scan.json" "$R74" "$W" <<'PY'
import json, sys
p, rid, www = sys.argv[1:]
d = json.load(open(p))
def site(sid, root):
    return {"site_id": sid, "site_key": sid, "pb_id": "PB-005", "server_names": [sid], "docroot": root,
            "owner_user": "root", "binding_kind": "nginx_fastcgi", "binding_ref": "/etc/nginx/sites-enabled/%s:1" % sid,
            "current_branch": "7.4", "current_bin": None, "runtime_id": rid, "runtime_endpoint": "unix:/run/php/php7.4-fpm.sock",
            "log_sources": [], "hc_urls": ["http://%s/" % sid], "hc_mode": "full"}
d["result"]["sites"] = [site("legacy.test", www + "/legacy"), site("ok.test", www + "/ok"), site("c.test", www + "/missing")]
json.dump(d, open(p, "w"))
PY
}
scan_with "$B/p74/bin/php"

# --- plan create: offline, no tools, no $NEW_BIN yet --------------------------------------
qp plan create --runtime-id "$R74" --target 8.5 --offline --json >"$J" 2>/dev/null; rc=$?
P=$(json_get "$J" 'd["result"]["plan"]["plan_id"]')
assert_eq "plan create cross_branch with the compatibility scan: exit 0" "$rc $(json_get "$J" 'd["result"]["plan"]["mode"]')" "0 cross_branch"
check "plan create output valid against schema" schema_ok "$J"
codes=$(json_get "$J" 'sorted({e["code"] for e in d["errors"]})')
assert_contains "TC-CMPT-002 KQ2: offline, no tools -> ERR-CMPT-424-01" "$codes" "ERR-CMPT-424-01"
assert_contains "TC-CMPT-011: no PHP 8.5 -> ERR-ENV-412-01" "$codes" "ERR-ENV-412-01"
assert_contains "TC-CMPT-006 KQ1: file of 2,097,153 bytes -> ERR-CMPT-413-01" "$codes" "ERR-CMPT-413-01"
assert_eq "ERR-ENV-412-01 message names PHP 8.5" "$(json_get "$J" '[e["message"] for e in d["errors"] if e["code"]=="ERR-ENV-412-01"][0]')" \
  "PHP 8.5 is not installed on the server."
qp plan compat "$P" --site legacy.test --json >"$J" 2>/dev/null; rc=$?
S="d['result']['sites'][0]"
assert_eq "plan compat: exit 0, one site" "$rc $(json_get "$J" 'len(d["result"]["sites"])')" "0 1"
assert_eq "TC-CMPT-004 KQ1: lib/a.php line 12 BC-PHP-80-02 error" \
  "$(json_get "$J" "[(h['line'], h['rule_id'], h['level']) for h in ${S}['hits'] if h['file']=='lib/a.php']")" "[(12, 'BC-PHP-80-02', 'error')]"
assert_eq "TC-CMPT-004 KQ2: snippets <= 200 characters, hit ids H-<12 hex>" \
  "$(json_get "$J" "all(len(h['snippet']) <= 200 and len(h['hit_id']) == 14 for h in ${S}['hits'])")" "True"
assert_eq "TC-CMPT-006 KQ1/KQ2: big.php skipped; no hit in vendor/, node_modules/, .git/" \
  "$(json_get "$J" "([s['file'] for s in ${S}['skipped_files']], [h['file'] for h in ${S}['hits'] if h['file'].split('/')[0] in ('vendor','node_modules','.git')])")" \
  "(['big.php'], [])"
assert_eq "TC-CMPT-006 KQ3: rules of (7.4, 8.5] only" \
  "$(json_get "$J" "(any(r.startswith('BC-PHP-74') for r in ${S}['rules_applied']), 'BC-PHP-85-01' in ${S}['rules_applied'])")" "(False, True)"
assert_eq "TC-CMPT-011: lint PENDING, phpcompat PENDING (no tools), code_scan done" \
  "$(json_get "$J" "(${S}['parts']['lint_new_bin'], ${S}['parts']['phpcompat'], ${S}['parts']['code_scan'])")" "('pending', 'pending', 'done')"
assert_eq "TC-CMPT-019 KQ1: .user.ini line 3 track_errors removed_in 8.0" \
  "$(json_get "$J" "[(f['file'], f['line'], f['directive'], f['removed_in']) for f in ${S}['ini_findings']]")" "[('.user.ini', 3, 'track_errors', '8.0')]"
assert_eq "TC-CMPT-019 KQ2 / 020 / 021: mysqli available, legacy_test missing (14 calls), unused_test 0 calls" \
  "$(json_get "$J" "sorted((g['extension'], g['resolution'], g['usage_hits']) for g in ${S}['extension_gaps'])")" \
  "[('legacy_test', 'missing', 14), ('mbstring', 'available', 0), ('mysqli', 'available', 0), ('unused_test', 'missing', 0)]"
assert_eq "TC-CMPT-013: vendor-test/a 2.1.0 blocks 8.5.12, minimum compatible 2.3.0 (Packagist cache)" \
  "$(json_get "$J" "[(b['package'], b['version'], b['min_compatible_version']) for b in ${S}['composer_blockers']]")" \
  "[('vendor-test/a', '2.1.0', '2.3.0')]"
assert_eq "TC-CMPT-014 KQ2: no composer.phar offline -> composer_platform PENDING" "$(json_get "$J" "${S}['parts']['composer_platform']")" "pending"
assert_eq "TC-CMPT-015 KQ2: post-install script not run, composer files unchanged" \
  "$(test -e /tmp/qp-test-marker && echo marker; sha_tree "$L")" "$L_SHA"

qp plan compat "$P" --site nope.test --json >"$J" 2>/dev/null; rc=$?
assert_eq "plan compat: site not in the plan -> ERR-CON-404-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CON-404-01"
assert_contains "plan compat (text): one line per site verdict" "$(qp plan compat "$P" 2>/dev/null)" "legacy.test                    FAIL"
check "plan compat output valid against schema" schema_ok "$J"
qp plan show "$P" --json >"$J" 2>/dev/null
PL="d['result']['plan']"
assert_eq "FR-CMPT-RES-001: verdicts legacy FAIL (errors), ok PENDING, c PENDING (code_scan)" \
  "$(json_get "$J" "[(v['site_id'], v['status'], v['pending_parts'] == ['code_scan']) for v in ${PL}['compat_verdicts']]")" \
  "[('ok.test', 'PENDING', False), ('c.test', 'PENDING', True), ('legacy.test', 'FAIL', False)]"
assert_eq "TC-PLAN-009 KQ1: blocked_sites, FAIL site last, canary = first site" \
  "$(json_get "$J" "([b['site_id'] for b in ${PL}['blocked_sites']], ${PL}['site_order'][-1], ${PL}['canary_site_id'])")" "(['legacy.test'], 'legacy.test', 'ok.test')"
assert_eq "TC-PLAN-009 KQ1: P5 items of legacy.test PENDING with a blocking reason" \
  "$(json_get "$J" "sorted({(i['status'], (i['reason'] or '')[:31]) for i in ${PL}['checklist_items'] if i['phase']=='P5' and i['site_id']=='legacy.test' and i['status']!='SKIPPED'})")" \
  "[('PENDING', 'blocked: compatibility FAIL (2 ')]"
assert_eq "TC-PLAN-011: upgrade_items rows carry component_type..chk_id; Composer row -> P4 item" \
  "$(json_get "$J" "[(r['component_type'], r['name'], r['min_compatible'], (r['chk_id'] or '')[:8]) for r in ${PL}['upgrade_items'] if r['site_id']=='legacy.test' and r['component_type']=='composer']")" \
  "[('composer', 'vendor-test/a', '2.3.0', 'CHK-PHP-')]"
CK=$(json_get "$J" "[r['chk_id'] for r in ${PL}['upgrade_items'] if r['site_id']=='legacy.test' and r['component_type']=='composer'][0]")
assert_eq "FR-PLAN-DEP-001: the Composer P4 item names the package" \
  "$(json_get "$J" "[(i['phase'], i['action'][:40]) for i in ${PL}['checklist_items'] if i['item_key']=='$CK@legacy.test']")" \
  "[('P4', 'Upgrade Composer package vendor-test/a 2')]"
assert_eq "TC-CMPT-020 KQ1 / 021 KQ2: legacy_test P4 item PENDING, unused_test SKIPPED" \
  "$(json_get "$J" "sorted((i['component']['name'], i['status']) for i in ${PL}['checklist_items'] if i.get('component') and i['component']['type']=='extension' and i['site_id']=='legacy.test')")" \
  "[('legacy_test', 'PENDING'), ('unused_test', 'SKIPPED')]"
LINT=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='legacy.test' and (i['cli_action'] or '').endswith('--parts lint_new_bin')][0]")
BC=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='legacy.test' and (i['cli_action'] or '').endswith('--parts code_scan')][0]")
PC=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='legacy.test' and (i['cli_action'] or '').endswith('--parts phpcompat')][0]")
RECT=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='legacy.test' and (i['cli_action'] or '').startswith('compat-rector')][0]")
P5=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='legacy.test' and i['phase']=='P5' and i['status']=='PENDING' and i['exec_type']!='MANUAL'][0]")
assert_eq "P3 items from the scan: BC rules FAILED, lint PENDING" \
  "$(json_get "$J" "[i['status'] for i in ${PL}['checklist_items'] if i['item_key'] in ('$BC@legacy.test', '$LINT@legacy.test')]")" "['PENDING', 'FAILED']"

# --- control actions: approve, run a blocked P5 item, waive ----------------------------------
qp plan approve "$P" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-PLAN-021 KQ1: approve refused, missing names c.test" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-412-01"
assert_contains "TC-PLAN-021 KQ1: missing lists the site without a code scan" "$(json_get "$J" 'd["errors"][0]["message"]')" "compatibility scan of 1 site(s): c.test"
qp plan run "$P" "$P5" --site legacy.test --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-PLAN-009 KQ2: P5 of a FAIL site -> ERR-UPG-409-01" "$rc $(json_get "$J" '[e["code"] + ": " + e["message"] for e in d["errors"]]')" \
  "2 ['ERR-UPG-409-01: Site legacy.test has 3 unresolved compatibility errors.']"
qp plan compat "$P" --site legacy.test --level error --rule 'BC-PHP-*' --waived false --json >"$J" 2>/dev/null
H=$(json_get "$J" "','.join(h['hit_id'] for h in d['result']['sites'][0]['hits'])")
assert_eq "plan compat filters: unwaived BC error hits (each(), function match)" "$(json_get "$J" "sorted(h['file'] for h in d['result']['sites'][0]['hits'])")" "['inc/x.inc', 'lib/a.php']"
qp plan waive "$P" --site legacy.test --hits "$H" --reason 'too short' --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-029 KQ1: reason < 20 -> ERR-PLAN-422-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-422-01"
qp plan waive "$P" --site legacy.test --hits H-xyz --reason 'each() is in dead code never called' --json >"$J" 2>/dev/null; rc=$?
assert_eq "FR-CLI-CMD-002: hit id must match ^H-[0-9a-f]{12}$" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp plan waive "$P" --site legacy.test --hits H-0123456789ab --reason 'each() is in dead code never called' --json >"$J" 2>/dev/null; rc=$?
assert_eq "plan waive: hit not in the result -> ERR-CON-422-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CON-422-01"
qp plan compat "$P" --site legacy.test --json >"$J" 2>/dev/null
assert_eq "TC-CMPT-029 KQ2: verdict still FAIL after refused waivers" "$(json_get "$J" "d['result']['sites'][0]['verdict']['status']")" "FAIL"
n0=$(grep -c '"plan_waive_hits"' "$SD"/audit/*.jsonl 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
qp plan waive "$P" --site legacy.test --hits "$H" --reason 'each() is in dead code never called' --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-030 KQ1: waived, verdict FAIL -> still FAIL (Composer blocker), waived = 2" \
  "$rc $(json_get "$J" '(d["result"]["waived"] == "'"$H"'".split(","), d["result"]["compat_verdict"]["status"], d["result"]["compat_verdict"]["waived"], d["result"]["compat_verdict"]["blockers"])')" \
  "0 (True, 'FAIL', 2, 1)"
n1=$(grep -c '"plan_waive_hits"' "$SD"/audit/*.jsonl 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
assert_eq "TC-CMPT-030 KQ1: audit INTENT + RESULT for the waiver" "$((n1 - n0))" "2"
qp plan waive "$P" --site legacy.test --hits "$H" --reason 'each() is in dead code never called' --json >"$J" 2>/dev/null
assert_eq "plan waive again: already_waived" "$(json_get "$J" '(d["result"]["waived"], len(d["result"]["already_waived"]))')" "([], 2)"
qp plan show "$P" --json >"$J" 2>/dev/null
assert_eq "waiver closes the BC rules item (DONE)" "$(json_get "$J" "[i['status'] for i in ${PL}['checklist_items'] if i['item_key']=='$BC@legacy.test']")" "['DONE']"

# --- plan run of a compat item: reuse (TC-CMPT-030 KQ3), Rector offline (TC-CMPT-032/033) --
qp plan run "$P" "$BC" --site legacy.test --offline --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-03: a DONE item is not run again" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
qp plan run "$P" "$PC" --site legacy.test --offline --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-030 KQ3: same fingerprint and target, nothing new can run -> result reused" \
  "$rc $(json_get "$J" '(d["result"]["run"]["reused"], d["result"]["item"]["status"])')" "1 (True, 'PENDING')"
qp plan run "$P" "$RECT" --site legacy.test --offline --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-032 KQ1: no Rector offline -> ERR-CMPT-424-01, item PENDING" \
  "$rc $(json_get "$J" '([e["code"] for e in d["errors"]], d["result"]["item"]["status"])')" "1 (['ERR-CMPT-424-01'], 'PENDING')"
qp plan run "$P" "$RECT" --site legacy.test --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "FR-CMPT-RCT-001: apply needs a reviewed dry-run diff first -> ERR-CLI-428-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-428-01"
assert_eq "TC-CMPT-033 KQ1: docroot unchanged" "$(sha_tree "$L")" "$L_SHA"
check "TC-CMPT-033: no tool file under any docroot" test -z "$(find "$W" -name 'phpcs' -o -name 'rector' -o -name '*.phar')"

# --- $NEW_BIN installed: lint (TC-CMPT-010, 012), real PHPCompatibility when tools are there --
new_php "$B/p85/bin/php"
if [ -n "${QP_TEST_TOOLS_DIR:-}" ] && [ -f "$QP_TEST_TOOLS_DIR/tools_manifest.json" ]; then
  rm -rf "$SD/tools/php"; mkdir -p "$SD/tools"; cp -a "$QP_TEST_TOOLS_DIR" "$SD/tools/php"; REAL_TOOLS=1
else
  REAL_TOOLS=0
fi
scan_with "$B/p74/bin/php $B/p85/bin/php"
qp plan show "$P" --json >"$J" 2>/dev/null
assert_eq "BR-PLAN-006: new scan -> plan stale (SCAN_CHANGED)" "$(json_get "$J" "(${PL}['stale'], 'SCAN_CHANGED' in ${PL}['stale_reasons'])")" "(True, True)"
qp plan run "$P" "$LINT" --site legacy.test --offline --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-012 KQ2: inc/x.inc parse error -> lint item FAILED, rescan (not reused)" \
  "$rc $(json_get "$J" '(d["result"]["run"]["reused"], d["result"]["item"]["status"], d["result"]["run"]["verdict"]["status"])')" "1 (False, 'FAILED', 'FAIL')"
qp plan compat "$P" --site legacy.test --rule php-l --json >"$J" 2>/dev/null
assert_eq "TC-CMPT-012 KQ1: inc/x.inc line 7 Parse error" \
  "$(json_get "$J" "[(h['file'], h['line'], h['snippet'][:11]) for h in d['result']['sites'][0]['hits']]")" "[('inc/x.inc', 7, 'Parse error')]"
assert_eq "TC-CMPT-010: lint of every file with \$NEW_BIN" \
  "$(json_get "$J" "(d['result']['sites'][0]['lint']['bin'], d['result']['sites'][0]['lint']['files'], d['result']['sites'][0]['lint']['checked'])")" \
  "('$B/p85/bin/php', 3, 2)"
assert_eq "waivers kept across the rescan (by hit_id)" "$(json_get "$J" "d['result']['sites'][0]['verdict']['waived']")" "2"
qp plan show "$P" --json >"$J" 2>/dev/null
OKL=$(json_get "$J" "[i['chk_id'] for i in ${PL}['checklist_items'] if i['site_id']=='ok.test' and (i['cli_action'] or '').endswith('--parts lint_new_bin')][0]")
qp plan run "$P" "$OKL" --site ok.test --offline --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-010 KQ2: 0 parse error -> lint item DONE" "$rc $(json_get "$J" 'd["result"]["item"]["status"]')" "0 DONE"
if (( REAL_TOOLS )); then
  qp plan compat "$P" --site ok.test --json >"$J" 2>/dev/null
  assert_eq "TC-CMPT-007 / TC-CMPT-028: real PHPCompatibility on ok.test -> phpcompat done, verdict PASS" \
    "$(json_get "$J" "(d['result']['sites'][0]['parts']['phpcompat'], d['result']['sites'][0]['phpcs']['test_version'], d['result']['sites'][0]['verdict']['status'])")" \
    "('done', '8.5', 'PASS')"
  qp plan compat "$P" --site legacy.test --json >"$J" 2>/dev/null
  assert_contains "TC-CMPT-007 KQ3: PHPCompatibility sniff codes as rule_id" \
    "$(json_get "$J" "sorted({h['rule_id'] for h in d['result']['sites'][0]['hits'] if h['source']=='phpcompatibility'})")" "PHPCompatibility.FunctionUse.RemovedFunctions.eachDeprecatedRemoved"
  assert_eq "TC-CMPT-015: check-platform-reqs ran on the copy with 8.5 (vendor-test/a blocks), no script run" \
    "$(json_get "$J" "(d['result']['sites'][0]['parts']['composer_platform'], d['result']['sites'][0]['composer_platform']['exit_code'] != 0)") $(test -e /tmp/qp-test-marker && echo marker)" "('done', True) "
  if [ -d "$SD/tools/php/rector__rector" ]; then
    qp plan run "$P" "$RECT" --site legacy.test --offline --dry-run --json >"$J" 2>/dev/null; rc=$?
    assert_eq "TC-CMPT-031 KQ1/KQ2: Rector --dry-run on a copy in STATE_DIR/work, diff kept in the plan, item PENDING" \
      "$rc $(json_get "$J" "(d['result']['run']['rector']['copy'].startswith('$SD/work/$P/'), d['result']['run']['rector']['files_changed'] > 0, d['result']['item']['status'])")" \
      "0 (True, True, 'PENDING')"
    check "TC-CMPT-031 KQ2: rector-legacy.test.diff in the plan directory" test -s "$SD/plans/$P/rector-legacy.test.diff"
    qp plan run "$P" "$RECT" --site legacy.test --offline --yes --json >"$J" 2>/dev/null; rc=$?
    assert_eq "TC-CMPT-031 KQ3: apply after review writes the copy only, item DONE" "$rc $(json_get "$J" 'd["result"]["item"]["status"]')" "0 DONE"
  else
    echo "# skip real Rector: no rector__rector in QP_TEST_TOOLS_DIR"
  fi
  qp plan show "$P" --json >"$J" 2>/dev/null
  assert_eq "TC-PLAN-008: ok.test PASS is the canary" "$(json_get "$J" "${PL}['canary_site_id']")" "ok.test"
else
  echo "# skip real PHPCompatibility: set QP_TEST_TOOLS_DIR"
fi
assert_eq "TC-CMPT-033: docroot still unchanged after the rescan" "$(sha_tree "$L")" "$L_SHA"
check "TC-CMPT-015 KQ3: composer work copy removed" test -z "$(find "$SD/work" -type d -name composer 2>/dev/null)"

# --- framework range limits the candidates (FR-CMPT-FWK-001, TC-CMPT-026) ------------------
mkdir -p "$W/lara"
echo '{"packages": [{"name": "laravel/framework", "version": "v9.52.0", "require": {"php": "^8.0.2"}}]}' >"$W/lara/composer.lock"
python3 - "$SD/state/last-scan.json" "$W/lara" <<'PY'
import json, sys
p, root = sys.argv[1:]
d = json.load(open(p))
s = dict(d["result"]["sites"][0], site_id="lara.test", site_key="lara.test", docroot=root, server_names=["lara.test"])
d["result"]["sites"] = [s]
json.dump(d, open(p, "w"))
PY
qp assess --runtime-id "$R74" --candidates --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CMPT-026: laravel 9.52.0 (PHP 8.0 - 8.2, 8.2 EOL < T+365) -> ERR-SCN-409-01, upgrade the framework first" \
  "$rc $(json_get "$J" '[e["message"] for e in d["errors"] if e["code"]=="ERR-SCN-409-01"]')" \
  "0 ['No target version is compatible with laravel 9.52.0. Upgrade laravel 9.52.0 first (PHP 8.0 - 8.2).']"
assert_eq "TC-CMPT-026: branches above 8.2 not selectable (outside the framework range)" \
  "$(json_get "$J" "sorted({c['selectable'] for c in d['result']['candidates'] if c['branch'] in ('8.3', '8.4', '8.5')})")" "[False]"

# --- Node.js app found through systemd (PB-017) as a site; engines check (FR-CMPT-NPM-001) -----
# Private to this mount namespace: /run/systemd/system marks systemd, the unit dir is a tmpfs.
mount -t tmpfs tmpfs /run/systemd && mkdir -p /run/systemd/system && mount -t tmpfs tmpfs /etc/systemd/system
fake_node "$T/n20" 20.20.2 115; fake_node "$T/n24" 24.22.1 137
dpkg_owns "$T/n24/bin/node" nodejs 24.22.1-1nodesource1; rm -rf "$T/n24/lib"
API=$W/api; mkdir -p "$API"
echo '{"name": "api", "version": "1.0.0", "engines": {"node": ">=18"}}' >"$API/package.json"
printf '%s\n' '{"name": "api", "lockfileVersion": 3, "packages": {"": {"name": "api"},' \
  ' "node_modules/pkg-a": {"version": "1.0.0", "engines": {"node": ">=18"}},' \
  ' "node_modules/pkg-b": {"version": "2.0.0", "engines": {"node": "<=20"}},' \
  ' "node_modules/pkg-c": {"version": "3.0.0", "engines": {"node": "<=16"}, "dev": true},' \
  ' "node_modules/pkg-d": {"version": "4.0.0"}}}' >"$API/package-lock.json"
printf '[Service]\nUser=root\nWorkingDirectory=%s\nExecStart=%s %s/server.js\n' "$API" "$T/n20/bin/node" "$API" >/etc/systemd/system/api.service
QP_PHP_BINS=" " QP_NODE_BINS="$T/n20/bin/node $T/n24/bin/node" qp scan --offline --json --only node,sites >"$J" 2>/dev/null
N20=$(json_get "$J" "[r['runtime_id'] for r in d['result']['runtimes'] if r['bin']=='$T/n20/bin/node'][0]")
assert_eq "PB-017: systemd app is a site of the Node.js 20 runtime" \
  "$(json_get "$J" "[(s['site_id'], s['binding_kind'], s['docroot'], s['runtime_id']=='$N20', s['pb_id']) for s in d['result']['sites']]")" \
  "[('app:systemd:api', 'systemd_execstart', '$API', True, 'PB-017')]"
assert_eq "PB-017: runtime lists the app as app and site" \
  "$(json_get "$J" "[(r['apps'][0]['unit_or_name'], r['site_ids']) for r in d['result']['runtimes'] if r['runtime_id']=='$N20']")" "[('api.service', ['app:systemd:api'])]"
qp plan create --runtime-id "$N20" --target 24 --reason 'Chờ Node.js 26 vào LTS ngày 2026-10-28' --offline --json >"$J" 2>/dev/null; rc=$?
PN=$(json_get "$J" 'd["result"]["plan"]["plan_id"]')
assert_eq "Node.js plan 20 -> 24 with the app compatibility scan" "$rc $(json_get "$J" 'd["result"]["plan"]["mode"]')" "0 cross_branch"
assert_contains "TC-CMPT-018 KQ2: pkg-d without engines, offline -> ERR-FEED-503-01" "$(json_get "$J" '[e["code"] for e in d["errors"]]')" "ERR-FEED-503-01"
qp plan compat "$PN" --json >"$J" 2>/dev/null
S="d['result']['sites'][0]"
assert_eq "TC-CMPT-016 KQ1 / TC-CMPT-018 KQ1: pkg-b error, pkg-c (dev) warning" \
  "$(json_get "$J" "[(v['package'], v['severity']) for v in ${S}['npm_engine_violations']]")" "[('pkg-b', 'error'), ('pkg-c', 'warning')]"
assert_eq "TC-CMPT-018 KQ2: pkg-d unknown offline" "$(json_get "$J" "[u['package'] for u in ${S}['npm_unknown']]")" "['pkg-d']"
assert_eq "TC-PLAN-013 KQ2: dev violation is a warning row without a P4 item; pkg-b has one" \
  "$(json_get "$J" "sorted((r['name'], r['chk_id'] is not None) for r in d['result']['upgrade_items'])")" "[('pkg-b', True), ('pkg-c', False)]"
qp plan show "$PN" --json >"$J" 2>/dev/null
assert_eq "FR-CMPT-NPM-001: engines item FAILED, verdict FAIL" \
  "$(json_get "$J" "(sorted({i['status'] for i in ${PL}['checklist_items'] if (i['cli_action'] or '').endswith('--parts npm_engines')}), ${PL}['compat_verdicts'][0]['status'])")" \
  "(['FAILED'], 'FAIL')"

t_done
