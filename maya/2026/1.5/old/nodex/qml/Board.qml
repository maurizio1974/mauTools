// NodeX board: canvas, wires, nodes, wiring gestures. All scene work goes through `bridge`.
// Colours arrive from bridge.theme() and node/wire data.
//
// Big graphs (hundreds of nodes, thousands of wires) stay fluid because:
//  - nodes outside the view are culled (`viewRect`), and rows are only built for nodes that
//    were seen at a readable zoom (`far` LOD, Node.qml);
//  - the wire canvas is not repainted while panning / zooming: the last painted image is
//    moved and scaled (`pv`), and repainted when the view rests or its margin runs out; far
//    out, when the whole board fits one texture, it is painted whole and a pan never repaints;
//  - wires are culled to the view, styled per group and stroked one by one (one path of many
//    crossing curves chokes QPainter's rasterizer, see paintWires);
//  - "node links" draw one wire per node pair, with every connection of the hovered or
//    selected nodes in detail.
import QtQuick 2.15

Item {
    id: board
    focus: true
    clip: true

    property var th: bridge.theme()
    property real panX: 60
    property real panY: 60
    property real zoom: 1.0
    property var nodeItems: ({})
    property var pendingInfo: ({})
    property int nodesVersion: 0
    property var wireList: []
    property var wireMap: ({})
    property var sel: ({})
    property string lead: ""
    property string hoverNode: ""
    property string hoverWire: ""
    property string selWire: ""
    property var isolate: null          // {a, b, wire} -- wire "" isolates the node pair
    property var connectionFocus: null  // All connection chains found between two selected nodes.
    onConnectionFocusChanged: repaintWires()
    property var drag: null             // wire being dragged from a port
    property var dropHit: null
    property var knife: null            // Ctrl+RMB cut line, screen space
    property var lazy: null             // Node Wrangler: Alt+RMB node-to-node connect
    property var marquee: null
    property bool animate: false
    property bool showGrid: true
    property bool snap: false
    property string query: ""
    property point mouseWorld: Qt.point(0, 0)
    property string hiddenWire: ""
    property string renaming: ""        // node whose header holds the name editor
    property var frames: []             // Blender frames of the tab (bridge.framesChanged)
    property var frameEdit: null        // {id, field: "label" | "text"} being edited
    readonly property int gridStep: 22
    readonly property real minZoom: 0.06
    readonly property real maxZoom: 2.5

    // node links (big graphs): one wire per (source node, destination node)
    property bool links: false
    property var bundles: []
    property var bundleMap: ({})
    property var rowMap: ({})           // "r:" id -> connections sharing both rows
    property var drawList: []           // wires as drawn: single wires and row groups
    readonly property int detailLimit: 900     // detail wires drawn over node links at most

    // culling and level of detail
    property rect viewRect: Qt.rect(-1e7, -1e7, 2e7, 2e7)   // world rect nodes stay visible in
    property bool far: false                                  // below readable zoom: no rows

    // what the wire canvas holds: the view it was painted at (pan x / y, zoom z), the screen
    // rect it covers then (rx, ry, cw, ch) and whether that is the whole board; the drawn curves
    property var pv: ({x: 0, y: 0, z: 1, rx: -wireMargin, ry: -wireMargin, cw: 0, ch: 0, whole: false})
    property var geo: []
    property var paintStats: ({})       // last wire paint: JS ms, curves, style groups
    readonly property int wireMargin: 220
    readonly property int wireCap: 4096         // whole-board canvas: max px a side
    property var worldBox: null                 // nodes' world bbox, cached (boxDirty)
    property bool boxDirty: true
    // ------------------------------------------------------------------ helpers
    function toWorld(sx, sy) { return Qt.point((sx - panX) / zoom, (sy - panY) / zoom) }
    function registerNode(id, item) { nodeItems[id] = item; nodesVersion++; boxDirty = true; repaintWires() }
    function unregisterNode(id, item) { if (nodeItems[id] === item) { delete nodeItems[id]; nodesVersion++; boxDirty = true } }
    function wiresDirty() { boxDirty = true; repaintWires() }
    function findWire(id) { return wireMap[id] || null }
    function findItem(id) {
        if (id.indexOf("b:") === 0) return bundleMap[id] || null
        if (id.indexOf("r:") === 0) return rowMap[id] || null
        return findWire(id)
    }
    function idsOf(id) { var b = bundleMap[id] || rowMap[id]; return b ? b.ids : [id] }
    function isGroup(id) { return id.indexOf("b:") === 0 || id.indexOf("r:") === 0 }
    function wireInto(nid, key) {
        for (var i = 0; i < wireList.length; i++) { var w = wireList[i]; if (w.dst === nid && w.dstPlug === key) return w }
        return null
    }
    function indexWires() {
        var m = {}, bm = {}, out = [], rm = {}, rows = [], i, w
        for (i = 0; i < wireList.length; i++) {
            w = wireList[i]
            m[w.id] = w
            var k = "b:" + w.src + ">" + w.dst, b = bm[k]
            if (!b) { b = bm[k] = {id: k, src: w.src, dst: w.dst, ids: [], color: w.color, mixed: false}; out.push(b) }
            b.ids.push(w.id)
            if (b.color !== w.color) b.mixed = true
            // connections that meet the same two rows (both compounds folded) are one wire,
            // as in Maya: drawn, hovered, selected, cut and disconnected together.
            var rk = "r:" + w.src + "|" + w.srcY + ">" + w.dst + "|" + w.dstY, r = rm[rk]
            if (!r) { r = rm[rk] = {id: rk, src: w.src, dst: w.dst, srcY: w.srcY, dstY: w.dstY, ids: [],
                                    color: w.color, uc: false, compound: true, first: w}; rows.push(r) }
            r.ids.push(w.id)
            if (w.uc) r.uc = true
            if (r.color !== w.color) r.color = th.muted
        }
        var draw = []
        for (i = 0; i < rows.length; i++) {
            if (rows[i].ids.length > 1) draw.push(rows[i])
            else { draw.push(rows[i].first); delete rm[rows[i].id] }
        }
        wireMap = m; bundleMap = bm; bundles = out; rowMap = rm; drawList = draw
    }
    function anchorOf(nid, key) {
        var it = nodeItems[nid]
        if (!it || !it.info) return 14
        var a = it.info.anchors, p = it.info.parents, k = key, n = 0
        while (k && n < 16) {
            if (a[k] !== undefined) return a[k]
            k = p[k] !== undefined ? p[k] : ""
            n++
        }
        return 14
    }
    // Screen point of a port. Culled (invisible) nodes still have their wires.
    function portPt(nid, ly, out) {
        var it = nodeItems[nid]
        if (!it || !it.info) return null
        return Qt.point(panX + zoom * (it.x + (out ? it.width : 0)), panY + zoom * (it.y + ly))
    }
    function bezDx(ax, bx) { return Math.max(40 * zoom, Math.abs(bx - ax) * 0.5) }
    function bezPts(a, b, n) { return bezPtsD(a.x, a.y, b.x, b.y, bezDx(a.x, b.x), n) }
    function bezPtsD(ax, ay, bx, by, dx, n) {
        var p1x = ax + dx, p2x = bx - dx, pts = []
        for (var i = 0; i <= n; i++) {
            var t = i / n, u = 1 - t
            pts.push(Qt.point(u*u*u*ax + 3*u*u*t*p1x + 3*u*t*t*p2x + t*t*t*bx,
                              u*u*u*ay + 3*u*u*t*ay + 3*u*t*t*by + t*t*t*by))
        }
        return pts
    }
    function segDist(px, py, a, b) {
        var vx = b.x - a.x, vy = b.y - a.y, L = vx*vx + vy*vy
        var t = L > 0 ? Math.max(0, Math.min(1, ((px - a.x) * vx + (py - a.y) * vy) / L)) : 0
        var dx = a.x + t * vx - px, dy = a.y + t * vy - py
        return Math.sqrt(dx*dx + dy*dy)
    }
    function wireEnds(w) {
        var a = portPt(w.src, w.srcY, true), b = portPt(w.dst, w.dstY, false)
        return (a && b) ? [a, b] : null
    }
    // Screen point -> the wire canvas's own pixels (it may be moved / scaled since painted).
    function toPainted(sx, sy) {
        var k = pv.z / zoom
        return Qt.point(pv.x + (sx - panX) * k, pv.y + (sy - panY) * k)
    }
    // Hit tests run over what was drawn (`geo`): culled and bundled like the picture.
    function hitWire(sx, sy) {
        var p = toPainted(sx, sy), tol = 6 * pv.z / zoom, best = "", bd = tol
        for (var i = 0; i < geo.length; i++) {
            var g = geo[i]
            if (p.x < g.x0 - tol || p.x > g.x1 + tol || p.y < g.y0 - tol || p.y > g.y1 + tol) continue
            var pts = bezPtsD(g.ax, g.ay, g.bx, g.by, g.dx, 20)
            for (var j = 0; j < pts.length - 1; j++) {
                var d = segDist(p.x, p.y, pts[j], pts[j + 1])
                if (d < bd) { bd = d; best = g.id }
            }
        }
        return best
    }
    function segCross(a, b, c, d) {
        function side(p, q, r) { return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x) }
        var d1 = side(c, d, a), d2 = side(c, d, b), d3 = side(a, b, c), d4 = side(a, b, d)
        return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0))
    }
    function knifeHits() {
        var out = []
        if (!knife) return out
        var k0 = toPainted(knife.x0, knife.y0), k1 = toPainted(knife.x1, knife.y1)
        for (var i = 0; i < geo.length; i++) {
            var g = geo[i]
            if (Math.max(k0.x, k1.x) < g.x0 || Math.min(k0.x, k1.x) > g.x1 ||
                Math.max(k0.y, k1.y) < g.y0 || Math.min(k0.y, k1.y) > g.y1) continue
            var pts = bezPtsD(g.ax, g.ay, g.bx, g.by, g.dx, 32)
            for (var j = 0; j < pts.length - 1; j++)
                if (segCross(pts[j], pts[j + 1], k0, k1)) { out = out.concat(idsOf(g.id)); break }
        }
        return out
    }
    function compat(a, ac, b, bc) {
        if (a === "MultiAmbiguous" || b === "MultiAmbiguous") return true
        if (a === b) return true
        var scalar = {"Numeric": 1, "Integer": 1, "Boolean": 1, "Rotation": 1}
        if (!ac && !bc && scalar[a] && scalar[b]) return true
        var v3 = {"ThreeDNumericVector": 1, "Rotation": 1, "Color": 1, "ThreeDIntegerVector": 1}
        return !!(ac && bc && v3[a] && v3[b])
    }
    function portState(nid, r, side) {
        // 0 idle, 1 dimmed (not a target), 2 valid target, 3 origin
        if (!drag) return 0
        if (drag.nid === nid && drag.key === r.key && drag.side === side) return 3
        if (side !== drag.want || nid === drag.nid) return 1
        return compat(drag.cls, drag.compound, r.cls, r.compound) ? 2 : 1
    }
    function portAt(sx, sy, want, exclude) {
        var w = toWorld(sx, sy)
        for (var id in nodeItems) {
            var it = nodeItems[id]
            if (id === exclude || !it.info || it.info.dead) continue
            if (w.x < it.x - 14 || w.x > it.x + it.width + 14 || w.y < it.y || w.y > it.y + it.height) continue
            var ly = w.y - it.y, rows = it.info.rows
            for (var i = 0; i < rows.length; i++) {
                var r = rows[i]
                if (ly < r.y || ly >= r.y + r.h) continue
                if (want === "in" && r.inPort) return {nid: id, key: r.key, cls: r.cls, compound: r.compound}
                if (want === "out" && r.outPort) return {nid: id, key: r.key, cls: r.cls, compound: r.compound}
            }
        }
        return null
    }

    // ------------------------------------------------------------------ model sync
    ListModel { id: nodeModel }

    function reset() {
        nodeModel.clear()
        nodeItems = ({}); pendingInfo = ({}); buildQueue = []
        isolate = null; connectionFocus = null; selWire = ""; hoverWire = ""; hoverNode = ""; drag = null
        vdrag = null        // its row delegates are gone; the snapshot below is newer than its deferred infos
        var s = JSON.parse(bridge.snapshot())
        links = s.links === true
        cull()      // before the delegates exist, or every node builds its rows once
        for (var i = 0; i < s.nodes.length; i++) {
            pendingInfo[s.nodes[i].id] = s.nodes[i]
            nodeModel.append({nid: s.nodes[i].id})
        }
        wireList = s.wires
        frames = s.frames || []
        frameEdit = null
        indexWires()
        applySel(s.sel, s.lead)
        repaintBurst.count = 0; repaintBurst.start()
    }
    function applySel(ids, ld) {
        var m = {}
        for (var i = 0; i < ids.length; i++) m[ids[i]] = true
        sel = m; lead = ld
        board.repaintWires()
    }

    Connections {
        target: bridge
        function onBoardReset() { board.reset() }
        function onNodeAdded(id, info) {
            if (board.nodeItems[id]) { board.nodeItems[id].info = info; return }
            board.pendingInfo[id] = info
            nodeModel.append({nid: id})
        }
        function onNodeChanged(id, info) {
            // A value drag holds the mouse inside a row delegate: rebuilding the rows would
            // drop the grab, so the node's new info waits until the drag ends.
            if (board.vdrag && board.vdrag.nodes[id]) { board.vdrag.deferred[id] = info; return }
            var it = board.nodeItems[id]; if (it) it.info = info
        }
        function onNodeRemoved(id) {
            if (board.connectionFocus && board.connectionFocus.nodes[id]) board.connectionFocus = null
            for (var i = nodeModel.count - 1; i >= 0; i--)
                if (nodeModel.get(i).nid === id) { nodeModel.remove(i); break }
            if (board.isolate && (board.isolate.a === id || board.isolate.b === id)) board.isolate = null
            if (board.hoverNode === id) board.hoverNode = ""
            board.repaintWires()
        }
        function onWiresChanged(list) {
            board.wireList = JSON.parse(list)
            board.indexWires()
            if (board.selWire && !board.findItem(board.selWire)) board.selWire = ""
            if (board.isolate && board.isolate.wire && !board.findWire(board.isolate.wire)) board.isolate = null
            board.repaintWires()
        }
        function onSelectionChanged(ids, ld) { board.applySel(ids, ld) }
        function onNodesMoved(map, anim) {
            board.animate = anim
            for (var id in map) { var it = board.nodeItems[id]; if (it) { it.x = map[id][0]; it.y = map[id][1] } }
            animTimer.restart()
        }
        function onViewRequested(x, y, z) { zoomTick.stop(); board.panX = x; board.panY = y; board.zoom = z; board.cull() }
        function onFrameRequested(all) { board.frame(all) }
        function onConnectionsFound(nodes, wires) {
            var nm = {}, wm = {}
            for (var i = 0; i < nodes.length; ++i) nm[nodes[i]] = true
            for (var j = 0; j < wires.length; ++j) wm[wires[j]] = true
            board.isolate = null; board.selWire = ""
            board.connectionFocus = {nodes: nm, wires: wm}
            board.frameNodes(nodes)
        }
        function onRenameRequested(id) { board.startRename(id) }
        function onFramesChanged(list) { board.frames = JSON.parse(list) }
        function onFrameEditRequested(id, field) { board.frameEdit = {id: id, field: field} }
        function onLinksChanged(on, mode) {
            board.links = on
            if (board.selWire) board.selWire = ""
            board.repaintWires()
        }
    }
    Timer { id: animTimer; interval: 380; onTriggered: board.animate = false }
    Timer { id: viewSave; interval: 400; onTriggered: bridge.setView(board.panX, board.panY, board.zoom) }
    // A Canvas.requestPaint() before the first frame is dropped (global leaf qt/qml-in-a-host-app).
    Timer {
        id: repaintBurst; interval: 60; repeat: true; property int count: 0
        onTriggered: { board.repaintWires(); if (++count > 8) stop() }
    }
    Component.onCompleted: { reset(); repaintBurst.start() }

    onPanXChanged: viewMoved()
    onPanYChanged: viewMoved()
    onZoomChanged: {
        viewMoved()
        // hysteresis, so a zoom resting on the threshold does not rebuild rows back and forth
        if (far && zoom > 0.5) far = false
        else if (!far && zoom < 0.42) far = true
    }
    onWidthChanged: { cullTick(); board.repaintWires(); bridge.setViewSize(width, height) }
    onHeightChanged: { cullTick(); board.repaintWires(); bridge.setViewSize(width, height) }
    onQueryChanged: board.repaintWires()
    onIsolateChanged: board.repaintWires()
    onSelChanged: board.repaintWires()
    onHoverNodeChanged: board.repaintWires()

    // ------------------------------------------------------------------ view
    // Pan / zoom move the painted wire image; it is repainted when the view rests (wireIdle)
    // or at once when the image no longer covers the view. A whole-board image never runs
    // out, so a pure pan over it repaints nothing.
    function viewMoved() {
        viewSave.restart()
        cullTick()
        var k = zoom / pv.z
        var ox = panX + k * (pv.rx - pv.x), oy = panY + k * (pv.ry - pv.y)
        var covered = pv.whole || (ox <= 0 && oy <= 0 && ox + k * pv.cw >= width && oy + k * pv.ch >= height)
        if (!covered || k < 0.7 || k > 1.45) repaintWires()
        else if (!(pv.whole && k === 1)) wireIdle.restart()
    }

    // Wire canvas extent. Far out a big board is a few thousand px on screen: the canvas then
    // covers the whole board (its screen bbox, padded for bezier overshoot) instead of the
    // view + `wireMargin`, and a far pan only moves the image. On the live 1907-node board at
    // zoom 0.06 the view-sized canvas left its margin every few moves and each repaint cost
    // ~180 ms (run 6). The canvas must be sized before it paints (a resize inside onPaint
    // shows the old image stretched and paints twice), so every repaint request goes through
    // repaintWires -> planWires, coalesced by Qt.callLater (registerNode runs 1900 times in a
    // reset; the bbox is computed once).
    function repaintWires() { Qt.callLater(planWires) }
    function boardBox() {
        if (!boxDirty) return worldBox
        var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, n = 0
        for (var id in nodeItems) {
            var it = nodeItems[id]
            x0 = Math.min(x0, it.x); y0 = Math.min(y0, it.y)
            x1 = Math.max(x1, it.x + it.width); y1 = Math.max(y1, it.y + it.height)
            n++
        }
        worldBox = n ? {x0: x0, y0: y0, x1: x1, y1: y1} : null
        boxDirty = false
        return worldBox
    }
    // -> the whole board's padded screen rect at the current view, or null when it does not
    // fit: wider than wireCap, more than 4x the view canvas' area, or a wire is being dragged
    // (its loose end follows the pointer, which may be off the board).
    function wholeRect() {
        var b = boardBox()
        if (!b || drag) return null
        var w = (b.x1 - b.x0) * zoom, h = (b.y1 - b.y0) * zoom
        // a backward wire overshoots its source port by <= 0.081 of its span; a short forward
        // one by <= 12 * zoom; the widest pen adds 8 * max(0.6, zoom) on every side
        var pen = 8 * Math.max(0.6, zoom), px = 0.09 * w + 12 * zoom + pen
        var r = {x: panX + b.x0 * zoom - px, y: panY + b.y0 * zoom - pen, w: w + 2 * px, h: h + 2 * pen}
        var M = wireMargin
        if (r.w > wireCap || r.h > wireCap || r.w * r.h > 4 * (width + 2 * M) * (height + 2 * M)) return null
        return r
    }
    function planWires() {
        var r = wholeRect(), cw, ch
        if (r) {
            // round up to 256 px and keep a canvas that is already big enough but not much
            // bigger: zooming does not reallocate it on every repaint
            cw = wires.width; ch = wires.height
            if (cw < r.w || cw > r.w + 512) cw = Math.ceil(r.w / 256) * 256
            if (ch < r.h || ch > r.h + 512) ch = Math.ceil(r.h / 256) * 256
        } else {
            cw = width + 2 * wireMargin; ch = height + 2 * wireMargin
        }
        if (wires.width !== cw) wires.width = cw
        if (wires.height !== ch) wires.height = ch
        wires.requestPaint()
    }
    Timer { id: wireIdle; interval: 90; onTriggered: board.repaintWires() }

    // Culling: nodes outside the view (plus a margin) are hidden; throttled, not per frame.
    function cull() {
        var m = 260 / zoom
        viewRect = Qt.rect(-panX / zoom - m, -panY / zoom - m, width / zoom + 2 * m, height / zoom + 2 * m)
    }
    function cullTick() { if (!cullTimer.running) cullTimer.start() }
    Timer { id: cullTimer; interval: 50; onTriggered: board.cull() }

    // Node detail is built a few nodes per tick (~8 ms), not all at once when a zoom crosses
    // `far` or a pan reveals a crowd: building 59 at once froze the board for ~1 s.
    property var buildQueue: []
    function queueBuild(it) { buildQueue.push(it); if (!buildTick.running) buildTick.start() }
    Timer {
        // interval 1, not 0: a repeating 0 ms QML Timer stopped firing after a restart
        id: buildTick; interval: 1; repeat: true
        onTriggered: {
            var q = board.buildQueue, t0 = Date.now()
            while (q.length && Date.now() - t0 < 8) {
                var it = q.shift()
                // a delegate destroyed or replaced since it asked is no longer in nodeItems
                if (!it || board.nodeItems[it.nid] !== it || it.built || board.far || !it.visible) continue
                it.built = true
            }
            if (!q.length) stop()
        }
    }

    // Smooth zoom (wheel, Alt+RMB drag): the input moves a goal, a ~60 Hz tick eases the
    // view towards it in log space around the pointer.
    property real zoomGoal: 1.0
    property point zoomAnchor: Qt.point(0, 0)
    function zoomSmooth(goal, mx, my) {
        zoomGoal = Math.min(maxZoom, Math.max(minZoom, goal))
        zoomAnchor = Qt.point(mx, my)
        if (!zoomTick.running) zoomTick.start()
    }
    Timer {
        id: zoomTick; interval: 16; repeat: true
        onTriggered: {
            var z = board.zoom * Math.pow(board.zoomGoal / board.zoom, 0.3)
            if (Math.abs(Math.log(board.zoomGoal / z)) < 0.002) { z = board.zoomGoal; stop() }
            board.zoomAt(z / board.zoom, board.zoomAnchor.x, board.zoomAnchor.y)
        }
    }
    function zoomAt(f, mx, my) {
        var nz = Math.min(maxZoom, Math.max(minZoom, zoom * f))
        panX = mx - (mx - panX) * (nz / zoom)
        panY = my - (my - panY) * (nz / zoom)
        zoom = nz
    }
    function frame(all) {
        var ids = []
        if (!all) for (var k in sel) if (nodeItems[k]) ids.push(k)
        if (!ids.length) for (var j in nodeItems) ids.push(j)
        frameNodes(ids)
    }
    function frameNodes(ids) {
        if (!ids.length) return
        zoomTick.stop()
        var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9
        for (var i = 0; i < ids.length; i++) {
            var it = nodeItems[ids[i]] || pendingInfo[ids[i]]
            if (!it) continue
            x0 = Math.min(x0, it.x); y0 = Math.min(y0, it.y - 20)
            x1 = Math.max(x1, it.x + it.width); y1 = Math.max(y1, it.y + it.height)
        }
        var pad = 56
        var z = Math.min(1.15, Math.max(minZoom, Math.min((width - pad * 2) / Math.max(1, x1 - x0),
                                                          (height - pad * 2) / Math.max(1, y1 - y0))))
        zoom = z
        panX = (width - (x1 - x0) * z) / 2 - x0 * z
        panY = (height - (y1 - y0) * z) / 2 - y0 * z
    }

    // ------------------------------------------------------------------ node drag
    function dragStarts() {
        var s = {}
        for (var id in sel) { var it = nodeItems[id]; if (it) s[id] = [it.x, it.y] }
        return s
    }
    function dragTo(starts, dx, dy) {
        for (var id in starts) {
            var it = nodeItems[id]
            if (!it) continue
            var x = starts[id][0] + dx, y = starts[id][1] + dy
            if (snap) { x = Math.round(x / gridStep) * gridStep; y = Math.round(y / gridStep) * gridStep }
            it.x = x; it.y = y
        }
    }
    function commitDrag(starts) {
        var m = {}
        for (var id in starts) { var it = nodeItems[id]; if (it) m[id] = [it.x, it.y] }
        bridge.moveNodes(m)
    }

    // ------------------------------------------------------------------ wiring
    function wireStart(nid, r, side, bp, modifiers) {
        var distribute = (modifiers & Qt.AltModifier) !== 0
        if (side === "in" && r.inConn) {
            var w = wireInto(nid, r.key)
            if (w) {   // pick the wire up off this input (drop elsewhere = move, drop on empty = cut)
                hiddenWire = distribute ? "" : w.id
                drag = {pick: !distribute, fanout: distribute, targets: [], oldDst: nid, oldPlug: r.key, nid: w.src, key: w.srcPlug, side: "out",
                        want: "in", cls: w.cls, compound: w.compound, color: w.color, ly: w.srcY,
                        mx: bp.x, my: bp.y}
                board.repaintWires()
                return
            }
        }
        drag = {pick: false, fanout: distribute && side === "out", targets: [], nid: nid, key: r.key, side: side, want: side === "out" ? "in" : "out",
                cls: r.cls, compound: r.compound, color: r.color, ly: anchorOf(nid, r.key), mx: bp.x, my: bp.y,
                x0: bp.x, y0: bp.y}
        board.repaintWires()
    }
    function wireMove(bp) {
        if (!drag) return
        if (drag.fanout) sweepPorts(Qt.point(drag.mx, drag.my), bp)
        // Mutated in place: re-assigning `drag` would re-run portState() on every port.
        drag.mx = bp.x; drag.my = bp.y
        var hit = portAt(bp.x, bp.y, drag.want, drag.nid)
        if (JSON.stringify(hit) !== JSON.stringify(dropHit)) dropHit = hit
        board.repaintWires()
    }
    function sweepPorts(a, b) {
        // Test the whole mouse segment so a fast stroke does not skip a socket.
        var dx = b.x - a.x, dy = b.y - a.y, length2 = dx * dx + dy * dy
        for (var id in nodeItems) {
            var it = nodeItems[id]
            if (id === drag.nid || !it.info || it.info.dead) continue
            var edge = panX + zoom * it.x, top = panY + zoom * it.y
            if (edge < Math.min(a.x, b.x) - 10 || edge > Math.max(a.x, b.x) + 10
                    || top > Math.max(a.y, b.y) + 10
                    || top + it.height * zoom < Math.min(a.y, b.y) - 10) continue
            var rows = it.info.rows
            for (var i = 0; i < rows.length; ++i) {
                var r = rows[i]
                if (!r.inPort || !compat(drag.cls, drag.compound, r.cls, r.compound)) continue
                var p = portPt(id, anchorOf(id, r.key), false)
                if (!p) continue
                var t = length2 ? Math.max(0, Math.min(1, ((p.x-a.x)*dx + (p.y-a.y)*dy) / length2)) : 0
                var ex = p.x - a.x - t * dx, ey = p.y - a.y - t * dy
                if (ex * ex + ey * ey > 100) continue
                var exists = false
                for (var j = 0; j < drag.targets.length; ++j)
                    if (drag.targets[j].nid === id && drag.targets[j].key === r.key) { exists = true; break }
                if (!exists) drag.targets.push({nid: id, key: r.key})
            }
        }
    }
    function wireCancel() {
        drag = null; dropHit = null; hiddenWire = ""
        board.repaintWires()
    }
    function wireEnd(bp) {
        if (!drag) return
        if (drag.fanout) wireMove(bp)
        var d = drag, hit = portAt(bp.x, bp.y, d.want, d.nid)
        drag = null; dropHit = null; hiddenWire = ""
        if (d.fanout) {
            if (d.targets.length) bridge.distributeWire(d.nid, d.key, d.targets)
        } else if (d.pick) {
            if (hit && hit.nid === d.oldDst && hit.key === d.oldPlug) { board.repaintWires(); return }
            bridge.rerouteInput(d.oldDst, d.oldPlug, hit ? hit.nid : "", hit ? hit.key : "")
        } else if (hit) {
            if (d.side === "out") bridge.connectPlugs(d.nid, d.key, hit.nid, hit.key)
            else bridge.connectPlugs(hit.nid, hit.key, d.nid, d.key)
        } else if (!nodeAtScreen(bp.x, bp.y) && Math.abs(bp.x - d.x0) + Math.abs(bp.y - d.y0) > 24) {
            // Blender link-drag search: a new wire dropped on empty canvas asks which node to
            // create there and connects it.
            var wp = toWorld(bp.x, bp.y)
            bridge.linkSearch(d.nid, d.key, d.side, wp.x, wp.y)
        }
        board.repaintWires()
    }

    // ------------------------------------------------------------------ value fields (Blender)
    // LMB or RMB drag on a number field slides it: Shift fine, Ctrl snap (Ctrl+Shift fine snap).
    // Dragging vertically first sweeps over more fields of the same kind, which then slide
    // together; a bool drag toggles every bool it passes. Maya gets live values with no undo
    // entries while dragging; release commits them as one undo step, Escape restores them.
    property var vdrag: null
    property int vtick: 0
    function fieldKey(nid, key) { return nid + "|" + key }
    function shownValue(nid, key, v) {
        var t = vtick
        if (!vdrag) return v
        var f = vdrag.map[fieldKey(nid, key)]
        return f ? f.text : v
    }
    function inValueDrag(nid, key) { var t = vtick; return !!(vdrag && vdrag.map[fieldKey(nid, key)]) }
    function fmtValue(v, isInt) {
        if (isInt) return String(Math.round(v))
        var s = v.toFixed(3).replace(/0+$/, "")
        if (s.charAt(s.length - 1) === ".") s += "0"
        return s === "-0.0" ? "0.0" : s
    }
    // The value box of a row under a screen point (same geometry as Node.qml's valueBox).
    function fieldAt(sx, sy, kind) {
        if (far) return null
        var w = toWorld(sx, sy)
        for (var id in nodeItems) {
            var it = nodeItems[id]
            if (!it.info || it.info.dead || !it.visible) continue
            if (w.x < it.x || w.x > it.x + it.width || w.y < it.y || w.y > it.y + it.height) continue
            var rows = it.info.rows, ly = w.y - it.y, lx = w.x - it.x
            for (var i = 0; i < rows.length; i++) {
                var r = rows[i]
                if (r.valueKind !== kind || ly < r.y || ly >= r.y + r.h) continue
                var bw = kind === "bool" ? 40 : 58, bx = it.width - 12 - bw - (r.outPort ? 4 : 0)
                if (lx >= bx - 8 && lx <= bx + bw + 8) return {nid: id, key: r.key, value: r.value}
            }
        }
        return null
    }
    function addField(f) {
        var d = vdrag, k = fieldKey(f.nid, f.key)
        if (d.map[k]) return
        var m = null
        if (d.kind === "num") {
            m = bridge.valueMeta(f.nid, f.key)
            if (!m) return
        }
        var e = {nid: f.nid, key: f.key, orig: f.value, meta: m, text: f.value}
        if (d.kind === "bool") e.text = d.state ? "on" : "off"
        d.map[k] = e; d.list.push(e); d.nodes[f.nid] = true
    }
    function valueStart(nid, r, sp, button, mods) {
        tipStop()
        vdrag = {kind: r.valueKind, map: {}, list: [], nodes: {}, deferred: {}, phase: 0, button: button,
                 x0: sp.x, y0: sp.y, lx: sp.x, ly: sp.y, sx: sp.x, mods: mods, moved: false,
                 state: r.valueKind === "bool" ? r.value !== "on" : false}
        addField({nid: nid, key: r.key, value: r.value})
        if (vdrag.kind === "bool") valuePreview()
        vtick++
    }
    function valueMove(sp, mods) {
        var d = vdrag
        if (!d) return
        if (d.phase === 0) {
            if (Math.abs(sp.x - d.x0) + Math.abs(sp.y - d.y0) < 4) return
            d.moved = true
            d.phase = (d.kind === "bool" || Math.abs(sp.y - d.y0) > Math.abs(sp.x - d.x0)) ? 1 : 2
            d.sx = d.x0
        }
        if (d.phase === 1) {
            var stepX = sp.x - d.lx, stepY = sp.y - d.ly
            var n = Math.max(1, Math.ceil(Math.abs(stepY) / 4))
            for (var i = 1; i <= n; i++) {
                var f = fieldAt(d.lx + stepX * i / n, d.ly + stepY * i / n, d.kind)
                if (f) addField(f)
            }
            if (Math.abs(stepY) >= Math.abs(stepX)) d.sx = sp.x
            else if (d.kind === "num" && Math.abs(sp.x - d.sx) > 10) { d.phase = 2; d.sx = sp.x }
            if (d.kind === "bool") valuePreview()
        }
        if (d.phase === 2) {
            var shift = (mods & Qt.ShiftModifier) !== 0, ctrl = (mods & Qt.ControlModifier) !== 0
            if (shift !== ((d.mods & Qt.ShiftModifier) !== 0)) {
                // precision changed mid-drag: continue from the current values, no jump
                for (var j = 0; j < d.list.length; j++) d.list[j].meta.v = parseFloat(d.list[j].text)
                d.sx = sp.x
            }
            var px = sp.x - d.sx
            for (var k = 0; k < d.list.length; k++) {
                var e = d.list[k], m = e.meta
                var v = m.v + px * m.step * (shift ? 0.1 : 1)
                if (ctrl) { var u = shift ? m.fine : m.coarse; v = Math.round(v / u) * u }
                if (m.min !== null && m.min !== undefined) v = Math.max(m.min, v)
                if (m.max !== null && m.max !== undefined) v = Math.min(m.max, v)
                e.text = fmtValue(v, m.isInt)
            }
            valuePreview()
        }
        d.mods = mods
        d.lx = sp.x; d.ly = sp.y
        vtick++
    }
    function valueRows(withOrig) {
        var out = []
        for (var i = 0; i < vdrag.list.length; i++) {
            var e = vdrag.list[i]
            out.push(withOrig ? [e.nid, e.key, e.orig, e.text] : [e.nid, e.key, e.text])
        }
        return out
    }
    function valuePreview() { Qt.callLater(valueFlush) }
    function valueFlush() { if (vdrag) bridge.previewValues(valueRows(false)) }
    function valueFinish() {
        var d = vdrag
        vdrag = null
        for (var id in d.deferred) { var it = nodeItems[id]; if (it) it.info = d.deferred[id] }
        vtick++
    }
    // -> "edit" when it was a plain click on a number field (the caller opens the text editor)
    // A slot that throws surfaces here as a JS exception: `finally` still ends the drag, or a
    // left-over vdrag would swallow every later info of its nodes (frozen rows).
    function valueEnd() {
        var d = vdrag
        if (!d) return ""
        // A vertical sweep that never slid selects the fields for typing (Blender multi-edit):
        // vdrag stays in phase 3 until the editor confirms (valueTyped) or is left (valueEditDone).
        if (d.moved && d.kind === "num" && d.phase === 1 && d.list.length > 1) {
            d.phase = 3
            vtick++
            return "multi"
        }
        if ((!d.moved || d.phase === 1) && d.kind === "num") {
            // a click, or a vertical drag that stayed on its own field: nothing was set
            valueFinish()
            if (d.button === Qt.RightButton) { if (!d.moved && d.list.length) bridge.nodeMenu(d.list[0].nid); return "" }
            return "edit"
        }
        try { bridge.commitValues(valueRows(true)) } finally { valueFinish() }
        return ""
    }
    function valueCancel() {
        if (!vdrag) return
        try { bridge.revertValues(valueRows(true)) } finally { valueFinish() }
    }
    // Phase 3: the number typed into one swept field goes to all of them, clamped per field,
    // as one undo step. Text that is not a number cancels.
    function valueTyped(text) {
        var d = vdrag
        if (!d || d.phase !== 3) return false
        var v = parseFloat(text)
        if (isNaN(v)) { valueCancel(); return true }
        for (var i = 0; i < d.list.length; i++) {
            var e = d.list[i], m = e.meta, x = v
            if (m.min !== null && m.min !== undefined) x = Math.max(m.min, x)
            if (m.max !== null && m.max !== undefined) x = Math.min(m.max, x)
            e.text = fmtValue(x, m.isInt)
        }
        try { bridge.commitValues(valueRows(true)) } finally { valueFinish() }
        return true
    }
    // The editor lost focus without confirming (e.g. invalid text): drop the selection.
    function valueEditDone() { if (vdrag && vdrag.phase === 3) valueFinish() }
    // Ctrl+wheel over a field steps it (Blender): numbers by their snap, enums to the next item.
    function valueWheel(nid, r, up) {
        if (r.valueKind === "enum") { bridge.stepEnum(nid, r.key, up ? -1 : 1); return }
        if (r.valueKind === "bool") { bridge.toggleBool(nid, r.key); return }
        var m = bridge.valueMeta(nid, r.key)
        if (!m) return
        var v = m.v + (up ? 1 : -1) * m.coarse
        if (m.min !== null && m.min !== undefined) v = Math.max(m.min, v)
        if (m.max !== null && m.max !== undefined) v = Math.min(m.max, v)
        bridge.setValue(nid, r.key, fmtValue(v, m.isInt))
    }

    // ------------------------------------------------------------------ tooltip
    property var tipPending: null
    function tipStart(nid, key, item) {
        if (drag) return
        tipPending = {nid: nid, key: key, item: item}
        tipTimer.restart()
    }
    function tipBundle(id, sx, sy) {
        if (drag) return
        tipPending = {ids: idsOf(id), x: sx, y: sy}
        tipTimer.restart()
    }
    function tipStop() { tipTimer.stop(); tipPending = null; tip.visible = false }
    Timer {
        id: tipTimer; interval: 350
        onTriggered: {
            var t = board.tipPending
            if (!t) return
            var html = t.ids ? bridge.bundleTip(t.ids) : bridge.tooltip(t.nid, t.key)
            if (!html) return
            tipText.text = html
            var p = t.ids ? Qt.point(t.x + 16, t.y + 16) : t.item.mapToItem(board, 16, 16)
            tip.x = Math.min(p.x, board.width - tip.width - 8)
            tip.y = Math.min(p.y, board.height - tip.height - 8)
            tip.visible = true
        }
    }

    // open the name editor in a node's header (F2, node menu, double-click on the name).
    // Far out the header text is not built, so there is nothing to type into.
    function startRename(id) {
        var it = nodeItems[id]
        if (!id || !it || it.dead || far) return
        tipStop()
        renaming = id
    }

    // ------------------------------------------------------------------ keys (provisional v1 map, see panel Help)
    Keys.onPressed: function(event) {
        if (!board.activeFocus) { event.accepted = false; return }
        var k = event.key, m = event.modifiers
        event.accepted = true
        if (k === Qt.Key_Escape && drag) { wireCancel(); return }
        if (k === Qt.Key_Escape && vdrag) { valueCancel(); return }
        if (m & Qt.AltModifier) {
            if (k === Qt.Key_I) bridge.transfer("in")
            else if (k === Qt.Key_O) bridge.transfer("out")
            else if (k === Qt.Key_T) bridge.transfer("all")
            else if (k === Qt.Key_L) bridge.linkByName((m & Qt.ShiftModifier) !== 0)
            else if (k === Qt.Key_S) bridge.swapSelected()
            else event.accepted = false
            return
        }
        if (m & Qt.ControlModifier) {
            if (m & Qt.ShiftModifier) { event.accepted = false; return }
            if (k === Qt.Key_C) bridge.copyFragment()
            else if (k === Qt.Key_V) bridge.pasteFragment(mouseWorld.x, mouseWorld.y)
            else event.accepted = false
            return
        }
        if (k === Qt.Key_D && (m & Qt.ShiftModifier)) { bridge.duplicateFragment(); return }
        if (k === Qt.Key_K) { bridge.linkByName((m & Qt.ShiftModifier) !== 0); return }
        if (k === Qt.Key_1) bridge.displayMode("simple")
        else if (k === Qt.Key_2) bridge.displayMode("connected")
        else if (k === Qt.Key_3) bridge.displayMode("full")
        else if (k === Qt.Key_4) bridge.displayMode("custom")
        else if (k === Qt.Key_W) bridge.setLinks(links ? "off" : "on")
        else if (k === Qt.Key_F2) startRename(lead)
        else if (k === Qt.Key_F) frame(false)
        else if (k === Qt.Key_A) frame(true)
        else if (k === Qt.Key_Delete || k === Qt.Key_Backspace) {
            if (selWire) { bridge.disconnectWires(idsOf(selWire)); selWire = "" }
            else bridge.deleteSelected()
        }
        else if (k === Qt.Key_Escape) {
            connectionFocus = null
            if (lazy || knife || marquee || drag) {
                lazy = null; knife = null; marquee = null; drag = null
                canvasMouse.gesture = 0; fx.requestPaint()
            } else { isolate = null; selWire = ""; bridge.clearSelection() }
        }
        else event.accepted = false
    }

    // ------------------------------------------------------------------ layers
    Rectangle { anchors.fill: parent; color: th.canvas }

    // Faint dot grid: radial-gradient(--grid 1px, transparent 1.3px)
    // in 22*zoom cells, i.e. a round ~1.15 px dot at the centre of each cell, the same size at
    // every zoom. Drawn by the GPU: the JS Canvas version cost ~20 us per dot (40-60 ms a frame)
    // and lagged zooming out. Zoomed far out the step doubles so dots never merge into a haze.
    ShaderEffect {
        id: grid
        anchors.fill: parent
        visible: board.showGrid
        readonly property real base: board.gridStep * board.zoom
        // `cell`, not `step`: step() is a GLSL built-in, and the Qt 6 shader compiler renames a
        // uniform called step, which then never receives its value on OpenGL.
        property real cell: { var s = base; while (s < 8) s *= 2; return s }
        property point origin: Qt.point(board.panX + (base - cell) / 2, board.panY + (base - cell) / 2)
        property size res: Qt.size(width, height)
        property real alpha: board.th.gridAlpha
        // Qt 6 (Maya 2025+) needs a precompiled shader: source in tools/shaders/grid.frag.
        fragmentShader: (typeof qtMajor !== "undefined" && qtMajor >= 6) ? Qt.resolvedUrl("shaders/grid.frag.qsb") : "
            varying highp vec2 qt_TexCoord0;
            uniform highp float cell;
            uniform highp vec2 origin;
            uniform highp vec2 res;
            uniform lowp float alpha;
            uniform lowp float qt_Opacity;
            void main() {
                highp vec2 c = mod(qt_TexCoord0 * res - origin, cell) - 0.5 * cell;
                lowp float a = alpha * qt_Opacity * (1.0 - smoothstep(0.9, 1.45, length(c)));
                gl_FragColor = vec4(a, a, a, a);
            }"
    }

    // Wires: a screen-space Canvas (QPainter antialiasing at every zoom), painted
    // over the view + `wireMargin` px on every side, or over the whole board (planWires), and
    // moved / scaled with the view between repaints: canvas pixel c shows at
    // panX + k * (c + pv.rx - pv.x), k = zoom / pv.z. Size is set by planWires only.
    Canvas {
        id: wires
        width: board.width + 2 * board.wireMargin
        height: board.height + 2 * board.wireMargin
        transformOrigin: Item.TopLeft
        scale: board.zoom / board.pv.z
        x: board.panX + scale * (board.pv.rx - board.pv.x)
        y: board.panY + scale * (board.pv.ry - board.pv.y)
        onPaint: board.paintWires(getContext("2d"))
    }

    function paintWires(ctx) {
        var t0 = Date.now()
        ctx.reset()
        // the region this canvas covers: the whole board if planWires sized it for that,
        // else the view centred in it
        var cw = wires.width, ch = wires.height, r = wholeRect(), whole = !!r && cw >= r.w && ch >= r.h
        var rx = Math.floor(whole ? r.x - (cw - r.w) / 2 : -(cw - width) / 2)
        var ry = Math.floor(whole ? r.y - (ch - r.h) / 2 : -(ch - height) / 2)
        pv = {x: panX, y: panY, z: zoom, rx: rx, ry: ry, cw: cw, ch: ch, whole: whole}
        ctx.translate(-rx, -ry)
        var vx0 = rx, vy0 = ry, vx1 = rx + cw, vy1 = ry + ch
        var z = Math.max(0.6, zoom)
        var groups = {}, order = [], drawn = [], halos = [], labels = []

        function add(id, a, b, color, alpha, lw, uc, n, hot) {
            var dx = bezDx(a.x, b.x)
            var x0 = Math.min(a.x, b.x - dx), x1 = Math.max(b.x, a.x + dx)
            var y0 = Math.min(a.y, b.y), y1 = Math.max(a.y, b.y)
            if (x1 < vx0 || x0 > vx1 || y1 < vy0 || y0 > vy1) return
            var key = color + "|" + alpha + "|" + lw
            var g = groups[key]
            if (!g) { g = groups[key] = {color: color, alpha: alpha, lw: lw, segs: []}; order.push(key) }
            var s = {id: id, ax: a.x, ay: a.y, bx: b.x, by: b.y, dx: dx, x0: x0, y0: y0, x1: x1, y1: y1, uc: uc, n: n}
            g.segs.push(s)
            drawn.push(s)
            if (id === selWire) halos.push(s)
            // Canvas text costs ~2 ms a label: counts only where the eye is (hover, selection,
            // focus); 500 labels made a repaint take 1.2 s.
            if (n > 1 && hot && labels.length < 60) labels.push(s)
        }

        // focus: the hovered node, else the selection
        var focus = {}, hasFocus = false
        if (hoverNode) { focus[hoverNode] = true; hasFocus = true }
        else for (var s in sel) { focus[s] = true; hasFocus = true }
        var iso = isolate

        function style(w, isBundle) {
            // -> [alpha, lw]; detail wires of the focus stand out over the rest
            // lw 1 = hairline: a 1 px stroke at every zoom (see the stroke loop)
            var alpha = isBundle ? 0.55 : 0.85, lw = 1
            if (hasFocus) {
                if (focus[w.src] || focus[w.dst]) { alpha = 1; lw = 2.2 } else alpha = isBundle ? 0.16 : 0.18
            }
            var na = nodeItems[w.src], nb = nodeItems[w.dst]
            if ((na && na.dimmed) || (nb && nb.dimmed)) alpha = Math.min(alpha, 0.14)
            if (iso) {
                var pair = (w.src === iso.a && w.dst === iso.b) || (w.src === iso.b && w.dst === iso.a)
                var on = iso.wire ? w.id === iso.wire : pair
                if (on) { alpha = 1; lw = 2.2 } else alpha = 0.07
            }
            if (connectionFocus) {
                var found = isBundle ? connectionFocus.nodes[w.src] && connectionFocus.nodes[w.dst]
                                     : connectionFocus.wires[w.id]
                if (!isBundle && !found) {
                    var members = idsOf(w.id)
                    for (var mi = 0; mi < members.length; ++mi)
                        if (connectionFocus.wires[members[mi]]) { found = true; break }
                }
                if (found) { alpha = 1; lw = 2.2 } else alpha = 0.07
            }
            if (w.id === hoverWire || w.id === selWire) { alpha = 1; lw = 2.4 }
            return [alpha, lw]
        }

        var list = wireList, i, w, st, e
        if (!links) {
            for (i = 0; i < drawList.length; i++) {
                w = drawList[i]
                if (w.id === hiddenWire) continue
                e = wireEnds(w)
                if (!e) continue
                st = style(w, false)
                add(w.id, e[0], e[1], w.color, st[0], st[1], w.uc, 1, false)
            }
        } else {
            // Node links: every connection of the focus / isolated pair in detail (if not too
            // many), one wire per node pair for the rest.
            var detail = {}, nd = 0
            function wantDetail(x) {
                return (hasFocus && (focus[x.src] || focus[x.dst])) ||
                       (connectionFocus && connectionFocus.nodes[x.src] && connectionFocus.nodes[x.dst]) ||
                       (iso && ((x.src === iso.a && x.dst === iso.b) || (x.src === iso.b && x.dst === iso.a)))
            }
            if (hasFocus || iso || connectionFocus) {
                for (i = 0; i < list.length && nd <= detailLimit; i++)
                    if (wantDetail(list[i])) nd++
            }
            var showDetail = nd > 0 && nd <= detailLimit
            for (i = 0; i < bundles.length; i++) {
                var b = bundles[i]
                if (showDetail && wantDetail(b)) { detail[b.id] = true; continue }
                var a = portPt(b.src, 14, true), c = portPt(b.dst, 14, false)
                if (!a || !c) continue
                st = style(b, true)
                var n = b.ids.length
                var blw = st[1] + Math.min(2.6, Math.log(n) / Math.LN2 * 0.5)
                var hot = b.id === hoverWire || b.id === selWire || (hasFocus && (focus[b.src] || focus[b.dst]))
                add(b.id, a, c, b.mixed ? th.muted : b.color, st[0], blw, false, n, hot)
            }
            if (showDetail) {
                for (i = 0; i < drawList.length; i++) {
                    w = drawList[i]
                    if (!detail["b:" + w.src + ">" + w.dst] || w.id === hiddenWire) continue
                    e = wireEnds(w)
                    if (!e) continue
                    st = style(w, false)
                    add(w.id, e[0], e[1], w.color, st[0], st[1], w.uc, 1, false)
                }
            }
        }

        // clip box of wide strokes: the canvas plus room for the widest pen
        var cp = 8 * z, cx0 = vx0 - cp, cy0 = vy0 - cp, cx1 = vx1 + cp, cy1 = vy1 + cp
        // selection halo under the wire
        for (i = 0; i < halos.length; i++) {
            ctx.globalAlpha = 0.28; ctx.strokeStyle = th.ink; ctx.lineWidth = (2.4 + 3) * z
            ctx.beginPath(); curveClip(ctx, halos[i], cx0, cy0, cx1, cy1); ctx.stroke()
        }
        // Style set once per group, but one stroke per wire: QPainter's rasterizer degrades on a
        // path of hundreds of crossing antialiased curves (a 500-node column: one path per style
        // 12-13 s a paint, one stroke per wire 0.4 s; tests/_perf_probe.py column:500).
        var chevrons = zoom >= 0.4 && drawn.length < 2500
        var sgs
        for (var gi = 0; gi < order.length; gi++) {
            var g = groups[order[gi]]
            sgs = g.segs
            ctx.globalAlpha = g.alpha
            ctx.strokeStyle = g.color
            // Plain wires are 1 px hairlines at every zoom: QPainter strokes a pen of <= 1 device
            // px on its fast cosmetic path, a wider one is outlined into a polygon and filled
            // antialiased -- that is why the board was fastest zoomed far out (1.6 * 0.6 < 1 px)
            // and slowed down zooming in. Only the few hot wires (hover, selection, focus,
            // isolation) and node-link bundles stay wide and scale with the zoom.
            // A pen under 1.5 px snaps to the hairline too: node-link bundles at z 0.6 came out
            // 0.9-2.2 px, so a far 1900-node board stroked thousands of them the slow way.
            var wide = g.lw > 1 && g.lw * z >= 1.5
            ctx.lineWidth = wide ? g.lw * z : 1
            ctx.lineCap = "round"; ctx.lineJoin = "round"
            // (Batching N curves per stroke() was measured in run 6: no gain at N = 8 or 32.)
            for (i = 0; i < sgs.length; i++) {
                ctx.beginPath()
                if (!wide) curveTo(ctx, sgs[i]); else curveClip(ctx, sgs[i], cx0, cy0, cx1, cy1)
                ctx.stroke()
            }
            if (!chevrons) continue
            // Direction chevron at mid-wire; doubled when a unitConversion sits on the path.
            ctx.lineWidth = g.lw <= 1 ? 1 : Math.max(1.2, 1.7 * z)
            ctx.beginPath()
            for (i = 0; i < sgs.length; i++) chevron(ctx, sgs[i], z)
            ctx.stroke()
        }
        // connection counts on node links
        if (labels.length && zoom >= 0.35) {
            ctx.globalAlpha = 1
            ctx.font = Math.round(10 * z) + "px sans-serif"
            ctx.textAlign = "center"; ctx.textBaseline = "middle"
            for (i = 0; i < labels.length; i++) {
                var L = labels[i], mid = bezPtsD(L.ax, L.ay, L.bx, L.by, L.dx, 2)[1]
                var txt = String(L.n), tw = (txt.length * 6.2 + 8) * z
                ctx.fillStyle = th.canvas
                ctx.fillRect(mid.x - tw / 2, mid.y - 13 * z, tw, 10 * z + 2)
                ctx.fillStyle = th.muted
                ctx.fillText(txt, mid.x, mid.y - 8 * z)
            }
        }
        geo = drawn
        paintStats = {ms: Date.now() - t0, curves: drawn.length, groups: order.length, labels: labels.length}

        if (drag) {
            var d = drag
            var o = portPt(d.nid, d.ly, d.side === "out")
            if (o) {
                var m = Qt.point(d.mx, d.my)
                if (dropHit) {
                    var hy = anchorOf(dropHit.nid, dropHit.key)
                    var hp = portPt(dropHit.nid, hy, d.want === "out")
                    if (hp) m = hp
                }
                var a2 = d.side === "out" ? o : m, b2 = d.side === "out" ? m : o
                var ddx = bezDx(a2.x, b2.x)
                ctx.globalAlpha = 1; ctx.strokeStyle = d.color; ctx.lineWidth = 1.8 * z
                ctx.beginPath()
                curveTo(ctx, {ax: a2.x, ay: a2.y, bx: b2.x, by: b2.y, dx: ddx})
                ctx.stroke()
                if (d.fanout) {
                    for (var ti = 0; ti < d.targets.length; ++ti) {
                        var target = d.targets[ti]
                        var tp = portPt(target.nid, anchorOf(target.nid, target.key), false)
                        if (!tp) continue
                        ctx.beginPath()
                        curveTo(ctx, {ax: o.x, ay: o.y, bx: tp.x, by: tp.y, dx: bezDx(o.x, tp.x)})
                        ctx.stroke()
                    }
                }
            }
        }
    }
    // Adds a wire's cubic to the path. (Clipping long hairlines to the canvas was measured and
    // dropped: no gain once wires are stroked one by one, and its JS cost 5x on 500 nodes.)
    function curveTo(ctx, q) {
        ctx.moveTo(q.ax, q.ay); ctx.bezierCurveTo(q.ax + q.dx, q.ay, q.bx - q.dx, q.by, q.bx, q.by)
    }
    // Wide (hot) wires only: a pen > 1 px is outlined over the curve's whole length, off-canvas
    // part included. At zoom 2.5 the wires of a selected fan-out node ran 10-40k px past the
    // canvas and one repaint rasterized for 280 ms (live, 87 wires; 6 ms unselected). Splits the
    // cubic (de Casteljau) and adds only the pieces whose control box meets the canvas
    // [x0, x1] x [y0, y1]; neighbouring pieces stay one subpath, so no caps show inside.
    function curveClip(ctx, q, x0, y0, x1, y1) {
        var st = {open: false, ex: 0, ey: 0}
        clipPiece(ctx, st, q.ax, q.ay, q.ax + q.dx, q.ay, q.bx - q.dx, q.by, q.bx, q.by, x0, y0, x1, y1, 0)
    }
    function clipPiece(ctx, st, p0x, p0y, p1x, p1y, p2x, p2y, p3x, p3y, x0, y0, x1, y1, depth) {
        var bx0 = Math.min(p0x, p1x, p2x, p3x), bx1 = Math.max(p0x, p1x, p2x, p3x)
        var by0 = Math.min(p0y, p1y, p2y, p3y), by1 = Math.max(p0y, p1y, p2y, p3y)
        if (bx1 < x0 || bx0 > x1 || by1 < y0 || by0 > y1) { st.open = false; return }
        var inside = bx0 >= x0 && bx1 <= x1 && by0 >= y0 && by1 <= y1
        if (inside || depth >= 16 || Math.max(bx1 - bx0, by1 - by0) < 96) {
            if (!st.open || st.ex !== p0x || st.ey !== p0y) ctx.moveTo(p0x, p0y)
            ctx.bezierCurveTo(p1x, p1y, p2x, p2y, p3x, p3y)
            st.open = true; st.ex = p3x; st.ey = p3y
            return
        }
        var ax = (p0x + p1x) / 2, ay = (p0y + p1y) / 2, bx = (p1x + p2x) / 2, by = (p1y + p2y) / 2
        var cx = (p2x + p3x) / 2, cy = (p2y + p3y) / 2, dx = (ax + bx) / 2, dy = (ay + by) / 2
        var ex = (bx + cx) / 2, ey = (by + cy) / 2, mx = (dx + ex) / 2, my = (dy + ey) / 2
        clipPiece(ctx, st, p0x, p0y, ax, ay, dx, dy, mx, my, x0, y0, x1, y1, depth + 1)
        clipPiece(ctx, st, mx, my, ex, ey, cx, cy, p3x, p3y, x0, y0, x1, y1, depth + 1)
    }
    function chevron(ctx, q, z) {
        var t = 0.5, u = 0.5, ax = q.ax, ay = q.ay, bx = q.bx, by = q.by, dx = q.dx
        var mx = u*u*u*ax + 3*u*u*t*(ax + dx) + 3*u*t*t*(bx - dx) + t*t*t*bx
        var my = u*u*u*ay + 3*u*u*t*ay + 3*u*t*t*by + t*t*t*by
        var tx = 3*u*u*dx + 6*u*t*((bx - dx) - (ax + dx)) + 3*t*t*dx
        var ty = 6*u*t*(by - ay)
        var L = Math.sqrt(tx*tx + ty*ty) || 1
        tx /= L; ty /= L
        var nx = -ty, ny = tx, s = 4 * z, offs = q.uc ? [-3.5, 3.5] : [0]
        if (q.n > 1) { mx += tx * 6 * z; my += ty * 6 * z }
        for (var i = 0; i < offs.length; i++) {
            var cx = mx + tx * (offs[i] + 3) * z, cy = my + ty * (offs[i] + 3) * z
            var bx2 = cx - tx * 5 * z, by2 = cy - ty * 5 * z
            ctx.moveTo(bx2 + nx * s, by2 + ny * s); ctx.lineTo(cx, cy); ctx.lineTo(bx2 - nx * s, by2 - ny * s)
        }
    }

    // Nodes whose centre lies inside a frame belong to it (dragged with it, fitted, selected).
    function frameMembers(f) {
        var out = []
        for (var id in nodeItems) {
            var it = nodeItems[id], cx = it.x + it.width / 2, cy = it.y + it.height / 2
            if (cx > f.x && cx < f.x + f.w && cy > f.y && cy < f.y + f.h) out.push(id)
        }
        return out
    }
    function frameAtScreen(x, y) {
        var p = toWorld(x, y)
        for (var i = frames.length - 1; i >= 0; i--) {
            var f = frames[i]
            if (p.x >= f.x && p.x <= f.x + f.w && p.y >= f.y && p.y <= f.y + f.h) return f
        }
        return null
    }
    function nodeAtScreen(x, y) {
        var p = toWorld(x, y)
        for (var id in nodeItems) {
            var it = nodeItems[id]
            if (!it.dead && p.x >= it.x && p.x <= it.x + it.width &&
                    p.y >= it.y && p.y <= it.y + it.height) return id
        }
        return ""
    }

    // Canvas gestures: MMB / Alt+LMB pan, LMB marquee or wire pick, RMB menu, Ctrl/Shift+RMB knife,
    // Alt+RMB zoom drag, wheel zoom.
    MouseArea {
        id: canvasMouse
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        hoverEnabled: true
        property int gesture: 0       // 1 pan, 2 marquee, 3 knife, 4 menu, 5 zoom drag, 6 lazy connect
        property real z0: 1
        property real sx: 0
        property real sy: 0
        property real px: 0
        property real py: 0
        property bool moved: false
        onPressed: function(mouse) {
            board.forceActiveFocus()
            board.tipStop()
            sx = mouse.x; sy = mouse.y; px = mouse.x; py = mouse.y; moved = false
            var w = board.toWorld(mouse.x, mouse.y)
            board.mouseWorld = w
            bridge.setCursor(w.x, w.y)
            if (mouse.button === Qt.MiddleButton || (mouse.button === Qt.LeftButton && (mouse.modifiers & Qt.AltModifier)))
                gesture = 1
            else if (mouse.button === Qt.RightButton && (mouse.modifiers & Qt.AltModifier) &&
                     board.nodeAtScreen(mouse.x, mouse.y)) {
                gesture = 6
                board.lazy = {src: board.nodeAtScreen(mouse.x, mouse.y),
                              choose: (mouse.modifiers & Qt.ShiftModifier) !== 0,
                              x0: mouse.x, y0: mouse.y, x1: mouse.x, y1: mouse.y}
                fx.requestPaint()
            } else if (mouse.button === Qt.RightButton &&
                       (mouse.modifiers & (Qt.ControlModifier | Qt.ShiftModifier))) {
                gesture = 3
                board.knife = {x0: mouse.x, y0: mouse.y, x1: mouse.x, y1: mouse.y}
                fx.requestPaint()
            } else if (mouse.button === Qt.RightButton && (mouse.modifiers & Qt.AltModifier)) {
                gesture = 5
                z0 = zoomTick.running ? board.zoomGoal : board.zoom
            } else if (mouse.button === Qt.RightButton) gesture = 4
            else {
                var hw = board.hitWire(mouse.x, mouse.y)
                if (hw) { board.selWire = hw; gesture = 0; board.repaintWires() }
                else gesture = 2
            }
        }
        onPositionChanged: function(mouse) {
            board.mouseWorld = board.toWorld(mouse.x, mouse.y)
            if (!pressed) {
                var hw = board.hitWire(mouse.x, mouse.y)
                if (hw !== board.hoverWire) {
                    board.hoverWire = hw
                    if (board.isGroup(hw)) board.tipBundle(hw, mouse.x, mouse.y)
                    else board.tipStop()
                    board.repaintWires()
                }
                return
            }
            if (Math.abs(mouse.x - sx) + Math.abs(mouse.y - sy) > 3) moved = true
            // Pan by the step since the last move, not from the press: the smooth zoom may still
            // be easing the view, and an absolute pan threw it back (the "teleport").
            if (gesture === 1) { board.panX += mouse.x - px; board.panY += mouse.y - py; px = mouse.x; py = mouse.y }
            else if (gesture === 5)   // drag right / up zooms in, around the press point
                board.zoomSmooth(z0 * Math.exp(((mouse.x - sx) - (mouse.y - sy)) * 0.006), sx, sy)
            else if (gesture === 2 && moved)
                board.marquee = {x: Math.min(sx, mouse.x), y: Math.min(sy, mouse.y),
                                 w: Math.abs(mouse.x - sx), h: Math.abs(mouse.y - sy)}
            else if (gesture === 3) {
                var k = board.knife; k.x1 = mouse.x; k.y1 = mouse.y; board.knife = k; fx.requestPaint()
            } else if (gesture === 6 && board.lazy) {
                var line = board.lazy; line.x1 = mouse.x; line.y1 = mouse.y
                board.lazy = line; fx.requestPaint()
            }
        }
        onReleased: function(mouse) {
            if (gesture === 2) {
                if (moved && board.marquee) {
                    var m = board.marquee, a = board.toWorld(m.x, m.y), b = board.toWorld(m.x + m.w, m.y + m.h)
                    var ids = []
                    for (var id in board.nodeItems) {
                        var it = board.nodeItems[id]
                        if (it.x < b.x && it.x + it.width > a.x && it.y < b.y && it.y + it.height > a.y) ids.push(id)
                    }
                    bridge.selectNodes(ids, (mouse.modifiers & Qt.ShiftModifier) !== 0)
                } else {
                    board.isolate = null; board.connectionFocus = null; board.selWire = ""
                    bridge.clearSelection()
                }
                board.marquee = null
            } else if (gesture === 3) {
                var cut = board.knifeHits()
                board.knife = null
                fx.requestPaint()
                if (cut.length) bridge.disconnectWires(cut)
            } else if (gesture === 6 && board.lazy) {
                var line = board.lazy, target = board.nodeAtScreen(mouse.x, mouse.y)
                board.lazy = null; fx.requestPaint()
                if (target && target !== line.src) bridge.lazyConnect(line.src, target, line.choose)
            } else if (gesture === 4 && !moved) {
                var rw = board.hitWire(mouse.x, mouse.y)
                if (rw) {
                    board.selWire = rw
                    board.tipStop()
                    if (board.isGroup(rw)) bridge.bundleMenu(board.idsOf(rw))
                    else bridge.wireMenu(rw)
                } else {
                    var w = board.toWorld(mouse.x, mouse.y), fm = board.frameAtScreen(mouse.x, mouse.y)
                    bridge.setCursor(w.x, w.y)
                    if (fm) bridge.frameMenu(fm.id, board.frameMembers(fm))
                    else bridge.canvasMenu(w.x, w.y)
                }
            }
            gesture = 0
            board.repaintWires()
        }
        onCanceled: {
            gesture = 0; board.lazy = null; board.knife = null; board.marquee = null
            fx.requestPaint()
        }
        // Leaving the canvas (onto a node, or out of the panel) must drop the hovered wire,
        // or it stays drawn hot until the pointer comes back.
        onExited: if (board.hoverWire !== "") { board.hoverWire = ""; board.tipStop(); board.repaintWires() }
        onDoubleClicked: function(mouse) {
            if (mouse.button !== Qt.LeftButton) return
            var hw = board.hitWire(mouse.x, mouse.y)
            if (!hw) {
                var fm = board.frameAtScreen(mouse.x, mouse.y)
                if (fm) board.frameEdit = {id: fm.id, field: "text"}
                return
            }
            var w = board.findItem(hw)
            if (!w) return
            if (hw.indexOf("b:") === 0) {   // a node link: isolate the pair with its detail
                board.isolate = {a: w.src, b: w.dst, wire: ""}
                board.selWire = ""
                return
            }
            if (w.conv) {   // on the double chevron: show the hidden unitConversion node
                var e = board.wireEnds(w), mid = e ? board.bezPts(e[0], e[1], 2)[1] : null
                if (mid && Math.abs(mid.x - mouse.x) + Math.abs(mid.y - mouse.y) < 16 * Math.max(1, board.zoom)) {
                    bridge.expandConversion(w.id)
                    return
                }
            }
            board.isolate = {a: w.src, b: w.dst, wire: w.id}
            board.selWire = ""
        }
        onWheel: function(wheel) {
            board.zoomSmooth((zoomTick.running ? board.zoomGoal : board.zoom) * Math.exp(wheel.angleDelta.y * 0.0015),
                             wheel.x, wheel.y)
        }
    }

    Item {
        id: world
        x: board.panX
        y: board.panY
        scale: board.zoom
        transformOrigin: Item.TopLeft
        // Frames (Blender): coloured boxes under the nodes. A node belongs to a frame while its
        // centre lies inside it, so dropping a node in puts it in and dragging it out takes it
        // out. The title drags the frame with its nodes; the corner resizes; double-click the
        // title to rename, the body to write a comment; RMB for colour, fit, select, delete.
        Repeater {
            model: board.frames
            delegate: Item {
                id: fr
                property var f: modelData
                property real dx: 0
                property real dy: 0
                property real dw: 0
                property real dh: 0
                readonly property bool editLabel: board.frameEdit !== null && board.frameEdit.id === f.id && board.frameEdit.field === "label"
                readonly property bool editText: board.frameEdit !== null && board.frameEdit.id === f.id && board.frameEdit.field === "text"
                x: f.x + dx
                y: f.y + dy
                width: Math.max(140, f.w + dw)
                height: Math.max(90, f.h + dh)
                z: 0
                Rectangle { anchors.fill: parent; radius: 8; color: fr.f.color; opacity: 0.30 }
                Rectangle { width: parent.width; height: 34; radius: 8; color: fr.f.color; opacity: 0.45 }
                Rectangle {
                    anchors.fill: parent; radius: 8; color: "transparent"
                    border.width: 1; border.color: fr.f.color
                }
                Text {
                    visible: !fr.editLabel
                    x: 12; y: 0; height: 34; width: parent.width - 24
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    text: fr.f.label
                    color: board.th.ink
                    font.pixelSize: 15; font.weight: Font.DemiBold
                }
                Text {
                    visible: !fr.editText && fr.f.text !== ""
                    x: 12; y: 40; width: parent.width - 24; height: parent.height - 48
                    wrapMode: Text.Wrap; elide: Text.ElideRight
                    text: fr.f.text
                    color: board.th.text
                    font.pixelSize: 12
                    lineHeight: 1.15
                }
                Loader {
                    active: fr.editLabel
                    x: 8; y: 5; width: parent.width - 16; height: 24
                    sourceComponent: Component {
                        Rectangle {
                            radius: 3; color: board.th.field; border.width: 1; border.color: board.th.accent
                            TextInput {
                                anchors.fill: parent; anchors.leftMargin: 5; anchors.rightMargin: 5
                                verticalAlignment: TextInput.AlignVCenter
                                color: board.th.ink; font.pixelSize: 14; selectByMouse: true; clip: true
                                property bool cancelled: false
                                text: fr.f.label
                                Component.onCompleted: { forceActiveFocus(); selectAll() }
                                Keys.onEscapePressed: { cancelled = true; board.frameEdit = null; board.forceActiveFocus() }
                                onEditingFinished: {
                                    if (cancelled || !fr.editLabel) return
                                    board.frameEdit = null
                                    if (text !== fr.f.label) bridge.setFrame(fr.f.id, {label: text})
                                    board.forceActiveFocus()
                                }
                            }
                        }
                    }
                }
                Loader {
                    active: fr.editText
                    x: 8; y: 38; width: parent.width - 16; height: parent.height - 46
                    sourceComponent: Component {
                        Rectangle {
                            radius: 3; color: board.th.field; border.width: 1; border.color: board.th.accent
                            TextEdit {
                                id: comment
                                anchors.fill: parent; anchors.margins: 5
                                color: board.th.ink; font.pixelSize: 12; wrapMode: TextEdit.Wrap
                                selectByMouse: true
                                text: fr.f.text
                                property bool done: false
                                function finish(keep) {
                                    if (done) return
                                    done = true
                                    board.frameEdit = null
                                    if (keep && text !== fr.f.text) bridge.setFrame(fr.f.id, {text: text})
                                    board.forceActiveFocus()
                                }
                                Component.onCompleted: { forceActiveFocus(); cursorPosition = text.length }
                                Keys.onEscapePressed: finish(false)
                                Keys.onPressed: function(event) {
                                    if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                                            && (event.modifiers & Qt.ControlModifier)) { finish(true); event.accepted = true }
                                }
                                onActiveFocusChanged: if (!activeFocus) finish(true)
                            }
                        }
                    }
                }
                // title: drag moves the frame with its nodes, RMB menu, double-click renames
                MouseArea {
                    width: parent.width; height: 34
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                    property point start
                    property var starts: null
                    onPressed: function(mouse) {
                        board.forceActiveFocus()
                        board.tipStop()
                        if (mouse.button === Qt.RightButton) { bridge.frameMenu(fr.f.id, board.frameMembers(fr.f)); return }
                        start = mapToItem(board, mouse.x, mouse.y)
                        var s = {}, ids = board.frameMembers(fr.f)
                        for (var i = 0; i < ids.length; i++) { var it = board.nodeItems[ids[i]]; s[ids[i]] = [it.x, it.y] }
                        starts = s
                    }
                    onPositionChanged: function(mouse) {
                        if (!pressed || !starts) return
                        var p = mapToItem(board, mouse.x, mouse.y)
                        fr.dx = (p.x - start.x) / board.zoom; fr.dy = (p.y - start.y) / board.zoom
                        board.dragTo(starts, fr.dx, fr.dy)
                    }
                    onReleased: {
                        if (!starts) return
                        var s = starts
                        starts = null
                        if (fr.dx === 0 && fr.dy === 0) return
                        if (Object.keys(s).length) board.commitDrag(s)
                        var nx = fr.f.x + fr.dx, ny = fr.f.y + fr.dy
                        fr.dx = 0; fr.dy = 0
                        bridge.setFrame(fr.f.id, {x: nx, y: ny})
                    }
                    onDoubleClicked: function(mouse) { if (mouse.button === Qt.LeftButton) board.frameEdit = {id: fr.f.id, field: "label"} }
                }
                // corner: resize
                MouseArea {
                    x: parent.width - 16; y: parent.height - 16; width: 18; height: 18
                    cursorShape: Qt.SizeFDiagCursor
                    property point start
                    onPressed: function(mouse) { { board.forceActiveFocus(); start = mapToItem(board, mouse.x, mouse.y) } }
                    onPositionChanged: function(mouse) {
                        if (!pressed) return
                        var p = mapToItem(board, mouse.x, mouse.y)
                        fr.dw = (p.x - start.x) / board.zoom; fr.dh = (p.y - start.y) / board.zoom
                    }
                    onReleased: {
                        var w = fr.width, h = fr.height
                        fr.dw = 0; fr.dh = 0
                        bridge.setFrame(fr.f.id, {w: w, h: h})
                    }
                    Text { anchors.right: parent.right; anchors.bottom: parent.bottom; anchors.margins: 2; text: "◢"; font.pixelSize: 9; color: board.th.faint }
                }
            }
        }
        Repeater { model: nodeModel; delegate: Node {} }
    }

    // Knife line and marquee, above the nodes.
    Canvas {
        id: fx
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var line = board.lazy || board.knife
            if (!line) return
            ctx.strokeStyle = board.lazy ? board.th.accent : board.th.ink
            ctx.globalAlpha = 0.85; ctx.lineWidth = 1.5
            ctx.beginPath(); ctx.moveTo(line.x0, line.y0); ctx.lineTo(line.x1, line.y1); ctx.stroke()
        }
    }
    Rectangle {
        visible: board.marquee !== null
        x: board.marquee ? board.marquee.x : 0
        y: board.marquee ? board.marquee.y : 0
        width: board.marquee ? board.marquee.w : 0
        height: board.marquee ? board.marquee.h : 0
        color: "transparent"
        border.color: th.accent
        border.width: 1
        Rectangle { anchors.fill: parent; color: th.accent; opacity: 0.12 }
    }

    // Isolation hint
    Rectangle {
        visible: board.isolate !== null || board.connectionFocus !== null
        anchors.horizontalCenter: parent.horizontalCenter
        y: 10
        radius: 4
        color: "#232324"
        width: isoText.implicitWidth + 20
        height: 22
        Text { id: isoText; anchors.centerIn: parent; text: board.connectionFocus ? "Connection chains - click the canvas or Escape to leave" : "Isolated connection - click the canvas to leave"; color: th.muted; font.pixelSize: 11 }
    }

    // ------------------------------------------------------------------ enum list (Blender drop-down)
    // Opens under the field (above it when there is no room), in screen pixels like Blender's
    // menus: hover highlights, click / Enter picks, typing filters, Escape or a click outside closes.
    property var enumPop: null
    property int enumHover: 0
    property string enumFilter: ""
    readonly property var enumShown: {
        if (!enumPop) return []
        var q = enumFilter.toLowerCase(), out = []
        for (var i = 0; i < enumPop.items.length; i++)
            if (!q || enumPop.items[i].name.toLowerCase().indexOf(q) >= 0) out.push(enumPop.items[i])
        return out
    }
    function openEnum(nid, key, item) {
        var o = bridge.enumOptions(nid, key)
        if (!o || !o.items.length) return
        tipStop()
        var longest = 0
        for (var i = 0; i < o.items.length; i++) longest = Math.max(longest, o.items[i].name.length)
        var below = item.mapToItem(board, 0, item.height + 3), above = item.mapToItem(board, 0, -3)
        enumFilter = ""
        enumPop = {nid: nid, key: key, items: o.items, cur: o.cur, label: o.label,
                   x: below.x, below: below.y, above: above.y,
                   w: Math.max(item.width * zoom, 150, longest * 7 + 44)}
        enumHover = 0
        for (var j = 0; j < o.items.length; j++) if (o.items[j].i === o.cur) enumHover = j
        enumBox.forceActiveFocus()
    }
    function closeEnum() { enumPop = null; board.forceActiveFocus() }
    function enumPick(entry) {
        var p = enumPop
        closeEnum()
        if (p && entry && entry.i !== p.cur) bridge.setValue(p.nid, p.key, String(entry.i))
    }
    MouseArea {
        anchors.fill: parent
        visible: board.enumPop !== null
        z: 199
        acceptedButtons: Qt.AllButtons
        onPressed: board.closeEnum()
        onWheel: {}
    }
    Rectangle {
        id: enumBox
        visible: board.enumPop !== null
        z: 200
        readonly property int rowH: 22
        readonly property int listH: Math.min(16, Math.max(1, board.enumShown.length)) * rowH
        width: board.enumPop ? board.enumPop.w : 0
        height: 26 + listH + 6
        x: board.enumPop ? Math.max(4, Math.min(board.enumPop.x, board.width - width - 4)) : 0
        y: !board.enumPop ? 0 : (board.enumPop.below + height <= board.height - 4 ? board.enumPop.below
                                 : Math.max(4, board.enumPop.above - height))
        radius: 5
        color: "#1d1d1e"
        border.width: 1
        border.color: "#000000"
        Rectangle { z: -1; x: 2; y: 4; width: parent.width; height: parent.height; radius: 6; color: "#000000"; opacity: 0.35 }
        Text {
            x: 10; y: 5; height: 16
            width: parent.width - 20
            elide: Text.ElideRight
            text: board.enumFilter ? "⌕ " + board.enumFilter : (board.enumPop ? board.enumPop.label : "")
            color: board.enumFilter ? board.th.ink : board.th.faint
            font.pixelSize: 11
        }
        Rectangle { x: 6; y: 24; width: parent.width - 12; height: 1; color: "#333335" }
        ListView {
            id: enumList
            x: 3; y: 28; width: parent.width - 6; height: enumBox.listH
            clip: true
            model: board.enumShown
            currentIndex: board.enumHover
            boundsBehavior: Flickable.StopAtBounds
            delegate: Rectangle {
                width: enumList.width; height: enumBox.rowH; radius: 3
                readonly property bool cur: board.enumPop !== null && modelData.i === board.enumPop.cur
                color: index === board.enumHover ? board.th.accent : "transparent"
                Text {
                    x: 8; anchors.verticalCenter: parent.verticalCenter
                    text: parent.cur ? "•" : ""
                    color: board.th.ink; font.pixelSize: 12
                }
                Text {
                    x: 22; anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - 30; elide: Text.ElideRight
                    text: modelData.name
                    color: index === board.enumHover || parent.cur ? board.th.ink : board.th.text
                    font.pixelSize: 12
                    font.weight: parent.cur ? Font.DemiBold : Font.Normal
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: board.enumHover = index
                    onClicked: board.enumPick(modelData)
                }
            }
        }
        Keys.onPressed: function(event) {
            var n = board.enumShown.length
            event.accepted = true
            if (event.key === Qt.Key_Escape) board.closeEnum()
            else if (event.key === Qt.Key_Down) board.enumHover = Math.min(n - 1, board.enumHover + 1)
            else if (event.key === Qt.Key_Up) board.enumHover = Math.max(0, board.enumHover - 1)
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                if (n) board.enumPick(board.enumShown[Math.max(0, Math.min(n - 1, board.enumHover))])
            } else if (event.key === Qt.Key_Backspace) {
                board.enumFilter = board.enumFilter.slice(0, -1); board.enumHover = 0
            } else if (event.text && event.text.length === 1 && event.text >= " ") {
                board.enumFilter += event.text; board.enumHover = 0
            } else event.accepted = false
        }
    }

    Rectangle {
        id: tip
        visible: false
        z: 100
        color: "#232324"
        radius: 4
        width: Math.min(360, tipText.implicitWidth) + 18
        height: tipText.implicitHeight + 12
        Text {
            id: tipText
            x: 9; y: 6
            width: Math.min(360, implicitWidth)
            textFormat: Text.RichText
            color: board.th.text
            font.pixelSize: 11
            lineHeight: 1.2
        }
    }
}
