import cv2
import numpy as np

def generate_aruco_markers(dictionary_type=cv2.aruco.DICT_5X5_50, num_markers=5, marker_size=300):
    """
    Genera y guarda marcadores ArUco.
    
    Args:
        dictionary_type: Tipo de diccionario ArUco
        num_markers: Número de marcadores a generar
        marker_size: Tamaño de cada marcador en píxeles
    """
    # Verificar versión de OpenCV
    print(f"Versión de OpenCV: {cv2.__version__}")
    
    # Crear el diccionario ArUco (compatible con diferentes versiones)
    try:
        # Para OpenCV 4.7+
        aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_type)
    except AttributeError:
        try:
            # Para OpenCV 4.x
            aruco_dict = cv2.aruco.Dictionary_get(dictionary_type)
        except AttributeError:
            # Intento alternativo
            aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_type)
    
    # Generar y guardar cada marcador
    for i in range(num_markers):
        # Crear imagen para el marcador
        marker_img = np.zeros((marker_size, marker_size), dtype=np.uint8)
        
        # Generar marcador (compatible con diferentes versiones)
        try:
            # Para OpenCV 4.7+
            cv2.aruco.generateImageMarker(aruco_dict, i, marker_size, marker_img, 1)
        except AttributeError:
            try:
                # Para versiones anteriores
                cv2.aruco.drawMarker(aruco_dict, i, marker_size, marker_img, 1)
            except AttributeError:
                # Último intento
                aruco_dict.drawMarker(i, marker_size, marker_img, 1)
        
        # Guardar el marcador como imagen
        filename = f"aruco_marker_{i}.png"
        cv2.imwrite(filename, marker_img)
        print(f"Marcador ArUco ID {i} guardado como {filename}")

if __name__ == "__main__":
    # Verificar las constantes disponibles en cv2.aruco
    print("Constantes disponibles en cv2.aruco:")
    for attr in dir(cv2.aruco):
        if attr.startswith("DICT_"):
            print(f"  {attr}")
    
    # Usar un valor entero directo si las constantes no están disponibles
    try:
        dictionary_value = cv2.aruco.DICT_5X5_50
        print(f"Usando constante DICT_5X5_50 = {dictionary_value}")
    except AttributeError:
        # Valores típicos para diccionarios 5x5 con 50 marcadores
        dictionary_value = 7  # Este valor puede variar según tu versión
        print(f"Constante no disponible, usando valor {dictionary_value}")
    
    generate_aruco_markers(dictionary_type=dictionary_value, num_markers=5, marker_size=300)