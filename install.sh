#!/usr/bin/env bash
# Instalador completo del escritorio macOS sobre Ubuntu + GNOME.
# Uso:  ./install.sh            (todo)
#       ./install.sh 40 60      (solo los pasos indicados)
set -euo pipefail
cd "$(dirname "$0")"
source scripts/lib.sh

require_gnome
[ "$(id -u)" -ne 0 ] || fail "no lo ejecutes como root; usa tu usuario normal"

VER="$(shell_version)"
if [ "$VER" -lt 45 ] 2>/dev/null; then
  warn "GNOME $VER es anterior a la 45; algunas extensiones pueden no existir"
fi

ALL=(00-packages 10-themes 20-fix-libadwaita-css 30-extensions 40-settings 50-spotlight-patches 60-terminal)

if [ $# -gt 0 ]; then
  SELECTED=()
  for want in "$@"; do
    for s in "${ALL[@]}"; do
      case "$s" in "$want"*) SELECTED+=("$s") ;; esac
    done
  done
  [ ${#SELECTED[@]} -gt 0 ] || fail "ningun paso coincide con: $*"
else
  SELECTED=("${ALL[@]}")
fi

for s in "${SELECTED[@]}"; do
  printf '\n'
  bash "scripts/$s.sh"
done

printf '\n'
step "Instalacion terminada"
cat <<'TXT'

  Cierra sesion y vuelve a entrar para que carguen las extensiones y el
  tema del Shell. En Wayland no hay forma de recargarlo en caliente.

  Al volver:
    Super + Espacio   buscador flotante tipo Spotlight
    Super             vista general de ventanas
    Super + A         rejilla de aplicaciones

  Para deshacerlo todo:  ./uninstall.sh

TXT
