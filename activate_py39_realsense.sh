#!/bin/bash
echo "Activando ambiente Python 3.9 con RealSense..."
cd /home/pi/Documentos/new_direc/ProgramaDelfin2025
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
source venv_py39_realsense/bin/activate
echo "Ambiente activado: $(python --version)"
