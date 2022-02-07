from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Union


@dataclass(frozen=True)
class DatetimeInterval:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("start must be lesser than end")

    def overlaps(self, other: 'DatetimeInterval', involve_eq=False) -> bool:
        return overlaps(self, other, involve_eq)


def overlaps(
    interval1: Union[Tuple[datetime, datetime], DatetimeInterval],
    interval2: Union[Tuple[datetime, datetime], DatetimeInterval],
    involve_eq=False
) -> bool:
    if isinstance(interval1, tuple):
        interval1 = DatetimeInterval(interval1[0], interval1[1])
    if isinstance(interval2, tuple):
        interval2 = DatetimeInterval(interval2[0], interval2[1])

    if involve_eq:
        return _overlap_eq(interval1, interval2)

    return _overlap_noneq(interval1, interval2)


def _overlap_eq(
    interval1: DatetimeInterval,
    interval2: DatetimeInterval
) -> bool:
    if interval2.end >= interval1.start >= interval2.start:
        return True

    if interval1.end >= interval2.start >= interval1.start:
        return True

    if interval2.end >= interval1.end >= interval2.start:
        return True

    if interval1.end >= interval2.end >= interval1.start:
        return True

    return False


def _overlap_noneq(
    interval1: DatetimeInterval,
    interval2: DatetimeInterval,
) -> bool:
    if interval2.end > interval1.start > interval2.start:
        return True

    if interval1.end > interval2.start > interval1.start:
        return True

    if interval2.end > interval1.end > interval2.start:
        return True

    if interval1.end > interval2.end > interval1.start:
        return True

    return False