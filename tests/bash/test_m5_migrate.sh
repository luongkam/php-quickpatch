#!/usr/bin/env bash
# M5 — migrate: switch one site C1-C12 with the health check HC-C0..C9, automatic rollback,
# rollback-site R1-R7, ack, status, hc-urls, BR-ENV-013 (FR-UPG-SWT-001, FR-UPG-CFG-001,
# FR-UPG-HC-001..006, FR-UPG-RBK-001/002, FR-UPG-ACK-001, FR-UPG-SEQ-001, FR-CLI-CMD-003;
# TC-UPG-010..013, 024..038, 101..106, 108).
#
# Runs against a real Nginx and two real PHP-FPM branches (Debian layout, PB-001/PB-005) inside a
# private mount namespace: /etc, /var/lib, /var/log and /run are overlays, so the host keeps its
# configuration; the daemons the test starts are stopped on exit. The site's index.php changes its
# answer on the target branch only (mode file), which drives every health check criterion.
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
need_root
OLD=""; NEW=""
for b in /usr/sbin/php-fpm[0-9]*; do
  [ -x "$b" ] || continue; v=${b#/usr/sbin/php-fpm}
  if [ -z "$OLD" ]; then OLD=$v; elif [ -z "$NEW" ]; then NEW=$v; fi
done
if ! command -v nginx >/dev/null || [ -z "$NEW" ] || ! command -v curl >/dev/null || ! command -v python3 >/dev/null; then
  echo "# skip $(basename "$0"): needs nginx, two php-fpm branches (/usr/sbin/php-fpmX.Y), curl and python3"; exit 0
fi
if [ -z "${QP_IN_NS:-}" ]; then QP_IN_NS=1 exec unshare -m --propagation private bash "$0" "$@"; fi

T=$(new_tmp)
for d in etc var/lib var/log run; do
  mkdir -p "$T/ov/$d.u" "$T/ov/$d.w"
  mount -t overlay overlay -o "lowerdir=/$d,upperdir=$T/ov/$d.u,workdir=$T/ov/$d.w" "/$d" || { echo "# overlay /$d failed"; exit 1; }
done
mkdir -p /run/php && chown www-data:www-data /run/php && rm -f /run/php/* /run/nginx.pid
stop_all() { # every daemon started in this mount namespace
  local p me; me=$(readlink /proc/self/ns/mnt)
  for p in $(pgrep -f 'php-fpm: master|nginx: master'); do [ "$(readlink "/proc/$p/ns/mnt")" = "$me" ] && kill "$p" 2>/dev/null; done
  sleep 1
}
trap 'stop_all; for d in run var/log var/lib etc; do umount -l "/$d"; done; rm -rf "$T"' EXIT

STUB=$T/stub; mkdir -p "$STUB"
# sleep: waits of 5 s and more (health check rounds, baseline interval, timeout retry) take 50 ms.
# With $T/slowwin they take 1 s (a switch that stays in its window while other commands run).
cat >"$STUB/sleep" <<EOF
#!/bin/bash
a=\${1%%.*}
if [ "\${a:-0}" -ge 5 ] 2>/dev/null; then [ -f $T/slowwin ] && exec /usr/bin/sleep 1; exec /usr/bin/sleep 0.05; fi
exec /usr/bin/sleep "\$1"
EOF
# nginx: the real one, except for the faults a test asks for (flag files in $T).
cat >"$STUB/nginx" <<EOF
#!/bin/bash
if [ "\$*" = "-s reload" ] && [ -f $T/noreload ]; then exit 0; fi
if [ "\$*" = "-t" ] && [ -f $T/failtest ] && grep -rqs "qp-shop.test-$NEW.sock" /etc/nginx/sites-enabled/; then echo "nginx: [emerg] test fault"; exit 1; fi
if [ "\$*" = "-t" ] && [ -f $T/rbfail ] && ! grep -rqs "qp-shop.test-$NEW.sock" /etc/nginx/sites-enabled/; then echo "nginx: [emerg] test fault after restore"; exit 1; fi
exec /usr/sbin/nginx "\$@"
EOF
chmod +x "$STUB/sleep" "$STUB/nginx"

# --- the site -----------------------------------------------------------------------------------
W=$T/www/shop; mkdir -p "$W"; MODE=$T/mode; echo ok >"$MODE"; chmod 0644 "$MODE"
cat >"$W/index.php" <<EOF
<?php
\$mode = trim((string) @file_get_contents('$MODE'));
if (PHP_VERSION_ID >= ${NEW/./0}00 && (isset(\$_GET['qp_hc']) || \$mode === 'probe')) {
  switch (\$mode) {
    case 'probe': case '500': http_response_code(500); echo 'error'; exit;
    case '404': http_response_code(404); echo 'not found'; exit;
    case 'timeout': sleep(5); break;
    case 'slow': usleep(400000); break;
    case 'big': echo str_repeat('B', 6000); break;
    case 'forbid': echo 'Parse error: oops'; break;
    case 'fatallog': error_log('PHP Fatal error:  Uncaught Error: qp test in /x.php:1'); break;
    case 'warn': for (\$i = 0; \$i < 30; \$i++) trigger_error("qp test warning \$i", E_USER_WARNING); break;
    case 'crash': error_log('WARNING: [pool qp-shop.test] child 4242 exited on signal 11 (SIGSEGV) after 1.0 seconds from start'); break;
  }
} elseif (\$mode === 'oldbad' && isset(\$_GET['qp_hc'])) { static \$n = 0; http_response_code(rand(0, 1) ? 500 : 200); exit; }
echo '<html><body>', str_repeat('shop ', 600), '</body></html>';
EOF
printf '<?php echo "about page";\n' >"$W/about.php"
chmod -R a+rX "$T/www"
rm -f /etc/nginx/sites-enabled/default
cat >/etc/nginx/sites-enabled/shop.test.conf <<EOF
server {
    listen 127.0.0.1:18080;
    server_name shop.test www.shop.test;
    root $W;
    index index.php;
    access_log /var/log/nginx/shop.test.access.log;
    error_log /var/log/nginx/shop.test.error.log;
    location ~ \.php\$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php$OLD-fpm.sock;
    }
}
EOF
cat >/etc/nginx/sites-enabled/blog.test.conf <<EOF
server {
    listen 127.0.0.1:18080;
    server_name blog.test;
    root $W;
    location ~ \.php\$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php$OLD-fpm.sock;
    }
}
EOF
for b in "$OLD" "$NEW"; do sed -i "s#^;*php_admin_value\[error_log\].*##" "/etc/php/$b/fpm/pool.d/www.conf"; done
printf 'php_admin_value[error_log] = /var/log/php%s-www.error.log\nphp_admin_flag[log_errors] = on\n' "$OLD" >>"/etc/php/$OLD/fpm/pool.d/www.conf"
# packages without "pid =" (ondrej) write no pid file when started by the init script (no systemd here)
for b in "$OLD" "$NEW"; do grep -q '^pid' "/etc/php/$b/fpm/php-fpm.conf" || sed -i "s#^\[global\]#[global]\npid = /run/php/php$b-fpm.pid#" "/etc/php/$b/fpm/php-fpm.conf"; done
mkdir -p /etc/php-quickpatch && printf 'timeout_s = 3\n' >/etc/php-quickpatch/healthcheck.conf
PATH="$STUB:$PATH" service "php$OLD-fpm" start >/dev/null 2>&1
PATH="$STUB:$PATH" service "php$NEW-fpm" start >/dev/null 2>&1
/usr/sbin/nginx || { echo "# nginx did not start"; exit 1; }
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -S "/run/php/php$OLD-fpm.sock" ] && [ -S "/run/php/php$NEW-fpm.sock" ] && break; sleep 1; done
assert_eq "fixture: home page of shop.test on PHP $OLD" "$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' --resolve shop.test:18080:127.0.0.1 http://shop.test:18080/)" 200

J=$T/out.json
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
jr() { json_get "$J" "$1"; }
SD=/var/lib/php-quickpatch
binding() { grep -h 'fastcgi_pass' /etc/nginx/sites-enabled/shop.test.conf | sed -E 's/.*fastcgi_pass +([^;]+);.*/\1/'; }
set_mode() { echo "$1" >"$MODE"; }
last_run() { ls "$SD/backups" | tail -n1; }
REASON="switch without plan for the M5 test suite"

OLDSOCK="unix:/run/php/php$OLD-fpm.sock"; NEWSOCK="unix:/run/php/qp-shop.test-$NEW.sock"
sw() { qp migrate switch shop.test --target "$NEW" --no-plan --reason "$REASON" --yes --json >"$J" 2>"$T/err"; }
idx_status() { awk -F'\t' -v r="$1" '$2 == r && $11 !~ /^ack:/ { s = $6 } END { print s }' "$SD/switches/index.tsv"; }

# --- dry-run (no change) and the preconditions of FR-UPG-SEQ-001 ------------------------------------------
fp0=$(fingerprint /etc/nginx /etc/php)
qp migrate switch shop.test --target "$NEW" --no-plan --reason "$REASON" --dry-run --json >"$J" 2>"$T/err"; rc=$?
assert_eq "switch --dry-run exits 0" "$rc" 0
assert_eq "switch --dry-run changes nothing" "$(fingerprint /etc/nginx /etc/php)" "$fp0"
assert_eq "switch --dry-run: preview of pool, binding, reload" "$(jr '[c["type"] for c in d["result"]["preview"]["changes"]]')" \
  "['pool', 'site_binding', 'service']"
check "switch --dry-run --json valid against qp.migrate/1" schema_ok "$J"
qp migrate switch shop.test --target "$NEW" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-020: no plan and no --no-plan -> ERR-UPG-409-02, exit 2" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-409-02"
qp migrate switch shop.test --target "$NEW" --no-plan --reason short --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "--reason shorter than 20 characters -> ERR-CLI-400-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp migrate switch shop.test --target "$NEW" --no-plan --reason "$REASON" --json >"$J" 2>/dev/null </dev/null; rc=$?
assert_eq "switch without --yes and no TTY -> ERR-CLI-428-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-428-01"
qp migrate switch nosuch.test --target "$NEW" --no-plan --reason "$REASON" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "unknown site -> ERR-ENV-422-02" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-ENV-422-02"

# --- FR-UPG-SEQ-001 with a plan: order of site_order[], plan run of the P5 item (dry-run) -----------------------
PID=PLN-20261026-000000-abcd; mkdir -p "$SD/plans/$PID"; chmod 0700 "$SD/plans" "$SD/plans/$PID"
python3 - "$SD/plans/$PID" "$NEW" <<'PY'
import json, sys
d, new = sys.argv[1], sys.argv[2]
order = ['shop.test', 'blog.test']
json.dump({'plan_id': 'PLN-20261026-000000-abcd', 'runtime_id': 'php:0123456789ab', 'runtime_kind': 'php',
           'status': 'approved', 'mode': 'cross_branch', 'target': {'branch': new, 'patch_version': new + '.0'},
           'stale': False, 'stale_reasons': [], 'site_order': order, 'blocked_sites': [], 'inputs': {},
           'created_at': '2026-10-26T00:00:00.000Z'}, open(d + '/plan.json', 'w'))
json.dump({'items': [{'item_key': 'CHK-PHP-010-24@' + s, 'chk_id': 'CHK-PHP-010-24', 'scenario_id': 'SCN-PHP-011',
                      'site_id': s, 'phase': 'P5', 'action': 'Switch', 'status': 'PENDING', 'depends_on': [],
                      'blocked_by': [], 'exec_type': 'SEMI', 'verified': True,
                      'cli_action': 'migrate switch %s --target %s --plan $PLAN_ID' % (s, new)} for s in order]},
          open(d + '/items.json', 'w'))
PY
qp migrate switch blog.test --target "$NEW" --plan "$PID" --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-021: second site of site_order[] before the canary passed -> ERR-UPG-409-03" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-409-03"
qp migrate switch shop.test --target 8.9 --plan "$PID" --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "--target differs from the plan target -> ERR-CLI-400-01" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp plan run "$PID" CHK-PHP-010-24 --site shop.test --dry-run --json >"$J" 2>/dev/null; rc=$?
assert_eq "plan run of the P5 item --dry-run runs migrate switch --dry-run" \
  "$rc $(jr '(d["result"]["run"]["action"], d["result"]["run"]["child_schema"], d["result"]["run"]["child_exit_code"])')" \
  "0 ('migrate switch shop.test --target $NEW --plan \$PLAN_ID', 'qp.migrate/1', 0)"
assert_contains "plan run --dry-run: preview of the switch" "$(jr '[c["type"] for c in d["result"]["preview"]["changes"]]')" "'site_binding'"
rm -rf "$SD/plans"

# --- PASSED (TC-UPG-010, TC-UPG-030) ------------------------------------------------------------------
set_mode ok
sw; rc=$?
assert_eq "TC-UPG-010: switch PASSED exits 0" "$rc" 0
assert_eq "TC-UPG-010: status PASSED" "$(jr 'd["result"]["switch"]["status"]')" PASSED
assert_eq "TC-UPG-010: steps C1..C12 done" "$(jr '[s["step"] for s in d["result"]["steps"] if s["status"] == "done"]')" \
  "['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12']"
assert_eq "TC-UPG-010: binding now on the site pool of $NEW" "$(binding)" "$NEWSOCK"
check "TC-UPG-007: pool file qp-shop.test.conf names the site" grep -q '^; qp-site-id = shop.test$' "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
check "TC-UPG-008: pool has its own error_log and status path" grep -q "^pm.status_path = /qp-fpm-status" "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
check "migrate switch --json valid against qp.migrate/1" schema_ok "$J"
assert_eq "TC-UPG-030: hc verdict PASS, 10 rounds, mode full" "$(jr '(d["result"]["hc"]["verdict"], d["result"]["hc"]["rounds_done"], d["result"]["hc"]["mode"])')" "('PASS', 10, 'full')"
R1=$(jr 'd["result"]["run_id"]')
assert_eq "index.tsv: PREFLIGHT, SWITCHED, HC_RUNNING, PASSED" "$(awk -F'\t' -v r="$R1" '$2 == r { printf "%s ", $6 }' "$SD/switches/index.tsv")" \
  "PREFLIGHT SWITCHED HC_RUNNING PASSED "
assert_eq "manifest order §5.4: switch, reload fpm, created pool, reload nginx, copy" \
  "$(cut -f1 "$SD/backups/$R1/manifest" | paste -sd' ')" "switch reload created reload copy"
check "hc.json and baseline.json written" test -s "$SD/backups/$R1/hc.json" -a -s "$SD/backups/$R1/baseline.json"
qp migrate status --json >"$J" 2>/dev/null
assert_eq "migrate status lists the PASSED run" "$(jr '[(s["run_id"], s["status"]) for s in d["result"]["switches"]]')" "[('$R1', 'PASSED')]"

# --- rollback-site R1-R7 (TC-UPG-036, NFR-ENV-02 <= 60 s) ---------------------------------------------------
qp rollback-site shop.test --dry-run --json >"$J" 2>/dev/null
assert_eq "rollback-site --dry-run lists the manifest in reverse" "$(jr '[m["action"] for m in d["result"]["manifest"]]')" \
  "['copy', 'reload', 'created', 'reload', 'switch']"
assert_eq "rollback-site --dry-run changes nothing" "$(binding)" "$NEWSOCK"
t0=$(date +%s)
qp rollback-site shop.test --yes --json >"$J" 2>"$T/err"; rc=$?
dt=$(( $(date +%s) - t0 ))
assert_eq "TC-UPG-036: rollback-site exits 0, ROLLED_BACK MANUAL" "$rc $(jr 'd["result"]["switch"]["status"]') $(jr 'd["result"]["switch"]["rollback_reason"]')" "0 ROLLED_BACK MANUAL"
check "TC-UPG-036: R1-R7 within 60 s ($dt s)" test "$dt" -le 60
assert_eq "TC-UPG-036: binding back on PHP $OLD" "$(binding)" "$OLDSOCK"
assert_eq "command.name migrate, subcommand rollback (alias rollback-site)" "$(jr '(d["command"]["name"], d["command"]["subcommand"])')" "('migrate', 'rollback')"
check "rollback-site --json valid against qp.migrate/1" schema_ok "$J"
check "rollback-site keeps the target pool (no --purge-pool)" test -f "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
qp rollback-site shop.test --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "second rollback-site: nothing to roll back -> exit 2" "$rc" 2

# --- automatic rollback for each criterion (TC-UPG-031..033, TC-UPG-101, TC-UPG-103) ---------------------------------
for c in noreload:HC-C0 404:HC-C1 500:HC-C2 timeout:HC-C3 big:HC-C4 forbid:HC-C5 slow:HC-C6 fatallog:HC-C7 warn:HC-C8 crash:HC-C9; do
  m=${c%%:*}; crit=${c#*:}
  if [ "$m" = noreload ]; then set_mode ok; touch "$T/noreload"; else set_mode "$m"; fi
  sw; rc=$?; rm -f "$T/noreload"
  assert_eq "TC-UPG-033 $crit ($m): ROLLED_BACK, exit 1" "$rc $(jr 'd["result"]["switch"]["status"]')" "1 ROLLED_BACK"
  assert_eq "TC-UPG-033 $crit ($m): rollback_reason" "$(jr 'd["result"]["switch"]["rollback_reason"]')" "$crit"
  assert_contains "TC-UPG-101 $crit ($m): violation listed in hc" "$(jr '[v["criterion"] for v in d["result"]["hc"]["violations"]]')" "'$crit'"
  assert_eq "TC-UPG-033 $crit ($m): ERR-SCN-500-01" "$(jr 'd["errors"][-1]["code"]')" ERR-SCN-500-01
  assert_eq "TC-UPG-033 $crit ($m): binding back on PHP $OLD" "$(binding)" "$OLDSOCK"
  assert_eq "TC-UPG-033 $crit ($m): home page answers 200 again" \
    "$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' --resolve shop.test:18080:127.0.0.1 'http://shop.test:18080/?qp_hc=t')" 200
done
check "rolled-back switch --json valid against qp.migrate/1" schema_ok "$J"

# --- --no-auto-rollback -> HC_FAILED_KEPT (TC-UPG-034, BR-SCN-010), then rollback-site and ack -------------------------
set_mode 500
qp migrate switch shop.test --target "$NEW" --no-plan --reason "$REASON" --no-auto-rollback --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-034: --no-auto-rollback keeps the site: HC_FAILED_KEPT, exit 1, ERR-HC-500-01" \
  "$rc $(jr 'd["result"]["switch"]["status"]') $(jr 'd["errors"][-1]["code"]')" "1 HC_FAILED_KEPT ERR-HC-500-01"
assert_eq "TC-UPG-034: binding stays on the target" "$(binding)" "$NEWSOCK"
RK=$(jr 'd["result"]["run_id"]')
qp rollback-site shop.test "$RK" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "rollback-site of the HC_FAILED_KEPT run" "$rc $(jr 'd["result"]["switch"]["status"]') $(binding)" "0 ROLLED_BACK $OLDSOCK"
qp migrate ack "$RK" --reason "checked the 500 of the target, code fixed" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-022: ack of a ROLLED_BACK run" "$rc $(jr 'd["result"]["acknowledgement"]["status"]') $(jr 'd["result"]["acknowledgement"]["switch_lock_released"]')" "0 ROLLED_BACK False"
assert_eq "ack: next_allowed_sites = the site (no plan)" "$(jr 'd["result"]["acknowledgement"]["next_allowed_sites"]')" "['shop.test']"
check "ack --json valid against qp.migrate/1" schema_ok "$J"
qp migrate ack "$RK" --reason "checked the 500 of the target, code fixed" --json >"$J" 2>/dev/null; rc=$?
assert_eq "second ack -> ERR-UPG-409-04" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-409-04"

# --- ROLLBACK_FAILED locks every switch until acknowledged (TC-UPG-035, ERR-UPG-423-01) --------------------------
set_mode 500; touch "$T/rbfail"
sw; rc=$?
assert_eq "TC-UPG-035: restored config invalid -> ROLLBACK_FAILED, exit 2, ERR-HC-500-02" \
  "$rc $(jr 'd["result"]["switch"]["status"]') $(jr 'd["errors"][-1]["code"]')" "2 ROLLBACK_FAILED ERR-HC-500-02"
RF=$(jr 'd["result"]["run_id"]')
rm -f "$T/rbfail"; set_mode ok
qp migrate switch blog.test --target "$NEW" --no-plan --reason "$REASON" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "ERR-UPG-423-01: no switch on the server until the failure is acknowledged" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-UPG-423-01"
qp migrate status --json >"$J" 2>/dev/null
assert_eq "status: locked_after_rollback_failed" "$(jr 'd["result"]["locked_after_rollback_failed"]')" True
/usr/sbin/nginx -s reload; sleep 1                                     # the operator repairs the site by hand
qp migrate ack "$RF" --reason "restored nginx by hand after the failed rollback" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-022: ack of ROLLBACK_FAILED releases the lock" "$rc $(jr 'd["result"]["acknowledgement"]["switch_lock_released"]')" "0 True"
assert_eq "ack: binding_now read again (PHP $OLD)" "$(jr 'd["result"]["acknowledgement"]["binding_now"]["current_branch"]')" "$OLD"

# --- ABORTED at C2-C8: the site is not changed (TC-UPG-011, TC-UPG-027/028) ------------------------------------------
abort_case() { # abort_case DESC EXPECTED_CODE ARGS...
  local desc=$1 code=$2; shift 2
  local fp; fp=$(find /etc/nginx -type f -exec sha256sum {} + | sort)
  qp migrate switch shop.test --no-plan --reason "$REASON" --yes --json "$@" >"$J" 2>/dev/null; local rc=$?
  assert_eq "$desc: ABORTED, exit 2, $code" "$rc $(jr 'd["result"]["switch"]["status"]') $(jr '[e["code"] for e in d["errors"]][0]')" "2 ABORTED $code"
  assert_eq "$desc: Nginx files unchanged" "$(find /etc/nginx -type f -exec sha256sum {} + | sort)" "$fp"
}
set_mode ok
other=8.9; abort_case "C2 target not installed" ERR-ENV-412-01 --target "$other"
sed -i '1s/.*/; qp-site-id = other.test/' "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
abort_case "C3 pool name collision" ERR-ENV-500-01 --target "$NEW"
check "C3: the foreign pool file is left alone" grep -q '^; qp-site-id = other.test$' "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
rm -f "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"; PATH="$STUB:$PATH" service "php$NEW-fpm" reload >/dev/null 2>&1
set_mode probe; abort_case "C4 FastCGI probe (TC-UPG-028)" ERR-HC-424-01 --target "$NEW"
check "C4: the pool created by the aborted run was removed" test ! -e "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
set_mode oldbad; abort_case "C5 unstable baseline (TC-UPG-025)" ERR-HC-412-02 --target "$NEW"
set_mode ok; touch "$T/failtest"; abort_case "C8 nginx -t fails after the edit" ERR-ENV-500-02 --target "$NEW"; rm -f "$T/failtest"
assert_eq "C8: binding restored" "$(binding)" "$OLDSOCK"

# --- hc-urls, healthcheck --baseline-only (FR-UPG-HC-001/003, TC-UPG-024, TC-UPG-026) ---------------------------------
qp migrate hc-urls shop.test --set /about.php --set "http://evil.test/" --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-026: URL of another host refused" "$rc $(jr 'd["errors"][0]["code"]')" "2 ERR-CLI-400-01"
qp migrate hc-urls shop.test --set /about.php --set "http://www.shop.test:18080/about.php?x=1 expect=200" --json >"$J" 2>/dev/null; rc=$?
assert_eq "hc-urls: 2 URLs declared" "$rc $(jr 'len(d["result"]["hc_urls"])')" "0 2"
check "hc-urls: sites.d file names the site" grep -q '^# qp-site-id = shop.test$' /etc/php-quickpatch/sites.d/shop.test.conf
fp=$(fingerprint /etc/nginx /etc/php)
qp migrate healthcheck shop.test --baseline-only --json >"$J" 2>/dev/null; rc=$?
assert_eq "TC-UPG-024: baseline of 3 URLs (home + 2 declared)" "$rc $(jr '[u["code_b"] for u in d["result"]["baseline"]["per_url"]]')" "0 ['200', '200', '200']"
assert_eq "healthcheck --baseline-only changes nothing" "$(fingerprint /etc/nginx /etc/php)" "$fp"
check "healthcheck --json valid against qp.migrate/1" schema_ok "$J"

# --- BR-ENV-013: other write commands wait for the site lock of a running window ----------------------------------
set_mode ok; touch "$T/slowwin"
( sw ) & bg=$!
for _ in $(seq 1 60); do grep -q $'\tHC_RUNNING\t' "$SD/switches/index.tsv" 2>/dev/null && [ "$(tail -n1 "$SD/switches/index.tsv" | cut -f6)" = HC_RUNNING ] && break; sleep 0.5; done
qp migrate switch blog.test --target "$NEW" --no-plan --reason "$REASON" --yes --json >"$T/j2" 2>/dev/null; rc=$?
assert_eq "BR-ENV-013: switch of another site during the window -> ERR-ENV-409-01" "$rc $(json_get "$T/j2" 'd["errors"][0]["code"]')" "2 ERR-ENV-409-01"
assert_contains "ERR-ENV-409-01 names the remaining seconds" "$(json_get "$T/j2" 'd["errors"][0]["message"]')" "wait"
qp fix --only php --yes --json >"$T/j2" 2>/dev/null; rc=$?
assert_eq "BR-ENV-013: fix during the window -> ERR-ENV-409-01" "$rc $(json_get "$T/j2" '[e["code"] for e in d["errors"]][0]')" "2 ERR-ENV-409-01"
qp migrate status --json >"$T/j2" 2>/dev/null; rc=$?
assert_eq "status (read) runs during the window" "$rc $(json_get "$T/j2" 'd["result"]["switches"][-1]["status"]')" "0 HC_RUNNING"
wait "$bg"; rm -f "$T/slowwin"
assert_eq "the switch in the background ends PASSED" "$(jr 'd["result"]["switch"]["status"]')" PASSED
R2=$(jr 'd["result"]["run_id"]')
qp migrate ack "$R2" --reason "a PASSED run needs no acknowledgement" --json >"$T/j2" 2>/dev/null; rc=$?
assert_eq "ack of a PASSED run -> ERR-UPG-409-04" "$rc $(json_get "$T/j2" 'd["errors"][0]["code"]')" "2 ERR-UPG-409-04"

# --- FR-SCAN-DRF-001: binding changed outside the tool after a PASSED switch (TC-SCAN-013/014) ------------------------
qp scan --only sites --offline --json >"$J" 2>/dev/null
assert_eq "TC-SCAN-014: no drift right after the switch" "$(jr 'd["result"]["drift_warnings"]')" "[]"
sed -i "s#fastcgi_pass unix:/run/php/qp-shop.test-$NEW.sock;#fastcgi_pass unix:/run/php/php$OLD-fpm.sock;#" /etc/nginx/sites-enabled/shop.test.conf
qp scan --only sites --offline --json >"$J" 2>/dev/null
assert_eq "TC-SCAN-013: hand edit back to $OLD -> drift warning ERR-SCAN-409-01" \
  "$(jr '[(w["site_id"], w["code"]) for w in d["result"]["drift_warnings"]]')" "[('shop.test', 'ERR-SCAN-409-01')]"
assert_contains "drift warning names expected and actual" "$(jr 'd["result"]["drift_warnings"][0]["expected"] + " / " + d["result"]["drift_warnings"][0]["actual"]')" \
  "PHP $NEW ($NEWSOCK) / PHP $OLD ($OLDSOCK)"
check "scan with drift_warnings valid against qp.scan/1" schema_ok "$J"

# --- rollback <run_id> of a switch run = rollback-site --purge-pool (T-SW-15) -------------------------------------------
qp rollback "$R2" --yes --json >"$J" 2>/dev/null; rc=$?
assert_eq "rollback RUN_ID of a switch run: ROLLED_BACK" "$rc $(jr 'd["result"]["switch"]["status"]') $(binding)" "0 ROLLED_BACK $OLDSOCK"
check "rollback RUN_ID purges the target pool" test ! -e "/etc/php/$NEW/fpm/pool.d/qp-shop.test.conf"
assert_eq "index.tsv: last state of $R2" "$(idx_status "$R2")" ROLLED_BACK

# --- audit chain covers every write -------------------------------------------------------------------------
assert_eq "audit: intents of switch, rollback, ack, hc-urls" \
  "$(grep -o '"action":"[a-z_]*"' "$SD"/audit/*.jsonl 2>/dev/null | sort -u | cut -d'"' -f4 | grep -E '^(migrate_switch|migrate_rollback|switch_ack|site_set_hc_urls)$' | paste -sd' ')" \
  "migrate_rollback migrate_switch site_set_hc_urls switch_ack"
t_done
