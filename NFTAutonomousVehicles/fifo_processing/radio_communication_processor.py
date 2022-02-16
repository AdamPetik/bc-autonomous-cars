from datetime import datetime
from typing import Any, Callable, Dict, List
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor, ParallelFIFOsProcessing
from NFTAutonomousVehicles.fifo_processing.processable import Processable
from NFTAutonomousVehicles.utils.sinr_map import SINRMap


class SimpleBSRadioCommProcessor(ParallelFIFOsProcessing):

    def __init__(
        self,
        bs: TaskSolver,
        fifos: Dict[Any, FIFOProcessor],
        dt: float,
        datarate_calc: Callable,
    ) -> None:
        super().__init__(fifos, dt)
        self.bs = bs
        self.datarate_calc = datarate_calc

    def process(self, current_time: datetime) -> List[Processable]:
        # recalculate datarate
        connections = len(self.fifos)
        for ue_id, processsor in self.fifos.items():
            processsor.power = self.datarate_calc(ue_id, self.bs, connections)

        return super().process(current_time)


# class BSRadioComunicationProcessor(ParallelFIFOsProcessing):
#     # all_bss: List[TaskSolver] = []
#     # sinr_map: SINRMap = None

#     def __init__(
#         self,
#         bs: TaskSolver,
#         fifos: Dict[Any, FIFOProcessor],
#         dt: float,
#         datarate_calc: Callable,
#     ) -> None:
#         super().__init__(fifos, dt)
#         self.bs = bs
#         self.datarate_calc = datarate_calc

#     def on_event_time(self, time: datetime):
#         currently_active = 0
#         processors = list(self.fifos.values())
#         for processor in processors:
#             if processor.is_empty():
#                 continue
#             processable = processor.get_first_processable()
#             if processable.can_start_process_at <= time:
#                 currently_active += 1

#         for processor in processors:
#             if processor.is_empty():
#                 continue
#             processable = processor.get_first_processable()
#             vehicle_loc = processable.entity.vehicle.getLocation()

#             datarate = self.datarate_calc(
#                     vehicle_loc, self.bs, currently_active)

#             processor.power = datarate
