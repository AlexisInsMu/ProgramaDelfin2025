#!/usr/bin/env python3
import cv2
import numpy as np
import os

# Configurar variables de entorno
os.environ['LIBGL_ALWAYS_INDIRECT'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'xcb'

print("Probando X11 forwarding...")
print(f"DISPLAY: {os.environ.get('DISPLAY', 'No configurado')}")

try:
    # Crear una imagen simple
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    img[:] = (0, 255, 0)  # Verde
    
    cv2.putText(img, "X11 Forwarding OK!", (50, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("Test X11", img)
    print("Ventana creada. Presiona cualquier tecla para cerrar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("¡X11 forwarding funciona correctamente!")
    
except Exception as e:
    print(f"Error: {e}")
    print("X11 forwarding no está funcionando")
