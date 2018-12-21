
mkdir -p /g/data/xe2/phenomics/camupload-backups/
START=2000_01_01
END=2020_01_01
CAMUPLOAD=/g/data/xe2/phenomics/camupload
#CAMERAS=("GC36L" "GC36R")
#CAMERAS=$(echo GC{02,03,04,05,35,36,37}-Picam GC36L GC36R)
CAMERAS=$(echo GC{02,03,04,05,35,36,37}{L,R,-Picam})

set -e

for CAMERA in $CAMERAS
do
    camdir=${CAMUPLOAD}/picam/${CAMERA}
    for ext in jpg cr2 tif
    do
        nimg="$(find $camdir -type f -iname \*.$ext | wc -l)"
        if [ $nimg -gt 0 ]
        then
            echo -n "$CAMERA $ext $nimg "
            qsub -v CAMPATH=${CAMUPLOAD}/picam/${CAMERA},CAMERA=${CAMERA},STARTDATE=$START,ENDDATE=$END,FORMAT=$ext /g/data/xe2/phenomics/backups-working-dir/code/backup-camera.pbs
        fi
    done
done
