import mss
import mss.tools
import time
import os

# Crear directorio si no existe
custom_path = "./images"
if not os.path.exists(custom_path):
    os.makedirs(custom_path)

with mss.mss() as sct:
    i = 60
    while i <= 120:
        i += 1
        # Capturar toda la pantalla (monitor 0 es generalmente toda la pantalla)
        monitor = sct.monitors[0]  # monitor 0 representa toda el área visible
        screenshot = sct.grab(monitor)
        
        # Guardar la imagen
        output_path = os.path.join(custom_path, f"screenshot{i}.png")
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)
        print(f"Captura {i} guardada")
        time.sleep(1)