#coding=gbk
import base64
import os
import glob
import shutil
import sys
import math
import winsound
import multiprocessing as mp
from collections import namedtuple, OrderedDict
import time
import datetime
from packer import pack_res
from helper import *

WOOOL_FLAG_BLOCK = 1
WOOOL_FLAG_SMALLTILE = 2
WOOOL_FLAG_TILE = 4
WOOOL_FLAG_OBJECT = 8
WOOOL_FLAG_UNKNOW = 16

#特定的地图包不生成地图文件
IGNORED_MAPS = []
#角色图包类型
CHAR_TYPES = {'角色': 'human', '魔法': 'magic', '武器': 'weapon', 'npc': 'npc'}
NmpFileHeader = namedtuple('NmpFileHeader', 'size version width height unknown')
NmpFileHeader.struct_format = '4I16s'

def generate_map(sceneName, path):
    if sceneName in IGNORED_MAPS:
        return
    tileFile = os.path.join(RES_PATH, 'tile-{0}'.format(multi_get_letter(sceneName)), '01.png')
    if not os.path.exists(tileFile):
        return
    packIndex = find_leading_num(sceneName)
    tileData = {}
    objectData = {}
    imageWidth, imageHeight = identify_image(tileFile)[:2]
    os.remove(tileFile)
    mapHeader = NmpFileHeader(size=32, version=100, width=imageWidth / 64, height=imageHeight / 32, unknown='')

    for y in range(mapHeader.height):
        for x in range(mapHeader.width):
            if (y % 4 == 0) and (x % 2 == 0):
                imageIndex = '{0:02d}{1:02d}{2:02d}'.format(1, y / 4, x / 2)
                tileData[(x, y)] = int(imageIndex)

    for file in glob.glob(os.path.join(RES_PATH, 'obj-{0}'.format(multi_get_letter(sceneName)), '*.png')):
        if not file.endswith('-000001.png'):
            os.remove(file)
            continue
        w, h, raw_width, raw_height, offset_x, offset_y = identify_image(file)
        for i in range(int(math.ceil(w / 64.0))):
            x, y = offset_x / 64 + i, (h + offset_y) / 32 - 1
            imageIndex = '{0}{1:02d}'.format(file.split(os.sep)[-1][:-11], i)
            objectData[(x, y)] = (int(imageIndex), h)
        os.remove(file)

    with open(path, 'wb') as f:
        f.write(struct.pack(NmpFileHeader.struct_format, *mapHeader))
        for y in range(mapHeader.height):
            for x in range(mapHeader.width):
                flag = 0
                if (x, y) in tileData:
                    flag |= WOOOL_FLAG_TILE
                if (x, y) in objectData:
                    flag |= WOOOL_FLAG_OBJECT
                f.write(struct.pack('b', flag))
                if (x, y) in tileData:
                    f.write(struct.pack('I', tileData[(x, y)] - 1))
                    f.write(struct.pack('I', packIndex - 1))
                if (x, y) in objectData:
                    f.write(struct.pack('I', objectData[(x, y)][0] - 1))
                    f.write(struct.pack('I', packIndex - 1))
                    f.write(struct.pack('I', objectData[(x, y)][1]))


def generate_timap(sceneName, mapId):
    destPath = os.path.join(RES_PATH, 'timap', '{0:06d}'.format(mapId))
    force_directory(destPath)
    tileFile = os.path.join(RES_PATH, 'tile-{0}'.format(multi_get_letter(sceneName)), '01.png')
    if not os.path.exists(tileFile):
        return
    width, height = get_size(tileFile)
    ratio = width / 640
    resize_param = 'x320' if height / ratio < 320 else '640'
    os.system('convert.exe {0} -resize {1} {2}'.format(tileFile, resize_param, os.path.join(destPath, '000001.png')))


def generate_mmap(sceneName, mapId):
    pass


def process_tile(path):
    sceneName = path.split(os.sep)[-2]
    print '正在处理{0}地表...'.format(sceneName)
    destPath = os.path.join(RES_PATH, 'tile-{0}'.format(multi_get_letter(sceneName)))
    force_directory(destPath)
    for index, tileFile in enumerate(glob.glob(os.path.join(path, '*.png'))):
        destFile = os.path.join(destPath, '{0:02d}.png'.format(index + 1))
        shutil.copyfile(tileFile, destFile)
        os.system("convert {0} -crop 0x128 +repage {1}%02d.png".format(destFile, os.path.splitext(destFile)[0]))
        for file in glob.glob(os.path.join(destPath, "{0:02d}??.png".format(index + 1))):
            os.system("convert {0} -crop 128x0 +repage  {1}%02d-000001.png".format(file, os.path.splitext(file)[0]))
            os.remove(file)
        put_images_into_folder(os.path.join(destPath, "{0:02d}????-*.png".format(index + 1)))


def trim_object(path):
    trim_image(path, False)
    width, height, raw_width, raw_height, offset_x, offset_y = identify_image(path)
    pageInfo = '{0}x{1}+{2}+{3}'.format(raw_width, raw_height, offset_x - offset_x % 64, offset_y - offset_y % 32)
    extent_width = width + offset_x % 64
    extent_height = height + offset_y % 32
    os.system(
        'convert -gravity southeast -background transparent -extent {0}x{1} -repage {2} {3} {3}'.format(extent_width,
            extent_height, pageInfo, path))
    extent_height += int(math.ceil(extent_height / 32.0)) * 32 - extent_height
    os.system(
        'convert -gravity northwest -background transparent -extent {0}x{1} -repage {2} {3} {3}'.format(extent_width,
            extent_height, pageInfo, path))


def process_object(path):
    sceneName = path.split(os.sep)[-2]
    print '正在处理{0}物件...'.format(sceneName)
    destPath = os.path.join(RES_PATH, 'obj-{0}'.format(multi_get_letter(sceneName)))
    force_directory(destPath)
    for dir in filter(lambda dir: os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        dirIndex = find_leading_num(dir)
        for frameIndex, frameFile in enumerate(glob.glob(os.path.join(path, dir, '*.png'))):
            destFile = os.path.join(destPath, '{0:04d}-{1:06d}.png'.format(dirIndex, frameIndex + 1))
            shutil.copyfile(frameFile, destFile)
            trim_object(destFile)
            os.system("convert {0} +repage -crop 64x0 +repage {1}%02d-{2:06d}.png".format(destFile,
                destFile[:-11], frameIndex + 1))
            for file in glob.glob(os.path.join(destPath, "{0:04d}??-*.png".format(dirIndex))):
                trim_image(file)
        put_images_into_folder(os.path.join(destPath, "{0:04d}??-*.png".format(dirIndex)))


def process_map(path):
    process_tile(os.path.join(path, '地表'))
    process_object(os.path.join(path, '物件'))
    sceneName = path.split(os.sep)[-1]
    mapId = find_leading_num(sceneName)
    generate_timap(sceneName, mapId)
    generate_mmap(sceneName, mapId)
    mapPath = os.path.join(RES_PATH, 'map')
    if not os.path.exists(mapPath):
        os.makedirs(mapPath)
    generate_map(sceneName, os.path.join(mapPath, '__{0}.map'.format(multi_get_letter(sceneName))))


def process_scene(path):
    pool = mp.Pool(processes=MAX_PROCESS)
    for dir in filter(lambda dir: os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        pool.apply_async(process_map, (os.path.join(path, dir), ))
    pool.close()
    pool.join()


PersonInfo = namedtuple('PersonInfo', 'name actions')
ActionInfo = namedtuple('ActionInfo', 'imagePackName actionIndex directs')
DirectionInfo = namedtuple('DirectionInfo', 'images')

def process_action(dirPath, fileNames, name, action, packName):
    print '正在处理{0}...'.format(dirPath)
    actionTuple = ('出生', '待机', '采集', '跑步', '跳斩', '走路', '物理攻击', '魔法攻击', '骑乘待机', '骑乘跑动')
    if action not in actionTuple:
        return None
    actionIndex = actionTuple.index(action)
    actionInfo = ActionInfo(imagePackName=packName, actionIndex=actionIndex, directs=OrderedDict())
    fileNames = [fileName for fileName in fileNames if fileName[-4:] in ['.tga', '.png']]
    for index, fileName in enumerate(fileNames):
        directIndex = int(fileName[:2])
        leading_num = find_leading_num(name)
        imageIndex = '{0:03d}{1:03d}'.format(leading_num, actionIndex)
        if directIndex not in actionInfo.directs:
            actionInfo.directs[directIndex] = DirectionInfo(images=[])
        directInfo = actionInfo.directs[directIndex]
        if imageIndex not in directInfo.images:
            directInfo.images.append((imageIndex, index))
        destPath = os.path.join(RES_PATH, packName, imageIndex)
        if not os.path.exists(destPath):
            os.makedirs(destPath)
        destFile = os.path.join(destPath, fileName)
        shutil.copyfile(os.path.join(dirPath, fileName), destFile)
        if destFile.endswith('.tga'):
            pngFile = destFile.replace('.tga', '.png')
            os.system('convert {0} {1}'.format(destFile, pngFile))
            destFile = pngFile
        trim_image(destFile)
    return actionInfo


def process_character(path, resType, personInfos):
    pool = mp.Pool(processes=MAX_PROCESS)
    deferedResult = {}
    for  (dirPath, dirNames, fileNames) in os.walk(path):
        if len(os.path.relpath(dirPath, path).split(os.sep)) !=2:
            continue
        name, action = dirPath.split(os.sep)[-2:]
        deferedResult[(name, action)] = pool.apply_async(process_action, (dirPath, fileNames, name, action, CHAR_TYPES[resType]))
    pool.close()
    pool.join()
    for (name, action), defered in deferedResult.items():
        actionInfo = defered.get()
        if actionInfo is not None:
            if name not in personInfos:
                personInfos[name] = PersonInfo(name=name, actions=OrderedDict())
            personInfos[name].actions[action] = actionInfo


def export_per_file(path, personInfos):
    with open(path, 'wb') as f:
        f.write(struct.pack('I', len(personInfos)))
        for name, personInfo in sorted(personInfos.items()):
            f.write(struct.pack('32s', personInfo.name))
            f.write(struct.pack('I', len(personInfo.actions)))
            for actionInfo in personInfo.actions.values():
                f.write(struct.pack('32s', actionInfo.imagePackName))
                f.write(struct.pack('I', actionInfo.actionIndex))
                f.write(struct.pack('I', len(actionInfo.directs)))
                for directInfo in actionInfo.directs.values():
                    f.write(struct.pack('I', len(directInfo.images)))
                    for imageIndex in directInfo.images:
                        f.write(struct.pack('I', int(imageIndex[0])))
                        f.write(struct.pack('H', int(imageIndex[1])))


def useage():
    print "Usage: cutter.py [场景|角色|魔法|武器|npc]"


def main():
    if len(sys.argv) != 2:
        useage()
        exit(-1)
    if not os.path.isdir(sys.argv[1]):
        exit(-1)
    startTime = time.time()
    SRC_PATH, resType = sys.argv[1].rsplit(os.sep, 1)
    if resType == '场景':
        process_scene(os.path.join(SRC_PATH, resType))
        for dir in filter(lambda dir: os.path.isdir(os.path.join(RES_PATH, dir)) and
                                      (dir.startswith('tile-') or dir.startswith('obj-')), os.listdir(RES_PATH)):
            pack_res(os.path.join(RES_PATH, dir))
    elif resType in CHAR_TYPES:
        personInfos = {}
        force_directory(os.path.join(RES_PATH, CHAR_TYPES[resType]))
        for dir in ['通用', '战士', '法师', '道士']:
            process_character(os.path.join(SRC_PATH, resType, dir), resType, personInfos)
        if len(personInfos) != 0:
            datasPath = os.path.join(RES_PATH, 'datas')
            if not os.path.exists(datasPath):
                os.makedirs(datasPath)
            export_per_file(os.path.join(datasPath, '{0}.per'.format(CHAR_TYPES[resType])), personInfos)
            pack_res(os.path.join(RES_PATH, CHAR_TYPES[resType]))
    else:
        useage()
    print '总共耗时：{0}'.format(datetime.timedelta(seconds=time.time() - startTime))
    winsound.PlaySound(zlib.decompress(base64.b64decode(COMPLETE_SOUND_DATA)), winsound.SND_MEMORY)

if __name__ == '__main__':
    main()