# -*- coding: utf-8 -*-
"""
Created on Tue Nov 04 09:37:30 2014

@author: tharrison
"""

try:
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'
except ValueError as e:
    print "Error loading QT4. QT4 is required for CSVMaster"
    print "error was: "+ str(e.message)
    pass

import traits.api as traits
import traitsui.api as traitsui 
import os
from pyface.timer.api import Timer
import rpiADCClient
import pyface.image_resource
import platform
import chaco.api as chaco
from enable.api import  ComponentEditor
import scipy

import time
import csv

try:
    import labSounds
    ss=labSounds.getSoundSystem()
except ImportError as e:
    print "no winsound module found... I won't be able to speak :("
    ss=None
ss=None

try:
    import winsound
except ImportError as e:
    print "could not load winsound"
class ADCChannel(traits.HasTraits):
    
    voltage = traits.Float(desc="The voltage of the channel")
    channelName = traits.Str(desc="Human defined name of channel")
    channelNumber = traits.Int(desc = "channel number on box Can be integer from 0 to 7")
    channelMessage = traits.Str(desc="message to denote status of channel")
    criticalValue = traits.Float(desc="the value at which message will change and alarm will sound")
    plotScale = traits.Float(desc="scale factor to multiply voltage by on plot")
    logBool = traits.Bool(desc="if true data logged to a file")
    channelMessageHigh = "high"
    channelMessageLow = "low"
    statusHigh = traits.Bool(False)
    connection = None#It must be passed a connection in initialisation
    checkValueBool = traits.Bool(True)    
    highIsGood = traits.Bool(True)
    highSoundFile = None
    lowSoundFile = None
    
    currentLocalTime = time.localtime()
    currentYear = currentLocalTime.tm_year
    currentMonth = currentLocalTime.tm_mon

    
    
    def _voltage_get(self):
        """Uses PyHWI connection to ADC server to return voltage """
        #print "latest=%s" %  self.connection.latestResults
        if self.channelNumber in self.connection.latestResults:
            return self.connection.latestResults[self.channelNumber]
        else:
            return -999
            
    def check_status(self):
        """check if voltage is higher than critical value and change message """
        if self.voltage>self.criticalValue and not self.statusHigh:#just went high
            self.statusHigh = True
            self.channelMessage = self.channelMessageHigh
            if ss is not None:
                if self.highSoundFile is not None:#specific high soundfile
                    ss.playFile(os.path.join("sounds",self.highSoundFile),1, 60.0)
                elif self.highIsGood:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)#high is good and we just went high so nice sound
                else:
                    winsound.MessageBeep(winsound.MB_ICONHAND)#high is bad and we just went high so bad sound
            
        elif self.voltage<self.criticalValue and self.statusHigh:#just went low
            self.statusHigh = False
            self.channelMessage = self.channelMessageLow
            if ss is not None:
                if self.lowSoundFile is not None:#specific high soundfile
                    ss.playFile(os.path.join("sounds",self.lowSoundFile),1, 60.0)
                if not self.highIsGood:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)#high is bad and we just went low so good sound
                else:
                    winsound.MessageBeep(winsound.MB_ICONHAND)#high is good and we just went low so bad sound
                    
    def _voltage_changed(self):
        """whenever voltage is changed automatically update the status """
        if self.checkValueBool:
            self.check_status()
    
    def _voltage_update(self):
        self.voltage=self._voltage_get()

    def format_function_voltage(value):
        """Format function for voltage """
        if value == -999:
            return "Not in Use"
        else:
            return "%0.3f V" % (value)
        

    channelGroup = traitsui.VGroup(
        traitsui.HGroup(traitsui.Item('channelNumber', label="Channel Number", style="readonly",editor=traitsui.EnumEditor()),
                        traitsui.Item('checkValueBool', label="Check Value")),
        traitsui.Item('channelName',label="Channel Name",style="readonly"),
        traitsui.Item('channelMessage',show_label=False, style="readonly",style_sheet='* { font-size: 16px;  }'),
        traitsui.Item('voltage', show_label=False, style="readonly", format_func=format_function_voltage, style_sheet='* { font-size: 18px;  }'),
        traitsui.Item('criticalValue', label="Critical Voltage", show_label=True, style_sheet='* { font-size: 8px;  }'),
        traitsui.Item('plotScale', label="Plot Scale Factor", show_label=True, style_sheet='* { font-size: 8px;  }'),
        show_border=True
        )
        
    def __init__(self, channelNumber,connection,**traitsDict):
        super(ADCChannel, self).__init__(**traitsDict)
        self.connection = connection
        self.channelNumber = channelNumber
        if self.channelName is "":
            self.channelName = "Channel %s" % channelNumber
        
    traits_view = traitsui.View(channelGroup)
    
    
class ADCHandler(traitsui.Handler):
    """ Simply overidden to make it close the timer cleanly"""
    def closed(self, info, is_ok):
        """ Handles a dialog-based user interface being closed by the user.
        Overridden here to stop the timer once the window is destroyed.
        """
        info.object.timer.Stop()
        info.object.connection.close()#close PyHWI connection to ADC when window closes!
        return


class ADC(traits.HasTraits):
    
    refreshTime = traits.Float(0.1,desc="how often to update the frequencies in seconds")
    logFile = traits.File
    rpiADCLogFolder = traits.String
    averageN = traits.Int(100)
    VMax = traits.Enum(3.3,5.0)
    channelList = traits.List([1,3,5,6], desc="list of channels to show frequencies for and query")
    channelValues = [(0,'Ch 0'),(1,'Ch 1'),(2,'Ch 2'),(3,'Ch 3'),(4,'Ch 4'),(5,'Ch 5'),(6,'Ch 6'),(7,'Ch 7')]   
    #THIS ONLY WORKS IF PyHWI can be found! it is in the python path manager for lab-Monitoring-0
    connection = rpiADCClient.Connection()
    #if there are problems check the server is running on 192.168.0.111
    icon_trait = pyface.image_resource.ImageResource('icons/wavemeter.png')
    #oscilloscope = None
                        
    currentLocalTime = time.localtime()
    currentYear = currentLocalTime.tm_year
    currentMonth = currentLocalTime.tm_mon    
    currentDay =  currentLocalTime.tm_mday

    channel0=ADCChannel(channelNumber=0,connection = connection,channelName = "Na Cavity Lock",
                        channelMessageHigh="Na Cavity Locked", channelMessageLow="Na Cavity Out of Lock", criticalValue = 1.5,
                        highIsGood=True, highSoundFile = "NaLocked.wav", lowSoundFile="NaOutOfLock.wav"
                        )
    
    channel1=ADCChannel(channelNumber=1,connection = connection, channelName = "Li MOT Fluorescence", channelMessageHigh="MOT Loading", channelMessageLow="No MOT", criticalValue =0.1)
    channel2=ADCChannel(channelNumber=2,connection = connection, channelName = "Li MOT Power (stable)")  #changed by Martin
    channel3=ADCChannel(channelNumber=3,connection = connection, channelName = "Li MOT (unstable)")
    channel4=ADCChannel(channelNumber=4,connection = connection, channelName = "Na MOT Power (stable)")
    channel5=ADCChannel(channelNumber=5,connection = connection, channelName = "Na MOT Flourescence")
    channel6=ADCChannel(channelNumber=6,connection = connection, channelName = "ZS light Power")
    channel7=ADCChannel(channelNumber=7,connection = connection, channelName = "disconnected")    

    channels = {0:channel0, 1:channel1, 2:channel2, 3:channel3, 4:channel4, 5:channel5, 6:channel6, 7:channel7}
    def __init__(self, **traitsDict):
        """Called when object initialises. Starts timer etc. """
        print "Instantiating GUI.."
        super(ADC, self).__init__(**traitsDict)
        self.connection.connect()
        self.oscilloscope = Oscilloscope(connection = self.connection, resolution = self.refreshTime,visibleChannels=self.channelList)
        self.start_timer()
    
    def start_timer(self):
        """Called in init if user selected live update mode, otherwise called from menu action.
        Every self.wizard.updateRateSeconds, self._refresh_data_action will be called"""
        print "Timer Object Started. Will update ADC Information every %s seconds" % self.refreshTime
        self.timer=Timer(float(self.refreshTime)*1000, self._refresh_Visible_channels)
    
    def _refreshTime_changed(self):
        self.timer.setInterval(float(self.refreshTime)*1000)
        print "will update ADC every %s seconds" % (float(self.refreshTime))
        self.oscilloscope.resolution=self.refreshTime#use refresh time to set resolution of oscilloscope

    def _logFile_changed(self):
        self._create_log_file()
        
    def _channelList_changed(self):
        """push changes to visible channels in oscilloscope """
        self.oscilloscope.visibleChannels = self.channelList
        
    def _logFile_default(self):
        """default log file has date stamp. log file is changed once a day """
        print "choosing default log file"
        return os.path.join(self.rpiADCLogFolder,time.strftime("rpiADC-%Y-%m-%d.csv", self.currentLocalTime))

    def getGroupFolder(self):
        """returns the location of the group folder. supports both
         linux and windows. assumes it is mounted to /media/ursa/AQOGroupFolder
         for linux"""
        if platform.system()=="Windows":
            groupFolder = os.path.join("\\\\ursa","AQOGroupFolder")
        if platform.system()=="Linux":
            groupFolder = os.path.join("/media","ursa","AQOGroupFolder")
        return groupFolder

    def _rpiADCLogFolder_default(self):
        return os.path.join(self.getGroupFolder(),"Experiment Humphry","Experiment Control And Software","rpiADC","data" )

    def _create_log_file(self):
        if not os.path.exists(os.path.join(self.rpiADCLogFolder,self.logFile)):
            with open(self.logFile, 'a+' ) as csvFile:
                csvWriter = csv.writer(csvFile)  
                csvWriter.writerow(["epochSeconds", "Channel 0","Channel 1", "Channel 2", "Channel 3", "Channel 4", "Channel 5", "Channel 6", "Channel 7" ])

                
    def checkDateForFileName(self):
        """gets current date and time and checks if we should change file name
        if we should it creates the new file and the name"""
        #self.currentLocalTime was already changed in log Temperatures
        if self.currentLocalTime.tm_mday != self.currentDay:
            #the day has changed we should start a new log file!
            self.logFile = self._logFile_default()
            self._create_log_file()

    def _log_channels(self):
        self.currentLocalTime = time.localtime()
        self.checkDateForFileName()
        self.currentMonth = self.currentLocalTime.tm_mon
        self.currentDay = self.currentLocalTime.tm_mday
        
        if not os.path.exists(os.path.join(self.rpiADCLogFolder,self.logFile)):
            self._create_log_file()

        voltages = [self.channels[i]._voltage_get() for i in range(0,8) ]
        with open(self.logFile, 'a+' ) as csvFile:
            csvWriter = csv.writer(csvFile)  
            csvWriter.writerow([time.time()]+voltages)

    def _refresh_Visible_channels(self):
        self.connection.getResults()#updates dictionary in connection object
        for channelNumber in self.channelList:
            channel=self.channels[channelNumber]
            channel._voltage_update()
        self.oscilloscope.updateArrays()
        self.oscilloscope.updateArrayPlotData()
        self._log_channels()
    
    settingsGroup= traitsui.VGroup(traitsui.Item("logFile", label="Log File"),
                                   traitsui.HGroup( traitsui.Item('refreshTime', label='refreshTime'),
                                                    traitsui.Item('averageN', label='averaging Number', tooltip="Number of measurements taken and averaged for value shown"),
                                                    traitsui.Item('VMax', label='Maximum Voltage Setting', tooltip="Whether the box is set to 3.3V or 5V max")),
                                  
                                                    )
                                                    
    selectionGroup = traitsui.Group(traitsui.Item('channelList', editor=traitsui.CheckListEditor(values=channelValues,cols=4), style='custom', label='Show'))
    
    groupLeft = traitsui.VGroup( traitsui.Item('channel0', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(0 in channelList)"),
                                traitsui.Item('channel1', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(1 in channelList)"),
                                traitsui.Item('channel2', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(2 in channelList)"),
                                traitsui.Item('channel3', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(3 in channelList)"))
                                
    groupRight = traitsui.VGroup( traitsui.Item('channel4', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(4 in channelList)"),
                                traitsui.Item('channel5', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(5 in channelList)"),
                                traitsui.Item('channel6', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(6 in channelList)"),
                                traitsui.Item('channel7', editor=traitsui.InstanceEditor(),style='custom', show_label=False, visible_when="(7 in channelList)"))

    groupOscilloscope = traitsui.Group(traitsui.Item('oscilloscope', editor=traitsui.InstanceEditor(),style='custom', show_label=False))

    groupAll = traitsui.VGroup(
                    settingsGroup, 
                    selectionGroup,
                    traitsui.VSplit(
                        traitsui.HGroup(groupLeft, groupRight),
                        groupOscilloscope
                        )
                    )
                    
    traits_view = traitsui.View(groupAll,resizable = True, title="ADC Monitor",handler = ADCHandler(), icon=icon_trait)


class Oscilloscope(traits.HasTraits):
    """Oscilloscope style plot of the selected channels. Rolling mode/ auto trigger """
    masterContainer =  traits.Instance(chaco.Plot)
    arrayPlotData = traits.Instance(chaco.ArrayPlotData)
    visibleChannels = traits.List([0])
    connection = None
    numberOfPoints = traits.Int(10000, desc="number of points displayed on plot. number of Points*resolution = timespan of plot")
    verticalLimit = traits.Range(low=0.0, high=5.0, value=3.3)
    resolution = traits.Float(0.1, desc="number of points displayed on plot. number of Points*resolution = timespan of plot")
    
    settingsGroup = traitsui.Group(traitsui.Item("numberOfPoints"),
                                   traitsui.Item("verticalLimit", label="Vertical Scale"))    
    
    traits_view = traitsui.View(
                        traitsui.VGroup(
                            settingsGroup,
                            traitsui.Group(
                                traitsui.Item('masterContainer', editor=ComponentEditor(), show_label=False)
                                )
                            )
                        )
    
    def __init__(self, **traitsDict):
        """initialise the plot"""
        super(Oscilloscope, self).__init__(**traitsDict)
        self.colors = ["black", "red", "blue"]
        self.initialiseData()        
        self.initialisePlots()
        self._visibleChannels_changed()
        
    def _visibleChannels_changed(self):
        """make channels visible or not depending on list """
        for i in range(0,8):
            if i in self.visibleChannels:
                self.masterContainer.plots["channel"+str(i)][0].visible=True
            else:
                print i
                self.masterContainer.plots["channel"+str(i)][0].visible=False
                
                                     
    def _numberOfPoints_changed(self):
        """when number of points changes re-initialise the data """
        self.reinitialiseData()
            
    def _resolution_changed(self):
        """when resolution of points changes re-initialise the data """
        self.reinitialiseData()
        
    def _verticalLimit_changed(self):
        """"changes y scale of vertical axis """
        self.masterContainer.range2d.y_range.high = self.verticalLimit
     
    def initialisePlots(self):
        """draw plots """
        self.masterContainer = chaco.Plot(self.arrayPlotData, padding=100, bgcolor="white",use_backbuffer=True,border_visible=False,fill_padding=True)
        self.masterContainer.plot(("xs","channel0"), type="line", name="channel0", color=self.colors[0%len(self.colors)])
        
        self.masterContainer.plot(("xs","channel1"), type="line", name="channel1",color=self.colors[1%len(self.colors)])
        
        self.masterContainer.plot(("xs","channel2"), type="line", name="channel2",color=self.colors[2%len(self.colors)])
        self.masterContainer.plot(("xs","channel3"), type="line", name="channel3",color=self.colors[3%len(self.colors)])
        
        self.masterContainer.plot(("xs","channel4"), type="line", name="channel4",color=self.colors[4%len(self.colors)])
        self.masterContainer.plot(("xs","channel5"), type="line", name="channel5",color=self.colors[5%len(self.colors)])
        
        self.masterContainer.plot(("xs","channel6"), type="line", name="channel6",color=self.colors[6%len(self.colors)])
        self.masterContainer.plot(("xs","channel7"), type="line", name="channel7",color=self.colors[7%len(self.colors)])
        self.masterContainer.plot(("cursorXS","cursorVertical"), type="line",line_style = "dash", name="cursor",color="green")

    def getCurrentPositionAsFloat(self):
        return self.currentPosition*self.resolution
        
    
    def getCurrentPositionArray(self):
        return scipy.array([self.currentPosition*self.resolution]*2)

    def initialiseData(self):
        """sets up data arrays and fills arrayPlotData """
        self.currentPosition = 0
        self.xs = scipy.linspace(0.0, self.numberOfPoints*self.resolution, self.numberOfPoints)
        self.cursorXS = self.getCurrentPositionArray()
        self.cursorVertical = scipy.array([self.verticalLimit,0.0])
        self.array0 = scipy.zeros(self.numberOfPoints)
        self.array1 = scipy.zeros(self.numberOfPoints)
        self.array2 = scipy.zeros(self.numberOfPoints)
        self.array3 = scipy.zeros(self.numberOfPoints)
        self.array4 = scipy.zeros(self.numberOfPoints)
        self.array5 = scipy.zeros(self.numberOfPoints)
        self.array6 = scipy.zeros(self.numberOfPoints)
        self.array7 = scipy.zeros(self.numberOfPoints)
        self.channels = [self.array0,self.array1,self.array2,self.array3,
                         self.array4,self.array5,self.array6,self.array7]
        self.arrayPlotData = chaco.ArrayPlotData(xs=self.xs,channel0=self.array0,channel1=self.array1,
                                     channel2=self.array2,channel3=self.array3,
                                     channel4=self.array4,channel5=self.array5,
                                     channel6=self.array6,channel7=self.array7,
                                     cursorXS = self.cursorXS, cursorVertical=self.cursorVertical)#will be the ArrayPlotData We need

    def reinitialiseData(self):
        """sets up data arrays and fills arrayPlotData """
        if self.arrayPlotData is not None:
            self.currentPosition = 0
            self.xs = scipy.linspace(0.0, self.numberOfPoints*self.resolution, self.numberOfPoints)
            self.cursorXS = self.getCurrentPositionArray()
            self.cursorVertical = scipy.array([self.verticalLimit,0.0])
            self.arrayPlotData.set_data("xs",self.xs)
            self.array0 = scipy.zeros(self.numberOfPoints)
            self.array1 = scipy.zeros(self.numberOfPoints)
            self.array2 = scipy.zeros(self.numberOfPoints)
            self.array3 = scipy.zeros(self.numberOfPoints)
            self.array4 = scipy.zeros(self.numberOfPoints)
            self.array5 = scipy.zeros(self.numberOfPoints)
            self.array6 = scipy.zeros(self.numberOfPoints)
            self.array7 = scipy.zeros(self.numberOfPoints)
            self.channels = [self.array0,self.array1,self.array2,self.array3,
                             self.array4,self.array5,self.array6,self.array7]
            self.updateArrayPlotData()

    def _voltage_get(self, channelNumber):
        """Uses PyHWI connection to ADC server to return voltage """
        #print "latest=%s" %  self.connection.latestResults
        if channelNumber in self.connection.latestResults:
            return self.connection.latestResults[channelNumber]
        else:
            return scipy.NaN
    
    def updateArrays(self):
        """update all arrays with the latest value """
        for channelNumber in range(0, 8):
            self.channels[channelNumber][self.currentPosition]=self._voltage_get(channelNumber)#update next element in each array
        self.currentPosition+=1
        if self.currentPosition>=self.numberOfPoints:#reset position to beginning when we hit max number of points (like rolling oscilloscope)
            self.currentPosition=0
        self.cursorXS = self.getCurrentPositionArray()
        #could also set the next points to NaN's to make a gap!
        
    def updateArrayPlotData(self):
        """push changes of arrays to the plot """
        self.arrayPlotData.set_data("channel0",self.array0)
        self.arrayPlotData.set_data("channel1",self.array1)
        self.arrayPlotData.set_data("channel2",self.array2)
        self.arrayPlotData.set_data("channel3",self.array3)
        self.arrayPlotData.set_data("channel4",self.array4)
        self.arrayPlotData.set_data("channel5",self.array5)
        self.arrayPlotData.set_data("channel6",self.array6)
        self.arrayPlotData.set_data("channel7",self.array7)
        self.arrayPlotData.set_data("cursorXS",self.cursorXS)
        #self.arrayPlotData.set_data("cursorVertical",self.cursorVertical)


if __name__ == "__main__":
#    try:
    if os.name == 'nt':
        import ctypes
        print "changing to use a seperature processs!!!!"
        myappid = 'AQO.ADCMonitor' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    WC = ADC()
    WC.configure_traits(view='traits_view')
#    finally:
#        print "Rpi ADC connections (finally statement)"
#        WC.connection.close()
   