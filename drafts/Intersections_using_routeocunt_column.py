import osmnx as ox
import networkx as nx
import random
import pandas as pd
import json
from shapely.geometry import LineString
import copy


class Location:
    def __init__(self, latitude=0, longitude=0, altitude=0, osmnxNode=None):
        '''
        Location class representing point with GPS coordinates
        @param latitude: latitude
        @param longitude: longitude
        @param altitude: height above the surface of map
        '''
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.osmnxNode = osmnxNode
        self.gridCoordinates = []

    def toString(self):
        return f"location osmid:{self.osmnxNode}|latitude:{self.latitude},longitude:{self.longitude}"
    
    def toTestString(self):
        return f"{self.latitude}, {self.longitude}"
        
class MapEdge:

    def __init__(self, osmRow, nodes_by_coordinates):
        self.osmid = osmRow['osmid']
        self.oneway = osmRow['oneway']
        #self.lanes = osmRow['lanes']
        #self.maxspeed = osmRow['maxspeed']
        self.length = osmRow['length']
        self.highway = osmRow['highway']
        self.geometry = osmRow['geometry']
        self.name = osmRow['name']
        self.startLocation = Location(self.geometry.coords[0][1], self.geometry.coords[0][0])
        self.endLocation = Location(self.geometry.coords[1][1], self.geometry.coords[1][0])
        
        self.startLocation.osmnxNode = getNodeId(self.startLocation, nodes_by_coordinates)
        self.endLocation.osmnxNode = getNodeId(self.endLocation, nodes_by_coordinates)
        self.edgeId = self.toString()
        
    def toString(self):
        return f"{self.osmid}|start:{self.startLocation.toString()} end:{self.endLocation.toString()}"
        
        
    def getOppsiteEnd(self, location:Location):
        #print(f"----- getOppsiteEnd of edge: {self.edgeId}")
        #print(f"searching opposite location to: {location.toString()}")
        #print(f"start: {self.startLocation.toString()}")
        #print(f"end: {self.endLocation.toString()}")
        
        if(location.osmnxNode == self.startLocation.osmnxNode):
            return self.endLocation
        
        if(location.osmnxNode == self.endLocation.osmnxNode):
            return self.startLocation
        
        raise ValueError('It seems that specified location does not belong to this edge')
        


#  HElper methods -------------------------------------------------------------------------------------------------
def getNearestNode(location: Location):
    if (location.osmnxNode is None):
        location.osmnxNode = ox.distance.nearest_nodes(driveGraph, location.longitude, location.latitude)
    return location.osmnxNode

def getIntersectionDicts(gdfNodes):
    intersections_by_coordinates = {}
    intersections_by_id = {}
    
    print(gdfNodes.head())
    intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]
    for index, node in intersection_nodes.iterrows():
        intersection_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
        intersection_identifier = index
        intersections_by_coordinates[intersection_coordinates] = intersection_identifier
        
        intersections_by_id[intersection_identifier] = Location(round(node["y"], 6), round(node["x"], 6), osmnxNode=intersection_identifier)
    return intersections_by_coordinates, intersections_by_id

def getNodeDicts(gdfNodes):
    nodes_by_coordinates = {}
    nodes_by_id = {}
    
    print(gdfNodes.head())
    for index, node in gdfNodes.iterrows():
        node_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
        node_identifier = index
        nodes_by_coordinates[node_coordinates] = node_identifier
        
        nodes_by_id[node_identifier] = Location(round(node["y"], 6), round(node["x"], 6), osmnxNode=node_identifier)
    return nodes_by_coordinates, nodes_by_id

def getNodeId(location:Location, nodes_by_coordinates):
    node_coordinates = str(round(location.latitude, 6)) + "_" + str(round(location.longitude, 6))
    return nodes_by_coordinates.get(node_coordinates)


def isIntersection(location: Location, intersections):
    locationConverted = str(round(location.latitude, 6)) + "_" + str(round(location.longitude, 6))
    result = locationConverted in intersections
    return result

def getRouteCountFromNode(node_id, edges):
    routesWhereFirst = None
    try:
        routesWhereFirst = edges.loc[[node_id]]
    except:
        pass
    
    routesWhereSecond = None
    try:
        routesWhereSecond = edges.xs(node_id, axis=0, level=1, drop_level=False)
    except:
        pass

    routes = pd.concat([routesWhereFirst, routesWhereSecond])
    return routes.shape[0]

# Intersection Methods --------------------------------------------------------------------------------------------
def getMapEdgesForEachNode(gdfEdges, nodesDict, nodes_by_coordinates):
    edgesByNodeId = {}
    edgesDict = {}
    
    nodeIds =  [*nodesDict]
    
    for nodeId in nodeIds:
        #filter edges where given nodeId is starting node of route
        routesWhereFirst = None
        try:
            routesWhereFirst = gdfEdges.loc[[nodeId]]
        except:
            pass


        #filter edges where given nodeId is end node of route, but node is bidirectional
        routesWhereSecond = None
        try:
            routesWhereSecond = gdfEdges.xs(nodeId, axis=0, level=1, drop_level=False)
            #bidirectionalRoutesWhereSecond = routesWhereSecond[routesWhereSecond.oneway.eq(True)]
            #concat edges to single dataframe
        except:
            pass

        edges = pd.concat([routesWhereFirst, routesWhereSecond])
        
        #single node can be assigned to multpile edges, therefor we store them into a list
        listOfMapEdgesForGivenNode = []
        for index, row in edges.iterrows():
            mapEdge = MapEdge(row, nodes_by_coordinates)
            edgesDict[mapEdge.edgeId] = mapEdge
            listOfMapEdgesForGivenNode.append(mapEdge)
            
        #list of edges is stored in output directory under nodeId as a key
        edgesByNodeId[nodeId] = listOfMapEdgesForGivenNode
        
    return edgesByNodeId, edgesDict

def getPossibleRouteSequels(route, edgesByNodeId):   #TODO in case route can not be extended, it is thrown away in current implementation
    #print(f"get possible route sequels route list:{route}")
    currentLocation = route[-1]
    routeSequels = []
    edgesFromCurrentLocation = edgesByNodeId[currentLocation.osmnxNode]
    
    if (len(edgesFromCurrentLocation) == 1):
        return [route]
    else:
        for edge in edgesFromCurrentLocation:
            otherEndOfEdge = edge.getOppsiteEnd(currentLocation)
            
            if (len(route)>1):
                previousLocation = route[-2] #TODO in case there is no previous, method should work work anyway 

                if(otherEndOfEdge.osmnxNode != previousLocation.osmnxNode):
                    newroute = copy.deepcopy(route)
                    newroute.append(otherEndOfEdge)
                    routeSequels.append(newroute)
            else:
                newroute = copy.deepcopy(route)
                newroute.append(otherEndOfEdge)
                routeSequels.append(newroute)

        return routeSequels
    


def getRoutesV0(routes, edgesByNodeId):
    newRoutes = []
    for route in routes:
        newRoutes = newRoutes + getPossibleRouteSequels(route,edgesByNodeId)
        
    return newRoutes

def getRoutesWithIterations(routes, edgesByNodeId, numberOfEdges):
    for i in range(0, numberOfEdges):
        newRoutes = []
        for route in routes:
            newRoutes = newRoutes + getPossibleRouteSequels(route,edgesByNodeId)
        routes = newRoutes
    return newRoutes




def printIntersectionNodesWithRoutes(edgesByNodeId):
    hs = open("NodesTest.txt","a")
    for key, edgesList in edgesByNodeId.items():
        for edge in edgesList:
            startNode = f"{edge.startLocation.latitude}, {edge.startLocation.longitude}, START Uzol-{key}_Krizovatka-{edge.osmid}\n"
            endNode = f"{edge.endLocation.latitude}, {edge.endLocation.longitude}, END Uzol-{key}_Krizovatka-{edge.osmid}\n"
            #print(startNode)
            #print(endNode)
            hs.write(startNode)
            hs.write(endNode)
    hs.close()


location = Location(48.709936, 21.238923)
radius = 200 #
driveGraph = ox.graph_from_point((location.latitude, location.longitude), dist=radius, network_type='drive', simplify=False)
driveGraph = driveGraph.to_undirected()
gdfNodes, gdfEdges = ox.graph_to_gdfs(driveGraph)
#ox.plot_graph(driveGraph)


intersections_by_coordinates, intersections_by_ids = getIntersectionDicts(gdfNodes)
nodesByCoordinatesDict, nodes_by_id = getNodeDicts(gdfNodes)

edgesByNodeId, edgesDict = getMapEdgesForEachNode(gdfEdges, nodes_by_id, nodesByCoordinatesDict)


node_coordinates = str(round(48.709942, 6)) + "_" + str(round(21.2371895, 6))
this_osm_id = nodesByCoordinatesDict.get(node_coordinates)

#just print all intersections
#print("-------- Intersections ------------")
#for index, node in gdfNodes.iterrows():
#    node_coordinates = str(round(node["y"], 6)) + ", " + str(round(node["x"], 6))
#    route_count = getRouteCountFromNode(index, gdfEdges)
#    if route_count > 2:
#        print(f"{node_coordinates}")

#printIntersectionNodesWithRoutes(edgesByNodeId)
#intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]


# firstLocation = nodes_by_id.get(5381478638)
# secondLocation = nodes_by_id.get(242958683)

# route= [firstLocation, secondLocation]

#v0routes = getRoutesV0([[firstLocation, secondLocation, thirdLocation]], 3, edgesByNodeId)


# routes = [route]

#for i in range(0,10):
#    routes = getRoutesV0(routes, edgesByNodeId)
    

# routes  = getRoutesWithIterations(routes, edgesByNodeId, 3)

# routeIndex = 1
# for route in routes:
#     print(f" ---------- route # {routeIndex}")
#     locationIndex = 1
#     for location in route:
#         print(f"{location.toTestString()}, route#{routeIndex} step#{locationIndex}")
#         locationIndex = locationIndex + 1
#     routeIndex = routeIndex + 1


    

