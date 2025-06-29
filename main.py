import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import (
    Qt,
    QAbstractTableModel
)
from utils.database.basicdb import BasicDB

class BookModel(QAbstractTableModel):
    def __init__(self, books=None):
        super().__init__()
        self.books = books or []
        self.headers = ["Title", "Author", "ISBN-10", "ISBN-13", "Language", "Description", "Price"]

    def data(self, index, role):

        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return self.books[index.row()][index.column()]

    def rowCount(self, index):
        return len(self.books)
    
    def columnCount(self, index):
        # return len(self.books[0])
        return len(self.headers)
    
    def headerData(self, section, orientation, role):

        if role == Qt.ItemDataRole.DisplayRole:

            if orientation == Qt.Orientation.Horizontal:
                return self.headers[section]
            
            elif orientation == Qt.Orientation.Vertical:
                return str(section)

class Holocron(QMainWindow):
    
    def __init__(self):
        super().__init__()

        self.db = BasicDB(collection_name="books", root_dir=os.path.abspath(__file__))
        self.books = self.db.find()
        self.books_list = self.extract_values_from_docs(self.books)

        self.setup_ui()

        self.model = BookModel(self.books_list)
        self.table_view.setModel(self.model)

        
    def extract_values_from_docs(self, documents):

        result = []
        for doc in documents:
            result.append([value for key, value in doc.items()])

        return result


    def setup_ui(self):
        self.resize(600, 500)
        self.setWindowTitle("Holocron: Library Manager")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # ///////////////////////////////////
        layout_table = QVBoxLayout()
        layout.addLayout(layout_table)

        label_table_title = QLabel("Books")
        label_table_title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout_table.addWidget(label_table_title)

        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout_table.addWidget(self.table_view)

        # //////////////////////////////////
        layout_buttons_container = QHBoxLayout()
        layout.addLayout(layout_buttons_container)

        self.button_add = QPushButton("Add Book")
        self.button_add.setStyleSheet("padding: 5px 0;")
        layout_buttons_container.addWidget(self.button_add)

        self.button_edit = QPushButton("Edit")
        self.button_edit.setDisabled(True)
        self.button_edit.setStyleSheet("padding: 5px 0;")
        layout_buttons_container.addWidget(self.button_edit)

        self.button_delete = QPushButton("Delete")
        self.button_delete.setDisabled(True)
        self.button_delete.setStyleSheet("padding: 5px 0;")
        layout_buttons_container.addWidget(self.button_delete)
        
        



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Holocron()
    window.show()
    sys.exit(app.exec())