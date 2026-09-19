#!/usr/bin/env bash
# Paso 7: terminal con el aspecto de Terminal.app.
#
# No se instala ninguna terminal nueva. Ptyxis, la que trae Ubuntu, ya incluye
# de fabrica las paletas reales de Terminal.app; solo hay que elegir la buena.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

if ! gsettings list-schemas | grep -q '^org.gnome.Ptyxis$'; then
  warn "Ptyxis no esta instalada en este sistema, omito el paso de terminal"
  exit 0
fi

step "Configurando Ptyxis con el perfil Basico de Terminal.app"
UUID="$(gsettings get org.gnome.Ptyxis default-profile-uuid | sed "s/'//g")"
P="org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/$UUID/"

gsettings set "$P" palette 'Terminal Basic'   # fondo blanco, texto negro
gsettings set "$P" opacity 1.0
gsettings set "$P" bold-is-bright false
gsettings set "$P" scrollback-lines 100000
gsettings set org.gnome.Ptyxis interface-style 'light'
gsettings set org.gnome.Ptyxis use-system-font false
# Menlo, la fuente de Terminal.app, desciende de DejaVu Sans Mono.
gsettings set org.gnome.Ptyxis font-name 'DejaVu Sans Mono 12'
gsettings set org.gnome.Ptyxis cursor-shape 'block'
gsettings set org.gnome.Ptyxis cursor-blink-mode 'on'
gsettings set org.gnome.Ptyxis audible-bell false
gsettings set org.gnome.Ptyxis visual-bell false
gsettings set org.gnome.Ptyxis default-columns 80
gsettings set org.gnome.Ptyxis default-rows 24
ok "perfil aplicado"

step "Instalando el prompt de Terminal.app en ~/.bashrc"
MARK='# --- Terminal estilo macOS (ubuntu-macos-setup) ---'
if grep -qF "$MARK" "$HOME/.bashrc"; then
  ok "el prompt ya estaba instalado"
else
  backup_once "$HOME/.bashrc"
  cat "$REPO_ROOT/config/bashrc-macos.sh" >> "$HOME/.bashrc"
  ok "anadido al final de ~/.bashrc (copia previa en ~/.bashrc.pre-macos)"
fi
