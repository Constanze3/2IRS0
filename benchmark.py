from copy import deepcopy
import math
from multiprocessing import Manager, Pool, cpu_count, Process
from algorithm import System
from structures import Node, Graph, Edge
from typing import Callable, Tuple, List
from dataclasses import dataclass
from algorithm_test import test_algorithm
import random
import timeit
import time
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict
import sqlite3


def random_weights(max_delay: int) -> Tuple[int, int]:
    typical_delay = random.randint(1, max_delay)
    return (typical_delay, random.randint(typical_delay, max_delay))


@dataclass
class RandomGraphCreateInfo:
    max_delay: int
    min_nodes: int
    max_nodes: int
    min_edges: int
    max_edges: int | None = None


@dataclass
class RandomBenchmarkCreateInfo:
    graph_create_info: RandomGraphCreateInfo
    num_runs: int
    verify_against_baruah: bool = False


@dataclass
class BenchmarkResult:
    algo_time: float
    baruah_time: float
    messages_sent: int


def random_graph(create_info: RandomGraphCreateInfo) -> Graph:
    graph = {}

    num_nodes = random.randint(create_info.min_nodes, create_info.max_nodes)
    nodes = [x for x in range(num_nodes)]
    for node in nodes:
        graph[node] = {}

    max_edges_from_num_nodes = num_nodes * (num_nodes - 1) // 2

    if create_info.max_edges != None:
        max_edges = min(create_info.max_edges, max_edges_from_num_nodes)
    else:
        max_edges = max_edges_from_num_nodes

    min_edges = min(create_info.min_edges, max_edges_from_num_nodes)
    num_edges = random.randint(min_edges, max_edges)

    possible_edges: List[Tuple[Node, Node]] = []
    for u in nodes:
        for v in nodes:
            if u != v:
                possible_edges.append((u, v))

    for _ in range(num_edges):
        edge = random.choice(possible_edges)
        (u, v) = edge

        possible_edges.remove(edge)
        graph[u][v] = random_weights(create_info.max_delay)

    return Graph(graph)


def random_benchmark(
    create_info: RandomBenchmarkCreateInfo,
):

    # Prepare a list of tasks (args) to process in parallel
    tasks = []
    for i in range(create_info.num_runs):
        tasks.append((i, create_info.graph_create_info))

    res = parallel_benchmark(run_single_benchmark_task, tasks, benchmark_args=BenchmarkArgs(run_baruah=True))

    algo_times = [r[0] for r in res]
    baruah_times = [r[1] for r in res]
    print()
    std = np.std(algo_times) / 1e6
    mean = np.mean(algo_times) / 1e6
    print(f"mean: {mean} ms")
    print(f"std: {std} ms")
    print(f"baruah mean: {np.mean(baruah_times) / 1e6} ms")
    print(f"baruah std: {np.std(baruah_times) / 1e6} ms")

    plt.hist(algo_times)
    plt.show()


@dataclass
class BenchmarkArgs:
    run_baruah: bool


def run_single_benchmark_task(tasks, args: BenchmarkArgs = BenchmarkArgs(False)):
    """
    Each worker calls this function with a tuple of arguments.
    Returns (algo_time, baruah_time).
    """
    num_nodes, create_info = tasks

    # Create the random graph for this run
    graph = random_graph(create_info)

    # Pick a random edge and compute new delay
    edge_to_change = random.choice(list(graph.edges()))
    new_delay = random.randint(0, edge_to_change.worst_case_delay)

    # Initialize the system and run the single benchmark
    system = System(graph, 0)
    # algo_time, baruah_time = single_benchmark(system, edge_to_change, new_delay)
    algo_time = (
        timeit.timeit(
            lambda: system.simulate_edge_change((edge_to_change.from_node, edge_to_change.to_node), new_delay),
            timer=time.perf_counter_ns,
            number=1,
        )
        / 10e6
    )
    messages_sent = system.messages_sent
    if not args.run_baruah:
        return BenchmarkResult(algo_time, 0, messages_sent)
    baruah_time = timeit.timeit(lambda: system.recalculate_tables(), timer=time.perf_counter_ns, number=1) / 10e6

    return BenchmarkResult(algo_time, baruah_time, messages_sent)


def increasing_graph_size_benchmark(initial_graph_info, num_runs):
    # Prepare a list of tasks (args) to process in parallel
    tasks = []
    for num_nodes in range(initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1):
        create_info = RandomGraphCreateInfo(
            max_delay=initial_graph_info.max_delay,
            min_nodes=num_nodes,
            max_nodes=num_nodes,
            min_edges=initial_graph_info.min_edges,
        )
        # Repeat (num_nodes, create_info) for 'num_runs' times
        tasks.extend([(num_nodes, create_info) for _ in range(num_runs)])

    # Turn interactive mode on
    fig, ax = plt.subplots()

    (algo_line,) = ax.plot([], [], "o", label="Algorithm")
    (baruah_line,) = ax.plot([], [], "o", label="Baruah")
    (messages_line,) = ax.plot([], [], "o", label="Messages")

    ax.legend()
    ax.set_autoscaley_on(True)

    # ax.set_xlabel("Number of nodes")
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Average Time (ms)")
    ax.set_xscale("linear")

    def cb(results):
        node_range = range(initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1)
        # dict mapping each size to a list of results
        size_to_results: Dict[int, List[BenchmarkResult]] = {}

        i = 0
        for j, result in enumerate(results):
            size: int = initial_graph_info.min_nodes + i
            if size not in size_to_results:
                size_to_results[size] = []
            size_to_results[size].append(result)
            if j % num_runs == num_runs - 1:
                i += 1

        x = []
        for i in node_range:
            x.extend([i] * num_runs)

        algo_line.set_xdata(x)

        y = []
        for size in size_to_results:
            y.extend([(None if size_to_results[size][i] is None else size_to_results[size][i].algo_time) for i in range(num_runs)])
        algo_line.set_ydata(y)

        baruah_line.set_xdata(x)

        y = []
        for size in size_to_results:
            y.extend([(None if size_to_results[size][i] is None else size_to_results[size][i].baruah_time) for i in range(num_runs)])
        baruah_line.set_ydata(y)

        messages_line.set_xdata(x)
        y = []
        for size in size_to_results:
            y.extend([(None if size_to_results[size][i] is None else size_to_results[size][i].messages_sent) for i in range(num_runs)])
        messages_line.set_ydata(y)

        ax.relim()
        ax.autoscale_view()

        # Redraw
        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.show(block=False)  # Show the figure in non-blocking mode

    res = parallel_benchmark(run_single_benchmark_task, tasks, BenchmarkArgs(run_baruah=True), callback=cb)

    # Now gather the final results (in the correct order)
    algo_times = [r[0] for r in res]
    baruah_times = [r[1] for r in res]

    input("Press Enter to close the plot...")


def graph_size_vs_messages_benchmark(initial_graph_info, num_runs):
    # Prepare a list of tasks (args) to process in parallel
    tasks = []
    for num_nodes in range(initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1):
        create_info = RandomGraphCreateInfo(
            max_delay=initial_graph_info.max_delay,
            min_nodes=num_nodes,
            max_nodes=num_nodes,
            min_edges=initial_graph_info.min_edges,
        )
        # Repeat (num_nodes, create_info) for 'num_runs' times
        tasks.extend([(num_nodes, create_info) for _ in range(num_runs)])

    # Turn interactive mode on
    fig, ax = plt.subplots()
    (messages_line,) = ax.plot([], [], "o", label="Messages")

    ax.legend()
    ax.set_autoscaley_on(True)

    # ax.set_xlabel("Number of nodes")
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Total messages sent")
    ax.set_xscale("linear")

    def cb(results):
        node_range = range(initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1)
        # dict mapping each size to a list of results
        size_to_results: Dict[int, List[BenchmarkResult]] = {}

        i = 0
        for j, result in enumerate(results):
            size: int = initial_graph_info.min_nodes + i
            if size not in size_to_results:
                size_to_results[size] = []
            size_to_results[size].append(result)
            if j % num_runs == num_runs - 1:
                i += 1

        x = []
        for i in node_range:
            x.extend([i] * num_runs)

        messages_line.set_xdata(x)
        y = []
        for size in size_to_results:
            y.extend([(None if size_to_results[size][i] is None else size_to_results[size][i].messages_sent) for i in range(num_runs)])
        messages_line.set_ydata(y)

        ax.relim()
        ax.autoscale_view()

        # Redraw
        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.show(block=False)  # Show the figure in non-blocking mode

    res = parallel_benchmark(run_single_benchmark_task, tasks, BenchmarkArgs(run_baruah=True), callback=cb)

    input("Press Enter to close the plot...")


def parallel_benchmark(
    task_function: Callable,
    tasks,
    benchmark_args: BenchmarkArgs,
    callback: Callable | None = None,
):
    results = []
    total_tasks = len(tasks)
    # We need shared structures for task status and final results
    with Manager() as manager:
        # task_status[i] = True if i-th task has completed
        task_status = manager.list([False] * total_tasks)
        # results_store[i] = (algo_time, baruah_time) for i-th task
        results_store = manager.list([None] * total_tasks)

        # We'll use apply_async so we can specify a callback
        with Pool() as pool:
            for i, task_args in enumerate(tasks):
                pool.apply_async(
                    task_function,
                    args=(task_args, benchmark_args),
                    # The callback updates the shared data structures
                    callback=lambda result, i=i: (
                        task_status.__setitem__(i, True),
                        results_store.__setitem__(i, result),
                    ),
                )

            # Live-print status until all tasks are done
            while True:

                # Build a string: X for done, _ for not done
                num_done = sum(task_status)
                status_str = f"{num_done}/{total_tasks}"
                print(f"\r{status_str}", end="", flush=True)

                if callback is not None:
                    callback(deepcopy(results_store))

                # show

                # If all tasks are done, break
                if num_done >= total_tasks and all(task_status):
                    print()  # Move cursor to the next line
                    break

                # Sleep for demo purposes
                time.sleep(0.1)

            # Close the pool and wait for the workers to exit
            pool.close()
            pool.join()

            results.extend(results_store)
    return results


def find_complex_test_cases(threads: int):

    GRAPH_PARAMS = RandomGraphCreateInfo(50, 5, 50, 2)

    did_file_exist = False
    try:
        with open("complex_test_cases.db"):
            did_file_exist = True
    except FileNotFoundError:
        pass

    conn = sqlite3.connect("complex_test_cases.db")
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_nodes INTEGER,
            graph_data TEXT,
            change_from_node INTEGER,
            change_to_node INTEGER,
            new_delay INTEGER,
            expected_messages INTEGER
        );
        """
    )

    if not did_file_exist:
        test_cases = []
        # run 100 random test cases
        for i in range(200):
            print(f"Running test case {i}")
            graph = random_graph(GRAPH_PARAMS)
            system = System(graph, 0)
            edge = random.choice(list(graph.edges()))
            new_delay = random.randint(0, edge.worst_case_delay)

            system.simulate_edge_change((edge.from_node, edge.to_node), new_delay)
            test_cases.append((len(graph.nodes()), str(graph.data), edge.from_node, edge.to_node, new_delay, system.messages_sent))
            print(f"Expected messages: {system.messages_sent}")

        # average and std
        avg = np.mean([x[5] for x in test_cases])
        std = np.std([x[5] for x in test_cases])

        # filter for outliers > 2 std away from avg
        print([x[5] for x in test_cases])
        test_cases = [x for x in test_cases if x[5] > avg + std]
        print(f"Filtered out {len(test_cases)} outliers")

        # insert into db
        c.executemany(
            "INSERT INTO test_cases (num_nodes, graph_data, change_from_node, change_to_node, new_delay, expected_messages) VALUES (?, ?, ?, ?, ?, ?)",
            test_cases,
        )
        conn.commit()
    
    # assume database has test cases
    # get avg and std
    # SELECT AVG((t.row - sub.a) * (t.row - sub.a)) as var from t, 
    # (SELECT AVG(row) AS a FROM t) AS sub;
    
    # first avg
    c.execute("SELECT AVG(expected_messages) FROM test_cases")
    avg = c.fetchone()[0]
    # then std
    c.execute("SELECT AVG((expected_messages - ?) * (expected_messages - ?)) as var FROM test_cases", (avg, avg))
    var = c.fetchone()[0]
    if var == None:
        raise ValueError("No test cases in database")
    std = math.sqrt(var)
    print(f"Avg: {avg}, Std: {std}")
    # generate test cases with expected messages > avg + std using threads

    def generate_test_cases(i, avg, std, conn):
        while True:
            c = conn.cursor()
            graph = random_graph(GRAPH_PARAMS)
            system = System(graph, 0)
            edge = random.choice(list(graph.edges()))
            new_delay = random.randint(0, edge.worst_case_delay)

            system.simulate_edge_change((edge.from_node, edge.to_node), new_delay)
            test_case = (len(graph.nodes()), str(graph.data), edge.from_node, edge.to_node, new_delay, system.messages_sent)
            if test_case[5] > avg - std:
                print(f"Expected messages: {system.messages_sent}")
                c.execute(
                    "INSERT INTO test_cases (num_nodes, graph_data, change_from_node, change_to_node, new_delay, expected_messages) VALUES (?, ?, ?, ?, ?, ?)",
                    test_case,
                )
                conn.commit()
            else:
                print(f"Expected messages: {system.messages_sent} (not complex enough)")

    for i in range(threads):
        print(f"Running thread {i}")
        p = Process(target=generate_test_cases, args=(i, avg, std, conn))
        p.start()       
        
        


if __name__ == "__main__":
    # plt.style.use("bmh")
    # create_info = RandomBenchmarkCreateInfo(
    #     graph_create_info=RandomGraphCreateInfo(
    #         max_delay=10,
    #         min_nodes=5,
    #         max_nodes=50,
    #         min_edges=100**2,
    #     ),
    #     num_runs=100,
    #     verify_against_baruah=False,
    # )
    # # random_benchmark(create_info)
    # # cProfile.run("increasing_graph_size_benchmark(create_info.graph_create_info, 5)", sort="tottime")
    # # increasing_graph_size_benchmark(create_info.graph_create_info, 10)
    # graph_size_vs_messages_benchmark(create_info.graph_create_info, 10)

    find_complex_test_cases(15)
