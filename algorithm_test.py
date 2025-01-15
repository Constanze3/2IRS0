from __future__ import annotations
from algorithm import System
from structures import Node, Graph
from typing import Tuple, List
from copy import deepcopy
from dataclasses import dataclass
from util import draw_graph
from baruah import baruah, relax_original, apply_strict_domination_to_tables, relax_ppd_nce
from math import inf
import random

class TestResult:
    passed: bool
    message_count: int

    def __init__(self: TestResult, passed: bool, message_count: int):
        self.passed = passed
        self.message_count = message_count

def test_algorithm2(graph: Graph, destination: Node, edge: Tuple[Node, Node], new_expected_delay: int) -> TestResult:
    original_graph = deepcopy(graph)

    system = System(graph, destination)
    system.simulate_edge_change(edge, new_expected_delay)
        
    message_count = system.messages_sent 

    actual_tables = system.tables()
    actual_sd_tables = apply_strict_domination_to_tables(actual_tables)

    actual_simple_tables = {}
    for (node, table) in actual_sd_tables.items():
        simple_table = set()
        for entry in table:
            simple_table.add((entry.max_time, entry.parent(), entry.expected_time))
        actual_simple_tables[node] = simple_table

    expected_sd_tables = baruah(system.graph, destination, relax_original)

    expected_simple_tables = {}
    for (node, table) in expected_sd_tables.items():
        simple_table = set()
        for entry in table:
            simple_table.add((entry.max_time, entry.parent(), entry.expected_time))
        expected_simple_tables[node] = simple_table

    if actual_simple_tables != expected_simple_tables:
        print("FAIL")
        print()

        print("actual simple tables")
        print(actual_simple_tables)
        print()

        print("expected simple tables")
        print(expected_simple_tables)
        print()

        print("------------------------")
        print()

        print("actual")
        print(actual_tables)
        print()

        print("actual_sd_tables")
        print(actual_sd_tables)
        print()

        print("expected_sd_tables")
        print(expected_sd_tables)
        print()

        print("graph data")
        print(original_graph.data)
        print()

        print(f"destination: {destination}")
        print(f"edge: {edge}")
        print(f"new expected_delay: {new_expected_delay}")

        print("------------------------")
        print()

        print("graph data")
        print(original_graph.data)
        print()

        print("original graph")
        print(f"{original_graph}")

        print("modified graph")
        print(f"{system.graph}")

        print(f"destination: {destination}")
        print(f"edge: {edge}")
        print(f"new expected_delay: {new_expected_delay}")
        print()

        print("SYSTEM LOGS")
        for log in system.logs:
            print(log)

        print()


        return TestResult(False, message_count)

    return TestResult(True, message_count)



def test_algorithm(graph: Graph, destination: Node, edge: Tuple[Node, Node], new_expected_delay: int) -> bool:
    original_graph = deepcopy(graph)

    system = System(graph, destination)

    system.simulate_edge_change(edge, new_expected_delay)
    actual_tables = system.tables()
    
    system.recalculate_tables()
    expected_tables = system.tables()
    
    print("baruah result")
    print()

    if actual_tables != expected_tables:
        print("FAIL")

        print("graph data")
        print(original_graph.data)
        print()

        print("original graph")
        print(f"{original_graph}")

        print("modified graph")
        print(f"{system.graph}")

        print(f"destination: {destination}")
        print(f"edge: {edge}")
        print(f"new expected_delay: {new_expected_delay}")

        print()

        print("BARUAH on original")
        print(baruah(original_graph, destination, relax_ppd_nce))

        print("BARUAH on modified")
        print(baruah(system.graph, destination, relax_ppd_nce))

        print()

        print("SYSTEM LOGS")

        for log in system.logs:
            print(log)

        for node in actual_tables.keys():
            actual = actual_tables[node]
            expected = expected_tables[node]

            # if actual != expected:
            missing = actual.entries - expected.entries
            should_not_have_been_created = expected.entries - actual.entries

            print()
            if actual != expected:
                print(f"WRONG")
            print(f"TABLE AT NODE {node}")
            print("actual")
            print(actual)
            print("expected")
            print(expected)
            print("only in actual")
            print(missing)
            print("not in actual")
            print(should_not_have_been_created)

        print()
        return False
    return True

def random_weights(max_delay: int) -> Tuple[int, int]:
    typical_delay = random.randint(1, max_delay)
    return (typical_delay, random.randint(typical_delay, max_delay))

@dataclass
class RandomGraphCreateInfo:
    max_delay: int
    min_nodes: int
    max_nodes: int
    min_edges: int
    max_edges: int | None = None

def random_graph(create_info: RandomGraphCreateInfo) -> Graph:
    graph = {}

    num_nodes = random.randint(create_info.min_nodes, create_info.max_nodes)
    nodes = [x for x in range(num_nodes)]
    for node in nodes:
        graph[node] = {}

    max_edges_from_num_nodes = num_nodes * (num_nodes - 1) // 2

    if create_info.max_edges != None:
        max_edges = min(create_info.max_edges, max_edges_from_num_nodes)
    else:
        max_edges = max_edges_from_num_nodes

    min_edges = min(create_info.min_edges, max_edges_from_num_nodes)
    num_edges = random.randint(min_edges, max_edges)

    possible_edges: List[Tuple[Node, Node]] = []
    for u in nodes:
        for v in nodes:
            if u != v:
                possible_edges.append((u, v))

    for _ in range(num_edges):
        edge = random.choice(possible_edges)
        (u, v) = edge

        possible_edges.remove(edge)
        graph[u][v] = random_weights(create_info.max_delay)

    return Graph(graph)


def random_test(
    random_graph_create_info: RandomGraphCreateInfo,
    num_tests: int = 10000000,
):
    passed = 0
    max_e = -inf
    max_x = -inf  # 2V + x

    for test_num in range(1, num_tests + 1):
        print(f"\rAT TEST {test_num} | MAX RELAX ROUNDS V + ({max_x}) | ({max_e}) |", end="")

        graph = random_graph(random_graph_create_info)
        
        l = [edge for edge in list(graph.edges()) if edge.to_node == 0 ]
        if not l:
            continue

        edge_to_change = random.choice(l)
        new_delay = random.randint(0, edge_to_change.worst_case_delay)

        result = test_algorithm2(graph, 0, (edge_to_change.from_node, edge_to_change.to_node), new_delay)

        v = len(graph.nodes())
        e = len(graph.edges())
        x = result.message_count // e  - (v)

        if max_x < x:
            max_e = result.message_count // e
            max_x = x

        if result.passed:
            passed += 1
        else:
            print(f"\nFAILED AT TEST {test_num}\n")

    print(f"{passed} passed out of {num_tests}")

def whatt():
    graph = Graph({0: {}, 1: {2: (57, 97), 3: (6, 13)}, 2: {1: (68, 68), 4: (18, 41)}, 3: {0: (8, 46), 2: (68, 86)}, 4: {3: (88, 97), 2: (8, 14)}})  
    test_algorithm(graph, 0, (1, 3), 9)
    draw_graph(graph)

if __name__ == "__main__":
    random.seed(12)
    random_test(RandomGraphCreateInfo(
        max_delay=100,
        min_nodes=4,
        max_nodes=10,
        min_edges=3,
    ))
