
import PyHWI
import os
import sys


from PyQt4 import QtCore, QtGui

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString as MDParseString

# The maximum acceptable error in GHz to stay in lock
MAX_ERROR = 5

# GUI and lock update time in ms
UPDATETIME_GUI = 200
UPDATETIME_LOCK = 1000

INDEX_NAME = 0
INDEX_SETPOINT = 1
INDEX_FREQUENCY = 2
INDEX_GAIN = 3
INDEX_VOLTAGE = 4
INDEX_LOCKED = 5

class lockChannel():

    def __init__( self, lockElement ):

        self.name = str(lockElement.find('name').text)

        self.DACAlias = str(lockElement.find('DAC').get('alias'))
        self.DACChannel = int(str(lockElement.find('DAC').get('channel')))

        self.WLMAlias = str(lockElement.find('WLM').get('alias'))
        self.WLMChannel = int(str(lockElement.find('WLM').get('channel')))

        self.gain = float(lockElement.find('gain').text)
        self.voltage = float(lockElement.find('voltage').text)

        self.setpoint = float(lockElement.find('setpoint').text)

        self.frequency = 0

        self.locked = False

    def getElement( self ):

        lockElement = ET.Element( 'lockChannel' )

        nameElement = ET.Element( 'name' )
        nameElement.text = str(self.name)
        lockElement.append( nameElement )
        
        DACElement = ET.Element( 'DAC' )
        DACElement.set('alias', str(self.DACAlias))
        DACElement.set('channel', str(self.DACChannel))
        lockElement.append( DACElement )

        WLMElement = ET.Element( 'WLM' )
        WLMElement.set('alias', str(self.WLMAlias))
        WLMElement.set('channel', str(self.WLMChannel))
        lockElement.append( WLMElement )

        gainElement = ET.Element( 'gain' )
        gainElement.text = str(self.gain)
        lockElement.append( gainElement )

        voltageElement = ET.Element( 'voltage' )
        voltageElement.text = str(self.voltage)
        lockElement.append( voltageElement )

        setpointElement = ET.Element( 'setpoint' )
        setpointElement.text = str(self.setpoint)
        lockElement.append( setpointElement )

        return lockElement

    


class WMLockGUI():

    def __init__( self, configFile ):

        self.configFile = configFile

        self.HWIAliases = []
        self.HWIConnections = []

        self.lockChannels = []

        try:
            configTree = ET.parse( configFile )
            self.configRoot = configTree.getroot()

        except IOError:
            print 'Config file does not exist, creating blank config'
            self.configRoot = ET.Element( 'WMLockGUIConfig' )

        self.app = QtGui.QApplication( [""] )
        self.MW = QtGui.QMainWindow()
        self.app.setActiveWindow( self.MW )
        self.MW.setWindowIcon( QtGui.QIcon('unlock.png' ) )
        
        # Create GUI
        self.createGUI()

        self.MW.show()

        # Create update timer for GUI
        self.GUIUpdateTimer = QtCore.QTimer( self.MW )
        self.GUIUpdateTimer.setInterval( UPDATETIME_GUI )
        self.GUIUpdateTimer.timeout.connect( self.updateGUI )
        self.GUIUpdateTimer.start()

        # Create update timer for locks
        self.LockUpdateTimer = QtCore.QTimer( self.MW )
        self.LockUpdateTimer.setInterval( UPDATETIME_LOCK )
        self.LockUpdateTimer.timeout.connect( self.updateLocks )
        self.LockUpdateTimer.start()

        #self.MW.closeEvent = self.quit 
        
        self.app.exec_()

        # Clear up
        self.GUIUpdateTimer.stop()
        self.LockUpdateTimer.stop()
        
        # Save the config
        self.saveConfig()


    def createGUI( self ):


        ## Window Name
        nameElement = self.configRoot.find( 'name' )
        if nameElement is None:
            self.name = 'WMLockGUI_V2'
        else:
            self.name = str(nameElement.text)

        self.MW.setWindowTitle( self.name + ' - WMLockGUI' )


        ## Window geometry
        geometryElement = self.configRoot.find( 'windowGeometry' )
        if geometryElement is None:
            width = 800
            height = 600
            x = 0
            y = 0
        else:
            width = geometryElement.get( 'width' )
            height = geometryElement.get( 'height' )
            x = geometryElement.get( 'x' )
            y = geometryElement.get( 'y' )

        self.MW.resize( int(width), int(height) )
        self.MW.move( int(x), int(y) )

        ##
        self.MWFrame = QtGui.QWidget( self.MW )
        self.channelWidget = QtGui.QWidget( self.MW )
        self.connectionWidget = QtGui.QWidget( self.MW )
        self.MWLayout = QtGui.QVBoxLayout()
        self.MWFrame.setLayout( self.MWLayout )
        
        self.MWLayout.addWidget( self.channelWidget )
        self.MWLayout.addWidget( self.connectionWidget )
        self.channelLayout = QtGui.QGridLayout()
        self.channelWidget.setLayout( self.channelLayout )


        self.MW.setCentralWidget( self.MWFrame )

        ## Lock channels
        lockElements = self.configRoot.findall( 'lockChannel' )

        # Add labels for lock channels
        self.channelLayout.addWidget( QtGui.QLabel( 'Laser', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_NAME )
        self.channelLayout.addWidget( QtGui.QLabel( 'Target Frequency (THz)', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_SETPOINT )
        self.channelLayout.addWidget( QtGui.QLabel( 'Current Frequency (THz)', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_FREQUENCY )
        self.channelLayout.addWidget( QtGui.QLabel( 'Feedback Gain (V/GHz)', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_GAIN )
        self.channelLayout.addWidget( QtGui.QLabel( 'Voltage (V)', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_VOLTAGE )
        self.channelLayout.addWidget( QtGui.QLabel( 'Lock', alignment=QtCore.Qt.AlignCenter ), 0, INDEX_LOCKED )

        for i in range( len(lockElements) ):
            self.createLockGUI( lockElements[i] )

        ## Add the menus
        self.menu = self.MW.menuBar()
        
        self.fileMenu = self.menu.addMenu( '&File' )
        self.fileMenu.addAction( '&Quit', self.MW.close )
     
        self.connectionMenu = self.menu.addMenu( '&Connections' )
        for alias in self.HWIAliases:
            action = QtGui.QAction( alias, self.connectionMenu, checkable=True )
            action.triggered.connect( lambda checked, a=alias: self.connectClicked( a, checked ) )
            self.connectionMenu.addAction( action )

            self.connect( alias )
        
    def createLockGUI( self, lockElement ):

        thisChannel = lockChannel( lockElement )
        thisRow = self.channelLayout.rowCount()

        self.lockChannels.append( thisChannel )

        if thisChannel.DACAlias not in self.HWIAliases:
            self.HWIAliases.append( thisChannel.DACAlias )
            self.HWIConnections.append( None )

        if thisChannel.WLMAlias not in self.HWIAliases:
            self.HWIAliases.append( thisChannel.WLMAlias )
            self.HWIConnections.append( None )

        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)

        nameLabel = QtGui.QLabel()
        nameLabel.setText( thisChannel.name )
        nameLabel.setFont( font )

        setpointBox = QtGui.QDoubleSpinBox()
        setpointBox.setMinimum( 0 )
        setpointBox.setMaximum( 1000 )
        setpointBox.setDecimals( 6 )
        setpointBox.setSingleStep( 1e-5 )
        setpointBox.setValue( thisChannel.setpoint )
        setpointBox.valueChanged.connect( lambda newValue: setattr( thisChannel, 'setpoint', newValue ) )


        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        
        frequencyBox = QtGui.QLineEdit( alignment=QtCore.Qt.AlignCenter )
        frequencyBox.setEnabled( True )
        frequencyBox.setReadOnly( False )
        frequencyBox.setText( '-' )
        frequencyBox.setFont( font )

        gainBox = QtGui.QDoubleSpinBox()
        gainBox.setMinimum( -999999 )
        gainBox.setMaximum( 999999 )
        gainBox.setDecimals( 2 )
        gainBox.setSingleStep( 1e-2 )
        gainBox.setValue( thisChannel.gain )
        gainBox.valueChanged.connect( lambda newValue: setattr( thisChannel, 'gain', newValue ) )
        
        voltageBox = QtGui.QDoubleSpinBox()
        voltageBox.setMinimum( -10 )
        voltageBox.setMaximum( 10 )
        voltageBox.setDecimals( 3 )
        voltageBox.setSingleStep( 1e-2 )
        voltageBox.setValue( thisChannel.voltage )
        voltageBox.valueChanged.connect( lambda newValue: self.setVoltageFromGUI( thisChannel, newValue ) )


        lockBox = QtGui.QCheckBox()
        lockBox.setChecked( thisChannel.locked )
        lockBox.clicked.connect( lambda newState: setattr( thisChannel, 'locked', newState ) )

        self.channelLayout.addWidget( nameLabel, thisRow, 0 )
        self.channelLayout.addWidget( setpointBox, thisRow, INDEX_SETPOINT )
        self.channelLayout.addWidget( frequencyBox, thisRow, INDEX_FREQUENCY )
        self.channelLayout.addWidget( gainBox, thisRow, INDEX_GAIN )
        self.channelLayout.addWidget( voltageBox, thisRow, INDEX_VOLTAGE )
        self.channelLayout.addWidget( lockBox, thisRow, INDEX_LOCKED )
        

    def saveConfig( self ):
        # Create new config
        self.configRoot = ET.Element( 'WMLockGUIConfig' )

        nameElement = ET.Element( 'name' )
        nameElement.text = self.name
        self.configRoot.append( nameElement )
        

        # Save the window geometry
        geometryElement = ET.Element( 'windowGeometry' )
        geometryElement.set( 'width', str(self.MW.geometry().width()) )
        geometryElement.set( 'height', str(self.MW.geometry().height()) )
        geometryElement.set( 'x', str(self.MW.x()) )
        geometryElement.set( 'y', str(self.MW.y()) )        
        self.configRoot.append( geometryElement )


        # Save all the lock channels
        for i in range( len(self.lockChannels) ):
            lockElement = self.lockChannels[i].getElement()
            self.configRoot.append( lockElement )


        
        # Now all the elements are added, we need to save
        configTree = ET.ElementTree()
        configTree._setroot( self.configRoot )

        # Pretty print
        dataString = ET.tostring( self.configRoot )
        # Strip any newlines from the XML
        dataString = dataString.replace( '\n', '' )
        # String any tabs from the XML
        dataString = dataString.replace( '\t', '' )

        xmlOutput = MDParseString( dataString ).toprettyxml() 

        f = open( self.configFile, 'w' )  
        f.write( xmlOutput )
        f.close()

    def updateGUI( self ):

        for i in range( len(self.HWIAliases) ):

            if self.HWIConnections[i] is not None and\
               self.HWIConnections[i].connected is True and \
               self.HWIConnections[i].functionListInitialised is True:
                self.connectionMenu.actions()[i].setChecked( True )
            else:
                self.connectionMenu.actions()[i].setChecked( False )

        for i in range(len(self.lockChannels)):

            channel = self.lockChannels[i]

            if channel.frequency == 0:
                frequencyStr = '-'
            elif channel.frequency == -3:
                frequencyStr = 'Underexposed'
            elif channel.frequency == -4:
                frequencyStr = 'Overexposed'
            else:
                frequencyStr = '%.6f' % (channel.frequency)
                
            self.channelLayout.itemAtPosition( i+1, INDEX_FREQUENCY ).widget().setText( frequencyStr )

            self.channelLayout.itemAtPosition( i+1, INDEX_VOLTAGE ).widget().blockSignals( True )
            self.channelLayout.itemAtPosition( i+1, INDEX_VOLTAGE ).widget().setValue( channel.voltage )
            self.channelLayout.itemAtPosition( i+1, INDEX_VOLTAGE ).widget().blockSignals( False )

            self.channelLayout.itemAtPosition( i+1, INDEX_LOCKED ).widget().setChecked( channel.locked )
            
            

    def updateLocks( self ):

        for channel in self.lockChannels:

            WLMIndex = self.HWIAliases.index( channel.WLMAlias )
            DACIndex = self.HWIAliases.index( channel.DACAlias )

            if self.HWIConnections[WLMIndex] is None or\
               self.HWIConnections[WLMIndex].connected is False or\
               self.HWIConnections[WLMIndex].functionListInitialised is False:
                channel.locked = False
                continue
            else:
                channel.frequency = self.HWIConnections[WLMIndex].getFrequency( True, channel.WLMChannel )[1]

            if self.HWIConnections[DACIndex] is None or\
               self.HWIConnections[DACIndex].connected is False or\
               self.HWIConnections[DACIndex].functionListInitialised is False:
                channel.locked = False
                continue

            if channel.locked:
                # Calculate error in GHz
                error = (channel.frequency - channel.setpoint)*10**3
                if abs( error ) < MAX_ERROR:
                    channel.voltage += error*channel.gain

                    if channel.voltage > 10:
                        channel.voltage = 10
                    elif channel.voltage < -10:
                        channel.voltage = -10

                    self.HWIConnections[DACIndex].setDACSingle( False, channel.DACChannel, channel.voltage )
                    print error, channel.voltage
                    


    def setVoltageFromGUI( self, channel, newVoltage ):
        
        channel.voltage = newVoltage
        DACIndex = self.HWIAliases.index( channel.DACAlias )
        self.HWIConnections[DACIndex].setDACSingle( False, channel.DACChannel, channel.voltage )

    def connectClicked( self, alias, checked ):

        if checked is False:
            self.disconnect( alias )
        else:
            self.connect( alias )


    # Connect to HWI
    def connect( self, alias ):

        i = self.HWIAliases.index( alias )

        if self.HWIConnections[i] is not None:
            self.HWIConnections[i].close()

        self.HWIConnections[i] = PyHWI.DECADSClientConnection( alias, blocking=False )
        
    def disconnect( self, alias ):
        i = self.HWIAliases.index( alias )

        if self.HWIConnections[i] is not None:
            self.HWIConnections[i].close()
            self.HWIConnections[i] = None

    def quit( self, value ):
        self.GUIUpdateTimer.stop()
        self.LockUpdateTimer.stop()
        
        # Save the config
        self.saveConfig()
            



if __name__ == '__main__':

    # If we are running windows, change the appUserModelID so the windows does not group us with
    # other python programs
    if os.name == 'nt':
        import ctypes
        AppID = 'AQO.WMLock_V2' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID( AppID )
#####debug
    filename="UVC_174.xml"
    WMLockGUI( filename )
#####
    
    #WMLockGUI( sys.argv[1] )

        


        
