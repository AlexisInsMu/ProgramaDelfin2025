#include <librealsense2/rs.hpp>
#include <iostream>
#include <vector>

int main() {
    try {
        std::cout << "=== Verificando RealSense C++ API ===" << std::endl;
        
        // Crear contexto
        rs2::context ctx;
        std::cout << "✅ rs2::context creado" << std::endl;
        
        // Listar dispositivos
        std::vector<rs2::device> devices = ctx.query_devices();
        std::cout << "✅ Dispositivos encontrados: " << devices.size() << std::endl;
        
        if (devices.empty()) {
            std::cout << "❌ No se encontraron dispositivos RealSense" << std::endl;
            return 1;
        }
        
        // Mostrar información de dispositivos
        for (size_t i = 0; i < devices.size(); ++i) {
            rs2::device device = devices[i];
            std::cout << "  Dispositivo " << i << ": " 
                      << device.get_info(RS2_CAMERA_INFO_NAME) << std::endl;
            std::cout << "    Serial: " 
                      << device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER) << std::endl;
        }
        
        // Crear pipeline
        rs2::pipeline pipeline;
        std::cout << "✅ rs2::pipeline creado" << std::endl;
        
        // Crear configuración
        rs2::config config;
        config.enable_stream(RS2_STREAM_DEPTH, 640, 480, RS2_FORMAT_Z16, 30);
        std::cout << "✅ rs2::config configurado" << std::endl;
        
        // Iniciar pipeline
        rs2::pipeline_profile profile = pipeline.start(config);
        std::cout << "✅ Pipeline iniciado" << std::endl;
        
        // Obtener algunos frames
        for (int i = 0; i < 5; ++i) {
            rs2::frameset frames = pipeline.wait_for_frames();
            rs2::depth_frame depth = frames.get_depth_frame();
            
            if (depth) {
                std::cout << "✅ Frame " << i << " - Dimensiones: " 
                          << depth.get_width() << "x" << depth.get_height() << std::endl;
                
                // Obtener distancia en el centro
                float distance = depth.get_distance(320, 240);
                std::cout << "  Distancia en centro: " << distance << "m" << std::endl;
            }
        }
        
        // Detener pipeline
        pipeline.stop();
        std::cout << "✅ Pipeline detenido" << std::endl;
        
        std::cout << "=== Todas las funciones C++ funcionan correctamente ===" << std::endl;
        return 0;
        
    } catch (const rs2::error & e) {
        std::cerr << "❌ Error RealSense: " << e.what() << std::endl;
        return 1;
    } catch (const std::exception & e) {
        std::cerr << "❌ Error: " << e.what() << std::endl;
        return 1;
    }
}