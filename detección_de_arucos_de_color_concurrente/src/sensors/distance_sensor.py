import pyrealsense2 as rs
import numpy as np
import threading
import time

class DistanceSensor:
    def __init__(self, width=640, height=480, fps=30):
        """
        Inicializar el sensor de distancia usando Intel RealSense D455
        
        Args:
            width: Ancho de la imagen de profundidad
            height: Alto de la imagen de profundidad  
            fps: Frames por segundo
        """
        self.width = width
        self.height = height
        self.fps = fps
        
        # Pipeline y configuración de RealSense
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # Configurar stream de profundidad
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        
        # Variables para almacenar datos
        self.current_depth_frame = None
        self.lock = threading.Lock()
        self.is_streaming = False
        
        # Filtros para mejorar la calidad de profundidad
        self.spatial_filter = rs.spatial_filter()
        self.temporal_filter = rs.temporal_filter()
        self.hole_filling_filter = rs.hole_filling_filter()
        
        # Configuración de filtros
        self.spatial_filter.set_option(rs.option.filter_magnitude, 2)
        self.spatial_filter.set_option(rs.option.filter_smooth_alpha, 0.5)
        self.spatial_filter.set_option(rs.option.filter_smooth_delta, 20)
        
        print("✓ RealSense D455 Distance Sensor inicializado")

    def start_streaming(self):
        """Iniciar el streaming del sensor de profundidad"""
        try:
            # Verificar que hay dispositivos conectados
            ctx = rs.context()
            devices = ctx.query_devices()
            if len(devices) == 0:
                print("❌ No se encontraron dispositivos RealSense")
                return False
            
            # Iniciar pipeline
            profile = self.pipeline.start(self.config)
            
            # Obtener información del sensor de profundidad
            depth_sensor = profile.get_device().first_depth_sensor()
            depth_scale = depth_sensor.get_depth_scale()
            print(f"✓ Depth Scale: {depth_scale}")
            
            self.is_streaming = True
            
            # Hilo para capturar frames continuamente
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            print("✓ RealSense streaming iniciado")
            return True
            
        except Exception as e:
            print(f"❌ Error al iniciar RealSense: {e}")
            return False

    def _capture_loop(self):
        """Loop para capturar frames de profundidad continuamente"""
        while self.is_streaming:
            try:
                # Esperar por frames
                frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                depth_frame = frames.get_depth_frame()
                
                if depth_frame:
                    # Aplicar filtros para mejorar calidad
                    filtered_frame = self.spatial_filter.process(depth_frame)
                    filtered_frame = self.temporal_filter.process(filtered_frame)
                    filtered_frame = self.hole_filling_filter.process(filtered_frame)
                    
                    with self.lock:
                        self.current_depth_frame = filtered_frame
                        
            except Exception as e:
                print(f"Error en capture loop: {e}")
                time.sleep(0.1)

    def get_distance(self, x=None, y=None, region_size=20):
        """
        Obtener distancia en un punto específico o en el centro
        
        Args:
            x, y: Coordenadas del punto (None para centro)
            region_size: Tamaño de la región para promediar
            
        Returns:
            float: Distancia en metros, 0.0 si no hay datos válidos
        """
        with self.lock:
            if self.current_depth_frame is None:
                return 0.0
            
            # Usar centro si no se especifican coordenadas
            if x is None or y is None:
                x = self.width // 2
                y = self.height // 2
            
            # Validar coordenadas
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                return 0.0
            
            try:
                # Obtener región alrededor del punto
                half_region = region_size // 2
                x_start = max(0, x - half_region)
                x_end = min(self.width, x + half_region)
                y_start = max(0, y - half_region)
                y_end = min(self.height, y + half_region)
                
                # Convertir depth frame a numpy array
                depth_image = np.asanyarray(self.current_depth_frame.get_data())
                
                # Extraer región
                region = depth_image[y_start:y_end, x_start:x_end]
                
                # Filtrar valores válidos (> 0)
                valid_depths = region[region > 0]
                
                if len(valid_depths) > 0:
                    # Usar mediana para ser robusto ante outliers
                    distance_mm = np.median(valid_depths)
                    # Convertir a metros
                    return distance_mm / 1000.0
                else:
                    return 0.0
                    
            except Exception as e:
                print(f"Error obteniendo distancia: {e}")
                return 0.0

    def get_distance_center(self):
        """Obtener distancia en el centro de la imagen"""
        return self.get_distance()

    def get_distance_array(self):
        """
        Obtener array completo de distancias
        
        Returns:
            numpy.ndarray: Array 2D con distancias en metros
        """
        with self.lock:
            if self.current_depth_frame is None:
                return None
            
            try:
                depth_image = np.asanyarray(self.current_depth_frame.get_data())
                # Convertir a metros
                return depth_image.astype(np.float32) / 1000.0
            except Exception as e:
                print(f"Error obteniendo array de distancias: {e}")
                return None

    def is_obstacle_detected(self, threshold=0.3, x=None, y=None):
        """
        Detectar si hay un obstáculo dentro del umbral
        
        Args:
            threshold: Distancia umbral en metros
            x, y: Coordenadas del punto a verificar
            
        Returns:
            bool: True si hay obstáculo, False si no
        """
        distance = self.get_distance(x, y)
        return 0 < distance < threshold

    def get_closest_obstacle(self, min_distance=0.1, max_distance=2.0):
        """
        Encontrar el obstáculo más cercano en toda la imagen
        
        Args:
            min_distance: Distancia mínima válida en metros
            max_distance: Distancia máxima a considerar en metros
            
        Returns:
            tuple: (distancia, x, y) del obstáculo más cercano, o None si no hay
        """
        depth_array = self.get_distance_array()
        if depth_array is None:
            return None
        
        # Filtrar rango válido
        valid_mask = (depth_array > min_distance) & (depth_array < max_distance)
        
        if not np.any(valid_mask):
            return None
        
        # Encontrar punto más cercano
        min_distance_value = np.min(depth_array[valid_mask])
        min_indices = np.where(depth_array == min_distance_value)
        
        if len(min_indices[0]) > 0:
            y, x = min_indices[0][0], min_indices[1][0]
            return (min_distance_value, x, y)
        
        return None

    def get_obstacles_in_path(self, path_width=100, max_distance=1.0):
        """
        Detectar obstáculos en el camino frontal del robot
        
        Args:
            path_width: Ancho del camino en píxeles
            max_distance: Distancia máxima a considerar en metros
            
        Returns:
            list: Lista de obstáculos [(distancia, x, y), ...]
        """
        depth_array = self.get_distance_array()
        if depth_array is None:
            return []
        
        # Definir región del camino (centro de la imagen)
        center_x = self.width // 2
        x_start = max(0, center_x - path_width // 2)
        x_end = min(self.width, center_x + path_width // 2)
        
        # Extraer región del camino
        path_region = depth_array[:, x_start:x_end]
        
        # Filtrar obstáculos válidos
        valid_mask = (path_region > 0.1) & (path_region < max_distance)
        
        obstacles = []
        if np.any(valid_mask):
            # Encontrar todos los puntos con obstáculos
            y_indices, x_indices = np.where(valid_mask)
            
            for y, x in zip(y_indices, x_indices):
                actual_x = x + x_start
                distance = path_region[y, x]
                obstacles.append((distance, actual_x, y))
        
        # Ordenar por distancia (más cercano primero)
        obstacles.sort(key=lambda obs: obs[0])
        return obstacles

    def stop_streaming(self):
        """Detener el streaming del sensor"""
        self.is_streaming = False
        
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1.0)
        
        try:
            self.pipeline.stop()
            print("✓ RealSense streaming detenido")
        except Exception as e:
            print(f"Error deteniendo pipeline: {e}")

    def __del__(self):
        """Destructor para limpiar recursos"""
        if self.is_streaming:
            self.stop_streaming()