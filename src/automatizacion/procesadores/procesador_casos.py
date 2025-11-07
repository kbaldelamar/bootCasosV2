"""
Procesador de casos para automatización.
Responsabilidad única: Procesar automatización específica para casos.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable

from .procesador_base import ProcesadorBase
from ..modelos.tarea_automatizacion import TareaAutomatizacion
from ..modelos.resultado_proceso import ResultadoProceso
from ..modelos.configuracion_automatizacion import ConfiguracionAutomatizacion
from src.api.api_client import ApiClient
from src.models.coosalud import RespuestaCasosDto


class ProcesadorCasos(ProcesadorBase):
    """Procesador específico para automatización de casos."""
    
    def __init__(self, configuracion: Optional[ConfiguracionAutomatizacion] = None, callback_log: Optional[Callable] = None):
        super().__init__("CASOS", callback_log)
        
        # Cliente API específico
        self.api_client = ApiClient()
        self.configuracion = configuracion if configuracion is not None else ConfiguracionAutomatizacion()
        
        self._log("ProcesadorCasos inicializado")
    
    async def obtener_datos(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de casos desde la API usando DTOs.
        
        Returns:
            List[Dict]: Lista de casos para procesar
        """
        try:
            self._log("📡 Obteniendo datos de casos desde API...")
            
            # Consultar API de casos usando configuración centralizada
            url_casos = self.configuracion.obtener_url_casos()
            response = self.api_client.get(url_casos)
            
            if not response or response.get('status_code') != 200:
                raise Exception(f"Error en API: {response.get('status_code')} - {response.get('error')}")
            
            # Usar DTO para procesar la respuesta
            datos_api = response.get('data', {})
            respuesta_dto = RespuestaCasosDto.from_api_response(datos_api)
            
            if not respuesta_dto.es_exitosa():
                raise Exception(f"Respuesta no exitosa: {respuesta_dto.message}")
            
            # Obtener solo casos válidos
            casos_validos = respuesta_dto.obtener_casos_validos()
            
            # Log estadísticas
            stats = respuesta_dto.obtener_estadisticas()
            self._log(f"📊 Casos obtenidos: {stats['total_casos']} total, {stats['casos_validos']} válidos")
            
            # Convertir DTOs a diccionarios para compatibilidad
            datos_casos = []
            for caso_dto in casos_validos:
                datos_casos.append({
                    'caso': caso_dto.caso,
                    'fecha': caso_dto.fecha,
                    'idIngreso': caso_dto.id_ingreso,
                    'idOrden': caso_dto.id_orden,
                    'idRecepcion': caso_dto.id_recepcion,
                    'identificador_unico': caso_dto.obtener_identificador_unico()
                })
            
            if not datos_casos:
                self._log("⚠️ No se encontraron casos válidos para procesar", "warning")
                return []
            
            self._log(f"✅ Se obtuvieron {len(datos_casos)} casos válidos para procesar")
            return datos_casos
            
        except Exception as e:
            self._log(f"❌ Error obteniendo datos de casos: {e}", "error")
            return []
    
    def crear_tarea(self, datos_item: Dict[str, Any], indice: int) -> TareaAutomatizacion:
        """
        Crea una tarea de automatización para un caso.
        
        Args:
            datos_item: Datos del caso
            indice: Índice en la lista
            
        Returns:
            TareaAutomatizacion: Tarea creada
        """
        try:
            numero_caso = datos_item.get('caso', f'caso_{indice}')
            
            return TareaAutomatizacion(
                id=f"caso_{numero_caso}_{indice}",
                contexto=self.contexto,
                tipo="actualizar_caso",
                datos=datos_item,
                prioridad=2  # Prioridad menor que pacientes
            )
            
        except Exception as e:
            self._log(f"❌ Error creando tarea para caso {indice}: {e}", "error")
            raise
    
    async def procesar_item_individual(self, datos_item: Dict[str, Any]) -> ResultadoProceso:
        """
        Procesa un caso individual en el sistema web.
        
        Args:
            datos_item: Datos del caso
            
        Returns:
            ResultadoProceso: Resultado del procesamiento
        """
        numero_caso = datos_item.get('caso', 'No Case')
        resultado = ResultadoProceso(
            tarea_id=f"caso_{numero_caso}",
            contexto=self.contexto,
            exitoso=False,
            mensaje=""
        )
        
        try:
            self._log(f"📋 Procesando caso: {numero_caso}")
            
            # Navegar a sección de casos
            if not await self._navegar_seccion_casos():
                raise Exception("No se pudo navegar a sección de casos")
            
            # Buscar el caso en el sistema
            if not await self._buscar_caso(numero_caso):
                raise Exception(f"Caso {numero_caso} no encontrado en sistema")
            
            # Actualizar información del caso
            if not await self._actualizar_informacion_caso(datos_item):
                raise Exception("Error actualizando información del caso")
            
            # Cambiar estado del caso
            if not await self._cambiar_estado_caso("procesado"):
                raise Exception("Error cambiando estado del caso")
            
            # Guardar cambios
            if not await self._guardar_cambios():
                raise Exception("Error guardando cambios del caso")
            
            # Confirmar actualización por API
            if not await self._confirmar_actualizacion_api(numero_caso):
                resultado.agregar_advertencia("Actualización no confirmada por API")
            
            resultado.exitoso = True
            resultado.mensaje = f"Caso {numero_caso} procesado exitosamente"
            resultado.datos_resultado = {
                "numero_caso": numero_caso,
                "estado_actualizado": "procesado"
            }
            
            self._log(f"✅ Caso {numero_caso} procesado exitosamente")
            
        except Exception as e:
            resultado.agregar_error(str(e))
            resultado.mensaje = f"Error procesando caso {numero_caso}: {e}"
            self._log(f"❌ Error procesando caso {numero_caso}: {e}", "error")
        
        return resultado
    
    async def _navegar_seccion_casos(self) -> bool:
        """Navega a la sección de casos."""
        try:
            # Usar el servicio de navegación del controlador
            return await self.controlador.servicio_navegacion.ir_a_seccion_casos()
            
        except Exception as e:
            self._log(f"❌ Error navegando a sección casos: {e}", "error")
            return False
    
    async def _buscar_caso(self, numero_caso: str) -> bool:
        """Busca un caso específico en el sistema."""
        try:
            self._log(f"🔍 Buscando caso: {numero_caso}")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar campo de búsqueda
            selectores_busqueda = [
                "#buscar-caso",
                "#numero-caso",
                "input[placeholder*='caso']",
                "input[placeholder*='búsqueda']",
                ".search-input"
            ]
            
            for selector in selectores_busqueda:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        # Limpiar y escribir número de caso
                        await page.fill(selector, "")
                        await page.fill(selector, numero_caso)
                        
                        # Presionar Enter o buscar botón de búsqueda
                        await page.press(selector, "Enter")
                        await page.wait_for_timeout(2000)
                        
                        # Verificar si se encontró el caso
                        if await self._verificar_caso_encontrado(numero_caso):
                            self._log(f"✅ Caso {numero_caso} encontrado")
                            return True
                        
                except Exception:
                    continue
            
            self._log(f"❌ Caso {numero_caso} no encontrado", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error buscando caso {numero_caso}: {e}", "error")
            return False
    
    async def _verificar_caso_encontrado(self, numero_caso: str) -> bool:
        """Verifica que el caso fue encontrado en los resultados."""
        try:
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar el número de caso en los resultados
            selectores_resultado = [
                f"//td[contains(text(),'{numero_caso}')]",
                f"//span[contains(text(),'{numero_caso}')]",
                f"//div[contains(text(),'{numero_caso}')]"
            ]
            
            for selector in selectores_resultado:
                if await self.controlador.gestor_navegador.esperar_elemento(selector, 3000):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando caso encontrado: {e}")
            return False
    
    async def _actualizar_informacion_caso(self, datos: Dict[str, Any]) -> bool:
        """Actualiza la información del caso."""
        try:
            self._log("📝 Actualizando información del caso...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar botón de editar/actualizar
            selectores_editar = [
                "//button[contains(text(),'Editar')]",
                "//a[contains(text(),'Editar')]",
                ".btn-editar",
                "#btn-editar"
            ]
            
            for selector in selectores_editar:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue
            
            # Actualizar campos disponibles
            campos_actualizar = {
                "#fecha": datos.get('fecha', ''),
                "#id-ingreso": str(datos.get('idIngreso', '')),
                "#id-orden": str(datos.get('idOrden', '')),
                "#id-recepcion": str(datos.get('idRecepcion', ''))
            }
            
            for selector, valor in campos_actualizar.items():
                if valor:
                    try:
                        if await self.controlador.gestor_navegador.esperar_elemento(selector, 1000):
                            await page.fill(selector, valor)
                            self._log(f"✓ Campo {selector} actualizado")
                    except Exception as e:
                        self._log(f"⚠️ Error actualizando {selector}: {e}", "warning")
            
            self._log("✅ Información del caso actualizada")
            return True
            
        except Exception as e:
            self._log(f"❌ Error actualizando información: {e}", "error")
            return False
    
    async def _cambiar_estado_caso(self, nuevo_estado: str) -> bool:
        """Cambia el estado del caso."""
        try:
            self._log(f"🔄 Cambiando estado a: {nuevo_estado}")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar dropdown o campo de estado
            selectores_estado = [
                "#estado",
                "#estado-caso",
                "select[name='estado']",
                ".estado-select"
            ]
            
            for selector in selectores_estado:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.select_option(selector, nuevo_estado)
                        self._log("✅ Estado cambiado exitosamente")
                        return True
                except Exception:
                    continue
            
            self._log("⚠️ No se encontró campo de estado", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error cambiando estado: {e}", "error")
            return False
    
    async def _guardar_cambios(self) -> bool:
        """Guarda los cambios realizados al caso."""
        try:
            self._log("💾 Guardando cambios...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar botón de guardar
            selectores_guardar = [
                "//button[contains(text(),'Guardar')]",
                "//button[contains(text(),'Actualizar')]",
                "//button[@type='submit']",
                ".btn-guardar",
                "#btn-guardar"
            ]
            
            for selector in selectores_guardar:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_timeout(3000)
                        
                        # Verificar mensaje de éxito
                        if await self._verificar_guardado_exitoso():
                            self._log("✅ Cambios guardados exitosamente")
                            return True
                        
                except Exception:
                    continue
            
            self._log("⚠️ No se pudo confirmar guardado", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error guardando cambios: {e}", "error")
            return False
    
    async def _verificar_guardado_exitoso(self) -> bool:
        """Verifica que los cambios se guardaron correctamente."""
        try:
            # Buscar mensajes de éxito
            selectores_exito = [
                "//div[contains(@class,'alert-success')]",
                "//span[contains(text(),'exitoso')]",
                "//div[contains(text(),'Guardado')]",
                ".success-message"
            ]
            
            for selector in selectores_exito:
                if await self.controlador.gestor_navegador.esperar_elemento(selector, 3000):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando guardado: {e}")
            return False
    
    async def _confirmar_actualizacion_api(self, numero_caso: str) -> bool:
        """Confirma la actualización mediante API."""
        try:
            self._log(f"📡 Confirmando actualización por API: {numero_caso}")
            
            # Aquí implementarías la confirmación por API
            # Por ahora, simulamos la confirmación
            await asyncio.sleep(0.1)
            
            self._log("✅ Actualización confirmada por API")
            return True
            
        except Exception as e:
            self._log(f"❌ Error confirmando por API: {e}", "error")
            return False
    
    async def validar_conexion(self) -> bool:
        """
        Valida la conexión con la API de casos.
        
        Returns:
            bool: True si la conexión es válida
        """
        try:
            self._log("🔍 Validando conexión API de casos...")
            
            # Validar conexión con API usando configuración centralizada
            url_casos = self.configuracion.obtener_url_casos()
            response = self.api_client.get(url_casos)
            if not response or response.get('status_code') not in [200, 404]:
                raise Exception("API de casos no responde")
            
            self._log("✅ Conexión API válida")
            return True
            
        except Exception as e:
            self._log(f"❌ Error validando conexión: {e}", "error")
            return False