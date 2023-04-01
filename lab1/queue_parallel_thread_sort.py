import threading as td
import sys
from queue import Queue
from utils import *


def parallel_thread_sort(size=100, n_thread=4, arr=[], verbose=False):
    if not arr:
        arr = generate_array(size)

    split_arr = split_array(arr, n_thread)
    
    if verbose:
        print(f'initial array: {arr}')
        print(f'initial split array: {split_arr}')

    # sort
    results = []
    threads = []
    queue = Queue()

    for a in split_arr:
        p = td.Thread(target=sort_array, args=(a, queue))
        threads.append(p)
        p.start()

    for p in threads:
        p.join()
        results.append(queue.get())
    
    if verbose:
        print(f'sorted partitions: {results}')
    
    # merge
    while True:
        # if only one partition is left then the array is sorted
        if len(results) == 1:
            break

        # begin merge
        threads = []
        merged_results = []
        n_cpu = len(results) // 2
        rest = len(results) % 2
        i = 0        
        for _ in range(n_cpu):
            p = td.Thread(target=merge, args=(results[i], results[i+1], queue))
            threads.append(p)
            p.start()
            i += 2

        for p in threads:
            p.join()
            merged_results.append(queue.get())
        
        # in case theres an odd number of partitions
        if rest:
            merged_results.append(results[-1])

        results = merged_results.copy()

        if verbose:
            print(f'merged results: {results}')

    if verbose:
        print(f'final results: {results[0]}')

    return results[0] 

if __name__ == '__main__':
    size = int(sys.argv[1])
    n_thread = int(sys.argv[2])
    result = parallel_thread_sort(size=size, n_thread=n_thread, verbose=True)