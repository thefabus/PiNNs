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

x, y, mn, std, xt = utils.loaddata('NAS', 0, dir="./data/", raw=True)

yp_tr = pd.read_csv("./data/train_soro.csv")
yp_te = pd.read_csv("./data/test_soro.csv")
yp_tr.index = pd.DatetimeIndex(yp_tr['date'])
yp_te.index = pd.DatetimeIndex(yp_te['date'])
yptr = yp_tr.drop(yp_tr.columns.difference(['GPPp']), axis=1)
ypte = yp_te.drop(yp_te.columns.difference(['GPPp']), axis=1)

yp = pd.concat([yptr, ypte])


ypp = (yp[1:]-mn['GPP'])/std['GPP']

splits = len(x.index.year.unique())

x.index, y.index = np.arange(0, len(x)), np.arange(0, len(y))

arch_grid = NAS.ArchitectureSearchSpace(x.shape[1], y.shape[1], 200, 4)

# architecture search
layersizes = NAS.ArchitectureSearch(arch_grid, {'epochs': 300, 'batchsize': 8, 'lr':0.01}, x, y, splits, "arSres")

# Hyperparameter Search Space
hpar_grid = NAS.HParSearchSpace(200)

# Hyperparameter search
hpars, grid = NAS.HParSearch(layersizes, hpar_grid, x, y, splits, "hpres")

print( 'hyperparameters: ', hpars)


grid.to_csv("./Nres.csv")

