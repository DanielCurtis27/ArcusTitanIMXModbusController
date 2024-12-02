from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
import time

#used to write to the motors
builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
def Write_registers(client, register, value):
        builder.add_32bit_int(value)
        payload = builder.build()
        client.write_registers(register, payload, skip_encode=True, unit=0)
        builder.reset()

def Check_registers(client, register):
    result = client.read_holding_registers(register, 2)
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
    return decoder.decode_32bit_int()

def DigInput_wait(client, register, bit1, bit2):
    i = 0
    while i==0:
        Dinputs = client.read_holding_registers(register, 2)
        decoder = BinaryPayloadDecoder.fromRegisters(Dinputs.registers, byteorder=Endian.BIG, wordorder=Endian.BIG)
        bits = int(decoder.decode_32bit_int())
        #replace this to check the actual bit instead of decimal value, python makes this hard because it hates leading 0's
        #print(bits)
        if bits == bit1 or bits==bit2: #this corresponds to the motor being on, in position, and homed
            i = 1
        time.sleep(.25)

class Probes:
    def __init__(self, ID, IP, InsertRadius, MOVEPERMM):
        self.id = ID #this will be posted on the side of the motors (ID 5 is the one currently on SABER)
        self.ip = IP
        self.r = InsertRadius #for the soft limit of the motor, more like an "outsert radius"
        self.MOVEPERMM = MOVEPERMM
        self.client = ModbusClient(host=self.ip, port=5000)

    def connect(self):
        self.client.connect()
        self.client.write_coils(13, [False]) 
        self.client.write_coils(13, [True])

    def initiate(self, speed: int, accel: int):
        payloadunbuilt = [speed, accel, 10000, 1, 0]
        addresses = [2, 4, 6, 8, 10]
        #in order, these addresses corrispond to:
        #target speed, target acceleration, target jerk, move pattern, homing mode
        for i in range(len(payloadunbuilt)): #encodes and sends the data to the motor
            Write_registers(self.client, int(addresses[i]), int(payloadunbuilt[i]))
            time.sleep(.1)

        self.client.write_coils(7, [False]) 
        self.client.write_coils(7, [True]) #turn servo on

    def home(self):
        self.client.write_coils(14, [False])
        self.client.write_coils(14, [True]) #stop all motion

        print("homing")
        time.sleep(1.5)
        self.client.write_coils(12, [False])
        self.client.write_coils(12, [True]) #homes the motor until limit switch is hit

        DigInput_wait(self.client, 10, 19, 23) #halts program until motor is homed

        self.client.write_coils(14, [False])
        self.client.write_coils(14, [True]) #stop all motion

        time.sleep(1.5)
        Write_registers(self.client, 14, 0) #sets position to 0
        time.sleep(.5)
        print(f"pos: {Check_registers(self.client, 0)}")
        time.sleep(1)
    def move(self, distance): #give distance in mm

        MovDistance = -1*(distance * float(self.MOVEPERMM))
        SoftLimit = -1*(self.r * self.MOVEPERMM)
        if MovDistance >= SoftLimit:
            raise Exception(f"You cannot move more than what this probe allows ({self.r})")

        builder.add_32bit_int(MovDistance)
        payload = builder.build()
        self.client.write_registers(0, payload, skip_encode=True, unit=0)

        self.client.write_coils(9, [False])
        self.client.write_coils(9, [True]) #begin movement

        DigInput_wait(self.client, 10, 19, 23) #waits until movement is done
        builder.reset()

    def disconnect(self):
        self.client.write_coils(8, [False])
        self.client.write_coils(8, [True]) #turn off motor

        self.client.close() #close the connection
    