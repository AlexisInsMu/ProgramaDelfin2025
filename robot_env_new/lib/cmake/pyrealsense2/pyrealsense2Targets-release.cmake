#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "pyrealsense2::pyrsutils" for configuration "Release"
set_property(TARGET pyrealsense2::pyrsutils APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(pyrealsense2::pyrsutils PROPERTIES
  IMPORTED_LOCATION_RELEASE "/home/pi/Documentos/new_direc/ProgramaDelfin2025/robot_env_new/lib/python3.11/site-packages/pyrealsense2/pyrsutils.cpython-311-aarch64-linux-gnu.so.2.55.1"
  IMPORTED_SONAME_RELEASE "pyrsutils.cpython-311-aarch64-linux-gnu.so.2.55"
  )

list(APPEND _cmake_import_check_targets pyrealsense2::pyrsutils )
list(APPEND _cmake_import_check_files_for_pyrealsense2::pyrsutils "/home/pi/Documentos/new_direc/ProgramaDelfin2025/robot_env_new/lib/python3.11/site-packages/pyrealsense2/pyrsutils.cpython-311-aarch64-linux-gnu.so.2.55.1" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
