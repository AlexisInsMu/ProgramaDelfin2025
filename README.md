# Programa Delfín 2025 - Raspberry Pi Car Project

Este proyecto es un sistema integral para un carro inteligente basado en Raspberry Pi con múltiples capacidades de detección y control autónomo desarrollado para el Programa Delfín 2025.

Su propósito principal es permitir ayudar con la carga de alimento, grano, agua y otros suministros a los animales de la granja o sembradíos, mientras va siguiendo a un persona o en su defecto siguiendo una ruta preestablecida, evitando obstáculos y detectando marcadores ArUco para navegación precisa.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Módulos del Sistema](#módulos-del-sistema)
- [Pruebas](#pruebas)
- [Solución de Problemas](#solución-de-problemas)
- [Contribución](#contribución)
- [Licencia](#licencia)

## 🚗 Descripción General

Este proyecto implementa un sistema de navegación autónoma para un carro Raspberry Pi con múltiples capacidades:

- **Detección de ArUco markers** con procesamiento concurrente
- **Detección de líneas de colores** (secuencial y concurrente)
- **Detección de personas** con procesamiento concurrente
- **Control de motores** y navegación
- **Integración con Intel RealSense** para visión 3D
- **Interfaz X11** para visualización

## 📁 Estructura del Proyecto

```
ProgramaDelfin2025/
├── arucos/                                    # Marcadores ArUco y utilidades
│   ├── aruco_marker_*.png                    # Marcadores ArUco generados
│   └── arucos.py                             # Utilidades para ArUco
├── detección_de_arucos_de_color_concurrente/  # Detección ArUco con threading
│   ├── src/                                  # Código fuente principal
│   ├── tests/                                # Pruebas unitarias
│   ├── config/                               # Configuraciones
│   ├── scripts/                              # Scripts de instalación
│   └── README.md                             # Documentación específica
├── detección_de_linea_de_color_concurrente/   # Detección de líneas (concurrente)
├── detección_de_linea_de_color_secuencial/    # Detección de líneas (secuencial)
├── detección_de_personas_concurrente/         # Detección de personas con threading
├── pruebas_individuales/                      # Pruebas y experimentos
├── Programa_para_camara_EY3D/                # Programa para cámara EY3D
├── raspberry-pi-car/                          # Implementación base del carro
├── test_x11.py                               # Pruebas de interfaz X11
└── README.md                                 # Este archivo
```

## 🔧 Requisitos del Sistema

### Hardware
- **Raspberry Pi 4** (recomendado) o superior
- **Cámara Intel RealSense** (D435i/D455)
- **Motores DC** con controladores
- **Sensores ultrasónicos** para detección de obstáculos (temporalmente deshabilitado para este proyecto)
- **Tarjeta microSD** (32GB mínimo)

### Software
- **Raspberry Pi OS** (64-bit recomendado)
- **Python 3.11+**
- **OpenCV 4.7+**
- **librealsense2** (instalar repecto al sistema operativo que se use)
- **X11** para interfaz gráfica


### Dependencias Python
```bash
# Principales dependencias
opencv-python>=4.5.0
numpy>=1.21.0
pyrealsense2>=2.55.1 (checar Warning)
threading
concurrent.futures
```
> [!WARNING]
> tener cuidado con la libreria pyrealsense ya que depende del sistema operativo, su manera de instalar
>
> SI estan un sistema raspberry pi 4, pueden usar el siguiente comando dentro de la carpeta de cada implementación
> ```bash
> cd src/sensors/realsense_cpp/
> python setup.py install
> ``` 

## 🚀 Instalación

### 1. Instalación Automática (Recomendado) (compatible solo con raspberry pi 4)

Cada módulo incluye un script de instalación automatizada:

```bash
# Para detección de ArUco
cd detección_de_arucos_de_color_concurrente/
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh

# Para detección de personas
cd detección_de_personas_concurrente/
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
```

> [!Caution]
> Solo compatible con la funcionalidad de detección de ArUco

### 3. Configuración de Permisos USB

```bash
# Configurar permisos para RealSense
sudo cp robot_env_new/config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## ⚙️ Configuración

### Configuración Principal

Cada módulo tiene su archivo de configuración en `config/settings.json`:

```json
{
  "camera": {
    "resolution": [640, 480],
    "fps": 30,
    "format": "RGB8"
  },
  "detection": {
    "confidence_threshold": 0.7,
    "nms_threshold": 0.4
  },
  "motors": {
    "speed": 50,
    "turn_speed": 30
  }
}
```

> [!NOTE]
> Considere que las configuración depende de la camara que utilice

### Variables de Entorno

ejecutar el start_on_boot.sh para configurar las variables de entorno necesarias

> [!Caution]
> Solo compatible con la funcionalidad de detección de ArUco

```bash
cd detección_de_arucos_de_color_concurrente/
chmod +x scripts/start_on_boot.sh
./scripts/start_on_boot.sh
```


## 🎯 Uso

### Ejecución de Módulos Individuales

```bash
# Detección de ArUco
cd detección_de_arucos_de_color_concurrente/
python src/main.py

# Detección de personas
cd detección_de_personas_concurrente/
python src/main.py

# Detección de líneas (concurrente)
cd detección_de_linea_de_color_concurrente/
python src/main.py
```

## 🧩 Módulos del Sistema

### 1. Detección de ArUco Markers
- **Ubicación**: `detección_de_arucos_de_color_concurrente/`
- **Funcionalidad**: Detección y reconocimiento de marcadores ArUco
- **Procesamiento**: Concurrente con threading
- **Uso**: Navegación y posicionamiento

### 2. Detección de Líneas de Color
- **Secuencial**: `detección_de_linea_de_color_secuencial/`
- **Concurrente**: `detección_de_linea_de_color_concurrente/`
- **Funcionalidad**: Seguimiento de líneas de colores
- **Algoritmos**: Filtrado HSV, detección de contornos

### 3. Detección de Personas
- **Ubicación**: `detección_de_personas_concurrente/`
- **Funcionalidad**: Detección y seguimiento de personas
- **Tecnología**: Mediapipe DE Google y threading
- **Aplicación**: Navegación segura y evitación de obstáculos

### 4. Control de Motores
- **Ubicación**: `raspberry-pi-car/`
- **Funcionalidad**: Control de movimiento del carro
- **Características**: PWM, control de velocidad, giros

## 🧪 Pruebas

### Ejecución de Pruebas

```bash
# Pruebas específicas por módulo
cd [módulo]/tests/
python -m pytest test_*.py -v

# Pruebas de integración
python -m pytest tests/ -v --cov=src/
```

### Pruebas Individuales

```bash
# Probar cámara
python test_x11.py

# Pruebas específicas
cd pruebas_individuales/
python [test_específico].py
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### Error de Permisos USB
```bash
# Verificar permisos
lsusb
sudo usermod -a -G video $USER
# Reiniciar sesión
```

#### Error de Memoria Insuficiente
```bash
# Aumentar swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### Error de Dependencias
```bash
# Reinstalar dependencias
pip install --upgrade --force-reinstall -r requirements.txt
```

### Logs y Depuración

```bash
# Activar modo debug
export DEBUG=1
python src/main.py

# Ver logs del sistema
journalctl -u [servicio] -f


## Scripts extras
## Script para usar camaras EY3D en Jetson Nano
### Requisitos
- **Jetson Nano** con Ubuntu 18.04 o superior
- **Cámara EY3D** conectada
- **Python 3.6+** instalado
### Instalación de Dependencias

```bash
cd programa_para_camara_EY3D/
chmod +x scripts/install_eys3d_dependencies.sh
./scripts/install_eys3d_dependencies.sh

./build_NVIDIA.sh
./run_pipeline_viewer.sh
```


## 🤝 Contribución

1. **Fork** el proyecto
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Estándares de Código

- **PEP 8** para Python
- **Docstrings** en todas las funciones
- **Type hints** cuando sea posible
- **Pruebas unitarias** para nuevas funcionalidades

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
Consideración impotante, la licencia para el subproyecto de uso de camaras EYS3D contiene codigo bajo la licencia Apache 2.0, por lo que se debe de considerar al momento de hacer uso de este subproyecto.

---

## 📞 Soporte

Para soporte técnico o preguntas:

- **Email**: amurillob2000@alumno.ipn.mx
- **Issues**: https://github.com/AlexisInsMu/ProgramaDelfin2025/issues
- **Wiki**: https://github.com/AlexisInsMu/ProgramaDelfin2025/wiki

---

**Programa Delfín 2025** - Desarrollado en el IPN y Tecnologico Nacional de México de Tuxtla Gutiérrez
```
















