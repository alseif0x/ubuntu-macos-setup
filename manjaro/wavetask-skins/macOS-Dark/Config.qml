import QtQuick
// Dock de macOS: rectángulo redondeado translúcido que envuelve los iconos.
QtObject {
    property string imageTop: "bgt.png"
    property string imageBottom: "bg.png"
    property string imageLeft: "bgl.png"
    property string imageRight: "bgr.png"
    property string imagetask: "tasks.svgz"
    property bool blur: true
    property int blurRadius: 16
    property int positionTaskIndicator: 9
    property int leftMargin: 18
    property int topMargin: 18
    property int rightMargin: 18
    property int bottomMargin: 18
    property int outsideLeftMargin: 14
    property int outsideTopMargin: -5
    property int outsideRightMargin: 14
    property int outsideBottomMargin: -4
}
