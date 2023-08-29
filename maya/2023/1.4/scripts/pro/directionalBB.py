import maya.cmds as cmds
import string
import numpy as np


def eigenBB(dir, typ, geo):
    # create lists containing x,y,z position
    p = [[], [], []]
    po = []

    if(typ == 12):
        points = cmds.polyEvaluate(geo[0], v=True)
        for i in range(points):
            po = cmds.xform(
                (geo[0] + '.vtx[' + (str(i)) + ']'),
                q=True,
                ws=True,
                t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])
    elif(typ == 10):
        cPoints = (geo[0] + '.cv[0:' + str(int(
            cmds.getAttr(geo[0] + '.spansV') - 2)) + '][0:' + str(int(
            cmds.getAttr(geo[0] + '.spansV') - 1)) + ']')
        for i in (cmds.ls(cPoints, fl=True)):
            po = cmds.xform(i, q=True, ws=True, t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])

    elif (typ == 28 or typ == 31):
        points = geo
        for i in geo:
            po = cmds.xform(i, q=True, ws=True, t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])

    # create a numpy array containing point positions
    m = np.array([p[0], p[1], p[2]])

    # Calculate the center of the geometry
    length = len(p[0])
    centroid = ([sum(p[0]) / length, sum(p[1]) / length, sum(p[2]) / length])

    # calculate covariance matrix
    var_x = np.var(p[0], ddof=0)
    var_y = np.var(p[1], ddof=0)
    var_z = np.var(p[2], ddof=0)
    cov_xy = np.cov(p[0], p[1], bias=1)[0][1]
    cov_xz = np.cov(p[0], p[2], bias=1)[0][1]
    cov_yz = np.cov(p[1], p[2], bias=1)[0][1]

    matrix_covariant = np.array([
        [var_x, cov_xy, cov_xz],
        [cov_xy, var_y, cov_yz],
        [cov_xz, cov_yz, var_z]])

    # Calculate the eigenvalues and eigenvectors
    eigen = np.linalg.eigh(matrix_covariant)
    eigenmatrix = eigen[1]
    eigenvalues = eigen[0]

    # eigenvectors are the basis vectors of the new coordinate system
    # that is aligned with the object's "direction"
    eigenvec = [eigenmatrix[:, 0], eigenmatrix[:, 1], eigenmatrix[:, 2]]

    # Order the eigenvectors so that if eigenvalues[i] correspond to
    # eigenvector[i] then eigenvalues[i]>eigenvalues[i]>eigenvalues[i]
    eigenvec = [eigenvec[i] for i, x in sorted(enumerate(eigenvalues), key=lambda pair: pair[1], reverse=True)]

    return(eigenvec, centroid)


def eigenLoc():
    loc_obj = cmds.spaceLocator()
    return loc_obj


def eigenPivot(loc, geo):
    pc = cmds.parentConstraint(loc, geo, mo=True)
    p = cmds.xform(loc, q=True, m=True)
    cmds.setAttr((loc + '.t'), 0, 0, 0)
    cmds.setAttr((loc + '.r'), 0, 0, 0)
    cmds.delete(pc)
    cmds.makeIdentity(geo, apply=True, t=1, r=1, s=1, n=0)
    cmds.makeIdentity(geo, apply=False, t=1, r=1, s=1)
    pc = cmds.parentConstraint(loc, geo, mo=True)
    cmds.xform(loc, m=p)
    cmds.delete(pc, loc)
    cmds.delete(geo, ch=True)
    cmds.select(geo)

    # print 'Pivot Reworked'


def do_directionalBB(dir, typ, sel):
        eigenvecMau = eigenBB(dir, typ, sel)
        loc = eigenLoc()

        # define vectors and create target transformation matrix
        v0 = eigenvecMau[0][0]
        v1 = eigenvecMau[0][1]
        v2 = eigenvecMau[0][2]
        v3 = eigenvecMau[1]

        # translation (centroid)
        cmds.xform(
            loc,
            m=(
                v0[0], v0[1], v0[2], 0,
                v1[0], v1[1], v1[2], 0,
                v2[0], v2[1], v2[2], 0,
                v3[0], v3[1], v3[2], 1)
            )

        if dir == 1:
                # geo = string.split(sel[0], '.')
                geo = sel[0].split('.')
                eigenPivot(loc[0], geo[0])
        if cmds.objExists(loc):
            cmds.setAttr(loc[0] + '.s', 1, 1, 1)
        return loc, eigenvecMau


def directionalBB(dir):
        BB = ''
        typ = 0
        cond1 = [
            type(cmds.filterExpand(sm=31)).__name__ != 'NoneType',
            type(cmds.filterExpand(sm=28)).__name__ != 'NoneType'
            ]
        cond2 = [
            type(cmds.filterExpand(sm=32)).__name__ != 'NoneType',
            type(cmds.filterExpand(sm=34)).__name__ != 'NoneType'
            ]
        if any(cond1):  # vertex and CVs
                typ = 31
                BB = do_directionalBB(dir, typ, cmds.ls(sl=True, fl=True))
        elif any(cond2):  # edges and faces
                BB = cmds.confirmDialog(
                    t='OK',
                    m='Select only meshes, subDs, nurbs, vertexs,'
                    ' subD vertexs or nurbs control Vertexes'
                    )
        elif type(cmds.filterExpand(sm=12)).__name__ != 'NoneType':  # Meshes
                typ = 12
                BB = do_directionalBB(dir, typ, cmds.filterExpand(sm=12))
        elif type(cmds.filterExpand(sm=10)).__name__ != 'NoneType':  # Nurbs
                typ = 10
                BB = do_directionalBB(dir, typ, cmds.filterExpand(sm=10))
        return BB[0]


def mFastCentroid():
    # create lists containing x,y,z position
    p, po, typ = [[], [], []], [], 0
    geo = cmds.ls(sl=True, fl=True)
    if not geo:
        cmds.warning('Please select vertex CVs or subD vertex')
        return
    cond1 = [
        type(cmds.filterExpand(sm=31)).__name__ != 'NoneType',
        type(cmds.filterExpand(sm=28)).__name__ != 'NoneType']
    cond2 = [
        type(cmds.filterExpand(sm=32)).__name__ != 'NoneType',
        type(cmds.filterExpand(sm=34)).__name__ != 'NoneType']
    if any(cond1):  # vertex and CVs
            typ = 31
    elif any(cond2):  # edges and faces
            cmds.warning(
                'Select only meshes, subDs, nurbs, vertexs, subD vertexs or nurbs control Vertexes')
    elif type(cmds.filterExpand(sm=12)).__name__ != 'NoneType':  # Meshes
            typ = 12
    elif type(cmds.filterExpand(sm=10)).__name__ != 'NoneType':  # Nurbs
            typ = 10

    if typ == 12:
        points = cmds.polyEvaluate(geo[0], v=True)
        for i in range(points):
            po = cmds.xform(
                (geo[0] + '.vtx[' + (str(i)) + ']'),
                q=True,
                ws=True,
                t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])
    elif typ == 10:
        cPoints = (geo[0]+'.cv[0:'+str(int(cmds.getAttr(geo[0]+'.spansV')-2))+'][0:'+str(int(cmds.getAttr(geo[0]+'.spansV')-1))+']')
        for i in (cmds.ls(cPoints, fl=True)):
            po = cmds.xform(i, q=True, ws=True, t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])
    elif (typ == 28 or typ == 31):
        points = geo
        for i in geo:
            po = cmds.xform(i, q=True, ws=True, t=True)
            p[0].append(po[0])
            p[1].append(po[1])
            p[2].append(po[2])

    if typ != 0:
        # Calculate the center of the geometry
        length = len(p[0])
        # print length
        centroid = ([sum(p[0]) / length, sum(p[1]) / length, sum(p[2]) / length])
        loc_obj = cmds.spaceLocator()
        cmds.xform(
            loc_obj,
            t=(centroid[0], centroid[1], centroid[2]),
            ws=True)
        return centroid, loc_obj

'''


HOUDINI VERSION
http://www.sidefx.com/index.php?option=com_forum&Itemid=172&page=viewtopic&p=88114&highlight=#88114
http://vimeo.com/10274660


import numpy as np

# This code is called when instances of this SOP cook.
geo = hou.pwd().geometry()

# create lists containing x,y,z position
p=[ [],[],[]]
points = geo.points()
for i in points:
    p[0].append( i.position()[0] )
    p[1].append( i.position()[1] )
    p[2].append( i.position()[2] )

# create a numpy array containing point positions
m = np.array([p[0],p[1],p[2]])

#Calculate the center of the geometry
length = len(p[0])
centroid = hou.Vector3([ sum(p[0])/length, sum(p[1])/length, sum(p[2])/length ])

#calculate covariance matrix
var_x = np.var(p[0],ddof = 0)
var_y = np.var(p[1],ddof = 0)
var_z = np.var(p[2],ddof = 0)
cov_xy = np.cov(p[0],p[1],bias = 1)[0][1]
cov_xz = np.cov(p[0],p[2],bias = 1)[0][1]
cov_yz = np.cov(p[1],p[2],bias = 1)[0][1]

matrix_covariant = np.array([
[var_x,cov_xy,cov_xz],
[cov_xy,var_y,cov_yz],
[cov_xz,cov_yz,var_z]])

#Calculate the eigenvalues and eigenvectors
eigen = np.linalg.eigh(matrix_covariant)
eigenmatrix = eigen[1]
eigenvalues = eigen[0]

#eigenvectors are the basis vectors of the new coordinate system that is aligned with the object's "direction"
eigenvec = [eigenmatrix[:,0],eigenmatrix[:,1],eigenmatrix[:,2]]

#Order the eigenvectors so that if eigenvalues[i] correspond to eigenvector[i] then
#eigenvalues[i]>eigenvalues[i]>eigenvalues[i]
eigenvec = [eigenvec[i] for i,x in sorted(enumerate(eigenvalues), key=lambda pair: pair[1], reverse=True)]


#Adds a box into the network
def makebox():
    obj = hou.node("/obj")
    #check for existence
    if hou.node("/obj").glob("Bounding*") !=():
        pass
    else:
        bounding_obj = obj.createNode("geo","Bounding", run_init_scripts=False)
        bounding_obj.createNode("box")

#Transform the bounding box to the calculated eigenvectors.
def movebox():
    makebox()
    obj = hou.node("/obj")
    bbox_object = obj.node("Bounding")

    #calculate scale vector (by projecting points onto eigenvectors and taking the max and min)
    basis = [hou.Vector3( eigenvec[0] ),hou.Vector3( eigenvec[1] ),hou.Vector3( eigenvec[2] )]
    tlength=[ [], [], [] ]
    for i in points:
        p_vector = i.position()
        difference_vector = p_vector - centroid
        for j in basis:
            c = basis.index(j)
            tlength[c].append( difference_vector.dot(j) )

    s = [ np.ptp( tlength[0]), np.ptp( tlength[1]), np.ptp( tlength[2]) ] #ptp gets the range of an axis

    # set the scale matrix
    Ms = hou.Matrix4((
    (s[0],0,0,0),
    (0,s[1],0,0),
    (0,0,s[2],0),
    (0, 0, 0, 1)))

    #define vectors and create target transformation matrix
    v0 = eigenvec[0]
    v1 = eigenvec[1]
    v2 = eigenvec[2]
    v3 = centroid

    Mp = hou.Matrix4((
    (v0[0],v0[1],v0[2],0),
    (v1[0],v1[1],v1[2],0),
    (v2[0],v2[1],v2[2],0),
    (v3[0],v3[1],v3[2],1))) #translation (centroid)


    #set the bounding box transformation matrix to the target transformation matrix
    Mp = Ms*Mp
    bbox_object.setWorldTransform(Mp)

###---------------------------------


movebox()
'''
