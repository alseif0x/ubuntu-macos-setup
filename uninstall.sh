#!/usr/bin/env bash
# Devuelve el escritorio al aspecto original de Ubuntu.
# No borra los temas ni las extensiones del disco, solo deja de usarlos, asi
# que volver a activarlos es cuestion de reejecutar install.sh.
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${XDG_CURRENT_DESKTOP:-}" == *KDE* ]]; then
  exec bash ./install-manjaro.sh --restore
fi
source scripts/lib.sh

step "Restaurando los ajustes por defecto de GNOME"
for k in gtk-theme icon-theme cursor-theme font-name color-scheme; do
  gsettings reset org.gnome.desktop.interface "$k"
done
gsettings reset org.gnome.desktop.wm.preferences titlebar-font
gsettings reset org.gnome.desktop.wm.preferences button-layout
gsettings reset org.gnome.desktop.background picture-uri
gsettings reset org.gnome.desktop.background picture-uri-dark
gsettings reset org.gnome.desktop.screensaver picture-uri
gsettings reset org.gnome.shell.extensions.user-theme name 2>/dev/null || true
gsettings reset org.gnome.desktop.wm.keybindings switch-input-source
gsettings reset org.gnome.desktop.wm.keybindings switch-input-source-backward
ok "aspecto restaurado"

step "Devolviendo el dock de Ubuntu"
for uuid in dash-to-dock@micxgx.gmail.com blur-my-shell@aunetx \
            just-perfection-desktop@just-perfection spotlight@nin; do
  disable_extension "$uuid"
done
enable_extension "ubuntu-dock@ubuntu.com"
gsettings set org.gnome.shell disabled-extensions "@as []"
ok "dock original activo"

step "Restaurando la terminal"
if gsettings list-schemas | grep -q '^org.gnome.Ptyxis$'; then
  UUID="$(gsettings get org.gnome.Ptyxis default-profile-uuid | sed "s/'//g")"
  gsettings reset "org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/$UUID/" palette
  gsettings reset org.gnome.Ptyxis use-system-font
  gsettings reset org.gnome.Ptyxis font-name
  gsettings reset org.gnome.Ptyxis interface-style
  ok "Ptyxis con sus valores de fabrica"
fi
if [ -f "$HOME/.bashrc.pre-macos" ]; then
  cp -a "$HOME/.bashrc.pre-macos" "$HOME/.bashrc"
  ok "~/.bashrc restaurado desde la copia previa"
else
  warn "no hay copia de ~/.bashrc; quita a mano el bloque 'Terminal estilo macOS'"
fi

printf '\n'
warn "cierra sesion y vuelve a entrar para ver el escritorio original"
