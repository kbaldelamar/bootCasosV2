"""
DTO para la respuesta del endpoint /list-pacientes-casos?estado=0.
"""
from dataclasses import dataclass
from typing import List
from .paciente_autorizacion_dto import PacienteAutorizacionDto


@dataclass 
class RespuestaPacientesPendientesDto:
    """DTO específico para la respuesta de pacientes pendientes con estado=0."""
    
    data: List[PacienteAutorizacionDto]
    description: str
    estado_filtrado: int
    message: str
    status_code: int
    total_records: int
    
    @classmethod
    def from_api_response(cls, response_data: dict) -> 'RespuestaPacientesPendientesDto':
        """Crea una instancia desde la respuesta de la API."""
        # Procesar los pacientes del array data
        pacientes_raw = response_data.get("data", [])
        pacientes_dto = []
        
        for item in pacientes_raw:
            paciente = PacienteAutorizacionDto(
                identificacion=item.get('identificacion', ''),
                nombre=item.get('nombre', ''),
                id_municipio=item.get('idMunicipio', ''),
                telefono=item.get('telefono', ''),
                municipio=item.get('municipio', ''),
                factura_evento=item.get('facturaEvento', ''),
                tipo_contrato=item.get('tipoContrato', ''),
                fecha_factura_evento=item.get('fechaFacturaEvento', ''),
                url_orden_medica=item.get('urlOrdenMedica', ''),
                url_screenshot=item.get('urlScreenshot', ''),
                es_citologia=item.get('esCitologia', ''),
                diagnostico=item.get('diagnostico', ''),
                tipo_identificacion=item.get('tipoIdentificacion', ''),
                id_orden_procedimiento=item.get('idOrdenProcedimiento', '')
            )
            pacientes_dto.append(paciente)
        
        return cls(
            data=pacientes_dto,
            description=response_data.get("description", ""),
            estado_filtrado=response_data.get("estado_filtrado", 0),
            message=response_data.get("message", ""),
            status_code=response_data.get("statusCode", 0),
            total_records=response_data.get("total_records", len(pacientes_dto))
        )
    
    def obtener_pacientes_validos(self) -> List[PacienteAutorizacionDto]:
        """Obtiene solo los pacientes que tienen los datos mínimos necesarios."""
        return [p for p in self.data if p.identificacion and p.nombre]
    
    def obtener_pacientes_con_orden_medica(self) -> List[PacienteAutorizacionDto]:
        """Obtiene pacientes que tienen orden médica."""
        return [p for p in self.data if p.tiene_orden_medica]
    
    def obtener_pacientes_por_municipio(self, municipio: str) -> List[PacienteAutorizacionDto]:
        """Filtra pacientes por municipio."""
        return [p for p in self.data if p.municipio.upper() == municipio.upper()]
    
    def es_exitosa(self) -> bool:
        """Verifica si la respuesta fue exitosa."""
        return self.status_code == 200
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de los pacientes pendientes."""
        pacientes_validos = self.obtener_pacientes_validos()
        pacientes_con_orden = self.obtener_pacientes_con_orden_medica()
        
        municipios = {}
        for paciente in self.data:
            municipio = paciente.municipio
            municipios[municipio] = municipios.get(municipio, 0) + 1
        
        return {
            "total_pacientes": self.total_records,
            "pacientes_en_data": len(self.data),
            "pacientes_validos": len(pacientes_validos),
            "pacientes_con_orden_medica": len(pacientes_con_orden),
            "pacientes_sin_orden_medica": len(self.data) - len(pacientes_con_orden),
            "estado_filtrado": self.estado_filtrado,
            "municipios": municipios,
            "porcentaje_completitud": (len(pacientes_validos) / self.total_records * 100) if self.total_records > 0 else 0
        }
    
    def to_dict(self) -> dict:
        """Convierte la instancia a diccionario."""
        return {
            "data": [
                {
                    "identificacion": p.identificacion,
                    "nombre": p.nombre,
                    "idMunicipio": p.id_municipio,
                    "telefono": p.telefono,
                    "municipio": p.municipio,
                    "facturaEvento": p.factura_evento,
                    "tipoContrato": p.tipo_contrato,
                    "fechaFacturaEvento": p.fecha_factura_evento,
                    "urlOrdenMedica": p.url_orden_medica,
                    "urlScreenshot": p.url_screenshot,
                    "esCitologia": p.es_citologia,
                    "diagnostico": p.diagnostico,
                    "tipoIdentificacion": p.tipo_identificacion,
                    "idOrdenProcedimiento": p.id_orden_procedimiento
                }
                for p in self.data
            ],
            "description": self.description,
            "estado_filtrado": self.estado_filtrado,
            "message": self.message,
            "statusCode": self.status_code,
            "total_records": self.total_records
        }