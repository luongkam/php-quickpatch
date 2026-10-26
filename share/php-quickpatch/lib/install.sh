# shellcheck shell=bash disable=SC2034  # globals shared with php-quickpatch.sh and the other lib/*.sh
# migrate install / remove-old (FR-UPG-PRE-001, FR-UPG-INST-001, FR-UPG-CFG-002, FR-UPG-RMV-001):
# side-by-side install of the target branch (PHP: PB-001 apt; Node.js: PB-015 official tarball
# into /opt/node-<major>) and removal of an old branch that nothing used for 14 days.
# Sourced by php-quickpatch.sh for migrate (after migrate.sh, hc.sh, pb.sh).

INST_PRE=(); INST_PKGS=(); INST_COPIED=(); INST_DROPPED=(); INST_EXT_OK=(); INST_NOT=(); INST_REPO_ADDED=0
INST_SOURCE=""; INST_NEW_BIN=""

# OS end of standard support (BR-SCN-016 "OS còn hỗ trợ"); unknown OS -> not judged.
OS_EOL="ubuntu:20.04 2025-05-31
ubuntu:22.04 2027-06-01
ubuntu:24.04 2029-05-31
ubuntu:26.04 2031-05-31
debian:11 2026-08-31
debian:12 2028-06-30
debian:13 2030-06-30"

# pre CHECK REQUIRED ACTUAL PASS(0|1): one preconditions[] entry (FR-UPG-PRE-001).
pre() {
  jo check=s:"$1" required=s:"$2" actual=s:"$3" pass=b:"$4"; INST_PRE+=("$REPLY")
  if (( $4 )); then say "    [ok] $1: $3 (need $2)"; else say "    [FAILED] $1: $3 (need $2)"; fi
}

# apt_candidate PKG: REPLY = candidate version ("" when none).
apt_candidate() {
  REPLY=$(LC_ALL=C apt-cache policy "$1" 2>/dev/null | awk '/Candidate:/ { print $2; exit }')
  [ "$REPLY" = "(none)" ] && REPLY=""
  [ -n "$REPLY" ]
}

# php_ext_pkg MODULE BRANCH: REPLY = package suffix of a module of `php -m` ("" = built in).
php_ext_pkg() {
  local m=${1,,} b=$2
  case $m in
    core|date|libxml|openssl|pcre|zlib|filter|hash|json|random|reflection|spl|standard|session|sodium|ctype|exif|\
    fileinfo|ftp|gettext|iconv|pdo|phar|posix|shmop|sockets|sysvmsg|sysvsem|sysvshm|tokenizer|calendar|ffi|lexbor|uri|pcntl)
      REPLY="" ;;
    mysqlnd|mysqli|pdo_mysql) REPLY=mysql ;;
    pgsql|pdo_pgsql) REPLY=pgsql ;;
    sqlite3|pdo_sqlite) REPLY=sqlite3 ;;
    'zend opcache'|opcache) if ver_lt "$b" 8.5; then REPLY=opcache; else REPLY=""; fi ;;   # built in from 8.5
    dom|simplexml|xml|xmlreader|xmlwriter|xsl) REPLY=xml ;;
    *) REPLY=$m ;;
  esac
}

# php_modules BIN: lower-case module names of `BIN -m` (one per line, unique).
php_modules() { "$1" -m 2>/dev/null | grep -v '^\[' | grep -v '^$' | tr 'A-Z' 'a-z' | sort -u; }

# ppa_or_sury: REPLY = how the target branch is added (BR-ENV-004): ppa (Ubuntu) | sury (Debian).
repo_kind() { if [ "$OS_ID" = ubuntu ]; then REPLY=ppa; else REPLY=sury; fi; }

mig_install() {
  case $MIG_RUNTIME in
    php) [[ $MIG_TARGET =~ ^[5-9]\.[0-9]$ ]] || arg_error "--target ${MIG_TARGET:-}" ;;
    node) [[ $MIG_TARGET =~ ^[0-9]{1,3}$ ]] || arg_error "--target ${MIG_TARGET:-}" ;;
    *) arg_error "--runtime ${MIG_RUNTIME:-}" ;;
  esac
  (( IS_ROOT )) || fatal ERR-CLI-403-01 "{command} requires root." command="migrate install"
  mig_inventory
  (( IN_CONTAINER )) && fatal ERR-ENV-422-01 "Cannot identify how PHP is installed and assigned to sites on this server."
  if [ "$MIG_RUNTIME" = php ]; then inst_php; else inst_node; fi
}

# --- PHP (PB-001 §2.4) -----------------------------------------------------------------------------
inst_php() {
  local new=$MIG_TARGET old=$MIG_FROM oldbin t b
  [ "$PB_OS" = PB-001 ] || fatal ERR-ENV-422-01 "Cannot identify how PHP is installed and assigned to sites on this server."
  if [ -z "$old" ]; then                                    # the branch of the system default, else the newest one below
    b=$(readlink -f /usr/bin/php 2>/dev/null); [ -n "$b" ] && { b=$(php_version "$b") && old=${b%.*}; }
  fi
  [ -n "$old" ] && { php_bin_for "$old"; oldbin=$REPLY; }
  [ "$old" = "$new" ] && fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--target $new (same branch as $old; use fix)"
  head_ "Install PHP $new side by side${old:+ (current $old)}$( ((DRY_RUN)) && echo ' (dry-run)')"
  # FR-UPG-PRE-001 / BR-SCN-016
  local free avail osid=$OS_ID:$OS_VER eol="" pfail=()
  free=$(free_kib /usr); avail=$(awk '/^MemAvailable:/ { printf "%d", $2 / 1024 }' /proc/meminfo 2>/dev/null)
  pre disk_free_mb ">= 2048" "$((${free:-0} / 1024))" $(( ${free:-0} >= 2097152 )); (( ${free:-0} >= 2097152 )) || pfail+=(disk)
  pre mem_available_mb ">= 512" "${avail:-0}" $(( ${avail:-0} >= 512 )); (( ${avail:-0} >= 512 )) || pfail+=(ram)
  pre privilege "root" "euid $EUID" 1
  eol=$(awk -v k="$osid" '$1 == k { print $2 }' <<<"$OS_EOL")
  if [ -n "$eol" ] && [[ $eol < $(date -u +%F) ]]; then pre os_supported "supported" "$osid (end of support $eol)" 0; pfail+=(os)
  else pre os_supported "supported" "$osid${eol:+ (until $eol)}" 1; fi
  local cand need_repo=0
  if apt_candidate "php$new-fpm"; then cand=$REPLY; INST_SOURCE=package
    grep -rqsE 'ppa.launchpadcontent.net/ondrej/php|packages.sury.org/php' /etc/apt/sources.list.d/ && INST_SOURCE=repo:ondrej
    pre repo_has_target "php$new-fpm candidate" "$cand" 1
  elif (( MIG_ADD_REPO )); then need_repo=1; repo_kind; INST_SOURCE=repo:$( [ "$REPLY" = ppa ] && echo ppa:ondrej/php || echo packages.sury.org/php)
    pre repo_has_target "php$new-fpm candidate" "none; --add-repo: $INST_SOURCE" 1
  else pre repo_has_target "php$new-fpm candidate" "none (add the repository with --add-repo)" 0; pfail+=(repo); fi
  if (( ${#pfail[@]} )); then
    msg ERR-SCN-412-01 "The server does not meet the side-by-side install conditions: {detail}." detail="${pfail[*]}"
    printf '%s\n' "$REPLY" >&2; add_error ERR-SCN-412-01 "$REPLY" host
    inst_result 2
  fi
  # extensions of $OLD (BR-SCN-045, PB-001 step 4)
  local m sfx exts=() seen=" "
  if [ -n "$oldbin" ]; then
    while IFS= read -r m; do
      php_ext_pkg "$m" "$new"; sfx=$REPLY; [ -n "$sfx" ] || continue
      [[ $seen == *" $sfx "* ]] && continue; seen+="$sfx "; exts+=("$sfx")
    done < <(php_modules "$oldbin")
  fi
  INST_PKGS=("php$new-fpm" "php$new-cli")
  for sfx in ${exts[@]+"${exts[@]}"}; do
    if (( need_repo )) || apt_candidate "php$new-$sfx"; then INST_PKGS+=("php$new-$sfx")
    else INST_NOT+=("$sfx: no package php$new-$sfx"); fi
  done
  if (( DRY_RUN )); then
    (( need_repo )) && change repo create "$INST_SOURCE" "" "" "BR-ENV-004 (SEMI)"
    change link modify "alternatives php, php-fpm.sock" "" "" "update-alternatives --set <current value> (BR-SCN-012)"
    local p; for p in "${INST_PKGS[@]}"; do change package install "$p" "" "" "apt-get install -y"; done
    change file create "/etc/php/$new/{fpm,cli}/conf.d" "" "" "custom ini of PHP $old (FR-UPG-CFG-002)"
    change service restart "php$new-fpm"
    say "  packages: ${INST_PKGS[*]}"
    say "Dry-run: nothing was changed."
    inst_result 0
  fi
  confirm "migrate install --runtime php --target $new"
  t=$(now_ms); ensure_backup_dir
  AUDIT_PLAN_ID=$MIG_PLAN; audit_intent migrate_install
  record note "packages installed by migrate install are not removed by rollback: ${INST_PKGS[*]}"
  printf 'MANIFEST_WRITTEN\n' >"$BACKUP_DIR/phase"
  # step 3: pin the current defaults of php and php-fpm.sock (BR-SCN-012)
  local g out val st link pins=()
  for g in php php-fpm.sock; do
    if out=$(LC_ALL=C update-alternatives --query "$g" 2>/dev/null); then
      val=$(awk '/^Value:/ { print $2 }' <<<"$out"); st=$(awk '/^Status:/ { print $2 }' <<<"$out"); link=$(awk '/^Link:/ { print $2 }' <<<"$out")
      if [ "$st" = auto ]; then record link "alt:$g" auto; else record link "alt:$g" "$val"; fi
      [ -n "$val" ] && update-alternatives --set "$g" "$val" >/dev/null 2>&1
      pins+=("$g ${link} $(readlink -f "$link" 2>/dev/null)")
    else record note "no alternatives group $g"; fi
  done
  step INST-PIN 'done' "$t" "pinned: ${pins[*]:-none}"
  # step 2: repository (SEMI, BR-ENV-004)
  if (( need_repo )); then
    t=$(now_ms)
    if ! inst_add_repo; then
      mig_error ERR-ENV-424-01 "Installing {runtime} {target} failed: {detail}." runtime=PHP target="$new" detail="$REPLY"
      step INST-REPO failed "$t" "$REPLY" ERR-ENV-424-01; inst_finish 2
    fi
    step INST-REPO 'done' "$t" "$REPLY"
    local keep=("php$new-fpm" "php$new-cli") p; INST_NOT=()
    for p in "${INST_PKGS[@]:2}"; do if apt_candidate "$p"; then keep+=("$p"); else INST_NOT+=("${p#php"$new"-}: no package $p"); fi; done
    INST_PKGS=("${keep[@]}")
  fi
  # step 5: install (no meta package php$NEW)
  t=$(now_ms)
  local log="$BACKUP_DIR/apt-install.log"
  if ! svc_run env DEBIAN_FRONTEND=noninteractive apt-get install -y -q -o Dpkg::Options::=--force-confold "${INST_PKGS[@]}" >"$log" 2>&1; then
    mig_error ERR-ENV-424-01 "Installing {runtime} {target} failed: {detail}." runtime=PHP target="$new" detail="apt-get install exit (see $log): $(tail -n 2 "$log" | tr '\n' ' ')"
    step INST-PKG failed "$t" "apt-get install" ERR-ENV-424-01; inst_pin_check "${pins[@]}"; inst_finish 2
  fi
  step INST-PKG 'done' "$t" "${#INST_PKGS[@]} package(s): ${INST_PKGS[*]}"
  RT_BRANCH=(); php_bin_for "$new"; INST_NEW_BIN=${REPLY:-/usr/bin/php$new}
  # step 6: defaults unchanged
  t=$(now_ms)
  if ! inst_pin_check "${pins[@]}"; then
    mig_error ERR-ENV-424-01 "Installing {runtime} {target} failed: {detail}." runtime=PHP target="$new" detail="$REPLY"
    step INST-PIN-CHECK failed "$t" "$REPLY" ERR-ENV-424-01; inst_finish 2
  fi
  step INST-PIN-CHECK 'done' "$t" "default links unchanged"
  # FR-UPG-CFG-002: custom ini of $OLD
  t=$(now_ms)
  [ -n "$old" ] && inst_copy_ini "$old" "$new"
  step INST-CFG 'done' "$t" "${#INST_COPIED[@]} file(s) copied, ${#INST_DROPPED[@]} directive(s) dropped"
  # start php$NEW-fpm, active <= 15 s, $NEW_BIN runs without Warning/Fatal
  t=$(now_ms)
  local unit="php$new-fpm" i outp
  fpm_test "$new" || { mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$new" site="-"
                       step INST-VERIFY failed "$t" "php-fpm$new -t: ${REPLY:0:200}" ERR-ENV-500-01; inst_finish 2; }
  svc_restart "$unit" >/dev/null 2>&1
  for ((i = 0; i < 15; i++)); do svc_active "$unit" && break; sleep 1; done
  outp=$(svc_run "$INST_NEW_BIN" -r 'exit(0);' 2>&1)
  if ! svc_active "$unit" || grep -qE 'Warning|Fatal' <<<"$outp"; then
    mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$new" site="-"
    step INST-VERIFY failed "$t" "$unit active: $(svc_active "$unit" && echo yes || echo no); ${outp:0:200}" ERR-ENV-500-01; inst_finish 2
  fi
  local have; have=$(php_modules "$INST_NEW_BIN")
  for sfx in ${exts[@]+"${exts[@]}"}; do
    case $sfx in mysql) m=mysqli ;; xml) m=dom ;; opcache) m='zend opcache' ;; *) m=$sfx ;; esac
    if grep -qx "$m" <<<"$have"; then INST_EXT_OK+=("$sfx")
    else [[ " ${INST_NOT[*]} " == *" $sfx:"* ]] || INST_NOT+=("$sfx: not loaded by $INST_NEW_BIN"); fi
  done
  step INST-VERIFY 'done' "$t" "$unit active, $INST_NEW_BIN runs, ${#INST_EXT_OK[@]} extension(s)"
  (( ${#INST_NOT[@]} )) && mig_warn "" "extensions not transferred: ${INST_NOT[*]}"
  inst_finish 0
}

# inst_add_repo: Surý PPA (Ubuntu) or packages.sury.org (Debian); new files are recorded as created.
inst_add_repo() {
  local before after f
  before=$(find /etc/apt/sources.list.d /etc/apt/trusted.gpg.d /etc/apt/keyrings /usr/share/keyrings -maxdepth 1 -type f 2>/dev/null | sort)
  repo_kind
  if [ "$REPLY" = ppa ]; then
    if ! { has add-apt-repository && svc_run add-apt-repository -y ppa:ondrej/php >"$BACKUP_DIR/repo.log" 2>&1; }; then
      inst_repo_record "$before"; before=$(find /etc/apt/sources.list.d /etc/apt/trusted.gpg.d /etc/apt/keyrings /usr/share/keyrings -maxdepth 1 -type f 2>/dev/null | sort)
      inst_ppa_manual || { inst_repo_record "$before"; return 1; }
    fi
  else
    svc_run env DEBIAN_FRONTEND=noninteractive apt-get -y -q install lsb-release ca-certificates curl >"$BACKUP_DIR/repo.log" 2>&1
    curl -fsSLo "$WORK_DIR/debsuryorg-archive-keyring.deb" https://packages.sury.org/debsuryorg-archive-keyring.deb \
      || { REPLY="download of debsuryorg-archive-keyring.deb failed"; return 1; }
    dpkg -i "$WORK_DIR/debsuryorg-archive-keyring.deb" >>"$BACKUP_DIR/repo.log" 2>&1 || { REPLY="dpkg -i keyring failed"; return 1; }
    printf 'deb [signed-by=/usr/share/keyrings/debsuryorg-archive-keyring.gpg] https://packages.sury.org/php/ %s main\n' \
      "$(lsb_release -sc)" >/etc/apt/sources.list.d/php.list
  fi
  inst_repo_record "$before"
  svc_run apt-get update -q >>"$BACKUP_DIR/repo.log" 2>&1
  INST_REPO_ADDED=1
  apt_candidate "php$MIG_TARGET-fpm" || { REPLY="php$MIG_TARGET-fpm has no candidate after adding the repository"; return 1; }
  REPLY="$INST_SOURCE added, php$MIG_TARGET-fpm $REPLY"
}

# inst_ppa_manual: what add-apt-repository does for ppa:ondrej/php when it is missing or broken:
# signing key fingerprint from the Launchpad API, key from keyserver.ubuntu.com (fingerprint checked
# with gpg), deb822 source signed by that key only.
inst_ppa_manual() {
  local fpr got code key="/etc/apt/keyrings/ondrej-ubuntu-php.asc" src
  code=$(. /etc/os-release && echo "${VERSION_CODENAME:-}")
  [ -n "$code" ] || { REPLY="add-apt-repository failed and VERSION_CODENAME is unknown"; return 1; }
  has gpg || { REPLY="add-apt-repository failed and gpg is missing (cannot check the PPA key)"; return 1; }
  fpr=$(curl -fsS --max-time 30 https://launchpad.net/api/1.0/~ondrej/+archive/ubuntu/php 2>>"$BACKUP_DIR/repo.log" |
        grep -oE '"signing_key_fingerprint": *"[0-9A-F]{40}"' | grep -oE '[0-9A-F]{40}')
  [ -n "$fpr" ] || { REPLY="cannot read the signing key of ppa:ondrej/php from launchpad.net"; return 1; }
  curl -fsS --max-time 30 -o "$WORK_DIR/ondrej.asc" "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$fpr" \
    || { REPLY="cannot download key $fpr from keyserver.ubuntu.com"; return 1; }
  got=$(gpg --show-keys --with-colons "$WORK_DIR/ondrej.asc" 2>/dev/null | awk -F: '$1 == "fpr" { print $10; exit }')
  [ "$got" = "$fpr" ] || { REPLY="key from keyserver.ubuntu.com has fingerprint ${got:-none}, expected $fpr"; return 1; }
  mkdir -p /etc/apt/keyrings && install -m 0644 "$WORK_DIR/ondrej.asc" "$key"
  src="/etc/apt/sources.list.d/ondrej-ubuntu-php-$code.sources"
  printf 'Types: deb\nURIs: https://ppa.launchpadcontent.net/ondrej/php/ubuntu/\nSuites: %s\nComponents: main\nSigned-By: %s\n' "$code" "$key" >"$src"
  chmod 0644 "$src"
  log "ppa:ondrej/php added without add-apt-repository (key $fpr)"
}

inst_repo_record() { # inst_repo_record BEFORE: record created for every new repository/key file
  local after f
  after=$(find /etc/apt/sources.list.d /etc/apt/trusted.gpg.d /etc/apt/keyrings /usr/share/keyrings -maxdepth 1 -type f 2>/dev/null | sort)
  while IFS= read -r f; do [ -n "$f" ] && record created "$f"; done < <(comm -13 <(printf '%s\n' "$1") <(printf '%s\n' "$after"))
}

# inst_pin_check "GROUP LINK TARGET"...: default links unchanged; else restore them (UC-UPG-001 7a).
inst_pin_check() {
  local e g l want now bad=""
  for e in "$@"; do
    read -r g l want <<<"$e"; [ -n "$l" ] || continue
    now=$(readlink -f "$l" 2>/dev/null)
    if [ "$now" != "$want" ]; then bad+="$l -> $now (was $want); "; update-alternatives --set "$g" "$want" >/dev/null 2>&1; fi
  done
  REPLY="default link changed: $bad"; [ -z "$bad" ]
}

# inst_copy_ini OLD NEW: conf.d files that no package owns + non-default php.ini values (FR-UPG-CFG-002).
inst_copy_ini() {
  local old=$1 new=$2 sapi f dest name drop line k changed
  drop=" $(removed_directives "$old" "$new" | tr '\n' ' ') "
  for sapi in fpm cli; do
    [ -d "/etc/php/$new/$sapi/conf.d" ] || continue
    for f in /etc/php/"$old"/"$sapi"/conf.d/*.ini; do
      [ -f "$f" ] && [ ! -L "$f" ] || continue
      name=${f##*/}
      [ "$name" = zz-php-quickpatch-mitigation.ini ] && continue          # never carried over
      dpkg -S "$f" >/dev/null 2>&1 && continue
      dest="/etc/php/$new/$sapi/conf.d/$name"
      [ -e "$dest" ] && { INST_NOT+=("$f: $dest exists"); continue; }
      record created "$dest"
      while IFS= read -r line; do
        k=${line%%=*}; k=${k//[[:space:]]/}
        if [ -n "$k" ] && [[ $k != ';'* ]] && [[ $drop == *" $k "* ]]; then INST_DROPPED+=("$k ($f)"); printf '; dropped by php-quickpatch (removed in PHP %s): %s\n' "$new" "$line"; continue; fi
        printf '%s\n' "$line"
      done <"$f" >"$dest"
      chmod 0644 "$dest"; INST_COPIED+=("$f -> $dest")
    done
    # php.ini values that differ from the packaged production defaults
    local ini="/etc/php/$old/$sapi/php.ini" ref="/usr/lib/php/$old/php.ini-production"
    [ "$sapi" = cli ] && [ -f "/usr/lib/php/$old/php.ini-production.cli" ] && ref="/usr/lib/php/$old/php.ini-production.cli"
    [ -f "$ini" ] && [ -f "$ref" ] || continue
    changed=$(diff <(grep -E '^[a-zA-Z_.]+[[:space:]]*=' "$ref" | sed -E 's/[[:space:]]*=[[:space:]]*/ = /' | sort) \
                   <(grep -E '^[a-zA-Z_.]+[[:space:]]*=' "$ini" | sed -E 's/[[:space:]]*=[[:space:]]*/ = /' | sort) | sed -n 's/^> //p')
    [ -n "$changed" ] || continue
    dest="/etc/php/$new/$sapi/conf.d/90-php-quickpatch-from-$old.ini"
    [ -e "$dest" ] && continue
    record created "$dest"
    {
      printf '; php.ini values of PHP %s (%s) that differ from the packaged defaults, copied by php-quickpatch\n' "$old" "$ini"
      while IFS= read -r line; do
        k=${line%% *}
        if [[ $drop == *" $k "* ]]; then INST_DROPPED+=("$k ($ini)"); continue; fi
        printf '%s\n' "$line"
      done <<<"$changed"
    } >"$dest"
    chmod 0644 "$dest"; INST_COPIED+=("$ini (non-default values) -> $dest")
  done
}

inst_finish() { # inst_finish CODE: audit result + result
  audit_result migrate_install "$1"
  inst_result "$1"
}

inst_result() { # inst_result CODE: result object of migrate install (api-spec-cli-json §9)
  local jp jc jd je jn jpre js cfg
  jas ${INST_PKGS[@]+"${INST_PKGS[@]}"}; jp=$REPLY; jas ${INST_COPIED[@]+"${INST_COPIED[@]}"}; jc=$REPLY
  jas ${INST_DROPPED[@]+"${INST_DROPPED[@]}"}; jd=$REPLY; jas ${INST_EXT_OK[@]+"${INST_EXT_OK[@]}"}; je=$REPLY
  jas ${INST_NOT[@]+"${INST_NOT[@]}"}; jn=$REPLY; jarr INST_PRE; jpre=$REPLY; jarr J_STEPS; js=$REPLY
  jo copied=j:"$jc" dropped_directives=j:"$jd" extensions_installed=j:"$je" not_transferable=j:"$jn"; cfg=$REPLY
  jo runtime=s:"$MIG_RUNTIME" target=s:"$MIG_TARGET" new_bin=S:"$INST_NEW_BIN" install_source=S:"$INST_SOURCE" \
     repo_added=b:$INST_REPO_ADDED packages=j:"$jp" cfg_report=j:"$cfg" preconditions=j:"$jpre" \
     run_id=S:"$( ((DRY_RUN)) || echo "${RUN_ID:-}")" steps=j:"$js"
  local res=$REPLY
  (( DRY_RUN )) && { mig_preview; json_merge "$res" "$REPLY"; res=$REPLY; }
  [ -n "${RUN_ID:-}" ] && (( ! DRY_RUN )) && say "  rollback: $0 rollback $RUN_ID"
  finish "$1" "$res"
}

# mig_preview: REPLY = {"preview":…,"fingerprint":…} of a migrate dry-run (api-spec-cli-json §4).
mig_preview() {
  local ch af notes=() level=full
  jarr J_CHANGES; ch=$REPLY; jarr J_AFFECTED; af=$REPLY
  [[ $ch == *'"type":"package"'* ]] && { level=partial; notes+=("Packages installed or removed with apt are not undone by rollback"); }
  jas ${notes[@]+"${notes[@]}"}
  jo level=s:"$level" rollback_command=S:"$0 rollback <run_id>" notes=j:"$REPLY"; local rev=$REPLY
  jo expected_s=j:null scope=s:"$( [ "$MIG_SUB" = switch ] && echo site || echo runtime)" basis=s:"graceful reload / restart of the listed services"; local dis=$REPLY
  jo changes=j:"$ch" affected=j:"$af" disruption=j:"$dis" reversibility=j:"$rev" requires_retype=j:null; local pv=$REPLY
  jo bundle_id=S:"$DATA_BUNDLE_ID" scan_fingerprint=S:"${SCAN_FP:-}" catalog_version=S:"$CATALOG_VERSION"; local fp=$REPLY
  jo preview=j:"$pv" fingerprint=j:"$fp"
}

# --- Node.js (PB-015: official tarball into /opt/node-<major>) --------------------------------------------
inst_node() {
  local major=$MIG_TARGET prefix="/opt/node-$MIG_TARGET" ver arch tarball sums t free avail
  head_ "Install Node.js $major side by side in $prefix$( ((DRY_RUN)) && echo ' (dry-run)')"
  free=$(free_kib /opt); avail=$(awk '/^MemAvailable:/ { printf "%d", $2 / 1024 }' /proc/meminfo 2>/dev/null)
  local pfail=()
  pre disk_free_mb ">= 2048" "$((${free:-0} / 1024))" $(( ${free:-0} >= 2097152 )); (( ${free:-0} >= 2097152 )) || pfail+=(disk)
  pre mem_available_mb ">= 512" "${avail:-0}" $(( ${avail:-0} >= 512 )); (( ${avail:-0} >= 512 )) || pfail+=(ram)
  pre privilege "root" "euid $EUID" 1
  case $(uname -m) in x86_64) arch=x64 ;; aarch64) arch=arm64 ;; armv7l) arch=armv7l ;; ppc64le) arch=ppc64le ;; s390x) arch=s390x ;; *) arch="" ;; esac
  if [ -z "$arch" ]; then
    fatal ERR-SCN-412-03 "Node.js {target} cannot run on {os} ({detail})." target="$major" os="$OS_ID $OS_VER" detail="arch $(uname -m)"
  fi
  ver=$(node_latest "$major" 2>/dev/null) || ver=""
  if [ -n "$ver" ]; then pre repo_has_target "node v$major.x on $NODE_BASE_URL" "v$ver" 1
  else pre repo_has_target "node v$major.x on $NODE_BASE_URL" "not found (offline or no such line)" 0; pfail+=(repo); fi
  if (( ${#pfail[@]} )); then
    msg ERR-SCN-412-01 "The server does not meet the side-by-side install conditions: {detail}." detail="${pfail[*]}"
    printf '%s\n' "$REPLY" >&2; add_error ERR-SCN-412-01 "$REPLY" host; inst_result 2
  fi
  [ -e "$prefix" ] && fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--target $major ($prefix exists)"
  tarball="node-v$ver-linux-$arch.tar.xz"; INST_SOURCE=tarball; INST_PKGS=("$tarball"); INST_NEW_BIN="$prefix/bin/node"
  if (( DRY_RUN )); then
    change file create "$prefix" "" "$ver" "install $tarball (SHASUMS256.txt checked)"
    say "Dry-run: nothing was changed."; inst_result 0
  fi
  confirm "migrate install --runtime node --target $major"
  t=$(now_ms); ensure_backup_dir
  AUDIT_PLAN_ID=$MIG_PLAN; audit_intent migrate_install
  fetch "$NODE_BASE_URL/v$ver/$tarball" "$WORK_DIR/$tarball" && sums=$(fetch "$NODE_BASE_URL/v$ver/SHASUMS256.txt") || {
    mig_error ERR-ENV-424-01 "Installing {runtime} {target} failed: {detail}." runtime=Node.js target="$major" detail="download of $tarball failed"
    step INST-PKG failed "$t" "download" ERR-ENV-424-01; inst_finish 2; }
  if ! (cd "$WORK_DIR" && grep " $tarball\$" <<<"$sums" | sha256sum -c --status); then
    mig_error ERR-PTCH-502-01 "checksum mismatch for {file}" file="$tarball"
    step INST-PKG failed "$t" "checksum" ERR-PTCH-502-01; inst_finish 2
  fi
  record created "$prefix"
  printf 'MANIFEST_WRITTEN\n' >"$BACKUP_DIR/phase"
  mkdir -p "$prefix" && tar -xJf "$WORK_DIR/$tarball" -C "$prefix" --strip-components=1 --no-same-owner
  step INST-PKG 'done' "$t" "$tarball -> $prefix (SHASUMS256.txt ok)"
  t=$(now_ms)
  local out; out=$(svc_run "$INST_NEW_BIN" -e 'process.exit(0)' 2>&1)
  if [ $? -ne 0 ]; then
    local why=exit; [[ $out == *GLIBC_* ]] && why=glibc
    mig_error ERR-SCN-412-03 "Node.js {target} cannot run on {os} ({detail})." target="$major" os="$OS_ID $OS_VER" detail="$why: ${out:0:200}"
    step INST-VERIFY failed "$t" "${out:0:200}" ERR-SCN-412-03; inst_finish 2
  fi
  [ "$(readlink -f /usr/bin/node 2>/dev/null)" = "$(readlink -f "$INST_NEW_BIN")" ] && mig_warn "" "/usr/bin/node points to the new prefix"
  step INST-VERIFY 'done' "$t" "$INST_NEW_BIN $(svc_run "$INST_NEW_BIN" -v)"
  inst_finish 0
}

# --- remove-old (FR-UPG-RMV-001, BR-SCN-014) -------------------------------------------------------------
mig_remove_old() {
  case $MIG_RUNTIME in php) [[ $MIG_FROM =~ ^[5-9]\.[0-9]$ ]] || arg_error "--from ${MIG_FROM:-}" ;;
                       node) [[ $MIG_FROM =~ ^[0-9]{1,3}$ ]] || arg_error "--from ${MIG_FROM:-}" ;;
                       *) arg_error "--runtime ${MIG_RUNTIME:-}" ;; esac
  (( IS_ROOT )) || fatal ERR-CLI-403-01 "{command} requires root." command="migrate remove-old"
  (( DRY_RUN )) || [ -n "$MIG_REASON" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--reason (second confirmation of a SEMI item, 20-500 characters)"
  mig_inventory
  local old=$MIG_FROM users=() s last=0 e f idle rid prefix="" pkgs=()
  for s in "${!S_BRANCH[@]}"; do [ "${S_BRANCH[$s]}" = "$old" ] && [ "${S_KIND[$s]}" != unmapped ] && users+=("site:$s"); done
  if [ "$MIG_RUNTIME" = php ]; then
    php_bin_for "$old"; local bin=$REPLY; [ -n "$bin" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--from $old (not installed)"
    runtime_id php "$bin"; rid=$REPLY
    local pid exe                                          # CLI/cron processes of $OLD (FPM workers serve sites, counted above)
    for pid in $(pgrep -f "php$old" 2>/dev/null); do
      exe=$(readlink -f "/proc/$pid/exe" 2>/dev/null)
      [ "$exe" = "$(readlink -f "$bin")" ] && users+=("process:$pid")
    done
    for f in "/var/log/php$old-fpm.log" /etc/php/"$old"/fpm/pool.d/*.conf; do [ -f "$f" ] && { e=$(stat -c %Y "$f"); (( e > last )) && last=$e; }; done
    mapfile -t pkgs < <(dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' "php$old-*" 2>/dev/null | awk '$1 == "ii" { print $2 }')
  else
    prefix="/opt/node-$old"; [ -x "$prefix/bin/node" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--from $old ($prefix/bin/node missing)"
    runtime_id node "$prefix/bin/node"; rid=$REPLY
    local pid; for pid in $(pgrep -x node 2>/dev/null); do
      [ "$(readlink -f "/proc/$pid/exe")" = "$(readlink -f "$prefix/bin/node")" ] && users+=("process:$pid"); done
    e=$(stat -c %Y "$prefix/bin/node"); (( e > last )) && last=$e
  fi
  # the last switch away from $OLD counts as its last use (index.tsv)
  e=$(awk -F'\t' -v o="$old" '$5 ~ ("^" o ">") && $6 == "PASSED" { t = $1 } END { print t }' "$STATE_DIR/switches/index.tsv" 2>/dev/null)
  [ -n "$e" ] && iso_epoch "$e" && (( REPLY > last )) && last=$REPLY
  idle=$(( ($(date +%s) - last) / 86400 ))
  head_ "Remove $MIG_RUNTIME $old (idle $idle day(s))$( ((DRY_RUN)) && echo ' (dry-run)')"
  if (( ${#users[@]} )) || (( idle < 14 )); then
    (( ${#users[@]} )) || users+=("last use $idle day(s) ago")
    msg ERR-UPG-412-01 "Cannot remove {runtime}: {count} sites/processes used it in the last 14 days." runtime="$MIG_RUNTIME $old" count="${#users[@]}"
    printf '%s\n' "$REPLY" >&2; add_error ERR-UPG-412-01 "$REPLY (${users[*]})" "runtime:$rid"
    rmo_result 2 "$rid" "$idle"
  fi
  # switch runs that lose their one-command rollback (BR-SCN-014 exception)
  local run aff=()
  while IFS=$'\t' read -r run _ _ _ _; do
    sw_load "$run" 2>/dev/null || continue
    [ "${SW[from_branch]}" = "$old" ] && [ "${SW[rollback_available]:-1}" = 1 ] && aff+=("$run")
  done < <(idx_runs)
  RMO_AFF=("${aff[@]+"${aff[@]}"}")
  (( ${#aff[@]} )) && mig_warn "" "after removal, rollback is no longer available for switch run(s): ${aff[*]}"
  if (( DRY_RUN )); then
    local p; for p in ${pkgs[@]+"${pkgs[@]}"}; do change package remove "$p"; done
    [ -n "$prefix" ] && change file delete "$prefix"
    say "Dry-run: nothing was changed."; RMO_PKGS=("${pkgs[@]+"${pkgs[@]}"}"); rmo_result 0 "$rid" "$idle"
  fi
  confirm "migrate remove-old --runtime $MIG_RUNTIME --from $old"
  local t; t=$(now_ms); ensure_backup_dir
  audit_intent migrate_remove_old
  if [ "$MIG_RUNTIME" = php ]; then
    record note "removed packages (not reinstalled by rollback): ${pkgs[*]}"
    printf 'MANIFEST_WRITTEN\n' >"$BACKUP_DIR/phase"
    svc_run service "php$old-fpm" stop >/dev/null 2>&1
    if ! svc_run env DEBIAN_FRONTEND=noninteractive apt-get remove -y -q "${pkgs[@]}" >"$BACKUP_DIR/apt-remove.log" 2>&1; then
      mig_error ERR-ENV-424-01 "Installing {runtime} {target} failed: {detail}." runtime=PHP target="$old" detail="apt-get remove failed (see $BACKUP_DIR/apt-remove.log)"
      audit_result migrate_remove_old 2; rmo_result 2 "$rid" "$idle"
    fi
    RMO_PKGS=("${pkgs[@]}")
  else
    local saved; saved="$BACKUP_DIR/node-$(tr / _ <<<"$prefix").tar.gz"
    tar -czf "$saved" -C / "${prefix#/}" && record untar "$saved" /
    printf 'MANIFEST_WRITTEN\n' >"$BACKUP_DIR/phase"
    rm -rf "$prefix"; RMO_PKGS=("$prefix")
  fi
  for run in ${aff[@]+"${aff[@]}"}; do sw_load "$run" && { SW[rollback_available]=0; sw_save; }; done
  step RMV 'done' "$t" "removed ${RMO_PKGS[*]}"
  audit_result migrate_remove_old 0
  rmo_result 0 "$rid" "$idle"
}

rmo_result() { # rmo_result CODE RUNTIME_ID IDLE_DAYS
  local r a=() jp ja
  for r in ${RMO_AFF[@]+"${RMO_AFF[@]}"}; do jo run_id=s:"$r" rollback_available=b:0; a+=("$REPLY"); done
  jas ${RMO_PKGS[@]+"${RMO_PKGS[@]}"}; jp=$REPLY; jarr a; ja=$REPLY
  jo runtime_id=S:"$2" idle_days=n:"$3" removed_packages=j:"$jp" affected_switches=j:"$ja"
  local res=$REPLY
  (( DRY_RUN )) && { mig_preview; json_merge "$res" "$REPLY"; res=$REPLY; }
  finish "$1" "$res"
}
