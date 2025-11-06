"""
Ventana principal de la aplicación con menú y navegación.
"""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QStatusBar, QStackedWidget, QLabel,
    QMessageBox, QDialog
)
from PySide6.QtCore import Qt, QTimer, QTimer
from PySide6.QtGui import QIcon, QAction
from src.core.config import config
from src.license.license_manager import LicenseManager, LicenseException
from src.ui.license_dialog import LicenseDialog
from src.ui.pages.home_page import HomePage
from src.ui.pages.api_page import ApiPage
from src.ui.pages.playwright_page import PlaywrightPage
from src.ui.pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Inicializar gestor de licencias
        try:
            self.license_manager = LicenseManager()
        except LicenseException as e:
            QMessageBox.critical(
                None, "Error de Configuración", 
                f"Error configurando sistema de licencias: {e}\\n\\n"
                "Verifique la configuración del servidor de licencias en el archivo .env"
            )
            return
        
        # Flag para evitar diálogos de licencia duplicados
        self._license_dialog_open = False
        
        self.setup_window()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Verificar licencia después de configurar la UI
        self.check_license_on_startup()
        
        self.logger.info("Ventana principal inicializada")
    
    def setup_window(self):
        """Configura las propiedades básicas de la ventana."""
        self.setWindowTitle(f"{config.get('app.name')} v{config.get('app.version')}")
        self.setGeometry(100, 100, 
                        config.get('ui.window_width'), 
                        config.get('ui.window_height'))
        
        # Aplicar tema si está configurado
        if config.get('ui.theme') == 'dark':
            self.apply_dark_theme()
    
    def setup_ui(self):
        """Configura la interfaz de usuario principal."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Stack de páginas
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Crear páginas
        self.home_page = HomePage(self.license_manager)  # Pasar la instancia
        self.api_page = ApiPage()
        self.playwright_page = PlaywrightPage()
        self.settings_page = SettingsPage()
        
        # Añadir páginas al stack
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.api_page)
        self.stacked_widget.addWidget(self.playwright_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        # Mostrar página de inicio por defecto
        self.stacked_widget.setCurrentWidget(self.home_page)
    
    def setup_menu(self):
        """Configura el menú de la aplicación."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('&Archivo')
        
        # Acción Salir
        exit_action = QAction('&Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Navegación
        nav_menu = menubar.addMenu('&Navegación')
        
        # Acción Inicio
        home_action = QAction('&Inicio', self)
        home_action.setShortcut('Ctrl+H')
        home_action.triggered.connect(lambda: self.show_page(self.home_page))
        nav_menu.addAction(home_action)
        
        # Acción API
        api_action = QAction('&API', self)
        api_action.setShortcut('Ctrl+A')
        api_action.triggered.connect(lambda: self.show_page(self.api_page))
        nav_menu.addAction(api_action)
        
        # Acción Playwright
        playwright_action = QAction('&Playwright', self)
        playwright_action.setShortcut('Ctrl+P')
        playwright_action.triggered.connect(lambda: self.show_page(self.playwright_page))
        nav_menu.addAction(playwright_action)
        
        nav_menu.addSeparator()
        
        # Acción Configuración
        settings_action = QAction('&Configuración', self)
        settings_action.setShortcut('Ctrl+S')
        settings_action.triggered.connect(lambda: self.show_page(self.settings_page))
        nav_menu.addAction(settings_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('&Herramientas')
        
        # Acción Verificar Licencia
        check_license_action = QAction('&Verificar Licencia', self)
        check_license_action.triggered.connect(self.check_license_manual)
        tools_menu.addAction(check_license_action)
        
        # Acción Gestionar Licencia
        manage_license_action = QAction('&Gestionar Licencia', self)
        manage_license_action.triggered.connect(self.show_license_dialog)
        tools_menu.addAction(manage_license_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('&Ayuda')
        
        # Acción Acerca de
        about_action = QAction('&Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Configura la barra de estado."""
        self.status_bar = self.statusBar()
        
        # Label de estado de licencia
        self.license_status_label = QLabel("Verificando licencia...")
        self.status_bar.addPermanentWidget(self.license_status_label)
        
        # Label de estado general
        self.status_bar.showMessage("Listo")
    
    def show_page(self, page):
        """Muestra una página específica."""
        self.stacked_widget.setCurrentWidget(page)
        page_name = page.__class__.__name__.replace('Page', '')
        self.status_bar.showMessage(f"Página actual: {page_name}")
        self.logger.debug(f"Navegando a página: {page_name}")
        
        # Si es la página de inicio, actualizar información de licencia
        if page == self.home_page:
            QTimer.singleShot(100, self.home_page.refresh_license_info)
    
    def check_license_on_startup(self):
        """Verifica la licencia al iniciar la aplicación."""
        self.logger.info("Verificando licencia al iniciar...")
        
        try:
            # Verificar si ya existe una licencia activa para este hardware
            license_check = self.license_manager.check_existing_license()
            
            if license_check.get('has_license'):
                # Hay licencia activa
                license_data = license_check.get('license_data', {})
                client_name = license_data.get('client_name', 'Usuario')
                license_key = license_data.get('license_key', '')
                status = license_data.get('status', 'unknown')
                
                self.logger.info(f"Licencia activa encontrada: {license_key} para {client_name}")
                
                # Verificar si la licencia está expirada
                if status.lower() == 'expired':
                    self.logger.warning("Licencia encontrada pero expirada")
                    self.show_license_dialog("expired")
                    return
                elif status.lower() != 'active':
                    self.logger.warning(f"Licencia encontrada pero con estado: {status}")
                    self.show_license_dialog("invalid")
                    return
                
                # Licencia activa y válida - continuar con la aplicación
                self.update_license_status(show_dialog_on_error=False)
                self.logger.info("Aplicación iniciada con licencia válida")
                
                # Actualizar dashboard después de un breve delay
                QTimer.singleShot(1500, self.home_page.refresh_license_info)
                
                # Mostrar mensaje de bienvenida discreto en la barra de estado
                self.status_bar.showMessage(f"Bienvenido {client_name} - Licencia activa", 3000)
                return
                
            else:
                # No hay licencia activa
                error_type = license_check.get('error_type')
                message = license_check.get('message', 'No se encontró licencia')
                
                if error_type == 'connection_error':
                    # Error de conexión - verificar si hay licencia local
                    self.logger.warning(f"Error de conexión: {message}")
                    try:
                        if self.license_manager.is_valid(check_api=False):
                            # Hay licencia local válida, trabajar en modo offline
                            self.update_license_status(show_dialog_on_error=False)
                            self.status_bar.showMessage("Trabajando en modo offline", 5000)
                            return
                    except:
                        pass
                
                # No hay licencia válida, mostrar diálogo
                self.logger.info("No se encontró licencia válida, mostrando diálogo")
                self.show_license_dialog("first_time")
                
        except Exception as e:
            self.logger.error(f"Error verificando licencia al iniciar: {e}")
            # En caso de error, mostrar diálogo como fallback
            self.show_license_dialog("first_time")
    
    def check_license_manual(self):
        """Verifica manualmente el estado de la licencia."""
        self.update_license_status(show_dialog_on_error=True)
    
    def update_license_status(self, show_dialog_on_error=True):
        """
        Actualiza el estado de la licencia en la UI.
        
        Args:
            show_dialog_on_error: Si False, no muestra diálogos automáticamente
        """
        try:
            # Verificar licencia con API (True para consultar API en tiempo real)
            if self.license_manager.is_valid(check_api=True):
                license_info = self.license_manager.get_license_info()
                
                if license_info.get('valid'):
                    client_name = license_info.get('client_name', 'Usuario')
                    license_key = license_info.get('license_key', '')
                    features = license_info.get('features', [])
                    status = license_info.get('status', 'unknown')
                    
                    # Mostrar información completa de la licencia
                    status_text = f"✓ {client_name} - {license_key} - {status.upper()}"
                    if features:
                        status_text += f" - Características: {', '.join(features)}"
                    
                    self.license_status_label.setText(status_text)
                    self.license_status_label.setStyleSheet("color: green;")
                    
                    # Verificar días restantes si está disponible
                    days_remaining = license_info.get('days_remaining', None)
                    if days_remaining is not None:
                        if days_remaining <= 7:
                            self.license_status_label.setStyleSheet("color: orange;")
                            if days_remaining <= 0:
                                self.license_status_label.setText("⚠️ Licencia expirada")
                                self.license_status_label.setStyleSheet("color: red;")
                                if show_dialog_on_error:
                                    self.show_license_dialog("expired")
                else:
                    self.license_status_label.setText("✗ Licencia inválida")
                    self.license_status_label.setStyleSheet("color: red;")
                    if show_dialog_on_error:
                        self.show_license_dialog("invalid")
            else:
                self.license_status_label.setText("? Sin licencia")
                self.license_status_label.setStyleSheet("color: orange;")
                if show_dialog_on_error:
                    self.show_license_dialog("first_time")
                
        except Exception as e:
            self.logger.error(f"Error verificando licencia: {e}")
            self.license_status_label.setText("⚠️ Error de conexión - Modo offline")
            self.license_status_label.setStyleSheet("color: orange;")
            # En caso de error de conexión, verificar si hay licencia local válida
            try:
                if self.license_manager.is_valid(check_api=False):
                    license_info = self.license_manager.get_license_info()
                    client_name = license_info.get('client_name', 'Usuario')
                    self.license_status_label.setText(f"⚠️ {client_name} (sin conexión)")
                    self.license_status_label.setStyleSheet("color: orange;")
            except:
                pass
    
    def show_license_dialog(self, reason="first_time"):
        """Muestra el diálogo de gestión de licencias."""
        # Evitar abrir múltiples diálogos
        if self._license_dialog_open:
            return
            
        self._license_dialog_open = True
        
        try:
            dialog = LicenseDialog(self, reason)
            result = dialog.exec()
            
            if result == QDialog.Accepted:
                # Licencia procesada exitosamente, actualizar estado SIN mostrar diálogos automáticos
                self.update_license_status(show_dialog_on_error=False)
                
                # Actualizar el dashboard si está visible
                if self.stacked_widget.currentWidget() == self.home_page:
                    QTimer.singleShot(500, self.home_page.refresh_license_info)
                
                QMessageBox.information(
                    self,
                    "¡Bienvenido a BootCasosV2!",
                    "La licencia ha sido activada correctamente.\\n\\n"
                    "¡Ya puede utilizar todas las funcionalidades de la aplicación!"
                )
            elif reason in ["expired", "invalid"]:
                # Si no se procesó la licencia y es crítico, cerrar la aplicación
                reply = QMessageBox.question(
                    self,
                    "Licencia Requerida",
                    "La aplicación requiere una licencia válida para funcionar.\\n"
                    "¿Desea intentar nuevamente o cerrar la aplicación?",
                    QMessageBox.Retry | QMessageBox.Close
                )
                
                if reply == QMessageBox.Retry:
                    self._license_dialog_open = False  # Permitir abrir nuevamente
                    self.show_license_dialog(reason)
                else:
                    self.close()
            elif reason == "first_time":
                # Primera vez, permitir cerrar sin licencia pero con advertencia
                reply = QMessageBox.question(
                    self,
                    "Sin Licencia",
                    "Sin una licencia válida, la aplicación tendrá funcionalidad limitada.\\n"
                    "¿Desea continuar de todos modos?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    self.close()
        finally:
            self._license_dialog_open = False
    
    def check_license(self):
        """Método de compatibilidad - redirige a check_license_manual."""
        self.check_license_manual()
    
    def show_license_warning(self):
        """Muestra advertencia de licencia inválida."""
        QMessageBox.warning(
            self,
            "Licencia Inválida",
            "La licencia de la aplicación no es válida o ha expirado.\\n"
            "Algunas funcionalidades pueden estar limitadas."
        )
    
    def show_about(self):
        """Muestra información sobre la aplicación."""
        QMessageBox.about(
            self,
            f"Acerca de {config.get('app.name')}",
            f"""
            <h3>{config.get('app.name')}</h3>
            <p>Versión: {config.get('app.version')}</p>
            <p>Una aplicación de escritorio construida con PySide6 y Playwright.</p>
            <p>Desarrollado con Python y tecnologías modernas.</p>
            """
        )
    
    def apply_dark_theme(self):
        """Aplica un tema oscuro a la aplicación."""
        dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background-color: #555555;
        }
        QMenu {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenu::item:selected {
            background-color: #555555;
        }
        QStatusBar {
            background-color: #3c3c3c;
            color: #ffffff;
            border-top: 1px solid #555555;
        }
        """
        self.setStyleSheet(dark_style)
    
    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.logger.info("Cerrando aplicación")
        event.accept()