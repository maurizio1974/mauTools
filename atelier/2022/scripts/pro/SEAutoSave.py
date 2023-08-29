import threading, time, math
import pymel.core as pm
#import pymel.mayautils as utils
from maya.utils import executeInMainThreadWithResult as execute, executeDeferred as deferred
import maya.mel as mel
import os, time
from os.path import isfile, join
import maya.OpenMaya as om

class SaveScriptError( Exception ):
    pass
class OtherScriptError( Exception ):
    pass

class AutoSaveThread( object ):
    """Thread to run in the background to auto save the script editor contents."""
    
    def __init__( self, wait=0 ):
        """Start self.run() as a thread.
        
        wait:
            How many seconds to wait before starting the timer, to be used if loading
            the script automatically when Maya starts.
             - Integer
             - Recommended 0 if manually activated, 10 if automatically loading
        """
        #Set up values
        self.wait = wait
        self.location = execute( AutoSave().location )
        self.enabled=True
        
        #Begin thread
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
        
    def run(self):
    
        #Wait a short while before starting the execution
        time.sleep( self.wait )
        
        printStuff( "Started at intervals of {} seconds. Do not open or close the script editor during saving.".format( execute( AutoSave().interval ) ), AutoSave.printPrefix )
        alreadySaidItsPaused = False
        
        #Loop until the running state becomes False
        while execute( AutoSave().enabled ):
        
            #Find if code is paused
            if not execute( AutoSave().paused ):
                
                #Update progress
                interval = execute( AutoSave().interval )
                intervals = set( i for i in ( 15, 10, 5, 3, 2, 1 ) if i*2 <= interval )
                totalCount = 0
                
                #Print if just unpaused
                if alreadySaidItsPaused:
                    printStuff( "Resuming backup, activating in {0} seconds.".format( interval ), AutoSave.printPrefix )
                    alreadySaidItsPaused = False
                    
                #Count down from interval
                for i in xrange( interval, 0, -1 ):
                
                    execute( AutoSave().progress, time.time() )
                    
                    #Make sure interval hasn't been changed
                    if i <= execute( AutoSave().interval ):
                    
                        #Check state hasn't been changed to paused or stopped
                        runningState = execute( AutoSave().enabled )
                        if runningState > 0:
                        
                            #Only print progress if the time matches anything in the list
                            if i in intervals:
                                s = ''
                                if i != 1:
                                    s = 's'
                                printStuff( "Activating in {0} second{1}...".format( i, s ), AutoSave.printPrefix )
                        else:
                            break
                            
                    time.sleep( 1 )
                    
                #Continue if state is still running
                if execute( AutoSave().enabled ) > 0:
                    
                    interval = execute( AutoSave().interval )
                    
                    #Attempt to save
                    onlySavedBackupFiles = False
                    printStuff( "Saving scripts... Do not open or close the script editor during this time.", AutoSave.printPrefix )
                    try:
                        execute( saveScriptEditorFiles, True, self.location )    #Backup files first
                        onlySavedBackupFiles = True
                        execute( saveScriptEditorFiles, False, self.location )   #Overwrite main files
                        onlySavedBackupFiles = False
                        
                    #If script editor window is closed (tabs don't exist)
                    except RuntimeError:
                        printStuff( "Item doesn't exist (window is probably closed), trying again in {0} seconds.".format( interval ), AutoSave.printPrefix )
                        
                        #This shouldn't ever happen, but just in case, save the backup files from deletion
                        if onlySavedBackupFiles:
                            MoveBackupScriptsToFolder( self.location )
                            moveLocation = self.location+'/scriptEditorTemp/{0}'.format( time.time() )
                            printStuff( "Normal files may have become corrupted so backup files have been moved into '{0}'.".format( moveLocation ), AutoSave.printPrefix )
                    
                    #If file is read only
                    except WindowsError:
                        printStuff( "Failed to save scripts, one or more of the files is read only.", AutoSave.printPrefix )
                    
                    #If saving is disabled
                    except SaveScriptError:
                        printStuff( "Saving to the script editor is not enabled, type 'pm.optionVar['saveActionsScriptEditor']=1' to enable.", AutoSave.printPrefix )
                    
                    #Other unknown error
                    except:
                        #This also shouldn't happen
                        printStuff( "Failed to save scripts for unknown reason, if it keeps happening please let me know.", AutoSave.printPrefix )
                    
                    #Successful save
                    else:
                        printStuff( "Successfully saved scripts, saving again in {0} seconds.".format( interval ), AutoSave.printPrefix )
                    
            
            else:
            
                #Only print that the script has been paused once, but keep looping
                if not alreadySaidItsPaused:
                    alreadySaidItsPaused = True
                    printStuff( "Paused by user", AutoSave.printPrefix )
                execute( AutoSave().progress, time.time() )
                time.sleep(1)
        
        #Print confirmation that loop has been stopped
        execute( AutoSave().progress, False )
        printStuff( "Cancelled by user", AutoSave.printPrefix )

def printWrapper( input ):
    """Wrapper to be used with executeDeferred."""
    pm.mel.mprint( input+'\n' )

def printStuff( stuff, prefix='', suffix='' ):
    """Print function to use the wrapper."""
    if not pm.optionVar[AutoSave.printName]:
        currentTime = time.strftime('[%H:%M:%S] ', time.localtime(time.time()))
        execute( printWrapper, '// '+str( currentTime )+str( prefix )+str( stuff )+str( suffix ) )


def saveScriptEditorFiles( backup=False, saveLocation=None ):
    """Modification of the inbuilt MEL code syncExecuterBackupFiles(),
    to allow for backup files to be created separately, and not be 
    deleted when overwriting the main files.
    
    backup:
        changes the fileNames it will save and delete, always run the
        backup first, since if it crashes, the main files are still 
        intact.
         - Boolean
    
    saveLocation:
        Will automatically set itself to the correct value if left empty, 
        only needs to be given when being used inside a thread.
         - String:
            "C:/Users/(name)/Documents/Maya/(version)/prefs/"
            pymel.core.internalVar( userPrefDir=True )
    """
    
    #Needs to be manually set if being run from thread
    if not saveLocation:
        saveLocation = pm.optionVar[AutoSaveThread.locationName]
    saveLocation += 'scriptEditorTemp/'
    
    #Get MEL global variables
    mel.eval( 'global string $gCommandExecuter[]' )
    mel.eval( 'global string $executerBackupFileName' )
    scriptEditorTabs = mel.eval( '$scriptEditorTabs=$gCommandExecuter' )
    backupFileName = mel.eval( '$backupFileName=$executerBackupFileName' )
    if backup:
        backupFileName += 'Backup'
    
    #Continue if saving is enabled in preferences
    saveScriptEditor = pm.optionVar['saveActionsScriptEditor']
    
    if saveScriptEditor :
        if scriptEditorTabs:
        
            #Get folder location and list of files
            oldFiles = [f for f in os.listdir( saveLocation ) if os.path.isfile( os.path.join( saveLocation, f ) )]
            
            #Get matching file number
            numMatchingFiles = 0
            for i in oldFiles:
                if i.split('-')[0] == backupFileName:
                    numMatchingFiles += 1
                        
            #Save new files                                       
            for i in range( max( numMatchingFiles, len( scriptEditorTabs ) ) ):
            
                #Overwrite files
                if i <= len( scriptEditorTabs )-1:
                    
                    #Will raise RuntimeError if script editor is closed, because the tab doesn't exist
                    tabContents = pm.cmdScrollFieldExecuter( scriptEditorTabs[i], text=True, query=True )
                        
                    #Keep line breaks actually written in the code
                    breakInCodeMarker = '---linebreaktemp.{}---'.format( time.time() )
                    textToStore = tabContents.replace('\\n',breakInCodeMarker).replace('\n','\r\n').replace(breakInCodeMarker,'\\n')
                    
                    #Generate correct file name
                    fileName = saveLocation+backupFileName
                    if i:
                        fileName += '-'+str( i-1 )
                    with open( fileName, 'w' ) as f:
                        f.write( textToStore )
            
                #Delete files
                else:
                    try:
                        os.remove( saveLocation+oldFiles[i] )
                    except:
                        printStuff( "Couldn't remove file: {0}".format( saveLocation+i ) )
                    
                                           
        #Fix to stop scripts deleting before opening editor for the first time
        else:
            raise RuntimeError()
    else:
        raise SaveScriptError()

        
def MoveBackupScriptsToFolder( saveLocation=None ):
    """Move any files containing 'backup' in the name to a timestamped folder.
    
    saveLocation:
        Will automatically set itself to the correct value if left empty, 
        only needs to be given when being used inside a thread.
         - String:
            "C:/Users/(name)/Documents/Maya/(version)/prefs/"
            pm.internalVar( userPrefDir=True )
    """
    #Automatically set location
    if saveLocation == None:
        saveLocation = pm.optionVar[self.locationName]
    
    #Get current folder and new folder names
    saveLocation += "scriptEditorTemp/"
    newBackupDir = saveLocation+'backup-'+str( int( time.time() ) )+"/"
    
    #Get list of files
    fileNames = [f for f in os.listdir( saveLocation ) if os.path.isfile( os.path.join( saveLocation, f ) )]
    for i in fileNames:
        if 'Backup' in i:
        
            #Make folder if it doesn't exist
            if not os.path.exists( newBackupDir ):
                os.makedirs( newBackupDir )
                
            #Move file
            os.rename(saveLocation+i, newBackupDir+i.replace( 'Backup', '' ))
        
        
firstRun = False
try:
    AutoSave()
except:
    firstRun = True

class AutoSave:
    """Control the auto save thread. Setting values in this will edit the
    prefs dictionary (pymel.core.optionVar), so values will be persistent
    between sessions.
    
    Functions:
        start( interval=0 ) - start/resume thread
        pause() - pause thread
        paused() - return if paused
        stop() - stop thread
        interval() - how many seconds between saves
        enabled() - current state of thread
        progress() - current progress of thread
        location() - location of script editor files
        silent() - if messages should be disabled
        clear() - remove all preferences to do with this script
        reset() - reset preferences to default
    """
    printPrefix = 'SE Auto Save: '
    autoSaveName = 'scriptEditorAutoSave'
    intervalName = 'scriptEditorSaveInterval'
    progressName = 'scriptEditorSaveInProgress'
    printName = 'scriptEditorSilentSave'
    locationName = 'scriptEditorSaveLocation'
    def __init__(self):
        """Auto set values if they don't exist yet."""
        #Set interval at 2 minutes
        if pm.optionVar.get( self.intervalName, None ) is None:
            self.interval( 60 )
        #Set current progress to False
        if pm.optionVar.get( self.progressName, None ) is None:
            self.progress( False )
        #Set silent mode to False
        if pm.optionVar.get( self.printName, None ) is None:
            self.silent( False )
        #Set the script editor location
        self.location( True )
        #Set state of the thread to 'stopped'
        if pm.optionVar.get( self.autoSaveName, None ) is None:
            self.enabled( False )
            
    def start( self, timing=None, wait=0 ):
        """Start or unpause the thread, and change the interval.
        
        timing:
            Uses AutoSave().interval() to change the interval to the provided
            value for conveniance.
             - Integer above 2
        
        wait:
            The number of seconds to wait before the thread will begin.
             - Integer above 0
        """
        #Set interval
        if str( timing ).isdigit():
            self.interval( timing )
            
        #Find if previously paused
        wasPaused = False
        if self.paused():
            wasPaused = True
        
        #Start the thread
        self.enabled( True )
        if not self.progress() and not wasPaused or time.time()-2 > self.progress():
            AutoSaveThread( wait )
            
    def pause(self):
        """Stop the thread from saving anything, but keep it running."""
        self.enabled(-1)
            
    def stop( self ):
        """End the thread."""
        self.progress( False )
        
    def paused( self ):
        """If the thread is currently paused."""
        return self.enabled() == -1
        
    def interval( self, timing=None ):
        """Set or return the interval between saving.
        
        timing:
            Number of seconds between saving attempts. If left empty,
            returns the current set value.
             - Integer above 2
        """
        #Return current interval
        if timing is None:
            return pm.optionVar[self.intervalName]
            
        #Check if it is a number
        try:
            int( timing )/1
        except:
            pass
        else:
            #Make sure it is above 2 seconds
            pm.optionVar[self.intervalName] = max( 2, timing )
            
    def enabled( self, state=None ):
        """Set or return the current state of the thread. 1 or True is active,
        0 or False is stopped, and -1 is paused.
        
        state:
            Set the state of the thread. If left empty, returns the current 
            state.
             - Integer (1, 0, -1)
        """
        #Return current state
        if state is None:
            return pm.optionVar[self.autoSaveName]
        
        #Set state
        pm.optionVar[self.autoSaveName] = state
        
    def progress( self, progress=None ):
        """Similar to the states, but used to check the thread is still
        active, and not just in an active state because of an improper
        shutdown. If it has not been updated in the last 2 seconds and
        AutoSave().start() is called, it is presumed the thread is not
        active.
        
        progress:
            Set the time of the latest thread activity. If left empty,
            returns the last time it was updated. Set to 0 to mark the
            thread as stopped.
             - Integer
        """
        #Return progress
        if progress is None:
            return pm.optionVar[self.progressName]
         
        #Set progress
        pm.optionVar[self.progressName] = progress
        
        #Update state if progress is False
        if progress == False:
            self.enabled( False )
            
    def silent(self,silence=None):
        """If all print messages should be disabled. Currently not recommended
        due to crashing if loading/closing the script editor during saving.
        
        silence:
            Choose if script should run silently. If left empty, returns the
            current setting.
             - Boolean
        """
        #Return if code should be silent
        if silence is None:
            return pm.optionVar[self.printName]
        
        #Set if code should be silent
        pm.optionVar[self.printName] = silence
        
        
    def location( self, update=None ):
        """Location of the script editor files.
        
        update:
            Refresh the location. If left empty, return the stored location.
             - Boolean
        """
        #Return location of script editor files
        if update is None:
            return pm.optionVar[self.locationName]
        
        #Refresh location of script editor files
        pm.optionVar[self.locationName] = pm.internalVar( userPrefDir=True )
    
    def clear( self, reset=False ):
        """Delete all stored options, and reset if required."""
        
        AutoSave().stop()
        pm.optionVar.pop( self.autoSaveName )
        pm.optionVar.pop( self.intervalName )
        pm.optionVar.pop( self.progressName )
        pm.optionVar.pop( self.printName )
        pm.optionVar.pop( self.locationName )
        
        if reset:
            AutoSave()
    
    def reset( self ):
        """Quick reset of the values using self.clear()."""
        self.clear( True )
        
        
    def quickSave( self, interval=None ):
        """
        Manually save the files.
        A little messy currently as it's just copied and pasted from the threaded version.
        """
        
        scriptLocation = execute( self.location )
        
        #Attempt to save
        onlySavedBackupFiles = False
        printStuff( "Saving scripts... Do not open or close the script editor during this time.", self.printPrefix )
        execute( saveScriptEditorFiles, True, scriptLocation )
        try:
            execute( saveScriptEditorFiles, True, scriptLocation )    #Backup files first
            onlySavedBackupFiles = True
            execute( saveScriptEditorFiles, False, scriptLocation )   #Overwrite main files
            onlySavedBackupFiles = False
            
        #If script editor window is closed (tabs don't exist)
        except RuntimeError:
            printMessage = "Item doesn't exist (window is probably closed)."
            if interval: 
                printMessage = printMessage[:-1]+", trying again in {0} seconds.".format( interval )
            printStuff( printMessage, self.printPrefix )
            
            #This shouldn't ever happen, but just in case, save the backup files from deletion
            if onlySavedBackupFiles:
                MoveBackupScriptsToFolder( scriptLocation )
                moveLocation = scriptLocation+'/scriptEditorTemp/{0}'.format( time.time() )
                printStuff( "Normal files may have become corrupted so backup files have been moved into '{0}'.".format( moveLocation ), self.printPrefix )
        
        #If file is read only
        except WindowsError:
            printStuff( "Failed to save scripts, one or more of the files is read only.", self.printPrefix )
        
        #If saving is disabled
        except SaveScriptError:
            printStuff( "Saving to the script editor is not enabled, type 'pm.optionVar['saveActionsScriptEditor']=1' to enable.", self.printPrefix )
        
        #Other unknown error
        except:
            #This also shouldn't happen
            printStuff( "Failed to save scripts for unknown reason, if it keeps happening please let me know.", self.printPrefix )
        
        #Successful save
        else:
            printMessage = "Successfully saved scripts."
            if interval: 
                printMessage = printMessage[:-1]+", saving again in {0} seconds.".format( interval )
            printStuff( printMessage, self.printPrefix )
        

class AutoSaveCallback:
    """
    Temporary class to link saveScriptEditorFiles to the saving callbacks.
    """
    
    @classmethod
    def save( self, backup ):
        """Save the files, and output the result."""
                
        #Attempt to save
        if backup:
            printStuff( "Backing up script editor...", AutoSave.printPrefix )
        else:
            printStuff( "Saving main script files...", AutoSave.printPrefix )
            
        try:
            execute( saveScriptEditorFiles, backup, AutoSave().location() )
            
        #If script editor window is closed (tabs don't exist)
        except RuntimeError:
            if not backup:
                printStuff( "Item doesn't exist (window is probably closed).", AutoSave.printPrefix )
            
        #If file is read only
        except WindowsError:
            printStuff( "Failed to save scripts, one or more of the files is read only.", AutoSave.printPrefix )
        
        #If saving is disabled
        except SaveScriptError:
            if backup:   #Only write this once
                printStuff( "Saving script editor contents is disabled, enable it in the preferences to allow auto saving.", AutoSave.printPrefix )
        
        #Other unknown error
        except Exception as e:
            printStuff( "Failed to save scripts for unknown reason ({}), tell me if you see this message.".format( e.message ), AutoSave.printPrefix )
        
        #Successful save
        else:
            if not backup:
                printStuff( "Successfully saved scripts.", AutoSave.printPrefix )
    
    @classmethod
    def causeUndo(self):
        """Create a node then delete it, to mark the scene as 'changed' and force the autosaving."""
        tempNode = pm.createNode('unknown', n='SEAutoSaveTemp')
        pm.delete( tempNode )
        
    @classmethod
    def deferredCauseUndo(self, *args):
        """Wrapper for causeUndo()"""
        deferred( self.causeUndo )
        
    @classmethod
    def register(self):
        """Register callbacks for the save events."""
        om.MSceneMessage().addCallback( om.MSceneMessage.kBeforeExport, self.save, True )
        om.MSceneMessage().addCallback( om.MSceneMessage.kBeforeSave, self.save, True )
        om.MSceneMessage().addCallback( om.MSceneMessage.kAfterExport, self.save, False )
        om.MSceneMessage().addCallback( om.MSceneMessage.kAfterSave, self.save, False )
    
    def registerUndo(self):
        """Register callbacks for forcing autosaves with deferredCauseUndo()."""
        self.deferredCauseUndo()
        om.MSceneMessage().addCallback( om.MSceneMessage.kAfterOpen, self.deferredCauseUndo, 'kAfterOpen' )
        om.MSceneMessage().addCallback( om.MSceneMessage.kAfterNew, self.deferredCauseUndo, 'kAfterNew' )
        om.MSceneMessage().addCallback( om.MSceneMessage.kMayaInitialized, self.deferredCauseUndo, 'kMayaInitialized' )
        om.MSceneMessage().addCallback( om.MSceneMessage.kAfterSave, self.deferredCauseUndo, 'kAfterSave' )
        
#Reset progress in case it wasn't properly stopped on previous run
if firstRun:
    AutoSave().progress(False)
    MoveBackupScriptsToFolder( pm.optionVar[AutoSave.locationName] )