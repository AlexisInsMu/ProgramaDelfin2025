import cv2
import time
import sys
import os

# Configurar backend de OpenCV para evitar problemas con Qt y OpenGL
import os
#se puede comentar ya que solo funcionaba para permitir pantalla compartida por ssh con windows
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.thread_safe_data import ThreadSafeData
from src.camera.camera_manager import CameraManager
from src.camera.image_processor import ImageProcessor
from src.control.car_controller import CarController
import numpy as np

#interruptores para activar ventanas de visualización

SHOW_WINDOWS ={
    'camera': True,       # Imagen original de la cámara
    'processed': True,    # Imagen procesada con visualizaciones
    'debug': True,         # Información adicional de depuración
    'depth': True          # Imagen de profundidad
}

def main():
    # Objeto para compartir datos entre hilos
    shared_data = ThreadSafeData()
    print("=== Iniciando Programa Delfín 2025 ===")
    
    # Inicializar variable distance_sensor DENTRO de main()
    distance_sensor = None
    
    # Importar DistanceSensor con manejo de errores
    try:
        from src.sensors.distance_sensor import DistanceSensor
        print("✓ DistanceSensor importado correctamente")
        
        # Probar crear instancia
        distance_sensor = DistanceSensor()
        print("✓ DistanceSensor creado correctamente")
    except ImportError as e:
        print(f"❌ Error importando DistanceSensor: {e}")
        print("Continuando sin sensor de distancia")
        distance_sensor = None
    #solo activar si se esta usando la libreria de pyrealsense2
    # except AttributeError as e:
    #     print(f"❌ Error de atributo en pyrealsense2: {e}")
    #     print("Verificar configuración de variables de entorno")
    #     print("Continuando sin sensor de distancia")
    #     distance_sensor = None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("Continuando sin sensor de distancia")
        distance_sensor = None
    
    # Verificar si hay GUI disponible
    try:
        cv2.namedWindow('test', cv2.WINDOW_AUTOSIZE)
        cv2.destroyWindow('test')
        print("GUI disponible - Mostrando ventanas")
        show_gui = True
    except:
        print("GUI NO disponible - Modo headless")
        show_gui = False
        # Desactivar todas las ventanas si no hay GUI
        for key in SHOW_WINDOWS:
            SHOW_WINDOWS[key] = False
    
    # Verificar versión de OpenCV y ArUco
    print(f"OpenCV versión: {cv2.__version__}")
    
    # Inicializar componentes
    camera = CameraManager(shared_data, resolution=(600, 500))
    processor = ImageProcessor(shared_data)
    controller = CarController(shared_data, distance_sensor)
    
    # Iniciar todos los hilos
    if not camera.start_stream():
        print("Error al iniciar la cámara. Abortando.")
        return
    # Iniciar sensor de distancia si está disponible
    if distance_sensor is not None:
        try:
            if distance_sensor.start_streaming():
                print("✓ Sensor de distancia iniciado")
            else:
                print("⚠️ Error al iniciar sensor de distancia. Continuando sin él.")
                distance_sensor = None
        except Exception as e:
            print(f"⚠️ Error en start_streaming: {e}")
            distance_sensor = None
    else:
        print("⚠️ Sensor de distancia no disponible")
        
    processor.start()
    controller.start()
    
    print(" Todos los componentes iniciados")
    print("Presiona 'q' para salir")
     #Crear y configurar ventanas una sola vez
    if SHOW_WINDOWS['camera']:
        cv2.namedWindow("Cámara", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['processed']:
        cv2.namedWindow("ArUcos Detectados", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['debug']:
        cv2.namedWindow("Depuración", cv2.WINDOW_NORMAL)
    if SHOW_WINDOWS['depth']:
        cv2.namedWindow("Imagen de Profundidad", cv2.WINDOW_NORMAL)
    
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
            pose_center = shared_data.get_data('pose_center', None)
            pose_confidence = shared_data.get_data('pose_confidence', 0.0)
            
            
            if distance_sensor is not None:
                try:
                    distance_center = distance_sensor.get_distance_center()
                    obstacle_detected = distance_sensor.is_obstacle_detected(threshold=0.5)
                    closest_obstacle = distance_sensor.get_closest_obstacle()
                    frame_depth = distance_sensor.get_current_depth_image()
                    rgb_image = distance_sensor.get_rgb_image()
                    
                    # Compartir datos de distancia
                    shared_data.set_data('init_realsense', True)
                    shared_data.set_data('distance_center', distance_center)
                    shared_data.set_data('obstacle_detected', obstacle_detected)
                    shared_data.set_data('closest_obstacle', closest_obstacle)
                    #shared_data.set_data('frame_depth', frame_depth)
                    shared_data.set_data('frame_rgb', rgb_image)
                except Exception as e:
                    print(f"Error obteniendo datos del sensor: {e}")
                    distance_center = 0.0
                    obstacle_detected = False
                    closest_obstacle = None
                    frame_depth = None
                    rgb_image = None
                    shared_data.set_data('init_realsense', False)
            else:
                distance_center = 0.0
                obstacle_detected = False
                closest_obstacle = None
                frame_depth = None
                rgb_image = None
                shared_data.set_data('init_realsense', False)
            # Mostrar ventanas
            if SHOW_WINDOWS['camera'] and frame is not None:
                cv2.imshow("Cámara", frame)
            
            if SHOW_WINDOWS['processed'] and processed_frame is not None:
                cv2.imshow("ArUcos Detectados", processed_frame)
                
            if SHOW_WINDOWS['debug'] and processed_frame is not None:
                debug_frame = processed_frame.copy()
                
                # Mostrar información de la persona detectada con MediaPipe
                if pose_center is not None:
                    cv2.circle(debug_frame, pose_center, 10, (255, 0, 0), -1)
                    cv2.putText(debug_frame, f"Persona: {pose_center} Conf: {pose_confidence:.2f}", 
                                (pose_center[0] + 15, pose_center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                
                # Mostrar información de distancia
                if distance_sensor is not None:
                    y_offset = 150
                    cv2.putText(debug_frame, f"Distancia Centro: {distance_center:.2f}m", (10, y_offset), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                    
                    obstacle_color = (0, 0, 255) if obstacle_detected else (0, 255, 0)
                    obstacle_text = "OBSTACULO!" if obstacle_detected else "Camino libre"
                    cv2.putText(debug_frame, obstacle_text, (10, y_offset + 25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, obstacle_color, 2)
                    
                    if closest_obstacle:
                        dist, x, y = closest_obstacle
                        cv2.putText(debug_frame, f"Mas cercano: {dist:.2f}m", (10, y_offset + 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
                else:
                    cv2.putText(debug_frame, "Sensor distancia: No disponible", (10, 150), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 2)
                
                # Mostrar posición del control
                cv2.putText(debug_frame, f"Control: {position}", (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
                if alto is not None and pose_center is not None:
                    alto_text = "Alto persona cerca" if alto else "persona lejos"
                    cv2.putText(debug_frame, f"Alto: {alto_text}", (10, 140), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                cv2.imshow("Depuración", debug_frame)
                
                                
                if SHOW_WINDOWS['depth'] and distance_sensor is not None:
                    if rgb_image is not None:
                        cv2.imshow("Imagen RGB", rgb_image)
                    if frame_depth is not None:
                        cv2.imshow("Imagen de Profundidad", frame_depth)
            
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