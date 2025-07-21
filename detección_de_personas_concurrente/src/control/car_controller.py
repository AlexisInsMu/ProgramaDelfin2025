from src.control.YB_Pcb_Car import YB_Pcb_Car
from threading import Thread
import time

class CarController:

    def __init__(self, shared_data, distnce_sensor=None):
        self.car = YB_Pcb_Car()
        self.running = True
        self.thread = Thread(target=self.control_loop)
        self.shared_data = shared_data
        self.distance_sensor = distnce_sensor
        self.thread.daemon = True 
        
    def start(self):
        self.thread.start()

    def control_loop(self):
        while self.running:
            # Obtener datos del sistema
            pose_center = self.shared_data.get_data('pose_center', None)
            print(f"Pose Center: {pose_center}")
            alto = self.shared_data.get_data('alto', False)
            image_center_x = self.shared_data.get_data('center_x', 300)
            
            position = "Unknown"
            color = (255, 255, 255)  # Default color (white)
            
            # Obtener datos del sensor de distancia
            obstacle_detected = self.shared_data.get_data('obstacle_detected', False)
            distance_center = self.shared_data.get_data('distance_center', 0.0)
            # Prioridad 1: detectar obstáculo
            if obstacle_detected and distance_center < 1:
                self.car.Car_Stop()
                position = "Stopped - Obstacle detected"
                color = (0, 0, 255)  # Red
                time.sleep(0.1)
                
                
            # Prioridad 2: Si hay persona detectada, seguirla
            elif pose_center is not None:
                pose_x, pose_y = pose_center
                if pose_x < image_center_x - 50:
                    position = "Following Person - Left"
                    color = (255, 0, 255)
                    self.car.Car_Left(40, 40)
                elif pose_x > image_center_x + 50:
                    position = "Following Person - Right"
                    color = (255, 0, 255)
                    self.car.Car_Right(40, 40)
                else:
                    position = "Following Person - Center"
                    color = (0, 255, 255)
                    self.car.Car_Run(40, 40)
                time.sleep(0.1)
                self.car.Car_Stop()
            
            
            # Prioridad 3: Si no hay persona, buscar gente, detenido
            else:
                position = "Buscando personas"
                color = (0, 0, 255)  # Red
                self.car.Car_Stop()
            
            # Guardar estado para depuración
            self.shared_data.set_data('position', position)
            self.shared_data.set_data('color', color)
            time.sleep(0.05)

    def move_forward(self, speed):
        pass

    def move_backward(self, speed):
        pass

    def turn_left(self, speed):
        pass

    def turn_right(self, speed):
        pass

    def stop(self):
        self.car.Car_Stop()
        self.running = False
        self.thread.join(timeout=1.0)  # Wait for the control loop to finish