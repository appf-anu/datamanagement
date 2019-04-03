#!/bin/bash

module load parallel

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
DRYRUN="${DRYRUN:-no}"
export DRYRUN



function putfile {
    do=""
    if [ "${DRYRUN:-no}" != "no" ]
    then
        do="echo"
    fi
    echo -n $(basename "$1") " "
    here=$(ls -l "$1" | cut -f 5-8 -d " ")
    remote=$( mdss ls -l "$2" 2>/dev/null | cut -f 5-8 -d " " || true )

    if [ "$here" == "$remote" ]
    then
        echo "skip"
        return
    fi

    destdir=$(dirname "$2")
    $do mdss mkdir -m 770 "$destdir"
    $do mdss put "$1" "$destdir"
    $do mdss chmod ug=rw,o= "$2" 2>/dev/null || true

    echo "sync"
}
export -f putfile

(for src in $SOURCES
do
    if [ -d $src ]
    then
        echo "Descending into directory: $src" >&2
        pushd "$(dirname "$src")" >/dev/null 2>&1
        for file in $(find "$(basename "$src")" -type f | sort)
        do

            echo putfile "$(readlink -f $file)" "$MDSSDEST/$file"
        done
        popd >/dev/null 2>&1
    elif [ -f $src ]
    then
        echo putfile "$(readlink -f $src)" "$MDSSDEST/$src"
    else
        echo "ERROR: $src doesn't exist" >&2
        exit 1
    fi
done) | parallel -j 3
