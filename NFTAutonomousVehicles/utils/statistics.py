import os
import subprocess
from typing import Any, Dict, Union
from . import json_utils
from .singleton import Singleton
from collections import defaultdict
from enum import Enum


class TimestampEvent(Enum):
    pass


class IncrementalEvent(Enum):
    DISCARDED_TASK = 'discarded_task'
    GENERATED_TASK = 'generated_task'


class MeanEvent(Enum):
    ROUTE_PROLONGATION = 'route_prolongation'


class Statistics(metaclass=Singleton):
    """Singleton used for submitting statistics."""

    def __init__(self) -> None:
        self._timestamp_records = defaultdict(lambda: [])
        self._incremental_records = defaultdict(lambda: 0)
        self._mean_records = defaultdict(lambda: 0)
        self._mean_couter = defaultdict(lambda: 0)

    def timestamp_event(
        self,
        event: Union[TimestampEvent, str],
        value: Any,
        timestamp: Any
    ) -> None:
        """Record event depended on time.

        Args:
            event (Union[TimestampEvent, str]): Event name.
            value (Any): Value to be recorded.
            timestamp (Any): Any value representing timestamp.
        """
        event_str = _event_str(event)

        self._timestamp_records[event_str].append({
            'value': value,
            'timestamp': timestamp,
        })

    def incremental_event(
        self,
        event: Union[IncrementalEvent, str],
        increment_amount: float = 1,
    ) -> None:
        """Record incremental event by specified value.

        Args:
            event (Union[IncrementalEvent, str]): Event name.
            increment_amount (float, optional): Value to be added.
                Defaults to 1.
        """
        event_str = _event_str(event)
        self._incremental_records[event_str] += increment_amount

    def mean_event(self, event: Union[MeanEvent, str], value: float) -> None:
        """Record mean event - mean is recalculated with a new value.

        Args:
            event (Union[MeanEvent, str]): Event name.
            value (float): Value to be added to the current mean.
        """
        event_str = _event_str(event)

        previous_mean = self._mean_records[event_str]
        counter = self._mean_couter[event_str]

        new_mean = (counter * previous_mean + value) / (counter + 1)

        self._mean_records[event_str] = new_mean
        self._mean_couter[event_str] = counter + 1

    def reset(self) -> None:
        self._timestamp_records.clear()
        self._incremental_records.clear()
        self._mean_records.clear()
        self._mean_couter.clear()

    def save_json(
        self,
        dir_path: str,
        file_name: str,
        sufix: str = None,
        prefix: str = None,
        additional_info: dict = {},
        config: Dict[str, Any] = None,
    ) -> None:
        """Save statistics to a file in json format.

        Args:
            dir_path (str): Directory path.
            file_name (str): File name without '.json' ending.
            sufix (str, optional): File name sufix. Defaults to None.
            prefix (str, optional): File name prefix. Defaults to None.
            additional_info (dict, optional): Dict format data to additionaly
                save into json. Defaults to {}.
        """
        dict_ = {
            'incremental_events': self._incremental_records,
            'mean_events': self._mean_records,
            'timestamp_events': self._timestamp_records,
            'commit': _get_commit_hash(),
            'additional_info': additional_info,
        }
        if config is not None:
            dict_['config'] = config
        # task lost rate calculation
        DTs = self._incremental_records[IncrementalEvent.DISCARDED_TASK.value]
        GTs = self._incremental_records[IncrementalEvent.GENERATED_TASK.value]

        if GTs != 0:
            dict_['incremental_events']['task_lost_rate'] =  DTs / GTs * 100

        if sufix is not None:
            file_name += f'_{sufix}'

        if prefix is not None:
            file_name = f'{prefix}_{file_name}'

        full_path = os.path.join(dir_path, file_name + '.json')

        json_utils.save_dict(dict_, full_path)


def _event_str(event: Union[TimestampEvent, str]):
    return event if isinstance(event, str) else event.value

def _get_commit_hash():
    return subprocess.check_output(
        ['git', 'rev-parse', 'HEAD']
    ).decode('ascii').strip()


def _test():
    # test functionality
    s = Statistics()
    mean_e = 'test_mean'
    timestamp_e = 'test_timestamp'

    s.incremental_event(IncrementalEvent.DISCARDED_TASK, 2)
    s.incremental_event(IncrementalEvent.GENERATED_TASK, 3)

    s.mean_event(mean_e, 20)
    s.mean_event(mean_e, 30)

    s.timestamp_event(timestamp_e, 20, timestamp=1)
    s.timestamp_event(timestamp_e, 30, timestamp=2)

    s.save_json(
        dir_path='./test_statistics',
        file_name='stats',
        sufix='sufix',
        prefix='prefix',
        additional_info={'ues_count': 30}
    )

# if __name__ == '__main__':
#     _test()