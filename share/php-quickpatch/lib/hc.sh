# shellcheck shell=bash disable=SC2034,SC2154  # globals shared with php-quickpatch.sh and the other lib/*.sh
# Health check of a switched site (DOC-SRS-QP-ENV-002, FR-UPG-HC-001..006, BR-HC-001..012).
# Sourced by php-quickpatch.sh for migrate. All probes are GET requests to the address the
# site's front-end vhost listens on (curl --resolve), one at a time (BR-HC-012).

# Parameters (§2): name default min max
HC_PARAMS="window_s 600 300 3600
interval_s 60 15 300
timeout_s 10 3 60
connect_timeout_s 3 1 10
max_user_urls 10 0 10
baseline_rounds 5 3 10
baseline_interval_s 10 5 60
size_dev_pct 15 5 50
size_dev_cap_pct 40 15 80
small_body_bytes 512 128 4096
small_body_abs_bytes 256 64 2048
p95_factor 1.5 1.1 3.0
p95_add_ms 1000 200 5000
p95_floor_ms 100 0 1000
warn_min 20 0 1000
warn_factor 1.2 1.0 5.0
timeout_retry 1 0 2
skip_window_s 120 60 600
node_rss_factor 1.5 1.1 4.0"
declare -gA HCP=()
HC_CACHEBUST=on
HC_URL=(); HC_EXPECT=(); HC_SIZEIGN=(); HC_CB=(); HC_INSECURE=(); HC_ALIVE=()
HC_HOST=""; HC_PORT=""; HC_SCHEME=""; HC_ADDR=""; HC_MODE=full; HC_VHOST_CHECK=""; HC_LISTEN_SEEN=""
declare -gA B_CODE=() B_LOC=() B_M=() B_SPREAD=() B_P95=() B_FORBID=() B_SIZES=()
declare -gA LOG_OFF=() LOG_INO=()
HC_W0=0; HC_VIOL=(); HC_ROUNDS=(); HC_LOGLINES=(); HC_TIMEOUTS=0
HC_FORBID_PHP='<?php|Fatal error|Parse error'
HC_FORBID_NODE='Fatal error|Error: Cannot find module'
RE_FATAL='PHP (Fatal error|Parse error|Compile error|Core error|Recoverable fatal error)|Fatal error: Uncaught'
RE_CRASH='child [0-9]+ exited on signal (6|7|11)'
RE_WARN='PHP Warning'
RE_NODE_ERR='uncaughtException|UnhandledPromiseRejection|ERR_OSSL_EVP_UNSUPPORTED'

# --- parameters (§2) ----------------------------------------------------------------------------
hc_conf_files() { # global file then the site's sites.d file
  if (( IS_ROOT )); then echo /etc/php-quickpatch/healthcheck.conf; else echo "${HOME:-/nonexistent}/.config/php-quickpatch/healthcheck.conf"; fi
}

hc_load_params() { # hc_load_params SITE KEY
  local name def min max line k v f
  while read -r name def min max; do HCP[$name]=$def; done <<<"$HC_PARAMS"
  HC_CACHEBUST=on; HC_MODE=full
  for f in $(hc_conf_files); do
    [ -f "$f" ] || continue
    while IFS= read -r line; do hc_param_line "$line"; done <"$f"
  done
  while IFS= read -r line; do hc_param_line "$line"; done < <(site_conf_lines "$1" "$2")
}

hc_param_line() {
  local line=$1 k v name def min max
  [[ $line =~ ^[[:space:]]*(hc\.)?([a-z_0-9]+)[[:space:]]*=[[:space:]]*([^[:space:]#]+) ]] || return 0
  k=${BASH_REMATCH[2]}; v=${BASH_REMATCH[3]}
  case $k in
    cachebust) [[ $v == on || $v == off ]] && HC_CACHEBUST=$v; return 0 ;;
    hc_mode) [[ $v == skip ]] && HC_MODE_DECLARED=skip; return 0 ;;
  esac
  while read -r name def min max; do
    [ "$name" = "$k" ] || continue
    if [[ $v =~ ^[0-9]+(\.[0-9]+)?$ ]] && awk -v v="$v" -v a="$min" -v b="$max" 'BEGIN { exit !(v + 0 >= a + 0 && v + 0 <= b + 0) }'; then
      HCP[$k]=$v
    else
      mig_warn ERR-HC-422-01 "Value {key}={value} is invalid; using default {default}." key="hc.$k" value="$v" default="$def"
    fi
  done <<<"$HC_PARAMS"
}

# --- addresses (§3.1, §3.1.1) ---------------------------------------------------------------------
local_addrs() { # IPv4/IPv6 addresses assigned on the interfaces
  if has ip; then ip -o addr show 2>/dev/null | awk '{ a = $4; sub(/\/.*/, "", a); print a }'; return; fi
  awk '/^ +\|-- / { a = $2 } /\/32 host LOCAL/ { print a }' /proc/net/fib_trie 2>/dev/null | sort -u
  awk '{ s = $1; o = ""; for (i = 1; i <= 32; i += 4) o = o (i > 1 ? ":" : "") substr(s, i, 4); print o }' /proc/net/if_inet6 2>/dev/null
}

addr_assigned() {
  local a=$1 x
  [[ $a == 127.* || $a == ::1 ]] && return 0
  for x in $(local_addrs); do [ "$x" = "$a" ] && return 0; done
  return 1
}

# hc_target SITE: HC_HOST, HC_SCHEME, HC_PORT, HC_ADDR from server_names and listen (rules 1, 2, 4a-4c).
hc_target() {
  local site=$1 n lv addr port ssl https_port="" http_port="" cands=() wild4="" wild6="" v4="" v6=""
  HC_HOST=""
  for n in ${S_NAMES[$site]:-}; do
    [[ $n == _ || $n == localhost || $n == default || $n == *'*'* || $n =~ ^[0-9.]+$ || $n == *:* || $n == '~'* ]] && continue
    HC_HOST=$n; break
  done
  [ -n "$HC_HOST" ] || return 1
  for lv in ${S_LISTEN[$site]:-}; do
    ssl=0; [[ $lv == */ssl* ]] && ssl=1; lv=${lv%%/*}
    if [[ $lv =~ ^\[(.*)\]:([0-9]+)$ ]]; then addr=${BASH_REMATCH[1]}; port=${BASH_REMATCH[2]}
    elif [[ $lv =~ ^([^:]+):([0-9]+)$ ]]; then addr=${BASH_REMATCH[1]}; port=${BASH_REMATCH[2]}
    elif [[ $lv =~ ^[0-9]+$ ]]; then addr='*'; port=$lv
    else continue; fi
    [ "$port" = 443 ] && ssl=1
    if (( ssl )); then https_port=${https_port:-$port}; else http_port=${http_port:-$port}; fi
    cands+=("$addr $port $ssl")
  done
  (( ${#cands[@]} )) || cands=("* 80 0")
  if [ -n "$https_port" ]; then HC_SCHEME=https; HC_PORT=$https_port; else HC_SCHEME=http; HC_PORT=${http_port:-80}; fi
  HC_LISTEN_SEEN=$(printf '%s,' "${cands[@]}")
  local c a p s
  for c in "${cands[@]}"; do
    read -r a p s <<<"$c"; [ "$p" = "$HC_PORT" ] || continue
    case $a in
      '*'|0.0.0.0|_default_) wild4=${wild4:-127.0.0.1} ;;
      ::|'[::]') wild6=${wild6:-::1} ;;
      *:*) addr_assigned "$a" && v6=${v6:-$a} ;;
      *) addr_assigned "$a" && v4=${v4:-$a} ;;
    esac
  done
  HC_ADDR=${wild4:-${wild6:-${v4:-$v6}}}
  [ -n "$HC_ADDR" ]
}

# hc_vhost_static SITE: §3.1.1 4d - the vhost the web server picks for (addr:port, host) is the site's.
hc_vhost_static() {
  local site=$1 picked=""
  case ${S_KIND[$site]} in
    nginx_fastcgi) picked=$(nginx_pick "$HC_ADDR" "$HC_PORT" "$HC_HOST") ;;
    apache_proxy_fcgi|apache_mod_php) picked=$(apache_pick "$HC_ADDR" "$HC_PORT" "$HC_HOST") ;;
    *) HC_VHOST_CHECK=none; return 0 ;;
  esac
  [ -n "$picked" ] || return 1
  local r; for r in ${S_REFS[$site]//,/ }; do [ "$r" = "$picked" ] && { HC_VHOST_CHECK=static; return 0; }; done
  log "vhost check: $HC_ADDR:$HC_PORT $HC_HOST -> $picked, site refs ${S_REFS[$site]}"
  return 1
}

# nginx_pick ADDR PORT HOST: file:line of the server block Nginx uses (request_processing.html).
nginx_pick() {
  probe 10 nginx -T 2>/dev/null | awk -v A="$1" -v P="$2" -v H="$3" '
    /^# configuration file .*:$/ { file = substr($0, 22); sub(/:$/, "", file); ln = 0; next }
    { ln++; line = $0; sub(/(^|[ \t])#.*/, "", line); gsub(/\{/, "{\n", line); gsub(/;/, ";\n", line); gsub(/\}/, "\n}\n", line)
      n = split(line, parts, "\n"); for (i = 1; i <= n; i++) st(parts[i]) }
    function st(s,   w, k, v, a, p) {
      gsub(/^[ \t]+|[ \t]+$/, "", s); if (s == "") return
      split(s, w, /[ \t;]+/)
      if (s ~ /\{$/) { d++; if (w[1] == "server" && cur == "") { cur = ++ns; sd = d; ref[cur] = file ":" ln; nl[cur] = 0 } ; return }
      if (s ~ /^\}/) { if (cur != "" && d == sd) cur = ""; d--; return }
      if (cur == "") return
      if (w[1] == "listen") {
        v = w[2]; a = "*"; p = v
        if (v ~ /^\[.*\]:[0-9]+$/) { a = v; sub(/\]:[0-9]+$/, "", a); sub(/^\[/, "", a); p = v; sub(/.*:/, "", p) }
        else if (v ~ /:[0-9]+$/) { a = v; sub(/:[0-9]+$/, "", a); p = v; sub(/.*:/, "", p) }
        else if (v !~ /^[0-9]+$/) { a = v; p = 80 }
        if (a == "0.0.0.0") a = "*"
        if (p == P && (a == A || a == "*" || (A == "127.0.0.1" && a == "*") || (A == "::1" && a == "::"))) {
          exact = (a == A) ? 2 : 1
          if (exact > m[cur]) m[cur] = exact
          if (s ~ /default_server/ || s ~ /[ \t]default([ \t;]|$)/) dflt[cur] = 1
        }
      }
      if (w[1] == "server_name") for (k = 2; k in w; k++) if (w[k] != "") names[cur] = names[cur] " " tolower(w[k])
    }
    END {
      best = 0; for (b = 1; b <= ns; b++) if (m[b] > best) best = m[b]
      if (best == 0) exit
      h = tolower(H); pick = ""; wl = 0
      for (b = 1; b <= ns; b++) if (m[b] == best) { nn = split(names[b], x, " "); for (k = 1; k <= nn; k++) if (x[k] == h) { print ref[b]; exit } }
      for (b = 1; b <= ns; b++) if (m[b] == best) { nn = split(names[b], x, " "); for (k = 1; k <= nn; k++) {
          if (x[k] ~ /^\*\./ || x[k] ~ /^\./) { suf = substr(x[k], index(x[k], ".")); if (substr(h, length(h) - length(suf) + 1) == suf && length(suf) > wl) { wl = length(suf); pick = ref[b] } } } }
      if (pick != "") { print pick; exit }
      for (b = 1; b <= ns; b++) if (m[b] == best) { nn = split(names[b], x, " "); for (k = 1; k <= nn; k++) {
          if (x[k] ~ /\.\*$/) { pre = substr(x[k], 1, length(x[k]) - 1); if (substr(h, 1, length(pre)) == pre && length(pre) > wl) { wl = length(pre); pick = ref[b] } } } }
      if (pick != "") { print pick; exit }
      for (b = 1; b <= ns; b++) if (m[b] == best && dflt[b]) { print ref[b]; exit }
      for (b = 1; b <= ns; b++) if (m[b] == best) { print ref[b]; exit }
    }'
}

# apache_pick ADDR PORT HOST: file:line of the <VirtualHost> Apache uses (vhosts/details.html).
apache_pick() {
  [ -n "$APACHE_CTL" ] || return 0
  probe 10 "$APACHE_CTL" -S 2>&1 | awk -v A="$1" -v P="$2" -v H="$3" '
    function grp(g,   a, p) { a = g; sub(/:[0-9]+$/, "", a); p = g; sub(/.*:/, "", p); ga = a; gp = p }
    /^[^ ]+:[0-9]+ +is a NameVirtualHost/ { grp($1); cg = ++ng; gaddr[cg] = ga; gport[cg] = gp; next }
    /^[^ ]+:[0-9]+ +[^ ]+ \(\/.*:[0-9]+\)/ { grp($1); cg = ++ng; gaddr[cg] = ga; gport[cg] = gp; r = $3; gsub(/[()]/, "", r); first[cg] = r; name[cg, ++cnt[cg]] = tolower($2); vref[cg, cnt[cg]] = r; next }
    /^ +default server / { r = $4; gsub(/[()]/, "", r); first[cg] = r; next }
    /^ +port [0-9]+ namevhost / { r = $5; gsub(/[()]/, "", r); name[cg, ++cnt[cg]] = tolower($4); vref[cg, cnt[cg]] = r; next }
    /^ +alias / { als[cg, cnt[cg]] = als[cg, cnt[cg]] " " tolower($2); next }
    END {
      g = 0
      for (i = 1; i <= ng; i++) if (gport[i] == P && gaddr[i] == A) g = i
      if (!g) for (i = 1; i <= ng; i++) if (gport[i] == P && (gaddr[i] == "*" || gaddr[i] == "_default_")) g = i
      if (!g) exit
      h = tolower(H)
      for (k = 1; k <= cnt[g]; k++) { if (name[g, k] == h || index(als[g, k] " ", " " h " ")) { print vref[g, k]; exit } }
      print first[g]
    }'
}

# --- URL set (§3.1, §3.2) ----------------------------------------------------------------------------
hc_build_urls() { # hc_build_urls SITE KEY
  local site=$1 key=$2 line u opts exp sz cb n=0 reason dropped=0
  HC_URL=(); HC_EXPECT=(); HC_SIZEIGN=(); HC_CB=(); HC_INSECURE=()
  local base="$HC_SCHEME://$HC_HOST"; { [ "$HC_SCHEME" = http ] && [ "$HC_PORT" = 80 ]; } || { [ "$HC_SCHEME" = https ] && [ "$HC_PORT" = 443 ]; } || base+=":$HC_PORT"
  HC_URL+=("$base/"); HC_EXPECT+=(""); HC_SIZEIGN+=(0); HC_CB+=("$HC_CACHEBUST"); HC_INSECURE+=(0)
  local decl=()
  while IFS= read -r line; do [[ $line =~ ^[[:space:]]*hc_url[[:space:]]+(.*)$ ]] && decl+=("${BASH_REMATCH[1]}"); done < <(site_conf_lines "$site" "$key")
  for u in ${MIG_HC_URLS[@]+"${MIG_HC_URLS[@]}"}; do decl+=("$u"); done
  for line in ${decl[@]+"${decl[@]}"}; do
    read -r u opts <<<"$line"; exp=""; sz=0; cb=$HC_CACHEBUST
    [[ $opts =~ expect=([0-9]{3}) ]] && exp=${BASH_REMATCH[1]}
    [[ $opts == *size=ignore* ]] && sz=1
    [[ $opts == *cachebust=off* ]] && cb=off
    if ! url_ok "$u" "$site"; then reason=$REPLY
      mig_warn ERR-HC-422-02 "Check URL {url} skipped: {reason}." url="$u" reason="$reason"; continue; fi
    if (( n >= ${HCP[max_user_urls]} )); then dropped=$((dropped + 1)); continue; fi
    if [[ $u == /* ]]; then u="$base$u"
    else u="$HC_SCHEME://${u#*://}"; fi
    HC_URL+=("$u"); HC_EXPECT+=("$exp"); HC_SIZEIGN+=("$sz"); HC_CB+=("$cb"); HC_INSECURE+=(0); n=$((n + 1))
  done
  (( dropped )) && mig_warn ERR-HC-422-02 "Check URL {url} skipped: {reason}." url="($dropped)" reason="more than ${HCP[max_user_urls]} URLs"
  return 0
}

# --- one request ------------------------------------------------------------------------------
# hc_get IDX TAG: R_CODE R_SIZE R_MS R_LOC R_EXIT, body in $WORK_DIR/hc.body
hc_get() {
  local i=$1 tag=$2 u=${HC_URL[$1]} hostport port out ins=()
  if [ "${HC_CB[$i]}" = on ] && [ -n "$tag" ]; then [[ $u == *\?* ]] && u+="&qp_hc=$tag" || u+="?qp_hc=$tag"; fi
  hostport=${u#*://}; hostport=${hostport%%/*}; hostport=${hostport%%\?*}
  local host=${hostport%:*}
  if [[ $hostport == *:* ]]; then port=${hostport##*:}
  else port=80; [[ $u == https:* ]] && port=443; fi
  (( ${HC_INSECURE[$i]} )) && ins=(--insecure)
  local addr=$HC_ADDR; [[ $addr == *:* ]] && addr="[$addr]"
  out=$(curl -sS --noproxy '*' -o "$WORK_DIR/hc.body" --max-redirs 0 --max-time "${HCP[timeout_s]}" --connect-timeout "${HCP[connect_timeout_s]}" \
        --resolve "$host:$port:$addr" -H "User-Agent: php-quickpatch-hc/$QP_VERSION" -H 'Accept-Encoding: identity' \
        -H 'Cache-Control: no-cache' ${ins[@]+"${ins[@]}"} -w '%{http_code}\t%{size_download}\t%{time_total}\t%{redirect_url}' \
        "$u" 9>&- 7>&- 2>/dev/null)
  R_EXIT=$?
  IFS=$'\t' read -r R_CODE R_SIZE R_MS R_LOC <<<"$out"
  R_CODE=${R_CODE:-000}; R_SIZE=${R_SIZE:-0}; R_MS=$(awk -v t="${R_MS:-0}" 'BEGIN { printf "%d", t * 1000 }')
  R_LOC=$(sed -E 's/([?&])qp_hc=[^&]*&?/\1/; s/[?&]$//' <<<"${R_LOC:-}")
  [ -f "$WORK_DIR/hc.body" ] || : >"$WORK_DIR/hc.body"
}

# hc_forbidden: REPLY = forbidden strings found in the last body (|-joined).
hc_forbidden() {
  local re=$HC_FORBID_PHP s found=()
  [ "${SW[node_kind]:-}" ] && re=$HC_FORBID_NODE
  local IFS='|'; for s in $re; do grep -qF -- "$s" "$WORK_DIR/hc.body" 2>/dev/null && found+=("$s"); done
  REPLY="${found[*]}"
}

# --- baseline (§4) ------------------------------------------------------------------------------
# hc_baseline SITE RUN: 5 rounds on $OLD; sets B_* arrays; 0 = home valid.
hc_baseline() {
  local site=$1 run=$2 r i n=${#HC_URL[@]} codes sizes times locs forb
  declare -A codes=() sizes=() times=() locs=() forb=()
  for ((r = 1; r <= HCP[baseline_rounds]; r++)); do
    for ((i = 0; i < n; i++)); do
      [ "${HC_ALIVE[$i]:-1}" = 1 ] || continue
      hc_get "$i" "$run-b$r"
      if (( R_EXIT == 60 )) && (( r == 1 )) && (( ! ${HC_INSECURE[$i]} )); then
        HC_INSECURE[$i]=1; HC_TLS_VERIFY=false; hc_get "$i" "$run-b$r"
      fi
      hc_forbidden
      codes[$i]+="${codes[$i]:+ }$R_CODE"; sizes[$i]+="${sizes[$i]:+ }$R_SIZE"; times[$i]+="${times[$i]:+ }$R_MS"
      locs[$i]=$R_LOC; [ -n "$REPLY" ] && forb[$i]+="|$REPLY"
    done
    if (( r == 1 )) && [ -n "${HC_ACCESS_LOG:-}" ]; then hc_access_log_check "$run"; fi
    (( r < HCP[baseline_rounds] )) && sleep "${HCP[baseline_interval_s]}"
  done
  local ok_home=1 cs c0 all
  for ((i = 0; i < n; i++)); do
    cs=${codes[$i]:-}; c0=${cs%% *}; all=1
    for c in $cs; do [ "$c" = "$c0" ] || all=0; done
    local good=1
    (( all )) || good=0
    [[ $c0 == 5* || $c0 == 000 ]] && good=0
    if (( i == 0 )); then
      if [ -n "${HC_EXPECT[0]}" ]; then [ "$c0" = "${HC_EXPECT[0]}" ] || good=0
      else [[ $c0 =~ ^[23][0-9][0-9]$ ]] || good=0; fi
    elif [ -n "${HC_EXPECT[$i]}" ]; then [ "$c0" = "${HC_EXPECT[$i]}" ] || good=0
    else [[ $c0 =~ ^[234][0-9][0-9]$ ]] || good=0; fi
    if (( ! good )); then
      if (( i == 0 )); then ok_home=0; HC_BAD_CODES=$cs
      else HC_ALIVE[$i]=0
        mig_warn ERR-HC-412-04 "Check URL {url} of {site} was removed from the probe set: different HTTP codes, a 5xx or an unexpected code in 5 samples before the switch (codes {codes})." url="${HC_URL[$i]}" site="$site" codes="$cs"
      fi
      continue
    fi
    B_CODE[$i]=$c0; B_LOC[$i]=${locs[$i]:-}; B_FORBID[$i]=${forb[$i]:-}; B_SIZES[$i]=${sizes[$i]}
    read -r B_M[$i] B_SPREAD[$i] B_P95[$i] < <(printf '%s\n' ${sizes[$i]} | sort -n | awk -v t="${times[$i]}" '
      { s[NR] = $1 } END { m = s[int((NR + 1) / 2)]; sp = (m > 0) ? (s[NR] - s[1]) / m : 0
        n = split(t, x, " "); mx = 0; for (k = 1; k <= n; k++) if (x[k] + 0 > mx) mx = x[k] + 0
        printf "%d %.4f %d\n", m, sp, mx }')
  done
  (( ok_home ))
}

# --- logs (§5) ------------------------------------------------------------------------------------
# hc_log_sources SITE: files to read (pool error_log of the target first, then the site's sources).
hc_log_sources() {
  local f out=()
  [ -n "${SW[fpm_error_log]:-}" ] && out+=("${SW[fpm_error_log]}")
  [ -n "${SW[to_branch]:-}" ] && [ -z "${SW[node_kind]:-}" ] && out+=("/var/log/php${SW[to_branch]}-fpm.log")
  for f in ${S_LOGS[$1]:-}; do out+=("$f"); done
  printf '%s\n' "${out[@]}" | awk 'NF && !s[$0]++'
}

# hc_log_mark: byte offset + inode of every log file at t_C7 (BR-HC-005).
hc_log_mark() {
  local f
  LOG_OFF=(); LOG_INO=()
  while IFS= read -r f; do
    [[ $f == journal:* ]] && { LOG_OFF[$f]=$(date +%s); continue; }
    LOG_OFF[$f]=$(stat -c %s "$f" 2>/dev/null || echo 0); LOG_INO[$f]=$(stat -c %i "$f" 2>/dev/null || echo 0)
  done < <(hc_log_sources "$1")
}

# hc_log_new SITE: new lines (since the mark) that belong to the site (§5.3) on stdout.
hc_log_new() {
  local site=$1 f off ino cur root=${S_ROOT[$1]:-} pool=${SW[fpm_pool]:-} own
  for f in "${!LOG_OFF[@]}"; do
    if [[ $f == journal:* ]]; then
      has journalctl && journalctl -u "${f#journal:}" --since "@${LOG_OFF[$f]}" -o short-iso --no-pager 2>/dev/null | tail -n +2
      continue
    fi
    [ -f "$f" ] || continue
    off=${LOG_OFF[$f]}; ino=${LOG_INO[$f]}; cur=$(stat -c %i "$f" 2>/dev/null)
    own=0; [ "$f" = "${SW[fpm_error_log]:-}" ] && own=1
    {
      if [ "$cur" != "$ino" ]; then [ -f "$f.1" ] && tail -c +"$((off + 1))" "$f.1"; cat "$f"
      else tail -c +"$((off + 1))" "$f"; fi
    } 2>/dev/null | if (( own )); then cat; else grep -F -e "[pool ${pool:-qp-none}]" -e "${HC_HOST:-qp-none}" ${root:+-e "$root"} || true; fi
  done
}

# hc_w0 SITE: PHP Warning lines of the site in the 600 s before now (timestamps of PHP and Nginx logs).
hc_w0() {
  local f now; now=$(date -u +%s)
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    awk -v now="$now" -v re="$RE_WARN" '
      function days(y, m, d) { if (m <= 2) { y--; m += 12 } return 365 * y + int(y / 4) - int(y / 100) + int(y / 400) + int(153 * (m - 3) / 5 + 2) / 1 + d }
      BEGIN { split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", mn, " "); for (i = 1; i <= 12; i++) mon[mn[i]] = i; e0 = days(1970, 1, 1) }
      $0 !~ re { next }
      {
        t = -1
        if (match($0, /\[[0-9][0-9]-[A-Z][a-z][a-z]-[0-9][0-9][0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]/)) {
          s = substr($0, RSTART + 1, 20); t = (days(substr(s, 8, 4) + 0, mon[substr(s, 4, 3)], substr(s, 1, 2) + 0) - e0) * 86400 + substr(s, 13, 2) * 3600 + substr(s, 16, 2) * 60 + substr(s, 19, 2)
        } else if (match($0, /^[0-9][0-9][0-9][0-9]\/[0-9][0-9]\/[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]/)) {
          s = substr($0, 1, 19); t = (days(substr(s, 1, 4) + 0, substr(s, 6, 2) + 0, substr(s, 9, 2) + 0) - e0) * 86400 + substr(s, 12, 2) * 3600 + substr(s, 15, 2) * 60 + substr(s, 18, 2)
        }
        if (t >= 0 && t >= now - 600) c++
      }
      END { print c + 0 }' "$f"
  done < <(hc_log_sources "$1") | awk '{ s += $1 } END { print s + 0 }'
}

hc_keep_log() { # ≤ 50 violating log lines, redacted (BR-HC-011)
  local l
  while IFS= read -r l; do
    (( ${#HC_LOGLINES[@]} >= 50 )) && return 0
    clean "$(redact_text "${l:0:500}")"; HC_LOGLINES+=("$REPLY")
  done
}

# --- access log check (§3.1.1 4e) ----------------------------------------------------------------
hc_access_log_check() {
  local run=$1 i
  for ((i = 0; i < 10; i++)); do
    grep -qF "qp_hc=$run-" "$HC_ACCESS_LOG" 2>/dev/null && { HC_VHOST_CHECK=static+access_log; return 0; }
    sleep 1
  done
  HC_VHOST_FAIL=1
}

# --- runtime process checks (HC-C9) -----------------------------------------------------------------
hc_runtime_ok() {
  if [ -n "${SW[node_kind]:-}" ]; then node_hc_ok; return; fi
  local unit=${SW[fpm_unit]:-}
  if [ -n "$unit" ]; then svc_active "$unit" || return 1; fi
  return 0
}

# --- the window (§6) --------------------------------------------------------------------------------
# hc_window SITE RUN: HC_VERDICT PASS|FAIL|TERM, HC_VIOL[], HC_ROUNDS[]; fail-fast criteria stop early.
hc_window() {
  local site=$1 run=$2 rounds interval k i n=${#HC_URL[@]} t0
  local -a c4rounds=() samples=()
  if [ "$HC_MODE" = skip ]; then rounds=$(( ${HCP[skip_window_s]%.*} / 30 )); interval=30; n=1
  else interval=${HCP[interval_s]%.*}; rounds=$(( ${HCP[window_s]%.*} / interval )); fi
  HC_WINDOW_S=$(( rounds * interval )); SW[hc_window]=$HC_WINDOW_S; sw_save
  HC_VIOL=(); HC_ROUNDS=(); HC_TIMEOUTS=0; HC_ROUNDS_DONE=0; HC_VERDICT=""; HC_VSEEN=()
  t0=$(date +%s)
  local wmax; wmax=$(awk -v a="${HCP[warn_min]}" -v f="${HCP[warn_factor]}" -v w="$HC_W0" 'BEGIN { x = f * w; printf "%d", (x > a ? x : a) }')
  local warn_total=0
  for ((k = 1; k <= rounds; k++)); do
    local due=$(( t0 + (k - 1) * interval )) nowt; nowt=$(date +%s)
    (( due > nowt )) && sleep $(( due - nowt ))
    (( MIG_TERM )) && { HC_VERDICT=TERM; return 0; }
    local per=()
    for ((i = 0; i < n; i++)); do
      [ "${HC_ALIVE[$i]:-1}" = 1 ] && [ -n "${B_CODE[$i]:-}" ] || continue
      hc_get "$i" "$run-$k"
      local to=0
      if (( R_EXIT == 28 )); then
        to=1; HC_TIMEOUTS=$((HC_TIMEOUTS + 1))
        if (( ${HCP[timeout_retry]%.*} > 0 )); then sleep 5; hc_get "$i" "$run-$k"r
          if (( R_EXIT == 28 )); then HC_TIMEOUTS=$((HC_TIMEOUTS + 1)); hc_viol HC-C3 "$i" "2 consecutive timeouts"; fi
        fi
      fi
      (( HC_TIMEOUTS > 2 )) && hc_viol HC-C3 "$i" "$HC_TIMEOUTS timeouts in the window"
      jo url=s:"${HC_URL[$i]}" code=s:"$R_CODE" size=n:"$R_SIZE" ms=n:"$R_MS" timeout=b:$to; per+=("$REPLY")
      if (( R_EXIT != 28 )); then
        [[ $R_CODE == 5* ]] && hc_viol HC-C2 "$i" "HTTP $R_CODE"
        [ "$R_CODE" = "${B_CODE[$i]}" ] || hc_viol HC-C1 "$i" "HTTP $R_CODE, baseline ${B_CODE[$i]}"
        if [ "$HC_MODE" != skip ]; then
          hc_forbidden; local fs=$REPLY s
          if [ -n "$fs" ]; then
            while IFS= read -r s; do [ -n "$s" ] || continue; [[ ${B_FORBID[$i]} == *"$s"* ]] || hc_viol HC-C5 "$i" "body contains $s"; done < <(tr '|' '\n' <<<"$fs")
          fi
          if [[ $R_CODE == 3* ]]; then [ "$R_LOC" = "${B_LOC[$i]}" ] || c4rounds[$k]+=" $i"
          elif (( ! ${HC_SIZEIGN[$i]} )); then
            awk -v s="$R_SIZE" -v m="${B_M[$i]}" -v sp="${B_SPREAD[$i]}" -v sm="${HCP[small_body_bytes]}" -v ab="${HCP[small_body_abs_bytes]}" \
                -v lo="${HCP[size_dev_pct]}" -v hi="${HCP[size_dev_cap_pct]}" 'BEGIN {
                d = s - m; if (d < 0) d = -d
                if (m < sm) exit !(d <= ab)
                t = 2 * sp * 100; if (t < lo) t = lo; if (t > hi) t = hi
                exit !(d / m * 100 <= t) }' || c4rounds[$k]+=" $i"
          fi
          (( k > 1 )) && samples[$i]+=" $R_MS"
        fi
      fi
    done
    # logs and runtime (HC-C7, HC-C8, HC-C9)
    if [ "$HC_MODE" != skip ]; then
      local newl; newl=$(hc_log_new "$site")
      local fat crash wn
      if [ -n "${SW[node_kind]:-}" ]; then fat=$(grep -cE "$RE_NODE_ERR" <<<"$newl")
      else fat=$(grep -cE "$RE_FATAL" <<<"$newl"); fi
      crash=$(grep -cE "$RE_CRASH" <<<"$newl"); wn=$(grep -cE "$RE_WARN" <<<"$newl")
      (( fat > 0 )) && { hc_viol HC-C7 "" "$fat new fatal line(s)"; grep -E "$RE_FATAL|$RE_NODE_ERR" <<<"$newl" | hc_keep_log; }
      (( crash > 0 )) && { hc_viol HC-C9 "" "$crash worker crash line(s)"; grep -E "$RE_CRASH" <<<"$newl" | hc_keep_log; }
      warn_total=$wn
      (( warn_total > wmax )) && { hc_viol HC-C8 "" "$warn_total new PHP Warning line(s) > $wmax"; grep -E "$RE_WARN" <<<"$newl" | head -n 10 | hc_keep_log; }
    fi
    hc_runtime_ok || hc_viol HC-C9 "" "runtime of the target is not active (${SW[fpm_unit]:-${SW[node_unit]:-}})"
    jarr per; local jp=$REPLY
    jo k=n:$k at=s:"$(iso_now)" per_url=j:"$jp"; HC_ROUNDS+=("$REPLY"); HC_ROUNDS_DONE=$k
    say "  health check round $k/$rounds: $(printf '%s ' "${per[@]}" | grep -oE '"code":"[0-9]+"' | cut -d'"' -f4 | paste -sd' ') ${HC_VIOL[*]:+violations ${#HC_VIOL[@]}}"
    if (( ${#HC_VIOL[@]} )); then HC_VERDICT=FAIL; return 0; fi
  done
  # end of the window: HC-C4 (2 rounds with a deviation), HC-C6 (P95 of rounds 2..N)
  local rk cnt=0; for rk in "${!c4rounds[@]}"; do [ -n "${c4rounds[$rk]}" ] && cnt=$((cnt + 1)); done
  if (( cnt >= 2 )); then
    for rk in "${!c4rounds[@]}"; do for i in ${c4rounds[$rk]}; do hc_viol HC-C4 "$i" "size or Location differs from the baseline (round $rk)"; done; done
  fi
  if [ "$HC_MODE" != skip ]; then
    for ((i = 0; i < n; i++)); do
      [ -n "${samples[$i]:-}" ] || continue
      local p95 lim
      read -r p95 lim < <(printf '%s\n' ${samples[$i]} | sort -n | awk -v b="${B_P95[$i]}" -v f="${HCP[p95_factor]}" -v add="${HCP[p95_add_ms]}" -v fl="${HCP[p95_floor_ms]}" '
        { s[NR] = $1 } END { k = int(0.95 * NR + 0.999999); if (k < 1) k = 1; p = s[k]
          a = f * b; if (b + fl > a) a = b + fl; if (a > b + add) a = b + add; printf "%d %d\n", p, a }')
      (( p95 > lim )) && hc_viol HC-C6 "$i" "P95 ${p95} ms > ${lim} ms"
    done
  fi
  if (( ${#HC_VIOL[@]} )); then HC_VERDICT=FAIL; else HC_VERDICT=PASS; fi
}

declare -gA HC_VSEEN=()
hc_viol() { # hc_viol CRITERION URL_IDX DETAIL (once per criterion and URL)
  local u=""; [ -n "$2" ] && u=${HC_URL[$2]}
  [ -n "${HC_VSEEN["$1|$u"]:-}" ] && return 0
  HC_VSEEN["$1|$u"]=1
  jo criterion=s:"$1" url=S:"$u" detail=s:"$3"; HC_VIOL+=("$REPLY")
  log "health check violation $1 ${u:-} $3"
}

hc_criteria() { # REPLY = comma list of violated criteria
  REPLY=$(printf '%s\n' "${HC_VIOL[@]}" | grep -oE '"criterion":"HC-C[0-9]"' | cut -d'"' -f4 | sort -u | paste -sd,)
}

# hc_after_rollback: 1 round on $OLD, codes must equal the baseline codes (§6.4).
hc_after_rollback() {
  local run=$1 i n=${#HC_URL[@]} bad="" try
  for ((try = 1; try <= 10; try++)); do           # the graceful reload takes effect shortly after the signal
    bad=""
    for ((i = 0; i < n; i++)); do
      [ -n "${B_CODE[$i]:-}" ] || continue
      hc_get "$i" "$run-rb$try"
      [ "$R_CODE" = "${B_CODE[$i]}" ] || bad+="${HC_URL[$i]} $R_CODE (baseline ${B_CODE[$i]}); "
    done
    [ -z "$bad" ] && break
    sleep 1
  done
  REPLY=$bad; [ -z "$bad" ]
}

# --- files ------------------------------------------------------------------------------------------
hc_baseline_json() { # REPLY = baseline object (also used for healthcheck --baseline-only)
  local i per=() n=${#HC_URL[@]}
  for ((i = 0; i < n; i++)); do
    [ -n "${B_CODE[$i]:-}" ] || continue
    jas ${B_SIZES[$i]}; local js=$REPLY
    jo url=s:"${HC_URL[$i]}" code_b=s:"${B_CODE[$i]}" size_b=n:"${B_M[$i]}" spread=n:"${B_SPREAD[$i]}" p95_ms=n:"${B_P95[$i]}" \
       location=S:"${B_LOC[$i]}" forbidden_in_baseline=S:"${B_FORBID[$i]#|}" sizes=j:"$js"; per+=("$REPLY")
  done
  jarr per; local jp=$REPLY
  jo rounds=n:"${HCP[baseline_rounds]}" per_url=j:"$jp" w0=n:"$HC_W0" addr=s:"$HC_ADDR" host=s:"$HC_HOST" port=s:"$HC_PORT" \
     scheme=s:"$HC_SCHEME" vhost_check=S:"$HC_VHOST_CHECK" tls_verify=b:"$([ "${HC_TLS_VERIFY:-true}" = false ] && echo 0 || echo 1)" \
     taken_at=s:"$(iso_now)"
}

hc_save_files() { # hc_save_files DIR: baseline.json, baseline.tsv, hc.json
  local d=$1 i
  hc_baseline_json; (umask 077; printf '%s\n' "$REPLY" >"$d/baseline.json")
  (umask 077; for ((i = 0; i < ${#HC_URL[@]}; i++)); do
     [ -n "${B_CODE[$i]:-}" ] || continue
     printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$i" "${HC_URL[$i]}" "${B_CODE[$i]}" "${B_M[$i]}" "${B_SPREAD[$i]}" \
       "${B_P95[$i]}" "${B_LOC[$i]:--}" "${B_FORBID[$i]:--}" "${HC_SIZEIGN[$i]}" "${HC_CB[$i]}"
   done >"$d/baseline.tsv"
   printf 'addr\t%s\nhost\t%s\nport\t%s\nscheme\t%s\nw0\t%s\n' "$HC_ADDR" "$HC_HOST" "$HC_PORT" "$HC_SCHEME" "$HC_W0" >"$d/baseline.meta")
  hc_summary_json "backups/${d##*/}/hc.json"; local sum=$REPLY
  jarr HC_ROUNDS; local jr=$REPLY; jas ${HC_LOGLINES[@]+"${HC_LOGLINES[@]}"}; local jl=$REPLY
  json_merge "$sum" "{\"rounds\":$jr,\"log_lines\":$jl,\"baseline\":$(cat "$d/baseline.json")}"
  (umask 077; printf '%s\n' "$REPLY" >"$d/hc.json")
}

# hc_restore DIR: baseline arrays from baseline.tsv (interrupted window re-run, §6.4).
hc_restore() {
  local d=$1 i u c m sp p loc fb si cb k v
  HC_URL=(); HC_EXPECT=(); HC_SIZEIGN=(); HC_CB=(); HC_INSECURE=(); HC_ALIVE=()
  while IFS=$'\t' read -r i u c m sp p loc fb si cb; do
    HC_URL[$i]=$u; B_CODE[$i]=$c; B_M[$i]=$m; B_SPREAD[$i]=$sp; B_P95[$i]=$p; B_LOC[$i]=${loc#-}; B_FORBID[$i]=${fb#-}
    HC_SIZEIGN[$i]=$si; HC_CB[$i]=$cb; HC_INSECURE[$i]=0; HC_EXPECT[$i]=""; HC_ALIVE[$i]=1
  done <"$d/baseline.tsv"
  while IFS=$'\t' read -r k v; do
    case $k in addr) HC_ADDR=$v ;; host) HC_HOST=$v ;; port) HC_PORT=$v ;; scheme) HC_SCHEME=$v ;; w0) HC_W0=$v ;; esac
  done <"$d/baseline.meta"
  [ ${#HC_URL[@]} -gt 0 ]
}

hc_summary_json() { # REPLY = HcSummary
  local verdict=${HC_VERDICT:-}; [ "$verdict" = TERM ] && verdict=FAIL
  jarr HC_VIOL; local jv=$REPLY
  jo verdict=S:"$verdict" mode=s:"$HC_MODE" window_s=n:"${HC_WINDOW_S:-${HCP[window_s]%.*}}" rounds_done=n:"${HC_ROUNDS_DONE:-0}" \
     violations=j:"$jv" report_ref=S:"$1"
}
