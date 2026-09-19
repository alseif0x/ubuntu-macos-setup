
# --- Terminal estilo macOS (ubuntu-macos-setup) ---
# Prompt identico al de Terminal.app:  maquina:carpeta usuario$
# El prefijo \[\e]0;\W\a\] pone la carpeta actual en el titulo de la ventana,
# igual que hace macOS.
PS1='\[\e]0;\W\a\]\h:\W \u\$ '

# Listados con estado de git y carpetas primero. Requieren eza; si no esta
# instalado, los alias simplemente no se definen y ls sigue funcionando.
if command -v eza >/dev/null 2>&1; then
  alias ll='eza -l --group-directories-first --git'
  alias la='eza -la --group-directories-first --git'
  alias lt='eza --tree --level=2'
fi
