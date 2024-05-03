#!/bin/bash
#
# Wrapper for python app PicGridder.py
# - 1st param: /source-dir-of-pictures/
# - 2nd param: /destination-dir-of-bigpicture/

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

docker run -v $1:/apps/data/pic-source \
           -v $2:/apps/data/pic-dest \
           -v $SCRIPT_DIR/apps:/apps --rm python-env:latest \
           python ./PicGridder.py -q
