from threading import Thread
import time
import cv2

class CameraManager:
    def __init__(self,shared_data, resolution=(600, 500), camera_index=0):
        self.resolution = resolution
        self.camera_index = camera_index
        self.capture = None
        self.is_streaming = False
        self.thread = None
        self.shared_data =  shared_data

    def start_stream(self):
        if not self.is_streaming:
            self.capture = cv2.VideoCapture(self.camera_index)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            if not self.capture.isOpened():
                print("Error: No se pudo abrir la cámara")
                return False
            
            print(f"Cámara iniciada en {self.resolution[0]}x{self.resolution[1]}")
            self.is_streaming = True
            self.thread = Thread(target=self._stream)
            self.thread.daemon = True
            self.thread.start()
            return True
        return False
    def _stream(self):
        while self.is_streaming:
            ret, frame = self.capture.read()
            if ret:
                self.shared_data.set_data('current_frame', frame)
                center_x = self.resolution[0] // 2
                self.shared_data.set_data('center_x', center_x)
                time.sleep(0.03)
            else:
                print("Failed to read frame from camera")
                time.sleep(0.1)

    def stop_stream(self):
        if self.is_streaming:
            self.is_streaming = False
            if hasattr(self, 'thread') and self.thread.is_alive():
                self.thread.join(timeout=1.0)
            self.capture.release()