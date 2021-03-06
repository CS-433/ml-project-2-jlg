import os
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

SEED = 66478
torch.manual_seed(SEED)

class ImgDataset(Dataset):
    """ Dataset loader - Train or validation mode
    """
    def __init__(self, image_dir, gt_dir, mode="train", split_ratio=0.8):
        self.mode = mode
        self.image_dir = image_dir
        self.gt_dir = gt_dir

        ids = [int(file[9:12]) for file in os.listdir(image_dir)]
        n = len(ids)
        if self.mode == "train" :
            self.ids = ids[0:int(n * split_ratio)]
        if self.mode == "val":
            self.ids = ids[int(n * split_ratio):n]
        self.ids.sort()

        self.images = os.listdir(image_dir) #list all files in that folder
        self.gt = os.listdir(gt_dir)
        print(f'Creating {mode} dataset with {len(self.ids)} samples')

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, index):
        idx = self.ids[index]-1 # bc index [0,99] and ids [1,100] and images[idx] needs [0,99]
        image_path = os.path.join(self.image_dir, self.images[idx])
        gt_path = os.path.join(self.gt_dir, self.images[idx])
        image = np.array(Image.open(image_path).convert("RGB"))
        gt = np.array(Image.open(gt_path).convert("L"), dtype=np.float32)
        gt[gt>0.5] = 1
        gt[gt<=0.5] = 0
        return image, gt

class TestDataset(Dataset):
    """ Test dataset loader
    """
    def __init__(self, test_dir):
        self.dir = test_dir
        self.images = os.listdir(test_dir)
        print(f'Creating test dataset')

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path = os.path.join(self.dir + 'test_' + str(index+1) + '/test_' + str(index+1) + '.png')
        image = np.array(Image.open(image_path).convert("RGB"))
        return image
