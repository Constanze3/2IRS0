from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Mapping, Set
from copy import deepcopy

class Table:
    entries: List[Entry]

    def __init__(self, entries=None) -> None:
        self.entries = entries or []

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __str__(self) -> str:
        return str(self.entries)

    def remove_parent(self, parent):
        remove = []
        for entry in self.entries:
            if entry.parent == parent:
                remove.append(entry)
        for entry in remove:
            self.entries.remove(entry)

    def insert(self, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with domination checks.
        """

        if entry.parent is None:
            self.entries.append(entry)
            return

        should_insert = True
        remove = []
        for existing_entry in self.entries:
            if existing_entry.max_time <= entry.max_time and existing_entry.expected_time <= entry.max_time:
                # entry is dominated by an existing entry
                should_insert = False
                break

            elif existing_entry.max_time >= entry.max_time and existing_entry.expected_time >= entry.expected_time:
                # entry dominates existing entry
                remove.append(existing_entry)
        
        for entry_to_remove in remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.append(entry)

    def insert_ppd(self, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with per parent domination checks.
        
        If `entry` is not dominated by any entries that have the same parent it gets inserted and
        all entries that have the same parent and are dominated by `entry` get removed.
        """

        should_insert = True
        remove = []
        for existing_entry in self.entries:
            if existing_entry.parent != None and entry.parent != None and existing_entry.parent != entry.parent:
                # only consider domination if existing entry has the same parent as entry
                continue

            if existing_entry.max_time <= entry.max_time and existing_entry.expected_time <= entry.expected_time:
                # entry is dominated by existing entry
                should_insert = False
                break

            if entry.max_time <= existing_entry.max_time and entry.expected_time <= existing_entry.expected_time:
                # entry dominates existing entry
                remove.append(existing_entry)

        for entry_to_remove in remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.append(entry)

Node = int | str

@dataclass
class Node_obj:
    label: Node
    out_going: Dict[Node_obj, Tuple[int, int]]  # Neighboring nodes with (expected delay, worst-case delay)
    in_going: Dict[Node_obj, Tuple[int, int]]  # Neighboring nodes with (expected delay, worst-case delay)
    routing_table: RoutingTable

    def __init__(self, node_id):
        self.label = node_id
        self.neighbors = {}
        self.out_going = {}
        self.in_going = {}
        self.routing_table = Table()

    def update_in(self, neighbor: Node_obj, delays: Tuple[int, int]) -> None:
        self.in_going[neighbor] = delays

    def update_out(self, neighbor: Node_obj, delays: Tuple[int, int]) -> None:
        self.out_going[neighbor] = delays
    
    def set_table(self, table):
        self.routing_table = table

    def update_tables(self, entries, parent):
        self.routing_table.remove_parent(parent)
        for entry in entries:
            self.routing_table.insert_ppd(entry)

    def relax(self, u):
        tab_u = Table()
        c_t, c_w = self.in_going[u]

        if len(self.routing_table) == 0:
            # the tab[v] is empty there is nothing to update the tab[u] with
            return

        # tab[v], = informs us
        # of a path from v to the destinaton with
        # worst-case delay bound d_v and typical delay de_v
        # the next node along this path is p_v

        # d_min is the smallest worst-case delay bound from u to the destination
        d_min = c_w + min([entry.max_time for entry in self.routing_table])

        for entry in self.routing_table:
            d_v = entry.max_time
            de_v = entry.expected_time
            p_v = entry.parent
            # d is a worst case delay bound
            # it's exact definition is complicated
            d = max(d_min, c_t + d_v)
            de = de_v + c_t

            new_entry = Entry(d, self.label, de)
            tab_u.insert_ppd(new_entry)
        return tab_u

    def clean(self, relaxed_edges, parent):
        new_relaxed = deepcopy(relaxed_edges)
        for neighbor, (expected, worse) in self.in_going.items():
            new_relaxed.append(Edge(neighbor.label, self.label, expected, worse))
        self.update_tables([], parent)
        for neighbor, (expected, worse) in self.in_going.items():
            edge = Edge(neighbor.label, self.label, expected, worse)
            if edge in relaxed_edges:
                continue
            neighbor.clean(new_relaxed, self.label)

    def propogate(self, relaxed_edges, parent, entries):
        new_relaxed = deepcopy(relaxed_edges)
        for neighbor, (expected, worse) in self.in_going.items():
            new_relaxed.append(Edge(neighbor.label, self.label, expected, worse))
        if entries:
            self.update_tables(entries, parent)
        for neighbor, (expected, worse) in self.in_going.items():
            edge = Edge(neighbor.label, self.label, expected, worse)
            if edge in relaxed_edges:
                continue
            new_entries = self.relax(neighbor)
            neighbor.propogate(new_relaxed, self.label, new_entries)

    def __str__(self):
        return f"Node {self.label} with routing table:\n{self.routing_table}"

    def __hash__(self):
        return hash(self.label)

    def __eq__(self, other):
        return isinstance(other, Node) and self.label == other.label

@dataclass
class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worst_case_delay: int

    def get_other_side(self, node):
        return self.to_node if self.from_node == node else self.from_node
    
    # equals
    def __eq__(self, other):
        return self.from_node == other.from_node and self.to_node == other.to_node and self.expected_delay == other.expected_delay and self.worst_case_delay == other.worst_case_delay
    
    def __str__(self):
        return f"Edge {self.from_node} -({self.expected_delay}, {self.worst_case_delay})-> {self.to_node}"
    
    def __hash__(self):
        return hash((self.from_node, self.to_node, self.expected_delay, self.worst_case_delay))


@dataclass
class Entry:
    max_time: int
    parent: Node | None
    expected_time: int

    # equals
    def __eq__(self, other):
        return hash(self) == hash(other) 
    
    # less than
    def __lt__(self, other):
        return hash(self) < hash(other)
    
    # hash
    def __hash__(self):
        return hash((self.parent, self.max_time, self.expected_time))
    
    def __str__(self):
        return f"Entry: {self.max_time} {self.parent} {self.expected_time}"
    
    def __repr__(self):
        return self.__str__()

Tables = Dict[Node, Table]

@dataclass
class Graph:
    data: Dict[Node, Dict[Node, Tuple[int, int]]]
    nodes_obj: Dict[Node, Node_obj]

    def __init__(self: Graph, adjacency_list: Mapping[Node, Mapping[Node, Tuple[int, int]]]) -> None:
        """
        Constructs a new graph.

        Maps a node to a map of neighboring nodes and (expected delay, worst case delay).
        """
        self.data = {}
        self.nodes_obj = {}
        for x in adjacency_list.keys():
            self.nodes_obj[x] = Node_obj(x)

        for (node, v) in adjacency_list.items():
            self.data[node] = {}
            for (other_node, edge_weights) in v.items():
                self.data[node][other_node] = edge_weights
                self.nodes_obj[node].update_out(self.nodes_obj[other_node], edge_weights)
                self.nodes_obj[other_node].update_in(self.nodes_obj[node], edge_weights)

    def init_tables(self, destination):
        tables = original_baruah(self, destination, True)
        for node, table in tables.items():
            self.nodes_obj[node].set_table(table)
        return

    def edge(self, u: Node, v: Node) -> Edge:
        weights = self.data[u][v]
        return Edge(u, v, *weights)

    def modify_edge(self, u, v, data: Tuple[int, int]):
        self.data[u][v] = data
        self.nodes_obj[u].update_out(self.nodes_obj[v], data)
        self.nodes_obj[v].update_in(self.nodes_obj[u], data)

    def nodes(self: Graph) -> List[Node]:
        return list(self.data.keys())
    
    def edges(self: Graph) -> Set[Edge]:
        edges: Set[Edge] = set()

        for (node, neighbors) in self.data.items():
            for (neighbor, weights) in neighbors.items():
                edges.add(Edge(node, neighbor, *weights))

        return edges

    def neighbors(self: Graph, node: Node) -> List[Node]:
        neighbors = []
        for neighbor in self.data[node].keys():
            neighbors.append(neighbor)

        return neighbors
    
    def neighbor_of(self: Graph, node: Node) -> List[Node]:
        neighborof = []
        for (n, edges) in self.data.items():
            if node in edges.keys():
                neighborof.append(n)
        return neighborof
        
    
    def outgoing_edges(self: Graph, node: Node) -> List[Edge]:
        edges = []
        for (node, neighbors) in self.data.items():
            for (neighbor, weights) in neighbors.items():
                edges.append(Edge(node, neighbor, *weights))
        return edges
    
    def incoming_edges(self: Graph, node: Node) -> List[Edge]:
        edges = []
        for (n, neighbors) in self.data.items():
            if node in neighbors.keys():
                edges.append(Edge(n, node, *neighbors[node]))
        return edges
    
    def __str__(self):
        result = ""
        for (node, neighbors) in self.data.items():
            result += f"{node}:\n"
            if len(neighbors) == 0:
                result += "    None\n"
            for (neighbor, weights) in neighbors.items():
                result += f"    -({weights[0]}, {weights[1]})-> {neighbor}\n"

        return result 

def test():
    G = Graph({
        1: {2: (4, 10), 4: (15, 25)},
        2: {3: (4, 10), 4: (12, 15)},
        3: {4: (4, 10)},
        4: {}
    })

    print(G)

@dataclass
class TemporalGraph:
    time_to_graph: List[Graph]

    def __len__(self):
        return len(self.time_to_graph)

    def __init__(self, graphs: List[Graph]):
        self.time_to_graph = graphs

    def at_time(self, t: int) -> Graph:
        return self.time_to_graph[t]
    
    def __str__(self):
        string = ""
        for i, graph in enumerate(self.time_to_graph):
            string += (f"Time {i}: {graph}\n")
        return string

def original_baruah(graph: Graph, destination: str, keep_entries: bool) -> Tables:
    """
    Runs Baruah's routing algorithm.

    'graph' adjacency list of the graph.
    'destination' the destination node.
    'keep_entries' will make sure for the routing tables of each node to keep a routing table entry for each neighboring node.
    """

    # get list of nodes and edges of the graph
    nodes = graph.nodes()
    edges = graph.edges()

    # shuffle(edges)

    # initialization
    tab: Tables = {}
    for node in nodes:
        tab[node] = Table()
    tab[destination] = Table(entries=[Entry(parent=None, max_time=0, expected_time=0)])

    def relax(edge: Edge):
        # u, v are the start and end vertices of the edge
        # c_w is the worst case delay traversing the edge
        # c_t is the estimate of the typical delay when traversing the edge
        u = edge.from_node
        v = edge.to_node
        c_t = edge.expected_delay
        c_w = edge.worst_case_delay

        # this function attempts to use the entries in tab[v] to update tab[u]

        if len(tab[v].entries) == 0:
            # the tab[v] is empty there is nothing to update the tab[u] with
            return

        # tab[v], = informs us
        # of a path from v to the destinaton with
        # worst-case delay bound d_v and typical delay de_v
        # the next node along this path is p_v

        # d_min is the smallest worst-case delay bound from u to the destination
        d_min = c_w + min([entry.max_time for entry in tab[v].entries])

        for entry in tab[v].entries:
            d_v = entry.max_time
            de_v = entry.expected_time
            p_v = entry.parent
            # d is a worst case delay bound
            # it's exact definition is complicated
            d = max(d_min, c_t + d_v)
            de = de_v + c_t
            
            new_entry = Entry(d, v, de)
            if keep_entries:
                tab[u].insert_ppd(new_entry)
            else:
                tab[u].insert(new_entry)

    for i in range(len(nodes)):
        for edge in edges:
            relax(edge)

    # since tables are a set of entries having them as a sorted list is convenient
    for table in tab.values():
        table.entries.sort()

    # assign the tables to the nodes
    # for node in nodes:
    #     node.table = tab[node]

    return tab

def get_single_edge_change(graphs: TemporalGraph, time: int) -> None | Edge:
    if time == 0:
        return None

    old_graph = graphs.at_time(time - 1)
    new_graph = graphs.at_time(time)

    old_edges = old_graph.edges()
    new_edges = new_graph.edges()
    # assuming there is only 1 edge that changes

    for edge in new_edges:
        if edge not in old_edges:
            return edge

    return None

class TableDiff:
    def __init__(self, removed: Set[Entry] | None = None, added: Set[Entry] | None = None) -> None:
        self.removed = removed or set()
        self.added = added or set()
    
    def __len__(self):
        return len(self.removed) + len(self.added)

    def __eq__(self, other):
        return self.removed == other.removed and self.added == other.added
    
    def __str__(self):
        return f"removed: {self.removed}, added: {self.added}"
    
    def __repr__(self):
        return self.__str__()

    def __ior__(self, other):
        return TableDiff(self.removed | other.removed, self.added | other.added)