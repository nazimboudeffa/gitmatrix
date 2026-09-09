"""Thème sombre global de GitMatrix (QSS)."""

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e2127;
    color: #d7dae0;
    font-size: 13px;
}

QToolBar {
    background-color: #22252b;
    border-bottom: 1px solid #3a3f46;
    padding: 4px;
    spacing: 4px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 5px 11px;
    color: #d7dae0;
    font-weight: 500;
}
QToolBar QToolButton:hover {
    background-color: #2d3138;
    border-color: #3a3f46;
}
QToolBar QToolButton:pressed {
    background-color: #262a31;
}
QToolBar QToolButton:disabled {
    color: #6b7381;
}

/* Bouton d'action primaire (Commit) dans la toolbar — accent doré */
QToolBar QToolButton#ActionCommit {
    background-color: #e5c07b;
    border-color: #e5c07b;
    color: #1f2228;
    font-weight: 600;
    padding: 5px 16px;
}
QToolBar QToolButton#ActionCommit:hover {
    background-color: #d4b06e;
    border-color: #d4b06e;
}
QToolBar QToolButton#ActionCommit:pressed {
    background-color: #c9a565;
}
QToolBar QToolButton#ActionDanger {
    color: #e06c75;
}

QTreeWidget, QListWidget, QPlainTextEdit {
    background-color: #22252b;
    border: 1px solid #32363e;
    border-radius: 4px;
    padding: 4px;
    selection-background-color: #2f4f6f;
    selection-color: #ffffff;
}
QTreeWidget::item, QListWidget::item {
    border-radius: 3px;
}
QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #262a31;
}

QSplitter::handle {
    background-color: #2a2e35;
    width: 6px;
    height: 6px;
}
QSplitter::handle:hover {
    background-color: #3a3f46;
}

QStatusBar {
    background-color: #22252b;
    color: #9da5b4;
    border-top: 1px solid #32363e;
}

QInputDialog, QInputDialog QLabel {
    background-color: #22252b;
    color: #d7dae0;
}

QMessageBox, QMessageBox QLabel {
    background-color: #22252b;
    color: #d7dae0;
}

QLineEdit {
    background-color: #2a2e35;
    border: 1px solid #3a3f46;
    border-radius: 4px;
    padding: 5px 8px;
    color: #d7dae0;
    selection-background-color: #2f4f6f;
}
QLineEdit:focus {
    border-color: #61afef;
}

QDialog {
    background-color: #22252b;
}

QPushButton {
    background-color: #2d3138;
    border: 1px solid #3a3f46;
    border-radius: 4px;
    padding: 7px 16px;
    color: #d7dae0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #373c44;
    border-color: #4a5058;
}
QPushButton:pressed {
    background-color: #262a31;
}
QPushButton:disabled {
    color: #6b7381;
    background-color: #262a31;
}
/* Bouton primaire (Committer) */
QPushButton[accent="true"] {
    background-color: #e5c07b;
    border-color: #e5c07b;
    color: #1f2228;
    font-weight: 600;
}
QPushButton[accent="true"]:hover {
    background-color: #d4b06e;
    border-color: #d4b06e;
}

QLabel#PanelTitle {
    font-weight: 600;
    color: #9da5b4;
    background-color: transparent;
    border: none;
    padding: 4px 2px;
    font-size: 12px;
    letter-spacing: 0.03em;
}

QLabel#EmptyStateTitle {
    font-size: 18px;
    font-weight: 600;
    color: #ffffff;
}
QLabel#EmptyStateText {
    color: #9da5b4;
    font-size: 13px;
}

QMenu {
    background-color: #22252b;
    border: 1px solid #3a3f46;
    padding: 4px;
}
QMenu::item {
    padding: 6px 22px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #2f4f6f;
    color: #ffffff;
}
QMenu::item:disabled {
    color: #6b7381;
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

/* Tooltip natif */
QToolTip {
    background-color: #2d3138;
    color: #d7dae0;
    border: 1px solid #3a3f46;
    padding: 6px 10px;
}
"""
