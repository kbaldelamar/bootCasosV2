"""
DTO para manejar información de pacientes de autorizaciones Coosalud.
"""
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PacienteAutorizacionDto:
    """Modelo de datos para un paciente con autorización."""
    
    identificacion: str
    nombre: str
    id_municipio: str
    telefono: str
    municipio: str
    factura_evento: str
    tipo_contrato: str
    fecha_factura_evento: str
    url_orden_medica: str
    url_screenshot: str
    es_citologia: str
    diagnostico: str
    tipo_identificacion: str
    id_orden_procedimiento: str
    
    def __post_init__(self):
        """Procesa los datos después de la inicialización."""
        # Limpiar el nombre eliminando espacios extra
        self.nombre = " ".join(self.nombre.split())
        
        # Procesar fecha
        try:
            self.fecha_evento_obj = datetime.strptime(self.fecha_factura_evento, "%Y-%m-%d")
        except ValueError:
            self.fecha_evento_obj = None
    
    @property
    def nombre_completo_limpio(self) -> str:
        """Retorna el nombre limpio y formateado."""
        return self.nombre.title()
    
    @property
    def telefono_formateado(self) -> str:
        """Retorna el teléfono formateado."""
        if self.telefono.startswith("whatsapp"):
            return self.telefono
        
        # Limpiar número de teléfono
        numero = ''.join(filter(str.isdigit, self.telefono))
        if len(numero) == 10:
            return f"{numero[:3]} {numero[3:6]} {numero[6:]}"
        return self.telefono
    
    @property
    def tiene_orden_medica(self) -> bool:
        """Verifica si tiene orden médica disponible."""
        return bool(self.url_orden_medica and self.url_orden_medica.strip())
    
    @property
    def tiene_screenshot(self) -> bool:
        """Verifica si tiene screenshot disponible."""
        return bool(self.url_screenshot and self.url_screenshot.strip())
    
    @property
    def es_contrato_especial(self) -> bool:
        """Verifica si es un contrato especial (tipo 1)."""
        return self.tipo_contrato == "1"


@dataclass
class RespuestaPacientesDto:
    """DTO para la respuesta de la API de pacientes."""
    
    status_code: int
    message: str
    description: str
    data: List[PacienteAutorizacionDto]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RespuestaPacientesDto':
        """Crea una instancia desde un diccionario."""
        pacientes = []
        
        if data.get('data'):
            for item in data['data']:
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
                pacientes.append(paciente)
        
        return cls(
            status_code=data.get('statusCode', 0),
            message=data.get('message', ''),
            description=data.get('description', ''),
            data=pacientes
        )
    
    @property
    def tiene_pacientes(self) -> bool:
        """Verifica si hay pacientes para procesar."""
        return len(self.data) > 0
    
    @property
    def total_pacientes(self) -> int:
        """Retorna el total de pacientes."""
        return len(self.data)
    
    @property
    def es_exitoso(self) -> bool:
        """Verifica si la respuesta fue exitosa."""
        return self.status_code == 200 and self.message.upper() == "SUCCES"
    
    def pacientes_por_municipio(self) -> dict:
        """Agrupa pacientes por municipio."""
        municipios = {}
        for paciente in self.data:
            if paciente.municipio not in municipios:
                municipios[paciente.municipio] = []
            municipios[paciente.municipio].append(paciente)
        return municipios
    
    def pacientes_por_tipo_contrato(self) -> dict:
        """Agrupa pacientes por tipo de contrato."""
        contratos = {}
        for paciente in self.data:
            tipo = f"Tipo {paciente.tipo_contrato}"
            if tipo not in contratos:
                contratos[tipo] = []
            contratos[tipo].append(paciente)
        return contratos