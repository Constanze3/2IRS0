import networkx as nx
import matplotlib.pyplot as plt
from structures import Graph

def draw_graph(graph: Graph):
    nx_graph = nx.DiGraph()

    for node in graph.nodes():
        nx_graph.add_node(node)

    for edge in graph.edges():
        nx_graph.add_edge(
            edge.from_node,
            edge.to_node,
            expected_delay=edge.expected_delay,
            worst_case_delay=edge.worst_case_delay
        )

    pos = nx.spring_layout(nx_graph)

    colors = ["b"] * len(nx_graph.edges())
    nx.draw_networkx(nx_graph, pos, with_labels=True, edge_color=colors)
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=nx.get_edge_attributes(nx_graph, "expected_delay"), label_pos=0.3)
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=nx.get_edge_attributes(nx_graph, "worst_case_delay"), font_color="red", label_pos=0.4)

    plt.show()
