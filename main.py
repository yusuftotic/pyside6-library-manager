import sys
import os
import json
import uuid
import copy
import requests
from bs4 import BeautifulSoup
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
	QModelIndex,
	QObject,
	QTimer,
	QRunnable,
	QThreadPool,
	Signal,
	Slot,
)

class ScraperWorkerSignals(QObject):
	finished = Signal()
	error = Signal(str)
	result = Signal(dict)

class ScraperWorker(QRunnable):
	def __init__(self, _isbn:str="1692492780"):
		super().__init__()
		
		self._isbn = _isbn
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
			'Connection': 'keep-alive',
			'Upgrade-Insecure-Requests': '1',
			# 'Referer': 'https://www.google.com/'
		}

		self.signals = (
			ScraperWorkerSignals()
		)

	@Slot()
	def run(self):
		print("THREAD IS RUNNING...")

		_isbn10 = ""

		if "-" in self._isbn:
			self._isbn = self._isbn.replace("-", "")
		
		if len(self._isbn) == 13:
			_isbn10 = self._isbn[3::]
		
		elif len(self._isbn) == 10:
			_isbn10 = self._isbn

		else:
			print("[ERROR] - You should enter a valid ISBN.")
			return
		
		try:
			book_amazon_url = f"https://www.amazon.com/dp/{_isbn10}"

			page = requests.get(url=book_amazon_url, headers=self.headers)

			soup = BeautifulSoup(page.text, "html.parser")

			title = ""
			author = ""
			publisher = ""
			publication_date = ""
			isbn10 = ""
			isbn13 = ""
			page_count = ""
			language = ""
			description = ""

			if soup.find(id="productTitle"):
				title = soup.find(id="productTitle").text.strip()

			# +++++++++ Translator
			if soup.find(class_="author").a:
				author = soup.find(class_="author").a.text # Author


			for i in soup.find(id="detailBullets_feature_div").find("ul").find_all(class_="a-list-item"):
				
				if ("Publisher" in i.find_all("span")[0].text):
					publisher = i.find_all("span")[1].text
				
				elif ("Publication date" in i.find_all("span")[0].text):
					publication_date = i.find_all("span")[1].text

				elif ("ISBN-10" in i.find_all("span")[0].text):
					isbn10 = i.find_all("span")[1].text
				
				elif ("ISBN-13" in i.find_all("span")[0].text):
					isbn13 = i.find_all("span")[1].text
				
				elif ("Print length" in i.find_all("span")[0].text):
					page_count = i.find_all("span")[1].text
				
				elif ("Language" in i.find_all("span")[0].text):
					language = i.find_all("span")[1].text

			isDescription = True if soup.find(id="bookDescription_feature_div") else False
			description = soup.find(id="bookDescription_feature_div").text.strip().replace(" Read more", "") if isDescription else "" # Description
			
			# price = soup.find(class_="slot-price").text.strip().replace("from ", "") # Price

			# print(title, author, isbn10, isbn13, language, description, price)

		except Exception as err:
			self.signals.error.emit(err)

		else:
			self.signals.finished.emit()
			self.signals.result.emit({
				"title": title,
				"author": author,
				"publisher": publisher,
				"publication_date": publication_date,
				"isbn10": isbn10,
				"isbn13": isbn13,
				"page_count": page_count,
				"language": language,
				"description": description,
			})

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

class MainWindow(QMainWindow):
	
	def __init__(self):
		super().__init__()

		self.db = BasicDB(collection_name="books", root_dir=os.path.abspath(__file__))
		self.books = self.db.find()
		self.books_list = self.extract_values_from_docs(self.books)
		self.scraped_book = None

		self.setup_ui()

		self.model = BookModel(self.books_list)
		self.table_view.setModel(self.model)

		## QThreadPool
		self.threadpool = QThreadPool()
		print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")


		# ////////////////////////
		# Signals
		self.button_add.clicked.connect(self.add_book)
		self.button_edit.clicked.connect(self.edit_book)
		self.button_delete.clicked.connect(self.delete_book)

		self.table_view.pressed.connect(lambda: self.button_edit.setDisabled(False))
		self.table_view.pressed.connect(lambda: self.button_delete.setDisabled(False))

		self.table_view.doubleClicked.connect(self.show_book_details_dialog)

		self.lineedit_search.textChanged.connect(self.search_book)

		
	def handle_search_text_changed(self, search_text):

		QTimer.singleShot(300, lambda: self.search_book(search_text=search_text))

	def search_book(self, search_text):

		if len(search_text) == 0:
			self._update_model()
			return

		books = self.db.find()

		search_text = search_text.lower()

		def linear_search(search_text):
			found_books = []
			for book in books:
				for key, value in book.items():

					if search_text and search_text in value.lower() and key != "_id":
						found_books.append(book)
						break
			return found_books

		self._update_model(linear_search(search_text))

	
		
	def add_book(self):
		self.show_form_dialog()



	def edit_book(self):

		indexes = self.table_view.selectedIndexes()

		if indexes:
			row = indexes[0].row()

			selected_book = self.books[row]

			self.show_form_dialog(existing_book=selected_book)



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

				# print(f"[INFO] - '{selected_book[0]}' was deleted.")
				self._update_model()


	# ////////////////////////////////////////////////////////////
	# SCRAPER WORKER ////////////////////////////////////////////
	def start_scraper_worker(self, _isbn:str, callback=None):
		## Defining ScraperWorker for scraping
		scraper_worker = ScraperWorker(_isbn)
		if callback:
			scraper_worker.signals.result.connect(callback)
		scraper_worker.signals.result.connect(self.scaper_worker_output)
		scraper_worker.signals.error.connect(self.scraper_worker_error)
		scraper_worker.signals.finished.connect(self.scaper_worker_complete)
		self.threadpool.start(scraper_worker)

	def scaper_worker_output(self, s):
		print("RESULT", s)

	def scaper_worker_complete(self):
		print("THREAD COMPLETE")

	def scraper_worker_error(self, t):
		print("ERROR: ", t)
	# ////////////////////////////////////////////////////////////


	def show_form_dialog(self, existing_book:list=None):

		self.keep_dialog_open_state = False

		dialog = QDialog(self)

		dialog_x , dialog_y = self.get_available_coordinates()

		dialog.setWindowTitle("Holocron - Add Contact")

		dialog.setModal(True)

		dialog.setFixedWidth(600)
		dialog.resize(600, 600)
		# dialog.setGeometry(dialog_x, dialog_y, 600, 500)

		layout = QVBoxLayout()
		layout.setSpacing(15)

		#///////////////////////////////////////////////////
		# SETUP DIALOG UI

		## Scraping
		layout_scraping_input = QHBoxLayout()
		layout_scraping_input.setSpacing(10)
		layout_scraping_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

		lineedit_scraping_input = QLineEdit()
		lineedit_scraping_input.setPlaceholderText("Enter ISBN-10 or ISBN-13...")
		# lineedit_scraping_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		lineedit_scraping_input.clearFocus()
		layout_scraping_input.addWidget(lineedit_scraping_input)

		button_scraping_input = QPushButton("Scrape Book")
		button_scraping_input.setStyleSheet("padding: 5px 10px;")
		button_scraping_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		layout_scraping_input.addWidget(button_scraping_input)
		if not existing_book:
			layout.addLayout(layout_scraping_input)


		## Add Form: Title
		layout_add_title = QHBoxLayout()
		label_add_title = QLabel("Title*")
		label_add_title.setStyleSheet("font-size: 12px;")
		label_add_title.setFixedWidth(120)
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
		label_add_authors.setFixedWidth(120)
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
		label_add_publisher.setFixedWidth(120)
		layout_add_publisher.addWidget(label_add_publisher)

		lineedit_add_publisher = QLineEdit()
		if existing_book:
			lineedit_add_publisher.setText(existing_book["publisher"])
		lineedit_add_publisher.setPlaceholderText("e.g. Secker & Warburg")
		lineedit_add_publisher.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_publisher.addWidget(lineedit_add_publisher)
		## Add Form: Publication Date
		layout_add_publication_date = QHBoxLayout()
		label_add_publication_date = QLabel("Publication Date")
		label_add_publication_date.setStyleSheet("font-size: 12px;")
		label_add_publication_date.setFixedWidth(120)
		layout_add_publication_date.addWidget(label_add_publication_date)

		lineedit_add_publication_date = QLineEdit()
		if existing_book:
			lineedit_add_publication_date.setText(existing_book["publicationDate"])
		lineedit_add_publication_date.setPlaceholderText("e.g. 1949")
		lineedit_add_publication_date.setStyleSheet("padding: 2px 0; font-size: 12px;")
		layout_add_publication_date.addWidget(lineedit_add_publication_date)
		## Add Form: ISBN-10
		layout_add_isbn10 = QHBoxLayout()
		label_add_isbn10 = QLabel("ISBN-10")
		label_add_isbn10.setStyleSheet("font-size: 12px;")
		label_add_isbn10.setFixedWidth(120)
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
		label_add_isbn13.setFixedWidth(120)
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
		label_add_page_count.setFixedWidth(120)
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
		label_add_language.setFixedWidth(120)
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
		label_add_genres.setFixedWidth(120)
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
		label_add_description.setFixedWidth(120)
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
		layout_add_form.setSpacing(10)
		layout.addLayout(layout_add_form)


		layout_add_form.addLayout(layout_add_title)
		layout_add_form.addLayout(layout_add_authors)
		layout_add_form.addLayout(layout_add_publisher)
		layout_add_form.addLayout(layout_add_publication_date)
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
			publication_date = lineedit_add_publication_date.text().strip()
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
					"publicationDate": publication_date,
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

				lineedit_scraping_input.clear()

				title = lineedit_add_title.clear()
				authors = lineedit_add_authors.clear()
				publisher = lineedit_add_publisher.clear()
				publication_date = lineedit_add_publication_date.clear()
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
		

		def fill_scraped_book(scraped_book):

			if scraped_book:
				
				lineedit_add_title.setText(scraped_book["title"])
				lineedit_add_authors.setText(scraped_book["author"])
				lineedit_add_publisher.setText(scraped_book["publisher"])
				lineedit_add_publication_date.setText(scraped_book["publication_date"])
				lineedit_add_isbn10.setText(scraped_book["isbn10"])
				lineedit_add_isbn13.setText(scraped_book["isbn13"])
				lineedit_add_page_count.setText(scraped_book["page_count"])
				lineedit_add_language.setText(scraped_book["language"])
				# lineedit_add_genres.setText()
				textedit_add_description.setText(scraped_book["description"])


		#/////////////////////////////////////////////////////////
		## Signals
		button_scraping_input.clicked.connect(
			lambda: self.start_scraper_worker(lineedit_scraping_input.text().strip(), fill_scraped_book)
		)

		button_form_save_book.clicked.connect(save_book)
		button_form_cancel.clicked.connect(dialog.close)

		checkbox_keep_dialog_open.stateChanged.connect(update_keep_dialog_open_state)
		#/////////////////////////////////////////////////////////


		dialog.show()



	def show_book_details_dialog(self, index:QModelIndex):

		row = index.row()
		selected_books_id = self.books_list[row][-1]
		book_in_detail = self.db.find_by_id(selected_books_id)

		dialog = QDialog(self)
		dialog_x, dialog_y = self.get_available_coordinates()
		dialog.setGeometry(dialog_x, dialog_y, 500, 400)
		dialog.setFixedWidth(500)
		dialog.setModal(True)
		dialog.setWindowTitle(f"{book_in_detail['title']} - Details")

		# Main layout
		layout = QVBoxLayout()
		layout.setSpacing(5)
		dialog.setLayout(layout)

		# Title section
		title_label = QLabel(book_in_detail['title'])
		title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
		title_label.setWordWrap(True)
		layout.addWidget(title_label)

		# Author section
		if book_in_detail.get('authors'):
			author_label = QLabel(f"<b>Author:</b> {book_in_detail['authors']}")
			author_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			author_label.setWordWrap(True)
			layout.addWidget(author_label)

		# Publisher section
		if book_in_detail.get('publisher'):
			publisher_label = QLabel(f"<b>Publisher:</b> {book_in_detail['publisher']}")
			publisher_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			publisher_label.setWordWrap(True)
			layout.addWidget(publisher_label)

		# Publication date section
		if book_in_detail.get('publicationDate'):
			pub_date_label = QLabel(f"<b>Publication Date:</b> {book_in_detail['publicationDate']}")
			pub_date_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			layout.addWidget(pub_date_label)

		# ISBN section
		isbn_layout = QHBoxLayout()
		if book_in_detail.get('isbn10'):
			isbn10_label = QLabel(f"<b>ISBN-10:</b> {book_in_detail['isbn10']}")
			isbn10_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			isbn_layout.addWidget(isbn10_label)
		
		if book_in_detail.get('isbn13'):
			isbn13_label = QLabel(f"<b>ISBN-13:</b> {book_in_detail['isbn13']}")
			isbn13_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			isbn_layout.addWidget(isbn13_label)
		
		if isbn_layout.count() > 0:
			layout.addLayout(isbn_layout)

		# Page count section
		if book_in_detail.get('pageCount'):
			page_count_label = QLabel(f"<b>Pages:</b> {book_in_detail['pageCount']}")
			page_count_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			layout.addWidget(page_count_label)

		# Language section
		if book_in_detail.get('language'):
			language_label = QLabel(f"<b>Language:</b> {book_in_detail['language']}")
			language_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			layout.addWidget(language_label)

		# Genres section
		if book_in_detail.get('genres'):
			genres_label = QLabel(f"<b>Genres:</b> {book_in_detail['genres']}")
			genres_label.setStyleSheet("font-size: 14px; margin: 5px 0;")
			genres_label.setWordWrap(True)
			layout.addWidget(genres_label)

		# Description section
		if book_in_detail.get('description'):
			description_label = QLabel("<b>Description:</b>")
			description_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0 5px 0;")
			layout.addWidget(description_label)
			
			description_text = QTextEdit()
			description_text.setPlainText(book_in_detail['description'])
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
		edit_button.clicked.connect(lambda: self.edit_book_from_details(book_in_detail, dialog))
		close_button.clicked.connect(dialog.close)

		dialog.show()

	def edit_book_from_details(self, book_data, dialog=None):
		if dialog:
			dialog.close()
		self.show_form_dialog(existing_book=book_data)

	def get_available_coordinates(self):

		geo = self.geometry()

		windowsize = { "x": geo.x(), "y": geo.y(), "width": geo.width(), "height": geo.height()} 

		screensize = { "width": self.screen().size().toTuple()[0], "hieght": self.screen().size().toTuple()[1]}

		dialog_width = 400
		dialog_x = None
		dialog_y = windowsize["y"] + 0

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



	def _update_model(self, books:dict = None):

		self.books = books if books != None else self.db.find()

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
		
		# ///////////////////////////////////
		layout_search = QHBoxLayout()
		layout.addLayout(layout_search)

		self.lineedit_search = QLineEdit()
		self.lineedit_search.setPlaceholderText("Search a book...")
		self.lineedit_search.setFixedSize(400, 30)
		layout_search.addWidget(self.lineedit_search)


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




class BasicDB:

    def __init__(self, collection_name: str, root_dir : str):
        self.collection_name = collection_name

        self.base_dir = os.path.join(os.path.dirname(root_dir), "data")
        self.file_path = os.path.join(self.base_dir, f"{self.collection_name}.json")

        self._ensure_data_directory_exists()
        self._ensure_collection_file_exists()
        


    def _ensure_data_directory_exists(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            print(f"[INFO] - '{self.base_dir}' directory was created.")
            

    def _read_all_documents(self) -> list:
        try:
            with open(self.file_path, mode="r", encoding="utf-8") as file:
                return json.load(file)
            
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
    def _write_all_documents(self, documents: list):
        try:
            with open(self.file_path, mode="w", encoding="utf-8") as file:
                json.dump(documents, file, ensure_ascii=False, indent=None)
        
        except IOError as err:
            print(f"[ERROR] - {self.collection_name}.json dosyasına yazma hatası: {err}")
            raise


    def _ensure_collection_file_exists(self):
        if not os.path.exists(self.file_path):
            self._write_all_documents([])
            print(f"[INFO] - '{self.collection_name}.json' file was created.")


    # CREATE Opearations

    def create(self, doc: dict) -> dict:
        
        if not isinstance(doc, dict):
            raise ValueError("Documents must be a dictionary.")
        
        _id = uuid.uuid4().hex
        
        documents = self._read_all_documents()

        new_doc = copy.deepcopy(doc)
        new_doc["_id"] = _id

        documents.append(new_doc)

        self._write_all_documents(documents)
        
        print(f"[INFO] - Belge eklendi: {new_doc.get('title', new_doc.get('name', new_doc['_id']))}")
        
        return new_doc
        
    
    # READ Operations

    def find(self, query: dict=None) -> list:
        
        documents = self._read_all_documents()

        if not query:
            return documents

        results = []
        for doc in documents:
            query_bools = []
            for key, value in query.items():
                if key in doc and doc[key] == value:
                    query_bools.append(True)
                else:
                    query_bools.append(False)
            if all(query_bools):
                results.append(doc)

        # results = [
        #     doc for doc in documents
        #     if all(key in doc and doc[key] == value for key, value in query.items())
        # ]

        if results:
            return results

        return None
    
    
    def find_by_id(self, _id: str) -> dict | None:
        
        documents = self._read_all_documents()

        # result = [
        #     doc for doc in documents if doc and doc["_id"] == _id
        # ]

        result = None

        for doc in documents:
            if doc["_id"] == _id:
                result = doc
            
        return result


    # UPDATE Operations

    def find_by_id_and_update(self, _id: str, update: dict) -> dict | None:

        documents = self._read_all_documents()
        
        doc = self.find_by_id(_id)

        if not doc:
            return None

        doc_index = documents.index(doc)

        update["_id"] = _id

        documents[doc_index] = update

        self._write_all_documents(documents)

        return update


    # DELETE Operations

    def find_by_id_and_delete(self, _id: str):
        
        documents = self._read_all_documents()
        
        doc = self.find_by_id(_id)

        doc_index = documents.index(doc)

        documents.pop(doc_index)

        self._write_all_documents(documents)



if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())