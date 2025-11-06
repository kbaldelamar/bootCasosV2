"""
Página de configuración de la aplicación.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QCheckBox, QSpinBox,
    QGroupBox, QFormLayout, QComboBox, QTextEdit,
    QTabWidget, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from src.core.config import config


class SettingsPage(QWidget):
    """Página de configuración de la aplicación."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Configura la interfaz de usuario de la página de configuración."""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Configuración de la Aplicación")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Tabs para diferentes categorías de configuración
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Tab 1: Configuración general
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "General")
        
        # Tab 2: Configuración de API
        api_tab = self.create_api_tab()
        tab_widget.addTab(api_tab, "API")
        
        # Tab 3: Configuración de Playwright
        playwright_tab = self.create_playwright_tab()
        tab_widget.addTab(playwright_tab, "Playwright")
        
        # Tab 4: Configuración de licencia
        license_tab = self.create_license_tab()
        tab_widget.addTab(license_tab, "Licencia")
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)
        
        reset_button = QPushButton("Restablecer")
        reset_button.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(reset_button)
        
        buttons_layout.addStretch()
        
        reload_button = QPushButton("Recargar desde .env")
        reload_button.clicked.connect(self.reload_settings)
        buttons_layout.addWidget(reload_button)
        
        layout.addLayout(buttons_layout)
    
    def create_general_tab(self):
        """Crea el tab de configuración general."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración de la aplicación
        app_group = QGroupBox("Aplicación")
        app_layout = QFormLayout(app_group)
        
        self.app_name_input = QLineEdit()
        app_layout.addRow("Nombre:", self.app_name_input)
        
        self.debug_check = QCheckBox("Modo Debug")
        app_layout.addRow("Debug:", self.debug_check)
        
        layout.addWidget(app_group)
        
        # Configuración de UI
        ui_group = QGroupBox("Interfaz de Usuario")
        ui_layout = QFormLayout(ui_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setSuffix(" px")
        ui_layout.addRow("Ancho ventana:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        self.window_height_spin.setSuffix(" px")
        ui_layout.addRow("Alto ventana:", self.window_height_spin)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['light', 'dark'])
        ui_layout.addRow("Tema:", self.theme_combo)
        
        layout.addWidget(ui_group)
        
        # Configuración de logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        log_layout.addRow("Nivel de log:", self.log_level_combo)
        
        self.log_file_input = QLineEdit()
        log_layout.addRow("Archivo de log:", self.log_file_input)
        
        browse_log_btn = QPushButton("Examinar...")
        browse_log_btn.clicked.connect(self.browse_log_file)
        log_layout.addRow("", browse_log_btn)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        return widget
    
    def create_api_tab(self):
        """Crea el tab de configuración de API."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        api_group = QGroupBox("Configuración de API")
        api_layout = QFormLayout(api_group)
        
        self.api_base_url_input = QLineEdit()
        api_layout.addRow("URL Base:", self.api_base_url_input)
        
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setRange(5, 300)
        self.api_timeout_spin.setSuffix(" seg")
        api_layout.addRow("Timeout:", self.api_timeout_spin)
        
        self.api_retries_spin = QSpinBox()
        self.api_retries_spin.setRange(0, 10)
        api_layout.addRow("Reintentos:", self.api_retries_spin)
        
        layout.addWidget(api_group)
        
        # Test de conexión
        test_group = QGroupBox("Prueba de Conexión")
        test_layout = QVBoxLayout(test_group)
        
        test_button = QPushButton("Probar Conexión API")
        test_button.clicked.connect(self.test_api_connection)
        test_layout.addWidget(test_button)
        
        self.api_test_result = QTextEdit()
        self.api_test_result.setMaximumHeight(100)
        self.api_test_result.setReadOnly(True)
        test_layout.addWidget(self.api_test_result)
        
        layout.addWidget(test_group)
        
        layout.addStretch()
        return widget
    
    def create_playwright_tab(self):
        """Crea el tab de configuración de Playwright."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        playwright_group = QGroupBox("Configuración de Playwright")
        playwright_layout = QFormLayout(playwright_group)
        
        self.playwright_headless_check = QCheckBox("Modo Headless")
        playwright_layout.addRow("Headless:", self.playwright_headless_check)
        
        self.playwright_timeout_spin = QSpinBox()
        self.playwright_timeout_spin.setRange(5000, 120000)
        self.playwright_timeout_spin.setSuffix(" ms")
        playwright_layout.addRow("Timeout:", self.playwright_timeout_spin)
        
        layout.addWidget(playwright_group)
        
        # Instalación de navegadores
        browsers_group = QGroupBox("Navegadores")
        browsers_layout = QVBoxLayout(browsers_group)
        
        install_browsers_btn = QPushButton("Instalar Navegadores Playwright")
        install_browsers_btn.clicked.connect(self.install_playwright_browsers)
        browsers_layout.addWidget(install_browsers_btn)
        
        self.browsers_status = QTextEdit()
        self.browsers_status.setMaximumHeight(100)
        self.browsers_status.setReadOnly(True)
        browsers_layout.addWidget(self.browsers_status)
        
        layout.addWidget(browsers_group)
        
        layout.addStretch()
        return widget
    
    def create_license_tab(self):
        """Crea el tab de configuración de licencia."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        license_group = QGroupBox("Configuración de Licencia")
        license_layout = QFormLayout(license_group)
        
        self.license_server_input = QLineEdit()
        license_layout.addRow("Servidor de Licencia:", self.license_server_input)
        
        self.license_check_interval_spin = QSpinBox()
        self.license_check_interval_spin.setRange(300, 86400)
        self.license_check_interval_spin.setSuffix(" seg")
        license_layout.addRow("Intervalo de verificación:", self.license_check_interval_spin)
        
        self.license_file_input = QLineEdit()
        license_layout.addRow("Archivo de licencia:", self.license_file_input)
        
        browse_license_btn = QPushButton("Examinar...")
        browse_license_btn.clicked.connect(self.browse_license_file)
        license_layout.addRow("", browse_license_btn)
        
        layout.addWidget(license_group)
        
        # Estado de licencia
        status_group = QGroupBox("Estado de Licencia")
        status_layout = QVBoxLayout(status_group)
        
        check_license_btn = QPushButton("Verificar Licencia")
        check_license_btn.clicked.connect(self.check_license_status)
        status_layout.addWidget(check_license_btn)
        
        self.license_status = QTextEdit()
        self.license_status.setMaximumHeight(100)
        self.license_status.setReadOnly(True)
        status_layout.addWidget(self.license_status)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """Carga la configuración actual en los campos del formulario."""
        # General
        self.app_name_input.setText(config.get('app.name', ''))
        self.debug_check.setChecked(config.get('app.debug', False))
        
        # UI
        self.window_width_spin.setValue(config.get('ui.window_width', 1200))
        self.window_height_spin.setValue(config.get('ui.window_height', 800))
        theme = config.get('ui.theme', 'dark')
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Logging
        log_level = config.get('logging.level', 'INFO')
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        self.log_file_input.setText(config.get('logging.file', ''))
        
        # API
        self.api_base_url_input.setText(config.get('api.base_url', ''))
        self.api_timeout_spin.setValue(config.get('api.timeout', 30))
        self.api_retries_spin.setValue(config.get('api.retries', 3))
        
        # Playwright
        self.playwright_headless_check.setChecked(config.get('playwright.headless', True))
        self.playwright_timeout_spin.setValue(config.get('playwright.timeout', 30000))
        
        # License
        self.license_server_input.setText(config.get('license.server_url', ''))
        self.license_check_interval_spin.setValue(config.get('license.check_interval', 3600))
        self.license_file_input.setText(config.get('license.file_path', ''))
    
    def save_settings(self):
        """Guarda la configuración actual."""
        try:
            # Actualizar configuración en memoria
            config.set('app.name', self.app_name_input.text())
            config.set('app.debug', self.debug_check.isChecked())
            
            config.set('ui.window_width', self.window_width_spin.value())
            config.set('ui.window_height', self.window_height_spin.value())
            config.set('ui.theme', self.theme_combo.currentText())
            
            config.set('logging.level', self.log_level_combo.currentText())
            config.set('logging.file', self.log_file_input.text())
            
            config.set('api.base_url', self.api_base_url_input.text())
            config.set('api.timeout', self.api_timeout_spin.value())
            config.set('api.retries', self.api_retries_spin.value())
            
            config.set('playwright.headless', self.playwright_headless_check.isChecked())
            config.set('playwright.timeout', self.playwright_timeout_spin.value())
            
            config.set('license.server_url', self.license_server_input.text())
            config.set('license.check_interval', self.license_check_interval_spin.value())
            config.set('license.file_path', self.license_file_input.text())
            
            QMessageBox.information(self, "Configuración", "Configuración guardada exitosamente.")
            self.logger.info("Configuración guardada")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar configuración: {e}")
            self.logger.error(f"Error guardando configuración: {e}")
    
    def reset_settings(self):
        """Restablece la configuración a los valores por defecto."""
        reply = QMessageBox.question(
            self, "Restablecer", 
            "¿Está seguro de que desea restablecer toda la configuración?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            config.reload()
            self.load_settings()
            QMessageBox.information(self, "Configuración", "Configuración restablecida.")
    
    def reload_settings(self):
        """Recarga la configuración desde el archivo .env"""
        config.reload()
        self.load_settings()
        QMessageBox.information(self, "Configuración", "Configuración recargada desde .env")
    
    def browse_log_file(self):
        """Examina para seleccionar archivo de log."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Seleccionar archivo de log", "", "Log files (*.log);;All files (*.*)"
        )
        if file_path:
            self.log_file_input.setText(file_path)
    
    def browse_license_file(self):
        """Examina para seleccionar archivo de licencia."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de licencia", "", "License files (*.dat *.lic);;All files (*.*)"
        )
        if file_path:
            self.license_file_input.setText(file_path)
    
    def test_api_connection(self):
        """Prueba la conexión con la API."""
        self.api_test_result.setText("Probando conexión...")
        # TODO: Implementar test real de API
        self.api_test_result.setText("Conexión exitosa (simulado)")
    
    def install_playwright_browsers(self):
        """Instala los navegadores de Playwright."""
        self.browsers_status.setText("Instalando navegadores...")
        # TODO: Implementar instalación real
        self.browsers_status.setText("Navegadores instalados exitosamente (simulado)")
    
    def check_license_status(self):
        """Verifica el estado de la licencia."""
        self.license_status.setText("Verificando licencia...")
        # TODO: Implementar verificación real de licencia
        self.license_status.setText("Licencia válida (simulado)")