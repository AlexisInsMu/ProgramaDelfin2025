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

## Contactos
En caso de presentar algún problema o tener alguna duda, puedes contactar a los siguientes correos electrónicos:
- **Alexis Novo**: amurillob2000@alumno.ipn.mx>
