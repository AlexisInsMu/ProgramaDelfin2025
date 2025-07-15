#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <librealsense2/rs.hpp>
// Comentar OpenCV por ahora
// #include <opencv2/opencv.hpp>
#include <thread>
#include <mutex>
#include <atomic>
#include <vector>
#include <algorithm>
#include <chrono>
#include <iostream>

class RealSenseDistanceSensor {
private:
    rs2::pipeline pipeline;
    rs2::config config;
    rs2::frameset frames;
    // Cambiar de rs2::depth_frame a un puntero opcional
    std::unique_ptr<rs2::depth_frame> current_depth_frame;
    std::unique_ptr<rs2::video_frame> current_color_frame;
    
    std::mutex frame_mutex;
    std::atomic<bool> is_streaming{false};
    std::thread capture_thread;
    
    int width, height, fps;
    float depth_scale;
    
    // Filtros para mejorar calidad
    rs2::spatial_filter spatial_filter;
    rs2::temporal_filter temporal_filter;
    rs2::hole_filling_filter hole_filling_filter;
    
    void capture_loop() {
        while (is_streaming) {
            try {
                auto frames = pipeline.wait_for_frames(1000);
                auto depth = frames.get_depth_frame();
                auto color = frames.get_color_frame();
                
                if (depth) {
                    // Aplicar filtros
                    depth = spatial_filter.process(depth);
                    depth = temporal_filter.process(depth);
                    depth = hole_filling_filter.process(depth);
                    
                    std::lock_guard<std::mutex> lock(frame_mutex);
                    current_depth_frame = std::make_unique<rs2::depth_frame>(depth);
                }
                if(color){
                    std::lock_guard<std::mutex> lock(frame_mutex);
                    current_color_frame = std::make_unique<rs2::video_frame>(color);
                }
            } catch (const rs2::error& e) {
                std::cerr << "RealSense error: " << e.what() << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        }
    }
    
public:
    RealSenseDistanceSensor(int w = 640, int h = 480, int f = 30) 
        : width(w), height(h), fps(f), depth_scale(0.001f), current_depth_frame(nullptr) {
        
        // Configurar filtros
        spatial_filter.set_option(RS2_OPTION_FILTER_MAGNITUDE, 2);
        spatial_filter.set_option(RS2_OPTION_FILTER_SMOOTH_ALPHA, 0.5f);
        spatial_filter.set_option(RS2_OPTION_FILTER_SMOOTH_DELTA, 20);
        
        std::cout << "✓ RealSense C++ Distance Sensor inicializado" << std::endl;
    }
    
    bool start_streaming() {
        try {
            // Verificar dispositivos
            rs2::context ctx;
            auto devices = ctx.query_devices();
            if (devices.size() == 0) {
                std::cerr << "❌ No se encontraron dispositivos RealSense" << std::endl;
                return false;
            }
            
            // Configurar stream
            config.enable_stream(RS2_STREAM_DEPTH, width, height, RS2_FORMAT_Z16, fps);
            config.enable_stream(RS2_STREAM_COLOR, width, height, RS2_FORMAT_RGB8, fps);
            
            // Iniciar pipeline
            auto profile = pipeline.start(config);
            
            // Obtener escala de profundidad
            auto depth_sensor = profile.get_device().first<rs2::depth_sensor>();
            depth_scale = depth_sensor.get_depth_scale();
            
            std::cout << "✓ Depth Scale: " << depth_scale << std::endl;
            
            is_streaming = true;
            capture_thread = std::thread(&RealSenseDistanceSensor::capture_loop, this);
            
            std::cout << "✓ RealSense C++ streaming iniciado" << std::endl;
            return true;
            
        } catch (const rs2::error& e) {
            std::cerr << "❌ Error al iniciar RealSense: " << e.what() << std::endl;
            return false;
        }
    }
    
    float get_distance(int x = -1, int y = -1, int region_size = 20) {
        std::lock_guard<std::mutex> lock(frame_mutex);
        
        if (!current_depth_frame) {
            return 0.0f;
        }
        
        // Usar centro si no se especifican coordenadas
        if (x < 0 || y < 0) {
            x = width / 2;
            y = height / 2;
        }
        
        // Validar coordenadas
        if (x < 0 || x >= width || y < 0 || y >= height) {
            return 0.0f;
        }
        
        try {
            // Definir región
            int half_region = region_size / 2;
            int x_start = std::max(0, x - half_region);
            int x_end = std::min(width, x + half_region);
            int y_start = std::max(0, y - half_region);
            int y_end = std::min(height, y + half_region);
            
            std::vector<float> valid_depths;
            
            // Recopilar valores válidos en la región
            for (int py = y_start; py < y_end; py++) {
                for (int px = x_start; px < x_end; px++) {
                    float depth = current_depth_frame->get_distance(px, py);
                    if (depth > 0) {
                        valid_depths.push_back(depth);
                    }
                }
            }
            
            if (!valid_depths.empty()) {
                // Calcular mediana
                std::sort(valid_depths.begin(), valid_depths.end());
                return valid_depths[valid_depths.size() / 2];
            }
            
            return 0.0f;
            
        } catch (const std::exception& e) {
            std::cerr << "Error obteniendo distancia: " << e.what() << std::endl;
            return 0.0f;
        }
    }
    
    float get_distance_center() {
        return get_distance();
    }
    
    bool is_obstacle_detected(float threshold = 0.3f, int x = -1, int y = -1) {
        float distance = get_distance(x, y);
        return (distance > 0) && (distance < threshold);
    }
    
    std::tuple<float, int, int> get_closest_obstacle(float min_distance = 0.1f, float max_distance = 2.0f) {
        std::lock_guard<std::mutex> lock(frame_mutex);
        
        if (!current_depth_frame) {
            return std::make_tuple(0.0f, -1, -1);
        }
        
        float min_dist = max_distance;
        int closest_x = -1, closest_y = -1;
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                float depth = current_depth_frame->get_distance(x, y);
                if (depth > min_distance && depth < min_dist) {
                    min_dist = depth;
                    closest_x = x;
                    closest_y = y;
                }
            }
        }
        
        if (closest_x >= 0) {
            return std::make_tuple(min_dist, closest_x, closest_y);
        }
        
        return std::make_tuple(0.0f, -1, -1);
    }
    
    pybind11::array_t<float> get_distance_array() {
        std::lock_guard<std::mutex> lock(frame_mutex);
        
        if (!current_depth_frame) {
            return pybind11::array_t<float>();
        }
        
        auto result = pybind11::array_t<float>(width * height);
        auto buf = result.request();
        float* ptr = static_cast<float*>(buf.ptr);
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                ptr[y * width + x] = current_depth_frame->get_distance(x, y);
            }
        }
        
        result.resize({height, width});
        return result;
    }
    
    // capturar la imagen de profundidad actual
    pybind11::array_t<uint16_t> get_current_depth_image() {
        std::lock_guard<std::mutex> lock(frame_mutex);
        if (!current_depth_frame) {
            return pybind11::array_t<uint16_t>();
        }
        auto result = pybind11::array_t<uint16_t>({height, width});
        auto buf = result.request();
        uint16_t* ptr = static_cast<uint16_t*>(buf.ptr);
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                ptr[y * width + x] = static_cast<uint16_t>(current_depth_frame->get_distance(x, y) / depth_scale);
            }
        }
        return result;
    }

    pybind11::array_t<uint8_t> get_image_rgb(){
        std::lock_guard<std::mutex> lock(frame_mutex);
    
        if (!current_color_frame) {
            return pybind11::array_t<uint8_t>();
        }
        
        // Crear un array RGB
        auto result = pybind11::array_t<uint8_t>({height, width, 3});
        auto buf = result.request();
        uint8_t* ptr = static_cast<uint8_t*>(buf.ptr);
        
        // Copiar los datos del frame de color
        const uint8_t* color_data = static_cast<const uint8_t*>(current_color_frame->get_data());
        std::memcpy(ptr, color_data, width * height * 3);
        
        return result;
    }
    
    void stop_streaming() {
        is_streaming = false;
        
        if (capture_thread.joinable()) {
            capture_thread.join();
        }
        
        try {
            pipeline.stop();
            std::cout << "✓ RealSense C++ streaming detenido" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error deteniendo pipeline: " << e.what() << std::endl;
        }
    }
    
    ~RealSenseDistanceSensor() {
        if (is_streaming) {
            stop_streaming();
        }
    }
};

// Binding de pybind11
PYBIND11_MODULE(realsense_cpp, m) {
    m.doc() = "RealSense C++ Distance Sensor";
    
    pybind11::class_<RealSenseDistanceSensor>(m, "RealSenseDistanceSensor")
        .def(pybind11::init<int, int, int>(), 
             pybind11::arg("width") = 640, 
             pybind11::arg("height") = 480, 
             pybind11::arg("fps") = 30)
        .def("start_streaming", &RealSenseDistanceSensor::start_streaming)
        .def("get_distance", &RealSenseDistanceSensor::get_distance,
             pybind11::arg("x") = -1, 
             pybind11::arg("y") = -1, 
             pybind11::arg("region_size") = 20)
        .def("get_distance_center", &RealSenseDistanceSensor::get_distance_center)
        .def("is_obstacle_detected", &RealSenseDistanceSensor::is_obstacle_detected,
             pybind11::arg("threshold") = 0.3f,
             pybind11::arg("x") = -1,
             pybind11::arg("y") = -1)
        .def("get_closest_obstacle", &RealSenseDistanceSensor::get_closest_obstacle,
             pybind11::arg("min_distance") = 0.1f,
             pybind11::arg("max_distance") = 2.0f)
        .def("get_distance_array", &RealSenseDistanceSensor::get_distance_array)
        .def("get_current_depth_image", &RealSenseDistanceSensor::get_current_depth_image)
        .def("get_image_rgb", &RealSenseDistanceSensor::get_image_rgb)
        .def("stop_streaming", &RealSenseDistanceSensor::stop_streaming);
}