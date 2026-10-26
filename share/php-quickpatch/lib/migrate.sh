# shellcheck shell=bash disable=SC2034  # globals shared with php-quickpatch.sh and the other lib/*.sh
# migrate (M5): side-by-side install, switch one site, health check, roll back one site
# (FR-UPG-*, FR-CLI-CMD-003, DOC-SRS-QP-ENV-001 §5). Sourced by php-quickpatch.sh when
# MODE=migrate; uses its helpers (jo, msg, fatal, backup_file, record, audit_*, inventory).
#
# Data of a switch run (run_id = backup directory name, YYYYmmdd-HHMMSS):
#   STATE_DIR/switches/index.tsv        one line per state change (erd-feeds-files §9.4 + site_key, note)
#   STATE_DIR/switches/<site_key>.lock  site lock held from C1 to the end of C12/R7 (BR-ENV-013)
#   STATE_DIR/backups/<run_id>/manifest rollback steps (§5.4 order)
#   STATE_DIR/backups/<run_id>/switch.json  the switch record (§9.5), switch.vars its key=value twin
#   STATE_DIR/backups/<run_id>/baseline.json, hc.json  health check (DOC-SRS-QP-ENV-002)

MIG_SITE=""; MIG_TARGET=""; MIG_RUNTIME=""; MIG_PLAN=""; MIG_NO_PLAN=0; MIG_REASON=""; MIG_RUNARG=""
MIG_HC_URLS=(); MIG_SET=(); MIG_SET_GIVEN=0; MIG_NO_AUTO_RB=0; MIG_PURGE=0; MIG_BASE_ONLY=0
MIG_FROM=""; MIG_RID=""; MIG_ADD_REPO=0; MIG_HC_SKIP=0; MIG_TERM=0
J_STEPS=(); J_MIG_MANIFEST=()
declare -gA SW=()
INDEX_HEAD=$'#ts\trun_id\tsite_id\tsite_key\tfrom>to\tstatus\tactor\tplan_id\tjob_id\trollback_reason\tnote'
SITE_ID_RE='^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,252}$'

# --- small helpers --------------------------------------------------------------------
iso_now() { date -u +%Y-%m-%dT%H:%M:%S.%3NZ; }
now_ms() { date +%s%3N; }
clean() { REPLY=${1//$'\t'/ }; REPLY=${REPLY//$'\n'/ }; REPLY=${REPLY//$'\r'/}; }
actor_of() { REPLY=${QP_ACTOR:-cli:$(id -un 2>/dev/null || echo "$EUID")}; }

# mig_error CODE DEFAULT_EN key=value...: message into errors[] and stderr, no exit.
mig_error() { local c=$1 t=$2 keep=$REPLY; shift 2; msg "$c" "$t" "$@"; printf '%s\n' "$REPLY" >&2; log "ERROR $c: $REPLY"; add_error "$c" "$REPLY"; REPLY=$keep; }
mig_warn() { local c=$1 t=$2 keep=$REPLY; shift 2; msg "$c" "$t" "$@"; warn "$REPLY"; add_warning "$c" "$REPLY"; REPLY=$keep; }

# step NAME STATUS STARTED_MS DETAIL [ERROR_CODE]: one entry of steps[] (api-spec-cli-json §9).
step() {
  local name=$1 st=$2 t0=$3 detail=$4 code=${5:-} t1 started
  t1=$(now_ms); started=$(date -u -d "@$((t0 / 1000))" +%Y-%m-%dT%H:%M:%S 2>/dev/null).$(printf '%03d' $((t0 % 1000)))Z
  clean "$detail"; detail=${REPLY:0:500}
  jo step=s:"$name" status=s:"$st" started_at=s:"$started" duration_ms=n:$((t1 - t0)) detail=S:"$detail" error_code=S:"$code"
  J_STEPS+=("$REPLY")
  case $st in done) say "  [$name] $detail" ;; skipped) say "  [$name] skipped: $detail" ;; *) say "  [$name] FAILED: $detail" ;; esac
  log "step $name $st $detail${code:+ ($code)}"
}

valid_reason() { # valid_reason TEXT MIN: 20/10-500 characters, no control characters
  local t=$1 min=$2 s; s=${t//[[:space:]]/}
  (( ${#s} >= 1 )) && (( ${#t} >= min && ${#t} <= 500 )) && ! [[ $t =~ [[:cntrl:]] ]]
}

# --- arguments ----------------------------------------------------------------------------
migrate_parse() {
  local pos=()
  while [ $# -gt 0 ]; do
    case $1 in
      --json) JSON=1 ;; --dry-run) DRY_RUN=1 ;; --yes|-y) ASSUME_YES=1 ;; --offline) OFFLINE=1 ;;
      --no-restart) NO_RESTART=1 ;;
      --target) [ $# -ge 2 ] || arg_error ""; MIG_TARGET=$2; shift ;;
      --runtime) [ $# -ge 2 ] || arg_error ""; MIG_RUNTIME=$2; shift ;;
      --from) [ $# -ge 2 ] || arg_error ""; MIG_FROM=$2; shift ;;
      --plan) [ $# -ge 2 ] || arg_error ""; MIG_PLAN=$2; shift ;;
      --no-plan) MIG_NO_PLAN=1 ;;
      --reason) [ $# -ge 2 ] || arg_error ""; MIG_REASON=$2; shift ;;
      --hc-url) [ $# -ge 2 ] || arg_error ""; MIG_HC_URLS+=("$2"); shift ;;
      --set) [ $# -ge 2 ] || arg_error ""; MIG_SET+=("$2"); MIG_SET_GIVEN=1; shift ;;
      --no-auto-rollback) MIG_NO_AUTO_RB=1 ;;
      --purge-pool) MIG_PURGE=1 ;;
      --baseline-only) MIG_BASE_ONLY=1 ;;
      --runtime-id) [ $# -ge 2 ] || arg_error ""; MIG_RID=$2; shift ;;
      --add-repo) MIG_ADD_REPO=1 ;;
      --hc-skip) MIG_HC_SKIP=1 ;;
      -*) arg_error "$1" ;;
      *) pos+=("$1") ;;
    esac
    shift
  done
  case $MIG_SUB in
    switch|healthcheck|hc-urls)
      [ ${#pos[@]} -eq 1 ] || arg_error "${pos[1]:-}"; MIG_SITE=${pos[0]} ;;
    rollback)
      [ ${#pos[@]} -ge 1 ] && [ ${#pos[@]} -le 2 ] || arg_error "${pos[2]:-}"; MIG_SITE=${pos[0]}; MIG_RUNARG=${pos[1]:-} ;;
    ack) [ ${#pos[@]} -eq 1 ] || arg_error "${pos[1]:-}"; MIG_RUNARG=${pos[0]} ;;
    status) [ ${#pos[@]} -le 1 ] || arg_error "${pos[1]}"; MIG_SITE=${pos[0]:-} ;;
    install|remove-old) [ ${#pos[@]} -eq 0 ] || arg_error "${pos[0]}" ;;
    *) arg_error "migrate ${MIG_SUB:-}" ;;
  esac
  if [ -n "$MIG_SITE" ] && ! [[ $MIG_SITE =~ $SITE_ID_RE ]]; then arg_error "$MIG_SITE"; fi
  if [ -n "$MIG_RUNARG" ] && ! [[ $MIG_RUNARG =~ ^[0-9]{8}-[0-9]{6}$ ]]; then
    fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="run_id $MIG_RUNARG"
  fi
  if [ -n "$MIG_REASON" ] && ! valid_reason "$MIG_REASON" 20; then
    fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--reason (20-500 characters)"
  fi
  return 0
}

# --- locks (BR-JOB-002, BR-ENV-013) -----------------------------------------------------------
lock_state() { # lock_state -x|-s: STATE_DIR/.lock on fd 9
  exec 9>"$STATE_DIR/.lock"
  if ! flock "$1" -n 9; then
    msg ERR-CLI-423-01 "Another php-quickpatch run is in progress."; echo "$REPLY" >&2; add_error ERR-CLI-423-01 "$REPLY" host; finish 2
  fi
}
unlock_state() { flock -u 9 2>/dev/null; }

switches_dir() { [ -d "$STATE_DIR/switches" ] || mkdir -m 0700 "$STATE_DIR/switches"; REPLY="$STATE_DIR/switches"; }

# lock_site KEY: the site lock on fd 7; fails when another process holds it.
lock_site() {
  switches_dir
  exec 7>"$STATE_DIR/switches/$1.lock"
  flock -x -n 7
}
unlock_site() { flock -u 7 2>/dev/null; exec 7>&-; }

# idx_append RUN SITE KEY FROMTO STATUS PLAN REASON [NOTE]: one line of switches/index.tsv.
idx_append() {
  switches_dir
  local f="$STATE_DIR/switches/index.tsv" a; actor_of; a=$REPLY
  [ -s "$f" ] || printf '%s\n' "$INDEX_HEAD" >>"$f"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(iso_now)" "$1" "$2" "$3" "$4" "$5" "$a" "${6:--}" \
    "${QP_JOB_ID:--}" "${7:--}" "${8:--}" >>"$f"
  chmod 0600 "$f" 2>/dev/null
}

# idx_last RUN: REPLY = last index line of the run ("" when none).
idx_last() {
  REPLY=$(awk -F'\t' -v r="$1" '$2 == r { l = $0 } END { print l }' "$STATE_DIR/switches/index.tsv" 2>/dev/null)
}

# idx_runs: "run_id<TAB>site_id<TAB>site_key<TAB>status<TAB>acked" of every run, oldest first.
idx_runs() {
  awk -F'\t' '/^#/ { next } NF >= 6 {
      if (!($2 in seen)) { seen[$2] = 1; order[++n] = $2 }
      site[$2] = $3; key[$2] = $4; if ($11 ~ /^ack:/) ack[$2] = 1; else st[$2] = $6 }
    END { for (i = 1; i <= n; i++) { r = order[i]; print r "\t" site[r] "\t" key[r] "\t" st[r] "\t" (ack[r] ? 1 : 0) } }' \
    "$STATE_DIR/switches/index.tsv" 2>/dev/null
}

# --- switch record (switch.vars + switch.json) ----------------------------------------------
SW_KEYS=(run_id site_id site_key pb_id binding_kind binding_ref from_branch to_branch old_bin new_bin old_ep new_ep
         plan_id no_plan_reason install_run_id job_id actor status hc_mode auto_rollback rollback_reason
         rollback_available t_start t_switched t_c9 t_hc_end t_rollback_end docroot owner host port scheme addr
         vhost_check web fpm_pool fpm_socket fpm_error_log fpm_unit fpm_test probe_ok probe_detail verify_method
         verify_ok hc_verdict violations errors acknowledged_at acknowledged_by ack_reason node_unit node_kind
         node_dropin hc_window pool_reused install_kind)

sw_save() { # write switch.vars and switch.json of SW into the run directory
  local d="$STATE_DIR/backups/${SW[run_id]}" k v tmp
  [ -d "$d" ] || return 0
  tmp="$d/.switch.vars.$$"
  ( umask 077; for k in "${SW_KEYS[@]}"; do clean "${SW[$k]:-}"; printf '%s=%s\n' "$k" "$REPLY"; done >"$tmp" ) && mv -f "$tmp" "$d/switch.vars"
  local args=() viol=() x
  for k in "${SW_KEYS[@]}"; do
    v=${SW[$k]:-}
    case $k in
      violations|errors) IFS=';' read -r -a viol <<<"$v"; local arr=(); for x in ${viol[@]+"${viol[@]}"}; do [ -n "$x" ] && arr+=("$x"); done
                         jas ${arr[@]+"${arr[@]}"}; args+=("$k=j:$REPLY") ;;
      auto_rollback|rollback_available|probe_ok|verify_ok)
        if [ -z "$v" ]; then args+=("$k=j:null"); else args+=("$k=b:$v"); fi ;;
      *) args+=("$k=S:$v") ;;
    esac
  done
  jo "${args[@]}"
  tmp="$d/.switch.json.$$"
  ( umask 077; printf '%s\n' "$REPLY" >"$tmp" ) && mv -f "$tmp" "$d/switch.json"
}

sw_load() { # sw_load RUN_ID: SW from backups/RUN/switch.vars
  local f="$STATE_DIR/backups/$1/switch.vars" k v
  SW=()
  [ -f "$f" ] || return 1
  local r; r=$(unsafe_reason "$STATE_DIR/backups/$1" dir) && state_dir_fail "$STATE_DIR/backups/$1" "$r"
  r=$(unsafe_reason "$f" file) && state_dir_fail "$f" "$r"
  while IFS='=' read -r k v; do [ -n "$k" ] && SW[$k]=$v; done <"$f"
  [ -n "${SW[run_id]:-}" ]
}

# sw_status STATUS [REASON]: new state of the current run (index line + record).
sw_status() {
  SW[status]=$1; [ -n "${2:-}" ] && SW[rollback_reason]=$2
  idx_append "${SW[run_id]}" "${SW[site_id]}" "${SW[site_key]}" "${SW[from_branch]}>${SW[to_branch]}" "$1" \
    "${SW[plan_id]:-}" "${SW[rollback_reason]:-}"
  sw_save
}

# switch_json: REPLY = SwitchRecord of SW (api-spec-cli-json §9).
switch_json() {
  local ra=null; [ -n "${SW[rollback_available]:-}" ] && { [ "${SW[rollback_available]}" = 1 ] && ra=true || ra=false; }
  jo run_id=s:"${SW[run_id]}" site_id=s:"${SW[site_id]}" plan_id=S:"${SW[plan_id]:-}" from_branch=S:"${SW[from_branch]:-}" \
     to_branch=S:"${SW[to_branch]:-}" status=s:"${SW[status]}" t_start=S:"${SW[t_start]:-}" t_switched=S:"${SW[t_switched]:-}" \
     t_hc_end=S:"${SW[t_hc_end]:-}" t_rollback_end=S:"${SW[t_rollback_end]:-}" rollback_reason=S:"${SW[rollback_reason]:-}" \
     rollback_available=j:"$ra" actor=S:"${SW[actor]:-}"
}

# --- sites ----------------------------------------------------------------------------------
# mig_inventory: fresh site inventory (same code as scan --only sites) into the S_* arrays.
mig_inventory() {
  [ -n "${MIG_INVENTORIED:-}" ] && return 0
  MIG_INVENTORIED=1
  detect_env >/dev/null 2>&1
  inventory_sites >/dev/null 2>&1 || true
  local bin v rid
  for bin in $(discover_node_bins); do       # Node.js apps of systemd units (PB-017)
    v=$(probe 10 "$bin" -v 2>/dev/null) || continue; v=${v#v}
    runtime_id node "$bin"; rid=$REPLY
    node_apps "$bin" "$rid" "${v%%.*}" >/dev/null 2>&1
  done
  return 0
}

site_known() { [ -n "${S_KIND[$1]:-}" ]; }

# site_index_key SITE_ID: site_key of a site that is not in the inventory any more (from index.tsv).
site_index_key() {
  REPLY=$(awk -F'\t' -v s="$1" '$3 == s { k = $4 } END { print k }' "$STATE_DIR/switches/index.tsv" 2>/dev/null)
}

# --- main -------------------------------------------------------------------------------------
migrate_main() {
  migrate_parse "$@"
  case $MIG_SUB in
    status) lock_state -s; mig_status ;;
    hc-urls) lock_state -x; mig_hc_urls ;;
    ack) lock_state -x; mig_ack ;;
    healthcheck)
      if (( MIG_BASE_ONLY )); then lock_state -s; else lock_state -x; fi
      mig_healthcheck ;;
    switch) if (( DRY_RUN )); then lock_state -s; else lock_state -x; fi; mig_switch ;;
    rollback) if (( DRY_RUN )); then lock_state -s; else lock_state -x; fi; mig_rollback ;;
    install) if (( DRY_RUN )); then lock_state -s; else lock_state -x; fi; mig_install ;;
    remove-old) if (( DRY_RUN )); then lock_state -s; else lock_state -x; fi; mig_remove_old ;;
  esac
}

# mig_busy: BR-ENV-013 / BR-ENV-003 - another run holds a site lock. REPLY = site, remaining.
mig_busy() {
  local f key line run site rem t9 win
  for f in "$STATE_DIR"/switches/*.lock; do
    [ -e "$f" ] || continue
    flock -n "$f" true 2>/dev/null && continue
    key=${f##*/}; key=${key%.lock}
    line=$(awk -F'\t' -v k="$key" '$4 == k { l = $0 } END { print l }' "$STATE_DIR/switches/index.tsv" 2>/dev/null)
    IFS=$'\t' read -r _ run site _ <<<"$line"
    rem=600
    if [ -n "$run" ] && [ -f "$STATE_DIR/backups/$run/switch.vars" ]; then
      t9=$(sed -n 's/^t_c9=//p' "$STATE_DIR/backups/$run/switch.vars"); win=$(sed -n 's/^hc_window=//p' "$STATE_DIR/backups/$run/switch.vars")
      if [ -n "$t9" ] && iso_epoch "$t9"; then rem=$(( REPLY + ${win:-600} - $(date +%s) )); (( rem < 0 )) && rem=0; fi
    fi
    REPLY="${site:-$key}"$'\t'"$rem"; return 0
  done
  return 1
}

busy_or_die() { # stop with ERR-ENV-409-01 when a switch run holds a site lock (dry-run: warning)
  if mig_busy; then
    local site rem; IFS=$'\t' read -r site rem <<<"$REPLY"
    if (( DRY_RUN )); then mig_warn ERR-ENV-409-01 "Site {site} is in its post-switch check; wait {remaining} seconds." site="$site" remaining="$rem"
    else fatal ERR-ENV-409-01 "Site {site} is in its post-switch check; wait {remaining} seconds." site="$site" remaining="$rem"; fi
  fi
}

# interrupted_runs: HC_RUNNING runs whose window ended long ago and whose site lock is free (§6.4).
interrupted_runs() {
  local run site key st ack t9 now; now=$(date +%s)
  while IFS=$'\t' read -r run site key st ack; do
    [ "$st" = HC_RUNNING ] || continue
    [ -e "$STATE_DIR/switches/$key.lock" ] && ! flock -n "$STATE_DIR/switches/$key.lock" true 2>/dev/null && continue
    t9=$(sed -n 's/^t_c9=//p' "$STATE_DIR/backups/$run/switch.vars" 2>/dev/null)
    [ -n "$t9" ] || continue
    iso_epoch "$t9" && (( now - REPLY > 900 )) && printf '%s\t%s\n' "$run" "$site"
  done < <(idx_runs)
}

warn_interrupted() {
  local run site
  while IFS=$'\t' read -r run site; do
    [ -n "$run" ] || continue
    warn "health check of $site was interrupted (run $run); run: $0 migrate healthcheck $site"
    add_warning "" "health check of $site was interrupted (run $run); run migrate healthcheck $site" "site:$site"
  done < <(interrupted_runs)
}

# --- status (read) -----------------------------------------------------------------------------
mig_status() {
  head_ "Switch runs"
  local run site key st ack recs=() locked=false
  while IFS=$'\t' read -r run site key st ack; do
    [ -n "$run" ] || continue
    [ "$st" = ROLLBACK_FAILED ] && [ "$ack" = 0 ] && locked=true
    [ -n "$MIG_SITE" ] && [ "$site" != "$MIG_SITE" ] && continue
    if sw_load "$run"; then
      SW[status]=$st; switch_json
      local base=$REPLY extra; jo acknowledged_at=S:"${SW[acknowledged_at]:-}" hc_verdict=S:"${SW[hc_verdict]:-}"; extra=$REPLY
      json_merge "$base" "$extra"; recs+=("$REPLY")
      say "  $run  $site  ${SW[from_branch]}>${SW[to_branch]}  $st${SW[rollback_reason]:+ (${SW[rollback_reason]})}$([ "$ack" = 1 ] && echo ' acknowledged')"
    fi
  done < <(idx_runs)
  (( ${#recs[@]} )) || say "  no switch run"
  warn_interrupted
  jarr recs; local jr=$REPLY
  jo switches=j:"$jr" locked_after_rollback_failed=b:"$([ $locked = true ] && echo 1 || echo 0)"
  finish 0 "$REPLY"
}

# --- hc-urls (control) ----------------------------------------------------------------------------
site_conf_path() { # site_conf_path KEY: sites.d/<site_key>.conf (root /etc, else ~/.config)
  local d
  if (( IS_ROOT )); then d=/etc/php-quickpatch/sites.d; else d="${HOME:-/nonexistent}/.config/php-quickpatch/sites.d"; fi
  REPLY="$d/$1.conf"
}

# site_conf_urls SITE KEY: hc_url lines of sites.d (only when the first line names the site).
site_conf_lines() {
  site_conf_path "$2"; local f=$REPLY
  [ -f "$f" ] || return 0
  [ "$(head -n1 "$f")" = "# qp-site-id = $1" ] || { warn "$f ignored: its first line does not name $1"; return 0; }
  tail -n +2 "$f"
}

# url_ok URL SITE: BR-HC-002 (http/https, host of the site, no userinfo, no fragment, <= 2048).
url_ok() {
  local u=$1 site=$2 rest host n
  (( ${#u} <= 2048 )) || { REPLY="longer than 2048 characters"; return 1; }
  if [[ $u == /* ]]; then [[ $u == *'#'* ]] && { REPLY="fragment"; return 1; }; return 0; fi
  [[ $u =~ ^https?:// ]] || { REPLY="scheme is not http or https"; return 1; }
  [[ $u == *'#'* ]] && { REPLY="fragment"; return 1; }
  rest=${u#*://}; host=${rest%%/*}; host=${host%%\?*}
  [[ $host == *@* ]] && { REPLY="user information in the URL"; return 1; }
  host=${host%%:*}; host=${host,,}
  for n in ${S_NAMES[$site]:-}; do [ "${n,,}" = "$host" ] && return 0; done
  REPLY="host $host is not a name of the site"; return 1
}

mig_hc_urls() {
  mig_inventory
  site_known "$MIG_SITE" || fatal ERR-CON-404-01 "{resource} not found." resource="site $MIG_SITE"
  local key=${S_KEY[$MIG_SITE]} u good=() lines=()
  (( ${#MIG_SET[@]} <= 10 )) || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--set (at most 10 URLs)"
  for u in ${MIG_SET[@]+"${MIG_SET[@]}"}; do
    url_ok "$u" "$MIG_SITE" || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--set $u ($REPLY)"
    good+=("$u")
  done
  site_conf_path "$key"; local f=$REPLY
  audit_intent site_set_hc_urls
  mkdir -p "${f%/*}" && chmod 0755 "${f%/*}" 2>/dev/null
  while IFS= read -r u; do [[ $u =~ ^[[:space:]]*hc_url[[:space:]] ]] || lines+=("$u"); done < <(site_conf_lines "$MIG_SITE" "$key")
  {
    printf '# qp-site-id = %s\n' "$MIG_SITE"
    for u in ${lines[@]+"${lines[@]}"}; do printf '%s\n' "$u"; done
    for u in ${good[@]+"${good[@]}"}; do printf 'hc_url %s\n' "$u"; done
  } >"$f.tmp.$$" && chmod 0644 "$f.tmp.$$" && mv -f "$f.tmp.$$" "$f"
  ok "health check URLs of $MIG_SITE: ${#good[@]} declared ($f)"
  audit_result site_set_hc_urls 0
  jas ${good[@]+"${good[@]}"}; local ju=$REPLY
  jo site_id=s:"$MIG_SITE" hc_urls=j:"$ju" config_file=s:"$f"
  finish 0 "$REPLY"
}

# --- ack (control, FR-UPG-ACK-001) ----------------------------------------------------------------
mig_ack() {
  [ -n "$MIG_REASON" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--reason (20-500 characters)"
  idx_last "$MIG_RUNARG"
  [ -n "$REPLY" ] && sw_load "$MIG_RUNARG" || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="run_id $MIG_RUNARG"
  local st; st=$(awk -F'\t' -v r="$MIG_RUNARG" '$2 == r && $11 !~ /^ack:/ { s = $6 } END { print s }' "$STATE_DIR/switches/index.tsv")
  if [ -n "${SW[acknowledged_at]:-}" ] || [[ ! $st =~ ^(ROLLED_BACK|HC_FAILED_KEPT|ROLLBACK_FAILED)$ ]]; then
    fatal ERR-UPG-409-04 "Switch run {run_id} is {status} or was already acknowledged at {acknowledged_at}; no acknowledgement is needed." \
      run_id="$MIG_RUNARG" status="$st" acknowledged_at="${SW[acknowledged_at]:--}"
  fi
  AUDIT_PLAN_ID=${SW[plan_id]:-}
  audit_intent switch_ack
  mig_inventory
  local site=${SW[site_id]} binding=null
  if [ -n "${S_KIND[$site]:-}" ]; then
    jo binding_kind=s:"${S_KIND[$site]}" binding_ref=s:"${S_REFS[$site]}" current_branch=S:"${S_BRANCH[$site]}" \
       current_bin=S:"${S_BIN[$site]}" runtime_endpoint=S:"${S_EP[$site]}" runtime_id=S:"${S_RID[$site]}"; binding=$REPLY
  fi
  actor_of; local by=$REPLY at; at=$(iso_now)
  SW[acknowledged_at]=$at; SW[acknowledged_by]=$by; clean "$(redact_text "$MIG_REASON")"; SW[ack_reason]=$REPLY
  sw_save
  idx_append "$MIG_RUNARG" "$site" "${SW[site_key]}" "${SW[from_branch]}>${SW[to_branch]}" "$st" "${SW[plan_id]:-}" \
    "${SW[rollback_reason]:-}" "ack:$at"
  local released=false others=0 r s k st2 a
  while IFS=$'\t' read -r r s k st2 a; do [ "$st2" = ROLLBACK_FAILED ] && [ "$a" = 0 ] && others=$((others + 1)); done < <(idx_runs)
  [ "$st" = ROLLBACK_FAILED ] && (( others == 0 )) && released=true
  local next=()
  if (( others == 0 )); then
    next+=("$site")
    if [ -n "${SW[plan_id]:-}" ] && plan_next_site "${SW[plan_id]}" "$site"; then [ -n "$REPLY" ] && next+=("$REPLY"); fi
  fi
  ok "run $MIG_RUNARG ($site, $st) acknowledged by $by"
  audit_result switch_ack 0
  jas ${next[@]+"${next[@]}"}; local jn=$REPLY
  jo run_id=s:"$MIG_RUNARG" site_id=s:"$site" plan_id=S:"${SW[plan_id]:-}" status=s:"$st" acknowledged_at=s:"$at" \
     acknowledged_by=s:"$by" binding_now=j:"$binding" switch_lock_released=b:"$([ $released = true ] && echo 1 || echo 0)" \
     next_allowed_sites=j:"$jn"
  local ackj=$REPLY
  jo acknowledgement=j:"$ackj"
  finish 0 "$REPLY"
}

# redact_text TEXT: BR-SEC-006 on free text (password=, token=, Authorization:).
redact_text() {
  sed -E 's/(password|passwd|token|secret|api[_-]?key)=[^ &]*/\1=***/Ig; s/(Authorization:)[^,;]*/\1 ***/Ig' <<<"$1"
}

# plan_next_site PLAN SITE: REPLY = the site after SITE in site_order[] (Python plan store).
plan_next_site() {
  REPLY=""
  python_ok || return 1
  REPLY=$(qp_py plan-gate "$1" --site "$2" --next 2>/dev/null) || { REPLY=""; return 1; }
}

# --- switch (FR-UPG-SWT-001, §5.1 C1-C12) ---------------------------------------------------------
# target_bin KIND BRANCH: REPLY = binary of the target branch on this machine.
target_bin() {
  local kind=$1 br=$2 b v
  if [ "$kind" = php ]; then php_bin_for "$br"; return; fi
  REPLY=""
  for b in /opt/node-"$br"/bin/node $(discover_node_bins); do
    [ -x "$b" ] || continue
    v=$(probe 10 "$b" -v 2>/dev/null) || continue; v=${v#v}
    [ "${v%%.*}" = "$br" ] && { REPLY=$(readlink -f "$b"); return; }
  done
}

# plan_gate: FR-UPG-SEQ-001 checks of a plan (Python plan store); errors in errors[], exit 2.
plan_gate() {
  local out code msg n=0
  python_ok || fatal ERR-CLI-424-01 "{command} requires Python 3.6+." command="migrate switch --plan"
  out=$(qp_py plan-gate "$MIG_PLAN" --site "$MIG_SITE" --target "$MIG_TARGET" 2>/dev/null)
  while IFS=$'\t' read -r code msg; do
    [ -n "$code" ] || continue
    [ "$code" = OK ] && continue
    printf '%s\n' "$msg" >&2; add_error "$code" "$msg" "site:$MIG_SITE"; n=$((n + 1))
  done <<<"$out"
  [ -n "$out" ] || { add_error ERR-PLAN-404-01 "plan $MIG_PLAN could not be read" host; n=1; }
  (( n == 0 )) || finish 2
}

# unacked_rollback_failed: REPLY = site of an unacknowledged ROLLBACK_FAILED run (ERR-UPG-423-01).
unacked_rollback_failed() {
  local run site key st ack
  while IFS=$'\t' read -r run site key st ack; do
    [ "$st" = ROLLBACK_FAILED ] && [ "$ack" = 0 ] && { REPLY=$site; return 0; }
  done < <(idx_runs)
  return 1
}

mig_switch() {
  mig_inventory
  site_known "$MIG_SITE" || fatal ERR-ENV-422-02 "Cannot determine which PHP site {site} uses." site="$MIG_SITE"
  local site=$MIG_SITE kind=php pb=${S_PB[$MIG_SITE]} bk=${S_KIND[$MIG_SITE]}
  [ "$bk" = systemd_execstart ] && kind=node
  if [ "$kind" = php ]; then [[ $MIG_TARGET =~ ^[5-9]\.[0-9]$ ]] || arg_error "--target ${MIG_TARGET:-}"
  else [[ $MIG_TARGET =~ ^[0-9]{1,2}$ ]] || arg_error "--target ${MIG_TARGET:-}"; fi
  # Preconditions that need no change (C1/C2 order of FR-UPG-SEQ-001).
  (( IN_CONTAINER )) && fatal ERR-ENV-422-01 "Cannot identify how PHP is installed and assigned to sites on this server."
  case $bk in
    nginx_fastcgi|apache_proxy_fcgi|systemd_execstart) ;;
    apache_mod_php) fatal ERR-SCN-412-02 "Site {vhost} runs mod_php; switch it to PHP-FPM before changing the version." vhost="$site" ;;
    unmapped) fatal ERR-ENV-422-02 "Cannot determine which PHP site {site} uses." site="$site" ;;
    *) fatal ERR-ENV-422-01 "Cannot identify how PHP is installed and assigned to sites on this server." ;;
  esac
  if unacked_rollback_failed; then fatal ERR-UPG-423-01 "Site switching is locked until the rollback failure of {site} is resolved." site="$REPLY"; fi
  if [ -n "$MIG_PLAN" ]; then plan_gate
  elif (( ! MIG_NO_PLAN )) || [ -z "$MIG_REASON" ]; then
    fatal ERR-UPG-409-02 "An approved plan is required before switching {site}." site="$site"
  fi
  if (( MIG_NO_AUTO_RB )) && [ -z "$MIG_REASON" ]; then
    fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--no-auto-rollback needs --reason (BR-SCN-010)"
  fi
  busy_or_die
  resume_interrupted
  local from=${S_BRANCH[$site]} newbin
  [ "$from" = "$MIG_TARGET" ] && fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="--target $MIG_TARGET (the site already runs $from)"
  target_bin "$kind" "$MIG_TARGET"; newbin=$REPLY
  head_ "Switch $site: $from -> $MIG_TARGET (${pb}, $bk)$( ((DRY_RUN)) && echo ' (dry-run)')"
  if (( DRY_RUN )); then mig_switch_plan "$kind" "$newbin"; fi
  confirm "migrate switch $site"
  # --- C1: run, site lock, PREFLIGHT
  local t; t=$(now_ms)
  ensure_backup_dir
  SW=(); SW[run_id]=$RUN_ID; SW[site_id]=$site; SW[site_key]=${S_KEY[$site]}; SW[pb_id]=$pb; SW[binding_kind]=$bk
  SW[binding_ref]=${S_REFS[$site]}; SW[from_branch]=$from; SW[to_branch]=$MIG_TARGET; SW[old_bin]=${S_BIN[$site]}
  SW[new_bin]=$newbin; SW[old_ep]=${S_EP[$site]}; SW[plan_id]=$MIG_PLAN; SW[docroot]=${S_ROOT[$site]}; SW[owner]=${S_OWNER[$site]}
  SW[no_plan_reason]=$( ((MIG_NO_PLAN)) && echo "$MIG_REASON"); SW[job_id]=${QP_JOB_ID:-}; actor_of; SW[actor]=$REPLY
  SW[auto_rollback]=$( ((MIG_NO_AUTO_RB)) && echo 0 || echo 1); SW[rollback_available]=1; SW[t_start]=$(iso_now)
  SW[web]=""; web_of "$bk"; SW[web]=$REPLY
  [ "$kind" = node ] && { SW[node_kind]=systemd; SW[node_unit]=${S_UNIT[$site]}; }
  if ! lock_site "${SW[site_key]}"; then
    busy_or_die; fatal ERR-ENV-409-01 "Site {site} is in its post-switch check; wait {remaining} seconds." site="$site" remaining=600
  fi
  AUDIT_PLAN_ID=$MIG_PLAN
  audit_intent migrate_switch
  sw_status PREFLIGHT
  step C1 'done' "$t" "run ${SW[run_id]}, site lock ${SW[site_key]}.lock"
  # --- C2: target runtime
  t=$(now_ms)
  if [ -z "$newbin" ] || { [ "$kind" = php ] && ! svc_run "$newbin" -r 'exit(0);' >/dev/null 2>&1; } \
     || { [ "$kind" = node ] && ! svc_run "$newbin" -e 'process.exit(0)' >/dev/null 2>&1; }; then
    mig_error ERR-ENV-412-01 "{runtime} {target} is not installed on the server." runtime="$( [ $kind = php ] && echo PHP || echo Node.js)" target="$MIG_TARGET"
    step C2 failed "$t" "target ${newbin:-not found}" ERR-ENV-412-01; switch_abort ERR-ENV-412-01 "C2"
  fi
  if [ "$kind" = php ]; then fpm_bin_of "$MIG_TARGET"
    [ -x "$REPLY" ] || { mig_error ERR-ENV-412-01 "{runtime} {target} is not installed on the server." runtime="PHP-FPM" target="$MIG_TARGET"
                         step C2 failed "$t" "$REPLY missing" ERR-ENV-412-01; switch_abort ERR-ENV-412-01 "C2"; }
  fi
  step C2 'done' "$t" "target $newbin runs"
  # --- C3: manifest head + target pool
  t=$(now_ms)
  record switch "$site" "$from>$MIG_TARGET"
  if [ "$kind" = php ]; then
    SW_DROPPED=()
    if ! pb5_pool "$site" "$from" "$MIG_TARGET"; then step C3 failed "$t" "pool" ERR-ENV-500-01; switch_abort ERR-ENV-500-01 "pool"; fi
    local pdetail=$REPLY
    if ! pb5_pool_ready "$MIG_TARGET"; then
      mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$MIG_TARGET" site="$site"
      step C3 failed "$t" "$pdetail; $REPLY" ERR-ENV-500-01; switch_abort ERR-ENV-500-01 "$REPLY"
    fi
    step C3 'done' "$t" "$pdetail; $REPLY${SW_DROPPED[*]:+; dropped ${SW_DROPPED[*]}}"
  else
    step C3 skipped "$t" "Node.js app: no pool"
  fi
  sw_save
  # --- C4: FastCGI probe on the target pool (BR-HC-003)
  t=$(now_ms)
  if [ "$kind" = node ]; then step C4 skipped "$t" "Node.js: no FastCGI probe (hc_node_probe not declared)"
  elif [ ! -f "${S_ROOT[$site]}/index.php" ]; then step C4 skipped "$t" "no index.php in ${S_ROOT[$site]}"
  elif ! python_ok; then
    mig_warn ERR-HC-424-02 "Skipped the pre-switch trial run (Python 3 missing)."; step C4 skipped "$t" "Python 3 missing" ERR-HC-424-02
  else
    local pr; pr=$(qp_py fcgi probe --endpoint "${SW[new_ep]}" --docroot "${S_ROOT[$site]}" --host "${S_NAMES[$site]%% *}" \
                   --port 80 --version "$QP_VERSION" 2>/dev/null)
    SW[probe_detail]=$(sed -nE 's/.*"detail": "([^"]*)".*/\1/p' <<<"$pr")
    if [[ $pr == *'"ok": true'* ]]; then SW[probe_ok]=1; step C4 'done' "$t" "FastCGI probe ${SW[new_ep]}: ${SW[probe_detail]}"
    else
      SW[probe_ok]=0
      mig_error ERR-HC-424-01 "Code of {site} failed the trial run on PHP {target}: {detail}. The site was not changed." site="$site" target="$MIG_TARGET" detail="${SW[probe_detail]:-no answer}"
      step C4 failed "$t" "${SW[probe_detail]:-no answer}" ERR-HC-424-01; switch_abort ERR-HC-424-01 "probe"
    fi
  fi
  # --- C5: URL set, address, vhost check, log sources, baseline on $OLD
  t=$(now_ms)
  hc_load_params "$site" "${SW[site_key]}"
  if (( MIG_HC_SKIP )); then
    [ "${HC_MODE_DECLARED:-}" = skip ] || fatal_abort ERR-CLI-400-01 "--hc-skip needs hc_mode = skip in sites.d/${SW[site_key]}.conf"
    HC_MODE=skip
  fi
  SW[hc_mode]=$HC_MODE
  if ! hc_prepare "$site"; then step C5 failed "$t" "$REPLY" "$HC_ERR"; switch_abort "$HC_ERR" "C5"; fi
  local blog="$REPLY"
  if ! hc_baseline "$site" "${SW[run_id]}"; then
    mig_error ERR-HC-412-02 "Home page {url} of {site} returned different HTTP codes, a 5xx or an unexpected code in 5 samples before the switch (codes {codes}); switch aborted." url="${HC_URL[0]}" site="$site" codes="${HC_BAD_CODES:-}"
    step C5 failed "$t" "baseline of ${HC_URL[0]}: ${HC_BAD_CODES:-}" ERR-HC-412-02; switch_abort ERR-HC-412-02 "baseline"
  fi
  if [ -n "${HC_VHOST_FAIL:-}" ]; then
    mig_error ERR-HC-412-03 "Cannot determine the home page address of {site}." site="$site"
    step C5 failed "$t" "access log of the site did not show the probe" ERR-HC-412-03; switch_abort ERR-HC-412-03 "vhost"
  fi
  HC_W0=$(hc_w0 "$site"); [ "$kind" = node ] && node_baseline
  SW[vhost_check]=$HC_VHOST_CHECK; SW[host]=$HC_HOST; SW[port]=$HC_PORT; SW[scheme]=$HC_SCHEME; SW[addr]=$HC_ADDR
  hc_save_files "$BACKUP_DIR"; sw_save
  step C5 'done' "$t" "$blog; baseline ${#B_CODE[@]} URL(s), W0 $HC_W0"
  # --- C6: manifest of the binding layer (§5.4)
  t=$(now_ms)
  if [ "$kind" = php ]; then
    record reload "${SW[web]}"
    local f; while IFS= read -r f; do backup_file "$f"; done < <(pb5_files "$site")
  else
    record systemd "${SW[node_unit]}"
    record created "/etc/systemd/system/${SW[node_unit]}.d/zz-php-quickpatch-node.conf" binding
  fi
  printf 'MANIFEST_WRITTEN\n' >"$BACKUP_DIR/phase"
  trap '' HUP PIPE                                  # FR-JOB-LOG-001: the run reaches a conclusion
  trap 'MIG_TERM=1' TERM
  step C6 'done' "$t" "manifest $(wc -l <"$BACKUP_DIR/manifest") line(s)"
  # --- C7: change the binding
  t=$(now_ms)
  hc_log_mark "$site"
  if [ "$kind" = php ]; then pb5_apply "$site" "${SW[fpm_socket]}"; local d7="${SW[web]} binding -> ${SW[new_ep]}"
  else pb17_apply "$site" "$newbin" || { step C7 failed "$t" "$REPLY"; switch_abort ERR-ENV-500-02 "$REPLY" restore; }; local d7=$REPLY; fi
  step C7 'done' "$t" "$d7"
  # --- C8: syntax check of the web server
  t=$(now_ms)
  if [ "$kind" = php ]; then
    if ! web_test "${SW[web]}"; then
      log "${SW[web]} test: $REPLY"
      mig_error ERR-ENV-500-02 "The web server configuration is invalid after switching {site}; restored." site="$site"
      step C8 failed "$t" "${REPLY:0:200}" ERR-ENV-500-02; switch_abort ERR-ENV-500-02 "test" restore
    fi
    step C8 'done' "$t" "${SW[web]} configuration test ok"
  else
    if has systemd-analyze && ! systemd-analyze verify "${S_REFS[$site]}" >/dev/null 2>&1; then
      step C8 failed "$t" "systemd-analyze verify" ERR-ENV-500-02; switch_abort ERR-ENV-500-02 "verify" restore
    fi
    step C8 'done' "$t" "unit drop-in written"
  fi
  # --- C9: graceful reload (Node.js: daemon-reload + restart)
  t=$(now_ms)
  local rl_ok=1
  if [ "$kind" = php ]; then web_reload "${SW[web]}" >/dev/null 2>&1 || rl_ok=0
  else pb17_reload "${SW[node_unit]}" >/dev/null 2>&1 || rl_ok=0; fi
  if (( ! rl_ok )); then step C9 failed "$t" "reload failed"; switch_rollback "C9" "" ; fi
  SW[t_switched]=$(iso_now); SW[t_c9]=${SW[t_switched]}
  sw_status SWITCHED
  step C9 'done' "$t" "$( [ $kind = php ] && echo "graceful reload ${SW[web]}" || echo "restarted ${SW[node_unit]}")"
  # --- C10: the binding is in effect (HC-C0)
  t=$(now_ms)
  local vok=1
  if [ "$kind" = php ]; then pb5_verify || vok=0; else SW[verify_method]=5; pb17_verify "${SW[node_unit]}" "$newbin" || vok=0; fi
  SW[verify_ok]=$vok
  if (( ! vok )); then
    local vd=$REPLY; jo criterion=s:HC-C0 url=j:null detail=s:"$vd"; HC_VIOL=("$REPLY"); HC_VERDICT=FAIL
    step C10 failed "$t" "$vd"; switch_rollback HC-C0 ""
  fi
  step C10 'done' "$t" "HC-C0: $REPLY"
  sw_status HC_RUNNING
  # --- C11: release STATE_DIR/.lock, keep the site lock, watch the window
  t=$(now_ms)
  unlock_state
  hc_window "$site" "${SW[run_id]}"
  SW[t_hc_end]=$(iso_now); hc_save_files "$BACKUP_DIR"
  if [ "$HC_VERDICT" = TERM ]; then step C11 failed "$t" "stopped by SIGTERM"; switch_rollback MANUAL ""; fi
  if [ "$HC_VERDICT" = FAIL ]; then
    hc_criteria; local crit=$REPLY
    step C11 failed "$t" "health check: $crit"
    if (( MIG_NO_AUTO_RB )); then
      SW[hc_verdict]=FAIL; SW[violations]=${crit//,/;}; sw_status HC_FAILED_KEPT
      mig_error ERR-HC-500-01 "Site {site} failed the check ({criteria}) and is running PHP {target}." site="$site" criteria="$crit" target="$MIG_TARGET"
      switch_finish 1
    fi
    local why=${crit%%,*}; [[ ,$crit, == *,HC-C2,* ]] && why=HC-C2   # a 5xx also differs from the baseline code (HC-C1)
    switch_rollback "$why" "$crit"
  fi
  step C11 'done' "$t" "health check PASS (${HC_ROUNDS_DONE} round(s), $HC_MODE)"
  # --- C12
  t=$(now_ms)
  SW[hc_verdict]=PASS; sw_status PASSED
  step C12 'done' "$t" "PASSED"
  switch_finish 0
}

fatal_abort() { fatal "$1" "Invalid or missing value for {arg}." arg="$2"; }

# hc_prepare SITE: URL set, address and vhost check (C5 head). REPLY = detail, HC_ERR = code.
hc_prepare() {
  local site=$1
  HC_ERR=""
  if [ -n "${SW[node_kind]:-}" ]; then
    node_port "${SW[node_unit]}" || { HC_ERR=ERR-HC-412-03; mig_error ERR-HC-412-03 "Cannot determine the home page address of {site}." site="$site"; REPLY="no port"; return 1; }
    HC_HOST=127.0.0.1; HC_ADDR=127.0.0.1; HC_PORT=$REPLY; HC_SCHEME=http; HC_VHOST_CHECK=none
    S_NAMES[$site]=127.0.0.1
  else
    if ! hc_target "$site"; then
      HC_ERR=ERR-HC-412-03; mig_error ERR-HC-412-03 "Cannot determine the home page address of {site}." site="$site"
      REPLY="no host or listen address (listen: ${HC_LISTEN_SEEN:-none})"; return 1
    fi
    if ! hc_vhost_static "$site"; then
      HC_ERR=ERR-HC-412-03; mig_error ERR-HC-412-03 "Cannot determine the home page address of {site}." site="$site"
      REPLY="vhost_mismatch: $HC_ADDR:$HC_PORT $HC_HOST is not served by ${S_REFS[$site]}"; return 1
    fi
  fi
  hc_build_urls "$site" "${SW[site_key]:-${S_KEY[$site]}}"
  if [ "$HC_MODE" != skip ]; then
    local src n=0; while IFS= read -r src; do [[ $src == journal:* || -e $src || $src == "${SW[fpm_error_log]:-}" ]] && n=$((n + 1)); done < <(hc_log_sources "$site")
    if (( n == 0 )); then
      HC_ERR=ERR-HC-412-01; mig_error ERR-HC-412-01 "No PHP error log found for {site}; the post-switch check cannot run." site="$site"
      REPLY="no log source"; return 1
    fi
  fi
  REPLY="${#HC_URL[@]} URL(s) at $HC_ADDR:$HC_PORT ($HC_SCHEME), vhost check ${HC_VHOST_CHECK:-none}"
}

node_baseline() {
  local unit=${SW[node_unit]} pid i s=0
  NODE_NR0=$(systemctl show -p NRestarts --value "$unit" 2>/dev/null)
  pid=$(node_main_pid "$unit")
  for ((i = 0; i < 5; i++)); do s=$((s + $(awk '/^VmRSS:/ { print $2 }' "/proc/$pid/status" 2>/dev/null || echo 0))); done
  NODE_RSS0=$((s / 5))
}

# switch_abort CODE DETAIL [restore]: ABORTED branch (§5.1): restore files, purge the run's pool, release.
switch_abort() {
  local code=$1 t; t=$(now_ms)
  if [ "${3:-}" = restore ]; then
    local f; while IFS= read -r f; do rollback_files_for "$f"; done < <(pb5_files "$MIG_SITE")
    [ -n "${SW[node_kind]:-}" ] && rm -f "/etc/systemd/system/${SW[node_unit]}.d/zz-php-quickpatch-node.conf"
  fi
  if [ -n "$BACKUP_DIR" ] && grep -q $'^created\t' "$BACKUP_DIR/manifest" 2>/dev/null; then
    replay_run "$BACKUP_DIR" abort || mig_error ERR-ENV-500-03 "Revert of {site} not applied: the restored configuration is invalid." site="$MIG_SITE"
  fi
  SW[errors]="${SW[errors]:+${SW[errors]};}$code"
  [ -n "${SW[run_id]:-}" ] && sw_status ABORTED
  step ABORTED 'done' "$t" "switch aborted ($code); the site was not changed"
  switch_finish 2
}

# switch_rollback REASON CRITERIA: automatic rollback after C9 (R1-R7 with the held site lock).
switch_rollback() {
  local reason=$1 crit=${2:-$1} t
  SW[hc_verdict]=FAIL; [ -n "$crit" ] && SW[violations]=${crit//,/;}
  t=$(now_ms)
  if rollback_core "$reason"; then
    sw_status ROLLED_BACK "$reason"
    msg ERR-SCN-500-01 "Site {vhost} failed the post-switch check on {target}; reverted to {old}." vhost="${SW[site_id]}" target="${SW[to_branch]}" old="${SW[from_branch]}"
    printf '%s\n' "$REPLY ($crit)" >&2; add_error ERR-SCN-500-01 "$REPLY ($crit)" "site:${SW[site_id]}"
    step R7 'done' "$t" "ROLLED_BACK ($crit)"
    switch_finish 1
  fi
  sw_status ROLLBACK_FAILED "$reason"
  mig_error ERR-HC-500-02 "Could not revert {site} to PHP {old}: {detail}." site="${SW[site_id]}" old="${SW[from_branch]}" detail="$RB_DETAIL"
  step R7 failed "$t" "ROLLBACK_FAILED: $RB_DETAIL" ERR-HC-500-02
  switch_finish 2
}

# rollback_core REASON: R2, R4-R6 of the run in SW (site lock already held). RB_DETAIL on failure.
rollback_core() {
  local reason=$1 t dir="$STATE_DIR/backups/${SW[run_id]}" mode=site
  RB_DETAIL=""
  (( MIG_PURGE )) && mode=purge
  t=$(now_ms)
  if [ -n "${SW[old_bin]:-}" ] && [ ! -x "${SW[old_bin]}" ]; then
    msg ERR-ENV-410-01 "Cannot revert {site}: PHP {old} has been removed from the server." site="${SW[site_id]}" old="${SW[from_branch]}"
    add_error ERR-ENV-410-01 "$REPLY"; RB_DETAIL=$REPLY; step R2 failed "$t" "$REPLY" ERR-ENV-410-01; return 1
  fi
  step R2 'done' "$t" "${SW[old_bin]:-old runtime} present"
  t=$(now_ms)
  if ! replay_run "$dir" "$mode"; then
    RB_DETAIL=$REPLY
    mig_error ERR-ENV-500-03 "Revert of {site} not applied: the restored configuration is invalid." site="${SW[site_id]}"
    step R4 failed "$t" "$RB_DETAIL" ERR-ENV-500-03; return 1
  fi
  step R4 'done' "$t" "manifest replayed ($mode): $(printf '%s\n' "${J_MIG_MANIFEST[@]}" | grep -c '"status":"done"') step(s)"
  step R5 'done' "$t" "syntax check and graceful reload"
  t=$(now_ms)
  (( ${#HCP[@]} )) || hc_load_params "${SW[site_id]}" "${SW[site_key]}"
  if [ ${#HC_URL[@]} -eq 0 ] && [ -f "$dir/baseline.tsv" ]; then hc_restore "$dir"; fi
  if [ -n "${SW[node_kind]:-}" ]; then
    pb17_verify "${SW[node_unit]}" "${SW[old_bin]}" || { RB_DETAIL=$REPLY; step R6 failed "$t" "$REPLY"; return 1; }
  fi
  if [ ${#HC_URL[@]} -gt 0 ] && ! hc_after_rollback "${SW[run_id]}"; then
    RB_DETAIL="after rollback: $REPLY"; step R6 failed "$t" "$RB_DETAIL"; return 1
  fi
  SW[t_rollback_end]=$(iso_now)
  step R6 'done' "$t" "binding back on ${SW[from_branch]}, home page code = baseline"
  return 0
}

switch_finish() {
  local code=$1
  sw_save
  audit_result "$( [ "$MIG_SUB" = rollback ] && echo migrate_rollback || echo migrate_switch)" "$code"
  unlock_site
  jarr J_STEPS; local js=$REPLY; switch_json; local sw=$REPLY
  local hc=null; [ ${#HC_URL[@]} -gt 0 ] || [ -n "${HC_VERDICT:-}" ] && { hc_summary_json "backups/${SW[run_id]}/hc.json"; hc=$REPLY; }
  if [ "$MIG_SUB" = rollback ]; then jarr J_MIG_MANIFEST; jo switch=j:"$sw" steps=j:"$js" manifest=j:"$REPLY"
  else jo run_id=s:"${SW[run_id]}" switch=j:"$sw" steps=j:"$js" hc=j:"$hc"; fi
  local res=$REPLY
  say "  result: ${SW[status]} (run ${SW[run_id]})"
  finish "$code" "$res"
}

# mig_switch_plan KIND NEWBIN: dry-run of C1-C12 (no change).
mig_switch_plan() {
  local kind=$1 nb=$2 site=$MIG_SITE
  SW=(); SW[run_id]="(new)"; SW[site_id]=$site; SW[site_key]=${S_KEY[$site]}
  local t; t=$(now_ms)
  if [ -z "$nb" ]; then
    msg ERR-ENV-412-01 "{runtime} {target} is not installed on the server." runtime="$( [ $kind = php ] && echo PHP || echo Node.js)" target="$MIG_TARGET"
    add_warning ERR-ENV-412-01 "$REPLY"; step C2 failed "$t" "$REPLY" ERR-ENV-412-01
  else step C2 'done' "$t" "target $nb"; fi
  if [ "$kind" = php ]; then
    pb5_pool "$site" "${S_BRANCH[$site]}" "$MIG_TARGET" && step C3 'done' "$t" "$REPLY" || step C3 failed "$t" "pool" ERR-ENV-500-01
    local f l k; while IFS=$'\t' read -r f l k; do step C7 'done' "$t" "planned: $f:$l ($k) -> unix:/run/php/qp-${S_KEY[$site]}-$MIG_TARGET.sock"; done < <(pb5_plan "$site" x)
  else
    step C7 'done' "$t" "planned: drop-in /etc/systemd/system/${S_UNIT[$site]}.d/zz-php-quickpatch-node.conf, ExecStart with $nb"
  fi
  hc_load_params "$site" "${S_KEY[$site]}"
  if hc_prepare "$site"; then step C5 'done' "$t" "planned: $REPLY"; else step C5 failed "$t" "$REPLY" "$HC_ERR"; fi
  local u; for u in "${HC_URL[@]}"; do say "    probe URL: $u"; done
  if [ "$kind" = php ]; then
    change pool create "/etc/php/$MIG_TARGET/fpm/pool.d/qp-${S_KEY[$site]}.conf" "" "unix:/run/php/qp-${S_KEY[$site]}-$MIG_TARGET.sock"
    change site_binding switch "$site" "${S_EP[$site]}" "unix:/run/php/qp-${S_KEY[$site]}-$MIG_TARGET.sock" "${S_REFS[$site]}"
    web_of "${S_KIND[$site]}"; change service reload "$REPLY" "" "" "graceful reload"
  else
    change systemd create "/etc/systemd/system/${S_UNIT[$site]}.d/zz-php-quickpatch-node.conf" "" "$nb"
    change service restart "${S_UNIT[$site]}"
  fi
  affected site "$site" "$site"
  say "Dry-run: nothing was changed."
  jarr J_STEPS; local js=$REPLY ju res
  jas ${HC_URL[@]+"${HC_URL[@]}"}; ju=$REPLY
  jo run_id=j:null switch=j:null steps=j:"$js" hc=j:null hc_urls=j:"$ju"; res=$REPLY
  mig_preview; json_merge "$res" "$REPLY"
  finish 0 "$REPLY"
}

# --- rollback (FR-UPG-RBK-001, §5.2 R1-R7) -------------------------------------------------------------
mig_rollback() {
  # R1: the run
  local t run="$MIG_RUNARG" site=$MIG_SITE r s k st a
  t=$(now_ms)
  if [ -z "$run" ]; then
    while IFS=$'\t' read -r r s k st a; do
      [ "$s" = "$site" ] && [[ $st =~ ^(SWITCHED|HC_RUNNING|PASSED|HC_FAILED_KEPT)$ ]] && run=$r
    done < <(idx_runs)
  fi
  [ -n "$run" ] && sw_load "$run" || fatal ERR-PTCH-404-01 "No backup run found in {dir}" dir="$STATE_DIR/backups (switch of $site)"
  [ "${SW[site_id]}" = "$site" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="run $run is a switch of ${SW[site_id]}"
  idx_last "$run"; st=$(awk -F'\t' -v r="$run" '$2 == r && $11 !~ /^ack:/ { s = $6 } END { print s }' "$STATE_DIR/switches/index.tsv")
  [[ $st =~ ^(SWITCHED|HC_RUNNING|PASSED|HC_FAILED_KEPT)$ ]] || \
    fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="run $run is $st (nothing to roll back)"
  [ "${SW[rollback_available]:-1}" = 1 ] || fatal ERR-ENV-410-01 "Cannot revert {site}: PHP {old} has been removed from the server." site="$site" old="${SW[from_branch]}"
  SW[status]=$st
  head_ "Rollback $site (run $run, $st)$( ((DRY_RUN)) && echo ' (dry-run)')"
  if (( DRY_RUN )); then
    local action x y seq=0
    while IFS=$'\t' read -r action x y; do
      seq=$((seq + 1)); say "    [dry-run] $action $x${y:+ $y}"
      jas "$x" ${y:+"$y"}; jo seq=n:$seq action=s:"$action" args=j:"$REPLY" status=s:planned; J_MIG_MANIFEST+=("$REPLY")
    done < <(tac "$STATE_DIR/backups/$run/manifest")
    say "Dry-run: nothing was changed."
    switch_json; local sw=$REPLY; jarr J_MIG_MANIFEST; local jm=$REPLY
    jo switch=j:"$sw" steps=j:"[]" manifest=j:"$jm"; finish 0 "$REPLY"
  fi
  confirm "migrate rollback $site"
  step R1 'done' "$t" "run $run ($st)"
  # R3: locks (STATE_DIR/.lock taken by migrate_main), the site lock
  t=$(now_ms)
  BACKUP_DIR="$STATE_DIR/backups/$run"; RUN_ID=$run
  if ! lock_site "${SW[site_key]}"; then
    busy_or_die; fatal ERR-ENV-409-01 "Site {site} is in its post-switch check; wait {remaining} seconds." site="$site" remaining=600
  fi
  AUDIT_PLAN_ID=${SW[plan_id]:-}
  audit_intent migrate_rollback
  step R3 'done' "$t" "site lock ${SW[site_key]}.lock"
  mig_inventory
  if rollback_core MANUAL; then
    sw_status ROLLED_BACK MANUAL; step R7 'done' "$(now_ms)" "ROLLED_BACK (manual)"
    if [ -n "${SW[plan_id]:-}" ] && python_ok; then             # T-CHK-13: P5 items of the site back to FAILED
      qp_py plan-gate "${SW[plan_id]}" --site "$site" --rolled-back "$run" >/dev/null 2>&1 || \
        mig_warn "" "plan ${SW[plan_id]}: P5 items of $site could not be set to FAILED"
    fi
    switch_finish 0
  fi
  sw_status ROLLBACK_FAILED MANUAL
  mig_error ERR-HC-500-02 "Could not revert {site} to PHP {old}: {detail}." site="$site" old="${SW[from_branch]}" detail="$RB_DETAIL"
  switch_finish 2
}

# rollback_switch_run DIR: `rollback <run_id>` of a switch run = rollback-site with --purge-pool (T-SW-15).
rollback_switch_run() {
  local dir=$1
  MIG_SUB=rollback; MIG_PURGE=1
  sw_load "${dir##*/}" || return 1
  MIG_SITE=${SW[site_id]}; MIG_RUNARG=${SW[run_id]}
  mig_rollback
}

# --- interrupted window (§6.4 item 2) ---------------------------------------------------------------------
resume_interrupted() {
  local run site
  while IFS=$'\t' read -r run site; do
    [ -n "$run" ] || continue
    (( DRY_RUN )) && { warn "health check of $site was interrupted (run $run)"; continue; }
    say "  health check of $site (run $run) was interrupted: running it again"
    ( MIG_SUB=healthcheck; MIG_SITE=$site; MIG_BASE_ONLY=0; JSON=0; mig_resume_run "$run" ) 3>/dev/null
    idx_last "$run"; local st; st=$(cut -f6 <<<"$REPLY")
    case $st in
      PASSED|ROLLED_BACK) ;;
      HC_FAILED_KEPT) fatal ERR-HC-500-01 "Site {site} failed the check ({criteria}) and is running PHP {target}." site="$site" criteria="re-run" target="?" ;;
      *) fatal ERR-HC-500-02 "Could not revert {site} to PHP {old}: {detail}." site="$site" old="?" detail="$st" ;;
    esac
  done < <(interrupted_runs)
}

# mig_resume_run RUN: full window again with the saved baseline, then the decision of §6.4.
mig_resume_run() {
  sw_load "$1" || return 1
  lock_site "${SW[site_key]}" || return 1
  BACKUP_DIR="$STATE_DIR/backups/$1"; RUN_ID=$1
  mig_inventory
  hc_load_params "${SW[site_id]}" "${SW[site_key]}"; HC_MODE=${SW[hc_mode]:-full}
  hc_restore "$BACKUP_DIR" || return 1
  hc_log_mark "${SW[site_id]}"
  SW[t_c9]=$(iso_now); sw_save
  hc_window "${SW[site_id]}" "$1"
  SW[t_hc_end]=$(iso_now); hc_save_files "$BACKUP_DIR"
  if [ "$HC_VERDICT" = PASS ]; then SW[hc_verdict]=PASS; sw_status PASSED; unlock_site; return 0; fi
  hc_criteria; local crit=$REPLY
  if [ "${SW[auto_rollback]:-1}" = 0 ]; then SW[hc_verdict]=FAIL; sw_status HC_FAILED_KEPT; unlock_site; return 0; fi
  local why=${crit%%,*}; [[ ,$crit, == *,HC-C2,* ]] && why=HC-C2
  if rollback_core "$why"; then sw_status ROLLED_BACK "$why"; else sw_status ROLLBACK_FAILED "$why"; fi
  unlock_site
}

# --- healthcheck (FR-UPG-HC-001/003/006) ------------------------------------------------------------------
mig_healthcheck() {
  mig_inventory
  local site=$MIG_SITE
  if (( MIG_BASE_ONLY )); then
    site_known "$site" || fatal ERR-ENV-422-02 "Cannot determine which PHP site {site} uses." site="$site"
    SW=(); SW[site_key]=${S_KEY[$site]}; [ "${S_KIND[$site]}" = systemd_execstart ] && { SW[node_kind]=systemd; SW[node_unit]=${S_UNIT[$site]}; }
    head_ "Health check baseline of $site (read only)"
    hc_load_params "$site" "${S_KEY[$site]}"
    hc_prepare "$site" || finish 2
    say "  $REPLY"
    local okb=1; hc_baseline "$site" "base-$(date +%s)" || okb=0
    HC_W0=$(hc_w0 "$site")
    warn_interrupted
    jas "${HC_URL[@]}"; local ju=$REPLY; hc_baseline_json; local jb=$REPLY
    (( okb )) || mig_warn ERR-HC-412-02 "Home page {url} of {site} returned different HTTP codes, a 5xx or an unexpected code in 5 samples before the switch (codes {codes}); switch aborted." url="${HC_URL[0]}" site="$site" codes="${HC_BAD_CODES:-}"
    jo site_id=s:"$site" baseline_only=b:1 hc_urls=j:"$ju" baseline=j:"$jb" hc=j:null
    finish $(( okb ? 0 : 1 )) "$REPLY"
  fi
  # write variant: re-run the window of the site's interrupted run (§6.4 item 2)
  local run="" r s k st a
  while IFS=$'\t' read -r r s k st a; do [ "$s" = "$site" ] && [ "$st" = HC_RUNNING ] && run=$r; done < <(idx_runs)
  [ -n "$run" ] || fatal ERR-CLI-400-01 "Invalid or missing value for {arg}." arg="$site has no switch run waiting for its health check"
  confirm "migrate healthcheck $site"
  AUDIT_PLAN_ID=""; audit_intent migrate_healthcheck
  mig_resume_run "$run" || fatal ERR-ENV-409-01 "Site {site} is in its post-switch check; wait {remaining} seconds." site="$site" remaining=600
  audit_result migrate_healthcheck 0
  jas "${HC_URL[@]}"; local ju=$REPLY; hc_baseline_json; local jb=$REPLY; hc_summary_json "backups/$run/hc.json"; local jh=$REPLY
  jo site_id=s:"$site" baseline_only=b:0 hc_urls=j:"$ju" baseline=j:"$jb" hc=j:"$jh"
  finish "$( [ "${SW[status]}" = PASSED ] && echo 0 || echo 1)" "$REPLY"
}
