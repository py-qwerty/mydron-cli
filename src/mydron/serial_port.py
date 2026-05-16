from __future__ import annotations

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Falta pyserial. Instala el proyecto con: pip install -e ."
    ) from exc


def list_serial_ports() -> list[list_ports.ListPortInfo]:
    return list(list_ports.comports())


def open_serial(port: str, baud: int = 115200, timeout: float = 0.1) -> serial.Serial:
    return serial.Serial(
        port=port,
        baudrate=baud,
        timeout=timeout,
        write_timeout=2,
    )
