from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
import enum

class Task:

    def __init__(self, vehicle: AutonomousVehicle, solver: TaskSolver,
                 transfer_rate: int, size_in_megabytes: int,
                 created_at: int, deadline_at: int,
                 nft: NFT = None):
        self.vehicle = vehicle
        self.solver = solver
        self.iterations_needed_to_solve = None

        self.size_in_megabytes = size_in_megabytes
        self.transfer_rate = transfer_rate
        self.status: TaskStatus = None

        self.created_at = created_at
        self.deadline_at = deadline_at

        self.received_by_task_solver_at = None
        self.solved_by_task_solver_at = None
        self.returned_to_creator_at = None

        self.nft = nft



class TaskStatus(enum.Enum):
    SUBMITTED = 1
    BEING_PROCESSED = 2
    SOLVED = 3
