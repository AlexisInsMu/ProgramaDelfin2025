#!/bin/bash

# filepath: /home/pi/Documentos/new_direc/ProgramaDelfin2025/detección_de_arucos_de_color_concurrente/scripts/start_on_boot.sh
echo "=== Configuración para iniciar detección de Arucos de Color Concurrente al arrancar ==="
# Verificar si el script de instalación de dependencias existe
if [ ! -f "/home/pi/Documentos/new_direc/ProgramaDelf
in2025/detección_de_arucos_de_color_concurrente/scripts/install_dependencies.sh" ]; then
    echo "❌ El script de instalación de dependencias no existe. Por favor, verifica la ruta."
    exit 1
fi

echo "=== Activando ambiente RealSense ==="

# Activar ambiente virtual
source ../../robot_env_new/bin/activate

# Configurar variables de entorno
export PYTHONPATH="$VIRTUAL_ENV/lib/python3.11/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH"

# Verificar que todo esté bien
echo "✓ Ambiente virtual: $VIRTUAL_ENV"
echo "✓ PYTHONPATH: $PYTHONPATH"
echo "✓ LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# Verificar RealSense
python -c "import pyrealsense2 as rs; print('✓ RealSense disponible:', rs.__version__)" 2>/dev/null || echo "⚠ RealSense no encontrado"

echo "=== Ambiente RealSense activado ==="
echo "Para usar: python tu_script.py"