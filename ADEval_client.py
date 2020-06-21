'''
Created on 14 Dec 2015

@author: Martin
'''

import socket
#import ast
#import logging

class Connection:
    """provides a wrapper to all the socket calls so that you can communicate
    with rpiADC over the network. """
    
    def __init__(self, port=8888, IP_ADDRESS = "192.168.16.67"):
        self.PORT = port
        self.bufferSize = 1024
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 5.0 #seconds
        self.latestResults = {}
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        print "attempting to connect to {} port {}".format(self.IP_ADDRESS, self.PORT)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        print "connected socket, waiting to receive"
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
        try:        
            # Python wrapper for sending command to controller.
            #logger.debug("sending command: %s" % commandString)
            print "Sending command: %s" %commandString        
            #commandString += '\n'        
            self.socket.sendall(commandString)
            #time.sleep(0.1)
        except:
            self.socket.close()

    def sendwithoutcomment(self, commandString):
        try:        
            # Python wrapper for sending command to controller.
            #logger.debug("sending command: %s" % commandString)
            #print "Sending command: %s" %commandString        
            #commandString += '\n'        
            self.socket.sendall(commandString)
            #time.sleep(0.1)
        except:
            self.socket.close()

    def receive(self):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(self.bufferSize)
        #print "aze"
        return data
            
if __name__=="__main__":
    conn = Connection(IP_ADDRESS="192.168.16.67")
