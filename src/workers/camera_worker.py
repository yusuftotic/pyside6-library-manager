import cv2
from pyzbar.pyzbar import decode
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QImage

class CameraWorker(QThread):

    frame = Signal(QImage)
    isbn = Signal(str)
    error = Signal(str)
    finished = Signal()
    number = Signal(int)
    status = Signal(str)  # Status updates

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.camera = None
        self.is_camera_active = False

    @Slot()
    def run(self):
        self.is_running = True
        self.status.emit("Starting camera...")
        
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not self.camera.isOpened():
                self.error.emit("Camera could not be opened")
                return
            
            self.is_camera_active = True
            self.status.emit("Camera started successfully")
            
            fps = int(self.camera.get(5))
            print(f"Frame Rate : {fps} frames per second")

            while self.camera.isOpened():
                if not self.is_running:
                    return

                ret, frame = self.camera.read()

                if not ret:
                    self.error.emit("Failed to read frame")
                    break
                
                isbn_barcode = None
                
                decoded_barcodes = decode(frame)
                for decoded_barcode in decoded_barcodes:
                    if decoded_barcode:
                        if decoded_barcode.type == "EAN13":
                            isbn_barcode = decoded_barcode

                if isbn_barcode:
                    isbn_code = isbn_barcode.data.decode("utf-8")
                    self.isbn.emit(isbn_code)

                    (x, y, w, h) = isbn_barcode.rect
                    pt1_rect = (x, y)
                    pt2_rect = (x + w, y + h)

                    cv2.rectangle(
                        img=frame,
                        pt1=pt1_rect,
                        pt2=pt2_rect,
                        thickness=2,
                        color=(0, 0, 255),
                        lineType=cv2.LINE_8
                    )

                h, w, ch = frame.shape
                bytes_per_line = ch * w
                q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
                self.frame.emit(q_img)

                CameraWorker.msleep(30)
                
        except Exception as e:
            self.error.emit(f"Camera error: {str(e)}")
        finally:
            self.stop_camera()
            self.status.emit("Camera stopped")
            self.finished.emit()
    
    def stop_camera(self):
        if self.camera and self.is_camera_active:
            self.is_running = False
            self.camera.release()
            self.is_camera_active = False
            print("Camera stopped")
    
    def start_camera(self):
        if not self.is_running:
            self.start()
    
    def is_camera_running(self):
        return self.is_running and self.is_camera_active
