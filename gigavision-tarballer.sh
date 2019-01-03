#!/bin/bash

# tars by hour, one tar of tifs and one of jpgs
# since images are being archived by hour, there is no dir structure
# stored with the images. The tar name (and image file names) include the metadata.

usage() {
    echo "USAGE: $0 CAMERA_DIR [CAMERA_DIR ...]"
    echo
    echo "Will tarball each hour directory within CAMERA_DIR"
    exit 1
}



# Check all camdirs exist
for camdir in "$@"
do
    camdir="$(readlink -f "$camdir")"
    if [ ! -d "$camdir" ]
    then
        echo "Not a directory (give me a path to the camera directory)"
        echo "$camdir"
        exit 1
    fi
done

set -xeo pipefail

for camdir in "$@"
do
    camdir="$(readlink -f "$camdir")"
    cam=$(basename $camdir)
    echo DOING $camdir "($cam)"

    for hourdir in $(find $camdir -links 2 -type d -not -path *2019*) # bad hack, so that we don't do current data
    do
        # I called this hour, but note it actually includes the date, e.g. 2018_10_22_12
        hour="$(basename $hourdir)"
        echo "$hour"

        # run the tar in the hourdir to avoid storing the dir tree in the tar file
        cd "$hourdir"

        # create separate archive files for jpgs and tifs
        for ext in jpg tif
        do

            archive="${cam}_${hour}_${ext}.tar"

            if [ -f $archive ]
            then
                tarmode="--append"
            else
                tarmode="--create"
            fi

            # find files
            if [ $ext == "jpg" ]
            then
                files=$(find . -maxdepth 1 -type f -iname '*.jpg' -or -iname '*.jpeg')
            elif [ $ext == "tif" ]
            then
                files=$(find . -maxdepth 1 -type f -iname '*.tif' -or -iname '*.tiff')
            fi
            if [ -z "$files" ]
            then
                continue
            fi

            # tar flat, without including any directory structure
            # tar jpgs and tifs separately
            tar $tarmode -v -f $archive $files

            # List files from tar for deletion | skip directories (end with /) | \
            # null-delimit so xargs can do spaces | delete files in batches of 500
            tar tf $archive | grep -v '/$' | tr '\n' '\0' | xargs -0 -n 500 rm -fv
        done
    done
done
