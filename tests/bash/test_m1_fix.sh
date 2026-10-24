#!/usr/bin/env bash
# M1 — fix/rollback (FR-PTCH-*): package upgrade, package groups, mitigation,
# Node.js tarball, Composer/npm, WordPress, Docker, restart checks, manifest,
# atomic run directory, audit (TC-PTCH-001..025, 101..106; TC-JOB-019/020).
# Package managers, systemd, Docker, wp-cli and the network are stubs.
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'rm -rf "$T"' EXIT
SD=/var/lib/php-quickpatch
STUB=$T/stub CALLS=$T/calls FX=$T/fx
J=$T/out.json
export QP_PHP_BINS=" " QP_NODE_BINS=" "
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }

# reset: fresh state dir, stubs and fixtures for one scenario
reset() {
  rm -rf "$SD" "$STUB" "$FX" "$T/w"; mkdir -p "$T/w"
  stubs_init; chmod 666 "$CALLS"; chmod 777 "$FX/state"; dpkg_stubs; apt_stub; curl_stub; touch "$FX/state/osv.vulns"
}
calls() { grep -E "^$1 " "$CALLS"; }
manifest() { cat "$SD"/backups/*/manifest 2>/dev/null; }

# A distro PHP 8.2.34 (php8.2-cli, -fpm, -mysql) with two conf.d dirs.
php82() {
  mkdir -p "$T/w/etc/php/8.2/cli/conf.d" "$T/w/etc/php/8.2/fpm/conf.d"
  fake_php "$T/w/usr/bin/php8.2" 8.2.34 "$T/w/etc/php/8.2/cli/conf.d:$T/w/etc/php/8.2/fpm/conf.d"
  dpkg_owns "$T/w/usr/bin/php8.2" php8.2-cli 8.2.34-1 php8.2-fpm php8.2-mysql
  export QP_PHP_BINS="$T/w/usr/bin/php8.2"
}

# --- TC-PTCH-001: dpkg upgrade 8.2.34 -> 8.2.35 ------------------------------
reset; php82; apt_upgrades "$T/w/usr/bin/php8.2" 8.2.35
qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?
check "TC-PTCH-001 apt-get --only-upgrade with the 3 packages of the build" \
  grep -qx 'apt-get install -y -q --only-upgrade -o Dpkg::Options::=--force-confold php8.2-cli php8.2-fpm php8.2-mysql' "$CALLS"
check "TC-PTCH-001 manifest has a note line for the upgrade" bash -c "grep -qP '^note\tapt upgraded: php8.2-cli php8.2-fpm php8.2-mysql' $SD/backups/*/manifest"
check "TC-PTCH-001 text: PHP 8.2.35 now has the fix" grep -q 'PHP 8.2.35.* now has the fix (ok)' "$T/err.txt"
assert_eq "TC-PTCH-001 runtimes_after state ok" "$(json_get "$J" '[(r["version_before"], r["version_after"], r["state_after"]) for r in d["result"]["runtimes_after"]]')" "[('8.2.34', '8.2.35', 'ok')]"
check "TC-PTCH-001 restart flag set (restart section printed)" grep -q '== Restarting PHP services ==' "$T/err.txt"
assert_eq "TC-PTCH-001 exit 0" "$rc" 0
check "TC-PTCH-001 fix output valid against schema" schema_ok "$J"
assert_eq "TC-JOB-019 audit: INTENT then RESULT for fix" "$(python3 -c 'import json,glob; print([(r["record_type"], r["action"], r["result"]) for f in sorted(glob.glob("/var/lib/php-quickpatch/audit/*.jsonl")) for r in map(json.loads, open(f))])')" \
  "[('INTENT', 'fix', None), ('RESULT', 'fix', 'ok')]"
check "TC-JOB-019 audit file mode 0600" test "$(stat -c %a "$SD"/audit/audit-*.jsonl)" = 600
assert_eq "TC-JOB-019 audit_anchor = last record" "$(json_get "$J" 'd["audit_anchor"]["seq"]')" 2
check "TC-JOB-019 python verifies the Bash-written chain" qp audit verify

# --- TC-PTCH-002: package groups (BR-PTCH-002) --------------------------------
grp=$(bash -c '. "$1"; php_pkg_group dpkg ea-php82-php-cli; php_pkg_group rpm alt-php82-cli; php_pkg_group dpkg lsphp82; php_pkg_group apk php82; php_pkg_group dpkg custom-php-test; php_pkg_group dpkg php8.2-cli; php_pkg_group rpm php84-php-cli' _ "$QP" | tr '\n' ' ')
assert_eq "TC-PTCH-002 groups (ea-php on dpkg = CR-SRS-07)" "$grp" "ea-php82 alt-php82* lsphp82 php82 php php8.2 php84* "

# --- TC-PTCH-003: repository has no fixed build --------------------------------
reset; php82
qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-PTCH-003 ERR-PTCH-424-01 recorded" "$(json_get "$J" '[a["error_code"] for a in d["result"]["actions"] if a["kind"]=="runtime_patch"]')" "['ERR-PTCH-424-01']"
assert_eq "TC-PTCH-003 critical issue with code" "$(json_get "$J" '[(i["severity"], i["code"]) for i in d["issues"]]')" "[('critical', 'ERR-PTCH-424-01')]"
check "TC-PTCH-003 mitigation written" test -f "$T/w/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini"
assert_eq "TC-PTCH-003 exit 1" "$rc" 1

# --- TC-PTCH-004: dry-run changes nothing -------------------------------------
reset; php82; apt_upgrades "$T/w/usr/bin/php8.2" 8.2.35
qp fix --only php --dry-run --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-004 prints the upgrade command" grep -q '\[dry-run\] env DEBIAN_FRONTEND=noninteractive apt-get install' "$T/err.txt"
assert_eq "TC-PTCH-004 apt-get never ran" "$(calls apt-get | wc -l)" 0
check "TC-PTCH-004 no backups/<run_id> created" test ! -d "$SD/backups"
assert_eq "TC-PTCH-004 version unchanged" "$("$T/w/usr/bin/php8.2" -r 'echo PHP_VERSION;')" 8.2.34
assert_eq "TC-PTCH-004 preview lists the package upgrade" "$(json_get "$J" '[c["type"]+":"+c["action"] for c in d["result"]["preview"]["changes"]][:1]')" "['package:upgrade']"
assert_eq "TC-PTCH-004 reversibility partial (packages)" "$(json_get "$J" 'd["result"]["preview"]["reversibility"]["level"]')" partial
check "TC-PTCH-004 dry-run output valid against schema" schema_ok "$J"
assert_eq "TC-PTCH-004 no audit for dry-run" "$(ls "$SD/audit" 2>/dev/null | wc -l)" 0

# --- TC-PTCH-005: mitigation in 2 conf.d, removed once patched -----------------
reset; mkdir -p "$T/w/c1" "$T/w/c2"; fake_php "$T/w/php85/bin/php" 8.5.11 "$T/w/c1:$T/w/c2"; export QP_PHP_BINS="$T/w/php85/bin/php"
qp fix --only php >"$T/o.txt" 2>&1
assert_eq "TC-PTCH-005 file in both conf.d" "$(find "$T/w/c1" "$T/w/c2" -name zz-php-quickpatch-mitigation.ini | wc -l)" 2
assert_eq "TC-PTCH-005 one created line per file" "$(manifest | grep -cP '^created\t')" 2
check "TC-PTCH-005 8.5 rule: fatal_error_backtraces = 0" grep -qx 'fatal_error_backtraces = 0' "$T/w/c1/zz-php-quickpatch-mitigation.ini"
echo 8.5.12 >"$(php_ver_file "$T/w/php85/bin/php")"
qp fix --only php --json >"$J" 2>"$T/o.txt"
assert_eq "TC-PTCH-005 both files removed once patched" "$(find "$T/w/c1" "$T/w/c2" -name zz-php-quickpatch-mitigation.ini | wc -l)" 0
assert_eq "TC-PTCH-005 copy lines before removal" "$(tac "$(ls -d "$SD"/backups/*/ | tail -n1)manifest" | grep -cP '^copy\t.*zz-php-quickpatch-mitigation.ini')" 2
check "TC-PTCH-005 restart flag set" grep -q '== Restarting PHP services ==' "$T/o.txt"
assert_eq "TC-PTCH-005 mitigations[] removed x2" "$(json_get "$J" '[m["action"] for m in d["result"]["mitigations"]]')" "['removed', 'removed']"

# --- TC-PTCH-006: build without conf.d -----------------------------------------
reset; fake_php "$T/w/srv/test/php/bin/php" 8.2.34 ""; echo 'x=1' >"$T/w/php.ini"; export QP_PHP_BINS="$T/w/srv/test/php/bin/php"
qp fix --only php --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-006 wording" grep -q "No conf.d scan dir for $T/w/srv/test/php/bin/php; set the mitigation in its php.ini by hand." "$T/err.txt"
check "TC-PTCH-006 ERR-PTCH-412-01 in output" grep -q ERR-PTCH-412-01 "$J"
assert_eq "TC-PTCH-006 php.ini untouched" "$(cat "$T/w/php.ini")" "x=1"

# --- TC-PTCH-007: existing file kept, --no-memlimit ------------------------------
reset; mkdir -p "$T/w/c1" "$T/w/c2"; fake_php "$T/w/php82b/bin/php" 8.2.34 "$T/w/c1:$T/w/c2"; export QP_PHP_BINS="$T/w/php82b/bin/php"
printf '; edited by hand\nsession.upload_progress.enabled = 0\nmax_input_vars = 5000\n' >"$T/w/c1/zz-php-quickpatch-mitigation.ini"
h=$(sha256sum <"$T/w/c1/zz-php-quickpatch-mitigation.ini")
qp fix --only php --no-memlimit >/dev/null 2>&1
assert_eq "TC-PTCH-007 hand-edited file keeps its SHA-256" "$(sha256sum <"$T/w/c1/zz-php-quickpatch-mitigation.ini")" "$h"
check "TC-PTCH-007 new file has no memory_limit line" bash -c "! grep -q memory_limit $T/w/c2/zz-php-quickpatch-mitigation.ini"
check "TC-PTCH-007 new file exists" test -f "$T/w/c2/zz-php-quickpatch-mitigation.ini"

# --- TC-PTCH-008/009: Node.js tarball in a private prefix -------------------------
mk_node_tar() { # mk_node_tar VERSION: tarball + SHASUMS256.txt served by the curl stub
  local v=$1 d="$T/w/dl/node-v$1-linux-x64"
  mkdir -p "$d/bin" "$d/lib/node_modules/npm"
  printf '#!/bin/sh\necho v%s\n' "$v" >"$d/bin/node"; chmod +x "$d/bin/node"
  echo '{"version": "10.9.9"}' >"$d/lib/node_modules/npm/package.json"
  tar -cJf "$T/w/dl/node-v$v-linux-x64.tar.xz" -C "$T/w/dl" "node-v$v-linux-x64"
  (cd "$T/w/dl" && sha256sum "node-v$v-linux-x64.tar.xz" >SHASUMS256.txt)
  printf '[{"version":"v26.12.1"},{"version":"v%s"},{"version":"v24.21.0"}]\n' "$v" >"$T/w/dl/index.json"
  curl_serve "https://nodejs.org/dist/index.json" "$T/w/dl/index.json"
  curl_serve "https://nodejs.org/dist/v$v/node-v$v-linux-x64.tar.xz" "$T/w/dl/node-v$v-linux-x64.tar.xz"
  curl_serve "https://nodejs.org/dist/v$v/SHASUMS256.txt" "$T/w/dl/SHASUMS256.txt"
}
if [ "$(uname -m)" = x86_64 ]; then
  reset; export QP_PHP_BINS=" "; fake_node "$T/w/usr/local" 24.21.0; export QP_NODE_BINS="$T/w/usr/local/bin/node"; mk_node_tar 24.22.1
  qp fix --only node --json >"$J" 2>"$T/err.txt"
  check "TC-PTCH-008 tarball downloaded" grep -q 'curl .*node-v24.22.1-linux-x64.tar.xz' "$CALLS"
  check "TC-PTCH-008 untar line in manifest" bash -c "grep -qP '^untar\t.*node-_.*\.tar\.gz\t$T/w/usr/local\$' $SD/backups/*/manifest"
  assert_eq "TC-PTCH-008 backup holds bin and npm" "$(tar -tzf "$SD"/backups/*/node-*.tar.gz | grep -cE '^(bin/node|lib/node_modules/npm/package.json)$')" 2
  assert_eq "TC-PTCH-008 node --version" "$("$T/w/usr/local/bin/node" --version)" v24.22.1
  reset; fake_node "$T/w/usr/local" 24.21.0; mk_node_tar 24.22.1; echo "0000000000000000000000000000000000000000000000000000000000000000  node-v24.22.1-linux-x64.tar.xz" >"$T/w/dl/SHASUMS256.txt"
  qp fix --only node --json >"$J" 2>"$T/err.txt"
  assert_eq "TC-PTCH-009 ERR-PTCH-502-01" "$(json_get "$J" '[a["error_code"] for a in d["result"]["actions"]]')" "['ERR-PTCH-502-01']"
  assert_eq "TC-PTCH-009 prefix unchanged" "$("$T/w/usr/local/bin/node" --version)" v24.21.0
else
  echo "# skip TC-PTCH-008/009: not x86_64"
fi
export QP_NODE_BINS=" "

# --- TC-PTCH-011/012: Composer project owned by another user ----------------------
composer_proj() {
  mkdir -p "$T/w/var/www/shop.test"
  printf '{"packages":[{"name":"vendor-test/lib","version":"1.2.0"}]}\n' >"$T/w/var/www/shop.test/composer.lock"
  echo '{"require":{"vendor-test/lib":"^1.2"}}' >"$T/w/var/www/shop.test/composer.json"
  chown -R nobody "$T/w/var/www/shop.test"; chmod 777 "$T/w" "$T/w/var" "$T/w/var/www"
  echo "vendor-test/lib 1.2.0 GHSA-test-0001" >"$FX/state/osv.vulns"
}
reset; composer_proj
stub composer 'echo "uid=$(id -u) $*" >>"$FX/state/composer.log"; [ "$1" = update ] && sed -i s/1.2.0/1.2.5/ composer.lock; exit 0'
qp fix --only composer --path "$T/w" --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-011 manifest: composer-install line" bash -c "grep -qP '^composer-install\t$T/w/var/www/shop.test\$' $SD/backups/*/manifest"
assert_eq "TC-PTCH-011 composer.json and composer.lock copied" "$(manifest | grep -cP '^copy\t.*shop.test/composer\.(json|lock)\t')" 2
check "TC-PTCH-011 composer update as the owner" grep -q "^uid=65534 update vendor-test/lib --with-all-dependencies --no-interaction --no-progress" "$FX/state/composer.log"
assert_eq "TC-PTCH-011 OSV re-check shows 0 left" "$(json_get "$J" 'len(d["result"]["actions"]) and [a["status"] for a in d["result"]["actions"]]')" "['done']"
check "TC-PTCH-011 fixed counted" grep -q 'FIXED: .*1 vulnerable Packagist package(s) updated' "$T/err.txt"
reset; composer_proj
stub composer 'echo "uid=$(id -u) $*" >>"$FX/state/composer.log"; [ "$1" = update ] && { echo broken >composer.lock; exit 2; }; exit 0'
before=$(sha256sum "$T/w/var/www/shop.test/composer.lock" | cut -c1-64)
qp fix --only composer --path "$T/w" --json >"$J" 2>"$T/err.txt"
assert_eq "TC-PTCH-012 composer.lock restored" "$(sha256sum "$T/w/var/www/shop.test/composer.lock" | cut -c1-64)" "$before"
check "TC-PTCH-012 composer install re-run" grep -q '^uid=65534 install --no-interaction --no-progress' "$FX/state/composer.log"
assert_eq "TC-PTCH-012 ERR-PTCH-424-02 high issue" "$(json_get "$J" '[(i["severity"], i["code"]) for i in d["issues"] if i["code"]]')" "[('high', 'ERR-PTCH-424-02')]"

# --- TC-PTCH-013: npm audit fix, no --force, as the owner --------------------------
reset; mkdir -p "$T/w/home/shop/app"; chmod 777 "$T/w" "$T/w/home" "$T/w/home/shop"
printf '{"lockfileVersion":3,"packages":{"":{},"node_modules/left-pad":{"version":"1.0.0"}}}\n' >"$T/w/home/shop/app/package-lock.json"
echo '{}' >"$T/w/home/shop/app/package.json"; chown -R nobody "$T/w/home/shop/app"
echo "left-pad 1.0.0 GHSA-test-0002" >"$FX/state/osv.vulns"
stub npm 'echo "uid=$(id -u) $*" >>"$FX/state/npm.log"; exit 0'
qp fix --only npm --path "$T/w" >/dev/null 2>&1
check "TC-PTCH-013 npm audit fix --no-fund" grep -qx 'uid=65534 audit fix --no-fund' "$FX/state/npm.log"
check "TC-PTCH-013 never --force" bash -c "! grep -q -- --force $FX/state/npm.log"

# --- TC-PTCH-014/016/105: WordPress with tar backups --------------------------------
wp_site() {
  W=$T/w/var/www/blog.test; mkdir -p "$W/wp-includes" "$W/wp-admin" "$W/wp-content/plugins/akismet"
  printf '<?php\n$wp_version = '"'"'%s'"'"';\n' "${1:-7.0.2}" >"$W/wp-includes/version.php"; echo 'admin v1' >"$W/wp-admin/index.php"
  echo '<?php // root' >"$W/index.php"; echo 'akismet 5.0' >"$W/wp-content/plugins/akismet/akismet.php"
  chown -R nobody "$W"; chmod 640 "$W/wp-includes/version.php"; chmod 777 "$T/w" "$T/w/var" "$T/w/var/www"
  stub wp '
echo "uid=$(id -u) $*" >>"$FX/state/wp.log"
case "$1 $2" in
  "plugin list") echo akismet ;;
  "core update") sed -i "s/7.0.2/7.0.7/" wp-includes/version.php; echo "admin v2" >wp-admin/index.php ;;
  "plugin update") echo "akismet 5.1" >wp-content/plugins/akismet/akismet.php ;;
  "core verify-checksums") [ -f "$FX/state/wp.tampered" ] && exit 1; exit 0 ;;
esac'
}
reset; wp_site
qp fix --only wp --path "$T/w" --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-014 core update --minor as the owner" grep -q '^uid=65534 core update --minor' "$FX/state/wp.log"
check "TC-PTCH-014 plugin update --all --patch as the owner" grep -q '^uid=65534 plugin update --all --patch' "$FX/state/wp.log"
check "TC-PTCH-014 version >= 7.0.7" grep -q "7.0.7" "$W/wp-includes/version.php"
check "TC-PTCH-105 untar line for core" bash -c "grep -qP '^untar\t.*/files/wp-[0-9a-f]{12}-core\.tar\.gz\t$W\$' $SD/backups/*/manifest"
check "TC-PTCH-105 untar line for the plugin" bash -c "grep -qP '^untar\t.*/files/wp-[0-9a-f]{12}-plugin-akismet\.tar\.gz\t$W\$' $SD/backups/*/manifest"
assert_eq "TC-PTCH-105 no copy line for version.php" "$(manifest | grep -c 'copy.*version.php')" 0
run_id=$(ls "$SD/backups" | tail -n1)
qp rollback "$run_id" --dry-run --json >"$J" 2>/dev/null
assert_eq "TC-PTCH-105 rollback preview: WordPress untar is reversible=partial" "$(json_get "$J" '[p["reversible"] for p in d["result"]["planned_actions"] if p["action"]=="untar"]')" "['partial', 'partial']"
qp rollback "$run_id" >/dev/null 2>&1
check "TC-PTCH-105 core back to 7.0.2" grep -q "7.0.2" "$W/wp-includes/version.php"
assert_eq "TC-PTCH-105 plugin back" "$(cat "$W/wp-content/plugins/akismet/akismet.php")" "akismet 5.0"
assert_eq "TC-PTCH-105 owner and mode of version.php kept" "$(stat -c '%U %a' "$W/wp-includes/version.php")" "nobody 640"
reset; wp_site; touch "$FX/state/wp.tampered"
qp fix --only wp --path "$T/w" --json >"$J" 2>"$T/err.txt"
assert_eq "TC-PTCH-016 ERR-PTCH-424-04 high issue" "$(json_get "$J" '[(i["severity"], i["code"]) for i in d["issues"] if i["code"]]')" "[('high', 'ERR-PTCH-424-04')]"

# --- TC-PTCH-015: no wp-cli available -------------------------------------------------
reset; wp_site 7.0.1; rm -f "$STUB/wp"   # 7.0.1: below the v0.1 data (7.0.2) until the M2 bundle
before=$(find "$W" -type f -exec sha256sum {} + | sort)
qp fix --only wp --path "$T/w" --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-015 wording + ERR-PTCH-424-03" grep -q "$W: wp-cli unavailable, update WordPress core to 7.0.2 by hand\",\"object_ref\".*ERR-PTCH-424-03\|ERR-PTCH-424-03.*$W: wp-cli unavailable, update WordPress core to 7.0.2 by hand" "$J"
assert_eq "TC-PTCH-015 site files untouched" "$(find "$W" -type f -exec sha256sum {} + | sort)" "$before"

# --- TC-PTCH-017: image tags ------------------------------------------------------------
reset; D=$T/w/srv/app; mkdir -p "$D"; echo 'FROM php:8.2.34-fpm' >"$D/Dockerfile"; printf 'services:\n  web:\n    image: node:24.21.0\n' >"$D/compose.yaml"
echo '{"version":"8.2.35"}' >"$T/w/rel.json"; curl_serve "https://www.php.net/releases/index.php?json&version=8.2" "$T/w/rel.json"
printf '[{"version":"v24.22.1"}]\n' >"$T/w/index.json"; curl_serve "https://nodejs.org/dist/index.json" "$T/w/index.json"
qp fix --only docker --path "$T/w" --json >"$J" 2>"$T/err.txt"
assert_eq "TC-PTCH-017 Dockerfile bumped" "$(cat "$D/Dockerfile")" "FROM php:8.2.35-fpm"
check "TC-PTCH-017 compose bumped" grep -q 'image: node:24.22.1' "$D/compose.yaml"
assert_eq "TC-PTCH-017 both files backed up" "$(manifest | grep -cP '^copy\t.*(Dockerfile|compose.yaml)\t')" 2
assert_eq "TC-PTCH-017 rebuild issue per file" "$(json_get "$J" 'sum(1 for i in d["issues"] if "rebuild and redeploy" in i["message"])')" 2
check "TC-PTCH-017 no docker build/push" bash -c "! grep -qE '^docker (build|push)' $CALLS"

# --- TC-PTCH-018/106: running containers ---------------------------------------------
docker_stub() { # containers: web-test (conf.d) and noconf (no conf.d)
  stub docker '
case "$1" in
  info) exit 0 ;;
  ps) printf "c1 web-test php:8.2.34-fpm\nc2 noconf php:8.2.34-cli\n" ;;
  inspect) [ -f "$FX/state/gone" ] && exit 1; exit 0 ;;
  exec) shift; [ "$1" = -i ] && shift; id=$1; shift
        case "$id:$*" in
          *PHP_VERSION*) printf 8.2.34 ;;
          c1:*--ini*) echo "Scan for additional .ini files in: /usr/local/etc/php/conf.d" ;;
          c2:*--ini*) echo "Scan for additional .ini files in: (none)" ;;
          c1:test\ -e\ *) [ -f "$FX/state/c1.ini" ] ;;
          c1:sh\ -c\ cat*) cat >"$FX/state/c1.ini" ;;
          c1:rm\ -f\ *) rm -f "$FX/state/c1.ini" ;;
          *) exit 1 ;;
        esac ;;
  restart) exit 0 ;;
esac'
}
reset; docker_stub
qp fix --only docker --path "$T/w" --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-018 ERR-PTCH-412-01 for the container without conf.d" grep -q 'ERR-PTCH-412-01' "$J"
check "TC-PTCH-018 web-test mitigation written" test -s "$FX/state/c1.ini"
check "TC-PTCH-018 web-test restarted" grep -qx 'docker restart c1' "$CALLS"
assert_eq "TC-PTCH-018 critical rebuild issue per container" "$(json_get "$J" 'sum(1 for i in d["issues"] if i["severity"]=="critical" and "needs a rebuild" in i["message"])')" 2
check "TC-PTCH-106 docker-created line before writing" bash -c "grep -qP '^docker-created\tc1\t/usr/local/etc/php/conf.d/zz-php-quickpatch-mitigation.ini\$' $SD/backups/*/manifest"
: >"$CALLS"; qp fix --only docker --path "$T/w" >/dev/null 2>&1
check "TC-PTCH-106 existing file in container is not rewritten" bash -c "! grep -q 'sh -c cat' $CALLS"
run_id=$(ls "$SD/backups" | head -n1)
qp rollback "$run_id" >/dev/null 2>&1
check "TC-PTCH-106 rollback removed the file in the container" test ! -e "$FX/state/c1.ini"
qp fix --only docker --path "$T/w" >/dev/null 2>&1; run_id=$(ls "$SD/backups" | tail -n1); touch "$FX/state/gone"
qp rollback "$run_id" >"$T/o.txt" 2>&1; rc=$?
check "TC-PTCH-106 container gone: warning, line skipped" grep -q 'container c1 no longer exists' "$T/o.txt"
assert_eq "TC-PTCH-106 container gone: rollback still exits 0" "$rc" 0

# --- TC-PTCH-020/104/022: restarts under systemd ----------------------------------------
systemd_on() { mount -t tmpfs tmpfs /run && mkdir -p /run/systemd/system; }
systemd_stub() { # systemd_stub IS_ACTIVE_EXIT
  stub systemctl '
case "$1" in
  list-units) printf "php8.2-fpm.service loaded active running PHP\nphp84-php-fpm.service loaded active running Remi\nnginx.service loaded active running nginx\n" ;;
  is-active) exit '"$1"' ;;
  *) exit 0 ;;
esac'
}
systemd_on
reset; php82; apt_upgrades "$T/w/usr/bin/php8.2" 8.2.35; systemd_stub 0
qp fix --only php --json >"$J" 2>"$T/err.txt"
check "TC-PTCH-020 php8.2-fpm restarted" grep -qx 'systemctl restart php8.2-fpm.service' "$CALLS"
check "TC-PTCH-020 Remi php84-php-fpm restarted (CR-SRS-07)" grep -qx 'systemctl restart php84-php-fpm.service' "$CALLS"
check "TC-PTCH-020 nginx not restarted" bash -c "! grep -q 'restart nginx' $CALLS"
assert_eq "TC-PTCH-020 restarted[] active" "$(json_get "$J" '[(r["service"], r["active"]) for r in d["result"]["restarted"]]')" "[('php8.2-fpm.service', True), ('php84-php-fpm.service', True)]"
reset; php82; systemd_stub 3
start=$SECONDS; qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?; el=$((SECONDS - start))
check "TC-PTCH-104 waited 15 s per failing service (took ${el}s)" test "$el" -ge 30 -a "$el" -le 45
check "TC-PTCH-104 wording" grep -q 'Service php8.2-fpm.service is not running 15 seconds after restart; sites may be down. Check its log, then run rollback .* if needed.' "$T/err.txt"
assert_eq "TC-PTCH-104 restarted[] inactive, waited 15" "$(json_get "$J" 'd["result"]["restarted"][0]')" "{'service': 'php8.2-fpm.service', 'active': False, 'waited_s': 15}"
assert_eq "TC-PTCH-104 restart_failures[]" "$(json_get "$J" 'len(d["result"]["restart_failures"])')" 2
assert_eq "TC-PTCH-104 ERR-PTCH-500-01 in errors[]" "$(json_get "$J" 'sorted(set(e["code"] for e in d["errors"]))')" "['ERR-PTCH-500-01']"
assert_eq "TC-PTCH-104 exit 2" "$rc" 2
assert_eq "TC-PTCH-104 audit result = failed" "$(tail -n1 "$SD"/audit/*.jsonl | python3 -c 'import json,sys; r=json.loads(sys.stdin.read()); print(r["result"], r["exit_code"])')" "failed 2"
reset; php82; apt_upgrades "$T/w/usr/bin/php8.2" 8.2.35; systemd_stub 0
qp fix --only php --no-restart --json >"$J" 2>/dev/null
assert_eq "TC-PTCH-022 --no-restart: 0 restarts" "$(calls systemctl | grep -c restart)" 0
check "TC-PTCH-022 --no-restart: high issue" grep -q 'PHP services not restarted' "$J"
reset; export QP_PHP_BINS=" "; systemd_stub 0; qp fix --only php >/dev/null 2>&1
assert_eq "TC-PTCH-022 nothing changed: no restart" "$(calls systemctl | grep -c restart)" 0
umount /run

# --- TC-PTCH-023: manifest written before the change, rollback hint ---------------------
reset; php82
stub apt-get '[ "$1" = update ] && exit 0; ls /var/lib/php-quickpatch/backups/*/manifest >/dev/null 2>&1 && grep -q "^note" /var/lib/php-quickpatch/backups/*/manifest && echo manifest-first >>"$FX/state/order"; exit 0'
qp fix --only php >"$T/o.txt" 2>&1
check "TC-PTCH-023 manifest line exists when apt-get runs" grep -q manifest-first "$FX/state/order"
run_id=$(ls "$SD/backups" | tail -n1)
check "TC-PTCH-023 run_id format" test -n "$(echo "$run_id" | grep -xE '[0-9]{8}-[0-9]{6}')"
check "TC-PTCH-023 every manifest line is ACTION<TAB>ARG1[<TAB>ARG2]" bash -c "! grep -vP '^[a-z-]+\t[^\t]+(\t[^\t]+)?\$' $SD/backups/$run_id/manifest"
check "TC-PTCH-023 summary rollback hint" grep -q "rollback: .*php-quickpatch.sh rollback $run_id" "$T/o.txt"

# --- TC-PTCH-024: not enough space for backups ---------------------------------------------
reset; php82; mount -t tmpfs -o size=40m tmpfs /var/lib
qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-PTCH-024 exit 2" "$rc" 2
assert_eq "TC-PTCH-024 ERR-ENV-507-01" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-ENV-507-01
assert_eq "TC-PTCH-024 no package change" "$(calls apt-get | grep -c install)" 0
assert_eq "TC-PTCH-024 no conf.d file written" "$(find "$T/w/etc" -name 'zz-*' | wc -l)" 0
umount /var/lib

# --- TC-PTCH-025: backups/ larger than 1 GiB -------------------------------------------------
reset; php82; stub du 'case "$*" in *backups*) printf "1153434\t%s\n" "${@: -1}" ;; *) exec /usr/bin/du "$@" ;; esac'
qp fix --only php --dry-run >/dev/null 2>&1
check "TC-PTCH-025 dry-run creates no backup dir" test ! -d "$SD/backups"
qp fix --only php >"$T/o.txt" 2>&1
check "TC-PTCH-025 warning > 1 GiB" grep -q 'uses 1126 MiB (> 1 GiB)' "$T/o.txt"

# --- TC-PTCH-101: rollback --dry-run --json with 5 manifest lines ---------------------------
reset; R=20261022-104201; mkdir -p "$SD/backups/$R/files"; chmod 700 "$SD" "$SD/backups/$R"
printf 'copy\t/var/www/shop.test/composer.lock\t%s/files/var/www/shop.test/composer.lock\ncreated\t/etc/php/8.2/fpm/conf.d/zz-php-quickpatch-mitigation.ini\nuntar\t%s/node-_usr_local.tar.gz\t/usr/local\ndocker-created\tweb-test\t/usr/local/etc/php/conf.d/zz-php-quickpatch-mitigation.ini\nnote\tapt upgraded: php8.2-cli php8.2-fpm (packages are not downgraded by rollback)\n' \
  "$SD/backups/$R" "$SD/backups/$R" >"$SD/backups/$R/manifest"; chmod 600 "$SD/backups/$R/manifest"
docker_stub
qp rollback "$R" --dry-run --json >"$J" 2>"$T/err.txt"
assert_eq "TC-PTCH-101 planned_actions in replay order" "$(json_get "$J" '[(p["action"], p["reversible"]) for p in d["result"]["planned_actions"]]')" \
  "[('note', 'none'), ('docker-created', 'full'), ('untar', 'full'), ('created', 'full'), ('copy', 'full')]"
assert_eq "TC-PTCH-101 dry_run true" "$(json_get "$J" 'd["dry_run"]')" True
assert_eq "TC-PTCH-101 one [dry-run] line per manifest line (note = warning)" "$(grep -c '\[dry-run\] ' "$T/err.txt")" 4
assert_eq "TC-PTCH-101 no docker/systemctl call" "$(grep -cE '^(docker (exec|restart)|systemctl)' "$CALLS")" 0
check "TC-PTCH-101 no audit for dry-run" test ! -d "$SD/audit"
check "TC-PTCH-101 rollback output valid against schema" schema_ok "$J"

# --- TC-PTCH-102/103: atomic backup run directory ----------------------------------------------
date_shim() { # date_shim ID...: +%Y%m%d-%H%M%S returns the IDs in turn (last one repeats)
  printf '%s\n' "$@" >"$FX/state/date.ids"; echo 0 >"$FX/state/date.n"
  stub date '
if [ "$1" = "+%Y%m%d-%H%M%S" ]; then
  n=$(cat "$FX/state/date.n"); echo $((n + 1)) >"$FX/state/date.n"
  total=$(wc -l <"$FX/state/date.ids"); [ "$n" -ge "$total" ] && n=$((total - 1))
  sed -n "$((n + 1))p" "$FX/state/date.ids"; exit 0
fi
exec /usr/bin/date "$@"'
}
reset; php82; mkdir -p "$SD/backups/20261022-104201/files"; printf 'note\tolder run\n' >"$SD/backups/20261022-104201/manifest"
old=$(cd "$SD/backups/20261022-104201" && find . -type f -exec sha256sum {} + | sort)
date_shim 20261022-104201 20261022-104202
qp fix --only php >"$T/o.txt" 2>&1
check "TC-PTCH-102 second run got its own directory" test -s "$SD/backups/20261022-104202/manifest"
assert_eq "TC-PTCH-102 first run untouched" "$(cd "$SD/backups/20261022-104201" && find . -type f -exec sha256sum {} + | sort)" "$old"
check "TC-PTCH-102 summary names the new run" grep -q 'rollback 20261022-104202' "$T/o.txt"
reset; php82; mkdir -p "$SD/backups/20261022-104201/files"; printf 'note\tolder run\n' >"$SD/backups/20261022-104201/manifest"
date_shim 20261022-104201
start=$SECONDS; qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?; el=$((SECONDS - start))
assert_eq "TC-PTCH-103 ERR-PTCH-409-01" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-PTCH-409-01
check "TC-PTCH-103 wording" grep -q "Could not create a new backup directory: $SD/backups/20261022-104201 still exists after 10 attempts; nothing was changed." "$T/err.txt"
assert_eq "TC-PTCH-103 exit 2" "$rc" 2
check "TC-PTCH-103 waited <= 10 s (took ${el}s)" test "$el" -le 12
assert_eq "TC-PTCH-103 no conf.d file, no package change" "$(find "$T/w/etc" -name 'zz-*' | wc -l) $(calls apt-get | grep -c install)" "0 0"

# --- TC-JOB-020: audit intent cannot be written ------------------------------------------------
reset; php82; apt_upgrades "$T/w/usr/bin/php8.2" 8.2.35; mkdir -m 0750 "$SD"; echo x >"$SD/audit"
qp fix --only php --json >"$J" 2>"$T/err.txt"; rc=$?
assert_eq "TC-JOB-020 ERR-AUD-500-01, exit 2" "$(json_get "$J" 'd["errors"][0]["code"]') $rc" "ERR-AUD-500-01 2"
check "TC-JOB-020 wording" grep -q 'Could not write the audit log; the change was cancelled.' "$T/err.txt"
assert_eq "TC-JOB-020 0 packages changed" "$(calls apt-get | wc -l)" 0

t_done
