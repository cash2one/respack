#coding=gbk
import os
import glob
import shutil
import sys
import math
from helper import *
from collections import namedtuple

WOOOL_FLAG_BLOCK		= 1
WOOOL_FLAG_SMALLTILE	= 2
WOOOL_FLAG_TILE			= 4
WOOOL_FLAG_OBJECT		= 8
WOOOL_FLAG_UNKNOW		= 16

NmpFileHeader = namedtuple('NmpFileHeader', 'size version width height unknown')
NmpFileHeader.struct_format = '4I16s'

def generate_map(mapData, path):
    pass

def trim_object(path):
    os.system('convert -trim {0} {0}'.format(path))
    width, height, raw_width, raw_height, offset_x, offset_y = identify_image(path)
    pageInfo = '{0}x{1}+{2}+{3}'.format(raw_width, raw_height, offset_x - offset_x % 64, offset_y - offset_y % 32)
    extent_width = width + offset_x % 64
    extent_height = height + offset_y % 32 #先算上边
    os.system('convert -gravity southeast -background transparent -extent {0}x{1} -repage {2} {3} {3}'.format(extent_width, extent_height, pageInfo, path))
    extent_height += int(math.ceil(extent_height/32.0)) * 32 - extent_height
    os.system('convert -gravity northwest -background transparent -extent {0}x{1} -repage {2} {3} {3}'.format(extent_width, extent_height, pageInfo, path))

def process_scene(path):
    prefixMap = {'地表' : 'tile', '物件' : 'obj'}
    for dir in filter(lambda dir:os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        mapData = {'name' : dir}
        scenePath = os.path.join(path, dir)
        for (dirPath, dirNames, fileNames) in os.walk(scenePath):
            if len(dirPath.split(os.sep)) != 4:
                continue
            sceneName, resType = dirPath.split(os.sep)[-2:]
            if resType not in prefixMap.keys():
                continue
            destPath = os.path.join(RES_PATH, '{0}_{1}'.format(prefixMap[resType], multi_get_letter(sceneName)))
            if os.path.exists(destPath):
                shutil.rmtree(destPath)
            os.makedirs(destPath)
            for index, name in enumerate(fileNames):
                if name[-4:] not in ['.tga', '.png']:
                    continue
                destFile = os.path.join(destPath, '{0:05d}{1}'.format(index + 1, name[-4:]))
                shutil.copyfile(os.path.join(dirPath, name), destFile)
                if destFile.endswith('.tga'):
                    pngFile = destFile.replace('.tga', '.png')
                    os.system('convert {0} {1}'.format(destFile, pngFile))
                    os.remove(destFile)
                    destFile = pngFile
                if resType == '地表':
                    os.system("convert {0} -crop 0x128 +repage {1}%02d.png".format(destFile, os.path.splitext(destFile)[0]))
                    os.remove(destFile)
                    for file in glob.glob(os.path.join(destPath, "{0:05d}*.png".format(index + 1))):
                        os.system("convert {0} -crop 128x0 +repage  {1}%02d.png".format(file, os.path.splitext(file)[0]))
                        os.remove(file)
                    move_images(os.path.join(destPath, '*.png'))
                elif resType == '物件':
                    trim_object(destFile)
                    os.system("convert {0} +repage -crop 64x0 +repage {1}%04d.png".format(destFile, os.path.splitext(destFile)[0]))
                    os.remove(destFile)
                    for file in glob.glob(os.path.join(destPath, "{0:05d}*.png".format(index + 1))):
                        trim_image(file)
                    move_images(os.path.join(destPath, '*.png'))
        generate_map(mapData, os.path.join(RES_PATH, '{0}.map'.format(multi_get_letter(dir))))


PersonInfo = namedtuple('PersonInfo','name actions')
ActionInfo = namedtuple('ActionInfo', 'imagePackName actionIndex directs')
DirectionInfo = namedtuple('DirectionInfo','images')
personInfos = {}

def process_character(path):
    global personInfos
    prefixMap = {'角色' : 'human', '魔法' : 'magic', '武器' : 'weapon'}
    actionTuple = ('出生', '待机','采集', '跑步', '跳斩', '走路', '物理攻击', '魔法攻击', '骑乘待机', '骑乘跑动')
    resType = path.split(os.sep)[-2]
    if resType  not in prefixMap.keys():
        return
    for  (dirPath, dirNames, fileNames) in os.walk(path):
        if len(dirPath.split(os.sep)) != 5:
            continue
        name, action = dirPath.split(os.sep)[-2:]
        if action not in actionTuple:
            continue
        actionIndex = actionTuple.index(action)
        if name not in personInfos:
            personInfos[name] = PersonInfo(name=name, actions={})
        personInfo = personInfos[name]

        if action not in personInfo.actions:
            personInfo.actions[action] = ActionInfo(imagePackName=os.path.join('data', prefixMap[resType]), actionIndex=actionIndex, directs={})
        actionInfo = personInfo.actions[action]

        for fileName in fileNames:
            if fileName[-4:] not in ['.png', '.tga']:
                continue
            directIndex = int(fileName[0])
            frameIndex = fileName[-6:-4]
            leading_num = find_leading_num(name)
            assert len(leading_num) == 1, '角色目录名不规范，必须以纯数字开头'
            imageIndex = '{0:03d}{1:02d}{2:02d}{3}'.format(int(leading_num[0]), actionIndex, directIndex,frameIndex)
            if directIndex not in actionInfo.directs:
                actionInfo.directs[directIndex] = DirectionInfo(images=[])
            directInfo = actionInfo.directs[directIndex]
            if imageIndex not in directInfo.images:
                directInfo.images.append(imageIndex)
            destPath = os.path.join(RES_PATH, prefixMap[resType], imageIndex)
            if os.path.exists(destPath):
                shutil.rmtree(destPath)
            os.makedirs(destPath)
            destFile = os.path.join(destPath, '000001{0}'.format(fileName[-4:]))
            shutil.copyfile(os.path.join(dirPath, fileName), destFile)
            if destFile.endswith('.tga'):
                pngFile = destFile.replace('.tga', '.png')
                os.system('convert.exe {0} {1}'.format(destFile, pngFile))
                trim_image(pngFile)
                os.remove(destFile)
            else:
                trim_image(destFile)

def export_per_file(path):
    with open(path, 'wb') as f:
        f.write(struct.pack('I', len(personInfos)))
        for personInfo in personInfos.values():
            f.write(struct.pack('32s', personInfo.name))
            f.write(struct.pack('I', len(personInfo.actions)))
            for actionInfo in personInfo.actions.values():
                f.write(struct.pack('32s', actionInfo.imagePackName))
                f.write(struct.pack('I', actionInfo.actionIndex))
                f.write(struct.pack('I', len(actionInfo.directs)))
                for directInfo in actionInfo.directs.values():
                    f.write(struct.pack('I', len(directInfo.images)))
                    for imageIndex in directInfo.images:
                        f.write(struct.pack('I',int(imageIndex)))

def useage():
    print "Usage: cutter.py [scene|char|magic|weapon|npc|monster]"

def main():
    if len(sys.argv) != 2:
        useage()
        exit(0)
    action = sys.argv[1]
    if action == 'scene':
        process_scene(os.path.join(SRC_PATH, '场景'))
    elif action == 'char':
        process_character(os.path.join(SRC_PATH, '角色', '通用'))
        process_character(os.path.join(SRC_PATH, '角色', '战士'))
        process_character(os.path.join(SRC_PATH, '角色', '法师'))
        process_character(os.path.join(SRC_PATH, '角色', '道士'))
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES_PATH, 'human.per'))
    elif action == 'magic':
        process_character(os.path.join(SRC_PATH, '魔法', '战士'))
        process_character(os.path.join(SRC_PATH, '魔法', '法师'))
        process_character(os.path.join(SRC_PATH, '魔法', '道士'))
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES_PATH, 'magic.per'))
    elif action == 'weapon':
        process_character(os.path.join(SRC_PATH, '武器', '战士'))
        process_character(os.path.join(SRC_PATH, '武器', '法师'))
        process_character(os.path.join(SRC_PATH, '武器', '道士'))
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES_PATH, 'weapon.per'))
    elif action == 'npc':
        process_character(os.path.join(SRC_PATH, 'npc', '通用'))
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES_PATH, 'npc.per'))
    elif action == 'monster':
        process_character(os.path.join(SRC_PATH, 'monster', '通用'))
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES_PATH, 'monster.per'))
    else:
        useage()

if __name__ == '__main__':
    main()
