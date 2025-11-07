"""
Servicio de captcha para automatización.
Responsabilidad única: Resolver captchas usando API de 2Captcha.
"""
import logging
from typing import Optional, Callable
from twocaptcha import TwoCaptcha
from ..nucleo.gestor_navegador import GestorNavegador
from src.core.config import config


class ServicioCaptcha:
    """Servicio responsable de la resolución de captchas."""
    
    def __init__(self, gestor_navegador: GestorNavegador, contexto: str, callback_log: Optional[Callable] = None):
        self.gestor_navegador = gestor_navegador
        self.contexto = contexto
        self.callback_log = callback_log
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Obtener configuración
        from ..modelos.configuracion_automatizacion import ConfiguracionAutomatizacion
        self.configuracion = ConfiguracionAutomatizacion()
        
        # Configuración de 2Captcha desde ConfiguracionAutomatizacion
        self.api_key = self.configuracion.captcha_api_key
        self.site_key = self.configuracion.captcha_site_key
        
        # Inicializar cliente 2Captcha
        self.solver = TwoCaptcha(self.api_key) if self.api_key else None
        
        self.logger.info(f"ServicioCaptcha inicializado para: {contexto}")
    
    def _log(self, mensaje: str, nivel: str = "info"):
        """Envía log limpiando TODOS los emojis."""
        # Lista COMPLETA de emojis a reemplazar
        mensaje_limpio = (mensaje
            .replace("🔍", "[SEARCH]")
            .replace("🧩", "[CAPTCHA]")
            .replace("⏳", "[WAIT]")
            .replace("✅", "[OK]")
            .replace("❌", "[ERROR]")
            .replace("⚠️", "[WARN]")
            .replace("🎯", "[TARGET]")
            .replace("🔄", "[RETRY]")
            .replace("💥", "[FAIL]")
            .replace("🎉", "[SUCCESS]")
            .replace("🤖", "[BOT]")
            .replace("📤", "[SEND]")
            .replace("💰", "[MONEY]")
            .replace("ℹ️", "[INFO]")
            .replace("🔘", "[BUTTON]")    
            .replace("🖱️", "[CLICK]")
            .replace("📋", "[FORM]")
            .replace("🔑", "[KEY]")
        )

        # Resto del código igual...
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
    
    async def detectar_captcha(self) -> bool:
        """
        Detecta si hay un captcha presente en la página.
        
        Returns:
            bool: True si se detecta un captcha
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Selectores comunes para reCAPTCHA
            selectores_captcha = [
                ".g-recaptcha",
                "#g-recaptcha", 
                "iframe[src*='recaptcha']",
                ".recaptcha-checkbox",
                "[data-sitekey]"
            ]
            
            for selector in selectores_captcha:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        self._log(f"🤖 Captcha detectado: {selector}")
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self._log(f"❌ Error detectando captcha: {e}", "error")
            return False
    
    async def resolver_captcha(self) -> Optional[str]:
        """
        Resuelve el captcha usando la API de 2Captcha exactamente como el método que funciona.
        
        Returns:
            str: Token de respuesta del captcha o None si falla
        """
        try:
            if not self.solver:
                raise Exception("Cliente 2Captcha no inicializado (API key faltante)")
            
            self._log("🔍 Iniciando resolución de captcha...")
            
            # Obtener URL actual para el captcha
            url_actual = await self.gestor_navegador.obtener_url_actual()
            if not url_actual:
                raise Exception("No se pudo obtener URL actual")
            
            self._log("⏳ Enviado para resolver...")
            
            # Usar el método oficial de la API: recaptcha()
            resultado = self.solver.recaptcha(
                sitekey=self.site_key,
                url=url_actual
            )
            
            # Extraer el token como en la API oficial
            if resultado and 'code' in resultado:
                token = str(resultado['code'])  # Extraer el token del resultado
                self._log(f"✅ Captcha resuelto exitosamente - Token: {token}")
                print(f"Successfully solved the captcha. Captcha token: {token}")
                return token
            else:
                raise Exception("Respuesta inválida de 2Captcha")
                
        except Exception as e:
            self._log(f"❌ Error resolviendo captcha: {e}", "error")
            return None
    
    async def enviar_respuesta_captcha(self, token: str) -> bool:
        """
        Envía la respuesta del captcha al formulario usando el script que funciona.
        Método idéntico al de tu clase LoginService que ya funciona.

        Args:
            token: Token de respuesta del captcha

        Returns:
            bool: True si se envió correctamente
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                raise Exception("No hay página activa")

            self._log("📤 Enviando respuesta de captcha al formulario...")

            # Log del token para debug
            print(f"Token a enviar: {token}")
            self._log(f"Token recibido: {token}")

            # Script usando template string de JavaScript - NO usar json.dumps
            # Playwright usa página.evaluate() que ya maneja correctamente los argumentos
            script_captcha = """
            (function(captchaToken) {
                function retrieveCallback(obj, visited = new Set()) {
                    if (typeof obj === 'function') return obj;
                    for (const key in obj) {
                        if (!visited.has(obj[key])) {
                            visited.add(obj[key]);
                            if (typeof obj[key] === 'object' || typeof obj[key] === 'function') {
                                const value = retrieveCallback(obj[key], visited);
                                if (value) {
                                    return value;
                                }
                            }
                            visited.delete(obj[key]);
                        }
                    }
                }
                const callback = retrieveCallback(window.___grecaptcha_cfg.clients[0]);
                if (typeof callback === 'function') {
                    callback(captchaToken);
                    return true;
                } else {
                    throw new Error('Callback function not found.');
                }
            })
            """

            # Debug: mostrar el script final que se va a ejecutar
            self._log(f"Script JavaScript preparado para ejecutar")
            self._log(f"--- INICIO SCRIPT ---")
            self._log(script_captcha)
            self._log(f"--- FIN SCRIPT ---")

            # Ejecutar el script - Playwright maneja el argumento automáticamente
            try:
                self._log("Llamando a evaluate con el código del captcha...")

                # MÉTODO 1: Pasar el token como argumento (RECOMENDADO)
                resultado = await page.evaluate(script_captcha, token)
                self._log(f"✅ Captcha resuelto con éxito. Resultado: {resultado}")

            except Exception as e1:
                self._log(f"⚠️ Error con script usando argumento: {e1}", "error")

                # MÉTODO 2: Fallback - Inyectar directamente con formato string
                self._log("Intentando con método alternativo de inyección directa...")
                try:
                    # Escapar comillas en el token
                    token_escapado = token.replace('\\', '\\\\').replace("'", "\\'")

                    script_directo = f"""
                    (function() {{
                        function retrieveCallback(obj, visited = new Set()) {{
                            if (typeof obj === 'function') return obj;
                            for (const key in obj) {{
                                if (!visited.has(obj[key])) {{
                                    visited.add(obj[key]);
                                    if (typeof obj[key] === 'object' || typeof obj[key] === 'function') {{
                                        const value = retrieveCallback(obj[key], visited);
                                        if (value) {{
                                            return value;
                                        }}
                                    }}
                                    visited.delete(obj[key]);
                                }}
                            }}
                        }}
                        const callback = retrieveCallback(window.___grecaptcha_cfg.clients[0]);
                        if (typeof callback === 'function') {{
                            callback('{token_escapado}');
                            return true;
                        }} else {{
                            throw new Error('Callback function not found.');
                        }}
                    }})();
                    """

                    resultado = await page.evaluate(script_directo)
                    self._log(f"✅ Captcha resuelto con método alternativo. Resultado: {resultado}")

                except Exception as e2:
                    self._log(f"❌ Error con método alternativo: {e2}", "error")

                    # MÉTODO 3: Último intento - Script muy simplificado
                    self._log("Último intento con script ultra-simplificado...")
                    try:
                        token_escapado = token.replace('\\', '\\\\').replace("'", "\\'")
                        script_simple = f"""
                        window.___grecaptcha_cfg.clients[0].callback('{token_escapado}');
                        """
                        await page.evaluate(script_simple)
                        self._log("✅ Captcha resuelto con script simplificado.")

                    except Exception as e3:
                        self._log(f"❌ Todos los métodos fallaron. Último error: {e3}", "error")
                        return False

            # Esperar un momento para que se procese
            await page.wait_for_timeout(2000)
            self._log("✅ Respuesta de captcha enviada correctamente")
            return True

        except Exception as e:
            self._log(f"❌ Error enviando respuesta de captcha: {e}", "error")
            import traceback
            self._log(f"Traceback completo:\n{traceback.format_exc()}", "error")
            return False
    
    async def resolver_captcha_completo(self) -> bool:
        """
        Proceso completo de detección y resolución de captcha.
        
        Returns:
            bool: True si el captcha se resolvió completamente
        """
        try:
            # Detectar si hay captcha
            if not await self.detectar_captcha():
                self._log("ℹ️ No se detectó captcha en la página")
                return True  # No hay captcha, consideramos éxito
            
            # Resolver captcha
            token = await self.resolver_captcha()
            if not token:
                raise Exception("No se pudo obtener token de captcha")
            
            # Enviar respuesta
            if not await self.enviar_respuesta_captcha(token):
                raise Exception("No se pudo enviar respuesta de captcha")
            
            # Verificar que se resolvió correctamente
            if await self._verificar_captcha_resuelto():
                self._log("🎉 Captcha resuelto y verificado exitosamente")
                return True
            else:
                raise Exception("Captcha no se marcó como resuelto")
                
        except Exception as e:
            self._log(f"💥 Error en proceso completo de captcha: {e}", "error")
            return False
    
    async def _verificar_captcha_resuelto(self) -> bool:
        """
        Verifica que el captcha se haya resuelto correctamente.
        
        Returns:
            bool: True si el captcha está resuelto
        """
        try:
            page = self.gestor_navegador.page
            if not page:
                return False
            
            # Esperar unos segundos para que se procese
            await page.wait_for_timeout(3000)
            
            # Buscar indicadores de que el captcha está resuelto
            indicadores_resuelto = [
                ".recaptcha-checkbox-checked",
                "[data-recaptcha-verified='true']",
                ".captcha-success"
            ]
            
            for selector in indicadores_resuelto:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 2000):
                        return True
                except Exception:
                    continue
            
            # Si no encontramos indicadores visuales, verificar si podemos continuar
            # (algunos sitios no muestran indicadores claros)
            # Intentar buscar si el botón de submit está habilitado
            selectores_submit = [
                "button[type='submit']:not([disabled])",
                "input[type='submit']:not([disabled])",
                ".login-button:not([disabled])"
            ]
            
            for selector in selectores_submit:
                try:
                    if await self.gestor_navegador.esperar_elemento(selector, 1000):
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self._log(f"❌ Error verificando captcha resuelto: {e}", "error")
            return False
    
    async def obtener_balance_api(self) -> Optional[float]:
        """
        Obtiene el balance disponible en la cuenta de 2Captcha.
        
        Returns:
            float: Balance disponible o None si hay error
        """
        try:
            if not self.solver:
                return None
            
            balance = self.solver.balance()
            return float(balance)
            
        except Exception as e:
            return None