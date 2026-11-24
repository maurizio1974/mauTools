"""Read LOD geometry, joints and skinning from a MetaHuman DNA into numpy (OpenRigLogic `dna`)."""
import numpy as np


def open_dna(path):
    from mh_paths import ensure_dna
    dna = ensure_dna()
    s = dna.FileStream(path, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
    r = dna.BinaryStreamReader(s, dna.DataLayer_All)
    r.read()
    if not dna.Status.isOk():
        raise RuntimeError("Error loading DNA %s: %s" % (path, dna.Status.get().message))
    return r


def euler_xyz_matrix(rx, ry, rz):
    """Maya rotate order xyz, row-vector convention (p' = p @ M), degrees."""
    x, y, z = np.radians([rx, ry, rz])
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, sx], [0, -sx, cx]])
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rz = np.array([[cz, sz, 0], [-sz, cz, 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def read_mesh(r, m):
    n = r.getVertexPositionCount(m)
    pos = np.stack([np.array(r.getVertexPositionXs(m)), np.array(r.getVertexPositionYs(m)),
                    np.array(r.getVertexPositionZs(m))], 1).astype(np.float64)
    lay_pos = np.array(r.getVertexLayoutPositionIndices(m), np.int64)
    lay_uv = np.array(r.getVertexLayoutTextureCoordinateIndices(m), np.int64)
    uv = np.stack([np.array(r.getVertexTextureCoordinateUs(m)), np.array(r.getVertexTextureCoordinateVs(m))], 1)
    faces_layout = [np.array(r.getFaceVertexLayoutIndices(m, f), np.int64) for f in range(r.getFaceCount(m))]
    counts = np.array([len(f) for f in faces_layout])
    flat_layout = np.concatenate(faces_layout)
    # skin weights
    sk_j, sk_w = [], []
    for v in range(n):
        sk_j.append(np.array(r.getSkinWeightsJointIndices(m, v), np.int64))
        sk_w.append(np.array(r.getSkinWeightsValues(m, v), np.float64))
    # blendshape targets
    targets = []
    for t in range(r.getBlendShapeTargetCount(m)):
        idx = np.array(r.getBlendShapeTargetVertexIndices(m, t), np.int64)
        d = np.stack([np.array(r.getBlendShapeTargetDeltaXs(m, t)), np.array(r.getBlendShapeTargetDeltaYs(m, t)),
                      np.array(r.getBlendShapeTargetDeltaZs(m, t))], 1) if len(idx) else np.zeros((0, 3))
        targets.append({"channel": int(r.getBlendShapeChannelIndex(m, t)), "idx": idx, "delta": d})
    return {"index": m, "name": r.getMeshName(m), "pos": pos, "counts": counts,
            "connects": lay_pos[flat_layout], "uv": uv, "uv_ids": lay_uv[flat_layout],
            "skin_joints": sk_j, "skin_weights": sk_w, "targets": targets,
            "max_influence": int(r.getMaximumInfluencePerVertex(m))}


def triangles(mesh):
    """Fan-triangulate polygons -> (T, 3) vertex ids."""
    tris = []
    start = 0
    c = mesh["connects"]
    for k in mesh["counts"]:
        f = c[start:start + k]
        for i in range(1, k - 1):
            tris.append((f[0], f[i], f[i + 1]))
        start += k
    return np.array(tris, np.int64)


def read_joints(r):
    n = r.getJointCount()
    names = [r.getJointName(i) for i in range(n)]
    parents = np.array([r.getJointParentIndex(i) for i in range(n)])
    t = np.array([list(r.getNeutralJointTranslation(i)) for i in range(n)], np.float64)
    rot = np.array([list(r.getNeutralJointRotation(i)) for i in range(n)], np.float64)
    world = np.zeros((n, 4, 4))
    for i in range(n):  # parents always come first in a DNA
        L = np.eye(4)
        L[:3, :3] = euler_xyz_matrix(*rot[i])
        L[3, :3] = t[i]
        p = parents[i]
        world[i] = L if p == i else L @ world[p]
    return {"names": names, "parents": parents, "t": t, "r": rot, "world": world}


def read_lod(path, lod=0):
    r = open_dna(path)
    meshes = [read_mesh(r, m) for m in r.getMeshIndicesForLOD(lod)]
    return r, meshes, read_joints(r)
