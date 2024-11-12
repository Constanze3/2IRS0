from typing import Dict

from baruah import baruah

# test name, input graph, destination node, output tables
TestCase = (str, Dict, int, Dict)
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
            1: [(25, 4, 15)],
            2: [(15, 4, 12), (20, 3, 8)],
            3: [(10, 4, 4)],
            4: [(0, None, 0)]
        }
    ),
]


def compare_tables(table1, table2):
    for node, entries in table1.items():
        for entry1, entry2 in zip(entries, table2[node]):
            if entry1 != entry2:
                print(entry1, entry2)
                return False
    return True


def run_test(test: TestCase):
    name, graph, destination, expected_table = test
    result = baruah(graph, destination, False)
    return compare_tables(result, expected_table)


def main():
    tests_passed = 0
    for i, test in enumerate(tests):
        result = run_test(test)
        if not result:
            print(f"Test {test[0]} failed.")
        else:
            print(f"Test {test[0]} passed.")
            tests_passed += 1
    if tests_passed == len(tests):
        print("All tests passed.")
    else:
        print(f"FAIL. {tests_passed}/{len(tests)} tests passed.")


if __name__ == '__main__':
    main()
