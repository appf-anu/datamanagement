RESOURCES=/g/data/xe2/phenomics/resources/cameras/
CAMUPLOAD=/g/data/xe2/phenomics/camupload/
TSORG=/g/data/xe2/phenomics/go-timestreamtools/tsorganize_linux-amd64

CAMERAS=$(cd $CAMUPLOAD && find ipcam picam -maxdepth 1 -mindepth 1 -type d)
for cam in ${CAMERAS}
do
    echo $cam
done


cam="picam/BK04L"
cam="ipcam/Darwinia08-IPCam01"


TMP=$(mktemp -d)
CUTMP=$TMP/camupload/$cam
BUTMP=$TMP/bundled/
mkdir -p $CUTMP
mkdir -p $BUTMP/$cam
trap "rm -rvf $TMP" EXIT


# Organise camupload to temp
find $CAMUPLOAD/$cam -type f  | \
    $TSORG -output $TMP/camupload/$cam


# Extract zipbundles to temp
find $RESOURCES/$cam -type f -name \*.zip | \
    parallel -j ${PBS_NCPUS:-2} \
        cd $TMP/bundled/$(dirname $cam) \&\& unzip -o {}

files=$(cd $TMP/camupload/$cam && find -type f)
for file in ${files}
do
    if cmp $TMP/camupload/$cam/$file $TMP/bundled/$cam/$file 2>/dev/null
    then
        orig_file=$(find $CAMUPLOAD/$cam -name $(basename $file))
        echo $orig_file >> ${cam//\//_}_OK_files.txt
    fi
done
