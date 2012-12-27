#coding=gbk
import os
import glob
import shutil
import sys
import math
import winsound
from multiprocessing import Pool, Manager, cpu_count
from collections import namedtuple, OrderedDict
from packer import pack_res
from helper import *

WOOOL_FLAG_BLOCK = 1
WOOOL_FLAG_SMALLTILE = 2
WOOOL_FLAG_TILE = 4
WOOOL_FLAG_OBJECT = 8
WOOOL_FLAG_UNKNOW = 16

#最大并发进程数=cpu数量
MAX_PROCESS = cpu_count()
#特定的地图包不生成地图文件
IGNORED_MAPS = []

NmpFileHeader = namedtuple('NmpFileHeader', 'size version width height unknown')
NmpFileHeader.struct_format = '4I16s'

def generate_map(sceneName, path):
    if sceneName in IGNORED_MAPS:
        return
    tileFile = os.path.join(RES_PATH, 'tile-{0}'.format(multi_get_letter(sceneName)), '00001.png')
    if not os.path.exists(tileFile):
        return
    packIndex = find_leading_num(sceneName)
    assert len(packIndex) == 1, '地图目录名不规范，必须以纯数字开头'
    tileData = {}
    objectData = {}
    imageWidth, imageHeight = identify_image(tileFile)[:2]
    os.remove(tileFile)
    mapHeader = NmpFileHeader(size=32, version=100, width=imageWidth / 64, height=imageHeight / 32, unknown='')

    for y in range(mapHeader.height):
        for x in range(mapHeader.width):
            if (y % 4 == 0) and (x % 2 == 0):
                imageIndex = '{0:05d}{1:02d}{2:02d}'.format(1, y / 4, x / 2)
                tileData[(x, y)] = int(imageIndex)

    for file in glob.glob(os.path.join(RES_PATH, 'obj-{0}'.format(multi_get_letter(sceneName)), '*.png')):
        if not file.endswith('-000001.png'):
            os.remove(file)
            continue
        w, h, raw_width, raw_height, offset_x, offset_y = identify_image(file)
        for i in range(int(math.ceil(w / 64.0))):
            x, y = offset_x / 64 + i, (h + offset_y) / 32 - 1
            imageIndex = '{0}{1:02d}{2:02d}'.format(file.split(os.sep)[-1][:-11], 0, i)
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
                    f.write(struct.pack('I', int(packIndex[0]) - 1))
                if (x, y) in objectData:
                    f.write(struct.pack('I', objectData[(x, y)][0] - 1))
                    f.write(struct.pack('I', int(packIndex[0]) - 1))
                    f.write(struct.pack('I', objectData[(x, y)][1]))


def process_tile(path):
    sceneName = path.split(os.sep)[-2]
    print '正在处理{0}地表...'.format(sceneName)
    destPath = os.path.join(RES_PATH, 'tile-{0}'.format(multi_get_letter(sceneName)))
    force_directory(destPath)
    for index, tileFile in enumerate(glob.glob(os.path.join(path, '*.png'))):
        destFile = os.path.join(destPath, '{0:05d}.png'.format(index + 1))
        shutil.copyfile(tileFile, destFile)
        os.system("convert {0} -crop 0x128 +repage {1}%02d.png".format(destFile, os.path.splitext(destFile)[0]))
        for file in glob.glob(os.path.join(destPath, "{0:05d}??.png".format(index + 1))):
            os.system("convert {0} -crop 128x0 +repage  {1}%02d-000001.png".format(file, os.path.splitext(file)[0]))
            os.remove(file)
        put_images_into_folder(os.path.join(destPath, "{0:05d}????-*.png".format(index + 1)))


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
        assert len(dirIndex) == 1, '物件目录名不规范，必须以纯数字开头'
        for frameIndex, frameFile in enumerate(glob.glob(os.path.join(path, dir, '*.png'))):
            destFile = os.path.join(destPath, '{0:05d}-{1:06d}.png'.format(int(dirIndex[0]), frameIndex + 1))
            shutil.copyfile(frameFile, destFile)
            trim_object(destFile)
            os.system("convert {0} +repage -crop 64x0 +repage {1}%04d-{2:06d}.png".format(destFile,
                os.path.splitext(destFile)[0][:-7], frameIndex + 1))
            for file in glob.glob(os.path.join(destPath, "{0:05d}00*.png".format(int(dirIndex[0])))):
                trim_image(file)
        put_images_into_folder(os.path.join(destPath, "{0:05d}00*.png".format(int(dirIndex[0]))))


def process_map(path):
    process_tile(os.path.join(path, '地表'))
    process_object(os.path.join(path, '物件'))
    sceneName = path.split(os.sep)[-1]
    mapPath = os.path.join(RES_PATH, 'map')
    if not os.path.exists(mapPath):
        os.makedirs(mapPath)
    generate_map(sceneName, os.path.join(mapPath, '__{0}.map'.format(multi_get_letter(sceneName))))


def process_scene(path):
    pool = Pool(processes=MAX_PROCESS)
    for dir in filter(lambda dir: os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        pool.apply_async(process_map, (os.path.join(path, dir), ))
    pool.close()
    pool.join()


PersonInfo = namedtuple('PersonInfo', 'name actions')
ActionInfo = namedtuple('ActionInfo', 'imagePackName actionIndex directs')
DirectionInfo = namedtuple('DirectionInfo', 'images')

def process_character(path, packName, personInfos):
    print '正在处理{1}{0}...'.format(*path.split(os.sep)[-2:])
    actionTuple = ('出生', '待机', '采集', '跑步', '跳斩', '走路', '物理攻击', '魔法攻击', '骑乘待机', '骑乘跑动')
    for  (dirPath, dirNames, fileNames) in os.walk(path):
        if len(dirPath.split(os.sep)) != 5:
            continue
        name, action = dirPath.split(os.sep)[-2:]
        if action not in actionTuple:
            continue
        actionIndex = actionTuple.index(action)
        if name not in personInfos:
            personInfos[name] = PersonInfo(name=name, actions=OrderedDict())
        personInfo = personInfos[name]

        if action not in personInfo.actions:
            personInfo.actions[action] = ActionInfo(imagePackName=packName, actionIndex=actionIndex,
                directs=OrderedDict())
        actionInfo = personInfo.actions[action]

        for fileName in fileNames:
            if fileName[-4:] not in ['.png', '.tga']:
                continue
            directIndex = int(fileName[0])
            frameIndex = fileName[-6:-4]
            leading_num = find_leading_num(name)
            assert len(leading_num) == 1, '角色目录名不规范，必须以纯数字开头'
            imageIndex = '{0:03d}{1:02d}{2:02d}{3}'.format(int(leading_num[0]), actionIndex, directIndex, frameIndex)
            if directIndex not in actionInfo.directs:
                actionInfo.directs[directIndex] = DirectionInfo(images=[])
            directInfo = actionInfo.directs[directIndex]
            if imageIndex not in directInfo.images:
                directInfo.images.append(imageIndex)
            destPath = os.path.join(RES_PATH, packName, imageIndex)
            force_directory(destPath)
            destFile = os.path.join(destPath, '000001{0}'.format(fileName[-4:]))
            shutil.copyfile(os.path.join(dirPath, fileName), destFile)
            if destFile.endswith('.tga'):
                pngFile = destFile.replace('.tga', '.png')
                os.system('convert.exe {0} {1}'.format(destFile, pngFile))
                trim_image(pngFile)
                os.remove(destFile)
            else:
                trim_image(destFile)


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
                        f.write(struct.pack('I', int(imageIndex)))


def useage():
    print "Usage: cutter.py [scene|human|magic|weapon|npc]"


def main():
    if len(sys.argv) != 2:
        useage()
        exit(0)
    action = sys.argv[1]
    dirNames = { 'human': '角色', 'magic': '魔法', 'weapon': '武器', 'npc': 'npc'}
    if action == 'scene':
        process_scene(os.path.join(SRC_PATH, '场景'))
        pool = Pool(processes=MAX_PROCESS)
        for dir in filter(lambda dir: os.path.isdir(os.path.join(RES_PATH, dir)) and
                                      (dir.startswith('tile-') or dir.startswith('obj-')), os.listdir(RES_PATH)):
            pool.apply_async(pack_res, (os.path.join(RES_PATH, dir), ))
        pool.close()
        pool.join()
    elif action in dirNames:
        manager = Manager()
        personInfos = manager.dict()
        pool = Pool(processes=MAX_PROCESS)
        for dir in ['战士', '法师', '道士', '通用']:
            pool.apply_async(process_character, args=(os.path.join(SRC_PATH, dirNames[action], dir), action, personInfos))
        pool.close()
        pool.join()
        if len(personInfos) != 0:
            datasPath = os.path.join(RES_PATH, 'datas')
            if not os.path.exists(datasPath):
                os.makedirs(datasPath)
            export_per_file(os.path.join(datasPath, '{0}.per'.format(action)), personInfos)
            pack_res(os.path.join(RES_PATH, action))
    else:
        useage()

if __name__ == '__main__':
    main()
    winsound.PlaySound('complete.wav', winsound.SND_FILENAME)
