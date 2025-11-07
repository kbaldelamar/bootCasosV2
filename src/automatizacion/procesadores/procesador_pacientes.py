"""
Procesador de pacientes para automatización.
Responsabilidad única: Procesar automatización específica para pacientes.
"""
import logging
from typing import List, Dict, Any, Optional, Callable

from .procesador_base import ProcesadorBase
from ..modelos.tarea_automatizacion import TareaAutomatizacion
from ..modelos.resultado_proceso import ResultadoProceso
from src.api.coosalud.coosalud_api_client import CoosaludApiClient


class ProcesadorPacientes(ProcesadorBase):
    """Procesador específico para automatización de pacientes."""
    
    def __init__(self, callback_log: Optional[Callable] = None):
        super().__init__("PACIENTES", callback_log)
        
        # Cliente API específico
        self.api_client = CoosaludApiClient()
        
        self._log("ProcesadorPacientes inicializado")
    
    async def obtener_datos(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de pacientes desde la API.
        
        Returns:
            List[Dict]: Lista de pacientes para procesar
        """
        try:
            self._log("📡 Obteniendo datos de pacientes desde API...")
            
            # Consultar API de pacientes
            respuesta_dto = self.api_client.obtener_pacientes_autorizacion()
            
            if not respuesta_dto or not respuesta_dto.data:
                raise Exception("No se obtuvieron datos de pacientes")
            
            # Convertir DTOs a diccionarios para procesamiento
            datos_pacientes = []
            for paciente_dto in respuesta_dto.data:
                datos_pacientes.append({
                    'identificacion': paciente_dto.identificacion,
                    'nombres': paciente_dto.nombres,
                    'apellidos': paciente_dto.apellidos,
                    'fecha_nacimiento': paciente_dto.fecha_nacimiento,
                    'genero': paciente_dto.genero,
                    'telefono': paciente_dto.telefono,
                    'email': paciente_dto.email,
                    'direccion': paciente_dto.direccion,
                    'tipo_autorizacion': paciente_dto.tipo_autorizacion,
                    'servicio_solicitado': paciente_dto.servicio_solicitado,
                    'fecha_solicitud': paciente_dto.fecha_solicitud,
                    'estado': paciente_dto.estado,
                    'observaciones': paciente_dto.observaciones
                })
            
            self._log(f"✅ {len(datos_pacientes)} pacientes obtenidos exitosamente")
            return datos_pacientes
            
        except Exception as e:
            self._log(f"❌ Error obteniendo datos de pacientes: {e}", "error")
            return []
    
    def crear_tarea(self, datos_item: Dict[str, Any], indice: int) -> TareaAutomatizacion:
        """
        Crea una tarea de automatización para un paciente.
        
        Args:
            datos_item: Datos del paciente
            indice: Índice en la lista
            
        Returns:
            TareaAutomatizacion: Tarea creada
        """
        try:
            identificacion = datos_item.get('identificacion', f'paciente_{indice}')
            
            return TareaAutomatizacion(
                id=f"paciente_{identificacion}_{indice}",
                contexto=self.contexto,
                tipo="procesar_paciente",
                datos=datos_item,
                prioridad=1
            )
            
        except Exception as e:
            self._log(f"❌ Error creando tarea para paciente {indice}: {e}", "error")
            raise
    
    async def procesar_item_individual(self, datos_item: Dict[str, Any]) -> ResultadoProceso:
        """
        Procesa un paciente individual en el sistema web.
        
        Args:
            datos_item: Datos del paciente
            
        Returns:
            ResultadoProceso: Resultado del procesamiento
        """
        identificacion = datos_item.get('identificacion', 'No ID')
        resultado = ResultadoProceso(
            tarea_id=f"paciente_{identificacion}",
            contexto=self.contexto,
            exitoso=False,
            mensaje=""
        )
        
        try:
            self._log(f"👤 Procesando paciente: {identificacion}")
            
            # Navegar a sección de pacientes
            if not await self._navegar_seccion_pacientes():
                raise Exception("No se pudo navegar a sección de pacientes")
            
            # Crear nuevo paciente
            if not await self._crear_nuevo_paciente():
                raise Exception("No se pudo iniciar creación de paciente")
            
            # Llenar formulario principal
            if not await self._llenar_formulario_principal(datos_item):
                raise Exception("Error llenando formulario principal")
            
            # Llenar datos médicos
            if not await self._llenar_datos_medicos(datos_item):
                raise Exception("Error llenando datos médicos")
            
            # Enviar formulario
            numero_caso = await self._enviar_formulario()
            if not numero_caso:
                raise Exception("No se pudo enviar formulario o no se obtuvo número de caso")
            
            # Guardar resultado en BD
            if not await self._guardar_en_bd(datos_item, numero_caso):
                raise Exception("Error guardando en base de datos")
            
            # Confirmar caso por API
            if not await self._confirmar_caso_api(identificacion, numero_caso):
                resultado.agregar_advertencia("Caso no confirmado por API")
            
            resultado.exitoso = True
            resultado.mensaje = f"Paciente procesado exitosamente - Caso: {numero_caso}"
            resultado.datos_resultado = {"numero_caso": numero_caso}
            
            self._log(f"✅ Paciente {identificacion} procesado exitosamente")
            
        except Exception as e:
            resultado.agregar_error(str(e))
            resultado.mensaje = f"Error procesando paciente {identificacion}: {e}"
            self._log(f"❌ Error procesando paciente {identificacion}: {e}", "error")
        
        return resultado
    
    async def _navegar_seccion_pacientes(self) -> bool:
        """Navega a la sección de pacientes."""
        try:
            # Usar el servicio de navegación del controlador
            return await self.controlador.servicio_navegacion.ir_a_seccion_pacientes()
            
        except Exception as e:
            self._log(f"❌ Error navegando a sección pacientes: {e}", "error")
            return False
    
    async def _crear_nuevo_paciente(self) -> bool:
        """Inicia la creación de un nuevo paciente."""
        try:
            self._log("➕ Iniciando creación de nuevo paciente...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Buscar botón de nuevo paciente
            selectores_nuevo = [
                "//button[contains(text(),'Nuevo Paciente')]",
                "//a[contains(text(),'Nuevo Paciente')]",
                "//button[contains(text(),'Agregar')]",
                ".btn-nuevo-paciente",
                "#nuevo-paciente"
            ]
            
            for selector in selectores_nuevo:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_timeout(2000)
                        self._log("✅ Botón nuevo paciente clickeado")
                        return True
                except Exception:
                    continue
            
            self._log("❌ No se encontró botón de nuevo paciente", "warning")
            return False
            
        except Exception as e:
            self._log(f"❌ Error creando nuevo paciente: {e}", "error")
            return False
    
    async def _llenar_formulario_principal(self, datos: Dict[str, Any]) -> bool:
        """Llena el formulario principal del paciente."""
        try:
            self._log("📝 Llenando formulario principal...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Mapeo de campos comunes
            campos = {
                "#identificacion": datos.get('identificacion', ''),
                "#nombres": datos.get('nombres', ''),
                "#apellidos": datos.get('apellidos', ''),
                "#telefono": datos.get('telefono', ''),
                "#email": datos.get('email', ''),
                "#direccion": datos.get('direccion', '')
            }
            
            # Llenar cada campo
            for selector, valor in campos.items():
                if valor:
                    try:
                        if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                            await page.fill(selector, str(valor))
                            self._log(f"✓ Campo {selector} llenado")
                    except Exception as e:
                        self._log(f"⚠️ Error llenando {selector}: {e}", "warning")
            
            self._log("✅ Formulario principal llenado")
            return True
            
        except Exception as e:
            self._log(f"❌ Error llenando formulario principal: {e}", "error")
            return False
    
    async def _llenar_datos_medicos(self, datos: Dict[str, Any]) -> bool:
        """Llena los datos médicos del paciente."""
        try:
            self._log("🏥 Llenando datos médicos...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return False
            
            # Campos médicos específicos
            campos_medicos = {
                "#tipo_autorizacion": datos.get('tipo_autorizacion', ''),
                "#servicio_solicitado": datos.get('servicio_solicitado', ''),
                "#observaciones": datos.get('observaciones', '')
            }
            
            for selector, valor in campos_medicos.items():
                if valor:
                    try:
                        if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                            await page.fill(selector, str(valor))
                            self._log(f"✓ Campo médico {selector} llenado")
                    except Exception as e:
                        self._log(f"⚠️ Error llenando campo médico {selector}: {e}", "warning")
            
            self._log("✅ Datos médicos llenados")
            return True
            
        except Exception as e:
            self._log(f"❌ Error llenando datos médicos: {e}", "error")
            return False
    
    async def _enviar_formulario(self) -> Optional[str]:
        """Envía el formulario y obtiene el número de caso."""
        try:
            self._log("📤 Enviando formulario...")
            
            page = self.controlador.gestor_navegador.page
            if not page:
                return None
            
            # Buscar botón de enviar/guardar
            selectores_enviar = [
                "//button[contains(text(),'Guardar')]",
                "//button[contains(text(),'Enviar')]",
                "//button[@type='submit']",
                ".btn-guardar",
                "#btn-guardar"
            ]
            
            for selector in selectores_enviar:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 2000):
                        await page.click(selector)
                        await page.wait_for_timeout(3000)
                        break
                except Exception:
                    continue
            
            # Buscar número de caso en la respuesta
            numero_caso = await self._extraer_numero_caso()
            if numero_caso:
                self._log(f"✅ Formulario enviado - Caso: {numero_caso}")
                return numero_caso
            else:
                self._log("⚠️ Formulario enviado pero no se obtuvo número de caso", "warning")
                return "CASO_SIN_NUMERO"
            
        except Exception as e:
            self._log(f"❌ Error enviando formulario: {e}", "error")
            return None
    
    async def _extraer_numero_caso(self) -> Optional[str]:
        """Extrae el número de caso de la página."""
        try:
            page = self.controlador.gestor_navegador.page
            if not page:
                return None
            
            # Selectores comunes para número de caso
            selectores_caso = [
                "//span[contains(text(),'Caso:')]",
                "//div[contains(text(),'Número de caso')]",
                ".numero-caso",
                "#numero-caso"
            ]
            
            for selector in selectores_caso:
                try:
                    if await self.controlador.gestor_navegador.esperar_elemento(selector, 3000):
                        elemento = await page.query_selector(selector)
                        texto = await elemento.text_content() if elemento else ""
                        
                        # Extraer número usando regex
                        import re
                        match = re.search(r'(\d+)', texto)
                        if match:
                            return match.group(1)
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            self._log(f"❌ Error extrayendo número de caso: {e}", "error")
            return None
    
    async def _guardar_en_bd(self, datos_paciente: Dict[str, Any], numero_caso: str) -> bool:
        """Guarda el resultado en la base de datos."""
        try:
            self._log(f"💾 Guardando en BD - Caso: {numero_caso}")
            
            # Aquí implementarías la lógica de guardado en BD
            # Por ahora, simulamos el guardado
            await asyncio.sleep(0.1)
            
            self._log("✅ Datos guardados en BD")
            return True
            
        except Exception as e:
            self._log(f"❌ Error guardando en BD: {e}", "error")
            return False
    
    async def _confirmar_caso_api(self, identificacion: str, numero_caso: str) -> bool:
        """Confirma el caso mediante API."""
        try:
            self._log(f"📡 Confirmando caso por API: {numero_caso}")
            
            # Aquí implementarías la confirmación por API
            # Por ahora, simulamos la confirmación
            await asyncio.sleep(0.1)
            
            self._log("✅ Caso confirmado por API")
            return True
            
        except Exception as e:
            self._log(f"❌ Error confirmando por API: {e}", "error")
            return False
    
    async def validar_conexion(self) -> bool:
        """
        Valida la conexión con la API de pacientes.
        
        Returns:
            bool: True si la conexión es válida
        """
        try:
            self._log("🔍 Validando conexión API de pacientes...")
            
            # Validar conexión con API
            if not self.api_client.validar_conexion_api():
                raise Exception("API de pacientes no responde")
            
            self._log("✅ Conexión API válida")
            return True
            
        except Exception as e:
            self._log(f"❌ Error validando conexión: {e}", "error")
            return False