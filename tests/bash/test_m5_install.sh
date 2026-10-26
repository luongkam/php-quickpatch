#!/usr/bin/env bash
# M5 — migrate install / remove-old (FR-UPG-PRE-001, FR-UPG-INST-001, FR-UPG-CFG-002, FR-UPG-RMV-001;
# TC-UPG-001..007, TC-UPG-009, TC-UPG-045..047, BR-SCN-012, BR-SCN-014, BR-SCN-016).
# Needs two installed PHP-FPM branches (Debian layout). apt-get is a stub that records its call (the
# packages of the target are already installed); apt-cache, update-alternatives, dpkg and php-fpm are the
# real ones inside a private mount namespace (/etc, /var/lib, /var/log and /run are overlays).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
OLD=""; NEW=""
for b in /usr/sbin/php-fpm[0-9]*; do
  [ -x "$b" ] || continue; v=${b#/usr/sbin/php-fpm}
  if [ -z "$OLD" ]; then OLD=$v; elif [ -z "$NEW" ]; then NEW=$v; fi
done
if [ -z "$NEW" ] || ! command -v apt-cache >/dev/null || ! command -v update-alternatives >/dev/null || \
   [ "$(apt-cache policy "php$NEW-fpm" 2>/dev/null | awk '/Candidate:/ { print $2 }')" = "(none)" ]; then
  echo "# skip $(basename "$0"): needs two php-fpm branches installed with apt (Debian/Ubuntu)"; exit 0
fi
if [ -z "${QP_IN_NS:-}" ]; then QP_IN_NS=1 exec unshare -m --propagation private bash "$0" "$@"; fi

T=$(new_tmp)
for d in etc var/lib var/log run opt; do
  mkdir -p "$T/ov/$d.u" "$T/ov/$d.w"
  mount -t overlay overlay -o "lowerdir=/$d,upperdir=$T/ov/$d.u,workdir=$T/ov/$d.w" "/$d" || { echo "# overlay /$d failed"; exit 1; }
done
mkdir -p /run/php && chown www-data:www-data /run/php && rm -f /run/php/*
stop_all() {
  local p me; me=$(readlink /proc/self/ns/mnt)
  for p in $(pgrep -f 'php-fpm: master'); do [ "$(readlink "/proc/$p/ns/mnt")" = "$me" ] && kill "$p" 2>/dev/null; done
  sleep 1
}
trap 'stop_all; for d in opt run var/log var/lib etc; do umount -l "/$d"; done; rm -rf "$T"' EXIT
for b in "$OLD" "$NEW"; do grep -q '^pid' "/etc/php/$b/fpm/php-fpm.conf" || sed -i "s#^\[global\]#[global]\npid = /run/php/php$b-fpm.pid#" "/etc/php/$b/fpm/php-fpm.conf"; done

# shellcheck disable=SC2034  # FX is read by the stubs
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; curl_stub
cat >"$STUB/apt-get" <<EOF
#!/bin/bash
printf 'apt-get %s\n' "\$*" >>"$CALLS"
[ -f "$T/apt-moves-default" ] && [[ " \$* " == *" install "* ]] && update-alternatives --set php /usr/bin/php$NEW >/dev/null 2>&1
exit 0
EOF
chmod +x "$STUB/apt-get"
J=$T/out.json
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
jr() { json_get "$J" "$1"; }
SD=/var/lib/php-quickpatch
update-alternatives --set php "/usr/bin/php$OLD" >/dev/null 2>&1
DEF0=$(readlink -f /usr/bin/php)

# custom configuration of $OLD (FR-UPG-CFG-002)
printf 'memory_limit = 384M\nmax_input_vars = 3000\n' >"/etc/php/$OLD/fpm/conf.d/99-site-custom.ini"
printf '; mitigation\nzend.assertions = -1\n' >"/etc/php/$OLD/fpm/conf.d/zz-php-quickpatch-mitigation.ini"
sed -i -E 's/^upload_max_filesize = .*/upload_max_filesize = 64M/' "/etc/php/$OLD/fpm/php.ini"
rm -f "/etc/php/$NEW/fpm/conf.d/99-site-custom.ini" "/etc/php/$NEW/fpm/conf.d/90-php-quickpatch-from-$OLD.ini"

# --- dry-run (TC-UPG-004 preview, BR-CLI-003) ---------------------------------------------------------------
fp0=$(fingerprint /etc/php /etc/alternatives)
qp migrate install --runtime php --target "$NEW" --from "$OLD" --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "install --dry-run exits 0" "$rc" 0
assert_eq "install --dry-run changes nothing" "$(fingerprint /etc/php /etc/alternatives)" "$fp0"
assert_eq "install --dry-run runs no apt-get" "$(cat "$CALLS")" ""
assert_eq "TC-UPG-001: 5 preconditions, all pass" "$(jr '[(p["check"], p["pass"]) for p in d["result"]["preconditions"]]')" \
  "[('disk_free_mb', True), ('mem_available_mb', True), ('privilege', True), ('os_supported', True), ('repo_has_target', True)]"
assert_contains "dry-run: packages php$NEW-fpm php$NEW-cli, no meta package" "$(jr 'd["result"]["packages"][:2]') $(jr '"php'"$NEW"'" in d["result"]["packages"]')" \
  "['php$NEW-fpm', 'php$NEW-cli'] False"
assert_contains "dry-run: preview pins the defaults (BR-SCN-012)" "$(jr '[c["type"] for c in d["result"]["preview"]["changes"]]')" "'link'"
check "install --dry-run --json valid against qp.migrate/1" schema_ok "$J"

# --- TC-UPG-002/003: precondition failure -> ERR-SCN-412-01 ------------------------------------------------------
qp migrate install --runtime php --target 8.9 --from "$OLD" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-003: no package for the target -> ERR-SCN-412-01, exit 2" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-SCN-412-01"
assert_eq "TC-UPG-003: failed check repo_has_target" "$(jr '[p["check"] for p in d["result"]["preconditions"] if not p["pass"]]')" "['repo_has_target']"
qp migrate install --runtime php --target "$NEW" --json >"$J" 2>/dev/null </dev/null; rc=$?
assert_eq "install without --yes and no TTY -> ERR-CLI-428-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-428-01"

# --- install (TC-UPG-004..007, TC-UPG-009) --------------------------------------------------------------------
qp migrate install --runtime php --target "$NEW" --from "$OLD" --yes --json >"$J" 2>"$T/err"; rc=$?
assert_eq "TC-UPG-004: install exits 0" "$rc" 0
RI=$(jr 'd["result"]["run_id"]')
assert_contains "TC-UPG-004: apt-get install of php$NEW-fpm php$NEW-cli" "$(cat "$CALLS")" "install -y -q -o Dpkg::Options::=--force-confold php$NEW-fpm php$NEW-cli"
assert_eq "TC-UPG-005 / BR-SCN-012: default php unchanged" "$(readlink -f /usr/bin/php)" "$DEF0"
assert_contains "BR-SCN-012: manifest pins the php group" "$(cat "$SD/backups/$RI/manifest")" $'link\talt:php\t'
assert_eq "new_bin" "$(jr 'd["result"]["new_bin"]')" "/usr/bin/php$NEW"
check "TC-UPG-007: custom conf.d ini copied" grep -q '^memory_limit = 384M' "/etc/php/$NEW/fpm/conf.d/99-site-custom.ini"
check "FR-UPG-CFG-002: mitigation file not copied" test ! -e "/etc/php/$NEW/fpm/conf.d/zz-php-quickpatch-mitigation.ini"
check "FR-UPG-CFG-002: non-default php.ini value carried over" grep -q '^upload_max_filesize = 64M' "/etc/php/$NEW/fpm/conf.d/90-php-quickpatch-from-$OLD.ini"
assert_contains "cfg_report.copied lists both files" "$(jr 'd["result"]["cfg_report"]["copied"]')" "99-site-custom.ini"
assert_contains "TC-UPG-009: extensions of $OLD checked on $NEW" "$(jr 'd["result"]["cfg_report"]["extensions_installed"]')" "'mbstring'"
assert_contains "php$NEW-fpm restarted and active" "$(PATH="$STUB:$PATH" service "php$NEW-fpm" status 2>&1)" "is running"
check "install --json valid against qp.migrate/1" schema_ok "$J"
src=$(bash -c ". '$QP'; CATALOG_DIR='$QP_ROOT/share/php-quickpatch/catalog'; . '$QP_ROOT/share/php-quickpatch/lib/pb.sh'; removed_directives 8.4 8.5")
assert_eq "BR-SCN-046: directives removed in (8.4, 8.5] from the catalog" "$src" "disable_classes"

# --- rollback of the install run: copied files removed, pin restored; packages kept ---------------------------------
qp rollback "$RI" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "rollback of the install run exits 0" "$rc" 0
check "rollback removed the copied ini files" test ! -e "/etc/php/$NEW/fpm/conf.d/99-site-custom.ini" -a ! -e "/etc/php/$NEW/fpm/conf.d/90-php-quickpatch-from-$OLD.ini"
assert_contains "rollback keeps the packages (note)" "$(jr '[m["action"] for m in d["result"]["manifest"]]')" "'note'"

# --- UC-UPG-001 7a: the default moved during the install -> restored, ERR-ENV-424-01 --------------------------------------
touch "$T/apt-moves-default"
qp migrate install --runtime php --target "$NEW" --from "$OLD" --yes --json >"$J" 2>/dev/null; rc=$?
rm -f "$T/apt-moves-default"
assert_eq "7a: default link changed by the install -> exit 2 ERR-ENV-424-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-ENV-424-01"
assert_eq "7a: default php restored" "$(readlink -f /usr/bin/php)" "$DEF0"

# --- remove-old (TC-UPG-045..047, BR-SCN-014) ------------------------------------------------------------------------
qp migrate remove-old --runtime php --from "$OLD" --reason "branch unused since the switch of all sites" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-046: used in the last 14 days -> ERR-UPG-412-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-412-01"
qp migrate remove-old --runtime php --from "$OLD" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "remove-old needs --reason (second confirmation)" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
# 20 days without use; one PASSED switch away from $OLD keeps its rollback until the removal
old_ts=$(date -u -d '20 days ago' +%Y-%m-%dT%H:%M:%S.000Z)
for f in "/var/log/php$OLD-fpm.log" /etc/php/"$OLD"/fpm/pool.d/*.conf; do [ -e "$f" ] && touch -d '20 days ago' "$f"; done
mkdir -p "$SD/switches" "$SD/backups/20260101-000000" && chmod 0700 "$SD/backups/20260101-000000"
printf '#ts\trun_id\tsite_id\tsite_key\tfrom>to\tstatus\tactor\tplan_id\tjob_id\trollback_reason\tnote\n%s\t20260101-000000\told.test\told.test\t%s>%s\tPASSED\tcli:root\t-\t-\t-\t-\n' \
  "$old_ts" "$OLD" "$NEW" >"$SD/switches/index.tsv"
printf 'run_id=20260101-000000\nsite_id=old.test\nsite_key=old.test\nfrom_branch=%s\nto_branch=%s\nstatus=PASSED\nrollback_available=1\n' "$OLD" "$NEW" \
  >"$SD/backups/20260101-000000/switch.vars"; chmod 0600 "$SD/backups/20260101-000000/switch.vars"
: >"$CALLS"
qp migrate remove-old --runtime php --from "$OLD" --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-045: remove-old --dry-run after 20 idle days" "$rc $(jr 'd["result"]["idle_days"] >= 14')" "0 True"
assert_eq "remove-old --dry-run: affected switch loses its rollback" "$(jr 'd["result"]["affected_switches"]')" "[{'run_id': '20260101-000000', 'rollback_available': False}]"
assert_eq "remove-old --dry-run runs no apt-get" "$(cat "$CALLS")" ""
check "remove-old --dry-run --json valid against qp.migrate/1" schema_ok "$J"
qp migrate remove-old --runtime php --from "$OLD" --reason "branch unused since the switch of all sites" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-047: remove-old exits 0" "$rc" 0
assert_contains "TC-UPG-047: apt-get remove of the $OLD packages" "$(cat "$CALLS")" "remove -y -q php$OLD-"
assert_eq "TC-UPG-047: switch record rollback_available=false" "$(sed -n 's/^rollback_available=//p' "$SD/backups/20260101-000000/switch.vars")" 0
qp rollback-site old.test --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "rollback-site after remove-old -> ERR-ENV-410-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-ENV-410-01"

# --- Node.js: PB-015 tarball into /opt/node-<major> (FR-UPG-INST-001, TC-UPG-006, BR-SCN-026/028) ----------------------
if [ "$(uname -m)" = x86_64 ]; then
  mk_node_tar() { # mk_node_tar VERSION [glibc]: tarball + SHASUMS256.txt + index.json served by the curl stub
    local v=$1 d="$T/dl/node-v$1-linux-x64"; rm -rf "$T/dl"; mkdir -p "$d/bin"
    if [ "${2:-}" = glibc ]; then printf '#!/bin/sh\necho "node: /lib/x86_64-linux-gnu/libc.so.6: version GLIBC_2.99 not found" >&2; exit 1\n' >"$d/bin/node"
    else printf '#!/bin/sh\ncase "$1" in -v) echo v%s ;; esac\nexit 0\n' "$v" >"$d/bin/node"; fi
    chmod +x "$d/bin/node"
    tar -cJf "$T/dl/node-v$v-linux-x64.tar.xz" -C "$T/dl" "node-v$v-linux-x64"
    (cd "$T/dl" && sha256sum "node-v$v-linux-x64.tar.xz" >SHASUMS256.txt)
    printf '[{"version":"v%s"},{"version":"v22.23.4"}]\n' "$v" >"$T/dl/index.json"
    curl_serve "https://nodejs.org/dist/index.json" "$T/dl/index.json"
    curl_serve "https://nodejs.org/dist/v$v/node-v$v-linux-x64.tar.xz" "$T/dl/node-v$v-linux-x64.tar.xz"
    curl_serve "https://nodejs.org/dist/v$v/SHASUMS256.txt" "$T/dl/SHASUMS256.txt"
  }
  mk_node_tar 24.22.1
  qp migrate install --runtime node --target 24 --dry-run --json >"$J" 2>/dev/null; rc=$?
  assert_eq "Node install --dry-run: tarball planned, nothing written" "$rc $(jr 'd["result"]["packages"]') $(test -e /opt/node-24 && echo exists || echo absent)" \
    "0 ['node-v24.22.1-linux-x64.tar.xz'] absent"
  qp migrate install --runtime node --target 24 --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "TC-UPG-006: Node.js 24 installed in /opt/node-24" "$rc $(/opt/node-24/bin/node -v) $(jr 'd["result"]["new_bin"]')" "0 v24.22.1 /opt/node-24/bin/node"
  RN=$(jr 'd["result"]["run_id"]')
  check "install --runtime node --json valid against qp.migrate/1" schema_ok "$J"
  qp rollback "$RN" --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "rollback of the Node.js install removes /opt/node-24" "$rc $(test -e /opt/node-24 && echo exists || echo absent)" "0 absent"
  mk_node_tar 24.22.1; echo "0000000000000000000000000000000000000000000000000000000000000000  node-v24.22.1-linux-x64.tar.xz" >"$T/dl/SHASUMS256.txt"
  qp migrate install --runtime node --target 24 --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "checksum mismatch -> ERR-PTCH-502-01, nothing installed" "$rc $(jr 'd["errors"][0]["code"]') $(test -e /opt/node-24 && echo exists || echo absent)" "2 ERR-PTCH-502-01 absent"
  mk_node_tar 24.22.1 glibc
  qp migrate install --runtime node --target 24 --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "BR-SCN-028: binary needs a newer glibc -> ERR-SCN-412-03" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-SCN-412-03"
  qp rollback "$(jr 'd["result"]["run_id"]')" --yes >/dev/null 2>&1
  # remove-old of a tarball prefix: kept 14 days, then removed with an untar line (reversible)
  mk_node_tar 24.22.1; qp migrate install --runtime node --target 24 --yes >/dev/null 2>&1
  qp migrate remove-old --runtime node --from 24 --reason "Node.js 24 prefix unused after the switch" --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "remove-old Node.js prefix used recently -> ERR-UPG-412-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-412-01"
  touch -d '20 days ago' /opt/node-24/bin/node
  qp migrate remove-old --runtime node --from 24 --reason "Node.js 24 prefix unused after the switch" --yes --json >"$J" 2>/dev/null; rc=$?
  assert_eq "remove-old of /opt/node-24 after 20 idle days" "$rc $(test -e /opt/node-24 && echo exists || echo absent)" "0 absent"
  qp rollback --yes >/dev/null 2>&1
  assert_eq "rollback of remove-old restores the prefix from its tar" "$(/opt/node-24/bin/node -v 2>/dev/null)" v24.22.1
else
  echo "# skip Node.js install: not x86_64"
fi
t_done
