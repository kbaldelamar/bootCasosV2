"""
DTO para la respuesta del endpoint /pacientes-casos.
"""
from dataclasses import dataclass
from typing import List, Optional
from .caso_dto import CasoDto


@dataclass
class RespuestaCasosDto:
    """DTO que representa la respuesta completa del endpoint de casos."""
    
    data: List[CasoDto]
    message: str
    status_code: int
    description: Optional[str] = None
    total_records: Optional[int] = None
    
    def __post_init__(self):
        """Calcula el total de registros si no se proporciona."""
        if self.total_records is None:
            self.total_records = len(self.data)
    
    @classmethod
    def from_api_response(cls, response_data: dict) -> 'RespuestaCasosDto':
        """Crea una instancia desde la respuesta de la API."""
        # Extraer los casos del array data
        casos_raw = response_data.get("data", [])
        casos_dto = [CasoDto.from_dict(caso) for caso in casos_raw]
        
        return cls(
            data=casos_dto,
            message=response_data.get("message", ""),
            status_code=response_data.get("statusCode", 0),
            description=response_data.get("description"),
            total_records=len(casos_dto)  # Calcular basado en los datos
        )
    
    def obtener_casos_validos(self) -> List[CasoDto]:
        """Obtiene solo los casos que son válidos."""
        return [caso for caso in self.data if caso.es_valido()]
    
    def obtener_casos_por_fecha(self, fecha_inicio: str = None, fecha_fin: str = None) -> List[CasoDto]:
        """Filtra casos por rango de fechas."""
        casos_filtrados = []
        for caso in self.data:
            if caso.fecha_procesamiento:
                # Aquí podrías implementar filtrado por fechas si es necesario
                casos_filtrados.append(caso)
        return casos_filtrados
    
    def es_exitosa(self) -> bool:
        """Verifica si la respuesta fue exitosa."""
        return self.status_code == 200
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de los casos."""
        casos_validos = self.obtener_casos_validos()
        return {
            "total_casos": self.total_records,
            "casos_validos": len(casos_validos),
            "casos_invalidos": self.total_records - len(casos_validos),
            "porcentaje_validez": (len(casos_validos) / self.total_records * 100) if self.total_records > 0 else 0
        }
    
    def to_dict(self) -> dict:
        """Convierte la instancia a diccionario."""
        return {
            "data": [caso.to_dict() for caso in self.data],
            "message": self.message,
            "statusCode": self.status_code,
            "description": self.description,
            "total_records": self.total_records
        }