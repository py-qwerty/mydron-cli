from __future__ import annotations

from dataclasses import dataclass
from contextlib import suppress
from pathlib import Path
import time

from .msp import (
    MSP_API_VERSION,
    MSP_BOARD_INFO,
    MSP_BUILD_INFO,
    MSP_FC_VARIANT,
    MSP_FC_VERSION,
    MSP_STATUS,
    MspDirection,
    MspError,
    build_msp_v1_request,
    parse_api_version,
    parse_ascii,
    parse_board_info,
    parse_fc_version,
    parse_status,
    read_frame,
)
from .serial_port import open_serial


@dataclass(frozen=True)
class InavInfo:
    api_version: dict[str, int]
    fc_variant: str
    fc_version: str
    board_info: dict[str, int | str]
    build_info: str


class InavClient:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 2.0) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial = open_serial(port, baud=baud, timeout=0.1)

    def close(self) -> None:
        self.serial.close()

    def __enter__(self) -> "InavClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def request(self, command: int, payload: bytes = b"") -> bytes:
        self.serial.reset_input_buffer()
        self.serial.write(build_msp_v1_request(command, payload))
        self.serial.flush()

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            frame = read_frame(self.serial, timeout=max(0.05, deadline - time.monotonic()))
            if frame.command != command:
                continue
            if frame.direction == MspDirection.ERROR:
                raise MspError(f"Flight controller returned MSP error for {command}")
            return frame.payload

        raise TimeoutError(f"No MSP response for command {command}")

    def read_info(self) -> InavInfo:
        return InavInfo(
            api_version=parse_api_version(self.request(MSP_API_VERSION)),
            fc_variant=parse_ascii(self.request(MSP_FC_VARIANT)),
            fc_version=parse_fc_version(self.request(MSP_FC_VERSION)),
            board_info=parse_board_info(self.request(MSP_BOARD_INFO)),
            build_info=parse_ascii(self.request(MSP_BUILD_INFO)),
        )

    def read_status(self) -> dict[str, int]:
        return parse_status(self.request(MSP_STATUS))

    def enter_cli(self) -> str:
        self.serial.reset_input_buffer()
        self.serial.write(b"#\r")
        self.serial.flush()
        return self._read_text_until_prompt(timeout=4.0)

    def cli_command(self, command: str, timeout: float = 5.0) -> str:
        line = command.rstrip("\r\n").encode("ascii", errors="replace") + b"\r"
        self.serial.write(line)
        self.serial.flush()
        return self._read_text_until_prompt(timeout=timeout)

    def exit_cli(self) -> str:
        self.serial.write(b"exit\r")
        self.serial.flush()
        with suppress(Exception):
            return self._read_text(timeout=2.0)
        return ""

    def dump_cli(self, destination: Path, timeout: float = 20.0) -> None:
        self.enter_cli()
        try:
            output = self.cli_command("dump", timeout=timeout)
            destination.write_text(output, encoding="utf-8")
        finally:
            self.exit_cli()

    def _read_text_until_prompt(self, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        data = bytearray()
        while time.monotonic() < deadline:
            chunk = self.serial.read(512)
            if chunk:
                data.extend(chunk)
                text = data.decode("utf-8", errors="replace")
                if text.rstrip().endswith("#"):
                    return text
        return data.decode("utf-8", errors="replace")

    def _read_text(self, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        data = bytearray()
        while time.monotonic() < deadline:
            with suppress(Exception):
                chunk = self.serial.read(512)
                if chunk:
                    data.extend(chunk)
                continue
            break
        return data.decode("utf-8", errors="replace")
