"""
Servicio de navegación para automatización.
Responsabilidad única: Manejar la navegación entre páginas web.
"""
import logging
from typing import Optional, Callable
from ..nucleo.gestor_navegador import GestorNavegador
from ..modelos.configuracion_automatizacion import ConfiguracionAutomatizacion


class ServicioNavegacion:
    """Servicio responsable de la navegación web."""
    
    def __init__(self, gestor_navegador: GestorNavegador, configuracion: ConfiguracionAutomatizacion, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.configuracion = configuracion
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # URLs centralizadas desde la configuración
        self.url_login = self.configuracion.url_login
        self.url_home = self.configuracion.url_home
        
        self.logger.info(f"ServicioNavegacion inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback, sin emojis problemáticos."""
        # Reemplazar emojis problemáticos
        mensaje_limpio = (mensaje
                         .replace("🔄", "[RESTART]")
                         .replace("✅", "[OK]")
                         .replace("❌", "[ERROR]")
                         .replace("⚠️", "[WARN]")
                         .replace("🔍", "[SEARCH]")
                         .replace("🔗", "[LINK]"))
        
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
    
    async def ir_a_login(self) -> bool:
        """
        Navega a la página de login.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self._log(f"🔗 Navegando a página de login: {self.url_login}")
            
            exito = await self.gestor_navegador.navegar_a(self.url_login)
            if not exito:
                raise Exception("Fallo en navegación")
            
            # Verificar que estamos en la página correcta
            if await self._verificar_pagina_login():
                self._log("✅ Navegación a login exitosa")
                return True
            else:
                self._log("❌ No se detectó la página de login", "warning")
                return False
                
        except Exception as e:
            self._log(f"❌ Error navegando a login: {e}", "error")
            return False
    
    async def ir_a_home(self) -> bool:
        """
        Navega a la página principal después del login.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self._log(f"🏠 Navegando a página principal: {self.url_home}")
            
            exito = await self.gestor_navegador.navegar_a(self.url_home)
            if not exito:
                raise Exception("Fallo en navegación")
            
            if await self._verificar_pagina_home():
                self._log("✅ Navegación a home exitosa")
                return True
            else:
                self._log("❌ No se detectó la página principal", "warning")
                return False
                
        except Exception as e:
            self._log(f"❌ Error navegando a home: {e}", "error")
            return False
    
    async def ir_a_seccion_pacientes(self) -> bool:
        """
        Navega a la sección de pacientes.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self._log("👥 Navegando a sección de pacientes...")
            
            # Buscar y hacer clic en el enlace/botón de pacientes
            page = self.gestor_navegador.page
            if not page:
                raise Exception("No hay página activa")
            
            # Intentar varios selectores comunes para sección de pacientes
            selectores_pacientes = [
                "//a[contains(text(), 'Pacientes')]",
                "//button[contains(text(), 'Pacientes')]", 
                "//nav//a[contains(@href, 'pacientes')]",
                "[data-menu='pacientes']"
            ]
            
            for selector in selectores_pacientes:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_load_state("networkidle")
                        self._log("✅ Navegación a sección de pacientes exitosa")
                        return True
                except Exception:
                    continue
            
            self._log("❌ No se encontró la sección de pacientes", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error navegando a sección de pacientes: {e}", "error")
            return False
    
    async def ir_a_seccion_casos(self) -> bool:
        """
        Navega a la sección de casos.
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self._log("📋 Navegando a sección de casos...")
            
            page = self.gestor_navegador.page
            if not page:
                raise Exception("No hay página activa")
            
            # Intentar varios selectores comunes para sección de casos
            selectores_casos = [
                "//a[contains(text(), 'Casos')]",
                "//button[contains(text(), 'Casos')]",
                "//nav//a[contains(@href, 'casos')]",
                "[data-menu='casos']"
            ]
            
            for selector in selectores_casos:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_load_state("networkidle")
                        self._log("✅ Navegación a sección de casos exitosa")
                        return True
                except Exception:
                    continue
            
            self._log("❌ No se encontró la sección de casos", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error navegando a sección de casos: {e}", "error")
            return False
    
    async def recargar_pagina_actual(self) -> bool:
        """
        Recarga la página actual.
        
        Returns:
            bool: True si la recarga fue exitosa
        """
        try:
            self._log("🔄 Recargando página actual...")
            
            exito = await self.gestor_navegador.recargar_pagina()
            if exito:
                self._log("✅ Página recargada exitosamente")
            else:
                self._log("❌ Error recargando página", "error")
            
            return exito
            
        except Exception as e:
            self._log(f"❌ Error en recarga de página: {e}", "error")
            return False
    
    async def _verificar_pagina_login(self) -> bool:
        """
        Verifica que estamos en la página de login.
        
        Returns:
            bool: True si estamos en la página de login
        """
        try:
            # Selectores que indican que estamos en login
            selectores_login = [
                "//input[contains(@id,'email')]",
                "//input[contains(@placeholder,'correo')]",
                "//input[contains(@type,'email')]",
                "//form[contains(@class,'login')]"
            ]
            
            for selector in selectores_login:
                if await self.gestor_navegador.esperar_elemento(selector, 3000):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando página de login: {e}")
            return False
    
    async def _verificar_pagina_home(self) -> bool:
        """
        Verifica que estamos en la página principal.
        
        Returns:
            bool: True si estamos en la página principal
        """
        try:
            # Selectores que indican que estamos en home/dashboard
            selectores_home = [
                "//nav[contains(@class,'navbar')]",
                "//div[contains(@class,'dashboard')]",
                "//a[contains(text(),'Cerrar sesión')]",
                "//button[contains(text(),'Logout')]"
            ]
            
            for selector in selectores_home:
                if await self.gestor_navegador.esperar_elemento(selector, 5000):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando página home: {e}")
            return False
    
    async def obtener_url_actual(self) -> Optional[str]:
        """
        Obtiene la URL actual.
        
        Returns:
            str: URL actual o None si hay error
        """
        return await self.gestor_navegador.obtener_url_actual()
    
    async def esperar_carga_completa(self, timeout: int = 10000) -> bool:
        """
        Espera a que la página termine de cargar completamente.
        
        Args:
            timeout: Tiempo máximo de espera en milisegundos
            
        Returns:
            bool: True si la página cargó completamente
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return True
            
        except Exception as e:
            self._log(f"Timeout esperando carga completa: {e}", "warning")
            return False