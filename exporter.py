#coding=gbk
import os
import sys
import zipfile as zf
from helper import *

def export_res(resFile, exportDir):
    force_directory(exportDir)
    with zf.ZipFile(resFile, 'r') as zip:
        with open(os.path.join(exportDir, 'filelist.zdat'), 'wb') as f:
            infolist = zip.infolist()
            f.write(struct.pack('I', len(infolist)))
            for info in infolist:
                if info.CRC == 0:
                    continue
                f.write(struct.pack('50s', info.filename))
                f.write(struct.pack('50s', str(info.CRC)))
                f.write(struct.pack('I', info.file_size))
                f.write(struct.pack('?', 0))
                with open(os.path.join(exportDir, str(info.CRC)), 'wb') as exportedFile:
                    exportedFile.write(zip.read(info))
    compress_file(os.path.join(exportDir, 'filelist.zdat'))

if __name__ == '__main__':
    resFile = sys.argv[1] if len(sys.argv) == 2 else 'res.zip'
    export_res(resFile, 'update')