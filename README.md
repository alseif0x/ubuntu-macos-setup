# ubuntu-macos-setup

## Manjaro / KDE Plasma 6

La rama `manjaro-kde` añade un instalador específico para Plasma 6:

```bash
./install-manjaro.sh
```

Incluye copia de seguridad y restauración. Consulta [manjaro/README.md](manjaro/README.md).
Las instrucciones siguientes corresponden al instalador original de Ubuntu/GNOME.

Convierte un Ubuntu con GNOME en un clon visual de macOS: tema WhiteSur en
ventanas y aplicaciones modernas, dock inferior translúcido, reloj a la derecha,
notificaciones arriba a la derecha, buscador flotante tipo Spotlight y la
terminal con los colores reales de Terminal.app.

Todo se instala en el usuario, no reemplaza el escritorio, y se deshace con un
comando.

## Probado en

| | |
| --- | --- |
| Distribución | Ubuntu 26.04 LTS |
| GNOME Shell | 50 |
| Sesión | Wayland |

Debería funcionar en GNOME 45 o superior. Cada extensión se descarga pidiendo
explícitamente la versión compatible con tu Shell, y si alguna no la tiene, el
instalador lo avisa y sigue en vez de romperse.

## Instalación

```bash
git clone https://github.com/alseif0x/ubuntu-macos-setup.git
cd ubuntu-macos-setup
./install.sh
```

Pide `sudo` solo en el primer paso, para instalar paquetes de los repositorios
oficiales. Al terminar hay que **cerrar sesión y volver a entrar**: en Wayland
las extensiones y el tema del Shell no se recargan en caliente.

Para reejecutar un paso suelto:

```bash
./install.sh 40        # solo los ajustes
./install.sh 30 50     # extensiones y parches
```

## Qué hace cada paso

| Script | Qué hace |
| --- | --- |
| `00-packages.sh` | Paquetes del sistema: soporte de extensiones, `sassc`, `xmllint`, fuente Inter |
| `10-themes.sh` | Compila e instala WhiteSur: GTK3, GTK4, libadwaita, iconos, cursores y fondos |
| `20-fix-libadwaita-css.sh` | Corrige reglas `color-mix()` mal formadas que genera el tema |
| `30-extensions.sh` | Descarga Dash to Dock, Blur my Shell, Just Perfection y Spotlight |
| `40-settings.sh` | Tema, tipografía, botones a la izquierda, dock, desenfoque, reloj, atajos |
| `50-spotlight-patches.sh` | Parchea la extensión Spotlight (ver más abajo) |
| `60-terminal.sh` | Ptyxis con la paleta de Terminal.app y el prompt de macOS |

## Decisiones que conviene conocer

**La terminal no se sustituye.** Ptyxis, la que trae Ubuntu, ya incluye de
fábrica las paletas reales de Terminal.app. Se activa `Terminal Basic`, que es
el perfil Básico del Mac, con `DejaVu Sans Mono` porque Menlo desciende de ella.
Probé Ghostty y Kitty antes de llegar aquí y ninguna aporta nada que Ptyxis no
haga ya para este objetivo.

**Los snaps necesitan su propia copia del tema.** Firefox y Thunderbird están
confinados y no ven `~/.themes`. El paso 10 copia el tema dentro de su carpeta,
que es la única forma de que lo adopten.

**El CSS de libadwaita viene roto.** El generador de WhiteSur emite
`color-mix(in srgb, black 6% #HEX)` sin la coma antes del segundo color. GTK
descarta esas reglas y llena el journal de errores en cada arranque de una app
GTK4. El paso 20 lo arregla.

**`ubuntu-dock` y `dash-to-dock` no conviven.** Son la misma extensión
bifurcada. El instalador desactiva la de Ubuntu; `uninstall.sh` la devuelve.

## Los parches a Spotlight

La extensión `spotlight@nin` es la mejor opción disponible para replicar el
buscador de macOS, pero tal como se publica tiene un problema real:

1. **Rompe el botón "Mostrar aplicaciones".** Retira de forma permanente el
   widget de búsqueda de la vista general. Sin él, la transición a la rejilla no
   se completa: la vista se desplaza y no dibuja ningún icono. El parche hace
   que lo tome prestado solo mientras el panel está abierto y lo devuelva al
   cerrarlo.
2. **Guarda contra `null`.** Consecuencia de lo anterior: al cerrar, el objeto
   de búsqueda ya puede ser nulo y la extensión muere con un `TypeError`.
3. **Panel más grande.** De 520 a 760 px de ancho, resultados de 380 a 620 px y
   texto de búsqueda de 18 a 21 px.
4. **Anclado arriba.** Sale centrado verticalmente; se ancla al 18 % de la
   altura, que es donde aparece Spotlight en el Mac, y crece hacia abajo.

Se aplican por sustitución de texto, no con `patch`, para que sobrevivan a
cambios menores de versión. Son idempotentes y guardan copia `.orig` de cada
archivo. El diff legible está en
[`patches/reference/spotlight-macos.diff`](patches/reference/spotlight-macos.diff).

## Lo que no se puede conseguir

Vale la pena saberlo antes de instalar, para no perseguirlo:

- **Chrome y las apps Electron** dibujan su propia barra de título. En Chrome se
  arregla a mano: `chrome://settings/appearance` → *Usar la barra de título y
  los bordes del sistema*. En Electron no hay solución desde el sistema.
- **Los menús de la aplicación en la barra superior** (Archivo, Edición…) no
  existen en GNOME y no hay extensión fiable que los replique.
- **La magnificación del dock** al pasar el ratón: Dash to Dock no la tiene.
  Haría falta un dock aparte tipo Plank.

Si la coherencia total importa más que mantener GNOME, KDE Plasma llega más
cerca del aspecto Mac porque el panel y las decoraciones son configurables de
raíz.

## Desinstalación

```bash
./uninstall.sh
```

Restaura los ajustes de GNOME, devuelve el dock de Ubuntu, deja Ptyxis como
estaba y recupera `~/.bashrc` desde la copia previa. Los temas y las extensiones
se quedan en el disco, así que reactivarlos es reejecutar `install.sh`.

## Créditos

Los temas son de [vinceliuice](https://github.com/vinceliuice): WhiteSur GTK,
iconos, cursores y fondos. Las extensiones son de sus respectivos autores y se
descargan desde extensions.gnome.org. Este repositorio solo orquesta la
instalación y aporta los parches a Spotlight.
