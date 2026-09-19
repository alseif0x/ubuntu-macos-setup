#!/usr/bin/env bash
# Paso 4: descargar e instalar las extensiones de GNOME desde el repositorio oficial.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_gnome; require_cmd curl; require_cmd python3

SHELL_VER="$(shell_version)"
step "GNOME Shell detectado: version $SHELL_VER"

install_ego() {
  local uuid="$1" url
  if [ -d "$HOME/.local/share/gnome-shell/extensions/$uuid" ]; then
    ok "$uuid ya instalada, no la toco"
    return 0
  fi
  url="$(curl -fsS "https://extensions.gnome.org/extension-info/?uuid=$uuid&shell_version=$SHELL_VER" \
        --max-time 30 | python3 -c 'import json,sys; print(json.load(sys.stdin)["download_url"])')" \
    || { warn "$uuid no tiene version para GNOME $SHELL_VER, se omite"; return 0; }
  curl -fsSL -o "/tmp/$uuid.zip" "https://extensions.gnome.org$url" --max-time 120
  gnome-extensions install --force "/tmp/$uuid.zip"
  ok "$uuid instalada"
}

step "Instalando extensiones"
install_ego "dash-to-dock@micxgx.gmail.com"
install_ego "blur-my-shell@aunetx"
install_ego "just-perfection-desktop@just-perfection"
install_ego "spotlight@nin"

step "Activando extensiones y apartando el dock de Ubuntu"
# user-theme viene del paquete gnome-shell-extensions y hace falta para que el
# tema alcance al propio Shell (panel superior, menus, overview).
enable_extension "user-theme@gnome-shell-extensions.gcampax.github.com"
enable_extension "dash-to-dock@micxgx.gmail.com"
enable_extension "blur-my-shell@aunetx"
enable_extension "just-perfection-desktop@just-perfection"
enable_extension "spotlight@nin"
# ubuntu-dock y dash-to-dock son la misma extension bifurcada: no pueden convivir.
disable_extension "ubuntu-dock@ubuntu.com"

warn "en Wayland las extensiones nuevas solo cargan tras cerrar sesion"
