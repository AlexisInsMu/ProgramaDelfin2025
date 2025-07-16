from src.control.YB_Pcb_Car import YB_Pcb_Car
from threading import Thread
import time

class CarController:

    def __init__(self, shared_data, distance_sensor=None): 
        self.car = YB_Pcb_Car()
        self.running = True
        self.thread = Thread(target=self.control_loop)
        self.shared_data = shared_data
        self.distance_sensor = distance_sensor
        self.thread.daemon = True 
        
    def start(self):
        self.thread.start()

    def control_loop(self):
        while self.running:
            # Obtener datos del sistema
            aruco_center = self.shared_data.get_data('aruco_center', None)
            alto = self.shared_data.get_data('alto', False)
            image_center_x = self.shared_data.get_data('center_x', 300)  # Centro de imagen por defecto
            
            # Obtener datos del sensor de distancia
            obstacle_detected = self.shared_data.get_data('obstacle_detected', False)
            distance_center = self.shared_data.get_data('distance_center', 0.0)
            
            position = "Unknown"
            color = (255, 255, 255)  # Default color (white)
            
            # Prioridad 1: Si hay obstáculo muy cerca, detenerse
            if obstacle_detected and distance_center < 0.3:
                self.car.Car_Stop()
                position = "Stopped - Obstacle detected"
                color = (0, 0, 255)  # Red
                time.sleep(0.1)
                
            # Prioridad 2: Si hay ArUco grande, detenerse
            elif alto is True:
                self.car.Car_Stop()
                position = "Stopped - Large ArUco"
                color = (0, 0, 255)  # Red
                time.sleep(0.1)
                
            # Prioridad 3: Si hay ArUco detectado, seguirlo (pero cuidando obstáculos)
            elif aruco_center is not None:
                aruco_x, aruco_y = aruco_center
                
                # Solo moverse si no hay obstáculos muy cerca
                if not obstacle_detected or distance_center > 0.5:
                    if aruco_x < image_center_x - 50:
                        position = "Following ArUco - Left"
                        color = (255, 255, 0)  # Yellow
                        self.car.Car_Left(40, 40)
                        time.sleep(0.1)
                        self.car.Car_Stop()
                        
                    elif aruco_x > image_center_x + 50:
                        position = "Following ArUco - Right"
                        color = (255, 255, 0)  # Yellow
                        self.car.Car_Right(40, 40)
                        time.sleep(0.1)
                        self.car.Car_Stop()
                        
                    else:
                        position = "Following ArUco - Center"
                        color = (0, 255, 0)  # Green
                        self.car.Car_Run(40, 40)
                        time.sleep(0.1)
                        self.car.Car_Stop()
                else:
                    position = "ArUco found but obstacle near"
                    color = (255, 165, 0)  # Orange
                    self.car.Car_Stop()
            
            # Prioridad 4: Si no hay ArUco, buscar girando (pero cuidando obstáculos)
            else:
                position = "Searching for ArUco"
                color = (0, 0, 255)  # Red
                self.car.Car_Stop()
            
            # Guardar estado para depuración
            self.shared_data.set_data('position', position)
            self.shared_data.set_data('color', color)
            time.sleep(0.05)

    def move_forward(self, speed):
        self.car.Car_Run(speed, speed)

    def move_backward(self, speed):
        self.car.Car_Back(speed, speed)

    def turn_left(self, speed):
        self.car.Car_Left(speed, speed)

    def turn_right(self, speed):
        self.car.Car_Right(speed, speed)

    def stop(self):
        self.car.Car_Stop()
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)