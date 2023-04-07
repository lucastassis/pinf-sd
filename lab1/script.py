import matplotlib.pyplot as plt
from utils import generate_array
from parallel_process_sort import parallel_process_sort
from parallel_thread_sort import parallel_thread_sort
import time

# sort with merge_sort and python_sort
array_sizes = [64, 256, 1024, 8192, 65536, 262144, 1048576]
n_divisions = [1, 2, 4, 8, 16]

process_time = []
thread_time = []

for sort in ['merge_sort', 'python_sort']:
    for n in n_divisions:
        process_temp = []
        thread_temp = []
        
        for size in array_sizes:
            arr = generate_array(size=size)
            print(f'start process parallel for size={size}')
            # run process parallel and time it
            start = time.time()
            process = parallel_process_sort(n_process=n, arr=arr, sort=sort)
            total = time.time() - start
            process_temp.append(total)
            print(f'finished process parallel in {total}s')

            # run thread parallel and time it
            print(f'start thread parallel for size={size}')
            start = time.time()
            thread = parallel_thread_sort(n_thread=n, arr=arr, sort=sort)
            total = time.time() - start
            thread_temp.append(total)
            print(f'finished thread parallel in {total}s')
        
        
        process_time.append(process_temp)
        thread_time.append(thread_temp)


    # plot thread and process thread/process comparison
    fig, ax = plt.subplots(1, 1)
    for i in range(0, len(n_divisions)):
        ax.plot(list(map(str, array_sizes)), process_time[i], label=f'n={n_divisions[i]}')
    plt.xlabel('array size')
    plt.ylabel('total time')
    plt.title(f'comparing {sort} times for multiple number of processes')
    plt.legend()
    plt.savefig(f'./results/process-sort={sort}.png', dpi=400)
    plt.close(fig)

    fig, ax = plt.subplots(1, 1)
    for i in range(0, len(n_divisions)):
        ax.plot(list(map(str, array_sizes)), thread_time[i], label=f'n={n_divisions[i]}')
    plt.xlabel('array size')
    plt.ylabel('total time')
    plt.title(f'comparing {sort} times for multiple number of threads')
    plt.legend()
    plt.savefig(f'./results/thread-sort={sort}.png', dpi=400)
    plt.close(fig)


# sort selection_sort with less array_sizes because of computation time (it is slower)
array_sizes = [64, 256, 1024, 8192, 65536]
n_divisions = [1, 2, 4, 8, 16]

process_time = []
thread_time = []

for sort in ['selection_sort']:
    for n in n_divisions:
        process_temp = []
        thread_temp = []
        
        for size in array_sizes:
            arr = generate_array(size=size)
            print(f'start process parallel for size={size}')
            # run process parallel and time it
            start = time.time()
            process = parallel_process_sort(n_process=n, arr=arr, sort=sort)
            total = time.time() - start
            process_temp.append(total)
            print(f'finished process parallel in {total}s')

            # run thread parallel and time it
            print(f'start thread parallel for size={size}')
            start = time.time()
            thread = parallel_thread_sort(n_thread=n, arr=arr, sort=sort)
            total = time.time() - start
            thread_temp.append(total)
            print(f'finished thread parallel in {total}s')
        
        
        process_time.append(process_temp)
        thread_time.append(thread_temp)


    # plot thread and process thread/process comparison
    fig, ax = plt.subplots(1, 1)
    for i in range(0, len(n_divisions)):
        ax.plot(list(map(str, array_sizes)), process_time[i], label=f'n={n_divisions[i]}')
    plt.xlabel('array size')
    plt.ylabel('total time')
    plt.title(f'comparing {sort} times for multiple number of processes')
    plt.legend()
    plt.savefig(f'./results/process-sort={sort}.png', dpi=400)
    plt.close(fig)

    fig, ax = plt.subplots(1, 1)
    for i in range(0, len(n_divisions)):
        ax.plot(list(map(str, array_sizes)), thread_time[i], label=f'n={n_divisions[i]}')
    plt.xlabel('array size')
    plt.ylabel('total time')
    plt.title(f'comparing {sort} times for multiple number of threads')
    plt.legend()
    plt.savefig(f'./results/thread-sort={sort}.png', dpi=400)
    plt.close(fig)
