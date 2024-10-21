import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button, Slider
import random
from pathfinding import Pathfinder

from baruah import build_routing_tables

def generate_random_graph(node_count, overall_max_time=20):
    edge_count = random.randint(node_count - 1, int((node_count * node_count - 1) / 2)) 

    G = nx.Graph()
    G.add_nodes_from([0, node_count - 1])

    def create_edge(u, v):
        typical_time = random.randint(1, overall_max_time)
        max_time = random.randint(typical_time, overall_max_time)

        G.add_edge(u, v, typical_delay=typical_time, max_delay=max_time)

    possible_edges = [(i, j) for i in range(node_count) for j in range(node_count) if i != j]

    # add a path involving all nodes to the graph to make sure it is connected
    path = list(range(0, node_count))
    random.shuffle(path)
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        create_edge(u, v)
        possible_edges.remove((u, v))

    # create the remaining edges randomly
    for _ in range(edge_count - G.number_of_edges()):
        index = random.randrange(len(possible_edges))
        edge = possible_edges.pop(index)
        create_edge(*edge)
    return G

test_graph = [
    [None, (6, 10), None, None, (30, 50)],
    [(6, 10), None, (2, 5), (16, 20), (20, 30)],
    [None, (2, 5), None, (18, 19), (15, 20)],
    [None, (16, 20), (18, 19), None, (12, 15)],
    [(30, 50), (20, 30), (15, 20), (12, 15)]
]

def from_adjacency_matrix(matrix):
    G = nx.Graph()
    G.add_nodes_from([0, len(matrix) - 1])
    for u, nodes in enumerate(matrix):
        for v, delays in enumerate(nodes[u:], start=u):
            if delays:
                print((u, v))
                G.add_edge(u, v, typical_delay=delays[0], max_delay=delays[1])
    return G


def plot_graph(G, ax, pos):
    colors = ["b"] * len(G.edges())
    nx.draw_networkx(G, pos, with_labels=True, ax=ax, edge_color=colors)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "typical_delay"), ax=ax, label_pos=0.3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "max_delay"), ax=ax, font_color='red', label_pos=0.7)

def baruah(G, ax, pos):
    G_for_baruah = {node: {key: (list(value.values())[0], list(value.values())[1]) for key, value in edge.items()} for node, edge in G.adjacency()}
    table = build_routing_tables(G_for_baruah, len(G_for_baruah.keys()) - 1)

    def format_node(node_tuples):
        result = ""
        for node_tuple in node_tuples:
            result += f"{node_tuple}\n"
        result += "\n"
        return result
    baruah_labels = {node: format_node(table[node]) for node in table}
    nx.draw_networkx_labels(G, pos, labels=baruah_labels, ax=ax)

if __name__ == "__main__":
    node_count = 5
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    # graph = generate_random_graph(node_count)
    graph = from_adjacency_matrix(test_graph)
    pos = nx.spring_layout(graph)
    plot_graph(graph, ax, pos)
    baruah(graph, ax, pos)

    def refresh(event):
        ax.clear()
        graph = generate_random_graph(node_count)
        pos = nx.spring_layout(graph)
        plot_graph(graph, ax, pos)
        baruah(graph, ax, pos)
        fig.canvas.draw()


    axbutton = plt.axes((0.2, 0.05, 0.1, 0.07))
    button = Button(axbutton, "new")
    button.on_clicked(refresh)

    def submit_nodes(count):
        global node_count
        node_count = int(count)

    axbox = plt.axes((0.45, 0.05, 0.07, 0.07))
    text_box = TextBox(axbox, "nodes: ", initial=str(node_count))
    text_box.on_submit(submit_nodes)


    axslider = plt.axes((0.7, 0.05, 0.2, 0.07))
    slider = Slider(axslider, "time", 0, 100, 0, valstep=1)

    def onclick(event):
        if 120 < event.y:
            return

    fig.canvas.mpl_connect('button_press_event', onclick)

    plt.show()

