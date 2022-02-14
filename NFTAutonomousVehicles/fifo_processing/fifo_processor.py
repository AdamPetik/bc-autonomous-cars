import heapq
from datetime import datetime, timedelta
from tkinter import E
from typing import Any, Callable, Dict, List, NamedTuple, Tuple, Union

from .processable import Processable


class FIFOProcessor:
    def __init__(self, step_available_power, dt) -> None:
        self.power = step_available_power
        self.dt = dt
        self.process_fifo: List[Tuple[Any, Processable]] = []

    def add_list(self, processables: List[Tuple[Any, Processable]]) -> None:
        for p in processables:
            self.add(p)

    def add(self, processable: Tuple[Any, Processable]) -> None:
            heapq.heappush(self.process_fifo, processable)

    def process_all(self, current_time: datetime) -> List[Processable]:
        available_power = self.power
        processed_time = current_time
        deadline = current_time + timedelta(seconds=self.dt)
        processed: List[Processable] = []

        cond = lambda pf, pt, ap: len(pf) > 0 and deadline > pt and ap > 0

        while cond(self.process_fifo, processed_time, available_power):
            processable = self.process_fifo[0][-1]

            if processable.is_processed():
                processed.append(processable)
                continue

            started_time = max(
                    processed_time, processable.can_start_process_at)

            if started_time > deadline:
                break

            seconds_wasted = (started_time - processed_time).total_seconds()
            available_power -= seconds_wasted / self.dt * self.power

            used_amout = processable.process(available_power)

            if not processable.is_processed():
                break

            processed.append(processable)

            heapq.heappop(self.process_fifo)

            spent_seconds = self._spent_seconds(used_amout)

            processed_time += timedelta(seconds=spent_seconds)
            processable.processed_at = processed_time

            available_power -= used_amout
        return processed

    def process_next(
        self,
        current_time: datetime,
        deadline: datetime = None,
    ) -> Processable:
        if len(self.process_fifo) == 0:
            return None

        start_time = current_time
        processable = self.process_fifo[0][-1]

        if deadline is not None:
            if processable.can_start_process_at >= deadline:
                return None
            start_time = max(current_time, processable.can_start_process_at)
            available_sec = (deadline - start_time).total_seconds()
            available_amount = available_sec / self.dt * self.power # TODO verify
        else:
            available_amount = processable.to_process_amount

        used_amount = processable.process(available_amount)

        if deadline is None and not processable.is_processed():
            raise Exception("Processable not processed after using "
                            "required amount to process")

        spent_seconds = self._spent_seconds(used_amount)
        processed_time = start_time + timedelta(seconds=spent_seconds)

        if not processable.is_processed():
            return None

        processable.processed_at = processed_time
        heapq.heappop(self.process_fifo)
        return processable

    def is_empty(self):
        return len(self.process_fifo) == 0

    def calculate_next_process_time(self) -> float:
        to_process = self.process_fifo[0][-1].to_process_amount
        return to_process / self.power * self.dt

    def _spent_seconds(self, used_amount):
        ratio = used_amount / self.power
        return self.dt * ratio


class Info(NamedTuple):
    processor: FIFOProcessor
    processable: Processable


class ParallelFIFOsProcessing:

    def __init__(
        self,
        fifos: Dict[Any, FIFOProcessor],
        dt: float,
        loop_processed_handler: Callable[[Info], None] = lambda x: None,
    ) -> None:
        self.fifos = fifos
        self.dt = dt
        self.loop_processed_handler = loop_processed_handler

    def process(self, current_time: datetime) -> List[Processable]:
        processing_time = current_time
        deadline = current_time + timedelta(seconds=self.dt)

        processed: List[Processable] = []

        while(processing_time < deadline):
            infos = []

            min_processing_sec = self.get_min_processing_sec()

            loop_deadline = processing_time + timedelta(
                                                    seconds=min_processing_sec)

            loop_deadline = min(deadline, loop_deadline)

            loop_processed, infos = self.process_with_deadline(
                                                processing_time, loop_deadline)
            processed += loop_processed

            if len(infos) > 0:
                self.loop_processed_handler(infos)

            processing_time = loop_deadline

        return sorted(processed, key=lambda p: p.processed_at)

    def get_min_processing_sec(self) -> Union[float, None]:
        min_processing_time = None

        for processor in self.fifos.values():
            if processor.is_empty():
                continue
            p_time = processor.calculate_next_process_time()

            if min_processing_time is None:
                min_processing_time = p_time
            else:
                min_processing_time = min(min_processing_time, p_time)
        return min_processing_time

    def process_with_deadline(
        self,
        processing_time: datetime,
        deadline: datetime
    ) -> Tuple[List[Processable], List[Info]]:
        processed = []
        infos = []
        for processor in self.fifos.values():
            p = processor.process_next(processing_time, deadline)
            if p is not None:
                processed.append(p)
                info = Info(
                    processor,
                    p
                )
                infos.append(info)
        return processed, infos
