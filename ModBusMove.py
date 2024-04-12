import time
import math
import warnings
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

## variables ###
totalDistance = 5  #type float (mm)
intervals = 5      #type int

if intervals <= 0:
    intervals = 1

intcopy = intervals #just a copy for a while loop

timeatpoint = 3 #in seconds

speed = 200 #rpm
accel = 3000 #rpm/s

################

#####CONTS######

MOVEPERINCH = 34376.0743 #in pul/mm, rough estamate

################

totalDistanceM = totalDistance/(10^3) #mm to m
dispint = totalDistanceM/intervals


totalDistanceP = totalDistance * MOVEPERINCH #converts mm to pul
dispint = totalDistanceP/intervals #pul to pul/interval

# init modbus client
c = ModbusClient(host='169.254.246.100', port=5000)
c.connect()


#configure servo

#used to encode data in 32 bit big endian format for servo
builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)

c.write_coils(5, [False]) #blue led off
c.write_coils(4, [True]) #green led on

#note for coils like 13, which are Pos Transition coils
#they are only activated by the transition from 0 to 1
#not 1 to 0. So I set to 0 then 1 to make sure they weren't
#already activated beforehand
c.write_coils(13, [False]) 
c.write_coils(13, [True]) #clear errors (if any)



payloadunbuilt = [speed, accel, 10000, 1, 2]
addresses = [2, 4, 6, 8, 10]

#in order, these addresses corrispond to:
#target speed, target acceleration, target jerk, move pattern, homing mode

for i in range(len(payloadunbuilt)):
    builder.add_32bit_int(int(payloadunbuilt[i]))
    payload = builder.build()
    c.write_registers(int(addresses[i]), payload, skip_encode=True, unit=0)
    builder.reset()

time.sleep(3)

c.write_coils(5, [True]) #blue led on
c.write_coils(4, [False]) #green led off

c.write_coils(7, [False]) 
c.write_coils(7, [True]) #turn servo on

c.write_coils(11, [False])
c.write_coils(11, [True]) #jog in minus direction

time.sleep(2)

#read the speed
result = c.read_holding_registers(2, 2) #speed register
decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
speedch = decoder.decode_32bit_int()
print("Current Soeed: {}".format(speedch))

if speedch > -(.9*speed):
    warnings.warn("Speed is lower than expected!")
elif speedch < -(1.1*speed):
    warnings.warn("Speed is higher than expected!")


time.sleep(1)
c.write_coils(14, [False])
c.write_coils(14, [True]) #stop all motion

time.sleep(1)
c.write_coils(12, [False])
c.write_coils(12, [True]) #homes the motor until limit switch is hit

time.sleep(8)
builder.add_32bit_int(0)
payload = builder.build()
c.write_registers(14, payload, skip_encode=True, unit=0) #sets the position to 0
builder.reset()


while intcopy > 0:
    
    moveto = -((intervals % intcopy) + 1)*dispint #thanks modern physics for being boring enough for me to figure this out
    moveto = int(math.floor(moveto))


    builder.add_32bit_int(moveto)
    payload = builder.build()

    c.write_registers(0, payload, skip_encode=1, unit=1) #set move target

    builder.reset()
    
    c.write_coils(9, [False])
    c.write_coils(9, [True]) #begin movement
    time.sleep(2) #buffer to allow the motor to move based on kinematics

    print("AT POSITION {}!".format((intervals % intcopy) + 1))
    time.sleep(timeatpoint)

    c.write_coils(14, [False])
    c.write_coils(14, [True]) #stop movement incase it is still going

    result = c.read_holding_registers(0, 2) #position register
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    posch = decoder.decode_32bit_int()
    if posch != moveto:
        warnings.warn("Actual position isn't lined up with set position!")
    
    intcopy = intcopy - 1



c.write_coils(8, [False])
c.write_coils(8, [True]) #turn off motor



c.close()