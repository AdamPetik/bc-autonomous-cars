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

    def getTasksForSolving(self, fifo_array: [Task], iteration) -> [Task]:
        tasks = []
        for task in fifo_array:
            if task.received_by_task_solver <= iteration:
                tasks.append(task)
            else:
                break
        return tasks


    def solveTasks(self, iteration:int):
        #solve tasks with NFTs first
        while len(self.nft_tasks_fifo) > 0:
            nft_task = self.nft_tasks_fifo[0]
            if self.verifyNFTValidForIteration(nft_task.nft, iteration):


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
                self.solving_capacity[iteration] -= required_capacity_per_iteration
            nft = NFT(vehicle,self,start_iteration,end_iteration, required_capacity_per_iteration)
            self.nft_collection[nft.id] = nft
            return nft
        else:
            return None

    def removeNFTFromCollection(self, nft: NFT):
        self.nft_collection.pop(nft.id)

    def verifyNFTValidForIteration(self, nft: NFT, iteration: int):
        if nft.id in self.nft_collection.keys() and iteration in range(nft.valid_from, nft.valid_to):
            return True
        else:
            raise ValueError(f"NFT is not valid for given iteration #{iteration} | NFT: {nft.toJson()}")
            return False

