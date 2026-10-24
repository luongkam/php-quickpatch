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

QP_VERSION="2.0.0-alpha.3"

# --- Advisory data ----------------------------------------------------------
# Patched versions, CVEs and lifecycle come from the normalized feeds bundle
# (STATE_DIR/feeds/current, FR-CLI-COMP-002). SHA-256 pin of the packaged
# snapshot share/php-quickpatch/feeds-snapshot.tar.gz (FR-FEED-SNAP-001);
# set by the release pipeline (FR-FEED-SNAP-004). Empty: no packaged snapshot.
QP_SNAPSHOT_SHA256=""

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
ONLY="php,node,composer,npm,wp,docker,webshell,sites"
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
  jo bundle_id=S:"$DATA_BUNDLE_ID" freshness=S:"$DATA_FRESHNESS" data_age_h=n:"$DATA_AGE_H" stale_sources=j:"$DATA_STALE"; local data=$REPLY
  jarr J_ISSUES; local issues=$REPLY; jarr J_ERRORS; local errors=$REPLY; jarr J_WARNINGS; local warnings=$REPLY
  local now; now=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  jo schema=s:"$schema" schema_version=s:"1.0.0" tool=j:'{"name":"php-quickpatch","version":"'"$QP_VERSION"'"}' \
     generated_at=s:"$now" host=j:"$host" command=j:"$cmd" dry_run=b:$DRY_RUN exit_code=n:"$code" \
     data=j:"$data" catalog_version=S:"$CATALOG_VERSION" result=j:"$result" issues=j:"$issues" errors=j:"$errors" \
     warnings=j:"$warnings" audit_anchor=j:"$J_AUDIT_ANCHOR"
  local doc=$REPLY
  # Paths may hold bytes that are not UTF-8: drop them so the document stays valid.
  if has iconv && ! printf '%s' "$doc" | iconv -f UTF-8 -t UTF-8 >/dev/null 2>&1; then
    doc=$(printf '%s' "$doc" | iconv -f UTF-8 -t UTF-8 -c)
  fi
  printf '%s\n' "$doc" >&3
  # The newest scan result for assess/plan and the console (DOC-API-QP-005 §5).
  if [ "$MODE" = scan ] && [ "$result" != null ] && [ -n "$STATE_DIR" ] && [ -d "$STATE_DIR" ]; then
    (umask 077; mkdir -p "$STATE_DIR/state" && printf '%s\n' "$doc" >"$STATE_DIR/state/.last-scan.$$" \
      && mv -f "$STATE_DIR/state/.last-scan.$$" "$STATE_DIR/state/last-scan.json") 2>/dev/null
  fi
  return 0
}

# finish CODE [RESULT_JSON]: emit the envelope when --json, then exit.
finish() {
  local code=$1
  if (( JSON )) || [ "$MODE" = scan ]; then emit_envelope "$code" "${2:-null}"; fi
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

sha1_12() { printf '%s' "$1" | sha1sum | cut -c1-12; }
runtime_id() { REPLY="$1:$(sha1_12 "$2")"; }   # runtime_id php|node PATH

# probe SECONDS CMD...: run a read-only probe with a time limit (BR-SCAN-002)
probe() { local t=$1; shift; if has timeout; then timeout "$t" "$@"; else "$@"; fi; }

# run CMD...: execute (or print in dry-run), output goes to the log. The
# lock fd 9 and the JSON fd 3 are closed so no child keeps them (BR-JOB-002).
run() {
  if (( DRY_RUN )); then say "    [dry-run] $*"; return 0; fi
  log "+ $*"
  "$@" >>"$LOG" 2>&1 9>&- 3>&- 7<&-
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

# --- Feeds bundle (FR-CLI-COMP-002, DOC-SRS-QP-FEED-003 §2.5, §3.4) ------
# scan/fix read the normalized bundle feeds/current/*.tsv with awk, so they
# work without Python (C-01). The bundle path is resolved once per run and a
# shared flock on its .lock is held on fd 7 until exit (BR-FEED-051).
FEEDS_DIR=""; QP_FEEDS_BUNDLE=""; TODAY=""; TODAY_DAY=0
DATA_BUNDLE_ID=""; DATA_FRESHNESS=""; DATA_AGE_H=""; DATA_STALE="[]"; DATA_LINE=""
BUNDLE_ERR=""
# Scheduled sources whose age counts for data_age_h (SRC-013 is optional).
COUNTED_SOURCES=" SRC-001 SRC-002 SRC-003 SRC-004 SRC-006 SRC-008 SRC-009 SRC-010 SRC-011 SRC-012 "

# iso_epoch YYYY-MM-DD[THH:MM:SS[Z]]: REPLY = seconds since 1970 (UTC), pure Bash.
iso_epoch() {
  [[ $1 =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})(T([0-9]{2}):([0-9]{2}):([0-9]{2}))? ]] || return 1
  local y=$((10#${BASH_REMATCH[1]})) m=$((10#${BASH_REMATCH[2]})) d=$((10#${BASH_REMATCH[3]}))
  local H=$((10#${BASH_REMATCH[5]:-0})) M=$((10#${BASH_REMATCH[6]:-0})) S=$((10#${BASH_REMATCH[7]:-0}))
  local era yoe doy doe
  (( m <= 2 )) && y=$((y - 1))
  era=$(( (y >= 0 ? y : y - 399) / 400 )); yoe=$(( y - era * 400 ))
  doy=$(( (153 * (m > 2 ? m - 3 : m + 9) + 2) / 5 + d - 1 )); doe=$(( yoe * 365 + yoe / 4 - yoe / 100 + doy ))
  REPLY=$(( (era * 146097 + doe - 719468) * 86400 + H * 3600 + M * 60 + S ))
}

# feeds_dir_ready: STATE_DIR/feeds (0755 root, 0700 otherwise) and its subdirs.
feeds_dir_ready() {
  local r mode=0700; (( IS_ROOT )) && mode=0755
  FEEDS_DIR="$STATE_DIR/feeds"
  if [ ! -e "$FEEDS_DIR" ] && [ ! -L "$FEEDS_DIR" ]; then mkdir -m "$mode" -- "$FEEDS_DIR" 2>/dev/null || return 1; fi
  r=$(unsafe_reason "$FEEDS_DIR" dir) && { [ "$r" = mode ] && (( IS_ROOT )) || { BUNDLE_ERR="feeds dir $FEEDS_DIR is unsafe ($r)"; FEEDS_DIR=""; return 1; }; }
  mkdir -p -- "$FEEDS_DIR"/{raw,parts,cache,bundles,state,snapshots} 2>/dev/null
  return 0
}

# manifest_field FILE KEY: top-level "key": "value" of a bundle manifest (indent 1).
manifest_field() { sed -n "s/^ \"$2\": \"\\([^\"]*\\)\".*/\\1/p" "$1" 2>/dev/null | head -n1; }

# bundle_swap DIR ID: W2-W5 of BR-FEED-051 for a checked bundle directory.
bundle_swap() {
  local dir=$1 id=$2 old b keep1 keep2
  [ -e "$FEEDS_DIR/bundles/$id" ] && return 1
  : >"$dir/.lock"
  mv -- "$dir" "$FEEDS_DIR/bundles/$id" || return 1
  old=$(readlink "$FEEDS_DIR/current" 2>/dev/null)
  rm -f "$FEEDS_DIR/.current.new"; ln -s "bundles/$id" "$FEEDS_DIR/.current.new" && mv -T "$FEEDS_DIR/.current.new" "$FEEDS_DIR/current" || return 1
  if [ -n "$old" ] && [ "$old" != "bundles/$id" ]; then
    rm -f "$FEEDS_DIR/.previous.new"; ln -s "$old" "$FEEDS_DIR/.previous.new" && mv -T "$FEEDS_DIR/.previous.new" "$FEEDS_DIR/previous"
  fi
  keep1=$(basename "$(readlink "$FEEDS_DIR/current")"); keep2=$(basename "$(readlink "$FEEDS_DIR/previous" 2>/dev/null)")
  for b in "$FEEDS_DIR"/bundles/*; do
    [ -d "$b" ] || continue
    case ${b##*/} in "$keep1"|"$keep2") continue ;; esac
    if [ -f "$b/.lock" ]; then flock -n -x "$b/.lock" rm -rf -- "$b" 2>/dev/null; else rm -rf -- "$b"; fi
  done
  return 0
}

# bundle_install_packaged: BR-FEED-053/054 without Python. The packaged
# snapshot is used when there is no current bundle or it is newer; it must
# match QP_SNAPSHOT_SHA256, be a safe tar and match every SHA256SUMS line
# (BR-FEED-010), otherwise ERR-FEED-422-02 and it is not used.
bundle_install_packaged() {
  local snap="$SHARE_DIR/feeds-snapshot.tar.gz" gen cur_gen sum work id total
  [ -n "$SHARE_DIR" ] && [ -f "$snap" ] || return 0
  gen=$(tar -xzOf "$snap" manifest.json 2>/dev/null | sed -n 's/^ "generated_at": "\([^"]*\)".*/\1/p' | head -n1)
  [ -n "$gen" ] || return 0
  if [ -L "$FEEDS_DIR/current" ]; then
    cur_gen=$(manifest_field "$FEEDS_DIR/current/manifest.json" generated_at)
    [ -n "$cur_gen" ] && [[ ! $gen > $cur_gen ]] && return 0
  fi
  sum=$(sha256sum "$snap" | awk '{print $1}')
  if [ -z "$QP_SNAPSHOT_SHA256" ] || [ "$sum" != "$QP_SNAPSHOT_SHA256" ]; then
    msg ERR-FEED-422-02 "The data snapshot does not match its SHA-256; it was rejected."
    warn "$REPLY ($snap)"; add_warning ERR-FEED-422-02 "$REPLY (expected=${QP_SNAPSHOT_SHA256:-unset} actual=$sum)" host
    return 0
  fi
  # Refuse links, devices, absolute paths, '..' and more than 50 MB unpacked (§4.3).
  if tar -tvzf "$snap" 2>/dev/null | awk '{ if (substr($1,1,1) != "-" && substr($1,1,1) != "d") bad=1; t += $3 } END { exit (bad || t > 52428800) }' &&
     ! tar -tzf "$snap" 2>/dev/null | grep -qE '(^/|(^|/)\.\.(/|$))'; then :; else
    msg ERR-FEED-422-02 "The data snapshot does not match its SHA-256; it was rejected."
    warn "$REPLY (unsafe archive $snap)"; add_warning ERR-FEED-422-02 "$REPLY (unsafe archive)" host; return 0
  fi
  exec 6>>"$FEEDS_DIR/.lock"
  flock -w 10 6 || { exec 6>&-; return 0; }
  work=$(mktemp -d "$FEEDS_DIR/staging-snapshot.XXXXXX") || { exec 6>&-; return 0; }
  if tar -xzf "$snap" -C "$work" --no-same-owner 2>/dev/null &&
     (cd "$work" && sha256sum -c --quiet --strict SHA256SUMS >/dev/null 2>&1) &&
     (cd "$work/bundle" && sha256sum -c --quiet --strict SHA256SUMS >/dev/null 2>&1) &&
     id=$(manifest_field "$work/bundle/manifest.json" bundle_id) && [[ $id =~ ^b-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$ ]] &&
     total=$(awk '{print $2}' "$work/SHA256SUMS" | sed 's#^bundle/##' | sort | tr '\n' ' ') &&
     [ "$total" = "$(cd "$work/bundle" && for n in * .[!.]*; do [ -e "$n" ] && echo "$n"; done | sort | tr '\n' ' ')" ] &&
     bundle_swap "$work/bundle" "$id"; then
    rm -f "$FEEDS_DIR"/parts/* "$FEEDS_DIR"/state/{nvd-cursor,counts,sync-status}.json
    printf '{"generated_at": "%s", "sha256": "%s", "type": "snapshot"}\n' "$gen" "$sum" >"$FEEDS_DIR/state/base.json"
    log "packaged snapshot $gen installed as bundle $id"
  else
    msg ERR-FEED-422-02 "The data snapshot does not match its SHA-256; it was rejected."
    warn "$REPLY ($snap: SHA256SUMS)"; add_warning ERR-FEED-422-02 "$REPLY (SHA256SUMS)" host
  fi
  rm -rf -- "$work"
  exec 6>&-
}

# python_ok: Python 3.6+ and qp-feeds.py are available (BR-FEED-012).
python_ok() {
  [ -n "$SHARE_DIR" ] && [ -f "$SHARE_DIR/qp-feeds.py" ] && has python3 || return 1
  local v; v=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null) || return 1
  ! ver_lt "$v" 3.6
}

# qp_py ARGS...: run an internal qp-feeds.py command (stdout = its output).
qp_py() { python3 -I "$SHARE_DIR/qp-feeds.py" --script "$SCRIPT_PATH" "$@" 9>&- 3>&-; }

# sources_due: true when an enabled source is older than its TTL (BR-FEED-001 (a)).
sources_due() {
  local cur="$FEEDS_DIR/current/sources.tsv" now
  [ -f "$cur" ] || return 0
  now=$(date -u +%s)
  local src st ok ttl
  while IFS=$'\t' read -r src _ _ st ok ttl _; do
    [[ $src == SRC-* ]] || continue
    [[ $COUNTED_SOURCES == *" $src "* ]] && [ "$st" != DISABLED ] || continue
    iso_epoch "$ok" || continue          # never fetched: nothing to refresh from age
    (( now - REPLY > ${ttl:-6} * 3600 )) && return 0
  done < <(awk -F'\t' -v OFS='\t' 'NR > 1 { for (i = 1; i <= NF; i++) if ($i == "") $i = "-"; print }' "$cur")
  return 1
}

# bundle_open: packaged snapshot, refresh when stale (<= 120 s), resolve and lock.
bundle_open() {
  TODAY=$(date -u +%F); iso_epoch "$TODAY"; TODAY_DAY=$((REPLY / 86400))
  feeds_dir_ready || return 0
  bundle_install_packaged
  if (( ! OFFLINE )) && python_ok && sources_due; then
    note "refreshing CVE/lifecycle data (feeds update, at most 120 s)..."
    if has timeout; then timeout 130 python3 -I "$SHARE_DIR/qp-feeds.py" --script "$SCRIPT_PATH" feeds update --quiet --budget 110 >>"$LOG" 2>&1 9>&- 3>&-
    else python3 -I "$SHARE_DIR/qp-feeds.py" --script "$SCRIPT_PATH" feeds update --quiet --budget 110 >>"$LOG" 2>&1 9>&- 3>&-; fi
  fi
  local i real root
  root=$(readlink -f "$FEEDS_DIR/bundles")
  for i in 1 2 3; do
    [ -L "$FEEDS_DIR/current" ] || break
    real=$(readlink -f "$FEEDS_DIR/current") || break
    [ "${real%/*}" = "$root" ] || break
    if { exec 7<"$real/.lock"; } 2>/dev/null; then
      flock -s 7; QP_FEEDS_BUNDLE=$real; export QP_FEEDS_BUNDLE; break
    fi
  done
  [ -n "$QP_FEEDS_BUNDLE" ] && bundle_freshness
}

# bundle_freshness: data_age_h, freshness and stale sources (BR-FEED-005, FR-FEED-AGE-001).
bundle_freshness() {
  local now src name st ok ttl err age lvl worst=0 oldest=-1 oldest_src="" oldest_name="" oldest_err=""
  local -a stale=()
  now=$(date -u +%s)
  DATA_BUNDLE_ID=$(manifest_field "$QP_FEEDS_BUNDLE/manifest.json" bundle_id)
  while IFS=$'\t' read -r src name _ st ok ttl err _; do
    [[ $src == SRC-* ]] || continue
    [[ $COUNTED_SOURCES == *" $src "* ]] && [ "$st" != DISABLED ] && [ "$ok" != - ] || continue
    iso_epoch "$ok" || continue
    age=$(( (now - REPLY) / 3600 )); (( age < 0 )) && age=0
    if (( age <= ttl )); then lvl=0; elif (( age <= 168 )); then lvl=1; elif (( age <= 2160 )); then lvl=2; else lvl=3; fi
    (( lvl > worst )) && worst=$lvl
    if (( age > oldest )); then oldest=$age; oldest_src=$src; oldest_name=$name; oldest_err=${err#-}; fi
    if (( age > ttl )); then jo src_id=s:"$src" age_h=n:$age last_error=S:"${err#-}"; stale+=("$age"$'\t'"$REPLY"); fi
  done < <(awk -F'\t' -v OFS='\t' 'NR > 1 { for (i = 1; i <= NF; i++) if ($i == "") $i = "-"; print }' "$QP_FEEDS_BUNDLE/sources.tsv")
  local levels=(FRESH AGING STALE EXPIRED) s out=""
  if (( oldest < 0 )); then DATA_FRESHNESS=""; DATA_AGE_H=""; else DATA_FRESHNESS=${levels[$worst]}; DATA_AGE_H=$oldest; fi
  while IFS=$'\t' read -r _ s; do [ -n "$s" ] && out+="${out:+,}$s"; done < <(printf '%s\n' ${stale[@]+"${stale[@]}"} | sort -t$'\t' -k1,1nr)
  DATA_STALE="[$out]"
  DATA_LINE="CVE/lifecycle data: bundle $DATA_BUNDLE_ID"
  [ -n "$DATA_AGE_H" ] && DATA_LINE+=" - data $DATA_AGE_H h old (oldest source: $oldest_src $oldest_name${oldest_err:+, error $oldest_err})"
}

# bundle_report: the data line under Environment (§3.5) and STALE/EXPIRED warnings.
bundle_report() {
  if [ -z "$QP_FEEDS_BUNDLE" ]; then
    msg ERR-FEED-503-01 "Could not get data from {source}; using {origin} ({age_h} h old)." source="feeds (no bundle, no snapshot)" origin="nothing" age_h="-"
    warn "$REPLY Runtimes are reported as unknown."; add_error ERR-FEED-503-01 "$REPLY" host
    [ -n "$BUNDLE_ERR" ] && warn "$BUNDLE_ERR"
    return 0
  fi
  case $DATA_FRESHNESS in
    STALE)
      local since; since=$(date -u -d "@$(( $(date -u +%s) - DATA_AGE_H * 3600 ))" +%F 2>/dev/null)
      warn "$DATA_LINE. Results may miss CVEs published after ${since:-the data date}."
      msg ERR-FEED-412-01 "Data used for this assessment is {age_d} days old (sources: {sources})." age_d=$((DATA_AGE_H / 24)) sources="$(sed -n 's/.*"src_id":"\(SRC-[0-9]*\)".*/\1/p' <<<"${DATA_STALE//\},/$'}\n'}" | paste -sd, -)"
      add_warning ERR-FEED-412-01 "$REPLY" host ;;
    EXPIRED)
      warn "$DATA_LINE."
      msg ERR-SCN-503-01 "Lifecycle data is {days} days old; branch upgrade proposals are paused." days=$((DATA_AGE_H / 24))
      warn "$REPLY"; add_warning ERR-SCN-503-01 "$REPLY" host ;;
    *) note "$DATA_LINE" ;;
  esac
}

# tsv_row FILE K1 K2: first row whose columns 1 and 2 are K1 K2 (REPLY, tab-separated).
tsv_row() { REPLY=$(awk -F'\t' -v a="$2" -v b="$3" '$1 == a && $2 == b { print; exit }' "$QP_FEEDS_BUNDLE/$1" 2>/dev/null); [ -n "$REPLY" ]; }

# branch_of PRODUCT VERSION -> REPLY
branch_of() { if [ "$1" = node ]; then REPLY=${2%%.*}; [ "$REPLY" = 0 ] && REPLY=0.$(cut -d. -f2 <<<"$2"); else REPLY=$(cut -d. -f1-2 <<<"$2"); fi; }

# bundle_exposure PRODUCT VERSION [EXCLUDE_CSV]: unpatched advisories of one
# version (exposure.tsv, else matched on affected.tsv), summarized like
# normalize.summarize. REPLY = "n_c n_h n_m n_l cvss10 n_kev ids sec_ids found"
bundle_exposure() {
  local p=$1 v=$2 ex=${3:-}
  REPLY=$(awk -F'\t' -v p="$p" -v v="$v" -v ex=",$ex," '
    function vcmp(a, b,   x, y, n, m, i, k, xa, yb) {
      n = split(a, x, /[^0-9]+/); m = split(b, y, /[^0-9]+/); k = (n > m ? n : m)
      for (i = 1; i <= k; i++) { xa = (i <= n && x[i] != "" ? x[i] + 0 : 0); yb = (i <= m && y[i] != "" ? y[i] + 0 : 0)
        if (xa < yb) return -1; if (xa > yb) return 1 }
      return 0 }
    function hit(  c) {
      if ($12 != "1" || $9 != "any" || $10 == "1" || $2 != p) return 0
      if ($3 == "NODE_WG") { semver = 1; return 0 }
      if ($16 != "" && index(v, $16) != 1) return 0
      if ($8 != "") return vcmp(v, $8) == 0
      if ($4 != "") { c = vcmp(v, $4); if (c < 0 || (c == 0 && $5 == "0")) return 0 }
      if ($6 != "") { c = vcmp(v, $6); if (c > 0 || (c == 0 && $7 == "0")) return 0 }
      return 1 }
    FILENAME ~ /advisories.tsv$/ { if ($4 == p) { st[$1] = $3; kind[$1] = $2; rep[$1] = $5; kev[$1] = $7 } ; next }
    FILENAME ~ /exposure.tsv$/ { if ($1 == p && $2 == v) { found = 1; n = split($9, a, ","); for (i = 1; i <= n; i++) if (a[i] != "") ids[a[i]] = 1 } ; next }
    !found && FNR > 1 && hit() { ids[$1] = 1 }
    END {
      for (id in ids) {
        if (index(ex, "," id ",")) continue
        if (st[id] == "REJECTED" || st[id] == "WITHDRAWN" || kind[id] == "MALWARE") continue
        s = rep[id]; if (s == "") s = "7.5"
        split(s, q, "."); c10 = q[1] * 10 + q[2]
        if (c10 >= 90) nc++; else if (c10 >= 70) nh++; else if (c10 >= 40) nm++; else if (c10 >= 1) nl++
        if (c10 > max) max = c10
        if (kev[id] == "1") nk++
        all = all (all == "" ? "" : ",") id
        if (c10 >= 70 || kev[id] == "1") sec = sec (sec == "" ? "" : ",") id
      }
      printf "%d %d %d %d %d %d %s %s %d\n", nc, nh, nm, nl, max, nk, (all == "" ? "-" : all), (sec == "" ? "-" : sec), (found || !semver) ? 1 : 0
    }' "$QP_FEEDS_BUNDLE/advisories.tsv" "$QP_FEEDS_BUNDLE/exposure.tsv" "$QP_FEEDS_BUNDLE/affected.tsv" 2>/dev/null)
  [ -n "$REPLY" ] || REPLY="0 0 0 0 0 0 - - 0"
}

# lifecycle_status PRODUCT VERSION: DOC-SRS-QP-SCN-000 §2.1 (same rules as risk.py). REPLY.
lifecycle_status() {
  local p=$1 v=$2 b ga lts sup eol pre phpnet
  if [[ $v =~ (alpha|beta|RC|rc|-dev|-pre|nightly) ]]; then REPLY=PRE_RELEASE; return; fi
  branch_of "$p" "$v"; b=$REPLY
  tsv_row lifecycle.tsv "$p" "$b" || { REPLY=UNKNOWN; return; }
  ga=$(cut -f3 <<<"$REPLY"); lts=$(cut -f4 <<<"$REPLY"); sup=$(cut -f5 <<<"$REPLY")
  eol=$(cut -f6 <<<"$REPLY"); pre=$(cut -f7 <<<"$REPLY"); phpnet=$(cut -f8 <<<"$REPLY")
  if [ "$p" = wordpress ]; then
    local newest mp
    newest=$(awk -F'\t' '$1 == "wordpress" { print $3 }' "$QP_FEEDS_BUNDLE/releases.tsv" | sort -V | tail -n1 | cut -d. -f1-2)
    tsv_row min_patched.tsv wordpress "$b" && mp=$(cut -f3 <<<"$REPLY")
    if [ "${mp:-}" = NONE ]; then REPLY=EOL
    elif [ "$newest" = "$b" ]; then REPLY=ACTIVE
    elif awk -F'\t' -v b="$b" '$1 == "wordpress" && $2 == b && ($6 == "latest" || $6 == "outdated") { f = 1 } END { exit !f }' "$QP_FEEDS_BUNDLE/releases.tsv"; then REPLY=SECURITY_ONLY
    elif [ -n "$eol" ] && [[ $eol < $TODAY ]]; then REPLY=EOL
    else REPLY=UNKNOWN; fi
    return
  fi
  if [ -n "$eol" ] && [[ $TODAY > $eol ]] && ! { [ "$p" = php ] && [ "$phpnet" = 1 ]; }; then REPLY=EOL; return; fi
  if [ -n "$ga" ] && [[ $TODAY < $ga ]]; then REPLY=PRE_RELEASE; return; fi
  if [ -z "$ga" ] && [ -n "$pre" ]; then REPLY=PRE_RELEASE; return; fi
  [ -n "$ga" ] || { REPLY=UNKNOWN; return; }
  if [ "$p" = node ]; then
    if [ -z "$lts" ] || [[ $TODAY < $lts ]]; then REPLY=CURRENT
    elif [ -z "$sup" ] || [[ ! $TODAY > $sup ]]; then REPLY=ACTIVE_LTS
    else REPLY=MAINTENANCE_LTS; fi
    return
  fi
  if [ -n "$sup" ] && [[ $TODAY > $sup ]]; then REPLY=SECURITY_ONLY; else REPLY=ACTIVE; fi
}

t10() { REPLY="$(( $1 / 10 )).$(( $1 % 10 ))"; }   # 392 -> 39.2

# risk_score STATUS DAYS(or -) NC NH NM NL NKEV CVSS10: BR-FEED-040/041 in
# integer tenths, same arithmetic as risk.py. Sets RISK_R RISK_LEVEL RISK_PRIO RISK_JSON.
risk_score() {
  local st=$1 d=$2 nc=$3 nh=$4 nm=$5 nl=$6 nk=$7 c10=$8 s_cvss s_cnt s_kev s_life s_eol r10 floor
  s_cvss=$((4 * c10)); s_cnt=$((40 * nc + 20 * nh + 5 * nm + nl)); (( s_cnt > 200 )) && s_cnt=200
  s_kev=0; (( nk >= 1 )) && s_kev=200
  case $st in ACTIVE|ACTIVE_LTS|CURRENT) s_life=0 ;; SECURITY_ONLY|MAINTENANCE_LTS) s_life=50 ;; PRE_RELEASE) s_life=80 ;; *) s_life=100 ;; esac
  if [ "$d" = - ] || (( d > 365 )); then s_eol=0; elif (( d < 0 )); then s_eol=100; elif (( d <= 90 )); then s_eol=80
  elif (( d <= 180 )); then s_eol=50; else s_eol=20; fi
  r10=$((s_cvss + s_cnt + s_kev + s_life + s_eol))
  if [ "$st" = UNKNOWN ] || { [ "$d" != - ] && (( d < -365 )); } || (( nk > 0 )); then RISK_PRIO=CRITICAL
  elif { [ "$d" != - ] && (( d >= -365 && d <= 90 )); } || (( c10 >= 70 )); then RISK_PRIO=HIGH
  elif [[ $st == SECURITY_ONLY || $st == MAINTENANCE_LTS ]] && { [ "$d" = - ] || (( d > 90 )); }; then RISK_PRIO=MEDIUM
  elif [[ $st == ACTIVE || $st == ACTIVE_LTS || $st == CURRENT ]] && [ "$d" != - ] && (( d <= 365 )); then RISK_PRIO=MEDIUM
  else RISK_PRIO=LOW; fi
  case $RISK_PRIO in CRITICAL) floor=70 ;; HIGH) floor=40 ;; MEDIUM) floor=20 ;; *) floor=0 ;; esac
  RISK_R=$(( (r10 + 5) / 10 )); (( RISK_R < floor )) && RISK_R=$floor
  if (( RISK_R >= 70 )); then RISK_LEVEL=CRITICAL; elif (( RISK_R >= 40 )); then RISK_LEVEL=HIGH
  elif (( RISK_R >= 20 )); then RISK_LEVEL=MEDIUM; else RISK_LEVEL=LOW; fi
  local c k l e f; t10 $s_cvss; c=$REPLY; t10 $s_cnt; k=$REPLY; t10 $s_kev; l=$REPLY; t10 $s_life; e=$REPLY; t10 $s_eol; f=$REPLY
  t10 $r10
  RISK_JSON="{\"R\":$RISK_R,\"score\":$RISK_R,\"level\":\"$RISK_LEVEL\",\"components\":{\"S_cvss\":$c,\"S_cnt\":$k,\"S_kev\":$l,\"S_life\":$e,\"S_eol\":$f,\"floor\":$floor,\"R_raw\":$REPLY}}"
}

# assess PRODUCT VERSION [MANAGER PACKAGE]: lookups of one runtime version.
# Sets A_STATE (ok|ok-backport|vulnerable|eol|unknown), A_LC, A_EOL, A_DAYS,
# A_MIN, A_LATEST, A_DRIVERS (space list), A_SEC, A_RISK, A_PRIO, A_BACKPORT, ...
assess() {
  local p=$1 v=$2 mgr=${3:-} pkg=${4:-} b nc nh nm nl c10 nk ids sec excl="" offline=()
  A_STATE=unknown; A_LC=UNKNOWN; A_EOL=""; A_DAYS=""; A_MIN=""; A_LATEST=""; A_DRIVERS=""; A_SEC=""; A_IDS=""
  A_RISK=null; A_PRIO=""; A_BACKPORT=null; A_LTS=""; A_CODENAME=""
  (( OFFLINE )) && offline=(--offline)
  [ -n "$QP_FEEDS_BUNDLE" ] && [ -n "$v" ] || return 0
  branch_of "$p" "$v"; b=$REPLY
  lifecycle_status "$p" "$v"; A_LC=$REPLY
  [ -n "$ASSESS_LC" ] && A_LC=$ASSESS_LC   # raw version is pre-release/abnormal (BR-SCN-040, BR-SCN-020)
  if tsv_row lifecycle.tsv "$p" "$b"; then
    A_EOL=$(cut -f6 <<<"$REPLY"); A_LTS=$(cut -f4 <<<"$REPLY"); A_CODENAME=$(cut -f11 <<<"$REPLY")
    if [ -n "$A_EOL" ] && iso_epoch "$A_EOL"; then A_DAYS=$(( REPLY / 86400 - TODAY_DAY )); fi
  fi
  if tsv_row min_patched.tsv "$p" "$b"; then
    A_MIN=$(cut -f3 <<<"$REPLY"); A_LATEST=$(cut -f5 <<<"$REPLY"); A_DRIVERS=$(cut -f6 <<<"$REPLY"); A_DRIVERS=${A_DRIVERS//,/ }
  fi
  [ "$A_LC" = UNKNOWN ] && { A_PRIO=CRITICAL; return 0; }   # DOC-SRS-QP-SCN-000 §2.2
  bundle_exposure "$p" "$v"; read -r nc nh nm nl c10 nk ids sec _ <<<"$REPLY"
  A_IDS=${ids#-}; A_SEC=${sec#-}
  if [ "$A_LC" = EOL ]; then A_STATE=eol
  elif [ -z "$A_MIN" ] || { [[ $A_MIN != NONE && $A_MIN != PENDING_RELEASE ]] && ! ver_lt "$v" "$A_MIN"; }; then A_STATE=ok
  else A_STATE=vulnerable; fi
  [ -z "$A_SEC" ] && [ "$A_STATE" = vulnerable ] && A_SEC=${A_DRIVERS// /,}
  # Backport of a distro package (BR-FEED-026, §7): Python chain, else the local changelog (SRC-016).
  if [ -n "$mgr" ] && [[ $A_STATE == vulnerable || $A_STATE == eol ]] && [ -n "$A_SEC" ]; then
    local out line cve st origin fx pver bp_cves=() fixed_ids=() state=""
    pver=$(pkg_version "$mgr" "$pkg")
    if python_ok && out=$(qp_py backport --manager "$mgr" --package "$pkg" --version "${pver:-$v}" --cves "$A_SEC" ${offline[@]+"${offline[@]}"} 2>>"$LOG"); then
      state=$(head -n1 <<<"$out" | cut -f1)
      while IFS=$'\t' read -r cve st origin fx; do
        [[ $cve == CVE-* ]] || continue
        jo adv_id=s:"$cve" state=s:"$st" origin=S:"$origin" fixed_version=S:"$fx"; bp_cves+=("$REPLY")
        [[ $st == FIXED || $st == NOT_AFFECTED ]] && fixed_ids+=("$cve")
      done < <(tail -n +2 <<<"$out")
    else
      local sec_list=(); IFS=, read -r -a sec_list <<<"$A_SEC"
      if pkg_has_cves "$mgr" "$pkg" "${sec_list[@]}"; then state="ok-backport"; fixed_ids=("${sec_list[@]}"); else state=vulnerable; fi
      local c; for c in ${A_SEC//,/ }; do
        if [[ " ${fixed_ids[*]-} " == *" $c "* ]]; then st=FIXED; else st=UNKNOWN; fi
        jo adv_id=s:"$c" state=s:"$st" origin=s:LOCAL_CHANGELOG fixed_version=j:null; bp_cves+=("$REPLY")
      done
    fi
    jarr bp_cves; jo state=s:"${state:-vulnerable}" manager=s:"$mgr" package=s:"$pkg" version=S:"$pver" cves=j:"$REPLY"; A_BACKPORT=$REPLY
    if [ "$state" = "ok-backport" ]; then A_STATE="ok-backport"; fi
    if (( ${#fixed_ids[@]} )); then
      excl=$(IFS=,; echo "${fixed_ids[*]}")
      bundle_exposure "$p" "$v" "$excl"; read -r nc nh nm nl c10 nk ids sec _ <<<"$REPLY"
    fi
  fi
  risk_score "$A_LC" "${A_DAYS:--}" "$nc" "$nh" "$nm" "$nl" "$nk" "$c10"
  A_RISK=$RISK_JSON; A_PRIO=$RISK_PRIO; A_NKEV=$nk; A_C10=$c10
}

ASSESS_LC=""

# rank_add OBJECT_REF: one ranking[] entry from the last assess (FEAT-033 order).
RANKING=(); EOL_90=0; KEV_FINDINGS=0
rank_add() {
  [ "$A_RISK" != null ] || return 0
  local reasons=() k=5
  (( A_NKEV > 0 )) && { reasons+=(KEV); KEV_FINDINGS=$((KEV_FINDINGS + 1)); }
  (( A_C10 >= 90 )) && reasons+=(CVSS_GE_9)
  [ "$A_LC" = EOL ] && reasons+=(EOL)
  (( A_C10 >= 70 && A_C10 < 90 )) && reasons+=(CVSS_7_TO_8_9)
  if [ -n "$A_DAYS" ] && (( A_DAYS >= 0 && A_DAYS <= 90 )); then reasons+=(EOL_LE_90D); EOL_90=$((EOL_90 + 1)); fi
  (( ${#reasons[@]} )) || reasons=(OTHER)
  case ${reasons[0]} in KEV) k=0 ;; CVSS_GE_9) k=1 ;; EOL) k=2 ;; CVSS_7_TO_8_9) k=3 ;; EOL_LE_90D) k=4 ;; esac
  jas ${reasons[@]+"${reasons[@]}"}
  jo object_ref=s:"$1" R=n:"$RISK_R" level=s:"$RISK_LEVEL" reason_codes=j:"$REPLY"
  RANKING+=("$(printf '%03d\t%d\t%s' "$((100 - RISK_R))" "$k" "$REPLY")")
}
A_NKEV=0; A_C10=0

# assess_json: the bundle fields of a runtime object (FR-ASMT-RISK-001).
assess_json() {
  local drivers=() d; for d in $A_DRIVERS; do drivers+=("$d"); done
  jas ${drivers[@]+"${drivers[@]}"}; local jd=$REPLY
  local lts=false; [ -n "$A_LTS" ] && lts=true
  local lc=null prio=null; [ -n "$QP_FEEDS_BUNDLE" ] && [ -n "$A_LC" ] && { _js "$A_LC"; lc=$REPLY; }; [ -n "$A_PRIO" ] && { _js "$A_PRIO"; prio=$REPLY; }
  jo lifecycle_status=j:"$lc" priority=j:"$prio" eol_date=S:"$A_EOL" days_to_eol=n:"$A_DAYS" is_lts=b:"$lts" \
     lts_codename=S:"$A_CODENAME" latest_patch=S:"$A_LATEST" min_patched=S:"$A_MIN" driver_ids=j:"$jd" \
     backport=j:"$A_BACKPORT" risk=j:"$A_RISK"
}

# deadline_add RUNTIME_ID: plan approval deadline from the last assess (FR-PLAN-DL-001,
# BR-SCN-049, BR-SCN-029): EOL - 30 days for SECURITY_ONLY/MAINTENANCE_LTS or <= 90 days to EOL.
J_DEADLINES=()
deadline_add() {
  local rid=$1 dl days f pid="" pst="" sev=info
  [ -n "$A_EOL" ] && [ -n "$A_DAYS" ] && (( A_DAYS >= 0 )) || return 0
  [[ $A_LC == SECURITY_ONLY || $A_LC == MAINTENANCE_LTS ]] || (( A_DAYS <= 90 )) || return 0
  dl=$(date -u -d "$A_EOL -30 days" +%F 2>/dev/null) || return 0
  days=$(( A_DAYS - 30 ))
  for f in "$STATE_DIR"/plans/PLN-*/plan.json; do
    [ -f "$f" ] && grep -q "\"runtime_id\": \"$rid\"" "$f" || continue
    local st; st=$(sed -n 's/^ "status": "\([a-z_]*\)".*/\1/p' "$f" | head -n1)
    [[ $st == cancelled ]] && continue
    pid=$(basename "${f%/plan.json}"); pst=$st
  done
  (( A_DAYS <= 90 )) && sev=warning
  if (( days < 0 )) && [[ $pst != approved && $pst != in_progress && $pst != completed ]]; then
    sev=high; add_warning "" "plan for $rid is overdue: approve it before $dl (BR-SCN-049)" "runtime:$rid"
  fi
  jo runtime_id=s:"$rid" deadline=s:"$dl" days_left=n:"$days" overdue=b:$(( days < 0 )) severity=s:"$sev" \
     plan_id=S:"$pid" plan_status=S:"$pst"
  J_DEADLINES+=("$REPLY")
}

# supported_branches PRODUCT: branches not EOL today, oldest first (REPLY, space list).
supported_branches() {
  REPLY=$(awk -F'\t' -v p="$1" -v t="$TODAY" '$1 == p && ($6 == "" || $6 >= t || ($8 == "1" && p == "php")) && $3 != "" && $3 <= t { print $2 }' \
            "$QP_FEEDS_BUNDLE/lifecycle.tsv" 2>/dev/null | sort -V | tr '\n' ' ')
  REPLY=${REPLY% }
}

# lts_branches: Node.js branches in ACTIVE_LTS or MAINTENANCE_LTS, newest last.
lts_branches() {
  REPLY=$(awk -F'\t' -v t="$TODAY" '$1 == "node" && $4 != "" && $4 <= t && ($6 == "" || $6 >= t) { print $2 }' \
            "$QP_FEEDS_BUNDLE/lifecycle.tsv" 2>/dev/null | sort -n | tr '\n' ' ')
  REPLY=${REPLY% }
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

# --- Scenario catalog (FR-SCN-CAT-001) -------------------------------------
# The packaged catalog (share/php-quickpatch/catalog) or one imported with a
# snapshot (STATE_DIR/feeds/catalog), whichever is valid and newer. Invalid:
# SHA256SUMS mismatch -> ERR-FEED-422-02, missing keys -> ERR-FEED-502-02;
# the other catalog stays in use.
CATALOG_FILES="scenarios.json checklists.json playbooks.json bc_rules.json mitigations.json framework_php.tsv catalog.json"
CATALOG_DIR=""; CATALOG_VERSION=""

# catalog_check DIR: REPLY = catalog_version, or the error code on failure.
catalog_check() {
  local d=$1 f n_pb n_act
  REPLY=ERR-FEED-422-02
  [ -f "$d/SHA256SUMS" ] || return 1
  for f in $CATALOG_FILES; do grep -q "  $f\$" "$d/SHA256SUMS" && [ -f "$d/$f" ] || return 1; done
  (cd "$d" && sha256sum -c --status --strict SHA256SUMS) 2>/dev/null || return 1
  REPLY=ERR-FEED-502-02
  grep -q '"scenarios": \[' "$d/scenarios.json" && grep -q '"rules": \[' "$d/mitigations.json" \
    && grep -q '"items": \[' "$d/checklists.json" || return 1
  n_pb=$(grep -c '"pb_id":' "$d/playbooks.json"); n_act=$(grep -c '"actions":' "$d/playbooks.json")
  [ "$n_pb" -gt 0 ] && [ "$n_pb" = "$n_act" ] || return 1
  REPLY=$(sed -n 's/.*"catalog_version": *"\([0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}-[0-9]*\)".*/\1/p' "$d/catalog.json" | head -n1)
  [ -n "$REPLY" ] || { REPLY=ERR-FEED-502-02; return 1; }
}

catalog_open() {
  local d v
  CATALOG_DIR=""; CATALOG_VERSION=""
  for d in "$SHARE_DIR/catalog" "${STATE_DIR:+$STATE_DIR/feeds/catalog}"; do
    [ -n "$d" ] && [ -f "$d/catalog.json" ] || continue
    if catalog_check "$d"; then
      v=$REPLY
      if [ -z "$CATALOG_VERSION" ] || ver_lt "$CATALOG_VERSION" "$v"; then CATALOG_DIR=$d; CATALOG_VERSION=$v; fi
    elif [ "$REPLY" = ERR-FEED-422-02 ]; then
      msg ERR-FEED-422-02 "The data snapshot does not match its SHA256 hash; rejected."
      warn "catalog $d: $REPLY"; add_error ERR-FEED-422-02 "catalog $d: $REPLY" host
    else
      msg ERR-FEED-502-02 "Data from {source} is abnormal ({detail}); keeping old data." source="catalog $d" detail="schema"
      warn "$REPLY"; add_error ERR-FEED-502-02 "$REPLY" host
    fi
  done
  [ -n "$CATALOG_DIR" ] || warn "No valid scenario catalog: runtimes get no scenario_ids."
  return 0
}

# cat_field LINE KEY: string or number value of KEY in one catalog record line.
cat_field() {
  local re='"'"$2"'": ("(([^"\\]|\\.)*)"|(-?[0-9]+)|null)'
  if [[ $1 =~ $re ]]; then REPLY=${BASH_REMATCH[2]}${BASH_REMATCH[4]}; REPLY=${REPLY//\\\\/\\}; else REPLY=""; fi
}

# scn_version_rules RUNTIME: "order<TAB>scenario_id<TAB>ERE" of the VERSION
# scenarios with a regex version_match, lowest match_order first.
scn_version_rules() {
  local line sid order vm
  [ -n "$CATALOG_DIR" ] || return 0
  while IFS= read -r line; do
    cat_field "$line" kind; [ "$REPLY" = VERSION ] || continue
    cat_field "$line" runtime; [ "$REPLY" = "$1" ] || continue
    cat_field "$line" scenario_id; sid=$REPLY; cat_field "$line" match_order; order=$REPLY
    cat_field "$line" version_match; vm=$REPLY
    [[ $vm == ^* ]] || continue
    vm=${vm//\\d/[0-9]}
    printf '%05d\t%s\t%s\n' "$order" "$sid" "$vm"
  done < <(grep '"scenario_id":' "$CATALOG_DIR/scenarios.json") | sort -n
}

# php_ga_max / php_prerelease_branches: from lifecycle.tsv of the bundle.
php_ga_max() {
  REPLY=$(awk -F'\t' '$1 == "php" && $3 != "" { print $2 }' "$QP_FEEDS_BUNDLE/lifecycle.tsv" 2>/dev/null | sort -V | tail -n1)
}
php_prerelease_branch() { # BRANCH: an official pre-release build exists (BR-SCN-040 step 1)
  awk -F'\t' -v b="$1" '$1 == "php" && $2 == b && $3 == "" && ($7 != "" || $10 != "") { f = 1 } END { exit !f }' \
    "$QP_FEEDS_BUNDLE/lifecycle.tsv" 2>/dev/null
}

php_panel_path() {
  case $1 in
    /opt/cpanel/*|/opt/alt/*|/opt/plesk/*|/www/server/*|/usr/local/lsws/*) return 0 ;;
    /usr/local/php[0-9]*) [ "$PANEL" = directadmin ] ;;
    *) return 1 ;;
  esac
}

# classify RUNTIME RAW BIN MGR PKG_VERSION: BR-SCN-040 (PHP), BR-SCN-020 (Node.js).
# Sets SCN_IDS (1 VERSION + 0..n OVERLAY), SCN_LC (""|PRE_RELEASE|UNKNOWN)
# and SCN_LOCK (BR-SCN-013, FR-SCN-LOCK-001).
classify() {
  local rt=$1 raw=$2 bin=$3 mgr=$4 pver=$5 vsid="" sid re
  SCN_IDS=(); SCN_LC=""; SCN_LOCK=0
  [ -n "$CATALOG_DIR" ] || return 0
  if [ "$rt" = php ]; then
    local M N P suf stype="ga" gamax="" mm overlay16=0
    if [[ $raw =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
      M=${BASH_REMATCH[1]}; N=${BASH_REMATCH[2]}; P=${BASH_REMATCH[3]}; suf=${BASH_REMATCH[4]}; mm="$M.$N"
      case $suf in
        "") stype=ga ;; alpha*|beta*|RC*) stype=pre ;; -dev) stype=dev ;; -*) stype=extra ;; *) stype=abnormal ;;
      esac
      [ -n "$QP_FEEDS_BUNDLE" ] && { php_ga_max; gamax=$REPLY; }
      if [ -n "$gamax" ] && ver_lt "$gamax" "$mm" && php_prerelease_branch "$mm"; then vsid=SCN-PHP-014; SCN_LC=PRE_RELEASE
      elif [ "$stype" = abnormal ] || (( M == 6 || M >= 10 )) || { [ -n "$gamax" ] && ver_lt "$gamax" "$mm"; }; then
        vsid=SCN-PHP-005; SCN_LC=UNKNOWN
      else
        while IFS=$'\t' read -r _ sid re; do
          [[ "$M.$N.$P" =~ $re ]] && { vsid=$sid; break; }
        done < <(scn_version_rules php)
        if [ -z "$vsid" ]; then vsid=SCN-PHP-005; SCN_LC=UNKNOWN
        elif [[ $stype == pre || $stype == dev ]]; then SCN_LC=PRE_RELEASE; overlay16=1; fi
      fi
    else
      vsid=SCN-PHP-005; SCN_LC=UNKNOWN
    fi
    SCN_IDS=("$vsid")
    if [ -n "$mgr" ]; then SCN_IDS+=(SCN-PHP-015)
    elif ! php_panel_path "$bin"; then overlay16=1; fi
    (( overlay16 )) && SCN_IDS+=(SCN-PHP-016)
  else
    local maj suf newest row ga alpha prefix=${bin%/bin/node}
    if [[ $raw =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
      maj=${BASH_REMATCH[1]}; suf=${BASH_REMATCH[4]}
      [ -n "$QP_FEEDS_BUNDLE" ] && newest=$(awk -F'\t' '$1 == "node" { print $2 }' "$QP_FEEDS_BUNDLE/lifecycle.tsv" | sort -n | tail -n1)
      row=""; [ -n "$QP_FEEDS_BUNDLE" ] && tsv_row lifecycle.tsv node "$maj" && row=$REPLY
      ga=$(cut -f3 <<<"$row"); alpha=$(cut -f7 <<<"$row")
      if [[ $suf =~ ^-(nightly|rc\.|pre|alpha) ]] || { [ -n "$ga" ] && [[ $ga > $TODAY ]]; } \
         || { [ -z "$ga" ] && [ -n "$alpha" ]; }; then vsid=SCN-NODE-008; SCN_LC=PRE_RELEASE
      elif [ -n "$suf" ] || { [ -n "${newest:-}" ] && (( maj > newest )); }; then vsid=SCN-NODE-008; SCN_LC=UNKNOWN
      else
        while IFS=$'\t' read -r _ sid re; do
          [[ $raw =~ $re ]] && { vsid=$sid; break; }
        done < <(scn_version_rules node)
        [ -n "$vsid" ] || { vsid=SCN-NODE-008; SCN_LC=UNKNOWN; }
      fi
    else
      vsid=SCN-NODE-008; SCN_LC=UNKNOWN
    fi
    SCN_IDS=("$vsid")
    if [[ $bin == */.nvm/versions/node/* ]]; then SCN_IDS+=(SCN-NODE-009)
    elif [ -n "$mgr" ]; then
      if [[ $pver == *nodesource* ]]; then SCN_IDS+=(SCN-NODE-011); else SCN_IDS+=(SCN-NODE-012); fi
    elif [ -d "$prefix/lib/node_modules/npm" ] && [[ $bin != /www/server/* ]]; then SCN_IDS+=(SCN-NODE-010)
    fi
  fi
  [ -n "$SCN_LC" ] && SCN_LOCK=1
  return 0
}

# scn_lock_error RUNTIME_LABEL RAW: ERR-SCN-422-01 for a locked runtime.
scn_lock_error() {
  msg ERR-SCN-422-01 "Unrecognized {runtime} version '{raw}'. Automation for this runtime is locked." runtime="$1" raw="$2"
  warn "$REPLY"; add_error ERR-SCN-422-01 "$REPLY"
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
  [ -n "$TODAY" ] || { TODAY=$(date -u +%F); iso_epoch "$TODAY"; TODAY_DAY=$((REPLY / 86400)); }
  detect_playbooks
  return 0
}

# --- Environment and playbooks (FR-SCAN-ENV-001, FR-SCN-ENV-001) ---------------
# environment-playbooks.md §2.3: every step that matches adds evidence[];
# restrictions[] carry the limits of FR-SCN-ENV-001.
OS_ID=""; OS_LIKE=""; OS_VER=""; PB_PANEL=""; PB_OS=""; PB_PHP=""
WEB_SERVERS=(); PB_BINDINGS=(); PB_NODE=(); J_EVIDENCE=(); J_RESTRICTIONS=()
NGINX_UP=0; APACHE_UP=0; APACHE_CTL=""; APACHE_MODPHP=0; APACHE_FCGI=0

evidence() { jo step=n:"$1" pb_id=S:"$2" signal=s:"$3"; J_EVIDENCE+=("$REPLY"); }
restrict() { # restrict CODE EN VI
  local m=$2; [ "${QP_LANG:-}" = vi ] && m=$3
  jo code=s:"$1" message=s:"$m"; J_RESTRICTIONS+=("$REPLY")
}
add_unique() { local -n _u=$1; local x; for x in "${_u[@]}"; do [ "$x" = "$2" ] && return 0; done; _u+=("$2"); }

detect_playbooks() {
  [ -r /etc/os-release ] && { OS_ID=$(. /etc/os-release && echo "${ID:-}"); OS_LIKE=$(. /etc/os-release && echo "${ID_LIKE:-}"); OS_VER=$(. /etc/os-release && echo "${VERSION_ID:-}"); }
  (( IN_CONTAINER )) && evidence 1 PB-013 "$( [ -f /.dockerenv ] && echo /.dockerenv || echo /proc/1/cgroup)"
  case $PANEL in
    cpanel) PB_PANEL=PB-007; evidence 2 PB-007 /usr/local/cpanel/cpanel ;;
    plesk) PB_PANEL=PB-009; evidence 2 PB-009 /usr/local/psa ;;
    aapanel) PB_PANEL=PB-010; evidence 2 PB-010 /www/server/panel ;;
    cyberpanel) PB_PANEL=PB-011; evidence 2 PB-011 /usr/local/CyberCP ;;
    directadmin) PB_PANEL=PB-012; evidence 2 PB-012 /usr/local/directadmin ;;
  esac
  if has selectorctl && [ -f /etc/cl.selector/selector.conf ]; then add_unique PB_BINDINGS PB-008; evidence 3 PB-008 /etc/cl.selector/selector.conf; fi
  if [ -z "$PB_PANEL" ] && [ -x /usr/local/lsws/bin/lswsctrl ]; then PB_PANEL=PB-011; evidence 4 PB-011 /usr/local/lsws/bin/lswsctrl; fi
  local like=" $OS_ID $OS_LIKE "
  if [[ $like == *" debian "* || $like == *" ubuntu "* ]] && [ "$PKG_MGR" = apt ]; then PB_OS=PB-001; evidence 5 PB-001 "ID=$OS_ID apt"
  elif [[ $like =~ \ (rhel|almalinux|rocky|centos|fedora)\  ]] && [[ $PKG_MGR == dnf || $PKG_MGR == yum ]]; then
    if { has rpm && rpm -q remi-release >/dev/null 2>&1; } || compgen -G '/etc/yum.repos.d/remi*.repo' >/dev/null; then
      PB_OS=PB-003; evidence 5 PB-003 "remi-release"
    else PB_OS=PB-002; evidence 5 PB-002 "ID=$OS_ID $PKG_MGR"; fi
  elif [ "$OS_ID" = alpine ] && [ "$PKG_MGR" = apk ]; then PB_OS=PB-004; evidence 5 PB-004 "ID=alpine apk"
  fi
  if has pgrep && pgrep -f 'nginx: master' >/dev/null 2>&1; then NGINX_UP=1; WEB_SERVERS+=(nginx); fi
  if has pgrep && { pgrep -x apache2 >/dev/null 2>&1 || pgrep -x httpd >/dev/null 2>&1; }; then
    APACHE_UP=1; WEB_SERVERS+=(apache)
    local c; for c in apachectl apache2ctl httpd; do has "$c" && { APACHE_CTL=$c; break; }; done
    if [ -n "$APACHE_CTL" ]; then
      local mods; mods=$(probe 10 "$APACHE_CTL" -M 2>/dev/null)
      grep -qE '(^| )php[0-9]*_module' <<<"$mods" && APACHE_MODPHP=1
      grep -q 'proxy_fcgi_module' <<<"$mods" && APACHE_FCGI=1
    fi
    compgen -G '/etc/apache2/mods-enabled/php*.load' >/dev/null && APACHE_MODPHP=1
  fi
  if [ -z "$PB_PANEL" ]; then
    (( NGINX_UP )) && { add_unique PB_BINDINGS PB-005; evidence 6 PB-005 "nginx: master"; }
    (( APACHE_UP && APACHE_FCGI )) && { add_unique PB_BINDINGS PB-005; evidence 6 PB-005 "apache proxy_fcgi_module"; }
    (( APACHE_UP && APACHE_MODPHP )) && { add_unique PB_BINDINGS PB-006; evidence 6 PB-006 "apache php_module"; }
  fi
  (( HAS_DOCKER )) && { add_unique PB_BINDINGS PB-013; evidence 7 PB-013 "docker info"; }
  (( IS_ROOT )) || restrict SCN-ENV-NOROOT "not root: project level only" "không root: chỉ cấp dự án"
  (( IN_CONTAINER )) && restrict SCN-ENV-DOCKER "inside a container: mitigation only (run PB-013 on the host)" "trong container: chỉ mitigation (chạy PB-013 ở host)"
  [ -n "$PB_PANEL" ] && restrict SCN-ENV-PANEL "panel $PANEL: sites change only through the panel ($PB_PANEL)" "panel $PANEL: chỉ đổi site qua panel ($PB_PANEL)"
  return 0
}

# php_provider BIN MGR: playbook that provides one PHP binary (§2.3 steps 2-5; PB-000 otherwise).
php_provider() {
  local bin=$1 mgr=$2
  if php_panel_path "$bin" && [ -n "$PB_PANEL" ]; then REPLY=$PB_PANEL
  elif [[ $bin == /opt/alt/* ]]; then REPLY=PB-008
  elif [[ $bin == /opt/remi/* ]]; then REPLY=PB-003
  elif (( IN_CONTAINER )); then REPLY=PB-013
  elif [ -n "$mgr" ] && [ -n "$PB_OS" ]; then REPLY=$PB_OS
  else REPLY=PB-000; fi
}

# env_after_runtimes: the server-level PHP provider, PB-000 handling, Node playbooks.
env_after_runtimes() {
  if (( ${#RT_PROVIDERS[@]} )); then
    local p; PB_PHP=""
    for p in "${RT_PROVIDERS[@]}"; do [ "$p" != PB-000 ] && { PB_PHP=$p; break; }; done
    # A web server playbook (step 6) still identifies the server; PB-000 only when steps 2-7 all miss.
    local b; for b in ${PB_BINDINGS[@]+"${PB_BINDINGS[@]}"}; do [ -z "$PB_PHP" ] && [ -n "$PB_OS" ] && PB_PHP=$PB_OS; done
    if [ -z "$PB_PHP" ]; then
      PB_PHP=PB-000; evidence 9 PB-000 "no playbook matched the PHP binaries"
      msg ERR-ENV-422-01 "Cannot identify how PHP is installed and assigned to sites on this server."
      warn "$REPLY"; add_error ERR-ENV-422-01 "$REPLY" host
      restrict SCN-ENV-UNKNOWN "PB-000: interim mitigation and guidance only" "PB-000: chỉ mitigation và hướng dẫn"
    fi
  else
    PB_PHP=${PB_PANEL:-$PB_OS}
  fi
  return 0
}

env_json() {
  local pbs=() p
  [ -n "$PB_PHP" ] && { jo pb_id=s:"$PB_PHP" layer=s:"$( [[ $PB_PHP == PB-00[7-9] || $PB_PHP == PB-01[0-2] ]] && echo panel || echo provider)"; pbs+=("$REPLY"); }
  for p in ${PB_BINDINGS[@]+"${PB_BINDINGS[@]}"}; do
    jo pb_id=s:"$p" layer=s:"$(case $p in PB-008) echo panel_overlay ;; PB-013) echo provider ;; *) echo binding ;; esac)"; pbs+=("$REPLY")
  done
  for p in ${PB_NODE[@]+"${PB_NODE[@]}"}; do jo pb_id=s:"$p" layer=s:"$(case $p in PB-017|PB-018) echo binding ;; *) echo provider ;; esac)"; pbs+=("$REPLY"); done
  jarr pbs; local jp=$REPLY
  jas ${WEB_SERVERS[@]+"${WEB_SERVERS[@]}"}; local ws=$REPLY
  local bind=() ; for p in ${PB_BINDINGS[@]+"${PB_BINDINGS[@]}"}; do [ "$p" != PB-013 ] && bind+=("$p"); done
  jas ${bind[@]+"${bind[@]}"}; local jb=$REPLY
  jas ${PB_NODE[@]+"${PB_NODE[@]}"}; local jn=$REPLY
  jarr J_EVIDENCE; local ev=$REPLY; jarr J_RESTRICTIONS; local rs=$REPLY
  jo os_id=S:"$OS_ID" os_version=S:"$OS_VER" pkg_mgr=s:"$PKG_MGR" panel=s:"$PANEL" has_systemd=b:$HAS_SYSTEMD \
     has_docker=b:$HAS_DOCKER in_container=b:$IN_CONTAINER is_root=b:$IS_ROOT web_servers=j:"$ws" playbooks=j:"$jp" \
     restrictions=j:"$rs" pb_provider=S:"$PB_PHP" pb_bindings=j:"$jb" pb_node=j:"$jn" evidence=j:"$ev"
}

# --- Site inventory (FR-SCAN-MAP-001; PB-005 Nginx/Apache + FPM, PB-006 mod_php) ---
J_SITES=(); declare -A SITE_RT=() SITE_SEEN=()

# site_key SITE_ID [SOCKET_DIR]: §4.4 / DOC-SRS-QP-ENV-003 §6.3.1.
site_key() {
  local id=$1 dir=${2:-/run/php/}
  if [[ $id =~ ^[a-z0-9.-]{1,48}$ ]] && (( ${#dir} + ${#id} + 12 <= 107 )); then REPLY=$id
  else REPLY="h_$(sha1_12 "$id")"; fi
}

# fpm_pools: "listen<TAB>pool_file<TAB>branch<TAB>user<TAB>error_log" of every FPM pool.
fpm_pools() {
  local f b
  for f in /etc/php/*/fpm/pool.d/*.conf /etc/opt/remi/php*/php-fpm.d/*.conf /etc/php[0-9]*/php-fpm.d/*.conf /etc/php-fpm.d/*.conf; do
    [ -f "$f" ] || continue
    b=""
    if [[ $f =~ ^/etc/php/([0-9]+\.[0-9]+)/ ]]; then b=${BASH_REMATCH[1]}
    elif [[ $f =~ ^/etc/opt/remi/php([0-9])([0-9]+)/ ]]; then b=${BASH_REMATCH[1]}.${BASH_REMATCH[2]}
    elif [[ $f =~ ^/etc/php([0-9])([0-9]+)/ ]]; then b=${BASH_REMATCH[1]}.${BASH_REMATCH[2]}
    elif [ -x /usr/bin/php ]; then b=$(php_version /usr/bin/php 2>/dev/null); b=${b%.*}; fi
    awk -F'=' -v f="$f" -v b="$b" '
      function emit() { if (l != "") print l "\t" f "\t" b "\t" u "\t" e }
      /^[ \t]*\[/ { emit(); l = ""; u = ""; e = ""; next }
      { k = $1; gsub(/[ \t]/, "", k); v = substr($0, index($0, "=") + 1); gsub(/^[ \t]+|[ \t;]+$/, "", v) }
      k == "listen" { l = v } k == "user" { u = v } k == "php_admin_value[error_log]" { e = v }
      END { emit() }' "$f"
  done
}

# pool_of ENDPOINT: REPLY = pool line (fpm_pools) serving ENDPOINT.
POOLS=""; POOLS_READ=0
pool_of() {
  local ep=$1 line l port
  (( POOLS_READ )) || { POOLS=$(fpm_pools); POOLS_READ=1; }
  port=""; [[ $ep =~ :([0-9]+)$ ]] && port=${BASH_REMATCH[1]}
  while IFS= read -r line; do
    l=${line%%$'\t'*}
    if [ "$l" = "$ep" ] || { [ -n "$port" ] && [[ $l == "$port" || $l == "0.0.0.0:$port" || $l == "[::]:$port" ]]; }; then REPLY=$line; return 0; fi
    if [[ $ep == /* && -e $ep && $l == /* && -e $l ]] && [ "$(readlink -f "$ep")" = "$(readlink -f "$l")" ]; then REPLY=$line; return 0; fi
  done <<<"$POOLS"
  REPLY=""; return 1
}

# php_bin_for BRANCH: the PHP binary of that branch among the discovered ones.
declare -A RT_BRANCH=()
php_bin_for() {
  local b=$1 bin best=""
  if (( ! ${#RT_BRANCH[@]} )); then
    local v; for bin in $(discover_php_bins); do v=$(php_version "$bin" 2>/dev/null) && RT_BRANCH[$bin]=${v%.*}; done
  fi
  for bin in "${!RT_BRANCH[@]}"; do
    [ "${RT_BRANCH[$bin]}" = "$b" ] || continue
    if [ -z "$best" ] || [[ $bin == /usr/bin/php* && $best != /usr/bin/php* ]]; then best=$bin; fi
  done
  REPLY=$best
}

# add_site ID PB KIND REFS ROOT NAMES(space) ENDPOINT BRANCH LOGS(space) SCHEME POOL_USER
add_site() {
  local id=$1 pb=$2 kind=$3 refs=$4 root=$5 names=$6 ep=$7 b=$8 logs=$9 scheme=${10} puser=${11:-} bin="" rid="" owner key
  [ -n "${SITE_SEEN[$id]:-}" ] && return 0
  SITE_SEEN[$id]=1
  if [ -n "$b" ]; then php_bin_for "$b"; bin=$REPLY; fi
  [ -n "$bin" ] && { runtime_id php "$bin"; rid=$REPLY; SITE_RT[$rid]+="${SITE_RT[$rid]:+ }$id"; }
  owner=""; [ -n "$root" ] && [ -d "$root" ] && owner=$(stat -c %U "$root" 2>/dev/null)
  owner=${owner:-${puser:-unknown}}
  site_key "$id"; key=$REPLY
  local n urls=() lg=() jn ju jl
  for n in $names; do urls+=("$scheme://$n/"); break; done
  read -r -a lg <<<"$logs"
  jas $names; jn=$REPLY; jas ${urls[@]+"${urls[@]}"}; ju=$REPLY; jas ${lg[@]+"${lg[@]}"}; jl=$REPLY
  jo site_id=s:"$id" site_key=s:"$key" pb_id=s:"$pb" server_names=j:"$jn" docroot=S:"$root" owner_user=s:"$owner" \
     binding_kind=s:"$kind" binding_ref=s:"$refs" current_branch=S:"$b" current_bin=S:"$bin" runtime_id=S:"$rid" \
     runtime_endpoint=S:"$ep" log_sources=j:"$jl" hc_urls=j:"$ju" hc_mode=s:full
  J_SITES+=("$REPLY")
}

# site_endpoint ID REFS ROOT NAMES EP LOGS SCHEME KIND PB: resolve EP to a pool and record the site.
site_endpoint() {
  local id=$1 refs=$2 root=$3 names=$4 ep=$5 logs=$6 scheme=$7 kind=$8 pb=$9 b="" f puser="" el=""
  if [ -L "$ep" ]; then
    warn "site $id uses the unversioned socket $ep -> $(readlink -f "$ep")"
    add_warning "" "site $id points to a socket without a version number ($ep)" "site:$id"
  fi
  if pool_of "$ep"; then
    IFS=$'\t' read -r _ f b puser el <<<"$REPLY"
    [ -n "$el" ] && logs+=" $el"
    [ -f "/var/log/php$b-fpm.log" ] && logs+=" /var/log/php$b-fpm.log"
  fi
  [[ $ep == /* ]] && ep="unix:$ep"
  add_site "$id" "$pb" "$kind" "$refs" "$root" "$names" "$ep" "$b" "$logs" "$scheme" "$puser"
}

nginx_sites() {
  local out
  out=$(probe 10 nginx -T 2>/dev/null) || [ -n "$out" ] || { warn "nginx -T failed: Nginx sites are not inventoried."; return 0; }
  local recs
  recs=$(awk '
    /^# configuration file .*:$/ { file = substr($0, 22); sub(/:$/, "", file); ln = 0; depth = 0; srv = ""; up = ""; next }
    {
      ln++; line = $0; sub(/(^|[ \t])#.*/, "", line)
      gsub(/\{/, "{\n", line); gsub(/;/, ";\n", line); gsub(/\}/, "\n}\n", line)
      np = split(line, parts, "\n")
      for (pi = 1; pi <= np; pi++) stmt(parts[pi])
    }
    function stmt(line,   n, w, d, v) {
      gsub(/^[ \t]+|[ \t]+$/, "", line)
      if (line == "") return
      n = split(line, w, /[ \t;]+/)
      if (line ~ /\{$/) {
        depth++; kind[depth] = w[1]
        if (w[1] == "server" && srv == "") { srv = ++nsrv; sdepth = depth; print "S\t" srv "\t" file "\t" ln }
        if (w[1] == "upstream") { up = w[2]; udepth = depth }
        return
      }
      if (line ~ /^\}/) { if (srv != "" && depth == sdepth) srv = ""; if (up != "" && depth == udepth) up = ""; depth--; return }
      d = w[1]; v = line; sub(/^[^ \t]+[ \t]+/, "", v); sub(/;$/, "", v)
      if (up != "" && d == "server") { if (!(up in upseen)) { upseen[up] = 1; print "U\t" up "\t" w[2] }; return }
      if (srv != "") {
        if (d == "server_name") print "N\t" srv "\t" v
        else if (d == "root") print "R\t" srv "\t" w[2]
        else if (d == "listen") print "L\t" srv "\t" v
        else if (d == "fastcgi_pass") print "F\t" srv "\t" w[2] "\t" file ":" ln
        else if (d == "include") print "I\t" srv "\t" w[2] "\t" file ":" ln
        else if (d == "error_log") print "E\t" srv "\t" w[2]
      } else if (d == "fastcgi_pass") print "P\t" file "\t" w[2] "\t" file ":" ln
    }' <<<"$out")
  declare -A s_file=() s_names=() s_root=() s_ssl=() s_fcgi=() s_ref=() s_err=() ups=() snip=()
  local t a b c d id
  while IFS=$'\t' read -r t a b c d; do
    case $t in
      S) s_file[$a]="$b:$c" ;;
      N) s_names[$a]=$b ;;
      R) s_root[$a]=$b ;;
      L) [[ $b == *443* || $b == *ssl* ]] && s_ssl[$a]=1 ;;
      F) s_fcgi[$a]=$b; s_ref[$a]=$c ;;
      I) [ -z "${s_fcgi[$a]:-}" ] && s_fcgi[$a]="include:$b" && s_ref[$a]="$c" ;;
      E) s_err[$a]=$b ;;
      U) ups[$a]=$b ;;
      P) snip[$a]="$b"$'\t'"$c" ;;
    esac
  done <<<"$recs"
  declare -A merged_ref=() merged_names=() first=()
  local order=() k ep names main
  for k in $(printf '%s\n' "${!s_file[@]}" | sort -n); do
    ep=${s_fcgi[$k]:-}
    if [[ $ep == include:* ]]; then
      local inc=${ep#include:} f found=""
      [[ $inc == /* ]] || inc="/etc/nginx/$inc"
      # shellcheck disable=SC2053  # include paths are globs (sites-enabled/*)
      for f in "${!snip[@]}"; do [[ $f == $inc ]] && { found=${snip[$f]}; break; }; done
      [ -n "$found" ] || continue
      ep=${found%%$'\t'*}; s_ref[$k]+=",${found#*$'\t'}"
    fi
    [ -n "$ep" ] || continue
    [[ $ep == unix:* || $ep == *:* || $ep =~ ^[0-9]+$ ]] || ep=${ups[$ep]:-$ep}
    names=${s_names[$k]:-_}; main=${names%% *}; main=${main,,}; [ "$main" = _ ] && main=default
    if [ -z "${first[$main]:-}" ]; then first[$main]=$k; order+=("$main"); merged_ref[$main]=${s_file[$k]}; merged_names[$main]=${names,,}
    else merged_ref[$main]+=",${s_file[$k]}"; fi
    merged_ref[$main]+=",${s_ref[$k]}"
    [ -n "${s_ssl[$k]:-}" ] && s_ssl[${first[$main]}]=1
    s_fcgi[${first[$main]}]=$ep
  done
  for main in ${order[@]+"${order[@]}"}; do
    k=${first[$main]}
    local refs; refs=$(tr ',' '\n' <<<"${merged_ref[$main]}" | awk 'NF && !s[$0]++' | paste -sd,)
    site_endpoint "$main" "$refs" "${s_root[$k]:-}" "${merged_names[$main]//_/}" "${s_fcgi[$k]#unix:}" "${s_err[$k]:-}" \
      "$( [ -n "${s_ssl[$k]:-}" ] && echo https || echo http)" nginx_fastcgi PB-005
    # §2.3 conflict rule: an Apache file for the same site that Apache does not load is only evidence.
    local af; for af in /etc/apache2/sites-available/*.conf /etc/httpd/conf.d/*.conf; do
      [ -f "$af" ] && grep -qiE "^\s*Server(Name|Alias)\s+.*\b${main//./\\.}\b" "$af" && evidence 6 PB-005 "site $main: $af (Apache, not loaded); Nginx binding used"
    done
  done
}

apache_sites() {
  [ -n "$APACHE_CTL" ] || return 0
  local out line name f l seen=" " glob_ep="" glob_ref="" modphp_b=""
  out=$(probe 10 "$APACHE_CTL" -S 2>&1) || true
  for f in /etc/apache2/conf-enabled/php*-fpm.conf /etc/httpd/conf.d/php*-fpm.conf; do
    [ -f "$f" ] || continue
    line=$(grep -m1 -nE 'SetHandler +"?proxy:unix:' "$f") || continue
    glob_ep=$(sed -E 's/.*proxy:unix:([^|"]+).*/\1/' <<<"$line"); glob_ref="$f:${line%%:*}"
  done
  for f in /etc/apache2/mods-enabled/php*.load; do [ -f "$f" ] && { modphp_b=${f##*/php}; modphp_b=${modphp_b%.load}; }; done
  while IFS= read -r line; do
    [[ $line =~ (namevhost|default\ server|[0-9*]:[0-9]+)\ +([^ ]+)\ \((/[^:]+):([0-9]+)\) ]] || continue
    name=${BASH_REMATCH[2],,}; f=${BASH_REMATCH[3]}; l=${BASH_REMATCH[4]}
    [[ $seen == *" $f:$l "* ]] && continue
    seen+="$f:$l "
    local blk sn al root ep="" ref="" err="" ssl=http kind=apache_proxy_fcgi pb=PB-005 b=""
    blk=$(awk -v s="$l" 'NR >= s { print NR "\t" $0; if (tolower($0) ~ /<\/virtualhost>/) exit }' "$f")
    sn=$(awk -F'\t' 'tolower($2) ~ /^[ \t]*servername[ \t]/ { split($2, w, /[ \t]+/); for (i = 1; i <= length(w); i++) if (tolower(w[i]) == "servername") { print w[i+1]; exit } }' <<<"$blk")
    al=$(awk -F'\t' 'tolower($2) ~ /^[ \t]*serveralias[ \t]/ { sub(/^[ \t]*[Ss]erver[Aa]lias[ \t]+/, "", $2); printf "%s ", $2 }' <<<"$blk")
    root=$(awk -F'\t' 'tolower($2) ~ /^[ \t]*documentroot[ \t]/ { v = $2; sub(/^[ \t]*[^ \t]+[ \t]+/, "", v); gsub(/"/, "", v); print v; exit }' <<<"$blk")
    err=$(awk -F'\t' 'tolower($2) ~ /^[ \t]*errorlog[ \t]/ { v = $2; sub(/^[ \t]*[^ \t]+[ \t]+/, "", v); gsub(/"/, "", v); print v; exit }' <<<"$blk")
    line=$(grep -m1 -E 'SetHandler +"?proxy:unix:|ProxyPassMatch .*fcgi://' <<<"$blk") || line=""
    if [[ $line == *proxy:unix:* ]]; then ep=$(sed -E 's/.*proxy:unix:([^|"]+).*/\1/' <<<"$line"); ref="$f:${line%%$'\t'*}"
    elif [[ $line == *fcgi://* ]]; then ep=$(sed -E 's#.*fcgi://([^/"]+).*#\1#' <<<"$line"); ref="$f:${line%%$'\t'*}"
    elif [ -n "$glob_ep" ]; then ep=$glob_ep; ref=$glob_ref
    elif (( APACHE_MODPHP )); then kind=apache_mod_php; pb=PB-006; b=$modphp_b
    else continue; fi
    [[ $l == 443 || $line == *443* || $blk == *SSLEngine* ]] && ssl=https
    sn=${sn,,}; [ -n "$sn" ] || sn=$name
    if [ "$kind" = apache_mod_php ]; then
      add_site "$sn" "$pb" "$kind" "$f:$l" "$root" "$sn ${al,,}" "" "$b" "$err" "$ssl"
    else
      site_endpoint "$sn" "$f:$l${ref:+,$ref}" "$root" "$sn ${al,,}" "$ep" "$err" "$ssl" "$kind" "$pb"
    fi
  done <<<"$out"
}

# unmapped_sites: sites in web server files that no running server loads (BR-ENV-001).
unmapped_sites() {
  local f n
  for f in /etc/nginx/sites-available/* /etc/nginx/conf.d/*.conf /etc/apache2/sites-available/*.conf; do
    [ -f "$f" ] || continue
    for n in $(awk 'tolower($1) == "server_name" || tolower($1) == "servername" || tolower($1) == "serveralias" { for (i = 2; i <= NF; i++) { v = $i; sub(/;$/, "", v); if (v != "_" && v != "") print tolower(v) } }' "$f" | sort -u); do
      [ -n "${SITE_SEEN[$n]:-}" ] && continue
      local hit=0 s; for s in "${J_SITES[@]}"; do [[ $s == *"\"server_names\":["*"\"$n\""* ]] && { hit=1; break; }; done
      (( hit )) && continue
      SITE_SEEN[$n]=1
      msg ERR-ENV-422-02 "Cannot determine which PHP site {site} uses." site="$n"
      CUR_REF="site:$n"; issue_c ERR-ENV-422-02 high "$REPLY ($f is not loaded by a running web server)"; CUR_REF=""
      site_key "$n"
      jo site_id=s:"$n" site_key=s:"$REPLY" pb_id=s:PB-000 server_names=j:"[\"$n\"]" docroot=j:null owner_user=s:unknown \
         binding_kind=s:unmapped binding_ref=s:"$f" current_branch=j:null current_bin=j:null runtime_id=j:null \
         runtime_endpoint=j:null log_sources=j:"[]" hc_urls=j:"[]" hc_mode=s:full
      J_SITES+=("$REPLY")
    done
  done
}

inventory_sites() {
  head_ "Sites"
  if [ -n "$PB_PANEL" ]; then
    note "Sites are managed by $PANEL ($PB_PANEL): panel inventory is not available in this build."
  fi
  (( NGINX_UP )) && [ -z "$PB_PANEL" ] && has nginx && nginx_sites
  (( APACHE_UP )) && [ -z "$PB_PANEL" ] && apache_sites
  (( NGINX_UP || APACHE_UP )) && [ -z "$PB_PANEL" ] && unmapped_sites
  local s n=0
  for s in ${J_SITES[@]+"${J_SITES[@]}"}; do [[ $s == *'"binding_kind":"unmapped"'* ]] || n=$((n + 1)); done
  note "$n site(s) mapped to a PHP runtime."
  return 0
}

# node_apps BIN: systemd units whose ExecStart runs BIN (PB-017). REPLY = JSON array.
node_apps() {
  local bin=$1 u apps=() user
  if (( HAS_SYSTEMD )); then
    for u in $(grep -lsE "ExecStart=.*${bin//./\\.}" /etc/systemd/system/*.service /lib/systemd/system/*.service 2>/dev/null | xargs -r -n1 basename | sort -u); do
      user=$(sed -n 's/^User=//p' "/etc/systemd/system/$u" 2>/dev/null | head -n1)
      jo app_id=s:"app:systemd:${u%.service}" manager=s:systemd unit_or_name=s:"$u" user=s:"${user:-root}"; apps+=("$REPLY")
    done
    (( ${#apps[@]} )) && add_unique PB_NODE PB-017
  fi
  jarr apps
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

# php_assess BIN: A_STATE = ok | ok-backport | vulnerable | eol | unknown and
# the other A_* fields from the bundle (min_patched, backport, risk).
php_assess() {
  local v mgr="" pkg=""
  if ! v=$(php_version "$1"); then assess php ""; return; fi
  read -r mgr pkg <<<"$(pkg_owner "$1")"
  assess php "$v" "$mgr" "$pkg"
}

# cve_list: the CVEs behind the current verdict, space separated (for messages).
cve_list() {
  local l=${A_SEC//,/ }; [ -n "$l" ] || l=$A_DRIVERS
  REPLY=${l:-known CVEs}
}

# risk_sev [DEFAULT]: issue severity from the risk level (FR-CLI-COMP-002, BR-FEED-042).
risk_sev() {
  case $A_RISK in *'"level":"CRITICAL"'*) REPLY=critical ;; *'"level":"HIGH"'*) REPLY=high ;;
    *'"level":"MEDIUM"'*) REPLY=medium ;; *'"level":"LOW"'*) REPLY=low ;; *) REPLY=${1:-high} ;; esac
}

# json_merge OBJ1 OBJ2: REPLY = OBJ1 with the members of OBJ2 appended.
json_merge() { if [ "$2" = "{}" ]; then REPLY=$1; else REPLY="${1%\}},${2#\{}"; fi; }

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

# mit_rules VERSION: "rule_id<TAB>directive" of the mitigations.json rules that
# match the unpatched CVEs of the last assess and the branch of VERSION
# (FR-PTCH-MIT-001). No catalog -> the v0.1 rules built in below.
MIT_BUILTIN='{"rule_id": "MIT-PHP-001", "cves": ["CVE-2026-109618", "CVE-2026-109619"], "branches": [], "directive": "session.upload_progress.enabled = 0", "flag": null}
{"rule_id": "MIT-PHP-002", "cves": ["CVE-2026-109618", "CVE-2026-109619"], "branches": [], "directive": "memory_limit = -1", "flag": "memlimit"}
{"rule_id": "MIT-PHP-003", "cves": ["CVE-2026-109618", "CVE-2026-109619"], "branches": ["8.5"], "directive": "fatal_error_backtraces = 0", "flag": null}'
mit_rules() {
  local b=${1%.*} line ids=",${A_IDS},${A_SEC},${A_DRIVERS// /,}," cves br id dir flag c hit
  {
    if [ -n "$CATALOG_DIR" ]; then grep '"rule_id":' "$CATALOG_DIR/mitigations.json"; else printf '%s\n' "$MIT_BUILTIN"; fi
  } | while IFS= read -r line; do
    cat_field "$line" rule_id; id=$REPLY; cat_field "$line" directive; dir=$REPLY; cat_field "$line" flag; flag=$REPLY
    [ "$flag" = memlimit ] && (( NO_MEMLIMIT )) && continue
    br=$(sed -n 's/.*"branches": \[\([^]]*\)\].*/\1/p' <<<"$line" | tr -d '" ')
    [ -z "$br" ] || [[ ",$br," == *",$b,"* ]] || continue
    cves=$(sed -n 's/.*"cves": \[\([^]]*\)\].*/\1/p' <<<"$line" | tr -d '" ')
    hit=0; for c in ${cves//,/ }; do [[ $ids == *",$c,"* ]] && { hit=1; break; }; done
    (( hit )) && printf '%s\t%s\t%s\n' "$id" "$dir" "$cves"
  done | sort
}

# php_mitigation_ini VERSION: the wanted file D (FR-PTCH-MIT-001): first line
# "; qp-rules=<ids>; sha256=<SHA-256 of the body>", then the body. Empty when no rule matches.
php_mitigation_ini() {
  local rules ids body sha cves
  rules=$(mit_rules "$1"); [ -n "$rules" ] || return 1
  ids=$(cut -f1 <<<"$rules" | paste -sd,); cves=$(cut -f3 <<<"$rules" | tr ',' '\n' | sort -u | paste -sd' ')
  body="; php-quickpatch interim mitigation ($cves). It only reduces exposure: upgrade PHP, then delete this file."$'\n'"$(cut -f2 <<<"$rules")"
  sha=$(printf '%s\n' "$body" | sha256sum | cut -c1-64)
  printf '; qp-rules=%s; sha256=%s\n%s\n' "$ids" "$sha" "$body"
}

# mit_by_tool FILE: written by the tool and not edited since: a qp-rules line whose
# sha256 matches the body (a), or a v0.1 file with exactly one v0.1 pattern (b).
mit_by_tool() {
  local f=$1 first sha lines
  first=$(head -n1 "$f")
  if [[ $first =~ ^\;\ qp-rules=[^\;]*\;\ sha256=([0-9a-f]{64})$ ]]; then
    sha=$(tail -n +2 "$f" | sha256sum | cut -c1-64); [ "$sha" = "${BASH_REMATCH[1]}" ]; return
  fi
  grep -q 'qp-rules=' "$f" && return 1
  lines=$(grep -v '^[[:space:]]*;' "$f" | grep -v '^[[:space:]]*$' | sed -E 's/[[:space:]]+//g' | sort | paste -sd'|')
  case $lines in
    'session.upload_progress.enabled=0'|'memory_limit=-1|session.upload_progress.enabled=0'| \
    'fatal_error_backtraces=0|session.upload_progress.enabled=0'| \
    'fatal_error_backtraces=0|memory_limit=-1|session.upload_progress.enabled=0') return 0 ;;
  esac
  return 1
}

php_mitigate() {
  local bin=$1 v d f want dirs
  v=$(php_version "$bin")
  if ! want=$(php_mitigation_ini "$v"); then
    note "no mitigations.json rule matches the unpatched CVEs of $bin"
    act mitigation_add skipped "no mitigation rule for ${A_IDS:-$A_DRIVERS}"; return 1
  fi
  if ! dirs=$(php_scan_dirs "$bin"); then
    msg ERR-PTCH-412-01 "No conf.d scan dir for {bin}; set the mitigation in its php.ini by hand." bin="$bin"
    warn "$REPLY"; add_warning ERR-PTCH-412-01 "$REPLY"; act mitigation_add failed "$REPLY" ERR-PTCH-412-01
    return 1
  fi
  local rules; rules=$(sed -n '1s/^; qp-rules=\([^;]*\);.*/\1/p' <<<"$want")
  while read -r d; do
    [ -d "$d" ] || continue
    f="$d/$PHP_MITIGATION_FILE"
    if [ ! -f "$f" ]; then
      change file create "$f" "" "" "interim mitigation $rules (FR-PTCH-MIT-001)"
      if (( DRY_RUN )); then say "    [dry-run] write $f"; act mitigation_add planned "$f"; continue; fi
      record created "$f" && printf '%s\n' "$want" >"$f" && note "wrote $f"
      act mitigation_add "done" "$f"; mit_json "$f" added; RESTART_PHP=1
    elif [ "$(cat "$f")" = "$want" ]; then
      note "$f unchanged"; mit_json "$f" unchanged
    elif mit_by_tool "$f"; then
      change file modify "$f" "" "" "rewrite interim mitigation $rules (FR-PTCH-MIT-001)"
      if (( DRY_RUN )); then say "    [dry-run] rewrite $f"; act mitigation_add planned "rewrite $f"; continue; fi
      if ! space_for "$(du -sk "$f" | awk '{print $1}')"; then
        msg ERR-ENV-507-01 "Not enough disk space to back up before switching {site}." site="$f"
        issue_c ERR-ENV-507-01 high "$f kept: not enough space in $STATE_DIR to back it up"; act mitigation_add skipped "$f" ERR-ENV-507-01; continue
      fi
      backup_file "$f"
      local tmp; tmp=$(mktemp "$d/.qp-mitigation.XXXXXX") && printf '%s\n' "$want" >"$tmp" && chmod 0644 "$tmp" && mv -f "$tmp" "$f" \
        && note "rewrote $f" && act mitigation_add "done" "rewrote $f" && mit_json "$f" rewritten && RESTART_PHP=1
    else
      local miss=() line; while IFS= read -r line; do
        [[ $line == \;* ]] && continue
        grep -qxF "$line" "$f" || miss+=("$line")
      done <<<"$want"
      note "$f kept (modified by hand)"; mit_json "$f" kept
      issue high "$f was modified by hand and is kept; missing: ${miss[*]:-none}"
    fi
  done <<<"$dirs"
  (( NO_MEMLIMIT )) || [[ $rules != *MIT-PHP-002* ]] || note "memory_limit=-1 removes PHP's memory cap; apps calling ini_set('memory_limit') can still override it."
  return 0
}

mit_json() { # mit_json FILE ACTION
  # shellcheck disable=SC2086
  jas $A_DRIVERS; jo runtime_id=s:"${CUR_REF#runtime:}" file=s:"$1" action=s:"$2" driver_ids=j:"$REPLY"; J_MITIG+=("$REPLY")
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

# php_runtime_json BIN VERSION STATE RAW: append a runtime object (FR-SCAN-RT-001);
# scenario fields come from the last classify call.
RT_PROVIDERS=()
php_runtime_json() {
  local bin=$1 v=$2 st=$3 raw=${4:-$2} rid mgr="" pkg="" pver="" src sfx d exts=() sapis=(cli) dirs=() owner
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
  php_provider "$bin" "$mgr"; local pb=$REPLY; RT_PROVIDERS+=("$pb")
  [ -n "$v" ] && RT_BRANCH[$bin]=${v%.*}
  jas ${SCN_IDS[@]+"${SCN_IDS[@]}"}; local js_scn=$REPLY lr=""
  (( SCN_LOCK )) && lr=scn.version.unrecognized
  jo runtime_id=s:"$rid" kind=s:php bin=s:"$bin" version_raw=S:"$raw" version=S:"$v" branch=S:"${v%.*}" \
     sapis=j:"$js_sapis" ini_scan_dirs=j:"$js_dirs" extensions=j:"$js_exts" owner_pkg=j:"$jpkg" \
     install_source=s:"$src" scenario_ids=j:"$js_scn" state=s:"$st" locked=b:$SCN_LOCK lock_reason=S:"$lr" \
     pb_id=s:"$pb" abi=j:null npm_version=j:null apps=j:"[]" site_ids=j:"[]"
  local rt=$REPLY; assess_json; json_merge "$rt" "$REPLY"
  J_RUNTIMES+=("$REPLY"); rank_add "runtime:$rid"; deadline_add "$rid"
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
    local raw m p pv; read -r m p <<<"$(pkg_owner "$bin")"; pv=""; [ -n "${m:-}" ] && pv=$(pkg_version "$m" "$p")
    raw=$(probe 10 "$bin" -n -r 'echo PHP_VERSION;' 2>/dev/null) || raw=""
    classify php "$raw" "$bin" "${m:-}" "$pv"
    v=${raw%%[^0-9.]*}
    if [ -z "$v" ]; then
      scn_lock_error "PHP ($bin)" ""
      assess php ""; php_runtime_json "$bin" "" unknown ""
      [ "$MODE" = fix ] && act runtime_patch skipped "PHP $bin: automation locked (scn.version.unrecognized)" ERR-SCN-422-01
      CUR_REF=""; continue
    fi
    ASSESS_LC=$SCN_LC; assess php "$v" "${m:-}" "${p:-}"; ASSESS_LC=""; st=$A_STATE; label="PHP $v ($bin)"; before=$v
    php_runtime_json "$bin" "$v" "$st" "$raw"
    affected runtime "$rid" "PHP $v $bin"
    if (( SCN_LOCK )); then
      # BR-SCN-013: pre-release/abnormal version -> checks and report only.
      scn_lock_error "PHP ($bin)" "$raw"
      local sev; risk_sev critical; sev=$REPLY
      issue_c ERR-SCN-422-01 "$sev" "PHP $raw ($bin): $SCN_LC version, automation locked (${SCN_IDS[*]})"
      if [ "$MODE" = fix ]; then
        act runtime_patch skipped "PHP $raw: automation locked (scn.version.unrecognized)" ERR-SCN-422-01
        act mitigation_add skipped "PHP $raw: automation locked (scn.version.unrecognized)" ERR-SCN-422-01
      fi
      CUR_REF=""; continue
    fi
    case $st in
      ok)          ok "$label is patched."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      ok-backport) cve_list; ok "$label has the vendor backport for $REPLY."; [ "$MODE" = fix ] && php_unmitigate "$bin" ;;
      unknown)     warn "$label: newer than the advisory data, not checked." ;;
      vulnerable|eol)
        cve_list; local cves=$REPLY sev; risk_sev critical; sev=$REPLY
        if [ "$st" = eol ]; then bad "$label is end-of-life upstream and has no $cves fix."
        else bad "$label is vulnerable to $cves (fixed in $A_MIN)."; fi
        if [ "$MODE" != fix ]; then issue "$sev" "$label: unpatched $cves (risk $RISK_R $RISK_LEVEL)"; CUR_REF=""; continue; fi
        if (( ! IS_ROOT )); then issue_c ERR-PTCH-403-01 "$sev" "$label: needs root (or the hosting panel) to upgrade"; act runtime_patch skipped "needs root" ERR-PTCH-403-01; CUR_REF=""; continue; fi
        if php_upgrade "$bin" && (( ! DRY_RUN )); then
          php_assess "$bin"; st=$A_STATE; v=$(php_version "$bin")
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
        supported_branches php; local oldest=${REPLY%% *}
        issue_c ERR-PTCH-424-01 "$sev" "$label: still unpatched, interim mitigation applied. Move to a supported branch (>= ${oldest:-a supported one}) or a vendor backport."
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

node_assess() { # node_assess BIN VERSION: A_* for one Node.js binary
  local mgr="" pkg=""
  read -r mgr pkg <<<"$(pkg_owner "$1")"
  assess node "$2" "$mgr" "$pkg"
}

node_latest() { # node_latest MAJOR: newest release of that line, online
  fetch "$NODE_BASE_URL/index.json" | grep -o "\"version\":\"v$1\\.[0-9.]*\"" | head -n1 | grep -o '[0-9][0-9.]*'
}

# Replace a tarball-style Node install (PREFIX/bin/node) with the newest
# release of the same major, verified against SHASUMS256.txt.
node_upgrade_prefix() {
  local prefix=$1 major=$2 ver arch tarball sums
  if ! ver=$(node_latest "$major"); then
    tsv_row min_patched.tsv node "$major" && ver=$(cut -f5 <<<"$REPLY")
    [ -n "$ver" ] || return 1
  fi
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

# node_runtime_json BIN VERSION STATE RAW (FR-SCAN-RT-002)
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
  local pb=""   # §2.3 step 8: provider playbook of this binary
  case $src in nvm) pb=PB-016 ;; nodesource) pb=PB-014 ;; tarball|package) pb=PB-015 ;; docker) pb=PB-013 ;; esac
  [ -n "$pb" ] && add_unique PB_NODE "$pb"
  node_apps "$bin"; local japps=$REPLY
  jas ${SCN_IDS[@]+"${SCN_IDS[@]}"}; local js_scn=$REPLY lr=""
  (( SCN_LOCK )) && lr=scn.version.unrecognized
  jo runtime_id=s:"$rid" kind=s:node bin=s:"$bin" version_raw=S:"${4:-$v}" version=S:"$v" branch=S:"${v%%.*}" \
     sapis=j:"[]" ini_scan_dirs=j:"[]" extensions=j:"[]" owner_pkg=j:"$jpkg" install_source=s:"$src" \
     scenario_ids=j:"$js_scn" state=s:"$st" locked=b:$SCN_LOCK lock_reason=S:"$lr" pb_id=S:"$pb" abi=S:"$abi" \
     npm_version=S:"$npmv" apps=j:"$japps" site_ids=j:"[]"
  local rt=$REPLY; assess_json; json_merge "$rt" "$REPLY"
  J_RUNTIMES+=("$REPLY"); rank_add "runtime:$rid"; deadline_add "$rid"
  count_state "$st"
}

check_node() {
  head_ "Node.js runtimes"
  local bins bin v st label major rid before
  mapfile -t bins < <(discover_node_bins)
  if [ ${#bins[@]} -eq 0 ]; then note "No Node.js binary found."; return; fi
  for bin in "${bins[@]}"; do
    runtime_id node "$bin"; rid=$REPLY; CUR_REF="runtime:$rid"
    local raw m p pv; read -r m p <<<"$(pkg_owner "$bin")"; pv=""; [ -n "${m:-}" ] && pv=$(pkg_version "$m" "$p")
    if ! v=$(probe 10 "$bin" -v 2>/dev/null) || [ -z "$v" ]; then
      classify node "" "$bin" "${m:-}" "$pv"
      scn_lock_error "Node.js ($bin)" ""; assess node ""; node_runtime_json "$bin" "" unknown ""
      [ "$MODE" = fix ] && act runtime_patch skipped "Node.js $bin: automation locked (scn.version.unrecognized)" ERR-SCN-422-01
      CUR_REF=""; continue
    fi
    raw=$v; classify node "$raw" "$bin" "${m:-}" "$pv"
    v=${v#v}; v=${v%%[^0-9.]*}; major=${v%%.*}
    ASSESS_LC=$SCN_LC; node_assess "$bin" "$v"; ASSESS_LC=""; st=$A_STATE; label="Node.js $v ($bin)"; before=$v
    node_runtime_json "$bin" "$v" "$st" "$raw"; affected runtime "$rid" "Node.js $v $bin"
    if (( SCN_LOCK )); then
      scn_lock_error "Node.js ($bin)" "$raw"
      local sev; risk_sev critical; sev=$REPLY
      issue_c ERR-SCN-422-01 "$sev" "Node.js $raw ($bin): $SCN_LC version, automation locked (${SCN_IDS[*]})"
      [ "$MODE" = fix ] && act runtime_patch skipped "Node.js $raw: automation locked (scn.version.unrecognized)" ERR-SCN-422-01
      CUR_REF=""; continue
    fi
    case $st in
      ok) ok "$label is patched." ;;
      unknown) warn "$label: newer than the advisory data, not checked." ;;
      ok-backport) cve_list; ok "$label has the vendor backport for $REPLY." ;;
      eol) bad "$label is end-of-life and gets no security fixes."
           lts_branches; local l2=${REPLY% *} l1=${REPLY##* }; l2=${l2##* }; [ "$l2" = "$l1" ] && l2=""
           risk_sev high; issue "$REPLY" "$label: end-of-life, move to Node ${l2:+$l2 or }$l1 LTS" ;;
      vulnerable)
        bad "$label is below the latest security release ($A_MIN)."
        if [ "$MODE" != fix ]; then risk_sev high; issue "$REPLY" "$label: unpatched"; CUR_REF=""; continue; fi
        if (( ! IS_ROOT )) && [[ $bin != "$HOME"/* ]]; then issue_c ERR-PTCH-403-01 high "$label: needs root to upgrade"; act runtime_patch skipped "needs root" ERR-PTCH-403-01; CUR_REF=""; continue; fi
        NODE_ERR=""
        if node_upgrade "$bin" "$major" && (( ! DRY_RUN )); then
          v=$("$bin" -v); v=${v#v}; node_assess "$bin" "$v"
          jo runtime_id=s:"$rid" version_before=s:"$before" version_after=s:"$v" state_after=s:"$A_STATE"; J_RT_AFTER+=("$REPLY")
          if [ "$A_STATE" = ok ]; then ok "upgraded to Node.js $v"; fixed "Node.js $bin -> $v"; act runtime_patch "done" "Node.js $before -> $v"; CUR_REF=""; continue; fi
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
  local eco=$1 hits=$2 name ver ids sev mal advs kev fixed info fx=()
  [ -n "$hits" ] || return 0
  while read -r name ver ids; do
    [ -n "$name" ] || continue
    IFS=, read -r -a advs <<<"$ids"
    if [[ ",$ids" == *,MAL-* ]]; then mal=1; sev=critical; else mal=0; sev=high; fi
    kev=0; fx=()
    info=${OSV_INFO["$name@$ver"]:-}
    if [ -n "$info" ]; then
      read -r sev kev mal fixed <<<"$info"; [ "$fixed" = - ] || IFS=, read -r -a fx <<<"$fixed"
    fi
    jas ${fx[@]+"${fx[@]}"}; local jfx=$REPLY
    jas "${advs[@]}"
    jo project_id=s:"${CUR_REF#project:}" ecosystem=s:"$eco" package=s:"$name" version=s:"$ver" advisories=j:"$REPLY" \
       severity=s:"$sev" in_kev=b:$kev is_malware=b:$mal fixed_versions=j:"$jfx"
    J_DEPS+=("$REPLY"); VULN_PACKAGES=$((VULN_PACKAGES + 1))
  done <<<"$hits"
}

# osv_lookup ECOSYSTEM LOCKFILE < "name version": like osv_check, through
# qp-feeds.py when Python is available (cache per lockfile SHA-256, severity,
# KEV, fixed versions; FR-FEED-OSV-001). Exit 3 = no result (ERR-FEED-503-02).
declare -A OSV_INFO=()
osv_lookup() {
  local eco=$1 lock=$2 out rc name ver ids sev kev mal fixed offline=()
  (( OFFLINE )) && offline=(--offline)
  if ! python_ok; then
    (( OFFLINE )) && return 3
    osv_check "$eco"; return
  fi
  out=$(qp_py osv-check --ecosystem "$eco" --lockfile "$lock" ${offline[@]+"${offline[@]}"} 2>>"$LOG"); rc=$?
  (( rc == 0 )) || return 3
  while IFS=$'\t' read -r name ver ids sev kev mal fixed; do
    [ -n "$name" ] || continue
    OSV_INFO["$name@$ver"]="$sev $kev $mal ${fixed:--}"
    printf '%s %s %s\n' "$name" "$ver" "$ids"
  done <<<"$out"
}

# Report and optionally fix vulnerable/malicious packages of one lockfile.
# audit_lockfile ECOSYSTEM LOCKFILE FIX_FN
audit_lockfile() {
  local eco=$1 lock=$2 fixfn=$3 dir=${2%/*} hits names mal
  project_ref "$lock"; CUR_REF=$REPLY
  if (( OFFLINE )) && ! python_ok; then warn "$lock: skipped (offline)"; return; fi
  local deps; deps=$(deps_of "$lock")
  if [ -z "$deps" ]; then warn "$lock: could not read packages (needs php, node or jq)"; return; fi
  osv_lookup "$eco" "$lock" <<<"$deps" >"$WORK_DIR/osv.hits"; local orc=$?
  hits=$(cat "$WORK_DIR/osv.hits")
  if (( orc != 0 )); then
    if (( OFFLINE )); then warn "$lock: skipped (offline)"; return; fi
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
      local after; deps_of "$lock" | osv_lookup "$eco" "$lock" >"$WORK_DIR/osv.hits" && after=$(cat "$WORK_DIR/osv.hits") || after="$hits"
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

wp_status_json() { # wp_status_json SITE VERSION FIX STATUS (A_* of the version)
  project_ref "$1"; local pid=${REPLY#project:} ids=() i
  for i in ${A_IDS//,/ }; do ids+=("$i"); done
  jas ${ids[@]+"${ids[@]}"}; local adv=$REPLY kev=0; (( A_NKEV > 0 )) && kev=1
  jo site_dir=s:"$1" project_id=S:"$pid" version=s:"$2" min_patched=S:"$3" status=s:"$4" advisories=j:"$adv" in_kev=b:$kev risk=j:"$A_RISK"
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
    assess wordpress "$v"; fix=$A_MIN
    if [ "$A_STATE" = unknown ]; then
      warn "$site: WordPress $v is not in the advisory data, not checked."
      [ "$MODE" = fix ] || wp_status_json "$site" "$v" "" unknown
      CUR_REF=""; continue
    elif [[ $A_STATE == vulnerable || $A_STATE == eol ]]; then
      cve_list
      if [[ $fix == NONE || $fix == PENDING_RELEASE || -z $fix ]]; then
        bad "$site: WordPress $v is vulnerable ($REPLY); no patched release in its branch, upgrade to a supported branch."; fix=""
      else bad "$site: WordPress $v is vulnerable to $REPLY (fixed in $fix)."; fi
      [ "$MODE" = fix ] || wp_status_json "$site" "$v" "$A_MIN" vulnerable
    else
      ok "$site: WordPress $v is patched."
      [ "$MODE" = fix ] || { wp_status_json "$site" "$v" "$A_MIN" ok; CUR_REF=""; continue; }
      fix=""
    fi
    if [ "$MODE" != fix ]; then cve_list; risk_sev critical; issue "$REPLY" "$site: WordPress $v unpatched (risk $RISK_R $RISK_LEVEL)"; CUR_REF=""; continue; fi
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
    assess wordpress "$v"
    if [ -n "$fix" ]; then
      if ver_lt "$v" "$fix"; then risk_sev critical; issue "$REPLY" "$site: WordPress still $v after update attempt (see $LOG)"; act wp_update failed "$site still $v"; wp_status_json "$site" "$v" "$fix" vulnerable
      else ok "$site: WordPress updated to $v"; fixed "$site: WordPress -> $v"; act wp_update "done" "$site -> $v"; wp_status_json "$site" "$v" "$fix" ok; fi
    else wp_status_json "$site" "$v" "$A_MIN" "$( [[ $A_STATE == ok* ]] && echo ok || echo vulnerable)"
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
        local prod=node kind="Node.js" full=$ver
        [[ $img == *php ]] && { prod=php; kind=PHP; }
        [[ $prod == php && $ver != *.*.* ]] && full="$ver.0"
        [[ $prod == node && $ver != *.*.* ]] && full="${ver%%.*}.0.0"
        assess "$prod" "$full"; fix=$A_MIN
        if [ "$A_LC" = EOL ]; then
          bad "$f: $img:$ver is an end-of-life $kind image"; issue high "$f: $kind image $ver is EOL"
        elif [ "$A_LC" = UNKNOWN ] || [[ -z $fix || $fix == NONE || $fix == PENDING_RELEASE ]]; then
          :
        elif [[ $ver == *.*.* ]] && ver_lt "$ver" "$fix"; then
          target=${A_LATEST:-$fix}
        elif [[ $ver != *.*.* ]]; then
          if [ "$prod" = php ]; then note "$f: $img:$ver$suffix floats on the branch; rebuild with 'docker build --pull' / 'docker compose build --pull'."
          else note "$f: $img:$ver$suffix floats on the line; rebuild with --pull."; fi
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
      assess php "$v"
      if [ "$A_STATE" = ok ]; then ok "$name ($image): PHP $v patched"
      elif [ "$A_STATE" = unknown ]; then note "$name: PHP $v not in advisory data"
      else
        bad "$name ($image): PHP $v unpatched; rebuild the image on a fixed base."
        risk_sev critical; issue "$REPLY" "container $name: PHP $v (image $image) needs a rebuild"
        [ "$MODE" = fix ] && container_mitigate "$id" "$name" "$v"
      fi
    fi
    if [ -n "$nv" ]; then
      assess node "$nv"; st=$A_STATE
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
  local want; want=$(php_mitigation_ini "$v") || { note "$name: no mitigation rule matches"; act container_mitigation skipped "$name: no rule"; return; }
  if printf '%s\n' "$want" | docker exec -i "$id" sh -c "cat > '$f'" 9>&- 3>&-; then
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
  kev=$KEV_FINDINGS
  jo runtimes=n:${#J_RUNTIMES[@]} by_state=j:"{\"ok\":$BY_STATE_OK,\"ok_backport\":$BY_STATE_BACKPORT,\"vulnerable\":$BY_STATE_VULN,\"eol\":$BY_STATE_EOL,\"unknown\":$BY_STATE_UNKNOWN}" \
     eol_within_90d=n:$EOL_90 kev_findings=n:$kev critical_issues=n:$CRITICAL vulnerable_packages=n:$VULN_PACKAGES
  local summary=$REPLY
  # site_ids of each runtime from the site inventory
  local i r ids id
  for i in "${!J_RUNTIMES[@]}"; do
    r=${J_RUNTIMES[$i]}; [[ $r =~ \"runtime_id\":\"([^\"]+)\" ]] || continue
    ids=${SITE_RT[${BASH_REMATCH[1]}]:-}; [ -n "$ids" ] || continue
    local arr=(); for id in $ids; do arr+=("$id"); done; jas "${arr[@]}"
    J_RUNTIMES[$i]=${r/\"site_ids\":\[\]/\"site_ids\":$REPLY}
  done
  jarr J_RUNTIMES; rt=$REPLY
  local sites; jarr J_SITES; sites=$REPLY
  # FR-PLAN-GEN-001: SHA-256 of the site bindings + runtime versions.
  fp=$( { printf '%s\n' ${J_SITES[@]+"${J_SITES[@]}"} | sort; printf '%s\n' ${J_RUNTIMES[@]+"${J_RUNTIMES[@]}"} | grep -o '"bin":"[^"]*"\|"version_raw":"[^"]*"'; } | sha256sum | cut -c1-64)
  local dls; jarr J_DEADLINES; dls=$REPLY
  env_json; local envj=$REPLY rk="" line
  while IFS=$'\t' read -r _ _ line; do [ -n "$line" ] && rk+="${rk:+,}$line"; done < <(printf '%s\n' ${RANKING[@]+"${RANKING[@]}"} | sort -t$'\t' -k1,1n -k2,2n -k3,3)
  jo scan_fingerprint=s:"$fp" environment=j:"$envj" runtimes=j:"$rt" sites=j:"$sites" projects=j:"$pr" containers=j:"$ct" \
     dependency_findings=j:"$dp" wordpress_findings=j:"$wp" webshell_findings=j:"$ws" drift_warnings=j:"[]" \
     ranking=j:"[$rk]" plan_deadlines=j:"$dls" summary=j:"$summary"
  SCAN_FP=$fp
}
SCAN_FP=""

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
    jo bundle_id=S:"$DATA_BUNDLE_ID" scan_fingerprint=S:"$SCAN_FP" catalog_version=S:"$CATALOG_VERSION"; fpj=$REPLY
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
  catalog_open
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
  if [ "$MODE" = rollback ]; then detect_env; do_rollback; fi

  [ "$MODE" = fix ] && (( ! DRY_RUN )) && audit_intent fix
  detect_env
  # Runtime, WordPress and image checks need the bundle; Composer/npm use its KEV list.
  local need_data=0
  if want php || want node || want wp || want docker; then need_data=1; fi
  if (( need_data )) || want composer || want npm; then bundle_open; (( need_data )) && bundle_report; fi
  discover_projects
  want php && check_php
  want node && check_node
  env_after_runtimes
  want sites && inventory_sites
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
  (( need_data )) && [ -z "$QP_FEEDS_BUNDLE" ] && code=2   # no data at all (DOC-SRS-QP-FEED-003 §4.5 step 3)
  if [ "$MODE" = fix ]; then
    (( DRY_RUN )) || audit_result fix "$code"
    scan_result_json >/dev/null; fix_result_json; finish "$code" "$REPLY"
  fi
  scan_result_json; finish "$code" "$REPLY"
}

# Run unless sourced (tests source the file to call single functions).
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
