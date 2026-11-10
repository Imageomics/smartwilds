# This script extracts behavior transitions from KABR dataset

# import libraries
import pandas as pd
import numpy as np


# read in data from csv file
df = pd.read_csv('data/raw_data/zebra_transitions.csv')

# clean up the data to get time in seconds 
df['time'] = df['time'].str.replace('0 days ', '')
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S') 
start = df['time'].min()
df['time'] = df['time'].apply(lambda x: x - start)
df['time'] = df['time'].dt.total_seconds()

# sort the data by time
df = df.sort_values(by='time')

# export the data to a csv file
df.to_csv('zebra_transitions_cleaned.csv', index=False)