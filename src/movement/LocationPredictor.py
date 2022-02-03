import copy

from src.city.Map import Map
from src.common.CommonFunctions import CommonFunctions
from src.common.UniqueID import UniqueID
from src.movement.LocationsTable import LocationsTable
from src.movement.movementStrategies.MovementStrategyFactory import MovementStrategyFactory
from src.movement.movementStrategies.MovementStrategyType import MovementStrategyType
from src.placeable.movable.Movable import Movable
from src.common.SimulationClock import *
import json


class LocationPrediction:
    def __init__(self):
        self.id = None
        self.agent = None
        self.agentId = None
        self.timestamp = None
        self.location = None
        self.targetLocation = None
        self.madeAt = None
        self.routeIndexes = []

    def toJson(self):
        data = {}
        data['key'] = 'value'
        data['agentId'] = self.agentId
        data['timestamp'] = str(self.timestamp)
        data['routeIndexes'] = self.routeIndexes
        data['location'] = self.location.toJson()
        data['targetLocation'] = self.targetLocation.toJson()
        data['made_at'] = str(self.madeAt)
        return json.dumps(data)

    def toMapMakerString(self):
        '''
        You can copy output of this method into https://maps.co/ to show prediction on map
        :return:
        '''
        return f"{self.location.latitude}, {self.location.longitude}, agent:{self.agentId} | {self.timestamp} | routeIndexes:{self.routeIndexes} | "

    def equalsWithPrediction(self, prediction):
        if self.agentId == prediction.agentId and self.timestamp == prediction.timestamp and self.location.equlsWithLocation(
                prediction.location) and self.id != prediction.id:
            return True
        else:
            return False

    def mergeRouteIndexWithAnotherPrediction(self, prediction):
        self.routeIndexes = self.routeIndexes + prediction.routeIndexes
        return self


class LocationPredictor:
    def __init__(self):
        self.comm = CommonFunctions()

    def predictLocationsForNextIterations(self, map: Map, actorsAtDestinations, actorSet, secondsPerTick,
                                                 iterationsCount, movementBackwardsAllowed):

        # self.comm.appendToFile("NewRoutesMethod", f"\n\n---- {getDateTime()} ----------------------------------------\n")
        predictions = []
        # print(f"Actors at intersections: {actorsAtIntersections}")
        predictions = []

        timestamp = copy.deepcopy(getDateTime())
        locationsTable = LocationsTable(map.mapGrid)
        possibleRoutesByActorId_dict = {}

        for actorId, actor in actorSet.items():
            # print(f"Actor {actor.id} at location:{actor.getLocation().toJson()} is intersection: {map.isIntersection(actor.getLocation())}| target: "
            #       f"{actor.getTargetLocation().toJson()} | previous target {actor.previousTarget.toJson()}")
            if (actor in actorsAtDestinations):
                # print("Actor is at destination node")
                possibleRoutesForActor = map.getPossibleSequelsToLocationListsBasedOnDistance(
                    [[actor.previousTarget, actor.getLocation()]], actor.getSpeed(), iterationsCount, movementBackwardsAllowed)
                # self.comm.appendToFile("NewRoutesMethod", self.printRoutes(possibleRoutesForActor, False))
                possibleRoutesByActorId_dict[actor.id] = self.preprocessRoutePredictions(actor, possibleRoutesForActor,
                                                                                         2)
            else:
                # print("Actor is NOT at destination node")
                # for actors that are not located at the intersection
                possibleRoutesForActor = map.getPossibleSequelsToLocationListsBasedOnDistance(
                    [[actor.previousTarget, actor.getTargetLocation()]], actor.getSpeed(), iterationsCount, movementBackwardsAllowed)
                # self.comm.appendToFile("NewRoutesMethod", self.printRoutes(possibleRoutesForActor, False))
                possibleRoutesByActorId_dict[actor.id] = self.preprocessRoutePredictions(actor, possibleRoutesForActor,
                                                                                         1)

            # self.printRoutes(possibleRoutesByActorId_dict[actor.id])
            if (movementBackwardsAllowed == True and map.removeDeadEnds == True and len(
                    possibleRoutesByActorId_dict[actor.id]) == 1):
                print("There might be issue with a prediction because only 1 possible route was found")
                # raise ValueError("There might be issue with a prediction because only 1 possible route was found")

        # each possible target of each actor will be inserted into location table
        for actorId, possibleRoutes in possibleRoutesByActorId_dict.items():
            # chosen actor is get
            actor = actorSet[actorId]

            # each of his targets is written into table
            routeIndex = 0
            for route in possibleRoutes:
                rowNumber = locationsTable.insertNewRow(actor,
                                                        actor.getLocation(),
                                                        route.pop(0),
                                                        # route is modified in the process (pop of next location)
                                                        actor.getSpeed(),
                                                        routeIndex
                                                        )
                # if(actor.getLocation().equlsWithLocation(actor.getTargetLocation())):
                #     newTargetLocation = self.popNextTargetLocationForAgent(possibleRoutesByActorId_dict,
                #                                                            actor.id,
                #                                                            routeIndex)
                #     locationsTable.setTargetLocation(rowNumber, newTargetLocation)
                #     print(
                #     f"WARNING agent {actor.id} was at destination! setting new target{newTargetLocation.toJson()}")

                locationsTable.setTargetReached(rowNumber, False)
                routeIndex = routeIndex + 1
        # locations table should be ready by now

        if (locationsTable.table.shape[0] == 0):
            pass
            # print(f"locationsTable is empty, therefore no cuda simulation: {locationsTable.table}")
        else:
            # print(f"locationsTable that is sent to cuda kernel: {locationsTable.table}")
            movementStrategy = MovementStrategyFactory().getStrategy(
                MovementStrategyType.RANDOM_INTERSECTION_WAYPOINT_CITY_CUDA, locationsTable,
                actorSet, map, map.mapGrid)

            for iteration in range(0, iterationsCount):
                timestamp = timestamp + timedelta(seconds=secondsPerTick)
                movementStrategy.move()

                num_rows, num_cols = locationsTable.table.shape
                for rowIndex in range(0, num_rows):
                    prediction = LocationPrediction()
                    prediction.id = UniqueID().getId()
                    prediction.agent = actorSet[locationsTable.getId(rowIndex)]
                    prediction.agentId = prediction.agent.id
                    prediction.location = locationsTable.getLocation(rowIndex)
                    prediction.targetLocation = locationsTable.getTargetLocation(rowIndex)
                    prediction.timestamp = copy.deepcopy(timestamp)
                    prediction.madeAt = copy.deepcopy(getDateTime())
                    routeIndex = locationsTable.getRouteIndex(rowIndex)
                    prediction.routeIndexes.append(routeIndex)

                    if (locationsTable.getTargetReached(rowIndex)):
                        newTargetLocation = self.popNextTargetLocationForAgent(possibleRoutesByActorId_dict,
                                                                               prediction.agentId,
                                                                               prediction.routeIndexes[0],
                                                                               )
                        if newTargetLocation is not None:
                            locationsTable.setTargetLocation(rowIndex, newTargetLocation)
                            locationsTable.setTargetReached(rowIndex, False)
                        else:
                            raise ValueError("Next location for agent route was required, but None was returned")
                    predictions.append(prediction)

        # print("Predictions before postprocessing ------------------- ")
        # self.printPredictions(predictions)
        # print("Predictions after postprocessing ------------------- ")

        predictions = self.postprocessLocationPredictions(predictions)
        # self.printPredictions(predictions)

        # self.comm.appendToFile("NewPredictionssMethod", f"\n\n---- {getDateTime()} ----------------------------------------\n")
        # self.comm.appendToFile("NewPredictionssMethod", self.printPredictions(predictions,False))
        return predictions


    def preprocessRoutePredictions(self, actor: Movable, possibleRoutesList, itemsToRemove):
        # because each route contains previous target and current location at the beginning we need to remove them
        outputListOfLists = []
        for route in possibleRoutesList:
            newRoute = copy.deepcopy(route[itemsToRemove:])
            outputListOfLists.append(newRoute)
        return outputListOfLists


    def postprocessLocationPredictions(self, predictions):
        postprocessedPredictionsAsDict = {}
        processedPredictionIds = set()

        for firstPrediction in predictions:
            # print(f"First is: {firstPrediction.id}")
            # print("processed set: ", processedPredictionIds)
            if firstPrediction.id not in processedPredictionIds:
                processedPredictionIds.add(firstPrediction.id)
                # print("processed set: ", processedPredictionIds)

                for secondPrediction in predictions:
                    # print(f"Second is: {firstPrediction.id}")
                    # print("processed set: ", processedPredictionIds)
                    if secondPrediction.id not in processedPredictionIds:
                        #
                        # print(f"comparing {firstPrediction.id} with {secondPrediction.id}")
                        # print(f"first: {firstPrediction.toJson()}")
                        # print(f"second: {secondPrediction.toJson()}")

                        if firstPrediction.equalsWithPrediction(secondPrediction):
                            # print("TheyEqual!")
                            firstPrediction.mergeRouteIndexWithAnotherPrediction(secondPrediction)
                            # print(f"first after merged {firstPrediction.toJson()}")
                            processedPredictionIds.add(secondPrediction.id)

                dictKey = (firstPrediction.agentId, firstPrediction.timestamp.strftime("%m/%d/%Y, %H:%M:%S.%f"))
                if dictKey not in postprocessedPredictionsAsDict:
                    postprocessedPredictionsAsDict[dictKey] = []
                postprocessedPredictionsAsDict[dictKey].append(firstPrediction)

        return postprocessedPredictionsAsDict

    def popNextTargetLocationForAgent(self, possibleRoutesByActorId_dict, actorId, routeIndex):
        routeIndex = routeIndex
        if (len(possibleRoutesByActorId_dict[actorId][routeIndex]) > 0):
            return possibleRoutesByActorId_dict[actorId][routeIndex].pop(0)
        else:
            return None

    def printPredictions(self, predictions, printPrediction=True):
        output = str(f"PREDICTION from time: {getDateTime()}\n")
        for key, values in predictions.items():
            for value in values:
                output = output + f"key: {key} | value: {value.toMapMakerString()}\n"
        if printPrediction:
            print(output)
        return output

    def printRoutes(self, routes, printRoutes=True):
        output = str(f"Routes from time: {getDateTime()}\n")
        routeIndex = 0
        for route in routes:
            output = output + f" ---------- route # {routeIndex}\n"
            locationIndex = 1
            for location in route:
                output = output + f"{locationIndex}.    |{location.toString()}, route#{routeIndex} step#{locationIndex}\n"
                locationIndex = locationIndex + 1
            routeIndex = routeIndex + 1

        if printRoutes:
            print(output)
        return output
