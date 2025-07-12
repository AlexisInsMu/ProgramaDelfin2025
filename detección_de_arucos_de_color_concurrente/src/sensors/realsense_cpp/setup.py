from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension
import subprocess
import os

# Obtener flags de pkg-config
def get_pkg_config_flags(package):
    try:
        cflags = subprocess.check_output(['pkg-config', '--cflags', package]).decode().strip().split()
        libs = subprocess.check_output(['pkg-config', '--libs', package]).decode().strip().split()
        return cflags, libs
    except subprocess.CalledProcessError:
        return [], []

# Obtener flags de RealSense
rs_cflags, rs_libs = get_pkg_config_flags('realsense2')

# Solo usar RealSense por ahora, sin OpenCV
include_dirs = [
    "/usr/local/include",
    "/usr/include",
]

# Definir extensión solo con RealSense
ext_modules = [
    Pybind11Extension(
        "realsense_cpp",
        ["realsense_module.cpp"],
        include_dirs=include_dirs,
        libraries=["realsense2"],
        library_dirs=["/usr/local/lib", "/usr/lib"],
        cxx_std=14,
        extra_compile_args=rs_cflags + ["-O3"],
        extra_link_args=rs_libs,
    ),
]

setup(
    name="realsense_cpp",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)