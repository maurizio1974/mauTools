"""The key map shown by Help > Keys, by section. HOTKEYS.md carries the same sections and rows
(tests/test_qml.py checks that every shortcut here appears there)."""

SECTIONS = [
    ("Navigation", [
        ("MMB drag / Alt+LMB drag", "Pan"),
        ("Wheel / Alt+RMB drag on empty canvas", "Zoom"),
        ("F / A", "Frame selected / frame all"),
        ("Toolbar bookmark buttons", "Bookmark the view, previous / next bookmark"),
    ]),
    ("Selection", [
        ("LMB on a node", "Select it; Shift adds or makes it the lead, Ctrl toggles"),
        ("LMB drag on empty canvas", "Marquee select; Shift adds"),
        ("LMB on empty canvas", "Clear selection, isolation and the selected wire"),
        ("Find field + Enter", "Select and frame the nodes matching the text"),
        ("Esc", "Cancel a gesture, else leave isolation, else clear selection"),
    ]),
    ("Wiring", [
        ("Drag port to port", "Connect"),
        ("Drag off a connected input", "Move the wire to another input, or drop it to cut"),
        ("Release a new wire on empty canvas", "Search a node to create and connect"),
        ("Alt+LMB drag from a socket", "Sweep inputs: one source to every input crossed"),
        ("Alt+RMB drag, node to node", "Lazy connect to a compatible free input"),
        ("Alt+Shift+RMB drag, node to node", "Choose output and input sockets"),
        ("Shift+RMB / Ctrl+RMB drag", "Knife: cut every wire crossed"),
        ("Del / Backspace", "Disconnect the selected wire, else delete selected nodes"),
        ("Double-click a wire", "Isolate its two nodes; click the canvas to leave"),
        ("RMB wire > Inbetween", "Insert a utility node into the connection"),
        ("RMB on a port", "Copy attribute name, node.attr or full DAG path"),
        ("W", "Node links: one wire per node pair"),
    ]),
    ("Bulk connect", [
        ("Wire between two selected nodes", "Repeats for every selected pair with similar names"),
        ("Wire into a selected node", "Same input of every selected node of that type"),
        ("K / Shift+K", "Link the lead to the others by attribute name / replace inputs"),
        ("Alt+L / Alt+Shift+L", "Same as K / Shift+K"),
        ("Alt+I / Alt+O / Alt+T", "Transfer inputs / outputs / all connections from the lead"),
        ("Alt+S", "Swap the inputs of two selected nodes"),
    ]),
    ("Values", [
        ("LMB / RMB drag a number field", "Slide; Shift fine, Ctrl snap"),
        ("Click a number field", "Type a value"),
        ("Drag down over number fields, release", "Select them; type a number for all of them"),
        ("Drag down, then sideways", "Slide several fields together"),
        ("Drag over bool fields", "Toggle them all"),
        ("Ctrl+Wheel over a field", "Step a number, next enum item, toggle a bool"),
        ("Esc while sliding", "Restore the values"),
    ]),
    ("Nodes", [
        ("Tab", "Create a node at the cursor"),
        ("F2 / double-click a node name", "Rename"),
        ("Drag a node's right edge", "Width; double-click it for auto width"),
        ("1 / 2 / 3 / 4", "Simple / connected / full / custom display"),
        ("RMB a node > Show all attributes", "Every attribute of that node"),
        ("RMB node > Delete inbetween", "Bypass the node and delete it"),
        ("Double-click a double chevron", "Show the unit conversion node"),
    ]),
    ("Frames", [
        ("Ctrl+J", "Frame the selected nodes; nothing selected: a frame at the cursor"),
        ("Drag a frame's title / corner", "Move it with its nodes / resize"),
        ("Double-click the title / body", "Rename / write a comment"),
        ("RMB on a frame", "Colour, fit to nodes, select nodes, delete"),
    ]),
    ("Clipboard and presets", [
        ("Ctrl+C / Ctrl+V", "Copy / paste nodes with their internal connections"),
        ("Shift+D", "Maya Duplicate with shapes and hierarchy"),
        ("Presets > Save selection as preset", "Store the selection as a reusable fragment"),
        ("Tab > Presets", "Insert a saved preset"),
    ]),
    ("Arrange and display", [
        ("Toolbar Rearrange arrow / Graph > Arrange", "Layered, flow, straighten, grid, row, column"),
        ("Display buttons", "All shapes / except shading networks / no shapes"),
        ("Two selected nodes > RMB > Find connections between", "Highlight every chain joining them"),
    ]),
]


def html(theme):
    """Help window content: one two-column table per section."""
    c = theme
    out = ['<div style="color:%s">' % c["text"],
           '<p style="color:%s">The lead is the last selected node (green). '
           'Text fields keep their normal editing keys.</p>' % c["muted"]]
    for title, rows in SECTIONS:
        out.append('<h3 style="color:%s; margin-top:12px; margin-bottom:4px">%s</h3>'
                   % (c["accent"], title))
        out.append('<table cellspacing="0" cellpadding="3" width="100%">')
        for keys, action in rows:
            out.append('<tr><td width="42%%" style="color:%s"><b>%s</b></td><td>%s</td></tr>'
                       % (c["ink"], _esc(keys), _esc(action)))
        out.append('</table>')
    out.append('</div>')
    return "".join(out)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
