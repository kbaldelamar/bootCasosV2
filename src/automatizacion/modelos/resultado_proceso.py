"""
Modelo para resultados de procesamiento.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ResultadoProceso:
    """Resultado de procesamiento de una tarea individual."""
    tarea_id: str
    contexto: str
    exitoso: bool
    mensaje: str
    datos_resultado: Optional[Dict[str, Any]] = None
    tiempo_ejecucion: Optional[float] = None
    errores: List[str] = None
    advertencias: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.errores is None:
            self.errores = []
        if self.advertencias is None:
            self.advertencias = []
    
    def agregar_error(self, error: str):
        """Agrega un error al resultado."""
        self.errores.append(error)
        self.exitoso = False
    
    def agregar_advertencia(self, advertencia: str):
        """Agrega una advertencia al resultado."""
        self.advertencias.append(advertencia)
    
    def tiene_errores(self) -> bool:
        """Verifica si hay errores."""
        return len(self.errores) > 0
    
    def tiene_advertencias(self) -> bool:
        """Verifica si hay advertencias."""
        return len(self.advertencias) > 0


@dataclass
class ResumenEjecucion:
    """Resumen de una ejecución completa de automatización."""
    contexto: str
    total_tareas: int
    tareas_exitosas: int
    tareas_fallidas: int
    tiempo_total: float
    velocidad_promedio: float
    errores_principales: List[str]
    timestamp_inicio: datetime
    timestamp_fin: datetime
    
    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_tareas == 0:
            return 0.0
        return (self.tareas_exitosas / self.total_tareas) * 100
    
    @property
    def tasa_fallo(self) -> float:
        """Calcula la tasa de fallo."""
        if self.total_tareas == 0:
            return 0.0
        return (self.tareas_fallidas / self.total_tareas) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resumen a diccionario."""
        return {
            "contexto": self.contexto,
            "total_tareas": self.total_tareas,
            "tareas_exitosas": self.tareas_exitosas,
            "tareas_fallidas": self.tareas_fallidas,
            "tiempo_total": self.tiempo_total,
            "velocidad_promedio": self.velocidad_promedio,
            "tasa_exito": self.tasa_exito,
            "tasa_fallo": self.tasa_fallo,
            "errores_principales": self.errores_principales,
            "timestamp_inicio": self.timestamp_inicio.isoformat(),
            "timestamp_fin": self.timestamp_fin.isoformat()
        }