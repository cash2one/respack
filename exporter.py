#coding=gbk
import os
import sys
import zipfile as zf
from helper import *

def export_res(resFile, exportDir):
    force_directory(exportDir)
    with zf.ZipFile(resFile, 'r') as zipFile:
        with open(os.path.join(exportDir, 'filelist.zdat'), 'wb') as filelist:
            infolist = [info for info in zipFile.infolist() if info.CRC != 0]
            filelist.write(struct.pack('I', len(infolist)))
            for info in infolist:
                filelist.write(struct.pack('50s', info.filename))
                filelist.write(struct.pack('I', info.CRC))
                filelist.write(struct.pack('I', info.file_size))
                filelist.write(struct.pack('?', 0))
                print '导出{0}为{1:x}'.format(info.filename, info.CRC)
                with open(os.path.join(exportDir, '{0:x}'.format(info.CRC)), 'wb') as exportedFile:
                    exportedFile.write(zipFile.read(info))
    compress_file(os.path.join(exportDir, 'filelist.zdat'))

if __name__ == '__main__':
    resFile = sys.argv[1] if len(sys.argv) == 2 else 'res.zip'
    export_res(resFile, 'update')