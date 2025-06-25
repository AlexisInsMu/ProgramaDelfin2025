import cv2
import time
import sys
import os
# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.thread_safe_data import ThreadSafeData
from src.camera.camera_manager import CameraManager
from src.camera.image_processor import ImageProcessor
from src.control.car_controller import CarController
import numpy as np

SHOW_WINDOWS ={
    'camera': True,       # Imagen original de la cámara
    'processed': True,    # Imagen procesada con visualizaciones
    'mask': True,        # Máscara binaria utilizada para detección
    'debug': True         # Información adicional de depuración
}

def main():
    # Objeto para compartir datos entre hilos
    shared_data = ThreadSafeData()
    
    # Inicializar componentes
    camera = CameraManager(shared_data, resolution=(600, 500))
    processor = ImageProcessor(shared_data)
    controller = CarController(shared_data)
    
    # Iniciar todos los hilos
    if not camera.start_stream():
        print("Error al iniciar la cámara. Abortando.")
        return
        
    processor.start()
    controller.start()
    
    print("Sistema iniciado - Presione 'q' para salir")
     #Crear y configurar ventanas una sola vez
    if SHOW_WINDOWS['camera']:
        cv2.namedWindow("Cámara", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['processed']:
        cv2.namedWindow("Seguimiento de Línea", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['mask']:
        cv2.namedWindow("Máscara", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['debug']:
        cv2.namedWindow("Depuración", cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # Obtener imágenes procesadas para visualización
            frame = shared_data.get_data('current_frame')
            processed_frame = processor.get_processed_image()
            mask = processor.get_mask()
            
            # MOSTRAR las imágenes (esto falta en tu código)
            if SHOW_WINDOWS['camera'] and frame is not None:
                cv2.imshow("Cámara", frame)
            
            if SHOW_WINDOWS['processed'] and processed_frame is not None:
                cv2.imshow("Seguimiento de Línea", processed_frame)
            
            if SHOW_WINDOWS['mask'] and mask is not None:
                cv2.imshow("Máscara", mask)
                
            if SHOW_WINDOWS['debug'] and processed_frame is not None:
                # Obtener datos para visualización
                position = shared_data.get_data('position', "Unknown")
                color = shared_data.get_data('color', (255, 255, 255))
                cx, cy = shared_data.get_data('line_error', (None, None))
                
                # Obtener datos de ArUco
                aruco_points = shared_data.get_data('position_qr', None)
                aruco_ids = shared_data.get_data('aruco_ids', None)
                
                # Crear una copia del frame procesado para dibujar información de depuración
                debug_frame = processed_frame.copy()
                
                # Dibujar información de seguimiento de línea
                area =None
                if cx is not None and cy is not None:
                    cv2.putText(debug_frame, position, (cx-20, cy-20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.circle(debug_frame, (cx, cy), 5, color, -1)
                
                # Dibujar información de ArUcos detectados
                if aruco_points is not None and len(aruco_points) > 0:
                    # Dibujar un texto indicando cuántos ArUcos se detectados
                    num_arucos = len(aruco_points)
                    cv2.putText(debug_frame, f"ArUcos: {num_arucos}", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Dibujar los marcos de los ArUcos
                    for i, points in enumerate(aruco_points):
                        # Convertir puntos a formato de numpy para dibujar polígono
                        marker_points = np.array(points, dtype=np.int32)
                        
                        # Dibujar el contorno del marcador
                        cv2.polylines(debug_frame, [marker_points], True, (0, 255, 0), 2)
                        
                        # Dibujar las esquinas del marcador
                        for j, corner in enumerate(points):
                            corner_x, corner_y = int(corner[0]), int(corner[1])
                            cv2.circle(debug_frame, (corner_x, corner_y), 4, (255, 0, 255), -1)
                            # Opcional: mostrar número de esquina
                            cv2.putText(debug_frame, str(j), (corner_x + 5, corner_y + 5),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
                        
                        # Calcular el centro del marcador
                        center_x = int(np.mean([p[0] for p in points]))
                        center_y = int(np.mean([p[1] for p in points]))
                        
                        area = cv2.contourArea(marker_points)
                        # Dibujar el centro del marcador
                        cv2.circle(debug_frame, (center_x, center_y), 5, (0, 0, 255), -1)
                        print(f"ArUco ID {i}: Área = {area}")
                        
                        if(area > float(500*600)/float(7)):
                            shared_data.set_data('alto', "True")
                        else:
                            shared_data.set_data('alto', "False")
                        
                        # Mostrar el ID del marcador si está disponible
                        if aruco_ids is not None and i < len(aruco_ids):
                            marker_id = aruco_ids[i][0]
                            cv2.putText(debug_frame, f"ID: {marker_id}", (center_x + 10, center_y), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                else:
                    if aruco_ids is not None:
                        shared_data.set_data('position_qr', None)
                        shared_data.set_data('aruco_ids', None)
                        shared_data.set_data('alto', "False")
                    cv2.putText(debug_frame, "No ArUcos", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Mostrar el frame de depuración
                cv2.imshow("Depuración", debug_frame)
                
                
        
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Control de velocidad del bucle principal
            time.sleep(0.03)
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    finally:
        # Detener componentes en orden inverso
        controller.stop()
        processor.stop()
        camera.stop_stream()
        cv2.destroyAllWindows()
        print("Sistema detenido correctamente")

if __name__ == "__main__":
    main()