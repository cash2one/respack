#coding=gbk
import glob
import os
import shutil
import struct
import subprocess
import zlib
import re

SRC = 'src'
RES = 'res'

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


def get_size(filename):
    output = subprocess.check_output("identify.exe -format %w,%h {0}".format(filename))
    result = map(int, output.split(','))
    return result


def get_offset(path):
    if not os.path.exists(path):
        return (0, 0)
    if path.endswith('.tga'):
        with open(path, 'rb') as f:
            f.seek(3)
            offset_x, offset_y = struct.unpack('2H', f.read(struct.calcsize('2H')))
    elif path.endswith('.png'):
        output = subprocess.check_output("identify.exe -format %g {0}".format(path))
        offset_x, offset_y = map(int, re.split('[+-]', output)[-2:])
    else:
        offset_x, offset_y = 0, 0
    return offset_x, offset_y


def crop_image(filename):
    if not os.path.exists(filename):
        return
    dirname = filename[:-4]
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    os.system("convert -crop 256x256 {0} {1}\\%02d{2}".format(filename, dirname, os.path.splitext(filename)[1]))


def trim_image(path):
    if os.path.exists(path):
        os.system('convert.exe -trim {0} {0}'.format(path))

def move_images(path):
    for file in glob.glob(path):
        os.mkdir(file[:-4])
        shutil.move(file, '{0}\\000001{1}'.format(file[:-4], file[-4:]))

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
    print multi_get_letter('新手村')