import numpy as np
import os, sys
import torch
import skimage.io as io
from dataset import TestDataset
from helpers import load_checkpoint, make_img_overlay, concatenate_images
from model import UNET
from mask_to_submission import *
from train import DEVICE, BATCH_SIZE, OUTPUT_DIR, SEED

torch.manual_seed(SEED)

IMG_PLOTS = False #save one test image with overlay and a concatenated image of the satellite test image with its prediction mask
IMG = 1 #index of the image saved, can be between 1 and 50

print('\nStart running...')
if not torch.cuda.is_available() :
	print("\nThings will go much quicker if you enable a GPU in Colab under 'Runtime / Change Runtime Type'")
else :
	print("\nYou are running the prediction of the test data on a GPU")

# Load the test set 
print('\nTest data loading...')
test_dir = "../data/test_set_images/"
test_set = TestDataset(test_dir)
test_loader = torch.utils.data.DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=False)


# Load checkpoint
root_dir = "../outputs"  
checkpoint_path = os.path.join(root_dir, 'parameters.pt')
model = UNET().to(DEVICE)
load_checkpoint(checkpoint_path, model)

# Model evaluation
model.eval() 

# Make and save test binary prediction images
save_path = os.path.join(root_dir, 'binary_masks')
if not os.path.isdir(save_path) :
	os.mkdir(save_path)
it = 1
print('\nDo not care about the warnings...')
for batch_x in test_loader :
	batch_x = batch_x.permute(0, 3, 1, 2).float()
	batch_x = batch_x.to(DEVICE)
	pred = model(batch_x)
	pred = pred.squeeze(1)
	pred = torch.sigmoid(pred)
	for i in range(BATCH_SIZE) : 
		mask = pred[i].cpu().detach().numpy() #we can not convert cuda tensor into numpy
		mask[mask>0.5] = 1
		mask[mask<=0.5] = 0
		mask_path = os.path.join(save_path, '%.3d' % it + '.png')
		io.imsave(mask_path, mask, check_contrast=False) 
		print('Prediction binary mask for test image {} is saved'.format(it))

		# Make some plot of test image number IMG if IMG_PLOTS = true
		if (IMG_PLOTS and it==IMG) :
			cimg_path = os.path.join(root_dir, 'cimg%.3d' % IMG + '.png')
			overlay_path = os.path.join(root_dir, 'overlay%.3d' % IMG + '.png')
			img = batch_x[i].permute(1, 2, 0)
			img_overlay =  make_img_overlay(img, mask)
			io.imsave(overlay_path, np.asanyarray(img_overlay), check_contrast=False)
			cimg = concatenate_images(img.cpu().detach().numpy(), mask)
			io.imsave(cimg_path, cimg, check_contrast=False)
			print('\nConcatenated image with satellite image and predicted mask for test image {}/50 saved in {}'.format(it,cimg_path))
			print('\nOverlay image for test image {}/50 saved in {}\n'.format(it,overlay_path))

		it = it + 1
print('\nYou can find all the test binary masks by following the path : {}'.format(save_path))

# Make a submission csv file
print('\nTransformation of the binary masks into a submission csv file...')
submission(save_path, root_dir)
print('\nYou can find the submission.csv file by following the path : {}'.format(root_dir))






