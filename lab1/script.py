import matplotlib.pyplot as plt
from utils import generate_array
from parallel_process_sort import parallel_process_sort
from parallel_thread_sort import parallel_thread_sort
import time

array_sizes = [10, 100, 1000, 10000, 20000, 25000]
n_divisions = [1, 2, 4, 8, 16]

for n in n_divisions:
    process_time = []
    thread_time = []
    
    for size in array_sizes:
        arr = generate_array(size=size)
        print(f'start process parallel for size={size}')
        # run process parallel and time it
        start = time.time()
        process = parallel_process_sort(n_process=n, arr=arr)
        total = time.time() - start
        process_time.append(total)
        print(f'finished process parallel in {total}s')

        # run thread parallel and time it
        print(f'start thread parallel for size={size}')
        start = time.time()
        thread = parallel_thread_sort(n_thread=n, arr=arr)
        total = time.time() - start
        thread_time.append(total)
        print(f'finished thread parallel in {total}s')
        
    fig, ax = plt.subplots(1, 1)
    ax.plot(list(map(str, array_sizes)), process_time, label='process')
    ax.plot(list(map(str, array_sizes)), thread_time, label='thread')
    plt.xlabel('array size')
    plt.ylabel('total time')
    plt.title(f'process parallelism x thread parallelism for n={n} process/threads')
    plt.legend()
    plt.savefig(f'./results/{n}.png', dpi=400)
    plt.close(fig)
    
