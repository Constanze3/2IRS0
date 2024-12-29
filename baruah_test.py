from structures import Graph, Edge, Table, Entry, TableDiff
from baruah import baruah, relax_original, relax_ppd_nce
from util import draw_graph

def simple_test():
    print("BARUAH TEST")
    print()

    G = Graph({
        0: {1: (5, 10)},
        1: {2: (5, 10), 3: (5, 10), 4: (5, 10)},
        2: {3: (5, 10)},
        3: {0: (5, 10)},
        4: {1: (5, 10)}
    })

    print("original baruah")
    tables = baruah(G, 3, relax_original)
    for (node, table) in tables.items():
        print(f"{node}: {table}")

    print()

    print("modified baruah")
    tables = baruah(G, 3, relax_ppd_nce)
    for (node, table) in tables.items():
        print(f"{node}: {table}")

    draw_graph(G)

def exploration():
    edge = Edge(2, 1, 3, 3)
    tab1 = Table()
    tab1.insert_ppd(Entry(33, [0], 26))

    tab2 = Table()
    tab2.insert_ppd(Entry(33, [0], 28))
    
    result1 = Table()
    relax_ppd_nce(edge, result1, tab1)

    result2 = Table()
    relax_ppd_nce(edge, result2, tab2)

    diff = TableDiff(result1, result2)

    print(diff)
    print(len(diff))

exploration()