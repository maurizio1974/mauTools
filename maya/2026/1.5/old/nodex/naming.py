"""Name rules for bulk connection (pure Python, no Maya).

One wire dragged between two selected nodes teaches a rename: the part of the source name
that differs from the destination name, e.g.

    skin_spine1 -> drv_spine1      rule "skin" -> "drv"   (common suffix "_spine1")
    L_arm_jnt   -> L_arm_ctrl      rule "jnt"  -> "ctrl"  (common prefix "L_arm_")
    arm1        -> arm1_ctrl       rule ""     -> "_ctrl" (insert before the common suffix)

and every other selected node whose renamed name is also selected gets the same connection.
"""


def short(name):
    """Leaf name without DAG path; the namespace stays (rigA:hand -> rigB:hand is a rule too)."""
    return name.rsplit("|", 1)[-1]


def rule(a, b):
    """-> (prefix, a_mid, b_mid, suffix) for names a and b, or None when they are equal."""
    a, b = short(a), short(b)
    if a == b:
        return None
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    q = 0
    while q < min(len(a), len(b)) - p and a[-1 - q] == b[-1 - q]:
        q += 1
    pre, suf = a[:p], a[len(a) - q:] if q else ""
    return pre, a[p:len(a) - q], b[p:len(b) - q], suf


def apply(x, r):
    """The partner name of `x` under rule r, or None when x does not follow the pattern."""
    if r is None:
        return None
    x = short(x)
    pre, am, bm, suf = r
    if am:
        # the varying part between the same neighbours as in the taught pair first:
        # arm_L_jnt -> arm_R_jnt maps Leg_L_jnt to Leg_R_jnt, not to Reg_L_jnt
        left, right = pre[-1:], suf[:1]
        i = x.find(left + am + right)
        if i >= 0:
            i += len(left)
        else:
            i = x.find(am)
        if i < 0:
            return None
        return x[:i] + bm + x[i + len(am):]
    # pure insertion: put b_mid before the common suffix (or at the end)
    if suf and x.endswith(suf):
        return x[:len(x) - len(suf)] + bm + suf
    if not suf:
        return x + bm
    return None


def pairs(a, b, selected):
    """[(x, y)] other selected names paired by the rule taught by a -> b (short names compared,
    full names returned). Each node is used once; a and b themselves are left out."""
    r = rule(a, b)
    by_short = {}
    for n in selected:
        by_short.setdefault(short(n), []).append(n)
    out, used = [], {a, b}
    for x in selected:
        if x in used:
            continue
        y_short = apply(x, r)
        if not y_short or y_short == short(x):
            continue
        ys = [y for y in by_short.get(y_short, []) if y not in used]
        if len(ys) != 1:
            continue
        out.append((x, ys[0]))
        used.update((x, ys[0]))
    return out
