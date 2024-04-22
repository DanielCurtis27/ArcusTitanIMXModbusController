import time
import math
import sys
import warnings
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

## variables ###
totalDistance = 5  #type float (mm)
intervals = 10      #type int

if intervals <= 0:
    intervals = 1
if totalDistance < 0:
    totalDistance = totalDistance * -1

intcopy = intervals #just a copy for a while loop

speed = 200 #rpm
accel = 8000 #rpm/s

################

#####CONTS######

MOVEPERMM = 34376.0743 #in pul/mm, rough estamate

################

totalDistanceP = totalDistance * MOVEPERMM #converts mm to pul
dispint = totalDistanceP/intervals #pul to pul/interval

# init modbus client
c = ModbusClient(host='169.254.246.100', port=5000)
c.connect()

#configure servo

#used to encode data in 32 bit big endian format for servo
builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)

def DigInput_wait(register, bit1, bit2):
    i = 0
    while i==0:
        Dinputs = c.read_holding_registers(register, 2)
        decoder = BinaryPayloadDecoder.fromRegisters(Dinputs.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
        bits = int(decoder.decode_32bit_int())
        #replace this to check the actual bit instead of decimal value, python makes this hard because it hates leading 0's
        #print(bits)
        if bits == bit1 or bits==bit2: #this corresponds to the motor being on, in position, and homed
            i = 1
        time.sleep(.25)
def Check_registers(register):
    result = c.read_holding_registers(register, 2)
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    return decoder.decode_32bit_int()
def Write_registers(register, value):
    builder.add_32bit_int(value)
    payload = builder.build()
    c.write_registers(register, payload, skip_encode=True, unit=0)
    builder.reset()



c.write_coils(5, [False]) #blue led off
c.write_coils(4, [True]) #green led on

#note for coils like 13, which are Pos Transition coils
#they are only activated by the transition from 0 to 1
#not 1 to 0. So I set to 0 then 1 to make sure they weren't
#already activated beforehand
c.write_coils(13, [False]) 
c.write_coils(13, [True]) #clear errors (if any)


payloadunbuilt = [speed, accel, 10000, 1, 0]
addresses = [2, 4, 6, 8, 10]

#in order, these addresses corrispond to:
#target speed, target acceleration, target jerk, move pattern, homing mode

for i in range(len(payloadunbuilt)): #encodes and sends the data to the motor
    Write_registers(int(addresses[i]), int(payloadunbuilt[i]))
    time.sleep(.1)

time.sleep(3)

c.write_coils(5, [True]) #blue led on
c.write_coils(4, [False]) #green led off

c.write_coils(7, [False]) 
c.write_coils(7, [True]) #turn servo on


##### This can be commented out, it's just for testing to make sure the code is working #####
c.write_coils(11, [False])
c.write_coils(11, [True]) #jog in minus direction

time.sleep(1)

#read the speed
speedch = Check_registers(2)
print("Current Speed: {}".format(speedch))

if speedch > -(.9*speed):
    warnings.warn("Speed is lower than expected!")
elif speedch < -(1.1*speed):
    warnings.warn("Speed is higher than expected!")

time.sleep(.25)
#############################################################################################

c.write_coils(14, [False])
c.write_coils(14, [True]) #stop all motion

print("homing")
time.sleep(1.5)
c.write_coils(12, [False])
c.write_coils(12, [True]) #homes the motor until limit switch is hit

DigInput_wait(10, 19, 23) #halts program until motor is homed

c.write_coils(14, [False])
c.write_coils(14, [True]) #stop all motion

time.sleep(1.5)
Write_registers(14, 0) #sets position to 0
time.sleep(.5)
print(f"pos: {Check_registers(0)}")
time.sleep(1)

err = []
while intcopy > 0:
    
    moveto = -(((20000000+intervals) % (20000000+intcopy)) + 1)*dispint #thanks modern physics for being boring enough for me to figure this out
    moveto = int(math.floor(moveto))
    print(f"moveto: {moveto}")
    Write_registers(0, moveto) #sets target position to moveto
    
    c.write_coils(9, [False])
    c.write_coils(9, [True]) #begin movement

    c.write_coils(0, [True]) #digital output 1 to high to denote moving
    
    time.sleep(.25)
    DigInput_wait(10, 19, 23) #waits until movement is done

    currentPos = Check_registers(0)
    print(f"set distance: {-moveto/MOVEPERMM} mm")
    print(f"actual distance: {-currentPos/MOVEPERMM} mm")
    print(f"percent error: {abs((-moveto/MOVEPERMM - (-currentPos/MOVEPERMM))/(-currentPos/MOVEPERMM) * 100)} %")
    err.append(abs((-moveto/MOVEPERMM - (-currentPos/MOVEPERMM))/(-currentPos/MOVEPERMM) * 100))

    if currentPos > .9*moveto or currentPos < 1.1*moveto:
        warnings.warn("Current position is not at target position!")


    c.write_coils(0, [False]) #digital output 1 to low to denote movement complete

    print("AT POSITION {}!".format(((20000000+intervals) % (20000000+intcopy)) + 1))

    
    #checks digital input 5 to see if signal for completed measurement is sent (not working currently)
    #i = 0
    #while i==0:
    #    input5 = c.read_input_registers(0, 8) #inputs
    #    decoder = BinaryPayloadDecoder.fromRegisters(input5.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    #    bits = int(decoder.decode_32bit_int())
    #
    #    if bits == 16 or bits == 80 or bits == 48: #if digital input 5 is tripped (48 and 80 are for if it is at a limit switch and input 5 is tripped)
    #        i = 1

    c.write_coils(14, [False])
    c.write_coils(14, [True]) #stop movement incase it is still going

    time.sleep(.5) #replace this with the digital input 5 stuff

    
    
    intcopy = intcopy - 1

averageerror = sum(err)/len(err)

print(f"average error: {averageerror} %")

c.write_coils(8, [False])
c.write_coils(8, [True]) #turn off motor



c.close()