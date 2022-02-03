# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 11:26:38 2021

@author: marvo
"""

import geopy.distance
import math

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
        



def getReal2dDistance(first:Location, second:Location):
    coords_1 = (first.latitude, first.longitude)
    coords_2 = (second.latitude, second.longitude)
    return geopy.distance.geodesic(coords_1, coords_2).m

def get2dCoordDistance(first=Location, second=Location):
    latDifference = first.latitude - second.latitude
    lonDifference = first.longitude - second.longitude
    coorDistance = math.sqrt(math.pow(latDifference, 2) + math.pow(lonDifference, 2))
    return coorDistance


print("0.5")
real1 = Location(48.7095434, 21.2400651)
real2 = Location(48.70956091212842, 21.240058862961977)


predicted = Location(48.70955653409632, 21.24006042222149)


print(f"realna: {getReal2dDistance(real1, real2)}  vs {get2dCoordDistance(real1, real2)}")
print(f"predikovana: {getReal2dDistance(real1, predicted)}")


print("0.1")

real1 = Location(48.7095434, 21.2400651)
real2 = Location(48.70954690242571,21.240063852592403)
predicted = Location(48.709545326334144, 21.24006441392582)
print(f"realna: {getReal2dDistance(real1, real2)}")
print(f"predikovana: {getReal2dDistance(real1, predicted)}")



print("0.2")
real1 = Location(48.7095434, 21.2400651)
real2 = Location(48.70955040485138, 21.2400626051848)
predicted = Location(48.70954760291084, 21.240063603110883)
print(f"realna: {getReal2dDistance(real1, real2)}")
print(f"predikovana: {getReal2dDistance(real1, predicted)}")








