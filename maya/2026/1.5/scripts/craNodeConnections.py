"""
'Node Connections' script - Python port for Maya 2026.

Original MEL script:
    Author: Carlos Rico Adega - carlos.rico.3d@gmail.com
    First Release Date: November 2, 2014
    Version 1.1.0

Copyright (c) 2014 Carlos Rico Adega

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

DESCRIPTION:
    Lists the selected node's source and destination connections.

LAUNCH SCRIPT:
    import craNodeConnections
    craNodeConnections.craNodeConnections()
"""

from maya import cmds, mel

VERSION = "1.1.0"

WIN = "craNodeConnectionsWin"
ABOUT_WIN = "craNodeConnectionsAboutWin"
OPTION_VAR = "craNodeConnectionsCBStatesOV"
DEFAULT_CB_STATES = [0, 1, 0, 0, 1, 0]

NAME_TF = "craNodeConnectionsNodeNameTF"
TYPE_TF = "craNodeConnectionsNodeTypeTF"
TYPE_ICON = "craNodeConnectionsNodeTypeITB"
PANE = "craNodeConnectionsPaneLayout"
LAYOUT_BTN = "craNodeConnectionsChangeLayoutITBTN"

# Per side ("Out" / "In") UI names
LABEL_TXT = {"Out": "craOutConnectionsTXT", "In": "craInConnectionsTXT"}
FILTER_OM = {"Out": "craNodeConnectionsFilterOutOM", "In": "craNodeConnectionsFilterInOM"}
ALL_ITEM = {"Out": "all output attributes", "In": "all input attributes"}
TYPES_CB = {"Out": "craOutConnectionsAttrTypesCB", "In": "craInConnectionsAttrTypesCB"}
SCN_CB = {"Out": "craOutConnectionsSCNCB", "In": "craInConnectionsSCNCB"}
SWAP_CB = {"Out": "craSwapOutConnectionsCB", "In": "craSwapInConnectionsCB"}
FIELD_SF = {"Out": "craOutConnectionsSF", "In": "craInConnectionsSF"}

_SINGLE = "#057cf3"
_TYPE_COLORS = {}
for _t in ("message",):
    _TYPE_COLORS[_t] = "white"
for _t in ("bool", "doubleLinear", "double", "matrix", "float", "enum", "long",
           "byte", "short", "doubleAngle", "time"):
    _TYPE_COLORS[_t] = _SINGLE
for _t in ("double2", "float2", "long2"):
    _TYPE_COLORS[_t] = "cyan"
for _t in ("double3", "float3", "long3", "short2"):
    _TYPE_COLORS[_t] = "LimeGreen"
for _t in ("newParticles", "Nobject", "Nid", "doubleArray", "nurbsSurface", "nurbsTrimface",
           "nurbsCurve", "mesh", "pointArray", "Int32Array", "vectorArray", "TdataCompound",
           "componentList", "string", "stringArray", "floatArray", "lattice"):
    _TYPE_COLORS[_t] = "Fuchsia"
_DEFAULT_COLOR = "Gold"

# Name of the node currently loaded in the tool (stays loaded when selection is cleared).
_loaded_node = ""


# --------------------------------------------------------------------------- helpers

def _cb_states():
    states = cmds.optionVar(q=OPTION_VAR) if cmds.optionVar(exists=OPTION_VAR) else None
    if not isinstance(states, (list, tuple)) or len(states) != len(DEFAULT_CB_STATES):
        states = list(DEFAULT_CB_STATES)
        _store_cb_states(states)
    return [bool(s) for s in states]


def _store_cb_states(states):
    cmds.optionVar(remove=OPTION_VAR)
    for state in states:
        cmds.optionVar(intValueAppend=(OPTION_VAR, int(state)))


def _update_cb_states(*_):
    _store_cb_states([
        cmds.checkBox(cb, q=True, v=True)
        for cb in (TYPES_CB["Out"], SCN_CB["Out"], SWAP_CB["Out"],
                   TYPES_CB["In"], SCN_CB["In"], SWAP_CB["In"])
    ])


def _select_loaded(*_):
    if _loaded_node and cmds.objExists(_loaded_node):
        cmds.select(_loaded_node, r=True, noExpand=True)


def _select_shape(*_):
    if _loaded_node and cmds.objExists(_loaded_node):
        shapes = cmds.listRelatives(_loaded_node, f=True, s=True, ni=True)
        if shapes:
            cmds.select(shapes, r=True)


def _select_from_field(field):
    text = (cmds.scrollField(field, q=True, selection=True) or "").strip()
    if text and cmds.objExists(text):
        cmds.select(text, r=True, noExpand=True)


def _node_icon(node_type):
    for name in ("out_{}.png".format(node_type), "out_{}.svg".format(node_type)):
        if cmds.resourceManager(nameFilter=name):
            return ":/" + name
    return "out_default.png"


def _split_plug(plug):
    node, _, attr = plug.partition(".")
    return node, attr


# --------------------------------------------------------------------------- update

def craNodeConnectionsInfoSelChange(*_):
    global _loaded_node
    if not cmds.window(WIN, exists=True):
        return

    sel = cmds.ls(sl=True)
    if sel:
        node = sel[0]
        node_type = cmds.nodeType(node)
        _loaded_node = node

        cmds.text(NAME_TF, e=True, ann=node,
                  l="<b><font size=4 color=indianred>&nbsp;{}&nbsp;&nbsp;</font></b>".format(node))
        cmds.text(TYPE_TF, e=True, ann=node_type,
                  l="<b><font size=4 color=chocolate>&nbsp;{}</font></b>".format(node_type))
        cmds.nodeIconButton(
            TYPE_ICON, e=True,
            image=_node_icon(node_type),
            ann='Click for help on "{}" node'.format(node_type),
            c=lambda *_, t=node_type: cmds.showHelp("Nodes/{}.html".format(t), docs=True))
        cmds.window(WIN, e=True, title="Node Connections - " + node)

    craFillNodeConnections("Out", False, True, cmds.checkBox(SWAP_CB["Out"], q=True, v=True))
    craFillNodeConnections("In", True, False, cmds.checkBox(SWAP_CB["In"], q=True, v=True))


def _clear_loaded():
    global _loaded_node
    _loaded_node = ""
    for side in ("Out", "In"):
        cmds.scrollField(FIELD_SF[side], e=True, clear=True)
    cmds.text(NAME_TF, e=True, l="")
    cmds.text(TYPE_TF, e=True, l="")
    cmds.nodeIconButton(TYPE_ICON, e=True, image="invisibleCursor.png")


def craFillNodeConnections(plugs, source, destination, swap):
    """plugs is 'Out' or 'In'."""
    sel = cmds.ls(sl=True)
    node = sel[0] if sel else _loaded_node

    current_attr = cmds.optionMenu(FILTER_OM[plugs], q=True, v=True)

    # Header arrow
    if plugs == "Out":
        label = ("<font color=darkseagreen>&#x25C4;OUTPUTS</font>" if swap
                 else "<font color=darkseagreen>OUTPUTS&#x25BA;</font>")
    else:
        label = ("<font color=Khaki>&#x25BA;INPUTS</font>" if swap
                 else "<font color=Khaki>INPUTS&#x25C4;</font>")
    cmds.text(LABEL_TXT[plugs], e=True, l=label)

    # Reset the attribute filter menu
    for item in cmds.optionMenu(FILTER_OM[plugs], q=True, itemListLong=True) or []:
        cmds.deleteUI(item)
    cmds.menuItem(l=ALL_ITEM[plugs], p=FILTER_OM[plugs])

    if not node or not cmds.objExists(node):
        _clear_loaded()
        return

    skip_conversion = cmds.checkBox(SCN_CB[plugs], q=True, v=True)
    show_types = cmds.checkBox(TYPES_CB[plugs], q=True, v=True)

    target = node
    if current_attr != ALL_ITEM[plugs]:
        try:
            cmds.listAttr("{}.{}".format(node, current_attr))
            target = "{}.{}".format(node, current_attr)
        except (RuntimeError, ValueError):
            pass

    connections = cmds.listConnections(target, p=True, s=source, d=destination,
                                       c=True, scn=skip_conversion) or []
    if not connections:
        cmds.scrollField(FIELD_SF[plugs], e=True, clear=True)
        return

    lines, menu_items = [], set()
    for left, right in zip(connections[0::2], connections[1::2]):
        try:
            attr_type = cmds.getAttr(left, type=True) or ""
        except (RuntimeError, ValueError):
            attr_type = ""
        color = _TYPE_COLORS.get(attr_type, _DEFAULT_COLOR)
        type_txt = " {} ".format(attr_type) if show_types else ""

        left_node, left_attr = _split_plug(left)
        right_node, right_attr = _split_plug(right)
        menu_items.add(left_attr)

        to_right = "&nbsp;&#x25CF;&mdash;&mdash;{}&#x25BA;&mdash;&mdash;&#x25CF;&nbsp;".format(type_txt)
        to_left = "&nbsp;&#x25CF;&mdash;&mdash;&#x25C4;{}&mdash;&mdash;&#x25CF;&nbsp;".format(type_txt)

        if swap:
            first_node, first_attr = right_node, right_attr
            second_node, second_attr = left_node, left_attr
            first_node_color, second_node_color = "MediumPurple", "indianred"
            if plugs == "Out":
                first_attr_color, second_attr_color, arrow = "Khaki", "darkseagreen", to_left
            else:
                first_attr_color, second_attr_color, arrow = "darkseagreen", "Khaki", to_right
        else:
            first_node, first_attr = left_node, left_attr
            second_node, second_attr = right_node, right_attr
            first_node_color, second_node_color = "indianred", "MediumPurple"
            if plugs == "Out":
                first_attr_color, second_attr_color, arrow = "darkseagreen", "Khaki", to_right
            else:
                first_attr_color, second_attr_color, arrow = "Khaki", "darkseagreen", to_left

        lines.append(
            "<font color={fnc}>{fn}</font>.<i><font color={fac}>{fa}</font></i>"
            "<font color={col}>{arrow}</font>"
            "<font color={snc}>{sn}</font>.<i><font color={sac}>{sa}</font></i>".format(
                fnc=first_node_color, fn=first_node, fac=first_attr_color, fa=first_attr,
                col=color, arrow=arrow,
                snc=second_node_color, sn=second_node, sac=second_attr_color, sa=second_attr))

    lines.sort()
    cmds.scrollField(FIELD_SF[plugs], e=True, ip=1, text="<br>\n".join(lines))

    for attr in sorted(menu_items):
        cmds.menuItem(p=FILTER_OM[plugs], l=attr)
    try:
        cmds.optionMenu(FILTER_OM[plugs], e=True, v=current_attr)
    except RuntimeError:
        pass


def _clear_filter(plugs):
    cmds.optionMenu(FILTER_OM[plugs], e=True, v=ALL_ITEM[plugs])
    craNodeConnectionsInfoSelChange()


def _swap_changed(plugs, value):
    if plugs == "Out":
        craFillNodeConnections("Out", False, True, value)
    else:
        craFillNodeConnections("In", True, False, value)
    _update_cb_states()


def _option_changed(*_):
    craNodeConnectionsInfoSelChange()
    _update_cb_states()


# --------------------------------------------------------------------------- layout

def craNodeConnectionsLayout(*_):
    if cmds.paneLayout(PANE, q=True, cn=True) == "horizontal2":
        cmds.paneLayout(PANE, e=True, cn="vertical2")
        cmds.nodeIconButton(LAYOUT_BTN, e=True, image="defaultTwoStackedLayout.png",
                            ann="Change UI Layout to Stacked")
    else:
        cmds.paneLayout(PANE, e=True, cn="horizontal2")
        cmds.nodeIconButton(LAYOUT_BTN, e=True, image="defaultTwoSideBySideLayout.png",
                            ann="Change UI Layout to Side by Side")
        cmds.window(WIN, e=True, w=600)


def craNodeConnectionsPanelSize(panel):
    cmds.paneLayout(PANE, e=True, ps=(panel, 100, 100))


def _open_hypershade(*_):
    mel.eval("HypershadeWindow")
    cmds.evalDeferred(lambda: mel.eval('hyperShadePanelGraphCommand("hyperShadePanel1", "showUpAndDownstream")'))


def _open_node_editor(*_):
    mel.eval("NodeEditorWindow")
    cmds.evalDeferred(lambda: mel.eval("NodeEditorGraphUpDownstream"))


# --------------------------------------------------------------------------- build

def _connections_section(plugs, states, icon, arrow_icon, panel_index):
    types_state, scn_state, swap_state = states
    cmds.frameLayout(bv=False, lv=False, mw=3, mh=2, bs="in")
    cmds.rowLayout(nc=9, adj=5)
    cmds.image(w=20, h=20, image=icon)
    cmds.text(LABEL_TXT[plugs], w=65, l="")
    cmds.optionMenu(FILTER_OM[plugs], w=157, cc=lambda *_: craNodeConnectionsInfoSelChange())
    cmds.menuItem(l=ALL_ITEM[plugs], p=FILTER_OM[plugs])
    cmds.nodeIconButton(w=20, h=20, image="muted.png",
                        ann="clear {} filter".format("output" if plugs == "Out" else "input"),
                        c=lambda *_: _clear_filter(plugs))
    cmds.text(l="")
    cmds.checkBox(TYPES_CB[plugs], v=types_state, l="attribute types",
                  ann="show attribute types", cc=_option_changed)
    cmds.checkBox(SCN_CB[plugs], v=scn_state, l="no conversions",
                  ann="skip unit conversion nodes", cc=_option_changed)
    cmds.checkBox(SWAP_CB[plugs], v=swap_state, l="swap sides",
                  cc=lambda v: _swap_changed(plugs, v))
    cmds.nodeIconButton(w=16, h=20, image=arrow_icon,
                        ann="maximize {} connections".format("output" if plugs == "Out" else "input"),
                        c=lambda *_: craNodeConnectionsPanelSize(panel_index))
    cmds.setParent("..")

    cmds.scrollField(FIELD_SF[plugs], ed=False, ww=False,
                     ann="Right-Click to load node from selected text")
    cmds.popupMenu(pmc=lambda *_: _select_from_field(FIELD_SF[plugs]))
    cmds.setParent("..", menu=True)
    cmds.setParent("..")


def craNodeConnections():
    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN)

    states = _cb_states()

    cmds.window(WIN, t=" Node Connections", tlb=False, s=True)
    cmds.frameLayout(lv=False, mw=2, mh=2, bs="in")
    cmds.frameLayout("craNodeConnectionsMainFL", lv=False, mw=5, mh=5, bs="in")

    # ---- node name / type header
    cmds.columnLayout(adj=True)
    cmds.frameLayout(lv=False, mw=2, mh=2, bs="out")
    cmds.rowLayout(nc=3, adj=1)

    cmds.frameLayout(lv=False, mw=2, mh=2, bs="in")
    cmds.rowLayout(nc=5, adj=2)
    cmds.text(l="<font color=grey>&nbsp;Name</font>")
    cmds.text(NAME_TF, w=150, al="left", l="")
    cmds.text(w=1, l=" ")
    cmds.nodeIconButton("craSelectNodeINB", h=20, style="iconOnly", image="redSelect.png",
                        l="node", ann="select node", c=_select_loaded)
    cmds.button(h=20, l="shape", ann="select shape node", c=_select_shape)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.text(w=1, l="")

    cmds.frameLayout(lv=False, mw=2, mh=2, bs="in")
    cmds.rowLayout(nc=4, adj=3)
    cmds.text(l="<font color=grey>&nbsp;&nbsp;Type&nbsp;</font>")
    cmds.nodeIconButton(TYPE_ICON, w=24, h=22, image="invisibleCursor.png")
    cmds.text(TYPE_TF, al="left", w=150, l="")
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    # ---- outputs / inputs
    cmds.frameLayout("craNodeConnectionsPaneLayoutFL", lv=False, mw=2, mh=2, bs="out")
    cmds.paneLayout(PANE, cn="horizontal2")
    _connections_section("Out", states[0:3], "hsDownStreamCon.png", "arrowDown.png", 1)
    _connections_section("In", states[3:6], "hsUpStreamCon.png", "arrowUp.png", 2)
    cmds.setParent("..")
    cmds.setParent("..")

    # ---- bottom buttons
    cmds.columnLayout(adj=True)
    cmds.frameLayout(mw=3, mh=3, bs="out", lv=False)
    cmds.frameLayout(mw=3, mh=3, bs="in", lv=False)
    cmds.rowLayout(nc=7, adj=4)
    cmds.button(h=20, w=160, l="Hypergraph", c=lambda *_: mel.eval("HypergraphDGWindow"))
    cmds.button(h=20, w=160, l="Hypershade", c=_open_hypershade)
    cmds.button(h=20, w=160, l="Node Editor", c=_open_node_editor)
    cmds.text(l="")
    cmds.nodeIconButton(LAYOUT_BTN, h=20, w=40, image="defaultTwoSideBySideLayout.png",
                        ann="Change UI Layout to Side by Side", c=craNodeConnectionsLayout)
    cmds.text(l="")
    cmds.nodeIconButton("craConnectionsAboutNIB", h=20, w=20, image="pickOtherObj.png",
                        ann="About", c=lambda *_: craNodeConnectionsAboutScript())
    cmds.setParent("..")
    cmds.setParent("..")

    craNodeConnectionsInfoSelChange()

    cmds.showWindow(WIN)
    cmds.scriptJob(e=("SelectionChanged", craNodeConnectionsInfoSelChange), p=WIN)


def craNodeConnectionsAboutScript():
    if cmds.window(ABOUT_WIN, exists=True):
        cmds.deleteUI(ABOUT_WIN)

    def swatch(color, label):
        cmds.text(al="left", l="<font color={}>&nbsp;&nbsp;&nbsp;&nbsp;&#x25CF;&ndash;&ndash;"
                               "&#x25BA;&ndash;&ndash;&#x25CF;&nbsp;</font> {}".format(color, label))

    cmds.window(ABOUT_WIN, t=" About/Help", s=True, tlb=True)
    cmds.frameLayout(mw=5, mh=5, lv=False)
    cmds.frameLayout(mw=5, mh=5, lv=False)
    cmds.columnLayout(adj=True)
    cmds.text(l="Node Connections " + VERSION)
    cmds.text(l="")
    cmds.frameLayout(mw=5, mh=5, lv=False, bs="in")
    cmds.columnLayout(adj=True)
    cmds.text(l="COLOR CODES")
    cmds.text(h=16, bgc=(.17, .17, .17), l="Nodes")
    cmds.text(l="<font color=IndianRed>Loaded node</font>")
    cmds.text(l="<font color=MediumPurple>Other nodes</font>")
    cmds.text(h=16, bgc=(.17, .17, .17), l="Attributes")
    cmds.text(l="<i><font color=darkseagreen>Output attributes</font></i>")
    cmds.text(l="<i><font color=Khaki>Input attributes</font></i>")
    cmds.text(h=16, bgc=(.17, .17, .17), l="Connections")
    swatch("Fuchsia", "Data Attributes")
    swatch("cyan", "Double Attributes")
    swatch("white", "Message Attributes")
    swatch("gold", "Other Attributes")
    swatch(_SINGLE, "Single Attributes")
    swatch("LimeGreen", "Triple Attributes")
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.text(l="")
    cmds.text(h=20, bgc=(.17, .17, .17), l="Carlos Rico Adega 2014")
    cmds.textField(bgc=(.17, .17, .17), ed=False, text="        carlos.rico.3d@gmail.com")
    cmds.text(l="")
    cmds.button(w=150, l="Linked[In] Profile",
                c=lambda *_: cmds.showHelp("http://www.linkedin.com/pub/carlos-rico/6/58/325", absolute=True))
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.window(ABOUT_WIN, e=True, s=False, wh=(205, 420))
    cmds.showWindow(ABOUT_WIN)


if __name__ == "__main__":
    craNodeConnections()