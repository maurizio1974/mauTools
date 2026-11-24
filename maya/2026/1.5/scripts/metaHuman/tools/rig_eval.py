"""Evaluate a MetaHuman face like Maya does: RigLogic -> blendshapes -> skinCluster (linear blend)."""
import numpy as np
from mh_dna_geo import euler_xyz_matrix


class Rig(object):
    def __init__(self, reader, meshes, joints, lod=0):
        import riglogic
        cfg = riglogic.Configuration()
        cfg.calculationType = riglogic.CalculationType_Scalar
        self.rl = riglogic.RigLogic(reader, cfg)
        self.ri = riglogic.RigInstance(self.rl)
        self.ri.setLOD(lod)
        self.meshes, self.j = meshes, joints
        self.gui_names = [reader.getGUIControlName(i) for i in range(reader.getGUIControlCount())]
        self.bind_inv = np.linalg.inv(joints["world"])
        self.channel_names = [reader.getBlendShapeChannelName(i) for i in range(reader.getBlendShapeChannelCount())]

    def evaluate(self, gui):
        """gui: {name: value}. Returns (posed world matrices, blendshape channel weights, map values)."""
        for i, n in enumerate(self.gui_names):
            self.ri.setGUIControl(i, float(gui.get(n, 0.0)))
        self.rl.mapGUIToRawControls(self.ri)
        self.rl.calculate(self.ri)
        jo = np.array(self.ri.getJointOutputs()).reshape(-1, 9)
        bs = np.array(self.ri.getBlendShapeOutputs())
        am = np.array(self.ri.getAnimatedMapOutputs())
        J = self.j
        n = len(J["names"])
        world = np.zeros((n, 4, 4))
        for i in range(n):
            L = np.eye(4)
            L[:3, :3] = np.diag(1.0 + jo[i, 6:9]) @ euler_xyz_matrix(*jo[i, 3:6]) @ euler_xyz_matrix(*J["r"][i])
            L[3, :3] = J["t"][i] + jo[i, 0:3]
            p = J["parents"][i]
            world[i] = L if p == i else L @ world[p]
        return world, bs, am

    def deform(self, mesh, world, bs, pos=None):
        """pos: neutral positions to deform (defaults to the mesh's own)."""
        p = (mesh["pos"] if pos is None else pos).copy()
        for t in mesh["targets"]:
            w = bs[t["channel"]]
            if w != 0.0 and len(t["idx"]):
                p[t["idx"]] += w * t["delta"]
        skin = self.bind_inv @ world  # (n,4,4)
        out = np.zeros_like(p)
        ph = np.concatenate([p, np.ones((len(p), 1))], 1)
        for v in range(len(p)):
            js, ws = mesh["skin_joints"][v], mesh["skin_weights"][v]
            if len(js) == 0:
                out[v] = p[v]
                continue
            M = np.tensordot(ws, skin[js], axes=1)
            out[v] = (ph[v] @ M)[:3]
        return out


def skin_arrays(mesh, max_inf=None):
    """Dense (V, K) joint ids / weights for fast skinning."""
    K = max(len(j) for j in mesh["skin_joints"]) if max_inf is None else max_inf
    V = len(mesh["skin_joints"])
    ids = np.zeros((V, K), np.int64)
    w = np.zeros((V, K))
    for v in range(V):
        k = len(mesh["skin_joints"][v])
        ids[v, :k] = mesh["skin_joints"][v]
        w[v, :k] = mesh["skin_weights"][v]
    return ids, w


def deform_fast(rig, mesh, world, bs, pos=None, skin=None):
    p = (mesh["pos"] if pos is None else pos).copy()
    for t in mesh["targets"]:
        w = bs[t["channel"]]
        if w != 0.0 and len(t["idx"]):
            p[t["idx"]] += w * t["delta"]
    ids, w = skin if skin is not None else skin_arrays(mesh)
    S = rig.bind_inv @ world
    ph = np.concatenate([p, np.ones((len(p), 1))], 1)
    M = np.einsum("vk,vkij->vij", w, S[ids])
    return np.einsum("vi,vij->vj", ph, M)[:, :3]
