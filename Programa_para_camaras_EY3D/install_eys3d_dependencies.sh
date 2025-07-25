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
# Instalar OpenCV
sudo apt install libopencv-dev python3-opencv
# Instalar eYs3D SDK
echo "📥 Instalando eYs3D SDK...


echo "✅ Instalación completada!"

