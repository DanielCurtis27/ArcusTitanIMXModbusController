import Probe as Pr
import time

#this is an example script for how the Probe file can be used

probe1 = Pr.Probes(5, '169.254.35.100', 100, 36000) #Initiate a probe, Pr.Probes(ID, IP, softLimit, MOVEPERMM)
#MOVEPERMM is just found by moving the probe a certain amount of pul and seeing how many mm it moved, IT IS CURRENTLY INCORRECT.

Pr.ConnectandInitializeProbe(probe1) 
print("initalized!")
time.sleep(1)

Pr.Home() #Home until limit switch is pressed
print("homed")

Pr.Move(probe1, 20) #Which probe and how far (in mm), although currently only one probe can be connected to at a time, it should be simple to fix this later.
time.sleep(2)

position = Pr.Check_registers(0) #register 0 is the position register
print(position)

Pr.Disconnect()

print("Successfully disconnected, attempting a reconnect")
time.sleep(2)
Pr.ConnectandInitializeProbe(probe1)
time.sleep(2)
print("reconnected!!!!")

time.sleep(2)
Pr.Disconnect()