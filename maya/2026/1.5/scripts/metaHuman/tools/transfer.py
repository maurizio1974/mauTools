"""
After the head fit: move the other LOD meshes and the joints, and write the new DNA.

  eyes, eyeshell        rigid (rotation + translation + scale) from the eyelid ring around each eye
  teeth, saliva         rigid from the mouth region (lips + mouth interior)
  lashes, eyeEdge,      bound to the head surface (closest triangle, barycentric + normal offset)
  cartilage
  joints                eye / teeth families rigid as above; all others by a smooth (thin-plate)
                        interpolation of the head displacement; orientations kept, local
                        translations recomputed
Blendshape deltas and the Rig Logic data are kept as they are.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator

import fit as F


def apply_sim(sim, P):
    s, R, t = sim
    return s * P @ R.T + t


def region_sim(T0, X, ids, scale=True):
    return F.umeyama(T0[ids], X[ids], scale=scale)


def closest_on_triangles(P, V, T, cand=12):
    """Closest point of each P on the mesh (V, T): (tri index, barycentric (3,), point)."""
    cent = V[T].mean(1)
    tree = cKDTree(cent)
    _, near = tree.query(P, k=cand)
    best_d = np.full(len(P), np.inf)
    best_t = np.zeros(len(P), int)
    best_b = np.zeros((len(P), 3))
    for c in range(near.shape[1]):
        tri = near[:, c]
        a, b, cc = V[T[tri, 0]], V[T[tri, 1]], V[T[tri, 2]]
        bary = _closest_bary(P, a, b, cc)
        q = bary[:, 0:1] * a + bary[:, 1:2] * b + bary[:, 2:3] * cc
        d = np.linalg.norm(P - q, axis=1)
        better = d < best_d
        best_d[better], best_t[better], best_b[better] = d[better], tri[better], bary[better]
    return best_t, best_b


def _closest_bary(p, a, b, c):
    """Ericson's closest point on triangle, vectorised; returns barycentric weights."""
    ab, ac, ap = b - a, c - a, p - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    out = np.zeros((len(p), 3))
    den = va + vb + vc
    den[den == 0] = 1e-30
    v = vb / den
    w = vc / den
    out[:] = np.stack([1 - v - w, v, w], 1)
    # regions (order matters: later assignments win only where their condition holds)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3)
    out[m] = np.stack([1 - t, t, 0 * t], 1)[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6)
    out[m] = np.stack([1 - t, 0 * t, t], 1)[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6))
    out[m] = np.stack([0 * t, 1 - t, t], 1)[m]
    m = (d1 <= 0) & (d2 <= 0)
    out[m] = [1, 0, 0]
    m = (d3 >= 0) & (d4 <= d3)
    out[m] = [0, 1, 0]
    m = (d6 >= 0) & (d5 <= d6)
    out[m] = [0, 0, 1]
    return out


def face_frames(V, T):
    """Per-triangle orthonormal frame (e1, e2, n) rows."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1 = b - a
    e1 /= np.linalg.norm(e1, axis=1, keepdims=True) + 1e-12
    n = np.cross(b - a, c - a)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    e2 = np.cross(n, e1)
    return np.stack([e1, e2, n], 1)


def surface_bind(P, V0, T, X):
    """Carry points P (near the template surface V0) onto the fitted surface X, keeping their
    offset from the surface in the local triangle frame."""
    tri, bary = closest_on_triangles(P, V0, T)
    q0 = np.einsum("ij,ijk->ik", bary, V0[T[tri]])
    off = np.einsum("ij,ikj->ik", P - q0, face_frames(V0, T)[tri])      # local coords
    q1 = np.einsum("ij,ijk->ik", bary, X[T[tri]])
    # local scale: ratio of triangle sizes
    a0 = np.linalg.norm(np.cross(V0[T[tri, 1]] - V0[T[tri, 0]], V0[T[tri, 2]] - V0[T[tri, 0]]), axis=1)
    a1 = np.linalg.norm(np.cross(X[T[tri, 1]] - X[T[tri, 0]], X[T[tri, 2]] - X[T[tri, 0]]), axis=1)
    k = np.sqrt(np.clip(a1 / np.maximum(a0, 1e-12), 0.25, 4.0))[:, None]
    return q1 + k * np.einsum("ik,ikj->ij", off, face_frames(X, T)[tri])


def refit_rig(meshes, joints, head_index, X, exterior, log=print):
    """Returns (new positions per mesh name, new joint world positions, info)."""
    head = meshes[head_index]
    T0 = head["pos"]
    tris = None
    import mh_dna_geo as G
    tris = G.triangles(head)
    names = joints["names"]
    W = joints["world"]
    jpos = W[:, 3, :3].copy()
    new_pos = {head["name"]: X.copy()}
    info = {}

    # --- eyes: eyelid ring around each eye
    sims = {}
    for side in "LR":
        ej = names.index("FACIAL_%s_Eye" % side)
        c = jpos[ej]
        d = np.linalg.norm(T0 - c, axis=1)
        ring = np.where(exterior & (d < 2.2))[0]
        sims[side] = region_sim(T0, X, ring)
        info["eye_%s" % side] = (len(ring), sims[side][0])
    # --- mouth: lips + mouth interior around the teeth
    teeth = [m for m in meshes if m["name"].startswith("teeth")][0]
    tc = teeth["pos"].mean(0)
    d = np.linalg.norm(T0 - tc, axis=1)
    mouth = np.where(d < 4.0)[0]
    sims["mouth"] = region_sim(T0, X, mouth)
    info["mouth"] = (len(mouth), sims["mouth"][0])

    for m in meshes:
        n = m["name"].split("_")[0]
        if m is head:
            continue
        P = m["pos"]
        if n in ("eyeLeft", "eyeRight"):
            new_pos[m["name"]] = apply_sim(sims["L" if n == "eyeLeft" else "R"], P)
        elif n == "eyeshell":
            out = P.copy()
            for side, sel in (("L", P[:, 0] >= 0), ("R", P[:, 0] < 0)):
                out[sel] = apply_sim(sims[side], P[sel])
            new_pos[m["name"]] = out
        elif n in ("teeth", "saliva"):
            new_pos[m["name"]] = apply_sim(sims["mouth"], P)
        else:  # eyelashes, eyeEdge, cartilage and anything else on the skin
            new_pos[m["name"]] = surface_bind(P, T0, tris, X)

    # --- joints
    rng = np.random.default_rng(0)
    sample = np.unique(np.concatenate([rng.choice(len(T0), min(6000, len(T0)), replace=False), mouth]))
    rbf = RBFInterpolator(T0[sample], (X - T0)[sample], kernel="thin_plate_spline", neighbors=64, smoothing=1e-3)
    disp = rbf(jpos)
    new_j = jpos + disp
    for i, jn in enumerate(names):
        base = jn.replace("FACIAL_", "")
        if base.startswith(("L_Eye", "R_Eye", "L_Pupil", "R_Pupil")) and "Eyelid" not in base and "Eyelash" not in base \
                and "EyeCorner" not in base and "Eyesack" not in base:
            new_j[i] = apply_sim(sims[base[0]], jpos[i][None])[0]
        elif base.startswith(("C_Teeth", "C_Tongue", "L_Tongue", "R_Tongue")):
            new_j[i] = apply_sim(sims["mouth"], jpos[i][None])[0]
    return new_pos, new_j, info


def local_translations(joints, new_world_pos):
    """Keep every joint's world orientation, recompute local translations for new positions."""
    W = joints["world"]
    par = joints["parents"]
    t = np.zeros_like(joints["t"])
    for i in range(len(par)):
        p = par[i]
        if p == i:
            t[i] = new_world_pos[i]
        else:
            t[i] = (new_world_pos[i] - new_world_pos[p]) @ np.linalg.inv(W[p][:3, :3])
    return t


def write_dna(src_path, out_path, new_pos, joint_t, lod=0, recompute_normals=True, behaviour_scale=1.0):
    """LOD `lod` only DNA = source with new vertex positions and neutral joint translations.
    behaviour_scale: multiplies Rig Logic joint translations and all blendshape deltas (a bigger head
    moves proportionally more); rotations are unchanged."""
    import dna
    import mh_dna_geo as G
    s = dna.FileStream(src_path, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
    r = dna.BinaryStreamReader(s, dna.DataLayer_All, dna.UnknownLayerPolicy_Preserve, lod, lod)
    r.read()
    if not dna.Status.isOk():
        raise RuntimeError(dna.Status.get().message)
    o = dna.FileStream(out_path, dna.FileStream.AccessMode_Write, dna.FileStream.OpenMode_Binary)
    w = dna.BinaryStreamWriter(o)
    w.setFrom(r)
    for m in range(r.getMeshCount()):
        name = r.getMeshName(m)
        if name not in new_pos:
            continue
        P = np.asarray(new_pos[name], np.float64)
        w.setVertexPositions(m, [[float(x), float(y), float(z)] for x, y, z in P])
        if recompute_normals:
            mesh = G.read_mesh(r, m)
            nrm = F.vertex_normals(P, G.triangles(mesh))
            # DNA normals are per layout-normal index; positions and normals share the layout
            ln = np.array(r.getVertexLayoutNormalIndices(m))
            lp = np.array(r.getVertexLayoutPositionIndices(m))
            N = np.zeros((r.getVertexNormalCount(m), 3))
            N[ln] = nrm[lp]
            w.setVertexNormals(m, [[float(x), float(y), float(z)] for x, y, z in N])
    w.setNeutralJointTranslations([[float(x), float(y), float(z)] for x, y, z in joint_t])
    if behaviour_scale != 1.0:
        k = float(behaviour_scale)
        for g in range(r.getJointGroupCount()):
            outs = np.array(r.getJointGroupOutputIndices(g))
            vals = np.array(r.getJointGroupValues(g), np.float64)
            if len(outs) and len(vals):
                M = vals.reshape(len(outs), -1)
                M[(outs % 9) < 3] *= k          # translation rows only
                w.setJointGroupValues(g, [float(v) for v in M.ravel()])
        for m in range(r.getMeshCount()):
            for t in range(r.getBlendShapeTargetCount(m)):
                if r.getBlendShapeTargetDeltaCount(m, t):
                    D = np.stack([np.array(r.getBlendShapeTargetDeltaXs(m, t)), np.array(r.getBlendShapeTargetDeltaYs(m, t)),
                                  np.array(r.getBlendShapeTargetDeltaZs(m, t))], 1) * k
                    w.setBlendShapeTargetDeltas(m, t, [[float(x), float(y), float(z)] for x, y, z in D])
    w.write()
    if not dna.Status.isOk():
        raise RuntimeError(dna.Status.get().message)
