from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

class BookModel(QAbstractTableModel):
    def __init__(self, books=None):
        super().__init__()
        self.books = books or []
        self.headers = ["Title", "Author", "Publisher", "ISBN-13"]

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return self.books[index.row()][index.column()]

    def rowCount(self, index: QModelIndex = QModelIndex()):
        return len(self.books)
    
    def columnCount(self, index: QModelIndex = QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.headers[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None
