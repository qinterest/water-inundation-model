# -*- coding: utf-8 -*-
"""
This script:
    - move selected file to Interpretion folder
    - Unzip the file and delete the zipped one
    - Make data list
    
@author: mao
"""
import pandas as pd
import os
import glob
import numpy as np
import re
import datetime
import tarfile
import shutil

datadf = pd.DataFrame(index=['P121R044','P121R045','P122R043','P122R044','P122R045','P123R043','P123R045','P124R044'],columns=['1nf','1f','2nf','2f','3nf','3f'])
datadf[:] = 0

def un_tar(file_name):
    tar = tarfile.open(file_name)
    names = tar.getnames()
    tarpath = os.path.dirname(file_name)
    tarname = os.path.basename(file_name).strip('.tar.gz')
    zippath = os.path.join(tarpath,tarname)
    os.mkdir(zippath)  
    for name in names:  
        tar.extract(name, zippath)  
    tar.close() 
    return zippath

def num2str(num,digit):
    numdigit = len(str(num))  
    if digit<numdigit:
        return None
    else:
        return str(0)*(digit-numdigit)+str(num)

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

def getcol(yr,mon):
    if mon >= 4 and mon <=9:
        s = 'f'
    else:
        s = 'nf'
    if yr < 2006:
        p = '1'
    elif yr < 2012:
        p = '2'
    else:
        p = '3'
    return p+s

path = r'C:\Users\dell\Desktop\Data'
folders = os.listdir(path)
count = np.zeros((6,),dtype = 'int')
for folder in folders:
    if os.path.isdir(folder) and folder != 'dup' and folder != 'Interpretation':        
        fpath = os.path.join(path,folder,'L*')
        ffiles = glob.glob(fpath)
        for ffile in ffiles:
            name = os.path.basename(ffile)
            [p,r,yr,mon,dy] = matchingfile(name)
            idx = 'P'+num2str(p,3)+'R'+num2str(r,3)
            col = getcol(yr,mon)
            colcount = datadf.at[idx,col]
            if colcount < 3:                
                datadf.at[idx,col] += 1
                zippath = un_tar(ffile)
                duppath = os.path.join(path,'Interpretation',folder,os.path.basename(zippath))
                shutil.copytree(zippath, duppath)
                shutil.rmtree(zippath) 
                print(zippath+' done!')
                
datadf.to_csv('datadf.csv')

