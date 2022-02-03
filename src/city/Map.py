import os
import copy
import os
import osmnx as ox
import networkx as nx
import pandas as pd
import pickle
import random

from src.city.MapEdge import MapEdge
from src.city.MapZone import MapZone
from src.city.ZoneType import ZoneType
from src.common.CommonFunctions import CommonFunctions
from src.common.Location import Location
from src.city.Building import Building
from os import path
from random import randrange


class Map:

    def __init__(self, radius, location: Location, oneWayEnabled=False, removeDeadends=True):
        """
        Map class is a "wrapper" for osmnx package functionality
        :param radius:          radius of downloaded map
        :param location:        center of map that will be used
        :param oneWayEnabled:   open street maps include information about directions of roads
                                oneWayEnabled=False enables actors to move one-way roads the opposite way, we use it
                                because agents got stuck at the edges of map on one-ways if enabled
        :param removeDeadends:  True will remove all map nodes that are part of a single edge
        """
        ox.config(use_cache=True, log_console=False)
        print("Osmnx version: " + ox.__version__)
        self.oneWayEnabled = oneWayEnabled
        self.removeDeadends = removeDeadends
        self.comm = CommonFunctions()
        self.gdfBuildings = ox.geometries_from_point((location.latitude, location.longitude), tags={"building": True},
                                                     dist=radius)
        self.buildings = self.parseBuildings(self.gdfBuildings)

        # attempt to load driveGraph from cache
        cacheDriveGraphFilename = f"loc={location.toString()}__r={radius}__ow={oneWayEnabled}__rd={removeDeadends}"
        # self.driveGraph = self.loadDriveGraphFromCache(filename=cacheDriveGraphFilename)

        self.driveGraph = self.loadDriveGraphFromCache(filename="middleMap")
        # fig, ax = ox.plot_graph(self.driveGraph, figsize=(10, 10), node_size=1.5, edge_linewidth=1.0, save=True,
        #                         show=False, filepath=f"iism_cache/driveGraphCache/manhattan_map.png")
        if (self.driveGraph is None):
            self.driveGraph = ox.graph_from_point((location.latitude, location.longitude), dist=radius,
                                                  network_type='drive', simplify=False)
            if (oneWayEnabled == False):
                self.driveGraph = self.driveGraph.to_undirected()
            self.gdfNodes, self.gdfEdges = ox.graph_to_gdfs(self.driveGraph)
            self.intersections_by_coordinates, self.intersections_by_id = self.getIntersectionDicts(self.gdfNodes)
            self.nodesByCoordinatesDict, self.nodesByIdDict = self.getNodeDicts(self.gdfNodes)
            self.edgesByNodeIdDict, self.edgesByIdDict = self.getMapEdgesForEachNode(self.gdfEdges,
                                                                                     self.nodesByIdDict)
            if removeDeadends:
                self.driveGraph = self.removeDeadEnds(self.driveGraph)
                self.gdfNodes, self.gdfEdges = ox.graph_to_gdfs(self.driveGraph)
                self.intersections_by_coordinates, self.intersections_by_id = self.getIntersectionDicts(self.gdfNodes)
                self.nodesByCoordinatesDict, self.nodesByIdDict = self.getNodeDicts(self.gdfNodes)
                self.edgesByNodeIdDict, self.edgesByIdDict = self.getMapEdgesForEachNode(self.gdfEdges,
                                                                                         self.nodesByIdDict)
            self.storeDriveGraphToCache(driveGraph=self.driveGraph, filename=cacheDriveGraphFilename)

        else:
            self.gdfNodes, self.gdfEdges = ox.graph_to_gdfs(self.driveGraph)
            self.intersections_by_coordinates, self.intersections_by_id = self.getIntersectionDicts(self.gdfNodes)
            self.nodesByCoordinatesDict, self.nodesByIdDict = self.getNodeDicts(self.gdfNodes)
            self.edgesByNodeIdDict, self.edgesByIdDict = self.getMapEdgesForEachNode(self.gdfEdges,
                                                                                     self.nodesByIdDict)

        self.latitudeInterval = [self.gdfNodes['y'].min(), self.gdfNodes['y'].max()]
        self.longitudeInterval = [self.gdfNodes['x'].min(), self.gdfNodes['x'].max()]
        print("MAP INTERVALS: ")
        print("Latitude interval: ", self.latitudeInterval)
        print("Longitudeinterval: ", self.longitudeInterval)
        self.mapZones = {}
        self.mapGrid = None

    def setMapGrid(self, mapGrid):
        """
        setter for mapGrid functionality, grid is created in IISMotion class but we may use it somewhere here too
        :param mapGrid: object of map grid
        :return: nothing
        """
        self.mapGrid = mapGrid

    def getRandomNode(self, location=None) -> Location:
        """
        returns random node included in a simulated area
        :param location: in case location object is passed, method will return different node than was passed
        :return: location object of random node
        """
        nodes = self.gdfNodes.sample(n=1)
        ran_loc = Location()
        ran_loc.setLatitude(nodes.iloc[0]['y'])
        ran_loc.setLongitude(nodes.iloc[0]['x'])
        ran_loc.osmnxNode = nodes.index.get_level_values(0).values[0]

        while (ran_loc.equlsWithLocation(location)):
            nodes = self.gdfNodes.sample(n=1)
            ran_loc = Location()
            ran_loc.setLatitude(nodes.iloc[0]['y'])
            ran_loc.setLongitude(nodes.iloc[0]['x'])
            ran_loc.osmnxNode = nodes.index.get_level_values(0).values[0]

        return ran_loc

    def getRandomIntersectionNode(self, location=None) -> Location:
        """
        returns random intersection node included in a simulated area
        :param location: in case location object is passed, method will return different node than was passed
        :return: location object of random intersection node
        """
        nodeLocation = random.choice(list(self.intersections_by_id.values()))
        while (nodeLocation.equlsWithLocation(location)):
            nodeLocation = random.choice(list(self.intersections_by_id.values()))

        return nodeLocation

    def getRouteBetweenNodes(self, locationA: Location, locationB: Location) -> [Location]:
        """
        method that returns shortest path between 2 nodes represented by location objects
        :param locationA: location of starting node
        :param locationB: location of destination node
        :return: list of locations objects, route from locationA to locationB (locationA is not included in a list)
        """
        if (locationB == None):
            return [Location(locationA.getLatitude(), locationA.getLongitude())]
        orig_node = self.getNearestNode(locationA)
        dest_node = self.getNearestNode(locationB)

        # print("-----------Getting route between nodes>")
        route = nx.shortest_path(self.driveGraph, orig_node, dest_node, weight='length')
        # nx_route_len = nx.shortest_path_length(self.driveGraph,orig_node,dest_node, weight='length')

        locList = []
        nodes = self.gdfNodes.loc[route]
        for i in range(1, len(nodes.index)):
            loc = Location()
            loc.setLatitude(nodes.iloc[i]['y'])
            loc.setLongitude(nodes.iloc[i]['x'])
            loc.osmnxNode = nodes.index.get_level_values(0).values[i]
            locList.append(loc)
            # print(f"{i}: {loc.toJson()}")
        # print("----------->")
        # print(f"Route len comparison ox:{nx_route_len} vs cuda:{self.getRouteLength(locList, 0)}")
        return locList

    def getRouteBetweenNodesExcludingNodes(self, locationA: Location, locationB: Location, excludedLocationPairs) -> [
        Location]:
        """
        method that returns shortest path between 2 nodes represented by location objects
        :param locationA: location of starting node
        :param locationB: location of destination node
        :param excludedLocationPairs: list of location pairs that need to be excluded during route planning
        :return: list of locations objects, route from locationA to locationB (locationA is not included in a list)
        """
        if (locationB == None):
            return [Location(locationA.getLatitude(), locationA.getLongitude())]
        orig_node = self.getNearestNode(locationA)
        dest_node = self.getNearestNode(locationB)

        # exclude nodes
        if (excludedLocationPairs):
            modifiedDriveGraph = copy.deepcopy(self.driveGraph)
            for excludedLocationPair in excludedLocationPairs:
                firstLocation = excludedLocationPair[0]
                secondLocation = excludedLocationPair[1]
                modifiedDriveGraph.remove_edge(firstLocation.getOsmnxNode(), secondLocation.getOsmnxNode())
            route = nx.shortest_path(modifiedDriveGraph, orig_node, dest_node, weight='length')
            # nx_route_len = nx.shortest_path_length(self.driveGraph, orig_node, dest_node, weight='length')
            # print(f"Excluded - Route len comparison ox:{nx_route_len} vs cuda:{self.getRouteLength(route, 0)}")
        else:
            # print("-----------Getting route between nodes>")
            route = nx.shortest_path(self.driveGraph, orig_node, dest_node, weight='length')
            # nx_route_len = nx.shortest_path_length(self.driveGraph, orig_node, dest_node, weight='length')
        locList = []
        nodes = self.gdfNodes.loc[route]
        for i in range(1, len(nodes.index)):
            loc = Location()
            loc.setLatitude(nodes.iloc[i]['y'])
            loc.setLongitude(nodes.iloc[i]['x'])
            loc.osmnxNode = nodes.index.get_level_values(0).values[i]
            locList.append(loc)
            # print(f"{i}: {loc.toJson()}")
        # print("----------->")
        # print(f"Excluded - Route len comparison ox:{nx_route_len} vs cuda:{self.getRouteLength(locList, 0)}")

        return locList

    def getRouteLengthBetweenNodes(self, locationA: Location, locationB: Location):
        """
        method that returns length of shortest path between 2 nodes represented by location objects
        :param locationA: location of starting node
        :param locationB: location of destination node
        :return: distance in metres
        """
        orig_node = self.getNearestNode(locationA)
        dest_node = self.getNearestNode(locationB)
        length = nx.shortest_path_length(self.driveGraph, orig_node, dest_node, weight='length')
        return length

    def getRandomPoint(self) -> Location:
        """
        method that returns random location within simulated area
        :return: Location object
        """
        ranWaypint = Location()
        ranWaypint.setLatitude(round(random.uniform(self.latitudeInterval[0], self.latitudeInterval[1]), 6))
        ranWaypint.setLongitude(round(random.uniform(self.longitudeInterval[0], self.longitudeInterval[1]), 6))
        return ranWaypint

    def getNearestNode(self, location: Location) -> Location:
        """
        returns osmnx id of nearest OpenStreetMap node to the given location
        :param location: location to which we want to find the node
        :return: id of osmnx node
        """
        if (location.osmnxNode is None):
            location.osmnxNode = ox.distance.nearest_nodes(self.driveGraph, location.getLongitude(),
                                                           location.getLatitude())
        return location.osmnxNode

    def getRouteBetweenPoints(self, locationA: Location, locationB: Location) -> [Location]:
        """
        returns list with a single location object
        :param locationA:
        :param locationB:
        :return:
        """
        locList = []
        locList.append(locationB)
        return locList

    def isInsideBuilding(self, point: Location) -> bool:
        """
        verifies whether given location is inside building
        :param point: location that is verified
        :return: boolean value (True = location is inside building)
        """
        for building in self.buildings:
            if (building.pointInBuilding(point)):
                return True
        return False

    def getOnBuildingHeight(self, point: Location):
        """
        returns height of building (and building id) at give location
        in case there is no building (0, None) is returned
        :param point: location that is verified
        :return: height in meters, id of building
        """
        for building in self.buildings:
            if (building.pointInBuilding(point)):
                return building.height, building.id
        return 0, None

    def parseBuildings(self, gdfBuild):
        """
        creates building objects from the osmnx downloaded data
        :param gdfBuild: osmnx building data
        :return: list of buildings
        """
        buildings = []
        for index, row in gdfBuild.iterrows():
            building = Building()
            geom = []
            lon, lat = row["geometry"].exterior.coords.xy
            for i in range(0, len(lon)):
                location = Location()
                location.setLatitude(float(lat[i]))
                location.setLongitude(float(lon[i]))
                geom.append(location)
            building.geometryLocations = geom
            building.getCentroid()
            buildings.append(building)
        return buildings

    # Plotting
    def plotRoute(self, route, name):
        fig, ax = ox.plot_graph_route(self.driveGraph, route)
        # fig.savefig(f"{name}.pdf")

    def plotRouteFromGraph(self, graph, route):
        fig, ax = ox.plot_graph_route(graph, route)

    def plotCity(self, type, name):
        if type == 'drive':
            fig, ax = ox.plot_graph(self.driveGraph, figsize=(30, 30), node_size=1.2, edge_linewidth=0.5, save=True,
                                    show=False, filepath=name + ".pdf")
        if type == 'buildings':
            fig, ax = ox.plot_buildings(ox.project_gdf(self.gdfBuildings), save=True, show=False,
                                        filepath=name + ".pdf")

    def addMapZone(self, zone: MapZone):
        """
        adds zone into the system's dictionary of zones
        :param zone: zone that will be inserted
        :return: no return value
        """
        if (zone.zoneType not in self.mapZones):
            self.mapZones[zone.zoneType] = []
        self.mapZones[zone.zoneType].append(zone)

    def getRandomBuildingFromZoneType(self, zoneType: ZoneType) -> Building:
        """
        returns object of building from desired zone type (considering probability of zones of given type)
        :param zoneType: type of zone
        :return: Building object
        """
        print("> > Going to calculate probabilities of zones with type: ", zoneType)
        sumProbability = 0
        zones = self.mapZones[zoneType]
        # TODO chack sum of probabilities for zone type only once
        for zone in zones:
            print(zone.name, " has probability: ", zone.probability, "%")
            sumProbability += zone.probability
        if sumProbability != 100:
            raise NameError('Sum of probabilities for zones with type ', zoneType, "is not equal 100% but: ",
                            sumProbability, "%")

        # Iterate over all zones of given type. Zone will be chosen with given probability (Cumulative distribution function)
        tmpProbability = 0
        randomInt = randrange(100)
        for zone in zones:
            tmpProbability += zone.probability
            if (randomInt <= tmpProbability):
                return zone.getRandomBuilding()

    def getIntersectionDicts(self, gdfNodes):
        """
        returns intersection dictionaries based on given osmnx dataframe
        1st dict contains locations of intersections (with osmnx node id) under lat-lon key
        2nd dict contains locations of intersections (with osmnx node id) under osmnx node id key
        :param gdfNodes: osmnx dataframe
        :return: intersections_by_coordinates, intersections_by_id
        """
        intersections_by_coordinates = {}
        intersections_by_id = {}

        intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]
        for index, node in intersection_nodes.iterrows():
            location = Location(node["y"], node["x"], osmnxNode=index)
            intersections_by_coordinates[location.toRoundedString()] = index
            intersections_by_id[index] = location
        return intersections_by_coordinates, intersections_by_id

    def isIntersection(self, location: Location) -> bool:
        """
        verifies whether  given location is an intersection
        :param location: location to be verified
        :return: boolean (True = is intersection)
        """
        result = location.toRoundedString() in self.intersections_by_coordinates
        return result

    def getNodeDicts(self, gdfNodes):
        """
        returns node dictionaries based on given osmnx dataframe
        1st dict contains locations of nodes (with osmnx node id) under lat-lon key
        2nd dict contains locations of nodes (with osmnx node id) under osmnx node id key
        :param gdfNodes: osmnx dataframe
        :return: nodesByCoordinatesDict, nodesByIdDict
        """
        nodesByCoordinatesDict = {}
        nodesByIdDict = {}

        for index, node in gdfNodes.iterrows():
            location = Location(node["y"], node["x"], osmnxNode=index)
            nodesByCoordinatesDict[location.toRoundedString()] = index
            nodesByIdDict[index] = location
        return nodesByCoordinatesDict, nodesByIdDict

    def getNodeId(self, location: Location):
        """
        returns osmnx node of given node location
        :param location:
        :return: osmnx node id of given node (None, in case location does not correspond to any node)
        """
        if location.toRoundedString() in self.nodesByCoordinatesDict:
            return self.nodesByCoordinatesDict.get(location.toRoundedString())
        else:
            return None

    def getMapEdgesForEachNode(self, gdfEdges, nodesByIdDict):
        """
        returns edge dictionaries based on given osmnx dataframe
        1st dict contains edge objects stored under osmnx node id keys
        2nd dict contains  edge objects stored under edge id keys
        :param gdfEdges: osmnx dataframe of edges
        :param nodesByIdDict: dictionary of nodes (stored under osmnx id key)
        :return: edgesByNodeIdDict, edgesByIdDict
        """
        edgesByNodeIdDict = {}
        edgesByIdDict = {}

        nodeIds = [*nodesByIdDict]
        for nodeId in nodeIds:
            # filter edges where given nodeId is starting node of route
            routesWhereFirst = None
            try:
                routesWhereFirst = gdfEdges.loc[[nodeId]]
            except:
                pass

            # filter edges where given nodeId is end node of route, but node is bidirectional
            routesWhereSecond = None
            try:
                routesWhereSecond = gdfEdges.xs(nodeId, axis=0, level=1, drop_level=False)
            except:
                pass

            edges = pd.concat([routesWhereFirst, routesWhereSecond])

            # single node can be assigned to multpile edges, therefor we store them into a list
            listOfMapEdgesForGivenNode = []
            for index, row in edges.iterrows():
                mapEdge = self.getMapEdgeBasedOnGdfEdge(row)
                edgesByIdDict[mapEdge.edgeId] = mapEdge
                listOfMapEdgesForGivenNode.append(mapEdge)

            # list of edges is stored in output directory under nodeId as a key
            edgesByNodeIdDict[nodeId] = listOfMapEdgesForGivenNode
        return edgesByNodeIdDict, edgesByIdDict

    def removeDeadEnds(self, driveGraph):
        """
        method modifies drive graph in a loop to the point it does not contain dead ends
        :param driveGraph: osmnx dataframe
        :return: modified driveGraph
        """
        print("-----------  Map preprocessing started - removal of dead ends  -----------")
        deadendRemovalNeeded = True
        iterationNumber = 1
        while deadendRemovalNeeded:
            print(f"Removal of deadends iteration #{iterationNumber}")
            deadendRemovalNeeded = False
            gdfNodes, gdfEdges = ox.graph_to_gdfs(driveGraph)
            nodesByCoordinatesDict, nodesByIdDict = self.getNodeDicts(gdfNodes)
            edgesByNodeIdDict, edgesByIdDict = self.getMapEdgesForEachNode(gdfEdges, nodesByIdDict)
            for nodeId, edgeList in edgesByNodeIdDict.items():
                if (len(edgeList) == 1):
                    deadendRemovalNeeded = True
                    driveGraph.remove_node(nodeId)
            iterationNumber += 1
        print("-----------  Map preprocessing finished  -----------")
        return driveGraph

    def getMapEdgeBasedOnGdfEdge(self, gdfEdge) -> MapEdge:
        """
        constructs objects of MapEdge accroding to a single line of osmnx edges data
        :param gdfEdge: single line from self.gdfEdges = ox.graph_to_gdfs(self.driveGraph)
        :return: object of a MapEdge
        """
        mapEdge = MapEdge()
        mapEdge.osmid = gdfEdge['osmid']
        mapEdge.oneway = gdfEdge['oneway']
        # mapEdge.lanes = gdfEdge['lanes']
        # mapEdge.maxspeed = gdfEdge['maxspeed']
        mapEdge.length = gdfEdge['length']
        mapEdge.highway = gdfEdge['highway']
        mapEdge.geometry = gdfEdge['geometry']
        mapEdge.name = gdfEdge['name']
        mapEdge.startLocation = Location(mapEdge.geometry.coords[0][1], mapEdge.geometry.coords[0][0])
        mapEdge.endLocation = Location(mapEdge.geometry.coords[1][1], mapEdge.geometry.coords[1][0])

        mapEdge.startLocation.osmnxNode = self.getNodeId(mapEdge.startLocation)
        mapEdge.endLocation.osmnxNode = self.getNodeId(mapEdge.endLocation)
        mapEdge.edgeId = mapEdge.toString()
        return mapEdge

    def getPossibleSequelsToLocationList(self, route, movementBackwardsAllowed):
        """
        method that will find all possible extensions of given route
        :param route: list of locations representing a route that will be extended
        :param movementBackwardsAllowed: by movement backwards we mean leaving the intersection via the same route
                                        it was entered to
        :return: list of all possible routes extended by a single location of node
        """
        currentLocation = route[-1]
        isIntersection = self.isIntersection(currentLocation)
        routeSequels = []

        # print(f"Getting possible sequels for route of length {len(route)} with current location {currentLocation.toJson()} which is intersection {isIntersection}")
        if (currentLocation.osmnxNode is None):
            currentLocation.osmnxNode = self.getNodeId(currentLocation)
            if (currentLocation.osmnxNode is None):
                print(f"Could not find {currentLocation.toRoundedString()} in following dict")
                print(self.nodesByCoordinatesDict)
                raise ValueError(f"Could not find osmnx node for location {currentLocation.toJson()}")

        edgesFromCurrentLocation = self.edgesByNodeIdDict[currentLocation.osmnxNode]
        # print(f"There are {len(edgesFromCurrentLocation)} edges from current location")

        for edge in edgesFromCurrentLocation:
            otherEndOfEdge = edge.getOppsiteEnd(currentLocation)
            # print(f"processing edge: {edge.toString()} with other end {otherEndOfEdge.toJson()}")

            # if length of original route is 2 and more, we need to consider previous location
            # (due to ability to travel backwards)
            if (len(route) > 1):
                previousLocation = route[-2]
                # print(f"Route input is of size {len(route)} therefore we consider previous location {previousLocation.toJson()} too")

                # if movement backwards is not allowed we process only those edges that will not take us backwards
                if (movementBackwardsAllowed == False):
                    # print("Movement backwards is NOT allowed")
                    # check if other end of edge is not our previous location
                    if (otherEndOfEdge.osmnxNode != previousLocation.osmnxNode):
                        newroute = copy.deepcopy(route)
                        newroute.append(otherEndOfEdge)
                        routeSequels.append(newroute)
                        # print("Previous location is different than other end of edge, therefore output is extended by newRoute:")
                        # self.comm.printRoutes([newroute])
                        # print("Output routes:")
                        # self.comm.printRoutes(routeSequels)
                    else:
                        # it is, therefore we ignore it
                        pass

                else:  # movementBackwardsAllowed == True
                    # print("Movement backwards IS allowed, but only for actors at intersection")
                    # in case current location is intersection, it is allowed to move backwards
                    if (isIntersection == True):
                        # print(f"It is intersection! New route is following!")
                        newroute = copy.deepcopy(route)
                        newroute.append(otherEndOfEdge)
                        # self.comm.printRoutes([newroute])
                        routeSequels.append(newroute)
                        # print("Output routes:")
                        # self.comm.printRoutes(routeSequels)

                    else:  # not in intersection
                        # ignoring edges that will take us backwards
                        if (otherEndOfEdge.osmnxNode != previousLocation.osmnxNode):
                            # print("Previous location is different than other end of edge, therefore output is extended by newRoute:")
                            newroute = copy.deepcopy(route)
                            newroute.append(otherEndOfEdge)
                            # self.comm.printRoutes([newroute])
                            routeSequels.append(newroute)
                            # print("Output routes:")
                            # self.comm.printRoutes(routeSequels)
                        else:
                            pass
            else:
                # print(f"Len of input routes is only{len(route)}, therefore not considering previous location. New Route will be:")
                newroute = copy.deepcopy(route)
                newroute.append(otherEndOfEdge)
                # self.comm.printRoutes([newroute])
                routeSequels.append(newroute)
                # print("Output routes:")
                # self.comm.printRoutes(routeSequels)

        # print(f">Final output from this method is: {routeSequels}")
        return routeSequels

    def getPossibleSequelsToLocationLists(self, routes, numberOfNodes, movementBackwardsAllowed):
        """
        method that will find all possible extensions of given route/routes
        :param routes: route/routes to be extended
        :param numberOfNodes: number of nodes that will be added to given to route
        :param movementBackwardsAllowed: by movement backwards we mean leaving the intersection via the same route
                                        it was entered to
        :return: list of all possible routes extended by a numberOfNodes Locations
        """
        for i in range(0, numberOfNodes):
            newRoutes = []
            for route in routes:
                newRoutes = newRoutes + self.getPossibleSequelsToLocationList(route, movementBackwardsAllowed)
            routes = newRoutes
        return newRoutes


    def getPossibleSequelsToLocationListsBasedOnDistance(self, routesToExtend, actorSpeed, numberOfIterations, movementBackwardsAllowed): #TODO verify
        finalRoutes = []
        neededDistance = actorSpeed * numberOfIterations
        # print(f"Needed distance: {neededDistance} for routes:")

        while len(routesToExtend) > 0:
            # print(f"Number of routes that still need to be extended: {len(routesToExtend)}")
            # self.comm.printRoutes(routesToExtend)

            tempRoutes = []
            for route in routesToExtend:
                tempRoutes = tempRoutes + self.getPossibleSequelsToLocationList(route, movementBackwardsAllowed)
            # print(f"Len of temp routes: {len(tempRoutes)}")
            # self.comm.printRoutes(tempRoutes)

            routesToExtend = []
            for tempRoute in tempRoutes:
                if (self.getRouteLength(tempRoute, 1) > neededDistance):
                    finalRoutes.append(tempRoute)
                    # print(f"Length is longer than needed!!! Appending route to final routes. Final routes now contains {len(finalRoutes)} routes")
                else:
                    routesToExtend.append(tempRoute)
            # print(f">>>> final routes :")
            # self.comm.printRoutes(finalRoutes)
        return finalRoutes

    def getRouteLength(self, route, startIndex):
        distance = 0
        # print(f"Calculating length of route:")
        # for point in route:
            # print(f"-{point.toJson()}")
        for firstLocationIndex in range(startIndex, len(route) - 1):
            # cudaDistance = self.comm.getCuda2dDistance(route[firstLocationIndex], route[firstLocationIndex + 1])
            # real2dDistance = self.comm.getReal2dDistance(route[firstLocationIndex], route[firstLocationIndex + 1])
            #
            # if (cudaDistance != real2dDistance):
            #     print(f"length difference {real2dDistance} vs {cudaDistance} = {abs(real2dDistance - cudaDistance) / cudaDistance * 100}%")
            distance += self.comm.getCuda2dDistance(route[firstLocationIndex], route[firstLocationIndex + 1])
        # print(f"length is: {distance}")
        return distance

    def storeDriveGraphToCache(self, driveGraph, filename):
        """
        stores drive graph to a cach file located at iism_cache/driveGraphCache/
        (path will be created if it deesn`t exist)
        :param driveGraph: graph to be stored
        :param filename: filename of cache file (based on map characteristics)
        :return: no return value
        """
        cache_dir = os.path.join('iism_cache', 'driveGraphCache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        with open(f'iism_cache/driveGraphCache/{filename}.pkl', 'wb') as outp:
            pickle.dump(driveGraph, outp, pickle.HIGHEST_PROTOCOL)
        fig, ax = ox.plot_graph(driveGraph, figsize=(10, 10), node_size=1.5, edge_linewidth=1.0, save=True,
                                show=False, filepath=f"iism_cache/driveGraphCache/{filename}.png")

    def loadDriveGraphFromCache(self, filename):
        """
        loads drive graph from a cache
        :param filename: filename of given file
        :return: osmnx drive graph
        """
        pathname = f"iism_cache/driveGraphCache/{filename}.pkl"
        if path.exists(pathname):
            print(f"Drive graph will be loaded from cache file: {pathname}")
            with open(pathname, 'rb') as inp:
                return pickle.load(inp)
        else:
            return None
