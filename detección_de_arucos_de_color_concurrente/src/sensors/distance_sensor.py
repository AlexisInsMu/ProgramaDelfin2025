import numpy as np
import threading
import time
import sys
import os

class DistanceSensor:
    def __init__(self, width=640, height=480, fps=30):
        """
        Wrapper Python para el sensor de distancia C++ RealSense
        """
        self.width = width
        self.height = height
        self.fps = fps
        
        # Importar módulo C++
        try:
            # Agregar el directorio del módulo C++ al path
            current_dir = os.path.dirname(__file__)
            cpp_module_path = os.path.join(current_dir, 'realsense_cpp')
            if cpp_module_path not in sys.path:
                sys.path.insert(0, cpp_module_path)
            
            # Importar el módulo C++
            import realsense_cpp
            self.sensor = realsense_cpp.RealSenseDistanceSensor(width, height, fps)
            print("✓ Sensor C++ RealSense inicializado")
        except ImportError as e:
            print(f"❌ Error importando módulo C++: {e}")
            print("Ruta actual:", os.path.dirname(__file__))
            print("Archivos disponibles:", os.listdir(os.path.join(os.path.dirname(__file__), 'realsense_cpp')))
            raise
        
        # Variables para compatibilidad
        self.is_streaming = False
        self.lock = threading.Lock()
        
    def start_streaming(self):
        """Iniciar el streaming del sensor"""
        try:
            result = self.sensor.start_streaming()
            self.is_streaming = result
            return result
        except Exception as e:
            print(f"❌ Error iniciando streaming: {e}")
            return False
    
    def get_distance(self, x=None, y=None, region_size=20):
        """Obtener distancia en un punto específico"""
        if not self.is_streaming:
            return 0.0
        
        try:
            if x is None or y is None:
                return self.sensor.get_distance_center()
            else:
                return self.sensor.get_distance(x, y, region_size)
        except Exception as e:
            print(f"Error obteniendo distancia: {e}")
            return 0.0
    
    def get_distance_center(self):
        """Obtener distancia en el centro"""
        return self.get_distance()
    
    def is_obstacle_detected(self, threshold=0.3, x=None, y=None):
        """Detectar obstáculo"""
        if not self.is_streaming:
            return False
        
        try:
            if x is None or y is None:
                return self.sensor.is_obstacle_detected(threshold)
            else:
                return self.sensor.is_obstacle_detected(threshold, x, y)
        except Exception as e:
            print(f"Error detectando obstáculo: {e}")
            return False
    
    def get_closest_obstacle(self, min_distance=0.1, max_distance=2.0):
        """Obtener obstáculo más cercano"""
        if not self.is_streaming:
            return None
        
        try:
            distance, x, y = self.sensor.get_closest_obstacle(min_distance, max_distance)
            if distance > 0:
                return (distance, x, y)
            return None
        except Exception as e:
            print(f"Error obteniendo obstáculo más cercano: {e}")
            return None
    
    def get_distance_array(self):
        """Obtener array de distancias"""
        if not self.is_streaming:
            return None
        
        try:
            return self.sensor.get_distance_array()
        except Exception as e:
            print(f"Error obteniendo array de distancias: {e}")
            return None
    
    def get_obstacles_in_path(self, path_width=100, max_distance=1.0):
        """Compatibilidad: detectar obstáculos en el camino"""
        depth_array = self.get_distance_array()
        if depth_array is None:
            return []
        
        # Lógica similar a la versión Python original
        center_x = self.width // 2
        x_start = max(0, center_x - path_width // 2)
        x_end = min(self.width, center_x + path_width // 2)
        
        path_region = depth_array[:, x_start:x_end]
        valid_mask = (path_region > 0.1) & (path_region < max_distance)
        
        obstacles = []
        if np.any(valid_mask):
            y_indices, x_indices = np.where(valid_mask)
            for y, x in zip(y_indices, x_indices):
                actual_x = x + x_start
                distance = path_region[y, x]
                obstacles.append((distance, actual_x, y))
        
        obstacles.sort(key=lambda obs: obs[0])
        return obstacles
    
    def get_current_depth_image(self, colormap=True):
        """Obtener imagen de profundidad con mapa de colores"""
        if not self.is_streaming:
            return None
        
        try:
            # Obtener array de profundidad
            depth_array = self.get_distance_array()
            if depth_array is None:
                return None
                
            # Normalizar para visualización
            import cv2
            import numpy as np
            
            # Filtrar valores no válidos (0) para no afectar normalización
            valid_mask = depth_array > 0.001
            
            if np.any(valid_mask):
                # Normalizar solo valores válidos
                min_val = np.min(depth_array[valid_mask])
                max_val = np.max(depth_array[valid_mask])
                
                # Crear imagen normalizada de 8 bits (0-255)
                normalized = np.zeros_like(depth_array, dtype=np.uint8)
                if max_val > min_val:
                    normalized[valid_mask] = 255 * ((depth_array[valid_mask] - min_val) / (max_val - min_val))
                
                # Aplicar mapa de colores
                if colormap:
                    # Opciones de mapas de colores:
                    # - cv2.COLORMAP_JET: azul a rojo (popular para profundidad)
                    # - cv2.COLORMAP_INFERNO: negro a amarillo
                    # - cv2.COLORMAP_TURBO: azul a rojo (más suave)
                    # - cv2.COLORMAP_RAINBOW: violeta a rojo
                    depth_colormap = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
                    return depth_colormap
                else:
                    return normalized
                
        except Exception as e:
            print(f"Error procesando imagen de profundidad: {e}")

        return None
    
    def get_rgb_image(self):
        """Obtener la imagen RGB actual"""
        if not self.is_streaming:
            return None

        try:
            rgb_array = self.sensor.get_image_rgb()
            if rgb_array is not None and rgb_array.size > 0:
                return rgb_array
        except Exception as e:
            print(f"Error obteniendo imagen RGB: {e}")

        return None
    
    def stop_streaming(self):
        """Detener streaming"""
        if self.is_streaming:
            try:
                self.sensor.stop_streaming()
                self.is_streaming = False
                print("✓ Streaming C++ detenido")
            except Exception as e:
                print(f"Error deteniendo streaming: {e}")
    
    def __del__(self):
        """Destructor"""
        if self.is_streaming:
            self.stop_streaming()