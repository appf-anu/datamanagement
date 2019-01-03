#!/usr/bin/env python3

"""
Tar trial (chamber) images for a given camera dir by week and move the tar to
massdata for back up. The week starts on Monday.

User optionally provides start and end dates for the process.

Tars files all together, regardless of type. If a tar already exists for a given
month, then append to that.

IMPORTANT! Tar files are named form the camera dir provided for processing.
Do not give a dir that is not named by camera, or the tar files will be incorrectly
named.

Ignores any jpg containing the string "last_image".

Does NOT remove the original files.

Allows for possible nested directory structure, and only tars files at the lowest level.

Creates a temporary backup dir for tar files (to avoid potential issues with
permissions and avoid writing into the source dir).

Backup directory structure on massdata is phenomics/backup/picam/year/month.ext.tar

Usage example
./backup_to_mdss -s 2018_10_25 -e 2018_12_25 GC35L GC35R



"""

import sys
import os
import glob
import re
import tarfile
import argparse
import datetime

if sys.version_info.major != 3:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')
if sys.version_info.minor < 5:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')


temp_tar_dir = '/g/data1a/xe2/phenomics/temp_backup_dir_for_tars'

"""
 regex format:
 ^ start of string
 $ end of string
 [0-9] match numbers in range
 hyphen - can be matched without \ if it is the 1st or last char in []; otherwise, escape with backslash
 undersore _ is not a special character
"""

# regex to match file name format e.g. GC02L_2016_04_28_16_35_00.jpg
# allow year to 2099
camera_regex = re.compile('^[a-zA-Z0-9-]')
day_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]')
day_hour_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]_[0-1][0-9]')
hms_regex = re.compile('[0-1][0-9]_[0-5][0-9]_[0-5][0-9]')
# file_name_regex_no_ext = re.compile(camera_regex + '_' + day_regex + '_' + hms_regex + '$')

extensions_to_include = ['.jpg','.cr2', '.jpeg', '.tiff', '.tif']

"""
# verify regex works - you can use this to check regex logic before running
hour_dir = '/network/largedata/a_data/gigapixel/Gigavision/ARB-GV-HILL-1/2014/2014_12/2014_12_20/2014_12_20_18'
print('Testing regex match for hour_dir "{}".'.format(hour_dir))
if re.search(hour_dir_name_format, hour_dir):
	print('Passed!')
else:
	print('Failed!')

day_dir = '/network/largedata/a_data/gigapixel/Gigavision/ARB-GV-HILL-1/2014/2014_12/2014_12_20'
print('Testing regex match for day_dir "{}".'.format(day_dir))
if re.search(day_dir_name_format, day_dir):
	print('Passed!')
else:
	print('Failed!')

input('Press enter.')
"""

def date_in_range(date_str: string, lower_bound: date, upper_bound: date):
    """
    returns True if image_date falls after the lower bound date (if it is not None) and
    before upper bound date (if it is not None). lower_bound and/or upper_bound can be None.
    If neither is specified then returns True.

    Argument types are explicit to avoid confusion about usage.

    """

    if not (lower_bound or upper_bound):
        return True

    # convert image_date_str to a date object for comparison
    date = datetime.strptime(date_str, '%Y_%m_%d')

    if lower_bound:
        if date => lower_bound:
            within_lower_bound = True
        else:
            return False
    else:
        within_lower_bound = True
    if upper_bound:
        if date <= upper_bound:
            within_upper_bound = True
        else:
            return False
    else:
        within_upper_bound = True

    return within_lower_bound and within_upper_bound


def main():

    # process arguments
    (source_dirs, has_start_date, has_end_date, start_date, end_date) = parse_args()


    # try to create the temporary dir
    try:
        os.mkdir(temp_tar_dir)
    except FileExistsError:
        print('Temp directory {} already exists. Please investigate and remove before running program.'.format(temp_tar_dir))
    except:
        print('Failed to create temp directory {}.'.format(temp_tar_dir))
        raise

    for camera_dir in source_dirs:
        for file in glob.iglob(*[os.path.join(camera_dir, "**/*"+ext) for x in extensions_to_include], recursive=True):
            # iglob returns an iterable of files matching the required image extensions,
            # located within the tree of the provided camera dir
            # note there is no sanity checking for structure: the image name
            # contains enough metadata to manage each image and create a correct
            # dir tree if required

            # check the file name for a date in correct format
            # this code is for tarring by week
            date_match = day_regex.search(file)
            if date_match:
                image_date = date_match.group() # get the image date from the file name
            else:
                continue  # skip any files which don't include a date in the name

            # determine whether the date of the file falls within the specified
            # date range

            if date_in_range(image_date, start_date, end_date):

                tar_file_name = camera_dir + '_' + image_date + '.tar'

                tar_file_path = temp_tar_dir + '/' + tar_file_name

                # Check if tar file already exists, and if it does, verify
                # whether current image file has already been written to it.

                if os.path.isfile(tar_file_path):
                    # open existing tarfile in append mode
                    try:
                        tarfile.open(tar_file_path, 'a')
                    except Exception as e:
                        print('Failed to open existing tar file for appending.')
                        raise e
                else: # tar file does not exist
                    try:
                        # create the new tar file in write mode
                        tarfile.open(tar_file_path, 'w')
                    except Exception as e:
                        print('Failed to create new tar file for writing.')
                        raise e

                # check if the image is already in the tar file
                if

            else: # image date is not in specified range, so ignore file
                continue



"""
# old code using os.walk

        for current_dir, subdirs, files in os.walk(source_dir, topdown=False):
    		if len(subdirs) == 0:  # only process files in the lowest dir
                if len(files) > 0:  # check that there are some files in the dir;
                    # if there are few files, check whether they're all ignorable
                    if len(files) < 8: # an arbitrarily small number of files; verify whether dir contains any data to back up
                        processable_files = 0
                        for f in files:
                            if ('last_image' not in f) and (not f.endswith(extensions_to_exclude):
                                processable_files += 1
                        if processable_files < 1:
                            continue

                    # remove files which don't
                    wanted_files = [f for f in files if (('last_image' not in f) and (not f.endswith(extensions_to_exclude))]

                    # sort the files by name, which are in date order
                    files.sort()
"""


if __name__ == '__main__':
	main()
