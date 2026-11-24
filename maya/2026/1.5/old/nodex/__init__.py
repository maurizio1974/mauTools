"""NodeX -- a refreshed Maya Node Editor.

    import nodex; nodex.show()

Qt and the panel are imported lazily so that model/ops/store stay importable in mayapy
tests without a GUI.
"""


def show():
    from . import panel
    return panel.show()


def close():
    from . import panel
    panel.close()
