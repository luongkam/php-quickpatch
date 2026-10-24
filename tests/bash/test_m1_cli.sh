#!/usr/bin/env bash
# M1 — CLI contract: --json envelope, schema, compatibility with v0.1, locks,
# environment checks, languages (FR-CLI-JSON-001/002, FR-CLI-COMP-001,
# FR-CLI-ENV-001, FR-CLI-SAFE-001; TC-CLI-001..009, 014, 028, 029, 101, 102).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'rm -rf "$T"' EXIT
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; curl_stub
SD=/var/lib/php-quickpatch
P=$T/proj; mkdir -p "$P/site"
echo '{}' >"$P/site/composer.json"
fake_php "$T/php82/bin/php" 8.2.34 "$T/php82/conf.d"; mkdir -p "$T/php82/conf.d"
fake_node "$T/node24" 24.21.0
export QP_PHP_BINS="$T/php82/bin/php" QP_NODE_BINS="$T/node24/bin/node"
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }

# --- TC-CLI-001: exactly one JSON document on stdout -------------------------
qp scan --json --offline --path "$P" >"$T/out.json" 2>"$T/err.txt"; rc=$?
check "TC-CLI-001 stdout is one valid JSON document" python3 -c 'import json,sys; json.loads(open(sys.argv[1]).read())' "$T/out.json"
assert_eq "TC-CLI-001 schema = qp.scan/1" "$(json_get "$T/out.json" 'd["schema"]')" "qp.scan/1"
assert_eq "TC-CLI-001 every envelope field present" \
  "$(json_get "$T/out.json" 'all(k in d for k in ("schema","schema_version","tool","generated_at","host","command","dry_run","exit_code","data","catalog_version","result","issues","errors","warnings"))')" True
assert_eq "TC-CLI-001 exit_code = process exit code" "$(json_get "$T/out.json" 'd["exit_code"]')" "$rc"
check "TC-CLI-001 human text only on stderr" grep -q '\[VULN\]' "$T/err.txt"
check "TC-CLI-001 no human text on stdout" test "$(grep -c '\[OK\]\|\[WARN\]\|\[VULN\]\|\[i\]' "$T/out.json")" -eq 0
check "TC-CLI-001 log written" grep -q 'PHP runtimes' "$SD/php-quickpatch.log"
check "TC-CLI-004 scan output valid against qp.scan.v1.schema.json" schema_ok "$T/out.json"
assert_eq "scan: runtime_id format" "$(json_get "$T/out.json" '[r["runtime_id"] for r in d["result"]["runtimes"] if r["kind"]=="php"][0]')" \
  "php:$(printf '%s' "$T/php82/bin/php" | sha1sum | cut -c1-12)"

# --- TC-CLI-002: bad argument after --json -----------------------------------
qp scan --json --bogus >"$T/out.json" 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-002 exit 2" "$rc" 2
assert_eq "TC-CLI-002 errors[0].code" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-400-01
assert_eq "TC-CLI-002 exit_code field" "$(json_get "$T/out.json" 'd["exit_code"]')" 2
check "TC-CLI-002 envelope valid" schema_ok "$T/out.json"

# --- TC-CLI-003: escaping and secret masking without jq ----------------------
NOJQ=$(path_without "$T/nojq" jq)
check "TC-CLI-003 precondition: jq not on PATH" env PATH="$NOJQ" bash -c '! command -v jq'
W=$T/$'we"ird\\na\tme'; mkdir -p "$W"; echo '{}' >"$W/composer.lock"
QP_NVD_API_KEY=QPTESTKEY0001 PATH="$STUB:$NOJQ" bash "$QP" scan --json --offline --only composer --path "$W" --path "$T/token=QPTESTKEY0001" >"$T/out.json" 2>/dev/null
check "TC-CLI-003 parses with python3 -m json.tool" python3 -m json.tool "$T/out.json"
assert_eq "TC-CLI-003 path keeps its characters" "$(json_get "$T/out.json" '[p["dir"] for p in d["result"]["projects"]][0]')" "$W"
assert_eq "TC-CLI-003 secret appears 0 times on stdout" "$(grep -c QPTESTKEY0001 "$T/out.json")" 0
check "TC-CLI-003 argv masked with ***" grep -q 'token=\*\*\*' "$T/out.json"

# --- TC-CLI-004/005/006: schema publication ----------------------------------
for c in scan fix assess plan migrate feeds.status audit report; do
  f="$QP_ROOT/share/php-quickpatch/schemas/qp.$c.v1.schema.json"
  assert_eq "TC-CLI-004 $c schema is JSON Schema 2020-12" "$(json_get "$f" 'd["$schema"]')" "https://json-schema.org/draft/2020-12/schema"
done
assert_eq "TC-CLI-004 'schema scan' prints the file" "$(qp schema scan | sha256sum)" "$(sha256sum <"$QP_ROOT/share/php-quickpatch/schemas/qp.scan.v1.schema.json")"
qp schema foo >/dev/null 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-005 unknown command: exit 2" "$rc" 2
check "TC-CLI-005 unknown command: ERR-CLI-400-01 wording" grep -q 'Unknown argument: schema foo' "$T/err.txt"
qp schema foo --json >"$T/out.json" 2>/dev/null
assert_eq "TC-CLI-005 --json errors[0].code" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-400-01
qp scan --json --json-schema 1 --offline --only webshell --path "$P" >"$T/out.json" 2>/dev/null
assert_eq "TC-CLI-006 --json-schema 1 keeps qp.scan/1" "$(json_get "$T/out.json" 'd["schema"]')" qp.scan/1
qp scan --json --json-schema 2 >"$T/out.json" 2>/dev/null; rc=$?
assert_eq "TC-CLI-006 unsupported major -> exit 2" "$rc" 2
assert_eq "TC-CLI-006 unsupported major -> ERR-CLI-400-01" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-400-01

# --- TC-CLI-007 + NFR-CMP-001: v0.1 syntax and text output ------------------
NOPY=$(path_without "$T/nopy" python3 python3.13 python3.12 python3.11)
PATH="$STUB:$NOPY" bash "$QP" fix --only php,node,composer,npm,wp,docker,webshell --no-memlimit --path "$P" >"$T/v2.txt" 2>&1; rc=$?
check "TC-CLI-007 runs without python3" test "$rc" -le 1
for tag in '\[OK\]\|\[i\]' '\[VULN\]' '\[WARN\]' '== Summary ==' 'rollback: '; do
  check "TC-CLI-007 text keeps '$tag'" grep -q "$tag" "$T/v2.txt"
done
check "TC-CLI-007 STATE_DIR /var/lib/php-quickpatch" grep -q "log=$SD/php-quickpatch.log" "$T/v2.txt"
check "TC-CLI-007 manifest keeps the v0.1 TAB format" bash -c "grep -qP '^created\t/' $SD/backups/*/manifest"
# Same fixture, scan mode: every v0.1.1 output line is still printed by v2 (BR-CLI-002: only new lines may be added).
git -C "$QP_ROOT" show 5919d7e:php-quickpatch.sh >"$T/qp-011.sh"
rm -f "$T/php82/conf.d/"*; norm() { sed -E "s/[0-9]{8}-[0-9]{6}/RUN/g; s/^php-quickpatch [^ ]+/php-quickpatch X/; s#rollback: [^ ]+ #rollback: SCRIPT #; s#run '[^']+ fix'#run 'SCRIPT fix'#"; }
PATH="$STUB:$PATH" bash "$T/qp-011.sh" scan --offline --path "$P" 2>&1 | norm >"$T/a.txt"
PATH="$STUB:$PATH" bash "$QP" scan --offline --path "$P" 2>&1 | norm >"$T/b.txt"
missing=$(grep -vxF -f "$T/b.txt" "$T/a.txt" | grep -v '^php-quickpatch X')
assert_eq "NFR-CMP-001 scan: no v0.1.1 line missing or changed" "$missing" ""
a_rc=$(PATH="$STUB:$PATH" bash "$T/qp-011.sh" scan --offline --path "$P" >/dev/null 2>&1; echo $?)
b_rc=$(PATH="$STUB:$PATH" bash "$QP" scan --offline --path "$P" >/dev/null 2>&1; echo $?)
assert_eq "NFR-CMP-001 scan: same exit code as v0.1.1" "$b_rc" "$a_rc"

# --- TC-CLI-008/009: unknown argument, locks ----------------------------------
qp scan --foo >"$T/o.txt" 2>&1; rc=$?
assert_eq "TC-CLI-008 unknown argument exit 2" "$rc" 2
check "TC-CLI-008 v0.1 wording + usage" grep -q '^Unknown argument: --foo' "$T/o.txt"
check "TC-CLI-008 usage printed" grep -q '^Usage:' "$T/o.txt"
hold() { flock "$1" "$SD/.lock" sleep 5 & sleep 0.5; }   # hold the state lock 5 s
hold -x; qp fix --path "$P" --only webshell >"$T/o.txt" 2>&1; rc=$?; wait
assert_eq "TC-CLI-008 fix while fix runs: exit 2" "$rc" 2
check "TC-CLI-008 v0.1 lock message" grep -q 'Another php-quickpatch run is in progress.' "$T/o.txt"
hold -s; qp scan --path "$P" --only webshell >/dev/null 2>&1; rc=$?; wait
assert_eq "TC-CLI-009 scan while scan runs: allowed (shared lock)" "$rc" 0
hold -x; qp scan --path "$P" --only webshell >/dev/null 2>&1; rc=$?; wait
assert_eq "TC-CLI-009 scan while fix runs: exit 2" "$rc" 2
hold -s; qp fix --path "$P" --only webshell >/dev/null 2>&1; rc=$?; wait
assert_eq "TC-CLI-009 fix while scan runs: exit 2" "$rc" 2
hold -s; qp fix --dry-run --path "$P" --only webshell >/dev/null 2>&1; rc=$?; wait
assert_eq "TC-CLI-009 fix --dry-run while scan runs: allowed (read)" "$rc" 0

# --- TC-CLI-014: commands that need Python ----------------------------------
PATH="$STUB:$NOPY" bash "$QP" assess --json >"$T/out.json" 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-014 no python3: exit 2" "$rc" 2
assert_eq "TC-CLI-014 no python3: ERR-CLI-424-01" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-424-01
check "TC-CLI-014 wording" grep -q 'assess requires Python 3.6+.' "$T/err.txt"

# --- TC-CLI-028: core commands without Python --------------------------------
for args in "scan" "fix --dry-run" "rollback --dry-run"; do
  # shellcheck disable=SC2086
  PATH="$STUB:$NOPY" bash "$QP" $args --path "$P" --only php >/dev/null 2>&1; rc=$?
  check "TC-CLI-028 '$args' without python3 ends 0 or 1 (got $rc)" test "$rc" -le 1
done

# --- TC-CLI-029: flock missing -------------------------------------------------
NOFLOCK=$(path_without "$T/noflock" flock)
PATH="$NOFLOCK" bash "$QP" scan --json >"$T/out.json" 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-029 no flock: exit 2" "$rc" 2
assert_eq "TC-CLI-029 no flock: ERR-CLI-424-02" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-424-02
check "TC-CLI-029 wording" grep -q 'Bash 4.3+, flock and curl are required (found: ' "$T/err.txt"

# --- TC-CLI-101: languages -----------------------------------------------------
QP_LANG="vi" qp scan --json --foo >"$T/out.json" 2>/dev/null; rc=$?
assert_eq "TC-CLI-101 vi: same code" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-400-01
assert_eq "TC-CLI-101 vi: Vietnamese message" "$(json_get "$T/out.json" 'd["errors"][0]["message"]')" "Tham số không hợp lệ hoặc thiếu: --foo"
assert_eq "TC-CLI-101 vi: exit 2 like en" "$rc" 2
python3 - "$QP_ROOT/share/php-quickpatch/catalog/errors.tsv" <<'PY' && pass "TC-CLI-101 every ERR code has vi and en text" || fail "TC-CLI-101 every ERR code has vi and en text"
import sys
rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[1]) if l.startswith("ERR-")]
bad = [r[0] for r in rows if len(r) < 6 or not r[4] or not r[5]]
print("codes:", len(rows), "missing:", bad)
sys.exit(1 if bad or len(rows) < 129 else 0)
PY

# --- TC-CLI-102 (JSON part): unsafe STATE_DIR reported in errors[] ------------
rm -rf "$SD"; mkdir -p "$T/evil"; chown "$QP_OTHER_UID" "$T/evil"; chmod 0777 "$T/evil"; ln -s "$T/evil" "$SD"
qp scan --json >"$T/out.json" 2>"$T/err.txt"; rc=$?
assert_eq "TC-CLI-102 symlink: exit 2" "$rc" 2
assert_eq "TC-CLI-102 symlink: errors[0].code" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-412-01
check "TC-CLI-102 symlink: reason=symlink in details" grep -q 'reason=symlink' "$T/out.json"
check "TC-CLI-102 stderr wording" grep -q "State directory $SD is unsafe (symlink); aborting." "$T/err.txt"
qp audit verify --json >"$T/out.json" 2>/dev/null; rc=$?
assert_eq "TC-CLI-102 symlink: python commands exit 2 too" "$rc" 2
assert_eq "TC-CLI-102 symlink: python errors[0].code" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-CLI-412-01
assert_eq "TC-CLI-102 /tmp/qp-evil stays empty" "$(find "$T/evil" -mindepth 1 | wc -l)" 0
rm -f "$SD"

# --- FR-CLI-SAFE-001: y/N on a TTY, --yes otherwise (used by new write commands) --
safe() { bash -c '. "$1"; JSON=0; exec 3>/dev/null; DRY_RUN=$2; ASSUME_YES=$3; confirm "migrate install" && echo applied' _ "$QP" "$@"; }
out=$(safe 0 0 </dev/null 2>&1); rc=$?
assert_eq "TC-CLI-026 no TTY, no --yes: exit 2" "$rc" 2
assert_contains "TC-CLI-026 wording (ERR-CLI-428-01)" "$out" "migrate install needs --yes when not interactive."
assert_eq "TC-CLI-026 --yes: goes on" "$(safe 0 1 </dev/null)" applied
assert_eq "TC-CLI-025 --dry-run: no question" "$(safe 1 0 </dev/null)" applied
if command -v script >/dev/null; then
  out=$(printf 'y\n' | script -qec "bash -c '. \"$QP\"; JSON=0; exec 3>/dev/null; DRY_RUN=0; ASSUME_YES=0; confirm \"migrate install\" && echo applied'" /dev/null 2>&1)
  assert_contains "TC-CLI-025 TTY answer y: applied" "$out" applied
  out=$(printf '\n' | script -qec "bash -c '. \"$QP\"; JSON=0; exec 3>/dev/null; DRY_RUN=0; ASSUME_YES=0; confirm \"migrate install\" && echo applied'" /dev/null 2>&1)
  assert_not_contains "TC-CLI-027 TTY Enter (default N): nothing applied" "$out" applied
fi

# --- ERR-PTCH-404-01 in JSON -------------------------------------------------
rm -rf "$SD"; qp rollback --json >"$T/out.json" 2>/dev/null; rc=$?
assert_eq "TC-PTCH-027 rollback without runs: exit 2" "$rc" 2
assert_eq "TC-PTCH-027 rollback without runs: ERR-PTCH-404-01" "$(json_get "$T/out.json" 'd["errors"][0]["code"]')" ERR-PTCH-404-01

t_done
