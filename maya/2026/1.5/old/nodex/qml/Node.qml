// One node plate. Geometry (row y, heights, width) comes
// from model.describe() in Python, so wires and hit tests agree with what is drawn.
import QtQuick 2.15

Item {
    id: node
    property string nid: model.nid
    property var info: null
    readonly property var th: board.th
    readonly property bool selected: board.sel[nid] === true
    readonly property bool isLead: board.lead === nid
    readonly property bool dead: info ? info.dead : false
    readonly property bool simple: info ? info.rows.length === 0 : true
    readonly property bool dimmed: (board.isolate !== null && board.isolate.a !== nid && board.isolate.b !== nid)
                                   || (board.connectionFocus !== null && !board.connectionFocus.nodes[nid])
                                   || (board.query !== "" && info !== null && info.search.indexOf(board.query.toLowerCase()) < 0)
    readonly property color selColor: isLead ? th.selLead : th.selActive

    // a width being dragged on the right edge wins until the new info arrives.
    property real dragW: -1
    property real nameW: 0              // drawn width of the header name (double-click target)
    readonly property bool renaming: board.renaming === nid
    width: dragW > 0 ? dragW : (info ? info.width : 200)
    height: info ? info.height : 28
    opacity: dead ? 0.35 : (dimmed ? 0.38 : 1)
    z: selected ? 2 : 1

    // Culling: off-view nodes are not rendered (Board.cull() moves viewRect, throttled).
    readonly property rect vr: board.viewRect
    visible: x < vr.x + vr.width && x + width > vr.x && y - 20 < vr.y + vr.height && y + height > vr.y
    // Level of detail: a node is a plate + header + mouse until it is first seen at a readable
    // zoom; then its detail (shadow, glow, icon, name, buttons, rows) is built by the two
    // loaders below -- through the board's build queue, a few nodes a frame (59 nodes built at
    // once froze the board ~1 s when a zoom crossed `far`) -- and kept: zoomed out past `far`
    // it is only hidden, and greek bars (below) stand in for its text.
    // 600 full delegates took ~1.1 s to create; plates alone are nearly free.
    readonly property bool far: board.far
    property bool built: false
    function updBuilt() { if (!built && !board.far && visible) board.queueBuild(node) }
    onVisibleChanged: updBuilt()
    onFarChanged: updBuilt()

    Behavior on x { enabled: board.animate; NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
    Behavior on y { enabled: board.animate; NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: 150 } }
    onXChanged: board.wiresDirty()
    onYChanged: board.wiresDirty()
    onWidthChanged: board.wiresDirty()
    onHeightChanged: board.wiresDirty()
    onInfoChanged: { dragW = -1; board.wiresDirty() }
    onDimmedChanged: board.wiresDirty()

    Component.onCompleted: {
        var i = board.pendingInfo[nid]
        if (i === undefined) i = bridge.nodeInfo(nid)
        else delete board.pendingInfo[nid]
        info = i
        if (info) { x = info.x; y = info.y }
        updBuilt()
        board.registerNode(nid, node)
    }
    Component.onDestruction: board.unregisterNode(nid, node)

    property real selFade: selected ? 1 : 0
    Behavior on selFade { NumberAnimation { duration: 150; easing.type: Easing.OutQuad } }
    property color selTint: selColor
    Behavior on selTint { ColorAnimation { duration: 150 } }

    Loader {
        anchors.fill: parent
        active: node.built
        visible: !node.far
        sourceComponent: Component {
            Item {
                // Node type above the plate
                Text {
                    x: 2; y: -17
                    text: node.info ? node.info.type : ""
                    font.pixelSize: 11
                    color: node.selected ? th.muted : th.faint
                }

                // Soft shadow, no border
                Rectangle { x: -2; y: 3; width: parent.width + 4; height: parent.height + 5; radius: 9; color: "#000000"; opacity: 0.16 }
                Rectangle { x: 0; y: 1; width: parent.width; height: parent.height + 1; radius: 7; color: "#000000"; opacity: 0.28 }

                // Selection: a 1.5 px ring plus a soft 12-14 px glow at
                // 22% / 30%, fading in and changing colour over 150 ms (like a CSS box-shadow transition).
                // The glow is 1 px rings with a falling alpha: Maya's QtGraphicalEffects plugin does not
                // provide RectangularGlow outside the GUI, so nothing here depends on it.
                Repeater {
                    model: node.selFade > 0 ? (node.isLead ? 8 : 7) : 0
                    delegate: Rectangle {
                        readonly property real k: 1 - index / (node.isLead ? 8 : 7)
                        x: -1.5 - index; y: -1.5 - index
                        width: node.width + 3 + 2 * index; height: node.height + 3 + 2 * index
                        radius: 7.5 + index
                        color: "transparent"
                        border.width: 1
                        border.color: node.selTint
                        antialiasing: true
                        opacity: node.selFade * (node.isLead ? 0.30 : 0.22) * k * k
                    }
                }
            }
        }
    }

    Rectangle { id: plate; anchors.fill: parent; radius: 6; color: th.plate }

    // Header in the node's Maya category colour
    Rectangle {
        id: header
        width: parent.width; height: 28; radius: 6
        color: node.info ? node.info.color : th.panel
        Rectangle { visible: !node.simple; anchors.bottom: parent.bottom; width: parent.width; height: 6; color: parent.color }
    }

    // Greek bars (far LOD): text too small to read is drawn as bars where it stands, so a zoom
    // out fades text into shapes instead of dropping it. One ShaderEffect a node, no items per
    // row: each row is two floats packed into 16 vec4 uniforms (32 rows; the rest are not
    // drawn) -- f1 = centreY * 512 + labelX, f2 = labelW * 2048 + inPort * 1024 + outPort * 512
    // + boxW. Port dots are neutral: the type colour has no room in the uniforms.
    readonly property var greek: {
        var g = [], i
        for (i = 0; i < 64; i++) g.push(-1)
        if (!info) return g
        var rows = info.rows, n = 0
        for (i = 0; i < rows.length && n < 32; i++) {
            var r = rows[i]
            var port = r.kind === "port" || r.kind === "enum" || r.kind === "slot"
            if (!port && r.kind !== "nomatch") continue
            var bw = !r.valueKind ? 0 : (r.valueKind === "enum" ? Math.max(70, String(r.value).length * 6 + 28)
                                                                : (r.valueKind === "bool" ? 40 : 58))
            var indent = 12 + r.depth * 14 + (r.chev > 0 ? 11 : 0)
            var room = width - indent - 24 - (bw ? bw + 6 : 0)
            var lw = Math.max(6, Math.min(room, String(r.label || "").length * (r.depth > 0 ? 5.6 : 6.2)))
            var outOnly = r.outPort && !r.inPort
            var lx = outOnly ? width - 12 - lw : indent
            g[2 * n] = Math.round(r.y + r.h / 2) * 512 + Math.round(Math.max(0, lx))
            g[2 * n + 1] = Math.round(lw) * 2048 + (r.inPort ? 1024 : 0) + (r.outPort ? 512 : 0) + bw
            n++
        }
        return g
    }
    ShaderEffect {
        visible: node.far && node.info !== null
        x: -8
        y: -18
        width: node.width + 16
        height: node.height + 18
        property size sz: Qt.size(width, height)
        property real nodeW: node.width
        property real px: 1 / Math.max(0.01, board.zoom)          // node units per screen pixel
        property real nameW: node.info ? Math.min(node.width - 87, node.info.name.length * 7) : 0
        property real typeW: node.info ? node.info.type.length * 5.6 : 0
        property color ink: node.th.ink
        property color text: node.th.text
        property color faint: node.th.faint
        property color field: node.th.field
        readonly property var g: node.greek
        property vector4d r0: Qt.vector4d(g[0], g[1], g[2], g[3])
        property vector4d r1: Qt.vector4d(g[4], g[5], g[6], g[7])
        property vector4d r2: Qt.vector4d(g[8], g[9], g[10], g[11])
        property vector4d r3: Qt.vector4d(g[12], g[13], g[14], g[15])
        property vector4d r4: Qt.vector4d(g[16], g[17], g[18], g[19])
        property vector4d r5: Qt.vector4d(g[20], g[21], g[22], g[23])
        property vector4d r6: Qt.vector4d(g[24], g[25], g[26], g[27])
        property vector4d r7: Qt.vector4d(g[28], g[29], g[30], g[31])
        property vector4d r8: Qt.vector4d(g[32], g[33], g[34], g[35])
        property vector4d r9: Qt.vector4d(g[36], g[37], g[38], g[39])
        property vector4d r10: Qt.vector4d(g[40], g[41], g[42], g[43])
        property vector4d r11: Qt.vector4d(g[44], g[45], g[46], g[47])
        property vector4d r12: Qt.vector4d(g[48], g[49], g[50], g[51])
        property vector4d r13: Qt.vector4d(g[52], g[53], g[54], g[55])
        property vector4d r14: Qt.vector4d(g[56], g[57], g[58], g[59])
        property vector4d r15: Qt.vector4d(g[60], g[61], g[62], g[63])
        // Qt 6 (Maya 2025+) needs a precompiled shader: source in tools/shaders/greek.frag.
        fragmentShader: (typeof qtMajor !== "undefined" && qtMajor >= 6) ? Qt.resolvedUrl("shaders/greek.frag.qsb") : "
            varying highp vec2 qt_TexCoord0;
            uniform highp vec2 sz;
            uniform highp float px;
            uniform highp float nodeW;
            uniform highp float nameW;
            uniform highp float typeW;
            uniform lowp vec4 ink;
            uniform lowp vec4 text;
            uniform lowp vec4 faint;
            uniform lowp vec4 field;
            uniform lowp float qt_Opacity;
            uniform highp vec4 r0; uniform highp vec4 r1; uniform highp vec4 r2; uniform highp vec4 r3;
            uniform highp vec4 r4; uniform highp vec4 r5; uniform highp vec4 r6; uniform highp vec4 r7;
            uniform highp vec4 r8; uniform highp vec4 r9; uniform highp vec4 r10; uniform highp vec4 r11;
            uniform highp vec4 r12; uniform highp vec4 r13; uniform highp vec4 r14; uniform highp vec4 r15;
            highp vec2 p;
            lowp vec4 acc;
            // coverage of a rounded bar [x0, x1] x [cy - h/2, cy + h/2], antialiased over one pixel
            void bar(highp float x0, highp float x1, highp float cy, highp float h, lowp vec4 c) {
                highp float r = 0.5 * h;
                highp vec2 q = vec2(clamp(p.x, x0 + r, max(x0 + r, x1 - r)), cy);
                highp float d = length(p - q) - r;
                lowp float a = c.a * clamp(0.5 - d / px, 0.0, 1.0);
                acc = mix(acc, vec4(c.rgb, 1.0), a);
            }
            void row(highp float f1, highp float f2) {
                if (f1 < 0.0) return;
                highp float cy = floor(f1 / 512.0), lx = f1 - cy * 512.0;
                if (abs(p.y - cy) > 9.0) return;
                highp float lw = floor(f2 / 2048.0), rest = f2 - lw * 2048.0;
                highp float inp = floor(rest / 1024.0); rest -= inp * 1024.0;
                highp float outp = floor(rest / 512.0), bw = rest - outp * 512.0;
                if (inp > 0.0) bar(0.0, 0.0, cy, 7.0, vec4(faint.rgb, 0.9));
                if (outp > 0.0) bar(nodeW, nodeW, cy, 7.0, vec4(faint.rgb, 0.9));
                bar(lx, lx + lw, cy, 7.0, vec4(text.rgb, 0.55));
                if (bw > 0.0) {
                    highp float bx1 = nodeW - 12.0 - outp * 4.0;
                    bar(bx1 - bw, bx1, cy, 14.0, vec4(field.rgb, 1.0));
                }
            }
            void main() {
                p = qt_TexCoord0 * sz - vec2(8.0, 18.0);
                acc = vec4(0.0);
                bar(2.0, 2.0 + typeW, -11.0, 7.0, vec4(faint.rgb, 0.8));
                bar(35.0, 35.0 + nameW, 14.0, 9.0, vec4(ink.rgb, 0.7));
                if (p.y > 28.0) {
                    row(r0.x, r0.y); row(r0.z, r0.w); row(r1.x, r1.y); row(r1.z, r1.w);
                    row(r2.x, r2.y); row(r2.z, r2.w); row(r3.x, r3.y); row(r3.z, r3.w);
                    row(r4.x, r4.y); row(r4.z, r4.w); row(r5.x, r5.y); row(r5.z, r5.w);
                    row(r6.x, r6.y); row(r6.z, r6.w); row(r7.x, r7.y); row(r7.z, r7.w);
                    row(r8.x, r8.y); row(r8.z, r8.w); row(r9.x, r9.y); row(r9.z, r9.w);
                    row(r10.x, r10.y); row(r10.z, r10.w); row(r11.x, r11.y); row(r11.z, r11.w);
                    row(r12.x, r12.y); row(r12.z, r12.w); row(r13.x, r13.y); row(r13.z, r13.w);
                    row(r14.x, r14.y); row(r14.z, r14.w); row(r15.x, r15.y); row(r15.z, r15.w);
                }
                gl_FragColor = acc * qt_Opacity;     // bar() accumulates premultiplied
            }"
    }

    // Selection ring, drawn over the plate edge
    Rectangle {
        visible: node.selFade > 0
        opacity: node.selFade
        x: -1.5; y: -1.5; width: parent.width + 3; height: parent.height + 3; radius: 7.5
        color: "transparent"; border.width: 1.5; border.color: node.selTint
        antialiasing: true
    }

    // Hover focus for wires. A HoverHandler on the whole node stays hovered over ports,
    // labels and buttons; the body MouseArea alone lost hover to those siblings, and the wire
    // focus then flickered to the selection's wires.
    HoverHandler {
        onHoveredChanged: {
            if (hovered) board.hoverNode = node.nid
            else if (board.hoverNode === node.nid) board.hoverNode = ""
        }
    }

    // ---------------------------------------------------------------- body gestures (below the rows)
    MouseArea {
        id: body
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        property point start
        property var starts: null
        property bool moved: false
        onPressed: function(mouse) {
            board.forceActiveFocus()
            board.tipStop()
            // Modified mouse gestures start on the canvas below (including lazy connect).
            if ((mouse.modifiers & Qt.AltModifier)
                    || (mouse.button === Qt.RightButton &&
                        (mouse.modifiers & (Qt.ControlModifier | Qt.ShiftModifier)))) {
                mouse.accepted = false
                return
            }
            if (mouse.button === Qt.RightButton) return
            if (node.dead) { bridge.clickNode(node.nid, mouse.modifiers); return }
            bridge.clickNode(node.nid, mouse.modifiers)
            start = mapToItem(board, mouse.x, mouse.y)
            moved = false
            starts = board.dragStarts()
        }
        onPositionChanged: function(mouse) {
            board.mouseWorld = board.toWorld(mapToItem(board, mouse.x, mouse.y).x,
                                            mapToItem(board, mouse.x, mouse.y).y)
            if (!pressed || !starts) return
            var p = mapToItem(board, mouse.x, mouse.y)
            var dx = (p.x - start.x) / board.zoom, dy = (p.y - start.y) / board.zoom
            if (!moved && Math.abs(dx) + Math.abs(dy) < 2) return
            moved = true
            board.dragTo(starts, dx, dy)
        }
        onReleased: function(mouse) {
            if (mouse.button === Qt.RightButton) { bridge.nodeMenu(node.nid); return }
            if (moved && starts) board.commitDrag(starts)
            starts = null
        }
        onDoubleClicked: function(mouse) {
            if (mouse.button !== Qt.LeftButton || mouse.y >= 28) return
            // On the name itself: rename, as Maya's Node Editor; elsewhere on the header: fold.
            if (!node.dead && mouse.x >= 31 && mouse.x <= 39 + Math.max(16, node.nameW)) { board.startRename(node.nid); return }
            if (node.info && node.info.conv) bridge.collapseConversion(node.nid)   // back into the wire
            else bridge.toggleFold(node.nid)
        }
    }

    // drag the right edge to set the node's width; double-click it for the computed width.
    // Above the body, below the rows: a port on the edge keeps its own clicks.
    MouseArea {
        x: parent.width - 4; width: 8; height: parent.height
        enabled: !node.dead && !node.far
        hoverEnabled: true
        cursorShape: Qt.SizeHorCursor
        property real x0
        property real w0
        onPressed: function(mouse) {
            board.forceActiveFocus()
            board.tipStop()
            x0 = mapToItem(board, mouse.x, mouse.y).x
            w0 = node.width
        }
        onPositionChanged: function(mouse) {
            if (!pressed) return
            var dx = (mapToItem(board, mouse.x, mouse.y).x - x0) / board.zoom
            node.dragW = Math.max(120, Math.min(900, Math.round(w0 + dx)))
        }
        onReleased: if (node.dragW > 0) bridge.setNodeWidth(node.nid, node.dragW)
        onDoubleClicked: { node.dragW = -1; bridge.setNodeWidth(node.nid, 0) }
    }

    Loader {
        anchors.fill: parent
        active: node.built
        visible: !node.far
        sourceComponent: Component {
            Item {
                // ---------------------------------------------------------------- header content
                Image {
                    id: icon
                    x: 8; y: 4; width: 20; height: 20
                    sourceSize: Qt.size(40, 40)
                    smooth: true
                    mipmap: true
                    property string type: node.info ? node.info.type : ""
                    // Local copy first (nodex/icons, extracted from the same Maya resource), then Maya's own
                    // resource for types without a copy -- :/ resources exist only inside the Maya GUI.
                    onTypeChanged: {
                        if (!type) { source = ""; return }
                        var local = bridge.iconUrl(type)
                        source = local ? local : "qrc:/out_" + type + "_200.png"
                    }
                }
                Text {
                    x: 35; y: 0
                    width: parent.width - 35 - 52
                    height: 28
                    visible: !node.renaming
                    verticalAlignment: Text.AlignVCenter
                    text: node.info ? node.info.name : ""
                    elide: Text.ElideRight
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    font.strikeout: node.dead
                    color: th.ink
                    onContentWidthChanged: function() { node.nameW = contentWidth }
                    Component.onCompleted: node.nameW = contentWidth
                }
                // the name editor. Enter or a click elsewhere renames; Esc keeps the old name.
                Loader {
                    active: node.renaming
                    x: 31; y: 4; width: parent.width - 31 - 52; height: 20
                    sourceComponent: Component {
                        Rectangle {
                            radius: 3
                            color: th.field
                            border.width: 1
                            border.color: th.accent
                            TextInput {
                                id: nameInput
                                anchors.fill: parent; anchors.leftMargin: 4; anchors.rightMargin: 4
                                verticalAlignment: TextInput.AlignVCenter
                                color: th.ink; font.pixelSize: 12; font.weight: Font.DemiBold
                                selectByMouse: true; clip: true
                                property bool cancelled: false
                                text: node.info ? node.info.name : ""
                                Component.onCompleted: { forceActiveFocus(); selectAll() }
                                Keys.onEscapePressed: { cancelled = true; board.renaming = ""; board.forceActiveFocus() }
                                onEditingFinished: {
                                    if (cancelled || board.renaming !== node.nid) return
                                    board.renaming = ""
                                    if (node.info && text !== node.info.name) bridge.renameNode(node.nid, text)
                                    board.forceActiveFocus()
                                }
                            }
                        }
                    }
                }
                // Simple-mode stubs where the node has connections. Small circles are drawn 4x large and
                // scaled down: the scene graph tessellates a radius by its local size, so a 4 px radius
                // under the board's zoom showed its polygon edges.
                Rectangle { visible: node.simple && node.info !== null && node.info.hasIn; x: -16; y: -2; width: 32; height: 32; radius: 16; scale: 0.25; antialiasing: true; color: th.faint }
                Rectangle { visible: node.simple && node.info !== null && node.info.hasOut; x: parent.width - 16; y: -2; width: 32; height: 32; radius: 16; scale: 0.25; antialiasing: true; color: th.faint }

                // Attribute filter and fold buttons
                Item {
                    x: parent.width - 48; y: 4; width: 20; height: 20
                    Rectangle { anchors.fill: parent; radius: 3; color: "#000000"; opacity: 0.22; visible: fma.containsMouse || (node.info !== null && node.info.filterOpen) }
                    Image {
                        anchors.centerIn: parent; width: 14; height: 14; sourceSize: Qt.size(40, 40)
                        source: bridge.toolbarIcon("search"); smooth: true; mipmap: true
                        opacity: fma.containsMouse || (node.info !== null && node.info.filterOpen) ? 1 : 0.6
                    }
                    MouseArea { id: fma; anchors.fill: parent; hoverEnabled: true; onClicked: bridge.toggleFilter(node.nid) }
                }
                Item {
                    x: parent.width - 26; y: 4; width: 20; height: 20
                    Rectangle { anchors.fill: parent; radius: 3; color: "#555558"; visible: foldMa.containsMouse }
                    Text {
                        anchors.centerIn: parent
                        text: "▾"
                        rotation: node.simple ? -90 : 0
                        font.pixelSize: 12
                        color: foldMa.containsMouse ? th.ink : Qt.rgba(1, 1, 1, 0.55)
                    }
                    MouseArea { id: foldMa; anchors.fill: parent; hoverEnabled: true; onClicked: bridge.toggleFold(node.nid) }
                }

                // Filter field lives outside the row Repeater so typing survives the row rebuilds.
                Rectangle {
                    visible: node.info !== null && node.info.filterOpen
                    x: 8; y: 32; width: parent.width - 16; height: 20; radius: 3
                    color: th.field
                    border.width: filterInput.activeFocus ? 1 : 0
                    border.color: th.accent
                    TextInput {
                        id: filterInput
                        anchors.fill: parent; anchors.leftMargin: 7; anchors.rightMargin: 7
                        verticalAlignment: TextInput.AlignVCenter
                        color: th.ink; font.pixelSize: 11; selectByMouse: true; clip: true
                        Component.onCompleted: text = node.info ? node.info.filterText : ""
                        onTextEdited: bridge.setFilter(node.nid, text)
                        Keys.onEscapePressed: { text = ""; bridge.toggleFilter(node.nid); board.forceActiveFocus() }
                        Text {
                            visible: !parent.text; anchors.verticalCenter: parent.verticalCenter
                            text: "Filter attributes"; color: th.faint; font.pixelSize: 11
                        }
                    }
                    readonly property bool open: node.info !== null && node.info.filterOpen
                    onOpenChanged: { if (open) filterInput.forceActiveFocus(); else filterInput.text = "" }
                }

                // ---------------------------------------------------------------- rows
                Repeater {
                    model: node.info ? node.info.rows : []
                    delegate: Item {
                        id: row
                        property var r: modelData
                        readonly property bool outOnly: r.outPort && !r.inPort
                        readonly property bool isPort: r.kind === "port" || r.kind === "enum" || r.kind === "slot"
                        readonly property int indent: 12 + r.depth * 14
                        y: r.y
                        width: node.width
                        height: r.h

                        // chevron for compounds
                        Text {
                            visible: r.chev > 0
                            x: row.outOnly ? lbl.x - 13 : row.indent - 3
                            anchors.verticalCenter: parent.verticalCenter
                            text: "▸"
                            rotation: r.chev === 2 ? 90 : 0
                            font.pixelSize: 10
                            color: chevMa.containsMouse ? th.ink : th.faint
                            MouseArea {
                                id: chevMa; anchors.fill: parent; anchors.margins: -4; hoverEnabled: true
                                onClicked: bridge.toggleExpand(node.nid, r.key)
                            }
                        }
                        Text {
                            id: lbl
                            visible: row.isPort || r.kind === "nomatch"
                            x: row.outOnly ? row.width - 12 - width : row.indent + (r.chev > 0 ? 11 : 0)
                            width: Math.min(implicitWidth, row.width - row.indent - 24 - (valueBox.visible ? valueBox.width + 6 : 0))
                            anchors.verticalCenter: parent.verticalCenter
                            // A find-field / filter match comes as styled text with the match underlined.
                            text: r.hit ? r.hit : (r.label || "")
                            textFormat: r.hit ? Text.StyledText : Text.PlainText
                            elide: Text.ElideRight
                            font.pixelSize: r.depth > 0 ? 11 : 12
                            font.italic: r.kind === "slot" || r.kind === "nomatch"
                            color: r.kind === "slot" || r.kind === "nomatch" ? th.faint
                                   : (r.inConn || r.outConn) ? th.text : th.muted
                        }

                        // value in the node: number field, bool toggle, enum dropdown
                        Rectangle {
                            id: valueBox
                            visible: r.valueKind !== "" && r.valueKind !== undefined
                            width: r.valueKind === "enum" ? Math.max(70, enumText.implicitWidth + 28) : (r.valueKind === "bool" ? 40 : 58)
                            height: r.kind === "enum" ? 18 : 16
                            x: row.width - 12 - width - (r.outPort ? 4 : 0)
                            anchors.verticalCenter: parent.verticalCenter
                            radius: 3
                            readonly property bool sliding: board.inValueDrag(node.nid, r.key)
                            color: sliding ? Qt.lighter(th.field, 1.6) : (valMa.containsMouse && !numInput.activeFocus ? Qt.lighter(th.field, 1.3) : th.field)
                            border.width: numInput.activeFocus || sliding ? 1 : 0
                            border.color: th.accent
                            // Blender number field: arrows on hover, drag to slide, click to type.
                            Text {
                                visible: r.valueKind === "num" && valMa.containsMouse && !numInput.activeFocus
                                x: 3; anchors.verticalCenter: parent.verticalCenter
                                text: "‹"; font.pixelSize: 11; color: th.muted
                            }
                            Text {
                                visible: r.valueKind === "num" && valMa.containsMouse && !numInput.activeFocus
                                anchors.right: parent.right; anchors.rightMargin: 3; anchors.verticalCenter: parent.verticalCenter
                                text: "›"; font.pixelSize: 11; color: th.muted
                            }
                            TextInput {
                                id: numInput
                                visible: r.valueKind === "num"
                                anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9
                                horizontalAlignment: activeFocus ? TextInput.AlignLeft : TextInput.AlignHCenter
                                verticalAlignment: TextInput.AlignVCenter
                                font.family: "Consolas"; font.pixelSize: 11
                                color: th.ink
                                selectByMouse: true
                                clip: true
                                text: board.shownValue(node.nid, r.key, r.value)
                                validator: DoubleValidator {}
                                onEditingFinished: {
                                    if (board.valueTyped(text)) return       // swept fields: all at once
                                    if (text !== r.value) bridge.setValue(node.nid, r.key, text)
                                }
                                onActiveFocusChanged: if (!activeFocus) Qt.callLater(board.valueEditDone)
                                Keys.onEscapePressed: { board.valueCancel(); text = r.value; board.forceActiveFocus() }
                            }
                            Text {
                                visible: r.valueKind === "bool"
                                anchors.centerIn: parent
                                text: board.shownValue(node.nid, r.key, r.value); font.pixelSize: 11; color: th.ink
                            }
                            Text {
                                id: enumText
                                visible: r.valueKind === "enum"
                                x: 7; anchors.verticalCenter: parent.verticalCenter
                                text: r.value; font.pixelSize: 11; color: th.ink
                            }
                            Text {
                                visible: r.valueKind === "enum"
                                anchors.right: parent.right; anchors.rightMargin: 6; anchors.verticalCenter: parent.verticalCenter
                                text: "▾"; font.pixelSize: 10; color: th.muted
                            }
                            MouseArea {
                                id: valMa
                                // While the text editor is open the TextInput keeps its own mouse.
                                enabled: !numInput.activeFocus
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                cursorShape: r.valueKind === "num" ? Qt.SizeHorCursor : Qt.PointingHandCursor
                                onPressed: function(mouse) {
                                    board.forceActiveFocus()
                                    if (node.dead) return
                                    if (r.valueKind === "enum") {
                                        if (mouse.button === Qt.RightButton) { mouse.accepted = false; return }
                                        board.openEnum(node.nid, r.key, valueBox)
                                        return
                                    }
                                    if (board.vdrag) { board.valueCancel(); return }   // the other button cancels (Blender)
                                    board.valueStart(node.nid, r, mapToItem(board, mouse.x, mouse.y), mouse.button, mouse.modifiers)
                                }
                                onPositionChanged: function(mouse) { if (pressed && board.vdrag) board.valueMove(mapToItem(board, mouse.x, mouse.y), mouse.modifiers) }
                                onReleased: {
                                    if (!board.vdrag) return
                                    var how = board.valueEnd()
                                    if (how === "edit" || how === "multi") { numInput.forceActiveFocus(); numInput.selectAll() }
                                }
                                onCanceled: board.valueCancel()
                                onWheel: function(wheel) {
                                    if (!(wheel.modifiers & Qt.ControlModifier)) { wheel.accepted = false; return }
                                    board.valueWheel(node.nid, r, wheel.angleDelta.y > 0)
                                }
                            }
                        }

                        // ports: a filled circle in the attribute type's colour, as Maya
                        Repeater {
                            model: row.isPort ? [["in", r.inPort], ["out", r.outPort]] : []
                            delegate: Item {
                                id: port
                                property string side: modelData[0]
                                readonly property int st: board.portState(node.nid, r, side)
                                visible: modelData[1]
                                x: side === "in" ? -7 : row.width - 7
                                y: row.height / 2 - 7
                                width: 14; height: 14
                                opacity: st === 1 ? 0.2 : 1
                                // Drawn 4x large and scaled by 0.25 (see the simple-mode stubs): round at any zoom.
                                Rectangle {
                                    visible: port.st === 2 || portMa.containsMouse
                                    anchors.centerIn: parent
                                    width: 68; height: 68; radius: 34; scale: 0.25
                                    antialiasing: true
                                    color: r.color; opacity: 0.3
                                }
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 36; height: 36; radius: 18; scale: 0.25
                                    antialiasing: true
                                    color: r.color
                                }
                                MouseArea {
                                    id: portMa
                                    anchors.fill: parent
                                    anchors.margins: -2
                                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                                    hoverEnabled: true
                                    cursorShape: Qt.CrossCursor
                                    onEntered: board.tipStart(node.nid, r.key, port)
                                    onExited: board.tipStop()
                                    onPressed: function(mouse) {
                                        board.forceActiveFocus()
                                        board.tipStop()
                                        if (mouse.button === Qt.RightButton) { bridge.portMenu(node.nid, r.key); return }
                                        if (node.dead) return
                                        board.wireStart(node.nid, r, port.side, mapToItem(board, mouse.x, mouse.y), mouse.modifiers)
                                    }
                                    onPositionChanged: function(mouse) { if (pressed && board.drag) board.wireMove(mapToItem(board, mouse.x, mouse.y)) }
                                    onReleased: function(mouse) { if (board.drag) board.wireEnd(mapToItem(board, mouse.x, mouse.y)) }
                                    onCanceled: board.wireCancel()
                                }
                            }
                        }

                        // Hovering the label also explains the attribute
                        MouseArea {
                            visible: row.isPort
                            x: lbl.x; width: lbl.width; height: row.height
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                            onEntered: board.tipStart(node.nid, r.key, lbl)
                            onExited: board.tipStop()
                        }
                    }
                }

                // "+N more attributes" / "Show connected only"
                Text {
                    visible: node.info !== null && node.info.foot !== ""
                    x: 12; y: node.height - 22; height: 20
                    verticalAlignment: Text.AlignVCenter
                    text: node.info ? node.info.foot : ""
                    font.pixelSize: 11
                    color: footMa.containsMouse ? th.text : th.faint
                    MouseArea { id: footMa; anchors.fill: parent; hoverEnabled: true; onClicked: bridge.toggleFoot(node.nid) }
                }
            }
        }
    }
}
