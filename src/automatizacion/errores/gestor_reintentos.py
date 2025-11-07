"""
Gestor de reintentos para automatización.
Responsabilidad única: Decidir cuándo y cómo reintentar operaciones fallidas.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from .clasificador_errores import TipoError, GravedadError


class GestorReintentos:
    """Gestor responsable de la lógica de reintentos."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configuración de reintentos por tipo de error
        self.config_reintentos = {
            TipoError.NAVEGADOR_CERRADO: {
                "max_reintentos": 3,
                "tiempo_espera": 5,  # segundos
                "incremento_espera": 2,  # factor multiplicador
                "reintentos_inmediatos": 0
            },
            TipoError.SESION_PERDIDA: {
                "max_reintentos": 3,
                "tiempo_espera": 3,
                "incremento_espera": 1.5,
                "reintentos_inmediatos": 0
            },
            TipoError.ELEMENTO_NO_ENCONTRADO: {
                "max_reintentos": 3,
                "tiempo_espera": 1,
                "incremento_espera": 1,
                "reintentos_inmediatos": 1
            },
            TipoError.TIMEOUT_RED: {
                "max_reintentos": 5,
                "tiempo_espera": 10,
                "incremento_espera": 1.2,
                "reintentos_inmediatos": 0
            },
            TipoError.TIMEOUT_ELEMENTO: {
                "max_reintentos": 3,
                "tiempo_espera": 2,
                "incremento_espera": 1,
                "reintentos_inmediatos": 1
            },
            TipoError.CAPTCHA_FALLIDO: {
                "max_reintentos": 2,
                "tiempo_espera": 1,
                "incremento_espera": 1,
                "reintentos_inmediatos": 0
            },
            TipoError.CREDENCIALES_INVALIDAS: {
                "max_reintentos": 1,
                "tiempo_espera": 0,
                "incremento_espera": 1,
                "reintentos_inmediatos": 0
            },
            TipoError.ERROR_API: {
                "max_reintentos": 3,
                "tiempo_espera": 5,
                "incremento_espera": 1.5,
                "reintentos_inmediatos": 0
            },
            TipoError.ERROR_NAVEGACION: {
                "max_reintentos": 2,
                "tiempo_espera": 3,
                "incremento_espera": 1,
                "reintentos_inmediatos": 0
            },
            TipoError.ERROR_DESCONOCIDO: {
                "max_reintentos": 2,
                "tiempo_espera": 5,
                "incremento_espera": 1,
                "reintentos_inmediatos": 0
            }
        }
        
        # Registro de reintentos por contexto
        self.historial_reintentos: Dict[str, Dict] = {}
        
        self.logger.info("GestorReintentos inicializado")
    
    def puede_reintentar(self, tipo_error: TipoError, intento_actual: int, contexto: str = "default") -> bool:
        """
        Determina si se puede realizar un reintento.
        
        Args:
            tipo_error: Tipo de error clasificado
            intento_actual: Número del intento actual
            contexto: Contexto del proceso (para tracking)
            
        Returns:
            bool: True si se puede reintentar
        """
        try:
            config = self.config_reintentos.get(tipo_error)
            if not config:
                self.logger.warning(f"No hay configuración para tipo de error: {tipo_error}")
                return False
            
            max_reintentos = config["max_reintentos"]
            puede_reintentar = intento_actual < max_reintentos
            
            if puede_reintentar:
                self._registrar_intento(contexto, tipo_error, intento_actual)
            
            self.logger.debug(
                f"Reintento {intento_actual}/{max_reintentos} para {tipo_error.value}: "
                f"{'Permitido' if puede_reintentar else 'No permitido'}"
            )
            
            return puede_reintentar
            
        except Exception as e:
            self.logger.error(f"Error evaluando reintento: {e}")
            return False
    
    def calcular_tiempo_espera(self, tipo_error: TipoError, intento: int) -> int:
        """
        Calcula el tiempo de espera antes del siguiente intento.
        
        Args:
            tipo_error: Tipo de error
            intento: Número de intento
            
        Returns:
            int: Tiempo de espera en segundos
        """
        try:
            config = self.config_reintentos.get(tipo_error)
            if not config:
                return 5  # Default fallback
            
            # Si es un reintento inmediato
            if intento <= config["reintentos_inmediatos"]:
                return 0
            
            # Calcular tiempo con incremento progresivo
            tiempo_base = config["tiempo_espera"]
            incremento = config["incremento_espera"]
            
            tiempo_calculado = tiempo_base * (incremento ** (intento - config["reintentos_inmediatos"] - 1))
            tiempo_final = min(tiempo_calculado, 60)  # Máximo 60 segundos
            
            self.logger.debug(f"Tiempo de espera calculado para intento {intento}: {tiempo_final}s")
            return int(tiempo_final)
            
        except Exception as e:
            self.logger.error(f"Error calculando tiempo de espera: {e}")
            return 5
    
    def debe_abortar(self, contexto: str, ventana_tiempo_minutos: int = 10) -> bool:
        """
        Determina si se debe abortar el proceso por demasiados errores.
        
        Args:
            contexto: Contexto del proceso
            ventana_tiempo_minutos: Ventana de tiempo para evaluar errores
            
        Returns:
            bool: True si se debe abortar
        """
        try:
            if contexto not in self.historial_reintentos:
                return False
            
            historial = self.historial_reintentos[contexto]
            ahora = datetime.now()
            limite_tiempo = ahora - timedelta(minutes=ventana_tiempo_minutos)
            
            # Contar errores recientes
            errores_recientes = 0
            for timestamp_str, info in historial.items():
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= limite_tiempo:
                        errores_recientes += info["intentos"]
                except (ValueError, KeyError):
                    continue
            
            # Abortar si hay más de 10 errores en la ventana de tiempo
            debe_abortar = errores_recientes > 10
            
            if debe_abortar:
                self.logger.warning(
                    f"Abortando proceso {contexto}: {errores_recientes} errores en {ventana_tiempo_minutos} minutos"
                )
            
            return debe_abortar
            
        except Exception as e:
            self.logger.error(f"Error evaluando si abortar: {e}")
            return False
    
    def _registrar_intento(self, contexto: str, tipo_error: TipoError, intento: int):
        """Registra un intento de reintento."""
        try:
            if contexto not in self.historial_reintentos:
                self.historial_reintentos[contexto] = {}
            
            timestamp = datetime.now().isoformat()
            self.historial_reintentos[contexto][timestamp] = {
                "tipo_error": tipo_error.value,
                "intentos": intento,
                "timestamp": timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error registrando intento: {e}")
    
    def obtener_configuracion(self, tipo_error: TipoError) -> Dict[str, Any]:
        """
        Obtiene la configuración de reintentos para un tipo de error.
        
        Args:
            tipo_error: Tipo de error
            
        Returns:
            dict: Configuración de reintentos
        """
        return self.config_reintentos.get(tipo_error, {})
    
    def limpiar_historial(self, contexto: str = None):
        """
        Limpia el historial de reintentos.
        
        Args:
            contexto: Contexto específico a limpiar, None para todos
        """
        try:
            if contexto:
                if contexto in self.historial_reintentos:
                    del self.historial_reintentos[contexto]
                    self.logger.info(f"Historial limpiado para contexto: {contexto}")
            else:
                self.historial_reintentos.clear()
                self.logger.info("Historial completo limpiado")
                
        except Exception as e:
            self.logger.error(f"Error limpiando historial: {e}")
    
    def generar_estadisticas(self, contexto: str = None) -> Dict[str, Any]:
        """
        Genera estadísticas de reintentos.
        
        Args:
            contexto: Contexto específico, None para todos
            
        Returns:
            dict: Estadísticas de reintentos
        """
        try:
            if contexto and contexto in self.historial_reintentos:
                datos = {contexto: self.historial_reintentos[contexto]}
            else:
                datos = self.historial_reintentos
            
            total_intentos = 0
            errores_por_tipo = {}
            
            for ctx, historial in datos.items():
                for info in historial.values():
                    if isinstance(info, dict) and "intentos" in info:
                        total_intentos += info["intentos"]
                        tipo = info.get("tipo_error", "desconocido")
                        errores_por_tipo[tipo] = errores_por_tipo.get(tipo, 0) + 1
            
            return {
                "total_intentos": total_intentos,
                "contextos_activos": len(datos),
                "errores_por_tipo": errores_por_tipo,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando estadísticas: {e}")
            return {}
    
    def actualizar_configuracion(self, tipo_error: TipoError, nueva_config: Dict[str, Any]):
        """
        Actualiza la configuración de reintentos para un tipo de error.
        
        Args:
            tipo_error: Tipo de error
            nueva_config: Nueva configuración
        """
        try:
            if tipo_error in self.config_reintentos:
                self.config_reintentos[tipo_error].update(nueva_config)
                self.logger.info(f"Configuración actualizada para {tipo_error.value}")
            else:
                self.logger.warning(f"Tipo de error no encontrado: {tipo_error}")
                
        except Exception as e:
            self.logger.error(f"Error actualizando configuración: {e}")