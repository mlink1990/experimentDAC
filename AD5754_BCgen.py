'''
Created on 14 Dec 2015

@author: Martin
'''

#This class generates the bytecode to be sent to the RPi, which then subsequently sends it to the DAC

class ADEvalBC():
    
    
    def bth( self, a ):
        return int(a ,2)
    
        # This function generates the adress bits for the different DACs
    def getChannelAdress( self, chan ):
        if (chan == 'A'):
            return '000'
        elif chan == 'B':
            return '001'
        elif chan == 'C':
            return '010'
        elif chan == 'D':
            return '011'
        elif chan == 'all':
            return '100'
        else: 
            print 'wrong channel!'
            return None

    def turnOnAllDACs(self):
        return "000100000000000000001111"
    #Generates a voltage on the given Channel, taking into account the different Settings
    # for the maximum value    
    def generate_voltage (self, chan, maxSet, minSet, setPoint):
    
        RWHead = '00'
        DACRegister = '000'
        DACAdr = self.getChannelAdress( chan )
        firstByte = RWHead + DACRegister + DACAdr  #First Byte, adress etc.
    
        
        factor = 65535.0/(maxSet - minSet) #16Bit resolution
        intSetPoint = int((setPoint-minSet) * factor)
        #print intSetPoint
        lastBytes = '{0:016b}'.format(intSetPoint)
        return firstByte + lastBytes[0:8] + lastBytes[8:16]



    #Sets the voltage Range of the DAC for selected Channel
    def setMaxValue(self, chan, maxSet, bipolar):
        if maxSet == 5:
            if bipolar == True:
                OutputReg = '011'
            else:
                OutputReg = '000'
        elif maxSet == 10:
            if bipolar == True:
                OutputReg = '100'
            else:
                OutputReg = '001'        
        elif maxSet == 10.8:
            if bipolar == True:
                OutputReg = '101'
            else:
                OutputReg = '010'
        else:
            return 'Voltage not supported!'
    
        DACAdr = self.getChannelAdress( chan )
    
        inputo = '00001' + DACAdr + '0000000000000' + OutputReg
        return inputo[0:8]+ inputo[8:16] + inputo[16:24] 
        #return inputo  
    
    #Sets the channels to Power Modes, takes [Bool, Bool, Bool, Bool] as argument.
    #True means power Mode on, False means off, channels are [A, B, C, D]
    def setPowerMode( self, channelModes ):
        regHead = '0001000000000'
        regTorso = '0000000'
        if channelModes[0] == True:
            pUa = '1'
        else:
            pUa = '0'
        if channelModes[1] == True:
            pUb = '1'
        else:
            pUb = '0'
        if channelModes[2] == True:
            pUc = '1'
        else:
            pUc = '0'
        if channelModes[3] == True:
            pUd = '1'
        else:
            pUd = '0'
        input = regHead + regTorso + pUd + pUc + pUb + pUa
        return input[0:8] + input[8:16] + input[16:24] 
        
        
#===============================================================================
#     def readVoltage(self, chan, maxVolt):
#         RWHead = '10'
#         DACRegister = '000'
#         DACAdr = self.getChannelAdress( chan )
#         firstByte = RWHead + DACRegister + DACAdr  #First Byte, adress etc.
# 
#         crapByte1 = '00000000'
#         crapByte2 = '00000000'
#         a = self.send_input( [ self.bth(firstByte), self.bth(crapByte1), self.bth(crapByte2) ] ) 
#         #print "{0:08b}".format(a[0])
#         voltageInt = self.bth( "{0:08b}".format(a[1]) + "{0:08b}".format(a[2]) )
#         print ((voltageInt/65535.0)-0.5)*2*maxVolt
#===============================================================================
        
if __name__=="__main__":
    bc = ADEvalBC()
    