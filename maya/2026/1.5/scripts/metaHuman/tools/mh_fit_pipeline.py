"""
Put a MetaHuman face rig on a head or full-body mesh of any topology. Runs outside Maya
(Python 3.11 + numpy + scipy, and the OpenRigLogic `dna` / `riglogic` modules in ../lib/linux/py311).

    python3.11 mh_fit_pipeline.py character.obj out_dir [--profile my_topology.json]

The mesh must be Y-up, facing +Z (Maya default), in centimetres. The first run finds 13 landmarks by
itself (eye corners and lids, mouth corners and lips, nose tip) and saves them as vertex ids in a
topology profile; characters with the same topology then reuse that profile.
Writes, in out_dir:
  <name>_fitted.dna          LOD 0 DNA in YOUR mesh's space and size (Rig Logic scaled to the head)
  <name>_usermesh.npz        your mesh + transferred skin weights and blendshapes, for the Maya build
  <name>_topology.json       landmark vertex ids (reuse with --profile)
  <name>_preview.png         expressions evaluated with OpenRigLogic on your mesh
"""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "lib", "linux", "py311")]
import numpy as np
from scipy.spatial import cKDTree
import mh_dna_geo as G, fit as F, transfer as TR, user_transfer as U, render as R, features as FT

LANDMARKS = ["FACIAL_L_EyeCornerInner", "FACIAL_L_EyeCornerOuter", "FACIAL_L_EyelidUpperA", "FACIAL_L_EyelidLowerA",
             "FACIAL_R_EyeCornerInner", "FACIAL_R_EyeCornerOuter", "FACIAL_R_EyelidUpperA", "FACIAL_R_EyelidLowerA",
             "FACIAL_L_LipCorner", "FACIAL_R_LipCorner", "FACIAL_C_LipUpper", "FACIAL_C_LipLower", "FACIAL_C_NoseTip"]
BODY_JOINT = "spine_04"


def template_exterior(base, meshes):
    """MetaHuman head vertices visible from outside WITH the eyeballs in place (cached next to the DNA)."""
    cache = os.path.splitext(base)[0] + "_exterior.npy"
    if os.path.isfile(cache):
        return np.load(cache)
    head = meshes[0]
    parts = [head] + [m for m in meshes if m["name"].startswith(("eyeLeft", "eyeRight"))]
    V = np.concatenate([p["pos"] for p in parts])
    Ts, off = [], 0
    for p in parts:
        Ts.append(G.triangles(p) + off)
        off += len(p["pos"])
    ext = F.visible_vertices(V, np.concatenate(Ts))[:len(head["pos"])]
    np.save(cache, ext)
    return ext


def template_features(meshes, joints, tris, ext, base=None):
    """Rough feature centres + the 13 feature points on the MetaHuman head (cached next to the DNA)."""
    P, J, nm = meshes[0]["pos"], joints["world"], joints["names"]
    cache = os.path.splitext(base)[0] + "_features.json" if base else None
    if cache and os.path.isfile(cache):
        d = json.load(open(cache))
        return ({k: np.array(v) for k, v in d["centres"].items()}, {k: np.array(v) for k, v in d["points"].items()})
    tpl = F.template_landmarks(P, tris, joints, ext)
    c = {"eyeL": J[nm.index("FACIAL_L_Eye"), 3, :3] + np.array([0, 0, 1.2]),
         "eyeR": J[nm.index("FACIAL_R_Eye"), 3, :3] + np.array([0, 0, 1.2]),
         "mouth": (P[tpl["FACIAL_L_LipCorner"]] + P[tpl["FACIAL_R_LipCorner"]]) / 2,
         "nose": P[tpl["FACIAL_C_NoseTip"]]}
    pts = FT.feature_landmarks(P, tris, c["eyeL"], c["eyeR"], c["mouth"], c["nose"])
    if cache:
        try:
            json.dump({"centres": {k: list(map(float, v)) for k, v in c.items()},
                       "points": {k: list(map(float, v)) for k, v in pts.items()}}, open(cache, "w"))
        except OSError:
            pass
    return c, pts


def coarse_align(V, P, ext, nose_mh, log=print):
    """Scale + translation (no rotation) MetaHuman = s * yours + t, from crown / nose tip, then ICP on the head."""
    top_u = V[V[:, 1].argmax()]
    face = (V[:, 1] > top_u[1] - 30) & (np.abs(V[:, 0] - top_u[0]) < 3)
    nose_u = V[face][V[face][:, 2].argmax()]
    top_mh = P[P[:, 1].argmax()]
    s = (top_mh[1] - nose_mh[1]) / (top_u[1] - nose_u[1])
    t = nose_mh - s * nose_u
    src = V[V[:, 1] > nose_u[1] - 14]
    tgt = P[ext & (P[:, 1] > nose_mh[1] - 12)]
    tree = cKDTree(tgt)
    for _ in range(40):
        d, k = tree.query(s * src + t)
        ok = d < np.percentile(d, 80)
        A, B = src[ok], tgt[k[ok]]
        ma, mb = A.mean(0), B.mean(0)
        s = ((A - ma) * (B - mb)).sum() / ((A - ma) ** 2).sum()
        t = mb - s * ma
    log("  rough alignment: scale %.4f (MetaHuman / yours), residual %.3f cm" % (s, d[ok].mean()))
    return s, t


# ----------------------------------------------------------------------------- stages
def prepare(user, base=None, log=print):
    """user: mesh dict (pos, counts, connects, uv, uv_ids) in its own space. Reads the base DNA and
    aligns roughly (scale + translation). Returns the context the other stages use."""
    base = base or os.path.join(HERE, "..", "data", "Ada_mh4.dna")
    reader, meshes, joints = G.read_lod(base, 0)
    head, tris = meshes[0], G.triangles(meshes[0])
    ext = template_exterior(base, meshes)
    V = user["pos"]
    ut = U.triangles(user)
    log("   your mesh: %d vertices, %d faces" % (len(V), len(user["counts"])))
    c_mh, f_mh = template_features(meshes, joints, tris, ext, base)
    ext_ids = np.where(ext)[0]
    tpl_ids = {k: int(ext_ids[v]) for k, v in FT.snap(head["pos"][ext], f_mh).items()}
    s, t = coarse_align(V, head["pos"], ext, f_mh["FACIAL_C_NoseTip"], log=log)
    return {"base": base, "meshes": meshes, "joints": joints, "head": head, "tris": tris, "ext": ext,
            "user": user, "V": V, "ut": ut, "c_mh": c_mh, "f_mh": f_mh, "tpl_ids": tpl_ids, "s": s, "t": t}


def guess_landmarks(ctx):
    """Template landmark positions carried over by the rough alignment, snapped to your vertices.
    A starting point for placing landmarks by hand."""
    s, t, V = ctx["s"], ctx["t"], ctx["V"]
    tree = cKDTree(V)
    P = ctx["head"]["pos"]
    return {n: V[tree.query((P[ctx["tpl_ids"][n]] - t) / s)[1]] for n in LANDMARKS if n in ctx["tpl_ids"]}


def detect_landmarks(ctx, log=print):
    """The 13 landmarks found on your mesh from depth images. A feature that can't be found falls
    back to the rough guess; returns (landmarks, names that are only guesses)."""
    s, t, V, ut = ctx["s"], ctx["t"], ctx["V"], ctx["ut"]
    c = {k: (v - t) / s for k, v in ctx["c_mh"].items()}
    pts = {}
    for side, key in (("L", "eyeL"), ("R", "eyeR")):
        try:
            e, _ = FT.eye_points(V, ut, c[key], extent=2.6 / s)
            for part, nm in (("inner", "EyeCornerInner"), ("outer", "EyeCornerOuter"), ("upper", "EyelidUpperA"),
                             ("lower", "EyelidLowerA")):
                if e[part] is not None:
                    pts["FACIAL_%s_%s" % (side, nm)] = e[part]
        except Exception as ex:
            log("   %s eye not found automatically (%s)" % (side, ex))
    try:
        m, _ = FT.mouth_points(V, ut, c["mouth"], extent=3.5 / s)
        for part, nm in (("left", "FACIAL_L_LipCorner"), ("right", "FACIAL_R_LipCorner"), ("upper", "FACIAL_C_LipUpper"),
                         ("lower", "FACIAL_C_LipLower")):
            if m[part] is not None:
                pts[nm] = m[part]
    except Exception as ex:
        log("   mouth not found automatically (%s)" % ex)
    try:
        pts["FACIAL_C_NoseTip"] = FT.nose_tip(V, c["nose"], radius=3.0 / s)
    except Exception as ex:
        log("   nose tip not found automatically (%s)" % ex)
    guess = guess_landmarks(ctx)
    guessed = [n for n in guess if n not in pts]
    for n in guessed:
        pts[n] = guess[n]
    return pts, guessed


def landmarks_from_profile(ctx, profile):
    prof = json.load(open(profile))
    if prof.get("vertex_count") != len(ctx["V"]):
        raise RuntimeError("profile is for %s vertices, this mesh has %d" % (prof.get("vertex_count"), len(ctx["V"])))
    return {k: ctx["V"][i] for k, i in prof["landmarks"].items()}


def save_profile(ctx, lm_user, path):
    names = [n for n in LANDMARKS if n in lm_user]
    json.dump({"vertex_count": int(len(ctx["V"])), "landmarks": FT.snap(ctx["V"], {n: lm_user[n] for n in names}),
               "note": "landmark vertex ids for this topology (mh_fit_pipeline --profile)"}, open(path, "w"), indent=1)
    return path


def fit(ctx, lm_user, log=print):
    """Wrap the MetaHuman head onto your surface. Returns its vertices in MetaHuman space;
    to_user(ctx, X) gives them in yours."""
    s, t, head, ut = ctx["s"], ctx["t"], ctx["head"], ctx["ut"]
    names = [n for n in LANDMARKS if n in lm_user and n in ctx["tpl_ids"]]
    if len(names) < 6:
        raise RuntimeError("only %d landmarks: at least 6 are needed" % len(names))
    Vm = s * ctx["V"] + t                                  # your mesh in MetaHuman space
    lo, hi = head["pos"].min(0) - 2.0, head["pos"].max(0) + 2.0
    keep = np.all((Vm[ut] >= lo) & (Vm[ut] <= hi), axis=(1, 2))   # only the head / neck region of your mesh
    ids = np.array([ctx["tpl_ids"][n] for n in names])
    lm_m = np.array([s * np.asarray(lm_user[n], float) + t for n in names])
    X = F.nicp(head["pos"], ctx["tris"], Vm, ut[keep], ids, lm_m, ctx["ext"], log=lambda m: log("  " + m))
    d = F.surface_distance(X, Vm, ut[keep], ctx["ext"])
    log("   fitted head to your surface: mean %.3f cm, 95%% %.3f cm (MetaHuman scale)" % (d.mean(), np.percentile(d, 95)))
    ctx["fit_error"] = (float(d.mean()), float(np.percentile(d, 95)))
    return X


def to_user(ctx, P):
    return (np.asarray(P) - ctx["t"]) / ctx["s"]


def to_metahuman(ctx, P):
    return ctx["s"] * np.asarray(P) + ctx["t"]


def finish(ctx, X, out, name, previews=True, log=print):
    """From fitted head vertices X (MetaHuman space) to <name>_fitted.dna + <name>_usermesh.npz."""
    os.makedirs(out, exist_ok=True)
    s, t, head, tris, meshes, joints, user = (ctx["s"], ctx["t"], ctx["head"], ctx["tris"], ctx["meshes"],
                                              ctx["joints"], ctx["user"])
    Vm = s * ctx["V"] + t
    lo, hi = head["pos"].min(0) - 2.0, head["pos"].max(0) + 2.0
    log("4/7 eyes, teeth, lashes and joints...")
    new_pos, new_j, info = TR.refit_rig(meshes, joints, 0, X, ctx["ext"], log=log)
    new_pos = {k: to_user(ctx, v) for k, v in new_pos.items()}
    jt = TR.local_translations(joints, to_user(ctx, new_j))
    log("5/7 writing the DNA (your space, Rig Logic x%.4f)..." % (1 / s))
    dna_out = os.path.join(out, name + "_fitted.dna")
    TR.write_dna(ctx["base"], dna_out, new_pos, jt, behaviour_scale=1.0 / s)
    log("6/7 skin weights + blendshapes onto your mesh...")
    tr = U.transfer({"pos": Vm, "counts": user["counts"], "connects": user["connects"]}, head, X, tris,
                    log=lambda m: log("  " + m))
    # body = outside the MetaHuman head/neck region; the mouth bag and eye pockets are inside it and follow
    far = ~np.all((Vm >= lo) & (Vm <= hi), axis=1)
    body_j = joints["names"].index(BODY_JOINT)
    for v in np.where(far)[0]:
        tr["skin_joints"][v] = np.array([body_j])
        tr["skin_weights"][v] = np.array([1.0])
    for tg in tr["targets"]:
        tg["delta"] = tg["delta"] / s                       # deltas to your size
        k = ~far[tg["idx"]]
        tg["idx"], tg["delta"] = tg["idx"][k], tg["delta"][k]
    tr["targets"] = [tg for tg in tr["targets"] if len(tg["idx"])]
    log("   %d vertices follow the face, %d stay on %s" % ((~far).sum(), far.sum(), BODY_JOINT))
    npz = os.path.join(out, name + "_usermesh.npz")
    U.save_npz(npz, name, user, tr)
    if previews:
        log("7/7 previews...")
        preview(dna_out, npz, os.path.join(out, name + "_preview.png"))
    return dna_out, npz


def clean_name(name):
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return "m_" + name if name[0].isdigit() else name


def run(obj, out, base=None, profile=None, name=None, previews=True, log=print):
    os.makedirs(out, exist_ok=True)
    name = clean_name(name or os.path.splitext(os.path.basename(obj))[0])
    t0 = time.time()
    log("1/7 reading %s and the base DNA..." % os.path.basename(obj))
    ctx = prepare(U.read_obj(obj), base, log=log)
    log("2/7 landmarks...")
    if profile and os.path.isfile(profile):
        lm_user = landmarks_from_profile(ctx, profile)
        log("   from profile %s" % os.path.basename(profile))
    else:
        lm_user, guessed = detect_landmarks(ctx, log=log)
        log("   found automatically: %d%s" % (len(lm_user) - len(guessed),
                                            (", only guessed: %s" % ", ".join(guessed)) if guessed else ""))
    save_profile(ctx, lm_user, os.path.join(out, name + "_topology.json"))
    log("3/7 fitting the MetaHuman head to your surface...")
    X = fit(ctx, lm_user, log=log)
    dna_out, npz = finish(ctx, X, out, name, previews=previews, log=log)
    log("done in %.0fs -> %s" % (time.time() - t0, out))
    return dna_out, npz


POSES = [("neutral", {}), ("jaw open", {"CTRL_C_jaw.ty": 1.0}),
         ("smile", {"CTRL_L_mouth_cornerPull.ty": 1.0, "CTRL_R_mouth_cornerPull.ty": 1.0}),
         ("blink + brows", {"CTRL_L_eye_blink.ty": 1, "CTRL_R_eye_blink.ty": 1, "CTRL_L_brow_raiseIn.ty": 1,
                            "CTRL_R_brow_raiseIn.ty": 1, "CTRL_L_brow_raiseOut.ty": 1, "CTRL_R_brow_raiseOut.ty": 1}),
         ("pucker + look", {"CTRL_L_mouth_purseU.ty": 1, "CTRL_R_mouth_purseU.ty": 1, "CTRL_L_mouth_purseD.ty": 1,
                            "CTRL_R_mouth_purseD.ty": 1, "CTRL_L_eye.tx": 0.7, "CTRL_R_eye.tx": 0.7})]


def preview(dna_path, npz, png, size=330):
    import rig_eval as E
    r, meshes, joints = G.read_lod(dna_path, 0)
    rig = E.Rig(r, meshes, joints)
    z = np.load(npz, allow_pickle=True)
    um = {"pos": z["pos"], "targets": list(z["targets"]), "skin_joints": list(z["skin_joints"]),
          "skin_weights": list(z["skin_weights"])}
    ut = U.triangles({"counts": z["counts"], "connects": z["connects"]})
    head_mask = np.zeros(len(um["pos"]), bool)
    hp = meshes[0]["pos"]
    lo, hi = hp.min(0) - 1, hp.max(0) + 1
    head_mask = np.all((um["pos"] >= lo) & (um["pos"] <= hi), axis=1)
    ut = ut[head_mask[ut].all(1)]
    sk = E.skin_arrays(um)
    others = [m for m in meshes if m["name"].split("_")[0] in ("teeth", "eyeLeft", "eyeRight", "eyelashes")]
    osk = {m["name"]: E.skin_arrays(m) for m in others}
    eyes = joints["world"][[joints["names"].index("FACIAL_L_Eye"), joints["names"].index("FACIAL_R_Eye")], 3, :3]
    center = eyes.mean(0) + np.array([0, -(hp[:, 1].max() - eyes[0, 1]) * 0.35, 0])
    ext = (hp[:, 1].max() - eyes[0, 1]) * 1.25
    rows = []
    for yaw in (0, 35):
        imgs = []
        for _, g in POSES:
            world, bs, am = rig.evaluate(g)
            ml = [(E.deform_fast(rig, um, world, bs, skin=sk), ut, (0.82, 0.72, 0.62))]
            for m in others:
                b = m["name"].split("_")[0]
                ml.append((E.deform_fast(rig, m, world, bs, skin=osk[m["name"]]), G.triangles(m),
                           {"teeth": (1, 1, .92), "eyelashes": (.15, .1, .08)}.get(b, (.92, .92, 1))))
            imgs.append(R.render(ml, size, yaw=yaw, center=center, extent=ext))
        rows.append(np.concatenate(imgs, 1))
    R.save(np.concatenate(rows, 0), png)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("obj"); ap.add_argument("out")
    ap.add_argument("--base", default=None, help="base DNA (default: data/Ada_mh4.dna)")
    ap.add_argument("--profile", default=None, help="topology profile json from a previous run")
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args()
    run(a.obj, a.out, a.base, a.profile, previews=not a.no_preview)
