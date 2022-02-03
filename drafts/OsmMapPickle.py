# -*- coding: utf-8 -*-
"""
Created on Tue Aug 10 10:53:40 2021

@author: marvo
"""
import osmnx as ox
import networkx as nx
import random
import pandas as pd
import json
from shapely.geometry import LineString
import copy
import pickle



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
        





location = Location(48.709936, 21.238923)
radius = 800
driveGraph = ox.graph_from_point((location.latitude, location.longitude), dist=radius, network_type='drive', simplify=False)
driveGraph = driveGraph.to_undirected()
gdfNodes, gdfEdges = ox.graph_to_gdfs(driveGraph)






with open('driveGrapPicke.pkl', 'wb') as outp:
    pickle.dump(driveGraph, outp, pickle.HIGHEST_PROTOCOL)

#del mapData



#
#with open('driveGrapPicke.pkl', 'rb') as inp:
#    mapData = pickle.load(inp)



