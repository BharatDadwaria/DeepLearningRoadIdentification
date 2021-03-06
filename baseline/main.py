#in.ipynb

#Automatically generated by Colaboratory.

#Original file is located at
    #https://colab.research.google.com/drive/1Q1tC_mt8qshnnRBpcoOy3LbtQW2R0bpk
"""

#n[12]:


from __future__ import print_function
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
from torchvision import datasets, transforms
from torch.autograd import Variable
import sys



# In[13]:


import os
import random

import numpy as np
import pandas as pd

import torchvision.transforms as transforms

import sys
from data_helper import UnlabeledDataset, LabeledDataset, ObjDetectionLabeledDataset
from helper import collate_fn, draw_box

import utils
from engine import train_one_epoch, evaluate


# In[23]:


parser = argparse.ArgumentParser(description='Object Detection task')


parser.add_argument('--data', type=str, default='data', metavar='D',
                    help="folder where data is located.")
parser.add_argument('--batch_size', type=int, default=2, metavar='N',
                    help='input batch size for training (default: 2)')
parser.add_argument('--epoch', type=int, default=20, metavar='E',
                    help='number of epochs to train (default: 10)')
parser.add_argument('--lr', type=float, default=0.005, metavar='LR',
                    help='learning rate (default: 0.01)')
parser.add_argument('--momentum', type=float, default=0.09, metavar='M',
                    help='SGD momentum (default: 0.09)')
parser.add_argument('--seed', type=int, default=0, metavar='S',
                    help='random seed (default: 0)')
parser.add_argument('--log-interval', type=int, default=10, metavar='LI',
                    help='how many batches to wait before logging training status')
parser.add_argument('--unlabelledSceneIndex', type=int, default=106, metavar='U',
                    help='unlabelled scene index')
parser.add_argument('--labelledSceneIndex', type=int, default=130, metavar='L',
                    help='labelled scene index')
parser.add_argument('--validationSceneIndex', type=int, default=130, metavar='V',
                    help='validation scene index')


# In[ ]:





# In[26]:


#args = parser.parse_args() # uncomment for command line


# In[8]:


random.seed(0)
np.random.seed(0)
torch.manual_seed(0);


# In[ ]:


image_folder = 'data'
annotation_csv = 'data/annotation.csv'


# In[ ]:


# You shouldn't change the unlabeled_scene_index
# The first 106 scenes are unlabeled
unlabeled_scene_index = np.arange(106)
# The scenes from 106 - 133 are labeled
# You should devide the labeled_scene_index into two subsets (training and validation)
labeled_scene_index = np.arange(106, 130)

## validation scene index.
validation_scene_index = np.arange(130, 134)


# In[ ]:


transform = transforms.Compose([
    transforms.ToTensor()
])


# In[ ]:


# Data Loading and validation.

# The labeled dataset can only be retrieved by sample.
# And all the returned data are tuple of tensors, since bounding boxes may have different size
# You can choose whether the loader returns the extra_info. It is optional. You don't have to use it.
labeled_trainset = LabeledDataset(image_folder=image_folder,
                                  annotation_file=annotation_csv,
                                  scene_index=labeled_scene_index,
                                  transform=transform,
                                  extra_info=True
                                 )
trainloader = torch.utils.data.DataLoader(labeled_trainset, batch_size=2, shuffle=True, num_workers=2,drop_last=True, collate_fn=collate_fn)


# In[ ]:


# The labeled dataset can only be retrieved by sample.
# And all the returned data are tuple of tensors, since bounding boxes may have different size
# You can choose whether the loader returns the extra_info. It is optional. You don't have to use it.
validation_trainset = LabeledDataset(image_folder=image_folder,
                                  annotation_file=annotation_csv,
                                  scene_index=validation_scene_index,
                                  transform=transform,
                                  extra_info=True
                                 )
valLoader = torch.utils.data.DataLoader(validation_trainset, batch_size=2, shuffle=True, num_workers=2, drop_last=True, collate_fn=collate_fn)



TrainUpTrainset = ObjDetectionLabeledDataset(image_folder=image_folder,
                                  annotation_file=annotation_csv,
                                  scene_index=labeled_scene_index,
                                  transform=transform,
                                  extra_info=True,
                                  batch_size = 2
                                 )
TrainLoaderNew = torch.utils.data.DataLoader(TrainUpTrainset, batch_size=2, shuffle=True, num_workers=2, collate_fn=collate_fn)


validationUpTrainset = ObjDetectionLabeledDataset(image_folder=image_folder,
                                  annotation_file=annotation_csv,
                                  scene_index=validation_scene_index,
                                  transform=transform,
                                  extra_info=True,
                                  batch_size = 2
                                 )
valLoaderNew = torch.utils.data.DataLoader(validationUpTrainset, batch_size=2, shuffle=True, num_workers=2, collate_fn=collate_fn)



# In[ ]:


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# In[ ]:


# import your model.

from modelobj import NetObj
mdl = NetObj()
model = mdl.model



#print(model)
if torch.cuda.device_count() > 1:
    print("Let's use", torch.cuda.device_count(), "GPUs!")
    model = nn.DataParallel(model)

model.to(device)


# In[ ]:


# Optimizer
params = [p for p in model.parameters() if p.requires_grad]
optimizerNew = torch.optim.SGD(params, lr=0.005,
                            momentum=0.09, weight_decay=0.0005)

# and a learning rate scheduler which decreases the learning rate by
# 10x every 3 epochs
lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizerNew,
                                               step_size=3,
                                               gamma=0.1)


# In[ ]:


# loss func

def modify_output_for_loss_fn(loss_fn, output, dim):
    if loss_fn == "ce":
        return output
    if loss_fn == "mse":
        return F.softmax(output, dim=dim)
    if loss_fn == "nll":
        return F.log_softmax(output, dim=dim)
    if loss_fn in ["bce", "wbce", "wbce1"]:
        return torch.sigmoid(output)


# In[ ]:

for epoch in range(0, 20):
  # train for one epoch, printing every 10 iterations
  train_one_epoch(model, optimizerNew, TrainLoaderNew, device, epoch, print_freq=10)
  # update the learning rate
  lr_scheduler.step()
  # evaluate on the test dataset
  evaluate(model, valLoaderNew, device=device)

  model_file = 'modelobj/fasterrcnn_model_' + str(epoch) + '.pth'
  torch.save({'modelObjectDetection_state_dict': model.state_dict()},model_file)
  print('\nSaved model to ' + model_file )

!zip -r /content/modelobj.zip /content/modelobj

from google.colab import files
files.download("/content/modelobj.zip")

'''from google.colab import drive
drive.mount('/data/')
from pathlib import Path
base_dir = ('/data/My Drive')'''

#!cp  /data/My\ Drive/DeepLearning/student_data.zip /content/
#!unzip student_data.zip

#pip install numpy==1.17.4


