"""
Sistema de gestión de licencias basado 100% en API.
Valida licencias en tiempo real con el servidor y permite activación de nuevas licencias.
"""
import os
import json
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from src.core.config import config
from src.api.api_client import ApiClient, ApiException


class LicenseManager:
    """Gestor de licencias con validación exclusiva por API."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.server_url = config.get('license.server_url')
        self.api_client = ApiClient()
        
        # Cache temporal de licencia (solo durante la sesión)
        self._current_license = None
        self._hardware_id = self._generate_hardware_id()
        
        if not self.server_url:
            self.logger.error("URL del servidor de licencias no configurada")
            raise LicenseException("Servidor de licencias no configurado")
    
    def _generate_hardware_id(self) -> str:
        """Genera un ID único del hardware del cliente."""
        try:
            import platform
            import getpass
            
            # Crear ID basado en características del sistema
            system_info = f"{platform.machine()}-{platform.node()}-{getpass.getuser()}-{platform.processor()}"
            hardware_id = hashlib.sha256(system_info.encode()).hexdigest()[:16]
            return hardware_id
            
        except Exception as e:
            self.logger.warning(f"No se pudo generar hardware_id único: {e}")
            return "default_hardware_id"
    
"""
Sistema de gestión de licencias integrado con API real de BootCasosV2.
Incluye desencriptación de códigos de licencia y validación con servidor.
"""
import hashlib
import logging
import time
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.core.config import config
from src.api.api_client import ApiClient, ApiException


class LicenseDecryptor:
    """Clase para desencriptar códigos de licencia usando los mismos parámetros de la app generadora."""
    
    def __init__(self):
        self.password = "BootCasosV2_License_Key_2024"
        self.salt = b'boot_casos_v2_salt_2024'
        self.iterations = 100000
        self._key = self._generate_key()
    
    def _generate_key(self) -> bytes:
        """Genera la misma clave usada en la app generadora."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=self.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def decrypt_license_code(self, encrypted_code: str) -> Dict[str, Any]:
        """
        Desencripta un código de licencia encriptado.
        
        Args:
            encrypted_code: Código encriptado en base64
            
        Returns:
            Diccionario con los datos de la licencia
        """
        try:
            # Decodificar de base64
            encrypted_data = base64.b64decode(encrypted_code.encode())
            
            # Desencriptar usando Fernet
            fernet = Fernet(self._key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parsear JSON
            license_data = json.loads(decrypted_data.decode())
            
            return license_data
            
        except Exception as e:
            raise LicenseException(f"Error desencriptando código de licencia: {e}")


class LicenseManager:
    """Gestor de licencias integrado con API real de BootCasosV2."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.server_url = config.get('license.server_url')
        self.api_client = ApiClient()
        self.decryptor = LicenseDecryptor()
        
        # Cache temporal de licencia (solo durante la sesión)
        self._current_license = None
        self._hardware_id = self._generate_hardware_id()
        
        if not self.server_url:
            self.logger.error("URL del servidor de licencias no configurada")
            raise LicenseException("Servidor de licencias no configurado")
    
    def _generate_hardware_id(self) -> str:
        """Genera un ID único del hardware del cliente."""
        try:
            import platform
            import getpass
            
            # Crear ID basado en características del sistema
            system_info = f"{platform.machine()}-{platform.node()}-{getpass.getuser()}-{platform.processor()}"
            hardware_id = f"HW-{hashlib.sha256(system_info.encode()).hexdigest()[:12].upper()}"
            return hardware_id
            
        except Exception as e:
            self.logger.warning(f"No se pudo generar hardware_id único: {e}")
            return "HW-DEFAULT-ID"
    
    def process_encrypted_license_code(self, encrypted_code: str) -> Dict[str, Any]:
        """
        Procesa un código de licencia encriptado, lo desencripta y lo registra en la API.
        
        Args:
            encrypted_code: Código encriptado de la licencia
            
        Returns:
            Resultado del procesamiento
        """
        try:
            # 1. Desencriptar el código
            self.logger.info("Desencriptando código de licencia...")
            license_data = self.decryptor.decrypt_license_code(encrypted_code)
            
            # 2. Validar estructura del JSON desencriptado
            required_fields = ['license_key', 'client_identification', 'client_name', 
                             'expiration_date', 'features']
            
            for field in required_fields:
                if field not in license_data:
                    raise LicenseException(f"Campo requerido faltante: {field}")
            
            # 3. Validar formato de license_key
            if not license_data['license_key'].startswith('BOOT-'):
                raise LicenseException("Formato de license_key inválido")
            
            # 4. Verificar que no esté expirada
            expiration_str = license_data['expiration_date']
            try:
                expiration_date = datetime.strptime(expiration_str, "%Y-%m-%d %H:%M:%S")
                if expiration_date < datetime.now():
                    return {
                        'success': False,
                        'error_type': 'license_expired',
                        'message': f'La licencia expiró el {expiration_str}',
                        'license_data': license_data
                    }
            except ValueError:
                raise LicenseException("Formato de fecha de expiración inválido")
            
            # 5. Crear/actualizar licencia en la API
            creation_result = self._create_license_in_api(license_data)
            
            if not creation_result.get('success'):
                return creation_result
            
            # 6. Activar la licencia
            activation_result = self.activate_license(license_data['license_key'])
            
            return activation_result
            
        except LicenseException as e:
            self.logger.error(f"Error procesando código de licencia: {e}")
            return {
                'success': False,
                'error_type': 'processing_error',
                'message': str(e)
            }
        except Exception as e:
            self.logger.error(f"Error inesperado procesando licencia: {e}")
            return {
                'success': False,
                'error_type': 'unexpected_error',
                'message': f'Error inesperado: {e}'
            }
    
    def _create_license_in_api(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea o actualiza una licencia en la API."""
        try:
            # Preparar datos para la API
            api_data = {
                'license_key': license_data['license_key'],
                'client_identification': license_data['client_identification'],
                'client_name': license_data['client_name'],
                'expiration_date': license_data['expiration_date'],
                'features': license_data['features'],
                'hardware_id': self._hardware_id,
                'app_version': config.get('app.version', '1.0.0')
            }
            
            self.logger.info(f"Creando licencia en API: {license_data['license_key']}")
            
            # Hacer solicitud a la API
            response = self.api_client.post(
                f"{self.server_url}/api/licenses/create",
                json=api_data
            )
            
            if response.get('status_code') == 200:
                api_response = response.get('data', {})
                
                if api_response.get('statusCode') == 200:
                    self.logger.info("Licencia creada exitosamente en API")
                    return {
                        'success': True,
                        'message': 'Licencia registrada en servidor'
                    }
                else:
                    error_msg = api_response.get('description', 'Error desconocido')
                    return {
                        'success': False,
                        'error_type': 'api_error',
                        'message': f'Error del servidor: {error_msg}'
                    }
            else:
                return {
                    'success': False,
                    'error_type': 'connection_error',
                    'message': f'Error de conexión: {response.get("status_code")}'
                }
                
        except ApiException as e:
            self.logger.error(f"Error creando licencia en API: {e}")
            return {
                'success': False,
                'error_type': 'connection_error',
                'message': f'No se pudo conectar al servidor: {e}'
            }
    
    def check_existing_license(self) -> Dict[str, Any]:
        """
        Verifica si ya existe una licencia activa para este hardware en la API.
        
        Returns:
            Resultado de la verificación con información de la licencia si existe
        """
        try:
            # Intentar con licencia guardada localmente primero
            stored_license = self._load_stored_license()
            if stored_license:
                self.logger.info(f"Verificando licencia almacenada: {stored_license}")
                validation_result = self.validate_license(stored_license)
                if validation_result.get('valid'):
                    return {
                        'has_license': True,
                        'license_data': validation_result.get('license_data', {}),
                        'message': 'Licencia activa encontrada localmente'
                    }
                else:
                    # Licencia local no es válida, limpiar cache
                    self._current_license = None
                    self.logger.warning("Licencia local no es válida, será removida")
            
            # No hay licencia local válida
            return {
                'has_license': False,
                'message': 'No se encontró licencia válida'
            }
                
        except Exception as e:
            self.logger.error(f"Error verificando licencia existente: {e}")
            return {
                'has_license': False,
                'error_type': 'connection_error',
                'message': f'Error al verificar licencia: {e}'
            }
    
    def validate_license(self, license_key: str) -> Dict[str, Any]:
        """
        Valida una licencia con la API real.
        
        Args:
            license_key: Clave de licencia a validar
            
        Returns:
            Resultado de la validación
        """
        try:
            validation_data = {
                'license_key': license_key,
                'hardware_id': self._hardware_id,
                'app_version': config.get('app.version', '1.0.0')
            }
            
            self.logger.info(f"Validando licencia: {license_key}")
            
            response = self.api_client.post(
                f"{self.server_url}/api/licenses/validate",
                json=validation_data
            )
            
            if response.get('status_code') == 200:
                api_response = response.get('data', {})
                
                if api_response.get('statusCode') == 200:
                    # Licencia válida
                    license_info = api_response.get('data', {})
                    
                    # Procesar fecha de expiración encriptada si existe
                    if 'expiration_date_encrypted' in license_info:
                        # La fecha viene encriptada, necesitaríamos desencriptarla
                        # Por ahora usamos la fecha sin encriptar si está disponible
                        pass
                    
                    self._current_license = license_info
                    self.logger.info(f"Licencia válida para: {license_info.get('client_name')}")
                    
                    # Guardar licencia localmente si es válida
                    self._save_license_locally(license_key)
                    
                    return {
                        'valid': True,
                        'license_data': license_info,
                        'message': api_response.get('description', 'Licencia válida')
                    }
                else:
                    # Error en validación
                    error_msg = api_response.get('description', 'Error desconocido')
                    error_type = 'license_invalid'
                    
                    if 'expirada' in error_msg.lower():
                        error_type = 'license_expired'
                    elif 'no encontrada' in error_msg.lower():
                        error_type = 'license_not_found'
                    
                    return {
                        'valid': False,
                        'error_type': error_type,
                        'message': error_msg,
                        'require_new_license': True
                    }
            else:
                return {
                    'valid': False,
                    'error_type': 'server_error',
                    'message': f'Error del servidor: {response.get("status_code")}',
                    'require_new_license': False
                }
                
        except ApiException as e:
            self.logger.error(f"Error validando licencia: {e}")
            return {
                'valid': False,
                'error_type': 'connection_error',
                'message': f'No se pudo conectar al servidor: {e}',
                'require_new_license': False
            }
    
    def activate_license(self, license_key: str) -> Dict[str, Any]:
        """
        Activa una licencia con la API real.
        
        Args:
            license_key: Clave de licencia a activar
            
        Returns:
            Resultado de la activación
        """
        try:
            activation_data = {
                'license_key': license_key,
                'hardware_id': self._hardware_id,
                'app_version': config.get('app.version', '1.0.0')
            }
            
            self.logger.info(f"Activando licencia: {license_key}")
            
            response = self.api_client.post(
                f"{self.server_url}/api/licenses/activate",
                json=activation_data
            )
            
            if response.get('status_code') == 200:
                api_response = response.get('data', {})
                
                if api_response.get('statusCode') == 200:
                    # Activación exitosa - ahora validar para obtener datos completos
                    validation_result = self.validate_license(license_key)
                    if validation_result.get('valid'):
                        # Guardar licencia localmente después de activación exitosa
                        self._save_license_locally(license_key)
                    return validation_result
                else:
                    # Error en activación
                    error_msg = api_response.get('description', 'Error en activación')
                    error_type = 'activation_failed'
                    
                    if 'ya está activada' in error_msg.lower():
                        error_type = 'already_activated'
                        # Si ya está activada, intentar validar
                        validation_result = self.validate_license(license_key)
                        if validation_result.get('valid'):
                            return validation_result
                    
                    return {
                        'success': False,
                        'error_type': error_type,
                        'message': error_msg
                    }
            else:
                return {
                    'success': False,
                    'error_type': 'server_error',
                    'message': f'Error del servidor: {response.get("status_code")}'
                }
                
        except ApiException as e:
            self.logger.error(f"Error activando licencia: {e}")
            return {
                'success': False,
                'error_type': 'connection_error',
                'message': f'No se pudo conectar al servidor: {e}'
            }
    
    def is_valid(self, check_api: bool = True) -> bool:
        """
        Verifica si hay una licencia válida.
        
        Args:
            check_api: Si True, verifica con la API. Si False, solo revisa cache local.
        """
        # Si no hay licencia en cache y se requiere verificación API
        if self._current_license is None and check_api:
            # Intentar cargar desde configuración local si existe
            stored_license = self._load_stored_license()
            if stored_license:
                # Validar la licencia almacenada con la API
                validation_result = self.validate_license(stored_license)
                if validation_result.get('valid'):
                    return True
            return False
        
        # Si hay licencia en cache
        if self._current_license is not None:
            # Si se requiere verificación API, validar en tiempo real
            if check_api:
                license_key = self._current_license.get('license_key')
                if license_key:
                    validation_result = self.validate_license(license_key)
                    return validation_result.get('valid', False)
            
            # Solo verificación local
            return self._current_license.get('status') == 'active'
        
        return False
    
    def get_license_info(self) -> Dict[str, Any]:
        """Obtiene información de la licencia actual."""
        
        if not self._current_license:
            return {
                'valid': False,
                'message': 'No hay licencia válida cargada'
            }
        
        try:
            # Intentar calcular días restantes si hay fecha de expiración
            days_remaining = 0
            expiration_date = None
            
            # La API podría devolver la fecha en diferentes formatos
            if 'expiration_date' in self._current_license:
                try:
                    expiration_date = datetime.fromisoformat(
                        self._current_license['expiration_date'].replace('Z', '+00:00')
                    )
                    # Hacer datetime.now() timezone-aware para comparación correcta
                    now = datetime.now(expiration_date.tzinfo)
                    days_remaining = (expiration_date - now).days
                except:
                    days_remaining = 0
            
            license_info = {
                'valid': True,
                'license_key': self._current_license.get('license_key', ''),
                'client_name': self._current_license.get('client_name', ''),
                'client_identification': self._current_license.get('client_identification', ''),
                'expiration_date': self._current_license.get('expiration_date', ''),
                'days_remaining': max(0, days_remaining),
                'features': self._current_license.get('features', []),
                'status': self._current_license.get('status', 'unknown'),
                'hardware_id': self._current_license.get('hardware_id', ''),
                'last_validation': self._current_license.get('last_validation', '')
            }
            
            return license_info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de licencia: {e}")
            return {
                'valid': False,
                'message': f'Error procesando licencia: {e}'
            }
    
    def has_feature(self, feature: str) -> bool:
        """Verifica si una característica está habilitada."""
        if not self._current_license:
            return False
        
        features = self._current_license.get('features', [])
        return feature in features
    
    def get_hardware_id(self) -> str:
        """Obtiene el ID de hardware del cliente."""
        return self._hardware_id
    
    def clear_license(self):
        """Limpia la licencia actual del cache."""
        self._current_license = None
        self.logger.info("Licencia limpiada del cache")
    
    def require_license_input(self) -> bool:
        """
        Determina si se requiere ingresar una nueva licencia.
        Verifica tanto cache local como API.
        """
        # Si no hay licencia en cache
        if self._current_license is None:
            # Intentar cargar desde configuración local
            stored_license = self._load_stored_license()
            if stored_license:
                # Validar con API si existe una licencia almacenada
                validation_result = self.validate_license(stored_license)
                if validation_result.get('valid'):
                    # Licencia válida encontrada, no se requiere input
                    return False
            
            # No hay licencia válida, se requiere input
            return True
        
        # Hay licencia en cache, verificar si sigue siendo válida
        license_key = self._current_license.get('license_key')
        if license_key:
            validation_result = self.validate_license(license_key)
            if not validation_result.get('valid'):
                # Licencia ya no es válida, se requiere nueva
                self._current_license = None
                return True
        
        return False
    
    def _load_stored_license(self) -> Optional[str]:
        """Carga la clave de licencia almacenada localmente si existe."""
        try:
            license_file = config.get('license.local_file', 'license.json')
            if os.path.exists(license_file):
                with open(license_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('license_key')
        except Exception as e:
            self.logger.debug(f"No se pudo cargar licencia almacenada: {e}")
        return None
    
    def _save_license_locally(self, license_key: str):
        """Guarda la clave de licencia localmente para verificaciones futuras."""
        try:
            license_file = config.get('license.local_file', 'license.json')
            data = {
                'license_key': license_key,
                'saved_at': datetime.now().isoformat()
            }
            with open(license_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.logger.info("Licencia guardada localmente")
        except Exception as e:
            self.logger.warning(f"No se pudo guardar licencia localmente: {e}")


class LicenseException(Exception):
    """Excepción personalizada para errores de licencia."""
    pass