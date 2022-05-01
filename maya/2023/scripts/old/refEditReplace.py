'''
REPLACE THE REFERENCE FILE LOCATION IN A MAYA SCENE
NEED TO KNOW :
    THE LOCATION OF THE MAYA SCENE FILE
    THE LOCATION OF THE NEW REFERENCE FILE
    THE NAME OF THE FOLDER WHERE WE WANT TO MAKE A COPY OF THE MAYA SCENE
'''

import string
import shutil
import os
import sys

def repl(loc, newLoc, file, newDir):
    if not os.path.isdir(loc+newDir):
        os.mkdir(loc+newDir)
    shutil.copy(loc+file,loc+newDir)
    os.rename(loc+newDir+file,loc+newDir+'new_'+file)
    f = open(loc+file,'r')
    lines = f.readlines()
    f.close()
    f = open(loc+newDir+'new_'+file,'w')
    for line in lines:
        if 'file -' in line:
            path = line.split('"')
            if path[5] in line:
                if not newLoc in line :
                    nuovo = line.replace(loc,newLoc)
                    print nuovo
                    f.write(nuovo)
                else:
                    f.write(line)
        else:
            f.write(line)
            #print line
    f.close()
