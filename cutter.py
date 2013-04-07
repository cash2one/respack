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
from distutils.dir_util import copy_tree
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
IGNORED_MAPS = ['99通用']
#角色图包类型
CHAR_TYPES = {'角色': 'human', '魔法': 'magic', '武器': 'weapon', 'npc': 'npc'}
NmpFileHeader = namedtuple('NmpFileHeader', 'size version width height unknown')
NmpFileHeader.struct_format = '4I16s'
MapsHeader = namedtuple('MapsHeader', 'name width height version')
MapsHeader.struct_format = '32s3I'
mapData = {
    "name": "",
    "sceneName": "",
    "width": 0,
    "height": 0,
    "tiles": {},
    "objects": {},
    "blocks": {}
}

def generate_map():
    sceneName = mapData["sceneName"]
    if sceneName in IGNORED_MAPS:
        return
    mapDir = os.path.join(RES_PATH, 'map')
    if not os.path.exists(mapDir):
        os.makedirs(mapDir)
    mapPath = os.path.join(mapDir, '__{0}.map'.format(mapData["name"]))
    packIndex = find_leading_num(sceneName)

    #从maps文件中加载阻挡信息
    mapsFile = os.path.join(mapDir, mapData["name"] + ".maps")
    if os.path.exists(mapsFile):
        with open(mapsFile, 'rb') as f:
            mapsHeader = MapsHeader(*struct.unpack(MapsHeader.struct_format, f.read(struct.calcsize(MapsHeader.struct_format))))
            if mapsHeader.width == mapData["width"] and mapsHeader.height == mapData["height"]:
                for y in range(mapsHeader.height):
                    for x in range(mapsHeader.width):
                        flag = struct.unpack('H', f.read(struct.calcsize('H')))[0]
                        if flag & WOOOL_FLAG_BLOCK:
                            mapData["blocks"][(x, y)] = flag

    mapHeader = NmpFileHeader(size=32, version=100, width=mapData["width"], height=mapData["height"], unknown='')
    with open(mapPath, 'wb') as f:
        f.write(struct.pack(NmpFileHeader.struct_format, *mapHeader))
        for y in range(mapHeader.height):
            for x in range(mapHeader.width):
                flag = 0
                if (x, y) in mapData["blocks"]:
                    flag |= WOOOL_FLAG_BLOCK
                if (x, y) in mapData["tiles"]:
                    flag |= WOOOL_FLAG_TILE
                if (x, y) in mapData["objects"]:
                    flag |= WOOOL_FLAG_OBJECT
                f.write(struct.pack('b', flag))
                if (x, y) in mapData["tiles"]:
                    f.write(struct.pack('I', mapData["tiles"][(x, y)] - 1))
                    f.write(struct.pack('I', packIndex - 1))
                if (x, y) in mapData["objects"]:
                    f.write(struct.pack('I', mapData["objects"][(x, y)][0] - 1))
                    f.write(struct.pack('I', packIndex - 1))
                    f.write(struct.pack('I', mapData["objects"][(x, y)][1]))
    compress_file(mapPath)


def generate_smallmap(path, directory, width, height):
    sceneName = path.split(os.sep)[-1]
    if sceneName in IGNORED_MAPS:
        return
    srcFile = os.path.join(path, '地表', '整图.png')
    if not os.path.exists(srcFile):
        return
    print '生成小地图到{0},场景名：{1}'.format(directory, sceneName)
    mapId = find_leading_num(sceneName)
    destFile = os.path.join(RES_PATH, directory, '{0:06d}'.format(mapId), '000001.png')
    ensure_directory(os.path.dirname(destFile))
    shutil.copyfile(srcFile, destFile)
    os.system('convert.exe {0} -resize {1}^>x{2}^> {0}'.format(destFile, width, height))


def generate_bmap(path, directory='bmap'):
    sceneName = path.split(os.sep)[-1]
    if sceneName in IGNORED_MAPS:
        return
    print '生成小地图到{0},场景名：{1}'.format(directory, sceneName)
    srcFile = os.path.join(path, '地表', '整图.png')
    if not os.path.exists(srcFile):
        return
    mapId = find_leading_num(sceneName)
    destFile = os.path.join(RES_PATH, directory, '{0:06d}.png'.format(mapId))
    ensure_directory(os.path.dirname(destFile))
    shutil.copyfile(srcFile, destFile)
    os.system('convert.exe {0} -resize 6.25%% {1}'.format(destFile, destFile))
    os.system('convert {0} {1}'.format(destFile, destFile.replace(".png", ".jpg")))
    os.remove(destFile)


def process_tile(path):
    global mapData
    sceneName = path.split(os.sep)[-2]
    mapName = multi_get_letter(sceneName)
    print '正在处理{0}地表...'.format(sceneName)
    mapData["name"] = mapName
    mapData["sceneName"] = sceneName
    destPath = os.path.join(RES_PATH, 'tile-{0}'.format(mapName))
    force_directory(destPath)
    for index, tileFile in enumerate(glob.glob(os.path.join(path, '*.png'))):
        destFile = os.path.join(destPath, '{0:02d}.png'.format(index + 1))
        shutil.copyfile(tileFile, destFile)
        imageWidth, imageHeight = get_size(destFile)
        mapData["width"] = imageWidth / 64
        mapData["height"] = imageHeight / 32
        os.system("convert {0} -crop 0x{1} +repage {2}%02d.png".format(destFile, TILE_HEIGHT, os.path.splitext(destFile)[0]))
        os.remove(destFile)
        for file in glob.glob(os.path.join(destPath, "{0:02d}??.png".format(index + 1))):
            os.system("convert {0} -crop {1}x0 +repage  {2}%02d-000001.png".format(file, TILE_WIDTH, os.path.splitext(file)[0]))
            os.remove(file)
        for file in glob.glob(os.path.join(destPath, "{0:02d}????-000001.png".format(index + 1))):
            imageIndex = os.path.basename(file)[:-11]
            x, y = (TILE_WIDTH / 64) * int(imageIndex[4:6]), (TILE_HEIGHT / 32) * int(imageIndex[2:4])
            mapData["tiles"][(x, y)] = int(imageIndex)
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
    global mapData
    sceneName = path.split(os.sep)[-2]
    print '正在处理{0}物件...'.format(sceneName)
    destPath = os.path.join(RES_PATH, 'obj-{0}'.format(multi_get_letter(sceneName)))
    force_directory(destPath)
    for dir in filter(lambda dir: os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        dirIndex = find_leading_num(dir)
        files_grabbed = []
        for files in ['*.tga', '*.png']:
            files_grabbed.extend(glob.glob(os.path.join(path, dir, files)))
        for frameIndex, frameFile in enumerate(files_grabbed):
            destFile = os.path.join(destPath, '{0:04d}-{1:06d}{2}'.format(dirIndex, frameIndex + 1, frameFile[-4:]))
            shutil.copyfile(frameFile, destFile)
            destFile = tga_to_png(destFile)
            trim_object(destFile)
            os.system("convert {0} +repage -crop 64x0 +repage {1}%02d-{2:06d}.png".format(destFile,
                destFile[:-11], frameIndex + 1))
            w, h, raw_width, raw_height, offset_x, offset_y = identify_image(destFile)
            for i, file in enumerate(glob.glob(os.path.join(destPath, "{0:04d}??-*.png".format(dirIndex)))):
                trim_image(file)
                _, h1, _, _, _, oy = identify_image(file)
                baseOffset = round(math.ceil((h - h1 - oy) / 32.0))
                x, y = offset_x / 64 + i, (h + offset_y) / 32 - 1 - baseOffset
                imageIndex = '{0}{1:02d}'.format(destFile.split(os.sep)[-1][:-11], i)
                mapData["objects"][(x, y)] = (int(imageIndex), h - baseOffset * 32)
            os.remove(destFile)
        put_images_into_folder(os.path.join(destPath, "{0:04d}??-*.png".format(dirIndex)))


def process_map(path):
    process_tile(os.path.join(path, '地表'))
    process_object(os.path.join(path, '物件'))
    generate_map()
    generate_smallmap(path, 'timap', 640, 320)
    generate_smallmap(path, 'mmap', 640, 320)
    generate_bmap(path)


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
    actionTuple = ('出生', '待机', '采集', '跑步', '跳斩', '走路', '物理攻击', '魔法攻击', '骑乘待机', '骑乘跑动', '受击', '死亡', '物攻待机', '魔攻待机')
    if action not in actionTuple:
        return None
    actionIndex = actionTuple.index(action)
    actionInfo = ActionInfo(imagePackName=packName, actionIndex=actionIndex, directs=OrderedDict())
    fileNames = sorted([fileName for fileName in fileNames if fileName[-4:] in ['.tga', '.png']])
    for index, fileName in enumerate(fileNames):
        directIndex = int(fileName[:2])
        leading_num = find_leading_num(name)
        if len(str(leading_num)) == 6:
            imageIndex = str(leading_num)
        else:
            imageIndex = '{0:03d}{1:03d}'.format(leading_num, actionIndex)
        if directIndex not in actionInfo.directs:
            actionInfo.directs[directIndex] = DirectionInfo(images=[])
        directInfo = actionInfo.directs[directIndex]
        directInfo.images.append((int(imageIndex), index))
        destPath = os.path.join(RES_PATH, packName, imageIndex)
        if not os.path.exists(destPath):
            os.makedirs(destPath)
        destFile = os.path.join(destPath, fileName)
        shutil.copyfile(os.path.join(dirPath, fileName), destFile)
        if dirPath.split(os.sep)[-3] == '传世':
            continue
        destFile = tga_to_png(destFile)
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
                        f.write(struct.pack('I', imageIndex[0]))
                        f.write(struct.pack('H', imageIndex[1]))


def useage():
    print "Usage: cutter.py [场景|角色|魔法|武器|npc|ui|timap_mmap|c]"


def main():
    if len(sys.argv) != 2:
        useage()
        exit(-1)
    startTime = time.time()
    SRC_PATH, resType = sys.argv[1].rsplit(os.sep, 1)
    if not os.path.isdir(SRC_PATH):
        exit(-1)
    if resType == '场景':
        process_scene(os.path.join(SRC_PATH, resType))
        for dir in filter(lambda dir: os.path.isdir(os.path.join(RES_PATH, dir)) and
                                      (dir.startswith('tile-') or dir.startswith('obj-')), os.listdir(RES_PATH)):
            pack_res(os.path.join(RES_PATH, dir))
    elif resType in CHAR_TYPES:
        personInfos = {}
        force_directory(os.path.join(RES_PATH, CHAR_TYPES[resType]))
        for dir in ['通用', '战士', '法师', '道士', '传世', '怪物']:
            process_character(os.path.join(SRC_PATH, resType, dir), resType, personInfos)
        if len(personInfos) != 0:
            perPath = os.path.join(RES_PATH, CHAR_TYPES[resType], '{0}.per'.format(CHAR_TYPES[resType]))
            export_per_file(perPath, personInfos)
            compress_file(perPath)
            pack_res(os.path.join(RES_PATH, CHAR_TYPES[resType]))
    elif resType == 'ui':
        copy_tree(os.path.join(SRC_PATH, '传世UI'), RES_PATH)
    elif resType == 'timap_mmap':
        SRC_PATH = os.path.join(SRC_PATH, '场景')
        for dir in filter(lambda dir: os.path.isdir(os.path.join(SRC_PATH, dir)), os.listdir(SRC_PATH)):
            path = os.path.join(SRC_PATH, dir)
            generate_smallmap(path, 'timap', 640, 320)
            generate_smallmap(path, 'mmap', 640, 320)
            generate_bmap(path)
    else:
        useage()
    print '总共耗时：{0}'.format(datetime.timedelta(seconds=time.time() - startTime))
    winsound.PlaySound(zlib.decompress(base64.b64decode(COMPLETE_SOUND_DATA)), winsound.SND_MEMORY)

if __name__ == '__main__':
    main()