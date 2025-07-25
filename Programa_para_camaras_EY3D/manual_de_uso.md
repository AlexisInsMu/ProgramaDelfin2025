## Manual de uso el programa de captura de imagenes eYs3D

## Requisitos previos 
[Instalación de dependencias](install_eys3d_dependencies.sh)
Antes de ejecutar el programa, asegúrese de que su sistema cumpla con los requisitos necesarios. Si está utilizando una NVIDIA Jetson Nano,
debe instalar las dependencias necesarias ejecutando el siguiente script:
```bash
sudo bash install_eys3d_dependencies.sh
```
>[!WARNING]
> Si ya se instalo las dependencias no es necesario volver a ejecutar este script.


> [!NOTE] 
> Este script está diseñado específicamente para la NVIDIA Jetson Nano. Si está utilizando otro sistema, es posible que deba instalar las dependencias manualmente.


## Uso del programa

Ejecute 
```bash
./build_NVIDIA.sh
```
para compilar el programa. Luego, ejecute el programa con el 
Debes de considerar que antes de ejecutar el programa, debes de asegurarte de que tu cámara eYs3D esté conectada correctamente a la NVIDIA Jetson Nano.

Una vez que hayas compilado el programa, puedes ejecutarlo con el
siguiente comando:
```bash
./run_pipeline_viewer.sh
```

Una vez que el programa esté en ejecución, deberías ver una ventana de visualización de la cámara eYs3D. Puedes interactuar con la interfaz para capturar imágenes y realizar otras acciones según las funcionalidades implementadas.
Inicialemente pedira 
```bash
Ingrese el número de imágenes a capturar:
```
Debes ingresar un número entero que represente la cantidad de imágenes que deseas capturar. Por
ejemplo, si deseas capturar 10 imágenes, ingresa `10` y presiona Enter.

Luego pedirá el intervalo de tiempo entre capturas:
```bash
Ingrese el intervalo de tiempo entre capturas (en segundos):
```
Debes ingresar un número entero que represente el intervalo de tiempo en segundos entre cada captura de imagen. Por ejemplo, si deseas un intervalo de 2 segundos, ingresa `2` y presiona Enter.
Después de ingresar estos valores, el programa comenzará a capturar imágenes de la cámara eYs3D según los parámetros especificados. Las imágenes se guardarán en un directorio específico dentro del proyecto.

> [!NOTE]
> Para salir del programa, puedes presionar `Ctrl + C` en la terminal donde se está ejecutando el script.
> O bien puedes seleccionar una de las ventanas emergentes que se abrirán y presionar la tecla `q` para salir de la ventana de visualización.


## Contactos
En caso de presentar algún problema o tener alguna duda, puedes contactar a los siguientes correos electrónicos:
- **Alexis Novo**: amurillob2000@alumno.ipn.mx>
