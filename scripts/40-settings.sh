#!/usr/bin/env bash
# Paso 5: todos los ajustes de aspecto, dock, panel y notificaciones.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_gnome

step "Tema, iconos, cursores y tipografia"
gsettings set org.gnome.desktop.interface gtk-theme     'WhiteSur-Light'
gsettings set org.gnome.desktop.interface icon-theme    'WhiteSur-light'
gsettings set org.gnome.desktop.interface cursor-theme  'WhiteSur-cursors'
gsettings set org.gnome.desktop.interface color-scheme  'default'
gsettings set org.gnome.desktop.interface font-name     'Inter 11'
gsettings set org.gnome.desktop.wm.preferences titlebar-font 'Inter Semi Bold 11'
# Botones de ventana a la izquierda, en el orden de los semaforos de macOS.
gsettings set org.gnome.desktop.wm.preferences button-layout 'close,minimize,maximize:'
gsettings set org.gnome.shell.extensions.user-theme name 'WhiteSur-Light' 2>/dev/null \
  || warn "user-theme aun no cargada; su valor se aplicara tras cerrar sesion"
ok "aspecto general aplicado"

step "Fondo de pantalla"
WALLS="$(pictures_dir)/Fondos-WhiteSur"
if [ -f "$WALLS/Sonoma-light.jpg" ]; then
  gsettings set org.gnome.desktop.background picture-uri      "file://$WALLS/Sonoma-light.jpg"
  gsettings set org.gnome.desktop.background picture-uri-dark "file://$WALLS/Sonoma-dark.jpg"
  gsettings set org.gnome.desktop.screensaver picture-uri     "file://$WALLS/Sonoma-light.jpg"
  gsettings set org.gnome.desktop.background picture-options  'zoom'
  ok "fondo Sonoma aplicado"
else
  warn "no encuentro los fondos, ejecuta antes 10-themes.sh"
fi

step "Dock estilo macOS: abajo, centrado, translucido y autoocultable"
D=org.gnome.shell.extensions.dash-to-dock
gsettings set $D dock-position 'BOTTOM'
gsettings set $D extend-height false          # dock flotante, no barra lateral completa
gsettings set $D dock-fixed false
gsettings set $D autohide true
gsettings set $D intellihide true
gsettings set $D intellihide-mode 'FOCUS_APPLICATION_WINDOWS'
gsettings set $D transparency-mode 'DYNAMIC'
gsettings set $D background-opacity 0.35
gsettings set $D customize-alphas true
gsettings set $D min-alpha 0.2
gsettings set $D max-alpha 0.6
gsettings set $D custom-theme-shrink true
gsettings set $D apply-custom-theme false
gsettings set $D running-indicator-style 'DOTS'
gsettings set $D show-trash true
gsettings set $D show-mounts false
gsettings set $D show-apps-at-top false
gsettings set $D dash-max-icon-size 52
gsettings set $D click-action 'minimize-or-previews'
gsettings set $D scroll-action 'cycle-windows'
gsettings set $D hot-keys false
ok "dock configurado"

step "Desenfoque en panel, vista general y dock"
B=org.gnome.shell.extensions.blur-my-shell
U=blur-my-shell@aunetx
ext_gsettings $U set $B.panel blur true
ext_gsettings $U set $B.panel brightness 0.85
ext_gsettings $U set $B.panel sigma 30
ext_gsettings $U set $B.overview blur true
ext_gsettings $U set $B.dash-to-dock blur true
ext_gsettings $U set $B.dash-to-dock brightness 0.6
ext_gsettings $U set $B.dash-to-dock sigma 30
ext_gsettings $U set $B.applications blur false
ok "desenfoque configurado"

step "Reloj a la derecha y notificaciones en la esquina superior derecha"
J=org.gnome.shell.extensions.just-perfection
P=just-perfection-desktop@just-perfection
ext_gsettings $P set $J clock-menu-position 1         # 0 centro, 1 derecha, 2 izquierda
ext_gsettings $P set $J clock-menu-position-offset 20 # al final del todo
ext_gsettings $P set $J notification-banner-position 2
gsettings set org.gnome.desktop.interface clock-show-weekday true
gsettings set org.gnome.desktop.interface clock-show-date true
ok "panel superior configurado"

step "Buscador tipo Spotlight con Super+Espacio"
# Ese atajo lo ocupa por defecto el cambio de idioma del teclado; hay que liberarlo.
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "[]"
gsettings set org.gnome.desktop.wm.keybindings switch-input-source-backward "[]"
ext_gsettings spotlight@nin set org.gnome.shell.extensions.spotlight \
  toggle-shortcut "['<Super>space', '<Control>space']"
ext_gsettings spotlight@nin set org.gnome.shell.extensions.spotlight \
  theme-preference 'default'
ok "atajo asignado"
