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
        self.solving_capacity = {}
        self.nft_collection = {}

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
                        f"NFT is not valid for given iteration #{iteration} | NFT: {nft_task.nft.toJson()}")
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

    def getAvailableCapacity(self, timestamp):
        rounded_millis_timestamp = timestampToMillisecondsSinceStartRoundendToTen(timestamp)
        if rounded_millis_timestamp not in self.solving_capacity.keys():
            self.solving_capacity[rounded_millis_timestamp] = self.cpu_count
        return self.solving_capacity[rounded_millis_timestamp]

    def checkAvailableCapacity(self, start_timestamp, end_timestamp, required_capacity: int):
        rounded_millis_start_timestamp = timestampToMillisecondsSinceStartRoundendToTen(start_timestamp)
        rounded_millis_end_timestamp = timestampToMillisecondsSinceStartRoundendToTen(end_timestamp)

        for rounded_millis_timestamp in range(rounded_millis_start_timestamp, rounded_millis_end_timestamp, 10):
            if self.getAvailableCapacity(rounded_millis_timestamp) < required_capacity:
                return False
        return True

    def reserveSolvingCapacity(self, start_timestamp, end_timestamp, required_capacity_per_iteration: int, vehicle):
        from NFTAutonomousVehicles.taskProcessing.NFT import NFT

        if self.cpu_count < required_capacity_per_iteration:
            raise ValueError(f"SIMPLIFICATION! Required capacity per iteration ({required_capacity_per_iteration}) is higher than CPU count ({self.cpu_count}) of Task Solver {self.id}")

        rounded_millis_start_timestamp = timestampToMillisecondsSinceStartRoundendToTen(start_timestamp)
        rounded_millis_end_timestamp = timestampToMillisecondsSinceStartRoundendToTen(end_timestamp)

        if self.checkAvailableCapacity(start_timestamp, end_timestamp, required_capacity_per_iteration):
            for rounded_millis_timestamp in range(rounded_millis_start_timestamp, rounded_millis_end_timestamp, 10):
                self.reduceSolvingCapacity(rounded_millis_timestamp, required_capacity_per_iteration)
            nft = NFT(vehicle, self, start_timestamp, end_timestamp, required_capacity_per_iteration)
            self.nft_collection[nft.id] = nft
            return nft
        else:
            return None

    def reduceSolvingCapacity(self, timestamp, capacity: int):
        rounded_millis_timestamp = timestampToMillisecondsSinceStartRoundendToTen(timestamp)
        available_capacity = self.getAvailableCapacity(rounded_millis_timestamp)
        if available_capacity < capacity:
            raise ValueError(f"Capacity at rounded_millis_timestamp {rounded_millis_timestamp} is {available_capacity}, but attempted to reduce by {capacity}")
        self.solving_capacity[rounded_millis_timestamp] -= capacity

    def removeNFTFromCollection(self, nft):
        self.nft_collection.pop(nft.id)

    def verifyNFTValidForTimestamp(self, nft, timestamp):
        if nft.id in self.nft_collection.keys() and (nft.valid_from <= timestamp <= nft.valid_to):
            return True
        else:
            return False

