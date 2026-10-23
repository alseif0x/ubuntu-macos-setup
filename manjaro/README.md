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

- WhiteSur claro para Plasma, ventanas Aurorae, Qt/Kvantum y GTK/libadwaita.
- Iconos WhiteSur, cursores y fondo Sonoma.
- Botones cerrar/minimizar/maximizar a la izquierda.
- Panel superior con lanzador, menú global, bandeja y reloj a la derecha.
- Dock flotante inferior centrado que esquiva ventanas; lanzadores habituales.
- KRunner flotante mediante Super+Espacio y Alt+Espacio.
- Perfil claro macOS Basic en Konsole, conservando Zsh y sus ajustes.

No instala GNOME ni extensiones de GNOME, Latte, nuevos servicios, SDDM ni
fuentes propietarias de Apple. El dock usa el applet nativo de tareas y no
incluye magnificación. El menú global requiere soporte de cada aplicación.
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

`--skip-packages` permite repetir la instalación si las dependencias ya existen.
