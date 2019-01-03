#!/bin/bash
START=2000_01_01
END=2020_01_01
CAMUPLOAD=/g/data/xe2/phenomics/camupload
DEST=/g/data/xe2/phenomics/camupload-backups/picam/
mkdir -p $DEST
CAMERAS=$(echo GC{02,03,04,05,35,36,37}{L,R,-Picam} BK{04,07}{L,R,-Picam} GC37L-NIR-C01 GC37R-NIR-C02 Eucalyptus02-Cam01 Eucalyptus02-Picam Eucalyptus02-Cam02)

set -e
trap "exit 1" INT

for CAMERA in $CAMERAS
do
    camdir=${CAMUPLOAD}/picam/${CAMERA}
    #for ext in jpg cr2 tif
    for ext in tif
    do
        extra=""
        if [ $ext == "tif" ]; then extra="-or -iname \*.tiff"; fi
        if [ $ext == "jpg" ]; then extra="-or -iname \*.jpeg"; fi
        nimg="$(find $camdir -type f -iname \*.$ext $extra | wc -l)"
        if [ $nimg -gt 0 ]
        then
            echo -n "$CAMERA $ext $nimg "
            qsub -v "CAMPATH=${camdir},CAMERA=${CAMERA},STARTDATE=$START,ENDDATE=$END,FORMAT=$ext,DEST=${DEST}" /g/data/xe2/phenomics/backups-working-dir/code/backup-camera.pbs
        else
            echo "$CAMERA $ext SKIPPING"
        fi
    done
done
