# Raspberry Pi Car Project

This project is a Raspberry Pi-based car that utilizes threading for camera processing and car control. The car is equipped with a camera for streaming and image processing, as well as sensors for obstacle detection.

## Project Structure

```
raspberry-pi-car
├── src
│   ├── camera
│   │   ├── __init__.py
│   │   ├── camera_manager.py
│   │   └── image_processor.py
│   ├── control
│   │   ├── __init__.py
│   │   ├── car_controller.py
│   │   └── motor_driver.py
│   ├── sensors
│   │   ├── __init__.py
│   │   └── distance_sensor.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── thread_safe_data.py
│   ├── __init__.py
│   └── main.py
├── tests
│   ├── __init__.py
│   ├── test_camera.py
│   ├── test_control.py
│   └── test_utils.py
├── config
│   └── settings.json
├── scripts
│   ├── install_dependencies.sh
│   └── start_on_boot.sh
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd raspberry-pi-car
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the installation script to set up any additional dependencies:
   ```
   ./scripts/install_dependencies.sh
   ```

## Usage

To start the car control and camera processing, run the main application:
```
python src/main.py
```

## Components

- **Camera Module**: Handles camera initialization and streaming.
  - `CameraManager`: Manages camera operations.
  - `ImageProcessor`: Processes images captured by the camera.

- **Control Module**: Manages car movement.
  - `CarController`: Controls the car's movement.
  - `MotorDriver`: Interfaces with the motor hardware.

- **Sensors Module**: Measures distance and detects obstacles.
  - `DistanceSensor`: Provides distance measurements.

- **Utils Module**: Contains utility functions and classes.
  - `ThreadSafeData`: Provides thread-safe data storage.

## Testing

To run the tests for the project, use the following command:
```
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.