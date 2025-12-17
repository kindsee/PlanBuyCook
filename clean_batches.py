"""
Script para limpiar batches y meal_dishes corruptos de la migración
"""
from app import create_app
from models import db, DishBatch, MealDish, Meal

app = create_app()

with app.app_context():
    print("=" * 50)
    print("Limpiando batches y relaciones corruptas...")
    print("=" * 50)
    
    # Contar antes
    batch_count = DishBatch.query.count()
    meal_dish_count = MealDish.query.count()
    
    print(f"\nAntes de limpiar:")
    print(f"  - Batches: {batch_count}")
    print(f"  - MealDishes: {meal_dish_count}")
    
    # Borrar todas las relaciones meal_dishes
    MealDish.query.delete()
    print("\n✓ Borradas todas las relaciones meal_dishes")
    
    # Borrar todos los batches
    DishBatch.query.delete()
    print("✓ Borrados todos los batches")
    
    # Limpiar special_type de meals (opcional)
    meals_with_special = Meal.query.filter(Meal.special_type != None).all()
    for meal in meals_with_special:
        meal.special_type = None
    print(f"✓ Limpiados {len(meals_with_special)} meals con special_type")
    
    # Confirmar cambios
    db.session.commit()
    
    print("\n" + "=" * 50)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 50)
    print("\nAhora cuando asignes un plato:")
    print("  1. Verificará stock disponible")
    print("  2. Descontará TODOS los ingredientes al 100%")
    print("  3. Creará un batch nuevo con ingredients_deducted=True")
    print("\nPuedes empezar a planificar comidas desde cero.")
