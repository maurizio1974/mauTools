import pymel.core as pm

# Our mesh and transform
mesh = pm.PyNode('pCone1')
loc = pm.PyNode('locator1')

# creating a poly cube that we will use to manipulate the shape to the origin
# this is what we will get the boudning box of
local_shape = pm.polyCube(ch=False)[0]
transform_geo_node = pm.createNode('transformGeometry')
mesh.getShape().worldMesh >> transform_geo_node.inputGeometry
transform_geo_node.outputGeometry >> local_shape.getShape().inMesh

# using the transform geo I'm connecting the worldInverseMatrix in to the transformGeo
# This will basically bring the shape back to the origin and align it to the local space of our locator
loc.worldInverseMatrix >> transform_geo_node.transform
pm.delete(local_shape, ch=True)
local_bounding = local_shape.getBoundingBox()
# to get the scale values of the bounding box I'm just taking the largest values and subtracting the smallest ones
# we also need to get the ratio or scale difference so that we can make sure that the lattice shape doesn't have
# any built in scale, we want to set the scale with the transform so that we can match it with our lattice base
scale_x = local_bounding[1][0] - local_bounding[0][0]
scale_x_ratio = 1.0/scale_x
scale_y = local_bounding[1][1] - local_bounding[0][1]
scale_y_ratio = 1.0/scale_y
scale_z = local_bounding[1][2] - local_bounding[0][2]
scale_z_ratio = 1.0/scale_z

scaled_bounding = [[],[]]
scaled_bounding[0] = [local_bounding[0][0]*scale_x_ratio, local_bounding[0][1]*scale_y_ratio, local_bounding[0][2]*scale_z_ratio]
scaled_bounding[1] = [local_bounding[1][0]*scale_x_ratio, local_bounding[1][1]*scale_y_ratio, local_bounding[1][2]*scale_z_ratio]

# just creating and getting the lattice objects
lattice_data = pm.lattice(mesh, dv=(2,2,2))
lattice_node = lattice_data[0]
lattice = lattice_data[1]
lattice_base = lattice_data[2]

# setting the lattice to our bounding box just to make it easier to get the object center of it
pm.xform(lattice.pt[0][0][0], t=local_bounding[0])
pm.xform(lattice.pt[0][0][1], t=[local_bounding[0][0], local_bounding[0][1], local_bounding[1][2]])
pm.xform(lattice.pt[0][1][1], t=[local_bounding[0][0], local_bounding[1][1], local_bounding[1][2]])
pm.xform(lattice.pt[0][1][0], t=[local_bounding[0][0], local_bounding[1][1], local_bounding[0][2]])
pm.xform(lattice.pt[1][1][0], t=[local_bounding[1][0], local_bounding[1][1], local_bounding[0][2]])
pm.xform(lattice.pt[1][0][1], t=[local_bounding[1][0], local_bounding[0][1], local_bounding[1][2]])
pm.xform(lattice.pt[1][0][0], t=[local_bounding[1][0], local_bounding[0][1], local_bounding[0][2]])
pm.xform(lattice.pt[1][1][1], t=local_bounding[1])
# we need to get the object center of it, because this is basically the offset from the origin
# we need to store this for later
lattice_offset = pm.objectCenter(lattice)

# after we've gotten the offset we can now apply the scaled bounding box values
pm.xform(lattice.pt[0][0][0], t=scaled_bounding[0])
pm.xform(lattice.pt[0][0][1], t=[scaled_bounding[0][0], scaled_bounding[0][1], scaled_bounding[1][2]])
pm.xform(lattice.pt[0][1][1], t=[scaled_bounding[0][0], scaled_bounding[1][1], scaled_bounding[1][2]])
pm.xform(lattice.pt[0][1][0], t=[scaled_bounding[0][0], scaled_bounding[1][1], scaled_bounding[0][2]])
pm.xform(lattice.pt[1][1][0], t=[scaled_bounding[1][0], scaled_bounding[1][1], scaled_bounding[0][2]])
pm.xform(lattice.pt[1][0][1], t=[scaled_bounding[1][0], scaled_bounding[0][1], scaled_bounding[1][2]])
pm.xform(lattice.pt[1][0][0], t=[scaled_bounding[1][0], scaled_bounding[0][1], scaled_bounding[0][2]])
pm.xform(lattice.pt[1][1][1], t=scaled_bounding[1])

# we need to get the offset of the scaled lattice as well so that we can remove it
# could probably skip this if we prepare this math earlier, but I'm lazy right now
scaled_lattice_offset = pm.objectCenter(lattice)

# loop through the scaled bounding values and remove the scaled lattice offset
centered_bounding = [[],[]]
centered_bounding[0] = [x - y for x,y in zip(scaled_bounding[0], scaled_lattice_offset)]
centered_bounding[1] = [x - y for x,y in zip(scaled_bounding[1], scaled_lattice_offset)]

# set the new centered bounding box
pm.xform(lattice.pt[0][0][0], t=centered_bounding[0])
pm.xform(lattice.pt[0][0][1], t=[centered_bounding[0][0], centered_bounding[0][1], centered_bounding[1][2]])
pm.xform(lattice.pt[0][1][1], t=[centered_bounding[0][0], centered_bounding[1][1], centered_bounding[1][2]])
pm.xform(lattice.pt[0][1][0], t=[centered_bounding[0][0], centered_bounding[1][1], centered_bounding[0][2]])
pm.xform(lattice.pt[1][1][0], t=[centered_bounding[1][0], centered_bounding[1][1], centered_bounding[0][2]])
pm.xform(lattice.pt[1][0][1], t=[centered_bounding[1][0], centered_bounding[0][1], centered_bounding[1][2]])
pm.xform(lattice.pt[1][0][0], t=[centered_bounding[1][0], centered_bounding[0][1], centered_bounding[0][2]])
pm.xform(lattice.pt[1][1][1], t=centered_bounding[1])

# move the lattice and lattice base to the transform input
# we also want to add the original lattice offset in the local space of the object (os=True)
lattice.setMatrix(loc.getMatrix(ws=True), ws=True)
lattice_base.setMatrix(loc.getMatrix(ws=True), ws=True)
pm.move(lattice_offset[0], lattice_offset[1], lattice_offset[2], lattice, r=True, os=True, wd=True)
pm.move(lattice_offset[0], lattice_offset[1], lattice_offset[2], lattice_base, r=True, os=True, wd=True)
# and we just set the scale that we calculated earlier
lattice.s.set(scale_x, scale_y, scale_z)
lattice_base.s.set(scale_x, scale_y, scale_z)