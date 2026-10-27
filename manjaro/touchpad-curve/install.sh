#!/usr/bin/env bash
# Curva del touchpad estilo Windows para KWin (ver touchpad-curve.c).
#   install.sh            compilar, instalar y cargar en KWin al iniciar sesión
#   install.sh --remove   quitarlo (efecto al volver a iniciar sesión)
#
# Si KWin no arrancara: Ctrl+Alt+F3, iniciar sesión y borrar
#   ~/.config/systemd/user/plasma-kwin_wayland.service.d/touchpad-curve.conf
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
lib=$HOME/.local/lib/macos-setup/libtouchpad-curve.so
dropin=$HOME/.config/systemd/user/plasma-kwin_wayland.service.d/touchpad-curve.conf
conf=$HOME/.config/macos-setup/touchpad-curve.conf

if [[ ${1:-} == --remove ]]; then
  rm -f "$dropin" "$lib"
  systemctl --user daemon-reload
  echo 'Curva del touchpad quitada; cierra sesión y vuelve a entrar.'
  exit 0
fi

mkdir -p "$(dirname "$lib")" "$(dirname "$dropin")" "$(dirname "$conf")"
gcc -O2 -Wall -Wextra -fPIC -shared -o "$lib.new" "$here/touchpad-curve.c" -linput -lm -ldl
mv "$lib.new" "$lib"
# Conservar los ajustes del usuario si ya existen.
[[ -f $conf ]] || cp "$here/touchpad-curve.conf" "$conf"
printf '[Service]\nEnvironment=LD_PRELOAD=%s\n' "$lib" > "$dropin"
systemctl --user daemon-reload
echo 'Curva del touchpad instalada; se aplica al volver a iniciar sesión.'
