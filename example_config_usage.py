"""
Ejemplo de uso del sistema de configuración DTO
Muestra cómo acceder y modificar configuraciones desde cualquier parte de la aplicación.
"""

from src.core.config import config, get_config, set_config

def ejemplo_uso_configuracion():
    """Ejemplos de cómo usar el sistema de configuración."""
    
    print("=== EJEMPLOS DE USO DEL SISTEMA DE CONFIGURACIÓN ===\n")
    
    # 1. Acceder a configuraciones usando la instancia global
    print("1. Usando la instancia global 'config':")
    print(f"   Nombre de la app: {config.get('app.name')}")
    print(f"   Versión: {config.get('app.version')}")
    print(f"   Debug activado: {config.get('app.debug')}")
    print(f"   URL de la API: {config.get('api.base_url')}")
    print(f"   Servidor de licencias: {config.get('license.server_url')}")
    print(f"   Archivo local de licencia: {config.get('license.local_file')}")
    
    # 2. Usando las funciones de conveniencia
    print("\n2. Usando funciones de conveniencia:")
    print(f"   Ancho de ventana: {get_config('ui.window_width')}")
    print(f"   Alto de ventana: {get_config('ui.window_height')}")
    print(f"   Tema: {get_config('ui.theme')}")
    print(f"   Playwright headless: {get_config('playwright.headless')}")
    
    # 3. Valores por defecto
    print("\n3. Usando valores por defecto:")
    print(f"   Configuración inexistente: {get_config('inexistente.valor', 'VALOR_DEFAULT')}")
    
    # 4. Modificar configuraciones en tiempo de ejecución
    print("\n4. Modificando configuraciones:")
    print(f"   Debug antes: {get_config('app.debug')}")
    set_config('app.debug', False)
    print(f"   Debug después: {get_config('app.debug')}")
    
    # 5. Agregar nuevas configuraciones
    print("\n5. Agregando nuevas configuraciones:")
    set_config('custom.nueva_config', 'Mi valor personalizado')
    print(f"   Nueva configuración: {get_config('custom.nueva_config')}")
    
    # 6. Obtener toda la configuración
    print("\n6. Estructura completa de configuración:")
    todas_config = config.get_all()
    for categoria, valores in todas_config.items():
        print(f"   {categoria}: {valores}")


class EjemploClase:
    """Ejemplo de cómo usar configuración en una clase."""
    
    def __init__(self):
        # Cargar configuraciones necesarias en el constructor
        self.app_name = get_config('app.name')
        self.api_url = get_config('api.base_url')
        self.debug_mode = get_config('app.debug')
    
    def hacer_algo(self):
        """Método que usa configuración."""
        if self.debug_mode:
            print(f"[DEBUG] {self.app_name} ejecutándose en modo debug")
            print(f"[DEBUG] Conectando a API: {self.api_url}")
        
        # También puedes acceder directamente sin almacenar en self
        timeout = get_config('api.timeout')
        print(f"Timeout configurado: {timeout} segundos")
    
    def cambiar_configuracion(self):
        """Ejemplo de modificar configuración desde un método."""
        # Cambiar el timeout de la API
        nuevo_timeout = 60
        set_config('api.timeout', nuevo_timeout)
        print(f"Timeout cambiado a: {nuevo_timeout} segundos")


if __name__ == "__main__":
    # Ejecutar ejemplos
    ejemplo_uso_configuracion()
    
    print("\n" + "="*60 + "\n")
    
    # Ejemplo con clase
    print("=== EJEMPLO CON CLASE ===")
    mi_clase = EjemploClase()
    mi_clase.hacer_algo()
    mi_clase.cambiar_configuracion()
    mi_clase.hacer_algo()  # Mostrar el cambio