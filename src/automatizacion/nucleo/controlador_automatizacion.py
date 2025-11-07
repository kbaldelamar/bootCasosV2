"""
Controlador principal de automatización.
Responsabilidad única: Coordinar todos los componentes del sistema de automatización.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .gestor_navegador import GestorNavegador
from .gestor_sesion import GestorSesion
from ..servicios.servicio_navegacion import ServicioNavegacion
from ..servicios.orquestador_login import OrquestadorLogin
from ..modelos.estado_automatizacion import EstadoProceso
from ..modelos.tarea_automatizacion import TareaAutomatizacion
from ..errores.clasificador_errores import ClasificadorErrores
from ..errores.gestor_reintentos import GestorReintentos


class ControladorAutomatizacion:
    """Controlador principal que coordina todo el sistema de automatización."""
    
    def __init__(self, contexto: str, callback_log: Optional[Callable] = None):
        self.contexto = contexto
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        self.callback_log = callback_log
        
        # Componentes principales
        self.gestor_navegador = GestorNavegador(contexto)
        self.gestor_sesion = GestorSesion(contexto)
        self.servicio_navegacion = None  # Se inicializa después del navegador
        self.orquestador_login = None    # Se inicializa después del navegador
        
        # Sistema de errores
        self.clasificador_errores = ClasificadorErrores()
        self.gestor_reintentos = GestorReintentos()
        
        # Control de ejecución
        self.ejecutando = False
        self.task_principal = None
        self.cola_tareas: List[TareaAutomatizacion] = []
        
        self._log(f"ControladorAutomatizacion inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        mensaje_completo = f"[{timestamp}] {self.contexto}: {mensaje}"
        
        # Log interno
        getattr(self.logger, nivel)(mensaje)
        
        # Callback externo si existe
        if self.callback_log:
            try:
                self.callback_log(mensaje_completo, nivel, self.contexto)
            except Exception as e:
                self.logger.warning(f"Error en callback de log: {e}")
    
    async def inicializar(self, tareas: List[TareaAutomatizacion]) -> bool:
        """
        Inicializa el sistema de automatización.
        
        Args:
            tareas: Lista de tareas a procesar
            
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            self._log("🚀 Iniciando sistema de automatización...")
            
            # Validar tareas
            if not tareas:
                raise Exception("No hay tareas para procesar")
            
            # Inicializar estado de sesión
            self.gestor_sesion.inicializar_estado(len(tareas))
            self.cola_tareas = tareas.copy()
            
            # Inicializar navegador
            self._log("🌐 Iniciando navegador...")
            if not await self.gestor_navegador.iniciar_navegador():
                raise Exception("No se pudo iniciar el navegador")
            
            # Inicializar servicios dependientes
            self.servicio_navegacion = ServicioNavegacion(
                self.gestor_navegador, 
                self.contexto, 
                self.callback_log
            )
   
            self.orquestador_login = OrquestadorLogin(
                self.gestor_navegador,
                self.contexto,
                self.callback_log
            )
            
            # Navegar a página de login
            self._log("🔗 Navegando a página de login...")
            if not await self.servicio_navegacion.ir_a_login():
                raise Exception("No se pudo navegar a la página de login")
            
            # Realizar login
            self._log("🔑 Iniciando proceso de autenticación...")
            if not await self.orquestador_login.ejecutar_login_completo():
                raise Exception("No se pudo completar el login")
            
            self._log("✅ Sistema inicializado correctamente")
            return True
            
        except Exception as e:
            self._log(f"❌ Error en inicialización: {e}", "error")
            await self._limpiar_recursos()
            return False
    
    async def ejecutar(self) -> bool:
        """
        Ejecuta el proceso de automatización completo.
        
        Returns:
            bool: True si se completó exitosamente
        """
        try:
            if self.ejecutando:
                self._log("⚠️ Ya hay un proceso en ejecución")
                return False
            
            self.ejecutando = True
            self.gestor_sesion.iniciar_sesion()
            
            self._log(f"📊 Iniciando procesamiento de {len(self.cola_tareas)} tareas...")
            
            # Ejecutar tareas con manejo de errores
            await self._ejecutar_con_recuperacion()
            
            self._log("🎉 Proceso de automatización completado")
            return True
            
        except Exception as e:
            self._log(f"💥 Error crítico en ejecución: {e}", "error")
            return False
        finally:
            self.ejecutando = False
    
    async def _ejecutar_con_recuperacion(self):
        """Ejecuta las tareas con sistema de recuperación automática."""
        intentos_globales = 0
        max_intentos_globales = 3
        
        while intentos_globales < max_intentos_globales and self.cola_tareas:
            try:
                # Procesar todas las tareas pendientes
                await self._procesar_tareas()
                break  # Si llegamos aquí, todo fue exitoso
                
            except Exception as e:
                intentos_globales += 1
                tipo_error = self.clasificador_errores.clasificar(e)
                
                self._log(f"🔥 Error crítico (intento {intentos_globales}/{max_intentos_globales}): {e}", "error")
                
                # Verificar si podemos recuperar
                if intentos_globales >= max_intentos_globales:
                    self._log("❌ Máximo de intentos alcanzado. Proceso terminado.", "error")
                    self.gestor_sesion.detener_sesion("Fallo definitivo después de 3 intentos")
                    break
                
                # Intentar recuperación
                self._log(f"🔄 Iniciando recuperación automática...", "warning")
                self.gestor_sesion.iniciar_recuperacion()
                
                if await self._recuperar_sistema():
                    self._log("✅ Recuperación exitosa, continuando proceso...")
                    self.gestor_sesion.recuperacion_exitosa()
                else:
                    self._log("❌ Recuperación fallida", "error")
                    break
    
    async def _procesar_tareas(self):
        """Procesa todas las tareas en la cola."""
        indice = 0
        
        while indice < len(self.cola_tareas) and self.ejecutando:
            tarea = self.cola_tareas[indice]
            
            # Verificar si está pausado
            while self.gestor_sesion.pausada and self.ejecutando:
                await asyncio.sleep(0.5)
            
            if not self.ejecutando:
                break
            
            try:
                self._log(f"📝 Procesando tarea {indice + 1}/{len(self.cola_tareas)}: {tarea.id}")
                
                # Aquí es donde se llamaría al procesador específico
                # Por ahora, simulamos el procesamiento
                await self._procesar_tarea_individual(tarea)
                
                self.gestor_sesion.actualizar_progreso(True, f"Tarea {tarea.id} completada")
                indice += 1
                
            except Exception as e:
                self._log(f"❌ Error procesando tarea {tarea.id}: {e}", "error")
                
                # Clasificar error y decidir acción
                tipo_error = self.clasificador_errores.clasificar(e)
                
                if self.gestor_reintentos.puede_reintentar(tipo_error, tarea.reintentos):
                    self._log(f"🔄 Reintentando tarea {tarea.id}...")
                    tarea.reintentos += 1
                    # No incrementamos indice para reintentar la misma tarea
                else:
                    self._log(f"⏭️ Saltando tarea {tarea.id} (máximo de reintentos alcanzado)")
                    self.gestor_sesion.actualizar_progreso(False, f"Tarea {tarea.id} falló")
                    indice += 1
    
    async def _procesar_tarea_individual(self, tarea: TareaAutomatizacion):
        """
        Procesa una tarea individual.
        NOTA: Este método será implementado por los procesadores específicos.
        """
        # Simulación de procesamiento
        await asyncio.sleep(0.1)
        
        # Aquí se llamaría al procesador específico según el tipo de tarea
        if tarea.tipo == "procesar_paciente":
            # Llamar a ProcesadorPacientes
            pass
        elif tarea.tipo == "actualizar_caso":
            # Llamar a ProcesadorCasos
            pass
    
    async def _recuperar_sistema(self) -> bool:
        """
        Intenta recuperar el sistema después de un error crítico.
        
        Returns:
            bool: True si la recuperación fue exitosa
        """
        try:
            self._log("🔧 Cerrando navegador actual...")
            await self.gestor_navegador.cerrar_navegador()
            
            self._log("⏳ Esperando antes de reiniciar...")
            await asyncio.sleep(5)
            
            self._log("🌐 Reiniciando navegador...")
            if not await self.gestor_navegador.iniciar_navegador():
                return False
            
            self._log("🔗 Re-navegando a login...")
            if not await self.servicio_navegacion.ir_a_login():
                return False
            
            self._log("🔑 Re-autenticando...")
            if not await self.orquestador_login.ejecutar_login_completo():
                return False
            
            return True
            
        except Exception as e:
            self._log(f"❌ Error en recuperación: {e}", "error")
            return False
    
    async def pausar(self):
        """Pausa la ejecución actual."""
        self.gestor_sesion.pausar_sesion()
        self._log("⏸️ Proceso pausado")
    
    async def reanudar(self):
        """Reanuda la ejecución pausada."""
        self.gestor_sesion.reanudar_sesion()
        self._log("▶️ Proceso reanudado")
    
    async def detener(self):
        """Detiene completamente la ejecución."""
        self.ejecutando = False
        self.gestor_sesion.detener_sesion("Detenido por usuario")
        self._log("⏹️ Proceso detenido")
        
        if self.task_principal:
            self.task_principal.cancel()
        
        await self._limpiar_recursos()
    
    async def _limpiar_recursos(self):
        """Limpia todos los recursos utilizados."""
        try:
            await self.gestor_navegador.cerrar_navegador()
            self._log("🧹 Recursos limpiados")
        except Exception as e:
            self._log(f"⚠️ Error limpiando recursos: {e}", "warning")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del controlador.
        
        Returns:
            dict: Estado completo del sistema
        """
        return {
            "contexto": self.contexto,
            "ejecutando": self.ejecutando,
            "sesion": self.gestor_sesion.obtener_resumen(),
            "navegador": self.gestor_navegador.obtener_estado(),
            "tareas_pendientes": len(self.cola_tareas),
            "timestamp": datetime.now().isoformat()
        }