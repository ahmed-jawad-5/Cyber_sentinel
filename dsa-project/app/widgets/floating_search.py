from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QComboBox, QPushButton, QLabel, QListView
from PyQt5.QtCore import Qt

class FloatingSearch(QWidget):
    def __init__(self, search_callback, sort_callback):
        super().__init__()
        self.search_callback = search_callback
        self.sort_callback = sort_callback
        
        # Grid layout
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(10)

        # --- SEARCH SECTION ---
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search query...")
        self.search_input.setMinimumWidth(150)
        
        self.column_selector = QComboBox()
        self.column_selector.setMinimumWidth(120)
        self.column_selector.setView(QListView())  # Force stylable dropdown
        
        self.search_type_selector = QComboBox()
        self.search_type_selector.addItems(["linear", "binary"])
        self.search_type_selector.setView(QListView())
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self._on_search_clicked)

        # --- SORT SECTION ---
        self.sort_label = QLabel("Sort By:")
        self.sort_column_selector = QComboBox()
        self.sort_column_selector.setMinimumWidth(120)
        self.sort_column_selector.setView(QListView())
        
        self.sort_type_selector = QComboBox()
        self.sort_type_selector.addItems(["bubble", "insertion", "merge", "quick"])
        self.sort_type_selector.setView(QListView())
        
        self.sort_btn = QPushButton("Sort")
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.clicked.connect(self._on_sort_clicked)

        # --- GRID POSITIONING ---
        # Row 0: Search
        self.layout.addWidget(QLabel("Search:"), 0, 0)
        self.layout.addWidget(self.search_input, 0, 1)
        self.layout.addWidget(self.column_selector, 0, 2)
        self.layout.addWidget(self.search_type_selector, 0, 3)
        self.layout.addWidget(self.search_btn, 0, 4)

        # Row 1: Sort
        self.layout.addWidget(self.sort_label, 1, 0)
        self.layout.addWidget(self.sort_column_selector, 1, 1, 1, 2)
        self.layout.addWidget(self.sort_type_selector, 1, 3)
        self.layout.addWidget(self.sort_btn, 1, 4)

        self.setFixedHeight(100)

    def update_columns(self, columns):
        """Update both dropdowns when a CSV is loaded."""
        self.column_selector.clear()
        self.sort_column_selector.clear()
        self.column_selector.addItems(columns)
        self.sort_column_selector.addItems(columns)

    def _on_search_clicked(self):
        query = self.search_input.text()
        col = self.column_selector.currentText()
        stype = self.search_type_selector.currentText()
        if self.search_callback:
            self.search_callback(query, col, stype)

    def _on_sort_clicked(self):
        col = self.sort_column_selector.currentText()
        stype = self.sort_type_selector.currentText()
        if self.sort_callback:
            self.sort_callback(col, stype)

    def set_theme(self, mode):
        """Apply light/dark theme to all widgets."""
        if mode == "light":
            bg_color = "#FFFFFF"
            text_color = "#000000"
            btn_bg = "#3D5AFE"
            btn_hover = "#5F7CFF"
        else:  # dark
            bg_color = "#050E3C"
            text_color = "#FFFFFF"
            btn_bg = "#3D5AFE"
            btn_hover = "#5F7CFF"

        # LineEdit
        self.search_input.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 5px;
            padding: 4px;
        """)

        # ComboBoxes
        combo_style = f"""
            QComboBox {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 5px;
                padding: 4px;
            }}
            QListView {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QListView::item:selected {{
                background-color: rgba(220,0,0,0.55);
                color: {text_color};
            }}
            QListView::item:selected:!active {{
                background-color: rgba(220,0,0,0.35);
                color: {text_color};
            }}
        """
        for combo in [self.column_selector, self.search_type_selector, self.sort_column_selector, self.sort_type_selector]:
            combo.setStyleSheet(combo_style)

        # Buttons
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """
        for btn in [self.search_btn, self.sort_btn]:
            btn.setStyleSheet(btn_style)

        return bg_color, text_color
