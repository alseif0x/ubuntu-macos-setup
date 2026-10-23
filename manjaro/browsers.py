#!/usr/bin/env python3
"""Barras compactas con pestañas integradas en Chrome y Firefox."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

HOME = Path.home()
STATE = HOME / '.local/state/macos-setup'
SAVED = STATE / 'browser-appearance.json'
MARKER = '// macos-setup: barra de título del sistema'

def chrome_pids():
    result = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            args = (proc / 'cmdline').read_bytes().split(b'\0')
            if args and Path(os.fsdecode(args[0])).name in {'chrome', 'google-chrome'} and not any(a.startswith(b'--type=') for a in args):
                result.append(int(proc.name))
        except (OSError, ValueError):
            pass
    return result

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.appearance-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, separators=(',', ':'))
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()

def configure(restore=False):
    STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
    saved = json.loads(SAVED.read_text()) if SAVED.exists() else {'chrome': {}, 'firefox': {}}
    if chrome_pids():
        print('Chrome abierto: ejecutar browsers.py --restart-chrome cuando se pueda reiniciar.')
    else:
        for prefs in (HOME / '.config/google-chrome').glob('*/Preferences'):
            key = str(prefs.relative_to(HOME))
            data = json.loads(prefs.read_text())
            browser = data.setdefault('browser', {})
            if restore:
                if key not in saved['chrome']:
                    continue
                old = saved['chrome'][key]
                if old['present']:
                    browser['custom_chrome_frame'] = old['value']
                else:
                    browser.pop('custom_chrome_frame', None)
                if 'theme' in old:
                    data.setdefault('extensions', {})['theme'] = old['theme']
            else:
                saved['chrome'].setdefault(key, {'present': 'custom_chrome_frame' in browser,
                                                'value': browser.get('custom_chrome_frame')})
                theme = data.setdefault('extensions', {}).setdefault('theme', {})
                saved['chrome'][key].setdefault('theme', dict(theme))
                browser['custom_chrome_frame'] = True
                theme['id'] = ''
                theme['system_theme'] = 1
                save_json(SAVED, saved)
            save_json(prefs, data)
            print('Chrome: pestañas integradas y tema GTK configurados.')
    for base in [HOME / '.mozilla/firefox', HOME / '.config/mozilla/firefox']:
        for prefs in base.glob('*/prefs.js'):
            user = prefs.parent / 'user.js'
            key = str(user.relative_to(HOME))
            if restore:
                if key not in saved['firefox']:
                    continue
                old = saved['firefox'][key]
                if old is None:
                    user.unlink(missing_ok=True)
                else:
                    user.write_text(old)
            else:
                text = user.read_text() if user.exists() else ''
                saved['firefox'].setdefault(key, text if user.exists() else None)
                save_json(SAVED, saved)
                if MARKER not in text:
                    user.write_text(text + '\n' + MARKER + '\nuser_pref("browser.tabs.inTitlebar", 1);\n')
                else:
                    user.write_text(text.replace(MARKER+'\nuser_pref("browser.tabs.inTitlebar", 0);', MARKER+'\nuser_pref("browser.tabs.inTitlebar", 1);'))
                print('Firefox: pestañas integradas, sin una barra de título adicional.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart-chrome', action='store_true', help='Cerrar Chrome normalmente y restaurar sus pestañas; guardar formularios antes.')
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    running = chrome_pids()
    if args.restart_chrome and running:
        for pid in running:
            os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 30
        while chrome_pids() and time.monotonic() < deadline:
            time.sleep(0.2)
        if chrome_pids():
            raise SystemExit('Chrome no se ha cerrado; no se modifican sus preferencias ni se fuerza el cierre.')
    configure(args.restore)
    if args.restart_chrome and running:
        subprocess.Popen(['google-chrome-stable', '--restore-last-session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
