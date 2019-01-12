#!/usr/bin/env python3
from sys import stdin

dir = "."
files = []
for line in stdin:
    line=line.rstrip()
    if line == "" and dir and files:
        for f in files:
            print(dir + "/" + f)
        dir = "???"
        files = []
    elif line.endswith(":"):
        dir = line.rstrip(":")
    else:
        files.append(line)
for f in files:
    print(dir + "/" + f)
