"""
Orquestador de login para automatización.
Responsabilidad única: Coordinar el proceso completo de autenticación.
"""
import logging
from typing import Optional, Callable
from ..nucleo.gestor_navegador import GestorNavegador
from .servicio_login import ServicioLogin
from .servicio_captcha import ServicioCaptcha
from .servicio_verificacion import ServicioVerificacion


class OrquestadorLogin:
    """Orquestador responsable de coordinar todo el proceso de login."""
    
    def __init__(self, gestor_navegador: GestorNavegador, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Servicios de login
        self.servicio_login = ServicioLogin(gestor_navegador, contexto, callback_log)
        self.servicio_captcha = ServicioCaptcha(gestor_navegador, contexto, callback_log)
        self.servicio_verificacion = ServicioVerificacion(gestor_navegador, contexto, callback_log)
        
        self.logger.info(f"OrquestadorLogin inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback."""
        getattr(self.logger, nivel)(mensaje)
        if self.callback_log:
            try:
                self.callback_log(f"{self.contexto}: {mensaje}", nivel, self.contexto)
            except Exception:
                pass
    
    async def ejecutar_login_completo(self) -> bool:
        """
        Ejecuta el proceso completo de login incluyendo captcha.
        
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            self._log("🔐 Iniciando proceso completo de autenticación...")
            
            # Paso 1: Verificar que estamos en página de login
            if not await self._verificar_pagina_login():
                raise Exception("No estamos en la página de login")
            
            # Paso 2: Verificar que los campos están disponibles
            if not await self.servicio_login.verificar_campos_requeridos():
                raise Exception("Campos de login no disponibles")
            
            # Paso 3: Limpiar campos existentes
            await self.servicio_login.limpiar_campos()
            
            # Paso 4: Ingresar credenciales
            if not await self.servicio_login.ingresar_credenciales():
                raise Exception("Error ingresando credenciales")
            
            # Paso 5: Resolver captcha si está presente
            if not await self.servicio_captcha.resolver_captcha_completo():
                raise Exception("Error resolviendo captcha")
            
            # Paso 6: Buscar y hacer clic en botón de login
            selector_boton = await self.servicio_login.buscar_boton_login()
            if not selector_boton:
                raise Exception("No se encontró botón de login")
            
            if not await self.servicio_login.hacer_click_login(selector_boton):
                raise Exception("Error haciendo clic en botón de login")
            
            # Paso 7: Verificar que el login fue exitoso
            if not await self._verificar_login_exitoso():
                raise Exception("Login no fue exitoso")
            
            self._log("🎉 Proceso de autenticación completado exitosamente")
            return True
            
        except Exception as e:
            self._log(f"💥 Error en proceso de login: {e}", "error")
            return False
    
    async def ejecutar_login_basico(self) -> bool:
        """
        Ejecuta solo el login básico sin captcha.
        
        Returns:
            bool: True si el login básico fue exitoso
        """
        try:
            self._log("🔑 Iniciando login básico...")
            
            # Verificar página
            if not await self._verificar_pagina_login():
                raise Exception("No estamos en la página de login")
            
            # Ingresar credenciales
            if not await self.servicio_login.ingresar_credenciales():
                raise Exception("Error ingresando credenciales")
            
            self._log("✅ Login básico completado")
            return True
            
        except Exception as e:
            self._log(f"❌ Error en login básico: {e}", "error")
            return False
    
    async def _verificar_pagina_login(self) -> bool:
        """
        Verifica que estamos en la página de login.
        
        Returns:
            bool: True si estamos en página de login
        """
        try:
            self._log("🔍 Verificando página de login...")
            
            return await self.servicio_verificacion.verificar_pagina_login()
            
        except Exception as e:
            self._log(f"❌ Error verificando página de login: {e}", "error")
            return False
    
    async def _verificar_login_exitoso(self) -> bool:
        """
        Verifica que el login fue exitoso.
        
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            self._log("🔍 Verificando éxito de login...")
            
            # Esperar unos segundos para que la página redireccione
            await self.gestor_navegador.page.wait_for_timeout(5000)
            
            # Verificar si estamos en dashboard/home
            if await self.servicio_verificacion.verificar_pagina_home():
                self._log("✅ Login exitoso - Estamos en dashboard")
                return True
            
            # Verificar si hay errores de login
            if await self.servicio_verificacion.verificar_error_login():
                self._log("❌ Error de login detectado", "error")
                return False
            
            # Si no hay errores claros pero tampoco estamos en home,
            # verificar otros indicadores de éxito
            if await self._verificar_indicadores_login_exitoso():
                self._log("✅ Login exitoso - Indicadores de éxito detectados")
                return True
            
            self._log("❓ Estado de login ambiguo", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando éxito de login: {e}", "error")
            return False
    
    async def _verificar_indicadores_login_exitoso(self) -> bool:
        """
        Verifica indicadores adicionales de login exitoso.
        
        Returns:
            bool: True si se detectan indicadores de éxito
        """
        try:
            # Indicadores de que el login fue exitoso
            indicadores_exito = [
                "//a[contains(text(),'Cerrar sesión')]",
                "//button[contains(text(),'Logout')]",
                "//nav[contains(@class,'navbar')]",
                "//div[contains(@class,'dashboard')]",
                ".user-menu",
                ".header-user",
                "[data-testid='user-menu']"
            ]
            
            for selector in indicadores_exito:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 3000):
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando indicadores de éxito: {e}")
            return False
    
    async def reintentar_login(self) -> bool:
        """
        Reintenta el proceso de login desde el principio.
        
        Returns:
            bool: True si el reintento fue exitoso
        """
        try:
            self._log("🔄 Reintentando proceso de login...")
            
            # Recargar página para empezar limpio
            await self.gestor_navegador.recargar_pagina()
            
            # Esperar a que cargue
            await self.gestor_navegador.page.wait_for_timeout(3000)
            
            # Reintentar login completo
            return await self.ejecutar_login_completo()
            
        except Exception as e:
            self._log(f"❌ Error en reintento de login: {e}", "error")
            return False
    
    async def obtener_estado_login(self) -> dict:
        """
        Obtiene el estado actual del proceso de login.
        
        Returns:
            dict: Estado detallado del login
        """
        try:
            estado = {
                "en_pagina_login": await self.servicio_verificacion.verificar_pagina_login(),
                "en_dashboard": await self.servicio_verificacion.verificar_pagina_home(),
                "hay_error_login": await self.servicio_verificacion.verificar_error_login(),
                "captcha_presente": await self.servicio_captcha.detectar_captcha(),
                "campos_disponibles": await self.servicio_login.verificar_campos_requeridos(),
                "url_actual": await self.gestor_navegador.obtener_url_actual(),
                "navegador_activo": self.gestor_navegador.page is not None
            }
            
            return estado
            
        except Exception as e:
            self._log(f"❌ Error obteniendo estado de login: {e}", "error")
            return {}
    
    async def cerrar_sesion(self) -> bool:
        """
        Cierra la sesión actual.
        
        Returns:
            bool: True si se cerró correctamente
        """
        try:
            self._log("👋 Cerrando sesión actual...")
            
            page = self.gestor_navegador.page
            if not page:
                return True  # Ya no hay sesión
            
            # Buscar botón de cerrar sesión
            selectores_logout = [
                "//a[contains(text(),'Cerrar sesión')]",
                "//button[contains(text(),'Cerrar sesión')]",
                "//a[contains(text(),'Logout')]",
                "//button[contains(text(),'Logout')]",
                ".logout-btn",
                "#logout",
                "[data-testid='logout']"
            ]
            
            for selector in selectores_logout:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_timeout(2000)
                        self._log("✅ Sesión cerrada exitosamente")
                        return True
                except Exception:
                    continue
            
            self._log("⚠️ No se encontró botón de cerrar sesión", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error cerrando sesión: {e}", "error")
            return False