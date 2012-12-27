#coding=gbk
__author__ = 'harmy'
import os
import zlib
import struct
import math
from collections import namedtuple, OrderedDict
from helper import *

ImageInfo = namedtuple('ImageInfo',
    """
    width
    height
    dataWidth
    dataHeight
    offsetX
    offsetY
    blockX
    blockY
    """)
ImageInfo.struct_format = '8H'

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
        for ddsfile in os.listdir(path):
            if not ddsfile.endswith('.dds'):
                continue
            w, h = get_size(os.path.join(path, ddsfile))
            with open(os.path.join(path, ddsfile), 'rb') as ddsfd:
                ddsfd.seek(128)
                blockData = zlib.compress(ddsfd.read())
                blockInfo = BlockInfo(
                    width=w,
                    height=h,
                    len=len(blockData))
                buffer += blockData
            blockInfos.append(blockInfo)
        texfile = "{0}\\{1}.tex".format(os.path.abspath(os.path.join(path, os.path.pardir)), os.path.basename(path))
        with open(texfile, 'wb') as texfd:
            texfd.write(buffer)
        return blockInfos


def save_bin(binData, path):
    with open(path, 'wb') as f:
        f.write(struct.pack('I', binData.imageFormat))
        f.write(struct.pack('I', len(binData.frames)))
        for index in binData.frames:
            imageNum = len(binData.frames[index])
            f.write(struct.pack('I', imageNum))
            f.write(struct.pack('I', index))
            for i in range(imageNum):
                imageInfo = binData.frames[index][i]['image']
                f.write(struct.pack(ImageInfo.struct_format, *imageInfo))
                blockNum = imageInfo.blockX * imageInfo.blockY
                blockInfos = binData.frames[index][i]['blocks']
                for j in range(blockNum):
                    f.write(struct.pack(BlockInfo.struct_format, *blockInfos[j]))


def pack_res(path):
    bin = namedtuple('InfoBin', 'imageFormat frameNum frames')
    bin.imageFormat = PF_DXT3
    bin.frameNum = 0
    bin.frames = OrderedDict()
    for (dirPath, dirNames, fileNames) in os.walk(path):
        if len(dirPath.split(os.sep)) != 3:
            continue
        index = int(dirPath.split(os.sep)[-1])
        images = []
        for fileName in fileNames:
            fileExt = os.path.splitext(fileName)[1]
            if fileExt not in ['.tga', '.png']:
                continue
            image = {}
            imagePath = os.path.join(dirPath, fileName)
            w, h = get_size(imagePath)
            raw_width, raw_height, offset_x, offset_y = get_rawsize_offset(imagePath)
            if offset_x < 0 or offset_y < 0:
                continue
            imageInfo = ImageInfo(
                width=raw_width if raw_width else w + offset_x,
                height=raw_height if raw_height else h + offset_y,
                dataWidth=w,
                dataHeight=h,
                offsetX=offset_x,
                offsetY=offset_y,
                blockX=int(math.ceil(w / 256.0)) if w > 256 else 1,
                blockY=int(math.ceil(h / 256.0)) if h > 256 else 1)
            if w > 256 or h > 256:
                crop_image(imagePath)
                to_dds(os.path.join(dirPath, os.path.basename(imagePath)[:-4], '*{}'.format(fileExt)))
                image['blocks'] = folder_to_tex(os.path.join(dirPath, os.path.basename(imagePath)[:-4]))
            else:
                to_dds(imagePath)
                image['blocks'] = dds_to_tex(imagePath.replace(fileExt, '.dds'))
            image['image'] = imageInfo
            images.append(image)
        bin.frames[index] = images
    save_bin(bin, os.path.join(path, "info.bin"))
    compress_file(os.path.join(path, "info.bin"))
