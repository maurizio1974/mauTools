HOW TO INSTALL RIGBOX REBORN PYTHON 3, CURVES TOOL
Version : 3

- First install Pymel in Maya 2022 if it's not already done: https://forums.autodesk.com/t5/maya-programming/maya-2022-pymel-how-to-import/m-p/10409310 
- Lets check if its really installed: navigate to maya installation folder find folder bin select it and while holding down shift press rmb  to open modified context menu from there find and click "open in powerShell".
then just type mayapy and press [TAB] (it will expand like .\mayapy.exe) then continue typing " -m pip list":
PS <installed_path>Maya2022\bin> .\mayapy.exe -m pip list
and press enter
if you will get something like this
future 0.18.2
pip 20.2.2
PySide2 5.15.2
setuptools 41.2.0
shiboken2 5.15.2
shiboken2-generator 5.15.2
* there is no pymel
- Then you need to install it this way:
.\mayapy.exe -m pip install pymel
- After installation is complete you can check it again:
you should get something similar:
future 0.18.2
pip 21.2.2
pymel 1.2.0
PySide2 5.15.2
setuptools 41.2.0
shiboken2 5.15.2
shiboken2-generator 5.15.2
* pymel is now installed!
you're ready to go! no need to modify PATH environment variable
- If you receive message that new version of pip installer is available and if you wish to upgrade it use this cmd:
.\mayapy.exe -m pip install --upgrade pip
- Now install Rigbox in Maya 2022: Place all files files contained within the RigBox_Reborn folder or RAR file into the Maya Scripts folder.
- Once the files have been placed correctly, copy and paste the following lines of code into the Script Editor, Python tab, and click the Execute button.
import rr_main_curves
rr_main_curves.window_creation()
- A Rigbox Windows should popup.
- Get the script as a permanent button in Maya's interface: in Maya, display the Rigging tool tab. In the script editor, select these 2 Python lines. Middle click and drag them to the right end of the Rigging tool tab. An ugly button should appear.
- Right click the button and choose edit. Go to the "Shelves" tab. Click the folder button on the right side of "Icon name", browse to where you put the rigbox files. Pick the CTRL_BOX_icon.png file.
- Voila! Cheers,

Jen and David

Text updated by David at 2021-11-01. www.dreamcraftdigital.com
Python 2 to Python 3 conversion done by Melody's BF
CTRL_BOX_icon.png created by Jeromine
