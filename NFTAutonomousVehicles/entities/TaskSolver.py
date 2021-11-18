from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from src.city.Map import Map
from src.placeable.Placeable import Placeable
from collections import deque

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

    def submitTask(self, task: Task, transfer_time: int):
        task.received_by_task_solver_at = task.created_at + transfer_time
        if(task.nft is None):
            self.basic_tasks_fifo.append(task)
        else:
            if(task.received_by_task_solver_at not in range(task.nft.valid_from, task.nft.valid_to)):
                raise ValueError(f"Submitted task with included NFT is out of reserved timeframe\n"
                                 f"task.received_by_task_solver_at: {task.received_by_task_solver_at}\n"
                                 f"NFT is valid from: {task.nft.valid_from} to: {task.nft.valid_to}")
            self.nft_tasks_fifo.append(task)
        task.status = TaskStatus.SUBMITTED


    def solveTasks(self, iteration:int):
        #solve tasks with NFTs first
        self.solveTasksFromNFTTaskFifo(iteration)

        #solve other tasks without NFTs
        self.solveTasksFromBasicTaskFifo(iteration)

    def solveTasksFromNFTTaskFifo(self, iteration):
        while len(self.nft_tasks_fifo) > 0:
            nft_task = self.nft_tasks_fifo[0]
            if iteration >= nft_task.received_by_task_solver_at:
                if self.verifyNFTValidForIteration(nft_task.nft, iteration):
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

    def getAvailableCapacity(self, iteration: int):
        if iteration not in self.solving_capacity.keys():
            self.solving_capacity[iteration] = self.cpu_count
        return self.solving_capacity[iteration]

    def checkAvailableCapacity(self, start_iteration: int, end_iteration: int, required_capacity: int):
        for iteration in range(start_iteration, end_iteration):
            if self.getAvailableCapacity(iteration) < required_capacity:
                return False
        return True

    def reserveSolvingCapacity(self, start_iteration: int, end_iteration: int, required_capacity_per_iteration: int, vehicle: AutonomousVehicle) -> NFT:
        if self.cpu_count < required_capacity_per_iteration:
            raise ValueError(f"Required capacity per iteration ({required_capacity_per_iteration}) is higher than CPU count ({self.cpu_count}) of Task Solver {self.id}")
        if self.checkAvailableCapacity(start_iteration, end_iteration, required_capacity_per_iteration):
            for iteration in range(start_iteration, end_iteration):
                self.reduceSolvingCapacity(iteration, required_capacity_per_iteration)
            nft = NFT(vehicle, self, start_iteration, end_iteration, required_capacity_per_iteration)
            self.nft_collection[nft.id] = nft
            return nft
        else:
            return None

    def reduceSolvingCapacity(self, iteration: int, capacity: int):
        available_capacity = self.getAvailableCapacity(iteration)
        if available_capacity < capacity:
            raise ValueError(f"Capacity at iteration {iteration} is {available_capacity}, but attempted to reduce by {capacity}")
        self.solving_capacity[iteration] -= capacity

    def removeNFTFromCollection(self, nft: NFT):
        self.nft_collection.pop(nft.id)

    def verifyNFTValidForIteration(self, nft: NFT, iteration: int):
        if nft.id in self.nft_collection.keys() and iteration in range(nft.valid_from, nft.valid_to):
            return True
        else:
            return False

