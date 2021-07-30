# !/usr/bin/env python
# coding: utf-8
import utils
import NAS
import utils
import trainloaded
import embtraining
import torch
import pandas as pd
import numpy as np

x, y, mn, std, xt = utils.loaddata('NAS', 1, dir="./data/", raw=True)
splits = len(x.index.year.unique())
print(splits)
x.index, y.index = np.arange(0, len(x)), np.arange(0, len(y))

arch_grid = NAS.ArchitectureSearchSpace(x.shape[1], y.shape[1], 200, 4)

# architecture search
layersizes = NAS.ArchitectureSearch(arch_grid, {'epochs': 300, 'batchsize': 8, 'lr':0.01}, x, y, splits, "arSmlp")

# Hyperparameter Search Space
hpar_grid = NAS.HParSearchSpace(200)

# Hyperparameter search
hpars, grid = NAS.HParSearch(layersizes, hpar_grid, x, y, splits, "hpmlp")

print( 'hyperparameters: ', hpars)


grid.to_csv("./Nmlp.csv")
