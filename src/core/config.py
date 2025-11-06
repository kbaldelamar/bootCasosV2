"""
Gestor de configuración global para la aplicación.
Permite cargar configuraciones desde .env y acceder a ellas desde cualquier clase.
"""
import os
import logging
from typing import Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Singleton para gestión de configuración global."""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Carga la configuración desde el archivo .env"""
        # Cargar variables de entorno desde .env
        load_dotenv()
        
        # Configuración de la aplicación
        self._config = {
            'app': {
                'name': os.getenv('APP_NAME', 'BootCasosV2'),
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true'
            },
            'api': {
                'base_url': os.getenv('API_BASE_URL', 'https://api.example.com'),
                'timeout': int(os.getenv('API_TIMEOUT', '30')),
                'retries': int(os.getenv('API_RETRIES', '3'))
            },
            'license': {
                'server_url': os.getenv('LICENSE_SERVER_URL', 'https://license.example.com'),
                'local_file': os.getenv('LICENSE_LOCAL_FILE', './data/license.json')
            },
            'ui': {
                'window_width': int(os.getenv('WINDOW_WIDTH', '1200')),
                'window_height': int(os.getenv('WINDOW_HEIGHT', '800')),
                'theme': os.getenv('THEME', 'dark')
            },
            'playwright': {
                'headless': os.getenv('PLAYWRIGHT_HEADLESS', 'True').lower() == 'true',
                'timeout': int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000'))
            },
            'database': {
                'path': os.getenv('DB_PATH', './data/app.db')
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'file': os.getenv('LOG_FILE', './logs/app.log')
            }
        }
        
        # Configurar logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        log_level = getattr(logging, self._config['logging']['level'].upper(), logging.INFO)
        log_file = self._config['logging']['file']
        
        # Crear directorio de logs si no existe
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.
        
        Args:
            key_path: Ruta del valor usando notación de punto (ej: 'app.name')
            default: Valor por defecto si no existe la clave
            
        Returns:
            El valor de configuración o el valor por defecto
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Establece un valor de configuración usando notación de punto.
        
        Args:
            key_path: Ruta del valor usando notación de punto
            value: Nuevo valor a establecer
        """
        keys = key_path.split('.')
        config = self._config
        
        # Navegar hasta el penúltimo nivel
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Establecer el valor final
        config[keys[-1]] = value
    
    def get_all(self) -> dict:
        """Retorna toda la configuración."""
        return self._config.copy()
    
    def reload(self) -> None:
        """Recarga la configuración desde el archivo .env"""
        self._load_config()


# Instancia global del gestor de configuración
config = ConfigManager()


def get_config(key_path: str, default: Any = None) -> Any:
    """Función de conveniencia para obtener configuración."""
    return config.get(key_path, default)


def set_config(key_path: str, value: Any) -> None:
    """Función de conveniencia para establecer configuración."""
    config.set(key_path, value)