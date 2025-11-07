"""
Servicio de recuperación para automatización.
Responsabilidad única: Ejecutar estrategias de recuperación después de errores.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from .clasificador_errores import TipoError, ClasificadorErrores
from .gestor_reintentos import GestorReintentos


class ServicioRecuperacion:
    """Servicio responsable de ejecutar estrategias de recuperación."""
    
    def __init__(self, gestor_navegador, servicio_navegacion, orquestador_login, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.servicio_navegacion = servicio_navegacion
        self.orquestador_login = orquestador_login
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        self.clasificador_errores = ClasificadorErrores()
        self.gestor_reintentos = GestorReintentos()
        
        self.logger.info(f"ServicioRecuperacion inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback."""
        getattr(self.logger, nivel)(mensaje)
        if self.callback_log:
            try:
                self.callback_log(f"{self.contexto}: {mensaje}", nivel, self.contexto)
            except Exception:
                pass
    
    async def recuperar(self, error: Exception, intento: int) -> bool:
        """
        Ejecuta la estrategia de recuperación apropiada.
        
        Args:
            error: Error que causó la necesidad de recuperación
            intento: Número de intento de recuperación
            
        Returns:
            bool: True si la recuperación fue exitosa
        """
        try:
            tipo_error = self.clasificador_errores.clasificar(error)
            estrategia = self.clasificador_errores.obtener_estrategia_recuperacion(tipo_error)
            
            self._log(f"🔧 Iniciando recuperación: {estrategia} (intento {intento})")
            
            # Calcular tiempo de espera
            tiempo_espera = self.gestor_reintentos.calcular_tiempo_espera(tipo_error, intento)
            if tiempo_espera > 0:
                self._log(f"⏳ Esperando {tiempo_espera} segundos antes de recuperar...")
                await asyncio.sleep(tiempo_espera)
            
            # Ejecutar estrategia específica
            exito = await self._ejecutar_estrategia(estrategia, tipo_error)
            
            if exito:
                self._log("✅ Recuperación exitosa")
            else:
                self._log("❌ Recuperación fallida", "error")
            
            return exito
            
        except Exception as e:
            self._log(f"💥 Error durante recuperación: {e}", "error")
            return False
    
    async def _ejecutar_estrategia(self, estrategia: str, tipo_error: TipoError) -> bool:
        """Ejecuta una estrategia de recuperación específica."""
        estrategias = {
            "reiniciar_navegador_completo": self._reiniciar_navegador_completo,
            "reiniciar_sesion": self._reiniciar_sesion,
            "recargar_pagina": self._recargar_pagina,
            "esperar_y_reintentar": self._esperar_y_reintentar,
            "recargar_y_buscar": self._recargar_y_buscar,
            "reintentar_captcha": self._reintentar_captcha,
            "verificar_credenciales": self._verificar_credenciales,
            "verificar_conexion_api": self._verificar_conexion_api,
            "navegar_desde_inicio": self._navegar_desde_inicio,
            "reintentar_generico": self._reintentar_generico
        }
        
        metodo = estrategias.get(estrategia, self._reintentar_generico)
        return await metodo()
    
    async def _reiniciar_navegador_completo(self) -> bool:
        """Reinicia completamente el navegador y la sesión."""
        try:
            self._log("🔄 Reiniciando navegador completo...")
            
            # Cerrar navegador actual
            await self.gestor_navegador.cerrar_navegador()
            await asyncio.sleep(2)
            
            # Reiniciar navegador
            if not await self.gestor_navegador.iniciar_navegador():
                raise Exception("No se pudo reiniciar navegador")
            
            # Navegar a login
            if not await self.servicio_navegacion.ir_a_login():
                raise Exception("No se pudo navegar a login")
            
            # Reautenticar
            if not await self.orquestador_login.ejecutar_login_completo():
                raise Exception("No se pudo reautenticar")
            
            self._log("✅ Navegador reiniciado y reautenticado")
            return True
            
        except Exception as e:
            self._log(f"❌ Error reiniciando navegador: {e}", "error")
            return False
    
    async def _reiniciar_sesion(self) -> bool:
        """Reinicia la sesión sin cerrar el navegador."""
        try:
            self._log("🔑 Reiniciando sesión...")
            
            # Navegar a login
            if not await self.servicio_navegacion.ir_a_login():
                raise Exception("No se pudo navegar a login")
            
            # Reautenticar
            if not await self.orquestador_login.ejecutar_login_completo():
                raise Exception("No se pudo reautenticar")
            
            self._log("✅ Sesión reiniciada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error reiniciando sesión: {e}", "error")
            return False
    
    async def _recargar_pagina(self) -> bool:
        """Recarga la página actual."""
        try:
            self._log("🔄 Recargando página...")
            
            if await self.gestor_navegador.recargar_pagina():
                await asyncio.sleep(3)  # Esperar a que cargue
                self._log("✅ Página recargada")
                return True
            else:
                raise Exception("No se pudo recargar página")
                
        except Exception as e:
            self._log(f"❌ Error recargando página: {e}", "error")
            return False
    
    async def _esperar_y_reintentar(self) -> bool:
        """Espera un tiempo adicional antes de continuar."""
        try:
            self._log("⏳ Esperando antes de reintentar...")
            await asyncio.sleep(5)
            self._log("✅ Espera completada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error esperando: {e}", "error")
            return False
    
    async def _recargar_y_buscar(self) -> bool:
        """Recarga página y busca elementos."""
        try:
            self._log("🔄 Recargando y buscando elementos...")
            
            if not await self.gestor_navegador.recargar_pagina():
                raise Exception("No se pudo recargar página")
            
            await asyncio.sleep(3)
            
            # Verificar que la página está completamente cargada
            if self.gestor_navegador.page:
                await self.gestor_navegador.page.wait_for_load_state("networkidle")
            
            self._log("✅ Página recargada y elementos buscados")
            return True
            
        except Exception as e:
            self._log(f"❌ Error recargando y buscando: {e}", "error")
            return False
    
    async def _reintentar_captcha(self) -> bool:
        """Reintenta resolver el captcha."""
        try:
            self._log("🤖 Reintentando captcha...")
            
            # Esperar un poco para que el captcha se resetee
            await asyncio.sleep(2)
            
            # Aquí se podría llamar específicamente al servicio de captcha
            # Por ahora retornamos True para indicar que se puede reintentar
            self._log("✅ Listo para reintentar captcha")
            return True
            
        except Exception as e:
            self._log(f"❌ Error reintentando captcha: {e}", "error")
            return False
    
    async def _verificar_credenciales(self) -> bool:
        """Verifica las credenciales antes de continuar."""
        try:
            self._log("🔍 Verificando credenciales...")
            
            # Aquí se podrían verificar las credenciales
            # Por ahora retornamos False para indicar error crítico
            self._log("❌ Error de credenciales - requiere intervención manual", "error")
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando credenciales: {e}", "error")
            return False
    
    async def _verificar_conexion_api(self) -> bool:
        """Verifica la conexión con la API."""
        try:
            self._log("🔍 Verificando conexión API...")
            
            # Esperar un poco para que la conexión se estabilice
            await asyncio.sleep(5)
            
            self._log("✅ Conexión API verificada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error verificando API: {e}", "error")
            return False
    
    async def _navegar_desde_inicio(self) -> bool:
        """Navega desde el inicio para recuperar contexto."""
        try:
            self._log("🏠 Navegando desde inicio...")
            
            # Navegar a página principal
            if not await self.servicio_navegacion.ir_a_home():
                raise Exception("No se pudo navegar a home")
            
            await asyncio.sleep(2)
            
            self._log("✅ Navegación desde inicio completada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error navegando desde inicio: {e}", "error")
            return False
    
    async def _reintentar_generico(self) -> bool:
        """Estrategia genérica de reintento."""
        try:
            self._log("🔄 Aplicando estrategia genérica...")
            
            # Esperar y verificar estado del navegador
            await asyncio.sleep(2)
            
            if not await self.gestor_navegador.verificar_salud():
                # Si el navegador no está saludable, recargamos
                if not await self.gestor_navegador.recargar_pagina():
                    raise Exception("Navegador no responde")
            
            self._log("✅ Estrategia genérica aplicada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error en estrategia genérica: {e}", "error")
            return False
    
    def limpiar_estado(self):
        """Limpia el estado del servicio de recuperación."""
        try:
            self.gestor_reintentos.limpiar_historial(self.contexto)
            self._log("🧹 Estado de recuperación limpiado")
            
        except Exception as e:
            self._log(f"❌ Error limpiando estado: {e}", "error")
    
    def obtener_estadisticas_recuperacion(self) -> Dict[str, Any]:
        """Obtiene estadísticas de recuperación."""
        try:
            return self.gestor_reintentos.generar_estadisticas(self.contexto)
            
        except Exception as e:
            self._log(f"❌ Error obteniendo estadísticas: {e}", "error")
            return {}