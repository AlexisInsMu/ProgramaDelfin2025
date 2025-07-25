/*
 * eYs3D Simple Viewer
 * Con guardado conservador de imágenes RGB y Depth
 */

#include "EYS3DSystem.h"
#include "devices/CameraDevice.h"
#include "devices/Pipeline.h"
#include "video/Frame.h"
#include "debug.h"

// OpenCV headers
#include <opencv2/opencv.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#include <iostream>
#include <atomic>
#include <thread>
#include <mutex>
#include <cinttypes>
#include <chrono>
#include <sys/stat.h>
#include <dirent.h>
#include <vector>
#include <algorithm>
#include <fstream>
#include <sys/statvfs.h>
#include <unistd.h>

#define LOG_TAG "Simple Viewer"

using namespace libeYs3D;

// Variables globales mínimas
static std::atomic<bool> g_running{true};
static cv::Mat g_colorImage;
static cv::Mat g_depthImage;
static cv::Mat g_depthRaw;
static std::mutex g_colorMutex;
static std::mutex g_depthMutex;
static cv::Mat g_leftImage;   // Imagen izquierda
static cv::Mat g_rightImage;  // Imagen derecha REAL
static std::mutex g_leftMutex;
static std::mutex g_rightMutex;
bool usbON = false;

// ✅ VARIABLES PARA GUARDADO CONSERVADOR
static std::atomic<int> g_target_images{0};
static std::atomic<int> g_saved_count{0};
static std::atomic<bool> g_save_enabled{true};
static std::atomic<bool> g_auto_save_enabled{true};
static int g_save_interval_seconds = 3; // Guardar cada 3 segundos
static std::string g_save_directory = "./saved_images/";
static std::chrono::steady_clock::time_point g_last_save_time;
static std::mutex g_save_mutex;

// ✅ FUNCIÓN CONSERVADORA PARA CREAR DIRECTORIO
bool createDirectory(const std::string &path)
{
    struct stat st = {0};
    if (stat(path.c_str(), &st) == -1)
    {
        if (mkdir(path.c_str(), 0755) == -1)
        {
            LOG_ERR(LOG_TAG, "Error creating directory: %s", path.c_str());
            return false;
        }
    }
    return true;
}
// ✅ FUNCIÓN para detectar si la cámara soporta acceso separado:
bool detectStereoCapabilities(std::shared_ptr<libeYs3D::devices::CameraDevice> device) {
    try {
        // Solo verificar soporte de interleave
        bool supported = device->isInterleaveModeSupported();
        LOG_INFO(LOG_TAG, "Capacidades estéreo: %s", supported ? "✓ DETECTADO" : "✗ NO DETECTADO");
        return supported;
    } catch (...) {
        LOG_WARN(LOG_TAG, "Error detectando capacidades - asumiendo NO estéreo");
        return false;
    }
}
bool saveStereoImageSet(const cv::Mat& leftImg, const cv::Mat& rightImg, const cv::Mat& depthImg, int imageNumber)
{
    try {
        if (leftImg.empty() || rightImg.empty() || depthImg.empty()) {
            LOG_ERR(LOG_TAG, "✗ Una o más imágenes están vacías");
            return false;
        }
        
        std::string timestamp = std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count());
        
        std::string baseFilename = g_save_directory + "stereo_" + std::to_string(imageNumber) + "_" + timestamp;
        
        // Archivos en formato BMP
        std::string leftFile = baseFilename + "_left.bmp";
        std::string rightFile = baseFilename + "_right.bmp";
        std::string depthFile = baseFilename + "_depth.bmp";
        
        // Guardar las tres imágenes
        bool leftSuccess = cv::imwrite(leftFile, leftImg);
        bool rightSuccess = cv::imwrite(rightFile, rightImg);
        bool depthSuccess = cv::imwrite(depthFile, depthImg);
        
        if (leftSuccess && rightSuccess && depthSuccess) {
            LOG_INFO(LOG_TAG, "✓ Conjunto estéreo completo guardado: %s", baseFilename.c_str());
            return true;
        } else {
            LOG_ERR(LOG_TAG, "✗ Error guardando: L=%d R=%d D=%d", 
                    leftSuccess, rightSuccess, depthSuccess);
            return false;
        }
        
    } catch (const std::exception& e) {
        LOG_ERR(LOG_TAG, "Error guardando conjunto estéreo: %s", e.what());
        return false;
    }
}

// ✅ FUNCIÓN CONSERVADORA PARA GUARDAR UN PAR DE IMÁGENES
bool saveImagePair(const cv::Mat &colorImg, const cv::Mat &depthImg, const cv::Mat &rawDepth, int imageNumber)
{
    try
    {
        // ✅ VERIFICACIONES EXHAUSTIVAS ANTES DE GUARDAR
        if (colorImg.empty() || depthImg.empty() || rawDepth.empty())
        {
            LOG_ERR(LOG_TAG, "✗ Imágenes vacías detectadas");
            return false;
        }

        if (colorImg.data == nullptr || depthImg.data == nullptr || rawDepth.data == nullptr)
        {
            LOG_ERR(LOG_TAG, "✗ Punteros de datos nulos");
            return false;
        }

        // ✅ VERIFICAR QUE LAS IMÁGENES SEAN VÁLIDAS
        if (colorImg.rows <= 0 || colorImg.cols <= 0 ||
            depthImg.rows <= 0 || depthImg.cols <= 0 ||
            rawDepth.rows <= 0 || rawDepth.cols <= 0)
        {
            LOG_ERR(LOG_TAG, "✗ Dimensiones inválidas");
            return false;
        }

        LOG_INFO(LOG_TAG, "Color: %dx%d tipo=%d, Depth: %dx%d tipo=%d, Raw: %dx%d tipo=%d",
                 colorImg.cols, colorImg.rows, colorImg.type(),
                 depthImg.cols, depthImg.rows, depthImg.type(),
                 rawDepth.cols, rawDepth.rows, rawDepth.type());

        std::string timestamp = std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(
                                                   std::chrono::system_clock::now().time_since_epoch())
                                                   .count());

        std::string baseFilename = g_save_directory + "img_" + std::to_string(imageNumber) + "_" + timestamp;

        LOG_INFO(LOG_TAG, "Guardando imagen #%d: %s", imageNumber, baseFilename.c_str());

        // ✅ CREAR COPIAS LOCALES PARA EVITAR PROBLEMAS DE CONCURRENCIA
        cv::Mat colorCopy, depthCopy, rawCopy;
        try
        {
            colorCopy = colorImg.clone();
            depthCopy = depthImg.clone();
            rawCopy = rawDepth.clone();
        }
        catch (const cv::Exception &e)
        {
            LOG_ERR(LOG_TAG, "Error clonando matrices: %s", e.what());
            return false;
        }

        // ✅ USAR FORMATOS MÁS SIMPLES Y SEGUROS
        std::string colorFile = baseFilename + "_color.bmp"; // BMP es más simple
        std::string depthFile = baseFilename + "_depth.bmp"; // BMP es más simple
        std::string rawFile = baseFilename + "_raw.bmp";     // BMP es más simple

        bool colorSuccess = false, depthSuccess = false, rawSuccess = false;

        // ✅ GUARDAR UNO POR UNO CON MANEJO DE ERRORES
        try
        {
            LOG_INFO(LOG_TAG, "Guardando color...");
            colorSuccess = cv::imwrite(colorFile, colorCopy);
            if (!colorSuccess)
            {
                LOG_ERR(LOG_TAG, "Error escribiendo archivo color");
            }
        }
        catch (const cv::Exception &e)
        {
            LOG_ERR(LOG_TAG, "OpenCV exception guardando color: %s", e.what());
        }
        catch (const std::exception &e)
        {
            LOG_ERR(LOG_TAG, "Exception guardando color: %s", e.what());
        }

        try
        {
            LOG_INFO(LOG_TAG, "Guardando depth...");
            depthSuccess = cv::imwrite(depthFile, depthCopy);
            if (!depthSuccess)
            {
                LOG_ERR(LOG_TAG, "Error escribiendo archivo depth");
            }
        }
        catch (const cv::Exception &e)
        {
            LOG_ERR(LOG_TAG, "OpenCV exception guardando depth: %s", e.what());
        }
        catch (const std::exception &e)
        {
            LOG_ERR(LOG_TAG, "Exception guardando depth: %s", e.what());
        }

        try
        {
            LOG_INFO(LOG_TAG, "Guardando raw...");
            rawSuccess = cv::imwrite(rawFile, rawCopy);
            if (!rawSuccess)
            {
                LOG_ERR(LOG_TAG, "Error escribiendo archivo raw");
            }
        }
        catch (const cv::Exception &e)
        {
            LOG_ERR(LOG_TAG, "OpenCV exception guardando raw: %s", e.what());
        }
        catch (const std::exception &e)
        {
            LOG_ERR(LOG_TAG, "Exception guardando raw: %s", e.what());
        }

        if (colorSuccess && depthSuccess && rawSuccess)
        {
            LOG_INFO(LOG_TAG, "✓ Guardado exitoso #%d: %s", imageNumber, baseFilename.c_str());
            return true;
        }
        else
        {
            LOG_ERR(LOG_TAG, "✗ Error parcial guardando #%d (C:%d D:%d R:%d)",
                    imageNumber, colorSuccess, depthSuccess, rawSuccess);
            return false;
        }
    }
    catch (const cv::Exception &e)
    {
        LOG_ERR(LOG_TAG, "OpenCV error guardando: %s", e.what());
        return false;
    }
    catch (const std::exception &e)
    {
        LOG_ERR(LOG_TAG, "Error guardando: %s", e.what());
        return false;
    }
    catch (...)
    {
        LOG_ERR(LOG_TAG, "Error desconocido guardando imagen");
        return false;
    }
}

static void color_image_reader(libeYs3D::devices::Pipeline *pipeline)
{
    libeYs3D::video::Frame frame;
    libeYs3D::devices::Pipeline::RESULT ret;

    while (g_running.load())
    {
        ret = pipeline->waitForColorFrame(&frame);
        if (ret < 0)
            break;
        if (ret > 0)
            continue;

        LOG_INFO(LOG_TAG, "[COLOR] Frame: S/N=%" PRIu32, frame.serialNumber);

        if (frame.dataVec.empty() || frame.width <= 0 || frame.height <= 0)
        {
            continue;
        }

        // Convertir YUV a BGR
        cv::Mat colorMat;
        uint8_t *frameData = frame.dataVec.data();
        cv::Mat yuyv(frame.height, frame.width, CV_8UC2, frameData);
        cv::cvtColor(yuyv, colorMat, cv::COLOR_YUV2BGR_YUY2);

        // Actualizar imagen global
        {
            std::lock_guard<std::mutex> lock(g_colorMutex);
            g_colorImage = colorMat.clone();
        }
    }

    LOG_INFO(LOG_TAG, "[COLOR] Thread terminado");
}

static void depth_image_reader(libeYs3D::devices::Pipeline *pipeline)
{
    libeYs3D::video::Frame frame;
    libeYs3D::devices::Pipeline::RESULT ret;

    while (g_running.load())
    {
        ret = pipeline->waitForDepthFrame(&frame);
        if (ret < 0)
            break;
        if (ret > 0)
            continue;

        LOG_INFO(LOG_TAG, "[DEPTH] Frame: S/N=%" PRIu32, frame.serialNumber);

        if (frame.dataVec.empty() || frame.width <= 0 || frame.height <= 0)
        {
            continue;
        }

        // Convertir depth a imagen colorizada
        uint8_t *frameData = frame.dataVec.data();
        cv::Mat depth16(frame.height, frame.width, CV_16UC1, frameData);

        cv::Mat depth8;
        depth16.convertTo(depth8, CV_8UC1, 255.0 / 2047.0);

        cv::Mat depthColorized;
        cv::applyColorMap(depth8, depthColorized, cv::COLORMAP_JET);

        // Actualizar imagen global
        {
            std::lock_guard<std::mutex> lock(g_depthMutex);
            g_depthImage = depthColorized.clone();
            g_depthRaw = depth16.clone(); // ✅ GUARDAR RAW TAMBIÉN
        }
    }

    LOG_INFO(LOG_TAG, "[DEPTH] Thread terminado");
}


std::vector<std::string> getUSBDevices()
{
    std::vector<std::string> devices;

    // Common USB mount points in Linux
    std::vector<std::string> mountPaths = {
        "/media",
        "/mnt",
        "/run/media"};

    for (const auto &basePath : mountPaths)
    {
        DIR *dir = opendir(basePath.c_str());
        if (dir == nullptr)
            continue;

        struct dirent *entry;
        while ((entry = readdir(dir)) != nullptr)
        {
            if (entry->d_type == DT_DIR &&
                strcmp(entry->d_name, ".") != 0 &&
                strcmp(entry->d_name, "..") != 0)
            {

                // Check if it's a user directory
                std::string userPath = basePath + "/" + entry->d_name;
                DIR *userDir = opendir(userPath.c_str());
                if (userDir != nullptr)
                {
                    struct dirent *userEntry;
                    while ((userEntry = readdir(userDir)) != nullptr)
                    {
                        if (userEntry->d_type == DT_DIR &&
                            strcmp(userEntry->d_name, ".") != 0 &&
                            strcmp(userEntry->d_name, "..") != 0)
                        {

                            std::string devicePath = userPath + "/" + userEntry->d_name;

                            // Verify it's writable and has space
                            struct stat st;
                            if (stat(devicePath.c_str(), &st) == 0 &&
                                access(devicePath.c_str(), W_OK) == 0)
                            {
                                devices.push_back(devicePath);
                            }
                        }
                    }
                    closedir(userDir);
                }
            }
        }
        closedir(dir);
    }

    // Also check direct mount points
    DIR *mediaDir = opendir("/media");
    if (mediaDir != nullptr)
    {
        struct dirent *entry;
        while ((entry = readdir(mediaDir)) != nullptr)
        {
            if (entry->d_type == DT_DIR &&
                strcmp(entry->d_name, ".") != 0 &&
                strcmp(entry->d_name, "..") != 0)
            {

                std::string devicePath = "/media/" + std::string(entry->d_name);
                struct stat st;
                if (stat(devicePath.c_str(), &st) == 0 &&
                    access(devicePath.c_str(), W_OK) == 0)
                {
                    devices.push_back(devicePath);
                }
            }
        }
        closedir(mediaDir);
    }

    // Remove duplicates and sort
    std::sort(devices.begin(), devices.end());
    devices.erase(std::unique(devices.begin(), devices.end()), devices.end());

    return devices;
}

// ✅ FUNCTION TO GET DEVICE INFO
std::string getDeviceInfo(const std::string &path)
{
    std::string info = path;

    // Try to get filesystem info
    struct statvfs vfs;
    if (statvfs(path.c_str(), &vfs) == 0)
    {
        unsigned long long totalSpace = vfs.f_blocks * vfs.f_frsize;
        unsigned long long freeSpace = vfs.f_bavail * vfs.f_frsize;

        // Convert to MB
        double totalMB = totalSpace / (1024.0 * 1024.0);
        double freeMB = freeSpace / (1024.0 * 1024.0);

        info += " (" + std::to_string((int)freeMB) + "MB free / " +
                std::to_string((int)totalMB) + "MB total)";
    }

    return info;
}

// ✅ IMPROVED USB DEVICE SELECTION
std::string list_usb_devices()
{
    while (true)
    {
        system("clear");
        std::cout << "=== Dispositivos USB Detectados ===\n\n";

        std::vector<std::string> devices = getUSBDevices();

        if (devices.empty())
        {
            std::cout << "❌ No se encontraron dispositivos USB montados.\n";
            std::cout << "   Intenta montar tu USB manualmente:\n";
            std::cout << "   sudo mkdir -p /mnt/usb\n";
            std::cout << "   sudo mount /dev/sdb1 /mnt/usb\n\n";
            std::cout << "Opciones:\n";
            std::cout << "  L - Usar directorio local (./saved_images/)\n";
            std::cout << "  R - Refrescar lista\n";
            std::cout << "  Q - Salir\n";
            std::cout << "\nSelección: ";
        }
        else
        {
            std::cout << "Dispositivos encontrados:\n\n";

            // ✅ SHOW INDEXED LIST
            for (size_t i = 0; i < devices.size(); ++i)
            {
                std::cout << "  [" << i << "] " << getDeviceInfo(devices[i]) << "\n";
            }

            std::cout << "\nOpciones:\n";
            std::cout << "  0-" << (devices.size() - 1) << " - Seleccionar dispositivo USB\n";
            std::cout << "  L - Usar directorio local (./saved_images/)\n";
            std::cout << "  R - Refrescar lista\n";
            std::cout << "  Q - Salir\n";
            std::cout << "\nSelección: ";
        }

        char choice;
        std::cin >> choice;
        choice = toupper(choice);

        if (choice == 'Q')
        {
            return "";
        }
        else if (choice == 'L')
        {
            std::cout << "\n✓ Usando directorio local: ./saved_images/\n";
            return "./saved_images/";
        }
        else if (choice == 'R')
        {
            continue; // Refresh the list
        }
        else if (choice >= '0' && choice <= '9')
        {
            int index = choice - '0';
            if (index >= 0 && index < (int)devices.size())
            {
                std::string selectedPath = devices[index];

                // ✅ VERIFY DEVICE IS STILL ACCESSIBLE
                struct stat st;
                if (stat(selectedPath.c_str(), &st) == 0 &&
                    access(selectedPath.c_str(), W_OK) == 0)
                {

                    std::cout << "\n✓ Dispositivo seleccionado: " << selectedPath << std::endl;

                    // ✅ CREATE TEST FILE TO VERIFY WRITE ACCESS
                    std::string testFile = selectedPath + "/.write_test";
                    std::ofstream test(testFile);
                    if (test.is_open())
                    {
                        test << "test";
                        test.close();
                        std::remove(testFile.c_str());

                        std::cout << "✓ Acceso de escritura verificado\n";
                        std::cout << "Presiona Enter para continuar...";
                        std::cin.ignore();
                        std::cin.get();
                        usbON = true; // Set USB flag
                        return selectedPath;
                    }
                    else
                    {
                        std::cout << "❌ Error: No se puede escribir en este dispositivo\n";
                        std::cout << "Presiona Enter para continuar...";
                        std::cin.ignore();
                        std::cin.get();
                    }
                }
                else
                {
                    std::cout << "❌ Error: Dispositivo no accesible: " << selectedPath << std::endl;
                    std::cout << "Presiona Enter para continuar...";
                    std::cin.ignore();
                    std::cin.get();
                }
            }
            else
            {
                std::cout << "❌ Índice inválido: " << index << std::endl;
                std::cout << "Presiona Enter para continuar...";
                std::cin.ignore();
                std::cin.get();
            }
        }
        else
        {
            std::cout << "❌ Selección inválida. Inténtalo de nuevo.\n";
            std::cout << "Presiona Enter para continuar...";
            std::cin.ignore();
            std::cin.get();
        }
    }
    return "";
}

// Verificador de memoria disponible
bool hasEnoughMemory(std::string path)
{
    struct statvfs vfs;
    if (statvfs(path.c_str(), &vfs) != 0)
    {
        // No se pudo obtener información del sistema de archivos
        return false;
    }
    unsigned long long freeBytes = vfs.f_bavail * vfs.f_frsize;
    unsigned long long requiredBytes = 1024 * 1024 * 1024; // 1 GB requerido
    return freeBytes >= requiredBytes;
}
static void right_image_reader(libeYs3D::devices::Pipeline *pipeline, bool isStereoDevice)
{
    LOG_INFO(LOG_TAG, "Iniciando thread de imagen derecha...");
    
    if (!isStereoDevice) {
        LOG_INFO(LOG_TAG, "Modo simulación para cámara derecha");
        
        // Modo simulación para cámaras no estéreo
        while (g_running.load()) {
            cv::Mat rightSimulated;
            
            {
                std::lock_guard<std::mutex> lock(g_colorMutex);
                if (!g_colorImage.empty()) {
                    cv::Mat grayImage;
                    cv::cvtColor(g_colorImage, grayImage, cv::COLOR_BGR2GRAY);
                    cv::cvtColor(grayImage, rightSimulated, cv::COLOR_GRAY2BGR);
                    
                    cv::putText(rightSimulated, "RIGHT (SIMULATED)", cv::Point(10, 30), 
                               cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 0, 255), 2);
                }
            }
            
            if (!rightSimulated.empty()) {
                std::lock_guard<std::mutex> lock(g_rightMutex);
                g_rightImage = rightSimulated.clone();
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(33));
        }
        return;
    }
    
    // ✅ MODO REAL para cámaras estéreo
    libeYs3D::video::Frame rightFrame;
    libeYs3D::devices::Pipeline::RESULT ret;
    
    while (g_running.load()) {
        try {
            // En modo interleave, los frames pueden venir alternados
            // Frame par = izquierda, Frame impar = derecha
            
            ret = pipeline->waitForColorFrame(&rightFrame);
            if (ret < 0) break;
            if (ret > 0) continue;
            
            // Verificar si este frame corresponde a la cámara derecha
            // (esto depende de la implementación específica del dispositivo)
            bool isRightFrame = (rightFrame.serialNumber % 2 == 1); // Ejemplo: frames impares
            
            if (!isRightFrame) {
                continue; // Saltar frames de cámara izquierda
            }
            
            LOG_INFO(LOG_TAG, "[RIGHT] Frame REAL: S/N=%" PRIu32, rightFrame.serialNumber);
            
            if (rightFrame.dataVec.empty()) continue;
            
            // Procesar frame derecho
            cv::Mat rightMat;
            uint8_t *frameData = rightFrame.dataVec.data();
            cv::Mat yuyv(rightFrame.height, rightFrame.width, CV_8UC2, frameData);
            cv::cvtColor(yuyv, rightMat, cv::COLOR_YUV2BGR_YUY2);
            
            // Agregar marca de identificación
            cv::putText(rightMat, "RIGHT CAMERA (REAL)", cv::Point(10, 30), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 0, 255), 2);
            
            // Actualizar imagen derecha global
            {
                std::lock_guard<std::mutex> lock(g_rightMutex);
                g_rightImage = rightMat.clone();
            }
            
        } catch (const std::exception& e) {
            LOG_ERR(LOG_TAG, "Error en imagen derecha: %s", e.what());
        }
    }
    
    LOG_INFO(LOG_TAG, "[RIGHT] Thread terminado");
}

static void left_image_reader(libeYs3D::devices::Pipeline *pipeline)
{
    libeYs3D::video::Frame frame;
    libeYs3D::devices::Pipeline::RESULT ret;

    while (g_running.load())
    {
        ret = pipeline->waitForColorFrame(&frame);
        if (ret < 0) break;
        if (ret > 0) continue;

        LOG_INFO(LOG_TAG, "[LEFT] Frame: S/N=%" PRIu32, frame.serialNumber);

        if (frame.dataVec.empty() || frame.width <= 0 || frame.height <= 0) {
            continue;
        }

        // Convertir YUV a BGR para imagen izquierda
        cv::Mat leftMat;
        uint8_t *frameData = frame.dataVec.data();
        cv::Mat yuyv(frame.height, frame.width, CV_8UC2, frameData);
        cv::cvtColor(yuyv, leftMat, cv::COLOR_YUV2BGR_YUY2);

        // Agregar marca de identificación
        cv::putText(leftMat, "LEFT CAMERA", cv::Point(10, 30), 
                   cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 255, 0), 2);

        // Actualizar imagen izquierda global
        {
            std::lock_guard<std::mutex> lock(g_colorMutex);
            g_colorImage = leftMat.clone(); // Mantener compatibilidad
        }
        
        // También actualizar variable específica izquierda si existe
        {
            std::lock_guard<std::mutex> lock(g_leftMutex);
            g_leftImage = leftMat.clone();
        }
    }

    LOG_INFO(LOG_TAG, "[LEFT] Thread terminado");
}
// ✅ REEMPLAZAR display_thread() COMPLETA (líneas 369-485):
static void display_thread()
{
    // ✅ CREAR TRES VENTANAS SEPARADAS
    cv::namedWindow("Left Camera", cv::WINDOW_AUTOSIZE);
    cv::namedWindow("Right Camera", cv::WINDOW_AUTOSIZE);
    cv::namedWindow("Depth Map", cv::WINDOW_AUTOSIZE);
    
    // Posicionar ventanas
    cv::moveWindow("Left Camera", 50, 100);
    cv::moveWindow("Right Camera", 350, 100);
    cv::moveWindow("Depth Map", 650, 100);

    LOG_INFO(LOG_TAG, "Presiona 'q' para salir, 's' para activar auto-guardado, 'x' para desactivar");
    g_last_save_time = std::chrono::steady_clock::now();

    while (g_running.load())
    {
        cv::Mat leftDisplay, rightDisplay, depthDisplay;
        bool hasLeft = false, hasRight = false, hasDepth = false;

        // ✅ OBTENER IMAGEN IZQUIERDA
        {
            std::lock_guard<std::mutex> lock(g_leftMutex);
            if (!g_leftImage.empty()) {
                leftDisplay = g_leftImage.clone();
                hasLeft = true;
            }
        }

        // ✅ OBTENER IMAGEN DERECHA
        {
            std::lock_guard<std::mutex> lock(g_rightMutex);
            if (!g_rightImage.empty()) {
                rightDisplay = g_rightImage.clone();
                hasRight = true;
            }
        }

        // ✅ OBTENER PROFUNDIDAD
        {
            std::lock_guard<std::mutex> lock(g_depthMutex);
            if (!g_depthImage.empty()) {
                depthDisplay = g_depthImage.clone();
                hasDepth = true;
            }
        }

        // ✅ LÓGICA DE GUARDADO PARA TRES IMÁGENES
        if (hasLeft && hasRight && hasDepth && g_auto_save_enabled.load()) {
            std::lock_guard<std::mutex> saveLock(g_save_mutex);
            
            auto currentTime = std::chrono::steady_clock::now();
            auto timeSinceLastSave = std::chrono::duration_cast<std::chrono::seconds>(
                currentTime - g_last_save_time);

            if (timeSinceLastSave.count() >= g_save_interval_seconds) {
                int currentCount = g_saved_count.load();
                int targetCount = g_target_images.load();

                if (currentCount < targetCount) {
                    LOG_INFO(LOG_TAG, "Guardando conjunto estéreo %d/%d...", 
                             currentCount + 1, targetCount);

                    // ✅ USAR saveStereoImageSet EN LUGAR DE saveImagePair
                    if (saveStereoImageSet(leftDisplay, rightDisplay, depthDisplay, currentCount + 1)) {
                        int newCount = g_saved_count.fetch_add(1) + 1;
                        g_last_save_time = currentTime;

                        LOG_INFO(LOG_TAG, "✓ Conjunto estéreo guardado: %d/%d", newCount, targetCount);

                        if (newCount >= targetCount) {
                            LOG_INFO(LOG_TAG, "✓ Auto-guardado completado: %d conjuntos", newCount);
                            g_auto_save_enabled.store(false);
                        }
                    }
                }
            }
        }

        // ✅ MOSTRAR TRES VENTANAS
        if (hasLeft) {
            cv::Mat displayLeft = leftDisplay.clone();
            
            std::string info = "Conjuntos: " + std::to_string(g_saved_count.load()) + 
                              "/" + std::to_string(g_target_images.load());
            cv::putText(displayLeft, info, cv::Point(10, 450), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 0), 2);
            
            if (g_auto_save_enabled.load()) {
                cv::putText(displayLeft, "AUTO-SAVE ACTIVO", cv::Point(10, 420), 
                           cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 255, 255), 2);
                
                // Countdown
                auto currentTime = std::chrono::steady_clock::now();
                auto timeSinceLastSave = std::chrono::duration_cast<std::chrono::seconds>(
                    currentTime - g_last_save_time);
                int timeLeft = g_save_interval_seconds - timeSinceLastSave.count();
                if (timeLeft > 0) {
                    std::string countdown = "Siguiente en: " + std::to_string(timeLeft) + "s";
                    cv::putText(displayLeft, countdown, cv::Point(10, 390),
                               cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(255, 255, 255), 2);
                }
            } else {
                cv::putText(displayLeft, "Presiona 's' para activar", cv::Point(10, 420), 
                           cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(255, 255, 0), 2);
            }
            
            cv::imshow("Left Camera", displayLeft);
        }

        if (hasRight) {
            cv::Mat displayRight = rightDisplay.clone();
            cv::putText(displayRight, "RIGHT CAMERA", cv::Point(10, 30), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(0, 0, 255), 2);
            cv::imshow("Right Camera", displayRight);
        }

        if (hasDepth) {
            cv::Mat displayDepth = depthDisplay.clone();
            cv::putText(displayDepth, "DEPTH MAP", cv::Point(10, 30), 
                       cv::FONT_HERSHEY_SIMPLEX, 0.8, cv::Scalar(255, 255, 0), 2);
            cv::imshow("Depth Map", displayDepth);
        }

        // Manejo de teclas
        int key = cv::waitKey(30) & 0xFF;
        if (key == 'q' || key == 27) {
            g_running.store(false);
            break;
        } else if (key == 's') {
            if (!g_auto_save_enabled.load()) {
                g_auto_save_enabled.store(true);
                g_last_save_time = std::chrono::steady_clock::now();
                LOG_INFO(LOG_TAG, "Auto-guardado activado cada %d segundos", g_save_interval_seconds);
            }
        } else if (key == 'x') {
            g_auto_save_enabled.store(false);
            LOG_INFO(LOG_TAG, "Auto-guardado desactivado");
        }
    }

    cv::destroyAllWindows();
    LOG_INFO(LOG_TAG, "Display terminado. Total guardado: %d conjuntos estéreo", g_saved_count.load());
}

int main(int argc, char **argv)
{
    g_save_enabled.store(true);
    LOG_INFO(LOG_TAG, "Starting Simple eYs3D Viewer with Image Saving...");
    
    std::string usb_device = list_usb_devices();
    if (usb_device.empty())
    {
        LOG_INFO(LOG_TAG, "No USB device selected, using local directory.");
        g_save_directory = "./saved_images/";
    }
    else
    {
        g_save_directory = usb_device;
        if (g_save_directory.back() != '/')
        {
            g_save_directory += "/";
        }
        g_save_directory += "eys3d_images/";
        LOG_INFO(LOG_TAG, "✓ USB seleccionado: %s", g_save_directory.c_str());
    }

    // ✅ CONFIGURAR NÚMERO DE IMÁGENES A GUARDAR
    int n_images = 5;
    if (argc > 1)
    {
        n_images = std::atoi(argv[1]);
        if (n_images <= 0)
            n_images = 5;
    }
    else
    {
        std::cout << "¿Cuántas imágenes desea capturar? (-1 para ilimitado, por defecto 5): ";
        std::cin >> n_images;
        if (n_images == -1) {
            n_images = INT_MAX; // Modo ilimitado
            LOG_INFO(LOG_TAG, "✓ Modo ilimitado activado");
        } else if (n_images <= 0) {
            n_images = 5;
        }
    }

    // ✅ AGREGAR CONFIGURACIÓN DE INTERVALO CUSTOM
    int custom_interval = 3;
    if (argc > 2) {
        custom_interval = std::atoi(argv[2]);
        if (custom_interval < 1 || custom_interval > 60) {
            custom_interval = 3;
        }
    } else {
        std::cout << "¿Cada cuántos SEGUNDOS quiere guardar imágenes? (1-60, por defecto 3): ";
        std::cin >> custom_interval;
        if (custom_interval < 1 || custom_interval > 60) {
            custom_interval = 3;
            LOG_INFO(LOG_TAG, "⚠ Intervalo fuera de rango. Usando 3 segundos por defecto");
        }
    }
    
    g_save_interval_seconds = custom_interval; // ✅ ASIGNAR VALOR CUSTOM
    g_target_images.store(n_images);
    
    if (n_images == INT_MAX) {
        LOG_INFO(LOG_TAG, "✓ Configurado para captura ILIMITADA cada %d segundos", g_save_interval_seconds);
    } else {
        LOG_INFO(LOG_TAG, "✓ Configurado para capturar %d imágenes cada %d segundos", n_images, g_save_interval_seconds);
    }

    // ✅ CREAR DIRECTORIO DE GUARDADO
    if (!createDirectory(g_save_directory))
    {
        LOG_ERR(LOG_TAG, "No se pudo crear directorio: %s", g_save_directory.c_str());
        return -1;
    }

    std::cout << "Imágenes se guardarán en: " << g_save_directory << std::endl;
    std::cout << "Intervalo configurado: " << g_save_interval_seconds << " segundos\n" << std::endl;

    // Inicializar sistema
    std::shared_ptr<EYS3DSystem> eYs3DSystem =
        std::make_shared<EYS3DSystem>(EYS3DSystem::COLOR_BYTE_ORDER::COLOR_BGR24);

    if (0 == eYs3DSystem->getCameraDeviceCount())
    {
        LOG_ERR(LOG_TAG, "No camera devices found...");
        return -1;
    }

    std::shared_ptr<libeYs3D::devices::CameraDevice> device =
        eYs3DSystem->getCameraDevice(0);

    if (!device)
    {
        LOG_ERR(LOG_TAG, "Unable to get camera device...");
        return -1;
    }

    bool isStereoDevice = detectStereoCapabilities(device);
    
    if (isStereoDevice) {
        LOG_INFO(LOG_TAG, "✓ Cámara estéreo detectada - habilitando modo interleave");
        
        // Habilitar modo interleave para acceso a ambas cámaras
        int result = device->enableInterleaveMode(true);
        if (result == 0) {
            LOG_INFO(LOG_TAG, "✓ Modo interleave habilitado exitosamente");
        } else {
            LOG_WARN(LOG_TAG, "⚠ Error habilitando modo interleave: %d", result);
        }
    } else {
        LOG_INFO(LOG_TAG, "⚠ Cámara no estéreo o sin soporte - usando simulación para cámara derecha");
    }

    // ✅ CONFIGURAR PIPELINE con formato específico para estéreo
    std::shared_ptr<libeYs3D::devices::Pipeline> pipeline;
    
    if (isStereoDevice) {
        // Configuración optimizada para cámaras estéreo
        pipeline = device->initStream(
            libeYs3D::video::COLOR_RAW_DATA_TYPE::COLOR_RAW_DATA_YUY2,
            640, 480, 15,
            libeYs3D::video::DEPTH_RAW_DATA_TYPE::DEPTH_RAW_DATA_11_BITS,
            640, 480,
            DEPTH_IMG_COLORFUL_TRANSFER,
            IMAGE_SN_SYNC,
            0);
    } else {
        // Configuración estándar para cámaras simples
        pipeline = device->initStream(
            libeYs3D::video::COLOR_RAW_DATA_TYPE::COLOR_RAW_DATA_YUY2,
            640, 480, 15,
            libeYs3D::video::DEPTH_RAW_DATA_TYPE::DEPTH_RAW_DATA_11_BITS,
            640, 480,
            DEPTH_IMG_COLORFUL_TRANSFER,
            IMAGE_SN_SYNC,
            0);
    }
    if (!pipeline)
    {
        LOG_ERR(LOG_TAG, "Failed to initialize pipeline");
        return -1;
    }

     LOG_INFO(LOG_TAG, "Pipeline configurado: 640x480@15fps");

    // ✅ INICIAR THREADS ESPECÍFICOS PARA ESTÉREO
    std::thread leftThread([&]() { left_image_reader(pipeline.get()); });
    std::thread rightThread([&]() { right_image_reader(pipeline.get(), isStereoDevice); });
    std::thread depthThread([&]() { depth_image_reader(pipeline.get()); });
    std::thread displayThread(display_thread);

    // Habilitar stream
    device->enableStream();
    LOG_INFO(LOG_TAG, "Stream iniciado. Presiona 's' para activar auto-guardado, 'q' para salir.");

    // Esperar a que termine el display
    displayThread.join();

    // ✅ CLEANUP - TERMINAR TODOS LOS THREADS
    g_running.store(false);
    device->closeStream();

    if (leftThread.joinable()) leftThread.join();
    if (rightThread.joinable()) rightThread.join();
    if (depthThread.joinable()) depthThread.join();

    LOG_INFO(LOG_TAG, "Simple Viewer terminado. %d conjuntos estéreo guardados.", g_saved_count.load());
    return 0;
}