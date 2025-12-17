"""
Script de Verificación del Proyecto PlanBuyCook

Verifica que todos los componentes del proyecto estén correctamente instalados
y configurados antes de ejecutar la aplicación.
"""
import sys
import os
from pathlib import Path


def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_status(message, status):
    """Imprime un mensaje con estado"""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {message}")


def check_python_version():
    """Verifica la versión de Python"""
    print_header("Verificando Python")
    version = sys.version_info
    required = (3, 10)
    
    current = f"{version.major}.{version.minor}.{version.micro}"
    print(f"  Versión actual: Python {current}")
    
    is_valid = version >= required
    print_status(f"Python {required[0]}.{required[1]}+ requerido", is_valid)
    
    return is_valid


def check_dependencies():
    """Verifica las dependencias de Python"""
    print_header("Verificando Dependencias")
    
    dependencies = {
        'flask': 'Flask',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'pymysql': 'PyMySQL',
        'dotenv': 'python-dotenv',
        'sqlalchemy': 'SQLAlchemy'
    }
    
    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_status(f"{name} instalado", True)
        except ImportError:
            print_status(f"{name} NO instalado", False)
            all_ok = False
    
    if not all_ok:
        print("\n  💡 Instala las dependencias con: pip install -r requirements.txt")
    
    return all_ok


def check_project_structure():
    """Verifica la estructura del proyecto"""
    print_header("Verificando Estructura del Proyecto")
    
    required_files = [
        'app.py',
        'config.py',
        'models.py',
        'routes.py',
        'services.py',
        'init_db.py',
        'requirements.txt',
        '.env.example',
        'README.md'
    ]
    
    required_dirs = [
        'templates',
        'static',
        'static/css'
    ]
    
    all_ok = True
    
    # Verificar archivos
    for file in required_files:
        exists = Path(file).exists()
        print_status(f"Archivo: {file}", exists)
        if not exists:
            all_ok = False
    
    # Verificar directorios
    for directory in required_dirs:
        exists = Path(directory).is_dir()
        print_status(f"Directorio: {directory}/", exists)
        if not exists:
            all_ok = False
    
    return all_ok


def check_templates():
    """Verifica los templates HTML"""
    print_header("Verificando Templates")
    
    templates = [
        'base.html',
        'index.html',
        'calendar.html',
        'dishes.html',
        'dish_form.html',
        'ingredients.html',
        'ingredient_form.html',
        'pantry.html',
        'shopping.html',
        'shopping_detail.html',
        'shopping_generate.html'
    ]
    
    all_ok = True
    for template in templates:
        path = Path('templates') / template
        exists = path.exists()
        print_status(f"Template: {template}", exists)
        if not exists:
            all_ok = False
    
    return all_ok


def check_env_file():
    """Verifica el archivo de configuración"""
    print_header("Verificando Configuración")
    
    env_example = Path('.env.example').exists()
    env_file = Path('.env').exists()
    
    print_status(".env.example existe", env_example)
    print_status(".env configurado", env_file)
    
    if not env_file:
        print("\n  💡 Crea el archivo .env copiando .env.example")
        print("     y configura tus credenciales de base de datos")
    
    return env_example


def check_database_connection():
    """Verifica la conexión a la base de datos"""
    print_header("Verificando Conexión a Base de Datos")
    
    try:
        import pymysql
        from dotenv import load_dotenv
        
        load_dotenv()
        
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '')
        db_port = int(os.getenv('DB_PORT', 3306))
        
        print(f"  Intentando conectar a: {db_user}@{db_host}:{db_port}")
        
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        print_status("Conexión a MariaDB/MySQL exitosa", True)
        
        # Verificar si existe la base de datos
        cursor = connection.cursor()
        db_name = os.getenv('DB_NAME', 'planbuycook')
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        db_exists = cursor.fetchone() is not None
        
        print_status(f"Base de datos '{db_name}' existe", db_exists)
        
        if not db_exists:
            print(f"\n  💡 Crea la base de datos con: mysql -u root -p < create_database.sql")
            print(f"     o ejecuta: CREATE DATABASE {db_name};")
        
        connection.close()
        return True
        
    except ImportError:
        print_status("PyMySQL no instalado", False)
        print("  💡 Instala con: pip install pymysql")
        return False
    except Exception as e:
        print_status(f"Error de conexión: {str(e)}", False)
        print("\n  💡 Verifica:")
        print("     1. MariaDB/MySQL está ejecutándose")
        print("     2. Credenciales en .env son correctas")
        print("     3. Usuario tiene permisos necesarios")
        return False


def print_summary(checks):
    """Imprime resumen de verificaciones"""
    print_header("Resumen de Verificación")
    
    total = len(checks)
    passed = sum(checks.values())
    
    print(f"\n  Total de verificaciones: {total}")
    print(f"  Exitosas: {passed}")
    print(f"  Fallidas: {total - passed}")
    
    if passed == total:
        print("\n  🎉 ¡Todas las verificaciones pasaron!")
        print("  ✅ El proyecto está listo para ejecutarse")
        print("\n  Siguiente paso:")
        print("     1. Inicializar base de datos: python init_db.py")
        print("     2. Ejecutar aplicación: python app.py")
    else:
        print("\n  ⚠️  Algunas verificaciones fallaron")
        print("  ❌ Corrige los errores antes de continuar")
        print("\n  Consulta:")
        print("     - README.md para instrucciones de instalación")
        print("     - GUIA_USO.md para solución de problemas")


def main():
    """Función principal"""
    print("\n" + "🔍 " * 20)
    print("  Script de Verificación - PlanBuyCook")
    print("🔍 " * 20)
    
    checks = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Project Structure': check_project_structure(),
        'Templates': check_templates(),
        'Configuration': check_env_file(),
        'Database': check_database_connection()
    }
    
    print_summary(checks)
    
    print("\n" + "=" * 60)
    print()
    
    return all(checks.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
