# app/algorithms/searches.py
from typing import List, Optional

def linear_search(arr: List, target) -> Optional[int]:
    # case-insensitive string matching, numeric preserved
    for i, v in enumerate(arr):
        try:
            if v == target:
                return i
            # compare as lowered strings
            if str(v).lower() == str(target).lower():
                return i
        except:
            continue
    return -1

def binary_search(arr: List, target) -> Optional[int]:
    # assume arr is already sorted
    left, right = 0, len(arr) - 1
    tgt = str(target).lower()
    while left <= right:
        mid = (left + right) // 2
        mid_val = str(arr[mid]).lower()
        if mid_val == tgt:
            return mid
        elif mid_val < tgt:
            left = mid + 1
        else:
            right = mid - 1
    return -1
