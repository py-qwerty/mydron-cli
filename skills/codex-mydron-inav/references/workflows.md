# MyDron INAV Workflows

## Identify the USB port

1. List ports:

   ```powershell
   mydron ports
   ```

2. Prefer the entry named like `Dispositivo serie USB (COMx)` over Bluetooth serial ports.

3. Probe candidates one at a time:

   ```powershell
   mydron info --port COM5
   ```

4. A valid response should include `INAV`, `SPEEDYBEEF405V4`, and MSP API.

## Full read-only diagnostic

Run sequentially:

```powershell
mydron info --port COM5
mydron status --port COM5
mydron cli --port COM5 status
mydron cli --port COM5 resource
mydron cli --port COM5 tasks
mydron cli --port COM5 memory
mydron cli --port COM5 sd_info
mydron cli --port COM5 diff all
```

Summarize sensors, arming flags, receiver/GPS presence, SD/OSD/VTX state, and configuration drift.

## Quick health for SpeedyBee F405 V4

Use the board-specific profile and store reports in the board folder:

```powershell
mydron quick-health --port COM5 --board speedybee-f405-v4
```

Expected output folder:

```text
D:\MyDron\boards\speedybee-f405-v4\reports
```

This is read-only and checks board ID, target, native sensors, I2C errors, OSD,
SD, and ADC channel visibility.

## Backup

Use:

```powershell
mydron dump-cli --port COM5 --out D:\MyDron\backups\speedybee-v4-dump.txt
mydron cli --port COM5 diff all > D:\MyDron\backups\speedybee-v4-diff-all.txt
```

For change sessions, create a timestamped backup:

```powershell
mydron dump-cli --port COM5 --out D:\MyDron\backups\before-change-YYYYMMDD-HHMM.txt
```

Store generated artifacts here:

```text
D:\MyDron\backups   dump and diff outputs
D:\MyDron\logs      raw command sessions
D:\MyDron\reports   summaries and diagnostics
D:\MyDron\plans     command plans before risky changes
D:\MyDron\exports   parsed settings as JSON/CSV
```

## Configure receiver

First inspect:

```powershell
mydron cli --port COM5 get receiver
mydron cli --port COM5 get serialrx
mydron cli --port COM5 serial
```

Typical serial receiver shape:

```powershell
mydron cli --port COM5 --allow-unsafe "set receiver_type = SERIAL"
mydron cli --port COM5 --allow-unsafe "set serialrx_provider = IBUS"
```

The serial port command depends on which UART the receiver is wired to. Do not guess; ask the user which UART/pads were used or inspect the SpeedyBee wiring.

After setting, read back:

```powershell
mydron cli --port COM5 get receiver
mydron cli --port COM5 get serialrx
```

Save only after confirmation:

```powershell
mydron cli --port COM5 --allow-unsafe save
```

## Configure GPS

First inspect:

```powershell
mydron cli --port COM5 get gps
mydron cli --port COM5 serial
mydron cli --port COM5 status
```

Typical GPS settings already observed:

```text
gps_provider = UBLOX
gps_auto_config = ON
gps_auto_baud = ON
gps_min_sats = 6
```

The UART/serial command depends on the physical UART used for GPS. Do not guess the `serial` line; ask for wiring or compare current `serial` output with board documentation.

After wiring and serial feature are correct, use:

```powershell
mydron cli --port COM5 gpssats
mydron cli --port COM5 status
```

## Configure failsafe

Inspect:

```powershell
mydron cli --port COM5 get failsafe
```

Observed current:

```text
failsafe_procedure = LAND
failsafe_throttle = 1000
```

Changing failsafe affects flight behavior. Prefer discussing flight goal first: multirotor landing, drop, or RTH with GPS. RTH requires GPS configuration and validation.

## Motor diagnostics

Only after safety confirmation. Use the lowest possible test and one motor at a time.

Read current motor command/help first:

```powershell
mydron cli --port COM5 motor
```

Possible test shape:

```powershell
mydron cli --port COM5 --allow-unsafe "motor 0 1050"
mydron cli --port COM5 --allow-unsafe "motor 0 1000"
```

Repeat for motor indices only if the first test behaves as expected. Stop immediately on unexpected movement.

## Restore or apply batch

Avoid full restore unless necessary. Prefer applying minimal changes.

If restoring from `diff` or `dump`, first create a plan file under `D:\MyDron\plans`, review lines before sending them, and treat the final `save` line as a separate explicit step.
