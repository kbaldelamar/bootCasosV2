# BootCasosV2

Una aplicación de escritorio moderna construida con PySide6 y Playwright para automatización web y gestión de datos.

## Características

- **Interfaz moderna**: Desarrollada con PySide6 6.6.1
- **Automatización web**: Integración completa con Playwright 1.40.0
- **Sistema de configuración**: Gestión centralizada con archivos .env
- **Cliente API**: Cliente HTTP robusto con reintentos automáticos
- **Sistema de licencias**: Validación híbrida (local + servidor) con encriptación
- **Logging avanzado**: Sistema de logging configurable
- **Temas**: Soporte para temas claro y oscuro

## Estructura del Proyecto

```
# BootCasosV2

Una aplicación de escritorio moderna construida con PySide6 y Playwright para automatización web y gestión de datos a través de APIs.

## Características

- 🖥️ **Interfaz de usuario moderna** con PySide6
- 🌐 **Cliente API robusto** con reintentos automáticos y manejo de errores
- 🎭 **Automatización web** con Playwright
- ⚙️ **Sistema de configuración flexible** con archivos .env
- 🔐 **Sistema de licencias híbrido** (cliente + servidor)
- 📝 **Logging comprehensivo** con múltiples niveles
- 🎨 **Temas personalizables** (claro/oscuro)

## Estructura del Proyecto

```
bootCasosV2/
├── .env                    # Configuración de la aplicación
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias Python
├── run.bat                # Script para ejecutar en Windows
└── src/
    ├── api/               # Cliente API y utilidades
    │   └── api_client.py
    ├── core/              # Configuración y utilidades centrales
    │   └── config.py
    ├── license/           # Sistema de gestión de licencias
    │   └── license_manager.py
    ├── ui/                # Interfaz de usuario
    │   ├── main_window.py
    │   └── pages/         # Páginas de la aplicación
    │       ├── home_page.py
    │       ├── api_page.py
    │       ├── playwright_page.py
    │       └── settings_page.py
    └── utils/             # Utilidades generales
```

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/kbaldelamar/bootCasosV2.git
   cd bootCasosV2
   ```

2. **Crear un entorno virtual:**
   ```bash
   python -m venv .venv
   ```

3. **Activar el entorno virtual:**
   
   En Windows:
   ```bash
   .venv\Scripts\activate
   ```
   
   En Linux/Mac:
   ```bash
   source .venv/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Instalar navegadores de Playwright:**
   ```bash
   playwright install
   ```

6. **Configurar variables de entorno:**
   
   Edita el archivo `.env` con tus configuraciones específicas.

## Configuración

### Archivo .env

El archivo `.env` contiene todas las configuraciones de la aplicación:

```bash
# Configuración de la aplicación
APP_NAME=BootCasosV2
APP_VERSION=1.0.0
DEBUG=True

# Configuración de API
API_BASE_URL=https://api.example.com
API_TIMEOUT=30
API_RETRIES=3

# Configuración de licencia
LICENSE_SERVER_URL=https://license.example.com
LICENSE_CHECK_INTERVAL=3600

# Configuración de UI
WINDOW_WIDTH=1200
WINDOW_HEIGHT=800
THEME=dark

# Configuración de Playwright
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_TIMEOUT=30000
```

### Sistema de Configuración Global

La aplicación utiliza un sistema de configuración centralizado que permite:

- **Cargar configuraciones** desde archivos .env
- **Acceder desde cualquier clase** usando `get_config()`
- **Modificar configuraciones** en tiempo de ejecución con `set_config()`
- **Recargar configuraciones** sin reiniciar la aplicación

Ejemplo de uso:

```python
from src.core.config import get_config, set_config

# Obtener configuración
api_url = get_config('api.base_url')
debug_mode = get_config('app.debug', False)

# Establecer configuración
set_config('ui.theme', 'dark')
```

## Uso

### Ejecutar la aplicación

```bash
python main.py
```

O en Windows, usar el archivo batch:
```bash
run.bat
```

### Funcionalidades principales

#### 1. Gestión de API
- Testing de endpoints HTTP (GET, POST, PUT, DELETE)
- Configuración de headers y autenticación
- Visualización de respuestas en formato JSON
- Manejo automático de errores y reintentos

#### 2. Automatización Web
- Navegación automatizada con Playwright
- Extracción de datos de páginas web
- Capturas de pantalla automatizadas
- Ejecución de scripts JavaScript personalizados

#### 3. Sistema de Licencias
- Validación de licencias local y remota
- Renovación automática de licencias
- Gestión de características por tipo de licencia

#### 4. Configuración
- Interface gráfica para configurar la aplicación
- Modificación de configuraciones en tiempo real
- Export/import de configuraciones

## Desarrollo

### Arquitectura

La aplicación sigue una arquitectura modular:

- **Core**: Configuración global y utilidades centrales
- **UI**: Interfaz de usuario con PySide6
- **API**: Cliente HTTP robusto con manejo de errores
- **License**: Sistema de gestión de licencias
- **Utils**: Utilidades generales

### Extensiones

Para añadir nuevas funcionalidades:

1. **Crear nueva página**: Añadir archivo en `src/ui/pages/`
2. **Registrar en menú**: Modificar `main_window.py`
3. **Añadir configuración**: Actualizar `config.py` y `.env`

### Testing

Para ejecutar pruebas (cuando estén disponibles):

```bash
pytest tests/
```

## Sistema de Licencias

### Recomendaciones de Implementación

**Enfoque Híbrido Recomendado:**

1. **Validación Inicial (Cliente)**:
   - Verificación de licencia local
   - Validación de firma digital
   - Control de características básicas

2. **Validación Periódica (Servidor)**:
   - Verificación en línea cada X horas
   - Actualización de estado de licencia
   - Renovación automática

3. **Seguridad**:
   - Encriptación de archivos de licencia
   - Firma digital con claves RSA
   - Ofuscación de código crítico

### Ventajas del Sistema Híbrido:

- ✅ **Funciona offline** temporalmente
- ✅ **Seguridad robusta** con validación servidor
- ✅ **Experiencia de usuario fluida**
- ✅ **Control centralizado** de licencias
- ✅ **Prevención de piratería** efectiva

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## Soporte

Para soporte y preguntas:

- **Issues**: Crear un issue en GitHub
- **Email**: kbaldelamar@example.com
- **Documentación**: Ver la wiki del proyecto

## Changelog

### v1.0.0 (2025-11-06)
- ✨ Implementación inicial
- 🎨 Interfaz de usuario con PySide6
- 🌐 Cliente API con reintentos
- 🎭 Integración con Playwright
- 🔐 Sistema de licencias
- ⚙️ Sistema de configuración global
├── src/
│   ├── core/
│   │   └── config.py          # Gestor de configuración global
│   ├── ui/
│   │   ├── main_window.py     # Ventana principal
│   │   └── pages/             # Páginas de la aplicación
│   │       ├── home_page.py
│   │       ├── api_page.py
│   │       ├── playwright_page.py
│   │       └── settings_page.py
│   ├── api/
│   │   └── api_client.py      # Cliente API HTTP
│   ├── license/
│   │   └── license_manager.py # Sistema de licencias
│   └── utils/                 # Utilidades generales
├── main.py                    # Punto de entrada
├── .env                       # Configuración de la aplicación
└── requirements.txt           # Dependencias
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/usuario/bootCasosV2.git
cd bootCasosV2
```

2. Crear entorno virtual:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Instalar navegadores de Playwright:
```bash
playwright install
```

5. Configurar variables de entorno:
   - Copiar `.env.example` a `.env`
   - Ajustar las configuraciones según tus necesidades

## Configuración

La aplicación utiliza un archivo `.env` para la configuración. Las opciones principales incluyen:

### Configuración de la Aplicación
- `APP_NAME`: Nombre de la aplicación
- `APP_VERSION`: Versión actual
- `DEBUG`: Modo de depuración

### Configuración de API
- `API_BASE_URL`: URL base de la API
- `API_TIMEOUT`: Timeout para solicitudes HTTP
- `API_RETRIES`: Número de reintentos

### Configuración de Licencia
- `LICENSE_SERVER_URL`: URL del servidor de licencias
- `LICENSE_CHECK_INTERVAL`: Intervalo de verificación (segundos)
- `LICENSE_FILE_PATH`: Ruta del archivo de licencia local

### Configuración de UI
- `WINDOW_WIDTH`: Ancho de la ventana
- `WINDOW_HEIGHT`: Alto de la ventana
- `THEME`: Tema de la aplicación (light/dark)

### Configuración de Playwright
- `PLAYWRIGHT_HEADLESS`: Modo headless para navegadores
- `PLAYWRIGHT_TIMEOUT`: Timeout para operaciones web

## Uso

### Ejecutar la aplicación:
```bash
python main.py
```

### Funcionalidades principales:

1. **Gestión de API**:
   - Testing de endpoints HTTP
   - Soporte para GET, POST, PUT, DELETE
   - Manejo de headers y autenticación
   - Visualización de respuestas

2. **Automatización Web**:
   - Navegación automatizada
   - Extracción de datos
   - Capturas de pantalla
   - Ejecución de scripts JavaScript personalizados

3. **Configuración**:
   - Gestión de configuraciones en tiempo real
   - Recarga automática desde .env
   - Validación de configuraciones

## Sistema de Configuración Global

La aplicación incluye un sistema de configuración centralizado que permite:

```python
from src.core.config import config, get_config, set_config

# Obtener configuración
app_name = config.get('app.name')
api_url = get_config('api.base_url')

# Establecer configuración
config.set('ui.theme', 'dark')
set_config('api.timeout', 60)
```

## Sistema de Licencias

La aplicación incluye un sistema de licencias híbrido que:

- **Validación local**: Verificación rápida sin conexión
- **Validación remota**: Sincronización con servidor de licencias
- **Encriptación**: Almacenamiento seguro de licencias
- **Características por licencia**: Control granular de funcionalidades

### Uso del sistema de licencias:

```python
from src.license.license_manager import LicenseManager

license_manager = LicenseManager()

# Verificar licencia
if license_manager.is_valid():
    print("Licencia válida")

# Verificar característica específica
if license_manager.has_feature('advanced_automation'):
    # Habilitar funcionalidad avanzada
    pass

# Instalar nueva licencia
license_manager.install_license('LICENCIA-CLAVE-AQUI')
```

## Cliente API

Cliente HTTP robusto con características avanzadas:

```python
from src.api.api_client import api_client

# Configurar autenticación
api_client.set_auth_token('tu_token_aqui')

# Realizar solicitudes
response = api_client.get('/users')
result = api_client.post('/data', json={'key': 'value'})
```

## Sugerencias para el Sistema de Licencias

### Implementación Recomendada:

1. **Híbrido (Cliente + Servidor)** - RECOMENDADO:
   - **Ventajas**: 
     - Funciona offline después de validación inicial
     - Permite control centralizado
     - Dificulta la piratería
     - Flexibilidad en características
   
   - **Implementación**:
     - Servidor valida y firma licencias
     - Cliente almacena licencia encriptada localmente
     - Verificación periódica con servidor
     - Características controladas por licencia

2. **Solo Cliente**:
   - Más simple pero menos seguro
   - Vulnerable a modificaciones locales
   - No permite revocación remota

3. **Solo Servidor**:
   - Muy seguro pero requiere conexión constante
   - Problemático para usuarios sin internet
   - Mayor latencia en operaciones

### Recomendaciones de Seguridad:

1. **Encriptación**: Usar claves derivadas del hardware
2. **Obfuscación**: Dificultar ingeniería inversa
3. **Verificación temporal**: Checks periódicos automáticos
4. **Características granulares**: Control fino de funcionalidades
5. **Logging de licencias**: Auditoría de uso

## Desarrollo

### Agregar nuevas páginas:
1. Crear archivo en `src/ui/pages/`
2. Heredar de `QWidget`
3. Agregar al `main_window.py`

### Agregar nuevas configuraciones:
1. Actualizar `.env`
2. Modificar `config.py` si es necesario
3. Usar `config.get()` y `config.set()` en el código

### Extender el cliente API:
1. Agregar métodos en `api_client.py`
2. Manejar autenticación específica
3. Implementar cache si es necesario

## Dependencias

- `PySide6==6.6.1`: Framework de interfaz gráfica
- `playwright==1.40.0`: Automatización web
- `python-dotenv`: Gestión de variables de entorno
- `requests`: Cliente HTTP
- `cryptography`: Encriptación para licencias

## Licencia

[Especificar la licencia del proyecto]

## Contribuciones

[Instrucciones para contribuir al proyecto]