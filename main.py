import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import TextBox, Button, Slider
import random
from pathfinding import Pathfinder
import copy
from baruah import build_routing_tables
from table import TKTable
import tkinter as tk

from window import routing_table_widget, create_frame, create_root


def generate_random_graph(node_count, overall_max_time=20, max_t=100):
    G = [
        [None for x in range(node_count)] for y in range(node_count)
    ]
    Gs = []
    edge_count = random.randint(node_count - 1, int((node_count * node_count - 1) / 2)) 
    
    def create_edge(u, v):
        typical_time = random.randint(1, overall_max_time)
        max_time = random.randint(typical_time, overall_max_time)
        G[u][v] = (typical_time, max_time)
        G[v][u] = (typical_time, max_time)

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
    for _ in range(edge_count - node_count):
        index = random.randrange(len(possible_edges))
        edge = possible_edges.pop(index)
        create_edge(*edge)

    Gs.append(G)
    for t in range(max_t):
        G0 = copy.deepcopy(G)
        u = random.randint(0, node_count - 1)
        v = random.randint(0, node_count - 1)
        while not G0[u][v]:
            u = random.randint(0, node_count - 1)
            v = random.randint(0, node_count - 1)
        (expected_delay, max_delay) = G0[u][v]
        G0[u][v] = (random.randint(1, max_delay), max_delay)
        # for u, nodes in enumerate(G):
        #     for v, delays in enumerate(nodes):
        #         if delays:
        #             max_delay = delays[1]
        #             G0[u][v] = (random.randint(1, max_delay), max_delay)
        Gs.append(G0)
    return Gs


def from_adjacency_matrix(matrix):
    G = nx.Graph()
    G.add_nodes_from([0, len(matrix) - 1])
    for u, nodes in enumerate(matrix):
        for v, delays in enumerate(nodes[u:], start=u):
            if delays:
                G.add_edge(u, v, typical_delay=delays[0], max_delay=delays[1])
    return G

root = create_root()
frame = create_frame(root)

graph_frame = create_frame(root)

node_count = 5
time = 0
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)

canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

def plot_graph(G, ax, pos):
    colors = ["b"] * len(G.edges())
    nx.draw_networkx(G, pos, with_labels=True, ax=ax, edge_color=colors)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "typical_delay"), ax=ax, label_pos=0.3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "max_delay"), ax=ax, font_color='red', label_pos=0.7)

def show_tables(tables):
    index = 0
    root = tk.Tk()
    print(len(tables[index]))
    t = TKTable(root, len(tables[index]), 1, tables[index])
    root.mainloop()



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
    # show_tables(baruah_labels)

    # Table = Dict[Node, Set[Tuple[float, Node | None, float]]]
    # we need an array of tuples for each node

    # r0 = routing_table_widget(frame, 0, len(G_for_baruah.keys()) - 1, table[0])    # nx.draw_networkx_labels(G, pos, labels=baruah_labels, ax=ax)
    # r0.grid(column=0, row=0, sticky="nsw", padx=5)

    for node in G_for_baruah.keys():
        r = routing_table_widget(frame, node, len(G_for_baruah.keys()) - 1, table[node])
        r.grid(column=node, row=0, sticky="nsw", padx=5)






graphs = generate_random_graph(node_count)
G = from_adjacency_matrix(graphs[time])
pos = nx.spring_layout(G)
plot_graph(G, ax, pos)
baruah(G, ax, pos)

def refresh(event):
    global time, graphs, graph, ax, pos
    ax.clear()
    graphs = generate_random_graph(node_count)
    G = from_adjacency_matrix(graphs[time])
    pos = nx.spring_layout(G)
    plot_graph(G, ax, pos)
    baruah(G, ax, pos)
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

def update_time(t):
    global time, graphs, graph, ax, pos
    time = t
    if t >= len(graphs):
        return
    ax.clear()
    graph = from_adjacency_matrix(graphs[t])
    plot_graph(graph, ax, pos)
    baruah(graph, ax, pos)
    fig.canvas.draw()


axslider = plt.axes((0.7, 0.05, 0.2, 0.07))
slider = Slider(axslider, "time", 0, 100, valstep=1)
slider.on_changed(update_time)

def onclick(event):
    if 120 < event.y:
        return

def on_press(event):
    global time
    if event.key == "d" and time < 100:
        time += 1
        slider.set_val(time)
        update_time(time)
    elif event.key == "a" and time > 0:
        time -= 1
        slider.set_val(time)
        update_time(time)

fig.canvas.mpl_connect('key_press_event', on_press)
fig.canvas.mpl_connect('button_press_event', onclick)

# plt.show()
root.mainloop()