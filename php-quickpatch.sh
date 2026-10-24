#!/usr/bin/env bash
# php-quickpatch: detect, audit and auto-patch PHP and Node.js stacks on
# plain VPS hosts, hosting panels (cPanel, Plesk, aaPanel, CyberPanel,
# DirectAdmin) and Docker hosts or containers.
#
# Usage: php-quickpatch.sh [scan|fix|rollback [ID]] [options]   (see --help)
set -uo pipefail

QP_VERSION="0.1.1"

# --- Advisory data: bump these when a new security release ships ----------
# Lowest patched release per PHP branch (PHP2Shell, 2026-10-21).
PHP_FIXED=(8.2.35 8.3.36 8.4.27 8.5.12)
PHP_CVES=(CVE-2026-109618 CVE-2026-109619)
# Lowest patched release per Node.js line (security release 2026-10-21).
NODE_FIXED=(22.23.4 24.22.1 26.12.1)
# WordPress core "wp2shell" (CVE-2026-63030, CVE-2026-60137).
WP_FIXED=(6.9.5 7.0.2)

PHP_RELEASES_URL="https://www.php.net/releases/index.php?json&version="
NODE_BASE_URL="https://nodejs.org/dist"
OSV_BATCH_URL="https://api.osv.dev/v1/querybatch"
COMPOSER_PHAR_URL="https://getcomposer.org/download/latest-stable/composer.phar"
WPCLI_PHAR_URL="https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"

# --- Options --------------------------------------------------------------
MODE=scan
ROLLBACK_ID=""
DRY_RUN=0
NO_RESTART=0
OFFLINE=0
NO_MEMLIMIT=0
ONLY="php,node,composer,npm,wp,docker,webshell"
SCAN_PATHS=()

# --- State ----------------------------------------------------------------
IS_ROOT=0; (( EUID == 0 )) && IS_ROOT=1
IN_CONTAINER=0; PANEL=none; PKG_MGR=none; HAS_SYSTEMD=0; HAS_DOCKER=0
STATE_DIR=""; LOG=""; BACKUP_DIR=""; WORK_DIR=""
RESTART_PHP=0; RESTART_NODE_PREFIXES=(); APT_UPDATED=0
ISSUES=0; FIXED=0; CRITICAL=0
SUMMARY=()

if [ -t 1 ]; then C_R=$'\e[31m'; C_G=$'\e[32m'; C_Y=$'\e[33m'; C_B=$'\e[1m'; C_0=$'\e[0m'
else C_R=""; C_G=""; C_Y=""; C_B=""; C_0=""; fi

log()  { [ -n "$LOG" ] && printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; return 0; }
say()  { printf '%s\n' "$*"; log "$*"; }
head_() { say ""; say "${C_B}== $* ==${C_0}"; }
ok()   { say "  ${C_G}[OK]${C_0} $*"; }
warn() { say "  ${C_Y}[WARN]${C_0} $*"; }
bad()  { say "  ${C_R}[VULN]${C_0} $*"; }
note() { say "  [i] $*"; }

# Record an unresolved finding (severity: high|critical) for the summary.
issue() {
  local sev=$1; shift
  ISSUES=$((ISSUES + 1)); [ "$sev" = critical ] && CRITICAL=$((CRITICAL + 1))
  SUMMARY+=("${sev^^}: $*")
}
fixed() { FIXED=$((FIXED + 1)); SUMMARY+=("FIXED: $*"); }

usage() {
  cat <<'EOF'
php-quickpatch: detect, audit and auto-patch PHP and Node.js stacks.

Usage:
  php-quickpatch.sh scan     [options]   audit only, change nothing (default)
  php-quickpatch.sh fix      [options]   audit, then apply every safe fix
  php-quickpatch.sh rollback [ID]        undo file changes of a fix run
                                          (latest run when ID is omitted)
Options:
  --path DIR        project/web root to scan (repeatable). Default: common
                    web roots (/var/www, /home, /srv, /www/wwwroot, ...)
  --only LIST       comma list of: php,node,composer,npm,wp,docker,webshell
  --dry-run         with fix or rollback: print what would change, change nothing
  --no-restart      do not restart PHP-FPM/web server/Node services/containers
  --no-memlimit     skip the memory_limit=-1 interim mitigation
  --offline         no network lookups (no OSV, no release feeds, no downloads)
  -h, --help        this help;  --version  print version

Exit status: 0 nothing left to fix, 1 issues remain, 2 usage or runtime error.
Run as root for system-level fixes; without root only project-level fixes
(Composer, npm, WordPress) are applied.
EOF
}

# --- Small helpers --------------------------------------------------------
has() { command -v "$1" >/dev/null 2>&1; }

# ver_lt A B: true when version A sorts before version B.
ver_lt() { [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]; }

# fixed_for PREFIX LIST...: print the entry of LIST that starts with "PREFIX."
fixed_for() {
  local prefix=$1 f; shift
  for f in "$@"; do [[ $f == "$prefix".* ]] && { echo "$f"; return 0; }; done
  return 1
}

# run CMD...: execute (or print in dry-run), output goes to the log.
run() {
  if (( DRY_RUN )); then say "    [dry-run] $*"; return 0; fi
  log "+ $*"
  "$@" >>"$LOG" 2>&1
}

# run_in_dir_as_owner DIR CMD...: run CMD in DIR as the owner of DIR so
# project files never end up owned by root.
run_in_dir_as_owner() {
  local dir=$1; shift
  local owner home
  owner=$(stat -c %U "$dir" 2>/dev/null || echo root)
  if (( IS_ROOT )) && [ "$owner" != root ] && has runuser; then
    home=$(getent passwd "$owner" | cut -d: -f6)
    (cd "$dir" && run runuser -u "$owner" -- env HOME="${home:-/tmp}" "$@")
  else
    (cd "$dir" && run "$@")
  fi
}

fetch() { # fetch URL [OUTFILE]
  (( OFFLINE )) && return 1
  if [ $# -ge 2 ]; then curl -fsSL --max-time 120 -o "$2" "$1"; else curl -fsSL --max-time 30 "$1"; fi
}

ensure_backup_dir() {
  [ -n "$BACKUP_DIR" ] && return 0
  BACKUP_DIR="$STATE_DIR/backups/$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP_DIR/files" && : >"$BACKUP_DIR/manifest"
  say "  [i] Backups for this run: $BACKUP_DIR"
}

backup_file() { # backup_file PATH: copy PATH into the run's backup dir
  local f=$1 dest
  (( DRY_RUN )) && return 0
  [ -e "$f" ] || return 0
  ensure_backup_dir
  dest="$BACKUP_DIR/files$(readlink -f "$f")"
  mkdir -p "${dest%/*}" && cp -a "$f" "$dest" && printf 'copy\t%s\t%s\n' "$(readlink -f "$f")" "$dest" >>"$BACKUP_DIR/manifest"
}

record() { # record ACTION ARG...: append a rollback step to the manifest
  (( DRY_RUN )) && return 0
  ensure_backup_dir
  local IFS=$'\t'; printf '%s\n' "$*" >>"$BACKUP_DIR/manifest"
}

# Which package owns FILE: prints "MANAGER PACKAGE" or nothing.
pkg_owner() {
  local f p; f=$(readlink -f "$1")
  if has dpkg-query && p=$(dpkg -S "$f" 2>/dev/null | head -n1 | cut -d: -f1) && [ -n "$p" ]; then
    echo "dpkg $p"
  elif has rpm && p=$(rpm -qf --qf '%{NAME}\n' "$f" 2>/dev/null | head -n1) && [ -n "$p" ] && [[ $p != *"not owned"* ]]; then
    echo "rpm $p"
  elif has apk && p=$(apk info --who-owns "$f" 2>/dev/null | awk '{print $NF}') && [ -n "$p" ]; then
    echo "apk ${p%-[0-9]*}"
  fi
}

# Does the installed package's changelog mention every CVE in the list?
pkg_has_cves() { # pkg_has_cves MANAGER PACKAGE CVE...
  local mgr=$1 pkg=$2 text="" cve; shift 2
  case $mgr in
    dpkg)
      local src; src=$(dpkg-query -W -f='${source:Package}' "$pkg" 2>/dev/null)
      local f
      for f in /usr/share/doc/"$pkg"/changelog.Debian.gz /usr/share/doc/"${src:-$pkg}"/changelog.Debian.gz; do
        [ -f "$f" ] && { text=$(zcat "$f" 2>/dev/null); break; }
      done ;;
    rpm) text=$(rpm -q --changelog "$pkg" 2>/dev/null) ;;
    *) return 1 ;;
  esac
  [ -n "$text" ] || return 1
  for cve in "$@"; do grep -q "$cve" <<<"$text" || return 1; done
}

# --- JSON helpers (php, node or jq, whichever exists) ---------------------
json_tool() {
  if has php; then echo php; elif has node; then echo node; elif has jq; then echo jq; else return 1; fi
}

# deps_of LOCKFILE: print "name version" for every locked package.
deps_of() {
  local file=$1 tool; tool=$(json_tool) || return 1
  case "${file##*/}:$tool" in
    composer.lock:php)
      php -r '$j=json_decode(file_get_contents($argv[1]),true);
        foreach(array_merge($j["packages"]??[],$j["packages-dev"]??[]) as $p)
          echo $p["name"]," ",ltrim($p["version"],"v"),"\n";' "$file" ;;
    composer.lock:node)
      node -e 'const j=require(process.argv[1]);
        for(const p of [...(j.packages||[]),...(j["packages-dev"]||[])])
          console.log(p.name+" "+p.version.replace(/^v/,""))' "$file" ;;
    composer.lock:jq)
      jq -r '(.packages // []) + (."packages-dev" // []) | .[] | "\(.name) \(.version|ltrimstr("v"))"' "$file" ;;
    package-lock.json:php)
      php -r '$j=json_decode(file_get_contents($argv[1]),true);
        $walk=function($deps)use(&$walk){foreach($deps as $n=>$d){if(isset($d["version"]))echo $n," ",$d["version"],"\n";$walk($d["dependencies"]??[]);}};
        if(isset($j["packages"])){foreach($j["packages"] as $k=>$p){if($k===""||empty($p["version"])||!empty($p["link"]))continue;
          $n=substr($k,strrpos($k,"node_modules/")+13);echo $n," ",$p["version"],"\n";}}
        else $walk($j["dependencies"]??[]);' "$file" ;;
    package-lock.json:node)
      node -e 'const j=require(process.argv[1]);
        const walk=d=>{for(const[n,v]of Object.entries(d||{})){if(v.version)console.log(n+" "+v.version);walk(v.dependencies)}};
        if(j.packages){for(const[k,p]of Object.entries(j.packages)){if(!k||!p.version||p.link)continue;
          console.log(k.slice(k.lastIndexOf("node_modules/")+13)+" "+p.version)}}else walk(j.dependencies)' "$file" ;;
    package-lock.json:jq)
      jq -r 'if .packages then .packages | to_entries[] | select(.key != "" and .value.version and (.value.link|not))
               | "\(.key | sub(".*node_modules/"; "")) \(.value.version)"
             else [.dependencies | .. | objects | select(.version)] | empty end' "$file" ;;
  esac | sort -u
}

# osv_check ECOSYSTEM < "name version" lines: print "name version ID,ID" for
# every package that has at least one OSV advisory (MAL-* means malware).
osv_check() {
  local eco=$1 tool lines chunk payload resp i
  tool=$(json_tool) || return 1
  mapfile -t lines
  for ((i = 0; i < ${#lines[@]}; i += 500)); do
    chunk=("${lines[@]:i:500}")
    payload=$(printf '%s\n' "${chunk[@]}" | awk -v eco="$eco" '
      function esc(s){gsub(/\\/,"\\\\",s);gsub(/"/,"\\\"",s);return s}
      BEGIN{printf "{\"queries\":["} NF==2{printf "%s{\"package\":{\"name\":\"%s\",\"ecosystem\":\"%s\"},\"version\":\"%s\"}", (n++?",":""), esc($1), eco, esc($2)} END{printf "]}"}')
    resp=$(curl -fsS --max-time 60 -H 'Content-Type: application/json' -d "$payload" "$OSV_BATCH_URL") || return 1
    case $tool in
      php)  php -r '$r=json_decode(stream_get_contents(STDIN),true);foreach($r["results"]??[] as $x){echo implode(",",array_column($x["vulns"]??[],"id")),"\n";}' <<<"$resp" ;;
      node) node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{for(const x of JSON.parse(s).results||[])console.log((x.vulns||[]).map(v=>v.id).join(","))})' <<<"$resp" ;;
      jq)   jq -r '.results[] | [(.vulns // [])[].id] | join(",")' <<<"$resp" ;;
    esac | paste -d' ' <(printf '%s\n' "${chunk[@]}") - | awk 'NF==3'
  done
}

# --- Environment detection ------------------------------------------------
detect_env() {
  head_ "Environment"
  if [ -f /.dockerenv ] || grep -qsE '(docker|containerd|kubepods|libpod)' /proc/1/cgroup; then IN_CONTAINER=1; fi
  if   [ -x /usr/local/cpanel/cpanel ]; then PANEL=cpanel
  elif [ -d /usr/local/psa ]; then PANEL=plesk
  elif [ -d /www/server/panel ]; then PANEL=aapanel
  elif [ -d /usr/local/CyberCP ]; then PANEL=cyberpanel
  elif [ -d /usr/local/directadmin ]; then PANEL=directadmin
  fi
  if   has apt-get; then PKG_MGR=apt
  elif has dnf; then PKG_MGR=dnf
  elif has yum; then PKG_MGR=yum
  elif has apk; then PKG_MGR=apk
  fi
  [ -d /run/systemd/system ] && HAS_SYSTEMD=1
  if has docker && docker info >/dev/null 2>&1; then HAS_DOCKER=1; fi

  local os="unknown"; [ -r /etc/os-release ] && os=$(. /etc/os-release && echo "${PRETTY_NAME:-$ID}")
  note "OS: $os | package manager: $PKG_MGR | panel: $PANEL"
  note "inside container: $([ $IN_CONTAINER = 1 ] && echo yes || echo no) | docker daemon: $([ $HAS_DOCKER = 1 ] && echo yes || echo no) | systemd: $([ $HAS_SYSTEMD = 1 ] && echo yes || echo no) | root: $([ $IS_ROOT = 1 ] && echo yes || echo no)"
  (( IS_ROOT )) || warn "Not root: PHP/Node runtime upgrades and server config are skipped (shared hosting mode)."
  (( IN_CONTAINER )) && warn "Running inside a container: runtime fixes are lost when it is recreated; rebuild the image too."
}

# --- PHP runtimes ---------------------------------------------------------
discover_php_bins() {
  local c
  if [ -n "${QP_PHP_BINS:-}" ]; then printf '%s\n' $QP_PHP_BINS; return; fi
  {
    has php && command -v php
    for c in /usr/bin/php[0-9]* /usr/local/bin/php /opt/cpanel/ea-php*/root/usr/bin/php \
             /opt/alt/php*/usr/bin/php /opt/remi/php*/root/usr/bin/php /opt/plesk/php/*/bin/php \
             /www/server/php/*/bin/php /usr/local/lsws/lsphp*/bin/php /usr/local/php*/bin/php; do
      [ -x "$c" ] && echo "$c"
    done
  } | while read -r c; do readlink -f "$c"; done | grep -v -- '-config$' | sort -u
}

php_version() { local v; v=$("$1" -n -r 'echo PHP_VERSION;' 2>/dev/null) || return 1; echo "${v%%[^0-9.]*}"; }

# php_state BIN -> prints one of: ok | ok-backport | vulnerable | eol | unknown
php_state() {
  local bin=$1 v branch fix owner newest
  v=$(php_version "$bin") || { echo unknown; return; }
  branch=${v%.*}
  newest=${PHP_FIXED[-1]%.*}
  if fix=$(fixed_for "$branch" "${PHP_FIXED[@]}"); then
    ver_lt "$v" "$fix" || { echo ok; return; }
  elif ver_lt "$newest" "$branch"; then
    echo unknown; return
  fi
  owner=$(pkg_owner "$bin")
  if [ -n "$owner" ] && pkg_has_cves $owner "${PHP_CVES[@]}"; then echo ok-backport; return; fi
  if fixed_for "$branch" "${PHP_FIXED[@]}" >/dev/null; then echo vulnerable; else echo eol; fi
}

php_sapis_note() {
  local s=""
  if [ -d /etc/apache2/mods-enabled ] && ls /etc/apache2/mods-enabled/php*.load >/dev/null 2>&1; then s+=" mod_php(apache2)"; fi
  if has httpd && httpd -M 2>/dev/null | grep -q php; then s+=" mod_php(httpd)"; fi
  [ -n "$s" ] && warn "Apache mod_php detected:$s. PHP2Shell is easiest to exploit there; prefer PHP-FPM."
}

# Install all newer packages of the PHP build that owns BIN.
php_upgrade() {
  local bin=$1 mgr pkg glob pkgs
  read -r mgr pkg <<<"$(pkg_owner "$bin")"
  if [ -z "${mgr:-}" ]; then
    warn "$bin is not from a package (source build or panel build). Upgrade it in the panel or rebuild it; applying interim mitigation."
    return 1
  fi
  case $mgr in
    dpkg)
      if [[ $pkg =~ ^(php[0-9.]+|lsphp[0-9]+|plesk-php[0-9]+) ]]; then glob=${BASH_REMATCH[1]}; else glob=php; fi
      mapfile -t pkgs < <(dpkg-query -W -f='${db:Status-Abbrev} ${binary:Package}\n' "${glob}*" 2>/dev/null | awk '$1 ~ /^ii/ {print $2}')
      [ ${#pkgs[@]} -gt 0 ] || return 1
      if (( ! APT_UPDATED )); then run apt-get update -q && APT_UPDATED=1; fi
      record note "apt upgraded: ${pkgs[*]} (packages are not downgraded by rollback)"
      run env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade \
          -o Dpkg::Options::=--force-confold "${pkgs[@]}" ;;
    rpm)
      if [[ $pkg =~ ^(ea-php[0-9]+|alt-php[0-9]+|php[0-9]+|lsphp[0-9]+|plesk-php[0-9]+) ]]; then glob="${BASH_REMATCH[1]}*"; else glob='php*'; fi
      record note "rpm upgraded: $glob (packages are not downgraded by rollback)"
      if has dnf; then run dnf -y -q upgrade "$glob"; else run yum -y -q update "$glob"; fi ;;
    apk)
      [[ $pkg =~ ^(php[0-9]*) ]] && glob=${BASH_REMATCH[1]} || glob=php
      record note "apk upgraded: ${glob}* (packages are not downgraded by rollback)"
      mapfile -t pkgs < <(apk info 2>/dev/null | grep "^${glob}")
      run apk upgrade --no-cache "${pkgs[@]}" ;;
  esac
}

# The conf.d directories that BIN and its sibling SAPIs read.
php_scan_dirs() {
  local bin=$1 d
  d=$("$bin" --ini 2>/dev/null | sed -n 's/^Scan for additional .ini files in: *//p')
  [ -z "$d" ] || [ "$d" = "(none)" ] && return 1
  if [[ $d =~ ^(/etc/php/[0-9.]+)/[^/]+/conf\.d$ ]]; then
    ls -d "${BASH_REMATCH[1]}"/*/conf.d 2>/dev/null
  else
    tr ':' '\n' <<<"$d"
  fi
}

PHP_MITIGATION_FILE=zz-php-quickpatch-mitigation.ini

php_mitigation_ini() { # php_mitigation_ini VERSION
  echo "; Added by php-quickpatch $(date +%F): interim PHP2Shell mitigation"
  echo "; (${PHP_CVES[*]}). It only reduces exposure. Upgrade PHP, then delete this file."
  echo "session.upload_progress.enabled = 0"
  (( NO_MEMLIMIT )) || echo "memory_limit = -1"
  [[ $1 == 8.5.* ]] && echo "fatal_error_backtraces = 0"
  return 0
}

php_mitigate() {
  local bin=$1 v d f
  v=$(php_version "$bin")
  local dirs; dirs=$(php_scan_dirs "$bin") || { warn "No conf.d scan dir for $bin; set the mitigation in its php.ini by hand."; return 1; }
  while read -r d; do
    [ -d "$d" ] || continue
    f="$d/$PHP_MITIGATION_FILE"
    if [ -f "$f" ]; then note "mitigation already present: $f"; continue; fi
    if (( DRY_RUN )); then say "    [dry-run] write $f"; continue; fi
    php_mitigation_ini "$v" >"$f" && record created "$f" && note "wrote $f"
  done <<<"$dirs"
  (( NO_MEMLIMIT )) || note "memory_limit=-1 removes PHP's memory cap; apps calling ini_set('memory_limit') can still override it."
  RESTART_PHP=1
}

# Remove the interim mitigation once a runtime is patched.
php_unmitigate() {
  local bin=$1 d dirs
  dirs=$(php_scan_dirs "$bin") || return 0
  while read -r d; do
    [ -f "$d/$PHP_MITIGATION_FILE" ] || continue
    backup_file "$d/$PHP_MITIGATION_FILE"
    run rm -f "$d/$PHP_MITIGATION_FILE" && note "removed obsolete $d/$PHP_MITIGATION_FILE" && RESTART_PHP=1
  done <<<"$dirs"
}

check_php() {
  head_ "PHP runtimes"
  local bins bin v st label
  mapfile -t bins < <(discover_php_bins)
  if [ ${#bins[@]} -eq 0 ]; then note "No PHP binary found."; return; fi
  php_sapis_note
  for bin in "${bins[@]}"; do
    v=$(php_version "$bin") || continue
    st=$(php_state "$bin"); label="PHP $v ($bin)"
    case $st in
      ok)          ok "$label is patched."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      ok-backport) ok "$label has the vendor backport for ${PHP_CVES[*]}."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      unknown)     warn "$label: newer than the advisory data, not checked." ;;
      vulnerable|eol)
        if [ "$st" = eol ]; then bad "$label is end-of-life upstream and has no ${PHP_CVES[*]} fix."
        else bad "$label is vulnerable to ${PHP_CVES[*]} (fixed in $(fixed_for "${v%.*}" "${PHP_FIXED[@]}"))."; fi
        if [ "$MODE" != fix ]; then issue critical "$label: PHP2Shell RCE"; continue; fi
        if (( ! IS_ROOT )); then issue critical "$label: needs root (or the hosting panel) to upgrade"; continue; fi
        if php_upgrade "$bin" && (( ! DRY_RUN )); then
          st=$(php_state "$bin"); v=$(php_version "$bin")
          if [[ $st == ok* ]]; then
            local pv; pv=$(read -r m p <<<"$(pkg_owner "$bin")"; [ "${m:-}" = dpkg ] && dpkg-query -W -f=' (package ${Version})' "$p"; [ "${m:-}" = rpm ] && rpm -q --qf ' (package %{VERSION}-%{RELEASE})' "$p")
            ok "PHP $v$pv now has the fix ($st)"; fixed "PHP runtime $bin -> $v$pv"; RESTART_PHP=1; php_unmitigate "$bin"; continue
          fi
          warn "package upgrade did not bring a fixed PHP (still $v)."
        fi
        php_mitigate "$bin"
        issue critical "$label: still unpatched, interim mitigation applied. Move to a supported branch (>= ${PHP_FIXED[0]%.*}) or a vendor backport."
        ;;
    esac
  done
}

# --- Node.js runtimes -----------------------------------------------------
discover_node_bins() {
  local c
  if [ -n "${QP_NODE_BINS:-}" ]; then printf '%s\n' $QP_NODE_BINS; return; fi
  {
    has node && command -v node
    for c in /usr/bin/node /usr/local/bin/node /opt/*/bin/node /www/server/nodejs/*/bin/node \
             /root/.nvm/versions/node/*/bin/node /home/*/.nvm/versions/node/*/bin/node; do
      [ -x "$c" ] && echo "$c"
    done
  } | while read -r c; do readlink -f "$c"; done | sort -u
}

node_state() { # node_state VERSION -> ok | vulnerable | eol | unknown
  local v=$1 major=${1%%.*} fix
  if fix=$(fixed_for "$major" "${NODE_FIXED[@]}"); then
    ver_lt "$v" "$fix" && echo vulnerable || echo ok
  elif (( major < ${NODE_FIXED[-1]%%.*} )); then echo eol
  else echo unknown; fi
}

node_latest() { # node_latest MAJOR: newest release of that line, online
  fetch "$NODE_BASE_URL/index.json" | grep -o "\"version\":\"v$1\\.[0-9.]*\"" | head -n1 | grep -o '[0-9][0-9.]*'
}

# Replace a tarball-style Node install (PREFIX/bin/node) with the newest
# release of the same major, verified against SHASUMS256.txt.
node_upgrade_prefix() {
  local prefix=$1 major=$2 ver arch tarball sums
  ver=$(node_latest "$major") || ver=$(fixed_for "$major" "${NODE_FIXED[@]}") || return 1
  case $(uname -m) in x86_64) arch=x64 ;; aarch64) arch=arm64 ;; armv7l) arch=armv7l ;; ppc64le) arch=ppc64le ;; s390x) arch=s390x ;; *) return 1 ;; esac
  tarball="node-v$ver-linux-$arch.tar.xz"
  if (( DRY_RUN )); then say "    [dry-run] install $tarball into $prefix"; return 0; fi
  fetch "$NODE_BASE_URL/v$ver/$tarball" "$WORK_DIR/$tarball" || { warn "download of $tarball failed"; return 1; }
  sums=$(fetch "$NODE_BASE_URL/v$ver/SHASUMS256.txt") || return 1
  (cd "$WORK_DIR" && grep " $tarball\$" <<<"$sums" | sha256sum -c --status) || { warn "checksum mismatch for $tarball"; return 1; }
  ensure_backup_dir
  local saved parts=()
  saved="$BACKUP_DIR/node-$(echo "$prefix" | tr / _).tar.gz"
  local p; for p in bin include lib/node_modules/npm lib/node_modules/corepack share/doc/node; do [ -e "$prefix/$p" ] && parts+=("$p"); done
  tar -czf "$saved" -C "$prefix" "${parts[@]}" && record untar "$saved" "$prefix"
  run tar -xJf "$WORK_DIR/$tarball" -C "$prefix" --strip-components=1 --no-same-owner
}

node_upgrade() { # node_upgrade BIN MAJOR
  local bin=$1 major=$2 mgr pkg
  read -r mgr pkg <<<"$(pkg_owner "$bin")"
  case ${mgr:-} in
    dpkg)
      if (( ! APT_UPDATED )); then run apt-get update -q && APT_UPDATED=1; fi
      record note "apt upgraded: $pkg (not downgraded by rollback)"
      run env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade "$pkg" ;;
    rpm)
      record note "rpm upgraded: $pkg (not downgraded by rollback)"
      if has dnf; then run dnf -y -q upgrade "$pkg"; else run yum -y -q update "$pkg"; fi ;;
    apk) run apk upgrade --no-cache "$pkg" ;;
    *)
      if [[ $bin == */.nvm/versions/node/* ]]; then
        warn "nvm install: run 'nvm install $major && nvm alias default $major' as its owner, then restart the app."
        return 1
      fi
      local prefix=${bin%/bin/node}
      [ -d "$prefix/lib/node_modules/npm" ] || { warn "unrecognised Node install at $bin"; return 1; }
      node_upgrade_prefix "$prefix" "$major" || return 1 ;;
  esac
  RESTART_NODE_PREFIXES+=("${bin%/bin/node}")
}

check_node() {
  head_ "Node.js runtimes"
  local bins bin v st label major
  mapfile -t bins < <(discover_node_bins)
  if [ ${#bins[@]} -eq 0 ]; then note "No Node.js binary found."; return; fi
  for bin in "${bins[@]}"; do
    v=$("$bin" -v 2>/dev/null) || continue
    v=${v#v}; major=${v%%.*}; st=$(node_state "$v"); label="Node.js $v ($bin)"
    case $st in
      ok) ok "$label is patched." ;;
      unknown) warn "$label: newer than the advisory data, not checked." ;;
      eol) bad "$label is end-of-life and gets no security fixes."
           issue high "$label: end-of-life, move to Node ${NODE_FIXED[-2]%%.*} or ${NODE_FIXED[-1]%%.*} LTS" ;;
      vulnerable)
        bad "$label is below the October 2026 security release ($(fixed_for "$major" "${NODE_FIXED[@]}"))."
        if [ "$MODE" != fix ]; then issue high "$label: unpatched"; continue; fi
        if (( ! IS_ROOT )) && [[ $bin != "$HOME"/* ]]; then issue high "$label: needs root to upgrade"; continue; fi
        if node_upgrade "$bin" "$major" && (( ! DRY_RUN )); then
          v=$("$bin" -v); v=${v#v}
          if [ "$(node_state "$v")" = ok ]; then ok "upgraded to Node.js $v"; fixed "Node.js $bin -> $v"; continue; fi
        fi
        (( DRY_RUN )) || issue high "$label: upgrade failed, see $LOG" ;;
    esac
  done
}

# --- Projects (Composer, npm, WordPress, Dockerfiles) ---------------------
PROJECT_FILES=()

discover_projects() {
  local roots=() r
  if [ ${#SCAN_PATHS[@]} -gt 0 ]; then roots=("${SCAN_PATHS[@]}")
  else for r in /var/www /srv /home /www/wwwroot /usr/share/nginx/html /usr/local/lsws/Example/html; do [ -d "$r" ] && roots+=("$r"); done; fi
  [ ${#roots[@]} -gt 0 ] || return 0
  mapfile -t PROJECT_FILES < <(find "${roots[@]}" -maxdepth 7 \
      \( -name node_modules -o -name vendor -o -name .git -o -name .cache -o -name .nvm -o -name .npm -o -name .composer \) -prune -o \
      \( -name composer.lock -o -name package-lock.json -o -name yarn.lock -o -name pnpm-lock.yaml \
         -o -path '*/wp-includes/version.php' -o -name Dockerfile -o -name 'Dockerfile.*' \
         -o -name 'docker-compose.y*ml' -o -name 'compose.y*ml' \) -type f -print 2>/dev/null | sort)
}

# shellcheck disable=SC2053  # $pat is a glob on purpose
project_files() { local pat=$1 f; for f in "${PROJECT_FILES[@]}"; do [[ ${f##*/} == $pat ]] && echo "$f"; done; return 0; }

composer_cmd() {
  if has composer; then echo composer; return; fi
  has php || return 1
  local phar="$WORK_DIR/composer.phar"
  if [ ! -f "$phar" ]; then
    fetch "$COMPOSER_PHAR_URL" "$phar" || return 1
    local sum; sum=$(fetch "$COMPOSER_PHAR_URL.sha256sum" | awk '{print $1}')
    [ -n "$sum" ] && [ "$(sha256sum "$phar" | awk '{print $1}')" = "$sum" ] || { rm -f "$phar"; return 1; }
  fi
  echo "php $phar"
}

# Report and optionally fix vulnerable/malicious packages of one lockfile.
# audit_lockfile ECOSYSTEM LOCKFILE FIX_FN
audit_lockfile() {
  local eco=$1 lock=$2 fixfn=$3 dir=${2%/*} hits names mal
  if (( OFFLINE )); then warn "$lock: skipped (offline)"; return; fi
  local deps; deps=$(deps_of "$lock")
  if [ -z "$deps" ]; then warn "$lock: could not read packages (needs php, node or jq)"; return; fi
  if ! hits=$(osv_check "$eco" <<<"$deps"); then warn "$lock: OSV lookup failed (network or no php/node/jq)"; return; fi
  if [ -z "$hits" ]; then ok "$lock: no known vulnerable packages."; return; fi
  mal=$(awk '$3 ~ /(^|,)MAL-/' <<<"$hits")
  while read -r name ver ids; do bad "$dir: $name $ver -> $ids"; done <<<"$hits"
  if [ "$MODE" = fix ]; then
    names=$(awk '{print $1}' <<<"$hits" | sort -u | tr '\n' ' ')
    $fixfn "$dir" $names
    if (( ! DRY_RUN )); then
      local after; after=$(deps_of "$lock" | osv_check "$eco") || after="$hits"
      local n_before n_after
      n_before=$(grep -c . <<<"$hits"); n_after=$(grep -c . <<<"$after")
      (( n_after < n_before )) && fixed "$dir: $((n_before - n_after)) vulnerable $eco package(s) updated"
      hits=$after; mal=$(awk '$3 ~ /(^|,)MAL-/' <<<"$hits")
      [ -n "$hits" ] && while read -r name ver ids; do warn "still present: $name $ver ($ids)"; done <<<"$hits"
    fi
  fi
  if [ -n "$mal" ]; then
    issue critical "$dir: MALWARE package(s) in lockfile: $(awk '{print $1"@"$2}' <<<"$mal" | tr '\n' ' ')- remove them, rotate every secret on this host (npm/GitHub tokens, SSH keys, .env)"
  fi
  local rest; rest=$(awk '$3 !~ /(^|,)MAL-/' <<<"$hits" | grep -c .)
  if (( rest > 0 )); then
    if [ "$MODE" = fix ]; then issue high "$dir: $rest vulnerable $eco package(s) left; they need a manual major upgrade"
    else issue high "$dir: $rest vulnerable $eco package(s)"; fi
  fi
  return 0
}

fix_composer() {
  local dir=$1; shift
  local cmd; cmd=$(composer_cmd) || { warn "composer not available"; return 1; }
  record composer-install "$dir"   # replayed after the restores (manifest runs in reverse)
  backup_file "$dir/composer.json"; backup_file "$dir/composer.lock"
  if ! run_in_dir_as_owner "$dir" $cmd update "$@" --with-all-dependencies --no-interaction --no-progress; then
    warn "$dir: composer update failed, restoring composer.json/lock (see $LOG)"
    rollback_files_for "$dir/composer.json" "$dir/composer.lock"
    run_in_dir_as_owner "$dir" $cmd install --no-interaction --no-progress
    return 1
  fi
}

fix_npm() {
  local dir=$1; shift
  has npm || { warn "npm not available"; return 1; }
  record npm-ci "$dir"   # replayed after the restores (manifest runs in reverse)
  backup_file "$dir/package.json"; backup_file "$dir/package-lock.json"
  run_in_dir_as_owner "$dir" npm audit fix --no-fund \
    || warn "$dir: npm audit fix could not resolve everything (no --force used)"
}

check_composer() {
  head_ "Composer projects"
  local locks l; mapfile -t locks < <(project_files composer.lock)
  [ ${#locks[@]} -gt 0 ] || { note "No composer.lock found."; return; }
  for l in "${locks[@]}"; do audit_lockfile Packagist "$l" fix_composer; done
}

check_npm() {
  head_ "npm projects"
  local locks l; mapfile -t locks < <(project_files package-lock.json)
  for l in $(project_files yarn.lock) $(project_files pnpm-lock.yaml); do
    warn "${l%/*}: ${l##*/} is not audited; run 'yarn npm audit' / 'pnpm audit' there."
  done
  [ ${#locks[@]} -gt 0 ] || { note "No package-lock.json found."; return; }
  for l in "${locks[@]}"; do audit_lockfile npm "$l" fix_npm; done
}

wp_cmd() {
  if has wp; then echo wp; return; fi
  has php || return 1
  local phar="$WORK_DIR/wp-cli.phar"
  if [ ! -f "$phar" ]; then
    fetch "$WPCLI_PHAR_URL" "$phar" || return 1
    local sum; sum=$(fetch "$WPCLI_PHAR_URL.sha512" | awk '{print $1}')
    [ -n "$sum" ] && [ "$(sha512sum "$phar" | awk '{print $1}')" = "$sum" ] || { rm -f "$phar"; return 1; }
  fi
  echo "php $phar"
}

check_wordpress() {
  head_ "WordPress sites"
  local files f site v fix wp
  mapfile -t files < <(project_files version.php)
  [ ${#files[@]} -gt 0 ] || { note "No WordPress install found."; return; }
  for f in "${files[@]}"; do
    site=${f%/wp-includes/version.php}
    v=$(sed -n "s/^\$wp_version *= *'\([^']*\)'.*/\1/p" "$f"); [ -n "$v" ] || continue
    if fix=$(fixed_for "${v%.*}" "${WP_FIXED[@]}") && ver_lt "$v" "$fix"; then
      bad "$site: WordPress $v is vulnerable to wp2shell RCE (fixed in $fix)."
    else
      ok "$site: WordPress $v is not in the wp2shell range."
      [ "$MODE" = fix ] || continue
      fix=""
    fi
    if [ "$MODE" != fix ]; then [ -n "$fix" ] && issue critical "$site: WordPress $v wp2shell"; continue; fi
    if ! wp=$(wp_cmd); then [ -n "$fix" ] && issue critical "$site: wp-cli unavailable, update WordPress core to $fix by hand"; continue; fi
    backup_file "$f"
    run_in_dir_as_owner "$site" $wp core update --minor --path="$site" --skip-plugins --skip-themes --allow-root
    run_in_dir_as_owner "$site" $wp plugin update --all --patch --path="$site" --skip-themes --allow-root
    (( DRY_RUN )) && continue
    v=$(sed -n "s/^\$wp_version *= *'\([^']*\)'.*/\1/p" "$f")
    if [ -n "$fix" ]; then
      if ver_lt "$v" "$fix"; then issue critical "$site: WordPress still $v after update attempt (see $LOG)"
      else ok "$site: WordPress updated to $v"; fixed "$site: WordPress -> $v"; fi
    fi
    if ! (cd "$site" && $wp core verify-checksums --path="$site" --skip-plugins --skip-themes --allow-root >>"$LOG" 2>&1); then
      issue high "$site: core files differ from wordpress.org checksums (possible tampering), see $LOG"
    fi
    local unknown; unknown=$(cd "$site" && $wp plugin verify-checksums --all --path="$site" --skip-plugins --skip-themes --allow-root 2>&1 | grep -iE 'could not retrieve|plugin .* not' | head -n 20)
    [ -n "$unknown" ] && warn "$site: plugins not verifiable against wordpress.org (check they are legitimate):" && say "$unknown"
  done
}

# Bump pinned php:/node: image tags in Dockerfiles and compose files.
check_dockerfiles() {
  head_ "Dockerfiles and compose files"
  local files f line changed img ver suffix fix target out pre
  mapfile -t files < <(project_files 'Dockerfile*'; project_files 'docker-compose.y*ml'; project_files 'compose.y*ml')
  [ ${#files[@]} -gt 0 ] || { note "No Dockerfile or compose file found."; return; }
  local re='^([[:space:]]*(FROM[[:space:]]+(--platform=[^[:space:]]+[[:space:]]+)?|image:[[:space:]]*["'\'']?))((docker\.io/)?(library/)?(php|node)):([0-9]+(\.[0-9]+)*)([^[:space:]"'\'']*)(.*)$'
  for f in "${files[@]}"; do
    changed=0; out=""
    while IFS= read -r line || [ -n "$line" ]; do
      if [[ $line =~ $re ]]; then
        pre=${BASH_REMATCH[1]}; img=${BASH_REMATCH[4]}; ver=${BASH_REMATCH[8]}; suffix=${BASH_REMATCH[10]}${BASH_REMATCH[11]}
        target=""
        if [[ $img == *php ]]; then
          fix=$(fixed_for "$(cut -d. -f1-2 <<<"$ver")" "${PHP_FIXED[@]}") || fix=""
          if [ -z "$fix" ]; then
            [[ $ver == *.*.* || $ver == *.* ]] && ver_lt "$ver" "${PHP_FIXED[0]}" && { bad "$f: $img:$ver is an end-of-life PHP image"; issue high "$f: PHP image $ver is EOL"; }
          elif [[ $ver == *.*.* ]] && ver_lt "$ver" "$fix"; then
            target=$fix
            local latest; latest=$(fetch "${PHP_RELEASES_URL}${ver%.*}" | grep -o "\"version\":\"${ver%.*}\.[0-9]*\"" | grep -o '[0-9][0-9.]*' | head -n1) && ver_lt "$target" "$latest" && target=$latest
          else
            note "$f: $img:$ver$suffix floats on the branch; rebuild with 'docker build --pull' / 'docker compose build --pull'."
          fi
        else
          local major=${ver%%.*}
          fix=$(fixed_for "$major" "${NODE_FIXED[@]}") || fix=""
          if [ -z "$fix" ]; then
            (( major < ${NODE_FIXED[-1]%%.*} )) && { bad "$f: $img:$ver is an end-of-life Node.js image"; issue high "$f: Node image $ver is EOL"; }
          elif [[ $ver == *.*.* ]] && ver_lt "$ver" "$fix"; then
            target=$(node_latest "$major") || target=$fix
          else
            note "$f: $img:$ver$suffix floats on the line; rebuild with --pull."
          fi
        fi
        if [ -n "$target" ]; then
          bad "$f: $img:$ver is unpatched (use $target)"
          if [ "$MODE" = fix ]; then line="$pre$img:$target$suffix"; changed=1
          else issue high "$f: pin $img:$ver -> $target"; fi
        fi
      fi
      out+="$line"$'\n'
    done <"$f"
    if (( changed )); then
      if (( DRY_RUN )); then say "    [dry-run] rewrite image tags in $f"
      else backup_file "$f"; printf '%s' "$out" >"$f"; ok "$f: image tags bumped"; fixed "$f: image tags bumped"
           issue high "$f: rebuild and redeploy the image(s) to apply the new tag"; fi
    fi
  done
}

# Running containers on a Docker host.
check_containers() {
  (( HAS_DOCKER )) || return 0
  head_ "Running Docker containers"
  local id name image v st scan
  while read -r id name image; do
    [ -n "$id" ] || continue
    v=$(docker exec "$id" sh -c 'php -n -r "echo PHP_VERSION;" 2>/dev/null' 2>/dev/null); v=${v%%[^0-9.]*}
    if [ -n "$v" ]; then
      local fix; fix=$(fixed_for "${v%.*}" "${PHP_FIXED[@]}") || fix=""
      if [ -n "$fix" ] && ! ver_lt "$v" "$fix"; then ok "$name ($image): PHP $v patched"
      else
        bad "$name ($image): PHP $v unpatched; rebuild the image on a fixed base."
        issue critical "container $name: PHP $v (image $image) needs a rebuild"
        if [ "$MODE" = fix ]; then
          scan=$(docker exec "$id" sh -c 'php --ini 2>/dev/null' | sed -n 's/^Scan for additional .ini files in: *//p' | cut -d: -f1)
          if [ -n "$scan" ] && [ "$scan" != "(none)" ]; then
            if (( DRY_RUN )); then say "    [dry-run] write $scan/$PHP_MITIGATION_FILE in $name and restart it"
            elif php_mitigation_ini "$v" | docker exec -i "$id" sh -c "cat > '$scan/$PHP_MITIGATION_FILE'"; then
              note "$name: interim mitigation written to $scan (kept across restarts, lost on recreate)"
              (( NO_RESTART )) || run docker restart "$id"
            fi
          fi
        fi
      fi
    fi
    v=$(docker exec "$id" sh -c 'node -v 2>/dev/null' 2>/dev/null); v=${v#v}
    if [ -n "$v" ]; then
      st=$(node_state "$v")
      case $st in
        ok) ok "$name ($image): Node.js $v patched" ;;
        unknown) note "$name: Node.js $v not in advisory data" ;;
        *) bad "$name ($image): Node.js $v $st; rebuild on a patched node image."; issue high "container $name: Node.js $v ($st)" ;;
      esac
    fi
  done < <(docker ps --format '{{.ID}} {{.Names}} {{.Image}}')
}

# Report likely webshells; never deletes anything.
check_webshells() {
  head_ "Webshell indicators"
  local dirs=() f hits=()
  for f in "${PROJECT_FILES[@]}"; do
    case ${f##*/} in composer.lock|package-lock.json) dirs+=("${f%/*}") ;; version.php) dirs+=("${f%/wp-includes/version.php}") ;; esac
  done
  [ ${#dirs[@]} -gt 0 ] || { note "No project directories to scan."; return; }
  mapfile -t dirs < <(printf '%s\n' "${dirs[@]}" | sort -u)
  local pat='eval[[:space:]]*\([[:space:]]*(base64_decode|gzinflate|gzuncompress|str_rot13|\$_(POST|GET|REQUEST|COOKIE))|assert[[:space:]]*\([[:space:]]*\$_(POST|GET|REQUEST|COOKIE)|(system|shell_exec|passthru|exec|popen|proc_open)[[:space:]]*\([[:space:]]*\$_(GET|POST|REQUEST|COOKIE)|preg_replace[[:space:]]*\(.*/e["'\'']'
  mapfile -t hits < <({
    find "${dirs[@]}" \( -name node_modules -o -name vendor -o -name .git \) -prune -o -type f -name '*.php' -size -2M -print0 2>/dev/null \
      | xargs -0 -r grep -lsE "$pat" 2>/dev/null | head -n 50
    find "${dirs[@]}" -path '*/wp-content/uploads/*' -type f -name '*.ph*' 2>/dev/null | head -n 50
  } | sort -u)
  if [ ${#hits[@]} -eq 0 ]; then ok "No webshell patterns found."; return; fi
  for f in "${hits[@]}"; do bad "suspicious: $f"; done
  issue critical "${#hits[@]} suspicious PHP file(s): review them; if confirmed, treat the host as compromised (patching does not remove backdoors)"
}

# --- Service restarts -----------------------------------------------------
restart_php_services() {
  (( RESTART_PHP )) || return 0
  head_ "Restarting PHP services"
  if (( NO_RESTART )); then warn "--no-restart: restart PHP-FPM and the web server yourself to load the changes."; issue high "PHP services not restarted"; return; fi
  local n=0 u s
  if [ "$PANEL" = cpanel ]; then
    run /scripts/restartsrv_apache_php_fpm && n=$((n + 1)); run /scripts/restartsrv_httpd && n=$((n + 1))
  elif (( HAS_SYSTEMD )); then
    for u in $(systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null | awk '{print $1}' \
              | grep -E '^(php[0-9.]*-fpm|php-fpm[0-9.]*|ea-php[0-9]+-php-fpm|rh-php[0-9]+-php-fpm|plesk-php[0-9.]+-fpm|apache2|httpd|lsws|lshttpd|lsws-[a-z]+)\.service$'); do
      run systemctl restart "$u" && note "restarted $u" && n=$((n + 1))
    done
  else
    for s in /etc/init.d/php-fpm*; do [ -x "$s" ] && run "$s" restart && n=$((n + 1)); done
    pgrep -f 'php-fpm: master' >/dev/null && run pkill -USR2 -f 'php-fpm: master' && n=$((n + 1))
    has apachectl && pgrep -x apache2 >/dev/null && run apachectl -k restart && n=$((n + 1))
    has httpd && pgrep -x httpd >/dev/null && run httpd -k restart && n=$((n + 1))
  fi
  [ -x /usr/local/lsws/bin/lswsctrl ] && run /usr/local/lsws/bin/lswsctrl restart && n=$((n + 1))
  (( n > 0 )) || warn "No running PHP-FPM/web server found to restart; restart them by hand if they run elsewhere."
  return 0
}

restart_node_services() {
  [ ${#RESTART_NODE_PREFIXES[@]} -gt 0 ] || return 0
  head_ "Restarting Node.js services"
  if (( NO_RESTART )); then warn "--no-restart: restart your Node.js apps to load the new runtime."; issue high "Node.js apps not restarted"; return; fi
  local p u restarted=0
  if (( HAS_SYSTEMD )); then
    for p in "${RESTART_NODE_PREFIXES[@]}"; do
      for u in $(grep -lsE "ExecStart=.*(${p}/bin/(node|npm)|pm2)" /etc/systemd/system/*.service | xargs -r -n1 basename); do
        systemctl is-active -q "$u" && run systemctl restart "$u" && note "restarted $u" && restarted=1
      done
    done
  fi
  if has pm2 && pm2 pid >/dev/null 2>&1; then run pm2 reload all && note "pm2 reload all" && restarted=1; fi
  (( restarted )) || warn "No systemd/pm2 Node service found; restart your Node.js apps by hand."
}

# --- Rollback -------------------------------------------------------------
rollback_files_for() { # restore specific files from the current run's backups
  local f src
  for f in "$@"; do
    src="$BACKUP_DIR/files$(readlink -f "$f")"
    [ -f "$src" ] && cp -a "$src" "$f"
  done
}

# Replay a run's manifest in reverse. The run directory and its manifest are
# checked like STATE_DIR before a single line is read (FR-PTCH-RBK-002);
# with --dry-run every step is only printed (changed in 0.1.1).
do_rollback() {
  local base="$STATE_DIR/backups" dir r
  if [ -n "$ROLLBACK_ID" ]; then
    [[ $ROLLBACK_ID =~ ^[0-9]{8}-[0-9]{6}$ ]] || { echo "Invalid rollback ID: $ROLLBACK_ID (expected YYYYmmdd-HHMMSS)" >&2; exit 2; }
    dir="$base/$ROLLBACK_ID"
  else
    local c; dir=""
    for c in "$base"/[0-9]*-[0-9]*; do [[ ${c##*/} =~ ^[0-9]{8}-[0-9]{6}$ ]] && dir=$c; done   # glob order = oldest first
  fi
  if [ -z "$dir" ] || { [ ! -e "$dir/manifest" ] && [ ! -L "$dir/manifest" ]; }; then say "No backup run found in $base"; exit 2; fi
  r=$(unsafe_reason "$dir" dir) && state_dir_fail "$dir" "$r"
  r=$(unsafe_reason "$dir/manifest" file) && state_dir_fail "$dir/manifest" "$r"
  head_ "Rolling back $(basename "$dir")$( ((DRY_RUN)) && echo ' (dry-run)')"
  local action a b
  while IFS=$'\t' read -r action a b; do
    if (( DRY_RUN )); then
      case $action in
        "") ;;
        note) warn "$a" ;;
        *) say "    [dry-run] $action $a${b:+ $b}" ;;
      esac
      case $action in created) RESTART_PHP=1 ;; untar) RESTART_NODE_PREFIXES+=("$b") ;; esac
      continue
    fi
    case $action in
      copy)    cp -a "$b" "$a" && note "restored $a" ;;
      created) rm -f "$a" && note "removed $a"; RESTART_PHP=1 ;;
      untar)   tar -xzf "$a" -C "$b" && note "restored Node.js in $b"; RESTART_NODE_PREFIXES+=("$b") ;;
      composer-install) local cmd; cmd=$(composer_cmd) && run_in_dir_as_owner "$a" $cmd install --no-interaction --no-progress && note "composer install in $a" ;;
      npm-ci)  run_in_dir_as_owner "$a" npm ci --no-fund --no-audit && note "npm ci in $a" ;;
      note)    warn "$a" ;;
    esac
  done < <(tac "$dir/manifest")
  restart_php_services; restart_node_services
  if (( DRY_RUN )); then say "Dry-run: nothing was changed."
  else say "Rollback done. Package upgrades (apt/dnf/yum) are kept."; fi
}

# --- State directory (spec §2.1, CR-SRS-13, NFR-SEC-010) ------------------
STATE_WARN=()

# unsafe_reason PATH dir|file: print why PATH must not be trusted (symlink,
# not_dir, owner, mode) and succeed; fail when PATH is safe. Never follows
# symlinks, so a path planted by another local user is rejected.
unsafe_reason() {
  local p=$1 kind=$2 uid mode
  if [ -L "$p" ]; then echo symlink; return 0; fi
  if [ "$kind" = dir ]; then [ -d "$p" ] || { echo not_dir; return 0; }
  else [ -f "$p" ] || { echo not_dir; return 0; }; fi
  read -r uid mode <<<"$(stat -c '%u %a' -- "$p" 2>/dev/null)"
  [ "${uid:-}" = "$EUID" ] || { echo owner; return 0; }
  (( (8#${mode:-777} & 8#022) == 0 )) || { echo mode; return 0; }
  return 1
}

state_dir_fail() { # state_dir_fail PATH REASON: ERR-CLI-412-01, exit 2
  local uid; uid=$(stat -c %u -- "$1" 2>/dev/null) || uid=-
  echo "State directory $1 is unsafe ($2); aborting. [ERR-CLI-412-01] path=$1 reason=$2 uid=$uid euid=$EUID" >&2
  exit 2
}

# Drop permission bits beyond WANT (e.g. 0755 left by v0.1 under umask 022).
tighten_state_dir() { # tighten_state_dir DIR WANT
  local mode; mode=$(stat -c %a -- "$1") || return 0
  if (( 8#$mode & ~8#$2 & 8#777 )); then
    chmod "$2" -- "$1" && STATE_WARN+=("state dir $1: mode $mode tightened to $2")
  fi
}

# Pick STATE_DIR: root uses /var/lib/php-quickpatch with no fallback; other
# users use ~/.php-quickpatch, else the newest safe php-quickpatch-$EUID[.*]
# in TMPDIR, else a fresh mktemp -d. Unsafe primary path -> exit 2.
select_state_dir() {
  local p r
  if (( IS_ROOT )); then
    p=/var/lib/php-quickpatch
    if [ ! -e "$p" ] && [ ! -L "$p" ]; then mkdir -m 0750 -- "$p" 2>/dev/null || state_dir_fail "$p" create_failed; fi
    r=$(unsafe_reason "$p" dir) && state_dir_fail "$p" "$r"
    tighten_state_dir "$p" 0750; STATE_DIR=$p; return
  fi
  if [ -n "${HOME:-}" ]; then
    p="$HOME/.php-quickpatch"
    if [ -e "$p" ] || [ -L "$p" ] || mkdir -m 0700 -- "$p" 2>/dev/null; then
      r=$(unsafe_reason "$p" dir) && state_dir_fail "$p" "$r"
      if [ -w "$p" ] && [ -x "$p" ]; then tighten_state_dir "$p" 0700; STATE_DIR=$p; return; fi
    fi
  fi
  local tmp=${TMPDIR:-/tmp} c best="" best_m=-1 m
  for c in "$tmp/php-quickpatch-$EUID" "$tmp/php-quickpatch-$EUID".*; do
    [ -e "$c" ] || [ -L "$c" ] || continue
    if r=$(unsafe_reason "$c" dir); then
      STATE_WARN+=("skipped state dir candidate $c ($r)"); echo "[WARN] skipped unsafe state dir candidate $c ($r)" >&2; continue
    fi
    [ -w "$c" ] && [ -x "$c" ] || continue
    m=$(stat -c %Y -- "$c") && (( m > best_m )) && { best=$c; best_m=$m; }
  done
  if [ -n "$best" ]; then
    tighten_state_dir "$best" 0700
  else
    best=$(mktemp -d "$tmp/php-quickpatch-$EUID.XXXXXX" 2>/dev/null) || state_dir_fail "$tmp/php-quickpatch-$EUID.XXXXXX" create_failed
    r=$(unsafe_reason "$best" dir) && state_dir_fail "$best" "$r"
  fi
  STATE_DIR=$best
}

# --- Main -----------------------------------------------------------------
parse_args() {
  while [ $# -gt 0 ]; do
    case $1 in
      scan|fix) MODE=$1 ;;
      rollback) MODE=rollback; if [ $# -gt 1 ] && [[ $2 != -* ]]; then ROLLBACK_ID=$2; shift; fi ;;
      --path) [ $# -ge 2 ] || { usage; exit 2; }; SCAN_PATHS+=("$(readlink -f "$2")"); shift ;;
      --only) [ $# -ge 2 ] || { usage; exit 2; }; ONLY=$2; shift ;;
      --dry-run) DRY_RUN=1 ;;
      --no-restart) NO_RESTART=1 ;;
      --no-memlimit) NO_MEMLIMIT=1 ;;
      --offline) OFFLINE=1 ;;
      --version) echo "php-quickpatch $QP_VERSION"; exit 0 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
  done
}

want() { [[ ",$ONLY," == *",$1,"* ]]; }

main() {
  parse_args "$@"
  select_state_dir
  LOG="$STATE_DIR/php-quickpatch.log"
  (umask 077; : >>"$LOG") 2>/dev/null
  local w; for w in ${STATE_WARN[@]+"${STATE_WARN[@]}"}; do log "WARN: $w"; done
  WORK_DIR=$(mktemp -d) || exit 2
  trap 'rm -rf "$WORK_DIR"' EXIT
  exec 9>"$STATE_DIR/.lock"
  flock -n 9 || { echo "Another php-quickpatch run is in progress." >&2; exit 2; }

  say "${C_B}php-quickpatch $QP_VERSION${C_0} mode=$MODE$( ((DRY_RUN)) && echo ' (dry-run)') log=$LOG"
  if [ "$MODE" = rollback ]; then detect_env; do_rollback; exit 0; fi

  detect_env
  discover_projects
  want php && check_php
  want node && check_node
  want composer && check_composer
  want npm && check_npm
  want wp && check_wordpress
  if want docker; then check_dockerfiles; check_containers; fi
  want webshell && check_webshells
  if [ "$MODE" = fix ]; then restart_php_services; restart_node_services; fi

  head_ "Summary"
  local s; for s in "${SUMMARY[@]}"; do say "  - $s"; done
  say "  fixed: $FIXED | open issues: $ISSUES (critical: $CRITICAL)"
  [ -n "$BACKUP_DIR" ] && say "  rollback: $0 rollback $(basename "$BACKUP_DIR")"
  [ "$MODE" = scan ] && (( ISSUES > 0 )) && say "  run '$0 fix' to apply the fixes."
  (( ISSUES == 0 ))
}

main "$@"
