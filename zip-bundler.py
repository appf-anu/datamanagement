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
import os.path as op
import signal
import glob
import re
import zipfile
import argparse
import datetime

TS_IMAGE_DATETIME_RE = re.compile(r"(\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d)(_\d+)?(_\w+)?")
TS_IMAGE_FILE_RE = re.compile(r"\d{4}_[0-1]\d_[0-3]\d_[0-2]\d_[0-5]\d_[0-5]\d(_\d+)?.(\S+)$", re.I)


class SigHandler(object):
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True

class LockFile(object):
    def __init__(self, lockpath):
        self.path = lockpath
    def __enter__(self, *args):
        if op.exists(self.path):
            raise RuntimeError(f"Can't lock {self.path}")
        with open(self.path, "w") as f:
            pass
    def __exit__(self, *args):
        os.unlink(self.path)




def path_is_timestream_file(path, extensions=None):
    """Test if pathname pattern matches the expected

    :param path: File path, with or without directory
    :param path: Optionally, one or more extensions to accept

    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00_1.jpg")
    True
    >>> path_is_timestream_file("2018_12_31_23_59_59_00.jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg", extensions="jpg")
    True
    >>> path_is_timestream_file("test_2018_12_31_23_59_59_00.jpg", extensions="tif")
    False
    >>> path_is_timestream_file("not-a-timestream.jpg")
    False
    """
    if isinstance(extensions, str):
        extensions = [extensions, ]
    try:
        m = TS_IMAGE_DATETIME_RE.search(path)
        if m is None:
            return False
        if extensions is not None:
            return any([path.lower().endswith(ext) for ext in extensions])
        return True
    except ValueError:
        return False

def extract_datetime(path):
    m = TS_IMAGE_DATETIME_RE.search(path)
    if m is None:
        return path
    else:
        return m[0]

def parse_date(datestamp):
    if isinstance(datestamp, datetime.datetime):
        return datestamp
    return datetime.datetime.strptime(datestamp, "%Y_%m_%d_%H_%M_%S")


def path_within_archive(datestamp, imagepath, camname):
    """Gets path for timestream image.
    """
    dt = parse_date(datestamp)
    imgbasename = op.basename(imagepath) # include ext
    path = f"{camname}/%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{imgbasename}"
    path = dt.strftime(path)
    return path

def archive_path(outdir, datetime, camname, bundle="hour", format="jpg"):
    datetime = parse_date(datetime)
    if bundle == "root" or bundle == "none":
        raise NotImplemented()
    elif bundle == "year":
        bpath = f"{camname}_%Y.{format}.zip"
    elif bundle == "month":
        bpath = f"%Y/{camname}_%Y_%m.{format}.zip"
    elif bundle == "day":
        bpath = f"%Y/%Y_%m/{camname}_%Y_%m_%d.{format}.zip"
    elif bundle == "hour":
        bpath = f"%Y/%Y_%m/%Y_%m_%d/{camname}_%Y_%m_%d_%H.{format}.zip"
    elif bundle == "minute":
        bpath = f"%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{camname}_%Y_%m_%d_%H_%M.{format}.zip"
    elif bundle == "second":
        bpath = f"%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/{camname}_%Y_%m_%d_%H_%M_%S.{format}.zip"
    else:
        raise ValueError(f"Invalid bundle level: {bundle}")
    #k if basename(outdir.rstrip("/")) != camname:
    #k     outdir = op.join(outdir, camname)
    return op.join(outdir, datetime.strftime(bpath))


def date_in_range(date: str, lower_bound: str, upper_bound: str):
    """Test if a date is in a given range
    Returns True if image_date falls after the lower bound date (if it is not None) and
    before upper bound date (if it is not None). lower_bound and/or upper_bound can be None.
    If neither is specified then returns True.

    String date format assumed to be 'YYYY_MM_DD' e.g. '2018_10_25'. Relies on
    dates stored as strings specified year-first sorting the same way as real dates.
    """
    date = '_'.join(date.split('_')[0:2]) # FIXME: horrible hack, our dates include time now

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
    parser.add_argument('-s', '--start-date', metavar='start date', type=str, required=False,
        help='Start of date range to process (inclusive).')
    parser.add_argument('-e', '--end-date', metavar='end date', type=str, required=False,
        help='End of date range to process (inclusive).')
    parser.add_argument('-f', '--format', metavar='extension', type=str, default="jpg",
        help='File format to process (case insensitive, jpg will also catch *.jpeg, tif will also catch *.tiff)')
    parser.add_argument('-o', '--output', metavar='output_dir', type=str, required=True,
        help='Output directory of backed-up images (should include camera, no subdir will be created)')
    parser.add_argument('-b', '--bundle', metavar='timelevel', type=str, default="day",
        help="Level at which to bundle images. must be year, month, day, hour, minute or second")
    parser.add_argument('camera_dir', metavar='camera dir', type=str,
        help='Camera directory to process.')
    args = parser.parse_args()

    if args.start_date == "":
        args.start_date = None
    if args.end_date == "":
        args.end_date = None
    if args.start_date is not None and args.end_date is not None:
        if args.end_date < args.start_date:
            raise ValueError('End date must not be less than start date. Quitting.')
    args.format = args.format.lstrip(".")
    return args


def main():
    """
    Zip up applicable files in the specified dirs, within the specified range

    - Use iglob to locate files which match the file extension search criteria (image files).
    - Use regex to target appropriately named files (must include a timestamp, down to hour)
    - Only include files where the timestamp (in the name) is within the user-specified range (if given)
    - After zipping is finished, use iglob to locate all zipfiles
    - Fix the permissions for the zip file
    - For each zipfile, list the files contained; use the list to delete the original
      files, since they are now archived

    KNOWN ISSUES:
        - jpg doesn't catch jpeg, raw doesn't catch *.cr2; tif doesn't catch
        tiff
    """
    # process arguments
    args = parse_args()
    camera_name = op.basename(args.camera_dir.rstrip('/'))

    if not op.isdir(op.dirname(args.output)):
        print(f'Directory does not exist: "{args.output}". Quitting.', file=sys.stderr)
        sys.exit(1)
    elif not op.isdir(args.output):
        try:
            os.mkdir(args.output)
        except FileExistsError:
            pass

    if not op.isdir(args.camera_dir):
        print(f'Directory does not exist: "{args.camera_dir}". Quitting.', file=sys.stderr)
        sys.exit(1)

    # create a signal handler to enable program to exit gracefully if process is killed
    sig_handler = SigHandler()

    allowed_exts = set([args.format.lower()])
    if args.format == "jpg":
        allowed_exts = set(["jpg", "jpeg"])

    print(f"Processing '{camera_name}'")

    for current_dir, subdir_list, file_list in os.walk(args.camera_dir, topdown=False):
        subdir_list.sort()
        file_list.sort(key=lambda f: extract_datetime(f))
        for file_name in file_list:
            file_path = op.join(current_dir, file_name)
            file_ext = op.splitext(file_name)[1].lstrip('.')
            if file_ext.lower() not in allowed_exts:
                continue

            if not path_is_timestream_file(file_name):
                continue

            image_date = extract_datetime(file_name)
            if not date_in_range(image_date, args.start_date, args.end_date):
                continue

            zip_path = archive_path(args.output, image_date, camera_name,
                                    bundle=args.bundle, format=args.format)
            subpath = path_within_archive(image_date, file_name, camera_name)
            try:
                zip_dir = op.dirname(zip_path)
                os.makedirs(zip_dir)
            except OSError:
                pass
            try:
                with LockFile(zip_path + ".lock"):
                    with zipfile.ZipFile(zip_path, 'a') as zip:
                        if subpath not in zip.namelist():
                            zip.write(file_path, arcname=subpath, compress_type=None)
                            print(f"Added {file_name} to {zip_path}")
                        else:
                            print(f"{file_name} already in {zip_path}, skipping")
            except IOError as exc:
                print(f'Error ({str(exc)}), skipping {file_path}', file=sys.stderr)
            except zipfile.BadZipFile as exc:
                print(f'Bad zip file ({str(exc)}) for {zip_path}. Skipping', file=sys.stderr)

            # here's a safe place to exit if set kill signal
            if sig_handler.kill_now:
                sys.exit(1)
    print('Done.')


if __name__ == '__main__':
	main()
