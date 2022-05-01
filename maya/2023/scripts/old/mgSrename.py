import sys
import os
import string
import shutil

def ren (match,repla,path,newDir):
    
    files = os.listdir(path)
    
    if os.path.isdir(path+newDir) == False:
        os.mkdir(path+newDir)
        
    for i in files:
        if match in i:
            name = i.replace(match,repla)
            shutil.copyfile(path+i,path+newDir+'/'+name)
            print 'renamed '+path+i+' to '+path+newDir+'/'+name
    
    print '\n ALL DONE'
		
		
