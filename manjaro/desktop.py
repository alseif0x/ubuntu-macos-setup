#!/usr/bin/env python3
"""Copia recuperable y ajustes nativos de Plasma 6; nunca lee credenciales."""
from datetime import datetime
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
    '.config/dolphinrc',
    '.config/kscreenlockerrc',
    '.local/share/kio/servicemenus/macos-quicklook.desktop',
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

# Dolphin 24.05+ guarda la vista común en un atributo extendido, no en .directory.
DOLPHIN_GLOBAL = HOME / '.local/share/dolphin/view_properties/global'
DOLPHIN_XATTR = 'user.kde.fm.viewproperties#1'
DOLPHIN_SAVED = STATE / 'dolphin-global-viewprops'

def finder():
    """Dolphin como Finder: iconos con miniaturas, sin ocultos y Vista rápida."""
    DOLPHIN_GLOBAL.mkdir(parents=True, exist_ok=True)
    if not DOLPHIN_SAVED.exists():
        try:
            DOLPHIN_SAVED.write_bytes(os.getxattr(DOLPHIN_GLOBAL, DOLPHIN_XATTR))
        except OSError:
            DOLPHIN_SAVED.write_bytes(b'')
    stamp = datetime.now().strftime('%Y,%m,%d,%H,%M,%S.000')
    props = (f'[Dolphin]\nPreviewsShown=true\nSortFoldersFirst=true\nTimestamp={stamp}\n'
             'Version=4\nViewMode=0\n\n[Settings]\nHiddenFilesShown=false\n')
    os.setxattr(DOLPHIN_GLOBAL, DOLPHIN_XATTR, props.encode())
    write('dolphinrc', 'General', 'GlobalViewProps', 'true')
    # Vista rápida con Kiview (manjaro/plugins.sh); Dolphin aún no permite la barra espaciadora.
    menu = HOME / '.local/share/kio/servicemenus/macos-quicklook.desktop'
    if shutil.which('kiview'):
        menu.parent.mkdir(parents=True, exist_ok=True)
        menu.write_text('[Desktop Entry]\nType=Service\nMimeType=all/all;\nActions=quicklook\n'
                        'X-KDE-Priority=TopLevel\nX-KDE-RequiredNumberOfUrls=1\n\n'
                        '[Desktop Action quicklook]\nName=Vista rápida\nIcon=view-preview\n'
                        'Exec=kiview -s %f\n')
        menu.chmod(0o755)
    elif menu.exists():
        menu.unlink()

def copy_into_backup(relative):
    source, dest = HOME / relative, BACKUP / relative
    if not (source.exists() or source.is_symlink()):
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, dest, symlinks=True)
    else:
        shutil.copy2(source, dest, follow_symlinks=False)
    return True

def backup():
    manifest_path = BACKUP / 'manifest.json'
    if manifest_path.exists():
        # Una versión nueva puede gestionar más archivos: añadirlos antes de tocarlos.
        manifest = json.loads(manifest_path.read_text())
        added = [relative for relative in FILES if relative not in manifest['files']]
        for relative in added:
            manifest['files'].append(relative)
            if copy_into_backup(relative):
                manifest['present'].append(relative)
        if added:
            manifest_path.write_text(json.dumps(manifest, indent=2))
        print('Conservando copia inicial:', BACKUP, f'(+{len(added)} archivos)' if added else '')
        return
    BACKUP.mkdir(parents=True, mode=0o700, exist_ok=True)
    present = [relative for relative in FILES if copy_into_backup(relative)]
    manifest_path.write_text(json.dumps({'files': FILES, 'present': present,
                                         'krunner_shortcuts': runner_shortcuts()}, indent=2))
    print('Copia guardada:', BACKUP)

def restore():
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    if 'krunner_shortcuts' in manifest:
        runner_shortcuts(manifest['krunner_shortcuts'])
    kwin_shortcuts(restore=True)
    if DOLPHIN_SAVED.exists():
        saved = DOLPHIN_SAVED.read_bytes()
        if saved:
            os.setxattr(DOLPHIN_GLOBAL, DOLPHIN_XATTR, saved)
        else:
            try:
                os.removexattr(DOLPHIN_GLOBAL, DOLPHIN_XATTR)
            except OSError:
                pass
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
    # Tema de Firefox de WhiteSur: enlaces chrome de cada perfil (user.js lo repone browsers.py).
    for chrome in (HOME / '.mozilla/firefox').glob('*/chrome'):
        if chrome.is_symlink() and chrome.resolve().name == 'firefox-themes':
            chrome.unlink()
    run('python3', str(HERE / 'browsers.py'), '--restore')
    run('python3', str(HERE / 'appearance.py'), 'uninstall')
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
    finder()
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
        # InputActions es un efecto de KWin: no viene activado por defecto.
        ('kwinrc', 'Plugins', 'kwin_gesturesEnabled', 'true'),
        ('kwinrc', 'TabBox', 'LayoutName', 'big_icons'),
        ('kwinrc', 'TabBox', 'ApplicationsMode', '1'),
        ('kwinrc', 'TabBox', 'HighlightWindows', 'false'),
        # Sonidos suaves de elementary (system.sh); los de Apple no son redistribuibles.
        ('kdeglobals', 'Sounds', 'Theme', 'elementary'),
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
                       'gtk-decoration-layout':'close,minimize,maximize:',
                       'gtk-sound-theme-name':'elementary'}.items():
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
    if (Path('/usr/lib/qt6/plugins/kwin/effects/plugins/kwin_gestures.so')).exists():
        run('qdbus6', 'org.kde.KWin', '/Effects', 'org.kde.kwin.Effects.loadEffect', 'kwin_gestures')
    panels = (HERE / 'panels.js').read_text()
    panels = panels.replace('__TUX_ICON__', str(icons / 'tux-bitten.svg'))
    # Respetar el directorio de Imágenes aunque el usuario lo tenga personalizado.
    # Paquete Sonoma con variante oscura (appearance.py); Plasma alterna el fondo solo.
    run('python3', str(HERE / 'appearance.py'), 'install', str(pictures))
    panels = panels.replace('userDataPath("pictures") + "/Fondos-WhiteSur/Sonoma-light.jpg"',
                            json.dumps(str(HOME / '.local/share/wallpapers/Sonoma')))
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
