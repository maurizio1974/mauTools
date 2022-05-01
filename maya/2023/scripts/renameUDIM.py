import os

def renameUDIM(path, ext):
    images = os.listdir(path)
    ext = '.' + ext
    for f in images:
        if f.endswith(ext):
            full = os.path.join(path, f).replace('\\', '/')
            index = f.split('_u')[-1].split('_')[0], f.split('_u')[-1].split('_v')[-1].split('.')[0]
            index = list(index)
            value, name = '', ''
            if index[1] != '2':
                value = int(index[0]) + 1000
                # print int(index[0]) + 1000, index
            elif index[1] == '2':
                value = int(index[0]) + 1010
                # print int(index[0]) + 1010, index
            base  = f.split('_')[0]
            name = base + '.' + str(value) + ext
            old = os.path.join(path, f).replace('\\', '/')
            new = os.path.join(path, name).replace('\\', '/')
            if os.path.isfile(old):
                print f + ' --->>> ' + name
                os.rename(old, new)
