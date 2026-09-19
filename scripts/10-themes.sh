#!/usr/bin/env bash
# Paso 2: tema GTK, iconos, cursores y fondos de WhiteSur.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_cmd git

step "Descargando los repositorios de WhiteSur"
clone_or_update https://github.com/vinceliuice/WhiteSur-gtk-theme.git
clone_or_update https://github.com/vinceliuice/WhiteSur-icon-theme.git
clone_or_update https://github.com/vinceliuice/WhiteSur-cursors.git
clone_or_update https://github.com/vinceliuice/WhiteSur-wallpapers.git

step "Compilando el tema GTK (claro y oscuro, capa de shell, Nautilus estilo Big Sur)"
( cd "$THEMES_SRC/WhiteSur-gtk-theme" && ./install.sh -c Light -c Dark -a normal --shell -i apple -N stable >/dev/null )
ok "tema GTK3/GTK4 instalado en ~/.themes"

step "Aplicando la capa libadwaita (asi tambien cambian Archivos, Ajustes, etc.)"
( cd "$THEMES_SRC/WhiteSur-gtk-theme" && ./install.sh -l -c Light >/dev/null )
ok "libadwaita enlazado en ~/.config/gtk-4.0"

step "Instalando iconos y cursores"
( cd "$THEMES_SRC/WhiteSur-icon-theme" && ./install.sh -a >/dev/null )
( cd "$THEMES_SRC/WhiteSur-cursors" && ./install.sh >/dev/null )
ok "iconos y cursores instalados"

step "Copiando fondos de pantalla"
WALLS="$(pictures_dir)/Fondos-WhiteSur"
mkdir -p "$WALLS"
cp -n "$THEMES_SRC/WhiteSur-wallpapers/4k/"*.jpg "$WALLS/" 2>/dev/null || true
ok "fondos en $WALLS"

# Las aplicaciones empaquetadas como snap estan confinadas y no ven ~/.themes.
# Copiar el tema dentro de su carpeta propia es la unica forma de que lo adopten.
step "Propagando el tema a snaps y al sistema"
for app in firefox thunderbird; do
  if [ -d "$HOME/snap/$app" ]; then
    mkdir -p "$HOME/snap/$app/common/.themes"
    cp -rn "$HOME/.themes/WhiteSur-Light" "$HOME/snap/$app/common/.themes/" 2>/dev/null || true
    ok "tema copiado dentro del snap de $app"
  fi
done
sudo cp -rn "$HOME/.themes/WhiteSur-Light" "$HOME/.themes/WhiteSur-Dark" /usr/share/themes/ 2>/dev/null || true
ok "tema disponible tambien a nivel de sistema"
