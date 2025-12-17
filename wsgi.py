"""
Punto de entrada WSGI para producción con Gunicorn
"""
from app import create_app

# Crear la aplicación Flask
app = create_app()

if __name__ == "__main__":
    app.run()
