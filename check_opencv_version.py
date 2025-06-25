import cv2 as cv
import sys

# Imprimir la versión de OpenCV
print(f"OpenCV Versión: {cv.__version__}")

# Verificar si ArucoDetector está disponible
try:
    # Intentar crear un diccionario ArUco
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_5X5_50)
    
    # Intentar crear un detector ArUco (método nuevo)
    try:
        parameters = cv.aruco.DetectorParameters()
        detector = cv.aruco.ArucoDetector(aruco_dict, parameters)
        print("✓ ArucoDetector está disponible (método nuevo)")
        
        # Verificar si detectMarkers funciona con el método nuevo
        import numpy as np
        dummy_img = np.zeros((100, 100), dtype=np.uint8)
        corners, ids, rejected = detector.detectMarkers(dummy_img)
        print("✓ detector.detectMarkers() funciona")
        
    except AttributeError:
        print("ArucoDetector NO está disponible")
        print("Usando método antiguo de detección de ArUco:")
        parameters = cv.aruco.DetectorParameters_create()
        print("✓ cv.aruco.DetectorParameters_create() funciona")
        
        # Verificar si detectMarkers funciona con el método antiguo
        import numpy as np
        dummy_img = np.zeros((100, 100), dtype=np.uint8)
        corners, ids, rejected = cv.aruco.detectMarkers(dummy_img, aruco_dict, parameters=parameters)
        print("✓ cv.aruco.detectMarkers() funciona")
        
except Exception as e:
    print(f"Error al verificar ArUco: {e}")
    
print("\nMódulos y funciones disponibles en cv.aruco:")
aruco_items = dir(cv.aruco)
for item in aruco_items:
    if not item.startswith("_"):  # Filtrar métodos privados
        print(f"- {item}")
