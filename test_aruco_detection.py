import cv2 as cv
import numpy as np
import time

def test_aruco_detection():
    """
    Script para probar la detección de marcadores ArUco usando la webcam.
    Muestra el video con los marcadores detectados resaltados.
    """
    # Inicializar la cámara
    cap = cv.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    print("Presiona 'q' para salir")
    
    while True:
        # Capturar frame
        ret, frame = cap.read()
        
        if not ret:
            print("Error: No se pudo leer el frame")
            break
        
        # Convertir a escala de grises
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        # Detectar ArUcos con el método compatible con OpenCV 4.6.0
        aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
        parameters = cv.aruco.DetectorParameters_create()
        corners, ids, rejected = cv.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        
        # Dibujar los marcadores detectados
        if ids is not None:
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Mostrar información de los marcadores detectados
            for i, marker_id in enumerate(ids):
                print(f"Marcador ID {marker_id[0]} detectado")
                
                # Calcular el centro del marcador
                marker_corners = corners[i][0]
                center_x = int(np.mean([corner[0] for corner in marker_corners]))
                center_y = int(np.mean([corner[1] for corner in marker_corners]))
                
                # Dibujar el centro y el ID
                cv.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                cv.putText(frame, f"ID: {marker_id[0]}", (center_x + 10, center_y), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Mostrar número total de marcadores detectados
        cv.putText(frame, f"Detectados: {len(ids) if ids is not None else 0}", (10, 30), 
                  cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Mostrar imagen
        cv.imshow('ArUco Detection', frame)
        
        # Salir si se presiona 'q'
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Pequeña pausa para no saturar CPU
        time.sleep(0.01)
    
    # Liberar recursos
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    test_aruco_detection()
