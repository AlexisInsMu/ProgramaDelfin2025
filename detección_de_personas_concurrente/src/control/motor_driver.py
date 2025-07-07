class MotorDriver:
    def __init__(self, motor_pin):
        self.motor_pin = motor_pin
        self.speed = 0
        # Initialize motor hardware here (e.g., GPIO setup)

    def set_speed(self, speed):
        self.speed = speed
        # Code to set motor speed using hardware interface

    def stop_motor(self):
        self.set_speed(0)
        # Code to stop the motor using hardware interface

    def forward(self):
        self.set_speed(100)  # Example speed value for moving forward
        # Code to set motor direction for forward movement

    def backward(self):
        self.set_speed(100)  # Example speed value for moving backward
        # Code to set motor direction for backward movement

    def turn_left(self):
        self.set_speed(50)  # Example speed value for turning
        # Code to set motor direction for turning left

    def turn_right(self):
        self.set_speed(50)  # Example speed value for turning
        # Code to set motor direction for turning right