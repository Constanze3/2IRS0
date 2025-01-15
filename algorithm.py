from __future__ import annotations
import sys
from baruah import baruah, relax_ppd_nce
from structures import Entry, Node, Edge, Graph, Table, TableDiff
from typing import Dict, List, Tuple
from copy import deepcopy

class Message:
    from_node: Node | None
    to_node: Node
    changes: TableDiff

    def __init__(self: Message, from_node: Node | None, to_node: Node, changes: TableDiff):
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
            
            if original_edge.worst_case_delay != new_edge.worst_case_delay:
                raise ValueError("worst case delay should not change")

            considered_table = deepcopy(self.table)
            considered_table.remove_all_entries_with_n_parents(len(self.system.graph.nodes()) - 1)
            
            old = Table() 
            relax_ppd_nce(original_edge, old, considered_table)

            new = Table()
            relax_ppd_nce(new_edge, new, considered_table)

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

        considered_table = deepcopy(self.table)
        considered_table.remove_all_entries_with_n_parents(len(self.system.graph.nodes()) - 1)

        new_table = deepcopy(self.table)
        message.changes.apply(new_table)

        new_considered_table = deepcopy(new_table)
        new_considered_table.remove_all_entries_with_n_parents(len(self.system.graph.nodes()) - 1)

        for edge in self.incoming_edges:
            old = Table()
            relax_ppd_nce(edge, old, considered_table)

            new = Table()
            relax_ppd_nce(edge, new, new_considered_table)

            changes = TableDiff(old, new)
            self.system.logs.append(f"[ROUTER {self.node}] evaluating changes for edge ({edge})")
            self.system.logs.append(f"[ROUTER {self.node}] old table {self.table} new table {new_table}")
            self.system.logs.append(f"[ROUTER {self.node}] old considered table {considered_table} new considered table {new_considered_table}")
            self.system.logs.append(f"[ROUTER {self.node}] old {old} new {new} changes {changes}")

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
    messages: List[Message]
    processing_messages: bool
    messages_sent: int

    def __init__(self: System, graph: Graph, destination: Node):
        self.graph = graph
        self.destination = destination
        
        self.routers = {}
        for node in graph.nodes():
            incoming_edges = graph.incoming_edges(node)
            self.routers[node] = Router(self, node, incoming_edges)

        self.messages = []
        self.processing_messages = False

        self.logs = []
        self.messages_sent = 0
        
        diff = TableDiff(Table(), Table(set([Entry(0, [], 0)])))
        self.send(Message(None, destination, diff))

    def send(self: System, message: Message):
        self.logs.append(f"[SYSTEM] message from {message.from_node} to {message.to_node} with content {message.changes}")
        self.messages.append(message)

        self.messages_sent += 1

        if not self.processing_messages:
            self.proccess_messages()

    def proccess_messages(self: System):
        self.processing_messages = True
       
        while self.messages:
            message = self.messages.pop(0)
            self.routers[message.to_node].send(message)

        self.processing_messages = False

    def simulate_edge_change(self: System, edge: Tuple[Node, Node], new_expected_delay: int):
        self.messages_sent = 0
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
