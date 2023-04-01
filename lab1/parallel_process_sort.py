import multiprocessing as mp
import sys
from utils import generate_array, split_array
import time 

def sort_array(arr, queue):
    arr.sort()
    queue.put(arr)

def merge(left_arr, right_arr, queue):
    merged = []
    i, j = 0, 0
    while i < len(left_arr) and j < len(right_arr):
        if left_arr[i] < right_arr[j]:
            merged.append(left_arr[i])
            i += 1
        else:
            merged.append(right_arr[j])
            j += 1
        
    while i < len(left_arr):
        merged.append(left_arr[i])
        i += 1

    while j < len(right_arr):
        merged.append(right_arr[j])
        j += 1
    
    queue.put(merged)

def parallel_process_sort(size=100, n_process=4, arr=[], verbose=False):
    if not arr:
        arr = generate_array(size)

    split_arr = split_array(arr, n_process)
    
    if verbose:
        print(f'initial array: {arr}')
        print(f'initial split array: {split_arr}')

    # sort
    results = []
    processes = []
    queue = mp.Queue()

    for a in split_arr:
        p = mp.Process(target=sort_array, args=(a, queue))
        processes.append(p)
        p.start()

    for p in processes:
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
        processes = []
        merged_results = []
        n_cpu = len(results) // 2
        rest = len(results) % 2
        i = 0        
        for _ in range(n_cpu):
            p = mp.Process(target=merge, args=(results[i], results[i+1], queue))
            processes.append(p)
            p.start()
            i += 2

        for p in processes:
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
    n_process = int(sys.argv[2])
    result = parallel_process_sort(size=size, n_process=n_process, verbose=True)
