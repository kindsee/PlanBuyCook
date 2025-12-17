"""
Script de inicialización de la base de datos

Crea las tablas y opcionalmente carga datos de ejemplo.
"""
from datetime import datetime, timedelta
from app import create_app
from models import db, Ingredient, PantryStock, Dish, DishIngredient, Day, Meal


def init_database(load_sample_data=True):
    """
    Inicializa la base de datos
    
    Args:
        load_sample_data: Si True, carga datos de ejemplo
    """
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🗄️  Inicializando Base de Datos - PlanBuyCook")
        print("=" * 60)
        
        # Eliminar tablas existentes
        print("\n1. Eliminando tablas existentes...")
        db.drop_all()
        print("   ✓ Tablas eliminadas")
        
        # Crear tablas nuevas
        print("\n2. Creando tablas nuevas...")
        db.create_all()
        print("   ✓ Tablas creadas")
        
        if load_sample_data:
            print("\n3. Cargando datos de ejemplo...")
            load_sample_ingredients()
            load_sample_dishes()
            load_sample_calendar()
            print("   ✓ Datos de ejemplo cargados")
        
        print("\n" + "=" * 60)
        print("✅ Base de datos inicializada correctamente")
        print("=" * 60)
        print("\nPuedes iniciar la aplicación ejecutando:")
        print("   python app.py")
        print("=" * 60)


def load_sample_ingredients():
    """Carga ingredientes de ejemplo con stock inicial"""
    print("\n   → Creando ingredientes...")
    
    ingredients_data = [
        # Cereales y granos
        {'name': 'Arroz', 'unit': 'g', 'stock': 1000},
        {'name': 'Pasta', 'unit': 'g', 'stock': 500},
        {'name': 'Pan', 'unit': 'unidades', 'stock': 2},
        {'name': 'Harina', 'unit': 'g', 'stock': 1000},
        
        # Proteínas
        {'name': 'Pollo', 'unit': 'g', 'stock': 800},
        {'name': 'Carne de res', 'unit': 'g', 'stock': 600},
        {'name': 'Huevos', 'unit': 'unidades', 'stock': 12},
        {'name': 'Pescado', 'unit': 'g', 'stock': 400},
        
        # Lácteos
        {'name': 'Leche', 'unit': 'ml', 'stock': 2000},
        {'name': 'Queso', 'unit': 'g', 'stock': 300},
        {'name': 'Mantequilla', 'unit': 'g', 'stock': 250},
        {'name': 'Yogur', 'unit': 'unidades', 'stock': 6},
        
        # Verduras
        {'name': 'Tomate', 'unit': 'unidades', 'stock': 6},
        {'name': 'Cebolla', 'unit': 'unidades', 'stock': 4},
        {'name': 'Ajo', 'unit': 'unidades', 'stock': 10},
        {'name': 'Zanahoria', 'unit': 'unidades', 'stock': 5},
        {'name': 'Pimiento', 'unit': 'unidades', 'stock': 3},
        {'name': 'Lechuga', 'unit': 'unidades', 'stock': 1},
        
        # Aceites y condimentos
        {'name': 'Aceite de oliva', 'unit': 'ml', 'stock': 500},
        {'name': 'Sal', 'unit': 'g', 'stock': 1000},
        {'name': 'Pimienta', 'unit': 'g', 'stock': 100},
    ]
    
    for ing_data in ingredients_data:
        ingredient = Ingredient(
            name=ing_data['name'],
            unit=ing_data['unit']
        )
        db.session.add(ingredient)
        db.session.flush()
        
        # Crear stock inicial
        stock = PantryStock(
            ingredient_id=ingredient.id,
            quantity=ing_data['stock']
        )
        db.session.add(stock)
        print(f"      • {ing_data['name']}: {ing_data['stock']} {ing_data['unit']}")
    
    db.session.commit()


def load_sample_dishes():
    """Carga platos de ejemplo con sus ingredientes"""
    print("\n   → Creando platos...")
    
    # Obtener ingredientes por nombre para facilitar la asignación
    def get_ing_id(name):
        return Ingredient.query.filter_by(name=name).first().id
    
    dishes_data = [
        {
            'name': 'Arroz con Pollo',
            'description': 'Clásico arroz con pollo casero',
            'ingredients': [
                {'name': 'Arroz', 'quantity': 200},
                {'name': 'Pollo', 'quantity': 300},
                {'name': 'Cebolla', 'quantity': 1},
                {'name': 'Ajo', 'quantity': 2},
                {'name': 'Aceite de oliva', 'quantity': 30},
            ]
        },
        {
            'name': 'Pasta Carbonara',
            'description': 'Pasta con salsa carbonara',
            'ingredients': [
                {'name': 'Pasta', 'quantity': 200},
                {'name': 'Huevos', 'quantity': 2},
                {'name': 'Queso', 'quantity': 50},
                {'name': 'Mantequilla', 'quantity': 20},
            ]
        },
        {
            'name': 'Ensalada César',
            'description': 'Ensalada fresca con pollo',
            'ingredients': [
                {'name': 'Lechuga', 'quantity': 1},
                {'name': 'Pollo', 'quantity': 150},
                {'name': 'Pan', 'quantity': 1},
                {'name': 'Queso', 'quantity': 30},
            ]
        },
        {
            'name': 'Tortilla de Patatas',
            'description': 'Tortilla española tradicional',
            'ingredients': [
                {'name': 'Huevos', 'quantity': 4},
                {'name': 'Cebolla', 'quantity': 1},
                {'name': 'Aceite de oliva', 'quantity': 50},
            ]
        },
        {
            'name': 'Sopa de Verduras',
            'description': 'Sopa casera nutritiva',
            'ingredients': [
                {'name': 'Zanahoria', 'quantity': 2},
                {'name': 'Cebolla', 'quantity': 1},
                {'name': 'Tomate', 'quantity': 2},
                {'name': 'Aceite de oliva', 'quantity': 20},
            ]
        },
    ]
    
    for dish_data in dishes_data:
        dish = Dish(
            name=dish_data['name'],
            description=dish_data['description']
        )
        db.session.add(dish)
        db.session.flush()
        
        # Añadir ingredientes al plato
        for ing in dish_data['ingredients']:
            dish_ingredient = DishIngredient(
                dish_id=dish.id,
                ingredient_id=get_ing_id(ing['name']),
                quantity=ing['quantity']
            )
            db.session.add(dish_ingredient)
        
        print(f"      • {dish_data['name']} ({len(dish_data['ingredients'])} ingredientes)")
    
    db.session.commit()


def load_sample_calendar():
    """Carga un calendario de ejemplo para la semana actual"""
    print("\n   → Creando calendario de ejemplo...")
    
    # Obtener platos
    arroz_pollo = Dish.query.filter_by(name='Arroz con Pollo').first()
    pasta = Dish.query.filter_by(name='Pasta Carbonara').first()
    ensalada = Dish.query.filter_by(name='Ensalada César').first()
    tortilla = Dish.query.filter_by(name='Tortilla de Patatas').first()
    
    # Crear días para la semana actual
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Lunes
    
    # Planificar algunos días de ejemplo
    calendar_data = [
        # Lunes
        {
            'date': start_of_week,
            'meals': [
                {'type': 'breakfast', 'dish': tortilla},
                {'type': 'lunch', 'dish': arroz_pollo},
                {'type': 'dinner', 'dish': ensalada},
            ]
        },
        # Martes
        {
            'date': start_of_week + timedelta(days=1),
            'meals': [
                {'type': 'lunch', 'dish': pasta},
                {'type': 'dinner', 'special': 'order'},  # Pedir comida
            ]
        },
        # Miércoles
        {
            'date': start_of_week + timedelta(days=2),
            'meals': [
                {'type': 'lunch', 'dish': ensalada},
                {'type': 'dinner', 'special': 'eat_out'},  # Comer fuera
            ]
        },
    ]
    
    for day_data in calendar_data:
        day = Day(date=day_data['date'])
        db.session.add(day)
        db.session.flush()
        
        for meal_data in day_data['meals']:
            meal = Meal(
                day_id=day.id,
                meal_type=meal_data['type'],
                dish_id=meal_data.get('dish').id if 'dish' in meal_data else None,
                special_type=meal_data.get('special'),
                ingredients_deducted=False  # No descontar en datos de ejemplo
            )
            db.session.add(meal)
        
        print(f"      • {day_data['date'].strftime('%d/%m/%Y')}: {len(day_data['meals'])} comidas")
    
    db.session.commit()


if __name__ == '__main__':
    import sys
    
    # Permitir ejecutar sin datos de ejemplo con --no-sample
    load_sample = '--no-sample' not in sys.argv
    
    init_database(load_sample_data=load_sample)
