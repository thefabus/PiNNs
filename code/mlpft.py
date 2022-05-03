# !/usr/bin/env python
# coding: utf-8
import utils
import HP
import torch
import pandas as pd
import numpy as np
import random
import training
import argparse

parser = argparse.ArgumentParser(description='Define data usage and splits')
parser.add_argument('-d', metavar='data', type=str, help='define data usage: full vs sparse')
#parser.add_argument('-s', metavar='splits', type=int, help='define number of splits')
args = parser.parse_args()

print(args)

def mlpft(data_use="full"):
    if data_use == 'sparse':
        x, y, xt = utils.loaddata('NAS', 1, dir="./data/", raw=True, sparse=True)
    else:
        x, y, xt = utils.loaddata('NAS', 1, dir="./data/", raw=True)
    print(x.shape)
    print(xt.shape)
    
    train_x, train_y = x[x.index.year.isin([2004])], y[y.index.year.isin([2004])].to_frame()
    test_x, test_y = x[x.index.year.isin([2005])][1:], y[y.index.year.isin([2005])][1:].to_frame()
    print('TRAINTEST_', train_x, train_y)
    print(test_x, test_y)
    
    train_x.index, train_y.index = np.arange(0, len(train_x)), np.arange(0, len(train_y))
    test_x.index, test_y.index = np.arange(0, len(test_x)), np.arange(0, len(test_y))
    
    res_as = pd.read_csv(f"/scratch/project_2000527/pgnn/results/NmlpAS_{data_use}.csv")
    a = res_as.loc[res_as.ind_mini.idxmin()][1:5]
    b = a.to_numpy()
    layersizes = list(b[np.isfinite(b)].astype(int))
    print('layersizes', layersizes)

    model_design = {'layersizes': layersizes}

    res_hp = pd.read_csv(f"/scratch/project_2000527/pgnn/results/NmlpHP_{data_use}.csv")
    a = res_hp.loc[res_hp.ind_mini.idxmin()][1:3]
    b = a.to_numpy()
    print(b)
    lrini = b[0]
    bs = b[1]
    
    lrs = []
    for i in range(300):
        l = round(random.uniform(1e-8, lrini),8)
        if l not in lrs:
            lrs.append(l)
            
    print(lrs, len(lrs))
    mse_train_mean = []
    mse_val_mean = []
    mse_train_sd = []
    mse_val_sd = []

    for i in range(300):
        
        hp = {'epochs': 1000, #orignially: 2000
              'batchsize': int(bs),
              'lr': lrs[i]}
        
        data_dir = "./data/"
        data = "mlp"
        loss = training.finetune(hp, model_design, (train_x, train_y), (test_x, test_y), data_dir, data, reg=None, emb=False)
        mse_train_mean.append(np.mean(loss['train_loss']))
        mse_val_mean.append(np.mean(loss['val_loss']))
        mse_train_sd.append(np.std(loss['train_loss']))
        mse_val_sd.append(np.std(loss['val_loss']))

    df = pd.DataFrame(lrs)
    df['train_loss'] = mse_train_mean
    df['val_loss'] = mse_val_mean
    df["train_loss_sd"] = mse_train_sd
    df["val_loss_sd"] = mse_val_sd
    df["ind_mini"] = ((np.array(mse_val_mean)**2 + np.array(mse_val_sd)**2)/2)

    print("Random hparams search best result:")
    print(df.loc[[df["ind_mini"].idxmin()]])
    lr = lrs[df["ind_mini"].idxmin()]
    print("Dataframe:", df)

    df.to_csv(f"/scratch/project_2000527/pgnn/results/mlp_lr_{data_use}.csv")

if __name__ == '__main__':
    mlpft(args.d)
