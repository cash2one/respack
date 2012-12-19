#coding=gbk
import os
import glob
import shutil
import sys
from helper import *

def process_scene(path):
    prefixMap = {'�ر�' : 'tile', '���' : 'obj'}
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
                if resType == '�ر�':
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


def process_character(path, idOffset=0):
    prefixMap = {'��ɫ' : 'human', 'ħ��' : 'magic', '����' : 'weapon'}
    actionTuple = ('����', '����','�ɼ�', '�ܲ�', '��ն', '��·', '������', 'ħ������', '��˴���', '����ܶ�')
    resType = path.split(os.sep)[-2]
    if resType  not in prefixMap.keys():
        return
    for  (dirPath, dirNames, fileNames) in os.walk(path):
        if len(dirPath.split(os.sep)) != 5:
            continue
        name, action = dirPath.split(os.sep)[-2:]
        if action not in actionTuple:
            continue
        for fileName in fileNames:
            destPath = os.path.join(RES, prefixMap[resType],'{0:03d}{1:02d}{2:02d}{3}'.format(idOffset + int(name[:2]), actionTuple.index(action), int(fileName[0]),fileName[-6:-4]))
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

def useage():
    print "Usage: cutter.py [scene|char|magic|weapon]"

def main():
    if len(sys.argv) != 2:
        useage()
        exit(0)
    action = sys.argv[1]
    if action == 'scene':
        process_scene(os.path.join(SRC, '����'))
    elif action == 'char':
        process_character(os.path.join(SRC, '��ɫ', 'սʿ'))
        process_character(os.path.join(SRC, '��ɫ', '��ʦ'), 100)
        process_character(os.path.join(SRC, '��ɫ', '��ʿ'), 200)
    elif action == 'magic':
        process_character(os.path.join(SRC, 'ħ��', 'սʿ'))
        process_character(os.path.join(SRC, 'ħ��', '��ʦ'), 100)
        process_character(os.path.join(SRC, 'ħ��', '��ʿ'), 200)
    elif action == 'weapon':
        process_character(os.path.join(SRC, '����', 'սʿ'))
        process_character(os.path.join(SRC, '����', '��ʦ'), 100)
        process_character(os.path.join(SRC, '����', '��ʿ'), 200)
    else:
        useage()

if __name__ == '__main__':
    main()
