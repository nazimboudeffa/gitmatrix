"""Thème sombre global de GitMatrix (QSS)."""

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e2127;
    color: #d7dae0;
    font-size: 13px;
}

QToolBar {
    background-color: #262a31;
    border-bottom: 1px solid #32363e;
    padding: 4px;
    spacing: 4px;
}
QToolBar QToolButton {
    background-color: #2d3138;
    border: 1px solid #3a3f46;
    border-radius: 4px;
    padding: 4px 10px;
    color: #d7dae0;
}
QToolBar QToolButton:hover {
    background-color: #373c44;
}

QTreeWidget, QListWidget, QPlainTextEdit {
    background-color: #22252b;
    border: 1px solid #32363e;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #2f4f6f;
    selection-color: #ffffff;
}

QSplitter::handle {
    background-color: #2a2e35;
    width: 5px;
}

QStatusBar {
    background-color: #262a31;
    color: #9da5b4;
    border-top: 1px solid #32363e;
}

QInputDialog, QInputDialog QLabel {
    background-color: #22252b;
    color: #d7dae0;
}

QMessageBox {
    background-color: #22252b;
}

QLineEdit {
    background-color: #2a2e35;
    border: 1px solid #3a3f46;
    border-radius: 4px;
    padding: 4px 8px;
    color: #d7dae0;
    selection-background-color: #2f4f6f;
}

QDialog {
    background-color: #22252b;
}

QPushButton {
    background-color: #2d3138;
    border: 1px solid #3a3f46;
    border-radius: 4px;
    padding: 6px 14px;
    color: #d7dae0;
}
QPushButton:hover {
    background-color: #373c44;
}
QPushButton:disabled {
    color: #6b7381;
}

QLabel#PanelTitle {
    font-weight: bold;
    color: #9da5b4;
    background-color: #262a31;
    border: 1px solid #32363e;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    padding: 6px 10px;
}

QMenu {
    background-color: #262a31;
    border: 1px solid #3a3f46;
}
QMenu::item {
    padding: 6px 20px;
}
QMenu::item:selected {
    background-color: #2f4f6f;
}

QScrollBar:vertical {
    background: #1e2127;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3a3f46;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #4a5058;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""