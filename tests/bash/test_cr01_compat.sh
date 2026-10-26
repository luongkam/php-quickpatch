#!/usr/bin/env bash
# CR-01 — `compat --path DIR --target N`: Node.js compatibility of project directories
# (AWS Lambda repository) with a target branch, and its HTML/Markdown report. Uses the
# fake feeds server for lifecycle (fixture bundle), OSV (SRC-007) and the npm registry.
# Day T = 2026-10-22 (QP_TODAY).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'feeds_cleanup; rm -rf "$T"' EXIT
# shellcheck disable=SC2034  # FX is read by the stubs
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init
SD=/var/lib/php-quickpatch
feeds_fixture
export QP_TODAY=2026-10-22
J=$T/out.json
qp() { bash "$QP" "$@"; }
printf '[registry]\nnpm_url = %s/NPM\n' "$FEEDS_BASE" >>"$SD/feeds/sources.conf"

# --- fixture: SAM repository with two Lambda functions on nodejs18.x ----------------------
R=$T/repo; F1=$R/functions/reset; F2=$R/functions/verify
mkdir -p "$F1" "$F2/node_modules/addon-x" "$R/.github/workflows"
cp "$QP_ROOT/tests/fixtures/compat/template.yaml" "$R/template.yaml"
printf 'jobs:\n  t:\n    steps:\n      - uses: actions/setup-node@v4\n        with:\n          node-version: 18\n' >"$R/.github/workflows/ci.yml"
cp "$QP_ROOT/tests/fixtures/compat/reset-package.json" "$F1/package.json"
cp "$QP_ROOT/tests/fixtures/compat/reset-package-lock.json" "$F1/package-lock.json"
cp "$QP_ROOT/tests/fixtures/compat/reset-index.js" "$F1/index.js"
echo '{"name": "verify", "dependencies": {"lodash": "^4.17.20"}}' >"$F2/package.json"
echo '{"name": "verify", "lockfileVersion": 3, "packages": {"": {}, "node_modules/lodash": {"version": "4.17.20"}, "node_modules/addon-x": {"version": "1.0.0"}}}' >"$F2/package-lock.json"
echo '{"name": "addon-x", "version": "1.0.0"}' >"$F2/node_modules/addon-x/package.json"
echo '{"targets": []}' >"$F2/node_modules/addon-x/binding.gyp"
echo 'module.exports = 1;' >"$F2/node_modules/addon-x/index.js"
printf "exports.handler = async () => ({ statusCode: 200 });\n" >"$F2/index.js"
# OSV: axios has two advisories (fixed 0.21.2; fixed 0.28.0 or 1.6.0), lodash one, aws-sdk one with no fix.
printf 'axios 0.21.1 GHSA-aaaa-0001,GHSA-aaaa-0002\nlodash 4.17.20 GHSA-bbbb-0001\naws-sdk 2.1000.0 GHSA-cccc-0001\n' >"$FEEDS_SRV/osv.vulns"
mkdir -p "$FEEDS_SRV/osv-vulns" "$FEEDS_SRV/npm"
cp "$QP_ROOT"/tests/fixtures/compat/osv/*.json "$FEEDS_SRV/osv-vulns/"
cp "$QP_ROOT"/tests/fixtures/compat/npm/*.json "$FEEDS_SRV/npm/"
sha_tree() { (cd "$1" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c1-64); }
R_SHA=$(sha_tree "$R")

# --- arguments ----------------------------------------------------------------------------
qp compat --path "$R" --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: --target missing -> ERR-CLI-400-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp compat --path "$T/none" --target 22 --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: --path not a directory -> ERR-CLI-400-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp compat --path "$R" --target 22 --runtime php --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: --runtime php not available" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp compat --path "$R" --target 22 --report "$T/r.txt" --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: --report must be .html or .md" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
fake_node "$T/n20" 20.20.2
qp compat --path "$R" --target 22 --node-bin "$T/n20/bin/node" --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: --node-bin of another major is refused" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"

# --- scan of the repository ---------------------------------------------------------------
qp compat --path "$R" --target 22 --report "$T/report.html" --json >"$J" 2>"$T/err"; rc=$?
P="d['result']['projects']"
assert_eq "CR-01: exit 1 (work to do), schema qp.compat/1" "$rc $(json_get "$J" 'd["schema"]')" "1 qp.compat/1"
check "CR-01: output valid against schema" schema_ok "$J"
assert_eq "CR-01: two projects, current branch 18 from the SAM template, target patch from the bundle" \
  "$(json_get "$J" "([(p['name'], p['current_branch'], p['current_source']) for p in $P], d['result']['target_patch'])")" \
  "([('reset', '18', 'declarations'), ('verify', '18', 'declarations')], '22.23.4')"
assert_eq "CR-01: Runtime of each function attributed by CodeUri / Handler" \
  "$(json_get "$J" "[(p['name'], [(x['file'], x['line'], x['kind']) for x in p['declarations']]) for p in $P]")" \
  "[('reset', [('template.yaml', 6, 'lambda_runtime')]), ('verify', [('template.yaml', 11, 'lambda_runtime')])]"
assert_eq "CR-01: CI node-version is a shared declaration to change" \
  "$(json_get "$J" "[(x['file'], x['kind'], x['to_change']) for x in d['result']['shared_declarations']]")" \
  "[('.github/workflows/ci.yml', 'ci_node_version', True)]"
assert_eq "CR-01: lifecycle 18 EOL, 22 has 190 days (< 365), 24 recommended" \
  "$(json_get "$J" "(d['result']['lifecycle']['current']['status'], d['result']['lifecycle']['target']['days_to_eol'], d['result']['lifecycle']['target_ok'], d['result']['lifecycle']['recommended'])")" \
  "('EOL', 190, False, '24')"
assert_eq "CR-01: axios 0.21.1 -> 0.28.0 fixes both advisories on the same major; aws-sdk has no fix" \
  "$(json_get "$J" "[(v['package'], v['severity'], v['fix_version'], v['major_bump'], v['unfixed_advisories']) for v in ${P}[0]['vulnerabilities']]")" \
  "[('axios', 'high', '0.28.0', False, []), ('aws-sdk', 'low', None, None, ['GHSA-cccc-0001'])]"
assert_eq "CR-01: lodash 4.17.20 -> 4.17.21 (medium)" \
  "$(json_get "$J" "[(v['package'], v['severity'], v['fix_version']) for v in ${P}[1]['vulnerabilities']]")" "[('lodash', 'medium', '4.17.21')]"
assert_eq "CR-01: aws-sdk v2 migration (catalog) with its call site; request deprecated on npm" \
  "$(json_get "$J" "[(x['package'], x['source'], x['call_sites']) for x in ${P}[0]['deprecated']]")" \
  "[('aws-sdk', 'catalog', [{'file': 'index.js', 'line': 1}]), ('request', 'npm', [])]"
assert_eq "CR-01: old-engines 1.0.0 (engines <=20) blocks Node.js 22 -> reset FAIL" \
  "$(json_get "$J" "([(v['package'], v['severity']) for v in ${P}[0]['npm_engine_violations']], ${P}[0]['verdict']['status'])")" \
  "([('old-engines', 'error')], 'FAIL')"
assert_eq "CR-01: url.parse() on line 2 -> BC-NODE-20-01 warning" \
  "$(json_get "$J" "[(h['file'], h['line'], h['rule_id'], h['level']) for h in ${P}[0]['hits']]")" "[('index.js', 2, 'BC-NODE-20-01', 'warning')]"
assert_eq "CR-01: native addon of verify not loaded without --node-bin -> PENDING" \
  "$(json_get "$J" "(${P}[1]['native_addons'], ${P}[1]['verdict']['status'], ${P}[1]['verdict']['pending_parts'])")" \
  "([{'package': 'addon-x', 'load_ok': None}], 'PENDING', ['native_addons'])"
assert_eq "CR-01: work items of reset" "$(json_get "$J" "[(w['kind'], w['count'], w['size']) for w in ${P}[0]['work_items']]")" \
  "[('runtime_declarations', 1, 'S'), ('vuln_minor_upgrades', 1, 'S'), ('vuln_no_fix', 1, 'M'), ('engines_violations', 1, 'M'), ('migrate_package', 1, 'M'), ('migrate_package', 1, 'S'), ('code_warnings', 1, 'S'), ('regression_test', 1, 'M')]"
assert_eq "CR-01: the scanned repository is not modified" "$(sha_tree "$R")" "$R_SHA"
check "CR-01: --report written" test -s "$T/report.html"
RD=$(json_get "$J" "d['result']['artifacts_dir']")
check "CR-01: report.html, report.md and result.json kept in STATE_DIR/reports" test -s "$RD/report.html" -a -s "$RD/report.md" -a -s "$RD/result.json"
assert_eq "CR-01: report is escaped (no script from the code), self-contained" \
  "$(grep -c '<script' "$T/report.html") $(grep -c 'https\?://[^"]*\.\(css\|js\)' "$T/report.html") $(grep -c '&lt;script&gt;' "$T/report.html")" "0 0 1"
assert_contains "CR-01: report names the recommended branch" "$(cat "$T/report.html")" "Node.js 24 is recommended"
assert_contains "CR-01: report suggests the new Lambda runtime" "$(cat "$T/report.html")" "Runtime: nodejs22.x"
check "CR-01: no request to the real registries" test -z "$(grep -E 'registry\.npmjs|osv\.dev' "$T/err")"

# --- Vietnamese text mode and Markdown ------------------------------------------------------
out=$(qp compat --path "$R" --target 22 --lang vi --report "$T/report.md" 2>/dev/null); rc=$?
assert_eq "CR-01: text mode exit 1" "$rc" "1"
assert_contains "CR-01: Vietnamese summary" "$out" "Báo cáo tương thích Node.js 18 -> 22"
assert_contains "CR-01: Vietnamese lifecycle advice" "$out" "Khuyến nghị Node.js 24."
assert_contains "CR-01: Markdown report in Vietnamese" "$(cat "$T/report.md")" "## Khối lượng việc"

# --- target 24 with a Node.js 24 binary for the native addon ---------------------------------
fake_node "$T/n24" 24.22.1 137
qp compat --path "$F2" --target 24 --node-bin "$T/n24/bin/node" --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: one project path, addon loaded with --node-bin, current from engines-less project unknown" \
  "$(json_get "$J" "([a['load_ok'] for a in ${P}[0]['native_addons']], ${P}[0]['current_branch'])")" "([True], None)"
assert_eq "CR-01: --current fills the branch when nothing declares it" \
  "$(qp compat --path "$F2" --target 24 --current 18 --json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["result"]["projects"][0]["current_branch"], d["result"]["projects"][0]["current_source"], d["result"]["lifecycle"]["target_ok"])')" \
  "18 option True"

# --- offline: no cached OSV answer for a new lockfile -------------------------------------------
echo '{"name": "verify", "lockfileVersion": 3, "packages": {"": {}, "node_modules/lodash": {"version": "4.17.21"}}}' >"$F2/package-lock.json"
qp compat --path "$F2" --target 22 --current 18 --offline --json >"$J" 2>/dev/null; rc=$?
assert_eq "CR-01: offline without cache -> ERR-FEED-503-02, vulnerabilities pending" \
  "$rc $(json_get "$J" "([e['code'] for e in d['errors']], ${P}[0]['vulnerabilities'], 'vulnerabilities' in ${P}[0]['verdict']['pending_parts'])")" \
  "1 (['ERR-FEED-503-02'], None, True)"

t_done
