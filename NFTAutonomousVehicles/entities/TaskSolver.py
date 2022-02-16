# from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
# from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from asyncio import Task
from heapq import heappush, heappop
import heapq
from typing import Generator, List
from NFTAutonomousVehicles.fifo_processing.fifo_processor import FIFOProcessor, ParallelFIFOsProcessing
from NFTAutonomousVehicles.fifo_processing.processable import Processable, TaskCPUProcessable, TaskConnectionProcessable
from NFTAutonomousVehicles.utils.datetime_interval import DatetimeInterval

from src.city.Map import Map
from src.placeable.Placeable import Placeable
from collections import defaultdict, deque
from datetime import datetime, timedelta

from src.common.SimulationClock import *
from decimal import *
import math
import pandas as pd


class TaskSolver(Placeable):

    def __init__(self, locationsTable, map:Map, simulation_dt):
        super(TaskSolver, self).__init__(locationsTable, map)
        # ips - instructions per second
        self.simulation_dt = simulation_dt
        self.uplink_conn_processor: ParallelFIFOsProcessing = None
        self.downlink_conn_processor: ParallelFIFOsProcessing = None
        _ips_available = 70
        self.cpu_processor = FIFOProcessor(_ips_available, self.simulation_dt)
        self.setProcessingIterationDurationInSeconds(0.1)
        self.ips_capacity = {}
        self.nft_collection = {}

        self.nft_tasks_fifo = []
        self.basic_tasks_fifo = []

        self.no_of_successful_tasks = 0
        self.no_of_failed_tasks = 0

        self.resource_blocks = 50
        self.rb_free = defaultdict(lambda: self.resource_blocks)

        self.tx_power = 0.0316 # wats
        self.tx_frequency = 2e9 # Hz
        self.bandwidth = 10e6 # Hz  ==  10 MHz
        self.association_coverage_radius = 900 # m

    @property
    def ips_available(self):
        return self.cpu_processor.power

    @ips_available.setter
    def ips_available(self, value):
        self.cpu_processor.power = value

    def setProcessingIterationDurationInSeconds(self, value):
        self.processing_iteration_duration_seconds = value
        self.round_precision = -3 + math.ceil(abs(Decimal(value).log10()))

    def increaseReputation(self):
        self.no_of_successful_tasks += 1

    def decreaseReputation(self):
        self.no_of_failed_tasks += 1

    def getReputation(self):
        tasks_in_total = self.no_of_successful_tasks + self.no_of_failed_tasks
        return tasks_in_total / self.no_of_successful_tasks

    def receiveTask(self, task, transfer_seconds: int):
        from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
        task.single_transfer_time = transfer_seconds
        task.received_by_task_solver_at = task.created_at + + timedelta(seconds=transfer_seconds)
        if(task.nft.signed == False):
            heappush(self.basic_tasks_fifo, (task.received_by_task_solver_at, task.id, task))
        else:
            if task.nft.valid_from <= task.received_by_task_solver_at <= task.nft.valid_to:
                heappush(self.nft_tasks_fifo, (task.received_by_task_solver_at, task.id, task))
            else:
                raise ValueError(f"Submitted task with included NFT is out of reserved timeframe\n"
                                 f"task.received_by_task_solver_at: {task.received_by_task_solver_at}\n"
                                 f"NFT is valid from: {task.nft.valid_from} to: {task.nft.valid_to}")
        task.status = TaskStatus.SUBMITTED

    # def receive_taks_fifo(self, task):
    #     processable = TaskConnectionProcessable(task, task.created_at)
    #     to_add = (task.created_at, task.id, processable)
    #     self.uplink_conn_processor.fifos[task.vehicle.id].add(to_add)

    def process_uplink(self, timestamp: datetime, logger):
        from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus

        sended = self.uplink_conn_processor.process(timestamp)
        if len(sended) == 0:
            return

        def map_fun(p: TaskCPUProcessable):
            p.entity.received_by_task_solver_at = p.processed_at
            p.entity.solver = self
            p.entity.status = TaskStatus.SUBMITTED

            new_p = TaskCPUProcessable(p.entity, p.processed_at)
            return (p.entity.created_at, p.entity.id, new_p)

        cpu_processables = list(map(map_fun, sended))
        self.cpu_processor.add_list(cpu_processables)

    def process_cpu(self, timestamp: datetime, logger):
        processed = self.cpu_processor.process(timestamp)
        def map_fun(p: TaskConnectionProcessable):
            p.entity.solved_by_task_solver_at = p.processed_at
            new_p = TaskConnectionProcessable(p.entity, p.processed_at)
            return (p.entity.created_at, p.entity.id, new_p)

        processables = list(map(map_fun, processed))
        for p in processables:
            if p[-1].entity.timed_out(p[-1].entity.solved_by_task_solver_at, logger):
                continue
            self.downlink_conn_processor.fifos[p[-1].entity.vehicle.id].add(p)

    def process_downlink(self, timestamp: datetime, logger):
        from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus

        sended: List[TaskConnectionProcessable] = self.downlink_conn_processor.process(timestamp)
        for s in sended:
            s.entity.returned_to_creator_at = s.processed_at
            if s.entity.timed_out(s.processed_at, logger):
                continue
            s.entity.status = TaskStatus.SOLVED
            s.entity.vehicle.receiveSolvedTask(s.entity, logger)

    def solveTasks(self, timestamp, logger):
        #solve tasks with NFTs first
        self.solveTasksFromNFTTaskFifo(timestamp, logger)
        #solve other tasks without NFTs
        self.solveTasksFromBasicTaskFifo(timestamp, logger)


    def solveTasksFromNFTTaskFifo(self, timestamp, logger):
        from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus
        # print(f"Solver: {self.id} solving NFT tasks for timestamp:{timestamp}")
        end_timestamp = timestamp + timedelta(seconds=self.simulation_dt)
        
        while(len(self.nft_tasks_fifo) > 0 and self.nft_tasks_fifo[0][2].received_by_task_solver_at < end_timestamp):
            nft_task = self.nft_tasks_fifo[0][2]

            if not self.verifyNFTValidForTimestamp(nft_task, timestamp):
                ValueError(f"NFT is not valid for given timestamp #{timestamp} | NFT: {nft_task.nft.toJson()}")

            self._process_single_nft_task(
                timestamp,
                end_timestamp,
                nft_task,
                logger
            )

    def _process_single_nft_task(self, step_start, step_end, task, logger):
        from NFTAutonomousVehicles.taskProcessing.Task import TaskStatus
        start = max(task.received_by_task_solver_at, step_start, task.nft.valid_from)
        end = min(task.nft.valid_to, step_end)

        if start > end:
            raise Exception('Task cannot be processed in this iteration..')

        solving_time = task.instruction_count / task.nft.reserved_ips
        available_time = (end - start).total_seconds()

        if solving_time > available_time:
            raise Exception('SIMPLIFICATION: task was not processed in one simulation step')

        solved_at = start + timedelta(seconds=solving_time)

        task.instruction_count = 0
        task.status = TaskStatus.SOLVED
        task.solved_by_task_solver_at = solved_at
        task.returned_to_creator_at = solved_at + timedelta(seconds=task.single_transfer_time)
        task = heappop(self.nft_tasks_fifo)[2]
        task.vehicle.receiveSolvedTask(task, logger)


    def _iter_timestamps(self, start, end=None) -> Generator[datetime, None, None]:
        if end is None:
            end = start + timedelta(seconds=self.simulation_dt)
        timestamp = start
        while timestamp < end:
            yield timestamp
            timestamp += timedelta(seconds=self.processing_iteration_duration_seconds)

    def solveTasksFromBasicTaskFifo(self, timestamp, logger):
        self.process_uplink(timestamp, logger)
        self.process_cpu(timestamp, logger)
        self.process_downlink(timestamp, logger)
        return
        from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus

        end_timestamp = timestamp + timedelta(seconds=self.simulation_dt)
        processing_tasks = []

        while len(self.basic_tasks_fifo) > 0:
            task = self.basic_tasks_fifo[0][2]

            if task.received_by_task_solver_at >= end_timestamp:
                break

            if task.timed_out(timestamp, logger):
                heappop(self.basic_tasks_fifo)
                continue

            processing_tasks.append(heappop(self.basic_tasks_fifo))

            req_capacity = task.nft.reserved_ips * self.processing_iteration_duration_seconds
            start = max(task.received_by_task_solver_at, timestamp)

            # substract time in first cpu iteration if needed (if task arrived
            # between two itter timestamps so not the whole time of
            # self.processing_iteration_duration_seconds is available for
            # computing in first iteration)
            diff_millis = (start - timestamp).total_seconds() * 1000
            itter_millis = self.processing_iteration_duration_seconds * 1000
            reduce_factor = 1 - (int(diff_millis % itter_millis) / 1000)

            for timestamp_iter in self._iter_timestamps(timestamp, end_timestamp):
                if timestamp_iter + timedelta(seconds=self.processing_iteration_duration_seconds) < start:
                    continue

                available_capacity = self.getAvailableCapacityForTimestamp(timestamp_iter)
                capacity_used = min(req_capacity, available_capacity)

                if capacity_used <= 0:
                    continue

                if reduce_factor > 0:
                    capacity_used *= reduce_factor
                    reduce_factor = 0

                task.status = TaskStatus.BEING_PROCESSED
                self.reduceSolvingCapacityForTimestamp(timestamp_iter, min(capacity_used, task.instruction_count))
                task.instruction_count -= capacity_used

                if task.instruction_count <= 0:

                    task.status = TaskStatus.SOLVED

                    iter_time_processing = self.processing_iteration_duration_seconds
                    iter_time_processing *= 1 + task.instruction_count / capacity_used

                    solved_at = timestamp_iter + timedelta(seconds=iter_time_processing)

                    task.solved_by_task_solver_at = solved_at
                    task.returned_to_creator_at = solved_at + timedelta(seconds=task.single_transfer_time)
                    task = processing_tasks.pop()[2]
                    if not task.timed_out(task.returned_to_creator_at, logger):
                        task.vehicle.receiveSolvedTask(task, logger)
                    break
        self.basic_tasks_fifo += processing_tasks
        heapq.heapify(self.basic_tasks_fifo)

        # while len(self.basic_tasks_fifo) > 0 and self.getAvailableCapacityForTimestamp(timestamp) > 0:
        #     basic_task = self.basic_tasks_fifo[0][2]
        #     if timestamp >= basic_task.received_by_task_solver_at:
        #         req_capacity_iter = basic_task.nft.reserved_ips * self.processing_iteration_duration_seconds
        #         capacity_used = min(req_capacity_iter, self.getAvailableCapacityForTimestamp(timestamp))

        #         basic_task.status = TaskStatus.BEING_PROCESSED
        #         basic_task.instruction_count -= capacity_used
        #         self.reduceSolvingCapacityForTimestamp(timestamp, capacity_used)

        #         if basic_task.instruction_count <= 0:
        #             basic_task.status = TaskStatus.SOLVED
        #             basic_task.solved_by_task_solver_at = timestamp
        #             basic_task.returned_to_creator_at = timestamp + timedelta(seconds=basic_task.single_transfer_time)
        #             basic_task = heappop(self.basic_tasks_fifo)[2]
        #             basic_task.vehicle.receiveSolvedTask(basic_task, logger)
        #     else:
        #         break

    # NFT related methods ------
    def getUnsignedNFT(self, start_timestamp, end_timestamp, required_capacity_per_second: int, single_transfer_time, transfer_rate, vehicle):
        from NFTAutonomousVehicles.taskProcessing.NFT import NFT

        if self.ips_available < required_capacity_per_second:
            # raise ValueError(f"SIMPLIFICATION! Required capacity per iteration ({required_capacity_per_second}) is higher than CPU count ({self.ips_available}) of Task Solver {self.id}")
            raise ValueError(f"Required capacity per second ({required_capacity_per_second}) is higher than ips ({self.ips_available}) of Task Solver {self.id} - cant provide have enough power")
        if self.checkAvailableCapacityBetweenTimestamps(start_timestamp, end_timestamp, required_capacity_per_second):
            nft = NFT(vehicle, self, start_timestamp, end_timestamp, required_capacity_per_second, single_transfer_time, transfer_rate, False)
            return nft
        else:
            return None

    def signNFT(self, nft):
        req_capacity_per_iter = nft.reserved_ips * self.processing_iteration_duration_seconds
        self.reduceSolvingCapacityBetweenTimestamps(nft.valid_from, nft.valid_to, req_capacity_per_iter)
        self.reduce_rbs(nft.valid_from, nft.valid_to, nft.reserved_rbs)
        self.nft_collection[nft.id] = nft
        nft.signed = True
        return nft

    def reduce_rbs(self, start: datetime, end: datetime, reserved_rbs: int):
        start_millis = int(round(
                timestampToMillisecondsSinceStart(start), self.round_precision))
        end_millis = int(round(
                timestampToMillisecondsSinceStart(end), self.round_precision))

        step = int(1000*self.processing_iteration_duration_seconds)
        for rounded_millis_since_start in range(start_millis, end_millis, step):
            if self.rb_free[rounded_millis_since_start] >= reserved_rbs:
                self.rb_free[rounded_millis_since_start] -= reserved_rbs
            else:
                raise Exception("Cannot reduce rbs!")

    def max_available_rbs(self, start: datetime, end: datetime) -> int:
        start_millis = int(round(
                timestampToMillisecondsSinceStart(start), self.round_precision))
        end_millis = int(round(
                timestampToMillisecondsSinceStart(end), self.round_precision))
        rbs = self.resource_blocks
        step = int(1000*self.processing_iteration_duration_seconds)
        for rounded_millis_since_start in range(start_millis, end_millis, step):
            rbs = min(rbs, self.rb_free[rounded_millis_since_start])
        return rbs

    def removeNFTFromCollection(self, nft):
        self.nft_collection.pop(nft.id)

    def verifyNFTValidForTimestamp(self, nft, timestamp):
        if nft.id in self.nft_collection.keys() and (nft.valid_from <= timestamp <= nft.valid_to):
            return True
        else:
            return False

    # Capacity reservation methods ------
    def getAvailableCapacityForTimestamp(self, timestamp):
        return self.getAvailableCapacityForMillisecondsSinceStart(timestampToMillisecondsSinceStart(timestamp))

    def getAvailableCapacityForMillisecondsSinceStart(self, milliseconds_since_start):
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.round_precision))
        if rounded_milliseconds_since_start not in self.ips_capacity.keys():
            self.ips_capacity[rounded_milliseconds_since_start] = self.ips_available * self.processing_iteration_duration_seconds
        return self.ips_capacity[rounded_milliseconds_since_start]

    def checkAvailableCapacityBetweenTimestamps(self, start_timestamp, end_timestamp, required_capacity_per_second: int):
        required_capacity_per_iter = required_capacity_per_second * self.processing_iteration_duration_seconds
        start_rounded_milliseconds_since_start = int(
            round(timestampToMillisecondsSinceStart(start_timestamp), self.round_precision))
        end_rounded_milliseconds_since_start = int(
            round(timestampToMillisecondsSinceStart(end_timestamp), self.round_precision))
        step = int(1000*self.processing_iteration_duration_seconds)
        for rounded_millis_since_start in range(start_rounded_milliseconds_since_start,
                                                end_rounded_milliseconds_since_start, step):
            if self.getAvailableCapacityForMillisecondsSinceStart(rounded_millis_since_start) < required_capacity_per_iter:
                return False
        return True

    def reduceSolvingCapacityForMillisecondsSinceStart(self, milliseconds_since_start, required_capacity: int):
        available_capacity = self.getAvailableCapacityForMillisecondsSinceStart(milliseconds_since_start)
        if available_capacity < required_capacity:
            return False
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.round_precision))
        self.ips_capacity[rounded_milliseconds_since_start] -= required_capacity
        return True

    def reduceSolvingCapacityForTimestamp(self, timestamp, required_capacity: int):
        milliseconds_since_start = timestampToMillisecondsSinceStart(timestamp)
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.round_precision))
        available_capacity = self.getAvailableCapacityForMillisecondsSinceStart(rounded_milliseconds_since_start)
        if available_capacity < required_capacity:
            return False
        self.ips_capacity[rounded_milliseconds_since_start] -= required_capacity
        return True

    def reduceSolvingCapacityBetweenTimestamps(self, start_timestamp, end_timestamp, required_capacity_per_iter: int):
        start_rounded_milliseconds_since_start = int(round(timestampToMillisecondsSinceStart(start_timestamp), self.round_precision))
        end_rounded_milliseconds_since_start = int(round(timestampToMillisecondsSinceStart(end_timestamp), self.round_precision))
        step = int(1000*self.processing_iteration_duration_seconds)
        for rounded_millis_since_start in range(start_rounded_milliseconds_since_start, end_rounded_milliseconds_since_start, step):
            if self.getAvailableCapacityForMillisecondsSinceStart(rounded_millis_since_start) >= required_capacity_per_iter:
                self.reduceSolvingCapacityForMillisecondsSinceStart(rounded_millis_since_start, required_capacity_per_iter)
            else:
                return False
        return True

    def printSolvingCapacity(self):
        print("Printing solving capacity--------")
        for millis, capacity in self.ips_capacity.items():
            print(f"{millis} : {capacity}")
