"""Node type index for every "which node?" question: Tab create, wire inbetween, link-drag search.

One index of creatable types with their static sockets (indexing all ~1250 Maya 2024 types
takes ~0.7 s, so it is built lazily and rebuilt only when the plug-in list changes). Ranking
mixes three signals:
  - text: exact > prefix > camel initials ("dm" -> decomposeMatrix) > substring > subsequence,
    over the type name and a few rigger aliases ("add" -> sum, plusMinusAverage);
  - context: how well the type's sockets fit the wire (same class beats merely compatible);
  - habit: how often the user picked the type (optionVar nodexTypeUsage), plus a small prior
    that puts Maya's rigging math above Arnold / Redshift shading utilities.
"""
import json
import math
import re

import maya.cmds as cmds

from . import model, ops

USAGE_VAR = "nodexTypeUsage"

# Rigging staples first: a prior, not a filter (anything still matches by name).
PRIOR = {
    "multMatrix": 9, "decomposeMatrix": 9, "composeMatrix": 7, "blendMatrix": 8, "pickMatrix": 7,
    "aimMatrix": 7, "inverseMatrix": 7, "wtAddMatrix": 5, "holdMatrix": 4, "parentMatrix": 5,
    "plusMinusAverage": 8, "multiplyDivide": 8, "multDoubleLinear": 6, "addDoubleLinear": 6,
    "reverse": 6, "condition": 6, "clamp": 5, "clampRange": 5, "remapValue": 7, "setRange": 6,
    "blendColors": 6, "blendTwoAttr": 5, "blendWeighted": 5, "pairBlend": 5, "choice": 4,
    "distanceBetween": 7, "vectorProduct": 6, "angleBetween": 5, "curveInfo": 6,
    "pointOnCurveInfo": 6, "motionPath": 4, "sum": 6, "multiply": 6, "divide": 5, "subtract": 5,
    "crossProduct": 5, "dotProduct": 5, "normalize": 5, "length": 5, "lerp": 5,
    "rotationFromMatrix": 5, "translationFromMatrix": 5, "rowFromMatrix": 4,
    "fourByFourMatrix": 5, "quatToEuler": 5, "eulerToQuat": 5, "quatSlerp": 4,
    "floatMath": 4, "unitConversion": -20,
}
ALIASES = {
    "add": ("sum", "plusMinusAverage", "addDoubleLinear", "addMatrix"),
    "mult": ("multiply", "multiplyDivide", "multDoubleLinear", "multMatrix"),
    "mul": ("multiply", "multiplyDivide", "multDoubleLinear", "multMatrix"),
    "sub": ("subtract", "plusMinusAverage"),
    "div": ("divide", "multiplyDivide"),
    "inv": ("inverseMatrix", "reverse", "negate"),
    "invert": ("inverseMatrix", "reverse", "negate"),
    "mix": ("blendColors", "blendMatrix", "pairBlend", "blendTwoAttr", "lerp"),
    "blend": ("blendColors", "blendMatrix", "pairBlend", "blendTwoAttr", "blendWeighted"),
    "remap": ("remapValue", "setRange", "clampRange"),
    "range": ("setRange", "remapValue", "clampRange"),
    "dist": ("distanceBetween",),
    "if": ("condition", "choice"),
    "switch": ("choice", "condition"),
    "offset": ("multMatrix", "composeMatrix"),
    "space": ("multMatrix", "blendMatrix", "parentMatrix", "pickMatrix"),
}
# Tab create window: categories first while the query is empty.
CREATE_GROUPS = [
    ("Transform", ["transform", "joint"]),
    ("Matrix", ["multMatrix", "decomposeMatrix", "composeMatrix", "blendMatrix", "pickMatrix",
                "aimMatrix", "inverseMatrix", "wtAddMatrix", "rotationFromMatrix"]),
    ("Math", ["plusMinusAverage", "multiplyDivide", "sum", "multiply", "divide", "reverse", "clamp",
              "clampRange", "blendColors", "multDoubleLinear", "addDoubleLinear", "condition"]),
    ("Vector", ["vectorProduct", "crossProduct", "dotProduct", "normalize", "length", "angleBetween"]),
    ("Utility", ["distanceBetween", "remapValue", "setRange", "curveInfo", "pointOnCurveInfo",
                 "blendTwoAttr", "blendWeighted", "pairBlend", "choice"]),
]
# Shading plug-ins crowd every list; they sink unless asked for by name.
RENDER_PREFIXES = ("ai", "Redshift", "rs", "PxrSurface", "vray")


def _is_render(type_name, cls):
    if type_name.startswith(RENDER_PREFIXES) and type_name[2:3].isupper():
        return True
    return any(part.startswith(("shader/", "texture/", "rendernode/", "light"))
               for part in cls.split(":")) and "math/" not in cls


class Entry(object):
    __slots__ = ("name", "cls", "dag", "render", "hidden", "inputs", "outputs", "initials", "lower")

    def __init__(self, name, cls, dag):
        self.name = name
        self.cls = cls
        self.dag = dag
        self.render = _is_render(name, cls)
        self.hidden = cls.startswith("hidden") or ":hidden" in cls
        self.inputs = None
        self.outputs = None
        self.lower = name.lower()
        self.initials = initials(name)

    def sockets(self, output):
        if self.inputs is None:
            try:
                self.inputs = ops.type_socket_options(self.name, False)
                self.outputs = ops.type_socket_options(self.name, True)
            except RuntimeError:
                self.inputs, self.outputs = [], []
        return self.outputs if output else self.inputs


def initials(name):
    """camelCase / snake_case word starts: decomposeMatrix -> 'dm', mgear_mulMatrix -> 'mmm'."""
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", name)
    return "".join(w[0].lower() for w in words)


def text_score(query, entry):
    """0 when the query does not match; higher is better (exact 100 ... subsequence ~20)."""
    q = query.lower()
    n = entry.lower
    if not q:
        return 1.0
    if n == q:
        return 100.0
    if n.startswith(q):
        return 80.0 - min(20.0, (len(n) - len(q)) * 0.5)
    if entry.initials.startswith(q) and len(q) >= 2:
        return 70.0 - (len(entry.initials) - len(q))
    i = n.find(q)
    if i >= 0:
        # a hit at a word start ("matrix" in multMatrix) beats one inside a word
        at_word = i > 0 and entry.name[i:i + 1].isupper()
        return (62.0 if at_word else 50.0) - min(10.0, i * 0.5)
    for alias, targets in ALIASES.items():
        if alias.startswith(q) and len(q) >= 2 and entry.name in targets:
            return 58.0 - targets.index(entry.name)
    # subsequence: every character in order, scored by how compact the match is
    pos, gaps, last = 0, 0, -1
    for ch in q:
        j = n.find(ch, pos)
        if j < 0:
            return 0.0
        if last >= 0:
            gaps += j - last - 1
        last, pos = j, j + 1
    return max(5.0, 30.0 - gaps)


def socket_fit(want, cls):
    """2 exact class, 1 compatible, 0 not connectable."""
    if want == cls and want not in ("MultiAmbiguous", "Array"):
        return 2
    return 1 if ops.compatible_sockets(want, cls) else 0


def rank_sockets(sockets, want, hint=""):
    """Sockets of one node ordered for a wire of class `want`; `hint` is the other end's plug
    name (worldMatrix -> prefer a socket named *matrix*). -> [(score, path, cls)]."""
    words = set(w.lower() for w in re.findall(r"[A-Z]?[a-z]+", hint.split(".")[-1].split("[")[0]))
    out = []
    for order, (path, cls) in enumerate(sockets):
        fit = socket_fit(want, cls)
        if not fit:
            continue
        leaf = path.split(".")[-1].split("[")[0]
        lw = set(w.lower() for w in re.findall(r"[A-Z]?[a-z]+", leaf))
        score = (fit * 10 + len(words & lw) * 2 + (1 if "." not in path else 0) - order * 0.01
                 + (1.5 if leaf.lower().startswith("in") else 0))
        out.append((score, path, cls))
    out.sort(key=lambda t: -t[0])
    return out


class Catalog(object):
    def __init__(self):
        self._plugins = None
        self._entries = {}
        self._memo = {}     # socket fits per wire context: typing only re-scores the text

    def _fits(self, key, fn):
        """[(entry, sockets...)] for one wire context, computed once per plug-in set."""
        self.entries()
        if key not in self._memo:
            self._memo[key] = [r for r in (fn(e) for e in self._entries.values()) if r]
        return self._memo[key]

    def entries(self):
        plugins = tuple(sorted(cmds.pluginInfo(q=True, listPlugins=True) or []))
        if plugins != self._plugins:
            self._plugins = plugins
            self._memo = {}
            old = self._entries
            self._entries = {}
            for t in cmds.allNodeTypes() or []:
                if t in old:
                    self._entries[t] = old[t]
                    continue
                try:
                    cls = ":".join(cmds.getClassification(t) or [])
                    inh = cmds.nodeType(t, inherited=True, isTypeName=True) or []
                except RuntimeError:
                    continue
                self._entries[t] = Entry(t, cls, "dagNode" in inh)
        return self._entries

    # ------------------------------------------------------------------ usage history

    @staticmethod
    def usage():
        try:
            return json.loads(cmds.optionVar(q=USAGE_VAR) or "{}") if cmds.optionVar(exists=USAGE_VAR) else {}
        except (ValueError, TypeError):
            return {}

    @classmethod
    def record(cls, type_name):
        u = cls.usage()
        u[type_name] = u.get(type_name, 0) + 1
        cmds.optionVar(stringValue=(USAGE_VAR, json.dumps(u)))

    def recent(self, n=8):
        u = self.usage()
        ents = self.entries()
        return [t for t, _ in sorted(u.items(), key=lambda kv: -kv[1]) if t in ents][:n]

    def _habit(self, e, usage):
        h = PRIOR.get(e.name, 0) + 3.0 * math.log1p(usage.get(e.name, 0))
        if e.render:
            h -= 8
        if e.hidden:
            h -= 30
        return h

    # ------------------------------------------------------------------ queries

    def search(self, query, limit=200):
        """Tab create: ranked type names for a typed query."""
        usage = self.usage()
        out = []
        for e in self.entries().values():
            t = text_score(query, e)
            if t <= 0 or (e.hidden and not query):
                continue
            out.append((t * 2 + self._habit(e, usage), e.name))
        out.sort(key=lambda p: (-p[0], p[1]))
        return [n for _, n in out[:limit]]

    def inbetween(self, sc, dc, query="", src_hint="", dst_hint="", limit=120):
        """Types that take a `sc` wire in and give a `dc` wire out, each with its best socket
        pair. -> [(type, input, output, all_inputs, all_outputs)] best first."""
        def fit(e):
            if e.dag or e.hidden or e.name in model.CONVERSION_TYPES:
                return None
            ins = rank_sockets(e.sockets(False), sc, src_hint)
            outs = self._outs_for(e, dc, dst_hint) if ins else None
            return (e, ins, outs) if outs else None
        usage = self.usage()
        out = []
        for e, ins, outs in self._fits(("ib", sc, dc, src_hint, dst_hint), fit):
            t = text_score(query, e) if query else 1.0
            if t <= 0:
                continue
            score = (t * 2 if query else 0) + ins[0][0] + outs[0][0] + self._habit(e, usage)
            out.append((score, e.name, ins[0][1], outs[0][1],
                        [(p, c) for _, p, c in ins], [(p, c) for _, p, c in outs]))
        out.sort(key=lambda r: (-r[0], r[1]))
        return [r[1:] for r in out[:limit]]

    @staticmethod
    def _outs_for(e, dc, hint):
        # output sockets are ranked by what they FEED: socket_fit(socket class -> dc)
        words = set(w.lower() for w in re.findall(r"[A-Z]?[a-z]+", hint.split(".")[-1].split("[")[0]))
        res = []
        for order, (path, cls) in enumerate(e.sockets(True)):
            if not ops.compatible_sockets(cls, dc):
                continue
            fit = 2 if cls == dc else 1
            leaf = path.split(".")[-1].split("[")[0]
            lw = set(w.lower() for w in re.findall(r"[A-Z]?[a-z]+", leaf))
            res.append((fit * 10 + len(words & lw) * 2 + (1 if "." not in path else 0) - order * 0.01
                        + (1.5 if leaf.lower().startswith("out") else 0), path, cls))
        res.sort(key=lambda t: -t[0])
        return res

    def link_targets(self, cls, output, query="", hint="", per_type=3, limit=150):
        """Blender's link-drag search: nodes that can take (output=True: the dragged wire is an
        output, we need an INPUT socket) or give a wire of class `cls`.
        -> [(type, socket, socket_class)] best first, a few sockets per type."""
        def fit(e):
            if e.hidden or e.name in model.CONVERSION_TYPES:
                return None
            socks = rank_sockets(e.sockets(False), cls, hint) if output else self._outs_for(e, cls, hint)
            return (e, socks) if socks else None
        usage = self.usage()
        q = query.lower().strip()
        tq, sq = (q.split(".", 1) + [""])[:2] if "." in q else (q, "")
        out = []
        for e, socks in self._fits(("link", cls, output, hint), fit):
            t = text_score(tq, e) if tq else 1.0
            if t <= 0:
                continue
            if sq:
                socks = [s for s in socks if sq in s[1].lower()]
                if not socks:
                    continue
            base = (t * 2 if tq else 0) + self._habit(e, usage) - (4 if e.dag else 0)
            for k, (fit_, path, scls) in enumerate(socks[:per_type]):
                out.append((base + fit_ - k * 3, e.name, path, scls))
        out.sort(key=lambda r: (-r[0], r[1], r[2]))
        return [r[1:] for r in out[:limit]]


_catalog = [None]


def get():
    if _catalog[0] is None:
        _catalog[0] = Catalog()
    return _catalog[0]
