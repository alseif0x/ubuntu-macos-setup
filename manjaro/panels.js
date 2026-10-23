// Reutilizar paneles conserva bandeja, redes, batería y demás preferencias.
var all = panels();
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
    if (ordered.indexOf(kept[i].id) === -1 && kept[i].id !== tray.id && kept[i].id !== clock.id)
        ordered.push(kept[i].id);
}
ordered.push(tray.id, clock.id);
top.currentConfigGroup = ["General"];
top.writeConfig("AppletOrder", ordered.join(";"));

if (!dock) dock = new Panel;
// Wave Task (manjaro/plugins.sh) añade la magnificación de macOS; sin él se usa
// el gestor de tareas de KDE. Wave Task dibuja su propio fondo y necesita altura
// para que el zoom no se recorte, por eso el panel queda transparente.
var wave = knownWidgetTypes.indexOf("org.vicko.wavetask") !== -1;
dock.location = "bottom";
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
// Launchpad: cuadrícula de aplicaciones a pantalla completa, antes de los lanzadores.
var launchpad = ensure(dock, "org.kde.plasma.kickerdash");
launchpad.currentConfigGroup = ["General"];
launchpad.writeConfig("icon", "view-app-grid");
var taskType = wave ? "org.vicko.wavetask" : "org.kde.plasma.icontasks";
var stale = dock.widgets();
for (var i = 0; i < stale.length; ++i) {
    var type = stale[i].type;
    if ((type === "org.kde.plasma.icontasks" || type === "org.vicko.wavetask") && type !== taskType)
        stale[i].remove();
}
var tasks = ensure(dock, taskType);
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", ["applications:org.kde.dolphin.desktop", "applications:google-chrome.desktop", "applications:org.kde.konsole.desktop", "applications:org.kde.kate.desktop", "applications:chatgpt.desktop", "applications:com.anthropic.Claude.desktop", "applications:systemsettings.desktop"]);
tasks.writeConfig("maxStripes", 1);
tasks.writeConfig("unhideOnAttention", false);
tasks.writeConfig("showToolTips", true);
if (wave) {
    tasks.writeConfig("skinName", "Big Sur Light");
    tasks.writeConfig("iconSize", 48);
    tasks.writeConfig("showReflection", false);
}
var separator = ensure(dock, "org.kde.plasma.marginsseparator");
var trash = ensure(dock, "org.kde.plasma.trash");
dock.currentConfigGroup = ["General"];
dock.writeConfig("AppletOrder", [launchpad.id, tasks.id, separator.id, trash.id].join(";"));

var ds = desktops();
for (var i = 0; i < ds.length; ++i) {
    ds[i].wallpaperPlugin = "org.kde.image";
    ds[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    ds[i].writeConfig("Image", "file://" + userDataPath("pictures") + "/Fondos-WhiteSur/Sonoma-light.jpg");
}
print("Panel superior " + top.id + ", dock " + dock.id);
