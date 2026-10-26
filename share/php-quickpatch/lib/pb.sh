# shellcheck shell=bash disable=SC2034,SC2154  # globals shared with php-quickpatch.sh and the other lib/*.sh
# Playbook steps of migrate (DOC-SRS-QP-ENV-003 §2, §6, §7; -container-node §4, §6): services,
# target FPM pool (PB-005), binding change (Nginx/Apache), Node.js systemd drop-in (PB-017),
# and the replay of a switch manifest (§5.2 R4/R5). Sourced by php-quickpatch.sh for migrate.

# --- services (BR-ENV-006: graceful reload of the smallest scope) ------------------------------
# Every command started here closes the lock descriptors so a daemon never inherits them.
svc_run() { "$@" 9>&- 7>&- 3>&-; }
svc_reload() { if (( HAS_SYSTEMD )); then svc_run systemctl reload "$1"; else svc_run service "$1" reload; fi; }
svc_restart() { if (( HAS_SYSTEMD )); then svc_run systemctl restart "$1"; else svc_run service "$1" restart; fi; }
svc_start() { if (( HAS_SYSTEMD )); then svc_run systemctl start "$1"; else svc_run service "$1" start; fi; }
svc_active() {
  if (( HAS_SYSTEMD )); then systemctl is-active -q "$1" 2>/dev/null; return; fi
  svc_run service "$1" status >/dev/null 2>&1
}

web_of() { case $1 in nginx_fastcgi) REPLY=nginx ;; apache_proxy_fcgi|apache_mod_php) REPLY=apache ;; *) REPLY="" ;; esac; }
apache_unit() { if [ -d /etc/apache2 ]; then REPLY=apache2; else REPLY=httpd; fi; }
web_test() { # web_test nginx|apache: REPLY = output
  case $1 in
    nginx) REPLY=$(svc_run nginx -t 2>&1) ;;
    apache) REPLY=$(svc_run "${APACHE_CTL:-apachectl}" configtest 2>&1) ;;
    *) REPLY=""; return 0 ;;
  esac
}
web_reload() {
  case $1 in
    nginx) if (( HAS_SYSTEMD )); then svc_run systemctl reload nginx; else svc_run nginx -s reload; fi ;;
    apache) svc_run "${APACHE_CTL:-apachectl}" -k graceful ;;
  esac
}

# Debian layout (PB-001); other providers stop with ERR-ENV-500-01 (MANUAL in this build).
fpm_unit_of() { REPLY="php$1-fpm"; }
fpm_bin_of() { REPLY="/usr/sbin/php-fpm$1"; }
fpm_pool_dir() { REPLY="/etc/php/$1/fpm/pool.d"; }
fpm_test() { local b; fpm_bin_of "$1"; b=$REPLY; REPLY=$(svc_run "$b" -t 2>&1); }

# ini directives removed in (OLD, NEW] (BR-SCN-046) from the catalog.
removed_directives() { # removed_directives OLD NEW
  local f="$CATALOG_DIR/bc_rules.json" d r
  [ -f "$f" ] || return 0
  tr -d '\n' <"$f" | grep -oE '"directive": *"[^"]*", *"removed_in": *"[^"]*"' | sed -E 's/"directive": *"([^"]*)", *"removed_in": *"([^"]*)"/\1 \2/' |
  while read -r d r; do ver_lt "$1" "$r" && ! ver_lt "$2" "$r" && echo "$d"; done
}

# --- PB-005: target pool (FR-UPG-CFG-001, BR-ENV-007, §6.3) ------------------------------------------
# pool_section FILE: lines of the pool section that serves the site's endpoint.
pool_section() {
  local file=$1 ep=${2#unix:}
  awk -v ep="$ep" '
    /^[ \t]*\[/ { if (keep) exit; buf = ""; sec = $0; next }
    { buf = buf $0 "\n"; k = $0; sub(/=.*/, "", k); gsub(/[ \t]/, "", k); v = $0; sub(/^[^=]*=[ \t]*/, "", v); sub(/[ \t;]+$/, "", v)
      if (k == "listen" && (v == ep || ep ~ (":" v "$"))) keep = 1 }
    END { if (keep) printf "%s", buf }' "$file"
}

# pb5_pool SITE OLD NEW: write the pool file (dry-run: only REPLY = plan). Sets SW[fpm_*].
pb5_pool() {
  local site=$1 old=$2 new=$3 key=${S_KEY[$1]} dir sock file log unit sec line k v
  fpm_pool_dir "$new"; dir=$REPLY
  sock="/run/php/qp-$key-$new.sock"
  if (( ${#sock} > 107 )); then
    mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$new" site="$site"
    log "socket_path_too_long ${#sock} > 107: $sock"; return 1
  fi
  file="$dir/qp-$key.conf"; log="/var/log/php-quickpatch/$key-$new.error.log"; fpm_unit_of "$new"; unit=$REPLY
  SW[fpm_pool]="qp-$key"; SW[fpm_socket]=$sock; SW[fpm_error_log]=$log; SW[fpm_unit]=$unit; SW[new_ep]="unix:$sock"
  if [ ! -d "$dir" ]; then
    mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$new" site="$site"
    log "pool directory $dir missing (provider layout not supported in this build)"; return 1
  fi
  if [ -f "$file" ]; then
    if [ "$(head -n1 "$file")" != "; qp-site-id = $site" ]; then
      mig_error ERR-ENV-500-01 "Cannot create the PHP {target} pool for {site}." target="$new" site="$site"
      log "pool_name_collision $file"; return 1
    fi
    REPLY="reuse $file"; SW[pool_reused]=1; return 0
  fi
  (( DRY_RUN )) && { REPLY="create $file (listen $sock)"; return 0; }
  sec=""; [ -n "${S_POOLFILE[$site]:-}" ] && sec=$(pool_section "${S_POOLFILE[$site]}" "${S_EP[$site]}")
  local drop; drop=" $(removed_directives "$old" "$new" | tr '\n' ' ') "
  local user group webu webg; user=$(awk -F'=' '/^[ \t]*user[ \t]*=/ { gsub(/[ \t;]/, "", $2); print $2; exit }' <<<"$sec")
  group=$(awk -F'=' '/^[ \t]*group[ \t]*=/ { gsub(/[ \t;]/, "", $2); print $2; exit }' <<<"$sec")
  user=${user:-${S_OWNER[$site]:-www-data}}; group=${group:-$user}
  webu=www-data; webg=www-data; id nginx >/dev/null 2>&1 && ! id www-data >/dev/null 2>&1 && { webu=nginx; webg=nginx; }
  # RAM (§6.7 risk 1): pm.max_children × RSS of an old worker + 256 MB must fit in MemAvailable.
  local maxc rss avail ondemand=""
  maxc=$(awk -F'=' '/^[ \t]*pm.max_children[ \t]*=/ { gsub(/[ \t;]/, "", $2); print $2; exit }' <<<"$sec")
  rss=$(ps -o rss= -C "php-fpm$old" 2>/dev/null | awk '{ s += $1; n++ } END { if (n) printf "%d", s / n / 1024 }')
  avail=$(awk '/^MemAvailable:/ { printf "%d", $2 / 1024 }' /proc/meminfo 2>/dev/null)
  if [ -n "$maxc" ] && [ -n "$rss" ] && [ -n "$avail" ] && (( rss > 0 )) && (( maxc * rss + 256 > avail )); then
    ondemand=$(( (avail - 256) / rss )); (( ondemand < 2 )) && ondemand=2
    mig_warn "" "RAM: pool qp-$key uses pm = ondemand, pm.max_children = $ondemand (MemAvailable $avail MB)"
  fi
  record reload "fpm:$unit" purge-only
  record created "$file"
  mkdir -p /var/log/php-quickpatch && chmod 0755 /var/log/php-quickpatch
  : >>"$log"; chown "$user" "$log" 2>/dev/null
  {
    printf '; qp-site-id = %s\n; created by php-quickpatch for the switch %s of %s (%s -> %s)\n[qp-%s]\n' "$site" "${SW[run_id]}" "$site" "$old" "$new" "$key"
    printf 'user = %s\ngroup = %s\nlisten = %s\nlisten.owner = %s\nlisten.group = %s\nlisten.mode = 0660\n' "$user" "$group" "$sock" "$webu" "$webg"
    if [ -n "$ondemand" ]; then printf 'pm = ondemand\npm.max_children = %s\n' "$ondemand"; fi
    while IFS= read -r line; do
      k=${line%%=*}; k=${k//[[:space:]]/}
      case $k in ''|';'*|'#'*|user|group|listen|listen.*|pm.status_path|catch_workers_output|'php_admin_value[error_log]'|'php_admin_flag[log_errors]') continue ;; esac
      [ -n "$ondemand" ] && [[ $k == pm || $k == pm.max_children ]] && continue
      if [[ $k =~ ^php_(admin_)?(value|flag)\[(.+)\]$ ]]; then
        v=${BASH_REMATCH[3]}
        [[ $drop == *" $v "* ]] && { SW_DROPPED+=("$v"); continue; }
      fi
      printf '%s\n' "$line"
    done <<<"$sec"
    [ -n "$sec" ] || printf 'pm = dynamic\npm.max_children = 5\npm.start_servers = 2\npm.min_spare_servers = 1\npm.max_spare_servers = 3\n'
    printf 'pm.status_path = /qp-fpm-status\ncatch_workers_output = yes\nphp_admin_value[error_log] = %s\nphp_admin_flag[log_errors] = on\n' "$log"
  } >"$file"
  chmod 0644 "$file"
  REPLY="created $file (listen $sock)"
}

# pb5_pool_ready NEW: php-fpm -t, reload (start when stopped), socket present ≤ 15 s.
pb5_pool_ready() {
  local new=$1 unit=${SW[fpm_unit]} i
  fpm_test "$new" || { log "php-fpm$new -t: $REPLY"; REPLY="php-fpm$new -t failed: ${REPLY:0:200}"; return 1; }
  if svc_active "$unit"; then svc_reload "$unit" >/dev/null 2>&1 || { REPLY="reload $unit failed"; return 1; }
  else svc_start "$unit" >/dev/null 2>&1 || { REPLY="start $unit failed"; return 1; }; fi
  for ((i = 0; i < 15; i++)); do [ -S "${SW[fpm_socket]}" ] && { REPLY="$unit reloaded, ${SW[fpm_socket]} ready"; return 0; }; sleep 1; done
  REPLY="${SW[fpm_socket]} did not appear within 15 s"; return 1
}

# --- PB-005: binding change (§6.4) ----------------------------------------------------------------
# pb5_files SITE: files of the binding (unique, real paths) on stdout.
pb5_files() {
  local r f
  for r in ${S_REFS[$1]//,/ }; do f=${r%:*}; [ -f "$f" ] && readlink -f "$f"; done | awk '!s[$0]++'
}

# pb5_plan SITE NEWSOCK: edits as "file<TAB>line<TAB>kind" (direct|include|vhost|sethandler) on stdout.
pb5_plan() {
  local site=$1 r f l text incfiles=" "
  for r in ${S_REFS[$site]//,/ }; do
    f=${r%:*}; l=${r##*:}; [ -f "$f" ] || continue
    text=$(sed -n "${l}p" "$f")
    case ${S_KIND[$site]} in
      nginx_fastcgi)
        if [[ $text =~ ^[[:space:]]*include[[:space:]] ]]; then printf '%s\t%s\tinclude\n' "$f" "$l"; incfiles+="$(sed -E 's/^[[:space:]]*include[[:space:]]+([^;]+);.*/\1/' <<<"$text") "
        fi ;;
    esac
  done
  for r in ${S_REFS[$site]//,/ }; do
    f=${r%:*}; l=${r##*:}; [ -f "$f" ] || continue
    text=$(sed -n "${l}p" "$f")
    case ${S_KIND[$site]} in
      nginx_fastcgi)
        if [[ $text =~ fastcgi_pass ]]; then
          local shared=0 inc; for inc in $incfiles; do [[ $inc == /* ]] || inc="/etc/nginx/$inc"
            # shellcheck disable=SC2053
            [[ $f == $inc ]] && shared=1; done
          (( shared )) || printf '%s\t%s\tdirect\n' "$f" "$l"
        fi ;;
      apache_proxy_fcgi)
        if [[ ${text,,} =~ \<virtualhost ]]; then
          local h; h=$(awk -v s="$l" 'NR >= s { if (tolower($0) ~ /sethandler +"?proxy:unix:/) { print NR; exit } if (tolower($0) ~ /<\/virtualhost>/) exit }' "$f")
          if [ -n "$h" ]; then printf '%s\t%s\tsethandler\n' "$f" "$h"; else printf '%s\t%s\tvhost\n' "$f" "$l"; fi
        fi ;;
    esac
  done | awk '!s[$0]++'
}

# pb5_apply SITE NEWSOCK: change the binding (C7). Files were backed up at C6.
pb5_apply() {
  local site=$1 sock=$2 key=${S_KEY[$1]} f l kind snip
  while IFS=$'\t' read -r f l kind; do
    case $kind in
      direct) sed -i -E "${l}s#(fastcgi_pass[[:space:]]+)[^;]+;#\\1unix:${sock};#" "$f" ;;
      include)
        local inc; inc=$(sed -n "${l}p" "$f" | sed -E 's/^[[:space:]]*include[[:space:]]+([^;]+);.*/\1/'); [[ $inc == /* ]] || inc="/etc/nginx/$inc"
        snip="/etc/nginx/snippets/qp-$key-php.conf"
        if [ ! -f "$snip" ]; then
          record created "$snip"
          mkdir -p /etc/nginx/snippets
          sed -E "s#(fastcgi_pass[[:space:]]+)[^;]+;#\\1unix:${sock};#" "$inc" >"$snip"
        else
          sed -i -E "s#(fastcgi_pass[[:space:]]+)[^;]+;#\\1unix:${sock};#" "$snip"
        fi
        sed -i -E "${l}s#include[[:space:]]+[^;]+;#include ${snip};#" "$f" ;;
      sethandler) sed -i -E "${l}s#proxy:unix:[^|\"]+#proxy:unix:${sock}#" "$f" ;;
      vhost)
        sed -i "${l}a\\
    <FilesMatch \".+\\\\.ph(?:ar|p|tml)\$\">\\
        SetHandler \"proxy:unix:${sock}|fcgi://localhost\"\\
    </FilesMatch>" "$f" ;;
    esac
  done < <(pb5_plan "$site" "$sock")
}

# pb5_verify (C10, §3.4 method 1): accepted conn of the target pool grows after 1 home request.
pb5_verify() {
  local a b
  if ! python_ok; then
    hc_get 0 "${SW[run_id]}-c0"
    pgrep -f "php-fpm: pool ${SW[fpm_pool]}" >/dev/null 2>&1 && { REPLY="method 2: worker of pool ${SW[fpm_pool]} running"; SW[verify_method]=2; return 0; }
    REPLY="no worker of pool ${SW[fpm_pool]}"; return 1
  fi
  SW[verify_method]=1
  a=$(qp_py fcgi status --endpoint "${SW[new_ep]}" --timeout 5 2>/dev/null | sed -nE 's/.*"accepted_conn": ([0-9]+).*/\1/p')
  local i; for ((i = 1; i <= 10; i++)); do
    hc_get 0 "${SW[run_id]}-c0$i"                     # a graceful reload takes effect shortly after the signal
    b=$(qp_py fcgi status --endpoint "${SW[new_ep]}" --timeout 5 2>/dev/null | sed -nE 's/.*"accepted_conn": ([0-9]+).*/\1/p')
    # every status request counts itself: the i-th one sees a + i when no home request reached the pool
    [ -n "$a" ] && [ -n "$b" ] && (( b > a + i )) && { REPLY="accepted conn $a -> $b"; return 0; }
    sleep 1
  done
  REPLY="accepted conn ${a:-?} -> ${b:-?} (home request did not reach pool ${SW[fpm_pool]})"; return 1
}

# --- PB-017: Node.js app of a systemd unit (container-node §6.2) ---------------------------------------
node_unit_file() { REPLY=${S_REFS[$1]}; }
node_main_pid() { systemctl show -p MainPID --value "$1" 2>/dev/null; }

pb17_apply() { # pb17_apply SITE NEW_BIN: drop-in with an empty ExecStart= and the new one
  local site=$1 nb=$2 unit=${S_UNIT[$1]} uf=${S_REFS[$1]} exec dir drop ob=${S_BIN[$1]}
  exec=$(sed -n 's/^ExecStart=//p' "$uf" | tail -n1)
  [ -n "$exec" ] || { REPLY="no ExecStart in $uf"; return 1; }
  dir="/etc/systemd/system/$unit.d"; drop="$dir/zz-php-quickpatch-node.conf"
  SW[node_unit]=$unit; SW[node_dropin]=$drop
  local newexec=${exec//$ob/$nb}
  [ "$newexec" != "$exec" ] || newexec="$nb ${exec#* }"
  mkdir -p "$dir"
  printf '# created by php-quickpatch (switch %s of %s)\n[Service]\nExecStart=\nExecStart=%s\n' "${SW[run_id]}" "$site" "$newexec" >"$drop"
  chmod 0644 "$drop"
  REPLY="$drop: ExecStart=$newexec"
}

pb17_reload() { svc_run systemctl daemon-reload && svc_run systemctl restart "$1"; }

pb17_verify() { # HC-C0 method 5: /proc/<MainPID>/exe = $NEW_BIN
  local i pid exe
  for ((i = 0; i < 10; i++)); do
    pid=$(node_main_pid "$1"); exe=$(readlink -f "/proc/$pid/exe" 2>/dev/null)
    [ -n "$pid" ] && [ "$pid" != 0 ] && [ "$exe" = "$(readlink -f "$2")" ] && { REPLY="MainPID $pid runs $exe"; return 0; }
    sleep 1
  done
  REPLY="MainPID ${pid:-?} runs ${exe:-?}, not $2"; return 1
}

node_hc_ok() { # HC-C9 Node.js: NRestarts unchanged, RSS ≤ factor × baseline
  local unit=${SW[node_unit]} nr pid rss
  nr=$(systemctl show -p NRestarts --value "$unit" 2>/dev/null)
  [ -n "${NODE_NR0:-}" ] && [ -n "$nr" ] && (( nr > NODE_NR0 )) && return 1
  pid=$(node_main_pid "$unit"); rss=$(awk '/^VmRSS:/ { print $2 }' "/proc/$pid/status" 2>/dev/null)
  if [ -n "${NODE_RSS0:-}" ] && [ -n "$rss" ]; then
    awk -v r="$rss" -v b="$NODE_RSS0" -v f="${HCP[node_rss_factor]}" 'BEGIN { exit !(r <= f * b) }' || return 1
  fi
  svc_active "$unit"
}

# node_port UNIT: port of the app (PORT in the unit environment, else the listening socket of MainPID).
node_port() {
  local unit=$1 p pid
  p=$(systemctl show -p Environment --value "$unit" 2>/dev/null | tr ' ' '\n' | sed -n 's/^PORT=//p' | head -n1)
  [ -n "$p" ] || p=$(sed -n 's/^Environment=.*PORT=\([0-9]*\).*/\1/p' "${S_REFS[$MIG_SITE]:-/dev/null}" | head -n1)
  if [ -z "$p" ] && has ss; then
    pid=$(node_main_pid "$unit")
    p=$(ss -ltnpH 2>/dev/null | awk -v pid="pid=$pid," 'index($0, pid) { n = split($4, a, ":"); print a[n]; exit }')
  fi
  REPLY=$p; [ -n "$p" ]
}

# --- manifest replay (R4/R5, ABORTED branch) ---------------------------------------------------------
# replay_run DIR MODE: MODE = site (rollback-site), purge (rollback-site --purge-pool, rollback ID),
# abort (only created/purge-only lines). REPLY = failure detail; J_MIG_MANIFEST = replayed lines.
replay_run() {
  local dir=$1 mode=$2 action a b st detail="" purged=" " seq=0
  J_MIG_MANIFEST=()
  while IFS=$'\t' read -r action a b; do
    [ -n "$action" ] || continue
    seq=$((seq + 1)); st="done"
    case $action in
      switch) st=skipped ;;
      copy) if [ "$mode" = abort ]; then st=skipped; else cp -a "$b" "$a" && note "restored $a" || { st=failed; detail+="restore $a; "; }; fi ;;
      created)
        if [ "$b" = binding ] && [ "$mode" != abort ]; then rm -f "$a" && note "removed $a" || st=failed
        elif [ "$mode" = purge ] || [ "$mode" = abort ]; then rm -f "$a" && { note "removed $a"; purged+="$a "; } || st=failed
        else st=skipped; fi ;;
      reload)
        if [ "$b" = purge-only ]; then
          if [[ $purged == " " ]]; then st=skipped
          else replay_reload "$a" || { st=failed; detail+="$REPLY; "; }; fi
        elif [ "$mode" = abort ]; then st=skipped
        else replay_reload "$a" || { st=failed; detail+="$REPLY; "; break_after=1; }; fi ;;
      link) if [ "$mode" = abort ]; then st=skipped; else ln -sfn "$b" "$a" && note "link $a -> $b" || st=failed; fi ;;
      systemd) if [ "$mode" = abort ]; then st=skipped; else pb17_reload "$a" && note "restarted $a" || { st=failed; detail+="restart $a; "; }; fi ;;
      note) warn "$a"; st=skipped ;;
      *) st=skipped ;;
    esac
    local args=("$a"); [ -n "$b" ] && args+=("$b")
    jas "${args[@]}"; jo seq=n:$seq action=s:"$action" args=j:"$REPLY" status=s:"$st"; J_MIG_MANIFEST+=("$REPLY")
    [ -n "${break_after:-}" ] && break
  done < <(tac "$dir/manifest")
  unset break_after
  REPLY=$detail; [ -z "$detail" ]
}

replay_reload() { # replay_reload KEY: syntax check, then graceful reload (ERR-ENV-500-03 when the check fails)
  local key=$1
  case $key in
    nginx|apache) web_test "$key" || { log "$key test after restore: $REPLY"; REPLY="$key configuration test failed after restore"; return 1; }
                  web_reload "$key" >/dev/null 2>&1 || { REPLY="$key reload failed"; return 1; } ;;
    fpm:*) local unit=${key#fpm:} br; br=${unit#php}; br=${br%-fpm}
           fpm_test "$br" || { REPLY="php-fpm$br -t failed after removing the pool"; return 1; }
           svc_active "$unit" && { svc_reload "$unit" >/dev/null 2>&1 || { REPLY="reload $unit failed"; return 1; }; } ;;
  esac
  return 0
}
