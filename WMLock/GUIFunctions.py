
from PyQt4 import QtGui, QtCore




############################
### createSocketPair creates a pair of sockets which are connected which 
### can be used to transfer information in a thread-safe way
############################

import socket
import threading


def createSocketPair():
    try:
        S1, S2 = socket.socketpair()
        return (S1, S2)
    except AttributeError:
        listenSocket = socket.socket()
        listenSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        listenSocket.bind( ('localhost', 0) )
        iface, ephport = listenSocket.getsockname()
        listenSocket.listen(1)

        S1 = socket.socket()
        
        def connectThreadExec( s, port ):
            s.connect( ('localhost', port) )
            
        cThread = threading.Thread( target=connectThreadExec, args=( S1, ephport) )
        cThread.daemon = True
        cThread.start()
        S2, S2Addr = listenSocket.accept()
        listenSocket.close()
        return (S1, S2)




############################
### signalConnector objects can be shared with standard python threads
### and will emit Qt signals in the Qt thread safely triggered
### by any other thread.  Must be initialised in the Qt main thread
############################

import Queue

    
class signalConnector:
    def __init__( self ):
        # Create a socket pair for signalling between the two threads
        self._rsock, self._wsock = createSocketPair()
        # A queue to store messages
        self._queue = Queue.Queue()
        # A QtObject to trigger Qt signals 
        self._qt_object = QtCore.QObject()
        # A notifier which will call self._recv() when there is data on the socket
        self._notifier = QtCore.QSocketNotifier( self._rsock.fileno(),
                                                 QtCore.QSocketNotifier.Read )
        self._notifier.activated.connect( self._recv )

    # Called in Qt main thread when there is data on the socket
    def _recv( self ):
        # Remove the "!" from the socket
        self._rsock.recv(1)
        # Get the information from the queue
        signal, args = self._queue.get()
        # Fire off the Qt Signal
        self._qt_object.emit( signal, args )

    # Called by the application in the Qt main thread to connect signals
    # from the QObject safely to the Qt main thread
    def connect( self, signal, receiver ):
        QtCore.QObject.connect( self._qt_object, signal, receiver )

    # Called by any thread to safely trigger the Qt signal in the main thread
    def emit( self, signalStr, args=None ):
        # Add the signal to the queue
        self._queue.put( (QtCore.SIGNAL( signalStr ), args) )
        # Send a byte on the socket to signal that we have added to the queue
        self._wsock.send("!")

    
