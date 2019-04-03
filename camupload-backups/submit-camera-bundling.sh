#!/bin/bash
START=2000_01_01
END=2020_01_01
CAMUPLOAD=/g/data/xe2/phenomics/camupload

set -e
trap "exit 1" INT

for TYPE in picam ipcam
do
    if [ $TYPE == picam ]
    then
        CAMERAS=$(echo GC{02,03,04,05,35,36,37}{L,R,-Picam} BK{04,07}{L,R,-Picam} GC37L-NIR-C01 GC37R-NIR-C02 Eucalyptus02-Cam01 Eucalyptus02-Picam Eucalyptus02-Cam02)
    else
        CAMERAS=$(echo Darwinia08-IPCam{01..03} Eucalyptus{01..06}-IPCam{01..04} Eucalyptus{01,02,04,05,06}-IPCam05 GC36-IPCam03 GC36-IPCam04 )
    fi
    for CAMERA in $CAMERAS
    do
        camdir=${CAMUPLOAD}/$TYPE/${CAMERA}
        for ext in tif cr2 jpg
        do
            extra=""
            if [ $ext == "tif" ]; then extra="-or -iname \*.tiff"; fi
            if [ $ext == "jpg" ]; then extra="-or -iname \*.jpeg"; fi
            nimg="$(find $camdir -type f -iname \*.$ext $extra | wc -l)"
            if [ $nimg -gt 0 ]
            then
                echo -n "$CAMERA $ext $nimg "
                qsub -v "CAMPATH=${camdir},CAMERA=${CAMERA},STARTDATE=$START,ENDDATE=$END,FORMAT=$ext,TYPE=${TYPE}" /g/data/xe2/phenomics/datamanagement-workspace/code/camupload-backups/backup-camera.pbs
            else
                echo "$CAMERA $ext SKIPPING"
            fi
        done
    done
done
