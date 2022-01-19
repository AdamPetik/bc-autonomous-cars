import copy

from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.iisMotionCustomInterface.TaskSolverLoader import TaskSolverLoader
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

from src.common.MacrocellLoader import MacrocellLoader
from src.placeable.stationary.Attractor import Attractor


class ActorCollection:

    def __init__(self, name, map, ableOfMovement, movementStrategy, mapGrid, secondsPerTick):
        self.name = name
        self.map = map
        self.ableOfMovement = ableOfMovement
        self.locationsTable = LocationsTable(mapGrid)
        self.actorSet = {}
        self.mapGrid = mapGrid
        self.secondsPerTick = secondsPerTick
        self.movementStrategy = MovementStrategyFactory().getStrategy(movementStrategy, self.locationsTable,
                                                                      self.actorSet, self.map, self.mapGrid)
        self.attractors = []
        self.guiEnabled = False
        self.com = CommonFunctions()

    def setGuiEnabled(self, value: bool) -> 'ActorCollection':
        self.guiEnabled = value
        return self


    def planRouteAccordingToConnections(self):
        for actorId in self.locationsTable.getAllIds():
            actor: AutonomousVehicle = self.actorSet[int(actorId)]
            new_location = self.movementStrategy.getPreloadedLocation(actor, getDateTime())

            if (new_location is None):
                print(f"Actor#{actorId} requires route planning for time:{getDateTime()}")

                newTargetLocation = self.map.getRandomNode(actor.getLocation())
                # plan route towards targetLocation here

                suitableRouteFound = False
                shortestPath = self.map.getRouteBetweenNodes(actor.getLocation(), newTargetLocation)

                while (suitableRouteFound == False):
                    timestamp_location_dict, timestamp_nft_dict, \
                    missing_NFTs, route_length_in_meters, route_step_count = self.getNFTsForRoute(shortestPath, actor, self.secondsPerTick)
                    self.movementStrategy.preloadLocationsDictForWalkable(actor, timestamp_location_dict)
                    suitableRouteFound = True








    def getNFTsForRoute(self, route, actor, secondsPerTick):
        timestamp = copy.deepcopy(getDateTime())
        timestamp_location_dict = dict()
        timestamp_nft_dict = dict()
        route_length_in_meters = self.map.getRouteLength(route,0)
        route_step_count = 0
        missing_NFTs = 0

        timestamp = copy.deepcopy(getDateTime())
        locationsTable = LocationsTable(self.mapGrid)
        actor_set = copy.deepcopy(self.actorSet)

        movementStrategy = MovementStrategyFactory().getStrategy(
            MovementStrategyType.RANDOM_WAYPOINT_CITY, locationsTable,
            actor_set, self.map, self.mapGrid)

        while len(route) > 0:
            print(f"Route size: {len(route)}")
            next_target = route.pop(0)
            current_location = copy.deepcopy(actor.getLocation())
            targetReached = False

            while(targetReached == False):
                timestamp = timestamp + timedelta(seconds=secondsPerTick)
                print(f"----distanceToTargetBEFORE={self.com.getCuda2dDistance(current_location, next_target)}")
                current_location, targetReached = movementStrategy.getNextLocationOnRoute(current_location, next_target, actor.getSpeed())
                route_step_count = route_step_count + 1
                print(f"----distanceToTargetAFTER={self.com.getCuda2dDistance(current_location, next_target)}")
                print(f"----stepCount={route_step_count}")
                timestamp_location_dict[timestampToMillisecondsSinceStart(timestamp)] = copy.deepcopy(current_location)
                obtained_nft = None
                if(obtained_nft is None):
                    missing_NFTs = missing_NFTs + 1

        return timestamp_location_dict, timestamp_nft_dict, missing_NFTs, route_length_in_meters, route_step_count







    def stepForNFTVehicles(self, newDay: bool):
        # print("step_ New day:", newDay)
        # print(self.locationsTable.getTable())



        # for id in self.locationsTable.getIdsInDestinations():
        #     walkable: object = self.actorSet[int(id)]
        self.planRouteAccordingToConnections()
        self.movementStrategy.move()

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


    def addAutonomousVehicles(self, count, withInitialMove=False) -> 'ActorCollection':
        """
        adds vehicles to the simulation model with the random location within the simulated space
        @param count: number of vehicles to be added
        @param withInitialMove: True/False make steps in random direction to leave the initial location
        @return: no return value
        """
        for i in range(0, count):
            location = self.map.getRandomIntersectionNode()
            vehicle = AutonomousVehicle(self.locationsTable, self.map)
            vehicle.tableRow = self.locationsTable.insertNewActor(vehicle)
            vehicle.setSpeed(20 * self.secondsPerTick)
            vehicle.setMap(self.map)
            x, y = self.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            vehicle.setLocation(location)
            vehicle.home = location
            vehicle.setTargetLocation(location)
            vehicle.setTargetReached(True)
            if (self.movementStrategy.strategyType == MovementStrategyType.PERSON_BEHAVIOUR_CITY_CUDA):
                raise ValueError("PERSON_BEHAVIOUR_CITY_CUDA is not applicable for Autonomous Vehicles")
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
        taskSolvers = solverLoader.getTaskSolvers(self.locationsTable, self.map, count, minRadius)
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
        taskSolvers = solverLoader.loadTaskSolversFromFile(self.locationsTable, self.map, filename)
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
