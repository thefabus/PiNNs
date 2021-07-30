# !/usr/bin/env python
# coding: utf-8
import torch
import numpy as np
import pandas as pd
import torch.nn as nn
import torch.optim as optim
from sklearn import metrics
from sklearn.model_selection import train_test_split
import utils
import random
import models
import os
from torch.utils.data import TensorDataset, DataLoader
from torch import Tensor
import csv


def train(hpar, model_design, X, Y, Xn, data_dir='./', mean=None, std=None, pt=None, pre=None):
    # initialize data
    # hyperparameters
    n_epoch = hpar['epochs']
    batchsize = hpar['batchsize']
    lr = hpar['learningrate']
    layersizes = model_design['layer_sizes']    
    # shuffle data
    #x_train, x_test, y_train, y_test = train_test_split(X, Y)
    x_train, y_train = X, Y
    xn_train = Xn
    pre_train = pre
    train_set = TensorDataset(torch.tensor(x_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32), torch.tensor(xn_train, dtype=torch.float32), torch.tensor(pre_train, dtype=torch.float32))
    #test_set = TensorDataset(Tensor(x_test), Tensor(y_test))
    model = models.EMB(X.shape[1], Y.shape[1], layersizes, 27, 1)
    #if pt:
    #    state = model.state_dict()
    #    md = torch.load("modEMBNAS.pth")
    #    pk = [m for m in md.keys() if m.startswith("parnet")]
    #    parnetdict = {key: value for key, value in md.items() if key in pk}
    #    state.update(parnetdict)
    #    model.load_state_dict(state)
    #optimizer = optim.Adam([{"params": model.parnet.parameters(), "lr": 2e-3},
    #{"params": model.resnet.parameters()}], lr = lr)#, weight_decay=0.03)
    #model = models.NMLP(Y.shape[1], Y.shape[1], [8,8])
    optimizer = optim.Adam(model.parameters(), lr)
    criterion = nn.MSELoss()
    
    #test_loader = torch.utils.data.DataLoader(test_set, batch_size=len(test_set))
    #test_loader = torch.utils.data.DataLoader(test_set, batch_size=len(test_set))
    train_set_size = len(train_set)
    sample_id = list(range(train_set_size))
    train_sampler = torch.utils.data.sampler.SequentialSampler(sample_id[:int(train_set_size // 100 * 80)])
    val_sampler = torch.utils.data.sampler.SequentialSampler(sample_id[int(train_set_size // 100 * 80):])
    #train_data = train_set[:int(train_set_size // 100 * 80),...]
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=batchsize, sampler = train_sampler, shuffle=False)
    #scheduler = optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.0001)
    #val_data = train_set[int(train_set_size // 100 * 80):,...]
    val_loader = torch.utils.data.DataLoader(train_set, batch_size=batchsize, sampler=val_sampler, shuffle=False)
    train_loss = []
    val_loss = []
    #nbatches = (train_set_size//100*80)/batchsize
    #print(val_loader[0:2])
    epoch_loss = []
    for i in range(n_epoch):
        model.train()
        batch_diff = []
        batch_loss = []
        for step, train_data in enumerate(train_loader):
            xt = train_data[0]
            yt = train_data[1]
            xnt = train_data[2]
            pt = (train_data[3]-mean['GPP'])/std['GPP']
            #print('OBSERVED', pt)
            P = torch.tensor([[413.0/400,
                               0.450, 0.118, 3., 0.748464, 12.74915/12,
                               -3.566967/10, 18.4513/10, -0.136732,
                               0.033942, 0.448975, 0.500, -0.364,
                               0.33271/10, 0.857291, 0.041781,
                               0.474173, 0.278332/5, 1.5, 0.33,
                               4.824704/4, 0., 0., 180./180,
                               0., 0., 10./10
                               ]]*len(xt))
            #P = torch.tensor([[0.450, 0.118, 0.748464, 12.74915/12, -3.566967/10, 18.4513/10, -0.136732, 0.033942, 0.448975, 0.33271/10]]*len(xt))
            # zero parameter gradients
            optimizer.zero_grad()

            # forward
            y_hat = model(pt.unsqueeze(-1), xnt, mean, std)
            #p = model(xt, xnt)
            #print('y_target', yt)
            loss = criterion(y_hat, yt) #+ 0.5*criterion(p, pt.unsqueeze(-1))
            #loss = criterion(p, pt.unsqueeze(-1))
            print('loss', loss)
            # backward
            loss.backward()
            optimizer.step()
            #scheduler.step()
            batch_loss.append(loss.item())
        
        # results per epoch
        train_loss.append((sum(batch_loss)/len(batch_loss)))
        #train_loss.append(batch_loss)
        print('train_loss', train_loss)

        # test model
        model.eval()

        e_bl = []
        # deactivate autograd
        with torch.no_grad():
            for step, val_sample in enumerate(val_loader):
                x_val = val_sample[0]
                y_val = val_sample[1]
                xn_val = val_sample[2]
                pval = (val_sample[3]-mean['GPP'])/std['GPP']
                
                #Pv = torch.tensor([[413.0/400,
                #                   0.450, 0.118, 3., 0.748464, 12.74915/12,
                #                   -3.566967/10, 18.4513/10, -0.136732,
                #                   0.033942, 0.448975, 0.500, -0.364,
                #                   0.33271/10, 0.857291, 0.041781,
                #                   0.474173, 0.278332/5, 1.5, 0.33,
                #                   4.824704/4, 0., 0., 180./180,
                #                   0., 0., 10./10
                #                   ]]*len(x_val))
                #Pv = torch.tensor([[0.450, 0.118, 0.748464, 12.74915/12, -3.566967/10, 18.4513/10, -0.136732, 0.033942, 0.448975, 0.33271/10]]*len(xn_val))
                #pv = model(x_val, xn_val)
                y_hat_val = model(pval.unsqueeze(-1), xn_val, mean, std)
                loss = criterion(y_hat_val, y_val) #+ criterion(pv, pval.unsqueeze(-1))
                #loss = criterion(pv, pval.unsqueeze(-1))
                print("eval_loss", loss)
                #print("Parameters:", pv, pval)
                e_bl.append(loss.item())

        val_loss.append(sum(e_bl) / len(e_bl))
        #val_loss.append(e_bl)
    torch.save(model.state_dict(), os.path.join(data_dir, "model.pth"))
    

        
    return {'train_loss': train_loss, 'val_loss': val_loss}







