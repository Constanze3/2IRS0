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
import signal

import numpy as np

from window import routing_table_widget, create_frame, create_root

MAX_TIME = 10

def generate_random_graph(node_count, overall_max_time=20, max_t=MAX_TIME):
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

def plot_graph(G, ax, pos):
    colors = ["b"] * len(G.edges())
    nx.draw_networkx(G, pos, with_labels=True, ax=ax, edge_color=colors)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "typical_delay"), ax=ax, label_pos=0.3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "max_delay"), ax=ax, font_color='red', label_pos=0.7)

table_root = create_root()
table_frame = None
def baruah(G, ax, pos, destinations=None):
    global table_frame

    if table_frame is not None:
        table_frame.destroy()
    table_frame = create_frame(table_root)
    for widget in table_frame.winfo_children():
        widget.destroy()

    G_for_baruah = {node: {key: (list(value.values())[0], list(value.values())[1]) for key, value in edge.items()} for node, edge in G.adjacency()}
    if destinations is None:
        destinations = G_for_baruah.keys()

    for node in destinations:
        table = build_routing_tables(G_for_baruah, node)

        table_frame.grid_rowconfigure(node, weight=1)
        col = 0
        for node2 in G_for_baruah.keys():
            if node2 == node:
                continue
            r = routing_table_widget(table_frame, node2, node, table[node2])
            r.grid(column=col, row=node, sticky="nsw", padx=5)
            col += 1


def regenerate(event):
    global time, graphs, ax, pos, adj_matrix_frame
    graphs = generate_random_graph(node_count)
    ax.clear()
    G = from_adjacency_matrix(graphs[time])
    pos = nx.spring_layout(G)
    plot_graph(G, ax, pos)
    baruah(G, ax, pos)
    fig.canvas.draw()
    update_adj_matrix()

def refresh(event):
    global graphs, time, adj_matrix, ax, pos
    graphs[time] = adj_matrix.get_values()
    ax.clear()
    G = from_adjacency_matrix(graphs[time])
    plot_graph(G, ax, pos)
    baruah(G, ax, pos)
    fig.canvas.draw()

def submit_nodes(count):
    global node_count
    node_count = int(count)

def update_time(t):
    global time, graphs, graph, ax, pos
    time = t
    if t >= len(graphs):
        return
    ax.clear()
    graph = from_adjacency_matrix(graphs[t])
    plot_graph(graph, ax, pos)
    update_adj_matrix()
    baruah(graph, ax, pos)
    fig.canvas.draw()

def onclick(event):
    if 120 < event.y:
        return

def on_press(event):
    global time
    if event.key == "d" and time < MAX_TIME:
        time += 1
        slider.set_val(time)
        update_time(time)
    elif event.key == "a" and time > 0:
        time -= 1
        slider.set_val(time)
        update_time(time)

def update_adj_matrix():
    global adj_matrix, adj_matrix_frame, graphs, time
    matrix = graphs[time]
    for widget in adj_matrix_frame.winfo_children():
        widget.destroy()

    adj_matrix = TKTable(adj_matrix_frame, len(matrix), len(matrix[0]), matrix)
    adj_matrix_frame.pack()

def save():
    global graphs
    print(graphs)
    a = np.array(graphs, dtype=object)
    np.savetxt("graph.csv", a, delimiter=",")

def load():
    return

if __name__ == "__main__":
    adj_matrix = None
    graph_root = create_root()
    graph_frame = create_frame(graph_root)

    node_count = 5
    time = 0
    fig, ax = plt.subplots()
    # plt.subplots_adjust(bottom=0.2)

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    adj_matrix_frame = create_frame(graph_root)
    adj_matrix_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

    graphs = generate_random_graph(node_count)
    G = from_adjacency_matrix(graphs[time])
    pos = nx.spring_layout(G)
    plot_graph(G, ax, pos)
    baruah(G, ax, pos)

    update_adj_matrix()

    axbutton = plt.axes((0.15, 0.05, 0.1, 0.07))
    button = Button(axbutton, "new")
    button.on_clicked(regenerate)

    axrefresh = plt.axes((0.3, 0.05, 0.1, 0.07))
    refresh_button = Button(axrefresh, "refresh")
    refresh_button.on_clicked(refresh)

    axbox = plt.axes((0.5, 0.05, 0.07, 0.07))
    text_box = TextBox(axbox, "nodes: ", initial=str(node_count))
    text_box.on_submit(submit_nodes)

    axslider = plt.axes((0.7, 0.05, 0.2, 0.07))
    slider = Slider(axslider, "time", 0, MAX_TIME, valstep=1)
    slider.on_changed(update_time)

    closebutton = plt.axes((0.9, 0.05, 0.1, 0.07))
    close_button = Button(closebutton, "close")
    close_button.on_clicked(lambda x: exit())

    fig.canvas.mpl_connect('key_press_event', on_press)
    fig.canvas.mpl_connect('button_press_event', onclick)

    # exit on close graph window
    graph_root.protocol("WM_DELETE_WINDOW", exit)
    # exit on close table window
    table_root.protocol("WM_DELETE_WINDOW", exit)

    # catch sigint
    signal.signal(signal.SIGINT, lambda x, y: exit())
    # sigterm
    signal.signal(signal.SIGTERM, lambda x, y: exit())

    graph_root.mainloop()
    table_root.mainloop()