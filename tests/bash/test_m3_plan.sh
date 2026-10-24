#!/usr/bin/env bash
# M3 — assess and plan (FR-CLI-CMD-001/002, FR-ASMT-CUR-001, FR-ASMT-CAND-001/002,
# FR-ASMT-CMP-001, FR-PLAN-TGT-001, FR-PLAN-GEN-001/002, FR-PLAN-CHK-001/002,
# FR-PLAN-STS-001, FR-PLAN-DL-001, FR-SCN-CHK-001; TC-ASMT-001..009, TC-SCN-011..013,
# TC-SCN-101, 102, 106..110, TC-PLAN-*, TC-CLI-013..018). Day T = 2026-10-22 (QP_TODAY).
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
stub apt-cache 'case "$2" in php8.2-fpm|php8.3-fpm) printf "%s:\n  Installed: (none)\n  Candidate: 1:%s-1\n" "$2" "${2:3:3}";; *) printf "%s:\n  Installed: (none)\n  Candidate: (none)\n" "$2";; esac'

B=$T/bin; P=$T/www; mkdir -p "$P"
fake_php "$B/p82/bin/php" 8.2.34 "$T/c82"; mkdir -p "$T/c82"; dpkg_owns "$B/p82/bin/php" php8.2-cli 8.2.34-1 php8.2-fpm
fake_php "$B/p83/bin/php" 8.3.6; dpkg_owns "$B/p83/bin/php" php8.3-cli 8.3.6-0ubuntu0.24.04.13
fake_php "$B/p56/bin/php" 5.6.40
fake_php "$B/p74/bin/php" 7.4.33; dpkg_owns "$B/p74/bin/php" php7.4-cli 7.4.33-1
fake_php "$B/p85/bin/php" 8.5.11
fake_php "$B/p6/bin/php" 6.0.0-dev
fake_node "$T/n20" 20.20.2; fake_node "$T/n24" 24.22.1; dpkg_owns "$T/n24/bin/node" nodejs 24.22.1-1nodesource1; rm -rf "$T/n24/lib"
export QP_PHP_BINS="$B/p82/bin/php $B/p83/bin/php $B/p56/bin/php $B/p74/bin/php $B/p85/bin/php $B/p6/bin/php"
export QP_NODE_BINS="$T/n20/bin/node $T/n24/bin/node"
qp scan --offline --json --only php,node,sites --path "$P" >"$J" 2>/dev/null
rid() { json_get "$J" "[r['runtime_id'] for r in d['result']['runtimes'] if r['bin']=='$1'][0]"; }
R82=$(rid "$B/p82/bin/php"); R83=$(rid "$B/p83/bin/php"); R56=$(rid "$B/p56/bin/php"); R74=$(rid "$B/p74/bin/php")
R85=$(rid "$B/p85/bin/php"); R6=$(rid "$B/p6/bin/php"); N20=$(rid "$T/n20/bin/node"); N24=$(rid "$T/n24/bin/node")
# Two sites on PHP 8.2 and one on 8.3 (site inventory itself: test_m3_scan.sh).
mkdir -p "$T/www/shop/src" "$T/www/blog" "$T/www/wp/wp-includes"
for i in 1 2 3; do echo '<?php' >"$T/www/shop/src/f$i.php"; done; echo '<?php' >"$T/www/blog/index.php"
echo '{}' >"$T/www/shop/composer.json"; echo '<?php $wp_version = "7.0.1";' >"$T/www/wp/wp-includes/version.php"
python3 - "$SD/state/last-scan.json" "$R82" "$R83" "$T/www" <<'PY'
import json, sys
p, r82, r83, www = sys.argv[1:]
d = json.load(open(p))
def site(sid, rid, root, branch):
    return {"site_id": sid, "site_key": sid, "pb_id": "PB-005", "server_names": [sid], "docroot": root,
            "owner_user": "www-data", "binding_kind": "nginx_fastcgi", "binding_ref": "/etc/nginx/sites-enabled/%s:1" % sid,
            "current_branch": branch, "current_bin": None, "runtime_id": rid, "runtime_endpoint": "unix:/run/php/php%s-fpm.sock" % branch,
            "log_sources": [], "hc_urls": ["http://%s/" % sid], "hc_mode": "full"}
d["result"]["sites"] = [site("shop.test", r82, www + "/shop", "8.2"), site("blog.test", r82, www + "/blog", "8.2"),
                        site("wp.test", r83, www + "/wp", "8.3")]
json.dump(d, open(p, "w"))
PY
cp "$SD/state/last-scan.json" "$T/scan.bak"
A=$T/a.json

# --- FR-ASMT-CUR-001: current runtime (TC-ASMT-001, 002, 003) --------------------
qp assess --runtime-id "$R82" --json >"$A" 2>/dev/null; rc=$?
assert_eq "TC-CLI-013: assess exit 0, schema qp.assess/1" "$rc $(json_get "$A" 'd["schema"]')" "0 qp.assess/1"
check "TC-CLI-013: output valid against schema" schema_ok "$A"
assert_eq "TC-ASMT-001 KQ2: SECURITY_ONLY, EOL 2026-12-31, 70 days, latest 8.2.35, min 8.2.35" \
  "$(json_get "$A" '[d["result"]["current"][k] for k in ("lifecycle_status","eol_date","days_to_eol","latest_patch","min_patched")]')" \
  "['SECURITY_ONLY', '2026-12-31', 70, '8.2.35', '8.2.35']"
# C-15: NVD scores CVE-2026-109619 8.1 (document: 9.8) -> 1 critical + 1 high, R 58 (document 60).
assert_eq "TC-ASMT-001 KQ1: CVE counts and KEV (C-15)" "$(json_get "$A" '(d["result"]["current"]["cve_counts"], d["result"]["current"]["kev_count"])')" \
  "({'critical': 1, 'high': 1, 'medium': 0, 'low': 0}, 0)"
assert_eq "TC-ASMT-001 KQ3: risk score/level/components (C-15: R 58)" \
  "$(json_get "$A" '(d["result"]["current"]["risk"]["score"], d["result"]["current"]["risk"]["level"], {k: v for k, v in d["result"]["current"]["risk"]["components"].items() if k.startswith("S_")})')" \
  "(58, 'HIGH', {'S_cvss': 39.2, 'S_cnt': 6.0, 'S_kev': 0.0, 'S_life': 5.0, 'S_eol': 8.0})"
assert_eq "FR-ASMT-CUR-001: advisories[] UNPATCHED with aliases/sources" "$(json_get "$A" 'sorted((a["adv_id"], a["status"]) for a in d["result"]["advisories"])')" \
  "[('CVE-2026-109618', 'UNPATCHED'), ('CVE-2026-109619', 'UNPATCHED')]"
assert_eq "BR-ASMT-003: evaluated_on = T, bundle id and catalog version shown" \
  "$(json_get "$A" '(d["result"]["evaluated_on"], d["result"]["bundle_id"] == d["data"]["bundle_id"], d["catalog_version"] is not None)')" "('2026-10-22', True, True)"
QP_LANG="vi" qp assess --runtime-id "$R74" --json >"$A" 2>/dev/null
assert_eq "TC-ASMT-002: 7.4.33 R 70 CRITICAL (floor), EOL label" \
  "$(json_get "$A" '(d["result"]["current"]["risk"]["R"], d["result"]["current"]["risk"]["level"], d["result"]["current"]["not_assessed_label"])')" \
  "(70, 'CRITICAL', 'Nhánh EOL — nguồn không còn đánh giá CVE mới')"
qp assess --runtime-id php:0123456789ab --json >"$A" 2>/dev/null; rc=$?
assert_eq "TC-ASMT-003: unknown runtime -> ERR-ASMT-404-01, exit 2" "$rc $(json_get "$A" '[e["code"] + ": " + e["message"] for e in d["errors"]]')" \
  "2 ['ERR-ASMT-404-01: Runtime php:0123456789ab not found; run a new scan.']"
cp "$T/scan.bak" "$SD/state/last-scan.json"   # the unknown id made assess scan again
qp assess --json >"$A" 2>/dev/null; rc=$?
assert_eq "TC-CLI-015: assess without --runtime-id/--bin -> ERR-CLI-400-01" "$rc $(json_get "$A" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp assess --bin "$B/p85/bin/php" --json >"$A" 2>/dev/null
assert_eq "TC-CLI-014: assess --bin PATH" "$(json_get "$A" 'd["result"]["runtime_id"]')" "$R85"

# --- FR-ASMT-CAND-001/002, FR-ASMT-CMP-001 (TC-ASMT-005, 008; DOC-API-QP-005 §6) ---
qp assess --runtime-id "$R82" --candidates --json >"$A" 2>/dev/null
assert_eq "TC-ASMT-005 KQ1: candidate types" "$(json_get "$A" '[(c["version"], c["types"]) for c in d["result"]["candidates"] if c["types"]]')" \
  "[('8.2.35', ['SAME_BRANCH_LATEST']), ('8.3.36', ['NEXT_SUPPORTED']), ('8.5.12', ['RECOMMENDED', 'LATEST_STABLE'])]"
assert_eq "TC-ASMT-005 KQ2: each version once" "$(json_get "$A" 'len({c["version"] for c in d["result"]["candidates"]}) == len(d["result"]["candidates"])')" True
assert_eq "TC-ASMT-005 KQ3: 8.6 PRE_RELEASE not selectable, with a reason" \
  "$(json_get "$A" '[(c["version"], c["selectable"], bool(c["not_selectable_reason"])) for c in d["result"]["candidates"] if c["branch"]=="8.6"]')" "[('8.6.0RC4', False, True)]"
assert_eq "TC-ASMT-005 KQ4: installable / install_source (PB-001, apt-cache)" \
  "$(json_get "$A" '[(c["version"], c["installable"], c["install_source"]) for c in d["result"]["candidates"] if c["types"]]')" \
  "[('8.2.35', 'yes', 'package'), ('8.3.36', 'yes', 'package'), ('8.5.12', 'needs_repo', 'repo:ppa:ondrej/php')]"
assert_eq "TC-ASMT-008: comparison R of 8.2.35/8.3.36/8.5.12 = 40/20/0 (§6 table)" \
  "$(json_get "$A" '[(r["version"], r["R"]) for r in d["result"]["comparison"]["rows"][1:4]]')" "[('8.2.35', 40), ('8.3.36', 20), ('8.5.12', 0)]"
assert_eq "TC-ASMT-008 KQ1: delta_R = R - R(current)" "$(json_get "$A" 'all(r["delta_R"] == r["R"] - d["result"]["comparison"]["rows"][0]["R"] for r in d["result"]["comparison"]["rows"])')" True
assert_eq "FR-ASMT-CMP-001: major_gap 8.2 -> 8.5 = 0, rows carry bundle id" "$(json_get "$A" '(d["result"]["comparison"]["rows"][3]["major_gap"], d["result"]["comparison"]["bundle_id"] == d["data"]["bundle_id"])')" "(0, True)"
check "TC-CLI-014: --candidates output valid against schema" schema_ok "$A"

qp assess --runtime-id "$R56" --candidates --json >"$A" 2>/dev/null
assert_eq "TC-SCN-101 KQ2: 5.6 EOL 2018-12-31, -2852 days, CRITICAL" \
  "$(json_get "$A" '[d["result"]["current"][k] for k in ("lifecycle_status","eol_date","days_to_eol","priority")]')" "['EOL', '2018-12-31', -2852, 'CRITICAL']"
assert_eq "TC-SCN-101 KQ3: R >= 70, CRITICAL" "$(json_get "$A" 'd["result"]["current"]["risk"]["R"] >= 70 and d["result"]["current"]["risk"]["level"] == "CRITICAL"')" True
assert_eq "TC-SCN-101 KQ4: no SAME_BRANCH_LATEST, 8.5.12 RECOMMENDED, 8.2.35 NEXT_SUPPORTED not selectable" \
  "$(json_get "$A" '[(c["version"], c["types"], c["selectable"]) for c in d["result"]["candidates"] if c["types"]]')" \
  "[('8.2.35', ['NEXT_SUPPORTED'], False), ('8.5.12', ['RECOMMENDED', 'LATEST_STABLE'], True)]"
qp assess --runtime-id "$R85" --candidates --json >"$A" 2>/dev/null
assert_eq "TC-SCN-106 KQ3: 8.5.12 SAME_BRANCH_LATEST selectable; 8.6 not selectable" \
  "$(json_get "$A" '[(c["version"], c["types"], c["selectable"]) for c in d["result"]["candidates"]]')" \
  "[('8.5.12', ['SAME_BRANCH_LATEST', 'RECOMMENDED', 'LATEST_STABLE'], True), ('8.6.0RC4', [], False)]"
qp assess --runtime-id "$N20" --candidates --json >"$A" 2>/dev/null
assert_eq "TC-SCN-107 KQ2: Node 20 EOL, -175 days, HIGH" "$(json_get "$A" '[d["result"]["current"][k] for k in ("lifecycle_status","days_to_eol","priority")]')" "['EOL', -175, 'HIGH']"
assert_eq "TC-SCN-107 KQ3: 26.12.1 RECOMMENDED; 22.23.4 NEXT_SUPPORTED not selectable, manual with reason" \
  "$(json_get "$A" '[(c["version"], c["types"], c["selectable"], c["manual_with_reason"]) for c in d["result"]["candidates"]]')" \
  "[('22.23.4', ['NEXT_SUPPORTED'], False, True), ('26.12.1', ['RECOMMENDED', 'LATEST_STABLE'], False, False)]"
qp assess --runtime-id "$N24" --candidates --json >"$A" 2>/dev/null
assert_eq "TC-SCN-110 KQ2: Node 24 MAINTENANCE_LTS, 556 days, ok, MEDIUM" \
  "$(json_get "$A" '[d["result"]["current"][k] for k in ("lifecycle_status","days_to_eol","priority")]')" "['MAINTENANCE_LTS', 556, 'MEDIUM']"
assert_eq "TC-SCN-110 KQ3: 26.12.1 CURRENT not selectable before 2026-10-28" \
  "$(json_get "$A" '[(c["lifecycle_status"], c["selectable"]) for c in d["result"]["candidates"] if c["version"]=="26.12.1"]')" "[('CURRENT', False)]"
assert_eq "TC-ASMT-007: on 2026-10-29 Node 26 is ACTIVE_LTS and selectable" \
  "$(QP_TODAY=2026-10-29 qp assess --runtime-id "$N24" --candidates --json 2>/dev/null | python3 -c 'import json,sys; print([(c["lifecycle_status"], c["selectable"]) for c in json.load(sys.stdin)["result"]["candidates"] if c["version"]=="26.12.1"])')" "[('ACTIVE_LTS', True)]"
qp assess --runtime-id "$R6" --candidates --json >"$A" 2>/dev/null
assert_eq "SCN-PHP-005: locked runtime -> no candidates, ERR-SCN-422-01 warning" "$(json_get "$A" '(d["result"]["candidates"], [w["code"] for w in d["warnings"]])')" "([], ['ERR-SCN-422-01'])"

# --- FR-PLAN-TGT-001 (TC-SCN-102 KQ1, TC-SCN-108 KQ1/2) --------------------------
qp plan create --runtime-id "$R56" --target 7.4 --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-SCN-102 KQ1: 5.6 -> 7.4 refused ERR-SCN-409-02" "$rc $(json_get "$J" '[e["code"] + ": " + e["message"] for e in d["errors"]]')" \
  "2 ['ERR-SCN-409-02: Cannot switch a production site to 7.4: the branch is EOL.']"
check "TC-SCN-102 KQ1: no plan created" test -z "$(compgen -G "$SD/plans/PLN-*")"
qp plan create --runtime-id "$R82" --target 8.6 --json >"$J" 2>/dev/null; rc=$?
assert_eq "BR-UPG-004: target PRE_RELEASE refused" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-SCN-409-02"
qp plan create --runtime-id "$N20" --target 24 --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-SCN-108 KQ1: target not RECOMMENDED without reason -> ERR-PLAN-422-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-422-01"
qp plan create --runtime-id "$N20" --target 24 --reason 'short' --json >"$J" 2>/dev/null; rc=$?
assert_eq "ERR-PLAN-422-01: reason < 20 characters" "$rc $(json_get "$J" 'd["errors"][0]["message"]')" "2 Enter a reason of at least 20 characters."
qp plan create --runtime-id "$N20" --target 24 --reason 'Chờ Node.js 26 vào LTS ngày 2026-10-28' --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-SCN-108 KQ2: draft with override_reason" "$rc $(json_get "$J" '(d["result"]["plan"]["status"], d["result"]["plan"]["target"]["override_reason"])')" \
  "0 ('draft', 'Chờ Node.js 26 vào LTS ngày 2026-10-28')"
check "TC-CLI-016: plan create output valid against schema" schema_ok "$J"
assert_eq "TC-SCN-108 KQ3: CHK-NODE-003-01 ... -31 + overlay SCN-NODE-010" \
  "$(json_get "$J" 'sorted({i["chk_id"][:12] for i in d["result"]["plan"]["checklist_items"]})')" "['CHK-NODE-003', 'CHK-NODE-010']"
assert_eq "TC-SCN-108 KQ3: 31 items of SCN-NODE-003" "$(json_get "$J" 'len({i["chk_id"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"].startswith("CHK-NODE-003")})')" 31
check "TC-SCN-108 KQ2: audit has the plan_create record" bash -c "PATH='$STUB:$PATH' bash '$QP' audit list --action plan_create --json | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)[\"result\"][\"total\"] >= 2 else 1)'"

# --- FR-PLAN-GEN-001/002, FR-SCN-CHK-001 (TC-SCN-011, 013; TC-PLAN-*) -------------
qp plan create --runtime-id "$R82" --target 8.5 --json >"$J" 2>/dev/null; rc=$?
P85=$(json_get "$J" 'd["result"]["plan"]["plan_id"]')
assert_eq "TC-PLAN-005: cross_branch draft PLN-YYYYmmdd-HHMMSS-xxxx" "$rc $(json_get "$J" '(d["result"]["plan"]["mode"], d["result"]["plan"]["status"])') $([[ $P85 =~ ^PLN-[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$ ]] && echo id-ok)" \
  "0 ('cross_branch', 'draft') id-ok"
items() { json_get "$J" "$1"; }
assert_eq "TC-SCN-011 KQ1: chk_id pattern, site_id shop.test on per-site items" \
  "$(items '(all(__import__("re").match(r"^CHK-PHP-[0-9]{3}-[0-9]{2}(-[0-9]{2})?$", i["chk_id"]) for i in d["result"]["plan"]["checklist_items"]), sorted({i["site_id"] for i in d["result"]["plan"]["checklist_items"] if i["phase"]=="P5"}))')" \
  "(True, ['blog.test', 'shop.test'])"
assert_eq "TC-SCN-011 KQ2: OVERLAY SCN-PHP-015 before VERSION SCN-PHP-010 in each phase" \
  "$(items 'all(min([n for n, i in enumerate(d["result"]["plan"]["checklist_items"]) if i["phase"]==p and i["scenario_id"]=="SCN-PHP-010"] or [999]) > max([n for n, i in enumerate(d["result"]["plan"]["checklist_items"]) if i["phase"]==p and i["scenario_id"]=="SCN-PHP-015"] or [-1]) for p in ("P1","P2","P3","P4","P5","P6","P7"))')" True
assert_eq "TC-SCN-011 KQ3: \$OLD/\$NEW/\$SITE replaced" \
  "$(items 'sum(1 for i in d["result"]["plan"]["checklist_items"] for v in ("$OLD", "$NEW ", "$SITE") if v in (i["check_mechanism"] + i["action"]))') $(items '[i["action"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"]=="CHK-PHP-010-16"][0]')" \
  "0 Cài \`8.5\` song song và extension tương ứng (§8 A1, BR-SCN-045)"
assert_eq "TC-SCN-013 KQ1: framework=wordpress item SKIPPED on non-WordPress sites" \
  "$(items 'sorted({i["status"] for i in d["result"]["plan"]["checklist_items"] if i["applies_when"]=="framework=wordpress"})')" "[]"
assert_eq "FR-PLAN-GEN-002: site order by PHP file count, canary first" \
  "$(items '(d["result"]["plan"]["site_order"], d["result"]["plan"]["canary_site_id"])')" "(['blog.test', 'shop.test'], 'blog.test')"
assert_eq "FR-PLAN-GEN-001: inputs bundle/catalog/scan fingerprint" \
  "$(items 'sorted(k for k in d["result"]["plan"]["inputs"] if k in ("bundle_id","catalog_version","scan_fingerprint") and d["result"]["plan"]["inputs"][k])')" \
  "['bundle_id', 'catalog_version', 'scan_fingerprint']"
assert_eq "TC-PLAN-024: deadline 2026-12-01, 40 days left" "$(items 'd["result"]["plan"]["deadline"]["date"], d["result"]["plan"]["deadline"]["days_left"]')" "('2026-12-01', 40)"
assert_eq "BR-UPG-006: same-branch patch item before the side-by-side install" \
  "$(items '[i["chk_id"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"] in ("CHK-PHP-010-06","CHK-PHP-010-16")]')" "['CHK-PHP-010-06', 'CHK-PHP-010-16']"
assert_eq "T-CHK-05: P1 checks answered by scan/assess are DONE" \
  "$(items '[i["status"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"] in ("CHK-PHP-010-01","CHK-PHP-010-04")]')" "['DONE', 'DONE']"
assert_eq "BR-SCN-016: preconditions disk/mem/root checked" "$(items '[p["check"] for p in d["result"]["plan"]["preconditions"]]')" "['disk_free_gb', 'mem_available_mb', 'root']"
qp plan create --runtime-id "$R83" --target 8.5 --json >"$J" 2>/dev/null
P83=$(json_get "$J" 'd["result"]["plan"]["plan_id"]')
assert_eq "TC-SCN-013 KQ2: '(khi nâng nhánh)' item expanded into -01..-05" \
  "$(items '[i["chk_id"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"].startswith("CHK-PHP-011-11")]')" \
  "['CHK-PHP-011-11-01', 'CHK-PHP-011-11-02', 'CHK-PHP-011-11-03', 'CHK-PHP-011-11-04', 'CHK-PHP-011-11-05']"
assert_eq "FR-SCN-CHK-001: sub-item copies its template (CHK-PHP-010-13 backup)" \
  "$(items '[(i["template"], i["parent"]) for i in d["result"]["plan"]["checklist_items"] if i["chk_id"]=="CHK-PHP-011-11-01"]')" "[('CHK-PHP-010-13', 'CHK-PHP-011-11')]"
assert_eq "TC-SCN-013: applies_when framework=wordpress holds for the WordPress site" \
  "$(items '[i["status"] for i in d["result"]["plan"]["checklist_items"] if i["applies_when"]=="framework=wordpress"]')" "[]"

# --- T-CHK-*, T-PLN-* on the cross-branch plan ------------------------------------
qp plan run "$P85" CHK-PHP-010-23 --site blog.test --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-SCN-012 KQ1: P5 before P3/P4 -> ERR-SCN-424-01 naming a P3 item" "$rc $(json_get "$J" '[e["code"] for e in d["errors"]]')" "2 ['ERR-SCN-424-01']"
assert_contains "TC-SCN-012 KQ1: message names a P3 item" "$(json_get "$J" 'd["errors"][0]["message"]')" "Cannot run CHK-PHP-010-23 yet: item CHK-PHP-01"
qp plan show "$P85" --json >"$J" 2>/dev/null
assert_eq "TC-SCN-012 KQ2: P5 item stays PENDING with blocked_by" \
  "$(json_get "$J" '[(i["status"], bool(i["blocked_by"])) for i in d["result"]["plan"]["checklist_items"] if i["item_key"]=="CHK-PHP-010-23@blog.test"]')" "[('PENDING', True)]"
qp plan run "$P85" CHK-PHP-010-23 --json >"$J" 2>/dev/null; rc=$?
assert_eq "plan run: ambiguous per-site item needs --site" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp plan approve "$P85" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-PLAN-020 (BR-PLAN-003): approve blocked, compatibility scan missing -> ERR-PLAN-412-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-412-01"
assert_contains "BR-PLAN-003: missing lists the sites and the P1 AUTO baseline" "$(json_get "$J" 'd["errors"][0]["message"]')" "compatibility scan of 2 site(s)"
qp plan item "$P85" CHK-PHP-010-14 --set waive --reason 'too short' --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-14: waive reason < 20 -> ERR-PLAN-422-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-422-01"
qp plan item "$P85" CHK-PHP-010-14 --set 'done' --evidence 'short' --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-09: MANUAL done with evidence < 10 -> ERR-PLAN-422-01" "$rc $(json_get "$J" 'd["errors"][0]["message"]')" "2 Enter a reason of at least 10 characters."
qp plan item "$P85" CHK-PHP-010-14 --set start --json >"$J" 2>/dev/null
assert_eq "T-CHK-10: MANUAL start -> RUNNING" "$(json_get "$J" 'd["result"]["item"]["status"]')" RUNNING
qp plan item "$P85" CHK-PHP-010-14 --set 'done' --evidence 'staging http://stg.test/ HTTP 200 at 10:20' --json >"$J" 2>/dev/null
assert_eq "T-CHK-09: MANUAL done with evidence" "$(json_get "$J" '(d["result"]["item"]["status"], d["result"]["item"]["evidence"])')" "('DONE', 'staging http://stg.test/ HTTP 200 at 10:20')"
check "TC-CLI-017: plan item output valid against schema" schema_ok "$J"
qp plan item "$P85" CHK-PHP-010-14 --set waive --reason 'staging is not needed for this site at all' --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-16: DONE item cannot change -> ERR-PLAN-409-02" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
qp plan item "$P85" CHK-PHP-010-15 --set 'done' --evidence 'checked by hand on the host' --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-09: done on an AUTO item -> ERR-PLAN-409-02 (use plan run)" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
qp plan item "$P85" CHK-PHP-010-19 --site shop.test --set skip --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-15: skip refused while applies_when (composer=true) holds" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
qp plan item "$P85" CHK-PHP-010-19 --site blog.test --json --set skip >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-02: composer=true item already SKIPPED for blog.test (no composer.json)" "$rc $(json_get "$J" 'd["errors"][0]["message"]')" \
  "2 Cannot skip CHK-PHP-010-19@blog.test while the plan is SKIPPED."
qp plan canary "$P85" shop.test --json >"$J" 2>/dev/null
assert_eq "BR-PLAN-004: canary changed on a draft" "$(json_get "$J" '(d["result"]["plan"]["canary_site_id"], d["result"]["plan"]["site_order"], d["result"]["plan"]["status"])')" \
  "('shop.test', ['shop.test', 'blog.test'], 'draft')"

# --- BR-PLAN-006 stale: scan fingerprint, catalog of its scenarios ----------------
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["result"]["scan_fingerprint"]="0"*64; json.dump(d, open(p,"w"))' "$SD/state/last-scan.json"
qp plan show "$P85" --json >"$J" 2>/dev/null
assert_eq "T-PLN-12: SCAN_CHANGED -> stale" "$(json_get "$J" '(d["result"]["plan"]["stale"], d["result"]["plan"]["stale_reasons"])')" "(True, ['SCAN_CHANGED'])"
qp plan approve "$P85" --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-PLN-12: approve of a stale plan -> ERR-PLAN-410-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-410-01"
cp "$T/scan.bak" "$SD/state/last-scan.json"
qp plan show "$P85" --json >"$J" 2>/dev/null
assert_eq "BR-PLAN-006: stays stale until regenerated" "$(json_get "$J" 'd["result"]["plan"]["stale"]')" True
python3 "$QP_ROOT/tools/build-catalog.py" --version 2099.01.01-1 --out "$SD/feeds/catalog" >/dev/null
qp plan show "$P83" --json >"$J" 2>/dev/null
assert_eq "BR-PLAN-006: newer catalog, same scenarios -> not stale" "$(json_get "$J" '(d["catalog_version"], d["result"]["plan"]["stale"])')" "('2099.01.01-1', False)"
python3 - "$SD/feeds/catalog" <<'PY'
import hashlib, json, os, sys
d = sys.argv[1]
p = os.path.join(d, "checklists.json")
doc = json.load(open(p))
for it in doc["items"]:
    if it["chk_id"] == "CHK-PHP-011-01":
        it["done_criteria"] += " (changed)"
json.dump(doc, open(p, "w"), ensure_ascii=False, indent=1)
names = ["scenarios.json", "checklists.json", "playbooks.json", "bc_rules.json", "mitigations.json", "framework_php.tsv", "catalog.json"]
with open(os.path.join(d, "SHA256SUMS"), "w") as f:
    for n in names:
        f.write("%s  %s\n" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n))
PY
qp plan show "$P83" --json >"$J" 2>/dev/null
assert_eq "BR-PLAN-006: catalog changed for its scenario -> CATALOG_CHANGED" "$(json_get "$J" 'd["result"]["plan"]["stale_reasons"]')" "['CATALOG_CHANGED']"
rm -rf "$SD/feeds/catalog"

# --- same_branch plan through its whole life (T-PLN-01/03/07/09, T-CHK-03/05/14) --
qp plan create --runtime-id "$R82" --target 8.2 --json >"$J" 2>/dev/null
PS=$(json_get "$J" 'd["result"]["plan"]["plan_id"]')
assert_eq "BR-PLAN-002 / T-PLN-04: older draft of the runtime superseded" "$(qp plan show "$P85" --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["plan"]["status"])')" cancelled
assert_eq "FR-PLAN-GEN-001: same_branch plan to 8.2.35, upgrade steps SKIPPED" \
  "$(json_get "$J" '(d["result"]["plan"]["mode"], d["result"]["plan"]["target"]["patch_version"], [i["status"] for i in d["result"]["plan"]["checklist_items"] if i["chk_id"]=="CHK-PHP-010-16"])')" \
  "('same_branch', '8.2.35', ['SKIPPED'])"
qp plan approve "$PS" --json >"$J" 2>/dev/null; rc=$?
assert_eq "BR-PLAN-003: P1 AUTO baseline per site still PENDING -> ERR-PLAN-412-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-412-01"
for s in shop.test blog.test; do
  qp plan item "$PS" CHK-PHP-010-05 --site "$s" --set waive --reason 'baseline taken by hand before the patch window' >/dev/null 2>&1
done
qp plan approve "$PS" --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-PLN-03: approved, approved_by set" "$rc $(json_get "$J" '(d["result"]["plan"]["status"], d["result"]["plan"]["approved_by"] is not None)')" "0 ('approved', True)"
assert_eq "TC-PLAN-025: approved plan in scan plan_deadlines" \
  "$(qp scan --offline --only php --json --path "$P" 2>/dev/null | python3 -c 'import json,sys; print([x["plan_status"] for x in json.load(sys.stdin)["result"]["plan_deadlines"] if x["runtime_id"]=="'"$R82"'"])')" "['approved']"
cp "$T/scan.bak" "$SD/state/last-scan.json"   # the scan above rewrote it without the test sites
qp plan run "$PS" CHK-PHP-010-06 --json </dev/null >"$J" 2>/dev/null; rc=$?
assert_eq "FR-CLI-SAFE-001: write item without --yes (no TTY) -> ERR-CLI-428-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-428-01"
: >"$CALLS"
qp plan run "$PS" CHK-PHP-010-06 --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-03 dry-run: preview, item unchanged, no apt-get" \
  "$rc $(json_get "$J" '(d["result"]["run"]["child_schema"], d["result"]["item"]["status"], d["result"]["preview"] is not None)') $(grep -c '^apt-get install' "$CALLS")" \
  "0 ('qp.fix/1', 'PENDING', True) 0"
apt_upgrades "$B/p82/bin/php" 8.2.35
qp plan run "$PS" CHK-PHP-010-06 --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-05/06 / T-PLN-07: fix ran (exit 1 from other runtimes), item DONE, plan in_progress" \
  "$rc $(json_get "$J" '(d["result"]["item"]["status"], d["result"]["run"]["child_exit_code"])') $(qp plan show "$PS" --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["plan"]["status"])')" \
  "0 ('DONE', 1) in_progress"
check "TC-CLI-018: plan run output valid against schema" schema_ok "$J"
cp "$T/scan.bak" "$SD/state/last-scan.json"
qp plan create --runtime-id "$R82" --target 8.5 --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-PLN-02: runtime has an in_progress plan -> ERR-PLAN-409-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-01"
qp plan complete "$PS" --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-PLN-13: complete with open items -> ERR-PLAN-409-02" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
for k in $(qp plan show "$PS" --json 2>/dev/null | python3 -c 'import json,sys; print(" ".join(i["item_key"] for i in json.load(sys.stdin)["result"]["plan"]["checklist_items"] if i["status"] in ("PENDING","FAILED")))'); do
  qp plan item "$PS" "$k" --set waive --reason 'covered by the patch run of this test plan' >/dev/null 2>&1
done
qp plan show "$PS" --json >"$J" 2>/dev/null
assert_eq "T-PLN-09: last item closed -> completed" "$(json_get "$J" '(d["result"]["plan"]["status"], d["result"]["plan"]["counts"]["PENDING"])')" "('completed', 0)"
qp plan cancel "$PS" --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-PLN-13: cancel a completed plan -> ERR-PLAN-409-02" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-409-02"
assert_eq "events.jsonl records the life of the plan" "$(python3 -c 'import json,sys; print(sorted({json.loads(l)["event"] for l in open(sys.argv[1])}))' "$SD/plans/$PS/events.jsonl")" \
  "['approved', 'completed', 'created', 'in_progress', 'item', 'run']"
assert_eq "storage: plan.json, items.json, events.jsonl, no temp file" "$(ls "$SD/plans/$PS" | tr '\n' ' ')" "events.jsonl items.json plan.json "

# --- list / show / cancel / unknown ids ------------------------------------------
qp plan list --json >"$J" 2>/dev/null
assert_eq "TC-CLI-016: plan list" "$(json_get "$J" 'sorted(p["status"] for p in d["result"]["plans"])')" "['cancelled', 'completed', 'draft', 'draft']"
check "TC-CLI-016: plan list output valid against schema" schema_ok "$J"
PN=$(json_get "$J" '[p["plan_id"] for p in d["result"]["plans"] if p["runtime_id"]=="'"$N20"'"][0]')
qp plan cancel "$PN" --json >"$J" 2>/dev/null
assert_eq "T-PLN-05: cancel a draft" "$(json_get "$J" 'd["result"]["plan"]["status"]')" cancelled
qp plan show PLN-20990101-000000-abcd --json >"$J" 2>/dev/null; rc=$?
assert_eq "ERR-PLAN-404-01: unknown plan" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-404-01"
qp plan item "$P83" CHK-PHP-999-01 --set 'done' --evidence 'whatever evidence text' --json >"$J" 2>/dev/null; rc=$?
assert_eq "T-CHK-16: unknown item -> ERR-PLAN-404-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-404-01"
qp plan waive "$P83" --site wp.test --hits H-0123456789ab --reason 'tests folder is not deployed to prod' --json >"$J" 2>/dev/null; rc=$?
assert_eq "plan waive: unknown hit (no compatibility result before M4) -> ERR-PLAN-404-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-PLAN-404-01"
qp plan frobnicate --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-CLI-018: unknown subcommand -> ERR-CLI-400-01" "$rc $(json_get "$J" 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"

t_done
