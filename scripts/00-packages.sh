#!/usr/bin/env bash
# Paso 1: paquetes del sistema necesarios para compilar y aplicar el tema.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

step "Instalando paquetes base"
sudo apt-get update -qq

# Imprescindibles: soporte de extensiones, compilador sass del tema,
# glib-compile-* para los esquemas y xmllint que usa el instalador de WhiteSur.
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  gnome-shell-extensions gnome-tweaks gnome-shell-extension-manager \
  sassc libglib2.0-dev-bin libxml2-utils \
  git curl unzip fonts-inter

# Opcionales: mejoran la terminal pero el resto funciona sin ellos.
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y eza bat \
  || warn "eza/bat no disponibles en esta version de Ubuntu, se omiten"

ok "paquetes instalados"
