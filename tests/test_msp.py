from io import BytesIO

from mydron.msp import (
    MSP_API_VERSION,
    build_msp_v1_request,
    build_msp_v2_request,
    parse_board_info,
    read_frame,
)
from mydron.safety import is_safe_cli_command


def test_build_msp_api_version_request() -> None:
    assert build_msp_v1_request(MSP_API_VERSION) == b"$M<\x00\x01\x01"


def test_read_msp_v1_frame() -> None:
    frame = read_frame(BytesIO(b"$M>\x03\x01\x02\x08\x00\x08"))

    assert frame.version == 1
    assert frame.command == MSP_API_VERSION
    assert frame.payload == b"\x02\x08\x00"


def test_build_and_read_msp_v2_frame() -> None:
    request = build_msp_v2_request(100)

    assert request == b"$X<\x00d\x00\x00\x00\x8f"


def test_parse_board_info() -> None:
    board = parse_board_info(b"SB44\x00\x00\x02\x03\x0fSPEEDYBEEF405V4")

    assert board["identifier"] == "SB44"
    assert board["target_name"] == "SPEEDYBEEF405V4"


def test_cli_safety_allows_read_commands() -> None:
    assert is_safe_cli_command("diff all")
    assert is_safe_cli_command("get nav")


def test_cli_safety_blocks_write_commands() -> None:
    assert not is_safe_cli_command("set nav_rth_altitude = 5000")
    assert not is_safe_cli_command("motor 0 1100")
