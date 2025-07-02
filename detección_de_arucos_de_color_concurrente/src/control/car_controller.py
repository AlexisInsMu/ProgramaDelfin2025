from src.control.YB_Pcb_Car import YB_Pcb_Car
from threading import Thread
import time

class CarController:

    def __init__(self, shared_data):
        self.car = YB_Pcb_Car()
        self.running = True
        self.thread = Thread(target=self.control_loop)
        self.shared_data = shared_data
        self.thread.daemon = True 
        
    def start(self):
        self.thread.start()

    def control_loop(self):
        while self.running:
            # Obtener datos del sistema
            aruco_center = self.shared_data.get_data('aruco_center', None)
            alto = self.shared_data.get_data('alto', False)
            image_center_x = self.shared_data.get_data('center_x', 300)  # Centro de imagen por defecto
            
            position = "Unknown"
            color = (255, 255, 255)  # Default color (white)
            
            # Prioridad 1: Si hay ArUco grande, detenerse
            if alto is True:
                self.car.Car_Stop()
                position = "Stopped - Large ArUco"
                color = (0, 0, 255)  # Red
                time.sleep(0.1)
                
            # Prioridad 2: Si hay ArUco detectado, seguirlo
            elif aruco_center is not None:
                aruco_x, aruco_y = aruco_center
                
                if aruco_x < image_center_x - 50:
                    position = "Following ArUco - Left"
                    color = (255, 255, 0)  # Yellow
                    self.car.Car_Left(35, 35)
                    time.sleep(0.1)
                    self.car.Car_Stop()
                    
                elif aruco_x > image_center_x + 50:
                    position = "Following ArUco - Right"
                    color = (255, 255, 0)  # Yellow
                    self.car.Car_Right(35, 35)
                    time.sleep(0.1)
                    self.car.Car_Stop()
                    
                else:
                    position = "Following ArUco - Center"
                    color = (0, 255, 0)  # Green
                    self.car.Car_Run(35, 35)
                    time.sleep(0.1)
                    self.car.Car_Stop()
            
            # Prioridad 3: Si no hay ArUco, buscar girando
            else:
                position = "Searching for ArUco"
                color = (0, 0, 255)  # Red
                self.car.Car_Left(35, 35)
                time.sleep(0.1)
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