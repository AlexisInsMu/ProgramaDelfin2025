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
            cx, cy = self.shared_data.get_data('line_error', (None, None))
            center_x = self.shared_data.get_data('center_x', 300)
            position = "Unknown"
            color = (255, 255, 255)  # Default color (white)
            alto = self.shared_data.get_data('alto', False)
            if alto:
                self.car.Car_Stop()
                time.sleep(0.1)
            elif (cx is None or cy is None):
                # If no line detected, stop the car
                self.car.Car_Left(32, 32)
                time.sleep(0.1)
                self.car.Car_Stop()
                
            else:
                if cx < center_x - 50:
                    position = "Left"
                    color = (0, 0, 255)  # Red
                    self.car.Car_Left(35, 35)
                    time.sleep(0.1)  # Small delay to allow self.car to run
                    self.car.Car_Stop()
                    
                elif cx > center_x + 50:
                    position = "Right"
                    color = (0, 0, 255)  # Red
                    self.car.Car_Right(35, 35)
                    time.sleep(0.1)  # Small delay to allow self.car to run
                    self.car.Car_Stop()
                    
                else:
                    position = "Center"
                    color = (0, 255, 0)  # Green
                    self.car.Car_Run(35, 35)
                    self.car.Car_Stop()
                    time.sleep(0.1)  # Small delay to allow self.car to run
                    self.car.Car_Stop()
            
            self.shared_data.set_data('position', position)
            self.shared_data.set_data('color', color)
            time.sleep(0.05)  # Simulate a control loop delay

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