# app/workers.py
from PyQt5.QtCore import QThread, pyqtSignal
from app.utils.timers import timed

class SortWorker(QThread):
    # emits (pandas.Series sorted_series, float elapsed_seconds)
    finished = pyqtSignal(object, float)
    error = pyqtSignal(str)

    def __init__(self, data_controller, alg_controller, column_name, method):
        super().__init__()
        self.dc = data_controller
        self.ac = alg_controller
        self.column = column_name
        self.method = method

    def run(self):
        try:
            df = self.dc.get_dataframe()
            # get column values as list (dropna to keep simple)
            arr = list(df[self.column].dropna())
            # run sort via algorithm controller (returns list or pandas.Series)
            sorted_ser, elapsed = self.ac.sort_column(df, self.column, self.method)
            # sorted_ser should be a pandas.Series with same name
            self.finished.emit(sorted_ser, elapsed)
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QThread):
    # emits (int index_or_minus1, float elapsed_seconds)
    finished = pyqtSignal(object, float)
    error = pyqtSignal(str)

    def __init__(self, data_controller, alg_controller, column_name, target, method):
        super().__init__()
        self.dc = data_controller
        self.ac = alg_controller
        self.column = column_name
        self.target = target
        self.method = method

    def run(self):
        try:
            df = self.dc.get_dataframe()
            arr = list(df[self.column].dropna())
            # If binary search is requested, ensure it's sorted
            if self.method == "Binary Search" and not self.dc.is_column_sorted(self.column):
                raise RuntimeError("Column must be sorted for binary search. Please sort the column first.")
            idx, elapsed = self.ac.search_in_column(arr, self.target, self.method)
            self.finished.emit(idx, elapsed)
        except Exception as e:
            self.error.emit(str(e))
