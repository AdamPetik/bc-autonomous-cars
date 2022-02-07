import json

from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from src.common.UniqueID import UniqueID


class NFT:

    def __init__(self, owner: AutonomousVehicle, solver: TaskSolver, valid_from, valid_to, reserved_cores, single_transfer_time, transfer_rate, signed, reserved_rbs=0):
        uid = UniqueID()
        self.id = uid.getId()

        self.owner = owner
        self.solver = solver
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.reserved_cores_each_iteration = reserved_cores
        self.single_transfer_time = single_transfer_time
        self.transfer_rate = transfer_rate
        self.signed = signed

        self.reserved_rbs = reserved_rbs

    def toJson(self) ->str:
        output = {}
        output["owner"] = self.owner.id
        output["solver"] = self.solver.id
        output["valid_from"] = self.valid_from.strftime('%Y-%m-%d %H:%M:%S.%f')
        output["valid_to"] = self.valid_to.strftime('%Y-%m-%d %H:%M:%S.%f')
        output["reserved_cores_each_iteration"] = self.reserved_cores_each_iteration
        output["single_transfer_time"] = self.single_transfer_time
        output["signed"] = self.signed
        output["transfer_rate"] = self.transfer_rate
        output["reserved_rbs"] = self.reserved_rbs
        return json.dumps(output, indent=2)