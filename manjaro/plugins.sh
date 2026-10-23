#!/usr/bin/env bash
# Plugins nativos compilados contra KWin/Plasma: Klassy (decoración), Wave Task
# (dock con zoom), InputActions (gestos) y Kiview (Vista rápida). Tras actualizar KDE deben
# recompilarse; un hook de pacman lo programa y el servicio lo hace solo.
#
#   plugins.sh install        como usuario: compila lo que falte e instala
#   plugins.sh build [pkg…]    como usuario: solo compila
#   plugins.sh rebuild USER   como root (servicio): recompila lo instalado
set -euo pipefail
shopt -s inherit_errexit

PKGS=(klassy inputactions-ctl inputactions-kwin wavetask kiview)
SYSTEM_LIB=/usr/local/lib/macos-setup
here=$(cd "$(dirname "$0")" && pwd)

# En el repo los PKGBUILD están junto al script; instalados, en SYSTEM_LIB.
pkgbuild_dir() {
  local base=$here
  [[ -d $base/klassy ]] || base=$SYSTEM_LIB
  if [[ $1 == klassy ]]; then echo "$base/klassy"; else echo "$base/aur/$1"; fi
}

build() {
  local cache=$HOME/.cache/macos-setup list
  list=$cache/built.list
  mkdir -p "$cache"
  # Dos ejecuciones a la vez se borrarían el directorio de compilación.
  exec 9>"$cache/.lock"
  flock -n 9 || { echo 'Ya hay otra compilación en curso.' >&2; return 1; }
  : > "$list"
  for pkg in "$@"; do
    rm -rf "${cache:?}/$pkg"
    cp -r "$(pkgbuild_dir "$pkg")" "$cache/$pkg"
    # --nodeps: inputactions-kwin depende de inputactions-ctl, que se instala
    # en la misma transacción; las dependencias de compilación ya están.
    (cd "$cache/$pkg" && MAKEFLAGS="-j$(( $(nproc) / 2 > 0 ? $(nproc) / 2 : 1 ))" \
      nice -n 15 makepkg -f --nodeps --noconfirm --cleanbuild >&2 && makepkg --packagelist) >> "$list" || return 1
  done
  cat "$list"
}

install_system_files() {
  # Copia propiedad de root: el servicio no ejecuta scripts editables por el usuario.
  local user=$1
  install -d "$SYSTEM_LIB/aur"
  install -m755 "$here/plugins.sh" "$SYSTEM_LIB/plugins.sh"
  rm -rf "$SYSTEM_LIB/klassy" "$SYSTEM_LIB/aur"/*
  cp -r "$here/klassy" "$SYSTEM_LIB/klassy"
  for pkg in "${PKGS[@]}"; do [[ $pkg == klassy ]] || cp -r "$here/aur/$pkg" "$SYSTEM_LIB/aur/$pkg"; done
  chown -R root:root "$SYSTEM_LIB"
  cat > /etc/systemd/system/macos-setup-rebuild.service <<EOF
[Unit]
Description=Recompilar los plugins macOS tras actualizar KDE

[Service]
Type=oneshot
ExecStart=$SYSTEM_LIB/plugins.sh rebuild $user
Nice=15
IOSchedulingClass=idle
TimeoutStartSec=infinity
EOF
  install -d /etc/pacman.d/hooks
  cat > /etc/pacman.d/hooks/macos-setup-rebuild.hook <<'EOF'
[Trigger]
Operation = Upgrade
Type = Package
Target = kwin
Target = kdecoration
Target = libplasma
Target = plasma-workspace
Target = qt6-base
Target = qt6-declarative

[Action]
Description = Programando la recompilación de Klassy, Wave Task e InputActions...
When = PostTransaction
Exec = /usr/bin/systemctl start --no-block macos-setup-rebuild.service
EOF
  systemctl daemon-reload
}

case "${1:-}" in
  build)
    shift
    [[ $EUID -ne 0 ]] || { echo 'Compila como usuario normal.' >&2; exit 1; }
    (($#)) || set -- "${PKGS[@]}"
    build "$@" ;;
  install)
    [[ $EUID -ne 0 ]] || { echo 'Ejecuta como usuario normal.' >&2; exit 1; }
    missing=()
    for pkg in "${PKGS[@]}"; do pacman -Q "$pkg" >/dev/null 2>&1 || missing+=("$pkg"); done
    files=()
    if ((${#missing[@]})); then
      built=$(build "${missing[@]}")
      mapfile -t files <<< "$built"
    fi
    if [[ -t 0 ]]; then elevate=(sudo); else elevate=(pkexec); fi
    "${elevate[@]}" bash -c 'set -e; if (($# > 2)); then pacman -U --noconfirm "${@:3}"; fi; "$1" system-files "$2"' \
      _ "$here/plugins.sh" "$USER" "${files[@]}"
    echo 'Plugins instalados. Cierra sesión y vuelve a entrar para que KWin cargue InputActions.' ;;
  system-files)
    [[ $EUID -eq 0 ]] || { echo 'Requiere root.' >&2; exit 1; }
    install_system_files "$2" ;;
  rebuild)
    [[ $EUID -eq 0 && -n ${2:-} ]] || { echo 'Uso (root): plugins.sh rebuild USUARIO' >&2; exit 1; }
    user=$2
    home=$(getent passwd "$user" | cut -d: -f6)
    # El hook se dispara dentro de la transacción: esperar a que pacman libere la base.
    while [[ -e /var/lib/pacman/db.lck ]]; do sleep 5; done
    installed=()
    for pkg in "${PKGS[@]}"; do pacman -Q "$pkg" >/dev/null 2>&1 && installed+=("$pkg"); done
    ((${#installed[@]})) || exit 0
    built=$(runuser -u "$user" -- env HOME="$home" PATH=/usr/bin:/bin \
      "$SYSTEM_LIB/plugins.sh" build "${installed[@]}")
    mapfile -t files <<< "$built"
    while [[ -e /var/lib/pacman/db.lck ]]; do sleep 5; done
    pacman -U --noconfirm "${files[@]}"
    echo 'Plugins recompilados; se cargarán en el próximo inicio de sesión.' ;;
  *)
    echo 'Uso: plugins.sh install | build [paquete…] | rebuild USUARIO' >&2; exit 1 ;;
esac
