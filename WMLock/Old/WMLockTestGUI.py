

import Exp
import WMLock

import time

import sys
from PyQt4 import QtGui

class mainWindow( QtGui.QWidget ):
    
    def __init__( self, lock ):
        super( mainWindow, self ).__init__()

        self.lock = lock
        
        self.initUI()
        
    def initUI(self):
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('WMLockTestGUI')
               
        self.buttonStart = QtGui.QPushButton( 'Start Lock', self)
        self.buttonStart.clicked.connect( self.lock.start )
        self.buttonStart.move( 5,5 )
        
        self.buttonStop = QtGui.QPushButton( 'Stop Lock', self)
        self.buttonStop.clicked.connect( self.lock.stop )
        self.buttonStop.move( 5,30 )

        self.buttonMFR = QtGui.QPushButton( 'Find MFR', self)
        self.buttonMFR.clicked.connect( self.lock.findMFR )
        self.buttonMFR.move( 5,55 )

        self.buttonStart = QtGui.QPushButton( 'Start Jumping Lock', self)
        self.buttonStart.clicked.connect( self.lock.jumpingStart )
        self.buttonStart.move( 105, 5 )

        self.editFrequency = QtGui.QLineEdit( self )
        self.editFrequency.move( 105, 30 )
        self.editFrequency.setText( str(self.lock.targetFrequency) )
        self.editFrequency.returnPressed.connect( self.changeFrequency )
        
    
        self.show()

    def changeFrequency( self ):
        # Called when the user changes the frequency text field
        text = self.editFrequency.text()

        try:
            newFrequency = float(text)
        except ValueError:
            print "Frequency not a number: %r" % text
            self.editFrequency.setText( str(self.lock.targetFrequency) )
            return

        
        self.lock.targetFrequency = newFrequency
        

def main():

    state = Exp.expState()

    #WMLock399 = WMLock.WMLock( state, 2, 0, 320.571965 )
    WMLock399 = WMLock.WMLock( state, 1, 1, 751.52644 )
    #WMLock399 = WMLock.WMLock( state, 3, 2, 811.291409 )

    
    application = QtGui.QApplication( sys.argv )

    mw = mainWindow( WMLock399 )


    sys.exit( application.exec_() )



if __name__ == '__main__':
    main()



for i in range( 0, 10 ):
    time.sleep(1)

    WMLock399.update()

WMLock399.findMFR()

while(1):

    time.sleep(1)

    WMLock399.update()    
