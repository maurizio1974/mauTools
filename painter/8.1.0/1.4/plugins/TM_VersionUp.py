'''
==================================================================================================

TM Version Up (v1.1)

==================================================================================================
Add a Version Up button to the File Menu of Substance Painter. Also Assign a shortcut F12.
This button save as a new incremented version your substance painter project/file. 
If no version are present in the name already, it will add one automatically and save as.
Otherwise it will respect your current version naming convention.
===================================================================================================

:author: Timothee Maron
         https://gumroad.com/timotheemaron
         https://www.artstation.com/timotheemaron

If you like this tool, please share the gumroad link and support my work and hours spent building it ! :)

===================================================================================================
REQUIREMENTS :
Substance Painter with at least version 2020.1+ (6.1.0+)

INSTALL

- Copy this file (TM_VersionUp.py) to your Substance Painter python plugin folder
Default Substance Painter python plugin folder on Windows is :
    C:/Users/USERNAME/Documents/Allegorithmic/Substance Painter/python/plugins
- Start Substance Painter ! 
TM Version Up should be enabled by default under the Python Menu and a "Version UP" button should be
available under the File menu.

! If the button is grayed out, it is probably because you haven't saved at leat once yet !
    
'''

# --------------------------------------------------------------------------------------------------
#
# --------------------------------------------------------------------------------------------------


from PySide2 import QtWidgets, QtCore, QtGui
import os
import glob
import substance_painter.project
import substance_painter.ui

VERSIONUP_PLUGIN = None
plugin_widgets = [] #Keep track of added ui elements for cleanup

class versionUp_plugin(QtWidgets.QDialog):
    def __init__(self):
        #create widget
        self.versionUp_action = QtWidgets.QAction("Version Up")
        #create connection
        self.versionUp_action.triggered.connect(self.versionUpandSave)
        #add widget to menu
        substance_painter.ui.add_action(substance_painter.ui.ApplicationMenu.File,self.versionUp_action)
        #set shortcut
        shortcutKey = QtGui.QKeySequence(QtCore.Qt.Key_F12) 
        self.versionUp_action.setShortcut(shortcutKey)
        
        if not substance_painter.project.is_open():
            self.versionUp_action.setDisabled(True)
            
        # Subscribe to project related events.
        connections = {
            substance_painter.event.ProjectOpened: self.on_project_opened,
            substance_painter.event.ProjectAboutToClose: self.on_project_about_to_close,
            substance_painter.event.ProjectSaved: self.on_project_saved
        }
        for event, callback in connections.items():
            substance_painter.event.DISPATCHER.connect(event, callback)
    
    def on_project_opened(self, e):
        self.versionUp_action.setDisabled(False)
        
    def on_project_about_to_close(self, e):
        self.versionUp_action.setDisabled(True)
        
    def on_project_saved(self, e):
        self.versionUp_action.setDisabled(False)
        
    def versionUpandSave(self):
        if not substance_painter.project.is_open():
            substance_painter.logging.log(substance_painter.logging.WARNING,
            "Plugin - TM Version Up",
            "Save at least one first time your project to use TM Version Up.") 
            return
        
        projectPath = substance_painter.project.file_path()
        if projectPath == None :
            substance_painter.logging.log(substance_painter.logging.WARNING,
            "Plugin - TM Version Up",
            "Save at least one first time your project to use TM Version Up.") 
            return
           
        old_projectName = projectPath.split('/')
        old_projectName = old_projectName[-1]
        if '_v' in old_projectName:
            old_version = old_projectName.split('_v')
            old_version = old_version[-1]
            old_version = old_version.split('.')
            old_version = old_version[0]
            new_version = str(int(old_version) + 1)
            new_version = new_version.zfill(len(old_version))
            
            new_projectName = old_projectName.replace(old_version,new_version)
            new_projectPath = projectPath.replace(old_projectName,new_projectName)
            
        else:
            new_version = "001"
            new_projectPath = projectPath.replace('.spp','_v'+new_version+'.spp')
        
        #check if file exist and find latest version    
        if os.path.isfile(new_projectPath):
            substance_painter.logging.log(substance_painter.logging.INFO,
            "Plugin - TM Version Up",
            "File already exists, using latest version number found in folder.")
            searchPath = new_projectPath.split('_v')
            del searchPath[-1]
            searchPath = '_v'.join(searchPath)
            
            listExistingFiles = glob.glob(searchPath + '_v*.spp')
            listExistingFiles_APPROVED = []
            for check in listExistingFiles:
                checkName = check.split('_v')
                del checkName[-1]
                checkName = '_v'.join(checkName)
                checkNameSlash = checkName.replace('\\','/')
                if checkNameSlash == searchPath :
                    listExistingFiles_APPROVED.append(check)
                else:
                    pass
                    
            latestExistingFile = listExistingFiles_APPROVED[-1]
            existing_version = latestExistingFile.split('_v')
            existing_versionFull = existing_version[-1]
            
            existing_version = existing_versionFull.replace('.spp','')
            real_new_version = str(int(existing_version) + 1)
            real_new_version = real_new_version.zfill(len(existing_version))
            real_new_version = real_new_version
            
            new_projectPath = new_projectPath.replace(new_version+'.spp',real_new_version+'.spp')
            
        
        #save as   
        substance_painter.project.save_as(new_projectPath, substance_painter.project.ProjectSaveMode.Full)

def start_plugin():
    global VERSIONUP_PLUGIN
    VERSIONUP_PLUGIN = versionUp_plugin()
    plugin_widgets.append(VERSIONUP_PLUGIN)
    
def close_plugin():
    global VERSIONUP_PLUGIN
    del VERSIONUP_PLUGIN
    for widget in plugin_widgets:
        substance_painter.ui.delete_ui_element(widget)
    plugin_widgets.clear()
    
if __name__ == "__main__":
    start_plugin()    