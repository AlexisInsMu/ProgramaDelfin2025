class DistanceSensor:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        # Initialize GPIO pins here if necessary

    def get_distance(self):
        # Trigger the sensor and calculate distance
        # This is a placeholder for actual distance measurement logic
        return 0.0

    def is_obstacle_detected(self, threshold=10.0):
        distance = self.get_distance()
        return distance < threshold