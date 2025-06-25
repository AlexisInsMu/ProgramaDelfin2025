import cv2 as cv  # Change this to match the import convention in your file
import numpy as np
from threading import Thread, Lock
import time
from src.utils.thread_safe_data import ThreadSafeData  # Changed from relative to absolute import


class LineDetector:
    def __init__(self):
        self.lower_hsv = np.array([40,40,30])
        self.upper_hsv = np.array([85,255,255])
        self.last_cx = None
        self.last_cy = None
        
    def detect_line(self, frame) -> tuple:
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        mask = cv.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Aplicar opening para eliminar ruido pequeño

        # Aplicar closing para cerrar pequeños huecos
        #mascara2 = cv.inRange(hsv, rojo_bajo2, rojo_alto2)
        #mascara_rojo = cv.bitwise_or(mascara1, mascara2)
        
        #image improvement
        kernel = np.ones((5,5), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
        mask = cv.GaussianBlur(mask, (5, 5), 0)
        contornos, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        
        # Process each contour
        for contorno in contornos:
            # Filter small contours
            area = cv.contourArea(contorno)
            if area > 500:
                # Filtrar por relación de aspecto
                x, y, w, h = cv.boundingRect(contorno)
                aspect_ratio = float(w)/h
    
            cv.drawContours(frame, [contorno], -1, (0, 255, 0), 2)
            
            # Calculate centroid
            M = cv.moments(contorno)
            # Y en el procesamiento de centroides:
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Suavizar movimientos con media ponderada
                if self.last_cx is not None:
                    # Aplica peso de 70% al valor actual y 30% al anterior
                    cx = int(0.7 * cx + 0.3 * self.last_cx)
                    cy = int(0.7 * cy + 0.3 * self.last_cy)
                
                self.last_cx = cx
                self.last_cy = cy

        return frame, mask, self.last_cx, self.last_cy
    
    
    
class QrDetector:
    def __init__(self):
        self.detector = cv.QRCodeDetector()
        
    def detect_qr(self, frame) -> tuple:
        retval, decoded_info, points, straight_qrcode = self.detector.detectAndDecodeMulti(frame)
        
        return retval, decoded_info, points, straight_qrcode
        

class ImageProcessor:
    def __init__(self, shared_data):
        self.line_detector = LineDetector()
        self.qr_detector = QrDetector()
        self.shared_data = shared_data
        self.running = False
        self.lock = Lock()
        self.frame = None
        self.processed_frame = None
        self.mask = None
        
    def start(self):
        self.running = True
        self.thread = Thread(target=self._processing_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def _processing_loop(self):
        while self.running:
            # Obtener frame de forma segura
            frame = self.shared_data.get_data('current_frame')
            if frame is not None:
                with self.lock:
                    # Detectar línea en el frame
                    processed, mask, cx, cy = self.line_detector.detect_line(frame.copy())
                    # Detectar aruco
                    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
                    parameters = cv.aruco.DetectorParameters()
                    detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
                    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
                    points = None
                    # Dibujar marcadores detectados si hay alguno
                    if ids is not None and len(ids) > 0:
                        #cv.aruco.drawDetectedMarkers(processed, corners, ids)
                        # Procesar los puntos de los marcadores
                        points = [corner[0] for corner in corners]
                        print(f"aruco code: {ids.flatten()}")
                        
                    # Compartir tanto los puntos como los IDs para que main.py pueda usarlos
                    self.shared_data.set_data('position_qr', points)
                    self.shared_data.set_data('aruco_ids', ids)
                        
                        
                            
                            
                    self.processed_frame = processed
                    self.mask = mask
                    
                    # Compartir el error con el controlador
                    self.shared_data.set_data('line_error', (cx, cy) if cx is not None and cy is not None else (None, None))
                    
            time.sleep(0.01)  # Control de velocidad
            
    def get_processed_image(self):
        with self.lock:
            if self.processed_frame is not None:
                return self.processed_frame.copy()
            return None
            
    def get_mask(self):
        with self.lock:
            if self.mask is not None:
                return self.mask.copy()
            return None
            
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)