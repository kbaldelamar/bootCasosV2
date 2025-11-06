"""
Página para gestión de API y recursos remotos.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from src.api.api_client import ApiClient


class ApiWorker(QThread):
    """Worker thread para llamadas a la API."""
    
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, method, url, data=None):
        super().__init__()
        self.method = method
        self.url = url
        self.data = data
        self.api_client = ApiClient()
    
    def run(self):
        """Ejecuta la llamada a la API en un hilo separado."""
        try:
            if self.method == 'GET':
                result = self.api_client.get(self.url)
            elif self.method == 'POST':
                result = self.api_client.post(self.url, self.data)
            elif self.method == 'PUT':
                result = self.api_client.put(self.url, self.data)
            elif self.method == 'DELETE':
                result = self.api_client.delete(self.url)
            else:
                raise ValueError(f"Método HTTP no soportado: {self.method}")
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ApiPage(QWidget):
    """Página para testing y gestión de APIs."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.api_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario de la página de API."""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Gestión de API")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Panel izquierdo - Configuración de la solicitud
        request_group = QGroupBox("Configuración de Solicitud")
        request_layout = QFormLayout(request_group)
        
        # Método HTTP
        self.method_combo = QComboBox()
        self.method_combo.addItems(['GET', 'POST', 'PUT', 'DELETE'])
        request_layout.addRow("Método:", self.method_combo)
        
        # URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.ejemplo.com/endpoint")
        request_layout.addRow("URL:", self.url_input)
        
        # Headers
        self.headers_text = QTextEdit()
        self.headers_text.setMaximumHeight(100)
        self.headers_text.setPlaceholderText('{"Content-Type": "application/json"}')
        request_layout.addRow("Headers:", self.headers_text)
        
        # Body
        self.body_text = QTextEdit()
        self.body_text.setMaximumHeight(150)
        self.body_text.setPlaceholderText('{"key": "value"}')
        request_layout.addRow("Body:", self.body_text)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Enviar Solicitud")
        self.send_button.clicked.connect(self.send_request)
        buttons_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self.clear_fields)
        buttons_layout.addWidget(self.clear_button)
        
        request_layout.addRow(buttons_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        request_layout.addRow(self.progress_bar)
        
        splitter.addWidget(request_group)
        
        # Panel derecho - Respuesta
        response_group = QGroupBox("Respuesta")
        response_layout = QVBoxLayout(response_group)
        
        # Status y headers de respuesta
        self.response_status = QLabel("Estado: Esperando solicitud...")
        response_layout.addWidget(self.response_status)
        
        # Cuerpo de la respuesta
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        response_layout.addWidget(self.response_text)
        
        splitter.addWidget(response_group)
        
        # Configurar proporción del splitter
        splitter.setSizes([400, 600])
    
    def send_request(self):
        """Envía la solicitud HTTP."""
        method = self.method_combo.currentText()
        url = self.url_input.text().strip()
        
        if not url:
            self.show_error("La URL es requerida")
            return
        
        # Preparar datos
        data = None
        if method in ['POST', 'PUT'] and self.body_text.toPlainText().strip():
            try:
                import json
                data = json.loads(self.body_text.toPlainText())
            except json.JSONDecodeError:
                self.show_error("El cuerpo de la solicitud no es JSON válido")
                return
        
        # Configurar UI para solicitud en progreso
        self.send_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progreso indeterminado
        self.response_status.setText("Estado: Enviando solicitud...")
        self.response_text.clear()
        
        # Crear y ejecutar worker
        self.api_worker = ApiWorker(method, url, data)
        self.api_worker.finished.connect(self.on_request_finished)
        self.api_worker.error.connect(self.on_request_error)
        self.api_worker.start()
    
    def on_request_finished(self, result):
        """Maneja la finalización exitosa de la solicitud."""
        import json
        
        # Restaurar UI
        self.send_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Mostrar respuesta
        status_code = result.get('status_code', 'N/A')
        self.response_status.setText(f"Estado: {status_code} - Solicitud completada")
        
        # Formatear respuesta JSON
        try:
            formatted_response = json.dumps(result, indent=2, ensure_ascii=False)
            self.response_text.setPlainText(formatted_response)
        except Exception:
            self.response_text.setPlainText(str(result))
        
        self.logger.info(f"Solicitud API completada con estado: {status_code}")
    
    def on_request_error(self, error_message):
        """Maneja errores en la solicitud."""
        # Restaurar UI
        self.send_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Mostrar error
        self.response_status.setText(f"Estado: Error - {error_message}")
        self.response_text.setPlainText(f"Error: {error_message}")
        
        self.logger.error(f"Error en solicitud API: {error_message}")
    
    def show_error(self, message):
        """Muestra un mensaje de error."""
        self.response_status.setText(f"Estado: Error - {message}")
        self.response_text.setPlainText(f"Error: {message}")
    
    def clear_fields(self):
        """Limpia todos los campos del formulario."""
        self.url_input.clear()
        self.headers_text.clear()
        self.body_text.clear()
        self.response_text.clear()
        self.response_status.setText("Estado: Esperando solicitud...")
        self.method_combo.setCurrentText('GET')