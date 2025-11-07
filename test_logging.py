#!/usr/bin/env python3
"""
Script de prueba para verificar el logging mejorado
"""
import asyncio
import sys
import os

# Configurar PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

from src.automatizacion.servicios.servicio_login import ServicioLogin
from src.automatizacion.nucleo.gestor_navegador import GestorNavegador
from src.automatizacion.modelos.configuracion_automatizacion import ConfiguracionAutomatizacion

async def probar_logging():
    """Prueba del sistema de logging mejorado"""
    
    print("=== PRUEBA DE LOGGING MEJORADO ===")
    print("Iniciando prueba del sistema de logging...")
    
    # Configurar
    configuracion = ConfiguracionAutomatizacion()
    
    # Crear gestor de navegador
    gestor = GestorNavegador("test_context")
    
    def callback_test(mensaje, nivel, contexto):
        print(f"CALLBACK LOG [{nivel.upper()}] [{contexto}]: {mensaje}")
    
    # Crear servicio de login
    servicio = ServicioLogin(
        gestor_navegador=gestor,
        contexto="test_login",
        callback_log=callback_test,
        configuracion=configuracion
    )
    
    # Probar diferentes tipos de logs con emojis
    print("\n--- Probando logging con emojis ---")
    servicio._log("📧 Probando emoji de email", "info")
    servicio._log("🔒 Probando emoji de contraseña", "info") 
    servicio._log("✅ Probando emoji de éxito", "info")
    servicio._log("❌ Probando emoji de error", "error")
    servicio._log("⚠️ Probando emoji de advertencia", "warning")
    
    # Probar métodos reales que usan emojis
    print("\n--- Probando método real ---")
    try:
        await gestor.inicializar()
        await servicio.verificar_campos_login()
    except Exception as e:
        print(f"Error esperado durante prueba: {e}")
    finally:
        await gestor.cerrar()
    
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    asyncio.run(probar_logging())