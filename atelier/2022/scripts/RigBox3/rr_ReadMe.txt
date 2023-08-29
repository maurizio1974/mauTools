NAME: RigBox Reborn Curves Tool, Python 3
VERSION: 3.07
AUTHOR: David Saber, www.DavidSaber.com www.dreamcraftdigital.com , Jennifer Conley
SCRIPTING LANGUAGE: Python
DATE OF LATEST VERSION: 2022-10-13
LATEST VERSION BY: David Saber
USAGE: This is a main tool comprised of smaller, sub-scripts. The Curves Tool script contains commonly used features such as:
	- Control icon creation
	- Colorizing options
	- Preset and custom attribut creation
	- Control clean up options
MANUAL:	1. Install the script : see below
		2. Run the Script.
		3. In the interface, name the object, select an object shape, color it, lock channels
LINKS:	Check author's link, https://www.highend3d.com/maya/script/rigbox-reborn-curves-tool-for-maya
FEEDBACK, BUG REPORTS AND FEATURE REQUEST: Contact David Saber, see author above
TODO:	better installation

NOTES:
RigBox Reborn Curves Tool in Python 3 for Maya 2022. Updated Jennifer Conley's Script to Python version 3. Rigbox Curve tool version 3.
Jennifer Conley's Script "RigBox Reborn Curves Tool" was just translated into Python 3, so it's compatible with Maya 2022. I told Jen that I could send this updated script to her, so she could upload it to her account herself. But she didn't answer so I'm uploading it to my account because I know many Maya riggers are waiting for it! Enjoy.
Install and other info : Check the text file rr_ReadMe.txt.

CREDITS
Original script : Jennifer Conley
Script and information text updated by David from 2021-11-12. www.dreamcraftdigital.com
Python 2 to Python 3 conversion done by Reddit user SheepRSA https://www.reddit.com/r/Maya/comments/nvg422/update_pymel_for_2022/h14pz74/
CTRL_BOX_icon.png created by Jeromine

CHANGE LOG
- Version : 3.00, 2021-11-12: converted to Python 3
- Version : 3.01, 2022-01-10: arrow curves renamed
- Version : 3.02, 2022-05-01: better help text file, coloring nurbs curves : orange color added
- Version : 3.03, 2022-05-02: all files are now inside a folder called "RigBox3"
- Version : 3.04, 2022-05-04: little GUI improvement
- Version : 3.05, 2022-05-10: replaced index colors by RGB colors, source : https://forums.autodesk.com/t5/maya-programming/how-to-set-rgb-color-for-drawing-overrides-with-python/td-p/7592153 
- Version : 3.06, 2022-05-10: some objects were not created at the scene center, as reported here: https://www.highend3d.com/maya/script/rigbox_reborn-curves-tool-for-maya/bugs/2201 . Fixed.
- Version : 3.07, 2022-10-13: attempt to fix the error message "inconsistent use of tabs and spaces in indentation", which prevents some users to install the script in Maya 2023, as reported here: https://www.highend3d.com/maya/script/rigbox-reborn-curves-tool-for-maya/topics/install-on-maya-2023 .

HOW TO INSTALL: PYMEL
- First install Pymel in Maya 2022. PyMEL is an optional item when you install Maya 2022, you could run the installer again and tick the PyMEL box to install it. If you didn't install it during the Maya installation process, follow the instructions below.
- Lets check if its really installed: navigate to maya installation folder find folder bin select it and while holding down shift press RMB (right mouse button) to open modified context menu, from there find and click "open in powerShell".
- In Powershell, you should see this:
	PS <installed_path>Maya2022\bin>
- You must use this command : 
	.\mayapy.exe -m pip list
To get this command, just type mayapy and press [TAB] (it will expand like .\mayapy.exe) then continue typing " -m pip list". then you should see this:
	PS <installed_path>Maya2022\bin> .\mayapy.exe -m pip list
- If you see this, press enter
- If you get something like this, it means there is no pymel:
	future 0.18.2
	pip 20.2.2
	PySide2 5.15.2
	setuptools 41.2.0
	shiboken2 5.15.2
	shiboken2-generator 5.15.2
- Then you need to install Pymel this way:
	.\mayapy.exe -m pip install pymel
- After installation is complete you can check it again, using :
	.\mayapy.exe -m pip list
- If you get something like this, it means Pymel is now installed:
	future 0.18.2
	pip 21.2.2
	pymel 1.2.0
	PySide2 5.15.2
	setuptools 41.2.0
	shiboken2 5.15.2
	shiboken2-generator 5.15.2
- You're ready to go! no need to modify PATH environment variable. 
- If you receive message that new version of pip installer is available, and if you wish to upgrade it, use this cmd:
	.\mayapy.exe -m pip install --upgrade pip
- That's it. For more info, You can also check this discussion : https://forums.autodesk.com/t5/maya-programming/maya-2022-pymel-how-to-import/m-p/10409310 

HOW TO INSTALL: RIGBOX SCRIPT
- Now install Rigbox in Maya 2022 following these instructions below.
- Go to your Maya preference folder, usually it's in Documents\Maya. Go inside the folder Documents\Maya\scripts .
- Unzip/Unrar the file "Rigbox Reborn Curve Tool Python 3.rar", place the "RigBox3" folder into the folder Documents\Maya\scripts
- Once the files have been placed correctly, copy and paste the following lines of code into the Script Editor, Python tab, and click the Execute button.
import RigBox3.rr_main_curves
RigBox3.rr_main_curves.window_creation()
- A Rigbox Windows should popup.
- Get the script as a permanent button in Maya's interface: in Maya, display the Rigging tool tab. In the script editor, select these 2 Python lines. Middle click and drag them to the right end of the Rigging tool tab. An ugly button should appear.
- Right click the button and choose edit. Go to the "Shelves" tab. Click the folder button on the right side of "Icon name", browse to where you put the rigbox files. Pick the file: "rr_RigBox3_icon.png". You can also type "RigBox" in ""Icon label".
- Voila! Cheers, Jen and David