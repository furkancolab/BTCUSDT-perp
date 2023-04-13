#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#


# Import
import sys
import os
import numpy as np
import pandas as pd

# Data READ class
class READ:
  def __init__(self,name):
    self.name = name

  def check_data_format(self):
    # Read data set - It must be excel file with Column A showing dates, and Column B showing Prices.
    try: 
      dataframe = pd.ExcelFile(self.name)
    except:
      print ("Something went wrong when opening the file. Expected input is an Excel file.")
    try:
      daily = pd.read_excel(dataframe, usecols="A:B")
      daily['Date'] = pd.to_datetime(daily['Date'])
      daily.sort_values('Date')
    except:
      print ("Something went wrong when reading the columns. Expected format has 2 columns named 'Date' and 'Price'")
    
    return daily

# EDA class
class EDA:
  def __init__(self,data):
    self.data = data

  def data_sourcing(self):
    zeros = np.argwhere(self.data == 0)
    nans = np.argwhere(np.isnan(self.data))
    return [zeros, nans]

  def data_cleaning(self,interpolate=False):
    zeros, nans = self.data_sourcing()
    if (interpolate):
      pass
    else:
      remove = np.unique(np.concatenate([zeros[:,0], nans[:,0]]))
      return np.delete(self.data, remove, axis=0) , remove

  def manipulation_analysis(self,frequency=1,nMax=20):
    data, remove = self.data_cleaning()
    diff_usd = [t - s for s, t in zip(data[::frequency], data[frequency::frequency])]
    diff_per = [(t - s)/s*100 for s, t in zip(data[::frequency], data[frequency::frequency])]
    sort_diff_usd = np.sort(diff_usd)
    sort_diff_per = np.sort(diff_per)
    abs_diff_usd = np.sort(np.absolute(diff_usd))
    abs_diff_per = np.sort(np.absolute(diff_per))
    upper = np.mean(abs_diff_per[-nMax:]) + np.std(abs_diff_per[-nMax:])
    lower = np.mean(abs_diff_per[-nMax:]) - np.std(abs_diff_per[-nMax:])
    conf_levels=[]
    for diff in diff_per:
      if (diff <= lower):
        conf_levels.append(100)
      elif (diff >= upper):
        conf_levels.append(0)
      else:
        conf_levels.append(100 - (diff-lower)/(upper-lower)*100)
    conf_levels = np.array(conf_levels)
    return lower, upper, conf_levels

def main():
  import argparse
  parser = argparse.ArgumentParser(description="""\
Manipulation limits calculator
""")
  parser.add_argument("--version", action="version", version='%(prog)s 0.0.1')
  parser.add_argument("-o", "--output", metavar="output-file", default="output", help="output file")
  parser.add_argument("-l", "--little", action="store_true", help="little endian")
  parser.add_argument("-n", "--n_max", type=int, default=20, help="Number of maximum values to be averaged")
  parser.add_argument("-s", "--stride", type=int, default=1, help="Time stride")
  parser.add_argument("-m", "--min_confidence", type=float, default=50, help="minimum market confidence level")
  parser.add_argument("file", metavar="input-file", help="input file")
  options = parser.parse_args()
  ## options, args = parser.parse_known_args()
  ## options.config = args
  
  # Initial Read
  if(not os.path.isfile(options.file)):
    raise Exception("The input file does not exist.")
  global end
  end = ">"
  if(options.little): end = "<"

  # Read data file
  print ("Reading data: ")
  df = READ(options.file)
  data = df.check_data_format()
  print (data.head)

  # Manipulation analysis
  print ("Calculating manipulation limits: ")
  arr = data.iloc[:,1].to_numpy()
  eda = EDA(arr)
  mani = eda.manipulation_analysis(options.stride,options.n_max)
  print ("Lower limit: %r and Upper limit: %r" % (mani[0], mani[1]))

  # Remove 0s and Nans from data
  dummy, remove = eda.data_cleaning()
  data.drop(remove)

  # Check the confidence levels
  print ("Printing when the market confidence level is lower than certain percentage.")
  inds = np.argwhere(mani[2] < options.min_confidence)
  for i in inds:
    ind = i+1
    print ("At ", data.iloc[ind,0].to_string(), " the market confidence level is ", mani[2][i], " and lower than given limit ", options.min_confidence)

if(__name__ == '__main__'):
  main()
