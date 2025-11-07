"""
Gestor de navegadores para automatización con Playwright.
Responsabilidad única: Crear, configurar y gestionar instancias de navegador.
"""
import logging
from typing import Optional, Dict, Any
import asyncio
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from src.core.config import config
from ..modelos.estado_automatizacion import EstadoProceso


class GestorNavegador:
    """Gestor responsable de crear y mantener instancias de navegador."""
    
    def __init__(self, contexto: str):
        self.contexto = contexto
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Estado del navegador
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Configuración específica por contexto
        self.puerto_depuración = self._asignar_puerto()
        self.directorio_datos = f"./datos_navegador_{contexto.lower()}"
        
        self.logger.info(f"GestorNavegador inicializado para contexto: {contexto}")
    
    def _asignar_puerto(self) -> int:
        """Asigna un puerto único para depuración según el contexto."""
        puertos = {
            "PACIENTES": 9222,
            "CASOS": 9223
        }
        return puertos.get(self.contexto, 9224)
    
    async def iniciar_navegador(self) -> bool:
        """
        Inicia una nueva instancia del navegador.
        
        Returns:
            bool: True si el navegador se inició correctamente
        """
        try:
            self.logger.info(f"Iniciando navegador para {self.contexto}...")
            
            # Inicializar Playwright
            self.playwright = await async_playwright().start()
            
            # Configurar opciones del navegador
            opciones_navegador = {
                "headless": config.get('automation.headless', False),
                "args": [
                    f"--remote-debugging-port={self.puerto_depuración}",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            }
            
            # Crear instancia del navegador
            self.browser = await self.playwright.chromium.launch(**opciones_navegador)
            
            # Crear contexto con configuración específica
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1366, "height": 768},
                ignore_https_errors=True
            )
            
            # Crear página inicial
            self.page = await self.context.new_page()
            
            self.logger.info(f"Navegador iniciado exitosamente en puerto {self.puerto_depuración}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando navegador: {e}")
            await self._limpiar_recursos()
            return False
    
    async def verificar_salud(self) -> bool:
        """
        Verifica que el navegador esté en estado saludable.
        
        Returns:
            bool: True si el navegador está funcionando correctamente
        """
        try:
            if not self.browser or not self.page:
                return False
            
            # Intentar una operación simple para verificar conectividad
            await self.page.evaluate("() => document.title")
            return True
            
        except Exception as e:
            self.logger.warning(f"Navegador no está saludable: {e}")
            return False
    
    async def navegar_a(self, url: str, timeout: int = 30000) -> bool:
        """
        Navega a una URL específica.
        
        Args:
            url: URL destino
            timeout: Timeout en milisegundos
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            if not self.page:
                raise Exception("No hay página activa")
            
            self.logger.info(f"Navegando a: {url}")
            await self.page.goto(url, timeout=timeout, wait_until="networkidle")
            
            self.logger.info(f"Navegación exitosa a: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error navegando a {url}: {e}")
            return False
    
    async def recargar_pagina(self) -> bool:
        """
        Recarga la página actual.
        
        Returns:
            bool: True si la recarga fue exitosa
        """
        try:
            if not self.page:
                raise Exception("No hay página activa")
            
            self.logger.info("Recargando página...")
            await self.page.reload(wait_until="networkidle")
            
            self.logger.info("Página recargada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recargando página: {e}")
            return False
    
    async def obtener_url_actual(self) -> Optional[str]:
        """
        Obtiene la URL actual de la página.
        
        Returns:
            str: URL actual o None si hay error
        """
        try:
            if not self.page:
                return None
            return self.page.url
        except Exception:
            return None
    
    async def esperar_elemento(self, selector: str, timeout: int = 10000) -> bool:
        """
        Espera a que aparezca un elemento.
        
        Args:
            selector: Selector CSS o XPath del elemento
            timeout: Timeout en milisegundos
            
        Returns:
            bool: True si el elemento apareció
        """
        try:
            if not self.page:
                return False
            
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
            
        except Exception as e:
            self.logger.debug(f"Elemento {selector} no encontrado: {e}")
            return False
    
    async def cerrar_navegador(self):
        """Cierra el navegador y limpia recursos."""
        try:
            self.logger.info(f"Cerrando navegador para {self.contexto}...")
            await self._limpiar_recursos()
            self.logger.info("Navegador cerrado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error cerrando navegador: {e}")
    
    async def _limpiar_recursos(self):
        """Limpia todos los recursos del navegador."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as e:
            self.logger.warning(f"Error limpiando recursos: {e}")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del navegador.
        
        Returns:
            dict: Estado del navegador
        """
        return {
            "contexto": self.contexto,
            "activo": self.browser is not None and self.page is not None,
            "puerto": self.puerto_depuración,
            "url_actual": asyncio.create_task(self.obtener_url_actual()) if self.page else None,
            "directorio_datos": self.directorio_datos
        }