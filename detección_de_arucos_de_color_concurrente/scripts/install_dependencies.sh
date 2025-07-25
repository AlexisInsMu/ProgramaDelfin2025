#!/bin/bash
# filepath: /home/pi/Documentos/new_direc/ProgramaDelfin2025/install_dependencies.sh

echo "=== Instalación Completa Intel RealSense D455 para Raspberry Pi 4 ==="

# Verificar ambiente virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Activa tu ambiente virtual primero:"
    echo "source robot_env_new/bin/activate"
    exit 1
fi

echo "✓ Ambiente virtual: $VIRTUAL_ENV"

# Directorio de trabajo
WORK_DIR="/home/pi/Documentos/new_direc/ProgramaDelfin2025"
cd "$WORK_DIR"

# PASO 1: Instalar dependencias del sistema
echo "📦 Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y git cmake build-essential libssl-dev libusb-1.0-0-dev 
sudo apt install -y pkg-config libgtk-3-dev libglfw3-dev 
sudo apt install -y libgl1-mesa-dev libglu1-mesa-dev python3-dev python3-numpy
sudo apt install -y libudev-dev dkms

# PASO 2: Clonar librealsense
echo "📥 Clonando librealsense..."
if [ -d "librealsense" ]; then
    echo "Directorio librealsense existe, actualizando..."
    cd librealsense
    git pull
    git clean -fd
    rm -rf build
    cd ..
else
    git clone https://github.com/IntelRealSense/librealsense.git
fi

cd librealsense

# PASO 3: Configurar permisos USB
echo "🔧 Configurando permisos USB..."
sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

# PASO 4: Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip install numpy cython setuptools wheel pybind11

# PASO 5: Configurar memoria (importante para compilación)
echo "💾 Configurando memoria virtual..."
# Aumentar swap temporalmente
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# PASO 6: Compilar librealsense
echo "🔨 Compilando librealsense (esto puede tomar 60-90 minutos)..."
mkdir -p build
cd build

# Configurar cmake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_PYTHON_BINDINGS:bool=true \
    -DPYTHON_EXECUTABLE="$VIRTUAL_ENV/bin/python" \
    -DBUILD_EXAMPLES=false \
    -DBUILD_GRAPHICAL_EXAMPLES=false \
    -DBUILD_UNIT_TESTS=false \
    -DBUILD_TOOLS=true \
    -DFORCE_RSUSB_BACKEND=true \
    -DBUILD_WITH_CUDA=false \
    -DCMAKE_INSTALL_PREFIX="$VIRTUAL_ENV" \
    -DPYTHON_INSTALL_DIR="$VIRTUAL_ENV/lib/python3.11/site-packages"

if [ $? -ne 0 ]; then
    echo "❌ Error en configuración cmake"
    exit 1
fi

# Compilar (usar menos cores para evitar problemas de memoria)
FREE_RAM=$(free -m | awk 'NR==2{print $7}')
if [ $FREE_RAM -lt 500 ]; then
    CORES=1
elif [ $FREE_RAM -lt 1000 ]; then
    CORES=2
else
    CORES=3
fi

echo "Compilando con $CORES cores..."
make -j$CORES

if [ $? -ne 0 ]; then
    echo "❌ Error en compilación, reintentando con 1 core..."
    make clean
    make -j1
    if [ $? -ne 0 ]; then
        echo "❌ Compilación falló completamente"
        exit 1
    fi
fi

# PASO 7: Instalar
echo "📦 Instalando librealsense..."
make install

# PASO 8: Configurar variables de entorno
echo "🔧 Configurando variables de entorno..."
echo "export PYTHONPATH=\"$VIRTUAL_ENV/lib/python3.11/site-packages:\$PYTHONPATH\"" >> "$VIRTUAL_ENV/bin/activate"
echo "export LD_LIBRARY_PATH=\"$VIRTUAL_ENV/lib:\$LD_LIBRARY_PATH\"" >> "$VIRTUAL_ENV/bin/activate"

# Aplicar variables ahora
export PYTHONPATH="$VIRTUAL_ENV/lib/python3.11/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH"

# PASO 9: Restaurar swap original
echo "💾 Restaurando configuración de swap..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=100/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# PASO 10: Verificar instalación
echo "🧪 Verificando instalación..."
python -c "import pyrealsense2 as rs; print('✓ pyrealsense2 importado correctamente'); print('Versión:', rs.__version__)"

if [ $? -eq 0 ]; then
    echo "🎉 ¡Instalación completada exitosamente!"
    echo ""
    echo "Para usar RealSense:"
    echo "1. Conecta la cámara D455 a un puerto USB 3.0"
    echo "2. Activa el ambiente virtual: source robot_env_new/bin/activate"
    echo "3. Ejecuta: python -c \"import pyrealsense2 as rs; print('RealSense OK')\""
else
    echo "❌ Error en la verificación"
    exit 1
fi

echo "=== Instalación finalizada ==="