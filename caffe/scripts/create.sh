#!/usr/bin/env sh
# Create the imagenet leveldb inputs
# N.B. set the path to the imagenet train + val data dirs

TOOLS=/www/picturedetector/caffe/build/tools
DATA=/www/picturedetector/caffe/gen

TRAIN_DATA=$1
VAL_DATA=$2
IMAGENET_TRAIN_NAME=$3
IMAGENET_VAL_NAME=$4

# Set RESIZE=true to resize the images to 256x256. Leave as false if images have
# already been resized using another tool.
RESIZE=false
if $RESIZE; then
  RESIZE_HEIGHT=256
  RESIZE_WIDTH=256
else
  RESIZE_HEIGHT=0
  RESIZE_WIDTH=0
fi

if [ ! -f "$TRAIN_DATA" ]; then
  echo "Error: TRAIN_DATA is not a path to a file: $TRAIN_DATA"
  echo "Set the TRAIN_DATA variable in create_imagenet.sh to the path" \
       "where the ImageNet training data is stored."
  exit 1
fi

if [ ! -f "$VAL_DATA" ]; then
  echo "Error: VAL_DATA is not a path to a file: $VAL_DATA"
  echo "Set the VAL_DATA variable in create_imagenet.sh to the path" \
       "where the ImageNet validation data is stored."
  exit 1
fi

echo "Creating train leveldb..."

GLOG_logtostderr=1 $TOOLS/convert_imageset.bin \
    / \
    $TRAIN_DATA \
    $IMAGENET_TRAIN_NAME 1
    $RESIZE_HEIGHT $RESIZE_WIDTH

echo "Creating val leveldb..."

GLOG_logtostderr=1 $TOOLS/convert_imageset.bin \
    / \
    $VAL_DATA \
    $IMAGENET_VAL_NAME 1
    $RESIZE_HEIGHT $RESIZE_WIDTH

echo "Done."
