# Flappy Bird con Visión Artificial 

Un juego estilo Flappy Bird que se controla **con la mano** a través de la webcam.
No se necesita teclado ni ratón: el pájaro aletea cuando **juntas el pulgar y el
índice (pinza)**, o abriendo la mano si lo prefieres (y con ESPACIO como respaldo).

Se abren **dos ventanas**: la del juego (pygame) y la de la cámara (OpenCV), que
muestra en directo la mano detectada y el gesto reconocido.

## ¿Cómo funciona?

```
                 ┌─────────────────── proceso "cámara" ───────────────────┐
Webcam --> OpenCV --> MediaPipe (HandLandmarker) --> gesto (pinza) --> eventos JSON
                 └───────────────────────────┬───────────────────────────┘
                                             │ stdout (una línea JSON por evento)
                                             ▼
                                    pygame (juego a 60 FPS)
```

1. **OpenCV** captura los fotogramas de la webcam y abre la ventana de la cámara.
2. **MediaPipe** (la librería de Google) detecta 21 puntos (*landmarks*) de la mano.
3. Se reconocen los gestos con esos puntos:
   - **Pinza** (pulgar e índice juntos) → el pájaro aletea.
   - **Mano abierta / puño** → alternativa si usas `--gesture open` o `both`.
4. La detección corre en un **proceso aparte** y envía eventos al juego por stdout
   (líneas JSON). Así la ventana de la cámara y la del juego no se bloquean.

Para aletear hay que **hacer el gesto** (se detecta el flanco de subida), no vale
mantenerlo: hay que separar y volver a juntar los dedos. Además hay un pequeño
tiempo de espera (*cooldown*) entre aleteos.

> Un puño cerrado **no** cuenta como pinza: se comprueba además que el dedo
> índice no esté recogido, para distinguir la pinza real de un puño.

## Requisitos

- Python 3.10 – 3.14 (probado con **3.14.8**)
- Una webcam (`/dev/video0` en Linux)
- Linux/macOS/Windows con entorno gráfico

## Instalación

```bash
cd flappybird_vision

# 1. Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

> Nota: `mediapipe`, `opencv` y `pygame` son pesados (~200 MB en total).
> La primera instalación puede tardar varios minutos.

> Este proyecto ya viene con un entorno `venv/` listo para usar:
> basta con `venv/bin/python main.py`. Si lo copias a otra máquina,
> recrea el entorno con los pasos de arriba.

### Modelo de MediaPipe

El detector de manos necesita el archivo
`assets/hand_landmarker.task`. Ya está incluido, pero si falta puedes
descargarlo así:

```bash
mkdir -p assets
curl -L -o assets/hand_landmarker.task \
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
```

### Nota sobre las fuentes (pygame)

Si tu instalación de `pygame` no incluye SDL_ttf (ocurre cuando se compila
desde fuente en algunos sistemas), el módulo `pygame.font` puede fallar.
El proyecto lo detecta automáticamente y usa `pygame._freetype` como
respaldo, por lo que el juego funciona igual.

## Ejecución

**Importante:** usa el Python del entorno virtual, no el del sistema.
Si ejecutas `python3 main.py` sin activar el venv verás
`ModuleNotFoundError: No module named 'pygame'`.

La forma más fácil es el lanzador incluido:

```bash
./run.sh
```

O bien activando el entorno virtual:

```bash
source venv/bin/activate
python main.py
```

O llamando directamente al Python del venv:

```bash
venv/bin/python main.py
```

### Opciones de línea de comandos

```bash
./run.sh --help

./run.sh --camera 1              # usar otra cámara
./run.sh --no-vision            # jugar solo con teclado (sin cámara)
./run.sh --no-camera-window     # detecta pero NO abre la ventana de la cámara
./run.sh --gesture open         # aletear abriendo la mano en vez de con pinza
./run.sh --gesture both         # aceptar pinza y mano abierta
./run.sh --pinch-threshold 0.2  # pinza más estricta (hay que juntar más los dedos)
./run.sh --pinch-threshold 0.3  # pinza más fácil de activar
./run.sh --no-mirror            # no espejar la imagen de la cámara
./run.sh --max-hands 1          # nº máximo de manos a detectar
```

`--pinch-threshold` es la distancia pulgar-índice **relativa al tamaño de la
palma**. Cuanto menor, más tienen que tocarse los dedos. Por defecto `0.25`
(los dedos deben estar a menos de ~25 px). Súbelo si te cuesta activarlo y
bájalo si se activa solo.

### Gestos disponibles (`--gesture`)

| Valor | Gesto que hace aletear |
| --- | --- |
| `pinch` (por defecto) | Juntar el pulgar y el índice (pinza) |
| `open` | Abrir la mano (viniendo de puño) |
| `both` | Cualquiera de los dos |

## Controles

| Acción | Gesto / Tecla |
| --- | --- |
| Aletear | Pinza (pulgar + índice) |
| **Empezar la partida** | Primera pinza |
| **Reiniciar (continuar) tras Game Over** | Una pinza (reinicia y empieza a jugar) |
| Aletear (respaldo) | `ESPACIO` o `↑` |
| Cerrar la ventana de la cámara | Tecla `q` sobre ella (o cerrar el juego) |
| Salir | `ESC` o cerrar la ventana del juego |

## Estructura del proyecto

```
flappybird_vision/
├── main.py                  # Punto de entrada y bucle principal (pygame)
├── game.py                  # Lógica y renderizado del juego (pygame)
├── bird.py                  # Clase del pájaro (física del salto)
├── pipe.py                  # Clase de las tuberías
├── vision.py                # Lanza/controla el proceso de cámara (lado juego)
├── camera_view.py           # Proceso hijo: cámara + ventana OpenCV + eventos
├── hand_detector.py         # MediaPipe + reglas de gestos (pinza, mano abierta)
├── fonts.py                 # Carga de fuentes (con respaldo freetype)
├── settings.py              # Constantes de configuración del juego
├── run.sh                   # Lanzador que usa el venv automáticamente
├── assets/
│   └── hand_landmarker.task # Modelo de detección de manos de MediaPipe
├── packaging/               # Empaquetado en aplicación/instalador
│   ├── flappybird.spec      # Spec de PyInstaller (Linux/Windows/macOS)
│   ├── build.sh             # Compila para Linux (+ .tar.gz / AppImage)
│   ├── build_windows.bat    # Compila para Windows (+ instalador Inno Setup)
│   └── windows_installer.iss# Script del instalador de Windows
├── .github/workflows/
│   └── build.yml            # Genera los paquetes de Linux y Windows en CI
├── requirements.txt
└── README.md
```

## Solución de problemas

- **"No se pudo abrir la cámara"**: prueba con `--camera 1` u otro índice.
  El juego sigue funcionando con el teclado.
- **No detecta la mano**: mira la ventana de la cámara; la mano debe salir
  completa y bien iluminada. Ajusta si es necesario.
- **La pinza no responde**: junta bien las yemas del pulgar y el índice, con
  la mano de frente. Sube la sensibilidad con `--pinch-threshold 0.3` (o más).
- **La pinza se activa sola**: baja la sensibilidad con `--pinch-threshold 0.2`
  (o menos), para exigir que los dedos se toquen más.
- **Prefiero otro gesto**: usa `--gesture open` (abrir la mano) o `both`.
- **Va lento**: cierra otras apps que usen la cámara; MediaPipe corre en CPU.
- **Aviso de fuentes de Qt** al abrir la ventana de la cámara: es inofensivo
  (el texto se dibuja con las fuentes propias de OpenCV).

## Empaquetado: instaladores para Linux y Windows 📦

Se puede empaquetar todo (código, dependencias y modelo) en una aplicación
que no necesita Python instalado, usando **PyInstaller**.

> ⚠️ **No hay compilación cruzada**: el paquete de Windows se genera en
> Windows y el de Linux en Linux. La forma cómoda de obtener **ambos** es la
> integración de GitHub Actions incluida (ver más abajo).

### Linux

```bash
./packaging/build.sh              # crea dist/FlappyBirdVision/ + .tar.gz
./packaging/build.sh --appimage   # además intenta crear un .AppImage
```

Resultado:
- `dist/FlappyBirdVision/` — ejecutable portable (cópialo donde quieras).
- `dist/FlappyBirdVision-linux-<arch>-<fecha>.tar.gz` — para distribuir.
- `dist/FlappyBirdVision-<arch>.AppImage` — si has pedido `--appimage`.

### Windows

En una máquina Windows (con Python 3.10+ instalado):

```bat
packaging\build_windows.bat
```

Resultado:
- `dist\FlappyBirdVision\` — carpeta portable con `FlappyBirdVision.exe`.
- `dist\FlappyBirdVision-Setup.exe` — **instalador** (si tienes
  [Inno Setup 6](https://jrsoftware.org/isdl.php) instalado).

### Los dos a la vez con GitHub Actions

El repo incluye `.github/workflows/build.yml`. Al subirlo a GitHub puedes:

- lanzarlo a mano desde la pestaña **Actions → Build instaladores → Run
  workflow**, o
- crear un tag de versión: `git tag v1.0.0 && git push --tags` (además
  publica una *release* con los ficheros).

En ambos casos descarga los artefactos `flappybird-linux` y
`flappybird-windows` (el de Windows incluye el instalador de Inno Setup).

### Detalles técnicos del empaquetado

- La app lanza un proceso aparte para la cámara. Dentro de un ejecutable no
  existe `python` ni `camera_view.py`, así que el propio binario se relanza
  con el flag interno `--run-camera-process` (ver `main.py`).
- La comunicación cámara↔juego usa un **socket local** en vez de `stdout`,
  porque una app de ventana en Windows no tiene consola.
- El modelo `assets/hand_landmarker.task` se incluye y se localiza con
  `resource_path()` (funciona también dentro del ejecutable).
- El paquete pesa bastante (~370 MB) porque incluye MediaPipe, OpenCV (con
  Qt para la ventana de cámara) y matplotlib. Es lo normal en este tipo de
  aplicaciones.

## ¿Y la librería de Google para gestos?

**MediaPipe es la librería de Google** que ya usamos aquí. Incluye un
`Gesture Recognizer` con gestos ya entrenados (puño, palma abierta,
victoria, pulgar arriba, etc.), pero **no trae "pinza"**. Por eso la pinza
se calcula a partir de los 21 puntos de la mano (distancia pulgar↔índice),
que además es más flexible y no requiere descargar otro modelo.

Si quisieras usar los gestos ya hechos de Google, se puede cambiar
`hand_detector.py` para usar `GestureRecognizer` en lugar de `HandLandmarker`.

## Cómo está hecho

El juego no depende de la webcam para funcionar: la lógica de `pygame`
corre a 60 FPS en el proceso principal, mientras que la cámara y MediaPipe
corren en **otro proceso** que solo envía eventos (gesto actual y "hay
aleteo pendiente"). Así el juego nunca se queda bloqueado esperando a la
cámara, y las dos ventanas (pygame y OpenCV) no compiten por el mismo hilo.

## Ajustes

Todos los parámetros del juego (gravedad, tamaño de hueco, velocidad…)
están en `settings.py`. Los umbrales de detección de la pinza están en el
constructor de `HandDetector` (`hand_detector.py`): `pinch_enter`,
`pinch_exit` y `pinch_index_min`. El primero se puede ajustar desde la línea
de comandos con `--pinch-threshold`.
