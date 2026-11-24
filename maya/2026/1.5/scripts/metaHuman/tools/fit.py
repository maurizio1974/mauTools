"""
Fit the MetaHuman head (template, MetaHuman topology) onto a head mesh of any topology.

  1. similarity alignment from landmarks (target -> MetaHuman space)
  2. non-rigid ICP: displacement-Laplacian smoothness + landmarks + point-to-plane / point-to-point
     data term on the template's OUTER surface only (mouth bag, eye sockets etc. just follow),
     stiffness decreasing over the iterations
Needs numpy + scipy (run outside Maya).
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.spatial import cKDTree

# template landmarks: named facial joints, snapped to the closest head-surface vertex
LANDMARK_JOINTS = [
    "FACIAL_L_EyeCornerInner", "FACIAL_R_EyeCornerInner", "FACIAL_L_EyeCornerOuter", "FACIAL_R_EyeCornerOuter",
    "FACIAL_L_EyelidUpperA", "FACIAL_R_EyelidUpperA", "FACIAL_L_EyelidLowerA", "FACIAL_R_EyelidLowerA",
    "FACIAL_L_LipCorner", "FACIAL_R_LipCorner", "FACIAL_C_LipUpper", "FACIAL_C_LipLower",
    "FACIAL_C_NoseTip", "FACIAL_L_Nostril", "FACIAL_R_Nostril", "FACIAL_C_NoseBridge",
    "FACIAL_C_Chin", "FACIAL_C_UnderChin", "FACIAL_L_Ear", "FACIAL_R_Ear",
    "FACIAL_C_Forehead", "FACIAL_L_Temple", "FACIAL_R_Temple", "FACIAL_L_Jawline", "FACIAL_R_Jawline",
    "FACIAL_L_CheekOuter", "FACIAL_R_CheekOuter",
]


# --------------------------------------------------------------------------- mesh helpers
def vertex_normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, T[:, k], n)
    return vn / (np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12)


def orientation_sign(V, T):
    """+1 / -1 if the mesh's winding is consistent (normals out / in), 0 if it is not consistent
    (then only |cos| between normals can be used)."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    key = np.minimum(e[:, 0], e[:, 1]) * (len(V) + 1) + np.maximum(e[:, 0], e[:, 1])
    fwd = e[:, 0] < e[:, 1]
    order = np.argsort(key)
    k, f = key[order], fwd[order]
    same = k[1:] == k[:-1]
    pairs_ok = (f[1:] != f[:-1])[same]                      # neighbours traverse a shared edge oppositely
    if pairs_ok.size == 0 or pairs_ok.mean() < 0.98:
        return 0
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    c = V.mean(0)
    out = np.einsum("ij,ij->i", n, V[T].mean(1) - c)
    return 1 if out.sum() >= 0 else -1


def uniform_laplacian(n, T):
    i = np.concatenate([T[:, 0], T[:, 1], T[:, 2], T[:, 1], T[:, 2], T[:, 0]])
    j = np.concatenate([T[:, 1], T[:, 2], T[:, 0], T[:, 0], T[:, 1], T[:, 2]])
    A = sp.coo_matrix((np.ones(len(i)), (i, j)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1
    return sp.eye(n) - sp.diags(1.0 / deg) @ A


def visible_vertices(V, T, views=48, size=700, tol=None):
    """Vertices seen from outside in at least one of `views` orthographic directions."""
    import render as R
    c = (V.max(0) + V.min(0)) / 2
    ext = np.linalg.norm(V.max(0) - V.min(0)) * 0.55
    tol = tol if tol is not None else ext * 2 / size * 1.5
    vis = np.zeros(len(V), bool)
    golden = np.pi * (3 - np.sqrt(5))
    for k in range(views):
        y = 1 - 2 * (k + 0.5) / views
        yaw = np.degrees(golden * k) % 360
        pitch = np.degrees(np.arcsin(y))
        _, cam = R.render([(V, T, (1, 1, 1))], size, yaw=yaw, pitch=pitch, center=c, extent=ext, return_camera=True)
        q = (V - c) @ cam["R"].T
        px = np.round((q[:, 0] / ext * 0.5 + 0.5) * (size - 1)).astype(int).clip(0, size - 1)
        py = np.round((0.5 - q[:, 1] / ext * 0.5) * (size - 1)).astype(int).clip(0, size - 1)
        vis |= q[:, 2] >= cam["zbuf"][py, px] - tol
    return vis


def sample_surface(V, T, density):
    """Points + normals densely sampled on triangles (for closest-point queries)."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    fn = n / (2 * area[:, None] + 1e-12)
    k = np.maximum(1, np.ceil(area * density)).astype(int)
    tri = np.repeat(np.arange(len(T)), k)
    r1, r2 = np.random.default_rng(0).random((2, len(tri)))
    s = np.sqrt(r1)
    w0, w1, w2 = 1 - s, s * (1 - r2), s * r2
    P = w0[:, None] * a[tri] + w1[:, None] * b[tri] + w2[:, None] * c[tri]
    P = np.concatenate([P, V])
    vn = vertex_normals(V, T)
    N = np.concatenate([fn[tri], vn])
    return P, N


def umeyama(src, dst, scale=True):
    """Similarity (s, R, t) with dst ~ s * src @ R.T + t."""
    ms, md = src.mean(0), dst.mean(0)
    S, D = src - ms, dst - md
    U, sig, Vt = np.linalg.svd(D.T @ S / len(src))
    d = np.sign(np.linalg.det(U @ Vt))
    E = np.diag([1, 1, d])
    R = U @ E @ Vt
    s = (sig * np.diag(E)).sum() / (S ** 2).sum() * len(src) if scale else 1.0
    t = md - s * ms @ R.T
    return s, R, t


# --------------------------------------------------------------------------- fit
def template_landmarks(head_pos, head_tris, joints, exterior):
    names = joints["names"]
    ids, used = {}, []
    ext_ids = np.where(exterior)[0]
    tree = cKDTree(head_pos[ext_ids])
    for jn in LANDMARK_JOINTS:
        if jn in names:
            p = joints["world"][names.index(jn), 3, :3]
            ids[jn] = int(ext_ids[tree.query(p)[1]])
    return ids


def nicp(T0, tris, target_V, target_T, lm_ids, lm_pts, exterior,
         stiffness=(100, 50, 25, 12, 6, 3, 1.5, 0.8, 0.4), iters=3, lm_weight=(10.0, 0.5),
         max_dist=(3.0, 0.6), normal_cos=0.5, p2p=0.1, target_sign=None, log=print):
    """Non-rigid ICP of template vertices T0 (MetaHuman space) onto the target surface."""
    n = len(T0)
    L = uniform_laplacian(n, tris)
    L3 = sp.kron(L, sp.eye(3)).tocsr()
    LtL = (L3.T @ L3).tocsr()
    LT0 = LtL @ T0.ravel()
    P, N = sample_surface(target_V, target_T, density=60.0)
    sign = orientation_sign(target_V, target_T) if target_sign is None else target_sign
    if sign:
        N = N * sign          # consistent winding: signed normals tell the upper lip from the lower lip
    tree = cKDTree(P)
    X = T0.copy()
    lm_ids = np.asarray(lm_ids)
    lm_pts = np.asarray(lm_pts)
    steps = len(stiffness)
    for si, alpha in enumerate(stiffness):
        f = si / max(1, steps - 1)
        wl = lm_weight[0] * (1 - f) + lm_weight[1] * f
        md = max_dist[0] * (1 - f) + max_dist[1] * f
        for it in range(iters):
            vn = vertex_normals(X, tris)
            d, k = tree.query(X)
            C, CN = P[k], N[k]
            # |cos|: works with inconsistently wound target meshes (scans, OBJ exports)
            cosn = np.einsum("ij,ij->i", vn, CN)
            ok = exterior & (d < md) & ((cosn if sign else np.abs(cosn)) > normal_cos)
            idx = np.where(ok)[0]
            # point-to-plane rows: n^T x = n^T c   (one row per matched vertex)
            rows = np.repeat(np.arange(len(idx)), 3)
            cols = (3 * idx[:, None] + np.arange(3)).ravel()
            A_pl = sp.coo_matrix((CN[idx].ravel(), (rows, cols)), shape=(len(idx), 3 * n)).tocsr()
            b_pl = np.einsum("ij,ij->i", CN[idx], C[idx])
            # point-to-point rows (small weight) and landmarks
            sel = sp.coo_matrix((np.ones(3 * len(idx)), (np.arange(3 * len(idx)), cols)), shape=(3 * len(idx), 3 * n)).tocsr()
            lcols = (3 * lm_ids[:, None] + np.arange(3)).ravel()
            S_lm = sp.coo_matrix((np.ones(len(lcols)), (np.arange(len(lcols)), lcols)), shape=(len(lcols), 3 * n)).tocsr()
            A = alpha * LtL + A_pl.T @ A_pl + p2p * (sel.T @ sel) + wl * (S_lm.T @ S_lm)
            b = alpha * LT0 + A_pl.T @ b_pl + p2p * (sel.T @ C[idx].ravel()) + wl * (S_lm.T @ lm_pts.ravel())
            A = A + sp.eye(3 * n) * 1e-8
            x, info = spla.cg(A, b, x0=X.ravel(), rtol=1e-7, maxiter=2000)
            X = x.reshape(n, 3)
        err = d[ok]
        log("  stiffness %6.2f: %5d matched, mean %.3f cm, 95%% %.3f cm, landmarks %.3f cm"
            % (alpha, ok.sum(), err.mean(), np.percentile(err, 95), np.linalg.norm(X[lm_ids] - lm_pts, axis=1).mean()))
    return X


def surface_distance(V, target_V, target_T, mask=None):
    P, _ = sample_surface(target_V, target_T, density=200.0)
    d, _ = cKDTree(P).query(V if mask is None else V[mask])
    return d
