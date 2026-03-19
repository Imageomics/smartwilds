# This script extracts arrival times of camera trap images from the Orinoquia dataset

# import libraries
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

# read in camera trap data from json file
# data source: https://lila.science/datasets/orinoquia-camera-traps/
with open('data/raw_data/orinoquia_camera_traps.json') as f:
    data = json.load(f)

# create a dataframe of locations and datetimes
camera_trap = pd.DataFrame(data['images'])

# convert the datetime column to a datetime object
camera_trap['datetime'] = pd.to_datetime(camera_trap['datetime'])

# convert the location column to a string
camera_trap['location'] = camera_trap['location'].astype(str)

# create a new column for the date
camera_trap['date'] = camera_trap['datetime'].dt.date

# get create column of time
camera_trap['time'] = camera_trap['datetime'].dt.time

# extract arrival times from day 1 of the study
day_1 = camera_trap[camera_trap['date'] == camera_trap['date'].unique()[0]]

# sort the data by datetime
day_1 = day_1.sort_values('datetime')         

# write to csv file
day_1.to_csv('data/cleaned_data/camera_trap.csv', index=False)