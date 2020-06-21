# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 19:38:05 2015

@author: HUMPHRY
This script is for use with the RPI-ADC box used for logging analog channels,
Inside the box is a MCP-3008 ADC chip connected to a raspberry Pi. 
The chip is run with each of the 8 inputs individually (not in differential mode)

NOTE: The grounds of all channels is shared. Both by connection and by the chip.

NOTE: the box has 10 bit resolution and can measure voltages from 0-3.3V
or 0-5V depending on the position of the switch at the front.

If you change the position of the switch you should also change the value of the V_MAX
parameter in the script


The script must be run from the Rpi and then it can log to the group folder etc.


To use the group folder it should be mounted...

sudo mount -t cifs //192.168.0.2/AQOGroupFolder /media/ursa/AQOGroupFolder/ -o   "username=humphry,password=wsw3ma"
"""
#!/usr/bin/python

import spidev
import threading

class RPiADCMeasurementThread(threading.Thread):
    """takes measurements and updates results dictionary. If settings
    are changed the next measurement will be appropriate"""
    def run(self):
        while True:
            self.rpiADCReference.results = self.rpiADCReference.getResults()

class RPiADC():
    """this class talks to the ADC chip via SPI. It measures selected channels
    N times before updating the measured values. This measured value is what
    can be pulled from the RPiADC server.

    It doesn't do any logging to files. This should be performed by the client.    
    """


    def __init__(self, channels=[0,1,2,3,4,5,6,7], averageN = 100, VMax = 3.3):
        """channels defines which channels will be measured AverageN times before
        the values stored are updated. V Max is set by a switch on the box and
        must be updated here to reflect the status of the switch"""

        # Open SPI bus
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        
        #set channels, averageN, vmax
        self.channels = channels
        self.averageN = averageN
        self.VMax = VMax
        
        self.precision = 3
        
        self.results = {}# where results dictionary will be stored


    def setChannels(self,channels):
        self.channels = channels
        print "channels updated to %s " % channels
        
    def setAverageN(self, averageN):
        self.averageN = averageN
        print "averageN updated to %s " % averageN
        
    def setVMax(self, VMax):
        self.VMax = VMax
        print "VMax updated to %s " % VMax
        
    # Function to read SPI data from MCP3008 chip
    # Channel must be an integer 0-7
    def readChannel(self, channel):
        adc = self.spi.xfer2([1,(8+channel)<<4,0])
        data = ((adc[1]&3) << 8) + adc[2]
        return data

    # Function to convert data to voltage level,
    # rounded to specified number of decimal places.
    def convertVolts(self,data,places):
        volts = (data * self.VMax) / float(1023)
        volts = round(volts,places)
        return volts

    #averages n measurements
    def average(self,channel, n):
        data = [self.readChannel(channel) for _ in range(0, n)]
        total =sum(data)
        return total/ float(n)
        
    def getResults(self):
        """form of results is a dictionary mapping channel number to Voltage """
        return {channel:self.convertVolts( self.average(channel, self.averageN), self.precision) for channel in self.channels}
        
    def start(self):
        """starts the thread getting results and making measurements """
        measurementThread = RPiADCMeasurementThread()
        measurementThread.rpiADCReference = self
        measurementThread.start()


                

