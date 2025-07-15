cmake_minimum_required(VERSION 3.12)
project(realsense_cpp)

set(CMAKE_CXX_STANDARD 14)

# Buscar dependencias
find_package(PkgConfig REQUIRED)
pkg_check_modules(REALSENSE2 REQUIRED realsense2)
pkg_check_modules(OPENCV REQUIRED opencv4)

# Buscar pybind11
find_package(pybind11 REQUIRED)

# Crear módulo
pybind11_add_module(realsense_cpp realsense_module.cpp)

# Configurar includes y links
target_include_directories(realsense_cpp PRIVATE ${REALSENSE2_INCLUDE_DIRS} ${OPENCV_INCLUDE_DIRS})
target_link_libraries(realsense_cpp PRIVATE ${REALSENSE2_LIBRARIES} ${OPENCV_LIBRARIES})
target_compile_options(realsense_cpp PRIVATE ${REALSENSE2_CFLAGS_OTHER} ${OPENCV_CFLAGS_OTHER})

# Optimizaciones
target_compile_options(realsense_cpp PRIVATE -O3)