from __future__ import annotations


SAFE_CLI_COMMANDS = {
    "diff",
    "dump",
    "get",
    "gpssats",
    "help",
    "memory",
    "resource",
    "sd_info",
    "showdebug",
    "status",
    "tasks",
    "version",
}


def cli_command_root(command: str) -> str:
    return command.strip().split(maxsplit=1)[0].lower() if command.strip() else ""


def is_safe_cli_command(command: str) -> bool:
    return cli_command_root(command) in SAFE_CLI_COMMANDS

