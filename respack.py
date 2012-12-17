#coding=gbk
import os
import subprocess
import zlib
import struct
import math
from collections import namedtuple

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

resPath = "res"

def tga_to_dds(files, format="dxt3"):
    if format in ['dxt1', 'dxt2', 'dxt3', 'dxt4', 'dxt5']:
        os.system("texconv.exe -m 1 -f {0} {1} -o {2}".format(format, files, os.path.dirname(files)))


def get_size(filename):
    output = subprocess.check_output("identify.exe -format %w,%h {0}".format(filename))
    result = map(int, output.split(','))
    return result

def get_offset(path):
    with open(path, 'rb') as f:
        f.seek(3)
        offset_x, offset_y = struct.unpack('2H', f.read(struct.calcsize('2H')))
    return offset_x, offset_y


def crop_image(filename):
    if not os.path.exists(filename):
        return
    dirname = filename[:-4]
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    os.system("convert -crop 256x256 {0} {1}\\%02d.tga".format(filename, dirname))


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


def load_bin(path):
    bin = namedtuple('InfoBin', 'imageFormat frameNum frames')
    bin.imageFormat = PF_DXT3
    bin.frameNum = 0
    bin.frames = {}
    if os.path.exists(path):
        with open(path, 'rb') as f:
            bin.imageFormat = struct.unpack('I', f.read(struct.calcsize('I')))[0]
            assert bin.imageFormat == PF_A8R8G8B8 or bin.imageFormat == PF_DXT1 or bin.imageFormat == PF_DXT3 or bin.imageFormat == PF_DXT5
            bin.frameNum = struct.unpack('I', f.read(struct.calcsize('I')))[0]
            for i in range(bin.frameNum):
                imageNum = struct.unpack('I', f.read(struct.calcsize('I')))[0]
                index = struct.unpack('I', f.read(struct.calcsize('I')))[0]
                images = []
                for j in range(imageNum):
                    image = {}
                    imageInfo = ImageInfo(*struct.unpack(ImageInfo.struct_format,
                        f.read(struct.calcsize(ImageInfo.struct_format))))
                    image['image'] = imageInfo
                    blockNum = imageInfo.blockX * imageInfo.blockY
                    if blockNum > 1:
                        blocks = [BlockInfo(*struct.unpack(BlockInfo.struct_format,
                            f.read(struct.calcsize(BlockInfo.struct_format)))) for k in range(blockNum)]
                        image['blocks'] = blocks
                    images.append(image)
                bin.frames[str(index)] = images
    return bin


def save_bin(binData, path):
    with open(path, 'wb') as f:
        f.write(struct.pack('I', binData.imageFormat))
        f.write(struct.pack('I', len(binData.frames.keys())))
        for index in binData.frames:
            imageNum = len(binData.frames[index])
            f.write(struct.pack('I', imageNum))
            f.write(struct.pack('I', int(index)))
            for i in range(imageNum):
                imageInfo = binData.frames[index][i]['image']
                f.write(struct.pack(ImageInfo.struct_format, *imageInfo))
                blockNum = imageInfo.blockX * imageInfo.blockY
                if blockNum >= 1:
                    blockInfos = binData.frames[index][i]['blocks']
                    for j in range(blockNum):
                        f.write(struct.pack(BlockInfo.struct_format, *blockInfos[j]))


def compress_file(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            buffer = zlib.compress(f.read())
        with open(path, 'wb') as f:
            f.write(buffer)


def decompress_file(path):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            buffer = zlib.decompress(f.read())
        with open(path, 'wb') as f:
            f.write(buffer)


def main():
    for dir in os.listdir(resPath):
        dirPath = os.path.join(resPath, dir)
        if os.path.isdir(dirPath):
            decompress_file(os.path.join(dirPath, "info.bin"))
            bin = load_bin(os.path.join(dirPath, "info.bin"))
            for (dirpath, dirnames, filenames) in os.walk(dirPath):
                if len(dirpath.split(os.sep)) != 3:
                    continue
                index = dirpath.split(os.sep)[-1].lstrip('0')
                images = bin.frames[index] if index in bin.frames else []
                for filename in filenames:
                    if not filename.endswith('.tga'):
                        continue
                    if os.path.exists(os.path.join(dirpath, filename.replace('.tga', '.tex')))\
                    and index in bin.frames:
                        continue
                    image = {}
                    tgapath = os.path.join(dirpath, filename)
                    w, h = get_size(tgapath)
                    offset_x, offset_y = get_offset(tgapath)
                    imageInfo = ImageInfo(
                        width=w + offset_x,
                        height=h + offset_y,
                        dataWidth=w,
                        dataHeight=h,
                        offsetX=offset_x,
                        offsetY=offset_y,
                        blockX=int(math.ceil(w / 256.0)) if w > 256 else 1,
                        blockY=int(math.ceil(h / 256.0)) if h > 256 else 1)
                    if w > 256 or h > 256:
                        crop_image(tgapath)
                        tga_to_dds(os.path.join(dirpath, os.path.basename(tgapath)[:-4], '*.tga'))
                        image['blocks'] = folder_to_tex(os.path.join(dirpath, os.path.basename(tgapath)[:-4]))
                    else:
                        tga_to_dds(tgapath)
                        image['blocks'] = dds_to_tex(tgapath.replace('.tga', '.dds'))
                    image['image'] = imageInfo
                    images.append(image)
                bin.frames[index] = images
            save_bin(bin, os.path.join(dirPath, "info.bin"))
            compress_file(os.path.join(dirPath, "info.bin"))

if __name__ == '__main__':
    main()