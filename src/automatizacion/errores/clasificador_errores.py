"""
Clasificador de errores para automatización.
Responsabilidad única: Clasificar tipos de errores y determinar gravedad.
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional


class TipoError(Enum):
    """Tipos de errores clasificados por gravedad y tratamiento."""
    NAVEGADOR_CERRADO = "navegador_cerrado"
    SESION_PERDIDA = "sesion_perdida"
    ELEMENTO_NO_ENCONTRADO = "elemento_no_encontrado"
    TIMEOUT_RED = "timeout_red"
    TIMEOUT_ELEMENTO = "timeout_elemento"
    CAPTCHA_FALLIDO = "captcha_fallido"
    CREDENCIALES_INVALIDAS = "credenciales_invalidas"
    ERROR_API = "error_api"
    ERROR_NAVEGACION = "error_navegacion"
    ERROR_DESCONOCIDO = "error_desconocido"


class GravedadError(Enum):
    """Gravedad del error para determinar acción."""
    CRITICO = "critico"      # Requiere reinicio completo
    ALTO = "alto"            # Requiere recuperación específica
    MEDIO = "medio"          # Reintento simple
    BAJO = "bajo"            # Continuar o ignorar


class ClasificadorErrores:
    """Clasificador responsable de analizar y categorizar errores."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Mapeo de patrones de error a tipos
        self.patrones_error = {
            # Errores críticos
            "invalid session": TipoError.SESION_PERDIDA,
            "session not created": TipoError.NAVEGADOR_CERRADO,
            "no such session": TipoError.SESION_PERDIDA,
            "chrome not reachable": TipoError.NAVEGADOR_CERRADO,
            "session timed out": TipoError.SESION_PERDIDA,
            "disconnected": TipoError.NAVEGADOR_CERRADO,
            
            # Errores de elementos
            "element not found": TipoError.ELEMENTO_NO_ENCONTRADO,
            "no such element": TipoError.ELEMENTO_NO_ENCONTRADO,
            "element not visible": TipoError.ELEMENTO_NO_ENCONTRADO,
            "element not clickable": TipoError.ELEMENTO_NO_ENCONTRADO,
            
            # Errores de timeout
            "timeout": TipoError.TIMEOUT_ELEMENTO,
            "timed out": TipoError.TIMEOUT_ELEMENTO,
            "connection timeout": TipoError.TIMEOUT_RED,
            
            # Errores de autenticación
            "captcha": TipoError.CAPTCHA_FALLIDO,
            "login failed": TipoError.CREDENCIALES_INVALIDAS,
            "invalid credentials": TipoError.CREDENCIALES_INVALIDAS,
            
            # Errores de API
            "api error": TipoError.ERROR_API,
            "connection error": TipoError.ERROR_API,
            "404": TipoError.ERROR_API,
            "500": TipoError.ERROR_API,
            
            # Errores de navegación
            "navigation": TipoError.ERROR_NAVEGACION,
            "page not found": TipoError.ERROR_NAVEGACION
        }
        
        # Mapeo de tipos a gravedad
        self.gravedad_por_tipo = {
            TipoError.NAVEGADOR_CERRADO: GravedadError.CRITICO,
            TipoError.SESION_PERDIDA: GravedadError.CRITICO,
            TipoError.CREDENCIALES_INVALIDAS: GravedadError.CRITICO,
            TipoError.CAPTCHA_FALLIDO: GravedadError.ALTO,
            TipoError.ERROR_NAVEGACION: GravedadError.ALTO,
            TipoError.TIMEOUT_RED: GravedadError.ALTO,
            TipoError.ELEMENTO_NO_ENCONTRADO: GravedadError.MEDIO,
            TipoError.TIMEOUT_ELEMENTO: GravedadError.MEDIO,
            TipoError.ERROR_API: GravedadError.MEDIO,
            TipoError.ERROR_DESCONOCIDO: GravedadError.BAJO
        }
        
        self.logger.info("ClasificadorErrores inicializado")
    
    def clasificar(self, error: Exception) -> TipoError:
        """
        Clasifica un error según su mensaje y tipo.
        
        Args:
            error: Excepción a clasificar
            
        Returns:
            TipoError: Tipo de error clasificado
        """
        try:
            mensaje_error = str(error).lower()
            tipo_error_str = type(error).__name__.lower()
            
            self.logger.debug(f"Clasificando error: {mensaje_error}")
            
            # Buscar patrones en el mensaje
            for patron, tipo in self.patrones_error.items():
                if patron in mensaje_error or patron in tipo_error_str:
                    self.logger.info(f"Error clasificado como: {tipo.value}")
                    return tipo
            
            # Si no se encuentra patrón específico, clasificar por tipo de excepción
            tipo_clasificado = self._clasificar_por_tipo_excepcion(error)
            self.logger.info(f"Error clasificado por tipo: {tipo_clasificado.value}")
            return tipo_clasificado
            
        except Exception as e:
            self.logger.error(f"Error clasificando excepción: {e}")
            return TipoError.ERROR_DESCONOCIDO
    
    def _clasificar_por_tipo_excepcion(self, error: Exception) -> TipoError:
        """Clasifica error por tipo de excepción."""
        tipo_error = type(error).__name__
        
        clasificacion_tipos = {
            "TimeoutError": TipoError.TIMEOUT_ELEMENTO,
            "ConnectionError": TipoError.TIMEOUT_RED,
            "NoSuchElementException": TipoError.ELEMENTO_NO_ENCONTRADO,
            "ElementNotVisibleException": TipoError.ELEMENTO_NO_ENCONTRADO,
            "WebDriverException": TipoError.NAVEGADOR_CERRADO,
            "InvalidSessionIdException": TipoError.SESION_PERDIDA,
            "requests.exceptions.ConnectionError": TipoError.TIMEOUT_RED,
            "requests.exceptions.Timeout": TipoError.TIMEOUT_RED
        }
        
        return clasificacion_tipos.get(tipo_error, TipoError.ERROR_DESCONOCIDO)
    
    def obtener_gravedad(self, tipo_error: TipoError) -> GravedadError:
        """
        Obtiene la gravedad de un tipo de error.
        
        Args:
            tipo_error: Tipo de error
            
        Returns:
            GravedadError: Gravedad del error
        """
        return self.gravedad_por_tipo.get(tipo_error, GravedadError.BAJO)
    
    def es_error_critico(self, error: Exception) -> bool:
        """
        Determina si un error es crítico.
        
        Args:
            error: Excepción a evaluar
            
        Returns:
            bool: True si el error es crítico
        """
        tipo = self.clasificar(error)
        gravedad = self.obtener_gravedad(tipo)
        return gravedad == GravedadError.CRITICO
    
    def requiere_reinicio_completo(self, error: Exception) -> bool:
        """
        Determina si el error requiere reinicio completo del navegador.
        
        Args:
            error: Excepción a evaluar
            
        Returns:
            bool: True si requiere reinicio completo
        """
        tipo = self.clasificar(error)
        return tipo in [
            TipoError.NAVEGADOR_CERRADO,
            TipoError.SESION_PERDIDA,
            TipoError.CREDENCIALES_INVALIDAS
        ]
    
    def obtener_estrategia_recuperacion(self, tipo_error: TipoError) -> str:
        """
        Obtiene la estrategia de recuperación recomendada.
        
        Args:
            tipo_error: Tipo de error
            
        Returns:
            str: Estrategia de recuperación
        """
        estrategias = {
            TipoError.NAVEGADOR_CERRADO: "reiniciar_navegador_completo",
            TipoError.SESION_PERDIDA: "reiniciar_sesion",
            TipoError.ELEMENTO_NO_ENCONTRADO: "recargar_pagina",
            TipoError.TIMEOUT_RED: "esperar_y_reintentar",
            TipoError.TIMEOUT_ELEMENTO: "recargar_y_buscar",
            TipoError.CAPTCHA_FALLIDO: "reintentar_captcha",
            TipoError.CREDENCIALES_INVALIDAS: "verificar_credenciales",
            TipoError.ERROR_API: "verificar_conexion_api",
            TipoError.ERROR_NAVEGACION: "navegar_desde_inicio",
            TipoError.ERROR_DESCONOCIDO: "reintentar_generico"
        }
        
        return estrategias.get(tipo_error, "reintentar_generico")
    
    def generar_reporte_error(self, error: Exception) -> Dict[str, Any]:
        """
        Genera un reporte completo del error.
        
        Args:
            error: Excepción a reportar
            
        Returns:
            dict: Reporte completo del error
        """
        tipo = self.clasificar(error)
        gravedad = self.obtener_gravedad(tipo)
        estrategia = self.obtener_estrategia_recuperacion(tipo)
        
        return {
            "mensaje_original": str(error),
            "tipo_excepcion": type(error).__name__,
            "tipo_clasificado": tipo.value,
            "gravedad": gravedad.value,
            "es_critico": self.es_error_critico(error),
            "requiere_reinicio": self.requiere_reinicio_completo(error),
            "estrategia_recuperacion": estrategia,
            "timestamp": self._obtener_timestamp()
        }
    
    def _obtener_timestamp(self) -> str:
        """Obtiene timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()