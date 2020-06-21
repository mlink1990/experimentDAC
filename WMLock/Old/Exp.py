

from PyHWI import *


class expState():

    def __init__( self ):

        self.WLM = DECADSClientConnection( "WLM", "131.220.167.90", 6100, blocking=True )
        print "Wavemeter initialised."
        
        self.DAC = DECADSClientConnection( "DACBox", "131.220.167.105", 6100, blocking=True ) 
        print "DAC initialised."


    def close( self ):
        self.WLM.close()
        self.DAC.close()
        

    
