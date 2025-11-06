# API de Licencias - Documentación Técnica

## 📋 Resumen de Cambios Implementados

He modificado completamente el sistema de licencias para que funcione **100% con tu API**. Aquí tienes toda la información que necesitas:

## 🗄️ **Base de Datos MariaDB - Estructura Requerida**

```sql
CREATE TABLE licenses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    license_key VARCHAR(50) UNIQUE NOT NULL,
    client_identification VARCHAR(50) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    expiration_date_encrypted TEXT NOT NULL,  -- Fecha encriptada con AES
    features JSON DEFAULT '["basic_access"]',  -- Características habilitadas
    status ENUM('active', 'expired', 'suspended', 'revoked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_validation TIMESTAMP NULL,  -- Última vez que se validó
    hardware_id VARCHAR(64),  -- ID del hardware del cliente
    app_version VARCHAR(20),  -- Versión de la app
    validation_count INT DEFAULT 0  -- Contador de validaciones
);

-- Índices recomendados
CREATE INDEX idx_license_key ON licenses(license_key);
CREATE INDEX idx_hardware_id ON licenses(hardware_id);
CREATE INDEX idx_status ON licenses(status);
```

## 🌐 **Endpoints de API que debes implementar**

### **1. POST `/api/licenses/validate`**
**Propósito**: Validar una licencia existente

**Request Body:**
```json
{
    "license_key": "BOOT-2024-ABCD-1234",
    "hardware_id": "a1b2c3d4e5f6g7h8", 
    "app_version": "1.0.0"
}
```

**Response Exitosa (200):**
```json
{
    "success": true,
    "data": {
        "license_key": "BOOT-2024-ABCD-1234",
        "client_name": "Juan Pérez",
        "client_identification": "12345678",
        "expiration_date": "2025-12-31T23:59:59Z",
        "features": ["api_access", "playwright_automation", "premium_features"],
        "status": "active",
        "days_remaining": 90
    }
}
```

**Response Licencia Expirada (400):**
```json
{
    "success": false,
    "error": "license_expired",
    "message": "La licencia ha expirado el 2024-10-15",
    "data": {
        "expired_date": "2024-10-15T23:59:59Z",
        "require_renewal": true
    }
}
```

**Response Licencia No Encontrada (404):**
```json
{
    "success": false,
    "error": "license_not_found", 
    "message": "La clave de licencia no es válida"
}
```

### **2. POST `/api/licenses/activate`**
**Propósito**: Activar/registrar una nueva licencia

**Request Body:**
```json
{
    "license_key": "BOOT-2024-WXYZ-5678",
    "hardware_id": "a1b2c3d4e5f6g7h8",
    "app_version": "1.0.0"
}
```

**Response Exitosa (200):**
```json
{
    "success": true,
    "message": "Licencia activada correctamente",
    "data": {
        "license_key": "BOOT-2024-WXYZ-5678", 
        "client_name": "María González",
        "client_identification": "87654321",
        "expiration_date": "2025-12-31T23:59:59Z",
        "features": ["api_access", "playwright_automation", "premium_features"],
        "status": "active",
        "days_remaining": 425
    }
}
```

**Response Error (404/400):**
```json
{
    "success": false,
    "error": "license_not_found",
    "message": "La clave de licencia no es válida"
}
```

## 🔧 **Lógica de Backend Recomendada**

### **Endpoint `/api/licenses/validate`**

```php
// Pseudocódigo para validación
function validateLicense($licenseKey, $hardwareId, $appVersion) {
    // 1. Buscar licencia en BD
    $license = DB::table('licenses')
        ->where('license_key', $licenseKey)
        ->first();
    
    if (!$license) {
        return ['success' => false, 'error' => 'license_not_found'];
    }
    
    // 2. Desencriptar fecha de expiración
    $expirationDate = decrypt($license->expiration_date_encrypted);
    
    // 3. Verificar si está expirada
    if (Carbon::parse($expirationDate)->isPast()) {
        return [
            'success' => false, 
            'error' => 'license_expired',
            'data' => ['expired_date' => $expirationDate]
        ];
    }
    
    // 4. Verificar estado
    if ($license->status !== 'active') {
        return ['success' => false, 'error' => 'license_suspended'];
    }
    
    // 5. Actualizar última validación
    DB::table('licenses')
        ->where('id', $license->id)
        ->update([
            'last_validation' => now(),
            'hardware_id' => $hardwareId,
            'app_version' => $appVersion,
            'validation_count' => DB::raw('validation_count + 1')
        ]);
    
    // 6. Retornar datos de licencia
    return [
        'success' => true,
        'data' => [
            'license_key' => $license->license_key,
            'client_name' => $license->client_name,
            'client_identification' => $license->client_identification,
            'expiration_date' => $expirationDate,
            'features' => json_decode($license->features),
            'status' => $license->status,
            'days_remaining' => Carbon::parse($expirationDate)->diffInDays(now())
        ]
    ];
}
```

### **Endpoint `/api/licenses/activate`**

```php
function activateLicense($licenseKey, $hardwareId, $appVersion) {
    // 1. Buscar licencia
    $license = DB::table('licenses')
        ->where('license_key', $licenseKey)
        ->first();
    
    if (!$license) {
        return ['success' => false, 'error' => 'license_not_found'];
    }
    
    // 2. Verificar si ya está activada en otro hardware
    if ($license->hardware_id && $license->hardware_id !== $hardwareId) {
        return ['success' => false, 'error' => 'license_already_activated'];
    }
    
    // 3. Verificar expiración
    $expirationDate = decrypt($license->expiration_date_encrypted);
    if (Carbon::parse($expirationDate)->isPast()) {
        return ['success' => false, 'error' => 'license_expired'];
    }
    
    // 4. Activar licencia
    DB::table('licenses')
        ->where('id', $license->id)
        ->update([
            'hardware_id' => $hardwareId,
            'app_version' => $appVersion,
            'status' => 'active',
            'last_validation' => now(),
            'updated_at' => now()
        ]);
    
    // 5. Retornar datos
    return [
        'success' => true,
        'message' => 'Licencia activada correctamente',
        'data' => [
            'license_key' => $license->license_key,
            'client_name' => $license->client_name,
            'client_identification' => $license->client_identification,
            'expiration_date' => $expirationDate,
            'features' => json_decode($license->features),
            'status' => 'active',
            'days_remaining' => Carbon::parse($expirationDate)->diffInDays(now())
        ]
    ];
}
```

## 🔐 **Encriptación de Fechas**

Para encriptar las fechas en la base de datos:

```php
// Encriptar fecha antes de guardar
$encryptedDate = encrypt('2025-12-31T23:59:59Z');

// Desencriptar al leer
$decryptedDate = decrypt($license->expiration_date_encrypted);
```

## ⚙️ **Configuración en la Aplicación**

El cliente solo necesita configurar en `.env`:

```bash
# URL de tu API
LICENSE_SERVER_URL=https://tu-api.example.com
```

## 🎯 **Características del Sistema**

✅ **Validación en tiempo real** con tu API  
✅ **No almacena licencias localmente** (más seguro)  
✅ **Interfaz gráfica** para ingresar licencias  
✅ **Detección automática** de licencias vencidas  
✅ **Gestión de características** por tipo de licencia  
✅ **Hardware binding** para prevenir piratería  
✅ **Logs completos** de todas las operaciones  

## 🚀 **Flujo de Funcionamiento**

1. **Al iniciar la app**: Verifica si necesita licencia
2. **Primera vez**: Muestra diálogo para ingresar licencia
3. **Licencia vencida**: Fuerza renovación  
4. **Validación**: Conecta con tu API en tiempo real
5. **Activación**: Registra hardware_id en tu BD
6. **Características**: Controla qué funciones están disponibles

## 📝 **Datos que tu API recibirá**

- **license_key**: La clave que le das al cliente
- **hardware_id**: ID único del hardware (16 caracteres hex)
- **app_version**: Versión de la aplicación

¿Te sirve esta especificación? ¿Necesitas alguna modificación o tienes preguntas sobre la implementación?