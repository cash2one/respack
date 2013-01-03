#coding=gbk
import os
import sys
import zipfile as zf
import fnmatch as fn
from helper import *

#必须下载的文件们
MUST_PRESENT_FILES = ['[!res]*.dll',
                      'client2d.dat',
                      'res/datas/*',
                      'res/map/*.map',
                      'res/tile-01xsc/*',
                      'res/*.sgl',
                      'res/*.dqi',
                      'res/*.fnt'
]

def export_res(filename, dest):
    if not os.path.exists(filename):
        return
    force_directory(dest)
    with zf.ZipFile(filename, 'r') as zipFile:
        with open(os.path.join(dest, 'filelist.zdat'), 'wb') as filelist:
            infolist = [info for info in zipFile.infolist() if info.CRC != 0]
            filelist.write(struct.pack('I', len(infolist)))
            for info in infolist:
                filelist.write(struct.pack('64s', info.filename))
                filelist.write(struct.pack('I', info.CRC))
                filelist.write(struct.pack('I', info.file_size))
                mustFlag = 1 if any([fn.fnmatch(info.filename, pattern) for pattern in MUST_PRESENT_FILES]) else 0
                filelist.write(struct.pack('?', mustFlag))
                print '导出{0}为{1:x}'.format(info.filename, info.CRC)
                exportedFileName = os.path.join(dest, '{0:x}'.format(info.CRC))
                if not os.path.exists(exportedFileName):
                    with open(exportedFileName, 'wb') as exportedFile:
                        exportedFile.write(zipFile.read(info))
    compress_file(os.path.join(dest, 'filelist.zdat'))

if __name__ == '__main__':
    resFileName = sys.argv[1] if len(sys.argv) == 2 else 'res.zip'
    export_res(resFileName, 'update')