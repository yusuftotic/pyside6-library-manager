import sys
import os
from PySide6.QtWidgets import (
	QApplication,
	QMainWindow,
	QDialog,
	QMessageBox,
	QWidget,
	QVBoxLayout,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QTextEdit,
	QPushButton,
	QCheckBox,
	QTableView,
	QAbstractItemView,
	QHeaderView
)
from PySide6.QtCore import (
	Qt,
	QAbstractTableModel,
	Signal,
	Slot
)
from utils.database.basicdb import BasicDB

class BookModel(QAbstractTableModel):
	def __init__(self, books=None):
		super().__init__()
		self.books = books or []
		self.headers = ["Title", "Author", "Publisher", "ISBN-13"]

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
				return str(section+1)

class Holocron(QMainWindow):
	
	def __init__(self):
		super().__init__()

		self.db = BasicDB(collection_name="books", root_dir=os.path.abspath(__file__))
		self.books = self.db.find()
		self.books_list = self.extract_values_from_docs(self.books)

		self.setup_ui()

		self.model = BookModel(self.books_list)
		self.table_view.setModel(self.model)


		# ////////////////////////
		# Signals
		self.button_add.clicked.connect(self.add_book)
		self.button_edit.clicked.connect(self.edit_book)
		self.button_delete.clicked.connect(self.delete_book)

		self.table_view.pressed.connect(lambda: self.button_edit.setDisabled(False))
		self.table_view.pressed.connect(lambda: self.button_delete.setDisabled(False))

		
		
	def add_book(self):
		self.show_dialog()

	def edit_book(self):

		indexes = self.table_view.selectedIndexes()

		if indexes:
			row = indexes[0].row()

			selected_book = self.books[row]

			self.show_dialog(existing_book=selected_book)



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

			if reply:
				_id = selected_book[-1]

				self.db.find_by_id_and_delete(_id)

				# print(f"[INFO] - '{selected_book[0]}' was deleted.")
				self._update_model()

					



	def show_dialog(self, existing_book:list=None):

		self.keep_dialog_open_state = False

		dialog = QDialog(self)

		dialog_x , dialog_y = self.get_available_coordinates()

		dialog.setWindowTitle("Holocron - Add Contact")

		dialog.setModal(True)

		dialog.setFixedWidth(400)
		dialog.setGeometry(dialog_x, dialog_y, 400, 250)

		layout = QVBoxLayout()
		layout.setSpacing(40)

		#///////////////////////////////////////////////////
		# SETUP DIALOG UI

		## Add Form: Title
		layout_add_title = QHBoxLayout()
		label_add_title = QLabel("Title*")
		label_add_title.setStyleSheet("font-size: 12px;")
		label_add_title.setFixedWidth(90)
		layout_add_title.addWidget(label_add_title)
		
		lineedit_add_title = QLineEdit()
		if existing_book:
			lineedit_add_title.setText(existing_book["title"])
		lineedit_add_title.setPlaceholderText("e.g. 1984")
		lineedit_add_title.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_title.addWidget(lineedit_add_title)
		## Add Form: Authors
		layout_add_authors = QHBoxLayout()
		label_add_authors = QLabel("Authors*")
		label_add_authors.setStyleSheet("font-size: 12px;")
		label_add_authors.setFixedWidth(90)
		layout_add_authors.addWidget(label_add_authors)

		lineedit_add_authors = QLineEdit()
		if existing_book:
			lineedit_add_authors.setText(existing_book["authors"])
		lineedit_add_authors.setPlaceholderText("e.g. George Orwell")
		lineedit_add_authors.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_authors.addWidget(lineedit_add_authors)
		## Add Form: Publisher
		layout_add_publisher = QHBoxLayout()
		label_add_publisher = QLabel("Publisher")
		label_add_publisher.setStyleSheet("font-size: 12px;")
		label_add_publisher.setFixedWidth(90)
		layout_add_publisher.addWidget(label_add_publisher)

		lineedit_add_publisher = QLineEdit()
		if existing_book:
			lineedit_add_publisher.setText(existing_book["publisher"])
		lineedit_add_publisher.setPlaceholderText("e.g. Secker & Warburg")
		lineedit_add_publisher.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_publisher.addWidget(lineedit_add_publisher)
		## Add Form: Publication Year
		layout_add_publication_year = QHBoxLayout()
		label_add_publication_year = QLabel("Publication Year")
		label_add_publication_year.setStyleSheet("font-size: 12px;")
		label_add_publication_year.setFixedWidth(90)
		layout_add_publication_year.addWidget(label_add_publication_year)

		lineedit_add_publication_year = QLineEdit()
		if existing_book:
			lineedit_add_publication_year.setText(existing_book["publicationYear"])
		lineedit_add_publication_year.setPlaceholderText("e.g. 1949")
		lineedit_add_publication_year.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_publication_year.addWidget(lineedit_add_publication_year)
		## Add Form: ISBN-10
		layout_add_isbn10 = QHBoxLayout()
		label_add_isbn10 = QLabel("ISBN-10")
		label_add_isbn10.setStyleSheet("font-size: 12px;")
		label_add_isbn10.setFixedWidth(90)
		layout_add_isbn10.addWidget(label_add_isbn10)

		lineedit_add_isbn10 = QLineEdit()
		if existing_book:
			lineedit_add_isbn10.setText(existing_book["isbn10"])
		lineedit_add_isbn10.setPlaceholderText("e.g. 6052090493")
		lineedit_add_isbn10.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_isbn10.addWidget(lineedit_add_isbn10)
		## Add Form: ISBN-13
		layout_add_isbn13 = QHBoxLayout()
		label_add_isbn13 = QLabel("ISBN-13*")
		label_add_isbn13.setStyleSheet("font-size: 12px;")
		label_add_isbn13.setFixedWidth(90)
		layout_add_isbn13.addWidget(label_add_isbn13)

		lineedit_add_isbn13 = QLineEdit()
		if existing_book:
			lineedit_add_isbn13.setText(existing_book["isbn13"])
		lineedit_add_isbn13.setPlaceholderText("e.g. 978-0451524935")
		lineedit_add_isbn13.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_isbn13.addWidget(lineedit_add_isbn13)
		## Add Form: Page Count
		layout_add_page_count = QHBoxLayout()
		label_add_page_count = QLabel("Page Count")
		label_add_page_count.setStyleSheet("font-size: 12px;")
		label_add_page_count.setFixedWidth(90)
		layout_add_page_count.addWidget(label_add_page_count)

		lineedit_add_page_count = QLineEdit()
		if existing_book:
			lineedit_add_page_count.setText(existing_book["pageCount"])
		lineedit_add_page_count.setPlaceholderText("e.g. 328")
		lineedit_add_page_count.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_page_count.addWidget(lineedit_add_page_count)
		## Add Form: Language
		layout_add_language = QHBoxLayout()
		label_add_language = QLabel("Language")
		label_add_language.setStyleSheet("font-size: 12px;")
		label_add_language.setFixedWidth(90)
		layout_add_language.addWidget(label_add_language)

		lineedit_add_language = QLineEdit()
		if existing_book:
			lineedit_add_language.setText(existing_book["language"])
		lineedit_add_language.setPlaceholderText("e.g. English")
		lineedit_add_language.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_language.addWidget(lineedit_add_language)
		## Add Form: Genre
		layout_add_genres = QHBoxLayout()
		label_add_genres = QLabel("Genres")
		label_add_genres.setStyleSheet("font-size: 12px;")
		label_add_genres.setFixedWidth(90)
		layout_add_genres.addWidget(label_add_genres)

		lineedit_add_genres = QLineEdit()
		if existing_book:
			lineedit_add_genres.setText(existing_book["genres"])
		lineedit_add_genres.setPlaceholderText("e.g. Dystopian, Political Fiction, Science Fiction")
		lineedit_add_genres.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_genres.addWidget(lineedit_add_genres)
		## Add Form: Description
		layout_add_description = QHBoxLayout()
		label_add_description = QLabel("Description")
		label_add_description.setStyleSheet("font-size: 12px;")
		label_add_description.setFixedWidth(90)
		label_add_description.setAlignment(Qt.AlignmentFlag.AlignTop)
		layout_add_description.addWidget(label_add_description)

		textedit_add_description = QTextEdit()
		if existing_book:
			textedit_add_description.setPlainText(existing_book["description"])
		textedit_add_description.setPlaceholderText("e.g. Dystopian, Political Fiction, Science Fiction")
		textedit_add_description.setStyleSheet("padding: 2px 0; font-size: 12px;")
		textedit_add_description.setFixedHeight(100)
		layout_add_description.addWidget(textedit_add_description)

		

		layout_add_form = QVBoxLayout()
		layout_add_form.setSpacing(15)
		layout.addLayout(layout_add_form)


		layout_add_form.addLayout(layout_add_title)
		layout_add_form.addLayout(layout_add_authors)
		layout_add_form.addLayout(layout_add_publisher)
		layout_add_form.addLayout(layout_add_publication_year)
		layout_add_form.addLayout(layout_add_isbn10)
		layout_add_form.addLayout(layout_add_isbn13)
		layout_add_form.addLayout(layout_add_page_count)
		layout_add_form.addLayout(layout_add_language)
		layout_add_form.addLayout(layout_add_genres)
		layout_add_form.addLayout(layout_add_description)
		

		## Keep window open?
		layout_keep_dialog_open = QHBoxLayout()
		layout_keep_dialog_open.addStretch()
		if not existing_book:
			layout_add_form.addLayout(layout_keep_dialog_open)
		label_keep_dialog_open = QLabel("Keep window open?")
		layout_keep_dialog_open.addWidget(label_keep_dialog_open)
		checkbox_keep_dialog_open = QCheckBox("No")
		checkbox_keep_dialog_open.setChecked(self.keep_dialog_open_state)
		layout_keep_dialog_open.addWidget(checkbox_keep_dialog_open)


		## Form Buttons
		layout_add_form_buttons_container = QHBoxLayout()
		layout_add_form_buttons_container.setSpacing(10)
		layout.addLayout(layout_add_form_buttons_container)

		button_form_save_book = QPushButton("Save Changes") if existing_book else QPushButton("Save Book")
		button_form_save_book.setStyleSheet("padding: 5px 0;")
		button_form_save_book.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		layout_add_form_buttons_container.addWidget(button_form_save_book)

		button_form_cancel = QPushButton("Cancel")
		button_form_cancel.setStyleSheet("padding: 5px 0;")
		button_form_cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		layout_add_form_buttons_container.addWidget(button_form_cancel)

		layout.addStretch()
		dialog.setLayout(layout)


		#/////////////////////////////////////////////////////////


		def save_book():
			
			title = lineedit_add_title.text().strip()
			authors = lineedit_add_authors.text().strip()
			publisher = lineedit_add_publisher.text().strip()
			publication_year = lineedit_add_publication_year.text().strip()
			isbn10 = lineedit_add_isbn10.text().strip()
			isbn13 = lineedit_add_isbn13.text().strip()
			page_count = lineedit_add_page_count.text().strip()
			language = lineedit_add_language.text().strip()
			genres = lineedit_add_genres.text().strip()
			description = textedit_add_description.toPlainText().strip()

			if all([title, authors, isbn13]):

				book_data ={
					"title": title,
					"authors": authors,
					"publisher": publisher,
					"publicationYear": publication_year,
					"isbn10": isbn10,
					"isbn13": isbn13,
					"pageCount": page_count,
					"language": language,
					"genres": genres,
					"description": description
				}

				if existing_book:

					updated_book = self.db.find_by_id_and_update(existing_book["_id"], book_data)
					
					if updated_book:
						self._update_model()

						dialog.close()


				else:
					new_book = self.db.create(book_data)

					if new_book:
						self._update_model()

						if not self.keep_dialog_open_state:
							dialog.close()

				title = lineedit_add_title.clear()
				authors = lineedit_add_authors.clear()
				publisher = lineedit_add_publisher.clear()
				publication_year = lineedit_add_publication_year.clear()
				isbn10 = lineedit_add_isbn10.clear()
				isbn13 = lineedit_add_isbn13.clear()
				page_count = lineedit_add_page_count.clear()
				language = lineedit_add_language.clear()
				genres = lineedit_add_genres.clear()
				description = textedit_add_description.clear()

			else:
				QMessageBox.warning(
					dialog,
					"Add Contact",
					f"Please fill in the required fields",
					QMessageBox.Ok,
					QMessageBox.Ok
				)

		def update_keep_dialog_open_state(check_state):

			if check_state == 2: # Qt.CheckState.Checked
				self.keep_dialog_open_state = True

			elif check_state == 0:
				self.keep_dialog_open_state = False
		

		#/////////////////////////////////////////////////////////
		## Signals
		button_form_save_book.clicked.connect(save_book)
		button_form_cancel.clicked.connect(dialog.close)

		checkbox_keep_dialog_open.stateChanged.connect(update_keep_dialog_open_state)
		#/////////////////////////////////////////////////////////


		dialog.show()

		
	def get_available_coordinates(self):

		geo = self.geometry()

		windowsize = { "x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()} 

		screensize = { "width": self.screen().size().toTuple()[0], "hieght": self.screen().size().toTuple()[1]}

		dialog_width = 400
		dialog_x = None
		dialog_y = windowsize["y"] + 50

		distance_between_windows = - 200

		if (screensize["width"] - (windowsize["x"] + windowsize["width"]) < (dialog_width + distance_between_windows)):
			dialog_x = windowsize["x"] - (dialog_width + distance_between_windows)

		else:
			dialog_x = windowsize["x"] + windowsize["width"] + distance_between_windows

		return (dialog_x, dialog_y)
	
		
	def extract_values_from_docs(self, documents):

		result = []
		for doc in documents:
			# result.append([value for key, value in doc.items() if key in ["title", "authors", "publisher", "isbn13"]])
			result.append([doc["title"], doc["authors"], doc["publisher"], doc["isbn13"], doc["_id"]])

		return result
	
	
	
	def _update_model(self):

		self.books = self.db.find()

		self.books_list = self.extract_values_from_docs(self.books)

		self.model.books = self.books_list

		self.model.layoutChanged.emit()
	
		

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