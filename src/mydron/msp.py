from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import time
from typing import BinaryIO


MSP_API_VERSION = 1
MSP_FC_VARIANT = 2
MSP_FC_VERSION = 3
MSP_BOARD_INFO = 4
MSP_BUILD_INFO = 5
MSP_STATUS = 101


class MspDirection(IntEnum):
    REQUEST = ord("<")
    RESPONSE = ord(">")
    ERROR = ord("!")


@dataclass(frozen=True)
class MspFrame:
    version: int
    direction: MspDirection
    command: int
    payload: bytes
    flags: int = 0


class MspError(RuntimeError):
    pass


class MspChecksumError(MspError):
    pass


class MspTimeoutError(MspError):
    pass


def build_msp_v1_request(command: int, payload: bytes = b"") -> bytes:
    if not 0 <= command <= 255:
        raise ValueError("MSP v1 command must fit in one byte")
    if len(payload) > 255:
        raise ValueError("MSP v1 payload must be <= 255 bytes")

    size = len(payload)
    checksum = size ^ command
    for byte in payload:
        checksum ^= byte

    return bytes((ord("$"), ord("M"), ord("<"), size, command, *payload, checksum))


def build_msp_v2_request(command: int, payload: bytes = b"", flags: int = 0) -> bytes:
    if not 0 <= command <= 65535:
        raise ValueError("MSP v2 command must fit in two bytes")
    if not 0 <= flags <= 255:
        raise ValueError("MSP v2 flags must fit in one byte")
    if len(payload) > 65535:
        raise ValueError("MSP v2 payload must be <= 65535 bytes")

    body = bytes((flags,)) + struct.pack("<HH", command, len(payload)) + payload
    checksum = crc8_dvb_s2(body)
    return b"$X<" + body + bytes((checksum,))


def crc8_dvb_s2(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def parse_api_version(payload: bytes) -> dict[str, int]:
    if len(payload) < 3:
        raise MspError("MSP_API_VERSION payload too short")
    return {
        "protocol": payload[0],
        "major": payload[1],
        "minor": payload[2],
    }


def parse_fc_version(payload: bytes) -> str:
    if len(payload) < 3:
        raise MspError("MSP_FC_VERSION payload too short")
    return f"{payload[0]}.{payload[1]}.{payload[2]}"


def parse_ascii(payload: bytes) -> str:
    return payload.rstrip(b"\x00").decode("ascii", errors="replace")


def parse_board_info(payload: bytes) -> dict[str, int | str]:
    if len(payload) < 4:
        raise MspError("MSP_BOARD_INFO payload too short")

    info: dict[str, int | str] = {
        "identifier": payload[:4].decode("ascii", errors="replace"),
    }

    if len(payload) >= 6:
        info["hardware_revision"] = struct.unpack_from("<H", payload, 4)[0]
    if len(payload) >= 7:
        info["fc_type"] = payload[6]
    if len(payload) >= 8:
        info["target_capabilities"] = payload[7]
    if len(payload) >= 9:
        name_length = payload[8]
        name_start = 9
        name_end = min(len(payload), name_start + name_length)
        info["target_name"] = payload[name_start:name_end].decode(
            "ascii", errors="replace"
        )

    return info


def parse_status(payload: bytes) -> dict[str, int]:
    if len(payload) < 11:
        raise MspError("MSP_STATUS payload too short")

    cycle_time, i2c_errors, sensors, mode_flags = struct.unpack_from("<HHHI", payload)
    profile = payload[10]
    return {
        "cycle_time_us": cycle_time,
        "i2c_errors": i2c_errors,
        "sensors_mask": sensors,
        "mode_flags": mode_flags,
        "profile": profile,
    }


def read_frame(stream: BinaryIO, timeout: float = 2.0) -> MspFrame:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        lead = stream.read(1)
        if lead == b"$":
            protocol = _read_exact(stream, 1, deadline)
            if protocol == b"M":
                return _read_v1_frame(stream, deadline)
            if protocol == b"X":
                return _read_v2_frame(stream, deadline)

    raise MspTimeoutError("Timed out waiting for MSP frame")


def _read_v1_frame(stream: BinaryIO, deadline: float) -> MspFrame:
    direction = MspDirection(_read_exact(stream, 1, deadline)[0])
    size = _read_exact(stream, 1, deadline)[0]
    command = _read_exact(stream, 1, deadline)[0]
    payload = _read_exact(stream, size, deadline)
    checksum = _read_exact(stream, 1, deadline)[0]

    expected = size ^ command
    for byte in payload:
        expected ^= byte

    if checksum != expected:
        raise MspChecksumError(
            f"Invalid MSP v1 checksum for command {command}: "
            f"got 0x{checksum:02x}, expected 0x{expected:02x}"
        )

    return MspFrame(version=1, direction=direction, command=command, payload=payload)


def _read_v2_frame(stream: BinaryIO, deadline: float) -> MspFrame:
    direction = MspDirection(_read_exact(stream, 1, deadline)[0])
    header = _read_exact(stream, 5, deadline)
    flags, command, size = struct.unpack("<BHH", header)
    payload = _read_exact(stream, size, deadline)
    checksum = _read_exact(stream, 1, deadline)[0]

    expected = crc8_dvb_s2(header + payload)
    if checksum != expected:
        raise MspChecksumError(
            f"Invalid MSP v2 checksum for command {command}: "
            f"got 0x{checksum:02x}, expected 0x{expected:02x}"
        )

    return MspFrame(
        version=2,
        direction=direction,
        command=command,
        payload=payload,
        flags=flags,
    )


def _read_exact(stream: BinaryIO, size: int, deadline: float) -> bytes:
    data = bytearray()
    while len(data) < size and time.monotonic() < deadline:
        chunk = stream.read(size - len(data))
        if chunk:
            data.extend(chunk)

    if len(data) != size:
        raise MspTimeoutError(f"Timed out reading {size} byte(s)")

    return bytes(data)
