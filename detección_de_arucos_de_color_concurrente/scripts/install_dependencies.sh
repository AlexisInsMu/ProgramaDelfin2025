#!/bin/bash
# filepath: /home/pi/Documentos/new_direc/ProgramaDelfin2025/detección_de_arucos_de_color_concurrente/scripts/install_dependencies.sh

echo "=== Instalación de Intel RealSense en ambiente virtual ==="

# Verificar que estamos en el ambiente virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ No se detectó ambiente virtual activo."
    echo "Activa tu ambiente virtual primero:"
    echo "source robot_env_new/bin/activate"
    exit 1
fi

echo "✓ Ambiente virtual detectado: $VIRTUAL_ENV"

# Obtener directorio base del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Directorio del script: $SCRIPT_DIR"

# Navegar al directorio del script
cd "$SCRIPT_DIR"

# PASO 1: Instalar dependencias del sistema
echo "Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y git cmake build-essential libssl-dev libusb-1.0-0-dev 
sudo apt install -y pkg-config libgtk-3-dev libglfw3-dev 
sudo apt install -y libgl1-mesa-dev libglu1-mesa-dev python3-dev python3-numpy
sudo apt install -y libudev-dev

# PASO 2: Actualizar herramientas de Python en el venv
echo "Actualizando herramientas de Python en ambiente virtual..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install numpy cython

# PASO 3: Verificar/limpiar instalación anterior
LIBREALSENSE_DIR="$SCRIPT_DIR/librealsense"

if [ -d "$LIBREALSENSE_DIR" ]; then
    echo "Directorio librealsense encontrado en: $LIBREALSENSE_DIR"
    echo "¿Deseas limpiar instalación anterior? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Limpiando instalación anterior..."
        cd "$LIBREALSENSE_DIR"
        rm -rf build
        git clean -fd
        git reset --hard HEAD
    else
        echo "Continuando con instalación existente..."
        cd "$LIBREALSENSE_DIR"
    fi
else
    echo "Clonando repositorio librealsense en: $LIBREALSENSE_DIR"
    git clone https://github.com/IntelRealSense/librealsense.git "$LIBREALSENSE_DIR"
    cd "$LIBREALSENSE_DIR"
fi

# Verificar que estamos en el directorio correcto
if [ ! -f "CMakeLists.txt" ]; then
    echo "❌ Error: No se encontró CMakeLists.txt en $(pwd)"
    echo "Verifica que el repositorio se haya clonado correctamente"
    exit 1
fi

echo "✓ CMakeLists.txt encontrado en: $(pwd)"

# PASO 4: Configurar permisos USB
echo "Configurando permisos USB..."
if [ -f "config/99-realsense-libusb.rules" ]; then
    sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger
    echo "✓ Permisos USB configurados"
else
    echo "⚠ Archivo de reglas USB no encontrado, continuando..."
fi

# PASO 5: Verificar recursos del sistema
echo "Verificando recursos del sistema..."
free -h
df -h .

# Verificar espacio (necesitamos al menos 2GB)
available_space_kb=$(df . | tail -1 | awk '{print $4}')
available_space_gb=$((available_space_kb / 1024 / 1024))

if [ $available_space_gb -lt 2 ]; then
    echo "⚠ ADVERTENCIA: Poco espacio disponible ($available_space_gb GB)"
    echo "Liberando espacio..."
    sudo apt autoremove -y
    sudo apt autoclean
fi

# Ajustar cores según RAM disponible
available_ram_mb=$(free -m | awk 'NR==2{print $7}')
if [ $available_ram_mb -lt 500 ]; then
    CORES=1
    echo "Usando 1 core (RAM: ${available_ram_mb}MB)"
elif [ $available_ram_mb -lt 1000 ]; then
    CORES=2
    echo "Usando 2 cores (RAM: ${available_ram_mb}MB)"
else
    CORES=3
    echo "Usando 3 cores (RAM: ${available_ram_mb}MB)"
fi

# PASO 6: Configurar build
BUILD_DIR="$LIBREALSENSE_DIR/build"
echo "Configurando build en: $BUILD_DIR"

# Crear y entrar al directorio build
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Verificar que estamos en el directorio build correcto
if [ "$(pwd)" != "$BUILD_DIR" ]; then
    echo "❌ Error: No se pudo acceder al directorio build"
    exit 1
fi

echo "Directorio de trabajo actual: $(pwd)"
echo "Directorio padre: $(dirname $(pwd))"

# Obtener paths del ambiente virtual
PYTHON_EXECUTABLE="$VIRTUAL_ENV/bin/python"
PYTHON_VERSION=$($PYTHON_EXECUTABLE -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

# Usar sysconfig en lugar de distutils (deprecado)
PYTHON_INCLUDE_DIR=$($PYTHON_EXECUTABLE -c "import sysconfig; print(sysconfig.get_path('include'))")
PYTHON_LIBRARY=$($PYTHON_EXECUTABLE -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")/libpython${PYTHON_VERSION}.so

echo "Python ejecutable: $PYTHON_EXECUTABLE"
echo "Python versión: $PYTHON_VERSION"
echo "Python include: $PYTHON_INCLUDE_DIR"
echo "Python library: $PYTHON_LIBRARY"

# Verificar que el archivo padre CMakeLists.txt existe
PARENT_CMAKE="$LIBREALSENSE_DIR/CMakeLists.txt"
if [ ! -f "$PARENT_CMAKE" ]; then
    echo "❌ Error: No se encontró $PARENT_CMAKE"
    exit 1
fi

# Configurar cmake con paths específicos del venv
echo "Ejecutando cmake desde: $(pwd)"
echo "Apuntando a: $LIBREALSENSE_DIR"

cmake "$LIBREALSENSE_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_PYTHON_BINDINGS:bool=true \
    -DPYTHON_EXECUTABLE="$PYTHON_EXECUTABLE" \
    -DPYTHON_INCLUDE_DIR="$PYTHON_INCLUDE_DIR" \
    -DPYTHON_LIBRARY="$PYTHON_LIBRARY" \
    -DBUILD_EXAMPLES=false \
    -DBUILD_GRAPHICAL_EXAMPLES=false \
    -DBUILD_UNIT_TESTS=false \
    -DBUILD_TOOLS=false \
    -DFORCE_RSUSB_BACKEND=true \
    -DBUILD_WITH_CUDA=false \
    -DCMAKE_INSTALL_PREFIX="$VIRTUAL_ENV"

if [ $? -ne 0 ]; then
    echo "❌ Error en configuración cmake"
    echo "Verifica que el ambiente virtual esté correctamente activado"
    echo "Y que todas las dependencias estén instaladas"
    exit 1
fi

echo "✓ Configuración cmake exitosa"

# PASO 7: Compilar
echo "Iniciando compilación en: $(pwd)"
echo "Esto puede tomar 45-90 minutos..."

# Compilar con reintentos
for attempt in 1 2 3; do
    echo "Intento $attempt de 3..."
    
    if make -j$CORES; then
        echo "✓ Compilación exitosa"
        break
    else
        echo "❌ Compilación falló en intento $attempt"
        if [ $attempt -eq 3 ]; then
            echo "Todos los intentos fallaron."
            echo "Intenta manualmente con: cd $BUILD_DIR && make -j1"
            exit 1
        fi
        
        make clean
        CORES=$((CORES > 1 ? CORES - 1 : 1))
        echo "Reintentando con $CORES cores..."
        sleep 5
    fi
done

# PASO 8: Instalar en el ambiente virtual
echo "Instalando en ambiente virtual..."
make install

if [ $? -ne 0 ]; then
    echo "❌ Error en la instalación"
    exit 1
fi

# PASO 9: Configurar Python path en el venv
echo "Configurando Python path..."
SITE_PACKAGES="$VIRTUAL_ENV/lib/python${PYTHON_VERSION}/site-packages"

# Buscar donde se instaló pyrealsense2
POSSIBLE_REALSENSE_PATHS=(
    "$VIRTUAL_ENV/lib/python${PYTHON_VERSION}/pyrealsense2"
    "$VIRTUAL_ENV/lib/python${PYTHON_VERSION}/site-packages/pyrealsense2"
    "$VIRTUAL_ENV/lib/pyrealsense2"
)

REALSENSE_LIB=""
for path in "${POSSIBLE_REALSENSE_PATHS[@]}"; do
    if [ -d "$path" ]; then
        REALSENSE_LIB="$path"
        echo "✓ pyrealsense2 encontrado en: $REALSENSE_LIB"
        break
    fi
done

# Crear enlace simbólico si es necesario
if [ -n "$REALSENSE_LIB" ] && [ "$REALSENSE_LIB" != "$SITE_PACKAGES/pyrealsense2" ]; then
    mkdir -p "$SITE_PACKAGES"
    ln -sf "$REALSENSE_LIB" "$SITE_PACKAGES/" 2>/dev/null || cp -r "$REALSENSE_LIB" "$SITE_PACKAGES/"
fi

# PASO 10: Verificar instalación
echo "Verificando instalación..."
if python -c "import pyrealsense2 as rs; print('✓ pyrealsense2 importado correctamente'); print('Versión:', rs.__version__)" 2>/dev/null; then
    echo "🎉 ¡Instalación en ambiente virtual completada exitosamente!"
    
    # Agregar al activate script del venv para persistencia
    if [ -n "$REALSENSE_LIB" ]; then
        echo "# RealSense Python bindings" >> "$VIRTUAL_ENV/bin/activate"
        echo "export PYTHONPATH=\"$REALSENSE_LIB:\$PYTHONPATH\"" >> "$VIRTUAL_ENV/bin/activate"
    fi
    
else
    echo "⚠ Instalación completada pero hay problemas de importación"
    if [ -n "$REALSENSE_LIB" ]; then
        echo "Intenta agregar manualmente al PYTHONPATH:"
        echo "export PYTHONPATH=\"$REALSENSE_LIB:\$PYTHONPATH\""
    fi
    
    # Mostrar posibles ubicaciones para debug
    echo "Buscando pyrealsense2 en:"
    find "$VIRTUAL_ENV" -name "*pyrealsense*" -type d 2>/dev/null || echo "No encontrado"
fi

echo "=== Instalación finalizada ==="
echo "Directorio de trabajo final: $(pwd)"
echo "Para usar en tu proyecto, asegúrate de que el ambiente virtual esté activo"