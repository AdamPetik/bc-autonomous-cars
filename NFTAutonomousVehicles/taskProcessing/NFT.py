import json

from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from src.common.UniqueID import UniqueID


class NFT:

    def __init__(self, owner: AutonomousVehicle, solver: TaskSolver, valid_from, valid_to, reserved_cores, signed):
        uid = UniqueID()
        self.id = uid.getId()

        self.owner = owner
        self.solver = solver
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.reserved_cores_each_iteration = reserved_cores
        self.signed = signed

    def toJson(self) ->str:
        output = {}
        output["owner"] = self.owner.id
        output["solver"] = self.solver.id
        output["valid_from"] = self.valid_from
        output["valid_to"] = self.valid_to
        output["reserved_cores_each_iteration"] = self.reserved_cores_each_iteration
        output["signed"] = self.signed
        return json.dumps(output, indent=2)