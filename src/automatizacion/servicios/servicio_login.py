"""
Servicio de login para automatización.
Responsabilidad única: Manejar el ingreso de credenciales de usuario.
"""
import logging
from typing import Optional, Callable
from ..nucleo.gestor_navegador import GestorNavegador
from src.core.config import config


class ServicioLogin:
    """Servicio responsable del ingreso de credenciales."""
    
    def __init__(self, gestor_navegador: GestorNavegador, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Credenciales del sistema
        self.email = config.get('automation.login_email', '')
        self.password = config.get('automation.login_password', '')
        
        self.logger.info(f"ServicioLogin inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log tanto al logger como al callback."""
        getattr(self.logger, nivel)(mensaje)
        if self.callback_log:
            try:
                self.callback_log(f"{self.contexto}: {mensaje}", nivel, self.contexto)
            except Exception:
                pass
    
    async def ingresar_credenciales(self) -> bool:
        """
        Ingresa las credenciales de usuario en el formulario de login.
        
        Returns:
            bool: True si las credenciales se ingresaron correctamente
        """
        try:
            # Validar que tenemos credenciales
            if not self.email or not self.password:
                raise Exception("Credenciales no configuradas en config")
            
            page = self.gestor_navegador.page
            if not page:
                raise Exception("No hay página activa")
            
            self._log("📝 Ingresando credenciales de usuario...")
            
            # Ingresar email
            if not await self._ingresar_email():
                raise Exception("Error ingresando email")
            
            # Ingresar contraseña
            if not await self._ingresar_password():
                raise Exception("Error ingresando contraseña")
            
            self._log("✅ Credenciales ingresadas correctamente")
            return True
            
        except Exception as e:
            self._log(f"❌ Error ingresando credenciales: {e}", "error")
            return False
    
    async def _ingresar_email(self) -> bool:
        """
        Ingresa el email en el campo correspondiente.
        
        Returns:
            bool: True si se ingresó correctamente
        """
        try:
            page = self.gestor_navegador.page
            
            # Selectores comunes para campo de email
            selectores_email = [
                "//input[@placeholder='Ingresa tu correo electrónico'][contains(@id,'email')]",
                "//input[contains(@id,'email')]",
                "//input[contains(@name,'email')]",
                "//input[contains(@type,'email')]",
                "#email",
                "[name='email']"
            ]
            
            for selector in selectores_email:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        # Limpiar campo y escribir email
                        await page.fill(selector, "")
                        await page.fill(selector, self.email)
                        
                        # Verificar que se escribió
                        valor = await page.input_value(selector)
                        if valor == self.email:
                            self._log(f"📧 Email ingresado: {self.email}")
                            return True
                except Exception:
                    continue
            
            raise Exception("No se encontró el campo de email")
            
        except Exception as e:
            self._log(f"❌ Error ingresando email: {e}", "error")
            return False
    
    async def _ingresar_password(self) -> bool:
        """
        Ingresa la contraseña en el campo correspondiente.
        
        Returns:
            bool: True si se ingresó correctamente
        """
        try:
            page = self.gestor_navegador.page
            
            # Selectores comunes para campo de contraseña
            selectores_password = [
                "//input[@placeholder='Ingresa tu contraseña'][contains(@id,'password')]",
                "//input[contains(@id,'password')]",
                "//input[contains(@name,'password')]",
                "//input[contains(@type,'password')]",
                "#password",
                "[name='password']"
            ]
            
            for selector in selectores_password:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        # Limpiar campo y escribir contraseña
                        await page.fill(selector, "")
                        await page.fill(selector, self.password)
                        
                        # Verificar que se escribió (sin mostrar la contraseña en logs)
                        valor = await page.input_value(selector)
                        if len(valor) == len(self.password):
                            self._log("🔒 Contraseña ingresada correctamente")
                            return True
                except Exception:
                    continue
            
            raise Exception("No se encontró el campo de contraseña")
            
        except Exception as e:
            self._log(f"❌ Error ingresando contraseña: {e}", "error")
            return False
    
    async def buscar_boton_login(self) -> Optional[str]:
        """
        Busca el botón de login en la página.
        
        Returns:
            str: Selector del botón encontrado o None si no se encuentra
        """
        try:
            # Selectores comunes para botón de login
            selectores_boton = [
                "//button[contains(text(),'Iniciar sesión')]",
                "//button[contains(text(),'Entrar')]", 
                "//button[contains(text(),'Login')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "#login-button",
                ".login-button",
                "[data-testid='login-button']"
            ]
            
            for selector in selectores_boton:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 1000):
                        self._log(f"🔘 Botón de login encontrado: {selector}")
                        return selector
                except Exception:
                    continue
            
            self._log("❌ No se encontró botón de login", "warning")
            return None
            
        except Exception as e:
            self._log(f"❌ Error buscando botón de login: {e}", "error")
            return None
    
    async def hacer_click_login(self, selector: str) -> bool:
        """
        Hace clic en el botón de login.
        
        Args:
            selector: Selector del botón de login
            
        Returns:
            bool: True si el clic fue exitoso
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                raise Exception("No hay página activa")
            
            self._log("🖱️ Haciendo clic en botón de login...")
            
            # Hacer clic en el botón
            await page.click(selector)
            
            # Esperar un poco para que la página procese
            await page.wait_for_timeout(1000)
            
            self._log("✅ Clic en botón de login realizado")
            return True
            
        except Exception as e:
            self._log(f"❌ Error haciendo clic en botón de login: {e}", "error")
            return False
    
    async def verificar_campos_requeridos(self) -> bool:
        """
        Verifica que todos los campos requeridos estén presentes.
        
        Returns:
            bool: True si todos los campos están presentes
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Verificar campo email
            campos_email = [
                "//input[contains(@type,'email')]",
                "//input[contains(@id,'email')]",
                "//input[contains(@name,'email')]"
            ]
            
            email_encontrado = False
            for selector in campos_email:
                if await self.gestor_navegador.esperar_elemento(selector, 1000):
                    email_encontrado = True
                    break
            
            # Verificar campo password
            campos_password = [
                "//input[contains(@type,'password')]",
                "//input[contains(@id,'password')]",
                "//input[contains(@name,'password')]"
            ]
            
            password_encontrado = False
            for selector in campos_password:
                if await self.gestor_navegador.esperar_elemento(selector, 1000):
                    password_encontrado = True
                    break
            
            if email_encontrado and password_encontrado:
                self._log("✅ Todos los campos de login están presentes")
                return True
            else:
                self._log("❌ Faltan campos de login", "warning")
                return False
                
        except Exception as e:
            self._log(f"❌ Error verificando campos: {e}", "error")
            return False
    
    async def limpiar_campos(self) -> bool:
        """
        Limpia todos los campos de login antes de ingresar datos.
        
        Returns:
            bool: True si se limpiaron correctamente
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            self._log("🧹 Limpiando campos de login...")
            
            # Limpiar email
            selectores_email = ["#email", "[name='email']", "//input[contains(@type,'email')]"]
            for selector in selectores_email:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 1000):
                        await page.fill(selector, "")
                        break
                except Exception:
                    continue
            
            # Limpiar password
            selectores_password = ["#password", "[name='password']", "//input[contains(@type,'password')]"]
            for selector in selectores_password:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 1000):
                        await page.fill(selector, "")
                        break
                except Exception:
                    continue
            
            self._log("✅ Campos limpiados correctamente")
            return True
            
        except Exception as e:
            self._log(f"❌ Error limpiando campos: {e}", "error")
            return False