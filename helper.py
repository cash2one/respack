#coding=gbk
import glob
import os
import shutil
import struct
import subprocess
import zlib
import re
from multiprocessing import  cpu_count

SRC_PATH = '.'
RES_PATH = 'res'
TILE_WIDTH = 512
TILE_HEIGHT = 512
#最大并进程数
MAX_PROCESS = cpu_count() * 2
COMPLETE_SOUND_DATA = """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"""

def tga_to_png(tgaFile):
    if tgaFile.endswith('.tga'):
        pngFile = tgaFile.replace('.tga', '.png')
        os.system('convert {0} {1}'.format(tgaFile, pngFile))
        os.remove(tgaFile)
        return pngFile
    return tgaFile

def find_leading_num(name):
    result = re.findall(r'^\d+', name)
    assert len(result) == 1, '目录名不规范，必须以纯数字开头'
    return int(result[0])


def compress_file(path):
    if os.path.exists(path):
        fileSize = os.path.getsize(path)
        with open(path, 'rb') as originFile:
            buffer = originFile.read()
        if buffer[:4] != 'ZLIB':   
            with open(path, 'wb') as compressedFile:
                compressedFile.write(struct.pack('4s', 'ZLIB'))
                compressedFile.write(struct.pack('I', fileSize))
                compressedFile.write(zlib.compress(buffer))


def identify_image(filename):
    output = subprocess.check_output('identify.exe -format %w,%h,%g {0}'.format(filename))
    return [int(item) for item in re.search(r'(\d+),(\d+),(\d+)x(\d+)([\+\-]\d+)([\+\-]\d+)', output).groups()]


def get_parent_dir(path):
    return os.path.abspath(os.path.join(path, os.path.pardir))


def get_size(filename):
    return identify_image(filename)[:2]


def get_rawsize_offset(filename):
    if not os.path.exists(filename):
        return (0,) * 4
    if filename.endswith('.tga'):
        with open(filename, 'rb') as f:
            f.seek(3)
            offset_x, offset_y = struct.unpack('2H', f.read(struct.calcsize('2H')))
            f.seek(8)
            raw_width, raw_height = struct.unpack('2H', f.read(struct.calcsize('2H')))
    elif filename.endswith('.png'):
        _, _, raw_width, raw_height, offset_x, offset_y = identify_image(filename)
    else:
        raw_width, raw_height, offset_x, offset_y = (0,) * 4
    return raw_width, raw_height, offset_x, offset_y


def crop_image(filename):
    if not os.path.exists(filename):
        return
    dirname = filename[:-4]
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    os.system("convert +repage -crop 256x256 {0} {1}\\%02d{2}".format(filename, dirname, os.path.splitext(filename)[1]))


def trim_image(path, ddsoptimized=True):
    if os.path.exists(path):
        os.system('convert.exe -trim {0} {0}'.format(path))
        if ddsoptimized: #dds格式需确保宽高是4的倍数，否则图片会被拉升导致模糊
            w, h = get_size(path)
            extended_width = w if w % 4 == 0 else w + (4 - w % 4)
            extended_height = h if h % 4 == 0 else h + (4 - h % 4)
            old_page_info = subprocess.check_output("identify.exe -format %g {0}".format(path)).rstrip()
            os.system('convert -gravity northwest -background transparent -extent {0}x{1} -repage {2} {3} {3}'.format(
                extended_width, extended_height, old_page_info, path))


def put_images_into_folder(path):
    for file in glob.glob(path):
        dirName = file[:-11]
        fileName = file[-10:]
        if not os.path.exists(dirName):
            os.mkdir(dirName)
        shutil.move(file, os.path.join(dirName, fileName))


def force_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def multi_get_letter(str_input):
    if isinstance(str_input, unicode):
        unicode_str = str_input
    else:
        try:
            unicode_str = str_input.decode('utf8')
        except:
            try:
                unicode_str = str_input.decode('gbk')
            except:
                print 'unknown coding'
                return

    return_list = []
    for one_unicode in unicode_str:
        return_list.append(single_get_first(one_unicode))
    return "".join(return_list)


def single_get_first(unicode1):
    str1 = unicode1.encode('gbk')
    try:
        ord(str1)
        return str1
    except:
        asc = ord(str1[0]) * 256 + ord(str1[1]) - 65536
        if asc >= -20319 and asc <= -20284:
            return 'a'
        if asc >= -20283 and asc <= -19776:
            return 'b'
        if asc >= -19775 and asc <= -19219:
            return 'c'
        if asc >= -19218 and asc <= -18711:
            return 'd'
        if asc >= -18710 and asc <= -18527:
            return 'e'
        if asc >= -18526 and asc <= -18240:
            return 'f'
        if asc >= -18239 and asc <= -17923:
            return 'g'
        if asc >= -17922 and asc <= -17418:
            return 'h'
        if asc >= -17417 and asc <= -16475:
            return 'j'
        if asc >= -16474 and asc <= -16213:
            return 'k'
        if asc >= -16212 and asc <= -15641:
            return 'l'
        if asc >= -15640 and asc <= -15166:
            return 'm'
        if asc >= -15165 and asc <= -14923:
            return 'n'
        if asc >= -14922 and asc <= -14915:
            return 'o'
        if asc >= -14914 and asc <= -14631:
            return 'p'
        if asc >= -14630 and asc <= -14150:
            return 'q'
        if asc >= -14149 and asc <= -14091:
            return 'r'
        if asc >= -14090 and asc <= -13119:
            return 's'
        if asc >= -13118 and asc <= -12839:
            return 't'
        if asc >= -12838 and asc <= -12557:
            return 'w'
        if asc >= -12556 and asc <= -11848:
            return 'x'
        if asc >= -11847 and asc <= -11056:
            return 'y'
        if asc >= -11055 and asc <= -10247:
            return 'z'
        return ''

if __name__ == '__main__':
    put_images_into_folder('src\\场景\\魔界\\物件\\*.png')