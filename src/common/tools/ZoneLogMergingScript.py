# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:47:18 2019

@author: marvo
"""



from os import listdir
from os.path import isfile, join
import pandas as pd


finalDataframe = None;
initialised = False

mypath = "D:\Development\Movement-Python\movementLogs\placeablesInZone"
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]



for filename in onlyfiles:
    pathname = mypath + "\\" + filename
    name = filename.split('.')[0] 

    data = pd.read_csv(pathname, header=None)
    
    if (initialised == False):
        finalDataframe = data
        initialised = True
        New_Labels=['datatime', name]
        finalDataframe.columns = New_Labels
    else:
        stlpec = data.iloc[:,1]
        stlpec = stlpec.rename(name)
        finalDataframe = pd.concat([finalDataframe, stlpec], axis=1)
        
        
        
export_csv =finalDataframe.to_csv(mypath+ '\mergedzoneLog.csv', index = None, header=True) #Don't forget to add '.csv' at the end of the path