from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.taskProcessing.CommonFunctionsForTaskSolving import CommonFunctionsForTaskSolving
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
import enum

from NFTAutonomousVehicles.taskProcessing.Task import Task
from src.IISMotion import IISMotion
from src.city.Map import Map
from src.common.CommonFunctions import CommonFunctions


class SolverFinder:
    def __init__(self):
        self.com = CommonFunctions()
        self.com_solving = CommonFunctionsForTaskSolving()


    def searchForBestProviders(self, route_with_timestamps, iismotion: IISMotion, collection_names, task: Task):
        # output should be dict: key:timestamp  value:NFT for given timestamp

        effective_radius = self.com_solving.getEffectiveDistanceOfConnection(time_limit=(task.deadline_at - task.created_at),
                                                                             task_size_in_megabytes=task.size_in_megabytes)
        for location_timestamp in route_with_timestamps:
            timestamp = location_timestamp[0]
            location = location_timestamp[1]

            #radius, collectionNames, location=Location
            solvers_list = iismotion.mapGrid.getActorsInRadius(effective_radius, collection_names, location)

            #nepotrebujeme mat spojitu rezervaciu u konkretneho providera, staci pre kazdy tick vybrat najlepsieho
            if not solvers_list:
                raise ValueError(f"Could not find solver for {location.toJson()} within radius of {effective_radius}m")

            for solver in solvers_list:
                #self, start_iteration: int, end_iteration: int, required_capacity: int
                solver.checkAvailableCapacity()




