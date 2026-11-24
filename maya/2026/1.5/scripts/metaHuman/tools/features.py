"""
Find facial feature points on a head mesh the same way on any topology, from front depth images:
  eyes   the eye opening (a hole, or a pocket behind the lids): inner / outer corner, upper / lower lid
  mouth  the crevice where the lips meet: corners, upper / lower lip at the middle
  nose   tip (most forward point near the midline)
Used to give the MetaHuman template and the user's mesh landmarks with exactly the same meaning.
"""
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

import render as R


def _depth(V, T, center, extent, size):
    _, cam = R.render([(V, T, (1, 1, 1))], size, yaw=0, center=center, extent=extent, return_camera=True)
    return cam


def _pix_to_point(cam, x, y):
    return R.unproject(cam, x, y)


def eye_points(V, T, center, extent=2.6, size=700, depth=0.45):
    """center: rough eye centre. Returns dict inner/outer/upper/lower 3D points on the lid rim
    (inner = towards the nose)."""
    cam = _depth(V, T, center, extent, size)
    z = cam["zbuf"].copy()
    ci = size // 2
    f = np.isfinite(z)
    zf = np.where(f, z, np.nanmin(np.where(f, z, np.nan)) - 1.0)
    # depression depth: how far each pixel lies below the surface with its dents filled (grey closing)
    dent = ndimage.grey_closing(zf, size=(size // 3, size // 3)) - zf
    q = size // 6
    thr = depth * dent[ci - q:ci + q, ci - q:ci + q].max()     # relative: same meaning on any mesh
    deep = dent > thr
    lab, n = ndimage.label(deep)
    # component nearest the image centre (the eye opening)
    best, bd = 0, 1e9
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 50:
            continue
        d = np.hypot(xs.mean() - ci, ys.mean() - ci)
        touches = xs.min() == 0 or ys.min() == 0 or xs.max() == size - 1 or ys.max() == size - 1
        if not touches and d < bd:
            best, bd = k, d
    ys, xs = np.nonzero(lab == best)
    side = 1.0 if center[0] > 0 else -1.0      # +x = character's left
    i_in = np.argmin(xs * side)
    i_out = np.argmax(xs * side)
    mid = (xs.min() + xs.max()) / 2
    band = np.abs(xs - mid) < max(3, (xs.max() - xs.min()) * 0.04)
    i_up = np.where(band)[0][np.argmin(ys[band])]
    i_lo = np.where(band)[0][np.argmax(ys[band])]
    cx, cy = xs.mean(), ys.mean()
    out = {}
    for name, i in (("inner", i_in), ("outer", i_out), ("upper", i_up), ("lower", i_lo)):
        d = np.array([xs[i] - cx, ys[i] - cy], float)
        d = d / (np.linalg.norm(d) + 1e-9) * 3.0          # 3 px outside the opening = on the lid rim
        out[name] = _pix_to_point(cam, xs[i] + d[0], ys[i] + d[1])
    return out, (lab == best)


def mouth_points(V, T, center, extent=3.5, size=700, rel=0.3):
    """center: rough mouth centre. Corners + upper/lower lip contact points at the middle.
    The lip line is a narrow horizontal groove: depth below a vertically-closed surface."""
    cam = _depth(V, T, center, extent, size)
    z = cam["zbuf"]
    f = np.isfinite(z)
    zf = np.where(f, z, np.nanmin(np.where(f, z, np.nan)) - 1.0)
    k = size // 20
    groove = ndimage.grey_closing(zf, size=(k, 1)) - zf
    ci = size // 2
    q = size // 6
    crev = f & (groove > rel * groove[ci - q:ci + q, ci - q:ci + q].max())
    lab, n = ndimage.label(ndimage.binary_closing(crev, structure=np.ones((3, 9)), iterations=2))
    best, bd = 0, -1
    for kk in range(1, n + 1):
        ys, xs = np.nonzero(lab == kk)
        if len(xs) < 30 or abs(ys.mean() - ci) > size * 0.2 or xs.min() > ci or xs.max() < ci:
            continue
        w = xs.max() - xs.min()
        if w > bd:
            best, bd = kk, w
    ys, xs = np.nonzero(lab == best)
    iL = np.argmax(xs)        # image right = +X = character's left
    iR = np.argmin(xs)
    mid = int(round((xs.min() + xs.max()) / 2))
    col = ys[np.abs(xs - mid) < 2]
    top, bot = col.min(), col.max()
    return {"left": _pix_to_point(cam, xs[iL] - 2, ys[iL]), "right": _pix_to_point(cam, xs[iR] + 2, ys[iR]),
            "upper": _pix_to_point(cam, mid, top - 2), "lower": _pix_to_point(cam, mid, bot + 2)}, (lab == best)


def nose_tip(V, center, radius=3.0):
    sel = np.where((np.abs(V[:, 0] - center[0]) < 1.0) & (np.linalg.norm(V[:, [1, 2]] - center[[1, 2]], axis=1) < radius))[0]
    return V[sel[np.argmax(V[sel, 2])]]


def feature_landmarks(V, T, eyeL, eyeR, mouth, nose):
    """Rough centres in -> named 3D feature points (names reuse the facial joint names)."""
    pts = {}
    for side, c in (("L", eyeL), ("R", eyeR)):
        e, _ = eye_points(V, T, c)
        pts["FACIAL_%s_EyeCornerInner" % side] = e["inner"]
        pts["FACIAL_%s_EyeCornerOuter" % side] = e["outer"]
        pts["FACIAL_%s_EyelidUpperA" % side] = e["upper"]
        pts["FACIAL_%s_EyelidLowerA" % side] = e["lower"]
    m, _ = mouth_points(V, T, mouth)
    pts["FACIAL_L_LipCorner"] = m["left"]
    pts["FACIAL_R_LipCorner"] = m["right"]
    pts["FACIAL_C_LipUpper"] = m["upper"]
    pts["FACIAL_C_LipLower"] = m["lower"]
    pts["FACIAL_C_NoseTip"] = nose_tip(V, nose)
    return {k: v for k, v in pts.items() if v is not None}


def snap(V, pts):
    tree = cKDTree(V)
    return {k: int(tree.query(p)[1]) for k, p in pts.items()}
