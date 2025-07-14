# Navega al directorio del módulo
cd /home/pi/Documentos/new_direc/ProgramaDelfin2025/detección_de_arucos_de_color_concurrente/src/sensors/realsense_cpp

# Limpia compilaciones anteriores
rm -rf build/ dist/ *.egg-info/

# Asegura que estás en el entorno virtual correcto
pyenv activate venv_py39_realsense

# Reconstruye el módulo
python setup.py build_ext --inplace

# Verifica la creación del archivo .so
ls -l realsense_cpp*.so

# Prueba el módulo
cd ..
python -c "import sys; sys.path.insert(0, '.'); import realsense_cpp; print('Módulo cargado correctamente')"