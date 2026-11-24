"""Where the mh_nodeps package is: finds lib/linux/py311 (the OpenRigLogic `dna` / `riglogic` modules)
and data/, also when scripts/ is symlinked or copied elsewhere. Set MH_NODEPS_ROOT to the mh_nodeps
folder to point at it explicitly."""
import os
import sys

_LIB = os.path.join("lib", "linux", "py311")


def _candidates():
    out = []
    env = os.environ.get("MH_NODEPS_ROOT")
    if env:
        out.append(os.path.expanduser(env))
    for f in (os.path.realpath(__file__), os.path.abspath(__file__)):   # realpath: follow symlinks
        here = os.path.dirname(f)
        out += [os.path.dirname(here), here, os.path.dirname(os.path.dirname(here))]
    for p in list(sys.path):                                              # an mh_nodeps folder on sys.path
        if p:
            out += [p, os.path.dirname(p)]
    seen, res = set(), []
    for c in out:
        c = os.path.normpath(c)
        if c not in seen:
            seen.add(c)
            res.append(c)
    return res


def root():
    for c in _candidates():
        if os.path.isfile(os.path.join(c, _LIB, "dna.py")) and os.path.isdir(os.path.join(c, "data")):
            return c
    raise ImportError("mh_nodeps not found: no %s/dna.py next to data/ in any of:\n  %s\n"
                      "Unzip the whole mh_nodeps folder (lib/, data/, scripts/, tools/ together) and set the "
                      "environment variable MH_NODEPS_ROOT to it, or add mh_nodeps/scripts itself to sys.path."
                      % (_LIB, "\n  ".join(_candidates()[:8])))


def lib_dir():
    return os.path.join(root(), _LIB)


def data_dir():
    return os.path.join(root(), "data")


def ensure_dna():
    """Import Epic's `dna` module, adding the package's lib folder to sys.path when needed."""
    try:
        import dna
        if hasattr(dna, "BinaryStreamReader"):
            return dna
    except ImportError:
        pass
    lib = lib_dir()
    if lib not in sys.path:
        sys.path.insert(0, lib)
    sys.modules.pop("dna", None)
    import dna
    return dna
