from NFTAutonomousVehicles.utils.sinr_route_alg import SINRRouteALG
from NFTAutonomousVehicles.utils.statistics import MeanEvent, Statistics
from src.common.Location import Location
from src.movement.movementStrategies.PreloadedLocationsStrategy import PreloadedLocationsStrategy
from src.placeable.movable.Movable import Movable
import src.common.SimulationClock as simclock
from NFTAutonomousVehicles.utils import path_utils


class SINRAwareMovementStrategy(PreloadedLocationsStrategy):
    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType,
                route_alg: SINRRouteALG, dt: float):
        super().__init__(locationsTable, movableSet, map, mapGrid, strategyType)
        self.routing_alg = route_alg
        self.dt = dt

    def getNewRoute(self, walkable: Movable):
        l1 = walkable.getLocation()
        l2 = self.map.getRandomNode(l1)
        return self.getRouteTo(walkable, l2)

    def getRouteTo(self, walkable: Movable, location: Location):
        best_route, shortest_route = self.routing_alg.plan_route(
                walkable.getLocation(), location, walkable.getSpeed() / self.dt)
        dict_ = path_utils.get_loc_with_time(
                best_route, walkable.getSpeed(), self.dt, simclock.getDateTime())

        prolongation = path_utils.path_length_diff(
                                        self.map, best_route, shortest_route)
        Statistics().mean_event(MeanEvent.ROUTE_PROLONGATION, prolongation)

        self.preloadLocationsDictForWalkable(walkable, dict_)

        return best_route

    def onDayChange(self, walkable):
        return

    def move(self):
        for actorId in self.locationsTable.getAllIds():
            walkable: Movable = self.movableSet[int(actorId)]
            l: Location = self.getPreloadedLocation(walkable, simclock.getDateTime())
            walkable.setLocation(l)

            dest_node = walkable.getCurrentMovementActivity().destination.osmnxNode
            if l.osmnxNode is not None and dest_node == l.osmnxNode:
                walkable.setTargetReached(True)
                walkable.removeFirstActivity()