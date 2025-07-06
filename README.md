# PySide6 Library Manager

A modern desktop application for managing your personal library with advanced features like ISBN barcode scanning and automatic book data fetching.

## Features

- 📚 **Book Management**: Add, edit, delete, and search books
- 📷 **Barcode Scanning**: Scan ISBN barcodes using your computer's camera
- 🌐 **Auto Data Fetching**: Automatically fetch book details from Amazon using ISBN
- 🔍 **Search Functionality**: Search books by title, author, publisher, or ISBN
- 💾 **Local Storage**: Store all data locally in JSON format
- 🎨 **Modern UI**: Clean and intuitive PySide6-based interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pyside6-library-manager.git
cd pyside6-library-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Requirements

- Python 3.8+
- Webcam (for barcode scanning)
- Internet connection (for book data fetching)

## Dependencies

- **PySide6**: Modern Qt framework for Python
- **OpenCV**: Computer vision for camera operations
- **pyzbar**: Barcode detection and decoding
- **requests**: HTTP requests for web scraping
- **BeautifulSoup4**: HTML parsing
- **isbnlib**: ISBN validation and conversion

## Usage

1. **Adding Books**: Click "Add Book" and either manually enter details or scan an ISBN barcode
2. **Scanning Barcodes**: Use the camera to scan ISBN barcodes for automatic data entry
3. **Searching**: Use the search bar to find books by various criteria
4. **Editing**: Select a book and click "Edit" to modify details
5. **Viewing Details**: Double-click a book to see full details

## Project Structure

```
pyside6-library-manager/
├── main.py              # Main application file
├── data/                # Data storage directory
│   └── books.json       # Book database
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## Development Status

- [x] Create UI for initial setup
- [x] Create QTableView
- [x] Add manual book entry functionality
- [x] Write a class for JSON operations
- [x] Implement book addition, editing and deletion operations using this class
- [x] Write book add and edit dialogs
- [x] Fetch book data from Amazon using ISBN
- [x] Implement scraping operations with QRunnable & QThreadPool (ScraperWorker)
- [x] Add search book functionality
- [x] Implement camera-based ISBN barcode scanning with OpenCV
- [x] Add CameraWorker thread for real-time camera processing
- [x] Integrate barcode detection using pyzbar library
- [x] Replace pyisbn with isbnlib for better ISBN validation and conversion
- [x] Add automatic ISBN input from camera scan to form fields
- [x] Implement thread-safe camera start/stop functionality
- [x] Add camera status monitoring and error handling

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).
