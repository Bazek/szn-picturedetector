#!/usr/bin/env sh
# Compute the mean image from the imagenet training leveldb
# N.B. this is available in data/ilsvrc12

TOOLS=/www/picturedetector/caffe/build/tools

IMAGENET_TRAIN_NAME=$1
MEAN_FILE_NAME=$2

$TOOLS/compute_image_mean.bin $IMAGENET_TRAIN_NAME $MEAN_FILE_NAME

echo "Done."
