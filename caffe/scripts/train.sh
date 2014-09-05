#!/usr/bin/env sh

TOOLS=/www/picturedetector/caffe/build/tools
TRAIN_ARGS=""

# model configuration
if [ -n "$1"  ]; then
    TRAIN_ARGS="-solver=$1"
fi

# start iteration file
if [ -n "$2"  ]; then
    TRAIN_ARGS="$TRAIN_ARGS --snapshot=$2"
fi

$TOOLS/caffe train $TRAIN_ARGS

echo "Done."

