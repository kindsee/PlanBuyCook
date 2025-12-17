"""
Aplicación Flask principal - PlanBuyCook

Inicializa la aplicación, registra blueprints y ejecuta el servidor.
"""
from flask import Flask, render_template
from config import Config
from models import db


def create_app(config_class=Config):
    """
    Factory function para crear la aplicación Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Ruta de inicio
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("🍽️  PlanBuyCook - Sistema de Gestión de Comidas")
    print("=" * 50)
    print("Servidor iniciado en: http://localhost:5001")
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5001)
