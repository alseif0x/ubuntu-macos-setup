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
dock.location = "bottom";
dock.height = 64;
dock.alignment = "center";
dock.lengthMode = "fit";
dock.hiding = "autohide";
dock.floating = true;
dock.currentConfigGroup = ["General"];
dock.writeConfig("macosSetupRole", "dock");
var tasks = ensure(dock, "org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", ["applications:org.kde.dolphin.desktop", "applications:google-chrome.desktop", "applications:org.kde.konsole.desktop", "applications:org.kde.kate.desktop", "applications:chatgpt.desktop", "applications:com.anthropic.Claude.desktop", "applications:systemsettings.desktop"]);
tasks.writeConfig("maxStripes", 1);
tasks.writeConfig("unhideOnAttention", false);
tasks.writeConfig("showToolTips", true);
ensure(dock, "org.kde.plasma.trash");

var ds = desktops();
for (var i = 0; i < ds.length; ++i) {
    ds[i].wallpaperPlugin = "org.kde.image";
    ds[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    ds[i].writeConfig("Image", "file://" + userDataPath("pictures") + "/Fondos-WhiteSur/Sonoma-light.jpg");
}
print("Panel superior " + top.id + ", dock " + dock.id);
