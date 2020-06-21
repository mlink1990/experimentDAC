# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 12:47:27 2015

@author: tharrison
"""

'''
    Simple socket server using threads
'''
 
import socket
import sys
import threading
import logging
import ADEval

IP_ADDRESS = '192.168.16.67'   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port

class SocketThreadConnection(threading.Thread):
    """Thread checking for connections from client. When one occurs it starts the 
    client thread"""
    def run(self):
        while True:
            #wait to accept a connection - blocking call
            conn, addr = self.socketServerReference.s.accept()#hangs until a connection is made!
            print 'Connected with ' + addr[0] + ':' + str(addr[1]) 
            #when a new connection is made  start a client thread for this connection
            clientThread = ClientThread()
            clientThread.conn = conn
            clientThread.socketServerReference = self.socketServerReference
            clientThread.start()
            
class ClientThread(threading.Thread):
    """defines what occurs when a command is received from client """
    def run(self):
        ADEval = self.socketServerReference.ADEvalReference # defines reference to rpi ADC device for results dict
        self.conn.send('1\n') #send only takes string
        #infinite loop so that function do not terminate and thread do not end.
        while True:
            #Receiving from client
            data = self.conn.recv(1024)
            print data
            if data[0:4] == "cmd=":
                inputData = data[4:28]
                print inputData
                print len(inputData)
                if len(inputData)!=24:
                    print "data not correct length. Will not send"
                else:
                    ADEval.send_input(inputData)
                    self.conn.send('1\n')
            elif data[0:4] == "pin=":
                inputData = data[4:6]
                ADEval.set_pin(inputData)
            else:
                print "Nope"
            #===================================================================
            # if len(data)==0:
            #     break
            # if data == "?\n":
            #     logger.info("results requested")
            #     returnValue = str(rpiADC.results)+"\n"
            #     self.conn.send(returnValue)
            # elif data[0:3]=="ch=":
            #     channels = data[3:-1].split(",")
            #     rpiADC.setChannels(channels)
            #     self.conn.send('1\n')
            # elif data[0:2]=="V=":
            #     V = float(data[2:-1])
            #     rpiADC.setVMax(V)
            #     self.conn.send('1\n')
            # elif data[0:2]=="N=":
            #     averageN = int(data[2:-1])
            #     rpiADC.setAverageN(averageN)
            #     self.conn.send('1\n')
            # else:
            #     self.conn.send('0\n')
            #===================================================================
        #came out of loop
        self.conn.close()

class SocketServer:
    """Socket server. adaption of general socket server. Commands and their
    return properties are defined in client Thread"""
    def __init__(self, PORT=PORT, IP_ADDRESS = IP_ADDRESS):
        self.commandsList = [] #FIFO list of commands to execute when triggered
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Bind socket to local host and port
        try:
            #allows socket to instantly be reused
            #see: http://stackoverflow.com/questions/5875177/how-to-close-a-socket-left-open-by-a-killed-program
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #means that when killed we can run again straight away
            self.s.bind((IP_ADDRESS, PORT))
        except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
             
        #logger.debug( 'Socket bind complete')
        #Start listening on socket
        self.s.listen(10)
        #logger.debug('Socket now listening')
        
        self.socketThreadConnection = SocketThreadConnection()
        self.socketThreadConnection.socketServerReference = self
        #now keep talking with the client
        self.socketThreadConnection.start()
        
    def close(self):
        self.s.close()
        
    def __del__(self):
        self.close()
        
    def clearCommandQueue(self):
        self.commandsList = [] #FIFO list of commands to execute when triggered
