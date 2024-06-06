from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
import time
import math

class Probes:
    def __init__(self, ID, IP, InsertRadius, MOVEPERMM):
        self.id = ID #this will be posted on the side of the motors (ID 5 is the one currently on SABER)
        self.ip = IP
        self.r = InsertRadius #for the soft limit of the motor, more like an "outsert radius"
        self.MOVEPERMM = MOVEPERMM


c = ModbusClient(host="x", port=5000) #dummy value for initializing c as a ModbusClient

builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
def ConnectandInitializeProbe(probe: Probes):
    global c
    c = ModbusClient(host=probe.ip, port=5000)
    c.connect()
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
        Write_registers(int(addresses[i]), int(payloadunbuilt[i]))
        time.sleep(.1)

    c.write_coils(7, [False]) 
    c.write_coils(7, [True]) #turn servo on
 
def Home():
    global c
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

def Disconnect(): #run this before connecting to a new probe
    global c
    c.write_coils(8, [False])
    c.write_coils(8, [True]) #turn off motor

    c.close() #close the connection

def DigInput_wait(register, bit1, bit2):
    global c
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
    global c
    result = c.read_holding_registers(register, 2)
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    return decoder.decode_32bit_int()

def Write_registers(register, value):
    global c
    builder.add_32bit_int(value)
    payload = builder.build()
    c.write_registers(register, payload, skip_encode=True, unit=0)
    builder.reset()

def Move(probes: Probes, distance): #give distance in mm
    global c
    MovDistance = -1*(distance * float(probes.MOVEPERMM))
    SoftLimit = -1*(probes.r * probes.MOVEPERMM)
    if MovDistance <= SoftLimit:
        raise Exception(f"You cannot move more than what this probe allows (more than {probes.r} mm)")
    
    builder.add_32bit_int(int(math.floor(MovDistance)))
    payload = builder.build()
    c.write_registers(0, payload, skip_encode=True, unit=0)
    
    c.write_coils(9, [False])
    c.write_coils(9, [True]) #begin movement
    
    DigInput_wait(10, 19, 23) #waits until movement is done
    builder.reset()