#!/usr/bin/env python3

"""
Tar trial (chamber) images for a given camera dir by week to enable back up to
massdata.

The week starts on Monday.

User optionally provides start and end dates for the process.

Tars files all together, regardless of type. If a tar already exists, then append to that.

Tar files are named form the camera dir provided for processing.

Does NOT remove the original files.

Allows for possible nested directory structure, and only tars files at the lowest level.

Creates a temporary backup dir for tar files.

Usage example
./tar_images_by_week -t temp_tar_dir -s 2018_10_25 -e 2018_12_25 GC35L GC35R



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

# regex to match date and hour in file name format e.g. GC02L_2016_04_28_16_35_00.jpg
# allow year to 2099
date_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]')

extensions_to_include = ['.tar','.jpg','.cr2', '.jpeg', '.tiff', '.tif']


def date_in_range(date: str, lower_bound: str, upper_bound: str):
    """Test if a date is in a given range
    Returns True if image_date falls after the lower bound date (if it is not None) and
    before upper bound date (if it is not None). lower_bound and/or upper_bound can be None.
    If neither is specified then returns True.

    String date format assumed to be 'YYYY_MM_DD' e.g. '2018_10_25'. Relies on
    dates stored as strings specified year-first sorting the same way as real dates.
    """

    if lower_bound is None and upper_bound is None:
        return True
    if lower_bound:
        if date < lower_bound:
            return False
    if upper_bound:
        if date > upper_bound:
            return False
    return True


def parse_args():
    parser = argparse.ArgumentParser(description = 'Tar images for a '
    'given camera dir by hour, putting the tar in the same dir. '
    'Then delete the images, keeping only the tar.')
    parser.add_argument('-t', '--temp', metavar='temp dir', type=str, required=True,
        help='Temporary directory for tar files.')
    parser.add_argument('-s', '--start', metavar='start date', type=str, required=False,
        help='Start of date range to process (inclusive).')
    parser.add_argument('-e', '--end', metavar='end date', type=str, required=False,
        help='End of date range to process (inclusive).')
    parser.add_argument('dirs', metavar='camera dir/s', type=str, nargs='+',
        help='Camera directory to process.')
    args = parser.parse_args()

    if args.start is not None and args.end is not None:
        if args.end < args.start:
            raise ValueError('End date must not be less than start date. Quitting.')

    return args.temp, args.dirs, args.start, args.end


def main():
    """
    Tar up all files in the specified dirs, within the specified range
    - Use iglob to locate files which match the file extension search criteria (image files).
    - Use regex to target appropriately named files (must include a timestamp, down to hour)
    - Only include files where the timestamp (in the name) is within the user-specified range (if given)
    - After tarring is finished, fix the permissions for the tar files
    """
    # process arguments
    (temp_tar_dir, source_dirs, start_date, end_date) = parse_args()

    for dir in source_dirs:
        if not os.path.isdir(dir):
            raise OSError('Directory does not exist: "{}". Quitting.'.format(dir))

    if not os.path.isdir(temp_tar_dir):
        try:
            os.mkdir(temp_tar_dir)
        except:
            raise ('Directory does not exist and cannot be created: "{}". Quitting.'.format(temp_tar_dir))

    for camera_dir in source_dirs:
        file_list = [os.path.join(camera_dir, "**/*"+x) for x in extensions_to_include]
        print ('Search terms:', end=' ')
        print (file_list, '\n')
        for file_path in file_list:
            for file_name in glob.iglob(file_path, recursive=True):
                # iglob returns an iterable of file paths (str) matching the required image extensions,
                # located within the tree of the provided camera dir
                # dir tree if required)
                # note there is no sanity checking for structure. (And the image name
                # contains enough metadata to manage each image and create a correct


                # print('Processing file: "{}"'.format(file_name))

                # check the file name for a hour and date in correct format
                # e.g. 2018_10_25_11
                date_match = date_regex.search(file_name)
                if date_match:
                    image_date_str = date_match.group() # get the image date from the file name
                else:
                    #print('Skipping file that doesn\'t match.')
                    continue  # skip any files which don't include a date in the name

                # determine whether the date of the file falls within the specified
                # date range
                if date_in_range(image_date_str, start_date, end_date):

                    # find the date for the Monday closest to the image date - this will be the week for the tar
                    # weekdays Mon=0 .. Sun=6. So the date of the previous Mon is
                    # the image date minus the weekday num (i.e. -0 if today is Mon, -1 if today is Tue, etc)
                    image_date = datetime.datetime.strptime(image_date_str, '%Y_%m_%d')
                    monday_date = image_date - datetime.timedelta(days=image_date.weekday())
                    monday_date_str = monday_date.strftime('%Y_%m_%d')

                    tar_file_name = os.path.join(temp_tar_dir, '{}_{}_week.tar'.format(os.path.basename(camera_dir), monday_date_str))

                    try:
                        tar = tarfile.open(tar_file_name, 'a')
                    except Exception as e:
                        print('Failed to open existing tar file for appending / create tar file for writing. Skipping. "{}"'.format(tar_file_name))

                    # Dumb write to the tarfile.
                    # Should probably check if the file is already in the archive (if archive exists)
                    # - but that raises the task of comparing and deciding which file is correct...
                    # maybe at least we could report on discrepancies?

                    # need the full path to locate the current file to be written to archive,
                    # but only write the base name to the archive (not full path)
                    file_path = os.path.realpath(file_name)
                    tar.add(file_path, arcname=os.path.basename(file_path))
                    tar.close()



if __name__ == '__main__':
	main()
