import time
from app.algorithms.sorts import (
    bubble_sort_indices,
    merge_sort_indices,
    quick_sort_indices,
)
from app.algorithms.searches import linear_search, binary_search

class AlgorithmController:

    def __init__(self, data_controller):
        # Make sure attribute matches usage
        self.data_ctrl = data_controller

    # ---------------------- SORT USING INDEXES -------------------------
    def run_sort(self, column_name, sort_type="bubble"):
        df = self.data_ctrl.df
        if df is None:
            return False, 0

        if column_name not in df.columns:
            return False, 0

        col_data = df[column_name].tolist()

        start = time.perf_counter()

        # Choose algorithm
        if sort_type == "bubble":
            sorted_indices = bubble_sort_indices(col_data)
        elif sort_type == "merge":
            sorted_indices = merge_sort_indices(col_data)
        elif sort_type == "quick":
            sorted_indices = quick_sort_indices(col_data)
        else:
            return False, 0

        end = time.perf_counter()
        elapsed = (end - start) * 1000  # ms

        # Reorder entire DataFrame based on sorted indices
        self.data_ctrl.df = df.iloc[sorted_indices].reset_index(drop=True)

        return True, elapsed

    # ---------------------- SEARCH -------------------------
    def run_search(self, query, column_name, search_type="linear"):
        df = self.data_ctrl.df
        if df is None:
            return None, "No CSV loaded."

        if column_name not in df.columns:
            return None, f"Column '{column_name}' does not exist."

        data_list = df[column_name].astype(str).tolist()

        start = time.perf_counter()

        if search_type == "linear":
            idx = linear_search(data_list, query)
        elif search_type == "binary":
            sorted_list = sorted(data_list)
            idx = binary_search(sorted_list, query)
        else:
            return None, "Invalid search type."

        end = time.perf_counter()
        elapsed = (end - start) * 1000

        return idx, elapsed
