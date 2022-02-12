import copy
import os
from typing import Any, Dict, List

from isort import file
from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver
from NFTAutonomousVehicles.iisMotionCustomInterface.ActorCollection import ActorCollection
from NFTAutonomousVehicles.iisMotionCustomInterface.IISMotion import IISMotion
from NFTAutonomousVehicles.resultCollectors.MainCollector import MainCollector
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.utils.sinr_map import SINRMap
from NFTAutonomousVehicles.utils.run_utils import parallel_simulation_run
from NFTAutonomousVehicles.utils import dict_utils
from NFTAutonomousVehicles.utils.statistics import Statistics
from src.city.ZoneType import ZoneType
from src.common.Location import Location
from src.common.CommonFunctions import CommonFunctions
from src.common.SimulationClock import *
import asyncio
import time
import osmnx as ox
import matplotlib.pyplot as plt
from src.movement.LocationPredictor import LocationPredictor
from src.movement.movementStrategies.MovementStrategyType import MovementStrategyType

fun = CommonFunctions()


def plott_map_and_nodes(G_map, nodes: list, filename:str):
    node_id = max(G_map.nodes) + 1
    G = copy.deepcopy(G_map)
    for movable in nodes:
        location: Location = movable.getLocation()
        G.add_node(node_id, y=location.latitude, x=location.longitude)
        node_id += 1

    fig, ax = ox.plot_graph(G, save=True, filepath=filename)
    plt.close(fig)

def _config_task_solvers(collection: ActorCollection, config):
    bss: List[TaskSolver] = list(collection.actorSet.values())
    for bs in bss:
        bs.ips_available = config.ips
        bs.tx_frequency = config.tx_frequency
        bs.tx_power = config.tx_power
        bs.association_coverage_radius = config.coverage_radius
        bs.bandwidth = config.bandwidth
        bs.resource_blocks = config.resource_blocks

def _config_vehicles(collection: ActorCollection, config):
    task_config = config.task
    vehicles: List[AutonomousVehicle] = list(collection.actorSet.values())
    for v in vehicles:
        v.sample_task = Task(
            vehicle=v,
            size_in_megabytes=task_config.size_mb,
            instruction_count=task_config.instructions,
            limit_time=task_config.limit_time,
            solving_time=task_config.solving_time,
        )
        v.setSpeed(config.speed_ms)

def main_run(config_dict: Dict[str, Any]):
    config = dict_utils.to_object(config_dict)

    # exit()
    # Setting location that will be simulated - this is not used since we are
    # using a custom map but we need this in order to crete IISMotion instance
    location = Location()
    location.setLatitude(48.709936)
    location.setLongitude(21.238923)
    location.setAltitude(0)
    # half of the width/height of the selected map
    radius = 325  # radius around the location that will be included

    oneway = False  # oneways are disabled so agents will not get stuck at the edges of simulated area
    guiEnabled = config.simulation.gui_enabled  # gui enabled, to see the agents, open /frontend/index.html in your browser while simulation running
    guiTimeout = config.simulation.gui_timeout  # in seconds, sleep between simulations steps (gui is unable to keep up with updates at full speed)
    intersectionCheck = True  # check whether agents are located at the intersection nodes
    gridRows = 5  # grid that world is split into (used to find closest pairs of agents when needed)

    secondsPerTick = config.simulation.dt  # each iteration will increment clock by 1 second
    processing_iteration_duration_seconds = config.simulation.processing_dt
    noOfTicks = config.simulation.steps  # number of iterations simulation will take


    logger = MainCollector(config.result_dir, config.result_name)

    iismotion = IISMotion(radius=radius,
                        location=location,
                        oneWayEnabled=oneway,
                        guiEnabled=guiEnabled,
                        gridRows=gridRows,
                        secondsPerTick=secondsPerTick,
                        removeDeadends=True
                        )  # initialize IISMotion

    map_grid = iismotion.mapGrid
    sinr_map = SINRMap(
        x_size=130,
        y_size=130,
        latmin=map_grid.latmin,
        latmax=map_grid.latmax,
        lonmin=map_grid.lonmin,
        lonmax=map_grid.lonmax,
    )

    vehicles_type = config.vehicles.type
    vehicles_count = config.vehicles.count

    vehicle_movement_strategy = MovementStrategyType.PRELOADED_LOCATIONS_STRATEGY

    if vehicles_type == 1: # shortest path
        vehicle_movement_strategy = MovementStrategyType.RANDOM_WAYPOINT_CITY

    vehicles_collection = iismotion\
        .createActorCollection("vehicles", True, vehicle_movement_strategy) \
        .addAutonomousVehicles(vehicles_count, False, vehicles_type) \
        .setGuiEnabled(guiEnabled)
    _config_vehicles(vehicles_collection, config.vehicles)
    # basicVehicles = iismotion\
    #     .createActorCollection("basicVehicles", True, MovementStrategyType.RANDOM_WAYPOINT_CITY) \
    #     .addAutonomousVehicles(1, False, 1) \
    #     .setGuiEnabled(guiEnabled)

    vehicles_collection.sinr_map = sinr_map
    vehicles_collection.epsilon = config.algorithm.epsilon
    # basicVehicles.sinr_map = sinr_map

    taskSolvers = iismotion\
        .createActorCollection("taskSolvers", False, MovementStrategyType.DRONE_MOVEMENT_CUDA) \
        .setGuiEnabled(guiEnabled)

    if config.base_stations.location_file is None:
        count = config.base_stations.count
        radius = config.base_stations.min_radius
        iismotion.getActorCollection("taskSolvers").generateTaskSolvers(count, radius)
        print(" - solvers generated")
        filename = config.result_dir + '__' + config.result_name + '.json'
        filename = filename.replace('/', '__')
        taskSolvers.storeTaskSolvers(filename)
    else:
        taskSolvers.loadTaskSolversFromFile(config.base_stations.location_file)
    _config_task_solvers(taskSolvers, config.base_stations)
    iismotion.getActorCollection("taskSolvers").setSolversProcessingIterationDurationInSeconds(processing_iteration_duration_seconds)


    # method that moves agents for desired number of iterations
    # async because of "GUI"
    async def simulate():
        print("=================== Simulation started ===================")
        start = time.time()
        for step in range(0, noOfTicks):
            newDay = updateSimulationClock(secondsPerTick)
            print(f"---------------- step: {step} ---------------- dateTime : {getDateTime()} ----------------")
            stepStart = time.time()

            if vehicles_type == 0:
                vehicles_collection.planRoutesForNFTVehicles(['taskSolvers'], logger)
            elif vehicles_type == 1:
                vehicles_collection.planRoutesForNonNFTVehicles(newDay)
            else:
                raise Exception(f"Not implemented type of vehicle {vehicles_type}")

            iismotion.stepAllCollections(newDay, logger)

            if vehicles_type == 0:
                vehicles_collection.generateAndSendNFTTasks(logger)
            elif vehicles_type == 1:
                vehicles_collection.generateAndSendNonNFTTasks(['taskSolvers'], logger)
            else:
                raise Exception(f"Not implemented type of vehicle {vehicles_type}")

            taskSolvers.solveTasks(logger)

            stepEnd = time.time()
            print("step took ", stepEnd - stepStart)
            global DATETIME
            if (guiEnabled == True):
                await asyncio.sleep(guiTimeout)
            end = time.time()

        elapsed = end - start
        print("================== Simulation finished ===================")
        print("elapsed time:", elapsed)

    if (guiEnabled):
        loop = asyncio.get_event_loop()
        loop.create_task(simulate())
        loop.run_until_complete(iismotion.frontend.start_server)
        loop.run_forever()
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate())

    logger.closeCollector()

    # plot map and sinr map
    pm = config.simulation.plot_map_and_sinr
    if pm is not None and pm:
        dirpath_sinr = os.path.join(config.result_dir, config.result_name + '_sinrmap.png')
        dirpath_map = os.path.join(config.result_dir, config.result_name + '_map.png')

        sinr_map.save_global_heat_map(dirpath_sinr, 2)

        plott_map_and_nodes(
            iismotion.map.driveGraph,
            list(taskSolvers.actorSet.values()),
            dirpath_map,
        )

    Statistics().save_json(
        config.result_dir,
        config.result_name,
        config=config_dict
    )

if __name__ == '__main__':
    parallel_simulation_run(main_run)
