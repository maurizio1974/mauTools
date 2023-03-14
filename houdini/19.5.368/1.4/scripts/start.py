import hou
import sys

dds = [
	'C:/Users/mauri/Documents/code', 'C:/Users/mauri/Documents/houdini19.0/scripts',
	'C:/Users/mauri/Documents/code/assetPack']
for dd in dds:
	if dd not in sys.path:
		sys.path.append(dd)

# hou.ui.displayMessage('make sure to show\ncheck camera\ncheck frame range')