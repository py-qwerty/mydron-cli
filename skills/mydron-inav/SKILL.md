---
name: mydron-inav
description: Operate, diagnose, back up, and safely configure Pablo's MyDron INAV setup from the local `mydron` CLI. Use when working with the SpeedyBee F405 V4 / INAV flight controller over USB, identifying the correct COM port, reading status/configuration, creating backups, planning or applying INAV CLI changes, configuring receiver/GPS/failsafe/ports/OSD, or performing high-risk diagnostics such as motor or servo tests with explicit safety gates.
---

# MyDron INAV

## Core Rules

Treat the flight controller as a live system. Prefer read-only commands first, take a backup before changes, and never run motor/servo/output commands unless the user explicitly asks for that diagnostic and confirms safety conditions.

For graphical explanations in text, always use plain ASCII diagrams, tables, pin maps, and flowcharts. Avoid Unicode box drawing so the output stays portable across terminals, logs, GitHub, and PowerShell.

Use terminal colors when they improve scanning of diagnostics or command output. Prefer ANSI colors through the CLI/code for statuses such as OK/warn/error, safe/risky commands, and sensor states. Provide a no-color path or avoid color when writing logs/reports to files.

Use `D:\MyDron` as the operational root. Store generated backups, logs, plans, reports, and exports under this root, not inside the skill folder.

Use the code project at `D:\MyDron\mydron-cli`. The command is available as `mydron` after `D:\MyDron\mydron-cli\bin` is on PATH; otherwise call `D:\MyDron\mydron-cli\bin\mydron.cmd`.

Operational folders:

```text
D:\MyDron\backups   configuration dumps and diff backups
D:\MyDron\logs      raw command outputs and session logs
D:\MyDron\reports   human-readable diagnostic summaries
D:\MyDron\plans     proposed command plans before execution
D:\MyDron\exports   parsed settings, JSON/CSV exports, derived data
D:\MyDron\references official board/manual reference files
```

Known current target:

```text
Port: COM5 when connected in the current setup
Firmware: INAV 9.0.1
Target: SPEEDYBEEF405V4
Board ID: SB44
Board: SpeedyBee F405 V4
```

## First Workflow

1. Identify the USB port:

   ```powershell
   mydron ports
   mydron info --port COM5
   ```

2. Verify state:

   ```powershell
   mydron status --port COM5
   mydron cli --port COM5 status
   ```

3. Create or refresh backup before any change:

   ```powershell
   mydron dump-cli --port COM5 --out D:\MyDron\backups\speedybee-v4-dump.txt
   mydron cli --port COM5 diff all > D:\MyDron\backups\speedybee-v4-diff-all.txt
   ```

4. For changes, build a small command plan, explain risk, then use `--allow-unsafe` only for the exact commands needed.

## Safety Gates

`mydron cli` blocks write/risky commands by default. To send a command such as `set`, `save`, `motor`, `servo`, `defaults`, `dfu`, or passthrough commands, pass `--allow-unsafe`.

Never bypass this silently. State the exact command and its effect before running it.

For motor/servo/output tests, require all of these:

- Propellers removed.
- Drone restrained and clear of people.
- User explicitly requested output movement.
- Battery requirement understood: USB alone usually cannot spin motors; ESC power normally requires LiPo.
- Stop command plan is ready before start command.

## Reference Loading

Load only the reference needed for the task:

- `references/commands.md`: command list, safe/risky categories, `mydron cli` syntax.
- `references/workflows.md`: procedures for port detection, backup, receiver, GPS, failsafe, motor diagnostics.
- `references/safety.md`: hard safety rules and confirmation requirements.
- `references/system-facts.md`: facts observed from this specific drone and backup files.
- `references/boards/`: board-specific knowledge, one file per board.

Before wiring/configuration work, consult the downloaded official SpeedyBee manuals at `D:\MyDron\references\speedybee-f405-v4`.

## Common Commands

Read-only:

```powershell
mydron ports
mydron info --port COM5
mydron status --port COM5
mydron cli --port COM5 help
mydron cli --port COM5 version
mydron cli --port COM5 status
mydron cli --port COM5 get receiver
mydron cli --port COM5 get gps
mydron cli --port COM5 get failsafe
mydron cli --port COM5 resource
mydron cli --port COM5 diff all
```

Write/risky pattern:

```powershell
mydron cli --port COM5 --allow-unsafe "set name = value"
mydron cli --port COM5 --allow-unsafe save
```

Do not run write/risky patterns until the relevant reference has been checked and a backup exists.
