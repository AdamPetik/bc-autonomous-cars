import heapq
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

from .processable import Processable


class FIFOProcessor:

    def __init__(self, step_available_power, dt) -> None:
        self.power = step_available_power
        self.dt = dt
        self.process_fifo: List[Tuple[Any, Processable]] = []

    def add_list(self, processables: List[Tuple[Any, Processable]]) -> None:
        """Add list of processables.

        Args:
            processables (List[Tuple[Any, Processable]]): List of tuples where
                the last element of tuple is processable and elements before
                it are used to specify order in the heap.
        """
        for p in processables:
            self.add(p)

    def add(self, processable: Tuple[Any, Processable]) -> None:
        """Add processable.

        Args:
            processable (Tuple[Any, Processable]): Tuple where the last element
                of tuple is processable and elements before
                it are used to specify order in the heap.
        """
        heapq.heappush(self.process_fifo, processable)

    def process(
        self,
        current_time: datetime,
        deadline: datetime = None,
    ) -> List[Processable]:
        """Process the processables.

        Args:
            current_time (datetime): Current datetime.
            deadline (datetime, optional): Specifies the end of the process
                step. Defaults to None, and deadline is created by adding
                self.dt to the current_time.

        Returns:
            List[Processable]: Processed processables.
        """
        available_power = self.power
        processed_time = current_time

        if deadline is None:
            deadline = current_time + timedelta(seconds=self.dt)
        else:
            available_power *= (deadline - current_time).total_seconds() / self.dt

        processed: List[Processable] = []

        cond = lambda pf, pt, ap: len(pf) > 0 and deadline > pt and ap > 0

        while cond(self.process_fifo, processed_time, available_power):
            # get the first processable
            processable = self.process_fifo[0][-1]

            # if its processed add to processed list (should not happen though)
            if processable.is_processed():
                processed.append(processable)
                continue

            # adjust start time of processing
            started_time = max(
                    processed_time, processable.can_start_process_at)

            # break if cannot process
            if started_time > deadline:
                break

            # recalculate avalable power
            seconds_wasted = (started_time - processed_time).total_seconds()
            available_power -= seconds_wasted / self.dt * self.power

            timed_out = processable.is_timed_out(deadline)
            if timed_out:
                # if its going to be timed out during this process step, give
                # the processable just the right amount of power until timeout
                seconds = (processable.timeout_at - started_time).total_seconds()
                to_be_used = seconds / self.dt * self.power
                used_amount = processable.process(to_be_used)
            else:
                # process the processable
                used_amount = processable.process(available_power)

            # if is processable was not processed and not timed out,
            # then we know for sure that all power was used so we can break
            if not (processable.is_processed() or timed_out):
                break

            # calculate time after processing
            spent_seconds = self._spent_seconds(used_amount) + seconds_wasted
            processed_time += timedelta(seconds=spent_seconds)

            if not processable.is_processed() and timed_out:
                # don't add timed out processable to the processed list
                self._on_deadline(processable, processed_time)
            else:
                processed.append(processable)
                processable.processed_at = processed_time

            heapq.heappop(self.process_fifo)

            # decrease available_power by used amount
            available_power -= used_amount
        return processed

    def _on_deadline(self, processable: Processable, time: datetime) -> None:
        pass

    def process_next(
        self,
        current_time: datetime,
        deadline: datetime = None,
    ) -> Processable:
        """Process only next processable if any available. if deadline is
        specified, processes until deadline is reached.
        NOTE: This method has not been tested.. WIP
        """
        if len(self.process_fifo) == 0:
            return None

        start_time = current_time
        processable = self.process_fifo[0][-1]

        if deadline is not None:
            if processable.can_start_process_at >= deadline:
                return None
            start_time = max(current_time, processable.can_start_process_at)
            available_sec = (deadline - start_time).total_seconds()
            available_amount = available_sec / self.dt * self.power
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

    def get_length(self):
        return len(self.process_fifo)

    def calculate_next_process_time(self) -> float:
        to_process = self.process_fifo[0][-1].to_process_amount
        return to_process / self.power * self.dt

    def calculate_next_continues_process_time(
        self,
        current_time: datetime,
    ) -> Union[float, None]:
        """NOTE: not tested, WIP"""
        if self.is_empty():
            return None

        seconds = 0

        ends = max(
            current_time,
            self.get_first_processable().can_start_process_at
        )

        for *_, p in self.process_fifo:
            if p.can_start_process_at > ends:
                break;
            seconds += p.to_process_amount / self.power * self.dt
            ends += timedelta(seconds=seconds)

        if seconds == 0:
            return None

        return seconds

    def get_first_processable(self) -> Processable:
        if len(self.process_fifo) == 0:
            return None
        return self.process_fifo[0][-1]

    def _spent_seconds(self, used_amount):
        ratio = used_amount / self.power
        return self.dt * ratio


class ParallelFIFOsProcessing():
    """
    Groups processing fifos together in order to handle them as a group.
    (for example as a radio connections FIFOs between UEs and base stations)
    """
    def __init__(
        self,
        fifos: Dict[Any, FIFOProcessor],
        dt: float,
    ) -> None:
        self.fifos = fifos
        self.dt = dt

    def process(self, current_time: datetime) -> List[Processable]:
        processed: List[Processable] = []
        deadline = current_time + timedelta(seconds=self.dt)

        for processor in self.fifos.values():
            processed += processor.process(current_time, deadline)

        return sorted(processed, key=lambda x: x.processed_at)



# attempts to create advanced parallel fifo...
# class Info(NamedTuple):
#     processor: FIFOProcessor
#     processable: List[Processable]
# class ParallelFIFOsProcessing:

#     def __init__(
#         self,
#         fifos: Dict[Any, FIFOProcessor],
#         dt: float,
#         loop_processed_handler: Callable[[Info], None] = lambda x: None,
#     ) -> None:
#         self.fifos = fifos
#         self.dt = dt
#         self.loop_processed_handler = loop_processed_handler

#     # def on_event_time(self, time: datetime):
#     #     pass

#     def process(self, current_time: datetime) -> List[Processable]:
#         processing_time = current_time
#         deadline = current_time + timedelta(seconds=self.dt)

#         processed: List[Processable] = []

#         times = self.get_times(current_time, deadline)
#         for event_time in times:
#             loop_processed, infos = self.process_with_deadline(
#                                                    processing_time, event_time)
#             processing_time = event_time
#             processed += loop_processed

#             self.on_event_time(event_time)

#         return processed
#         # while(processing_time < deadline):
#         #     infos = []

#         #     min_processing_sec = self.get_min_processing_sec()

#         #     loop_deadline = processing_time + timedelta(
#         #                                             seconds=min_processing_sec)

#         #     loop_deadline = min(deadline, loop_deadline)

#         #     loop_processed, infos = self.process_with_deadline(
#         #                                         processing_time, loop_deadline)
#         #     processed += loop_processed

#         #     if len(infos) > 0:
#         #         self.loop_processed_handler(infos)

#         #     processing_time = loop_deadline

#         # return sorted(processed, key=lambda p: p.processed_at)

#     def get_times(self, current_time: datetime, deadline: datetime) -> List[datetime]:
#         times = []
#         for processor in self.fifos.values():
#             if processor.is_empty():
#                 continue
#             first_proc = processor.get_first_processable()
#             starts_at = first_proc.can_start_process_at

#             if starts_at >= deadline:
#                 continue

#             times.append(max(starts_at, current_time))

#             processing_secs = processor.calculate_next_continues_process_time(
#                                                                 current_time)
#             if processing_secs is None:
#                 continue

#             ends_at = starts_at + timedelta(seconds=processing_secs)
#             if ends_at > deadline:
#                 continue

#             times.append(ends_at)
#         times.append(deadline)
#         return sorted(list(dict.fromkeys(times)))

#     # def get_min_processing_sec(self) -> Union[float, None]:
#     #     min_processing_time = None

#     #     for processor in self.fifos.values():
#     #         if processor.is_empty():
#     #             continue
#     #         p_time = processor.calculate_next_process_time()

#     #         if min_processing_time is None:
#     #             min_processing_time = p_time
#     #         else:
#     #             min_processing_time = min(min_processing_time, p_time)
#     #     return min_processing_time

#     def process_with_deadline(
#         self,
#         processing_time: datetime,
#         deadline: datetime
#     ) -> Tuple[List[Processable], List[Info]]:
#         processed = []
#         infos = []
#         for processor in self.fifos.values():
#             p = processor.process(processing_time, deadline)
#             if p:
#                 processed += p
#                 info = Info(
#                     processor,
#                     p
#                 )
#                 infos.append(info)
#         return processed, infos

#     # def process_next_with_deadline(
#     #     self,
#     #     processing_time: datetime,
#     #     deadline: datetime
#     # ) -> Tuple[List[Processable], List[Info]]:
#     #     processed = []
#     #     infos = []
#     #     for processor in self.fifos.values():
#     #         p = processor.process_next(processing_time, deadline)
#     #         if p is not None:
#     #             processed.append(p)
#     #             info = Info(
#     #                 processor,
#     #                 p
#     #             )
#     #             infos.append(info)
#     #     return processed, infos
