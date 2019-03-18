#!/usr/bin/env python3

"""
Move files from a dir into an already structured camera dir:
  cam/year/month/day/hour

Assumes files are named camera-year-month-day-hour...
(doesn't care about anything after the hour)
"""

import os
import shutil
import re

cameraname = 'kioloa-hill-GV01'
cameradir = cameraname
sourcedir = os.path.join(cameradir,'csvs')

time_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]_[0-2][0-9]')

for f in os.listdir(sourcedir):
    if f.startswith(cameraname):
        time_match = time_regex.search(f)
        if time_match:
            image_time = time_match.group() # get the image date from the file name
            # time: yyyy_mm_dd_hh  0123_56_89_12
            year = image_time[:4]
            yearmonth = image_time[:7]
            yearmonthday = image_time[:10]
            yearmonthdayhour = image_time
            destdir = os.path.join(cameradir, year, yearmonth, yearmonthday, yearmonthdayhour)
            sourcepath = os.path.join(sourcedir, f)
            print(f'Will move {sourcepath} to {destdir}')
            shutil.move(sourcepath, destdir)
        else:
            print('Skipping file that doesn\'t match.')
            continue  # skip any files which don't include a date in the name

