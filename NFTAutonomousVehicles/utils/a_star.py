from collections import defaultdict
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import reduce
from heapq import heappush, heappop
from pickletools import stackslice
from turtle import distance
from typing import Any, DefaultDict, Dict, Iterator, List, NamedTuple, Tuple, TypeVar, Union
from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.taskProcessing.NFT import NFT
from NFTAutonomousVehicles.taskProcessing.SolverFinder import SolverFinder
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.utils import path_utils
from src.common.Location import Location
import networkx as nx
from src.city.grid.MapGrid import MapGrid
from src.common.CommonFunctions import CommonFunctions
from src.placeable.movable.Vehicles.Vehicle import Vehicle

class Node(NamedTuple):
    osmnx_node: int
    timestamp: datetime


class Metrics(NamedTuple):
    missing: int
    rbs: int
    distance: float

_inf = 9999999999999999999999999
_InfinityMetric = lambda: Metrics(_inf, _inf, float(_inf))
_ZeroMetric = lambda: Metrics(0, 0, 0.0)


class CameFromData(NamedTuple):
    node: Node
    nft_dict: Dict[datetime, NFT]
    location_dict: Dict[datetime, Location]


class Result(NamedTuple):
    path: List[Location]
    nft_dict: Dict[datetime, NFT]
    location_dict: Dict[datetime, Location]


M = TypeVar('M')
def add_tuples(a: M, b: M) -> M:
    return type(a)(*tuple(map(sum,zip(a,b))))


def node_to_loc(graph: nx.Graph, node) -> Location:
    lat, long = graph.nodes[node]['y'], graph.nodes[node]['x']
    return Location(lat, long, osmnxNode=node)


def reconstruct_path(G: nx.Graph, came_from: Dict[Node, CameFromData], current: Node) -> Result:
    total_path = [node_to_loc(G, current.osmnx_node)]

    nft_dict = {}
    loc_dict = {}

    while current in came_from.keys():
        current_data = came_from[current]

        nft_dict.update(current_data.nft_dict)
        loc_dict.update(current_data.location_dict)

        current = current_data.node
        l = node_to_loc(G, current.osmnx_node)
        total_path.insert(0, l)

    return Result(total_path, nft_dict, loc_dict)


class AStarMetric:
    def __init__(
        self,
        graph: nx.Graph,
        dt: float,
        map_grid: MapGrid,
        solver_coll_names: List[str],
        solver_finder: SolverFinder,
    ) -> None:
        self.graph = graph
        self.step = 0
        self.com = CommonFunctions()
        self.cache_distance = {}
        self.dt = dt
        self.map_grid = map_grid
        self.solver_coll_names: List[str] = solver_coll_names
        self.solver_finder = solver_finder

    def search_path(
        self,
        origin: int,
        destination: int,
        origin_timestamp: datetime,
        vehicle: AutonomousVehicle,
        longest_distance: float,
    ) -> Union[Result, None]:
        origin_node = Node(origin, origin_timestamp)

        stack: List[Tuple[Metrics,Node]] = []
        came_from: Dict[Node, CameFromData] = {}

        g_score: DefaultDict[Node, Metrics] = defaultdict(lambda: _InfinityMetric())
        g_score[origin_node] = _ZeroMetric()

        f_score: DefaultDict[Node, Metrics] = defaultdict(lambda: _InfinityMetric())
        f_score[origin_node] = self.h(origin, destination)

        heappush(stack, (*f_score[origin_node], origin_node.osmnx_node, origin_node))

        while len(stack) > 0:
            current_node = heappop(stack)[-1]

            if current_node.osmnx_node == destination:
                return reconstruct_path(self.graph, came_from, current_node)

            for neighbor in self._neighbours(current_node, came_from):
                g_metrics, neighbor_node, t_nft, t_loc = self.g(current_node, neighbor, vehicle)
                tentative_g_score = add_tuples(g_score[current_node], g_metrics)

                if tentative_g_score < g_score[neighbor_node] and tentative_g_score.distance <= longest_distance:
                    came_from[neighbor_node] = CameFromData(current_node, t_nft, t_loc)
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = add_tuples(tentative_g_score, self.h(neighbor, destination))

                    if neighbor_node not in stack:
                        heappush(stack, (*f_score[neighbor_node], neighbor_node.osmnx_node, neighbor_node))
        return None

    def _neighbours(self, current_node: Node, came_from: Dict[Node, CameFromData]) -> Generator[int, None, None]:
        for n in self.graph.neighbors(current_node.osmnx_node):
            if current_node not in came_from:
                yield n
            elif n != came_from[current_node].node.osmnx_node:
                yield n


    def g(self, node1: Node, node2: int, vehicle: AutonomousVehicle) -> Tuple[Metrics, Node]:
        node1_loc = node_to_loc(self.graph, node1.osmnx_node)
        node2_loc = node_to_loc(self.graph, node2)

        gen = path_utils.location_from_path_generator(
            [node1_loc, node2_loc], vehicle.getSpeed())

        route_step = 0
        timestamp = node1.timestamp
        timestamp_nft_dict = {}
        timestamp_location_dict = {}
        first = True
        vehicle_loc = copy.deepcopy(vehicle.getLocation())
        for current_loc in gen:

            if first:
                first = not first
                continue

            route_step += 1
            timestamp = timestamp + timedelta(seconds=self.dt)

            timestamp_location_dict[timestamp] = current_loc

            vehicle.setLocation(current_loc)

            dummy_task = Task(vehicle=vehicle,size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                                  created_at=timestamp, limit_time=vehicle.sample_task.limit_time, deadline_at=timestamp+timedelta(seconds=vehicle.sample_task.limit_time),
                                  instruction_count=vehicle.sample_task.instruction_count,
                                  solving_time=vehicle.sample_task.solving_time)

            obtained_nft = self.solver_finder.searchForTaskSolverSINR(
                                    self.map_grid, dummy_task, self.solver_coll_names)

            if obtained_nft is not None:
                timestamp_nft_dict[timestamp] = obtained_nft

        vehicle.setLocation(vehicle_loc)

        missing_nfts = route_step - len(timestamp_nft_dict)
        rbs = reduce(lambda a,b: a + b.reserved_rbs, timestamp_nft_dict.values(), 0)
        dist = self.com.getCuda2dDistance(node1_loc, node2_loc)

        return Metrics(missing_nfts, rbs, dist), Node(node2, timestamp), timestamp_nft_dict, timestamp_location_dict

    def h(self, node: int, destination: int) -> Metrics:
        key = (node,destination)

        if key in self.cache_distance:
            return Metrics(0, 0, self.cache_distance[key])

        d = self.com.getCuda2dDistance(
            node_to_loc(self.graph, node),
            node_to_loc(self.graph, destination),
        )
        self.cache_distance[key] = d
        return Metrics(0, 0, d)


class AStar:
    def __init__(self, graph, g, h) -> None:
        self.graph = graph

    def search_path(self, origin, destination):
        stack = []
        came_from = {}

        g_score = defaultdict(lambda: 99999999999.0)
        g_score[origin] = 0

        f_score = defaultdict(lambda: 99999999999.0)
        f_score[origin] = self.h(origin)

        heappush(stack, (f_score[origin], origin))

        while len(stack) > 0:
            current = heappop(stack)[-1]

            if current == destination:
                return reconstruct_path(came_from, current)

            for neighbor in self._neighbours:
                tentative_g_score = g_score[current] + self.g(current, neighbor)

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.h(neighbor)

                    if neighbor not in stack:
                        heappush(stack, (f_score[neighbor], neighbor))


    def _neighbours(self, current):
        pass

    def g(self, node1, node2):
        return 0

    def h(self, node):
        return 0