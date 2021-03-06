#!/usr/bin/env python3

import os
import numpy as np
import matplotlib.image as mpimg
import re

foreground_threshold = 0.25 # percentage of pixels > 1 required to assign a foreground label to a patch

def patch_to_label(patch):
    """Assign a label to a patch"""
    df = np.mean(patch)
    if df > foreground_threshold:
        return 1
    else:
        return 0


def mask_to_submission_strings(image_filename):
    """Reads a single image and outputs the strings that should go into the submission file"""
    img_number = int(re.search(r"\d+", image_filename).group(0))
    im = mpimg.imread(image_filename)
    patch_size = 16
    for j in range(0, im.shape[1], patch_size):
        for i in range(0, im.shape[0], patch_size):
            patch = im[i:i + patch_size, j:j + patch_size]
            label = patch_to_label(patch)
            yield("{:03d}_{}_{},{}".format(img_number, j, i, label))


def masks_to_submission(submission_filename, *image_filenames):
    """Converts images into a submission file"""
    with open(submission_filename, 'w') as f:
        f.write('id,prediction\n')
        for fn in image_filenames[0:]:
            print('file name for write {}'.format(fn))
            f.writelines('{}\n'.format(s) for s in mask_to_submission_strings(fn))


def submission(save_path, sub_path, sub_filename = 'submission.csv', test_size=50) :
    """ Make a submission file from the predicted binary masks"""
    sub_filename = os.path.join(sub_path ,sub_filename)
    image_filenames = []
    for i in range(1, test_size+1):
        image_filename = os.path.join(save_path, '%.3d' % i + '.png')
        image_filenames.append(image_filename)
    masks_to_submission(sub_filename, *image_filenames)

