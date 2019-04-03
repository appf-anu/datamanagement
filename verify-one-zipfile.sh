if [ "${ZIP:-SDLKFJSD}" == "SDLKFJSD" ]
then
    ZIP=$1
fi
if [ -z "$ZIP" ]
then
    echo USAGE: verify-one-zipfile.sh bundled_images.zip >&2
    exit 1
fi

CAMUPLOAD=/g/data/xe2/phenomics/camupload/
CAM=$(basename $ZIP)
CAM=${CAM%%_*}

CAMDIR=$(find $CAMUPLOAD -maxdepth 2 -mindepth 2 -type d -name $CAM)
if [ -z $CAMDIR ]
then
    echo "Can't find camera '$CAM' for $ZIP" >&2
    exit 1
fi

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

cd $TMP
unzip -o $ZIP >/dev/null
cd $CAM
ZIPFILES=$(find -type f)

for file in ${ZIPFILES}
do
    # file will be yyyy/yy_mm/yy_mm_dd/cam_yyy_mm.... except proper
    if [ -f $CAMDIR/$file ] # i.e. if cam is ts-organised in camupload
    then
        CU=$CAMDIR/$file
    elif [ -f $CAMDIR/$(basename $file) ] # if flat structure
    then
        CU=$CAMDIR/$(basename $file)
    else
        echo "Can't find $file, perhaps it has been deleted" >&2
        continue
        # below is how to find the file with funky non-organised structures
        # takes ages, and this case will mostly be triggered by removed files
        # this is a bit too slow, tidy up this crap later
        #CU=$(find $CAMDIR -type f -name $(basename $file)) 
    fi

    if cmp -s $CU $file 2>/dev/null # check file contents exactly equal
    then
        echo rm -vf $CU # pretend to delete
    fi
done
