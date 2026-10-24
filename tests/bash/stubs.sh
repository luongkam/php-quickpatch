# shellcheck shell=bash
# Fake system commands for the Bash tests. Every stub appends one line
# "<name> <args>" to $CALLS so tests can assert what would have run.
# Usage: STUB=<dir> CALLS=<file> FX=<fixture dir>; stubs_init

stubs_init() {
  mkdir -p "$STUB" "$FX/state"; : >"$CALLS"
}

# stub NAME [BODY]: create $STUB/NAME that records its call, then runs BODY
# (a shell snippet; "$@" are the arguments). Default BODY: exit 0.
stub() {
  local name=$1 body=${2:-exit 0}
  cat >"$STUB/$name" <<EOF
#!/usr/bin/env bash
printf '%s %s\n' "$name" "\$*" >>"$CALLS"
FX="$FX"
$body
EOF
  chmod +x "$STUB/$name"
}

# fake_php PATH VERSION [SCAN_DIRS] [MODULES]: a PHP CLI double. The version
# lives in $FX/state/<sha>.ver so an apt-get stub can "upgrade" it.
fake_php() {
  local bin=$1 ver=$2 scan=${3:-} mods=${4:-"Core date json mbstring"} key
  key=$(printf '%s' "$bin" | sha1sum | cut -c1-12)
  mkdir -p "${bin%/*}"; printf '%s\n' "$ver" >"$FX/state/$key.ver"
  cat >"$bin" <<EOF
#!/usr/bin/env bash
case "\$*" in
  *PHP_VERSION*) cat "$FX/state/$key.ver" | tr -d '\n' ;;
  --ini) echo "Configuration File (php.ini) Path: /etc"; echo "Scan for additional .ini files in: ${scan:-(none)}" ;;
  -m) echo "[PHP Modules]"; for m in $mods; do echo "\$m"; done; echo; echo "[Zend Modules]" ;;
  *) exit 0 ;;
esac
EOF
  chmod +x "$bin"
}
php_ver_file() { printf '%s/state/%s.ver' "$FX" "$(printf '%s' "$1" | sha1sum | cut -c1-12)"; }

# fake_node PREFIX VERSION [ABI]: a Node.js double at PREFIX/bin/node.
fake_node() {
  local prefix=$1 ver=$2 abi=${3:-127}
  mkdir -p "$prefix/bin" "$prefix/lib/node_modules/npm"
  printf '{\n  "name": "npm",\n  "version": "10.9.0"\n}\n' >"$prefix/lib/node_modules/npm/package.json"
  cat >"$prefix/bin/node" <<EOF
#!/usr/bin/env bash
case "\$*" in
  -v|--version) echo "v$ver" ;;
  *process.versions.modules*) echo "$abi" ;;
esac
EOF
  chmod +x "$prefix/bin/node"
}

# dpkg_owns BIN PKG VERSION [GROUP_PKGS...]: make the dpkg stubs report that
# PKG owns BIN, and that GROUP_PKGS are installed.
dpkg_owns() {
  local bin=$1 pkg=$2 ver=$3; shift 3
  printf '%s\t%s\t%s\n' "$bin" "$pkg" "$ver" >>"$FX/state/dpkg.owners"
  local p; for p in "$pkg" "$@"; do printf '%s\t%s\n' "$p" "$ver" >>"$FX/state/dpkg.installed"; done
}

dpkg_stubs() {
  touch "$FX/state/dpkg.owners" "$FX/state/dpkg.installed"
  stub dpkg 'if [ "$1" = -S ]; then awk -F"\t" -v f="$2" '"'"'$1==f{print $2": "f; found=1} END{exit !found}'"'"' "$FX/state/dpkg.owners"; else exit 1; fi'
  stub dpkg-query '
fmt=""; while [ $# -gt 0 ]; do case $1 in -W) ;; -f*) fmt=${1#-f}; [ -z "$fmt" ] && { shift; fmt=$1; } ;; *) pat=$1 ;; esac; shift; done
case $fmt in
  *Status-Abbrev*) awk -F"\t" -v p="${pat%\*}" '"'"'index($1,p)==1{print "ii  "$1}'"'"' "$FX/state/dpkg.installed" ;;
  *source:Package*) echo "$pat" ;;
  *Version*) awk -F"\t" -v p="$pat" '"'"'$1==p{print $2}'"'"' "$FX/state/dpkg.installed" | head -n1 | tr -d "\n" ;;
esac'
}

# apt_upgrades BIN NEWVERSION: apt-get install --only-upgrade bumps BIN.
apt_stub() {
  stub apt-get '
[ "$1" = update ] && exit 0
if [ -f "$FX/state/apt.upgrade" ]; then
  while IFS="	" read -r verfile newver; do printf "%s\n" "$newver" >"$verfile"; done <"$FX/state/apt.upgrade"
fi
exit 0'
}
apt_upgrades() { printf '%s\t%s\n' "$(php_ver_file "$1")" "$2" >>"$FX/state/apt.upgrade"; }

# curl_serve URL FILE: the curl stub returns FILE for URL (fail otherwise).
curl_serve() { mkdir -p "$FX/web"; printf '%s\t%s\n' "$1" "$2" >>"$FX/web/map"; }
curl_stub() {
  mkdir -p "$FX/web"; touch "$FX/web/map"
  stub curl '
out=""; url=""; data=""
while [ $# -gt 0 ]; do case $1 in -o) out=$2; shift ;; -d) data=$2; shift ;; -H|--max-time) shift ;; -*) ;; *) url=$1 ;; esac; shift; done
if [[ $url == *querybatch ]]; then
  python3 -c '"'"'
import json, sys
vul = {}
for line in open(sys.argv[1]):
    n, v, ids = line.split()
    vul[(n, v)] = ids.split(",")
q = json.loads(sys.argv[2])["queries"]
print(json.dumps({"results": [{"vulns": [{"id": i} for i in vul.get((x["package"]["name"], x["version"]), [])]} for x in q]}))
'"'"' "$FX/state/osv.vulns" "$data"; exit
fi
src=$(awk -F"\t" -v u="$url" '"'"'$1==u{print $2}'"'"' "$FX/web/map" | tail -n1)
[ -n "$src" ] && [ -f "$src" ] || exit 22
if [ -n "$out" ]; then cp "$src" "$out"; else cat "$src"; fi'
}
