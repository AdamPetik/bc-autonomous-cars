# from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
# from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from src.city.Map import Map
from src.placeable.Placeable import Placeable
from collections import deque
import datetime
from src.common.SimulationClock import *

class TaskSolver(Placeable):

    def __init__(self, locationsTable, map:Map):
        super(TaskSolver, self).__init__(locationsTable, map)
        self.cpu_count = 8
        self.processing_iteration_duration_seconds = 0.01
        self.solving_capacity = {}
        self.nft_collection = {}
        self.decimal_places = 1

        self.nft_tasks_fifo = deque()
        self.basic_tasks_fifo = deque()

        self.no_of_successful_tasks = 0
        self.no_of_failed_tasks = 0

    def increaseReputation(self):
        self.no_of_successful_tasks += 1

    def decreaseReputation(self):
        self.no_of_failed_tasks += 1

    def getReputation(self):
        tasks_in_total = self.no_of_successful_tasks + self.no_of_failed_tasks
        return tasks_in_total / self.no_of_successful_tasks

    def receiveTask(self, task, transfer_milliseconds: int):
        from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus

        task.received_by_task_solver_at = task.created_at + + datetime.timedelta(milliseconds=transfer_milliseconds)
        if(task.nft is None):
            self.basic_tasks_fifo.append(task)
        else:
            if task.nft.valid_from <= task.received_by_task_solver_at <= task.nft.valid_to:
                self.nft_tasks_fifo.append(task)
            else:
                raise ValueError(f"Submitted task with included NFT is out of reserved timeframe\n"
                                 f"task.received_by_task_solver_at: {task.received_by_task_solver_at}\n"
                                 f"NFT is valid from: {task.nft.valid_from} to: {task.nft.valid_to}")
        task.status = TaskStatus.SUBMITTED


    def solveTasks(self, timestamp):
        #solve tasks with NFTs first
        self.solveTasksFromNFTTaskFifo(timestamp)
        #solve other tasks without NFTs
        self.solveTasksFromBasicTaskFifo(timestamp)


    def solveTasksFromNFTTaskFifo(self, timestamp):
        from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus

        while len(self.nft_tasks_fifo) > 0:
            nft_task = self.nft_tasks_fifo[0]
            if timestamp >= nft_task.received_by_task_solver_at:
                if self.verifyNFTValidForIteration(nft_task.nft, timestamp):
                    nft_task.status = TaskStatus.BEING_PROCESSED
                    nft_task.capacity_needed_to_solve -= nft_task.nft.reserved_cores_each_iteration

                    if nft_task.capacity_needed_to_solve <= 0:
                        nft_task.status = TaskStatus.SOLVED
                        self.nft_tasks_fifo.popleft()
                        nft_task.vehicle.receiveSolvedTask(task=nft_task)
                else:
                    raise ValueError(
                        f"NFT is not valid for given timestamp #{timestamp} | NFT: {nft_task.nft.toJson()}")
            else:
                break

    def solveTasksFromBasicTaskFifo(self, iteration):
        from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus

        while len(self.basic_tasks_fifo) > 0 and self.getAvailableCapacity(iteration) > 0:
            basic_task = self.basic_tasks_fifo[0]
            if iteration >= basic_task.received_by_task_solver_at:

                capacity_used = min(basic_task.capacity_needed_to_solve, self.getAvailableCapacity(iteration))

                basic_task.status = TaskStatus.BEING_PROCESSED
                basic_task.capacity_needed_to_solve -= capacity_used
                self.reduceSolvingCapacity(iteration, capacity_used)

                if basic_task.capacity_needed_to_solve <= 0:
                    basic_task.status = TaskStatus.SOLVED
                    self.basic_tasks_fifo.popleft()
                    basic_task.vehicle.receiveSolvedTask(task=basic_task)
            else:
                break

    # NFT related methods ------
    def getUnsignedNFT(self, start_timestamp, end_timestamp, required_capacity_per_iteration: int, vehicle):
        from NFTAutonomousVehicles.taskProcessing.NFT import NFT

        if self.cpu_count < required_capacity_per_iteration:
            raise ValueError(f"SIMPLIFICATION! Required capacity per iteration ({required_capacity_per_iteration}) is higher than CPU count ({self.cpu_count}) of Task Solver {self.id}")

        if self.checkAvailableCapacityBetweenTimestamps(start_timestamp, end_timestamp, required_capacity_per_iteration):
            nft = NFT(vehicle, self, start_timestamp, end_timestamp, required_capacity_per_iteration, False)
            return nft
        else:
            return None

    def signNFT(self, nft):
        self.reduceSolvingCapacityBetweenTimestamps(nft.valid_from, nft.valid_to, nft.reserved_cores_each_iteration)
        self.nft_collection[nft.id] = nft
        nft.signed = True
        return nft

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
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.decimal_places))
        if rounded_milliseconds_since_start not in self.solving_capacity.keys():
            self.solving_capacity[rounded_milliseconds_since_start] = self.cpu_count
        return self.solving_capacity[rounded_milliseconds_since_start]

    def checkAvailableCapacityBetweenTimestamps(self, start_timestamp, end_timestamp, required_capacity: int):
        start_rounded_milliseconds_since_start = int(
            round(timestampToMillisecondsSinceStart(start_timestamp), self.decimal_places))
        end_rounded_milliseconds_since_start = int(
            round(timestampToMillisecondsSinceStart(end_timestamp), self.decimal_places))

        for rounded_millis_since_start in range(start_rounded_milliseconds_since_start,
                                                end_rounded_milliseconds_since_start, 10 ** self.decimal_places):
            if self.getAvailableCapacityForMillisecondsSinceStart(rounded_millis_since_start) < required_capacity:
                return False
        return True

    def reduceSolvingCapacityForMillisecondsSinceStart(self, milliseconds_since_start, required_capacity: int):
        available_capacity = self.getAvailableCapacityForMillisecondsSinceStart(milliseconds_since_start)
        if available_capacity < required_capacity:
            return False
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.decimal_places))
        self.solving_capacity[rounded_milliseconds_since_start] -= required_capacity
        return True

    def reduceSolvingCapacityForTimestamp(self, timestamp, required_capacity: int):
        milliseconds_since_start = timestampToMillisecondsSinceStart(timestamp)
        rounded_milliseconds_since_start = int(round(milliseconds_since_start, self.decimal_places))
        available_capacity = self.getAvailableCapacityForMillisecondsSinceStart(rounded_milliseconds_since_start)
        if available_capacity < required_capacity:
            return False
        self.solving_capacity[rounded_milliseconds_since_start] -= required_capacity
        return True

    def reduceSolvingCapacityBetweenTimestamps(self, start_timestamp, end_timestamp, required_capacity: int):
        start_rounded_milliseconds_since_start = int(round(timestampToMillisecondsSinceStart(start_timestamp), self.decimal_places))
        end_rounded_milliseconds_since_start = int(round(timestampToMillisecondsSinceStart(end_timestamp), self.decimal_places))
        for rounded_millis_since_start in range(start_rounded_milliseconds_since_start, end_rounded_milliseconds_since_start, 10**self.decimal_places):
            if self.getAvailableCapacityForMillisecondsSinceStart(rounded_millis_since_start) >= required_capacity:
                self.reduceSolvingCapacityForMillisecondsSinceStart(rounded_millis_since_start, required_capacity)
            else:
                return False
        return True

    def printSolvingCapacity(self):
        print("Printing solving capacity--------")
        for millis, capacity in self.solving_capacity.items():
            print(f"{millis} : {capacity}")
