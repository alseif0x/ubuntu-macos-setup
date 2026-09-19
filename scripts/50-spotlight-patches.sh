#!/usr/bin/env bash
# Paso 6: parches a la extension Spotlight.
#
# Tal como se publica, la extension tiene un problema real y tres limitaciones
# esteticas. Se aplican por sustitucion de texto en lugar de con diffs de
# contexto porque asi sobreviven a cambios menores de version. Cada edicion es
# idempotente: se detecta por un marcador propio si ya estaba puesta.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

EXT="$HOME/.local/share/gnome-shell/extensions/spotlight@nin"
[ -d "$EXT" ] || fail "Spotlight no esta instalada; ejecuta antes 30-extensions.sh"

step "Parcheando Spotlight en $EXT"
for f in extension.js lib/popup/widget/spotlightPopup.js \
         lib/popup/components/positioner.js stylesheet.css; do
  [ -e "$EXT/$f.orig" ] || cp -a "$EXT/$f" "$EXT/$f.orig"
done

python3 - "$EXT" <<'PY'
import sys, pathlib
ext = pathlib.Path(sys.argv[1])
problems = 0

def edit(relpath, old, new, label, done):
    """done(texto) -> True si el parche ya esta aplicado."""
    global problems
    p = ext / relpath
    s = p.read_text(encoding="utf-8")
    if done(s):
        print(f"  -- ya estaba  {label}")
        return
    if old not in s:
        print(f"  !! ANCLAJE NO ENCONTRADO en {relpath}: {label}")
        problems += 1
        return
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print(f"  ok aplicado   {label}")

POPUP = "lib/popup/widget/spotlightPopup.js"
POS   = "lib/popup/components/positioner.js"

# --- Parche 1: robo del buscador acotado al tiempo que el popup esta abierto ---
# De serie la extension retira PARA SIEMPRE el widget de busqueda de la vista
# general. Sin el, la transicion a la rejilla de aplicaciones no se completa:
# el boton "Mostrar aplicaciones" desplaza la vista y no dibuja ningun icono.
edit("extension.js",
     """        // Steal the overview search widgets permanently. The overview search stays gone
        // for as long as Spotlight is loaded, which is the whole point of the extension.
        this._popup.stealOverviewSearch();
""",
     """        // Parche: el robo de widgets se hace solo mientras el popup esta abierto,
        // para no romper la rejilla de aplicaciones de la vista general.
""",
     "1a: no robar el buscador al arrancar",
     lambda s: "this._popup.stealOverviewSearch();" not in s)

edit(POPUP,
     """        if (!this._stealer.entry || !this._stealer.search)
            return;""",
     """        this.stealOverviewSearch();
        if (!this._stealer.entry || !this._stealer.search)
            return;""",
     "1b: robarlo al abrir el panel",
     lambda s: "this.stealOverviewSearch();\n        if (!this._stealer.entry" in s)

edit(POPUP,
     """        this._visible = false;
        this.hide();
        if (this.get_parent())
            Main.layoutManager.removeChrome(this);
    }""",
     """        this._visible = false;
        this.hide();
        if (this.get_parent())
            Main.layoutManager.removeChrome(this);
        this.returnOverviewSearch();
    }""",
     "1c: devolverlo al cerrarlo",
     lambda s: "this.returnOverviewSearch();\n    }" in s)

# --- Parche 2: guarda contra null ---
# Consecuencia del parche 1: al cerrar, search ya puede ser null y la extension
# muere con un TypeError que la deja en estado ERROR.
edit(POPUP,
     """            this._stealer.search._text.disconnect(this._textChangedEventId);""",
     """            if (this._stealer.search)
                this._stealer.search._text.disconnect(this._textChangedEventId);""",
     "2: proteger el cierre contra search nulo",
     lambda s: "if (this._stealer.search)\n                this._stealer.search._text" in s)

# --- Parche 3: panel mas grande ---
edit(POPUP, "width: 520,", "width: 760,",
     "3a: ancho del contenedor 520 -> 760",
     lambda s: "width: 760," in s)
edit(POS, "Math.min(520,", "Math.min(760,",
     "3b: ancho del popup 520 -> 760",
     lambda s: "Math.min(760," in s)
edit("stylesheet.css", "max-height: 380px;", "max-height: 620px;",
     "3c: alto de resultados 380 -> 620",
     lambda s: "max-height: 620px;" in s)
edit("stylesheet.css", "  font-size: 18px;\n  font-weight: 400;",
     "  font-size: 21px;\n  font-weight: 400;",
     "3d: texto de busqueda 18 -> 21px",
     lambda s: "font-size: 21px;" in s)

# --- Parche 4: anclado al tercio superior ---
# De serie sale centrado verticalmente. Spotlight en macOS aparece arriba y
# crece hacia abajo, que es bastante mas comodo de leer.
edit(POS,
     """        this._popup.set_position(
            Math.floor(monitor.x + (monitor.width - popupWidth) / 2),
            Math.floor(monitor.y + (monitor.height - naturalHeight) / 2),
        );""",
     """        // Parche: anclado al tercio superior, como Spotlight en macOS, en lugar
        // del centro vertical. Con tope arriba y abajo para no salirse nunca.
        const top = Math.max(
            monitor.y + 60,
            Math.floor(monitor.y + monitor.height * 0.18),
        );
        const maxTop = monitor.y + Math.max(0, monitor.height - naturalHeight - 40);
        this._popup.set_position(
            Math.floor(monitor.x + (monitor.width - popupWidth) / 2),
            Math.floor(Math.min(top, maxTop)),
        );""",
     "4: anclar el panel arriba",
     lambda s: "const maxTop =" in s)

if problems:
    print(f"\n  {problems} parche(s) sin anclaje: la extension ha cambiado de version.")
    print("  Compara con patches/reference/spotlight-macos.diff y ajusta a mano.")
    sys.exit(1)
PY

if command -v node >/dev/null 2>&1; then
  step "Comprobando la sintaxis del JavaScript resultante"
  for f in extension.js lib/popup/widget/spotlightPopup.js lib/popup/components/positioner.js; do
    node --check "$EXT/$f" && ok "$f sin errores de sintaxis"
  done
fi

warn "los cambios de codigo solo entran al cerrar sesion: GNOME cachea las extensiones"
