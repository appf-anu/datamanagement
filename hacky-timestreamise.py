#!/usr/bin/env python3

import glob, os, shutil

dirs = list(filter( os.path.isdir, glob.glob("*")))
dirs = list(filter(lambda x: not x.startswith("_") and "_" in x, dirs))
for d in dirs:
    year,month,day,hour = d.split("_")
    newdir = "{0}/{0}_{1}/{0}_{1}_{2}/".format(year, month, day)
    print(newdir)
    os.makedirs(newdir, exist_ok=True)
    try:
        shutil.move(d, newdir)
    except:
        print('Skipping {}, already exists.'.format(d))       

