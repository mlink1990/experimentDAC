# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 10:42:27 2015

@author: tharrison
"""

import socket
import logging
import ast#used for safe evaluation of returned strings

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreakClient")
   
class Connection:
    """provides a wrapper to all the socket calls so that you can communicate
    with rpiADC over the network. """
    
    def __init__(self, port=8888, IP_ADDRESS = "192.168.16.28"):
        self.PORT = port
        self.bufferSize = 1024
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 5.0 #seconds
        self.latestResults = {}
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        return self.receive()
        #time.sleep(0.1)
        
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        self.socket.close()
        
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        # Python wrapper for sending command to controller.
        logger.debug("sending command: %s" % commandString)        
        commandString += '\n'        
        self.socket.sendall(commandString)
        #time.sleep(0.1)

    def receive(self):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(self.bufferSize)
        return data
        
    def getResults(self):
        """wrapper for producing the commandString for interepret  """
        cmd = "?"
        self.send(cmd)
        returnValue = self.receive()
        #returned string is python string dictionary
        #use literal eval to safely return the dictionary
        #update latest results
        self.latestResults = ast.literal_eval(returnValue)
        return self.latestResults
        
    def setChannels(self, channels):
        cmd = "ch=%s" % channels
        self.send(cmd)
        return self.receive()
        
    def setVMax(self, VMax):
        cmd = "V=%s" % VMax
        self.send(cmd)
        return self.receive()
        
    def setAverageN(self, averageN):
        cmd = "N=%s" % averageN
        self.send(cmd)
        return self.receive()
            
if __name__=="__main__":
    conn = Connection(IP_ADDRESS="192.168.16.28")
    