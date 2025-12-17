# 🚀 Guía de Despliegue en Ubuntu Server

## Requisitos Previos
- Ubuntu Server (18.04+)
- MariaDB ya instalado y funcionando
- Python 3.10+
- Git instalado
- Nginx o Apache ya configurado (para otras páginas)

---

## 1️⃣ Preparar el Servidor

### Instalar dependencias del sistema
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip git nginx -y
```

### Clonar el repositorio
```bash
cd /var/www
sudo git clone https://github.com/kindsee/Visual-Studio.git planbuycook
cd planbuycook

# Cambiar permisos
sudo chown -R $USER:$USER /var/www/planbuycook
```

---

## 2️⃣ Configurar la Aplicación

### Crear entorno virtual
```bash
cd /var/www/planbuycook
python3.10 -m venv venv
source venv/bin/activate
```

### Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Servidor WSGI para producción
```

### Configurar variables de entorno
```bash
sudo nano /var/www/planbuycook/.env
```

**Contenido del .env:**
```env
# Base de datos MariaDB
DB_HOST=localhost
DB_PORT=3306
DB_NAME=planbuycook
DB_USER=planbuycook_user
DB_PASSWORD=TU_PASSWORD_SEGURA

# Flask
FLASK_SECRET_KEY=GENERA_UNA_CLAVE_SEGURA_AQUI
FLASK_ENV=production
```

**Generar clave segura:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3️⃣ Configurar Base de Datos

### Crear usuario y base de datos en MariaDB
```bash
sudo mysql -u root -p
```

```sql
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS planbuycook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario
CREATE USER IF NOT EXISTS 'planbuycook_user'@'localhost' IDENTIFIED BY 'TU_PASSWORD_SEGURA';

-- Dar permisos
GRANT ALL PRIVILEGES ON planbuycook.* TO 'planbuycook_user'@'localhost';
FLUSH PRIVILEGES;

-- Salir
EXIT;
```

### Inicializar la base de datos
```bash
cd /var/www/planbuycook
source venv/bin/activate
python init_db.py
```

---

## 4️⃣ Configurar Gunicorn (Servidor WSGI)

### Crear archivo de entrada WSGI
```bash
nano /var/www/planbuycook/wsgi.py
```

**Contenido de wsgi.py:**
```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
```

### Probar Gunicorn manualmente
```bash
cd /var/www/planbuycook
source venv/bin/activate
gunicorn --bind 0.0.0.0:5001 wsgi:app
```

Si funciona (accede a `http://TU_IP:5001`), presiona `Ctrl+C` para detener.

### Crear servicio systemd
```bash
sudo nano /etc/systemd/system/planbuycook.service
```

**Contenido del servicio:**
```ini
[Unit]
Description=PlanBuyCook Flask Application
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/planbuycook
Environment="PATH=/var/www/planbuycook/venv/bin"
ExecStart=/var/www/planbuycook/venv/bin/gunicorn --workers 3 --bind unix:planbuycook.sock -m 007 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Activar y arrancar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl start planbuycook
sudo systemctl enable planbuycook
sudo systemctl status planbuycook
```

---

## 5️⃣ Opción A: Configurar Nginx (Recomendado)

### Crear configuración de sitio
```bash
sudo nano /etc/nginx/sites-available/planbuycook
```

**Contenido (con subdominio):**
```nginx
server {
    listen 80;
    server_name planbuycook.tudominio.com;  # Cambia por tu dominio/subdominio

    # Logs
    access_log /var/log/nginx/planbuycook_access.log;
    error_log /var/log/nginx/planbuycook_error.log;

    # Archivos estáticos
    location /static {
        alias /var/www/planbuycook/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy a Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/planbuycook/planbuycook.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**O si prefieres usar un path (ej: tudominio.com/planbuycook):**
```nginx
# Agregar dentro del server block de tu sitio existente
location /planbuycook {
    rewrite ^/planbuycook(/.*)$ $1 break;
    include proxy_params;
    proxy_pass http://unix:/var/www/planbuycook/planbuycook.sock;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Script-Name /planbuycook;
}

location /planbuycook/static {
    alias /var/www/planbuycook/static;
    expires 30d;
}
```

### Activar el sitio
```bash
sudo ln -s /etc/nginx/sites-available/planbuycook /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl reload nginx
```

### Configurar SSL con Let's Encrypt (Opcional pero recomendado)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d planbuycook.tudominio.com
```

---

## 5️⃣ Opción B: Configurar Apache

### Instalar mod_wsgi
```bash
sudo apt install libapache2-mod-wsgi-py3 -y
sudo a2enmod wsgi proxy proxy_http
```

### Crear configuración de sitio
```bash
sudo nano /etc/apache2/sites-available/planbuycook.conf
```

**Contenido:**
```apache
<VirtualHost *:80>
    ServerName planbuycook.tudominio.com
    ServerAdmin admin@tudominio.com

    # Proxy a Gunicorn
    ProxyPreserveHost On
    ProxyPass /static !
    ProxyPass / http://127.0.0.1:5001/
    ProxyPassReverse / http://127.0.0.1:5001/

    # Archivos estáticos
    Alias /static /var/www/planbuycook/static
    <Directory /var/www/planbuycook/static>
        Require all granted
    </Directory>

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/planbuycook_error.log
    CustomLog ${APACHE_LOG_DIR}/planbuycook_access.log combined
</VirtualHost>
```

### Activar el sitio
```bash
sudo a2ensite planbuycook
sudo systemctl reload apache2
```

---

## 6️⃣ Configurar Firewall (UFW)

```bash
# Permitir HTTP y HTTPS
sudo ufw allow 'Nginx Full'  # O 'Apache Full' si usas Apache
sudo ufw reload
sudo ufw status
```

---

## 7️⃣ Verificar que Todo Funciona

### Comprobar servicios
```bash
# Ver logs de Gunicorn
sudo systemctl status planbuycook
sudo journalctl -u planbuycook -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/planbuycook_error.log

# Ver logs de la aplicación (si tienes logging configurado)
tail -f /var/www/planbuycook/app.log
```

### Acceder a la aplicación
- Con subdominio: `http://planbuycook.tudominio.com`
- Con path: `http://tudominio.com/planbuycook`
- Con SSL: `https://planbuycook.tudominio.com`

---

## 8️⃣ Mantenimiento y Actualizaciones

### Actualizar código desde GitHub
```bash
cd /var/www/planbuycook
git pull origin main
sudo systemctl restart planbuycook
```

### Ver qué páginas tienes desplegadas
```bash
# Con Nginx
ls -la /etc/nginx/sites-enabled/

# Con Apache
ls -la /etc/apache2/sites-enabled/
```

### Verificar qué servidor web usas
```bash
# Ver si Nginx está corriendo
sudo systemctl status nginx

# Ver si Apache está corriendo
sudo systemctl status apache2

# Ver qué puertos están en uso
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

---

## 🔒 Seguridad Adicional

### Cambiar permisos del .env
```bash
chmod 600 /var/www/planbuycook/.env
sudo chown www-data:www-data /var/www/planbuycook/.env
```

### Configurar backup automático de la base de datos
```bash
sudo nano /usr/local/bin/backup_planbuycook.sh
```

**Contenido del script:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/planbuycook"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

mysqldump -u planbuycook_user -pTU_PASSWORD planbuycook | gzip > $BACKUP_DIR/planbuycook_$DATE.sql.gz

# Eliminar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup_planbuycook.sh

# Agregar a crontab (backup diario a las 3 AM)
sudo crontab -e
# Agregar línea:
0 3 * * * /usr/local/bin/backup_planbuycook.sh
```

---

## 🐛 Solución de Problemas

### Error "Permission denied" en el socket
```bash
sudo chown www-data:www-data /var/www/planbuycook/planbuycook.sock
sudo chmod 666 /var/www/planbuycook/planbuycook.sock
```

### Error "Bad Gateway" en Nginx
```bash
# Verificar que Gunicorn está corriendo
sudo systemctl status planbuycook

# Reiniciar ambos servicios
sudo systemctl restart planbuycook
sudo systemctl restart nginx
```

### Ver logs en tiempo real
```bash
# Logs de Gunicorn
sudo journalctl -u planbuycook -f

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Logs de la app Flask
tail -f /var/www/planbuycook/*.log
```

### Problemas de conexión a la base de datos
```bash
# Verificar que MariaDB está corriendo
sudo systemctl status mariadb

# Probar conexión
mysql -u planbuycook_user -p -h localhost planbuycook
```

---

## 📝 Resumen de Comandos Útiles

```bash
# Reiniciar aplicación
sudo systemctl restart planbuycook

# Ver estado
sudo systemctl status planbuycook

# Ver logs
sudo journalctl -u planbuycook -f

# Actualizar código
cd /var/www/planbuycook && git pull && sudo systemctl restart planbuycook

# Reiniciar servidor web
sudo systemctl restart nginx  # o apache2
```

---

## 🎯 Siguiente Paso

1. **Identifica qué servidor web usas** ejecutando:
   ```bash
   sudo systemctl status nginx
   sudo systemctl status apache2
   ```

2. **Revisa tus sitios actuales**:
   ```bash
   # Nginx
   ls -la /etc/nginx/sites-enabled/
   
   # Apache
   ls -la /etc/apache2/sites-enabled/
   ```

3. **Decide cómo desplegar**:
   - **Subdominio**: `planbuycook.tudominio.com` (más limpio)
   - **Path**: `tudominio.com/planbuycook` (comparte dominio)

4. **Sigue los pasos correspondientes** de esta guía según tu servidor web.

---

¿Necesitas ayuda con algún paso específico? Dime qué servidor web usas y te ayudo a configurarlo.
