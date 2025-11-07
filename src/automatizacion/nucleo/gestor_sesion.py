"""
Gestor de sesiones para automatización.
Responsabilidad única: Mantener y gestionar el estado de las sesiones de automatización.
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from ..modelos.estado_automatizacion import EstadoAutomatizacion, EstadoProceso


class GestorSesion:
    """Gestor responsable del estado y ciclo de vida de las sesiones."""
    
    def __init__(self, contexto: str):
        self.contexto = contexto
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Estado de la sesión
        self.sesion_id = f"{contexto}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.estado: EstadoAutomatizacion = None
        self.activa = False
        self.pausada = False
        
        # Datos de la sesión
        self.datos_sesion: Dict = {}
        self.metadatos: Dict = {
            "contexto": contexto,
            "inicio": datetime.now(),
            "version": "1.0.0"
        }
        
        self.logger.info(f"GestorSesion inicializado - ID: {self.sesion_id}")
    
    def inicializar_estado(self, items_totales: int) -> EstadoAutomatizacion:
        """
        Inicializa el estado de automatización.
        
        Args:
            items_totales: Número total de items a procesar
            
        Returns:
            EstadoAutomatizacion: Estado inicializado
        """
        try:
            self.estado = EstadoAutomatizacion(
                contexto=self.contexto,
                estado=EstadoProceso.DETENIDO,
                items_totales=items_totales,
                items_procesados=0,
                items_exitosos=0,
                items_fallidos=0,
                tiempo_inicio=None,
                intentos_recuperacion=0,
                mensaje_estado=f"Sesión {self.sesion_id} inicializada"
            )
            
            self.logger.info(f"Estado inicializado para {items_totales} items")
            return self.estado
            
        except Exception as e:
            self.logger.error(f"Error inicializando estado: {e}")
            raise
    
    def iniciar_sesion(self):
        """Inicia la sesión de automatización."""
        try:
            if not self.estado:
                raise Exception("Estado no inicializado")
            
            self.activa = True
            self.pausada = False
            self.estado.estado = EstadoProceso.INICIANDO
            self.estado.tiempo_inicio = datetime.now()
            self.estado.mensaje_estado = "Sesión iniciada"
            
            self.metadatos["inicio_real"] = datetime.now()
            
            self.logger.info(f"Sesión iniciada: {self.sesion_id}")
            
        except Exception as e:
            self.logger.error(f"Error iniciando sesión: {e}")
            raise
    
    def pausar_sesion(self):
        """Pausa la sesión actual."""
        try:
            if not self.activa:
                self.logger.warning("Intento de pausar sesión no activa")
                return
            
            self.pausada = True
            self.estado.estado = EstadoProceso.PAUSADO
            self.estado.mensaje_estado = "Sesión pausada por el usuario"
            
            self.logger.info(f"Sesión pausada: {self.sesion_id}")
            
        except Exception as e:
            self.logger.error(f"Error pausando sesión: {e}")
    
    def reanudar_sesion(self):
        """Reanuda la sesión pausada."""
        try:
            if not self.activa or not self.pausada:
                self.logger.warning("Intento de reanudar sesión que no está pausada")
                return
            
            self.pausada = False
            self.estado.estado = EstadoProceso.PROCESANDO
            self.estado.mensaje_estado = "Sesión reanudada"
            
            self.logger.info(f"Sesión reanudada: {self.sesion_id}")
            
        except Exception as e:
            self.logger.error(f"Error reanudando sesión: {e}")
    
    def detener_sesion(self, razon: str = "Detenida por usuario"):
        """
        Detiene la sesión actual.
        
        Args:
            razon: Razón por la cual se detiene la sesión
        """
        try:
            self.activa = False
            self.pausada = False
            
            if self.estado:
                self.estado.estado = EstadoProceso.DETENIDO
                self.estado.mensaje_estado = razon
            
            self.metadatos["fin"] = datetime.now()
            self.metadatos["razon_fin"] = razon
            
            self.logger.info(f"Sesión detenida: {self.sesion_id} - Razón: {razon}")
            
        except Exception as e:
            self.logger.error(f"Error deteniendo sesión: {e}")
    
    def actualizar_progreso(self, exitoso: bool = True, mensaje: str = ""):
        """
        Actualiza el progreso de la sesión.
        
        Args:
            exitoso: Si el último item fue procesado exitosamente
            mensaje: Mensaje descriptivo del estado actual
        """
        try:
            if not self.estado:
                return
            
            self.estado.incrementar_procesado(exitoso)
            
            if mensaje:
                self.estado.mensaje_estado = mensaje
            
            # Verificar si se completó
            if self.estado.items_procesados >= self.estado.items_totales:
                self.estado.estado = EstadoProceso.COMPLETADO
                self.estado.mensaje_estado = "Proceso completado"
                self.detener_sesion("Proceso completado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error actualizando progreso: {e}")
    
    def marcar_error(self, error: str):
        """
        Marca un error en la sesión.
        
        Args:
            error: Descripción del error
        """
        try:
            if self.estado:
                self.estado.estado = EstadoProceso.ERROR
                self.estado.mensaje_estado = f"Error: {error}"
            
            self.logger.error(f"Error en sesión {self.sesion_id}: {error}")
            
        except Exception as e:
            self.logger.error(f"Error marcando error en sesión: {e}")
    
    def iniciar_recuperacion(self):
        """Inicia un proceso de recuperación."""
        try:
            if not self.estado:
                return
            
            self.estado.incrementar_intento_recuperacion()
            self.estado.estado = EstadoProceso.RECUPERANDO
            self.estado.mensaje_estado = f"Recuperando... (Intento {self.estado.intentos_recuperacion}/{self.estado.max_intentos})"
            
            self.logger.info(f"Iniciando recuperación - Intento {self.estado.intentos_recuperacion}")
            
        except Exception as e:
            self.logger.error(f"Error iniciando recuperación: {e}")
    
    def recuperacion_exitosa(self):
        """Marca una recuperación como exitosa."""
        try:
            if self.estado:
                self.estado.estado = EstadoProceso.PROCESANDO
                self.estado.mensaje_estado = "Recuperación exitosa, continuando proceso"
            
            self.logger.info("Recuperación completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error marcando recuperación exitosa: {e}")
    
    def obtener_estado_actual(self) -> Optional[EstadoAutomatizacion]:
        """
        Obtiene el estado actual de la automatización.
        
        Returns:
            EstadoAutomatizacion: Estado actual o None si no está inicializado
        """
        return self.estado
    
    def obtener_resumen(self) -> Dict:
        """
        Obtiene un resumen completo de la sesión.
        
        Returns:
            dict: Resumen de la sesión
        """
        resumen = {
            "sesion_id": self.sesion_id,
            "contexto": self.contexto,
            "activa": self.activa,
            "pausada": self.pausada,
            "metadatos": self.metadatos.copy()
        }
        
        if self.estado:
            resumen.update({
                "estado_proceso": self.estado.estado.value,
                "progreso": {
                    "total": self.estado.items_totales,
                    "procesados": self.estado.items_procesados,
                    "exitosos": self.estado.items_exitosos,
                    "fallidos": self.estado.items_fallidos,
                    "porcentaje": self.estado.porcentaje_progreso
                },
                "velocidad": self.estado.velocidad_promedio,
                "tasa_exito": self.estado.tasa_exito,
                "recuperaciones": self.estado.intentos_recuperacion,
                "mensaje": self.estado.mensaje_estado
            })
        
        return resumen
    
    def guardar_dato_sesion(self, clave: str, valor):
        """
        Guarda un dato específico en la sesión.
        
        Args:
            clave: Clave del dato
            valor: Valor a guardar
        """
        self.datos_sesion[clave] = valor
    
    def obtener_dato_sesion(self, clave: str, default=None):
        """
        Obtiene un dato específico de la sesión.
        
        Args:
            clave: Clave del dato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del dato o default si no existe
        """
        return self.datos_sesion.get(clave, default)