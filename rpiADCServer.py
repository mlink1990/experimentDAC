# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 12:36:28 2015

@author: tharrison
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 10:39:53 2015

@author: tharrison
"""

import server
import logging
import rpiADC

IP_ADDRESS = "192.168.16.28"   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

logger=logging.getLogger("rpiADC.rpiADCServer")

class RPiADCServer:
    
    def __init__(self, PORT=PORT, IP_ADDRESS=IP_ADDRESS, channels = [0,1,2,3,4,5,6,7], VMax = 3.3, averageN =100):
        """construct Synth Network Manager object.
        pin is GPIO pin on the Raspberry pi that the trigger input is connected to.        
        """
        logger.debug("initialisng synthNetworkManager")
        self.PORT = PORT
        self.IP_ADDRESS = IP_ADDRESS
        
        #defined by functions below
        self.server = None
        self.rpiADC = None
        
        self.channels = channels
        self.VMax = VMax
        self.averageN = averageN
        
        self.setupADC()#initialises ADC. Note this should be done before starting the server!
        self.startServer()#starts a threaded server waiting for input commands
        
        self.startADC()#starts the serial connection to the synth

    def setupADC(self):
        self.rpiADC = rpiADC.RPiADC()
        self.rpiADC.setChannels(self.channels)         
        self.rpiADC.setVMax(self.VMax)         
        self.rpiADC.setAverageN(self.averageN)         
        
    def startServer(self):
        logger.debug("starting server")
        self.server = server.SocketServer(self.PORT,self.IP_ADDRESS)
        self.server.rpiADCReference = self.rpiADC#so that the server can access the results dictionary
        
    def startADC(self):
        logger.debug("starting ADC")
        
        self.rpiADC.start()
        
if __name__=="__main__":
    s=RPiADCServer(IP_ADDRESS=IP_ADDRESS)
    print "complete"

