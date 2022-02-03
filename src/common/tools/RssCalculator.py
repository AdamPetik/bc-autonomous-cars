from src.city.grid.MapGrid import MapGrid
from src.movement.ActorCollection import ActorCollection
import math
from src.common.CommonFunctions import CommonFunctions

class RssCalculator:

    def __init__(self, actorCollections, mapGrid = MapGrid):
        self.mapGrid = mapGrid
        self.actorCollections = actorCollections
        self.com = CommonFunctions()

    def updateRssOfAllCells(self):
        grid = self.mapGrid.grid

        for x in range(self.mapGrid.rows):
            for y in range(self.mapGrid.rows):
                cell = grid[x][y]
                cell.location.setAltitude(1.8)
                cell.rss = self.getRssAtLocation(cell.location)

    def udateRssOfCellsWithActors(self, collectionNames):

        grid = self.mapGrid.grid

        for x in range(self.mapGrid.rows):
            for y in range(self.mapGrid.rows):
                cell = grid[x][y]
                cell.location.setAltitude(1.8)
                cell.rss = self.getRssAtLocation(cell.location)

                # Calculate RSS only when agents from collections are present
                # if(len(self.mapGrid.getMovablesAtXYFromCollections(collectionNames,x,y)) > 0):
                #     cell = grid[x][y]
                #     cell.location.setAltitude(1.8)
                #     cell.rss = self.getRssAtLocation(cell.location)
                # else:
                #     cell.rss=0

    def getRssAtLocation(self, location):

        nearBTSs = self.mapGrid.getClosestActorsFromV2(0, self.actorCollections, location)
        closestBTS = self.com.getClosestActorFromList(location,nearBTSs)
        distance = self.com.getReal2dDistance(location, closestBTS.getLocation())

        log10_f = math.log10(closestBTS.Tx_frequency)
        log10_hb = math.log10(closestBTS.getLocation().getAltitude())
        Tx_dBm = 10 * math.log10(closestBTS.Tx_power) + 30
        correction = 0.8 + (1.1 * log10_f - 0.7) * location.getAltitude() - 1.56 * log10_f
        path_loss_hata = 69.55 + 26.16 * log10_f - 13.82 * log10_hb - correction + \
                         (44.9 - 6.55 * log10_hb) * math.log10(distance)
        P_Tx_dB = Tx_dBm - path_loss_hata
        rss = math.pow(10, (P_Tx_dB / 10))
        print("distance =", round(distance, 5), " | rss=", rss)
        return rss