#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
    echo "$0: exactly 1 argument expected"
    exit 3
fi

if [ $1 = "build" ]; then
    echo "Python, no building needed."
elif [ $1 = "install" ]; then
    python setup.py install
else
    echo "Unrecognized command!"
    exit 2
fi
