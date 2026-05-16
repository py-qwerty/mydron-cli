# MyDron Observed System Facts

Observed on 2026-05-16 from `D:\MyDron\mydron-cli`.

## Flight controller

```text
Port: COM5
Firmware: INAV 9.0.1
Target: SPEEDYBEEF405V4
Board ID: SB44
MSP API: 2.5
Build: Feb 13 2026 06:49:35 d44f2cf6
```

## Status observations

```text
GYRO: OK, ICM42605
ACC: OK, ICM42605
BARO: OK, SPL06
MAG: NONE
GPS: NONE detected
Voltage: 0.00V, battery not present
I2C errors: 0
OSD: MAX7456 30x16
SD card: Startup failed
VTX: not detected
Arming disabled flags: CAL ACC RX CLI
```

## Current key configuration observations

```text
receiver_type = NONE
serialrx_provider = IBUS
gps_provider = UBLOX
gps_auto_config = ON
gps_auto_baud = ON
gps_ublox_use_galileo = ON
gps_ublox_use_beidou = ON
gps_ublox_use_glonass = ON
gps_min_sats = 6
failsafe_procedure = LAND
failsafe_throttle = 1000
motor_pwm_protocol = DSHOT300
```

## Resource highlights

```text
A11: USB IN
A12: USB OUT
B06: MOTOR1 OUT
B07: MOTOR2 OUT
B00: MOTOR3 OUT
B01: MOTOR4 OUT
B08: I2C1 SCL
B09: I2C1 SDA
B12: OSD CS
C13: LED1 OUT
C14: SDCARD CS
C15: BEEPER OUT
```

## Local files

```text
D:\MyDron\backups\
D:\MyDron\logs\
D:\MyDron\reports\
D:\MyDron\plans\
D:\MyDron\exports\
D:\MyDron\references\speedybee-f405-v4\
D:\MyDron\mydron-cli\docs\INAV_CLI_COMMANDS.md
```

Older exploratory files may exist under `D:\MyDron\mydron-cli\backups`, but new operational artifacts should be written to the root-level folders under `D:\MyDron`.
