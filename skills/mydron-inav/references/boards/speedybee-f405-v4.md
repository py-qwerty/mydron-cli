# SpeedyBee F405 V4 Knowledge

Date updated: 2026-05-16

## Identity

```text
Target: SPEEDYBEEF405V4
Board ID: SB44
Firmware: INAV 9.0.1
USB Port Seen: COM5
Board family: SpeedyBee F405 V4
```

## Native Sensors

```text
GYRO: OK, ICM42605
ACC: OK, ICM42605
BARO: OK, SPL06
MAG: QMC5883 when enabled
GPS: UBLOX10 on UART6 when enabled
SD card: Startup failed
```

## Known Good Configuration

```text
feature GPS = ON
serial 5 = 2 115200 115200 0 115200
mag_hardware = QMC5883
baro_hardware = SPL06
gps_provider = UBLOX
gps_auto_config = ON
gps_auto_baud = ON
gps_ublox_use_galileo = ON
gps_ublox_use_beidou = ON
gps_ublox_use_glonass = ON
gps_min_sats = 6
failsafe_procedure = LAND
failsafe_throttle = 1000
```

## Wiring Notes

```text
GPS TX -> R6
GPS RX -> T6
GPS VCC -> 4V5 or valid 5V
GPS GND -> GND
Compass SDA -> SDA
Compass SCL -> SCL
```

Important:

- `SDA/SCL` are for compass/barometer I2C, not GPS data.
- `R6/T6` are the GPS UART for this setup.
- `4V5` is the recommended power source for receiver/GPS from USB per the board manual.

## Health History

```text
Initial state:
- GPS not detected
- I2C errors high after I2C miswire
- MAG/BARO unavailable during bad I2C connection

Recovered state:
- GPS lock achieved
- 6+ satellites observed
- I2C errors returned to 0 after fixing wiring
```

## Quick Health Profile

Use:

```powershell
mydron quick-health --port COM5 --board speedybee-f405-v4
```

Expected:

```text
Board ID: SB44
Target: SPEEDYBEEF405V4
GYRO OK
ACC OK
BARO OK
I2C errors 0
GPS lock when UART6 is wired correctly
```
