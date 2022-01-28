from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
import enum
from src.common.SimulationClock import *
from src.common.UniqueID import UniqueID


class TaskStatus(enum.Enum):
    SUBMITTED = 1
    BEING_PROCESSED = 2
    SOLVED = 3
    PROCESSING_FAILED = 4
    TASK_TIMED_OUT = 5


class Task:

    def __init__(self, vehicle=None, solver=None,
                 transfer_rate=None, size_in_megabytes=None, capacity_needed_to_solve=None, solving_time=None, limit_time=None,
                 created_at=None, deadline_at=None,
                 nft=None,
                 name=None):
        uid = UniqueID()
        self.id = uid.getId()
        self.vehicle = vehicle
        self.solver = solver
        self.capacity_needed_to_solve = capacity_needed_to_solve
        self.solving_time = solving_time
        self.limit_time = limit_time

        self.size_in_megabytes = size_in_megabytes
        self.transfer_rate = transfer_rate
        self.status: TaskStatus = None

        self.created_at = created_at
        self.deadline_at = deadline_at

        self.received_by_task_solver_at = None
        self.solved_by_task_solver_at = None
        self.returned_to_creator_at = None

        self.nft = nft
        self.name = name

    def getTotalTimeSpent(self):
        return self.returned_to_creator_at - self.created_at

    def getDeadlineInterval(self):
        return self.deadline_at - self.created_at