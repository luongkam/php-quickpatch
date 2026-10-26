#!/usr/bin/env bash
# M2 — feeds commands and the bundle seen by scan/fix (FR-FEED-CMD-001..006,
# FR-FEED-SNAP-001/003, FR-FEED-AGE-001, FR-CLI-COMP-002, FR-ASMT-RISK-001;
# TC-FEED-001..004, 029..031, 035..041, 045..050, TC-CLI-010..012, TC-ASMT-001/002).
# Sources are the local fake server (tests/fakesrv.py); no real network.
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'feeds_cleanup; rm -rf "$T"' EXIT
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; dpkg_stubs; curl_stub
SD=/var/lib/php-quickpatch; FD=$SD/feeds
feeds_fixture
J=$T/out.json
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
NOPY=$(path_without "$T/nopy" python3 python3.13 python3.12 python3.11)
qpn() { PATH="$STUB:$NOPY" bash "$QP" "$@"; }       # host without Python

# --- TC-FEED-001..004: feeds update / sync ------------------------------------
qp feeds update --json >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-FEED-001 update: exit 1 (SRC-008 secondary failed, rest OK)" "$rc" 1
assert_eq "TC-FEED-001 schema qp.feeds.update/1" "$(json_get "$J" 'd["schema"]')" qp.feeds.update/1
check "TC-FEED-001 output valid against schema" schema_ok "$J"
assert_eq "TC-FEED-002 within TTL: every enabled source not_due" \
  "$(json_get "$J" 'sorted({s["outcome"] for s in d["result"]["sources"] if s["src_id"] not in ("SRC-008","SRC-013")})')" "['not_due']"
assert_eq "TC-FEED-001 data.bundle_id = new current" "$(json_get "$J" 'd["data"]["bundle_id"]')" "$(basename "$(readlink "$FD/current")")"
qp sync --force --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-003 sync alias = feeds update" "$(json_get "$J" 'd["schema"]')" qp.feeds.update/1
assert_eq "TC-FEED-003 --force refetches (304 with ETag)" "$(json_get "$J" '[s["outcome"] for s in d["result"]["sources"] if s["src_id"]=="SRC-010"]')" "['not_modified']"
qp feeds update --source SRC-999 --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-004 bad --source: exit 2" "$rc" 2
assert_eq "TC-FEED-004 bad --source: ERR-CLI-400-01" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-CLI-400-01
qp feeds update --accept-shrink >/dev/null 2>&1; rc=$?
assert_eq "TC-FEED-004 --accept-shrink needs --force" "$rc" 2
feeds_control '{"SRC-009": {"status": 503}}'
qp feeds update --force --source SRC-009 --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-001 primary down: exit 1" "$rc" 1
assert_eq "TC-FEED-001 primary down: ERR-FEED-503-01 in errors[]" "$(json_get "$J" '[e["code"] for e in d["errors"]]')" "['ERR-FEED-503-01']"
feeds_control '{}'
check "TC-FEED-104 last-sync.log has fetched/not_modified/not_due/failed" \
  bash -c "grep -q ' fetched ' $FD/state/last-sync.log && grep -q ' not_modified ' $FD/state/last-sync.log && grep -q ' not_due' $FD/state/last-sync.log && grep -q ' failed ' $FD/state/last-sync.log"
# feeds/.lock held -> ERR-FEED-423-01 after 30 s is too slow for a test: hold it 35 s in background? no; the
# 30 s wait is covered by the Python suite (FeedsLock wait). Here: the lock file is separate from STATE_DIR/.lock.
flock -x "$SD/.lock" true
check "BR-FEED-015 feeds update does not use STATE_DIR/.lock" bash -c "flock -x $SD/.lock bash $QP feeds update --quiet >/dev/null 2>&1; [ \$? -le 1 ]"

# --- TC-FEED-048..050: feeds status ---------------------------------------------
qp feeds status --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-048 status: FRESH -> exit 0" "$rc" 0
check "TC-FEED-048 status valid against qp.feeds.status/1" schema_ok "$J"
assert_eq "TC-FEED-048 freshness FRESH" "$(json_get "$J" 'd["result"]["freshness"]')" FRESH
assert_eq "TC-FEED-048 SRC-013 DISABLED" "$(json_get "$J" '[s["status"] for s in d["result"]["sources"] if s["src_id"]=="SRC-013"]')" "['DISABLED']"
qp feeds status >"$T/st.txt" 2>&1
check "TC-FEED-048 text table" grep -q '^SRC-004  NVD CVE API 2.0' "$T/st.txt"
check "TC-FEED-048 text freshness line" grep -q '^Freshness: FRESH' "$T/st.txt"

# --- TC-FEED-049: feeds verify ------------------------------------------------------
qp feeds verify --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-049 verify OK: exit 0" "$rc" 0
check "TC-FEED-049 verify output valid" schema_ok "$J"
cur=$(readlink -f "$FD/current"); echo tampered >>"$cur/kev.tsv"
qp feeds verify --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-049 tampered bundle: exit 2" "$rc" 2
assert_eq "TC-FEED-049 tampered: ERR-FEED-422-02" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-FEED-422-02
check "TC-FEED-049 rebuilt from stored data" test "$(readlink -f "$FD/current")" != "$cur"

# --- TC-FEED-038..041: export / import ------------------------------------------------
qp feeds export --out "$T/snap.tar.gz" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-038 export exit 0" "$rc" 0
check "TC-FEED-038 export output valid" schema_ok "$J"
SHA=$(json_get "$J" 'd["result"]["sha256"]')
assert_eq "TC-FEED-038 printed sha256 = file" "$SHA" "$(sha256sum "$T/snap.tar.gz" | cut -c1-64)"
qp snapshot export --out "$T/snap.tar.gz" >/dev/null 2>&1; rc=$?
assert_eq "TC-FEED-038 never overwrites --out (alias snapshot export)" "$rc" 2
check "BR-FEED-056 no host data in the snapshot" bash -c "! tar -tzf $T/snap.tar.gz | grep -qE '^(cache|raw|parts)/|\\.lock$'"
before=$(readlink "$FD/current")
qp feeds import "$T/snap.tar.gz" --sha256 "$SHA" --json </dev/null >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-039 import without --yes and no TTY: exit 2" "$rc" 2
assert_eq "TC-FEED-039 ERR-CLI-428-01" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-CLI-428-01
qp feeds import "$T/snap.tar.gz" --sha256 "$(printf 'f%.0s' {1..64})" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-040 wrong --sha256: exit 2" "$rc" 2
assert_eq "TC-FEED-040 wrong --sha256: ERR-FEED-422-02" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-FEED-422-02
assert_eq "TC-FEED-040 current unchanged" "$(readlink "$FD/current")" "$before"
qp feeds import "$T/snap.tar.gz" --sha256 "$SHA" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-041 same/older snapshot: ERR-FEED-409-02" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-FEED-409-02
fp_before=$(fingerprint "$FD/bundles" "$FD/snapshots")
qp feeds import "$T/snap.tar.gz" --sha256 "$SHA" --force --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-039 --dry-run: exit 0" "$rc" 0
assert_eq "TC-FEED-039 --dry-run: dry_run true" "$(json_get "$J" 'd["dry_run"]')" True
assert_eq "TC-FEED-039 --dry-run: 0 changes" "$(fingerprint "$FD/bundles" "$FD/snapshots")" "$fp_before"
check "TC-FEED-039 --dry-run: work dir removed" bash -c "! ls -d $SD/work/dryrun-* 2>/dev/null"
qp feeds import "$T/snap.tar.gz" --sha256 "$SHA" --force --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-039 import --force: exit 0" "$rc" 0
check "TC-FEED-039 import output valid" schema_ok "$J"
assert_eq "TC-FEED-039 current -> imported bundle" "$(basename "$(readlink "$FD/current")")" "$(json_get "$J" 'd["result"]["bundle_id"]')"
# 3 audited attempts: wrong --sha256, older snapshot, --force (the no-TTY refusal changes nothing, no record).
assert_eq "BR-FEED-055 audit INTENT+RESULT for every import attempt" \
  "$(python3 -c 'import json,glob; print([(r["record_type"], r["result"]) for f in sorted(glob.glob("/var/lib/php-quickpatch/audit/*.jsonl")) for r in map(json.loads, open(f)) if r["action"]=="feeds_import"])')" \
  "[('INTENT', None), ('RESULT', 'failed'), ('INTENT', None), ('RESULT', 'failed'), ('INTENT', None), ('RESULT', 'ok')]"
check "BR-FEED-055 audit_anchor in the envelope" test "$(json_get "$J" 'd["audit_anchor"]["seq"] > 0')" = True
check "BR-FEED-055 audit chain verifies" qp audit verify

# --- TC-FEED-045..047: schedule (no file written in --dry-run) -----------------------------
qp feeds schedule install --interval-hours 5 --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-045 interval not in {1,2,3,4,6,8,12,24}: exit 2" "$rc" 2
fp_before=$(fingerprint /etc/cron.d /etc/systemd/system 2>/dev/null)
qp feeds schedule install --interval-hours 6 --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-045 install --dry-run: exit 0" "$rc" 0
check "TC-FEED-045 schedule output valid" schema_ok "$J"
check "TC-FEED-045 dry-run shows the 6 h job" bash -c "grep -q '\\*/6 \\* \\* \\*\\|00/6:' $J"
assert_eq "TC-FEED-045 dry-run wrote nothing" "$(fingerprint /etc/cron.d /etc/systemd/system 2>/dev/null)" "$fp_before"
qp feeds schedule install </dev/null >/dev/null 2>&1; rc=$?
assert_eq "TC-FEED-046 install without --yes, no TTY: exit 2" "$rc" 2
qp feeds schedule show --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-047 show: exit 0" "$rc" 0

# --- TC-CLI-010..012 / FR-CLI-COMP-002: scan reads the bundle, also without Python -----------
fake_php "$T/php84/bin/php" 8.4.26
fake_php "$T/php82/bin/php" 8.2.34
fake_node "$T/node22" 22.23.3
fake_node "$T/node20" 20.20.2
W=$T/w/blog; mkdir -p "$W/wp-includes"; printf '<?php\n$wp_version = '"'"'7.0.1'"'"';\n' >"$W/wp-includes/version.php"
export QP_PHP_BINS="$T/php84/bin/php $T/php82/bin/php" QP_NODE_BINS="$T/node22/bin/node $T/node20/bin/node"
qpn scan --offline --json --only php,node,wp --path "$T/w" >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-010 scan without Python: exit 1 (issues)" "$rc" 1
check "TC-CLI-010 scan output valid" schema_ok "$J"
rt() { json_get "$J" "[(r['state'], r['min_patched'], r['lifecycle_status'], r['risk']['R'], r['risk']['level']) for r in d['result']['runtimes'] if r['version']=='$1'][0]"; }
assert_eq "TC-CLI-010 PHP 8.4.26 vulnerable, min 8.4.27" "$(rt 8.4.26 | cut -d, -f1-3)" "('vulnerable', '8.4.27', 'ACTIVE'"
assert_eq "TC-CLI-010 PHP 8.2.34 min 8.2.35" "$(rt 8.2.34 | cut -d, -f1-2)" "('vulnerable', '8.2.35'"
assert_eq "TC-CLI-011 Node 22.23.3 below 22.23.4 (temporary advisory)" "$(rt 22.23.3 | cut -d, -f1-2)" "('vulnerable', '22.23.4'"
assert_eq "TC-CLI-012 Node 20 EOL" "$(rt 20.20.2 | cut -d, -f1)" "('eol'"
assert_eq "TC-CLI-010 driver_ids from min_patched.tsv" "$(json_get "$J" "[r['driver_ids'] for r in d['result']['runtimes'] if r['version']=='8.4.26'][0]")" "['CVE-2026-109618', 'CVE-2026-109619']"
assert_eq "TC-CLI-012 WordPress 7.0.1 vulnerable, min 7.0.7, KEV" "$(json_get "$J" '[(w["status"], w["min_patched"], w["in_kev"], w["risk"]["R"]) for w in d["result"]["wordpress_findings"]][0]')" "('vulnerable', '7.0.7', True, 71)"
check "FR-FEED-AGE-001 data line under Environment" grep -q '\[i\] CVE/lifecycle data: bundle b-' "$T/err.txt"
assert_eq "FR-FEED-AGE-001 envelope data.freshness" "$(json_get "$J" 'd["data"]["freshness"]')" FRESH
assert_eq "FEAT-033 ranking sorted by R" "$(json_get "$J" '[r["R"] for r in d["result"]["ranking"]] == sorted([r["R"] for r in d["result"]["ranking"]], reverse=True)')" True
# BR-FEED-040: Bash and Python give the same R for the same inputs.
today=$(date -u +%F)
for pv in php:8.4.26 php:8.2.34 node:22.23.3 node:20.20.2 php:8.3.6; do
  p=${pv%%:*} v=${pv#*:}
  py=$(python3 -I "$QPF" --script "$QP" risk --product "$p" --version "$v" --today "$today" --json | python3 -c 'import json,sys; d=json.load(sys.stdin)["result"]; print(d["risk"]["R"], d["risk"]["level"], d["lifecycle_status"], d["priority"])')
  sh=$(bash -c '. "$1"; STATE_DIR=/var/lib/php-quickpatch; feeds_dir_ready; QP_FEEDS_BUNDLE=$(readlink -f "$FEEDS_DIR/current"); TODAY=$(date -u +%F); iso_epoch "$TODAY"; TODAY_DAY=$((REPLY/86400)); assess "$2" "$3"; echo "$RISK_R $RISK_LEVEL $A_LC $A_PRIO"' _ "$QP" "$p" "$v")
  assert_eq "BR-FEED-040 Bash = Python for $p $v ($py)" "$sh" "$py"
done
# §8.2.1 RT-1 / RT-2 with the Bash arithmetic (no awk printf, no float).
rt1=$(bash -c '. "$1"; risk_score ACTIVE 500 0 0 1 0 0 50; echo "$RISK_R $RISK_LEVEL"; risk_score SECURITY_ONLY 120 0 0 5 0 0 60; echo "$RISK_R $RISK_LEVEL"' _ "$QP" | tr '\n' ' ')
assert_eq "TC-ASMT-002 RT-1 = 21, RT-2 = 37 in Bash" "$rt1" "21 MEDIUM 37 MEDIUM "
ex=$(bash -c '. "$1"; for c in "ACTIVE 1166 0 0 0 0 0 0" "ACTIVE 801 2 0 0 0 0 98" "SECURITY_ONLY 70 2 0 0 0 0 98" "SECURITY_ONLY 70 0 0 0 0 0 0" "SECURITY_ONLY 435 9 15 21 3 0 98" "SECURITY_ONLY 435 0 0 1 0 0 69" "EOL -1424 2 0 2 0 0 98" "MAINTENANCE_LTS 190 0 1 0 0 0 75" "MAINTENANCE_LTS 190 0 3 3 1 0 80" "EOL -175 0 0 0 0 0 0" "SECURITY_ONLY - 1 1 1 0 3 98" "SECURITY_ONLY - 0 1 0 0 1 81"; do risk_score $c; printf "%s " "$RISK_R"; done' _ "$QP")
assert_eq "TC-ASMT-001 §8.5 examples 1-11 in Bash" "$ex" "0 47 60 40 64 33 70 40 47 40 71 70 "

# --- TC-FEED-029..031: freshness levels from the bundle's source ages ----------------------------
age_bundle() { # age_bundle HOURS: rewrite last_ok_at in sources.tsv of a copy of current
  local cur new old; cur=$(readlink -f "$FD/current"); new="$FD/bundles/b-20000101T000000Z-0000000$1"
  rm -rf "$new"; cp -a "$cur" "$new"
  old=$(date -u -d "-$1 hours" +%Y-%m-%dT%H:%M:%SZ)
  awk -F'\t' -v OFS='\t' -v t="$old" 'NR > 1 && $5 != "" { $5 = t } { print }' "$cur/sources.tsv" >"$new/sources.tsv"
  ln -sfn "bundles/${new##*/}" "$FD/current"
}
age_bundle 200
qpn scan --offline --json --only php --path "$T/w" >"$J" 2>"$T/err.txt"
assert_eq "TC-FEED-030 200 h -> STALE" "$(json_get "$J" 'd["data"]["freshness"]')" STALE
assert_eq "TC-FEED-030 STALE warning ERR-FEED-412-01" "$(json_get "$J" '[w["code"] for w in d["warnings"] if w["code"]=="ERR-FEED-412-01"]')" "['ERR-FEED-412-01']"
check "TC-FEED-030 [WARN] data line" grep -q '\[WARN\] CVE/lifecycle data: bundle .* 200 h old' "$T/err.txt"
age_bundle 2200
qpn scan --offline --json --only php --path "$T/w" >"$J" 2>/dev/null
assert_eq "TC-FEED-031 2200 h -> EXPIRED + ERR-SCN-503-01" "$(json_get "$J" 'd["data"]["freshness"], [w["code"] for w in d["warnings"] if w["code"]=="ERR-SCN-503-01"]')" "('EXPIRED', ['ERR-SCN-503-01'])"
# BR-FEED-001 (a): not --offline and a source older than its TTL -> feeds update first (fake server).
age_bundle 10
qp scan --json --only php --path "$T/w" >"$J" 2>/dev/null
assert_eq "TC-FEED-029 stale source refreshed before the scan" "$(json_get "$J" 'd["data"]["freshness"]')" FRESH
check "TC-FEED-029 new bundle built" test "$(basename "$(readlink "$FD/current")")" != b-20000101T000000Z-000000010

# --- TC-FEED-035..037: packaged snapshot, no Python (FR-FEED-SNAP-001, BR-FEED-053) ------------
TOOL=$T/tool; mkdir -p "$TOOL/share/php-quickpatch"
for f in "$QP_ROOT"/share/php-quickpatch/*; do ln -s "$f" "$TOOL/share/php-quickpatch/"; done
cp "$T/snap.tar.gz" "$TOOL/share/php-quickpatch/feeds-snapshot.tar.gz"
sed "s/^QP_SNAPSHOT_SHA256=\"\"/QP_SNAPSHOT_SHA256=\"$SHA\"/" "$QP" >"$TOOL/php-quickpatch.sh"
rm -rf "$FD"
PATH="$STUB:$NOPY" bash "$TOOL/php-quickpatch.sh" scan --offline --json --only php --path "$T/w" >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-FEED-035 first run installs the packaged snapshot (no Python)" "$(basename "$(readlink "$FD/current")")" "$(tar -xzOf "$T/snap.tar.gz" manifest.json | sed -n 's/^ "bundle_id": "\(.*\)",/\1/p')"
assert_eq "TC-FEED-035 scan uses it: exit 1" "$rc" 1
check "TC-FEED-035 base.json records the snapshot" grep -q '"type": "snapshot"' "$FD/state/base.json"
rm -rf "$FD"
sed "s/^QP_SNAPSHOT_SHA256=\"\"/QP_SNAPSHOT_SHA256=\"$(printf '0%.0s' {1..64})\"/" "$QP" >"$TOOL/php-quickpatch.sh"
PATH="$STUB:$NOPY" bash "$TOOL/php-quickpatch.sh" scan --offline --json --only php --path "$T/w" >"$J" 2>/dev/null; rc=$?
assert_eq "TC-FEED-036 wrong pin: ERR-FEED-422-02 warning" "$(json_get "$J" '[w["code"] for w in d["warnings"]][:1]')" "['ERR-FEED-422-02']"
check "TC-FEED-036 wrong pin: no bundle installed" test ! -e "$FD/current"
assert_eq "TC-FEED-037 no data at all: exit 2 + ERR-FEED-503-01" "$rc $(json_get "$J" '[e["code"] for e in d["errors"] if e["code"].startswith("ERR-FEED")]')" "2 ['ERR-FEED-503-01']"
assert_eq "TC-FEED-037 runtimes unknown" "$(json_get "$J" 'sorted({r["state"] for r in d["result"]["runtimes"]})')" "['unknown']"

t_done
