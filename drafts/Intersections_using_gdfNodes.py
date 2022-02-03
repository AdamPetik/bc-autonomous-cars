# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 10:30:51 2021

@author: marvo
"""
import osmnx as ox
import networkx as nx
import random
import pandas as pd
import json
from shapely.geometry import LineString



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

class MapEdge:

    def __init__(self, osmRow):
        self.osmid = osmRow['osmid']
        self.oneway = osmRow['oneway']
        self.lanes = osmRow['lanes']
        self.maxspeed = osmRow['maxspeed']
        self.length = osmRow['length']
        self.highway = osmRow['highway']
        self.geometry = osmRow['geometry']
        self.name = osmRow['name']
        self.startLocation = Location(self.geometry.coords[0][1], self.geometry.coords[0][0])
        self.endLocation = Location(self.geometry.coords[1][1], self.geometry.coords[1][0])



def getNearestNode(location: Location):
    if (location.osmnxNode is None):
        location.osmnxNode = ox.distance.nearest_nodes(driveGraph, location.longitude, location.latitude)
    return location.osmnxNode



























def getIntersections(gdfNodes):
    intersections_by_coordinates = {}
    intersections_by_id = {}

    intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]
    for index, node in intersection_nodes.iterrows():
        intersection_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
        intersection_identifier = index
        intersections_by_coordinates[intersection_coordinates] = intersection_identifier

        intersections_by_id[intersection_identifier] = Location(round(node["y"], 6), round(node["x"], 6), osmnxNode=intersection_identifier)
    return intersections_by_coordinates, intersections_by_id




def getIntersectionsV2(gdfNodes, gdfEdges):
    intersections_by_coordinates = {}
    intersections_by_id = {}

    nodes_set = set()
    
    
    
    
    
    
    edges_dict = {}

    for index, node in intersection_nodes.iterrows():
       intersection_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
       intersection_identifier = index
       intersections_by_coordinates[intersection_coordinates] = intersection_identifier
    


    intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]
    for index, node in intersection_nodes.iterrows():
        intersection_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
        intersection_identifier = index
        intersections_by_coordinates[intersection_coordinates] = intersection_identifier

        intersections_by_id[intersection_identifier] = Location(round(node["y"], 6), round(node["x"], 6), osmnxNode=intersection_identifier)
    return intersections_by_coordinates, intersections_by_id



























def isIntersection(location: Location, intersections):
    locationConverted = str(round(location.latitude, 6)) + "_" + str(round(location.longitude, 6))
    result = locationConverted in intersections
    return result


def getMapEdgesForEachNode(gdfEdges, intersectionsByIdsDict):
    edgesByNodeId = {}
    edgesDict = {}
    
    nodeIds =  [*intersectionsByIdsDict]
    
    for nodeId in nodeIds:
        #filter edges where given nodeId is starting node of route
        routesWhereFirst = None
        try:
            routesWhereFirst = gdfEdges.loc[[nodeId]]
        except:
            pass


        #filter edges where given nodeId is end node of route, but node is bidirectional
        bidirectionalRoutesWhereSecond = None
        routesWhereSecond = None
        try:
            routesWhereSecond = gdfEdges.xs(nodeId, axis=0, level=1, drop_level=False)
            #bidirectionalRoutesWhereSecond = routesWhereSecond[routesWhereSecond.oneway.eq(True)]
            #concat edges to single dataframe
        except:
            pass

        routes = pd.concat([routesWhereFirst, routesWhereSecond])

        #single node can be assigned to multpile edges, therefor we store them into a list
        listOfMapEdges = []
        for index, row in routes.iterrows():
            if(row['osmid'] in edgesDict):
                mapEdge = edgesDict[row['osmid']]
            else:
                mapEdge = MapEdge(row)
            listOfMapEdges.append(mapEdge)
            edgesDict[mapEdge.osmid] = mapEdge
        #list of edges is stored in output directory under nodeId as a key
        edgesByNodeId[nodeId] = listOfMapEdges
        
    return edgesByNodeId, edgesDict



def printIntersectionNodesWithRoutes(edgesByNodeId):
    hs = open("NodesTest.txt","a")
    for key, edgesList in edgesByNodeId.items():
        for edge in edgesList:
            startNode = f"{edge.startLocation.latitude}, {edge.startLocation.longitude}, START Uzol-{key}_Krizovatka-{edge.osmid}\n"
            endNode = f"{edge.endLocation.latitude}, {edge.endLocation.longitude}, END Uzol-{key}_Krizovatka-{edge.osmid}\n"
            print(startNode)
            print(endNode)
            hs.write(startNode)
            hs.write(endNode)
    hs.close()


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



location = Location(48.7018419, 21.2344516)
radius = 400


driveGraph = ox.graph_from_point((location.latitude, location.longitude), dist=radius, network_type='drive', simplify=False)
driveGraph = driveGraph.to_undirected()
gdfNodes, gdfEdges = ox.graph_to_gdfs(driveGraph)

intersection_nodes = gdfNodes[gdfNodes['street_count'] > 2]


for index, node in gdfNodes.iterrows():

    node_coordinates = str(round(node["y"], 6)) + "_" + str(round(node["x"], 6))
    route_count = getRouteCountFromNode(index, gdfEdges)
    
    if route_count > 2:
        print(f"{index} - {node_coordinates}  - routecount: {route_count}")
    
    
#ox.plot_graph(driveGraph)
#intersections_by_coordinates, intersections_by_ids = getIntersections(gdfNodes)
#edgesByNodeId, edgesDict = getMapEdgesForEachNode(gdfEdges, intersections_by_ids)

#printIntersectionNodesWithRoutes(edgesByNodeId)



