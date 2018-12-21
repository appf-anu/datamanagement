#!/usr/bin/env python3

"""
By Ellen Levingston, 2018-19

Zip images for a given camera dir by month, putting the zipfile in the specified output dir.
Main purpose is to use this on picam directories.

Does not remove original files.

User optionally provides start and end dates for the process.

Zips files by type, so that jpgs, tifs, cr2s each get their own zip. Relies on
file name extensions being correct. Only zips files which contain a timestamp in
the name.

Zip files are named form the camera dir provided for processing, not from the
file names of the images.

Does not check if file is already in archive.

Provides recursive directory search, so supports both nested and flat structures.

Usage example
./zip_images_by_month.py --output archive_picam_for_backup GC037L

"""

import sys
import os
import signal
import glob
import re
import zlib, zipfile
import argparse

if sys.version_info.major != 3:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')
if sys.version_info.minor < 5:
    raise RuntimeError('Python version 3, >= 3.5 required (uses iglob recursive).')

# regex to match date in file name format e.g. GC02L_2016_04_28_16_35_00.jpg
# allow year to 2099
date_regex = re.compile('20[1-9][0-9]_[0-1][0-9]_[0-3][0-9]')
month_regex = re.compile('20[1-9][0-9]_[0-1][0-9]')

extensions_to_include = ['.cr2', '.jpg',  '.jpeg', '.tiff', '.tif']

class SigHandler:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True


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
    parser = argparse.ArgumentParser(description = 'Zip images for a '
    'given camera dir by hour, putting the zip in the same dir. '
    'Then delete the images, keeping only the zip.')
    parser.add_argument('-s', '--start', metavar='start date', type=str, required=False,
        help='Start of date range to process (inclusive).')
    parser.add_argument('-e', '--end', metavar='end date', type=str, required=False,
        help='End of date range to process (inclusive).')
    parser.add_argument('-o', '--output', metavar='output_dir', type=str, required=True,
        help='Camera directory to process.')
    parser.add_argument('dirs', metavar='camera_dir/s', type=str, nargs='+',
        help='Camera directory to process.')
    args = parser.parse_args()

    if args.start is not None and args.end is not None:
        if args.end < args.start:
            raise ValueError('End date must not be less than start date. Quitting.')

    return args.dirs, args.output, args.start, args.end

def archive(file_name, zip_file_name):
    """
    Write to the zipfile.
    Check if the file is already in the archive (if archive exists) and don't
    write to the archive if file is already there.
    Note: function call is wrapped in a try:except statement, no IOError checking
    is done inside this function
    """

    # need the full path to locate the current file to be written to archive,
    # but only write the base name to the archive (not full path)
    file_path = os.path.realpath(file_name)
    arch_file_name = (os.path.basename(file_path))

    with zipfile.ZipFile(zip_file_name, 'a') as zip:
        if arch_file_name not in zip.namelist():
            zip.write(file_path, arcname=arch_file_name, compress_type=None)

def match_ext(file_list, ext):
    matches = []
    for f in file_list:
        if f.endswith(ext):
            matches.append(f)
    return matches


def main():
    """
    Zip up applicable files in the specified dirs, within the specified range

    - Use iglob to locate files which match the file extension search criteria (image files).
    - Use regex to target appropriately named files (must include a timestamp, down to hour)
    - Only include files where the timestamp (in the name) is within the user-specified range (if given)
    - After zipring is finished, use iglob to locate all zipfiles
    - Fix the permissions for the zip file
    - For each zipfile, list the files contained; use the list to delete the original
      files, since they are now archived
    """
    # process arguments
    source_dirs, output_dir, start_date, end_date = parse_args()

    if not os.path.isdir(output_dir):
        raise OSError(f'Directory does not exist: "{output_dir}". Quitting.')
    for dir in source_dirs:
        if not os.path.isdir(dir):
            raise OSError(f'Directory does not exist: "{dir}". Quitting.')

    # create a signal handler to enable program to exit gracefully if process is killed
    sig_handler = SigHandler()

    for camera_dir in source_dirs:

        lockfile = os.path.join(output_dir, f'{camera_dir}_process_is_still_running_{os.getpid()}')
        try:
            open(lockfile, 'w').close()
        except:
            print(f'Failed to create lockfile {lockfile}.')


        for current_dir, subdir_list, file_list in os.walk(camera_dir, topdown=False):
            # accepted_filelist = [os.path.join(current_dir, f'**/*{x}') for x in extensions_to_include]
            #print ('Search terms:', end=' ')
            #print (file_list, '\n')

            if len(file_list) > 0:  # only work on dirs which have files in them
                for ext in extensions_to_include:
                    for file_name in match_ext(file_list, ext):
                        # iglob returns an iterable of file paths (str) matching the required image extensions,
                        # located within the tree of the current dir
                        # note there is no sanity checking for structure. (And the image name
                        # contains enough metadata to manage each image and create a correct
                        # dir tree if required)

                        # check the file name for a hour and date in correct format
                        # e.g. 2018_10_25_11

                        # check whether zip already exists for current month

                        date_match = date_regex.search(file_name)
                        if date_match:
                            image_date = date_match.group() # get the image date from the file name
                        else:
                            #print('Skipping file that doesn\'t match.')
                            continue  # skip any files which don't include a date in the name

                        if date_in_range(image_date, start_date, end_date):
                            month_match = month_regex.search(file_name)
                            image_month = month_match.group() # get the image date from the file name
                            zip_file_name = os.path.join(output_dir, f'{image_month}_{ext[1:]}.zip')

                            try:
                                archive(file_name, zip_file_name)
                                # archive_and_remove(file_name, zip) - not in use. note: would need to test removal on real data
                            except IOError:
                                print(f'IOError, skipping {file_name}')
                            except zipfile.BadZipFile:
                                print(f'Bad zip file returned for {zip_file_name}. Skipping.')

                        # here's a safe place to exit if set kill signal
                        if sig_handler.kill_now:
                            sys.exit(1)
        try:
            os.remove(lockfile)
        except:
            print(f'Failed to remove lockfile {lockfile}.')
    print('Done.')


if __name__ == '__main__':
	main()
