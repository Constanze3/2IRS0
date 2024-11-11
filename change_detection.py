import baruah as bh
import networkx as nx

def detect_changes(old_tables: bh.Tables, new_tables: bh.Tables):
    assert(len(old_tables) == len(new_tables))

    num_of_changes = 0 

    for node, old_table_set in old_tables.items():
        new_table_set = new_tables[node]

        diff = old_table_set.difference(new_table_set)

        if 0 < len(diff): 
            print(f"diff for {node}")
            print(list(old_table_set.difference(new_table_set)))
        
        num_of_changes += len(diff)

    return num_of_changes

if __name__ == "__main__":
    G = {}
    G[1] = {2: (4, 10), 4: (15, 25)}
    G[2] = {1: (4, 10), 3: (4, 10), 4: (12, 15)}
    G[3] = {2: (4, 10), 4: (3, 10)}
    G[4] = {1: (15, 25), 2: (12, 15), 3: (4, 10)}

    e = (1, 2)
    ew = G[e[0]][e[1]] # weigths of edge e
    
    e2 = (1, 4)
    e2w = G[e2[0]][e2[1]]

    while ew[0] < ew[1]:
        num_of_changes = 0

        for node in G.keys():
            old_tables = bh.build_routing_tables(G, node)
        
            # increment edge typical time
            G[e[0]][e[1]] = (ew[0] + 1, ew[1])
            G[e[1]][e[0]] = (ew[0] + 1, ew[1])

            G[e2[0]][e2[1]] = (e2w[0] + 1, e2w[1])
            G[e2[1]][e2[0]] = (e2w[0] + 1, e2w[1])

            new_tables = bh.build_routing_tables(G, node)
            num_of_changes += detect_changes(old_tables, new_tables)

             # decrement edge maximum time
            G[e[0]][e[1]] = (ew[0] - 1, ew[1])
            G[e[1]][e[0]] = (ew[0] - 1, ew[1])

            G[e2[0]][e2[1]] = (e2w[0] - 1, e2w[1])
            G[e2[1]][e2[0]] = (e2w[0] - 1, e2w[1])

        # print number of changes of the increase
        print(f"{e} : {ew[0]} -> {ew[0] + 1} = {num_of_changes}")

        ew = (ew[0] + 1, ew[1])
        G[e[0]][e[1]] = (ew[0], ew[1])

        e2w = (e2w[0] + 1, e2w[1])
        G[e2[0]][e2[1]] = (e2w[0], ew[1])