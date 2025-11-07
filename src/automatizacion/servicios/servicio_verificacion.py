"""
Servicio de verificación para automatización.
Responsabilidad única: Verificar estados de páginas y elementos.
"""
import logging
from typing import Optional, Callable
from ..nucleo.gestor_navegador import GestorNavegador


class ServicioVerificacion:
    """Servicio responsable de verificar estados de páginas y elementos."""
    
    def __init__(self, gestor_navegador: GestorNavegador, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        self.logger.info(f"ServicioVerificacion inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback, sin emojis problemáticos."""
        # Reemplazar emojis problemáticos
        mensaje_limpio = (mensaje
                         .replace("✅", "[OK]")
                         .replace("❌", "[ERROR]")
                         .replace("⚠️", "[WARN]"))
        
        # Agregar información del método actual
        import inspect
        frame = inspect.currentframe().f_back
        metodo_actual = frame.f_code.co_name
        clase_actual = self.__class__.__name__
        mensaje_con_contexto = f"[{clase_actual}.{metodo_actual}] {mensaje_limpio}"
        
        getattr(self.logger, nivel)(mensaje_con_contexto)
        if self.callback_log:
            try:
                self.callback_log(f"{self.contexto}: {mensaje_con_contexto}", nivel, self.contexto)
            except Exception:
                pass
    
    async def verificar_pagina_login(self) -> bool:
        """
        Verifica que estamos en la página de login.
        
        Returns:
            bool: True si estamos en página de login
        """
        try:
            # Selectores que indican página de login
            selectores_login = [
                "//input[contains(@id,'email')]",
                "//input[contains(@placeholder,'correo')]",
                "//input[contains(@type,'email')]",
                "//input[contains(@placeholder,'usuario')]",
                "//form[contains(@class,'login')]",
                ".login-form",
                "#login-form"
            ]
            
            for selector in selectores_login:
                if await self.gestor_navegador.esperar_elemento(selector, 2000):
                    self._log("✅ Página de login confirmada")
                    return True
            
            # Verificar por URL también
            url_actual = await self.gestor_navegador.obtener_url_actual()
            if url_actual and 'login' in url_actual.lower():
                self._log("✅ Página de login confirmada por URL")
                return True
            
            self._log("❌ No se detectó página de login")
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando página de login: {e}", "error")
            return False
    
    async def verificar_pagina_home(self) -> bool:
        """
        Verifica que estamos en la página principal/dashboard.
        
        Returns:
            bool: True si estamos en página principal
        """
        try:
            # Selectores que indican dashboard/home
            selectores_home = [
                "//nav[contains(@class,'navbar')]",
                "//div[contains(@class,'dashboard')]",
                "//a[contains(text(),'Cerrar sesión')]",
                "//button[contains(text(),'Logout')]",
                ".main-navigation",
                ".dashboard",
                ".user-menu",
                "#main-content"
            ]
            
            for selector in selectores_home:
                if await self.gestor_navegador.esperar_elemento(selector, 3000):
                    self._log("✅ Página principal confirmada")
                    return True
            
            # Verificar por URL
            url_actual = await self.gestor_navegador.obtener_url_actual()
            if url_actual:
                indicadores_url = ['dashboard', 'home', 'main', 'portal']
                for indicador in indicadores_url:
                    if indicador in url_actual.lower():
                        self._log("✅ Página principal confirmada por URL")
                        return True
            
            self._log("❌ No se detectó página principal")
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando página principal: {e}", "error")
            return False
    
    async def verificar_error_login(self) -> bool:
        """
        Verifica si hay errores de login en la página.
        
        Returns:
            bool: True si hay errores de login
        """
        try:
            # Selectores que indican errores de login
            selectores_error = [
                "//div[contains(@class,'error')]",
                "//div[contains(@class,'alert-danger')]",
                "//span[contains(text(),'incorrecto')]",
                "//span[contains(text(),'inválido')]",
                "//div[contains(text(),'Error')]",
                ".error-message",
                ".login-error",
                ".alert-error"
            ]
            
            for selector in selectores_error:
                if await self.gestor_navegador.esperar_elemento(selector, 2000):
                    self._log("⚠️ Error de login detectado", "warning")
                    return True
            
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando errores de login: {e}", "error")
            return False
    
    async def verificar_elemento_presente(self, selector: str, timeout: int = 5000) -> bool:
        """
        Verifica que un elemento específico esté presente.
        
        Args:
            selector: Selector del elemento
            timeout: Timeout en milisegundos
            
        Returns:
            bool: True si el elemento está presente
        """
        try:
            return await self.gestor_navegador.esperar_elemento(selector, timeout)
            
        except Exception as e:
            self._log(f"❌ Error verificando elemento {selector}: {e}", "error")
            return False
    
    async def verificar_elemento_visible(self, selector: str) -> bool:
        """
        Verifica que un elemento sea visible.
        
        Args:
            selector: Selector del elemento
            
        Returns:
            bool: True si el elemento es visible
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Verificar que existe y es visible
            return await page.is_visible(selector)
            
        except Exception as e:
            self._log(f"❌ Error verificando visibilidad de {selector}: {e}", "error")
            return False
    
    async def verificar_elemento_clickeable(self, selector: str) -> bool:
        """
        Verifica que un elemento sea clickeable.
        
        Args:
            selector: Selector del elemento
            
        Returns:
            bool: True si el elemento es clickeable
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Verificar que existe, es visible y está habilitado
            if not await page.is_visible(selector):
                return False
            
            if not await page.is_enabled(selector):
                return False
            
            return True
            
        except Exception as e:
            self._log(f"❌ Error verificando clickeabilidad de {selector}: {e}", "error")
            return False
    
    async def verificar_pagina_cargada(self) -> bool:
        """
        Verifica que la página esté completamente cargada.
        
        Returns:
            bool: True si la página está cargada
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Verificar estado de carga
            await page.wait_for_load_state("networkidle", timeout=10000)
            return True
            
        except Exception as e:
            self._log(f"❌ Error verificando carga de página: {e}", "error")
            return False
    
    async def verificar_url_contiene(self, texto: str) -> bool:
        """
        Verifica que la URL actual contenga un texto específico.
        
        Args:
            texto: Texto a buscar en la URL
            
        Returns:
            bool: True si la URL contiene el texto
        """
        try:
            url_actual = await self.gestor_navegador.obtener_url_actual()
            if url_actual:
                return texto.lower() in url_actual.lower()
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando URL: {e}", "error")
            return False
    
    async def verificar_titulo_contiene(self, texto: str) -> bool:
        """
        Verifica que el título de la página contenga un texto específico.
        
        Args:
            texto: Texto a buscar en el título
            
        Returns:
            bool: True si el título contiene el texto
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            titulo = await page.title()
            return texto.lower() in titulo.lower()
            
        except Exception as e:
            self._log(f"❌ Error verificando título: {e}", "error")
            return False
    
    async def verificar_texto_presente(self, texto: str) -> bool:
        """
        Verifica que un texto específico esté presente en la página.
        
        Args:
            texto: Texto a buscar
            
        Returns:
            bool: True si el texto está presente
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Buscar texto en la página
            contenido = await page.content()
            return texto.lower() in contenido.lower()
            
        except Exception as e:
            self._log(f"❌ Error verificando texto '{texto}': {e}", "error")
            return False
    
    async def obtener_estado_completo(self) -> dict:
        """
        Obtiene un estado completo de verificación de la página actual.
        
        Returns:
            dict: Estado completo de la página
        """
        try:
            estado = {
                "url_actual": await self.gestor_navegador.obtener_url_actual(),
                "pagina_login": await self.verificar_pagina_login(),
                "pagina_home": await self.verificar_pagina_home(),
                "error_login": await self.verificar_error_login(),
                "pagina_cargada": await self.verificar_pagina_cargada(),
                "navegador_activo": self.gestor_navegador.page is not None,
                "timestamp": self._obtener_timestamp()
            }
            
            # Obtener título si es posible
            try:
                if self.gestor_navegador.page:
                    estado["titulo"] = await self.gestor_navegador.page.title()
            except Exception:
                estado["titulo"] = "No disponible"
            
            return estado
            
        except Exception as e:
            self._log(f"❌ Error obteniendo estado completo: {e}", "error")
            return {}
    
    def _obtener_timestamp(self) -> str:
        """Obtiene timestamp actual."""
        from datetime import datetime
        return datetime.now().isoformat()