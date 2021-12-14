from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
import enum

from src.common.UniqueID import UniqueID


class Task:

    def __init__(self, vehicle, solver: TaskSolver,
                 transfer_rate: int, size_in_megabytes: int, capacity_needed_to_solve : int,
                 created_at: int, deadline_at: int,
                 nft = None,
                 name = None):
        uid = UniqueID()
        self.id = uid.getId()
        self.vehicle = vehicle
        self.solver = solver
        self.capacity_needed_to_solve = capacity_needed_to_solve

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


class TaskStatus(enum.Enum):
    SUBMITTED = 1
    BEING_PROCESSED = 2
    SOLVED = 3
    PROCESSING_FAILED = 4
    TASK_TIMED_OUT = 5
