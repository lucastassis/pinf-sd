import numpy as np

def generate_array(size):
    return np.random.permutation(size).tolist()

def split_array(arr, n_process):
    split_arr = np.array_split(arr, n_process)
    return [a.tolist() for a in split_arr]

