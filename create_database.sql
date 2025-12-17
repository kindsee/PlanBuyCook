-- Script SQL para crear la base de datos PlanBuyCook
-- Ejecutar este script en MariaDB antes de iniciar la aplicación

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS planbuycook 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE planbuycook;

-- Mensaje de confirmación
SELECT 'Base de datos planbuycook creada correctamente' AS mensaje;

-- Mostrar bases de datos disponibles
SHOW DATABASES;
