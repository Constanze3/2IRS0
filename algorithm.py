from __future__ import annotations
from baruah import baruah, relax_ppd_nce
from structures import Node, Edge, Graph, Table, TableDiff
from typing import Dict, List, Tuple
from copy import deepcopy

class Message:
    from_node: Node
    to_node: Node
    changes: TableDiff

    def __init__(self: Message, from_node: Node, to_node: Node, changes: TableDiff):
        self.from_node = from_node
        self.to_node = to_node
        self.changes = changes

class Router:
    system: System
    node: Node
    incoming_edges: List[Edge]
    table: Table

    def __init__(self: Router, system: System, node: Node, incoming_edges: List[Edge]):
        self.system = system
        self.node = node
        self.incoming_edges = incoming_edges
        self.table = Table()

    # def calculate_tables(self: Router):
    #     """
    #     Calculate routing tables towards `self.system.destination`.
    #     This is run at the start when every router has a consistent view of the graph.
    #     """
    #     self.table = baruah(self.system.graph, self.system.destination, relax_ppd_nce)[self.node]

    def update_incoming_edges(self: Router, new_incoming_edges: List[Edge]):
        """
        This method simulates the router detecting the change of edge expected time. 
        """
        to_send: List[Message] = []

        if len(new_incoming_edges) != len(self.incoming_edges):
            raise ValueError("`new_incoming_edges` should have the same length as `self.incoming_edges`")

        for new_edge in new_incoming_edges:
            original_edge = None
            for edge in self.incoming_edges:
                if edge.from_node == new_edge.from_node and edge.to_node == new_edge.to_node:
                    original_edge = edge
            
            if original_edge == None:
                raise ValueError("there should be no completely new edges")
            
            # if original_edge.worst_case_delay != new_edge.worst_case_delay:
            #     raise ValueError("worst case delay should not change")
            
            old = Table() 
            relax_ppd_nce(original_edge, old, self.table)

            new = Table()
            relax_ppd_nce(new_edge, new, self.table)

            changes = TableDiff(old, new)
            
            if 0 < len(changes):
                to_send.append(Message(self.node, new_edge.from_node, changes))

        self.incoming_edges = new_incoming_edges
        
        for message in to_send:
            self.system.send(message)

    def send(self: Router, message: Message):
        """
        This method simulates the router receiving a message about changes. 
        """
        to_send = []

        new_table = deepcopy(self.table)
        message.changes.apply(new_table)

        for edge in self.incoming_edges:
            old = Table()
            relax_ppd_nce(edge, old, self.table)

            new = Table()
            relax_ppd_nce(edge, new, new_table)

            changes = TableDiff(old, new)
            self.system.logs.append(f"[ROUTER {self.node}] evaluating changes for edge ({edge.from_node}, {edge.to_node})")
            self.system.logs.append(f"[ROUTER {self.node}] old table {self.table} new table {new_table} old {old} new {new} changes {changes}")
            
            if 0 < len(changes):
                to_send.append(Message(self.node, edge.from_node, changes))
        
        self.table = new_table

        for message in to_send:
            self.system.send(message)

class System:
    graph: Graph
    destination: Node
    routers: Dict[Node, Router]
    logs: List[str]

    def __init__(self: System, graph: Graph, destination: Node):
        self.graph = graph
        self.destination = destination

        self.routers = {}
        for node in graph.nodes():
            incoming_edges = graph.incoming_edges(node)
            self.routers[node] = Router(self, node, incoming_edges)
        
        self.recalculate_tables()
        
        self.logs = []

    def send(self: System, message: Message):
        self.logs.append(f"[SYSTEM] message from {message.from_node} to {message.to_node} with content {message.changes}")
        self.routers[message.to_node].send(message)

    def simulate_edge_change(self: System, edge: Tuple[Node, Node], new_expected_delay: int):
        (u, v) = edge
        self.graph.modify_edge_weights(u, v, new_expected_delay=new_expected_delay)
        self.routers[v].update_incoming_edges(self.graph.incoming_edges(v))

    def recalculate_tables(self):
        """
        Simulates the case when the graph view is distributed to every router in the network
        and routing tables are recalculated based on the uniform graph view. 
        """

        tables = baruah(self.graph, self.destination, relax_ppd_nce)
        for (node, table) in tables.items():
            self.routers[node].table = table

    def tables(self) -> Dict[Node, Table]:
        result = {}
        for (node, router) in self.routers.items():
            result[node] = deepcopy(router.table)

        return result
