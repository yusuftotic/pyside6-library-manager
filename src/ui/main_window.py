import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableView,
    QAbstractItemView, QHeaderView, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QModelIndex, Slot


from src.database.basic_db import BasicDB
from src.models.book_model import BookModel
from src.workers.camera_worker import CameraWorker
from src.ui.dialogs.book_form_dialog import BookFormDialog
from src.ui.dialogs.book_details_dialog import BookDetailsDialog
from src.utils.helpers import get_available_coordinates

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()

        # Resolve root directory dynamically relative to this file
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_root_reference = os.path.join(project_root, "main.py")

        self.db = BasicDB(collection_name="books", root_dir=db_root_reference)
        self.books = self.db.find() or []
        self.books_list = self.extract_values_from_docs(self.books)
        self.scraped_book = None
        self.keep_dialog_open_state = False

        self.setup_ui()

        self.model = BookModel(self.books_list)
        self.table_view.setModel(self.model)

        # Camera worker initialization
        self.camera_worker = CameraWorker()
        self.camera_worker.status.connect(self.handle_camera_status)
        self.camera_worker.error.connect(self.handle_camera_error)

        ## QThreadPool
        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        # Signals
        self.button_add.clicked.connect(self.add_book)
        self.button_edit.clicked.connect(self.edit_book)
        self.button_delete.clicked.connect(self.delete_book)

        self.table_view.pressed.connect(lambda: self.button_edit.setDisabled(False))
        self.table_view.pressed.connect(lambda: self.button_delete.setDisabled(False))

        self.table_view.doubleClicked.connect(self.show_book_details_dialog)

        self.lineedit_search.textChanged.connect(self.search_book)

        QApplication.instance().aboutToQuit.connect(self.camera_worker.stop_camera)

    def handle_camera_error(self, error_msg):
        print(f"Camera error: {error_msg}")
    
    def handle_camera_status(self, status_msg):
        print(f"Camera status: {status_msg}")
        
    def handle_search_text_changed(self, search_text):
        QTimer.singleShot(300, lambda: self.search_book(search_text=search_text))

    def search_book(self, search_text):
        if len(search_text) == 0:
            self._update_model()
            return

        books = self.db.find() or []
        search_text = search_text.lower()

        def linear_search(text):
            found_books = []
            for book in books:
                for key, value in book.items():
                    if text and text in value.lower() and key != "_id":
                        found_books.append(book)
                        break
            return found_books

        self._update_model(linear_search(search_text))

    def add_book(self):
        dialog = BookFormDialog(
            db=self.db,
            threadpool=self.threadpool,
            camera_worker=self.camera_worker,
            keep_dialog_open_state=self.keep_dialog_open_state,
            parent=self,
            on_save_callback=self._update_model
        )
        
        def sync_keep_open_state():
            self.keep_dialog_open_state = dialog.keep_dialog_open_state
        dialog.finished.connect(sync_keep_open_state)
        
        dialog_x, dialog_y = get_available_coordinates(self)
        dialog.setGeometry(dialog_x, dialog_y, 600, 300)
        dialog.show()

    def edit_book(self):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            selected_book = self.books[row]
            
            dialog = BookFormDialog(
                db=self.db,
                threadpool=self.threadpool,
                camera_worker=self.camera_worker,
                existing_book=selected_book,
                parent=self,
                on_save_callback=self._update_model
            )
            dialog_x, dialog_y = get_available_coordinates(self)
            dialog.setGeometry(dialog_x, dialog_y, 600, 300)
            dialog.show()

    def delete_book(self):
        indexes = self.table_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            selected_book = self.books_list[row]

            reply = QMessageBox.question(
                self,
                "Holocron - Delete Book",
                f"Are you sure you want to delete {selected_book[0]}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                _id = selected_book[-1]
                self.db.find_by_id_and_delete(_id)
                self._update_model()

    def show_book_details_dialog(self, index: QModelIndex):
        row = index.row()
        selected_books_id = self.books_list[row][-1]
        book_in_detail = self.db.find_by_id(selected_books_id)

        dialog = BookDetailsDialog(
            book_in_detail=book_in_detail,
            parent=self,
            on_edit_callback=self.show_form_dialog_from_details
        )
        dialog_x, dialog_y = get_available_coordinates(self)
        dialog.setGeometry(dialog_x, dialog_y, 500, 400)
        dialog.show()

    def show_form_dialog_from_details(self, book_data):
        dialog = BookFormDialog(
            db=self.db,
            threadpool=self.threadpool,
            camera_worker=self.camera_worker,
            existing_book=book_data,
            parent=self,
            on_save_callback=self._update_model
        )
        dialog_x, dialog_y = get_available_coordinates(self)
        dialog.setGeometry(dialog_x, dialog_y, 600, 300)
        dialog.show()

    def extract_values_from_docs(self, documents):
        result = []
        if documents:
            for doc in documents:
                result.append([doc["title"], doc["authors"], doc["publisher"], doc["isbn13"], doc["_id"]])
        return result

    def _update_model(self, books: dict = None):
        self.books = books if books is not None else self.db.find() or []
        self.books_list = self.extract_values_from_docs(self.books)
        self.model.books = self.books_list
        self.model.layoutChanged.emit()

    def setup_ui(self):
        self.resize(800, 600)
        self.setWindowTitle("Holocron: Library Manager")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Search layout
        layout_search = QHBoxLayout()
        layout.addLayout(layout_search)

        self.lineedit_search = QLineEdit()
        self.lineedit_search.setPlaceholderText("Search a book...")
        self.lineedit_search.setFixedSize(400, 30)
        layout_search.addWidget(self.lineedit_search)

        # Table layout
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

        # Buttons layout
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
