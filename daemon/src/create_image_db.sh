#!/usr/bin/env sh
# Create the imagenet leveldb inputs
# N.B. set the path to the imagenet train + val data dirs

TOOLS=/home/hol/caffe/build/tools

TRAIN_DATA=$1
VAL_DATA=$2
IMAGENET_TRAIN_NAME=$3
IMAGENET_VAL_NAME=$4

# Set RESIZE=true to resize the images to 256x256. Leave as false if images have
# already been resized using another tool.
RESIZE=false
RESIZE_SIZE=256
GRAY=false
SHUFFLE=false

if $RESIZE; then
  RESIZE_HEIGHT=" -resize_height $RESIZE_SIZE"
  RESIZE_WIDTH=" -resize_width $RESIZE_SIZE"
else
  RESIZE_HEIGHT=""
  RESIZE_WIDTH=""
fi

if $GRAY; then
  USE_GRAY=" -gray 1"
else
  USE_GRAY=""
fi

if $SHUFFLE; then
  USE_SHUFFLE=" -shuffle 1"
else
  USE_SHUFFLE=""
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

GLOG_logtostderr=1 $TOOLS/convert_imageset $RESIZE_HEIGHT $RESIZE_WIDTH \
    / \
    $TRAIN_DATA \
    $IMAGENET_TRAIN_NAME

echo "Creating val leveldb..."

GLOG_logtostderr=1 $TOOLS/convert_imageset $RESIZE_HEIGHT $RESIZE_WIDTH \
    / \
    $VAL_DATA \
    $IMAGENET_VAL_NAME

echo "Done."
