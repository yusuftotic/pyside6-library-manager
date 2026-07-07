from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from src.scraper.amazon_scraper import scrape_amazon_book

class ScraperWorkerSignals(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(dict)

class ScraperWorker(QRunnable):
    def __init__(self, _isbn: str = "1692492780"):
        super().__init__()
        self._isbn = _isbn
        self.signals = ScraperWorkerSignals()

    @Slot()
    def run(self):
        try:
            result_data = scrape_amazon_book(self._isbn)
        except Exception as err:
            self.signals.error.emit(str(err))
        else:
            self.signals.finished.emit()
            self.signals.result.emit(result_data)
