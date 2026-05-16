# MyDron INAV Command Reference

## `mydron` commands

```powershell
mydron ports
mydron info --port COM5
mydron status --port COM5
mydron dump-cli --port COM5 --out D:\MyDron\backups\speedybee-v4-dump.txt
mydron cli --port COM5 <safe INAV CLI command>
mydron cli --port COM5 --allow-unsafe "<risky INAV CLI command>"
```

Do not run multiple commands against `COM5` in parallel. Windows allows only one process to hold the port.

## Safe INAV CLI commands allowed by default

These are read-only or diagnostic:

```text
help
version
status
get
diff
dump
resource
memory
tasks
sd_info
gpssats
showdebug
```

Examples:

```powershell
mydron cli --port COM5 version
mydron cli --port COM5 status
mydron cli --port COM5 get gps
mydron cli --port COM5 get serialrx
mydron cli --port COM5 diff all
mydron cli --port COM5 resource
```

## Risky INAV CLI commands

These require `--allow-unsafe` and an explicit plan:

```text
set
save
defaults
dfu
msc
motor
servo
serial
feature
blackbox
beeper
aux
map
rxrange
mmix
smix
resource
timer_output_mode
serialpassthrough
gpspassthrough
bind_rx
play_sound
batch
control_profile
mixer_profile
battery_profile
wp
geozone
safehome
logic
gvar
pid
osd_layout
osd_custom_elements
temp_sensor
fwapproach
```

## Commands exposed by this INAV 9.0.1 target

Observed from `mydron cli --port COM5 help`:

```text
adjrange, aux, batch, beeper, bind_rx, color, mode_color, cli_delay,
defaults, dfu, diff, dump, exit, feature, blackbox, fwapproach, get,
geozone, gpspassthrough, gpssats, help, led, ledpinpwm, map, memory,
mmix, motor, msc, play_sound, control_profile, mixer_profile,
battery_profile, resource, rxrange, safehome, save, serial,
serialpassthrough, servo, logic, gvar, pid, osd_custom_elements, set,
smix, sd_info, showdebug, status, tasks, temp_sensor, version, wp,
osd_layout, timer_output_mode
```

## Change pattern

Use this sequence for any configuration change:

1. Backup under `D:\MyDron\backups`:

   ```powershell
   mydron dump-cli --port COM5 --out D:\MyDron\backups\before-change.txt
   ```

2. Inspect current value and allowed range:

   ```powershell
   mydron cli --port COM5 get <setting-name-or-pattern>
   ```

3. Apply one change:

   ```powershell
   mydron cli --port COM5 --allow-unsafe "set <setting> = <value>"
   ```

4. Read it back:

   ```powershell
   mydron cli --port COM5 get <setting>
   ```

5. Save only after confirmation:

   ```powershell
   mydron cli --port COM5 --allow-unsafe save
   ```

`save` reboots the flight controller.

## Artifact locations

Keep generated files inside `D:\MyDron`:

```text
D:\MyDron\backups   dump/diff backups before and after changes
D:\MyDron\logs      raw command outputs
D:\MyDron\reports   diagnostic summaries
D:\MyDron\plans     planned command batches before execution
D:\MyDron\exports   parsed settings exports
```

Do not write operational artifacts into `C:\Users\pablo\.codex\skills\mydron-inav`; that folder is only for the reusable skill.
