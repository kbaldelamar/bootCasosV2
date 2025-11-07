"""
Controlador principal de automatización dual que integra todos los componentes.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.automatizacion.nucleo.gestor_navegador import GestorNavegador
from src.automatizacion.nucleo.gestor_sesion import GestorSesion
from src.automatizacion.servicios.servicio_navegacion import ServicioNavegacion
from src.automatizacion.servicios.servicio_login import ServicioLogin
from src.automatizacion.servicios.servicio_captcha import ServicioCaptcha
from src.automatizacion.servicios.servicio_verificacion import ServicioVerificacion
from src.automatizacion.servicios.orquestador_login import OrquestadorLogin
from src.automatizacion.procesadores.procesador_pacientes import ProcesadorPacientes
from src.automatizacion.procesadores.procesador_casos import ProcesadorCasos
from src.automatizacion.errores.servicio_recuperacion import ServicioRecuperacion
from src.automatizacion.modelos.resultado_automatizacion import ResultadoAutomatizacion
from src.automatizacion.modelos.configuracion_automatizacion import ConfiguracionAutomatizacion


class ControladorAutomatizacionPrincipal:
    """Controlador principal que orquesta toda la automatización dual."""
    
    def __init__(self, callback_log: Optional[Callable] = None):
        self.callback_log = callback_log
        self.logger = logging.getLogger(__name__)
        
        # Estado de los procesos
        self.proceso_pacientes_activo = False
        self.proceso_casos_activo = False
        
        # Gestores principales
        self.gestor_navegador_pacientes = None
        self.gestor_navegador_casos = None
        self.gestor_sesion_pacientes = None
        self.gestor_sesion_casos = None
        
        # Servicios compartidos
        self.servicio_captcha = None  # Se creará cuando sea necesario
        
        # Procesadores
        self.procesador_pacientes = None
        self.procesador_casos = None
        
        # Servicios de recuperación
        self.servicio_recuperacion_pacientes = None
        self.servicio_recuperacion_casos = None
        
        # Resultados
        self.resultados_pacientes = None
        self.resultados_casos = None
        
        self.logger.info("ControladorAutomatizacionPrincipal inicializado")
    
    def _log(self, mensaje: str, nivel: str = "info", contexto: str = "principal"):
        """Envía log tanto al logger como al callback."""
        # Limpiar emojis para evitar problemas de encoding en Windows
        mensaje_limpio = (mensaje.replace("🔧", "[INIT]")
                                .replace("✅", "[OK]")
                                .replace("❌", "[ERROR]") 
                                .replace("🚀", "[START]")
                                .replace("💥", "[CRITICAL]")
                                .replace("🛑", "[STOP]")
                                .replace("⚠️", "[WARNING]")
                                .replace("🧹", "[CLEAN]")
                                .replace("🔄", "[RESTART]"))
        
        getattr(self.logger, nivel)(mensaje_limpio)
        if self.callback_log:
            try:
                self.callback_log(mensaje, nivel, contexto)  # UI puede manejar emojis
            except Exception:
                pass
    
    async def inicializar_automatizacion_pacientes(self, configuracion: ConfiguracionAutomatizacion) -> bool:
        """Inicializa el sistema de automatización para pacientes."""
        try:
            self._log("🔧 Inicializando automatización de pacientes...", "info", "pacientes")
            
            # Crear gestor de navegador independiente
            self.gestor_navegador_pacientes = GestorNavegador("pacientes")
            if not await self.gestor_navegador_pacientes.inicializar():
                raise Exception("No se pudo inicializar navegador de pacientes")
            
            # Crear gestor de sesión
            self.gestor_sesion_pacientes = GestorSesion("pacientes")
            
            # Crear servicios
            servicio_navegacion = ServicioNavegacion(
                self.gestor_navegador_pacientes, 
                "pacientes", 
                self.callback_log
            )
            
            # Crear servicio de captcha específico para pacientes
            servicio_captcha_pacientes = ServicioCaptcha(
                self.gestor_navegador_pacientes,
                "pacientes",
                self.callback_log
            )
            
            servicio_login = ServicioLogin(
                self.gestor_navegador_pacientes, 
                servicio_captcha_pacientes, 
                "pacientes", 
                self.callback_log
            )
            
            servicio_verificacion = ServicioVerificacion(
                self.gestor_navegador_pacientes, 
                "pacientes", 
                self.callback_log
            )
            
            # Crear orquestador
            orquestador_login = OrquestadorLogin(
                servicio_navegacion, 
                servicio_login, 
                servicio_verificacion, 
                self.gestor_sesion_pacientes,
                "pacientes",
                self.callback_log
            )
            
            # Crear servicio de recuperación
            self.servicio_recuperacion_pacientes = ServicioRecuperacion(
                self.gestor_navegador_pacientes,
                servicio_navegacion,
                orquestador_login,
                "pacientes",
                self.callback_log
            )
            
            # Crear procesador
            self.procesador_pacientes = ProcesadorPacientes(
                orquestador_login,
                self.gestor_navegador_pacientes,
                self.servicio_recuperacion_pacientes,
                configuracion,
                "pacientes",
                self.callback_log
            )
            
            self._log("✅ Automatización de pacientes inicializada", "success", "pacientes")
            return True
            
        except Exception as e:
            self._log(f"❌ Error inicializando automatización de pacientes: {e}", "error", "pacientes")
            return False
    
    async def inicializar_automatizacion_casos(self, configuracion: ConfiguracionAutomatizacion) -> bool:
        """Inicializa el sistema de automatización para casos."""
        try:
            self._log("🔧 Inicializando automatización de casos...", "info", "casos")
            
            # Crear gestor de navegador independiente
            self.gestor_navegador_casos = GestorNavegador("casos")
            if not await self.gestor_navegador_casos.inicializar():
                raise Exception("No se pudo inicializar navegador de casos")
            
            # Crear gestor de sesión
            self.gestor_sesion_casos = GestorSesion("casos")
            
            # Crear servicios
            servicio_navegacion = ServicioNavegacion(
                self.gestor_navegador_casos, 
                "casos", 
                self.callback_log
            )
            
            # Crear servicio de captcha específico para casos
            servicio_captcha_casos = ServicioCaptcha(
                self.gestor_navegador_casos,
                "casos",
                self.callback_log
            )
            
            servicio_login = ServicioLogin(
                self.gestor_navegador_casos, 
                servicio_captcha_casos, 
                "casos", 
                self.callback_log
            )
            
            servicio_verificacion = ServicioVerificacion(
                self.gestor_navegador_casos, 
                "casos", 
                self.callback_log
            )
            
            # Crear orquestador
            orquestador_login = OrquestadorLogin(
                servicio_navegacion, 
                servicio_login, 
                servicio_verificacion, 
                self.gestor_sesion_casos,
                "casos",
                self.callback_log
            )
            
            # Crear servicio de recuperación
            self.servicio_recuperacion_casos = ServicioRecuperacion(
                self.gestor_navegador_casos,
                servicio_navegacion,
                orquestador_login,
                "casos",
                self.callback_log
            )
            
            # Crear procesador
            self.procesador_casos = ProcesadorCasos(
                orquestador_login,
                self.gestor_navegador_casos,
                self.servicio_recuperacion_casos,
                configuracion,
                "casos",
                self.callback_log
            )
            
            self._log("✅ Automatización de casos inicializada", "success", "casos")
            return True
            
        except Exception as e:
            self._log(f"❌ Error inicializando automatización de casos: {e}", "error", "casos")
            return False
    
    async def ejecutar_automatizacion_pacientes(self, configuracion: ConfiguracionAutomatizacion) -> ResultadoAutomatizacion:
        """Ejecuta la automatización de pacientes."""
        try:
            if self.proceso_pacientes_activo:
                return ResultadoAutomatizacion(
                    False, "Proceso de pacientes ya está en ejecución"
                )
            
            self.proceso_pacientes_activo = True
            self._log("🚀 Iniciando proceso de automatización de pacientes", "info", "pacientes")
            
            # Inicializar si no está inicializado
            if not self.procesador_pacientes:
                if not await self.inicializar_automatizacion_pacientes(configuracion):
                    raise Exception("No se pudo inicializar automatización de pacientes")
            
            # Ejecutar procesamiento
            resultado = await self.procesador_pacientes.procesar()
            self.resultados_pacientes = resultado
            
            if resultado.exitoso:
                self._log("✅ Automatización de pacientes completada exitosamente", "success", "pacientes")
            else:
                self._log(f"❌ Automatización de pacientes falló: {resultado.mensaje}", "error", "pacientes")
            
            return resultado
            
        except Exception as e:
            self._log(f"💥 Error crítico en automatización de pacientes: {e}", "error", "pacientes")
            return ResultadoAutomatizacion(False, f"Error crítico: {e}")
            
        finally:
            self.proceso_pacientes_activo = False
    
    async def ejecutar_automatizacion_casos(self, configuracion: ConfiguracionAutomatizacion) -> ResultadoAutomatizacion:
        """Ejecuta la automatización de casos."""
        try:
            if self.proceso_casos_activo:
                return ResultadoAutomatizacion(
                    False, "Proceso de casos ya está en ejecución"
                )
            
            self.proceso_casos_activo = True
            self._log("🚀 Iniciando proceso de automatización de casos", "info", "casos")
            
            # Inicializar si no está inicializado
            if not self.procesador_casos:
                if not await self.inicializar_automatizacion_casos(configuracion):
                    raise Exception("No se pudo inicializar automatización de casos")
            
            # Ejecutar procesamiento
            resultado = await self.procesador_casos.procesar()
            self.resultados_casos = resultado
            
            if resultado.exitoso:
                self._log("✅ Automatización de casos completada exitosamente", "success", "casos")
            else:
                self._log(f"❌ Automatización de casos falló: {resultado.mensaje}", "error", "casos")
            
            return resultado
            
        except Exception as e:
            self._log(f"💥 Error crítico en automatización de casos: {e}", "error", "casos")
            return ResultadoAutomatizacion(False, f"Error crítico: {e}")
            
        finally:
            self.proceso_casos_activo = False
    
    async def ejecutar_automatizacion_dual(self, 
                                         config_pacientes: ConfiguracionAutomatizacion,
                                         config_casos: ConfiguracionAutomatizacion) -> Dict[str, ResultadoAutomatizacion]:
        """Ejecuta ambos procesos de automatización en paralelo."""
        self._log("🔄 Iniciando automatización dual (pacientes + casos)", "info", "principal")
        
        try:
            # Ejecutar ambos procesos en paralelo
            resultados = await asyncio.gather(
                self.ejecutar_automatizacion_pacientes(config_pacientes),
                self.ejecutar_automatizacion_casos(config_casos),
                return_exceptions=True
            )
            
            resultado_pacientes = resultados[0] if not isinstance(resultados[0], Exception) else \
                ResultadoAutomatizacion(False, f"Excepción en pacientes: {resultados[0]}")
            
            resultado_casos = resultados[1] if not isinstance(resultados[1], Exception) else \
                ResultadoAutomatizacion(False, f"Excepción en casos: {resultados[1]}")
            
            # Log final
            if resultado_pacientes.exitoso and resultado_casos.exitoso:
                self._log("🎉 Automatización dual completada exitosamente", "success", "principal")
            elif resultado_pacientes.exitoso or resultado_casos.exitoso:
                self._log("⚠️ Automatización dual parcialmente exitosa", "warning", "principal")
            else:
                self._log("❌ Automatización dual falló completamente", "error", "principal")
            
            return {
                "pacientes": resultado_pacientes,
                "casos": resultado_casos
            }
            
        except Exception as e:
            self._log(f"💥 Error crítico en automatización dual: {e}", "error", "principal")
            return {
                "pacientes": ResultadoAutomatizacion(False, f"Error dual: {e}"),
                "casos": ResultadoAutomatizacion(False, f"Error dual: {e}")
            }
    
    async def detener_proceso_pacientes(self):
        """Detiene el proceso de pacientes."""
        try:
            self._log("🛑 Deteniendo proceso de pacientes...", "warning", "pacientes")
            
            if self.procesador_pacientes:
                await self.procesador_pacientes.detener()
            
            if self.gestor_navegador_pacientes:
                await self.gestor_navegador_pacientes.cerrar_navegador()
            
            self.proceso_pacientes_activo = False
            self._log("✅ Proceso de pacientes detenido", "info", "pacientes")
            
        except Exception as e:
            self._log(f"❌ Error deteniendo proceso de pacientes: {e}", "error", "pacientes")
    
    async def detener_proceso_casos(self):
        """Detiene el proceso de casos."""
        try:
            self._log("🛑 Deteniendo proceso de casos...", "warning", "casos")
            
            if self.procesador_casos:
                await self.procesador_casos.detener()
            
            if self.gestor_navegador_casos:
                await self.gestor_navegador_casos.cerrar_navegador()
            
            self.proceso_casos_activo = False
            self._log("✅ Proceso de casos detenido", "info", "casos")
            
        except Exception as e:
            self._log(f"❌ Error deteniendo proceso de casos: {e}", "error", "casos")
    
    async def detener_todos_los_procesos(self):
        """Detiene todos los procesos activos."""
        self._log("🛑 Deteniendo todos los procesos...", "warning", "principal")
        
        await asyncio.gather(
            self.detener_proceso_pacientes(),
            self.detener_proceso_casos(),
            return_exceptions=True
        )
        
        self._log("✅ Todos los procesos detenidos", "info", "principal")
    
    def obtener_estado_sistema(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema."""
        return {
            "pacientes": {
                "activo": self.proceso_pacientes_activo,
                "inicializado": self.procesador_pacientes is not None,
                "navegador_activo": self.gestor_navegador_pacientes is not None and 
                                  self.gestor_navegador_pacientes.navegador_activo,
                "ultimo_resultado": self.resultados_pacientes.to_dict() if self.resultados_pacientes else None
            },
            "casos": {
                "activo": self.proceso_casos_activo,
                "inicializado": self.procesador_casos is not None,
                "navegador_activo": self.gestor_navegador_casos is not None and 
                                  self.gestor_navegador_casos.navegador_activo,
                "ultimo_resultado": self.resultados_casos.to_dict() if self.resultados_casos else None
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los procesos."""
        stats = {
            "pacientes": {},
            "casos": {},
            "recuperacion": {}
        }
        
        try:
            if self.procesador_pacientes:
                stats["pacientes"] = self.procesador_pacientes.obtener_estadisticas()
                
            if self.procesador_casos:
                stats["casos"] = self.procesador_casos.obtener_estadisticas()
            
            if self.servicio_recuperacion_pacientes:
                stats["recuperacion"]["pacientes"] = \
                    self.servicio_recuperacion_pacientes.obtener_estadisticas_recuperacion()
            
            if self.servicio_recuperacion_casos:
                stats["recuperacion"]["casos"] = \
                    self.servicio_recuperacion_casos.obtener_estadisticas_recuperacion()
                    
        except Exception as e:
            self._log(f"❌ Error obteniendo estadísticas: {e}", "error")
        
        return stats
    
    async def limpiar_recursos(self):
        """Limpia todos los recursos del controlador."""
        try:
            self._log("🧹 Limpiando recursos del controlador...", "info", "principal")
            
            # Detener procesos
            await self.detener_todos_los_procesos()
            
            # Limpiar servicios de recuperación
            if self.servicio_recuperacion_pacientes:
                self.servicio_recuperacion_pacientes.limpiar_estado()
            
            if self.servicio_recuperacion_casos:
                self.servicio_recuperacion_casos.limpiar_estado()
            
            # Limpiar gestores
            self.gestor_navegador_pacientes = None
            self.gestor_navegador_casos = None
            self.gestor_sesion_pacientes = None
            self.gestor_sesion_casos = None
            self.procesador_pacientes = None
            self.procesador_casos = None
            
            self._log("✅ Recursos limpiados", "info", "principal")
            
        except Exception as e:
            self._log(f"❌ Error limpiando recursos: {e}", "error", "principal")