# WhiteSur en Manjaro KDE Plasma 6

Esta rama mantiene el instalador Ubuntu/GNOME y añade una ruta independiente
para Manjaro/Arch con Plasma 6 en la sesión del usuario actual.

```bash
./install-manjaro.sh
```

`./install.sh` también detecta una sesión KDE y redirige a este instalador;
`./uninstall.sh` redirige a la restauración. La ruta Ubuntu sigue disponible
en sesiones GNOME.

Instala Kvantum Qt6/Qt5, Inter y herramientas desde los repositorios mediante
una actualización completa con pacman. Los temas se instalan solo para el
usuario desde los repositorios de vinceliuice en `~/.themes-src`. Se registra
el commit de cada fuente en `~/.local/state/macos-setup/sources.json`.
Los repositorios ya descargados se reutilizan sin actualizarlos automáticamente.

## Resultado

- WhiteSur claro para Plasma, Qt/Kvantum y GTK/libadwaita.
- Decoración nativa Klassy con preset Eaten Fruits y recorte real del contenido
  en las cuatro esquinas. Evita la banda inferior de las decoraciones SVG.
- Iconos WhiteSur, cursores y fondo Sonoma.
- Botones cerrar/minimizar/maximizar pequeños (≈12 px) a la izquierda, barra de
  título compacta y sin borde inferior añadido.
- Las ventanas maximizadas tienen una barra de título opaca. La transparencia
  suave queda limitada a los títulos de ventanas flotantes; las aplicaciones
  Qt no reducen la opacidad de todo su contenido.
- Panel superior con Tux mordido (adaptado de Papirus), menú global, bandeja y reloj a la derecha.
- Dock flotante inferior centrado con ocultación automática; aparece al acercar
  el puntero al borde inferior. Incluye los lanzadores habituales.
  Los avisos de aplicaciones no mantienen el dock desplegado; las notificaciones
  siguen disponibles en la bandeja superior.
  La activación del borde es inmediata, sin brillo azul ni resistencia al puntero.
- KRunner flotante mediante Super+Espacio y Alt+Espacio.
- Launchpad (cuadrícula de aplicaciones) al inicio del dock y separador antes
  de la papelera.
- Mission Control con Ctrl+↑ (también Super+W) y Exposé de la aplicación
  con Ctrl+↓. La esquina superior izquierda ya no abre la vista general.
- Alt+Tab con iconos grandes y una entrada por ventana. Agrupar por aplicación
  juntaría las apps instaladas de Chrome con Chrome: KWin las considera la misma
  aplicación porque comparten proceso. Alt+` recorre las ventanas de la
  aplicación actual.
- Minimizar con efecto genio (Magic Lamp) y escritorios virtuales en una fila.
- GTK 4 usa el mismo tema, iconos y tipografía que GTK 3.
- Dock con magnificación al estilo macOS mediante Wave Task, con skins propios
  (`manjaro/wavetask-skins`) claro y oscuro que siguen el modo del sistema,
  si está instalado; si no, se usa el gestor de tareas de KDE. Con Wave Task,
  Launchpad y la papelera son lanzadores del propio dock y el applet de
  Launchpad pasa a la barra superior, junto a la bandeja.
- Gestos de tres dedos con InputActions: arriba Mission Control, abajo Exposé
  de la aplicación, izquierda/derecha cambian de escritorio
  (`manjaro/inputactions.yaml`).
- El menú de Konsole aparece en la barra superior.
- Cerrar la tapa bloquea la sesión sin suspender, y no hay suspensión automática
  por inactividad salvo con batería baja: los procesos siguen en marcha.
- Touchpad con curva de aceleración continua estilo Windows (`manjaro/touchpad-curve`):
  KWin 6.7 no ofrece el perfil personalizado de libinput, así que una pequeña
  biblioteca precargada en KWin lo aplica al configurar el touchpad. Más fino al
  ir despacio y sin el salto brusco del perfil adaptativo por encima de ~130 mm/s.
  También aplica a los ratones (claves `mouse_*`): de 0,5 a 2 px por punto del
  sensor según la velocidad, en lugar de los 2 px/punto casi constantes de libinput.
  Se ajusta en `~/.config/macos-setup/touchpad-curve.conf`; sin ese archivo no
  hace nada. `touchpad-curve/install.sh --remove` lo desinstala.
- El vídeo flotante «Imagen en imagen» de Chrome/Firefox queda siempre encima
  (regla de KWin; en Wayland el navegador no puede pedirlo).
- Dolphin como Finder: iconos con miniaturas, carpetas primero y sin archivos
  ocultos (Ctrl+H los muestra). «Vista rápida» en el menú contextual con Kiview;
  Dolphin aún no permite asignarla a la barra espaciadora. F11 muestra el panel
  de previsualización.
- Modo claro/oscuro automático según la hora: dos temas globales propios
  (`org.macossetup.light/dark`) que conservan Klassy, fondo Sonoma con variante
  oscura y un vigilante (`macos-appearance.path`) que alterna GTK. Konsole se
  queda siempre claro para que Claude Code, Codex, etc. se lean bien.
  El horario se configura en Preferencias > Tema global.
- Firefox con el tema WhiteSur (botones a la izquierda). Requiere Firefox cerrado
  durante la instalación.
- Sonidos de elementary, suaves y de estilo macOS. Los sonidos de Apple no se
  incluyen porque no son redistribuibles.
- `manjaro/system.sh` (root): inicio de sesión SDDM WhiteSur con el fondo Sonoma
  y arranque Plymouth `bgrt` (logo del fabricante), que admite la contraseña de
  cifrado LUKS. Guarda el tema de arranque anterior para restaurarlo.
- Perfil claro macOS Basic en Konsole, conservando Zsh y sus ajustes.
- Chrome y Firefox conservan las pestañas integradas, sin otra fila de título.
  Chrome usa el tema GTK de WhiteSur. Los cambios se aplican con el navegador
  cerrado; el instalador no cierra navegadores automáticamente. Para reiniciar
  Chrome guardando las pestañas: `python3 manjaro/browsers.py --restart-chrome`.

## Plugins compilados

`manjaro/plugins.sh install` compila como usuario e instala con pacman Klassy,
Wave Task e InputActions. Los PKGBUILD de AUR están revisados y copiados en
`manjaro/aur` (commit de origen en `manjaro/aur/SOURCES`), con el SHA256 del
código fijado. Al estar compilados contra KWin/Plasma, se instala un hook de
pacman y el servicio `macos-setup-rebuild.service`, que los recompilan solos
tras cada actualización de KDE (también con la actualización diaria). Los
cambios se cargan en el siguiente inicio de sesión.

## Atajos tipo Cmd (opcional)

Para Cmd+C/Cmd+V, Cmd+Q, etc. se recomienda [Toshy](https://github.com/RedBearAK/toshy),
que reasigna modificadores por aplicación (en terminales conserva Ctrl). En un
teclado de PC, Alt pasa a ser Cmd. Su instalador es interactivo y se ejecuta aparte:

```bash
curl -L -o /tmp/toshy.zip https://github.com/RedBearAK/toshy/archive/refs/heads/main.zip
cd /tmp && unzip -o toshy.zip && cd toshy-main && ./setup_toshy.py install
```

Se desactiva desde su icono de la bandeja y se desinstala con `./setup_toshy.py uninstall`.

Klassy 6.7.3 se compila como usuario normal desde el código oficial, con SHA256
fijado, y se instala como paquete pacman. El PKGBUILD está en `manjaro/klassy`.
La compilación usa dos tareas simultáneas. Requiere Plasma 6.6 o posterior.

No instala GNOME ni extensiones de GNOME, Latte, nuevos servicios, SDDM ni
fuentes propietarias de Apple. El menú global requiere soporte de cada aplicación.
Las aplicaciones que dibujan sus propias ventanas pueden conservar su aspecto.
El prompt de Zsh se conserva. En sesiones con varios monitores se transforma
un panel principal, conservando los demás, y se aplica el fondo a los escritorios.

## Restaurar

Antes de cambiar la configuración se guarda una copia inicial, que no se
sobrescribe al repetir el instalador, en `~/.local/state/macos-setup/kde-backup`.

```bash
./install-manjaro.sh --restore
```

La restauración detiene y vuelve a iniciar únicamente Plasma Shell; después
conviene cerrar sesión y entrar para recargar todos los atajos, cursores y estilos.
Restaura los archivos completos guardados, por lo que también revierte otros
ajustes posteriores en esos mismos archivos. Los paquetes y temas permanecen
instalados. No toca archivos personales, claves SSH ni la configuración de Drive.
Para restaurar también las preferencias de Chrome, ciérralo antes de restaurar.

`--skip-packages` permite repetir la instalación si las dependencias ya existen.
