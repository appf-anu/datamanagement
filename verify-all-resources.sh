set -xo pipefail
RESOURCES=/g/data/xe2/phenomics/resources/cameras/
find $RESOURCES/picam/GC36* -type f -name \*_2016_\*.zip | tee /dev/stderr | parallel bash /g/data/xe2/phenomics/datamanagement-workspace/code/verify-one-zipfile.sh | tee /g/data/xe2/phenomics/datamanagement-workspace/CAMUPLOAD_CLEANUP${PBS_JOBID}.sh

