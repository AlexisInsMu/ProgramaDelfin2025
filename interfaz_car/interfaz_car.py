import cv2 as cv
import time
import numpy as np
from YB_Pcb_Car import YB_Pcb_Car




class interfaz_car:
    def __init__(self):
        # Initialize the car
        self.car = YB_Pcb_Car()
        self.last_cx = None
        self.last_cy = None
        self.last_detection_time = 0
        print("Car initialized.")
        
        
    def centroid_process(self):
       # Initialize the camera
        camera = cv.VideoCapture(0)

        # Set camera properties
        camera.set(cv.CAP_PROP_FRAME_WIDTH, 600)
        camera.set(cv.CAP_PROP_FRAME_HEIGHT, 500)
        camera.set(cv.CAP_PROP_FPS, 30)

        # Check if camera opened successfully
        if not camera.isOpened():
            print("Error: Could not open camera.")
            exit()

        # Create window once
        cv.namedWindow('Object Tracking', cv.WINDOW_NORMAL)


        lower_hsv = np.array([35,40,30])
        upper_hsv = np.array([90,255,255])

        # Rango alto para rojo
        rojo_bajo2 = np.array([160, 100, 100])
        rojo_alto2 = np.array([179, 255, 255])

        print("Press 'q' to exit")
        car = YB_Pcb_Car()
        try: 
            while True:
                # Capture frame
                ret, frame = camera.read()
                
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Get frame dimensions
                height, width = frame.shape[:2]
                center_x = width // 2
                
                # Process the frame
                hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
                mascara1 = cv.inRange(hsv, lower_hsv, upper_hsv)

                # Aplicar opening para eliminar ruido pequeño

                # Aplicar closing para cerrar pequeños huecos
                #mascara2 = cv.inRange(hsv, rojo_bajo2, rojo_alto2)
                #mascara_rojo = cv.bitwise_or(mascara1, mascara2)
                
                #image improvement
                kernel = np.ones((5,5), np.uint8)
                mascara1 = cv.morphologyEx(mascara1, cv.MORPH_OPEN, kernel)
                mascara1 = cv.morphologyEx(mascara1, cv.MORPH_CLOSE, kernel)
                mascara1 = cv.GaussianBlur(mascara1, (5, 5), 0)
                contornos, _ = cv.findContours(mascara1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                
                
                # Process each contour
                for contorno in contornos:
                    # Filter small contours
                    area = cv.contourArea(contorno)
                    if area > 500:
                        # Filtrar por relación de aspecto
                        x, y, w, h = cv.boundingRect(contorno)
                        aspect_ratio = float(w)/h
                    
                        
                        # Si cumple criterios de forma
                        if True:
            
                            cv.drawContours(frame, [contorno], -1, (0, 255, 0), 2)
                            
                            # Calculate centroid
                            M = cv.moments(contorno)
                            # Y en el procesamiento de centroides:
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                
                                # Suavizar movimientos con media ponderada
                                if self.last_cx is not None:
                                    # Aplica peso de 70% al valor actual y 30% al anterior
                                    cx = int(0.7 * cx + 0.3 * self.last_cx)
                                    cy = int(0.7 * cy + 0.3 * self.last_cy)
                                
                                self.last_cx = cx
                                self.last_cy = cy
                                # # Calcular desviación del centro
                                # error = cx - center_x
                                # max_error = width // 3  # Máximo error considerado (1/3 del ancho)

                                # # Normalizar el error a un rango de -1.0 a 1.0
                                # normalized_error = max(-1.0, min(1.0, error / max_error))

                                # # Velocidad base
                                # base_speed = 40

                                # # Calcular velocidades para cada rueda (control proporcional)
                                # left_speed = int(base_speed - (normalized_error * base_speed * 0.8))
                                # right_speed = int(base_speed + (normalized_error * base_speed * 0.8))

                                # # Asegurar que las velocidades estén en rangos válidos
                                # left_speed = max(20, min(70, left_speed))
                                # right_speed = max(20, min(70, right_speed))

                                # # Aplicar el movimiento sin detener el carro
                                # car.Car_Run(left_speed, right_speed)
                                # car.Car_Stop()
                                # time.sleep(0.1)  # Pequeño retraso para permitir que el carro se mueva

                                # Visualización
                                # if abs(normalized_error) > 0.3:
                                #     position = "Turning" + (" Right" if normalized_error > 0 else " Left")
                                #     color = (0, 165, 255)  # Naranja
                                # else:
                                #     position = "Forward"
                                #     color = (0, 255, 0)  # Verde
                                
                                position = "Center"
                                # Determine position
                                if cx < center_x - 100:
                                    position = "Left"
                                    color = (0, 0, 255)  # Red
                                    car.Car_Left(32, 32)
                                    time.sleep(0.1)  # Small delay to allow car to run
                                    car.Car_Stop()
                                    
                                elif cx > center_x + 100:
                                    position = "Right"
                                    color = (0, 0, 255)  # Red
                                    car.Car_Right(32, 32)
                                    time.sleep(0.1)  # Small delay to allow car to run
                                    car.Car_Stop()
                                    
                                else:
                                    position = "Center"
                                    color = (0, 255, 0)  # Green
                                    car.Car_Run(35, 35)
                                    car.Car_Stop()
                                    time.sleep(0.1)  # Small delay to allow car to run
                                    car.Car_Stop()
                                
                                # Display position
                                cv.putText(frame, position, (cx - 20, cy - 20), 
                                        cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                                
                            #print(f"Object at {position}: ({cx}, {cy})")
                
                # Display the frame
                cv.imshow('Object Tracking', frame)
                
                # Exit on 'q' key
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
                
                
                time.sleep(0.02)

            # Cleanup
            camera.release()
            cv.destroyAllWindows()
            car.Car_Stop()
        except KeyboardInterrupt:
            print("Program interrupted by user.")
            car.Car_Stop()
            
            
    def open_camara():
        # Initialize the camera
        camera = cv.VideoCapture(0)

        # Set camera properties
        camera.set(cv.CAP_PROP_FRAME_WIDTH, 600)
        camera.set(cv.CAP_PROP_FRAME_HEIGHT, 500)
        camera.set(cv.CAP_PROP_FPS, 30)

        # Check if camera opened successfully
        if not camera.isOpened():
            print("Error: Could not open camera.")
            exit()

        # Create window once
        cv.namedWindow('Object Tracking', cv.WINDOW_NORMAL)

        # Define HSV range for green
        
        lower_green = np.array([35,50,50])
        upper_green = np.array([85,255,255])
        
        #lower_green = cv.cvtColor(np.uint8([[lower_s]]), cv.COLOR_RGB2HSV)[0][0]
        #upper_green = cv.cvtColor(np.uint8([[upper_s]]), cv.COLOR_RGB2HSV)[0][0]


        try: 
            while True:
                # Capture frame
                ret, frame = camera.read()
                
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Convert to HSV
                hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
                mask = cv.inRange(hsv, lower_green, upper_green)
                
                # Find contours
                contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                
                # Draw contours
                for contour in contours:
                    if cv.contourArea(contour) > 500:
                        cv.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                
                # Show the result
                cv.imshow('Object Tracking', frame)
                
                # Exit on 'q' key
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.02)

        except KeyboardInterrupt:
            print("Program interrupted by user.")
            car.Car_Stop()

        finally:
            camera.release()
            cv.destroyAllWindows()
            car.Car_Stop()
       

    def run(self):
        # Start the car
        self.car.Car_Run(150, 150)
        time.sleep(1)
        self.car.Car_Stop()
        print("Car stopped.")

    def back(self):
        # Move the car backward
        self.car.Car_Back(150, 150)
        time.sleep(1)
        self.car.Car_Stop()
        print("Car moved backward and stopped.")


# Initialize the camera

if __name__ == "__main__":
    interfaz = interfaz_car()
    try:
        
        interfaz.centroid_process()
 #      interfaz_car.open_camara()
    except Exception as e:
        print(f"An error occurred: {e}")
