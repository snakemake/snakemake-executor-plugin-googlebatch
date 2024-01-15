#!/bin/bash

url=$1

tmp=$(mktemp -d -t snek-install-XXXX)
rm -rf ${tmp}

git clone --depth 1 ${url} ${tmp}
cd ${tmp}
/opt/conda/bin/python -m pip install .
rm -rf ${tmp}
