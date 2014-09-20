szn-picturedetector
===================

There is problem with converting mean file in protobinary format to npy format.
Here is mentioned fix: https://github.com/BVLC/caffe/issues/420
You must find io.py file in your PYTHONPATH
(for example: /usr/lib/python2.7/dist-packages/caffe/io.py)
and edit lines 107 and 110.
Lines before edit:
"blob.num, blob.channels, blob.height, blob.width)"

Lines after edit:
"blob.channels, blob.height, blob.width)"

The whole method will look like this:
def blobproto_to_array(blob, return_diff=False):
  """Convert a blob proto to an array. In default, we will just return the data,
  unless return_diff is True, in which case we will return the diff.
  """
  if return_diff:
    return np.array(blob.diff).reshape(
      blob.channels, blob.height, blob.width)
  else:
    return np.array(blob.data).reshape(
      blob.channels, blob.height, blob.width)

If you don't want to change the files (or you can't). You will not be able
to use mean file in caffe classification. You must set empty path to
neural network mean_file property in database.