#coding=gbk
import os
import zipfile
from helper import RES_PATH

def export_zip(path, exts = ['.tex', '.bin', '.per', '.map']):
    with zipfile.ZipFile(path, 'w') as reszip:
        for base, dirs, files in os.walk(RES_PATH):
            for file in files:
                if file[-4:] in exts:
                    reszip.write(os.path.join(base, file))

if __name__ == '__main__':
    export_zip('res.zip')