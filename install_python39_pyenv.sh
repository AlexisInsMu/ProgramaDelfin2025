#!/bin/bash

echo "=== Instalación de Python 3.9 con pyenv y configuración de pyrealsense2 ==="

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Instalar dependencias necesarias para compilar Python
echo "[INFO] Instalando dependencias para compilar Python..."
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev git

# Instalar pyenv si no está instalado
if ! command_exists pyenv; then
    echo "[INFO] Instalando pyenv..."
    curl https://pyenv.run | bash
    
    # Agregar pyenv al PATH
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    
    # Cargar pyenv en la sesión actual
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
else
    echo "[INFO] pyenv ya está instalado"
fi

# Instalar Python 3.9.19 (última versión de 3.9)
echo "[INFO] Instalando Python 3.9.19..."
pyenv install 3.9.19

# Configurar Python 3.9 como versión local para el proyecto
echo "[INFO] Configurando Python 3.9 como versión local..."
cd /home/pi/Documentos/new_direc/ProgramaDelfin2025
pyenv local 3.9.19

# Verificar la instalación
echo "[INFO] Verificando instalación de Python 3.9..."
python --version
pip --version

# Crear ambiente virtual con Python 3.9
echo "[INFO] Creando ambiente virtual con Python 3.9..."
python -m venv venv_py39_realsense
source venv_py39_realsense/bin/activate

# Verificar que estamos en el ambiente virtual
echo "[INFO] Verificando ambiente virtual..."
which python
python --version

# Actualizar pip
echo "[INFO] Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias básicas
echo "[INFO] Instalando dependencias básicas..."
pip install numpy opencv-python matplotlib

# Compilar e instalar pyrealsense2 desde el código fuente
echo "[INFO] Compilando pyrealsense2 desde código fuente..."
cd ~/librealsense/build

# Limpiar build anterior
make clean || true

# Configurar con CMAKE para Python 3.9
cmake .. -DBUILD_PYTHON_BINDINGS=bool:true \
         -DPYTHON_EXECUTABLE=$(which python) \
         -DPYTHON_INCLUDE_DIR=$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
         -DPYTHON_LIBRARY=$(python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")/libpython3.9.so \
         -DCMAKE_BUILD_TYPE=Release

# Compilar
make -j1

# Instalar
sudo make install

# Instalar el binding de Python
cd wrappers/python
python setup.py build
python setup.py install

# Volver al directorio del proyecto
cd /home/pi/Documentos/new_direc/ProgramaDelfin2025

# Crear script de activación
cat > activate_py39_realsense.sh << 'EOF'
#!/bin/bash
echo "Activando ambiente Python 3.9 con RealSense..."
cd /home/pi/Documentos/new_direc/ProgramaDelfin2025
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
source venv_py39_realsense/bin/activate
echo "Ambiente activado: $(python --version)"
EOF

chmod +x activate_py39_realsense.sh

# Probar pyrealsense2
echo "[INFO] Probando pyrealsense2..."
python -c "
import pyrealsense2 as rs
print('✅ pyrealsense2 importado correctamente')
print('Versión:', rs.__version__ if hasattr(rs, '__version__') else 'N/A')
print('Atributos disponibles:', len([x for x in dir(rs) if not x.startswith('_')]))
try:
    ctx = rs.context()
    devices = ctx.query_devices()
    print('Dispositivos RealSense detectados:', len(devices))
    for i, device in enumerate(devices):
        print(f'  Dispositivo {i}: {device.get_info(rs.camera_info.name)}')
except Exception as e:
    print('Error al detectar dispositivos:', e)
"

echo "[INFO] ¡Configuración completada!"
echo "Para activar el ambiente, ejecuta: source activate_py39_realsense.sh"
