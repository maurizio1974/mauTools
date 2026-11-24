"""
Export the behaviour layer (Rig Logic data) of a MetaHuman DNA to JSON, for the native facial rig
(scripts/native_riglogic.py). Runs outside Maya too: any Python that can import Epic's `dna` module.

Uses the OpenRigLogic `dna` module shipped in ../lib/linux/py311 (Python 3.11, e.g. mayapy 2026):
    python3.11 <mh_nodeps>/tools/dna_behavior_export.py character.dna character_behavior.json

Then in Maya: native_riglogic.build(source="character_behavior.json")
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "linux", "py311"))  # OpenRigLogic dna
from native_riglogic import behavior_from_reader  # noqa: E402  (no Maya import at module level)


def export(dna_path, json_path):
    import dna
    stream = dna.FileStream(dna_path, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
    reader = dna.BinaryStreamReader(stream, dna.DataLayer_All)
    reader.read()
    if not dna.Status.isOk():
        raise RuntimeError("Error loading DNA %s: %s" % (dna_path, dna.Status.get().message))
    data = behavior_from_reader(reader)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: dna_behavior_export.py <in.dna> <out.json>")
    d = export(sys.argv[1], sys.argv[2])
    print("written %s: %d GUI controls, %d raw controls, %d correctives, %d joints, %d blendshape channels, %d maps"
          % (sys.argv[2], len(d["guiControls"]), len(d["rawControls"]), d["psd"]["count"], len(d["joints"]),
             len(d["blendShapeChannels"]), len(d["animatedMaps"])))
