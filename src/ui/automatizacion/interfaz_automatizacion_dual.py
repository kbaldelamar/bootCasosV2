"""
Interfaz de automatización dual para Coosalud con lógica real integrada.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QProgressBar, QMessageBox, QGroupBox, QGridLayout, QSplitter,
    QTextEdit, QTabWidget, QCheckBox, QSpinBox, QComboBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor
from src.core.config import config
from src.automatizacion.controlador_automatizacion_principal import ControladorAutomatizacionPrincipal
from src.automatizacion.modelos.configuracion_automatizacion import ConfiguracionAutomatizacion


class ManejadorLogs(QObject):
    """Manejador de logs para mostrar en la interfaz."""
    
    log_recibido = Signal(str, str, str)  # mensaje, nivel, contexto
    
    def emitir_log(self, mensaje: str, nivel: str = "info", contexto: str = "general"):
        """Emite un log para mostrar en la interfaz."""
        self.log_recibido.emit(mensaje, nivel, contexto)


class HiloAutomatizacion(QThread):
    """Thread para ejecutar procesos de automatización con lógica real."""
    
    proceso_iniciado = Signal(str)  # contexto
    progreso_actualizado = Signal(str, int)  # contexto, porcentaje
    log_emitido = Signal(str, str, str)  # mensaje, nivel, contexto
    proceso_terminado = Signal(str, bool, str)  # contexto, exito, mensaje_final
    
    def __init__(self, contexto: str, controlador: ControladorAutomatizacionPrincipal):
        super().__init__()
        self.contexto = contexto
        self.controlador = controlador
        self.deberia_detenerse = False
        self.configuracion = None
        self.logger = logging.getLogger(f"{__name__}.{contexto}")
        
        # Configurar callback de logs
        self.controlador.callback_log = self.emitir_log_desde_controlador
    
    def configurar_proceso(self, config: Dict[str, Any]):
        """Configura el proceso con parámetros."""
        self.configuracion = ConfiguracionAutomatizacion(
            modo=config.get("modo", "automatico"),
            reintentos_maximos=config.get("reintentos", 3),
            navegador_headless=config.get("headless", False),
            activar_captcha_automatico=config.get("captcha_auto", True),
            url_login=config.get("url_login", "https://pqrcoosalud.com/auth/login"),
            usuario=config.get("usuario", ""),
            password=config.get("password", "")
        )
    
    def detener_proceso(self):
        """Solicita la detención del proceso."""
        self.deberia_detenerse = True
    
    def emitir_log_desde_controlador(self, mensaje: str, nivel: str, contexto: str):
        """Callback para recibir logs del controlador."""
        self.log_emitido.emit(mensaje, nivel, contexto)
        
        # Simular progreso basado en mensajes
        if "Inicializando" in mensaje:
            self.progreso_actualizado.emit(contexto, 10)
        elif "Navegando" in mensaje:
            self.progreso_actualizado.emit(contexto, 30)
        elif "Autenticando" in mensaje:
            self.progreso_actualizado.emit(contexto, 50)
        elif "Obteniendo" in mensaje:
            self.progreso_actualizado.emit(contexto, 70)
        elif "Procesando" in mensaje:
            self.progreso_actualizado.emit(contexto, 90)
        elif "completada" in mensaje or "completado" in mensaje:
            self.progreso_actualizado.emit(contexto, 100)
    
    def run(self):
        """Ejecuta el proceso real de automatización."""
        try:
            self.proceso_iniciado.emit(self.contexto)
            
            if not self.configuracion:
                raise Exception("Configuración no establecida")
            
            # Crear nuevo loop de eventos para este thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if self.contexto == "pacientes":
                    resultado = loop.run_until_complete(
                        self.controlador.ejecutar_automatizacion_pacientes(self.configuracion)
                    )
                elif self.contexto == "casos":
                    resultado = loop.run_until_complete(
                        self.controlador.ejecutar_automatizacion_casos(self.configuracion)
                    )
                else:
                    raise Exception(f"Contexto desconocido: {self.contexto}")
                
                # Procesar resultado
                if resultado.exitoso:
                    self.proceso_terminado.emit(self.contexto, True, "Proceso completado exitosamente")
                else:
                    self.proceso_terminado.emit(self.contexto, False, resultado.mensaje)
                    
            finally:
                loop.close()
            
        except Exception as e:
            self.log_emitido.emit(f"❌ Error en automatización {self.contexto}: {e}", "error", self.contexto)
            self.proceso_terminado.emit(self.contexto, False, f"Error: {e}")


class HiloProcesadorPacientes(HiloAutomatizacion):
    """Thread específico para automatización de pacientes."""
    
    def __init__(self, controlador: ControladorAutomatizacionPrincipal):
        super().__init__("pacientes", controlador)


class HiloProcesadorCasos(HiloAutomatizacion):
    """Thread específico para automatización de casos."""
    
    def __init__(self, controlador: ControladorAutomatizacionPrincipal):
        super().__init__("casos", controlador)


class PanelControlAutomatizacion(QFrame):
    """Panel de control para un proceso de automatización."""
    
    proceso_iniciado = Signal(str)  # contexto
    proceso_detenido = Signal(str)  # contexto
    
    def __init__(self, contexto: str, titulo: str, color_acento: str, controlador: ControladorAutomatizacionPrincipal):
        super().__init__()
        self.contexto = contexto
        self.titulo = titulo
        self.color_acento = color_acento
        self.controlador = controlador
        self.hilo_proceso = None
        self.activo = False
        self.estadisticas = {
            "procesados": 0,
            "exitosos": 0,
            "errores": 0,
            "tiempo_inicio": None
        }
        
        self.configurar_interfaz()
        self.configurar_estilos()
        self.configurar_timer_estadisticas()
    
    def configurar_interfaz(self):
        """Configura la interfaz del panel de control compacto."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header del panel más compacto
        header_layout = QHBoxLayout()
        
        self.lbl_titulo = QLabel(self.titulo)
        self.lbl_titulo.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.lbl_titulo)
        
        header_layout.addStretch()
        
        self.lbl_estado = QLabel("⏸️ Detenido")
        self.lbl_estado.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(self.lbl_estado)
        
        layout.addLayout(header_layout)
        
        # Configuración compacta
        config_group = QGroupBox("⚙️ Configuración")
        config_group.setMaximumHeight(120)
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(5)
        
        # Configuración en grid más compacto
        config_layout.addWidget(QLabel("Modo:"), 0, 0)
        self.combo_modo = QComboBox()
        self.combo_modo.addItems(["automatico", "manual", "supervisado"])
        self.combo_modo.setCurrentText("automatico")
        config_layout.addWidget(self.combo_modo, 0, 1)
        
        config_layout.addWidget(QLabel("Reintentos:"), 0, 2)
        self.spin_reintentos = QSpinBox()
        self.spin_reintentos.setMinimum(1)
        self.spin_reintentos.setMaximum(5)
        self.spin_reintentos.setValue(3)
        config_layout.addWidget(self.spin_reintentos, 0, 3)
        
        # Opciones en una fila
        self.check_headless = QCheckBox("Segundo plano")
        config_layout.addWidget(self.check_headless, 1, 0, 1, 2)
        
        self.check_captcha = QCheckBox("Captcha auto")
        self.check_captcha.setChecked(True)
        config_layout.addWidget(self.check_captcha, 1, 2, 1, 2)
        
        layout.addWidget(config_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Controles más compactos
        controles_layout = QHBoxLayout()
        
        self.btn_iniciar = QPushButton("▶️ Iniciar")
        self.btn_iniciar.setMaximumHeight(35)
        controles_layout.addWidget(self.btn_iniciar)
        
        self.btn_detener = QPushButton("⏹️ Detener")
        self.btn_detener.setMaximumHeight(35)
        self.btn_detener.setEnabled(False)
        controles_layout.addWidget(self.btn_detener)
        
        self.btn_reiniciar = QPushButton("🔄 Reiniciar")
        self.btn_reiniciar.setMaximumHeight(35)
        controles_layout.addWidget(self.btn_reiniciar)
        
        layout.addLayout(controles_layout)
        
        # Estadísticas compactas
        stats_group = QGroupBox("📊 Estadísticas")
        stats_group.setMaximumHeight(80)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(3)
        
        self.lbl_procesados = QLabel("Procesados: 0")
        self.lbl_procesados.setFont(QFont("Arial", 9))
        stats_layout.addWidget(self.lbl_procesados, 0, 0)
        
        self.lbl_exitosos = QLabel("Exitosos: 0")
        self.lbl_exitosos.setFont(QFont("Arial", 9))
        stats_layout.addWidget(self.lbl_exitosos, 0, 1)
        
        self.lbl_errores = QLabel("Errores: 0")
        self.lbl_errores.setFont(QFont("Arial", 9))
        stats_layout.addWidget(self.lbl_errores, 1, 0)
        
        self.lbl_tiempo = QLabel("Tiempo: 00:00")
        self.lbl_tiempo.setFont(QFont("Arial", 9))
        stats_layout.addWidget(self.lbl_tiempo, 1, 1)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        # Conectar señales
        self.btn_iniciar.clicked.connect(self.iniciar_proceso)
        self.btn_detener.clicked.connect(self.detener_proceso)
        self.btn_reiniciar.clicked.connect(self.reiniciar_proceso)
    
    def configurar_timer_estadisticas(self):
        """Configura el timer para actualizar estadísticas."""
        self.timer_estadisticas = QTimer()
        self.timer_estadisticas.timeout.connect(self.actualizar_estadisticas_ui)
        self.timer_estadisticas.setInterval(1000)  # Actualizar cada segundo
    
    def configurar_estilos(self):
        """Configura los estilos del panel."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {self.color_acento};
                border-radius: 10px;
                padding: 10px;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QPushButton {{
                background-color: {self.color_acento};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self._oscurecer_color(self.color_acento)};
            }}
            QPushButton:disabled {{
                background-color: #cbd5e0;
                color: #718096;
            }}
            QProgressBar {{
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background-color: #f7fafc;
            }}
            QProgressBar::chunk {{
                background-color: {self.color_acento};
                border-radius: 3px;
            }}
        """)
    
    def _oscurecer_color(self, color: str) -> str:
        """Oscurece un color para efectos hover."""
        color_map = {
            "#4299e1": "#3182ce",
            "#48bb78": "#38a169",
            "#ed8936": "#dd6b20",
            "#9f7aea": "#805ad5"
        }
        return color_map.get(color, color)
    
    def iniciar_proceso(self):
        """Inicia el proceso de automatización."""
        if self.activo:
            return
        
        try:
            # Configurar hilo según el contexto
            if self.contexto == "pacientes":
                self.hilo_proceso = HiloProcesadorPacientes(self.controlador)
            elif self.contexto == "casos":
                self.hilo_proceso = HiloProcesadorCasos(self.controlador)
            else:
                return
            
            # Crear configuración usando valores por defecto y datos de la UI
            configuracion_base = ConfiguracionAutomatizacion()  # Valores por defecto
            
            # Aplicar configuraciones de la UI
            config_dict = {
                "modo": self.combo_modo.currentText(),
                "reintentos": self.spin_reintentos.value(),
                "headless": self.check_headless.isChecked(),
                "captcha_auto": self.check_captcha.isChecked(),
                # Usar credenciales por defecto de ConfiguracionAutomatizacion
                "url_login": configuracion_base.url_login,  # https://portalsalud.coosalud.com/login
                "usuario": configuracion_base.usuario,      # biomedips@gmail.com
                "password": configuracion_base.password     # Caucasia1+
            }
            self.hilo_proceso.configurar_proceso(config_dict)
            
            # Conectar señales
            self.hilo_proceso.proceso_iniciado.connect(self.al_proceso_iniciado)
            self.hilo_proceso.progreso_actualizado.connect(self.al_progreso_actualizado)
            self.hilo_proceso.proceso_terminado.connect(self.al_proceso_terminado)
            
            # Iniciar
            self.hilo_proceso.start()
            
            # Actualizar UI
            self.activo = True
            self.btn_iniciar.setEnabled(False)
            self.btn_detener.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Inicializar estadísticas
            self.estadisticas["tiempo_inicio"] = datetime.now()
            self.timer_estadisticas.start()
            
            # Emitir señal
            self.proceso_iniciado.emit(self.contexto)
            
        except Exception as e:
            self.mostrar_error(f"Error al iniciar proceso: {e}")
    
    def detener_proceso(self):
        """Detiene el proceso de automatización."""
        if self.hilo_proceso and self.hilo_proceso.isRunning():
            self.hilo_proceso.detener_proceso()
            self.hilo_proceso.wait(3000)  # Esperar hasta 3 segundos
        
        self.al_proceso_terminado(self.contexto, False, "Detenido por usuario")
        self.proceso_detenido.emit(self.contexto)
    
    def reiniciar_proceso(self):
        """Reinicia el proceso de automatización."""
        if self.activo:
            self.detener_proceso()
        
        # Limpiar estadísticas
        self.limpiar_estadisticas()
        
        # Iniciar nuevamente
        self.iniciar_proceso()
    
    def limpiar_estadisticas(self):
        """Limpia las estadísticas del panel."""
        self.estadisticas = {
            "procesados": 0,
            "exitosos": 0,
            "errores": 0,
            "tiempo_inicio": None
        }
        self.actualizar_labels_estadisticas()
    
    def actualizar_labels_estadisticas(self):
        """Actualiza los labels de estadísticas."""
        self.lbl_procesados.setText(f"Procesados: {self.estadisticas['procesados']}")
        self.lbl_exitosos.setText(f"Exitosos: {self.estadisticas['exitosos']}")
        self.lbl_errores.setText(f"Errores: {self.estadisticas['errores']}")
        
        # Calcular tiempo transcurrido
        if self.estadisticas["tiempo_inicio"]:
            tiempo_transcurrido = datetime.now() - self.estadisticas["tiempo_inicio"]
            minutos = int(tiempo_transcurrido.total_seconds() // 60)
            segundos = int(tiempo_transcurrido.total_seconds() % 60)
            self.lbl_tiempo.setText(f"Tiempo: {minutos:02d}:{segundos:02d}")
        else:
            self.lbl_tiempo.setText("Tiempo: 00:00")
    
    def actualizar_estadisticas_ui(self):
        """Actualiza las estadísticas en la UI."""
        try:
            # Obtener estadísticas del controlador
            stats = self.controlador.obtener_estadisticas()
            if self.contexto in stats:
                contexto_stats = stats[self.contexto]
                self.estadisticas["procesados"] = contexto_stats.get("procesados", 0)
                self.estadisticas["exitosos"] = contexto_stats.get("exitosos", 0)
                self.estadisticas["errores"] = contexto_stats.get("errores", 0)
            
            self.actualizar_labels_estadisticas()
            
        except Exception:
            # Si hay error obteniendo stats, mantener las locales
            self.actualizar_labels_estadisticas()
    
    def al_proceso_iniciado(self, contexto: str):
        """Maneja el inicio del proceso."""
        self.lbl_estado.setText("▶️ Ejecutando")
        self.lbl_estado.setStyleSheet(f"color: {self.color_acento};")
    
    def al_progreso_actualizado(self, contexto: str, porcentaje: int):
        """Actualiza el progreso del proceso."""
        if contexto == self.contexto:
            self.progress_bar.setValue(porcentaje)
    
    def al_proceso_terminado(self, contexto: str, exito: bool, mensaje: str):
        """Maneja la finalización del proceso."""
        if contexto == self.contexto:
            self.activo = False
            self.btn_iniciar.setEnabled(True)
            self.btn_detener.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.timer_estadisticas.stop()
            
            if exito:
                self.lbl_estado.setText("✅ Completado")
                self.lbl_estado.setStyleSheet("color: #38a169;")
            else:
                self.lbl_estado.setText("❌ Error")
                self.lbl_estado.setStyleSheet("color: #e53e3e;")
    
    def mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error."""
        QMessageBox.critical(self, "Error", mensaje)
    
    def obtener_configuracion_actual(self) -> Dict[str, Any]:
        """Obtiene la configuración actual del panel."""
        return {
            "modo": self.combo_modo.currentText(),
            "reintentos": self.spin_reintentos.value(),
            "headless": self.check_headless.isChecked(),
            "captcha_auto": self.check_captcha.isChecked()
        }


class PanelLogs(QFrame):
    """Panel de logs con pestañas por contexto."""
    
    def __init__(self):
        super().__init__()
        self.logs_content = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del panel de logs optimizada."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Header compacto
        header_layout = QHBoxLayout()
        
        titulo = QLabel("📋 Logs de Automatización")
        titulo.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(titulo)
        
        header_layout.addStretch()
        
        # Botón limpiar más pequeño
        btn_limpiar = QPushButton("🧹 Limpiar")
        btn_limpiar.setMaximumHeight(25)
        btn_limpiar.setMaximumWidth(80)
        btn_limpiar.clicked.connect(self.limpiar_logs)
        header_layout.addWidget(btn_limpiar)
        
        layout.addLayout(header_layout)
        
        # Tabs de logs que usen todo el espacio disponible
        self.tabs_logs = QTabWidget()
        # Sin restricción de altura máxima para usar todo el espacio
        
        # Tab general
        self.log_general = QPlainTextEdit()
        self.configurar_log_widget(self.log_general)
        self.tabs_logs.addTab(self.log_general, "🌐 General")
        self.logs_content["general"] = self.log_general
        
        # Tab pacientes
        self.log_pacientes = QPlainTextEdit()
        self.configurar_log_widget(self.log_pacientes)
        self.tabs_logs.addTab(self.log_pacientes, "👥 Pacientes")
        self.logs_content["pacientes"] = self.log_pacientes
        
        # Tab casos
        self.log_casos = QPlainTextEdit()
        self.configurar_log_widget(self.log_casos)
        self.tabs_logs.addTab(self.log_casos, "📋 Casos")
        self.logs_content["casos"] = self.log_casos
        
        layout.addWidget(self.tabs_logs)
        
        self.configurar_estilos()
    
    def configurar_log_widget(self, widget: QPlainTextEdit):
        """Configura un widget de log optimizado."""
        widget.setReadOnly(True)
        widget.setMaximumBlockCount(500)  # Limitar líneas para mejor rendimiento
        widget.setFont(QFont("Consolas", 8))  # Fuente más pequeña
        widget.setLineWrapMode(QPlainTextEdit.WidgetWidth)  # Wrap automático
    
    def configurar_estilos(self):
        """Configura los estilos del panel de logs con tema coherente."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QPlainTextEdit {
                background-color: #fafbfc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 8px;
                line-height: 1.2;
                color: #2d3748;
            }
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
    
    def agregar_log(self, mensaje: str, nivel: str = "info", contexto: str = "general"):
        """Agrega un log al panel correspondiente."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Formatear mensaje
        nivel_icon = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅"
        }.get(nivel, "📝")
        
        log_line = f"[{timestamp}] {nivel_icon} {mensaje}"
        
        # Agregar a log general
        self.logs_content["general"].appendPlainText(log_line)
        
        # Agregar a log específico si existe
        if contexto in self.logs_content:
            self.logs_content[contexto].appendPlainText(log_line)
        
        # Auto-scroll al final
        for widget in self.logs_content.values():
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.End)
            widget.setTextCursor(cursor)
    
    def limpiar_logs(self):
        """Limpia todos los logs."""
        for widget in self.logs_content.values():
            widget.clear()


class InterfazAutomatizacionDual(QWidget):
    """Interfaz principal de automatización dual con lógica real."""
    
    def __init__(self):
        super().__init__()
        self.manejador_logs = ManejadorLogs()
        self.controlador = ControladorAutomatizacionPrincipal()
        self.configurar_interfaz()
        self.configurar_conexiones()
    
    def configurar_interfaz(self):
        """Configura la interfaz principal responsiva."""
        self.setWindowTitle("🤖 Automatización Dual - Coosalud")
        self.setMinimumSize(1200, 700)
        self.resize(1600, 900)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Splitter principal (vertical) con distribución optimizada
        self.main_splitter = QSplitter(Qt.Vertical)
        
        # Panel superior - Controles de automatización (más compacto)
        controles_splitter = QSplitter(Qt.Horizontal)
        
        # Panel de pacientes
        self.panel_pacientes = PanelControlAutomatizacion(
            "pacientes", 
            "👥 Pacientes", 
            "#4299e1",
            self.controlador
        )
        controles_splitter.addWidget(self.panel_pacientes)
        
        # Panel de casos
        self.panel_casos = PanelControlAutomatizacion(
            "casos", 
            "📋 Casos", 
            "#48bb78",
            self.controlador
        )
        controles_splitter.addWidget(self.panel_casos)
        
        # Configurar tamaños iguales
        controles_splitter.setSizes([600, 600])
        self.main_splitter.addWidget(controles_splitter)
        
        # Panel inferior - Logs (más espacio)
        self.panel_logs = PanelLogs()
        self.main_splitter.addWidget(self.panel_logs)
        
        # Configurar distribución: más espacio para logs
        self.main_splitter.setSizes([250, 750])  # 25% controles, 75% logs
        self.main_splitter.setStretchFactor(0, 0)  # No expandir controles
        self.main_splitter.setStretchFactor(1, 1)  # Expandir logs
        
        main_layout.addWidget(self.main_splitter)
        
        self.aplicar_estilos_generales()
    
    def quitar_header_interno(self):
        """Quita el header interno cuando se usa dentro de otra ventana."""
        # No hay header interno en esta versión
        pass
    
    def configurar_conexiones(self):
        """Configura las conexiones de señales."""
        # Conectar logs
        self.manejador_logs.log_recibido.connect(self.panel_logs.agregar_log)
        
        # Conectar procesos
        self.panel_pacientes.proceso_iniciado.connect(self.al_proceso_iniciado)
        self.panel_pacientes.proceso_detenido.connect(self.al_proceso_detenido)
        self.panel_casos.proceso_iniciado.connect(self.al_proceso_iniciado)
        self.panel_casos.proceso_detenido.connect(self.al_proceso_detenido)
        
        # Conectar logs de hilos
        self.conectar_logs_hilos()
    
    def conectar_logs_hilos(self):
        """Conecta los logs de los hilos al panel de logs."""
        # Los hilos se conectan automáticamente cuando se crean
        pass
    
    def al_proceso_iniciado(self, contexto: str):
        """Maneja el inicio de un proceso."""
        self.manejador_logs.emitir_log(f"🚀 Proceso {contexto} iniciado", "info", contexto)
        
        # Conectar logs del hilo específico
        if contexto == "pacientes" and hasattr(self.panel_pacientes, 'hilo_proceso'):
            if self.panel_pacientes.hilo_proceso:
                self.panel_pacientes.hilo_proceso.log_emitido.connect(self.panel_logs.agregar_log)
        elif contexto == "casos" and hasattr(self.panel_casos, 'hilo_proceso'):
            if self.panel_casos.hilo_proceso:
                self.panel_casos.hilo_proceso.log_emitido.connect(self.panel_logs.agregar_log)
    
    def al_proceso_detenido(self, contexto: str):
        """Maneja la detención de un proceso."""
        self.manejador_logs.emitir_log(f"⏹️ Proceso {contexto} detenido", "warning", contexto)
    
    def aplicar_estilos_generales(self):
        """Aplica estilos generales a la ventana con paleta de colores coherente."""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                color: #2d3748;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                margin: 3px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 11px;
                color: #4a5568;
                background-color: #f7fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2d3748;
            }
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 10px;
                min-width: 70px;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:disabled {
                background-color: #e2e8f0;
                color: #a0aec0;
            }
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                background-color: #f7fafc;
                font-size: 10px;
                color: #4a5568;
            }
            QSplitter::handle {
                background-color: #cbd5e0;
                width: 2px;
                height: 2px;
                border-radius: 1px;
                margin: 1px;
            }
            QSplitter::handle:hover {
                background-color: #a0aec0;
            }
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                padding: 6px 12px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: bold;
                color: #4a5568;
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #2d3748;
            }
            QTabBar::tab:hover {
                background-color: #edf2f7;
            }
            QComboBox, QSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 3px;
                padding: 4px 8px;
                background-color: white;
                font-size: 10px;
                color: #2d3748;
            }
            QComboBox:hover, QSpinBox:hover {
                border-color: #cbd5e0;
            }
            QCheckBox {
                font-size: 10px;
                color: #4a5568;
            }
            QCheckBox::indicator:checked {
                background-color: #48bb78;
                border: 1px solid #38a169;
            }
            QLabel {
                font-size: 10px;
                color: #4a5568;
            }
        """)
    
    def redimensionar_ventana(self, event):
        """Maneja el redimensionamiento de la ventana para responsividad."""
        super().resizeEvent(event)
        
        # Ajustar distribución según el tamaño de la ventana
        width = self.width()
        height = self.height()
        
        # Para pantallas muy pequeñas, cambiar el layout
        if hasattr(self, 'main_splitter'):
            if width < 1000:
                # En pantallas pequeñas, dar más espacio a los logs
                self.main_splitter.setSizes([200, 600])
            elif height < 700:
                # En pantallas bajas, comprimir más los controles
                self.main_splitter.setSizes([220, 580])
            else:
                # Distribución normal
                self.main_splitter.setSizes([250, 750])
    
    def mostrar_mensaje(self, titulo: str, mensaje: str, tipo: str = "info"):
        """Muestra un mensaje al usuario."""
        if tipo == "error":
            QMessageBox.critical(self, titulo, mensaje)
        elif tipo == "warning":
            QMessageBox.warning(self, titulo, mensaje)
        else:
            QMessageBox.information(self, titulo, mensaje)
    
    def obtener_configuracion_completa(self) -> Dict[str, Any]:
        """Obtiene la configuración completa de ambos paneles."""
        return {
            "pacientes": self.panel_pacientes.obtener_configuracion_actual(),
            "casos": self.panel_casos.obtener_configuracion_actual()
        }
    
    def obtener_estado_sistema(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema."""
        return self.controlador.obtener_estado_sistema()
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema."""
        return self.controlador.obtener_estadisticas()
    
    async def detener_todos_los_procesos(self):
        """Detiene todos los procesos activos."""
        try:
            await self.controlador.detener_todos_los_procesos()
            self.manejador_logs.emitir_log("🛑 Todos los procesos detenidos", "info", "sistema")
        except Exception as e:
            self.manejador_logs.emitir_log(f"❌ Error deteniendo procesos: {e}", "error", "sistema")
    
    def ejecutar_automatizacion_dual(self):
        """Ejecuta ambos procesos en paralelo."""
        try:
            # Iniciar ambos procesos
            if not self.panel_pacientes.activo:
                self.panel_pacientes.iniciar_proceso()
            
            if not self.panel_casos.activo:
                self.panel_casos.iniciar_proceso()
                
            self.manejador_logs.emitir_log("🔄 Automatización dual iniciada", "info", "sistema")
            
        except Exception as e:
            self.mostrar_mensaje("Error", f"Error iniciando automatización dual: {e}", "error")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        try:
            # Detener procesos activos
            if hasattr(self.panel_pacientes, 'activo') and self.panel_pacientes.activo:
                self.panel_pacientes.detener_proceso()
            
            if hasattr(self.panel_casos, 'activo') and self.panel_casos.activo:
                self.panel_casos.detener_proceso()
            
            # Limpiar recursos del controlador
            asyncio.create_task(self.controlador.limpiar_recursos())
            
            event.accept()
            
        except Exception as e:
            self.manejador_logs.emitir_log(f"❌ Error cerrando aplicación: {e}", "error", "sistema")
            event.accept()


    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana para responsividad."""
        self.redimensionar_ventana(event)


# Función de conveniencia para reemplazar la ventana actual
def crear_interfaz_automatizacion() -> InterfazAutomatizacionDual:
    """Crea y retorna la nueva interfaz de automatización integrada."""
    return InterfazAutomatizacionDual()