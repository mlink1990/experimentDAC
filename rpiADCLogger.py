# -*- coding: utf-8 -*-
"""
Created on Tue Sep 09 15:24:12 2014

@author: HUMPHRY
"""

import time
import csv
import os
import labAlerts
import rpiADCClient

LOG_FREQUENCY_SECONDS = 60.0 # default log of once a minute

currentLocalTime = time.localtime()
currentYear = currentLocalTime.tm_year
currentMonth = currentLocalTime.tm_mon

rpiADCLogFolder = os.path.join("/media","ursa","AQOGroupFolder", "Experiment Humphry", "HardwareLogs","rpiADCLog")
rpiLogFileName = "rpiADCLog"+time.strftime("-%Y-%m", currentLocalTime)+".csv"
LOG_FILE_NAME = LOG_FILE_NAME = os.path.join(rpiADCLogFolder,rpiLogFileName)

#write column headers if it is a new log file

if not os.path.exists(LOG_FILE_NAME):
    with open(LOG_FILE_NAME, 'a+' ) as csvFile:
        csvWriter = csv.writer(csvFile)  
        csvWriter.writerow(["epochSeconds", "Channel 1","Channel 2", "Channel 3", "Channel 4", "Channel 5", "Channel 6", "Channel 7", "Channel 8" ])

#open connection to wave meter
rpiADCConnection = rpiADCClient.Connection()
logChannels = [0,1,2,3,4,5,6,7]
rpiADCConnection.connect()

def _voltage_get(channels, voltagesDictionary):
    """returns list of voltages corresponding to channels. missing values replaced with -999 
    voltageDictionary is latest results (channelNumber--> voltage)"""
    voltages =[]
    for channelNumber in channels:
        if channelNumber in voltagesDictionary.keys():
            voltages.append(voltagesDictionary[channelNumber])
        else:
            voltages.append(-999)
    return voltages
try:
    while(1):
        try:
            currentLocalTime = time.localtime()            
            
            epochSecs = time.time()
            latestResults = rpiADCConnection.getResults()
            voltages = _voltage_get(logChannels,latestResults)
            with open(LOG_FILE_NAME, 'a+' ) as csvFile:
                print "writing"
                print [epochSecs]+voltages
                csvWriter = csv.writer(csvFile)  
                csvWriter.writerow([epochSecs]+voltages)
            if currentLocalTime.tm_mon != currentMonth:
                #the month has changed we should start a new log file!
                rpiLogFileName = "rpiADCLog"+time.strftime("-%Y-%m", currentLocalTime)+".csv"
                LOG_FILE_NAME = os.path.join(rpiADCLogFolder,rpiLogFileName)
                if not os.path.exists(LOG_FILE_NAME):
                    with open(LOG_FILE_NAME, 'a+' ) as csvFile:
                        csvWriter = csv.writer(csvFile)  
                        csvWriter.writerow(["epochSeconds", "Channel 1","Channel 2", "Channel 3", "Channel 4", "Channel 5", "Channel 6", "Channel 7", "Channel 8" ])
            currentYear = currentLocalTime.tm_year
            currentMonth = currentLocalTime.tm_mon
            time.sleep( LOG_FREQUENCY_SECONDS )
        except Exception as e:
            print e.message
            message = e.message
            labAlerts.writeAlert("medium", "RpiADC Log", "Python Error rpiADCLogger.py ", e.message,waitTime = 24*labAlerts.hours)
            time.sleep(LOG_FREQUENCY_SECONDS)
finally:
    rpiADCConnection.close()
