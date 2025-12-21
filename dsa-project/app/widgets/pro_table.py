from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt


class ProTable(QTableWidget):
    def __init__(self):
        super().__init__()

        # ---- Original behavior (kept) ----
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ---- Theme-aware text color (NEW) ----
        self.current_text_color = QColor("black")

    # ------------------------------------
    # Populate table
    # ------------------------------------
    def update_table(self, df):
        self.clearContents()
        self.setColumnCount(len(df.columns))
        self.setRowCount(len(df))
        self.setHorizontalHeaderLabels(df.columns.tolist())

        for r in range(len(df)):
            for c in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iat[r, c]))

                # ✅ Theme-aware text color (FIX)
                item.setForeground(QBrush(self.current_text_color))

                self.setItem(r, c, item)

    # ------------------------------------
    # Highlight search result
    # ------------------------------------
    def highlight_row(self, row_idx):
        if row_idx < 0 or row_idx >= self.rowCount():
            return

        self.selectRow(row_idx)
        self.scrollToItem(
            self.item(row_idx, 0),
            QTableWidget.PositionAtCenter
        )

    # ------------------------------------
    # Apply theme (called from MainWindow)
    # ------------------------------------
    def set_table_theme(self, bg_color="white", text_color="black"):
        # Store current theme text color
        self.current_text_color = QColor(text_color)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {bg_color};
                color: {text_color};
                gridline-color: rgba(255,255,255,0.08);
                font-size: 14px;
            }}

            QTableWidget::item:selected {{
                background-color: rgba(220, 0, 0, 0.35);
            }}

            QHeaderView::section {{
                background-color: #002455;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
        """)

        # Update already-created items
        for r in range(self.rowCount()):
            for c in range(self.columnCount()):
                item = self.item(r, c)
                if item:
                    item.setForeground(QBrush(self.current_text_color))
