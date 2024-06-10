from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
import time
import math


clist = [0] * 100

class Probes:
    def __init__(self, ID, IP, InsertRadius, MOVEPERMM):
        self.id = ID #this will be posted on the side of the motors (ID 5 is the one currently on SABER)
        self.ip = IP
        self.r = InsertRadius #for the soft limit of the motor, more like an "outsert radius"
        self.MOVEPERMM = MOVEPERMM

        global clist
        clist[int(self.id) - 1] = ModbusClient(host=self.ip, port=5000)


#c = ModbusClient(host="x", port=5000) #dummy value for initializing c as a ModbusClient

builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)

def ConnectandInitializeProbe(probe: Probes):
    
    c = clist[int(probe.id)-1]
    c.connect()
    
    #global c
    #c = ModbusClient(host=probe.ip, port=5000)
    #c.connect()
    #note for coils like 13, which are Pos Transition coils
    #they are only activated by the transition from 0 to 1
    #not 1 to 0. So I set to 0 then 1 to make sure they weren't
    #already activated beforehand
    c.write_coils(13, [False]) 
    c.write_coils(13, [True]) #clear errors (if any)


    speed = 200 #rpm
    accel = 8000 #rpm/s

    payloadunbuilt = [speed, accel, 10000, 1, 0]
    addresses = [2, 4, 6, 8, 10]

    #in order, these addresses corrispond to:
    #target speed, target acceleration, target jerk, move pattern, homing mode

    for i in range(len(payloadunbuilt)): #encodes and sends the data to the motor
        Write_registers(probe, int(addresses[i]), int(payloadunbuilt[i]))
        time.sleep(.1)

    c.write_coils(7, [False]) 
    c.write_coils(7, [True]) #turn servo on
 
def Home(probe: Probes):
    c = clist[int(probe.id)-1]

    c.write_coils(14, [False])
    c.write_coils(14, [True]) #stop all motion

    print("homing")
    time.sleep(1.5)
    c.write_coils(12, [False])
    c.write_coils(12, [True]) #homes the motor until limit switch is hit

    DigInput_wait(probe, 10, 19, 23) #halts program until motor is homed

    c.write_coils(14, [False])
    c.write_coils(14, [True]) #stop all motion

    time.sleep(1.5)
    Write_registers(probe, 14, 0) #sets position to 0
    time.sleep(.5)
    print(f"pos: {Check_registers(probe, 0)}")
    time.sleep(1)

def Disconnect(probe: Probes): #run this before connecting to a new probe
    
    c = clist[int(probe.id)-1]

    c.write_coils(8, [False])
    c.write_coils(8, [True]) #turn off motor

    c.close() #close the connection

def DigInput_wait(probe: Probes, register, bit1, bit2):
    c = clist[int(probe.id)-1]
    
    i = 0
    while i==0:
        Dinputs = c.read_holding_registers(register, 2)
        decoder = BinaryPayloadDecoder.fromRegisters(Dinputs.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
        bits = int(decoder.decode_32bit_int())
        #replace this to check the actual bit instead of decimal value, python makes this hard because it hates leading 0's
        #print(bits)
        
        if bits == bit1 or bits == bit2:
            i = 1
            time.sleep(.25)
def InverseDigInput_wait(probe: Probes, register, bit1: list):
    c = clist[int(probe.id)-1]
    
    i = 0
    while i==0:
        i = 1
        Dinputs = c.read_holding_registers(register, 2)
        decoder = BinaryPayloadDecoder.fromRegisters(Dinputs.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
        bits = int(decoder.decode_32bit_int())
        #replace this to check the actual bit instead of decimal value, python makes this hard because it hates leading 0's
        #print(bits)
        for i in bit1:
            if bits == i:
                i = 0
            time.sleep(.25)


def Check_registers(probe: Probes, register):
    c = clist[int(probe.id)-1]

    result = c.read_holding_registers(register, 2)
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    return decoder.decode_32bit_int()

def Write_registers(probe: Probes, register, value):
    c = clist[int(probe.id)-1]

    builder.add_32bit_int(value)
    payload = builder.build()
    c.write_registers(register, payload, skip_encode=True, unit=0)
    builder.reset()

def Move(probe: Probes, distance): #give distance in mm
    c = clist[int(probe.id)-1]

    MovDistance = -1*(distance * float(probe.MOVEPERMM))
    SoftLimit = -1*(probe.r * probe.MOVEPERMM)
    if MovDistance <= SoftLimit:
        raise Exception(f"You cannot move more than what this probe allows (more than {probe.r} mm)")
    
    builder.add_32bit_int(int(math.floor(MovDistance)))
    payload = builder.build()
    c.write_registers(0, payload, skip_encode=True, unit=0)
    
    c.write_coils(9, [False])
    c.write_coils(9, [True]) #begin movement
    
    DigInput_wait(probe, 10, 19, 23)
    builder.reset()



#Example#

#probe1 = Probes(1, "169.72.98.100", 100, 36000) #Note, because this is designed for Arcus Titan IMX servos, ID's start at 1, while list indexes start at 0. This is why any calls to elements in clist is offset by 1.
#probe5 = Probes(5, "xx", 100, 36000)

#print(clist[0]) #clist contains the ModbusTcpClient information to be able to connect to them.
#print(clist[4])

######### 