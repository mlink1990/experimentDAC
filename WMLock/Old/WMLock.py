

from PyHWI import *
import time

import threading

class WMLock():

    def __init__( self, state, WMChannel, DACChannel, targetFrequency ):
        # Time between updates, s
        self.updateTime = 1

        self.WMChannel = WMChannel
        self.DACChannel = DACChannel
        self.state = state

        # Target frequency in THz
        self.targetFrequency = targetFrequency

        # Frequency change per volt applied, MHz/V
        self.gain = 1000.0

        self.voltage = dvmValue( 0.0, 0.0, physUnit('V') )

        self.updating = False


    def updateThreadExec( self ):

        while( self.updating == True ):
        
            self.update()
            time.sleep( self.updateTime )
            
    def start( self ):

        if self.updating == True:
            return

        self.updating = True

        self.updateThread = threading.Thread( target=self.updateThreadExec )

        self.updateThread.start()


    def jumpingUpdateThreadExec( self ):

        while( self.updating == True ):
        
            self.update()
            time.sleep( self.updateTime )

            self.voltage.value += 0.2
            self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage ) 
            time.sleep( self.updateTime )
            self.voltage.value -= 0.2
            self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage ) 
            time.sleep( self.updateTime*0.1 )
            

            self.update()
            time.sleep( self.updateTime )
            
    def jumpingStart( self ):

        if self.updating == True:
            return
        self.updating = True

        self.updateThread = threading.Thread( target=self.jumpingUpdateThreadExec )
        self.updateThread.start()
        

    def stop( self ):
        self.updating = False
    
    def update( self ):

        # Get the current frequency
        index, frequency = self.state.WLM.getFrequency( True, self.WMChannel )
        error = (frequency - self.targetFrequency )*10**6

        if abs(error) < 5000.0:

            self.voltage.value += error/self.gain
        
            print "%.1f, %f" % ( error, self.voltage.value )
            self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage ) 

        else:
            self.voltage.value = 0.0
            print "Error too large, setting voltage to zero"
            self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage ) 

    def changeVoltageAndMeasure( self, newVoltageValue ):
        # Set the voltage
        self.voltage.value = newVoltageValue
        self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage )
        
        time.sleep(0.2)

        # Read wavemeter
        index, frequency = self.state.WLM.getFrequency( True, self.WMChannel )

        return frequency

    def findMFR( self ):

        # Finds the modehop free range

        if self.updating == True:
            self.updating = False

        # Step size in volts
        stepSize = 0.1

        # Save the initial voltage and frequency
        initVoltage = self.voltage.value
        index, initFrequency = self.state.WLM.getFrequency( True, self.WMChannel )

        frequency = initFrequency
        
        # Find the top mode-hop
        while( abs(frequency - initFrequency) < 0.01 ):

            newVoltage = self.voltage.value - stepSize
            if newVoltage < -10:
                break

            oldFrequency = frequency            
            frequency = self.changeVoltageAndMeasure( newVoltage )
            
            if abs(oldFrequency - frequency)*10**6 > 2.0* stepSize*self.gain:
                break


        topHeadroom = (oldFrequency - initFrequency)*10**6

        print "Top f headroom = ", topHeadroom, newVoltage

        frequency = self.changeVoltageAndMeasure( initVoltage )
        time.sleep(1)

        # Find the bottom mode-hop
        while( abs(frequency - initFrequency) < 0.01 ):

            newVoltage = self.voltage.value + stepSize
            if newVoltage > 10:
                break

            oldFrequency = frequency            
            frequency = self.changeVoltageAndMeasure( newVoltage )

            if abs(oldFrequency - frequency) > 10* stepSize*self.gain:
                break


        bottomHeadroom = (oldFrequency - initFrequency)*10**6

        print "Bottom f headroom = ", bottomHeadroom, newVoltage

        self.voltage.value = initVoltage
        self.state.DAC.setDACSingle( True, self.DACChannel, self.voltage )
        






               
        
