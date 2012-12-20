#coding=gbk
import os
import glob
import shutil
import sys
from helper import *
from collections import namedtuple

def process_scene(path):
    prefixMap = {'地表' : 'tile', '物件' : 'obj'}
    for dir in filter(lambda dir:os.path.isdir(os.path.join(path, dir)), os.listdir(path)):
        scenePath = os.path.join(path, dir)
        for (dirPath, dirNames, fileNames) in os.walk(scenePath):
            if len(dirPath.split(os.sep)) != 4:
                continue
            sceneName, resType = dirPath.split(os.sep)[-2:]
            if resType not in prefixMap.keys():
                continue
            destPath = os.path.join(RES, '{0}_{1}'.format(prefixMap[resType], multi_get_letter(sceneName)))
            if os.path.exists(destPath):
                shutil.rmtree(destPath)
            os.makedirs(destPath)
            for index, name in enumerate(fileNames):
                destFile = os.path.join(destPath, '{0:05d}.tga'.format(index + 1))
                shutil.copyfile(os.path.join(dirPath, name), destFile)
                if resType == '地表':
                    os.system("convert -crop 0x128 {0} {1}%02d.tga".format(destFile, os.path.splitext(destFile)[0]))
                    os.remove(destFile)
                    for file in glob.glob(os.path.join(destPath, "{0:05d}*.tga".format(index + 1))):
                        os.system("convert -crop 128x0 {0} {1}%02d.tga".format(file, os.path.splitext(file)[0]))
                        os.remove(file)
                    move_images(os.path.join(destPath, '*.tga'))
                else:
                    os.system("convert -crop 64x0 {0} {1}%04d.tga".format(destFile, os.path.splitext(destFile)[0]))
                    os.remove(destFile)
                    for file in glob.glob(os.path.join(destPath, "{0:05d}*.tga".format(index + 1))):
                        pngFile = file.replace('.tga', '.png')
                        os.system('convert {0} {1}'.format(file, pngFile))
                        trim_image(pngFile)
                        os.remove(file)
                    move_images(os.path.join(destPath, '*.png'))


PersonInfo = namedtuple('PersonInfo','name actions')
ActionInfo = namedtuple('ActionInfo', 'imagePackName actionIndex directs')
DirectionInfo = namedtuple('DirectionInfo','images')
personInfos = {}

def process_character(path, idOffset=0):
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
            directIndex = int(fileName[0])
            frameIndex = fileName[-6:-4]
            imageIndex = '{0:03d}{1:02d}{2:02d}{3}'.format(idOffset + int(name[:2]), actionIndex, directIndex,frameIndex)
            if directIndex not in actionInfo.directs:
                actionInfo.directs[directIndex] = DirectionInfo(images=[])
            directInfo = actionInfo.directs[directIndex]
            if imageIndex not in directInfo.images:
                directInfo.images.append(imageIndex)
            destPath = os.path.join(RES, prefixMap[resType], imageIndex)
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
                        f.write(imageIndex)

def useage():
    print "Usage: cutter.py [scene|char|magic|weapon]"

def main():
    if len(sys.argv) != 2:
        useage()
        exit(0)
    action = sys.argv[1]
    if action == 'scene':
        process_scene(os.path.join(SRC, '场景'))
    elif action == 'char':
        process_character(os.path.join(SRC, '角色', '战士'))
        process_character(os.path.join(SRC, '角色', '法师'), 100)
        process_character(os.path.join(SRC, '角色', '道士'), 200)
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES, 'human.per'))
    elif action == 'magic':
        process_character(os.path.join(SRC, '魔法', '战士'))
        process_character(os.path.join(SRC, '魔法', '法师'), 100)
        process_character(os.path.join(SRC, '魔法', '道士'), 200)
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES, 'magic.per'))
    elif action == 'weapon':
        process_character(os.path.join(SRC, '武器', '战士'))
        process_character(os.path.join(SRC, '武器', '法师'), 100)
        process_character(os.path.join(SRC, '武器', '道士'), 200)
        if len(personInfos) != 0:
            export_per_file(os.path.join(RES, 'weapon.per'))
    else:
        useage()

if __name__ == '__main__':
    main()
