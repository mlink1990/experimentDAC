# experimentDAC
 This software controls an AD5754 evaluation board via network. The board is connected to a RPi which runs a server that can be accessed through the GUI. The GUI is modular, several functions (manual DAC, laser relock, wavemeter lock) are provided.


To start the wavemeterlock proceed as follows:

	1. Start the python script: auto_Relock-UI.py. The computer must be connected to the internal group network.

	2. Turn on the power of your selected Channel on the DAC, which is connected to the Piezo of your Laser.

	3. Change the voltage settings to +-10V (bipolar).

	4. Pick the right wavemeter from the drop down menu as well as the correct wavemeter channel number.

	5. By checking "Connect to wavemeter" the live laser frequency shall be visible in the GUI.

	6. Define a proper target frequency for the lock as well as an suitable gain (+- depends on laser) (+-1 is a good choice).

	7. Start lock :-)

Further information:

On the RaspberryPi, which is connected to the DAC, the ADEval_server.py is running. The script is listed in the autostart routine of the Pi.
