#!/usr/bin/env bash
# Helpers compartidos por todos los pasos.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEMES_SRC="$HOME/.themes-src"

_c_blue=$'\033[1;34m'; _c_green=$'\033[1;32m'
_c_yellow=$'\033[1;33m'; _c_red=$'\033[1;31m'; _c_off=$'\033[0m'

step()  { printf '%s==>%s %s\n' "$_c_blue" "$_c_off" "$*"; }
ok()    { printf '%s  ok%s %s\n' "$_c_green" "$_c_off" "$*"; }
warn()  { printf '%s  !!%s %s\n' "$_c_yellow" "$_c_off" "$*"; }
fail()  { printf '%s  xx%s %s\n' "$_c_red" "$_c_off" "$*" >&2; exit 1; }

require_cmd() { command -v "$1" >/dev/null 2>&1 || fail "falta el comando '$1'"; }
require_gnome() { command -v gnome-shell >/dev/null 2>&1 || fail "esto requiere GNOME Shell"; }
shell_version() { gnome-shell --version | awk '{print $3}' | cut -d. -f1; }

# Carpeta de imagenes respetando el idioma del sistema (Pictures, Imagenes...).
pictures_dir() {
  local d
  d="$(xdg-user-dir PICTURES 2>/dev/null || true)"
  if [ -z "$d" ] || [ "$d" = "$HOME" ]; then d="$HOME/Pictures"; fi
  printf '%s' "$d"
}

clone_or_update() {
  local url="$1" name
  name="$(basename "$url" .git)"
  mkdir -p "$THEMES_SRC"
  if [ -d "$THEMES_SRC/$name/.git" ]; then
    git -C "$THEMES_SRC/$name" pull --ff-only --quiet || warn "no se pudo actualizar $name"
  else
    git clone --depth=1 --quiet "$url" "$THEMES_SRC/$name"
  fi
  ok "$name listo en $THEMES_SRC/$name"
}

# Anade un UUID a enabled-extensions sin duplicar ni borrar lo que ya hubiera.
enable_extension() {
  python3 - "$1" <<'PY'
import ast, subprocess, sys
uuid = sys.argv[1]
cur = subprocess.run(["gsettings","get","org.gnome.shell","enabled-extensions"],
                     capture_output=True, text=True, check=True).stdout.strip()
items = [] if cur in ("@as []", "[]") else ast.literal_eval(cur)
if uuid not in items:
    items.append(uuid)
    subprocess.run(["gsettings","set","org.gnome.shell","enabled-extensions",str(items)], check=True)
PY
  ok "extension activada: $1"
}

disable_extension() {
  python3 - "$1" <<'PY'
import ast, subprocess, sys
uuid = sys.argv[1]
cur = subprocess.run(["gsettings","get","org.gnome.shell","enabled-extensions"],
                     capture_output=True, text=True, check=True).stdout.strip()
items = [] if cur in ("@as []", "[]") else ast.literal_eval(cur)
if uuid in items:
    items.remove(uuid)
    subprocess.run(["gsettings","set","org.gnome.shell","enabled-extensions",str(items)], check=True)
PY
  gnome-extensions disable "$1" 2>/dev/null || true
  ok "extension desactivada: $1"
}

# gsettings contra el esquema privado de una extension instalada en ~/.local.
ext_gsettings() {
  local uuid="$1"; shift
  local dir="$HOME/.local/share/gnome-shell/extensions/$uuid/schemas"
  if [ ! -d "$dir" ]; then warn "sin esquemas para $uuid, omito"; return 0; fi
  GSETTINGS_SCHEMA_DIR="$dir" gsettings "$@"
}

backup_once() {
  [ -e "$1" ] || return 0
  [ -e "$1.pre-macos" ] || cp -a "$1" "$1.pre-macos"
}
