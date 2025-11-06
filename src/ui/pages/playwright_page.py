"""
Página para funcionalidades de Playwright y automatización web.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QLineEdit, QCheckBox,
    QGroupBox, QFormLayout, QComboBox, QSpinBox,
    QProgressBar, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QThread, Signal


class PlaywrightWorker(QThread):
    """Worker thread para operaciones de Playwright."""
    
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, action, url, script=None, options=None):
        super().__init__()
        self.action = action
        self.url = url
        self.script = script
        self.options = options or {}
    
    def run(self):
        """Ejecuta la acción de Playwright en un hilo separado."""
        try:
            from playwright.sync_api import sync_playwright
            
            self.progress.emit("Iniciando navegador...")
            
            with sync_playwright() as p:
                # Configurar navegador
                browser = p.chromium.launch(
                    headless=self.options.get('headless', True)
                )
                page = browser.new_page()
                
                if self.action == 'navigate':
                    self.progress.emit(f"Navegando a {self.url}")
                    page.goto(self.url)
                    title = page.title()
                    content = page.content()
                    result = f"Título: {title}\\n\\nContenido HTML:\\n{content[:1000]}..."
                    
                elif self.action == 'screenshot':
                    self.progress.emit(f"Tomando captura de {self.url}")
                    page.goto(self.url)
                    screenshot_path = "screenshot.png"
                    page.screenshot(path=screenshot_path)
                    result = f"Captura guardada en: {screenshot_path}"
                    
                elif self.action == 'extract_text':
                    self.progress.emit(f"Extrayendo texto de {self.url}")
                    page.goto(self.url)
                    text = page.inner_text('body')
                    result = f"Texto extraído:\\n{text[:2000]}..."
                    
                elif self.action == 'custom_script':
                    self.progress.emit(f"Ejecutando script en {self.url}")
                    page.goto(self.url)
                    # Ejecutar script personalizado
                    eval_result = page.evaluate(self.script)
                    result = f"Resultado del script:\\n{eval_result}"
                
                browser.close()
                self.finished.emit(result)
                
        except Exception as e:
            self.error.emit(str(e))


class PlaywrightPage(QWidget):
    """Página para automatización web con Playwright."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.playwright_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario de la página de Playwright."""
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Automatización Web con Playwright")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Tabs para diferentes funcionalidades
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Tab 1: Navegación básica
        nav_tab = self.create_navigation_tab()
        tab_widget.addTab(nav_tab, "Navegación")
        
        # Tab 2: Extracción de datos
        extract_tab = self.create_extraction_tab()
        tab_widget.addTab(extract_tab, "Extracción")
        
        # Tab 3: Scripts personalizados
        script_tab = self.create_script_tab()
        tab_widget.addTab(script_tab, "Scripts")
        
        # Área de resultados común
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout(results_group)
        
        # Status y progreso
        self.status_label = QLabel("Estado: Listo")
        results_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)
        
        # Área de resultados
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
    
    def create_navigation_tab(self):
        """Crea el tab de navegación básica."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # URL
        self.nav_url_input = QLineEdit()
        self.nav_url_input.setPlaceholderText("https://ejemplo.com")
        layout.addRow("URL:", self.nav_url_input)
        
        # Opciones
        self.headless_check = QCheckBox("Modo headless")
        self.headless_check.setChecked(True)
        layout.addRow("Opciones:", self.headless_check)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        navigate_btn = QPushButton("Navegar")
        navigate_btn.clicked.connect(self.navigate_to_url)
        buttons_layout.addWidget(navigate_btn)
        
        screenshot_btn = QPushButton("Captura de Pantalla")
        screenshot_btn.clicked.connect(self.take_screenshot)
        buttons_layout.addWidget(screenshot_btn)
        
        layout.addRow("Acciones:", buttons_layout)
        
        return widget
    
    def create_extraction_tab(self):
        """Crea el tab de extracción de datos."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # URL
        self.extract_url_input = QLineEdit()
        self.extract_url_input.setPlaceholderText("https://ejemplo.com")
        layout.addRow("URL:", self.extract_url_input)
        
        # Selector CSS
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("body, .content, #main")
        layout.addRow("Selector CSS:", self.selector_input)
        
        # Tipo de extracción
        self.extract_type_combo = QComboBox()
        self.extract_type_combo.addItems(['Texto completo', 'Solo texto visible', 'HTML'])
        layout.addRow("Tipo:", self.extract_type_combo)
        
        # Botón de extracción
        extract_btn = QPushButton("Extraer Datos")
        extract_btn.clicked.connect(self.extract_data)
        layout.addRow("Acción:", extract_btn)
        
        return widget
    
    def create_script_tab(self):
        """Crea el tab de scripts personalizados."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.script_url_input = QLineEdit()
        self.script_url_input.setPlaceholderText("https://ejemplo.com")
        url_layout.addWidget(self.script_url_input)
        layout.addLayout(url_layout)
        
        # Script JavaScript
        layout.addWidget(QLabel("Script JavaScript:"))
        self.script_text = QTextEdit()
        self.script_text.setPlaceholderText(
            "// Ejemplo:\\n"
            "document.title;\\n"
            "// o\\n"
            "document.querySelectorAll('a').length;"
        )
        self.script_text.setMaximumHeight(200)
        layout.addWidget(self.script_text)
        
        # Botón de ejecución
        execute_btn = QPushButton("Ejecutar Script")
        execute_btn.clicked.connect(self.execute_script)
        layout.addWidget(execute_btn)
        
        return widget
    
    def navigate_to_url(self):
        """Navega a la URL especificada."""
        url = self.nav_url_input.text().strip()
        if not url:
            self.show_error("La URL es requerida")
            return
        
        options = {'headless': self.headless_check.isChecked()}
        self.execute_playwright_action('navigate', url, options=options)
    
    def take_screenshot(self):
        """Toma una captura de pantalla de la URL."""
        url = self.nav_url_input.text().strip()
        if not url:
            self.show_error("La URL es requerida")
            return
        
        options = {'headless': True}  # Siempre headless para capturas
        self.execute_playwright_action('screenshot', url, options=options)
    
    def extract_data(self):
        """Extrae datos de la página web."""
        url = self.extract_url_input.text().strip()
        if not url:
            self.show_error("La URL es requerida")
            return
        
        self.execute_playwright_action('extract_text', url)
    
    def execute_script(self):
        """Ejecuta un script JavaScript personalizado."""
        url = self.script_url_input.text().strip()
        script = self.script_text.toPlainText().strip()
        
        if not url:
            self.show_error("La URL es requerida")
            return
        
        if not script:
            self.show_error("El script es requerido")
            return
        
        self.execute_playwright_action('custom_script', url, script=script)
    
    def execute_playwright_action(self, action, url, script=None, options=None):
        """Ejecuta una acción de Playwright en un hilo separado."""
        # Configurar UI para operación en progreso
        self.status_label.setText("Estado: Ejecutando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progreso indeterminado
        self.results_text.clear()
        
        # Crear y ejecutar worker
        self.playwright_worker = PlaywrightWorker(action, url, script, options)
        self.playwright_worker.finished.connect(self.on_operation_finished)
        self.playwright_worker.error.connect(self.on_operation_error)
        self.playwright_worker.progress.connect(self.on_operation_progress)
        self.playwright_worker.start()
    
    def on_operation_finished(self, result):
        """Maneja la finalización exitosa de la operación."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Estado: Operación completada")
        self.results_text.setPlainText(result)
        self.logger.info("Operación de Playwright completada")
    
    def on_operation_error(self, error_message):
        """Maneja errores en la operación."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Estado: Error - {error_message}")
        self.results_text.setPlainText(f"Error: {error_message}")
        self.logger.error(f"Error en operación de Playwright: {error_message}")
    
    def on_operation_progress(self, message):
        """Actualiza el progreso de la operación."""
        self.status_label.setText(f"Estado: {message}")
    
    def show_error(self, message):
        """Muestra un mensaje de error."""
        self.status_label.setText(f"Estado: Error - {message}")
        self.results_text.setPlainText(f"Error: {message}")