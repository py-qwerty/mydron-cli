# SpeedyBee F405 V4 Board Folder

Specific files for the connected MyDron SpeedyBee F405 V4 target live here.

Runtime reports should be written to:

```text
D:\MyDron\boards\speedybee-f405-v4\reports
```

Quick health command:

```powershell
mydron quick-health --port COM5 --board speedybee-f405-v4
```

This check is read-only. It verifies the native flight sensors and key onboard
peripherals:

- gyro
- accelerometer
- barometer
- I2C errors
- OSD
- SD card
- battery/current ADC availability

