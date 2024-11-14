from typing import Tuple
from baruah import baruah, Tables, Graph, Node

# test name, input graph, destination node, output tables, keep entries
TestCase = Tuple[str, Graph, Node, Tables, bool]

tests = [
    # Original Paper Example
    (
        "Example from Original Sanjoy Baruah Paper",
        {
            1: {2: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 15, 'max_delay': 25}},
            2: {3: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 12, 'max_delay': 15}},
            3: {4: {'typical_delay': 4, 'max_delay': 10}},
            4: {}
        },
        4,
        {
            1: [(25, 2, 12)],
            2: [(15, 4, 12), (20, 3, 8)],
            3: [(10, 4, 4)],
            4: [(0, None, 0)]
        },
        False,
    ),
    (
        "Con Worked Out Example 1 With KeepEntries",
        {
            1: {2: {'typical_delay': 5, 'max_delay': 7}, 4: {'typical_delay': 12, 'max_delay': 18}},
            2: {4: {'typical_delay': 8, 'max_delay': 9}, 3: {'typical_delay': 3, 'max_delay': 7}},
            3: {4: {'typical_delay': 4, 'max_delay': 5}},
            4: {},
        },
        4,
        {
            1: [(16, 2, 13), (17, 2, 12), (18, 4, 12)],
            2: [(12, 3, 7), (9, 4, 8)],
            3: [(5, 4, 4)],
            4: [(0, None, 0)],
        },
        True,
    ),
]


def compare_tables(tables1: Tables, tables2: Tables):
    for node, entries in tables1.items():
        if entries != tables2[node]:
            return False
    return True


def run_test(test: TestCase):
    name, graph, destination, expected_tables, keep_entries = test

    for table in expected_tables.values():
        table.sort()

    result = baruah(graph, destination, keep_entries)

    print(name)
    print("Result:   " + str(result))
    print("Expected: " + str(expected_tables))

    return compare_tables(result, expected_tables)


def main():
    tests_passed = 0

    for test in tests:
        result = run_test(test)

        if not result:
            print(f"Test {test[0]} failed.")
        else:
            print(f"Test {test[0]} passed.")
            tests_passed += 1

        print()

    if tests_passed == len(tests):
        print("All tests passed.")
    else:
        print(f"FAIL. {tests_passed}/{len(tests)} tests passed.")


if __name__ == '__main__':
    main()
