"""
Script de migración para actualizar el esquema de base de datos
De modelo antiguo (Meal con dish_id directo) a nuevo modelo (Meal con MealDish y DishBatch)

IMPORTANTE: Este script:
1. Crea las nuevas tablas (dish_batches, meal_dishes)
2. Migra los datos existentes de meals a meal_dishes
3. Elimina las columnas obsoletas de meals (dish_id, ingredients_deducted)

PRECAUCIÓN: Hacer backup de la base de datos antes de ejecutar
"""

from app import create_app
from models import db, Meal, MealDish, DishBatch
from datetime import datetime
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("MIGRACIÓN DE BASE DE DATOS - PlanBuyCook")
        print("=" * 60)
        print()
        
        # 1. Crear nuevas tablas
        print("1. Creando nuevas tablas (dish_batches, meal_dishes)...")
        try:
            # Crear solo las nuevas tablas
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS dish_batches (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dish_id INT NOT NULL,
                    preparation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    percentage_remaining FLOAT NOT NULL DEFAULT 100.0,
                    ingredients_deducted BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
                    CONSTRAINT check_percentage_valid CHECK (percentage_remaining >= 0 AND percentage_remaining <= 100)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS meal_dishes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    meal_id INT NOT NULL,
                    dish_id INT NOT NULL,
                    batch_id INT NOT NULL,
                    percentage INT NOT NULL,
                    `order` INT NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
                    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
                    FOREIGN KEY (batch_id) REFERENCES dish_batches(id) ON DELETE CASCADE,
                    CONSTRAINT check_valid_percentage CHECK (percentage IN (5, 10, 25, 50, 100))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            db.session.commit()
            print("   ✓ Tablas creadas exitosamente")
        except Exception as e:
            print(f"   ⚠ Error al crear tablas (puede que ya existan): {e}")
            db.session.rollback()
        
        print()
        
        # 2. Migrar datos de meals existentes
        print("2. Migrando datos de comidas existentes...")
        
        # Obtener comidas con platos asignados (usando SQL directo)
        result = db.session.execute(text("""
            SELECT id, dish_id, ingredients_deducted 
            FROM meals 
            WHERE dish_id IS NOT NULL
        """))
        meals_with_dishes = result.fetchall()
        
        migrated_count = 0
        batch_cache = {}  # Cache de batches por dish_id
        
        for meal_row in meals_with_dishes:
            meal_id, dish_id, ingredients_deducted = meal_row
            
            try:
                # Crear o reutilizar batch para este plato
                if dish_id not in batch_cache:
                    # Crear batch
                    db.session.execute(text("""
                        INSERT INTO dish_batches (dish_id, preparation_date, percentage_remaining, ingredients_deducted)
                        VALUES (:dish_id, :prep_date, 0.0, :deducted)
                    """), {
                        'dish_id': dish_id,
                        'prep_date': datetime.utcnow(),
                        'deducted': bool(ingredients_deducted)
                    })
                    db.session.flush()
                    
                    # Obtener el ID del batch creado
                    batch_result = db.session.execute(text("""
                        SELECT id FROM dish_batches WHERE dish_id = :dish_id ORDER BY id DESC LIMIT 1
                    """), {'dish_id': dish_id})
                    batch_id = batch_result.scalar()
                    batch_cache[dish_id] = batch_id
                else:
                    batch_id = batch_cache[dish_id]
                
                # Crear meal_dish
                db.session.execute(text("""
                    INSERT INTO meal_dishes (meal_id, dish_id, batch_id, percentage, `order`)
                    VALUES (:meal_id, :dish_id, :batch_id, 100, 0)
                """), {
                    'meal_id': meal_id,
                    'dish_id': dish_id,
                    'batch_id': batch_id
                })
                
                migrated_count += 1
                
            except Exception as e:
                print(f"   ⚠ Error migrando meal_id={meal_id}: {e}")
                continue
        
        db.session.commit()
        print(f"   ✓ {migrated_count} comidas migradas exitosamente")
        print()
        
        # 3. Eliminar columnas obsoletas de meals
        print("3. Eliminando columnas obsoletas de tabla meals...")
        try:
            # Primero eliminar el índice/foreign key de dish_id
            db.session.execute(text("""
                ALTER TABLE meals DROP FOREIGN KEY meals_ibfk_2
            """))
            db.session.commit()
            
            # Eliminar constraint que involucra dish_id
            db.session.execute(text("""
                ALTER TABLE meals DROP CONSTRAINT IF EXISTS check_meal_assignment
            """))
            db.session.commit()
            
            # Eliminar columnas
            db.session.execute(text("""
                ALTER TABLE meals 
                DROP COLUMN dish_id,
                DROP COLUMN ingredients_deducted
            """))
            db.session.commit()
            print("   ✓ Columnas eliminadas exitosamente")
        except Exception as e:
            print(f"   ⚠ Error al eliminar columnas: {e}")
            db.session.rollback()
        
        print()
        print("=" * 60)
        print("MIGRACIÓN COMPLETADA")
        print("=" * 60)
        print()
        print("Resumen:")
        print(f"  - Comidas migradas: {migrated_count}")
        print(f"  - Batches creados: {len(batch_cache)}")
        print()
        print("NOTA: Los batches migrados tienen 0% restante porque")
        print("      representan platos ya consumidos anteriormente.")
        print()


if __name__ == '__main__':
    response = input("¿Desea continuar con la migración de base de datos? (si/no): ")
    if response.lower() in ['si', 'sí', 'yes', 'y', 's']:
        migrate_database()
    else:
        print("Migración cancelada")
