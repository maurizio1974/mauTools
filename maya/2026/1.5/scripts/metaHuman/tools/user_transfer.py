"""Rig the user's own mesh from the fitted MetaHuman head: skin weights and blendshape deltas are
interpolated at each user vertex's closest point on the fitted head (barycentric)."""
import numpy as np
from scipy.spatial import cKDTree

import fit as F
from transfer import _closest_bary


def read_obj(path):
    V, VT, faces, fuv = [], [], [], []
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("vt "):
            VT.append([float(x) for x in line.split()[1:3]])
        elif line.startswith("f "):
            f, t = [], []
            for tok in line.split()[1:]:
                parts = tok.split("/")
                vi = int(parts[0])
                f.append(vi - 1 if vi > 0 else len(V) + vi)
                if len(parts) > 1 and parts[1]:
                    ti = int(parts[1])
                    t.append(ti - 1 if ti > 0 else len(VT) + ti)
            faces.append(f)
            fuv.append(t if len(t) == len(f) else None)
    V = np.array(V, np.float64)
    counts = np.array([len(f) for f in faces])
    connects = np.concatenate([np.array(f) for f in faces])
    has_uv = len(VT) > 0 and all(t is not None for t in fuv)
    return {"pos": V, "counts": counts, "connects": connects,
            "uv": np.array(VT, np.float64) if has_uv else np.zeros((0, 2)),
            "uv_ids": np.concatenate([np.array(t) for t in fuv]) if has_uv else np.zeros(0, int)}


def write_obj(path, mesh):
    with open(path, "w") as f:
        for p in mesh["pos"]:
            f.write("v %.6f %.6f %.6f\n" % tuple(p))
        has_uv = len(mesh.get("uv", [])) > 0
        if has_uv:
            for u in mesh["uv"]:
                f.write("vt %.6f %.6f\n" % tuple(u))
        s = 0
        for c in mesh["counts"]:
            ids = mesh["connects"][s:s + c] + 1
            if has_uv:
                uvs = mesh["uv_ids"][s:s + c] + 1
                f.write("f " + " ".join("%d/%d" % (a, b) for a, b in zip(ids, uvs)) + "\n")
            else:
                f.write("f " + " ".join(str(a) for a in ids) + "\n")
            s += c


def triangles(mesh):
    tris, s = [], 0
    for c in mesh["counts"]:
        f = mesh["connects"][s:s + c]
        tris += [(f[0], f[i], f[i + 1]) for i in range(1, c - 1)]
        s += c
    return np.array(tris, np.int64)


def bind(P, PN, V, T, cand=24, normal_cos=0.2, signed=False):
    """Closest triangle of mesh (V, T) for each point, preferring triangles whose normal agrees with
    the point's normal (so a vertex on the upper lip doesn't bind to the lower lip)."""
    cent = V[T].mean(1)
    tn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    tn /= np.linalg.norm(tn, axis=1, keepdims=True) + 1e-12
    _, near = cKDTree(cent).query(P, k=cand)
    best = np.full(len(P), np.inf)
    bt = np.zeros(len(P), int)
    bb = np.zeros((len(P), 3))
    for c in range(cand):
        tri = near[:, c]
        a, b, cc = V[T[tri, 0]], V[T[tri, 1]], V[T[tri, 2]]
        bary = _closest_bary(P, a, b, cc)
        q = bary[:, :1] * a + bary[:, 1:2] * b + bary[:, 2:3] * cc
        d = np.linalg.norm(P - q, axis=1)
        cosn = (tn[tri] * PN).sum(1)
        agree = cosn if signed else np.abs(cosn)  # signed when the user mesh's winding is consistent
        score = d + np.where(agree < normal_cos, 10.0, 0.0) + (1 - agree) * 0.05
        better = score < best
        best[better], bt[better], bb[better] = score[better], tri[better], bary[better]
    return bt, bb


def transfer(user, head, X, head_tris, max_influence=8, delta_eps=1e-5, log=print):
    """user: mesh dict (pos in MetaHuman space). head: DNA head mesh dict; X: fitted head positions."""
    ut = triangles(user)
    un = F.vertex_normals(user["pos"], ut)
    sign = F.orientation_sign(user["pos"], ut)
    if sign:
        un = un * sign
    log("  user mesh winding: %s" % ({1: "consistent, normals out", -1: "consistent, normals in (flipped here)",
                                      0: "inconsistent: lips are told apart by distance only"}[sign]))
    tri, bary = bind(user["pos"], un, X, head_tris, signed=bool(sign))
    vids = head_tris[tri]                                      # (V,3) head vertex ids
    d = np.linalg.norm(user["pos"] - np.einsum("ij,ijk->ik", bary, X[vids]), axis=1)
    log("  user vertices bound: median distance to fitted head %.3f cm, 95%% %.3f cm, max %.3f cm"
        % (np.median(d), np.percentile(d, 95), d.max()))
    # skin
    sj, sw = [], []
    for v in range(len(user["pos"])):
        acc = {}
        for k in range(3):
            hv = vids[v, k]
            for j, w in zip(head["skin_joints"][hv], head["skin_weights"][hv]):
                acc[int(j)] = acc.get(int(j), 0.0) + bary[v, k] * w
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:max_influence]
        tot = sum(w for _, w in top) or 1.0
        sj.append(np.array([j for j, _ in top], np.int64))
        sw.append(np.array([w / tot for _, w in top]))
    # blendshapes
    targets = []
    nh = len(X)
    for tg in head["targets"]:
        if not len(tg["idx"]):
            continue
        D = np.zeros((nh, 3))
        D[tg["idx"]] = tg["delta"]
        du = np.einsum("ij,ijk->ik", bary, D[vids])
        keep = np.where(np.abs(du).max(1) > delta_eps)[0]
        if len(keep):
            targets.append({"channel": tg["channel"], "idx": keep, "delta": du[keep]})
    log("  %d blendshape targets transferred" % len(targets))
    return {"skin_joints": sj, "skin_weights": sw, "targets": targets, "bind_tri": tri, "bind_bary": bary,
            "bind_dist": d, "max_influence": max_influence}


def save_npz(path, name, user, tr):
    obj = lambda lst: np.array(lst + [None], dtype=object)[:-1]   # keep a 1-D object array
    np.savez_compressed(path, name=name, pos=user["pos"], counts=user["counts"], connects=user["connects"],
                        uv=user["uv"], uv_ids=user["uv_ids"], skin_joints=obj(tr["skin_joints"]),
                        skin_weights=obj(tr["skin_weights"]), targets=obj(tr["targets"]),
                        max_influence=tr["max_influence"])
