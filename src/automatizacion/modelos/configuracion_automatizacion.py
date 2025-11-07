"""
Modelo de configuración para automatización.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


@dataclass
class ConfiguracionAutomatizacion:
    """Configuración para procesos de automatización."""
    
    # Configuración general
    modo: str = "automatico"  # Modo de ejecución: "automatico" (sin intervención), "manual" (paso a paso), "supervisado" (con confirmación)
    reintentos_maximos: int = 3  # Número máximo de intentos antes de fallar
    ejecutar_en_segundo_plano: bool = False  # Si ejecutar el navegador en modo headless (sin ventana visible)
    activar_captcha_automatico: bool = True  # Si resolver captchas automáticamente usando servicio 2Captcha
    
    # Configuración de navegador
    navegador_headless: bool = False  # Si mostrar el navegador (False) o ejecutar oculto (True)
    tiempo_espera_elemento: int = 10  # Segundos máximos para esperar que aparezca un elemento en la página
    tiempo_espera_pagina: int = 30  # Segundos máximos para esperar que cargue una página completa
    
    # Configuración de login - CREDENCIALES REALES DEL SISTEMA COOSALUD
    url_login: str = "https://portalsalud.coosalud.com/login"  # URL del sistema de login de Coosalud
    usuario: str = "biomedips@gmail.com"  # Email/usuario para autenticarse en Coosalud
    password: str = "Caucasia1+"  # Contraseña para autenticarse en Coosalud
    
    # Configuración de captcha
    clave_2captcha: str = ""  # API key del servicio 2Captcha para resolver captchas automáticamente
    activar_2captcha: bool = False  # Si usar el servicio 2Captcha (requiere API key válida)
    
    # Configuración específica del proceso
    configuracion_especifica: Dict[str, Any] = None
    
    def __post_init__(self):
        """Inicializa valores por defecto después de la creación."""
        if self.configuracion_especifica is None:
            self.configuracion_especifica = {}
    
    def obtener_configuracion_navegador(self) -> Dict[str, Any]:
        """Obtiene configuración específica del navegador."""
        return {
            "headless": self.navegador_headless,
            "timeout_elemento": self.tiempo_espera_elemento,
            "timeout_pagina": self.tiempo_espera_pagina
        }
    
    def obtener_configuracion_login(self) -> Dict[str, Any]:
        """Obtiene configuración de login."""
        return {
            "url": self.url_login,
            "usuario": self.usuario,
            "password": self.password,
            "reintentos": self.reintentos_maximos
        }
    
    def obtener_configuracion_captcha(self) -> Dict[str, Any]:
        """Obtiene configuración de captcha."""
        return {
            "activar": self.activar_captcha_automatico,
            "clave_2captcha": self.clave_2captcha,
            "usar_2captcha": self.activar_2captcha
        }
    
    def validar_configuracion(self) -> Tuple[bool, str]:
        """Valida que la configuración sea válida."""
        if self.modo not in ["automatico", "manual", "supervisado"]:
            return False, "Modo de ejecución inválido"
        
        if self.reintentos_maximos < 1 or self.reintentos_maximos > 10:
            return False, "Número de reintentos debe estar entre 1 y 10"
        
        if self.tiempo_espera_elemento < 5 or self.tiempo_espera_elemento > 60:
            return False, "Tiempo de espera de elemento debe estar entre 5 y 60 segundos"
        
        if self.tiempo_espera_pagina < 10 or self.tiempo_espera_pagina > 120:
            return False, "Tiempo de espera de página debe estar entre 10 y 120 segundos"
        
        if not self.url_login:
            return False, "URL de login es requerida"
        
        if not self.usuario:
            return False, "Usuario es requerido"
        
        if not self.password:
            return False, "Password es requerido"
        
        return True, "Configuración válida"
    
    def clonar(self) -> 'ConfiguracionAutomatizacion':
        """Crea una copia de la configuración."""
        return ConfiguracionAutomatizacion(
            modo=self.modo,
            reintentos_maximos=self.reintentos_maximos,
            ejecutar_en_segundo_plano=self.ejecutar_en_segundo_plano,
            activar_captcha_automatico=self.activar_captcha_automatico,
            navegador_headless=self.navegador_headless,
            tiempo_espera_elemento=self.tiempo_espera_elemento,
            tiempo_espera_pagina=self.tiempo_espera_pagina,
            url_login=self.url_login,
            usuario=self.usuario,
            password=self.password,
            clave_2captcha=self.clave_2captcha,
            activar_2captcha=self.activar_2captcha,
            configuracion_especifica=self.configuracion_especifica.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario."""
        return {
            "modo": self.modo,
            "reintentos_maximos": self.reintentos_maximos,
            "ejecutar_en_segundo_plano": self.ejecutar_en_segundo_plano,
            "activar_captcha_automatico": self.activar_captcha_automatico,
            "navegador_headless": self.navegador_headless,
            "tiempo_espera_elemento": self.tiempo_espera_elemento,
            "tiempo_espera_pagina": self.tiempo_espera_pagina,
            "url_login": self.url_login,
            "usuario": self.usuario,
            "password": self.password,
            "clave_2captcha": self.clave_2captcha,
            "activar_2captcha": self.activar_2captcha,
            "configuracion_especifica": self.configuracion_especifica
        }
    
    @classmethod
    def desde_diccionario(cls, datos: Dict[str, Any]) -> 'ConfiguracionAutomatizacion':
        """Crea una configuración desde un diccionario."""
        return cls(
            modo=datos.get("modo", "automatico"),
            reintentos_maximos=datos.get("reintentos_maximos", 3),
            ejecutar_en_segundo_plano=datos.get("ejecutar_en_segundo_plano", False),
            activar_captcha_automatico=datos.get("activar_captcha_automatico", True),
            navegador_headless=datos.get("navegador_headless", False),
            tiempo_espera_elemento=datos.get("tiempo_espera_elemento", 10),
            tiempo_espera_pagina=datos.get("tiempo_espera_pagina", 30),
            url_login=datos.get("url_login", ""),
            usuario=datos.get("usuario", ""),
            password=datos.get("password", ""),
            clave_2captcha=datos.get("clave_2captcha", ""),
            activar_2captcha=datos.get("activar_2captcha", False),
            configuracion_especifica=datos.get("configuracion_especifica", {})
        )