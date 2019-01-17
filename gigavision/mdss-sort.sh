#!/bin/bash
HERE=$(dirname $(readlink -f $0))
for file in $(mdss ls -R phenomics/gigavision-archives/  | $HERE/../lsR2lof.py | grep -P "201\d_\d\d_\d\d.*.tar")
do
    fn=$(basename $file)
    cam=$(echo $fn | cut -f 1 -d '~' )
    hour=$(basename $fn .tar | cut -f 2 -d '~')
    YMD=( $(echo $hour | tr "_" '\n') )
    destdir=phenomics/resources/cameras/gigavision/$cam/${YMD[0]}/${YMD[0]}_${YMD[1]}/${YMD[0]}_${YMD[1]}_${YMD[2]}/${YMD[0]}_${YMD[1]}_${YMD[2]}_${YMD[3]}
    mdss mkdir $destdir
    mdss mv $file $destdir/$fn
    echo mv $file $destdir/$fn
done
