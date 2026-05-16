from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from .inav import InavClient, InavInfo


DEFAULT_BOARD = "speedybee-f405-v4"
DEFAULT_BOARD_DIR = Path(r"D:\MyDron\boards\speedybee-f405-v4")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CheckRow:
    component: str
    state: str
    detail: str
    level: str


def load_board_profile(board: str = DEFAULT_BOARD) -> dict:
    path = PROJECT_ROOT / "boards" / board / "health-profile.json"
    if not path.exists():
        raise FileNotFoundError(f"No existe perfil de placa: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_quick_health(
    port: str,
    baud: int = 115200,
    board: str = DEFAULT_BOARD,
    out_dir: Path | None = None,
    color: bool = True,
) -> tuple[str, Path]:
    profile = load_board_profile(board)
    report_dir = out_dir or DEFAULT_BOARD_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    with InavClient(port, baud=baud) as client:
        info = client.read_info()
        msp_status = client.read_status()
        client.enter_cli()
        try:
            cli_status = client.cli_command("status", timeout=8.0)
            sd_info = client.cli_command("sd_info", timeout=5.0)
            tasks = client.cli_command("tasks", timeout=8.0)
            hardware = client.cli_command("get hardware", timeout=8.0)
        finally:
            client.exit_cli()

    parsed_status = parse_cli_status(cli_status)
    parsed_tasks = parse_tasks(tasks)
    parsed_hardware = parse_hardware(hardware)
    rows = evaluate_health(
        info=info,
        msp_status=msp_status,
        parsed_status=parsed_status,
        parsed_tasks=parsed_tasks,
        parsed_hardware=parsed_hardware,
        sd_info=sd_info,
        profile=profile,
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"quick-health-{board}-{timestamp}.md"
    report = render_report(
        port=port,
        baud=baud,
        board=board,
        info=info,
        rows=rows,
        parsed_status=parsed_status,
        msp_status=msp_status,
        parsed_tasks=parsed_tasks,
        color=False,
    )
    report_path.write_text(report, encoding="utf-8")

    terminal_output = render_report(
        port=port,
        baud=baud,
        board=board,
        info=info,
        rows=rows,
        parsed_status=parsed_status,
        msp_status=msp_status,
        parsed_tasks=parsed_tasks,
        color=color,
    )
    return terminal_output + f"\nReport: {report_path}\n", report_path


def parse_cli_status(text: str) -> dict[str, object]:
    result: dict[str, object] = {"sensors": {}, "adc": {}}
    sensor_match = re.search(r"Sensor status:\s*(.+)", text)
    if sensor_match:
        result["sensors"] = {
            key: value
            for key, value in re.findall(r"([A-Z]+)=([A-Z]+)", sensor_match.group(1))
        }

    for key, pattern in {
        "voltage": r"Voltage:\s*(.+)",
        "cpu": r"CPU Clock=(.+)",
        "sd": r"SD card:\s*(.+)",
        "i2c_errors": r"I2C Errors:\s*(\d+)",
        "arming_disabled_flags": r"Arming disabled flags:\s*(.+)",
        "osd": r"OSD:\s*(.+)",
        "vtx": r"VTX:\s*(.+)",
    }.items():
        match = re.search(pattern, text)
        if match:
            value: object = match.group(1).strip()
            if key == "i2c_errors":
                value = int(str(value))
            result[key] = value

    adc: dict[str, str] = {}
    for name, configured, used in re.findall(
        r"^\s*([A-Z]+)\s*:\s*configured\s*=\s*([^,]+),\s*used\s*=\s*(.+)$",
        text,
        flags=re.MULTILINE,
    ):
        adc[name] = f"configured={configured.strip()}, used={used.strip()}"
    result["adc"] = adc
    return result


def parse_tasks(text: str) -> dict[str, dict[str, str]]:
    tasks: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        match = re.match(
            r"\s*\d+\s*-\s*([A-Z ]+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%",
            line,
        )
        if match:
            name, rate, max_us, avg_us, maxload, avgload = match.groups()
            tasks[name.strip()] = {
                "rate_hz": rate,
                "max_us": max_us,
                "avg_us": avg_us,
                "maxload": maxload,
                "avgload": avgload,
            }
    return tasks


def parse_hardware(text: str) -> dict[str, str]:
    return {
        key: value
        for key, value in re.findall(
            r"^([a-z0-9_]+)\s*=\s*([A-Z0-9_]+)", text, flags=re.MULTILINE
        )
    }


def evaluate_health(
    info: InavInfo,
    msp_status: dict[str, int],
    parsed_status: dict[str, object],
    parsed_tasks: dict[str, dict[str, str]],
    parsed_hardware: dict[str, str],
    sd_info: str,
    profile: dict,
) -> list[CheckRow]:
    rows: list[CheckRow] = []
    sensors = parsed_status.get("sensors", {})
    assert isinstance(sensors, dict)

    board_id = str(info.board_info.get("identifier", "unknown"))
    target = str(info.board_info.get("target_name", "unknown"))
    expected_board_id = profile.get("expected_board_id")
    expected_target = profile.get("expected_target")
    board_ok = board_id == expected_board_id and target == expected_target
    rows.append(
        CheckRow(
            "BOARD",
            "OK" if board_ok else "WARN",
            f"{board_id} / {target}",
            "ok" if board_ok else "warn",
        )
    )

    hardware_by_sensor = {
        "GYRO": parsed_status.get("cpu", ""),
        "ACC": parsed_hardware.get("acc_hardware", "unknown"),
        "BARO": parsed_hardware.get("baro_hardware", "unknown"),
    }
    task_by_sensor = {"GYRO": "GYRO", "BARO": "BARO"}

    for sensor, cfg in profile["native_sensors"].items():
        state = str(sensors.get(sensor, "UNKNOWN"))
        required = bool(cfg.get("required", False))
        expected_state = cfg.get("expected_state")
        ok = state == expected_state
        level = "ok" if ok else ("fail" if required else "warn")
        detail_parts = [f"state={state}"]
        expected_hardware = cfg.get("expected_hardware")
        if expected_hardware:
            hardware_value = str(hardware_by_sensor.get(sensor, "unknown"))
            detail_parts.append(f"hardware={hardware_value}")
        task_name = task_by_sensor.get(sensor)
        if task_name and task_name in parsed_tasks:
            detail_parts.append(f"task={parsed_tasks[task_name]['rate_hz']}Hz")
        rows.append(
            CheckRow(
                sensor,
                "OK" if level == "ok" else ("FAIL" if level == "fail" else "WARN"),
                ", ".join(detail_parts),
                level,
            )
        )

    i2c_errors = int(msp_status.get("i2c_errors", parsed_status.get("i2c_errors", 0)))
    max_i2c = int(profile["limits"]["max_i2c_errors"])
    rows.append(
        CheckRow(
            "I2C",
            "OK" if i2c_errors <= max_i2c else "FAIL",
            f"errors={i2c_errors}",
            "ok" if i2c_errors <= max_i2c else "fail",
        )
    )

    osd = str(parsed_status.get("osd", "unknown"))
    osd_expected = profile["peripherals"]["OSD"]["expected_contains"]
    osd_ok = osd_expected in osd
    rows.append(
        CheckRow(
            "OSD",
            "OK" if osd_ok else "FAIL",
            osd,
            "ok" if osd_ok else "fail",
        )
    )

    sd_state = parse_sd_state(sd_info, parsed_status)
    sd_warn = profile["peripherals"]["SD"].get("warn_on")
    sd_ok = sd_warn not in sd_state
    rows.append(
        CheckRow(
            "SD",
            "OK" if sd_ok else "WARN",
            sd_state,
            "ok" if sd_ok else "warn",
        )
    )

    adc = parsed_status.get("adc", {})
    assert isinstance(adc, dict)
    for adc_name in ("BATTERY", "CURRENT", "RSSI"):
        detail = str(adc.get(adc_name, "not reported"))
        level = "ok" if "used=none" not in detail and detail != "not reported" else "warn"
        rows.append(
            CheckRow(
                f"ADC_{adc_name}",
                "OK" if level == "ok" else "WARN",
                detail,
                level,
            )
        )

    return rows


def parse_sd_state(sd_info: str, parsed_status: dict[str, object]) -> str:
    match = re.search(r"SD card:\s*(.+)", sd_info)
    if match:
        return match.group(1).strip()
    return str(parsed_status.get("sd", "unknown"))


def render_report(
    port: str,
    baud: int,
    board: str,
    info: InavInfo,
    rows: list[CheckRow],
    parsed_status: dict[str, object],
    msp_status: dict[str, int],
    parsed_tasks: dict[str, dict[str, str]],
    color: bool,
) -> str:
    target = info.board_info.get("target_name", "unknown")
    board_id = info.board_info.get("identifier", "unknown")
    overall = "FAIL" if any(row.level == "fail" for row in rows) else "OK"
    if any(row.level == "warn" for row in rows) and overall == "OK":
        overall = "WARN"

    lines = [
        f"# Quick Health - {board}",
        "",
        "```text",
        f"Port: {port}",
        f"Baud: {baud}",
        f"Firmware: {info.fc_variant} {info.fc_version}",
        f"Board: {board_id} / {target}",
        f"Overall: {paint(overall, level_for_state(overall), color)}",
        "```",
        "",
        render_table(rows, color=color),
        "",
        "```text",
        f"I2C errors: {msp_status.get('i2c_errors', 'unknown')}",
        f"Cycle time us: {msp_status.get('cycle_time_us', 'unknown')}",
        f"Sensors mask: {msp_status.get('sensors_mask', 'unknown')}",
        f"Voltage: {parsed_status.get('voltage', 'unknown')}",
        f"Arming disabled flags: {parsed_status.get('arming_disabled_flags', 'unknown')}",
        "```",
    ]
    if parsed_tasks:
        lines.extend(
            [
                "",
                "```text",
                "Key tasks:",
                f"GYRO: {parsed_tasks.get('GYRO', {}).get('rate_hz', 'n/a')} Hz",
                f"PID: {parsed_tasks.get('PID', {}).get('rate_hz', 'n/a')} Hz",
                f"BARO: {parsed_tasks.get('BARO', {}).get('rate_hz', 'n/a')} Hz",
                f"OSD: {parsed_tasks.get('OSD', {}).get('rate_hz', 'n/a')} Hz",
                "```",
            ]
        )
    return "\n".join(lines)


def render_table(rows: list[CheckRow], color: bool) -> str:
    headers = ("Component", "Health", "Detail")
    widths = [
        max(len(headers[0]), *(len(row.component) for row in rows)),
        max(len(headers[1]), *(len(row.state) for row in rows)),
        max(len(headers[2]), *(len(row.detail) for row in rows)),
    ]

    def sep() -> str:
        return "+" + "+".join("-" * (width + 2) for width in widths) + "+"

    def row(values: tuple[str, str, str], level: str | None = None) -> str:
        rendered = []
        for index, value in enumerate(values):
            cell = value.ljust(widths[index])
            if index == 1 and level:
                cell = paint(cell, level, color)
            rendered.append(f" {cell} ")
        return "|" + "|".join(rendered) + "|"

    lines = ["```text", sep(), row(headers), sep()]
    for item in rows:
        lines.append(row((item.component, item.state, item.detail), item.level))
    lines.append(sep())
    lines.append("```")
    return "\n".join(lines)


def paint(text: str, level: str, color: bool) -> str:
    if not color:
        return text
    colors = {"ok": "32", "warn": "33", "fail": "31"}
    code = colors.get(level)
    return f"\033[{code}m{text}\033[0m" if code else text


def level_for_state(state: str) -> str:
    return {"OK": "ok", "WARN": "warn", "FAIL": "fail"}.get(state, "")
