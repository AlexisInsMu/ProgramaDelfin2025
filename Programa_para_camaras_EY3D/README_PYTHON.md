# eYs3D Python Interface para Jetson Nano

Este directorio contiene programas en Python para conectarse a cámaras eYs3D en NVIDIA Jetson Nano.

## 📋 Requisitos

### Hardware
- NVIDIA Jetson Nano
- Cámara eYs3D compatible
- Cable USB 3.0 (recomendado)

### Software
- JetPack 4.6 o superior
- Python 3.6+
- OpenCV 4.x
- NumPy

## 🚀 Instalación Rápida

### 1. Compilar las librerías para Jetson Nano

```bash
# En el directorio del proyecto
cd /home/alexisnovo8/Downloads/eys3d_wrapper_prebuilt_linux

# Compilar para NVIDIA Jetson (aarch64)
sh build_NVIDIA.sh
```

### 2. Instalar dependencias de Python

```bash
# Opción 1: Instalar dependencias automáticamente
sudo bash install_eys3d_dependencies.sh

# Opción 2: Instalar manualmente
sudo apt update
sudo apt install python3-pip python3-opencv
pip3 install opencv-python numpy
```

### 3. Configurar permisos USB

```bash
# Agregar usuario a grupos necesarios
sudo usermod -a -G dialout $USER
sudo usermod -a -G video $USER

# Crear reglas udev
sudo tee /etc/udev/rules.d/99-eys3d-camera.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="1e4e", MODE="0666", GROUP="video"
SUBSYSTEM=="usb", ATTR{idVendor}=="04b4", MODE="0666", GROUP="video"
KERNEL=="video*", SUBSYSTEM=="video4linux", MODE="0666", GROUP="video"
EOF

# Recargar reglas
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 4. Reiniciar el sistema

```bash
sudo reboot
```

## 📁 Programas Incluidos

### 1. `eys3d_simple.py` - Interfaz Simple
Programa básico para capturar imágenes de color y profundidad.

```bash
python3 eys3d_simple.py
```

**Características:**
- Interfaz simple y fácil de usar
- Captura de imágenes de color y profundidad
- Guardado de imágenes en formato JPG/PNG
- Controles por teclado intuitivos

**Controles:**
- `q` - Salir
- `s` o `SPACE` - Guardar imágenes
- `c` - Mostrar/ocultar color
- `d` - Mostrar/ocultar profundidad

### 2. `eys3d_pipeline.py` - Pipeline Avanzado
Sistema de pipeline con threads para procesamiento en tiempo real.

```bash
python3 eys3d_pipeline.py
```

**Características:**
- Pipeline multithread para mejor rendimiento
- Queues para manejo de frames
- Sincronización de color y profundidad
- Monitoreo de FPS

**Controles:**
- `q` - Salir
- `s` - Guardar frame set
- `c` - Toggle color stream
- `d` - Toggle depth stream

### 3. `eys3d_wrapper.py` - Wrapper Completo
Wrapper completo con todas las funcionalidades.

```bash
python3 eys3d_wrapper.py
```

## 🔧 Configuración

### Verificar conexión de cámara

```bash
# Verificar dispositivos USB
lsusb | grep -i eys3d

# Verificar dispositivos de video
v4l2-ctl --list-devices

# Verificar permisos
ls -la /dev/video*
```

### Configurar resolución

Edita los archivos Python y modifica las variables:

```python
# En el constructor de la clase
self.image_width = 1280    # Cambiar resolución
self.image_height = 720
```

### Configurar FPS

```python
# En el bucle principal
time.sleep(0.033)  # 30 FPS
time.sleep(0.016)  # 60 FPS
```

## 🐛 Solución de Problemas

### Error: "Librería no encontrada"

```bash
# Verificar que las librerías estén compiladas
ls -la lib/eSPDI/libeSPDI_NVIDIA_64.so

# Si no existe, recompilar
sh build_NVIDIA.sh
```

### Error: "No se encontraron dispositivos"

```bash
# Verificar conexión USB
lsusb

# Verificar permisos
groups $USER  # Debe incluir 'video' y 'dialout'

# Reconectar la cámara
sudo rmmod uvcvideo
sudo modprobe uvcvideo
```

### Error: "Permission denied"

```bash
# Aplicar permisos
sudo chmod 666 /dev/video*

# O agregar usuario a grupo video
sudo usermod -a -G video $USER
```

### Error: "Import cv2 failed"

```bash
# Instalar OpenCV
pip3 install opencv-python

# O usar versión del sistema
sudo apt install python3-opencv
```

### Rendimiento bajo

```bash
# Verificar CPU/GPU
htop
tegrastats

# Optimizar configuración
sudo nvpmodel -m 0  # Modo máximo rendimiento
sudo jetson_clocks   # Maximizar clocks
```

## 📊 Ejemplos de Uso

### Capturar imagen simple

```python
from eys3d_simple import EYS3DSimpleCamera

camera = EYS3DSimpleCamera()
camera.load_library()
camera.initialize()
camera.open_device(0)

# Capturar imágenes
color_image = camera.get_color_image()
depth_image = camera.get_depth_image()

# Guardar
cv2.imwrite('color.jpg', color_image)
cv2.imwrite('depth.png', depth_image)

camera.cleanup()
```

### Procesamiento en tiempo real

```python
from eys3d_pipeline import EYS3DPipeline

pipeline = EYS3DPipeline()
pipeline.load_libraries()
pipeline.initialize_system()
pipeline.start_streaming()

while True:
    frame_set = pipeline.get_frame_set()
    if frame_set:
        # Procesar frames
        color = frame_set['color']['frame']
        depth = frame_set['depth']['frame']
        
        # Tu procesamiento aquí
        processed = process_frames(color, depth)
        
        cv2.imshow('Result', processed)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

pipeline.stop_streaming()
pipeline.cleanup()
```

## 📚 Recursos Adicionales

### Documentación de la API
- [eSPDI Documentation](https://eys3d.com/docs)
- [OpenCV Python Tutorials](https://opencv-python-tutroals.readthedocs.io)

### Ejemplos de procesamiento
- Detección de objetos con YOLO
- Segmentación de profundidad
- Tracking de objetos
- Mapeo 3D

### Optimización para Jetson
- Uso de TensorRT para inferencia
- Optimización de memoria
- Paralelización con CUDA

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una branch para tu feature
3. Commit tus cambios
4. Push a la branch
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia Apache 2.0. Ver el archivo LICENSE para más detalles.

## 💬 Soporte

Si tienes problemas:

1. Revisa la sección de solución de problemas
2. Verifica que la cámara esté soportada
3. Contacta al soporte técnico de eYs3D
4. Abre un issue en GitHub

---

**Nota:** Este es un wrapper no oficial para las cámaras eYs3D. Para soporte oficial, contacta a eYs3D Corporation.
