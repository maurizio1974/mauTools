"""Remove Epic's MayaUERBFPlugin nodes (neck corrective RBF) from a Maya ASCII GUI file, so it opens
without the plug-in. Usage: strip_rbf_from_gui.py in.ma out.ma"""
import re, sys

def strip(src, dst):
    lines = open(src, encoding="utf-8", errors="surrogateescape").read().split("\n")
    bad = set()
    for l in lines:
        m = re.match(r'createNode (UERBFSolverNode|UEPoseBlenderNode) -n "([^"]+)"', l)
        if m:
            bad.add(m.group(2))
    out, skipping, removed = [], False, {"nodes": 0, "lines": 0, "connections": 0}
    for l in lines:
        if skipping:
            if l.startswith("\t") or l.startswith("        "):
                removed["lines"] += 1
                continue
            skipping = False
        if re.match(r'createNode (UERBFSolverNode|UEPoseBlenderNode) ', l):
            skipping, removed["nodes"] = True, removed["nodes"] + 1
            continue
        if l.startswith("requires") and "MayaUERBFPlugin" in l:
            continue
        if l.startswith("connectAttr"):
            plugs = re.findall(r'"([^"]+)"', l)
            if any(p.split(".")[0] in bad for p in plugs[:2]):
                removed["connections"] += 1
                continue
        out.append(l)
    text = "\n".join(out)
    left = [b for b in bad if ('"%s' % b) in text or (" %s." % b) in text]
    open(dst, "w", encoding="utf-8", errors="surrogateescape").write(text)
    return removed, left

if __name__ == "__main__":
    print(strip(sys.argv[1], sys.argv[2]))
