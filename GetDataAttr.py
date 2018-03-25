# -*- coding: utf-8 -*-
"""
This script:
    - get row,path,date form landsat files

reference:
    https://landsat.usgs.gov/what-are-naming-conventions-landsat-scene-identifiers


@author: Mao
"""
import glob
import re
import datetime
import pandas as pd

files = glob.glob('LT5*')

def matchingfile(name):
    pattern = re.compile(r'LT\d(?P<path>\d{3})(?P<row>\d{3})(?P<yr>\d{4})(?P<day>\d{3})\D*')
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

df = pd.DataFrame(columns=['path','row','yr','mon','dy'])

def addnewrow(df,data):
    t = pd.DataFrame(data).T
    t.columns = df.columns
    df = pd.concat([df,t],ignore_index=True)
    return df

for file in files:
    df = addnewrow(df,matchingfile(file))
