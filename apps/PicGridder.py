#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# (c) 2023, 2024 Stefan Schmitt
#
# See below description


import os, itertools, sys, time, argparse
from array import *
from datetime import datetime, date, timedelta
from PIL import Image

spinner = itertools.cycle(['-', '/', '|', '\\'])

def spin(busy):
    if busy:
        sys.stdout.write(next(spinner))  # write the next character
        sys.stdout.flush()               # flush stdout buffer (actual character display)
        sys.stdout.write('\b')           # erase the last written char

def directory(raw_path):
    if not os.path.isdir(raw_path):
        raise argparse.ArgumentTypeError('"{}" is not an existing directory'.format(raw_path))
    return os.path.abspath(raw_path)

def get_image_exif_info(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data is not None:
                return exif_data.get(36867)
            else:
                return None
    except:
        return None

def find_min_max_date_time(directory):
    oldest_date, youngest_date = None, None
    smallest_time, largest_time = None, None
    dts = []
    fns = []
    filenames = os.listdir(directory)

    for filename in filenames:
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            image_path = os.path.join(directory, filename)
            exif_dt = get_image_exif_info(image_path)
          
            if exif_dt != None:
                dt = datetime.strptime(exif_dt, '%Y:%m:%d %H:%M:%S')
            else:
                dt = datetime.fromtimestamp(os.path.getmtime(image_path))
            # build two lists which pair date/time and filename at equal indices
            dts.append(dt)
            fns.append(filename)
            date = dt.date()
            time = dt.time()

            spin(busy)

            if date is not None and time is not None:
                if oldest_date is None or date < oldest_date:
                    oldest_date = date
                if youngest_date is None or date > youngest_date:
                    youngest_date = date

                if smallest_time is None or time < smallest_time:
                    smallest_time = time
                if largest_time is None or time > largest_time:
                    largest_time = time

    return oldest_date, youngest_date, smallest_time, largest_time, sorted(list(map(lambda x, y:(x,y), dts, fns))) # return timewise sorted list

def picGridder(srcDir, dstDir, dstPic, deltaSec, busy):
    
    print("Starting...")

    # Constants
    targetWidth = 160   # target width of single grid pic in number of pixel = reduced width of original pic
    targetHeight = 120  # target height of single grid pic in number of pixel = reduced height of original pic
    maxPicCols = 288    # maximum number of columns of pic grid = daytime grid
    maxPicRows = 546    # maximum number of rows of pic grid = days

    start=time.time()
    print(" Initialize the picture grid: Evaluate dates to calculate rows and times to calculate columns")
    print("Pass 1:", end=" ")
    oldest_date, youngest_date, smallest_time, largest_time, picList = find_min_max_date_time(srcDir)
    end=time.time()
    print("%.2f" % (end-start),"sec")

    picCols = int(((datetime.combine(date.today(), largest_time) - datetime.combine(date.today(), smallest_time)).total_seconds())/deltaSec) + 1
    if picCols > maxPicCols: picCols = maxPicCols
    picRows = (youngest_date - oldest_date).days + 1
    if picRows > maxPicRows: picRows = maxPicRows
    print("",picCols,"x",picRows,"grid = ",picCols*targetWidth,"px x",picRows*targetHeight,"px: from", oldest_date,"to",youngest_date,"between", smallest_time,"and",largest_time)

    start=time.time()
    print(" Build array of pictures.")
    print("Pass 2:", end=" ")

    picGrid = [[date.today] * picCols for _ in range(picRows)]
    dateGridStart = datetime.combine(oldest_date, smallest_time)
    idx = 0
    for r in range(picRows):
        for c in range(picCols):
            spin(busy)
            dateGrid = dateGridStart + timedelta(days=r) + timedelta(seconds=c*deltaSec)
            while True:
                if idx < len(picList) - 1:
                    diffSecA = (picList[idx][0] - dateGrid).total_seconds()
                    diffSecB = (picList[idx+1][0] - dateGrid).total_seconds()
                elif idx == len(picList) - 1:
                    diffSecA = (picList[idx][0] - dateGrid).total_seconds()
                    diffSecB = diffSecA
                else:
                    break
                if not ((diffSecA < -deltaSec/2) and (diffSecB < -deltaSec/2)):
                    break
                idx += 1

            if diffSecA > deltaSec/2 and diffSecB > deltaSec/2:
                continue
            else:
                if (idx <= len(picList) - 1) and (abs(diffSecA) <= abs(diffSecB)):
                    picGrid[r][c] = picList[idx]
                    idx += 1
                elif (idx < len(picList) - 2):
                    picGrid[r][c] = picList[idx+1]
                    idx += 2
                else:
                    pass
    end=time.time()
    print("%.2f" % (end-start),"sec")

    start=time.time()
    print(" Save big picture.")
    print("Pass 3:", end=" ")    
    new_im = Image.new('RGB', (targetWidth*picCols, targetHeight*picRows))
    for r in range(picRows):
        for c in range(picCols):
            spin(busy)
            try:
                src_im = Image.open(os.path.join(srcDir, picGrid[r][c][1]))
                src_im = src_im.resize((targetWidth, targetHeight), resample=Image.LANCZOS)
                new_im.paste(src_im, (c*targetWidth,r*targetHeight))
            except: 
                continue
    end=time.time()
    print("%.2f" % (end-start),"sec")

    try:
        new_im.save(os.path.join(dstDir, dstPic), 'JPEG', quality=95)
    except:
        print("Help! Cannot save to",os.path.join(dstDir, dstPic)," Likely permissions are not sufficient!")
    
    print("Finish.")


if __name__ == "__main__":
    
    argParser = argparse.ArgumentParser(
        description="Arranges source jpeg files in a destination jpeg file in a grid of rows and columns. \
                    All jpeg files of the same recording day are arranged in the same row \
                    and in columns with a temporal grid with definable resolution. \
                    A maximum destination jpeg resolution of 65536 by 65536 pixels is respected. "
    )
    argParser.add_argument("-s", "--srcdir", help="source directory of pictures to scan", type=directory, default="/apps/data/pic-source")
    argParser.add_argument("-d", "--dstdir", help="destination directory of gridded picture", type=directory, default="/apps/data/pic-dest")
    argParser.add_argument("-g", "--gridpic", help="filename of gridded picture", default="BigPicture.jpg")
    argParser.add_argument("-t", "--rest", help="temporal grid in seconds", type=int, default=300)
    argParser.add_argument("-q", "--quiet", help="do not spin", default=True, action='store_false')

    print("Using params:")
    args = argParser.parse_args()
    srcDir = args.srcdir
    dstDir = args.dstdir
    dstPic = args.gridpic
    deltaSec = args.rest
    busy = args.quiet
    
    print("srcDir =", srcDir)
    print("dstDir =", dstDir)
    print("dstPic =", dstPic)
    print("deltaSec =", deltaSec)
    print("spinner =", busy)
    picGridder(srcDir, dstDir, dstPic, deltaSec, busy)
