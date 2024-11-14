import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import TextBox, Button, Slider
import tkinter as tk
import random
import json
import copy
import signal

from baruah import baruah
from table import TKTable
from window import routing_table_widget, create_frame, create_root
from difference import difference

MAX_TIME = 10
node_count = 5
time = 0
graphs = []
closed_windows = 0
pos = None
table_root: tk.Tk | None = None
table_frame: tk.Frame | None = None
adj_matrix = None
adj_matrix_frame = None
graph_root: tk.Tk | None = None
graph_frame: tk.Frame | None = None
fig, ax = None, None
slider = None

def generate_random_graph(node_count, overall_max_time=20, max_t=MAX_TIME):
    """Generates an adjacency matrix for a random connected graph."""
    G = [[None for _ in range(node_count)] for _ in range(node_count)]
    Gs = []
    edge_count = random.randint(node_count - 1, (node_count * node_count - 1) // 2)

    def create_edge(u, v):
        typical_time = random.randint(1, overall_max_time)
        max_time = random.randint(typical_time, overall_max_time)
        G[u][v] = (typical_time, max_time)
        G[v][u] = (typical_time, max_time)

    # Ensure graph connectivity
    path = list(range(node_count))
    random.shuffle(path)
    for u, v in zip(path, path[1:]):
        create_edge(u, v)

    for _ in range(edge_count - node_count):
        u, v = random.sample(range(node_count), 2)
        if not G[u][v]:
            create_edge(u, v)

    Gs.append(G)
    for _ in range(max_t):
        G_temp = copy.deepcopy(G)
        u, v = random.choice([(u, v) for u in range(node_count) for v in range(node_count) if G_temp[u][v]])
        G_temp[u][v] = (random.randint(1, G_temp[u][v][1]), G_temp[u][v][1])
        Gs.append(G_temp)

    return Gs

def from_adjacency_matrix(matrix):
    """Converts an adjacency matrix to a NetworkX graph."""
    G = nx.Graph()
    G.add_nodes_from(range(len(matrix)))
    for u, row in enumerate(matrix):
        for v, delays in enumerate(row):
            if delays:
                G.add_edge(u, v, typical_delay=delays[0], max_delay=delays[1])
    return G

def plot_graph(G, ax, pos):
    """Plots a graph with NetworkX."""
    colors = ["b"] * len(G.edges())
    nx.draw_networkx(G, pos, with_labels=True, ax=ax, edge_color=colors)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "typical_delay"), ax=ax, label_pos=0.3)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "max_delay"), ax=ax, font_color='red', label_pos=0.7)

old_tables = None
def show_baruah_table(G, pos):
    """Displays Baruah routing tables for the graph."""
    global table_frame, old_tables
    if table_frame:
        table_frame.destroy()
    table_frame = create_frame(table_root)

    G_for_baruah = {node: {key: (list(value.values())[0], list(value.values())[1]) for key, value in edge.items()} for node, edge in G.adjacency()}
    # destinations = sorted(G_for_baruah.keys())
    destinations = [len(G_for_baruah) - 1]


    adj_list = adj_matrix_to_adj_list(graphs[time])

    for node in destinations:
        # table = build_routing_tables(G_for_baruah, node)
        # table = build_routing_tables(adj_list, node)

        table = baruah(adj_list, node, False)
        if not old_tables:
            old_tables = table
        else:
            diff = difference(old_tables, table)
            for n, d in diff.items():
                if not d.added and not d.removed:
                    continue
                print(f"Node {n}:")
                print(f"Added: {d.added}")
                print(f"Removed: {d.removed}")
                print()
            print("--------------------------------------------")
            old_tables = table


        table_frame.grid_rowconfigure(node, weight=1)
        for col, node2 in enumerate(sorted(G_for_baruah.keys())):
            widget = routing_table_widget(table_frame, node2, node, table[node2])
            widget.grid(column=col, row=node, sticky="nsw", padx=5)

def update_adj_matrix():
    """Updates the adjacency matrix display."""
    global adj_matrix
    matrix = graphs[time]
    for widget in adj_matrix_frame.winfo_children():
        widget.destroy()
    adj_matrix = TKTable(adj_matrix_frame, len(matrix), len(matrix[0]), matrix)
    adj_matrix_frame.pack()

def adj_matrix_to_adj_list(matrix):
    """Converts an adjacency matrix to an adjacency list."""
    adj_list = {}
    for u, row in enumerate(matrix):
        adj_list[u] = {}
        for v, delays in enumerate(row):
            if delays:
                adj_list[u][v] = {"typical_delay": delays[0], "max_delay": delays[1]}
    return adj_list

def regenerate_graph(event=None):
    """Regenerates a new random graph and updates the plot."""
    global graphs, pos
    graphs = generate_random_graph(node_count)
    update_graph_display()

def refresh_graph(event=None):
    """Refreshes the graph with current adjacency matrix values."""
    global graphs
    graphs[time] = adj_matrix.get_values()
    update_graph_display()

def update_time(t):
    """Updates the displayed graph for a new time."""
    global time
    time = int(t)
    update_graph_display()

def submit_node_count(count):
    """Submits the node count and regenerates the graph."""
    global node_count
    node_count = int(count)
    regenerate_graph()

def update_graph_display():
    """Clears and redraws the graph based on the current state."""
    global pos
    ax.clear()
    G = from_adjacency_matrix(graphs[time])
    pos = nx.spring_layout(G)
    plot_graph(G, ax, pos)
    show_baruah_table(G, pos)
    fig.canvas.draw()
    update_adj_matrix()

def save_graph():
    """Saves the current graph to a JSON file."""
    with open("graph.json", "w") as f:
        json.dump(graphs, f)

def load_graph():
    """Loads a graph from a JSON file."""
    global graphs, pos
    with open("graph.json", "r") as f:
        graphs = json.load(f)
    pos = nx.spring_layout(from_adjacency_matrix(graphs[0]))
    update_time(0)

def on_close(root):
    """Closes the Tkinter application safely."""
    global closed_windows
    closed_windows += 1
    if closed_windows == 2:
        exit()
    else:
        root.destroy()

def initialize_gui():
    """Sets up the GUI components and starts the main loop."""
    global graph_root, table_root, graph_frame, adj_matrix_frame, fig, ax, slider

    # Initialize Tkinter roots
    graph_root = create_root()
    table_root = create_root()

    # Setup frames
    graph_frame = create_frame(graph_root)
    graph_frame.pack()
    adj_matrix_frame = create_frame(graph_root)
    adj_matrix_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

    # Matplotlib figure setup
    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Menu setup
    menubar = tk.Menu(graph_root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Save", command=save_graph)
    filemenu.add_command(label="Load", command=load_graph)
    menubar.add_cascade(label="File", menu=filemenu)
    graph_root.config(menu=menubar)

    # Matplotlib control buttons
    button_new = Button(plt.axes((0.15, 0.05, 0.1, 0.07)), "new")
    button_new.on_clicked(regenerate_graph)

    button_refresh = Button(plt.axes((0.3, 0.05, 0.1, 0.07)), "refresh")
    button_refresh.on_clicked(refresh_graph)

    text_box = TextBox(plt.axes((0.5, 0.05, 0.07, 0.07)), "nodes:", initial=str(node_count))
    text_box.on_submit(submit_node_count)

    slider = Slider(plt.axes((0.7, 0.05, 0.2, 0.07)), "time", 0, MAX_TIME, valinit=0, valstep=1)
    slider.on_changed(update_time)

    close_button = Button(plt.axes((0.9, 0.05, 0.1, 0.07)), "close")
    close_button.on_clicked(lambda _: exit())

    fig.canvas.mpl_connect('key_press_event', lambda event: update_time(time + (1 if event.key == "d" else -1) if event.key in ("d", "a") else time))
    fig.canvas.mpl_connect('button_press_event', lambda event: None if event.y > 120 else None)

    # Window close protocols
    graph_root.protocol("WM_DELETE_WINDOW", lambda: on_close(graph_root))
    table_root.protocol("WM_DELETE_WINDOW", lambda: on_close(table_root))

    # Signal handling
    signal.signal(signal.SIGINT, lambda x, y: exit())
    signal.signal(signal.SIGTERM, lambda x, y: exit())

    # Generate initial graph and start main loop
    regenerate_graph()
    graph_root.mainloop()
    table_root.mainloop()

# Run the application
if __name__ == "__main__":
    initialize_gui()
