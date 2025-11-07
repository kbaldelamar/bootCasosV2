"""
Modelo para tareas de automatización.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class TareaAutomatizacion:
    """Representa una tarea individual de automatización."""
    id: str
    contexto: str  # "PACIENTES" o "CASOS"
    tipo: str  # "procesar_paciente", "actualizar_caso", etc.
    datos: Dict[str, Any]
    prioridad: int = 1  # 1 = alta, 5 = baja
    reintentos: int = 0
    max_reintentos: int = 3
    tiempo_creacion: datetime = None
    tiempo_inicio: Optional[datetime] = None
    tiempo_fin: Optional[datetime] = None
    resultado: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.tiempo_creacion is None:
            self.tiempo_creacion = datetime.now()
    
    @property
    def puede_reintentar(self) -> bool:
        """Determina si la tarea puede reintentarse."""
        return self.reintentos < self.max_reintentos
    
    @property
    def esta_completada(self) -> bool:
        """Determina si la tarea está completada."""
        return self.tiempo_fin is not None and self.resultado is not None
    
    @property
    def tiempo_ejecucion(self) -> Optional[float]:
        """Calcula el tiempo de ejecución en segundos."""
        if not self.tiempo_inicio or not self.tiempo_fin:
            return None
        return (self.tiempo_fin - self.tiempo_inicio).total_seconds()
    
    def iniciar(self):
        """Marca el inicio de la tarea."""
        self.tiempo_inicio = datetime.now()
    
    def completar(self, resultado: str):
        """Marca la tarea como completada exitosamente."""
        self.tiempo_fin = datetime.now()
        self.resultado = resultado
    
    def fallar(self, error: str):
        """Marca la tarea como fallida."""
        self.tiempo_fin = datetime.now()
        self.error = error
        self.reintentos += 1
    
    def reiniciar(self):
        """Reinicia la tarea para un nuevo intento."""
        self.tiempo_inicio = None
        self.tiempo_fin = None
        self.resultado = None
        self.error = None