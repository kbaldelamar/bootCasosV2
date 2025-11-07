"""
Estados de automatización para el sistema.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class EstadoProceso(Enum):
    """Estados posibles de un proceso de automatización."""
    DETENIDO = "detenido"
    INICIANDO = "iniciando"
    NAVEGANDO = "navegando"
    AUTENTICANDO = "autenticando"
    PROCESANDO = "procesando"
    PAUSADO = "pausado"
    COMPLETADO = "completado"
    ERROR = "error"
    RECUPERANDO = "recuperando"


class EstadoLogin(Enum):
    """Estados del proceso de login."""
    PENDIENTE = "pendiente"
    INGRESANDO_CREDENCIALES = "ingresando_credenciales"
    RESOLVIENDO_CAPTCHA = "resolviendo_captcha"
    VERIFICANDO = "verificando"
    EXITOSO = "exitoso"
    FALLIDO = "fallido"


@dataclass
class EstadoAutomatizacion:
    """Estado completo de un proceso de automatización."""
    contexto: str
    estado: EstadoProceso
    items_totales: int
    items_procesados: int
    items_exitosos: int
    items_fallidos: int
    tiempo_inicio: Optional[datetime] = None
    tiempo_ultimo_item: Optional[datetime] = None
    intentos_recuperacion: int = 0
    max_intentos: int = 3
    mensaje_estado: str = ""
    velocidad_promedio: float = 0.0  # items por minuto
    
    @property
    def porcentaje_progreso(self) -> float:
        """Calcula el porcentaje de progreso."""
        if self.items_totales == 0:
            return 0.0
        return (self.items_procesados / self.items_totales) * 100
    
    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito."""
        if self.items_procesados == 0:
            return 0.0
        return (self.items_exitosos / self.items_procesados) * 100
    
    @property
    def puede_recuperar(self) -> bool:
        """Determina si puede intentar recuperación."""
        return self.intentos_recuperacion < self.max_intentos
    
    def actualizar_velocidad(self):
        """Actualiza la velocidad promedio de procesamiento."""
        if not self.tiempo_inicio or self.items_procesados == 0:
            self.velocidad_promedio = 0.0
            return
        
        tiempo_transcurrido = (datetime.now() - self.tiempo_inicio).total_seconds() / 60  # minutos
        if tiempo_transcurrido > 0:
            self.velocidad_promedio = self.items_procesados / tiempo_transcurrido
    
    def incrementar_procesado(self, exitoso: bool = True):
        """Incrementa contadores de items procesados."""
        self.items_procesados += 1
        if exitoso:
            self.items_exitosos += 1
        else:
            self.items_fallidos += 1
        self.tiempo_ultimo_item = datetime.now()
        self.actualizar_velocidad()
    
    def reiniciar_recuperacion(self):
        """Reinicia el contador de intentos de recuperación."""
        self.intentos_recuperacion = 0
    
    def incrementar_intento_recuperacion(self):
        """Incrementa el contador de intentos de recuperación."""
        self.intentos_recuperacion += 1