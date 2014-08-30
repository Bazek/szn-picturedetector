#!/usr/bin/env sh

# todo fix this path
TOOLS=../../build/tools

train_args = ""

# model configuration
if [ -n "$1"  ] then
	train_args = "-solver=$1"

# start iteration file
if [ -n "$2"  ] then
	train_args = "$train_args --snapshot=$2"

$TOOLS/caffe train $train_args

echo "Done."

