#!/usr/bin/env bash
# WhiteSur para Manjaro/Arch con KDE Plasma 6. Ejecutar como usuario normal.
set -euo pipefail
cd "$(dirname "$0")"
[[ $EUID -ne 0 ]] || { echo 'Ejecuta este instalador como usuario normal.' >&2; exit 1; }
[[ "${XDG_CURRENT_DESKTOP:-}" == *KDE* ]] || { echo 'Se necesita una sesión KDE Plasma.' >&2; exit 1; }
[[ "$(plasmashell --version)" == *' 6.'* ]] || { echo 'Se necesita Plasma 6.' >&2; exit 1; }
case "${1:-}" in
  --restore) exec python3 manjaro/desktop.py restore ;;
  --skip-packages|'') ;;
  *) echo 'Uso: ./install-manjaro.sh [--skip-packages|--restore]' >&2; exit 1 ;;
esac

python3 manjaro/desktop.py backup
if [[ "${1:-}" != --skip-packages ]]; then
  if [[ -t 0 ]]; then elevate=(sudo); else elevate=(pkexec); fi
  "${elevate[@]}" pacman -Syu --needed --noconfirm kvantum kvantum-qt5 inter-font sassc libxml2 git curl unzip python-dbus cmake gcc make extra-cmake-modules \
    vulkan-headers yaml-cpp libevdev pkgconf cli11 gtest
fi

# Klassy (esquinas nativas), Wave Task (dock con zoom) e InputActions (gestos),
# más el servicio que los recompila tras cada actualización de KDE.
manjaro/plugins.sh install

src="$HOME/.themes-src"
mkdir -p "$src"
for theme in WhiteSur-kde WhiteSur-gtk-theme WhiteSur-icon-theme WhiteSur-cursors WhiteSur-wallpapers; do
  if [[ ! -d "$src/$theme/.git" ]]; then
    git clone --depth=1 "https://github.com/vinceliuice/$theme.git" "$src/$theme"
  fi
done
python3 - "$src" <<'PY'
import json, pathlib, subprocess, sys
src = pathlib.Path(sys.argv[1])
versions = {p.name: subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'], text=True).strip()
            for p in src.glob('WhiteSur-*') if (p/'.git').is_dir()}
target = pathlib.Path.home()/'.local/state/macos-setup/sources.json'
target.write_text(json.dumps(versions, indent=2)+'\n')
PY

(cd "$src/WhiteSur-kde" && bash install.sh -c light alt)
(cd "$src/WhiteSur-icon-theme" && bash install.sh -a)
(cd "$src/WhiteSur-cursors" && bash install.sh)
# GTK es para las aplicaciones GTK; el escritorio utiliza el tema nativo KDE.
(cd "$src/WhiteSur-gtk-theme" && bash install.sh -c Light -a normal -l && bash install.sh -c Dark -a normal)
bash scripts/20-fix-libadwaita-css.sh
python3 manjaro/desktop.py apply
printf '\nListo. Reabre las aplicaciones para que carguen WhiteSur.\n'
printf 'Restaurar el escritorio previo: ./install-manjaro.sh --restore\n'
