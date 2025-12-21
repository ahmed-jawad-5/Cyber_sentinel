
def bubble_sort_indices(arr):
    n = len(arr)
    indices = list(range(n))

    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[indices[j]] > arr[indices[j + 1]]:
                indices[j], indices[j + 1] = indices[j + 1], indices[j]

    return indices
def merge_sort_indices(arr):

    def merge_sort_helper(idx_list):
        if len(idx_list) <= 1:
            return idx_list

        mid = len(idx_list) // 2
        left = merge_sort_helper(idx_list[:mid])
        right = merge_sort_helper(idx_list[mid:])

        return merge(left, right)

    def merge(left, right):
        merged = []
        i = j = 0

        while i < len(left) and j < len(right):
            if arr[left[i]] <= arr[right[j]]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    return merge_sort_helper(list(range(len(arr))))


def quick_sort_indices(arr):

    def quick_sort_helper(idx_list):
        if len(idx_list) <= 1:
            return idx_list

        pivot = arr[idx_list[len(idx_list) // 2]]

        left = [i for i in idx_list if arr[i] < pivot]
        middle = [i for i in idx_list if arr[i] == pivot]
        right = [i for i in idx_list if arr[i] > pivot]

        return quick_sort_helper(left) + middle + quick_sort_helper(right)

    return quick_sort_helper(list(range(len(arr))))
