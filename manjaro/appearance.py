#!/usr/bin/env python3
"""Modo claro/oscuro automático como en macOS.

Plasma cambia entre dos temas globales propios según la hora (amanecer y
atardecer, configurable en Preferencias > Tema global). Esos temas solo tocan
colores, iconos, estilo de Plasma y Kvantum: conservan Klassy, a diferencia del
tema global de WhiteSur, que trae su decoración Aurorae. El fondo es un paquete
con variante oscura, que Plasma alterna solo. Lo que Plasma no cambia (GTK 3 y
Konsole) lo sincroniza `sync`, lanzado por una unidad .path al cambiar kdeglobals.

    appearance.py install PICTURES_DIR   instalar temas, fondo y vigilante
    appearance.py sync                   aplicar GTK/Konsole según el esquema actual
    appearance.py uninstall              quitarlo (lo usa desktop.py restore)
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HOME = Path.home()
HERE = Path(__file__).resolve().parent
LIB = HOME / '.local/lib/macos-setup'
STATE = HOME / '.local/state/macos-setup/appearance'
LNF = HOME / '.local/share/plasma/look-and-feel'
WALLPAPER = HOME / '.local/share/wallpapers/Sonoma'
UNITS = HOME / '.config/systemd/user'

VARIANTS = {
    'light': {'name': 'macOS claro', 'colors': 'WhiteSur', 'icons': 'WhiteSur-light',
              'style': 'kvantum', 'plasma': 'WhiteSur-alt', 'gtk': 'WhiteSur-Light',
              'konsole': 'MacOS-Basic', 'whitesur': 'com.github.vinceliuice.WhiteSur-alt'},
    'dark': {'name': 'macOS oscuro', 'colors': 'WhiteSurDark', 'icons': 'WhiteSur-dark',
             'style': 'kvantum-dark', 'plasma': 'WhiteSur-dark', 'gtk': 'WhiteSur-Dark',
             'konsole': 'MacOS-Dark', 'whitesur': 'com.github.vinceliuice.WhiteSur-dark'},
}

def run(*args, check=True, capture=False):
    return subprocess.run(args, check=check, text=True, capture_output=capture)

def write(file, group, key, value):
    run('kwriteconfig6', '--file', str(file), '--group', group, '--key', key, str(value))

def look_and_feel(variant, v):
    package = LNF / f'org.macossetup.{variant}'
    contents = package / 'contents'
    if package.exists():
        shutil.rmtree(package)
    contents.mkdir(parents=True)
    (package / 'metadata.json').write_text(json.dumps({
        'KPackageStructure': 'Plasma/LookAndFeel',
        'KPlugin': {'Id': f'org.macossetup.{variant}', 'Name': v['name'],
                    'Description': 'WhiteSur con decoración Klassy (macos-setup)',
                    'Authors': [{'Name': 'ubuntu-macos-setup'}], 'License': 'GPL-3.0'},
        'X-KDE-fallbackPackage': 'org.kde.breeze.desktop',
        'X-Plasma-MainScript': 'defaults',
        'X-Plasma-APIVersion': '2',
    }, indent=2, ensure_ascii=False))
    (contents / 'defaults').write_text(
        f"[kcminputrc][Mouse]\ncursorTheme=WhiteSur-cursors\n\n"
        f"[kdeglobals][General]\nColorScheme={v['colors']}\n\n"
        f"[kdeglobals][Icons]\nTheme={v['icons']}\n\n"
        f"[kdeglobals][KDE]\nwidgetStyle={v['style']}\n\n"
        "[kwinrc][WindowSwitcher]\nLayoutName=big_icons\n\n"
        "[kwinrc][org.kde.kdecoration2]\nButtonsOnLeft=XIA\nButtonsOnRight=\n"
        "library=org.kde.klassy\ntheme=\n\n"
        f"[plasmarc][Theme]\nname={v['plasma']}\n")
    # Pantalla de inicio y de cierre de sesión de WhiteSur; el resto, de Breeze.
    for part in ['splash', 'logout', 'previews']:
        source = LNF / v['whitesur'] / 'contents' / part
        if source.exists():
            (contents / part).symlink_to(source)

def kvantum_dark():
    """Variante oscura de WhiteSur-Compact, que Kvantum usa con el estilo kvantum-dark."""
    base, compact = HOME / '.config/Kvantum/WhiteSur', HOME / '.config/Kvantum/WhiteSur-Compact'
    compact.mkdir(parents=True, exist_ok=True)
    for extension in ['svg', 'kvconfig']:
        shutil.copy2(base / f'WhiteSurDark.{extension}', compact / f'WhiteSur-CompactDark.{extension}')
    config = compact / 'WhiteSur-CompactDark.kvconfig'
    # Mismos ajustes que la variante clara en desktop.py.
    for key, value in [('frame', 'false'), ('frame.top', '0'), ('frame.bottom', '0')]:
        run('kwriteconfig6', '--file', str(config), '--group', 'Window', '--key', key, value)
    for key, value in [('translucent_windows', 'false'), ('reduce_window_opacity', '0')]:
        run('kwriteconfig6', '--file', str(config), '--group', '%General', '--key', key, value)

def wallpaper(pictures):
    """Paquete de fondo con images/ e images_dark/: Plasma elige según el esquema."""
    walls = Path(pictures) / 'Fondos-WhiteSur'
    if WALLPAPER.exists():
        shutil.rmtree(WALLPAPER)
    for folder, name in [('images', 'Sonoma-light.jpg'), ('images_dark', 'Sonoma-dark.jpg')]:
        target = WALLPAPER / 'contents' / folder
        target.mkdir(parents=True)
        (target / '3840x3840.jpg').symlink_to(walls / name)
    (WALLPAPER / 'metadata.json').write_text(json.dumps({
        'KPlugin': {'Id': 'Sonoma', 'Name': 'Sonoma (claro/oscuro)',
                    'Authors': [{'Name': 'WhiteSur wallpapers'}], 'License': 'GPL-3.0'}}, indent=2))
    # Pantalla de bloqueo con el mismo fondo.
    run('kwriteconfig6', '--file', 'kscreenlockerrc', '--group', 'Greeter', '--group', 'Wallpaper',
        '--group', 'org.kde.image', '--group', 'General', '--key', 'Image', f'file://{WALLPAPER}')
    return WALLPAPER

def konsole_dark():
    light = (HERE / 'MacOS-Basic.colorscheme').read_text()
    dark = (light.replace('Description=macOS Terminal Basic', 'Description=macOS Terminal Basic (oscuro)')
                 .replace('[Background]\nColor=255,255,255', '[Background]\nColor=30,30,30')
                 .replace('[Foreground]\nColor=0,0,0', '[Foreground]\nColor=255,255,255'))
    target = HOME / '.local/share/konsole'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'MacOS-Dark.colorscheme').write_text(dark)

def watcher():
    LIB.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / 'appearance.py', LIB / 'appearance.py')
    UNITS.mkdir(parents=True, exist_ok=True)
    (UNITS / 'macos-appearance.path').write_text(
        '[Unit]\nDescription=Vigilar el esquema de color de Plasma (macos-setup)\n\n'
        '[Path]\nPathChanged=%h/.config/kdeglobals\n\n[Install]\nWantedBy=default.target\n')
    (UNITS / 'macos-appearance.service').write_text(
        '[Unit]\nDescription=Sincronizar GTK y Konsole con el modo claro/oscuro (macos-setup)\n\n'
        f'[Service]\nType=oneshot\nExecStart=/usr/bin/python3 {LIB / "appearance.py"} sync\n')
    run('systemctl', '--user', 'daemon-reload')
    run('systemctl', '--user', 'enable', '--now', 'macos-appearance.path')

def is_night():
    """Consulta el horario de Plasma (knighttimed): cada ciclo es (mediodía,
    inicio y fin del amanecer, inicio y fin del atardecer) en milisegundos."""
    import time
    import dbus
    manager = dbus.Interface(dbus.SessionBus().get_object(
        'org.kde.NightTime', '/org/kde/NightTime/Manager'), 'org.kde.NightTime.Manager')
    data = manager.Subscribe(dbus.Dictionary({}, signature='sv'))
    manager.Unsubscribe(data['Cookie'])
    now = time.time() * 1000
    return not any(cycle[2] <= now < cycle[3] for cycle in data['Schedule'][1])

def install(pictures):
    for variant, v in VARIANTS.items():
        look_and_feel(variant, v)
    kvantum_dark()
    konsole_dark()
    wallpaper(pictures)
    for key, value in [('AutomaticLookAndFeel', 'true'),
                       ('DefaultLightLookAndFeel', 'org.macossetup.light'),
                       ('DefaultDarkLookAndFeel', 'org.macossetup.dark')]:
        write('kdeglobals', 'KDE', key, value)
    watcher()
    # desktop.py acaba de escribir los valores claros: forzar la sincronización.
    STATE.unlink(missing_ok=True)
    sync()
    # desktop.py deja el modo claro; de noche, pasar ya al oscuro (el vigilante sigue).
    try:
        night = is_night()
    except Exception as error:  # sin knighttimed se queda en claro hasta el próximo cambio
        print('Horario de Plasma no disponible:', error)
        night = False
    if night:
        run('plasma-apply-lookandfeel', '-a', 'org.macossetup.dark')

def uninstall():
    run('systemctl', '--user', 'disable', '--now', 'macos-appearance.path', check=False)
    for path in [UNITS / 'macos-appearance.path', UNITS / 'macos-appearance.service',
                 LIB / 'appearance.py', STATE]:
        path.unlink(missing_ok=True)
    for path in [LNF / 'org.macossetup.light', LNF / 'org.macossetup.dark', WALLPAPER]:
        shutil.rmtree(path, ignore_errors=True)
    run('systemctl', '--user', 'daemon-reload', check=False)

def sync():
    scheme = run('kreadconfig6', '--file', 'kdeglobals', '--group', 'General',
                 '--key', 'ColorScheme', capture=True).stdout.strip()
    variant = 'dark' if scheme.endswith('Dark') else 'light'
    if STATE.exists() and STATE.read_text() == variant:
        return
    v = VARIANTS[variant]
    for gtk in ['gtk-3.0', 'gtk-4.0']:
        settings = HOME / '.config' / gtk / 'settings.ini'
        for key, value in [('gtk-theme-name', v['gtk']), ('gtk-icon-theme-name', v['icons']),
                           ('gtk-application-prefer-dark-theme', str(variant == 'dark').lower())]:
            run('kwriteconfig6', '--file', str(settings), '--group', 'Settings', '--key', key, value)
    if shutil.which('gsettings'):
        for key, value in [('gtk-theme', v['gtk']), ('icon-theme', v['icons']),
                           ('color-scheme', 'prefer-dark' if variant == 'dark' else 'default')]:
            run('gsettings', 'set', 'org.gnome.desktop.interface', key, value, check=False)
    profile = HOME / '.local/share/konsole/MacOS-Basic.profile'
    if profile.exists():
        run('kwriteconfig6', '--file', str(profile), '--group', 'Appearance', '--key', 'ColorScheme', v['konsole'])
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(variant)
    print('Apariencia:', variant)

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'install':
        install(sys.argv[2])
    elif sys.argv[1:] == ['sync']:
        sync()
    elif sys.argv[1:] == ['uninstall']:
        uninstall()
    else:
        raise SystemExit('Uso: appearance.py install CARPETA_IMÁGENES | sync')
