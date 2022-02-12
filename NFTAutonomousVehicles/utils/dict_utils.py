import json
from types import SimpleNamespace
from typing import Any, Dict


def path_get(dict_: Dict[str, Any], path: str, default=...) -> Any:
    """
    Get value from dict at specified path.

    Args:
        dict_ (Dict[str, Any]): Dictionary with string keys.
        path (str): Dict keys in string format seperated by '.'.
        default ([type], optional): Default value returned if dict does't
            contain value at specified path. If not specified, and value isn't
            at specified path, KeyError si raised.

    Raises:
        e: KeyError: raised if default value is not specified and value isn't
            at specified path

    Returns:
        Any: Dict value or default value.
    """
    throw = False
    keys = path.split('.')

    if default is ...:
        throw = True

    x = dict_
    for key in keys:
        try:
            if key.startswith('[') and key.endswith(']'):
                x = x[int(key[1:-1])]
                continue
            x = x.get(key)
        except KeyError as e:
            if throw:
                raise e
            return default
    return x


def path_set(dict_: Dict[str, Any], path: str, value: Any) -> None:
    """
    Set value from dict at specified path.

    Args:
        dict_ (Dict[str, Any]): Dictionary with string keys.
        path (str): Dict keys in string format seperated by '.'.
        value (Any): Value to be set.
    """
    keys = path.split('.')

    if len(keys) == 1:
        dict_[path] = value

    last_key = keys[-1]
    keys = keys[:-1]

    x = dict_

    for key in keys:
        if key.startswith('[') and key.endswith(']'):
            x = x[int(key[1:-1])]
            continue
        x = x.get(key)

    if last_key.startswith('[') and last_key.endswith(']'):
        x[int(last_key[1:-1])] = value
        return

    x[last_key] = value


def to_object(dict_: Dict[str, Any]):
    """Create nasted SimpleNamspace from dict."""
    return json.loads(
        json.dumps(dict_),
        object_hook=lambda item: SimpleNamespace(**item)
    )


def from_simple_namespace(sn) -> dict:
    """Converts a simple namespace to a dict"""
    return json.loads(json.dumps(sn, default=lambda s: vars(s)))