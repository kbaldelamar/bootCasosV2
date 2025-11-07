"""
Cliente API para consultar pacientes de autorizaciones Coosalud.
"""
import logging
from typing import Optional
from src.api.api_client import ApiClient
from src.models.coosalud.paciente_autorizacion_dto import RespuestaPacientesDto
from src.core.config import config


class CoosaludApiClient:
    """Cliente API para interactuar con el servicio de autorizaciones Coosalud."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_client = ApiClient()
        self.base_url = config.get('api.base_url')
    
    def obtener_pacientes_autorizacion(self) -> Optional[RespuestaPacientesDto]:
        """
        Consulta la lista de pacientes pendientes de autorización.
        
        Returns:
            RespuestaPacientesDto: Respuesta con la lista de pacientes o None si hay error
        """
        try:
            self.logger.info("Consultando pacientes de autorizaciones Coosalud...")
            
            # Realizar la petición a la API
            response = self.api_client.get(f"{self.base_url}/list-pacientes-casos?estado=0")
            
            if response.get('status_code') == 200:
                # Convertir respuesta a DTO
                data = response.get('data', {})
                respuesta_dto = RespuestaPacientesDto.from_dict(data)
                
                self.logger.info(f"Consulta exitosa: {respuesta_dto.total_pacientes} pacientes encontrados")
                return respuesta_dto
            else:
                self.logger.error(f"Error en la API: {response.get('status_code')} - {response.get('error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error consultando pacientes de autorizaciones: {e}")
            return None
    
    def validar_conexion_api(self) -> bool:
        """
        Valida que la API esté disponible.
        
        Returns:
            bool: True si la API está disponible, False en caso contrario
        """
        try:
            # Hacer una petición simple para verificar conectividad
            response = self.api_client.get(f"{self.base_url}/list-pacientes-casos?estado=0")
            return response.get('status_code') in [200, 404]  # 404 también indica que el servidor responde
        except Exception as e:
            self.logger.error(f"Error validando conexión API: {e}")
            return False