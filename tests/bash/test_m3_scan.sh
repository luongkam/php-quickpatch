#!/usr/bin/env bash
# M3 — catalog, scenario assignment, lock, environment/playbooks, site
# inventory, plan deadlines and mitigation rules seen by scan/fix
# (FR-SCN-CAT-001, FR-SCN-CLS-001/002, FR-SCN-LIFE-001, FR-SCN-LOCK-001,
# FR-SCN-ENV-001, FR-SCAN-ENV-001, FR-SCAN-MAP-001, FR-ASMT-RANK-001,
# FR-PLAN-DL-001, FR-PTCH-MIT-001; TC-SCN-001..004, 008..010, 014, 016,
# TC-SCAN-002, 003, TC-ASMT-011, 013, TC-PTCH-005..007, FR §15.3 case 11).
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
# shellcheck source=tests/bash/stubs.sh
. "$(dirname "$0")/stubs.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'feeds_cleanup; umount /etc 2>/dev/null; rm -rf "$T"' EXIT
# shellcheck disable=SC2034  # FX is read by the stubs
STUB=$T/stub CALLS=$T/calls FX=$T/fx; stubs_init; dpkg_stubs; curl_stub; apt_stub
SD=/var/lib/php-quickpatch; CAT=$QP_ROOT/share/php-quickpatch/catalog
feeds_fixture
J=$T/out.json
qp() { PATH="$STUB:$PATH" bash "$QP" "$@"; }
rt_of() { json_get "$J" "[(r['scenario_ids'], r['locked'], r['lifecycle_status']) for r in d['result']['runtimes'] if r['bin'] == '$1'][0]"; }

# --- FR-SCN-CAT-001: catalog built from the scenario documents ----------------
python3 "$QP_ROOT/tools/build-catalog.py" --out "$T/cat" >/dev/null
assert_eq "catalog: tools/build-catalog.py reproduces the packaged catalog" "$(cat "$T/cat/SHA256SUMS")" "$(cat "$CAT/SHA256SUMS")"
check "catalog: SHA256SUMS matches every file" bash -c "cd '$CAT' && sha256sum -c --status --strict SHA256SUMS"
assert_eq "catalog: 28 scenarios, 399 PHP + 224 Node.js items" \
  "$(json_get "$CAT/catalog.json" '[d["counts"][k] for k in ("scenarios", "php_items", "node_items")]')" "[28, 399, 224]"
doc_ids=$(grep -ho '^| `CHK-[A-Z]*-[0-9]*-[0-9]*`' "$QP_ROOT"/docs/php-quickpatch/srs/version-scenarios-*.md | tr -d '|` ' | sort -u)
cat_ids=$(json_get "$CAT/checklists.json" '"\n".join(sorted(i["chk_id"] for i in d["items"]))')
assert_eq "catalog: every CHK-* row of the documents is in checklists.json" "$cat_ids" "$doc_ids"
assert_eq "TC-SCN-005 KQ3: no lifecycle_status/priority stored in scenarios.json" "$(grep -c '"lifecycle_status"\|"priority"' "$CAT/scenarios.json")" 0
check "catalog: scenarios.json has one record per line (read by Bash)" test "$(grep -c '"scenario_id":' "$CAT/scenarios.json")" -eq 28

# --- FR-SCN-CLS-001 / BR-SCN-040 table 4.1 + ranges; FR-SCN-CLS-002 / BR-SCN-020 -
B=$T/bin; P=$T/www; mkdir -p "$P"
php_cases="8.6.0RC4:SCN-PHP-014,SCN-PHP-016:True:PRE_RELEASE 8.6.0-dev:SCN-PHP-014,SCN-PHP-016:True:PRE_RELEASE
8.4.28-dev:SCN-PHP-012,SCN-PHP-016:True:PRE_RELEASE 8.5.13RC1:SCN-PHP-013,SCN-PHP-016:True:PRE_RELEASE
8.4.27:SCN-PHP-012,SCN-PHP-015:False:ACTIVE 8.1.2-1ubuntu2.24:SCN-PHP-009,SCN-PHP-015:False:EOL
8.7.0-dev:SCN-PHP-005,SCN-PHP-016:True:UNKNOWN 6.0.0-dev:SCN-PHP-005,SCN-PHP-016:True:UNKNOWN
8.4.27custom:SCN-PHP-005,SCN-PHP-016:True:UNKNOWN 10.0.0:SCN-PHP-005,SCN-PHP-016:True:UNKNOWN
4.4.9:SCN-PHP-001,SCN-PHP-016:False:EOL 5.2.17:SCN-PHP-002,SCN-PHP-016:False:EOL 5.4.45:SCN-PHP-003,SCN-PHP-016:False:EOL
5.6.40:SCN-PHP-004,SCN-PHP-016:False:EOL 7.1.33:SCN-PHP-006,SCN-PHP-016:False:EOL 7.4.33:SCN-PHP-007,SCN-PHP-015:False:EOL
8.0.30:SCN-PHP-008,SCN-PHP-016:False:EOL 8.2.34:SCN-PHP-010,SCN-PHP-015:False:SECURITY_ONLY
8.3.6:SCN-PHP-011,SCN-PHP-015:False:SECURITY_ONLY"
bins=()
for c in $php_cases; do
  v=${c%%:*}; fake_php "$B/php-$v/bin/php" "$v"; bins+=("$B/php-$v/bin/php")
  case $v in 8.4.27|8.1.2-1ubuntu2.24|7.4.33|8.2.34|8.3.6) dpkg_owns "$B/php-$v/bin/php" "php${v:0:3}-cli" "$v-1" ;; esac
done
QP_PHP_BINS="${bins[*]}" qp scan --offline --only php --json --path "$P" >"$J" 2>/dev/null
for c in $php_cases; do
  IFS=: read -r v scn locked lc <<<"$c"
  assert_eq "TC-SCN-004 PHP $v -> $scn locked=$locked $lc" "$(rt_of "$B/php-$v/bin/php")" "($(python3 -c "print(repr('$scn'.split(',')))"), $locked, '$lc')"
done
check "TC-SCN-001/TC-SCN-004 output valid against schema" schema_ok "$J"
assert_eq "TC-SCN-001 KQ2: exactly one VERSION scenario per runtime" \
  "$(json_get "$J" 'sorted({sum(1 for s in r["scenario_ids"] if s not in ("SCN-PHP-015","SCN-PHP-016")) for r in d["result"]["runtimes"]})')" "[1]"
assert_eq "TC-SCN-003 KQ2: ERR-SCN-422-01 message for 6.0.0-dev" \
  "$(json_get "$J" '[e["message"] for e in d["errors"] if e["code"]=="ERR-SCN-422-01" and "6.0.0-dev" in e["message"]][:1]')" \
  "[\"Unrecognized PHP ($B/php-6.0.0-dev/bin/php) version '6.0.0-dev'. Automation for this runtime is locked.\"]"
assert_eq "TC-SCN-003: locked runtime has lock_reason" "$(json_get "$J" "[r['lock_reason'] for r in d['result']['runtimes'] if r['version_raw']=='6.0.0-dev']")" "['scn.version.unrecognized']"
assert_eq "SCN §2.2: UNKNOWN version -> priority CRITICAL" "$(json_get "$J" "[r['priority'] for r in d['result']['runtimes'] if r['version_raw']=='8.4.27custom']")" "['CRITICAL']"
assert_eq "envelope: catalog_version of the packaged catalog" "$(json_get "$J" 'd["catalog_version"]')" "$(json_get "$CAT/catalog.json" 'd["catalog_version"]')"

# Node.js: version lines, overlays nvm / tarball / NodeSource / distro package.
N=$T/node; nbins=()
node_cases="v16.20.2:$N/a:SCN-NODE-001,SCN-NODE-010:False v18.20.8:$N/b:SCN-NODE-002,SCN-NODE-010:False
v20.20.2:$N/c:SCN-NODE-003,SCN-NODE-010:False v25.9.0:$N/d:SCN-NODE-004,SCN-NODE-010:False
v22.23.3:$T/home/dev/.nvm/versions/node/v22.23.3:SCN-NODE-005,SCN-NODE-009:False
v24.22.1:$N/ns:SCN-NODE-006,SCN-NODE-011:False v26.12.1:$N/deb:SCN-NODE-007,SCN-NODE-012:False
v27.0.0-nightly20261020ab12:$N/n:SCN-NODE-008,SCN-NODE-010:True v24.0.0-rc.1:$N/rc:SCN-NODE-008,SCN-NODE-010:True
v99.0.0:$N/u:SCN-NODE-008,SCN-NODE-010:True"
for c in $node_cases; do
  IFS=: read -r v pre _ _ <<<"$c"; fake_node "$pre" "${v#v}"; nbins+=("$pre/bin/node")
done
dpkg_owns "$N/ns/bin/node" nodejs "24.22.1-1nodesource1"; dpkg_owns "$N/deb/bin/node" nodejs-distro "26.12.1+dfsg-1"
rm -rf "$N/ns/lib" "$N/deb/lib"
QP_NODE_BINS="${nbins[*]}" qp scan --offline --only node --json --path "$P" >"$J" 2>/dev/null
for c in $node_cases; do
  IFS=: read -r v pre scn locked <<<"$c"
  assert_eq "TC-SCN-002/004 Node $v -> $scn locked=$locked" "$(json_get "$J" "[(r['scenario_ids'], r['locked']) for r in d['result']['runtimes'] if r['bin']=='$pre/bin/node'][0]")" \
    "($(python3 -c "print(repr('$scn'.split(',')))"), $locked)"
done
assert_eq "BR-SCN-020: nightly -> PRE_RELEASE, v99 -> UNKNOWN" \
  "$(json_get "$J" "[r['lifecycle_status'] for r in sorted(d['result']['runtimes'], key=lambda r: r['bin']) if r['locked']]")" "['PRE_RELEASE', 'PRE_RELEASE', 'UNKNOWN']"
assert_eq "§2.3 step 8: Node playbooks PB-015, PB-016, PB-014" \
  "$(json_get "$J" 'sorted(d["result"]["environment"]["pb_node"])')" "['PB-014', 'PB-015', 'PB-016']"
assert_eq "TC-SCN-005 KQ2: Node 24 MAINTENANCE_LTS, is_lts, EOL 2028-04-30" \
  "$(json_get "$J" "[(r['lifecycle_status'], r['is_lts'], r['eol_date']) for r in d['result']['runtimes'] if r['bin']=='$N/ns/bin/node']")" "[('MAINTENANCE_LTS', True, '2028-04-30')]"

# --- FR-SCN-LOCK-001 / TC-SCN-003 KQ3: fix skips every change on a locked runtime -
D6=$T/conf6; mkdir -p "$D6"; fake_php "$B/php6/bin/php" 6.0.0-dev "$D6"
: >"$CALLS"
QP_PHP_BINS="$B/php6/bin/php" qp fix --only php --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-SCN-003 KQ3: runtime_patch and mitigation SKIPPED (ERR-SCN-422-01)" \
  "$(json_get "$J" '[(a["kind"], a["status"], a["error_code"]) for a in d["result"]["actions"]]')" \
  "[('runtime_patch', 'skipped', 'ERR-SCN-422-01'), ('mitigation_add', 'skipped', 'ERR-SCN-422-01')]"
check "TC-SCN-003 KQ3: no package manager call, no mitigation file" bash -c "! grep -q '^apt-get' '$CALLS' && [ -z \"\$(ls -A '$D6')\" ]"

# --- FR-SCN-CAT-001: imported catalog (TC-SCN-008, 009, 010) --------------------
mkimport() { # mkimport VERSION: a valid catalog with that version in STATE_DIR/feeds/catalog
  rm -rf "$SD/feeds/catalog"; python3 "$QP_ROOT/tools/build-catalog.py" --version "$1" --out "$SD/feeds/catalog" >/dev/null
}
mkimport 2099.11.05-1
fake_php "$B/p82/bin/php" 8.2.34
QP_PHP_BINS="$B/p82/bin/php" qp scan --offline --only php --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-SCN-008 KQ1: newer imported catalog in use" "$(json_get "$J" 'd["catalog_version"]')" 2099.11.05-1
echo '{"tampered": true}' >>"$SD/feeds/catalog/checklists.json"
QP_PHP_BINS="$B/p82/bin/php" qp scan --offline --only php --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-SCN-009 KQ1: ERR-FEED-422-02" "$(json_get "$J" '[e["code"] for e in d["errors"] if e["code"].startswith("ERR-FEED")]')" "['ERR-FEED-422-02']"
assert_eq "TC-SCN-009 KQ2: the packaged catalog stays in use" "$(json_get "$J" 'd["catalog_version"]')" "$(json_get "$CAT/catalog.json" 'd["catalog_version"]')"
mkimport 2099.11.06-1
sed -i '0,/"actions"/s//"actionz"/' "$SD/feeds/catalog/playbooks.json"
(cd "$SD/feeds/catalog" && sha256sum scenarios.json checklists.json playbooks.json bc_rules.json mitigations.json framework_php.tsv catalog.json >SHA256SUMS)
QP_PHP_BINS="$B/p82/bin/php" qp scan --offline --only php --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-SCN-010 KQ1: catalog without playbook actions -> ERR-FEED-502-02" "$(json_get "$J" '[e["code"] for e in d["errors"] if e["code"].startswith("ERR-FEED")]')" "['ERR-FEED-502-02']"
assert_eq "TC-SCN-010 KQ1: catalog in use kept" "$(json_get "$J" 'd["catalog_version"]')" "$(json_get "$CAT/catalog.json" 'd["catalog_version"]')"
rm -rf "$SD/feeds/catalog"

# --- FR-SCN-ENV-001, site_key (sourced functions) --------------------------------
envj=$(bash -c '. "$1"; IN_CONTAINER=1 IS_ROOT=0 PANEL=cpanel PKG_MGR=apt; detect_playbooks >/dev/null 2>&1; env_after_runtimes >/dev/null; env_json; echo "$REPLY"' _ "$QP")
assert_eq "TC-SCN-014/016: restrictions not root + in container + panel" \
  "$(python3 -c 'import json,sys; print([r["code"] for r in json.loads(sys.argv[1])["restrictions"]])' "$envj")" \
  "['SCN-ENV-NOROOT', 'SCN-ENV-DOCKER', 'SCN-ENV-PANEL']"
assert_eq "TC-SCN-014 KQ1: message (QP_LANG=vi) 'không root: chỉ cấp dự án'" \
  "$(QP_LANG="vi" bash -c '. "$1"; IS_ROOT=0; detect_playbooks >/dev/null 2>&1; env_json; echo "$REPLY"' _ "$QP" | python3 -c 'import json,sys; print(json.load(sys.stdin)["restrictions"][0]["message"])')" \
  "không root: chỉ cấp dự án"
assert_eq "TC-SCAN-001 KQ1 (markers): cPanel -> PB-007 with evidence /usr/local/cpanel/cpanel" \
  "$(python3 -c 'import json,sys; e=json.loads(sys.argv[1]); print(e["pb_provider"], [x["signal"] for x in e["evidence"] if x["pb_id"]=="PB-007"])' "$envj")" \
  "PB-007 ['/usr/local/cpanel/cpanel']"
for p in plesk:PB-009 aapanel:PB-010 cyberpanel:PB-011 directadmin:PB-012; do
  assert_eq "§2.3 step 2: panel ${p%%:*} -> ${p##*:}" "$(bash -c '. "$1"; PANEL=$2; detect_playbooks >/dev/null 2>&1; env_after_runtimes >/dev/null; echo "$PB_PHP"' _ "$QP" "${p%%:*}")" "${p##*:}"
done
assert_eq "§4.4 site_key: shop.example.com, svc:proj/web, app:pm2:api" \
  "$(bash -c '. "$1"; for s in shop.example.com svc:proj/web app:pm2:api; do site_key "$s"; printf "%s " "$REPLY"; done' _ "$QP")" \
  "shop.example.com h_ffd400634466 h_40a670b5bf62 "
assert_eq "§6.3.1 site_key: 48 characters readable, 49 hashed" \
  "$(bash -c '. "$1"; site_key "$(printf "a%.0s" {1..48})"; a=$REPLY; site_key "$(printf "a%.0s" {1..49})"; echo "${#a} ${REPLY:0:2}"' _ "$QP")" "48 h_"

# --- TC-SCAN-002: no panel, no web server, PHP from no package -> PB-000 ---------
QP_PHP_BINS="$B/p82/bin/php" qp scan --offline --only php,sites --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-SCAN-002 KQ1: pb_provider PB-000" "$(json_get "$J" 'd["result"]["environment"]["pb_provider"]')" PB-000
assert_eq "TC-SCAN-002 KQ2: ERR-ENV-422-01 message" "$(json_get "$J" '[e["message"] for e in d["errors"] if e["code"]=="ERR-ENV-422-01"]')" \
  "['Cannot identify how PHP is installed and assigned to sites on this server.']"
assert_eq "TC-SCAN-002 KQ3: restriction PB-000 = mitigation only" "$(json_get "$J" '[r["code"] for r in d["result"]["environment"]["restrictions"]]')" "['SCN-ENV-UNKNOWN']"

# --- FR-SCAN-MAP-001: Nginx/Apache + FPM, mod_php (fake /etc in this namespace) ---
cp -a /etc "$T/etc" && mount --bind "$T/etc" /etc
mkdir -p /etc/php/8.2/fpm/pool.d /etc/php/8.4/fpm/pool.d /etc/nginx/sites-available /etc/apache2/sites-available \
  /etc/apache2/conf-enabled /etc/apache2/mods-enabled
printf '[www]\nuser = www-data\nlisten = /run/php/php8.2-fpm.sock\n' >/etc/php/8.2/fpm/pool.d/www.conf
printf '[www]\nuser = www-data\nlisten = 127.0.0.1:9084\nphp_admin_value[error_log] = /var/log/fpm84.log\n' >/etc/php/8.4/fpm/pool.d/www.conf
mkdir -p "$T/www/shop" "$T/www/blog"; chown nobody "$T/www/shop"
cat >"$T/nginx-T.txt" <<EOF
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# configuration file /etc/nginx/nginx.conf:
http {
    include /etc/nginx/sites-enabled/*;
}

# configuration file /etc/nginx/sites-enabled/shop.test.conf:
upstream php84 {
    server 127.0.0.1:9084;
}
server {
    listen 80;
    server_name shop.test www.shop.test;
    root $T/www/shop;
    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    }
}
server {
    listen 443 ssl;
    server_name shop.test;
    root $T/www/shop;
    location ~ \.php$ { fastcgi_pass unix:/run/php/php8.2-fpm.sock; }
}
server {
    listen 80;
    server_name blog.test;
    root $T/www/blog;
    error_log /var/log/nginx/blog.err;
    location ~ \.php$ {
        fastcgi_pass php84;
    }
}
server {
    listen 80;
    server_name static.test;
    root /var/www/static;
}
server {
    server_name inc.test;
    location ~ \.php$ {
        include snippets/qp-php82.conf;
    }
}

# configuration file /etc/nginx/snippets/qp-php82.conf:
fastcgi_pass unix:/run/php/php8.2-fpm.sock;
EOF
printf 'server {\n  server_name legacy.test;\n}\n' >/etc/nginx/sites-available/legacy.test
printf '<VirtualHost *:80>\n  ServerName shop.test\n</VirtualHost>\n' >/etc/apache2/sites-available/shop.test.conf
stub nginx "cat '$T/nginx-T.txt'"
stub pgrep '[ "$*" = "-f nginx: master" ] && exit 0; exit 1'
fake_php "$T/usr/bin/php8.2" 8.2.34; fake_php "$T/usr/bin/php8.4" 8.4.27
dpkg_owns "$T/usr/bin/php8.2" php8.2-cli 8.2.34-1; dpkg_owns "$T/usr/bin/php8.4" php8.4-cli 8.4.27-1
export QP_PHP_BINS="$T/usr/bin/php8.2 $T/usr/bin/php8.4"
qp scan --offline --only php,sites --json --path "$P" >"$J" 2>/dev/null
check "FR-SCAN-MAP-001 output valid against schema" schema_ok "$J"
site() { json_get "$J" "[s.get('$2') for s in d['result']['sites'] if s['site_id']=='$1']"; }
assert_eq "TC-SCAN-003 KQ1: shop.test nginx_fastcgi on 8.2 (PB-005)" "$(site shop.test binding_kind) $(site shop.test current_branch) $(site shop.test pb_id)" \
  "['nginx_fastcgi'] ['8.2'] ['PB-005']"
assert_eq "§6.2 step 5: 80 + 443 blocks of shop.test in binding_ref" "$(site shop.test binding_ref)" \
  "['/etc/nginx/sites-enabled/shop.test.conf:4,/etc/nginx/sites-enabled/shop.test.conf:10,/etc/nginx/sites-enabled/shop.test.conf:13,/etc/nginx/sites-enabled/shop.test.conf:17']"
assert_eq "§6.2: server names, owner from docroot, https health URL" "$(site shop.test server_names) $(site shop.test owner_user) $(site shop.test hc_urls)" \
  "[['shop.test', 'www.shop.test']] ['nobody'] [['https://shop.test/']]"
assert_eq "§6.2 step 2-3: upstream -> 127.0.0.1:9084 -> pool of 8.4, logs" "$(site blog.test runtime_endpoint) $(site blog.test current_branch) $(site blog.test log_sources)" \
  "['127.0.0.1:9084'] ['8.4'] [['/var/log/nginx/blog.err', '/var/log/fpm84.log']]"
assert_eq "§6.2 step 2: fastcgi_pass in an included snippet" "$(site inc.test current_branch)" "['8.2']"
assert_eq "§6.2: server block without PHP is not a site" "$(site static.test site_id)" "[]"
assert_eq "TC-SCAN-003 KQ1: Apache file not loaded -> evidence" \
  "$(json_get "$J" '[e["signal"] for e in d["result"]["environment"]["evidence"] if "Apache, not loaded" in e["signal"]]')" \
  "['site shop.test: /etc/apache2/sites-available/shop.test.conf (Apache, not loaded); Nginx binding used']"
assert_eq "TC-SCAN-003 KQ2: legacy.test -> ERR-ENV-422-02 issue, PB-000 unmapped" \
  "$(json_get "$J" '[i["code"] for i in d["issues"] if "legacy.test" in i["message"]]') $(site legacy.test binding_kind)" "['ERR-ENV-422-02'] ['unmapped']"
assert_eq "FR-SCAN-RT-001: runtime.site_ids from the inventory" \
  "$(json_get "$J" "[r['site_ids'] for r in d['result']['runtimes'] if r['bin']=='$T/usr/bin/php8.2']")" "[['shop.test', 'inc.test']]"
assert_eq "§2.3: provider PB-001, binding PB-005" "$(json_get "$J" '(d["result"]["environment"]["pb_provider"], d["result"]["environment"]["pb_bindings"])')" "('PB-001', ['PB-005'])"
fp1=$(json_get "$J" 'd["result"]["scan_fingerprint"]')
sed -i 's#fastcgi_pass php84;#fastcgi_pass unix:/run/php/php8.2-fpm.sock;#' "$T/nginx-T.txt"
qp scan --offline --only php,sites --json --path "$P" >"$J" 2>/dev/null
check "FR-PLAN-GEN-001: scan_fingerprint changes with a site binding" test "$fp1" != "$(json_get "$J" 'd["result"]["scan_fingerprint"]')"
assert_eq "state/last-scan.json written, mode 0600" "$(stat -c %a "$SD/state/last-scan.json") $(json_get "$SD/state/last-scan.json" 'd["schema"]')" "600 qp.scan/1"

# Apache: SetHandler in the vhost, global php8.4-fpm.conf, mod_php.
stub pgrep '[ "$*" = "-x apache2" ] && exit 0; exit 1'
cat >/etc/apache2/sites-available/a.conf <<'EOF'
<VirtualHost *:80>
  ServerName a.test
  ServerAlias www.a.test
  DocumentRoot /var/www/a
  <FilesMatch ".+\.php$">
    SetHandler "proxy:unix:/run/php/php8.2-fpm.sock|fcgi://localhost"
  </FilesMatch>
</VirtualHost>
<VirtualHost *:80>
  ServerName b.test
  DocumentRoot /var/www/b
</VirtualHost>
EOF
printf '<FilesMatch ".+\\.ph(ar|p|tml)$">\n    SetHandler "proxy:unix:/run/php/php8.2-fpm.sock|fcgi://localhost"\n</FilesMatch>\n' >/etc/apache2/conf-enabled/php8.2-fpm.conf
stub apachectl 'case "$1" in -M) echo " proxy_fcgi_module (shared)";; -S) printf "VirtualHost configuration:\n*:80                   is a NameVirtualHost\n         default server a.test (/etc/apache2/sites-available/a.conf:1)\n         port 80 namevhost a.test (/etc/apache2/sites-available/a.conf:1)\n         port 80 namevhost b.test (/etc/apache2/sites-available/a.conf:9)\n";; esac'
qp scan --offline --only php,sites --json --path "$P" >"$J" 2>/dev/null
assert_eq "PB-005 Apache: SetHandler in vhost" "$(site a.test binding_kind) $(site a.test runtime_endpoint) $(site a.test server_names)" \
  "['apache_proxy_fcgi'] ['unix:/run/php/php8.2-fpm.sock'] [['a.test', 'www.a.test']]"
assert_eq "PB-005 Apache: global conf-enabled/php8.2-fpm.conf applies to b.test" "$(site b.test binding_ref)" \
  "['/etc/apache2/sites-available/a.conf:9,/etc/apache2/conf-enabled/php8.2-fpm.conf:2']"
rm /etc/apache2/conf-enabled/php8.2-fpm.conf; touch /etc/apache2/mods-enabled/php8.2.load
stub apachectl 'case "$1" in -M) echo " php_module (shared)";; -S) printf "         port 80 namevhost b.test (/etc/apache2/sites-available/a.conf:9)\n";; esac'
qp scan --offline --only php,sites --json --path "$P" >"$J" 2>/dev/null
assert_eq "PB-006: mod_php site (apache_mod_php, branch from mods-enabled)" "$(site b.test binding_kind) $(site b.test pb_id) $(site b.test current_branch)" \
  "['apache_mod_php'] ['PB-006'] ['8.2']"
umount /etc; rm -f "$STUB/pgrep" "$STUB/apachectl" "$STUB/nginx"; unset QP_PHP_BINS

# --- FR-ASMT-RANK-001: reason codes, order by R then object_ref (TC-ASMT-011/013) --
fake_php "$B/r1/bin/php" 7.4.33; fake_php "$B/r2/bin/php" 8.2.34; fake_php "$B/r3/bin/php" 8.5.12
QP_PHP_BINS="$B/r1/bin/php $B/r2/bin/php $B/r3/bin/php" qp scan --offline --only php --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-ASMT-011: ranking by R desc" "$(json_get "$J" '[x["R"] for x in d["result"]["ranking"]] == sorted([x["R"] for x in d["result"]["ranking"]], reverse=True)')" True
assert_eq "TC-ASMT-011 KQ2: reason codes from the spec enum, never empty" \
  "$(json_get "$J" 'all(x["reason_codes"] and set(x["reason_codes"]) <= {"KEV","CVSS_GE_9","EOL","CVSS_7_TO_8_9","EOL_LE_90D","OTHER"} for x in d["result"]["ranking"])')" True
assert_eq "BR-FEED-040: risk.components S_* as numbers, score = R" \
  "$(json_get "$J" "[(sorted(r['risk']['components']), r['risk']['score'] == r['risk']['R'], type(r['risk']['components']['S_cvss']).__name__) for r in d['result']['runtimes'] if r['version']=='8.2.34'][0]")" \
  "(['R_raw', 'S_cnt', 'S_cvss', 'S_eol', 'S_kev', 'S_life', 'floor'], True, 'float')"
py=$(python3 -I "$QP_ROOT/share/php-quickpatch/qp-feeds.py" --script "$QP" risk --product php --version 7.4.33 --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["risk"]["components"])')
assert_eq "NFR-CMP-005: Bash and Python components equal (7.4.33)" "$(json_get "$J" "[r['risk']['components'] for r in d['result']['runtimes'] if r['version']=='7.4.33'][0]")" "$py"

# --- FR-PLAN-DL-001: plan_deadlines (EOL - 30 days, SECURITY_ONLY or <= 90 days) --
dl=$(date -u -d '2026-12-31 -30 days' +%F); left=$(( ($(date -u -d "$dl" +%s) - $(date -u -d "$(date -u +%F)" +%s)) / 86400 ))
assert_eq "TC-PLAN-024: PHP 8.2 deadline 2026-12-01, days_left, no plan yet" \
  "$(json_get "$J" "[(x['deadline'], x['days_left'], x['plan_status']) for x in d['result']['plan_deadlines']]")" "[('$dl', $left, None)]"

# --- FR-PTCH-MIT-001: mitigations.json rules, qp-rules header, (a)(b)(c) ----------
CA=$T/ca; CB=$T/cb; CC=$T/cc; mkdir -p "$CA" "$CB" "$CC"
fake_php "$B/m/bin/php" 8.2.34 "$CA:$CB:$CC"
dpkg_owns "$B/m/bin/php" php8.2-cli 8.2.34-1
body='; php-quickpatch interim mitigation (CVE-2026-109618 CVE-2026-109619). It only reduces exposure: upgrade PHP, then delete this file.
session.upload_progress.enabled = 0'
printf '; qp-rules=MIT-PHP-001; sha256=%s\n%s\n' "$(printf '%s\n' "$body" | sha256sum | cut -c1-64)" "$body" >"$CA/zz-php-quickpatch-mitigation.ini"
printf '; Added by php-quickpatch 2026-10-21: interim PHP2Shell mitigation\nsession.upload_progress.enabled = 0\nmemory_limit = -1\n' >"$CB/zz-php-quickpatch-mitigation.ini"
printf '; qp-rules=MIT-PHP-001; sha256=%s\n%s\nopcache.enable = 0\n' "$(printf '%s\n' "$body" | sha256sum | cut -c1-64)" "$body" >"$CC/zz-php-quickpatch-mitigation.ini"
before=$(sha256sum "$CA"/*.ini "$CB"/*.ini "$CC"/*.ini | cut -c1-64)
QP_PHP_BINS="$B/m/bin/php" qp fix --only php --no-restart --json --path "$P" >"$J" 2>/dev/null
run1=$(json_get "$J" 'd["result"]["run_id"]')
assert_eq "FR §15.3 case 11: A, B rewritten with qp-rules=MIT-PHP-001,MIT-PHP-002" \
  "$(head -n1 "$CA/zz-php-quickpatch-mitigation.ini" | cut -c1-35) $(head -n1 "$CB/zz-php-quickpatch-mitigation.ini" | cut -c1-35)" \
  "; qp-rules=MIT-PHP-001,MIT-PHP-002; ; qp-rules=MIT-PHP-001,MIT-PHP-002;"
assert_eq "FR §15.3 case 11: one copy line per rewritten file" "$(grep -c "^copy.*zz-php-quickpatch-mitigation.ini" "$SD/backups/$run1/manifest")" 2
assert_eq "FR §15.3 case 11: C (edited by hand) unchanged" "$(sha256sum "$CC/zz-php-quickpatch-mitigation.ini" | cut -c1-64)" "$(sed -n 3p <<<"$before")"
assert_contains "FR §15.3 case 11: C -> high issue listing memory_limit" "$(json_get "$J" '[i["severity"] + " " + i["message"] for i in d["issues"] if "modified by hand" in i["message"]]')" "high"
assert_contains "FR §15.3 case 11: missing directive named" "$(json_get "$J" '[i["message"] for i in d["issues"] if "modified by hand" in i["message"]]')" "memory_limit = -1"
assert_eq "FR-PTCH-MIT-001: mitigations[] actions" "$(json_get "$J" 'sorted(m["action"] for m in d["result"]["mitigations"])')" "['kept', 'rewritten', 'rewritten']"
QP_PHP_BINS="$B/m/bin/php" qp fix --only php --no-restart --json --path "$P" >"$J" 2>/dev/null
run2=$(json_get "$J" 'd["result"]["run_id"]')
assert_eq "FR §15.3 case 11 run 2: A, B unchanged" "$(json_get "$J" 'sorted(m["action"] for m in d["result"]["mitigations"])')" "['kept', 'unchanged', 'unchanged']"
assert_eq "FR §15.3 case 11 run 2: no manifest line for mitigation files" "$(cat "$SD/backups/$run2/manifest" 2>/dev/null | grep -c 'zz-php-quickpatch')" 0
qp rollback "$run1" >/dev/null 2>&1
assert_eq "FR §15.3 case 11: rollback of run 1 restores A, B" "$(sha256sum "$CA"/*.ini "$CB"/*.ini "$CC"/*.ini | cut -c1-64)" "$before"
rm -f "$CA"/*.ini "$CB"/*.ini "$CC"/*.ini
QP_PHP_BINS="$B/m/bin/php" qp fix --only php --no-restart --no-memlimit --dry-run --json --path "$P" >"$J" 2>/dev/null
assert_eq "TC-PTCH-006 --no-memlimit dry-run: 3 writes planned, no file" "$(json_get "$J" '[a["status"] for a in d["result"]["actions"] if a["kind"]=="mitigation_add"]') $(ls "$CA" | wc -l)" "['planned', 'planned', 'planned'] 0"
fake_php "$B/m85/bin/php" 8.5.11 "$CA"
QP_PHP_BINS="$B/m85/bin/php" qp fix --only php --no-restart --json --path "$P" >/dev/null 2>&1
assert_eq "TC-SCN-106 KQ4: 8.5 mitigation has 3 directives incl. fatal_error_backtraces" \
  "$(grep -v '^;' "$CA/zz-php-quickpatch-mitigation.ini" | tr '\n' '|')" "session.upload_progress.enabled = 0|memory_limit = -1|fatal_error_backtraces = 0|"

# --- FR-SCN-CAT-001: the catalog travels in snapshots and is imported with them ---
qp feeds export --out "$T/snap.tar.gz" >/dev/null 2>&1
assert_eq "feeds export: catalog/ with its SHA256SUMS in the archive" "$(tar -tzf "$T/snap.tar.gz" | grep -c '^catalog/')" 8
mkdir "$T/x" && tar -xzf "$T/snap.tar.gz" -C "$T/x" && python3 - "$T/x" <<'PY'
import hashlib, json, os, sys
d = os.path.join(sys.argv[1], "catalog")
p = os.path.join(d, "catalog.json"); m = json.load(open(p)); m["catalog_version"] = "2099.12.31-1"; json.dump(m, open(p, "w"))
names = ["scenarios.json", "checklists.json", "playbooks.json", "bc_rules.json", "mitigations.json", "framework_php.tsv", "catalog.json"]
open(os.path.join(d, "SHA256SUMS"), "w").write("".join("%s  %s\n" % (hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest(), n) for n in names))
PY
(cd "$T/x" && tar -czf "$T/snap2.tar.gz" manifest.json SHA256SUMS bundle catalog)
qp feeds import "$T/snap2.tar.gz" --sha256 "$(sha256sum "$T/snap2.tar.gz" | cut -c1-64)" --force --yes >/dev/null 2>&1
assert_eq "TC-SCN-008: catalog of an imported snapshot installed in feeds/catalog" "$(json_get "$SD/feeds/catalog/catalog.json" 'd["catalog_version"]')" 2099.12.31-1
rm -rf "$SD/feeds/catalog"

t_done
