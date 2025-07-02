import cv2 as cv  # Change this to match the import convention in your file
import numpy as np
from threading import Thread, Lock
import time
from src.utils.thread_safe_data import ThreadSafeData  # Changed from relative to absolute import    
    
class Aruco_Detector:
    def __init__(self):
        # Detectar automáticamente qué API de ArUco usar
        try:
            # Intentar API nueva (OpenCV 4.7+)
            self.aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
            self.parameters = cv.aruco.DetectorParameters()
            self.detector = cv.aruco.ArucoDetector(self.aruco_dict, self.parameters)
            self.use_new_api = True
            print("Usando API nueva de ArUco (OpenCV 4.7+)")
        except AttributeError:
            # Usar API antigua (OpenCV 4.6.0 y anteriores)
            self.aruco_dict = cv.aruco.Dictionary_get(cv.aruco.DICT_5X5_50)
            self.parameters = cv.aruco.DetectorParameters_create()
            self.use_new_api = False
            print("Usando API antigua de ArUco (OpenCV 4.6.0 o anterior)")
        
    def detect_aruco(self, frame):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        if self.use_new_api:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
            
        return corners, ids
        
        
class ImageProcessor:
    def __init__(self, shared_data):
        self.aruco_detector = Aruco_Detector()
        self.shared_data = shared_data
        self.running = False
        self.lock = Lock()
        self.processed_frame = None
        
    def start(self):
        self.running = True
        self.thread = Thread(target=self._processing_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def _processing_loop(self):
        while self.running:
            frame = self.shared_data.get_data('current_frame')
            if frame is not None:
                with self.lock:
                    # Usar el frame original como base para el procesado
                    self.processed_frame = frame.copy()
                    
                    # Detectar ArUcos
                    corners, ids = self.aruco_detector.detect_aruco(frame)
                    
                    # Procesar datos de ArUco
                    aruco_points = []
                    aruco_center = None
                    largest_area = 0
                    alto = False
                    
                    if ids is not None and len(ids) > 0:
                        # Dibujar marcadores ArUco en la imagen procesada
                        cv.aruco.drawDetectedMarkers(self.processed_frame, corners, ids)
                        
                        # Procesar cada marcador detectado
                        for i, corner in enumerate(corners):
                            corner_points = corner.reshape((4, 2))
                            aruco_points.append(corner_points.tolist())
                            
                            # Calcular centro del ArUco
                            center_x = int(np.mean(corner_points[:, 0]))
                            center_y = int(np.mean(corner_points[:, 1]))
                            
                            # Calcular área del ArUco
                            area = cv.contourArea(corner_points.astype(np.int32))
                            
                            # Usar el ArUco más grande para control
                            if area > largest_area:
                                largest_area = area
                                aruco_center = (center_x, center_y)
                                
                                # Determinar si el ArUco es lo suficientemente grande para detenerse
                                image_area = frame.shape[0] * frame.shape[1]  # 500 * 600
                                if area > image_area / 5:  # Mayor a 1/5 del área de imagen
                                    alto = True
                    
                    # Guardar datos compartidos
                    self.shared_data.set_data('aruco_corners', corners)
                    self.shared_data.set_data('aruco_ids', ids)
                    self.shared_data.set_data('position_qr', aruco_points if aruco_points else None)
                    self.shared_data.set_data('aruco_center', aruco_center)
                    self.shared_data.set_data('largest_aruco_area', largest_area)
                    self.shared_data.set_data('alto', alto)
                    
            time.sleep(0.01)
            
    def get_processed_image(self):
        with self.lock:
            return self.processed_frame.copy() if self.processed_frame is not None else None
            
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)