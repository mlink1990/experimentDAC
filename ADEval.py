import spidev
import RPi.GPIO as GPIO
import time
import threading

#===============================================================================
# class ADEvalListening(threading.Thread):
#     def run(self):
#         while True:
#             self.ADEvalReference.results = self.ADEvalReference.getResults()
#===============================================================================

class ADEval():
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz = 1000000  #1MHz
        self.spi.bits_per_word = 8

        #setup LDAC and SYNC pins
        self.LDAC = 11
        self.SYNC = 13
        self.LOCKA = 29
        self.LOCKB = 31
        self.LOCKC = 33
        self.LOCKD = 37
        GPIO.setup(self.LDAC, GPIO.OUT) #LDAC
        GPIO.setup(self.SYNC, GPIO.OUT) #SYNC
        GPIO.setup(self.LOCKA, GPIO.OUT)
        GPIO.setup(self.LOCKB, GPIO.OUT)
        GPIO.setup(self.LOCKC, GPIO.OUT)
        GPIO.setup(self.LOCKD, GPIO.OUT)

        GPIO.output(self.LDAC, GPIO.LOW) #LDAC low by default for individual DAC update
        GPIO.output(self.SYNC, GPIO.LOW) #SYNC low
        GPIO.output(self.LOCKA, GPIO.LOW)
        GPIO.output(self.LOCKB, GPIO.LOW)
        GPIO.output(self.LOCKC, GPIO.LOW)
        GPIO.output(self.LOCKD, GPIO.LOW)
        print 'Initialization succesful'


    def bth( self, a ): #transfers bitstring to integer numbers
        return int(a ,2)
        
    def send_input( self, inputData ):
        print "sending input to DAC--> %s" % (inputData)
        b = self.spi.xfer2([ self.bth(inputData[0:8]), self.bth( inputData[8:16] ), self.bth ( inputData[16:24] ) ])
        print "output--> %s" % b 
        time.sleep(0.001)
        GPIO.output(self.SYNC, GPIO.HIGH)
        GPIO.output(self.SYNC, GPIO.LOW) #SYNC low
        return b
        
        
    def set_pin(self, inputData):
        if inputData[0] == 'A':
            if inputData[1] == '1':
                GPIO.output(self.LOCKA, GPIO.HIGH)
            else:
                GPIO.output(self.LOCKA, GPIO.LOW)
        elif inputData[0] == 'B':
            if inputData[1] == '1':
                GPIO.output(self.LOCKB, GPIO.HIGH)
            else:
                GPIO.output(self.LOCKB, GPIO.LOW)
        elif inputData[0] == 'D':
            if inputData[1] == '1':
                GPIO.output(self.LOCKC, GPIO.HIGH)
            else:
                GPIO.output(self.LOCKC, GPIO.LOW)
        else:
            if inputData[1] == '1':
                GPIO.output(self.LOCKD, GPIO.HIGH)
            else:
                GPIO.output(self.LOCKD, GPIO.LOW)
            
    
    #===========================================================================
    # def start(self):
    #     measurementThread = ADEvalListening()
    #     measurementThread.ADEvalReference = self
    #     measurementThread.start()
    #===========================================================================
    
if __name__=="__main__":
    ad =ADEval()
    import AD5754_BCgen
    bc = AD5754_BCgen.ADEvalBC()
    inputString=bc.turnOnAllDACs()
    ad.send_input(inputString)
    inputString=bc.generate_voltage("A", 5,0,1)
    ad.send_input(inputString)
    inputString=bc.generate_voltage("B", 5,0,2)
    ad.send_input(inputString)
    inputString=bc.generate_voltage("C", 5,0,3)
    ad.send_input(inputString)
    inputString=bc.generate_voltage("D", 5,0,4)
    ad.send_input(inputString)
    GPIO.cleanup()