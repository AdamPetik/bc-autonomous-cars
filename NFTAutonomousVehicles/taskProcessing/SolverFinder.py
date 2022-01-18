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

    # def searchForBestProvider(self, task, timestamp, location, task_solvers)->NFT:
    #     effective_radius = self.com_solving.getEffectiveDistanceOfConnection(
    #         time_limit=(task.deadline_at - task.created_at),
    #         task_size_in_megabytes=task.size_in_megabytes)
    #
    #         solvers_list = iismotion.mapGrid.getActorsInRadius(effective_radius, collection_names, location)
    #
    # if not solvers_list:
    #     raise ValueError(f"Could not find solver for {location.toJson()} within radius of {effective_radius}m")
    #
    # def searchForBestProvidersUselessVersion(self, timestamps_locations, iismotion: IISMotion, collection_names, task: Task):
    #     #output in form of dictinary:  key:timestamp  value:nft
    #     timestamp_nft = {}
    #
    #     #calculte max distance of solver based on sample task (so that task processing will be finished within deadline)
    #     effective_radius = self.com_solving.getEffectiveDistanceOfConnection(time_limit=(task.deadline_at - task.created_at),
    #                                                                          task_size_in_megabytes=task.size_in_megabytes)
    #
    #     #find solver with available capacity and within distance
    #     for timestamp_location in timestamps_locations:
    #         start_timestamp = timestamp_location[0]
    #         end_timestamp = start_timestamp + (task.deadline_at - task.created_at) #end based on deadline of sample task
    #         location = timestamp_location[1]
    #
    #         #get all solvers within effective_radius
    #         solvers_list = iismotion.mapGrid.getActorsInRadius(effective_radius, collection_names, location)
    #
    #         if not solvers_list:
    #             raise ValueError(f"Could not find solver for {location.toJson()} within radius of {effective_radius}m")
    #
    #         #find first solver with available solving capacity
    #         nft = None
    #         for solver in solvers_list:
    #             #direct allocation attempt
    #             nft = solver.reserveSolvingCapacity(start_timestamp, end_timestamp, task.capacity_needed_to_solve, task.vehicle)
    #             if nft is not None:
    #                 #FOUND solver with available capacity! we can break loop
    #                 break
    #         #in case nft is still None, no solver with available capacity was found
    #         if nft is None:
    #             raise ValueError(f"None of the solvers for{location.toJson()} had available solving capacity")
    #         else:
    #             timestamp_nft[start_timestamp] = nft
    #     return timestamp_nft

