szn-picturedetector
===================

There is problem with converting mean file in protobinary format to npy format.
Here is mentioned fix: https://github.com/BVLC/caffe/issues/420
Problem is solved with fixed copy of function blobproto_to_array from caffe io.py file.
This function is created in daemon.py.