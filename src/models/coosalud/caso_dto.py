"""
DTO para representar un caso del sistema Coosalud.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CasoDto:
    """DTO que representa un caso del sistema."""
    
    caso: str  # Número del caso
    fecha: str  # Fecha en formato string
    id_ingreso: int  # ID del ingreso
    id_orden: int  # ID de la orden
    id_recepcion: int  # ID de la recepción
    
    # Campos calculados
    fecha_procesamiento: Optional[datetime] = None
    
    def __post_init__(self):
        """Procesa la fecha después de la inicialización."""
        if self.fecha and not self.fecha_procesamiento:
            try:
                # Convertir fecha string a datetime
                self.fecha_procesamiento = datetime.strptime(self.fecha, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Si no se puede convertir, mantener como None
                self.fecha_procesamiento = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CasoDto':
        """Crea una instancia desde un diccionario de la API."""
        return cls(
            caso=data.get("caso", ""),
            fecha=data.get("fecha", ""),
            id_ingreso=data.get("idIngreso", 0),
            id_orden=data.get("idOrden", 0),
            id_recepcion=data.get("idRecepcion", 0)
        )
    
    def to_dict(self) -> dict:
        """Convierte la instancia a diccionario."""
        return {
            "caso": self.caso,
            "fecha": self.fecha,
            "idIngreso": self.id_ingreso,
            "idOrden": self.id_orden,
            "idRecepcion": self.id_recepcion,
            "fecha_procesamiento": self.fecha_procesamiento.isoformat() if self.fecha_procesamiento else None
        }
    
    def obtener_identificador_unico(self) -> str:
        """Obtiene un identificador único para el caso."""
        return f"caso_{self.caso}_{self.id_ingreso}"
    
    def es_valido(self) -> bool:
        """Valida si el caso tiene los datos mínimos necesarios."""
        return bool(self.caso and self.id_ingreso and self.id_orden and self.id_recepcion)
    
    def __str__(self) -> str:
        """Representación string del caso."""
        return f"Caso {self.caso} - Ingreso: {self.id_ingreso}"