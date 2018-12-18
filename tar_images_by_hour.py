#!/usr/bin/env python3

"""
Tar images for a given camera dir by hour, putting the tar in the same dir.
Then delete the images, keeping only the tar (to save inodes).
Main purpose is to use this on gigavision directories.

User optionally provides start and end dates for the process.

Tars files by type, so that jpgs, tifs, cr2s each get their own tar. Relies on
file name extensions being correct. Only tars files which contain a timestamp in
the name.

Tar files are named form the camera dir provided for processing, not from the
file names of the images.

Does not check if file is already in archive.

Removes the original files (only ones that are listed in an archive).

Provides recursive directory search, so supports both nested and flat structures.

Usage example
./tar_images_by_hour --start 2018_10_25 --end 2018_12_25 kioloa-hill-GV01

"""

import sys
import os
import signal
import glob
import re
import tarfile
import argparse

if sys.version_info.major != 3:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')
if sys.version_info.minor < 5:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')


# regex to match date in file name format e.g. GC02L_2016_04_28_16_35_00.jpg
# allow year to 2099
date_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]')

extensions_to_include = ['.jpg','.cr2', '.jpeg', '.tiff', '.tif']

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

    return args.dirs, args.start, args.end

def archive(file_name, tar):
    """
    Dumb write to the tarfile.
    Should probably check if the file is already in the archive (if archive exists)
    - but that raises the issue of comparing and deciding which file is correct...
    Note: function call is wrapped in a try:except statement, no IOError checking
    is done inside this function
    """

    # need the full path to locate the current file to be written to archive,
    # but only write the base name to the archive (not full path)
    file_path = os.path.realpath(file_name)
    with tarfile.open(tar_file_name, 'a') as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))


# not in use
def archive_and_remove(file_name, tar):
    """
    Dumb write to the tarfile.
    Should probably check if the file is already in the archive (if archive exists)
    - but that raises the issue of comparing and deciding which file is correct...
    Anyway, since the file is removed immediately after being archived, in theory
    it's unlikely to ever be added twice.
    Note: function call is wrapped in a try:except statement, no IOError checking
    is done inside this function
    """

    # need the full path to locate the current file to be written to archive,
    # but only write the base name to the archive (not full path)
    file_path = os.path.realpath(file_name)
    with tarfile.open(tar_file_name, 'a') as tar:
        tar.add(file_path, arcname=os.path.basename(file_path))
        os.remove(file_name)


def main():
    """
    Tar up applicable files in the specified dirs, within the specified range

    - Use iglob to locate files which match the file extension search criteria (image files).
    - Use regex to target appropriately named files (must include a timestamp, down to hour)
    - Only include files where the timestamp (in the name) is within the user-specified range (if given)
    - After tarring is finished, use iglob to locate all tarballs
    - Fix the permissions for the tar file
    - For each tarball, list the files contained; use the list to delete the original
      files, since they are now archived
    """
    # process arguments
    source_dirs, start_date, end_date, log_file_dir = parse_args()

    for dir in source_dirs:
        if not os.path.isdir(dir):
            raise OSError(f'Directory does not exist: "{dir}". Quitting.')


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


                # print(f'Processing file: "{file_name}"')

                # check the file name for a hour and date in correct format
                # e.g. 2018_10_25_11
                date_match = date_regex.search(file_name)
                if date_match:
                    image_date = date_match.group() # get the image date from the file name
                else:
                    #print('Skipping file that doesn\'t match.')
                    continue  # skip any files which don't include a date in the name

                # determine whether the date of the file falls within the specified
                # date range
                if date_in_range(image_date, start_date, end_date):

                    file_parent_dir = os.path.dirname(file_name)
                    tar_file_name = os.path.join(file_parent_dir, f'{os.path.basename(camera_dir)}_{image_date}.tar')

                    try:
                        archive(file_name, tar)
                        # archive_and_remove(file_name, tar) - not in use. note: would need to test removal on real data
                    except IOError:
                        print(f'Skipping {file_name}')

    print('Done.')


if __name__ == '__main__':
	main()
