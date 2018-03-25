# -*- coding: utf-8 -*-
"""
This script:
    - get row,path,date form landsat files
    - rename folder to Landsat Path Row
    - delete duplicate file from different collection(keep newer collection)
    - count temporal distribution of the data

reference:
    https://landsat.usgs.gov/what-are-naming-conventions-landsat-scene-identifiers


@author: Mao
"""
import glob
import re
import datetime
import pandas as pd
import numpy as np
import os


def matchingfile(name):
    pattern = re.compile(r'L\w\d(?P<path>\d{3})(?P<row>\d{3})(?P<yr>\d{4})(?P<day>\d{3})\D*')
    match = pattern.match(name)
    matchres = match.groupdict()
    path = int(matchres['path'])
    row = int(matchres['row'])
    yr = int(matchres['yr'])
    day = int(matchres['day'])
    date = datetime.datetime(yr, 1, 1) + datetime.timedelta(day-1) #first day is 1
    month = date.month
    dy = date.day
    return [path,row,yr,month,dy]

def addnewrow(df,data):
    t = pd.DataFrame(data).T
    t.columns = df.columns
    df = pd.concat([df,t],ignore_index=True)
    return df

def num2str(num,digit):
    numdigit = len(str(num))  
    if digit<numdigit:
        return None
    else:
        return str(0)*(digit-numdigit)+str(num)

"""
    for each folder:
        move duplicated file(from old version of landsat) to folder'dup'
        get file attr
        add file attr to df
"""
path = r'C:\Users\dell\Desktop\Data'
mfiles = glob.glob(path+r'\LA20180326211651276\*')
for mfile in mfiles:
    mname = os.path.basename(mfile)
    p,r = matchingfile(mname)[0:2]
    mvfolder = 'P'+num2str(p,3)+'R'+num2str(r,3)
    os.rename(mfile,os.path.join(path,mvfolder,mname))

df = pd.DataFrame(columns=['path','row','yr','mon','dy'])
folders = os.listdir(path)
for folder in folders:
    if os.path.isdir(folder) and folder != 'dup':
        fpath = os.path.join(path,folder,'L*')
        ffiles = glob.glob(fpath)
        ffilelist = list(map(os.path.basename,ffiles))
        ffilemain = [x[0:16] for x in ffilelist]
        ffilemaindf = pd.Series(ffilemain)
        dup = ffilemaindf.duplicated(keep = 'last')
        dupix = dup[dup==True].index
        for ix in dupix:           
            dupfile = ffilelist[ix]
            newpath = os.path.join(path,'dup',dupfile)
            os.rename(ffiles[ix],newpath)
        fpath = os.path.join(path,folder,'L*')
        ffiles = glob.glob(fpath)
        for ffile in ffiles:
            df = addnewrow(df,matchingfile(os.path.basename(ffile)))
        newfoldername = 'P'+num2str(matchingfile(os.path.basename(ffile))[0],3)+'R'+num2str(matchingfile(os.path.basename(ffile))[1],3)
        os.rename(os.path.join(path,folder),os.path.join(path,newfoldername))

#count attrs
def prslice(df,p,r):
    return df[(df['path'] == p) & (df['row'] == r)]

def countattr(dfslice):
    countlist = np.zeros((3,4),dtype = 'int')
    for i in range(3):
        styr = 2000+i*6
        endyr = 2006+i*6
        for j in range(4):
            stmon = 1 + j*3
            endmon = 4 + j*3
            res = len(dfslice[(dfslice['yr'] >= styr) & (dfslice['yr'] < endyr) & (dfslice['mon'] >= stmon) & (dfslice['mon'] <endmon)])
            countlist[i][j] = res
    return countlist.flatten()

gp=df.groupby(by=['path','row'])
newdf = gp.size()
count = np.zeros((len(newdf.index),12),dtype = 'int')  
for i in range(len(newdf.index)):
    p,r = newdf.index[i]
    dfslice = prslice(df,p,r)
    count[i] = countattr(dfslice)

yrinter = ['I','II','III']
season = range(1,5,1)
col = []
for y in yrinter:
    for s in season:
        X = y+str(s)
        col.append(X)
##['I1', 'I2', 'I3', 'I4', 'II1', 'II2', 'II3', 'II4', 'III1', 'III2', 'III3', 'III4']
countdf =pd.DataFrame(count,columns = col)
countdf.to_csv('countdf.csv')