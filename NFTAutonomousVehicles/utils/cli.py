import argparse
from typing import NamedTuple


class CLIArgs(NamedTuple):
    config_file: str
    processes: int
    force_dirs: bool

def parse_args() -> CLIArgs:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config-file",
        dest='config_file',
        default='config_files/configuration.json',
        type=str,
    )

    parser.add_argument("--processes", default=-1, type=int)
    parser.add_argument(
        "--force-dirs",
        dest='force_dirs',
        action='store_true',
    )

    args = parser.parse_args()

    return CLIArgs(
        config_file=args.config_file,
        processes=args.processes,
        force_dirs=args.force_dirs
    )