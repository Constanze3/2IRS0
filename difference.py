from baruah import Tables, Entry, Node, baruah
from typing import Mapping, List

class TableDiff:
    def __init__(self, removed: List[Entry], added: List[Entry]) -> None:
       self.removed = removed
       self.added = added
    
    def __len__(self):
        return len(self.removed) + len(self.added)

def difference(old_tables: Tables, new_tables: Tables) -> Mapping[Node, TableDiff]:
    """
    Finds for each table the difference between old and new tables.

    It returns for each table what are entries that were removed and what are entries 
    that were added to the old table to get to the new table.
    """
    assert(len(old_tables) == len(new_tables))

    result = {}
    for node, old_table in old_tables.items():
        new_table = new_tables[node]

        # entries in old table that were removed to get to the new table
        removed = []
        # entries in new table that were an addition to the entries of old table
        added = []

        index_old = 0
        index_new = 0

        while(True):
            if len(old_table) <= index_old and len(new_table) <= index_new:
                # no more entries to consider
                break

            if len(old_table) <= index_old:
                entry_new = new_table[index_new]
                # entry_new only exists in the new table -> it was added
                added.append(entry_new)
                index_new += 1
                continue

            if len(new_table) <= index_new:
                entry_old = old_table[index_old]
                # entry_old only exist in the old table -> it was removed
                removed.append(entry_old)
                index_old += 1
                continue
            
            # at this point: index_old < len(old_table) and index_new < len(new_table) 

            entry_old = old_table[index_old]
            entry_new = new_table[index_new]

            if entry_old == entry_new:
                # entry exists in both tables -> not a change
                index_new += 1
                index_old += 1
                continue

            if entry_old < entry_new:
                # entry_old was "skipped over" in new table, the table is sorted -> the new table doesn't contain it -> it was removed
                removed.append(entry_old)
                index_old += 1
                continue
            
            if entry_new < entry_old:
                # entry_new was "skipped over" in old table, the table is sorted -> the old table doesn't contain it -> it was added
                added.append(entry_new)
                index_new += 1
                continue
        
        result[node] = TableDiff(removed, added)

    return result


if __name__ == "__main__":
    G = {
        1: {2: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 15, 'max_delay': 25}},
        2: {3: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 12, 'max_delay': 15}},
        3: {4: {'typical_delay': 4, 'max_delay': 10}},
        4: {}
    }

    e = (1, 2)
    ew = G[e[0]][e[1]]

    old_tables = baruah(G, 4, True)
    while True:
        ew["typical_delay"] += 1
        
        if ew["max_delay"] <= ew["typical_delay"]:
            break

        new_tables = baruah(G, 4, True)
        diff = difference(old_tables, new_tables)

        # print what changed
        old_weight = ew["typical_delay"] - 1
        new_weight = ew["typical_delay"]
        print(f"ew: {old_weight} -> {new_weight}")

        # print num of differences for each node
        for node in G.keys():
            print(f"{node}: {len(diff[node])}")
        print()

        old_tables = new_tables