import json
import os
from types import SimpleNamespace
from typing import Any, Dict
from . import file_utils as f_utils


def load_to_object(file_path: str) -> object:
    """Loads a json file and converts it into object"""
    with open(file_path, 'r') as f:
        data = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
    return data


def load_dict(file_path: str) -> Dict[str, Any]:
    """Loads a json file into dict"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def save_dict(dict_: dict, file_path: str) -> None:
    """Saves a dict to a json formatted file."""
    f_utils.create_dir_if_not_exist(os.path.dirname(file_path))

    with open(file_path, mode='w') as f:
        json.dump(dict_, f, indent=4)