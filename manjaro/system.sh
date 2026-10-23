#!/usr/bin/env bash
# Partes del sistema (root): pantalla de inicio de sesión WhiteSur, arranque
# Plymouth con el logo del fabricante (bgrt) y tema de sonidos elementary.
#
#   system.sh apply SDDM_SRC FONDO.jpg   instalar y activar (SDDM_SRC: WhiteSur-kde/sddm)
#   system.sh restore           volver a lo anterior
#
# Plymouth también muestra la petición de contraseña de LUKS: bgrt (two-step,
# incluido en Plymouth) la admite. No usar temas de terceros sin comprobarlo.
set -euo pipefail
shopt -s inherit_errexit

[[ $EUID -eq 0 ]] || { echo 'Requiere root.' >&2; exit 1; }
state=/usr/local/lib/macos-setup
sddm_theme=/usr/share/sddm/themes/WhiteSur-light
sddm_conf=/etc/sddm.conf.d/zz-macos-setup.conf   # se lee después de kde_settings.conf

case "${1:-}" in
  apply)
    src=${2:?Falta WhiteSur-kde/sddm}
    background=${3:?Falta el fondo}
    pacman -S --needed --noconfirm sound-theme-elementary

    # Copia equivalente a WhiteSur-kde/sddm/install.sh (variante clara, Plasma 6.2+).
    rm -rf "$sddm_theme"
    cp -r "$src/WhiteSur-6.2" "$sddm_theme"
    install -m644 "$background" "$sddm_theme/background.jpeg"
    cp "$src/images/preview-light.jpeg" "$sddm_theme/preview.jpeg"
    sed -i '/Name=/s/WhiteSur/WhiteSur-light/; /Theme-Id=/s/WhiteSur/WhiteSur-light/' "$sddm_theme/metadata.desktop"
    sed -i 's/WhiteSur/WhiteSur-light/g' "$sddm_theme/Main.qml"
    printf '[Theme]\nCurrent=WhiteSur-light\n' > "$sddm_conf"

    install -d "$state"
    current=$(plymouth-set-default-theme)
    if [[ $current != bgrt ]]; then
      echo "$current" > "$state/plymouth-previous"
      plymouth-set-default-theme -R bgrt
    fi
    echo 'Sistema: inicio de sesión WhiteSur, arranque bgrt y sonidos elementary.' ;;
  restore)
    rm -f "$sddm_conf"
    rm -rf "$sddm_theme"
    if [[ -f $state/plymouth-previous ]]; then
      plymouth-set-default-theme -R "$(cat "$state/plymouth-previous")"
      rm -f "$state/plymouth-previous"
    fi
    echo 'Sistema restaurado (el paquete de sonidos se conserva).' ;;
  *)
    echo 'Uso: system.sh apply SDDM_SRC FONDO.jpg | restore' >&2; exit 1 ;;
esac
