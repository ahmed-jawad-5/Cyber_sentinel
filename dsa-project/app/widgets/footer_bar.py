from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel


class FooterBar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 0, 0, 0)
        self.setLayout(self.layout)

        self.setFixedHeight(30)

        self.label = QLabel("Ready")
        self.layout.addWidget(self.label)

        # ❌ DO NOT hardcode colors here
        # Theme will control background + text
        self.setStyleSheet("""
            padding-left: 10px;
        """)

    def update_status(self, row_count):
        self.label.setText(f"Showing {row_count} rows")

    def show_message(self, msg):
        self.label.setText(msg)
