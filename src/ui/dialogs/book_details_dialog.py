from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PySide6.QtCore import Qt

class BookDetailsDialog(QDialog):
    def __init__(self, book_in_detail: dict, parent=None, on_edit_callback=None):
        super().__init__(parent)
        self.book_in_detail = book_in_detail
        self.on_edit_callback = on_edit_callback
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setModal(True)
        self.setWindowTitle(f"{self.book_in_detail.get('title', '')} - Details")
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        self.setLayout(layout)

        # Title section
        title_label = QLabel(self.book_in_detail.get('title', ''))
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Author section
        if self.book_in_detail.get('authors'):
            author_label = QLabel(f"<b>Author:</b> {self.book_in_detail['authors']}")
            author_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            author_label.setWordWrap(True)
            layout.addWidget(author_label)

        # Publisher section
        if self.book_in_detail.get('publisher'):
            publisher_label = QLabel(f"<b>Publisher:</b> {self.book_in_detail['publisher']}")
            publisher_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            publisher_label.setWordWrap(True)
            layout.addWidget(publisher_label)

        # Publication date section
        if self.book_in_detail.get('publicationDate'):
            pub_date_label = QLabel(f"<b>Publication Date:</b> {self.book_in_detail['publicationDate']}")
            pub_date_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            layout.addWidget(pub_date_label)

        # ISBN section
        isbn_layout = QHBoxLayout()
        if self.book_in_detail.get('isbn10'):
            isbn10_label = QLabel(f"<b>ISBN-10:</b> {self.book_in_detail['isbn10']}")
            isbn10_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            isbn_layout.addWidget(isbn10_label)
        
        if self.book_in_detail.get('isbn13'):
            isbn13_label = QLabel(f"<b>ISBN-13:</b> {self.book_in_detail['isbn13']}")
            isbn13_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            isbn_layout.addWidget(isbn13_label)
        
        if isbn_layout.count() > 0:
            layout.addLayout(isbn_layout)

        # Page count section
        if self.book_in_detail.get('pageCount'):
            page_count_label = QLabel(f"<b>Pages:</b> {self.book_in_detail['pageCount']}")
            page_count_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            layout.addWidget(page_count_label)

        # Language section
        if self.book_in_detail.get('language'):
            language_label = QLabel(f"<b>Language:</b> {self.book_in_detail['language']}")
            language_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            layout.addWidget(language_label)

        # Genres section
        if self.book_in_detail.get('genres'):
            genres_label = QLabel(f"<b>Genres:</b> {self.book_in_detail['genres']}")
            genres_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
            genres_label.setWordWrap(True)
            layout.addWidget(genres_label)

        # Description section
        if self.book_in_detail.get('description'):
            description_label = QLabel("<b>Description:</b>")
            description_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0 5px 0;")
            layout.addWidget(description_label)
            
            description_text = QTextEdit()
            description_text.setPlainText(self.book_in_detail['description'])
            description_text.setReadOnly(True)
            description_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid transparent;
                    border-radius: 5px;
                    font-size: 13px;
                    line-height: 1.4;
                }
            """)
            description_text.setFixedHeight(150)
            layout.addWidget(description_text)

        # Add some spacing
        layout.addStretch()

        # Buttons section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        edit_button = QPushButton("Edit Book")
        edit_button.setStyleSheet("padding: 8px 0;")
        button_layout.addWidget(edit_button)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("padding: 8px 0;")
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # Connect signals
        edit_button.clicked.connect(self.on_edit_clicked)
        close_button.clicked.connect(self.close)

    def on_edit_clicked(self):
        if self.on_edit_callback:
            self.on_edit_callback(self.book_in_detail)
        self.close()
