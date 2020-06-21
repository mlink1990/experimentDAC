

import Exp
import WMLock

import time

state = Exp.expState()

WMLock399 = WMLock.WMLock( state, 1, 1, 751.526321 )

WMLock399.voltage.value = 5.0

for i in range( 0, 10 ):
    time.sleep(1)

    WMLock399.update()

WMLock399.findMFR()

while(1):

    time.sleep(1)

    WMLock399.update()    
