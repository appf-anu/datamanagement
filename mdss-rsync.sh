#!/bin/bash

if [ $# -lt 2 ]
then
    echo "USAGE: $0 SOURCE [SOURCE...] MDSS_DEST"
    echo
    echo "One can do DRYRUN=1 $0 ... to show what would be done rather than doing it"
    exit 1
fi

set -eu
SOURCES="${@:1:$# - 1}"
MDSSDEST="${@: -1}"

do=""
if [ "${DRYRUN:-no}" != "no" ]
then
    do="echo"
fi

for src in $SOURCES
do
    if [ ! -d $src ]
    then
        echo "ERROR: $src doesn't exist"
        exit 1
    fi
    echo "Source: $src"
    pushd "$(dirname "$src")" >/dev/null 2>&1
    for file in $(find "$(basename "$src")" -type f | sort)
    do
        echo -n $(basename "$file") " "


        here=$(ls -l "$file" | cut -f 5-8 -d " ")
        remote=$( mdss ls -l "$MDSSDEST/$file" 2>/dev/null | cut -f 5-8 -d " " || true )

        if [ "$here" == "$remote" ]
        then
            echo "skip"
            continue
        fi

        destdir=$(dirname "$MDSSDEST/$file")
        $do chmod ug=rw,o= "$file" || true
        $do mdss mkdir -m 770 "$destdir"
        $do mdss put "$file" "$destdir"
        echo "sync"
    done
    popd >/dev/null 2>&1
done
