#!/bin/bash

if [ $# -lt 2 ]
then
    echo "USAGE: $0 SOURCE [SOURCE...] MDSS_DEST"
    echo
    echo "One can do DRYRUN=1 $0 ... to show what would be done rather than doing it"
    exit 1
fi

set -euo pipefail
SOURCES="${@:1:$# - 1}"
MDSSDEST="${@: -1}"

do=""
if [ "${DRYRUN:-no}" != "no" ]
then
    do="echo"
fi

function putfile {
    echo -n $(basename "$1") " "
    here=$(ls -l "$1" | cut -f 5-8 -d " ")
    remote=$( mdss ls -l "$2" 2>/dev/null | cut -f 5-8 -d " " || true )

    if [ "$here" == "$remote" ]
    then
        echo "skip"
        continue
    fi

    destdir=$(dirname "$2")
    $do chmod ug=rw,o= "$1" 2>/dev/null || true
    $do mdss mkdir -m 770 "$destdir"
    $do mdss put "$1" "$destdir"
    echo "sync"
}

for src in $SOURCES
do
    if [ -d $src ]
    then
        echo "Descending into directory: $src"
        pushd "$(dirname "$src")" >/dev/null 2>&1
        for file in $(find "$(basename "$src")" -type f | sort)
        do

            putfile "$file" "$MDSSDEST/$file"
        done
        popd >/dev/null 2>&1
    elif [ -f $src ]
    then
        putfile "$src" "$MDSSDEST/$src"
    else
        echo "ERROR: $src doesn't exist"
        exit 1
    fi
done
