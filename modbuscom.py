import time
import math
#from pymodbus.client import ModbusTcpClient as ModbusTClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pyModbusTCP.client import ModbusClient

c = ModbusClient(host='169.254.246.100', port=5000)
c.open()
c.write_multiple_coils(5, [False])
time.sleep(3)
i = 0
while i < 10:
    c.write_multiple_coils(5, [False])
    c.write_multiple_coils(4, [True])
    print(c.read_coils(3,3))
    time.sleep(.25)
    c.write_multiple_coils(4, [False])
    c.write_multiple_coils(3, [True])
    print(c.read_coils(3,3))
    time.sleep(.25)
    c.write_multiple_coils(3, [False])
    c.write_multiple_coils(5, [True])
    print(c.read_coils(3,3))
    time.sleep(.25)
    i = i+1


print(c.read_holding_registers(0, 2))
print(c.read_holding_registers(2, 2))
c.write_multiple_registers(8, [1])
print(c.read_holding_registers(8, 2))

c.close()
