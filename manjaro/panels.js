// Reutilizar paneles conserva bandeja, redes, batería y demás preferencias.
var all = panels();
// Wave Task (manjaro/plugins.sh) añade la magnificación de macOS; sin él se usa
// el gestor de tareas de KDE.
var wave = knownWidgetTypes.indexOf("org.vicko.wavetask") !== -1;
var top = null, dock = null;
for (var i = 0; i < all.length; ++i) {
    all[i].currentConfigGroup = ["General"];
    var role = all[i].readConfig("macosSetupRole", "");
    if (role === "top") top = all[i];
    if (role === "dock") dock = all[i];
}
if (!top) {
    for (var i = 0; i < all.length; ++i) {
        if (all[i].location === "bottom" || all[i].location === "top") { top = all[i]; break; }
    }
}
if (!top) top = new Panel;
top.location = "top";
top.height = 30;
top.lengthMode = "fill";
top.hiding = "none";
top.floating = false;
top.currentConfigGroup = ["General"];
top.writeConfig("macosSetupRole", "top");

var existing = top.widgets();
for (var i = 0; i < existing.length; ++i) {
    if (["org.kde.plasma.icontasks", "org.kde.plasma.marginsseparator", "org.kde.plasma.showdesktop", "org.kde.plasma.pager"].indexOf(existing[i].type) !== -1)
        existing[i].remove();
}
function ensure(panel, type) {
    var ws = panel.widgets();
    for (var j = 0; j < ws.length; ++j) if (ws[j].type === type) return ws[j];
    return panel.addWidget(type);
}
var launch = ensure(top, "org.kde.plasma.kickoff");
launch.currentConfigGroup = ["General"];
launch.writeConfig("icon", "__TUX_ICON__");
var menu = ensure(top, "org.kde.plasma.appmenu");
var spacer = ensure(top, "org.kde.plasma.panelspacer");
spacer.currentConfigGroup = ["General"];
spacer.writeConfig("expanding", true);
// Con Wave Task, los applets del dock quedarían fuera de su fondo: Launchpad
// vive en la barra superior (donde macOS tiene el Centro de control) y el dock
// lo abre mediante el atajo global del applet (macos-launchpad.desktop).
var launchpad = null;
var topWidgets = top.widgets();
for (var i = 0; i < topWidgets.length; ++i)
    if (!wave && topWidgets[i].type === "org.kde.plasma.kickerdash") topWidgets[i].remove();
if (wave) {
    launchpad = ensure(top, "org.kde.plasma.kickerdash");
    launchpad.currentConfigGroup = ["General"];
    launchpad.writeConfig("icon", "view-app-grid-symbolic");
    launchpad.globalShortcut = "Meta+Ctrl+Shift+F4";
}
var tray = ensure(top, "org.kde.plasma.systemtray");
var clock = ensure(top, "org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateFormat", "custom");
clock.writeConfig("customDateFormat", "ddd d MMM");
clock.writeConfig("use24hFormat", 2);
// En Plasma 6.7 Widget.index puede devolver -1: guardar el orden explícito.
var ordered = [launch.id, menu.id, spacer.id];
var kept = top.widgets();
for (var i = 0; i < kept.length; ++i) {
    var id = kept[i].id;
    if (ordered.indexOf(id) === -1 && id !== tray.id && id !== clock.id && !(launchpad && id === launchpad.id))
        ordered.push(id);
}
if (launchpad) ordered.push(launchpad.id);
ordered.push(tray.id, clock.id);
top.currentConfigGroup = ["General"];
top.writeConfig("AppletOrder", ordered.join(";"));

if (!dock) dock = new Panel;
// Wave Task dibuja su propio fondo y necesita altura para que el zoom no se
// recorte, por eso el panel queda transparente.
dock.location = "bottom";
// Wave Task coloca el fondo del skin con «altura del panel − 76»: sus skins
// están pensados para 86 px con iconos de 44 px. El zoom (44 × 1,6 ≈ 70 px) cabe.
dock.height = wave ? 86 : 64;
dock.alignment = "center";
dock.lengthMode = "fit";
dock.hiding = "autohide";
dock.floating = !wave;
dock.currentConfigGroup = ["General"];
dock.writeConfig("macosSetupRole", "dock");
// Igual que la plantilla de Wave Task: 4 oculta el fondo del tema.
if (wave) {
    dock.currentConfigGroup = [];
    dock.writeConfig("backgroundHints", 4);
    dock.writeConfig("userBackgroundHints", 4);
}
dock.currentConfigGroup = ["General"];
var stale = dock.widgets();
for (var i = 0; i < stale.length; ++i) {
    var type = stale[i].type;
    var taskManager = type === "org.kde.plasma.icontasks" || type === "org.vicko.wavetask";
    var applet = ["org.kde.plasma.kickerdash", "org.kde.plasma.marginsseparator", "org.kde.plasma.trash"].indexOf(type) !== -1;
    if ((taskManager && type !== (wave ? "org.vicko.wavetask" : "org.kde.plasma.icontasks")) || (wave && applet))
        stale[i].remove();
}
var launchers = ["applications:org.kde.dolphin.desktop", "applications:google-chrome.desktop", "applications:org.kde.konsole.desktop", "applications:org.kde.kate.desktop", "applications:chatgpt.desktop", "applications:com.anthropic.Claude.desktop", "applications:systemsettings.desktop"];
var tasks;
if (wave) {
    tasks = ensure(dock, "org.vicko.wavetask");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", ["applications:macos-launchpad.desktop"].concat(launchers, ["applications:macos-trash.desktop"]));
    // Skins propios (manjaro/wavetask-skins), claro u oscuro según el esquema
    // actual; appearance.py los alterna al cambiar de modo.
    var globals = ConfigFile("kdeglobals");
    globals.group = "General";
    var dark = /Dark$/.test(globals.readEntry("ColorScheme"));
    tasks.writeConfig("skinName", "__WAVE_SKINS__/macOS-" + (dark ? "Dark" : "Light"));
    tasks.writeConfig("iconSize", 44);
    tasks.writeConfig("magnification", 60);
    tasks.writeConfig("showReflection", false);
} else {
    // Launchpad: cuadrícula de aplicaciones a pantalla completa, antes de los lanzadores.
    var dash = ensure(dock, "org.kde.plasma.kickerdash");
    dash.currentConfigGroup = ["General"];
    dash.writeConfig("icon", "view-app-grid");
    tasks = ensure(dock, "org.kde.plasma.icontasks");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", launchers);
    var separator = ensure(dock, "org.kde.plasma.marginsseparator");
    var trash = ensure(dock, "org.kde.plasma.trash");
}
tasks.writeConfig("maxStripes", 1);
tasks.writeConfig("unhideOnAttention", false);
tasks.writeConfig("showToolTips", true);
dock.currentConfigGroup = ["General"];
dock.writeConfig("AppletOrder", (wave ? [tasks.id] : [dash.id, tasks.id, separator.id, trash.id]).join(";"));

var ds = desktops();
for (var i = 0; i < ds.length; ++i) {
    ds[i].wallpaperPlugin = "org.kde.image";
    ds[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    ds[i].writeConfig("Image", "file://" + userDataPath("pictures") + "/Fondos-WhiteSur/Sonoma-light.jpg");
}
print("Panel superior " + top.id + ", dock " + dock.id);
if (launchpad) print("\nlaunchpad=" + launchpad.id);
