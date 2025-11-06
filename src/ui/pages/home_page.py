"""
Dashboard principal con información de licencia y estado del sistema.
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap
from src.core.config import config
from src.license.license_manager import LicenseManager


class HomePage(QWidget):
    """Dashboard principal con información de licencia y estado."""
    
    def __init__(self, license_manager=None):
        super().__init__()
        
        # Usar la instancia pasada o crear una nueva si no se proporciona
        if license_manager:
            self.license_manager = license_manager
        else:
            self.license_manager = LicenseManager()
            
        self.setup_ui()
        
        # Timer para actualizar información periódicamente
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_license_info)
        self.update_timer.start(300000)  # Actualizar cada 5 minutos
        
        # Cargar información inicial con delay para asegurar que la licencia está cargada
        QTimer.singleShot(1000, self.update_license_info)
    
    def setup_ui(self):
        """Configura la interfaz de usuario del dashboard."""
        # Scroll area para contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        main_widget = QWidget()
        scroll.setWidget(main_widget)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        content_layout = QVBoxLayout(main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Título del dashboard
        title_label = QLabel("📊 Dashboard - BootCasosV2")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        content_layout.addWidget(title_label)
        
        # Información de licencia
        self.license_group = self.create_license_info_group()
        content_layout.addWidget(self.license_group)
        
        # Información del sistema
        self.system_group = self.create_system_info_group()
        content_layout.addWidget(self.system_group)
        
        # Características disponibles
        self.features_group = self.create_features_group()
        content_layout.addWidget(self.features_group)
        
        # Estadísticas de uso
        self.stats_group = self.create_stats_group()
        content_layout.addWidget(self.stats_group)
        
        content_layout.addStretch()
    
    def create_license_info_group(self):
        """Crea el grupo de información de licencia."""
        group = QGroupBox("🔐 Información de Licencia")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #34495E;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Grid para información de licencia
        info_layout = QGridLayout()
        info_layout.setColumnStretch(1, 1)
        
        # Estado de la licencia
        self.status_label = QLabel("🔄 Estado:")
        self.status_value = QLabel("Verificando...")
        self.setup_info_row(info_layout, 0, "Estado:", self.status_label, self.status_value)
        
        # Cliente
        self.client_label = QLabel("👤 Cliente:")
        self.client_value = QLabel("Cargando...")
        self.setup_info_row(info_layout, 1, "Cliente:", self.client_label, self.client_value)
        
        # Identificación
        self.identification_label = QLabel("🆔 Identificación:")
        self.identification_value = QLabel("Cargando...")
        self.setup_info_row(info_layout, 2, "Identificación:", self.identification_label, self.identification_value)
        
        # Clave de licencia
        self.license_key_label = QLabel("🔑 Clave:")
        self.license_key_value = QLabel("Cargando...")
        self.setup_info_row(info_layout, 3, "Clave:", self.license_key_label, self.license_key_value)
        
        # Fecha de expiración
        self.expiration_label = QLabel("📅 Expiración:")
        self.expiration_value = QLabel("Verificando...")
        self.setup_info_row(info_layout, 4, "Expiración:", self.expiration_label, self.expiration_value)
        
        layout.addLayout(info_layout)
        return group
    
    def create_system_info_group(self):
        """Crea el grupo de información del sistema."""
        group = QGroupBox("💻 Información del Sistema")
        group.setStyleSheet(self.get_group_style())
        
        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)
        
        # Versión de la aplicación
        app_version_label = QLabel("📦 Versión:")
        app_version_value = QLabel(config.get('app.version'))
        self.setup_info_row(layout, 0, "Versión:", app_version_label, app_version_value)
        
        # Hardware ID
        hardware_id = self.license_manager.get_hardware_id()
        hardware_label = QLabel("🖥️ Hardware ID:")
        hardware_value = QLabel(hardware_id)
        hardware_value.setStyleSheet("font-family: monospace; color: #7F8C8D;")
        self.setup_info_row(layout, 1, "Hardware ID:", hardware_label, hardware_value)
        
        # Estado de conexión
        self.connection_label = QLabel("🌐 Conexión:")
        self.connection_value = QLabel("Verificando...")
        self.setup_info_row(layout, 2, "Conexión:", self.connection_label, self.connection_value)
        
        return group
    
    def create_features_group(self):
        """Crea el grupo de características disponibles."""
        group = QGroupBox("✨ Características Disponibles")
        group.setStyleSheet(self.get_group_style())
        
        layout = QVBoxLayout(group)
        
        self.features_layout = QVBoxLayout()
        layout.addLayout(self.features_layout)
        
        # Placeholder inicial
        self.features_placeholder = QLabel("🔄 Cargando características...")
        self.features_placeholder.setStyleSheet("color: #7F8C8D; font-style: italic;")
        self.features_layout.addWidget(self.features_placeholder)
        
        return group
    
    def create_stats_group(self):
        """Crea el grupo de estadísticas."""
        group = QGroupBox("📈 Estadísticas de Uso")
        group.setStyleSheet(self.get_group_style())
        
        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)
        
        # Tiempo de actividad
        uptime_label = QLabel("⏱️ Sesión iniciada:")
        self.uptime_value = QLabel(datetime.now().strftime("%H:%M:%S - %d/%m/%Y"))
        self.setup_info_row(layout, 0, "Sesión:", uptime_label, self.uptime_value)
        
        # Servidor de licencias
        server_label = QLabel("🌐 Servidor:")
        server_value = QLabel(config.get('license.server_url', 'No configurado'))
        self.setup_info_row(layout, 1, "Servidor:", server_label, server_value)
        
        return group
    
    def setup_info_row(self, layout, row, text, label, value):
        """Configura una fila de información."""
        label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        value.setStyleSheet("color: #34495E;")
        value.setWordWrap(True)
        
        layout.addWidget(label, row, 0, Qt.AlignTop)
        layout.addWidget(value, row, 1, Qt.AlignTop)
    
    def get_group_style(self):
        """Retorna el estilo CSS para los grupos."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #34495E;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """
    
    def update_license_info(self):
        """Actualiza la información de la licencia."""
        try:
            # Obtener información de la licencia actual
            license_info = self.license_manager.get_license_info()
            
            if license_info.get('valid'):
                # Licencia válida - actualizar UI
                
                # Actualizar estado
                status = license_info.get('status', 'unknown').upper()
                if status == 'ACTIVE':
                    self.status_value.setText("✅ ACTIVA")
                    self.status_value.setStyleSheet("color: #27AE60; font-weight: bold;")
                else:
                    self.status_value.setText(f"⚠️ {status}")
                    self.status_value.setStyleSheet("color: #F39C12; font-weight: bold;")
                
                # Actualizar información básica
                self.client_value.setText(license_info.get('client_name', 'No disponible'))
                self.identification_value.setText(license_info.get('client_identification', 'No disponible'))
                self.license_key_value.setText(license_info.get('license_key', 'No disponible'))
                self.license_key_value.setStyleSheet("font-family: monospace; color: #3498DB; font-weight: bold;")
                
                # Procesar fecha de expiración
                expiration_date = license_info.get('expiration_date')
                if expiration_date:
                    try:
                        # Convertir ISO format a fecha legible
                        dt = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                        
                        # Calcular días restantes (hacer datetime.now() timezone-aware)
                        now = datetime.now(dt.tzinfo)
                        days_remaining = (dt - now).days
                        
                        if days_remaining > 7:
                            self.expiration_value.setText(f"📅 {formatted_date} ({days_remaining} días)")
                            self.expiration_value.setStyleSheet("color: #27AE60; font-weight: bold;")
                        elif days_remaining > 0:
                            self.expiration_value.setText(f"⚠️ {formatted_date} ({days_remaining} días)")
                            self.expiration_value.setStyleSheet("color: #F39C12; font-weight: bold;")
                        else:
                            self.expiration_value.setText(f"❌ Expiró el {formatted_date}")
                            self.expiration_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
                    except Exception as e:
                        self.expiration_value.setText("📅 Formato de fecha no válido")
                        self.expiration_value.setStyleSheet("color: #7F8C8D;")
                else:
                    self.expiration_value.setText("📅 No especificada")
                    self.expiration_value.setStyleSheet("color: #7F8C8D;")
                
                # Actualizar características
                features = license_info.get('features', [])
                self.update_features(features)
                
                # Estado de conexión
                self.connection_value.setText("🟢 Conectado")
                self.connection_value.setStyleSheet("color: #27AE60; font-weight: bold;")
                
            else:
                # Sin licencia válida
                self.status_value.setText("❌ SIN LICENCIA")
                self.status_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
                
                self.client_value.setText("No disponible")
                self.identification_value.setText("No disponible")
                self.license_key_value.setText("No disponible")
                self.expiration_value.setText("No disponible")
                
                # Limpiar características
                self.clear_features()
                
                self.connection_value.setText("🔴 Sin licencia")
                self.connection_value.setStyleSheet("color: #E74C3C; font-weight: bold;")
                
        except Exception as e:
            # Error al obtener información
            self.status_value.setText("⚠️ ERROR")
            self.status_value.setStyleSheet("color: #E67E22; font-weight: bold;")
            
            self.client_value.setText("Error al cargar")
            self.identification_value.setText("Error al cargar")
            self.license_key_value.setText("Error al cargar")
            self.expiration_value.setText("Error al cargar")
            
            self.connection_value.setText("🟡 Error de conexión")
            self.connection_value.setStyleSheet("color: #F39C12; font-weight: bold;")
    
    def update_features(self, features_list):
        """Actualiza la lista de características."""
        # Limpiar características anteriores
        self.clear_features()
        
        if features_list:
            feature_icons = {
                'api_access': '🌐',
                'playwright_automation': '🎭', 
                'premium_features': '⭐',
                'advanced_reporting': '📊',
                'data_export': '📤',
                'custom_scripts': '📝'
            }
            
            for feature in features_list:
                icon = feature_icons.get(feature, '✅')
                feature_name = feature.replace('_', ' ').title()
                
                feature_label = QLabel(f"{icon} {feature_name}")
                feature_label.setStyleSheet("""
                    color: #27AE60; 
                    font-weight: bold; 
                    padding: 5px; 
                    background-color: #E8F5E8; 
                    border-radius: 4px;
                    margin: 2px;
                """)
                self.features_layout.addWidget(feature_label)
        else:
            placeholder = QLabel("ℹ️ No hay características disponibles")
            placeholder.setStyleSheet("color: #7F8C8D; font-style: italic;")
            self.features_layout.addWidget(placeholder)
    
    def clear_features(self):
        """Limpia todas las características mostradas."""
        while self.features_layout.count():
            item = self.features_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def refresh_license_info(self):
        """Método público para refrescar la información de licencia."""
        self.update_license_info()