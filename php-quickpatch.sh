#!/usr/bin/env bash
# php-quickpatch: detect, audit and auto-patch PHP and Node.js stacks on
# plain VPS hosts, hosting panels (cPanel, Plesk, aaPanel, CyberPanel,
# DirectAdmin) and Docker hosts or containers.
#
# Usage: php-quickpatch.sh [COMMAND] [options]   (see --help)
set -uo pipefail

# Bash 4.3+ is required (negative array indexes, mapfile, namerefs).
# This check must stay parseable by older shells (ERR-CLI-424-02).
if [ -z "${BASH_VERSINFO:-}" ] || [ "${BASH_VERSINFO[0]}" -lt 4 ] || { [ "${BASH_VERSINFO[0]}" -eq 4 ] && [ "${BASH_VERSINFO[1]}" -lt 3 ]; }; then
  echo "Bash 4.3+, flock and curl are required (found: bash ${BASH_VERSION:-unknown})." >&2
  exit 2
fi

QP_VERSION="2.0.0-alpha.1"

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
ASSUME_YES=0
JSON=0
ONLY="php,node,composer,npm,wp,docker,webshell"
SCAN_PATHS=()
SCHEMA_ARG=""
PASS_ARGS=()
ARGV_ORIG=("$@")

# --- State ----------------------------------------------------------------
IS_ROOT=0; (( EUID == 0 )) && IS_ROOT=1
IN_CONTAINER=0; PANEL=none; PKG_MGR=none; HAS_SYSTEMD=0; HAS_DOCKER=0
STATE_DIR=""; LOG=""; BACKUP_DIR=""; RUN_ID=""; WORK_DIR=""
RESTART_PHP=0; RESTART_NODE_PREFIXES=(); APT_UPDATED=0
ISSUES=0; FIXED=0; CRITICAL=0; RESTART_FAILED=0
SUMMARY=()
CUR_REF=""          # object_ref attached to issues raised while it is set
SCRIPT_PATH=$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "$0")
SHARE_DIR=""
for d in "${SCRIPT_PATH%/*}/share/php-quickpatch" /usr/local/share/php-quickpatch; do
  [ -d "$d" ] && { SHARE_DIR=$d; break; }
done

# JSON fragments collected for the --json envelope (FR-CLI-JSON-001).
J_ISSUES=(); J_ERRORS=(); J_WARNINGS=()
J_RUNTIMES=(); J_PROJECTS=(); J_CONTAINERS=(); J_DEPS=(); J_WP=(); J_WSH=()
J_ACTIONS=(); J_RT_AFTER=(); J_MITIG=(); J_RESTARTS=(); J_RESTARTED=(); J_RESTART_FAIL=()
J_CHANGES=(); J_AFFECTED=(); J_MANIFEST=(); J_PLANNED=()
J_AUDIT_ANCHOR="null"
BY_STATE_OK=0; BY_STATE_BACKPORT=0; BY_STATE_VULN=0; BY_STATE_EOL=0; BY_STATE_UNKNOWN=0
VULN_PACKAGES=0

if [ -t 1 ]; then C_R=$'\e[31m'; C_G=$'\e[32m'; C_Y=$'\e[33m'; C_B=$'\e[1m'; C_0=$'\e[0m'
else C_R=""; C_G=""; C_Y=""; C_B=""; C_0=""; fi

log()  { [ -n "$LOG" ] && printf '%s %s\n' "$(date '+%F %T')" "$*" >>"$LOG"; return 0; }
say()  { printf '%s\n' "$*"; log "$*"; }
head_() { say ""; say "${C_B}== $* ==${C_0}"; }
ok()   { say "  ${C_G}[OK]${C_0} $*"; }
warn() { say "  ${C_Y}[WARN]${C_0} $*"; }
bad()  { say "  ${C_R}[VULN]${C_0} $*"; }
note() { say "  [i] $*"; }

# --- JSON helpers ---------------------------------------------------------
# _js STRING: REPLY = JSON string literal, escaped exactly like Python's
# json.dumps(ensure_ascii=False) so audit hashes match across languages.
_js() {
  local LC_ALL=C s=$1 c hex
  s=${s//\\/\\\\}; s=${s//\"/\\\"}
  case $s in *[$'\x01'-$'\x1f']*)
    s=${s//$'\n'/\\n}; s=${s//$'\r'/\\r}; s=${s//$'\t'/\\t}; s=${s//$'\b'/\\b}; s=${s//$'\f'/\\f}
    while [[ $s =~ [$'\x01'-$'\x1f'] ]]; do c=${BASH_REMATCH[0]}; printf -v hex '\\u%04x' "'$c"; s=${s//"$c"/$hex}; done ;;
  esac
  REPLY="\"$s\""
}

# jo key=T:value ...: REPLY = JSON object, keys in the given order.
# T: s string, S string or null when empty, n number (null when empty),
#    b boolean (1/true), j raw JSON (null when empty).
jo() {
  local out="" kv k t v
  for kv in "$@"; do
    k=${kv%%=*}; v=${kv#*=}; t=${v%%:*}; v=${v#*:}
    case $t in
      s) _js "$v"; v=$REPLY ;;
      S) if [ -z "$v" ]; then v=null; else _js "$v"; v=$REPLY; fi ;;
      n|j) [ -n "$v" ] || v=null ;;
      b) case $v in 1|true) v=true ;; *) v=false ;; esac ;;
    esac
    out+="${out:+,}\"$k\":$v"
  done
  REPLY="{$out}"
}

# jarr NAME: REPLY = JSON array of the (already JSON) elements of array NAME.
jarr() { local -n _a=$1; local IFS=,; if (( ${#_a[@]} )); then REPLY="[${_a[*]}]"; else REPLY="[]"; fi; }

# jas STRING...: REPLY = JSON array of strings.
jas() { local s out=""; for s in "$@"; do _js "$s"; out+="${out:+,}$REPLY"; done; REPLY="[$out]"; }

# --- Messages and error codes (catalog/errors.tsv, BR-CLI-006) ------------
declare -A ERR_VI=()
ERR_LOADED=0
load_errors() {
  (( ERR_LOADED )) && return 0; ERR_LOADED=1
  local f="$SHARE_DIR/catalog/errors.tsv" code vi
  [ -n "$SHARE_DIR" ] && [ -r "$f" ] || return 0
  while IFS=$'\t' read -r code _ _ _ vi _; do
    [[ $code == ERR-* ]] && ERR_VI[$code]=$vi
  done <"$f"
}

# msg CODE DEFAULT_EN [key=value ...]: REPLY = message (Vietnamese when
# QP_LANG=vi and the catalog has CODE), placeholders {key} filled in.
msg() {
  local code=$1 text=$2 kv; shift 2
  if [ "${QP_LANG:-}" = vi ]; then load_errors; [ -n "${ERR_VI[$code]:-}" ] && text=${ERR_VI[$code]}; fi
  for kv in "$@"; do text=${text//"{${kv%%=*}}"/${kv#*=}}; done
  REPLY=$text
}

# BR-SEC-006: mask secrets in anything that leaves the process.
redact() {
  local s=$1 v name
  for name in $(compgen -e); do
    case $name in QP_*_KEY|QP_*_TOKEN|QP_*_SECRET)
      v=${!name}; [ ${#v} -ge 4 ] && s=${s//"$v"/***} ;;
    esac
  done
  if [[ $s =~ (password|passwd|token|secret|api_key|apikey)= ]]; then
    s=$(sed -E 's/((password|passwd|token|secret|api_key|apikey)=)[^&[:space:]]*/\1***/Ig' <<<"$s")
  fi
  if [[ $s == *://*:*@* ]]; then s=$(sed -E 's#(://[^/:@[:space:]]+:)[^@[:space:]]+@#\1***@#g' <<<"$s"); fi
  REPLY=$s
}

# Record an unresolved finding (severity: high|critical) for the summary.
issue() {
  local sev=$1; shift
  ISSUES=$((ISSUES + 1)); [ "$sev" = critical ] && CRITICAL=$((CRITICAL + 1))
  SUMMARY+=("${sev^^}: $*")
  jo severity=s:"$sev" code=S:"${ISSUE_CODE:-}" message=s:"$*" object_ref=S:"$CUR_REF"; J_ISSUES+=("$REPLY")
  ISSUE_CODE=""
}
ISSUE_CODE=""
issue_c() { ISSUE_CODE=$1; shift; issue "$@"; }   # issue_c CODE SEV MESSAGE
fixed() { FIXED=$((FIXED + 1)); SUMMARY+=("FIXED: $*"); }
add_error()   { jo code=s:"$1" message=s:"$2" object_ref=S:"${3:-$CUR_REF}"; J_ERRORS+=("$REPLY"); }
add_warning() { jo code=S:"$1" message=s:"$2" object_ref=S:"${3:-$CUR_REF}"; J_WARNINGS+=("$REPLY"); }

# act KIND STATUS DETAIL [ERROR_CODE]: one entry of result.actions[] (qp.fix/1)
act() { jo seq=n:$(( ${#J_ACTIONS[@]} + 1 )) object_ref=S:"$CUR_REF" kind=s:"$1" status=s:"$2" detail=s:"$3" error_code=S:"${4:-}"; J_ACTIONS+=("$REPLY"); }

# change TYPE ACTION TARGET [FROM] [TO] [DETAIL]: preview.changes[] entry
change() { jo type=s:"$1" action=s:"$2" target=s:"$3" from=S:"${4:-}" to=S:"${5:-}" detail=S:"${6:-}" verified=b:1; J_CHANGES+=("$REPLY"); }
affected() { # affected KIND ID LABEL (deduplicated)
  jo kind=s:"$1" id=s:"$2" label=s:"$3"; local e
  for e in ${J_AFFECTED[@]+"${J_AFFECTED[@]}"}; do [ "$e" = "$REPLY" ] && return 0; done
  J_AFFECTED+=("$REPLY")
}

usage() {
  cat <<'EOF'
php-quickpatch: detect, audit and auto-patch PHP and Node.js stacks.

Usage:
  php-quickpatch.sh scan     [options]   audit only, change nothing (default)
  php-quickpatch.sh fix      [options]   audit, then apply every safe fix
  php-quickpatch.sh rollback [ID]        undo file changes of a fix run
                                          (latest run when ID is omitted)
  php-quickpatch.sh schema COMMAND       print the JSON Schema of COMMAND's --json
  php-quickpatch.sh feeds|assess|plan|report|audit|serve ...
                                          need Python 3.6+ (see docs)
Options:
  --path DIR        project/web root to scan (repeatable). Default: common
                    web roots (/var/www, /home, /srv, /www/wwwroot, ...)
  --only LIST       comma list of: php,node,composer,npm,wp,docker,webshell,sites
  --dry-run         with fix or rollback: print what would change, change nothing
  --no-restart      do not restart PHP-FPM/web server/Node services/containers
  --no-memlimit     skip the memory_limit=-1 interim mitigation
  --offline         no network lookups (no OSV, no release feeds, no downloads)
  --json            print one JSON document on stdout (text goes to stderr)
  --yes             answer yes to confirmations of new write commands
  -h, --help        this help;  --version  print version

Exit status: 0 nothing left to fix, 1 issues remain, 2 usage or runtime error.
Run as root for system-level fixes; without root only project-level fixes
(Composer, npm, WordPress) are applied.
EOF
}

# --- Envelope -------------------------------------------------------------
schema_of() { # schema_of MODE -> REPLY = schema id
  case $1 in
    scan) REPLY="qp.scan/1" ;;
    fix|rollback) REPLY="qp.fix/1" ;;
    schema) REPLY="qp.schema/1" ;;
    *) REPLY="qp.$1/1" ;;
  esac
}

host_json() {
  local hn os="unknown" kernel
  hn=$(cat /proc/sys/kernel/hostname 2>/dev/null || hostname 2>/dev/null || echo unknown)
  [ -r /etc/os-release ] && os=$(. /etc/os-release && echo "${ID:-unknown} ${VERSION_ID:-}")
  kernel=$(uname -r 2>/dev/null || echo unknown)
  [ -f /.dockerenv ] || grep -qsE '(docker|containerd|kubepods|libpod)' /proc/1/cgroup && IN_CONTAINER=1
  jo hostname=s:"$hn" os=s:"${os% }" kernel=s:"$kernel" is_root=b:$IS_ROOT in_container=b:$IN_CONTAINER
}

# emit_envelope EXIT_CODE RESULT_JSON: print the --json document on fd 3.
emit_envelope() {
  local code=$1 result=${2:-null} a argv=() name=$MODE sub=null
  for a in ${ARGV_ORIG[@]+"${ARGV_ORIG[@]}"}; do redact "$a"; argv+=("$REPLY"); done
  schema_of "$MODE"; local schema=$REPLY
  [ "$MODE" = rollback ] && name=rollback
  host_json; local host=$REPLY
  jas ${argv[@]+"${argv[@]}"}; local jargv=$REPLY
  jo name=s:"$name" subcommand=j:"$sub" argv=j:"$jargv" job_id=S:"${QP_JOB_ID:-}" actor=S:"${QP_ACTOR:-}"; local cmd=$REPLY
  jo bundle_id=j:null freshness=j:null data_age_h=j:null stale_sources=j:"[]"; local data=$REPLY
  jarr J_ISSUES; local issues=$REPLY; jarr J_ERRORS; local errors=$REPLY; jarr J_WARNINGS; local warnings=$REPLY
  local now; now=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  jo schema=s:"$schema" schema_version=s:"1.0.0" tool=j:'{"name":"php-quickpatch","version":"'"$QP_VERSION"'"}' \
     generated_at=s:"$now" host=j:"$host" command=j:"$cmd" dry_run=b:$DRY_RUN exit_code=n:"$code" \
     data=j:"$data" catalog_version=j:null result=j:"$result" issues=j:"$issues" errors=j:"$errors" \
     warnings=j:"$warnings" audit_anchor=j:"$J_AUDIT_ANCHOR"
  local doc=$REPLY
  # Paths may hold bytes that are not UTF-8: drop them so the document stays valid.
  if has iconv && ! printf '%s' "$doc" | iconv -f UTF-8 -t UTF-8 >/dev/null 2>&1; then
    doc=$(printf '%s' "$doc" | iconv -f UTF-8 -t UTF-8 -c)
  fi
  printf '%s\n' "$doc" >&3
}

# finish CODE [RESULT_JSON]: emit the envelope when --json, then exit.
finish() {
  local code=$1
  (( JSON )) && emit_envelope "$code" "${2:-null}"
  exit "$code"
}

# fatal CODE DEFAULT_EN [key=value...]: report an error that stops the
# command (exit 2), on stderr and in errors[] (FR-CLI-JSON-001).
fatal() {
  local code=$1 text=$2; shift 2
  msg "$code" "$text" "$@"; local m=$REPLY
  printf '%s\n' "$m" >&2; log "ERROR $code: $m"
  add_error "$code" "$m"
  finish 2
}

arg_error() { # arg_error ARG: v0.1 wording, ERR-CLI-400-01
  if [ -n "$1" ]; then msg ERR-CLI-400-01 "Unknown argument: {arg}" arg="$1"; echo "$REPLY" >&2; fi
  usage >&2
  if (( JSON )); then
    exec 3>&1
    msg ERR-CLI-400-01 "Unknown argument: {arg}" arg="${1:-(missing value)}"; add_error ERR-CLI-400-01 "$REPLY"
    emit_envelope 2 null
  fi
  exit 2
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

sha1_12() { printf '%s' "$1" | sha1sum | cut -c1-12; }
runtime_id() { REPLY="$1:$(sha1_12 "$2")"; }   # runtime_id php|node PATH

# probe SECONDS CMD...: run a read-only probe with a time limit (BR-SCAN-002)
probe() { local t=$1; shift; if has timeout; then timeout "$t" "$@"; else "$@"; fi; }

# run CMD...: execute (or print in dry-run), output goes to the log. The
# lock fd 9 and the JSON fd 3 are closed so no child keeps them (BR-JOB-002).
run() {
  if (( DRY_RUN )); then say "    [dry-run] $*"; return 0; fi
  log "+ $*"
  "$@" >>"$LOG" 2>&1 9>&- 3>&-
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

# Free space (KiB) on the filesystem holding PATH.
free_kib() { df -Pk "$1" 2>/dev/null | awk 'NR==2 {print $4}'; }

# Create this run's backup directory atomically (FR-PTCH-RBK-001): a new
# backups/<YYYYmmdd-HHMMSS>/ is made with mkdir (no -p) so two runs that
# start in the same second never share or truncate a manifest.
ensure_backup_dir() {
  [ -n "$BACKUP_DIR" ] && return 0
  local base="$STATE_DIR/backups" id try free used
  mkdir -p "$base" || fatal ERR-ENV-507-01 "Cannot create $base"
  free=$(free_kib "$STATE_DIR")
  if [ -n "$free" ] && (( free < 51200 )); then
    fatal ERR-ENV-507-01 "Not enough disk space in {dir} to back up before changing anything (free: {free} MiB, need 50 MiB)." dir="$STATE_DIR" free=$((free / 1024)) site="$STATE_DIR"
  fi
  for ((try = 1; try <= 10; try++)); do
    id=$(date +%Y%m%d-%H%M%S)
    if mkdir -m 0700 "$base/$id" 2>/dev/null; then
      mkdir "$base/$id/files" && (set -o noclobber; : >"$base/$id/manifest") 2>/dev/null && break
    fi
    id=""; (( try < 10 )) && sleep 1
  done
  if [ -z "$id" ]; then
    log "dir=$base/$(date +%Y%m%d-%H%M%S) attempts=10"
    fatal ERR-PTCH-409-01 "Could not create a new backup directory: {dir} still exists after 10 attempts; nothing was changed." dir="$base/$(date +%Y%m%d-%H%M%S)"
  fi
  BACKUP_DIR="$base/$id"; RUN_ID=$id
  chmod 0600 "$BACKUP_DIR/manifest"
  say "  [i] Backups for this run: $BACKUP_DIR"
  used=$(du -sk "$base" 2>/dev/null | awk '{print $1}')
  if [ -n "$used" ] && (( used > 1048576 )); then
    warn "$base uses $((used / 1024)) MiB (> 1 GiB); remove old runs you no longer need."
    add_warning "" "backups/ uses $((used / 1024)) MiB (> 1 GiB)"
  fi
}

# space_for KIB: true when STATE_DIR can take KIB more plus 50 MiB.
space_for() { local free; free=$(free_kib "$STATE_DIR"); [ -z "$free" ] || (( free >= $1 + 51200 )); }

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

pkg_version() { # pkg_version MANAGER PACKAGE
  case $1 in
    dpkg) dpkg-query -W -f='${Version}' "$2" 2>/dev/null ;;
    rpm) rpm -q --qf '%{VERSION}-%{RELEASE}' "$2" 2>/dev/null ;;
    apk) apk info -e -v "$2" 2>/dev/null | sed "s/^$2-//" ;;
  esac
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
  return 0
}

# --- PHP runtimes ---------------------------------------------------------
discover_php_bins() {
  local c
  if [ -n "${QP_PHP_BINS:-}" ]; then
    for c in $QP_PHP_BINS; do readlink -f "$c" || echo "$c"; done | grep -v -- '-config[0-9.]*$' | sort -u
    return
  fi
  {
    has php && command -v php
    for c in /usr/bin/php[0-9]* /usr/local/bin/php /opt/cpanel/ea-php*/root/usr/bin/php \
             /opt/alt/php*/usr/bin/php /opt/remi/php*/root/usr/bin/php /opt/plesk/php/*/bin/php \
             /www/server/php/*/bin/php /usr/local/lsws/lsphp*/bin/php /usr/local/php*/bin/php; do
      [ -x "$c" ] && echo "$c"
    done
  } | while read -r c; do readlink -f "$c"; done | grep -v -- '-config[0-9.]*$' | sort -u
}

php_version() { local v; v=$(probe 10 "$1" -n -r 'echo PHP_VERSION;' 2>/dev/null) || return 1; v=${v%%[^0-9.]*}; [ -n "$v" ] || return 1; echo "$v"; }

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
  # shellcheck disable=SC2086  # "MANAGER PACKAGE" splits on purpose
  if [ -n "$owner" ] && pkg_has_cves $owner "${PHP_CVES[@]}"; then echo ok-backport; return; fi
  if fixed_for "$branch" "${PHP_FIXED[@]}" >/dev/null; then echo vulnerable; else echo eol; fi
}

php_sapis_note() {
  local s=""
  if [ -d /etc/apache2/mods-enabled ] && ls /etc/apache2/mods-enabled/php*.load >/dev/null 2>&1; then s+=" mod_php(apache2)"; fi
  if has httpd && httpd -M 2>/dev/null | grep -q php; then s+=" mod_php(httpd)"; fi
  [ -n "$s" ] && warn "Apache mod_php detected:$s. PHP2Shell is easiest to exploit there; prefer PHP-FPM."
  return 0
}

# BR-PTCH-002: package group of the build that owns a PHP binary.
php_pkg_group() { # php_pkg_group MANAGER PACKAGE -> group regex / glob
  local mgr=$1 pkg=$2
  case $mgr in
    dpkg) if [[ $pkg =~ ^(php[0-9.]+|ea-php[0-9]+|lsphp[0-9]+|plesk-php[0-9]+) ]]; then echo "${BASH_REMATCH[1]}"; else echo php; fi ;;
    rpm)  if [[ $pkg =~ ^(ea-php[0-9]+|alt-php[0-9]+|php[0-9]+|lsphp[0-9]+|plesk-php[0-9]+) ]]; then echo "${BASH_REMATCH[1]}*"; else echo 'php*'; fi ;;
    apk)  if [[ $pkg =~ ^(php[0-9]*) ]]; then echo "${BASH_REMATCH[1]}"; else echo php; fi ;;
  esac
}

# Install all newer packages of the PHP build that owns BIN.
php_upgrade() {
  local bin=$1 mgr pkg glob pkgs
  read -r mgr pkg <<<"$(pkg_owner "$bin")"
  if [ -z "${mgr:-}" ]; then
    warn "$bin is not from a package (source build or panel build). Upgrade it in the panel or rebuild it; applying interim mitigation."
    return 1
  fi
  glob=$(php_pkg_group "$mgr" "$pkg")
  case $mgr in
    dpkg)
      mapfile -t pkgs < <(dpkg-query -W -f='${db:Status-Abbrev} ${binary:Package}\n' "${glob}*" 2>/dev/null | awk '$1 ~ /^ii/ {print $2}')
      [ ${#pkgs[@]} -gt 0 ] || return 1
      if (( ! APT_UPDATED )); then run apt-get update -q && APT_UPDATED=1; fi
      record note "apt upgraded: ${pkgs[*]} (packages are not downgraded by rollback)"
      change package upgrade "${pkgs[*]}" "" "" "apt-get install -y -q --only-upgrade"
      run env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade \
          -o Dpkg::Options::=--force-confold "${pkgs[@]}" ;;
    rpm)
      record note "rpm upgraded: $glob (packages are not downgraded by rollback)"
      change package upgrade "$glob" "" "" "dnf/yum upgrade"
      if has dnf; then run dnf -y -q upgrade "$glob"; else run yum -y -q update "$glob"; fi ;;
    apk)
      record note "apk upgraded: ${glob}* (packages are not downgraded by rollback)"
      mapfile -t pkgs < <(apk info 2>/dev/null | grep "^${glob}")
      change package upgrade "${pkgs[*]}" "" "" "apk upgrade --no-cache"
      run apk upgrade --no-cache "${pkgs[@]}" ;;
  esac
}

# The conf.d directories that BIN and its sibling SAPIs read.
php_scan_dirs() {
  local bin=$1 d
  d=$(probe 10 "$bin" --ini 2>/dev/null | sed -n 's/^Scan for additional .ini files in: *//p')
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
  local dirs
  if ! dirs=$(php_scan_dirs "$bin"); then
    msg ERR-PTCH-412-01 "No conf.d scan dir for {bin}; set the mitigation in its php.ini by hand." bin="$bin"
    warn "$REPLY"; add_warning ERR-PTCH-412-01 "$REPLY"; act mitigation_add failed "$REPLY" ERR-PTCH-412-01
    return 1
  fi
  while read -r d; do
    [ -d "$d" ] || continue
    f="$d/$PHP_MITIGATION_FILE"
    if [ -f "$f" ]; then note "mitigation already present: $f"; continue; fi
    change file create "$f" "" "" "interim mitigation (FR-PTCH-MIT-001)"
    if (( DRY_RUN )); then say "    [dry-run] write $f"; act mitigation_add planned "$f"; continue; fi
    record created "$f" && php_mitigation_ini "$v" >"$f" && note "wrote $f"
    act mitigation_add "done" "$f"
    jas "${PHP_CVES[@]}"; jo runtime_id=s:"${CUR_REF#runtime:}" file=s:"$f" action=s:added driver_ids=j:"$REPLY"; J_MITIG+=("$REPLY")
  done <<<"$dirs"
  (( NO_MEMLIMIT )) || note "memory_limit=-1 removes PHP's memory cap; apps calling ini_set('memory_limit') can still override it."
  RESTART_PHP=1
}

# Remove the interim mitigation once a runtime is patched (FR-PTCH-MIT-002).
php_unmitigate() {
  local bin=$1 d dirs f
  dirs=$(php_scan_dirs "$bin") || return 0
  while read -r d; do
    f="$d/$PHP_MITIGATION_FILE"
    [ -f "$f" ] || continue
    change file delete "$f" "" "" "remove mitigation once patched (FR-PTCH-MIT-002)"
    if (( ! DRY_RUN )) && ! space_for "$(du -sk "$f" | awk '{print $1}')"; then
      warn "$f kept: not enough space in $STATE_DIR to back it up"; act mitigation_remove skipped "$f" ERR-ENV-507-01; continue
    fi
    backup_file "$f"
    if run rm -f "$f"; then
      note "removed obsolete $f"; RESTART_PHP=1
      act mitigation_remove "$( ((DRY_RUN)) && echo planned || echo "done")" "$f"
      jo runtime_id=s:"${CUR_REF#runtime:}" file=s:"$f" action=s:removed driver_ids=j:"[]"; J_MITIG+=("$REPLY")
    fi
  done <<<"$dirs"
}

# php_runtime_json BIN VERSION STATE: append a runtime object (FR-SCAN-RT-001)
php_runtime_json() {
  local bin=$1 v=$2 st=$3 rid mgr="" pkg="" pver="" src sfx d exts=() sapis=(cli) dirs=() owner
  runtime_id php "$bin"; rid=$REPLY
  owner=$(pkg_owner "$bin"); read -r mgr pkg <<<"$owner"
  [ -n "$mgr" ] && pver=$(pkg_version "$mgr" "$pkg")
  sfx=${bin##*/php}; d=${bin%/*}
  [ -x "${d%/bin}/sbin/php-fpm$sfx" ] || [ -x "/usr/sbin/php-fpm$sfx" ] && sapis+=(fpm)
  [ -x "$d/php-cgi$sfx" ] && sapis+=(cgi)
  if [ -n "$v" ]; then
    mapfile -t exts < <(probe 10 "$bin" -m 2>/dev/null | awk '/^\[Zend Modules\]/{exit} /^[A-Za-z]/{print tolower($0)}' | sort -u)
    mapfile -t dirs < <(php_scan_dirs "$bin" 2>/dev/null)
  fi
  case $bin in
    /opt/cpanel/*|/opt/plesk/*|/www/server/*|/usr/local/lsws/*|/opt/alt/*) src=panel ;;
    /opt/remi/*|/opt/rh/*) src=scl ;;
    *) if (( IN_CONTAINER )); then src=docker; elif [ -n "$mgr" ]; then src=package; elif [ -n "$v" ]; then src=source_build; else src=unknown; fi ;;
  esac
  [ -n "$mgr" ] && (( IN_CONTAINER )) && src=docker
  local jpkg=null; [ -n "$mgr" ] && { jo manager=s:"$mgr" name=s:"$pkg" version=S:"$pver"; jpkg=$REPLY; }
  jas "${sapis[@]}"; local js_sapis=$REPLY
  jas ${dirs[@]+"${dirs[@]}"}; local js_dirs=$REPLY
  jas ${exts[@]+"${exts[@]}"}; local js_exts=$REPLY
  jo runtime_id=s:"$rid" kind=s:php bin=s:"$bin" version_raw=S:"$v" version=S:"$v" branch=S:"${v%.*}" \
     sapis=j:"$js_sapis" ini_scan_dirs=j:"$js_dirs" extensions=j:"$js_exts" owner_pkg=j:"$jpkg" \
     install_source=s:"$src" scenario_ids=j:"[]" state=s:"$st" locked=b:0 lock_reason=j:null \
     abi=j:null npm_version=j:null apps=j:"[]" site_ids=j:"[]"
  J_RUNTIMES+=("$REPLY")
  count_state "$st"
}

count_state() {
  case $1 in
    ok) BY_STATE_OK=$((BY_STATE_OK + 1)) ;; ok-backport) BY_STATE_BACKPORT=$((BY_STATE_BACKPORT + 1)) ;;
    vulnerable) BY_STATE_VULN=$((BY_STATE_VULN + 1)) ;; eol) BY_STATE_EOL=$((BY_STATE_EOL + 1)) ;;
    *) BY_STATE_UNKNOWN=$((BY_STATE_UNKNOWN + 1)) ;;
  esac
}

check_php() {
  head_ "PHP runtimes"
  local bins bin v st label rid before
  mapfile -t bins < <(discover_php_bins)
  if [ ${#bins[@]} -eq 0 ]; then note "No PHP binary found."; return; fi
  php_sapis_note
  for bin in "${bins[@]}"; do
    runtime_id php "$bin"; rid=$REPLY; CUR_REF="runtime:$rid"
    if ! v=$(php_version "$bin"); then
      msg ERR-SCN-422-01 "Unrecognized {runtime} version '{raw}'. Automation for this runtime is locked." runtime="PHP ($bin)" raw=""
      warn "$REPLY"; add_error ERR-SCN-422-01 "$REPLY"
      php_runtime_json "$bin" "" unknown; CUR_REF=""; continue
    fi
    st=$(php_state "$bin"); label="PHP $v ($bin)"; before=$v
    php_runtime_json "$bin" "$v" "$st"
    affected runtime "$rid" "PHP $v $bin"
    case $st in
      ok)          ok "$label is patched."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      ok-backport) ok "$label has the vendor backport for ${PHP_CVES[*]}."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      unknown)     warn "$label: newer than the advisory data, not checked." ;;
      vulnerable|eol)
        if [ "$st" = eol ]; then bad "$label is end-of-life upstream and has no ${PHP_CVES[*]} fix."
        else bad "$label is vulnerable to ${PHP_CVES[*]} (fixed in $(fixed_for "${v%.*}" "${PHP_FIXED[@]}"))."; fi
        if [ "$MODE" != fix ]; then issue critical "$label: PHP2Shell RCE"; CUR_REF=""; continue; fi
        if (( ! IS_ROOT )); then issue_c ERR-PTCH-403-01 critical "$label: needs root (or the hosting panel) to upgrade"; act runtime_patch skipped "needs root" ERR-PTCH-403-01; CUR_REF=""; continue; fi
        if php_upgrade "$bin" && (( ! DRY_RUN )); then
          st=$(php_state "$bin"); v=$(php_version "$bin")
          if [[ $st == ok* ]]; then
            local pv; pv=$(read -r m p <<<"$(pkg_owner "$bin")"; [ "${m:-}" = dpkg ] && dpkg-query -W -f=' (package ${Version})' "$p"; [ "${m:-}" = rpm ] && rpm -q --qf ' (package %{VERSION}-%{RELEASE})' "$p")
            ok "PHP $v$pv now has the fix ($st)"; fixed "PHP runtime $bin -> $v$pv"; RESTART_PHP=1
            act runtime_patch "done" "PHP $before -> $v$pv"
            jo runtime_id=s:"$rid" version_before=s:"$before" version_after=s:"$v" state_after=s:"$st"; J_RT_AFTER+=("$REPLY")
            php_unmitigate "$bin"; CUR_REF=""; continue
          fi
          warn "package upgrade did not bring a fixed PHP (still $v)."
          act runtime_patch failed "still $v" ERR-PTCH-424-01
          jo runtime_id=s:"$rid" version_before=s:"$before" version_after=s:"$v" state_after=s:"$st"; J_RT_AFTER+=("$REPLY")
        elif (( DRY_RUN )); then act runtime_patch planned "upgrade the packages of $bin"
        fi
        php_mitigate "$bin"
        issue_c ERR-PTCH-424-01 critical "$label: still unpatched, interim mitigation applied. Move to a supported branch (>= ${PHP_FIXED[0]%.*}) or a vendor backport."
        ;;
    esac
    CUR_REF=""
  done
}

# --- Node.js runtimes -----------------------------------------------------
discover_node_bins() {
  local c
  if [ -n "${QP_NODE_BINS:-}" ]; then
    for c in $QP_NODE_BINS; do readlink -f "$c" || echo "$c"; done | sort -u
    return
  fi
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
  change file modify "$prefix" "" "$ver" "install $tarball (SHASUMS256.txt checked)"
  if (( DRY_RUN )); then say "    [dry-run] install $tarball into $prefix"; return 0; fi
  fetch "$NODE_BASE_URL/v$ver/$tarball" "$WORK_DIR/$tarball" || { warn "download of $tarball failed"; return 1; }
  sums=$(fetch "$NODE_BASE_URL/v$ver/SHASUMS256.txt") || { rm -f "$WORK_DIR/$tarball"; return 1; }
  if ! (cd "$WORK_DIR" && grep " $tarball\$" <<<"$sums" | sha256sum -c --status); then
    rm -f "$WORK_DIR/$tarball"
    warn "checksum mismatch for $tarball"; NODE_ERR=ERR-PTCH-502-01; return 1
  fi
  ensure_backup_dir
  local saved parts=()
  saved="$BACKUP_DIR/node-$(echo "$prefix" | tr / _).tar.gz"
  local p; for p in bin include lib/node_modules/npm lib/node_modules/corepack share/doc/node; do [ -e "$prefix/$p" ] && parts+=("$p"); done
  tar -czf "$saved" -C "$prefix" "${parts[@]}" && record untar "$saved" "$prefix"
  run tar -xJf "$WORK_DIR/$tarball" -C "$prefix" --strip-components=1 --no-same-owner
}
NODE_ERR=""
REV_PARTIAL=0

node_upgrade() { # node_upgrade BIN MAJOR
  local bin=$1 major=$2 mgr pkg
  read -r mgr pkg <<<"$(pkg_owner "$bin")"
  case ${mgr:-} in
    dpkg)
      if (( ! APT_UPDATED )); then run apt-get update -q && APT_UPDATED=1; fi
      record note "apt upgraded: $pkg (not downgraded by rollback)"
      change package upgrade "$pkg" "" "" "apt-get install -y -q --only-upgrade"
      run env DEBIAN_FRONTEND=noninteractive apt-get install -y -q --only-upgrade "$pkg" ;;
    rpm)
      record note "rpm upgraded: $pkg (not downgraded by rollback)"
      change package upgrade "$pkg" "" "" "dnf/yum upgrade"
      if has dnf; then run dnf -y -q upgrade "$pkg"; else run yum -y -q update "$pkg"; fi ;;
    apk) change package upgrade "$pkg" "" "" "apk upgrade"; run apk upgrade --no-cache "$pkg" ;;
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

# node_runtime_json BIN VERSION STATE (FR-SCAN-RT-002)
node_runtime_json() {
  local bin=$1 v=$2 st=$3 rid mgr="" pkg="" pver="" src abi="" npmv="" prefix=${1%/bin/node}
  runtime_id node "$bin"; rid=$REPLY
  read -r mgr pkg <<<"$(pkg_owner "$bin")"
  [ -n "$mgr" ] && pver=$(pkg_version "$mgr" "$pkg")
  [ -n "$v" ] && abi=$(probe 10 "$bin" -p process.versions.modules 2>/dev/null)
  [ -r "$prefix/lib/node_modules/npm/package.json" ] && npmv=$(sed -n 's/^ *"version": *"\([^"]*\)".*/\1/p' "$prefix/lib/node_modules/npm/package.json" | head -n1)
  if (( IN_CONTAINER )); then src=docker
  elif [[ $bin == */.nvm/versions/node/* ]]; then src=nvm
  elif [[ $bin == /www/server/nodejs/* ]]; then src=panel
  elif [ -n "$mgr" ]; then if [[ $pver == *nodesource* ]]; then src=nodesource; else src=package; fi
  elif [ -d "$prefix/lib/node_modules/npm" ]; then src=tarball
  else src=unknown; fi
  local jpkg=null; [ -n "$mgr" ] && { jo manager=s:"$mgr" name=s:"$pkg" version=S:"$pver"; jpkg=$REPLY; }
  jo runtime_id=s:"$rid" kind=s:node bin=s:"$bin" version_raw=S:"$v" version=S:"$v" branch=S:"${v%%.*}" \
     sapis=j:"[]" ini_scan_dirs=j:"[]" extensions=j:"[]" owner_pkg=j:"$jpkg" install_source=s:"$src" \
     scenario_ids=j:"[]" state=s:"$st" locked=b:0 lock_reason=j:null abi=S:"$abi" npm_version=S:"$npmv" \
     apps=j:"[]" site_ids=j:"[]"
  J_RUNTIMES+=("$REPLY")
  count_state "$st"
}

check_node() {
  head_ "Node.js runtimes"
  local bins bin v st label major rid before
  mapfile -t bins < <(discover_node_bins)
  if [ ${#bins[@]} -eq 0 ]; then note "No Node.js binary found."; return; fi
  for bin in "${bins[@]}"; do
    runtime_id node "$bin"; rid=$REPLY; CUR_REF="runtime:$rid"
    if ! v=$(probe 10 "$bin" -v 2>/dev/null) || [ -z "$v" ]; then
      msg ERR-SCN-422-01 "Unrecognized {runtime} version '{raw}'. Automation for this runtime is locked." runtime="Node.js ($bin)" raw=""
      warn "$REPLY"; add_error ERR-SCN-422-01 "$REPLY"; node_runtime_json "$bin" "" unknown; CUR_REF=""; continue
    fi
    v=${v#v}; major=${v%%.*}; st=$(node_state "$v"); label="Node.js $v ($bin)"; before=$v
    node_runtime_json "$bin" "$v" "$st"; affected runtime "$rid" "Node.js $v $bin"
    case $st in
      ok) ok "$label is patched." ;;
      unknown) warn "$label: newer than the advisory data, not checked." ;;
      eol) bad "$label is end-of-life and gets no security fixes."
           issue high "$label: end-of-life, move to Node ${NODE_FIXED[-2]%%.*} or ${NODE_FIXED[-1]%%.*} LTS" ;;
      vulnerable)
        bad "$label is below the October 2026 security release ($(fixed_for "$major" "${NODE_FIXED[@]}"))."
        if [ "$MODE" != fix ]; then issue high "$label: unpatched"; CUR_REF=""; continue; fi
        if (( ! IS_ROOT )) && [[ $bin != "$HOME"/* ]]; then issue_c ERR-PTCH-403-01 high "$label: needs root to upgrade"; act runtime_patch skipped "needs root" ERR-PTCH-403-01; CUR_REF=""; continue; fi
        NODE_ERR=""
        if node_upgrade "$bin" "$major" && (( ! DRY_RUN )); then
          v=$("$bin" -v); v=${v#v}
          jo runtime_id=s:"$rid" version_before=s:"$before" version_after=s:"$v" state_after=s:"$(node_state "$v")"; J_RT_AFTER+=("$REPLY")
          if [ "$(node_state "$v")" = ok ]; then ok "upgraded to Node.js $v"; fixed "Node.js $bin -> $v"; act runtime_patch "done" "Node.js $before -> $v"; CUR_REF=""; continue; fi
        fi
        if (( DRY_RUN )); then act runtime_patch planned "upgrade Node.js $bin"
        else act runtime_patch failed "upgrade failed" "${NODE_ERR:-ERR-PTCH-424-01}"; issue_c "${NODE_ERR:-ERR-PTCH-424-01}" high "$label: upgrade failed, see $LOG"; fi ;;
    esac
    CUR_REF=""
  done
}

# --- Projects (Composer, npm, WordPress, Dockerfiles) ---------------------
PROJECT_FILES=()
declare -A PROJ_KINDS=() PROJ_LOCKS=()

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
  collect_projects
}

# Group project files by directory (FR-SCAN-PRJ-001).
collect_projects() {
  local f dir kind
  for f in ${PROJECT_FILES[@]+"${PROJECT_FILES[@]}"}; do
    dir=${f%/*}
    case ${f##*/} in
      composer.lock) kind=composer ;; package-lock.json) kind=npm ;; yarn.lock) kind=yarn ;; pnpm-lock.yaml) kind=pnpm ;;
      version.php) kind=wordpress; dir=${f%/wp-includes/version.php} ;;
      *) kind=docker ;;
    esac
    [[ " ${PROJ_KINDS[$dir]:-} " == *" $kind "* ]] || PROJ_KINDS[$dir]+="${PROJ_KINDS[$dir]:+ }$kind"
    [ "$kind" = wordpress ] || PROJ_LOCKS[$dir]+="${PROJ_LOCKS[$dir]:+$'\n'}$f"
  done
}

project_ref() { # project_ref PATH -> REPLY = project:<id> of the deepest project dir containing PATH
  local p=$1 best="" d
  for d in "${!PROJ_KINDS[@]}"; do
    [[ $p == "$d" || $p == "$d"/* ]] && (( ${#d} > ${#best} )) && best=$d
  done
  if [ -n "$best" ]; then REPLY="project:$(sha1_12 "$best")"; else REPLY=""; fi
}

projects_json() {
  local d kinds locks
  (( ${#PROJ_KINDS[@]} )) || return 0
  while IFS= read -r -d '' d; do
    # shellcheck disable=SC2086
    jas ${PROJ_KINDS[$d]}; kinds=$REPLY
    mapfile -t locks <<<"${PROJ_LOCKS[$d]:-}"; [ -n "${locks[0]:-}" ] || locks=()
    jas ${locks[@]+"${locks[@]}"}
    jo project_id=s:"$(sha1_12 "$d")" dir=s:"$d" owner=s:"$(stat -c %U "$d" 2>/dev/null || echo unknown)" kinds=j:"$kinds" site_id=j:null lockfiles=j:"$REPLY"
    J_PROJECTS+=("$REPLY")
  done < <(printf '%s\0' "${!PROJ_KINDS[@]}" | sort -z)
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

# dep_findings_json ECOSYSTEM HITS: one dependency_findings[] entry per hit
dep_findings_json() {
  local eco=$1 hits=$2 name ver ids sev mal advs
  [ -n "$hits" ] || return 0
  while read -r name ver ids; do
    [ -n "$name" ] || continue
    IFS=, read -r -a advs <<<"$ids"
    if [[ ",$ids" == *,MAL-* ]]; then mal=1; sev=critical; else mal=0; sev=high; fi
    jas "${advs[@]}"
    jo project_id=s:"${CUR_REF#project:}" ecosystem=s:"$eco" package=s:"$name" version=s:"$ver" advisories=j:"$REPLY" \
       severity=s:"$sev" in_kev=b:0 is_malware=b:$mal fixed_versions=j:"[]"
    J_DEPS+=("$REPLY"); VULN_PACKAGES=$((VULN_PACKAGES + 1))
  done <<<"$hits"
}

# Report and optionally fix vulnerable/malicious packages of one lockfile.
# audit_lockfile ECOSYSTEM LOCKFILE FIX_FN
audit_lockfile() {
  local eco=$1 lock=$2 fixfn=$3 dir=${2%/*} hits names mal
  project_ref "$lock"; CUR_REF=$REPLY
  if (( OFFLINE )); then warn "$lock: skipped (offline)"; return; fi
  local deps; deps=$(deps_of "$lock")
  if [ -z "$deps" ]; then warn "$lock: could not read packages (needs php, node or jq)"; return; fi
  if ! hits=$(osv_check "$eco" <<<"$deps"); then
    warn "$lock: OSV lookup failed (network or no php/node/jq)"; add_warning ERR-FEED-503-02 "$lock: OSV lookup failed"; return
  fi
  if [ -z "$hits" ]; then ok "$lock: no known vulnerable packages."; return; fi
  mal=$(awk '$3 ~ /(^|,)MAL-/' <<<"$hits")
  while read -r name ver ids; do bad "$dir: $name $ver -> $ids"; done <<<"$hits"
  [ "$MODE" = fix ] || dep_findings_json "$eco" "$hits"
  if [ "$MODE" = fix ]; then
    names=$(awk '{print $1}' <<<"$hits" | sort -u | tr '\n' ' ')
    # shellcheck disable=SC2086
    $fixfn "$dir" $names
    if (( ! DRY_RUN )); then
      local after; after=$(deps_of "$lock" | osv_check "$eco") || after="$hits"
      local n_before n_after
      n_before=$(grep -c . <<<"$hits"); n_after=$(grep -c . <<<"$after")
      (( n_after < n_before )) && fixed "$dir: $((n_before - n_after)) vulnerable $eco package(s) updated"
      hits=$after; mal=$(awk '$3 ~ /(^|,)MAL-/' <<<"$hits")
      [ -n "$hits" ] && while read -r name ver ids; do warn "still present: $name $ver ($ids)"; done <<<"$hits"
    fi
    dep_findings_json "$eco" "$hits"
  fi
  if [ -n "$mal" ]; then
    issue critical "$dir: MALWARE package(s) in lockfile: $(awk '{print $1"@"$2}' <<<"$mal" | tr '\n' ' ')- remove them, rotate every secret on this host (npm/GitHub tokens, SSH keys, .env)"
  fi
  local rest; rest=$(awk '$3 !~ /(^|,)MAL-/' <<<"$hits" | grep -c .)
  if (( rest > 0 )); then
    if [ "$MODE" = fix ]; then issue high "$dir: $rest vulnerable $eco package(s) left; they need a manual major upgrade"
    else issue high "$dir: $rest vulnerable $eco package(s)"; fi
  fi
  CUR_REF=""
  return 0
}

fix_composer() {
  local dir=$1; shift
  local cmd; cmd=$(composer_cmd) || { warn "composer not available"; act composer_update failed "composer not available" ERR-PTCH-424-02; return 1; }
  change file modify "$dir/composer.lock" "" "" "composer update $* --with-all-dependencies"
  affected project "${CUR_REF#project:}" "$dir"
  record composer-install "$dir"   # replayed after the restores (manifest runs in reverse)
  backup_file "$dir/composer.json"; backup_file "$dir/composer.lock"
  # shellcheck disable=SC2086
  if ! run_in_dir_as_owner "$dir" $cmd update "$@" --with-all-dependencies --no-interaction --no-progress; then
    warn "$dir: composer update failed, restoring composer.json/lock (see $LOG)"
    rollback_files_for "$dir/composer.json" "$dir/composer.lock"
    # shellcheck disable=SC2086
    run_in_dir_as_owner "$dir" $cmd install --no-interaction --no-progress
    act composer_update failed "$dir" ERR-PTCH-424-02
    issue_c ERR-PTCH-424-02 high "$dir: composer update failed, lockfile restored (see log)."
    return 1
  fi
  act composer_update "$( ((DRY_RUN)) && echo planned || echo "done")" "$dir: $*"
}

fix_npm() {
  local dir=$1; shift
  has npm || { warn "npm not available"; act npm_audit_fix failed "npm not available" ERR-PTCH-424-02; return 1; }
  change file modify "$dir/package-lock.json" "" "" "npm audit fix --no-fund"
  affected project "${CUR_REF#project:}" "$dir"
  record npm-ci "$dir"   # replayed after the restores (manifest runs in reverse)
  backup_file "$dir/package.json"; backup_file "$dir/package-lock.json"
  if run_in_dir_as_owner "$dir" npm audit fix --no-fund; then
    act npm_audit_fix "$( ((DRY_RUN)) && echo planned || echo "done")" "$dir"
  else
    warn "$dir: npm audit fix could not resolve everything (no --force used)"
    act npm_audit_fix failed "$dir" ERR-PTCH-424-02
  fi
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

# Back up WordPress core and the plugins about to be updated as tarballs
# (FR-PTCH-WP-001, CR-FR-03); rollback untars them over the site.
wp_backup() { # wp_backup SITE WP_CMD...
  local site=$1; shift
  local h tar plugins=() p roots=() need
  h=$(sha1_12 "$site")
  mapfile -t plugins < <(cd "$site" && run_capture_as_owner "$site" "$@" plugin list --update=available --field=name --path="$site" --skip-plugins --skip-themes --allow-root 2>/dev/null)
  roots=(wp-admin wp-includes); for p in "$site"/*.php; do [ -f "$p" ] && roots+=("${p##*/}"); done
  local dirs=("${roots[@]}"); for p in ${plugins[@]+"${plugins[@]}"}; do dirs+=("wp-content/plugins/$p"); done
  need=$(cd "$site" && du -skc "${dirs[@]}" 2>/dev/null | awk 'END{print $1}')
  REV_PARTIAL=1
  change file modify "$site" "" "" "wp core update --minor; wp plugin update --all --patch (core + ${#plugins[@]} plugin(s) backed up as tar)"
  if (( DRY_RUN )); then return 0; fi
  if ! space_for "${need:-0}"; then
    msg ERR-ENV-507-01 "Not enough disk space to back up before switching {site}." site="$site"
    warn "$REPLY"; issue_c ERR-ENV-507-01 high "$site: WordPress not updated, not enough space in $STATE_DIR for its backup"; return 1
  fi
  ensure_backup_dir
  tar="$BACKUP_DIR/files/wp-$h-core.tar.gz"
  record untar "$tar" "$site"
  tar -czf "$tar" -C "$site" "${roots[@]}" || return 1
  for p in ${plugins[@]+"${plugins[@]}"}; do
    [ -d "$site/wp-content/plugins/$p" ] || continue
    tar="$BACKUP_DIR/files/wp-$h-plugin-$p.tar.gz"
    record untar "$tar" "$site"
    tar -czf "$tar" -C "$site" "wp-content/plugins/$p" || return 1
  done
}

# run_capture_as_owner DIR CMD...: like run_in_dir_as_owner but keeps stdout
run_capture_as_owner() {
  local dir=$1; shift
  local owner home
  owner=$(stat -c %U "$dir" 2>/dev/null || echo root)
  if (( IS_ROOT )) && [ "$owner" != root ] && has runuser; then
    home=$(getent passwd "$owner" | cut -d: -f6)
    runuser -u "$owner" -- env HOME="${home:-/tmp}" "$@" 9>&- 3>&-
  else
    "$@" 9>&- 3>&-
  fi
}

wp_status_json() { # wp_status_json SITE VERSION FIX STATUS
  project_ref "$1"
  jo site_dir=s:"$1" project_id=S:"${REPLY#project:}" version=s:"$2" min_patched=S:"$3" status=s:"$4" advisories=j:"[]" in_kev=b:0 risk=j:null
  J_WP+=("$REPLY")
}

check_wordpress() {
  head_ "WordPress sites"
  local files f site v fix wp
  mapfile -t files < <(project_files version.php)
  [ ${#files[@]} -gt 0 ] || { note "No WordPress install found."; return; }
  for f in "${files[@]}"; do
    site=${f%/wp-includes/version.php}
    project_ref "$site"; CUR_REF=$REPLY
    v=$(sed -n "s/^\$wp_version *= *'\([^']*\)'.*/\1/p" "$f"); [ -n "$v" ] || continue
    if fix=$(fixed_for "${v%.*}" "${WP_FIXED[@]}") && ver_lt "$v" "$fix"; then
      bad "$site: WordPress $v is vulnerable to wp2shell RCE (fixed in $fix)."
      [ "$MODE" = fix ] || wp_status_json "$site" "$v" "$fix" vulnerable
    else
      ok "$site: WordPress $v is not in the wp2shell range."
      [ "$MODE" = fix ] || { wp_status_json "$site" "$v" "${fix:-}" ok; CUR_REF=""; continue; }
      fix=""
    fi
    if [ "$MODE" != fix ]; then [ -n "$fix" ] && issue critical "$site: WordPress $v wp2shell"; CUR_REF=""; continue; fi
    if ! wp=$(wp_cmd); then
      if [ -n "$fix" ]; then
        msg ERR-PTCH-424-03 "{site}: wp-cli unavailable, update WordPress core to {fix} by hand" site="$site" fix="$fix"
        issue_c ERR-PTCH-424-03 critical "$REPLY"; act wp_update failed "$REPLY" ERR-PTCH-424-03
      fi
      CUR_REF=""; continue
    fi
    # shellcheck disable=SC2086
    if ! wp_backup "$site" $wp; then CUR_REF=""; continue; fi
    affected project "${CUR_REF#project:}" "$site"
    # shellcheck disable=SC2086
    run_in_dir_as_owner "$site" $wp core update --minor --path="$site" --skip-plugins --skip-themes --allow-root
    # shellcheck disable=SC2086
    run_in_dir_as_owner "$site" $wp plugin update --all --patch --path="$site" --skip-themes --allow-root
    if (( DRY_RUN )); then act wp_update planned "$site"; CUR_REF=""; continue; fi
    v=$(sed -n "s/^\$wp_version *= *'\([^']*\)'.*/\1/p" "$f")
    if [ -n "$fix" ]; then
      if ver_lt "$v" "$fix"; then issue critical "$site: WordPress still $v after update attempt (see $LOG)"; act wp_update failed "$site still $v"; wp_status_json "$site" "$v" "$fix" vulnerable
      else ok "$site: WordPress updated to $v"; fixed "$site: WordPress -> $v"; act wp_update "done" "$site -> $v"; wp_status_json "$site" "$v" "$fix" ok; fi
    else wp_status_json "$site" "$v" "" ok
    fi
    # shellcheck disable=SC2086
    if ! (cd "$site" && $wp core verify-checksums --path="$site" --skip-plugins --skip-themes --allow-root >>"$LOG" 2>&1 9>&- 3>&-); then
      issue_c ERR-PTCH-424-04 high "$site: core files differ from wordpress.org checksums (possible tampering), see $LOG"
      act wp_verify failed "$site" ERR-PTCH-424-04
    else act wp_verify "done" "$site"
    fi
    # shellcheck disable=SC2086
    local unknown; unknown=$(cd "$site" && $wp plugin verify-checksums --all --path="$site" --skip-plugins --skip-themes --allow-root 2>&1 9>&- 3>&- | grep -iE 'could not retrieve|plugin .* not' | head -n 20)
    [ -n "$unknown" ] && warn "$site: plugins not verifiable against wordpress.org (check they are legitimate):" && say "$unknown"
    CUR_REF=""
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
    project_ref "$f"; CUR_REF=$REPLY
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
          if [ "$MODE" = fix ]; then line="$pre$img:$target$suffix"; changed=1; change file modify "$f" "$img:$ver" "$img:$target" "pin image tag"
          else issue high "$f: pin $img:$ver -> $target"; fi
        fi
      fi
      out+="$line"$'\n'
    done <"$f"
    if (( changed )); then
      if (( DRY_RUN )); then say "    [dry-run] rewrite image tags in $f"; act docker_tag planned "$f"
      elif ! space_for 1; then warn "$f not changed: not enough space in $STATE_DIR"; act docker_tag skipped "$f" ERR-ENV-507-01
      else backup_file "$f"; printf '%s' "$out" >"$f"; ok "$f: image tags bumped"; fixed "$f: image tags bumped"; act docker_tag "done" "$f"
           issue high "$f: rebuild and redeploy the image(s) to apply the new tag"; fi
    fi
    CUR_REF=""
  done
}

# Running containers on a Docker host.
check_containers() {
  (( HAS_DOCKER )) || return 0
  head_ "Running Docker containers"
  local id name image v nv st scan proj svc
  while read -r id name image; do
    [ -n "$id" ] || continue
    CUR_REF="container:$id"
    v=$(probe 10 docker exec "$id" sh -c 'php -n -r "echo PHP_VERSION;" 2>/dev/null' 2>/dev/null)
    [ $? = 124 ] && container_timeout "$name" php
    v=${v%%[^0-9.]*}
    nv=$(probe 10 docker exec "$id" sh -c 'node -v 2>/dev/null' 2>/dev/null)
    [ $? = 124 ] && container_timeout "$name" node
    nv=${nv#v}
    proj=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$id" 2>/dev/null)
    svc=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$id" 2>/dev/null)
    jo id=s:"$id" name=s:"$name" image=s:"$image" php_version=S:"$v" node_version=S:"$nv" compose_project=S:"$proj" compose_service=S:"$svc"
    J_CONTAINERS+=("$REPLY")
    if [ -n "$v" ]; then
      local fix; fix=$(fixed_for "${v%.*}" "${PHP_FIXED[@]}") || fix=""
      if [ -n "$fix" ] && ! ver_lt "$v" "$fix"; then ok "$name ($image): PHP $v patched"
      else
        bad "$name ($image): PHP $v unpatched; rebuild the image on a fixed base."
        issue critical "container $name: PHP $v (image $image) needs a rebuild"
        [ "$MODE" = fix ] && container_mitigate "$id" "$name" "$v"
      fi
    fi
    if [ -n "$nv" ]; then
      st=$(node_state "$nv")
      case $st in
        ok) ok "$name ($image): Node.js $nv patched" ;;
        unknown) note "$name: Node.js $nv not in advisory data" ;;
        *) bad "$name ($image): Node.js $nv $st; rebuild on a patched node image."; issue high "container $name: Node.js $nv ($st)" ;;
      esac
    fi
    CUR_REF=""
  done < <(docker ps --format '{{.ID}} {{.Names}} {{.Image}}' 2>/dev/null)
}

container_timeout() { # container_timeout NAME php|node: probe hit the 10 s limit (BR-SCAN-002)
  msg ERR-SCN-422-01 "Unrecognized {runtime} version '{raw}'. Automation for this runtime is locked." runtime="$2 in container $1" raw=""
  warn "$1: $2 version probe timed out after 10 s"; add_warning ERR-SCN-422-01 "$REPLY"
}

# Interim mitigation inside a running container (FR-PTCH-DKR-002, CR-FR-04):
# never overwrite an existing file; record docker-created before writing.
container_mitigate() { # container_mitigate ID NAME VERSION
  local id=$1 name=$2 v=$3 scan f
  scan=$(probe 10 docker exec "$id" sh -c 'php --ini 2>/dev/null' | sed -n 's/^Scan for additional .ini files in: *//p' | cut -d: -f1)
  if [ -z "$scan" ] || [ "$scan" = "(none)" ]; then
    msg ERR-PTCH-412-01 "No conf.d scan dir for {bin}; set the mitigation in its php.ini by hand." bin="container $name"
    warn "$REPLY"; add_warning ERR-PTCH-412-01 "$REPLY"; act container_mitigation failed "$name" ERR-PTCH-412-01; return
  fi
  f="$scan/$PHP_MITIGATION_FILE"
  if docker exec "$id" test -e "$f" 2>/dev/null; then note "$name: mitigation already present: $f"; act container_mitigation skipped "$name: $f exists"; return; fi
  change file create "$name:$f" "" "" "interim mitigation in container"; affected container "$id" "$name"
  if (( DRY_RUN )); then say "    [dry-run] write $f in $name and restart it"; act container_mitigation planned "$name:$f"; return; fi
  record docker-created "$id" "$f"
  if php_mitigation_ini "$v" | docker exec -i "$id" sh -c "cat > '$f'" 9>&- 3>&-; then
    note "$name: interim mitigation written to $scan (kept across restarts, lost on recreate)"
    act container_mitigation "done" "$name:$f"
    (( NO_RESTART )) || { run docker restart "$id" && jo unit=s:"container:$name" status=s:restarted && J_RESTARTS+=("$REPLY"); }
  fi
}

# Report likely webshells; never deletes anything (FR-SCAN-WSH-001, BR-SEC-003).
WSH_RULES=(
  'eval_decode|eval[[:space:]]*\([[:space:]]*(base64_decode|gzinflate|gzuncompress|str_rot13|\$_(POST|GET|REQUEST|COOKIE))'
  'assert_input|assert[[:space:]]*\([[:space:]]*\$_(POST|GET|REQUEST|COOKIE)'
  'exec_input|(system|shell_exec|passthru|exec|popen|proc_open)[[:space:]]*\([[:space:]]*\$_(GET|POST|REQUEST|COOKIE)'
  "preg_replace_e|preg_replace[[:space:]]*\\(.*/e[\"']"
)

check_webshells() {
  head_ "Webshell indicators"
  local dirs=() f hits=() uploads=() r pat=""
  for f in ${PROJECT_FILES[@]+"${PROJECT_FILES[@]}"}; do
    case ${f##*/} in composer.lock|package-lock.json) dirs+=("${f%/*}") ;; version.php) dirs+=("${f%/wp-includes/version.php}") ;; esac
  done
  [ ${#dirs[@]} -gt 0 ] || { note "No project directories to scan."; return; }
  mapfile -t dirs < <(printf '%s\n' "${dirs[@]}" | sort -u)
  for r in "${WSH_RULES[@]}"; do pat+="${pat:+|}${r#*|}"; done
  mapfile -t hits < <(find "${dirs[@]}" \( -name node_modules -o -name vendor -o -name .git \) -prune -o -type f -name '*.php' -size -2097152c -print0 2>/dev/null \
      | xargs -0 -r grep -lsE "$pat" 2>/dev/null | head -n 50)
  mapfile -t uploads < <(find "${dirs[@]}" -path '*/wp-content/uploads/*' -type f -name '*.ph*' 2>/dev/null | head -n 50)
  local all; mapfile -t all < <(printf '%s\n' ${hits[@]+"${hits[@]}"} ${uploads[@]+"${uploads[@]}"} | sed '/^$/d' | sort -u)
  if [ ${#all[@]} -eq 0 ]; then ok "No webshell patterns found."; return; fi
  local rule sum mt sz
  for f in "${all[@]}"; do
    bad "suspicious: $f"
    rule=php_in_uploads
    for r in "${WSH_RULES[@]}"; do grep -qsE "${r#*|}" "$f" 2>/dev/null && { rule=${r%%|*}; break; }; done
    sum=$(sha256sum "$f" 2>/dev/null | cut -c1-64)
    read -r mt sz < <(stat -c '%Y %s' "$f" 2>/dev/null)
    mt=$(date -u -d "@${mt:-0}" +%Y-%m-%dT%H:%M:%SZ)
    project_ref "$f"
    jo path=s:"$f" rule=s:"$rule" sha256=s:"$sum" mtime=s:"$mt" size=n:"${sz:-0}" project_id=S:"${REPLY#project:}"
    J_WSH+=("$REPLY")
  done
  issue critical "${#all[@]} suspicious PHP file(s): review them; if confirmed, treat the host as compromised (patching does not remove backdoors)"
}

# --- Service restarts (FR-PTCH-RST-001) -----------------------------------
# verify_active SERVICE CHECK...: poll CHECK every second for up to 15 s.
verify_active() {
  local svc=$1 waited=0; shift
  if (( DRY_RUN )); then return 0; fi
  while ! "$@" >/dev/null 2>&1 9>&- 3>&-; do
    if (( waited >= 15 )); then
      jo service=s:"$svc" active=b:0 waited_s=n:15; J_RESTARTED+=("$REPLY")
      jo service=s:"$svc" check=s:"$*" waited_s=n:15 error_code=s:ERR-PTCH-500-01; J_RESTART_FAIL+=("$REPLY")
      jo unit=s:"$svc" status=s:failed; J_RESTARTS+=("$REPLY")
      log "service=$svc check='$*' waited_s=15 active=false"
      msg ERR-PTCH-500-01 "Service {service} is not running 15 seconds after restart; sites may be down. Check its log, then run rollback {run_id} if needed." service="$svc" run_id="${RUN_ID:-<run_id>}"
      warn "$REPLY"; printf '%s\n' "$REPLY" >&2
      add_error ERR-PTCH-500-01 "$REPLY" "host"
      CUR_REF=host issue_c ERR-PTCH-500-01 critical "$svc is not active after restart; check it, then run: $0 rollback ${RUN_ID:-<run_id>}"
      RESTART_FAILED=1
      return 1
    fi
    sleep 1; waited=$((waited + 1))
  done
  jo service=s:"$svc" active=b:1 waited_s=n:$waited; J_RESTARTED+=("$REPLY")
  jo unit=s:"$svc" status=s:restarted; J_RESTARTS+=("$REPLY")
}

restart_php_services() {
  (( RESTART_PHP )) || return 0
  head_ "Restarting PHP services"
  if (( NO_RESTART )); then
    warn "--no-restart: restart PHP-FPM and the web server yourself to load the changes."; issue high "PHP services not restarted"
    jo unit=s:php status=s:skipped_no_restart; J_RESTARTS+=("$REPLY"); return
  fi
  local n=0 u s
  if [ "$PANEL" = cpanel ]; then
    for s in apache_php_fpm httpd; do
      change service restart "restartsrv_$s"
      if run "/scripts/restartsrv_$s"; then n=$((n + 1)); verify_active "restartsrv_$s" "/scripts/restartsrv_$s" --check; fi
    done
  elif (( HAS_SYSTEMD )); then
    for u in $(systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null | awk '{print $1}' \
              | grep -E '^(php[0-9.]*-fpm|php-fpm[0-9.]*|php[0-9]+-php-fpm|ea-php[0-9]+-php-fpm|rh-php[0-9]+-php-fpm|plesk-php[0-9.]+-fpm|apache2|httpd|lsws|lshttpd|lsws-[a-z]+)\.service$'); do
      change service restart "$u"
      run systemctl restart "$u" && note "restarted $u" && n=$((n + 1)) && verify_active "$u" systemctl is-active --quiet "$u"
    done
  else
    for s in /etc/init.d/php-fpm*; do
      [ -x "$s" ] || continue
      change service restart "$s"
      run "$s" restart && n=$((n + 1)) && verify_active "${s##*/}" pgrep -f 'php-fpm: master'
    done
    if pgrep -f 'php-fpm: master' >/dev/null; then
      change service reload php-fpm
      run pkill -USR2 -f 'php-fpm: master' && n=$((n + 1)) && verify_active php-fpm pgrep -f 'php-fpm: master'
    fi
    if has apachectl && pgrep -x apache2 >/dev/null; then change service restart apache2; run apachectl -k restart && n=$((n + 1)) && verify_active apache2 pgrep -x apache2; fi
    if has httpd && pgrep -x httpd >/dev/null; then change service restart httpd; run httpd -k restart && n=$((n + 1)) && verify_active httpd pgrep -x httpd; fi
  fi
  if [ -x /usr/local/lsws/bin/lswsctrl ]; then
    change service restart lsws
    # Not verified on a real LiteSpeed host: the check below is a best guess.
    run /usr/local/lsws/bin/lswsctrl restart && n=$((n + 1)) && verify_active lsws pgrep -f 'litespeed|lshttpd'
  fi
  (( n > 0 )) || warn "No running PHP-FPM/web server found to restart; restart them by hand if they run elsewhere."
  return 0
}

pm2_all_online() { local j; j=$(pm2 jlist 2>/dev/null) || return 1; [ "$(grep -o '"status":"[a-z_]*"' <<<"$j" | grep -vc '"status":"online"')" -eq 0 ]; }

restart_node_services() {
  [ ${#RESTART_NODE_PREFIXES[@]} -gt 0 ] || return 0
  head_ "Restarting Node.js services"
  if (( NO_RESTART )); then
    warn "--no-restart: restart your Node.js apps to load the new runtime."; issue high "Node.js apps not restarted"
    jo unit=s:node status=s:skipped_no_restart; J_RESTARTS+=("$REPLY"); return
  fi
  local p u restarted=0
  if (( HAS_SYSTEMD )); then
    for p in "${RESTART_NODE_PREFIXES[@]}"; do
      for u in $(grep -lsE "ExecStart=.*(${p}/bin/(node|npm)|pm2)" /etc/systemd/system/*.service | xargs -r -n1 basename); do
        if systemctl is-active -q "$u"; then
          change service restart "$u"
          run systemctl restart "$u" && note "restarted $u" && restarted=1 && verify_active "$u" systemctl is-active --quiet "$u"
        fi
      done
    done
  fi
  if has pm2 && pm2 pid >/dev/null 2>&1; then
    change pm2 reload all
    run pm2 reload all && note "pm2 reload all" && restarted=1 && verify_active pm2 pm2_all_online
  fi
  (( restarted )) || warn "No systemd/pm2 Node service found; restart your Node.js apps by hand."
  return 0
}

# --- Rollback -------------------------------------------------------------
rollback_files_for() { # restore specific files from the current run's backups
  local f src
  for f in "$@"; do
    src="$BACKUP_DIR/files$(readlink -f "$f")"
    [ -f "$src" ] && cp -a "$src" "$f"
  done
}

# reversible ACTION ARG1: full | partial | none for planned_actions[]
reversible_of() {
  case $1 in
    note) REPLY=none ;;
    untar) case ${2##*/} in wp-*.tar.gz) REPLY=partial ;; *) REPLY=full ;; esac ;;
    *) REPLY=full ;;
  esac
}

# Replay a run's manifest in reverse. The run directory and its manifest are
# checked like STATE_DIR before a single line is read (FR-PTCH-RBK-002);
# with --dry-run every step is only printed.
do_rollback() {
  local base="$STATE_DIR/backups" dir r
  if [ -n "$ROLLBACK_ID" ]; then
    if ! [[ $ROLLBACK_ID =~ ^[0-9]{8}-[0-9]{6}$ ]]; then
      fatal ERR-CLI-400-01 "Invalid rollback ID: {arg} (expected YYYYmmdd-HHMMSS)" arg="$ROLLBACK_ID"
    fi
    dir="$base/$ROLLBACK_ID"
  else
    local c; dir=""
    for c in "$base"/[0-9]*-[0-9]*; do [[ ${c##*/} =~ ^[0-9]{8}-[0-9]{6}$ ]] && dir=$c; done   # glob order = oldest first
  fi
  if [ -z "$dir" ] || { [ ! -e "$dir/manifest" ] && [ ! -L "$dir/manifest" ]; }; then
    msg ERR-PTCH-404-01 "No backup run found in {dir}" dir="$base"; say "$REPLY"
    add_error ERR-PTCH-404-01 "$REPLY"; finish 2
  fi
  r=$(unsafe_reason "$dir" dir) && state_dir_fail "$dir" "$r"
  r=$(unsafe_reason "$dir/manifest" file) && state_dir_fail "$dir/manifest" "$r"
  RUN_ID=${dir##*/}
  head_ "Rolling back $(basename "$dir")$( ((DRY_RUN)) && echo ' (dry-run)')"
  (( DRY_RUN )) || audit_intent rollback_run
  local action a b seq=0 st
  while IFS=$'\t' read -r action a b; do
    [ -n "$action" ] || continue
    seq=$((seq + 1)); st="done"
    if (( DRY_RUN )); then
      if [ "$action" = note ]; then warn "$a"; else say "    [dry-run] $action $a${b:+ $b}"; fi
      reversible_of "$action" "$a"
      jo action=s:"$action" arg1=S:"$a" arg2=S:"$b" reversible=s:"$REPLY"; J_PLANNED+=("$REPLY")
      case $action in created) RESTART_PHP=1 ;; untar) [ -e "$b/bin/node" ] && RESTART_NODE_PREFIXES+=("$b") ;; esac
      st=planned
    else
      case $action in
        copy)    cp -a "$b" "$a" && note "restored $a" || st=failed ;;
        created) rm -f "$a" && note "removed $a" || st=failed; RESTART_PHP=1 ;;
        untar)   if tar -xzf "$a" -C "$b"; then note "restored $b from ${a##*/}"; [ -e "$b/bin/node" ] && RESTART_NODE_PREFIXES+=("$b"); else st=failed; fi ;;
        docker-created)
          if ! docker inspect "$a" >/dev/null 2>&1; then warn "container $a no longer exists; skipped removing $b"; st=skipped
          elif docker exec "$a" rm -f "$b" 9>&- 3>&-; then note "removed $b in container $a"; (( NO_RESTART )) || run docker restart "$a"
          else st=failed; fi ;;
        composer-install) local cmd; if cmd=$(composer_cmd); then
                            # shellcheck disable=SC2086
                            run_in_dir_as_owner "$a" $cmd install --no-interaction --no-progress && note "composer install in $a" || st=failed
                          else st=failed; fi ;;
        npm-ci)  run_in_dir_as_owner "$a" npm ci --no-fund --no-audit && note "npm ci in $a" || st=failed ;;
        note)    warn "$a" ;;
        *)       warn "unknown manifest action '$action' skipped"; st=skipped ;;
      esac
    fi
    local args=("$a"); [ -n "$b" ] && args+=("$b")
    jas "${args[@]}"; jo seq=n:$seq action=s:"$action" args=j:"$REPLY" status=s:"$st"; J_MANIFEST+=("$REPLY")
  done < <(tac "$dir/manifest")
  restart_php_services; restart_node_services
  if (( DRY_RUN )); then say "Dry-run: nothing was changed."
  else say "Rollback done. Package upgrades (apt/dnf/yum) are kept."; fi
  local code=0; (( RESTART_FAILED )) && code=2
  (( DRY_RUN )) || audit_result rollback_run "$code"
  fix_result_json; finish "$code" "$REPLY"
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
  msg ERR-CLI-412-01 "State directory {path} is unsafe ({reason}); aborting." path="$1" reason="$2"
  local m=$REPLY
  printf '%s [ERR-CLI-412-01] path=%s reason=%s uid=%s euid=%s\n' "$m" "$1" "$2" "$uid" "$EUID" >&2
  add_error ERR-CLI-412-01 "$m (path=$1 reason=$2 uid=$uid euid=$EUID)" host
  finish 2
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

# --- Audit log (FR-JOB-AUD-001, BR-AUD-001..006) --------------------------
# One JSON line per record in STATE_DIR/audit/audit-YYYYMM.jsonl, keys in
# alphabetical order, hash = SHA-256(prev_hash || record without "hash").
# The same canonical form is produced by qplib/audit.py.
AUDIT_ARGS_JSON="[]"

audit_args() {
  local a out=()
  for a in ${ARGV_ORIG[@]+"${ARGV_ORIG[@]}"}; do redact "$a"; out+=("$(printf '%s' "$REPLY" | iconv -f UTF-8 -t UTF-8 -c 2>/dev/null || printf '%s' "$REPLY")"); done
  jas ${out[@]+"${out[@]}"}; AUDIT_ARGS_JSON=$REPLY
}

# audit_write TYPE ACTION RESULT EXIT_CODE: append one record; REPLY = "seq hash"
audit_write() {
  local type=$1 action=$2 result=${3:-} code=${4:-} dir="$STATE_DIR/audit"
  [ -d "$dir" ] || mkdir -m 0700 "$dir" 2>/dev/null || return 1
  local out
  out=$(
    umask 077; exec 8>>"$dir/.lock" || exit 1
    flock -x -w 5 8 || exit 1
    last="" prev=$(printf '%064d' 0) seq=0
    files=("$dir"/audit-[0-9][0-9][0-9][0-9][0-9][0-9].jsonl)
    for ((i = ${#files[@]} - 1; i >= 0; i--)); do
      [ -s "${files[i]}" ] && { last=$(tail -n1 "${files[i]}"); break; }
    done
    if [ -n "$last" ]; then
      [[ $last =~ [,{]\"hash\":\"([0-9a-f]{64})\" ]] && prev=${BASH_REMATCH[1]}
      [[ $last =~ [,{]\"seq\":([0-9]+)[,}] ]] && seq=${BASH_REMATCH[1]}
    fi
    seq=$((seq + 1))
    ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
    user=$(id -un 2>/dev/null || echo "$EUID")
    actor=${QP_ACTOR:-cli:$user}; source=cli; [ -n "${QP_JOB_ID:-}" ] && source=console
    q() { if [ -z "$1" ]; then REPLY=null; else _js "$1"; fi; }
    q "$action"; j_action=$REPLY; q "$actor"; j_actor=$REPLY; q "${QP_JOB_ID:-}"; j_job=$REPLY
    q "${AUDIT_PLAN_ID:-}"; j_plan=$REPLY; q "$result"; j_result=$REPLY; q "${RUN_ID:-}"; j_run=$REPLY
    q "$user"; j_user=$REPLY; q "$source"; j_source=$REPLY; q "$type"; j_type=$REPLY
    j_code=${code:-null}
    head="{\"action\":$j_action,\"actor\":$j_actor,\"args\":$AUDIT_ARGS_JSON,\"exit_code\":$j_code"
    tail=",\"job_id\":$j_job,\"plan_id\":$j_plan,\"prev_hash\":\"$prev\",\"record_type\":$j_type,\"result\":$j_result,\"run_id\":$j_run,\"seq\":$seq,\"source\":$j_source,\"sys_user\":$j_user,\"ts\":\"$ts\"}"
    h=$(printf '%s%s%s' "$prev" "$head" "$tail" | sha256sum | cut -c1-64)
    file="$dir/audit-$(date -u +%Y%m).jsonl"
    (umask 077; printf '%s,"hash":"%s"%s\n' "$head" "$h" "$tail" >>"$file") || exit 1
    sync "$file" 2>/dev/null
    echo "$seq $h"
  ) || return 1
  REPLY=$out
}

# audit_intent ACTION: BR-AUD-004 - no intent record, no change.
audit_intent() {
  audit_args
  if ! audit_write INTENT "$1" "" ""; then
    msg ERR-AUD-500-01 "Could not write the audit log; the change was cancelled."
    printf '%s\n' "$REPLY" >&2; add_error ERR-AUD-500-01 "$REPLY" host; finish 2
  fi
}

# audit_result ACTION EXIT_CODE: retried 3 times, 1 s apart (BR-AUD-004).
audit_result() {
  local res=ok try; [ "$2" = 2 ] && res=failed
  for try in 1 2 3 4; do
    if audit_write RESULT "$1" "$res" "$2"; then
      local s h; read -r s h <<<"$REPLY"; J_AUDIT_ANCHOR="{\"seq\":$s,\"hash\":\"$h\"}"; return 0
    fi
    (( try < 4 )) && sleep 1
  done
  msg ERR-AUD-500-01 "Could not write the audit log; the change was cancelled."
  printf 'audit result not written: %s\n' "$REPLY" >&2; add_error ERR-AUD-500-01 "audit result record not written" host
}

# --- JSON results ----------------------------------------------------------
scan_result_json() {
  projects_json
  local rt pr ct dp wp ws fp
  jarr J_RUNTIMES; rt=$REPLY; jarr J_PROJECTS; pr=$REPLY; jarr J_CONTAINERS; ct=$REPLY
  jarr J_DEPS; dp=$REPLY; jarr J_WP; wp=$REPLY; jarr J_WSH; ws=$REPLY
  local kev=0
  jo runtimes=n:${#J_RUNTIMES[@]} by_state=j:"{\"ok\":$BY_STATE_OK,\"ok_backport\":$BY_STATE_BACKPORT,\"vulnerable\":$BY_STATE_VULN,\"eol\":$BY_STATE_EOL,\"unknown\":$BY_STATE_UNKNOWN}" \
     eol_within_90d=n:0 kev_findings=n:$kev critical_issues=n:$CRITICAL vulnerable_packages=n:$VULN_PACKAGES
  local summary=$REPLY
  fp=$(printf '%s\n' ${J_RUNTIMES[@]+"${J_RUNTIMES[@]}"} | grep -o '"bin":"[^"]*"\|"version":"[^"]*"' | sha256sum | cut -c1-64)
  env_json; local envj=$REPLY
  jo scan_fingerprint=s:"$fp" environment=j:"$envj" runtimes=j:"$rt" sites=j:"[]" projects=j:"$pr" containers=j:"$ct" \
     dependency_findings=j:"$dp" wordpress_findings=j:"$wp" webshell_findings=j:"$ws" drift_warnings=j:"[]" \
     ranking=j:"[]" plan_deadlines=j:"[]" summary=j:"$summary"
  SCAN_FP=$fp
}
SCAN_FP=""

env_json() {
  local os_id="" os_ver=""
  [ -r /etc/os-release ] && { os_id=$(. /etc/os-release && echo "${ID:-}"); os_ver=$(. /etc/os-release && echo "${VERSION_ID:-}"); }
  jo os_id=S:"$os_id" os_version=S:"$os_ver" pkg_mgr=s:"$PKG_MGR" panel=s:"$PANEL" has_systemd=b:$HAS_SYSTEMD \
     has_docker=b:$HAS_DOCKER in_container=b:$IN_CONTAINER is_root=b:$IS_ROOT web_servers=j:"[]" playbooks=j:"[]" restrictions=j:"[]"
}

fix_result_json() {
  local only=() IFS=, p a m r rd rf c pv="" fpj=""
  read -r -a only <<<"$ONLY"; IFS=$' \t\n'
  jas ${only[@]+"${only[@]}"}; local jonly=$REPLY
  jas ${SCAN_PATHS[@]+"${SCAN_PATHS[@]}"}; p=$REPLY
  jo only=j:"$jonly" paths=j:"$p" no_restart=b:$NO_RESTART no_memlimit=b:$NO_MEMLIMIT; local scope=$REPLY
  jarr J_ACTIONS; a=$REPLY; jarr J_RT_AFTER; local ra=$REPLY; jarr J_MITIG; m=$REPLY
  jarr J_RESTARTS; r=$REPLY; jarr J_RESTARTED; rd=$REPLY; jarr J_RESTART_FAIL; rf=$REPLY
  jo fixed=n:$FIXED open_issues=n:$ISSUES critical=n:$CRITICAL; c=$REPLY
  local run_id="" hint=""
  if (( ! DRY_RUN )) && [ -n "$BACKUP_DIR" ] && [ "$MODE" = fix ]; then run_id=$RUN_ID; hint="$0 rollback $RUN_ID"; fi
  if (( DRY_RUN )); then
    local ch af level=full notes=() scope_d=none
    jarr J_CHANGES; ch=$REPLY; jarr J_AFFECTED; af=$REPLY
    (( REV_PARTIAL )) && { level=partial; notes+=("WordPress database changes of an update are not undone by rollback"); }
    [[ $ch == *'"type":"package"'* ]] && { level=partial; notes+=("Packages upgraded with apt/dnf/yum/apk are not downgraded by rollback"); }
    [[ $ch == *'"type":"service"'* || $ch == *'"type":"pm2"'* ]] && scope_d=runtime
    [ "$MODE" = rollback ] && level=full
    jas ${notes[@]+"${notes[@]}"}
    jo level=s:"$level" rollback_command=S:"$( [ "$MODE" = fix ] && echo "$0 rollback <run_id>")" notes=j:"$REPLY"; local rev=$REPLY
    jo expected_s=j:null scope=s:"$scope_d" basis=s:"restart/reload of the listed services"; local dis=$REPLY
    jo changes=j:"$ch" affected=j:"$af" disruption=j:"$dis" reversibility=j:"$rev" requires_retype=j:null; pv=$REPLY
    jo bundle_id=j:null scan_fingerprint=S:"$SCAN_FP" catalog_version=j:null; fpj=$REPLY
  fi
  local extra=""
  if [ "$MODE" = rollback ]; then
    jarr J_MANIFEST; extra+=",\"manifest\":$REPLY"
    if (( DRY_RUN )); then jarr J_PLANNED; extra+=",\"planned_actions\":$REPLY"; fi
  fi
  jo run_id=S:"$run_id" scope=j:"$scope" actions=j:"$a" runtimes_after=j:"$ra" mitigations=j:"$m" restarts=j:"$r" \
     restarted=j:"$rd" restart_failures=j:"$rf" counts=j:"$c" rollback_hint=S:"$hint"
  REPLY=${REPLY%\}}$extra
  [ -n "$pv" ] && REPLY+=",\"preview\":$pv,\"fingerprint\":$fpj"
  REPLY+="}"
}

# --- Other commands --------------------------------------------------------
cmd_schema() {
  local name=${SCHEMA_ARG//\//.} f
  case $name in rollback) name=fix ;; feeds|"feeds status") name=feeds.status ;; esac
  f="$SHARE_DIR/schemas/qp.$name.v1.schema.json"
  if [ -z "$SCHEMA_ARG" ] || [[ ! $name =~ ^[a-z]+(\.[a-z]+)*$ ]] || [ ! -f "$f" ]; then
    fatal ERR-CLI-400-01 "Unknown argument: {arg}" arg="schema ${SCHEMA_ARG:-}"
  fi
  if (( JSON )); then
    jo command=s:"$name" schema_file=s:"${f#"$SHARE_DIR"/}" schema=j:"$(cat "$f")"; finish 0 "$REPLY"
  fi
  cat "$f"; exit 0
}

# Commands implemented in Python (qp-feeds.py, console): FR-CLI-ENV-001 (3)
run_python() {
  local py="" v target="$SHARE_DIR/qp-feeds.py"
  [ "$MODE" = serve ] && target="$SHARE_DIR/console/qp-console.py"
  if has python3; then
    v=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
    [ -n "$v" ] && ! ver_lt "$v" 3.6 && py=python3
  fi
  if [ -z "$py" ]; then
    fatal ERR-CLI-424-01 "{command} requires Python 3.6+." command="$MODE"
  fi
  if [ -z "$SHARE_DIR" ] || [ ! -f "$target" ]; then
    fatal ERR-CLI-424-01 "{command} is not installed ({file} missing)." command="$MODE" file="$target"
  fi
  (( JSON )) && exec 1>&3 3>&-
  exec "$py" -I "$target" --script "$SCRIPT_PATH" "$MODE" ${PASS_ARGS[@]+"${PASS_ARGS[@]}"}
}

# FR-CLI-SAFE-001: new write commands ask y/N on a TTY, need --yes otherwise.
confirm() { # confirm COMMAND_NAME
  (( DRY_RUN || ASSUME_YES )) && return 0
  if [ -t 0 ]; then
    local a; read -r -p "$1: apply these changes? [y/N] " a </dev/tty || a=""
    [[ $a == [yY]* ]] && return 0
    say "Nothing was changed."; finish 1
  fi
  fatal ERR-CLI-428-01 "{command} needs --yes when not interactive." command="$1"
}

# --- Main -----------------------------------------------------------------
parse_args() {
  while [ $# -gt 0 ]; do
    case $1 in
      scan|fix) MODE=$1 ;;
      rollback) MODE=rollback; if [ $# -gt 1 ] && [[ $2 != -* ]]; then ROLLBACK_ID=$2; shift; fi ;;
      schema) MODE=schema; [ $# -ge 2 ] || arg_error ""; SCHEMA_ARG=$2; shift ;;
      feeds|assess|plan|report|audit|serve|sync|snapshot)
        MODE=$1; [ "$MODE" = sync ] && { MODE=feeds; PASS_ARGS=(update); }
        [ "$MODE" = snapshot ] && MODE=feeds
        shift; PASS_ARGS+=("$@")
        local a; for a in "$@"; do [ "$a" = --json ] && JSON=1; done
        return ;;
      migrate|upgrade|switch-site|healthcheck|rollback-site)
        MODE=migrate; shift; local a; for a in "$@"; do [ "$a" = --json ] && JSON=1; done
        PASS_ARGS=("$@"); return ;;
      --path) [ $# -ge 2 ] || arg_error ""; SCAN_PATHS+=("$(readlink -f "$2")"); shift ;;
      --only) [ $# -ge 2 ] || arg_error ""; ONLY=$2; shift ;;
      --dry-run) DRY_RUN=1 ;;
      --no-restart) NO_RESTART=1 ;;
      --no-memlimit) NO_MEMLIMIT=1 ;;
      --offline) OFFLINE=1 ;;
      --json) JSON=1 ;;
      --json-schema) [ $# -ge 2 ] || arg_error ""; [ "$2" = 1 ] || arg_error "--json-schema $2"; shift ;;
      --yes|-y) ASSUME_YES=1 ;;
      --version) echo "php-quickpatch $QP_VERSION"; exit 0 ;;
      -h|--help) usage; exit 0 ;;
      *) arg_error "$1" ;;
    esac
    shift
  done
}

want() { [[ ",$ONLY," == *",$1,"* ]]; }

# BR-ENV-013: a write command never runs while a site switch holds its lock.
check_switch_locks() {
  local f
  for f in "$STATE_DIR"/switches/*.lock; do
    [ -e "$f" ] || continue
    if ! flock -n "$f" true 2>/dev/null; then
      msg ERR-ENV-409-01 "A site switch is in progress ({file}); try again when it ends." file="$f"
      if (( DRY_RUN )); then warn "$REPLY"; add_warning ERR-ENV-409-01 "$REPLY"; else fatal ERR-ENV-409-01 "$REPLY"; fi
    fi
  done
}

main() {
  parse_args "$@"
  if (( JSON )); then exec 3>&1 1>&2; else exec 3>/dev/null; fi
  has flock || fatal ERR-CLI-424-02 "Bash 4.3+, flock and curl are required (found: {detail})." detail="bash $BASH_VERSION, flock no, curl $(has curl && echo yes || echo no)"
  case $MODE in
    schema) cmd_schema ;;
    feeds|assess|plan|report|audit|serve) run_python ;;
    migrate) fatal ERR-CLI-400-01 "{arg} is not available in this build yet (milestone M5)." arg=migrate ;;
  esac
  select_state_dir
  LOG="$STATE_DIR/php-quickpatch.log"
  (umask 077; : >>"$LOG") 2>/dev/null
  local w; for w in ${STATE_WARN[@]+"${STATE_WARN[@]}"}; do log "WARN: $w"; done
  WORK_DIR=$(mktemp -d) || exit 2
  trap 'flock -u 9 2>/dev/null; rm -rf "$WORK_DIR"' EXIT
  exec 9>"$STATE_DIR/.lock"
  local kind=-x; { (( DRY_RUN )) || [ "$MODE" = scan ]; } && kind=-s
  if ! flock "$kind" -n 9; then
    msg ERR-CLI-423-01 "Another php-quickpatch run is in progress."
    echo "$REPLY" >&2; add_error ERR-CLI-423-01 "$REPLY" host; finish 2
  fi
  [ "$MODE" != scan ] && check_switch_locks

  say "${C_B}php-quickpatch $QP_VERSION${C_0} mode=$MODE$( ((DRY_RUN)) && echo ' (dry-run)') log=$LOG"
  if (( JSON )); then add_warning ERR-FEED-503-01 "No feeds bundle yet: advisory data built into this version is used."; fi
  if [ "$MODE" = rollback ]; then detect_env; do_rollback; fi

  [ "$MODE" = fix ] && (( ! DRY_RUN )) && audit_intent fix
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
  local s; for s in ${SUMMARY[@]+"${SUMMARY[@]}"}; do say "  - $s"; done
  say "  fixed: $FIXED | open issues: $ISSUES (critical: $CRITICAL)"
  [ -n "$BACKUP_DIR" ] && say "  rollback: $0 rollback $(basename "$BACKUP_DIR")"
  [ "$MODE" = scan ] && (( ISSUES > 0 )) && say "  run '$0 fix' to apply the fixes."
  local code=0
  (( ISSUES > 0 )) && code=1
  (( RESTART_FAILED )) && code=2
  if [ "$MODE" = fix ]; then
    (( DRY_RUN )) || audit_result fix "$code"
    scan_result_json >/dev/null; fix_result_json; finish "$code" "$REPLY"
  fi
  scan_result_json; finish "$code" "$REPLY"
}

# Run unless sourced (tests source the file to call single functions).
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
