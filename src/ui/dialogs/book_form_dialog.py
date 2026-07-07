from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap, QImage
from src.workers.scraper_worker import ScraperWorker

class BookFormDialog(QDialog):
    def __init__(self, db, threadpool, camera_worker, existing_book=None, keep_dialog_open_state=False, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.db = db
        self.threadpool = threadpool
        self.camera_worker = camera_worker
        self.existing_book = existing_book
        self.keep_dialog_open_state = keep_dialog_open_state
        self.on_save_callback = on_save_callback
        
        self.label_camera = QLabel()
        self.lineedit_scraping_input = None
        
        self.setup_ui()
        
        # Start camera if not editing and camera not already running
        if not self.camera_worker.is_camera_running() and not self.existing_book:
            self.camera_worker.frame.connect(self.update_frame)
            self.camera_worker.isbn.connect(self.handle_scanned_isbn)
            self.camera_worker.start_camera()

        self.finished.connect(self.cleanup_camera)
        
    def setup_ui(self):
        self.setWindowTitle("Holocron - Add Contact" if not self.existing_book else "Holocron - Edit Book")
        self.setModal(True)
        self.setFixedWidth(600)
        self.resize(600, 300)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Scraping Section (only if adding a new book)
        if not self.existing_book:
            layout_scraping_input = QHBoxLayout()
            layout_scraping_input.setSpacing(10)
            layout_scraping_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.label_camera.setFixedSize(200, 200)
            layout_scraping_input.addWidget(self.label_camera)

            self.lineedit_scraping_input = QLineEdit()
            self.lineedit_scraping_input.setPlaceholderText("Enter ISBN-10 or ISBN-13...")
            self.lineedit_scraping_input.clearFocus()
            layout_scraping_input.addWidget(self.lineedit_scraping_input)

            button_scraping_input = QPushButton("Scrape Book")
            button_scraping_input.setStyleSheet("padding: 5px 10px;")
            button_scraping_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button_scraping_input.clicked.connect(self.start_scraper)
            layout_scraping_input.addWidget(button_scraping_input)
            
            layout.addLayout(layout_scraping_input)

        # Form Fields
        layout_add_form = QVBoxLayout()
        layout_add_form.setSpacing(10)
        layout.addLayout(layout_add_form)

        # Helper to create horizontal form rows
        def create_form_row(label_text, placeholder, is_required=False, text_edit=False):
            row_layout = QHBoxLayout()
            lbl = QLabel(f"{label_text}*" if is_required else label_text)
            lbl.setStyleSheet("font-size: 12px;")
            lbl.setFixedWidth(120)
            if text_edit:
                lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
            row_layout.addWidget(lbl)
            
            if text_edit:
                field = QTextEdit()
                field.setPlaceholderText(placeholder)
                field.setStyleSheet("padding: 2px 0; font-size: 12px;")
                field.setFixedHeight(100)
            else:
                field = QLineEdit()
                field.setPlaceholderText(placeholder)
                field.setStyleSheet("padding: 2px 0; font-size: 12px;")
            
            row_layout.addWidget(field)
            layout_add_form.addLayout(row_layout)
            return field

        self.field_title = create_form_row("Title", "e.g. 1984", is_required=True)
        self.field_authors = create_form_row("Authors", "e.g. George Orwell", is_required=True)
        self.field_publisher = create_form_row("Publisher", "e.g. Secker & Warburg")
        self.field_publication_date = create_form_row("Publication Date", "e.g. 1949")
        self.field_isbn10 = create_form_row("ISBN-10", "e.g. 6052090493")
        self.field_isbn13 = create_form_row("ISBN-13", "e.g. 978-0451524935", is_required=True)
        self.field_page_count = create_form_row("Page Count", "e.g. 328")
        self.field_language = create_form_row("Language", "e.g. English")
        self.field_genres = create_form_row("Genres", "e.g. Dystopian, Political Fiction, Science Fiction")
        self.field_description = create_form_row("Description", "e.g. Dystopian, Political Fiction...", text_edit=True)

        if self.existing_book:
            self.field_title.setText(self.existing_book.get("title", ""))
            self.field_authors.setText(self.existing_book.get("authors", ""))
            self.field_publisher.setText(self.existing_book.get("publisher", ""))
            self.field_publication_date.setText(self.existing_book.get("publicationDate", ""))
            self.field_isbn10.setText(self.existing_book.get("isbn10", ""))
            self.field_isbn13.setText(self.existing_book.get("isbn13", ""))
            self.field_page_count.setText(self.existing_book.get("pageCount", ""))
            self.field_language.setText(self.existing_book.get("language", ""))
            self.field_genres.setText(self.existing_book.get("genres", ""))
            self.field_description.setPlainText(self.existing_book.get("description", ""))

        # Keep window open checkbox (only if adding a new book)
        if not self.existing_book:
            layout_keep_dialog_open = QHBoxLayout()
            layout_keep_dialog_open.addStretch()
            layout_keep_dialog_open.addWidget(QLabel("Keep window open?"))
            self.checkbox_keep_dialog_open = QCheckBox("No")
            self.checkbox_keep_dialog_open.setChecked(self.keep_dialog_open_state)
            self.checkbox_keep_dialog_open.stateChanged.connect(self.update_keep_dialog_open_state)
            layout_keep_dialog_open.addWidget(self.checkbox_keep_dialog_open)
            layout_add_form.addLayout(layout_keep_dialog_open)

        # Form Buttons
        layout_add_form_buttons_container = QHBoxLayout()
        layout_add_form_buttons_container.setSpacing(10)
        layout.addLayout(layout_add_form_buttons_container)

        self.btn_save = QPushButton("Save Changes" if self.existing_book else "Save Book")
        self.btn_save.setStyleSheet("padding: 5px 0;")
        self.btn_save.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_save.clicked.connect(self.save_book)
        layout_add_form_buttons_container.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("padding: 5px 0;")
        self.btn_cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_cancel.clicked.connect(self.close)
        layout_add_form_buttons_container.addWidget(self.btn_cancel)

        layout.addStretch()
        self.setLayout(layout)

    @Slot(QImage)
    def update_frame(self, q_img):
        if self.label_camera:
            self.label_camera.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.label_camera.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

    @Slot(str)
    def handle_scanned_isbn(self, isbn):
        if self.lineedit_scraping_input:
            self.lineedit_scraping_input.setText(isbn)

    def update_keep_dialog_open_state(self, check_state):
        self.keep_dialog_open_state = (check_state == 2) # Qt.CheckState.Checked

    def cleanup_camera(self):
        try:
            self.camera_worker.frame.disconnect(self.update_frame)
        except (RuntimeError, TypeError):
            pass
        try:
            self.camera_worker.isbn.disconnect(self.handle_scanned_isbn)
        except (RuntimeError, TypeError):
            pass
        self.camera_worker.stop_camera()

    def start_scraper(self):
        isbn = self.lineedit_scraping_input.text().strip()
        if isbn:
            scraper_worker = ScraperWorker(isbn)
            scraper_worker.signals.result.connect(self.fill_scraped_book)
            scraper_worker.signals.error.connect(lambda err: print(f"Scraper error: {err}"))
            self.threadpool.start(scraper_worker)

    @Slot(dict)
    def fill_scraped_book(self, scraped_book):
        if scraped_book:
            self.field_title.setText(scraped_book.get("title", ""))
            self.field_authors.setText(scraped_book.get("author", ""))
            self.field_publisher.setText(scraped_book.get("publisher", ""))
            self.field_publication_date.setText(scraped_book.get("publication_date", ""))
            self.field_isbn10.setText(scraped_book.get("isbn10", ""))
            self.field_isbn13.setText(scraped_book.get("isbn13", ""))
            self.field_page_count.setText(scraped_book.get("page_count", ""))
            self.field_language.setText(scraped_book.get("language", ""))
            self.field_description.setPlainText(scraped_book.get("description", ""))

    def save_book(self):
        title = self.field_title.text().strip()
        authors = self.field_authors.text().strip()
        publisher = self.field_publisher.text().strip()
        publication_date = self.field_publication_date.text().strip()
        isbn10 = self.field_isbn10.text().strip()
        isbn13 = self.field_isbn13.text().strip()
        page_count = self.field_page_count.text().strip()
        language = self.field_language.text().strip()
        genres = self.field_genres.text().strip()
        description = self.field_description.toPlainText().strip()

        if all([title, authors, isbn13]):
            book_data = {
                "title": title,
                "authors": authors,
                "publisher": publisher,
                "publicationDate": publication_date,
                "isbn10": isbn10,
                "isbn13": isbn13,
                "pageCount": page_count,
                "language": language,
                "genres": genres,
                "description": description
            }

            if self.existing_book:
                updated_book = self.db.find_by_id_and_update(self.existing_book["_id"], book_data)
                if updated_book:
                    if self.on_save_callback:
                        self.on_save_callback()
                    self.close()
            else:
                new_book = self.db.create(book_data)
                if new_book:
                    if self.on_save_callback:
                        self.on_save_callback()
                    if not self.keep_dialog_open_state:
                        self.close()
                    else:
                        self.clear_fields()
        else:
            QMessageBox.warning(
                self,
                "Add Contact",
                "Please fill in the required fields",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok
            )

    def clear_fields(self):
        if self.lineedit_scraping_input:
            self.lineedit_scraping_input.clear()
        self.field_title.clear()
        self.field_authors.clear()
        self.field_publisher.clear()
        self.field_publication_date.clear()
        self.field_isbn10.clear()
        self.field_isbn13.clear()
        self.field_page_count.clear()
        self.field_language.clear()
        self.field_genres.clear()
        self.field_description.clear()
