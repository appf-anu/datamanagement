#!/bin/bash
START=2000_01_01
END=2020_01_01
CAMBASE=/g/data/xe2/phenomics/camupload
DEST=/g/data/xe2/phenomics/camupload-backups/gigavision/
mkdir -p $DEST
CAMERAS=(ARB-GV-ANU-HILL-C01)

set -e
trap "exit 1" INT

for CAMERA in $CAMERAS
do
    camdir=${CAMBASE}/gigavision/${CAMERA}
    for ext in jpg tif
    do
	echo -n "$CAMERA $ext "
	qsub -v "CAMPATH=${camdir},CAMERA=${CAMERA},STARTDATE=$START,ENDDATE=$END,FORMAT=$ext,DEST=${DEST}" /g/data/xe2/phenomics/backups-working-dir/code/backup-camera.pbs
    done
done

