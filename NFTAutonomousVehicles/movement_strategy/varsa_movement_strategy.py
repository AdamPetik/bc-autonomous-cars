from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from email.policy import default
import math
from typing import Any, Generator, Iterator, List, NamedTuple, Optional, Tuple
from NFTAutonomousVehicles.utils.sinr_map import SINRMap
from NFTAutonomousVehicles.utils.sinr_route_alg import SINRRouteALG
from NFTAutonomousVehicles.utils.statistics import MeanEvent, Statistics
from src.city.Map import Map
from src.common.Location import Location
from src.movement.movementStrategies.PreloadedLocationsStrategy import PreloadedLocationsStrategy
from src.placeable.movable.Movable import Movable
import src.common.SimulationClock as simclock
from NFTAutonomousVehicles.utils import path_utils
import abc
from src.common.SimulationClock import timestampToMillisecondsSinceStart, getDateTime
from NFTAutonomousVehicles.utils import sinr
from NFTAutonomousVehicles.utils.radio_data_rate import RadioDataRate


def second_precision_to_round_precision(second_precision: float) -> int:
    return -3 + math.ceil(abs(Decimal(second_precision).log10()))

def round_to_millis(timestamp: datetime, precision: int) -> int:
    miliseconds = timestampToMillisecondsSinceStart(timestamp)
    return int(round(miliseconds, precision))

class DescreteTimeResource:
    def __init__(self, default=None, precision_sec=0.1) -> None:
        self._dict = defaultdict(lambda: default)
        self._precision_sec = precision_sec
        self._round_precision = -3 + math.ceil(abs(Decimal(precision_sec).log10()))

    def get(self, k: datetime):
        return self._dict[self._convert_to_key(k)]

    def set(self, k: datetime, value) -> None:
        self._dict[self._convert_to_key(k)] = value

    def set_interval(self, k_start: datetime, k_end: datetime, value) -> None:
        for k in self._key_iter(k_start, k_end):
            self._dict[k] = value

    def get_interval(self, k_start: datetime, k_end: datetime) -> list:
        result = []
        for k in self._key_iter(k_start, k_end):
            result.append(self._dict[k])
        return result

    def decrease_interval(self, k_start: datetime, k_end: datetime, value) -> list:
        for k in self._key_iter(k_start, k_end):
            self._dict[k] -= value

    def _key_iter(self, k_start: datetime, k_end: datetime) -> Generator[int, None, None]:
        step = int(self._precision_sec * 1000)

        k_start = self._convert_to_key(k_start)
        k_end = self._convert_to_key(k_end)

        for k in range(k_start, k_end, step):
            yield k

    def _convert_to_key(self, timestamp: datetime) -> int:
        return round_to_millis(timestamp, self._round_precision)


class RouteAlg(abc.ABC):
    @abc.abstractmethod
    def plan_route(
        self, source: Location, dest: Location, speed_ms: float,
    ) -> Tuple[List[Location], List[Location]]:
        pass


class _FakeReservation(NamedTuple):
    interval: Tuple[datetime, datetime]
    bs: Any
    rbs_amount: int


def _handle_reservation_overlap(
    r1: _FakeReservation, r2: _FakeReservation, second_precision: float,
) -> Tuple[_FakeReservation, _FakeReservation]:
    start1, end1 = r1.interval
    start2, end2 = r2.interval

    round_precision = second_precision_to_round_precision(second_precision)

    if (
        round_to_millis(end1, round_precision)
        != round_to_millis(start2, round_precision)
    ):
        return r1, r2


    end1_millis = timestampToMillisecondsSinceStart(end1)
    end1_rounded = round_to_millis(end1, round_precision)

    if end1_millis < end1_rounded:
        end1 = end1 - timedelta(seconds=second_precision)
    else:
        start2 = start2 + timedelta(seconds=second_precision)

    return (
        _FakeReservation((start1, end1), r1.bs, r1.rbs_amount),
        _FakeReservation((start2, end2), r2.bs, r2.rbs_amount),
    )


def _join_reservations(
    rs: List[_FakeReservation],
    second_precision: float,
) -> Generator[_FakeReservation, None, None]:
    if not rs:
        return []
    handled = [rs[0]]
    for reservation in rs[1:]:
        last = handled[-1]
        r1, r2 = _handle_reservation_overlap(last, reservation, second_precision)
        handled[-1] = r1
        handled.append(r2)
    return handled



class VaRSARouteAlg(RouteAlg):
    def __init__(
        self,
        map: Map,
        sinr_map: SINRMap,
        normalization_dist: float,
        t_coef: float,
        base_stations: list,
        required_datarate: float,
    ) -> None:
        super().__init__()
        self.map = map
        self.sinr_map = sinr_map
        self.dist = normalization_dist
        self.t_coef = t_coef
        self.base_stations = base_stations
        self._free_rb_mapping = {
            bs.id: DescreteTimeResource(bs.resource_blocks, precision_sec=0.1)
            for bs in base_stations
        }
        self._sinr_limit = -6.7
        self._best_bs_cache = defaultdict()
        self.required_datarate = required_datarate

    def plan_route(
        self, source: Location, dest: Location, speed_ms: float
    ) -> Tuple[List[Location], List[Location]]:
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

        # get shortest path and calculate the shortest and the longest allowed
        # travel times
        shortest_path, raw_path = path_utils.get_shortest_path(
                                                    self.map, source, dest)

        t_shortest = path_utils.path_time(self.map, raw_path, speed_ms)
        t_longest = self.t_coef * t_shortest

        best_route = (shortest_path, 999999999, [])

        time_between_sections = timedelta(seconds=self.dist / speed_ms)

        for path, raw_path in path_utils.get_shortest_paths(
            self.map, source, dest,
            break_condition=path_utils.break_condition_time(
                t_longest,
                speed_ms,
            )
        ):
            # get "normalized path"
            normalized_path = path_utils.normalize_path(path, self.dist)

            # count low sinr nodes
            under_qos_count, reservations = self.count_under_qos_nodes(
                normalized_path,
                time_between_sections,
            )

            if under_qos_count == 0:
                # all sinr levels are above min sinr so the route is
                # the shortest possible and QoS is assured by sinr
                self._decrease_rbs(reservations)
                return path, shortest_path

            # check if this route is better than the current best route
            if under_qos_count < best_route[1]:
                best_route = (path, under_qos_count, reservations)

        self._decrease_rbs(best_route[-1])
        return best_route[0], shortest_path

    def _decrease_rbs(self, reservations: List[_FakeReservation]) -> None:
        for r in _join_reservations(reservations):
            self._free_rb_mapping[r.bs.id].decrease_interval(
                *r.interval, r.rbs_amount,
            )


    def count_under_qos_nodes(
        self,
        path: List[Location],
        time_between_sections: timedelta,
    ) -> Tuple[int, List[_FakeReservation]]:
        count = 0
        reservations = []
        start_t = getDateTime()
        for index, l in enumerate(path):
            if index == 0:
                dt = start_t + 1.5 * time_between_sections
            elif index == (len(path) - 1):
                dt = time_between_sections
            else:
                dt = time_between_sections / 2

            end_t = start_t + dt

            reservation = self._create_reservation(l, start_t, end_t)
            start_t = end_t

            if reservation is None:
                count += 1
                continue

            reservations.append(reservation)

        return count, reservations

    def _create_reservation(
        self,
        l: Location,
        start: datetime,
        end: datetime,
    ) -> Optional[_FakeReservation]:
        sinr_value = self.sinr_map.get_loc(l)

        if sinr_value == self.sinr_map.init_sinr_val:
            sinr_value, bs = sinr.calculate_highest_sinr(l, self.base_stations)
            self.sinr_map.update_loc(l, sinr_value)
            self._best_bs_cache[self._best_bs_cache_key(l)] = bs

        if sinr_value < self._sinr_limit:
            return None

        bs = self._best_bs_cache[self._best_bs_cache_key(l)]

        required_rbs = RadioDataRate.get_rb_count(sinr_value, self.required_datarate)
        free_rbs = self._free_rb_mapping[bs.id].get_interval(start, end)

        if any(rb < required_rbs for rb in free_rbs):
            return None

        reservation = _FakeReservation(
            interval=(start, end), bs=bs, rbs_amount=required_rbs
        )
        return reservation

    def _best_bs_cache_key(self, l: Location):
        if self.sinr_map.grid is None:
            return f"{l.getGridXcoor()}-{l.getGridYcoor()}"
        else:
            x, y = self.sinr_map.grid.coordinates(l)
            return f"{x}-{y}"


class RoutingAlgorithmMovementStrategy(PreloadedLocationsStrategy):
    def __init__(self, locationsTable, movableSet, map, mapGrid, strategyType,
                route_alg, dt: float):
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



def test():
    now = datetime(2020, 1, 1, 0, 0, 0, 0)

    next1 = now + timedelta(seconds=0.35)
    next2 = next1 + timedelta(seconds=0.35)
    next3 = next2 + timedelta(seconds=0.35)
    next4 = next3 + timedelta(seconds=0.35)

    r1 = _FakeReservation((now, next1), bs=None, rbs_amount=0)
    r2 = _FakeReservation((next1, next2), bs=None, rbs_amount=0)
    r3 = _FakeReservation((next2, next3), bs=None, rbs_amount=0)
    r4 = _FakeReservation((next3, next4), bs=None, rbs_amount=0)

    rs = [r1, r2, r3, r4]

    result = _join_reservations(rs, 0.1)

    print(rs)
    print("-----------")
    print(result)