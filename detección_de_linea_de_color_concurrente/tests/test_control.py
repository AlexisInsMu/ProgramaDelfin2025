from src.control.car_controller import CarController
from src.control.motor_driver import MotorDriver
import unittest

class TestCarController(unittest.TestCase):
    def setUp(self):
        self.car_controller = CarController()
    
    def test_move_forward(self):
        self.car_controller.move_forward()
        # Add assertions to verify the expected behavior

    def test_move_backward(self):
        self.car_controller.move_backward()
        # Add assertions to verify the expected behavior

    def test_turn_left(self):
        self.car_controller.turn_left()
        # Add assertions to verify the expected behavior

    def test_turn_right(self):
        self.car_controller.turn_right()
        # Add assertions to verify the expected behavior

class TestMotorDriver(unittest.TestCase):
    def setUp(self):
        self.motor_driver = MotorDriver()
    
    def test_set_speed(self):
        self.motor_driver.set_speed(100)
        # Add assertions to verify the expected behavior

    def test_stop_motor(self):
        self.motor_driver.stop_motor()
        # Add assertions to verify the expected behavior

if __name__ == '__main__':
    unittest.main()