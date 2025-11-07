#!/usr/bin/env python3
"""
Script de prueba simple para verificar logging y captcha
"""
import asyncio
import sys
import os

# Configurar PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

async def test_simple():
    """Prueba simple del logging"""
    print("=== PRUEBA SIMPLE DE LOGGING ===")
    
    # Importar y probar los servicios críticos
    from src.automatizacion.servicios.servicio_login import ServicioLogin
    from src.automatizacion.servicios.servicio_navegacion import ServicioNavegacion
    from src.automatizacion.servicios.orquestador_login import OrquestadorLogin
    from src.automatizacion.servicios.servicio_captcha import ServicioCaptcha
    from src.automatizacion.nucleo.gestor_navegador import GestorNavegador
    from src.automatizacion.modelos.configuracion_automatizacion import ConfiguracionAutomatizacion
    
    configuracion = ConfiguracionAutomatizacion()
    
    def callback_test(mensaje, nivel, contexto):
        print(f"LOG [{nivel.upper()}] [{contexto}]: {mensaje}")
    
    gestor = GestorNavegador("test_context")
    
    # Probar ServicioNavegacion con emoji 🔗
    nav = ServicioNavegacion(gestor, "test", callback_test, configuracion)
    nav._log("🔗 Probando emoji de link", "info")
    
    # Probar OrquestadorLogin con emoji 🔐  
    login = ServicioLogin(gestor, "test", callback_test, configuracion)
    orq = OrquestadorLogin(gestor, "test", callback_test, configuracion)
    orq._log("🔐 Probando emoji de autenticación", "info")
    
    # Probar ServicioCaptcha con emoji 💥
    captcha = ServicioCaptcha(gestor, "test", callback_test)
    captcha._log("💥 Probando emoji de fallo", "error")
    captcha._log("🎉 Probando emoji de éxito", "info")
    
    print("=== TODOS LOS EMOJIS FUNCIONAN ===")

if __name__ == "__main__":
    asyncio.run(test_simple())