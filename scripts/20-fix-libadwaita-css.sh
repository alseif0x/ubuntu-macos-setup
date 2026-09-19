#!/usr/bin/env bash
# Paso 3: corregir el CSS que genera WhiteSur para libadwaita.
#
# El generador emite  color-mix(in srgb, black 6% #HEX)  sin la coma antes del
# segundo color. Es sintaxis invalida: GTK descarta esas reglas y ademas llena
# el journal de "Theme parser error" cada vez que arranca una app GTK4.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

step "Reparando reglas color-mix mal formadas"
fixed_total=0
for f in "$HOME/.config/gtk-4.0/gtk-Light.css" "$HOME/.config/gtk-4.0/gtk-Dark.css"; do
  [ -f "$f" ] || continue
  n=$(grep -c 'color-mix(in srgb, [a-z]* [0-9]*% #' "$f" || true)
  if [ "$n" -gt 0 ]; then
    backup_once "$f"
    sed -i -E 's/color-mix\(in srgb, ([a-z]+) ([0-9]+%) (#[0-9A-Fa-f]{3,8})\)/color-mix(in srgb, \1 \2, \3)/g' "$f"
    ok "$(basename "$f"): $n reglas corregidas"
    fixed_total=$((fixed_total + n))
  else
    ok "$(basename "$f"): sin reglas que corregir"
  fi
done
[ "$fixed_total" -gt 0 ] && warn "cierra y reabre las apps GTK4 para que recarguen el CSS" || true
