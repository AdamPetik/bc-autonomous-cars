from typing import List, Tuple
from NFTAutonomousVehicles.utils.sinr_map import SINRMap
from src.city.Map import Map
from src.common.Location import Location
from . import path_utils
from . import sinr


class SINRRouteALG:
    def __init__(self,
        map: Map,
        sinr_limit: float,
        dist: float,
        t_coef: float,
        sinr_map: SINRMap,
        speed_ms: float,
        base_stations: list,
    ) -> None:
        self.map = map
        self.dist = dist
        self.t_coef = t_coef
        self.sinr_limit = sinr_limit
        self.sinr_map = sinr_map
        self.speed_ms = speed_ms
        self.base_stations = base_stations

    def plan_route(self,
        l1: Location,
        l2: Location,
        vehicle_speed_ms: float = None,
    ) -> Tuple[List[Location], list]:
        """[summary]

        Args:
            l1 (Location): Origin location.
            l2 (Location): Destinaton location.
            vehicle_speed_ms (float, optional): Vehicle speed. If not specified,
                    self.speed is used. Defaults to None.

        Returns:
            Tuple[List[Location], list]:
                best route as list of locations, best route as list of nodes ids
        """
        if vehicle_speed_ms is None:
            vehicle_speed_ms = self.speed_ms

        # get shortest path and calculate the shortest and the longest allowed
        # travel times
        shortest_path, raw_path = path_utils.get_shortest_path(
                                                    self.map, l1, l2)

        t_shortest = path_utils.path_time(self.map, raw_path, vehicle_speed_ms)
        t_longest = self.t_coef * t_shortest

        best_route = (shortest_path, 999999999)

        for path, raw_path in path_utils.get_shortest_paths(
            self.map, l1, l2,
            break_condition=path_utils.break_condition_time(
                t_longest,
                vehicle_speed_ms,
            )
        ):
            # get "normalized path"
            normalized_path = path_utils.normalize_path(path, self.dist)

            # count low sinr nodes
            sinr_under_count = self.count_unsatisfying_sinr_nodes(
                normalized_path,
            )

            if sinr_under_count == 0:
                # all sinr levels are above min sinr so the route is
                # the shortest possible and QoS is assured by sinr
                return path, shortest_path

            # check if this route is better than the current best route
            if sinr_under_count < best_route[1]:
                best_route = (path, sinr_under_count)

        return best_route[0], shortest_path

    def count_unsatisfying_sinr_nodes(self, locs: List[Location]) -> int:
        count = 0
        for l in locs:
            sinr_value = self.sinr_map.get_loc(l)
            if sinr_value == self.sinr_map.init_sinr_val:
                sinr_value, _ = sinr.calculate_highest_sinr(l, self.base_stations)
                self.sinr_map.update_loc(l, sinr_value)

            if sinr_value < self.sinr_limit:
                count += 1
        return count
