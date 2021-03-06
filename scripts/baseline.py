# Baseline model based on https://github.com/epfml/ML_course/blob/master/projects/project2/project_road_segmentation/tf_aerial_images.py

import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from sklearn.metrics import f1_score, accuracy_score
from sklearn.neural_network import MLPClassifier
from mask_to_submission import *
from PIL import Image
import skimage.io as io

################################ HELPERS ####################################
def value_to_class(v):
    """Assign a label to a patch v"""
    foreground_threshold = 0.25  # percentage of pixels > 1 required to assign a foreground label to a patch
    df = np.sum(v)
    if df > foreground_threshold:  # road
        return [0, 1]
    else:  # bgrd
        return [1, 0]

def img_crop(im, w, h):
    """Extract patches from a given image"""
    list_patches = []
    imgwidth = im.shape[0]
    imgheight = im.shape[1]
    is_2d = len(im.shape) < 3
    for i in range(0,imgheight,h):
        for j in range(0,imgwidth,w):
            if is_2d:
                im_patch = im[j:j+w, i:i+h]
            else:
                im_patch = im[j:j+w, i:i+h, :]
            list_patches.append(im_patch)
    return list_patches

def extract_features_2d(img):
    """Extract mean and variance from an image"""
    feat_m = np.mean(img)
    feat_v = np.var(img)
    feat = np.append(feat_m, feat_v)
    return feat

def extract_img_features(img):
    """Extract mean and variance from a patch-wise (16x16) image"""
    img_patches = img_crop(img, 16, 16)
    X = np.asarray([ extract_features_2d(img_patches[i]) for i in range(len(img_patches))])
    return X

def label_to_img(imgwidth, imgheight, w, h, labels):
    """Convert array of labels to an image"""
    im = np.zeros([imgwidth, imgheight])
    idx = 0
    for i in range(0,imgheight,h):
        for j in range(0,imgwidth,w):
            im[j:j+w, i:i+h] = labels[idx]
            idx = idx + 1
    return im

################################# MAIN ########################################
def main() :
    # Loading the data
    root_dir = "../data/training/"
    image_dir = root_dir + "images/"
    gt_dir = root_dir + "groundtruth/"

    files = os.listdir(image_dir)
    print("Loading images")
    images = np.asarray([mpimg.imread(image_dir + files[i]) for i in range(len(files))])
    print("Loading groundtruth images")
    gt = np.asarray([mpimg.imread(gt_dir + files[i]) for i in range(len(files))])

    # Use 16x16 patches
    img_patches = [img_crop(images[i], 16, 16) for i in range(len(files))]
    gt_patches = [img_crop(gt[i], 16, 16) for i in range(len(files))]
    # Linearize list of patches
    img_patches = np.asarray([img_patches[i][j] for i in range(len(img_patches)) for j in range(len(img_patches[i]))])
    gt_patches =  np.asarray([gt_patches[i][j] for i in range(len(gt_patches)) for j in range(len(gt_patches[i]))])
    labels = np.asarray([value_to_class(np.mean(gt_patches[i])) for i in range(len(gt_patches))])
    # Convert to dense 1-hot representation.
    labels.astype(np.float32)

    # Separate into training and validation set
    n = 0.8 # split ratio for train/val
    N = len(labels)
    idx = np.floor(n*N).astype('int32') # index to stop training set
    X_train = np.asarray([extract_features_2d(img_patches[i]) for i in np.arange(idx)])
    Y_train = np.asarray([labels[i] for i in np.arange(idx)])

    X_val = np.asarray([extract_features_2d(img_patches[i]) for i in np.arange(idx+1, N)])
    Y_val = np.asarray([value_to_class(np.mean(labels[i])) for i in np.arange(idx+1, N)])

    # Balance the training data if needed
    c0 = 0  # bgrd
    c1 = 0  # road
    for i in range(len(Y_train)):
        if Y_train[i][0] == 1:
            c0 = c0 + 1
        else:
            c1 = c1 + 1
    print('Number of data points per class before balancing: c0 = ' + str(c0) + ' c1 = ' + str(c1))
    print('Balancing training data...')
    min_c = min(c0, c1)
    idx0 = [i for i, j in enumerate(Y_train) if j[0] == 1]
    idx1 = [i for i, j in enumerate(Y_train) if j[1] == 1]
    new_indices = idx0[0:min_c] + idx1[0:min_c]
    X_train = X_train[new_indices, :]
    Y_train = Y_train[new_indices]
    c0 = 0
    c1 = 0
    for i in range(len(Y_train)):
        if Y_train[i][0] == 1:
            c0 = c0 + 1
        else:
            c1 = c1 + 1
    train_size = Y_train.shape[0]
    print('Number of data points per class after balancing: c0 = ' + str(c0) + ' c1 = ' + str(c1))

    # Fitting the model
    clf = MLPClassifier(max_iter=200,
                    hidden_layer_sizes=(10, 10),
                    random_state=5,
                    verbose=False,
                    learning_rate_init=1e-4,
                    learning_rate = 'adaptive')
    clf.fit(X_train, Y_train)


    # Testing the model with a validation set
    Y_pred = clf.predict(X_val)
    #print('Y val: {} and Y_pred: {}'.format(Y_val, Y_pred))

    acc0 = accuracy_score(Y_val[:,0], Y_pred[:,0])
    acc1 = accuracy_score(Y_val[:,1], Y_pred[:,1])
    f1 = f1_score(Y_val, Y_pred, average = 'micro')
    #TESTS: 
    print(np.sum(Y_val[:,0]==Y_pred[:,0])/Y_val.shape[0])
    print(np.sum(Y_val[:,1]==Y_pred[:,1])/Y_val.shape[0])
    print('F1 score: {}\t accuracy 0: {}\t acuracy 1: {}'.format(f1, acc0, acc1))


    # Test the model and generate a submission
    test_dir = "../data/test_set_images/"
    files_test = os.listdir(test_dir)
    images_test = []
    print("\nLoading test images")
    images_test = np.asarray([mpimg.imread(test_dir + 'test_' + str(i+1) + '/test_' + str(i+1) + '.png') for i in range(len(files_test))])

    # For each test image, make the patches, do the prediction and save the mask
    root_dir = "../outputs"
    save_path = os.path.join(root_dir, 'binary_masks')
    if not os.path.isdir(save_path) :
    	os.mkdir(save_path)
    h = images_test[1].shape[1]
    w = images_test[1].shape[0]

    for i, x in enumerate(images_test):
        X_test = extract_img_features(x)
        Y_test = clf.predict(X_test)
        mask = label_to_img(w, h, 16, 16, Y_test[:, 1])
        mask_path = os.path.join(save_path, '%.3d' % (i+1) + '.png')
        io.imsave(mask_path, mask, check_contrast=False)
        print('Prediction binary mask for test image {} is saved'.format(i))

    # Make a submission csv file
    print('\nYou can find all the test binary masks by following the path : {}'.format(save_path))
    print('\nTransformation of the binary masks into a submission csv file...')
    submission(save_path, root_dir)
    print('\nYou can find the submission.csv file by following the path : {}'.format(root_dir))



if __name__ == "__main__":
    main()
