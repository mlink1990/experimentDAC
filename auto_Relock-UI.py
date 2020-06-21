'''
Created on 10 Dec 2015

Wavemeterlock Daniel 17 Sept 2018

@author: Martin
'''

import traits.api as traits
import traitsui.api as traitsui
import AD5754_BCgen as ad #bytecode generator for AD5754R EVAL board 
import ADEval_client
import time
import rpiADCClient
from pyface.timer.api import Timer
import numpy as np
import PyHWI

from pyface.timer.api import Timer


class GetOutOfLoop( Exception ):
    pass

class DACChannel(traits.HasTraits):


    
    def __init__(self, setchannelName, port, connection, rpiADC):
        self.channelName = setchannelName
        self.x = ad.ADEvalBC()
        self.port = port
        self.connection = connection
        self.rpiADC = rpiADC
        self.wmLockTimer = Timer(1000, self.wmLock2)
        self.wmLockTimer.Stop()
#        time.sleep(5)
#        self.start_timer()
        
        
        
    update = traits.Button()
    set = traits.Button()
    
    pinMode = '0'    
    relockMode = traits.Enum("Manual Mode", "Doubling cavity Relock", "Wavemeter Relock", "Wavemeter Lock")
    #set_Relock = traits.Button()
    
#---- MANUAL MODE ----#    
    
    voltage = traits.Float(desc="Voltage of the Channel")
    setVoltage = traits.Float(desc="set Voltage")
    powerModeMult = 0
    channelName = traits.Str(desc="Name")
    channelDescription = traits.Str(desc="Description")
    powerMode = traits.Enum(5, 10, 10.8,
                            desc = "power Mode",
                            )
    bipolar = traits.Bool(desc="Bipolarity")
    channelMessage = traits.Str()
    bytecode = traits.Str()
    port = traits.Str()
    
    def pinSet(self, channel, mode):
        cmd = "pin="+channel+mode
        self.connection.send(cmd)
        #print cmd
    
    def _update_fired(self):
        if self.bipolar == True:
            a= "bipolar"
            bip = True
            self.powerModeMult = -1
        else:
            a= "unipolar"
            bip = False
            self.powerModeMult = 0
            
        cmd = "cmd="+self.x.setMaxValue(self.port, self.powerMode, bip)
        #print cmd
        self.connection.send(cmd)
        b= "Mode set to %.1f" %self.powerMode
        self.channelMessage = b + ' ' + a
        self._set_fired()
    
    def _set_fired(self):
        if ((self.setVoltage > self.powerMode) and (self.bipolar == False)):
            print "setVoltage out of bounds. Not sending."
        elif ((abs(self.setVoltage) > self.powerMode) and (self.bipolar == True)) :
            print "setVoltage out of bounds. Not sending."
        else:
            cmd = "cmd=" + self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, self.setVoltage)
            self.connection.send(cmd)
            self.bytecode = self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, self.setVoltage)
            self.voltage = self.setVoltage
        

        
#---- MANUAL MODE GUI ----#

                   
    voltageGroup = traitsui.HGroup(
                            traitsui.VGroup(
                                           traitsui.Item('voltage', label="Measured Voltage",  style_sheet='* { font-size: 18px;  }', style="readonly"),
                                           traitsui.Item('setVoltage', label="Set Value"), ),
                            traitsui.Item('set', show_label=False),
                            show_border=True
                                   )
    
    powerGroup = traitsui.VGroup(
                                 traitsui.HGroup(
                                                 traitsui.Item('powerMode', label="Power Mode"),
                                                 traitsui.Item('bipolar'),
                                                 ),
                                 traitsui.HGroup(
                                                 traitsui.Item('update', show_label = False),
                                                 traitsui.Item('channelMessage', show_label = False, style = "readonly"),
                                                 ),
                                 traitsui.Item('bytecode', show_label = False, style = "readonly"),
                                 traitsui.Item('switch_Lock'),
                                 show_border=True
                                 )
    
    manualGroup = traitsui.VGroup(
        traitsui.Item('channelName',label="Channel Name", style="readonly"),
        voltageGroup,
        show_border=True,
        visible_when = 'relockMode == "Manual Mode"'
        )
        
#---- DOUBLING CAVITY MODE GUI----#

    adcChannel = traits.Enum(0,1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                               desc = "Channel of the rpiADC")
    adcVoltage = traits.Float(desc= "Voltage on rpiADC Channel")
    DCscan_and_lock = traits.Button()
    switch_Lock = traits.Button()
    DCconnect = traits.Bool()
    DCautolock = traits.Button()
    DCadcVoltages = None
    DCadcVoltagesMean = None
    DCtolerance = 0.01 #Volt
    DCmistakeCounter = 0
    DCminBoundary = traits.Float()
    DCmaxBoundary = traits.Float()
    DCnoOfSteps = traits.Int()
    
    #Updates voltage of the selected channel"
    def _adcVoltage_update(self):
        self.adcVoltage = self._adcVoltage_get() 
    
	#Gets voltage of the selected channel via rpiADC Client    
    def _adcVoltage_get(self):
        return self.rpiADC.getResults()[self.adcChannel]        
#        print "latest results = %s " % self.rpiADC.latestResults
#        self.rpiADC.getResults()
#        print "latest results = %s " % self.rpiADC.latestResults
#        if self.adcChannel in self.rpiADC.latestResults:
#            return self.rpiADC.latestResults[self.adcChannel]
#        else:
#            return -999
	
	#As soon as the connect button is checked, automatic updating of the adc voltage is initiated.
	#When it is unchecked, the update stops
    def _DCconnect_changed(self):
         
        if self.DCconnect == True:         
            self._start_PD_timer()
        else:
            self.PDtimer.stop()
            self.adcVoltage = -999
            print "PD timer stopped."
     
	#Starts the timer, that only updates the displayed voltage
    def _start_PD_timer(self):
         self.PDtimer = Timer(1000.0, self._adcVoltage_update)
		 
    #Starts a timer, that updates the displayed voltage, as well as does the "in lock" checking     
    def _start_PD_lock_timer(self):
        self.PDtimer = Timer(1000.0, self.update_PD_and_Lock)
    
	#Controls if everything is still in lock. Also updates displayed voltage. It counts still in lock, when the measured frequency
	#is within DC tolerance of the mean of the last five measured frequencies.
    def update_PD_and_Lock(self):     
        self._adcVoltage_update() #still display Voltage
        pdVoltage = self._adcVoltage_get()
        #print "Updated Frequency"
        #mistakeCounter = 0
        if len(self.DCadcVoltages) < 5: #number of Measurements that will be compared
            print "Getting Data for Lock. Do not unlock!"
            self.DCadcVoltages = np.append( self.DCadcVoltages, pdVoltage )
        else:
            self.DCadcVoltagesMean = np.mean( self.DCadcVoltages ) #Mean Frequency to compare to
            if (abs(pdVoltage - self.DCadcVoltagesMean) < self.DCtolerance):
                self.DCadcVoltages = np.append( self.DCadcVoltages, pdVoltage )
                self.DCadcVoltages = np.delete( self.DCadcVoltages, 0 ) #keep Array at constant length
                print "Still locked."
                if self.DCmistakeCounter > 0:
                    self.DCmistakeCounter = 0
            else:
                self.DCmistakeCounter += 1
                if self.DCmistakeCounter >5:
                    self.PDtimer.stop()
                    self._start_PD_timer() #keep Frequency on display..
                    self._DCscan_and_lock_fired()
                    self._DCautolock_fired()
                else: print self.DCmistakeCounter
                
    
        
    #This button is used, when everything is already locked. It prepares the voltage mean array, stops the PD timer and starts the update_PD_and_Lock timer routine
    def _DCautolock_fired(self):
        if self.DCconnect == True:        
            self.DCadcVoltages = np.array([])
            self.PDtimer.stop()
            self._start_PD_lock_timer()
        else:
            print "No adcRPi connected."
        
        
	#This function (button) scans the voltage and reads the RPiADC voltage of the selected channel. It subsequently attempts
	#to lock the Cavity at the voltage, where the RPiADC voltage is highest. The Algorithm for the lock is as follows:
	#1) It does a coarse DAC voltage scan with the parameters selected in the input (minBoundary etc). This scan is terminated when
	#	the adc voltage goes above a threshold (3.2 V - hardcoded, maybe add input), or after scanning the whole range.
	#2) A fine scan 0.3V(dac) around the maximum (or around the 3.2V dac voltage) is done. Currently the number of steps is hardcoded to 600,
	#	which worked well. This scan terminated either by going to a 3.3V (adc) threshhold or after finishing. 
	#3) The Cavity is locked at a dac voltage that corresponds to either the maximum after the whole scan or the 3.3V threshold.
    def _DCscan_and_lock_fired(self):
        self.pinSet(self.port, '1') #Unlock
        time.sleep(1) #If the cavity was in lock before we can not directly start scanning, or else it will read 3.3V as first value
        voltages = np.linspace(self.DCminBoundary, self.DCmaxBoundary, self.DCnoOfSteps) #Parameters for first scan set by GUI
        diodeVoltages = np.array([])
        for entry in voltages: #First scan
            self.setVoltage = entry
            self._set_fired() #update setVoltage
            diodeVoltages = np.append(diodeVoltages, self._adcVoltage_get())
            volt = self._adcVoltage_get()
            print volt
            if volt >= 3.2: #Threshold for first scan
                break
            time.sleep(0.05) #sleep time between every step for adc readout, maybe it is possible to make the scan faster
        self.setVoltage = voltages[diodeVoltages.argmax(axis=0)] #DAC Voltage corresponding to the highest adc voltage
        print "Attempting to reduce scan Range"
        print self.setVoltage
        time.sleep(2.0)
        if self.setVoltage < 0.3: #make sure we do not scan below zero, as the lock box does not like negative voltages.
            auxSetVolt = 0
        else: 
            auxSetVolt = self.setVoltage - 0.3
        voltages = np.linspace(auxSetVolt, self.setVoltage + 0.3, 600) #parameters for second scan
        diodeVoltages = np.array([])
        for entry in voltages: #Second scan
            if entry > self.powerMode: #Our voltage can not go above our maximum value
                break
            self.setVoltage = entry
            self._set_fired()
            diodeVoltages = np.append(diodeVoltages, self._adcVoltage_get())
            volt = self._adcVoltage_get()            
            print volt
            if volt >= 3.3: #threshold for second scan
                print self.setVoltage
                self.pinSet(self.port, '0')                
                return
            time.sleep(0.1)
        self.setVoltage = voltages[diodeVoltages.argmax(axis=0)]        
        print "DAC Voltage set to %f" % voltages[diodeVoltages.argmax(axis=0)]
        print ".. this corresponds to a diode Voltage of %f" % diodeVoltages[diodeVoltages.argmax(axis=0)]
        self._set_fired()
        time.sleep(0.2)
        self.pinSet(self.port, '0') #Lock
        print "Voltage set to %f to attempt relock." % self.setVoltage
        return

        
            
    #Changes from lock to dither and other way around    
    def _switch_Lock_fired(self):
        if self.pinMode == '0':
            self.pinMode ='1'
            self.pinSet(self.port, self.pinMode)
        else:
           self.pinMode ='0'
           self.pinSet(self.port, self.pinMode) 
    

#Gui Stuff#	
    DCgroup = traitsui.VGroup(
        traitsui.HGroup(        
        
        traitsui.VGroup(        
        traitsui.Item('adcChannel'),
        traitsui.Item('adcVoltage', style = 'readonly'),),
        traitsui.VGroup(
        traitsui.Item('DCmaxBoundary'),
        traitsui.Item('DCminBoundary'),
        traitsui.Item('DCnoOfSteps'),        
        ),
        
        ),
        #traitsui.Item('switch_Lock'),
        traitsui.HGroup(
        traitsui.VGroup(        
        traitsui.Item('DCscan_and_lock'),
        traitsui.Item('DCautolock'),
        ),   
        traitsui.Item('DCconnect')        
        ),
        visible_when = 'relockMode == "Doubling cavity Relock"',
        show_border=True,
    )
        
 
#---- WAVEMETER GUI ----#
    wavemeter = traits.Enum("Humphry", "Ion Cavity")
    wmChannel = traits.Enum(1, 2, 3, 4, 5, 6, 7, 8)
    wmFrequency = traits.Float()
    wmConnected = traits.Bool()
    wmHWI = None
    wmIP = None
    wmPort = None
    wmReLock = traits.Button()
    wmFrequencyLog = np.array([])
    wmMeanFrequency = None
    wmTolerance = 0.0000006 #Frequency tolerance in THz, set to 60 MHz in accordance with wm accuracy
    mistakeCounter = 0
    #wmPolarity = traits.Enum("+", "-")
    wmEmptyMemory = traits.Button()
    
	#When hitting wmConnected, a connection to the wavemeter and readout is established
    def _wmConnected_changed(self):
        if self.wmConnected == True:
            if self.wavemeter == "Humphry":
                self.wmIP = '192.168.0.111'
                self.wmPort = 6101
            elif self.wavemeter == "Ion Cavity":
                self.wmIP = '192.168.32.2'
                self.wmPort = 6100
                
            self.wmHWI = PyHWI.DECADSClientConnection( 'WLM', self.wmIP, self.wmPort )
            #frequencyArray = wmHWI.getFrequency(True, self.wmChannel) 
            self.start_timer()
        else: 
            self.wmFrequency = -999
            self.timer.Stop() #stops either lock_timer or read_timer.
            print "Timer stopped"

    #GUI stuff
    wmGroup = traitsui.VGroup(
        traitsui.Item('wmFrequency', style='readonly'),
        traitsui.Item('wmConnected'),
        traitsui.Item('wmReLock'),
        traitsui.HGroup(        
            traitsui.Item('wavemeter'),
            traitsui.Item('wmChannel'),
            traitsui.Item('wmEmptyMemory', show_label = False)
        ),
        visible_when = 'relockMode == "Wavemeter Relock"'
    )
    
	#Resets the memory of the lock (the array which saves the last read frequencies)
    def _wmEmptyMemory_fired(self):
        self.wmFrequencyLog = np.array([])
        print "Memory empty."
    
	#starts readout-only timer
    def start_timer(self):
        print "Timer started"
        self.timer = Timer(1000.0, self.update_wm)
    
	#starts readout-and-lock timer, analogue to the doubling cavity case    
    def start_lock_timer(self):
        print "Lock timer started"
        self.timer = Timer(1000.0, self.update_wm_and_lock)
    
	#updates the displayed frequency
    def update_wm(self):
        frequencyArray = self.wmHWI.getFrequency(True, self.wmChannel)
        self.wmFrequency = frequencyArray[1]
    
	#updates frequency and checks if its still near the mean of the last five (hardcoded, see below) measured frequencies. If not, it attempts a relock.
    def update_wm_and_lock(self): 
        self.update_wm()
        frequencyArray = self.wmHWI.getFrequency(True, self.wmChannel)
        #print "Updated Frequency"
        #mistakeCounter = 0
        if len(self.wmFrequencyLog) < 5: #number of Measurements that will be compared
            print "Getting Data for Lock. Do not unlock!"
            self.wmFrequencyLog = np.append( self.wmFrequencyLog, frequencyArray[1] )
        else:
            self.wmMeanFrequency = np.mean( self.wmFrequencyLog ) #Mean Frequency to compare to
            if (abs(frequencyArray[1] - self.wmMeanFrequency) < self.wmTolerance):
                self.wmFrequencyLog = np.append( self.wmFrequencyLog, frequencyArray[1] )
                self.wmFrequencyLog = np.delete( self.wmFrequencyLog, 0 ) #keep Array at constant length
                print "Still locked."
                if self.mistakeCounter > 0:
                    self.mistakeCounter = 0
            else:
                self.mistakeCounter += 1
                if self.mistakeCounter >5: #number of measurements that still count as locked, though the frequency is not within boundaries
                    self.timer.stop()
                    self.start_timer() #keep Frequency on display..
                    self.wmRelock(self.wmMeanFrequency) 
                else: print self.mistakeCounter
                
    #Relock procedure.
	#For now this scans only one time, with a hardcoded number of steps. It might be worth modifying this to look like the doubling cavity relock procedure.
    def wmRelock(self, wantedFrequency):
        self.pinSet(self.port, '1')
        voltages = np.linspace(self.powerModeMult*self.powerMode, self.powerMode, 10)
        wmRelockTry = 0
        try:            
            while (wmRelockTry < 5):  #attempt relock five times      
                for entry in voltages:
                    self.setVoltage = entry
                    self._set_fired()
                    time.sleep(1.0)
                    frequencyArray = self.wmHWI.getFrequency(True, self.wmChannel)
                    if (abs(frequencyArray[1]-wantedFrequency) < self.wmTolerance):
                        print "Relock_attempt!"
                        self.pinSet(self.port, '0')
                        self._wmLock_fired()
                        raise GetOutOfLoop#Opens the function again (inductively). Maybe fix that by going back
                        #to the level above somehow.
                wmRelockTry+=1
                print "Relock try %f not succesful" % wmRelockTry
            print "Was not able to Relock."
        except GetOutOfLoop:
            print "gotOutOfLoop"
            pass
        
                
            
            
        
    def _wmReLock_fired(self):
        #self.wmFrequencyLog = np.array([])
        self.mistakeCounter = 0        
        if self.wmConnected == True:
            self.timer.Stop()  #Switch from read-only timer to read-and-log timer. If both run at the same time
            self.start_lock_timer() #we run into timing problems.
        else:
            print "No Wavemeter connected!"
        
        print "hi"

#---- WAVEMETERLOCK - DE 17092018 GUI ----#
    wavemeter = traits.Enum("Humphry", "Ion Cavity")
    wmChannel = traits.Enum(1, 2, 3, 4, 5, 6, 7, 8)
    wmFrequency = traits.Float()
    wmConnected = traits.Bool()
    wmHWI = None
    wmIP = None
    wmPort = None
    isRunning = traits.Bool(False)
    wmVoltage = 0
    wmLockTimer = traits.Instance(Timer)
    wmLockStart = traits.Button()
    wmLockStop = traits.Button()
    wmFrequencyLog = np.array([])
    wmMeanFrequency = None
    wmTargetFrequency = traits.Float()#frequency to lock
    wmGain = traits.Float()#Gain for wavemeterlock
    wmTolerance = 0.0000006 #Frequency tolerance in THz, set to 60 MHz in accordance with wm accuracy
    mistakeCounter = 0
    #wmPolarity = traits.Enum("+", "-")
    wmEmptyMemory = traits.Button()
    
    #GUI stuff
    wmlockGroup = traitsui.VGroup(
        traitsui.HGroup(        
            traitsui.Item('wavemeter'),
            traitsui.Item('wmChannel'),
            traitsui.Item('wmEmptyMemory', show_label = False)
        ),
        traitsui.Item('wmFrequency', style='readonly'),
        traitsui.Item('wmConnected'),
        traitsui.Item('wmTargetFrequency'),
        traitsui.Item('wmGain'),
        traitsui.HGroup( 
            traitsui.Item('wmLockStart', visible_when = "isRunning == False"),
            traitsui.Item('wmLockStop', visible_when = "isRunning == True")
        ),
        visible_when = 'relockMode == "Wavemeter Lock"'
    )


    def _wmLockStart_fired( self ):
        print "Start: Wavemeterlock"
        self.isRunning = True
        self.wmLockTimer.Start()
        
    def wmLock2( self ):
        # Calculate error in MHz
        error = (self.wmFrequency - self.wmTargetFrequency)*10**3
        if abs( error ) < 5000: 
            self.wmVoltage = self.wmVoltage + error * self.wmGain
            if self.wmVoltage > 10:
                self.wmVoltage = 10
            elif self.wmVoltage < -10:
                self.wmVoltage = -10
        
        cmd = "cmd=" + self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, self.wmVoltage)
        self.connection.sendwithoutcomment(cmd)
        self.bytecode = self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, self.wmVoltage)

        #self.saveToFile( "frequency_data.csv" )

    def _wmLockStop_fired( self ):
        print "Stop: Wavemeterlock"
        self.isRunning = False
        
        cmd = "cmd=" + self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, 0)#Spannung wieder auf 0
        self.connection.sendwithoutcomment(cmd)
        self.bytecode = self.x.generate_voltage(self.port, self.powerMode, self.powerModeMult*self.powerMode, 0)
        self.wmVoltage = 0 

        self.wmLockTimer.Stop()

    def saveToFile( self, fileName ):

        f = open( fileName, "a" )

        f.write( "%f \n" % self.wmFrequency )

        f.close()


#---- PUT TOGETHER CHANNEL ----#        
    selectionGroup = traitsui.HGroup(
        traitsui.Item('relockMode'),
        #traitsui.Item('set_Relock'),        
        )
        
    channelGroup= traitsui.VGroup (
        selectionGroup,
        powerGroup,
        wmGroup,
        wmlockGroup,
        DCgroup,
        manualGroup,
    )

    
    traits_view = traitsui.View(channelGroup)

    
    
class DACHandler(traits.HasTraits):
    connection = ADEval_client.Connection()
    rpiADC = rpiADCClient.Connection()
    def __init__(self):
        self.x = ad.ADEvalBC()
        self.connection.connect() #connect to ADEval
        #self.rpiADC.connect() # connect to rpiADC
        #self.start_timer()
        
    
    DACC1 = DACChannel("DAC A", 'A', connection, rpiADC)
    DACC2 = DACChannel("DAC B", 'B', connection, rpiADC)
    DACC3 = DACChannel("DAC C", 'C', connection, rpiADC)
    DACC4 = DACChannel("DAC D", 'D', connection, rpiADC)
    
    power_A = traits.Bool(desc="Power A")
    power_B = traits.Bool(desc="Power B")
    power_C = traits.Bool(desc="Power C")
    power_D = traits.Bool(desc="Power D")
    Power_switch = traits.Button()
    
    
#    def start_timer(self):
#        print "Timer started"
#        self.timer = Timer(1000.0, self.update_channels) 
#        
#    def update_channels(self):
#        self.DACC1._adcVoltage_update()
#        self.DACC2._adcVoltage_update()
#        self.DACC3._adcVoltage_update()
#        self.DACC4._adcVoltage_update()
    
    groupLeft = traitsui.VGroup(
                    traitsui.Item('DACC1', editor=traitsui.InstanceEditor(),style='custom', show_label=False , resizable = True),
                    traitsui.Item('power_A'),
                    traitsui.Item('DACC3', editor=traitsui.InstanceEditor(),style='custom', show_label=False),
                    traitsui.Item('power_C'),
                    
                    
                    )
    
    groupRight = traitsui.VGroup(
                    traitsui.Item('DACC2', editor=traitsui.InstanceEditor(),style='custom', show_label=False),
                    traitsui.Item('power_B'),
                    traitsui.Item('DACC4', editor=traitsui.InstanceEditor(),style='custom', show_label=False),
                    traitsui.Item('power_D'),
                                 )

    groupH = traitsui.HGroup(
                    groupLeft,
                    groupRight,
                               )
   
    groupall = traitsui.VGroup(
                               groupH,
                               traitsui.Item('Power_switch', show_label=False),
                               )
    

    
    def _Power_switch_fired(self):
        #print self.x.setPowerMode( [self.power_A, self.power_B, self.power_C, self.power_D] )
        cmd = "cmd=" + self.x.setPowerMode( [self.power_A, self.power_B, self.power_C, self.power_D] )
        self.connection.send(cmd)
    
    
    traits_view = traitsui.View(groupall, resizable = True)
    
DACHandler().configure_traits()
