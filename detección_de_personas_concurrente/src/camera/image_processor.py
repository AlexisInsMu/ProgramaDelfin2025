import cv2 as cv  # Change this to match the import convention in your file
import numpy as np
import mediapipe as mp
from threading import Thread, Lock
import time
# Changed from relative to absolute import
from src.utils.thread_safe_data import ThreadSafeData

import cv2
import mediapipe as mp
import numpy as np
from threading import Lock


class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Menor complejidad para RPi
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.lock = Lock()

    def detect_pose(self, image):
        """Detectar pose en la imagen"""
        with self.lock:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_image)
            return results

    def get_centroid(self, results, image_shape):
        """Obtener centroide del convex hull de los puntos visibles del torso"""
        if results.pose_landmarks:
            # CORREGIDO: usar height, width = image_shape[:2]
            height, width = image_shape[:2]
            landmarks = results.pose_landmarks.landmark
            torso_indices = [
                mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
                mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
                mp.solutions.pose.PoseLandmark.LEFT_HIP,
                mp.solutions.pose.PoseLandmark.RIGHT_HIP
            ]
            points = []
            for i in torso_indices:
                lm = landmarks[i]
                if lm.visibility > 0.7:
                    x = int(lm.x * width)
                    y = int(lm.y * height)
                    points.append([x, y])
            if len(points) >= 3:
                points_np = np.array(points)
                hull = cv2.convexHull(points_np)
                M = cv2.moments(hull)
                if M["m00"] != 0:
                    centroid_x = int(M["m10"] / M["m00"])
                    centroid_y = int(M["m01"] / M["m00"])
                    return (centroid_x, centroid_y)
        return None

    def draw_pose(self, image, results):
        """Dibujar pose en la imagen"""
        if results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_draw.DrawingSpec(
                    color=(0, 255, 0), thickness=2, circle_radius=2),
                self.mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2)
            )
        return image

    def get_pose_confidence(self, results):
        """Obtener confianza promedio de la pose"""
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            visibilities = [lm.visibility for lm in landmarks]
            return sum(visibilities) / len(visibilities)
        return 0.0


class Aruco_Detector:
    def __init__(self):
        # Detectar automáticamente qué API de ArUco usar
        try:
            # Intentar API nueva (OpenCV 4.7+)
            self.aruco_dict = cv.aruco.getPredefinedDictionary(
                cv.aruco.DICT_5X5_50)
            self.parameters = cv.aruco.DetectorParameters()
            self.detector = cv.aruco.ArucoDetector(
                self.aruco_dict, self.parameters)
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
            corners, ids, _ = cv.aruco.detectMarkers(
                gray, self.aruco_dict, parameters=self.parameters)

        return corners, ids


class ImageProcessor:
    def __init__(self, shared_data):
        self.aruco_detector = Aruco_Detector()
        self.pose_detector = PoseDetector()
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

                    results = self.pose_detector.detect_pose(frame)
                    pose_center = self.pose_detector.get_centroid(
                        results, frame.shape)

                    # Dibujar pose en la imagen procesada
                    if results.pose_landmarks:
                        self.processed_frame = self.pose_detector.draw_pose(
                            self.processed_frame, results)

                    # Mandar datos del centroide de la pose
                    if pose_center:
                        self.shared_data.set_data('pose_center', pose_center)
                        self.shared_data.set_data(
                            'pose_confidence', self.pose_detector.get_pose_confidence(results))
                        distance_center = self.shared_data.get_data('distance_center', 0.0)
                        if distance_center < 1.1:
                            self.shared_data.set_data('alto', True)
                        else:
                            self.shared_data.set_data('alto', False)
                        alto = self.shared_data.get_data('alto', False)
                        
                        
                    else:
                        self.shared_data.set_data('pose_center', None)
                        self.shared_data.set_data('pose_confidence', 0.0)

            time.sleep(0.01)
    def get_processed_image(self):
        with self.lock:
            return self.processed_frame.copy() if self.processed_frame is not None else None

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
