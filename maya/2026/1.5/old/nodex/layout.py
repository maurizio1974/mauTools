"""Where nodes go. Pure Python, no Maya.

place(): a new node lands at the cursor or beside its upstream neighbour, in free
space, and never moves anything already on the board.
layered(): the Rearrange button -- columns by longest path from the sources, rows ordered
by the average position of their upstream nodes (a light Sugiyama).
wrap(): folds that layout into bands so it covers a view of a given aspect evenly instead
of one column thousands of pixels tall.
"""

GAP_X = 80
GAP_Y = 40
MARGIN = 24
TYPE_LABEL = 20   # the node type is printed above the node


def _overlaps(r, rects):
    x, y, w, h = r
    for (ox, oy, ow, oh) in rects:
        if (x < ox + ow + MARGIN and x + w + MARGIN > ox and
                y - TYPE_LABEL < oy + oh + MARGIN and y + h + MARGIN > oy - TYPE_LABEL):
            return True
    return False


def free_spot(x, y, w, h, rects, step=30, tries=80):
    """Nearest free position to (x, y): scan down, then shift right a column and retry."""
    for col in range(8):
        cx = x + col * (w + GAP_X)
        for i in range(tries):
            cy = y + i * step
            if not _overlaps((cx, cy, w, h), rects):
                return cx, cy
    return x, y


def place(size, rects, cursor=None, upstream=None, downstream=None, fallback=None):
    """Position for one new node of `size` (w, h).

    upstream / downstream: rects (x, y, w, h) of neighbours already on the board.
    """
    w, h = size
    if cursor is not None:
        return free_spot(cursor[0] - w / 2.0, cursor[1] - 14, w, h, rects)
    if upstream:
        ux, uy, uw, uh = max(upstream, key=lambda r: r[0] + r[2])
        return free_spot(ux + uw + GAP_X, uy, w, h, rects)
    if downstream:
        dx, dy, dw, dh = min(downstream, key=lambda r: r[0])
        return free_spot(dx - w - GAP_X, dy, w, h, rects)
    if fallback is not None:
        return free_spot(fallback[0], fallback[1], w, h, rects)
    if rects:
        x1 = max(r[0] + r[2] for r in rects)
        y0 = min(r[1] for r in rects)
        return free_spot(x1 + GAP_X, y0, w, h, rects)
    return 60.0, 60.0


def columns(ids, edges):
    """Column index per id: longest path from a source, cycle-safe."""
    ids = list(ids)
    idset = set(ids)
    ups = dict((i, []) for i in ids)
    for a, b in edges:
        if a in idset and b in idset and a != b:
            ups[b].append(a)
    # Iterative depth-first search: a chain of a thousand nodes would overflow recursion.
    # An edge back into the current path (a cycle) counts as coming from column 0.
    col = {}
    visiting = set()
    best = {}
    for root in ids:
        if root in col:
            continue
        visiting.add(root)
        best[root] = 0
        stack = [(root, 0)]
        while stack:
            i, k = stack[-1]
            if k < len(ups[i]):
                stack[-1] = (i, k + 1)
                u = ups[i][k]
                if u in col:
                    best[i] = max(best[i], col[u] + 1)
                elif u in visiting:
                    best[i] = max(best[i], 1)
                else:
                    visiting.add(u)
                    best[u] = 0
                    stack.append((u, 0))
            else:
                stack.pop()
                visiting.discard(i)
                col[i] = best[i]
                if stack:
                    parent = stack[-1][0]
                    best[parent] = max(best[parent], col[i] + 1)
    return col, ups


def layered(ids, sizes, edges, origin=(60.0, 60.0), order_hint=None):
    """Positions {id: (x, y)} for a left-to-right layered layout."""
    col, ups = columns(ids, edges)
    cols = {}
    hint = order_hint or {}
    for i in ids:
        cols.setdefault(col[i], []).append(i)
    pos = {}
    x = origin[0]
    for c in sorted(cols):
        members = cols[c]
        if c == 0:
            members.sort(key=lambda i: hint.get(i, 0))
        else:
            def bary(i):
                ys = [pos[u][1] for u in ups[i] if u in pos]
                return sum(ys) / len(ys) if ys else hint.get(i, 0)
            members.sort(key=bary)
        y = origin[1]
        width = 0
        for i in members:
            w, h = sizes[i]
            pos[i] = (x, y)
            y += h + GAP_Y + TYPE_LABEL
            width = max(width, w)
        x += width + GAP_X
    return pos


def _bbox(pos, sizes):
    x0 = min(pos[i][0] for i in pos)
    y0 = min(pos[i][1] for i in pos)
    x1 = max(pos[i][0] + sizes[i][0] for i in pos)
    y1 = max(pos[i][1] + sizes[i][1] for i in pos)
    return x0, y0, x1, y1


def wrap(pos, sizes, aspect=1.6, slack=1.5, min_side=2400):
    """Fold a layout far taller or wider than `aspect` (width / height) into bands.

    Too tall: cut it into horizontal slices and set them side by side, left to right.
    Too wide: cut it into vertical slices and stack them, top to bottom. A slice keeps
    every column's relative order, so nodes that were neighbours stay neighbours.
    A layout whose long side is under `min_side` fits a view anyway and is left alone.
    """
    if len(pos) < 2:
        return dict(pos)
    x0, y0, x1, y1 = _bbox(pos, sizes)
    w, h = max(1.0, x1 - x0), max(1.0, y1 - y0)
    out = dict(pos)
    if max(w, h) < min_side:
        return out
    if h * aspect > w * slack:
        n = max(2, int(round((h * aspect / w) ** 0.5)))
        band = h / n
        which = dict((i, min(n - 1, int((pos[i][1] - y0 + sizes[i][1] / 2.0) / band))) for i in pos)
        tops = {}
        for i, b in which.items():
            tops[b] = min(tops.get(b, pos[i][1]), pos[i][1])
        for i, b in which.items():
            out[i] = (pos[i][0] + b * (w + GAP_X * 2), pos[i][1] - tops[b] + y0)
    elif w > h * aspect * slack:
        n = max(2, int(round((w / (h * aspect)) ** 0.5)))
        band = w / n
        which = dict((i, min(n - 1, int((pos[i][0] - x0) / band))) for i in pos)
        lefts = {}
        for i, b in which.items():
            lefts[b] = min(lefts.get(b, pos[i][0]), pos[i][0])
        for i, b in which.items():
            out[i] = (pos[i][0] - lefts[b] + x0, pos[i][1] + b * (h + GAP_Y * 3 + TYPE_LABEL))
    return out


# ---------------------------------------------------------------------------- arrange variants
# Blender references: Node Arrange (layered), Node Wrangler "Align Nodes" (row / column with
# even gaps), "Straighten links" (snap each node to its main upstream socket), and a plain grid.

def align_row(ids, sizes, pos):
    """Selection in one row at its mean top, left-to-right order kept, even gaps."""
    ids = sorted(ids, key=lambda i: pos[i][0])
    y = sum(pos[i][1] for i in ids) / float(len(ids))
    x = pos[ids[0]][0]
    out = {}
    for i in ids:
        out[i] = (x, y)
        x += sizes[i][0] + GAP_X
    return out


def align_column(ids, sizes, pos):
    """Selection in one column at its leftmost edge, top-to-bottom order kept, even gaps."""
    ids = sorted(ids, key=lambda i: pos[i][1])
    x = min(pos[i][0] for i in ids)
    y = pos[ids[0]][1]
    out = {}
    for i in ids:
        out[i] = (x, y)
        y += sizes[i][1] + GAP_Y + TYPE_LABEL
    return out


def grid(ids, sizes, key, origin, aspect=1.6):
    """Nodes sorted by `key` (category, type, name) in rows filling a view of `aspect`."""
    ids = sorted(ids, key=key)
    if not ids:
        return {}
    cw = max(sizes[i][0] for i in ids) + GAP_X / 2.0
    ch = max(sizes[i][1] for i in ids) + GAP_Y / 2.0 + TYPE_LABEL
    n = len(ids)
    cols = max(1, int(round((n * aspect * ch / cw) ** 0.5)))
    out = {}
    for k, i in enumerate(ids):
        out[i] = (origin[0] + (k % cols) * cw, origin[1] + (k // cols) * ch)
    return out


def straighten(ids, sizes, pos, links):
    """Keep every node's x; move it vertically so its main input wire runs straight.

    links: [(src, src_y, dst, dst_y)] wire ends as offsets from the node tops. Nodes are
    visited left to right; a node follows the upstream wire whose source is placed nearest
    above it in that order, then nodes sharing a column are pushed apart without overlap."""
    idset = set(ids)
    main = {}
    for s, sy, d, dy in links:
        if s in idset and d in idset and s != d and pos[s][0] < pos[d][0]:
            if d not in main or pos[s][0] > pos[main[d][0]][0]:
                main[d] = (s, sy, dy)
    out = dict((i, pos[i]) for i in ids)
    for i in sorted(ids, key=lambda i: pos[i][0]):
        if i in main:
            s, sy, dy = main[i]
            out[i] = (pos[i][0], out[s][1] + sy - dy)
    # resolve overlaps: nodes whose x ranges overlap form a column, stacked in y order
    order = sorted(ids, key=lambda i: (out[i][1], out[i][0]))
    placed = []
    for i in order:
        x, y = out[i]
        w, h = sizes[i]
        moved = True
        while moved:
            moved = False
            for j in placed:
                jx, jy = out[j]
                jw, jh = sizes[j]
                if x < jx + jw + MARGIN and x + w + MARGIN > jx and \
                        y < jy + jh + GAP_Y + TYPE_LABEL and y + h + GAP_Y > jy - TYPE_LABEL:
                    y = jy + jh + GAP_Y + TYPE_LABEL
                    moved = True
        out[i] = (x, y)
        placed.append(i)
    return out
