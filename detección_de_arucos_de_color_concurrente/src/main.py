import cv2
import time
import sys
import os

# Configurar backend de OpenCV para evitar problemas con Qt y OpenGL
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'

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
    'debug': True         # Información adicional de depuración
}

def main():
    # Objeto para compartir datos entre hilos
    shared_data = ThreadSafeData()
    
    # Verificar si podemos usar ventanas GUI
    try:
        # Intentar crear una ventana de prueba
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imshow("Test", test_img)
        cv2.waitKey(1)
        cv2.destroyWindow("Test")
        print("GUI disponible - Mostrando ventanas")
        gui_available = True
    except:
        print("GUI no disponible - Ejecutando sin ventanas")
        gui_available = False
        # Desactivar todas las ventanas si GUI no está disponible
        for key in SHOW_WINDOWS:
            SHOW_WINDOWS[key] = False
    
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
        cv2.namedWindow("ArUcos Detectados", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['debug']:
        cv2.namedWindow("Depuración", cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # Obtener datos
            frame = shared_data.get_data('current_frame')
            processed_frame = processor.get_processed_image()
            aruco_points = shared_data.get_data('position_qr', None)
            aruco_ids = shared_data.get_data('aruco_ids', None)
            aruco_center = shared_data.get_data('aruco_center', None)
            largest_area = shared_data.get_data('largest_aruco_area', 0)
            alto = shared_data.get_data('alto', False)
            position = shared_data.get_data('position', "Unknown")
            
            # Mostrar ventanas
            if SHOW_WINDOWS['camera'] and frame is not None:
                cv2.imshow("Cámara", frame)
            
            if SHOW_WINDOWS['processed'] and processed_frame is not None:
                cv2.imshow("ArUcos Detectados", processed_frame)
                
            if SHOW_WINDOWS['debug'] and processed_frame is not None:
                debug_frame = processed_frame.copy()
                
                # Información de ArUcos
                if aruco_points is not None and len(aruco_points) > 0:
                    num_arucos = len(aruco_points)
                    cv2.putText(debug_frame, f"ArUcos: {num_arucos}", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Dibujar centro del ArUco más grande
                    if aruco_center is not None:
                        center_x, center_y = aruco_center
                        cv2.circle(debug_frame, (center_x, center_y), 10, (0, 0, 255), -1)
                        cv2.putText(debug_frame, f"Centro: ({center_x}, {center_y})", 
                                    (center_x + 15, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    
                    # Mostrar área del ArUco más grande
                    cv2.putText(debug_frame, f"Area Max: {largest_area:.0f}", (10, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    
                    # Estado del sistema
                    status_color = (0, 0, 255) if alto else (0, 255, 0)
                    status_text = "ALTO - ArUco Grande" if alto else "SIGUIENDO"
                    cv2.putText(debug_frame, status_text, (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                else:
                    cv2.putText(debug_frame, "No ArUcos detectados", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Mostrar posición del control
                cv2.putText(debug_frame, f"Control: {position}", (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                cv2.imshow("Depuración", debug_frame)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
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