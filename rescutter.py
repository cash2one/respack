#coding=gbk
import os
import glob
import shutil
import sys
from helper import *

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
                    os.system("convert -crop 64x0 {0} {1}%02d00.tga".format(destFile, os.path.splitext(destFile)[0]))
                    os.remove(destFile)
                    for file in glob.glob(os.path.join(destPath, "{0:05d}*.tga".format(index + 1))):
                        pngFile = file.replace('.tga', '.png')
                        os.system('convert {0} {1}'.format(file, pngFile))
                        trim_image(pngFile)
                        os.remove(file)
                    move_images(os.path.join(destPath, '*.png'))


def useage():
    print "Usage: rescutter.py [scene|char|magic|weapon|all]"

def main():
    if len(sys.argv) != 2:
        useage()
        exit(0)
    if sys.argv[1] == 'scene':
        process_scene(os.path.join(SRC, '场景'))
    else:
        useage()

if __name__ == '__main__':
    main()
