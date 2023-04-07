def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left_arr = arr[:mid]
        right_arr = arr[mid:]
        
        merge_sort(left_arr)
        merge_sort(right_arr)

        i, j, k = 0, 0, 0

        while i < len(left_arr) and j < len(right_arr):
            if left_arr[i] < right_arr[j]:
                arr[k] = left_arr[i]
                i += 1
            else:
                arr[k] = right_arr[j]
                j += 1
            k += 1
        
        while i < len(left_arr):
            arr[k] = left_arr[i]
            i += 1
            k += 1

        while j < len(right_arr):
            arr[k] = right_arr[j]
            j += 1
            k += 1

def selection_sort(arr):
    for i in range(0, len(arr)):
        idx = i
        for j in range(i, len(arr)):
            if arr[j] < arr[idx]:
                idx = j
        # swap
        temp = arr[i]
        arr[i] = arr[idx]
        arr[idx] = temp
