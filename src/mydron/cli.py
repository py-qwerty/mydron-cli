from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .health import DEFAULT_BOARD, run_quick_health
from .inav import InavClient
from .safety import cli_command_root, is_safe_cli_command
from .serial_port import list_serial_ports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mydron",
        description="CLI para comunicarse con controladoras INAV por USB/MSP.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ports", help="Lista los puertos serie disponibles.")

    info = subparsers.add_parser("info", help="Lee informacion basica de la placa.")
    info.add_argument("--port", required=True, help="Puerto serie, por ejemplo COM5.")
    info.add_argument("--baud", type=int, default=115200, help="Baudrate serie.")

    status = subparsers.add_parser("status", help="Lee estado basico MSP.")
    status.add_argument("--port", required=True, help="Puerto serie, por ejemplo COM5.")
    status.add_argument("--baud", type=int, default=115200, help="Baudrate serie.")

    quick_health = subparsers.add_parser(
        "quick-health",
        help="Ejecuta un health check rapido especifico de una placa.",
    )
    quick_health.add_argument("--port", required=True, help="Puerto serie, por ejemplo COM5.")
    quick_health.add_argument("--baud", type=int, default=115200, help="Baudrate serie.")
    quick_health.add_argument(
        "--board",
        default=DEFAULT_BOARD,
        help=f"Perfil de placa. Por defecto: {DEFAULT_BOARD}.",
    )
    quick_health.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Carpeta donde guardar el informe. Por defecto usa la carpeta de la placa.",
    )
    quick_health.add_argument(
        "--no-color",
        action="store_true",
        help="Desactiva colores ANSI en la salida de terminal.",
    )

    dump = subparsers.add_parser("dump-cli", help="Guarda un dump CLI de INAV.")
    dump.add_argument("--port", required=True, help="Puerto serie, por ejemplo COM5.")
    dump.add_argument("--baud", type=int, default=115200, help="Baudrate serie.")
    dump.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Ruta de salida para el backup, por ejemplo backups\\dump.txt.",
    )
    dump.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Tiempo maximo de espera para el dump.",
    )

    cli = subparsers.add_parser("cli", help="Ejecuta un comando en la CLI textual INAV.")
    cli.add_argument("--port", required=True, help="Puerto serie, por ejemplo COM5.")
    cli.add_argument("--baud", type=int, default=115200, help="Baudrate serie.")
    cli.add_argument(
        "--allow-unsafe",
        action="store_true",
        help="Permite comandos CLI que pueden cambiar configuracion o estado.",
    )
    cli.add_argument(
        "cli_command",
        nargs=argparse.REMAINDER,
        help="Comando CLI INAV, por ejemplo: status, get nav, diff all.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ports":
        ports = list_serial_ports()
        if not ports:
            print("No se encontraron puertos serie.")
            return 1

        for port in ports:
            print(f"{port.device}\t{port.description}")
        return 0

    if args.command == "info":
        try:
            with InavClient(args.port, baud=args.baud) as client:
                info = client.read_info()
        except Exception as exc:
            print(f"Error leyendo info: {exc}", file=sys.stderr)
            return 1

        api = info.api_version
        print(f"Puerto: {args.port}")
        print(f"Baud: {args.baud}")
        print(f"MSP API: {api['major']}.{api['minor']} (protocol {api['protocol']})")
        print(f"Firmware: {info.fc_variant} {info.fc_version}")
        print(f"Board ID: {info.board_info.get('identifier', 'unknown')}")
        if "target_name" in info.board_info:
            print(f"Target: {info.board_info['target_name']}")
        if "hardware_revision" in info.board_info:
            print(f"Hardware revision: {info.board_info['hardware_revision']}")
        print(f"Build: {info.build_info}")
        return 0

    if args.command == "status":
        try:
            with InavClient(args.port, baud=args.baud) as client:
                status = client.read_status()
        except Exception as exc:
            print(f"Error leyendo status: {exc}", file=sys.stderr)
            return 1

        for key, value in status.items():
            print(f"{key}: {value}")
        return 0

    if args.command == "quick-health":
        try:
            output, _report_path = run_quick_health(
                port=args.port,
                baud=args.baud,
                board=args.board,
                out_dir=args.out_dir,
                color=not args.no_color,
            )
        except Exception as exc:
            print(f"Error ejecutando quick-health: {exc}", file=sys.stderr)
            return 1

        print(output)
        return 0

    if args.command == "dump-cli":
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with InavClient(args.port, baud=args.baud) as client:
                client.dump_cli(args.out, timeout=args.timeout)
        except Exception as exc:
            print(f"Error creando dump CLI: {exc}", file=sys.stderr)
            return 1

        print(f"Dump guardado en: {args.out}")
        return 0

    if args.command == "cli":
        cli_command = " ".join(args.cli_command).strip()
        if not cli_command:
            print("Falta el comando CLI INAV.", file=sys.stderr)
            return 2

        if not args.allow_unsafe and not is_safe_cli_command(cli_command):
            root = cli_command_root(cli_command)
            print(
                "Comando bloqueado por seguridad: "
                f"{root}. Usa --allow-unsafe solo si ya hiciste backup "
                "y entiendes el efecto.",
                file=sys.stderr,
            )
            return 1

        try:
            with InavClient(args.port, baud=args.baud) as client:
                client.enter_cli()
                try:
                    output = client.cli_command(cli_command)
                finally:
                    try:
                        client.exit_cli()
                    except Exception:
                        pass
        except Exception as exc:
            print(f"Error ejecutando CLI INAV: {exc}", file=sys.stderr)
            return 1

        print(output)
        return 0

    parser.error(f"Comando no reconocido: {args.command}")
    return 2
