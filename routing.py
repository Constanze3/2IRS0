from math import inf, isinf
from heapq import heappush, heappop
from typing import Any, Mapping, Tuple, List

Node = Any
Edges = Mapping[Node, float]
Graph = Mapping[Node, Edges]

def dijkstra(graph: Graph, start: Node) -> Tuple[List, List]:
    node_count = len(graph.keys())

    handled = 0
    deltas = {}
    parents = {}

    heap = []
    heappush(heap, (0, start, None))

    while heap:
        delta, node, parent = heappop(heap) 

        if handled == node_count:
            break

        if node in deltas:
            continue

        deltas[node] = delta
        parents[node] = parent

        handled += 1

        for neighbor, distance in graph[node].items():
            heappush(heap, (delta + distance, neighbor, node))
    
    return (deltas, parents)

class Pathfinder:
    def __init__(self, graph: Graph, start: Node) -> None:
        deltas, parents = dijkstra(graph, start)
        self.deltas = deltas
        self.parents = parents
    
    def find_path(self, goal: Node):
        path = []

        node = goal
        while node is not None:
            path.append(node)
            node = self.parents[node]

        return path[::-1]