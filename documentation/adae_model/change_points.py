# this script calculates the change points and arrival rates from ADAE traces

# Define global variables
TRACES = 'data/raw_data/zebra_transitions.csv' # path to the csv file containing ADAE traces
OUTPUTS = 'data/outputs/' # path to the directory to save the outputs
CP_THRESHOLDS = [0.8, 0.95, 0.99, 0.995] # thresholds for change points

# import libraries

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import matplotlib.patches as mpatches
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_percentage_error

# read in traces from dataset
# this dataset contains the timestamps when the behavior of a zebra changes

def getChangePoints(dataframe, threshold1):
    # calculate the gradient of the cumulative distribution
    sum = dataframe['time']
    sum = pd.DataFrame(sum)
    sum['counts'] = sum.groupby('time')['time'].transform('count')
    sum= sum.drop_duplicates()
    sum['gradient'] = np.gradient(sum['counts'])
    sum.head()

    # calculate the differences in the gradient
    sum['grad_diff'] = sum['gradient'].diff().abs()
    sum['grad_diff'] = sum['grad_diff'].fillna(0)

    sum['change_point'] = sum['grad_diff'].apply(lambda x: 1 if x > threshold1 else 0)

    change_points = sum[sum['change_point'] == 1]

    return change_points, dataframe

def plotChangePoints(change_points, df, name, outputs):
    # plot the cumulative distribution of transitions with the change points
    fig, ax = plt.subplots()

    ax.plot(df['time'], range(len(df['time'])))
    plt.xlabel
    plt.ylabel('Transitions')
    plt.title('Zebra Transitions')
    plt.ylim(0, len(df))
    plt.figure(figsize=(10, 5))

    for index, row in change_points.iterrows():
        ax.axvline(x=row['time'], color='g', linestyle=':')

    plt.show()
    plt.savefig(outputs + name + '.png')

def arrivalRate(df, start, end):
    return len(df[(df['time'] >= start) & (df['time'] < end)]) / (end - start)

def avgArrivalTimes(df, change_points):
    # calculate the arrival rate before and after each change point
    arrival_rates = {}
    for i in range(len(change_points)-1):
        start = change_points[i] # start of the trace
        end = change_points[i+1] # end of the trace
        
        arrival_rate = arrivalRate(df, start, end)
        
        arrival_rates[start] = arrival_rate
    return arrival_rates

def poisson_process_with_rate_variation(total_time, rates, change_points):
    
    arrival_times = []
    current_time = 0

    for i in range(len(change_points)-1):
        rate = rates[i]
        duration = change_points[i] - current_time

        # Generate arrivals based on Poisson process
        arrivals = np.random.poisson(rate * duration)
        arrival_times.extend(np.sort(np.random.uniform(current_time, current_time + duration, arrivals)))
        current_time = change_points[i]

    # Handle the last interval
    rate = rates[-1]
    duration = total_time - current_time
    arrivals = np.random.poisson(rate * duration)
    arrival_times.extend(np.sort(np.random.uniform(current_time, current_time + duration, arrivals)))

    return arrival_times

def plotArrivalTimes(arrival_times, df, name, outputs):
    plt.figure(figsize=(10, 5))
    plt.title('Bursty Request Arrival Times (Poisson Process with Rate Variation))')
    plt.xlabel('Time')
    plt.ylabel('Cumulative Request Arrivals')
    plt.plot(arrival_times, np.arange(len(arrival_times)), label='simulated trace')
    plt.plot(df['time'], range(len(df['time'])), label='real trace')
    plt.legend()
    plt.show()
    plt.savefig(outputs + name + '.png')

def joinArrivalTimes(arrival_times, real_trace, simulated_trace):

    # fill in missing time reconds with 0 for the counts
    time = pd.DataFrame(np.arange(0, max(arrival_times)), columns=['time'])
    time['time'] = time['time'].astype(int)
    time['counts'] = 0

    # get count of each time in the simulated trace
    simulated_trace = pd.DataFrame(arrival_times, columns=['time'])
    # round the time to the nearest second
    simulated_trace['time'] = simulated_trace['time'].round(0)
    simulated_trace['time'] = simulated_trace['time'].astype(int)

    simulated_trace['counts'] = simulated_trace.groupby('time')['time'].transform('count')
    simulated_trace=simulated_trace.drop_duplicates()

    # join time and simulated traces on time column
    merged = pd.merge(time, simulated_trace, on='time', how='left')
    merged.rename(columns={'counts_x': 'blank', 'counts_y': 'simulated'}, inplace=True)

    # get the real_traces
    real_trace = pd.DataFrame(df, columns=['time'])
    real_trace['counts'] = real_trace.groupby('time')['time'].transform('count')
    real_trace = real_trace.drop_duplicates()
    merged = pd.merge(merged, real_trace, on='time', how='left')
    merged.rename(columns={'counts': 'real'}, inplace=True)
    # fill in NaN with 0s
    merged['real'] = merged['real'].fillna(0)
    merged['simulated'] = merged['simulated'].fillna(0)

    merged = merged[['simulated', 'real']]

    return merged

def bucketValues(time_series, bucket):
    # sum the occurances of values from series into groups by bucket size
    return time_series.groupby(time_series.index // bucket).sum()

def bucketValuesByChangePoints(time_series, change_points):
    # sum the occurances of values from series into groups by change points
    return time_series.groupby(pd.cut(time_series.index, change_points)).sum()

def error_metrics(actual_values, predicted_values):

    # Calculate MAE
    mae = round(mean_absolute_error(actual_values, predicted_values), 6)

    # Calculate MSE
    mse = round(mean_squared_error(actual_values, predicted_values), 6)
   
    # Calculate MAPE
    mape = round(mean_absolute_percentage_error(actual_values, predicted_values), 6)
    
    return mae, mse, mape

def calculate_change_points():
    # get the change points from the dataset
    # read in traces from dataset
    # this dataset contains the timestamps when the behavior of a zebra changes
    df = pd.read_csv(TRACES)

    # clean up the data to get time in seconds 
    df['time'] = df['time'].str.replace('0 days ', '')
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S') 
    start = df['time'].min()
    df['time'] = df['time'].apply(lambda x: x - start)
    df['time'] = df['time'].dt.total_seconds()

    # sort the data by time
    df = df.sort_values(by='time')

    # location to save outputs
    outputs = OUTPUTS

    cp_results = pd.DataFrame(columns=['threshold', 'mae', 'mse', 'mape'])

    # get the change points from the dataset
    # Change Points

    for threshold in CP_THRESHOLDS:
        change_points, df = getChangePoints(df, threshold)

        # convert change points to list 
        cp = change_points['time'].tolist()
        cp.insert(0, 0)
        cp.append(df['time'].max())

        name = '/change_points_' + str(threshold)
        #plotChangePoints(change_points, df, name, outputs)

        # calculate the arrival rates and simulate the arrival times
        arrival_rates = avgArrivalTimes(df, cp)

        # simulate the arrival times
        rates = list(arrival_rates.values())
        change_points = list(arrival_rates.keys())
        arrival_times = poisson_process_with_rate_variation(df['time'].max(), rates, change_points)

        # plot the arrival times
        name = '/arrival_times_' + str(threshold)
        plotArrivalTimes(arrival_times, df, name, outputs)

        # bucket the simulated and real arrival times into 1 second intervals 
        merged = joinArrivalTimes(df, arrival_times)
        # save to csv
        name = '/real_and_simulated_arrival_times_' + str(threshold)
        merged.to_csv(outputs + name + '.csv', index=False)
        # save change points to csv
        name = '/change_points_' + str(threshold)
        # convert cp to dataframe
        # change_points = pd.DataFrame(change_points)
        # change_points.to_csv(outputs + name + '.csv', index=False)

        # save arrival rates to csv
        arrival_rates = pd.DataFrame(arrival_rates.items(), columns=['change_point', 'arrival_rate'])
        arrival_rates.to_csv(outputs + name + '_arrival_rates.csv', index=False)

        # calculate the error rates between real and simulated values
        data = merged.drop(index=0) # drop start of behaviors, not a true transition
        actual_values = data['real']
        predicted_values = data['simulated']

        mae, mse, mape = error_metrics(actual_values, predicted_values)

        # add to results dataframe
        # cp_results = cp_results.append({'threshold': threshold, 'mae': mae, 'mse': mse, 'mape': mape}, ignore_index=True)
        cp_results.loc[len(cp_results.index)] = {'threshold': threshold, 'mae': mae, 'mse': mse, 'mape': mape}
        # write to csv
        cp_results.to_csv(outputs + '/change_point_results.csv', index=False)


def main ():
    calculate_change_points()

if __name__ == "__main__":
    main()