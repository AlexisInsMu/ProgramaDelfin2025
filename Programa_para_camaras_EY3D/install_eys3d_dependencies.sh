#!/bin/bash

# Script de instalación y configuración para eYs3D en Jetson Nano
# Ejecutar como: sudo bash install_eys3d_dependencies.sh

echo "=== Instalador de dependencias para eYs3D en Jetson Nano ==="

# Verificar si estamos en Jetson Nano
if [ ! -f /etc/nv_tegra_release ]; then
    echo "⚠️  Advertencia: Este script está diseñado para NVIDIA Jetson Nano"
    echo "   Continuando de todas maneras..."
fi

# Actualizar sistema
echo "📦 Actualizando sistema..."
apt update
apt upgrade -y

# Instalar dependencias del sistema
echo "🔧 Instalando dependencias del sistema..."
apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    pkg-config \
    libusb-1.0-0-dev \
    libhidapi-dev \
    libudev-dev \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gfortran \
    openexr \
    libatlas-base-dev \
    python3-numpy \
    libtbb2 \
    libtbb-dev \
    libdc1394-22-dev \
    libgtk2.0-dev \
    libmp3lame-dev \
    libtheora-dev \
    libvorbis-dev \
    libxvidcore-dev \
    libx264-dev \
    libopencore-amrnb-dev \
    libopencore-amrwb-dev \
    libavresample-dev \
    x264 \
    v4l-utils

# Instalar Python packages
echo "🐍 Instalando paquetes de Python..."
pip3 install --upgrade pip
pip3 install \
    numpy \
    opencv-python \
    Pillow \
    matplotlib \
    scipy

# Verificar instalación de OpenCV
echo "🔍 Verificando instalación de OpenCV..."
python3 -c "import cv2; print(f'OpenCV versión: {cv2.__version__}')"

# Configurar permisos para USB
echo "🔐 Configurando permisos USB..."
usermod -a -G dialout $USER
usermod -a -G video $USER

# Crear reglas udev para cámaras eYs3D
echo "📝 Creando reglas udev para cámaras eYs3D..."
cat > /etc/udev/rules.d/99-eys3d-camera.rules << 'EOF'
# eYs3D Camera Rules
SUBSYSTEM=="usb", ATTR{idVendor}=="1e4e", MODE="0666", GROUP="video"
SUBSYSTEM=="usb", ATTR{idVendor}=="04b4", MODE="0666", GROUP="video"
SUBSYSTEM=="usb", ATTR{idVendor}=="0547", MODE="0666", GROUP="video"
KERNEL=="video*", SUBSYSTEM=="video4linux", MODE="0666", GROUP="video"
EOF

# Recargar reglas udev
udevadm control --reload-rules
udevadm trigger

echo "✅ Instalación completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Reinicia el sistema para aplicar cambios de permisos"
echo "2. Conecta tu cámara eYs3D"
echo "3. Verifica la conexión con: lsusb"
echo "4. Ejecuta el programa Python: python3 eys3d_pipeline.py"
echo ""
echo "🔧 Para verificar que la cámara está conectada:"
echo "   lsusb | grep -i eys3d"
echo "   v4l2-ctl --list-devices"
echo ""
echo "⚠️  Nota: Si hay problemas con permisos, ejecuta:"
echo "   sudo usermod -a -G video \$USER"
echo "   sudo usermod -a -G dialout \$USER"
echo "   Luego cierra sesión y vuelve a iniciar sesión"
