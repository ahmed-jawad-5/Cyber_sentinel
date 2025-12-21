from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QListView
from PyQt5.QtCore import Qt


class TopMenu(QWidget):
    def __init__(
        self,
        load_callback,
        download_callback,
        reset_callback,
        theme_toggle_callback,
        load_results_callback=None,
        save_db_callback=None,
        load_from_db_callback=None,
    ):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Title/Branding
        self.title = QLabel("DSA Project")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Core buttons
        self.load_btn = QPushButton("Load CSV")
        self.download_btn = QPushButton("Download CSV")
        self.reset_btn = QPushButton("Reset Data")
        self.theme_btn = QPushButton("Toggle Theme")

        # Optional integration buttons
        self.load_results_btn = None
        self.save_db_btn = None
        self.load_from_db_btn = None

        # Connect callbacks
        self.load_btn.clicked.connect(load_callback)
        self.download_btn.clicked.connect(download_callback)
        self.reset_btn.clicked.connect(reset_callback)
        self.theme_btn.clicked.connect(theme_toggle_callback)

        col = 1
        self.layout.addWidget(self.title, 0, 0)
        self.layout.addWidget(self.load_btn, 0, col); col += 1
        self.layout.addWidget(self.download_btn, 0, col); col += 1
        self.layout.addWidget(self.reset_btn, 0, col); col += 1
        self.layout.addWidget(self.theme_btn, 0, col); col += 1

        buttons = [self.load_btn, self.download_btn, self.reset_btn, self.theme_btn]

        if load_results_callback is not None:
            self.load_results_btn = QPushButton("Load Network Results")
            self.load_results_btn.clicked.connect(load_results_callback)
            self.layout.addWidget(self.load_results_btn, 0, col); col += 1
            buttons.append(self.load_results_btn)

        if save_db_callback is not None:
            self.save_db_btn = QPushButton("Save to DB")
            self.save_db_btn.clicked.connect(save_db_callback)
            self.layout.addWidget(self.save_db_btn, 0, col); col += 1
            buttons.append(self.save_db_btn)

        if load_from_db_callback is not None:
            self.load_from_db_btn = QPushButton("Load From DB")
            self.load_from_db_btn.clicked.connect(load_from_db_callback)
            self.layout.addWidget(self.load_from_db_btn, 0, col); col += 1
            buttons.append(self.load_from_db_btn)

        # Cursor & height
        for btn in buttons:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(35)

        self.layout.setColumnStretch(0, 1)

        # Default style (overridden by set_theme)
        self.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #3D5AFE;
                border-radius: 8px;
                padding: 5px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5F7CFF;
            }
            QPushButton:pressed {
                background-color: #2A3FB1;
            }
        """)

    def set_theme(self, mode):
        """Apply light/dark theme to buttons and title"""
        if mode == "light":
            text_color = "#000000"
            btn_bg = "#3D5AFE"
            btn_hover = "#5F7CFF"
        else:
            text_color = "#FFFFFF"
            btn_bg = "#3D5AFE"
            btn_hover = "#5F7CFF"

        self.title.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {text_color};")

        all_buttons = [
            self.load_btn,
            self.download_btn,
            self.reset_btn,
            self.theme_btn,
        ]
        if self.load_results_btn is not None:
            all_buttons.append(self.load_results_btn)
        if self.save_db_btn is not None:
            all_buttons.append(self.save_db_btn)
        if self.load_from_db_btn is not None:
            all_buttons.append(self.load_from_db_btn)

        for btn in all_buttons:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_bg};
                    color: {text_color};
                    border-radius: 8px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background-color: {btn_hover};
                }}
                QPushButton:pressed {{
                    background-color: #2A3FB1;
                }}
            """)
