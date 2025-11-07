"""
Modelo de resultado de automatización.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class ResultadoAutomatizacion:
    """Resultado de un proceso de automatización."""
    
    exitoso: bool
    mensaje: str
    datos_procesados: int = 0
    errores_encontrados: int = 0
    tiempo_inicio: Optional[datetime] = None
    tiempo_fin: Optional[datetime] = None
    detalles: Optional[Dict[str, Any]] = None
    registros_log: Optional[List[str]] = None
    
    def __post_init__(self):
        """Inicializa valores por defecto después de la creación."""
        if self.detalles is None:
            self.detalles = {}
        if self.registros_log is None:
            self.registros_log = []
        if self.tiempo_fin is None:
            self.tiempo_fin = datetime.now()
    
    @property
    def duracion_segundos(self) -> float:
        """Calcula la duración del proceso en segundos."""
        if self.tiempo_inicio and self.tiempo_fin:
            return (self.tiempo_fin - self.tiempo_inicio).total_seconds()
        return 0.0
    
    @property
    def porcentaje_exito(self) -> float:
        """Calcula el porcentaje de éxito."""
        total = self.datos_procesados
        if total == 0:
            return 0.0
        exitosos = total - self.errores_encontrados
        return (exitosos / total) * 100.0
    
    def agregar_detalle(self, clave: str, valor: Any):
        """Agrega un detalle al resultado."""
        if self.detalles is None:
            self.detalles = {}
        self.detalles[clave] = valor
    
    def agregar_log(self, mensaje: str):
        """Agrega un mensaje de log."""
        if self.registros_log is None:
            self.registros_log = []
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.registros_log.append(f"[{timestamp}] {mensaje}")
    
    def establecer_inicio(self):
        """Establece el tiempo de inicio."""
        self.tiempo_inicio = datetime.now()
    
    def establecer_fin(self):
        """Establece el tiempo de fin."""
        self.tiempo_fin = datetime.now()
    
    def incrementar_procesados(self, cantidad: int = 1):
        """Incrementa el contador de datos procesados."""
        self.datos_procesados += cantidad
    
    def incrementar_errores(self, cantidad: int = 1):
        """Incrementa el contador de errores."""
        self.errores_encontrados += cantidad
    
    def obtener_resumen(self) -> str:
        """Obtiene un resumen del resultado."""
        estado = "✅ EXITOSO" if self.exitoso else "❌ FALLÓ"
        duracion = f"{self.duracion_segundos:.1f}s"
        porcentaje = f"{self.porcentaje_exito:.1f}%"
        
        return (f"{estado} | Procesados: {self.datos_procesados} | "
                f"Errores: {self.errores_encontrados} | "
                f"Éxito: {porcentaje} | Duración: {duracion}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario."""
        return {
            "exitoso": self.exitoso,
            "mensaje": self.mensaje,
            "datos_procesados": self.datos_procesados,
            "errores_encontrados": self.errores_encontrados,
            "tiempo_inicio": self.tiempo_inicio.isoformat() if self.tiempo_inicio else None,
            "tiempo_fin": self.tiempo_fin.isoformat() if self.tiempo_fin else None,
            "duracion_segundos": self.duracion_segundos,
            "porcentaje_exito": self.porcentaje_exito,
            "detalles": self.detalles,
            "registros_log": self.registros_log,
            "resumen": self.obtener_resumen()
        }
    
    @classmethod
    def desde_diccionario(cls, datos: Dict[str, Any]) -> 'ResultadoAutomatizacion':
        """Crea un resultado desde un diccionario."""
        tiempo_inicio = None
        tiempo_fin = None
        
        if datos.get("tiempo_inicio"):
            tiempo_inicio = datetime.fromisoformat(datos["tiempo_inicio"])
        
        if datos.get("tiempo_fin"):
            tiempo_fin = datetime.fromisoformat(datos["tiempo_fin"])
        
        return cls(
            exitoso=datos.get("exitoso", False),
            mensaje=datos.get("mensaje", ""),
            datos_procesados=datos.get("datos_procesados", 0),
            errores_encontrados=datos.get("errores_encontrados", 0),
            tiempo_inicio=tiempo_inicio,
            tiempo_fin=tiempo_fin,
            detalles=datos.get("detalles", {}),
            registros_log=datos.get("registros_log", [])
        )
    
    @classmethod
    def crear_exitoso(cls, mensaje: str = "Proceso completado exitosamente") -> 'ResultadoAutomatizacion':
        """Crea un resultado exitoso."""
        resultado = cls(True, mensaje)
        resultado.establecer_inicio()
        resultado.establecer_fin()
        return resultado
    
    @classmethod
    def crear_fallo(cls, mensaje: str = "Proceso falló") -> 'ResultadoAutomatizacion':
        """Crea un resultado de fallo."""
        resultado = cls(False, mensaje)
        resultado.establecer_inicio()
        resultado.establecer_fin()
        return resultado
    
    @classmethod
    def crear_en_progreso(cls, mensaje: str = "Proceso iniciado") -> 'ResultadoAutomatizacion':
        """Crea un resultado para proceso en progreso."""
        resultado = cls(True, mensaje)
        resultado.establecer_inicio()
        resultado.tiempo_fin = None
        return resultado