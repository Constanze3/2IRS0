from algorithm import System
from structures import Node, Graph
from typing import Tuple
from copy import deepcopy
import random

from baruah import baruah, relax_ppd_nce

def test_algorithm(graph: Graph, destination: Node, edge: Tuple[Node, Node], new_expected_delay: int):
    original_graph = deepcopy(graph)

    system = System(graph, destination)

    system.simulate_edge_change(edge, new_expected_delay)
    actual_tables = system.tables()
    
    system.recalculate_tables()
    expected_tables = system.tables()

    if actual_tables != expected_tables:
        print("FAIL")

        print("graph data")
        print(graph.data)
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
        return 0
    return 1

def random_weights(max_delay: int) -> Tuple[int, int]:
    typical_delay = random.randint(1, max_delay)
    return (typical_delay, random.randint(typical_delay, max_delay))

def random_test(
        num_tests: int = 100000, 
        min_nodes: int = 3, 
        max_nodes: int = 5, 
        min_edges: int = 1, 
        max_edges: int | None = None, 
        max_delay=20,
):
    passes = 0

    for i in range(1, num_tests + 1):
        if i % 1000 == 0:
            print(f"AT TEST {i}")
            print()

        graph = {}

        num_nodes = random.randint(min_nodes, max_nodes)
        nodes = [x for x in range(num_nodes)]

        for node in nodes:
            graph[node] = {}

        max_edges_from_num_nodes = num_nodes * (num_nodes - 1) // 2  
        if max_edges != None:
            max_edges = min(max_edges, max_edges_from_num_nodes)
        else:
            max_edges = max_edges_from_num_nodes

        min_edges = min(min_edges, max_edges_from_num_nodes)

        possible_edges = []
        for u in nodes:
            for v in nodes:
                if u != v:
                    possible_edges.append((u, v))

        num_edges = random.randint(min_edges, max_edges_from_num_nodes)

        for i in range(num_edges):
            edge = random.choice(possible_edges)
            (u, v) = edge

            possible_edges.remove(edge)
            graph[u][v] = random_weights(max_delay)

        graph = Graph(graph)

        edge_to_change = random.choice(list(graph.edges()))
        new_delay = random.randint(0, edge_to_change.worst_case_delay)

        biggest_node = num_nodes - 1

        passes += test_algorithm(graph, biggest_node, (edge_to_change.from_node, edge_to_change.to_node), new_delay)
    
    print(f"{passes} passed out of {num_tests}")

if __name__ == "__main__":
    random.seed(0)
    random_test()
