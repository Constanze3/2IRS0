from algorithm import System
from structures import Node, Graph
from typing import Tuple, List
from copy import deepcopy
from dataclasses import dataclass
import random

from baruah import baruah, relax_original, relax_ppd_nce, apply_domination_to_tables

def test_algorithm(graph: Graph, destination: Node, edge: Tuple[Node, Node], new_expected_delay: int) -> bool:
    original_graph = deepcopy(graph)

    system = System(graph, destination)

    system.simulate_edge_change(edge, new_expected_delay)
    actual_tables = system.tables()
    
    system.recalculate_tables()
    expected_tables = system.tables()

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

            if actual != expected:
                missing = actual.entries - expected.entries
                should_not_have_been_created = expected.entries - actual.entries

                print()
                print(f"WRONG TABLE AT NODE {node}")
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

    for test_num in range(1, num_tests + 1):
        print(f"\rAT TEST {test_num}", end="")

        graph = random_graph(random_graph_create_info)
        
        edge_to_change = random.choice(list(graph.edges()))
        new_delay = random.randint(0, edge_to_change.worst_case_delay)

        if test_algorithm(graph, 0, (edge_to_change.from_node, edge_to_change.to_node), new_delay):
            passed += 1
        else:
            print(f"\nFAILED AT TEST {test_num}\n")

    print(f"{passed} passed out of {num_tests}")

def test_against_baruah():
    create_info = RandomGraphCreateInfo(
        max_delay=10,
        min_nodes=50,
        max_nodes=50,
        min_edges=3,
    )
    
    graph = random_graph(create_info)
    system = System(graph, 0)

    edge = random.choice(list(graph.edges()))
    system.simulate_edge_change((edge.from_node, edge.to_node), random.randint(0, edge.worst_case_delay))
    
    baruah_tables = baruah(system.graph, system.destination, relax_original)
    
    algorithm_tables = system.tables()
    dom_algorithm_tables = apply_domination_to_tables(algorithm_tables)
     
    for (node, baruah_table) in baruah_tables.items():
        algorithm_table = dom_algorithm_tables[node] 
            
        baruah_set = set([(entry.max_time, entry.expected_time) for entry in baruah_table])
        algorithm_set = set([(entry.max_time, entry.expected_time) for entry in algorithm_table])

        if baruah_set != algorithm_set:
            print("OH NO")
            print()
            print(baruah_set)
            print()
            print(algorithm_set)
            print()
            print(algorithm_tables[node])

if __name__ == "__main__":
    random_test(RandomGraphCreateInfo(
        max_delay=100,
        min_nodes=4,
        max_nodes=6,
        min_edges=3,
    ))
