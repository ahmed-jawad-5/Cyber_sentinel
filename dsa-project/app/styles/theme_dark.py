DARK_THEME = """
/* ---------------- Main Window ---------------- */
QMainWindow, QWidget {
    background-color: #050E3C;
    color: #FFFFFF;
}

/* ---------------- Labels (DSA Project, Search, Sort) ---------------- */
QLabel {
    color: #FFFFFF;
    font-size: 13px;
}

/* ---------------- Buttons ---------------- */
QPushButton {
    background-color: #002455;
    color: #FFFFFF;
    border-radius: 8px;
    padding: 5px 12px;
}

QPushButton:hover {
    background-color: #DC0000;
}

/* ---------------- Inputs ---------------- */
QLineEdit, QComboBox {
    background-color: #002455;
    color: #FFFFFF;
    border-radius: 8px;
    padding: 5px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Dropdown list text (CRITICAL FIX) */
QComboBox QAbstractItemView {
    background-color: #002455;
    color: #FFFFFF;
    selection-background-color: rgba(220,0,0,0.4);
    selection-color: #FFFFFF;
}

/* ---------------- Tables ---------------- */
QTableWidget {
    background-color: #002455;
    color: #FFFFFF;
    alternate-background-color: #050E3C;
}

/* ---------------- Footer / Status text ---------------- */
QStatusBar, QStatusBar QLabel {
    color: #FFFFFF;
    background-color: #002455;
}
QStatusBar, FooterBar, QWidget#FooterBar {
    background-color: #002455;
    color: white;
}

FooterBar QLabel {
    color: white;
}
/* ---------- ALL DROPDOWN / POPUP LISTS ---------- */
QAbstractItemView {
    background-color: #002455;
    color: #FFFFFF;
    border: 1px solid rgba(255,255,255,0.12);
    outline: 0;
}

/* Selected item (WORKS on Fusion + Wayland) */
QAbstractItemView::item:selected {
    background-color: rgba(220, 0, 0, 0.55);
    color: #FFFFFF;
}

/* Selected but NOT focused (CRITICAL FIX) */
QAbstractItemView::item:selected:!active {
    background-color: rgba(220, 0, 0, 0.35);
    color: #FFFFFF;
}

/* Item spacing */
QAbstractItemView::item {
    padding: 6px;
}

"""
