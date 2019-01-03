# rename files to a set string pus incrementing number

import os

# directory to work in
working_dir = '.'
# what you're changing the name to
new_file_string = 'chess'
# number to start at
i = 1
# file extension to apply to all the files
extension = 'jpg'

# list contents of working_dir and extract only the files (exclude directories)
files = []
for (dirpath, dirnames, filenames) in os.walk(working_dir):
    files.extend(filenames)
    break

for f in files:
    try:
        os.rename (f, new_file_string+"{:0=2d}.{}".format(i, extension))
    except Exception as e:
        print('Exception is: {0}'.format(e)) 
    i += 1
