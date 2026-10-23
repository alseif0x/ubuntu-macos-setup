#!/usr/bin/env python3
"""Copia recuperable y ajustes nativos de Plasma 6; nunca lee credenciales."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HOME = Path.home()
HERE = Path(__file__).resolve().parent
STATE = HOME / '.local/state/macos-setup'
BACKUP = STATE / 'kde-backup'
FILES = [
    '.config/kdeglobals', '.config/kwinrc', '.config/kcminputrc',
    '.config/plasma-org.kde.plasma.desktop-appletsrc', '.config/plasmashellrc',
    '.config/plasmarc', '.config/krunnerrc', '.config/kglobalshortcutsrc',
    '.config/konsolerc', '.config/Kvantum/kvantum.kvconfig',
    '.config/gtk-3.0/settings.ini', '.config/gtk-4.0', '.gtkrc-2.0',
    '.local/share/konsole/MacOS-Basic.profile',
    '.local/share/konsole/MacOS-Basic.colorscheme',
    '.local/share/applications/org.kde.konsole.desktop',
    '.config/klassy',
    '.config/inputactions/config.yaml',
    '.local/share/applications/macos-trash.desktop',
    '.local/share/applications/macos-launchpad.desktop',
]

def run(*args, capture=False):
    return subprocess.run(args, check=True, text=True, capture_output=capture)

def write(file, group, key, value):
    args = ['kwriteconfig6', '--file', str(file)]
    for name in group if isinstance(group, list) else [group]:
        args += ['--group', name]
    run(*args, '--key', key, str(value))

def shortcuts(action, keys=None):
    import dbus
    bus = dbus.SessionBus()
    interface = dbus.Interface(bus.get_object('org.kde.kglobalaccel', '/kglobalaccel'), 'org.kde.KGlobalAccel')
    action = dbus.Array(action, signature='s')
    if keys is None:
        return [int(key) for key in interface.shortcut(action)]
    interface.setShortcut(action, dbus.Array(keys, signature='i'), dbus.UInt32(4))

RUNNER = ['org.kde.krunner.desktop', '_launch', 'KRunner', 'Run Command']
# Mission Control (Ctrl+↑) y Exposé de la aplicación (Ctrl+↓), como en macOS.
KWIN_SHORTCUTS = {
    'Overview': ([0x10000057], [0x10000057, 0x04000000 | 0x01000013]),
    'ExposeClass': ([0x04000000 | 0x01000036, 0x10000000 | 0x01000036],
                    [0x04000000 | 0x01000036, 0x04000000 | 0x01000015]),
}

def runner_shortcuts(keys=None):
    return shortcuts(RUNNER, keys)

def kwin_shortcuts(restore=False):
    for name, (default, mac) in KWIN_SHORTCUTS.items():
        shortcuts(['kwin', name, 'KWin', name], default if restore else mac)

def window_theme():
    """Klassy recorta el cliente con KDecoration3, sin añadir un faldón SVG."""
    preset = Path('/usr/lib/qt6/plugins/org.kde.kdecoration3.kcm/klassydecoration/presets/Eaten_Fruits.klpw')
    if not preset.exists():
        raise RuntimeError('Falta Klassy: ejecutar el instalador completo antes de aplicar.')
    # El importador oficial distribuye los campos del preset entre sus grupos.
    run('klassy-settings', '--import-preset', str(preset))
    run('klassy-settings', '--load-windeco-preset', 'Eaten Fruits')
    target = HOME / '.config/klassy/klassyrc'
    for group, settings in {
        # Semáforos de unos 12 px y barra de 28 px, como en macOS.
        'Windeco': {'WindowCornerRadius': '10', 'RoundAllCornersWhenNoBorders': 'true',
                    'MatchTitleBarToApplicationColor': 'false', 'IconSize': 'IconSmall',
                    'ButtonSpacingLeft': '6', 'TitleBarTopMargin': '2', 'TitleBarBottomMargin': '2'},
        'ButtonSizing': {'ButtonSpacingLeft': '6'},
        'TitleBarSpacing': {'TitleBarTopMargin': '2', 'TitleBarBottomMargin': '2'},
        'TitleBarOpacity': {'TitleBarOpacityActive': '95', 'TitleBarOpacityInactive': '90',
                            'OverrideTitleBarOpacityActive': 'true',
                            'OverrideTitleBarOpacityInactive': 'true',
                            'OpaqueMaximizedTitleBars': 'true'},
        'ButtonColors': {'ButtonBackgroundOpacityActive': '100'},
        'WindowOutlineStyle': {'WindowOutlineStyleActive': 'WindowOutlineNone',
                               'WindowOutlineStyleInactive': 'WindowOutlineNone',
                               'WindowOutlineThickness': '0'},
    }.items():
        for key, value in settings.items():
            write(target, group, key, value)

def backup():
    if (BACKUP / 'manifest.json').exists():
        print('Conservando copia inicial:', BACKUP)
        return
    BACKUP.mkdir(parents=True, mode=0o700, exist_ok=True)
    present = []
    for relative in FILES:
        source, dest = HOME / relative, BACKUP / relative
        if source.exists() or source.is_symlink():
            dest.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir() and not source.is_symlink():
                shutil.copytree(source, dest, symlinks=True)
            else:
                shutil.copy2(source, dest, follow_symlinks=False)
            present.append(relative)
    (BACKUP / 'manifest.json').write_text(json.dumps({'files': FILES, 'present': present,
                                                    'krunner_shortcuts': runner_shortcuts()}, indent=2))
    print('Copia guardada:', BACKUP)

def restore():
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    if 'krunner_shortcuts' in manifest:
        runner_shortcuts(manifest['krunner_shortcuts'])
    kwin_shortcuts(restore=True)
    # Plasma guarda los paneles al salir: detenerlo antes de reponer su copia.
    run('systemctl', '--user', 'stop', 'plasma-plasmashell.service')
    try:
        for relative in manifest['files']:
            dest, source = HOME / relative, BACKUP / relative
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            elif dest.is_dir():
                shutil.rmtree(dest)
            if relative in manifest['present']:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir() and not source.is_symlink():
                    shutil.copytree(source, dest, symlinks=True)
                else:
                    shutil.copy2(source, dest, follow_symlinks=False)
    finally:
        run('systemctl', '--user', 'start', 'plasma-plasmashell.service')
    run('qdbus6', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure')
    run('python3', str(HERE / 'browsers.py'), '--restore')
    print('Restaurado. Cierra sesión y vuelve a entrar para recargar todos los ajustes y atajos.')

def apply():
    if not (BACKUP / 'manifest.json').exists():
        raise SystemExit('Primero ejecuta el paso backup.')
    pictures = Path(run('xdg-user-dir', 'PICTURES', capture=True).stdout.strip())
    if pictures == HOME:
        pictures = HOME / 'Pictures'
    walls = pictures / 'Fondos-WhiteSur'
    walls.mkdir(parents=True, exist_ok=True)
    for name in ['Sonoma-light.jpg', 'Sonoma-dark.jpg']:
        shutil.copy2(HOME / '.themes-src/WhiteSur-wallpapers/4k' / name, walls / name)

    window_theme()
    icons = HOME / '.local/share/icons'
    icons.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / 'assets/tux-bitten.svg', icons / 'tux-bitten.svg')
    run('plasma-apply-colorscheme', 'WhiteSur')
    run('plasma-apply-desktoptheme', 'WhiteSur-alt')
    # Aplicar componentes explícitos evita que un tema global sustituya paneles.
    for file, group, key, value in [
        ('kdeglobals', 'KDE', 'widgetStyle', 'kvantum'),
        ('kdeglobals', 'Icons', 'Theme', 'WhiteSur-light'),
        ('kdeglobals', 'General', 'font', 'Inter,11,-1,5,50,0,0,0,0,0'),
        ('kdeglobals', 'General', 'menuFont', 'Inter,11,-1,5,50,0,0,0,0,0'),
        ('kdeglobals', 'General', 'smallestReadableFont', 'Inter,9,-1,5,50,0,0,0,0,0'),
        ('kdeglobals', 'General', 'toolBarFont', 'Inter,10,-1,5,50,0,0,0,0,0'),
        ('kdeglobals', 'General', 'fixed', 'DejaVu Sans Mono,11,-1,5,50,0,0,0,0,0'),
        ('kcminputrc', 'Mouse', 'cursorTheme', 'WhiteSur-cursors'),
        ('kcminputrc', 'Mouse', 'cursorSize', '24'),
        ('kwinrc', 'org.kde.kdecoration2', 'library', 'org.kde.klassy'),
        ('kwinrc', 'org.kde.kdecoration2', 'theme', ''),
        ('kwinrc', 'org.kde.kdecoration2', 'ButtonsOnLeft', 'XIA'),
        ('kwinrc', 'org.kde.kdecoration2', 'ButtonsOnRight', ''),
        ('kwinrc', 'org.kde.kdecoration2', 'BorderSize', 'None'),
        ('kwinrc', 'org.kde.kdecoration2', 'BorderSizeAuto', 'false'),
        ('kwinrc', 'Plugins', 'blurEnabled', 'true'),
        ('kwinrc', 'Plugins', 'screenedgeEnabled', 'false'),
        ('kwinrc', 'Windows', 'ElectricBorderDelay', '0'),
        ('kwinrc', 'Windows', 'ElectricBorderCooldown', '150'),
        ('kwinrc', 'Windows', 'ElectricBorderPushbackPixels', '0'),
        # La esquina superior izquierda es el Tux: no abrir la vista general al ir a él.
        ('kwinrc', 'ElectricBorders', 'TopLeft', 'None'),
        ('kwinrc', 'Desktops', 'Rows', '1'),
        # Minimizar con efecto genio; Alt+Tab con iconos grandes, una entrada por aplicación.
        ('kwinrc', 'Plugins', 'magiclampEnabled', 'true'),
        ('kwinrc', 'Plugins', 'squashEnabled', 'false'),
        ('kwinrc', 'TabBox', 'LayoutName', 'big_icons'),
        ('kwinrc', 'TabBox', 'ApplicationsMode', '1'),
        ('kwinrc', 'TabBox', 'HighlightWindows', 'false'),
        ('krunnerrc', 'General', 'FreeFloating', 'true'),
        ('krunnerrc', 'General', 'RetainPriorSearch', 'false'),
        ('krunnerrc', 'General', 'historyBehavior', 'Disabled'),
    ]:
        write(file, group, key, value)
    (HOME / '.config/Kvantum').mkdir(parents=True, exist_ok=True)
    # El cliente Qt tampoco necesita el marco interior de 10 px del tema.
    compact = HOME / '.config/Kvantum/WhiteSur-Compact'
    compact.mkdir(parents=True, exist_ok=True)
    base = HOME / '.config/Kvantum/WhiteSur'
    for extension in ['svg', 'kvconfig']:
        shutil.copy2(base / ('WhiteSur.' + extension), compact / ('WhiteSur-Compact.' + extension))
    for key, value in [('frame', 'false'), ('frame.top', '0'), ('frame.bottom', '0')]:
        write(compact / 'WhiteSur-Compact.kvconfig', 'Window', key, value)
    for key, value in [('translucent_windows', 'false'), ('reduce_window_opacity', '0')]:
        write(compact / 'WhiteSur-Compact.kvconfig', '%General', key, value)
    write(HOME / '.config/Kvantum/kvantum.kvconfig', 'General', 'theme', 'WhiteSur-Compact')

    gtk = HOME / '.config/gtk-3.0/settings.ini'
    gtk.parent.mkdir(parents=True, exist_ok=True)
    for key, value in {'gtk-theme-name':'WhiteSur-Light', 'gtk-icon-theme-name':'WhiteSur-light',
                       'gtk-cursor-theme-name':'WhiteSur-cursors', 'gtk-font-name':'Inter 11',
                       'gtk-decoration-layout':'close,minimize,maximize:'}.items():
        write(gtk, 'Settings', key, value)
        # GTK 4 conservaba Breeze y Noto: las apps libadwaita no casaban con el resto.
        write(HOME / '.config/gtk-4.0/settings.ini', 'Settings', key, value)

    konsole = HOME / '.local/share/konsole'
    konsole.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / 'MacOS-Basic.colorscheme', konsole)
    shutil.copy2(HERE / 'MacOS-Basic.profile', konsole)
    write('konsolerc', 'Desktop Entry', 'DefaultProfile', 'MacOS-Basic.profile')
    run('python3', str(HERE / 'browsers.py'))

    # Sin barra de herramientas; el menú pasa a la barra superior (--hide-menubar
    # impediría que Konsole lo publique en el menú global).
    desktop = Path('/usr/share/applications/org.kde.konsole.desktop')
    if desktop.exists():
        target = HOME / '.local/share/applications/org.kde.konsole.desktop'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(desktop.read_text().replace('Exec=konsole', 'Exec=konsole --hide-toolbars'))

    # Gestos de tres dedos; se respeta un config.yaml propio del usuario.
    gestures = HOME / '.config/inputactions/config.yaml'
    marker = '# macos-setup:'
    if not gestures.exists() or not gestures.read_text().strip() or gestures.read_text().startswith(marker):
        gestures.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / 'inputactions.yaml', gestures)

    # Registrar el atajo en vivo: editar solo kglobalshortcutsrc no actualiza el daemon.
    runner_shortcuts([0x10000020, 0x08000020])
    kwin_shortcuts()
    run('qdbus6', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure')
    run('qdbus6', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.loadEffect', 'blur')
    run('qdbus6', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.unloadEffect', 'screenedge')
    run('qdbus6', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.unloadEffect', 'squash')
    run('qdbus6', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.loadEffect', 'magiclamp')
    panels = (HERE / 'panels.js').read_text()
    panels = panels.replace('__TUX_ICON__', str(icons / 'tux-bitten.svg'))
    # Respetar el directorio de Imágenes aunque el usuario lo tenga personalizado.
    panels = panels.replace('userDataPath("pictures") + "/Fondos-WhiteSur/Sonoma-light.jpg"', json.dumps(str(walls / 'Sonoma-light.jpg')))
    apps = HOME / '.local/share/applications'
    apps.mkdir(parents=True, exist_ok=True)
    (apps / 'macos-trash.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=Papelera\nIcon=user-trash\n'
        'Exec=dolphin trash:/\nCategories=System;\n')
    # Plasma reescribe AppletOrder al añadir applets nuevos: la segunda pasada,
    # ya sin altas, fija el orden definitivo.
    for _ in range(2):
        output = run('qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript',
                     panels, capture=True).stdout
    launchpad = next((line.split('=', 1)[1].strip() for line in output.splitlines()
                      if line.startswith('launchpad=')), None)
    entry = apps / 'macos-launchpad.desktop'
    if launchpad:
        # Abre el applet de Launchpad de la barra superior desde el dock de Wave Task.
        entry.write_text(
            '[Desktop Entry]\nType=Application\nName=Launchpad\nIcon=view-app-grid\n'
            'Exec=qdbus6 org.kde.kglobalaccel /component/plasmashell '
            f'org.kde.kglobalaccel.Component.invokeShortcut "activate widget {launchpad}"\n'
            'Categories=System;\n')
    elif entry.exists():
        entry.unlink()
    run('kbuildsycoca6', '--noincremental')
    # Recargar Shell aplica el orden de applets, iconos y tipografía en vivo.
    # Las ventanas abiertas y KWin siguen ejecutándose.
    run('systemctl', '--user', 'restart', 'plasma-plasmashell.service')
    print('WhiteSur aplicado a Plasma, GTK, ventanas, paneles, KRunner y Konsole.')

if __name__ == '__main__':
    if os.geteuid() == 0:
        raise SystemExit('Ejecuta como usuario normal.')
    mode = sys.argv[1] if len(sys.argv) == 2 else ''
    if mode not in {'backup', 'apply', 'restore'}:
        raise SystemExit('Uso: desktop.py backup|apply|restore')
    {'backup': backup, 'apply': apply, 'restore': restore}[mode]()
