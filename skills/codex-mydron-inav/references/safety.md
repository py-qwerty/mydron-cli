# MyDron INAV Safety Rules

## Hard stops

Do not run these unless the user explicitly asks for that exact operation and confirms the risk:

```text
motor
servo
save
defaults
dfu
msc
serialpassthrough
gpspassthrough
resource changes
timer_output_mode changes
```

Do not run `defaults` unless the user wants to wipe configuration.

Do not run `save` automatically after `set`. Always read back and ask/confirm first unless the user already gave explicit instruction to save that exact change.

## Motor and servo tests

Before motor/servo/output movement:

1. Tell the user to remove propellers.
2. Confirm the drone is restrained and clear.
3. Explain that USB alone usually will not power ESC motor movement; LiPo may be needed.
4. Prepare stop command first.
5. Test one output at a time, low value, short duration.

Typical motor diagnostic shape:

```powershell
mydron cli --port COM5 motor
mydron cli --port COM5 --allow-unsafe "motor 0 1050"
mydron cli --port COM5 --allow-unsafe "motor 0 1000"
```

Treat `1000` as the stop/minimum command, but verify behavior on this INAV version before relying on it. If uncertain, use INAV Configurator motor tab instead of CLI.

## COM port safety

Only one process can own `COM5`. Close INAV Configurator before using `mydron`.

If a command fails with access denied:

- Close other serial/configurator apps.
- Wait a few seconds after CLI `exit`/`save`.
- Run `mydron ports` again.

## Backup safety

Before any write:

```powershell
mydron dump-cli --port COM5 --out D:\MyDron\backups\before-YYYYMMDD-HHMM.txt
mydron cli --port COM5 diff all > D:\MyDron\backups\before-YYYYMMDD-HHMM-diff.txt
```

Keep all backups in `D:\MyDron\backups`. Keep raw command logs in `D:\MyDron\logs`, reports in `D:\MyDron\reports`, plans in `D:\MyDron\plans`, and parsed exports in `D:\MyDron\exports`.

Do not store live-drone operational artifacts inside the skill folder.

## Interpreting arming flags

Observed flags include:

```text
CAL ACC RX CLI
```

Meaning:

- `CAL`: calibration or sensor readiness blocks arming.
- `ACC`: accelerometer calibration/health blocks arming.
- `RX`: receiver not detected/configured.
- `CLI`: being in CLI mode blocks arming.

Do not try to arm from this tool.
