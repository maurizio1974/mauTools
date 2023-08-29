''' -----------------------------------------------------------------------

                        NODE EDITOR PLUS TOOLS

-------------------------------------------------------------------------'''

import maya.cmds as cmds
import maya.mel as mel
import mnmConnectPopUP
reload(mnmConnectPopUP)


# GET UNIQUE NAME
def mauGetName(node):
    all = cmds.ls(node + '*')
    return len(all)


# TURN THE SELECTED NODES STATE ON OR OFF
def mauState(dir, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        cmds.setAttr(s + '.nodeState', dir)
    mauStateCheckUI(ui)


# TURN THE SELECTED NODES INTERMEDIATE
def mauInter(dir, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        if cmds.attributeQuery('intermediateObject', n=s, ex=True):
            cmds.setAttr(s + '.intermediateObject', dir)
    mauInterCheckUI(ui)


# TOGGLE AN ATTRIBUTE ON OR OFF OF THE SELCTED NODES
def mauTattr(attr, ui):
    sel = cmds.ls(sl=True)
    for s in sel:
        if cmds.attributeQuery(attr, n=s, ex=True):
            if cmds.getAttr(s + '.' + attr) == 1:
                cmds.setAttr(s + '.' + attr, 0)
            else:
                cmds.setAttr(s + '.' + attr, 1)
    if attr == 'intermediateObject':
        mauInterCheckUI(ui)
    elif attr == 'nodeState':
        mauStateCheckUI(ui)


# CONNECT THE KEYABLE ATTRIBUTE OF TWO NODES
def mauAttrConnector(node1=None, node2=None):

    mayaCB = mel.eval(
        'global string $gChannelBoxName; $temp=$gChannelBoxName;'
    )
    attrs = cmds.channelBox(mayaCB, q=True, sma=True)

    if not node1 and not node2:
        sel = cmds.ls(sl=True)
        if sel:
            node1 = sel[0]
            node1 = sel[1]
        else:
            cmds.warning('Please select two equal nodes')

    nType1 = cmds.nodeType(node1)
    nType2 = cmds.nodeType(node2)

    if nType1 == nType2:
        if not attrs:
            attrs1 = cmds.listAttr(node1, k=True)
        else:
            attrs1 = attrs

        for a in attrs1:
            print 'Connected ' + node1 + '.' + a + '  --->  ' + node2 + '.' + a
            try:
                cmds.connectAttr(node1 + '.' + a, node2 + '.' + a, f=True)
            except:
                print 'Skipping ' + a
    else:
        cmds.warning('The selected nodes are not the same')


# CONNECT THE SHAPES ATTRIBUTE OF TWO NODES
def mauMeshConnector(node1=None, node2=None, dir=0):
    index, connected = 0, 0

    if not node1 and not node2:
        sel = cmds.ls(sl=True)
        if sel:
            node1 = sel[0]
            node1 = sel[1]
        else:
            cmds.warning('Please select two equal nodes')

    if dir == 0:
        attrsOut = [
            'worldMesh[0]', 'outMesh', 'outGeometry', 'output',
            'worldSpace[0]', 'outCurve', 'outputCurve', 'outputGeometry'
        ]
        attrsIn = [
            'input', 'inMesh', 'inGeometry', 'inputGeometry', 'inputMesh',
            'inputPolymesh', 'inputPoly', 'create', 'inputCurve'
        ]

        for ao in attrsOut:
            try:
                for ai in attrsIn:
                    try:
                        if ai == 'input':
                            if connected != 0:
                                return
                            conn = cmds.listConnections(
                                node2 + '.input', s=True, d=False
                            )
                            if conn:
                                index = len(conn)
                            cmds.connectAttr(
                                node1 + '.' + ao,
                                node2 + '.' + ai + '[' + str(index) + ']',
                                f=True
                            )
                            conn = cmds.listConnections(
                                node1 + '.' + ao, d=True, s=False
                            )
                            if conn[0] == node2:
                                connected = 1
                        else:
                            if connected != 0:
                                return
                            cmds.connectAttr(
                                node1 + '.' + ao, node2 + '.' + ai, f=True
                            )
                            conn = cmds.listConnections(
                                node1 + '.' + ao, d=True, s=False
                            )
                            if conn[0] == node2:
                                connected = 1
                            message = node1 + '.' + ao
                            message += '  -->  ' + node2 + '.' + ai
                            print message
                    except:
                        message = 'Skipping ' + node1 + '.' + ao
                        message += ' -->  ' + node2 + '.' + ai
                        print message
                        continue
            except:
                print 'Skipping ' + node1 + '.' + ao
    elif dir == 1:
        attrsOut = ['outComponents', 'groupId']
        attrsIn = ['inComponents', 'inputComponents', 'inGroupId']

        for ao in attrsOut:
            try:
                for ai in attrsIn:
                    try:
                        if connected != 0:
                            return
                        cmds.connectAttr(
                            node1 + '.' + ao, node2 + '.' + ai, f=True
                        )
                        conn = cmds.listConnections(
                            node1 + '.' + ao, d=True, s=False
                        )
                        if conn[0] == node2:
                                connected = 1
                    except:
                        continue
            except:
                print 'Skipping ' + node1 + '.' + ao


# SWAP CONNECTED NODES FROM THE FIRST TO THE LAST NODE
def swapConnections(src=None, swap=None, dest=None):
    if not src or not swap or not dest:
        sel = cmds.ls(sl=True)
        if len(sel) >= 3:
            src = sel[0]
            swap = sel
            dest = sel[-1]
        else:
            cmds.warning('Select at least 3 nodes the first and last need to be the same type')
            return
    # REMOVE FIRST AND LAST FROM THE NODE SEELCTION TO RECONNECT
    swap.pop(0)
    swap.pop(-1)
    # CHECK FIRST AND LAST NODE TYPE
    if cmds.nodeType(src) != cmds.nodeType(dest):
        cmds.warning('The first and last selection need to be the same node type')
        return
    for s in swap:
        conn = cmds.listConnections(s, s=True, d=False, p=True, c=True)
        if conn:
            for x in range(0, len(conn), 2):
                if src in conn[x+1]:
                    new = conn[x+1].replace(src, dest)
                    cmds.connectAttr(new, conn[x], f=True)
                    print s, 'remapped:', src, ' --->>> ', dest


# CLEAN THE GRAPH WITH MY PERSONAL SETTINGS
def mauCleanNE():
    list = []
    current = cmds.ls(sl=True)
    cmds.select(cl=True)
    remove = [
        'shadingEngine',
        'objectSet',
        'hyperLayout',
        'hyperView',
        'hyperGraphInfo',
        'renderLayer',
        'renderLayerManager',
        'displayLayer',
        'displayLayerManager',
        'script',
        'nodeGraphEditorInfo'
    ]
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        nodes = cmds.nodeEditor(ned, q=True, gnl=True)
        if nodes:
            for n in nodes:
                for rem in remove:
                    if cmds.nodeType(n) == rem:
                        list.append(n)
            for l in list:
                cmds.nodeEditor(ned, e=True, rem=l)
            cmds.nodeEditor(ned, e=True, fa=True, lay=True)
    cmds.select(cl=True)
    if current:
        cmds.select(current)


# CLEAN ALL THE JOINTS ATTACHED TO A SKINCLUSTER IN THE GRAPH
def mauCleanSkinNE():
    list = []
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        nodes = cmds.nodeEditor(ned, q=True, gnl=True)
        if nodes:
            for n in nodes:
                if cmds.nodeType(n) == 'skinCluster':
                    maj = cmds.listConnections(n + '.matrix')
                    coj = cmds.listConnections(n + '.influenceColor')
                    for m in maj:
                        list.append(m)
                    if coj:
                        for c in coj:
                            list.append(c)
            for l in list:
                cmds.nodeEditor(ned, e=True, rem=l)
            mauCleanNE()


# CLEAN ALL THE JOINTS ATTACHED TO THE SELECTED SKINCLUSTER
def mauSkinClusterClean():
    # Select the skinCluster to that has the vidible joints in the nodeEditor
    list = []
    sel = cmds.ls(sl=True)
    cmds.select(cl=True)
    if not sel:
        cmds.confirmDialog(t='Error', m='Select a skinCluster node')
        return
    for s in sel:
        if cmds.nodeType(s) == 'skinCluster':
            maj = cmds.listConnections(s + '.matrix')
            coj = cmds.listConnections(s + '.influenceColor')
            for m in maj:
                list.append(m)
            for c in coj:
                list.append(c)
        else:
            print 'Skipping {0} because it is not a skinCluster node'.format(s)
    ned = cmds.getPanel(wf=True) + 'NodeEditorEd'
    if ned:
        for l in list:
            cmds.nodeEditor(ned, e=True, rem=l)
        mauCleanNE()


# MAKE A CLEAN SEPARATION OF A MESH
def mauSeaparate(dir):
    sel = cmds.ls(type='mesh', sl=True)
    if not sel:
        cmds.confirmDialog(m='please Select a mesh shape')
        return
    top = cmds.listRelatives(sel[0], p=True)
    sepa = cmds.polySeparate(sel[0])
    if not sepa:
        cmds.confirmDialog(m='This mesh is not separated')
        return
    for s in sepa:
        sh = cmds.listRelatives(s, s=True)
        if sh:
            topN = cmds.listRelatives(sh[0], p=True)
            cmds.setAttr(sh[0] + '.intermediateObject', 0)
            if dir == 1:
                index = cmds.ls(sh[0].replace('Shape', '_NULL') + '*')
                tr = cmds.createNode(
                    'transform',
                    n=sh[0] + '_NULL' + str(len(index))
                )
                top.append(tr)
            cmds.parent(sh[0], top[-1], r=True, s=True)
            cmds.delete(topN)
    cmds.setAttr(sel[0] + '.intermediateObject', 0)

    # CLEAN NEW TRANSFORM FORM THE ORIG MESH
    topN = cmds.listRelatives(sel[0], p=True)
    cmds.parent(sel[0], top[0], r=True, s=True)
    cmds.delete(topN)
    # CLEAN UP
    # conn = cmds.listConnections(sepa[-1] + '.output')
    # if conn:
    #     for c in conn:
    #         if cmds.nodeType(c) == 'groupParts':
    #             cmds.delete(c)
    return sepa


# UNITE ONE OR MORE MESH SHAPE TO A SINGLE ONE WITH THE POLYUNITE NODE
def mauUnite(dir):
    sel = cmds.ls(type='mesh', sl=True)
    if not sel:
        cmds.confirmDialog(m='please Select at least one mesh shape')
        return
    fath = cmds.listRelatives(sel[0], p=True)
    unite = cmds.createNode(
        'polyUnite',
        n=sel[0].replace('Shape' + sel[0][-1], '_UNI')
    )
    i = 0
    for s in sel:
        cmds.connectAttr(
            s + '.worldMatrix[0]', unite + '.inputMat[' + str(i) + ']'
        )
        cmds.connectAttr(
            s + '.worldMesh[0]', unite + '.inputPoly[' + str(i) + ']'
        )
        i = i + 1
    endMesh = cmds.createNode('mesh')
    cmds.connectAttr(unite + '.output', endMesh + '.inMesh')
    if dir == 1:
        fathN = cmds.listRelatives(endMesh, p=True)
        cmds.parent(endMesh, fath[0], r=True, s=True)
        cmds.delete(fathN)
    return unite, endMesh


# BRANCH OFF A NEW SHAPE FROM THE SELECTED NODES
def mauSh(node, kind):
    # Select the node to outPut from
    # and then optionally the transform to parent the shape under
    attr = [
        'outMesh',
        'outGeometry',
        'output',
        'outputGeometry',
        'outputCurve',
        'worldSpace'
    ]
    sel = cmds.ls(sl=True)
    if sel:
        if cmds.nodeType(sel[-1]) != 'transform':
            index = mauGetName(sel[0].replace('Shape', ''))
            tr = cmds.createNode(
                'transform',
                n=sel[0].replace('Shape', '') + str(index) + '_NULL'
            )
            sel.append(tr)
    for n in node:
        for a in attr:
            if cmds.attributeQuery(a, n=n, ex=True):
                index = mauGetName(n)
                shape = cmds.createNode(
                    kind,
                    n=n.replace('Shape', '') + str(index) + 'Shape'
                )
                father = cmds.listRelatives(shape, p=True)
                if a == 'outputGeometry' or a == 'worldSpace':
                    if kind == 'mesh':
                        cmds.connectAttr(
                            n + '.' + a + '[0]', shape + '.inMesh'
                        )
                    elif kind == 'nurbsCurve' or kind == 'nurbsSurface':
                        cmds.connectAttr(
                            n + '.' + a + '[0]', shape + '.create'
                        )
                else:
                    if kind == 'mesh':
                        cmds.connectAttr(n + '.' + a, shape + '.inMesh')
                    elif kind == 'nurbsCurve' or kind == 'nurbsSurface':
                        cmds.connectAttr(n + '.' + a, shape + '.create')
                cmds.parent(shape, sel[-1], r=True, s=True)
                cmds.delete(father[0])


# PARENT TRHE SELECTED SHAPES UPDATE THE LAST SELECTED TRANSFORM
def mParentSh():
    sel = cmds.ls(sl=1)
    if not sel:
        cmds.confirmDialog(
            t='Error',
            m='Please select some shapes and last a transform'
        )
        return
    if cmds.nodeType(sel[-1]) != 'transform':
        cmds.confirmDialog(
            t='Error',
            m='Please select some shapes and last a transform'
        )
        return
    for s in sel:
        if s is not sel[-1]:
            cmds.parent(s, sel[-1], r=True, s=True)
            print '{0} parent to {1}'.format(s, sel[-1])
    cmds.select(cl=True)


# DRIVE ISOLATE VIEWPORT FROM NODE EDITOR
def mauIsolate(dir):
    sel = cmds.ls(sl=True)
    cPanel = cmds.getPanel(vis=True)
    for eP in cPanel:
        # eP = cmds.paneLayout('viewPanes', q=True, pane1=True)
        panelType = cmds.getPanel(to=eP)
        if panelType == 'modelPanel':
            # ISOLATE THE CURRENT SELECTION
            if dir == 0:
                if cmds.isolateSelect(eP, q=True, s=True) == 0:
                    cmds.isolateSelect(eP, s=1)
                    cmds.isolateSelect(eP, addSelected=True)
                else:
                    if len(sel) == 0:
                        cmds.isolateSelect(eP, s=0)
                    else:
                        cmds.isolateSelect(eP, s=1)
                        cmds.isolateSelect(eP, addSelected=True)

            # ADD THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 1:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, addSelected=True)

            # REMOVE THE CURRENT SELECTION TO THE ACTIVE ISOLATION
            if dir == 2:
                if cmds.isolateSelect(eP, q=True, s=True) == 1:
                    cmds.isolateSelect(eP, rs=True)


# ADD SELECTION TO SELECTED GROUP NODE
def mauGroupAddSel():
    out = ''
    sel = cmds.ls(sl=True, fl=True)
    if cmds.nodeType(sel[0]) == 'group':
        for s in sel:
            name = s.split('[')[-1].replace(']', '')
            if s != sel[0]:
                if s != sel[-1]:
                    out += name + ' '
                else:
                    out += name
        print out
        cmds.setAttr(sel[0] + '.pattern', out, type='string')
    else:
        cmds.warning(
            'Make sure to select a group node first, then some components'
        )


# GET SELECTION OF SELECTED GROUP NODE
def mauGetPatterSelection():
    sel = cmds.ls(sl=True, fl=True)
    if cmds.nodeType(sel[0]) == 'group':
        comp, mesh = '', []
        tipo = cmds.getAttr(sel[0] + '.componentType')
        if tipo == 0:
            comp = 'vtx'
        elif tipo == 1:
            comp = 'e'
        try:
            if not sel[1]:
                mesh = cmds.listConnections(sel[0] + '.inGeometry')
            else:
                if cmds.nodeType(sel[1]) == 'mesh':
                    mesh.append(sel[1])
                else:
                    cmds.warning(
                        'Please make sure the secon selecion is a meshShape'
                    )
        except:
            mesh = cmds.listConnections(sel[0] + '.inGeometry')
        components = cmds.getAttr(sel[0] + '.pattern').split(' ')
        cmds.select(sel[0], r=True)
        for c in components:
            cmds.select(mesh[0] + '.' + comp + '[' + str(c) + ']', add=True)
    else:
        cmds.warning('Make sure to select a group node first')


# MAKE A SOUP GROUP TO THE DEFORMER AND CLEAN THE MAYA ONE
def mauGRP():
    # select the orig mesh and then the deformer
    nodes = cmds.ls(sl=True)
    if len(nodes) < 1:
        cmds.confirmDialog(
            m='please Select the orig mesh and the deformer node'
        )
        return
    grp = cmds.createNode('group')
    if cmds.attributeQuery('worldMesh', n=nodes[0], ex=True):
        cmds.connectAttr(
            nodes[0] + '.worldMesh[0]', grp + '.inGeometry', f=True
        )
    elif cmds.attributeQuery('output', n=nodes[0], ex=True):
        cmds.connectAttr(nodes[0] + '.output', grp + '.inGeometry', f=True)
    elif cmds.attributeQuery('outMesh', n=nodes[0], ex=True):
        cmds.connectAttr(
            nodes[0] + '.outMesh[0]', grp + '.inGeometry', f=True
        )
    cmds.refresh()

    cmds.setAttr(grp + '.invert', 1)
    cmds.setAttr(grp + '.outputObjectGroup', 1)
    grpID = cmds.createNode('groupId')
    cmds.connectAttr(grpID + '.groupId', grp + '.groupId', f=True)
    cmds.refresh()
    cmds.select(grpID)
    # CLEAN UP
    headMesh = cmds.listConnections(nodes[1] + '.outputGeometry[0]', p=1)
    cmds.delete(
        cmds.listConnections(headMesh[0].split('.')[0] + '.tweakLocation')
    )
    cmds.delete(
        cmds.listConnections(
            headMesh[0].split('.')[0] + '.instObjGroups[0].objectGroups[0]'
        )
    )
    cmds.refresh()
    cmds.connectAttr(
        grp + '.outGeometry',
        nodes[1] + '.input[0].inputGeometry',
        f=True
    )
    cmds.refresh()
    cmds.connectAttr(
        grpID + '.groupId',
        nodes[1] + '.input[0].groupId',
        f=True
    )


# DUPLICATE THE GRPAH AND SPLIT IT AT THE BEGINNING
def mauDupChain():
    sel = cmds.ls(sl=True)  # Selected shape
    if cmds.nodeType(sel[0]) != 'mesh':
        cmds.warning('Select a mesh shape')
        return
    dup = cmds.duplicate(sel[0], un=True)  # duplicate the structure
    trans = cmds.listRelatives(sel[0], p=True)  # get transform of the shape
    sh = cmds.listRelatives(trans[0], s=True)  # get all the shapes of the node
    # get all the shapes of the duplicate node
    sh2 = cmds.listRelatives(dup[0], s=True)
    # get orig shape of the duplicated node
    conn = cmds.listConnections(sh2[-1], s=False, d=True)
    # connect the orig mesh to the duplicated deformation stack
    cmds.connectAttr(
        sh[-1] + '.worldMesh[0]', conn[0] + '.inputGeometry', f=True
    )
    # parent the duplicated shape to the original transform
    cmds.parent(sh2[0], trans[0], r=True, s=True)
    cmds.delete(dup[0])  # delete the original transform


''' --------------------------------------------------------------------------

                NODE EDITOR PLUS MARKIN MENU ( CTRL + RIGHT CLICK )

----------------------------------------------------------------------------'''


def nodePlusMM(ned):
    nedPP = cmds.popupMenu(p=ned, b=3, ctl=True)
    cmds.menuItem(label='Clean UP', p=nedPP)
    cmds.menuItem(label='CluenUP + Joints', p=nedPP)
    cmds.menuItem(label='------------', p=nedPP)
    cmds.menuItem(label='Connect Attr', p=nedPP)
    cmds.menuItem(label='Connect Shape Attr', p=nedPP)
    cmds.menuItem(label='------------', p=nedPP)
    cmds.menuItem(label='New Shape', p=nedPP)
    cmds.menuItem(label='New Shape + Transform', p=nedPP)
    cmds.menuItem(label='------------', p=nedPP)
    cmds.menuItem(label='Clean Separate', p=nedPP)
    cmds.menuItem(label='Clean Separate + Transform', p=nedPP)
    cmds.menuItem(label='------------', p=nedPP)
    cmds.menuItem(label='Clean Unite', p=nedPP)
    cmds.menuItem(label='Clean Unite + Transform', p=nedPP)
    cmds.menuItem(label='------------', p=nedPP)
    cmds.menuItem(label='Add Current Selection', p=nedPP)


''' --------------------------------------------------------------------------

                        NODE EDITOR PLUS UI CHANGES

----------------------------------------------------------------------------'''


def NODEplus():
    # CREATE A NODE ERITOR WINDOW
    ned = mel.eval('nodeEditorWindow()')
    # print ned
    # GET THE FLOWLAYOUT TOOLBAR
    location = cmds.iconTextButton(ned + 'LCB', q=True, p=True)
    # GET THE FORMLAYOUT
    frame = cmds.flowLayout(location, q=True, p=True)
    # DELETE THE CURRENT FLOWLAYOUT TOLLBAR
    cmds.deleteUI(location)
    # RECREATE THE TOOLBAR FLOWLAYOUT MODIFIED
    job = nodeEdCreateToolbarPy(ned.replace('NodeEditorEd', ''), frame)
    # KILL SCRIPT JOBS TO CHANGE ICONS
    # DEPENDING ON SELECTION WHEN CLOSING THE WINDOW
    cmds.scriptJob(uiDeleted=(
        location.split('|')[0],
        'cmds.scriptJob(kill=' + str(job[0]) + ', f=True)')
    )
    cmds.scriptJob(uiDeleted=(
        location.split('|')[0],
        'cmds.scriptJob(kill=' + str(job[1]) + ', f=True)')
    )
    nodePlusMM(ned)


# REBUILD THE NODEEDITOR TOOLBAR WITH OUR EXTRA BUTTONS
def nodeEdCreateToolbarPy(panelName, fl):
    ned = panelName + 'NodeEditorEd'
    toolBarFrame = fl
    toolBarForm = cmds.flowLayout(visible=True, p=fl)

    # Create quick access buttons which will be hooked up later
    # so they can be in sync with the menu as well as the popupMenu.
    iconsize = 26
    cmds.setParent(toolBarForm)

    # Filter UI
    filterField = mel.eval(
        'filterUICreateField("' + ned + '", "' + toolBarForm + '")'
    )

    # Re-Graph Controls & Sync
    # Create the expand/collapse button separators
    item = ned + 'RegraphCollapse'
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval(
            'uiRes("m_nodeEditorPanel.kShowHideNodeEditorRegraph")'
        ),
        i1='openBar.png',
        c='gp.nodeEditorToggleRegraphIconsPy(1, "' + ned + '")'
    )

    item = ned + 'SNEI'
    cmd = "mel.eval('NodeEditorToggleSyncedSelection')"
    cmds.iconTextButton(
        item,
        i1=mel.eval('nodeEdSyncImage("' + ned + '")'),
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorToggleSyncedSelection")'
        ),
        c=cmd
    )

    item = ned + 'UPSTRM'
    cmd = "mel.eval('NodeEditorGraphUpstream')"
    cmds.iconTextButton(
        item,
        image1="hsUpStreamCon.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorGraphUpstream")'),
        c=cmd
    )

    item = ned + 'UPDNSTRM'
    cmd = "mel.eval('NodeEditorGraphUpDownstream')"
    cmds.iconTextButton(
        item,
        i1="hsUpDownStreamCon.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphUpDownstream")'
        ),
        c=cmd
    )

    item = ned + 'DNSTRM'
    cmd = "mel.eval('NodeEditorGraphDownstream')"
    cmds.iconTextButton(
        item,
        image1="hsDownStreamCon.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphDownstream")'
        ),
        c=cmd
    )

    # check for optionVar
    if cmds.optionVar(exists="nodeEditorShowRegraphIcons"):
        cmds.optionVar(iv=("nodeEditorShowRegraphIcons", 1))
    else:
        mel.eval(
            'nodeEditorToggleRegraphIcons(`optionVar -q "nodeEditorShowRegraphIcons"`,"' + ned + '")'
        )

    # Layout & Clear
    # Create the expand/collapse button separators
    item = ned + 'LayoutCollapse'
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kShowHideNodeEditorLayout")'),
        i1='openBar.png',
        c="gp.nodeEditorToggleLayoutIconsPy(1, '" + ned + "')"
    )

    item = ned + "LCCV"
    cmd = "mel.eval('NodeEditorGraphClearGraph')"
    cmds.iconTextButton(
        item,
        image1="hsClearView.png",
        width=iconsize,
        height=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphClearGraph")'
        ),
        c=cmd
    )

    # TODO: get proper icon from design
    item = ned + "ADDSEL"
    cmd = "mel.eval('NodeEditorGraphAddSelected')"
    cmds.iconTextButton(
        item,
        image1="nodeGrapherAddNodes.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphAddSelected")'
        ),
        c=cmd
    )

    item = ned + "LCDA"
    cmd = "mel.eval('NodeEditorGraphRemoveSelected')"
    cmds.iconTextButton(
        item,
        image1="nodeGrapherRemoveNodes.png",
        width=iconsize,
        height=iconsize,
        ann=('getRunTimeCommandAnnotation("NodeEditorGraphRemoveSelected")'),
        c=cmd
    )

    item = ned + "LCHSR"
    cmd = 'mel.eval("NodeEditorGraphRearrange")'
    cmds.iconTextButton(
        item,
        image1="hsRearrange.png",
        width=iconsize,
        height=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphRearrange")'
        ),
        c=cmd
    )

    # ---------------------My BUTTONS ----------------------------------------

    # Create the expand/collapse button separators
    item = ned + 'MauCollapse'
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann='Collapse Mau Tools',
        i1='openBar.png',
        c="gp.nodeEditorToggleMauIconsPy(1, '" + ned + "')"
    )
    item = ned + "LCCLEAN"
    clHYPG = cmds.iconTextButton(
        item,
        image1='cleanerBrush',
        w=iconsize,
        h=iconsize,
        ann='Clean the curent NodeEditor from extra sets',
        c='gp.mauCleanNE()'
    )
    item = ned + "LCSTATE"
    stateHYPG = cmds.iconTextButton(
        item,
        image1='refresh',
        w=iconsize,
        h=iconsize,
        ann='Turn the selected node state to normal or has No Effect',
        c='gp.mauTattr(\'nodeState\', "' + item + '")',
    )
    # SCRIPT JOB TO CHANGE THE STATE ICON
    jobS = cmds.scriptJob(
        e=("SelectionChanged", 'gp.mauStateCheckUI("' + item + '")'),
        protected=True
    )

    item = ned + "LCINTER"
    interHYPG = cmds.iconTextButton(
        item,
        image1='out_polyPlane',
        w=iconsize,
        h=iconsize,
        ann='Toggle the selected shape to intermediated',
        c='gp.mauTattr(\'intermediateObject\', "' + item + '")'
    )
    # SCRIPT JOB TO CHANGE THE INTERMEDIATE ICON
    jobI = cmds.scriptJob(
        e=("SelectionChanged", 'gp.mauInterCheckUI("' + item + '")'),
        protected=True
    )

    item = ned + "LCPSH"
    isoHYPG = cmds.iconTextButton(
        item,
        image1='mParentSh',
        w=iconsize,
        h=iconsize,
        ann='Select shapes and then a transform to purant them under',
        c='gp.mParentSh()'
    )
    item = ned + "LCISO"
    isoHYPG = cmds.iconTextButton(
        item,
        image1='mISO',
        w=iconsize,
        h=iconsize,
        ann='Isolate',
        c='gp.mauIsolate(0)'
    )
    item = ned + "LCSHAPE"
    shHYPG = cmds.iconTextButton(
        item,
        image1='mauMesh',
        w=iconsize,
        h=iconsize,
        ann='Make an extra shape after the selected node and transform'
    )
    item = ned + "LCCONNECTOR"
    connectorHYPG = cmds.iconTextButton(
        item,
        image1='connectorAttribute',
        w=iconsize,
        h=iconsize,
        ann='Connect the Transform attributes of a node to another',
        c='gp.mauAttrConnector(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1])'
    )
    item = ned+"LCMCONNECTOR"
    connectorMHYPG = cmds.iconTextButton(
        item,
        image1='connectorMesh2',
        w=iconsize,
        h=iconsize,
        ann='Connect the Mesh attributes of a node to another',
        c='mnmConnectPopUP.mnmNodeAttr("out")'
    )
    item = ned + "LCSEPA"
    sapaHYPG = cmds.iconTextButton(
        item,
        image1='polySeparate',
        w=iconsize,
        h=iconsize,
        ann='Clean Separate of a mesh',
        c='gp.mauSeaparate(0)'
    )
    item = ned + "LCUNITE"
    uniteHYPG = cmds.iconTextButton(
        item,
        image1='polyUnite',
        w=iconsize,
        h=iconsize,
        ann='Make a single mesh from multiple meshes',
        c='gp.mauUnite(1)'
    )
    item = ned + "LCSWN"
    swapHYPG = cmds.iconTextButton(
        item,
        image1='mdisplayComp',
        w=iconsize,
        h=iconsize,
        ann='Swap first and last node selected connections',
        c='gp.swapConnections()'
    )
    item = ned + "LCGRP"
    grpHYPG = cmds.iconTextButton(
        item,
        image1='mauGRP',
        w=iconsize,
        h=iconsize,
        ann='Select the orig mesh and the the deformer',
        c='gp.mauGRP()'
    )
    item = ned + "LCDUP"
    dupHYPG = cmds.iconTextButton(
        item,
        image1='mDUP',
        w=iconsize,
        h=iconsize,
        ann='Duplicate the selected mesh hierarchy',
        c='gp.mauDupChain()'
    )
    item = ned + "LCSDC"
    sdcHYPG = cmds.iconTextButton(
        item,
        image1='mdisplayComp',
        w=iconsize,
        h=iconsize,
        ann='SOuP Display Components',
        c='soup().create(\'displayComponents\')'
    )

    # POPUP FOR THE CLEAN BUTTON
    mi0 = cmds.popupMenu(p=clHYPG)
    pmi0 = cmds.menuItem(label='Clean + all Joints', p=mi0)
    cmds.menuItem(pmi0, e=True, c='gp.mauCleanSkinNE()')
    pmi00 = cmds.menuItem(label='Clean Joint from Selected SkinCluster', p=mi0)
    cmds.menuItem(pmi00, e=True, c='gp.mauSkinClusterClean()')
    # POPUP FOR THE STATE BUTTON
    mi1 = cmds.popupMenu(p=stateHYPG)
    pmi1 = cmds.menuItem(label='on', p=mi1)
    cmds.menuItem(pmi1, e=True, c='gp.mauState(0, "' + ned + 'LCSTATE")')
    pmi11 = cmds.menuItem(label='off', p=mi1)
    cmds.menuItem(pmi11, e=True, c='gp.mauState(1, "' + ned + 'LCSTATE")')
    # POPUP FOR THE INTERMEDIATE BUTTON
    mi2 = cmds.popupMenu(p=interHYPG)
    pmi2 = cmds.menuItem(label='Intermediate On ', p=mi2)
    cmds.menuItem(pmi2, e=True, c='gp.mauInter(1, "' + ned + 'LCINTER")')
    pmi22 = cmds.menuItem(label='Intermediate Off', p=mi2)
    cmds.menuItem(pmi22, e=True, c='gp.mauInter(0, "' + ned + 'LCINTER")')
    # POPUP FOR THE SHAPE BUTTON
    mi3 = cmds.popupMenu(p=shHYPG)
    pmi3 = cmds.menuItem(label='Mesh Shape', p=mi3)
    cmds.menuItem(pmi3, e=True, c='gp.mauSh(cmds.ls(sl=True), \'mesh\')')
    pmi33 = cmds.menuItem(label='NurbsCurve Shape', p=mi3)
    cmds.menuItem(
        pmi33,
        e=True,
        c='gp.mauSh(cmds.ls(sl=True), \'nurbsCurve\')'
    )
    pmi333 = cmds.menuItem(label='NurbsSurface Shape', p=mi3)
    cmds.menuItem(
        pmi333,
        e=True,
        c='gp.mauSh(cmds.ls(sl=True), \'nurbsSurface\')'
    )
    # POPUP FOR THE UNITE BUTTON
    mi4 = cmds.popupMenu(p=uniteHYPG)
    pmi4 = cmds.menuItem(label='Unite with new Transform', p=mi4)
    cmds.menuItem(pmi4, e=True, c='gp.mauUnite(0)')
    # POPUP FOR THE SAPARATE BUTTON
    mi5 = cmds.popupMenu(p=sapaHYPG)
    pmi5 = cmds.menuItem(label='Separate with new Transform', p=mi5)
    cmds.menuItem(pmi5, e=True, c='gp.mauSeaparate(1)')
    # POPUP FOR THE ISOLATE BUTTON
    mi6 = cmds.popupMenu(p=isoHYPG)
    pmi6 = cmds.menuItem(label='Add to Isolate', p=mi6)
    cmds.menuItem(pmi6, e=True, c='gp.mauIsolate(1)')
    pmi66 = cmds.menuItem(label='Remove to Isolate', p=mi6)
    cmds.menuItem(pmi66, e=True, c='gp.mauIsolate(2)')
    # POPUP FOR THE CONNECTOR BUTTON
    mi7 = cmds.popupMenu(p=connectorMHYPG)
    cmds.menuItem(
        label='Geo Guess',
        c='gp.mauMeshConnector(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], 0)',
        p=mi7
    )
    cmds.menuItem(
        label='components',
        c='gp.mauMeshConnector(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], 1)',
        p=mi7
    )
    # POPUP FOR THE GROUP BUTTON
    mi8 = cmds.popupMenu(p=grpHYPG)
    pmi8 = cmds.menuItem(label='Add Selection to current group node', p=mi8)
    cmds.menuItem(pmi8, e=True, c='gp.mauGroupAddSel()')
    pmi88 = cmds.menuItem(label='Get Selection to current group node', p=mi8)
    cmds.menuItem(pmi88, e=True, c='gp.mauGetPatterSelection()')

    # -------------------------------------------------------------------------

    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowLayoutIcons"):
        cmds.optionVar(iv=("nodeEditorShowLayoutIcons", 1))
    else:
        mel.eval('nodeEditorToggleLayoutIcons(`optionVar -q "nodeEditorShowLayoutIcons"`, "' + ned + '")')

    # LOD & Pin Controls
    # Create the expand/collapse button separators
    item = ned + "LODPinCollapse"
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kShowHideNodeEditorLodPin")'),
        i1='openBar.png',
        c="gp.nodeEditorToggleLodPinIconsPy(1, '" + ned + "')"
    )

    item = ned + "LODSimpleMode"
    cmd = 'mel.eval("NodeEditorHideAttributes")'
    cmds.iconTextButton(
        item,
        i1='nodeGrapherModeSimpleLarge.png',
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorHideAttributes")'
        ),
        c=cmd
    )

    item = ned + "LODConnectedMode"
    cmd = 'mel.eval("NodeEditorShowConnectedAttrs")'
    cmds.iconTextButton(
        item,
        i1="nodeGrapherModeConnectedLarge.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorShowConnectedAttrs")'
        ),
        c=cmd
    )

    item = ned + "LODShowAll"
    cmd = 'mel.eval("NodeEditorShowAllAttrs")'
    cmds.iconTextButton(
        item,
        i1="nodeGrapherModeAllLarge.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorShowAllAttrs")'),
        c=cmd
    )

    item = ned + "LodPinSeparator"
    cmds.separator(item, h=iconsize, horizontal=False, style='single')

    # Pin Controls
    item = ned + "PinnedOn"
    cmd = 'mel.eval("NodeEditorPinSelected")'
    cmds.iconTextButton(
        item,
        i1="nodeGrapherPinnedLarge.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorPinSelected")'),
        c=cmd
    )

    item = ned + "PinnedOff"
    cmd = 'mel.eval("NodeEditorUnpinSelected")'
    cmds.iconTextButton(
        item,
        i1="nodeGrapherUnpinnedLarge.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorUnpinSelected")'),
        c=cmd
    )

    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowLodPinIcons"):
        cmds.optionVar(iv=("nodeEditorShowLodPinIcons", 1))
    else:
        mel.eval('nodeEditorToggleLodPinIcons(`optionVar -q "nodeEditorShowLodPinIcons"`, "' + ned + '")')

    # Bookmarks
    # Create the expand/collapse button separators
    item = ned + "BookmarkCollapse"
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kShowHideNodeEditorBookmark")'),
        i1='openBar.png',
        c="gp.nodeEditorToggleBookmarkIconsPy(1, '" + ned + "')"
    )

    # Create bookmark items
    mel.eval(
        'callPython("maya.app.general.nodeEditorBookmarks","buildToolbar",{"' + ned + '"})'
    )
    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowBookmarkIcons"):
        cmds.optionVar(iv=("nodeEditorShowBookmarkIcons", 1))
    else:
        mel.eval(
            'nodeEditorToggleBookmarkIcons(`optionVar -q "nodeEditorShowBookmarkIcons"`, "' + ned + '")'
        )

    # Display & Lock
    # Create the expand/collapse button separators
    item = ned + "DisplayCollapse"
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kShowHideNodeEditorDisplays")'),
        i1='openBar.png',
        c="gp.nodeEditorToggleDisplayIconsPy(1, '" + ned + "')"
    )

    cmds.iconTextRadioCollection()

    item = ned + "SSRB"
    cmd = 'mel.eval("NodeEditorGraphAllShapes")'
    cmds.iconTextRadioButton(
        item,
        image1="nodeGrapherDisplayAll.png",
        width=iconsize,
        height=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGraphAllShapes")'
        ),
        onCommand=cmd
    )

    item = ned + "SSGRB"
    cmd = 'mel.eval("NodeEditorGraphAllShapesExceptShading")'
    cmds.iconTextRadioButton(
        item,
        image1="nodeGrapherDisplayAllExcept.png",
        width=iconsize,
        height=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorGraphAllShapesExceptShading")'),
        onCommand=cmd
    )

    item = ned + "NSRB"
    cmd = 'mel.eval("NodeEditorGraphNoShapes")'
    cmds.iconTextRadioButton(
        item,
        image1="nodeGrapherDisplayNone.png",
        width=iconsize,
        height=iconsize,
        ann=mel.eval('getRunTimeCommandAnnotation("NodeEditorGraphNoShapes")'),
        onCommand=cmd
    )

    item = ned + "DisplayLockSeparator"
    cmds.separator(item, h=iconsize, horizontal=False, style='single')

    # Lock Current View
    item = ned + "LCB"
    cmd = 'mel.eval("NodeEditorToggleLockUnlock")'
    cmds.iconTextButton(
        item,
        i1="nodeGrapherUnlocked.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorToggleLockUnlock")'
        ),
        c=cmd
    )

    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowDisplayIcons"):
        cmds.optionVar(iv=("nodeEditorShowDisplayIcons", 1))
    else:
        mel.eval('nodeEditorToggleDisplayIcons (`optionVar -q "nodeEditorShowDisplayIcons"`, "' + ned + '")')

    # Depth Traversal Limit control
    # Create the expand/collapse button separators
    item = ned + "DepthTraversalCollapse"
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval(
            'uiRes("m_nodeEditorPanel.kShowHideNodeEditorDepthTraversal")'
        ),
        i1='openBar.png',
        c="gp.nodeEditorToggleDepthTraversalIconsPy(1, '" + ned + "')"
    )

    tdlcmd = "nodeEdTraversalDepthLimit \"" + ned + "\""

    item = ned + "ZeroDepth"
    cmd = 'mel.eval("NodeEditorSetTraversalDepthZero")'
    cmds.iconTextButton(
        item,
        i1="zeroDepth.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorSetTraversalDepthZero")'
        ),
        c=cmd
    )

    item = ned + "ReduceOne"
    cmd = 'mel.eval("NodeEditorReduceTraversalDepth")'
    cmds.iconTextButton(
        item,
        i1="reduceDepth.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorReduceTraversalDepth")'
        ),
        c=cmd
    )

    item = ned + "DepthTextField"

    cmds.textField(
        item,
        w=28,
        h=28,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kSetTraversalDepthAnnot")'),
        tx='-1',
        cc="nodeEditor -e -rfs 1 -tdl #1 \"" + ned + "\""
    )

    item = ned + "IncreaseDepth"
    cmd = 'mel.eval("NodeEditorIncreaseTraversalDepth")'
    cmds.iconTextButton(
        item,
        i1="increaseDepth.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorIncreaseTraversalDepth")'
        ),
        c=cmd
    )

    item = ned + "UnlimitedDepth"
    cmd = 'mel.eval("NodeEditorSetTraversalDepthUnlim")'
    cmds.iconTextButton(
        item,
        i1="unlimitedDepth.png",
        w=iconsize,
        h=iconsize,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorSetTraversalDepthUnlim")'
        ),
        c=cmd
    )

    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowDepthTraversalIcons"):
        cmds.optionVar(iv=("nodeEditorShowDepthTraversalIcons", 1))
    else:
        mel.eval('nodeEditorToggleDepthTraversalIcons(`optionVar -q "nodeEditorShowDepthTraversalIcons"`, "' + ned + '")')

    # Grid controls
    # Create the expand/collapse button separators
    item = ned + "GridCollapse"
    cmds.iconTextButton(
        item,
        vis=True,
        h=27,
        w=9,
        ann=mel.eval('uiRes("m_nodeEditorPanel.kShowHideNodeEditorGrid")'),
        i1='openBar.png',
        c="gp.nodeEditorToggleGridIconsPy(1, '" + ned + "')"
    )

    item = ned + "GridToggleVisibility"
    cmd = 'mel.eval("NodeEditorGridToggleVisibility")'
    cmds.iconTextCheckBox(
        item,
        i1="gridDisplay.png",
        w=iconsize,
        h=iconsize,
        v=0,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGridToggleVisibility")'
        ),
        cc=cmd
    )

    item = ned + "GridToggleSnap"
    cmd = 'mel.eval("NodeEditorGridToggleSnap")'
    cmds.iconTextCheckBox(
        item,
        i1="snapGrid.png",
        w=iconsize,
        h=iconsize,
        v=0,
        ann=mel.eval(
            'getRunTimeCommandAnnotation("NodeEditorGridToggleSnap")'
        ),
        cc=cmd
    )

    # Check for optionVar
    if cmds.optionVar(exists="nodeEditorShowGridIcons"):
        cmds.optionVar(iv=("nodeEditorShowGridIcons", 1))
    else:
        mel.eval('nodeEditorToggleGridIcons (`optionVar -q "nodeEditorShowGridIcons"`, "' + ned + '")')

    cmds.setParent()

    return jobS, jobI


# TOGGLE THE BUTTONS ON AND OFF DEFINITIONS
def nodeEditorToggleDisplayIconsPy(arg, ned):
    state = cmds.iconTextRadioButton(ned + "SSRB", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextRadioButton(ned + "SSRB", e=True, manage=state)
    cmds.iconTextRadioButton(ned + "SSGRB", e=True, manage=state)
    cmds.iconTextRadioButton(ned + "NSRB", e=True, manage=state)
    cmds.separator(ned + 'DisplayLockSeparator', e=True, manage=state)
    cmds.iconTextButton(ned + "LCB", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "DisplayCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "DisplayCollapse", e=True, i1='openBar.png')


def nodeEditorToggleLayoutIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "LCCV", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "LCCV", e=True, manage=state)
    cmds.iconTextButton(ned + "ADDSEL", e=True, manage=state)
    cmds.iconTextButton(ned + "LCDA", e=True, manage=state)
    cmds.iconTextButton(ned + "LCHSR", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "LayoutCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "LayoutCollapse", e=True, i1='openBar.png')


# -----------------------------------------------------------------------------
def nodeEditorToggleMauIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "LCCLEAN", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "LCCLEAN", e=True, manage=state)
    cmds.iconTextButton(ned + "LCSTATE", e=True, manage=state)
    cmds.iconTextButton(ned + "LCINTER", e=True, manage=state)
    cmds.iconTextButton(ned + "LCPSH", e=True, manage=state)
    cmds.iconTextButton(ned + "LCISO", e=True, manage=state)
    cmds.iconTextButton(ned + "LCSHAPE", e=True, manage=state)
    cmds.iconTextButton(ned + "LCCONNECTOR", e=True, manage=state)
    cmds.iconTextButton(ned + "LCMCONNECTOR", e=True, manage=state)
    cmds.iconTextButton(ned + "LCSEPA", e=True, manage=state)
    cmds.iconTextButton(ned + "LCUNITE", e=True, manage=state)
    cmds.iconTextButton(ned + "LCSWN", e=True, manage=state)
    cmds.iconTextButton(ned + "LCGRP", e=True, manage=state)
    cmds.iconTextButton(ned + "LCDUP", e=True, manage=state)
    cmds.iconTextButton(ned + "LCSDC", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "MauCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "MauCollapse", e=True, i1='openBar.png')


# CHANGE THE ICON OF THE NODE EDITOR BASED ON THE MESH STATE
def mauStateCheckUI(ui):
    sel = cmds.ls(sl=True)
    if sel:
        if len(sel[0].split('.')) == 1:
            if cmds.getAttr(sel[0] + '.nodeState'):
                cmds.iconTextButton(ui, e=True, i='refreshGray')
            else:
                cmds.iconTextButton(ui, e=True, i='refresh')


# CHANGE THE ICON OF THE NODE EDITOR BASED ON THE MESH INTERMEDIATE STATE
def mauInterCheckUI(ui):
    sel = cmds.ls(sl=True)
    if sel:
        if len(sel[0].split('.')) == 1:
            if cmds.attributeQuery('intermediateObject', n=sel[0], ex=True):
                if cmds.getAttr(sel[0] + '.intermediateObject'):
                    cmds.iconTextButton(ui, e=True, i='out_mesh')
                else:
                    cmds.iconTextButton(ui, e=True, i='out_polyPlane')
# -----------------------------------------------------------------------------


def nodeEditorToggleRegraphIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "SNEI", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "SNEI", e=True, manage=state)
    cmds.iconTextButton(ned + "UPSTRM", e=True, manage=state)
    cmds.iconTextButton(ned + "UPDNSTRM", e=True, manage=state)
    cmds.iconTextButton(ned + "DNSTRM", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "RegraphCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "RegraphCollapse", e=True, i1='openBar.png')


def nodeEditorToggleDepthTraversalIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "ZeroDepth", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "ZeroDepth", e=True, manage=state)
    cmds.iconTextButton(ned + "ReduceOne", e=True, manage=state)
    cmds.textField(ned + "DepthTextField", e=True, manage=state)
    cmds.iconTextButton(ned + "IncreaseDepth", e=True, manage=state)
    cmds.iconTextButton(ned + "UnlimitedDepth", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(
            ned + "DepthTraversalCollapse",
            e=True,
            i1='closeBar.png'
        )
    elif state == 1:
        cmds.iconTextButton(
            ned + "DepthTraversalCollapse",
            e=True,
            i1='openBar.png'
        )


def nodeEditorToggleLodPinIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "LODSimpleMode", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "LODSimpleMode", e=True, manage=state)
    cmds.iconTextButton(ned + "LODConnectedMode", e=True, manage=state)
    cmds.iconTextButton(ned + "LODShowAll", e=True, manage=state)
    cmds.separator(ned + 'LodPinSeparator', e=True, manage=state)
    cmds.iconTextButton(ned + "PinnedOn", e=True, manage=state)
    cmds.iconTextButton(ned + "PinnedOff", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "LODPinCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "LODPinCollapse", e=True, i1='openBar.png')


def nodeEditorToggleBookmarkIconsPy(arg, ned):
    state = cmds.iconTextButton(ned + "AddBM", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextButton(ned + "AddBM", e=True, manage=state)
    cmds.iconTextButton(ned + "EditBM", e=True, manage=state)
    cmds.iconTextButton(ned + "FDBack", e=True, manage=state)
    cmds.iconTextButton(ned + "FDForward", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(
            ned + "BookmarkCollapse",
            e=True,
            i1='closeBar.png'
        )
    elif state == 1:
        cmds.iconTextButton(
            ned + "BookmarkCollapse",
            e=True,
            i1='openBar.png'
        )


def nodeEditorToggleGridIconsPy(arg, ned):
    state = cmds.iconTextCheckBox(
        ned + "GridToggleVisibility", q=True, manage=True)
    if state == 0:
        state = 1
    elif state == 1:
        state = 0

    cmds.iconTextCheckBox(ned + "GridToggleVisibility", e=True, manage=state)
    cmds.iconTextCheckBox(ned + "GridToggleSnap", e=True, manage=state)

    if state == 0:
        cmds.iconTextButton(ned + "GridCollapse", e=True, i1='closeBar.png')
    elif state == 1:
        cmds.iconTextButton(ned + "GridCollapse", e=True, i1='openBar.png')


def mTextureViewWindow():
    mel.eval('TextureViewWindow')
    uvTexGlob = mel.eval('string $temp = $gUVTexEditToolBar')

    uiextra = ['outV', 'outU', 'uvVal', 'inU', 'inV']
    for u in uiextra:
        if cmds.objExists(u):
            cmds.deleteUI(u)

    cmds.iconTextButton(
        'outV', w=30, h=20,
        p=uvTexGlob, i='arrowLeft',
        c='cmds.polyEditUV(u=-1*cmds.floatField("uvVal", q=True, v=True), v=0)'
    )
    cmds.iconTextButton(
        'outU', w=30, h=20,
        p=uvTexGlob, i='arrowDown',
        c='cmds.polyEditUV(u=0, v=-1*cmds.floatField("uvVal", q=True, v=True))'
    )
    cmds.floatField('uvVal', pre=1, w=30, p=uvTexGlob, v=1)
    cmds.iconTextButton(
        'inU', w=30, h=20,
        p=uvTexGlob, i='arrowUp',
        c='cmds.polyEditUV(u=0, v=cmds.floatField("uvVal", q=True, v=True))'
    )
    cmds.iconTextButton(
        'inV', w=30, h=20,
        p=uvTexGlob, i='arrowRight',
        c='cmds.polyEditUV(u=cmds.floatField("uvVal", q=True, v=True), v=0)'
    )
    # preset for iterations
    prst = [
        '-1.0', '-0.5', '-0.1', '0.1', '0.5', '1.0'
    ]
    pps = cmds.popupMenu('uvValue', p='uvVal')
    for p in prst:
        cmds.menuItem(
            label=p,
            p=pps,
            c="cmds.floatField('uvVal', e=True, v=" + p + ")"
        )
