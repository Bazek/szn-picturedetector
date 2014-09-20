#!/usr/bin/env sh

TOOLS=/www/picturedetector/caffe/build/tools

if [ -z "$1" ]; then
  echo "Missing train val model file"
  exit
else
  MODEL="--model=$1"
fi

if [ -z "$2" ]; then
  ITERATIONS=""
else
  ITERATIONS="--iterations=$2"
fi

if [ -z "$3" ]; then
  echo "Using CPU! To time GPU mode, use:"
  echo "    ./time_imagenet.sh <device ID>"
  echo "(Try ./time_imagenet.sh 0 if you have just one GPU.)"
  sleep 3  # Let the user read
  GPU=""
else
  GPU="--gpu=$3"
fi

$TOOLS/caffe time ${MODEL} ${GPU} ${ITERATIONS}

echo "Done."
