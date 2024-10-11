from typing import Any, Mapping, Tuple, List, Dict

Node = Any
Edges = Mapping[Node, Tuple[float, float]]
Graph = Mapping[Node, Edges]

def route(nodes: List, edges: List, end: Node) -> Dict[Node, List]:
    tab = {} 

    for node in nodes:
        tab[node] = []
    tab[end] = [(0, None, 0)]

    def relax(edge):
        global tab
        u, v, c_w, c_t = edge

        if not tab[v]:
           return
       
        d_min = c_w + min(tab[v], key=lambda d_v, p_v, de_v: d_v).value

        for d_v, p_v, de_v in tab[v]:
            d = max(d_min, c_t + d_v)
            de = de_v + c_t

            insert = True
            new_tab = []

            for entry in tab[u]:
                d_u, p_u, de_u = entry
                if not d_u < d and de_u < de:
                    new_tab.append(entry)
                if d_u <= d and de_u < de:
                    insert = False

            if insert:
                new_tab.append((d, v, de))
            
            tab[u] = new_tab
                    
    for node in range(len(nodes) - 1):
        for edge in edges:
            relax(edge)
    
    return tab