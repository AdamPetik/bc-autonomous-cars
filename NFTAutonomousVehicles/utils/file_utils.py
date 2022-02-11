import os
from pathlib import Path
import shutil
from typing import Iterable


def create_dir_if_not_exist(path: str) -> None:
    """creates dir path if doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)


def throw_or_remove_file(paths: Iterable[str], force_remove: bool):
    """
    Check whether paths exists. If force_remove is true, existing files are
    removed otherwise if there exists any file, exception is thrown.

    Args:
        paths (Iterable[str]): List of paths.
        force_remove (bool): Whether to remove file if exists or not.

    Raises:
        FileExistsError: When force_remove is False and some file does not
            exists.
    """
    for path in paths:
        if os.path.exists(path):
            if not force_remove:
                raise FileExistsError(
                    f'Directory "{path}" already exists. '
                    'You can use --force-dirs flag to force delete.'
                )

            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)