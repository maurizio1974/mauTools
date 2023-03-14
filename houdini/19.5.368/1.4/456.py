import sys

pptemp = [
	'C:/Users/mauri/Documents/code',
	'C:/Users/mauri/Documents/houdini19.5/scripts']

for p in pptemp:
	if p not in sys.path:
		sys.path.append(p)