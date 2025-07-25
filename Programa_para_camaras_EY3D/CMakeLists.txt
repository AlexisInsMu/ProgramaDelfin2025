cmake_minimum_required(VERSION 3.10)
project(eys3d)
set(CMAKE_FIND_DEBUG_MODE TRUE)
set(CMAKE_DEBUG_TARGET_PROPERTIES TRUE)

set(CMAKE_CXX_STANDARD 17)  # ← CAMBIAR de 14 a 17 para std::filesystem

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE RelWithDebInfo)#Release Debug RelWithDebInfo
    message(STATUS "Build type not specify, default type is Release")
endif(NOT CMAKE_BUILD_TYPE)

add_definitions(-DUSE_OPENCL)

# Buscar OpenCV, Threads y filesystem
find_package(OpenCV REQUIRED)
find_package(Threads REQUIRED)

# ← AGREGAR: Para std::filesystem en C++17
find_package(PkgConfig REQUIRED)

include_directories(
        include/
        include/DMPreview_utility
        include/DMPreview_utility/sqlite3
        include/devices/
        include/devices/controller
        include/devices/model
        include/sensors
        lib/eSPDI/
        ${OpenCV_INCLUDE_DIRS}
        )

link_directories(${CMAKE_CURRENT_SOURCE_DIR}/lib
        ${CMAKE_CURRENT_SOURCE_DIR}/lib/eSPDI/
        )

set(DEPENDENCY_LIBS
                eSPDI_${ESPDI_PLATFORM_NAME}
                eys3d.${ESPDI_PLATFORM_NAME})

set(CMAKE_INSTALL_RPATH ${CMAKE_CURRENT_SOURCE_DIR}/lib)
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# Test file source
## (1) Target is callback.test
set(TEST_SRC src/callback_main.cpp)
add_executable(callback.test ${TEST_SRC})
target_link_libraries(callback.test ${DEPENDENCY_LIBS})
       
### (2) Target is pipeline.test
set(TEST_SRC src/pipeline_main.cpp)
add_executable(pipeline.test ${TEST_SRC})
target_link_libraries(pipeline.test ${DEPENDENCY_LIBS})

# ### (3) Target is frameset_pipeline.test
set(TEST_SRC src/frameset_pipeline_main.cpp)
add_executable(frameset_pipeline.test ${TEST_SRC})
target_link_libraries(frameset_pipeline.test ${DEPENDENCY_LIBS})

set(TEST_SRC src/pipeline_viewer.cpp)
add_executable(pipeline_viewer.test ${TEST_SRC})


target_link_libraries(pipeline_viewer.test
            ${DEPENDENCY_LIBS}
            ${OpenCV_LIBS}
            Threads::Threads
            )

# Install eys3d and eYs3D.test to out folder
install(TARGETS callback.test pipeline.test frameset_pipeline.test pipeline_viewer.test
            LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/out
            RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/out)

install(DIRECTORY eYs3D/ DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/out/eYs3D)