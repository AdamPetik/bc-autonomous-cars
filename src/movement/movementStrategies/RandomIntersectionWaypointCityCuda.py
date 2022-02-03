from __future__ import division

import copy

from numba import cuda
import math, time
import numpy as np
from src.common.Location import Location
from src.movement.movementStrategies.MovementStrategy import MovementStrategy

# CUDA kernel
from src.placeable.movable.Person import Person


@cuda.jit
def walking_kernel(io_array):
    def toRadians(degrees):
        return degrees * math.pi / 180

    def toDegrees(radians):
        return radians * 180 / math.pi

    pos = cuda.grid(1)

    latStep = io_array[pos, 11]
    latMin = io_array[pos, 12]

    lonStep = io_array[pos, 13]
    lonMin = io_array[pos, 14]

    if pos < io_array.size:
        lat1 = io_array[pos, 0]
        lon1 = io_array[pos, 1]
        lat2 = io_array[pos, 3]
        lon2 = io_array[pos, 4]
        distanceToWalk = io_array[pos, 6]  # speed actually

        d = distanceToWalk
        R = 6371000
        lat1rad = math.radians(lat1)
        lat2rad = math.radians(lat2)
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(lat1rad) * math.cos(lat2rad) * math.sin(
            dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distanceBetweenPoints = R * c

        # io_array[pos, 8] = distanceBetweenPoints   NO IDEA WHAT THIS SUPPOSED TO DO

        if (distanceToWalk >= distanceBetweenPoints):
            io_array[pos, 0] = lat2
            io_array[pos, 1] = lon2
            io_array[pos, 7] = True
        else:
            io_array[pos, 7] = False
            lat1rad = toRadians(lat1)
            lon1rad = toRadians(lon1)

            lat2rad = toRadians(lat2)
            diffLong = toRadians(lon2 - lon1)

            x = math.sin(diffLong) * math.cos(lat2rad)
            y = math.cos(lat1rad) * math.sin(lat2rad) - (math.sin(lat1rad) * math.cos(lat2rad) * math.cos(diffLong))
            initial_bearing = math.atan2(x, y)
            initial_bearing = toDegrees(initial_bearing)
            brng = toRadians((initial_bearing + 360) % 360)

            lat3rad = math.asin(
                math.sin(lat1rad) * math.cos(d / R) + math.cos(lat1rad) * math.sin(d / R) * math.cos(brng))
            lon3rad = lon1rad + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(lat1rad),
                                           math.cos(d / R) - math.sin(lat1rad) * math.sin(lat2rad))
            lat3 = toDegrees(lat3rad)
            lon3 = toDegrees(lon3rad)

            io_array[pos, 0] = lat3
            io_array[pos, 1] = lon3

            io_array[pos, 8] = int((lat3 - latMin) // latStep)
            io_array[pos, 9] = int((lon3 - lonMin) // lonStep)


class RandomIntersectionWaypointCityCuda(MovementStrategy):

    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType):
        super(RandomIntersectionWaypointCityCuda, self).__init__(locationsTable, movableSet, map, mapGrid, strategyType)

    def move(self):
        # print("PRED move-------\n", self.locationsTable.table)
        threadsperblock = 256
        blockspergrid = math.ceil(len(self.locationsTable.table) / threadsperblock)
        # print(f"Size of locations table | shape:{self.locationsTable.table.shape} size:{self.locationsTable.table.size}"
        #       f" | threadsperblock: {threadsperblock}   blockspergrid: {blockspergrid}")
        walking_kernel[blockspergrid, threadsperblock](self.locationsTable.table)
        # print("PO move-------\n", self.locationsTable.table)

    # def move_size_test(self):
    #     # print("PRED move-------\n", self.locationsTable.table)
    #     for i in range(0, 100000):
    #         print(f"testing numpy step {i}")
    #         rep = 5001
    #         last = np.repeat([self.locationsTable.table[-1]], repeats=rep - 1, axis=0)
    #         self.locationsTable.table = np.vstack([self.locationsTable.table, last])
    #
    #         threadsperblock = 256
    #         blockspergrid = math.ceil(len(self.locationsTable.table) / threadsperblock)
    #         print(f"Size of locations table | shape:{self.locationsTable.table.shape} size:{self.locationsTable.table.size}"
    #               f" | threadsperblock: {threadsperblock}   blockspergrid: {blockspergrid}")
    #         walking_kernel[blockspergrid, threadsperblock](self.locationsTable.table)
    #         # print("PO move-------\n", self.locationsTable.table)
    #         time.sleep(10)

    # def move_fix_attempt(self):
    #     # print("PRED move-------\n", self.locationsTable.table)
    #     for i in range(0, 100000):
    #         print(f">>>>>>>>>testing numpy step {i}")
    #         rep = 5001
    #         last = np.repeat([self.locationsTable.table[-1]], repeats=rep - 1, axis=0)
    #         self.locationsTable.table = np.vstack([self.locationsTable.table, last])
    #
    #         for split_into in (2**p for p in range(0, 12)):
    #             loc_table = copy.deepcopy(self.locationsTable.table)
    #
    #             print(f"splitting table into {split_into} parts")
    #             split_table_as_arrays = np.array_split(loc_table, split_into)
    #
    #             for table_part in split_table_as_arrays:
    #                 threadsperblock = 256
    #                 blockspergrid = math.ceil(len(table_part) / threadsperblock)
    #                 try:
    #                     walking_kernel[blockspergrid, threadsperblock](table_part)
    #                     print(f"succesfull kernel use with table of shape: {table_part.shape}")
    #                     break
    #                 except:
    #                     print(f"Failed to start kernel with table shape: {table_part.shape}")
    #                     break
    #             self.locationsTable.table = loc_table
    #
    #             # return
    #         # raise ValueError(f"Shape of table is too large to handle :{self.locationsTable.table.shape}")


    def getNewRoute(self, walkable):
        return self.map.getRouteBetweenNodes(walkable.getLocation(),
                                             self.map.getRandomIntersectionNode(walkable.getLocation()))

    def getRouteTo(self, walkable, location: Location):
        return self.map.getRouteBetweenNodes(walkable.getLocation(), location)

    def onDayChange(self, person: Person):
        '''
        No activity is needed on day change for this Strategy
        :param person:
        :return:
        '''
        return
