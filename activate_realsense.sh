#!/bin/bash
echo "=== Activando RealSense ==="
source robot_env_new/bin/activate
export PYTHONPATH="$VIRTUAL_ENV/lib/python3.11/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH"
echo "✓ Variables configuradas"
python -c "import pyrealsense2 as rs; print('✓ RealSense listo')" 2>/dev/null || echo "⚠ Conecta la cámara"
