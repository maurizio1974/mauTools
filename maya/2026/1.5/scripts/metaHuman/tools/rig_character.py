"""
One command: OBJ -> fitted DNA -> rigged Maya scene. Run with Maya 2026's mayapy:

    mayapy rig_character.py character.obj out_dir [--profile my_topology.json] [--name myChar]

Needs scipy in mayapy once:   mayapy -m pip install --user scipy pillow
Writes out_dir/<name>_rig.ma next to the DNA, the .npz, the topology profile and the preview.
"""
import argparse, os, sys, traceback
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "lib", "linux", "py311")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj"); ap.add_argument("out")
    ap.add_argument("--profile", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--skip-fit", action="store_true", help="reuse <name>_fitted.dna / _usermesh.npz in out")
    a = ap.parse_args()
    import mh_fit_pipeline as P
    name = a.name or os.path.splitext(os.path.basename(a.obj))[0]
    if a.skip_fit:
        dna_path = os.path.join(a.out, name + "_fitted.dna")
        npz = os.path.join(a.out, name + "_usermesh.npz")
    else:
        dna_path, npz = P.run(a.obj, a.out, a.base, a.profile, name=name)
    print("building the Maya scene...")
    import maya.standalone
    maya.standalone.initialize(name="python")
    from maya import cmds
    import mh_face_build as B
    try:
        B.build(dna_path, user_mesh=npz)
    except Exception:
        traceback.print_exc()
        print("build stopped; the scene so far is saved for inspection")
    ma = os.path.join(a.out, os.path.splitext(os.path.basename(dna_path))[0].replace("_fitted", "") + "_rig.ma")
    cmds.file(rename=ma)
    cmds.file(save=True, type="mayaAscii", force=True)
    print("saved", ma)
    maya.standalone.uninitialize()


if __name__ == "__main__":
    main()
