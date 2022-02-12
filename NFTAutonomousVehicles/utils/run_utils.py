from typing import Callable, Dict, List, Any
from . import dict_utils
from . import json_utils
from .cli import parse_args
from .file_utils import throw_or_remove_file
import multiprocessing
import os
import copy


def parallel_simulation_run(main_fun: Callable[[Dict[str, any]], None]) -> None:
    # parse arguments
    args = parse_args()

    # preprocess config
    config_dicts = []
    if os.path.isdir(args.config_file):
        # config file is directory - collect and preprocess every json file
        # from that directory 
        for file in os.listdir(args.config_file):
            file_path = os.path.join(args.config_file, file)
            if not file_path.endswith('.json'):
                continue
            config_dicts += preprocess_config(json_utils.load_dict(file_path))

    else:
        # config argument is file -> preprocess it
        config_dicts = preprocess_config(
            json_utils.load_dict(args.config_file)
        )

    # raise or remove if there already exists any result directory
    dirs = set([c['result_dir'] for c in config_dicts])
    throw_or_remove_file(dirs, args.force_dirs)

    # set number of processes
    if args.processes <= 0:
        processes = len(config_dicts)
    else:
        processes = min(args.processes, len(config_dicts))

    # run as pool of workers
    with multiprocessing.Pool(processes=processes,) as pool:
        pool.map(main_fun, config_dicts)


def preprocess_config(config_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Preprocess and creates configs from single config (when contains range
    parameters / repeat)

    Args:
        config_dict (Dict[str, Any]): Config.

    Returns:
        List[Dict[str, Any]]: Configs created from input config.
    """
    repeat = config_dict.get('repeat', 1)
    range_params: dict = config_dict.get('range_params', {})
    keys = list(range_params.keys())

    return _handle_range_params(config_dict, keys, range_params, repeat)


def _handle_range_params(
    dict_: dict,
    range_param_keys: list,
    range_params: dict,
    repeat: int,
) -> List[dict]:
    """
    Recursive function, used for generating configs from range params and
    repeat param.

    Args:
        dict_ (dict): Config to be used for generating other configs.
        range_param_keys (list): List of range param keys (key = 'dict path'
            to which variable is going to be changed).
        range_params (dict): Whole dict mapping range param key and value.
        repeat (int): [description]: Number representing how many times run
            the same config.

    Returns:
        List[dict]: List of constructed configs.
    """
    if (len(range_param_keys) == 0):
        # no range param keys -> there is only one config possibility
        return _handle_repeat(dict_, repeat)

    # select first range param and get values
    dict_path = range_param_keys[0]

    range_ = range_params[dict_path]

    dicts = []
    if 'step' in range_:
        start = range_['range'][0]
        end = range_['range'][-1]
        step = range_['step']
        iterator = range(start, end+1, step)
    else:
        iterator = range_['range']

    # iterate over all values
    for index, value in enumerate(iterator):

        tmp_dict = copy.deepcopy(dict_)

        _rename_by_value(
            tmp_dict,
            value_name=range_['name'],
            value=value,
            value_index=index,
        )

        dict_utils.path_set(tmp_dict, dict_path, value)

        # recursion call with other range params
        dicts += _handle_range_params(
            tmp_dict,
            range_param_keys[1:],
            range_params,
            repeat,
        )

    return dicts


def _handle_repeat(dict_, repeat) -> List[dict]:
    """Utility function which duplicates config <repeat> times."""
    res = []
    if repeat <= 1:
        return [copy.deepcopy(dict_)]
    for index in range(repeat):
        repeat_dict = copy.deepcopy(dict_)
        _rename_by_repeat(repeat_dict, index)
        res.append(repeat_dict)
    return res


def _rename_by_value(
    dict_: str,
    value_name: str,
    value: Any,
    value_index: int,
) -> None:
    """Utility function which renames result_name."""
    format = "{}-{}_{}"

    # use value index if value is not instace of simple type
    val_place = value_index if isinstance(value, (list, dict)) else value

    dict_['result_name'] = format.format(
        value_name,
        val_place,
        dict_['result_name'],
    )


def _rename_by_repeat(dict_: str, index: int) -> None:
    """Utility function which renames result_name by repeat value."""
    dict_['result_name'] = dict_['result_name'] + f'-{index+1}'
