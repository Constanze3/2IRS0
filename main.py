import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
import random


def plot_graph(node_count, ax):
    edge_count = random.randint(node_count - 1, int((node_count * node_count - 1) / 2)) 
    overall_max_time = 20

    G = nx.Graph()
    G.add_nodes_from([0, node_count - 1])
    edge_labels = {}

    def create_edge(u, v):
        typical_time = random.randint(1, overall_max_time)
        max_time = random.randint(typical_time, overall_max_time)

        G.add_edge(u, v)
        edge_labels[(u, v)] = (typical_time, max_time)

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

    pos = nx.spring_layout(G)
    nx.draw_networkx(G, pos, with_labels=True, ax=ax)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)

node_count = 10

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)

plot_graph(node_count, ax)

def submit_nodes(count):
    global node_count
    node_count = int(count)

axbox = plt.axes([0.5, 0.05, 0.3, 0.07])
text_box = TextBox(axbox, "nodes: ", initial=node_count)
text_box.on_submit(submit_nodes)

def onclick(event):
    if 120 < event.y:
        ax.clear()
        plot_graph(node_count, ax)
        fig.canvas.draw()

fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()