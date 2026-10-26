#!/usr/bin/env bash
# M1 — scan --json inventory: runtimes, projects, containers, webshells
# (FR-SCAN-RT-001/002, FR-SCAN-PRJ-001/002, FR-SCAN-WSH-001;
# TC-SCAN-004..010, TC-SCAN-012).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'feeds_cleanup; rm -rf "$T"' EXIT
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; dpkg_stubs; curl_stub
feeds_fixture
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
J=$T/out.json

# --- TC-SCAN-004: 1 distro PHP + 1 tarball Node.js -------------------------
fake_php "$T/usr/bin/php8.3" 8.3.6 "$T/etc/php/8.3/cli/conf.d" "Core curl mbstring opcache"
mkdir -p "$T/usr/sbin"; printf '#!/bin/sh\n' >"$T/usr/sbin/php-fpm8.3"; chmod +x "$T/usr/sbin/php-fpm8.3"
dpkg_owns "$T/usr/bin/php8.3" php8.3-cli 8.3.6-0ubuntu0.24.04.13
fake_node "$T/usr/local" 24.22.1 137
QP_PHP_BINS="$T/usr/bin/php8.3" QP_NODE_BINS="$T/usr/local/bin/node" qp scan --only php,node --json --offline --path "$T/empty" >"$J" 2>/dev/null
assert_eq "TC-SCAN-004 2 runtimes" "$(json_get "$J" 'len(d["result"]["runtimes"])')" 2
assert_eq "TC-SCAN-004 runtime_id regex" "$(json_get "$J" 'all(__import__("re").match(r"^(php|node):[0-9a-f]{12}$", r["runtime_id"]) for r in d["result"]["runtimes"])')" True
php='[r for r in d["result"]["runtimes"] if r["kind"]=="php"][0]'
assert_eq "TC-SCAN-004 PHP version/branch" "$(json_get "$J" "${php}[\"version\"]+' '+${php}[\"branch\"]")" "8.3.6 8.3"
assert_eq "TC-SCAN-004 PHP owner_pkg" "$(json_get "$J" "${php}[\"owner_pkg\"][\"name\"]+' '+${php}[\"owner_pkg\"][\"version\"]")" "php8.3-cli 8.3.6-0ubuntu0.24.04.13"
assert_eq "TC-SCAN-004 PHP install_source package" "$(json_get "$J" "${php}[\"install_source\"]")" package
assert_eq "TC-SCAN-004 PHP sapis cli+fpm" "$(json_get "$J" "${php}[\"sapis\"]")" "['cli', 'fpm']"
assert_eq "TC-SCAN-004 PHP extensions" "$(json_get "$J" "${php}[\"extensions\"]")" "['core', 'curl', 'mbstring', 'opcache']"
node='[r for r in d["result"]["runtimes"] if r["kind"]=="node"][0]'
assert_eq "TC-SCAN-004 Node install_source tarball" "$(json_get "$J" "${node}[\"install_source\"]")" tarball
assert_eq "TC-SCAN-004 Node abi from process.versions.modules" "$(json_get "$J" "${node}[\"abi\"]")" 137
assert_eq "TC-SCAN-004 Node npm_version" "$(json_get "$J" "${node}[\"npm_version\"]")" 10.9.0
assert_eq "TC-SCAN-004 state in the allowed set" "$(json_get "$J" 'all(r["state"] in ("ok","ok-backport","vulnerable","eol","unknown") for r in d["result"]["runtimes"])')" True
check "TC-SCAN-004 output valid against schema" schema_ok "$J"

# --- TC-SCAN-005: a binary that hangs --------------------------------------
mkdir -p "$T/srv/php-hang/bin"; printf '#!/bin/sh\nsleep 60\n' >"$T/srv/php-hang/bin/php"; chmod +x "$T/srv/php-hang/bin/php"
start=$SECONDS
QP_PHP_BINS="$T/srv/php-hang/bin/php $T/usr/bin/php8.3" QP_NODE_BINS=" " qp scan --only php --json --offline --path "$T/empty" >"$J" 2>/dev/null
el=$((SECONDS - start))
check "TC-SCAN-005 probe stopped after ~10 s (took ${el}s)" test "$el" -ge 9 -a "$el" -le 20
hang='[r for r in d["result"]["runtimes"] if r["bin"].endswith("php-hang/bin/php")][0]'
assert_eq "TC-SCAN-005 hung runtime state unknown" "$(json_get "$J" "${hang}[\"state\"]")" unknown
assert_eq "TC-SCAN-005 ERR-SCN-422-01 in errors[]" "$(json_get "$J" '[e["code"] for e in d["errors"]]')" "['ERR-SCN-422-01']"
assert_eq "TC-SCAN-005 other runtime complete" "$(json_get "$J" "[r['version'] for r in d['result']['runtimes'] if r['bin'].endswith('php8.3')]")" "['8.3.6']"

# --- TC-SCAN-006: duplicates through symlinks, php-config ignored -----------
mkdir -p "$T/etc/alternatives" "$T/bin"
ln -sf "$T/usr/bin/php8.3" "$T/etc/alternatives/php"; ln -sf "$T/etc/alternatives/php" "$T/bin/php"
printf '#!/bin/sh\necho 8.3.6\n' >"$T/usr/bin/php-config8.3"; chmod +x "$T/usr/bin/php-config8.3"
QP_PHP_BINS="$T/bin/php $T/usr/bin/php8.3 $T/usr/bin/php-config8.3" QP_NODE_BINS=" " qp scan --only php --json --offline --path "$T/empty" >"$J" 2>/dev/null
assert_eq "TC-SCAN-006 exactly 1 runtime" "$(json_get "$J" '[r["bin"] for r in d["result"]["runtimes"]]')" "['$T/usr/bin/php8.3']"
assert_eq "TC-SCAN-006 runtime_id = php:+sha1(path)[:12]" "$(json_get "$J" 'd["result"]["runtimes"][0]["runtime_id"]')" "php:$(printf '%s' "$T/usr/bin/php8.3" | sha1sum | cut -c1-12)"

# --- TC-SCAN-007: project with 4 kinds and 2 running containers -------------
S=$T/var/www/shop.test; mkdir -p "$S/wp-includes"
echo '{"packages":[]}' >"$S/composer.lock"; echo '{"packages":{}}' >"$S/package-lock.json"
printf '<?php\n$wp_version = '"'"'7.0.2'"'"';\n' >"$S/wp-includes/version.php"; echo 'FROM php:8.2.34-fpm' >"$S/Dockerfile"
chown -R nobody "$S"
stub docker '
case "$1" in
  info) exit 0 ;;
  ps) printf "c1 web-php php:8.2.34-fpm\nc2 web-node node:24.22.1\n" ;;
  exec) id=$2; shift 2; case "$id:$*" in c1:*PHP_VERSION*) printf 8.2.34 ;; c2:*node*) echo v24.22.1 ;; *) exit 1 ;; esac ;;
  inspect) case "$*" in *project*) echo shop ;; *service*) echo "web-${4:-x}" ;; esac ;;
esac'
QP_PHP_BINS=" " QP_NODE_BINS=" " qp scan --json --offline --only docker,composer --path "$T/var/www" >"$J" 2>/dev/null
pr='d["result"]["projects"][0]'
assert_eq "TC-SCAN-007 1 project" "$(json_get "$J" 'len(d["result"]["projects"])')" 1
assert_eq "TC-SCAN-007 project_id = sha1(dir)[:12]" "$(json_get "$J" "${pr}[\"project_id\"]")" "$(printf '%s' "$S" | sha1sum | cut -c1-12)"
assert_eq "TC-SCAN-007 owner" "$(json_get "$J" "${pr}[\"owner\"]")" nobody
assert_eq "TC-SCAN-007 kinds" "$(json_get "$J" "sorted(${pr}['kinds'])")" "['composer', 'docker', 'npm', 'wordpress']"
assert_eq "TC-SCAN-007 2 containers with versions" "$(json_get "$J" '[(c["name"], c["php_version"], c["node_version"]) for c in d["result"]["containers"]]')" \
  "[('web-php', '8.2.34', None), ('web-node', None, '24.22.1')]"
assert_eq "TC-SCAN-007 compose labels read" "$(json_get "$J" 'd["result"]["containers"][0]["compose_project"]')" shop
check "TC-SCAN-007 output valid against schema" schema_ok "$J"

# --- TC-SCAN-008: --path without value --------------------------------------
qp scan --path >"$T/o.txt" 2>&1; rc=$?
assert_eq "TC-SCAN-008 exit 2" "$rc" 2
check "TC-SCAN-008 usage printed" grep -q '^Usage:' "$T/o.txt"
qp scan --json --path >"$J" 2>/dev/null
assert_eq "TC-SCAN-008 --json: ERR-CLI-400-01" "$(json_get "$J" 'd["errors"][0]["code"]')" ERR-CLI-400-01

# --- TC-SCAN-009: depth 7, excluded dirs, symlinks, hanging container --------
R=$T/deep; mkdir -p "$R/a/b/c/d/e/f/g" "$R/app/node_modules/x" "$T/outside/proj"
echo '{}' >"$R/a/b/c/d/e/f/composer.lock"; echo '{}' >"$R/a/b/c/d/e/f/g/composer.lock"
echo '{}' >"$R/app/node_modules/x/package-lock.json"; echo '{}' >"$T/outside/proj/composer.lock"; ln -s "$T/outside" "$R/link"
stub docker '
case "$1" in info) exit 0 ;; ps) echo "c9 stuck php:8.2" ;; exec) sleep 60 ;; inspect) echo "" ;; esac'
start=$SECONDS
QP_PHP_BINS=" " QP_NODE_BINS=" " qp scan --json --offline --only docker,composer --path "$R" >"$J" 2>/dev/null
el=$((SECONDS - start))
assert_eq "TC-SCAN-009 only the depth-7 lockfile" "$(json_get "$J" '[p["dir"] for p in d["result"]["projects"]]')" "['$R/a/b/c/d/e/f']"
assert_eq "TC-SCAN-009 hanging container: empty php_version" "$(json_get "$J" 'd["result"]["containers"][0]["php_version"]')" None
check "TC-SCAN-009 hanging container: ERR-SCN-422-01 warning" grep -q 'ERR-SCN-422-01' "$J"
check "TC-SCAN-009 each container probe stops after 10 s (took ${el}s)" test "$el" -le 25

# --- TC-SCAN-010: PHP file in WordPress uploads ------------------------------
B=$T/var/www/blog.test; mkdir -p "$B/wp-includes" "$B/wp-content/uploads/2026/10"
printf '<?php\n$wp_version = '"'"'7.0.7'"'"';\n' >"$B/wp-includes/version.php"
head -c 1024 /dev/zero | tr '\0' 'a' >"$B/wp-content/uploads/2026/10/x.php"
before=$(stat -c '%Y %a %s' "$B/wp-content/uploads/2026/10/x.php"; sha256sum "$B/wp-content/uploads/2026/10/x.php")
QP_PHP_BINS=" " QP_NODE_BINS=" " qp scan --only webshell --json --offline --path "$B" >"$J" 2>/dev/null; rc=$?
w='d["result"]["webshell_findings"][0]'
assert_eq "TC-SCAN-010 finding path/rule/size" "$(json_get "$J" "(${w}['path'], ${w}['rule'], ${w}['size'])")" "('$B/wp-content/uploads/2026/10/x.php', 'php_in_uploads', 1024)"
assert_eq "TC-SCAN-010 sha256 is 64 hex" "$(json_get "$J" "${w}['sha256']")" "$(sha256sum "$B/wp-content/uploads/2026/10/x.php" | cut -c1-64)"
assert_eq "TC-SCAN-010 exactly 1 critical issue" "$(json_get "$J" '[i["severity"] for i in d["issues"]]')" "['critical']"
assert_eq "TC-SCAN-010 exit 1" "$rc" 1
assert_eq "TC-SCAN-010 file untouched" "$(stat -c '%Y %a %s' "$B/wp-content/uploads/2026/10/x.php"; sha256sum "$B/wp-content/uploads/2026/10/x.php")" "$before"

# --- TC-SCAN-012: size limit and 50 results per group ------------------------
M=$T/mass; mkdir -p "$M"; echo '{}' >"$M/composer.lock"
for i in $(seq 1 60); do echo '<?php eval(base64_decode($_POST["x"]));' >"$M/s$i.php"; done
{ echo '<?php eval(base64_decode($_POST["x"]));'; head -c 2097152 /dev/zero | tr '\0' ' '; } | head -c 2097152 >"$M/big.php"
QP_PHP_BINS=" " QP_NODE_BINS=" " qp fix --only webshell --json --offline --path "$M" >"$J" 2>/dev/null
assert_eq "TC-SCAN-012 2 MiB file not read" "$(json_get "$J" 'any(f["path"].endswith("big.php") for f in d["result"].get("webshell_findings", []))')" False
n=$(json_get "$J" 'd["result"]["actions"]')
QP_PHP_BINS=" " QP_NODE_BINS=" " qp scan --only webshell --json --offline --path "$M" >"$J" 2>/dev/null
assert_eq "TC-SCAN-012 at most 50 findings for the pattern group" "$(json_get "$J" 'len(d["result"]["webshell_findings"])')" 50
assert_eq "TC-SCAN-012 rule of a pattern hit" "$(json_get "$J" 'd["result"]["webshell_findings"][0]["rule"]')" eval_decode
assert_eq "TC-SCAN-012 fix writes no manifest line for webshells" "$n" "[]"
check "TC-SCAN-012 no backup run created" test ! -d /var/lib/php-quickpatch/backups

t_done
