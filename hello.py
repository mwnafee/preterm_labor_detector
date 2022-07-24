from attr import define
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import serial
import keyboard as kb
import time
import math
from scipy.signal import savgol_filter
# Data Collection:

fileName='analog-data.csv'
plt.ion()
fig = plt.figure()


i=0
x=list()
y=list()
ser  = serial.Serial('COM6', 9600, timeout = 1)

if(ser.isOpen() == False):
    ser.open()
else:
    ser.close()
    ser.open()

file= open(fileName,"w")
print("Created file")



while True:
    if kb.is_pressed("a"):
        print("close")
        break
    ser.write(bytes('x','utf-8'))
    time.sleep(0.5)
    data = ser.readline()
    data=data[0:][:-2]
    print(data.decode())
    
    data1=data.decode()
    data1=str(data1)
    file= open(fileName,"a")
    file.write(data1 + "\n")

    z=data1.split(',')
    arr=np.array(z)
    arr=arr.astype(np.float64)
    times=arr[0]
    value=arr[1]

    x.append(times)
    y.append(value)

    plt.scatter(times, value)
    
    plt.show()
    plt.pause(0.01)
    

print("The times are:")
for i in x:
    print(i)
print("The voltage values are:")
for j in y:
    
    print(j)  

#Data PreProcessing:
freq=20 # 20Hz sampling frequency
minutes=30
slice_time= minutes*60 # 30 minutes
slice_size= slice_time*freq

sample_size=len(x)
slice_num=math.floor(sample_size/slice_size)
x_sliced= [x[i*slice_size:(i+1)*slice_size] for i in range(0,slice_num)]
y_sliced= [y[i*slice_size:(i+1)*slice_size] for i in range(0,slice_num)]

x_sliced=np.array(x_sliced)
y_sliced=np.array(y_sliced)  #now time and voltage has been successfully divided into segments of 30 mins or 36,000 samples

def findPeakIndex(y):
    c=np.where(y==max(y))

    return c[0][0]

def percDiff(val1,val2):
    valM=abs(val1-val2)
    valP=abs(val1+val2)/2
    perDiff=(valM/ValP)*100
    return perDiff


# Data Analysis:
final_Decision=list()
Threshold=50
for i in range(0,len(x_sliced)):
    FD=0
    PFC=0
    fPFC=0
    PRPD=0
    peaksFD=0
    freqFD=0
    t=x_sliced[i,:]
    volt_raw=y_sliced[i,:]
    volt=savgol_filter(volt_raw,25,2)
    # phase-1
    sd_threshold=0.1
    sd=np.std(volt)
    if sd<sd_threshold:
        FD=0;
    else:
        #phase-2
        percent=5
        segments=100/percent
        segment_size= (percent/100)*len(t)
        t05=[t[p*segment_size:(p+1)*segment_size] for p in range(0,segments)]
        volt05=[volt[p*segment_size:(p+1)*segment_size] for p in range(0,segments)]
        for j in range(0,len(t05)):
            tp=t05[j,:]
            voltp=volt05[j,:]

            chunk_size=100
            chunk_num=math.floor(len(t)/chunk_size)  
            t_chunked=[tp[p*chunk_size:(p+1)*chunk_size] for p in range(0,chunk_num)]
            volt_chunked=[voltp[p*chunk_size:(p+1)*chunk_size] for p in range(0,chunk_num)]
            #Peaks Analysis
            for k in range(0,len(volt_chunked)-1):
                ind1=findPeakIndex(volt_chunked[k,:])
                ind2=findPeakIndex(volt_chunked[k+1,:])
                peak1=volt_chunked[k,:][ind1]
                peak2=volt_chunked[k+1,:][ind2]
                PDR=percDiff(peak1,peak2)
                if PDR>14:
                    PFC+=1
            PRPD=(PFC*100)/len(volt_chunked) 
            if PRPD>25:
                peaksFD+=5
            
            #Frequency Analysis
            for k in range(0,len(volt_chunked)-2):
                ind1=findPeakIndex(volt_chunked[k,:])
                ind2=findPeakIndex(volt_chunked[k+1,:])
                ind3=findPeakIndex(volt_chunked[k+2,:])
                time1=t_chunked[k,:][ind1]
                time2=t_chunked[k+1,:][ind2]
                time3=t_chunked[k+2,:][ind3]
                freq1=time2-time1
                freq2=time3-time2
                fPDR=percDiff(freq1,freq2)
                if fPDR>14:
                    fPFC+=1
            fPRPD=(fPFC*100)/len(volt_chunked) 
            if fPRPD>25:
                freqFD+=5
    
    #Final Decision Analysis
    FD=(peaksFD+freqFD)/2
    if FD>=Threshold:
        final_Decision.append(1)
    else:
        final_Decision.append(0)

print("Done")