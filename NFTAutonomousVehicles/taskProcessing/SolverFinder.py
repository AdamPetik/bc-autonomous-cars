from datetime import datetime, timedelta
from typing import List, Tuple, Union
import heapq
from NFTAutonomousVehicles.utils.sinr_map import SINRMap

from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.taskProcessing.CommonFunctionsForTaskSolving import CommonFunctionsForTaskSolving
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.utils import sinr
from NFTAutonomousVehicles.utils.radio_data_rate import RadioDataRate


class SolverFinder:
    def __init__(self, sinr_map: SINRMap):
        self.com = CommonFunctions()
        self.com_solving = CommonFunctionsForTaskSolving()
        self.sinr_map = sinr_map

    def searchForTaskSolver(self,  mapGrid, task, solver_collection_names):
        effective_radius = self.com_solving.getEffectiveDistanceOfConnection(
            solving_time= task.solving_time,
            time_limit=task.limit_time,
            task_size_in_megabytes=task.size_in_megabytes)

        solvers_list = mapGrid.getActorsInRadius(effective_radius, solver_collection_names, task.vehicle.getLocation())
        # if not solvers_list:
            # print(f"Could not find solver for {task.vehicle.getLocation().toString()} within radius of {effective_radius}m")
            # raise ValueError(f"Could not find solver for {task.vehicle.getLocation().toString()} within radius of {effective_radius}m")

        start_timestamp = task.created_at
        for solver in solvers_list:
            # direct allocation attempt
            single_transfer_time = self.com_solving.getTransferTimeInSeconds(task.vehicle.getLocation(), solver.getLocation(), task.size_in_megabytes)
            transfer_rate = self.com_solving.getConnectionSpeedInMegabytesPerSecondBetweenLocations(task.vehicle.getLocation(), solver.getLocation())
            end_timestamp = start_timestamp +timedelta(seconds=task.solving_time ) + timedelta(seconds=(2 * single_transfer_time))
            unsigned_nft = solver.getUnsignedNFT(start_timestamp, end_timestamp, task.instruction_count / task.solving_time, single_transfer_time, transfer_rate, task.vehicle)
            if unsigned_nft is not None:
                # print("AVAILABLE SOLVER")
                return unsigned_nft

        # print(f"Solver was not available for timestamp {start_timestamp}-{task.deadline_at} capacity:{task.instruction_count}")

        return None

    def searchForTaskSolverSINR(
        self,
        map_grid,
        task: Task,
        solver_collection_names,
    ) -> Union[None,NFT]:
        effective_radius = 900
        epsilon_mbps = 1
        epsilon_ips = 1

        vehicle_loc = task.vehicle.getLocation()
        potential_solvers = map_grid.getActorsInRadius(
            effective_radius,
            solver_collection_names,
            vehicle_loc,
        )

        max_single_transfer_time = (task.limit_time - task.solving_time) / 2
        min_data_rate_mbps = task.size_in_megabytes / max_single_transfer_time
        min_data_rate_mbps += epsilon_mbps

        start_timestamp = task.created_at
        end_timestamp = start_timestamp + timedelta(seconds=task.limit_time)
        
        ips_required = task.instruction_count / task.solving_time + epsilon_ips
        result = search_best_solver(
            vehicle_loc,
            min_data_rate_mbps,
            potential_solvers,
            ips_required,
            (start_timestamp, end_timestamp),
            self.sinr_map
        )

        if result is None:
            return None

        rbs, solver, _, datarate = result
        transfer_time = task.size_in_megabytes / datarate

        nft_unsigned: NFT = solver.getUnsignedNFT(
            start_timestamp,
            end_timestamp,
            ips_required,
            transfer_time,
            datarate,
            task.vehicle
        )
        nft_unsigned.reserved_rbs = rbs

        return nft_unsigned


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
    #             nft = solver.reserveSolvingCapacity(start_timestamp, end_timestamp, task.instruction_count, task.vehicle)
    #             if nft is not None:
    #                 #FOUND solver with available capacity! we can break loop
    #                 break
    #         #in case nft is still None, no solver with available capacity was found
    #         if nft is None:
    #             raise ValueError(f"None of the solvers for{location.toJson()} had available solving capacity")
    #         else:
    #             timestamp_nft[start_timestamp] = nft
    #     return timestamp_nft
    #
def search_best_solver(
    location: Location,
    min_data_rate_mbps: float,
    base_stations: List[TaskSolver],
    required_ips: float,
    timeinterval: Tuple[datetime, datetime],
    sinr_map: SINRMap
) -> Union[None, Tuple[int, TaskSolver, float, float]]:
    """Search best task solver.

    Args:
        location (Location): vehicle location
        min_data_rate_mbps (float): Minimum required data rate in mbps
        base_stations (List[TaskSolver]): List of base station on which to
                perform search.
        required_hw_power (float): Required HW power on base station.
        timeinterval (Tuple[datetime, datetime]): Time interval of interest.

    Returns:
        Union[None, Tuple[int, TaskSolver, float, float]]: None or
            tuple(reserved_resourceblocks, task solver, sinr value, data rate)
    """
    l = []
    for bs in base_stations:
        if not bs.checkAvailableCapacityBetweenTimestamps(
                *timeinterval, required_ips):
            continue

        sinrval = sinr_map.get_from_bs_map_loc(location, bs.id)
        if sinrval == sinr_map.init_sinr_val:
            sinrval = sinr.calculate_sinr(location, bs, base_stations)
            sinr_map.update_bs_map_loc(location, sinrval, bs.id)

        max_rbs = bs.max_available_rbs(*timeinterval)

        min_rbs = RadioDataRate.get_rb_count(sinrval, min_data_rate_mbps)

        if min_rbs > max_rbs:
            continue

        data_rate = RadioDataRate.calculate(sinrval, min_rbs)

        heapq.heappush(l, (min_rbs, bs, sinrval, data_rate))

    if len(l) == 0:
        return None

    return heapq.heappop(l)


# NOTE: draft of pseudocode....
# @dataclass
# class Reservation:
#     timeinterval: tuple
#     vehicle_id: int
#     nft_id: Any
#     min_mbps: float
#     hw_req: float
#     sinr: float
#     min_rb: float

# @dataclass
# class RBMapping:
#     datetime_start: datetime
#     datetime_end: datetime
#     rb: int
#     vehicle_id: int

# def pseudocode_plan_vehicle_path_nft(vehicle, origin, destination, base_stations, epsilon):
#     max_latency = vehicle.task_requirement.max_latency

#     task_size = vehicle.task_requirement.task_size

#     required_hw_power = vehicle.task_requirement.required_hw_power
#     task_processing_time = required_hw_power / vehicle.task_requirement.instruction_count

#     max_single_transfer_time = (max_latency - task_processing_time) / 2

#     min_data_rate_mbps = task_size / max_single_transfer_time + epsilon # epsilon -> nejaky este treshold pre istotu???

#     proposed_routes = []

#     for path, timeinterval in available_paths(origin, destination):
#         nfts = []
#         for (location, time_interval) in path:

#             available_bss = available_base_stations(
#                 location,
#                 min_data_rate_mbps,
#                 base_stations,
#                 required_hw_power,
#                 timeinterval,
#             )

#             for bs, *details in available_bss:
#                 unsigned_nft = bs.get_unsigned_nft(vehicle.id, time_interval, ...)

#                 if unsigned_nft is not None:
#                     break

#             if unsigned_nft is None:
#                 print('no solver')
#                 continue

#             nfts.append(unsigned_nft)

#         proposed_routes.append((path, nfts, ...))

#     best = select_best_path(proposed_routes)
#     best.nfts.sign_all()
#     return best


# def available_base_stations(
#     location,
#     min_data_rate_mbps,
#     base_stations,
#     required_hw_power,
#     timeinterval,
# ):
#     """select and order by the datarate"""
#     l = []
#     for bs in base_stations:
#         if bs.free_hw(timeinterval) < required_hw_power:
#             continue

#         # rbs = get_available_rb(location, bs)
#         sinrval = get_sinr(location, bs, base_stations)

#         max_rbs = max_available_rb(bs, timeinterval)
#         min_rbs = needed_rbs(min_data_rate_mbps, sinrval)

#         if min_rbs > max_rbs:
#             continue

#         datarate_mbps = datarate(rbs, sinrval)

#         l.append((bs, datarate_mbps, sinrval, min_rbs))

#     return sorted(l, key=lambda x: x[1], reverse=True)
