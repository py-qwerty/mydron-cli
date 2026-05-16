from mydron.health import (
    CheckRow,
    parse_cli_status,
    parse_hardware,
    parse_tasks,
    render_table,
)


STATUS_TEXT = """
CPU Clock=168MHz, GYRO=ICM42605, ACC=ICM42605, BARO=SPL06
Sensor status: GYRO=OK, ACC=OK, MAG=NONE, BARO=OK, RANGEFINDER=NONE, OPFLOW=NONE, GPS=NONE
SD card: Startup failed
I2C Errors: 0, config size: 13517, max available config: 131072
ADC channel usage:
   BATTERY : configured = ADC 1, used = ADC 1
      RSSI : configured = ADC 3, used = none
   CURRENT : configured = ADC 2, used = ADC 2
System load: 10, cycle time: 516, PID rate: 1937, RX rate: 49, System rate: 9
Arming disabled flags: CAL ACC RX CLI
OSD: MAX7456 [30 x 16]
VTX: not detected
"""


def test_parse_cli_status() -> None:
    parsed = parse_cli_status(STATUS_TEXT)

    assert parsed["sensors"]["GYRO"] == "OK"
    assert parsed["sensors"]["BARO"] == "OK"
    assert parsed["sensors"]["GPS"] == "NONE"
    assert parsed["i2c_errors"] == 0
    assert parsed["adc"]["BATTERY"] == "configured=ADC 1, used=ADC 1"
    assert parsed["sd"] == "Startup failed"
    assert parsed["osd"] == "MAX7456 [30 x 16]"


def test_parse_tasks() -> None:
    tasks = parse_tasks(" 2 -         GYRO    3984      14      11    6.0%    4.8%         1")

    assert tasks["GYRO"]["rate_hz"] == "3984"
    assert tasks["GYRO"]["avgload"] == "4.8"


def test_parse_hardware() -> None:
    hardware = parse_hardware("acc_hardware = ICM42605\nbaro_hardware = SPL06\n")

    assert hardware["acc_hardware"] == "ICM42605"
    assert hardware["baro_hardware"] == "SPL06"


def test_render_table_is_ascii() -> None:
    table = render_table(
        [CheckRow("GYRO", "OK", "state=OK", "ok")],
        color=False,
    )

    assert all(ord(character) < 128 for character in table)
    assert "| Component | Health | Detail   |" in table
    assert "\033" not in table
