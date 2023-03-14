# import json
import maya.cmds as cmds
from Xlib import display


def mnmConnectArray(modo, tipo):
    array = []
    if modo == 'in':
        if tipo == 'transform':
            array = [
                'atrix', 'translate', 'rotate', 'scale'
            ]
        else:
            array = [
                'input', 'inMesh', 'inGeometry',
                'PP', 'inArray', 'inputGeometry',
                'bind', 'Components'
            ]
    elif modo == 'out':
        if tipo == 'transform':
            array = [
                'atrix', 'world', 'translate', 'rotate', 'scale'
            ]
        else:
            array = [
                'output', 'Mesh', 'Geometry',
                'PP', 'outArray', 'worldMesh',
                'Components'
            ]
    return array


def mnmNodeAttr(modo, plug=None, ui=None):
    plugs, array, cond, current, attr = [], [], (), '', []
    sel = cmds.ls(sl=True)
    if sel:
        if len(sel) == 2:
            current = ''
            if modo == 'out':
                current = sel[0]
            elif modo == 'in':
                current = sel[1]

            # Get the list of attributes
            tipo = cmds.nodeType(current)
            array = mnmConnectArray(modo, tipo)
            # if cmds.nodeType(current) != 'transform':
            #     if modo == 'in':
            #         array = [
            #             'input', 'inMesh', 'inGeometry',
            #             'PP', 'inArray', 'inputGeometry'
            #         ]
            #     elif modo == 'out':
            #         array = [
            #             'output', 'Mesh', 'Geometry',
            #             'PP', 'outArray', 'worldMesh'
            #         ]
            # else:
            #     if modo == 'in':
            #         array = [
            #             'atrix'
            #         ]
            #     elif modo == 'out':
            #         array = [
            #             'atrix', 'world'
            #         ]
            attr = cmds.listAttr(current, c=True)
            # if modo == 'in':
            #     attr = cmds.attributeInfo(current, w=False)
            # elif modo == 'out':
            #     attr = cmds.attributeInfo(current, w=True)
            for at in attr:
                if tipo != 'transform':
                    if modo == 'in':
                        cond = [at.startswith(modo, 0, 2)]
                    elif modo == 'out':
                        cond = [
                            at.startswith(modo, 0, 3),
                            at.startswith('world', 0, 5)
                        ]
                else:
                    cond = [
                        'transflate' in array,
                        'rotate' in array,
                        'scale' in array
                    ]
                if any(cond):
                    for p in array:
                        if p in at:
                            # if len(at.split('.')) == 1:
                            #     plugs.append(at)

                            if len(at.split('.')) == 1:
                                typo = cmds.attributeQuery(
                                    at, n=current, m=True)
                                if typo:
                                    conn = cmds.listConnections(
                                        current + '.' + at)
                                    if conn:
                                        index = 0
                                        if modo == 'in':
                                            index = len(conn) + 1
                                        else:
                                            index = len(conn)
                                        for x in range(0, index):
                                            plugs.append(
                                                at + '[' + str(x) + ']')
                                    else:
                                        plugs.append(at + '[0]')
                                else:
                                    plugs.append(at)
                            else:
                                index = len(cmds.listConnections(
                                    current + '.' + at.split('.')[0])) / 2
                                uno = at.split('.')[0]
                                due = at.split('.')[-1]
                                for x in range(0, index):
                                    plugs.append(
                                        uno + '[' + str(x) + ']' + '.' + due)
            if modo == 'in':
                mnmConnectIn_UI(plug, sorted(list(set(plugs))), ui)
            elif modo == 'out':
                mnmConnectOut_UI(sorted(list(set(plugs))))
        else:
            cmds.confirmDialog(
                t='Fuck a Duck', m='Please select two nodes only'
            )
    else:
        cmds.confirmDialog(t='Fuck a Duck', m='Please select two nodes only')


def mnmConnectOut_UI(plugs):
    win_size = ''
    if cmds.window('connectUI_WIN', q=True, ex=True):
        cmds.deleteUI('connectUI_WIN')
    win = cmds.window('connectUI_WIN', t='  --->>>  ')

    fr = cmds.formLayout(p=win)
    tsl = cmds.textScrollList(ams=False, h=20)
    cmd = 'mnmConnectPopUP.mnmNodeAttr("in", cmds.textScrollList("'
    cmd += tsl + '", q=True, si=True),'
    cmd += '["' + fr + '", "' + tsl + '", "' + win + '"])'
    cmds.formLayout(
        fr,
        e=True,
        af=[
            (tsl, 'top', 0),
            (tsl, 'left', 0),
            (tsl, 'right', 0),
            (tsl, 'bottom', 0)
        ]
    )
    for p in plugs:
        cmds.textScrollList(tsl, e=True, a=p)
    cmds.textScrollList(tsl, e=True, sc=cmd)

    # Open Window
    cmds.showWindow(win)
    if len(plugs) * 20 < 40:
        win_size = 40
    else:
        win_size = len(plugs) * 20

    # Get Mouse Position and open popup
    mo = mnmGetMousePosition()
    cmds.window(
        win,
        e=True,
        wh=(120, win_size),
        tlc=(mo[0] - win_size / 2, mo[1] - 60)
    )


def mnmConnectIn_UI(plug, plugs, ui):
    win_size = ''
    cmds.textScrollList(ui[1], e=True, m=False)
    tsl = cmds.textScrollList(ams=False, h=20)

    cmd = 'mnmConnectPopUP.mnmMakeConnect("'
    cmd += plug[0] + '",cmds.textScrollList("' + tsl + '",q=True, si=True))'
    cmds.formLayout(
        ui[0],
        e=True,
        af=[
            (tsl, 'top', 0),
            (tsl, 'left', 0),
            (tsl, 'right', 0),
            (tsl, 'bottom', 0)
        ]
    )
    for p in plugs:
        cmds.textScrollList(tsl, e=True, a=p)
    cmds.textScrollList(tsl, e=True, sc=cmd)

    # Open Window
    if len(plugs) * 20 < 40:
        win_size = 40
    else:
        win_size = len(plugs) * 20

    # Get Mouse Position and open popup
    mo = mnmGetMousePosition()
    cmds.window(
        ui[2],
        e=True,
        wh=(120, win_size),
        tlc=(mo[0] - win_size / 2, mo[1] - 60)
    )


def mnmMakeConnect(plug1, plug2):
    plug2 = plug2[0]
    sel = cmds.ls(sl=True)

    # if 'worldMesh' not in plug1:
    #     if cmds.attributeQuery(plug1, n=sel[0], m=True):
    #         plug1 = mnmCheckInConn(sel[0] + '.' + plug1)

    # if cmds.attributeQuery(plug2, n=sel[1], m=True):
    #     plug2 = mnmCheckInConn(sel[1] + '.' + plug2)

    try:
        cmds.connectAttr(sel[0] + '.' + plug1, sel[1] + '.' + plug2, f=True)
        cmds.deleteUI('connectUI_WIN')
        print(sel[0] + '.' + plug1 + ' --->>> ' + sel[1] + '.' + plug2)
    except:
        info = 'Cannot connect these two guys:\n'
        info += sel[0] + '.' + plug1 + ' ' + sel[1] + '.' + plug2
        result = cmds.confirmDialog(
            t='Error', m=info, b=['Stop', 'Retry'], db='Retry')
        if result == 'Retry':
            cmds.deleteUI('connectUI_WIN')
            mnmNodeAttr('out')
        else:
            cmds.deleteUI('connectUI_WIN')

    # try:
    #     cmds.connectAttr(sel[0] + '.' + plug1, sel[1] + '.' + plug2, f=True)
    #     cmds.deleteUI('connectUI_WIN')
    #     print sel[0] + '.' + plug1 + ' --->>> ' + sel[1] + '.' + plug2
    # except:
    #     info = 'Cannot connect these two guys:\n'
    #     info += sel[0] + '.' + plug1 + ' ' + sel[1] + '.' + plug2
    #     result = cmds.confirmDialog(
    #         t='Error', m=info, b=['Stop', 'Retry'], db='Retry')
    #     if result == 'Retry':
    #         cmds.deleteUI('connectUI_WIN')
    #         mnmNodeAttr('out')
    #     else:
    #         print 'Not retrying'
    #         cmds.deleteUI('connectUI_WIN')


# def mnmCheckInConn(node):
#     out, index = '', 0
#     # conn = cmds.listAttr(node)
#     conn = cmds.listConnections(node)
#     print node, conn
#     if conn:
#         x = len(conn)
#         index = x
#     else:
#         index = 0
#     out = node.split('.')[-1] + '[' + str(index) + ']'
#     return out


def mnmGetMousePosition():
    mo = display.Display().screen().root.query_pointer()._data
    out = [mo["root_y"], mo["root_x"]]
    return out


# def mnmBuildArray(plugs):
#     out = '['
#     for p in plugs:
#         out += '"' + p + '",'
#     out += ']'
#     return out


'''
def makeNodetDataBase(where):
    din, dot = {}, {}
    version = cmds.about(v=True)
    fi = where + 'nodeIn_' + version + '.json'
    fo = where + 'nodeOut_' + version + '.json'
    allN = cmds.allNodeTypes()
    for a in allN:
        if 'anip' not in a and 'xgm' not in a and 'afc_SOuP' not in a:
            nd = cmds.createNode(a)
            attr = cmds.listAttr(nd, c=True)
            cmds.delete(nd)
            ina, outa = [], []
            inP = ['input', 'Mesh', 'Geometry', 'PP', 'inArray']
            for at in attr:
                if at.startswith('in', 0, 2):
                    for p in inP:
                        if p in at:
                            ina.append(at)
            if ina:
                din[a] = list(set(ina))
            outP = [
                'output', 'Mesh', 'Geometry', 'PP', 'outArray', 'worldMesh'
            ]
            for at in attr:
                if at.startswith('out', 0, 3) or at.startswith('world', 0, 5):
                    for p in outP:
                        if p in at:
                            outa.append(at)
            if outa:
                dot[a] = list(set(outa))
    with open(fi, 'w') as outfile:
        json.dump(
            din, outfile, indent=4, sort_keys=True, separators=(',', ':')
        )
    with open(fo, 'w') as outfile:
        json.dump(
            dot, outfile, indent=4, sort_keys=True, separators=(',', ':')
        )


def readNodeDatabase(modo, plug=None, ui=None):
    data, plugs = '', []
    version = cmds.about(v=True)
    if modo == 'in':
        data = 'nodeIn_' + version + '.json'
    elif modo == 'out':
        data = 'nodeOut_' + version + '.json'
    database = '/nfs/apps/minimo_scripts/pipeline/' + data

    # Start the shit
    sel = cmds.ls(sl=True)
    if sel:
        current = ''
        if modo == 'out':
            current = sel[0]
        elif modo == 'in':
            current = sel[1]

        nType = cmds.nodeType(current)
        with open(database) as data_file:
            data = json.load(data_file)
            for d in sorted(data[nType]):
                plugs.append(d)

    if modo == 'in':
        mnmConnectIn_UI(plug, plugs, ui)
    elif modo == 'out':
        mnmConnectOut_UI(plugs)
'''
