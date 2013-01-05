#coding=gbk
import zipfile

__author__ = 'harmy'
import os
import zlib
import struct
import math
import glob
import multiprocessing as mp
from collections import namedtuple, OrderedDict
from helper import *

ImageInfo = namedtuple('ImageInfo',
    """
    imgOffset
    width
    height
    dataWidth
    dataHeight
    offsetX
    offsetY
    blockX
    blockY
    """)
ImageInfo.struct_format = 'I8H'

BlockInfo = namedtuple('BlockInfo',
    """
    width
    height
    len
    """)
BlockInfo.struct_format = '2HI'

PF_A8R8G8B8 = 21
PF_DXT1 = 827611204
PF_DXT3 = 861165636
PF_DXT5 = 894720068

def to_dds(files, format="dxt3"):
    if format in ['dxt1', 'dxt2', 'dxt3', 'dxt4', 'dxt5']:
        os.system("texconv.exe -m 1 -if NONE -f {0} {1} -o {2}".format(format, files, os.path.dirname(files)))


def dds_to_tex(path):
    if path.endswith('.dds'):
        buffer = ''
        blockInfos = []
        w, h = get_size(path)
        with open(path, 'rb') as ddsfd:
            ddsfd.seek(128)
            blockData = zlib.compress(ddsfd.read())
            blockInfo = BlockInfo(
                width=w,
                height=h,
                len=len(blockData))
            buffer += blockData
        blockInfos.append(blockInfo)
        with open(path.replace('.dds', '.tex'), 'wb') as texfd:
            texfd.write(buffer)
        return blockInfos


def folder_to_tex(path):
    if os.path.isdir(path):
        buffer = ''
        blockInfos = []
        for ddsfile in glob.glob(os.path.join(path, '*.dds')):
            w, h = get_size(ddsfile)
            with open(ddsfile, 'rb') as ddsfd:
                ddsfd.seek(128)
                blockData = zlib.compress(ddsfd.read())
                blockInfo = BlockInfo(
                    width=w,
                    height=h,
                    len=len(blockData))
                buffer += blockData
            blockInfos.append(blockInfo)
        texfile = "{0}\\{1}.tex".format(get_parent_dir(path), os.path.basename(path))
        with open(texfile, 'wb') as texfd:
            texfd.write(buffer)
        return blockInfos


def save_bin(binData, path):
    with open(path, 'wb') as f:
        f.write(struct.pack('I', binData['imageFormat']))
        f.write(struct.pack('I', len(binData['frames'])))
        for index, images in binData['frames'].items():
            imageNum = len(images)
            f.write(struct.pack('I', imageNum))
            f.write(struct.pack('I', index))
            for i in range(imageNum):
                imageInfo = images[i]['image']
                f.write(struct.pack(ImageInfo.struct_format, *imageInfo))
                blockNum = imageInfo.blockX * imageInfo.blockY
                blockInfos = images[i]['blocks']
                for j in range(blockNum):
                    f.write(struct.pack(BlockInfo.struct_format, *blockInfos[j]))


def pack_frame(dirPath, fileNames):
    images = []
    imageOffset = 0
    buffer = ''
    for fileName in fileNames:
        fileExt = os.path.splitext(fileName)[1]
        if fileExt not in ['.png', '.tga']:
            continue
        image = {}
        imagePath = os.path.join(dirPath, fileName)
        w, h = get_size(imagePath)
        raw_width, raw_height, offsetX, offsetY = get_rawsize_offset(imagePath)
        if offsetX < 0 or offsetY < 0:
            continue
        if w > 256 or h > 256:
            crop_image(imagePath)
            to_dds(os.path.join(dirPath, os.path.basename(imagePath)[:-4], '*{}'.format(fileExt)))
            image['blocks'] = folder_to_tex(os.path.join(dirPath, os.path.basename(imagePath)[:-4]))
        else:
            to_dds(imagePath)
            image['blocks'] = dds_to_tex(imagePath.replace(fileExt, '.dds'))
        imageInfo = ImageInfo(
            imgOffset=imageOffset,
            width=raw_width if raw_width else w + offsetX,
            height=raw_height if raw_height else h + offsetY,
            dataWidth=w,
            dataHeight=h,
            offsetX=offsetX,
            offsetY=offsetY,
            blockX=int(math.ceil(w / 256.0)) if w > 256 else 1,
            blockY=int(math.ceil(h / 256.0)) if h > 256 else 1)
        image['image'] = imageInfo
        images.append(image)
        texFile = imagePath.replace(fileExt, '.tex')
        with open(texFile, 'rb') as f:
            buffer += f.read()
        imageOffset += os.path.getsize(texFile)
    packedFile = "{0}\\{1}.tex".format(get_parent_dir(dirPath), dirPath.split(os.sep)[-1])
    with open(packedFile, 'wb') as f:
        f.write(buffer)
    return images


def pack_res(path):
    bin = {'imageFormat': PF_DXT3, 'frames': OrderedDict()}
    pool = mp.Pool(processes=MAX_PROCESS)
    frames = {}
    for (dirPath, dirNames, fileNames) in os.walk(path):
        if len(dirPath.split(os.sep)) != 3:
            continue
        index = int(dirPath.split(os.sep)[-1])
        frames[index] = pool.apply_async(pack_frame, args=(dirPath, fileNames))
    pool.close()
    pool.join()
    for dir in filter(lambda dir: os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        shutil.rmtree(os.path.join(path, dir))
    for index, frame in frames.items():
        bin['frames'][index] = frame.get()
    if len(frames) > 0:
        save_bin(bin, os.path.join(path, "info.bin"))
        compress_file(os.path.join(path, "info.bin"))


def pack_into_zip(path, exts=['.tex', '.bin', '.per', '.map']):
    with zipfile.ZipFile(path, 'w') as reszip:
        for base, dirs, files in os.walk(RES_PATH):
            for file in files:
                if file[-4:] in exts:
                    reszip.write(os.path.join(base, file))

if __name__ == '__main__':
    for dir in filter(lambda dir: os.path.isdir(os.path.join(RES_PATH, dir)), os.listdir(RES_PATH)):
        pack_res(os.path.join(RES_PATH, dir))
    pack_into_zip('res.zip')
