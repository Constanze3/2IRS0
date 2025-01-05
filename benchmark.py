import cProfile
from copy import deepcopy
from multiprocessing import Manager, Pool
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
import matplotlib as mpl
import yappi


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

    res = parallel_benchmark(run_single_benchmark_task, tasks)

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


def run_single_benchmark_task(args):
    """
    Each worker calls this function with a tuple of arguments.
    Returns (algo_time, baruah_time).
    """
    num_nodes, create_info = args

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
            lambda: system.simulate_edge_change(
                (edge_to_change.from_node, edge_to_change.to_node), new_delay
            ),
            timer=time.perf_counter_ns,
            number=1,
        )
        / 10e6
    )
    baruah_time = (
        timeit.timeit(
            lambda: system.recalculate_tables(), timer=time.perf_counter_ns, number=1
        )
        / 10e6
    )
    # baruah_time = 0

    return algo_time, baruah_time


def increasing_graph_size_benchmark(initial_graph_info, num_runs):
    # Prepare a list of tasks (args) to process in parallel
    tasks = []
    for num_nodes in range(
        initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1
    ):
        create_info = RandomGraphCreateInfo(
            max_delay=initial_graph_info.max_delay,
            min_nodes=num_nodes,
            max_nodes=num_nodes,
            min_edges=initial_graph_info.min_edges,
        )
        # Repeat (num_nodes, create_info) for 'num_runs' times
        tasks.extend([(num_nodes, create_info) for _ in range(num_runs)])


    # plt.ion()             # Turn interactive mode on
    fig, ax = plt.subplots()

    # Plot placeholders
    # (line1,) = ax.plot([5], [5], "o", label="Algorithm")
    # (line2,) = ax.plot([6], [6], "o", label="Baruah")

    # algorithm_lines = []
    # baruah_lines = []
    # for i in range(1, num_runs + 1):
    #     algorithm_lines.append(ax.plot([], [], "o", label="Algorithm"))
    #     # (line2,) = ax.plot([], [], "o", label="Baruah")
    #     baruah_lines.append(ax.plot([], [], "o", label="Baruah"))

    algo_line, = ax.plot([], [], "o", label="Algorithm")
    baruah_line, = ax.plot([], [], "o", label="Baruah")

    ax.legend()
    ax.set_autoscaley_on(True)

    # ax.set_xlabel("Number of nodes")
    ax.set_xlabel("Number of nodes")
    ax.set_ylabel("Average Time (ms)")
    ax.set_xscale("linear")
    

    def cb(results):
        node_range = range(initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1)
        # dict mapping each size to a list of results
        size_to_results = {}

        i = 0
        for j, result in enumerate(results):
            size = initial_graph_info.min_nodes + i
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
            y.extend([None if size_to_results[size][i] is None else size_to_results[size][i][0] for i in range(num_runs)])
        algo_line.set_ydata(y)

        baruah_line.set_xdata(x)

        y = []
        for size in size_to_results:
            y.extend([None if size_to_results[size][i] is None else size_to_results[size][i][1] for i in range(num_runs)])
        baruah_line.set_ydata(y)

        ax.relim()
        ax.autoscale_view()

        # Redraw
        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.show(block=False)  # Show the figure in non-blocking mode

    res = parallel_benchmark(run_single_benchmark_task, tasks, callback=cb)

    # Now gather the final results (in the correct order)
    algo_times = [r[0] for r in res]
    baruah_times = [r[1] for r in res]

    # Compute average times per graph size
    algo_times_avg_per_size = []
    baruah_times_avg_per_size = []

    # We'll need to index into the results in blocks of size num_runs
    idx = 0
    for num_nodes in range(
        initial_graph_info.min_nodes, initial_graph_info.max_nodes + 1
    ):
        size_algo_times = algo_times[idx : idx + num_runs]
        size_baruah_times = baruah_times[idx : idx + num_runs]
        idx += num_runs

        algo_times_avg_per_size.append(np.mean(size_algo_times))
        baruah_times_avg_per_size.append(np.mean(size_baruah_times))


def parallel_benchmark(
    task_function: Callable, tasks, callback: Callable | None = None
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
                    args=(task_args,),
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


if __name__ == "__main__":
    plt.style.use("bmh")
    create_info = RandomBenchmarkCreateInfo(
        graph_create_info=RandomGraphCreateInfo(
            max_delay=10,
            min_nodes=5,
            max_nodes=50,
            min_edges=100**2,
        ),
        num_runs=100,
        verify_against_baruah=False,
    )
    # random_benchmark(create_info)
    # cProfile.run("increasing_graph_size_benchmark(create_info.graph_create_info, 5)", sort="tottime")
    increasing_graph_size_benchmark(create_info.graph_create_info, 10)
