# !/usr/bin/env python
# coding: utf-8
import torch
import pandas as pd
import numpy as np
import utils
import models
import torch.nn as nn
import torch.optim as optim
from sklearn import metrics
from sklearn.model_selection import train_test_split
import random
import os
from torch.utils.data import TensorDataset, DataLoader
from torch import Tensor
import csv
import training
import argparse

parser = argparse.ArgumentParser(description='Define data usage and splits')
parser.add_argument('-d', metavar='data', type=str, help='define data usage: full vs sparse')
parser.add_argument('-m', metavar='model', type=str, help='define model: mlp, res, res2, reg, emb, da')
args = parser.parse_args()

def predict(test_x, test_y, m, data_use, yp=None):
    # Architecture
    res_as = pd.read_csv(f"./HPresults/N{m}AS_{data_use}.csv")
    a = res_as.loc[res_as.ind_mini.idxmin()][1:5]
    b = a.to_numpy()
    layersizes = list(b[np.isfinite(b)].astype(int))

    model_design = {'layersizes': layersizes}
    data_dir = "./data/"
    mse = nn.MSELoss()
    mae = nn.L1Loss()
    if m == 'res2':
        yp_test = torch.tensor(yp.to_numpy(), dtype=torch.float32)
    x_test, y_test = torch.tensor(test_x.to_numpy(), dtype=torch.float32), torch.tensor(test_y.to_numpy(), dtype=torch.float32)

    test_rmse = []
    test_mae = []

    preds_test = np.zeros((x_test.shape[0], 4))

    for i in range(4):
        i += 1
        #import model
        if m in ['mlp', 'res', 'reg']:
            model = models.NMLP(x_test.shape[1], 1, model_design['layersizes'])
        elif m == 'res2':
            model = models.RES(x_test.shape[1], 1, model_design['layersizes'])
        

        model.load_state_dict(torch.load(''.join((data_dir, f"{m}_{data_use}_model{i}.pth"))))
        model.eval()
        with torch.no_grad():
            if m == 'res2':
                p_test = model(x_test, yp_test)
            else:
                p_test = model(x_test)
            #preds_test.update({f'test_{m}{i}': p_test.flatten().numpy()})
            preds_test[:,i-1] = p_test.flatten().numpy()

    preds_test = np.mean(preds_test, axis=1)

    return preds_test




def via(data_use, model, yp=None):

    if data_use == 'sparse':
        x, y, xt, mn, std = utils.loaddata('validation', 1, dir="./data/", raw=True, sparse=True, via=True)
        if model in ['res', 'res2']:
            yp_tr = utils.make_sparse(pd.read_csv("./data/train_hyt.csv"))
            yp_te = utils.make_sparse(pd.read_csv("./data/test_hyt.csv")[6:])
    else:
        x, y, xt, mn, std = utils.loaddata('validation', 1, dir="./data/", raw=True, via=True)
        if model in ['res', 'res2']:
            yp_tr = pd.read_csv("./data/train_hyt.csv")
            yp_te = pd.read_csv("./data/test_hyt.csv")


    thresholds = {'PAR': [0, 200], 
                  'Tair': [-20, 40],
                  'VPD': [0, 60],
                  'Precip': [0, 100],
                  #'co2': [],
                  'fapar': [0, 1],
                  'GPPp': [0, 30],
                  'ETp': [0, 800],
                  'SWp': [0, 400]
    }

    gridsize = 200
    
    if model == 'res2':
        yp_te.index = pd.DatetimeIndex(yp_te['date'])
        ypte = yp_te.drop(yp_te.columns.difference(['GPPp']), axis=1)
        yp = ypte
    if model == 'res':
        yp_tr.index = pd.DatetimeIndex(yp_tr['date'])
        yp_te.index = pd.DatetimeIndex(yp_te['date'])
        yptr = yp_tr.drop(yp_tr.columns.difference(['GPPp', 'ETp', 'SWp']), axis=1)
        ypte = yp_te.drop(yp_te.columns.difference(['GPPp', 'ETp', 'SWp']), axis=1)
        n = [1,1]
        x_tr, n = utils.add_history(yptr, n, 1)
        x_te, n = utils.add_history(ypte, n, 1)
        x_tr, mn, std = utils.standardize(x_tr, get_p=True)
        x_te = utils.standardize(x_te, [mn, std])
        test_x = x_te[x_te.index.year == 2008]
        test_y = y[y.index.year == 2008][1:]
        variables = ['GPPp', 'ETp', 'SWp']
                
    elif model in ['mlp', 'res2', 'reg']:
        test_x = x[x.index.year == 2008][1:]
        test_y = y[y.index.year == 2008][1:]
        variables = ['PAR', 'Tair', 'VPD', 'Precip', 'fapar']

    for v in variables:
        if model == 'res':
            var_range = (np.linspace(thresholds[v][0], thresholds[v][1], gridsize)-mn[''.join((v, '_x'))])/std[''.join((v, '_x'))]
        else:
            var_range = (np.linspace(thresholds[v][0], thresholds[v][1], gridsize)-mn[v])/std[v]
        output = {'mar':None, 'jun':None, 'sep':None, 'dec':None}

        dat = test_x.copy()
        if not yp is None:
            yp_dat = yp.copy()

        # Compute effect of variable at mean of 14 days around record dates for seasonal changes
        #mar = pd.concat([dat['2008-03-13':'2008-03-27'].mean().to_frame().T] * gridsize)
        #jun = pd.concat([dat['2008-06-14':'2008-06-28'].mean().to_frame().T] * gridsize)
        #sep = pd.concat([dat['2008-09-13':'2008-09-28'].mean().to_frame().T] * gridsize)
        #dec = pd.concat([dat['2008-12-14':'2008-12-28'].mean().to_frame().T] * gridsize)
        #days = {'mar':mar, 'jun':jun, 'sep':sep, 'dec':dec}

        mar = dat['2008-03-13':'2008-03-27']
        jun = dat['2008-06-14':'2008-06-28']
        sep = dat['2008-09-13':'2008-09-28']
        dec = dat['2008-12-14':'2008-12-28']
        days = {'mar':mar, 'jun':jun, 'sep':sep, 'dec':dec}

        if not yp is None:
            #yp_mar = pd.concat([yp_dat['2008-03-13':'2008-03-27'].mean().to_frame().T] * gridsize)
            #yp_jun = pd.concat([yp_dat['2008-06-14':'2008-06-28'].mean().to_frame().T] * gridsize)
            #yp_sep = pd.concat([yp_dat['2008-09-13':'2008-09-28'].mean().to_frame().T] * gridsize)
            #yp_dec = pd.concat([yp_dat['2008-12-14':'2008-12-28'].mean().to_frame().T] * gridsize)
            #days_yp = {'mar':yp_mar, 'jun':yp_jun, 'sep':yp_sep, 'dec':yp_dec}

            yp_mar = yp_dat['2008-03-13':'2008-03-27']
            yp_jun = yp_dat['2008-06-14':'2008-06-28']
            yp_sep = yp_dat['2008-09-13':'2008-09-28']
            yp_dec = yp_dat['2008-12-14':'2008-12-28']
            days_yp = {'mar':yp_mar, 'jun':yp_jun, 'sep':yp_sep, 'dec':yp_dec}

        for mon, df in days.items():
            out_i = []
            for i in var_range:
                df[''.join((v, '_x'))] = i
                df[''.join((v, '_y'))] = i
                #test_x.index, test_y.index = np.arange(0, len(test_x)), np.arange(0, len(test_y))

                if not yp is None:
                    ps = predict(df, test_y, model, data_use, days_yp[mon])
                else:
                    ps = predict(df, test_y, model, data_use, yp)

                out_i.append(ps)

            pd.DataFrame(out_i).to_csv(f'./results/{model}_{data_use}_{v}_via_cond_{mon}.csv')
            # pd.DataFrame.from_dict(ps).apply(lambda row: np.mean(row.to_numpy()), axis=1)


if __name__ == '__main__':
    #via('full', 'mlp')
    #via('sparse', 'mlp')
    via('full', 'res2')
    #via('sparse', 'res2')
