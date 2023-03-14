import hou
import os


def loadHdaLibrary():
    """
    Loads all the HDA files in a folder
    
    @param libPath: HDA library file path
    """
    fullName = os.getenv('HIPFILE')
    fileName = os.getenv('HIPNAME') + '.' + fullName.split('.')[-1]
    libPath = fullName.replace(fileName, 'hda')
    if not os.path.isdir(libPath):
        print('library path:\n' + libPath + '\tdoes not exist')
        return
    
    loaded_files = hou.hda.loadedFiles()
    
    # Get all the .otl files in the directory.
    filetypes = ['.otl', '.hda']
    otl_files = [f for f in os.listdir(libPath) if os.path.splitext(f)[1] in filetypes]
    
    for otl_path in otl_files:
        # backslashes are the devils work
        full_path = os.path.join(libPath, otl_path).replace('\\', '/')
        # If the file isn't already loaded, install it.
        if full_path not in loaded_files:
            print('installing', full_path)
            hou.hda.installFile(full_path)







# import datetime
# import os
# import hou

# def loadHdaLibrary(libPath):
#     """
#     Loads all the HDA files in a folder
    
#     @param libPath: HDA library file path
#     """
    
#     if os.path.isdir(libPath):
#         loaded_files = hou.hda.loadedFiles()
        
#         # Get all the .otl files in the directory.
#         filetypes = ['.otl', '.hda']
#         otl_files = [f for f in os.listdir(libPath) if os.path.splitext(f)[1] in filetypes]
        
#         for otl_path in otl_files:
            
#             # full_path = sep(os.path.join(libPath, otl_path))
#             full_path = os.path.join(libPath, otl_path).replace('\\', '/')
#             # If the file isn't already loaded, install it.
#             if full_path not in loaded_files:
#                 print('installing', full_path)
#                 hou.hda.installFile(full_path)
    
#     else:
#         print('library path\n' + libPath + '\tdoes not exist')


# print ('hello there, i was run at '),
# print (datetime.datetime.now().time())
# loadHdaLibrary(hou.getenv('HIP')+'/hda')