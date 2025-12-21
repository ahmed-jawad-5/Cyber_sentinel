import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QFileDialog
from PyQt5.QtCore import Qt
import os 
from app.controllers.data_controller import DataController
from app.controllers.algorithm_controller import AlgorithmController

from app.widgets.top_menu import TopMenu
from app.widgets.floating_search import FloatingSearch
from app.widgets.pro_table import ProTable
from app.widgets.footer_bar import FooterBar
from app.styles.theme_light import LIGHT_THEME
from app.styles.theme_dark import DARK_THEME

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSA Project - Sorting & Searching")
        self.resize(600, 700)

        # Controllers
        self.data_ctrl = DataController()
        self.alg_ctrl = AlgorithmController(self.data_ctrl)

        # Theme state
        self.current_theme = "light"

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.central_widget.setLayout(self.main_layout)

        # Top Menu
        self.top_menu = TopMenu(
            load_callback=self.load_csv,
            download_callback=self.download_csv,
            reset_callback=self.reset_data,
            theme_toggle_callback=self.toggle_theme,
            load_results_callback=self.load_network_results,
            save_db_callback=self.save_to_database,
            load_from_db_callback=self.load_from_database,
        )
        self.main_layout.addWidget(self.top_menu)

        # Floating Search Bar
        self.floating_search = FloatingSearch(
            search_callback=self.on_search,
            sort_callback=self.on_sort
        )
        self.main_layout.addWidget(self.floating_search)

        # Table
        self.table = ProTable()
        self.main_layout.addWidget(self.table)

        # Footer
        self.footer = FooterBar()
        self.main_layout.addWidget(self.footer)

        # Apply initial theme
        self.apply_theme()



    # ---------------------- THEME -----------------------
    def apply_theme(self):
        if self.current_theme == "light":
            # Apply main window stylesheet
            self.setStyleSheet(LIGHT_THEME)
            # Update floating search and table for light theme
            table_bg, table_fg = self.floating_search.set_theme("light")
            self.table.set_table_theme(table_bg, table_fg)

        else:  # dark theme
            self.setStyleSheet(DARK_THEME)
            # Update floating search and table for dark theme
            table_bg, table_fg = self.floating_search.set_theme("dark")
            self.table.set_table_theme(table_bg, table_fg)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()


    # ---------------------- CSV -------------------------
    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        ok, msg = self.data_ctrl.load_csv(path)
        if ok:
            self.table.update_table(self.data_ctrl.df)
            self.floating_search.update_columns(self.data_ctrl.df.columns)
            self.footer.update_status(len(self.data_ctrl.df))
        else:
            self.footer.show_message(msg)

    def load_network_results(self):
        """Load the backend-generated results.csv directly into the table."""
        # Repo root is one level above dsa-project
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        results_csv = os.path.join(repo_root, "backend", "output", "results.csv")

        if not os.path.exists(results_csv):
            self.footer.show_message(f"results.csv not found at {results_csv}")
            return

        ok, msg = self.data_ctrl.load_csv(results_csv)
        if ok:
            self.table.update_table(self.data_ctrl.df)
            self.floating_search.update_columns(self.data_ctrl.df.columns)
            self.footer.update_status(len(self.data_ctrl.df))
            self.footer.show_message("Loaded network results from backend.")
        else:
            self.footer.show_message(msg)

    def download_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            self.footer.show_message("Save cancelled")
            return
        ok, msg = self.data_ctrl.save_csv(path)  # ✅ pass path
        self.footer.show_message(msg)


    def reset_data(self):
        restored = self.data_ctrl.restore_original()
        if restored:
            self.table.update_table(self.data_ctrl.df)
            self.footer.update_status(len(self.data_ctrl.df))
            self.footer.show_message("Data restored")
        else:
            self.footer.show_message("No original data stored")

    # ---------------------- DATABASE ----------------------
    def save_to_database(self):
        """Persist current table into the custom DB under dbdata/network_results."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_root = os.path.join(repo_root, "dbdata")

        ok, msg = self.data_ctrl.save_to_db(db_root=db_root, table_name="network_results", primary_key="id")
        self.footer.show_message(msg)

    def load_from_database(self):
        """Load rows from the custom DB back into the table."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_root = os.path.join(repo_root, "dbdata")

        ok, msg = self.data_ctrl.load_from_db(db_root=db_root, table_name="network_results")
        if ok:
            self.table.update_table(self.data_ctrl.df)
            self.floating_search.update_columns(self.data_ctrl.df.columns)
            self.footer.update_status(len(self.data_ctrl.df))
        self.footer.show_message(msg)

    # ---------------------- SEARCH ----------------------
    def on_search(self, query, column_name, search_type):
        if not column_name or column_name not in self.data_ctrl.df.columns:
            self.footer.show_message("Select a valid column for search")
            return
        idx, ms = self.alg_ctrl.run_search(query, column_name, search_type)
        if idx is None or idx == -1:
            self.footer.show_message(f"'{query}' not found")
        else:
            self.footer.show_message(f"Found '{query}' at index {idx} in {ms:.3f}ms")
            self.table.highlight_row(idx)

    # ---------------------- SORT ------------------------
    def on_sort(self, column_name, sort_type):
        if not column_name or column_name not in self.data_ctrl.df.columns:
            self.footer.show_message("Select a valid column for sorting")
            return
        ok, ms = self.alg_ctrl.run_sort(column_name, sort_type)
        if ok:
            self.table.update_table(self.data_ctrl.df)
            self.footer.show_message(f"Sorted by '{column_name}' using {sort_type} ({ms:.3f}ms)")
        else:
            self.footer.show_message("Sort failed")
    def resizeEvent(self, event):
        """Forces the UI to recalculate hitboxes when Hyprland resizes the window."""
        super().resizeEvent(event)
        # Force a full layout recalculation
        self.centralWidget().updateGeometry()
        self.centralWidget().layout().activate()
        # Repaint the window to align mouse coordinates
        self.update()
if __name__ == "__main__":
    # Force absolute pixel mapping (Critical for Hyprland/Wayland)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    
    # Force Wayland backend
    os.environ["QT_QPA_PLATFORM"] = "wayland"

    app = QApplication(sys.argv)
    
    # Bypass Kvantum/System themes that cause mouse offset
    app.setStyle("Fusion") 
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())