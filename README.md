# ModbusMotor
Modbus TCP controller for automated probe drives.

## useful coils
| COIL | Purpose | TYPE |
|:----:|:-------:|:----:|
| 0-2  | Digitial outputs 1-3 | Level |
| 3-6  | Red, Green, Blue, LED toggles | Level |
| 7-8  | Servo on/off | Pos Transition |
| 9 | Start Target Move | Pos Transition |
| 10-11 | Start Jog Plus/Minus | Pos Transition |
| 12 | Start Homing | Pos Transition |
| 13 | Clear Fault | Pos Transition |
| 14 | Stop Motion | Pos Transition |
## useful registers
| REGISTER | Purpose |
|:--------:|:-------:|
| 0 | Target Pos|
| 2 | Target Vel|
| 4 | Target Acc|
| 6 | Target Jer|
| 8 | Move profile|
| 10 | Homing Mode (2 is most useful) |
| 14 | Set Encoder Position |
### note that registers are in the 32-bit Big Endian format, thus trying to write with basic integers won't work, nor will trying to write to a 16-bit register.

# ArcusModbus.py is the most up to date version of the software, adding support for connecting to and running multiple servos at the same time.

# NOW ON PYPI!!! Use "pip install ArcusModbus" to get it. Version 0.0.2 is for single servo use and is known to work, while version 0.0.3 is for single or multi-servo use, however is still experimental and not known if it works.
