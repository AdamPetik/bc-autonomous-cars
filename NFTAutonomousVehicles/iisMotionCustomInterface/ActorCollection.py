import copy
from functools import reduce
import json
from heapq import heappush, heappop
import networkx as nx

from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.radio_communication.radio_connection_handler import RadioConnectionHandler
from NFTAutonomousVehicles.taskProcessing.processables import TaskConnectionProcessable
from NFTAutonomousVehicles.iisMotionCustomInterface.TaskSolverLoader import TaskSolverLoader
from NFTAutonomousVehicles.taskProcessing.Task import Task, TaskStatus
from NFTAutonomousVehicles.utils.statistics import IncrementalEvent, MeanEvent, Statistics
from src.city.ZoneType import ZoneType
from src.common.CommonFunctions import CommonFunctions
from src.common.FemtocellLoader import FemtocellLoader
from src.common.Location import Location
from src.movement.LocationsTable import LocationsTable
from src.movement.movementStrategies.MovementStrategyFactory import MovementStrategyFactory
from src.movement.movementStrategies.MovementStrategyType import MovementStrategyType
from src.placeable.movable.Drone import Drone
from src.placeable.movable.Movable import Movable
from src.placeable.movable.MovementActivity import MovementActivity
from src.placeable.movable.MovementActivityType import MovementActivityType
from src.placeable.movable.Person import Person
from src.movement.LocationPredictor import LocationPredictor
from random import randint
from datetime import datetime
from src.common.SimulationClock import *
import time
from NFTAutonomousVehicles.utils.a_star import AStarMetric
from src.common.MacrocellLoader import MacrocellLoader
from src.placeable.stationary.Attractor import Attractor
from NFTAutonomousVehicles.utils import path_utils


class ProposedRoute:
    def __init__(self, index=None, path_of_locations=None, timestamp_location_dict=None, timestamp_solver_dict=None, timestamp_nft_dict=None,
                 missing_NFTs=None, route_length_in_meters=None, route_step_count=None,
                 segments_without_solvers=None):
        self.index = index
        self.path_of_locations = path_of_locations
        self.timestamp_location_dict = timestamp_location_dict
        self.timestamp_solver_dict = timestamp_solver_dict
        self.timestamp_nft_dict = timestamp_nft_dict
        self.missing_NFTs = missing_NFTs
        self.route_length_in_meters = route_length_in_meters
        self.route_step_count = route_step_count
        self.segments_without_solvers = segments_without_solvers

    def getMetrics(self):
        distance_weight = 0
        service_weight = 1
        path_metric = distance_weight * self.route_step_count + service_weight * self.missing_NFTs

        sum_rbs = lambda total_rbs, nft: total_rbs + nft.reserved_rbs
        total_rbs = reduce(sum_rbs, self.timestamp_nft_dict.values(), 0)
        rbs_metric = total_rbs / self.route_step_count

        return path_metric, rbs_metric

    def toJson(self) -> str:
        output = {}
        output["index"] = self.index
        output["route_length_in_meters"] = self.route_length_in_meters
        output["route_step_count"] = self.route_step_count
        output["missing_NFTs"] = self.missing_NFTs
        output["segments_without_solvers len"] = len(self.segments_without_solvers)
        output["Metrics"] = self.getMetrics()
        return json.dumps(output, indent=2)

class ActorCollection:

    def __init__(self, name, map, ableOfMovement, movementStrategy, mapGrid, secondsPerTick):
        self.name = name
        self.map = map
        self.ableOfMovement = ableOfMovement
        self.locationsTable = LocationsTable(mapGrid)
        self.actorSet = {}
        self.mapGrid = mapGrid
        self.secondsPerTick = secondsPerTick

        if isinstance(movementStrategy, MovementStrategyType):
            self.movementStrategy = MovementStrategyFactory().getStrategy(movementStrategy, self.locationsTable,
                                                                        self.actorSet, self.map, self.mapGrid)
        else:
            self.movementStrategy = movementStrategy(self.locationsTable, self.actorSet, self.map, self.mapGrid, None)

        self.attractors = []
        self.guiEnabled = False
        self.com = CommonFunctions()
        self.sinr_map = None
        self.epsilon = None
        self.a_star = AStarMetric(
            self.map.driveGraph, self.secondsPerTick, self.mapGrid, None, None)

    def setGuiEnabled(self, value: bool) -> 'ActorCollection':
        self.guiEnabled = value
        return self

    def planRoutesForNonNFTVehicles(self, newDay: bool):
        # print("step_ New day:", newDay)
        # print(self.locationsTable.getTable())
        if (newDay):
            for key, movable in self.actorSet.items():
                self.movementStrategy.onDayChange(movable)
        self.attractorEffects()
        for id in self.locationsTable.getIdsInDestinations():
            walkable: object = self.actorSet[int(id)]


            # if agent has no MovementActivity in queue, it is needed to create some
            # print(f"walkable with id: {id} is in destination {walkable.getLocation().toJson()}")
            # print("Size of its activity queue is: ", len(walkable.activityQueue))
            if walkable.getCurrentMovementActivity() == None:
                # route will be obtained from movement activity
                locationRoute = self.movementStrategy.getNewRoute(walkable)
                Statistics().mean_event(MeanEvent.ROUTE_PROLONGATION, 0)
                # print("Actor has no activity, so we create one using route: ", locationRoute)
                # for location in locationRoute:
                #     print(f"{location.toJson()}")
                destination = locationRoute[-1]
                # print("movement destination will be: ", destination.toJson())
                activity = MovementActivity(
                    destination=destination,
                    startTime=None,
                    endTime=None,
                    importance=0,
                    name="generated by StepNew",
                    type=MovementActivityType.REGULAR_ACTIVITY,
                    routePlanningRequired=False  # no need, because we route will be assigned in next step
                )
                # assignment of route to the freshly created activity
                activity.route = locationRoute
                # print("New activity is:", activity.toJson())
                # activity is appended to the queue of agent
                walkable.appendMovementActivity(activity)

            # First activity is obtained from agents queue
            activity = walkable.getCurrentMovementActivity()
            # print("ACTOR HAS ACTIVITY:", activity.toJson())
            if activity.getStarted():
                # if current activity is already started, its location route is used to plan target location
                # but first we need to check whether route planning should be performed
                # print("it even started!")
                if activity.getRoutePlanningRequired():
                    # print("But planning is required")
                    activity.route = self.movementStrategy.getRouteTo(walkable, activity.getDestination())
                    activity.setRoutePlanningRequired(False)
                    # print("thus new route will be:", activity.route)
                # else:
                # print("Planning was not required")
                targetLocation = activity.getNextLoctionFromRouteAndPopIt()
                if (targetLocation == None):
                    raise ValueError('TargetLocation is None')
                walkable.setTargetLocation(targetLocation)
                walkable.setTargetReached(False)
                # print("Target location was changed to:", walkable.getTargetLocation().toJson(), " and target reached is False")
            else:
            #     # if activity not yet started, agent should stay at current possition
                # print("But activity is not activated yet")
                walkable.setTargetRerached(False)

            # print("Decision about removal of activity: ", activity.toJson())
            if activity.routeEmpty() and activity.getFinished():
                # if route of current activity is empty, and activity finish time passed, activity can be removed
                # print("Removing activity!")
                walkable.removeFirstActivity()
                # print("AfterRemoval")
                # for acti in walkable.activityQueue:
                #     print(acti.toJson())
    def planRoutesForNFTVehiclesAStar(self, solver_collection_names, logger, t_coef=1.3):
        from NFTAutonomousVehicles.taskProcessing.SolverFinder import SolverFinder
        solver_finder = SolverFinder(self.sinr_map, self.epsilon)

        self.a_star.solver_finder = solver_finder
        self.a_star.solver_coll_names = solver_collection_names

        for actorId in self.locationsTable.getAllIds():
            # print(f"actor#{actorId}")
            actor: AutonomousVehicle = self.actorSet[int(actorId)]
            planned_location = self.movementStrategy.getPreloadedLocation(actor, getDateTime())

            if (planned_location is None):
                newTargetLocation = self.map.getRandomNode(actor.getLocation())

                shortest_path, raw_path = path_utils.get_shortest_path(
                                                    self.map, actor.getLocation(), newTargetLocation)

                longest_allowed_path_m = t_coef * nx.path_weight(
                        self.map.driveGraph, raw_path, weight='length')
                # plan route towards targetLocation here
                result = self.a_star.search_path(
                    self.map.getNearestNode(actor.getLocation()),
                    destination=newTargetLocation.osmnxNode,
                    origin_timestamp=getDateTime()-timedelta(seconds=self.secondsPerTick),
                    longest_distance=longest_allowed_path_m,
                    vehicle=actor,
                )

                if result is None:
                    raise Exception("No path found - this should be impossible.")
                prolongation = path_utils.path_length_diff(
                                        self.map, result.path, shortest_path)
                Statistics().mean_event(
                        MeanEvent.ROUTE_PROLONGATION, prolongation)
                proposed_route = ProposedRoute(
                    index=0,
                    path_of_locations=result.path,
                    timestamp_location_dict=result.location_dict,
                    timestamp_nft_dict=result.nft_dict)

                for unsigned_nft in proposed_route.timestamp_nft_dict.values():
                    unsigned_nft.solver.signNFT(unsigned_nft)

                self.movementStrategy.preloadLocationsDictForWalkable(
                                actor, proposed_route.timestamp_location_dict)
                actor.active_proposed_route = proposed_route


    def planRoutesForNFTVehiclesNew(self, solver_collection_names, logger, t_coef=1.3):
        # print("planRouteAccordingToConnections")
        for actorId in self.locationsTable.getAllIds():
            # print(f"actor#{actorId}")
            actor: AutonomousVehicle = self.actorSet[int(actorId)]
            planned_location = self.movementStrategy.getPreloadedLocation(actor, getDateTime())

            if (planned_location is None):
                # print(f"Actor#{actorId} requires route planning for time:{getDateTime()}")

                newTargetLocation = self.map.getRandomNode(actor.getLocation())

                shortest_path_of_locations, raw_path = path_utils.get_shortest_path(
                                                    self.map, actor.getLocation(), newTargetLocation)
                # plan route towards targetLocation here
                proposed_routes = []
                proposed_routes_counter = 0

                shortest_proposed_route = self.getProposedRoute(shortest_path_of_locations, actor, self.secondsPerTick, solver_collection_names)
                shortest_proposed_route.index = proposed_routes_counter

                actor_speed = actor.getSpeed() / self.secondsPerTick
                t_shortest = path_utils.path_time(self.map, raw_path, actor_speed)
                t_longest = t_coef * t_shortest

                for path, raw_path in path_utils.get_shortest_paths(
                    self.map, actor.getLocation(), newTargetLocation,
                    break_condition=path_utils.break_condition_time(
                        t_longest,
                        actor_speed,
                    )
                ):
                    proposed_route = self.getProposedRoute(path, actor, self.secondsPerTick, solver_collection_names)
                    proposed_route.index = proposed_routes_counter
                    heappush(proposed_routes, (*proposed_route.getMetrics(), proposed_routes_counter, proposed_route))

                    proposed_routes_counter = proposed_routes_counter + 1

                #also each vehicle should have sample task prepared without timestamps
                best_proposed_route = heappop(proposed_routes)[-1]
                logger.logProposedRoute(actor,getDateTime(),len(proposed_routes)+1,shortest_proposed_route, best_proposed_route)

                # print(f"This route was chosen as BEST: {best_proposed_route.toJson()}")

                #TODO compare best route with shortest route here! to have stats about route planning

                for timestamp, unsigned_nft in best_proposed_route.timestamp_nft_dict.items():
                    unsigned_nft.solver.signNFT(unsigned_nft)
                self.movementStrategy.preloadLocationsDictForWalkable(actor, best_proposed_route.timestamp_location_dict)
                actor.active_proposed_route = best_proposed_route

    def planRoutesForNFTVehicles(self, solver_collection_names, logger):
        # print("planRouteAccordingToConnections")
        for actorId in self.locationsTable.getAllIds():
            # print(f"actor#{actorId}")
            actor: AutonomousVehicle = self.actorSet[int(actorId)]
            planned_location = self.movementStrategy.getPreloadedLocation(actor, getDateTime())

            if (planned_location is None):
                # print(f"Actor#{actorId} requires route planning for time:{getDateTime()}")

                newTargetLocation = self.map.getRandomNode(actor.getLocation())
                # plan route towards targetLocation here
                proposed_routes = []
                proposed_routes_counter = 0
                segments_without_solvers = set()
                suitable_route_found = False
                shortest_path_of_locations = self.map.getRouteBetweenNodes(actor.getLocation(), newTargetLocation)
                shortest_proposed_route = self.getProposedRoute(shortest_path_of_locations, actor, self.secondsPerTick, solver_collection_names)
                shortest_proposed_route.index = proposed_routes_counter
                heappush(proposed_routes, (shortest_proposed_route.getMetrics(),proposed_routes_counter, shortest_proposed_route))
                proposed_routes_counter = proposed_routes_counter + 1
                segments_without_solvers = segments_without_solvers.union(shortest_proposed_route.segments_without_solvers)
                # print(f"Characteristics of shortest path: {shortest_proposed_route.toJson()}")

                if shortest_proposed_route.missing_NFTs != 0:

                    while True:
                        try:
                            alternative_path = self.map.getRouteBetweenNodesExcludingNodes(actor.getLocation(),
                                                                                           newTargetLocation,
                                                                                           segments_without_solvers)
                        except:
                            # print(f"could not find route in graph without given segments {segments_without_solvers}")
                            break

                        alternative_proposed_route = self.getProposedRoute(alternative_path, actor, self.secondsPerTick, solver_collection_names)
                        alternative_proposed_route.index = proposed_routes_counter
                        heappush(proposed_routes, (alternative_proposed_route.getMetrics(), proposed_routes_counter, alternative_proposed_route))
                        if(alternative_proposed_route.missing_NFTs == 0):
                            break

                        proposed_routes_counter = proposed_routes_counter + 1
                        # print(f"segments without solver before union {segments_without_solvers}")
                        count_of_segments_without_solvers_before = len(segments_without_solvers)
                        segments_without_solvers = segments_without_solvers.union(alternative_proposed_route.segments_without_solvers)
                        count_of_segments_without_solvers_after = len(segments_without_solvers)
                        # print(f"segments without solver after union {segments_without_solvers}")
                        # print(f"Characteristics of alternative path #{proposed_routes_counter}: {alternative_proposed_route.toJson()}")

                        if(count_of_segments_without_solvers_before == count_of_segments_without_solvers_after):
                            break

                        # self.map.plotRoute(alternative_path, str(proposed_routes_counter))
                #also each vehicle should have sample task prepared without timestamps
                best_proposed_route = heappop(proposed_routes)[2]
                logger.logProposedRoute(actor,getDateTime(),len(proposed_routes)+1,shortest_proposed_route, best_proposed_route)

                # print(f"This route was chosen as BEST: {best_proposed_route.toJson()}")

                #TODO compare best route with shortest route here! to have stats about route planning

                for timestamp, unsigned_nft in best_proposed_route.timestamp_nft_dict.items():
                    unsigned_nft.solver.signNFT(unsigned_nft)
                self.movementStrategy.preloadLocationsDictForWalkable(actor, best_proposed_route.timestamp_location_dict)
                actor.active_proposed_route = best_proposed_route


    def getProposedRoute(self, path_of_locations, actor, secondsPerTick, solver_collection_names):
        from NFTAutonomousVehicles.taskProcessing.SolverFinder import SolverFinder
        from NFTAutonomousVehicles.taskProcessing.Task import Task
        original_path_of_locations = copy.deepcopy(path_of_locations)
        # original_path_of_locations.insert(0, self.map.getNearestNodeLocation(actor.getLocation()))

        origin_location = path_of_locations[0]
        destination_location = path_of_locations[-1]
        solver_finder = SolverFinder(self.sinr_map, self.epsilon)

        # print(f"----getNFTsForRoute----")
        timestamp = copy.deepcopy(getDateTime())
        timestamp_location_dict = dict()
        timestamp_nft_dict = dict()
        route_length_in_meters = self.map.getRouteLength(original_path_of_locations, 0)
        route_step_count = 0
        missing_NFTs = 0
        segments_without_solvers = set()

        timestamp = copy.deepcopy(getDateTime())
        locationsTable = LocationsTable(self.mapGrid)
        # actor_set = copy.deepcopy(self.actorSet)

        movementStrategy = MovementStrategyFactory().getStrategy(
            MovementStrategyType.RANDOM_WAYPOINT_CITY, locationsTable,
            {}, self.map, self.mapGrid)

        current_location = copy.deepcopy(actor.getLocation())
        previous_target = copy.deepcopy(current_location)
        actor_location = copy.deepcopy(current_location)
        while len(path_of_locations) > 0:
            # print(f"Route size: {len(route)}")
            next_target = path_of_locations.pop(0)
            target_reached = False

            while(target_reached == False):
                # print(f"----distanceToTargetBEFORE={self.com.getCuda2dDistance(current_location, next_target)}")
                current_location, target_reached = movementStrategy.getNextLocationOnRoute(current_location, next_target, actor.getSpeed())
                route_step_count = route_step_count + 1
                # print(f"----distanceToTargetAFTER={self.com.getCuda2dDistance(current_location, next_target)}")
                # print(f"----stepCount={route_step_count}")
                # print(f"preloading locaiton for timestamp: {timestamp}")
                timestamp_location_dict[timestamp] = copy.deepcopy(current_location)
                actor.setLocation(current_location)
                dummy_task = Task(vehicle=actor,size_in_megabytes=actor.sample_task.size_in_megabytes,
                                  created_at=timestamp, limit_time=actor.sample_task.limit_time, deadline_at=timestamp+timedelta(seconds=actor.sample_task.limit_time),
                                  instruction_count=actor.sample_task.instruction_count,
                                  solving_time=actor.sample_task.solving_time)
                obtained_nft = solver_finder.searchForTaskSolverSINR(self.mapGrid,task=dummy_task,solver_collection_names=solver_collection_names)
                if(obtained_nft is None):
                    missing_NFTs = missing_NFTs + 1
                    if (previous_target.equlsWithLocation(origin_location)==False and
                            next_target.equlsWithLocation(origin_location)==False and
                            previous_target.equlsWithLocation(destination_location)==False and
                            next_target.equlsWithLocation(destination_location)==False):
                        segments_without_solvers.add((previous_target, next_target))
                else:
                    timestamp_nft_dict[timestamp]=obtained_nft
                    # print(f"Inserting under key {timestamp} nft: {obtained_nft}")

                timestamp = timestamp + timedelta(seconds=secondsPerTick)

            previous_target = copy.deepcopy(next_target)

        # NOTE - supposed check of segments_without_solvers, but edges at destination/start point cant be added to segments_without_solvers
        # if(missing_NFTs>0 and len(segments_without_solvers)==0):
        #     raise ValueError(f"segments_without_provider is not counted properly| missingNFTs: {missing_NFTs} but segments_without_provider: {len(segments_without_solvers)}")
        actor.setLocation(actor_location)

        proposed_route = ProposedRoute(path_of_locations=original_path_of_locations,
                                       timestamp_location_dict=timestamp_location_dict,
                                      timestamp_nft_dict=timestamp_nft_dict,
                                      missing_NFTs=missing_NFTs,
                                      route_length_in_meters=route_length_in_meters,
                                      route_step_count=route_step_count,
                                      segments_without_solvers=segments_without_solvers)
        return proposed_route


    def stepForVehicles(self, newDay: bool, logger):
        self.movementStrategy.move()

        # #print NFTs for current timestamp
        # for actorId in self.locationsTable.getAllIds():
        #     walkable: Movable = self.actorSet[int(actorId)]
        #
        #     if(getDateTime() in walkable.active_proposed_route.timestamp_nft_dict):
        #         nft = walkable.active_proposed_route.timestamp_nft_dict[getDateTime()]
        #         print(f"{actorId} has NFT for currentTimestamp {nft}")
        #     else:
        #         print(f"{actorId} does not have NFT for {getDateTime()}")


    def generateAndSendNFTTasks(self, logger):
        timestamp = getDateTime()
        for actorId in self.locationsTable.getAllIds():
            vehicle: AutonomousVehicle = self.actorSet[int(actorId)]

            Statistics().incremental_event(IncrementalEvent.GENERATED_TASK)

            if (timestamp in vehicle.active_proposed_route.timestamp_nft_dict):
                nft = vehicle.active_proposed_route.timestamp_nft_dict[timestamp]

                task = Task(vehicle=vehicle, size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                                  created_at=timestamp, limit_time=vehicle.sample_task.limit_time,
                                  deadline_at=timestamp + timedelta(seconds=vehicle.sample_task.limit_time),
                                  instruction_count=vehicle.sample_task.instruction_count,
                                  solving_time=vehicle.sample_task.solving_time)
                task.solver = nft.solver
                task.nft = nft
                nft.solver.receiveTask(task, nft.single_transfer_time)
            else:
                task = Task(vehicle=vehicle, size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                            created_at=timestamp, limit_time=vehicle.sample_task.limit_time,
                            deadline_at=timestamp + timedelta(seconds=vehicle.sample_task.limit_time),
                            instruction_count=vehicle.sample_task.instruction_count,
                            solving_time='null')
                task.single_transfer_time = 'null'
                task.status = TaskStatus.FAILED_TO_FIND_SOLVER
                logger.logTask(task)


    def generateAndSendNonNFTTasks(self, solver_collection_names, logger, connection_handler: RadioConnectionHandler):
        from NFTAutonomousVehicles.taskProcessing.SolverFinder import SolverFinder
        solver_finder = SolverFinder(self.sinr_map, self.epsilon)

        timestamp = getDateTime()
        for actorId in self.locationsTable.getAllIds():
            vehicle: AutonomousVehicle = self.actorSet[int(actorId)]

            Statistics().incremental_event(IncrementalEvent.GENERATED_TASK)

            task = Task(vehicle=vehicle, size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                        created_at=timestamp, limit_time=vehicle.sample_task.limit_time,
                        deadline_at=timestamp + timedelta(seconds=vehicle.sample_task.limit_time),
                        instruction_count=vehicle.sample_task.instruction_count,
                        solving_time=vehicle.sample_task.solving_time)

            non_signed_nft = solver_finder.searchForTaskSolverClosest(self.mapGrid, task, solver_collection_names)
            # uplink = connection_handler.get_uplink_ue(vehicle.id)
            # if uplink is not None:
            #     processable = TaskConnectionProcessable(task, task.created_at)

            #     uplink.fifos[actorId].add(
            #         (task.created_at, task.id, processable)
            #     )

            if (non_signed_nft is not None):
                task.nft = non_signed_nft
                non_signed_nft.solver.receiveTask(task, non_signed_nft.single_transfer_time, True)
                task.solver = non_signed_nft.solver
            else:
                task = Task(vehicle=vehicle, size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                            created_at=timestamp, limit_time=vehicle.sample_task.limit_time,
                            deadline_at=timestamp + timedelta(seconds=vehicle.sample_task.limit_time),
                            instruction_count=vehicle.sample_task.instruction_count,
                            solving_time='null')
                task.single_transfer_time = 'null'
                task.status = TaskStatus.FAILED_TO_FIND_SOLVER
                logger.logTask(task)


    def solveTasks(self, logger):
        from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver

        timestamp = copy.deepcopy(getDateTime())
        # next_timestamp = timestamp + timedelta(seconds=self.secondsPerTick)

        # time_increment = processing_iteration_duration_seconds
        # print(f"FIRST timestamp before loop: {timestamp} nextTImestamp: {next_timestamp} and increment: {time_increment}")
        # while (timestamp < next_timestamp):
        for actorId in self.locationsTable.getAllIds():
            solver: TaskSolver = self.actorSet[int(actorId)]
            solver.solveTasks(timestamp, logger)
            # timestamp = timestamp + timedelta(seconds=time_increment)


    def setSolversProcessingIterationDurationInSeconds(self, processing_iteration_duration_seconds):
        from NFTAutonomousVehicles.entities.TaskSolver import TaskSolver

        for actorId in self.locationsTable.getAllIds():
            solver: TaskSolver = self.actorSet[int(actorId)]
            solver.setProcessingIterationDurationInSeconds(processing_iteration_duration_seconds)

    def getLocationPredictionsForNextIterations(self, nuOfIterations, movementBackwardsAllowed=True):
        """
        This method returns possible locations of agent moving along routes
        !NOTE! that this method should be called right afer step() method
        :param nuOfIterations:
        :return: dictionary of lists with LocationPrediction objects
        """

        if (self.movementStrategy.strategyType not in [MovementStrategyType.RANDOM_INTERSECTION_WAYPOINT_CITY_CUDA]):
            raise ValueError('Location prediction is not available for collection with set MovementStrategyType:',
                             self.movementStrategy.strategyType)
        if (movementBackwardsAllowed == False):
            raise ValueError(
                'You required prediction that will ignore ability to move backwards, but mobility pattern may allow it')

        for actorId in self.locationsTable.getAllIds():
            walkable: Movable = self.actorSet[int(actorId)]
            # destination == node of open street map
            # update is done to find out which walkables are located at intersection nodes
            isAtIntersection = self.map.isIntersection(walkable.getLocation())
            walkable.setIsAtIntersection(isAtIntersection)
        locationPredictor = LocationPredictor()
        return locationPredictor.predictLocationsForNextIterations(self.map, self.getActorsInDestinations(),
                                                                          self.actorSet, self.secondsPerTick,
                                                                          nuOfIterations, movementBackwardsAllowed)

    def addPlaceables(self, placeables) -> 'ActorCollection':
        """
        before using this method, Placeables need to have their locations set (same with speed for Movables)
        :param placeables: list of Placeables that will be added to the actor set of ActorCollection
        :return: self
        """
        for placeable in placeables:
            self.actorSet[placeable.id] = placeable
        return self

    def addPersons(self, count, withInitialMove=False) -> 'ActorCollection':
        """
        adds persons to the simulation model with the random location within the simulated space
        @param count: number of persons to be added
        @param withInitialMove: True/False make steps in random direction to leave the initial location
        @return: no return value
        """
        for i in range(0, count):
            location = self.map.getRandomIntersectionNode()
            person = Person(self.locationsTable, self.map)
            person.tableRow = self.locationsTable.insertNewActor(person)
            person.setSpeed(2 * self.secondsPerTick)
            person.setMap(self.map)
            x, y = self.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            person.setLocation(location)
            person.home = location
            person.setTargetLocation(location)
            person.setTargetReached(True)
            if (self.movementStrategy.strategyType == MovementStrategyType.PERSON_BEHAVIOUR_CITY_CUDA):
                person.location = self.map.getRandomBuildingFromZoneType(ZoneType.HOUSING).getCentroid()
                person.work = self.map.getRandomBuildingFromZoneType(ZoneType.WORK).getCentroid()
                person.generateDailyActivityQueue()
            self.actorSet[person.id] = person
            person.setTargetReached(True)

        if withInitialMove:
            for key, person in self.actorSet.items():
                person.setSpeed(randint(0, 50))

            for i in range(0, 100):
                self.step()

            for key, person in self.actorSet.items():
                person.setSpeed(2 * self.secondsPerTick)

        return self


    def addAutonomousVehicles(self, count, withInitialMove=False, vehicle_type=0) -> 'ActorCollection':
        """
        adds vehicles to the simulation model with the random location within the simulated space
        @param count: number of vehicles to be added
        @param withInitialMove: True/False make steps in random direction to leave the initial location
        @return: no return value
        """
        for i in range(0, count):
            location = self.map.getRandomIntersectionNode()
            vehicle = AutonomousVehicle(self.locationsTable, self.map, vehicle_type)
            vehicle.tableRow = self.locationsTable.insertNewActor(vehicle)
            vehicle.setSpeed(20 * self.secondsPerTick)
            vehicle.setMap(self.map)

            x, y = self.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            vehicle.setLocation(location)
            vehicle.home = location
            vehicle.setTargetLocation(location)
            vehicle.setTargetReached(True)
            # if (self.movementStrategy.strategyType == MovementStrategyType.PERSON_BEHAVIOUR_CITY_CUDA):
            #     raise ValueError("PERSON_BEHAVIOUR_CITY_CUDA is not applicable for Autonomous Vehicles")
            self.actorSet[vehicle.id] = vehicle
            vehicle.setTargetReached(True)

        if withInitialMove:
            for key, vehicle in self.actorSet.items():
                vehicle.setSpeed(randint(0, 50))

            for i in range(0, 100):
                self.step()

            for key, vehicle in self.actorSet.items():
                vehicle.setSpeed(2 * self.secondsPerTick)
        return self

    def addDrones(self, count) -> 'ActorCollection':
        for i in range(0, count):
            location = self.map.getRandomPoint()
            location.setAltitude(10)
            x, y = self.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            drone = Drone(self.locationsTable, self.map)
            drone.tableRow = self.locationsTable.insertNewActor(drone)
            drone.setSpeed(2 * self.secondsPerTick)
            drone.setMap(self.map)
            drone.setLocation(location)
            drone.setTargetLocation(location)
            drone.setTargetReached(False)
            self.actorSet[drone.id] = drone
        return self

    def addAttractor(self, location: Location, radius, startTime, endtime) -> 'ActorCollection':
        location.setAltitude(0)
        x, y = self.mapGrid.getGridCoordinates(location)
        location.setGridCoordinates(x, y)
        attractor = Attractor(locationsTable=self.locationsTable, map=self.map, radius=radius, startTime=startTime,
                              endTime=endtime)
        attractor.tableRow = self.locationsTable.insertNewActor(attractor)
        attractor.setLocation(location)
        attractor.startTime = startTime
        attractor.endTime = endtime
        self.actorSet[attractor.id] = attractor
        return self

    def loadMacrocells(self, networks) -> 'ActorCollection':
        macrocellLoader = MacrocellLoader()
        macrocells = macrocellLoader.getMacrocells("147.232.40.82",
                                                   self.map.latitudeInterval[0],
                                                   self.map.latitudeInterval[1],
                                                   self.map.longitudeInterval[0],
                                                   self.map.longitudeInterval[1],
                                                   self.locationsTable,
                                                   self.map,
                                                   networks)
        for cell in macrocells:
            self.actorSet[cell.id] = cell
        return self

    def generateTaskSolvers(self, count, minRadius) -> 'ActorCollection':
        solverLoader = TaskSolverLoader()
        taskSolvers = solverLoader.getTaskSolvers(self.locationsTable, self.map, count, minRadius, self.secondsPerTick)
        for solver in taskSolvers:
            self.actorSet[solver.id] = solver
        return self

    def storeTaskSolvers(self, filename) -> 'ActorCollection':
        print("Actor set", self.actorSet)
        list = []
        for key, value in self.actorSet.items():
            list.append(value)
        solverLoader = TaskSolverLoader()
        solverLoader.storeTaskSolverLocationsIntoFile(list, filename)
        return self

    def loadTaskSolversFromFile(self, filename) -> 'ActorCollection':
        solverLoader = TaskSolverLoader()
        taskSolvers = solverLoader.loadTaskSolversFromFile(self.locationsTable, self.map, filename, self.secondsPerTick)
        for solver in taskSolvers:
            self.actorSet[solver.id] = solver
        return self

    def getFeaturesGeoJson(self):
        features = []
        for key, movable in self.actorSet.items():
            features.append(movable.getGeoStruct())
        return features

    def getActorsAtIntersections(self):
        return list(map(self.actorSet.get, self.locationsTable.getIdsAtIntersections()))

    def getActorsInDestinations(self):
        return list(map(self.actorSet.get, self.locationsTable.getIdsInDestinations()))

    def logMovement(self, newDay) -> 'ActorCollection':
        for id in self.locationsTable.getIdsInDestinations():
            walkable = self.actorSet[int(id)]
            walkable.logLocation(newDay)
        return self

    def getMovablesAtGridXY(self, x, y):
        ids = self.locationsTable.getIdsAtGridXY(x, y)
        movables = []
        for id in ids:
            movables.append(self.actorSet[id])
        return movables

    def attractorEffects(self) -> 'ActorCollection':
        global DATETIME
        for attractor in self.attractors:
            if attractor.startTime <= getDateTime() <= attractor.endTime:
                usersInArea = self.mapGrid.getActorsInRadius(attractor.radius, [self.name], attractor.getLocation())
                for user in usersInArea:
                    if user.getCurrentMovementActivity() == None or \
                            ((
                                     not user.getCurrentMovementActivity().getType() == MovementActivityType.ATTRACTOR_ACTIVITY) and user.getCurrentMovementActivity().importance < attractor.severity):
                        attractorActivity = MovementActivity(
                            attractor.getLocation(),
                            startTime=None,
                            endTime=attractor.endTime,
                            importance=attractor.severity,
                            name=attractor.name,
                            routePlanningRequired=False,
                            type=MovementActivityType.ATTRACTOR_ACTIVITY
                        )
                        locationRoute = self.movementStrategy.getRouteTo(user, attractor.getLocation())
                        attractorActivity.pushLocationListToRoute(locationRoute)
                        user.storeMovementActivity(attractorActivity, asFirst=True)

        self.attractors[:] = (x for x in self.attractors if x.endTime > getDateTime())
        return self

    def compareCurrentLocationsWithPredictions(self, predictionDict):
        for id, actor in self.actorSet.items():
            dictKey = (actor.id, getDateTime().strftime("%m/%d/%Y, %H:%M:%S.%f"))

            if (dictKey in predictionDict):
                predictions = predictionDict[dictKey]

                correctPredictionFound = False
                for prediction in predictions:
                    if prediction.location.equlsWithLocation(actor.getLocation()):
                        print(
                            f"Correct!!! Current location {actor.getLocation().toJson()} of actor {actor.id} corresponds to the prediction {prediction.toJson()}")
                        correctPredictionFound = True
                        break
                    else:
                        print(f"Prediction: {prediction.toJson()}")
                        print(f"Current location {actor.getLocation().toJson()}")
                        print("Note this is not the right prediction!")
                if (correctPredictionFound == False):
                    print(
                        f"Error will follow but this might be interesting: {actor.getLocation().toJson()} is intersection: {self.map.isIntersection(actor.getLocation())}")
                    raise ValueError(f"Not found in predictions {actor.getLocation().toJson()} of actor {actor.id} ")
            else:
                print(f"dict key not even in prediction {dictKey}")

    # def saveLocationsFile(self) -> 'ActorCollection':
    #     locations = ""
    #     for key, person in self.actorSet.items():
    #         location = person.getLocation()
    #         locations = locations + str(location.getLatitude()) + ", " + str(location.getLongitude()) + ", \n"
    #     self.com.appendToFile("locationsDebug", locations)
    #     return self
