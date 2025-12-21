# run.py
import os
import sys
from PyQt5.QtWidgets import QApplication

# Ensure the repository root is on sys.path so we can import `data_base` for DB integration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)  # .../UDP_server_NetworkApplication
DATA_BASE_DIR = os.path.join(REPO_ROOT, "data_base")
if DATA_BASE_DIR not in sys.path:
    sys.path.append(DATA_BASE_DIR)

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
