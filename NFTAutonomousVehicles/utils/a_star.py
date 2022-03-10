from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import reduce
from heapq import heappush, heappop
from pickletools import stackslice
from turtle import distance
from typing import Any, DefaultDict, Dict, Iterator, List, NamedTuple, Tuple, TypeVar
from NFTAutonomousVehicles.entities.AutonomousVehicle import AutonomousVehicle
from NFTAutonomousVehicles.taskProcessing.SolverFinder import SolverFinder
from NFTAutonomousVehicles.taskProcessing.Task import Task
from NFTAutonomousVehicles.utils import path_utils
from drafts.Intersections_using_gdfNodes import Location
import networkx as nx
from src.city.grid.MapGrid import MapGrid
from src.common.CommonFunctions import CommonFunctions

class Node(NamedTuple):
    osmnx_node: int
    step: int


class Metrics(NamedTuple):
    missing: int
    rbs: int
    distance: float

_inf = 9999999999999999999999999
_InfinityMetric = lambda: Metrics(_inf, _inf, float(_inf))
_ZeroMetric = lambda: Metrics(0, 0, 0.0)


M = TypeVar('M')
def add_tuples(a: M, b: M) -> M:
    return type(a)(*tuple(map(sum,zip(a,b))))


def node_to_loc(graph: nx.Graph, node) -> Location:
    lat, long = graph.nodes[node]['y'], graph.nodes[node]['x']
    return Location(lat, long, osmnxNode=node)


def reconstruct_path(came_from: Dict[Node, Node], current: Node):
    total_path = [current.osmnx_node]

    while current in came_from.keys():
        current = came_from[current]
        total_path.insert(0, current.osmnx_node)

    return total_path


class AStarMetric:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self.step = 0
        self.com = CommonFunctions()
        self.cache_distance = {}

    def search_path(self, origin: int, destination: int, origin_step: int):
        origin_node = Node(origin, origin_step)

        stack: List[Tuple[Metrics,Node]] = []
        came_from: Dict[Node, Node] = {}

        g_score: DefaultDict[Any, Metrics] = defaultdict(lambda: _InfinityMetric())
        g_score[origin_node] = _ZeroMetric()

        f_score: DefaultDict[Any, Metrics] = defaultdict(lambda: _InfinityMetric())
        f_score[origin_node] = self.h(origin, destination)

        heappush(stack, (*f_score[origin], origin_node.osmnx_node, origin_node))

        while len(stack) > 0:
            current_node = heappop(stack)[-1]

            if current_node.osmnx_node == destination:
                return reconstruct_path(came_from, current_node)

            for neighbor in self._neighbours(current_node.osmnx_node):
                g_score, neighbor_node = self.g(current_node, neighbor)
                tentative_g_score = add_tuples(g_score[current_node], g_score)

                if tentative_g_score < g_score[neighbor_node]:
                    came_from[neighbor_node] = current_node
                    g_score[neighbor_node] = tentative_g_score
                    f_score[neighbor_node] = add_tuples(tentative_g_score, self.h(neighbor, destination))

                    if neighbor_node not in stack:
                        heappush(stack, (*f_score[neighbor], neighbor))


    def _neighbours(self, current) -> Iterator[int]:
        return self.graph.neighbors(current)

    def g(self, node1: Node, node2: int) -> Tuple[Metrics, Node]:
        node1_loc = node_to_loc(self.graph, node1)
        node2_loc = node_to_loc(self.graph, node2)
        dist = 5
        gen = path_utils.location_from_path_generator(
            [node1_loc, node2_loc], dist)

        # DEPENDENCIES TO RESOLVE
        vehicle: AutonomousVehicle = None
        route_step = 0
        solver_finder: SolverFinder = None
        timestamp: datetime
        map_grid: MapGrid
        solver_coll_names: List[str] = ['ss']
        dt = 0.5

        timestamp_nft_dict = {}

        for current_loc in gen:
            # TODO skip first loc
            vehicle.setLocation(current_loc)

            dummy_task = Task(vehicle=vehicle,size_in_megabytes=vehicle.sample_task.size_in_megabytes,
                                  created_at=timestamp, limit_time=vehicle.sample_task.limit_time, deadline_at=timestamp+timedelta(seconds=vehicle.sample_task.limit_time),
                                  instruction_count=vehicle.sample_task.instruction_count,
                                  solving_time=vehicle.sample_task.solving_time)

            obtained_nft = solver_finder.searchForTaskSolverSINR(
                                    map_grid, dummy_task, solver_coll_names)

            if obtained_nft is not None:
                timestamp_nft_dict[timestamp] = obtained_nft
            timestamp = timestamp + timedelta(seconds=dt)
            route_step += 1

        missing_nfts = route_step - len(timestamp_nft_dict)
        rbs = reduce(lambda a,b: a + b.reserved_rbs, timestamp_nft_dict.values())
        dist = self.com.getCuda2dDistance(node1_loc, node2_loc)

        return Metrics(missing_nfts, rbs, distance), Node(node2, route_step)

    def h(self, node: int, destination: int) -> Metrics:
        key = (node,destination)

        if key in self.cache_distance:
            return self.cache_distance[key]

        d = self.com.getCuda2dDistance(
            node_to_loc(self.graph, node),
            node_to_loc(self.graph, destination),
        )
        self.cache_distance[key] = d
        return d


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