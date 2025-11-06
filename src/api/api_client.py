"""
Cliente API para consumir recursos remotos con manejo de errores y reintentos.
"""
import requests
import logging
import time
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.core.config import config


class ApiClient:
    """Cliente HTTP para interactuar con APIs externas."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = config.get('api.base_url')
        self.timeout = config.get('api.timeout', 30)
        self.max_retries = config.get('api.retries', 3)
        
        # Configurar sesión con reintentos automáticos
        self.session = requests.Session()
        self._setup_retries()
        
        # Headers por defecto
        self.session.headers.update({
            'User-Agent': f"{config.get('app.name')}/{config.get('app.version')}",
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _setup_retries(self):
        """Configura la estrategia de reintentos para la sesión."""
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _build_url(self, endpoint: str) -> str:
        """Construye la URL completa para un endpoint."""
        if endpoint.startswith('http'):
            return endpoint
        
        base = self.base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base}/{endpoint}"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Procesa la respuesta HTTP y maneja errores."""
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'url': response.url
        }
        
        try:
            # Intentar parsear como JSON
            if response.headers.get('content-type', '').startswith('application/json'):
                result['data'] = response.json()
            else:
                result['data'] = response.text
            
            # Verificar si la respuesta fue exitosa
            response.raise_for_status()
            
        except requests.exceptions.JSONDecodeError:
            result['data'] = response.text
            self.logger.warning(f"Respuesta no es JSON válido: {response.text[:200]}")
            
        except requests.exceptions.HTTPError as e:
            result['error'] = str(e)
            self.logger.error(f"Error HTTP {response.status_code}: {e}")
            raise ApiException(f"Error HTTP {response.status_code}: {e}")
        
        return result
    
    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Realiza una solicitud GET.
        
        Args:
            endpoint: Endpoint de la API o URL completa
            params: Parámetros de consulta
            headers: Headers adicionales
            
        Returns:
            Diccionario con la respuesta procesada
        """
        url = self._build_url(endpoint)
        
        try:
            self.logger.info(f"GET {url}")
            
            # Combinar headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = self.session.get(
                url,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout en solicitud GET a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión en GET a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except Exception as e:
            error_msg = f"Error inesperado en GET a {url}: {e}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, 
             headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Realiza una solicitud POST.
        
        Args:
            endpoint: Endpoint de la API o URL completa
            data: Datos a enviar en el cuerpo (form data)
            json: Datos JSON a enviar en el cuerpo
            headers: Headers adicionales
            
        Returns:
            Diccionario con la respuesta procesada
        """
        url = self._build_url(endpoint)
        
        try:
            self.logger.info(f"POST {url}")
            
            # Combinar headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout en solicitud POST a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión en POST a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except Exception as e:
            error_msg = f"Error inesperado en POST a {url}: {e}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None,
            headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Realiza una solicitud PUT.
        
        Args:
            endpoint: Endpoint de la API o URL completa
            data: Datos a enviar en el cuerpo (form data)
            json: Datos JSON a enviar en el cuerpo
            headers: Headers adicionales
            
        Returns:
            Diccionario con la respuesta procesada
        """
        url = self._build_url(endpoint)
        
        try:
            self.logger.info(f"PUT {url}")
            
            # Combinar headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = self.session.put(
                url,
                data=data,
                json=json,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout en solicitud PUT a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión en PUT a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except Exception as e:
            error_msg = f"Error inesperado en PUT a {url}: {e}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
    
    def delete(self, endpoint: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Realiza una solicitud DELETE.
        
        Args:
            endpoint: Endpoint de la API o URL completa
            headers: Headers adicionales
            
        Returns:
            Diccionario con la respuesta procesada
        """
        url = self._build_url(endpoint)
        
        try:
            self.logger.info(f"DELETE {url}")
            
            # Combinar headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = self.session.delete(
                url,
                headers=request_headers,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout en solicitud DELETE a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Error de conexión en DELETE a {url}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
            
        except Exception as e:
            error_msg = f"Error inesperado en DELETE a {url}: {e}"
            self.logger.error(error_msg)
            raise ApiException(error_msg)
    
    def set_auth_token(self, token: str, auth_type: str = 'Bearer'):
        """
        Configura el token de autenticación para todas las solicitudes.
        
        Args:
            token: Token de autenticación
            auth_type: Tipo de autenticación (Bearer, Basic, etc.)
        """
        self.session.headers['Authorization'] = f"{auth_type} {token}"
        self.logger.info("Token de autenticación configurado")
    
    def remove_auth(self):
        """Elimina la autenticación de las solicitudes."""
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
            self.logger.info("Autenticación eliminada")
    
    def set_base_url(self, base_url: str):
        """Cambia la URL base para las solicitudes."""
        self.base_url = base_url
        self.logger.info(f"URL base cambiada a: {base_url}")
    
    def close(self):
        """Cierra la sesión HTTP."""
        self.session.close()
        self.logger.info("Sesión API cerrada")


class ApiException(Exception):
    """Excepción personalizada para errores de API."""
    pass


# Instancia global del cliente API
api_client = ApiClient()