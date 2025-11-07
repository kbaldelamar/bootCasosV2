"""
Procesador base para automatización.
Responsabilidad única: Proveer funcionalidad común para todos los procesadores.
"""
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from ..nucleo.controlador_automatizacion import ControladorAutomatizacion
from ..modelos.tarea_automatizacion import TareaAutomatizacion
from ..modelos.resultado_proceso import ResultadoProceso


class ProcesadorBase(ABC):
    """Clase base abstracta para todos los procesadores."""
    
    def __init__(self, contexto: str, callback_log: Optional[Callable] = None):
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Controlador de automatización
        self.controlador = ControladorAutomatizacion(contexto, callback_log)
        
        # Estado del procesador
        self.ejecutando = False
        self.pausado = False
        self.tareas_procesadas = 0
        self.tareas_exitosas = 0
        self.tareas_fallidas = 0
        
        # Datos específicos del procesador
        self.datos_entrada: List[Dict[str, Any]] = []
        self.resultados: List[ResultadoProceso] = []
        
        self._log(f"ProcesadorBase inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        mensaje_completo = f"[{timestamp}] {self.contexto}: {mensaje}"
        
        getattr(self.logger, nivel)(mensaje)
        if self.callback_log:
            try:
                self.callback_log(mensaje_completo, nivel, self.contexto)
            except Exception as e:
                self.logger.warning(f"Error en callback de log: {e}")
    
    @abstractmethod
    async def obtener_datos(self) -> List[Dict[str, Any]]:
        """
        Obtiene los datos a procesar desde la API.
        
        Returns:
            List[Dict]: Lista de datos a procesar
        """
        pass
    
    @abstractmethod
    async def procesar_item_individual(self, datos_item: Dict[str, Any]) -> ResultadoProceso:
        """
        Procesa un item individual.
        
        Args:
            datos_item: Datos del item a procesar
            
        Returns:
            ResultadoProceso: Resultado del procesamiento
        """
        pass
    
    @abstractmethod
    def crear_tarea(self, datos_item: Dict[str, Any], indice: int) -> TareaAutomatizacion:
        """
        Crea una tarea de automatización desde los datos.
        
        Args:
            datos_item: Datos del item
            indice: Índice del item en la lista
            
        Returns:
            TareaAutomatizacion: Tarea creada
        """
        pass
    
    async def inicializar(self) -> bool:
        """
        Inicializa el procesador y obtiene los datos.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            self._log("🚀 Inicializando procesador...")
            
            # Obtener datos desde la API
            self.datos_entrada = await self.obtener_datos()
            if not self.datos_entrada:
                raise Exception("No se obtuvieron datos para procesar")
            
            self._log(f"📊 Datos obtenidos: {len(self.datos_entrada)} items")
            
            # Crear tareas de automatización
            tareas = []
            for i, datos_item in enumerate(self.datos_entrada):
                tarea = self.crear_tarea(datos_item, i)
                tareas.append(tarea)
            
            # Inicializar controlador con las tareas
            if not await self.controlador.inicializar(tareas):
                raise Exception("Error inicializando controlador de automatización")
            
            self._log("✅ Procesador inicializado correctamente")
            return True
            
        except Exception as e:
            self._log(f"❌ Error inicializando procesador: {e}", "error")
            return False
    
    async def ejecutar(self) -> bool:
        """
        Ejecuta el procesamiento completo.
        
        Returns:
            bool: True si se completó exitosamente
        """
        try:
            if self.ejecutando:
                self._log("⚠️ Procesador ya está ejecutando")
                return False
            
            self.ejecutando = True
            self._reiniciar_contadores()
            
            self._log(f"🔥 Iniciando procesamiento de {len(self.datos_entrada)} items...")
            
            # Ejecutar el controlador de automatización
            exito = await self.controlador.ejecutar()
            
            # Generar resumen final
            await self._generar_resumen_final()
            
            if exito:
                self._log("🎉 Procesamiento completado exitosamente")
            else:
                self._log("⚠️ Procesamiento completado con errores")
            
            return exito
            
        except Exception as e:
            self._log(f"💥 Error crítico en procesamiento: {e}", "error")
            return False
        finally:
            self.ejecutando = False
    
    async def pausar(self):
        """Pausa la ejecución actual."""
        if not self.ejecutando:
            self._log("⚠️ No hay proceso ejecutando para pausar")
            return
        
        self.pausado = True
        await self.controlador.pausar()
        self._log("⏸️ Procesador pausado")
    
    async def reanudar(self):
        """Reanuda la ejecución pausada."""
        if not self.pausado:
            self._log("⚠️ No hay proceso pausado para reanudar")
            return
        
        self.pausado = False
        await self.controlador.reanudar()
        self._log("▶️ Procesador reanudado")
    
    async def detener(self):
        """Detiene completamente la ejecución."""
        if not self.ejecutando:
            self._log("⚠️ No hay proceso ejecutando para detener")
            return
        
        self.ejecutando = False
        self.pausado = False
        await self.controlador.detener()
        self._log("⏹️ Procesador detenido")
    
    def _reiniciar_contadores(self):
        """Reinicia los contadores del procesador."""
        self.tareas_procesadas = 0
        self.tareas_exitosas = 0
        self.tareas_fallidas = 0
        self.resultados.clear()
    
    async def _generar_resumen_final(self):
        """Genera un resumen final del procesamiento."""
        try:
            estado_final = self.controlador.obtener_estado()
            sesion = estado_final.get('sesion', {})
            progreso = sesion.get('progreso', {})
            
            self.tareas_procesadas = progreso.get('procesados', 0)
            self.tareas_exitosas = progreso.get('exitosos', 0)
            self.tareas_fallidas = progreso.get('fallidos', 0)
            
            self._log("📊 === RESUMEN FINAL ===")
            self._log(f"Total procesados: {self.tareas_procesadas}")
            self._log(f"Exitosos: {self.tareas_exitosas}")
            self._log(f"Fallidos: {self.tareas_fallidas}")
            self._log(f"Tasa de éxito: {sesion.get('tasa_exito', 0):.1f}%")
            self._log(f"Velocidad promedio: {sesion.get('velocidad', 0):.1f} items/min")
            
        except Exception as e:
            self._log(f"❌ Error generando resumen final: {e}", "error")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del procesador.
        
        Returns:
            dict: Estado completo del procesador
        """
        try:
            estado_controlador = self.controlador.obtener_estado()
            
            return {
                "contexto": self.contexto,
                "ejecutando": self.ejecutando,
                "pausado": self.pausado,
                "datos_cargados": len(self.datos_entrada),
                "tareas_procesadas": self.tareas_procesadas,
                "tareas_exitosas": self.tareas_exitosas,
                "tareas_fallidas": self.tareas_fallidas,
                "controlador": estado_controlador,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._log(f"❌ Error obteniendo estado: {e}", "error")
            return {"error": str(e)}
    
    def obtener_progreso(self) -> Dict[str, Any]:
        """
        Obtiene información de progreso simplificada.
        
        Returns:
            dict: Información de progreso
        """
        try:
            estado = self.controlador.obtener_estado()
            sesion = estado.get('sesion', {})
            progreso = sesion.get('progreso', {})
            
            return {
                "total": progreso.get('total', len(self.datos_entrada)),
                "procesados": progreso.get('procesados', 0),
                "exitosos": progreso.get('exitosos', 0),
                "fallidos": progreso.get('fallidos', 0),
                "porcentaje": progreso.get('porcentaje', 0),
                "velocidad": sesion.get('velocidad', 0),
                "estado": sesion.get('estado_proceso', 'detenido')
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo progreso: {e}")
            return {}
    
    async def validar_conexion(self) -> bool:
        """
        Valida que la conexión con los servicios necesarios esté disponible.
        
        Returns:
            bool: True si la conexión es válida
        """
        try:
            # Validación básica - cada procesador puede sobrescribir
            self._log("🔍 Validando conexión...")
            
            # Aquí cada procesador específico puede agregar sus validaciones
            return True
            
        except Exception as e:
            self._log(f"❌ Error validando conexión: {e}", "error")
            return False