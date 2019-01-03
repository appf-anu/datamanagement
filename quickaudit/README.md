# quickaudit

Does a quick audit of images


```
# install zbar C library.
# sudo apt install libzbar-dev on Debian
# sudo pacman -Sy zbar on Arch

# install python deps
pip3 install zbarlight numpy rawpy pillow

# Pipe list of files into quickaudit, save resulting tsv
find -type f -iname \*.jpg | python3 ./quickaudit.py | tee image_audit.tsv
```
