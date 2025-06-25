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
    camera = CameraManager(shared_data, resolution=(320, 240))
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
                position = shared_data.get_data('position', "Unknown")
                color = shared_data.get_data('color', (255, 255, 255))
                debug_info = f"Posición: {position}, Color: {color}"
                cx, cy = shared_data.get_data('line_error', (None, None))
                position1 = shared_data.get_data('position_qr', "Unknown")
                if cx is not None and cy is not None:
                    if position1 is not None and len(position1) > 0:
                        centralx = 0
                        centraly = 0
                        area = 0
                        
                        for i in range(len(position1)):
                            if position1[i] is not None:
                                # Asegurarse de que estamos trabajando con escalares
                                x_i = float(position1[i][0]) if isinstance(position1[i][0], (int, float, np.number)) else 0
                                y_i = float(position1[i][1]) if isinstance(position1[i][1], (int, float, np.number)) else 0
                                
                                if i == 0 and len(position1) > 1:
                                    x_prev = float(position1[-1][0]) if isinstance(position1[-1][0], (int, float, np.number)) else 0
                                    y_prev = float(position1[-1][1]) if isinstance(position1[-1][1], (int, float, np.number)) else 0
                                    
                                    product_point = x_i * x_prev - y_i * y_prev
                                    area += (x_i + x_prev) * (y_i + y_prev)
                                    centralx += (x_i + x_prev) * product_point
                                    centraly += (y_i + y_prev) * product_point
                                elif i > 0:
                                    x_prev = float(position1[i-1][0]) if isinstance(position1[i-1][0], (int, float, np.number)) else 0
                                    y_prev = float(position1[i-1][1]) if isinstance(position1[i-1][1], (int, float, np.number)) else 0
                                    
                                    product_point = x_i * x_prev - y_i * y_prev
                                    area += (x_i + x_prev) * (y_i + y_prev)
                                    centralx += (x_i + x_prev) * product_point
                                    centraly += (y_i + y_prev) * product_point      
                            if area != 0:
                                centralx = int(centralx/(3*area))
                                centraly = int(centraly/(3*area))
                            else:
                                centralx = 0
                                centraly = 0
                            cv2.circle(processed_frame, (centralx, centraly), 5, color, -1)
                            
                    cv2.putText(processed_frame, position, (cx-20, cy-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.imshow("Depuración", processed_frame)
                
                
        
            
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