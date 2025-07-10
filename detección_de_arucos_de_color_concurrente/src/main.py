import cv2
import time
import sys
import os
import numpy as np

# Configurar backend de OpenCV
os.environ['QT_QPA_PLATFORM'] = 'xcb'
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.thread_safe_data import ThreadSafeData
from src.camera.camera_manager import CameraManager
from src.camera.image_processor import ImageProcessor
from src.control.car_controller import CarController

# Configuración de ventanas
SHOW_WINDOWS = {
    'camera': True,
    'processed': True,
    'debug': True
}

def main():
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
    
    # Detectar si usar API nueva o antigua de ArUco
    try:
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_50)
        detector = cv2.aruco.ArucoDetector(aruco_dict)
        print("Usando API nueva de ArUco (OpenCV 4.7.0+)")
        use_new_aruco = True
    except AttributeError:
        print("Usando API antigua de ArUco (OpenCV 4.6.0 o anterior)")
        use_new_aruco = False
    
    # Crear objetos principales
    shared_data = ThreadSafeData()
    
    # Crear componentes
    camera_manager = CameraManager(shared_data, resolution=(600, 500))
    image_processor = ImageProcessor(shared_data, use_new_aruco_api=use_new_aruco)
    car_controller = CarController(shared_data, distance_sensor)  # Pasar distance_sensor aquí
    
    # Intentar iniciar la cámara
    if not camera_manager.start_stream():
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
    
    # Iniciar procesador de imágenes
    image_processor.start()
    
    # Iniciar controlador del carro
    car_controller.start()
    
    print("✓ Todos los componentes iniciados")
    print("Presiona 'q' para salir")
    
    # Crear y configurar ventanas una sola vez
    if show_gui:
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
            processed_frame = image_processor.get_processed_image()
            aruco_points = shared_data.get_data('position_qr', None)
            aruco_ids = shared_data.get_data('aruco_ids', None)
            aruco_center = shared_data.get_data('aruco_center', None)
            largest_area = shared_data.get_data('largest_aruco_area', 0)
            alto = shared_data.get_data('alto', False)
            position = shared_data.get_data('position', "Unknown")
            
            # Obtener datos del sensor de distancia
            if distance_sensor is not None:
                try:
                    distance_center = distance_sensor.get_distance_center()
                    obstacle_detected = distance_sensor.is_obstacle_detected(threshold=0.5)
                    closest_obstacle = distance_sensor.get_closest_obstacle()
                    
                    # Compartir datos de distancia
                    shared_data.set_data('distance_center', distance_center)
                    shared_data.set_data('obstacle_detected', obstacle_detected)
                    shared_data.set_data('closest_obstacle', closest_obstacle)
                except Exception as e:
                    print(f"Error obteniendo datos del sensor: {e}")
                    distance_center = 0.0
                    obstacle_detected = False
                    closest_obstacle = None
            else:
                distance_center = 0.0
                obstacle_detected = False
                closest_obstacle = None
            
            # Mostrar ventanas si GUI está disponible
            if show_gui:
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
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
                    cv2.imshow("Depuración", debug_frame)
                
                # Verificar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Guardar frame
                    timestamp = int(time.time())
                    if frame is not None:
                        cv2.imwrite(f'frame_{timestamp}.jpg', frame)
                        print(f"Frame guardado: frame_{timestamp}.jpg")
                elif key == ord('d'):
                    # Toggle debug info
                    SHOW_WINDOWS['debug'] = not SHOW_WINDOWS['debug']
                    if not SHOW_WINDOWS['debug']:
                        cv2.destroyWindow("Depuración")
                    print(f"Debug window: {'ON' if SHOW_WINDOWS['debug'] else 'OFF'}")
            else:
                # Modo headless - solo imprimir estado
                if aruco_points:
                    print(f"ArUcos detectados: {len(aruco_points)}")
                if distance_sensor is not None:
                    print(f"Distancia: {distance_center:.2f}m, Obstáculo: {obstacle_detected}")
                time.sleep(0.5)
                
            time.sleep(0.01)  # Pequeña pausa
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción por teclado")
    
    except Exception as e:
        print(f"❌ Error en bucle principal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🔄 Limpiando recursos...")
        
        # Detener componentes
        car_controller.stop()
        image_processor.stop()
        camera_manager.stop_stream()
        
        if distance_sensor is not None:
            distance_sensor.stop_streaming()
        
        # Cerrar ventanas
        if show_gui:
            cv2.destroyAllWindows()
        
        print("✓ Programa terminado correctamente")

if __name__ == "__main__":
    main()