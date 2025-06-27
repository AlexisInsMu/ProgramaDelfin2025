import cv2 as cv
import numpy as np
import time
import sys
import os

# Añadir el directorio raíz del proyecto al path para poder importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'raspberry-pi-car')))

from src.utils.thread_safe_data import ThreadSafeData

def aruco_detection_diagnostic():
    """
    Script para diagnosticar la transmisión de datos de ArUco entre componentes.
    """
    print(f"OpenCV Version: {cv.__version__}")
    
    # Inicializar estructura de datos compartidos
    shared_data = ThreadSafeData()
    
    # Inicializar cámara
    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    print("Iniciando diagnóstico de detección de ArUco...")
    print("Presiona 'q' para salir, 'c' para capturar una imagen")
    
    # Crear ventanas
    cv.namedWindow("Original", cv.WINDOW_NORMAL)
    cv.namedWindow("Procesado", cv.WINDOW_NORMAL)
    cv.namedWindow("Datos Compartidos", cv.WINDOW_NORMAL)
    
    while True:
        # Capturar frame
        ret, frame = cap.read()
        if not ret:
            print("Error al leer frame")
            break
        
        # Guardar en datos compartidos como lo haría CameraManager
        shared_data.set_data('current_frame', frame)
        
        # Detectar ArUco como lo haría ImageProcessor
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
        parameters = cv.aruco.DetectorParameters_create()
        corners, ids, rejected = cv.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        
        # Crear imagen procesada
        processed = frame.copy()
        
        # Dibujar marcadores detectados
        if ids is not None and len(ids) > 0:
            cv.aruco.drawDetectedMarkers(processed, corners, ids)
            points = [corner[0] for corner in corners]
            print(f"ArUco detectado: IDs {ids.flatten()}")
            
            # Almacenar en datos compartidos como lo haría ImageProcessor
            shared_data.set_data('position_qr', points)
            shared_data.set_data('aruco_ids', ids)
        else:
            # Limpiar datos compartidos si no hay detecciones
            shared_data.set_data('position_qr', None)
            shared_data.set_data('aruco_ids', None)
            print("No se detectaron ArUcos")
        
        # Mostrar imagen original
        cv.imshow("Original", frame)
        
        # Mostrar imagen procesada
        cv.imshow("Procesado", processed)
        
        # Simular main.py leyendo los datos compartidos
        data_visualization = np.zeros((300, 500, 3), dtype=np.uint8)
        
        # Leer datos como lo haría main.py
        aruco_points = shared_data.get_data('position_qr', None)
        aruco_ids = shared_data.get_data('aruco_ids', None)
        
        # Mostrar información obtenida
        if aruco_points is not None and aruco_ids is not None:
            cv.putText(data_visualization, f"ArUcos detectados: {len(aruco_ids)}", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            for i, marker_id in enumerate(aruco_ids):
                cv.putText(data_visualization, f"ID {marker_id[0]}: encontrado", (10, 60 + i*30), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv.putText(data_visualization, "No se detectaron ArUcos", (10, 30), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Mostrar visualización de datos compartidos
        cv.imshow("Datos Compartidos", data_visualization)
        
        # Control de teclado
        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            # Capturar imagen para análisis
            timestamp = int(time.time())
            cv.imwrite(f"diagnostico_original_{timestamp}.jpg", frame)
            cv.imwrite(f"diagnostico_procesado_{timestamp}.jpg", processed)
            cv.imwrite(f"diagnostico_datos_{timestamp}.jpg", data_visualization)
            print(f"Imágenes de diagnóstico guardadas con timestamp {timestamp}")
        
        # Pequeña pausa
        time.sleep(0.01)
    
    # Liberar recursos
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    aruco_detection_diagnostic()
